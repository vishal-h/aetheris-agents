# Implementation notes — rig-p9 t5 (milestone close)

Ticket: docs sync + capability matrix + CLAUDE.md learning scan + milestone summary +
drift check. Docs-only.

---

## What shipped

- **`docs/rig/specs.md`** (the drift-checked, manifest-tracked spec — NOT the legacy
  `rig/docs/specs.md`; see path note below):
  - §4 `orchestrate_start` — documented `extra_env` (t1) + `script_path` (t4) + the `.py`
    top-level heuristic.
  - §1 env vars — added `DOCBUILDER_TENANT` (agent-side, like `GITHUB_PERSONAL_ACCESS_TOKEN`).
  - §8 module structure — added the `docbuilder/` module; updated the agentConfigDefs groups line.
- **`docs/rig/runbook.md`** — new "Docbuilder module" section (setup, the request flow, why
  it's a top-level script not an agent, inspecting the two sub-runs); added `DOCBUILDER_TENANT`
  to the env-var table (drift requires specs §1 ↔ runbook consistency).
- **`docs/capability-matrix.md`** — `chain_docbuilder.py` added to docbuilder **scripts**;
  docbuilder 2 agents / 21 scripts; repo total 25 / 59. No new agent.
- **`CLAUDE.md`** — `## Learning — rig-p9` (2 promotions): run_command no-env + sh/bash blocked
  → python script; no nested `mix aetheris run` → top-level/sequential.
- **Milestone summary** appended to `rig/docs/milestones/p9/README.md`.

## Path correction (found at t5)

The milestone doc's t5 Touches said `rig/docs/specs.md` / `rig/docs/runbook.md`, but
`drift_check.py` reads `docs/rig/specs.md` / `docs/rig/runbook.md` (`SPECS_MD`/`RUNBOOK_MD`),
and those are the manifest-tracked, actively-maintained specs (the `rig/docs/` copies are
stale legacy, untouched since early June). Updated the canonical `docs/rig/` files and fixed
the milestone doc's t5 references (`rig/docs/` → `docs/rig/`). Same class as the t1
`cargo build` path bug.

## Done-check

- `drift_check.py`: **8 PASS / 0 FAIL / 0 WARN / 13 INFO** (pre-commit). After committing,
  the changed tracked docs (`CLAUDE.md`, `capability-matrix.md`, `docs/rig/specs.md`,
  `docs/rig/runbook.md`) go ahead of the manifest → `project_knowledge` WARNs (expected;
  BL-002 human re-export).
- `routes`: 11 registry paths ↔ App.tsx (incl. `/docbuilder`). `tauri_commands`: 47 PASS.
- `DOCBUILDER_TENANT` env_vars: INFO (in specs §1, agent-side — not read via `env::var()`),
  consistent with specs §1 ↔ runbook now that both list it.

## rig-p9 close

t1–t5 complete; the Docbuilder panel runs the chain end-to-end (operator-verified smoke at
t4). **BL-002 (human-owned):** re-upload `CLAUDE.md`, `docs/capability-matrix.md`,
`docs/rig/specs.md`, `docs/rig/runbook.md`, then advance the manifest → 0 FAIL / 0 WARN.
