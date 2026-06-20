# Implementation notes — m-docbuilder-m2a t2

Ticket: `generate_xlsx.py` base-file support + `compute_doc.py` honours explicit `header_row`.

---

## What shipped

- `compute_doc.py`: honours an explicit per-sheet `header_row` (added in t1),
  falling back to the computed `max(merge_range.row) + 1` when absent. Applied in
  both Pass 1 (data sheets) and Pass 2 (summary sheets).
- `generate_xlsx.py`: `--base-file PATH` opens an existing workbook and writes data
  into it, preserving everything the base file owns (rows above `header_row`, columns
  left of `data_col_start`). Absent → fresh `Workbook()` (m1 behaviour, unchanged).
- Tests: +2 compute_doc (explicit override, both passes), +7 generate_xlsx (base file
  + `data_col_start`), and one existing CLI test updated for the demo's new row layout.
- Full suite: 132 passed (was 123; +9 new).

---

## Decisions

**Merge ranges above `header_row` are skipped in base-file mode.**
The t2 prompt said "write merge_ranges to their specified rows as before," but the
done-check requires the base file's logo at `A1` to survive, and the demo's Line Items
merge sits on row 1 — exactly the logo row. Writing it would overwrite `[ LOGO ]`.
Resolution (the t1 row-ownership finding): in base-file mode, skip any merge_range whose
`row < header_row` (the base file owns that region). In fresh mode, all merges are written
(m1 behaviour preserved — `test_merge_range_value` / `test_merge_range_is_merged` still
pass). This is the only intentional divergence from the prompt's literal wording, and it
is what makes the done-check's "logo preserved" assertion pass.

**`data_col_start` read from the doc spec top-level, default 1.**
`generate_xlsx` reads `doc_spec.get("data_col_start", 1)` and shifts both the data grid
and column widths by it. `compute_doc.py` does **not** pass this field through yet — that
is t5. So in the live demo pipeline the value defaults to 1 (no shift); the
`data_col_start: 2` behaviour is unit-tested by injecting the field directly into a spec.
When t5 lands the pass-through, the renderer needs no change.

**Unified column indexing.** Physical column = `data_col_start + col_offset`, and widths
use `get_column_letter(data_col_start + i)`. With the default `data_col_start == 1` this is
identical to the old `start=1` indexing, so fresh-mode output (and all m1 width/position
tests) is unchanged.

**`compute_doc.py` change kept minimal.** Per the t2 carve-out, the only change is honouring
`header_row`; no other compute_doc behaviour was touched. Both passes use
`sheet.get("header_row", computed)`.

---

## Ripple from the `header_row` change (and why the suite still passes)

Making `compute_doc` honour `header_row: 3` shifts the demo's **xlsx physical positions**:
fresh-mode Line Items is now row 1 merge / row 2 empty / row 3 header / rows 4–13 data /
row 14 aggregate (was header row 2, data 3–12, aggregate 13). One existing test asserted the
old positions — `test_cli_proposal_data_row_count` — and was updated (TOTAL row 13→14,
SRV-001 row 3→4, plus an `Item Code` at row 3 check).

The other renderers (docx, csv, json, xml, md) build output from the **logical `rows`
array**, not physical `header_row` offsets, so their demo-template integration tests are
unaffected — confirmed by the full suite (132 passed). `header_row` only changes xlsx (and
would change pdf if it positioned by it, which it does not).

---

## Carried items

- **Summary base sheet is under-built** (flagged in t1). The committed base file's `Summary`
  sheet has only a single styled row (row 1) — no logo/navy branding rows like Line Items.
  With `header_row: 3` the renderer writes the Summary header at row 3, leaving rows 1–2
  sparse. The renderer is correct; the *placeholder base file* is the gap. Not fixed here
  (t2's done-check only exercises Line Items, and base-file content is asset work). t3
  touches docx branding; whoever next regenerates the demo base files should add Summary
  branding rows (logo + navy separator) to match Line Items, or we accept the asymmetry as
  a known placeholder limitation.

## Forward notes

- **t3 (`generate_docx.py`):** same `--base-file` pattern; `table_style` comes from the doc
  spec (defaulted in the renderer until t5 passes it through, same as `data_col_start` here).
- **t5 (`compute_doc.py` pass-through):** add `data_col_start` (and `table_style`,
  `narrative`) to the doc spec output. Once `data_col_start` flows through, the xlsx
  renderer's existing read picks it up with no change.
