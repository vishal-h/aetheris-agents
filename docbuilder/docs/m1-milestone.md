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
and one or more raw source JSON files (m1: exactly one). Processes sheets
in **two passes** — this is required by the `summary_rows` design introduced
in t1:
- Pass 1: data-bearing sheets (`source_key` non-null) — apply column mapping
  (`source_field` → column), compute `aggregate_rows` values (sums, counts,
  averages), derive merge cell coordinates, resolve bold/align flags per cell.
- Pass 2: summary sheets (`source_key` null) — resolve `summary_rows` entries
  by referencing the pre-computed aggregate values from Pass 1 sheets.
  `aggregate_ref` rows look up their value from the named source sheet and
  column. `static` rows are passed through directly.

The doc spec emitted is complete and format-agnostic: renderers receive
pre-computed cell values with bold/align flags and must not compute anything.

**Contract refs.** agent-creation-guide.md §"Script design" (one
responsibility per script; stdout is the contract; exit codes); §"Scripts
must be runnable standalone"; README.md §"Design decisions"
(fetch/transform split; multi-source is m2); `docbuilder/docs/template-schema.md`
(authoritative — do not restate schema here).

**Touches.**
- `docbuilder/docs/milestones/m-docbuilder-m1-t1-implementation-notes.md`
  (new — **write this first**, backfilling the t1 audit trail; see prompt)
- `docbuilder/scripts/fetch_data.py` (new)
- `docbuilder/scripts/compute_doc.py` (new)
- `docbuilder/tests/conftest.py` (new)
- `docbuilder/tests/test_fetch_data.py` (new)
- `docbuilder/tests/test_compute_doc.py` (new)
- `docbuilder/docs/doc-spec-schema.md` (new — documents doc spec JSON fields)
- `docbuilder/docs/milestones/m-docbuilder-m1-t2-implementation-notes.md`
  (new — write at end of session before done-check)

**Do not generate.** No agent files, no renderer scripts in this ticket.
Do not add transformation logic to `fetch_data.py`.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# fetch_data standalone
python3 scripts/fetch_data.py --key main data/sample_data.csv | python3 -m json.tool

# full pipeline — Line Items sheet + Summary sheet both appear in output
python3 scripts/fetch_data.py --key main data/sample_data.csv > /tmp/raw.json
python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json /tmp/raw.json \
  | python3 -m json.tool

# Verify both sheets present and Summary sheet has pre-computed values
python3 scripts/fetch_data.py --key main data/sample_data.csv > /tmp/raw.json
python3 scripts/compute_doc.py data/templates/demo/proposal_v1.json /tmp/raw.json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
    sheets=[s['name'] for s in d['sheets']]; \
    assert sheets == ['Line Items', 'Summary'], sheets; \
    print('sheets OK:', sheets)"

# Tests
python3 -m pytest tests/test_fetch_data.py tests/test_compute_doc.py -v
```

**Claude-code prompt.**
> Read `docs/agent-creation-guide.md` (full), `CLAUDE.md`,
> `docbuilder/docs/template-schema.md` (authoritative schema — do not
> restate or paraphrase it), and `docbuilder/README.md` §"Design decisions"
> before writing any code.
>
> Also read `docs/reviews/m-docbuilder-m1-t1-review.md` — it contains
> three findings from the t1 review that this session must address.
>
> **First action — before any scripts:** write
> `docbuilder/docs/milestones/m-docbuilder-m1-t1-implementation-notes.md`.
> This backfills the missing t1 audit trail (t1 review finding 1, blocking).
> Content must cover:
> - The `summary_rows` vs `aggregate_rows` design decision: why two distinct
>   keys were used (data-sheet aggregates vs cross-sheet summary references),
>   and the downstream implication (two-pass processing required in t2).
> - The `source_key: null` pattern for summary sheets.
> - Anything else that required a decision during t1 that is not obvious
>   from reading the diff.
> Per aetheris-agents--CLAUDE.md §"Implementation notes": do not restate
> the diff; capture only context that does not survive in the code itself.
>
> **Implement `fetch_data.py`**: accepts `--key KEY` and one positional
> path arg. Outputs `{"key": KEY, "rows": [...]}` to stdout. Rows are
> dicts (CSV header → value for CSV; array elements for JSON). No
> filtering, no renaming, no computation. Errors to stderr, exit 1.
>
> **Implement `compute_doc.py`**: accepts template path and one or more
> raw source JSON paths as positional args (m1 validates exactly one;
> error and exit 1 if more). Two-pass processing as described in scope:
> - Pass 1: data-bearing sheets (`source_key` non-null). For each sheet,
>   map raw rows through `columns[].source_field`, resolve bold/align per
>   cell, compute all `aggregate_rows` values. Store computed aggregates
>   keyed by `(sheet_name, column_source_field, function)` for Pass 2.
> - Pass 2: summary sheets (`source_key` null). For `aggregate_ref` rows,
>   look up the pre-computed value from Pass 1 store. For `static` rows,
>   pass through label and value directly.
> Output doc spec JSON to stdout. Each row in the spec is an array of
> `{"value": ..., "bold": bool, "align": "left"|"right"|"center"}` cell
> objects. Renderers must not compute anything.
>
> **Write `docbuilder/docs/doc-spec-schema.md`**: full doc spec format
> with field types and one complete example (the demo proposal output).
>
> **Write pytest unit tests** covering: correct column mapping via
> `source_field`, aggregate computation (sum, count, avg), two-pass
> summary sheet resolution (`aggregate_ref` and `static`), merge range
> derivation, missing source field (exit 1), multi-source rejection
> (exit 1 in m1), `summary_rows` referencing a non-existent source sheet
> (exit 1).
>
> **Last action — after done-check passes:** write
> `docbuilder/docs/milestones/m-docbuilder-m1-t2-implementation-notes.md`
> covering decisions made, deviations from scope (if any), and anything
> t3–t4 renderers need to know about the doc spec shape.
>
> Run the done-check and include its output in the review packet.
> Review packet must contain: ticket ID + scope statement, diff,
> both implementation notes files, done-check output.

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
- `docbuilder/docs/milestones/m-docbuilder-m1-t3-implementation-notes.md` (new — write after done-check passes)

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
> After done-check passes, write
> `docbuilder/docs/milestones/m-docbuilder-m1-t3-implementation-notes.md`
> covering openpyxl-specific decisions, any doc spec fields that needed
> clarification, and anything t4–t5 renderers should know.
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
- `docbuilder/docs/milestones/m-docbuilder-m1-t4-implementation-notes.md` (new — write after done-check passes)

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
> After done-check passes, write
> `docbuilder/docs/milestones/m-docbuilder-m1-t4-implementation-notes.md`.
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
- `docbuilder/docs/milestones/m-docbuilder-m1-t5-implementation-notes.md` (new — write after done-check passes)

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
> After done-check passes, write
> `docbuilder/docs/milestones/m-docbuilder-m1-t5-implementation-notes.md`
> covering any weasyprint-specific gotchas, HTML template decisions, and
> anything relevant for the t6 renderers or the t7 orchestrator.
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
- `docbuilder/docs/milestones/m-docbuilder-m1-t6-implementation-notes.md` (new — write after done-check passes)

**Do not generate.** Do not combine these into a single script.

**Runbook update rule.** No new env vars or startup steps in this ticket — no runbook update required.

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
> Also read `docbuilder/docs/milestones/m-docbuilder-m1-t5-implementation-notes.md`
> §"t6 notes" before writing any code — it contains format-specific decisions
> already made.
>
> After done-check passes, write
> `docbuilder/docs/milestones/m-docbuilder-m1-t6-implementation-notes.md`
> covering any per-format decisions (e.g. how multi-sheet CSV was handled,
> what JSON output shape was chosen) and anything t7 needs to know.
>
> **Review packet must open with the full done-check output block** (pipeline
> file listing + complete `pytest -v` output with individual test names,
> PASSED/FAILED, and elapsed time). Do not submit the packet without it.

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
- `docbuilder/docs/milestones/m-docbuilder-m1-t7-implementation-notes.md` (new — write after done-check passes)

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
> After done-check passes, write
> `docbuilder/docs/milestones/m-docbuilder-m1-t7-implementation-notes.md`
> covering orchestrator design decisions, any system prompt iteration that
> was needed, and anything the t8 docs sync should know.
>
> **Review packet must open with the full done-check output block** (syntax
> check output + full sprint run output + `ls -lh` of output files). Do not
> submit the packet without it.

---

### t8 — Docs sync + capability matrix update

**Scope.** Sync all docs to match what shipped. Update the capability matrix.
Add `docbuilder` to `docs/agent-creation-guide.md` §"Applying to upcoming
agents" retrospective note if warranted. Verify `docbuilder/README.md` open
questions are all resolved.

**Contract refs.** milestone-methodology.md §7 (milestone-end ritual);
aetheris-agents CLAUDE.md doc-sync DoD.

**Touches.**
- `docs/capability-matrix.md` (update — run the generator)
- `docbuilder/README.md` (close all open questions)
- `docbuilder/milestone.md` (add milestone summary section at bottom)

**Done-check.**
```bash
# Regenerate capability matrix
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/agents/capability_matrix.exs

# Confirm docbuilder appears
grep -A 5 "docbuilder" ../aetheris-agents/docs/capability-matrix.md

# Confirm no open questions remain in README
grep -c "~~" ../aetheris-agents/docbuilder/README.md  # all questions struck-through

# Confirm all implementation notes files exist
ls ../aetheris-agents/docbuilder/docs/milestones/
```

**Claude-code prompt.**
> Read `CLAUDE.md`, `docs/milestone-methodology.md` §7, and
> `docbuilder/README.md` before starting.
>
> Also read all implementation notes files committed during this milestone:
> `docbuilder/docs/milestones/m-docbuilder-m1-t1-implementation-notes.md`
> through `m-docbuilder-m1-t7-implementation-notes.md`. These are the
> primary input for the milestone summary — do not restate the diffs,
> synthesise the decisions and open threads across tickets.
>
> Perform the t8 docs sync per scope above:
> - Regenerate the capability matrix.
> - Resolve all remaining open questions in `docbuilder/README.md`
>   (replace the open questions section with a "Decisions" subsection).
> - Write the milestone summary at the bottom of `docbuilder/milestone.md`
>   covering: what shipped, what was deferred (with → m2/m3 refs), surprises
>   or findings that recurred across tickets (candidates for CLAUDE.md
>   promotion per methodology §7), and open items for m2.
>
> Run the done-check and include its output in the review packet.

---

## Milestone summary

### What shipped

| Ticket | Artifact | Notes |
|--------|----------|-------|
| t1 | Template schema, `demo/proposal_v1.json`, `sample_data.csv` | Two-sheet B2B proposal fixture with merge ranges, aggregate rows, multi-format output |
| t2 | `fetch_data.py`, `compute_doc.py` | Two-pass engine (data-bearing sheets → summary sheets); doc spec JSON contract |
| t3 | `generate_xlsx.py` | openpyxl; merged cells, column widths, numeric formatting, aggregate border |
| t4 | `generate_docx.py` | python-docx; tables, alignment, bold; merge_ranges represented as sheet headings |
| t5 | `generate_pdf.py` | weasyprint; HTML intermediate; `_build_html()` pure function; merge_ranges as `<th colspan>` |
| t6 | `generate_csv.py`, `generate_json.py`, `generate_xml.py`, `generate_md.py` | stdlib only; 44 tests |
| t7 | `docbuilder_orchestrator.exs`, `runbook.md`, sprint case | Linear pipeline; `--input FILE` added to all renderers |
| t8 | Capability matrix, docs sync, learning promotions | `docbuilder/milestone.md` |

**Test count at milestone close:** 123 tests, all passing.

**Output formats proven end-to-end:** xlsx, pdf (via `output_formats` in demo template). csv, json, xml, md available and unit-tested.

---

### What was deferred

| Item | Target |
|------|--------|
| Template registry (fetch_template.py, tenant onboarding) | → m2 |
| Drive upload / email delivery integration | → m2 |
| Multi-source data fetch and join (template `data_sources` length > 1) | → m2 |
| Derived/formula columns in templates | → m2+ |
| Conversational template editing (patch schema, JSONL edit log) | → m3 |
| Real tenant data (sample data only in m1) | operational constraint, not deferred |
| reportlab PDF renderer | → backlog (single-script swap when needed) |

The template schema is forward-compatible with multi-source (`data_sources` is an array from day one); m1 validates that the array has exactly one entry.

---

### Surprises and recurring findings

#### 1. `run_command` has no stdin parameter — renderers need `--input FILE`

Discovered at t7 when the orchestrator tried to pipe the doc spec to `generate_xlsx.py` via stdin. `run_command` schema has no `stdin` parameter. The first attempt used `sh -c "cat spec.json | python3 scripts/generate_xlsx.py ..."` — the LLM did not follow this reliably and the script timed out.

**Fix:** added `--input FILE` (optional, falls back to stdin) to all 7 generate scripts. This is now a standing pattern.

**Learning promoted:** see `agent-creation-guide.md` §"Common failure modes" and `CLAUDE.md` §"Learning — m1-docbuilder".

#### 2. merge_ranges diverge significantly across renderers

| Renderer | merge_ranges handling |
|----------|-----------------------|
| xlsx | Merged cells via `worksheet.merge_cells` — value preserved |
| pdf | `<th colspan="N">` — value preserved |
| docx | Silently substituted with sheet name heading — value **lost** |
| csv, json, xml, md | Silently dropped — value **lost** |

Template authors who rely on merge_range values appearing faithfully in docx output will be surprised. Documented in t4 and t6 implementation notes. Added to `doc-spec-schema.md` §"Format characteristics".

#### 3. `_build_html()` pure function pattern worth propagating

Separating the HTML builder from the `weasyprint` call (t5) gave 8 fast unit tests with zero PDF rendering overhead. The integration tests (5 tests) cover weasyprint specifically. Useful wherever a renderer has a testable intermediate representation.

#### 4. max_steps sizing for a linear pipeline

The docbuilder pipeline consumes approximately: 4 setup tool calls (fetch, write_raw, compute, write_spec) + 1 LLM parse step + N render calls + 1 LLM per step = ~12 steps minimum for 2 formats. Set `max_steps: 20` with 8 steps of headroom. The first run hit the initial 15-step limit before completing.

#### 5. Review packet done-check completeness (raised t4 → t6)

The pipeline file listing (`ls -lh output/proposal.{fmt}`) was missing from packets at t5 and t6. The t4 packet was returned unreviewed. Resolution: milestone doc was updated to require "Review packet must open with the full done-check output block." This applies to all future use-case tickets.

---

### Open items for m2

- `fetch_template.py` — resolves template from registry by `(tenant, doc_type, version)`
- Multi-source joins in `compute_doc.py` (schema already supports it; m1 rejects arrays > 1)
- Non-convertible numeric string cells in xlsx renderer should emit a stderr warning instead of silently rendering as text
- `generate_json.py` drops row `type` field — m2 consumers may want `header`/`data`/`aggregate` metadata
- `--input` file handles should use `with` block (F1 from t7 review) — harmless for m1 short-lived scripts, revisit if scripts become longer-lived
- Sprint case `run_id` extraction now fixed but the underlying `no-json` label in sprint output is cosmetic noise — trace to the log line prefix in run.json format
