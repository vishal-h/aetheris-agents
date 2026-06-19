import json
import subprocess
import sys
from pathlib import Path

import pytest

USE_CASE_ROOT = Path(__file__).parent.parent


def test_read_csv_returns_dicts(tmp_path):
    from fetch_data import _read_csv
    csv = tmp_path / "t.csv"
    csv.write_text("a,b\n1,2\n3,4\n")
    rows = _read_csv(csv)
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_read_json_returns_list(tmp_path):
    from fetch_data import _read_json
    j = tmp_path / "t.json"
    j.write_text('[{"x": 1}, {"x": 2}]')
    assert _read_json(j) == [{"x": 1}, {"x": 2}]


def test_read_json_non_array_raises(tmp_path):
    from fetch_data import _read_json
    j = tmp_path / "t.json"
    j.write_text('{"x": 1}')
    with pytest.raises(ValueError, match="top-level array"):
        _read_json(j)


def test_cli_csv_key_and_rows(tmp_path):
    csv = tmp_path / "d.csv"
    csv.write_text("name,qty\nalpha,10\nbeta,20\n")
    result = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "test", str(csv)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["key"] == "test"
    assert len(data["rows"]) == 2
    assert data["rows"][0]["name"] == "alpha"


def test_cli_default_key(tmp_path):
    csv = tmp_path / "d.csv"
    csv.write_text("x\n1\n")
    result = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", str(csv)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["key"] == "main"


def test_cli_missing_file_exits_1(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", str(tmp_path / "nope.csv")],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 1


def test_cli_json_file(tmp_path):
    j = tmp_path / "d.json"
    j.write_text('[{"a": 1}]')
    result = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "--key", "src", str(j)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["key"] == "src"
    assert data["rows"] == [{"a": 1}]


def test_cli_sample_data_has_10_rows():
    result = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data["rows"]) == 10
