# Rig — Current State (2026-06)

_Reconstructed from code on 2026-06-11. Supersedes any prior handoff doc.
All evidence cited as file:line. "Documented" means the milestone spec or
specs.md made a specific claim. "DIVERGED" means the feature exists but
differs from the spec._

---

## 1. Milestone Status

### P1 — Consolidation + Run Inspection

**IMPLEMENTED**

- `commands/harness.rs` — 208 lines, all 4 commands present:
  - `harness_connection_status` (line 28) — returns `Ok(HarnessStatus{connected:false})` when DB absent; never returns `Err`
  - `harness_list_runs` (line 68)
  - `harness_get_events` (line 131)
  - `harness_get_run` (line 178)
- DB opened read-only: `lib.rs:141-144` uses `SQLITE_OPEN_READ_ONLY | SQLITE_OPEN_NO_MUTEX`
- `components/modules/harness/RunList.tsx` — 458 lines; Runs + Events tabs present
- Types match specs.md: `HarnessStatus`, `RunSummary`, `EventRow`, `RunDetail` in `types.ts:151-193`

---

### P2 — Live Monitoring

**IMPLEMENTED** (auto-scroll lives in RunList.tsx, not useHarness.ts)

- `useHarness.ts` — 130 lines
  - `useRunEvents` function: line 46
  - Polling interval: 2000ms (`line 94`)
  - Stop condition: `ev.event_type === 'run_complete'` (`line 87`)
  - 5 `useEffect` hooks (not 3 as some docs describe); effects handle: initial fetch, polling intent sync, stop-on-complete detection, polling interval, local status sync
- Auto-scroll threshold: `RunList.tsx:308` — `scrollHeight - scrollTop - clientHeight < 50`; scroll fires when user is within 50px of bottom
- Local status badge: `RunList.tsx:312-313` — `isComplete` derived from events, `displayStatus` set to `'done'` when `run_complete` seen (independent of `runs.status`)

---

### P3 — Orchestrator (NL → plan → execute)

**IMPLEMENTED**

The P3 README was marked "docs-only / future milestone" as of 2026-05-31.
All P3 components now exist in code:

- `commands/orchestrate.rs` — 125 lines; 4 commands: `orchestrate_start` (line 8), `orchestrate_poll` (line 82), `orchestrate_approve` (line 96), `orchestrate_cancel` (line 115)
- `lib.rs:21-26` — `OrchestratorJob` struct (child, stdin, buffer, done)
- `lib.rs:33-37` — `OrchestratorState` struct (jobs, agents_path, aetheris_dir)
- `hooks/useOrchestrator.ts` — 119 lines; full state machine
- `components/modules/orchestrator/OrchestratorView.tsx` — 311 lines; all 7 phases: idle, planning, plan_ready, executing, done, cancelled, error
- `agents/mock_orchestrator.exs` — kept for regression testing
- P3 TypeScript types all in `types.ts:256-284`; **two additions vs protocol.md**:
  - `PlanStep.context?: string` (line 260) — not in protocol.md
  - `OrchestratorPlan.params?: Record<string, string>` (line 267) — not in protocol.md
- `STEP_CONFIG_HINTS` in `OrchestratorView.tsx:13-31` — maps agent paths to env var checklists

---

### P4 — Trajectory Explorer + Run Diff

**IMPLEMENTED**

- `commands/trajectory.rs` — 91 lines; `trajectory_load` (line 35), `trajectory_export` (line 70)
- `components/modules/harness/TrajectoryView.tsx` — exists; meta panel + step-grouped events
- `components/modules/harness/DiffView.tsx` — exists; run picker + metadata/step diff
- `hooks/useTrajectory.ts` — 23 lines
- `hooks/useRunDiff.ts` — 144 lines; client-side `computeDiff`
- Types: `TrajectoryMeta`, `TrajectoryEvent`, `TrajectoryFile`, `MetaDiffRow`, `StepDiffEntry`, `RunDiff` — `types.ts:193-251`

---

### P4-tools — Tools Browser (scripts + MCP)

**IMPLEMENTED** (MCP beyond original spec scope)

- `commands/tools.rs` — 738 lines; 5 commands:
  - `tools_list_inventory` — walks `tools.json` manifests + undeclared `.py` files
  - `tools_read_script` — returns source of a Python script
  - `tools_run_script` — executes a script, streams output
  - `tools_list_mcp` — discovers MCP servers from `mcp/mcp_servers.json`, probes via stdio
  - `tools_call_mcp` — invokes a single MCP tool (Try panel)
- `components/modules/tools/ToolsView.tsx` — wrapper (491B)
- `components/modules/tools/ToolTree.tsx` — left-panel tree; use-case scripts + undeclared badge + Harness section + MCP section
- `components/modules/tools/ToolDetail.tsx` — 15KB right panel; arg form, example command, Run button, MCP try panel
- `hooks/useTools.ts` — 77 lines
- Types: `ManifestArg`, `ManifestScript`, `UseCaseGroup`, `HarnessToolArg`, `HarnessTool`, `McpTool`, `McpServerGroup`, `ToolsInventory`, `ScriptResult`, `McpCallResult`, `SelectedTool` — `types.ts:370-458`
- `ToolsState` in `lib.rs:39-41` — holds `agents_path`
- Module registered in `registry.ts` as `toolsModule` with route `/tools`

---

### P5 — Run Grouping + Capability Matrix

**IMPLEMENTED**

- `RunList.tsx` — grouping by use-case prefix (search "group" in file for `groupRuns` function)
- `commands/capability_matrix.rs` — `capability_matrix_load` (line 30); parses `docs/capability-matrix.md`
- `components/modules/harness/CapabilityMatrixView.tsx` — 6.6KB; collapsible use-case sections, agent rows with Run button, script rows, navigation to `/orchestrator` with prefill
- Types: `MatrixAgent`, `MatrixScript`, `MatrixUseCase`, `CapabilityMatrix` — `types.ts` (lines around 290-311)
- Harness sidebar has 4 sections: Runs, Diff, **Agents** (capability matrix), **Usage** — `registry.ts`

---

### P6 — Token/Cost Surface

**IMPLEMENTED**

- `commands/usage.rs` — 197 lines; `usage_stats_load` aggregates from `events` table via SQLite `json_extract`
  - Reads `cost_usd` from `llm_responded` events (line 45: `WHERE type = 'llm_responded'`)
  - Reads `input_tokens`, `output_tokens` (lines 69-74)
  - Computes per-run average in Rust, not SQL (line 87-88)
  - Filters `json_extract(payload_json, '$.cost_usd') IS NOT NULL` to exclude pre-instrumentation rows
- `components/modules/harness/UsageView.tsx` — 7KB; 4 summary cards + by-model table + by-use-case table
- `hooks/useUsageStats.ts` — 21 lines
- `TokenSummary` computed client-side in `TrajectoryView.tsx` from trajectory events
- Types: `TokenSummary`, `ModelUsageRow`, `UseCaseUsageRow`, `UsageStats` — `types.ts`
- **Note:** `cost_usd` is in harness event payloads (`execution/loop.ex:251,281`) but NOT documented in specs.md section 6

---

### P7 — Agent Config + Settings

**IMPLEMENTED + ENHANCED**

P7 specified 3 commands (`get_all`, `set`, `delete`). Code has 5:

- `commands/agent_config.rs` — 5 commands at lines 14, 21, 31, 40, 49:
  - `agent_config_get_all`, `agent_config_set`, `agent_config_delete` — as specified
  - `agent_config_export` — returns serialized JSON String (no path arg; caller handles persistence)
  - `agent_config_import` — takes `HashMap<String,String>`, returns `usize` count imported
- `AgentConfigState` in `lib.rs:28-31` — `store_path` + `cache: Mutex<HashMap<String,String>>`
- Store location: `~/.local/share/dev.rig.app/agent-config.json`
- `components/modules/settings/AgentConfigTab.tsx` — 7.8KB; grouped by category, masked fields
- `components/modules/settings/agentConfigDefs.ts` — 52 lines; hardcoded key definitions
  - Groups: Harness, Anthropic, SMTP, Google Drive, **Payslip**, GitHub (runbook.md lists all but Payslip)
- `hooks/useAgentConfig.ts` — 53 lines
- `hooks/useRequestHistory.ts` — 25 lines; localStorage MRU list for orchestrator requests
- All config values injected as env vars at orchestrator spawn: `orchestrate.rs:30-32`
- `AgentConfigEntry` (`types.ts:372`) is TypeScript-only — assembled by `useAgentConfig.ts` from
  `agentConfigDefs.ts` (hardcoded metadata) merged with the `HashMap<String,String>` returned by
  `agent_config_get_all`; no corresponding Rust struct exists

---

### P8 — Orchestrator Reliability + Drive Split

**IMPLEMENTED**

- `STEP_CONFIG_HINTS` in `OrchestratorView.tsx:13-31` — per-agent env var checklist shown in plan view; includes `payslip/agents/payslip_pipeline.exs` entry
- `stepErrors` and `stepStatuses` tracked in `useOrchestrator.ts`; failed steps show error message with Drive ID linkification
- Cancel: `orchestrate_cancel` at `orchestrate.rs:115` kills child process with `job.child.lock().unwrap().kill()`
- Drive agent split: `drive/agents/drive_download_orchestrator.exs`, `drive/agents/drive_upload_orchestrator.exs`, `drive/agents/drive_orchestrator.exs` all present (separate agents for download vs upload)

---

### orchestrator — Real Orchestrator Agent Spec

**IMPLEMENTED** — and the Rig switch has been made

The spec (`docs/rig/milestones/orchestrator/orchestrator-agent-spec.md`) describes creating `agents/orchestrator.exs` and updating `orchestrate.rs` to spawn it instead of the mock.

**Both have been done:**

- `agents/orchestrator.exs` — exists; full LLM-driven orchestrator using Anthropic API directly (`Req.post!` to `https://api.anthropic.com/v1/messages`), reads capability matrix, emits plan JSON, blocks for approval, executes steps via `RunHelpers.load_agent_file` + `Aetheris.start_run` + `RunHelpers.await_run`
- `orchestrate.rs:18` — spawns `agents/orchestrator.exs`, NOT `agents/mock_orchestrator.exs`

The spec noted: _"In orchestrate.rs... Currently (mock): mock_orchestrator.exs / Change to (real): orchestrator.exs"_ — this change is in place.

`agents/mock_orchestrator.exs` remains for regression testing.

---

## 2. Undocumented Features

Code present in `rig/` with no corresponding milestone doc:

| Feature | Evidence | Notes |
|---------|----------|-------|
| `agent_config_export` + `agent_config_import` | `agent_config.rs:40,49`; `lib.rs:74-75` | Config portability beyond P7 spec |
| `tools_call_mcp` (Try panel) | `tools.rs:676`; `lib.rs:87` | Beyond P4-tools phase breakdown |
| MCP types (`McpTool`, `McpServerGroup`, `McpCallResult`) | `types.ts:420-455` | No milestone doc |
| `mcp/mcp_servers.json` server registry | referenced in `runbook.md:151` | Described in runbook but no milestone |
| `payslip/agents/payslip_pipeline.exs` | `OrchestratorView.tsx:20-31` | In STEP_CONFIG_HINTS; no Rig milestone |
| `UsageView` / `usage_stats_load` | `usage.rs`, `registry.ts` sidebar | P6 issued late; architecture.md doesn't mention it |
| Settings route + `SettingsRoute.tsx` | `components/modules/settings/` | No milestone doc for the settings shell |
| `useRequestHistory` MRU | `hooks/useRequestHistory.ts` | No milestone doc |
| `STEP_CONFIG_HINTS` map | `OrchestratorView.tsx:13-31` | P8 work, but the map itself is undocumented |
| `params` field in `OrchestratorPlan` | `types.ts:267`, `OrchestratorView.tsx:201` | Not in protocol.md |
| `context` field in `PlanStep` | `types.ts:260`, `OrchestratorView.tsx:100-102` | Not in protocol.md |

---

## 3. Current Module Inventory

From `rig/src/modules/registry.ts`:

| Module | ID | Sidebar sections | Routes |
|--------|----|-----------------|--------|
| Harness | `harness` | Runs (`/harness`), Diff (`/diff`), Agents (`/capability-matrix`), Usage (`/usage`) | 4 |
| Orchestrator | `orchestrator` | Orchestrator (`/orchestrator`) | 1 |
| Tools | `tools` | Tools (`/tools`) | 1 |
| F2 | `f2` | Operations (`/f2/operations`), Viewer (`/f2/viewer`) | 2 |
| Provenance | `provenance` | Dashboard (`/provenance`) | 1 |
| Playground | `playground` | Composer (`/playground`) | 1 |

The sidebar order is: Harness → Orchestrator → Tools → Playground → F2 → Provenance.

`architecture.md` component map is missing: Tools module, Usage section, Agents (capability matrix) section, Settings.

---

## 4. Tauri Command Inventory

47 commands registered in `lib.rs`.

| Module | Commands | Spec said |
|--------|----------|-----------|
| f2 | 9 (`f2_get_watched_folders`, `f2_add_watched_folder`, `f2_toggle_watched_folder`, `f2_remove_watched_folder`, `f2_trigger_scan`, `f2_get_file_index`, `f2_get_file_count`, `f2_get_duplicates`, `f2_get_duplicate_stats`) | pre-existing |
| provenance | 11 (`provenance_corpus_summary`, `_client_breakdown`, `_scan_runs`, `_classification_list`, `_set_classification_status`, `_migration_summary`, `_zip_inventory`, `_duplicate_groups`, `get_system_username`, `_failed_migrations`, `_encrypted_zips`) | pre-existing |
| harness | 4 (`harness_connection_status`, `harness_list_runs`, `harness_get_events`, `harness_get_run`) | P1: 4 ✓ |
| agent_config | 5 (`agent_config_get_all`, `_set`, `_delete`, `_export`, `_import`) | P7: 3 + 2 extra |
| orchestrate | 4 (`orchestrate_start`, `_poll`, `_approve`, `_cancel`) | P3: 4 ✓ |
| trajectory | 2 (`trajectory_load`, `trajectory_export`) | P4: 2 ✓ |
| capability_matrix | 1 (`capability_matrix_load`) | P5: 1 ✓ |
| usage | 1 (`usage_stats_load`) | P6: 1 ✓ |
| tools | 5 (`tools_list_inventory`, `tools_read_script`, `tools_run_script`, `tools_call_mcp`, `tools_list_mcp`) | P4-tools: 4 + 1 extra |
| playground | 5 (`playground_connection_status`, `playground_get_policy`, `playground_get_sandboxes`, `playground_submit_run`, `playground_run_status`) | m-playground-p2: 5 ✓ |

**specs.md section 4** documents harness, trajectory, orchestrator, and playground commands. The agent_config, capability_matrix, usage, and tools command shapes are undocumented there.

---

## 5. Hooks and types.ts

### Hooks (21 files in `rig/src/hooks/`)

| Hook | Lines | Purpose |
|------|-------|---------|
| `useHarness.ts` | 130 | Runs list, events, polling, connection status |
| `useTrajectory.ts` | 23 | Single-run trajectory load |
| `useRunDiff.ts` | 144 | Client-side two-run diff |
| `useOrchestrator.ts` | 119 | Orchestrator state machine |
| `useCapabilityMatrix.ts` | 18 | Matrix load |
| `useUsageStats.ts` | 21 | Usage stats fetch |
| `useAgentConfig.ts` | 53 | Agent config CRUD |
| `useTools.ts` | 77 | Tools inventory + MCP |
| `useRequestHistory.ts` | 25 | Orchestrator MRU (localStorage) |
| `useCorpusOverview.ts` | 57 | Provenance corpus summary |
| `useClassifications.ts` | 60 | Provenance classification list |
| `useMigration.ts` | 52 | Provenance migration summary |
| `useScanStatus.ts` | 51 | Provenance scan runs |
| `useZipInventory.ts` | 52 | Provenance zip inventory |
| `useProvenanceStatus.ts` | 27 | Provenance connection check |
| `useFileIndex.ts` | 62 | F2 file index |
| `useDuplicates.ts` | 54 | F2 duplicate groups |
| `useWatchedFolders.ts` | 85 | F2 watched folders |
| `usePlayground.ts` | 181 | Playground: connection status, policy, sandboxes, submit, run status, MRU history |
| `useSessionRecord.ts` | 26 | Session recording |
| `types.ts` | 574 | All TypeScript interfaces (52+ exports + 11 playground types) |

### types.ts additions vs specs.md section 5

specs.md section 5 TypeScript block is missing:
- `TrajectoryMeta` (the meta sub-object — specs.md has the shape in prose but no TS interface)
- All diff types: `MetaDiffRow`, `StepDiffEntry`, `RunDiff`
- All orchestrator types: `PlanStep`, `OrchestratorPlan`, `PollResult`, `OrchestratorPhase`, `StepStatus`
- All capability matrix types: `MatrixAgent`, `MatrixScript`, `MatrixUseCase`, `CapabilityMatrix`
- All usage types: `TokenSummary`, `ModelUsageRow`, `UseCaseUsageRow`, `UsageStats`
- All agent config types: `AgentConfigEntry`
- All tools types: 12 types
- All provenance types: 11 types

The P3 types in code have two extra fields vs `protocol.md`:
- `PlanStep.context?: string` — shown in OrchestratorView.tsx if non-empty
- `OrchestratorPlan.params?: Record<string, string>` — shown as a strip below the request

---

## 6. Orchestrator: Mock vs Real

**`orchestrate.rs:18`** — current hardcoded path:
```rust
let script_path = format!("{}/agents/orchestrator.exs", agents_path);
```

This is the real LLM-driven agent, not the mock. The orchestrator-agent-spec.md
described this change as the final acceptance criterion; it has been applied.

**`agents/orchestrator.exs`** — behaviour:
1. Reads `ORCHESTRATOR_REQUEST` + `AETHERIS_AGENTS_PATH` env vars
2. Reads `docs/capability-matrix.md` from the agents path
3. Makes a direct Anthropic API call (`Req.post!`) to plan a step sequence
4. Emits `{"type":"plan","request":"...","steps":[...]}` to stdout
5. Blocks on stdin for `{"approved":true/false}`
6. If approved: iterates steps, uses `RunHelpers.load_agent_file` + `Aetheris.start_run` + `RunHelpers.await_run`
7. Emits `step_started` / `step_complete` per step, then `orchestration_complete`

**`agents/mock_orchestrator.exs`** — kept for regression testing; not currently used by Rig.

**architecture.md:100-101** still reads `"spawns: mix run agents/mock_orchestrator.exs"` — STALE.

---

## 7. Harness DB Schema vs specs.md Section 2

Actual schema from `../aetheris/lib/aetheris/store.ex`:

### `runs` (line 788)
```sql
CREATE TABLE runs (
  run_id      TEXT PRIMARY KEY,
  status      TEXT NOT NULL DEFAULT 'running',
  config_json TEXT,
  started_at  TEXT NOT NULL DEFAULT '',
  finished_at TEXT,
  label       TEXT          -- added via migration (store.ex:986)
)
```
**DRIFT:** specs.md shows no `label` column and no `DEFAULT 'running'` on status.

### `events` (line 803)
```sql
CREATE TABLE events (
  id           TEXT PRIMARY KEY,
  run_id       TEXT NOT NULL,
  step         INTEGER NOT NULL,
  seq          INTEGER NOT NULL,
  type         TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  timestamp    TEXT NOT NULL,
  UNIQUE(run_id, seq)
)
```
**MATCH** (column named `type`, not `event_type` in SQL — Rig aliases it in queries).

### `skills` (line 817)
```sql
CREATE TABLE skills (
  id                  TEXT PRIMARY KEY,
  name                TEXT NOT NULL,
  description         TEXT NOT NULL DEFAULT '',
  prompt_template     TEXT NOT NULL DEFAULT '',
  tool_sequence_json  TEXT NOT NULL DEFAULT '[]',  -- specs.md says "tool_sequence"
  step_count          INTEGER NOT NULL DEFAULT 0,
  examples_json       TEXT NOT NULL DEFAULT '[]',
  source_run_ids_json TEXT NOT NULL DEFAULT '[]',  -- not in specs.md
  extracted_at        TEXT NOT NULL
)
```
**DRIFT:**
- Column is `tool_sequence_json`, not `tool_sequence`
- `source_run_ids_json` not documented in specs.md

### `orbs` (line 832)
```sql
CREATE TABLE orbs (
  orb_id        TEXT PRIMARY KEY,
  agent_run_ids TEXT NOT NULL DEFAULT '[]',
  status        TEXT NOT NULL DEFAULT 'running',
  started_at    TEXT NOT NULL,
  finished_at   TEXT
)
-- plus agent_statuses TEXT (added via migration, store.ex:960)
```
**DRIFT:** `agent_statuses` column added via migration; not in specs.md.

### Tables not in specs.md (exist in store.ex)

| Table | Lines | Purpose |
|-------|-------|---------|
| `agent_trees` | 846-858 | Parent/child run relationships (`spawn_agent`) |
| `run_checkpoints` | 863-872 | Resume state (messages, tool history, wait condition) |
| `scheduled_runs` | 876-886 | Cron-style scheduled runs |
| `eval_tasks` | 890-899 | Eval task registry |
| `eval_suites` | 903-910 | Eval suite groupings |
| `eval_runs` | 914-930 | Eval run results (tokens, latency, pass/fail) |
| `eval_baselines` | 934-948 | Eval baseline snapshots |

Rig reads none of these tables. They are harness-internal.

---

## 8. Event Types vs specs.md Section 6

**Authoritative type definition:** `../aetheris/lib/aetheris/trajectory/event.ex:14-35`

| Event type | In specs.md section 6? | Notes |
|-----------|------------------------|-------|
| `prompt_built` | ✓ | |
| `llm_called` | ✓ | |
| `llm_responded` | ✓ | |
| `tool_called` | ✓ | |
| `tool_result` | ✓ | |
| `error` | ✓ | |
| `run_complete` | ✓ | |
| `step_complete` | ✓ | |
| `agent_message_sent` | ✓ | |
| `agent_message_received` | ✓ | |
| `observation` | ✗ | In code, not in docs |
| `run_cancelled` | ✗ | In code, not in docs |
| `loop_detected` | ✗ | In code, not in docs |
| `escalation_requested` | ✗ | In code, not in docs |
| `escalation_responded` | ✗ | In code, not in docs |
| `agent_waiting` | ✗ | In code, not in docs |
| `agent_resumed` | ✗ | In code, not in docs |
| `agent_spawned` | ✗ | In code, not in docs |
| `agent_tree_joined` | ✗ | In code, not in docs |
| `pre_tool_result` | ✗ | In code, not in docs |
| `context_summarised` | ✗ | In code, not in docs |

**Payload drift in specs.md section 6:**
- `cost_usd` is emitted in `llm_responded` payloads only (`execution/loop.ex:241-284`; computed by `execution/pricing.ex`); `llm_called` payload is `{"model"}` only (`loop.ex:178`). Not listed in specs.md section 6.
- `usage.rs` successfully reads `cost_usd` from `llm_responded` events via `json_extract` — the data is present in the DB

---

## 9. Environment Variables

### Read in Rig Rust source (`lib.rs`, `commands/*.rs`)

| Var | Where read | Purpose |
|-----|-----------|---------|
| `AETHERIS_DB_PATH` | `lib.rs:139`, `trajectory.rs:25` | Opens harness SQLite; derives aetheris_dir for orchestrator CWD |
| `AETHERIS_AGENTS_PATH` | `lib.rs:167`, `lib.rs:197`, `capability_matrix.rs:31` | Agent repo root for orchestrator + tools + capability matrix |
| `PROVENANCE_DB_PATH` | `lib.rs:111` | Opens corpus DuckDB read-only |
| `AETHERIS_API_URL` | `commands/playground.rs` | Base URL of running aetheris harness API (e.g. `http://localhost:4001`) |
| `AETHERIS_API_TOKEN` | `commands/playground.rs` | Bearer token matching `AETHERIS_PLAYGROUND_TOKENS` on the harness side |
| `USER` / `USERNAME` | `provenance.rs:11-12` | Display name in Provenance tab |

### Documented but NOT directly read by Rig

| Var | Documented in | Reality |
|-----|--------------|---------|
| `CORPUS_SEARCH_MCP_ENABLED` | specs.md§1, runbook.md | Not read by Rust; intended for search agent `.exs` file |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | runbook.md | Stored in `agent-config.json`; injected as env var when orchestrator spawns agents (via the `agent_config` cache loop at `orchestrate.rs:30-32`) — not read directly from env by Rig |

### Used by orchestrator.exs (set by Rig as env vars or already in env)

`ANTHROPIC_API_KEY`, `AETHERIS_MODEL`, `AETHERIS_PROVIDER`, `ORCHESTRATOR_REQUEST` — all passed as env vars to the child process. `ORCHESTRATOR_REQUEST` is set explicitly by orchestrate.rs; the rest come from `agent-config.json` values.

**Note:** There is no `AETHERIS_PROVIDER` in specs.md section 1, but it is read by every `.exs` agent file. It should be documented.

---

## 10. Stale Docs — Ordered by Mislead Severity

| # | Doc | Claim | Reality | Impact |
|---|-----|-------|---------|--------|
| 1 | `architecture.md:100` | "spawns: `mix run agents/mock_orchestrator.exs`" | `orchestrate.rs:18` spawns `agents/orchestrator.exs` — the real agent | New contributor would debug mock script instead of real one |
| 2 | `architecture.md` component map + repo layout | Shows only harness, orchestrator, f2, provenance modules | Missing: Tools, Settings, UsageView, CapabilityMatrixView, AgentConfig | Contributor adding a command would use wrong reference layout |
| 3 | `specs.md §8` Module Structure | Lists `harness/{RunList,TrajectoryView,DiffView}`, `orchestrator/` only | Missing: `settings/`, `tools/`, `harness/UsageView.tsx`, `harness/CapabilityMatrixView.tsx`, `harness/shared.tsx` | Contributor can't find half the component surface from the map |
| 4 | `specs.md §2` skills schema | Column named `tool_sequence TEXT` | Actual column: `tool_sequence_json TEXT` | Would break any query written to spec; Rig never reads skills so silent today |
| 5 | `specs.md §2` skills schema | No `source_run_ids_json` column | `source_run_ids_json TEXT NOT NULL DEFAULT '[]'` exists | Rig queries would miss the column |
| 6 | `specs.md §2` runs schema | No `label` column | `label TEXT` column exists, added via migration | Queries written to spec would miss the label |
| 7 | `specs.md §2` orbs schema | No `agent_statuses` column | `agent_statuses TEXT` added via migration | Queries written to spec would miss the column |
| 8 | `specs.md §6` event type table | 10 event types | 21 event types in code; 11 undocumented | Contributor filtering on event types would miss run_cancelled, agent_spawned, context_summarised, etc. |
| 9 | `specs.md §6` llm_called payload | No `cost_usd` field listed | `cost_usd` is emitted and read by `usage.rs` | Contributor adding cost-based features would not know the field exists |
| 10 | `specs.md §5` TypeScript types | Lists Harness, TrajectoryFile, Diff, Orchestrator types only | ~40 additional types exist in `types.ts` | Contributor would not know the shapes for tools, usage, config, matrix |
| 11 | `specs.md §5` `PlanStep` | `{id, agent, description}` only | Actual: `{id, agent, description, context?}` | UI renders `step.context` — doc gives wrong shape |
| 12 | `specs.md §5` `OrchestratorPlan` | No `params` field | `params?: Record<string,string>` present and rendered | Doc gives wrong shape |
| 13 | `runbook.md:189` | "Current groups: Harness, Anthropic, SMTP, Google Drive, Provenance, GitHub" | Payslip group was added to `agentConfigDefs.ts` | HR/operator docs would be incomplete |
| 14 | `specs.md §1` env vars | No `GITHUB_PERSONAL_ACCESS_TOKEN` | Documented in `runbook.md` but missing from `specs.md` | Contributor checking specs would not know the var exists |
| 15 | `specs.md §1` env vars | No `AETHERIS_PROVIDER` | Read by every agent `.exs` file | Var undocumented; contributor might not know to set it |
| 16 | `architecture.md:40-42` | `OrchestratorState { jobs: Mutex<HashMap<…>> }` only | Actual: also `agents_path: Option<String>` + `aetheris_dir: Option<String>` | Contributor modifying orchestrate.rs would use wrong struct definition |
| 17 | `architecture.md` trust boundary | lists only 4 backend modules | Missing: `commands/agent_config.rs`, `commands/capability_matrix.rs`, `commands/usage.rs`, `commands/tools.rs` | Trust boundary table is half the actual surface |
| 18 | `docs/rig/README.md` | milestone tree may reference P3 as future | P3 through P8 + orchestrator spec are all complete | Would mislead any contributor about project maturity |

---

## Gap Analysis

### A. Token/cost rollups in Rig

**Current state:** Mostly working.

- `cost_usd`, `input_tokens`, and `output_tokens` are all in `llm_responded` payloads (`execution/loop.ex:241-284`); `llm_called` payload contains only `{"model"}` (`loop.ex:178`). `usage.rs:45` aggregates via `json_extract(payload_json, '$.cost_usd')` filtering `WHERE type = 'llm_responded'`.
- `UsageView` shows per-run avg cost, total cost, by-model and by-use-case breakdowns.
- **Gap:** `harness_list_runs` does NOT include cost or token totals in `RunSummary` — they are not aggregated in the run list SQL. Adding them requires joining `events` and using `SUM(json_extract(...))` with a `IS NOT NULL` guard, same as `usage.rs`.
- Pricing for unknown models returns `cost_usd: nil` (`pricing.ex:21`), displayed as `—`.
- **Rig-side addressed:** `total_cost_usd` added to `harness_list_runs` query and `RunSummary`; rendered in run list Cost column (`RunList.tsx`). Harness-side token totals per-run remain absent from `RunSummary`.

### B. Stale/stuck run detection

**Current state:** No watchdog in harness or Rig.

- Harness has `max_runtime_ms` in `RunConfig` that terminates runs exceeding a wall-clock limit, but this only fires during active execution; it does not detect runs that crashed mid-flight and left `status = 'running'`.
- `run_checkpoints` table stores last-known-good state but no TTL or heartbeat is written to it on a timer.
- Rig has no stuck-run indicator. The cheapest signal would be: `SELECT run_id, MAX(timestamp) as last_event FROM events WHERE run_id IN (SELECT run_id FROM runs WHERE status = 'running') GROUP BY run_id` — if `now() - last_event > threshold`, the run is suspect.
- `RunList.tsx` shows live amber badge for `status = 'running'` runs but no staleness indicator.
- **Rig-side addressed:** `last_event_at` added to `RunSummary`; `RunList.tsx` renders "stalled?" marker with 5-minute threshold and 60s re-evaluation interval. Harness-side watchdog (auto-marking crashed runs failed) remains absent.

### C. Replay/fork from step

**Current state:** Infrastructure exists but is not exposed in Rig.

- `run_checkpoints` table (`store.ex:863`) stores per-run: `step`, `status`, `messages_json`, `tool_history_json`, `wait_condition_json`, `updated_at`. This is the resume mechanism for `wait_for_event` / paused runs.
- `priv/runs/{run_id}/trajectory.json` stores the full event sequence including `prompt_built` events with `context_hash` and `message_count`. The conversation context at step N can be reconstructed from the messages in `run_checkpoints.messages_json` (for live runs) or by replaying `llm_called` payloads from the trajectory (for completed runs).
- `Aetheris.fork_run` or equivalent is not visible in the harness public API from a search of `lib/aetheris.ex:111` (only `extract_skill` is near line 111). A fork-from-step feature would need a harness API addition plus a new Rig command — neither exists today.
- **Bottom line:** enough state is recorded to reconstruct context at step N, but no fork API or Rig command exposes it.

### D. Skills extraction

**Current state:** Schema and write path exist; no automatic extraction pipeline.

- `skills` table is fully defined in `store.ex:817`.
- `store.ex:132` (`insert_skill`) and `store.ex:619` (`handle_call {:insert_skill}`) implement the write path.
- `lib/aetheris.ex:111` (`extract_skill`) is the public API entry point — a manual call, not automatic post-run hook.
- `api/tenant/scripts/extract_skill_hints.py` reads a trajectory JSON and writes a skill-hint JSON for injection into `at1cmd` — this is a separate, domain-specific extraction script unrelated to the `skills` table.
- **Nothing writes to `skills` automatically after a run.** `extract_skill` must be called explicitly from IEx or a script. No Rig command reads the skills table. The table is schema-complete and write-capable but operationally empty in normal use.

---

## Part 3 — Reference Snapshot

### 3.1 trajectory.json Format

#### Writer location and timing

Writer: `agent/server.ex:673` and `agent/server.ex:944` via `Aetheris.Trajectory.File.write/3`.
Located at `lib/aetheris/trajectory/file.ex`.

**Written only at run end, not incrementally.** Both call sites are in the
`run_loop_*` private functions that execute after the execution loop returns.
The file does not exist during a live run; it appears atomically at completion
via a `.tmp` → rename (`file.ex:37-38`). A Rig trajectory load for a `status=running`
run will return an error ("read failed: No such file or directory").

#### Top-level structure

```
{
  "schema_version": "1",           // always "1"
  "run_id":         string,
  "meta":           object,         // see below
  "events":         array           // ordered by seq ASC
}
```

#### `meta` object — all fields

From `server.ex:655-671` (first write) and `:935-942` (resumed write):

| Field | Type | Notes |
|-------|------|-------|
| `model` | string | from RunConfig |
| `provider` | string | from RunConfig |
| `mode` | string | `"record"` \| `"replay"` \| `"verify"` |
| `step_count` | integer | unique step values in the events list |
| `max_steps` | integer | from RunConfig |
| `started_at` | ISO 8601 string | |
| `finished_at` | ISO 8601 string | |
| `tools` | string[] | from RunConfig |
| `system_prompt` | string | full text, untruncated |
| `user_prompt` | string | full text, untruncated |
| `sandbox_path` | string \| null | |
| `seed` | null (always seen as null) | |
| `overlay_changes` | array | from `collect_overlay_changes` |
| `resumed` | boolean | **only present when true** — added at `server.ex:941` for resumed runs |

**`TrajectoryMeta` in `types.ts:193-207` does not declare `resumed`.** Rust
returns `meta` as `serde_json::Value` (`trajectory.rs:50`), so the field
passes through to TypeScript, but the type interface silently drops it. Any
code that uses `meta as TrajectoryMeta` will not see `resumed`.

#### Per-event fields

From `file.ex:67-77` (writer) and actual files:

| File key | Rust `TrajectoryEvent` field | Type in file | Notes |
|----------|------------------------------|--------------|-------|
| `id` | `id` | hex string (MD5) | |
| `run_id` | `run_id` | string | |
| `step` | `step` | integer | 0-based |
| `seq` | `seq` | integer | monotonic across run |
| `type` | `event_type` | string | renamed by trajectory.rs:61 |
| `payload` | `payload` | JSON object | **inlined object, not a string** |
| `timestamp` | `timestamp` | ISO 8601 string | |

**Key difference from SQLite `events` table:** In SQLite, `payload_json` is
a TEXT column containing a JSON string. In the trajectory file, `payload`
is a JSON object. `trajectory.rs` maps the file's inline object to
`serde_json::Value`; `harness.rs` returns the raw string. Do not conflate
`EventRow.payload` (string) with `TrajectoryEvent.payload` (object).

#### Payload truncation

**No truncation in trajectory files.** `file.ex:73` writes `event.payload`
verbatim via `Jason.encode!`. All payloads are stored complete.

The `truncate_payload/1` function at `loop.ex:919-921` (200-char limit) is
used only for CLI progress display strings; it does not affect what is stored.

Evidence: `run_yfojFw` trajectory contains a `tool_input` with a 3KB Python
script stored in full inside a single `llm_responded` event.

#### Payload shapes for key event types (from actual files)

**`prompt_built`**
```json
{ "context_hash": "sha256:...", "message_count": 11 }
```
Does not include the conversation messages — only a hash. System/user prompts
are in `meta`, not per-event.

**`llm_called`**
```json
{ "model": "claude-haiku-4-5-20251001" }
```
No tokens or cost here. The Anthropic adapter populates tokens on the
_response_ object; they land in `llm_responded`.

**`llm_responded`** (real Anthropic API call — `payslip-orch-XBGmfw`)
```json
{
  "cost_usd": 0.0018968,
  "input_tokens": 1831,
  "latency_ms": 1207,
  "output_tokens": 108,
  "raw_response": null,
  "resolved_model": "claude-haiku-4-5-20251001",
  "response_type": "tool_call",
  "system_fingerprint": null,
  "tool_input": { "command": "python3", "args": [...] },
  "tool_name": "run_command"
}
```
`input_tokens`, `output_tokens`, `cost_usd` are populated by `loop.ex:249-256`
from the adapter response. For stub/Ollama runs they may be `null`.
**These fields are not declared in `TrajectoryMeta` or `TrajectoryEvent` in
`types.ts`** — they exist in the payload object but the interface uses
`Record<string, unknown>` so they are accessible as untyped values.
`specs.md §6` does not list `cost_usd` in the `llm_responded` payload column.

**`tool_called`**
```json
{
  "tool_name": "run_command",
  "tool_input": { "command": "python3", "args": [...] },
  "source": "mcp",
  "server_id": "aetheris_exec"
}
```

**`tool_result`**
```json
{
  "tool_name": "run_command",
  "output": "{\"duration_ms\":21,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"Generated 2026-03.html\\n\"}",
  "fs_hash": null
}
```
`output` is a JSON-encoded string (the tool's stdout/stderr). It is not
truncated. Large outputs (e.g. full file listings, wkhtmltopdf output) are
stored in their entirety.

**`agent_message_received`** (from orb run `orb-full-4100-agent-b`)
```json
{
  "content": "hello from A",
  "from_run_id": "orb-full-4100-agent-a",
  "message_id": "a7d75c3c..."
}
```

**`run_complete`**
```json
{ "reason": "agent_finished" }
```
Other `reason` values: `"max_steps_reached"`, `"error"`.

#### Fields Rig drops or assumes present

- `TrajectoryMeta.finished_at` typed as `string` (not `string | null`). If a
  run was interrupted, `finished_at` may be missing from the file; Rig would
  receive `""` (the `unwrap_or("")` default in `trajectory.rs:63`).
- `TrajectoryMeta` does not declare `resumed: boolean`. Present in files for
  resumed runs (`server.ex:941`); silently ignored by the TypeScript type.
- No `cost_usd`, `input_tokens`, `output_tokens` fields on `TrajectoryEvent` —
  accessible as `event.payload['cost_usd']` but not typed.
- `file.ex` event type map at line 99 includes `run_started` —
  **this type is in the deserialiser's map but not in `event.ex` `@type`**.
  It is safe to encounter in a file but would raise in trajectory/file.ex
  `to_event_type/1` only if the string is absent from the map. Not a current
  risk.

---

### 3.2 State Struct Inventory

All state structs managed via `app.manage()` in `lib.rs`. Every field
is set once at startup and read-only thereafter (no mutation after init).

| Struct | lib.rs lines | Fields | Used by |
|--------|-------------|--------|---------|
| `CorpusState` | 11–14 | `conn: Option<Arc<Mutex<duckdb::Connection>>>`, `path: Option<String>` | `commands/provenance.rs` (all 11 provenance commands) |
| `HarnessState` | 16–19 | `conn: Option<Arc<Mutex<rusqlite::Connection>>>`, `path: Option<String>` | `commands/harness.rs` (4 commands), `commands/trajectory.rs` (receives `_state` but reads env var directly for path) |
| `OrchestratorJob` | 21–26 | `child: Arc<Mutex<Child>>`, `stdin: Arc<Mutex<ChildStdin>>`, `buffer: Arc<Mutex<Vec<Value>>>`, `done: Arc<AtomicBool>` | Stored inside `OrchestratorState.jobs`; accessed by `commands/orchestrate.rs` |
| `AgentConfigState` | 28–31 | `store_path: PathBuf`, `cache: Mutex<HashMap<String,String>>` | `commands/agent_config.rs` (5 commands), `commands/orchestrate.rs` (`orchestrate_start` injects cache as env vars) |
| `OrchestratorState` | 33–37 | `jobs: Mutex<HashMap<String, OrchestratorJob>>`, `agents_path: Option<String>`, `aetheris_dir: Option<String>` | `commands/orchestrate.rs` (all 4 orchestrate commands) |
| `ToolsState` | 39–41 | `agents_path: Option<String>` | `commands/tools.rs` (all 5 tools commands) |

**Init notes:**
- `CorpusState.conn` — `None` if `PROVENANCE_DB_PATH` unset or file unreadable (`lib.rs:111-134`)
- `HarnessState.conn` — `None` if `AETHERIS_DB_PATH` unset or file unreadable (`lib.rs:139-163`); opened `SQLITE_OPEN_READ_ONLY | SQLITE_OPEN_NO_MUTEX`
- `OrchestratorState.aetheris_dir` — derived from `AETHERIS_DB_PATH` by walking two `.parent()` calls (`lib.rs:168-173`); `None` if `AETHERIS_DB_PATH` not set; this is the `current_dir` for `mix run` in `orchestrate.rs:25`
- `OrchestratorState.agents_path` and `ToolsState.agents_path` — both read from `AETHERIS_AGENTS_PATH` independently (`lib.rs:167,197`)
- `AgentConfigState.cache` — loaded from `agent-config.json` at startup; stays in memory; written back to disk on each `agent_config_set/delete/import` call

**`HarnessState` note:** `trajectory.rs` receives `_state: State<'_, HarnessState>` as a parameter but does not use the connection — it reads `AETHERIS_DB_PATH` directly via `std::env::var` (`trajectory.rs:25`). The state parameter exists for architectural consistency; the actual path derivation is independent.

---

### 3.3 Route Verification

#### Routes declared in `App.tsx` (lines 50–111)

| Path | Component | Wrapper |
|------|-----------|---------|
| `/` | `<Navigate to="/harness" replace />` | — |
| `/harness` | `HarnessRoute` | none (self-contained) |
| `/diff` | `DiffView` | `flex flex-1 flex-col overflow-y-auto` div |
| `/capability-matrix` | `CapabilityMatrixView` | `flex flex-1 flex-col overflow-hidden` div |
| `/usage` | `UsageView` | `flex flex-1 flex-col overflow-hidden` div |
| `/orchestrator` | `OrchestratorView` | `flex flex-1 flex-col overflow-y-auto p-8` div |
| `/tools` | `ToolsView` | `flex flex-1 h-full overflow-hidden` div |
| `/f2/operations` | `MainArea` with `F2Operations()` tabs | — |
| `/f2/viewer` | `MainArea` with `F2Viewer()` tabs | — |
| `/provenance` | `MainArea` with 4 tab arrays merged | — |
| `/settings` | `SettingsRoute` | none (self-contained) |

11 route declarations total (including the root redirect).

#### Diff against `registry.ts`

| registry.ts path | App.tsx route | Status |
|-----------------|--------------|--------|
| `/harness` | `/harness` | ✓ match |
| `/diff` | `/diff` | ✓ match |
| `/capability-matrix` | `/capability-matrix` | ✓ match |
| `/usage` | `/usage` | ✓ match |
| `/orchestrator` | `/orchestrator` | ✓ match |
| `/tools` | `/tools` | ✓ match |
| `/f2/operations` | `/f2/operations` | ✓ match |
| `/f2/viewer` | `/f2/viewer` | ✓ match |
| `/provenance` | `/provenance` | ✓ match |
| — | `/settings` | **App.tsx only** — no registry entry |
| — | `/` → redirect | App.tsx only — not a module route |

**`/settings` has no registry entry.** The Settings route (`SettingsRoute`) is
wired in `App.tsx:110` but has no corresponding entry in `registry.ts` and
therefore no sidebar item. Settings is reached by a separate mechanism (likely
a gear icon or menu item in the shell), not via the module sidebar. No module
section is missing from the sidebar; the route is reachable but not listed.

---

## §10 Resolution Log

**Resolved 2026-06-11** — All 18 stale items from §10 addressed in a single
doc-fix pass. Changes:

| # | Resolution |
|---|-----------|
| 1 | `architecture.md` data flow: `mock_orchestrator.exs` → `orchestrator.exs` |
| 2 | `architecture.md` component map + repo layout: added Tools, Settings, UsageView, CapabilityMatrixView, AgentConfig, all 9 hooks, all 8 commands |
| 3 | `specs.md §8` module structure: added `tools/`, `settings/`, `harness/UsageView.tsx`, `harness/CapabilityMatrixView.tsx`, `harness/shared.tsx` |
| 4 | `specs.md §2` skills: `tool_sequence` → `tool_sequence_json` |
| 5 | `specs.md §2` skills: added `source_run_ids_json` |
| 6 | `specs.md §2` runs: added `label TEXT` column + `DEFAULT 'running'` |
| 7 | `specs.md §2` orbs: added `agent_statuses` column |
| 8 | `specs.md §6` event types: expanded from 10 to 21; added all undocumented types |
| 9 | `specs.md §6` llm_called/llm_responded: added `cost_usd` field |
| 10 | `specs.md §5` TypeScript types: added note listing all 52+ types; pointer to `types.ts` |
| 11 | `specs.md §5` + `protocol.md`: `PlanStep.context?` added |
| 12 | `specs.md §5` + `protocol.md`: `OrchestratorPlan.params?` added |
| 13 | `runbook.md`: Payslip added to config groups list |
| 14 | `specs.md §1`: `GITHUB_PERSONAL_ACCESS_TOKEN` added |
| 15 | `specs.md §1`: `AETHERIS_PROVIDER` added |
| 16 | `architecture.md`: `OrchestratorState` updated with all 3 fields |
| 17 | `architecture.md` trust boundary: added agent_config, capability_matrix, usage, tools rows; flagged `tools.rs` as code-executing |
| 18 | `docs/rig/README.md`: milestone table updated; p4–p8 + orchestrator all marked ✅ |

**Additional fixes in same pass:**
- `runbook.md`: added troubleshooting entry for trajectory "read failed"
- `docs/rig/README.md`: added link to current-state-2026-06.md
- Phase READMEs (p1–p7): added `Status: IMPLEMENTED` headers
- `p8/README.md`: created
- `orchestrator/README.md`: created
- `p2-001-polling-hook.md`: clarified "three new effects" — final implementation is 5 total
- `docs/handoff-aetheris-provenance-rig.md`: prepended SUPERSEDED banner
- `architecture.md`: documented `/settings` sidebar oddity + `trajectory.rs` env var oddity (Part C)
- `rig/src/hooks/types.ts` (Part B): `LlmRespondedPayload` interface, `TrajectoryMeta.resumed?`, `finished_at` JSDoc, payload divergence JSDoc

**Drift baseline 2026-06-11:** 8 PASS  0 FAIL  0 WARN  12 INFO (aetheris-agents `09a74c2`, AETHERIS_DB_PATH set). First clean run post all parser fixes (paren-depth, payload `?` marker, `_evaluate_payload_fields`, project_knowledge check 8).

**Report errata fixed 2026-06-11** (found during d82cf7e specs.md review):
- §1/P6: `cost_usd` is in `llm_responded` events, not `llm_called`; `usage.rs:45` filters `WHERE type = 'llm_responded'`
- §8 payload-drift + Gap A: same correction — `llm_called` payload is `{"model"}` only (`loop.ex:178`); `cost_usd`/`input_tokens`/`output_tokens` are all `llm_responded`-only (`loop.ex:241-284`)
- §1/P7: `agent_config_export` returns `String` (no path arg); `agent_config_import` takes `HashMap<String,String>` → `usize`; `AgentConfigEntry` is TypeScript-only, no Rust struct

**Drift baseline 2026-07-15:** 8 PASS  0 FAIL  0 WARN  13 INFO (aetheris-agents `bdcf34d`; `AETHERIS_DB_PATH=/home/it/sandbox/elixirws/aetheris/priv/aetheris.db`, 23 MB, sole non-build DB). BL-001 (#42) clean-baseline capture. Delta from 2026-06-11 baseline: +1 INFO from `DOCBUILDER_TENANT` (agent-side env var added to specs §1 since; benign). Phantom `runs.finished_at` and `llm_responded.stop_reason` INFOs confirmed gone. The 13 INFO are all benign: 4 env_vars (agent-side vars in specs §1 not read by Rig) + 9 payload_fields (valid event payload fields not yet promoted to specs §6). Five orphaned May `running` rows (BL-003 fixtures) left untouched; DB and drift_check.py read-only this ticket.
