# Implementation notes — m-docbuilder-m6 t4 (offer letter bundle + validate_fields) — CORE

Ticket: create the offer-letter bundle (Jinja2 template + spec + catalogue entry) and the
`OFFER_LETTER_REQUIRED` validation branch. **Scope split:** the DOCX pipeline wiring
(compute_doc zero-source, rename_output candidate fallback, orchestrator docx-jinja branch)
was moved to a separate ticket **t4b** (see below); this t4 is bundle + validation only.

---

## t4/t4b split (decided with the user before implementation)

Mapping the real integration surface showed the offer-letter end-to-end needs three
production-pipeline changes none of which t4's done-check exercises (only the t5 sprint does):
- `compute_doc.py` — `nargs '+' → '*'` so a zero-data-source bundle produces a spec;
- `rename_output.py` — fall back to `candidate_name` (it raises on missing `client_name`);
- `docbuilder_orchestrator.exs` — a docx + narrative + `has_jinja` render branch
  (`generate_html.py` → `generate_docx_from_html.py`) + `client_slug` candidate fallback.

Each touches tested pipeline code with its own failure modes (the orchestrator prompt change
is the highest-risk). Per the user's call (Option 2), these were split into **t4b** so the
clean bundle/validation work merges independently and each wiring change is adjudicated on its
own — same spirit as the t3 `compute_doc` `has_jinja` passthrough. The milestone doc's t4
scope/Touches/prompt + ticket table were updated to record the split.

## What shipped (t4 core)

- **`offer_letter_v1.html.j2`** (new) — Jinja2 HTML offer letter. All fields
  `{{ field | default('') }}`. `{% if %}` conditional sections for
  `internship_acknowledgement` and the two performance bonuses (with
  `default('March/April')` / `default('September/October')` periods). docx-only → **no CSS
  link** (Pandoc styles from `reference.docx`; CSS deferred to the m7 PDF work). Semantic
  `<h1>`/`<h2>`/`<table>` so Pandoc maps them to the reference-doc styles.
- **`offer_letter_v1.json`** (new) — `template_id`, `title`, `data_sources: []`,
  `output_formats: ["docx"]`, `has_jinja: true`, `narrative: {template_file:
  offer_letter_v1.html.j2, css_file: null}`, `sheets: []`.
- **`catalogue.json`** — appended the `offer_letter` entry (`label: "Standard FTE"`,
  `output_formats: ["docx"]`, `has_narrative: false`). Invoice entry untouched.
- **`validate_fields.py`** — `OFFER_LETTER_REQUIRED` (18 fields, the complete list).
  Restructured the required selection: `invoice` → `BASE_REQUIRED + INVOICE_REQUIRED`;
  `offer_letter` → **exactly `OFFER_LETTER_REQUIRED`** (NOT `BASE_REQUIRED +`, so
  `client_name`/`client_email` are never required for an offer letter); else `BASE_REQUIRED`.
  Email format check now covers both `client_email` and `candidate_email`.
- **`test_validate_fields.py`** — `_offer_letter()` helper + 6 tests (valid → exit 0; missing
  candidate_name → missing; missing net_take_home → missing; invalid candidate_email →
  invalid; optional internship absent → exit 0; **regression guard: offer_letter does NOT
  require client_name/client_email**).
- **`context-schema.md`** — offer-letter field table (required candidate_* + optional
  conditional fields), noting the `OFFER_LETTER_REQUIRED`-replaces-`BASE_REQUIRED` rule.

## Done-check

- `test_validate_fields.py`: **29 passed** (+6 offer_letter).
- Full docbuilder suite: **364 passed, 3 skipped** (was 358/3 at t3 — +6).
- Catalogue: `doc_types == ['invoice', 'offer_letter']`. Bundle spec: valid JSON.
- §t4 smoke: `generate_html.py` on `offer_letter_v1.html.j2` with all required fields →
  exit 0, `grep -c '{{'` = **0**, no stderr.
- Conditional sections verified directly: absent internship/bonus → sections skipped (0
  matches); present → all three render (3 matches), individual-bonus period falls back to the
  Jinja `default('September/October')`.

## Notes

- **No DOCX produced in t4** — that needs the t4b orchestrator/compute/rename wiring. t4 only
  proves the HTML renders cleanly (the §t4 done-check is HTML-level by design).
- `narrative.css_file` is `null`: the docx-jinja path (t4b) calls `generate_html` (no CSS) →
  Pandoc (styles from `reference.docx`); the legacy `generate_pdf._narrative_html` css read is
  never hit for a docx-only, `has_jinja` doc. A CSS file lands with the m7 PDF output.
- Scope held: no compute_doc / rename_output / orchestrator / sprint changes (all t4b/t5).
