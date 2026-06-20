import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fetch_template import local_bundle_path

USE_CASE_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = USE_CASE_ROOT / "data" / "templates"


def _env_without_drive():
    """Subprocess env with DRIVE_DOCBUILDER_ID removed so the local-fallback path
    is exercised regardless of the caller's shell."""
    env = dict(os.environ)
    env.pop("DRIVE_DOCBUILDER_ID", None)
    return env


# --- unit ---

def test_local_bundle_path_is_nested():
    p = local_bundle_path("data/templates", "demo", "proposal", "v1")
    assert p == Path("data/templates/demo/proposal/v1")


def test_nested_demo_bundle_exists():
    # Option A: the nested demo bundle is committed alongside the flat files.
    bundle = TEMPLATES_DIR / "demo" / "proposal" / "v1"
    assert bundle.is_dir()
    assert (bundle / "proposal_v1.json").exists()


# --- CLI: local fallback (no Drive creds) ---

def test_cli_local_fallback_returns_bundle_path(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/fetch_template.py",
         "--tenant", "demo", "--doc-type", "proposal", "--version", "v1"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env_without_drive()
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    assert out.endswith("data/templates/demo/proposal/v1")
    assert (USE_CASE_ROOT / out).is_dir()


def test_cli_local_fallback_missing_exits_1():
    result = subprocess.run(
        [sys.executable, "scripts/fetch_template.py",
         "--tenant", "ghost", "--doc-type", "nope", "--version", "v9"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env_without_drive()
    )
    assert result.returncode == 1
    assert "error" in result.stderr


def test_cli_output_flag_writes_path(tmp_path):
    out_file = tmp_path / "cache_path.txt"
    result = subprocess.run(
        [sys.executable, "scripts/fetch_template.py",
         "--tenant", "demo", "--doc-type", "proposal", "--version", "v1",
         "--output", str(out_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env_without_drive()
    )
    assert result.returncode == 0, result.stderr
    # stdout is the --output path; the file holds the bundle path
    assert result.stdout.strip() == str(out_file)
    assert out_file.read_text().strip().endswith("data/templates/demo/proposal/v1")


# --- Drive path (integration; skipped without creds) ---

@pytest.mark.integration
def test_drive_fetch_requires_creds(tmp_path):
    if not os.environ.get("DRIVE_DOCBUILDER_ID"):
        pytest.skip("DRIVE_DOCBUILDER_ID not set")
    result = subprocess.run(
        [sys.executable, "scripts/fetch_template.py",
         "--tenant", "demo", "--doc-type", "proposal", "--version", "v1",
         "--cache-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "demo" / "proposal" / "v1").is_dir()
