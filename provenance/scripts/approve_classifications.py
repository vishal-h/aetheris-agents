#!/usr/bin/env python3
"""Import a reviewed CSV and apply approve/reject decisions to DuckDB."""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

VALID_ACTIONS = {"approve", "reject", ""}


def apply_reviews(
    conn: duckdb.DuckDBPyConnection,
    rows: list[dict],
    reviewer: str,
    dry_run: bool = False,
) -> dict:
    approved = 0
    rejected = 0
    skipped = 0
    errors = 0
    now = datetime.now(timezone.utc)

    for row in rows:
        path = row.get("path", "").strip()
        action = row.get("reviewer_action", "").strip().lower()

        if action not in VALID_ACTIONS:
            print(f"warning: invalid reviewer_action {action!r} for {path!r}, skipping",
                  file=sys.stderr)
            skipped += 1
            continue

        if not action:
            skipped += 1
            continue

        existing = conn.execute(
            "SELECT id, status FROM classifications WHERE path = ?", [path]
        ).fetchone()

        if existing is None:
            print(f"warning: path not found in classifications, skipping: {path}",
                  file=sys.stderr)
            skipped += 1
            continue

        _, current_status = existing
        target_status = "approved" if action == "approve" else "rejected"

        if current_status == target_status:
            skipped += 1
            continue

        if not dry_run:
            conn.execute(
                "UPDATE classifications SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE path = ?",
                [target_status, reviewer, now, path],
            )
        else:
            print(f"dry-run: {path!r} {current_status!r} → {target_status!r}",
                  file=sys.stderr)

        if action == "approve":
            approved += 1
        else:
            rejected += 1

    return {"approved": approved, "rejected": rejected, "skipped": skipped, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply reviewed CSV decisions to DuckDB")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--input", required=True, help="Reviewed CSV file")
    parser.add_argument("--reviewer", default=os.environ.get("USER", "unknown"),
                        help="Reviewer name (default: $USER)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print changes without writing to DB")
    args = parser.parse_args()

    try:
        with open(args.input, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except Exception as e:
        print(f"error: cannot read {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        conn = duckdb.connect(args.db, read_only=args.dry_run)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = apply_reviews(conn, rows, reviewer=args.reviewer, dry_run=args.dry_run)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(json.dumps(result))


if __name__ == "__main__":
    main()
