#!/usr/bin/env python3
"""
Provenance inventory report — stub for m1-003.
Produces a minimal Markdown report from a completed scan.
Full report (all sections from specs) is implemented in m1-004.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
import duckdb


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Provenance inventory report")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--out", required=True, help="Output directory for the report")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = duckdb.connect(args.db, read_only=True)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        report = _build_report(conn, args.db)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"inventory_{timestamp}.md"
    out_path.write_text(report)
    print(str(out_path))


def _build_report(conn: duckdb.DuckDBPyConnection, db_path: str) -> str:
    scan = conn.execute(
        "SELECT id, root_path, started_at, finished_at, files_scanned, files_new, files_updated, duplicates_found "
        "FROM scan_runs WHERE status = 'complete' ORDER BY started_at DESC LIMIT 1"
    ).fetchone()

    if scan is None:
        raise RuntimeError("No completed scan run found in scan_runs")

    run_id, root_path, started_at, finished_at, files_scanned, files_new, files_updated, dups = scan

    total_size = conn.execute(
        "SELECT COALESCE(SUM(size_bytes), 0) FROM f2_file_index WHERE status != 'missing'"
    ).fetchone()[0]

    mime_rows = conn.execute(
        "SELECT COALESCE(mime_type, 'unknown') AS mime, COUNT(*) AS cnt "
        "FROM f2_file_index WHERE status != 'missing' "
        "GROUP BY mime ORDER BY cnt DESC LIMIT 10"
    ).fetchall()

    lines = [
        f"# Provenance Inventory Report",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Summary",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Run ID | `{run_id}` |",
        f"| Root path | `{root_path}` |",
        f"| Scan started | {started_at} |",
        f"| Scan finished | {finished_at} |",
        f"| Files scanned | {files_scanned:,} |",
        f"| Files new | {files_new:,} |",
        f"| Files updated | {files_updated:,} |",
        f"| Duplicates found | {dups:,} |",
        f"| Total size | {_human_size(total_size)} |",
        f"",
        f"## By file type (top 10)",
        f"",
        f"| MIME type | Count |",
        f"|-----------|-------|",
    ]

    for mime, cnt in mime_rows:
        lines.append(f"| {mime} | {cnt:,} |")

    lines += [
        f"",
        f"---",
        f"*Full report with duplicate groups, FY distribution, and zip analysis: see m1-004.*",
    ]

    return "\n".join(lines) + "\n"


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


if __name__ == "__main__":
    main()
