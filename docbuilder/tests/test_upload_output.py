import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import _drive
import upload_output
from upload_output import upload_outputs

USE_CASE_ROOT = Path(__file__).parent.parent


def _env_without_drive():
    env = dict(os.environ)
    env.pop("DRIVE_DOCBUILDER_ID", None)
    return env


# --- unit: helpers ---

def test_drive_url_helper():
    assert _drive.drive_url("abc123") == "https://drive.google.com/file/d/abc123/view"


# --- unit: upload_outputs (mocked Drive, no creds) ---

def test_upload_outputs_mocked(tmp_path, monkeypatch):
    f1 = tmp_path / "acme_corp_proposal_2026-06-20.xlsx"
    f2 = tmp_path / "acme_corp_proposal_2026-06-20.pdf"
    f1.write_text("x")
    f2.write_text("y")

    folder_calls = []

    def fake_build_service(scopes=None):
        return "SVC"

    def fake_find_or_create(service, parent_id, name):
        folder_calls.append((parent_id, name))
        return f"{name}_folder"  # ROOT→demo_folder, demo_folder→output_folder

    def fake_upload(service, folder_id, file_path):
        assert folder_id == "output_folder"
        return f"id_{Path(file_path).name}"

    monkeypatch.setattr(_drive, "build_service", fake_build_service)
    monkeypatch.setattr(_drive, "find_or_create_folder", fake_find_or_create)
    monkeypatch.setattr(_drive, "upload_file", fake_upload)

    results = upload_outputs("demo", [str(f1), str(f2)], "ROOT")

    # navigated ROOT → demo → output
    assert folder_calls == [("ROOT", "demo"), ("demo_folder", "output")]
    assert [r["filename"] for r in results] == [f1.name, f2.name]
    assert results[0]["drive_file_id"] == f"id_{f1.name}"
    assert results[0]["drive_url"] == f"https://drive.google.com/file/d/id_{f1.name}/view"


def test_upload_outputs_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(_drive, "build_service", lambda scopes=None: "SVC")
    monkeypatch.setattr(_drive, "find_or_create_folder", lambda *a: "f")
    with pytest.raises(FileNotFoundError):
        upload_outputs("demo", [str(tmp_path / "nope.pdf")], "ROOT")


# --- CLI ---

def test_cli_no_drive_id_exits_1(tmp_path):
    f = tmp_path / "x.pdf"
    f.write_text("x")
    result = subprocess.run(
        [sys.executable, "scripts/upload_output.py",
         "--tenant", "demo", "--files", str(f)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env_without_drive()
    )
    assert result.returncode == 1
    assert "Drive id" in result.stderr


# --- integration (real Drive; skipped without creds) ---

@pytest.mark.integration
def test_cli_upload_roundtrip(tmp_path):
    if not os.environ.get("DRIVE_DOCBUILDER_ID"):
        pytest.skip("DRIVE_DOCBUILDER_ID not set")
    f = tmp_path / "acme_corp_proposal_2026-06-20.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    result = subprocess.run(
        [sys.executable, "scripts/upload_output.py",
         "--tenant", "demo", "--files", str(f)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out[0]["filename"] == f.name
    assert out[0]["drive_file_id"]
