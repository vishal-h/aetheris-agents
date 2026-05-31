# Rig — Specifications

---

## 1. Environment Variables

| Variable | Required | Default | Description |
|----------|---------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | — | Path to `aetheris/priv/aetheris.db` |
| `AETHERIS_AGENTS_PATH` | Yes (orchestrator) | — | Path to `aetheris-agents/` root |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | — | Path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | — | Enable corpus-search MCP in search agent |

---

## 2. Harness DB Schema (read from aetheris.db)

Tables Rig reads. Schema is owned by the harness — never written by Rig.

### `runs`
```sql
CREATE TABLE runs (
  run_id       TEXT PRIMARY KEY,
  status       TEXT,          -- idle | running | paused | done | failed
  config_json  TEXT,          -- JSON: RunConfig snapshot
  started_at   TEXT,          -- ISO 8601
  finished_at  TEXT           -- ISO 8601 | NULL
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
  agent_run_ids TEXT,         -- JSON array of run_ids
  status        TEXT,         -- running | done | failed
  started_at    TEXT,
  finished_at   TEXT
);
```

### `skills`
```sql
CREATE TABLE skills (
  id               TEXT PRIMARY KEY,
  name             TEXT,
  description      TEXT,
  prompt_template  TEXT,
  tool_sequence    TEXT,
  step_count       INTEGER,
  examples_json    TEXT,
  extracted_at     TEXT
);
```

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
}

interface OrchestratorPlan {
  type:    'plan';
  request: string;
  steps:   PlanStep[];
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

---

## 6. Event Type Reference

| Event type | Payload fields (key ones) |
|-----------|--------------------------|
| `prompt_built` | `system_prompt`, `user_prompt`, `context_hash`, `message_count` |
| `llm_called` | `model`, `provider`, `input_tokens` |
| `llm_responded` | `response_type`, `output_tokens`, `latency_ms`, `resolved_model` |
| `tool_called` | `tool_name`, `tool_input`, `source`, `server_id` |
| `tool_result` | `tool_name`, `output`, `exit_code`, `fs_hash`, `duration_ms` |
| `error` | `reason`, `step`, `retryable` |
| `run_complete` | `reason` — `agent_finished` \| `max_steps_reached` \| `error` |
| `step_complete` | `step` |
| `agent_message_sent` | `message_id`, `to_run_id`, `content` |
| `agent_message_received` | `message_id`, `from_run_id`, `content` |

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
    RunList.tsx          ← HarnessRoute + 3 tabs: Runs, Events, Trajectory (p4)
    TrajectoryView.tsx   ← p4: meta panel + step-grouped event stream
    DiffView.tsx         ← p4: run selection + metadata/step diff
  orchestrator/          ← p3
    OrchestratorView.tsx
  provenance/            ← existing
    CorpusOverview.tsx
    ClassificationReview.tsx
    MigrationStatus.tsx
    ZipStatus.tsx
    shared.tsx
```
