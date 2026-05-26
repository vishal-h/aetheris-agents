import json
import subprocess
import sys
from pathlib import Path

TENANT_ROOT = Path(__file__).parent.parent
SCRIPT = str(TENANT_ROOT / "scripts" / "gap_analysis.py")


def base_result(records=None):
    if records is None:
        records = [
            {"name": "Priya Sharma", "guid": "aaa-111", "status": "queued", "identity_state": "deterministic"},
            {"name": "Arjun Patel", "guid": "bbb-222", "status": "queued", "identity_state": "deterministic"},
            {"name": "Ravi Kumar", "guid": "ccc-333", "status": "queued", "identity_state": "non_idempotent"},
        ]
    return {
        "tap_version": "0",
        "message_type": "result",
        "intent_id": "int-abc12345",
        "correlation_id": "cor-test",
        "job_ref": "stub-job-ref-001",
        "records": records,
        "intent_lifecycle": {"status": "queued", "stage": "etl"},
        "summary": {
            "total": len(records),
            "queued": len(records),
            "failed": 0,
            "skipped": 0,
        },
    }


def run_script(result_dict):
    result_str = json.dumps(result_dict)
    return subprocess.run(
        [sys.executable, SCRIPT, result_str],
        capture_output=True,
        text=True,
        cwd=str(TENANT_ROOT),
    )


def test_exit_0_always():
    result = run_script(base_result())
    assert result.returncode == 0


def test_output_has_required_keys():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    for key in ["total", "queued", "failed", "skipped", "non_idempotent", "gaps"]:
        assert key in report, f"Missing key: {key}"


def test_total_count_correct():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    assert report["total"] == 3


def test_queued_count_correct():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    assert report["queued"] == 3


def test_non_idempotent_count():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    assert report["non_idempotent"] == 1


def test_ravi_kumar_in_gaps():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    gaps = report["gaps"]
    assert len(gaps) == 1
    assert gaps[0]["record"] == "Ravi Kumar"


def test_gap_has_suggested_action():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    gap = report["gaps"][0]
    assert "suggested_action" in gap
    assert gap["suggested_action"]


def test_gap_reason_is_non_idempotent():
    result = run_script(base_result())
    report = json.loads(result.stdout)
    gap = report["gaps"][0]
    assert "non_idempotent" in gap["reason"].lower() or "dob" in gap["reason"].lower()


def test_no_gaps_when_all_deterministic():
    records = [
        {"name": "Priya Sharma", "guid": "aaa", "status": "queued", "identity_state": "deterministic"},
        {"name": "Arjun Patel", "guid": "bbb", "status": "queued", "identity_state": "deterministic"},
    ]
    result = run_script(base_result(records))
    report = json.loads(result.stdout)
    assert report["non_idempotent"] == 0
    assert report["gaps"] == []


def test_failed_records_counted():
    records = [
        {"name": "Priya Sharma", "guid": "aaa", "status": "failed", "identity_state": "deterministic"},
    ]
    result_dict = base_result(records)
    result_dict["intent_lifecycle"]["status"] = "failed"
    result = run_script(result_dict)
    report = json.loads(result.stdout)
    assert report["failed"] == 1


def test_exit_0_even_with_bad_json_arg():
    proc = subprocess.run(
        [sys.executable, SCRIPT, "not-valid-json"],
        capture_output=True,
        text=True,
    )
    # Should still exit 0 per contract; errors go to stderr if any
    assert proc.returncode == 0
