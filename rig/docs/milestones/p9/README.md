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
3. A thin `docbuilder_context_orchestrator.exs` that chains the two steps
   into one Rig run (t3)
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

- **`run_command` has no `env` field** (verified: `aetheris/lib/aetheris/execution/
  tool_schema/registry.ex` — the schema is `command` / `args` / `working_dir` /
  `timeout_ms` only). t3 **must** use a `sh -c` wrapper to set per-invocation env vars;
  there is no env-passing form. The wrapper also has to `cd` into the **aetheris** repo
  (where `mix aetheris run` works) and reference the agents via `../aetheris-agents/…`.
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
| Chained execution approach | `docbuilder_context_orchestrator.exs` — a new thin Elixir agent that runs the context builder then the orchestrator as two sequential Aetheris runs via `run_command` on `mix aetheris run` | Keeps Rust side unchanged; each run has its own trajectory; no new `OrchestratorJob` sequencing in Rig |
| Per-invocation env in the chained agent | `sh -c` wrapper around `mix aetheris run` (run_command has no `env` field — verified) | The only way to set per-step env vars; step 2 also `env -u DOCBUILDER_CONTEXT` so the file is read |
| Docbuilder panel | New module (`docbuilder`) with a single route `/docbuilder` — tenant (from stored config), request field, Run button, output file list | Thin React wrapper over `orchestratorStart`; reuses `useOrchestrator` |
| Panel output file list | Read `docbuilder/output/renamed.json` via the existing `tools_read_script` command (no new Tauri command) | `tools_read_script` already reads any path under `AETHERIS_AGENTS_PATH` |
| `STEP_CONFIG_HINTS` entries | `context_builder.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']`; `docbuilder_orchestrator.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_CONTEXT_FILE']`; `docbuilder_context_orchestrator.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']` | Surfaces the vars the operator needs to verify before approving |

---

## Ticket structure

| Ticket | Title | Key artifacts |
|---|---|---|
| t1 | `orchestrate_start` per-run env vars — Rust + TypeScript | `commands/orchestrate.rs`, `useOrchestrator.ts`, `OrchestratorView.tsx` |
| t2 | Docbuilder config entries + `STEP_CONFIG_HINTS` | `agentConfigDefs.ts`, `OrchestratorView.tsx` |
| t3 | `docbuilder_context_orchestrator.exs` — chained context builder → orchestrator | `docbuilder/agents/docbuilder_context_orchestrator.exs` |
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

### t3 — `docbuilder_context_orchestrator.exs` (chained run)

**Scope.** A new thin Elixir agent that sequences the two-step docbuilder
flow as a single Aetheris run: runs `context_builder.exs` to produce
`confirmed_context.json`, then runs `docbuilder_orchestrator.exs` consuming
it, all without the operator switching between scripts.

**Design.** The agent uses `run_command` to invoke `mix aetheris run` for
each sub-agent (not `spawn_agent` — these are sequential, not parallel).
`mix aetheris run` on each `.exs` file records a trajectory in `aetheris.db`
under its own `run_id`, so both runs are inspectable separately. The outer
agent's job is purely sequencing and reporting: run the builder, verify
`confirmed_context.json` was written, set `DOCBUILDER_CONTEXT_FILE`, run
the orchestrator, report the rendered output files.

**`run_command` has no `env` field (verified — see Pre-implementation
verification).** The agent therefore wraps each `mix aetheris run` in a
`sh -c` command that sets the per-step env vars and `cd`s into the aetheris
repo. Step 2 also `env -u DOCBUILDER_CONTEXT` so the orchestrator reads the
confirmed-context file rather than a stray env var.

**Contract refs.**
- `agent-creation-guide.md` §"Core principle: scripts do, agents decide"
- `agent-creation-guide.md` §"Standard RunConfig fields"
- `agent-creation-guide.md` §"Be explicit about run_command format"
- `agent-creation-guide.md` §"Env vars and worker lifetime"
- m3-milestone §Design decisions — `DOCBUILDER_CONTEXT_FILE` takes
  precedence over the default file path; `DOCBUILDER_CONTEXT` must be unset
  (or not set) for the orchestrator to read the file

**Touches.**
- `docbuilder/agents/docbuilder_context_orchestrator.exs` — new
- `docbuilder/docs/milestones/p9-t3-implementation-notes.md` — new

**Do not generate.**
- Do not modify `context_builder.exs` or `docbuilder_orchestrator.exs`
- Do not modify the sprint.sh — the existing `docbuilder_context` case is
  unchanged; this agent is the Rig-facing entry point only
- Do not add Python scripts or tests — the agent delegates all logic to the
  existing agents; there is no new script logic to test here
- Do not add a sprint case for this agent — the existing `docbuilder_context`
  sprint case remains the CLI entry point

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents

# Eval check (no LLM)
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Invoice for XYZ for June 2026, same as last month" \
mix run --eval \
  'Code.eval_file("docbuilder/agents/docbuilder_context_orchestrator.exs")' \
  2>/dev/null
# Expected: EXIT 0

# Verify the RunConfig struct
DOCBUILDER_TENANT=bitloka DOCBUILDER_REQUEST="test" \
mix run --no-start --eval '
  {config, _} = Code.eval_file(
    "docbuilder/agents/docbuilder_context_orchestrator.exs")
  IO.inspect(config.tools, label: "tools")
  IO.inspect(config.model, label: "model")
  IO.inspect(String.length(config.system_prompt) > 100,
    label: "system_prompt_present")
'
# Expected: tools contains "run_command"; model is haiku; system_prompt_present true

# Full docbuilder suite — no regression
python3 -m pytest docbuilder/tests/ -v --tb=short
# Expected: 292 passed, 3 skipped (unchanged)
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) and `agent-creation-guide.md` in
> full before writing any code. Then implement t3 of
> `rig/docs/milestones/p9/README.md`.
>
> **Scope:** create `docbuilder/agents/docbuilder_context_orchestrator.exs`
> — a thin sequencing agent that chains the context builder → orchestrator
> into a single Aetheris run.
>
> **Agent behaviour:**
> - Reads `DOCBUILDER_TENANT` (raise if absent) and `DOCBUILDER_REQUEST`
>   (raise if absent) at eval time.
> - `tools: ["run_command", "read_file"]`
> - `model: "claude-haiku-4-5-20251001"`, `max_steps: 10`,
>   `context_strategy: :full`, `overlay_base_dir: nil`
> - System prompt workflow (two steps). **`run_command` has NO `env` field
>   (verified against the tool schema), so use a `sh -c` wrapper** that sets
>   the per-step env vars and `cd`s into the aetheris mix project:
>
>   Step 1 — run the context builder:
>   ```
>   run_command  command: "sh"
>                args: ["-c",
>                  "cd ../../aetheris && DOCBUILDER_TENANT='<tenant>' \
>                   DOCBUILDER_REQUEST='<request>' \
>                   mix aetheris run ../aetheris-agents/docbuilder/agents/context_builder.exs"]
>   ```
>   (Resolve the correct relative path to the aetheris repo + agent from the
>   outer agent's sandbox; confirm with a `pwd`/`ls` probe if unsure.)
>   Wait for it to complete. Then read_file
>   `docbuilder/output/confirmed_context.json` to verify it exists and is
>   valid JSON. If absent or invalid, report the error and stop.
>
>   Step 2 — run the orchestrator (unset DOCBUILDER_CONTEXT so the file wins):
>   ```
>   run_command  command: "sh"
>                args: ["-c",
>                  "cd ../../aetheris && env -u DOCBUILDER_CONTEXT \
>                   DOCBUILDER_TENANT='<tenant>' \
>                   DOCBUILDER_CONTEXT_FILE='<abs path to confirmed_context.json>' \
>                   mix aetheris run ../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs"]
>   ```
>   Wait for it to complete. Report the rendered output files.
>
> - Interpolate `tenant` and `request` from the eval-time env vars into the
>   system prompt as named variables (same pattern as `context_builder.exs`),
>   not inline `System.get_env` in the struct. Single-quote-escape the request
>   when embedding it into the `sh -c` string.
> - `user_prompt`: "Run the docbuilder context flow for: #{request}"
>
> **Document in the implementation notes** the exact wrapper form used and the
> working-directory resolution (the outer sandbox vs the aetheris mix project).
>
> **Touches:** `docbuilder/agents/docbuilder_context_orchestrator.exs`,
> `docbuilder/docs/milestones/p9-t3-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `rig/docs/milestones/p9/README.md §t3` and include
> its full output at the top of the review packet, before the diff.

---

### t4 — Docbuilder panel

**Scope.** A new Rig module (`docbuilder`) with a single route `/docbuilder`
and a sidebar entry. The panel has a request text field (maps to both
`ORCHESTRATOR_REQUEST` and `DOCBUILDER_REQUEST`), reads `DOCBUILDER_TENANT`
from stored config, and on submit runs `docbuilder_context_orchestrator.exs`
via `orchestratorStart` (from t1) with `DOCBUILDER_REQUEST` as a per-run
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

**Prerequisite (found in t1 — `orchestrate_start` hardcodes the script path).**
`orchestrate_start` currently runs a hardcoded `{agents_path}/agents/orchestrator.exs`,
and `useOrchestrator.start` takes no script path. To run
`docbuilder_context_orchestrator.exs`, t4 must first thread a script path through both:
- `rig/src-tauri/src/commands/orchestrate.rs` — add `script_path: Option<String>` to
  `orchestrate_start`; when `None`, default to the existing `agents/orchestrator.exs`
  (so every current caller is unaffected). Build the command path from it.
- `rig/src/hooks/useOrchestrator.ts` — add `scriptPath?: string` to `start`; pass it
  through to `invoke` (camelCase `scriptPath`).

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
>   - `scriptPath`: `docbuilder/agents/docbuilder_context_orchestrator.exs`
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
- `docs/capability-matrix.md` — add `docbuilder_context_orchestrator.exs`
  to the docbuilder agents section (→ 3 agents; total 26 / 58)
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
>    `docbuilder_context_orchestrator.exs` to the docbuilder agents section;
>    update the totals (3 agents, total 26 / 58).
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
- If the `sh -c` wrapper in t3 proves fragile (quoting, working-dir), consider
  adding an `env` field to the `run_command` tool schema in Aetheris (worker +
  schema change) so chained agents can pass per-invocation env directly.

---

## Milestone summary

_To be written by claude-code at t5. Do not fill in now._
