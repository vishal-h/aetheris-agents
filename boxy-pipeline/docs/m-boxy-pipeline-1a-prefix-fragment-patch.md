# Patch: plan_extractor — suppress prefix fragments in _filter_floor_plan_fragments

**Context.** `_filter_floor_plan_fragments` suppresses floor_plan codes that
are garbled fragments of longer elevation codes. It handles two patterns:

1. **Proper suffix** — floor_plan code is a trailing substring of an elevation
   code. e.g. `B42FHL` suppressed because `BLB42FHL`.endswith(`B42FHL`) ✓
2. **One-char-shifted suffix** — drop first char of floor_plan code, check if
   result is a suffix of a longer elevation code. e.g. `EEP2493` suppressed.

**The gap — prefix fragments not handled.**
`BPBC1` is a prefix of `BPBC12` (elevation, El3), not a suffix. The filter
checks `other.endswith(code)` — `"BPBC12".endswith("BPBC1")` is `False`
because `BPBC12` ends with `2`, not `BPBC1`. So `BPBC1` passes through.

**The fix:** add Pattern 3 — suppress floor_plan code if it is a proper prefix
of a strictly longer elevation code.

---

## Change

**File:** `scripts/plan_extractor.py`

In `_filter_floor_plan_fragments`, add Pattern 3 after Pattern 2:

```python
        # Pattern 3: proper prefix of a longer elevation code
        # e.g. BPBC1 suppressed because BPBC12.startswith(BPBC1) and len > len
        if any(len(other) > len(code) and other.startswith(code)
               for other in elevation_codes):
            continue
```

Also update the docstring to document Pattern 3:

```python
    """Suppress floor_plan codes that are garbled fragments of elevation codes.
    The floor plan is a dense spatial diagram where overlapping PDF text streams
    produce partial tokens. Three fragment patterns are detected:
    1. Proper suffix: floor_plan code is a trailing substring of a longer
       elevation code (e.g. B42FHL ← BLB42FHL).
    2. One-char-shifted suffix: dropping the first character of the floor_plan
       code gives a suffix of a strictly longer elevation code (e.g. EEP2493:
       drop E → EP2493, and FSEP2493 ends with EP2493).
    3. Proper prefix: floor_plan code is a leading substring of a longer
       elevation code (e.g. BPBC1 ← BPBC12).
    Exact same-length cross-drawing matches (e.g. DA 6698 W on both El3 and
    floor_plan) are never suppressed.
    """
```

---

## Tests

**File:** `tests/test_plan_extractor.py`

Add one unit test alongside the existing `_filter_floor_plan_fragments` tests:

```python
def test_filter_suppresses_prefix_fragment():
    """BPBC1 on floor_plan is suppressed when BPBC12 is on an elevation."""
    components = [
        PlanComponent(code="BPBC12", drawing="El3", qty=1, notes=None),
        PlanComponent(code="BPBC1",  drawing="floor_plan", qty=1, notes=None),
        PlanComponent(code="DB30",   drawing="El1", qty=1, notes=None),
    ]
    result = _filter_floor_plan_fragments(components)
    codes = {c.code for c in result}
    assert "BPBC12" in codes,  "BPBC12 (elevation) must be kept"
    assert "BPBC1"  not in codes, "BPBC1 (prefix fragment) must be suppressed"
    assert "DB30"   in codes,  "DB30 (elevation) must be kept"
```

Also add a guard test to confirm Pattern 3 doesn't over-suppress:

```python
def test_filter_does_not_suppress_prefix_on_elevation():
    """A code that is a prefix of another must NOT be suppressed if it's on an elevation."""
    components = [
        PlanComponent(code="BPBC12", drawing="El3", qty=1, notes=None),
        PlanComponent(code="BPBC1",  drawing="El3", qty=1, notes=None),  # elevation, not floor_plan
    ]
    result = _filter_floor_plan_fragments(components)
    codes = {c.code for c in result}
    assert "BPBC12" in codes
    assert "BPBC1"  in codes, "BPBC1 on elevation must NOT be suppressed"
```

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v

# Verify BPBC1 no longer appears in output
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
codes = {r['code'] for r in data}
assert 'BPBC1'  not in codes, 'BPBC1 (prefix fragment) must be suppressed'
assert 'BPBC12' in codes,     'BPBC12 (real code) must be kept'
assert 'BPBC9'  in codes,     'BPBC9 (real code) must be kept'
required = {'DB30', 'BLB42FHL', 'W2739', 'SB42', 'USF330', 'DCW2439R'}
missing = required - codes
assert not missing, f'Required codes missing: {missing}'
print(f'✓ BPBC1 suppressed, BPBC12 and BPBC9 kept')
print(f'Total: {len(codes)} distinct codes')
"
```

Expected: `BPBC1` absent, `BPBC12` and `BPBC9` present, all required codes
present, test count increases by 2.

---

## Claude-code prompt

> Apply the prefix-fragment suppression patch to `scripts/plan_extractor.py`
> per `docs/m-boxy-pipeline-1a-prefix-fragment-patch.md §Change`.
>
> Two changes only:
> 1. Add Pattern 3 to `_filter_floor_plan_fragments` after Pattern 2.
> 2. Update the docstring to document Pattern 3.
> The exact code is in §Change — copy it verbatim.
>
> Add the two new unit tests to `tests/test_plan_extractor.py` per §Tests.
> Do not modify any existing test.
>
> Do not modify any other file.
>
> Run the done-check from §Done-check and include actual output in your
> review packet.
