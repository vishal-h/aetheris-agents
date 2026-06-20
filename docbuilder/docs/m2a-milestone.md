# m-docbuilder-m2a — Template foundations

> Milestone doc for `aetheris-agents/docbuilder/` — m2a.
> Canonical. GitHub milestone and issues generated from this file.
> Do not edit scope in issue comments — edit here first.

---

## Goal

Branded output, queryable template catalogue, multi-source data, and
Markdown+CSS narrative PDF. All deterministic — no LLM selection yet.

After this milestone: a sprint run produces a branded proposal (company
logo in header, styled fonts, footer with page numbers) from two data
sources, in xlsx, docx, and pdf formats, using a Markdown narrative
template for the PDF cover and CSS for brand styles.

---

## What is NOT in m2a

- LLM template selection (→ m2b)
- Drive registry — templates remain flat files (→ m2b)
- Email or Drive delivery (→ m2b)
- Natural language requests (→ m3)
- Conversational template editing (→ m3)

---

## Contract refs (read before any ticket)

- `docs/agent-creation-guide.md` — all agent/script conventions (authoritative)
- `docs/milestone-methodology.md` — ticket loop, review format, sizing rule
- `CLAUDE.md` (aetheris-agents root) — standing conventions; read at session start
- `../aetheris/CLAUDE.md` — harness-side conventions
- `docbuilder/README.md` — design decisions, template model, row alignment
  convention, `header_row` / `data_col_start` / `table_style` decisions
- `docbuilder/docs/doc-spec-schema.md` — doc spec contract (authoritative for renderers)
- `docbuilder/docs/template-schema.md` — template JSON schema (update in t1)

---

## Design decisions (resolved before tickets start)

| Decision | Rationale |
|---|---|
| `header_row` is the xlsx base file alignment anchor | `header_row` in the template JSON equals the first empty row in the base file. Branding rows above are untouched by the renderer. See README §"Row alignment convention". |
| `data_col_start` optional (default: 1) | Allows a label column in the base file that the renderer skips. Added to template schema in t1. |
| `table_style` optional (default: `"Table Grid"`) | Makes docx table style configurable per template. Added to template schema in t1. |
| PDF narrative mode: `.md.template` + `.css` | Prose-heavy PDFs are better expressed as Markdown. Both modes (structured m1, narrative m2a) coexist — structured is the fallback when no `.md.template` exists. |
| `render_template.py` is a pure script (no LLM) | Markdown rendering + variable substitution is deterministic. The LLM is not involved. This is consistent with the agent-creation-guide.md principle: scripts do, agents decide. |
| Multi-source: one `fetch_data.py` call per source | Each source is fetched independently. `compute_doc.py` receives all source JSON files and merges. The orchestrator is responsible for calling fetch N times. |
| Base files committed (not fetched) in m2a | Flat files first, Drive registry in m2b. Same pattern as m1 JSON configs. |
| Fallback behaviour preserved in all renderers | If a base file or template file is absent, the renderer falls back to m1 behaviour. No regression for existing sprint cases. |

---

## Tickets

---

### t1 — Template schema update + demo assets

**Scope.** Update `template-schema.md` and `proposal_v1.json` with four new
optional fields: `table_style` (docx table style name), `data_col_start`
(xlsx first data column, 1-based), a `narrative` block for PDF mode
(`template_file`, `css_file`), and a per-sheet `header_row` explicit override
(set to `3` for the demo so the renderer writes below the base file's two
branding rows; honoured by `compute_doc.py` in t2). Also extend the demo's
`output_formats` to `["xlsx", "docx", "pdf"]`. Commit the four new demo template files:
`proposal_v1.md.template`, `proposal_v1.css`, and update the existing
`proposal_v1.docx` and `proposal_v1.xlsx` base files (already committed
as placeholders — verify `header_row: 3` alignment matches).
Add a second sample data source (`data/sample_data_summary.csv`) for the
multi-source demo in t4.

**Contract refs.** `docbuilder/docs/template-schema.md` (authoritative —
update it here); `docbuilder/README.md` §"Template model", §"Design decisions".

**Touches.**
- `docbuilder/docs/template-schema.md` (update — add four new fields:
  `table_style`, `data_col_start`, `narrative`, per-sheet `header_row`)
- `docbuilder/data/templates/demo/proposal_v1.json` (add `table_style`,
  `data_col_start`, `narrative` block, per-sheet `header_row: 3`; extend
  `output_formats` to `["xlsx", "docx", "pdf"]`; `data_sources` stays at one
  entry — the second entry is added in t4 alongside the guard removal)
- `docbuilder/data/templates/demo/proposal_v1.md.template` (new)
- `docbuilder/data/templates/demo/proposal_v1.css` (new)
- `docbuilder/data/sample_data_summary.csv` (new — second source for demo)
- `docbuilder/data/.gitignore` (add `!templates/demo/proposal_v1.md.template`
  and `!templates/demo/proposal_v1.css`)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t1-implementation-notes.md` (new)

**Do not generate.** No Python scripts, no agent files, no test files in
this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Template JSON is valid (data_sources stays at 1 in t1; second source added in t4)
python3 -c "import json; t=json.load(open('data/templates/demo/proposal_v1.json')); \
  print('data_sources:', len(t['data_sources'])); \
  assert len(t['data_sources']) == 1, 'data_sources must stay at 1 until t4'; \
  print('table_style:', t.get('table_style', 'NOT SET')); \
  print('data_col_start:', t.get('data_col_start', 'NOT SET')); \
  print('narrative:', 'present' if t.get('narrative') else 'NOT SET'); \
  print('header_row per sheet:', [s.get('header_row', 'NOT SET') for s in t['sheets']]); \
  assert all(s.get('header_row') == 3 for s in t['sheets']), 'each sheet needs header_row: 3'"

# New files exist
ls -lh data/templates/demo/
ls -lh data/sample_data_summary.csv

# CSS is non-empty
wc -l data/templates/demo/proposal_v1.css

# Markdown template is non-empty and contains at least one {{variable}}
grep -c "{{" data/templates/demo/proposal_v1.md.template
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/docs/template-schema.md`, `docbuilder/README.md` §"Template
> model" and §"Design decisions", and the existing
> `docbuilder/data/templates/demo/proposal_v1.json` before making any changes.
>
> Perform the t1 scope:
>
> **template-schema.md:** Add three new optional fields to the top-level
> object section:
> - `table_style` (string, optional, default `"Table Grid"`) — docx table
>   style name
> - `data_col_start` (integer, optional, default 1) — xlsx first data column
>   (1-based); rows above `header_row` and columns left of `data_col_start`
>   are owned by the base file
> - `narrative` (object, optional) — PDF narrative mode config:
>   `{"template_file": "{doc_type}_v{N}.md.template",
>    "css_file": "{doc_type}_v{N}.css"}`
> - `header_row` (integer, optional, per-sheet) — explicit 1-based row at which
>   the renderer writes the column-header row, overriding the value computed
>   from `merge_ranges`. Set the demo's sheets to `3` so the renderer writes
>   below the base file's two branding rows (logo row 1, navy separator row 2).
>   `compute_doc.py` honours it in t2 (falls back to the computed value when absent).
>
> **proposal_v1.json:** Add `"table_style": "Table Grid"`,
> `"data_col_start": 1`, a `"narrative"` block pointing to
> `proposal_v1.md.template` and `proposal_v1.css`, and `"header_row": 3` on
> each sheet. Extend `output_formats` to `["xlsx", "docx", "pdf"]`. Leave `data_sources`
> at its single `main` entry — the second `summary` source is wired in at
> t4 when the multi-source guard is removed (the schema change and guard
> removal land together so the build stays green through t2/t3).
>
> **sample_data_summary.csv:** Create with 3-4 rows of anonymised summary
> metrics that complement the line items (e.g. total_items, total_value,
> currency, valid_until). The file is committed now (t4 needs it) but is
> not referenced by the template until t4.
>
> **proposal_v1.md.template:** Create a realistic B2B proposal cover +
> intro section in Markdown. Must include:
> - `{{title}}` — document title
> - `{{client_name}}` — customer name
> - `{{date}}` — proposal date
> - `{{>line_items}}` — table partial placeholder for the Line Items sheet
> - `{{>summary}}` — table partial placeholder for the Summary sheet
> A brief "Terms & Conditions" paragraph after the tables is good practice.
>
> **proposal_v1.css:** Brand stylesheet for weasyprint. Must include:
> - `@page` rule with margins (20mm), header (logo placeholder text +
>   company name), footer (page number)
> - `body` — Arial/sans-serif, 10pt
> - `h1`, `h2` — navy `#1F4E79`, bold
> - `table` — border-collapse, full width
> - `th` — navy background, white text, bold
> - `td` — light border, padding
> - `.aggregate td` — bold, top border (matching m1 CSS class)
>
> **data/.gitignore:** Add `!templates/demo/proposal_v1.md.template` and
> `!templates/demo/proposal_v1.css`.
>
> Run the done-check and include its full output in the review packet.
> Review packet must open with the done-check output block.

---

### t2 — generate_xlsx.py: base file support

**Scope.** Two changes. (1) Teach `compute_doc.py` to honour an explicit
per-sheet `header_row` from the template (added in t1): use it when present,
fall back to the computed `max(merge_range.row) + 1` when absent. This is the
enabler for base-file alignment — the renderer consumes the doc spec, so the
doc spec's `header_row` must already be `3` for the demo. (2) Update
`generate_xlsx.py` to open a base file when one is provided via `--base-file
PATH`: open it with `openpyxl.load_workbook()`, locate existing sheets by name,
and write data starting at `header_row` (honoring `data_col_start`). When
`--base-file` is absent: current m1 behaviour (create fresh `Workbook()`).
All existing tests must continue to pass.

> The explicit-`header_row` change to `compute_doc.py` is carved out of the
> usual "do not modify compute_doc" rule because it is the minimal enabler for
> this ticket's base-file alignment and was the t1 review's blocking finding.
> Keep it to honouring the field + a test; no other compute_doc behaviour changes.

**Contract refs.** `docbuilder/docs/doc-spec-schema.md` §"Renderer contract";
`docbuilder/docs/template-schema.md` (`header_row`, `data_col_start`);
`docbuilder/README.md` §"Row alignment convention", §"Design decisions"
(`header_row` anchor, `data_col_start`); `agent-creation-guide.md` §"Script
design" (backward compatibility, `--input FILE` pattern).

**Touches.**
- `docbuilder/scripts/compute_doc.py` (update — honour explicit per-sheet `header_row`)
- `docbuilder/scripts/generate_xlsx.py` (update)
- `docbuilder/tests/test_compute_doc.py` (add explicit-`header_row` test)
- `docbuilder/tests/test_generate_xlsx.py` (add base file tests)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t2-implementation-notes.md` (new)

**Do not generate.** Do not modify the template schema or any renderer script
other than `generate_xlsx.py`. The only permitted `compute_doc.py` change is
honouring the explicit `header_row` field (above).

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Existing tests still pass (compute_doc honours explicit header_row; xlsx base files)
python3 -m pytest tests/test_compute_doc.py tests/test_generate_xlsx.py -v

# Base file round-trip: branding row survives
python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json - \
  | python3 scripts/generate_xlsx.py \
      --base-file data/templates/demo/proposal_v1.xlsx \
      --output-dir output --filename proposal_v1_branded

python3 -c "
import openpyxl
wb = openpyxl.load_workbook('output/proposal_v1_branded.xlsx')
ws = wb['Line Items']
# Row 1 A1 should still be the logo placeholder from the base file
print('A1:', ws.cell(1,1).value)
assert ws.cell(1,1).value == '[ LOGO ]', 'base file logo row overwritten'
# B1 should still be 'Company Name' (merged B1:E1 in the base file)
print('B1:', ws.cell(1,2).value)
assert ws.cell(1,2).value == 'Company Name', 'base file company name overwritten'
# Row 3 A3 should be the first column header written by the renderer (header_row=3)
print('A3:', ws.cell(3,1).value)
assert ws.cell(3,1).value == 'Item Code', 'header not written at row 3'
print('base-file alignment: OK')
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/docs/doc-spec-schema.md` §"Renderer contract",
> `docbuilder/README.md` §"Row alignment convention" and §"Design decisions",
> `docbuilder/docs/template-schema.md` (for `header_row` and `data_col_start`),
> `docbuilder/docs/milestones/m-docbuilder-m2a-t1-implementation-notes.md`
> (the row-ownership finding), and
> `docbuilder/docs/milestones/m-docbuilder-m1-t3-implementation-notes.md`
> before writing any code.
>
> **First, `compute_doc.py`:** where `header_row` is computed
> (`header_row = max(merge_rows) + 1 if merge_rows else 1`), honour an explicit
> override — `sheet.get("header_row", computed)`. Both Pass 1 and Pass 2 build
> sheets, so apply it in both. Add a `test_compute_doc.py` test: a template sheet
> with `"header_row": 3` produces a doc spec sheet with `header_row == 3`; absent →
> the computed value. No other compute_doc changes.
>
> **Then update `generate_xlsx.py` per t2 scope:**
>
> Add `--base-file PATH` optional argument (default: None). When provided:
> - Open with `openpyxl.load_workbook(args.base_file)` instead of
>   `Workbook()`
> - Do NOT call `wb.remove(wb.active)` (base file sheets must be preserved)
> - Look up each sheet from the doc spec by name: `wb[sheet["name"]]`.
>   If a sheet with that name does not exist in the base file, create it.
> - Write merge_ranges to their specified rows as before.
> - Write rows array starting at `header_row` (1-based), columns starting
>   at `data_col_start` (from doc spec, default 1 if absent). Do NOT write
>   to rows above `header_row` or columns left of `data_col_start`.
> - Column widths: only set widths for columns at or right of `data_col_start`.
>   Columns left of `data_col_start` are owned by the base file.
>
> When `--base-file` is absent: existing m1 behaviour unchanged.
>
> Add tests covering:
> - `--base-file` absent → fresh workbook (existing behaviour, already tested)
> - `--base-file` present → base file opened, row 1 content preserved,
>   renderer writes from `header_row` downward
> - `data_col_start: 2` → column A untouched, data written from column B
> - Sheet not in base file → sheet created and written normally
>
> All 17 existing tests must still pass. New tests use `tmp_path` and the
> committed `demo/proposal_v1.xlsx` as the base file fixture.
>
> **Review packet must open with the full done-check output block.**

---

### t3 — generate_docx.py: base file + table_style support

**Scope.** Update `generate_docx.py` to open a base file when provided via
`--base-file PATH`, and to read `table_style` from the doc spec (passed
through from the template JSON). When a base file is present: open it with
`Document(base_file_path)` and append content after existing body content.
When absent: current m1 behaviour. All existing tests must continue to pass.

**Contract refs.** `docbuilder/docs/doc-spec-schema.md` §"Renderer contract";
`docbuilder/README.md` §"Design decisions" (`table_style`);
`agent-creation-guide.md` §"Script design".

**Touches.**
- `docbuilder/scripts/generate_docx.py` (update)
- `docbuilder/tests/test_generate_docx.py` (add base file + table_style tests)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t3-implementation-notes.md` (new)

**Do not generate.** No changes to `generate_xlsx.py` or any other script.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Existing tests still pass
python3 -m pytest tests/test_generate_docx.py -v

# Base file round-trip: header/footer survive, tables appended
python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json - \
  | python3 scripts/generate_docx.py \
      --base-file data/templates/demo/proposal_v1.docx \
      --output-dir output --filename proposal_v1_branded

python3 -c "
from docx import Document
doc = Document('output/proposal_v1_branded.docx')
print('Tables:', len(doc.tables))
print('Sections:', len(doc.sections))
hdr = doc.sections[0].header
print('Header paragraphs:', len(hdr.paragraphs))
print('Header text:', hdr.paragraphs[0].text[:60])
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/docs/doc-spec-schema.md` §"Renderer contract",
> `docbuilder/README.md` §"Design decisions" (`table_style`),
> `docbuilder/docs/milestones/m-docbuilder-m1-t4-implementation-notes.md`,
> and the t3 review file for m1 (merge_ranges treatment in docx) before
> writing any code.
>
> Update `generate_docx.py` per t3 scope:
>
> Add `--base-file PATH` optional argument (default: None). When provided:
> - Open with `Document(args.base_file)` instead of `Document()`
> - Append content (headings + tables) after existing body content
> - The base file's header, footer, styles, and cover page content are
>   preserved automatically
>
> Add `table_style` support: read from `doc_spec.get("table_style",
> "Table Grid")` and pass to `table.style`. The doc spec must include
> `table_style` (passed through from template JSON by `compute_doc.py`
> in t5 — for now read it with a fallback default).
>
> When `--base-file` is absent: existing m1 behaviour unchanged.
>
> Add tests covering:
> - `--base-file` absent → fresh document (existing behaviour, already tested)
> - `--base-file` present → header text preserved, tables still present
> - `table_style` in doc spec → table style applied
> - `table_style` absent from doc spec → defaults to `"Table Grid"`
>
> All 17 existing tests must still pass.
>
> **Review packet must open with the full done-check output block.**

---

### t4 — compute_doc.py: multi-source support

**Scope.** Update `compute_doc.py` to accept and merge multiple source
JSON files. In m1, the m1 single-source constraint (exit 1 if >1 source)
is removed. Each sheet's `source_key` now maps to whichever source in the
provided sources dict has that key. The doc spec output is unchanged — only
the input side changes. Update `template-schema.md` validation rules to
remove the m1 single-source restriction. Wire the second `summary` data
source into `proposal_v1.json` here — the schema change and the guard
removal land together (deferred from t1 to keep t2/t3 green). All existing
tests must pass; add multi-source tests.

**Contract refs.** `docbuilder/docs/template-schema.md` §"Validation rules"
(remove m1 constraint); `docbuilder/docs/doc-spec-schema.md` §"Renderer
contract" (unchanged); `agent-creation-guide.md` §"Script design".

**Touches.**
- `docbuilder/scripts/compute_doc.py` (update — remove single-source guard,
  accept N source paths)
- `docbuilder/data/templates/demo/proposal_v1.json` (add the second
  `summary` data source entry — deferred from t1)
- `docbuilder/docs/template-schema.md` (update validation rules table —
  remove m1 single-source row)
- `docbuilder/tests/test_compute_doc.py` (add multi-source tests)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t4-implementation-notes.md` (new)

**Do not generate.** No renderer changes, no orchestrator changes, no new
scripts in this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# All existing compute_doc tests pass
python3 -m pytest tests/test_compute_doc.py -v

# Multi-source pipeline: two sources → two sheets
python3 scripts/fetch_data.py --key main data/sample_data.csv > /tmp/raw_main.json
python3 scripts/fetch_data.py --key summary data/sample_data_summary.csv \
  > /tmp/raw_summary.json
python3 scripts/compute_doc.py \
  data/templates/demo/proposal_v1.json \
  /tmp/raw_main.json /tmp/raw_summary.json \
  | python3 -c "
import json, sys
spec = json.load(sys.stdin)
sheets = [s['name'] for s in spec['sheets']]
print('Sheets:', sheets)
assert len(sheets) == 2, f'Expected 2 sheets, got {len(sheets)}'
print('Multi-source: OK')
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/docs/template-schema.md`, `docbuilder/README.md`
> §"Design decisions" (multi-source), and
> `docbuilder/docs/milestones/m-docbuilder-m1-t2-implementation-notes.md`
> (two-pass architecture, aggregate store) before writing any code.
>
> Update `compute_doc.py` per t4 scope:
>
> Remove the m1 guard: `if len(template["data_sources"]) > 1: raise ValueError(...)`.
> The script already accepts N positional source paths (m1 allowed only 1).
> Now allow N ≥ 1. Build `sources` dict from all provided source JSON files
> keyed by their `"key"` field. Each sheet's `source_key` maps into this dict
> as before. If a `source_key` is referenced but not provided, exit 1 with
> a clear error.
>
> Update `template-schema.md` validation rules: remove the
> `"data_sources has more than one entry → exit 1"` row. Add a new row:
> `"source_key references a key not present in provided sources → exit 1"`.
>
> Wire the second source into `proposal_v1.json` (deferred from t1): add a
> `summary` entry to `data_sources` pointing at `data/sample_data_summary.csv`.
> Decide whether the Summary sheet should consume it directly (set its
> `source_key` to `"summary"` with mapped columns) or keep deriving from
> `summary_rows` — document the choice in the t4 implementation notes.
>
> Add tests:
> - Two sources provided, two sheets each using a different source → both
>   sheets computed correctly
> - Source key referenced in sheet but not provided → exit 1
> - One source (existing behaviour) → still works
>
> All 24 existing compute_doc tests must pass.
>
> **Review packet must open with the full done-check output block.**

---

### t5 — compute_doc.py: pass-through of new template fields

**Scope.** Update `compute_doc.py` to pass `table_style`, `data_col_start`,
and the `narrative` block through to the doc spec output. These are
template-level fields that renderers need but `compute_doc.py` currently
drops. No logic change — pure pass-through. Update `doc-spec-schema.md`
to document these new top-level doc spec fields.

**Contract refs.** `docbuilder/docs/doc-spec-schema.md` (update);
`docbuilder/docs/template-schema.md` §"Top-level object" (source of truth
for field definitions); `agent-creation-guide.md` §"Script design".

**Touches.**
- `docbuilder/scripts/compute_doc.py` (update — pass through three fields)
- `docbuilder/docs/doc-spec-schema.md` (update — add three new top-level fields)
- `docbuilder/tests/test_compute_doc.py` (add pass-through assertions)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t5-implementation-notes.md` (new)

**Do not generate.** No renderer changes in this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

python3 -m pytest tests/test_compute_doc.py -v

# Verify pass-through in full pipeline output
python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py \
      data/templates/demo/proposal_v1.json - \
  | python3 -c "
import json, sys
spec = json.load(sys.stdin)
print('table_style:', spec.get('table_style', 'MISSING'))
print('data_col_start:', spec.get('data_col_start', 'MISSING'))
print('narrative:', 'present' if spec.get('narrative') else 'MISSING')
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/docs/template-schema.md` §"Top-level object",
> `docbuilder/docs/doc-spec-schema.md` §"Top-level object" before writing
> any code.
>
> Update `compute_doc.py`: in the `return` dict at the bottom of
> `compute_doc()`, add three new keys passed through from the template:
> - `"table_style": template.get("table_style", "Table Grid")`
> - `"data_col_start": template.get("data_col_start", 1)`
> - `"narrative": template.get("narrative")` (None if absent)
>
> Update `doc-spec-schema.md` §"Top-level object" table to add these three
> fields with types, defaults, and descriptions.
>
> Add tests asserting that all three fields appear in the doc spec output
> when present in the template, and that defaults are correct when absent.
>
> **Review packet must open with the full done-check output block.**

---

### t6 — render_template.py: Markdown + CSS → HTML

**Scope.** New script `render_template.py`. Reads a `.md.template` file,
a context JSON (scalar variables), and the doc spec JSON (for table partials).
Substitutes `{{variable}}` placeholders with context values, replaces
`{{>sheet_name}}` partials with HTML tables rendered from the doc spec,
applies a `.css` file, and outputs a complete HTML document to stdout.
`generate_pdf.py` will use this in t7 — for now it is a standalone script
tested independently.

**Contract refs.** `agent-creation-guide.md` §"Script design" (pure function,
stdout contract, exit codes); `docbuilder/README.md` §"Template model"
(narrative mode); `docbuilder/docs/doc-spec-schema.md` (doc spec structure
for table rendering).

**Touches.**
- `docbuilder/scripts/render_template.py` (new)
- `docbuilder/tests/test_render_template.py` (new)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t6-implementation-notes.md` (new)

**Do not generate.** No changes to `generate_pdf.py` in this ticket.
Do not add LLM calls — this is pure deterministic rendering.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

python3 -m pytest tests/test_render_template.py -v

# Standalone render: produces valid HTML with substituted variables
python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py \
      data/templates/demo/proposal_v1.json - > /tmp/spec.json

python3 scripts/render_template.py \
  --template data/templates/demo/proposal_v1.md.template \
  --css     data/templates/demo/proposal_v1.css \
  --context '{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}' \
  --spec    /tmp/spec.json \
  | python3 -c "
import sys
html = sys.stdin.read()
assert '<html' in html, 'Missing <html>'
assert 'Acme Corp' in html, 'Variable substitution failed'
assert '<table' in html, 'Table partial not rendered'
assert 'proposal_v1.css' in html or 'font-family' in html, 'CSS not applied'
print('render_template: OK')
print('HTML length:', len(html))
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/README.md` §"Template model" and §"PDF rendering modes",
> `docbuilder/docs/doc-spec-schema.md`, and
> `docbuilder/data/templates/demo/proposal_v1.md.template` before writing
> any code.
>
> Implement `render_template.py` per t6 scope:
>
> **Arguments:**
> - `--template PATH` — path to `.md.template` file
> - `--css PATH` — path to `.css` file
> - `--context JSON` — inline JSON string of scalar variables
> - `--spec PATH` — path to doc spec JSON file (or `-` for stdin)
>
> **Processing pipeline:**
> 1. Read template file, context JSON, doc spec JSON
> 2. Substitute `{{variable}}` placeholders using context dict. Unknown
>    variables: leave as-is with a stderr warning, do not error.
> 3. Replace `{{>sheet_name}}` partials: find the sheet in the doc spec
>    whose `name` matches `sheet_name` (case-insensitive). Render it as
>    an HTML table using the same logic as `_build_html()` in
>    `generate_pdf.py` — same CSS classes (`aggregate`, bold/align inline
>    styles). If no matching sheet: stderr warning, replace with empty string.
> 4. Convert the resulting Markdown string to HTML using the `markdown`
>    stdlib library (`import markdown; html_body = markdown.markdown(md_text,
>    extensions=['tables'])`).
> 5. Wrap in a complete HTML document:
>    `<!DOCTYPE html><html><head><meta charset='utf-8'>
>    <link rel='stylesheet' href='{css_path}'></head>
>    <body>{html_body}</body></html>`
>    Use an absolute path for the CSS `href` so weasyprint can resolve it.
> 6. Print HTML to stdout. Exit 1 on any error.
>
> **Tests** (no weasyprint needed — test HTML output only):
> - Variable substitution: `{{client_name}}` → correct value
> - Unknown variable: left as-is, warning on stderr
> - Table partial `{{>Line Items}}` → `<table>` present in output
> - Unknown partial: empty string, warning on stderr
> - CSS link present in `<head>`
> - Output is valid HTML (assert `<html>` and `</html>` present)
> - Markdown formatting: `# Heading` → `<h1>`, `**bold**` → `<strong>`
> - Exit 1 on missing template file
>
> **Review packet must open with the full done-check output block.**

---

### t7 — generate_pdf.py: narrative mode

**Scope.** Update `generate_pdf.py` to support narrative mode. When the
doc spec contains a `narrative` block with `template_file` and `css_file`,
call `render_template.py` to produce the HTML, then pass it to weasyprint.
When `narrative` is absent: structured mode (existing `_build_html()` — m1
behaviour preserved). Add `--context JSON` argument for scalar variable
substitution in narrative mode. Add `--template-dir PATH` to locate the
`.md.template` and `.css` files.

**Contract refs.** `docbuilder/docs/doc-spec-schema.md` §"Renderer contract";
`docbuilder/README.md` §"PDF rendering modes"; `agent-creation-guide.md`
§"Script design".

**Touches.**
- `docbuilder/scripts/generate_pdf.py` (update)
- `docbuilder/tests/test_generate_pdf.py` (add narrative mode tests)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t7-implementation-notes.md` (new)

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# All existing PDF tests pass (structured mode preserved)
python3 -m pytest tests/test_generate_pdf.py -v

# Narrative mode: produces PDF via Markdown template
python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py \
      data/templates/demo/proposal_v1.json - \
  | python3 scripts/generate_pdf.py \
      --template-dir data/templates/demo \
      --context '{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}' \
      --output-dir output --filename proposal_v1_narrative

ls -lh output/proposal_v1_narrative.pdf
python3 -c "
assert open('output/proposal_v1_narrative.pdf','rb').read(4) == b'%PDF'
print('PDF magic bytes: OK')
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design",
> `docbuilder/docs/doc-spec-schema.md` §"Renderer contract",
> `docbuilder/README.md` §"PDF rendering modes",
> `docbuilder/docs/milestones/m-docbuilder-m1-t5-implementation-notes.md`,
> and `docbuilder/docs/milestones/m-docbuilder-m2a-t6-implementation-notes.md`
> before writing any code.
>
> Update `generate_pdf.py` per t7 scope:
>
> Add arguments:
> - `--template-dir PATH` — directory containing `.md.template` and `.css`
>   files (optional; narrative mode requires it)
> - `--context JSON` — scalar variable context for `render_template.py`
>   (optional; defaults to `{}`)
>
> In `main()`, after loading the doc spec from stdin/`--input`:
> - If `doc_spec.get("narrative")` is present AND `--template-dir` is
>   provided: call `render_template.py` as a subprocess (via `subprocess.run`)
>   with `--template`, `--css`, `--context`, `--spec` args. Capture stdout
>   as the HTML string. Pass to `weasyprint.HTML(string=html).write_pdf()`.
> - Otherwise: call `_build_html(doc_spec)` as before (structured mode).
>
> Do not inline `render_template.py` logic — call it as a subprocess. This
> keeps the single-responsibility boundary clean and makes each script
> independently testable.
>
> Add tests:
> - Narrative mode: doc spec with `narrative` block + `--template-dir` →
>   PDF produced, magic bytes correct
> - Structured mode (no `narrative`): existing behaviour unchanged
> - `narrative` present but `--template-dir` absent → structured mode fallback
>   (warn on stderr, do not error)
>
> All 13 existing PDF tests must pass.
>
> **Review packet must open with the full done-check output block.**

---

### t8 — Orchestrator + sprint case update

**Scope.** Update `docbuilder_orchestrator.exs` to support m2a features:
pass `--base-file` to xlsx and docx renderers, pass `--template-dir` and
`--context` to the pdf renderer, call `fetch_data.py` N times for
multi-source templates (reading `data_sources` from the template JSON).
Update the sprint case to verify branded xlsx, docx, and narrative PDF
outputs. Update `runbook.md` with new env vars and multi-source notes.

**Contract refs.** `agent-creation-guide.md` §"Agent file conventions",
§"Orchestrator patterns", §"Pre-flight checklist"; `aetheris-agents/CLAUDE.md`
§"Implementation notes"; `docbuilder/runbook.md` (update).

**Touches.**
- `docbuilder/agents/docbuilder_orchestrator.exs` (update)
- `docbuilder/runbook.md` (update — new flags, multi-source, context JSON)
- `../aetheris/scripts/sprint.sh` (update docbuilder case — verify 3 output files)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t8-implementation-notes.md` (new)

**Runbook update rule.** New flags (`--base-file`, `--template-dir`,
`--context`) and multi-source behaviour must be documented in `runbook.md`
in this ticket — not deferred to t9.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

# Syntax check
DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}' \
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs")'

# Full sprint
DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}' \
./scripts/sprint.sh docbuilder

# Verify all three branded outputs
ls -lh ../aetheris-agents/docbuilder/output/proposal_v1.*
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` (full), `CLAUDE.md`,
> `docbuilder/runbook.md`, and
> `docbuilder/docs/milestones/m-docbuilder-m1-t7-implementation-notes.md`
> (orchestrator patterns, `--input FILE`, `write_file` justification)
> before writing any code.
>
> Update `docbuilder_orchestrator.exs` per t8 scope:
>
> Add `DOCBUILDER_CONTEXT` env var (optional; default `"{}"`).
>
> Read the template JSON after the compute step to determine:
> - `data_sources` array → call `fetch_data.py` once per source, write
>   each to a temp file (`output/pipeline_raw_{key}.json`)
> - `narrative` block → pass `--template-dir` and `--context` to
>   `generate_pdf.py`
> - Base files exist? → pass `--base-file output/../data/templates/{tenant}/
>   {doc_type}_{version}.{ext}` to xlsx and docx renderers
>
> For multi-source: `compute_doc.py` receives all raw source files as
> positional args after the template path.
>
> Update the sprint.sh docbuilder case to verify xlsx, docx, and pdf
> outputs all exist (currently only verifies xlsx and pdf).
>
> Update `runbook.md`: add `DOCBUILDER_CONTEXT` to the env vars table;
> add a multi-source section explaining `data_sources`; add base file and
> narrative mode to expected output section.
>
> After done-check passes, write
> `docbuilder/docs/milestones/m-docbuilder-m2a-t8-implementation-notes.md`.
>
> **Review packet must open with the full done-check output block.**
> Include: syntax check output, full sprint run output, `ls -lh output/`
> showing all three branded output files.

---

### t9 — Catalogue + list_templates.py

**Scope.** Add `data/templates/{tenant}/catalogue.json` (flat file listing
available doc types and variants for the tenant). Implement `list_templates.py`
— reads `catalogue.json` for a given tenant and outputs structured JSON.
This script is the foundation for LLM selection in m2b; in m2a it is
implemented and tested but not yet called by the orchestrator.

**Contract refs.** `agent-creation-guide.md` §"Script design";
`docbuilder/README.md` §"Template model" (catalogue.json structure).

**Touches.**
- `docbuilder/data/templates/demo/catalogue.json` (new)
- `docbuilder/scripts/list_templates.py` (new)
- `docbuilder/tests/test_list_templates.py` (new)
- `docbuilder/data/.gitignore` (add `!templates/demo/catalogue.json`)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t9-implementation-notes.md` (new)

**Do not generate.** Do not call `list_templates.py` from the orchestrator
in this ticket — that is m2b scope.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

python3 -m pytest tests/test_list_templates.py -v

# Standalone: returns catalogue for demo tenant
python3 scripts/list_templates.py --tenant demo | python3 -m json.tool

# Verify structure
python3 scripts/list_templates.py --tenant demo | python3 -c "
import json, sys
cat = json.load(sys.stdin)
print('Tenant:', cat['tenant_id'])
print('Doc types:', [d['doc_type'] for d in cat['doc_types']])
assert len(cat['doc_types']) >= 1, 'No doc types in catalogue'
print('list_templates: OK')
"
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design" and
> `docbuilder/README.md` §"Template model" before writing any code.
>
> Create `data/templates/demo/catalogue.json`:
> ```json
> {
>   "tenant_id": "demo",
>   "doc_types": [
>     {
>       "doc_type": "proposal",
>       "description": "B2B project proposal with line items and summary",
>       "variants": [
>         {
>           "version": "v1",
>           "label": "Standard",
>           "output_formats": ["xlsx", "docx", "pdf"],
>           "has_base_files": {"xlsx": true, "docx": true},
>           "has_narrative": true
>         }
>       ]
>     }
>   ]
> }
> ```
>
> Implement `list_templates.py`: accepts `--tenant TENANT_ID` and optional
> `--templates-dir PATH` (default: `data/templates`). Reads
> `{templates_dir}/{tenant_id}/catalogue.json`. Outputs the parsed JSON to
> stdout. Exit 1 if tenant not found or catalogue missing.
>
> Tests: tenant found → correct JSON; unknown tenant → exit 1; missing
> catalogue → exit 1; output is valid JSON.
>
> **Review packet must open with the full done-check output block.**

---

### t10 — Docs sync + capability matrix update

**Scope.** Sync all docs to match what shipped in m2a. Regenerate capability
matrix (new scripts: `render_template.py`, `list_templates.py`). Update
`docbuilder/README.md` decisions section if any were revised. Update
`rig--runbook.md` with m2a additions. Write milestone summary. Promote any
CLAUDE.md learning candidates from t1–t9 reviews.

**Contract refs.** `milestone-methodology.md` §7 (milestone-end ritual);
`aetheris-agents/CLAUDE.md` §"Doc-sync DoD".

**Touches.**
- `docs/capability-matrix.md` (regenerate)
- `docbuilder/README.md` (decisions + open questions if any)
- `docbuilder/docs/m2a-milestone.md` (add milestone summary at bottom)
- `rig--runbook.md` (m2a additions: `DOCBUILDER_CONTEXT`, multi-source,
  narrative PDF)
- `CLAUDE.md` (learning promotions if findings recurred ≥2 tickets)
- `docbuilder/docs/milestones/m-docbuilder-m2a-t10-implementation-notes.md` (new)

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

mix aetheris run ../aetheris-agents/agents/capability_matrix.exs
grep -A 3 "render_template\|list_templates" \
  ../aetheris-agents/docs/capability-matrix.md

# All docbuilder tests still green
cd ../aetheris-agents
python3 -m pytest docbuilder/tests/ -v --tb=short 2>&1 | tail -5
```

**Claude-code prompt.**
> Read `CLAUDE.md`, `docs/milestone-methodology.md` §7, and all m2a
> implementation notes (`m-docbuilder-m2a-t1-implementation-notes.md`
> through `m-docbuilder-m2a-t9-implementation-notes.md`) and review files
> before starting. These are the primary input for the milestone summary.
>
> Perform the t10 docs sync per scope above.
>
> For CLAUDE.md promotions: scan all t1–t9 review files for findings
> that recurred on ≥2 tickets. Promote each to a one-line bold rule +
> rationale + source ref.
>
> Write the milestone summary covering: what shipped (one line per ticket),
> what was deferred (→ m2b/m3 refs), surprises, open items for m2b.
>
> **Review packet must open with the full done-check output block.**

---

## Milestone summary

_(written by claude-code at milestone end, after t10)_
