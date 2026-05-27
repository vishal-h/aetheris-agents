#!/usr/bin/env python3
"""build_etl_job.py <intent_json> <context_json> <behaviour_jsonl>

Builds an ETL job list from a TAP enroll_students intent.

Maps TAP payload fields (snake_case) → API PascalCase.
Generates deterministic UUID v5 GUIDs where possible (dob or admissionNumber
present). Falls back to lookup_existing.py for deduplication guard; if
unavailable, assigns random UUID v4 and flags non_idempotent.

Output (stdout):
  First line:  # JOB_KEY: <sha256_of_stable_payload>
  Subsequent:  METHOD\\tENDPOINT\\tJSON_PAYLOAD  (one per capability per student)

Exit 0 on success, exit 1 on fatal error.
"""

import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

# Fixed namespace — generated 2026-05-26, commit and never change
CT_STU_NAMESPACE = uuid.UUID("f435adac-82f1-4894-beee-0c6128fa9216")

DOB_SENTINEL = "0001-01-01T00:00:00"

GENDER_MAP = {"female": 0, "male": 1, "other": 90}


def _gender_int(value: str | None) -> int:
    if not value:
        return 1
    return GENDER_MAP.get(value.strip().lower(), 1)


def _date_to_api(value: str | None) -> str:
    if not value:
        return DOB_SENTINEL
    v = value.strip()
    return v if "T" in v else v + "T00:00:00"


def _student_guid(inst_id: str, course_name: str, name: str,
                  dob: str | None, admission: str | None) -> tuple[str, bool]:
    sentinel = DOB_SENTINEL
    if admission:
        discriminator = admission.strip()
        idempotent = True
    elif dob and dob != sentinel and dob != "0001-01-01":
        discriminator = dob.strip()
        idempotent = True
    else:
        return str(uuid.uuid4()), False

    key = "|".join([
        inst_id.strip().lower(),
        course_name.strip().lower(),
        name.strip().lower(),
        discriminator,
    ])
    return str(uuid.uuid5(CT_STU_NAMESPACE, key)), True


def _lookup_existing(name: str, course: str, section: str, scripts_dir: Path) -> str | None:
    """Returns guid if found in ct-api, None otherwise."""
    try:
        r = subprocess.run(
            [sys.executable, str(scripts_dir / "lookup_existing.py"), name, course, section],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            if data.get("found"):
                return data.get("guid")
    except Exception:
        pass
    return None


def _load_behaviour(path: str) -> list[dict]:
    steps = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("record_type") == "execution" and rec.get("intent") == "enroll_students":
                    steps.append(rec)
    except Exception:
        pass
    return steps


def _condition_met(row: dict, step: dict) -> bool:
    when = step.get("when")
    if not when:
        return True
    field = when.get("field", "")
    # Map behaviour camelCase field names to intent payload snake_case keys
    field_map = {
        "fatherName": "father_name",
        "motherName": "mother_name",
        "guardianName": "guardian_name",
        "rollNo": "roll_no",
    }
    snake = field_map.get(field, field)
    present = bool(row.get(snake) or row.get(field))
    return present == when.get("present", True)


def _job_key(intent: dict) -> str:
    stable = {
        "correlation_id": intent.get("correlation_id", ""),
        "intent_type": intent.get("intent_type", ""),
        "payload": intent.get("payload", []),
    }
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True).encode()
    ).hexdigest()[:64]


def build(intent: dict, context: dict, behaviour_path: str, scripts_dir: Path) -> list[str]:
    inst_id = context.get("inst_id", "")
    course_map: dict[str, str] = context.get("course_map", {})
    term_name: str = context.get("term_name", "Annual")
    payload = intent.get("payload", [])
    steps = _load_behaviour(behaviour_path)

    lines: list[str] = []

    for row in payload:
        name = row.get("name") or ""
        course_name = row.get("course") or ""
        section = row.get("section") or ""
        course_id = course_map.get(course_name, "")

        dob = row.get("date_of_birth") or row.get("dob")
        doa = row.get("doa")
        admission = row.get("admissionNumber") or row.get("admission_number")

        student_id, idempotent = _student_guid(inst_id, course_name, name, dob, admission)

        if not idempotent:
            existing = _lookup_existing(name, course_name, section, scripts_dir)
            if existing:
                student_id = existing
                idempotent = True

        roll_no_raw = row.get("roll_no")
        roll_no = int(roll_no_raw) if roll_no_raw and str(roll_no_raw).isdigit() else 0

        for step in steps:
            if not _condition_met(row, step):
                continue

            cap = step.get("capability", "")

            if cap == "create_student":
                student_payload: dict = {
                    "Id": student_id,
                    "InstId": inst_id,
                    "Name": name,
                    "Gender": _gender_int(row.get("gender")),
                    "CourseId": course_id,
                    "SecName": section,
                    "TermName": term_name,
                    "DOB": _date_to_api(dob),
                    "DOA": _date_to_api(doa),
                    "RollNo": roll_no,
                    "Email": row.get("email"),
                    "Mobile": row.get("mobile"),
                }
                if admission:
                    student_payload["AdmissionNumber"] = admission
                lines.append(f"POST\t/api/stu/Student\t{json.dumps(student_payload, ensure_ascii=False)}")

            # TODO: update_father_details, update_mother_details, update_guardian_details —
            # ETL endpoint format unconfirmed (PUT vs POST, path vs body). Omitted until
            # CT dev team confirms the correct ETL method for family detail updates.

            elif cap == "set_roll_no":
                lines.append(f"PUT\t/api/stu/Student/{student_id}/rollno\t{json.dumps({'RollNo': roll_no}, ensure_ascii=False)}")

    return lines


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: build_etl_job.py <intent_json> <context_json> <behaviour_jsonl>",
              file=sys.stderr)
        sys.exit(1)

    intent_json, context_json, behaviour_path = sys.argv[1], sys.argv[2], sys.argv[3]
    scripts_dir = Path(__file__).parent

    try:
        intent = json.loads(intent_json)
    except json.JSONDecodeError as e:
        print(f"Error: invalid intent JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        context = json.loads(context_json)
    except json.JSONDecodeError:
        context = {}

    job_key = _job_key(intent)
    lines = build(intent, context, behaviour_path, scripts_dir)

    print(f"# JOB_KEY: {job_key}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
