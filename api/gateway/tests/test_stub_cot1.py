import json
import subprocess
import sys
from pathlib import Path

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "stub_cot1.py")


def base_intent(payload=None):
    if payload is None:
        payload = [
            {
                "name": "Priya Sharma",
                "date_of_birth": "2010-06-15",
                "gender": "Female",
                "course": "Standard I",
                "section": "A",
                "roll_no": "1",
                "father_name": "Rajesh Sharma",
                "father_email": "rajesh.sharma@gmail.com",
                "father_mobile": "9876543210",
            },
            {
                "name": "Arjun Patel",
                "date_of_birth": "2011-03-22",
                "gender": "Male",
                "course": "Standard I",
                "section": "A",
                "roll_no": "2",
            },
            {
                "name": "Ravi Kumar",
                "date_of_birth": None,
                "gender": "Male",
                "course": "Standard II",
                "section": "B",
                "roll_no": None,
            },
        ]
    return {
        "tap_version": "0",
        "message_type": "intent",
        "intent_id": "int-abc12345",
        "correlation_id": "cor-test",
        "seq": 1,
        "depends_on": [],
        "intent_type": "enroll_students",
        "user_intent": "Enroll students",
        "payload": payload,
        "flags": [{"record": "Ravi Kumar", "reason": "dob absent from source"}],
        "provenance": {"source_file": "data/sample.csv", "record_count": 3, "batch": 1, "of": 1},
    }


def run_script(intent):
    intent_str = json.dumps(intent)
    return subprocess.run(
        [sys.executable, SCRIPT, intent_str],
        capture_output=True,
        text=True,
        cwd=str(GATEWAY_ROOT),
    )


def test_exit_0_on_success():
    result = run_script(base_intent())
    assert result.returncode == 0


def test_output_is_valid_json():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert isinstance(report, dict)


def test_result_has_required_keys():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert "tap_version" in report
    assert "message_type" in report
    assert "intent_id" in report
    assert "job_ref" in report
    assert "records" in report
    assert "intent_lifecycle" in report


def test_message_type_is_result():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert report["message_type"] == "result"


def test_job_ref_is_stub():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert report["job_ref"] == "stub-job-ref-001"


def test_intent_id_echoed():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert report["intent_id"] == "int-abc12345"


def test_all_records_present():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert len(report["records"]) == 3


def test_priya_is_deterministic():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    priya = next(r for r in report["records"] if r["name"] == "Priya Sharma")
    assert priya["status"] == "queued"
    assert priya["identity_state"] == "deterministic"
    assert priya["guid"]


def test_arjun_is_deterministic():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    arjun = next(r for r in report["records"] if r["name"] == "Arjun Patel")
    assert arjun["identity_state"] == "deterministic"


def test_ravi_is_non_idempotent():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    ravi = next(r for r in report["records"] if r["name"] == "Ravi Kumar")
    assert ravi["status"] == "queued"
    assert ravi["identity_state"] == "non_idempotent"


def test_intent_lifecycle_status_queued():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert report["intent_lifecycle"]["status"] == "queued"
    assert report["intent_lifecycle"]["stage"] == "etl"


def test_no_args_exits_nonzero():
    result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert result.returncode != 0
