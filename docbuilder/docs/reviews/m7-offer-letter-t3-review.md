# Review — m7 t3 — round 1

Reviewer: claude-ui
Subject: `docbuilder_offer_letter` sprint → PDF + DOCX
(commits `ab929e2` aetheris-agents, `702bac5` aetheris/sprint.sh)

> Filed at `docbuilder/docs/reviews/` (m7 convention).

---

## Findings

**1. [non-blocking] Runbook deprecation note stale: "removal is m7".** `render_template.py`
removal was descoped from m7 — the runbook is a live operator doc, and a passed-milestone ref
accumulates drift. Fix to "removal deferred (post-m7)" or point to backlog.

**2. [question] Confirm `output/offer_letter_v1.html` persists after both renderers** so the
`OL_HTML` structural check's `[INFO]` fallback is a true "pdftotext absent" signal, not a
silent pass on a missing intermediate.

## Cross-ticket notes

Fresh-path → direct-context decision correctly adjudicated + honestly flagged (drops live
context_builder coverage for offer_letter; m6 t5 provenance + unit tests justify it for a
rendering gate). The done-check command-shape finding recurs — four instances now (t3 CAND
env/argv, t2 `cat["doc_types"]`, m6 t4b positional, m5 t1 smoke): **a confirmed t4
learning-promotion candidate** — "a done-check/sprint command written against an assumed data
shape or execution context that differs from runtime; verify the shape before writing it."

t3 otherwise clean.

---

## Resolution (actioned)

- **F1 — fixed.** `docbuilder/runbook.md` §"Jinja2 templates" deprecation note → "**removal
  deferred (post-m7)** — descoped from m7, tracked as an m8 open item".
- **F2 — confirmed + hardened.** The intermediate **persists**: the docx-jinja step
  (`generate_html.py --output`) writes it; `generate_pdf` renders **in-process** (`render_html`,
  no `.html` I/O); `rename_output.py` renames only `KNOWN_EXTS` (`.html` excluded). Nothing
  consumes-and-deletes it. Went beyond confirming: **hardened the check so a missing
  intermediate is now a `fail`, not `[INFO]`** — for a pdf+docx `has_jinja` bundle the file MUST
  exist, so the old `[INFO]` branch would have been a silent pass on a regression. Verified the
  hardened logic against the real `offer_letter_v1.html` artifact → still standalone
  `<table class="net">`. `bash -n` clean.

**Carried to t4:** promote the command-shape learning (the 4th instance this milestone).

**Disposition: t3 clear to merge.** F1 (runbook) + F2 (sprint check hardening) actioned; the
core t3 deliverables (sprint pdf+docx assertions, live PASS `docbuilder-orch-iDGIIQ`) stand.
