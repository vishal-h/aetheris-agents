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

### Rig — Phase 1 complete ✅

All three p1 issues done and pushed.

| Issue | Status |
|-------|--------|
| p1-001 Consolidation | ✅ hai-rig copied to aetheris-agents/rig/, rusqlite added, CLAUDE.md updated |
| p1-002 Harness DB commands | ✅ HarnessState, 4 Tauri commands, TypeScript types, useHarness.ts hooks |
| p1-003 Run list UI | ✅ Harness module in sidebar, RunList tabs, controlled MainArea, HarnessRoute |

**P1 completion gate — all met:**
- Harness tab shows all past agent runs from `aetheris.db`
- Clicking a run shows its event log
- "Not connected" placeholder when `AETHERIS_DB_PATH` absent
- Provenance module unaffected

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

### Thread 1 — Rig p2 (Live monitoring)

Watch an active run's events update in real time. Spec in
`docs/rig/milestones/p2/`. Not yet written — needs milestone + issue docs
before implementation.

**Goal:** polling `harness_get_events` every 2s when a run is `running`,
auto-scrolling to latest event, stopping when status reaches `done`/`failed`.

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
| p2 | Live monitoring — watch active runs in real time | ⬜ Needs milestone docs |
| p3 | Orchestrator — NL request → plan → confirm → execute agents | ⬜ |
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
      milestones/p1/                ← p1-001, p1-002, p1-003 (all done)
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
            RunList.tsx             ← HarnessRoute + RunsContent + EventsContent
            shared.tsx              ← NotConnected, LoadingShell
          provenance/               ← all 4 Provenance views + shared.tsx
          f2/                       ← F2Operations, F2Viewer, WatchedFolders
      hooks/
        useHarness.ts               ← useHarnessStatus, useRunList, useRunEvents, useRunDetail
        types.ts                    ← all TypeScript interfaces (harness + provenance + f2)

aetheris/
  priv/aetheris.db                  ← harness SQLite (runs, events, orbs, skills)
  priv/runs/                        ← trajectory JSON files per run
```

---

## Patterns established (this session)

**`harness_connection_status` returns `Ok`, not `Err`.**
Unlike all other harness commands (which return `Err("harness not connected")`
when `AETHERIS_DB_PATH` is absent), `harness_connection_status` returns
`Ok(HarnessStatus { connected: false, error: Some(...) })`. Check
`data.connected`, not the Result variant. This is intentional — a status
command shouldn't fail when you ask about connection status.

**Controlled/uncontrolled `MainArea`.**
`MainArea` accepts optional `activeTab`/`onTabChange` props. When omitted,
it manages tab state internally (uncontrolled mode — all existing routes).
When provided, the parent owns the active tab (controlled mode — Harness).
Controlled mode is how you build cross-tab interactions.

**`HarnessRoute` pattern for cross-tab shared state.**
When a route needs state shared between tabs (e.g. selected run), don't
put it in `Tab[]` factory functions — that path leads to pain. Instead,
create a `*Route` component that owns the shared state, wraps `MainArea`
with `activeTab`/`onTabChange`, and passes data down via props to tab
content components. See `src/components/modules/harness/RunList.tsx`.

**`get_harness_conn` helper mirrors `get_corpus_conn`.**
Both take `state: &'a State<'a, *State>` and return a `MutexGuard`. This
is the correct pattern for Tauri command handlers that need DB access.
New modules should follow the same shape.

**`useInvoke` args are not in `useCallback` deps (intentional).**
The shared `useInvoke` helper in `useHarness.ts` and `useCorpusOverview.ts`
only lists `command` in deps, not `args`. This means dynamic args won't
trigger a refetch. For fixed args this is correct. For dynamic args (like
`runId`), use an explicit `useCallback` with the arg in deps — see
`useRunEvents` and `useRunDetail` for the right pattern.

**Older patterns (still valid):**

Agent model config (two-level fallback):
```elixir
model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"
```

`Application.ensure_all_started/1` returns `{:ok, []}` not `:ok`.
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
```
