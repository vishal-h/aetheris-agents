"""
Dry-run acceptance tests for the classification orchestrator.

Validates SQL query logic and batch-count calculation against the fixture DB
without making LLM calls. Confirms agent evaluates without error.
"""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import list_unclassified as lu
import classify_documents as cd

FIXTURE = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"
SCRIPT  = Path(__file__).parent.parent / "scripts" / "list_unclassified.py"


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
# list_unclassified query logic
# ---------------------------------------------------------------------------

def test_returns_list_of_paths(db):
    paths = lu.list_unclassified(db)
    assert isinstance(paths, list)
    assert len(paths) > 0
    assert all(isinstance(p, str) for p in paths)


def test_one_path_per_unique_sha256(db):
    """Each SHA-256 appears at most once in the result."""
    paths = lu.list_unclassified(db)
    sha_counts = db.execute(
        "SELECT sha256, COUNT(*) FROM f2_file_index WHERE sha256 IS NOT NULL AND status != 'missing' GROUP BY sha256 HAVING COUNT(*) > 1"
    ).fetchall()
    unique_sha_count = db.execute(
        "SELECT COUNT(DISTINCT sha256) FROM f2_file_index WHERE sha256 IS NOT NULL AND status != 'missing'"
    ).fetchone()[0]
    assert len(paths) == unique_sha_count


def test_fixture_has_expected_unclassified_count(db):
    paths = lu.list_unclassified(db)
    assert len(paths) == 22  # 30 total, 8 are duplicates of existing SHA-256s


def test_batch_count_at_size_20(db):
    paths = lu.list_unclassified(db)
    batch_count = math.ceil(len(paths) / 20)
    assert batch_count == 2


def test_already_classified_paths_excluded(db):
    """Paths with proposed/approved status are not returned."""
    paths_before = lu.list_unclassified(db)
    first_path = paths_before[0]

    # Classify the first path
    cd.write_classifications(db, [{
        "path": first_path, "client": "acme", "financial_year": "FY2024",
        "doc_type": "tax", "confidence": 0.90,
    }])

    paths_after = lu.list_unclassified(db)
    assert first_path not in paths_after
    assert len(paths_after) == len(paths_before) - 1


def test_rejected_paths_are_re_queued(db):
    """Paths with 'rejected' status appear in the next run."""
    paths = lu.list_unclassified(db)
    first_path = paths[0]
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

    # Insert a rejected classification
    db.execute(
        "INSERT INTO classifications (id, path, client, financial_year, doc_type, confidence, status, classified_at) VALUES (?, ?, ?, ?, ?, ?, 'rejected', ?)",
        [str(__import__("uuid").uuid4()), first_path, "acme", "FY2024", "tax", 0.5, now],
    )

    paths_after = lu.list_unclassified(db)
    assert first_path in paths_after


# ---------------------------------------------------------------------------
# CLI — list_unclassified.py
# ---------------------------------------------------------------------------

def test_cli_outputs_json_array(db_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    paths = json.loads(result.stdout.strip())
    assert isinstance(paths, list)
    assert len(paths) == 22


def test_cli_reports_count_to_stderr(db_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        capture_output=True, text=True,
    )
    assert "22 files to classify" in result.stderr


def test_cli_bad_db_exits_1():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", "/nonexistent/path.duckdb"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Agent eval check
# ---------------------------------------------------------------------------

def test_agent_evaluates_without_error(tmp_path):
    """classification_orchestrator.exs evaluates with mix run --eval."""
    agent = Path(__file__).parent.parent / "agents" / "classification_orchestrator.exs"
    aetheris = Path(__file__).parent.parent.parent.parent / "aetheris"
    if not aetheris.exists():
        pytest.skip("aetheris repo not found at expected path")

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{agent}")'],
        cwd=str(aetheris),
        env={**__import__("os").environ, "PROVENANCE_DB_PATH": str(tmp_path / "corpus.duckdb")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
