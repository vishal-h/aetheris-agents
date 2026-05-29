#!/usr/bin/env python3
"""Initialize Provenance DuckDB schema. Idempotent — safe to run multiple times."""

import argparse
import sys
import duckdb

TABLES = {
    "f2_file_index": """
        CREATE TABLE IF NOT EXISTS f2_file_index (
            path          TEXT PRIMARY KEY,
            size_bytes    BIGINT,
            modified_at   TIMESTAMP,
            mime_type     TEXT,
            sha256        TEXT,
            status        TEXT DEFAULT 'ok',
            last_scanned  TIMESTAMP
        )
    """,
    "scan_runs": """
        CREATE TABLE IF NOT EXISTS scan_runs (
            id               TEXT PRIMARY KEY,
            root_path        TEXT NOT NULL,
            started_at       TIMESTAMP NOT NULL,
            finished_at      TIMESTAMP,
            status           TEXT DEFAULT 'running',
            files_scanned    BIGINT DEFAULT 0,
            files_new        BIGINT DEFAULT 0,
            files_updated    BIGINT DEFAULT 0,
            duplicates_found BIGINT DEFAULT 0,
            aetheris_run_id  TEXT
        )
    """,
    "classifications": """
        CREATE TABLE IF NOT EXISTS classifications (
            id              TEXT PRIMARY KEY,
            path            TEXT NOT NULL REFERENCES f2_file_index(path),
            client          TEXT,
            financial_year  TEXT,
            doc_type        TEXT,
            confidence      REAL,
            raw_excerpt     TEXT,
            status          TEXT DEFAULT 'proposed',
            classified_at   TIMESTAMP NOT NULL,
            reviewed_at     TIMESTAMP,
            reviewed_by     TEXT,
            aetheris_run_id TEXT
        )
    """,
    "migrations": """
        CREATE TABLE IF NOT EXISTS migrations (
            id                TEXT PRIMARY KEY,
            path              TEXT NOT NULL,
            dest_path         TEXT NOT NULL,
            classification_id TEXT REFERENCES classifications(id),
            status            TEXT DEFAULT 'proposed',
            proposed_at       TIMESTAMP NOT NULL,
            migrated_at       TIMESTAMP,
            error             TEXT,
            aetheris_run_id   TEXT
        )
    """,
    "zip_inventory": """
        CREATE TABLE IF NOT EXISTS zip_inventory (
            path            TEXT PRIMARY KEY,
            size_bytes      BIGINT,
            depth           INTEGER DEFAULT 0,
            parent_zip      TEXT,
            extracted_to    TEXT,
            contents_count  INTEGER,
            new_to_corpus   INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'pending',
            processed_at    TIMESTAMP,
            aetheris_run_id TEXT
        )
    """,
    "zip_contents": """
        CREATE TABLE IF NOT EXISTS zip_contents (
            id            TEXT PRIMARY KEY,
            zip_path      TEXT REFERENCES zip_inventory(path),
            internal_path TEXT NOT NULL,
            sha256        TEXT,
            size_bytes    BIGINT,
            corpus_match  TEXT,
            status        TEXT DEFAULT 'new'
        )
    """,
}

VIEWS = {
    "client_corpus": """
        CREATE VIEW IF NOT EXISTS client_corpus AS
        SELECT
            c.client,
            c.financial_year,
            c.doc_type,
            c.confidence,
            f.path,
            f.size_bytes,
            f.mime_type,
            f.sha256,
            c.status AS classification_status
        FROM classifications c
        JOIN f2_file_index f ON c.path = f.path
        WHERE f.status != 'missing'
        ORDER BY c.client, c.financial_year, c.doc_type
    """,
    "duplicate_groups": """
        CREATE VIEW IF NOT EXISTS duplicate_groups AS
        SELECT
            sha256,
            COUNT(*) AS copy_count,
            SUM(size_bytes) AS total_size,
            MIN(path) AS canonical_candidate,
            ARRAY_AGG(path) AS all_paths
        FROM f2_file_index
        WHERE sha256 IS NOT NULL AND status != 'missing'
        GROUP BY sha256
        HAVING COUNT(*) > 1
    """,
    "migration_queue": """
        CREATE VIEW IF NOT EXISTS migration_queue AS
        SELECT
            c.id AS classification_id,
            f.path AS source_path,
            '/clients/' || c.client || '/' || c.financial_year
                || '/' || c.doc_type || '/' || regexp_extract(f.path, '([^/]+)$', 1) AS proposed_dest,
            c.confidence
        FROM classifications c
        JOIN f2_file_index f ON c.path = f.path
        LEFT JOIN migrations m ON m.classification_id = c.id
        WHERE c.status = 'approved'
          AND m.id IS NULL
          AND f.status != 'missing'
    """,
    "zip_backlog": """
        CREATE VIEW IF NOT EXISTS zip_backlog AS
        SELECT path, size_bytes, depth, status
        FROM zip_inventory
        WHERE status IN ('pending', 'failed')
        ORDER BY depth, size_bytes DESC
    """,
}

# Columns spec requires in f2_file_index; added if absent so Tauri-created tables are compatible.
_F2_REQUIRED_COLUMNS = {
    "size_bytes":   "BIGINT",
    "modified_at":  "TIMESTAMP",
    "mime_type":    "TEXT",
    "sha256":       "TEXT",
    "status":       "TEXT DEFAULT 'ok'",
    "last_scanned": "TIMESTAMP",
}


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    for name, ddl in TABLES.items():
        conn.execute(ddl)
        print(f"table {name}: ok")

    _backfill_f2_columns(conn)

    for name, ddl in VIEWS.items():
        conn.execute(ddl)
        print(f"view  {name}: ok")


def _backfill_f2_columns(conn: duckdb.DuckDBPyConnection) -> None:
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'f2_file_index'"
        ).fetchall()
    }
    for col, col_type in _F2_REQUIRED_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE f2_file_index ADD COLUMN IF NOT EXISTS {col} {col_type}")
            print(f"  added column f2_file_index.{col}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise Provenance DuckDB schema")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    args = parser.parse_args()

    try:
        conn = duckdb.connect(args.db)
    except Exception as e:
        print(f"error: cannot open {args.db}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        init_schema(conn)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
