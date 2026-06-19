# Review — m-docbuilder-m1 t3 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design", §"--output-dir flag"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md

---

## Packet assessment

Ticket ID + scope: ✅ provided  
Diff — generate_xlsx.py: ✅ provided  
Diff — test_generate_xlsx.py: ✅ provided  
Implementation notes: ✅ `m-docbuilder-m1-t3-implementation-notes.md` — present and substantive  
Done-check output: ✅ 17/17 tests pass, pipeline output confirmed (6.3K xlsx)

---

## Findings

1. **[non-blocking]** The numeric string conversion in `_write_cell` applies
   `float()` coercion when `col_type in ("currency", "number")`. This is
   correct and the implementation notes explicitly justify it ("type coercion
   for correct rendering is not computation"). However, the coercion silently
   leaves non-convertible strings as strings — there is no warning or stderr
   note when a cell in a numeric column cannot be converted. For the current
   sample data this is fine, but a real proposal with a blank `unit_price`
   cell would render as a left-aligned text cell inside a right-aligned numeric
   column, which is a subtle visual defect that could go unnoticed. Non-blocking
   because the behaviour is documented and consistent with how `compute_doc.py`
   handles non-numeric values in aggregates (silent skip). Worth noting in the
   t3 implementation notes as a known limitation and a potential t6/t7 candidate
   for a renderer-level warning log.

2. **[non-blocking]** All 17 tests are marked `@pytest.mark.integration` and
   run unconditionally (they pass because openpyxl is installed). The milestone
   t3 prompt specified: "Mark integration tests with `@pytest.mark.integration`
   and skip if openpyxl not installed (conftest pattern from
   agent-creation-guide.md)." The `pytest.importorskip("openpyxl")` at the top
   of the file achieves the skip-if-absent behaviour correctly — the whole
   module is skipped if openpyxl is missing. This is a valid alternative to
   per-test `@pytest.mark.integration` skipping and arguably cleaner. Minor
   discrepancy from the prompt spec but the net effect is identical. No action
   required; noting for completeness.

3. **[non-blocking]** `wb.remove(wb.active)` correctly removes the default
   openpyxl sheet. This is documented in the implementation notes. One edge
   case worth noting for t8 docs: if `doc_spec["sheets"]` is empty (a valid
   but degenerate doc spec), `wb.save()` would produce a workbook with no
   sheets, which Excel rejects on open. The current sample data cannot produce
   this case, but a template validation rule ("sheets array must have ≥1 entry")
   in `compute_doc.py` would be a cleaner guard than silent empty-workbook
   generation. Deferred — not a t3 concern, but worth a backlog note.

---

## Cross-ticket notes

- The numeric string → float coercion pattern identified in finding 1 will
  recur in t4 (python-docx) and t5 (weasyprint). The t3 implementation notes
  already flag this explicitly for t4/t5 authors — good forward signalling.
  If all three renderers handle it identically and silently, the silence may
  become a finding in the t8 milestone summary as a shared limitation.
- The `header_row` as sole anchor pattern (rows array written sequentially from
  `header_row`, merge_ranges handled separately) is clean and consistent with
  the doc spec contract. t4 and t5 should follow the same anchor pattern —
  worth referencing these notes in t4/t5 prompts.
- No process gap in this ticket: implementation notes present, done-check
  complete, diff covers only the two Touches files listed in the milestone doc
  (plus the .gitignore additions committed separately in 239b931). The t3
  session is clean.
- **Zero blocking findings.** t3 is clear to merge and t4 is clear to start.
