# Review — m-docbuilder-m6 t5 — round 1

Reviewer: claude-ui
Subject: Jinja sprint cases + docx-jinja over-match fix
(commits `a86d539` aetheris-agents, `78fe332` aetheris/sprint.sh)

---

## Findings

1. [blocking → closes on evidence] F1 (docx-jinja over-match fix) is already actioned in this
   commit — the `no_sheets?` narrowing is in the diff. The fix is correct, the root cause is
   documented, and the eval-verify shows invoice docx → `generate_docx.py` (not jinja) and
   offer-letter docx → jinja chain (not legacy). No further action — finding closes on the
   evidence already in the packet.

2. [non-blocking] F2 (LLM named optional bonus fields off-schema — `business_performance_bonus`
   instead of `business_performance_bonus_pct`) is correctly recorded as a graceful,
   non-failing outcome and carried to m7. The sprint does not assert the bonus sections, so the
   live run passes. Context-builder prompt concern (the fresh extraction path is
   doc-type-agnostic). Noted for m7; no action in t5.

3. [non-blocking] The `no_sheets?` constraint should be in the §"Jinja2 templates (m6)" runbook
   section so future doc-type authors know: "if your docx output needs computed sheet tables,
   use the structured `generate_docx.py` path, not the jinja chain." Carry to t6: add a
   one-line note to `docbuilder/runbook.md` §"Jinja2 templates (m6)".

4. [non-blocking] `docbuilder_invoice_jinja` is substantively `docbuilder_context` + the
   `pdftotext` zero-`{{` assertion. Consider whether `docbuilder_context` should also gain the
   `{{` assertion (it exercises the same Jinja2 invoice path now). Low priority — the two cases
   can coexist; noting for t6 or m7.

## Cross-ticket notes

- F1 closes on evidence in this packet (no code change needed).
- F3 (no_sheets? note) → t6 Touches: add one line to `docbuilder/runbook.md`
  §"Jinja2 templates (m6)".
- F2 (bonus field names) → m7 open item: make the context builder offer-letter-schema-aware
  for optional field names, or add template aliases.
- F4 (`docbuilder_context` `{{` assertion) → low-priority m7 note.

Strong packet. Both live runs pass, F2 confirmed (both ordered sub-steps ran, `.docx` in
`renamed.json`), and the over-match fix is well-motivated and correctly scoped. The
standalone-`generate_html`-doesn't-inject-tables constraint is the kind of non-obvious thing
that belongs in the runbook for future authors.

---

## Disposition

**t5 clear to merge.** F1 closes on the evidence in the packet (the `no_sheets?` narrowing is
already in `a86d539`); no further code change. Carries:
- **F3 → t6:** one-line `no_sheets?` note added to the t6 scope (`docbuilder/runbook.md`
  §"Jinja2 templates (m6)" + the t6 Touches).
- **F2 → m7:** context builder offer-letter optional-field-name awareness (recorded in the m6
  doc's Open questions for m7).
- **F4 → m7:** consider moving the `{{` assertion into `docbuilder_context` (then
  `docbuilder_invoice_jinja` may be redundant). Low priority; recorded for m7.
