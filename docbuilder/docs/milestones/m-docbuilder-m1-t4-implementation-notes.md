# m-docbuilder-m1 t4 — Implementation Notes

Ticket: t4 — generate_docx.py  
Committed: (this session)

---

## What was built

- `scripts/generate_docx.py` — docx renderer using python-docx; stdin doc spec,
  `--output-dir` (default `output`), `--filename` (default `document`);
  prints output path to stdout; exit 1 on error
- `tests/test_generate_docx.py` — 17 tests (unit + CLI integration)

---

## Design decisions made during implementation

### Document structure: title → sheet heading → table

python-docx builds a linear paragraph stream. The output structure is:

```
Title heading (level=0)  ← doc_spec["title"]
Sheet heading (level=1)  ← sheet["name"]
Table (rows × cols)
Sheet heading (level=1)
Table
...
```

Tables are accessed via `doc.tables[i]`, which maps cleanly to sheet index.
Paragraphs (headings) do not appear in `doc.tables`, so `len(doc.tables) == len(sheets)` is a clean assertion.

### Per-cell alignment via `paragraph.alignment`

python-docx alignment is a paragraph-level property, not a cell-level one.
`cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.{LEFT|RIGHT|CENTER}`.
The `ALIGN_MAP` dict translates doc spec strings to `WD_ALIGN_PARAGRAPH` enum values.

### All values serialised to `str()`

Unlike xlsx (where numeric types are needed for `number_format`), docx cells
hold text. Every cell value is written as `str(value)`. There is no numeric
coercion in this renderer — int `400` becomes `"400"`, float `21090.0` would
become `"21090.0"`. For the current sample data, aggregate values are already
integers (via `_fmt()` in `compute_doc.py`), so the output is clean.

If `compute_doc.py` ever emits floats for aggregates, they would display as
`"21090.0"` rather than `"21090"` or `"21,090.00"`. The t3 notes named this
as a known limitation; in docx the same limitation exists but manifests
differently (wrong display string rather than wrong cell type).

### Table style: "Table Grid"

"Table Grid" is a built-in Word style that draws visible borders on all cells.
Without a style, tables have no visible borders, which makes the output hard
to read. "Table Grid" is universally available and appropriate for tabular data.

### `table.rows[i].cells[j]` — no index error on empty rows

`doc.add_table(rows=N, cols=M)` pre-allocates all rows. Accessing `rows[i]` is
safe for any 0 ≤ i < N. No dynamic `add_row()` calls needed.

### No merge_ranges in docx

The doc spec includes `merge_ranges` for merged header cells (used in xlsx).
python-docx can merge cells with `table.cell(r1,c1).merge(table.cell(r2,c2))`,
but the doc spec's `merge_ranges` refer to pre-data rows (e.g. a title row above
the column headers). In a Word document these are better represented as a
heading paragraph above the table, which is what the sheet-level `add_heading`
already provides. `merge_ranges` are silently ignored in this renderer — the
semantic equivalent (a title above the table) is handled by the heading. This
is a deliberate simplification.

**Known limitation (flag for t8 docs sync):** the heading text used is
`sheet["name"]` (e.g. "Line Items"), not the `merge_ranges[].value` (e.g.
"B2B Project Proposal — Line Items"). These are different strings. Template
authors who rely on the merge_range value appearing as the table title in docx
output will be surprised. xlsx faithfully renders the merge_range value; docx
substitutes the sheet name. t5 (HTML) is the only renderer that can express
merge_range values faithfully via `<th colspan="N">`.

---

## t5 notes

- weasyprint (t5) renders from HTML, so alignment is inline CSS (`text-align`)
  and bold is `font-weight: bold` — much simpler than python-docx.
- merge_ranges can be represented in HTML as `<th colspan="N">` — the only
  renderer where they can be naturally expressed without special-casing.
- The `str()` coercion pattern from this renderer applies equally to the HTML
  string-building in t5.
