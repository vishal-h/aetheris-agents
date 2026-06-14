"""Tests for scripts/plan_extractor.py — t1."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from plan_extractor import (
    _CABINET_RE,
    _drawing_label,
    _filter_floor_plan_fragments,
    _is_garbled,
    _token_to_code,
    extract_pdfs,
)
from schema import PlanComponent

USE_CASE_ROOT = Path(__file__).parent.parent
SAMPLES_DIR = USE_CASE_ROOT / "data" / "samples"

ELEVATION_PDF = SAMPLES_DIR / "Joey-_Kitchen_2D_Plans_V2.pdf"
FLOOR_PLAN_PDF = SAMPLES_DIR / "Joey-_Kitchen_Plan_V2.pdf"
SAMPLES_AVAILABLE = ELEVATION_PDF.exists() and FLOOR_PLAN_PDF.exists()


# ---------------------------------------------------------------------------
# Regex unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "token",
    [
        "DB30",
        "BLB42FHL",
        "W2739",
        "SB42",
        "USF330",
        "USF357",
        "WEP42",
        "DCW2439R",
        "BPBC12",
        "BPBC9",
        "OVB36",
        "FSEP2493",
        "FSEP2496",
        "CKT36",        # CKT.36 after dot-removal
        "W2439-24",
        "W2424-24",
        "WP3612-24HK",
        "SUW2418-24",
        "3DB21",        # leading qty digit
        "DB21",
    ],
)
def test_cabinet_re_matches_known_codes(token):
    assert _CABINET_RE.fullmatch(token), f"Expected {token!r} to match"


@pytest.mark.parametrize(
    "token",
    [
        "BM",                   # only letters, no digits
        "BEP",                  # only letters, no digits
        "9RDCW2439R",           # garbled: starts with non-qty digit
        "DCW243U9SRF339W2439",  # garbled compound token
        "WEWP94329RDCW2439R",   # garbled compound token
        "24",                   # dimension number only
        "conditions",           # plain word
        "All",                  # drawing label word
        "Design",               # plain word
        "F933",                 # single letter + 3 digits — fragment, not a real code
        "B42FHL",               # single letter + digits + letters — fragment of BLB42FHL
        "WEPWEP42",             # garbled overlap — two WEP42 labels blended
        "W939RDCW2439R",        # garbled overlap — W939R + DCW2439R blended
        "WEP4WEP42",            # garbled overlap — partial blend
    ],
)
def test_cabinet_re_rejects_non_codes(token):
    assert not _CABINET_RE.fullmatch(token), f"Expected {token!r} NOT to match"


def test_token_to_code_strips_dot():
    assert _token_to_code("CKT.36") == "CKT36"


def test_token_to_code_strips_leading_quote():
    assert _token_to_code('"FSEP2493') == "FSEP2493"


def test_token_to_code_rejects_short():
    assert _token_to_code("DB") is None   # no digits → no match anyway
    assert _token_to_code("W9") is None   # too short (< 4)


def test_token_to_code_returns_none_for_plain_word():
    assert _token_to_code("Filler") is None
    assert _token_to_code("conditions.") is None


def test_token_to_code_rejects_garbled_overlap_tokens():
    """Garbled overlap tokens must not produce false cabinet codes."""
    garbled = ["WEPWEP42", "W939RDCW2439R", "WEP4WEP42", "WEP429FDCW2439R"]
    for token in garbled:
        assert _token_to_code(token) is None, (
            f"Garbled overlap token {token!r} should not match"
        )


# ---------------------------------------------------------------------------
# Drawing label detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "footer_text, expected_label",
    [
        ("Joey- Kitchen Design V2 El 1 Drawing #: 1 No Scale.", "El1"),
        ("Joey- Kitchen Design V2 El 2 Drawing #: 1 No Scale.", "El2"),
        ("Joey- Kitchen Design V2 El 3 Drawing #: 1 No Scale.", "El3"),
        ("Joey- Kitchen Design V2 El 4 Drawing #: 1 No Scale.", "El4"),
        ("Joey- Kitchen Design V2 All Drawing #: 1 No Scale.", "floor_plan"),
    ],
)
def test_drawing_label_detection(footer_text, expected_label):
    assert _drawing_label(footer_text) == expected_label


def test_drawing_label_unknown_for_unrecognised_footer():
    assert _drawing_label("some random text") == "unknown"


# ---------------------------------------------------------------------------
# Deduplication logic
# ---------------------------------------------------------------------------


def test_deduplication_increments_qty_same_drawing(tmp_path):
    """Same code appearing twice on the same drawing → qty = 2."""
    # We test by running extract_pdfs and checking that duplicates in the
    # same drawing collapse correctly.  Use real PDFs to avoid mocking.
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")

    components = extract_pdfs([ELEVATION_PDF])
    # BLB42FHL appears twice on El3; verify qty ≥ 2 for that drawing
    el3_blb = [c for c in components if c.code == "BLB42FHL" and c.drawing == "El3"]
    assert el3_blb, "BLB42FHL not found on El3"
    assert el3_blb[0].qty >= 2


def test_deduplication_separate_records_across_drawings():
    """Same code on different drawings → separate PlanComponent records."""
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")

    components = extract_pdfs([ELEVATION_PDF])
    usf330 = [c for c in components if c.code == "USF330"]
    drawings = {c.drawing for c in usf330}
    # USF330 appears on El2, El3, El4 — at least 2 distinct drawings
    assert len(drawings) >= 2, f"Expected USF330 on multiple drawings, got {drawings}"


# ---------------------------------------------------------------------------
# Floor plan fragment filter
# ---------------------------------------------------------------------------


def test_filter_suppresses_proper_suffix_of_elevation_code():
    """floor_plan code that is a proper suffix of an elevation code → suppressed."""
    components = [
        PlanComponent(code="BLB42FHL", drawing="El1", qty=1, notes=None),
        PlanComponent(code="B42FHL",   drawing="floor_plan", qty=1, notes=None),  # fragment
    ]
    result = _filter_floor_plan_fragments(components)
    codes = {c.code for c in result}
    assert "BLB42FHL" in codes
    assert "B42FHL" not in codes


def test_filter_keeps_exact_match_across_drawings():
    """floor_plan code that exactly matches an elevation code → kept (not a fragment)."""
    components = [
        PlanComponent(code="DA 6698 W", drawing="El3",        qty=1, notes=None),
        PlanComponent(code="DA 6698 W", drawing="floor_plan", qty=1, notes=None),
    ]
    result = _filter_floor_plan_fragments(components)
    drawings = {c.drawing for c in result if c.code == "DA 6698 W"}
    assert "El3" in drawings
    assert "floor_plan" in drawings


def test_filter_suppresses_eep2493_as_fsep2493_fragment():
    """EEP2493 is a one-char-shifted garbling of FSEP2493: drop E → EP2493,
    which is a suffix of FSEP2493 (strictly longer)."""
    components = [
        PlanComponent(code="FSEP2493", drawing="El2",        qty=1, notes=None),
        PlanComponent(code="EEP2493",  drawing="floor_plan", qty=1, notes=None),
    ]
    result = _filter_floor_plan_fragments(components)
    codes = {c.code for c in result}
    assert "FSEP2493" in codes
    assert "EEP2493" not in codes


# ---------------------------------------------------------------------------
# Integration: full extraction against real sample PDFs
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_extract_pdfs_required_codes():
    """All five required codes must be present across both sample PDFs."""
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")

    components = extract_pdfs([ELEVATION_PDF, FLOOR_PLAN_PDF])
    codes = {c.code for c in components}

    assert len(codes) >= 15, f"Expected ≥15 distinct codes, got {len(codes)}: {sorted(codes)}"

    required = {"DB30", "BLB42FHL", "W2739", "SB42", "USF330"}
    missing = required - codes
    assert not missing, f"Required codes missing: {missing}"

    noise = {"B42FHL", "EEP2493", "F933"}
    present_noise = noise & codes
    assert not present_noise, f"Noise codes must not appear in output: {present_noise}"


@pytest.mark.integration
def test_extract_pdfs_schema_fields():
    """Every PlanComponent has the four required schema fields with correct types."""
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")

    components = extract_pdfs([ELEVATION_PDF, FLOOR_PLAN_PDF])
    assert components

    for c in components:
        assert isinstance(c, PlanComponent)
        assert isinstance(c.code, str) and c.code
        assert isinstance(c.drawing, str) and c.drawing
        assert isinstance(c.qty, int) and c.qty >= 1
        assert c.notes is None or isinstance(c.notes, str)


@pytest.mark.integration
def test_cli_outputs_valid_json():
    """CLI invocation produces a valid JSON array with the required codes."""
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")

    result = subprocess.run(
        [
            sys.executable,
            str(USE_CASE_ROOT / "scripts" / "plan_extractor.py"),
            str(ELEVATION_PDF),
            str(FLOOR_PLAN_PDF),
        ],
        capture_output=True,
        text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0, f"CLI failed:\n{result.stderr}"

    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) >= 1

    codes = {item["code"] for item in data}
    required = {"DB30", "BLB42FHL", "W2739", "SB42", "USF330"}
    missing = required - codes
    assert not missing, f"Required codes missing from CLI output: {missing}"


# ---------------------------------------------------------------------------
# _is_garbled unit tests (vision fallback heuristic)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "token",
    [
        "DCW243U9SRF339W2439",   # garbled token from El1 elevation page (len=19)
        "WEWP94W32E9LP42",       # garbled token from floor plan (len=15)
        "WEWP94329RDCW2439R",    # garbled token from floor plan (len=18)
        "FSEP2F4S9E6P2496",      # garbled token from floor plan (len=16)
        "DCW243U9SRF339W2439R",  # extended garbled token (len=19)
    ],
)
def test_is_garbled_returns_true_for_garbled_tokens(token):
    assert _is_garbled(token), f"Expected {token!r} to be detected as garbled"


@pytest.mark.parametrize(
    "token",
    [
        "BLB42FHL",
        "WEP42",
        "W2739",
        "DB30",
        "USF330",
        "DCW2439R",
        "SB42",
        "FSEP2493",
        # Short garbled blends: rejected by _CABINET_RE but also too short (len ≤ 12)
        # for _is_garbled — they're handled by _token_to_code returning None
        "WEPWEP42",
        "WEP4WEP42",
    ],
)
def test_is_garbled_returns_false_for_valid_codes(token):
    assert not _is_garbled(token), f"Expected {token!r} NOT to be detected as garbled"


# ---------------------------------------------------------------------------
# Integration: vision fallback recovers W0939L and W0939R
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_vision_fallback_fires_and_cleans_garbled_tokens():
    """Vision fallback fires on garbled pages and never lets garbled tokens through.

    El1 (Joey-_Kitchen_2D_Plans_V2.pdf page 0) has the garbled token
    DCW243U9SRF339W2439 (blend of DCW2439R and W2439 labels). The vision fallback
    detects this, crops the garbled region, and calls the Claude API. The required
    elevation codes (DCW2439R, W2739, WEP42) are already present in the text layer
    of El1 and remain in the output regardless of what vision returns.

    What this test guarantees: garbled tokens never appear in the output, and the
    vision fallback completes without raising — preserving all text-layer codes.

    Note: W0939L and W0939R do not appear in the text layer or visual content of
    either sample PDF. They exist in the sales order (SO86708) but are not labeled
    in these design drawings. The vision fallback cannot recover codes that are
    not present in the rendered image.

    Skipped when sample files are absent or ANTHROPIC_API_KEY is not set.
    """
    import os
    if not SAMPLES_AVAILABLE:
        pytest.skip("Sample files not available")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — vision fallback inactive")

    components = extract_pdfs([ELEVATION_PDF, FLOOR_PLAN_PDF])
    codes = {c.code for c in components}

    # Garbled tokens must never appear in output
    assert "DCW243U9SRF339W2439" not in codes, "El1 garbled token must not appear in output"
    assert "WEWP94W32E9LP42" not in codes, "Floor plan garbled token must not appear in output"
    assert "FSEP2F4S9E6P2496" not in codes, "Floor plan garbled token must not appear in output"

    # All required elevation codes must be present (not lost by vision fallback)
    required = {"DB30", "BLB42FHL", "W2739", "SB42", "USF330"}
    missing = required - codes
    assert not missing, f"Required codes lost after vision fallback: {missing}"
