# Rig — Specifications

---

## 1. Environment Variables

| Variable | Required | Default | Description |
|----------|---------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | — | Path to `aetheris/priv/aetheris.db` |
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

## 3. Tauri Command Shapes

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
    pub id:        String,
    pub run_id:    String,
    pub step:      i64,
    pub seq:       i64,
    pub event_type: String,
    pub payload:   String,         // raw JSON string
    pub timestamp: String,
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

---

## 4. TypeScript Interfaces

```typescript
// Harness
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
  payload:     string;   // raw JSON — parse per event_type
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
```

---

## 5. Event Type Reference

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

## 6. Config JSON Shape (inside `runs.config_json`)

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

## 7. Module Structure

```
rig/src/components/modules/
  harness/
    RunList.tsx          ← tab factory: run list + event log
  orchestrator/          ← p3
    Orchestrator.tsx
  provenance/            ← existing
    CorpusOverview.tsx
    ClassificationReview.tsx
    MigrationStatus.tsx
    ZipStatus.tsx
    shared.tsx
```
