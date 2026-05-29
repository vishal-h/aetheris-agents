"""
Tests for extract_zip.py.

All zip files are created programmatically with zipfile — no binary .zip
fixtures are committed to the repository.
"""

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import extract_zip as ez

SCRIPT = Path(__file__).parent.parent / "scripts" / "extract_zip.py"


# ---------------------------------------------------------------------------
# Helpers — build test zips in tmp_path
# ---------------------------------------------------------------------------

def _make_zip(path: Path, members: dict[str, bytes]) -> Path:
    """Create a zip at `path` with {internal_name: content} members."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return path


def _make_encrypted_zip(path: Path) -> Path:
    """Create a zip whose first member has the encryption flag set."""
    # Python's zipfile can't write encrypted zips natively.
    # Patch bit 0 (encryption flag) in both the local file header (offset 6)
    # AND the central directory header (offset 8) — zipfile.infolist() reads
    # flag_bits from the central directory, not the local header.
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("secret.txt", "secret content")

    data = bytearray(path.read_bytes())

    # Patch local file header: signature PK\x03\x04, flag at offset 6
    local_sig = b"PK\x03\x04"
    idx = data.find(local_sig)
    if idx != -1:
        data[idx + 6] = data[idx + 6] | 0x01

    # Patch central directory header: signature PK\x01\x02, flag at offset 8
    central_sig = b"PK\x01\x02"
    idx = data.find(central_sig)
    if idx != -1:
        data[idx + 8] = data[idx + 8] | 0x01

    path.write_bytes(bytes(data))
    return path


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_extracts_files_to_staging(tmp_path):
    zp = _make_zip(tmp_path / "archive.zip", {
        "acme/FY2024/tax.pdf": b"tax content",
        "acme/FY2024/letter.docx": b"letter content",
    })
    staging = tmp_path / "staging"

    result = ez.extract_zip(str(zp), str(staging))

    assert result["status"] == "extracted"
    assert result["file_count"] == 2
    assert result["error"] is None
    # All files exist on disk
    for f in result["files"]:
        assert Path(f["staging_path"]).exists()


def test_manifest_fields_present(tmp_path):
    zp = _make_zip(tmp_path / "archive.zip", {"doc.pdf": b"content"})
    result = ez.extract_zip(str(zp), str(tmp_path / "staging"))

    assert "zip_path" in result
    assert "status" in result
    assert "staging_dir" in result
    assert "file_count" in result
    assert "files" in result
    assert "nested_zips" in result
    assert "error" in result
    assert result["files"][0]["internal_path"] == "doc.pdf"
    assert result["files"][0]["size_bytes"] == len(b"content")


def test_staging_dir_is_zip_stem_subdir(tmp_path):
    zp = _make_zip(tmp_path / "myarchive.zip", {"a.txt": b"x"})
    staging = tmp_path / "staging"

    result = ez.extract_zip(str(zp), str(staging))

    assert result["staging_dir"] == str(staging / "myarchive")


def test_detects_nested_zips(tmp_path):
    inner_zip = tmp_path / "inner.zip"
    _make_zip(inner_zip, {"inner_doc.pdf": b"inner"})

    outer = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer, "w") as zf:
        zf.writestr("readme.txt", "top-level file")
        zf.write(inner_zip, "old_archive/inner.zip")

    result = ez.extract_zip(str(outer), str(tmp_path / "staging"))

    assert result["status"] == "extracted"
    assert len(result["nested_zips"]) == 1
    assert result["nested_zips"][0]["internal_path"] == "old_archive/inner.zip"


# ---------------------------------------------------------------------------
# Encrypted zip
# ---------------------------------------------------------------------------

def test_encrypted_zip_returns_encrypted_status(tmp_path):
    zp = _make_encrypted_zip(tmp_path / "confidential.zip")
    staging = tmp_path / "staging"

    result = ez.extract_zip(str(zp), str(staging))

    assert result["status"] == "encrypted"
    assert result["file_count"] == 0
    assert result["files"] == []
    assert result["staging_dir"] is None
    assert "encrypted" in (result["error"] or "").lower() or result["status"] == "encrypted"


def test_encrypted_zip_extracts_nothing(tmp_path):
    zp = _make_encrypted_zip(tmp_path / "confidential.zip")
    staging = tmp_path / "staging"

    ez.extract_zip(str(zp), str(staging))

    # No files should have been written to staging
    assert not (staging / "confidential").exists() or \
           not any((staging / "confidential").rglob("*"))


# ---------------------------------------------------------------------------
# Max depth guard
# ---------------------------------------------------------------------------

def test_max_depth_returns_max_depth_status(tmp_path):
    zp = _make_zip(tmp_path / "deep.zip", {"file.txt": b"deep"})
    result = ez.extract_zip(str(zp), str(tmp_path / "staging"), depth=ez.MAX_DEPTH)

    assert result["status"] == "max_depth"
    assert result["file_count"] == 0


def test_depth_below_max_extracts_normally(tmp_path):
    zp = _make_zip(tmp_path / "ok.zip", {"file.txt": b"ok"})
    result = ez.extract_zip(str(zp), str(tmp_path / "staging"), depth=ez.MAX_DEPTH - 1)

    assert result["status"] == "extracted"


# ---------------------------------------------------------------------------
# Failure cases
# ---------------------------------------------------------------------------

def test_nonexistent_zip_returns_failed(tmp_path):
    result = ez.extract_zip("/nonexistent/path/archive.zip", str(tmp_path / "staging"))

    assert result["status"] == "failed"
    assert result["error"] is not None


def test_corrupt_zip_returns_failed(tmp_path):
    bad = tmp_path / "corrupt.zip"
    bad.write_bytes(b"this is not a zip file")
    result = ez.extract_zip(str(bad), str(tmp_path / "staging"))

    assert result["status"] == "failed"
    assert "BadZipFile" in (result["error"] or "")


# ---------------------------------------------------------------------------
# Path traversal safety (zip slip)
# ---------------------------------------------------------------------------

def test_path_traversal_members_are_skipped(tmp_path, capsys):
    """Zip members with ../../ components must not be extracted outside staging."""
    evil_zip = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil_zip, "w") as zf:
        zf.writestr("safe/normal.txt", b"safe content")
        # Manually add a member with a traversal path
        info = zipfile.ZipInfo("../../evil.txt")
        zf.writestr(info, b"evil content")

    staging = tmp_path / "staging"
    result = ez.extract_zip(str(evil_zip), str(staging))

    # The evil.txt must NOT exist outside staging
    assert not (tmp_path / "evil.txt").exists()
    # The safe file should still be extracted
    safe_extracted = list(staging.rglob("normal.txt"))
    assert len(safe_extracted) == 1
    # Warning was printed
    captured = capsys.readouterr()
    assert "traversal" in captured.err.lower() or "skipping" in captured.err.lower()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_outputs_json(tmp_path):
    zp = _make_zip(tmp_path / "archive.zip", {"doc.txt": b"hello"})
    staging = tmp_path / "staging"

    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--zip", str(zp), "--staging-dir", str(staging)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    manifest = json.loads(result.stdout.strip())
    assert manifest["status"] == "extracted"
    assert manifest["file_count"] == 1


def test_cli_exits_0_on_encrypted(tmp_path):
    zp = _make_encrypted_zip(tmp_path / "enc.zip")
    staging = tmp_path / "staging"

    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--zip", str(zp), "--staging-dir", str(staging)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0  # always exits 0
    manifest = json.loads(result.stdout.strip())
    assert manifest["status"] == "encrypted"


def test_cli_exits_0_on_missing_zip(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--zip", "/no/such/file.zip",
         "--staging-dir", str(tmp_path / "staging")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    manifest = json.loads(result.stdout.strip())
    assert manifest["status"] == "failed"
