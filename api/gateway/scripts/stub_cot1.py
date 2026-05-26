#!/usr/bin/env python3
"""stub_cot1.py <intent_json>

Generates a mock TAP result packet for a given TAP intent JSON.
All records → status: "queued", identity_state: "deterministic",
EXCEPT records missing both dob and admissionNumber → identity_state: "non_idempotent".
Includes job_ref: "stub-job-ref-001" and per-record details.
Exit 0 on success, exit 1 on error.
"""

import json
import sys
import uuid

STUB_JOB_REF = "stub-job-ref-001"
CT_STU_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def is_idempotent(row: dict) -> bool:
    dob = row.get("date_of_birth") or row.get("dob")
    admission = row.get("admissionNumber") or row.get("admission_number")
    return bool(dob or admission)


def generate_guid(row: dict) -> str:
    if is_idempotent(row):
        name_str = "|".join([
            (row.get("course") or "").strip().lower(),
            (row.get("name") or "").strip().lower(),
            (row.get("date_of_birth") or row.get("dob") or "").strip(),
        ])
        return str(uuid.uuid5(CT_STU_NAMESPACE, name_str))
    return str(uuid.uuid4())


def build_result(intent: dict) -> dict:
    intent_id = intent.get("intent_id", "")
    correlation_id = intent.get("correlation_id", "")
    payload = intent.get("payload", [])

    records = []
    for row in payload:
        idempotent = is_idempotent(row)
        records.append({
            "name": row.get("name"),
            "guid": generate_guid(row),
            "status": "queued",
            "identity_state": "deterministic" if idempotent else "non_idempotent",
        })

    return {
        "tap_version": "0",
        "message_type": "result",
        "intent_id": intent_id,
        "correlation_id": correlation_id,
        "from": "cot1_stub",
        "to": "at1qry",
        "job_ref": STUB_JOB_REF,
        "records": records,
        "intent_lifecycle": {
            "status": "queued",
            "stage": "etl",
        },
        "summary": {
            "total": len(records),
            "queued": len(records),
            "failed": 0,
            "skipped": 0,
        },
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: stub_cot1.py <intent_json>", file=sys.stderr)
        sys.exit(1)

    try:
        intent = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(f"Error: invalid intent JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    result = build_result(intent)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
