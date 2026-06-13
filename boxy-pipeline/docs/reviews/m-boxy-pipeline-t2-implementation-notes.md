# Implementation notes — m-boxy-pipeline t2 — catalog resolver

## Dual-index strategy

The Boxy MSRP catalog uses item codes like `3DB30` (3-drawer base, 30") and
`2DB30` (2-drawer base, 30"), but 20-20 design plans use the stripped form
`DB30`. The catalog never contains `DB30` as a raw item code.

To resolve `DB30` as `match_confidence: "exact"`, `load_catalog` builds two
index entries per catalog code that starts with a leading digit:

- `"3DB30"` → `[CatalogItem(...)]`  (raw code)
- `"DB30"`  → `[CatalogItem(...)]`  (normalized: leading digit stripped)

`_resolve_component` checks `if code in index` — plan code `DB30` hits the
normalized key immediately, so `match_confidence = "exact"`. The SKU is then
built as `f"{matched_code}-{color_code}"` = `"DB30-2004"` (using the plan
code, not the raw catalog code), matching the milestone done-check expectation.

Codes with a dash suffix in 20-20 (e.g. `W2439-24`, where `-24` encodes the
depth in inches) fall through to a second path: `re.sub(r"-\d{2}[A-Z0-9]*$", "", code)` strips the suffix, and the result (`W2439`) is looked up. These
resolve as `"fuzzy"`.

## `_is_upper` finish routing logic

Finish rules are project-specific and passed as CLI flags:
```
--upper-finish "2001:Ivory White:2000"
--lower-finish "2004:Mingo Oak:2000"
```

Cabinet classification is derived from the catalog description. The first
comma-delimited segment is the cabinet type (e.g. `"Wall Cabinet"`,
`"Base Cabinet"`, `"Sink Base Cabinet"`). `_is_upper` returns
`"Wall" in cabinet_type` — wall cabinets get the upper finish, all others
get the lower finish.

This heuristic works for all Boxy catalog types encountered. If a new cabinet
type is added that contains "Wall" but is a lower cabinet, the logic would
need updating.

The finish spec also carries a preferred series (`"2000"`). When multiple
series are found for a given normalized code, `_resolve_component` prefers
`series == preferred_series`, then falls back to any item with the matching
color code.

## Column index discrepancy

The milestone doc describes the Price List layout as "col 2 = item code, col 3 = description" — this is 1-indexed counting from the `NO.` column. In 0-indexed
pandas terms (which is what the implementation uses), the actual positions are:

| pandas col | content |
|-----------|---------|
| 0 | empty / branding |
| 1 | series branding text |
| 2 | `NO.` |
| 3 | `Image` |
| 4 | `Item` (item code) |
| 5 | `Description` |
| 6+ | MSRP per color |

The implementation reads `row.iloc[4]` for item code and `row.iloc[5]` for
description. Category separator rows are detected by `"\n" in raw_code` (their
item cell contains a multiline label like `WALL CABINET\n39" Height`).

Color columns are parsed from the header row (row index 1) by extracting the
first line of each cell, stripping leading `*` markers (used for "coming soon"
colors), and matching against `r"\d{4}"`. This correctly picks up `2001`
through `2007` and the series-specific codes in other price lists (e.g. `1001`
in the 1000 Price List).

## Per-drawing resolution (finding 3)

`t1` emits one `PlanComponent` per `(drawing, code)` pair. The resolver
processes each component independently, so codes that appear on multiple
drawings emit multiple `ResolvedItem` records. `DA 6698 W` (dishwasher)
appears on both `El3` and `floor_plan` → two separate `unresolved` records
in the t2 output. `t3` (order formatter) will receive both and should emit
both as separate line items.
