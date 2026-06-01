# Phase 6 — Token & Cost Surface

**Goal:** Surface token counts, cost, and usage statistics from instrumented
runs. All data comes from `events.payload_json` via `json_extract` — no
trajectory file reads needed.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Trajectory summary](p6-001-trajectory-summary.md) | — | Token + cost summary bar in the Trajectory tab meta panel |
| 002 | [Usage view](p6-002-usage-view.md) | — | New Harness sidebar section: summary cards + cost-by-model + cost-by-use-case tables |
| 003 | [Diff cost row](p6-003-diff-cost.md) | 001 (shares types) | Add total tokens + cost to the diff metadata table |

001 and 002 are independent. 003 is a one-file change that reuses types
from 001 — implement after 001 is merged.

---

## Completion gate

- Trajectory tab meta panel shows total input tokens, output tokens, and
  cost for the selected run — computed from the already-loaded trajectory,
  no new Tauri command
- Usage section in Harness sidebar shows four summary cards (total spend,
  total runs, total tokens, avg cost/run) and two tables (by model, by
  use case)
- Diff metadata table includes total tokens and cost rows for both runs
- Runs with no instrumented events show `—` not `$0.00` or an error
- All values in USD, 4 decimal places for cost (`$0.0155`)
- `cargo build` exits 0, zero warnings
- `bun run build` exits 0, zero TypeScript errors

---

## Key decisions

**No new data source for trajectory summary (p6-001).** The trajectory is
already loaded in `useTrajectory`. Token counts and cost are in the
`llm_responded` event payloads — compute the summary client-side from the
events array. No new Tauri command needed.

**SQLite `json_extract` for usage stats (p6-002).** The `events` table has
`payload_json` as a text column. `json_extract` is available and confirmed
working. Usage stats require a new Tauri command `usage_stats_load` that
runs two aggregate queries against `aetheris.db`.

**Use-case grouping from run label prefix (p6-002).** Same prefix logic as
the run list grouping — `payslip`, `drive`, `email`, `api-tenant`,
`api-gateway`, `provenance`, `cap-matrix`. Labels that don't match go to
`Unclassified`. Computed in Rust, not re-derived on the frontend.

**Pre-instrumentation caveat.** Runs before the harness token/cost change
have `NULL` for `cost_usd`, `input_tokens`, `output_tokens` in their
`llm_responded` events. `json_extract` returns `NULL` for these — the SQL
`WHERE ... IS NOT NULL` filter excludes them from aggregates. The usage view
shows a note: "Data available from instrumented runs only."

**Cost format: `$0.0155` (4 decimal places).** Small runs are sub-cent —
rounding to 2dp loses meaningful precision. Use `$` prefix, 4dp, no
thousands separator for cost values under $1. For totals over $1, use
standard 2dp (`$1.24`).

**USD only.** No currency toggle for now. Field is `cost_usd`, display is
always `$`. INR conversion is a future display-time concern.
