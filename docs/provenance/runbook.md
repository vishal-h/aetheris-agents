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
