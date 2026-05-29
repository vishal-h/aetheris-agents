"""
Tests for list_pending_zips.py and zip_orchestrator.exs eval check.

Uses sample_corpus.duckdb fixture. Zip files are seeded via direct
f2_file_index inserts — no binary .zip fixtures committed.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import list_pending_zips as lpz

FIXTURE  = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"
SCRIPT   = Path(__file__).parent.parent / "scripts" / "list_pending_zips.py"
AGENT    = Path(__file__).parent.parent / "agents" / "zip_orchestrator.exs"
AETHERIS = Path(__file__).parent.parent.parent.parent / "aetheris"


# sample_corpus.duckdb has two zip rows that are not yet in zip_inventory.
# Mark them processed so every test starts with zero pending zips.
_FIXTURE_ZIPS = [
    "/data/archive/acme/archive_2022.zip",
    "/data/archive/globex/old_docs.zip",
]


def _mark_fixture_zips_processed(conn):
    for path in _FIXTURE_ZIPS:
        conn.execute(
            "INSERT INTO zip_inventory (path, status) VALUES (?, 'processed') "
            "ON CONFLICT (path) DO UPDATE SET status = 'processed'",
            [path],
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    conn = duckdb.connect(str(dest))
    _mark_fixture_zips_processed(conn)
    yield conn
    conn.close()


@pytest.fixture
def db_path(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    conn = duckdb.connect(str(dest))
    _mark_fixture_zips_processed(conn)
    conn.close()
    return dest


def _seed_zip(conn, path: str, depth: int = 0, status: str | None = None):
    """Seed an f2_file_index row and optional zip_inventory entry."""
    conn.execute(
        """INSERT INTO f2_file_index (path, size_bytes, mime_type, status, last_scanned)
           VALUES (?, 1000, 'application/zip', 'ok', now())
           ON CONFLICT (path) DO NOTHING""",
        [path],
    )
    if status is not None:
        conn.execute(
            """INSERT INTO zip_inventory (path, depth, status)
               VALUES (?, ?, ?)
               ON CONFLICT (path) DO UPDATE SET status = excluded.status, depth = excluded.depth""",
            [path, depth, status],
        )


def _seed_zip_by_extension(conn, path: str):
    """Seed a zip identified by .zip extension (no mime_type set)."""
    conn.execute(
        """INSERT INTO f2_file_index (path, size_bytes, mime_type, status, last_scanned)
           VALUES (?, 1000, 'application/octet-stream', 'ok', now())
           ON CONFLICT (path) DO NOTHING""",
        [path],
    )


# ---------------------------------------------------------------------------
# list_pending_zips — query logic
# ---------------------------------------------------------------------------

def test_empty_result_when_no_zips(db):
    result = lpz.list_pending_zips(db)
    # sample_corpus has no zip entries by default
    assert result["total"] == 0
    assert result["zips"] == []


def test_unprocessed_zip_appears(db):
    _seed_zip(db, "/data/archive/acme/backup.zip")
    result = lpz.list_pending_zips(db)
    assert result["total"] == 1
    assert result["zips"][0]["path"] == "/data/archive/acme/backup.zip"
    assert result["zips"][0]["depth"] == 0


def test_processed_zip_excluded(db):
    _seed_zip(db, "/data/archive/acme/done.zip", status="processed")
    result = lpz.list_pending_zips(db)
    assert result["total"] == 0


def test_pending_zip_included(db):
    _seed_zip(db, "/data/archive/acme/pending.zip", depth=1, status="pending")
    result = lpz.list_pending_zips(db)
    assert result["total"] == 1
    assert result["zips"][0]["depth"] == 1


def test_encrypted_zip_excluded(db):
    _seed_zip(db, "/data/archive/acme/encrypted.zip", status="encrypted")
    result = lpz.list_pending_zips(db)
    assert result["total"] == 0


def test_zip_detected_by_extension(db):
    _seed_zip_by_extension(db, "/data/archive/acme/archive.zip")
    result = lpz.list_pending_zips(db)
    assert result["total"] == 1


def test_missing_status_excluded(db):
    conn = db
    conn.execute(
        """INSERT INTO f2_file_index (path, size_bytes, mime_type, status, last_scanned)
           VALUES (?, 1000, 'application/zip', 'missing', now())
           ON CONFLICT (path) DO NOTHING""",
        ["/data/archive/acme/missing.zip"],
    )
    result = lpz.list_pending_zips(db)
    assert result["total"] == 0


def test_ordered_by_depth_then_path(db):
    _seed_zip(db, "/data/archive/c.zip", depth=0)
    _seed_zip(db, "/data/archive/a.zip", depth=1, status="pending")
    _seed_zip(db, "/data/archive/b.zip", depth=0)
    result = lpz.list_pending_zips(db)
    paths = [z["path"] for z in result["zips"]]
    depths = [z["depth"] for z in result["zips"]]
    # depth 0 entries before depth 1
    assert depths == sorted(depths)
    # within same depth, alphabetical
    depth0_paths = [z["path"] for z in result["zips"] if z["depth"] == 0]
    assert depth0_paths == sorted(depth0_paths)


def test_max_depth_filter(db):
    _seed_zip(db, "/data/archive/shallow.zip", depth=0)
    _seed_zip(db, "/data/archive/deep.zip", depth=2, status="pending")
    result = lpz.list_pending_zips(db, max_depth=1)
    assert result["total"] == 1
    assert result["zips"][0]["path"] == "/data/archive/shallow.zip"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_empty_result(db_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout.strip())
    assert out == {"total": 0, "zips": []}


def test_cli_reports_count_to_stderr(db_path):
    conn = duckdb.connect(str(db_path))
    _seed_zip(conn, "/data/archive/acme/test.zip")
    conn.close()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        capture_output=True, text=True,
    )
    assert "1 zips pending" in result.stderr


def test_cli_max_depth_flag(db_path):
    conn = duckdb.connect(str(db_path))
    _seed_zip(conn, "/data/archive/shallow.zip", depth=0)
    _seed_zip(conn, "/data/archive/deep.zip", depth=3, status="pending")
    conn.close()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path), "--max-depth", "1"],
        capture_output=True, text=True,
    )
    out = json.loads(result.stdout.strip())
    assert out["total"] == 1
    assert out["zips"][0]["path"] == "/data/archive/shallow.zip"


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
    if not AETHERIS.exists():
        pytest.skip("aetheris repo not found")

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{AGENT}")'],
        cwd=str(AETHERIS),
        env={**os.environ,
             "PROVENANCE_DB_PATH": str(tmp_path / "corpus.duckdb"),
             "STAGING_PATH": str(tmp_path / "zip_staging")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
