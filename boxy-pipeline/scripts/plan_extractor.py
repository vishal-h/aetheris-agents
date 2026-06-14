#!/usr/bin/env python3
"""Extract cabinet component codes from 20-20 kitchen design PDFs.

Outputs a JSON array of PlanComponent dicts to stdout.
"""
import json
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


def _extract_page_codes(page) -> tuple[str, list[str]]:
    """Return (drawing_label, list_of_codes) for one page."""
    text = page.extract_text() or ""
    # x_tolerance=1 (down from 3): keeps spatially overlapping cabinet labels
    # as separate tokens rather than merging them into garbled strings like
    # "WEPWEP42". At tolerance=3, pdfplumber merges words within 3pt —
    # too aggressive for dense 20-20 floor plans where labels physically overlap.
    # Note: garbled tokens from partial character blending are not recoverable
    # by text splitting and are correctly discarded as non-matches.
    # All real codes appear cleanly in the elevation drawings (El1–El4).
    words = page.extract_words(x_tolerance=1, y_tolerance=3)

    label = _drawing_label(text)
    codes: list[str] = []

    # Appliance codes from full text (spans multiple tokens in word list)
    for m in _APPLIANCE_RE.finditer(text):
        if m.group(3) not in _ANNOT_ABBREVS:
            codes.append(f"{m.group(1)} {m.group(2)} {m.group(3)}")

    # Cabinet codes from individual word tokens
    for w in words:
        code = _token_to_code(w["text"])
        if code:
            codes.append(code)

    return label, codes


def _filter_floor_plan_fragments(components: list[PlanComponent]) -> list[PlanComponent]:
    """Suppress floor_plan codes that are garbled fragments of elevation codes.

    The floor plan is a dense spatial diagram where overlapping PDF text streams
    produce partial tokens. Two fragment patterns are detected:

    1. Proper suffix: floor_plan code is a trailing substring of a longer
       elevation code (e.g. B42FHL ← BLB42FHL).
    2. One-char-shifted suffix: dropping the first character of the floor_plan
       code gives a suffix of a strictly longer elevation code (e.g. EEP2493:
       drop E → EP2493, and FSEP2493 ends with EP2493).

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
        result.append(c)
    return result


def extract_pdfs(pdf_paths: list[Path]) -> list[PlanComponent]:
    """Extract and deduplicate PlanComponents from one or more PDFs."""
    # key: (drawing, code) → component; same code×drawing increments qty
    seen: dict[tuple[str, str], PlanComponent] = {}

    for path in pdf_paths:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                label, codes = _extract_page_codes(page)
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: plan_extractor.py <pdf> [<pdf> ...]", file=sys.stderr)
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"Error: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    try:
        components = extract_pdfs(paths)
        print(json.dumps([asdict(c) for c in components], indent=2))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
