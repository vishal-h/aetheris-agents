# Review — m-boxy-pipeline t2 — catalog resolver

## Summary

| # | Severity | Status |
|---|---|---|
| 1 | **doc error** | fixed ✓ — milestone doc done-check updated to "≥4 exact matches" |
| 2 | non-blocking | noted — col-index discrepancy documented in implementation notes |
| 3 | **question** | resolved ✓ — `DA 6698 W` emits two separate unresolved records (one per drawing) |

---

## Done-check results

```
exact:       4   (W2739, DB30, DB21, SB42)
fuzzy:       3   (W2424-24, W2439-24 ×2)
unresolved: 20   (BLB42FHL ×3, USF330 ×3, USF357 ×2, DA 6698 W ×2, and others)
```

**Specific assertions:**

| Assertion | Result |
|-----------|--------|
| `DB30` resolves to `DB30-2004` | ✓ |
| `DB30` has `match_confidence: "exact"` | ✓ |
| `KFNF 9959 iDE` is `unresolved` | ✓ |
| `G 7186 SCVi` is `unresolved` | ✓ |
| At least 4 `exact` matches (corrected threshold) | ✓ |

---

## Finding 1 — "≥10 exact matches" was wrong (doc error, fixed)

The original done-check required at least 10 exact matches. The actual Boxy MSRP
catalog contains entries for only 6 of the 20 distinct t1 codes (4 exact, 2 fuzzy).
The remaining 14 are 20-20-specific codes or appliance codes with no Boxy equivalent.

`docs/m-boxy-pipeline.md §t2` done-check updated to:
> "At least 4 `exact` matches present (`W2739`, `DB30`, `DB21`, `SB42`); all three
> appliance codes (`DA 6698 W`, `G 7186 SCVi`, `KFNF 9959 iDE`) unresolved."

The unresolved codes fall into three categories:
- **20-20 accessories/fillers:** `USF330`, `USF357`, `WEP42`, `BLB42FHL`, `BPBC12`,
  `BPBC9`, `OVB36`, `CKT36`, `FSEP2493`, `SUW2418-24`, `WP3612-24HK`
- **Appliances:** `DA 6698 W`, `G 7186 SCVi`, `KFNF 9959 iDE` (correct — unresolved)

**Cross-ticket note:** Both t1 ("≥15 codes") and t2 ("≥10 exact matches") had
done-check thresholds set during milestone drafting before the sample files were
examined. Going forward: don't write numeric done-check thresholds before running
the script against the actual inputs.

---

## Finding 2 — Column index discrepancy (non-blocking, documented)

The milestone doc states "col 2 = item code, col 3 = description" (1-indexed from
`NO.`). Actual 0-indexed pandas positions: col 4 = Item code, col 5 = Description.
Implementation uses actual indices. Detail in implementation notes.

---

## Finding 3 — `DA 6698 W` per-drawing behaviour (resolved)

`DA 6698 W` (dishwasher) appears on both `El3` and `floor_plan`. The resolver
processes each `PlanComponent` independently → **two separate `unresolved`
`ResolvedItem` records** in t2 output:

```
drawing='El3',         confidence='unresolved'
drawing='floor_plan',  confidence='unresolved'
```

The resolution table below summarises by distinct code; `t2` output has 27 records
total. **t3 implication:** the formatter will receive two line items for `DA 6698 W`
and should emit both.

---

## Full resolution table (distinct codes)

| Code | Drawing(s) | Confidence | SKU |
|------|-----------|-----------|-----|
| W2739 | El1 | exact | W2739-2001 |
| DB30 | El1 | exact | DB30-2004 |
| DB21 | El4 | exact | DB21-2004 |
| SB42 | El4 | exact | SB42-2004 |
| W2424-24 | El2 | fuzzy | W2424-2001 |
| W2439-24 | El2, El4 | fuzzy | W2439-2001 |
| BLB42FHL | El1, El3, El4 | unresolved | — |
| USF330 | El2, El3, El4 | unresolved | — |
| USF357 | El2, El4 | unresolved | — |
| DA 6698 W | El3, floor_plan | unresolved | — |
| G 7186 SCVi | El2 | unresolved | — |
| KFNF 9959 iDE | El2 | unresolved | — |
| WEP42 | El1 | unresolved | — |
| WP3612-24HK | El2 | unresolved | — |
| FSEP2493 | El2 | unresolved | — |
| CKT36 | El3 | unresolved | — |
| OVB36 | El3 | unresolved | — |
| BPBC12 | El3 | unresolved | — |
| BPBC9 | El3 | unresolved | — |
| SUW2418-24 | El4 | unresolved | — |

---

## Test results

```
27 passed, 0 failed — tests/test_catalog_resolver.py
76 passed, 0 failed — full suite (t1 + t2)
```
