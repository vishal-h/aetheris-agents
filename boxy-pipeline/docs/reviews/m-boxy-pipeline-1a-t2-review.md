# Review — m-boxy-pipeline-1a t2 — SO extractor — round 1

## Summary

| # | Severity | Status |
|---|---|---|
| 1 | non-blocking | backlog → BL-013 (parameterise column x-boundaries) |
| 2 | non-blocking | backlog → BL-014 (parse bill_to/ship_to separately) |
| 3 | question | resolved ✓ — 34 items confirmed correct (see §Finding 3 disposition) |

**t2 approved for merge.**

## Done-check output

```
$ python3 scripts/so_extractor.py \
    --so data/samples/SO86708_Aria_Joey.pdf \
    --project joey \
    --output-dir data/projects/

SO SO86708 — 34 items — $8,099.54 — data/projects/joey/sales_order.json
```

Verification snippet:

```
Order: SO86708
Customer: Aria Interior Finishes
Line items: 34
Total: $8,099.54
  Cabinets: 17, Accessories: 12, Fees: 5
OK
```

| Assertion | Result |
|-----------|--------|
| `order_number == "SO86708"` | ✓ |
| `total == 8099.54` | ✓ |
| `len(line_items) > 20` | ✓ 34 items |
| `subtotal == 8099.54` | ✓ |
| `tax_total == 0.0` | ✓ |
| Assembly Fee qty=17 @ $30.00 | ✓ |

---

## Test results

```
32 passed, 0 failed — tests/test_so_extractor.py (1.01s)
158 passed, 0 failed — tests/ full suite (28m 58s)
```

Tests:
- 10 unit tests (no PDF): `_parse_money` variants, `_extract_sku` for products/fees/modifiers
- 22 integration tests using `scope="module"` fixture (PDF loaded once):
  order number, order date, customer, estimate number, payment term,
  line item count, subtotal, tax total, total, fee/accessory/cabinet
  presence, fee-not-accessory invariant, Assembly Fee spot-check,
  cabinet SKU format, Accs- prefix, sequential line numbers, source_file,
  extracted_at ISO format, JSON serialisation, CLI file creation, CLI summary

---

## Finding 3 disposition — 34 line items confirmed

The reviewer's estimate of ~27 was undercounting page 2. Actual breakdown:

**Page 1 (10 cabinets):** 3DB30-2004, BBC42-2004, BSR09-2004, Box-SB36,
BSR12-2004, 3DB21-2004, SB42-2004, Box-WP2493, D-W2439-2004, D-W3624-2004

**Page 2 (7 cabinets + 8 accessories):**
- Cabinets: D-W2424-2004, Box-W362124, D-W3612-2004, W2739-2001,
  W2439-2001, WDC2439-2001, W0939-2001
- Accessories: Accs-PNB36, Accs-TK8, Accs-BF3, Accs-BF6,
  Accs-PNI36, Accs-PNB96, Accs-WF03108, Accs-LCM3-1/2

**Page 3 (4 accessories + 5 fees):**
- Accessories: Accs-LCM3-2001, Accs-PNW48, Accs-WF0351, Accs-DFP24
- Fees: Assembly Fee, Modify-S, Modify-L, Installation fee, Delivery fee

Total: **17 cabinets + 12 accessories + 5 fees = 34** ✓

The $8,099.54 exact total confirms no double-counting.

---

## Design notes

- **x-coordinate column detection**: pdfplumber `extract_words()` with
  fixed column boundaries avoids brittle regex on layout-mode text. Rate
  values are right-aligned and may overspill into the Special Request
  column range — the extractor handles this by taking the last `$NNN.NN`
  token from the spec cell as the unit price.

- **Per-page `in_table` reset**: each page repeats the Boxy Inc header
  block before the table. Resetting `in_table = False` at each page
  boundary prevents header words from being appended to the last item's
  description. Items never span pages in this PDF, so the last pending
  item is finalised when the first item on the next page is encountered.

- **Fee SKU detection**: fees are identified by `_extract_sku`: first
  word lacking a hyphen and not starting with a digit → whole item text
  is the SKU (e.g. "Assembly Fee", "Delivery fee", "Installation fee
  for Add-on Accessories"). Hyphenated fees (Modify-S, Modify-L) are
  captured as a single token.
