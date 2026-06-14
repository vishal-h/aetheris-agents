"""Tests for scripts/so_extractor.py — boxy-pipeline-1a t2."""
import datetime
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from so_extractor import _parse_money, _extract_sku, extract_so
from schema import SalesOrder, SOLineItem

USE_CASE_ROOT = Path(__file__).parent.parent
SAMPLES_DIR   = USE_CASE_ROOT / "data" / "samples"
SO_FILE       = SAMPLES_DIR / "SO86708_Aria_Joey.pdf"


# ── Unit tests (no PDF needed) ─────────────────────────────────────────────────


def test_parse_money_plain():
    assert _parse_money("588.35") == pytest.approx(588.35)


def test_parse_money_dollar_sign():
    assert _parse_money("$588.35") == pytest.approx(588.35)


def test_parse_money_with_comma():
    assert _parse_money("$1,014.70") == pytest.approx(1014.70)


def test_extract_sku_product():
    assert _extract_sku("3DB30-2004 Mingo Oak") == "3DB30-2004"


def test_extract_sku_box_prefix():
    assert _extract_sku("Box-SB36") == "Box-SB36"


def test_extract_sku_accs_with_slash():
    assert _extract_sku("Accs-PNB36-2004/3004 Mingo Oak") == "Accs-PNB36-2004/3004"


def test_extract_sku_assembly_fee():
    assert _extract_sku("Assembly Fee") == "Assembly Fee"


def test_extract_sku_delivery_fee():
    assert _extract_sku("Delivery fee") == "Delivery fee"


def test_extract_sku_installation_fee():
    sku = _extract_sku("Installation fee for Add-on Accessories")
    assert sku == "Installation fee for Add-on Accessories"


def test_extract_sku_modify():
    assert _extract_sku("Modify-S") == "Modify-S"


# ── Integration tests — require real SO PDF ────────────────────────────────────


@pytest.fixture(scope="module")
def sales_order() -> SalesOrder:
    """Load real SO PDF once for all integration tests in this module."""
    if not SO_FILE.exists():
        pytest.skip("SO sample not present in data/samples/")
    return extract_so(SO_FILE)


@pytest.mark.integration
def test_order_number(sales_order):
    assert sales_order.header.order_number == "SO86708"


@pytest.mark.integration
def test_order_date(sales_order):
    assert sales_order.header.order_date == "2026-05-04"


@pytest.mark.integration
def test_customer_name(sales_order):
    assert "Aria" in sales_order.header.customer


@pytest.mark.integration
def test_estimate_number(sales_order):
    assert sales_order.header.estimate_number == "EST5178"


@pytest.mark.integration
def test_payment_term(sales_order):
    assert sales_order.header.payment_term == "COD"


@pytest.mark.integration
def test_line_item_count(sales_order):
    assert len(sales_order.line_items) > 20, (
        f"Expected >20 line items, got {len(sales_order.line_items)}"
    )


@pytest.mark.integration
def test_subtotal(sales_order):
    assert sales_order.subtotal == pytest.approx(8099.54)


@pytest.mark.integration
def test_tax_total(sales_order):
    assert sales_order.tax_total == pytest.approx(0.0)


@pytest.mark.integration
def test_total(sales_order):
    assert sales_order.total == pytest.approx(8099.54)


@pytest.mark.integration
def test_fee_items_present(sales_order):
    fees = [li for li in sales_order.line_items if li.is_fee]
    assert fees, "Expected at least one fee line item"


@pytest.mark.integration
def test_accessory_items_present(sales_order):
    accs = [li for li in sales_order.line_items if li.is_accessory]
    assert accs, "Expected at least one accessory line item"


@pytest.mark.integration
def test_cabinet_items_present(sales_order):
    cabinets = [li for li in sales_order.line_items
                if not li.is_fee and not li.is_accessory]
    assert cabinets, "Expected at least one cabinet line item"


@pytest.mark.integration
def test_fee_not_accessory(sales_order):
    # Fee items must not also be classified as accessories
    for li in sales_order.line_items:
        if li.is_fee:
            assert not li.is_accessory, f"{li.sku} is both fee and accessory"


@pytest.mark.integration
def test_assembly_fee_line(sales_order):
    assembly = [li for li in sales_order.line_items if li.sku == "Assembly Fee"]
    assert assembly, "Assembly Fee line item missing"
    assert assembly[0].is_fee
    assert assembly[0].qty == 17
    assert assembly[0].unit_price == pytest.approx(30.00)


@pytest.mark.integration
def test_cabinet_sku_format(sales_order):
    cabinets = [li for li in sales_order.line_items
                if not li.is_fee and not li.is_accessory]
    for li in cabinets:
        assert '-' in li.sku, f"Cabinet SKU missing hyphen: {li.sku!r}"


@pytest.mark.integration
def test_accessory_sku_prefix(sales_order):
    accs = [li for li in sales_order.line_items if li.is_accessory]
    for li in accs:
        assert li.sku.startswith("Accs-"), f"Accessory SKU wrong prefix: {li.sku!r}"


@pytest.mark.integration
def test_line_numbers_sequential(sales_order):
    nums = [li.line for li in sales_order.line_items]
    assert nums == list(range(1, len(nums) + 1))


@pytest.mark.integration
def test_source_file(sales_order):
    assert sales_order.source_file == "SO86708_Aria_Joey.pdf"


@pytest.mark.integration
def test_extracted_at_iso_datetime(sales_order):
    # Should be parseable as ISO datetime
    datetime.datetime.fromisoformat(sales_order.extracted_at)


@pytest.mark.integration
def test_output_serialises_to_json(sales_order):
    d = asdict(sales_order)
    s = json.dumps(d)
    parsed = json.loads(s)
    assert parsed["header"]["order_number"] == "SO86708"
    assert parsed["total"] == pytest.approx(8099.54)
    assert len(parsed["line_items"]) > 20


@pytest.mark.integration
def test_cli_creates_output_file(tmp_path):
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "so_extractor.py"),
         "--so", str(SO_FILE),
         "--project", "test_joey",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
    out_file = tmp_path / "test_joey" / "sales_order.json"
    assert out_file.exists(), "sales_order.json not created"
    data = json.loads(out_file.read_text())
    assert data["header"]["order_number"] == "SO86708"
    assert data["total"] == pytest.approx(8099.54)


@pytest.mark.integration
def test_cli_summary_output(tmp_path):
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "so_extractor.py"),
         "--so", str(SO_FILE),
         "--project", "test_joey",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0
    assert "SO86708" in result.stdout
    assert "8,099.54" in result.stdout
