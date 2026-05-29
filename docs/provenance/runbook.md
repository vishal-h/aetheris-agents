# Provenance — Runbook

## Environment setup

### Python dependencies

```bash
cd aetheris-agents/provenance
python3 -m pip install -r requirements.txt
```

### GitHub CLI

```bash
gh auth login
```

If `gh auth login` succeeds but subsequent commands still fail with auth errors,
check for a conflicting `GITHUB_TOKEN` env var — it shadows keyring credentials:

```bash
unset GITHUB_TOKEN
gh auth status   # should show your account as active
```

---

## Before Phase 2 begins — taxonomy session

Before running the classification agent, capture the client/FY/document-type
taxonomy by interviewing the auditor:

```bash
cd aetheris-agents/provenance
python3 scripts/taxonomy_session.py --auditor "Your Name"
```

This writes `agents/taxonomy.md` (gitignored — stays local). An example of the
expected output is in `agents/taxonomy.md.example`.

For CI or testing without a terminal:

```bash
python3 scripts/taxonomy_session.py --non-interactive --output agents/taxonomy.md
```

The classification agent reads `agents/taxonomy.md` at runtime. If the file is
missing, the agent will not know which clients or document types to assign.

---

## Run the scan orchestrator agent

### Required environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `PROVENANCE_NAS_PATH` | `/mnt/archive` | Root path to scan |
| `PROVENANCE_DB_PATH` | `/data/corpus.duckdb` | DuckDB file path |

Export before running:

```bash
export PROVENANCE_NAS_PATH=/mnt/archive
export PROVENANCE_DB_PATH=/data/corpus.duckdb
```

### Run the agent

```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs
```

### Evaluate the agent file (syntax check, no LLM call)

```bash
cd ~/sandbox/elixirws/aetheris
mix run --eval 'Code.eval_file("../aetheris-agents/provenance/agents/scan_orchestrator.exs")'
```

Note: this will raise at eval time if the env vars are not set.

### Where to find the report

The inventory report is written to `output/` relative to the `provenance/`
directory (`aetheris-agents/provenance/output/`), **not** the Aetheris working
directory. The agent's `sandbox_path` is set to `agent_root` (the `provenance/`
directory), so all relative paths in `run_command` resolve there.

---

## Initialise the DuckDB schema

```bash
python3 provenance/scripts/init_db.py --db /data/corpus.duckdb
```

Idempotent — safe to re-run. If `f2_file_index` already exists (e.g. created by
the Tauri app), missing columns are added with `ALTER TABLE … ADD COLUMN IF NOT
EXISTS`; no data is lost.

---

## Run the scanner

```bash
f2-scanner scan --root /path/to/corpus --db /data/corpus.duckdb
```

Check progress and past runs:

```bash
f2-scanner status --db /data/corpus.duckdb
```

Resume an interrupted scan:

```bash
f2-scanner resume --run-id <id> --db /data/corpus.duckdb
```

---

## Run the classification orchestrator

### Required environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `TAXONOMY_PATH` | `agents/taxonomy.md` | Path to taxonomy rules file |
| `CLASSIFICATION_BATCH_SIZE` | `20` | Files per sub-agent batch |
| `CLASSIFICATION_THRESHOLD` | `0.70` | Confidence threshold for `proposed` vs `needs_review` |
| `CLASSIFICATION_TIMEOUT_MS` | `600000` | Per-batch wait timeout (ms) |
| `DRY_RUN` | — | Set to `true` to report file/batch count without spawning agents |

### Dry run — estimate cost before classifying

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
DRY_RUN=true mix aetheris run ../aetheris-agents/provenance/agents/classification_orchestrator.exs
```

Reports how many files would be classified and how many batches would be spawned.
No agents are spawned and no LLM classification calls are made.

### Run classification

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
export TAXONOMY_PATH=agents/taxonomy.md
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/classification_orchestrator.exs
```

The orchestrator:
1. Queries DuckDB for unique unclassified files (one representative path per SHA-256).
2. Splits into batches of `CLASSIFICATION_BATCH_SIZE` (default 20).
3. Spawns one `classify_batch` sub-agent per batch in parallel.
4. Waits for all sub-agents to finish.
5. Reports classification counts by status and remaining unclassified files.

Re-running is safe — `classify_documents.py` skips paths already `proposed` or
`approved`. Rejected files are re-queued automatically.

### Query unclassified files (standalone)

```bash
python3 provenance/scripts/list_unclassified.py --db /data/corpus.duckdb
```

Prints a JSON array of paths (one per unique SHA-256) to stdout, count to stderr.

---

## Classification review

After the classification orchestrator runs, export proposed classifications for
human review, edit the CSV, then import the decisions.

### Export for review

```bash
python3 provenance/scripts/export_for_review.py \
  --db /data/corpus.duckdb \
  --out output/review_$(date +%Y%m%d).csv
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--status` | `proposed,needs_review` | Comma-separated statuses to export |
| `--client` | — | Filter to one client |
| `--limit` | — | Cap export row count |

Output is ordered by `confidence ASC` — low-confidence results appear first.

Prints the output path and a summary JSON to stdout:
```
output/review_20260115.csv
{"output": "output/review_20260115.csv", "exported": 247, "needs_review": 12}
```

**Large corpora — export per client:**

```bash
for client in acme globex initech; do
  python3 provenance/scripts/export_for_review.py \
    --db /data/corpus.duckdb \
    --client $client \
    --out output/review_${client}.csv
done
```

### Review the CSV

Open in Excel or any spreadsheet tool. Fill in the `reviewer_action` column:
- `approve` — accept the classification
- `reject` — reject it (file will be re-queued on next orchestrator run)
- blank — leave unchanged (skip)

`reviewer_notes` is a free-text field for comments; it is not read back into DuckDB.

### Import decisions

```bash
python3 provenance/scripts/approve_classifications.py \
  --db /data/corpus.duckdb \
  --input output/review_20260115.csv \
  --reviewer "Jane Smith"
```

`--reviewer` defaults to `$USER` if not provided.

Use `--dry-run` to preview what would change without writing to the database:

```bash
python3 provenance/scripts/approve_classifications.py \
  --db /data/corpus.duckdb \
  --input output/review_20260115.csv \
  --dry-run
```

Output JSON: `{"approved": N, "rejected": N, "skipped": N, "errors": N}`

Re-importing the same CSV is safe — rows already in the target status are skipped.

---

## Run the migration agent

### Pre-migration checklist

Before running, confirm:

1. **`/clients/` is mounted and writable** — the agent checks this at start and will stop if not.
2. **`/data/archive/` is mounted read-only** — the agent warns if writable, but does not stop.
3. **Disk space** — the agent estimates pending bytes vs free space and warns if tight.
4. **All classifications reviewed** — run `export_for_review.py` and confirm no `proposed` rows remain that should be rejected before migration.
5. **Taxonomy correct** — once files are copied to `/clients/`, the destination structure is derived from the taxonomy. Correct taxonomy errors before migrating.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `CLIENTS_ROOT` | `/clients` | Destination root on NAS |
| `MIGRATION_BATCH_SIZE` | `50` | Files per batch |
| `MIGRATION_ESCALATION_THRESHOLD` | `100` | Batches above this size require human approval |
| `DRY_RUN` | — | Set to `true` to preview without copying |

### Dry run — preview before committing

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
DRY_RUN=true mix aetheris run ../aetheris-agents/provenance/agents/migration_agent.exs
```

Shows how many files would be migrated and a sample of source → destination mappings.

### Run migration

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
export CLIENTS_ROOT=/clients
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/migration_agent.exs
```

For large batches (above `MIGRATION_ESCALATION_THRESHOLD`), the agent pauses and asks for
human approval. Respond via IEx:

```elixir
Aetheris.respond_to_escalation("run_id", "approve")
```

### Post-migration verification

1. Spot-check 10+ files: confirm they exist in `/clients/` at the expected path.
2. Check the migrations table:
   ```bash
   python3 -c "import duckdb; c=duckdb.connect('/data/corpus.duckdb'); print(c.execute('SELECT status,COUNT(*) FROM migrations GROUP BY status').fetchall())"
   ```
3. Confirm migration queue is empty:
   ```bash
   python3 provenance/scripts/list_migration_queue.py --db /data/corpus.duckdb
   ```
   Expected: `{"total": 0, "records": []}`
4. Re-running the migration agent on an already-migrated corpus is safe — all files
   will be reported as skipped.

---

## Rollback a migration

Use this when a batch produced wrong destination paths or incorrect classifications
were approved. Rollback deletes the destination copies and resets `migrations.status`
to `proposed` so the files re-enter the queue on the next run.

**Source files in `/archive/` are never touched by rollback.**

### Rollback all migrated files

```bash
python3 provenance/scripts/execute_migration.py \
  --db /data/corpus.duckdb \
  --rollback
```

Output: `{"rolled_back": N, "skipped": 0, "dry_run": false}`

### Rollback only recent migrations (since a timestamp)

```bash
python3 provenance/scripts/execute_migration.py \
  --db /data/corpus.duckdb \
  --rollback \
  --since 2026-01-15T09:00:00
```

Only files migrated at or after the given ISO timestamp are rolled back.

### Preview rollback without deleting

```bash
python3 provenance/scripts/execute_migration.py \
  --db /data/corpus.duckdb \
  --rollback \
  --dry-run
```

Prints what would be rolled back to stderr without modifying files or the database.

### After rollback

1. Fix the root cause (incorrect taxonomy, wrong approved classifications, etc.).
2. Re-run `approve_classifications.py` if classifications need correcting.
3. Re-run the migration agent — rolled-back files will appear in the queue again.

---

## Run zip archaeology

Zip archaeology extracts zip files found in the corpus, classifies their
contents as known (duplicate) or new-to-corpus, and registers new finds in
`f2_file_index` so the classification pipeline can pick them up.

### Required environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `STAGING_PATH` | `priv/zip_staging` | Root staging directory |
| `MAX_ZIP_DEPTH` | `4` | Maximum nesting depth for recursive extraction |
| `ZIP_TIMEOUT_MS` | `300000` | Per-zip sub-agent timeout (5 min) |

### Dry run — estimate work before extracting

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
DRY_RUN=true mix aetheris run ../aetheris-agents/provenance/agents/zip_orchestrator.exs
```

Reports the number of pending zips and depth distribution without extracting anything.

### Check pending zips (standalone)

```bash
python3 provenance/scripts/list_pending_zips.py --db /data/corpus.duckdb
python3 provenance/scripts/list_pending_zips.py --db /data/corpus.duckdb --max-depth 2
```

Prints a JSON object with total count and list of `{path, depth}` records.

### Run zip archaeology

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
export STAGING_PATH=priv/zip_staging
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/zip_orchestrator.exs
```

The orchestrator:
1. Queries `f2_file_index` for unprocessed zip files via `list_pending_zips.py`.
2. Spawns one `zip_archaeologist` sub-agent per zip in parallel.
3. Each archaeologist: extracts → classifies finds (known vs new-to-corpus) → updates `zip_inventory`.
4. After all sub-agents finish, escalates once for any encrypted zips (not per zip).
5. Checks for newly discovered nested zips and repeats until no pending zips remain or `MAX_ZIP_DEPTH` is reached.
6. Reports totals: zips processed, files found (known / new-to-corpus), encrypted pending.

New-to-corpus files are added to `f2_file_index` at their `priv/zip_staging/new_finds/` path.
Run the classification orchestrator next to classify them.

### Rollback a zip archaeology pass

Zip archaeology does not copy to `/clients/` — it only writes to `f2_file_index`,
`zip_inventory`, and `zip_contents`, and copies files into `priv/zip_staging/new_finds/`.

To reset a zip's processing status and re-run it:

```bash
python3 -c "
import duckdb
c = duckdb.connect('/data/corpus.duckdb')
c.execute(\"UPDATE zip_inventory SET status='pending' WHERE path='\$ZIP_PATH'\")
# Also remove zip_contents rows for this zip so process_zip_finds re-processes them
c.execute(\"DELETE FROM zip_contents WHERE zip_path='\$ZIP_PATH'\")
c.close()
print('reset done')
"
```

Then re-run the orchestrator.

---

## Run tests

```bash
# Schema init tests
python3 -m pytest provenance/tests/ -v

# Scanner unit tests (slow first run — compiles DuckDB)
cd provenance/scanner && cargo test
```
