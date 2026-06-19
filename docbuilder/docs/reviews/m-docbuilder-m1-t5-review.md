# Review — m-docbuilder-m1 t5 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md; docbuilder/docs/milestones/m-docbuilder-m1-t4-implementation-notes.md

---

## Packet assessment

Ticket ID + scope: ✅ provided  
Diff — generate_pdf.py: ✅ provided  
Diff — test_generate_pdf.py: ✅ provided  
Implementation notes: ✅ `m-docbuilder-m1-t5-implementation-notes.md` — present and substantive  
Done-check output: ✅ 13/13 tests pass (3.15s), pipeline output confirmed (14K pdf, %PDF magic bytes)

---

## Findings

1. **[non-blocking]** The implementation notes say "13 tests (8 HTML unit tests +
   2 PDF rendering integration + 3 CLI integration)" but the done-check shows
   13 tests with 5 integration tests running (2 PDF rendering + 3 CLI). The
   notes count is correct in total (13) but the breakdown description says
   "2 PDF rendering integration" which is accurate — the discrepancy is in
   the parenthetical description only, not the test count or the code. Minor
   doc inconsistency, no action needed beyond noting.

2. **[non-blocking]** The `test_html_merge_range_as_colspan` test uses an `or`
   assertion to handle both the escaped (`&#x2014;`) and unescaped (`—`)
   forms of the em-dash. This is pragmatic — `html.escape()` does not escape
   Unicode characters by default, so the unescaped form is what actually
   appears. The test passes correctly. The `or` form is slightly fragile (it
   would pass even if neither branch were the real output path, as long as one
   matched something), but in practice it's fine. Non-blocking — the `%PDF`
   magic bytes test and the `test_cli_pdf_magic_bytes` test together give
   strong correctness confidence at the integration level.

3. **[non-blocking]** `_build_html` uses single-quoted HTML attributes
   (`colspan='2'`, `class='aggregate'`, `style='...'`) which are valid HTML5
   but inconsistent with the double-quoted standard that most HTML linters
   enforce. This has no rendering impact with weasyprint, but if the HTML
   intermediate is ever exposed or logged it may trigger linter warnings.
   Non-blocking for m1.

---

## Cross-ticket notes

- **Done-check omission pattern resolved.** The "full review packet to xclip"
   command change should carry forward to t6 and t7 automatically. The
   milestone doc update (to be done in parallel) is belt-and-suspenders.
- **merge_ranges per-renderer divergence is now fully documented across t3–t5:**
  xlsx = merged cells (value preserved), docx = sheet heading substituted
  (value lost), pdf = `<th colspan>` (value preserved). t8 docs sync should
  record this table explicitly so template authors understand what they get
  per format.
- **`_build_html` as pure function tested independently of rendering** is a
  strong design pattern — 8 fast unit tests run in milliseconds, integration
  tests only for the weasyprint path. Worth calling out positively in the t8
  milestone summary as a technique to carry forward if other renderers develop
  a testable intermediate representation.
- **t6 notes in the implementation notes are detailed and actionable** — the
  four renderer-specific callouts (JSON strips metadata, CSV uses sheet
  separator comment, XML value-only cells, Markdown bold wrapping + separator
  row) give t6 a clear starting point. Good forward signalling.
- **Zero blocking findings.** t5 is clear to merge and t6 is clear to start.
