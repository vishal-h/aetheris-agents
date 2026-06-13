"""Tests for scripts/catalog_resolver.py — t2."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from catalog_resolver import (
    _extract_cabinet_type,
    _is_upper,
    _parse_dimensions,
    _parse_finish,
    _resolve_component,
    load_catalog,
    resolve,
)
from schema import CatalogItem, PlanComponent

USE_CASE_ROOT = Path(__file__).parent.parent
SAMPLES_DIR = USE_CASE_ROOT / "data" / "samples"
CATALOG_FILE = SAMPLES_DIR / "Updated_Boxy_MSRP_Sales_Order_Form.xlsx"

UPPER_FINISH = ("2001", "Ivory White", "2000")
LOWER_FINISH = ("2004", "Mingo Oak", "2000")


def _make_wall_item(**kwargs) -> CatalogItem:
    defaults = dict(
        sku="W2739-2001",
        series="2000",
        color_code="2001",
        color_name="Ivory White",
        description='Wall Cabinet, 27"W × 39"H × 12"D, 2 Doors',
        cabinet_type="Wall Cabinet",
        width_in=27.0,
        height_in=39.0,
        depth_in=12.0,
        msrp=450.8,
    )
    defaults.update(kwargs)
    return CatalogItem(**defaults)


def _make_base_item(**kwargs) -> CatalogItem:
    defaults = dict(
        sku="3DB30-2004",
        series="2000",
        color_code="2004",
        color_name="Mingo Oak",
        description='Base Cabinet, 30"W × 34-1/2"H × 24"D, 3 Drawers',
        cabinet_type="Base Cabinet",
        width_in=30.0,
        height_in=34.5,
        depth_in=24.0,
        msrp=1188.4,
    )
    defaults.update(kwargs)
    return CatalogItem(**defaults)


# ---------------------------------------------------------------------------
# _parse_finish
# ---------------------------------------------------------------------------


def test_parse_finish_valid():
    assert _parse_finish("2001:Ivory White:2000") == ("2001", "Ivory White", "2000")


def test_parse_finish_preserves_colons_in_name():
    assert _parse_finish("2004:Mingo Oak:2000") == ("2004", "Mingo Oak", "2000")


def test_parse_finish_invalid_raises():
    with pytest.raises(ValueError):
        _parse_finish("2001-Ivory White")


# ---------------------------------------------------------------------------
# _extract_cabinet_type
# ---------------------------------------------------------------------------


def test_extract_cabinet_type_wall():
    assert _extract_cabinet_type('Wall Cabinet, 27"W × 39"H × 12"D') == "Wall Cabinet"


def test_extract_cabinet_type_base():
    assert _extract_cabinet_type('Base Cabinet, 30"W × 34-1/2"H × 24"D, 3 Drawers') == "Base Cabinet"


def test_extract_cabinet_type_sink_base():
    assert _extract_cabinet_type('Sink Base Cabinet, 42"W × 34-1/2"H × 24"D') == "Sink Base Cabinet"


# ---------------------------------------------------------------------------
# _parse_dimensions
# ---------------------------------------------------------------------------


def test_parse_dimensions_standard():
    w, h, d = _parse_dimensions('Wall Cabinet, 27"W × 39"H × 12"D, 2 Doors')
    assert w == 27.0
    assert h == 39.0
    assert d == 12.0


def test_parse_dimensions_fractional_height():
    w, h, d = _parse_dimensions('Base Cabinet, 30"W × 34-1/2"H × 24"D, 3 Drawers')
    assert w == 30.0
    assert abs(h - 34.5) < 0.01
    assert d == 24.0


def test_parse_dimensions_missing_returns_none():
    w, h, d = _parse_dimensions("Cabinet with no dimensions")
    assert w is None
    assert h is None
    assert d is None


# ---------------------------------------------------------------------------
# _is_upper
# ---------------------------------------------------------------------------


def test_is_upper_wall_cabinet():
    assert _is_upper("Wall Cabinet")


def test_is_upper_base_cabinet_false():
    assert not _is_upper("Base Cabinet")


def test_is_upper_sink_base_false():
    assert not _is_upper("Sink Base Cabinet")


# ---------------------------------------------------------------------------
# _resolve_component — in-memory index, no real catalog required
# ---------------------------------------------------------------------------


def test_resolve_exact_match():
    """Plan code found directly in index → exact."""
    index = {"W2739": [_make_wall_item()]}
    comp = PlanComponent(code="W2739", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "exact"
    assert r.catalog_item is not None
    assert r.catalog_item.sku == "W2739-2001"


def test_resolve_exact_via_catalog_normalization():
    """DB30 found under normalized key (stripped from 3DB30) → exact."""
    # The index key "DB30" is the normalized form of catalog code "3DB30".
    index = {"DB30": [_make_base_item()]}
    comp = PlanComponent(code="DB30", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "exact"
    assert r.catalog_item.sku == "DB30-2004"
    assert r.catalog_item.color_code == "2004"


def test_resolve_exact_uses_plan_code_in_sku():
    """SKU is built from the plan code, not the raw catalog code."""
    index = {"DB30": [_make_base_item(sku="3DB30-2004")]}
    comp = PlanComponent(code="DB30", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.catalog_item.sku == "DB30-2004"


def test_resolve_fuzzy_via_suffix_strip():
    """W2439-24 → strip -24 → W2439 found in index → fuzzy."""
    index = {"W2439": [_make_wall_item(sku="W2439-2001", description='Wall Cabinet, 24"W × 39"H × 12"D', width_in=24.0)]}
    comp = PlanComponent(code="W2439-24", drawing="El2", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "fuzzy"
    assert r.catalog_item.sku == "W2439-2001"
    assert r.match_notes is not None


def test_resolve_unresolved_empty_index():
    """Code absent from index → unresolved, no catalog_item."""
    comp = PlanComponent(code="BLB42FHL", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, {}, UPPER_FINISH, LOWER_FINISH)
    assert r.match_confidence == "unresolved"
    assert r.catalog_item is None
    assert r.unit_price == 0.0
    assert r.line_total == 0.0


def test_resolve_upper_cabinet_gets_upper_finish():
    """Wall cabinet picks upper finish color."""
    item_2001 = _make_wall_item(color_code="2001", color_name="Ivory White", msrp=450.8)
    item_2004 = _make_wall_item(sku="W2739-2004", color_code="2004", color_name="Mingo Oak", msrp=581.15)
    index = {"W2739": [item_2001, item_2004]}
    comp = PlanComponent(code="W2739", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.catalog_item.color_code == "2001"
    assert r.unit_price == pytest.approx(450.8)


def test_resolve_lower_cabinet_gets_lower_finish():
    """Base cabinet picks lower finish color."""
    item_2001 = _make_base_item(sku="SB42-2001", color_code="2001", msrp=488.6,
                                description='Sink Base Cabinet, 42"W × 34-1/2"H × 24"D',
                                cabinet_type="Sink Base Cabinet")
    item_2004 = _make_base_item(sku="SB42-2004", color_code="2004", msrp=643.8,
                                description='Sink Base Cabinet, 42"W × 34-1/2"H × 24"D',
                                cabinet_type="Sink Base Cabinet")
    index = {"SB42": [item_2001, item_2004]}
    comp = PlanComponent(code="SB42", drawing="El4", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.catalog_item.color_code == "2004"
    assert r.unit_price == pytest.approx(643.8)


def test_resolve_line_total_uses_qty():
    """line_total = unit_price × qty."""
    index = {"W2739": [_make_wall_item(msrp=450.8)]}
    comp = PlanComponent(code="W2739", drawing="El1", qty=3, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.qty == 3
    assert r.line_total == pytest.approx(450.8 * 3)


def test_resolve_prefers_series_match():
    """When multiple series available, prefer the one matching finish spec."""
    item_1000 = _make_base_item(sku="DB30-2004", series="1000", color_code="2004", msrp=900.0)
    item_2000 = _make_base_item(sku="DB30-2004", series="2000", color_code="2004", msrp=1188.4)
    index = {"DB30": [item_1000, item_2000]}
    comp = PlanComponent(code="DB30", drawing="El1", qty=1, notes=None)
    r = _resolve_component(comp, index, UPPER_FINISH, LOWER_FINISH)
    assert r.catalog_item.series == "2000"
    assert r.unit_price == pytest.approx(1188.4)


# ---------------------------------------------------------------------------
# Integration tests — require data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_load_catalog_indexes_expected_codes():
    index = load_catalog(CATALOG_FILE)
    assert "W2739" in index, "W2739 must be in catalog index"
    assert "SB42" in index, "SB42 must be in catalog index"
    assert "DB30" in index, "DB30 must appear as normalized key (from 3DB30)"
    assert "DB21" in index, "DB21 must appear as normalized key (from 3DB21)"
    assert "W2424" in index, "W2424 must be in catalog index"
    assert "W2439" in index, "W2439 must be in catalog index"


@pytest.mark.integration
def test_load_catalog_item_fields():
    index = load_catalog(CATALOG_FILE)
    w2739_items = [ci for ci in index["W2739"] if ci.series == "2000" and ci.color_code == "2001"]
    assert w2739_items, "W2739 2000-series 2001-color item not found"
    item = w2739_items[0]
    assert item.cabinet_type == "Wall Cabinet"
    assert item.width_in == pytest.approx(27.0)
    assert item.height_in == pytest.approx(39.0)
    assert item.depth_in == pytest.approx(12.0)
    assert item.msrp == pytest.approx(450.8)


@pytest.mark.integration
def test_resolve_db30_exact_confidence():
    """DB30 must resolve with exact confidence and SKU DB30-2004."""
    comp = PlanComponent(code="DB30", drawing="El1", qty=1, notes=None)
    results = resolve([comp], CATALOG_FILE, UPPER_FINISH, LOWER_FINISH)
    assert len(results) == 1
    r = results[0]
    assert r.match_confidence == "exact"
    assert r.catalog_item is not None
    assert r.catalog_item.sku == "DB30-2004"
    assert r.catalog_item.color_code == "2004"
    assert r.catalog_item.series == "2000"
    assert r.unit_price > 0


@pytest.mark.integration
def test_resolve_w2739_exact_ivory_white():
    comp = PlanComponent(code="W2739", drawing="El1", qty=1, notes=None)
    results = resolve([comp], CATALOG_FILE, UPPER_FINISH, LOWER_FINISH)
    r = results[0]
    assert r.match_confidence == "exact"
    assert r.catalog_item.sku == "W2739-2001"
    assert r.catalog_item.color_code == "2001"


@pytest.mark.integration
def test_resolve_appliance_codes_unresolved():
    comps = [
        PlanComponent(code="DA 6698 W", drawing="El3", qty=1, notes=None),
        PlanComponent(code="G 7186 SCVi", drawing="El2", qty=1, notes=None),
        PlanComponent(code="KFNF 9959 iDE", drawing="El2", qty=1, notes=None),
    ]
    results = resolve(comps, CATALOG_FILE, UPPER_FINISH, LOWER_FINISH)
    for r in results:
        assert r.match_confidence == "unresolved", f"{r.component.code!r} should be unresolved"
        assert r.catalog_item is None


@pytest.mark.integration
def test_cli_pipe_t1_into_t2():
    """t1 | t2 CLI pipe produces valid ResolvedItem JSON with DB30 as exact."""
    elevation_pdf = SAMPLES_DIR / "Joey-_Kitchen_2D_Plans_V2.pdf"
    floor_pdf = SAMPLES_DIR / "Joey-_Kitchen_Plan_V2.pdf"

    t1 = subprocess.run(
        [
            sys.executable,
            str(USE_CASE_ROOT / "scripts" / "plan_extractor.py"),
            str(elevation_pdf),
            str(floor_pdf),
        ],
        capture_output=True,
        text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert t1.returncode == 0, f"t1 failed:\n{t1.stderr}"

    t2 = subprocess.run(
        [
            sys.executable,
            str(USE_CASE_ROOT / "scripts" / "catalog_resolver.py"),
            "--catalog", str(CATALOG_FILE),
            "--upper-finish", "2001:Ivory White:2000",
            "--lower-finish", "2004:Mingo Oak:2000",
        ],
        input=t1.stdout,
        capture_output=True,
        text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert t2.returncode == 0, f"t2 failed:\n{t2.stderr}"

    data = json.loads(t2.stdout)
    assert isinstance(data, list) and len(data) > 0

    # DB30 must resolve exact with SKU DB30-2004
    db30 = [item for item in data if item["component"]["code"] == "DB30"]
    assert db30, "DB30 not in output"
    assert db30[0]["match_confidence"] == "exact"
    assert db30[0]["catalog_item"]["sku"] == "DB30-2004"

    # Appliance codes must be unresolved
    for code in ("G 7186 SCVi", "KFNF 9959 iDE"):
        items = [item for item in data if item["component"]["code"] == code]
        assert items, f"{code} not in output"
        assert items[0]["match_confidence"] == "unresolved"
        assert items[0]["catalog_item"] is None
