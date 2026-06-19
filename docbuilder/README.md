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
generate_{format}.py   ← deterministic renderer → output file
```

The **doc spec JSON** is the handoff contract between compute and render.
It captures document structure, data, and formatting intent — independently
of output format.

**Template JSON** (one per tenant/doc-type, flat file in m1, registry in m2)
defines: sheets/sections, column order, merge regions, aggregate positions,
bold/alignment rules, output format(s) requested.

---

## Milestone Roadmap

### m1 — Core doc builder ✦ *build first*

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

### m2 — Template registry + base files + LLM-assisted selection ✦ *backlog*

**Goal:** tenant templates managed centrally. Base files (`.docx`, `.xlsx`)
carry branding — headers, footers, logos, fonts, colours. The LLM selects
the right doc type and variant from a known catalogue. Output delivered
automatically.

Scope:

**Template registry:**
- Registry: Drive folder (one subfolder per tenant) or lightweight DB table
- Each tenant has a catalogue of doc types: `proposal`, `invoice`, `rfq`, etc.
- Each doc type has: a JSON config (`proposal_v1.json`) + optional base files
  per format (`proposal_v1.docx`, `proposal_v1.xlsx`)
- Template versioning: slug-based (`proposal_v1`, `proposal_v2`); old versions
  remain runnable
- `list_templates.py` — returns available `{doc_type, variants, description}`
  for a given tenant; used by the orchestrator to give the LLM the catalogue
- `fetch_template.py` — fetches a specific template JSON + base file by
  `(tenant_id, doc_type, variant)`
- Runbook: tenant onboarding procedure

**Base file support in renderers:**
- Renderers check for a base file (`{doc_type}_{version}.docx` /
  `{doc_type}_{version}.xlsx`) alongside the JSON config
- If present: open it as the starting workbook/document (inherits branding,
  header, footer, logo, named styles, print settings)
- If absent: create fresh (current m1 behaviour — preserved as fallback)
- `generate_docx.py`: `Document("base.docx")` instead of `Document()`
- `generate_xlsx.py`: `openpyxl.load_workbook("base.xlsx")` instead of
  `Workbook()`; sheet names in the base file must match the template's
  sheet names or be cleared/replaced

**LLM template selection (Options A + B):**

Option A — caller provides `doc_type`; LLM selects `base_variant`:
- Orchestrator calls `list_templates.py` to get available variants
- LLM receives: `doc_type` (known), variant catalogue, context (customer
  name, deal type, tone)
- LLM picks variant and justifies choice in structured JSON:
  `{doc_type, variant, rationale}`
- Scripts do everything after that

Option B — caller provides context; LLM derives `doc_type` + `variant`:
- Orchestrator calls `list_templates.py` for the full tenant catalogue
- LLM receives: context (deal description, customer, amount), full catalogue
  with descriptions
- LLM picks `{doc_type, variant, rationale}`
- Input: `DOCBUILDER_CONTEXT` env var (structured JSON with deal fields)

Both A and B are in m2. Classification is LLM work; template fetch and
rendering are scripts.

**Delivery:**
- Drive upload integration (reuse `drive/scripts/drive_upload.py` pattern)
- Email delivery integration (reuse `email/scripts/email_send.py` pattern)

**Multi-source data:**
- Template `data_sources` array supports >1 entry
- Orchestrator calls `fetch_data.py` once per source
- `compute_doc.py` receives all results and merges/joins before applying
  the template

Not in m2: natural language requests, conversational template editing.

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
| LLM selects doc type + variant; scripts do everything after | Classification (which template to use) is ambiguous, context-dependent LLM work. Fetch, compute, render are deterministic. The LLM outputs a small structured JSON `{doc_type, variant, rationale}`; all downstream steps are scripted. |
| NL request extraction (Option C) requires a confirmation gate | LLM-extracted data fields must be shown to the user before rendering. A silently wrong customer-facing document is worse than no document. Gate is mandatory in m3; no silent rendering on extraction alone. |

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
          {doc_type}_v{N}.json    ← structure + data config (m1 flat file)
          {doc_type}_v{N}.docx    ← branding base file, optional (m2)
          {doc_type}_v{N}.xlsx    ← branding base file, optional (m2)
      .gitignore                  ← excludes real data, output/
    docs/
      t*-implementation-notes.md
    output/
      .gitkeep
    scripts/
      fetch_data.py
      compute_doc.py
      generate_xlsx.py
      generate_docx.py
      generate_pdf.py
      generate_csv.py
      generate_json.py
      generate_xml.py
      generate_md.py
      list_templates.py           ← m2: catalogue for LLM selection
      fetch_template.py           ← m2: fetches JSON config + base file
    tests/
      conftest.py
      test_compute_doc.py
      test_generate_xlsx.py
      test_generate_docx.py
      ...
    milestone.md                  ← m1 milestone doc (canonical)
    README.md                     ← this file
    runbook.md
```

---

## Key contracts

- `agent-creation-guide.md` — authoritative pattern for all agent/script work
- `milestone-methodology.md` — ticket loop, review format, done-check rules
- `aetheris-agents/CLAUDE.md` — standing conventions; read before any session
- `aetheris/CLAUDE.md` — harness-side conventions

---

## m1 scope decisions

All open questions from the start of m1 have been resolved:

| Question | Decision |
|----------|----------|
| Data source interface | m1 supports local CSV/JSON only. `fetch_data.py` does not transform. HTTP sources and multi-source joins are m2. |
| PDF renderer | weasyprint for m1. Pure Python, no system dependencies. reportlab is backlog — the doc spec contract means swapping is a single-script change. |
| Multi-format in one run | Orchestrator renders all formats listed in `output_formats` in sequence. No per-invocation format override in m1. |
