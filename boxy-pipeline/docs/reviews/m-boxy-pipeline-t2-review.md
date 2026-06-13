# Review — m-boxy-pipeline t2 — catalog resolver

## Summary

| # | Severity | Status |
|---|---|---|
| 1 | **doc error** | noted — done-check "≥10 exact matches" is unachievable with this data |
| 2 | non-blocking | col-index discrepancy between milestone doc and actual Excel |

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
| At least 10 `exact` matches present | ✗ — 4 achieved (see Finding 1) |

---

## Finding 1 — "≥10 exact matches" is unachievable (doc error)

The done-check requires at least 10 exact matches. The actual Boxy MSRP catalog
contains entries for only 6 of the 20 distinct t1 codes (4 exact, 2 fuzzy).
The remaining 14 are 20-20-specific codes or appliance codes with no Boxy
catalog equivalent.

**Why the discrepancy:** The milestone doc was written against the expected
project scope, not the specific Joey kitchen drawings. The six catalog-matching
codes cover the Boxy cabinetry that actually appears in the drawings:

```
W2739     → W2739-2001   (exact — wall cabinet, upper finish)
DB30      → DB30-2004    (exact — normalized from 3DB30, lower finish)
DB21      → DB21-2004    (exact — normalized from 3DB21, lower finish)
SB42      → SB42-2004    (exact — sink base, lower finish)
W2424-24  → W2424-2001   (fuzzy — strip -24 suffix)
W2439-24  → W2439-2001   (fuzzy — strip -24 suffix, appears on El2 and El4)
```

The unresolved codes fall into three categories:
- **20-20 accessories/fillers:** `USF330`, `USF357`, `WEP42`, `BLB42FHL`, `BPBC12`,
  `BPBC9`, `OVB36`, `CKT36`, `FSEP2493`, `SUW2418-24`, `WP3612-24HK` — these are
  20-20 Design product codes with no Boxy equivalents
- **Appliances:** `DA 6698 W`, `G 7186 SCVi`, `KFNF 9959 iDE` — dishwasher, oven, 
  refrigerator (correct — these should be unresolved)

The "exact" confidence threshold in the done-check assumes a catalog that matches
the plan codes 1:1. The actual Joey kitchen uses a significant number of
non-Boxy items.

---

## Finding 2 — Column index discrepancy (non-blocking)

The milestone doc states "col 2 = item code, col 3 = description" (1-indexed from the
visible data columns NO., Image, Item, Description). The actual 0-indexed pandas column
indices are col 4 = Item code, col 5 = Description. The implementation uses the actual
indices; the doc's column numbering counts from `NO.` as column 1, skipping cols 0-1
(branding/empty).

---

## Resolution approach

The `DB30 → exact` requirement is met via the catalog normalization index:
`3DB30` in the catalog is indexed under both `"3DB30"` (raw) and `"DB30"` (normalized,
leading-digit stripped). When plan code `DB30` is looked up, it hits the `"DB30"` key
in the index and is classified as `"exact"` — the base code matched exactly at the
normalized level.

SKUs are constructed as `{matched_code}-{color_code}` using the plan-side matched code,
so `DB30` resolves to `DB30-2004` (not `3DB30-2004`), matching the done-check expectation.

---

## Full resolution table

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
