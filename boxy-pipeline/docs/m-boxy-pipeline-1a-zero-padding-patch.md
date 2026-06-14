# Patch: catalog_resolver — zero-padding normalisation for W939 → W0939

**Context.** 20-20 design drawings label wall cabinets without a leading zero
in the numeric part: `W939L`, `W939R`. The Boxy catalog stores them as `W0939`
(`W0939-2001`, $105.46 each). The current resolver strips leading *digits*
(e.g. `3DB30` → `DB30`) but does not handle leading *zeros within the numeric
part* (e.g. `W939` → `W0939`).

**Confirmed from SO86708:**
- SO line item: `W0939-2001`, special_request: `"W0939L and W0939R"`
- Drawing label: `W939R` (no leading zero in numeric part)

**Result:** even if vision recovers `W939R` from the overlapping crop region,
the resolver flags it as `unresolved` because `W939` has no match in the
catalog index (which has `W0939` and `W939` stripped from `W0939` would need
a zero-pad step).

**The fix:** in `_resolve_component`, after the existing normalisation steps
(direct lookup → strip leading digit → strip dash suffix), add a zero-padding
step: if the code has a letter prefix followed by 3 digits, try padding to
4 digits. `W939` → `W0939`, `W939L` → `W0939L`.

---

## Change

**File:** `scripts/catalog_resolver.py`

In `_resolve_component`, add a zero-padding normalisation step after the
existing dash-suffix strip step. Insert between step 3 and the unresolved
return:

```python
    # 4. Zero-pad 3-digit numeric part → 4-digit (e.g. W939 → W0939, W939L → W0939L)
    # 20-20 drawings omit the leading zero that Boxy catalog uses.
    zero_padded = re.sub(r'^([A-Z]{1,4})(\d{3})([A-Z]{0,4})$', r'\g<1>0\g<2>\g<3>', code)
    if zero_padded != code:
        if zero_padded in index:
            matched_code = zero_padded
            catalog_items = index[zero_padded]
            match_confidence = "fuzzy"
            match_notes = f"matched as {zero_padded} after zero-padding numeric part"
        else:
            # Also try stripping trailing L/R suffix before zero-padding
            # e.g. W939L → W939 → W0939
            base = re.sub(r'[LR]$', '', zero_padded)
            if base != zero_padded and base in index:
                matched_code = base
                catalog_items = index[base]
                match_confidence = "fuzzy"
                match_notes = f"matched as {base} after zero-padding and suffix strip (was {code})"
```

The regex `^([A-Z]{1,4})(\d{3})([A-Z]{0,4})$` matches codes with exactly
3 digits (e.g. `W939`, `W939L`, `W939R`) and pads to 4 digits (`W0939`,
`W0939L`, `W0939R`). Codes already 4 digits (`W2739`, `DB30`) are unaffected.

---

## Tests

**File:** `tests/test_catalog_resolver.py` — add to existing unit tests.

```python
def test_resolve_zero_pads_three_digit_code():
    """W939 → W0939 via zero-padding normalisation → fuzzy match."""
    item = _make_wall_item(
        sku="W0939-2001",
        description='Wall Cabinet, 9"W × 39"H × 12"D, 1 Door',
        width_in=9.0,
    )
    # Index under W0939 (as catalog stores it)
    index = {"W0939": [item]}
    comp = PlanComponent(code="W939", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "fuzzy"
    assert r.catalog_item is not None
    assert r.catalog_item.sku == "W0939-2001"
    assert r.match_notes is not None
    assert "zero-padding" in r.match_notes


def test_resolve_zero_pads_with_lr_suffix():
    """W939L → W939 → W0939 via zero-padding + suffix strip → fuzzy match."""
    item = _make_wall_item(
        sku="W0939-2001",
        description='Wall Cabinet, 9"W × 39"H × 12"D, 1 Door',
        width_in=9.0,
    )
    index = {"W0939": [item]}
    comp = PlanComponent(code="W939L", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "fuzzy"
    assert r.catalog_item is not None


def test_resolve_four_digit_code_not_zero_padded():
    """W2739 (4 digits) must not be zero-padded to W02739."""
    item = _make_wall_item(sku="W2739-2001", description='Wall Cabinet, 27"W × 39"H × 12"D')
    index = {"W2739": [item]}
    comp = PlanComponent(code="W2739", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "exact"
    assert r.catalog_item.sku == "W2739-2001"
```

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_catalog_resolver.py -v

# Full pipeline — W939 codes (if extracted) should now resolve rather than unresolved
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/catalog.jsonl \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2_zeroPad \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"

# Verify W939 resolves correctly when present in extraction
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from catalog_resolver import load_catalog_jsonl, resolve, parse_finish
from schema import PlanComponent
from pathlib import Path

catalog = load_catalog_jsonl(Path('data/catalog.jsonl'))
upper = parse_finish('2001:Ivory White:2000')
lower = parse_finish('2004:Mingo Oak:2000')

test_codes = ['W939', 'W939L', 'W939R', 'W2739', 'DB30']
results = resolve(
    [PlanComponent(code=c, drawing='El1', qty=1, notes=None) for c in test_codes],
    Path('data/catalog.jsonl'), upper, lower
)
for r in results:
    print(f\"{r.component.code:<12} → {r.match_confidence:<10} {r.catalog_item.sku if r.catalog_item else 'unresolved'}\")
"
```

Expected: `W939`, `W939L`, `W939R` all resolve as `fuzzy` to `W0939-2001`.
`W2739` resolves as `exact`. `DB30` resolves as `exact`.

---

## Claude-code prompt

> Implement zero-padding normalisation in `scripts/catalog_resolver.py` per
> `docs/m-boxy-pipeline-1a-zero-padding-patch.md §Change`.
>
> Add step 4 to `_resolve_component` after the existing dash-suffix strip step.
> The regex and logic are specified in §Change — read that section, do not
> restate it here.
>
> Add the three new unit tests to `tests/test_catalog_resolver.py` per §Tests.
> Do not modify any existing test.
>
> Do not modify any other file.
>
> Run the done-check from §Done-check — include the `W939`/`W939L`/`W939R`
> resolution spot-check output in your review packet.
