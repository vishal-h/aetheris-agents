# Review — m-docbuilder-m2a t6 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/README.md §"Template model" (narrative mode, PDF rendering modes); docbuilder/docs/doc-spec-schema.md

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 11/11 tests, standalone render confirmed (5669 bytes HTML with Acme Corp + table), 156/156 full suite
Diff: ✅ included (3 files, 383 insertions, 0 deletions)
Implementation notes: ✅ committed — new dependency surfaced upfront, three design decisions documented, t2-review F-note about spaced partial names explicitly answered

---

## Findings

1. **[non-blocking]** `markdown` is a new third-party package not previously declared.
   The notes flag a t10 `requirements.txt`; the `pytest.importorskip` means a fresh env
   skips the module silently rather than failing loudly. **Actioned now:** added a Python
   dependencies section to `docbuilder/runbook.md` (`pip install openpyxl python-docx
   weasyprint markdown`). t10 still gets the pinned `requirements.txt`.

2. **[non-blocking]** `_render_table()` duplicates `_build_html()` markup. Correct,
   justified decision (keeps render_template weasyprint-free). A `_table_html.py` shared
   helper at t10 would remove the dual-maintenance risk. **Added as an explicit t10
   Touches item.**

3. **[non-blocking]** `test_cli_full_pipeline` (and the done-check standalone render)
   use single-source invocation of the two-source demo template. Correct per the t4
   contract (Summary uses `summary_rows`, needs no source). Confirmed intentional.

4. **[question — t7]** `render_template.py` uses `--spec` (not `--input`). t7 calling it
   as a subprocess should pass `--spec <temp file>` (the m1 write-to-temp pattern) or
   `--spec -` (stdin). **Actioned:** the t7 prompt already lists `--spec` among the
   subprocess args; added a one-line clarification that it takes a path (temp file) or
   `-`.

---

## Cross-ticket notes

- **Disjoint placeholder regexes** (`\w+` vs `>`) give order-independence; case-insensitive
  sheet-name resolution answers the t2-review spaced-name question. Both tested.
- **`file://` CSS href** is the right call for weasyprint (no base_url needed at t7).
- **t10 Touches confirmed:** (a) `docbuilder/requirements.txt` with pinned versions
  (`openpyxl`, `python-docx`, `weasyprint`, `markdown==3.10.2`); (b) `_table_html.py`
  shared helper to dedupe `_render_table`/`_build_html`. Both added to the t10 ticket.

---

**Outcome: zero blocking findings. t6 is clear to merge. t7 is clear to start.**
Non-blocking F1/F4 actioned in the same commit; F2 recorded as a t10 Touches item.
