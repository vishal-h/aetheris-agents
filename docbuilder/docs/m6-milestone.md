# Milestone — m6-docbuilder — Jinja2 renderer + offer letter

**Repo:** aetheris-agents
**Branch:** m6-docbuilder
**Depends on:** aetheris-agents `6dce721` (m5 closed, drift clean 8 PASS / 0 FAIL / 0 WARN)

> **Doc path:** `docbuilder/docs/m6-milestone.md` (aligned to the m1–m5 convention — all
> milestone scope docs live at `docbuilder/docs/m{N}-milestone.md`; `milestones/` holds
> per-ticket implementation notes, `reviews/` holds reviews).

---

## Goal

Replace the Markdown+regex renderer (`render_template.py`) with a Jinja2 HTML renderer,
migrate the invoice to use it, and add an offer letter doc type on top of it. The Jinja2
path gives conditional sections (`{% if %}`), loops (`{% for %}`), proper escaping, and
native absent-variable handling (`{{ field | default('') }}`). DOCX output uses Pandoc
(HTML → DOCX via a branding reference doc). PDF output uses WeasyPrint (unchanged path,
just a new template format).

---

## What is NOT in scope

- Removing `render_template.py` in this milestone — deprecated but kept for backward
  compatibility; removal is m7
- Changes to `generate_xlsx.py`, `generate_csv.py`, or other non-narrative renderers
- Multi-variant support beyond v1 for the offer letter
- Salary computation (`compute_offer.py`) — operator provides all amounts
- Drive upload wiring (PHASE E) — already works; no new milestone work needed
- Changes to `context_builder.exs`, `resolve_last_run.py`, or `run_log_writer.py`

---

## Pre-flight verification (scope-time, 2026-06-26)

Verified against the live environment before scoping — three facts that adjust the tickets:

- **Pandoc:** present (`pandoc 2.9.2.1`). t2 DOCX path is viable as written. ✓
- **Jinja2: NOT installed** and **not in `docbuilder/requirements.txt`** (the doc's
  "already installed, 3.1.6" is false here — `weasyprint 69.0` + `markdown 3.10.2` are
  the only narrative deps listed). **t1 must add `jinja2` to `docbuilder/requirements.txt`
  and install it**, or its `import jinja2` (and the `test_generate_html.py` done-check)
  fails at collection. `docbuilder/requirements.txt` is added to t1's Touches for this.
- **`invoice_v1.json` shape:** `template_file` is **nested under `narrative`**
  (`narrative.template_file` = `"invoice_v1.md.template"`, `narrative.css_file` =
  `"invoice_v1.css"`), NOT a top-level key. So t3's "update `template_file`" means
  `narrative.template_file → "invoice_v1.html.j2"`, and `has_jinja` is a new top-level key.
  Top-level keys: `template_id, title, data_sources, output_formats, table_style,
  data_col_start, narrative, sheets`.

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Template engine | Jinja2 (already installed, 3.1.6) | Native conditionals, loops, filters, proper escaping; `{{ field \| default('') }}` replaces the `OPTIONAL_FIELDS` workaround from m5 |
| HTML renderer script | New `generate_html.py` — Jinja2 template + context → HTML | Replaces `render_template.py` for new doc types; clean, testable |
| DOCX output | New `generate_docx_from_html.py` — Pandoc wrapper (HTML → DOCX via `--reference-doc`) | Pandoc 2.9 available; reference doc carries Bitloka branding/styles, no content; version-controlled plain text templates |
| PDF output | Existing WeasyPrint path — `generate_pdf.py` calls `generate_html.py` instead of `render_template.py` when `has_jinja: true` in the bundle spec | Minimal change to `generate_pdf.py`; WeasyPrint stays |
| Invoice migration | Replace `invoice_v1.md.template` with `invoice_v1.html.j2`; update bundle spec | One template, one renderer for both PDF and future DOCX; `render_template.py` left in place as deprecated |
| Regression gate | `docbuilder_invoice_jinja` sprint case renders the invoice via the new path and asserts zero `{{` artifacts in the PDF | Proves the migration is correct |
| Offer letter output | DOCX only (PDF deferred to m7) | Letters reviewed/signed in Word; Drive handles distribution |
| Offer letter fields | Offer-letter-specific aliases (`candidate_name` etc.); `OFFER_LETTER_REQUIRED` branch in `validate_fields.py` | Clearer semantics; same pattern as `INVOICE_REQUIRED` |
| Conditional sections | Jinja2 `{% if internship_acknowledgement %}…{% endif %}` | Natural in Jinja2; eliminates the optional-field workaround from the original m6 plan |
| `render_template.py` deprecation | Add deprecation comment; keep all existing tests passing | No breakage for any existing sprint case |

---

## Bundle spec convention (new field: `has_jinja`)

The bundle spec JSON gains one optional boolean field:

```json
{ "has_jinja": true }
```

When `true`, `generate_pdf.py` calls `generate_html.py` (Jinja2) instead of
`render_template.py` (Markdown). When absent or `false`, the existing path is used.
This is the only orchestrator-visible change — no PHASE numbering changes.

---

## Offer letter field list

### Required for `offer_letter`

| Field | Example |
|---|---|
| `title` | `"Offer Letter — Ajay Rao"` |
| `candidate_name` | `"Ajay Rao"` |
| `candidate_email` | `"ajay.rao@example.com"` |
| `candidate_phone` | `"980 000 1234"` |
| `candidate_address` | `"123, Main Street, Bengaluru, Karnataka - 560012"` |
| `role` | `"Software Engineer"` |
| `date` | `"01-Jul-2026"` |
| `annual_ctc` | `"₹9,00,000"` |
| `basic_monthly` | `"37,500.00"` |
| `hra_monthly` | `"18,750.00"` |
| `lta_monthly` | `"3,000.00"` |
| `wfh_allowance_monthly` | `"3,000.00"` |
| `flexi_pay_monthly` | `"12,750.00"` |
| `total_earnings_monthly` | `"75,000.00"` |
| `professional_tax_monthly` | `"200.00"` |
| `tds_monthly` | `"7,500.00"` |
| `total_deductions_monthly` | `"7,700.00"` |
| `net_take_home_monthly` | `"₹67,300.00"` |

### Optional for `offer_letter`

| Field | Notes |
|---|---|
| `internship_acknowledgement` | Full paragraph text; omit for direct hires |
| `business_performance_bonus_pct` | e.g. `"12.5%"` |
| `business_performance_bonus_period` | e.g. `"March/April"` |
| `individual_performance_bonus_pct` | e.g. `"12.5%"` |
| `individual_performance_bonus_period` | e.g. `"September/October"` |

---

## Ticket structure

| Ticket | Title | Key artifacts |
|---|---|---|
| t1 | `generate_html.py` — Jinja2 renderer | `scripts/generate_html.py`, tests |
| t2 | `generate_docx_from_html.py` — Pandoc wrapper | `scripts/generate_docx_from_html.py`, tests, `reference.docx` |
| t3 | Migrate invoice to Jinja2 + update `generate_pdf.py` | `invoice_v1.html.j2`, `generate_pdf.py` |
| t4 | Offer letter bundle + `validate_fields.py` (core) | `data/templates/bitloka/offer_letter/v1/`, `validate_fields.py` |
| t4b | DOCX pipeline wiring (compute_doc zero-source, rename_output candidate fallback, orchestrator docx-jinja branch) | `compute_doc.py`, `rename_output.py`, `docbuilder_orchestrator.exs` |
| t5 | Sprint cases + runbook | `sprint.sh`, `docbuilder/runbook.md` |
| t6 | Docs sync + milestone close | `docs/capability-matrix.md`, `docs/rig/runbook.md`, `CLAUDE.md` |

---

## Tickets

### t1 — `generate_html.py` (Jinja2 renderer)

**Scope.** A new script that renders a Jinja2 `.html.j2` template with a context dict
→ HTML string or file. Replaces `render_template.py` for new doc types.

**Contract refs.**
- `agent-creation-guide.md` §"Scripts do, agents decide"
- `render_template.py` — the script being superseded; match its CLI interface

**Touches.**
- `docbuilder/scripts/generate_html.py` — new
- `docbuilder/tests/test_generate_html.py` — new
- `docbuilder/requirements.txt` — add `jinja2` (NOT installed yet — see §Pre-flight)
- `docbuilder/docs/milestones/m-docbuilder-m6-t1-implementation-notes.md` — new

**Do not generate.**
- Do not modify `render_template.py`, `generate_pdf.py`, or any bundle asset

**Script contract:**
- CLI: `generate_html.py --template TEMPLATE [--context JSON] [--spec SPEC_JSON_FILE] [--output FILE]`
- Absent variables render as `""` (use `jinja2.Undefined` environment)
- Exit 1 on `TemplateNotFound`, `TemplateSyntaxError`, or JSON parse error
- Importable: `render_html(template_path, context, spec=None) -> str`

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

python3 -m pytest tests/test_generate_html.py -v
python3 -m pytest tests/ -q

echo '<p>Hello {{ name | default("") }}</p>' > /tmp/test.html.j2
python3 scripts/generate_html.py --template /tmp/test.html.j2 --context '{"name":"World"}'
# Expected: <p>Hello World</p>

python3 scripts/generate_html.py --template /tmp/test.html.j2 --context '{}'
# Expected: <p>Hello </p>  (absent var → empty, no error)
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing any code. Then implement t1
> of `docbuilder/docs/m6-milestone.md`.
>
> First add `jinja2` to `docbuilder/requirements.txt` and install it
> (`python3 -m pip install jinja2`) — it is NOT currently installed (see §Pre-flight
> verification); without it the new script and its tests cannot import.
>
> Create `generate_html.py` — a Jinja2 template renderer:
> - `render_html(template_path, context, spec=None) -> str` — importable. Uses
>   `jinja2.Environment(loader=jinja2.FileSystemLoader(...), undefined=jinja2.Undefined)`
>   so absent variables render as `""` rather than raising.
> - CLI: `--template`, `--context` (inline JSON, default `{}`), `--spec` (JSON file
>   path, optional; makes `spec` dict available in templates), `--output` (file; default
>   stdout). Exit 1 on `TemplateNotFound`, `TemplateSyntaxError`, bad JSON — emit
>   `{"status":"error","error":"..."}` to stderr (stage-CLI pattern).
>
> Tests:
> - Present variable renders its value
> - Absent variable renders as `""` (no exception)
> - `{% if field %}` block: present → rendered; absent → skipped
> - `{% for item in items %}` loop
> - `--spec` makes `spec` available in the template
> - CLI: `--output FILE` writes to file; stdout mode; missing template → exit 1;
>   bad context JSON → exit 1
>
> **Touches:** `docbuilder/scripts/generate_html.py`,
> `docbuilder/tests/test_generate_html.py`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t1-implementation-notes.md`.
> Do not generate anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t1` and include its full output at
> the top of the review packet.

---

### t2 — `generate_docx_from_html.py` (Pandoc wrapper)

**Scope.** A new script that converts HTML to DOCX via Pandoc, using a reference `.docx`
for Bitloka branding. Create the reference doc with `python-docx` (styles only, no
content).

**Touches.**
- `docbuilder/scripts/generate_docx_from_html.py` — new
- `docbuilder/data/templates/bitloka/reference.docx` — new (styles-only reference doc)
- `docbuilder/tests/test_generate_docx_from_html.py` — new
- `docbuilder/docs/milestones/m-docbuilder-m6-t2-implementation-notes.md` — new

**Do not generate.**
- Do not modify any bundle asset or catalogue

**Script contract:**
- CLI: `generate_docx_from_html.py --input HTML_FILE --output DOCX_FILE [--reference-doc DOCX]`
- Default `--reference-doc`: `data/templates/bitloka/reference.docx`
- Calls `pandoc --from html --to docx --reference-doc REF -o OUTPUT INPUT`
- Exit 1 if pandoc not found or returns non-zero
- Importable: `html_to_docx(html_path, output_path, reference_doc=None) -> None`

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

python3 -m pytest tests/test_generate_docx_from_html.py -v
python3 -m pytest tests/ -q

echo '<h1>Test</h1><p>Hello World</p>' > /tmp/test.html
python3 scripts/generate_docx_from_html.py \
  --input /tmp/test.html --output /tmp/test.docx
ls -lh /tmp/test.docx
# Expected: file exists, non-zero size
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing any code. Then implement t2
> of `docbuilder/docs/m6-milestone.md`.
>
> **`generate_docx_from_html.py`:**
> - `html_to_docx(html_path, output_path, reference_doc=None) -> None` — resolves
>   default reference doc path. Calls:
>   `["pandoc","--from","html","--to","docx","--reference-doc",ref,"-o",out,inp]`
>   Raises `FileNotFoundError` if pandoc not on PATH; `RuntimeError` (with stderr)
>   if pandoc exits non-zero.
> - CLI wrapping it: `--input`, `--output`, `--reference-doc`. Exit 1 on error.
>
> **`reference.docx`:** Create with `python-docx` — styles only, no content pages.
> Normal style: Calibri 11pt. Heading 1: bold 16pt dark grey `#333333`. Table style
> with thin borders. Include Bitloka orange `#F5A623` as a theme accent. Commit
> the generated `.docx` as a binary.
>
> Tests: `html_to_docx` produces non-empty `.docx`; pandoc not found →
> `FileNotFoundError`; pandoc non-zero → `RuntimeError`; CLI `--output` exists after
> run; bad `--input` → exit 1.
>
> **Touches:** `docbuilder/scripts/generate_docx_from_html.py`,
> `docbuilder/data/templates/bitloka/reference.docx`,
> `docbuilder/tests/test_generate_docx_from_html.py`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t2-implementation-notes.md`.
> Do not generate anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t2` and include its full output at
> the top of the review packet.

---

### t3 — Migrate invoice to Jinja2 + update `generate_pdf.py`

**Scope.** Replace `invoice_v1.md.template` with `invoice_v1.html.j2`. Update
`generate_pdf.py` to call `generate_html.py` when `has_jinja: true`. Update
`invoice_v1.json` to add `"has_jinja": true`. Do not delete `invoice_v1.md.template`.

**Touches.**
- `docbuilder/data/templates/bitloka/invoice/v1/invoice_v1.html.j2` — new
- `docbuilder/data/templates/bitloka/invoice/v1/invoice_v1.json` — add `"has_jinja": true`
- `docbuilder/scripts/generate_pdf.py` — add `has_jinja` branch in `_narrative_html`
- `docbuilder/scripts/compute_doc.py` — **pass `has_jinja` through** to the computed doc
  spec (scope addition, see note below)
- `docbuilder/tests/test_generate_pdf.py` — add/update tests for `has_jinja` path
- `docbuilder/tests/test_compute_doc.py` — `has_jinja` passthrough tests (scope addition)
- `docbuilder/docs/milestones/m-docbuilder-m6-t3-implementation-notes.md` — new

> **Scope addition (t3 implementation):** `compute_doc.py` builds a fresh output doc-spec
> dict and only copies selected keys — it dropped `has_jinja`, so `generate_pdf`'s
> `has_jinja` branch never fired in the real pipeline (`compute_doc → generate_pdf`) and the
> invoice fell back to the legacy Markdown renderer on the `.html.j2` (leaking literal
> `{{ … }}`). Passing `has_jinja` through `compute_doc` is required for the migration to hold
> end-to-end and for the t5 `docbuilder_invoice_jinja` `grep '{{'` gate to pass. Added with a
> default of `False` so every pre-m6 bundle is unchanged.

**Do not generate.**
- Do not delete `invoice_v1.md.template` or modify `render_template.py`
- Do not add a sprint case — that is t5

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

python3 -m pytest tests/test_generate_pdf.py -v
python3 -m pytest tests/ -q

# Zero unresolved Jinja2 vars in rendered HTML
python3 scripts/generate_html.py \
  --template data/templates/bitloka/invoice/v1/invoice_v1.html.j2 \
  --context '{"title":"Invoice 2627/XYZ/03","client_name":"XYZ Inc","client_email":"accounts@xyz.example","date":"30-Jun-2026","invoice_number":"2627/XYZ/03","client_address":"1234 Stevens Creek Blvd","amount_due":"$1,000.00"}' \
  | grep -c '{{'
# Expected: 0
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) and inspect `invoice_v1.md.template`,
> `invoice_v1.json`, `invoice_v1.css`, and `generate_pdf.py` carefully before writing
> any code. Then implement t3 of `docbuilder/docs/m6-milestone.md`.
>
> **`invoice_v1.html.j2`:** A Jinja2 HTML template reproducing the same invoice
> layout as `invoice_v1.md.template`. Use `{{ field | default('') }}` for all context
> variables. Link or inline `invoice_v1.css` (WeasyPrint resolves relative paths from
> `base_url` — a `<link>` tag with the relative CSS path works when `base_url` is set
> to the bundle directory in `generate_pdf.py`).
>
> **`invoice_v1.json`:** Add `"has_jinja": true`. Read the file first; do not change
> any other field. Update `"template_file"` to `"invoice_v1.html.j2"` if the bundle
> spec uses that field to name the narrative template.
>
> **`generate_pdf.py`:** In `_narrative_html`, add a `has_jinja` branch:
> when `doc_spec.get("has_jinja")` is true, call `generate_html.py` (importable
> `render_html`) instead of `render_template.py`. Both paths must set `base_url`
> correctly for WeasyPrint asset resolution.
>
> **Touches:** `data/templates/bitloka/invoice/v1/invoice_v1.html.j2`,
> `data/templates/bitloka/invoice/v1/invoice_v1.json`,
> `docbuilder/scripts/generate_pdf.py`,
> `docbuilder/tests/test_generate_pdf.py`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t3-implementation-notes.md`.
> Do not generate anything outside Touches. Do not delete `invoice_v1.md.template`.
>
> Run the done-check from `m6-milestone.md §t3` and include its full output at
> the top of the review packet.

---

### t4 — Offer letter bundle + `validate_fields.py` (core)

> **t4/t4b split (decided during implementation).** Examining the real integration surface
> showed the offer-letter end-to-end also needs three production-pipeline changes — (a)
> `compute_doc.py` accepting zero data sources (`nargs +→*`), (b) `rename_output.py` falling
> back to `candidate_name` (it currently raises on missing `client_name`), and (c) the
> orchestrator render-branch + `client_slug` fallback for context-only docx-jinja. None are
> exercised by t4's done-check (only by the t5 sprint), and each touches tested pipeline code
> with its own failure modes. **They were split into a separate ticket `t4b`** (drafted after
> the t4 review) so the clean bundle/validation work merges independently and each wiring
> change is adjudicated on its own — same spirit as the t3 `compute_doc` passthrough. This t4
> is the **core**: bundle assets + validation only.

**Scope.** Create the offer letter bundle: `offer_letter_v1.html.j2` with Jinja2
conditional sections, bundle spec, catalogue entry. Add `OFFER_LETTER_REQUIRED` to
`validate_fields.py`. **DOCX pipeline wiring is t4b, not here.**

**Touches.**
- `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.html.j2` — new
- `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.json` — new
- `docbuilder/data/templates/bitloka/catalogue.json` — add `offer_letter` entry
- `docbuilder/scripts/validate_fields.py` — `OFFER_LETTER_REQUIRED` + `candidate_email` check
- `docbuilder/tests/test_validate_fields.py` — offer_letter tests
- `docbuilder/docs/context-schema.md` — add offer-letter fields
- `docbuilder/docs/milestones/m-docbuilder-m6-t4-implementation-notes.md` — new

**Do not generate.**
- Do not add a sprint case — that is t5
- Do not wire the DOCX pipeline (compute_doc / rename_output / orchestrator) — that is t4b

**Key `offer_letter_v1.html.j2` patterns:**
```jinja2
{% if internship_acknowledgement %}
<p>{{ internship_acknowledgement }}</p>
{% endif %}

{% if business_performance_bonus_pct %}
<p>Business Performance Bonus: Up to {{ business_performance_bonus_pct }}
of total annual earnings, provisioned in
{{ business_performance_bonus_period | default('March/April') }}.</p>
{% endif %}
```

**`validate_fields.py` note:** `OFFER_LETTER_REQUIRED` is the complete list —
do NOT add `BASE_REQUIRED` on top (offer letters use `candidate_name`, not `client_name`).

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

python3 -m pytest tests/test_validate_fields.py -v
python3 -m pytest tests/ -q

python3 -c "
import json
cat = json.load(open('data/templates/bitloka/catalogue.json'))
types = [d['doc_type'] for d in cat['doc_types']]
assert 'offer_letter' in types; print('catalogue OK:', types)
"

python3 scripts/generate_html.py \
  --template data/templates/bitloka/offer_letter/v1/offer_letter_v1.html.j2 \
  --context '{"candidate_name":"Ajay Rao","role":"Software Engineer","date":"2026-07-01","annual_ctc":"₹9,00,000","basic_monthly":"37,500.00","hra_monthly":"18,750.00","lta_monthly":"3,000.00","wfh_allowance_monthly":"3,000.00","flexi_pay_monthly":"12,750.00","total_earnings_monthly":"75,000.00","professional_tax_monthly":"200.00","tds_monthly":"7,500.00","total_deductions_monthly":"7,700.00","net_take_home_monthly":"₹67,300.00"}' \
  | grep -c '{{'
# Expected: 0
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) and inspect `invoice_v1.json`,
> `invoice_v1.html.j2` (from t3), `generate_pdf.py`, and `generate_docx_from_html.py`
> (from t2) before writing any code. Then implement t4 of
> `docbuilder/docs/m6-milestone.md`.
>
> **`offer_letter_v1.html.j2`:** Jinja2 HTML template for the Bitloka FTE offer
> letter. All field references use `{{ field | default('') }}`. Use Jinja2 `{% if %}`
> for conditional sections (internship acknowledgement, performance bonuses). Match
> the structure of the actual BTL offer letter (header, body, compensation tables,
> signature, footer). Keep CSS clean — a simple letter stylesheet, not the invoice
> table-heavy style.
>
> **`offer_letter_v1.json`:** Read `invoice_v1.json` for the exact shape; adapt for
> offer_letter: `output_formats: ["docx"]`, `has_jinja: true`, no data sources,
> `template_file: "offer_letter_v1.html.j2"`.
>
> **`catalogue.json`:** Append the `offer_letter` entry:
> `doc_type: "offer_letter"`, `description: "Employment offer letter for new hires —
> Word document with compensation structure"`, `variants: [{version: "v1",
> label: "Standard FTE", output_formats: ["docx"], has_base_files: {xlsx: false,
> docx: false}, has_narrative: false}]`.
>
> **`validate_fields.py`:** Add `OFFER_LETTER_REQUIRED` (the complete list from
> §"Offer letter field list" — all 18 required fields). Update `validate()`. Extend
> the email format check to cover `candidate_email`. `OFFER_LETTER_REQUIRED` replaces
> `BASE_REQUIRED` entirely for offer_letter — do not combine them.
>
> **DOCX wiring is t4b — do NOT do it here.** The compute_doc/rename_output/orchestrator
> changes that wire the context-only docx-jinja delivery path live in ticket t4b (drafted
> after the t4 review). t4 stops at the bundle + validation.
>
> **Touches:** `data/templates/bitloka/offer_letter/v1/offer_letter_v1.html.j2`,
> `data/templates/bitloka/offer_letter/v1/offer_letter_v1.json`,
> `data/templates/bitloka/catalogue.json`,
> `docbuilder/scripts/validate_fields.py`,
> `docbuilder/tests/test_validate_fields.py`,
> `docbuilder/docs/context-schema.md`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t4-implementation-notes.md`.
> Do not generate anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t4` and include its full output at
> the top of the review packet.

---

### t5 — Sprint cases + runbook

**Scope.** Two new sprint cases: `docbuilder_invoice_jinja` (regression gate) and
`docbuilder_offer_letter` (offer letter proof). Runbook updates including the new
§"Jinja2 templates" section.

**Touches.**
- `aetheris/scripts/sprint.sh` — two new cases; usage line updated
- `docbuilder/runbook.md` — §"Jinja2 templates (m6)"; sprint entries; deprecation note
- `docbuilder/docs/milestones/m-docbuilder-m6-t5-implementation-notes.md` — new

**Do not generate.**
- Do not update `docs/rig/runbook.md` — that is t6

**Runbook sections to add to `docbuilder/runbook.md`:**

**§"Jinja2 templates (m6)"** — explain: `.html.j2` templates, `has_jinja: true` in
bundle spec, `generate_html.py` for HTML/PDF, `generate_docx_from_html.py` +
`reference.docx` for DOCX. Deprecation note: `render_template.py` and `.md.template`
files are deprecated; use `.html.j2` for new doc types. Short Jinja2 primer:
`{{ field | default('') }}`, `{% if field %}...{% endif %}`,
`{% for item in list %}...{% endfor %}`. **Autoescaping note (t1 F1):** autoescaping
is ON — all context values are HTML-escaped by default (so `$1,000.00` / `₹9,00,000`
render correctly and untrusted text can't inject markup). Use `{{ field | safe }}`
ONLY when the value is trusted HTML you want rendered as-is. **Canonical `| safe` example
(t3):** pre-rendered table markup from `render_table` injected as `{{ tables['Line Items']
| safe }}` — trusted Python-produced HTML. **Subscript-guard note (t3):** a
potentially-absent variable that you subscript must be guarded with
`{% if tables and 'Name' in tables %}…{% endif %}` — `{{ tables['Name'] | default('') }}`
does NOT work, because subscripting an *undefined* variable raises `UndefinedError` before
the `default` filter runs.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

# Invoice Jinja2 regression
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Invoice for XYZ for June 2026, same as last month" \
./scripts/sprint.sh docbuilder_invoice_jinja
# Expected: rendered PDF; zero {{ in PDF; run log appended

# Offer letter end-to-end
DOCBUILDER_TENANT=bitloka \
./scripts/sprint.sh docbuilder_offer_letter
# Expected: confirmed_context.json (candidate: Ajay Rao);
#           ajay_rao_offer_letter_{date}.docx rendered; run log appended
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) and `docbuilder/runbook.md` before writing.
> Then implement t5 of `docbuilder/docs/m6-milestone.md`.
>
> **`docbuilder_invoice_jinja`:** Follows `docbuilder_context` (recurring, "same as
> last month"). Additionally: after the rendered PDF is verified to exist, assert zero
> `{{` artifacts with `pdftotext` (degrades to `[INFO]` if unavailable) — this is the
> Jinja2 migration regression gate.
>
> **`docbuilder_offer_letter`:** Follows `docbuilder_fresh_render`. Key differences:
> - Default `DOCBUILDER_REQUEST` contains all required offer-letter fields for Ajay Rao
>   (all 18 required fields from the milestone doc §"Offer letter field list")
> - Assert `candidate_name` non-empty (not `client_name`)
> - Assert `renamed.json` output is a `.docx` file
> - No `pdftotext` check (DOCX output)
> - Run log goes 0 → 1
>
> Both cases under `all`. Update usage line.
>
> **`docbuilder/runbook.md`:** Add §"Jinja2 templates (m6)" and sprint-case entries
> per the milestone doc §t5.
>
> **Touches:** `aetheris/scripts/sprint.sh`, `docbuilder/runbook.md`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t5-implementation-notes.md`.
> Do not generate anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t5` and include its full output at
> the top of the review packet.

---

### t6 — Docs sync + milestone close

**Scope.** Capability matrix (two new scripts), `docs/rig/runbook.md` pointer (clears
pre-m6 deferred item), milestone summary, CLAUDE.md learning scan, drift check.

**Touches.**
- `docs/capability-matrix.md` — add `generate_html.py`, `generate_docx_from_html.py`;
  update `render_template.py` (deprecated) and `generate_pdf.py` (Jinja2 path);
  update counts: docbuilder 2 agents / 24 scripts; total 25 / 62
- `docs/rig/runbook.md` — add Jinja2 + new doc type pointer to `docbuilder/runbook.md`
  (clears the pre-m6 deferred BL-002 item from state memory)
- `docbuilder/docs/m6-milestone.md` — milestone summary appended
- `aetheris-agents/CLAUDE.md` — `## Learning — m6-docbuilder`
- `docbuilder/docs/milestones/m-docbuilder-m6-t6-implementation-notes.md` — new

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents

python3 scripts/drift_check.py
# Expected: 0 FAIL (project_knowledge WARNs = BL-002, human-owned)

grep -n "generate_html\|generate_docx_from_html" docs/capability-matrix.md
grep -n "Jinja2\|docbuilder/runbook" docs/rig/runbook.md
grep -c "^## Milestone summary" docbuilder/docs/m6-milestone.md
```

**Claude-code prompt.**
> Read `CLAUDE.md` and `milestone-methodology.md` §7 before writing. Then implement
> t6 of `docbuilder/docs/m6-milestone.md`. Docs-only.
>
> 1. `docs/capability-matrix.md`:
>    - Add `generate_html.py`: "Render a Jinja2 `.html.j2` template with a context
>      dict to HTML; replaces `render_template.py` for new doc types (m6)."
>    - Add `generate_docx_from_html.py`: "Convert an HTML file to DOCX via Pandoc
>      using a Bitloka reference doc for branding and styles (m6)."
>    - Update `render_template.py` row: append "(deprecated in m6 — use
>      `generate_html.py` for new doc types; kept for backward compatibility)."
>    - Update `generate_pdf.py` row: append "Jinja2 path added in m6 (`has_jinja: true`)."
>    - Update docbuilder counts: 2 agents / 24 scripts; total 25 / 62.
>
> 2. `docs/rig/runbook.md` — in the Docbuilder section, add after the m4 fresh-path
>    entry: "For Jinja2 template authoring and adding new doc types (e.g. offer
>    letter), see `docbuilder/runbook.md` §\"Jinja2 templates (m6)\"."
>
> 3. Scan `m-docbuilder-m6-t{1,2,3,4,4b,5}-review.md` for recurring findings (include
>    **t4b**). Write `## Learning — m6-docbuilder` in `CLAUDE.md`.
>
> 4. Append milestone summary to `m6-milestone.md`.
>
> 5. **(t4b F1)** If any t4b smoke command is referenced in this doc, ensure it uses the
>    positional form `compute_doc.py <template>` (NOT `--template <template>` — the template
>    is a positional arg). The t4b ticket lived outside this doc, so there may be nothing to
>    fix here; confirm and note it.
>
> 6. Run drift_check and include full output in the review packet.
>
> **Touches:** `docs/capability-matrix.md`, `docs/rig/runbook.md`,
> `docbuilder/docs/m6-milestone.md`, `aetheris-agents/CLAUDE.md`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t6-implementation-notes.md`.
> Do not generate anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t6` and include its full output at
> the top of the review packet.

---

## Runbook update summary

| Ticket | File | What changes |
|---|---|---|
| t5 | `docbuilder/runbook.md` | §"Jinja2 templates (m6)"; `docbuilder_invoice_jinja` + `docbuilder_offer_letter` sprint entries; `render_template.py` deprecation note |
| t6 | `docs/rig/runbook.md` | Pointer to `docbuilder/runbook.md` §"Jinja2 templates"; clears pre-m6 deferred BL-002 item; advances manifest past `cac8b67` |

---

## Open questions for m7

- Remove `render_template.py` and `.md.template` files once the Jinja2 invoice path
  is production-proven (after at least one full billing cycle).
- Add PDF output to the offer letter (WeasyPrint + Jinja2 path already proven on the invoice).
- `compute_offer.py` — derive the monthly breakdown from a single `annual_ctc` input.
- `is_intern` boolean → automatic internship acknowledgement paragraph.

---

## Milestone summary

_To be written by claude-code at t6, from the implementation notes._
