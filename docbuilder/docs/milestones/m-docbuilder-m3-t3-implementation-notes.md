# Implementation notes — m-docbuilder-m3 t3

Ticket: `resolve_last_run.py` (deterministic "same as last month" + FY invoice increment)
+ `context_builder.exs` prompt edit to call it.

---

## What shipped

- **`scripts/resolve_last_run.py`** (new) — finds the most recent run-log entry matching
  `{tenant, doc_type, client_name}`, copies its context, and produces the next period's
  context deterministically:
  - `date` → month-end of the target month (`DD-Mon-YYYY`, e.g. `30-Jun-2026`).
  - `invoice_number` → `{FY}/{client_code}/{seq+1}`; FY code = last two digits of each
    year, rolling April 1 (`fy_code(2026,6) → "2627"`, `fy_code(2026,3) → "2526"`);
    `seq+1` preserves zero-pad width and does **not** reset on FY change (per spec).
  - `title` → the old invoice-number substring is replaced with the new one.
  - all other fields carried verbatim (client_*, order_ref, order_effective_date, terms,
    amount_due).
  - importable helpers (`fy_code`, `month_end`, `bump_invoice_number`, `find_last_match`,
    `resolve`) for direct unit testing.
- **`agents/context_builder.exs`** — prompt-only edit (run_command was added in t2/F1):
  RECURRING requests ("same as last month") now call `resolve_last_run.py … --output
  output/confirmed_context.json`; the agent reads the file back and presents it without
  touching the date/invoice math. FRESH requests still build from the request (3b).
  On `{"status": "no_prior_run"}` the agent falls back to the fresh path.
- **`docs/m3-milestone.md`** — corrected the FY-code formula in the design-decisions
  table (the original `{year}{(year+1)%100:02d}` shorthand would have produced `202627`;
  the data-true form is `{start%100:02d}{end%100:02d}` → `2627`, matching the committed
  `2627/XYZ/02`).

---

## Design decisions

- **Match semantics.** `{tenant, doc_type}` exact; `client_name` case-insensitive with
  bidirectional substring ("XYZ" matches "XYZ Inc") so the agent can pass the client as
  named in the request. "Most recent" = max timestamp, tie-broken by array order — robust
  to the t1 idempotency-as-replace behaviour (a replaced entry moves to the array end).
- **Degrade vs hard-fail.** No matching prior run → `{"status": "no_prior_run"}`, exit 0
  (a valid outcome; the agent falls back). Unparseable existing invoice number → warn to
  stderr, leave it unchanged, still bump the date, exit 0. Hard errors (exit 1): malformed
  `--target-month`, unreadable/non-array run log (reuses `run_log_writer._load_log`).
- **Script owns the math; the LLM only orchestrates.** The script writes
  `confirmed_context.json` directly via `--output`; the agent reads it back to present.
  Verified by byte-identical diff (agent output == direct script output) — no LLM value
  computation, consistent with "scripts do, agents decide" and the m2a no-blob-roundtrip
  learning.
- **Target month** defaults to the current calendar month when `--target-month` is
  omitted (the implicit "same as last month → this month"); an explicit "for June 2026"
  becomes `--target-month 2026-06`.

---

## Done-check

- `test_resolve_last_run.py`: **31 passed** — fy_code (incl. April-1 boundary + next FY),
  month_end (incl. leap Feb), bump_invoice_number (basic / March→April FY rollover /
  pad-width / unparseable), find_last_match (exact / substring / wrong client / wrong
  doc_type / latest-by-timestamp), resolve (bump+carry / no-match / unparseable-warns /
  no-mutate), CLI (output-file / stdout / no_prior_run / missing-log / bad-month / corrupt-log).
- Full docbuilder suite: **287 passed, 3 skipped**.
- `context_builder.exs` eval: EXIT 0.
- End-to-end `docbuilder-ctx-0nDlug` → **done**. Request "Invoice for XYZ for June 2026,
  same as last month" → `confirmed_context.json` with `date 30-Jun-2026`,
  `invoice_number 2627/XYZ/03`, title updated, client fields carried — **byte-identical**
  to `resolve_last_run.py` run directly (script did the math).

---

## Forward to later m3 tickets

- **t4** — orchestrator reads `output/confirmed_context.json`; sprint case
  `docbuilder_context` chains context_builder → orchestrator end-to-end.
- **t5** — capability matrix: add `resolve_last_run.py` + `run_log_writer.py` (→ 20
  scripts) and `context_builder.exs` (→ 2 agents); confirm `_format.py` already present.
- Explicit field overrides on a recurring request ("same as last month but amount $2,000")
  are not handled by the resolver (it does base resolution only) — a future enhancement;
  out of t3 scope.
