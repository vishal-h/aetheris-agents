# Ticket — fix/docbuilder-currency-rendering

Standalone fix ticket (outside the m1/m2a/m2b milestone structure).

## Problem

The doc-spec column `type: "currency"` is only partially honored by the renderers,
surfaced by the bitloka invoice run (`docbuilder-orch-kQX1xg`):

| Output | Amount cell | Total cell | Issue |
|--------|-------------|------------|-------|
| xlsx | `1,000.00` | `1,000.00` | number format `#,##0.00` — no `$` |
| docx | `1000.00` | `1000` | no currency handling at all |
| pdf (deliverable) | `1000.00` | `1000` | `_table_html` does `esc(value)` — no type formatting |

Goal: a `currency` column shows `$1,000.00` in **all three** outputs, and a plain
`number` column (e.g. `# Resource(s)`) shows `1`, not `1.00`.

## Design note

After `compute_doc`, the cell value is a raw number (or numeric string) — the sum
aggregate yields `1000` (int via `_fmt`), the CSV data cell yields `"1000.00"`
(string). The doc-spec **columns** carry `type`; **cells do not**. Formatting must
happen in the renderer (keyed off the column type by index), not in `compute_doc`.
The renderers must not assume the value is pre-formatted.

## Touches

- `scripts/_format.py` (new) — shared `format_cell(value, col_type)` for the
  text-based renderers: `currency` → `$#,##0.00`, `number` → thousands-separated,
  trailing-zeros stripped (`1`, `1,234.5`). Non-numeric values pass through.
- `scripts/_table_html.py` — zip `row["cells"]` with `sheet["columns"]`; route cell
  values through `format_cell`. Covers PDF narrative (`render_template`) **and**
  structured PDF (`generate_pdf._build_html`) — both call `render_table`.
- `scripts/generate_docx.py` — pass the column type into `_write_cell`; format via
  `format_cell`.
- `scripts/generate_xlsx.py` — currency number format `#,##0.00` → `"$"#,##0.00`;
  plain `number` columns use `#,##0.##` (shows `1`, not `1.00`) instead of `#,##0.00`.
- Tests: `test_format.py` (new) + additions to `test_generate_xlsx.py`,
  `test_generate_docx.py`, `test_render_template.py`; re-run the bitloka invoice.

## Done-check

- `_format.py` unit tests: currency → `$1,000.00`; number `1` → `1`, `1000` → `1,000`.
- xlsx: Amount + Total cells carry the `"$"#,##0.00` format; `# Resource(s)` shows `1`.
- docx: Amount + Total render `$1,000.00`.
- pdf narrative: Amount + Total render `$1,000.00`.
- Full docbuilder pytest suite green; bitloka invoice sprint `done`, PDF shows
  `$1,000.00` line item + Total.
