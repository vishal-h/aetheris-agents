# Review — m-docbuilder-m5 t3 — round 1

Reviewer: claude-ui
Subject: `docbuilder_fresh_render` sprint case (commits `69f41a2` aetheris/sprint.sh,
`8dcfb47` aetheris-agents runbook + notes)

---

## Findings

1. [non-blocking] The `docbuilder_fresh_render` confirmed_context.json output in the
   done-check is missing `variant: "v1"` which appeared in the t2/t3 Northwind run
   from the m4 sanity tests. This is not a regression — the Northwind context written
   by `context_builder.exs` may or may not include `variant` depending on whether the
   LLM extracts it from the catalogue. It is an optional field and its absence is
   correct (it does not affect the render). Noting for the record; no action required.

2. [non-blocking] The live run result is the proof that matters: `confirmed_context.json`
   for Northwind contains no `order_ref`, `order_effective_date`, or `terms`, and the
   PDF placeholder assertion passed. This is the end-to-end verification of the t1
   `_sub_var` fix. Well-documented in the implementation notes.

## Cross-ticket notes

- The `bash -n` syntax check is a good gate to include; confirm it stays in the
  done-check for future sprint-case additions.
- t4 Touches must include the smoke command correction from the t1 review (F1):
  update `m5-milestone.md §t1 Done-check` to use `invoice_v1.md.template` /
  `invoice_v1.css` and `--spec '{"sheets":[]}'`. This was explicitly carried to t4.
- No recurring findings across t1–t3 to flag for learning promotion yet.

Clean. All assertions pass end-to-end: confirmed_context written, three rendered files
present, zero `{{` artifacts in the PDF, run log 0→1.

---

## Disposition

**t3 clear to merge as-is.** Both findings non-blocking; no code changes. Code unchanged
from `69f41a2`/`8dcfb47`.

**t4 carry confirmed:** the t1/F1 smoke-command correction is already recorded in the t4
Touches list in `m5-milestone.md §t4` (added when t1 closed, commit `5e3d7ba`) — claude-code
will action it in the t4 docs-sync commit. Cross-ticket note re: `variant` is informational
only (optional field, correct to omit). No t1–t3 recurring findings → the t4 CLAUDE.md
`## Learning — m5-docbuilder` scan will likely record "No recurring findings".
