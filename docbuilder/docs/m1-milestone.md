# m-docbuilder-m1 — Core doc builder

> Milestone doc for `aetheris-agents/docbuilder/` — m1.
> Canonical. GitHub milestone and issues are generated from this file.
> Do not edit scope in issue comments — edit here first.

---

## Goal

End-to-end working pipeline: data in, formatted document out.
Flat-file JSON templates (one per tenant/doc-type). Single orchestrator agent.
All planned output formats implemented and tested.

After this milestone: a sprint run produces a formatted xlsx proposal
(merged headers, bold columns, aggregate rows, multiple sheets) from
sample CSV data and a committed tenant template.

---

## What is NOT in m1

- Template registry / tenant management (→ m2)
- Drive or email delivery (→ m2)
- Multi-source data fetch and join (→ m2; template schema is forward-compatible but m1 enforces single source)
- Conversational template editing (→ m3)
- Natural language tweaks to templates
- Real tenant data (sample data only, committed anonymised)

---

## Contract refs (read before any ticket)

- `docs/agent-creation-guide.md` — all agent/script conventions (authoritative)
- `docs/milestone-methodology.md` — ticket loop, review format, sizing rule
- `CLAUDE.md` (aetheris-agents root) — standing conventions; read at session start
- `../aetheris/CLAUDE.md` — harness-side conventions

---

## Tickets

---

### t1 — Template schema + sample template

**Scope.** Define the JSON schema for a docbuilder template. Commit one
sample tenant template (`demo/proposal_v1.json`) that exercises the full
feature surface: multiple sheets, merged header cells, bold columns,
left/right alignment, aggregate rows (sum at bottom), column widths,
and two output formats (`xlsx`, `pdf`). Commit anonymised sample data
(`data/sample_data.csv`) that the template can be applied to.

**Contract refs.** agent-creation-guide.md §"Script design" (schema is data,
not code); README.md §"Design decisions" (template is JSON, not JSONL).

**Touches.**
- `docbuilder/data/templates/demo/proposal_v1.json` (new)
- `docbuilder/data/sample_data.csv` (new, anonymised)
- `docbuilder/data/.gitignore` (new — exclude real data and `output/`)
- `docbuilder/docs/template-schema.md` (new — documents every field)
- `docbuilder/README.md` (update open question 1 and 3 with decisions made)

**Do not generate.** No agent files, no Python scripts, no tests in this ticket.

**Done-check.**
```bash
# Schema doc exists and template validates as JSON
python3 -c "import json; json.load(open('docbuilder/data/templates/demo/proposal_v1.json'))"
echo "template valid"

# Sample data exists
wc -l docbuilder/data/sample_data.csv
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design", `CLAUDE.md`, and
> `docbuilder/README.md` in full.
>
> Create the docbuilder template schema and sample assets per t1 scope:
> - Design a JSON template schema that supports: `data_sources` (array of
>   source descriptors — m1 validates exactly one entry; schema supports
>   multiple for m2 forward-compatibility), sheets (array), columns
>   (name, source_field, type, bold, align, width), merge_ranges (for
>   header cells), aggregate_rows (sum/count/avg, position top or bottom),
>   output_formats (array of format strings).
> - Each `data_sources` entry has: `key` (string, used by compute_doc to
>   reference this source), `type` ("csv" or "json" for m1), `path`
>   (relative to sandbox root).
> - Write `docbuilder/data/templates/demo/proposal_v1.json` — a generic
>   B2B proposal template with 2 sheets: (1) "Line Items" with columns
>   item_code, description, quantity, unit_price, total (quantity × unit_price);
>   (2) "Summary" with aggregate totals and a notes row. Merged header across
>   all columns on row 1, bold column headers on row 2, `total` column bold
>   and right-aligned, aggregate sum row at bottom of sheet 1.
>   `data_sources` array with exactly one entry, `output_formats: ["xlsx", "pdf"]`.
> - Write `docbuilder/data/sample_data.csv` with anonymised rows that
>   satisfy the template's column requirements.
> - Write `docbuilder/data/.gitignore` per agent-creation-guide.md convention.
> - Write `docbuilder/docs/template-schema.md` documenting every field with
>   type, required/optional, and example value. Include a note that m1
>   rejects templates with `data_sources` length > 1.
> - Update the open questions in `docbuilder/README.md` (question 2, PDF
>   renderer) with the decision made; questions 1 and 3 are already resolved.
>
> Run the done-check and include its output in the review packet.

---

### t2 — fetch_data.py + compute_doc.py

**Scope.** Two scripts with strictly separated responsibilities.

`fetch_data.py`: reads ONE data source (local CSV or JSON file in m1) and
outputs a raw JSON array of row dicts to stdout. **No transformation** —
it parses and passes through. Takes a source `key` and `path` as args;
the key is echoed in the output so `compute_doc.py` can identify it.
Fails with exit 1 if the file is missing or unparseable.

`compute_doc.py`: owns **all transformation logic**. Reads the template JSON
and one or more raw source JSON files (m1: exactly one). Applies column
mapping (`source_field` → column), computes aggregate row values (sums,
counts, averages), derives merge cell coordinates, resolves bold/align flags
per cell, and emits a **doc spec JSON** to stdout. The doc spec is complete
and format-agnostic: renderers receive pre-computed values and must not
compute or transform anything.

**Contract refs.** agent-creation-guide.md §"Script design" (one
responsibility per script; stdout is the contract; exit codes); §"Scripts
must be runnable standalone"; README.md §"Design decisions"
(fetch/transform split; multi-source is m2).

**Touches.**
- `docbuilder/scripts/fetch_data.py` (new)
- `docbuilder/scripts/compute_doc.py` (new)
- `docbuilder/tests/conftest.py` (new)
- `docbuilder/tests/test_fetch_data.py` (new)
- `docbuilder/tests/test_compute_doc.py` (new)
- `docbuilder/docs/doc-spec-schema.md` (new — documents doc spec JSON fields)

**Do not generate.** No agent files, no renderer scripts in this ticket.
Do not add transformation logic to `fetch_data.py`.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# fetch_data standalone
python3 scripts/fetch_data.py --key main data/sample_data.csv | python3 -m json.tool

# full pipeline
python3 scripts/fetch_data.py --key main data/sample_data.csv > /tmp/raw.json
python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json /tmp/raw.json \
  | python3 -m json.tool

# Tests
python3 -m pytest tests/test_fetch_data.py tests/test_compute_doc.py -v
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` (full), `CLAUDE.md`,
> `docbuilder/docs/template-schema.md`, and README.md §"Design decisions"
> before writing any code.
>
> Implement `fetch_data.py` and `compute_doc.py` per t2 scope.
>
> `fetch_data.py`: accepts `--key KEY` and one positional path arg.
> Outputs `{"key": KEY, "rows": [...]}` to stdout. Rows are dicts
> (CSV header → value). No filtering, no renaming, no computation.
> Errors to stderr, exit 1.
>
> `compute_doc.py`: accepts template path and one or more raw source JSON
> paths as positional args (m1 validates exactly one; error if more).
> Outputs a doc spec JSON to stdout. The doc spec includes: `title`,
> `output_formats`, and for each sheet: `name`, `columns` (with
> `bold`, `align`, `width` resolved), `rows` (header + data + aggregate,
> each row is an array of `{value, bold, align}` cell objects),
> `merge_ranges` as `{sheet, row, col_start, col_end}` objects.
> All aggregate values (sums, counts, etc.) are pre-computed here.
> Renderers must not compute anything.
>
> Write `docbuilder/docs/doc-spec-schema.md` documenting the full doc spec
> format with types and examples.
>
> Write pytest unit tests covering: correct column mapping via `source_field`,
> aggregate computation (sum, count, avg), merge range derivation, missing
> source field handling (exit 1), multi-source rejection (exit 1 in m1).
>
> Run the done-check and include its output in the review packet.

---

### t3 — generate_xlsx.py

**Scope.** Renderer that takes a doc spec JSON and produces a `.xlsx` file.
Supports: multiple sheets, merged header cells, bold and alignment per cell,
numeric column formatting, column widths, aggregate rows visually
distinguished (e.g. bold + top border). Output path is `output/{filename}.xlsx`
unless `--output-dir` overrides.

**Contract refs.** agent-creation-guide.md §"Script design"; §"--output-dir
flag on generation scripts"; §"Scripts must be runnable standalone".

**Touches.**
- `docbuilder/scripts/generate_xlsx.py` (new)
- `docbuilder/tests/test_generate_xlsx.py` (new)

**Do not generate.** No other renderer scripts in this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Standalone — produces output/proposal.xlsx
python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json - \
  | python3 scripts/generate_xlsx.py --output-dir output --filename proposal

ls -lh output/proposal.xlsx

# Tests (skips if openpyxl missing)
python3 -m pytest tests/test_generate_xlsx.py -v
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design" and
> `docbuilder/docs/doc-spec-schema.md` before writing any code.
>
> Implement `generate_xlsx.py` per t3 scope using openpyxl.
>
> Script accepts: doc spec JSON on stdin, `--output-dir` (default `output`),
> `--filename` (default `document`). Writes `{output_dir}/{filename}.xlsx`.
> Prints the output path to stdout on success. Exit 1 on error.
>
> Implementation requirements:
> - Iterate sheets from doc spec; create one worksheet per sheet.
> - Apply merge_ranges using `worksheet.merge_cells`.
> - Apply bold and alignment per cell from doc spec flags.
> - Apply column widths.
> - Style aggregate rows: bold + thin top border.
> - Numeric cells: right-aligned, number format `#,##0.00` if type is
>   "currency" or "number" in the template column definition.
>
> Tests: use `tmp_path`; assert file exists; open with openpyxl and assert
> sheet count, cell value spot-checks, merge range presence. Mark
> integration tests with `@pytest.mark.integration` and skip if openpyxl
> not installed (conftest pattern from agent-creation-guide.md).
>
> Run the done-check and include its output in the review packet.

---

### t4 — generate_docx.py

**Scope.** Renderer that takes a doc spec JSON and produces a `.docx` file.
Supports: document title (from template metadata), one table per sheet,
bold header row, alignment per cell, aggregate row distinguished (bold).

**Contract refs.** agent-creation-guide.md §"Script design"; §"--output-dir".

**Touches.**
- `docbuilder/scripts/generate_docx.py` (new)
- `docbuilder/tests/test_generate_docx.py` (new)

**Done-check.**
```bash
cd aetheris-agents/docbuilder

python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json - \
  | python3 scripts/generate_docx.py --output-dir output --filename proposal

ls -lh output/proposal.docx
python3 -m pytest tests/test_generate_docx.py -v
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design" and
> `docbuilder/docs/doc-spec-schema.md` before writing any code.
>
> Implement `generate_docx.py` using python-docx. Same interface as
> `generate_xlsx.py` (stdin doc spec, `--output-dir`, `--filename`).
> One table per sheet. Bold header row. Per-cell alignment via
> `paragraph.alignment`. Aggregate rows bold. Document title set from
> `doc_spec.title` if present.
>
> Tests: assert file exists; open with python-docx and check table count,
> header cell text, row count. Skip if python-docx not installed.
>
> Run the done-check and include its output in the review packet.

---

### t5 — generate_pdf.py

**Scope.** Renderer that produces a `.pdf` from the doc spec via an
intermediate HTML representation. Uses **weasyprint** (pure Python,
HTML → PDF). reportlab is backlog — weasyprint is sufficient for m1
and the doc spec contract means swapping renderers later is a single-script
change with no upstream impact.

**Contract refs.** agent-creation-guide.md §"Script design".

**Touches.**
- `docbuilder/scripts/generate_pdf.py` (new)
- `docbuilder/tests/test_generate_pdf.py` (new)

**Done-check.**
```bash
cd aetheris-agents/docbuilder

python3 scripts/fetch_data.py data/sample_data.csv \
  | python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json - \
  | python3 scripts/generate_pdf.py --output-dir output --filename proposal

ls -lh output/proposal.pdf
python3 -m pytest tests/test_generate_pdf.py -v
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design" and
> `docbuilder/docs/doc-spec-schema.md` before writing any code.
>
> Implement `generate_pdf.py` using weasyprint. Same interface as previous
> renderers. Build an HTML string from the doc spec (one `<table>` per
> sheet, inline CSS for bold/alignment), then call `weasyprint.HTML(string=html).write_pdf(path)`.
>
> Tests: assert file exists and size > 0. Mark integration; skip if
> weasyprint not installed.
>
> Run the done-check and include its output in the review packet.

---

### t6 — Lightweight renderers (csv, json, xml, md)

**Scope.** Four remaining renderers, all using stdlib or lxml. Each is a
thin serialisation of the doc spec — no complex formatting. One script per
format. Tests for each.

**Contract refs.** agent-creation-guide.md §"Script design".

**Touches.**
- `docbuilder/scripts/generate_csv.py` (new)
- `docbuilder/scripts/generate_json.py` (new)
- `docbuilder/scripts/generate_xml.py` (new)
- `docbuilder/scripts/generate_md.py` (new)
- `docbuilder/tests/test_generate_csv.py` (new)
- `docbuilder/tests/test_generate_json.py` (new)
- `docbuilder/tests/test_generate_xml.py` (new)
- `docbuilder/tests/test_generate_md.py` (new)

**Do not generate.** Do not combine these into a single script.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

for fmt in csv json xml md; do
  python3 scripts/fetch_data.py data/sample_data.csv \
    | python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json - \
    | python3 scripts/generate_${fmt}.py --output-dir output --filename proposal
  echo "$fmt: $(ls -lh output/proposal.${fmt} 2>/dev/null || echo MISSING)"
done

python3 -m pytest tests/test_generate_csv.py tests/test_generate_json.py \
  tests/test_generate_xml.py tests/test_generate_md.py -v
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` §"Script design" and
> `docbuilder/docs/doc-spec-schema.md`.
>
> Implement the four lightweight renderers per t6 scope. Same interface
> as previous renderers (stdin, `--output-dir`, `--filename`).
>
> - `generate_csv.py`: one CSV per sheet; sheets separated by a blank line
>   and a `# Sheet: {name}` comment if multi-sheet. Use stdlib `csv`.
> - `generate_json.py`: pretty-printed JSON. Output is the doc spec's data
>   arrays only (strip formatting metadata — consumers want clean data).
> - `generate_xml.py`: `<document><sheet name="..."><row><cell>...</cell></row></sheet></document>`.
>   Use `xml.etree.ElementTree`.
> - `generate_md.py`: one markdown table per sheet with a `## {sheet_name}`
>   heading. Bold cells wrapped in `**...**`.
>
> Tests: all use `tmp_path`; assert file exists; assert content spot-checks
> (correct row count, expected cell value present). No external deps needed.
>
> Run the done-check and include its output in the review packet.

---

### t7 — docbuilder_orchestrator.exs + sprint case

**Scope.** The Aetheris agent that wires the pipeline together. Reads
`DOCBUILDER_TENANT`, `DOCBUILDER_DOC_TYPE`, `DOCBUILDER_VERSION`, and
`DOCBUILDER_DATA_PATH` from environment. Calls `fetch_data.py`,
`compute_doc.py`, then one `generate_{format}.py` per format in the doc
spec's `output_formats` array. Reports output paths and any failures.
Sprint case added to `sprint.sh`.

**Contract refs.** agent-creation-guide.md §"Agent file conventions"
(`__ENV__.file`, `overlay_base_dir: nil`, exact `run_command` format,
Rules section); §"Pre-flight checklist".

**Touches.**
- `docbuilder/agents/docbuilder_orchestrator.exs` (new)
- `docbuilder/runbook.md` (new — env vars, how to run, troubleshooting)
- `../aetheris/scripts/sprint.sh` (add `docbuilder` case)

**Do not generate.** No new Python scripts in this ticket.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

# Syntax/struct check (no LLM call)
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs")'

# Full sprint
DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
./scripts/sprint.sh docbuilder

# Verify outputs exist
ls -lh ../aetheris-agents/docbuilder/output/
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` in full and `CLAUDE.md` before
> writing any code. Pay special attention to: `__ENV__.file` pattern,
> `overlay_base_dir: nil`, exact `run_command` format (`command:` / `args:`
> fields shown explicitly), and the Rules section convention.
>
> Implement `docbuilder_orchestrator.exs` per t7 scope.
>
> System prompt must:
> 1. State the four env vars and what they mean.
> 2. Show exact `run_command` call for each script with `command: "python3"`.
> 3. Instruct: call fetch_data, then compute_doc (piping fetch output as
>    a temp file), then for each format in doc_spec.output_formats call
>    the matching generate script.
> 4. Include Rules: "If any script returns exit code 1, report the stderr
>    and stop. Do not retry or investigate manually."
>
> Use `context_strategy: :full` (pipeline is < 10 steps).
>
> Write `docbuilder/runbook.md` covering: required env vars, how to run
> the sprint, expected output, common failure modes.
>
> Add the `docbuilder` sprint case to `sprint.sh`.
>
> Run the done-check and include its output in the review packet.

---

### t8 — Docs sync + capability matrix update

**Scope.** Sync all docs to match what shipped. Update the capability matrix.
Add `docbuilder` to `docs/agent-creation-guide.md` §"Applying to upcoming
agents" retrospective note if warranted. Verify `docbuilder/README.md` open
questions are all resolved.

**Contract refs.** milestone-methodology.md §7 (milestone-end ritual);
aetheris-agents CLAUDE.md doc-sync DoD.

**Touches.**
- `docs/capability-matrix.md` (add docbuilder section — run the generator)
- `docbuilder/README.md` (close all open questions)
- `docbuilder/milestone.md` (this file — add milestone summary section)

**Done-check.**
```bash
# Regenerate capability matrix
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/agents/capability_matrix.exs

# Confirm docbuilder appears
grep -A 5 "docbuilder" ../aetheris-agents/docs/capability-matrix.md

# Confirm no open questions remain in README
grep "Open questions" ../aetheris-agents/docbuilder/README.md
```

**Claude-code prompt.**
> Read `CLAUDE.md`, `docs/milestone-methodology.md` §7, and
> `docbuilder/README.md` before starting.
>
> Perform the t8 docs sync per scope above. Regenerate the capability
> matrix. Resolve all remaining open questions in `docbuilder/README.md`
> (replace the open questions section with a "Decisions" subsection
> recording what was chosen and why). Write the milestone summary at the
> bottom of `docbuilder/milestone.md` (what shipped, what was deferred,
> surprises, open items for m2).
>
> Run the done-check and include its output in the review packet.

---

## Milestone summary

_(written by claude-code at milestone end, after t8)_
