#!/usr/bin/env python3
"""Extract cabinet component codes from 20-20 kitchen design PDFs.

Outputs a JSON array of PlanComponent dicts to stdout.
"""
import anthropic
import argparse
import base64
import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
from schema import PlanComponent

# Full-token cabinet code patterns (applied via re.fullmatch).
# Pattern A: single-letter wall cabinets — exactly 4 digits, no trailing letters.
#            Covers: W2739. Requires 4 digits to avoid matching fragments like F933.
# Pattern B: multi-letter codes — 2–4 uppercase letters + 1–4 digits + 0–4 trailing letters.
#            Covers: DB30, BLB42FHL, USF330, SB42, BPBC9, DCW2439R, WEP42 …
# Pattern C: dash-suffix codes — 1–4 letters + 4 digits + -NN + optional suffix.
#            Covers: W2439-24, WP3612-24HK, SUW2418-24, W2424-24 …
_CABINET_RE = re.compile(
    r"^(?:"
    r"[A-Z][0-9]{4}"
    r"|[1-3]?[A-Z]{2,4}[0-9]{1,4}[A-Z]{0,4}"
    r"|[A-Z]{1,4}[0-9]{4}-[0-9]{2}[A-Z0-9]{0,4}"
    r")$"
)

# Multi-token appliance codes: "KFNF 9959 iDE", "G 7186 SCVi", "DA 6698 W"
_APPLIANCE_RE = re.compile(r"\b([A-Z]{1,4})\s+(\d{4})\s+([A-Za-z]+)\b")
# 20-20 drawing annotation abbreviations that share the appliance pattern — skip these.
_ANNOT_ABBREVS = frozenset({"BM", "EP", "TK", "FP", "LP", "RP", "TP", "BP", "LF", "RF"})

# Drawing label from page footer: "… V2 El 1 Drawing …" or "… V2 All Drawing …"
_LABEL_RE = re.compile(r"V\d+\s+(El\s*\d+|All)\s+Drawing")

_MIN_CODE_LEN = 4


def _normalise_label(raw: str) -> str:
    if raw.strip() == "All":
        return "floor_plan"
    return re.sub(r"\s+", "", raw)  # "El 1" → "El1"


def _drawing_label(page_text: str) -> str:
    m = _LABEL_RE.search(page_text)
    return _normalise_label(m.group(1)) if m else "unknown"


def _token_to_code(token: str) -> str | None:
    """Return a cabinet code if token matches, else None.

    Known limitation: spatially overlapping labels in 20-20 floor plans
    may produce garbled tokens (e.g. "WEPWEP42") that do not match.
    These are correctly discarded — the same codes appear in the elevation
    drawings where labels do not overlap.
    """
    # Strip leading/trailing punctuation; remove embedded dots (e.g. "CKT.36")
    cleaned = token.strip("\"'.,;:()[]").replace(".", "")
    if len(cleaned) < _MIN_CODE_LEN:
        return None
    if _CABINET_RE.fullmatch(cleaned):
        return cleaned
    return None


def _is_garbled(token: str) -> bool:
    """Return True if token looks like a garbled overlap of multiple labels."""
    cleaned = token.strip("\"'.,;:()[]").replace(".", "")
    return len(cleaned) > 12 and not _CABINET_RE.fullmatch(cleaned)


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

    # 120pt padding (up from 60): the garbled region on El1 has overlapping labels
    # visually present ~80pt below the token bbox. 60pt padding cropped them out.
    # 120pt captures the full label neighbourhood in all directions.
    bbox = _union_bbox(garbled_words, page_width, page_height, padding=120.0)
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
    # x_tolerance=1 (down from 3): keeps spatially overlapping cabinet labels
    # as separate tokens rather than merging them into garbled strings like
    # "WEPWEP42". At tolerance=3, pdfplumber merges words within 3pt —
    # too aggressive for dense 20-20 floor plans where labels physically overlap.
    words = page.extract_words(x_tolerance=1, y_tolerance=3)

    label = _drawing_label(text)
    codes: list[str] = []

    # Appliance codes from full text (spans multiple tokens in word list)
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
            # Validate vision codes through the same filter as text-layer tokens
            for raw in vision_codes:
                code = _token_to_code(raw)
                if code:
                    codes.append(code)
        except Exception as exc:
            print(
                f"Warning: vision fallback failed for {label}: {exc}",
                file=sys.stderr,
            )

    return label, codes


def _filter_floor_plan_fragments(components: list[PlanComponent]) -> list[PlanComponent]:
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
    elevation_codes = {c.code for c in components if c.drawing != "floor_plan"}
    result = []
    for c in components:
        if c.drawing == "floor_plan":
            code = c.code
            # Pattern 1: proper suffix of a longer elevation code
            if any(other != code and other.endswith(code) for other in elevation_codes):
                continue
            # Pattern 2: drop first char → suffix of a strictly longer elevation code
            if len(code) > 1 and any(
                len(other) > len(code) and other.endswith(code[1:])
                for other in elevation_codes
            ):
                continue
            # Pattern 3: proper prefix of a longer elevation code
            # e.g. BPBC1 suppressed because BPBC12.startswith(BPBC1) and len > len
            if any(len(other) > len(code) and other.startswith(code)
                   for other in elevation_codes):
                continue
        result.append(c)
    return result


def extract_pdfs(pdf_paths: list[Path]) -> list[PlanComponent]:
    """Extract and deduplicate PlanComponents from one or more PDFs."""
    # key: (drawing, code) → component; same code×drawing increments qty
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
                            code=code,
                            drawing=label,
                            qty=1,
                            notes=None,
                        )

    return _filter_floor_plan_fragments(list(seen.values()))


def _write_plan_jsonl(
    components: list[PlanComponent],
    pdf_paths: list[Path],
    project: str,
    output_dir: Path,
) -> Path:
    """Write PlanComponent list to {output_dir}/{project}/plan.jsonl."""
    import datetime
    out_dir = output_dir / project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "plan.jsonl"
    with open(out_path, "w") as f:
        meta = {
            "_meta": True,
            "project": project,
            "source_drawings": [p.name for p in pdf_paths],
            "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        f.write(json.dumps(meta) + "\n")
        for c in components:
            f.write(json.dumps(asdict(c)) + "\n")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract cabinet codes from 20-20 kitchen design PDFs."
    )
    parser.add_argument("pdfs", nargs="+", type=Path, metavar="PDF")
    parser.add_argument(
        "--output", type=Path, default=None, metavar="DIR",
        help="If given, write plan.jsonl to DIR/{project}/plan.jsonl",
    )
    parser.add_argument(
        "--project", default=None, metavar="NAME",
        help="Project name (required when --output is given)",
    )
    args = parser.parse_args()

    if args.output is not None and args.project is None:
        print("Error: --project is required when --output is given", file=sys.stderr)
        sys.exit(1)

    paths = args.pdfs
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"Error: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    try:
        components = extract_pdfs(paths)
        print(json.dumps([asdict(c) for c in components], indent=2))
        if args.output is not None:
            out_path = _write_plan_jsonl(components, paths, args.project, args.output)
            print(f"Plan:       {out_path}", file=sys.stderr)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
