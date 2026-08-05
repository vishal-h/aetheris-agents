# cloudcost — runbook

Per-provider cost-report + orphan-detection agent, currently **DigitalOcean**, **AWS** and
**Linode**.
**Read-only, report-only:** it fetches the live bill and resource inventory, detects
wasteful/orphaned resources, and renders a local HTML report. It never writes to the cloud
account, mails, or uploads anything.

**One provider per run** (m2 decision H). `CLOUDCOST_PROVIDER` selects the pipeline; each run
produces its own report in its own directory. There is no cross-provider run and no combined
report — two providers means two runs.

Design detail and rationale live in `milestone.md` (§Normalized schemas, D1–D6),
`m2-milestone.md` (decisions A–H) and `m3-milestone.md` (D-L1–D-L11, Linode); this file is how
to run it.

## Prerequisites

- **`ANTHROPIC_API_KEY`** — for the orchestrator LLM (haiku). Without it the harness silently
  falls back to the stub adapter and produces nothing; confirm real calls in the trajectory
  (`latency_ms` non-zero, `resolved_model` = the haiku model).
- **python3** with `requests`, `Jinja2` and `boto3` (`pip install -r cloudcost/requirements.txt`).

Then the selected provider's read-only credential — and only that one:

### DigitalOcean

- **`CLOUDCOST_DO_TOKEN`** — a read-only DO Personal Access Token, exported before the run.
  It must be the *only* DO token in the environment: `pydo`/`doctl` and hand-rolled clients
  default to `DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN`, and a stray write token there would shadow
  the read-only one. Verify in a fresh login shell:
  ```
  [ -z "$DO_TOKEN" ] && [ -z "$DIGITALOCEAN_ACCESS_TOKEN" ] && [ -n "$CLOUDCOST_DO_TOKEN" ] && echo ok
  ```

### AWS

- **`CLOUDCOST_AWS_ACCESS_KEY_ID`** + **`CLOUDCOST_AWS_SECRET_ACCESS_KEY`** — the read-only IAM
  user's key (optionally `CLOUDCOST_AWS_SESSION_TOKEN`, `CLOUDCOST_AWS_REGION`, and
  `CLOUDCOST_AWS_REGIONS` to override the swept-region set). `fetch_aws.py` builds its boto3
  session **explicitly** from these and never consults the default credential chain.

  The shadowing problem is worse here than on DO, because boto3's default chain reads
  `AWS_ACCESS_KEY_ID`/`AWS_PROFILE`, `~/.aws/credentials` **and** instance metadata — and the
  operator's workstation legitimately carries a personal AWS credential in the first two. So
  the answer is *not* a globally clean environment; see the hermetic invocation below, which
  neutralizes the default chain for the harness process alone and leaves the personal setup
  untouched.

  Selecting AWS without the key pair raises at agent-eval time rather than falling back to
  anything else, so a misconfigured run fails loud and costs no LLM call.

- **Load the key with `set -a`, not a bare `source`.** If the credential lives in a
  `KEY=value` file, export it:
  ```
  set -a; source ~/.secrets/aws-cloudcost.env; set +a
  ```
  The sprint and the orchestrator run as **child processes**, so `CLOUDCOST_AWS_*` must be
  *exported*, not merely set. A bare `source` of a `KEY=val` file leaves the variables
  shell-local: `[ -n "$CLOUDCOST_AWS_ACCESS_KEY_ID" ]` in your own shell says they are there,
  the preflight in the child says they are unset, and the two disagree with no error in
  between. `set -a`/`set +a` exports everything the file sets. The `env -u` prefix below is
  unaffected and still strips your personal `AWS_*` for the child.

### Linode

- **`CLOUDCOST_LINODE_TOKEN`** — a read-only Linode Personal Access Token. Scope it **Read
  Only** on exactly six surfaces and **No Access** on everything else:

  | Read Only | Why |
  |---|---|
  | Account | the billing surface — there is no separate Billing scope |
  | Linodes | instances |
  | Volumes | block storage |
  | IPs | addresses (the `reserved` flag is what makes the static-IP rule reachable) |
  | NodeBalancers | load balancers, plus the per-balancer configs read |
  | Images | snapshots |

  **No Access includes Databases and Events**, deliberately: Managed Databases are excluded
  (`m3-milestone.md` §D-L7) and `/account/events` answers "when was this last *changed*", not
  "last *used*", so `last_activity_at` stays `null` (§D-L8). Granting either would be granting
  read on data nothing reads.

  `fetch_linode.py` authenticates with this variable and **only** this one. It never falls back
  to a default-pickup arm, and there is no Linode analogue of boto3's credential chain.

- **Token expiry: 2027-02-04.** PAT label `aetheris-cloudcost`, created 2026-08-04 15:34,
  expires 2027-02-04 00:00 — the value the Linode console displays, not one derived from
  "6 months" or "180 days", which give 2027-02-04 and 2027-01-31 respectively. When it
  expires the symptom will be a fatal auth error from `fetch_linode.py`, not something that
  reads like an expiry; re-issue with the same Read Only scope set in the table above.

- **The credential file and the `set -a` load requirement.** The token lives in
  `~/.secrets/linode-cloudcost.env`. Load it **exported**:
  ```
  set -a; source ~/.secrets/linode-cloudcost.env; set +a
  ```
  This is the same trap the AWS section records above, and it bites the same way: the sprint,
  the orchestrator and the agent eval all run as **child processes**, so a bare `source` of a
  `KEY=value` file leaves the variable shell-local — your own shell reports it present, the
  child preflight reports it unset, and nothing errors in between.

- **Shadowing.** `linode-cli` reads **`LINODE_CLI_TOKEN`**; **`LINODE_TOKEN`** is the spelling
  users conventionally export and is read by no library at all. The adapter reads neither and
  warns when either is set. The sprint's hermetic prefix strips both
  (`../aetheris/scripts/sprint.sh`, the `CC_HERMETIC` array), so a sprint leg cannot
  accidentally exercise an ambient token.

- **Endpoint redirection — a hazard neither predecessor has.** `LINODE_CLI_API_HOST`,
  `LINODE_CLI_API_VERSION` and `LINODE_CLI_API_SCHEME` are read by `linode-cli` and redirect
  *where a credential is sent*. The adapter constructs its own base URL and never reads them as
  configuration — it **warns** when they are set. They are deliberately **not** stripped by the
  hermetic prefix: stripping them would silence the only signal that hazard has.

- **A partial run now stops the pipeline, and that is a change from what you may expect.** If a
  resource class cannot be read, that class is recorded as `not_inventoried` — never degraded to
  an empty list (§D-L6) — and a non-empty `not_inventoried` makes the whole run `status:
  partial` with **exit 1**, even when no request returned an error. So a transient failure on one
  class stops the run rather than producing a report with a quiet hole in it. That is the
  intended trade: a report silently missing a class reads exactly like a clean account. Re-run;
  if the class keeps failing, check the PAT's scope set against the table above before assuming
  the account is empty.

- **Artifacts are named for the month they COVER, which is not the current month.** Linode
  publishes no preview invoice, so a run reads the newest *settled* invoice: a run on 2026-08-05
  writes `linode_costs_2026-07.json` and `cloudcost_report_2026-07.html`, while an AWS run the
  same day writes `…2026-08…`. The in-flight month exists only as `balance_uninvoiced`, which the
  report's balance block already carries. Never construct one of these filenames from the wall
  clock — read the period from the run's own output. (The sprint case does exactly that; it used
  to build the name from `date -u +%Y-%m`, which was right for two providers and wrong for this
  one.)

- **Fetch-step timeout — confirmed, unchanged.** `fetch_linode` measured **4441 ms** and
  **4097 ms** wall clock on two live runs (m3 t1), against the shared
  `fetch_timeout_ms = 300_000` declared at `agents/cloudcost_orchestrator.exs:147` — roughly a
  **73×** margin. Per [Adding a provider](#adding-a-provider) the measurement is *recorded*, and
  the declared value changes only if the margin is inadequate. It is not.

The credentials gate only the *live* steps; the offline test suite needs none of them.

## Run it

**DigitalOcean** (the default — `CLOUDCOST_PROVIDER` unset):
```
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```

**AWS — this is the canonical invocation, prefix included** (m2 decision C):
```
cd ~/sandbox/elixirws/aetheris
CLOUDCOST_PROVIDER=aws \
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \
    AWS_SHARED_CREDENTIALS_FILE=/dev/null \
    mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```
The `env -u …` prefix strips the three shadowing variables and points the credentials-file
lookup at nothing, **for that process only**. `CLOUDCOST_AWS_*` are deliberately *not* in the
`-u` list, so they survive the strip — that is the credential the adapter authenticates with.
Keep the prefix even though the adapter's explicit-session construction already ignores the
default chain: belt and suspenders, and the belt is the part that is visible in the command.

**Linode** — same shape, but the shadow names are Linode's own rather than boto3's:
```
cd ~/sandbox/elixirws/aetheris
set -a; source ~/.secrets/linode-cloudcost.env; set +a
CLOUDCOST_PROVIDER=linode \
env -u LINODE_CLI_TOKEN -u LINODE_TOKEN \
    mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```
Selecting Linode without `CLOUDCOST_LINODE_TOKEN` raises at agent-eval time, before any LLM
call — same posture as AWS, and for the same reason. There is no credentials-file arm to point
at `/dev/null`: Linode's shadowing surface is the two variables above and nothing else.

**AWS with the exploratory optimization spike** (m2 t4) — the same invocation with one more
variable:
```
cd ~/sandbox/elixirws/aetheris
CLOUDCOST_PROVIDER=aws CLOUDCOST_OPTIMIZATION=1 \
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \
    AWS_SHARED_CREDENTIALS_FILE=/dev/null \
    mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```
This adds one step — `detect_optimization_signals.py`, writing
`output/aws/optimization_signals_aws_{YYYY-MM}.json` — and threads that file into the render,
which then carries an extra "Optimization signals (exploratory)" section. Notes:

- **Unset, nothing changes.** The pipeline and the rendered report are exactly what they are
  without it; the orchestrator builds a byte-identical prompt, and the report is byte-identical
  to the core report. So there is no reason to unset it "to get a clean report" — leaving it
  off *is* the clean report.
- **It needs the t4 spike IAM actions** (§Prereqs 1: `s3:ListAllMyBuckets`,
  `s3:GetBucketLocation`, `s3:GetLifecycleConfiguration`, `s3:ListBucketMultipartUploads`,
  `ecr:DescribeRepositories`, `ecr:DescribeImages`, `ecr:GetLifecyclePolicy`,
  `secretsmanager:ListSecrets`, `cloudwatch:GetMetricData`). Without them the step degrades:
  it still exits 0 and still writes its file, and the refused calls are listed under
  `denied[]` and rendered as "Not checked" — an unchecked family never reads as an empty one.
- **A thin or empty result is a pass.** The spike is exploratory and non-gating.
- **Dollar figures are list prices** for prioritization, not the bill, and appear only where a
  published rate is held — a region or storage class without one is shown with no figure
  rather than an estimated one.
- **`CLOUDCOST_OPTIMIZATION=1` without `CLOUDCOST_PROVIDER=aws` raises**, rather than being
  silently ignored: the spike reads S3/ECR/Secrets Manager and exists for one provider only.

Sprint cases (same prereqs; each clears its own `output/{provider}/` first so its checks cannot
green on a stale run):
```
cd ~/sandbox/elixirws/aetheris
./scripts/sprint.sh cloudcost                          # DigitalOcean
CLOUDCOST_PROVIDER=aws ./scripts/sprint.sh cloudcost   # AWS (applies the prefix itself)
```

The four stages standalone (from `cloudcost/`, for debugging — the orchestrator just chains
these). Substitute `fetch_aws.py` / `aws` for the AWS pipeline:
```
P=$(date -u +%Y-%m)
python3 scripts/fetch_do.py --output-dir output/digitalocean
python3 scripts/detect_orphans.py output/digitalocean/do_inventory_$P.json --output-dir output/digitalocean
python3 scripts/compose_report_data.py --cost output/digitalocean/do_costs_$P.json \
    --inventory output/digitalocean/do_inventory_$P.json \
    --orphans output/digitalocean/digitalocean_orphan_candidates_$P.json \
    --output-dir output/digitalocean --history-dir history/digitalocean
python3 scripts/render_report.py output/digitalocean/report_data_$P.json --output-dir output/digitalocean
```

The optimization spike standalone (AWS only; needs the `CLOUDCOST_AWS_*` key in the
environment, and the same `env -u …` prefix if a personal `~/.aws` is present):
```
P=$(date -u +%Y-%m)
python3 scripts/detect_optimization_signals.py --output-dir output/aws
python3 scripts/render_report.py output/aws/report_data_$P.json --output-dir output/aws \
    --optimization-file output/aws/optimization_signals_aws_$P.json
```

## Output

`cloudcost/output/{provider}/cloudcost_report_{YYYY-MM}.html` is the deliverable — a
self-contained HTML report (open in any browser). Alongside it: the intermediate cost,
inventory, `{provider}_orphan_candidates_*` and `report_data_*` JSON. `output/` is gitignored.

**Each provider gets its own directory, and this matters.** `report_data_{period}.json` and
`cloudcost_report_{period}.html` carry no provider in their filenames, so two providers writing
into one directory would silently overwrite each other's report. The directory carries the
provider instead.

Period is the current UTC month (both adapters' default).

The AWS report states its **swept-region set** in the header ("aws regions swept (N)"), so a
sweep narrowed by `CLOUDCOST_AWS_REGIONS` or by a failed region enumeration is visible rather
than quietly shrinking the inventory behind an unchanged-looking report. DigitalOcean has no
region sweep, so its report carries no such line.

## Monthly cadence & history

Each run persists its cost snapshot to `cloudcost/history/{provider}/{YYYY-MM}/` (gitignored).
Next month's run reads the prior month from there to compute the month-on-month delta; the
first run for a provider reports "no prior month," which is expected, not an error. History
accumulates in production — do not seed or clear it between real monthly runs. (Tests and the
sprint use a scratch history dir so they stay deterministic.)

**The history tree is per-provider on purpose.** `compose_report_data.load_prior_snapshots`
globs every snapshot in the prior month's directory and sums them into one `prior_total`, which
is m1's N-provider merge assumption. Under per-provider runs a shared tree makes a solo AWS run
compare itself against DigitalOcean's previous month — measured at t3 as a `−185.21 USD`
headline (AWS's $0.29 August against DO's $185.50 July) where the honest answer is "no prior
month". Each provider reading only its own tree removes that. If you are upgrading a
pre-m2-t3 checkout, move the existing snapshots once:
```
cd cloudcost && mkdir -p history/digitalocean && mv history/2026-* history/digitalocean/
```

## Do not run the real-bill step on the first of a month

On day 1 both adapters degrade correctly and both degrade to **nothing useful**:

- **AWS** — Cost Explorer returns the period with a `ResultsByTime` entry carrying no groups, so
  the report has 0 line items and a $0.00 cost section. Honest, and empty.
- **DigitalOcean** — `select_invoice` finds no invoice for the new period at all, so the run is
  `status: partial` with no cost file written.

Neither is a defect; it is the degrade-don't-crash path working. But a report generated on the
1st has no cost section to review, which reads as a failure of the report rather than of the
calendar. Run it on the 2nd or later.

## Exercising the ≥1-orphan path

Detection only surfaces what the account actually carries, and **no live account currently
carries an orphan-shaped resource** — the DO reserved IP that used to arm this was deleted
2026-07-30 (BL-069), the AWS Elastic IP is `m2-milestone.md` §Prereqs 3 and still pending, and
the Linode account reports 0 candidates / 0 skipped over a full live inventory (m3 t1). All
three sprint legs therefore report 0 orphans and the `≥1` assertion is expected-red until one is
planted. Do not relax the assertion to make it green; plant the resource.

DO and AWS trip the **same** rule — m2 t2 unified the vocabulary, so it is
`unassociated_static_ip` (0.95, HIGH band) whether the resource is a DO reserved IP or an AWS
Elastic IP, and the rule has no age threshold: an unassociated static IP bills from the moment
it is unassociated.

**DigitalOcean** — console → **Networking → Reserved IPs → Reserve in Datacenter Region**, left
**unassigned**. ~$4.38/mo while it sits. **Delete it after the run** (a write, done by a human
in the console — the agent stays read-only). A *freshly created* unattached volume will not fire
for 14 days (the `>14d` threshold), so the reserved IP is the move.

**AWS** — console → **EC2 → Elastic IPs → Allocate**, left **unassociated**. Same posture —
release it after the run. Optional extras that exercise more of the catalog: a stopped EC2
instance with an attached EBS volume, or a stopped RDS instance (both hit
`rule_stopped_compute_with_attached_storage` / `rule_stopped_database_with_storage`).

**Linode — a zero-backend NodeBalancer, and *not* the reserved-IP recipe the other two use.**
Console → **NodeBalancers → Create**, type **`common`**, with **no backend nodes** on any
configuration. It trips `rule_idle_load_balancer`, which keys on type and `attached_to is None`
alone and carries **no age threshold**, so it fires the same day. **Delete it after the run.**

Two things make this the only sound same-day plant on Linode, and both are worth knowing before
substituting something cheaper:

- **Every other reachable rule carries an age threshold a same-day resource cannot satisfy** —
  `rule_unattached_volume` needs >14 days, `rule_stopped_compute_with_attached_storage` >30.
  Lowering `--snapshot-age-days` to make an orphan appear games the assertion rather than
  satisfying it.
- **The static-IP rule *is* reachable on Linode** (a reserved, unassigned address; the `reserved`
  flag the live API returns and the OpenAPI spec does not declare) — but Linode publishes no
  pricing endpoint for addresses, so such a candidate prices at `0.0` plus a named warning. It
  would satisfy `≥1` with **no dollar figure**, which is a weak proof for a cost report. A
  `premium` NodeBalancer is the same trap: that type is deliberately unmapped, since this account
  holds none and there is no evidence for which price row it bills at. Use `common`, which prices
  from a real invoice line.

A zero-backend `common` NodeBalancer also exercises the 1 + N configs read — Linode's most
distinctive inventory path, and the one nothing else covers.

Check without running the whole agent (AWS shown; use the DO equivalents for DO):
```
P=$(date -u +%Y-%m)
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE AWS_SHARED_CREDENTIALS_FILE=/dev/null \
    python3 scripts/fetch_aws.py --output-dir /tmp/live
python3 scripts/detect_orphans.py /tmp/live/aws_inventory_$P.json --output-dir /tmp/live
jq '.account, .totals.candidates' /tmp/live/aws_orphan_candidates_$P.json
```

**On Linode, `$(date -u +%Y-%m)` is the wrong period** — read the filename the adapter reports
instead of constructing one (see the `### Linode` prerequisites above):
```
env -u LINODE_CLI_TOKEN -u LINODE_TOKEN \
    python3 scripts/fetch_linode.py --output-dir /tmp/live | jq -r '.period, .files.inventory'
python3 scripts/detect_orphans.py /tmp/live/linode_inventory_<period>.json --output-dir /tmp/live
jq '.account, .totals.candidates' /tmp/live/linode_orphan_candidates_<period>.json
```

## Offline tests

```
python3 -m pytest cloudcost/tests/ -v      # no credentials; recorded DO + AWS + Linode fixtures
```

## Rig

Runs appear in Harness → Runs automatically, one per provider — the run id carries the provider
(`cloudcost-orch-aws-…`, `cloudcost-orch-digitalocean-…`, `cloudcost-orch-linode-…`), and so does
the label (`Cloudcost · AWS`, `Cloudcost · DigitalOcean`, `Cloudcost · Linode`), which is what
`classifyRun` groups on. The use case shows in the
capability-matrix view (Rig reads the regenerated `docs/capability-matrix.md` via
`rig/src-tauri/src/commands/capability_matrix.rs`). There is no dedicated cloudcost panel, and
the report is not yet surfaced against its run — that's BL-073.

### Launching from Rig (interim — the LLM planner door)

**This door adds an LLM planning turn.** Rig has no direct "run this orchestrator" control today;
the only path to a top-level named `.exs` run is the Orchestrator view, which asks a model to
turn your request into a plan of agent files. For a four-stage deterministic pipeline that is a
detour, and it is deliberate interim scope — the direct door is **BL-094**. The CLI recipe under
[Run it](#run-it) stays the deterministic path and is what sprint uses.

**1 — Credentials, once.** Settings → Agent Config → **CLOUDCOST**. The seven rows come from
`cloudcost/tools.json` alone; no `agentConfigDefs.ts` entry exists or is needed (BL-085 confirmed
the manifest path renders the group header and the masking by itself). Set:

| Row | Required for | Masked in the UI |
|---|---|---|
| `CLOUDCOST_AWS_ACCESS_KEY_ID` | AWS | no |
| `CLOUDCOST_AWS_SECRET_ACCESS_KEY` | AWS | yes |
| `CLOUDCOST_AWS_SESSION_TOKEN` | AWS, optional | yes |
| `CLOUDCOST_AWS_REGION` | AWS, optional (default `us-east-1`) | no |
| `CLOUDCOST_AWS_REGIONS` | AWS, optional sweep override | no |
| `CLOUDCOST_DO_TOKEN` | DigitalOcean | yes |
| `CLOUDCOST_LINODE_TOKEN` | Linode | yes |

Set the `CLOUDCOST_`-prefixed rows and **never** the bare `AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY` rows. Those belong to `api/tools.json` (group `aws`,
`api/tools.json:389-402`) and are the D2 poison — see the next section.

**2 — Provider, per launch.** Orchestrator → **"Additional env vars"** (collapsed by default,
above the Run button) → add a row:

```
CLOUDCOST_PROVIDER = aws          # or: digitalocean, linode
```

Exact literals, lowercase. Unset ⇒ `digitalocean`. Anything else raises *before* the run starts,
at `cloudcost/agents/cloudcost_orchestrator.exs:53-62`. Selecting `aws` or `linode` without that
provider's credential row set raises there too, for the same reason. These values are ephemeral: they are never
written to `agent-config.json`, they override a stored key of the same name for that launch only
(`rig/src-tauri/src/commands/orchestrate.rs:57-66`), and the rows clear themselves once the run
reaches a terminal phase (`OrchestratorView.tsx:139-141`).

Optionally add `CLOUDCOST_OPTIMIZATION = 1` — **AWS only**; it raises against any other provider
(`cloudcost_orchestrator.exs:176-181`).

**3 — Request text.** Write it so the planner names cloudcost, e.g. *"Run the cloudcost report
pipeline"*. The planner picks agent files out of `docs/capability-matrix.md`, where cloudcost is
listed at `:198`. Approve the plan when it appears; the run then behaves exactly as a CLI run.

> The provider hint is **not** surfaced on the plan card. `STEP_CONFIG_HINTS`
> (`OrchestratorView.tsx:13-33`) only displays keys that are set in *persisted* agent config, and
> `CLOUDCOST_PROVIDER` is deliberately not one — so a hint would render nothing, or worse, show a
> stale global while the run used your per-launch override. No cloudcost entry was added there on
> purpose; this section is the instruction instead.

### D2 posture — credentials in Rig (documented, not coded)

A Rig-launched run does **not** get the hermetic prefix. The canonical AWS invocation under
[Run it](#run-it) is wrapped in `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE
AWS_SHARED_CREDENTIALS_FILE=/dev/null`; Rig cannot apply that per agent, and `sprint.sh` gets it
only by building the prefix itself (`../aetheris/scripts/sprint.sh:2371-2373`).

It is worse than merely missing the belt. Rig injects the **entire** agent-config map as
environment, unfiltered by any script's declared `env`
(`rig/src-tauri/src/commands/orchestrate.rs:57-59`; same pattern for the Tools tab at
`tools.rs:662-664`), and `api/tools.json` declares bare `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` as config rows — so Rig's own settings surface actively *invites* setting
the two variables the belt exists to strip. **A Rig-launched cloudcost run may therefore have the
poison actively present, not merely lack the belt. "No belt" is not the same as "clean
environment" — do not read it as one.**

The guard holds anyway, by construction rather than by hygiene. Credentials are read from
`CLOUDCOST_AWS_*` only (`cloudcost/scripts/fetch_aws.py:229-250`) and passed to an explicitly
constructed session (`:301-310`) that both supplies the keys directly **and** nulls botocore's
`profile` session var, so neither the environment chain nor `~/.aws` is consulted. The shadowing
variables are read solely to emit a warning (`fetch_aws.py:257`). Verified live on 2026-08-04 in
exactly the poisoned condition — bare
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` exported **and** `~/.aws/credentials` present, no
`env -u` prefix:

```
$ CLOUDCOST_PROVIDER=aws mix run --eval \
    'Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")'
** (RuntimeError) CLOUDCOST_PROVIDER=aws requires CLOUDCOST_AWS_ACCESS_KEY_ID and
CLOUDCOST_AWS_SECRET_ACCESS_KEY to be set. cloudcost authenticates with the CLOUDCOST_AWS_*
read-only key only and never falls back to boto3's default credential chain.
                                                                        # exit 1
```

It refused rather than silently authenticating with the ambient key. That is the belt-and-suspenders
claim demonstrated, not asserted.

**Storage.** `agent-config.json` is plaintext on disk in the app data directory
(`rig/src-tauri/src/lib.rs:188-202`; the tab says so at `AgentConfigTab.tsx:195-199`). A read-only
key there is the same trust level as the GitHub PAT already stored there. **A write-capable key
must never go in it.**

**Export gap.** The six `CLOUDCOST_*` keys are editable and persisted, but `exportConfig()`
iterates the static defs only (`rig/src/hooks/useAgentConfig.ts:33-41`), so they are silently
omitted from Export until **BL-091**. Import is unaffected.

**Non-leak, verified.** Credentials do not reach the trajectory or `config_json`. Confirmed on a
live run — `cloudcost-orch-digitalocean-TW2-sA`, 2026-08-04, launched with `CLOUDCOST_DO_TOKEN`
set and the bare `AWS_*` poison present, producing
`output/digitalocean/cloudcost_report_2026-08.html`:

| Check | Result |
|---|---|
| `CLOUDCOST_` key names in trajectory (39,488 B) | 0 |
| `CLOUDCOST_DO_TOKEN` **value** in trajectory | 0 |
| bare `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` values in trajectory | 0 / 0 |
| `CLOUDCOST_` key names in `config_json` | 0 |
| `CLOUDCOST_DO_TOKEN` value in `config_json` | 0 |
| `RunConfig.env` as serialised | `{}` |

Both greps were mutation-checked against a file containing the token (each returned 1), so the
zeros are observations and not an empty-pattern artefact. See
`docs/bl-085-implementation-notes.md` for why a shell-launched run is representative of a
Rig-launched one, and for the structural argument that these keys *cannot* land in `config_json`.

**Confirmed on the real Rig door.** Run `cloudcost-orch-aws--ez4vQ`, 2026-08-04, launched from the
Orchestrator view with `CLOUDCOST_PROVIDER=aws` typed into "Additional env vars" — status `done`,
`output/aws/cloudcost_report_2026-08.html` (13,063 B) produced, authenticated with the read-only
`CLOUDCOST_AWS_*` key. Every value in the stored agent-config map was checked against this run's
trajectory (45,395 B) and `config_json` (4,865 B), not just cloudcost's:

| Stored key | value in trajectory | value in `config_json` |
|---|---|---|
| `CLOUDCOST_AWS_ACCESS_KEY_ID` | 0 | 0 |
| `CLOUDCOST_AWS_SECRET_ACCESS_KEY` | 0 | 0 |
| `CLOUDCOST_DO_TOKEN`, `ANTHROPIC_API_KEY`, `SMTP_PASSWORD`, `GITHUB_*`, `CT_API_TOKEN` | 0 | 0 |
| `CLOUDCOST_AWS_REGION` (not a secret) | 1 | 0 |
| `RunConfig.env` as serialised | `{}` | — |

The single `CLOUDCOST_AWS_REGION` hit is the region string appearing in cost data, and it doubles as
the control: the same method found a value that *is* present, so the zeros above are observations
rather than a matcher that never fires.

**The non-leak criterion — settled wording.** BL-085's original done-check said "`CLOUDCOST_AWS_*`
appears nowhere in the trajectory or `config_json`". That was too broad and is superseded. The
criterion is:

> **No secret *values* in the trajectory or `config_json` — 0/0 across all 22 stored agent-config
> entries. Key *names* may appear only inside the D2 guard warning at
> `cloudcost/scripts/fetch_aws.py:255-259`, where their presence is proof the guard fired on
> actively-present poison.**

The names do appear, twice, and that is expected and wanted:

```
warning: AWS_ACCESS_KEY_ID is set in this environment and is IGNORED; cloudcost authenticates
with CLOUDCOST_AWS_ACCESS_KEY_ID/CLOUDCOST_AWS_SECRET_ACCESS_KEY only.
```

Rig injects the whole agent-config map unfiltered and `api/tools.json` supplies the bare `AWS_*`
rows, so the poison was genuinely in the run's environment; the adapter ignored it and said so. A
guard that names the variable it honoured is evidence, not leakage. A run in which those names were
*absent* while bare `AWS_*` was set would be the finding — it would mean the warning path never
executed.

> **Step 1 no longer times out — BL-096 landed 2026-08-04 (`32933d8`).** `fetch_aws.py` takes
> 63–67 s against the real bill and `run_command`'s default timeout is 60 000 ms
> (`../aetheris/native/aetheris_exec_server/src/main.rs:472`), so STEP 1 used to time out and
> complete only because the model chose to retry at a larger `timeout_ms` — a recovery nothing
> instructed. The orchestrator now declares `fetch_timeout_ms = 300_000` on STEP 1, and the
> acceptance run went from two `fetch_aws` calls with one timeout event to **one call, zero
> timeouts**. A timeout on STEP 1 today is a finding, not the expected noise it was.
>
> The exec-server default is deliberately untouched: a low global default is a fail-fast property
> for every other script in every other use case.

**Interim.** Everything above describes the LLM-planner door, which is what Rig offers today. The
direct, non-LLM launch door is tracked by **BL-094** — it is blocked on a correctness defect
(`mix run` on a config-style `.exs` exits 0 having created no run), not on a missing parameter
concept.

## Adding a provider

A new provider is a new adapter emitting the two frozen normalized schemas (`milestone.md`
§Normalized schemas) using the canonical `type`/`state` vocabulary from `scripts/_normalized.py`,
plus recorded fixtures, plus a clause in the orchestrator's provider `case`.

**The wiring is five places, and they are enumerated here because m3 t2 found them one at a
time:** the provider `case` and the credential raise in `agents/cloudcost_orchestrator.exs`; a
`scripts[]` entry with its `env` rows in `cloudcost/tools.json` (undeclared means an amber badge
in Rig and no config row); the discovery count in `tests/test_tools_manifests.py`; the credential
preflight `case`, the `CC_HERMETIC` strip list and its poison-control arms in
`../aetheris/scripts/sprint.sh`; and a `### <Provider>` posture subsection in this file. Miss the
sprint `case` and the run dies at its `*)` arm on a reason unrelated to the provider; miss the
`CC_HERMETIC` entry and the hermetic proof passes while covering a provider it never tested.

**Declare the fetch step's `timeout_ms` explicitly** (BL-096 convention). STEP 1 is the only step
that calls a live cloud API and the only one whose runtime approaches `run_command`'s 60 000 ms
default. AWS exceeded that default on every run ever recorded and the pipeline survived only
because the model chose to retry — a recovery nothing instructs. STEP 1 is shared across
providers, so the existing `fetch_timeout_ms` declaration already covers a third adapter; the
thing to carry forward is the *habit* of measuring the new adapter's real duration and confirming
the declared value still has margin, rather than inheriting a number and assuming it fits. Linode
is the worked example: measured 4441 ms / 4097 ms, ~73× margin, **recorded and the number left
alone** (m3 t2). Do not
raise the exec-server default to solve this — a low global default is a fail-fast property for
every other script. `detect_orphans.py`,
`compose_report_data.py` and `render_report.py` are provider-agnostic and do not change — m2
tested that claim on AWS and it held, with one deliberate enumerated exception (the named
`region_coverage` field, A4).

**Do not assume the artifact period is the current month.** DO and AWS default to the current UTC
month; Linode does not, because it publishes no preview invoice. Any check that locates an
artifact by building `…_$(date -u +%Y-%m).…` is provider-specific even when it looks generic —
read the period the adapter reports, or glob for what the run wrote.

The `STOPPED_STATES` and `type`-vocabulary seams m1 flagged are closed (m2 t2). Linode was
provider three (m3) and needed **no §Normalized extension** — every in-scope class mapped onto an
existing canonical type. Before provider four,
read **BL-074** — the seam sweep for any remaining value, threshold or spelling a
provider could differ on (rule-catalog age thresholds and the `keep=true` tag spelling are the
named next candidates; Linode confirmed the `keep=true` finding, its tags being flat strings like
DO's) — and **BL-070**, which retires the now-unreachable cross-provider merge
code in `compose_report_data.py`.
