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
│  │  Sidebar (registry.ts)                            │   │
│  │  ├── Harness          ← p1/p2/p4/p5/p6           │   │
│  │  │   ├── Runs         ← run list + events         │   │
│  │  │   ├── Diff         ← p4: two-run comparison    │   │
│  │  │   ├── Agents       ← p5: capability matrix     │   │
│  │  │   └── Usage        ← p6: token/cost stats      │   │
│  │  ├── Orchestrator     ← p3: NL → plan → execute   │   │
│  │  ├── Tools            ← p4-tools: scripts + MCP   │   │
│  │  ├── F2               ← existing                  │   │
│  │  └── Provenance       ← existing corpus dashboard  │   │
│  │  (Settings at /settings — shell only, no sidebar) │   │
│  │                                                   │   │
│  │  Hooks (20 files)                                 │   │
│  │  ├── useHarness.ts        ← runs + events         │   │
│  │  ├── useTrajectory.ts     ← p4: single run load   │   │
│  │  ├── useRunDiff.ts        ← p4: two-run diff      │   │
│  │  ├── useOrchestrator.ts   ← p3: state machine     │   │
│  │  ├── useCapabilityMatrix.ts← p5: matrix load      │   │
│  │  ├── useUsageStats.ts     ← p6: cost aggregates   │   │
│  │  ├── useAgentConfig.ts    ← p7: env var config    │   │
│  │  ├── useTools.ts          ← p4-tools: inventory   │   │
│  │  ├── useRequestHistory.ts ← p3: MRU list          │   │
│  │  └── (+ 11 F2/Provenance hooks)                   │   │
│  └──────────────────────────────────────────────────┘   │
│                          │ invoke()                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │               Tauri Rust Backend                  │   │
│  │                                                   │   │
│  │  commands/harness.rs        ← SQLite reads (4)    │   │
│  │  commands/trajectory.rs     ← JSON file reads (2) │   │
│  │  commands/orchestrate.rs    ← child process (4)   │   │
│  │  commands/agent_config.rs   ← config store (5)    │   │
│  │  commands/capability_matrix.rs ← matrix parse (1) │   │
│  │  commands/usage.rs          ← cost aggregates (1) │   │
│  │  commands/tools.rs          ← scripts + MCP (5)   │   │
│  │  commands/provenance.rs     ← DuckDB reads + write│   │
│  │                                                   │   │
│  │  HarnessState      { conn: Option<SqliteConn> }   │   │
│  │  CorpusState       { conn: Option<DuckdbConn> }   │   │
│  │  OrchestratorState { jobs:        Mutex<HashMap>, │   │
│  │                      agents_path: Option<String>, │   │
│  │                      aetheris_dir: Option<String>}│   │
│  │  AgentConfigState  { store_path, cache: Mutex<…> }│   │
│  │  ToolsState        { agents_path: Option<String> }│   │
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
orchestrate.rs spawns: mix run agents/orchestrator.exs
  (LLM-driven; agents/mock_orchestrator.exs kept for regression only)
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
        lib.rs                ← 6 state structs + 42 command registrations
        commands/
          mod.rs
          f2.rs
          harness.rs          ← 4 read-only SQLite commands
          trajectory.rs       ← p4: trajectory_load + trajectory_export
          orchestrate.rs      ← p3: 4 process management commands
          agent_config.rs     ← p7: 5 config commands (get/set/del/export/import)
          capability_matrix.rs← p5: 1 command — parses capability-matrix.md
          usage.rs            ← p6: 1 command — aggregates cost/tokens from events
          tools.rs            ← p4-tools: 5 commands (list/read/run + MCP)
          provenance.rs
    src/
      App.tsx                 ← 11 routes: /harness /diff /capability-matrix /usage
                              ←   /orchestrator /tools /f2/* /provenance /settings
      hooks/
        types.ts              ← all TypeScript interfaces (52+ exports)
        index.ts              ← re-exports
        useHarness.ts
        useTrajectory.ts      ← p4: single-run trajectory load
        useRunDiff.ts         ← p4: two-run diff computation
        useOrchestrator.ts    ← p3: full state machine
        useCapabilityMatrix.ts← p5: matrix load
        useUsageStats.ts      ← p6: cost/token aggregates
        useAgentConfig.ts     ← p7: env var config CRUD
        useTools.ts           ← p4-tools: inventory + MCP
        useRequestHistory.ts  ← p3: localStorage MRU list
        useCorpusOverview.ts
        useClassifications.ts
        useMigration.ts
        useZipInventory.ts
        useProvenanceStatus.ts
        useFileIndex.ts
        useDuplicates.ts
        useWatchedFolders.ts
        useSessionRecord.ts
      components/
        shell/
          MainArea.tsx        ← controlled/uncontrolled tabs
          Sidebar.tsx         ← iconMap: Activity, GitCompare, Sparkles, …
        ui/
        modules/
          harness/
            RunList.tsx          ← HarnessRoute: Runs + Events + Trajectory tabs
            TrajectoryView.tsx   ← p4: meta panel + step-grouped event stream
            DiffView.tsx         ← p4: run selection + diff tables
            CapabilityMatrixView.tsx ← p5: collapsible agent/script matrix
            UsageView.tsx        ← p6: cost summary + by-model/use-case tables
          orchestrator/
            OrchestratorView.tsx ← p3: all 7 phases
          tools/
            ToolsView.tsx        ← p4-tools: wrapper
            ToolTree.tsx         ← left-panel tree (scripts + MCP)
            ToolDetail.tsx       ← right panel (args form + Run button)
          settings/
            AgentConfigTab.tsx   ← p7: grouped env var config
            agentConfigDefs.ts   ← key definitions (Harness/Anthropic/SMTP/Drive/Payslip/GitHub)
          f2/
          provenance/
      modules/
        registry.ts           ← 5 modules: harness (4 sections) + orchestrator
                              ←   + tools + f2 + provenance
  agents/
    orchestrator.exs          ← p3: LLM-driven orchestrator (real agent, Anthropic API)
    mock_orchestrator.exs     ← p3: deterministic mock kept for regression testing
  docs/
    rig/
      README.md
      specs.md
      architecture.md
      runbook.md
      current-state-2026-06.md ← code-verified reality check (authoritative)
      milestones/
        p1/ p2/ p3/ p4/ p4-tools/ p5/ p6/ p7/ p8/ orchestrator/
```

---

## Trust Boundary

| Component | Reads | Writes |
|-----------|-------|--------|
| Harness commands | `aetheris.db` | Never |
| Trajectory commands | `priv/runs/*/trajectory.json` | Never (export = copy to user path) |
| Provenance commands | `corpus.duckdb` | `set_classification_status` only |
| Orchestrate commands | — | stdin of child process; spawns `orchestrator.exs` |
| Agent config commands | `~/.local/share/dev.rig.app/agent-config.json` | `agent_config_set/delete/import` |
| Capability matrix commands | `docs/capability-matrix.md` | Never |
| Usage commands | `aetheris.db` (events table) | Never |
| Tools commands | scripts under `AETHERIS_AGENTS_PATH`; MCP servers via stdio | **Executes arbitrary local code** (`tools_run_script`, `tools_call_mcp`) |
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

**`/settings` is not in the sidebar registry.** `App.tsx` has a `/settings`
route rendering `SettingsRoute` (which hosts `AgentConfigTab`), but `registry.ts`
has no entry for it. The settings page is reachable by navigating directly —
it does not appear in the sidebar. This is intentional: config is a support
operation, not a primary workflow.

**`trajectory.rs` re-reads `AETHERIS_DB_PATH` from env instead of using
`HarnessState`.** The command signature receives `_state: State<HarnessState>`
but ignores it, deriving the trajectory path from the env var directly
(`std::env::var("AETHERIS_DB_PATH")`). This mirrors what `lib.rs` does at
startup — same var, same derivation — so there is no divergence in practice.
The reason is that `trajectory.rs` needs the file path, not the open SQLite
connection stored in `HarnessState`, and reading the env var is simpler than
adding a separate field to the state struct.
