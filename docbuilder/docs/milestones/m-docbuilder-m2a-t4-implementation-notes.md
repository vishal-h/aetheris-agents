# Implementation notes — m-docbuilder-m2a t4

Ticket: `compute_doc.py` multi-source support.

---

## What shipped

- `compute_doc.py`: removed the m1 single-source guard. The script already built
  the `sources` dict from N provided files and looked each sheet's `source_key`
  up in it, so removing the guard is the entire functional change.
- `proposal_v1.json`: added the second `summary` data source (deferred from t1).
- `template-schema.md`: `data_sources` description updated (one-or-more), m1
  constraint note replaced with a multi-source note, validation rules table
  updated (removed the >1-entry rule, added the missing-`source_key` rule).
- Tests: converted the two obsolete guard tests to multi-source success tests,
  added a unit + CLI test for an unprovided `source_key`.
- Full suite: 143 passed (was 141).

---

## Decision — the demo's Summary sheet keeps `summary_rows` (does NOT consume the second source)

The prompt asked me to choose: have the `Summary` sheet consume the `summary`
source directly (`source_key: "summary"`), or keep deriving it from `summary_rows`.

**Chosen: keep `summary_rows`** (Summary stays `source_key: null`). Rationale:
- The `aggregate_ref` rows (Total Line Items = count, Total Value = sum across the
  Line Items sheet) are the demonstration of the **two-pass engine** — the most
  valuable thing the demo template shows. Converting Summary to a flat metric/value
  table from the second source would throw that away.
- It keeps the existing `test_cli_summary_sheet_resolves_aggregates` green (it
  asserts Total Line Items = 10, Total Value = 21090, the Notes static row).
- Genuine two-source consumption is proven directly by the new
  `test_multi_source_two_sheets` (two sheets, each reading a different source).

So the demo **declares** two sources but the demo template only *reads* `main`
(Line Items) — `summary` is declared for the orchestrator to fetch and for the
multi-source plumbing, and is available for a future sheet to consume.

## Why single-source invocations of the two-source template still work

`compute_doc.py` validates only that each sheet's `source_key` is present in the
**provided** sources — it does not require every declared `data_sources` entry to
be provided. So:
- The existing single-source CLI tests (`test_cli_two_sheet_pipeline`,
  `test_cli_line_items_sheet_row_counts`, `test_cli_summary_sheet_resolves_aggregates`,
  and the renderer integration tests) pass only `main` and still succeed: Line Items
  reads `main`, Summary uses `summary_rows` (needs no source), and the declared
  `summary` source is simply not provided in those invocations.
- A declared-but-unconsumed source is allowed by design. A source is only required
  when a sheet's `source_key` names it.

This is the contract: **a `source_key` that names an absent source exits 1; a
declared source that no sheet reads is fine.**

## Tests changed

- `test_multi_source_rejected` → `test_multi_source_two_sheets` (the guard it tested
  no longer exists; now asserts two sheets from two sources resolve correctly).
- `test_cli_multi_source_exits_1` → `test_cli_multi_source_succeeds` (mirrors the
  done-check: demo template + both real sources → 2 sheets).
- Added `test_source_key_not_provided_raises` (unit) and
  `test_cli_unprovided_source_key_exits_1` (CLI) for the new failure mode.

---

## Forward notes

- **t8 orchestrator:** read `data_sources` from the template, call `fetch_data.py`
  once per entry, write each to a temp file, and pass them all to `compute_doc.py`.
  For the demo that is `main` + `summary`. The `summary` file being fetched but not
  rendered into a sheet is intentional (see decision above) — not a bug.
- **Optional future demo enhancement:** add a "Terms" sheet with `source_key:
  "summary"` mapping `metric`/`value`. That would make the second source visibly
  consumed, but changes the locked-in 2-sheet / 2-table assertions across the
  renderer tests, so it is deliberately out of scope for m2a.
- **t5 still owes the pass-through** of `table_style`, `data_col_start`, `narrative`
  from template → doc spec (unchanged by t4).
