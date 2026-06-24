# Milestone — rig-p9 — Per-run env vars + Docbuilder Rig integration

**Repo:** aetheris-agents (Rig)
**Milestone doc path:** `rig/docs/milestones/p9/README.md`
**Depends on:** aetheris-agents `80f2b26` (m3-docbuilder closed, drift clean).
**Branch from:** current HEAD (`d0580cc` at p9 start — the repo advanced past `80f2b26`
after m3 closed), not the dependency commit.

---

## Goal

Make the full docbuilder context-builder flow operable from Rig without
touching the terminal. Today, `orchestrate_start` injects only `agent_config`
values — per-run variables like `DOCBUILDER_REQUEST` must be pre-set in the
environment before Rig launches, and the two-step flow (context builder →
orchestrator) requires two manual Orchestrator invocations.

This milestone delivers:
1. Per-run env vars in the Orchestrator request form (t1)
2. Docbuilder stored config + `STEP_CONFIG_HINTS` (t2)
3. A `chain_docbuilder.py` script that chains the two steps, run **top-level**
   by Rig and emitting the orchestrator protocol (t3 — corrected from a wrapping
   agent, which can't nest `mix aetheris run`; see §t3)
4. A dedicated Docbuilder panel with a pre-populated form and one-click
   chained execution (t4)
5. Docs sync + milestone close (t5)

---

## What is NOT in scope

- Changes to `AgentConfigState` persistence (agent-config.json format unchanged)
- Changes to the docbuilder agents, scripts, or sprint cases
- Drive upload / email review of docbuilder output from the UI
- An interactive confirm/amend loop (deferred from m3; requires a
  conversational harness layer not yet built)
- `data.db` migration of agent config or request history (backlog item)
- Multi-tenant support in the Docbuilder panel

---

## Pre-implementation verification (session start, 2026-06-24)

Two design points from the milestone draft were verified against source before
writing this doc; the t3 and t4 prompts below reflect the findings.

- **`run_command` cannot set per-invocation env, and `sh`/`bash` are blocked**
  (corrected during t3). The schema (`aetheris/lib/aetheris/execution/tool_schema/
  registry.ex`) has no `env` field — `command` / `args` / `working_dir` / `timeout_ms`
  only — AND the exec-server allowlist (`native/aetheris_exec_server/src/runner.rs`,
  `PERMITTED_COMMANDS`) rejects `sh`/`bash` by basename. The original `sh -c "VAR=… mix
  aetheris run …"` plan is therefore impossible. `python3` IS allowlisted, so t3 moves the
  per-step env plumbing into a Python script (`chain_docbuilder.py`) that the agent calls
  via a single `run_command`. (The initial draft's "use a `sh -c` wrapper" claim was wrong
  — it verified the tool schema but not the command allowlist.)
- **No new Tauri file-read command is needed for t4.** `tools_read_script`
  (`rig/src-tauri/src/commands/tools.rs`) already reads any file under
  `AETHERIS_AGENTS_PATH` (joins `use_case`/`file`, canonicalizes, rejects path traversal —
  not restricted to `scripts/`). The panel reads the rendered list via
  `invoke('tools_read_script', { useCase: 'docbuilder', file: 'output/renamed.json' })`
  after the run completes.

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Per-run env var storage | Ephemeral React state — never written to `agent-config.json` | Per-run vars like `DOCBUILDER_REQUEST` change every invocation |
| Per-run env var precedence | Per-run vars injected after `agent_config` loop — per-run wins | Allows stored `DOCBUILDER_TENANT` to be overridden ad-hoc |
| `orchestrate_start` signature | Add `extra_env: HashMap<String, String>` | Minimal; does not touch the stdin/stdout protocol or polling |
| `DOCBUILDER_TENANT` placement | Stored config (`agentConfigDefs.ts`, new "Docbuilder" group) | Stable per installation — same pattern as `AETHERIS_MODEL` |
| `DOCBUILDER_REQUEST` placement | Per-run env var + Docbuilder panel text field | Changes every invocation; no value in persisting |
| `DOCBUILDER_CONTEXT_FILE` placement | Per-run env var; set automatically by the chained orchestrator | Path is run-specific; operator never types it in the chained flow |
| Chained execution approach | `chain_docbuilder.py` run **top-level** by Rig (via `orchestrate_start`, `.py` heuristic) — runs the two `mix aetheris run` sub-agents sequentially and emits the orchestrator protocol. **Corrected (t3):** a wrapping agent can't be used — a nested `mix aetheris run` hits `ETXTBSY` re-copying the in-use worker binary. Top-level = sequential, non-nested (like the sprint). | Each sub-run still records its own trajectory; one backend job; phase lifecycle via the protocol |
| Per-invocation env in the chained agent | `chain_docbuilder.py` (python3, allowlisted) runs both sub-agents via `subprocess.run(env=…, cwd=…)`; the agent makes one `run_command` to it | `run_command` has no `env` field and `sh`/`bash` are blocked by the exec-server allowlist, so a Python script is the only way to set per-step env; deterministic + unit-testable. Step 2 removes `DOCBUILDER_CONTEXT` from env so the file is read |
| Docbuilder panel | New module (`docbuilder`) with a single route `/docbuilder` — tenant (from stored config), request field, Run button, output file list | Thin React wrapper over `orchestratorStart`; reuses `useOrchestrator` |
| Panel output file list | Read `docbuilder/output/renamed.json` via the existing `tools_read_script` command (no new Tauri command) | `tools_read_script` already reads any path under `AETHERIS_AGENTS_PATH` |
| `STEP_CONFIG_HINTS` entries | `context_builder.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']`; `docbuilder_orchestrator.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_CONTEXT_FILE']` (t2 also added a `docbuilder_context_orchestrator.exs` entry; t3 removes it — that agent was dropped) | Surfaces the vars the operator needs to verify before approving |

---

## Ticket structure

| Ticket | Title | Key artifacts |
|---|---|---|
| t1 | `orchestrate_start` per-run env vars — Rust + TypeScript | `commands/orchestrate.rs`, `useOrchestrator.ts`, `OrchestratorView.tsx` |
| t2 | Docbuilder config entries + `STEP_CONFIG_HINTS` | `agentConfigDefs.ts`, `OrchestratorView.tsx` |
| t3 | `chain_docbuilder.py` — top-level chained run, emits orchestrator protocol | `docbuilder/scripts/chain_docbuilder.py` |
| t4 | Docbuilder panel — dedicated form + chained run | `src/components/modules/docbuilder/`, `registry.ts`, `App.tsx` |
| t5 | Docs sync + drift check + milestone close | `specs.md`, `runbook.md`, `CLAUDE.md` |

---

## Tickets

### t1 — `orchestrate_start` per-run env vars

**Scope.** Add an `extra_env` parameter to `orchestrate_start` so the
frontend can pass per-run key/value pairs that are injected into the agent
process alongside `agent_config` values. Per-run vars take precedence over
stored config. Add a collapsible "Additional env vars" section to the
Orchestrator request form.

**Contract refs.**
- Agent config architecture reference — `orchestrate_start`
  iterates `agent_config` and injects each as env var; per-run vars are a
  second loop after it
- `rig/CLAUDE.md` §"Tauri invoke() argument naming" — camelCase keys in
  `invoke()` map to Rust snake_case params

**Touches.**
- `rig/src-tauri/src/commands/orchestrate.rs` — add `extra_env: HashMap<String, String>` to `orchestrate_start`; inject after the `agent_config` loop
- `rig/src/hooks/useOrchestrator.ts` — add `extraEnv?: Record<string, string>` to `orchestratorStart`; default `{}`; pass through to `invoke`
- `rig/src/components/modules/orchestrator/OrchestratorView.tsx` — add collapsible "Additional env vars" section: key/value row inputs, add/remove buttons; `extraEnv` state not persisted; pass to `orchestratorStart`
- `rig/docs/milestones/p9/t1-implementation-notes.md` — new

**Do not generate.**
- Do not modify `AgentConfigState`, `agent_config.rs`, or `agentConfigDefs.ts`
- Do not persist per-run vars anywhere
- Do not modify the stdin/stdout orchestration protocol
- Do not add Docbuilder-specific entries — that is t2

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/rig

# Cargo.toml lives in rig/src-tauri/ — build from there (subshell keeps cwd at rig/
# for the rest of the block). `cargo tauri dev` works from rig/; raw `cargo build` does not.
( cd src-tauri && cargo build 2>&1 | tail -5 )
# Expected: Finished (no errors)

bun run tsc --noEmit
# Expected: no errors

grep -n "extra_env" src-tauri/src/commands/orchestrate.rs
# Expected: ≥2 hits (param + injection loop)

grep -n "extraEnv\|Additional env" \
  src/components/modules/orchestrator/OrchestratorView.tsx
# Expected: state declaration + form section

cargo tauri dev
# Smoke: Orchestrator → "Additional env vars" section visible (collapsed),
# add/remove rows work, key/value inputs accept text
```

**Claude-code prompt.**
> Read `rig/CLAUDE.md` in full before writing any code. Then implement t1
> of `rig/docs/milestones/p9/README.md`.
>
> **Rust (`commands/orchestrate.rs`):**
> - Add `extra_env: HashMap<String, String>` to `orchestrate_start` after
>   the existing params.
> - After the existing `for (key, value) in &agent_config` loop, add:
>   `for (key, value) in &extra_env { cmd.env(key, value); }`
>   Per-run vars injected second → win over stored config on collision.
> - No other changes to the orchestrate commands.
>
> **`useOrchestrator.ts`:**
> - Add `extraEnv?: Record<string, string>` to the `orchestratorStart`
>   call signature; default to `{}` if absent.
> - Pass as `extraEnv` to `invoke('orchestrate_start', { ..., extraEnv })`.
>
> **`OrchestratorView.tsx`:**
> - Add `extraEnv` state: `useState<{ key: string; value: string }[]>([])`.
> - In the idle/request form, add a collapsible "Additional env vars" section
>   below the request textarea and above the Run button.
>   - Collapsed by default; chevron toggle expands it.
>   - When expanded: list of key/value row pairs (text inputs), an
>     "+ Add variable" button, and a × remove button per row.
>   - Serialise to `Record<string, string>` before passing to
>     `orchestratorStart` (skip rows where key is empty).
>   - Reset to `[]` on transition to `done` / `cancelled`.
> - Pass `extraEnv` (serialised) to `orchestratorStart`.
>
> Tailwind utility classes only. Follow existing form styling.
>
> **Touches:** `src-tauri/src/commands/orchestrate.rs`,
> `src/hooks/useOrchestrator.ts`,
> `src/components/modules/orchestrator/OrchestratorView.tsx`,
> `rig/docs/milestones/p9/t1-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `rig/docs/milestones/p9/README.md §t1` and include
> its full output at the top of the review packet, before the diff.

---

### t2 — Docbuilder config entries + `STEP_CONFIG_HINTS`

**Scope.** Add `DOCBUILDER_TENANT` to stored config (new "Docbuilder" group
in Settings). Add `STEP_CONFIG_HINTS` entries for the three docbuilder agents.

**Contract refs.**
- Agent config architecture reference — adding a key to
  `agentConfigDefs.ts` is sufficient for the Settings UI and automatic env
  var injection at spawn time

**Touches.**
- `rig/src/components/modules/settings/agentConfigDefs.ts` — add:
  `{ key: 'DOCBUILDER_TENANT', label: 'Tenant', group: 'Docbuilder', masked: false, placeholder: 'bitloka' }`
- `rig/src/components/modules/orchestrator/OrchestratorView.tsx` — add to `STEP_CONFIG_HINTS`:
  - `'docbuilder/agents/context_builder.exs': ['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']`
  - `'docbuilder/agents/docbuilder_orchestrator.exs': ['DOCBUILDER_TENANT', 'DOCBUILDER_CONTEXT_FILE']`
  - `'docbuilder/agents/docbuilder_context_orchestrator.exs': ['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']`
- `rig/docs/milestones/p9/t2-implementation-notes.md` — new

**Do not generate.**
- Do not add `DOCBUILDER_REQUEST` or `DOCBUILDER_CONTEXT_FILE` to
  `agentConfigDefs.ts` — per-run vars only
- Do not add a new module, route, or sidebar entry — that is t4
- Do not modify the Rust backend

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/rig

bun run tsc --noEmit

grep -n "DOCBUILDER_TENANT\|Docbuilder" \
  src/components/modules/settings/agentConfigDefs.ts
# Expected: entry with group "Docbuilder"

grep -n "context_builder\|docbuilder_orchestrator\|docbuilder_context_orchestrator" \
  src/components/modules/orchestrator/OrchestratorView.tsx
# Expected: all three agent paths in STEP_CONFIG_HINTS

cargo tauri dev
# Smoke: Settings → "Docbuilder" section with DOCBUILDER_TENANT field
```

**Claude-code prompt.**
> Read `rig/CLAUDE.md` in full before writing any code. Then implement t2
> of `rig/docs/milestones/p9/README.md`.
>
> **`agentConfigDefs.ts`:** add a new "Docbuilder" group:
> ```typescript
> { key: 'DOCBUILDER_TENANT', label: 'Tenant', group: 'Docbuilder',
>   masked: false, placeholder: 'bitloka' },
> ```
> Do not add `DOCBUILDER_REQUEST` or `DOCBUILDER_CONTEXT_FILE` here.
>
> **`OrchestratorView.tsx` (`STEP_CONFIG_HINTS`):** add three entries:
> ```typescript
> 'docbuilder/agents/context_builder.exs':
>   ['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST'],
> 'docbuilder/agents/docbuilder_orchestrator.exs':
>   ['DOCBUILDER_TENANT', 'DOCBUILDER_CONTEXT_FILE'],
> 'docbuilder/agents/docbuilder_context_orchestrator.exs':
>   ['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST'],
> ```
>
> **Touches:** `src/components/modules/settings/agentConfigDefs.ts`,
> `src/components/modules/orchestrator/OrchestratorView.tsx`,
> `rig/docs/milestones/p9/t2-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `rig/docs/milestones/p9/README.md §t2` and include
> its full output at the top of the review packet, before the diff.

---

### t3 — `chain_docbuilder.py` (top-level chained run, emits the orchestrator protocol)

**Scope.** Chain the two-step docbuilder flow: run `context_builder.exs` →
`confirmed_context.json`, then `docbuilder_orchestrator.exs` consuming it. A new
Python script `chain_docbuilder.py` does the sequencing + env plumbing. **Rig runs
it as the top-level process** (no wrapping Aetheris agent) and it **emits the
orchestrator newline-JSON protocol** so the Docbuilder panel drives the phase
lifecycle natively.

**Design — corrected twice (no `sh -c`, no nesting).**
1. `run_command` can't help: the exec-server allowlist
   (`native/aetheris_exec_server/src/runner.rs`) rejects `sh`/`bash`, and
   `run_command` has no `env` field. So per-step env can't be set via a tool call.
2. A wrapping agent doesn't work either: a **nested `mix aetheris run`** (inside an
   outer agent run) fails — the inner run's `compile.aetheris_worker` step does an
   unconditional `File.copy!` of the worker binary the outer run holds open →
   `ETXTBSY` ("text file busy"); there is no `--no-compile`/skip escape. Verified
   empirically (run `docbuilder-ctx-orch-WRNyiQ`/`lsjxug`).
   **Therefore the chain must run top-level, not inside an agent.** Run top-level,
   the two `mix aetheris run` children are sequential — each worker exits and frees
   the binary before the next (exactly like the working `docbuilder_context` sprint).
3. So **Rig runs `chain_docbuilder.py` directly** (not `mix aetheris run <exs>`).
   `orchestrate_start` gets a one-line heuristic (t4): a `script_path` ending in
   `.py` is spawned as `python3 <path>` instead of `mix run <path>`. The script
   speaks the orchestrator protocol on stdout, so it's a drop-in for the existing
   `orchestrate_start`/`_poll` plumbing and the phase-lifecycle UI.

There is **no `docbuilder_context_orchestrator.exs`** — the wrapping agent is dropped.

**`chain_docbuilder.py` contract.**
- Args: `--tenant`, `--request`, `--aetheris-dir` (aetheris mix project, `cwd`),
  `--agents-dir` (aetheris-agents repo root), `--protocol` (emit the orchestrator
  newline-JSON protocol; without it, print a single JSON summary — for CLI/tests).
- Step 1: `subprocess.run(['mix','aetheris','run', '<agents>/docbuilder/agents/context_builder.exs'],
  env={**os.environ, 'DOCBUILDER_TENANT': tenant, 'DOCBUILDER_REQUEST': request}, cwd=aetheris_dir)`.
- Verify `<agents>/docbuilder/output/confirmed_context.json` exists + valid JSON; fail
  the step otherwise (do not run the orchestrator).
- Step 2: `subprocess.run(['mix','aetheris','run', '<agents>/docbuilder/agents/docbuilder_orchestrator.exs'],
  env={**os.environ, 'DOCBUILDER_TENANT': tenant, 'DOCBUILDER_CONTEXT_FILE': '<abs confirmed_context.json>'},
  cwd=aetheris_dir)` — **remove `DOCBUILDER_CONTEXT`** from that env (orchestrator
  precedence is env > file; a stray var would shadow the file).
- Sub-run output captured (not streamed).
- **`--protocol` mode** emits one JSON object per line, matching `useOrchestrator`:
  - `{"type":"plan","request":…,"params":{…},"steps":[{id,description,agent,context}×2]}`
    — step `agent` values are `docbuilder/agents/context_builder.exs` and
    `docbuilder/agents/docbuilder_orchestrator.exs` (the `STEP_CONFIG_HINTS` keys from t2).
  - `{"type":"step_started","step_id":…}` / `{"type":"step_complete","step_id":…,"status":"done"|"failed","error":…}` around each sub-run.
  - `{"type":"orchestration_complete"}` at the end (always — a failed step shows via its `step_complete`).
  - One-click: no approval gate (the script does not wait on stdin). If a gate is wanted later it's a t4 addition.
- **Default (no `--protocol`)** prints `{status, context_builder_exit, orchestrator_exit, confirmed_context_path, outputs}` and exits 0 only when both sub-runs succeed.

**Contract refs.**
- `agent-creation-guide.md` §"Core principle: scripts do, agents decide"
- exec-server allowlist: `native/aetheris_exec_server/src/runner.rs`
- worker-copy `ETXTBSY`: `aetheris/lib/mix/tasks/compile/aetheris_worker.ex` (unconditional `File.copy!`)
- orchestrator protocol consumer: `rig/src/hooks/useOrchestrator.ts` (`plan`/`step_started`/`step_complete`/`orchestration_complete`)
- m3-milestone §Design decisions — orchestrator context source precedence

**Touches.**
- `docbuilder/scripts/chain_docbuilder.py` — new (sequencing + env + protocol)
- `docbuilder/tests/test_chain_docbuilder.py` — new (mock `subprocess.run`; covers summary + protocol modes)
- `rig/src/components/modules/orchestrator/OrchestratorView.tsx` — remove the dead
  `docbuilder_context_orchestrator.exs` `STEP_CONFIG_HINTS` entry (that agent is dropped)
- `docbuilder/docs/milestones/p9-t3-implementation-notes.md` — new

**Do not generate.**
- Do not modify `context_builder.exs` or `docbuilder_orchestrator.exs`
- Do not modify sprint.sh (the `docbuilder_context` shell case is unchanged)
- Do not add the Rust `.py` heuristic here — that lands in t4 (`orchestrate_start`)
- Do not add a `docbuilder_context_orchestrator.exs` agent — the wrapping agent is dropped

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents

# Unit tests (mock subprocess) — summary mode + protocol-mode emission
python3 -m pytest docbuilder/tests/test_chain_docbuilder.py -v   # all pass

# Full docbuilder suite — no regression
python3 -m pytest docbuilder/tests/ -q                           # 292 + chain tests, 3 skipped

# Top-level end-to-end (NON-nested — this is the fix): reset run_log to the May seed, then
cd ~/sandbox/elixirws/aetheris
python3 ../aetheris-agents/docbuilder/scripts/chain_docbuilder.py \
  --tenant bitloka --request "Invoice for XYZ for June 2026, same as last month" \
  --aetheris-dir "$PWD" --agents-dir "$PWD/../aetheris-agents" --protocol
# Expected: plan + step events + orchestration_complete on stdout; exit 0;
# docbuilder/output/confirmed_context.json (June) + xyz_inc_invoice_30-Jun-2026.{xlsx,docx,pdf} written
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) and `agent-creation-guide.md` in full first.
> Then implement t3 per §t3 above (note: corrected design — no wrapping agent; Rig runs
> the script top-level; the script emits the orchestrator protocol).
>
> **`chain_docbuilder.py`** — importable `chain(tenant, request, aetheris_dir, agents_dir,
> on_event=None)` running the two sub-agents (step events via `on_event`); `build_plan(...)`;
> `main()` with `--protocol` (emit plan → step events → orchestration_complete; one-click,
> no stdin gate) vs default (print JSON summary). Step 2 env removes `DOCBUILDER_CONTEXT`.
> Protocol messages must match `useOrchestrator.ts`.
>
> **`test_chain_docbuilder.py`** — mock `subprocess.run`: both succeed; context builder
> fails (no step 2); confirmed-context missing/invalid (no step 2); orchestrator fails; env
> construction (step1 TENANT+REQUEST; step2 TENANT+CONTEXT_FILE and NOT DOCBUILDER_CONTEXT;
> cwd); `build_plan` shape (2 steps, correct agent paths); on_event emits the right sequence.
>
> **`OrchestratorView.tsx`** — remove the `docbuilder_context_orchestrator.exs`
> `STEP_CONFIG_HINTS` entry (dropped agent).
>
> **Touches:** `docbuilder/scripts/chain_docbuilder.py`,
> `docbuilder/tests/test_chain_docbuilder.py`,
> `rig/src/components/modules/orchestrator/OrchestratorView.tsx`,
> `docbuilder/docs/milestones/p9-t3-implementation-notes.md`.
> **Do not generate** anything outside Touches.
>
> Run the done-check from §t3 and put its full output at the top of the review packet.

---

### t4 — Docbuilder panel

**Scope.** A new Rig module (`docbuilder`) with a single route `/docbuilder`
and a sidebar entry. The panel has a request text field (maps to both
`ORCHESTRATOR_REQUEST` and `DOCBUILDER_REQUEST`), reads `DOCBUILDER_TENANT`
from stored config, and on submit runs `docbuilder/scripts/chain_docbuilder.py`
(top-level, via the `.py` heuristic in `orchestrate_start`) with `DOCBUILDER_REQUEST` as a per-run
env var. Shows the standard Orchestrator phase lifecycle (planning →
plan_ready → executing → done) and, on completion, lists the rendered output
files read from `docbuilder/output/renamed.json`.

**Contract refs.**
- `rig/CLAUDE.md` §"Module registration" — new modules need entries in
  `registry.ts`, a route in `App.tsx`, and a hook export from `index.ts`
- Agent config architecture reference — `DOCBUILDER_TENANT` is already in
  `agent_config` after t2; it is injected automatically; the panel reads it
  via `useAgentConfig` to display the current tenant
- Current-state doc §"Adding a new module" — 8-step checklist
- `tools_read_script` (`commands/tools.rs`) — reads any file under
  `AETHERIS_AGENTS_PATH`; the panel uses it for `renamed.json` (no new command)

**Prerequisite (found in t1; extended in t3 — `orchestrate_start` hardcodes
`mix aetheris run {agents_path}/agents/orchestrator.exs`).** To run the docbuilder
chain, t4 must thread a script path through `orchestrate_start` **and** add the `.py`
heuristic so the chain script runs top-level (t3's required design — it cannot be a
nested agent):
- `rig/src-tauri/src/commands/orchestrate.rs` — add `script_path: Option<String>` to
  `orchestrate_start`; when `None`, default to `agents/orchestrator.exs` (existing callers
  unaffected). **When `script_path` ends in `.py`, spawn `python3 <path>` (with the chain
  script's args + `--protocol`); otherwise spawn `mix aetheris run <path>`** (one heuristic,
  no new fields). The `.py` branch runs `chain_docbuilder.py` top-level — non-nested.
- `rig/src/hooks/useOrchestrator.ts` — add `scriptPath?: string` to `start`; pass it
  through to `invoke` (camelCase `scriptPath`).
- The Docbuilder panel's `scriptPath` is `docbuilder/scripts/chain_docbuilder.py`
  (NOT a `.exs` agent — the wrapping agent was dropped in t3).

**Touches.**
- `rig/src-tauri/src/commands/orchestrate.rs` — `script_path: Option<String>` param (prerequisite above)
- `rig/src/hooks/useOrchestrator.ts` — `scriptPath?` on `start` (prerequisite above)
- `rig/src/components/modules/docbuilder/DocbuilderView.tsx` — new; the panel
- `rig/src/hooks/useDocbuilder.ts` — new; thin wrapper over `useOrchestrator`
  with docbuilder-specific defaults
- `rig/src/hooks/index.ts` — export `useDocbuilder`
- `rig/src/hooks/types.ts` — add `DocbuilderState` type if needed
- `rig/src/modules/registry.ts` — register `docbuilderModule`
- `rig/src/App.tsx` — add `/docbuilder` route
- `rig/docs/milestones/p9/t4-implementation-notes.md` — new

**Do not generate.**
- Do not add **new** Rust commands — extending `orchestrate_start` with a
  `script_path` param is in scope (prerequisite above); the panel otherwise uses
  `orchestrate_start` from t1 and the existing `tools_read_script` for `renamed.json`
- Do not change the stdin/stdout orchestration protocol or polling
- Do not add a new `agentConfigDefs.ts` entry — `DOCBUILDER_TENANT` was
  added in t2

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/rig

bun run tsc --noEmit

grep -n "docbuilder\|Docbuilder" src/modules/registry.ts
# Expected: docbuilderModule entry

grep -n "/docbuilder" src/App.tsx
# Expected: route entry

grep -n "tools_read_script\|renamed.json" src/hooks/useDocbuilder.ts \
  src/components/modules/docbuilder/DocbuilderView.tsx
# Expected: renamed.json read via tools_read_script

cargo tauri dev
# Smoke:
# 1. Sidebar shows "Docbuilder" entry
# 2. Panel shows request field + tenant from stored config
# 3. Submit runs docbuilder_context_orchestrator.exs
# 4. Phase lifecycle renders (planning → plan_ready → executing → done)
# 5. On done: rendered file list shown (from renamed.json)
```

**Claude-code prompt.**
> Read `rig/CLAUDE.md` in full before writing any code. Then implement t4
> of `rig/docs/milestones/p9/README.md`. Follow the "Adding a new module"
> checklist in `rig/docs/runbook.md` (current-state doc §"Adding a new
> module").
>
> **Prerequisite — do this first.** `orchestrate_start` hardcodes
> `agents/orchestrator.exs` (found in t1). Before adding the panel, add
> `script_path: Option<String>` to `orchestrate_start` (default
> `agents/orchestrator.exs` when `None`, so existing callers are unaffected) and
> thread `scriptPath?: string` through `useOrchestrator.start` (camelCase
> `scriptPath` in the `invoke` args). This is required to run any agent other than
> the hardcoded orchestrator.
>
> **Scope:** a new Docbuilder module at `/docbuilder`.
>
> **`DocbuilderView.tsx`:** a single-panel view with:
> - A "Request" textarea (placeholder: "Invoice for XYZ for June 2026,
>   same as last month") — this is `ORCHESTRATOR_REQUEST`
> - A read-only "Tenant" display showing `DOCBUILDER_TENANT` from stored
>   config (via `useAgentConfig`) with a link to Settings if unset
> - A "Run" button (disabled when request is empty or a run is in progress)
> - The standard Orchestrator phase lifecycle (reuse the phase display from
>   `OrchestratorView.tsx` or extract a shared component)
> - On `done`: read `docbuilder/output/renamed.json` via
>   `invoke('tools_read_script', { useCase: 'docbuilder', file: 'output/renamed.json' })`,
>   parse the `[{original, renamed}]` array, and display the rendered file
>   list (basenames of `renamed`). If the read fails or the file is absent,
>   show a generic "Run complete" message — do not error the panel.
>
> **`useDocbuilder.ts`:** wraps `useOrchestrator`. On submit:
> - Sets `ORCHESTRATOR_REQUEST` = the request text
> - Calls `orchestratorStart` with:
>   - `scriptPath`: `docbuilder/scripts/chain_docbuilder.py` (the `.py` heuristic runs it top-level)
>     (relative to `AETHERIS_AGENTS_PATH`)
>   - `request`: the request text
>   - `extraEnv`: `{ DOCBUILDER_REQUEST: requestText }` (per-run; tenant
>     comes from stored config and is injected automatically)
>
> **Module registration** (follow the 8-step checklist):
> - `registry.ts`: add `docbuilderModule` with sidebar label "Docbuilder",
>   route `/docbuilder`, appropriate icon
> - `App.tsx`: add `<Route path="/docbuilder" element={<DocbuilderView />} />`
> - `hooks/index.ts`: export `useDocbuilder`
>
> **Styling:** Tailwind utility classes only. Keep the panel simple —
> single column, consistent with the Orchestrator and Playground panels.
>
> **Touches:** `src/components/modules/docbuilder/DocbuilderView.tsx`,
> `src/hooks/useDocbuilder.ts`, `src/hooks/index.ts`, `src/hooks/types.ts`
> (if needed), `src/modules/registry.ts`, `src/App.tsx`,
> `rig/docs/milestones/p9/t4-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `rig/docs/milestones/p9/README.md §t4` and include
> its full output at the top of the review packet, before the diff.

---

### t5 — Docs sync + drift check + milestone close

**Scope.** Bring `specs.md` and `runbook.md` in sync with t1–t4. Update the
capability matrix for the new agent. Run the drift check. Write the milestone
summary and CLAUDE.md learning scan.

**Contract refs.**
- `rig/CLAUDE.md` §"Doc sync"
- Milestone methodology §7 — milestone-end ritual

**Touches.**
- `rig/docs/specs.md` — add `extra_env` to `orchestrate_start`; add
  `DOCBUILDER_TENANT` to env var table (§1); add `DocbuilderState` to
  TypeScript interfaces (§5) if introduced in t4; add Docbuilder module to
  module structure (§8)
- `rig/docs/runbook.md` — add Docbuilder panel section (how to use the
  panel, what `DOCBUILDER_TENANT` to set, what the plan view shows, how to
  inspect the sub-runs)
- `docs/capability-matrix.md` — add `chain_docbuilder.py` to the docbuilder
  **scripts** section (→ 2 agents / 21 scripts; total 25 / 59). No new agent —
  the wrapping `.exs` was dropped in t3.
- `rig/docs/milestones/p9/README.md` — milestone summary appended
- `aetheris-agents/CLAUDE.md` — `## Learning — rig-p9` (recurring findings
  from t1–t4 reviews, or "No recurring findings" if none)
- `rig/docs/milestones/p9/t5-implementation-notes.md` — new

**Do not generate.**
- Do not modify any Rust or TypeScript source files

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents

python3 scripts/drift_check.py
# Expected: 0 FAIL (WARNs for project_knowledge = BL-002, human-owned)

grep -n "extra_env\|DOCBUILDER_TENANT" rig/docs/specs.md
grep -n "Docbuilder\|docbuilder_context_orchestrator" rig/docs/runbook.md
grep -n "docbuilder_context_orchestrator" docs/capability-matrix.md
```

**Claude-code prompt.**
> Read `rig/CLAUDE.md` and `milestone-methodology.md` §7 before writing.
> Then implement t5 of `rig/docs/milestones/p9/README.md`. Docs-only — no
> Rust or TypeScript changes.
>
> 1. `rig/docs/specs.md` — (a) add `extra_env: HashMap<String, String>` to
>    the `orchestrate_start` command description; (b) add `DOCBUILDER_TENANT`
>    to §1 env var table; (c) add `DocbuilderState` type to §5 if t4
>    introduced it; (d) add the Docbuilder module to §8 module structure.
>
> 2. `rig/docs/runbook.md` — add a "Docbuilder panel" section: how to
>    launch the flow from the sidebar, what `DOCBUILDER_TENANT` to configure
>    in Settings, what the plan view shows, how to inspect the context-builder
>    and orchestrator sub-runs separately in the Harness.
>
> 3. `docs/capability-matrix.md` — add
>    `chain_docbuilder.py` to the docbuilder **scripts** section; update the
>    totals (2 agents / 21 scripts; total 25 / 59). No new agent.
>
> 4. Scan `t1–t4-implementation-notes.md` for findings recurring on ≥2
>    tickets. Write `## Learning — rig-p9` in `aetheris-agents/CLAUDE.md`.
>
> 5. Append milestone summary to `rig/docs/milestones/p9/README.md`.
>
> **Touches:** `rig/docs/specs.md`, `rig/docs/runbook.md`,
> `docs/capability-matrix.md`, `rig/docs/milestones/p9/README.md`,
> `aetheris-agents/CLAUDE.md`,
> `rig/docs/milestones/p9/t5-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `rig/docs/milestones/p9/README.md §t5` and include
> its full output at the top of the review packet, before the diff.

---

## Open questions for p10

- The Docbuilder panel currently shows a single request field. A future
  iteration could support amendment: show the `confirmed_context.json` block
  after the context builder completes and allow the operator to edit it
  before the orchestrator runs — the interactive confirm/amend loop deferred
  from m3.
- Once the panel exists, additional doc types (proposals, reports) could be
  surfaced via a doc type selector populated from the tenant catalogue. Worth
  scoping once the invoice flow is stable.
- t3 routes per-step env through `chain_docbuilder.py` because `run_command` has no
  `env` field and the exec-server allowlist blocks `sh`/`bash`. If chained flows become
  common, consider adding an `env` field to the `run_command` tool schema (worker +
  schema change) so a chaining agent could set per-invocation env directly without a
  Python shim.

---

## Milestone summary

_To be written by claude-code at t5. Do not fill in now._
