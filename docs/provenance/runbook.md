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

## Run tests

```bash
# Schema init tests
python3 -m pytest provenance/tests/ -v

# Scanner unit tests (slow first run — compiles DuckDB)
cd provenance/scanner && cargo test
```
