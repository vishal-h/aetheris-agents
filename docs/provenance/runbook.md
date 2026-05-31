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

## Local test sandbox

A standalone script creates a self-contained corpus under
`~/sandbox/provenance-test/` for local end-to-end testing. No NAS or real
client data required.

### Create the sandbox

```bash
python3 provenance/scripts/create_test_sandbox.py
python3 provenance/scripts/create_test_sandbox.py --root ~/sandbox/provenance-test
python3 provenance/scripts/create_test_sandbox.py --overwrite   # recreate from scratch
```

### What it creates

Three clients with realistic documents across multiple financial years,
intentional duplicate groups, and five zip files covering all archaeology
scenarios.

| Item | Detail |
|------|--------|
| Clients | acme (FY2022–2024), globex (FY2023–2024), initech (FY2022) |
| Flat files | 21 text files across 4 doc types (tax, legal, accounts, correspondence) |
| Duplicate groups | 3 groups, 4 duplicate files total |
| Zip files | 5 (see below) |

**Zip files:**

| File | Purpose |
|------|---------|
| `acme_archive_FY2023.zip` | 2 known files + 1 new (`internal_memo_jun2023.txt`) |
| `globex_backup_FY2023.zip` | 1 known + 1 new (`contract_addendum.txt`) |
| `backup_of_backup.zip` | Depth 2 — contains `acme_archive_FY2023.zip` |
| `nested_depth3_outer.zip` | Depth 3 nesting — depth limit test |
| `confidential_board_minutes.zip` | Encrypted — triggers escalation |

### Expected results per pipeline stage

| Stage | Expected |
|-------|----------|
| Scan | 26 files (21 txt + 5 zip), 22 unique, 4 duplicates |
| Zip archaeology | 2 new-to-corpus, 3 known, 1 encrypted, max depth 3 |
| Classification | 22 unique files classified across 3 clients |
| Migration | 22 files copied to `/clients/` structure |

Note: zip files are indexed as flat files by the scanner AND processed separately
by zip archaeology.

### Run the full pipeline against the sandbox

```bash
export PROVENANCE_NAS_PATH=~/sandbox/provenance-test/archive
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb
export CORPUS_SEARCH_MCP_ENABLED=true
```

Run each agent in pipeline order:

```bash
# 1. Scan
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs

# 2. Classify (requires agents/taxonomy.md — see taxonomy session below)
mix aetheris run ../aetheris-agents/provenance/agents/classification_orchestrator.exs

# 3. Review classifications (export, edit CSV, import)
python3 provenance/scripts/export_for_review.py --db ~/sandbox/provenance-test/corpus.duckdb --out /tmp/review.csv
# edit /tmp/review.csv, then:
python3 provenance/scripts/approve_classifications.py --db ~/sandbox/provenance-test/corpus.duckdb --input /tmp/review.csv

# 4. Migrate
mix aetheris run ../aetheris-agents/provenance/agents/migration_agent.exs

# 5. Zip archaeology
mix aetheris run ../aetheris-agents/provenance/agents/zip_orchestrator.exs

# 6. Search (optional smoke test)
SEARCH_QUERY="tax returns for acme FY2024" \
  mix aetheris run ../aetheris-agents/provenance/agents/search_agent.exs
```

### Reset

```bash
python3 provenance/scripts/create_test_sandbox.py --overwrite
rm -f ~/sandbox/provenance-test/corpus.duckdb
```

`--overwrite` recreates the archive directory but leaves `corpus.duckdb` intact.
Delete the database file separately to fully reset all pipeline state.

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

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AETHERIS_MODEL`            | No | `claude-haiku-4-5-20251001` | Default model for all agents across all use cases |
| `AETHERIS_PROVIDER`         | No | `anthropic`                 | Default provider for all agents |
| `PROVENANCE_MODEL`          | No | `AETHERIS_MODEL`            | Override model for all Provenance agents |
| `PROVENANCE_CLASSIFY_MODEL` | No | `PROVENANCE_MODEL`          | Override model for classification agents only |

---

## Model configuration

Model and provider are resolved at agent eval time using a three-level
fallback chain read directly from environment variables:

```
{USE_CASE}_MODEL → AETHERIS_MODEL → hardcoded default
```

The hardcoded default is always `claude-haiku-4-5-20251001` and acts as
a safety net if neither env var is set. There is no application config
layer — agents call `System.get_env` directly.

### Switch all Provenance agents to Sonnet for a session

```bash
export PROVENANCE_MODEL=claude-sonnet-4-6
```

### Switch all agents across all use cases

```bash
export AETHERIS_MODEL=claude-sonnet-4-6
```

### Persistent defaults

Defaults live in `aetheris-agents/.env` (committed to the repo):

```bash
# View current defaults
cat ~/sandbox/elixirws/aetheris-agents/.env

# Edit to change persistent defaults for all future sessions
# Changes take effect after sourcing or opening a new shell:
set -a && source ~/sandbox/elixirws/aetheris-agents/.env && set +a
```

### Local overrides

For machine-specific overrides that should not be committed, use
`aetheris-agents/.env.local` (gitignored):

```bash
echo "AETHERIS_MODEL=claude-sonnet-4-6" \
  >> ~/sandbox/elixirws/aetheris-agents/.env.local
set -a \
  && source ~/sandbox/elixirws/aetheris-agents/.env.local \
  && set +a
```

### When to use Sonnet vs Haiku

| Task | Recommended | Reason |
|------|-------------|--------|
| Scan orchestrator | Haiku | Scripted steps, no reasoning needed |
| Classification batches | Haiku | High volume, excerpt-based judgment |
| Taxonomy session | Sonnet | Nuanced auditor interview |
| Migration agent | Haiku | Scripted steps |
| Zip orchestrator | Haiku | Scripted steps |
| Search agent | Haiku | Metadata lookup, simple broadening logic |
| Capability matrix | Haiku | File reading and summarising |

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

## corpus-search MCP server

The corpus-search MCP is a self-developed stdio JSON-RPC 2.0 server that exposes
DuckDB-backed metadata search to Aetheris agents. It lives at
`provenance/mcp/corpus-search/server.py` and requires no install step beyond
its Python dependencies.

### Installation

```bash
pip install -r provenance/mcp/corpus-search/requirements.txt
```

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORPUS_DB_PATH` | Yes | — | Path to DuckDB corpus file |
| `CORPUS_SEARCH_READ_ONLY` | No | `true` | Set `false` to open read-write |
| `CORPUS_SEARCH_MCP_ENABLED` | Yes (agent) | — | Must be `true` to wire server into agent |

### Test standalone

```bash
export CORPUS_DB_PATH=/data/corpus.duckdb
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | python3 provenance/mcp/corpus-search/server.py
```

### Wiring into an agent

```elixir
db_path = System.get_env("PROVENANCE_DB_PATH") || raise "PROVENANCE_DB_PATH required"

corpus_search_server =
  if System.get_env("CORPUS_SEARCH_MCP_ENABLED") == "true" do
    %{
      server_id: "corpus_search",
      path:      "python3",
      args:      [Path.expand("mcp/corpus-search/server.py")],
      env:       %{"CORPUS_DB_PATH" => db_path}
    }
  end

mcp_servers = [corpus_search_server] |> Enum.reject(&is_nil/1)
```

**Note:** `Path.expand("mcp/corpus-search/server.py")` resolves relative to
the process working directory (`aetheris/` when running `mix aetheris run`),
which resolves to `aetheris-agents/provenance/mcp/corpus-search/server.py`
since `sandbox_path` is set to the `provenance/` directory.

Actually `Path.expand` in Elixir resolves relative to the process cwd (the
`aetheris/` directory). Use an absolute path to avoid ambiguity:

```elixir
args: [Path.join([agent_root, "mcp", "corpus-search", "server.py"])]
```

where `agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))`.

### Tools

| Tool | Description |
|------|-------------|
| `search_corpus` | Keyword + metadata filter search over classified corpus |
| `list_clients` | All clients with file counts and doc type lists |
| `list_documents` | Documents for a client, optionally filtered by FY / doc type |
| `get_document_meta` | Full metadata for a single path; returns `null` if not found |
| `find_duplicates` | All corpus entries sharing a SHA-256 hash |

### Run MCP server tests

```bash
python3 -m pytest provenance/mcp/corpus-search/tests/ -v
```

---

## Run the search agent

The search agent takes a natural language query, searches the corpus via the
corpus-search MCP server, and returns a formatted list of matching documents.

### Required environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PROVENANCE_DB_PATH` | Yes | DuckDB corpus path |
| `CORPUS_SEARCH_MCP_ENABLED` | Yes | Must be `true` to enable MCP server |
| `SEARCH_QUERY` | No | Pre-set query (otherwise the agent uses its default user_prompt) |
| `LATTICE_MCP_ENABLED` | No | Set `true` to enable deeper content search via Matryoshka |

### Run a search

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
export CORPUS_SEARCH_MCP_ENABLED=true
SEARCH_QUERY="tax returns for acme FY2024" \
  mix aetheris run ../aetheris-agents/provenance/agents/search_agent.exs
```

The agent:
1. Calls `search_corpus` with the full query (limit 10).
2. If fewer than 3 results, tries narrower terms or client-based navigation.
3. If `lattice_load` is available, loads top candidates for deeper content search.
4. Returns a formatted list of matching documents with path, client, FY, type, and preview.

---

## Matryoshka content search (optional)

Matryoshka (lattice-mcp) provides deep content search over the corpus —
vector similarity over full document text rather than keyword matching on
raw_excerpt. It is wired into the search agent but disabled by default.

The corpus-search MCP's ILIKE search on raw_excerpt is sufficient for most
queries. Enable Matryoshka when auditors report that keyword search is missing
documents they expect to find — typically on a large corpus where excerpt
coverage is incomplete.

### Install

```bash
cd ~/sandbox/elixirws/aetheris-agents/mcp/stdio/node
npm install
```

Verify the binary exists:

```bash
ls mcp/stdio/node/node_modules/.bin/lattice-mcp
```

### Enable

Set the environment variable before running the search agent:

```bash
export LATTICE_MCP_ENABLED=true
```

The search agent checks both the env var and the binary path at eval time.
If either is missing, Matryoshka is silently skipped and the agent falls back
to corpus-search MCP only.

### How the search agent uses it

When Matryoshka tools appear in the MCP schema, the agent uses them as a
second pass after corpus-search MCP:

1. `search_corpus` returns metadata matches (ILIKE on path/client/raw_excerpt)
2. If results < 3, `lattice_load` loads top candidate files for content search
3. Results are merged and ranked before presentation

### Verify it is active

Check the trajectory of a search run:

```bash
mix aetheris inspect <run_id>
```

Look for `tool_called` events with `server_id: "lattice"`. If none appear,
the binary is missing or LATTICE_MCP_ENABLED was not set.

### When to enable on the real corpus

Enable Matryoshka when:
- Auditors report false negatives on queries that should match known documents
- The corpus exceeds ~10,000 files and excerpt coverage becomes sparse
- Queries involve document content not captured in the first 20 lines

Leave it disabled when:
- Keyword search on raw_excerpt is returning good results
- Running classification or migration agents (Matryoshka adds no value there)
- Debugging search issues — isolate corpus-search MCP first

---

## Validate search quality

Run the validation script before production sign-off. It sends 20 representative
queries to the search agent and measures the pass rate.

### Seed fixture classifications (local testing only)

The `sample_corpus.duckdb` fixture ships with an empty `classifications` table.
Seed it before running validation locally:

```bash
python3 provenance/scripts/seed_search_fixture.py --db /tmp/corpus_seeded.duckdb
```

This copies the fixture and inserts approved classifications for all five known
fixture paths, enabling the search agent to return results.

### Run validation

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
export CORPUS_SEARCH_MCP_ENABLED=true
python3 provenance/scripts/validate_search.py \
  --db /data/corpus.duckdb \
  --queries provenance/tests/fixtures/search_queries.json \
  --threshold 0.85
```

**Pass criteria:** pass_rate ≥ 0.85 (85%). Exits 0 on pass, 1 on fail.

Output JSON includes per-query pass/fail with result counts and run IDs.

| Flag | Default | Description |
|------|---------|-------------|
| `--db` | required | DuckDB corpus path |
| `--queries` | `tests/fixtures/search_queries.json` | Query fixture file |
| `--model` | agent default | Override model |
| `--n` | `1` | Runs per query |
| `--threshold` | `0.85` | Minimum pass rate |
| `--aetheris` | `../aetheris` | Path to aetheris repo |

### Query categories

The 20 queries cover: client+FY (4), client+doc_type (4), content keywords (4),
FY only (2), doc type only (2), multi-term (2), no-results expected (2).

`expected_paths: null` queries verify graceful "no documents found" handling.
`expected_paths: []` queries verify that ≥1 result is returned.

### Register the eval task (once)

```bash
cd ~/sandbox/elixirws/aetheris
mix run ../aetheris-agents/provenance/scripts/register_eval_task.exs
```

This registers the `provenance_search` eval task in the Aetheris eval store
(idempotent). After registration:

```bash
# Smoke-test the MCP server via the eval framework
mix aetheris eval run provenance_search

# Lock a baseline after first passing run
mix aetheris eval baseline lock provenance_search

# Regression check after future changes
mix aetheris eval compare provenance_search
```

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

---

## Before going live

Complete all items in this checklist before running Provenance against
the real corpus.

### Sandbox validation (complete these first)

- [ ] Run taxonomy session against the test sandbox:
      `python3 provenance/scripts/taxonomy_session.py`
      Confirm `provenance/agents/taxonomy.md` is produced.

- [ ] Run classification orchestrator against the sandbox:
      Confirm batches complete, confidence scores are reasonable,
      low-confidence files get `needs_review` status.

- [ ] Run export → review → import cycle:
      `export_for_review.py` → edit CSV → `approve_classifications.py`
      Confirm approved files appear in `migration_queue` view.

- [ ] Run migration agent against the sandbox:
      Confirm files copied to `/clients/` with SHA-256 verified,
      `migrations` table populated, rollback works.

- [ ] Run zip archaeology against the sandbox:
      Confirm 2 new-to-corpus files found, 1 encrypted zip escalates,
      depth-3 nesting handled correctly.

- [ ] Run search validation:
      `python3 provenance/scripts/validate_search.py --db $PROVENANCE_DB_PATH`
      Confirm pass rate ≥ 85%.

- [ ] Run eval sprint:
      `./scripts/sprint.sh eval`
      Confirm all four built-in tasks pass.

### Infrastructure (confirm with operator before real corpus run)

- [ ] NAS archive mount confirmed read-only at `/data/archive/`
- [ ] `/clients/` mounted and writable
- [ ] `PROVENANCE_DB_PATH` points to the real corpus DuckDB
- [ ] `PROVENANCE_NAS_PATH` points to the real archive root
- [ ] Disk space on `/clients/` confirmed sufficient
      (check: `df -h /clients`)
- [ ] `ANTHROPIC_API_KEY` set and credits confirmed
      (check: `mix aetheris doctor`)

### Sign-off

- [ ] Dry run of scan orchestrator: `DRY_RUN=true mix aetheris run ...`
- [ ] Dry run of classification: `DRY_RUN=true mix aetheris run ...`
- [ ] Dry run of migration: `DRY_RUN=true mix aetheris run ...`
- [ ] Stakeholder walkthrough of Tauri dashboard with real data
- [ ] Firm contact sign-off recorded
