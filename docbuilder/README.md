# docbuilder — README & Roadmap

> Aetheris use case: data-driven document generation from tenant-scoped templates.
> Lives at `aetheris-agents/docbuilder/`.

---

## What this is

`docbuilder` is an Aetheris agent that fetches data from one or more sources,
applies a tenant-scoped template, and renders a formatted output document.

The agent decides — which template, whether the data satisfies it, how to
handle gaps. Python scripts do everything else: fetch, compute, render.

Output formats: **xlsx, docx, pdf, csv, json, xml, md**. A single run can
produce multiple formats from the same doc spec.

Typical use case: a customer proposal Excel sheet with merged headers, bold
columns, aggregate rows, and multiple sheets — generated from live data and
a pre-approved tenant template.

---

## Architecture

```
data source(s)
    │
    ▼
fetch_data.py          ← pulls ONE source, outputs raw JSON as-is (no transform)
    │  (called once per source; orchestrator collects results)
    ▼
compute_doc.py         ← merges sources, transforms, applies template → doc spec JSON
    │
    ▼
render_template.py     ← (m2a, PDF only) substitutes variables into Markdown template
    │                     → combined HTML (prose + tables) for weasyprint
    ▼
generate_{format}.py   ← deterministic renderer → output file
    │                     xlsx/docx: opens base file if present, writes into it
    │                     pdf: weasyprint from HTML (plain or Markdown-rendered)
    ▼
output file            ← branded, data-filled document
```

The **doc spec JSON** is the handoff contract between compute and render.
It captures document structure, data, and formatting intent — independently
of output format.

---

## Template model

Each tenant/doc-type has a template bundle — a set of files in
`data/templates/{tenant_id}/`:

| File | Purpose | Formats |
|---|---|---|
| `{doc_type}_v{N}.json` | Structure: sheets, columns, aggregates, data sources | all |
| `{doc_type}_v{N}.docx` | Branding base file: header, footer, logo, styles | docx |
| `{doc_type}_v{N}.xlsx` | Branding base file: logo row, named styles, sheet layout | xlsx |
| `{doc_type}_v{N}.md.template` | Prose narrative with `{{variable}}` placeholders | pdf |
| `{doc_type}_v{N}.css` | Brand styles: fonts, colours, `@page` header/footer | pdf |
| `catalogue.json` | Doc type catalogue for LLM selection (m2a+) | — |

**The split:** JSON carries structure and data mapping. Base files (docx/xlsx)
carry visual identity. Markdown template + CSS carry prose and PDF branding.
Each can evolve independently.

**Row alignment convention (xlsx base files):** `header_row` in the JSON
template must equal the first empty row in the base file. Rows above
`header_row` are owned by the base file (branding); rows from `header_row`
down are owned by the renderer (data). An optional `data_col_start` field
(default: 1) controls which column data writing begins at.

**PDF rendering modes:**
- *Structured mode* (m1, current): `_build_html()` generates HTML directly
  from the doc spec. No Markdown template needed.
- *Narrative mode* (m2a): `render_template.py` reads the `.md.template`,
  substitutes `{{variables}}` and `{{>table_partial}}` placeholders, applies
  `.css` for branding, outputs combined HTML → weasyprint.
- Both modes produce the same weasyprint input — `generate_pdf.py` is
  unchanged.

---

## Milestone Roadmap

### m1 — Core doc builder ✦ *done*

**Goal:** end-to-end working pipeline. Data in, formatted document out.
Flat-file templates. Single orchestrator agent. All output formats supported.

Scope:
- Template schema (JSON) — defines structure, columns, formatting, output format(s)
- Sample tenant template (proposal xlsx, with merged headers + aggregate rows)
- `fetch_data.py` — reads ONE local CSV or JSON file, outputs raw rows as JSON array; no transformation
- `compute_doc.py` — receives raw data + template; owns all transformation (column mapping, joins, aggregations); produces doc spec JSON
- `generate_xlsx.py` — openpyxl; merged cells, bold, column widths, multi-sheet
- `generate_docx.py` — python-docx; tables, styles, headers/footers
- `generate_pdf.py` — weasyprint; HTML → PDF
- `generate_csv.py`, `generate_json.py`, `generate_xml.py`, `generate_md.py` — stdlib/lxml
- `docbuilder_orchestrator.exs` — fetch → compute → render(s), `overlay_base_dir: nil`
- pytest suite for compute + each renderer
- Sprint case in `sprint.sh`

Not in m1: template registry, conversational editing, delivery (email/Drive).

---

### m2a — Template foundations ✦ *backlog — build next*

**Goal:** branded output, queryable template catalogue, multi-source data,
Markdown+CSS narrative PDF. All deterministic — no LLM selection yet.
Independently shippable.

Scope:

**Base file support in xlsx + docx renderers:**
- Base files (`.docx`, `.xlsx`) committed alongside JSON config
- Renderers check for a base file at runtime; open it if present, create
  fresh if absent (m1 fallback preserved)
- `generate_docx.py`: `Document("base.docx")` instead of `Document()`;
  new optional `"table_style"` field in template JSON (default: `"Table Grid"`)
- `generate_xlsx.py`: `openpyxl.load_workbook("base.xlsx")` instead of
  `Workbook()`; writes from `header_row` downward, preserving branding rows
  above; new optional `"data_col_start"` field in template JSON (default: 1)
- Demo base files committed: `demo/proposal_v1.docx`, `demo/proposal_v1.xlsx`

**Markdown + CSS for PDF (narrative mode):**
- `{doc_type}_v{N}.md.template` — prose with `{{variable}}` scalar
  substitutions and `{{>sheet_name}}` table partials
- `{doc_type}_v{N}.css` — brand styles: fonts, colours, `@page` rules
  for PDF header/footer/margins; replaces hardcoded CSS in `_build_html()`
- `render_template.py` — new script: reads `.md.template`, substitutes
  scalar variables from a context JSON, replaces table partials with HTML
  tables rendered from the doc spec, applies `.css`, outputs combined HTML
  to stdout
- `generate_pdf.py` updated: if `.md.template` exists for the template,
  calls `render_template.py` pipeline; otherwise falls back to structured
  mode (`_build_html()` — m1 behaviour preserved)
- Demo files committed: `demo/proposal_v1.md.template`,
  `demo/proposal_v1.css`

**Template catalogue:**
- `data/templates/{tenant}/catalogue.json` — lists available doc types,
  variants, and descriptions; committed flat file in m2a, Drive-hosted in m2b
- `list_templates.py` — reads `catalogue.json`; outputs structured JSON;
  used by orchestrator in m2b for LLM selection

**Multi-source data:**
- `compute_doc.py` updated: accepts multiple source JSON paths; merges/joins
  before applying template
- Orchestrator calls `fetch_data.py` once per source
- Demo template updated with a two-source example

**Orchestrator updated:**
- Reads base file paths from template bundle and passes to renderers via
  `--base-file` (xlsx/docx) and `--template-dir` (pdf) flags
- Calls `fetch_data.py` N times for multi-source templates

**Template schema additions (m2a):**
- `"table_style"` — optional string, docx renderer table style
  (default: `"Table Grid"`)
- `"data_col_start"` — optional integer, xlsx first data column
  (default: 1)

Not in m2a: LLM selection, Drive registry, delivery.

---

### m2b — LLM selection + Drive registry + delivery ✦ *backlog*

**Goal:** LLM picks the right doc type and variant from the catalogue.
Templates and base files fetched from Drive at runtime. Output delivered
to Drive or email automatically.

Depends on: m2a (catalogue, base file support).

Scope:

**Drive registry:**
- Templates and base files move from flat files to Drive (one subfolder
  per tenant)
- `fetch_template.py` — downloads JSON config + base file from Drive by
  `(tenant_id, doc_type, variant)`; caches locally for the run
- `list_templates.py` updated: reads from Drive rather than flat
  `catalogue.json`
- Runbook: tenant onboarding procedure (how to add a template to Drive)

**LLM template selection (Options A + B):**

Option A — caller provides `doc_type`; LLM selects variant:
- `DOCBUILDER_DOC_TYPE` set by caller; `DOCBUILDER_CONTEXT` provides
  context (customer name, deal type, tone)
- Orchestrator calls `list_templates.py`, passes catalogue + context to LLM
- LLM outputs `{doc_type, variant, rationale}` as structured JSON
- Scripts fetch and render from there

Option B — caller provides context only; LLM derives both:
- `DOCBUILDER_CONTEXT` contains deal fields; no `DOCBUILDER_DOC_TYPE`
- LLM receives full tenant catalogue + context, picks `{doc_type, variant}`
- Same downstream pipeline

**Delivery:**
- Drive upload (reuse `drive/scripts/drive_upload.py`)
- Email delivery (reuse `email/scripts/email_send.py`)
- Orchestrator extended: select → fetch → fetch_data → compute → render → deliver

Not in m2b: natural language requests, conversational template editing.

---

### m3 — NL requests + conversational template editing ✦ *backlog*

**Goal:** Option C — user provides a natural language request; the LLM
extracts data fields, selects the template, and fills values. Users can
also refine a generated document via natural language instructions.

Scope:

**Natural language request handling (Option C):**
- Input: freeform text — "Generate a formal quote for Acme for 40 days of
  consulting at £1,200/day including our standard payment terms"
- LLM extracts: structured data fields (customer, line items, amounts,
  terms), infers `doc_type` + `variant`
- Extracted fields feed into the existing `compute_doc.py` pipeline
- Ambiguity handling: LLM asks clarifying questions before rendering if
  required fields are missing or ambiguous
- Reliability gate: extracted fields shown to the user for confirmation
  before rendering — LLM extraction errors must not silently produce a
  wrong customer-facing document

**Conversational template editing:**
- **Patch schema** — atomic operations:
  `set_bold`, `set_align`, `set_column_width`, `add_aggregate_row`,
  `set_merge_range`, `add_logo`, `reorder_columns`, `rename_column`, etc.
- **JSONL edit log** — one line per patch, append-only; full audit trail;
  template state = replay of all patches from base
- `patch_template.py` — applies a patch JSON to a template JSON, deterministic
- `replay_template.py` — reconstructs current template from base + JSONL log
- Conversational agent: reads current template + user instruction → emits
  patch JSON → calls `patch_template.py` → calls renderer for preview
- Ambiguity handling: agent clarifies underspecified instructions before
  applying patches
- Save path: accepted patches written to JSONL log; template registry updated
  (m2 dependency)

Not in m3: multi-user collaboration on templates, approval workflows.

---

## Design decisions (recorded here, not re-litigated per ticket)

| Decision | Rationale |
|---|---|
| Template is JSON (not JSONL) | A template is one structured object. JSONL is for the edit log (stream of patches), not the template itself. |
| Doc spec JSON as compute/render handoff | Decouples data logic from rendering. Renderers are independently testable. |
| `overlay_base_dir: nil` | Output files are the deliverable — must survive the run. |
| One renderer script per format | Each format has different dependencies (openpyxl, python-docx, weasyprint). Splitting means integration tests can skip missing tools. |
| Agent reads template at runtime | Template is data, not code. Agent validates fit between data and template; scripts do the rest. |
| JSONL edit log for m3 | Append-only audit trail; replay semantics; each conversational instruction maps to exactly one line. |
| `fetch_data.py` does not transform | One responsibility per script. Fetch = pull raw rows and output as-is. Transform = `compute_doc.py`. Mixing them makes both untestable in isolation. |
| Transformation lives in `compute_doc.py` | Column mapping, joins, aggregations, derived fields are all deterministic logic that belongs in compute. Renderers receive pre-computed values and must not compute anything. |
| Multi-source is m2, not m1 | The template schema includes a `data_sources` array from day one (no breaking change later), but m1 validates that the array has exactly one entry. Multi-source fetch + merge lands in m2 once the single-source pipeline is proven. |
| PDF renderer: weasyprint for m1 | Pure Python, no system dependencies beyond the package. reportlab is backlog — the doc spec contract means switching is a single-script swap with no upstream impact. |
| Base files carry branding; JSON config carries structure | `.docx`/`.xlsx` base files hold headers, footers, logos, named styles. JSON templates define sheets, columns, aggregates. Keeping them separate means branding can change without touching data config and vice versa. |
| Base files committed in m2a, Drive-hosted in m2b | Same pattern as JSON configs in m1 — flat files first, registry second. Renderer base file support is the m2a work; where files come from is a registry concern that lands in m2b. |
| Registry storage: Drive folder (m2b) | Drive is self-contained, reuses existing `drive/` scripts, templates are editable files. No schema needed. Natural fit since m2b delivers via Drive anyway. |
| LLM selects doc type + variant; scripts do everything after | Classification (which template to use) is ambiguous, context-dependent LLM work. Fetch, compute, render are deterministic. The LLM outputs a small structured JSON `{doc_type, variant, rationale}`; all downstream steps are scripted. |
| NL request extraction (Option C) requires a confirmation gate | LLM-extracted data fields must be shown to the user before rendering. A silently wrong customer-facing document is worse than no document. Gate is mandatory in m3; no silent rendering on extraction alone. |
| Markdown + CSS for PDF narrative (m2a) | Structured mode (`_build_html()`) suits tabular data. Narrative mode (`.md.template` + `.css`) suits prose-heavy documents. Both feed weasyprint — `generate_pdf.py` is unchanged. The two modes coexist: structured is the fallback when no `.md.template` exists. |
| `header_row` convention for xlsx base files | `header_row` in the template JSON must equal the first empty row in the base file. Rows above are owned by the base file (branding); rows from `header_row` down are owned by the renderer. No named range needed — `header_row` is the single source of truth, editable in JSON. |
| `data_col_start` optional field | Controls which column the renderer starts writing data into. Allows base files with a label or index column at column A that the renderer should not overwrite. Default: 1 (first column). |
| `table_style` optional field (docx) | Makes the docx table style configurable per template rather than hardcoded as `"Table Grid"`. Allows base files with custom named styles to drive table appearance. Default: `"Table Grid"`. |

---

## Repository layout

```
aetheris-agents/
  docbuilder/
    agents/
      docbuilder_orchestrator.exs
    data/
      sample_data.csv             ← committed (anonymised)
      templates/
        {tenant_id}/
          catalogue.json          ← doc type catalogue (m2a flat file)
          {doc_type}_v{N}.json    ← structure + data config
          {doc_type}_v{N}.docx    ← branding base file (m2a, optional)
          {doc_type}_v{N}.xlsx    ← branding base file (m2a, optional)
          {doc_type}_v{N}.md.template  ← PDF prose narrative (m2a, optional)
          {doc_type}_v{N}.css     ← PDF brand styles (m2a, optional)
      .gitignore
    docs/
      milestones/
      reviews/
    output/
      .gitkeep
    scripts/
      fetch_data.py
      compute_doc.py
      render_template.py          ← m2a: Markdown+CSS → HTML for PDF
      generate_xlsx.py
      generate_docx.py
      generate_pdf.py
      generate_csv.py
      generate_json.py
      generate_xml.py
      generate_md.py
      list_templates.py           ← m2a: reads catalogue.json
      fetch_template.py           ← m2b: fetches from Drive
    tests/
      ...
    docs/milestone-m1.md
    docs/milestone-m2a.md         ← m2a milestone doc (to be created)
    README.md
    runbook.md
```

---

## Key contracts

- `agent-creation-guide.md` — authoritative pattern for all agent/script work
- `milestone-methodology.md` — ticket loop, review format, done-check rules
- `aetheris-agents/CLAUDE.md` — standing conventions; read before any session
- `aetheris/CLAUDE.md` — harness-side conventions

---

## Open questions (to resolve before or during m1)

~~1. **Data source interface** — for m1, does `fetch_data.py` support only
   local CSV/JSON, or also a simple HTTP GET? Decide before t1.~~
   **Resolved:** m1 supports local CSV/JSON only. `fetch_data.py` does not
   transform. HTTP sources and multi-source joins are m2.

~~2. **PDF renderer** — weasyprint (HTML → PDF, pure Python) vs reportlab
   (programmatic, more control). weasyprint is simpler for m1 if output
   quality is acceptable.~~
   **Resolved:** weasyprint for m1. reportlab backlog (m2 or later).

~~3. **Multi-format in one run** — does the orchestrator render all formats
   listed in the template's `output_formats` array in sequence, or does
   the caller specify which format at invocation time? Sequence is simpler.~~
   **Resolved:** orchestrator renders all formats in `output_formats` in
   sequence. No per-invocation override in m1.
