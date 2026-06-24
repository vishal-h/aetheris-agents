# Implementation notes — rig-p9 t1

Ticket: `orchestrate_start` per-run env vars (Rust + TypeScript).

---

## What shipped

- **`src-tauri/src/commands/orchestrate.rs`** — `orchestrate_start` gains
  `extra_env: HashMap<String, String>` (added `use std::collections::HashMap;`).
  After the existing `for (key, value) in &agent_config` loop, a second loop injects
  `extra_env` — so per-run vars are applied *after* stored config and **win on a key
  collision**. Nothing is persisted; the values arrive per invocation.
- **`src/hooks/useOrchestrator.ts`** — `start(request, extraEnv: Record<string,string> = {})`;
  passes `{ request, extraEnv }` to `invoke('orchestrate_start', …)`. `extraEnv` is
  camelCase per rig/CLAUDE.md (Tauri maps it to the Rust `extra_env`).
- **`src/components/modules/orchestrator/OrchestratorView.tsx`** — collapsible
  "Additional env vars" section in the idle request form, between the textarea and the
  Run button:
  - Collapsed by default; chevron toggle (`ChevronRight`/`ChevronDown`).
  - Header shows a count when ≥1 key is filled.
  - Each row: KEY + value text inputs + a × remove button; "+ Add variable" appends a row.
  - `extraEnvRows` is ephemeral React state (never persisted). Serialised to
    `Record<string,string>` (rows with an empty key skipped) and passed to
    `start(request, …)`.
  - Cleared to `[]` when `phase` becomes `done`/`cancelled` (via a small `useEffect`),
    so the next run starts fresh.

---

## Done-check

- `cargo build` (from `rig/src-tauri`) → **Finished, no errors**.
  (Note: the milestone done-check says `cd rig && cargo build`, but `Cargo.toml` lives in
  `rig/src-tauri/` — `cargo build` must run from there. `cargo tauri dev` works from
  `rig/`. Ran the build from `src-tauri`.)
- `bun run tsc --noEmit` → **no errors**.
- `grep extra_env src-tauri/src/commands/orchestrate.rs` → 2 hits (param + injection loop).
- `grep extraEnv|Additional env OrchestratorView.tsx` → state + form section present.
- **`cargo tauri dev` smoke test — NOT run** (interactive GUI; no display in this
  environment). Needs a manual pass: Orchestrator → "Additional env vars" collapsed by
  default, expands, add/remove rows work, key/value inputs accept text.

---

## Notes / forward concerns

- **No other caller of `orchestrate_start`** breaks: the only frontend caller is
  `useOrchestrator.start` (now always passes `extraEnv`); `lib.rs` only registers the
  command. The new param is a non-`Option` `HashMap` per the spec — safe because the hook
  always supplies it (default `{}`).
- **Forward to t4 (gap found):** `orchestrate_start` currently **hardcodes** the script
  path (`{agents_path}/agents/orchestrator.exs`) and `useOrchestrator.start` takes no
  script path. The t4 plan assumes `orchestratorStart({ scriptPath, request, extraEnv })`
  to run `docbuilder_context_orchestrator.exs`. t4 will therefore also need to add a
  `script_path`/`scriptPath` parameter to `orchestrate_start` + the hook (it is not part
  of t1's scope). Flagging here so t4 budgets for it.
- The request textarea is intentionally **not** cleared on `reset` (pre-existing
  behaviour); only the per-run env rows are cleared on terminal phase.
