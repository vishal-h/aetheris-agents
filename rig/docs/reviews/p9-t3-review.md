# Review — rig-p9 t3 — round 1

Reviewer: claude-ui
Subject: `chain_docbuilder.py` — top-level chained run + orchestrator protocol (commit `acc12b1`)

---

## Findings

1. **[non-blocking → evidence provided] `orchestration_complete` emitted even on
   failure.** `main()` emits `orchestration_complete` then `sys.exit(code)` (code may be 1).
   **Evidence:** `useOrchestrator.ts` transitions to `'done'` on `orchestration_complete`
   (line 41) and does NOT read the process exit code — `'error'` phase fires only on an
   invoke/poll exception. A failed step surfaces via its `step_complete{status:"failed"}`;
   the done-view computes `anyFailed = stepStatuses.some(s => 'failed')` and renders
   **"Completed with errors"** (amber) vs "Done" (`OrchestratorView.tsx:332–338`). So a
   failed chain run shows "Completed with errors" — matching the real orchestrator. The
   design (unconditional `orchestration_complete` + correct exit code) is right; recorded
   in the t3 implementation notes (§"Review F1"). No code change.

2. **[non-blocking → merge gate] `cargo tauri dev` smoke for the `STEP_CONFIG_HINTS`
   removal** (dead `docbuilder_context_orchestrator.exs` entry) not run (no display). tsc
   passes; diff is correct. **Manual gate (operator-owned):** confirm the Orchestrator
   module still renders with the reduced hints map.

---

## Cross-ticket notes

- **t4 arg-passing (actioned in §t4):** `chain_docbuilder.py` requires `--tenant`,
  `--request`, `--aetheris-dir`, `--agents-dir`, `--protocol`. Updated the §t4 prereq to
  state that `orchestrate_start`'s `.py` branch supplies `--aetheris-dir` (`aetheris_dir`
  from state) and `--agents-dir` (`agents_path` / `AETHERIS_AGENTS_PATH`), with `--tenant`
  / `--request` mapped from the env values — so the script never errors on a missing arg.
- **t5 CLAUDE.md learning scan — two standing instructions qualify:**
  1. `run_command` has no `env` field and the exec-server allowlist blocks `sh`/`bash` —
     per-step env / shell logic must go in a `python3` script.
  2. `mix aetheris run` cannot be nested (inner worker-binary recopy → ETXTBSY) — chained
     runs must be top-level / sequential.

---

## Outcome

No t3 code changes. F1 answered with consumer-code evidence (failed run → "Completed with
errors", not a silent "Done"). F2 is the manual smoke gate. t4 arg-passing note actioned in
the milestone doc. **t3 clear once the manual Orchestrator-render smoke is confirmed.**
