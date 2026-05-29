#!/usr/bin/env python3
"""
Copy approved files to their destination, verify SHA-256, and log results to DuckDB.

Usage:
  # Migrate a batch
  python3 scripts/execute_migration.py --db corpus.duckdb --input batch.json [--dest-root /clients] [--dry-run]

  # Rollback migrated files
  python3 scripts/execute_migration.py --db corpus.duckdb --rollback [--since 2026-01-15T09:00:00] [--dry-run]
"""

import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def execute_migration(
    conn: duckdb.DuckDBPyConnection,
    records: list[dict],
    dest_root: str = None,
    dry_run: bool = False,
) -> dict:
    migrated = 0
    failed = 0
    skipped = 0

    for rec in records:
        source_path = rec.get("source_path", "")
        dest_path = rec.get("dest_path", "")
        classification_id = rec.get("classification_id")

        if dest_root and not dest_path.startswith(dest_root):
            print(
                f"warning: dest_path {dest_path!r} is outside dest-root {dest_root!r}, skipping",
                file=sys.stderr,
            )
            skipped += 1
            continue

        expected_sha = _lookup_sha256(conn, source_path)
        if expected_sha is None:
            print(
                f"warning: {source_path!r} not found in f2_file_index, skipping",
                file=sys.stderr,
            )
            skipped += 1
            continue

        # Already migrated in DB — idempotent skip
        existing = conn.execute(
            "SELECT id, status FROM migrations WHERE path = ? AND status = 'migrated'",
            [source_path],
        ).fetchone()
        if existing:
            skipped += 1
            continue

        src = Path(source_path)
        dst = Path(dest_path)

        # Destination already exists — check hash before deciding
        if dst.exists():
            actual_sha = _sha256_file(dst)
            if actual_sha == expected_sha:
                # Already there with correct content — treat as migrated
                if not dry_run:
                    _upsert_migration(conn, source_path, dest_path, classification_id,
                                      "migrated", migrated_at=datetime.now(timezone.utc))
                skipped += 1
                continue
            else:
                msg = f"dest exists with different hash — refusing to overwrite: {dest_path}"
                print(f"error: {msg}", file=sys.stderr)
                if not dry_run:
                    _upsert_migration(conn, source_path, dest_path, classification_id,
                                      "failed", error=msg)
                failed += 1
                continue

        if dry_run:
            migrated += 1
            continue

        # Create parent dirs and copy
        dst.parent.mkdir(parents=True, exist_ok=True)
        _copy_file(src, dst)

        # Verify hash of the copy
        actual_sha = _sha256_file(dst)
        if actual_sha != expected_sha:
            dst.unlink(missing_ok=True)
            msg = f"SHA-256 mismatch: expected {expected_sha} got {actual_sha}"
            _upsert_migration(conn, source_path, dest_path, classification_id,
                              "failed", error=msg)
            failed += 1
        else:
            _upsert_migration(conn, source_path, dest_path, classification_id,
                              "migrated", migrated_at=datetime.now(timezone.utc))
            migrated += 1

    if dry_run:
        total_would_skip = skipped
        return {"would_migrate": migrated, "would_skip": total_would_skip}
    return {"migrated": migrated, "failed": failed, "skipped": skipped}


def rollback_migrations(
    conn: duckdb.DuckDBPyConnection,
    since: datetime = None,
    dry_run: bool = False,
) -> dict:
    sql = "SELECT id, path, dest_path FROM migrations WHERE status = 'migrated'"
    params = []
    if since:
        sql += " AND migrated_at >= ?"
        params.append(since)

    rows = conn.execute(sql, params).fetchall()
    rolled_back = 0
    skipped = 0

    for row_id, path, dest_path in rows:
        dst = Path(dest_path)
        if dry_run:
            print(f"dry-run rollback: {dest_path!r} → delete, status → proposed",
                  file=sys.stderr)
            rolled_back += 1
            continue

        if dst.exists():
            dst.unlink()
        else:
            print(f"warning: dest not found (already deleted?): {dest_path}", file=sys.stderr)

        conn.execute(
            "UPDATE migrations SET status = 'proposed', migrated_at = NULL WHERE id = ?",
            [row_id],
        )
        rolled_back += 1

    return {"rolled_back": rolled_back, "skipped": skipped, "dry_run": dry_run}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lookup_sha256(conn: duckdb.DuckDBPyConnection, path: str) -> str | None:
    row = conn.execute(
        "SELECT sha256 FROM f2_file_index WHERE path = ?", [path]
    ).fetchone()
    return row[0] if row else None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy_file(src: Path, dst: Path) -> None:
    if src.stat().st_size >= LARGE_FILE_THRESHOLD:
        with src.open("rb") as fsrc, dst.open("wb") as fdst:
            shutil.copyfileobj(fsrc, fdst, length=1024 * 1024)
    else:
        shutil.copy2(src, dst)


def _upsert_migration(
    conn: duckdb.DuckDBPyConnection,
    path: str,
    dest_path: str,
    classification_id: str | None,
    status: str,
    migrated_at: datetime = None,
    error: str = None,
) -> None:
    now = datetime.now(timezone.utc)
    existing = conn.execute(
        "SELECT id FROM migrations WHERE path = ?", [path]
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE migrations SET dest_path=?, status=?, migrated_at=?, error=? WHERE path=?",
            [dest_path, status, migrated_at, error, path],
        )
    else:
        conn.execute(
            """
            INSERT INTO migrations
                (id, path, dest_path, classification_id, status, proposed_at, migrated_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [str(uuid.uuid4()), path, dest_path, classification_id,
             status, now, migrated_at, error],
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Execute or rollback file migrations")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--input", help="JSON input file (or stdin); not used with --rollback")
    parser.add_argument("--dest-root", help="Reject dest_paths not under this prefix")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would happen without writing")
    parser.add_argument("--rollback", action="store_true",
                        help="Rollback migrated files instead of migrating")
    parser.add_argument("--since", help="ISO datetime — only rollback records migrated after this")
    args = parser.parse_args()

    try:
        conn = duckdb.connect(args.db, read_only=args.dry_run and args.rollback)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.rollback:
            since = None
            if args.since:
                try:
                    since = datetime.fromisoformat(args.since)
                except ValueError as e:
                    print(f"error: invalid --since value: {e}", file=sys.stderr)
                    sys.exit(1)
            result = rollback_migrations(conn, since=since, dry_run=args.dry_run)
        else:
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

            result = execute_migration(
                conn,
                records,
                dest_root=args.dest_root,
                dry_run=args.dry_run,
            )
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(json.dumps(result))


if __name__ == "__main__":
    main()
