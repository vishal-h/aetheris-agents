# Review — m-docbuilder-m6 t3 — round 1

Reviewer: claude-ui
Subject: migrate invoice to Jinja2 + `has_jinja` PDF branch (commit `429972d`)

---

## Findings

1. [blocking → adjudicated ACCEPT] `compute_doc.py` scope addition. The migration cannot
   hold end-to-end without the `has_jinja` passthrough — the implementation notes document
   the root cause (compute_doc rebuilds a fresh output dict and dropped the key, causing the
   invoice to fall back to the legacy Markdown renderer on the `.html.j2` and leak literal
   `{{ client_name | default('') }}`). The fix is correct, backward-compatible (default
   `False` for pre-m6 bundles), regression-guarded (2 new compute_doc tests + the t5 gate),
   and the milestone doc's t3 Touches + scope-addition note are updated.
   **Adjudication (Vishal, accepted): scope addition accepted.** Rationale: it is not new
   scope but a required part of t3's stated goal ("migrate the invoice to Jinja2"); omitting
   it leaves a non-functional migration, not a smaller one. No code change — finding closes
   on adjudication.

2. [non-blocking] `_narrative_html_jinja` imports `generate_html` inside the function body.
   Correct per the "lazy heavy imports" learning (m2b) — the import only fires when the
   Jinja2 path is taken, keeping the module importable for legacy-only callers. Intentional;
   no action.

3. [non-blocking] Visual equivalence between the Jinja2 and Markdown invoice PDFs is
   best-effort (acknowledged in the notes). Same `invoice_v1.css` + same DOM class names →
   high structural equivalence. The t5 `docbuilder_invoice_jinja` sprint (`pdftotext` + zero
   `{{`) is the production regression gate. No action in t3.

## Cross-ticket notes

- F1 adjudication: **accepted** (recorded above).
- The `{% if tables and 'Line Items' in tables %}` guard (not
  `{{ tables['Line Items'] | default('') }}`) is the correct pattern for subscripting a
  potentially-undefined Jinja2 variable — subscripting an undefined raises `UndefinedError`
  before any filter runs. → carried to the t5 runbook §"Jinja2 templates" primer.
- The `| safe` on `render_table` output is the canonical legitimate autoescape bypass —
  trusted, pre-rendered Python markup. → carried to the t5 runbook primer as the example.

Excellent packet. The `compute_doc.py` scope addition is the standout — caught by an
end-to-end check during implementation, documented clearly, and correctly handled.

---

## Disposition

**t3 clear to merge.** F1 adjudicated ACCEPT (scope addition is a required part of the t3
goal; no code change). F2/F3 informational. Code unchanged from `429972d`. The two Jinja2
authoring notes (the `{% if %}` subscript guard + `| safe` for trusted `render_table` markup)
are carried into the t5 runbook §"Jinja2 templates (m6)" primer alongside the t1/F1 autoescape
note.
