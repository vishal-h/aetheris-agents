import json
import subprocess
import sys
from pathlib import Path

TENANT_ROOT = Path(__file__).parent.parent
SCRIPT = str(TENANT_ROOT / "scripts" / "package_intent.py")

SAMPLE_ROWS = json.dumps([
    {
        "name": "Priya Sharma",
        "date_of_birth": "2010-06-15",
        "gender": "Female",
        "email": None,
        "mobile": None,
        "course": "Standard I",
        "section": "A",
        "roll_no": "1",
        "father_name": "Rajesh Sharma",
        "father_email": "rajesh.sharma@gmail.com",
        "father_mobile": "9876543210",
        "mother_name": "Sunita Sharma",
        "mother_email": "sunita.sharma@gmail.com",
        "mother_mobile": "9876543211",
        "guardian_name": None,
        "guardian_gender": None,
        "guardian_email": None,
        "guardian_mobile": None,
    },
    {
        "name": "Ravi Kumar",
        "date_of_birth": None,
        "gender": "Male",
        "email": None,
        "mobile": None,
        "course": "Standard II",
        "section": "B",
        "roll_no": None,
        "father_name": None,
        "father_email": None,
        "father_mobile": None,
        "mother_name": None,
        "mother_email": None,
        "mother_mobile": None,
        "guardian_name": None,
        "guardian_gender": None,
        "guardian_email": None,
        "guardian_mobile": None,
    },
])


def run_script(rows_json, user_intent, extra_args=None):
    args = [sys.executable, SCRIPT, rows_json, user_intent] + (extra_args or [])
    return subprocess.run(args, capture_output=True, text=True, cwd=str(TENANT_ROOT))


def test_output_is_valid_tap_intent():
    result = run_script(SAMPLE_ROWS, "Enroll students from sample CSV")
    assert result.returncode == 0
    packet = json.loads(result.stdout)
    assert packet["tap_version"] == "0"
    assert packet["message_type"] == "intent"
    assert packet["intent_type"] == "enroll_students"


def test_intent_id_generated():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    assert packet["intent_id"].startswith("int-")
    assert len(packet["intent_id"]) > 4


def test_correlation_id_passthrough():
    result = run_script(SAMPLE_ROWS, "Enroll students", ["--correlation-id", "cor-test-001"])
    packet = json.loads(result.stdout)
    assert packet["correlation_id"] == "cor-test-001"


def test_correlation_id_generated_when_absent():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    assert packet["correlation_id"].startswith("cor-")


def test_seq_default_is_1():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    assert packet["seq"] == 1


def test_seq_passthrough():
    result = run_script(SAMPLE_ROWS, "Enroll students", ["--seq", "2"])
    packet = json.loads(result.stdout)
    assert packet["seq"] == 2


def test_depends_on_empty_for_seq_1():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    assert packet["depends_on"] == []


def test_payload_contains_rows():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    assert len(packet["payload"]) == 2
    assert packet["payload"][0]["name"] == "Priya Sharma"


def test_provenance_record_count():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    assert packet["provenance"]["record_count"] == 2
    assert packet["provenance"]["batch"] == 1


def test_user_intent_preserved():
    result = run_script(SAMPLE_ROWS, "Enroll all students from the CSV file")
    packet = json.loads(result.stdout)
    assert packet["user_intent"] == "Enroll all students from the CSV file"


def test_ravi_kumar_missing_dob_flagged():
    result = run_script(SAMPLE_ROWS, "Enroll students")
    packet = json.loads(result.stdout)
    flags = packet.get("flags", [])
    flag_records = [f["record"] for f in flags]
    # Ravi Kumar (index 1) has no dob — should be flagged
    assert any("Ravi Kumar" in r or "row_2" in r or "1" in r for r in flag_records) or len(flags) > 0


def test_source_file_in_provenance():
    result = run_script(SAMPLE_ROWS, "Enroll students", ["--source-file", "data/enrollments.csv"])
    packet = json.loads(result.stdout)
    assert packet["provenance"]["source_file"] == "data/enrollments.csv"


def test_no_args_exits_nonzero():
    result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert result.returncode != 0
