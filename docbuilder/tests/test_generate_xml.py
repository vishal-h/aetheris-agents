import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from generate_xml import generate_xml

USE_CASE_ROOT = Path(__file__).parent.parent


@pytest.fixture
def simple_spec():
    return {
        "title": "Test Report",
        "sheets": [
            {
                "name": "Items",
                "header_row": 1,
                "columns": [{"name": "Code", "type": "string", "width": 10},
                             {"name": "Amount", "type": "currency", "width": 10}],
                "merge_ranges": [],
                "rows": [
                    {"type": "header",    "cells": [{"value": "Code",   "bold": True,  "align": "left"},
                                                     {"value": "Amount", "bold": True,  "align": "right"}]},
                    {"type": "data",      "cells": [{"value": "A-01",   "bold": False, "align": "left"},
                                                     {"value": "250.00", "bold": False, "align": "right"}]},
                    {"type": "aggregate", "cells": [{"value": "Total",  "bold": True,  "align": "left"},
                                                     {"value": 250,      "bold": True,  "align": "right"}]},
                ],
            }
        ],
    }


# --- unit tests ---

def test_output_is_valid_xml(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    root = ET.parse(str(out)).getroot()
    assert root.tag == "document"


def test_title_as_attribute(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    root = ET.parse(str(out)).getroot()
    assert root.get("title") == "Test Report"


def test_sheet_name_attribute(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    root = ET.parse(str(out)).getroot()
    sheets = root.findall("sheet")
    assert len(sheets) == 1
    assert sheets[0].get("name") == "Items"


def test_row_type_attribute(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    root = ET.parse(str(out)).getroot()
    sheet = root.find("sheet")
    rows = sheet.findall("row")
    types = [r.get("type") for r in rows]
    assert types == ["header", "data", "aggregate"]


def test_cell_values_as_text(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    root = ET.parse(str(out)).getroot()
    cells = root.findall(".//cell")
    values = [c.text for c in cells]
    assert "Code" in values
    assert "A-01" in values
    assert "250" in values


def test_no_bold_in_xml(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    text = out.read_text()
    assert "bold" not in text


def test_no_align_in_xml(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    text = out.read_text()
    assert "align" not in text


def test_numeric_value_stringified(tmp_path, simple_spec):
    out = tmp_path / "out.xml"
    generate_xml(simple_spec, out)
    root = ET.parse(str(out)).getroot()
    cells = root.findall(".//cell")
    values = [c.text for c in cells]
    assert "250" in values


def test_special_chars_escaped(tmp_path):
    spec = {
        "title": "T",
        "sheets": [{
            "name": "S",
            "header_row": 1,
            "columns": [{"name": "C", "type": "string", "width": 10}],
            "merge_ranges": [],
            "rows": [{"type": "data",
                      "cells": [{"value": "<tag>& more", "bold": False, "align": "left"}]}],
        }],
    }
    out = tmp_path / "out.xml"
    generate_xml(spec, out)
    root = ET.parse(str(out)).getroot()
    cell = root.find(".//cell")
    assert cell.text == "<tag>& more"


def test_file_created(tmp_path, simple_spec):
    out = tmp_path / "doc.xml"
    generate_xml(simple_spec, out)
    assert out.exists()
    assert out.stat().st_size > 0


# --- CLI integration ---

@pytest.mark.integration
def test_cli_produces_file(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert fetch.returncode == 0
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert compute.returncode == 0
    render = subprocess.run(
        [sys.executable, "scripts/generate_xml.py",
         "--output-dir", str(tmp_path), "--filename", "report"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    out = tmp_path / "report.xml"
    assert out.exists()
    root = ET.parse(str(out)).getroot()
    assert root.tag == "document"


@pytest.mark.integration
def test_cli_prints_output_path(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_xml.py",
         "--output-dir", str(tmp_path), "--filename", "out"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    assert render.stdout.strip().endswith("out.xml")
