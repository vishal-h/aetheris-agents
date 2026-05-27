#!/usr/bin/env python3
"""package_intent.py <rows_json> <user_intent> [--intent-id IID] [--correlation-id CID] [--seq N] [--source-file PATH]

Packages normalised row dicts into a TAP intent packet for the enroll_students intent.
Flags rows with missing DOB (advisory) in the flags array.
Outputs the TAP intent JSON to stdout.
Exit 0 on success, exit 1 on error.
"""

import argparse
import json
import secrets
import sys


REQUIRED_FIELDS = ["name", "gender", "course", "section"]


def generate_short_id(length: int = 8) -> str:
    return secrets.token_hex(length // 2)


def flag_record(row: dict, index: int) -> dict | None:
    name = row.get("name") or f"row_{index}"
    if not row.get("date_of_birth"):
        return {"record": name, "reason": "dob absent from source"}
    return None


def package_intent(
    rows: list[dict],
    user_intent: str,
    intent_id: str | None = None,
    correlation_id: str | None = None,
    seq: int = 1,
    source_file: str | None = None,
) -> dict:
    if not correlation_id:
        correlation_id = f"cor-{generate_short_id()}"
    if not intent_id:
        intent_id = f"int-{generate_short_id()}"

    flags = []
    for i, row in enumerate(rows):
        flag = flag_record(row, i)
        if flag:
            flags.append(flag)

    provenance: dict = {
        "source_file": source_file or "unknown",
        "record_count": len(rows),
        "batch": seq,
        "of": 1,
    }

    return {
        "tap_version": "0",
        "message_type": "intent",
        "intent_id": intent_id,
        "correlation_id": correlation_id,
        "seq": seq,
        "depends_on": [],
        "intent_type": "enroll_students",
        "user_intent": user_intent,
        "payload": rows,
        "flags": flags,
        "provenance": provenance,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rows_json", help="JSON string or file path of normalised rows")
    parser.add_argument("user_intent", help="Original user intent string")
    parser.add_argument("--intent-id", default=None)
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--seq", type=int, default=1)
    parser.add_argument("--source-file", default=None)
    args = parser.parse_args()

    try:
        rows = json.loads(args.rows_json)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON for rows_json: {exc}", file=sys.stderr)
        sys.exit(1)

    packet = package_intent(
        rows=rows,
        user_intent=args.user_intent,
        intent_id=args.intent_id,
        correlation_id=args.correlation_id,
        seq=args.seq,
        source_file=args.source_file,
    )
    print(json.dumps(packet, ensure_ascii=False))


if __name__ == "__main__":
    main()
