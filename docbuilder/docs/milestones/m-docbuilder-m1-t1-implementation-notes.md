# m-docbuilder-m1 t1 — Implementation Notes

Ticket: t1 — Template schema + sample template  
Committed: cbeca3e (2026-06-19)

---

## What was built

- `data/templates/demo/proposal_v1.json` — full-feature demo template (2 sheets)
- `data/sample_data.csv` — 10-row anonymised B2B proposal fixture
- `data/.gitignore` — excludes real client data and real tenant templates
- `docs/template-schema.md` — field-by-field schema reference
- `output/.gitkeep` — commits the output directory

---

## Design decisions made during implementation

### `summary_rows` vs `aggregate_rows` — two distinct sheet types

The t1 prompt specified one sheet that aggregates its own data rows (Line Items)
and one sheet that summarises values from another sheet (Summary). These are
semantically different, and sharing a single key for both would have collapsed that
distinction.

**Decision:** introduce two separate keys in the sheet object:

- `aggregate_rows` — used when `source_key` is non-null; computes sums/counts/avgs
  directly over the sheet's own data rows and appends a row above or below the data.
- `summary_rows` — used when `source_key` is null; each row is either an
  `aggregate_ref` (cross-sheet pointer) or a `static` label/value pair.

Both are documented in `docs/template-schema.md`.

### Two-pass ordering constraint for `compute_doc.py` (t2 impact)

A sheet with `summary_rows` of type `aggregate_ref` references
`aggregate.source_sheet` — the name of another sheet. That source sheet must be
fully processed (data mapped + aggregates computed) before the summary sheet can
be built.

**`compute_doc.py` must process sheets in two passes:**
1. Pass 1 — all sheets where `source_key` is non-null (data-bearing). Compute
   column mapping and all `aggregate_rows` values.
2. Pass 2 — all sheets where `source_key` is null (summary). Build `summary_rows`
   using the aggregate values computed in pass 1.

This constraint is explicit in the t2 ticket scope. Sheets that mix `aggregate_rows`
and `summary_rows` are not valid; `compute_doc.py` should reject them with exit 1.

### `total` column is data, not a derived formula

The sample CSV includes `total` pre-calculated (quantity × unit_price). The template
maps it via `source_field: "total"` — `compute_doc.py` does not need formula
evaluation for m1. Formula support (`derived` field) is deferred to m2 or later.

### `data_sources[].path` is relative to the aetheris-agents sandbox root

`fetch_data.py` will be called with a path argument. The agent's `sandbox_path`
is the aetheris-agents root, so all script-relative paths start there.
The path in the template (`docbuilder/data/sample_data.csv`) reflects this.

---

## t2 prompt additions required (from this ticket)

The t2 milestone prompt must be updated to explicitly cover:

1. **Two-pass sheet processing** — data-bearing sheets (pass 1) before summary
   sheets (pass 2). Use `source_key` as the discriminator.
2. **`summary_rows` handler** — `compute_doc.py` must process both
   `aggregate_rows` (own-data aggregation) and `summary_rows` (cross-sheet
   references + static rows).
3. **Test coverage** — add tests for: summary sheet with `aggregate_ref` rows,
   summary sheet with `static` rows, rejection of a sheet that has both
   `source_key` non-null and `summary_rows` defined.
