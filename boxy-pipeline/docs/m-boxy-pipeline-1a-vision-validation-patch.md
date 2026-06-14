# Patch: plan_extractor — validate vision codes + increase crop padding to 120pt

**Context.** Two issues found after the vision fallback landed:

**Issue 1 — No validation on vision-returned codes.**
`codes.extend(vision_codes)` bypasses `_token_to_code`, allowing noise like
`F33` (3 chars, too short) to enter the output. Confirmed from live run:
```
Vision returned: ['DCW2439R', 'F33', 'W2439']
```
- `DCW2439R` — valid, should be kept ✓
- `F33` — noise, should be filtered ✗
- `W2439` — valid but duplicate; dedup handles it, still worth filtering

**Issue 2 — Crop padding too small, missing labels below the garbled region.**
The garbled token bbox is at `top=272.5, bottom=286.2`. With 60pt padding the
crop bottom is at ~346pt. Visual inspection of `output/debug_crop.png` confirms
that `W939L` and `W939R` labels are visually present ~60–80pt *below* the crop
bottom — they are cut off. Increasing padding from 60pt to 120pt captures them.

**Both fixes in one patch.**

---

## Changes

**File:** `scripts/plan_extractor.py` — two changes.

### Change 1 — Increase crop padding from 60pt to 120pt

In `_extract_codes_via_vision`, change the `_union_bbox` call:

```python
# BEFORE
bbox = _union_bbox(garbled_words, page_width, page_height, padding=60.0)

# AFTER
# 120pt padding (up from 60): the garbled region on El1 has overlapping labels
# visually present ~80pt below the token bbox. 60pt padding cropped them out.
# 120pt captures the full label neighbourhood in all directions.
bbox = _union_bbox(garbled_words, page_width, page_height, padding=120.0)
```

### Change 2 — Validate vision codes through `_token_to_code`

Replace:

```python
            codes.extend(vision_codes)
```

With:

```python
            # Validate vision codes through the same filter as text-layer tokens
            for raw in vision_codes:
                code = _token_to_code(raw)
                if code:
                    codes.append(code)
```

---

## Tests

**File:** `tests/test_plan_extractor.py`

Add one unit test (no API call, no sample files needed):

```python
def test_vision_codes_filtered_through_token_to_code(monkeypatch):
    """Vision-returned codes must pass _token_to_code validation.

    Noise like 'F33' (too short) must be dropped.
    Valid codes like 'DCW2439R' must be kept.
    """
    import plan_extractor

    # Patch _extract_codes_via_vision to return a mix of valid and noise codes
    monkeypatch.setattr(
        plan_extractor,
        "_extract_codes_via_vision",
        lambda **kwargs: ["DCW2439R", "F33", "W2439"],
    )

    # Also patch _is_garbled to force the vision path
    original_is_garbled = plan_extractor._is_garbled
    monkeypatch.setattr(
        plan_extractor,
        "_is_garbled",
        lambda token: token == "FAKEGARBLD12345",
    )

    import pdfplumber
    from pathlib import Path

    # Use real sample PDF — vision is mocked so no API call is made
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")

    # Inject a fake garbled word into the word list by monkeypatching extract_words
    original_extract_words = None

    class FakePage:
        def __init__(self, real_page):
            self._real = real_page
            self.width = real_page.width
            self.height = real_page.height

        def extract_text(self):
            return self._real.extract_text()

        def extract_words(self, **kwargs):
            words = self._real.extract_words(**kwargs)
            # Inject a fake garbled word so vision path fires
            words.append({
                'text': 'FAKEGARBLD12345',
                'x0': 100.0, 'top': 200.0,
                'x1': 200.0, 'bottom': 215.0,
            })
            return words

    with pdfplumber.open(ELEVATION_PDF) as pdf:
        fake_page = FakePage(pdf.pages[0])
        label, codes = plan_extractor._extract_page_codes(
            fake_page,
            pdf_path=ELEVATION_PDF,
            page_index=0,
        )

    assert "DCW2439R" in codes, "Valid vision code DCW2439R must be kept"
    assert "F33" not in codes,  "Noise code F33 must be filtered out"
```

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v

# Verify DCW2439R and W939L/W939R now appear; F33 does not
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
codes = {r['code'] for r in data}
assert 'DCW2439R' in codes, 'DCW2439R must be present (recovered by vision)'
assert 'F33' not in codes,  'F33 must be filtered out (vision noise)'
required = {'DB30', 'BLB42FHL', 'W2739', 'SB42', 'USF330'}
missing = required - codes
assert not missing, f'Required codes missing: {missing}'
print(f\"{'✓' if 'DCW2439R' in codes else '✗'} DCW2439R present (vision recovery)\")
print(f\"{'✓' if 'F33' not in codes else '✗'} F33 absent (noise filtered)\")
for code in ['W939L', 'W939R', 'W0939L', 'W0939R']:
    print(f\"{'✓' if code in codes else '-'} {code} {'recovered by vision' if code in codes else 'not in drawing'}\")
print(f'Total: {len(codes)} distinct codes')
"
```

Expected: `DCW2439R` present, `F33` absent, all 5 required codes present.
`W939L`/`W939R` (or `W0939L`/`W0939R`) present if visually legible in the
wider crop — this is the key assertion for the padding fix. If still absent,
include the new `debug_crop.png` in the review packet.

---

## Claude-code prompt

> Apply two changes to `scripts/plan_extractor.py` per
> `docs/m-boxy-pipeline-1a-vision-validation-patch.md`.
>
> Change 1 — in `_extract_codes_via_vision`, change the `_union_bbox` call
> from `padding=60.0` to `padding=120.0`. Add the comment from §Change 1.
>
> Change 2 — in `_extract_page_codes`, replace `codes.extend(vision_codes)`
> with a loop that runs each vision code through `_token_to_code` and only
> appends codes that pass. The exact replacement is in §Change 2 above.
>
> Add `test_vision_codes_filtered_through_token_to_code` to
> `tests/test_plan_extractor.py` per §Tests above.
>
> Do not modify any other file. Do not change `schema.py`, `requirements.txt`,
> or any other script.
>
> After implementing, save the new crop to `output/debug_crop.png` using the
> same technique as before and confirm visually (or via the verification
> snippet) whether `W939L`/`W939R` are now in the crop and recovered.
>
> Run the done-check from §Done-check and include actual output — including
> the W939L/W939R lines — in your review packet.
