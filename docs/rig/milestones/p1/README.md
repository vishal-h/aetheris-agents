# Phase 1 — Consolidation + Run Inspection

**Goal:** Tauri app lives in `aetheris-agents/rig/`, and you can browse all
past agent runs and their event trajectories without touching a terminal.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Repo consolidation](p1-001-consolidation.md) | — | Move hai-rig to aetheris-agents/rig/, update CLAUDE.md and paths |
| 002 | [Harness DB commands](p1-002-harness-commands.md) | 001 | SQLite reader: harness_list_runs, harness_get_events, harness_get_run |
| 003 | [Run list UI](p1-003-run-list-ui.md) | 002 | Harness module: run list tab + event log tab |

**001** first — it establishes the location. **002** and **003** follow in order.

---

## Completion gate

- `cargo tauri dev` starts cleanly from `aetheris-agents/rig/`
- Harness tab shows all past agent runs from `aetheris.db`
- Clicking a run shows its event log
- "Not connected" placeholder renders when `AETHERIS_DB_PATH` is absent
- Provenance module continues to work as before (no regression)

---

## Key decisions

**`rusqlite` for SQLite, not DuckDB.** `aetheris.db` is SQLite. Rig uses
`rusqlite` (with `bundled` feature) for harness commands alongside the
existing `duckdb-rs` for Provenance. Both connections live in separate
Tauri state structs.

**Read-only harness connection.** `HarnessState.conn` opens `aetheris.db`
with `SQLITE_OPEN_READ_ONLY` flag. The harness owns this database.

**Payload as raw JSON string.** Event payloads vary by type and can be
large. Rig passes `payload_json` as a raw string to the frontend, which
parses and renders it per event type. This avoids a combinatorial Rust
struct for every event type.

**No harness changes.** All data Rig needs is already in `aetheris.db`.
No new APIs, no changes to the harness codebase.
