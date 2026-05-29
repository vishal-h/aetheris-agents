# provenance/m3: Migration agent

## Context

With `execute_migration.py` in place, the migration agent drives the full
migration: it reads approved classifications from the `migration_queue` view,
groups them into batches, escalates large batches for human approval, executes
via `execute_migration.py`, and reports a summary.

## What to build

`agents/migration_agent.exs`

### Env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `CLIENTS_ROOT` | `/clients` | Destination root on NAS |
| `MIGRATION_BATCH_SIZE` | `50` | Files per migration batch |
| `MIGRATION_ESCALATION_THRESHOLD` | `100` | Batches above this size require ask_human |
| `DRY_RUN` | — | Set to `true` to report without migrating |

### Behaviour

**Step 1 — Pre-flight checks**

```
run_command:
  command: "python3"
  args: ["-c", "import os; print('writable' if os.access('/clients', os.W_OK) else 'not-writable')"]
```

If not writable, report and stop. Do not attempt migration.

```
run_command:
  command: "python3"
  args: ["-c", "import os; print('readonly' if not os.access('/data/archive', os.W_OK) else 'writable')"]
```

Warn (but continue) if `/archive/` is writable — it should be read-only by this point.

**Step 2 — Query migration queue**

```
run_command:
  command: "python3"
  args: ["scripts/list_migration_queue.py", "--db", "{db_path}"]
```

Returns JSON: `{"total": N, "records": [{source_path, dest_path, classification_id}, ...]}`

If total is 0, report "No approved files pending migration." and stop.

**Step 3 — Dry run check**

If `DRY_RUN=true`:
```
run_command:
  command: "python3"
  args: ["scripts/execute_migration.py", "--db", "{db_path}", "--dry-run",
         "--dest-root", "{clients_root}", "--input", "{batch_file}"]
```
Report dry-run summary and stop.

**Step 4 — Batch and escalate**

Split migration queue into batches of `MIGRATION_BATCH_SIZE`.

For any batch where `len(batch) > MIGRATION_ESCALATION_THRESHOLD`:
- Call `ask_human` with:
  - The batch size
  - Sample of source → destination mappings (first 5)
  - Prompt: "Approve migration of N files from /archive/ to /clients/?"
- If human responds with anything other than approval, skip this batch and log it

For batches below the threshold, proceed without escalation.

**Step 5 — Execute migrations**

For each approved batch:
1. Write batch JSON to a UUID-named temp file (same pattern as classification orchestrator)
2. Call `execute_migration.py --input {temp_file} --db {db_path} --dest-root {clients_root}`
3. Parse output `{"migrated": N, "failed": N, "skipped": N}`
4. Accumulate totals

**Step 6 — Report**

Query final state from `migrations` table and report:
- Total files in migration queue at start
- Batches processed
- Files migrated successfully
- Files failed (with sample of failed paths if any)
- Files skipped (already migrated)
- Batches escalated and not approved
- Any remaining files in `migration_queue`

## Supporting script

`scripts/list_migration_queue.py`

Queries the `migration_queue` view and returns:
```json
{
  "total": N,
  "records": [
    {"source_path": "...", "dest_path": "...", "classification_id": "..."},
    ...
  ]
}
```

CLI: `python3 scripts/list_migration_queue.py --db /data/corpus.duckdb [--limit N]`

## Acceptance criteria

**migration_agent.exs:**
- [ ] Agent evaluates without error
- [ ] `DRY_RUN=true` reports without executing
- [ ] Pre-flight check fails cleanly if `/clients` is not writable
- [ ] Escalation triggers for batches above threshold
- [ ] Each batch written to UUID temp file (no race conditions)
- [ ] Accumulates and reports totals correctly
- [ ] Re-run on already-migrated corpus reports all skipped

**list_migration_queue.py:**
- [ ] Returns correct records from `migration_queue` view
- [ ] Returns `{"total": 0, "records": []}` when queue is empty
- [ ] `pytest tests/test_migration_agent.py` passes (query logic + CLI)

**Runbook:**
- [ ] `docs/provenance/runbook.md` updated with migration section
- [ ] Pre-migration checklist (NAS mounts, disk space check) documented
- [ ] Post-migration verification steps documented
- [ ] Rollback procedure documented

## Files to create/modify

- `provenance/agents/migration_agent.exs`
- `provenance/scripts/list_migration_queue.py`
- `provenance/tests/test_migration_agent.py`
- `docs/provenance/runbook.md`

## Notes

**ask_human in migration context.** The escalation prompt should show enough
context for a non-technical person to make a decision: how many files, which
clients, sample paths. It should not require understanding of DuckDB or the
migration_queue view.

**Partial failure.** If a batch has mixed results (some migrated, some failed),
the agent should continue with the next batch rather than stopping. Failed
individual files are logged in `migrations` with `status = 'failed'` and
included in the final report. A subsequent re-run will retry failed files
(since `execute_migration.py` only skips `status = 'migrated'`).

**Disk space pre-check.** Before starting any batch, check available space on
the `/clients/` volume against the total size of pending migrations:

```python
import shutil
stat = shutil.disk_usage("/clients")
# warn if free < 1.2 * pending_bytes
```

Include this check in the pre-flight step. Warn but do not stop — disk space
is the operator's responsibility.

**The `/clients/` tree is created by the migration script** (`execute_migration.py`
calls `mkdir -p` for each destination parent). No separate directory setup step
is required. The first migration to a client creates that client's folder.
