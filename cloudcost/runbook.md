# cloudcost — runbook

Per-provider cost-report + orphan-detection agent, currently **DigitalOcean**, **AWS**,
**Linode** and **GitHub**.
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
  (`../aetheris/scripts/sprint.sh`, the `cc_hermetic` function), so a sprint leg cannot
  accidentally exercise an ambient token.

- **Endpoint redirection — a hazard neither predecessor has.** `LINODE_CLI_API_HOST`,
  `LINODE_CLI_API_VERSION` and `LINODE_CLI_API_SCHEME` are read by `linode-cli` and redirect
  *where a credential is sent*. The adapter constructs its own base URL and never reads them as
  configuration — it **warns** when they are set.

  **Changed 2026-08-06 (m4 t3).** These used to be deliberately *left unstripped* by the sprint's
  hermetic prefix, so that the adapter would see them and warn. Since the prefix became
  default-deny they **are** stripped, like everything else not on its allowlist — so a sprint leg
  cannot have its credential redirected, and the adapter never sees them and never warns. The
  signal is not lost: **the sprint now checks your ambient environment and warns before the
  strip**, naming any shadow or redirect variable it finds (names only, never values):

  ```
  [WARN]  ambient credential-shadow/redirect names set: LINODE_CLI_API_HOST — the prefix
          strips them so this run is unaffected, but your shell still carries them
  ```

  If you see that line, the run was safe and your **workstation** is the thing to clean up. Note
  that a **standalone** adapter invocation (below) does not go through the prefix, so there the
  adapter's own warning still applies and the redirect is live.

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

### GitHub

- **`CLOUDCOST_GITHUB_TOKEN`** — a read-only fine-grained personal access token, scoped to the
  organisation being billed. Two **Organization permissions**, and nothing else:

  | Read-only | Why |
  |---|---|
  | Administration | the billing surface — `/organizations/{org}/settings/billing/usage` and its `/summary` sibling. There is no separate Billing permission |
  | Copilot Business | `/orgs/{org}/copilot/billing/seats`, the whole inventory |

  **Both were read off the API rather than inferred**: GitHub states the permission each
  endpoint accepts in an `x-accepted-github-permissions` response header —
  `organization_administration=read` on the billing endpoints, and
  `organization_copilot_seat_management=read; organization_administration=read` on the seats
  endpoint. Grant Copilot Business rather than leaning on Administration for both, so the
  inventory keeps working if the billing grant is ever narrowed.

  `fetch_github.py` authenticates with this variable and **only** this one. It builds the
  `Authorization` header itself and there is no default-pickup arm to disable — unlike boto3's
  credential chain, there is nothing to neutralise, only something never to consult.

- **`CLOUDCOST_GITHUB_ORG`** *(optional)* — the organisation login. `--org` beats it, and if
  neither is set the adapter reads `/user/orgs` and uses the token's **sole** membership. It
  refuses to choose: no membership and more than one both raise, naming the flag. A token
  belonging to two organisations would otherwise bill the wrong one silently.

- **The credential file and the `set -a` load requirement.** The token lives in
  `~/.secrets/github-cloudcost.env`. Load it **exported**:
  ```
  set -a; source ~/.secrets/github-cloudcost.env; set +a
  ```
  This is the same trap the AWS section records above, and it bites the same way.

- **Shadowing — and this is the first provider where the shadowed names are normally PRESENT.**
  `gh` is installed on developer workstations and CI runners alike and reads **`GH_TOKEN`** then
  **`GITHUB_TOKEN`** for github.com, and **`GH_ENTERPRISE_TOKEN`** then
  **`GITHUB_ENTERPRISE_TOKEN`** for a GitHub Enterprise Server host — its own precedence order,
  from `gh help environment`. **`GITHUB_PERSONAL_ACCESS_TOKEN`** is read by none of them and is
  warned about because it is a conventional spelling users export. The adapter reads none of the
  five and warns when any is set. On a workstation with `gh` configured this warning is routine
  rather than exceptional, and the shadowing token is typically a **broader-scoped write**
  credential than the read-only one here — which is what makes the refusal load-bearing:
  ```
  warning: GITHUB_TOKEN is set in this environment and is IGNORED; cloudcost
           authenticates with CLOUDCOST_GITHUB_TOKEN only.
  ```
  `GH_CONFIG_DIR` is deliberately **not** on that list: it redirects which *stored* credential
  gh picks up, and this adapter reads no credential store.

- **Endpoint redirection.** **`GH_HOST`** (gh's own — *"if this host was previously
  authenticated with, the stored credentials will be used"*) and **`GITHUB_API_URL`** (read by
  `@actions/github`, not by gh) redirect *where a credential is sent*. The adapter constructs
  its own base URL and never reads them as configuration — it warns when they are set. Same
  class as Linode's `LINODE_CLI_API_*`.

- **The cost figure is checked against a second endpoint on every run.** The snapshot is built
  from the billing usage *summary* endpoint and reconciled against the *detail* endpoint, which
  must agree to within one hundredth (`m6-github.md` **D7**). A divergence **withholds the cost
  snapshot** — the inventory is still written, the run is `partial` and exits 1. That is louder
  than the Linode arm, which warns; the reason is that agreement between the two endpoints is
  the whole ground on which the summary endpoint was chosen as the source.

- **An empty month writes no cost file, and that is not a failure of the credential.** A month
  the organisation predates returns HTTP 200 with the period correctly echoed and no usage rows.
  The adapter refuses to write a `0.00` snapshot for it, because a bill of zero and no spend
  recorded are different claims. The inventory is still written.

- **GitHub is wired into the pipeline (m6 t2b).** `CLOUDCOST_PROVIDER=github` selects the
  adapter, `tools.json` declares it, and the sprint's cloudcost case runs a GitHub leg. Run it
  the same way as any other provider — see §Run it. The adapter can still be invoked directly,
  which is how a period other than the current month is fetched:
  ```
  set -a; source ~/.secrets/github-cloudcost.env; set +a
  cd ~/sandbox/elixirws/aetheris-agents
  python3 cloudcost/scripts/fetch_github.py --period 2026-07 --output-dir cloudcost/output
  ```
  **No orphan rule keys on `seat` yet (m6 t3).** The rule catalog's rules are all keyed on
  infrastructure types, so a GitHub run evaluates its seats against rules none of which can
  match and reports zero orphan candidates. That is the catalog reading the inventory
  correctly, not failing to — the rule-legibility arm is what distinguishes the two.

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

**GitHub** (m6 t2b) — same shape again, and the one provider whose shadow names are normally
*present* rather than exceptional, because `gh` is installed:
```
cd ~/sandbox/elixirws/aetheris
set -a; source ~/.secrets/github-cloudcost.env; set +a
CLOUDCOST_PROVIDER=github \
env -u GH_TOKEN -u GITHUB_TOKEN -u GITHUB_PERSONAL_ACCESS_TOKEN \
    mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```
Selecting GitHub without `CLOUDCOST_GITHUB_TOKEN` raises at agent-eval time, same posture as
AWS and Linode. **`CLOUDCOST_GITHUB_ORG` is optional and worth setting anyway** if the token
could ever reach a second organisation: unset, the adapter discovers the organisation from the
token's sole membership, and a token that later gains a second membership makes the run raise
rather than guess — but a token whose *single* membership is not the organisation you meant
bills the wrong one silently. Naming it is the cheap way to make that a configuration error
rather than a wrong report.

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
./scripts/sprint.sh cloudcost                            # DigitalOcean
CLOUDCOST_PROVIDER=aws ./scripts/sprint.sh cloudcost     # AWS (applies the prefix itself)
CLOUDCOST_PROVIDER=linode ./scripts/sprint.sh cloudcost  # Linode
CLOUDCOST_PROVIDER=github ./scripts/sprint.sh cloudcost  # GitHub
```

**What the sprint passes to the run — an allowlist, since m4 t3.** The prefix used to *unset named
hazards* and pass everything else. It is now **default-deny**: the run starts from nothing and
receives only these, and anything else you have exported does **not** reach it.

| Passed through | Why |
|---|---|
| `PATH`, `HOME` | nothing runs without them |
| `LANG` | without a UTF-8 locale the BEAM writes non-ASCII in the `--json` payload as invalid UTF-8, silently (BL-112) |
| `ANTHROPIC_API_KEY` | the run's LLM call |
| `CLOUDCOST_OPTIMIZATION` | its fail-fast guard silently stops firing otherwise |
| the selected provider's credential | read from the adapter itself, so this table cannot drift from it |
| `CLOUDCOST_AWS_REGION`, `CLOUDCOST_AWS_REGIONS`, `CLOUDCOST_GITHUB_ORG` | your documented operator knobs, which would otherwise be stripped and ignored **without any error** |

The knob row is the one that *can* drift, and did: it is selected by a list of constant **names**
in the bridge (`KNOB_CONSTANTS`), so an adapter declaring a knob under a name that list does not
carry is stripped silently. `CLOUDCOST_GITHUB_ORG` was in exactly that position until m6 t2b.

Plus two values the prefix *sets*: `CLOUDCOST_PROVIDER`, and `AWS_SHARED_CREDENTIALS_FILE=/dev/null`
— the latter explicitly, because merely *removing* it would restore boto3's default
`~/.aws/credentials` lookup rather than disabling it.

**The practical consequence for you:** if you add a new `CLOUDCOST_*` knob and the sprint appears
to ignore it, it is not being ignored — it is not reaching the run. Declare it on the adapter
under a constant name `KNOB_CONSTANTS` carries, in `../aetheris/scripts/sprint.sh`; adding the
variable to `CC_ALLOW` by hand works too but re-introduces the hand-typed copy the selection
exists to avoid. Standalone invocations (below) are unaffected; they inherit your shell as they
always did.

The four stages standalone (from `cloudcost/`, for debugging — the orchestrator just chains
these). Substitute the adapter and the provider slug for another pipeline — `fetch_aws.py` / `aws`,
`fetch_linode.py` / `linode`, `fetch_github.py` / `github` — and read the artifact names the
adapter prints rather than constructing them, since not every provider's period is the current
month:
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

## What a zero-orphan account means, and what the sprint asserts instead

**A zero is the desired state, not a gap.** Detection only surfaces what the account actually
carries, and none of the four live accounts currently carries an orphan-shaped resource. That is
what a well-kept account looks like.

**GitHub's zero is the first one that is a measurement rather than an absence of coverage**
(m6 t3, 2026-08-14). Until t3 the catalog had no rule keying on `seat`, so a GitHub run reported
zero candidates because nothing could evaluate its six resources. It now has one — a seat
unexercised for more than **30 days** — and the run still reports zero: the stalest of the six
seats was last used 8 days before the run. Read that as *this organisation's Copilot seats carry
no recoverable spend today*, which is a different statement from the one the same figure made a
day earlier. The threshold is tunable per run with `--seat-inactive-days N` on
`detect_orphans.py` (default 30, GitHub's own published figure for an inactive licence); it is
the only knob besides `--snapshot-age-days`, and lowering it to make a candidate appear tells you
nothing the timestamps do not already say.

**Do not create a resource to make a check fire.** Until 2026-08-06 the sprint asserted
`orphan candidates ≥ 1`, and this section was a recipe for planting the billable resource that
would satisfy it — a DO reserved IP, an AWS Elastic IP, a zero-backend Linode NodeBalancer,
created by hand before the run and deleted after. **The practice is retired on every provider**
(`m4-consolidation.md` §Ratified decisions → Technical, decision 12; BL-069 closed by retirement
at m4 t2). An assertion that can only be satisfied by spending money is not a check on the
pipeline; it is a standing instruction to keep waste on the account.

**What replaced it: a rule-legibility assertion**, in the same sprint case
(`../aetheris/scripts/sprint.sh`, the cloudcost block). It asserts the property the ≥1 tripwire
was standing in for — that the adapter's inventory **reached the rule catalog in a shape the
catalog could read**:

- every `type` the adapter emitted is drawn from the canonical closed set, imported from
  `scripts/_normalized.py` (`CANONICAL_TYPES`) rather than restated in the sprint — this is the
  provider-vocabulary-reaching-shared-machinery seam (BL-074), which is where this use case's
  defects have actually come from;
- the catalog skipped nothing as illegible, and its own resource count agrees with the inventory
  it read.

It needs no live resource, so it runs on every leg for free. **A zero-resource inventory reaches a
stated not-applicable arm, never a pass** — one provider's account legitimately inventories
nothing, and that is neither a legibility pass nor a legibility failure.

> **The not-applicable arm reports an unknown, and says so.** Whether the adapter's *coverage* was
> complete is recorded in no artifact the sprint can read: the inventory envelope is five keys and
> carries no `not_inventoried` (BL-098), and the adapter's summary — which does carry it — dies at
> its own stdout. So a zero cannot be read as "the account is clean"; it is read as "nothing was
> evaluated, and why is not established here". Re-run the adapter directly (below) and read its
> `status` and `not_inventoried` if you need that answer today.

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

**The wiring places are enumerated here because m3 t2 found them one at a time:** the provider
`case` and the credential raise in `agents/cloudcost_orchestrator.exs`; a `scripts[]` entry with
its `env` rows in `cloudcost/tools.json` (undeclared means an amber badge in Rig and no config
row); the discovery count in `../tests/test_tools_manifests.py` — the **repo root** `tests/`, not
`cloudcost/tests/`; the credential preflight `case`, **the `MODULES` map in the adapter env
bridge and that bridge's `KNOB_CONSTANTS`** in `../aetheris/scripts/sprint.sh`; a
`### <Provider>` posture subsection in this file; and **every prose enumeration of the provider
set** — this file's opening sentence, `cloudcost/tools.json`'s top-level `description`, the
orchestrator's header comment, and `sprint.sh`'s usage headers. Miss the sprint `case` and the run
dies at its `*)` arm on a reason unrelated to the provider.

> **Changed 2026-08-13 (m6 t2b), by the first ticket to follow this list since the defects were
> recorded.** Two repairs and two additions. **Repaired:** the manifest-test path did not resolve
> from this file's own directory (`cloudcost/tests/` holds no such file; it is at the repo root),
> and the lead-in asserted a *count* of places that its own enumeration disagreed with — now
> de-numeralised, because the list enumerates the places and a number in the prose is a second
> surface that can drift from it (m6 t1's rule). **Added:** `KNOB_CONSTANTS`, and the prose
> enumerations. The knob addition is the substantive one — GitHub's optional `CLOUDCOST_GITHUB_ORG`
> is declared on the adapter as `ORG_ENV`, which the bridge's `KNOB_CONSTANTS` did not name, so the
> default-deny prefix stripped it and the adapter fell through to sole-membership discovery. That
> is not degraded operation: where discovery resolves to an organisation other than the configured
> one, the run bills the wrong organisation and nothing downstream can tell.

> **Changed 2026-08-06 (m4 t3).** This used to read *"the `CC_HERMETIC` strip list and its
> poison-control arms"*, and warned that missing an entry there would leave the hermetic proof
> *"passing while covering a provider it never tested"*. **That entry no longer exists.** The
> prefix is default-deny, so there is nothing provider-specific to unset; the poison control
> proves a structural property that covers every provider at once; and the credential names come
> from the adapter module rather than from a list in the sprint. Six per-provider arms became
> three provider-agnostic ones.
>
> **What replaced it is smaller but not nothing**, and is named above so it is not rediscovered:
> the bridge maps a provider to its adapter module (`digitalocean → fetch_do`, and the DO case is
> why that map cannot be derived from the provider name). A provider missing from it fails
> **loudly** at the `could not read … credential env names from its adapter` preflight, before any
> run — unlike the old strip list, whose omission was silent. Filed as **BL-113**: the map is
> keyed on constant *names*, so an adapter adding a credential under a new constant is still
> missed silently.

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
existing canonical type. **BL-074's seam sweep is done** — closed 2026-08-07, its output the
54-item census and `cloudcost/milestone.md` §Contracts (C1–C15). Before provider four, read
**§Contracts**, not the row: it is where the sweep's rulings live, and the adapter obligations a
fourth adapter must meet are stated there per contract. The candidates the row named are ruled —
the rule-catalog age thresholds and the `keep=true` tag spelling among them; Linode confirmed the
`keep=true` finding, its tags being flat strings like DO's.
*(Corrected gc t3, 2026-08-12 — this read "Before provider four, / read **BL-074** — the seam
sweep for any remaining value, threshold or spelling a provider could differ on (rule-catalog age
thresholds and the `keep=true` tag spelling are the named next candidates; …)". BL-074 had closed
five days before that sentence was last read, so it sent an adapter author to an open row that was
shut. Corrected in place under hc decision 8, live operational guidance.)*

**BL-070's cross-provider deletions are not taken** *(corrected m5 t2, 2026-08-10 —
this sentence read "and **BL-070**, which retires the now-unreachable cross-provider merge
code in `compose_report_data.py`")*. That merge code is **reachable and uninvoked, not
unreachable**: three routes reach it and no orchestrator invocation takes any of them, so
nothing about provider four brings it into the pipeline. **m5-D2**
(`cloudcost/m5-n1-compose.md` §Ratified decisions) retains it as a library-and-CLI
capability the pipeline does not invoke, and requires it to say so — which
`compose_report_data.py`'s module docstring and §Contracts C4 and C11 now do.
