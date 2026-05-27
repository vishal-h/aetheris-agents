import json
import subprocess
import sys
from pathlib import Path

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "build_etl_job.py")
BEHAVIOUR = str(GATEWAY_ROOT.parent / "domain" / "ct.stu.behaviour.jsonl")

INST_ID = "0c250000-2425-11e7-89e2-1cbdb9e7fd04"
SSLC_ID = "09242481-2425-4f10-9f4a-9a6251465c04"

CONTEXT = json.dumps({
    "inst_id": INST_ID,
    "course_map": {"SSLC": SSLC_ID},
    "term_name": "Annual",
})

INTENT_2 = json.dumps({
    "tap_version": "0",
    "message_type": "intent",
    "intent_type": "enroll_students",
    "intent_id": "int-test001",
    "correlation_id": "cor-test001",
    "seq": 1,
    "payload": [
        {
            "name": "Priya Agent",
            "date_of_birth": "2010-06-15",
            "gender": "Female",
            "course": "SSLC",
            "section": "A",
            "roll_no": "101",
            "father_name": "Rajesh Agent",
            "father_email": "rajesh@example.com",
            "father_mobile": "9876543210",
            "mother_name": "Sunita Agent",
            "mother_email": None,
            "mother_mobile": None,
            "guardian_name": None,
            "guardian_gender": None,
            "guardian_email": None,
            "guardian_mobile": None,
            "email": None,
            "mobile": None,
        },
        {
            "name": "Ravi Agent",
            "date_of_birth": None,
            "gender": "Male",
            "course": "SSLC",
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
            "email": None,
            "mobile": None,
        },
    ],
})


def run_script(intent_json, context_json, behaviour_path=BEHAVIOUR):
    return subprocess.run(
        [sys.executable, SCRIPT, intent_json, context_json, behaviour_path],
        capture_output=True, text=True,
        cwd=str(GATEWAY_ROOT),
    )


def _parse_etl(stdout):
    lines = [l for l in stdout.strip().splitlines() if l and not l.startswith("#")]
    jobs = []
    for line in lines:
        parts = line.split("\t", 2)
        assert len(parts) == 3, f"malformed ETL line: {line!r}"
        jobs.append({"method": parts[0], "endpoint": parts[1], "payload": json.loads(parts[2])})
    return jobs


def test_exit_0_on_valid_input():
    result = run_script(INTENT_2, CONTEXT)
    assert result.returncode == 0, result.stderr


def test_output_has_job_key_header():
    result = run_script(INTENT_2, CONTEXT)
    assert "# JOB_KEY:" in result.stdout


def test_create_student_lines_present():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    create_jobs = [j for j in jobs if j["endpoint"] == "/api/stu/Student" and j["method"] == "POST"]
    assert len(create_jobs) == 2


def test_student_payload_pascal_case():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    priya = next(j for j in jobs if j["endpoint"] == "/api/stu/Student" and j["payload"].get("Name") == "Priya Agent")
    assert "Name" in priya["payload"]
    assert "Gender" in priya["payload"]
    assert "CourseId" in priya["payload"]
    assert "InstId" in priya["payload"]
    assert "Id" in priya["payload"]
    assert "SecName" in priya["payload"]
    assert "DOB" in priya["payload"]
    assert "DOA" in priya["payload"]
    assert "SectionName" not in priya["payload"]
    assert "Dob" not in priya["payload"]
    assert "Doa" not in priya["payload"]


def test_gender_mapped_to_integer():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    priya = next(j for j in jobs if j["payload"].get("Name") == "Priya Agent" and j["endpoint"] == "/api/stu/Student")
    ravi = next(j for j in jobs if j["payload"].get("Name") == "Ravi Agent" and j["endpoint"] == "/api/stu/Student")
    assert priya["payload"]["Gender"] == 0  # Female
    assert ravi["payload"]["Gender"] == 1   # Male


def test_course_id_resolved():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    create = next(j for j in jobs if j["endpoint"] == "/api/stu/Student" and j["payload"].get("Name") == "Priya Agent")
    assert create["payload"]["CourseId"] == SSLC_ID


def test_inst_id_in_payload():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    create = next(j for j in jobs if j["endpoint"] == "/api/stu/Student")
    assert create["payload"]["InstId"] == INST_ID


def test_dob_sentinel_when_missing():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    ravi = next(j for j in jobs if j["payload"].get("Name") == "Ravi Agent" and j["endpoint"] == "/api/stu/Student")
    assert ravi["payload"]["DOB"] == "0001-01-01T00:00:00"


def test_dob_set_when_present():
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    priya = next(j for j in jobs if j["payload"].get("Name") == "Priya Agent" and j["endpoint"] == "/api/stu/Student")
    assert priya["payload"]["DOB"] == "2010-06-15T00:00:00"


def test_dob_trailing_zero_not_corrupted():
    # rstrip("T00:00:00") strips chars from the set {T,0,:} so "2010-06-20" → "2010-06-2".
    # The fix uses string concatenation; this test guards against regression.
    intent = json.dumps({
        "tap_version": "0", "message_type": "intent", "intent_type": "enroll_students",
        "intent_id": "int-trz", "correlation_id": "cor-trz", "seq": 1,
        "payload": [{"name": "Zero Test", "date_of_birth": "2010-06-20", "gender": "Male",
                     "course": "SSLC", "section": "A"}],
    })
    result = run_script(intent, CONTEXT)
    jobs = _parse_etl(result.stdout)
    row = next(j for j in jobs if j["endpoint"] == "/api/stu/Student" and j["payload"].get("Name") == "Zero Test")
    assert row["payload"]["DOB"] == "2010-06-20T00:00:00"


def test_deterministic_guid_for_student_with_dob():
    result1 = run_script(INTENT_2, CONTEXT)
    result2 = run_script(INTENT_2, CONTEXT)
    jobs1 = _parse_etl(result1.stdout)
    jobs2 = _parse_etl(result2.stdout)
    priya1 = next(j for j in jobs1 if j["payload"].get("Name") == "Priya Agent" and j["endpoint"] == "/api/stu/Student")
    priya2 = next(j for j in jobs2 if j["payload"].get("Name") == "Priya Agent" and j["endpoint"] == "/api/stu/Student")
    assert priya1["payload"]["Id"] == priya2["payload"]["Id"]


def test_no_family_update_lines_in_etl():
    # Family updates (father/mother/guardian) are excluded from ETL pending
    # confirmation of the correct endpoint format with the CT dev team.
    result = run_script(INTENT_2, CONTEXT)
    jobs = _parse_etl(result.stdout)
    family_jobs = [j for j in jobs if any(k in j["endpoint"].lower() for k in ["father", "mother", "guardian"])]
    assert len(family_jobs) == 0


def test_admission_number_field_name():
    # Must be "AdmissionNumber" not "AdmissionNo".
    intent = json.dumps({
        "tap_version": "0", "message_type": "intent", "intent_type": "enroll_students",
        "intent_id": "int-adm", "correlation_id": "cor-adm", "seq": 1,
        "payload": [{"name": "Adm Test", "date_of_birth": None, "gender": "Male",
                     "course": "SSLC", "section": "A", "admissionNumber": "ADM-001"}],
    })
    result = run_script(intent, CONTEXT)
    jobs = _parse_etl(result.stdout)
    row = next(j for j in jobs if j["endpoint"] == "/api/stu/Student" and j["payload"].get("Name") == "Adm Test")
    assert row["payload"].get("AdmissionNumber") == "ADM-001"
    assert "AdmissionNo" not in row["payload"]


def test_exit_0_on_no_args():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert r.returncode != 0
