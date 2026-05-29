#!/usr/bin/env python3
"""Export proposed/needs_review classifications to CSV for human review."""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

EXPORT_COLUMNS = [
    "path", "client", "financial_year", "doc_type", "confidence",
    "status", "raw_excerpt", "classified_at",
    "reviewer_action", "reviewer_notes",
]

DEFAULT_STATUSES = ["proposed", "needs_review"]


def export_for_review(
    conn: duckdb.DuckDBPyConnection,
    out_path: Path,
    statuses: list[str] = None,
    client: str = None,
    limit: int = None,
) -> dict:
    if statuses is None:
        statuses = DEFAULT_STATUSES

    placeholders = ", ".join("?" for _ in statuses)
    params = list(statuses)

    where_clauses = [f"status IN ({placeholders})"]
    if client:
        where_clauses.append("client = ?")
        params.append(client)

    where_sql = " AND ".join(where_clauses)
    limit_sql = f"LIMIT {int(limit)}" if limit is not None else ""

    sql = f"""
        SELECT
            path,
            client,
            financial_year,
            doc_type,
            confidence,
            status,
            SUBSTRING(COALESCE(raw_excerpt, ''), 1, 200) AS raw_excerpt,
            classified_at
        FROM classifications
        WHERE {where_sql}
        ORDER BY confidence ASC
        {limit_sql}
    """

    rows = conn.execute(sql, params).fetchall()

    needs_review_count = sum(1 for r in rows if r[5] == "needs_review")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(EXPORT_COLUMNS)
        for row in rows:
            writer.writerow(list(row) + ["", ""])

    return {
        "output": str(out_path),
        "exported": len(rows),
        "needs_review": needs_review_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export classifications for human review")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--status", default=",".join(DEFAULT_STATUSES),
                        help="Comma-separated statuses to export")
    parser.add_argument("--client", help="Filter to one client")
    parser.add_argument("--limit", type=int, help="Cap export size")
    args = parser.parse_args()

    statuses = [s.strip() for s in args.status.split(",") if s.strip()]

    try:
        conn = duckdb.connect(args.db, read_only=True)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = export_for_review(
            conn,
            Path(args.out),
            statuses=statuses,
            client=args.client,
            limit=args.limit,
        )
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(result["output"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
