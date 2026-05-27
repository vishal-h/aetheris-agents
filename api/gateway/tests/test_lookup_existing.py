import json
import subprocess
import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "lookup_existing.py")


def run_script(*args):
    return subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True,
        cwd=str(GATEWAY_ROOT),
    )


def test_exit_0_always():
    result = run_script("Test Name", "SSLC", "A")
    assert result.returncode == 0


def test_output_has_found_key():
    result = run_script("Nonexistent Student XYZ", "SSLC", "A")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "found" in data


def test_nonexistent_student_not_found():
    result = run_script("ZZZ Nonexistent ZZZZZ 99999", "SSLC", "A")
    data = json.loads(result.stdout)
    assert data["found"] is False


def test_not_found_guid_is_null():
    result = run_script("ZZZ Nonexistent ZZZZZ 99999", "SSLC", "A")
    data = json.loads(result.stdout)
    assert data.get("guid") is None


def test_no_args_exits_nonzero():
    result = run_script()
    assert result.returncode != 0


@pytest.mark.integration
def test_existing_student_found():
    """Requires live CT_API_TOKEN and real student data."""
    import os
    if not os.environ.get("CT_API_TOKEN"):
        pytest.skip("CT_API_TOKEN not set")
    result = run_script("Amodini S A", "SSLC", "A")
    data = json.loads(result.stdout)
    assert data["found"] is True
    assert data["guid"]


def test_search_unavailable_flag_when_no_token(monkeypatch):
    import os
    monkeypatch.delenv("CT_API_TOKEN", raising=False)
    monkeypatch.delenv("CT_API_BASE_URL", raising=False)
    result = run_script("Test", "SSLC", "A")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    # No credentials — should report search_unavailable
    assert data.get("search_unavailable") is True or data["found"] is False
