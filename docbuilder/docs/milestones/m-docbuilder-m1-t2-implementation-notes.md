# m-docbuilder-m1 t2 — Implementation Notes

Ticket: t2 — fetch_data + compute_doc (two-pass engine)  
Committed: (this session)

---

## What was built

- `scripts/fetch_data.py` — reads CSV or JSON by path; `--key KEY` (default `"main"`);
  outputs `{"key": KEY, "rows": [...]}` to stdout; exit 1 on any error
- `scripts/compute_doc.py` — reads template JSON + one raw source JSON; two-pass
  sheet processing; outputs doc spec JSON to stdout; exit 1 on validation errors
- `tests/conftest.py` — adds `scripts/` to `sys.path`
- `tests/test_fetch_data.py` — 8 tests (unit + CLI)
- `tests/test_compute_doc.py` — 24 tests (unit + CLI)
- `docs/doc-spec-schema.md` — complete doc spec format reference for renderer authors

---

## Design decisions made during implementation

### `--key` defaults to `"main"`

The t3+ done-check pipes `fetch_data.py` directly into `compute_doc.py` without
`--key`. Making `"main"` the default means the pipeline works without the flag,
while remaining explicit in the t2 two-step done-check.

### Aggregate values returned as int when integer-valued

`_fmt()` converts a float to int when `val == int(val)` (e.g. `21090.0` → `21090`).
This keeps JSON output clean and avoids renderer float-formatting issues on whole
numbers. Non-integer floats are left as floats.

### `compute_doc.py` accepts `-` as source path

Allows both two-step usage (`fetch_data.py ... > /tmp/raw.json && compute_doc.py ... /tmp/raw.json`)
and piped usage (`fetch_data.py ... | compute_doc.py ... -`). The `-` path reads
from stdin once.

### Aggregate store uses raw rows, not a pre-keyed dict

Instead of pre-computing all `(sheet, column, function)` combinations in Pass 1 and
storing the results, Pass 2 looks up the source sheet's raw rows and re-runs
`_run_aggregate` on demand. This avoids a combinatorial explosion of stored values
(3 functions × N columns per sheet) while keeping the logic simple. The raw rows
are already in memory (Python list), so the re-computation cost is negligible.

### `header_row` is pre-computed in `compute_doc.py`

Per the doc spec contract ("renderers receive pre-computed values and must not
compute anything"), `header_row` is set to `max(merge_range.row) + 1` when merge
ranges exist, or `1` otherwise. Renderers read it directly without scanning
`merge_ranges`.

### Row ordering: `[header] + agg_top + data + agg_bottom`

The `rows` array in each sheet is written in final display order. Renderers iterate
it sequentially — no reordering is needed. `aggregate_rows[].position` is consumed
at compute time; the position field does not appear in the doc spec.

### Column metadata in doc spec is a subset

The doc spec `columns` array carries only `{name, type, width}` — the renderer-
relevant fields. `source_field`, `bold`, and `align` are dropped because those are
per-cell values already encoded in every cell object, not column-level renderer config.

---

## Validation errors enforced

| Error | Exit |
|-------|------|
| `data_sources` has more than one entry | 1 |
| Sheet has both `source_key` non-null and `summary_rows` | 1 |
| `source_key` value not found in provided sources | 1 |
| `source_field` not found in raw data rows | 1 |
| `summary_row.aggregate.source_sheet` not found | 1 |
| `output_formats` contains unknown format | 1 |
| `aggregate_rows[].aggregates[].function` unknown | 1 |
