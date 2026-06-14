# Patch: plan_extractor — tighten vision prompt to reduce floor plan noise

**Context.** The vision fallback is producing noise from the floor plan page.
After the 120pt padding patch, the floor plan vision pass returns codes
including hallucinations and garbled reads:

```
floor_plan vision results (observed):
  BPBC1     ← fragment of BPBC12 (real code is 4+ chars)
  CRT30     ← hallucination (no such Boxy code; probably misread of CKT36)
  DB2USF    ← garbled blend
  DA6698W   ← duplicate of 'DA 6698 W' without spaces
  WEP429    ← garbled fragment
```

`_token_to_code` filters `BPBC1` (too short after cleaning) but passes
`CRT30`, `DA6698W`, `WEP429` — they match the cabinet regex but are not
real codes.

**Root cause.** The vision prompt gives examples but doesn't constrain the
format tightly enough. The model reads partial overlapping labels and returns
fragments as codes. It also doesn't know to read overlapping labels as
separate items.

**The fix:** tighten the system prompt in `_extract_codes_via_vision` with:
1. Explicit format constraint (letter prefix + digits + optional letter suffix)
2. Instruction to read overlapping labels individually
3. Instruction to ignore appliance model numbers (they have spaces)
4. Minimum length constraint (≥4 characters)

---

## Change

**File:** `scripts/plan_extractor.py`

In `_extract_codes_via_vision`, replace the `"text"` content with:

```python
                {
                    "type": "text",
                    "text": (
                        "This is a cropped region of a 20-20 kitchen design drawing "
                        "where cabinet labels overlap. Extract all cabinet component "
                        "codes visible in the image.\n\n"
                        "Cabinet codes follow this strict format:\n"
                        "- 1–4 uppercase letters, followed by\n"
                        "- 2–4 digits, optionally followed by\n"
                        "- 0–4 uppercase letters (e.g. L, R, FHL)\n"
                        "- Minimum 4 characters total\n"
                        "- Examples: W0939L, W0939R, DCW2439R, WEP42, "
                        "BLB42FHL, DB30, USF330, W2739\n\n"
                        "Rules:\n"
                        "- If labels overlap, read each one separately\n"
                        "- Do NOT include dimension numbers (e.g. 39\", 9\")\n"
                        "- Do NOT include appliance model numbers with spaces "
                        "(e.g. DA 6698 W, G 7186 SCVi)\n"
                        "- Do NOT include partial codes or fragments\n"
                        "- Do NOT include annotation text (Filler, BEP, etc.)\n\n"
                        "Return ONLY a JSON array of strings, one code per element. "
                        "Example: [\"W0939L\", \"W0939R\", \"DCW2439R\"]. "
                        "No explanation — only the JSON array."
                    ),
                },
```

---

## Tests

No new unit tests needed — the prompt is a string constant, not logic.
The existing integration test `test_vision_fallback_fires_and_cleans_garbled_tokens`
covers the end-to-end behaviour.

Update the integration test's assertion comment to note that `CRT30` and
`WEP429` must not appear in output (they should now be absent with the
tighter prompt, and `_token_to_code` is a backstop):

```python
    # Noise from vision hallucinations must not appear
    # (_token_to_code is the backstop; tighter prompt reduces upstream noise)
    for noise in ["CRT30", "WEP429", "DB2USF", "BPBC1"]:
        assert noise not in codes, f"Vision noise {noise!r} must not appear in output"
```

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v

# Run extraction and check for noise codes
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
codes = {r['code'] for r in data}

noise_codes = {'CRT30', 'WEP429', 'DB2USF', 'BPBC1', 'DA6698W'}
found_noise = noise_codes & codes
if found_noise:
    print(f'✗ Noise codes still present: {found_noise}')
else:
    print('✓ No noise codes in output')

required = {'DB30', 'BLB42FHL', 'W2739', 'SB42', 'USF330', 'DCW2439R'}
missing = required - codes
if missing:
    print(f'✗ Required codes missing: {missing}')
else:
    print('✓ All required codes present')

print(f'Total: {len(codes)} distinct codes')
for r in sorted(data, key=lambda x: (x['drawing'], x['code'])):
    print(f\"  {r['code']:<25} {r['drawing']:<12} qty={r['qty']}\")
"
```

Expected: no noise codes, all required codes present including `DCW2439R`.
Full code list in review packet so reviewer can verify no regressions.

**Note on W939L/W939R:** these may or may not be recovered depending on
whether the vision model can read them individually from the overlapping
region. Include the full list — do not assert their presence in the
done-check. Their resolution is handled by the zero-padding patch
(`m-boxy-pipeline-1a-zero-padding-patch.md`).

---

## Claude-code prompt

> Update the vision prompt in `scripts/plan_extractor.py` per
> `docs/m-boxy-pipeline-1a-vision-prompt-patch.md §Change`.
>
> One change only: replace the `"text"` content string in
> `_extract_codes_via_vision` with the tighter prompt from §Change.
> The exact string is specified there — copy it verbatim.
>
> Update `test_vision_fallback_fires_and_cleans_garbled_tokens` in
> `tests/test_plan_extractor.py` to add the noise assertion block
> from §Tests. Do not modify any other test.
>
> Do not modify any other file.
>
> Run the done-check from §Done-check and include the full code list
> in your review packet.
