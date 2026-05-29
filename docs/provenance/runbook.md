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

## Run tests

```bash
# Schema init tests
python3 -m pytest provenance/tests/ -v

# Scanner unit tests (slow first run — compiles DuckDB)
cd provenance/scanner && cargo test
```
