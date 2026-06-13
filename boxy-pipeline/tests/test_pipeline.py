"""Tests for main.py — t4 end-to-end pipeline."""
import json
import re
import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest

USE_CASE_ROOT = Path(__file__).parent.parent
SAMPLES_DIR = USE_CASE_ROOT / "data" / "samples"
CATALOG_FILE = SAMPLES_DIR / "Updated_Boxy_MSRP_Sales_Order_Form.xlsx"
ELEVATION_PDF = SAMPLES_DIR / "Joey-_Kitchen_2D_Plans_V2.pdf"
FLOOR_PDF = SAMPLES_DIR / "Joey-_Kitchen_Plan_V2.pdf"

_BASE_ARGS = [
    sys.executable, str(USE_CASE_ROOT / "main.py"),
    "--drawings", str(ELEVATION_PDF), str(FLOOR_PDF),
    "--catalog", str(CATALOG_FILE),
    "--template", str(CATALOG_FILE),
    "--project", "Joey_Kitchen_V2",
    "--upper-finish", "2001:Ivory White:2000",
    "--lower-finish", "2004:Mingo Oak:2000",
]


@pytest.fixture(scope="module")
def pipeline_output(tmp_path_factory):
    """Run the full pipeline once; yield (returncode, stdout, stderr, out_dir)."""
    out_dir = tmp_path_factory.mktemp("pipeline_out")
    result = subprocess.run(
        _BASE_ARGS + ["--output-dir", str(out_dir)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    return result.returncode, result.stdout, result.stderr, out_dir


@pytest.mark.integration
def test_pipeline_exits_zero(pipeline_output):
    returncode, _, stderr, _ = pipeline_output
    assert returncode == 0, f"Pipeline failed:\n{stderr}"


@pytest.mark.integration
def test_pipeline_output_file_created(pipeline_output):
    _, _, _, out_dir = pipeline_output
    assert (out_dir / "Joey_Kitchen_V2_order_form.xlsx").exists()


@pytest.mark.integration
def test_pipeline_summary_total_items(pipeline_output):
    """Summary must report ≥10 total items."""
    _, stdout, _, _ = pipeline_output
    m = re.search(r"Items:\s+(\d+) total", stdout)
    assert m, f"Could not find 'Items: N total' in stdout:\n{stdout}"
    total = int(m.group(1))
    assert total >= 10, f"Expected ≥10 total items, got {total}"


@pytest.mark.integration
def test_pipeline_summary_contains_output_path(pipeline_output):
    _, stdout, _, out_dir = pipeline_output
    assert "Joey_Kitchen_V2_order_form.xlsx" in stdout


@pytest.mark.integration
def test_dry_run_prints_json_no_file(tmp_path):
    result = subprocess.run(
        _BASE_ARGS + ["--output-dir", str(tmp_path), "--dry-run"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0, f"Dry run failed:\n{result.stderr}"

    data = json.loads(result.stdout)
    assert "project_name" in data
    assert "resolved" in data
    assert "unresolved_codes" in data
    assert "subtotal" in data
    assert "source_drawings" in data
    assert data["project_name"] == "Joey_Kitchen_V2"
    assert len(data["resolved"]) >= 10

    assert not (tmp_path / "Joey_Kitchen_V2_order_form.xlsx").exists(), (
        "--dry-run must not write an xlsx file"
    )
