# Review — m-docbuilder-m5 t1 — round 1

Reviewer: claude-ui
Subject: `render_template.py` optional field fix (commit `2591d20`)

---

## Findings

1. [non-blocking] The milestone doc's smoke command has two defects documented
   in the implementation notes: (a) template/css filenames use `invoice.md.template`
   / `invoice.css` but the real assets are `invoice_v1.md.template` /
   `invoice_v1.css`; (b) `--spec /dev/null` fails JSON-parse (empty file → renderer
   never runs → trivial 0 count). Claude-code ran a corrected smoke instead and
   confirmed the fix works. Update the milestone doc §t1 Done-check smoke command
   to use the correct filenames and `--spec '{"sheets":[]}'`. Carry this fix into
   the t4 docs-sync commit rather than a separate round-2 here — it's a milestone
   doc edit, not a code change.

2. [non-blocking] `OPTIONAL_FIELDS` in `render_template.py` is a manual copy of
   "schema fields minus required" and must stay in sync with `validate_fields.py`.
   The implementation notes flag this explicitly: "A shared constant module would
   be over-engineering for two scripts. Noted for m6 if the field set grows." The
   comment in the code points to `validate_fields.py` and `docs/context-schema.md`.
   No action required for t1 — the m6 open item is already recorded.

## Cross-ticket notes

- F1 (smoke command correction) must land in t4's docs-sync commit. Add it to the
  t4 Touches list: update `m5-milestone.md §t1 Done-check` smoke command.
- The fix is correctly scoped: only `render_template.py` and its tests changed.
  `generate_pdf.py` is unaffected (it calls `render_template.py` via subprocess).
- t3's `docbuilder_fresh_render` PDF placeholder assertion (`grep -c '{{'` on the
  rendered PDF) is now meaningful — this fix is what makes that assertion
  non-trivially satisfied for fresh-path invoices with absent optional fields.

Clean. 14 tests pass, 329/3 suite, smoke confirmed 0 `{{` artifacts with the corrected command.

---

## Disposition

**t1 clear to merge as-is.** Both findings non-blocking; no code changes. F1 (smoke
command correction) carried into t4's Touches (recorded in `m5-milestone.md §t4`).
F2 is the already-recorded m6 open item.
