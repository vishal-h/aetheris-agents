# Rig — Runbook

---

## Environment variables

| Variable | Required | Description |
|----------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | Absolute path to `aetheris/priv/aetheris.db` |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | Absolute path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | Set `true` to enable corpus-search MCP |

---

## Development

```bash
cd aetheris-agents/rig

# Set env vars
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb

# Start dev server
cargo tauri dev
```

Both `AETHERIS_DB_PATH` and `PROVENANCE_DB_PATH` are optional at startup —
Rig renders "not connected" placeholders for features that require them.

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
cargo tauri dev
```

---

## Harness module — Run inspection

The Harness module shows all agent runs recorded in `aetheris.db`.

### What you see

**Run list tab:**
- Label, status badge, model, started at, duration, steps
- Click any row to open the event log for that run
- Refresh button — no auto-refresh

**Event log tab:**
- All events for the selected run, ordered by seq
- Step number, event type, timestamp, payload preview
- Colour coding by event type

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
tab shows a "Not connected" placeholder with the path to set.

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

**Fix:** Set `AETHERIS_DB_PATH` to the absolute path of `aetheris.db` and
restart:
```bash
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
```

### Run list is empty

`aetheris.db` exists but has no runs — no agents have been run yet.
Run any agent via `mix aetheris run` and refresh.

### Events table shows no events for a run

The run was recorded but the harness may have crashed before persisting
events. Check `mix aetheris inspect <run_id>` for details.

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

1. Create `src/components/modules/{name}/` with a tab factory function
2. Add hooks to `src/hooks/use{Name}.ts`
3. Add Tauri commands to `src-tauri/src/commands/{name}.rs`
4. Register commands in `src-tauri/src/lib.rs`
5. Add route to `src/App.tsx`
6. Add module entry to `src/modules/registry.ts`
7. Add TypeScript interfaces to `src/hooks/types.ts`

Follow the pattern established in `commands/harness.rs` and
`components/modules/harness/RunList.tsx`.
