#!/usr/bin/env python3
"""Write document classification results to the DuckDB classifications table."""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

THRESHOLD = float(os.environ.get("CLASSIFICATION_THRESHOLD", "0.70"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write document classifications to DuckDB"
    )
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--input", help="JSON input file (default: stdin)")
    args = parser.parse_args()

    if args.input:
        try:
            records = json.loads(Path(args.input).read_text())
        except Exception as e:
            print(f"error: cannot read {args.input}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            records = json.load(sys.stdin)
        except Exception as e:
            print(f"error: cannot parse JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    if not isinstance(records, list):
        print("error: input must be a JSON array", file=sys.stderr)
        sys.exit(1)

    try:
        conn = duckdb.connect(args.db)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = write_classifications(conn, records)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(json.dumps(result))


def write_classifications(
    conn: duckdb.DuckDBPyConnection,
    records: list,
    threshold: float = THRESHOLD,
) -> dict:
    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    for rec in records:
        path = rec.get("path", "")

        # Skip paths not indexed in f2_file_index
        if not conn.execute(
            "SELECT 1 FROM f2_file_index WHERE path = ?", [path]
        ).fetchone():
            print(f"warning: path not in f2_file_index, skipping: {path}", file=sys.stderr)
            skipped += 1
            continue

        # Idempotent — skip paths already proposed or approved
        if conn.execute(
            "SELECT 1 FROM classifications WHERE path = ? AND status IN ('proposed', 'approved')",
            [path],
        ).fetchone():
            skipped += 1
            continue

        confidence = float(rec.get("confidence", 0.0))
        excerpt = (rec.get("raw_excerpt") or "")[:500]
        status = "proposed" if confidence >= threshold else "needs_review"

        conn.execute(
            """
            INSERT INTO classifications
                (id, path, client, financial_year, doc_type,
                 confidence, raw_excerpt, status, classified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                str(uuid.uuid4()),
                path,
                rec.get("client"),
                rec.get("financial_year"),
                rec.get("doc_type"),
                confidence,
                excerpt,
                status,
                now,
            ],
        )
        inserted += 1

    return {"inserted": inserted, "skipped": skipped}


if __name__ == "__main__":
    main()
