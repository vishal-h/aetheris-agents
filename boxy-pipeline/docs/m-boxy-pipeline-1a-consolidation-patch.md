# Patch: main.py — consolidate ResolvedItems by code before formatting

**Context.** The pipeline emits one `ResolvedItem` per (drawing, code) pair.
`BLB42FHL` appears on El1, El3, El4, and floor_plan — so the order form
gets 4 rows for the same cabinet, each with qty=1. A reviewer has to manually
consolidate them. This is exactly the work the pipeline should eliminate.

**Evidence from order form review (Joey_Kitchen_V2_vision):**

| Code | Rows | Total qty in form | Correct qty |
|------|------|-------------------|-------------|
| BLB42FHL | 4 (lines 3, 17, 27, 31) | 1+2+1+1=5 | 5 ✓ (but 4 separate rows) |
| USF330 | 3 (lines 13, 16, 24) | 1+1+2=4 | 4 ✓ (but 3 separate rows) |
| DB30 | 2 (lines 4, 32) | 1+1=2 | 1 (floor_plan duplicate) |
| DCW2439R | 2 (lines 5, 30) | 1+1=2 | 1 (vision + floor_plan) |
| W2439-24 | 2 (lines 10, 21) | 1+1=2 | 2 ✓ (El2 + El4, different locations) |
| DA 6698 W | 2 (lines 14, 28) | 1+1=2 | 1 (El3 + floor_plan duplicate) |

The qty totals are sometimes correct (BLB42FHL: 5 cabinets across the project)
but sometimes inflated by floor_plan duplicates (DB30: appears on El1 AND
floor_plan, but it's the same cabinet). The order form should have one row
per code with the correct consolidated qty.

**The fix:** add a `_consolidate` step in `main.py` `_aggregate()` that
groups `ResolvedItem` list by `component.code` before building
`PipelineResult`. Each unique code becomes one consolidated `ResolvedItem`
with qty summed across drawings.

**On WEP429 (vision noise):** this ticket does not fix WEP429. It is a
known stochastic vision artefact — `_token_to_code` passes it (3 letters +
3 digits matches the regex), and there is no reliable way to distinguish
it from a real code without a catalog allowlist. Noted as a known limitation
for the customer demo. The correct long-term fix (post-M2) is to filter
unresolved codes that have no catalog match AND originated from the vision
fallback — but provenance tracking is not yet implemented.

---

## Consolidation rules

Group by `component.code`. For each group:

1. **qty** — sum `qty` across all `ResolvedItem` in the group
2. **catalog_item** — take from the first item with a non-None `catalog_item`
   (all items for the same code have the same catalog_item or None)
3. **unit_price** — take from the first item with `unit_price > 0`
4. **line_total** — recompute: `unit_price × consolidated_qty`
5. **match_confidence** — take the best: `exact` > `fuzzy` > `unresolved`
6. **match_notes** — concatenate non-None notes from all items, deduplicated,
   joined with `"; "`; None if all are None
7. **component.drawing** — set to `"multiple"` if the code appeared on more
   than one drawing; otherwise keep the single drawing name

---

## Change

**File:** `main.py`

Add `_consolidate(resolved: list[ResolvedItem]) -> list[ResolvedItem]`
and call it in `_aggregate` before building `PipelineResult`:

```python
_CONFIDENCE_RANK = {"exact": 0, "fuzzy": 1, "unresolved": 2}


def _consolidate(resolved: list[ResolvedItem]) -> list[ResolvedItem]:
    """Consolidate ResolvedItems by code across drawings.

    Groups items by component.code. For each group, sums qty, picks the
    best catalog_item and match_confidence, merges match_notes, and sets
    component.drawing to "multiple" when the code appeared on >1 drawing.
    """
    from collections import defaultdict
    groups: dict[str, list[ResolvedItem]] = defaultdict(list)
    for item in resolved:
        groups[item.component.code].append(item)

    consolidated = []
    for code, items in groups.items():
        total_qty = sum(i.qty for i in items)
        drawings = {i.component.drawing for i in items}

        # Best catalog_item and unit_price
        best_item = next(
            (i for i in items if i.catalog_item is not None), items[0]
        )
        unit_price = best_item.unit_price

        # Best confidence
        best_confidence = min(
            items, key=lambda i: _CONFIDENCE_RANK.get(i.match_confidence, 99)
        ).match_confidence

        # Merge notes
        notes = list(dict.fromkeys(
            n for i in items if i.match_notes
            for n in [i.match_notes]
        ))
        merged_notes = "; ".join(notes) if notes else None

        # Consolidated component
        consolidated_component = PlanComponent(
            code=code,
            drawing="multiple" if len(drawings) > 1 else next(iter(drawings)),
            qty=total_qty,
            notes=None,
        )

        consolidated.append(ResolvedItem(
            component=consolidated_component,
            catalog_item=best_item.catalog_item,
            qty=total_qty,
            unit_price=unit_price,
            line_total=unit_price * total_qty,
            match_confidence=best_confidence,
            match_notes=merged_notes,
        ))

    return consolidated


def _aggregate(
    resolved: list[ResolvedItem],
    project_name: str,
    catalog_file: str,
) -> PipelineResult:
    consolidated = _consolidate(resolved)
    unresolved_codes = sorted({
        r.component.code
        for r in consolidated
        if r.match_confidence == "unresolved"
    })
    subtotal = sum(r.line_total for r in consolidated)
    source_drawings = sorted({
        d
        for r in resolved      # use original resolved for drawing list
        for d in [r.component.drawing]
    })
    return PipelineResult(
        project_name=project_name,
        resolved=consolidated,
        unresolved_codes=unresolved_codes,
        subtotal=subtotal,
        source_drawings=source_drawings,
        catalog_file=catalog_file,
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )
```

Also import `PlanComponent` at the top of `main.py` if not already imported
(it's needed for `consolidated_component`).

---

## Tests

**File:** `tests/test_pipeline.py` — add unit test for `_consolidate`.

```python
from main import _consolidate
from schema import ResolvedItem, PlanComponent, CatalogItem

def _make_resolved(code, drawing, qty, confidence="unresolved",
                   unit_price=0.0, catalog_item=None, notes=None):
    return ResolvedItem(
        component=PlanComponent(code=code, drawing=drawing, qty=qty, notes=None),
        catalog_item=catalog_item,
        qty=qty,
        unit_price=unit_price,
        line_total=unit_price * qty,
        match_confidence=confidence,
        match_notes=notes,
    )


def test_consolidate_sums_qty_across_drawings():
    """BLB42FHL on El1 (qty=1), El3 (qty=2), El4 (qty=1) → consolidated qty=4."""
    items = [
        _make_resolved("BLB42FHL", "El1", 1),
        _make_resolved("BLB42FHL", "El3", 2),
        _make_resolved("BLB42FHL", "El4", 1),
    ]
    result = _consolidate(items)
    assert len(result) == 1
    assert result[0].qty == 4
    assert result[0].component.drawing == "multiple"


def test_consolidate_single_drawing_keeps_drawing_name():
    """A code on only one drawing keeps that drawing name."""
    items = [_make_resolved("DB30", "El1", 1)]
    result = _consolidate(items)
    assert result[0].component.drawing == "El1"


def test_consolidate_picks_best_confidence():
    """exact beats fuzzy beats unresolved."""
    items = [
        _make_resolved("W2439-24", "El2", 1, confidence="fuzzy"),
        _make_resolved("W2439-24", "El4", 1, confidence="exact"),
    ]
    result = _consolidate(items)
    assert result[0].match_confidence == "exact"


def test_consolidate_recomputes_line_total():
    """line_total = unit_price × consolidated qty."""
    items = [
        _make_resolved("DB21", "El4", 2, confidence="exact", unit_price=1026.4),
    ]
    result = _consolidate(items)
    assert result[0].line_total == pytest.approx(1026.4 * 2)


def test_consolidate_merges_notes():
    """Notes from different drawings are merged, deduplicated."""
    items = [
        _make_resolved("W2439-24", "El2", 1, notes="matched as W2439 after suffix strip"),
        _make_resolved("W2439-24", "El4", 1, notes="matched as W2439 after suffix strip"),
    ]
    result = _consolidate(items)
    # Same note deduplicated
    assert result[0].match_notes == "matched as W2439 after suffix strip"


def test_consolidate_preserves_distinct_codes():
    """Different codes are not merged."""
    items = [
        _make_resolved("DB30",     "El1", 1),
        _make_resolved("BLB42FHL", "El1", 1),
    ]
    result = _consolidate(items)
    assert len(result) == 2
```

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_pipeline.py -v

# Full pipeline — verify consolidated output
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/catalog.jsonl \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2_consolidated \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"

# Verify consolidation
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('output/Joey_Kitchen_V2_consolidated_order_form.xlsx')
ws = wb.active
items = {}
for row in ws.iter_rows(min_row=12, max_row=50, values_only=True):
    item, color, qty = row[1], row[2], row[3]
    if item and item not in ('Assembly Fee','Modification Fee','Delivery Fee'):
        if item in items:
            print(f'DUPLICATE: {item} appears twice in form')
        items[item] = qty

print(f'Distinct codes in form: {len(items)}')
# BLB42FHL must appear exactly once
assert items.get('BLB42FHL') is not None, 'BLB42FHL missing'
blb_qty = items['BLB42FHL']
print(f'BLB42FHL qty={blb_qty} (expected 5 = 1+2+1+1 across drawings)')
assert blb_qty == 5, f'Expected qty=5, got {blb_qty}'

usf_qty = items.get('USF330', 0)
print(f'USF330 qty={usf_qty} (expected 4 = 1+1+2 across drawings)')

print('✓ Consolidation correct — one row per code')
"
```

Expected: no duplicate codes in form, `BLB42FHL` qty=5, `USF330` qty=4,
pipeline summary shows fewer total items than before (was 33, now ~23).

---

## Claude-code prompt

> Implement cross-drawing consolidation in `main.py` per
> `docs/m-boxy-pipeline-1a-consolidation-patch.md §Change`.
>
> Add `_CONFIDENCE_RANK` and `_consolidate()` per §Change.
> Update `_aggregate()` to call `_consolidate(resolved)` before building
> `PipelineResult`. Ensure `PlanComponent` is imported in `main.py`.
>
> Add the six unit tests to `tests/test_pipeline.py` per §Tests.
> Add `import pytest` to `test_pipeline.py` if not already present.
> Do not modify any existing test.
>
> Do not modify any other file.
>
> Run the done-check from §Done-check — include the consolidation
> verification output (distinct codes, BLB42FHL qty, USF330 qty) in
> your review packet.
