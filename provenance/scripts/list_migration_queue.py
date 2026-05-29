#!/usr/bin/env python3
"""
Query the migration_queue view for approved files pending migration.

Prints JSON to stdout:
  {"total": N, "records": [{"source_path", "dest_path", "classification_id"}, ...]}
"""

import argparse
import json
import sys

import duckdb

SQL = """
SELECT classification_id, source_path, proposed_dest
FROM migration_queue
ORDER BY source_path
"""


def list_migration_queue(
    conn: duckdb.DuckDBPyConnection,
    limit: int = None,
) -> dict:
    sql = SQL
    params = []
    if limit is not None:
        sql += f" LIMIT {int(limit)}"

    rows = conn.execute(sql, params).fetchall()
    records = [
        {
            "source_path": source_path,
            "dest_path": proposed_dest,
            "classification_id": classification_id,
        }
        for classification_id, source_path, proposed_dest in rows
    ]
    return {"total": len(records), "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description="List files pending migration")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--limit", type=int, help="Cap result count")
    args = parser.parse_args()

    try:
        conn = duckdb.connect(args.db, read_only=True)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = list_migration_queue(conn, limit=args.limit)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(f"{result['total']} files pending migration", file=sys.stderr)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
