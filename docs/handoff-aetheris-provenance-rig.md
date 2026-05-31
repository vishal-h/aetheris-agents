# Handoff — Aetheris + Provenance + Rig

**Session date:** 2026-05-31
**Prepared for:** next Claude session

---

## Repo locations

| Repo | Path | Purpose |
|------|------|---------|
| `aetheris` | `~/sandbox/elixirws/aetheris/` | Harness (Elixir + Rust) |
| `aetheris-agents` | `~/sandbox/elixirws/aetheris-agents/` | Agents, scripts, Rig UI, docs |
| `hai-rig` | `~/workspaces/hai/hai-rig/` | Old standalone Tauri repo (retired — do not touch) |
| test sandbox | `~/sandbox/provenance-test/` | Local corpus for pipeline validation |

---

## What is complete

### Provenance — all 6 milestones done

| Milestone | What it does |
|-----------|-------------|
| m1 | Inventory — scan NAS, populate f2_file_index, generate report |
| m2 | Classification — taxonomy session, classify batches, review cycle |
| m3 | Migration — copy approved files to /clients/, SHA-256 verify, rollback |
| m4 | Zip archaeology — extract zips, find new-to-corpus, handle encrypted |
| m5 | Corpus MCP + search — corpus-search MCP server, search_agent, validation |
| m6 | Tauri dashboard — corpus overview, classification review, migration + zip status |

### Rig — Phase 1 + Phase 2 complete ✅

| Phase | Issues | Status |
|-------|--------|--------|
| p1 | p1-001 Consolidation, p1-002 Harness DB commands, p1-003 Run list UI | ✅ All done |
| p2 | p2-001 Polling hook, p2-002 Live events UI | ✅ All done |

**What p1 delivered:**
- `aetheris-agents/rig/` — full Tauri app (moved from hai-rig)
- `HarnessState` + 4 read-only SQLite commands for `aetheris.db`
- Harness module in sidebar: Runs tab (table + status filter) and Events tab (event log)
- Controlled/uncontrolled `MainArea` — supports cross-tab shared state

**What p2 delivered:**
- `useRunEvents` polls every 2s when `{ polling: true }` — stops automatically on `run_complete`
- Events tab auto-scrolls to bottom as new events arrive (smart: respects user scroll position)
- Pulsing "Live" indicator in the Events header while polling
- Status badge updates locally to 'done' when `run_complete` detected — no extra network call

### Infrastructure — done

- Model parameterisation: all agent files use `PROVENANCE_MODEL` →
  `AETHERIS_MODEL` → hardcoded fallback. Configured via `aetheris-agents/.env`
- Capability matrix: generated and committed at `docs/capability-matrix.md`
- Runbook: `docs/provenance/runbook.md` — complete including "Before going live"
  checklist and model configuration section
- Test sandbox: `provenance/scripts/create_test_sandbox.py` — creates 26 files,
  5 zips, 4 duplicate groups, 1 encrypted zip, depth-3 nesting

---

## What is in progress

Nothing active. Two threads ready to start:

### Thread 1 — Rig p3 (Orchestrator)

Natural language request → plan → confirm → execute agents. Spec in
`docs/rig/milestones/p3/`. **Not yet written** — needs milestone + issue docs
written in Claude.ai before any Claude Code work.

**Goal:** user types "email payslips for May 2026", orchestrator reads
capability matrix, reasons about agents needed, writes a plan to a temp file,
blocks on confirmation, executes on approval, shows live run progress.

### Thread 2 — uc-provenance-validation

Full pipeline validation against the test sandbox. In `ROADMAP.md` under
Planned. Steps in order:

1. Taxonomy session (`taxonomy_session.py` interactively)
2. Classification orchestrator against sandbox
3. Export → review → import cycle
4. Migration agent against sandbox
5. Zip archaeology against sandbox
6. Search validation (`validate_search.py`, pass rate ≥ 85%)
7. Eval sprint (`./scripts/sprint.sh eval`)

**Blocked on:** `ANTHROPIC_API_KEY` available in shell.

---

## What comes next (Rig roadmap)

| Phase | Goal | Status |
|-------|------|--------|
| p1 | Consolidation + run list UI | ✅ Complete |
| p2 | Live monitoring — watch active runs in real time | ✅ Complete |
| p3 | Orchestrator — NL request → plan → confirm → execute agents | ⬜ Needs milestone docs |
| p4 | Trajectory explorer — full event detail, search, export | ⬜ |

Phase docs live at `aetheris-agents/docs/rig/milestones/`.

---

## Key files to know

```
aetheris-agents/
  .env                              ← model defaults (AETHERIS_MODEL etc.)
  docs/
    capability-matrix.md            ← auto-generated, all agents + scripts
    rig/
      README.md                     ← Rig project overview
      specs.md                      ← data model, command shapes, TS types
      architecture.md               ← component map, data flow
      runbook.md                    ← dev setup, env vars, common issues
      milestones/
        p1/                         ← p1-001, p1-002, p1-003 (all done)
        p2/                         ← p2-001, p2-002 (all done)
    provenance/
      runbook.md                    ← full Provenance operator guide
  rig/                              ← Tauri app
    CLAUDE.md                       ← authoritative context for Claude Code
    src-tauri/src/
      lib.rs                        ← HarnessState + CorpusState setup
      commands/
        harness.rs                  ← 4 read-only SQLite commands
        provenance.rs               ← Provenance DuckDB commands
        f2.rs                       ← F2 file index commands
    src/
      App.tsx                       ← routes: /harness, /f2/*, /provenance, /settings
      components/
        shell/
          MainArea.tsx              ← controlled/uncontrolled tabs (see patterns)
        modules/
          harness/
            RunList.tsx             ← HarnessRoute, RunsContent, EventsContent (live)
            shared.tsx              ← NotConnected, LoadingShell
          provenance/               ← all 4 Provenance views + shared.tsx
          f2/                       ← F2Operations, F2Viewer, WatchedFolders
      hooks/
        useHarness.ts               ← useHarnessStatus, useRunList,
                                       useRunEvents (polling), useRunDetail
        types.ts                    ← all TypeScript interfaces

aetheris/
  priv/aetheris.db                  ← harness SQLite (runs, events, orbs, skills)
  priv/runs/                        ← trajectory JSON files per run
```

---

## Patterns established

### Rust / Tauri

**`harness_connection_status` returns `Ok`, not `Err`.**
Unlike all other harness commands (which return `Err("harness not connected")`
when `AETHERIS_DB_PATH` is absent), `harness_connection_status` returns
`Ok(HarnessStatus { connected: false, error: Some(...) })`. Check
`data.connected`, not the Result variant. Documented in `rig/CLAUDE.md`.

**`get_harness_conn` helper mirrors `get_corpus_conn`.**
Both take `state: &'a State<'a, *State>` and return a `MutexGuard`. This is
the correct pattern for all Tauri command handlers that need DB access.

### React / Frontend

**Controlled/uncontrolled `MainArea`.**
`MainArea` accepts optional `activeTab`/`onTabChange` props. Without them it
manages tab state internally (all existing routes). With them, the parent owns
the active tab (Harness route). Use controlled mode whenever a route needs
cross-tab shared state.

**`HarnessRoute` pattern for cross-tab shared state.**
When a route needs state shared between tabs, create a `*Route` component that
owns the shared state, wraps `MainArea` with `activeTab`/`onTabChange`, and
passes data down via props. Do not try to share state inside `Tab[]` factory
functions.

**Three-effect polling pattern.**
When a hook needs to poll and self-terminate, use three separate effects:
1. Sync internal `activelyPolling` state with caller's `polling` option
2. Watch fetched data for a stop signal (e.g. `run_complete` event); set
   `activelyPolling(false)` when found
3. Set up / tear down the `setInterval` based on `activelyPolling`

This separates concerns cleanly and allows the hook to self-terminate
independently of the caller.

**`loading && !data` for polling-safe skeletons.**
When a hook does background polling, `loading` is true on every refetch.
Using `loading` alone to show a skeleton flashes the UI every 2s. Use
`loading && !data` to show the skeleton only on the initial load, then
leave existing content in place during background refreshes. Applied in
`EventsContent` and should be used anywhere a polling hook drives a list.

**`useInvoke` args are not in `useCallback` deps (intentional).**
The shared `useInvoke` helper only lists `command` in deps, not `args`.
This means dynamic args won't trigger a refetch. For dynamic args, use an
explicit `useCallback` with the arg in deps — see `useRunEvents` and
`useRunDetail` for the right pattern.

### Older patterns (still valid)

**Agent model config (two-level fallback):**
```elixir
model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"
```

**`Application.ensure_all_started/1` returns `{:ok, []}` not `:ok`.**
Match as `{:ok, _} = Application.ensure_all_started(:aetheris)` in `.exs` scripts.

---

## Quick commands

```bash
# Open Rig
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb  # optional
cargo tauri dev

# Run any Provenance agent
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs

# Check a run
mix aetheris inspect <run_id>
mix aetheris list --limit 5

# Reset test sandbox
python3 provenance/scripts/create_test_sandbox.py --overwrite

# Regenerate capability matrix
./scripts/sprint.sh capability_matrix

# TypeScript build check (frontend only, no Tauri env needed)
cd ~/sandbox/elixirws/aetheris-agents/rig
bun run build
```
