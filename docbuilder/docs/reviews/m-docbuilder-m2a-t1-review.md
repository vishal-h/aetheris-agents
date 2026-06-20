# Review — m-docbuilder-m2a t1 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/template-schema.md; docbuilder/README.md §"Template model", §"Row alignment convention"

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet, all four checks pass
Diff: ❌ not included — 8426ea2 contents not in packet. Accepting on done-check evidence for a schema/asset ticket with no Python scripts, but the diff is a required packet element per methodology §5.2. Note for t2 onwards.
Implementation notes: ✅ committed (per CLAUDE.md standing instruction)
Regression: ✅ 123 passed in 7.03s — no regressions

---

## Findings

1. **[non-blocking]** Diff not included in packet. Per methodology §5: "The diff (changed files only)" is required packet element 2. For a schema/asset ticket with no Python scripts this is low risk — done-check output provides sufficient correctness signal — but the pattern must hold for t2 onwards where diffs carry implementation decisions. Not returning the packet; noting for the record.

2. **[non-blocking]** Decision 2 (adding `"docx"` to `output_formats`) is a scope addition not in the t1 touches list. Reasoning is sound and it is documented in the implementation notes, so process was followed. The t1 touches list in the milestone doc should be updated to include it for audit completeness.

3. **[blocking — design clarification before t2]** Row-ownership conflict. `header_row` is computed from `merge_ranges` (`max(row)+1` = 2 for the demo), but the base file's branding occupies rows 1–2 (logo + navy separator), making the first renderer-owned row 3, and t2's done-check expects column headers at row 3. The three do not reconcile.

   **Resolution chosen: Option A** — add an explicit per-sheet `header_row` override to the template schema. `compute_doc.py` uses it when present, falls back to the computed value when absent.

---

## Resolution (this commit)

t1-addendum applied (doc/asset only, keeping t1 within "no Python scripts"):

- **`template-schema.md`** — `header_row` added as an optional per-sheet field; full example shows `header_row: 3` on both sheets.
- **`proposal_v1.json`** — `"header_row": 3` added to `Line Items` and `Summary`.
- **t1 done-check** — now asserts every sheet has `header_row == 3`.
- **Milestone doc** — t1 scope/touches/prompt updated (header_row + the `output_formats` docx note for finding 2); **t2 scope updated** to (a) honour the explicit `header_row` in `compute_doc.py` — a deliberate, minimal carve-out from the "don't modify compute_doc" rule, since it is the enabler for base-file alignment — and (b) assert `Item Code` at row 3 in the base-file done-check.

Base-file layout confirmed via openpyxl (value + fill): `Line Items` row 1 = logo (`D6E4F0`), row 2 = navy separator (`1F4E79`), row 3 = styled header (`E9EFF7`) → `header_row: 3` is correct.

**Carried to t2:** the `Summary` base sheet is under-built (single styled row, no logo/navy rows). t2 should flesh out its branding to match `Line Items` or accept the placeholder gap.

---

## Cross-ticket notes

- gitignore: any new committed data file under `data/` needs an explicit `!filename` exception (the `*.csv` rule would otherwise swallow it). `!sample_data_summary.csv` added.
- Table partials use exact sheet names (`{{>Line Items}}`, not `{{>line_items}}`). t6's `render_template.py` must match `{{>Line Items}}` (with a space) under its case-insensitive rule — confirm the space is handled, not just slug-style names.
- The `"docx"` addition means t8's sprint must verify `proposal_v1.docx` output explicitly alongside xlsx and pdf.

---

**Outcome:** 1 blocking (resolved via Option A in this commit), 2 non-blocking (actioned/noted). t2 is unblocked.
