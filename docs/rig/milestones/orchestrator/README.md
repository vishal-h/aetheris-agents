# Orchestrator Agent Spec

**Status: IMPLEMENTED** — `agents/orchestrator.exs` created and wired up in
`orchestrate.rs`; `agents/mock_orchestrator.exs` retained for regression testing.

## Issue

- `orchestrator-agent-spec.md` — spec for the real LLM-driven orchestrator

## What was delivered

- `agents/orchestrator.exs` — full LLM-driven orchestrator using Anthropic API
  directly (`Req.post!`); reads `docs/capability-matrix.md`, plans a step
  sequence, emits plan JSON, blocks for approval, executes steps via
  `RunHelpers.load_agent_file` + `Aetheris.start_run` + `RunHelpers.await_run`
- `orchestrate.rs:18` — spawns `agents/orchestrator.exs` (not the mock)
- `agents/mock_orchestrator.exs` — kept; used in regression / offline testing
