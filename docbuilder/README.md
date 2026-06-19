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

### m2 — Template registry + delivery ✦ *backlog*

**Goal:** tenant templates managed centrally, not as flat files checked into
the repo. Output delivered to Drive or email automatically.

Scope:
- Template registry: Drive folder (one subfolder per tenant) or lightweight
  DB table — fetch template by `(tenant_id, doc_type, version)` at run time
- Template versioning: slug-based (`proposal_v1`, `proposal_v2`); old versions
  remain runnable
- `fetch_template.py` — resolves and downloads the correct template
- Drive upload integration (reuse `drive/scripts/drive_upload.py` pattern)
- Email delivery integration (reuse `email/scripts/email_send.py` pattern)
- Multi-source data: template `data_sources` array supports >1 entry; orchestrator calls `fetch_data.py` once per source; `compute_doc.py` receives all results and merges/joins before applying the template
- Runbook: tenant onboarding procedure (how to add a template to the registry)

Not in m2: conversational template editing.

---

### m3 — Conversational template editing ✦ *backlog*

**Goal:** users can refine a template via natural language. Each instruction
produces a structured patch. Patches are logged in a JSONL edit trail.
Re-render happens automatically after each accepted change.

Scope:
- **Patch schema** — atomic operations:
  `set_bold`, `set_align`, `set_column_width`, `add_aggregate_row`,
  `set_merge_range`, `add_logo`, `reorder_columns`, `rename_column`, etc.
- **JSONL edit log** — one line per patch, append-only; full audit trail;
  template state = replay of all patches from base
- `patch_template.py` — applies a patch JSON to a template JSON, deterministic
- `replay_template.py` — reconstructs current template from base + JSONL log
- Conversational agent: reads current template + user instruction → emits
  patch JSON → calls `patch_template.py` → calls renderer for preview
- Ambiguity handling: agent asks for clarification on underspecified
  instructions ("make it look more professional" → agent must clarify or
  decompose into concrete ops)
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
          {doc_type}_v{N}.json    ← flat-file templates (m1)
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
