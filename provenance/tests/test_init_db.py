import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from init_db import TABLES, VIEWS, init_schema

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
INIT_DB = SCRIPTS_DIR / "init_db.py"

EXPECTED_TABLES = set(TABLES.keys())
EXPECTED_VIEWS = set(VIEWS.keys())


def _tables(conn):
    return {
        row[0]
        for row in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_type = 'BASE TABLE'"
        ).fetchall()
    }


def _views(conn):
    return {
        row[0]
        for row in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_type = 'VIEW'"
        ).fetchall()
    }


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.duckdb")


def test_all_tables_created(db_path):
    conn = duckdb.connect(db_path)
    init_schema(conn)
    conn.close()

    conn = duckdb.connect(db_path)
    assert EXPECTED_TABLES <= _tables(conn)
    conn.close()


def test_all_views_created(db_path):
    conn = duckdb.connect(db_path)
    init_schema(conn)
    conn.close()

    conn = duckdb.connect(db_path)
    assert EXPECTED_VIEWS <= _views(conn)
    conn.close()


def test_idempotent(db_path):
    conn = duckdb.connect(db_path)
    init_schema(conn)
    conn.close()

    conn = duckdb.connect(db_path)
    init_schema(conn)  # second run must not raise
    assert EXPECTED_TABLES <= _tables(conn)
    assert EXPECTED_VIEWS <= _views(conn)
    conn.close()


def test_existing_f2_data_preserved(db_path):
    conn = duckdb.connect(db_path)
    init_schema(conn)
    conn.execute("INSERT INTO f2_file_index (path, sha256) VALUES ('/tmp/a.txt', 'abc123')")
    conn.close()

    conn = duckdb.connect(db_path)
    init_schema(conn)
    count = conn.execute("SELECT COUNT(*) FROM f2_file_index").fetchone()[0]
    conn.close()

    assert count == 1


def test_backfill_missing_f2_columns(tmp_path):
    """f2_file_index created with only path column gets required columns added."""
    db_path = str(tmp_path / "tauri.duckdb")
    conn = duckdb.connect(db_path)
    conn.execute("CREATE TABLE f2_file_index (path TEXT PRIMARY KEY)")
    conn.execute("INSERT INTO f2_file_index VALUES ('/doc.pdf')")
    conn.close()

    conn = duckdb.connect(db_path)
    init_schema(conn)
    cols = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'f2_file_index'"
        ).fetchall()
    }
    conn.close()

    assert {"sha256", "size_bytes", "modified_at", "mime_type", "status", "last_scanned"} <= cols


def test_cli_exit_zero(db_path):
    result = subprocess.run(
        [sys.executable, str(INIT_DB), "--db", db_path],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    for name in EXPECTED_TABLES:
        assert name in result.stdout
    for name in EXPECTED_VIEWS:
        assert name in result.stdout


def test_requirements_pins_duckdb():
    req = (Path(__file__).parent.parent / "requirements.txt").read_text()
    assert "duckdb==" in req
