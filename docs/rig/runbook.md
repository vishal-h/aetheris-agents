# Rig — Runbook

---

## Environment variables

| Variable | Required | Description |
|----------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | Absolute path to `aetheris/priv/aetheris.db` |
| `AETHERIS_AGENTS_PATH` | Yes (orchestrator) | Absolute path to `aetheris-agents/` root |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | Absolute path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | Set `true` to enable corpus-search MCP |

All variables except `CORPUS_SEARCH_MCP_ENABLED` are optional at startup —
Rig renders "not connected" placeholders for features that require them.

---

## Development

```bash
cd aetheris-agents/rig

export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb  # optional

cargo tauri dev
```

---

## Building

```bash
cd aetheris-agents/rig
cargo tauri build
```

Output binary: `src-tauri/target/release/bundle/`

---

## Running against the test sandbox

```bash
# Create/reset the test sandbox
python3 provenance/scripts/create_test_sandbox.py --overwrite

# Run the scan orchestrator to populate aetheris.db and corpus.duckdb
export PROVENANCE_NAS_PATH=~/sandbox/provenance-test/archive
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs

# Open Rig
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
cargo tauri dev
```

---

## Harness module

The Harness module reads from `aetheris.db` and `priv/runs/*/trajectory.json`.
It has two sidebar sections: **Runs** and **Diff**.

### Runs — three tabs

**Run list tab:**
- Label, status badge, model, started at, duration, steps
- Click any row to select it — enables the Events and Trajectory tabs
- Refresh button — no auto-refresh

**Event log tab** (requires a selected run):
- All events for the selected run, ordered by seq
- Step number, event type, timestamp, payload preview
- Colour coding by event type
- Polls every 2s while the run status is `running`; stops on `run_complete`

**Trajectory tab** (requires a selected run):
- Reads `priv/runs/{run_id}/trajectory.json` — the harness's immutable snapshot
- Meta panel (collapsible): model, provider, mode, steps, duration, tools,
  system prompt, user prompt
- Events grouped by step; each step group is collapsible (open by default)
- Click any event row to expand the full pretty-printed JSON payload
- Export JSON button — copies the trajectory file to a user-chosen path

### Diff

Navigate to the **Diff** section in the sidebar to compare two runs.

- Select Run A and Run B from the dropdowns (same list as the run list tab)
- Click Compare — loads both trajectory files in parallel
- Metadata table: model, provider, mode, step count, max steps, total LLM
  latency, terminal reason, tools — rows that differ are highlighted
- Step path table: per-step tool calls for each run; gaps where one run has
  no matching step shown as —

### Status badges

| Status | Colour |
|--------|--------|
| `done` | Green |
| `running` | Amber (animated) |
| `failed` | Red |
| `paused` | Blue |
| `idle` | Grey |

### Not connected

If `AETHERIS_DB_PATH` is not set or the file doesn't exist, the Harness
module shows a "Not connected" placeholder with the path to set.

---

## Orchestrator module

The Orchestrator module runs a natural language request through a plan →
confirm → execute workflow. Requires `AETHERIS_AGENTS_PATH` and
`AETHERIS_DB_PATH` to be set.

### Workflow

1. Type a request in the textarea and click **Run**
2. Rig spawns `agents/mock_orchestrator.exs` via `mix run` with the request
   passed as `ORCHESTRATOR_REQUEST`
3. After ~2s, a plan appears showing the steps the orchestrator intends to run
4. Click **Approve** to execute, or **Cancel** to abort
5. Approved: steps animate through pending → running → done in real time
6. Done: click **Run another** to reset

### States

| State | What you see |
|-------|-------------|
| `idle` | Textarea + Run button |
| `planning` | Spinner (~2s) |
| `plan_ready` | Step list + Approve / Cancel |
| `executing` | Step list with live status icons |
| `done` | Green checkmark + Run another |
| `cancelled` | Cancelled message + Run another |
| `error` | Error message + Run another |

---

## Provenance module

See `docs/provenance/runbook.md` for full Provenance documentation.

Quick reference:
- Corpus overview: `PROVENANCE_DB_PATH` must be set
- Classification review: approve/reject proposed classifications
- Migration status: progress by client
- Zip inventory: processed/encrypted/pending counts

---

## Common issues

### Harness tab shows "Not connected"

Set `AETHERIS_DB_PATH` and restart:
```bash
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
```

### Run list is empty

`aetheris.db` exists but has no runs. Run any agent via `mix aetheris run`
and refresh.

### Events table shows no events for a run

The run was recorded but the harness may have crashed before persisting
events. Check `mix aetheris inspect <run_id>` for details.

### Trajectory tab shows an error for a completed run

The trajectory file may not have been written — this can happen if the
harness crashed at run completion. Check whether
`priv/runs/{run_id}/trajectory.json` exists on disk. If absent, the run
data is only available in SQLite via the Events tab.

### Orchestrator shows "AETHERIS_AGENTS_PATH not set"

Set the variable and restart:
```bash
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
```

### Orchestrator plan never appears (spinner doesn't resolve)

The mock script failed to start. Temporarily set `stderr` to inherit in
`orchestrate.rs` (`Stdio::inherit()` instead of `Stdio::null()`) to see
Mix compile errors. Common cause: `aetheris_dir` is wrong (check
`AETHERIS_DB_PATH` points to the correct file).

### cargo tauri dev fails to compile

Ensure Rust toolchain is up to date:
```bash
rustup update
```

Check that `rusqlite` feature flags in `Cargo.toml` include `bundled`:
```toml
rusqlite = { version = "...", features = ["bundled"] }
```

---

## Adding a new module

1. Create `src/components/modules/{name}/` with component files
2. Add hooks to `src/hooks/use{Name}.ts`
3. Add Tauri commands to `src-tauri/src/commands/{name}.rs`
4. Register commands in `src-tauri/src/lib.rs`
5. Add route to `src/App.tsx`
6. Add module entry (and icon) to `src/modules/registry.ts` and `Sidebar.tsx`
7. Add TypeScript interfaces to `src/hooks/types.ts`, export from `index.ts`

Follow the pattern established in `commands/harness.rs` and
`components/modules/harness/RunList.tsx`.
