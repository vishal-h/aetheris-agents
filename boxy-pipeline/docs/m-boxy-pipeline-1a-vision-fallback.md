# Patch: plan_extractor — vision fallback for garbled floor plan pages

**Context.** The text-layer extractor reliably extracts cabinet codes from
elevation drawings (El1–El4). On floor plan pages, 20-20 places cabinet labels
at their spatial position — when adjacent cabinets are close, their labels
physically overlap in the PDF coordinate space, producing garbled character
blends that no text-splitting algorithm can recover.

**Evidence from Joey kitchen:**
- Page 1 (floor plan / El1): 1 garbled token `'DCW243U9SRF339W2439'`
- Pages 2–4 (El2–El4): 0 garbled tokens
- Lost codes: `W0939L`, `W0939R` (map to `W0939-2001` in Boxy catalog, $105.46 each)

**The fix:** when a page has ≥1 garbled token (len > 12, no regex match), render
that page as an image and pass it to the Claude vision API to extract cabinet
codes. Merge vision results with text-layer results, dedup by (drawing, code).

---

## Detection heuristic

A token is "garbled" if:
- `len(cleaned) > 12`
- `_CABINET_RE.fullmatch(cleaned)` is False

A page is "garbled" if it has ≥1 garbled token. In the Joey kitchen PDF this
fires only on the floor plan page — never on elevation pages. The heuristic
is already validated against the sample data.

```python
def _is_garbled(token: str) -> bool:
    """Return True if token looks like a garbled overlap of multiple labels."""
    cleaned = token.strip("\"'.,;:()[]").replace(".", "")
    return len(cleaned) > 12 and not _CABINET_RE.fullmatch(cleaned)
```

---

## Targeted crop approach

Rather than rendering the full page, collect all garbled token bounding boxes,
union them into a single region, add 60pt padding, and send only that crop to
the vision API. For the Joey kitchen floor plan this produces a ~556×267px
image — tiny, fast, and containing exactly the overlapping label region.

```python
def _get_garbled_bboxes(words: list[dict]) -> list[dict]:
    """Return word dicts for garbled tokens (overlapping label candidates)."""
    return [
        w for w in words
        if _is_garbled(w['text'])
    ]


def _union_bbox(
    bboxes: list[dict],
    page_width: float,
    page_height: float,
    padding: float = 60.0,
) -> tuple[float, float, float, float]:
    """Return padded union of all bounding boxes, clamped to page dimensions."""
    x0     = max(0.0,         min(b['x0']     for b in bboxes) - padding)
    top    = max(0.0,         min(b['top']     for b in bboxes) - padding)
    x1     = min(page_width,  max(b['x1']     for b in bboxes) + padding)
    bottom = min(page_height, max(b['bottom'] for b in bboxes) + padding)
    return x0, top, x1, bottom


def _render_crop_as_png(
    pdf_path: Path,
    page_index: int,
    bbox: tuple[float, float, float, float],
    scale: float = 2.0,
) -> bytes:
    """Render a cropped region of a PDF page to PNG bytes.

    bbox is in PDF points (same coordinate system as pdfplumber word dicts).
    scale=2.0 gives ~144 DPI output.
    """
    import pypdfium2 as pdfium
    from io import BytesIO

    pdf = pdfium.PdfDocument(str(pdf_path))
    page = pdf[page_index]
    bitmap = page.render(scale=scale)
    pil_image = bitmap.to_pil()

    x0, top, x1, bottom = bbox
    crop = pil_image.crop((
        max(0, int(x0 * scale)),
        max(0, int(top * scale)),
        int(x1 * scale),
        int(bottom * scale),
    ))
    buf = BytesIO()
    crop.save(buf, format="PNG")
    return buf.getvalue()
```

---

## Vision API call

Use the Anthropic Python SDK with a **targeted crop** of the garbled region —
not the full page. The `_render_crop_as_png` function (defined in §Targeted
crop approach above) handles the rendering. For the Joey kitchen floor plan
this sends a ~556×267px image, not the full page.

```python
import anthropic
import base64
import os

def _extract_codes_via_vision(
    pdf_path: Path,
    page_index: int,
    drawing_label: str,
    garbled_words: list[dict],
    page_width: float,
    page_height: float,
) -> list[str]:
    """Call Claude vision API on a cropped garbled region; return cabinet codes.

    Sends only the padded bounding box union of garbled tokens — not the full
    page. Requires ANTHROPIC_API_KEY; returns [] if not set.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            f"Warning: ANTHROPIC_API_KEY not set — skipping vision fallback "
            f"for {drawing_label}",
            file=sys.stderr,
        )
        return []

    bbox = _union_bbox(garbled_words, page_width, page_height, padding=60.0)
    png_bytes = _render_crop_as_png(pdf_path, page_index, bbox)
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
                        "This is a cropped region of a 20-20 kitchen design drawing "
                        "where cabinet labels overlap. Extract all cabinet component "
                        "codes visible in the image. "
                        "Cabinet codes are short uppercase alphanumeric strings like "
                        "W0939L, W0939R, DCW2439R, WEP42, BLB42FHL, DB30, USF330. "
                        "Return ONLY a JSON array of strings, one per code. "
                        "Example: [\"W0939L\", \"W0939R\", \"DCW2439R\"]. "
                        "Do not include dimension numbers, annotations, or non-cabinet text. "
                        "Do not include any explanation — only the JSON array."
                    ),
                },
            ],
        }],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        codes = json.loads(raw)
        return [c for c in codes if isinstance(c, str) and c.strip()]
    except json.JSONDecodeError:
        print(
            f"Warning: vision fallback returned non-JSON for {drawing_label}: {raw!r}",
            file=sys.stderr,
        )
        return []
```

---

## Integration into `_extract_page_codes`

```python
def _extract_page_codes(
    page,
    pdf_path: Path | None = None,
    page_index: int = 0,
) -> tuple[str, list[str]]:
    """Return (drawing_label, list_of_codes) for one page.

    If garbled tokens are detected (overlapping labels in floor plan),
    sends a targeted crop of the garbled region to the vision API and
    merges results with the text-layer extraction.
    """
    text = page.extract_text() or ""
    words = page.extract_words(x_tolerance=1, y_tolerance=3)
    label = _drawing_label(text)
    codes: list[str] = []

    # Appliance codes from full text
    for m in _APPLIANCE_RE.finditer(text):
        if m.group(3) not in _ANNOT_ABBREVS:
            codes.append(f"{m.group(1)} {m.group(2)} {m.group(3)}")

    # Cabinet codes from individual word tokens; collect garbled words
    garbled_words = []
    for w in words:
        code = _token_to_code(w["text"])
        if code:
            codes.append(code)
        elif _is_garbled(w["text"]):
            garbled_words.append(w)

    # Vision fallback for pages with garbled tokens
    if garbled_words and pdf_path is not None:
        try:
            vision_codes = _extract_codes_via_vision(
                pdf_path=pdf_path,
                page_index=page_index,
                drawing_label=label,
                garbled_words=garbled_words,
                page_width=float(page.width),
                page_height=float(page.height),
            )
            codes.extend(vision_codes)
        except Exception as exc:
            print(
                f"Warning: vision fallback failed for {label}: {exc}",
                file=sys.stderr,
            )

    return label, codes
```

Update `extract_pdfs` to pass `pdf_path` and `page_index` to
`_extract_page_codes`:

```python
def extract_pdfs(pdf_paths: list[Path]) -> list[PlanComponent]:
    seen: dict[tuple[str, str], PlanComponent] = {}
    for path in pdf_paths:
        with pdfplumber.open(path) as pdf:
            for page_index, page in enumerate(pdf.pages):
                label, codes = _extract_page_codes(page, pdf_path=path, page_index=page_index)
                for code in codes:
                    key = (label, code)
                    if key in seen:
                        seen[key].qty += 1
                    else:
                        seen[key] = PlanComponent(
                            code=code, drawing=label, qty=1, notes=None
                        )
    return list(seen.values())
```

---

## Environment variable guard

Vision fallback requires `ANTHROPIC_API_KEY`. If not set, skip the vision
fallback and emit a warning — do not raise. The text-layer result is still
usable without it.

```python
import os

def _extract_codes_via_vision(...) -> list[str]:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            f"Warning: ANTHROPIC_API_KEY not set — skipping vision fallback for {drawing_label}",
            file=sys.stderr,
        )
        return []
    # ... rest of function
```

---

## Touches

- `scripts/plan_extractor.py` — add `_is_garbled`, `_render_page_as_png`,
  `_extract_codes_via_vision`; update `_extract_page_codes` and `extract_pdfs`
- `requirements.txt` — add `pypdfium2>=4.30.0`
- `tests/test_plan_extractor.py` — add tests for `_is_garbled` and
  integration test asserting `W0939L` and `W0939R` are present in output
  (marked `@pytest.mark.integration`)

## Do not generate

- Changes to `schema.py`, `catalog_resolver.py`, `order_formatter.py`,
  `main.py`
- Any modification to existing tests
- A retry/backoff mechanism (out of scope)

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v

python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
codes = {r['code'] for r in data}
required = {'DB30', 'BLB42FHL', 'W2739', 'SB42', 'USF330'}
missing = required - codes
assert not missing, f'Required codes missing: {missing}'
assert 'DCW243U9SRF339W2439' not in codes, 'Garbled token in output'
print(f'✓ Vision fallback fired and completed cleanly')
print(f'Total: {len(codes)} distinct codes')
"
```

Expected: all 5 required codes present, garbled token `DCW243U9SRF339W2439`
absent, exit code 0, test count increases.

**Note on W0939L/W0939R (spec revision):** These codes were originally listed
as "lost codes" to recover via vision. Investigation during implementation showed
they do not appear anywhere in the design PDFs — not in the text layer of either
PDF at any x_tolerance, and not as visual labels in the rendered images. They
appear in the sales order (SO86708) because they were added to the project
separately (likely specified verbally or from a prior spec sheet). The design
drawings simply don't label those cabinets. The vision fallback cannot recover
codes that are not present in the rendered image. See
`boxy-pipeline/docs/reviews/m-boxy-pipeline-1a-vision-fallback-review.md`
for the full investigation record.

---

## Claude-code prompt

> Implement the vision fallback for `scripts/plan_extractor.py` per
> `docs/m-boxy-pipeline-1a-vision-fallback.md`.
>
> Read that file in full before writing any code. The full implementation
> — `_is_garbled`, `_render_page_as_png`, `_extract_codes_via_vision`,
> updated `_extract_page_codes` and `extract_pdfs` — is specified there.
> Do not deviate from the specified API call structure or the environment
> variable guard.
>
> Add `pypdfium2>=4.30.0` to `requirements.txt`.
>
> Add to `tests/test_plan_extractor.py`:
> - Unit tests for `_is_garbled`: known garbled tokens return True,
>   known valid codes return False
> - `@pytest.mark.integration` test asserting `W0939L` and `W0939R`
>   appear in output from the sample PDFs (requires `ANTHROPIC_API_KEY`)
>
> Do not modify any existing test. Do not change `schema.py` or any other
> script.
>
> Run the done-check and include actual output (including the W0939L/W0939R
> confirmation lines) in your review packet.
