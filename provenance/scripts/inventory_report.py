#!/usr/bin/env python3
"""Provenance inventory report — queries DuckDB and produces a Markdown report."""

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
        report = build_report(conn)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"inventory_{timestamp}.md"
    out_path.write_text(report)
    print(str(out_path))


def build_report(conn: duckdb.DuckDBPyConnection) -> str:
    sections = [
        _section_summary(conn),
        _section_by_filetype(conn),
        _section_fy_distribution(conn),
        _section_duplicate_groups(conn),
        _section_zip_files(conn),
        _section_whats_next(),
    ]
    return "\n\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _section_summary(conn: duckdb.DuckDBPyConnection) -> str:
    scan = conn.execute(
        """
        SELECT id, root_path, started_at, finished_at,
               files_scanned, files_new, files_updated, duplicates_found
        FROM scan_runs
        WHERE status = 'complete'
        ORDER BY started_at DESC
        LIMIT 1
        """
    ).fetchone()

    if scan is None:
        raise RuntimeError("No completed scan run found in scan_runs")

    run_id, root_path, started_at, finished_at, files_scanned, files_new, files_updated, dups = scan

    total_bytes = conn.execute(
        "SELECT COALESCE(SUM(size_bytes), 0) FROM f2_file_index WHERE status != 'missing'"
    ).fetchone()[0]

    unique_files = conn.execute(
        "SELECT COUNT(DISTINCT sha256) FROM f2_file_index WHERE sha256 IS NOT NULL AND status != 'missing'"
    ).fetchone()[0]

    unique_bytes = conn.execute(
        """
        SELECT COALESCE(SUM(size_bytes), 0)
        FROM (
            SELECT MIN(size_bytes) AS size_bytes
            FROM f2_file_index
            WHERE sha256 IS NOT NULL AND status != 'missing'
            GROUP BY sha256
        )
        """
    ).fetchone()[0]

    wasted_bytes = total_bytes - unique_bytes
    duration = _format_duration(started_at, finished_at)

    lines = [
        "# Provenance Inventory Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Run ID | `{run_id}` |",
        f"| Root path | `{root_path}` |",
        f"| Scan started | {started_at} |",
        f"| Scan finished | {finished_at} |",
        f"| Scan duration | {duration} |",
        f"| Files scanned | {files_scanned:,} |",
        f"| Files new | {files_new:,} |",
        f"| Files updated | {files_updated:,} |",
        f"| Unique files (by SHA-256) | {unique_files:,} |",
        f"| Duplicate files | {dups:,} |",
        f"| Total storage size | {_human_size(total_bytes)} |",
        f"| Unique content size | {_human_size(unique_bytes)} |",
        f"| Wasted space (duplicates) | {_human_size(wasted_bytes)} |",
    ]
    return "\n".join(lines)


def _section_by_filetype(conn: duckdb.DuckDBPyConnection) -> str:
    total = conn.execute(
        "SELECT COUNT(*) FROM f2_file_index WHERE status != 'missing'"
    ).fetchone()[0] or 1

    rows = conn.execute(
        """
        SELECT
            COALESCE(mime_type, 'unknown') AS mime,
            COUNT(*) AS cnt,
            COALESCE(SUM(size_bytes), 0) AS sz
        FROM f2_file_index
        WHERE status != 'missing'
        GROUP BY mime
        ORDER BY cnt DESC
        LIMIT 20
        """
    ).fetchall()

    lines = [
        "## By file type",
        "",
        "| MIME type | Count | Total size | % of corpus |",
        "|-----------|------:|----------:|------------:|",
    ]
    for mime, cnt, sz in rows:
        pct = cnt / total * 100
        lines.append(f"| {mime} | {cnt:,} | {_human_size(sz)} | {pct:.1f}% |")
    return "\n".join(lines)


def _section_fy_distribution(conn: duckdb.DuckDBPyConnection) -> str:
    rows = conn.execute(
        """
        SELECT
            COALESCE(CAST(YEAR(modified_at) AS VARCHAR), 'unknown') AS yr,
            COUNT(*) AS cnt,
            COALESCE(SUM(size_bytes), 0) AS sz
        FROM f2_file_index
        WHERE status != 'missing'
        GROUP BY yr
        ORDER BY yr DESC
        LIMIT 15
        """
    ).fetchall()

    lines = [
        "## Estimated FY distribution",
        "",
        "> **Note:** Years are derived from filesystem `modified_at` timestamps, not document",
        "> content. Actual financial year breakdown is determined in Phase 2 classification.",
        "",
        "| Year | File count | Size |",
        "|------|----------:|-----:|",
    ]
    for yr, cnt, sz in rows:
        lines.append(f"| {yr} | {cnt:,} | {_human_size(sz)} |")
    return "\n".join(lines)


def _section_duplicate_groups(conn: duckdb.DuckDBPyConnection) -> str:
    rows = conn.execute(
        """
        SELECT
            sha256,
            COUNT(*) AS copy_count,
            MIN(size_bytes) AS size_each,
            (COUNT(*) - 1) * MIN(size_bytes) AS wasted,
            LIST(path ORDER BY path) AS sample_paths
        FROM f2_file_index
        WHERE sha256 IS NOT NULL AND status != 'missing'
        GROUP BY sha256
        HAVING COUNT(*) > 1
        ORDER BY wasted DESC
        LIMIT 20
        """
    ).fetchall()

    lines = [
        "## Duplicate groups (top 20 by wasted space)",
        "",
    ]

    if not rows:
        lines.append("No duplicates found.")
        return "\n".join(lines)

    lines += [
        "| SHA-256 (prefix) | Copies | Size each | Wasted | Sample paths |",
        "|------------------|-------:|----------:|-------:|--------------|",
    ]
    for sha, copies, size_each, wasted, sample in rows:
        prefix = sha[:12] if sha else "?"
        paths_str = ", ".join(f"`{p}`" for p in (sample or [])[:2])
        lines.append(
            f"| `{prefix}…` | {copies} | {_human_size(size_each or 0)} | {_human_size(wasted or 0)} | {paths_str} |"
        )
    return "\n".join(lines)


def _section_zip_files(conn: duckdb.DuckDBPyConnection) -> str:
    zip_in_index = conn.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(size_bytes), 0)
        FROM f2_file_index
        WHERE mime_type IN ('application/zip', 'application/x-zip-compressed')
           OR lower(path) LIKE '%.zip'
        """
    ).fetchone()
    zip_count, zip_total = zip_in_index

    inv_rows = conn.execute(
        """
        SELECT path, size_bytes, status, contents_count
        FROM zip_inventory
        ORDER BY size_bytes DESC NULLS LAST
        LIMIT 10
        """
    ).fetchall()

    lines = [
        "## Zip files",
        "",
        f"- **{zip_count:,}** zip files found in the corpus ({_human_size(zip_total)} total)",
    ]

    if inv_rows:
        lines += [
            "",
            "### Largest zips (from zip inventory)",
            "",
            "| Path | Size | Status | Contents |",
            "|------|-----:|--------|---------|",
        ]
        for path, sz, status, contents in inv_rows:
            contents_str = str(contents) if contents is not None else "—"
            lines.append(f"| `{path}` | {_human_size(sz or 0)} | {status} | {contents_str} |")
    else:
        lines.append("- Zip inventory not yet populated (run zip_archaeologist to process zips).")

    return "\n".join(lines)


def _section_whats_next() -> str:
    return "\n".join([
        "## What's next",
        "",
        "This report marks the end of **Phase 1 — Inventory**.",
        "",
        "Before proceeding to Phase 2, please review:",
        "",
        "1. **Duplicate groups** — decide which copy to keep as canonical before classification.",
        "2. **Zip files** — run the zip archaeologist agent to extract and index zip contents.",
        "3. **Unknown MIME types** — review files listed as `unknown` to ensure they are",
        "   included in classification scope.",
        "",
        "**Phase 2 — Classification** will use the Aetheris classification agent to assign",
        "each file a client, financial year, and document type. Classifications are proposed",
        "first, then reviewed and approved before any files are moved.",
        "",
        "Contact your Aetheris operator to begin Phase 2.",
    ])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _human_size(n: int | float) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _format_duration(started_at, finished_at) -> str:
    if started_at is None or finished_at is None:
        return "—"
    try:
        delta = finished_at - started_at
        total_secs = int(delta.total_seconds())
        h, rem = divmod(total_secs, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h {m}m {s}s"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"
    except Exception:
        return "—"


if __name__ == "__main__":
    main()
