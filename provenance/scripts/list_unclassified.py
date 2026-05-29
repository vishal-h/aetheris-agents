#!/usr/bin/env python3
"""
Query DuckDB for unclassified unique files.

Prints a JSON array of file paths (one per unique SHA-256, alphabetically
first path) to stdout. Used by the classification orchestrator to build batches.
"""

import argparse
import json
import sys

import duckdb

SQL = """
SELECT MIN(path) AS path
FROM f2_file_index
WHERE sha256 IS NOT NULL
  AND status != 'missing'
  AND path NOT IN (
      SELECT path FROM classifications WHERE status != 'rejected'
  )
GROUP BY sha256
ORDER BY path
"""


def list_unclassified(conn: duckdb.DuckDBPyConnection) -> list[str]:
    return [row[0] for row in conn.execute(SQL).fetchall()]


def main() -> None:
    parser = argparse.ArgumentParser(description="List unclassified unique files")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    args = parser.parse_args()

    try:
        conn = duckdb.connect(args.db, read_only=True)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        paths = list_unclassified(conn)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(f"{len(paths)} files to classify", file=sys.stderr)
    print(json.dumps(paths))


if __name__ == "__main__":
    main()
