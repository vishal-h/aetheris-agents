# Review — m-docbuilder-m2a t3 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md §"Renderer contract"; docbuilder/README.md §"Design decisions" (`table_style`); docbuilder/docs/template-schema.md (`table_style`)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 26/26 tests, base-file round-trip assertions pass (header/footer preserved, 2 tables), 141/141 full suite, output file listing
Diff: ✅ included (3 files, 254 insertions, 8 deletions)
Implementation notes: ✅ committed — decisions well-documented, F4 from t2 review explicitly confirmed, carried items clearly listed

---

## Findings

1. **[non-blocking]** `_apply_table_style()` emits a JSON warning line to stderr —
   right channel and format. But it fires per table when the base file lacks the
   style (2 warnings for the demo's 2 sheets; 10 for a 10-sheet template). A single
   document-level warning ("style X not found; all tables use default") would be less
   noisy. Documented, expected, tested. Disappears once base files are regenerated.

2. **[non-blocking]** `test_base_file_title_not_duplicated` asserts `title_headings
   == []`, which relies on the demo base file having no `"Title"`-styled paragraph.
   If a regenerated base file uses a Word `"Title"` style for its cover, this test
   would fail despite the renderer being correct. A before/after count assertion (the
   `"Title"` count did not increase) would test renderer behaviour rather than a base
   file assumption. Correct for the committed base file.

3. **[non-blocking]** `_add_section_heading()`'s fallback produces a bold body
   paragraph with no paragraph style — in a branded doc, section headings would look
   inconsistent if the base file defines `Heading 1` with brand colours but the
   fallback bypasses it. Correct for "don't crash"; visual consistency depends on the
   base file defining `Heading 1`, which becomes a tenant onboarding requirement worth
   recording in the runbook.

---

## Cross-ticket notes

- **F4 from t2 explicitly confirmed** in the t3 notes and the `generate_docx()`
  docstring — `header_row` is xlsx-specific positioning; docx builds from the logical
  `rows` array. Right place, right detail.
- **Defensive pattern established.** The `_add_section_heading()` / `_apply_table_style()`
  "try named style, degrade gracefully" pattern is clean and worth recording in
  `agent-creation-guide.md` §"Script design" at milestone end (t10).
- **Base file asset gap — now flagged in t1, t1-addendum, t2, and t3 (four tickets).**
  Threshold for a CLAUDE.md promotion at t10: "Demo base files must include standard
  named styles (`Heading 1`, `Table Grid`) and consistent branding across all sheets
  before the sprint case runs." More immediately: the pre-t8 regeneration commit should
  happen before t4 starts (or at latest before t8) — while the docx changes are fresh
  and before the gap affects t4/t5/t6 outcomes.
- **t5 pass-through list confirmed:** `table_style`, `data_col_start`, `narrative` — all
  three must flow `compute_doc.py` → doc spec.

---

**Outcome: zero blocking findings. t3 is clear to merge. t4 is clear to start.**
