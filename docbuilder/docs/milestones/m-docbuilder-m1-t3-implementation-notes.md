# m-docbuilder-m1 t3 — Implementation Notes

Ticket: t3 — generate_xlsx.py  
Committed: (this session)

---

## What was built

- `scripts/generate_xlsx.py` — xlsx renderer using openpyxl; stdin doc spec,
  `--output-dir` (default `output`), `--filename` (default `document`);
  prints output path to stdout; exit 1 on error
- `tests/test_generate_xlsx.py` — 17 tests (unit + CLI integration)

---

## Design decisions made during implementation

### Numeric string conversion in the renderer

The doc spec carries data-row cell values as strings (passed through from CSV
as-is), while aggregate-row values are Python numbers. For openpyxl to apply
`#,##0.00` number formatting correctly, cell values must be numeric — Excel
treats a string `"250.00"` as text regardless of the `number_format` set.

`_write_cell` converts string values to `float` when the column type is
`"currency"` or `"number"`. Non-convertible strings (e.g., a blank cell in a
numeric column) are left as strings. This is a renderer-side concern; it does
not violate the doc spec contract ("renderers must not compute anything") —
type coercion for correct rendering is not computation.

**Known limitation:** non-convertible strings (e.g. a blank `unit_price` cell)
are silently left as strings. The cell will render as left-aligned text inside
a right-aligned numeric column — a subtle visual defect with no warning.
Consistent with `compute_doc.py` silently skipping non-numeric values in
aggregates. Candidate for a renderer-level stderr warning in m2.

**Note for t4/t5:** The same coercion and the same silent-failure behaviour
applies to any renderer that handles numeric formatting. Each renderer must
handle it independently.

### openpyxl read-back: `250.0` becomes `250`

When openpyxl saves a float whose value equals its integer equivalent
(e.g. `250.0`), it reads back as `int` (`250`). The test assertion uses
`isinstance(value, (int, float))` rather than `isinstance(value, float)`.
This is openpyxl behaviour, not a bug.

### Row placement: `header_row` as anchor

The `rows` array is written sequentially starting at `header_row` (1-based).
`merge_ranges` rows occupy their own physical rows before `header_row` and
are written separately. The renderer does not inspect merge_range row numbers
to determine where to start data rows — `header_row` is the sole anchor.

### Aggregate row border: per-cell, not per-row

openpyxl borders are set per cell. Each cell in an aggregate row receives
a `Border(top=Side(style="thin"))` independently. Cells in non-aggregate rows
receive no explicit border (openpyxl default = no border).

### Merge cell alignment: always center

Merged title cells (from `merge_ranges`) are centered regardless of any
per-column alignment. This matches standard document layout convention.
The `value` field is written to the top-left cell of the merge span only;
openpyxl handles the rest.

### `Workbook.remove(wb.active)` removes the default sheet

A new `Workbook()` always creates a default "Sheet" worksheet. If this is not
removed before creating the named sheets from the doc spec, the output file
contains a spurious empty first sheet. `wb.remove(wb.active)` runs before any
`wb.create_sheet()` calls.

---

## t4/t5 notes

- **python-docx (t4):** Per-cell alignment in python-docx is set via
  `paragraph.alignment` on the cell's paragraph, not on the cell itself.
  The `Pt()` font size and `WD_ALIGN_PARAGRAPH` import are the key ones.
- **weasyprint (t5):** Inline CSS `text-align` and `font-weight: bold` on `<td>`
  elements maps directly to the cell-level `align` and `bold` flags. Column
  widths can be approximated with `style="width: Xem"` on `<col>` elements,
  but weasyprint may not respect them perfectly.
- **Shared pattern:** all renderers convert numeric strings to numbers for
  type-appropriate display. Factor this into t4/t5 independently.
