# Implementation notes — m-docbuilder-m6 t5 (sprint cases + runbook)

Ticket: two live sprint cases — `docbuilder_invoice_jinja` (Jinja2 invoice migration
regression gate) and `docbuilder_offer_letter` (offer-letter fresh→DOCX end-to-end) — plus the
runbook §"Jinja2 templates (m6)" + sprint-case entries + deprecation note. Both live runs are
the real gate for everything t3/t4/t4b built.

---

## What shipped

- **`aetheris/scripts/sprint.sh`** (sibling repo) — two new cases (both under `all`; usage line
  updated):
  - `docbuilder_invoice_jinja` — models `docbuilder_context` (recurring "same as last month",
    May→June seed). The invoice now renders via `invoice_v1.html.j2` (`has_jinja: true`).
    Asserts the rendered **PDF has zero `{{`** (`pdftotext`; degrades to `[INFO]`).
  - `docbuilder_offer_letter` — models `docbuilder_fresh_render`. Freeform offer-letter NL
    request → `context_builder` (validates `OFFER_LETTER_REQUIRED`) → orchestrator docx-jinja
    branch. Asserts `candidate_name` non-empty, a `.docx` in `renamed.json`, run log 0→1.
- **`docbuilder/runbook.md`** — §"Jinja2 templates (m6)" (pipeline: `.html.j2` + `has_jinja`,
  `generate_html.py` for HTML/PDF, `generate_docx_from_html.py` + `reference.docx` for DOCX;
  `render_template.py`/`.md.template` deprecation; Jinja2 authoring primer incl. the t1-F1
  autoescape note, the t3 `| safe` canonical example, and the t3 subscript-guard note). Two
  sprint-case entries added to the "Other sprint cases" list.
- **`docbuilder_orchestrator.exs`** — see the t5 finding below (a fix to the t4b branch).

## t5 finding F1 (fixed) — docx-jinja branch over-matched the invoice docx

The first `docbuilder_invoice_jinja` live run (`docbuilder-orch-LEJsLg`) rendered the invoice
docx through the t4b docx-jinja branch (`fmt==docx and narrative? and has_jinja?`) — which the
invoice satisfies. But standalone `generate_html.py` does **not** inject sheet `tables` (only
`generate_pdf._narrative_html_jinja` does), so the `{% if tables %}` block was skipped and the
**invoice docx lost its Line Items table** (docx had 2 static tables, no line items; "Total/
Amount" absent). The invoice PDF was fine (generate_pdf injects tables).

The invoice docx was never in m6 scope — t3 migrated the invoice **PDF** to Jinja; its docx
should stay on the structured `generate_docx.py` path. **Fix:** narrowed the docx-jinja branch
to `fmt==docx and narrative? and has_jinja? and no_sheets?` (`no_sheets? = template["sheets"]
== []`). A bundle WITH sheets (invoice) → structured docx via `generate_docx.py`; a table-less
narrative bundle (offer letter, `sheets: []`) → jinja docx. This is the scope-correct fix and
restores the pre-m6 invoice docx behaviour.

Eval-verified: invoice context → docx via `generate_docx.py` (not jinja); offer-letter context
→ docx via `generate_html` + `generate_docx_from_html` (not legacy). Re-run
(`docbuilder-orch-vb69ng`) confirms the invoice docx is back to **37K structured with the Line
Items table** (1 table, headers Resource/Month/Amount present) and the PDF still zero `{{`.

## Done-check (live)

- **`docbuilder_invoice_jinja`** (`docbuilder-orch-vb69ng`): context_builder → confirmed_context
  → orchestrator → rendered `xyz_inc_invoice_30-Jun-2026.{xlsx(5.2K),docx(37K),pdf(85K)}`;
  **no `{{` in the PDF (Jinja2 path)**. Invoice docx table confirmed present (manual check).
- **`docbuilder_offer_letter`** (`docbuilder-orch-MXl0Ew`): confirmed_context (candidate: Ajay
  Rao) → orchestrator docx-jinja chain → `ajay_rao_offer_letter_2026-07-01.docx` (23K);
  `renamed.json` contains the `.docx`; run log 0→1. **F2 confirmed**: the `.docx` exists, which
  required the LLM to run both ordered sub-steps (C{i}a `generate_html` → html, then C{i}b
  `generate_docx_from_html` → docx). Docx content verified: candidate, role, comp tables
  (Basic/HRA/Total Earnings), signatory all present.
- `bash -n scripts/sprint.sh`: clean.

## t5 observation F2 (not fixed — m7 item) — optional field naming

In the offer-letter run, the context builder extracted the bonus info under **non-schema field
names** (`business_performance_bonus` / `business_performance_bonus_months`) rather than the
template/schema names (`business_performance_bonus_pct` / `business_performance_bonus_period`).
The template's `{% if business_performance_bonus_pct %}` sections were therefore skipped — a
graceful, non-failing outcome (the bonuses are optional and the sprint does not assert them; all
**required** fields extracted with correct names and rendered). Root cause: the context builder
is doc-type-agnostic and does not pin the offer-letter optional field names. **m7 item:** make
the context builder offer-letter-schema-aware for optional names, or add template aliases. No
t5 change (it's a context_builder prompt concern, out of the sprint+runbook scope).

## Notes

- `sprint.sh` is committed in the sibling `aetheris` repo (separate from this repo's commit).
- The orchestrator narrowing is a fix to the t4b branch surfaced by the t5 live run — committed
  with t5; the t4b implementation notes describe the original (broader) branch.
