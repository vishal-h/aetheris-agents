import json
import subprocess
import sys
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from generate_xlsx import generate_xlsx

USE_CASE_ROOT = Path(__file__).parent.parent
DEMO_XLSX = USE_CASE_ROOT / "data" / "templates" / "demo" / "proposal_v1.xlsx"


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
def test_currency_column_has_dollar_number_format(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # Cost column (3) is currency → "$"#,##0.00 so it renders $250.00.
    assert ws.cell(row=3, column=3).number_format == '"$"#,##0.00'


@pytest.mark.integration
def test_number_column_has_no_forced_decimals(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # Qty column (2) is number → #,##0.## so a count of 5 shows "5", not "5.00".
    assert ws.cell(row=3, column=2).number_format == "#,##0.##"


@pytest.mark.integration
def test_currency_aggregate_has_dollar_number_format(tmp_path, simple_spec):
    out = tmp_path / "out.xlsx"
    generate_xlsx(simple_spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Items"]
    # aggregate row at row 5 (header_row=2 + 1 header + 2 data); Cost total cell.
    assert ws.cell(row=5, column=3).number_format == '"$"#,##0.00'
    assert ws.cell(row=5, column=3).value == pytest.approx(400.0)


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
    # demo template now sets header_row=3 (explicit, honoured by compute_doc).
    # Fresh-workbook layout: row 1 merge title, row 2 empty, row 3 headers,
    # rows 4-13: 10 data, row 14: aggregate.
    assert ws.cell(row=14, column=2).value == "TOTAL"
    assert ws.cell(row=4, column=1).value == "SRV-001"
    assert ws.cell(row=3, column=1).value == "Item Code"


# --- base file support (m2a t2) ---

@pytest.fixture
def branded_spec():
    """A Line Items spec matching the committed demo base file: 5 columns,
    header_row=3, a merge_range on row 1 (base-file-owned, must be skipped)."""
    return {
        "title": "B2B Project Proposal",
        "template_id": "demo/proposal_v1",
        "output_formats": ["xlsx"],
        "sheets": [
            {
                "name": "Line Items",
                "header_row": 3,
                "columns": [
                    {"name": "Item Code",   "type": "string",   "width": 12},
                    {"name": "Description", "type": "string",   "width": 35},
                    {"name": "Quantity",    "type": "number",   "width": 10},
                    {"name": "Unit Price",  "type": "currency", "width": 12},
                    {"name": "Total",       "type": "currency", "width": 14},
                ],
                "merge_ranges": [
                    {"row": 1, "col_start": 1, "col_end": 5,
                     "value": "B2B Project Proposal — Line Items"}
                ],
                "rows": [
                    {"type": "header", "cells": [
                        {"value": "Item Code",   "bold": True, "align": "left"},
                        {"value": "Description", "bold": True, "align": "left"},
                        {"value": "Quantity",    "bold": True, "align": "right"},
                        {"value": "Unit Price",  "bold": True, "align": "right"},
                        {"value": "Total",       "bold": True, "align": "right"},
                    ]},
                    {"type": "data", "cells": [
                        {"value": "SRV-001",    "bold": False, "align": "left"},
                        {"value": "Consulting", "bold": False, "align": "left"},
                        {"value": "2",          "bold": False, "align": "right"},
                        {"value": "1500.00",    "bold": False, "align": "right"},
                        {"value": "3000.00",    "bold": True,  "align": "right"},
                    ]},
                ],
            }
        ],
    }


@pytest.mark.integration
def test_base_file_absent_creates_fresh_workbook(tmp_path, simple_spec):
    # No --base-file → fresh workbook, only the doc spec's sheets present.
    out = tmp_path / "fresh.xlsx"
    generate_xlsx(simple_spec, out, base_file=None)
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Items", "Summary"]


@pytest.mark.integration
def test_base_file_preserves_logo_row(tmp_path, branded_spec):
    out = tmp_path / "branded.xlsx"
    generate_xlsx(branded_spec, out, base_file=str(DEMO_XLSX))
    wb = openpyxl.load_workbook(out)
    ws = wb["Line Items"]
    # Base file branding in rows 1-2 must survive untouched.
    assert ws.cell(row=1, column=1).value == "[ LOGO ]"
    assert ws.cell(row=1, column=2).value == "Company Name"


@pytest.mark.integration
def test_base_file_merge_above_header_row_skipped(tmp_path, branded_spec):
    # The spec's merge_range is on row 1 (< header_row 3) — base-file-owned.
    # It must NOT be written, so the logo at A1 is preserved (not overwritten
    # with the merge value).
    out = tmp_path / "branded.xlsx"
    generate_xlsx(branded_spec, out, base_file=str(DEMO_XLSX))
    wb = openpyxl.load_workbook(out)
    ws = wb["Line Items"]
    assert ws.cell(row=1, column=1).value == "[ LOGO ]"
    assert ws.cell(row=1, column=1).value != "B2B Project Proposal — Line Items"


@pytest.mark.integration
def test_base_file_writes_from_header_row(tmp_path, branded_spec):
    out = tmp_path / "branded.xlsx"
    generate_xlsx(branded_spec, out, base_file=str(DEMO_XLSX))
    wb = openpyxl.load_workbook(out)
    ws = wb["Line Items"]
    # header_row=3 → column header at row 3, first data row at row 4.
    assert ws.cell(row=3, column=1).value == "Item Code"
    assert ws.cell(row=4, column=1).value == "SRV-001"


@pytest.mark.integration
def test_base_file_sheet_not_present_is_created(tmp_path, branded_spec):
    branded_spec["sheets"].append({
        "name": "Extra",
        "header_row": 1,
        "columns": [{"name": "Key", "type": "string", "width": 10}],
        "merge_ranges": [],
        "rows": [
            {"type": "header", "cells": [{"value": "Key", "bold": True, "align": "left"}]},
            {"type": "data",   "cells": [{"value": "v1",  "bold": False, "align": "left"}]},
        ],
    })
    out = tmp_path / "branded.xlsx"
    generate_xlsx(branded_spec, out, base_file=str(DEMO_XLSX))
    wb = openpyxl.load_workbook(out)
    assert "Extra" in wb.sheetnames
    assert wb["Extra"].cell(row=1, column=1).value == "Key"
    assert wb["Extra"].cell(row=2, column=1).value == "v1"


@pytest.mark.integration
def test_data_col_start_skips_left_columns(tmp_path):
    # data_col_start=2 → column A untouched, data grid begins at column B.
    spec = {
        "title": "T", "template_id": "t/v1", "output_formats": ["xlsx"],
        "data_col_start": 2,
        "sheets": [
            {
                "name": "S",
                "header_row": 1,
                "columns": [
                    {"name": "Code", "type": "string", "width": 10},
                    {"name": "Qty",  "type": "number", "width": 8},
                ],
                "merge_ranges": [],
                "rows": [
                    {"type": "header", "cells": [
                        {"value": "Code", "bold": True, "align": "left"},
                        {"value": "Qty",  "bold": True, "align": "right"},
                    ]},
                    {"type": "data", "cells": [
                        {"value": "A-1", "bold": False, "align": "left"},
                        {"value": "5",   "bold": False, "align": "right"},
                    ]},
                ],
            }
        ],
    }
    out = tmp_path / "shifted.xlsx"
    generate_xlsx(spec, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["S"]
    assert ws.cell(row=1, column=1).value is None       # column A untouched
    assert ws.cell(row=1, column=2).value == "Code"     # data starts at column B
    assert ws.cell(row=2, column=2).value == "A-1"
    # column width applied to B (data_col_start), not A
    assert ws.column_dimensions["B"].width == 10


@pytest.mark.integration
def test_cli_base_file_flag(tmp_path):
    # --base-file end-to-end via the demo pipeline.
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_xlsx.py",
         "--base-file", "data/templates/demo/proposal_v1.xlsx",
         "--output-dir", str(tmp_path), "--filename", "branded"],
        input=compute.stdout, capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0, render.stderr
    wb = openpyxl.load_workbook(tmp_path / "branded.xlsx")
    ws = wb["Line Items"]
    assert ws.cell(row=1, column=1).value == "[ LOGO ]"
    assert ws.cell(row=3, column=1).value == "Item Code"
    assert ws.cell(row=4, column=1).value == "SRV-001"
