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

### Rig — Phase 1, 2 and 3 complete ✅

| Phase | Issues | Status |
|-------|--------|--------|
| p1 | p1-001 Consolidation, p1-002 Harness DB commands, p1-003 Run list UI | ✅ All done |
| p2 | p2-001 Polling hook, p2-002 Live events UI | ✅ All done |
| p3 | p3-001 Mock script, p3-002 Rust backend, p3-003 Orchestrator UI | ✅ All done |

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

**What p3 delivered:**
- `agents/mock_orchestrator.exs` — deterministic Elixir script; stdin/stdout newline-delimited JSON
- `commands/orchestrate.rs` — 4 commands: start, poll, approve, cancel; reader thread + job map
- `useOrchestrator` hook — full phase state machine; poll effect self-terminates on terminal phase
- `OrchestratorView` — single-view workflow (idle → planning → plan_ready → executing → done/cancelled/error)

### Infrastructure — done

- Model parameterisation: `PROVENANCE_MODEL` → `AETHERIS_MODEL` → hardcoded fallback
- Capability matrix: committed at `docs/capability-matrix.md`
- Test sandbox: `provenance/scripts/create_test_sandbox.py` resets between runs

---

## What is in progress

### Thread 2 — uc-provenance-validation

Blocked on `ANTHROPIC_API_KEY` available in shell. Steps in `ROADMAP.md`.

---

## What comes next (Rig roadmap)

| Phase | Goal | Status |
|-------|------|--------|
| p1 | Consolidation + run list UI | ✅ Complete |
| p2 | Live monitoring | ✅ Complete |
| p3 | Orchestrator — NL → plan → confirm → execute | ✅ Complete |
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
          orchestrator/OrchestratorView.tsx  ← p3: single-view workflow, no MainArea wrapper
      hooks/
        useHarness.ts                 ← polling useRunEvents + 3 other hooks
        useOrchestrator.ts            ← p3: full phase state machine
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

## Prompts for Claude Code (p4)

p1, p2, p3 are all complete. p4 (Trajectory Explorer) is the next phase.
Milestone doc not yet written — create it before starting implementation.

### p4 kickoff

```
Create docs/rig/milestones/p4/ with README.md and issue docs.
Goal: full event detail view, event search/filter, and export.
Base it on the same pattern as p1-003: route issues under milestones/p4/.
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

**Env var delivery for Mix scripts.**
Pass request data via environment variable (`ORCHESTRATOR_REQUEST`), not CLI args.
`mix run script.exs arg` passes args to Mix, not to the script — `System.argv()` is
unreliable in this context. `System.get_env/1` is the correct pattern.

**`aetheris_dir` derived, not configured.**
The working directory for spawning the Mix process is derived from the existing
`AETHERIS_DB_PATH`: `Path::new(&path).parent().parent()` (priv/ → aetheris/).
No second env var needed. `AETHERIS_AGENTS_PATH` is the only new var (points to
`aetheris-agents/` for the script path).

**`orchestrate_approve` clones the stdin Arc before releasing the jobs lock.**
The pattern: acquire jobs lock → clone `job.stdin` (Arc clone is cheap) → drop
the lock → write to stdin. This avoids holding the jobs lock during stdin I/O,
which would block `orchestrate_poll` (which also acquires the same lock).
```rust
let stdin = {
    let jobs = state.jobs.lock().unwrap();
    let job  = jobs.get(&job_id).ok_or("job not found")?;
    job.stdin.clone()  // Arc clone — cheap; jobs lock released here
};
// Write without holding the jobs lock:
let mut guard = stdin.lock().unwrap();
let result = writeln!(guard, "{}", msg).map_err(|e| format!(...));
result
```
Note: the `let result = ...; result` pattern is required because Rust extends
temporary `MutexGuard` lifetimes in tail-position expressions, causing borrow
errors. Binding to a variable forces the guard to drop before the function exits.

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

**Poll effect deps `[jobId, phase, processMessage]` (p3 `useOrchestrator`).**
`phase` must be in the dependency array. When a terminal phase (`idle`, `done`,
`cancelled`, `error`) is set, the effect re-runs, hits the early-return guard, and
the previous interval is cleaned up. Without `phase` in deps, polling would continue
past terminal states — the effect would never re-run to clear the interval.

**`OrchestratorView` is not a tabs component.**
Single-view workflow — renders directly into the route's padded div, no `MainArea`
wrapper. Use this pattern for any future workflow that owns its own layout rather
than fitting into the tabbed inspector model.
```tsx
<Route path="/orchestrator" element={
  <div className="flex flex-1 flex-col h-full bg-background overflow-y-auto p-8">
    <OrchestratorView />
  </div>
} />
```

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
