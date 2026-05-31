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
- Harness module in sidebar: Runs tab (table + status filter) and Events tab
- Controlled/uncontrolled `MainArea` — supports cross-tab shared state

**What p2 delivered:**
- `useRunEvents` polls every 2s when `{ polling: true }` — stops on `run_complete`
- Smart auto-scroll (respects user scroll position, 50px threshold)
- Pulsing "Live" indicator while polling
- Local status badge update on `run_complete` — no extra network call

### Infrastructure — done

- Model parameterisation: `PROVENANCE_MODEL` → `AETHERIS_MODEL` → hardcoded fallback
- Capability matrix: committed at `docs/capability-matrix.md`
- Test sandbox: `provenance/scripts/create_test_sandbox.py` resets between runs

---

## What is in progress

### Rig p3 — Orchestrator

Docs written and committed. Implementation not yet started.

| Issue | Status | Notes |
|-------|--------|-------|
| p3-001 Mock script | ⬜ Ready | Elixir; lives in `aetheris-agents/agents/` |
| p3-002 Rust backend | ⬜ Ready | `commands/orchestrate.rs`, `OrchestratorState` in `lib.rs` |
| p3-003 Orchestrator UI | ⬜ Blocked on 001+002 | `OrchestratorView`, `useOrchestrator` hook |

**001 and 002 can be implemented in parallel — they share only `protocol.md`.**
003 needs both merged first.

**Key design decisions (all in `docs/rig/milestones/p3/`):**
- IPC via stdin/stdout newline-delimited JSON (not temp files)
- Request passed via `ORCHESTRATOR_REQUEST` env var (not CLI arg — Mix arg parsing is unreliable)
- `AETHERIS_AGENTS_PATH` — one new env var; `aetheris_dir` derived from existing `AETHERIS_DB_PATH`
  (parent of `priv/` — no second new var needed)
- Frontend polls `orchestrate_poll` every 1s (consistent with p2 polling pattern)
- `OrchestratorRoute` is not a tabs component — single-view workflow, rendered directly

**p3-002 is the hardest piece.** Reader thread + `Arc<Mutex<>>` pattern for the stdout buffer.
The issue doc has the full Rust code for all 4 commands — Claude Code should use it verbatim.

### Thread 2 — uc-provenance-validation

Blocked on `ANTHROPIC_API_KEY` available in shell. Steps in `ROADMAP.md`.

---

## What comes next (Rig roadmap)

| Phase | Goal | Status |
|-------|------|--------|
| p1 | Consolidation + run list UI | ✅ Complete |
| p2 | Live monitoring | ✅ Complete |
| p3 | Orchestrator — NL → plan → confirm → execute | 🔄 Docs done, impl pending |
| p4 | Trajectory explorer — full event detail, search, export | ⬜ |

---

## Key files

```
aetheris-agents/
  rig/
    CLAUDE.md                         ← authoritative context for Claude Code (read first)
    src-tauri/src/
      lib.rs                          ← HarnessState + CorpusState + OrchestratorState (p3)
      commands/
        harness.rs                    ← 4 read-only SQLite commands
        orchestrate.rs                ← p3: 4 process management commands
        provenance.rs
        f2.rs
    src/
      App.tsx                         ← routes: /harness, /orchestrator, /f2/*, /provenance
      components/
        shell/MainArea.tsx            ← controlled/uncontrolled tabs
        modules/
          harness/RunList.tsx         ← HarnessRoute + live EventsContent
          orchestrator/               ← p3: OrchestratorView (to be created)
      hooks/
        useHarness.ts                 ← polling useRunEvents + 3 other hooks
        useOrchestrator.ts            ← p3: full state machine (to be created)
        types.ts                      ← all TypeScript interfaces
  docs/rig/milestones/
    p1/                               ← done
    p2/                               ← done
    p3/
      README.md                       ← p3 overview + completion gate
      protocol.md                     ← JSON schema reference (read before p3-001/002)
      p3-001-mock-script.md           ← mock_orchestrator.exs spec
      p3-002-rust-backend.md          ← OrchestratorState + 4 Tauri commands (full code)
      p3-003-orchestrator-ui.md       ← useOrchestrator hook + OrchestratorView states
```

---

## Prompts for Claude Code (p3)

### p3-001 (run from aetheris-agents/)

```
Read docs/rig/milestones/p3/p3-001-mock-script.md and implement.

Context:
- File goes in aetheris-agents/agents/mock_orchestrator.exs
- Jason is available (aetheris/mix.exs has {:jason, "~> 1.4"})
- Request is passed via ORCHESTRATOR_REQUEST env var — not CLI args
- After writing the file, run the manual test from p3-001-mock-script.md
  to confirm the approve path produces the correct JSON sequence
```

### p3-002 (run from aetheris-agents/rig/)

```
Read docs/rig/milestones/p3/protocol.md and
docs/rig/milestones/p3/p3-002-rust-backend.md and implement.

Context:
- Run from aetheris-agents/rig/
- Add OrchestratorState and OrchestratorJob to src-tauri/src/lib.rs
  alongside the existing HarnessState and CorpusState
- aetheris_dir is derived from AETHERIS_DB_PATH (parent of priv/) —
  do not add a second env var
- Add serde_json = "1" to Cargo.toml if not already present
- The issue doc has full Rust implementations for all 4 commands —
  use them verbatim, do not rewrite
- Add TypeScript types from protocol.md to src/hooks/types.ts and
  export from src/hooks/index.ts
- When done: cargo build exits 0, zero warnings
```

### p3-003 (run from aetheris-agents/rig/, after 001 + 002 merged)

```
Read docs/rig/milestones/p3/protocol.md and
docs/rig/milestones/p3/p3-003-orchestrator-ui.md and implement.

Context:
- Run from aetheris-agents/rig/
- OrchestratorView is NOT a tabs component — single-view workflow,
  rendered directly in a padded div in App.tsx (see issue doc)
- Add Sparkles to iconMap in Sidebar.tsx
- orchestratorModule goes second in the modules array in registry.ts,
  after harnessModule
- No <form> tags, no <textarea> inside a form — onClick/onChange only
- When done: bun run build exits 0, zero TypeScript errors
```

---

## Patterns established

### Rust / Tauri

**`harness_connection_status` returns `Ok`, not `Err`.**
Returns `Ok(HarnessStatus { connected: false, error: Some(...) })` when not
connected. All other harness commands return `Err("harness not connected")`.
Check `data.connected`, not the Result. Documented in `rig/CLAUDE.md`.

**`get_harness_conn` / `get_corpus_conn` pattern.**
Helper takes `state: &'a State<'a, *State>` → returns `MutexGuard`. Follow
for all future DB command handlers.

**`OrchestratorState` pattern (p3).**
Long-running child processes stored as `Arc<Mutex<Child>>` in a job map.
Reader thread pushes parsed `serde_json::Value` to `Arc<Mutex<Vec>>` buffer.
Frontend drains buffer via `orchestrate_poll`. `AtomicBool` signals EOF.

### React / Frontend

**Controlled/uncontrolled `MainArea`.**
Optional `activeTab`/`onTabChange` props. Without: internal state (all
existing routes). With: parent owns tab (Harness route). Use controlled
when a route needs cross-tab shared state.

**`HarnessRoute` pattern.**
When a route needs shared state across tabs, create a `*Route` component
that owns state and wraps `MainArea` with `activeTab`/`onTabChange`.

**Three-effect polling pattern (`useRunEvents`).**
1. Sync internal `activelyPolling` with caller's option
2. Watch data for stop signal (`run_complete`); self-terminate
3. `setInterval` tied to `activelyPolling`

**`loading && !data` for polling-safe skeletons.**
Shows skeleton on initial load only. Prevents flash on every poll refetch.
Use anywhere a polling hook drives a list.

### Elixir

**Agent model config (two-level fallback):**
```elixir
model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"
```

**`Application.ensure_all_started/1` returns `{:ok, []}` not `:ok`.**

---

## Quick commands

```bash
# Open Rig
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb  # optional
cargo tauri dev

# Test mock orchestrator manually (from aetheris/)
cd ~/sandbox/elixirws/aetheris
(sleep 3; echo '{"type":"approval","approved":true}') \
  | ORCHESTRATOR_REQUEST="email payslips" \
    mix run ../aetheris-agents/agents/mock_orchestrator.exs

# TypeScript build check
cd ~/sandbox/elixirws/aetheris-agents/rig && bun run build

# Check a run
cd ~/sandbox/elixirws/aetheris
mix aetheris inspect <run_id>
mix aetheris list --limit 5
```
