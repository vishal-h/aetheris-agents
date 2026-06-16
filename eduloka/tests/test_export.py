"""Stage-4b export tests.

All tests are offline — no DB, no psycopg required.
"""

import json
import subprocess
import sys
from pathlib import Path

from edux_record import EduxRecord
from export_institute import _run

USE_CASE_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"

GWS_CSE_COLUMNS = {"link", "title", "snippet", "image", "search_term", "status", "metatags", "enrichment"}


def _rec(**kwargs):
    defaults = dict(
        link="https://iitm.ac.in", title="IIT Madras", snippet="Tech.",
        image="https://iitm.ac.in/logo.png", search_term="edu.in", status=1,
        metatags=[{"og:title": "IIT"}], enrichment={"domain": {"tld": "in", "_v": 1}},
    )
    defaults.update(kwargs)
    return EduxRecord(**defaults)


# ---------------------------------------------------------------------------
# Row projection
# ---------------------------------------------------------------------------

def test_exported_row_has_gws_cse_columns(tmp_path):
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(_rec().to_dict()) + "\n")
    out_file = tmp_path / "export.jsonl"
    _run(in_file, out_file)
    row = json.loads(out_file.read_text().strip())
    assert set(row) == GWS_CSE_COLUMNS


def test_exported_row_excludes_text(tmp_path):
    rec = _rec()
    rec.text = "full page body — must not leak into export"
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(rec.to_dict()) + "\n")
    out_file = tmp_path / "export.jsonl"
    _run(in_file, out_file)
    row = json.loads(out_file.read_text().strip())
    assert "text" not in row


def test_metatags_is_list_in_export(tmp_path):
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(_rec().to_dict()) + "\n")
    out_file = tmp_path / "export.jsonl"
    _run(in_file, out_file)
    row = json.loads(out_file.read_text().strip())
    assert isinstance(row["metatags"], list)


def test_enrichment_is_dict_in_export(tmp_path):
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(_rec().to_dict()) + "\n")
    out_file = tmp_path / "export.jsonl"
    _run(in_file, out_file)
    row = json.loads(out_file.read_text().strip())
    assert isinstance(row["enrichment"], dict)


def test_status_preserved_in_export(tmp_path):
    rec = _rec(status=0)
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(rec.to_dict()) + "\n")
    out_file = tmp_path / "export.jsonl"
    _run(in_file, out_file)
    row = json.loads(out_file.read_text().strip())
    assert row["status"] == 0


def test_multiple_records_exported(tmp_path):
    recs = [_rec(link="https://iitm.ac.in"), _rec(link="https://iitb.ac.in", title="IIT Bombay")]
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text("\n".join(json.dumps(r.to_dict()) for r in recs) + "\n")
    out_file = tmp_path / "export.jsonl"
    result = _run(in_file, out_file)
    assert result["exported"] == 2
    assert result["skipped"] == 0
    rows = [json.loads(ln) for ln in out_file.read_text().splitlines() if ln.strip()]
    assert len(rows) == 2


def test_malformed_line_skipped(tmp_path):
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(_rec().to_dict()) + "\n{bad json\n")
    out_file = tmp_path / "export.jsonl"
    result = _run(in_file, out_file)
    assert result["exported"] == 1
    assert result["skipped"] == 1


def test_empty_input_ok(tmp_path):
    in_file = tmp_path / "empty.jsonl"
    in_file.write_text("")
    out_file = tmp_path / "export.jsonl"
    result = _run(in_file, out_file)
    assert result["exported"] == 0
    assert result["skipped"] == 0


# ---------------------------------------------------------------------------
# Fixture smoke test
# ---------------------------------------------------------------------------

def test_exa_fixture_roundtrip(tmp_path):
    out_file = tmp_path / "exa_export.jsonl"
    result = _run(FIXTURES / "exa.edux.jsonl", out_file)
    assert result["exported"] >= 1
    assert result["skipped"] == 0
    for line in out_file.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        assert set(row) == GWS_CSE_COLUMNS
        assert "text" not in row


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_missing_input_exits_1():
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "export_institute.py"),
         "--in", "/tmp/nonexistent_eduloka_export.jsonl"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"


def test_cli_partial_exits_1(tmp_path):
    in_file = tmp_path / "bad.jsonl"
    in_file.write_text("{bad json\n")
    out_file = tmp_path / "export.jsonl"
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "export_institute.py"),
         "--in", str(in_file), "--out", str(out_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "partial"


def test_cli_ok_exit_0(tmp_path):
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(_rec().to_dict()) + "\n")
    out_file = tmp_path / "export.jsonl"
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "export_institute.py"),
         "--in", str(in_file), "--out", str(out_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "ok"
    assert data["exported"] == 1
