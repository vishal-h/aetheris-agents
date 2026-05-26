import json
import subprocess
import sys
from pathlib import Path

GATEWAY_ROOT = Path(__file__).parent.parent
REPO_ROOT = GATEWAY_ROOT.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "validate_intent.py")
VOCAB_PATH = str(REPO_ROOT / "domain" / "ct.stu.vocabulary.jsonl")


def run_script(intent, vocab=None):
    intent_str = json.dumps(intent) if not isinstance(intent, str) else intent
    vocab_path = vocab or VOCAB_PATH
    return subprocess.run(
        [sys.executable, SCRIPT, intent_str, vocab_path],
        capture_output=True,
        text=True,
        cwd=str(GATEWAY_ROOT),
    )


def base_intent(overrides=None):
    intent = {
        "tap_version": "0",
        "message_type": "intent",
        "intent_id": "int-abc12345",
        "correlation_id": "cor-test",
        "seq": 1,
        "depends_on": [],
        "intent_type": "enroll_students",
        "user_intent": "Enroll students",
        "payload": [
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
                "mother_name": None,
                "mother_email": None,
                "mother_mobile": None,
                "guardian_name": None,
                "guardian_gender": None,
            }
        ],
        "flags": [],
        "provenance": {"source_file": "data/sample.csv", "record_count": 1, "batch": 1, "of": 1},
    }
    if overrides:
        intent.update(overrides)
    return intent


def test_valid_intent_returns_valid_true():
    result = run_script(base_intent())
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["valid"] is True
    assert report["errors"] == []


def test_output_has_required_keys():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert "valid" in report
    assert "errors" in report
    assert "warnings" in report
    assert "flags" in report


def test_missing_name_field_is_error():
    intent = base_intent()
    intent["payload"][0].pop("name")
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert any("name" in e.lower() for e in report["errors"])


def test_missing_gender_field_is_error():
    intent = base_intent()
    intent["payload"][0].pop("gender")
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert any("gender" in e.lower() for e in report["errors"])


def test_invalid_gender_enum_is_error():
    intent = base_intent()
    intent["payload"][0]["gender"] = "Unknown"
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert any("gender" in e.lower() for e in report["errors"])


def test_valid_gender_female():
    result = run_script(base_intent())
    report = json.loads(result.stdout)
    assert report["valid"] is True


def test_valid_gender_male():
    intent = base_intent()
    intent["payload"][0]["gender"] = "Male"
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is True


def test_father_name_without_contact_is_error():
    intent = base_intent()
    # fatherName present but no fatherMobile or fatherEmail
    intent["payload"][0]["father_name"] = "John Doe"
    intent["payload"][0]["father_email"] = None
    intent["payload"][0]["father_mobile"] = None
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert len(report["errors"]) > 0


def test_father_name_with_email_is_valid():
    intent = base_intent()
    intent["payload"][0]["father_name"] = "John Doe"
    intent["payload"][0]["father_email"] = "john@example.com"
    intent["payload"][0]["father_mobile"] = None
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is True


def test_guardian_name_without_gender_is_error():
    intent = base_intent()
    intent["payload"][0]["guardian_name"] = "Uncle Bob"
    intent["payload"][0]["guardian_gender"] = None
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is False


def test_exit_0_on_invalid_intent():
    intent = base_intent()
    intent["payload"][0].pop("name")
    result = run_script(intent)
    # exit code 0 even when intent is invalid (errors are in the report)
    assert result.returncode == 0


def test_missing_course_field_is_error():
    intent = base_intent()
    intent["payload"][0].pop("course")
    result = run_script(intent)
    report = json.loads(result.stdout)
    assert report["valid"] is False
