# Handoff — Aetheris + Provenance + Rig

> **SUPERSEDED** — This handoff doc was written 2026-06-08 and is now out of date.
> The authoritative current-state reference is
> `docs/rig/current-state-2026-06.md` (code-verified, 2026-06-11).

**Session date:** 2026-06-08
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

### Rig — p1 through p4-tools complete ✅

| Phase | Issues | Status |
|-------|--------|--------|
| p1 | p1-001 Consolidation, p1-002 Harness DB commands, p1-003 Run list UI | ✅ Done |
| p2 | p2-001 Polling hook, p2-002 Live events UI | ✅ Done |
| p3 | p3-001 Mock script, p3-002 Rust backend, p3-003 Orchestrator UI | ✅ Done |
| p4-tools | p4-001 Manifests, p4-002 Rust backend, p4-003 Tools UI, p4-004 MCP discovery, p4-005 MCP Try panel, p4-006 stdio handshake | ✅ Done |

**What p3 delivered:**
- `agents/mock_orchestrator.exs` — deterministic mock for full UI pipeline testing
- `commands/orchestrate.rs` — 4 commands: start, poll, approve, cancel
- `OrchestratorView` — idle → planning → plan_ready → executing → done/cancelled
- stdin/stdout newline-delimited JSON IPC; `ORCHESTRATOR_REQUEST` via env var

**What p4-tools delivered:**
- `tools.json` manifest format — per use-case, `manifest_version: "1"`, declared + undeclared scripts
- `commands/tools.rs` — 5 commands: inventory walker, read script, run script, call MCP, list MCP
- `ToolsView` — two-panel: collapsible tree (use cases + Harness + MCP) + detail/run panel
- Script runner: arg form from manifest, `buildArgs` positional-before-flagged, output block
- MCP discovery: HTTP (curl) + stdio (full handshake) at inventory load time
- MCP Try panel: JSON textarea pre-populated from `input_schema`, Run → live response
- GitHub MCP server wired up and working end-to-end

### Infrastructure — done

- Model parameterisation: `PROVENANCE_MODEL` → `AETHERIS_MODEL` → hardcoded fallback
- Capability matrix: committed at `docs/capability-matrix.md`
- Test sandbox: `provenance/scripts/create_test_sandbox.py` resets between runs
- Agent config: `~/.local/share/dev.rig.app/agent-config.json` — injected as env vars at orchestrator spawn
- GitHub MCP: `github-mcp-server` installed via `go install`, token in Rig Settings

---

## What is in progress

Nothing actively in progress. Next phases are defined below.

---

## What comes next (Rig roadmap)

| Phase | Goal | Status |
|-------|------|--------|
| p1 | Consolidation + run list UI | ✅ Complete |
| p2 | Live monitoring | ✅ Complete |
| p3 | Orchestrator — NL → plan → confirm → execute | ✅ Complete |
| p4-tools | Tools explorer — browse, inspect, run scripts + MCP tools | ✅ Complete |
| p5-* | TBD (p5–p8 exist in repo — read milestone dirs for context) | ⬜ |

---

## Key files

```
aetheris-agents/
  rig/
    CLAUDE.md                         ← authoritative context for Claude Code (read first)
    src-tauri/src/
      lib.rs                          ← HarnessState + CorpusState + OrchestratorState + ToolsState
      commands/
        harness.rs                    ← 4 read-only SQLite commands
        orchestrate.rs                ← 4 process management commands
        tools.rs                      ← 5 tools commands + MCP session logic
        provenance.rs
        f2.rs
    src/
      App.tsx                         ← routes: /harness, /orchestrator, /tools, /f2/*, /provenance
      components/
        shell/MainArea.tsx            ← controlled/uncontrolled tabs
        modules/
          harness/RunList.tsx         ← HarnessRoute + live EventsContent
          orchestrator/OrchestratorView.tsx
          tools/                      ← ToolsView, ToolTree, ToolDetail
      hooks/
        useHarness.ts
        useOrchestrator.ts
        useTools.ts
        types.ts                      ← all TypeScript interfaces
  docs/rig/milestones/
    p1/                               ← done
    p2/                               ← done
    p3/                               ← done
    p4-tools/                         ← done (p4-001 through p4-006)
  mcp/
    mcp_servers.json                  ← declared MCP servers (google-drive, node-stdio, github)
  payslip/tools.json                  ← script manifest
  drive/tools.json                    ← placeholder
  email/tools.json                    ← placeholder
  api/tools.json                      ← placeholder

aetheris/
  mcp/
    stdio/github/
      README.md                       ← GitHub MCP setup instructions
      tools.json                      ← 12 read-only tool definitions
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

**`ToolsState` pattern (p4-tools).**
Stateless — just `agents_path: Option<String>` read once at startup.
No job map. Script runs are synchronous (`.output()`). MCP calls use
`run_stdio_session` which is also synchronous.

**MCP stdio session pattern (`run_stdio_session`).**
All stdio MCP servers require a handshake before accepting method calls:
1. Send `initialize` (id=1)
2. Send `notifications/initialized` (no response)
3. Send actual request (id=`MCP_SESSION_REQUEST_ID` = 99)
4. Read via channel until response with id=99 received or 15s timeout
5. Drop stdin → EOF → server exits

Reader thread spawned before any stdin writes. Response-driven stdin
close (channel + deadline loop) — no fixed sleep. `MCP_SESSION_REQUEST_ID`
(99) avoids collision with initialize response (id=1).

**`tools_run_script` path traversal guard asymmetry.**
`tools_read_script` guards against agents root (can read any declared file).
`tools_run_script` guards against use-case root (execution stays within use case).
Intentional — documented here because it looks like a bug.

**`env` field in `McpServerConfig`.**
Declared env vars forwarded to child process via `.env(k, resolved)`.
Template syntax: `"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"` —
value resolved from `std::env::var` at spawn time. Applied in both
`discover_stdio_tools` and `call_stdio_tool` via `run_stdio_session`.

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

**`key` prop for form state reset.**
When a detail panel has local form state (arg values, textarea content),
key it on the selected item's identity: `key={`${use_case}/${script.name}`}`
or `key={`${server_id}/${tool_name}`}`. Forces React remount on selection
change, resetting all local state cleanly.

**Tools route has no outer padding.**
`/tools` route wrapper in `App.tsx` has no `p-8` — `ToolsView` manages its
own padding. Left panel must flush against the border. Do not add padding
to the route wrapper.

### Elixir

**Agent model config (two-level fallback):**
```elixir
model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"
```

**`Application.ensure_all_started/1` returns `{:ok, []}` not `:ok`.**

### MCP

**`github-mcp-server` requires `GITHUB_PERSONAL_ACCESS_TOKEN`**, not
`GITHUB_TOKEN`. The binary calls `os.Exit` on EOF before flushing stdout —
handled by the response-driven stdin close in `run_stdio_session`.

**MCP discovery runs synchronously at inventory load time.**
If a server is unreachable, the 15s timeout applies per server.
Known latency: GitHub token scope fetch adds ~400ms on first connect.
If inventory load becomes noticeably slow, move MCP discovery to a
lazy separate call after main inventory loads.

**`parse_tool_call_response` filters by `MCP_SESSION_REQUEST_ID`.**
The response buffer contains multiple lines including the initialize
response. Filter `id == 99` to get only the tool call result.
`parse_tools_list_response` uses `val.pointer("/result/tools")` which
already skips the initialize response implicitly.

**Adding a new MCP server:**
1. Add entry to `aetheris-agents/mcp/mcp_servers.json`
2. Add token/credential key to `agentConfigDefs.ts` if auth needed
3. Add `tools.json` at `aetheris/mcp/{transport}/{server}/tools.json`
   for documentation (not read by Rig — discovery is live)
4. Restart Rig — server appears in Tools panel automatically

---

## Quick commands

```bash
# Open Rig
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb  # optional
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...                         # for GitHub MCP
cargo tauri dev

# Test mock orchestrator manually (from aetheris/)
cd ~/sandbox/elixirws/aetheris
(sleep 3; echo '{"type":"approval","approved":true}') \
  | ORCHESTRATOR_REQUEST="email payslips" \
    mix run ../aetheris-agents/agents/mock_orchestrator.exs

# Test GitHub MCP manually (from aetheris-agents/)
(
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rig","version":"0.1.0"}}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  sleep 2
) | GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
    github-mcp-server stdio 2>/dev/null

# TypeScript build check
cd ~/sandbox/elixirws/aetheris-agents/rig && bun run build

# Check a run
cd ~/sandbox/elixirws/aetheris
mix aetheris inspect <run_id>
mix aetheris list --limit 5
```
