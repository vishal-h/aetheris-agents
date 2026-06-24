# Implementation notes — rig-p9 t4

Ticket: Docbuilder panel — dedicated `/docbuilder` module that runs the chain
script top-level and shows the phase lifecycle.

---

## What shipped

**Prerequisite (Rust + hook):**
- `src-tauri/src/commands/orchestrate.rs` — `orchestrate_start` gains
  `script_path: Option<String>`. `None` → the existing `agents/orchestrator.exs` via
  `mix aetheris run` (existing callers unaffected). A `script_path` ending in `.py` is
  spawned **top-level** as `python3 <full_path> --tenant <T> --request <R> --aetheris-dir
  <state.aetheris_dir> --agents-dir <state.agents_path> --protocol` (tenant from
  `extra_env` else `agent_config`). `agent_config` + `extra_env` are still injected as env
  (so `ANTHROPIC_API_KEY`, `AETHERIS_MODEL`, etc. reach the chain's sub-runs). One heuristic,
  no new fields — per the t1/t3 review.
- `src/hooks/useOrchestrator.ts` — `start(request, extraEnv?, scriptPath?)`; passes
  `scriptPath` (camelCase) to `invoke`. Omitted → Rust `None` → orchestrator default.

**Panel:**
- `src/hooks/useDocbuilder.ts` — thin wrapper over `useOrchestrator`; `run(request)` calls
  `start(request, { DOCBUILDER_REQUEST: request }, 'docbuilder/scripts/chain_docbuilder.py')`.
- `src/components/modules/docbuilder/DocbuilderView.tsx` — request textarea, read-only
  tenant from `useAgentConfig` (Settings link if unset, Run disabled until set), phase
  lifecycle (own lightweight `StepRow`/`StepIcon` — does not touch `OrchestratorView`), and
  on `done` reads `output/renamed.json` via
  `invoke('tools_read_script', { useCase: 'docbuilder', file: 'output/renamed.json' })`
  to list rendered files (missing/unparseable → "Run complete", never errors the panel).
- `registry.ts` (docbuilderModule, `/docbuilder`, `FileText` icon), `App.tsx` (route),
  `hooks/index.ts` (export) — module registration.

---

## Design notes

- **One-click, no approval gate.** `chain_docbuilder.py --protocol` emits
  `plan → step events → orchestration_complete` without waiting on stdin. `useOrchestrator`
  goes `planning → plan_ready` (on `plan`) then `→ done` (on `orchestration_complete`); it
  never enters `executing` because `approve()` isn't called. The panel therefore renders the
  step list **whenever `plan` exists** (phase-tolerant), so steps update live (`step_started`
  → running, `step_complete` → done) through `plan_ready` → `done`. No Approve button.
- **Failed run** → `step_complete{failed}` + `orchestration_complete` → phase `done` with
  "Completed with errors" (amber), matching the Orchestrator panel (t3/F1). The rendered-file
  list is only shown when no step failed.
- **No `types.ts` change** — the hook reuses `OrchestratorPhase`/`StepStatus`/`PlanStep`;
  no `DocbuilderState` was needed.
- **No `OrchestratorView.tsx` change** — `StepRow`/`StepIcon` are duplicated (small) rather
  than exported from `OrchestratorView`, keeping t4 to its Touches.

---

## Done-check

- `bun run tsc --noEmit` → no errors.
- `cargo build` (from `src-tauri`) → Finished, no errors.
- `grep` registry/route/`tools_read_script`/`chain_docbuilder` → all present.
- **`cargo tauri dev` smoke — NOT run** (interactive GUI; no display). Manual gate:
  1. Sidebar shows "Docbuilder"; 2. panel shows request + tenant (or Settings link);
  3. submit runs `chain_docbuilder.py` top-level (`.py` heuristic); 4. phase lifecycle
  renders (planning → plan → steps → done); 5. on done, rendered file list from `renamed.json`.

---

## Forward to t5

- Capability matrix: `chain_docbuilder.py` → docbuilder **scripts** (2 agents / 21 scripts;
  total 25 / 59). No new agent.
- specs.md: `orchestrate_start` gains `extra_env` (t1) + `script_path` (t4); new Docbuilder
  module in §8; `DOCBUILDER_TENANT` in §1 (added t2).
- runbook.md: Docbuilder panel section (tenant in Settings, the request flow, the two
  sub-run trajectories in the Harness).
- CLAUDE.md `## Learning — rig-p9`: the two harness constraints (run_command no-env/sh-blocked
  → python script; no nested `mix aetheris run` → top-level/sequential).
