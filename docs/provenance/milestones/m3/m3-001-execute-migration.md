# provenance/m3: Migration script

## Context

`execute_migration.py` is the script that performs the actual file copies.
It receives a list of migration decisions (source → destination), copies each
file, verifies the copy's SHA-256 hash, and writes the result to the
`migrations` table in DuckDB.

The migration agent (m3-002) calls this script. It should also be runnable
standalone for testing and manual recovery.

## What to build

`scripts/execute_migration.py`

### Input

A JSON array of migration records passed via `--input` or stdin:

```json
[
  {
    "source_path": "/data/archive/acme/FY2024/tax_return.pdf",
    "dest_path":   "/clients/acme/FY2024/tax/tax_return.pdf",
    "classification_id": "uuid-..."
  },
  ...
]
```

### Behaviour per file

1. Look up `sha256` of `source_path` in `f2_file_index` (source of truth)
2. Create destination parent directories (`mkdir -p` equivalent)
3. Copy file to `dest_path`
4. Compute SHA-256 of the copy
5. Compare: if mismatch, delete the copy, log `status = 'failed'`, continue
6. If match, insert/update `migrations` table with `status = 'migrated'`
7. Never delete or modify `source_path`

### Output JSON to stdout

```json
{"migrated": N, "failed": N, "skipped": N}
```

- `migrated` — successful copies with hash verified
- `failed` — copies where hash verification failed (corrupt destination)
- `skipped` — records already in `status = 'migrated'` (idempotent re-run)

### CLI

```
python3 scripts/execute_migration.py \
  --db /data/corpus.duckdb \
  --input migrations_batch.json \
  [--dry-run] \
  [--dest-root /clients]
```

**`--dry-run`:** Print what would be copied without writing any files or DB records.
Output: `{"would_migrate": N, "would_skip": N}` — same format, different keys.

**`--dest-root`:** Optional safety check — reject any `dest_path` that doesn't
start with this prefix. Prevents accidental writes outside the `/clients/` tree.

### DuckDB writes

Insert into `migrations` table on each outcome:

```python
# Success
INSERT INTO migrations (id, path, dest_path, classification_id, status, proposed_at, migrated_at)
VALUES (uuid, source_path, dest_path, classification_id, 'migrated', now(), now())
ON CONFLICT (path) DO UPDATE SET status='migrated', migrated_at=now()

# Failure
INSERT INTO migrations (..., status, error)
VALUES (..., 'failed', "SHA-256 mismatch: expected X got Y")
ON CONFLICT (path) DO UPDATE SET status='failed', error=excluded.error
```

Note: `path` in `migrations` is the source path (FK to `f2_file_index`).

### Rollback helper

Also add a `--rollback` subcommand:

```
python3 scripts/execute_migration.py --db /data/corpus.duckdb --rollback \
  [--since 2026-01-15T09:00:00] \
  [--dry-run]
```

Reads `migrations` table for records with `status = 'migrated'`, deletes the
destination file, resets `status = 'proposed'`. Useful if a batch migration
produced wrong destinations.

## Acceptance criteria

- [ ] Copies files correctly, creates parent directories
- [ ] Verifies SHA-256 of copy against `f2_file_index`; marks `failed` on mismatch
- [ ] Deletes corrupt copy on hash failure (no partial copies left on disk)
- [ ] Idempotent — re-run on same input skips already-migrated files
- [ ] `--dry-run` writes nothing to disk or DB
- [ ] `--dest-root` rejects paths outside the specified root
- [ ] `--rollback` deletes destination files and resets `migrations` status
- [ ] Output JSON correct in all cases
- [ ] `pytest tests/test_execute_migration.py` — 10+ tests pass
- [ ] Tests use real temporary filesystem operations (`tmp_path`)

## Files to create

- `provenance/scripts/execute_migration.py`
- `provenance/tests/test_execute_migration.py`

## Notes

**SHA-256 source of truth.** Use the `sha256` from `f2_file_index` as the
expected hash — do not re-hash the source file during migration. The source was
already hashed at scan time; re-hashing is expensive and unnecessary. Only hash
the destination to verify the copy.

**Destination conflict.** If `dest_path` already exists and its hash matches
`f2_file_index.sha256`, treat it as already migrated (skip). If the hash
differs, fail with an error — never silently overwrite an existing destination
file.

**Path separator normalisation.** Destination paths from the `migration_queue`
view use forward slashes. On the server this is fine; no normalisation needed.

**Large files.** Use streaming copy (`shutil.copyfileobj` with a buffer) for
files above a configurable threshold (default: 100MB). Use `shutil.copy2` for
smaller files (preserves metadata).

**The `proposed_at` field** in the migrations table should be set to `now()` on
insert — it represents when the migration was proposed by the agent, not when
the file was created.
