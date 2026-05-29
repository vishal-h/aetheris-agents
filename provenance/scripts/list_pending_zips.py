#!/usr/bin/env python3
"""
List zip files pending extraction from the corpus.

Queries f2_file_index for zip files not yet in zip_inventory (or still
pending). Results ordered by depth then path so shallow zips are processed
before nested ones.

Usage:
  python3 scripts/list_pending_zips.py --db /data/corpus.duckdb [--max-depth N]
"""

import argparse
import json
import sys

import duckdb

SQL = """
SELECT f.path, COALESCE(zi.depth, 0) AS depth
FROM f2_file_index f
LEFT JOIN zip_inventory zi ON zi.path = f.path
WHERE (f.mime_type IN ('application/zip', 'application/x-zip-compressed')
       OR lower(f.path) LIKE '%.zip')
  AND f.status != 'missing'
  AND (zi.status IS NULL OR zi.status = 'pending')
ORDER BY COALESCE(zi.depth, 0), f.path
"""


def list_pending_zips(conn: duckdb.DuckDBPyConnection, max_depth: int | None = None) -> dict:
    rows = conn.execute(SQL).fetchall()
    zips = [{"path": r[0], "depth": r[1]} for r in rows]
    if max_depth is not None:
        zips = [z for z in zips if z["depth"] <= max_depth]
    return {"total": len(zips), "zips": zips}


def main() -> None:
    parser = argparse.ArgumentParser(description="List pending zip files")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--max-depth", type=int, default=None,
                        help="Only return zips at or below this depth")
    args = parser.parse_args()

    try:
        conn = duckdb.connect(args.db)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = list_pending_zips(conn, max_depth=args.max_depth)
        print(json.dumps(result))
        print(f"{result['total']} zips pending", file=sys.stderr)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
