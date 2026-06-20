# Review — m-docbuilder-m2a t2 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md §"Renderer contract"; docbuilder/README.md §"Row alignment convention", §"Design decisions"; docbuilder/docs/template-schema.md (`header_row`, `data_col_start`)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 50/50 tests, base-file round-trip assertions pass, 132/132 full suite, output file listing
Diff: ✅ included (5 files, 340 insertions, 16 deletions)
Implementation notes: ✅ committed — substantive, decisions well-documented

---

## Findings

1. **[non-blocking]** The merge_range write block applies `Font(bold=True)` and
   `Alignment(horizontal="center")` to the merged cell top-left. In base-file mode,
   merges above `header_row` are skipped before reaching this block. Confirmed the
   `continue` exits the entire `for mr in sheet.get("merge_ranges", []):` loop body, so
   both `merge_cells()` and the subsequent `top_left.font`/`top_left.alignment` writes are
   skipped. Clean. Noted so the t3 author doesn't need to re-verify.

2. **[non-blocking]** `test_base_file_merge_above_header_row_skipped` asserts both the
   positive (`A1 == "[ LOGO ]"`) and the redundant negative (`A1 != "B2B Project Proposal
   — Line Items"`). Harmless noise, no action needed.

3. **[non-blocking]** `data_col_start` is read from `doc_spec.get("data_col_start", 1)`
   (top-level), consistent with the template schema. t5 pass-through hasn't landed, so the
   live pipeline defaults to 1 silently; the test injects the field directly. Forward note
   is clear. t5 must include `data_col_start` in its pass-through list alongside
   `table_style` and `narrative`.

4. **[question — carry to t3]** `header_row` is xlsx-specific for positioning. The docx
   renderer builds tables from the logical `rows` array, not physical offsets, so it
   correctly ignores `header_row`. The t3 implementation notes should state this explicitly
   so it doesn't look like a missed requirement.

---

## Cross-ticket notes

- **Merge-skip pattern well-designed.** `base_mode and mr["row"] < header_row` generalises
  correctly: fresh mode skips nothing (m1 preserved), base-file mode protects only the
  base-file-owned region. docx has no merge_ranges (dropped per m1 t4 notes) so the pattern
  isn't ported there — the docx reviewer should confirm the absence is still intentional.
- **`header_row` ripple contained.** Only xlsx is affected by `header_row` as a physical
  position; docx/csv/json/xml/md and pdf (`_build_html()`) all work from the logical `rows`
  array. No cross-renderer ripple.
- **Summary base sheet gap** (third flag: t1 review, t1 addendum, t2 notes). Before t8 the
  demo xlsx base file's Summary sheet needs branding rows 1-2 to match Line Items, else the
  branded output has an asymmetric Summary tab. Candidate for a one-commit asset fix
  alongside t3 or t4 — no separate ticket needed.
- **t5 dependencies confirmed:** `data_col_start`, `table_style`, `narrative` all need to
  flow through `compute_doc.py` → doc spec. Renderers already read them with defaults.

---

**Outcome: zero blocking findings. t2 is clear to merge. t3 is clear to start.**
