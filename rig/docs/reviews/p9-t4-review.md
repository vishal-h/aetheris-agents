# Review — rig-p9 t4 — round 1

Reviewer: claude-ui
Subject: Docbuilder panel + `orchestrate_start` `.py` heuristic (commit `03759f3`)

---

## Findings

1. **[blocking → closed on evidence] `.py` branch `stdin` piping.** Concern: does the
   `.py` branch spawn with piped stdin/stdout, or only the `.exs` branch? **Evidence:** the
   `if rel.ends_with(".py") { … c } else { … c }` block only *constructs* the `Command`
   (python3 vs mix). The shared setup is applied **after** the `if/else`, to `cmd`,
   regardless of branch:
   ```rust
   let mut cmd = if rel.ends_with(".py") { … c } else { … c };
   cmd.stdin(std::process::Stdio::piped())
       .stdout(std::process::Stdio::piped())
       .stderr(std::process::Stdio::null());
   ```
   Neither branch touches `stdin` internally. So the `.py` chain gets piped stdin + stdout:
   stdout carries the protocol to `orchestrate_poll`; stdin is available (harmless — the
   one-click chain doesn't read it). **No code change.**

2. **[non-blocking, no action] Tenant + request channels.** `--tenant` resolves from
   `extra_env` then `agent_config`; `--request` from the `request` param. Both
   `DOCBUILDER_TENANT`/`DOCBUILDER_REQUEST` are also in the process env via the env-injection
   loops — env var + CLI arg are present and consistent. ✓

3. **[non-blocking → merge gate] `cargo tauri dev` smoke not run** (no display). Manual
   gate (operator-owned), five-point checklist in the §t4 done-check.

---

## Cross-ticket notes

- t3/F1 closed: the failed-run UI handling (`orchestration_complete` → `done`; "Completed
  with errors" via `stepStatuses`) is documented in the t4 notes and verified against
  `useOrchestrator`/`OrchestratorView`.
- t5 CLAUDE.md learning scan — two standing instructions confirmed (recurred as design
  blockers across t3/t4): (1) `run_command` has no `env` field + `sh`/`bash` blocked →
  per-step env in a `python3` script; (2) `mix aetheris run` cannot be nested → chained
  runs top-level / sequential.

---

## Outcome

No t4 code changes. F1 closed with evidence (shared `stdin/stdout/stderr` applies to both
branches). F2 confirmation; F3 is the manual `cargo tauri dev` smoke gate. **t4 clear once
the smoke pass is confirmed.**
