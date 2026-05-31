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
│  │  ├── F2 (existing)                                │   │
│  │  ├── Harness          ← p1: run inspection        │   │
│  │  ├── Orchestrator     ← p3: NL → plan → execute   │   │
│  │  └── Provenance       ← existing corpus dashboard  │   │
│  │                                                   │   │
│  │  Hooks                                            │   │
│  │  ├── useHarness.ts    ← invoke harness commands   │   │
│  │  ├── useCorpusOverview.ts (existing)              │   │
│  │  └── useClassifications.ts (existing)             │   │
│  └──────────────────────────────────────────────────┘   │
│                          │ invoke()                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │               Tauri Rust Backend                  │   │
│  │                                                   │   │
│  │  commands/harness.rs    ← SQLite reads            │   │
│  │  commands/provenance.rs ← DuckDB reads + 1 write  │   │
│  │  commands/orchestrate.rs← shells out to mix       │   │
│  │                                                   │   │
│  │  HarnessState { conn: Option<SqliteConn> }        │   │
│  │  CorpusState  { conn: Option<DuckdbConn> }        │   │
│  └──────────────────────────────────────────────────┘   │
│            │                        │                    │
│    rusqlite (SQLite)         duckdb-rs (DuckDB)          │
└────────────┼────────────────────────┼────────────────────┘
             │                        │
    aetheris/priv/            corpus.duckdb
      aetheris.db             (Provenance)
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
Rig starts orchestrator.exs via invoke("orchestrate", { request })
  ↓
orchestrator.exs:
  read_file("docs/capability-matrix.md")
  → reasons about agents needed
  → writes plan to temp file
  → ask_human("Confirm plan?")  ← blocks here
  ↓
Rig polls plan temp file → shows plan in UI
User approves → Rig writes approval → orchestrator continues
  ↓
orchestrator.exs executes each agent via run_command
  ↓
Rig shows live event log per agent (Phase 2 monitoring)
```

---

## Repository Layout

```
aetheris-agents/
  rig/                        ← Tauri app (moved from hai-rig)
    CLAUDE.md                 ← updated for new location + harness DB
    src-tauri/
      Cargo.toml
      src/
        lib.rs                ← HarnessState + CorpusState setup
        commands/
          mod.rs
          f2.rs               ← existing
          harness.rs          ← new p1
          provenance.rs       ← existing
          orchestrate.rs      ← new p3
    src/
      App.tsx
      hooks/
        types.ts              ← shared TypeScript interfaces
        useHarness.ts         ← new p1
        useCorpusOverview.ts  ← existing
        useClassifications.ts ← existing
        useMigration.ts       ← existing
        useZipInventory.ts    ← existing
        useProvenanceStatus.ts← existing
      components/
        shell/
        ui/
        modules/
          f2/                 ← existing
          harness/            ← new p1
          orchestrator/       ← new p3
          provenance/         ← existing
      modules/
        registry.ts           ← add Harness module p1, Orchestrator p3
  docs/
    rig/
      README.md
      specs.md
      architecture.md
      runbook.md
      milestones/
        p1/
          README.md
          p1-001-consolidation.md
          p1-002-harness-commands.md
          p1-003-run-list-ui.md
        p2/ ...
        p3/ ...
```

---

## Trust Boundary

| Component | Reads | Writes |
|-----------|-------|--------|
| Harness commands | `aetheris.db` | Never |
| Provenance commands | `corpus.duckdb` | `set_classification_status` only |
| Orchestrate commands | filesystem (temp files) | plan temp file |
| Frontend | — | Never touches DB directly |

---

## Key Design Decisions

**SQLite via rusqlite, not DuckDB.** `aetheris.db` is SQLite (the harness uses
Exqlite). Rig uses `rusqlite` for harness commands — a separate crate from
`duckdb-rs` already used for Provenance. Both connections live in app state.

**Read-only harness connection.** `HarnessState.conn` opens `aetheris.db`
with `OpenFlags::SQLITE_OPEN_READ_ONLY`. The harness owns this database;
Rig never writes to it.

**No new harness API.** All run and trajectory data is available in
`aetheris.db` and `priv/runs/{run_id}/trajectory.json`. Rig reads these
directly — no changes to the harness code needed.

**Polling, not websockets.** Live monitoring uses 2-second interval polling
via `useEffect` + `setTimeout`. Simple, reliable, sufficient for the
event volumes involved. Revisit if latency becomes an issue.

**Orchestrator confirmation via temp file.** The orchestrator agent writes
its plan to a UUID temp file and blocks on `ask_human`. Rig polls the
temp file path and surfaces the plan in the UI. User approval writes a
response file. This avoids any new IPC mechanism — the filesystem is the
message bus. Revisit for p3 when the full design is finalised.
