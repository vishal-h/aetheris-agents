# Rig — Specifications

---

## 1. Environment Variables

| Variable | Required | Default | Description |
|----------|---------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | — | Path to `aetheris/priv/aetheris.db`; also used by `trajectory.rs` to derive run directory |
| `AETHERIS_AGENTS_PATH` | Yes (orchestrator/tools) | — | Path to `aetheris-agents/` root; used by orchestrate.rs, tools.rs, capability_matrix.rs |
| `AETHERIS_PROVIDER` | No | `anthropic` | Default LLM provider passed to every `.exs` agent; not read by Rig Rust code directly |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | — | Path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | — | Not read by Rig Rust; intended for the `search_agent.exs` file when the corpus-search MCP is active |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No | — | Stored in `agent-config.json`; injected as env var when orchestrator spawns agents — not read from env directly by Rig |

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
    pub run_id:      String,
    pub label:       String,       // from config_json.label
    pub status:      String,
    pub provider:    String,       // from config_json.provider
    pub model:       String,       // from config_json.model
    pub started_at:  String,
    pub finished_at: Option<String>,
    pub step_count:  i64,          // MAX(step) from events
    pub event_count: i64,          // COUNT(*) from events
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
    pub label:       String,
    pub status:      String,
    pub config:      String,       // full config_json
    pub started_at:  String,
    pub finished_at: Option<String>,
    pub events:      Vec<EventRow>,
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

### Orchestrator commands (`commands/orchestrate.rs`) — p3

**`orchestrate_start`** — Takes `request: String`. Returns `job_id: String`.

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
| `agent_config_get_all` | — | `Vec<AgentConfigEntry>` (merged defs + stored values) |
| `agent_config_set` | `key`, `value` | `()` |
| `agent_config_delete` | `key` | `()` |
| `agent_config_export` | `path` (file path) | `()` — writes JSON file |
| `agent_config_import` | `path` (file path) | `()` — merges JSON file into store |

```rust
pub struct AgentConfigEntry {
    pub key:         String,
    pub label:       String,
    pub group:       String,
    pub masked:      bool,
    pub placeholder: Option<String>,
    pub link_prefix: Option<String>,
    pub value:       Option<String>,
}
```

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
  sandbox_path:    string;
  seed:            string | null;
  overlay_changes: unknown[];
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

| Event type | Payload fields (key ones) |
|-----------|--------------------------|
| `prompt_built` | `system_prompt`, `user_prompt`, `context_hash`, `message_count` |
| `llm_called` | `model`, `provider`, `input_tokens`, `cost_usd` |
| `llm_responded` | `response_type`, `output_tokens`, `latency_ms`, `resolved_model`, `cost_usd`, `input_tokens`, `raw_response`, `system_fingerprint` |
| `tool_called` | `tool_name`, `tool_input`, `source`, `server_id` |
| `tool_result` | `tool_name`, `output`, `exit_code`, `fs_hash`, `duration_ms` |
| `error` | `reason`, `step`, `retryable` |
| `run_complete` | `reason` — `agent_finished` \| `max_steps_reached` \| `error` |
| `step_complete` | `step` |
| `agent_message_sent` | `message_id`, `to_run_id`, `content` |
| `agent_message_received` | `message_id`, `from_run_id`, `content` |
| `observation` | agent-defined structured note |
| `run_cancelled` | emitted when a run is cancelled mid-flight |
| `loop_detected` | emitted when the harness detects a tool-call loop |
| `escalation_requested` | multi-agent: agent is requesting human escalation |
| `escalation_responded` | response to an escalation request |
| `agent_waiting` | run entered wait state (e.g. `wait_for_event`) |
| `agent_resumed` | run resumed from wait state |
| `agent_spawned` | child run created via `spawn_agent` |
| `agent_tree_joined` | child run completed; parent resuming |
| `pre_tool_result` | intermediate result before tool execution |
| `context_summarised` | rolling-context summary was applied |

**Note on `cost_usd`:** `llm_called` emits `cost_usd` (computed by
`execution/pricing.ex`); `llm_responded` also carries `cost_usd` for
convenience. For unknown models, `cost_usd` is `null`. `usage.rs` reads
`cost_usd` from `llm_called` events via `json_extract`.

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
  tools/                     ← p4-tools
    ToolsView.tsx            ← wrapper
    ToolTree.tsx             ← left panel (scripts + Harness + MCP sections)
    ToolDetail.tsx           ← right panel (args form + Run + MCP try)
  settings/                  ← p7 (route: /settings, no sidebar entry)
    AgentConfigTab.tsx       ← grouped env var config (masked fields)
    agentConfigDefs.ts       ← key definitions: Harness/Anthropic/SMTP/Drive/Payslip/GitHub
  provenance/                ← existing
    CorpusOverview.tsx
    ClassificationReview.tsx
    MigrationStatus.tsx
    ZipStatus.tsx
    shared.tsx
```
