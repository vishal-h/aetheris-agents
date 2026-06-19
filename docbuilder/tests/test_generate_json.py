import json
import subprocess
import sys
from pathlib import Path

import pytest

from generate_json import generate_json

USE_CASE_ROOT = Path(__file__).parent.parent


@pytest.fixture
def simple_spec():
    return {
        "title": "Test Report",
        "template_id": "test/v1",
        "output_formats": ["json"],
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

def test_output_is_valid_json(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_title_preserved(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    data = json.loads(out.read_text())
    assert data["title"] == "Test Report"


def test_sheet_name_preserved(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    data = json.loads(out.read_text())
    assert data["sheets"][0]["name"] == "Items"


def test_columns_are_name_strings(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    data = json.loads(out.read_text())
    assert data["sheets"][0]["columns"] == ["Code", "Amount"]


def test_rows_are_value_arrays(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    data = json.loads(out.read_text())
    rows = data["sheets"][0]["rows"]
    assert rows[0] == ["Code", "Amount"]
    assert rows[1] == ["A-01", "250.00"]
    assert rows[2] == ["Total", 250]


def test_no_bold_in_output(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    text = out.read_text()
    assert "bold" not in text


def test_no_align_in_output(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    text = out.read_text()
    assert "align" not in text


def test_no_template_id_in_output(tmp_path, simple_spec):
    out = tmp_path / "out.json"
    generate_json(simple_spec, out)
    data = json.loads(out.read_text())
    assert "template_id" not in data
    assert "output_formats" not in data


def test_file_created(tmp_path, simple_spec):
    out = tmp_path / "doc.json"
    generate_json(simple_spec, out)
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
        [sys.executable, "scripts/generate_json.py",
         "--output-dir", str(tmp_path), "--filename", "report"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    out = tmp_path / "report.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert "sheets" in data


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
        [sys.executable, "scripts/generate_json.py",
         "--output-dir", str(tmp_path), "--filename", "out"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    assert render.stdout.strip().endswith("out.json")
