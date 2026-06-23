"""Unit + CLI tests for run_log_writer.py (m3 t1).

Pure stdlib — runs in the standard `-m "not integration"` done-check.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from run_log_writer import _load_log, _read_outputs, append_run, build_entry

USE_CASE_ROOT = Path(__file__).parent.parent


@pytest.fixture
def entry():
    return build_entry(
        "bitloka", "invoice", "v1", "run-1",
        {"client_name": "XYZ Inc", "date": "31-May-2026"},
        ["output/xyz_inc_invoice_31-May-2026.pdf"],
        timestamp="2026-06-21T07:27:00+05:30",
    )


# --- append_run ---

def test_append_to_empty():
    assert append_run([], {"run_id": "a"}) == [{"run_id": "a"}]


def test_append_preserves_existing():
    log = append_run([{"run_id": "a"}], {"run_id": "b"})
    assert [e["run_id"] for e in log] == ["a", "b"]


def test_append_idempotent_same_run_id():
    # Same run_id → replaced in place, not duplicated.
    log = append_run([{"run_id": "a", "v": 1}], {"run_id": "a", "v": 2})
    assert log == [{"run_id": "a", "v": 2}]


def test_append_does_not_mutate_input():
    original = [{"run_id": "a"}]
    append_run(original, {"run_id": "b"})
    assert original == [{"run_id": "a"}]


# --- _load_log ---

def test_load_missing_file_returns_empty(tmp_path):
    assert _load_log(tmp_path / "nope.json") == []


def test_load_empty_file_returns_empty(tmp_path):
    p = tmp_path / "log.json"
    p.write_text("")
    assert _load_log(p) == []


def test_load_existing_array(tmp_path):
    p = tmp_path / "log.json"
    p.write_text(json.dumps([{"run_id": "a"}]))
    assert _load_log(p) == [{"run_id": "a"}]


def test_load_malformed_raises(tmp_path):
    p = tmp_path / "log.json"
    p.write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        _load_log(p)


def test_load_non_array_raises(tmp_path):
    p = tmp_path / "log.json"
    p.write_text('{"a": 1}')
    with pytest.raises(ValueError):
        _load_log(p)


# --- build_entry ---

def test_build_entry_shape(entry):
    assert entry["tenant"] == "bitloka"
    assert entry["doc_type"] == "invoice"
    assert entry["variant"] == "v1"
    assert entry["run_id"] == "run-1"
    assert entry["context"]["client_name"] == "XYZ Inc"
    assert entry["outputs"] == ["output/xyz_inc_invoice_31-May-2026.pdf"]
    assert entry["timestamp"] == "2026-06-21T07:27:00+05:30"


def test_build_entry_default_timestamp_is_iso_with_offset():
    e = build_entry("t", "d", "v", "r", {}, [])
    # ISO8601 with a timezone offset, no exception.
    assert "T" in e["timestamp"]
    assert e["timestamp"][-6] in "+-"  # offset like +05:30


# --- _read_outputs ---

def test_read_outputs_from_renamed(tmp_path):
    p = tmp_path / "renamed.json"
    p.write_text(json.dumps([
        {"original": "output/invoice_v1.pdf", "renamed": "output/out.pdf"},
        {"original": "output/invoice_v1.xlsx", "renamed": "output/out.xlsx"},
    ]))
    assert _read_outputs(str(p)) == ["output/out.pdf", "output/out.xlsx"]


def test_read_outputs_none_arg():
    assert _read_outputs(None) == []


def test_read_outputs_missing_file_degrades(tmp_path, capsys):
    assert _read_outputs(str(tmp_path / "nope.json")) == []
    assert "warning" in capsys.readouterr().err


def test_read_outputs_malformed_degrades(tmp_path, capsys):
    p = tmp_path / "renamed.json"
    p.write_text("{bad")
    assert _read_outputs(str(p)) == []
    assert "warning" in capsys.readouterr().err


# --- CLI integration ---

def _run(args, **kw):
    return subprocess.run(
        [sys.executable, "scripts/run_log_writer.py", *args],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), **kw,
    )


def test_cli_appends_and_creates_file(tmp_path):
    log = tmp_path / "run_log.json"
    renamed = tmp_path / "renamed.json"
    renamed.write_text(json.dumps([
        {"original": "output/invoice_v1.pdf", "renamed": "output/out.pdf"}]))
    r = _run([
        "--tenant", "bitloka", "--doc-type", "invoice", "--variant", "v1",
        "--run-id", "run-xyz", "--context", '{"client_name":"XYZ Inc","date":"31-May-2026"}',
        "--renamed", str(renamed), "--log-file", str(log)])
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(log)
    data = json.loads(log.read_text())
    assert len(data) == 1
    assert data[0]["run_id"] == "run-xyz"
    assert data[0]["tenant"] == "bitloka"
    assert data[0]["context"]["client_name"] == "XYZ Inc"
    assert data[0]["outputs"] == ["output/out.pdf"]


def test_cli_appends_second_entry(tmp_path):
    log = tmp_path / "run_log.json"
    base = ["--tenant", "bitloka", "--doc-type", "invoice", "--variant", "v1",
            "--context", "{}", "--log-file", str(log)]
    assert _run([*base, "--run-id", "run-1"]).returncode == 0
    assert _run([*base, "--run-id", "run-2"]).returncode == 0
    data = json.loads(log.read_text())
    assert [e["run_id"] for e in data] == ["run-1", "run-2"]


def test_cli_idempotent_rerun(tmp_path):
    log = tmp_path / "run_log.json"
    args = ["--tenant", "bitloka", "--doc-type", "invoice", "--variant", "v1",
            "--run-id", "run-1", "--context", "{}", "--log-file", str(log)]
    _run(args)
    _run(args)
    data = json.loads(log.read_text())
    assert len(data) == 1  # same run_id → not duplicated


def test_cli_invalid_context_exits_1(tmp_path):
    r = _run([
        "--tenant", "t", "--doc-type", "d", "--variant", "v",
        "--run-id", "r", "--context", "{bad json", "--log-file", str(tmp_path / "l.json")])
    assert r.returncode == 1
    assert "error" in r.stderr


def test_cli_corrupt_existing_log_exits_1(tmp_path):
    log = tmp_path / "run_log.json"
    log.write_text('{"not": "array"}')
    r = _run([
        "--tenant", "t", "--doc-type", "d", "--variant", "v",
        "--run-id", "r", "--context", "{}", "--log-file", str(log)])
    assert r.returncode == 1
    assert "error" in r.stderr


def test_cli_missing_renamed_still_succeeds(tmp_path):
    # No --renamed → outputs:[] but the entry is still written (exit 0).
    log = tmp_path / "run_log.json"
    r = _run([
        "--tenant", "bitloka", "--doc-type", "invoice", "--variant", "v1",
        "--run-id", "run-1", "--context", "{}", "--log-file", str(log)])
    assert r.returncode == 0, r.stderr
    assert json.loads(log.read_text())[0]["outputs"] == []
