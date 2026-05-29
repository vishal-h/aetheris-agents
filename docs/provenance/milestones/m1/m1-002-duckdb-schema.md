# provenance/m1: DuckDB schema v1

## Context

Provenance uses DuckDB as the shared data layer between the f2-scanner binary,
Aetheris agents, and the Tauri dashboard. The schema must be in place before
any scanning or classification work begins.

## What to build

A Python script `scripts/init_db.py` that creates all tables and views in a
DuckDB file if they do not already exist. Idempotent — safe to run multiple times.

**Tables to create** (full DDL in `docs/provenance/specs.md`):
- `f2_file_index` — file metadata and hash (may already exist from Tauri app; preserve data)
- `scan_runs` — scan run tracking
- `classifications` — classification results
- `migrations` — migration log
- `zip_inventory` — zip file tracking
- `zip_contents` — files found inside zips

**Views to create:**
- `client_corpus` — classified files by client/FY/doc_type
- `duplicate_groups` — files grouped by sha256 with count > 1
- `migration_queue` — approved classifications not yet migrated
- `zip_backlog` — zips pending processing

**CLI:**
```
python3 scripts/init_db.py --db /data/corpus.duckdb
```

Prints table and view names created/verified to stdout.
Exit 0 on success, exit 1 on error.

## Acceptance criteria

- [ ] `python3 scripts/init_db.py --db /tmp/test.duckdb` succeeds on empty file
- [ ] Running twice is a no-op (no error, no data loss)
- [ ] All 6 tables present after init
- [ ] All 4 views present after init
- [ ] Existing `f2_file_index` data preserved if table already exists
- [ ] `requirements.txt` includes `duckdb` pinned to a specific version

## Files to create

- `aetheris-agents/provenance/scripts/init_db.py`
- `aetheris-agents/provenance/requirements.txt`
- `aetheris-agents/provenance/tests/test_init_db.py`

## Notes

Use `CREATE TABLE IF NOT EXISTS` and `CREATE VIEW IF NOT EXISTS` throughout.
For `f2_file_index`: if the table exists with a different schema (from the
Tauri app), add any missing columns with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
rather than dropping and recreating.

Schema DDL is authoritative in `docs/provenance/specs.md`. Do not deviate.
