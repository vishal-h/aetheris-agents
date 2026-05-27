import json
import subprocess
import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "notify_at1qry.py")


def run_script(run_id: str, message: str, env: dict | None = None):
    import os
    e = os.environ.copy()
    if env:
        e.update(env)
    if "AETHERIS_API_BASE" not in (env or {}):
        e.pop("AETHERIS_API_BASE", None)
    return subprocess.run(
        [sys.executable, SCRIPT, run_id, message],
        capture_output=True, text=True, cwd=str(GATEWAY_ROOT), env=e
    )


def test_exit_0_always_when_server_unreachable():
    result = run_script("some-run-id", "hello", {"AETHERIS_API_BASE": "http://localhost:19999"})
    assert result.returncode == 0


def test_output_has_status_key_on_failure():
    result = run_script("some-run-id", "hello", {"AETHERIS_API_BASE": "http://localhost:19999"})
    data = json.loads(result.stdout)
    assert "status" in data
    assert data["status"] == "failed"


def test_failure_reason_is_string():
    result = run_script("some-run-id", "hello", {"AETHERIS_API_BASE": "http://localhost:19999"})
    data = json.loads(result.stdout)
    assert isinstance(data.get("reason"), str)


def test_no_args_exits_nonzero():
    result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert result.returncode != 0


def test_output_is_valid_json_on_failure():
    result = run_script("run-abc", "test message", {"AETHERIS_API_BASE": "http://localhost:19999"})
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


@pytest.mark.integration
def test_returns_ok_for_known_run():
    """Requires live Aetheris server at AETHERIS_API_BASE and a running at1qry."""
    import os
    base = os.environ.get("AETHERIS_API_BASE")
    run_id = os.environ.get("AT1QRY_RUN_ID")
    if not base or not run_id:
        pytest.skip("AETHERIS_API_BASE and AT1QRY_RUN_ID not set")
    result = run_script(run_id, "integration test message", {"AETHERIS_API_BASE": base})
    data = json.loads(result.stdout)
    assert data["status"] == "ok"


@pytest.mark.integration
def test_returns_failed_for_unknown_run_on_live_server():
    """Requires live Aetheris server at AETHERIS_API_BASE."""
    import os
    base = os.environ.get("AETHERIS_API_BASE")
    if not base:
        pytest.skip("AETHERIS_API_BASE not set")
    result = run_script("no-such-run-xyz", "hello", {"AETHERIS_API_BASE": base})
    data = json.loads(result.stdout)
    assert data["status"] == "failed"
