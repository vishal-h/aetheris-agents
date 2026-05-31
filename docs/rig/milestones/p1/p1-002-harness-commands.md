# rig/p1: Harness DB commands

## Context

With `rusqlite` in place, this issue wires up the SQLite connection to
`aetheris.db` and exposes the Tauri commands that the run list UI will use.

All work is in `aetheris-agents/rig/`.

## What to build

### `src-tauri/src/commands/harness.rs`

New command file following the pattern in `commands/provenance.rs`.

**State struct** (add to `src-tauri/src/lib.rs`):

```rust
pub struct HarnessState {
    pub conn: Option<Arc<Mutex<rusqlite::Connection>>>,
    pub path: Option<String>,
}
```

**Connection setup** (in `lib.rs` setup closure):

```rust
let harness_state = match std::env::var("AETHERIS_DB_PATH") {
    Ok(path) => {
        match rusqlite::Connection::open_with_flags(
            &path,
            rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY
                | rusqlite::OpenFlags::SQLITE_OPEN_NO_MUTEX,
        ) {
            Ok(conn) => {
                log::info!("Harness DB opened: {}", path);
                HarnessState {
                    conn: Some(Arc::new(Mutex::new(conn))),
                    path: Some(path),
                }
            }
            Err(e) => {
                log::warn!("Cannot open harness DB {}: {}", path, e);
                HarnessState { conn: None, path: None }
            }
        }
    }
    Err(_) => {
        log::info!("AETHERIS_DB_PATH not set — harness commands unavailable");
        HarnessState { conn: None, path: None }
    }
};
app.manage(harness_state);
```

### Commands to implement

All commands return `Result<T, String>` and return
`Err("harness not connected".to_string())` when `conn` is None.

---

**`harness_connection_status`** → `HarnessStatus`

```rust
pub struct HarnessStatus {
    pub connected: bool,
    pub db_path:   Option<String>,
    pub run_count: i64,
    pub error:     Option<String>,
}
```

Query: `SELECT COUNT(*) FROM runs`

---

**`harness_list_runs`**

Takes `limit: Option<i64>` (default 50). Returns `Vec<RunSummary>`.

```rust
pub struct RunSummary {
    pub run_id:      String,
    pub label:       String,
    pub status:      String,
    pub provider:    String,
    pub model:       String,
    pub started_at:  String,
    pub finished_at: Option<String>,
    pub step_count:  i64,
    pub event_count: i64,
}
```

Query:
```sql
SELECT
    r.run_id,
    COALESCE(
        json_extract(r.config_json, '$.label'),
        r.run_id
    ) AS label,
    r.status,
    COALESCE(json_extract(r.config_json, '$.provider'), '') AS provider,
    COALESCE(json_extract(r.config_json, '$.model'), '')    AS model,
    r.started_at,
    r.finished_at,
    COALESCE((SELECT MAX(e.step)   FROM events e WHERE e.run_id = r.run_id), 0) AS step_count,
    COALESCE((SELECT COUNT(*)      FROM events e WHERE e.run_id = r.run_id), 0) AS event_count
FROM runs r
ORDER BY r.started_at DESC
LIMIT ?
```

---

**`harness_get_events`**

Takes `run_id: String`. Returns `Vec<EventRow>`.

```rust
pub struct EventRow {
    pub id:         String,
    pub run_id:     String,
    pub step:       i64,
    pub seq:        i64,
    pub event_type: String,
    pub payload:    String,   // raw JSON string
    pub timestamp:  String,
}
```

Query:
```sql
SELECT id, run_id, step, seq, type, payload_json, timestamp
FROM events
WHERE run_id = ?
ORDER BY seq ASC
```

---

**`harness_get_run`**

Takes `run_id: String`. Returns `RunDetail`.

```rust
pub struct RunDetail {
    pub run_id:      String,
    pub label:       String,
    pub status:      String,
    pub config:      String,
    pub started_at:  String,
    pub finished_at: Option<String>,
}
```

Query:
```sql
SELECT
    run_id,
    COALESCE(json_extract(config_json, '$.label'), run_id) AS label,
    status,
    config_json,
    started_at,
    finished_at
FROM runs
WHERE run_id = ?
```

### TypeScript types

Add to `src/hooks/types.ts`:

```typescript
export interface HarnessStatus {
  connected:  boolean;
  db_path:    string | null;
  run_count:  number;
  error:      string | null;
}

export interface RunSummary {
  run_id:      string;
  label:       string;
  status:      'idle' | 'running' | 'paused' | 'done' | 'failed' | string;
  provider:    string;
  model:       string;
  started_at:  string;
  finished_at: string | null;
  step_count:  number;
  event_count: number;
}

export interface EventRow {
  id:          string;
  run_id:      string;
  step:        number;
  seq:         number;
  event_type:  string;
  payload:     string;
  timestamp:   string;
}

export interface RunDetail {
  run_id:      string;
  label:       string;
  status:      string;
  config:      string;
  started_at:  string;
  finished_at: string | null;
}
```

### `src/hooks/useHarness.ts`

```typescript
export function useHarnessStatus(): AsyncState<HarnessStatus>
export function useRunList(limit?: number): AsyncState<RunSummary[]>
export function useRunEvents(runId: string | null): AsyncState<EventRow[]>
export function useRunDetail(runId: string | null): AsyncState<RunDetail>
```

Use the `useInvoke` generic helper from `useCorpusOverview.ts` as a pattern.
`useRunEvents` and `useRunDetail` should not fetch when `runId` is null.

### Registration

In `src-tauri/src/lib.rs`, add to `generate_handler![]`:

```rust
commands::harness::harness_connection_status,
commands::harness::harness_list_runs,
commands::harness::harness_get_events,
commands::harness::harness_get_run,
```

Add `pub mod harness;` to `commands/mod.rs`.

## Acceptance criteria

- [ ] `HarnessState` in `lib.rs` with read-only SQLite connection
- [ ] All 4 commands compile and return correct shapes
- [ ] `harness_list_runs` returns runs ordered by `started_at DESC`
- [ ] `harness_get_events` returns events ordered by `seq ASC`
- [ ] `json_extract` used to read `label`, `provider`, `model` from `config_json`
- [ ] All commands return `Err("harness not connected")` when env var absent
- [ ] TypeScript interfaces added to `types.ts`
- [ ] `useHarness.ts` hooks implemented
- [ ] Commands registered in `lib.rs` and `commands/mod.rs`
- [ ] `cargo build` clean, no warnings
- [ ] Existing Provenance commands unaffected

## Notes

**SQLite `json_extract`.** SQLite has built-in JSON support via
`json_extract(column, '$.key')`. Use it to read fields from
`config_json` without deserialising in Rust. Returns NULL if the key
is absent — use `COALESCE` to provide defaults.

**`rusqlite` row mapping.** Use `row.get::<_, Option<String>>(N)?` for
nullable columns. `finished_at` is NULL for running/failed runs where
the harness crashed before writing it.

**No JOIN on events for list query.** The list query uses correlated
subqueries for `step_count` and `event_count` rather than a JOIN to
avoid duplicating run rows. For 50 runs this is fast enough; revisit
if the list query becomes slow on large DBs.
