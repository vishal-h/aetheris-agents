import json
import subprocess
import sys
from pathlib import Path

import pytest

from compute_doc import _run_aggregate, compute_doc

USE_CASE_ROOT = Path(__file__).parent.parent


# --- helpers ---

def _tmpl(sheets=None, data_sources=None, output_formats=None):
    return {
        "template_id": "test/v1",
        "title": "Test",
        "data_sources": data_sources or [{"key": "main", "type": "csv", "path": "x.csv"}],
        "output_formats": output_formats or ["csv"],
        "sheets": sheets or [],
    }


def _sheet(name, source_key="main", columns=None, aggregate_rows=None,
           merge_ranges=None, summary_rows=None, header_row=None):
    s = {
        "name": name,
        "source_key": source_key,
        "columns": columns or [
            {"name": "Item", "source_field": "item",
             "type": "string", "bold": False, "align": "left", "width": 10}
        ],
        "merge_ranges": merge_ranges or [],
    }
    if aggregate_rows is not None:
        s["aggregate_rows"] = aggregate_rows
    if summary_rows is not None:
        s["summary_rows"] = summary_rows
    if header_row is not None:
        s["header_row"] = header_row
    return s


# --- aggregate function unit tests ---

def test_aggregate_sum():
    assert _run_aggregate(["1", "2", "3"], "sum") == 6.0


def test_aggregate_count_skips_empty():
    assert _run_aggregate(["a", "b", "", "c"], "count") == 3


def test_aggregate_avg():
    assert _run_aggregate(["10", "20", "30"], "avg") == 20.0


def test_aggregate_sum_ignores_non_numeric():
    assert _run_aggregate(["1", "x", "2"], "sum") == 3.0


# --- column mapping ---

def test_data_rows_map_source_fields():
    tmpl = _tmpl(sheets=[_sheet("S", columns=[
        {"name": "Code", "source_field": "code", "type": "string",
         "bold": False, "align": "left", "width": 10},
        {"name": "Val", "source_field": "val", "type": "number",
         "bold": False, "align": "right", "width": 10},
    ])])
    spec = compute_doc(tmpl, {"main": [{"code": "A", "val": "1"}, {"code": "B", "val": "2"}]})
    data = [r for r in spec["sheets"][0]["rows"] if r["type"] == "data"]
    assert data[0]["cells"][0]["value"] == "A"
    assert data[1]["cells"][1]["value"] == "2"


# --- aggregate rows ---

def test_aggregate_row_bottom_position():
    tmpl = _tmpl(sheets=[_sheet("S", columns=[
        {"name": "Item", "source_field": "item", "type": "string",
         "bold": False, "align": "left", "width": 10},
        {"name": "Qty", "source_field": "qty", "type": "number",
         "bold": False, "align": "right", "width": 8},
    ], aggregate_rows=[{
        "position": "bottom",
        "label": "TOTAL",
        "label_column": "item",
        "aggregates": [{"column": "qty", "function": "sum"}],
    }])])
    spec = compute_doc(tmpl, {"main": [{"item": "X", "qty": "5"}, {"item": "Y", "qty": "10"}]})
    rows = spec["sheets"][0]["rows"]
    agg = [r for r in rows if r["type"] == "aggregate"]
    assert len(agg) == 1
    assert agg[0]["cells"][0]["value"] == "TOTAL"
    assert agg[0]["cells"][1]["value"] == 15
    # bottom: last row
    assert rows[-1]["type"] == "aggregate"


def test_aggregate_row_top_position():
    tmpl = _tmpl(sheets=[_sheet("S", columns=[
        {"name": "Item", "source_field": "item", "type": "string",
         "bold": False, "align": "left", "width": 10},
    ], aggregate_rows=[{
        "position": "top",
        "label": "HDR",
        "label_column": "item",
        "aggregates": [],
    }])])
    spec = compute_doc(tmpl, {"main": [{"item": "A"}]})
    types = [r["type"] for r in spec["sheets"][0]["rows"]]
    assert types == ["header", "aggregate", "data"]


def test_aggregate_row_all_cells_bold():
    tmpl = _tmpl(sheets=[_sheet("S", columns=[
        {"name": "C1", "source_field": "c1", "type": "string",
         "bold": False, "align": "left", "width": 10},
        {"name": "C2", "source_field": "c2", "type": "number",
         "bold": False, "align": "right", "width": 10},
    ], aggregate_rows=[{
        "position": "bottom",
        "label": "T",
        "label_column": "c1",
        "aggregates": [{"column": "c2", "function": "sum"}],
    }])])
    spec = compute_doc(tmpl, {"main": [{"c1": "x", "c2": "1"}]})
    agg = [r for r in spec["sheets"][0]["rows"] if r["type"] == "aggregate"][0]
    assert all(cell["bold"] for cell in agg["cells"])


# --- header_row ---

def test_header_row_with_merge():
    tmpl = _tmpl(sheets=[_sheet(
        "S", merge_ranges=[{"row": 1, "col_start": 1, "col_end": 2, "value": "Title"}]
    )])
    spec = compute_doc(tmpl, {"main": []})
    assert spec["sheets"][0]["header_row"] == 2


def test_header_row_no_merge():
    tmpl = _tmpl(sheets=[_sheet("S")])
    spec = compute_doc(tmpl, {"main": []})
    assert spec["sheets"][0]["header_row"] == 1


def test_header_row_explicit_override():
    # Explicit header_row wins over the value computed from merge_ranges
    # (merge on row 1 would otherwise compute header_row == 2).
    tmpl = _tmpl(sheets=[_sheet(
        "S",
        merge_ranges=[{"row": 1, "col_start": 1, "col_end": 2, "value": "Title"}],
        header_row=3,
    )])
    spec = compute_doc(tmpl, {"main": []})
    assert spec["sheets"][0]["header_row"] == 3


def test_header_row_explicit_override_summary_sheet():
    # Override also applies to summary sheets (Pass 2).
    tmpl = _tmpl(sheets=[_sheet(
        "Sum",
        source_key=None,
        columns=[
            {"name": "Metric", "source_field": None, "type": "string",
             "bold": True, "align": "left", "width": 10},
            {"name": "Value", "source_field": None, "type": "string",
             "bold": False, "align": "right", "width": 10},
        ],
        summary_rows=[{"type": "static", "label": "Notes", "value": "x"}],
        header_row=3,
    )])
    spec = compute_doc(tmpl, {})
    assert spec["sheets"][0]["header_row"] == 3


# --- two-pass: summary sheets ---

def test_summary_aggregate_ref():
    tmpl = _tmpl(sheets=[
        _sheet("Data", columns=[
            {"name": "Val", "source_field": "val", "type": "number",
             "bold": False, "align": "right", "width": 10}
        ]),
        {
            "name": "Summary", "source_key": None,
            "columns": [
                {"name": "Metric", "source_field": None, "type": "string",
                 "bold": True, "align": "left", "width": 15},
                {"name": "Value", "source_field": None, "type": "string",
                 "bold": False, "align": "right", "width": 12},
            ],
            "merge_ranges": [],
            "summary_rows": [{
                "type": "aggregate_ref",
                "label": "Total",
                "aggregate": {"source_sheet": "Data", "column": "val", "function": "sum"},
            }],
        },
    ])
    spec = compute_doc(tmpl, {"main": [{"val": "10"}, {"val": "20"}]})
    summary_rows = [r for r in spec["sheets"][1]["rows"] if r["type"] == "data"]
    assert summary_rows[0]["cells"][0]["value"] == "Total"
    assert summary_rows[0]["cells"][1]["value"] == 30


def test_summary_count_ref():
    tmpl = _tmpl(sheets=[
        _sheet("Data", columns=[
            {"name": "Code", "source_field": "code", "type": "string",
             "bold": False, "align": "left", "width": 10}
        ]),
        {
            "name": "Summary", "source_key": None,
            "columns": [
                {"name": "M", "source_field": None, "type": "string",
                 "bold": True, "align": "left", "width": 12},
                {"name": "V", "source_field": None, "type": "string",
                 "bold": False, "align": "right", "width": 10},
            ],
            "merge_ranges": [],
            "summary_rows": [{
                "type": "aggregate_ref",
                "label": "Count",
                "aggregate": {"source_sheet": "Data", "column": "code", "function": "count"},
            }],
        },
    ])
    spec = compute_doc(tmpl, {"main": [{"code": "A"}, {"code": "B"}, {"code": "C"}]})
    data = [r for r in spec["sheets"][1]["rows"] if r["type"] == "data"]
    assert data[0]["cells"][1]["value"] == 3


def test_summary_static_row():
    tmpl = _tmpl(sheets=[
        _sheet("Data"),
        {
            "name": "Summary", "source_key": None,
            "columns": [
                {"name": "M", "source_field": None, "type": "string",
                 "bold": True, "align": "left", "width": 12},
                {"name": "V", "source_field": None, "type": "string",
                 "bold": False, "align": "right", "width": 10},
            ],
            "merge_ranges": [],
            "summary_rows": [{"type": "static", "label": "Notes", "value": "See attached."}],
        },
    ])
    spec = compute_doc(tmpl, {"main": [{"item": "X"}]})
    data = [r for r in spec["sheets"][1]["rows"] if r["type"] == "data"]
    assert data[0]["cells"][0]["value"] == "Notes"
    assert data[0]["cells"][1]["value"] == "See attached."


def test_summary_label_column_bold():
    tmpl = _tmpl(sheets=[
        _sheet("Data"),
        {
            "name": "Summary", "source_key": None,
            "columns": [
                {"name": "M", "source_field": None, "type": "string",
                 "bold": True, "align": "left", "width": 12},
                {"name": "V", "source_field": None, "type": "string",
                 "bold": False, "align": "right", "width": 10},
            ],
            "merge_ranges": [],
            "summary_rows": [{"type": "static", "label": "X", "value": "Y"}],
        },
    ])
    spec = compute_doc(tmpl, {"main": [{"item": "A"}]})
    data = [r for r in spec["sheets"][1]["rows"] if r["type"] == "data"]
    assert data[0]["cells"][0]["bold"] is True
    assert data[0]["cells"][1]["bold"] is False


def test_sheet_order_preserved():
    tmpl = _tmpl(sheets=[_sheet("A"), _sheet("B")])
    spec = compute_doc(tmpl, {"main": []})
    assert [s["name"] for s in spec["sheets"]] == ["A", "B"]


# --- top-level field pass-through (m2a t5) ---

def test_passthrough_defaults_when_absent():
    # A template omitting the m2a fields → doc spec carries the defaults.
    tmpl = _tmpl(sheets=[_sheet("S")])
    spec = compute_doc(tmpl, {"main": []})
    assert spec["table_style"] == "Table Grid"
    assert spec["data_col_start"] == 1
    assert spec["narrative"] is None


def test_passthrough_values_when_present():
    # Explicit m2a fields flow through to the doc spec unchanged.
    tmpl = _tmpl(sheets=[_sheet("S")])
    tmpl["table_style"] = "Light List Accent 1"
    tmpl["data_col_start"] = 2
    tmpl["narrative"] = {"template_file": "p.md.template", "css_file": "p.css"}
    spec = compute_doc(tmpl, {"main": []})
    assert spec["table_style"] == "Light List Accent 1"
    assert spec["data_col_start"] == 2
    assert spec["narrative"] == {"template_file": "p.md.template", "css_file": "p.css"}


# --- error cases ---

def test_multi_source_two_sheets():
    # Two sources, two data-bearing sheets each reading a different source.
    tmpl = _tmpl(
        data_sources=[
            {"key": "a", "type": "csv", "path": "a.csv"},
            {"key": "b", "type": "csv", "path": "b.csv"},
        ],
        sheets=[
            _sheet("A", source_key="a", columns=[
                {"name": "X", "source_field": "x", "type": "string",
                 "bold": False, "align": "left", "width": 10}]),
            _sheet("B", source_key="b", columns=[
                {"name": "Y", "source_field": "y", "type": "string",
                 "bold": False, "align": "left", "width": 10}]),
        ],
    )
    spec = compute_doc(tmpl, {"a": [{"x": "ax"}], "b": [{"y": "by"}]})
    assert [s["name"] for s in spec["sheets"]] == ["A", "B"]
    a_data = [r for r in spec["sheets"][0]["rows"] if r["type"] == "data"]
    b_data = [r for r in spec["sheets"][1]["rows"] if r["type"] == "data"]
    assert a_data[0]["cells"][0]["value"] == "ax"
    assert b_data[0]["cells"][0]["value"] == "by"


def test_source_key_not_provided_raises():
    # A sheet referencing a source_key absent from the provided sources exits 1.
    tmpl = _tmpl(
        data_sources=[
            {"key": "a", "type": "csv", "path": "a.csv"},
            {"key": "b", "type": "csv", "path": "b.csv"},
        ],
        sheets=[_sheet("B", source_key="b")],
    )
    with pytest.raises(ValueError, match="source key 'b' not found in provided sources"):
        compute_doc(tmpl, {"a": []})  # 'b' not provided


def test_missing_source_field_raises():
    tmpl = _tmpl(sheets=[_sheet("S", columns=[
        {"name": "X", "source_field": "missing", "type": "string",
         "bold": False, "align": "left", "width": 10}
    ])])
    with pytest.raises(ValueError, match="source_field 'missing'"):
        compute_doc(tmpl, {"main": [{"other": "val"}]})


def test_summary_unknown_source_sheet_raises():
    tmpl = _tmpl(sheets=[
        _sheet("Data"),
        {
            "name": "Summary", "source_key": None,
            "columns": [
                {"name": "M", "source_field": None, "type": "string",
                 "bold": True, "align": "left", "width": 10},
                {"name": "V", "source_field": None, "type": "string",
                 "bold": False, "align": "right", "width": 10},
            ],
            "merge_ranges": [],
            "summary_rows": [{
                "type": "aggregate_ref",
                "label": "X",
                "aggregate": {"source_sheet": "NoSuchSheet", "column": "val", "function": "sum"},
            }],
        },
    ])
    with pytest.raises(ValueError, match="source_sheet 'NoSuchSheet' not found"):
        compute_doc(tmpl, {"main": [{"item": "A"}]})


def test_sheet_mixing_source_key_and_summary_rows_rejected():
    tmpl = _tmpl(sheets=[{
        "name": "Bad",
        "source_key": "main",
        "columns": [{"name": "X", "source_field": "x", "type": "string",
                     "bold": False, "align": "left", "width": 10}],
        "merge_ranges": [],
        "summary_rows": [{"type": "static", "label": "N", "value": "V"}],
    }])
    with pytest.raises(ValueError, match="source_key and summary_rows"):
        compute_doc(tmpl, {"main": [{"x": "1"}]})


def test_unknown_output_format_rejected():
    tmpl = _tmpl(output_formats=["xlsx", "foobar"])
    with pytest.raises(ValueError, match="unknown output_format 'foobar'"):
        compute_doc(tmpl, {})


# --- CLI integration ---

def test_cli_two_sheet_pipeline(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "main",
         "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert fetch.returncode == 0

    raw = tmp_path / "raw.json"
    raw.write_text(fetch.stdout)

    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", str(raw)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert compute.returncode == 0
    spec = json.loads(compute.stdout)
    assert [s["name"] for s in spec["sheets"]] == ["Line Items", "Summary"]


def test_cli_line_items_sheet_row_counts(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "main",
         "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    raw = tmp_path / "raw.json"
    raw.write_text(fetch.stdout)

    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", str(raw)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    spec = json.loads(compute.stdout)
    li = spec["sheets"][0]
    data_rows = [r for r in li["rows"] if r["type"] == "data"]
    agg_rows = [r for r in li["rows"] if r["type"] == "aggregate"]
    assert len(data_rows) == 10
    assert len(agg_rows) == 1


def test_cli_summary_sheet_resolves_aggregates(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "main",
         "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    raw = tmp_path / "raw.json"
    raw.write_text(fetch.stdout)

    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", str(raw)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    spec = json.loads(compute.stdout)
    summary = spec["sheets"][1]
    data = [r for r in summary["rows"] if r["type"] == "data"]
    # 3 aggregate_ref + 1 static = 4 data rows
    assert len(data) == 4
    # "Total Line Items" = count(item_code) = 10
    assert data[0]["cells"][0]["value"] == "Total Line Items"
    assert data[0]["cells"][1]["value"] == 10
    # "Total Value (USD)" = sum(total) = 21090
    assert data[2]["cells"][1]["value"] == 21090
    # static Notes row
    assert data[3]["cells"][0]["value"] == "Notes"


def test_cli_multi_source_succeeds(tmp_path):
    # The demo template now declares two sources; passing both raw files to
    # compute_doc succeeds and yields the two demo sheets.
    main = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "main",
         "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    summary = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "summary",
         "data/sample_data_summary.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    raw_main = tmp_path / "raw_main.json"
    raw_main.write_text(main.stdout)
    raw_summary = tmp_path / "raw_summary.json"
    raw_summary.write_text(summary.stdout)

    result = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json",
         str(raw_main), str(raw_summary)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    spec = json.loads(result.stdout)
    assert [s["name"] for s in spec["sheets"]] == ["Line Items", "Summary"]


def test_cli_output_flag_writes_file(tmp_path):
    # --output FILE writes the doc spec to the file and prints only the path.
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "main",
         "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    raw = tmp_path / "raw.json"
    raw.write_text(fetch.stdout)
    spec_file = tmp_path / "spec.json"

    result = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", str(raw),
         "--output", str(spec_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    # stdout is just the path, not the JSON blob
    assert result.stdout.strip() == str(spec_file)
    assert "\"sheets\"" not in result.stdout
    # the file holds the full doc spec
    spec = json.loads(spec_file.read_text())
    assert [s["name"] for s in spec["sheets"]] == ["Line Items", "Summary"]


def test_cli_unprovided_source_key_exits_1(tmp_path):
    # A template whose sheet references a source_key that is not provided exits 1.
    tmpl = {
        "template_id": "x", "title": "X",
        "data_sources": [{"key": "b", "type": "csv", "path": "b.csv"}],
        "output_formats": ["csv"],
        "sheets": [{
            "name": "B", "source_key": "b",
            "columns": [{"name": "Y", "source_field": "y", "type": "string",
                         "bold": False, "align": "left", "width": 10}],
            "merge_ranges": [],
        }],
    }
    tmpl_path = tmp_path / "t.json"
    tmpl_path.write_text(json.dumps(tmpl))
    src = tmp_path / "src.json"
    src.write_text(json.dumps({"key": "a", "rows": []}))  # provides 'a', not 'b'

    result = subprocess.run(
        [sys.executable, "scripts/compute_doc.py", str(tmpl_path), str(src)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 1
    assert "source key 'b' not found" in result.stderr
