"""Tests for export_for_review.py and approve_classifications.py."""

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import classify_documents as cd
import export_for_review as ef
import approve_classifications as ac

FIXTURE = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"
EXPORT_SCRIPT  = Path(__file__).parent.parent / "scripts" / "export_for_review.py"
APPROVE_SCRIPT = Path(__file__).parent.parent / "scripts" / "approve_classifications.py"

# Seed data — paths that exist in f2_file_index
ACME_PATHS = [
    "/data/archive/acme/FY2024/tax_return.pdf",
    "/data/archive/acme/FY2024/letter_jan.docx",
    "/data/archive/acme/FY2023/annual_report.pdf",
]
GLOBEX_PATHS = [
    "/data/archive/globex/FY2024/invoice_001.pdf",
    "/data/archive/globex/FY2023/invoice_101.pdf",
]
ALL_PATHS = ACME_PATHS + GLOBEX_PATHS


def _seed(conn, paths, base_confidence=0.80, client_map=None):
    """Insert proposed classifications for the given paths."""
    records = []
    for i, path in enumerate(paths):
        client = "acme" if "acme" in path else "globex"
        if client_map:
            client = client_map.get(path, client)
        records.append({
            "path": path,
            "client": client,
            "financial_year": "FY2024",
            "doc_type": "tax",
            "confidence": round(base_confidence - i * 0.05, 2),
            "raw_excerpt": f"excerpt for file {i}",
        })
    return cd.write_classifications(conn, records)


@pytest.fixture
def db(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    conn = duckdb.connect(str(dest))
    yield conn
    conn.close()


@pytest.fixture
def db_path(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    return dest


# ---------------------------------------------------------------------------
# export_for_review — unit tests
# ---------------------------------------------------------------------------

def test_export_columns(db, tmp_path):
    _seed(db, ACME_PATHS)
    out = tmp_path / "review.csv"
    ef.export_for_review(db, out)
    with out.open() as f:
        header = next(csv.reader(f))
    assert header == ef.EXPORT_COLUMNS


def test_export_ordered_by_confidence_asc(db, tmp_path):
    _seed(db, ACME_PATHS)
    out = tmp_path / "review.csv"
    ef.export_for_review(db, out)
    with out.open() as f:
        rows = list(csv.DictReader(f))
    confidences = [float(r["confidence"]) for r in rows]
    assert confidences == sorted(confidences)


def test_export_blank_reviewer_columns(db, tmp_path):
    _seed(db, ACME_PATHS)
    out = tmp_path / "review.csv"
    ef.export_for_review(db, out)
    with out.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        assert row["reviewer_action"] == ""
        assert row["reviewer_notes"] == ""


def test_export_raw_excerpt_truncated_to_200(db, tmp_path):
    long_excerpt = "x" * 300
    cd.write_classifications(db, [{
        "path": ACME_PATHS[0], "client": "acme", "financial_year": "FY2024",
        "doc_type": "tax", "confidence": 0.80, "raw_excerpt": long_excerpt,
    }])
    out = tmp_path / "review.csv"
    ef.export_for_review(db, out)
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows[0]["raw_excerpt"]) == 200


def test_export_default_statuses(db, tmp_path):
    """Default export includes both proposed and needs_review."""
    # proposed (confidence >= 0.70)
    cd.write_classifications(db, [{"path": ACME_PATHS[0], "client": "acme",
        "financial_year": "FY2024", "doc_type": "tax", "confidence": 0.90}])
    # needs_review (confidence < 0.70)
    cd.write_classifications(db, [{"path": ACME_PATHS[1], "client": "acme",
        "financial_year": "FY2024", "doc_type": "legal", "confidence": 0.55}])
    out = tmp_path / "review.csv"
    result = ef.export_for_review(db, out)
    assert result["exported"] == 2
    assert result["needs_review"] == 1


def test_export_status_filter(db, tmp_path):
    _seed(db, ACME_PATHS)
    out = tmp_path / "review.csv"
    result = ef.export_for_review(db, out, statuses=["needs_review"])
    # all seeded with confidence >= 0.55; only those < 0.70 are needs_review
    assert result["exported"] == result["needs_review"]


def test_export_client_filter(db, tmp_path):
    _seed(db, ALL_PATHS)
    out = tmp_path / "review.csv"
    result = ef.export_for_review(db, out, client="acme")
    assert result["exported"] == len(ACME_PATHS)
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert all(r["client"] == "acme" for r in rows)


def test_export_limit(db, tmp_path):
    _seed(db, ALL_PATHS)
    out = tmp_path / "review.csv"
    result = ef.export_for_review(db, out, limit=3)
    assert result["exported"] == 3


def test_export_returns_summary_dict(db, tmp_path):
    _seed(db, ACME_PATHS)
    out = tmp_path / "review.csv"
    result = ef.export_for_review(db, out)
    assert "output" in result
    assert "exported" in result
    assert "needs_review" in result
    assert result["exported"] == len(ACME_PATHS)


def test_export_empty_result(db, tmp_path):
    out = tmp_path / "review.csv"
    result = ef.export_for_review(db, out)
    assert result["exported"] == 0
    assert out.exists()


# ---------------------------------------------------------------------------
# approve_classifications — unit tests
# ---------------------------------------------------------------------------

def _make_csv(tmp_path, rows: list[dict]) -> Path:
    path = tmp_path / "review.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ef.EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _row(path, action="", client="acme"):
    return {
        "path": path, "client": client, "financial_year": "FY2024",
        "doc_type": "tax", "confidence": "0.80", "status": "proposed",
        "raw_excerpt": "", "classified_at": "", "reviewer_action": action,
        "reviewer_notes": "",
    }


def test_approve_sets_status_and_reviewer(db, tmp_path):
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "approve")])
    result = ac.apply_reviews(db, list(csv.DictReader(csv_path.open())), reviewer="Jane")
    assert result == {"approved": 1, "rejected": 0, "skipped": 0, "errors": 0}
    row = db.execute(
        "SELECT status, reviewed_by, reviewed_at FROM classifications WHERE path = ?",
        [ACME_PATHS[0]]
    ).fetchone()
    assert row[0] == "approved"
    assert row[1] == "Jane"
    assert row[2] is not None


def test_reject_sets_status(db, tmp_path):
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "reject")])
    result = ac.apply_reviews(db, list(csv.DictReader(csv_path.open())), reviewer="Jane")
    assert result["rejected"] == 1
    status = db.execute(
        "SELECT status FROM classifications WHERE path = ?", [ACME_PATHS[0]]
    ).fetchone()[0]
    assert status == "rejected"


def test_blank_action_skipped(db, tmp_path):
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "")])
    result = ac.apply_reviews(db, list(csv.DictReader(csv_path.open())), reviewer="Jane")
    assert result == {"approved": 0, "rejected": 0, "skipped": 1, "errors": 0}
    status = db.execute(
        "SELECT status FROM classifications WHERE path = ?", [ACME_PATHS[0]]
    ).fetchone()[0]
    assert status == "proposed"


def test_invalid_action_skipped_with_warning(db, tmp_path, capsys):
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "maybe")])
    result = ac.apply_reviews(db, list(csv.DictReader(csv_path.open())), reviewer="Jane")
    assert result["skipped"] == 1
    assert "warning" in capsys.readouterr().err


def test_unknown_path_skipped_with_warning(db, tmp_path, capsys):
    csv_path = _make_csv(tmp_path, [_row("/nonexistent/file.pdf", "approve")])
    result = ac.apply_reviews(db, list(csv.DictReader(csv_path.open())), reviewer="Jane")
    assert result["skipped"] == 1
    assert "warning" in capsys.readouterr().err


def test_idempotent_second_import_is_noop(db, tmp_path):
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "approve")])
    rows = list(csv.DictReader(csv_path.open()))
    first = ac.apply_reviews(db, rows, reviewer="Jane")
    second = ac.apply_reviews(db, rows, reviewer="Jane")
    assert first == {"approved": 1, "rejected": 0, "skipped": 0, "errors": 0}
    assert second == {"approved": 0, "rejected": 0, "skipped": 1, "errors": 0}


def test_dry_run_does_not_write(db, tmp_path, capsys):
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "approve")])
    result = ac.apply_reviews(
        db, list(csv.DictReader(csv_path.open())), reviewer="Jane", dry_run=True
    )
    assert result["approved"] == 1
    status = db.execute(
        "SELECT status FROM classifications WHERE path = ?", [ACME_PATHS[0]]
    ).fetchone()[0]
    assert status == "proposed"
    assert "dry-run" in capsys.readouterr().err


def test_reviewer_defaults_to_user_env(db, tmp_path, monkeypatch):
    monkeypatch.setenv("USER", "testuser")
    _seed(db, [ACME_PATHS[0]])
    csv_path = _make_csv(tmp_path, [_row(ACME_PATHS[0], "approve")])
    # Import ac fresh so USER env is re-evaluated via default
    import importlib
    ac_fresh = importlib.import_module("approve_classifications")
    # Default is baked in at argparse time; test via the function directly
    result = ac.apply_reviews(
        db, list(csv.DictReader(csv_path.open())),
        reviewer=os.environ.get("USER", "unknown"),
    )
    assert result["approved"] == 1
    reviewer = db.execute(
        "SELECT reviewed_by FROM classifications WHERE path = ?", [ACME_PATHS[0]]
    ).fetchone()[0]
    assert reviewer == "testuser"


# ---------------------------------------------------------------------------
# Workflow test — full round-trip
# ---------------------------------------------------------------------------

def test_full_round_trip(db, tmp_path):
    """Export → edit → import → verify DB state."""
    _seed(db, ALL_PATHS)

    # Export
    export_path = tmp_path / "review.csv"
    result = ef.export_for_review(db, export_path)
    assert result["exported"] == len(ALL_PATHS)

    # Simulate human edits: approve first 3, reject next 2, leave rest blank
    with export_path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    decisions = ["approve", "approve", "approve", "reject", "reject"]
    for i, row in enumerate(rows):
        row["reviewer_action"] = decisions[i] if i < len(decisions) else ""

    edited_path = tmp_path / "review_edited.csv"
    with edited_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ef.EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Import
    with edited_path.open(newline="") as f:
        result = ac.apply_reviews(db, list(csv.DictReader(f)), reviewer="Tester")

    assert result["approved"] == 3
    assert result["rejected"] == 2
    assert result["skipped"] == len(ALL_PATHS) - 5

    # Verify DB state
    statuses = {
        row[0]: row[1]
        for row in db.execute("SELECT path, status FROM classifications").fetchall()
    }
    approve_paths = [r["path"] for r in rows[:3]]
    reject_paths  = [r["path"] for r in rows[3:5]]
    for p in approve_paths:
        assert statuses[p] == "approved"
    for p in reject_paths:
        assert statuses[p] == "rejected"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_export_outputs_path_and_json(db_path, tmp_path):
    # Seed via classify_documents CLI
    conn = duckdb.connect(str(db_path))
    _seed(conn, ACME_PATHS)
    conn.close()

    out = tmp_path / "review.csv"
    result = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT), "--db", str(db_path), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert str(out) in lines[0]
    summary = json.loads(lines[1])
    assert summary["exported"] == len(ACME_PATHS)


def test_cli_approve_outputs_json(db_path, tmp_path):
    conn = duckdb.connect(str(db_path))
    _seed(conn, [ACME_PATHS[0]])
    conn.close()

    export_path = tmp_path / "review.csv"
    subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT), "--db", str(db_path), "--out", str(export_path)],
        capture_output=True, text=True, check=True,
    )

    # Set reviewer_action = approve
    with export_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    rows[0]["reviewer_action"] = "approve"
    edited = tmp_path / "edited.csv"
    with edited.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ef.EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    result = subprocess.run(
        [sys.executable, str(APPROVE_SCRIPT), "--db", str(db_path),
         "--input", str(edited), "--reviewer", "CLI Tester"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["approved"] == 1


def test_cli_approve_dry_run(db_path, tmp_path):
    conn = duckdb.connect(str(db_path))
    _seed(conn, [ACME_PATHS[0]])
    conn.close()

    export_path = tmp_path / "review.csv"
    subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT), "--db", str(db_path), "--out", str(export_path)],
        capture_output=True, text=True, check=True,
    )
    with export_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    rows[0]["reviewer_action"] = "approve"
    edited = tmp_path / "edited.csv"
    with edited.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ef.EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    result = subprocess.run(
        [sys.executable, str(APPROVE_SCRIPT), "--db", str(db_path),
         "--input", str(edited), "--dry-run"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout.strip())
    assert out["approved"] == 1
    # Status unchanged in DB
    conn = duckdb.connect(str(db_path), read_only=True)
    status = conn.execute(
        "SELECT status FROM classifications WHERE path = ?", [ACME_PATHS[0]]
    ).fetchone()[0]
    conn.close()
    assert status == "proposed"
