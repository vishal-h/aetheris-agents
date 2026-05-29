# provenance/m4: zip_archaeologist agent

## Context

The zip archaeologist is a sub-agent that processes one zip file end-to-end:
extract → process finds → report. It is spawned by the orchestrator (m4-004),
one per zip. It uses the two scripts from m4-001 and m4-002.

## What to build

`agents/zip_archaeologist.exs`

### Behaviour (4 steps)

**Step 1 — Extract**
```
run_command:
  command: "python3"
  args: ["scripts/extract_zip.py",
         "--zip", "{zip_path}",
         "--staging-dir", "{staging_path}/extractions",
         "--depth", "{depth}"]
```

Parse manifest from stdout.

- `status = 'encrypted'`: update zip_inventory, report, stop.
- `status = 'max_depth'`: report max depth reached, stop.
- `status = 'failed'`: report error, stop.
- `status = 'extracted'`: continue.

**Step 2 — Process finds**

Write the manifest to a UUID temp file, then:
```
run_command:
  command: "python3"
  args: ["scripts/process_zip_finds.py",
         "--db", "{db_path}",
         "--manifest", "{manifest_temp_file}",
         "--staging-path", "{staging_path}"]
```

Parse output: `{total_files, known, new_to_corpus, nested_zips, new_finds}`.

**Step 3 — Handle encrypted status (update DB)**

If Step 1 returned `encrypted`:
```
run_command:
  command: "python3"
  args: ["-c", "import duckdb; c=duckdb.connect('{db_path}'); c.execute(\"INSERT INTO zip_inventory (path, status) VALUES (?, 'encrypted') ON CONFLICT (path) DO UPDATE SET status='encrypted'\", ['{zip_path}']); print('ok')"]
```

**Step 4 — Report**

Output summary:
```
zip: {zip_path}
status: extracted | encrypted | max_depth | failed
files: {total} ({known} known, {new_to_corpus} new to corpus)
nested_zips: {N}
```

### Env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `STAGING_PATH` | `priv/zip_staging` | Root staging directory |

### `task_prompt` structure (set by orchestrator)

```
Process zip file: {zip_path}
Depth: {depth}

STEP 1 — Extract...
STEP 2 — Process finds...
STEP 3 — Handle encrypted...
STEP 4 — Report...

Rules:
- Never modify or delete the source zip at {zip_path}
- If any step exits non-zero, report the error and stop
- Pass the manifest as a UUID temp file between steps
```

## Acceptance criteria

- [ ] Agent evaluates without error
- [ ] `DRY_RUN` / test run against a real small zip completes with `agent_finished`
- [ ] Encrypted zip: logs to `zip_inventory`, reports, stops cleanly
- [ ] Max depth: reports and stops
- [ ] Source zip never modified or deleted
- [ ] UUID temp file used for manifest (no race conditions with parallel agents)
- [ ] `pytest tests/test_zip_archaeologist.py` — agent eval test passes

## Files to create

- `provenance/agents/zip_archaeologist.exs`
- `provenance/tests/test_zip_archaeologist.py` (eval check only — live run is m4-004's acceptance test)

## Notes

**`context_strategy: :full`** — the manifest from Step 1 must remain in context
for Step 2. A rolling strategy might evict it. Use `:full` with `max_steps: 20`.

**Tools:** `["run_command"]` only. This agent never reads file content directly.

**max_spawn_depth.** This is a sub-agent spawned by the orchestrator. It must
not spawn further agents. Set `max_spawn_depth: 0`.

The live end-to-end test (real zip → extract → process → DB) is covered by the
orchestrator acceptance test in m4-004, not here. Keep the archaeologist tests
focused on eval correctness.
