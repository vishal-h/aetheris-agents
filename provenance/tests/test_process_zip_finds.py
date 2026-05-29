"""
Tests for process_zip_finds.py.

All zip files are created programmatically with zipfile.
Uses the sample_corpus.duckdb fixture for DuckDB state.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import extract_zip as ez
import process_zip_finds as pzf

FIXTURE = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"
SCRIPT  = Path(__file__).parent.parent / "scripts" / "process_zip_finds.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_manifest(tmp_path: Path, members: dict[str, bytes]) -> dict:
    """Write a zip, extract it, and return the extract_zip manifest."""
    zp = tmp_path / "archive.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return ez.extract_zip(str(zp), str(tmp_path / "staging"))


def _seed_known(conn, content: bytes, path: str = "/data/archive/known.pdf"):
    """Insert an f2_file_index row whose sha256 matches content."""
    sha256 = _sha256_bytes(content)
    conn.execute(
        """INSERT INTO f2_file_index (path, size_bytes, sha256, status, last_scanned)
           VALUES (?, ?, ?, 'ok', now())
           ON CONFLICT (path) DO NOTHING""",
        [path, len(content), sha256],
    )
    return sha256


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
# Known-file path
# ---------------------------------------------------------------------------

def test_known_file_returns_known_status(db, tmp_path):
    content = b"content that already exists in corpus"
    _seed_known(db, content)
    manifest = _make_manifest(tmp_path, {"doc.pdf": content})

    result = pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    assert result["known"] == 1
    assert result["new_to_corpus"] == 0
    assert result["new_finds"] == []


def test_known_file_deleted_from_staging(db, tmp_path):
    content = b"duplicate content for deletion test"
    _seed_known(db, content)
    manifest = _make_manifest(tmp_path, {"doc.pdf": content})
    staging_file = Path(manifest["files"][0]["staging_path"])

    pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    assert not staging_file.exists()


def test_known_file_corpus_match_in_zip_contents(db, tmp_path):
    content = b"corpus file content"
    corpus_path = "/data/archive/acme/FY2024/known.pdf"
    _seed_known(db, content, path=corpus_path)
    manifest = _make_manifest(tmp_path, {"tax.pdf": content})

    pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    row = db.execute(
        "SELECT status, corpus_match FROM zip_contents WHERE zip_path = ?",
        [manifest["zip_path"]],
    ).fetchone()
    assert row[0] == "known"
    assert row[1] == corpus_path


# ---------------------------------------------------------------------------
# New-to-corpus path
# ---------------------------------------------------------------------------

def test_new_file_added_to_f2_file_index(db, tmp_path):
    content = b"genuinely new content not in corpus"
    manifest = _make_manifest(tmp_path, {"report.pdf": content})

    result = pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    assert result["new_to_corpus"] == 1
    sha256 = _sha256_bytes(content)
    row = db.execute(
        "SELECT sha256 FROM f2_file_index WHERE sha256 = ?", [sha256]
    ).fetchone()
    assert row is not None


def test_new_file_content_addressed_layout(db, tmp_path):
    content = b"new content for layout test"
    manifest = _make_manifest(tmp_path, {"letter.docx": content})
    finds_root = tmp_path / "finds"

    result = pzf.process_zip_finds(db, manifest, str(finds_root))

    sha256 = _sha256_bytes(content)
    expected = finds_root / "new_finds" / sha256[:2] / sha256 / "letter.docx"
    assert expected.exists()
    assert result["new_finds"][0]["staging_path"] == str(expected)
    assert result["new_finds"][0]["sha256"] == sha256


def test_new_file_zip_contents_row_status_new(db, tmp_path):
    content = b"new zip contents row test"
    manifest = _make_manifest(tmp_path, {"invoice.pdf": content})

    pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    row = db.execute(
        "SELECT status, corpus_match FROM zip_contents WHERE zip_path = ?",
        [manifest["zip_path"]],
    ).fetchone()
    assert row[0] == "new"
    assert row[1] is None


# ---------------------------------------------------------------------------
# zip_inventory and staging cleanup
# ---------------------------------------------------------------------------

def test_zip_inventory_updated_to_processed(db, tmp_path):
    content = b"file to drive zip_inventory update"
    manifest = _make_manifest(tmp_path, {"x.txt": content})

    pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    row = db.execute(
        "SELECT status, contents_count, new_to_corpus FROM zip_inventory WHERE path = ?",
        [manifest["zip_path"]],
    ).fetchone()
    assert row is not None
    assert row[0] == "processed"
    assert row[1] == 1
    assert row[2] == 1


def test_raw_staging_dir_deleted(db, tmp_path):
    content = b"file to trigger staging cleanup"
    manifest = _make_manifest(tmp_path, {"a.txt": content})
    staging_dir = Path(manifest["staging_dir"])
    assert staging_dir.exists()

    pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    assert not staging_dir.exists()


# ---------------------------------------------------------------------------
# Nested zips
# ---------------------------------------------------------------------------

def test_nested_zips_added_to_inventory_as_pending(db, tmp_path):
    inner_bytes = b"PK\x03\x04"  # minimal zip header marker is enough; real content:
    inner_zip = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner_zip, "w") as zf:
        zf.writestr("inner_doc.txt", b"inner content")

    manifest = _make_manifest(tmp_path, {
        "readme.txt": b"outer file",
        "old/inner.zip": inner_zip.read_bytes(),
    })

    pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    row = db.execute(
        "SELECT status, parent_zip FROM zip_inventory WHERE parent_zip = ?",
        [manifest["zip_path"]],
    ).fetchone()
    assert row is not None
    assert row[0] == "pending"
    assert row[1] == manifest["zip_path"]


def test_nested_zip_registered_at_permanent_path(db, tmp_path):
    """Nested zip's zip_inventory path is the new_finds permanent path, not staging."""
    inner_zip = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner_zip, "w") as zf:
        zf.writestr("file.txt", b"inner")
    inner_bytes = inner_zip.read_bytes()

    manifest = _make_manifest(tmp_path, {
        "readme.txt": b"outer",
        "nested.zip": inner_bytes,
    })

    finds_root = tmp_path / "finds"
    pzf.process_zip_finds(db, manifest, str(finds_root))

    # The permanent path must be under new_finds, not under the (deleted) staging dir
    nested_row = db.execute(
        "SELECT path FROM zip_inventory WHERE parent_zip = ?",
        [manifest["zip_path"]],
    ).fetchone()
    assert nested_row is not None
    assert "new_finds" in nested_row[0]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_idempotent_second_run_returns_same_counts(db, tmp_path):
    content = b"idempotent test file content"
    manifest = _make_manifest(tmp_path, {"file.pdf": content})
    finds_root = tmp_path / "finds"

    first  = pzf.process_zip_finds(db, manifest, str(finds_root))
    second = pzf.process_zip_finds(db, manifest, str(finds_root))

    assert second["total_files"] == first["total_files"]
    assert second["new_to_corpus"] == first["new_to_corpus"]
    assert second["known"] == first["known"]


# ---------------------------------------------------------------------------
# Mixed case
# ---------------------------------------------------------------------------

def test_mixed_known_and_new(db, tmp_path):
    known_content = b"already in corpus content"
    new_content   = b"unique new content xyz987abc"
    _seed_known(db, known_content, "/data/archive/acme/known.pdf")
    manifest = _make_manifest(tmp_path, {
        "known.pdf": known_content,
        "new.pdf":   new_content,
    })

    result = pzf.process_zip_finds(db, manifest, str(tmp_path / "finds"))

    assert result["known"] == 1
    assert result["new_to_corpus"] == 1
    assert result["total_files"] == 2
    assert len(result["new_finds"]) == 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_outputs_json(db_path, tmp_path):
    content = b"cli invocation test"
    manifest = _make_manifest(tmp_path, {"cli.pdf": content})
    mfile = tmp_path / "manifest.json"
    mfile.write_text(json.dumps(manifest))

    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--db", str(db_path),
         "--manifest", str(mfile),
         "--staging-path", str(tmp_path / "finds")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout.strip())
    assert out["total_files"] == 1
    assert out["new_to_corpus"] == 1
