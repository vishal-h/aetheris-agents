#!/usr/bin/env python3
"""gap_analysis.py <result_json>

Analyses a TAP result packet and produces a gap report.
Output: {"total": N, "queued": N, "failed": N, "skipped": N, "non_idempotent": N, "gaps": [...]}
Each gap entry: {"record": str, "reason": str, "suggested_action": str}
Exit 0 always.
"""

import json
import sys


def analyse(result: dict) -> dict:
    records = result.get("records", [])

    total = len(records)
    queued = 0
    failed = 0
    skipped = 0
    non_idempotent = 0
    gaps = []

    for rec in records:
        status = rec.get("status", "")
        identity_state = rec.get("identity_state", "")

        if status == "queued":
            queued += 1
        elif status == "failed":
            failed += 1
        elif status == "skipped":
            skipped += 1

        if identity_state == "non_idempotent":
            non_idempotent += 1
            gaps.append({
                "record": rec.get("name", "unknown"),
                "reason": "non_idempotent identity — no stable discriminator (dob or admissionNumber)",
                "suggested_action": "add DOB or admissionNumber to source data",
            })

        if status == "failed":
            reason = rec.get("reason", "unknown failure")
            if identity_state != "non_idempotent":
                gaps.append({
                    "record": rec.get("name", "unknown"),
                    "reason": reason,
                    "suggested_action": "review failure reason and re-submit",
                })

    return {
        "total": total,
        "queued": queued,
        "failed": failed,
        "skipped": skipped,
        "non_idempotent": non_idempotent,
        "gaps": gaps,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"total": 0, "queued": 0, "failed": 0, "skipped": 0, "non_idempotent": 0, "gaps": []}))
        return

    try:
        result = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(json.dumps({"total": 0, "queued": 0, "failed": 0, "skipped": 0, "non_idempotent": 0, "gaps": []}))
        return

    report = analyse(result)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
