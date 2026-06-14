# Review — m-boxy-pipeline-1a t1 — catalog extractor + schema additions

## Done-check output

```
$ python3 scripts/catalog_extractor.py \
    --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --output data/catalog.jsonl

Total entries: 4594
  Series 1000: 684 entries
  Series 2000: 1570 entries
  Series 3000: 1390 entries
  Series 4000: 760 entries
  Series 5000: 190 entries
Written to: data/catalog.jsonl
```

Verification snippet:

```
Total entries: 4594
  Series 1000: 684 entries
  Series 2000: 1570 entries
  Series 3000: 1390 entries
  Series 4000: 760 entries
  Series 5000: 190 entries
OK
```

| Assertion | Result |
|-----------|--------|
| All 5 series present | ✓ 1000, 2000, 3000, 4000, 5000 |
| Total entries > 200 | ✓ 4,594 |
| `W2739-2001` present | ✓ msrp=450.8 |
| `mapped_20_20_codes == []` | ✓ |
| `catalog_version` set | ✓ ISO date present |

---

## Test results

```
21 passed, 0 failed — tests/test_catalog_extractor.py (6.02s)
```

Tests:
- 14 unit tests using `minimal_catalog_xlsx` fixture (no real sample needed):
  entry count, SKU format, base_code stripping, enrichment fields, catalog_version
  ISO format, source_file basename, series, dimensions, cabinet_type, color_name,
  MSRP, JSONL serialization
- 7 integration tests against real Excel: all 5 series, entry count, W2739 spot-check,
  enrichment fields empty, catalog_version valid, CLI output file, CLI summary

---

## Design notes

- **Reuse of parsing helpers**: `_extract_cabinet_type`, `_parse_dimensions`,
  `_parse_color_columns`, `_color_name_from_header` duplicated from
  `catalog_resolver.py` rather than imported (avoids cross-script private
  function dependency). Logic is identical.

- **`base_code` vs `raw_code`**: `raw_code` is exactly as it appears in the
  Excel (e.g. `"3DB30"`). `base_code` is leading-digit-stripped (e.g. `"DB30"`).
  The SKU uses `raw_code` (matching catalog_resolver behavior: `"3DB30-2004"`).

- **Enrichment fields**: `mapped_20_20_codes` and `notes` are both empty/None
  at extraction time. Future tooling populates them. The JSONL is the source
  of truth for enrichment — edits survive re-extraction only if merged.

- **4,594 entries**: far more than the initial "total entries > 200" threshold
  (the milestone doc's conservative estimate). Breakdown by series reflects the
  catalog's actual coverage: series 2000 is largest (Frameless Regular Shaker,
  widest SKU range).
