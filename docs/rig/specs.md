# Rig — Specifications

---

## 1. Environment Variables

| Variable | Required | Default | Description |
|----------|---------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | — | Path to `aetheris/priv/aetheris.db`; also used by `trajectory.rs` to derive run directory |
| `AETHERIS_AGENTS_PATH` | Yes (orchestrator/tools) | — | Path to `aetheris-agents/` root; used by orchestrate.rs, tools.rs, capability_matrix.rs |
| `AETHERIS_PROVIDER` | No | `anthropic` | Default LLM provider passed to every `.exs` agent; not read by Rig Rust code directly |
| `AETHERIS_API_URL` | Yes (playground features) | — | Base URL of the running aetheris harness API (e.g. `http://localhost:4001`); read by `commands/playground.rs` |
| `AETHERIS_API_TOKEN` | Yes (playground features) | — | Bearer token matching one of `AETHERIS_PLAYGROUND_TOKENS` configured in the harness; read by `commands/playground.rs` |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | — | Path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | — | Not read by Rig Rust; intended for the `search_agent.exs` file when the corpus-search MCP is active |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No | — | Stored in `agent-config.json`; injected as env var when orchestrator spawns agents — not read from env directly by Rig |
| `DOCBUILDER_TENANT` | No | — | p9 — stored in `agent-config.json` ("Docbuilder" group); injected when the Docbuilder panel / orchestrator spawns agents, and passed as `--tenant` to the chain script. Not read from env directly by Rig |

---

## 2. Harness DB Schema (read from aetheris.db)

Tables Rig reads. Schema is owned by the harness — never written by Rig.

### `runs`
```sql
CREATE TABLE runs (
  run_id       TEXT PRIMARY KEY,
  status       TEXT NOT NULL DEFAULT 'running',  -- idle | running | paused | done | failed
  config_json  TEXT,          -- JSON: RunConfig snapshot
  started_at   TEXT NOT NULL DEFAULT '',         -- ISO 8601
  finished_at  TEXT,                             -- ISO 8601 | NULL
  label        TEXT           -- added via migration; extracted from config_json
);
```

### `events`
```sql
CREATE TABLE events (
  id           TEXT PRIMARY KEY,
  run_id       TEXT REFERENCES runs(run_id),
  step         INTEGER,
  seq          INTEGER,       -- monotonic within run
  type         TEXT,          -- event type atom
  payload_json TEXT,          -- event-type-specific JSON
  timestamp    TEXT           -- ISO 8601
);
```

### `orbs`
```sql
CREATE TABLE orbs (
  orb_id        TEXT PRIMARY KEY,
  agent_run_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of run_ids
  status        TEXT NOT NULL DEFAULT 'running',
  started_at    TEXT NOT NULL,
  finished_at   TEXT,
  agent_statuses TEXT          -- added via migration; per-agent status JSON
);
```

### `skills`
```sql
CREATE TABLE skills (
  id                  TEXT PRIMARY KEY,
  name                TEXT NOT NULL,
  description         TEXT NOT NULL DEFAULT '',
  prompt_template     TEXT NOT NULL DEFAULT '',
  tool_sequence_json  TEXT NOT NULL DEFAULT '[]',  -- note: _json suffix (not "tool_sequence")
  step_count          INTEGER NOT NULL DEFAULT 0,
  examples_json       TEXT NOT NULL DEFAULT '[]',
  source_run_ids_json TEXT NOT NULL DEFAULT '[]',  -- run IDs this skill was extracted from
  extracted_at        TEXT NOT NULL
);
```

### Harness-internal tables (not read by Rig)

The following tables exist in `aetheris.db` but Rig reads none of them:

| Table | Purpose |
|-------|---------|
| `agent_trees` | Parent/child run relationships (`spawn_agent`) |
| `run_checkpoints` | Resume state (messages, tool history, wait condition) |
| `scheduled_runs` | Cron-style scheduled runs |
| `eval_tasks` | Eval task registry |
| `eval_suites` | Eval suite groupings |
| `eval_runs` | Eval run results (tokens, latency, pass/fail) |
| `eval_baselines` | Eval baseline snapshots |

---

## 3. Trajectory File Schema

Written by the harness to `priv/runs/{run_id}/trajectory.json` at run
completion. Immutable after write. Read by Rig for the trajectory viewer
and run diff (p4).

```json
{
  "run_id": "ollama-LDykLQ",
  "schema_version": "1",
  "meta": {
    "model":           "llama3.2:latest",
    "provider":        "ollama",
    "mode":            "record",
    "step_count":      2,
    "max_steps":       2,
    "started_at":      "2026-05-27T02:53:45.097163Z",
    "finished_at":     "2026-05-27T02:55:12.150494Z",
    "tools":           ["list_dir"],
    "system_prompt":   "You are a helpful assistant. Be brief.",
    "user_prompt":     "List the top-level directories in this project.",
    "sandbox_path":    "/home/it/sandbox/elixirws/aetheris",
    "seed":            null,
    "overlay_changes": []
  },
  "events": [
    {
      "id":        "aba3866a…",
      "run_id":    "ollama-LDykLQ",
      "seq":       0,
      "step":      0,
      "type":      "prompt_built",
      "payload":   { "context_hash": "sha256:…", "message_count": 1 },
      "timestamp": "2026-05-27T02:53:45.105645Z"
    }
  ]
}
```

Key difference from `events` table: `payload` is a structured JSON object,
not a string. The trajectory file is the authoritative source for post-run
analysis; SQLite is the live source during a run.

Path derivation from `AETHERIS_DB_PATH`:
```
~/…/aetheris/priv/aetheris.db
  → parent → priv/
  → parent → aetheris/
  → join "priv/runs/{run_id}/trajectory.json"
```

---

## 4. Tauri Command Shapes

### Harness commands (`commands/harness.rs`)

**`harness_list_runs`**
```rust
pub struct RunSummary {
    pub run_id:         String,
    pub label:          String,        // COALESCE(runs.label, run_id) — the label column,
                                       // NOT config_json (the harness strips it, server.ex:758)
    pub status:         String,
    pub provider:       String,        // from config_json.provider
    pub model:          String,        // from config_json.model
    pub started_at:     String,
    pub finished_at:    Option<String>,
    pub step_count:     i64,           // MAX(step) from events
    pub event_count:    i64,           // COUNT(*) from events
    pub last_event_at:  Option<String>,// MAX(timestamp) from events; NULL if no events
    pub total_cost_usd: Option<f64>,   // SUM cost_usd from llm_responded events; NULL when no cost data
    pub total_input_tokens:  Option<i64>,  // SUM input_tokens from llm_responded; NULL when no token data
    pub total_output_tokens: Option<i64>,  // SUM output_tokens from llm_responded; NULL when no token data
}
```

**`harness_get_events`**

Takes `run_id: String`. Returns:
```rust
pub struct EventRow {
    pub id:         String,
    pub run_id:     String,
    pub step:       i64,
    pub seq:        i64,
    pub event_type: String,
    pub payload:    String,        // raw JSON string — differs from TrajectoryEvent
    pub timestamp:  String,
}
```

**`harness_get_run`**

Takes `run_id: String`. Returns:
```rust
pub struct RunDetail {
    pub run_id:      String,
    pub label:       String,       // COALESCE(runs.label, run_id) — see RunSummary.label
    pub status:      String,
    pub config:      String,       // full config_json
    pub started_at:  String,
    pub finished_at: Option<String>,
}
```

**`harness_connection_status`**

Returns:
```rust
pub struct HarnessStatus {
    pub connected: bool,
    pub db_path:   Option<String>,
    pub run_count: i64,
    pub error:     Option<String>,
}
```

### Trajectory commands (`commands/trajectory.rs`) — p4

**`trajectory_load`**

Takes `run_id: String`. Returns:
```rust
pub struct TrajectoryEvent {
    pub id:         String,
    pub run_id:     String,
    pub seq:        i64,
    pub step:       i64,
    pub event_type: String,
    pub payload:    serde_json::Value,   // parsed object — NOT a raw string
    pub timestamp:  String,
}

pub struct TrajectoryFile {
    pub run_id:         String,
    pub schema_version: String,
    pub meta:           serde_json::Value,
    pub events:         Vec<TrajectoryEvent>,
}
```

**`trajectory_export`**

Takes `run_id: String`. Opens a save dialog; copies
`priv/runs/{run_id}/trajectory.json` to the user-chosen path. Returns `()`.

### Fork command (`commands/fork.rs`) — BL-007 t3

**`fork_run`** — `async` command. Takes `run_id: String`, `step: u64`,
`label: Option<String>`. Resolves the source trajectory (`traj_path`, shared with
`trajectory.rs`) and spawns `mix aetheris --json fork <trajectory> --step N
[--name label]` in the aetheris repo root (`aetheris_root` =
`AETHERIS_DB_PATH`.parent().parent()). The child run is the post-t2 CLI's fork —
re-execution from step N (converged on `Fork.from_step/3`): it runs in `:record`
mode and is identified by `meta.fork_from`, not a `:fork` mode. Returns the forked
`run_id: String` parsed from the CLI's JSON result line, or an error string.
**Blocks to completion:** `mix aetheris fork` prints the run id only when the fork
reaches a terminal status (`await_run`), so the command runs the blocking
subprocess on `spawn_blocking` (`async`, off the UI thread — Tauri v2 runs *sync*
commands on the main thread); the invoke promise resolves when the fork finishes
(progress UX is t4's concern). **Terminal status:** a run id appears on stdout only
for a `done` fork; `failed`/`cancelled`/`step_not_found` produce a CLI error on
*stderr* with a zero exit code, so `fork_run` returns `Err` carrying that stderr —
never a false success. **`label` caveat:** persisted to the harness `runs.label`
column, but Rig's `harness_list_runs`/`harness_get_run` read the label from
`config_json` (where `encode_config` strips it), so a fork label is stored but not
surfaced by Rig today (see BL-007 t3 notes).

### Orchestrator commands (`commands/orchestrate.rs`) — p3 (extended p9)

**`orchestrate_start`** — Takes `request: String`, `extra_env: HashMap<String, String>`
(p9 t1 — per-run env vars, injected after `agent_config` so per-run wins on collision;
never persisted), and `script_path: Option<String>` (p9 t4 — agent/script path relative to
`AETHERIS_AGENTS_PATH`; `None` → the default `agents/orchestrator.exs`). A `script_path`
ending in `.py` is spawned **top-level** as `python3 <path> --tenant --request --aetheris-dir
--agents-dir --protocol` (the docbuilder chain — cannot be a nested `mix aetheris run`);
otherwise `mix aetheris run <path>`. Returns `job_id: String`.

**`orchestrate_poll`** — Takes `job_id: String`. Returns:
```rust
pub struct PollResult {
    pub messages: Vec<serde_json::Value>,
    pub done:     bool,
}
```

**`orchestrate_approve`** — Takes `job_id: String, approved: bool`. Returns `()`.

**`orchestrate_cancel`** — Takes `job_id: String`. Returns `()`.

### Agent config commands (`commands/agent_config.rs`) — p7

All take `key: String` / `value: String` as appropriate. Store path:
`~/.local/share/dev.rig.app/agent-config.json`.

| Command | Args | Returns |
|---------|------|---------|
| `agent_config_get_all` | — | `HashMap<String, String>` (raw stored values) |
| `agent_config_set` | `key`, `value` | `()` |
| `agent_config_delete` | `key` | `()` |
| `agent_config_export` | — | `String` (serialized JSON — no path; returned to caller) |
| `agent_config_import` | `values: HashMap<String, String>` | `usize` (count imported) |

`AgentConfigEntry` is a TypeScript-side type (`types.ts:372`) assembled by
`useAgentConfig.ts` from `agentConfigDefs.ts` (hardcoded field metadata) merged
with the HashMap returned by `agent_config_get_all`. No corresponding Rust struct exists.

### Capability matrix command (`commands/capability_matrix.rs`) — p5

**`capability_matrix_load`** — Takes no args. Reads
`docs/capability-matrix.md` from `AETHERIS_AGENTS_PATH`. Returns:
```rust
pub struct CapabilityMatrix {
    pub use_cases:    Vec<MatrixUseCase>,
    pub generated_at: Option<String>,
}
```

### Usage command (`commands/usage.rs`) — p6

**`usage_stats_load`** — Takes no args. Aggregates from `events` table via
`json_extract(payload_json, '$.cost_usd')`. Returns:
```rust
pub struct UsageStats {
    pub total_cost_usd:      f64,
    pub total_runs:          i64,
    pub instrumented_runs:   i64,
    pub total_input_tokens:  i64,
    pub total_output_tokens: i64,
    pub by_model:            Vec<ModelUsageRow>,
    pub by_use_case:         Vec<UseCaseUsageRow>,
}
```

### Tools commands (`commands/tools.rs`) — p4-tools

| Command | Args | Returns |
|---------|------|---------|
| `tools_list_inventory` | — | `ToolsInventory` |
| `tools_read_script` | `path` | `String` (source) |
| `tools_run_script` | `use_case`, `script_name`, `args: HashMap` | `ScriptResult` |
| `tools_list_mcp` | — | `Vec<McpServerGroup>` |
| `tools_call_mcp` | `server_id`, `tool_name`, `arguments: Value` | `McpCallResult` |

`tools_run_script` executes the named Python script as a subprocess. This is
the only Rig command that runs arbitrary code from the agent repo.

### F2 commands (`commands/f2.rs`) — pre-existing, shapes documented in code

| Command |
|---------|
| `f2_get_watched_folders` |
| `f2_add_watched_folder` |
| `f2_toggle_watched_folder` |
| `f2_remove_watched_folder` |
| `f2_trigger_scan` |
| `f2_get_file_index` |
| `f2_get_file_count` |
| `f2_get_duplicates` |
| `f2_get_duplicate_stats` |

### Provenance commands (`commands/provenance.rs`) — pre-existing, shapes documented in code

| Command |
|---------|
| `provenance_corpus_summary` |
| `provenance_client_breakdown` |
| `provenance_scan_runs` |
| `provenance_classification_list` |
| `provenance_set_classification_status` |
| `provenance_migration_summary` |
| `provenance_zip_inventory` |
| `provenance_duplicate_groups` |
| `provenance_failed_migrations` |
| `provenance_encrypted_zips` |
| `get_system_username` |

### Playground commands (`commands/playground.rs`) — m-playground-p2

| Command | Input | Output |
|---------|-------|--------|
| `playground_connection_status` | — | `PlaygroundStatus` |
| `playground_get_policy` | — | `PlaygroundPolicy` |
| `playground_get_sandboxes` | — | `PlaygroundSandboxes` |
| `playground_submit_run` | `{ request: PlaygroundSubmitRequest }` | `PlaygroundSubmitResult` |
| `playground_run_status` | `{ runId: String }` | `PlaygroundRunStatus` |

(Types are in `src/hooks/types.ts`.)

---

## 5. TypeScript Interfaces

```typescript
// ── Harness ──────────────────────────────────────────────────────────────────

interface RunSummary {
  run_id:       string;
  label:        string;
  status:       'idle' | 'running' | 'paused' | 'done' | 'failed';
  provider:     string;
  model:        string;
  started_at:   string;
  finished_at:  string | null;
  step_count:   number;
  event_count:  number;
}

interface EventRow {
  id:          string;
  run_id:      string;
  step:        number;
  seq:         number;
  event_type:  string;
  payload:     string;   // raw JSON string — parse per event_type
  timestamp:   string;
}

interface RunDetail {
  run_id:      string;
  label:       string;
  status:      string;
  config:      string;   // raw JSON
  started_at:  string;
  finished_at: string | null;
  events:      EventRow[];
}

interface HarnessStatus {
  connected:  boolean;
  db_path:    string | null;
  run_count:  number;
  error:      string | null;
}

// ── Trajectory (p4) ──────────────────────────────────────────────────────────

interface TrajectoryMeta {
  model:           string;
  provider:        string;
  mode:            string;
  step_count:      number;
  max_steps:       number;
  started_at:      string;
  finished_at:     string;
  tools:           string[];
  system_prompt:   string;
  user_prompt:     string;
  sandbox_path:    string | null;   // config.sandbox_path — no default, nil when unset (run_config.ex:171,88)
  seed:            number | null;   // harness writes config.seed (integer|nil) — server.ex:668,939
  overlay_changes: unknown[];
  resumed?:        boolean;         // only when true — server.ex:941 (resumed runs)
  fork_from?:      string;          // only on forks, always a non-nil string — server.ex:717,720
  fork_step?:      number | null;   // co-present with fork_from; value is config.fork_step (non_neg_integer|nil)
}

interface TrajectoryEvent {
  id:          string;
  run_id:      string;
  seq:         number;
  step:        number;
  event_type:  string;
  payload:     Record<string, unknown>;   // parsed object — NOT a raw string
  timestamp:   string;
}

interface TrajectoryFile {
  run_id:         string;
  schema_version: string;
  meta:           TrajectoryMeta;
  events:         TrajectoryEvent[];
}

// ── Diff (p4) ────────────────────────────────────────────────────────────────

interface MetaDiffRow {
  field:   string;
  a:       string;
  b:       string;
  differs: boolean;
}

interface StepDiffEntry {
  step:      number;
  tools_a:   string[];
  tools_b:   string[];
  differs:   boolean;
  only_in_a: boolean;
  only_in_b: boolean;
}

interface RunDiff {
  meta_rows:   MetaDiffRow[];
  step_rows:   StepDiffEntry[];
  any_differs: boolean;
}

// ── Orchestrator (p3) ────────────────────────────────────────────────────────

interface PlanStep {
  id:          string;
  agent:       string;
  description: string;
  context?:    string;    // optional execution context shown in plan view
}

interface OrchestratorPlan {
  type:    'plan';
  request: string;
  steps:   PlanStep[];
  params?: Record<string, string>;  // optional extracted params shown below request
}

interface PollResult {
  messages: Record<string, unknown>[];
  done:     boolean;
}

type OrchestratorPhase =
  | 'idle'
  | 'planning'
  | 'plan_ready'
  | 'executing'
  | 'done'
  | 'cancelled'
  | 'error';

type StepStatus = 'pending' | 'running' | 'done' | 'failed';
```

The interfaces above cover the core Harness, Trajectory, Diff, and Orchestrator
domains. The full `types.ts` (52+ exports) also defines:

- Capability matrix: `MatrixAgent`, `MatrixScript`, `MatrixUseCase`, `CapabilityMatrix`
- Usage: `TokenSummary`, `ModelUsageRow`, `UseCaseUsageRow`, `UsageStats`
- Agent config: `AgentConfigEntry`
- Tools: `EnvDep`, `ManifestArg`, `ManifestScript`, `UseCaseGroup`, `HarnessToolArg`, `HarnessTool`, `McpTool`, `McpServerGroup`, `ToolsInventory`, `ScriptResult`, `McpCallResult`, `SelectedTool`
- Provenance: `CorpusSummary`, `ClientRow`, `ScanRun`, `ClassificationRow`, `MigrationSummary`, `ZipRow`, `ZipInventory`, `CorpusDuplicateGroup`, `FailedMigration`, `EncryptedZipRow`
- `LlmRespondedPayload` — cast-opt-in type for `event_type === 'llm_responded'` payloads

See `rig/src/hooks/types.ts` for the canonical source.

---

## 6. Event Type Reference

Authoritative source: `../aetheris/lib/aetheris/trajectory/event.ex:14-35`.

A field suffixed with `?` (e.g. `` `stop_reason?` ``) is optional — the drift check reports INFO when absent rather than FAIL.

| Event type | Payload fields (key ones) |
|-----------|--------------------------|
| `prompt_built` | `system_prompt`, `user_prompt`, `context_hash`, `message_count`, `tool_schema` |
| `llm_called` | `model` |
| `llm_responded` | `response_type`, `output_tokens`, `latency_ms`, `resolved_model`, `cost_usd`, `input_tokens`, `raw_response`, `system_fingerprint`, `tool_name`, `tool_input` |
| `tool_called` | `tool_name`, `tool_input`, `source`, `server_id` |
| `tool_result` | `tool_name`, `output`, `exit_code`, `fs_hash`, `duration_ms`, `result`, `is_error` |
| `error` | `reason`, `detail` |
| `run_complete` | `reason` — `agent_finished` \| `max_steps_reached` \| `error` |
| `step_complete` | `step` |
| `agent_message_sent` | `message_id`, `to_run_id`, `content` |
| `agent_message_received` | `message_id`, `from_run_id`, `content` |
| `observation` | agent-defined structured note |
| `run_cancelled` | emitted when a run is cancelled mid-flight |
| `loop_detected` | emitted when the harness detects a tool-call loop |
| `escalation_requested` | multi-agent: agent is requesting human escalation |
| `escalation_responded` | response to an escalation request |
| `agent_waiting` | `condition`, `timeout_ms` |
| `agent_resumed` | run resumed from wait state |
| `agent_spawned` | `child_run_id`, `spawn_depth` |
| `agent_tree_joined` | child run completed; parent resuming |
| `pre_tool_result` | intermediate result before tool execution |
| `context_summarised` | rolling-context summary was applied |
| `run_orphaned` | `reason`, `last_event_type?` — written by the startup / `mix aetheris sweep` cure when an orphaned `running` run is marked `failed` |

**Note on `run_orphaned`:** unlike every other terminal event, `run_orphaned`
is written *by the harness sweep*, not by the run's own loop — the owning
process is already dead. It records an **event/status asymmetry by design**:
the trajectory event is `run_orphaned` while the `runs.status` it sets is
`failed` (there is no `orphaned` status). `finished_at` is stamped from the
run's **last-event timestamp** — or `started_at` for a run with no events —
**never the sweep time**, so the dormancy gap is not fabricated into the run's
duration. Reconcilable runs (whose trajectory already ends in
`run_complete`/`error`) receive **no** `run_orphaned` event: the sweep adopts
their recorded terminal outcome (`done`/`failed`) instead.

**Note on `cost_usd`:** `cost_usd` is computed by `execution/pricing.ex` and
emitted in `llm_responded` payloads. For unknown models, `cost_usd` is `null`.
`usage.rs` reads `cost_usd` from `llm_responded` events via `json_extract`.

**Legacy payload fields — not promoted (BL-015, #66).** Three field names
observed in the dev DB are **not** listed above because they are superseded
legacy emissions, not canonical fields. Promoting them would legitimize drift.
They remain as `payload_fields` INFOs in `drift_check` until the pre-2026-05-15
rows age out of the DB (DB is read-only to this ticket; not a BL-003 orphan):

- `llm_responded.content` / `llm_responded.type` — the pre-2026-05-15 emission
  shape (56 events, all 2026-05-12). Superseded by `raw_response` /
  `response_type` when the current `execution/loop.ex:241-284` emission landed
  2026-05-15. Canonical readers use `raw_response` / `response_type`.
- `prompt_built.key` — test-fixture payload `{"key":"value"}` (5 events, all
  2026-05-12); no emission source in `loop.ex`. Not a real field.

Stopping the legacy emission is already done in harness source; clearing the
residual INFOs needs a dev-DB reset, tracked separately from this doc ticket.

---

## 7. Config JSON Shape (inside `runs.config_json`)

```json
{
  "run_id":        "...",
  "label":         "Provenance Scan Orchestrator",
  "mode":          "record",
  "provider":      "anthropic",
  "model":         "claude-haiku-4-5-20251001",
  "max_steps":     20,
  "tools":         ["run_command"],
  "sandbox_path":  "...",
  "started_at":    "2026-05-31T..."
}
```

---

## 8. Module Structure

```
rig/src/components/modules/
  harness/
    RunList.tsx              ← HarnessRoute + 3 tabs: Runs, Events, Trajectory (p4)
    TrajectoryView.tsx       ← p4: meta panel + step-grouped event stream
    DiffView.tsx             ← p4: run selection + metadata/step diff
    CapabilityMatrixView.tsx ← p5: collapsible use-case sections, Run buttons
    UsageView.tsx            ← p6: 4 summary cards + by-model/use-case tables
    shared.tsx               ← shared UI helpers
  orchestrator/              ← p3
    OrchestratorView.tsx     ← 7 phases: idle → planning → plan_ready →
                             ←   executing → done | cancelled | error
  docbuilder/                ← p9 (route: /docbuilder)
    DocbuilderView.tsx       ← NL request → rendered document; runs
                             ←   chain_docbuilder.py top-level (.py heuristic),
                             ←   one-click (no approval gate); lists rendered
                             ←   files from output/renamed.json on done
  tools/                     ← p4-tools
    ToolsView.tsx            ← wrapper
    ToolTree.tsx             ← left panel (scripts + Harness + MCP sections)
    ToolDetail.tsx           ← right panel (args form + Run + MCP try)
  settings/                  ← p7 (route: /settings, no sidebar entry)
    AgentConfigTab.tsx       ← grouped env var config (masked fields)
    agentConfigDefs.ts       ← key definitions: Harness/Anthropic/SMTP/Drive/Payslip/Docbuilder/GitHub
  playground/                ← m-playground-p2
    RunComposer.tsx          ← Run Composer panel: policy, sandbox, prompt, submit, status
  provenance/                ← existing
    CorpusOverview.tsx
    ClassificationReview.tsx
    MigrationStatus.tsx
    ZipStatus.tsx
    shared.tsx
```
