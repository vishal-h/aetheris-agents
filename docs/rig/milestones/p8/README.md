# Phase 8 — Orchestrator Reliability + Drive Split

**Status: IMPLEMENTED**

**Goal:** Make the Orchestrator robust for production use: surface per-step
errors with actionable detail, split Drive operations into separate agents,
add cancel support, and show config readiness hints per agent.

## Issues

- `p8-001-plan-enrichment.md` — `STEP_CONFIG_HINTS` map; per-agent env var checklist in plan view
- `p8-002-drive-folder-convention.md` — Drive folder naming convention
- `p8-003-orchestrator-reliability.md` — cancel, stepErrors, failed-step display
- `p8-004-drive-agent-split.md` — separate `drive_download_orchestrator.exs` + `drive_upload_orchestrator.exs`

## What was delivered

- `STEP_CONFIG_HINTS` in `OrchestratorView.tsx:13-31` — maps agent paths to env var checklists shown in plan view
- `stepErrors` and `stepStatuses` in `useOrchestrator.ts` — failed steps display error message with Drive ID linkification
- `orchestrate_cancel` in `orchestrate.rs:115` — kills child process on cancel
- `drive/agents/drive_download_orchestrator.exs` — download-only agent
- `drive/agents/drive_upload_orchestrator.exs` — upload-only agent
- `drive/agents/drive_orchestrator.exs` — combined agent for backwards compatibility
