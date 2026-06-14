"""Tests for catalog_resolver.py JSONL path — boxy-pipeline-1a t3.

Existing test_catalog_resolver.py must remain unchanged and pass.
These tests cover only the new load_catalog_jsonl function and the
auto-detection logic in resolve().
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from catalog_resolver import load_catalog_jsonl, resolve, parse_finish
from schema import CatalogItem, PlanComponent

USE_CASE_ROOT = Path(__file__).parent.parent
CATALOG_JSONL  = USE_CASE_ROOT / "data" / "catalog.jsonl"
SAMPLES_DIR    = USE_CASE_ROOT / "data" / "samples"
CATALOG_XLSX   = SAMPLES_DIR / "Updated_Boxy_MSRP_Sales_Order_Form.xlsx"


# ── Minimal JSONL fixture (no real files needed) ──────────────────────────────

def _make_entry(raw_code: str, base_code: str, color_code: str = "2001",
                msrp: float = 100.0, series: str = "2000") -> dict:
    return {
        "sku": f"{raw_code}-{color_code}",
        "base_code": base_code,
        "raw_code": raw_code,
        "series": series,
        "color_code": color_code,
        "color_name": "Ivory White",
        "description": f"Test Cabinet, 30\"W x 34\"H x 24\"D",
        "cabinet_type": "Base Cabinet",
        "width_in": 30.0,
        "height_in": 34.0,
        "depth_in": 24.0,
        "msrp": msrp,
        "mapped_20_20_codes": [],
        "notes": None,
        "catalog_version": "2026-06-14",
        "source_file": "test.xlsx",
    }


@pytest.fixture()
def minimal_jsonl(tmp_path: Path) -> Path:
    """Small JSONL with entries covering raw_code and base_code cases."""
    entries = [
        _make_entry("3DB30", "DB30", "2001", msrp=588.35),   # leading-digit raw
        _make_entry("3DB30", "DB30", "2004", msrp=620.00),   # same raw, second color
        _make_entry("W2739", "W2739", "2001", msrp=225.41),  # no leading digit
    ]
    path = tmp_path / "catalog.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return path


# ── Unit tests (minimal fixture) ──────────────────────────────────────────────


def test_load_catalog_jsonl_returns_nonempty_dict(minimal_jsonl):
    index = load_catalog_jsonl(minimal_jsonl)
    assert isinstance(index, dict)
    assert index


def test_load_catalog_jsonl_indexes_raw_code(minimal_jsonl):
    """raw_code "3DB30" must appear as an index key."""
    index = load_catalog_jsonl(minimal_jsonl)
    assert "3DB30" in index


def test_load_catalog_jsonl_indexes_base_code(minimal_jsonl):
    """base_code "DB30" must also appear as an index key (dual-index)."""
    index = load_catalog_jsonl(minimal_jsonl)
    assert "DB30" in index


def test_raw_and_base_code_keys_share_same_items(minimal_jsonl):
    """Items under raw_code and base_code keys must be the same objects."""
    index = load_catalog_jsonl(minimal_jsonl)
    assert index["3DB30"] == index["DB30"]


def test_load_catalog_jsonl_catalog_item_fields(minimal_jsonl):
    """CatalogItem built from JSONL has all required fields populated."""
    index = load_catalog_jsonl(minimal_jsonl)
    item = index["3DB30"][0]
    assert isinstance(item, CatalogItem)
    assert item.sku == "3DB30-2001"
    assert item.series == "2000"
    assert item.color_code == "2001"
    assert item.color_name == "Ivory White"
    assert item.cabinet_type == "Base Cabinet"
    assert item.width_in == pytest.approx(30.0)
    assert item.msrp == pytest.approx(588.35)


def test_load_catalog_jsonl_multiple_colors_indexed(minimal_jsonl):
    """All color variants of a code must be present under its key."""
    index = load_catalog_jsonl(minimal_jsonl)
    color_codes = {item.color_code for item in index["DB30"]}
    assert "2001" in color_codes
    assert "2004" in color_codes


def test_load_catalog_jsonl_no_digit_raw_code_not_duplicated(minimal_jsonl):
    """W2739 has base_code == raw_code; must not appear duplicated."""
    index = load_catalog_jsonl(minimal_jsonl)
    assert "W2739" in index
    # Each color should appear exactly once
    msrps = [item.msrp for item in index["W2739"]]
    assert len(msrps) == len(set(msrps))


def test_db30_resolves_via_jsonl(minimal_jsonl):
    """DB30 plan code resolves to the 3DB30 catalog entry via base_code index."""
    index = load_catalog_jsonl(minimal_jsonl)
    component = PlanComponent(code="DB30", drawing="El1", qty=1, notes=None)
    upper = parse_finish("2001:Ivory White:2000")
    lower = parse_finish("2001:Ivory White:2000")
    from catalog_resolver import _resolve_component
    result = _resolve_component(component, index, upper, lower)
    assert result.match_confidence == "exact"
    assert result.unit_price == pytest.approx(588.35)


def test_resolve_auto_detects_jsonl_extension(minimal_jsonl):
    """resolve() picks load_catalog_jsonl when path ends in .jsonl."""
    components = [PlanComponent(code="DB30", drawing="El1", qty=1, notes=None)]
    upper = parse_finish("2001:Ivory White:2000")
    lower = parse_finish("2001:Ivory White:2000")
    results = resolve(components, minimal_jsonl, upper, lower)
    assert results[0].match_confidence == "exact"


def test_load_catalog_jsonl_skips_blank_lines(tmp_path):
    """Blank lines in JSONL must be silently ignored."""
    entry = _make_entry("W2739", "W2739", "2001")
    path = tmp_path / "catalog.jsonl"
    path.write_text(f"\n{json.dumps(entry)}\n\n")
    index = load_catalog_jsonl(path)
    assert "W2739" in index


# ── Integration tests — require data/catalog.jsonl ────────────────────────────


@pytest.fixture(scope="module")
def real_index():
    """Load actual catalog.jsonl once for all integration tests in this module."""
    if not CATALOG_JSONL.exists():
        pytest.skip("data/catalog.jsonl not present — run catalog_extractor.py first")
    return load_catalog_jsonl(CATALOG_JSONL)


@pytest.mark.integration
def test_real_jsonl_loads_nonempty(real_index):
    # 332 unique keys (raw_code + base_code combined, not total entries)
    assert len(real_index) > 100


@pytest.mark.integration
def test_real_jsonl_indexes_db30(real_index):
    """DB30 must be reachable via base_code dual-index in real catalog."""
    assert "DB30" in real_index
    assert "3DB30" in real_index


@pytest.mark.integration
def test_real_jsonl_db30_color_match(real_index):
    """DB30 via base_code index must include entries for color 2004 (Mingo Oak)."""
    items_2004 = [i for i in real_index["DB30"] if i.color_code == "2004"]
    assert items_2004, "No color 2004 entries found for DB30"


@pytest.mark.integration
def test_real_jsonl_resolve_matches_excel_result():
    """Full pipeline via JSONL must yield same resolved/unresolved split as Excel.

    Expected: 7 resolved, 14 unresolved, subtotal $5,346.45.
    """
    if not CATALOG_JSONL.exists():
        pytest.skip("data/catalog.jsonl not present")
    drawings = [
        USE_CASE_ROOT / "data" / "samples" / "Joey-_Kitchen_2D_Plans_V2.pdf",
        USE_CASE_ROOT / "data" / "samples" / "Joey-_Kitchen_Plan_V2.pdf",
    ]
    if not all(p.exists() for p in drawings):
        pytest.skip("drawing samples not present")

    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "main.py"),
         "--drawings", str(drawings[0]), str(drawings[1]),
         "--catalog", str(CATALOG_JSONL),
         "--template", str(CATALOG_XLSX),
         "--project", "jsonl_test",
         "--upper-finish", "2001:Ivory White:2000",
         "--lower-finish", "2004:Mingo Oak:2000"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0, f"Pipeline failed:\n{result.stderr}"

    stdout = result.stdout
    assert "7 resolved" in stdout, f"Expected '7 resolved' in: {stdout}"
    assert "14 unresolved" in stdout, f"Expected '14 unresolved' in: {stdout}"
    assert "5,346.45" in stdout, f"Expected subtotal $5,346.45 in: {stdout}"
