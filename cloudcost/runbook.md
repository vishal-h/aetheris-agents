# cloudcost — runbook

Per-provider cost-report + orphan-detection agent, currently **DigitalOcean** and **AWS**.
**Read-only, report-only:** it fetches the live bill and resource inventory, detects
wasteful/orphaned resources, and renders a local HTML report. It never writes to the cloud
account, mails, or uploads anything.

**One provider per run** (m2 decision H). `CLOUDCOST_PROVIDER` selects the pipeline; each run
produces its own report in its own directory. There is no cross-provider run and no combined
report — two providers means two runs.

Design detail and rationale live in `milestone.md` (§Normalized schemas, D1–D6) and
`m2-milestone.md` (decisions A–H); this file is how to run it.

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

Detection only surfaces what the account actually carries, and **neither live account currently
carries an orphan-shaped resource** — the DO reserved IP that used to arm this was deleted
2026-07-30 (BL-069), and the AWS Elastic IP is `m2-milestone.md` §Prereqs 3, still pending. Both
sprint legs therefore report 0 orphans and the `≥1` assertion is expected-red until one is
planted. Do not relax the assertion to make it green; plant the resource.

Both providers trip the **same** rule — t2 unified the vocabulary, so it is
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

Check without running the whole agent (AWS shown; use the DO equivalents for DO):
```
P=$(date -u +%Y-%m)
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE AWS_SHARED_CREDENTIALS_FILE=/dev/null \
    python3 scripts/fetch_aws.py --output-dir /tmp/live
python3 scripts/detect_orphans.py /tmp/live/aws_inventory_$P.json --output-dir /tmp/live
jq '.account, .totals.candidates' /tmp/live/aws_orphan_candidates_$P.json
```

## Offline tests

```
python3 -m pytest cloudcost/tests/ -v      # no credentials; recorded DO + AWS fixtures
```

## Rig

Runs appear in Harness → Runs automatically, one per provider — the run id carries the provider
(`cloudcost-orch-aws-…`, `cloudcost-orch-digitalocean-…`). The use case shows in the
capability-matrix view (Rig reads the regenerated `docs/capability-matrix.md` via
`rig/src-tauri/src/commands/capability_matrix.rs`). There is no dedicated cloudcost panel, and
the report is not yet surfaced against its run — that's BL-073.

## Adding a provider

A new provider is a new adapter emitting the two frozen normalized schemas (`milestone.md`
§Normalized schemas) using the canonical `type`/`state` vocabulary from `scripts/_normalized.py`,
plus recorded fixtures, plus a clause in the orchestrator's provider `case`. `detect_orphans.py`,
`compose_report_data.py` and `render_report.py` are provider-agnostic and do not change — m2
tested that claim on AWS and it held, with one deliberate enumerated exception (the named
`region_coverage` field, A4).

The `STOPPED_STATES` and `type`-vocabulary seams m1 flagged are closed (m2 t2). Before provider
three, read **BL-074** — the seam sweep for any remaining value, threshold or spelling a
provider could differ on (rule-catalog age thresholds and the `keep=true` tag spelling are the
named next candidates) — and **BL-070**, which retires the now-unreachable cross-provider merge
code in `compose_report_data.py`.
