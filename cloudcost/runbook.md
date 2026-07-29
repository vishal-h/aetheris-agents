# cloudcost — runbook

DigitalOcean cost-report + orphan-detection agent. **Read-only, report-only:** it fetches the
live DO bill and resource inventory, detects wasteful/orphaned resources, and renders a local
HTML report. It never writes to the DO account, mails, or uploads anything (m1 scope).

Design detail and rationale live in `milestone.md` (§Normalized schemas, D1–D6, §Open items);
this file is how to run it.

## Prerequisites

- **`CLOUDCOST_DO_TOKEN`** — a read-only DO Personal Access Token, exported before the run.
  It must be the *only* DO token in the environment: `pydo`/`doctl` and hand-rolled clients
  default to `DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN`, and a stray write token there would shadow
  the read-only one. Verify in a fresh login shell:
  ```
  [ -z "$DO_TOKEN" ] && [ -z "$DIGITALOCEAN_ACCESS_TOKEN" ] && [ -n "$CLOUDCOST_DO_TOKEN" ] && echo ok
  ```
- **`ANTHROPIC_API_KEY`** — for the orchestrator LLM (haiku). Without it the harness silently
  falls back to the stub adapter and produces nothing; confirm real calls in the trajectory
  (`latency_ms` non-zero, `resolved_model` = the haiku model).
- **python3** with `requests` and `Jinja2` (`pip install -r cloudcost/requirements.txt`).

The token gates only the *live* steps; the offline test suite needs none of the above.

## Run it

Full pipeline via the orchestrator (from the harness repo, token already exported):
```
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```
Or the sprint case (same prereqs; clears `output/` first so its checks can't green on a stale
run):
```
cd ~/sandbox/elixirws/aetheris && ./scripts/sprint.sh cloudcost
```
The four stages standalone (from `cloudcost/`, for debugging — the orchestrator just chains
these):
```
python3 scripts/fetch_do.py --output-dir output
python3 scripts/detect_orphans.py output/do_inventory_$(date -u +%Y-%m).json --output-dir output
python3 scripts/compose_report_data.py --cost output/do_costs_$(date -u +%Y-%m).json \
    --inventory output/do_inventory_$(date -u +%Y-%m).json \
    --orphans output/orphan_candidates_$(date -u +%Y-%m).json --output-dir output
python3 scripts/render_report.py output/report_data_$(date -u +%Y-%m).json --output-dir output
```

## Output

`cloudcost/output/cloudcost_report_{YYYY-MM}.html` is the deliverable — a self-contained HTML
report (open in any browser). Alongside it: the intermediate `do_costs_*`, `do_inventory_*`,
`orphan_candidates_*`, and `report_data_*` JSON. `output/` is gitignored.

Period is the current UTC month (`fetch_do.py`'s default).

## Monthly cadence & history

Each run persists its cost snapshot to `cloudcost/history/{YYYY-MM}/` (gitignored). Next
month's run reads the prior month from there to compute the month-on-month delta; the first
run reports "no prior month," which is expected, not an error. History accumulates in
production — do not seed or clear it between real monthly runs. (Tests and the sprint use a
scratch history dir so they stay deterministic.)

## Exercising the ≥1-orphan path

Detection only surfaces what the account actually carries. To test it end-to-end you need a
genuine orphan. Fastest: DO console → **Networking → Reserved IPs → Reserve in Datacenter
Region**, and leave it **unassigned** — that trips `unassociated_reserved_ip` (0.95, HIGH band)
immediately, and costs ~$4.38/mo while it sits. **Delete it after the run** (a write, done by
a human in the console — the agent stays read-only). Note a *freshly created* unattached volume
will not fire for 14 days (the `>14d` threshold), so the reserved IP is the move. Check without
running the whole agent:
```
python3 scripts/fetch_do.py --output-dir /tmp/live
python3 scripts/detect_orphans.py /tmp/live/do_inventory_$(date -u +%Y-%m).json --output-dir /tmp/live
jq '.account, .totals.candidates' /tmp/live/orphan_candidates_$(date -u +%Y-%m).json
```

## Offline tests

```
python3 -m pytest cloudcost/tests/ -v      # no token; recorded DO fixtures
```

## Rig

Runs appear in Harness → Runs automatically; the use case shows in the capability-matrix view
(Rig reads the regenerated `docs/capability-matrix.md`). There is no dedicated cloudcost panel
— that's a separate Rig ticket.

## Adding a provider (fan-out)

A new provider is a new adapter emitting the two frozen normalized schemas (`milestone.md`
§Normalized schemas) plus recorded fixtures; `detect_orphans.py`, `compose_report_data.py`, and
`render_report.py` are provider-agnostic and do not change. Watch the multi-currency and
`STOPPED_STATES` open items in `milestone.md` §Open items before the second provider lands.
