"""Tests for classify_documents.py — uses sample_corpus.duckdb fixture."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import classify_documents as cd

SCRIPT = Path(__file__).parent.parent / "scripts" / "classify_documents.py"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"

# A path that exists in f2_file_index in the fixture
KNOWN_PATH = "/data/archive/acme/FY2024/tax_return.pdf"


@pytest.fixture
def db(tmp_path):
    """Copy fixture to tmp_path and return a live connection."""
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    conn = duckdb.connect(str(dest))
    yield conn
    conn.close()


@pytest.fixture
def db_path(tmp_path):
    """Return path to a fresh fixture copy (for CLI tests)."""
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    return dest


# ---------------------------------------------------------------------------
# write_classifications — unit tests
# ---------------------------------------------------------------------------

def test_insert_single_record(db):
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.92, "raw_excerpt": "line1\nline2"}]
    result = cd.write_classifications(db, rec)
    assert result == {"inserted": 1, "skipped": 0}

    row = db.execute(
        "SELECT client, financial_year, doc_type, confidence, status FROM classifications WHERE path = ?",
        [KNOWN_PATH],
    ).fetchone()
    assert row == ("acme", "FY2024", "tax", pytest.approx(0.92, abs=1e-4), "proposed")


def test_status_proposed_at_threshold(db):
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.70}]
    cd.write_classifications(db, rec)
    status = db.execute(
        "SELECT status FROM classifications WHERE path = ?", [KNOWN_PATH]
    ).fetchone()[0]
    assert status == "proposed"


def test_status_needs_review_below_threshold(db):
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.65}]
    cd.write_classifications(db, rec)
    status = db.execute(
        "SELECT status FROM classifications WHERE path = ?", [KNOWN_PATH]
    ).fetchone()[0]
    assert status == "needs_review"


def test_idempotent_second_run_skips(db):
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.92}]
    first = cd.write_classifications(db, rec)
    second = cd.write_classifications(db, rec)
    assert first == {"inserted": 1, "skipped": 0}
    assert second == {"inserted": 0, "skipped": 1}
    count = db.execute(
        "SELECT COUNT(*) FROM classifications WHERE path = ?", [KNOWN_PATH]
    ).fetchone()[0]
    assert count == 1


def test_unknown_path_skipped_with_warning(db, capsys):
    rec = [{"path": "/nonexistent/file.pdf", "client": "acme",
            "financial_year": "FY2024", "doc_type": "tax", "confidence": 0.90}]
    result = cd.write_classifications(db, rec)
    assert result == {"inserted": 0, "skipped": 1}
    captured = capsys.readouterr()
    assert "warning" in captured.err
    assert "/nonexistent/file.pdf" in captured.err


def test_raw_excerpt_truncated_to_500_chars(db):
    long_text = "x" * 600
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.80, "raw_excerpt": long_text}]
    cd.write_classifications(db, rec)
    excerpt = db.execute(
        "SELECT raw_excerpt FROM classifications WHERE path = ?", [KNOWN_PATH]
    ).fetchone()[0]
    assert len(excerpt) == 500


def test_classified_at_is_set(db):
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.80}]
    cd.write_classifications(db, rec)
    classified_at = db.execute(
        "SELECT classified_at FROM classifications WHERE path = ?", [KNOWN_PATH]
    ).fetchone()[0]
    assert classified_at is not None


def test_multiple_records_inserted(db):
    paths = [
        "/data/archive/acme/FY2024/tax_return.pdf",
        "/data/archive/acme/FY2023/annual_report.pdf",
    ]
    recs = [{"path": p, "client": "acme", "financial_year": "FY2024",
             "doc_type": "tax", "confidence": 0.80} for p in paths]
    result = cd.write_classifications(db, recs)
    assert result["inserted"] == 2
    assert result["skipped"] == 0


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_stdin_writes_and_outputs_json(db_path, tmp_path):
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.91}]
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        input=json.dumps(rec),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out == {"inserted": 1, "skipped": 0}


def test_cli_input_file(db_path, tmp_path):
    input_file = tmp_path / "batch.json"
    rec = [{"path": KNOWN_PATH, "client": "acme", "financial_year": "FY2024",
            "doc_type": "tax", "confidence": 0.91}]
    input_file.write_text(json.dumps(rec))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path), "--input", str(input_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["inserted"] == 1


def test_cli_bad_db_exits_1(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", "/nonexistent/path/db.duckdb"],
        input="[]",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "error" in result.stderr
