# hai-rig/m6: Corpus DB connection + Tauri commands

## Context

The Provenance corpus lives in a DuckDB file on the server, populated by
Aetheris agents. Rig connects to it read-only over VPN. This issue wires up
the backend connection and exposes the Tauri commands that all Provenance UI
tabs will use.

All work is in the **hai-rig** repo.

## What to build

### `src-tauri/src/commands/provenance.rs`

New command file following the pattern in `src-tauri/src/commands/f2.rs`.

**Connection setup:** `src-tauri/src/lib.rs` already initialises `app_conn`.
Add `corpus_conn: Option<Arc<Mutex<Connection>>>` to the app state, opened
from `PROVENANCE_DB_PATH` at startup with `read_only=true`. If the env var is
absent or the file is not found, `corpus_conn` is `None` — commands return
an error that the frontend renders as "corpus not connected".

```rust
// In lib.rs setup:
let corpus_conn = match std::env::var("PROVENANCE_DB_PATH") {
    Ok(path) => match Connection::open_with_flags(&path, AccessMode::ReadOnly) {
        Ok(conn) => Some(Arc::new(Mutex::new(conn))),
        Err(e) => { log::warn!("Cannot open corpus DB {}: {}", path, e); None }
    },
    Err(_) => None,
};
```

### Tauri commands to implement

All commands return `Result<T, String>`. All return `Err("corpus not connected".to_string())` when `corpus_conn` is `None`.

---

**`provenance_corpus_summary`** → `CorpusSummary`

```rust
pub struct CorpusSummary {
    pub total_files: i64,
    pub unique_files: i64,        // distinct sha256
    pub duplicate_files: i64,
    pub total_size_bytes: i64,
    pub unique_size_bytes: i64,
    pub wasted_bytes: i64,
    pub classified_files: i64,    // classifications count
    pub migrated_files: i64,      // migrations with status='migrated'
    pub zip_files: i64,
    pub last_scan_at: Option<String>,  // CAST as VARCHAR (Rule D1)
}
```

---

**`provenance_client_breakdown`** → `Vec<ClientRow>`

```rust
pub struct ClientRow {
    pub client: String,
    pub file_count: i64,
    pub total_size_bytes: i64,
    pub migrated_count: i64,
    pub doc_types: Vec<String>,    // ARRAY_AGG(DISTINCT doc_type)
}
```

Query joins `classifications` with `f2_file_index` and `migrations`.

---

**`provenance_scan_runs`** → `Vec<ScanRun>`

```rust
pub struct ScanRun {
    pub id: String,
    pub root_path: String,
    pub status: String,
    pub files_scanned: i64,
    pub duplicates_found: i64,
    pub started_at: String,        // CAST(started_at AS VARCHAR) — Rule D1
    pub finished_at: Option<String>,
    pub duration_secs: Option<i64>,
}
```

---

**`provenance_classification_list`** → `Vec<ClassificationRow>`

Takes optional filters: `client: Option<String>`, `status: Option<String>`,
`limit: i64` (default 100).

```rust
pub struct ClassificationRow {
    pub path: String,
    pub client: String,
    pub financial_year: String,
    pub doc_type: String,
    pub confidence: f64,
    pub status: String,
    pub raw_excerpt: String,
    pub classified_at: String,    // Rule D1
    pub reviewed_by: Option<String>,
}
```

---

**`provenance_set_classification_status`**

Takes `path: String`, `status: String` (`"approved"` or `"rejected"`),
`reviewer: String`.

This is the one write command. Opens a **separate read-write connection**
(not `corpus_conn` which is read-only) for the single UPDATE, then closes it:

```rust
let write_conn = Connection::open(&corpus_path)?;
write_conn.execute(
    "UPDATE classifications SET status=?, reviewed_by=?, reviewed_at=now() WHERE path=?",
    [&status, &reviewer, &path],
)?;
```

Returns `Result<(), String>`.

---

**`provenance_migration_summary`** → `MigrationSummary`

```rust
pub struct MigrationSummary {
    pub total: i64,
    pub migrated: i64,
    pub failed: i64,
    pub pending: i64,             // approved but not yet migrated
    pub by_client: Vec<MigrationClientRow>,
}

pub struct MigrationClientRow {
    pub client: String,
    pub migrated: i64,
    pub failed: i64,
    pub pending: i64,
}
```

---

**`provenance_zip_inventory`** → `ZipInventory`

```rust
pub struct ZipInventory {
    pub total: i64,
    pub processed: i64,
    pub encrypted: i64,
    pub pending: i64,
    pub failed: i64,
    pub new_to_corpus: i64,        // SUM(new_to_corpus) from zip_inventory
    pub largest_zips: Vec<ZipRow>,  // top 10 by size
}

pub struct ZipRow {
    pub path: String,
    pub size_bytes: i64,
    pub status: String,
    pub contents_count: Option<i64>,
    pub new_to_corpus: Option<i64>,
}
```

### Registration

In `src-tauri/src/lib.rs`, add all new commands to `generate_handler![]`:
```rust
provenance_corpus_summary,
provenance_client_breakdown,
provenance_scan_runs,
provenance_classification_list,
provenance_set_classification_status,
provenance_migration_summary,
provenance_zip_inventory,
```

### TypeScript types

In `src/hooks/types.ts`, add TypeScript interfaces matching each Rust struct.

### Connection status hook

`src/hooks/useProvenanceStatus.ts` — a simple hook that calls
`provenance_corpus_summary` and returns `{connected: boolean, error: string | null}`.
Used by all Provenance tabs to render "not connected" gracefully.

## Acceptance criteria

- [ ] `corpus_conn` opened read-only when `PROVENANCE_DB_PATH` is set
- [ ] All commands return `Err("corpus not connected")` when env var absent
- [ ] All 7 commands compile and return correct shapes against the fixture DB
- [ ] `provenance_set_classification_status` uses a separate write connection
- [ ] All TIMESTAMP columns cast to VARCHAR (Rule D1)
- [ ] All commands registered in `generate_handler![]`
- [ ] TypeScript interfaces in `types.ts` for all return types
- [ ] `useProvenanceStatus` hook works
- [ ] `cargo build` clean, no warnings
- [ ] Existing F2 module unaffected

## Files to create/modify

- `src-tauri/src/commands/provenance.rs` (new)
- `src-tauri/src/commands/mod.rs` (add provenance module)
- `src-tauri/src/lib.rs` (add corpus_conn, register commands)
- `src/hooks/types.ts` (add TypeScript interfaces)
- `src/hooks/useProvenanceStatus.ts` (new)

## Notes

**`AccessMode::ReadOnly`** is in `duckdb::AccessMode`. Use
`Connection::open_with_flags` not `Connection::open` for the corpus connection.

**Corpus path for write connection.** `provenance_set_classification_status`
needs to re-read `PROVENANCE_DB_PATH` to get the path for the write connection.
Store it in app state alongside the read connection, not just the connection handle.

**`ARRAY_AGG` result type.** DuckDB's `ARRAY_AGG` returns a DuckDB list type.
Map it to `Vec<String>` via `row.get::<_, Vec<String>>(N)`. If this fails with
the duckdb-rs version in use, fall back to a comma-separated string and split
in Rust.
