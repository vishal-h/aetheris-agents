import subprocess
import sys
from pathlib import Path

import pytest

from generate_md import generate_md

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


@pytest.fixture
def multi_sheet_spec():
    return {
        "title": "Multi",
        "sheets": [
            {
                "name": "Sheet1",
                "header_row": 1,
                "columns": [{"name": "A", "type": "string", "width": 8}],
                "merge_ranges": [],
                "rows": [
                    {"type": "header", "cells": [{"value": "A", "bold": True,  "align": "left"}]},
                    {"type": "data",   "cells": [{"value": "x", "bold": False, "align": "left"}]},
                ],
            },
            {
                "name": "Sheet2",
                "header_row": 1,
                "columns": [{"name": "B", "type": "string", "width": 8}],
                "merge_ranges": [],
                "rows": [
                    {"type": "header", "cells": [{"value": "B", "bold": True,  "align": "left"}]},
                    {"type": "data",   "cells": [{"value": "y", "bold": False, "align": "left"}]},
                ],
            },
        ],
    }


# --- unit tests ---

def test_title_as_h1(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    text = out.read_text()
    assert "# Test Report" in text


def test_sheet_name_as_h2(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    text = out.read_text()
    assert "## Items" in text


def test_header_separator_row(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    text = out.read_text()
    assert "| --- | --- |" in text


def test_separator_after_header_row(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    lines = [l for l in out.read_text().splitlines() if l.startswith("|")]
    assert lines[0] == "| **Code** | **Amount** |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| A-01 | 250.00 |"


def test_bold_cells_wrapped(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    text = out.read_text()
    assert "**Code**" in text
    assert "**Amount**" in text
    assert "**Total**" in text
    assert "**250**" in text


def test_non_bold_cells_plain(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    text = out.read_text()
    assert "| A-01 |" in text
    assert "| 250.00 |" in text


def test_multi_sheet_both_headings(tmp_path, multi_sheet_spec):
    out = tmp_path / "out.md"
    generate_md(multi_sheet_spec, out)
    text = out.read_text()
    assert "## Sheet1" in text
    assert "## Sheet2" in text


def test_numeric_value_stringified(tmp_path, simple_spec):
    out = tmp_path / "out.md"
    generate_md(simple_spec, out)
    text = out.read_text()
    assert "250" in text


def test_file_created(tmp_path, simple_spec):
    out = tmp_path / "doc.md"
    generate_md(simple_spec, out)
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
        [sys.executable, "scripts/generate_md.py",
         "--output-dir", str(tmp_path), "--filename", "report"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    out = tmp_path / "report.md"
    assert out.exists()
    assert out.stat().st_size > 0


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
        [sys.executable, "scripts/generate_md.py",
         "--output-dir", str(tmp_path), "--filename", "out"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    assert render.stdout.strip().endswith("out.md")
