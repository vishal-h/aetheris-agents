# Docbuilder Runbook

Operational guide for the docbuilder pipeline.

---

## Required env vars

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCBUILDER_TENANT` | Tenant name — selects the tenant subtree (`data/templates/{tenant}/` locally, or the Drive subtree) | `demo` |
| `DOCBUILDER_CONTEXT` | The single input blob — inline JSON of all run fields (see `docs/context-schema.md`). Required fields: `title`, `client_name`, `client_email`, `date`. Optional `doc_type` (selects Option A). | `{"title":"…","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}` |
| `ANTHROPIC_API_KEY` | Anthropic API key for the LLM | _(set in shell)_ |

> m2b note: `DOCBUILDER_DOC_TYPE` / `DOCBUILDER_VERSION` / `DOCBUILDER_DATA_PATH` (m1/m2a)
> are gone — the doc type/variant come from `DOCBUILDER_CONTEXT` + the catalogue (LLM
> selection), and data-source paths come from the template.

Optional — delivery (PHASE E/F skip when absent):

| Variable | Description |
|----------|-------------|
| `DRIVE_DOCBUILDER_ID` | `docbuilder` Shared Drive root id. Set → PHASE E uploads outputs to `{tenant}/output/`; unset → upload skipped. Also makes `list_templates`/`fetch_template` read from Drive. |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Service-account JSON path for Drive auth (falls back to `GOOGLE_SERVICE_ACCOUNT`). |
| `DOCBUILDER_REVIEW_EMAIL` | Internal review alias. Set → PHASE F emails it (with `SMTP_*`); unset → email skipped. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | SMTP creds for PHASE F (same as `email/scripts/email_send.py`). |
| `AETHERIS_MODEL` / `AETHERIS_PROVIDER` | Model/provider overrides (default `claude-haiku-4-5-20251001` / `anthropic`). |

### Pipeline phases (m2b)

The orchestrator resolves the template + delivery options at eval time and runs:

- **PHASE 0 — Template selection:** `list_templates.py --tenant {tenant}` → the LLM picks
  `{doc_type, variant}` from the catalogue + context → `fetch_template.py` downloads the
  bundle (Drive → local cache; no Drive → committed local nested bundle).
- **PHASE A — Fetch:** one `fetch_data.py --output` per `data_sources` entry. Paths are
  the template's, with the leading `docbuilder/` stripped (sandbox-relative). A declared
  source not read by any sheet is still fetched (e.g. the demo `summary`).
- **PHASE B — Compute:** `compute_doc.py {bundle}/…json {raw files} --output pipeline_spec.json`.
- **PHASE C — Render:** each `output_formats` entry; xlsx/docx get `--base-file` from the
  bundle, pdf gets `--template-dir {bundle}` + `--context` (narrative mode).
- **PHASE D — Rename:** `rename_output.py` → `{client_name_slug}_{doc_type}_{date}.{ext}`.
- **PHASE E — Upload** (only if `DRIVE_DOCBUILDER_ID` set): `upload_output.py` → `{tenant}/output/`.
- **PHASE F — Email** (only if `DOCBUILDER_REVIEW_EMAIL` set): `email_send_review.py` to the
  review alias with the Drive links.

In dev (no Drive/SMTP creds) PHASE E/F skip with a notice; the sprint verifies PHASE 0–D.

---

## Python dependencies

The renderer scripts need these third-party packages in the mise Python env:

```bash
python3 -m pip install openpyxl python-docx weasyprint markdown
```

- `openpyxl` — `generate_xlsx.py`
- `python-docx` — `generate_docx.py`
- `weasyprint` — `generate_pdf.py`
- `markdown` — `render_template.py` (narrative-mode PDF)

> A pinned `requirements.txt` is added at m2a t10. Until then, tests for a renderer
> whose dependency is missing **skip** (via `pytest.importorskip`) rather than fail —
> so a missing package is silent. Install the list above for a complete run.

---

## How to run

### Via sprint.sh (recommended)

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
./scripts/sprint.sh docbuilder
# add DRIVE_DOCBUILDER_ID / GOOGLE_SERVICE_ACCOUNT_FILE / DOCBUILDER_REVIEW_EMAIL / SMTP_*
# to also exercise PHASE E (upload) and PHASE F (email).
```

Other sprint cases:
- `./scripts/sprint.sh docbuilder_context` — m3 context builder → orchestrator chain
  ("same as last month").
- `./scripts/sprint.sh docbuilder_fresh` — m4 freeform fresh path: `context_builder.exs`
  extracts fields from a freeform `DOCBUILDER_REQUEST`, validates via `validate_fields.py`,
  and writes `confirmed_context.json`. Resets `run_log.json` to `[]` first (forces the fresh
  path); asserts the context is written + parseable and the run log is NOT appended
  (builder-only — PHASE D2 runs with the orchestrator). Full m4 detail: §"m4 — freeform NL
  field extraction" below.
- `./scripts/sprint.sh docbuilder_fresh_render` — m5 full fresh→render chain: builder-only
  `docbuilder_fresh` plus the orchestrator step. Chains `context_builder.exs` (fresh extract)
  → `docbuilder_orchestrator.exs` (reads `confirmed_context.json` via `DOCBUILDER_CONTEXT_FILE`,
  renders + PHASE D2). Resets `run_log.json` to `[]`; asserts every `renamed.json` output
  exists + non-empty, the rendered **PDF has no unresolved `{{placeholder}}` strings** (m5 t1
  `_sub_var` fix — degrades to `[INFO]` if `pdftotext` is absent), and the run log has exactly
  1 entry (PHASE D2 appended: 0 → 1).
- `./scripts/sprint.sh docbuilder_invoice_jinja` — m6 invoice via the **Jinja2** renderer.
  Same recurring ("same as last month") chain as `docbuilder_context`, but the invoice now
  renders through `invoice_v1.html.j2` (`has_jinja: true`). Regression gate for the m6
  migration: asserts the rendered **PDF has zero `{{` artifacts** (`pdftotext`; degrades to
  `[INFO]` if absent).
- `./scripts/sprint.sh docbuilder_offer_letter` — m6 offer letter, **fresh → DOCX**. Freeform
  NL request → `context_builder.exs` (validates `OFFER_LETTER_REQUIRED`) → orchestrator's
  **docx-jinja branch** (`generate_html.py` → `generate_docx_from_html.py`). Asserts
  `confirmed_context.json` has a non-empty `candidate_name` (offer letters use `candidate_name`,
  not `client_name`), `renamed.json` contains a `.docx` output, and the run log goes 0 → 1.

### Direct run

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
mix aetheris run ../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs
```

### Syntax check (no LLM call)

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs")'
```

---

## Expected output

After a successful run, `docbuilder/output/` will contain:

```
output/template_cache_path.txt              # PHASE 0 — bundle path (fetch_template)
output/pipeline_raw_main.json               # PHASE A — raw fetch (one per source)
output/pipeline_raw_summary.json            # PHASE A — second source (demo)
output/pipeline_spec.json                   # PHASE B — computed doc spec
output/acme_corp_proposal_2026-06-20.xlsx   # PHASE C+D — branded, renamed (was proposal_v1.xlsx)
output/acme_corp_proposal_2026-06-20.docx   # PHASE C+D — branded, renamed
output/acme_corp_proposal_2026-06-20.pdf    # PHASE C+D — narrative, renamed
output/renamed.json                         # PHASE D — {original, renamed} pairs
output/uploaded.json                        # PHASE E — {filename, drive_file_id, drive_url} (only if Drive enabled)
```

The renamed filenames come from `DOCBUILDER_CONTEXT` (`{client_name_slug}_{doc_type}_{date}`).
The intermediate `proposal_v1.*` files are renamed away by PHASE D.

The formats generated depend on the `output_formats` array in the template. The
`demo/proposal_v1.json` template specifies `["xlsx", "docx", "pdf"]`. xlsx/docx open
their base files when present; pdf uses narrative mode when the template has a
`narrative` block and `--template-dir` is supplied.

---

## Template location convention

Templates live at:
```
data/templates/{DOCBUILDER_TENANT}/{DOCBUILDER_DOC_TYPE}_{DOCBUILDER_VERSION}.json
```

Example: `DOCBUILDER_TENANT=demo`, `DOCBUILDER_DOC_TYPE=proposal`, `DOCBUILDER_VERSION=v1`
→ `data/templates/demo/proposal_v1.json`

> **Two layers of config — know which is which.** `catalogue.json` is *selection*
> metadata only: `list_templates.py` (PHASE 0) surfaces its `output_formats` /
> `has_base_files` / `has_narrative` / `label` to the LLM so it can pick a template. The
> bundle spec `{prefix}_v1.json` (e.g. `invoice_v1.json`) is the *operative render config*:
> the orchestrator (at eval time) and `compute_doc.py` (at runtime) read `narrative`,
> `output_formats`, `data_sources`, and `sheets` from it. The orchestrator decides narrative
> vs structured by `is_map(template["narrative"])` in the **bundle spec**, not by the
> catalogue's `has_narrative`; and it uses a DOCX/XLSX base file only when that file
> **physically exists** in the bundle, not because `has_base_files` says so. Keep the two in
> sync, but the bundle spec is the source of truth.

---

## Editing an existing template

Template bundles live under the canonical nested layout:
```
data/templates/{tenant}/{doc_type}/{version}/
```

The Bitloka invoice bundle (`data/templates/bitloka/invoice/v1/`) actually contains:
```
invoice_v1.json          ← bundle spec (operative config): narrative pointer,
                           output_formats, data_sources, sheets — the file the
                           orchestrator + compute_doc read
invoice_v1.md.template   ← narrative layout (Markdown + {{placeholders}})
invoice_v1.css           ← PDF styling (WeasyPrint)
sample_invoice_data.csv  ← the `main` data source for the Line Items table
btl_logo-withtext.png    ← branding asset referenced by the template/CSS
```
There are **no** `invoice_v1.docx` / `invoice_v1.xlsx` base files here — the invoice's
`has_base_files` is `{xlsx:false, docx:false}` and all three formats (xlsx/docx/pdf) are
generated from scratch.

### The narrative template (`*.md.template`)

Markdown with two kinds of placeholders:

- `{{variable}}` — substituted from the resolved context at render time. Present fields
  are substituted with their value; absent **optional** fields render as empty string
  (never a raw `{{placeholder}}`); absent **unknown** vars also render empty but warn (m5 t1).
- `{{>Sheet Name}}` — replaced with an HTML table rendered from the bundle spec's named
  sheet (e.g. `{{>Line Items}}`).

To add a new field to the PDF layout:
1. Add `{{your_field}}` at the desired location in the `.md.template`.
2. If the field is **optional**, add `"your_field"` to `OPTIONAL_FIELDS` in
   `scripts/render_template.py` so it renders silently as empty rather than warning.
3. If the field is **required** for this doc type, add it to the appropriate required-fields
   list in `scripts/validate_fields.py`.
4. Document the field in `docbuilder/docs/context-schema.md`.

### The CSS file (`*.css`)

Standard CSS loaded by WeasyPrint — fonts, colours, table borders, header layout, page
margins. Edit directly; no pipeline changes needed.

### Base files (`*.docx`, `*.xlsx`) — only when present

When a `{prefix}.docx` / `{prefix}.xlsx` file is committed alongside the bundle spec, the
DOCX/XLSX renderers start from it (named styles like `Heading 1` / `Table Grid`, fonts,
per-sheet branding). When absent — as for the Bitloka invoice — the renderers generate from
scratch. The catalogue's `has_base_files` flag is selection metadata and should mirror this
reality, but file presence is what the renderers actually key on. To add/replace a base file,
drop it into the bundle directory and set `has_base_files` accordingly.

---

## Adding a new doc type

Adding a new doc type (e.g. `offer_letter`) is **not config-only** — it needs a bundle
(including the spec JSON), a catalogue entry, schema docs, and small code edits to
`validate_fields.py` (+ `render_template.py` for optional fields). Steps:

### Step 1 — Create the bundle directory and files

```
data/templates/bitloka/offer_letter/v1/
  offer_letter_v1.json          ← REQUIRED bundle spec (see below)
  offer_letter_v1.md.template   ← narrative layout
  offer_letter_v1.css           ← PDF styling
```

> **The spec JSON is mandatory.** The orchestrator does
> `File.read!("{bundle}/{prefix}.json")` at eval time — without
> `offer_letter_v1.json` the run crashes before any LLM call. For a PDF-only narrative
> letter with no tables, the minimal spec is:
> ```json
> {
>   "template_id": "bitloka/offer_letter_v1",
>   "title": "Offer Letter",
>   "data_sources": [],
>   "output_formats": ["pdf"],
>   "narrative": { "template_file": "offer_letter_v1.md.template", "css_file": "offer_letter_v1.css" },
>   "sheets": []
> }
> ```
> `data_sources` and `sheets` must be present (empty lists are fine — `compute_doc.py`
> iterates them directly). The `narrative` map is what makes the orchestrator route through
> `render_template.py`. DOCX/XLSX base files are optional and only needed if you add those to
> `output_formats` and want branded bases.

**`offer_letter_v1.md.template` example:**

```markdown
# {{title}}

Dear {{candidate_name}},

We are pleased to offer you the position of **{{role}}** at Bitloka Solutions
Private Limited, reporting to {{reporting_to}}.

**Start date:** {{start_date}}
**Compensation:** {{compensation}}
**Location:** {{location}}

{{terms}}

Please confirm acceptance by replying to this email by {{acceptance_deadline}}.

For Bitloka Solutions Pvt. Ltd

(Authorised Signatory)
```

All `{{fields}}` not always supplied go in `OPTIONAL_FIELDS` (step 4); required fields go in
`validate_fields.py` (step 4).

### Step 2 — Register in `catalogue.json`

Add an entry to the `doc_types` array in `data/templates/bitloka/catalogue.json`:

```json
{
  "doc_type": "offer_letter",
  "description": "Employment offer letter for new hires — PDF with role, compensation, and start date",
  "variants": [
    {
      "version": "v1",
      "label": "Standard",
      "output_formats": ["pdf"],
      "has_base_files": { "xlsx": false, "docx": false },
      "has_narrative": true
    }
  ]
}
```

This drives PHASE 0 selection only (`list_templates.py` → the LLM). `has_narrative` /
`output_formats` / `has_base_files` here should **mirror** the bundle spec from step 1 — they
do not themselves change rendering behaviour.

### Step 3 — Add fields to `context-schema.md`

Add the new doc type's fields to `docbuilder/docs/context-schema.md`, marking required vs
optional:
```
candidate_name      string  required for offer_letter  "Jane Smith"
role                string  required for offer_letter  "Senior Engineer"
start_date          string  required for offer_letter  "01-Aug-2026"
compensation        string  required for offer_letter  "₹25,00,000 per annum"
reporting_to        string  optional                   "Anil Kumar"
location            string  optional                   "Bangalore"
acceptance_deadline string  optional                   "05-Jul-2026"
```

### Step 4 — Update `validate_fields.py` and `render_template.py` (code change)

`scripts/validate_fields.py` — add a required-fields list and a doc-type branch:
```python
OFFER_LETTER_REQUIRED = ["candidate_name", "role", "start_date", "compensation"]

# In validate():
required = BASE_REQUIRED + (
    INVOICE_REQUIRED if doc_type == "invoice" else
    OFFER_LETTER_REQUIRED if doc_type == "offer_letter" else
    []
)
```

`scripts/render_template.py` — add the optional offer-letter fields to `OPTIONAL_FIELDS` so
they render silently when absent:
```python
OPTIONAL_FIELDS = {
    # … existing …
    "reporting_to", "location", "acceptance_deadline",
}
```

### Step 5 — Test it

```bash
cd ~/sandbox/elixirws/aetheris

# Fresh path — builder only (confirm extraction)
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Offer letter for Jane Smith joining as Senior Engineer on 1 Aug 2026 at ₹25L/year, reporting to Anil Kumar, email jane.smith@example.com" \
./scripts/sprint.sh docbuilder_fresh

# Full chain — render the PDF
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="…same request…" \
./scripts/sprint.sh docbuilder_fresh_render
```

Or from the Rig Docbuilder panel — type the same request and Run.

### What is automatic vs manual

Automatic: once the catalogue entry + bundle spec exist, PHASE 0 surfaces `offer_letter/v1`
and the LLM selects it from the request; the orchestrator and context builder need **no**
changes (they are doc-type-agnostic and read the bundle spec). Manual: the bundle spec JSON
(step 1), the `validate_fields.py` doc-type branch, and the `render_template.py`
`OPTIONAL_FIELDS` additions (step 4) — these are the code edits, so a new doc type is a
small ticket, not a pure docs/config change.

---

## Jinja2 templates (m6)

m6 introduced a Jinja2 HTML renderer that supersedes the Markdown+regex `render_template.py`
for new doc types. A bundle opts in with `"has_jinja": true` in its spec JSON.

**Pipeline.**
- **Template:** a `.html.j2` file (Jinja2 HTML), named by `narrative.template_file` in the
  bundle spec.
- **HTML / PDF:** `generate_html.py` renders the `.html.j2` + context → HTML;
  `generate_pdf.py` calls it (the `has_jinja` branch in `_narrative_html`) → WeasyPrint PDF.
- **DOCX:** `generate_docx_from_html.py` converts that HTML → DOCX via **Pandoc**, branded by
  `data/templates/bitloka/reference.docx` (Pandoc reads only the reference doc's named styles
  and ignores its body). The orchestrator emits the two-step chain
  `generate_html.py → generate_docx_from_html.py` for a `docx` + `has_jinja` bundle.

**Deprecation.** `render_template.py` and `.md.template` files are **deprecated** (kept for
backward compatibility; removal is m7). Use `.html.j2` for new doc types and migrations.

**Jinja2 authoring primer.**
- `{{ field | default('') }}` — substitute a field; render empty when absent. (The
  `jinja2.Undefined` environment already renders an absent `{{ field }}` as `""` and treats it
  as falsy in `{% if %}`, but `| default('')` documents intent.)
- `{% if field %}…{% endif %}` — conditional section (e.g. the offer letter's internship /
  performance-bonus blocks).
- `{% for item in list %}…{% endfor %}` — loops.
- **Autoescaping is ON** — all context values are HTML-escaped by default, so `$1,000.00` /
  `₹9,00,000` render correctly and untrusted text cannot inject markup. Use `{{ field | safe }}`
  ONLY when the value is trusted HTML you want rendered as-is. **Canonical `| safe` use:**
  pre-rendered table markup from `render_table`, injected as `{{ tables['Line Items'] | safe }}`.
- **Subscripting a possibly-absent variable** must be guarded:
  `{% if tables and 'Line Items' in tables %}{{ tables['Line Items'] | safe }}{% endif %}`.
  `{{ tables['Line Items'] | default('') }}` does NOT work — subscripting an *undefined*
  variable raises `UndefinedError` before the `default` filter runs.

---

## Running tests

```bash
cd ~/sandbox/elixirws/aetheris-agents

# All docbuilder tests
python3 -m pytest docbuilder/tests/ -v

# Single script
python3 -m pytest docbuilder/tests/test_compute_doc.py -v
```

---

## m4 — freeform NL field extraction

The context builder's **fresh path** (no recurring "same as last month" match) turns a
freeform `DOCBUILDER_REQUEST` into a `confirmed_context.json`:

1. **Extract** — the LLM extracts a raw field map from the request (client, title, date,
   doc_type, invoice fields, and any `unit_price`/`line_item_qty`/`currency` stated) →
   `output/raw_extraction.json`.
2. **Validate** — `validate_fields.py --input output/raw_extraction.json --output
   output/validated_extraction.json` validates + normalises against the context schema
   (date → ISO 8601; `amount_due` validated-as-money but **kept as a display string**;
   `unit_price`/`line_item_qty` → numeric; `currency` → upper + checked against
   `{GBP,USD,EUR,AED,INR}`; required fields per `doc_type`). Exit 0 → normalised context;
   exit 1 → `{"missing":[...],"invalid":{...}}` payload (no partial context).
3. **Self-correct once** — on exit 1 the agent re-reads the original request for the named
   fields and re-validates ONCE. There is **no in-run human reply** (single-shot
   `mix aetheris run`, no `ask_human` tool — same model as the m3 confirmation gate).
4. **Gate or clarify** — exit 0 → write `output/confirmed_context.json`, emit the
   `PROPOSED DOCBUILDER_CONTEXT` block (the operator reviews before rendering). Still
   failing after the second pass → the agent emits one clarifying message naming the
   fields and STOPS without writing the context; the operator re-runs with the field
   included (the "reply" is a re-run).

### Sprint case

```bash
cd ~/sandbox/elixirws/aetheris
DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh
```

Runs only `context_builder.exs` with a freeform `DOCBUILDER_REQUEST`, resets
`data/run_log.json` to `[]` (forces the fresh path), and asserts `confirmed_context.json`
is written + parseable and the run log is NOT appended (builder-only — PHASE D2 appends
only when the orchestrator runs). The client-match assertion is client-agnostic (m5 t2): it
passes for any non-empty `client_name` (and reports the parsed client in the `[OK]` line), so
overriding `DOCBUILDER_REQUEST` for a different client works.

### Output files (m4)

- `output/raw_extraction.json` — the LLM's raw extracted field map (gitignored).
- `output/validated_extraction.json` — `validate_fields.py`'s normalised context (exit 0)
  or `{missing,invalid}` error payload (exit 1). Inspect this when the fresh path stops
  with a clarifying message.

### Failure mode — `validate_fields.py` exit 1

Read `output/validated_extraction.json`: `missing` lists absent required fields, `invalid`
maps a field to why it was rejected (bad date, unknown currency, non-monetary amount, bad
email). Supply the field in `DOCBUILDER_REQUEST` and re-run. The validator never fabricates
or defaults a value (e.g. a fresh invoice missing `invoice_number` is flagged, not invented).

---

## Common failure modes

### `DOCBUILDER_TENANT not set` (or similar) on eval

All four `DOCBUILDER_*` vars must be exported before running `mix aetheris run`
or `mix run --eval`. The orchestrator raises immediately if any are absent.

### Output files missing after run

Check `overlay_base_dir` — it must be `nil`. If output files appeared in a
per-run `upper/` directory under `priv/runs/`, `overlay_base_dir` was set
non-nil. The orchestrator explicitly sets `overlay_base_dir: nil`.

### `python3 python3 script.py` in run_command

The LLM duplicated the executable in both `command` and `args`. The system
prompt explicitly warns: "Do not pass 'python3' inside the args array." If
this happens, re-run — the system prompt guard should prevent it.

### Template not found (exit code 1 from compute_doc.py)

Verify the template path:
```bash
ls docbuilder/data/templates/demo/
```
Expected: `proposal_v1.json`. The path is constructed as
`data/templates/{TENANT}/{DOC_TYPE}_{VERSION}.json`.

### Env vars not inherited by workers

The exec server spawns workers at invocation time and they inherit the
environment at that moment. If you exported env vars after starting a
long-lived worker, kill stale workers and re-run:
```bash
pkill -f aetheris_worker
```

### Stale `output/pipeline_raw_*.json` or `output/pipeline_spec.json`

These intermediates are overwritten on each run (one `pipeline_raw_{key}.json`
per data source, plus `pipeline_spec.json`). If a partial run left stale
intermediates, delete them before re-running:
```bash
rm -f docbuilder/output/pipeline_raw_*.json docbuilder/output/pipeline_spec.json
```
