# Patch: plan_extractor — full-page vision instead of crop

**Context.** The vision fallback currently renders a padded crop of the
garbled token bounding box and sends it to the Claude vision API. Three-run
experiment (vision_experiment.py) showed:

- **Crop (42KB):** 0/3 runs produced valid JSON — the model attempted to
  reason mid-response ("Wait, let me re-examine...") and broke out of JSON
  format. Usable codes returned: 0.
- **Full page at 1.5x (100KB):** 3/3 runs returned valid JSON.
  `DCW2439R` recovered every time. `F33` noise correctly filtered by
  `_token_to_code`. W939L/W939R not recovered by either approach —
  confirmed absent from rendered image at any scale.

**Decision:** switch to full page, remove crop logic entirely.

**Why full page wins:** the crop sends a dense overlapping blob with no
spatial context. The full page gives the model the surrounding cabinet boxes,
dimension lines, and other readable labels — enough context to identify
individual codes even where labels overlap.

---

## Changes

**File:** `scripts/plan_extractor.py`

**Remove entirely:**
- `_union_bbox()` function
- `_render_crop_as_png()` function
- All imports used exclusively by these functions (`pypdfium2` import inside
  `_render_crop_as_png` stays — it is now used by `_render_full_page_as_png`)

**Add:**
```python
def _render_full_page_as_png(
    pdf_path: Path,
    page_index: int,
    scale: float = 1.5,
) -> bytes:
    """Render a full PDF page to PNG bytes.

    scale=1.5 gives ~108 DPI — sufficient for vision model label recognition
    while keeping image size manageable (~100KB for a 20-20 elevation page).
    Full page preferred over crop: gives spatial context that helps the model
    disambiguate overlapping labels.
    """
    import pypdfium2 as pdfium
    from io import BytesIO

    pdf = pdfium.PdfDocument(str(pdf_path))
    page = pdf[page_index]
    bitmap = page.render(scale=scale)
    pil_image = bitmap.to_pil()
    buf = BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()
```

**Update `_extract_codes_via_vision` signature and body:**

Remove `garbled_words`, `page_width`, `page_height` parameters (no longer
needed — full page requires none of them). New signature:

```python
def _extract_codes_via_vision(
    pdf_path: Path,
    page_index: int,
    drawing_label: str,
) -> list[str]:
    """Call Claude vision API on a full rendered page; return cabinet codes.

    Sends the full page (not a crop) — spatial context improves label
    recognition in regions where labels overlap.
    Requires ANTHROPIC_API_KEY; returns [] if not set.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            f"Warning: ANTHROPIC_API_KEY not set — skipping vision fallback "
            f"for {drawing_label}",
            file=sys.stderr,
        )
        return []

    png_bytes = _render_full_page_as_png(pdf_path, page_index)
    image_data = base64.standard_b64encode(png_bytes).decode("utf-8")

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "This is a 20-20 kitchen design drawing where cabinet "
                        "labels overlap. Extract all cabinet component codes "
                        "visible in the image.\n\n"
                        "Cabinet codes follow this strict format:\n"
                        "- 1-4 uppercase letters, followed by 2-4 digits, "
                        "optionally followed by 0-4 uppercase letters\n"
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
                        "Return ONLY a JSON array of strings, one code per "
                        "element. No explanation — only the JSON array."
                    ),
                },
            ],
        }],
    )
    raw = response.content[0].text.strip()
    # Strip markdown fences (model sometimes wraps output despite instructions)
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    # If model included reasoning text before the JSON, extract the array
    m = re.search(r'\[.*\]', raw, re.DOTALL)
    if m:
        raw = m.group(0)
    try:
        codes = json.loads(raw)
        return [c for c in codes if isinstance(c, str) and c.strip()]
    except json.JSONDecodeError:
        print(
            f"Warning: vision fallback returned non-JSON for {drawing_label}: "
            f"{raw[:80]!r}",
            file=sys.stderr,
        )
        return []
```

Note the added `re.search(r'\[.*\]', raw, re.DOTALL)` fallback — this
recovers the JSON array even when the model inserts reasoning text before or
after it, which is what caused the crop's JSON parse errors.

**Update `_extract_page_codes`:** remove `garbled_words`, `page_width`,
`page_height` from the `_extract_codes_via_vision` call:

```python
    if garbled_words and pdf_path is not None:
        try:
            vision_codes = _extract_codes_via_vision(
                pdf_path=pdf_path,
                page_index=page_index,
                drawing_label=label,
            )
            for raw in vision_codes:
                code = _token_to_code(raw)
                if code:
                    codes.append(code)
        except Exception as exc:
            print(
                f"Warning: vision fallback failed for {label}: {exc}",
                file=sys.stderr,
            )
```

---

## Touches

- `scripts/plan_extractor.py` — remove `_union_bbox`, `_render_crop_as_png`;
  add `_render_full_page_as_png`; update `_extract_codes_via_vision` signature
  and body; update call in `_extract_page_codes`
- `tests/test_plan_extractor.py` — remove any tests for `_union_bbox` or
  `_render_crop_as_png` if present; update the vision fallback monkeypatch
  test to match new signature

**Do not generate.**
- Changes to `schema.py`, `main.py`, `catalog_resolver.py`, or any other file
- Changes to `requirements.txt` (`pypdfium2` stays)

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v

# Verify full-page vision recovers DCW2439R and doesn't emit _union_bbox error
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
codes = {r['code'] for r in data}
assert 'DCW2439R' in codes, 'DCW2439R must be present (full-page vision)'
assert 'F33' not in codes,  'F33 must be filtered (noise)'
required = {'DB30', 'BLB42FHL', 'W2739', 'SB42', 'USF330'}
missing = required - codes
assert not missing, f'Required codes missing: {missing}'
print(f'✓ DCW2439R present')
print(f'✓ F33 absent')
print(f'Total: {len(codes)} distinct codes')
for r in sorted(data, key=lambda x: (x['drawing'], x['code'])):
    print(f\"  {r['code']:<25} {r['drawing']:<12} qty={r['qty']}\")
"
```

Expected: `DCW2439R` present, `F33` absent, all required codes present,
no `_union_bbox` or `_render_crop_as_png` references in the output or errors.

---

## Claude-code prompt

> Refactor `scripts/plan_extractor.py` per
> `docs/m-boxy-pipeline-1a-fullpage-vision-patch.md §Changes`.
>
> Three changes:
> 1. Remove `_union_bbox()` and `_render_crop_as_png()` entirely.
> 2. Add `_render_full_page_as_png()` per §Changes.
> 3. Update `_extract_codes_via_vision()` — new signature (remove
>    `garbled_words`, `page_width`, `page_height`), use
>    `_render_full_page_as_png`, add the `re.search(r'\[.*\]', raw, re.DOTALL)`
>    JSON recovery fallback. The exact body is in §Changes — copy it verbatim.
> 4. Update the call in `_extract_page_codes` to match the new signature.
>
> In `tests/test_plan_extractor.py`: update the vision monkeypatch test
> (`test_vision_codes_filtered_through_token_to_code`) to match the new
> `_extract_codes_via_vision` signature (no `garbled_words`, `page_width`,
> `page_height` kwargs). Remove any tests that reference `_union_bbox` or
> `_render_crop_as_png` if they exist.
>
> Do not modify any other file.
>
> Run the done-check from §Done-check and include the full code list
> in your review packet.
