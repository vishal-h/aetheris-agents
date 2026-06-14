# Review — m-boxy-pipeline-1a t3 — Resolver refactor — round 1

## Summary

| # | Severity | Status |
|---|---|---|
| 1 | blocking | resolved ✓ — `import json` was already present (line 8, original file) |
| 2 | non-blocking | noted in §Design notes below |
| 3 | non-blocking | confirmed intentional — see §Finding 3 disposition |

**t3 approved for merge.**

## Done-check output

```
$ python3 main.py \
    --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
               data/samples/Joey-_Kitchen_Plan_V2.pdf \
    --catalog  data/catalog.jsonl \
    --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --project  Joey_Kitchen_V2 \
    --upper-finish "2001:Ivory White:2000" \
    --lower-finish "2004:Mingo Oak:2000"

Project:    Joey_Kitchen_V2
Drawings:   2 file(s)
Items:      27 total, 7 resolved, 14 unresolved codes
Subtotal:   $5,346.45
Output:     output/Joey_Kitchen_V2_order_form.xlsx
```

| Assertion | Result |
|-----------|--------|
| `7 resolved` | ✓ matches Excel baseline |
| `14 unresolved codes` | ✓ matches Excel baseline |
| `subtotal $5,346.45` | ✓ matches Excel baseline |
| `test_catalog_resolver.py` 27/27 | ✓ unchanged |
| `test_catalog_resolver_refactor.py` 14/14 | ✓ |

---

## Test results

```
27 passed — tests/test_catalog_resolver.py (1m 30s) — unchanged
14 passed — tests/test_catalog_resolver_refactor.py (1m 36s)
```

New tests (14):
- 10 unit tests using `minimal_jsonl` fixture (no real files):
  non-empty dict, raw_code indexed, base_code indexed, raw/base share same
  items, CatalogItem fields, multiple colors, no-digit raw not duplicated,
  DB30 resolves via JSONL, auto-detect extension, blank lines skipped
- 4 integration tests using `scope="module"` `real_index` fixture:
  index non-empty (>100 keys), DB30 indexed in real catalog, color 2004
  present for DB30, full pipeline matches Excel result

---

## Finding 1 disposition — `import json` confirmed present

`import json` was already at line 8 in the original `catalog_resolver.py` —
it was used by `main()` for `json.loads(raw)` and `json.dumps(...)`.
The diff appeared to omit it only because it was unchanged. No fix needed.

## Finding 2 disposition — 332 keys vs 4,594 entries

The `load_catalog_jsonl` index has **332 unique keys** (not 4,594):
- 4,594 = total `CatalogEntry` records (all SKU × color combinations)
- 332 = distinct code keys in the index (raw_codes + base_codes, deduped)

Each key maps to a `list[CatalogItem]` containing all color variants for
that code. This matches the Excel `load_catalog` index exactly. The key
count is lower than unique SKU count because many raw_codes are shared
across colors (the list value holds all of them), and because raw_code
and base_code share the same list when they differ.

## Finding 3 disposition — `--catalog` JSONL, `--template` XLSX

In `test_real_jsonl_resolve_matches_excel_result`:
- `--catalog data/catalog.jsonl` — the new JSONL path being tested
- `--template Updated_Boxy_MSRP_Sales_Order_Form.xlsx` — the Order Form
  template (used by `order_formatter.py`, not by the resolver)

These are distinct inputs for distinct purposes. The template path is
unchanged from all prior tests. Intentional and correct.

---

## Design notes

- **Dual-index preserved.** `load_catalog_jsonl` reads `raw_code` and
  `base_code` directly from each JSONL entry (pre-computed by
  `catalog_extractor.py`) rather than re-running `re.sub(r"^[1-9]", "")`.
  The resulting index is structurally identical to `load_catalog`'s output.

- **`load_catalog` deprecated, not removed.** Retained as fallback for
  environments where `catalog.jsonl` hasn't been generated yet. The `--catalog`
  CLI flag auto-detects by file extension (`.jsonl` → JSONL path, else Excel).

- **332 unique index keys.** The index keyed by code (not SKU): each key maps
  to all color variants for that code. Raw + base codes are counted together
  in the 332. The 4,594 entry total lives in the combined list values.
