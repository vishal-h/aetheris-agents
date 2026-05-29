# provenance/m4: zip orchestrator

## Context

The orchestrator drives the full zip archaeology process: it finds all zip files,
spawns archaeologist sub-agents in parallel, handles nested zips in successive
passes, and presents a single escalation for encrypted zips at the end of each
pass.

## What to build

`agents/zip_orchestrator.exs` + `scripts/list_pending_zips.py`

### Supporting script: `list_pending_zips.py`

Queries `f2_file_index` and `zip_inventory` to find zips that haven't been
processed yet.

```sql
SELECT f.path, COALESCE(zi.depth, 0) AS depth
FROM f2_file_index f
LEFT JOIN zip_inventory zi ON zi.path = f.path
WHERE (f.mime_type IN ('application/zip', 'application/x-zip-compressed')
       OR lower(f.path) LIKE '%.zip')
  AND f.status != 'missing'
  AND (zi.status IS NULL OR zi.status = 'pending')
ORDER BY COALESCE(zi.depth, 0), f.path
```

Output JSON:
```json
{"total": N, "zips": [{"path": "...", "depth": 0}, ...]}
```

CLI: `python3 scripts/list_pending_zips.py --db /data/corpus.duckdb [--max-depth N]`

### Orchestrator behaviour

**Env vars:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `STAGING_PATH` | `priv/zip_staging` | Root staging directory |
| `MAX_ZIP_DEPTH` | `4` | Maximum nesting depth |
| `ZIP_TIMEOUT_MS` | `300000` | Per-zip timeout (5 min) |
| `DRY_RUN` | — | Report without spawning |

**Step 1 — Query pending zips**

Call `list_pending_zips.py`. If total is 0, report "No zips pending." and stop.

Report: total zips, depth distribution.

**Step 2 — Dry run check**

If `DRY_RUN=true`: report zip count, depth breakdown, estimated batches, stop.

**Step 3 — Spawn archaeologists (one pass)**

Spawn one `zip_archaeologist` sub-agent per zip using `spawn_agent`:
- tools: `["run_command"]`
- max_steps: 20
- max_spawn_depth: 0
- task_prompt: filled from the zip path and depth

Collect all run_ids into a list.

**Step 4 — Wait**

Call `wait_for_all` with all run_ids and `ZIP_TIMEOUT_MS` timeout.

**Step 5 — Handle encrypted zips (single escalation)**

After `wait_for_all`, query encrypted zips from this pass:
```python
SELECT path FROM zip_inventory WHERE status = 'encrypted'
```

If any: call `ask_human` with the full list and prompt:
```
N encrypted zip(s) found. Please provide passwords to decrypt and re-run,
or acknowledge to skip them:
{list of paths}
```

Do not fail the run if the human skips — log as accepted and continue.

**Step 6 — Check for nested zips (multi-pass)**

Query `list_pending_zips.py` again. If new pending zips exist (discovered as
nested zips in this pass) and current pass < `MAX_ZIP_DEPTH`: go back to Step 3.

Otherwise: proceed to Step 7.

**Step 7 — Final report**

Query and report:
- Total zips processed (by status: processed / encrypted / failed / max_depth)
- Total files found across all zips (known / new_to_corpus)
- New-to-corpus files added to `f2_file_index`
- Encrypted zips pending (if human skipped the escalation)
- Passes completed
- Instruction: "Run the classification orchestrator to classify new finds."

## Acceptance criteria

**list_pending_zips.py:**
- [ ] Returns only unprocessed zips (NULL or `pending` in zip_inventory)
- [ ] `--max-depth` filters to zips at or below that depth
- [ ] Results ordered by depth then path
- [ ] `pytest tests/test_zip_orchestrator.py::test_list_*` passes

**zip_orchestrator.exs:**
- [ ] Agent evaluates without error
- [ ] `DRY_RUN=true` reports without spawning
- [ ] Spawns correct number of sub-agents
- [ ] Encrypted zip escalation fires once per pass (not per zip)
- [ ] Multi-pass: re-queries and spawns again when nested zips exist
- [ ] Final report includes new-to-corpus count
- [ ] Re-run on fully processed corpus reports "No zips pending"
- [ ] All tests pass: `pytest tests/test_zip_orchestrator.py`
- [ ] Runbook updated with zip archaeology section

## Files to create/modify

- `provenance/agents/zip_orchestrator.exs`
- `provenance/scripts/list_pending_zips.py`
- `provenance/tests/test_zip_orchestrator.py`
- `docs/provenance/runbook.md`

## Notes

**One escalation per pass, not per zip.** The orchestrator waits for all
archaeologists to finish before collecting the encrypted list. This avoids
interrupting the operator multiple times mid-pass.

**Nested zip depth.** `zip_archaeologist.exs` passes `--depth {depth+1}` to
`extract_zip.py`. The orchestrator gets the depth from `list_pending_zips.py`
output. Nested zips discovered during extraction are added to `zip_inventory`
with `status = 'pending'` and `depth = parent_depth + 1` by
`process_zip_finds.py`.

**Pass limit.** The orchestrator tracks pass count and stops after `MAX_ZIP_DEPTH`
passes regardless of whether pending zips remain. Log any remaining as
"max depth reached — not processed."

**After m4 completes.** New-to-corpus files in `f2_file_index` are classified
by re-running the m2 classification orchestrator. The migration agent then
picks them up via the `migration_queue` view. No changes to m2 or m3 needed —
the pipeline is already generic over the source of files in `f2_file_index`.
