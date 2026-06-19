# m-docbuilder-m1 t5 — Implementation Notes

Ticket: t5 — generate_pdf.py  
Committed: (this session)

---

## What was built

- `scripts/generate_pdf.py` — PDF renderer using weasyprint; builds an HTML
  intermediate from the doc spec, then calls `weasyprint.HTML(string=html).write_pdf()`;
  stdin doc spec, `--output-dir` (default `output`), `--filename` (default `document`);
  prints output path to stdout; exit 1 on error
- `tests/test_generate_pdf.py` — 13 tests (8 HTML unit tests + 2 PDF rendering
  integration + 3 CLI integration)

---

## Design decisions made during implementation

### HTML as intermediate representation

The full rendering pipeline is:
```
doc spec JSON → _build_html() → HTML string → weasyprint → PDF bytes → file
```

`_build_html()` is a pure function (no I/O) and is tested independently of PDF
rendering. This splits the test suite cleanly: HTML unit tests run without
weasyprint doing any rendering (fast); integration tests run the full PDF path.

### merge_ranges expressed faithfully via `<th colspan="N">`

Unlike xlsx (merged cells) and docx (silently substituted with sheet name),
HTML can express the merge_range `value` text faithfully using
`<th colspan="N">`. The merge_range value ("B2B Project Proposal — Line Items")
is written to the HTML, not the sheet name ("Line Items").

This was flagged in the t4 implementation notes as the key t5 design decision
to make deliberately. It resolves the per-renderer divergence: xlsx = correct,
docx = sheet name substituted, **pdf = correct** (merge_range value preserved).

The `<th colspan>` rows are inserted before the `rows` array in the `<table>`,
matching the physical row ordering of the doc spec (`merge_ranges` rows occupy
rows before `header_row`).

### Aggregate row via CSS class, not inline border

Aggregate rows receive `class='aggregate'` on the `<tr>`. The stylesheet rule
`tr.aggregate td { border-top: 2px solid #444; }` applies the top border to
all cells in aggregate rows. This is cleaner than per-cell inline style and
lets weasyprint apply it consistently across the row.

### All values serialised via `str()` — same as docx

HTML is string-based; no numeric type coercion is needed. `_esc(value)` calls
`str(value)` then `html.escape()`. The silent-coercion limitation from t3
(xlsx) does not apply here — any value displays as its string representation.
The t3 known limitation (blank numeric cell → wrong styling) also does not
apply: all cells look the same regardless of type.

### HTML escaping via `html.escape()`

`_esc()` wraps every value in `html.escape()` to prevent XSS in the HTML
intermediate. This matters if doc spec values ever contain `<`, `>`, `&`, or
`"`. The em-dash in the demo merge_range value ("—") is a Unicode character
and passes through correctly; `html.escape()` only escapes the five special
HTML characters.

### weasyprint 69.0 — no significant gotchas

weasyprint 69.0 renders the HTML + inline CSS correctly. `write_pdf()` accepts
a string path. No special font configuration was needed for the sample output.
PDF output is ~14K for the 2-sheet proposal, which is reasonable.

---

## t6 notes

- t6 renderers (csv, json, xml, md) are all stdlib — no external deps needed.
- All four use the same stdin + `--output-dir` + `--filename` interface.
- For `generate_json.py`: the spec says "strip formatting metadata — consumers
  want clean data." Output should be the data arrays only, not the full doc spec
  with bold/align flags.
- For `generate_csv.py`: multi-sheet output needs a separator between sheets.
  A blank line + `# Sheet: {name}` comment before each sheet's rows is the
  specified format.
- For `generate_xml.py`: use `xml.etree.ElementTree`; each `<cell>` holds the
  string value only (no bold/align in the XML output).
- For `generate_md.py`: `**{value}**` wrapping for bold cells; the header row
  separator (`| --- | --- |`) goes between the header row and the first data
  row.
