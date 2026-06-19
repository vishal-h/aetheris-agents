import json
import subprocess
import sys
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from generate_xlsx import generate_xlsx

USE_CASE_ROOT = Path(__file__).parent.parent


# --- fixture ---

@pytest.fixture
def simple_spec():
    return {
        "title": "Test Doc",
        "template_id": "test/v1",
        "output_formats": ["xlsx"],
        "sheets": [
            {
                "name": "Items",
                "header_row": 2,
                "columns": [
                    {"name": "Code", "type": "string",   "width": 12},
                    {"name": "Qty",  "type": "number",   "width": 8},
                    {"name": "Cost", "type": "currency", "width": 10},
                ],
                "merge_ranges": [
                    {"row": 1, "col_start": 1, "col_end": 3, "value": "Test Sheet Title"}
                ],
                "rows": [
                    {
                        "type": "header",
                        "cells": [
                            {"value": "Code", "bold": True,  "align": "left"},
                            {"value": "Qty",  "bold": True,  "align": "right"},
                            {"value": "Cost", "bold": True,  "align": "right"},
                        ],
                    },
                    {
                        "type": "data",
                        "cells": [
                            {"value": "A-01",   "bold": False, "align": "left"},
                            {"value": "5",      "bold": False, "align": "right"},
                            {"value": "250.00", "bold": False, "align": "right"},
                        ],
                    },
                    {
                        "type": "data",
                        "cells": [
                            {"value": "B-02",   "bold": False, "align": "left"},
                            {"value": "3",      "bold": False, "align": "right"},
                            {"value": "150.00", "bold": False, "align": "right"},
                        ],
                    },
                    {
                        "type": "aggregate",
                        "cells": [
                            {"value": "",     "bold": True, "align": "left"},
                            {"value": 8,      "bold": True, "align": "right"},
                            {"value": 400,    "bold": True, "align": "right"},
                        ],
                    },
                ],
            },
            {
                "name": "Summary",
                "header_row": 1,
                "columns": [
                    {"name": "Metric", "type": "string", "width": 18},
                    {"name": "Value",  "type": "string", "width": 12},
                ],
                "merge_ranges": [],
                "rows": [
                    {
                        "type": "header",
                        "cells": [
                            {"value": "Metric", "bold": True, "align": "left"},
                            {"value": "Value",  "bold": True, "align": "right"},
                        ],
                    },
                    {
                        "type": "data",
                        "cells": [
                            {"value": "Total Items", "bold": True,  "align": "left"},
                            {"value": 2,             "bold": False, "align": "right"},
                        ],
                    },
                ],
            },
        ],
    }


# --- unit tests ---

@pytest.mark.integration
def test_file_created(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    assert out.exists()
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_sheet_count_and_names(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Items", "Summary"]


@pytest.mark.integration
def test_merge_range_value(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    assert ws.cell(row=1, column=1).value == "Test Sheet Title"


@pytest.mark.integration
def test_merge_range_is_merged(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    merged = [str(r) for r in ws.merged_cells.ranges]
    assert any("A1" in r for r in merged)


@pytest.mark.integration
def test_header_row_at_correct_position(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # header_row = 2 → row 2 col 1 = "Code"
    assert ws.cell(row=2, column=1).value == "Code"


@pytest.mark.integration
def test_header_cells_bold(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    assert ws.cell(row=2, column=1).font.bold is True
    assert ws.cell(row=2, column=2).font.bold is True


@pytest.mark.integration
def test_data_cell_value(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # data row 1 is at row 3 (header_row=2, offset 1)
    assert ws.cell(row=3, column=1).value == "A-01"


@pytest.mark.integration
def test_numeric_string_converted_to_float(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # "250.00" in currency column → numeric (openpyxl may return int for whole numbers)
    assert isinstance(ws.cell(row=3, column=3).value, (int, float))
    assert ws.cell(row=3, column=3).value == pytest.approx(250.0)


@pytest.mark.integration
def test_numeric_column_has_number_format(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    assert ws.cell(row=3, column=3).number_format == "#,##0.00"


@pytest.mark.integration
def test_aggregate_row_bold(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # aggregate row: header_row=2, 1 header + 2 data + 1 agg → row 5
    agg_row = 2 + 3
    assert ws.cell(row=agg_row, column=2).font.bold is True


@pytest.mark.integration
def test_aggregate_row_top_border(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    agg_row = 2 + 3
    border = ws.cell(row=agg_row, column=2).border
    assert border.top.style == "thin"


@pytest.mark.integration
def test_column_width_applied(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    assert ws.column_dimensions["A"].width == 12
    assert ws.column_dimensions["B"].width == 8


@pytest.mark.integration
def test_no_border_on_data_row(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # data row at row 3 — no top border
    border = ws.cell(row=3, column=1).border
    assert border.top.style is None


# --- CLI integration ---

@pytest.mark.integration
def test_cli_produces_file(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert fetch.returncode == 0

    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert compute.returncode == 0

    render = subprocess.run(
        [sys.executable, "scripts/generate_xlsx.py",
         "--output-dir", str(tmp_path), "--filename", "test_proposal"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0
    out = tmp_path / "test_proposal.xlsx"
    assert out.exists()
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_cli_prints_output_path(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_xlsx.py",
         "--output-dir", str(tmp_path), "--filename", "out"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0
    assert render.stdout.strip().endswith("out.xlsx")


@pytest.mark.integration
def test_cli_proposal_two_sheets(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_xlsx.py",
         "--output-dir", str(tmp_path), "--filename", "prop"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0
    wb = openpyxl.load_workbook(tmp_path / "prop.xlsx")
    assert wb.sheetnames == ["Line Items", "Summary"]


@pytest.mark.integration
def test_cli_proposal_data_row_count(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_xlsx.py",
         "--output-dir", str(tmp_path), "--filename", "prop"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    wb = openpyxl.load_workbook(tmp_path / "prop.xlsx")
    ws = wb["Line Items"]
    # row 1: merge title; row 2: headers; rows 3-12: 10 data; row 13: aggregate
    assert ws.cell(row=13, column=2).value == "TOTAL"
    assert ws.cell(row=3, column=1).value == "SRV-001"
