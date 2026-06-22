# Review — fix/docbuilder-currency-rendering — round 1

Reviewer: claude-ui
Contract refs: agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md
§"Implementation notes" (shared `_helper.py` pattern with lazy imports);
docbuilder/docs/doc-spec-schema.md §"Column types";
docbuilder/docs/tickets/fix-docbuilder-currency-rendering.md

---

## Packet assessment

- Ticket ID + scope: ✅ provided (standalone fix, outside m1–m2b)
- Done-check output: ✅ opens packet — 233/233 + 3 skipped full suite, 159/159
  non-integration, targeted currency tests, bitloka invoice sprint
  (`docbuilder-orch-B34gfA`, status `done`, `$1,000.00` in all three outputs +
  Total row)
- Diff: ✅ included (335 insertions, clean and self-contained)
- Implementation notes: ✅ committed — design decision (formatting in the renderer
  layer, not `compute_doc`) documented, negative currency noted

---

## Findings (all non-blocking)

1. **`_format.py` is a new shared helper** — needs a capability-matrix row at the
   next regen (alongside `_drive.py`, `_table_html.py`). No action now; note for
   the next docs sync (m3 t8 or equivalent). Suggested description: "Shared display
   formatter for cell values: currency → `$1,234.56`, number → thousands-separated
   with no trailing zeros."

2. **`format_number` caps non-integer values at 2 dp** (`1234.567` → `1,234.57`)
   via `f"{num:,.2f}".rstrip("0").rstrip(".")`. Never fires for count columns
   (integers). **Actioned:** added a one-line doc comment to `format_number`
   noting the 2 dp cap.

3. **`format_currency(-50)` → `"$-50.00"`** not accounting-style `"-$50.00"`.
   Documented in the notes; correct for this scope (no negative-amount invoice
   case).

4. **xlsx uses native Excel number formats** (`"$"#,##0.00`, `#,##0.##`), not
   `_format.py`. Right decision — Excel formats display natively while the cell
   value stays numeric. Asymmetry is documented in `_format.py`'s module docstring.
   Intentional. ✅

5. **[positive]** `test_currency_cells_formatted` (render_template) asserts both
   `"$3,000.00" in out` AND `">3000.00<" not in out` — the negative assertion
   confirms the raw value doesn't leak. Right test pattern for a formatting fix. ✅

---

## Cross-ticket notes

- `_format.py` follows the shared-helper pattern — pure stdlib, no lazy imports
  needed (no heavy deps). Consistent with `_table_html.py`. ✅
- Capability matrix: `_format.py` needs a row at next regen (see F1).
- Design decision correct and documented: formatting lives in the renderer layer
  keyed off column type by index; `compute_doc` produces raw values; renderers
  never assume pre-formatted input. Right boundary.

---

**Outcome: zero blocking findings. Fix is clear to merge to main.**
F2 actioned (2 dp doc comment); F1 carried to next capability-matrix regen;
F3/F4/F5 are confirmations.
