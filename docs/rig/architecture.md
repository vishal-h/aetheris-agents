# Rig — Architecture

---

## Component Map

```
┌─────────────────────────────────────────────────────────┐
│                    Rig (Tauri App)                       │
│                 aetheris-agents/rig/                     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  React Frontend                   │   │
│  │                                                   │   │
│  │  Sidebar                                          │   │
│  │  ├── Harness          ← p1/p2/p4                  │   │
│  │  │   ├── Runs         ← run list + events         │   │
│  │  │   └── Diff         ← p4: two-run comparison    │   │
│  │  ├── Orchestrator     ← p3: NL → plan → execute   │   │
│  │  ├── F2               ← existing                  │   │
│  │  └── Provenance       ← existing corpus dashboard  │   │
│  │                                                   │   │
│  │  Hooks                                            │   │
│  │  ├── useHarness.ts        ← runs + events         │   │
│  │  ├── useTrajectory.ts     ← p4: single run load   │   │
│  │  ├── useRunDiff.ts        ← p4: two-run diff      │   │
│  │  ├── useOrchestrator.ts   ← p3: state machine     │   │
│  │  ├── useCorpusOverview.ts ← existing              │   │
│  │  └── useClassifications.ts← existing              │   │
│  └──────────────────────────────────────────────────┘   │
│                          │ invoke()                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │               Tauri Rust Backend                  │   │
│  │                                                   │   │
│  │  commands/harness.rs      ← SQLite reads          │   │
│  │  commands/trajectory.rs   ← p4: JSON file reads   │   │
│  │  commands/orchestrate.rs  ← p3: child process     │   │
│  │  commands/provenance.rs   ← DuckDB reads + write  │   │
│  │                                                   │   │
│  │  HarnessState      { conn: Option<SqliteConn> }   │   │
│  │  CorpusState       { conn: Option<DuckdbConn> }   │   │
│  │  OrchestratorState { jobs: Mutex<HashMap<…>> }    │   │
│  └──────────────────────────────────────────────────┘   │
│       │                   │               │              │
│  rusqlite (SQLite)   duckdb-rs        filesystem         │
│                      (DuckDB)         (JSON files)       │
└───────┼───────────────────┼───────────────┼──────────────┘
        │                   │               │
  aetheris/priv/      corpus.duckdb   priv/runs/*/
    aetheris.db        (Provenance)  trajectory.json
  (harness state)
```

---

## Data Flow — Run Inspection (p1)

```
User opens Harness tab
  ↓
useHarness.ts → invoke("harness_list_runs")
  ↓
harness.rs → SELECT * FROM runs ORDER BY started_at DESC LIMIT 50
  ↓
RunList.tsx renders table (label, status, model, started, duration, steps)

User clicks a run
  ↓
invoke("harness_get_events", { run_id })
  ↓
SELECT * FROM events WHERE run_id = ? ORDER BY seq ASC
  ↓
EventLog.tsx renders event rows (seq, step, type, payload preview)
```

---

## Data Flow — Live Monitoring (p2)

```
Run status = "running"
  ↓
useHarness polls harness_get_events every 2s
  ↓
New events append to EventLog in real time
  ↓
Auto-scroll to latest event
  ↓
When status = "done" | "failed": stop polling
```

---

## Data Flow — Orchestrator (p3)

```
User types: "email payslips to all employees for May 2026"
  ↓
invoke("orchestrate_start", { request })
  ↓
orchestrate.rs spawns: mix run agents/mock_orchestrator.exs
  with ORCHESTRATOR_REQUEST env var, stdin/stdout pipes
  ↓
Reader thread pushes newline-delimited JSON to Arc<Mutex<Vec>> buffer
  ↓
Frontend polls orchestrate_poll every 1s → drains buffer
  ↓
{ type: "plan", steps: [...] } → OrchestratorView shows plan, waits for user
  ↓
User approves → invoke("orchestrate_approve", { approved: true })
  ↓
orchestrate_approve writes {"type":"approval","approved":true} to stdin
  ↓
Script emits step_started / step_complete for each step
  ↓
orchestration_complete → phase = "done"
```

---

## Data Flow — Trajectory viewer (p4)

```
User selects a run in RunList, switches to Trajectory tab
  ↓
useTrajectory(runId) → invoke("trajectory_load", { run_id })
  ↓
trajectory.rs reads priv/runs/{run_id}/trajectory.json
  (path derived: AETHERIS_DB_PATH → parent → parent → priv/runs/…)
  ↓
Returns TrajectoryFile { meta, events[] } with parsed payload objects
  ↓
TrajectoryView renders:
  - Meta panel (model, provider, mode, steps, duration, tools,
    system_prompt, user_prompt) — collapsible
  - Events grouped by step, each step collapsible
  - Each event: seq badge + type badge + timestamp + expandable payload JSON

User clicks Export JSON
  ↓
invoke("trajectory_export", { run_id })
  ↓
trajectory_export opens save dialog → copies trajectory.json to chosen path
```

---

## Data Flow — Run diff (p4)

```
User navigates to /diff (Diff section under Harness in sidebar)
  ↓
DiffView renders run picker: two dropdowns from harness_list_runs
  ↓
User selects Run A and Run B, clicks Compare
  ↓
useRunDiff(runIdA, runIdB) → Promise.all([
  invoke("trajectory_load", { run_id: runIdA }),
  invoke("trajectory_load", { run_id: runIdB }),
])
  ↓
computeDiff(a, b):
  - meta_rows: model, provider, mode, step_count, max_steps,
               total_latency, terminal_reason, tools
  - step_rows: per-step tool lists (from tool_called events),
               gaps where one run has no matching step
  - differs flag per row
  ↓
DiffView renders:
  - Metadata table (3 cols: field | Run A | Run B)
    highlighted rows where A ≠ B
  - Step path table (3 cols: step | Run A tools | Run B tools)
    gaps shown as — for absent steps
```

---

## Repository Layout

```
aetheris-agents/
  rig/                        ← Tauri app
    CLAUDE.md                 ← authoritative context for Claude Code
    src-tauri/
      Cargo.toml
      src/
        lib.rs                ← HarnessState + CorpusState + OrchestratorState
        commands/
          mod.rs
          f2.rs
          harness.rs          ← 4 read-only SQLite commands
          trajectory.rs       ← p4: trajectory_load + trajectory_export
          orchestrate.rs      ← p3: 4 process management commands
          provenance.rs
    src/
      App.tsx                 ← routes: /harness, /diff, /orchestrator, /f2/*, /provenance
      hooks/
        types.ts              ← all TypeScript interfaces
        index.ts              ← re-exports
        useHarness.ts
        useTrajectory.ts      ← p4: single-run trajectory load
        useRunDiff.ts         ← p4: two-run diff computation
        useOrchestrator.ts    ← p3
        useCorpusOverview.ts
        useClassifications.ts
        useMigration.ts
        useZipInventory.ts
        useProvenanceStatus.ts
      components/
        shell/
          MainArea.tsx        ← controlled/uncontrolled tabs
          Sidebar.tsx         ← iconMap: Activity, GitCompare, Sparkles, …
        ui/
        modules/
          harness/
            RunList.tsx       ← HarnessRoute: Runs + Events + Trajectory tabs
            TrajectoryView.tsx← p4: meta panel + step-grouped event stream
            DiffView.tsx      ← p4: run selection + diff tables
          orchestrator/
            OrchestratorView.tsx ← p3
          f2/
          provenance/
      modules/
        registry.ts           ← harnessModule (2 sections) + orchestratorModule + …
  agents/
    mock_orchestrator.exs     ← p3: deterministic mock for orchestrator pipeline
  docs/
    rig/
      README.md
      specs.md
      architecture.md
      runbook.md
      milestones/
        p1/ p2/ p3/ p4/
```

---

## Trust Boundary

| Component | Reads | Writes |
|-----------|-------|--------|
| Harness commands | `aetheris.db` | Never |
| Trajectory commands | `priv/runs/*/trajectory.json` | Never (export = copy to user path) |
| Provenance commands | `corpus.duckdb` | `set_classification_status` only |
| Orchestrate commands | — | stdin of child process |
| Frontend | — | Never touches DB or files directly |

---

## Key Design Decisions

**SQLite via rusqlite, not DuckDB.** `aetheris.db` is SQLite (the harness uses
Exqlite). Rig uses `rusqlite` for harness commands — a separate crate from
`duckdb-rs` already used for Provenance. Both connections live in app state.

**Read-only harness connection.** `HarnessState.conn` opens `aetheris.db`
with `OpenFlags::SQLITE_OPEN_READ_ONLY`. The harness owns this database;
Rig never writes to it.

**Trajectory JSON as the p4 data source, not SQLite.** The `meta` block
(system_prompt, user_prompt, tools, mode, seed, overlay_changes) is only
in the trajectory file, not in SQLite. Reading the JSON avoids joins and
gives the complete picture. The file is written atomically at run completion
and is immutable thereafter — safe for concurrent reads.

**`payload` type divergence.** `EventRow.payload` (harness.rs) is a raw JSON
string — the harness stores it that way in SQLite. `TrajectoryEvent.payload`
(trajectory.rs) is a parsed `serde_json::Value` — the trajectory file has
structured payloads. Do not conflate these types.

**Trajectory tab in HarnessRoute, Diff as a second sidebar section.**
Trajectory is contextual to a single selected run — a third tab fits
naturally. Diff requires two run selections and doesn't fit the tab model;
it lives at `/diff` as a separate route with its own sidebar entry.

**Diff = metadata + step path only (p4).** Event-level structural diff
(aligning payload sequences across runs) is deferred. The metadata +
tool-path comparison answers the primary use case: comparing agent behaviour
across model or prompt changes.

**Export = file copy, not re-serialisation.** `trajectory_export` copies
the existing JSON file byte-for-byte. This guarantees fidelity with what
the harness wrote and avoids any serialisation differences.

**No new harness API.** All run and trajectory data is available in
`aetheris.db` and `priv/runs/{run_id}/trajectory.json`. Rig reads these
directly — no changes to the harness code needed.

**Polling, not websockets.** Live monitoring uses 2-second interval polling
via `useEffect` + `setInterval`. Trajectory viewer does not poll — files
are immutable post-run.
