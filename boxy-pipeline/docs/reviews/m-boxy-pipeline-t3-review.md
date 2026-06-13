# Review — m-boxy-pipeline t3 — order formatter — round 1

## Summary

| # | Severity | Status |
|---|---|---|
| 1 | non-blocking | noted — integration test duplication; fixture pattern for t4 |
| 2 | non-blocking | noted — t4 must pass `pipeline_result.resolved` to `write_order_form`, not full struct |
| 3 | question | resolved ✓ — rows 42–67 VLOOKUP retention is intentional |

**t3 approved for merge.**

## Done-check results

```bash
# Full pipe:
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 scripts/catalog_resolver.py \
    --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --upper-finish "2001:Ivory White:2000" \
    --lower-finish "2004:Mingo Oak:2000" \
  | python3 scripts/order_formatter.py \
    --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --project "Joey_Kitchen_V2" \
    --output-dir output/
```

Output: `output/Joey_Kitchen_V2_order_form.xlsx` (5.2 MB)

| Assertion | Result |
|-----------|--------|
| Output file created | ✓ `output/Joey_Kitchen_V2_order_form.xlsx` |
| ≥10 line items populated | ✓ 27 line items |
| Amount column contains formulas | ✓ 27/27 rows have `=IFERROR($D{row}*$E{row},"")` |
| ≥1 unresolved item flagged | ✓ 20 rows flagged "UNRESOLVED - manual review required" |
| 3 fee placeholder rows | ✓ Assembly Fee, Modification Fee, Delivery Fee (rows 39–41) |

---

## Order form line items

```
row 12: WEP42         color=       price=           ← UNRESOLVED
row 13: W2739         color=2001   price=450.8
row 14: BLB42FHL      color=       price=           ← UNRESOLVED
row 15: DB30          color=2004   price=1188.4
row 16: KFNF 9959 iDE color=       price=           ← UNRESOLVED
row 17: G 7186 SCVi   color=       price=           ← UNRESOLVED
row 18: WP3612-24HK   color=       price=           ← UNRESOLVED
row 19: W2424-24      color=2001   price=265.55
row 20: W2439-24      color=2001   price=372.55
row 21: USF357        color=       price=           ← UNRESOLVED
row 22: FSEP2493      color=       price=           ← UNRESOLVED
row 23: USF330        color=       price=           ← UNRESOLVED
row 24: DA 6698 W     color=       price=           ← UNRESOLVED
row 25: CKT36         color=       price=           ← UNRESOLVED
row 26: USF330        color=       price=           ← UNRESOLVED
row 27: BLB42FHL      color=       price=           ← UNRESOLVED
row 28: BPBC12        color=       price=           ← UNRESOLVED
row 29: OVB36         color=       price=           ← UNRESOLVED
row 30: BPBC9         color=       price=           ← UNRESOLVED
row 31: W2439-24      color=2001   price=372.55
row 32: USF357        color=       price=           ← UNRESOLVED
row 33: SUW2418-24    color=       price=           ← UNRESOLVED
row 34: USF330        color=       price=           ← UNRESOLVED
row 35: DB21          color=2004   price=1026.4
row 36: SB42          color=2004   price=643.8
row 37: BLB42FHL      color=       price=           ← UNRESOLVED
row 38: DA 6698 W     color=       price=           ← UNRESOLVED
row 39: Assembly Fee  (placeholder)
row 40: Modification Fee (placeholder)
row 41: Delivery Fee  (placeholder)
```

Resolved: 7 rows with prices (W2739, DB30, W2424-24, W2439-24 ×2, DB21, SB42)
Unresolved: 20 rows flagged
Fee placeholders: 3 rows

---

## Test results

```
22 passed, 0 failed — tests/test_order_formatter.py
98 passed, 0 failed — full suite (t1 + t2 + t3)
```

---

## Round-1 findings

**Finding 1 — Integration test duplication (non-blocking, deferred to t4)**
The four integration tests each repeat the full t1→t2 subprocess chain (~20 lines
each). A shared `@pytest.fixture` that runs the pipe once and returns the open
workbook would eliminate the duplication. Pattern to apply in `test_main.py` (t4).

**Finding 2 — `write_order_form` takes `list[dict]`, not `PipelineResult` (non-blocking)**
Intentional for t3 — the formatter is called directly from the t2 pipe. When `main.py`
(t4) wires the pipeline, it must extract `.resolved` from the `PipelineResult` before
calling `write_order_form`. No change needed in `order_formatter.py`.

**Finding 3 — Rows 42–67 retain template VLOOKUP formulas (answered)**
Intentional. Those rows are beyond the 27 items + 3 fees we write. Since col B (ITEM)
is empty, the VLOOKUP evaluates to `""` — the rows appear blank to the reviewer.
The `=SUM($F12:$F67)` subtotal in F68 sums correctly. On record; no fix needed.

---

## Design notes

- **Input format**: formatter reads a JSON array of ResolvedItem dicts from stdin
  (t2 output directly). `--project` provides the output filename stem. The t4
  aggregation step (PipelineResult) is deferred per the milestone scope.

- **Amount formula**: `=IFERROR($D{row}*$E{row},"")` written explicitly per row —
  matches the template's formula pattern and makes the output self-contained.

- **Color column**: writes the color code only (e.g. `"2001"`), not the full string
  (`"2001 Ivory White"`) that the template's VLOOKUP expects. Since we overwrite
  column E with the MSRP number directly, the VLOOKUP is not active and the Color
  cell is for human reference only.

- **Unresolved items**: ITEM = raw plan code, Color and Unit Price blank, Amount
  formula still present (evaluates to "" since E is blank), Special Request =
  "UNRESOLVED - manual review required".

- **Fee placeholder rows**: ITEM name only; Color, QTY, Unit Price, Amount, Special
  Request all set to None (clears template formulas in those cells).

- **Template rows beyond used range**: the template has 56 pre-filled formula rows
  (12–67). Rows 42–67 (beyond our 27 items + 3 fees) retain the template's
  VLOOKUP in col E — these evaluate to `""` since col B (ITEM) is empty.
  The SUM in F68 (`=SUM($F12:$F67)`) correctly totals only the resolved rows.
