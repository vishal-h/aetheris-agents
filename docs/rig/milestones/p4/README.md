# Phase 4 — Trajectory Explorer

**Status: IMPLEMENTED**

**Goal:** Surface the trajectory as a first-class artefact. Inspect any run's
full event stream with complete payload detail. Compare two runs side by side
to understand how model choice, prompt changes, or reruns affect agent
behaviour.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Trajectory viewer](p4-001-trajectory-viewer.md) | — | Rust command + third Harness tab: meta panel, step-grouped events, full payload expansion, JSON export |
| 002 | [Run diff](p4-002-run-diff.md) | 001 (shares Rust command + TS types) | Select two runs, compare metadata + step path side by side |

001 must land first — it introduces `trajectory_load`, `TrajectoryFile`, and
`TrajectoryEvent` which 002 depends on. Once 001 is merged, 002 can proceed.

---

## Completion gate

- Trajectory tab appears in Harness module (disabled until a run is selected)
- Clicking a run and switching to Trajectory shows the meta panel and full
  event stream grouped by step
- Each event's payload is collapsed by default; clicking expands the full
  pretty-printed JSON
- Export button copies the trajectory JSON file to a user-chosen path
- Diff section appears in the Harness sidebar entry
- Navigating to `/diff`, selecting two runs, and clicking Compare renders the
  metadata comparison table and step path side by side
- Fields that differ between runs are highlighted
- All existing modules (Harness runs/events, Orchestrator, Provenance, F2)
  unaffected
- `cargo build` exits 0, zero warnings
- `bun run build` exits 0, zero TypeScript errors

---

## Key decisions

**Data source: trajectory JSON files, not SQLite.**
`priv/runs/{run_id}/trajectory.json` is self-contained: events + meta in one
atomic snapshot. The `meta` block (system_prompt, user_prompt, tools, mode,
seed, overlay_changes) is not in SQLite. Reading the JSON avoids joins and
gives richer data. The runs directory is derived from `AETHERIS_DB_PATH`
(parent-of-parent) — no new env var needed.

**`payload` as parsed JSON, not a raw string.**
`TrajectoryEvent.payload` is `serde_json::Value` in Rust, `Record<string,
unknown>` in TypeScript. The trajectory file already has structured payloads —
no double-stringification. This differs from `EventRow.payload` (raw string)
used in the existing harness commands.

**Trajectory viewer as a third Harness tab.**
Trajectory is contextual to a selected run, the same way Events is. It fits
naturally as a third tab in `HarnessRoute` rather than a new route. Events
and Trajectory tabs are disabled until a run is selected.

**Diff as a second sidebar section under Harness.**
Diff needs two run selections — it doesn't fit the single-run tab model.
A separate `/diff` route with its own sidebar entry under `harnessModule`
keeps it discoverable without adding a top-level module.

**Export = file copy, not re-serialisation.**
The trajectory JSON is written atomically by the harness at run completion.
Copying the file byte-for-byte guarantees fidelity. A new Tauri command
`trajectory_export` opens a save dialog and copies the file.

**Metadata diff only for p4.**
Event-level structural diff (aligning sequences across runs) is deferred.
The metadata + step path comparison answers the primary use case: "how did
this agent perform with a different model?"

See individual issue docs for full implementation detail.
