import subprocess
import sys
from pathlib import Path

import pytest

from generate_csv import generate_csv

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
                    {"type": "header",    "cells": [{"value": "Code",    "bold": True,  "align": "left"},
                                                     {"value": "Amount",  "bold": True,  "align": "right"}]},
                    {"type": "data",      "cells": [{"value": "A-01",    "bold": False, "align": "left"},
                                                     {"value": "100.00",  "bold": False, "align": "right"}]},
                    {"type": "aggregate", "cells": [{"value": "Total",   "bold": True,  "align": "left"},
                                                     {"value": 100,       "bold": True,  "align": "right"}]},
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
                    {"type": "header", "cells": [{"value": "A", "bold": True, "align": "left"}]},
                    {"type": "data",   "cells": [{"value": "x", "bold": False, "align": "left"}]},
                ],
            },
            {
                "name": "Sheet2",
                "header_row": 1,
                "columns": [{"name": "B", "type": "string", "width": 8}],
                "merge_ranges": [],
                "rows": [
                    {"type": "header", "cells": [{"value": "B", "bold": True, "align": "left"}]},
                    {"type": "data",   "cells": [{"value": "y", "bold": False, "align": "left"}]},
                ],
            },
        ],
    }


# --- unit tests ---

def test_single_sheet_no_separator(tmp_path, simple_spec):
    out = tmp_path / "out.csv"
    generate_csv(simple_spec, out)
    text = out.read_text()
    assert "# Sheet:" not in text


def test_single_sheet_rows_present(tmp_path, simple_spec):
    out = tmp_path / "out.csv"
    generate_csv(simple_spec, out)
    lines = [l for l in out.read_text().splitlines() if l]
    assert lines[0] == "Code,Amount"
    assert lines[1] == "A-01,100.00"
    assert lines[2] == "Total,100"


def test_multi_sheet_separator_comment(tmp_path, multi_sheet_spec):
    out = tmp_path / "out.csv"
    generate_csv(multi_sheet_spec, out)
    text = out.read_text()
    assert "# Sheet: Sheet1" in text
    assert "# Sheet: Sheet2" in text


def test_multi_sheet_blank_line_between(tmp_path, multi_sheet_spec):
    out = tmp_path / "out.csv"
    generate_csv(multi_sheet_spec, out)
    text = out.read_text()
    idx1 = text.index("# Sheet: Sheet1")
    idx2 = text.index("# Sheet: Sheet2")
    between = text[idx1:idx2]
    assert "\n\n" in between


def test_multi_sheet_both_rows_present(tmp_path, multi_sheet_spec):
    out = tmp_path / "out.csv"
    generate_csv(multi_sheet_spec, out)
    text = out.read_text()
    assert "x" in text
    assert "y" in text


def test_numeric_value_stringified(tmp_path, simple_spec):
    out = tmp_path / "out.csv"
    generate_csv(simple_spec, out)
    assert "100" in out.read_text()


def test_file_created(tmp_path, simple_spec):
    out = tmp_path / "doc.csv"
    generate_csv(simple_spec, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_special_chars_quoted(tmp_path):
    spec = {
        "title": "T",
        "sheets": [{
            "name": "S",
            "header_row": 1,
            "columns": [{"name": "C", "type": "string", "width": 10}],
            "merge_ranges": [],
            "rows": [{"type": "data",
                      "cells": [{"value": 'say "hello"', "bold": False, "align": "left"}]}],
        }],
    }
    out = tmp_path / "out.csv"
    generate_csv(spec, out)
    text = out.read_text()
    assert '"say ""hello"""' in text


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
        [sys.executable, "scripts/generate_csv.py",
         "--output-dir", str(tmp_path), "--filename", "report"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    assert (tmp_path / "report.csv").exists()


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
        [sys.executable, "scripts/generate_csv.py",
         "--output-dir", str(tmp_path), "--filename", "out"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert render.returncode == 0
    assert render.stdout.strip().endswith("out.csv")
