# Review — m-boxy-pipeline t1 — round 2

## Summary

| # | Severity | Status |
|---|---|---|
| 1 | non-blocking | deferred — `pandas>=2.2.0` tighter floor; backlog before t2 merges |
| 3 | non-blocking | fixed ✓ — `pytest_collection_modifyitems` auto-skip hook added to `conftest.py` |
| 4 | non-blocking | fixed ✓ — stale `import pdfplumber` removed from deduplication test |
| 6 | **blocking** | fixed ✓ — three noise codes eliminated from floor plan output |

---

## Finding 1 (deferred) — pandas version floor

`requirements.txt` ships `pandas>=2.0.0`. Reviewer suggestion: tighten to `>=2.2.0`
(first release with full Python 3.12 support and stable `read_excel` behaviour).
`pandas>=3.0.2` (original milestone spec) is not yet published to PyPI. Deferred —
acceptable as-is; address before t2 merges since t2 uses the same `requirements.txt`.

## Finding 3 (fixed) — `conftest.py` missing `pytest_collection_modifyitems`

The established convention (from `agent-creation-guide.md`) centralises integration
test skipping in `conftest.py` via `pytest_collection_modifyitems`, rather than
inline `pytest.skip()` calls scattered across test functions. Fixed: `conftest.py`
now detects missing sample files once and auto-skips all `@pytest.mark.integration`
tests.

## Finding 4 (fixed) — stale `import pdfplumber` in test body

`test_deduplication_increments_qty_same_drawing` contained `import pdfplumber`
inside the test body but never used it. Removed.

## Finding 6 (fixed) — three noise codes in floor plan output

**Symptoms:** `B42FHL`, `EEP2493`, `F933` appeared in the extracted output with
`drawing=floor_plan`. All are garbled tokens from the floor plan page, not real
cabinet codes.

**Root cause:** The floor plan is a dense 2D spatial diagram where the PDF text
stream interleaves characters from nearby labels, producing partial tokens. The
elevation pages (`El1`–`El4`) extract cleanly because cabinet codes are listed
linearly in elevation views.

**Fix — two-part:**

1. **Regex tightening** (`_CABINET_RE`): split the single-letter prefix pattern
   into its own alternative requiring *exactly* 4 digits — `[A-Z][0-9]{4}`. This
   matches real wall cabinet codes (`W2739`) but rejects `F933` (1 letter + 3
   digits) and `B42FHL` (1 letter + fewer than 4 digits before the trailing
   letters).

2. **Post-extraction fragment filter** (`_filter_floor_plan_fragments`): after
   deduplication, suppress any `floor_plan` code that is a *proper string suffix*
   of a code found in the elevations. This catches `EEP2493` (proper suffix of
   `FSEP2493`). Exact matches across drawings are preserved (`DA 6698 W` appears
   on both `El3` and `floor_plan` and is kept on both).

**Tests added:**
- `F933`, `B42FHL` added to `test_cabinet_re_rejects_non_codes` parametrize.
- Three unit tests for `_filter_floor_plan_fragments`: suppresses suffix fragments,
  keeps exact cross-drawing matches, suppresses `EEP2493` as `FSEP2493` fragment.
- `test_extract_pdfs_required_codes` now asserts none of `{B42FHL, EEP2493, F933}`
  appear in the final output.

---

## Full code list (post-fix)

```
B42FHL               floor_plan   qty=1   ← REMOVED (fragment of BLB42FHL)
BLB42FHL             El1          qty=1
BLB42FHL             El3          qty=2
BLB42FHL             El4          qty=1
BPBC12               El3          qty=1
BPBC9                El3          qty=1
CKT36                El3          qty=1
DA 6698 W            El3          qty=1
DA 6698 W            floor_plan   qty=1
DB21                 El4          qty=2
DB30                 El1          qty=1
EEP2493              floor_plan   qty=1   ← REMOVED (fragment of FSEP2493)
F933                 floor_plan   qty=1   ← REMOVED (noise)
FSEP2493             El2          qty=1
G 7186 SCVi          El2          qty=1
KFNF 9959 iDE        El2          qty=1
OVB36                El3          qty=1
SB42                 El4          qty=1
SUW2418-24           El4          qty=1
USF330               El2          qty=1
USF330               El3          qty=1
USF330               El4          qty=2
USF357               El2          qty=2
USF357               El4          qty=1
W2424-24             El2          qty=1
W2439-24             El2          qty=1
W2439-24             El4          qty=1
W2739                El1          qty=1
WEP42                El1          qty=1
WP3612-24HK          El2          qty=1
```

Post-fix distinct code count: **20** (down from 23; 3 noise codes removed).
All 5 required codes present: `DB30` ✓ `BLB42FHL` ✓ `W2739` ✓ `SB42` ✓ `USF330` ✓
