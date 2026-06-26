# Implementation notes — m-docbuilder-m6 t3 (migrate invoice to Jinja2)

Ticket: replace the invoice's Markdown narrative template with a Jinja2 `.html.j2`, wire a
`has_jinja` branch into `generate_pdf.py`, and flip the bundle spec. `render_template.py` and
`invoice_v1.md.template` are left in place (deprecated, removed in m7).

---

## What shipped

- **`invoice_v1.html.j2`** (new) — a complete HTML document mirroring the
  `invoice_v1.md.template` layout (header/GST banner/meta block/bank block/signatory). It
  `<link>`s `invoice_v1.css` relatively (WeasyPrint resolves it against `base_url`, set by
  `generate_pdf` to the bundle dir). All context vars use `{{ field | default('') }}`. The
  Line Items table is emitted with
  `{% if tables and 'Line Items' in tables %}{{ tables['Line Items'] | safe }}{% endif %}`.

- **`invoice_v1.json`** — added top-level `"has_jinja": true`; changed
  `narrative.template_file` from `invoice_v1.md.template` → `invoice_v1.html.j2`
  (`template_file` is nested under `narrative`, per the m6 §Pre-flight note). No other field
  touched.

- **`generate_pdf.py`** — `_narrative_html` now branches: `doc_spec.get("has_jinja")` →
  new `_narrative_html_jinja`, else the legacy render_template.py subprocess path.
  `_narrative_html_jinja` imports `render_html` **in-process** (no subprocess — avoids the
  extra process per render), pre-renders each sheet with the shared `render_table` into
  `context["tables"][{sheet name}]` (so all table formatting stays in Python, not the
  template), and calls `render_html(template_path, context, spec=doc_spec)`.

- **`compute_doc.py`** (scope addition) — passes `has_jinja` through to the computed doc
  spec (`"has_jinja": template.get("has_jinja", False)`). See below.

- **Tests** — `test_generate_pdf.py` +3 (Jinja HTML has table + present var + zero `{{`;
  Jinja path renders a PDF; the committed `invoice_v1.html.j2` with optional fields absent →
  no leak); `test_compute_doc.py` +2 (`has_jinja` passthrough true; defaults False when
  absent).

## Scope addition — `compute_doc.py` passthrough (adjudicated)

The milestone t3 Touches did not list `compute_doc.py`, but the migration cannot hold
without it: `compute_doc` builds a fresh output dict copying only selected keys, so it
**dropped `has_jinja`**. In the real pipeline (`compute_doc → generate_pdf`) the spec reached
`generate_pdf` with no `has_jinja`, the branch never fired, and the invoice rendered via the
**legacy Markdown** path on the `.html.j2` — which leaked literal `{{ client_name | default('') }}`
(render_template's `VAR_RE` only matches `{{\w+}}`, not the filter syntax). Discovered by an
end-to-end check during implementation. Fix: pass `has_jinja` through with a `False` default
(pre-m6 bundles unchanged). The m6 doc's t3 Touches + a scope-addition note were updated in
this commit. This is the prerequisite for the t5 `docbuilder_invoice_jinja` `grep '{{'` gate.

## Done-check

- `test_generate_pdf.py`: **22 passed** (+3 Jinja).
- `test_compute_doc.py`: **33 passed** (+2 passthrough).
- Full docbuilder suite: **358 passed, 3 skipped** (was 353/3 at t2 — +5).
- Smoke (§t3, standalone `generate_html.py` on `invoice_v1.html.j2`): exit 0, `grep -c '{{'`
  = **0**, no stderr (the `{% if tables %}` guard makes the template safe to render without
  `tables`, e.g. this direct call).
- End-to-end (`fetch_data → compute_doc → generate_pdf`, instrumented): computed spec carries
  `has_jinja: True`, the **Jinja branch is taken**, PDF ~87 KB (`%PDF-`), rendered HTML
  contains the Line Items `<table>` and the client name, zero `{{` leaks.

## Notes / decisions

- **`| safe` on the table** is the legitimate t1-F1 case: `render_table` output is trusted,
  pre-rendered markup we want injected as-is (autoescaping is on for everything else).
- **Standalone-render safety:** the `{% if tables %}` guard (not `{{ tables['x'] | default }}`)
  is required — subscripting an *undefined* `tables` raises `UndefinedError` before any filter
  runs. The guard lets the §t3 smoke (which has no `tables`) render cleanly.
- **Visual equivalence** vs the Markdown path is best-effort: the `.html.j2` reproduces the
  same DOM/classes against the same `invoice_v1.css`, and the smoke confirms zero leaks, but
  neither asserts pixel layout. `render_template.py` + `invoice_v1.md.template` remain in place
  as the comparison/rollback reference until m7.
- Scope held otherwise: `render_template.py` untouched, `invoice_v1.md.template` not deleted.
