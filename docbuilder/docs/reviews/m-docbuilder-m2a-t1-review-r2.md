# Review — m-docbuilder-m2a t1 — round 2

Reviewer: claude-ui
Round 1 blocking finding resolved in fb46052.

---

## Finding dispositions

| # | Finding | Disposition | Assessment |
|---|---------|-------------|------------|
| F1 | [non-blocking] Diff missing from packet | noted — diffs required from t2 onwards | ✅ Acknowledged. Process note in impl notes and review. |
| F2 | [non-blocking] `"docx"` added to `output_formats` outside original touches | actioned — touches list updated in milestone doc | ✅ Audit trail complete. |
| F3 | [blocking] Row-ownership conflict — `header_row` computed vs base file rows | fixed — Option A applied (explicit per-sheet `header_row` field) | ✅ Resolved cleanly. See below. |

---

## F3 resolution assessment

The diff is exactly right for a doc/asset addendum:

- `template-schema.md` — `header_row` per-sheet field documented with the override semantics clearly stated (`overrides compute_doc`), correct example value (3), and cross-reference to README §"Row alignment convention". ✅
- `proposal_v1.json` — `"header_row": 3` on both `Line Items` and `Summary`. ✅
- `m2a-milestone.md` — t1 scope, touches, done-check, and prompt all updated. t2 scope updated with the deliberate `compute_doc.py` carve-out, new `test_compute_doc.py` touch, and hardened done-check assertions (`assert ws.cell(3,1).value == 'Item Code'`). ✅
- Implementation notes addendum — covers the openpyxl cell/fill verification, the "field is inert until t2" correctness point, the Summary base sheet gap carried to t2, and the two non-blocking findings actioned. ✅

No Python changes in this commit. 123 tests unaffected. Field inert until t2 consumes it. Correct.

---

## Carried items confirmed for t2

Two items from the t1 cross-ticket notes that t2 must address:

1. **Summary base sheet under-built** — single styled row (row 1), no logo/navy branding rows. With `header_row: 3` the renderer will leave rows 1–2 empty on the Summary sheet. t2 should either flesh out the Summary branding rows to match Line Items, or explicitly document the asymmetry as a known placeholder limitation in the t2 implementation notes.

2. **`{{>Line Items}}` space in partial name** — t6 must handle sheet names with spaces under its case-insensitive match. Confirmed carried to t6 via cross-ticket notes in the t1 review.

---

## Status

**Zero blocking findings. t1 is fully resolved. t2 is clear to start.**
