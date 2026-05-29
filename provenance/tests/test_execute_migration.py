"""
Tests for execute_migration.py.

All tests use real temporary filesystem operations (tmp_path). A fresh DuckDB
is created per test with real source files and their computed SHA-256 hashes.
Rollback tests are given their own section — they are the critical safety path.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import execute_migration as em
from init_db import init_schema

SCRIPT = Path(__file__).parent.parent / "scripts" / "execute_migration.py"


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_db(tmp_path: Path) -> tuple[duckdb.DuckDBPyConnection, Path]:
    """Create a fresh DuckDB with full schema."""
    db_path = tmp_path / "corpus.duckdb"
    conn = duckdb.connect(str(db_path))
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        init_schema(conn)
    return conn, db_path


def _seed_file(
    conn: duckdb.DuckDBPyConnection,
    src_root: Path,
    rel_path: str,
    content: bytes = b"test file content",
) -> tuple[Path, str]:
    """Create a real source file and register it in f2_file_index."""
    full_path = src_root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)
    sha = _sha256(content)
    conn.execute(
        "INSERT OR REPLACE INTO f2_file_index (path, sha256, size_bytes, status) VALUES (?, ?, ?, 'ok')",
        [str(full_path), sha, len(content)],
    )
    return full_path, sha


def _record(src: Path, dst: Path, classification_id: str = None) -> dict:
    return {
        "source_path": str(src),
        "dest_path": str(dst),
        "classification_id": classification_id,
    }


@pytest.fixture
def env(tmp_path):
    """Returns (conn, db_path, src_root, dst_root)."""
    conn, db_path = _make_db(tmp_path)
    src_root = tmp_path / "archive"
    dst_root = tmp_path / "clients"
    yield conn, db_path, src_root, dst_root
    conn.close()


# ---------------------------------------------------------------------------
# Migration — happy path
# ---------------------------------------------------------------------------

def test_copies_file_and_records_migrated(env, tmp_path):
    conn, db_path, src_root, dst_root = env
    src, sha = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax/tax.pdf"

    result = em.execute_migration(conn, [_record(src, dst)])

    assert result == {"migrated": 1, "failed": 0, "skipped": 0}
    assert dst.exists()
    assert _sha256(dst.read_bytes()) == sha

    row = conn.execute("SELECT status FROM migrations WHERE path = ?", [str(src)]).fetchone()
    assert row[0] == "migrated"


def test_creates_nested_destination_dirs(env, tmp_path):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "a/b/c/d/e/tax.pdf"

    result = em.execute_migration(conn, [_record(src, dst)])

    assert result["migrated"] == 1
    assert dst.exists()


def test_idempotent_second_run_skips(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    first = em.execute_migration(conn, [_record(src, dst)])
    second = em.execute_migration(conn, [_record(src, dst)])

    assert first == {"migrated": 1, "failed": 0, "skipped": 0}
    assert second == {"migrated": 0, "failed": 0, "skipped": 1}


def test_migrated_at_is_set(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    em.execute_migration(conn, [_record(src, dst)])

    migrated_at = conn.execute(
        "SELECT migrated_at FROM migrations WHERE path = ?", [str(src)]
    ).fetchone()[0]
    assert migrated_at is not None


def test_multiple_files_in_batch(env):
    conn, _, src_root, dst_root = env
    records = []
    for i in range(3):
        src, _ = _seed_file(conn, src_root, f"acme/FY2024/file_{i}.pdf",
                             content=f"content {i}".encode())
        dst = dst_root / f"acme/FY2024/file_{i}.pdf"
        records.append(_record(src, dst))

    result = em.execute_migration(conn, records)
    assert result == {"migrated": 3, "failed": 0, "skipped": 0}


# ---------------------------------------------------------------------------
# Migration — failure cases
# ---------------------------------------------------------------------------

def test_hash_mismatch_marks_failed_and_deletes_copy(env, tmp_path):
    """Register a wrong expected SHA-256 — copy will be detected as corrupt."""
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf", content=b"real content")
    # Overwrite f2_file_index with a wrong sha
    conn.execute("UPDATE f2_file_index SET sha256 = 'wrong000' WHERE path = ?", [str(src)])
    dst = dst_root / "acme/FY2024/tax.pdf"

    result = em.execute_migration(conn, [_record(src, dst)])

    assert result["failed"] == 1
    assert not dst.exists(), "corrupt copy must be deleted"
    row = conn.execute("SELECT status, error FROM migrations WHERE path = ?", [str(src)]).fetchone()
    assert row[0] == "failed"
    assert "mismatch" in row[1].lower()


def test_dest_exists_same_hash_skips(env):
    conn, _, src_root, dst_root = env
    content = b"known content"
    src, sha = _seed_file(conn, src_root, "acme/FY2024/tax.pdf", content=content)
    dst = dst_root / "acme/FY2024/tax.pdf"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(content)  # already there with correct hash

    result = em.execute_migration(conn, [_record(src, dst)])

    assert result["skipped"] == 1
    assert result["migrated"] == 0


def test_dest_exists_different_hash_fails(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf", content=b"original")
    dst = dst_root / "acme/FY2024/tax.pdf"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(b"different content already here")  # different hash

    result = em.execute_migration(conn, [_record(src, dst)])

    assert result["failed"] == 1
    # Must not have overwritten the existing file
    assert dst.read_bytes() == b"different content already here"


def test_source_not_in_f2_file_index_skips(env, capsys):
    conn, _, src_root, dst_root = env
    src = src_root / "ghost.pdf"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"ghost")
    dst = dst_root / "ghost.pdf"

    result = em.execute_migration(conn, [{"source_path": str(src), "dest_path": str(dst)}])

    assert result["skipped"] == 1
    assert "warning" in capsys.readouterr().err


def test_dest_root_rejects_outside_paths(env, capsys):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = src_root / "sneaky/tax.pdf"  # outside dst_root

    result = em.execute_migration(conn, [_record(src, dst)],
                                   dest_root=str(dst_root))

    assert result["skipped"] == 1
    assert "outside" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def test_dry_run_writes_no_files(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    result = em.execute_migration(conn, [_record(src, dst)], dry_run=True)

    assert result == {"would_migrate": 1, "would_skip": 0}
    assert not dst.exists()
    assert conn.execute("SELECT COUNT(*) FROM migrations").fetchone()[0] == 0


def test_dry_run_already_migrated_counted_as_skip(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    em.execute_migration(conn, [_record(src, dst)])  # real run first
    result = em.execute_migration(conn, [_record(src, dst)], dry_run=True)

    assert result["would_skip"] == 1


# ---------------------------------------------------------------------------
# Rollback — critical safety path
# ---------------------------------------------------------------------------

def test_rollback_deletes_dest_and_resets_status(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    em.execute_migration(conn, [_record(src, dst)])
    assert dst.exists()

    result = em.rollback_migrations(conn)

    assert result["rolled_back"] == 1
    assert not dst.exists()
    status = conn.execute(
        "SELECT status FROM migrations WHERE path = ?", [str(src)]
    ).fetchone()[0]
    assert status == "proposed"


def test_rollback_dry_run_does_not_delete(env):
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    em.execute_migration(conn, [_record(src, dst)])
    result = em.rollback_migrations(conn, dry_run=True)

    assert result["rolled_back"] == 1
    assert result["dry_run"] is True
    assert dst.exists(), "dry-run must not delete the file"
    status = conn.execute(
        "SELECT status FROM migrations WHERE path = ?", [str(src)]
    ).fetchone()[0]
    assert status == "migrated", "dry-run must not update DB"


def test_rollback_since_filter(env):
    conn, _, src_root, dst_root = env

    # Migrate two files; set one's migrated_at to the past
    src1, _ = _seed_file(conn, src_root, "acme/FY2024/old.pdf", content=b"old")
    dst1 = dst_root / "acme/FY2024/old.pdf"
    src2, _ = _seed_file(conn, src_root, "acme/FY2024/new.pdf", content=b"new")
    dst2 = dst_root / "acme/FY2024/new.pdf"

    em.execute_migration(conn, [_record(src1, dst1), _record(src2, dst2)])

    # Back-date src1's migration record
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    conn.execute("UPDATE migrations SET migrated_at = ? WHERE path = ?", [old_time, str(src1)])

    since = datetime(2025, 1, 1, tzinfo=timezone.utc)
    result = em.rollback_migrations(conn, since=since)

    # Only src2 (recent) should be rolled back
    assert result["rolled_back"] == 1
    assert not dst2.exists()
    assert dst1.exists()

    statuses = {
        r[0]: r[1]
        for r in conn.execute("SELECT path, status FROM migrations").fetchall()
    }
    assert statuses[str(src1)] == "migrated"
    assert statuses[str(src2)] == "proposed"


def test_rollback_missing_dest_does_not_error(env):
    """If the dest file is already gone, rollback still resets DB status."""
    conn, _, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"

    em.execute_migration(conn, [_record(src, dst)])
    dst.unlink()  # manually delete before rollback

    result = em.rollback_migrations(conn)

    assert result["rolled_back"] == 1
    status = conn.execute(
        "SELECT status FROM migrations WHERE path = ?", [str(src)]
    ).fetchone()[0]
    assert status == "proposed"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_migrate_outputs_json(env, tmp_path):
    conn, db_path, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    conn.close()  # release so CLI can open

    dst = dst_root / "acme/FY2024/tax.pdf"
    input_file = tmp_path / "batch.json"
    input_file.write_text(json.dumps([_record(src, dst)]))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path),
         "--input", str(input_file)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["migrated"] == 1


def test_cli_dry_run(env, tmp_path):
    conn, db_path, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    conn.close()

    dst = dst_root / "acme/FY2024/tax.pdf"
    input_file = tmp_path / "batch.json"
    input_file.write_text(json.dumps([_record(src, dst)]))

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path),
         "--input", str(input_file), "--dry-run"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout.strip())
    assert "would_migrate" in out
    assert not dst.exists()


def test_cli_rollback(env, tmp_path):
    conn, db_path, src_root, dst_root = env
    src, _ = _seed_file(conn, src_root, "acme/FY2024/tax.pdf")
    dst = dst_root / "acme/FY2024/tax.pdf"
    em.execute_migration(conn, [_record(src, dst)])
    conn.close()

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path), "--rollback"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout.strip())
    assert out["rolled_back"] == 1
    assert not dst.exists()


def test_cli_bad_db_exits_1(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", "/nonexistent/path.duckdb",
         "--rollback"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
