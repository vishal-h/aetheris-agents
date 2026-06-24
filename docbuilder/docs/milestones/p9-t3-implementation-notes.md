# Implementation notes — rig-p9 t3

Ticket: `chain_docbuilder.py` — top-level chained run (context builder → orchestrator),
emitting the orchestrator protocol.

---

## Two design corrections (why it is a top-level Python script)

The milestone draft's "thin agent runs `sh -c \"VAR=… mix aetheris run …\"`" plan was
infeasible — found in two stages while implementing:

1. **`run_command` can't do it.** The exec-server allowlist
   (`native/aetheris_exec_server/src/runner.rs`, `PERMITTED_COMMANDS`) rejects `sh`/`bash`
   by basename, and `run_command` has no `env` field. So per-step env can't be set via a
   tool call. (`python3` *is* allowlisted.)
2. **A wrapping agent can't do it either.** A nested `mix aetheris run` (inside an outer
   agent's run) fails: the inner run's `compile.aetheris_worker` does an unconditional
   `File.copy!` of the worker binary the outer run holds open → `ETXTBSY` ("text file
   busy"). No `--no-compile`/skip escape (verified: the copy ran even with `--no-compile`).
   Evidence: runs `docbuilder-ctx-orch-WRNyiQ` (sh blocked) and `…-lsjxug` (ETXTBSY).

**Fix:** run the chain **top-level**, not inside an agent. Top-level, the two
`mix aetheris run` children are sequential — each worker exits and frees the binary before
the next (exactly like the working `docbuilder_context` sprint). Rig runs the script via
`orchestrate_start`'s `.py` heuristic (t4). The wrapping `docbuilder_context_orchestrator.exs`
agent is **dropped**.

## What shipped

- **`scripts/chain_docbuilder.py`** — `chain(tenant, request, aetheris_dir, agents_dir,
  on_event)` runs the two sub-agents via `subprocess.run(env=…, cwd=aetheris_dir)`:
  step 1 env = TENANT+REQUEST; verify `confirmed_context.json`; step 2 env =
  TENANT+CONTEXT_FILE with **`DOCBUILDER_CONTEXT` removed** (orchestrator precedence is
  env > file). `build_plan(...)` + `--protocol` mode emit the orchestrator newline-JSON
  protocol (`plan` / `step_started` / `step_complete` / `orchestration_complete`); default
  prints a single JSON summary. Step `agent` paths match the t2 `STEP_CONFIG_HINTS` keys.
  One-click — no stdin approval gate.
- **`tests/test_chain_docbuilder.py`** — 12 tests (mock `subprocess.run`): env/cwd
  construction, `DOCBUILDER_CONTEXT` removal, all failure paths (each stops before the
  next step), `build_plan` shape, and the `on_event` emission sequence (success + failure).
- **`OrchestratorView.tsx`** — removed the now-dead `docbuilder_context_orchestrator.exs`
  `STEP_CONFIG_HINTS` entry (that agent was dropped).
- The `docbuilder_context_orchestrator.exs` agent created mid-implementation was deleted
  (never committed).

## Done-check

- `test_chain_docbuilder.py`: **12 passed**. Full docbuilder suite: **304 passed, 3
  skipped** (+3 over t2's 301). `bun run tsc --noEmit`: no errors.
- **Top-level e2e** (the fix): reset `run_log` to the May seed, then
  `python3 chain_docbuilder.py --tenant bitloka --request "…June 2026, same as last month"
  --aetheris-dir … --agents-dir … --protocol` →
  - stdout: `plan` → `step_started`/`step_complete`(done) ×2 → `orchestration_complete`; EXIT 0.
  - `confirmed_context.json`: `30-Jun-2026`, `2627/XYZ/03`, XYZ Inc.
  - rendered `xyz_inc_invoice_30-Jun-2026.{xlsx,docx,pdf}`.
  - `run_log` gained the orchestrator sub-run (`docbuilder-orch-IOR8Mw`, 30-Jun-2026) — PHASE D2 fired.

## Forward to t4

- `orchestrate_start` needs the `.py` heuristic: `script_path` ending in `.py` → spawn
  `python3 <path>` (with `--tenant/--request/--aetheris-dir/--agents-dir/--protocol`)
  instead of `mix aetheris run <path>`. (Prereq recorded in §t4.)
- The Docbuilder panel's `scriptPath` is `docbuilder/scripts/chain_docbuilder.py`.
- The panel gets the phase lifecycle for free from the emitted protocol; one-click (no
  approval gate). If a gate is wanted, it's a t4 addition.
- t5 capability matrix: add `chain_docbuilder.py` to docbuilder **scripts** (→ 2 agents /
  21 scripts); no new agent.
