# provenance/m1: Scan orchestrator agent

## Context

With the f2-scanner binary available and the DuckDB schema in place, we need an
Aetheris agent that drives the scan end-to-end: initialises the database, runs the
scanner against the NAS archive path, monitors completion, and hands off to the
inventory report agent.

## What to build

`agents/provenance/scan_orchestrator.exs` — a RunConfig that:

1. Calls `init_db.py` to ensure schema is ready
2. Calls `f2-scanner scan` with the configured root path and DB path
3. Polls `scan_runs` table until status = 'complete' or 'failed'
4. On completion, triggers `inventory_report.py` to produce the report
5. Writes report path to stdout and finishes

**Agent should read from env vars:**
- `PROVENANCE_NAS_PATH` — root path to scan (e.g. `/mnt/archive`)
- `PROVENANCE_DB_PATH` — DuckDB file path (e.g. `/data/corpus.duckdb`)

**System prompt guidance:**
- Use `run_command` for all external calls
- Poll scan progress by querying DuckDB via a small Python one-liner
- Do not attempt to parse f2-scanner stdout beyond the final JSON line
- If scanner exits non-zero, report the error and stop — do not retry automatically
- Max steps: 20 (scan itself is one run_command call; polling is the loop)

## Acceptance criteria

- [ ] Agent evaluates without error
- [ ] Runs against a small test directory (< 1000 files) to completion
- [ ] `scan_runs` row created with correct status and counts
- [ ] Inventory report produced at end of run
- [ ] Agent finishes with `agent_finished` reason
- [ ] Trajectory shows `run_command` events for scanner and report script
- [ ] env vars documented in `aetheris-agents/provenance/runbook.md`

## Files to create

- `aetheris-agents/provenance/agents/scan_orchestrator.exs`
- `aetheris-agents/provenance/runbook.md` (env vars, prerequisites, how to run)

## Notes

The polling pattern (check DuckDB every N seconds until done) should use
`run_command` with a Python one-liner rather than a dedicated script:

```
python3 -c "import duckdb; c = duckdb.connect('/data/corpus.duckdb');
print(c.execute('SELECT status, files_scanned FROM scan_runs
WHERE id = ?', ['<run_id>']).fetchone())"
```

The scan of terabytes of data will take hours. The agent must not time out.
Set `max_wait_ms` appropriately or use the `wait_for_event` pattern if the
scanner can write a completion event. For now, polling is sufficient.

Follow agent file conventions in `docs/agent-creation-guide.md`.
Use `__ENV__.file` for sandbox_path.
