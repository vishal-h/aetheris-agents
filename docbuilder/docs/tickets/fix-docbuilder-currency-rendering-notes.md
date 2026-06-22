# Implementation notes — fix/docbuilder-currency-rendering

## What shipped

A `currency` doc-spec column now renders `$1,000.00` in **all three** outputs
(xlsx, docx, PDF narrative + structured), and a plain `number` column shows `1`,
not `1.00`. Surfaced by the bitloka invoice run `docbuilder-orch-kQX1xg`.

- **`scripts/_format.py`** (new) — shared display formatter for the text renderers:
  - `format_currency(value)` → `$1,234.56` (2 dp, thousands sep); non-numeric passes through.
  - `format_number(value)` → thousands-separated, trailing zeros stripped (`1`, `1,000`, `1,234.5`).
  - `format_cell(value, col_type)` dispatch: `currency`/`number` formatted, everything
    else (string/None/unknown) falls through to `str(value)` — text renderers behave
    exactly as before for non-numeric columns.
- **`scripts/_table_html.py`** — `render_table` now zips `row["cells"]` with
  `sheet["columns"]` and routes data/aggregate cell values through `format_cell`.
  Header cells are left unformatted (they hold the column name). Covers both PDF
  paths (`render_template` narrative partials **and** `generate_pdf._build_html`
  structured) because both call `render_table`.
- **`scripts/generate_docx.py`** — `_write_cell` takes `col_type` and formats via
  `format_cell`; the row loop passes the column type for data/aggregate rows, `None`
  for headers.
- **`scripts/generate_xlsx.py`** — currency number format `#,##0.00` → `"$"#,##0.00`;
  plain `number` columns use `#,##0.##` (shows `1`, not `1.00`). xlsx keeps native
  Excel number formats — it does not use `_format.py`.

## Design

The doc-spec **columns** carry `type`; **cells do not** (see `compute_doc._cell`).
So formatting is keyed off the column type by index in each renderer. The value
reaching a renderer is raw — a numeric string `"1000.00"` for a CSV data cell, an
int `1000` for a sum aggregate (`_fmt` collapses `1000.0` → `1000`). `_format`
coerces via `float()` and formats; it never assumes a pre-formatted value. This
matches the agreed design note: formatting lives in the renderer layer (shared
helper), not in `compute_doc`.

Header cells are explicitly skipped (a currency-typed header label like "Amount"
would pass through `format_currency` unchanged anyway since it isn't numeric, but
skipping is clearer and avoids surprises).

## Tests

- **`tests/test_format.py`** (new, non-integration) — currency/number/dispatch +
  non-numeric passthrough + None handling.
- **`test_generate_xlsx.py`** — replaced `test_numeric_column_has_number_format`
  (asserted the old `#,##0.00`) with `test_currency_column_has_dollar_number_format`,
  `test_number_column_has_no_forced_decimals`, `test_currency_aggregate_has_dollar_number_format`.
- **`test_generate_docx.py`** — `test_currency_cells_formatted`,
  `test_number_cells_no_trailing_zeros`, `test_header_cells_not_type_formatted`.
- **`test_render_template.py`** — `test_currency_cells_formatted` (raw value must not
  leak; header label not formatted).

Done-check: docbuilder suite 233 passed / 3 skipped (159 non-integration). Bitloka
invoice sprint `docbuilder-orch-B34gfA` → `done`; PDF/docx/xlsx all show `$1,000.00`
line item + Total, resource count `1`.

## Notes

- `format_currency(-50)` → `$-50.00` (not `-$50.00`). Acceptable for this scope; no
  negative-amount use case in the invoice. Note for later if accounting-style
  negatives are needed.
- xlsx number format `#,##0.##` strips trailing zeros at display time but keeps the
  underlying numeric value intact (no data loss).
