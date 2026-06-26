# Review — m-docbuilder-m6 t1 — round 1

Reviewer: claude-ui
Subject: `generate_html.py` — Jinja2 narrative renderer (commit `3d7ab25`)

---

## Findings

1. [non-blocking] Autoescaping is ON for `.j2` templates — this is the correct and
   intentional design (cited in the milestone doc as a Jinja2 benefit). All context
   values in the invoice and offer letter are plain text, so this has no practical
   impact. However, if a future template needs to inject pre-rendered HTML into a
   field (e.g. a rich-text `notes` field), the template author must use
   `{{ field | safe }}` explicitly. Add a note to the t5 runbook §"Jinja2 templates"
   primer: "Autoescaping is on — all values are HTML-escaped by default. Use
   `{{ field | safe }}` only when the value is trusted HTML you want rendered as-is."
   No code change required; carry to t5 Touches.

2. [non-blocking] `pytest.importorskip("jinja2")` at module level in
   `test_generate_html.py` skips the entire module if jinja2 is not installed.
   This is the correct pattern (same as integration tests for wkhtmltopdf etc.).
   With jinja2 now in `requirements.txt`, this guard will never fire in a correctly
   set-up environment. Noting for the record; no action required.

## Cross-ticket notes

- The `jinja2.Undefined` environment setting is confirmed correct: absent variables
  render as `""` and are falsy in `{% if %}` — no `OPTIONAL_FIELDS` workaround needed
  in t3/t4 templates. Template authors use `{{ field | default('') }}` for explicit
  documentation, but the environment handles absent vars gracefully without it.
- F1 (autoescape note) must land in the t5 runbook §"Jinja2 templates" primer. Add it
  to the t5 Touches when prompting that ticket.
- `requirements.txt` change is pre-authorised and correctly scoped in t1 Touches.
  No action needed.

Clean. 15 tests pass, 347/3 suite, both smoke commands match exactly. The `jinja2.Undefined`
behaviour is confirmed correct — absent `{{ var }}` renders as `""`, `{% if var %}` is falsy,
no raw placeholders leak.

---

## Disposition

**t1 clear to merge as-is.** Both findings non-blocking; no code changes. Code unchanged
from `3d7ab25`. F1 (autoescape `{{ field | safe }}` note) carried into the t5 runbook
§"Jinja2 templates (m6)" primer — recorded in `m6-milestone.md §t5`. F2 is informational.
