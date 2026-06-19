# Review — m-docbuilder-m1 t4 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design", §"--output-dir flag"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md; docbuilder/docs/milestones/m-docbuilder-m1-t3-implementation-notes.md

---

## Packet assessment

Ticket ID + scope: ✅ provided  
Diff — generate_docx.py: ✅ provided  
Diff — test_generate_docx.py: ✅ provided  
Implementation notes: ✅ `m-docbuilder-m1-t4-implementation-notes.md` — present and substantive  
Done-check output: ✅ 17/17 tests pass (1.47s), pipeline output confirmed (37K docx)

---

## Findings

1. **[non-blocking]** `merge_ranges` are silently ignored in this renderer —
   documented in the implementation notes as a deliberate simplification, with
   the sheet-level `add_heading` providing the semantic equivalent. This is
   defensible for m1. However "silently ignored" means a template author who
   expects the merged title cell text to appear in the docx output will get a
   heading with the sheet name, not the merge_range value (e.g. "Line Items"
   rather than "B2B Project Proposal — Line Items"). These are different
   strings. Worth a one-liner in the t8 docs sync noting this renderer-level
   divergence, so it is a known and recorded limitation rather than an
   accidental omission. Non-blocking — the current behaviour is documented and
   the output is usable.

2. **[non-blocking]** `str(cell_spec["value"]) if cell_spec["value"] is not None else ""`
   — the `None` guard is correct and clean. One minor edge: an empty string
   value `""` (which the aggregate row uses for blank cells) serialises
   correctly to `""` via `str("")`, so the guard is not needed for that case
   but does no harm. No action needed, noted for completeness.

3. **[non-blocking]** The `generate_docx` function has `if not rows: continue`
   which skips sheets with no rows. This is consistent with t3's empty-sheets
   edge case (noted there as a backlog item for `compute_doc.py` validation).
   The docx renderer handles it more gracefully than xlsx would (no crash, just
   no table added). Worth a cross-reference in the t8 milestone summary as a
   renderer-level divergence: xlsx would produce a no-sheet workbook (Excel
   rejects), docx silently omits the table (Word opens fine). Both are edge
   cases not reachable with current templates.

---

## Cross-ticket notes

- The `merge_ranges` handling divergence across renderers is now established
  as a pattern: xlsx renders them as merged cells (correct), docx ignores them
  in favour of sheet headings (semantic equivalent, different text), t5
  (weasyprint/HTML) can use `<th colspan="N">` which is the only renderer that
  can faithfully express the merge_range value. The t8 docs sync should record
  this per-renderer behaviour difference explicitly — it will matter to template
  authors who care about the title cell text.
- The `str()` coercion pattern (no numeric conversion needed in docx) is a
  clean counterpoint to t3's float coercion. t5 will be the same as t4 —
  HTML is string-based. The t4 notes already flag this for t5 authors.
- Implementation notes quality: substantive and forward-looking. The t5 notes
  section is particularly useful — `<th colspan="N">` for merge_ranges is the
  right call and is now flagged before t5 starts.
- **Zero blocking findings.** t4 is clear to merge and t5 is clear to start.
