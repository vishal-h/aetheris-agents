# m-docbuilder-m1 t6 — Implementation Notes

Ticket: t6 — generate_csv.py, generate_json.py, generate_xml.py, generate_md.py  
Committed: (this session)

---

## What was built

- `scripts/generate_csv.py` — CSV renderer using stdlib `csv`; single-sheet output omits separator; multi-sheet output writes blank line + `# Sheet: {name}` comment before each sheet's rows
- `scripts/generate_json.py` — JSON renderer; strips bold/align metadata; outputs `{"title", "sheets": [{"name", "columns": [string, ...], "rows": [[value, ...], ...]}]}`
- `scripts/generate_xml.py` — XML renderer using `xml.etree.ElementTree`; `<document title="..."><sheet name="..."><row type="..."><cell>value</cell>...`
- `scripts/generate_md.py` — Markdown renderer; `# title`, `## sheet_name`, pipe table rows, `**value**` for bold cells, `| --- | --- |` separator immediately after header row
- `tests/test_generate_csv.py` — 10 tests (8 unit + 2 CLI integration)
- `tests/test_generate_json.py` — 11 tests (9 unit + 2 CLI integration)
- `tests/test_generate_xml.py` — 12 tests (10 unit + 2 CLI integration)
- `tests/test_generate_md.py` — 11 tests (9 unit + 2 CLI integration)

All four renderers: stdin doc spec JSON, `--output-dir` (default `output`), `--filename` (default `document`), print output path to stdout, exit 1 on error.

---

## Design decisions made during implementation

### No external dependencies

All four renderers use only stdlib: `csv`, `json`, `xml.etree.ElementTree`, and string formatting. No third-party installs needed. This contrasts with t3 (openpyxl), t4 (python-docx), and t5 (weasyprint).

### CSV: multi-sheet separator format

Single-sheet output has no separator at all — adding a `# Sheet:` comment when there is only one sheet adds noise for consumers that never need it. Multi-sheet output precedes each sheet's rows with a blank line and a `# Sheet: {name}` comment. The blank line is written using `buf.write("\n")` before the comment for i > 0 (not after the previous sheet's rows), ensuring there is exactly one blank line between sheets, not two.

### JSON: metadata stripped at output, not at input

`generate_json()` receives the full doc spec (with bold/align) and strips the formatting keys at write time by building the output dict from scratch (`columns` becomes a list of column name strings, `rows` becomes a list of value-only arrays). The input doc spec is not mutated. `template_id` and `output_formats` are also excluded — the output JSON contains only `title`, `sheets`, and within each sheet `name`, `columns`, `rows`. Consumers get clean data with no renderer-specific metadata.

### XML: `ET.indent()` for human-readable output

Python 3.9+ `ET.indent(tree, space="  ")` adds whitespace text nodes for indentation before `tree.write()`. The output is readable without any post-processing. `xml_declaration=False` keeps the preamble out; adding it would require specifying encoding and version, which is unnecessary for UTF-8 string output. ElementTree escapes `<`, `>`, `&` automatically — the `test_special_chars_escaped` test round-trips through parse to confirm the raw text value is preserved.

### XML: title as attribute, not child element

`<document title="Test Report">` is cleaner than `<document><title>Test Report</title>...` for a single-value scalar like the document title. Sheet names and row types similarly become attributes (`<sheet name="...">`, `<row type="...">`). Only the variable-length, multi-valued content (cell text) uses child elements.

### Markdown: separator placed by row type, not row index

The `| --- | --- |` separator is written immediately after the first row with `type == "header"`. This is correct regardless of whether `header_row > 1` in the doc spec — the MD renderer consumes the already-computed `rows` array, which always starts with the header row. The sentinel `header_written` flag prevents double-separators if a sheet somehow contained two header rows.

### Markdown: bold applied per-cell, alignment dropped

`_cell_text()` wraps in `**...**` if `cell["bold"]` is True, otherwise returns the plain string. The `align` field is not expressed in the output — Markdown pipe tables support `:---:` column alignment but this would require inspecting all cells in a column to determine the dominant alignment, which adds complexity for no practical benefit in m1. Alignment is silently dropped.

### All renderers: numeric values via `str()`

All four are string-based formats. `str(250)` → `"250"`, `str(250.0)` → `"250.0"` (but compute_doc already normalises integer-valued floats to int via `_fmt()`), `str("A-01")` → `"A-01"`. No type coercion is needed or performed. This is consistent with t4 (docx) and t5 (pdf) — only t3 (xlsx) needs string→float coercion for number_format to work.

### merge_ranges: silently skipped by all four renderers

CSV, JSON, XML, and Markdown have no concept of merged cells. merge_ranges are present in the doc spec but ignored by all four renderers. This is consistent with t4 (docx silently uses sheet name instead of merge_range value) and noted here as a known limitation. The merge_range `value` is not written anywhere in the t6 outputs.

---

## Known limitations

- **merge_ranges ignored:** all four renderers silently drop merge_range data. The merge_range value is not written to the output. This is the same trade-off as t4 (docx). Only t3 (xlsx via merged cells) and t5 (pdf via `<th colspan>`) preserve merge_range semantics.
- **CSV alignment ignored:** `align` is not expressible in CSV. Values are written as-is.
- **Markdown alignment dropped:** `| :--- |` / `| ---: |` syntax not used. All separator cells are `---`.
- **JSON: no type metadata in rows:** row type (`header`, `data`, `aggregate`) is not preserved in the JSON output. Consumers cannot distinguish aggregate rows from data rows. This matches the "clean data" contract — if type metadata is needed, use the doc spec JSON directly.

---

## t7 notes

- t7 is the Elixir orchestrator agent (`generate_doc_agent.exs`).
- The agent receives a template path + source file path, calls `fetch_data.py` → `compute_doc.py` → the appropriate `generate_{format}.py` based on the template's `output_formats` array.
- The agent must loop over all formats in `output_formats` (e.g. `["xlsx", "pdf", "csv"]`) and call a separate renderer for each.
- Use `run_command` for each subprocess; parse stdout as the output path; collect all output paths into a summary message.
- `overlay_base_dir: nil` — output must persist.
- `context_strategy: :full` — short-lived pipeline (< 10 steps).
