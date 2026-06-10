# Phase 3 — Orchestrator

**Status: IMPLEMENTED** — full pipeline including real LLM-driven
`agents/orchestrator.exs`; `agents/mock_orchestrator.exs` kept for regression.

**Goal:** Type a natural language request, confirm a plan, watch it execute.
Backed by a deterministic mock script so the full UI pipeline can be built
and tested without a real LLM orchestrator.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Mock script](p3-001-mock-script.md) | — | `mock_orchestrator.exs` + protocol definition |
| 002 | [Rust backend](p3-002-rust-backend.md) | 001 | Process spawning, stdin/stdout management, 4 Tauri commands |
| 003 | [Orchestrator UI](p3-003-orchestrator-ui.md) | 001 + 002 | OrchestratorRoute, all 5 UI states, polling |

001 and 002 can be written in parallel — they share only the protocol doc.
003 needs both.

---

## Completion gate

- Typing a request and clicking Run shows a spinner, then a plan
- Approving executes the mock steps with per-step progress
- Cancelling stops the process and shows a cancelled state
- "Run another" resets to idle
- No LLM call is made at any point — the mock script is fully deterministic
- All existing modules (Harness, Provenance, F2) unaffected

---

## Key decisions

**Mock-first.** The real orchestrator agent (`orchestrator.exs`) is not part
of p3. The mock script gives a stable, controllable backend. The real agent
drops in later by changing the script path.

**stdin/stdout, not temp files.** The architecture doc mentioned temp-file
polling as a sketch. stdin/stdout is cleaner: no filesystem cleanup, no
race conditions, standard IPC for child processes.

**One new env var.** `AETHERIS_AGENTS_PATH` — path to the `aetheris-agents/`
root. The aetheris harness directory is derived from the existing
`AETHERIS_DB_PATH` (parent of `priv/`) — no second new var needed.

**Polling, not Tauri events.** Frontend polls `orchestrate_poll` every 1s to
drain the message buffer. Consistent with the existing polling pattern used
in p2 live monitoring.

**No tabs.** The Orchestrator module renders a single-view workflow, not a
tabbed inspector. `OrchestratorRoute` fills `flex-1` directly without
wrapping `MainArea`.

See `protocol.md` for the full JSON schema.
