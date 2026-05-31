# Rig — AI Working Context

## Location

This app lives at `aetheris-agents/rig/`. The aetheris harness repo is
at `../aetheris/` (sibling directory). Claude Code must run from
`aetheris-agents/rig/` for all Rig work.

---

## What This Is

Rig is a cross-platform desktop app built with Tauri v2. It is a personal tool host — a single binary housing multiple unrelated modules under a shared app shell. Not a SaaS product. No telemetry. All data local.

Current module: **F2 — File & Folder**
- **F2O:** Operations (deduplication, file indexing)
- **F2V:** Viewer (virtual filesystem views)

Full documentation in `docs/`.

### Provenance

Rig is the reporting and analytics dashboard for **Provenance** — an intelligent
document management system for audit firms built on the Aetheris agent harness.

In the Provenance architecture:
- **Aetheris** drives all intelligence: scanning, classification, migration, search
- **Rig** reads results from the shared DuckDB corpus and surfaces them to users
- **DuckDB** is the handoff point — Aetheris writes, Rig reads

Rig does not trigger scans, classify documents, or execute migrations.
Those responsibilities belong entirely to Aetheris agents.

See `aetheris-agents/docs/provenance/` for the full Provenance architecture,
specs, and roadmap.

---

## Stack at a Glance

| Layer | Tech |
|---|---|
| App framework | Tauri v2 |
| Frontend | React 18 + TypeScript + Vite + Bun |
| Styling | Tailwind CSS + shadcn/ui |
| Storage | DuckDB (via duckdb-rs, bundled) |
| Backend | Rust |
| Async runtime | Tokio (via Tauri) |
| Filesystem walk | walkdir crate |
| Hashing | sha2 crate |
| System info | sysinfo crate |
| Glob matching | glob crate |
| Icons | lucide-react |
| Routing | react-router-dom (MemoryRouter) |

---

## Project Structure

```
rig/
├── src/                        # React frontend
│   ├── components/
│   │   ├── shell/              # TopBar, Sidebar, MainArea, RightPanel
│   │   └── modules/
│   │       └── f2/             # F2O and F2V components
│   ├── context/                # App-wide React context
│   ├── hooks/                  # Custom hooks wrapping invoke() calls
│   │   ├── types.ts            # Shared TypeScript types matching Rust structs
│   │   ├── useFileIndex.ts
│   │   ├── useDuplicates.ts
│   │   ├── useWatchedFolders.ts
│   │   └── useScanStatus.ts
│   ├── lib/
│   │   └── utils.ts            # cn(), formatBytes(), formatDate()
│   ├── modules/
│   │   └── registry.ts         # Frontend module registration
│   ├── App.tsx
│   └── main.tsx
│
├── src-tauri/                  # Rust backend
│   ├── src/
│   │   ├── main.rs             # Entry point
│   │   ├── lib.rs              # App setup, DB init, command registration
│   │   ├── commands/           # Tauri command handlers
│   │   │   └── f2.rs           # All F2 commands
│   │   ├── db/                 # DuckDB init, migrations
│   │   │   ├── mod.rs
│   │   │   └── migrations.rs
│   │   └── modules/            # Business logic
│   │       └── f2/
│   │           └── scanner.rs  # DEPRECATED — see Provenance note below
│   └── Cargo.toml
│
├── docs/
│   ├── architecture.md
│   ├── specs.md
│   └── runbook.md
│
├── README.md
└── CLAUDE.md                   # This file
```

---

## Key Architectural Rules

**1. The frontend never touches data directly.**
All DB access, filesystem operations, and hashing go through Tauri commands. React is a pure view layer.

**2. Commands are the only bridge.**
Frontend calls backend via `invoke('command_name', { ...args })`. Backend responds with typed results. Tauri events (`emit`/`listen`) are used for backend-initiated updates where needed.

**3. One file per module in commands/.**
`src-tauri/src/commands/f2.rs` contains all F2 command handlers. A new module gets its own file.

**4. Module registration happens in exactly two places.**
- Frontend: `src/modules/registry.ts`
- Backend: `src-tauri/src/lib.rs` in `generate_handler![]`

**5. DuckDB is the single source of truth.**
No frontend state is persisted. React state is ephemeral. Data comes from DuckDB on load.
In Provenance mode, DuckDB is populated by Aetheris agents — not by this app.

**6. Network calls are on-demand only.**
F2 makes zero network calls. Data comes from DuckDB reads.

**7. Scanning is owned by Aetheris. Do not restore it here.**
`src-tauri/src/modules/f2/scanner.rs` has been extracted to
`aetheris-agents/provenance/scanner/` and is maintained there.
This app no longer triggers directory scans. The Tauri events `scan-progress`
and `scan-complete` are no longer emitted — scan status is read from the
`scan_runs` table in DuckDB instead.
**Do not add scan triggering, progress events, or file hashing back to this app.**

**8. No destructive actions without explicit user confirmation.**
Files are never deleted automatically. Any destructive action (migration approval,
duplicate deletion) requires explicit user confirmation and is executed by
Aetheris, not by this app.

**9. F2Operations and F2Viewer are tab factory functions, not React components.**
Call them as `F2Operations()` and `F2Viewer()` to get `Tab[]`, then pass to `MainArea` via `tabs` prop. Do not use JSX syntax `<F2Operations />`.

---

## Provenance integration

Rig connects to the Provenance corpus DuckDB populated by Aetheris agents.

**DB path:** read from `PROVENANCE_DB_PATH` environment variable.
Do not use `app_data_dir()` for the corpus DB — it lives on the server, not the
local machine. Rig connects to it over VPN.

**Read-only:** All Provenance DuckDB access from Rig is read-only. Rig never
writes to the corpus. Writes are owned by Aetheris agents and their scripts.

**Available views** (defined by Aetheris, read by Rig):
- `client_corpus` — classified files by client / FY / doc_type
- `duplicate_groups` — files grouped by SHA-256 with count > 1
- `migration_queue` — approved classifications not yet migrated
- `zip_backlog` — zips pending processing

**Available tables relevant to reporting:**
- `f2_file_index` — full file index with status
- `scan_runs` — scan history and progress
- `classifications` — per-file classification with confidence and review status
- `migrations` — migration log with source, dest, status, timestamp
- `zip_inventory` — zip file processing status

**Classification review workflow:**
Rig surfaces proposed classifications (status = 'proposed') for human review.
Approve/reject actions write back to the `classifications` table
(`status = 'approved'` or `'rejected'`). This is the one write path Rig owns —
classification review is a human action, not an agent action.

---

## Harness DB (aetheris.db)

Rig reads the harness SQLite database at `AETHERIS_DB_PATH` for run
inspection features. Uses `rusqlite` with `bundled` feature.

Connection opened read-only at startup in `HarnessState`:

  pub struct HarnessState {
      pub conn: Option<Arc<Mutex<rusqlite::Connection>>>,
      pub path: Option<String>,
  }

If `AETHERIS_DB_PATH` is absent, `conn` is None and all harness commands
return Err("harness not connected") — **except `harness_connection_status`**,
which always returns `Ok(HarnessStatus { connected: false, error: Some(...) })`.
Check `data.connected` to gate the UI, not the Result.

**Never write to aetheris.db.** Open with SQLITE_OPEN_READ_ONLY always.

SQLite timestamp columns are TEXT in ISO 8601 format — no casting needed
(unlike DuckDB's TIMESTAMP type).

---

## Tauri invoke() argument naming

Tauri v2 deserializes command arguments by converting JS camelCase keys to Rust snake_case.
**Use camelCase keys in all `invoke()` calls.** This is the only form that is reliably safe.

```typescript
// Rust: pub fn trajectory_load(run_id: String) -> ...
invoke('trajectory_load', { runId })          // ✓ camelCase key → run_id parameter
invoke('trajectory_load', { run_id: runId })  // ✗ fails — "missing required key runId"
```

**Why `{ run_id: runId }` fails:** Tauri's pipeline converts camelCase → snake_case. A key
that is already snake_case (`run_id`) is not valid camelCase input and does not survive
the conversion correctly. Empirically, explicit snake_case keys like `{ job_id: jobId }`
have worked in some commands (P3), but `{ run_id: runId }` does not. Do not rely on
snake_case passthrough — camelCase keys are the only form that is consistently safe.

Error form: `invalid args runId for command X: missing required key runId`

---

## React / Frontend patterns

**`useState(prefill)` seeding from `useLocation().state`.**
To pre-fill a controlled input on navigation, derive the prefill from `useLocation()`
before the `useState` call, then pass it as the initial value:
```typescript
const location = useLocation();
const prefill  = (location.state as { prefill?: string } | null)?.prefill ?? '';
const [request, setRequest] = useState(prefill);
```
Seeded once on mount. Do NOT use `useEffect` — that causes a blank→filled flash.
No-state navigation gives `prefill = ''`; behaviour unchanged.
Pattern used in `OrchestratorView.tsx`.

**Default-expanded collapsible groups.**
Use `expanded[label] !== false` (not `=== true`) so groups start expanded without
initialising the full map. An absent key (`undefined`) evaluates as `true`; setting
`false` explicitly collapses the group:
```typescript
function isGroupExpanded(label: string): boolean {
  return expanded[label] !== false; // default expanded
}
```
Pattern used in `RunList.tsx`.

**`e.stopPropagation()` on nested clickables.**
When a `<button>` sits inside a clickable row or container, always call
`e.stopPropagation()` to prevent the parent `onClick` from also firing:
```tsx
<button onClick={(e) => { e.stopPropagation(); toggleShowAll(label); }}>
  Show more…
</button>
```
Pattern used in `RunList.tsx` show-more button (inside a clickable group-header row).

**Filter before group.**
Always apply filters to the flat list before calling `groupRuns()`. Empty groups
disappear naturally. Never filter after grouping — counts and membership would be stale:
```typescript
const filtered = runs.filter((r) => statusFilter === 'all' || r.status === statusFilter);
const groups   = groupRuns(filtered);
```
Pattern used in `RunList.tsx`.

---

## Database gotchas

SQLite and DuckDB have different type systems — do not mix up casting rules between them. SQLite timestamps are TEXT (no cast needed); DuckDB timestamps require `CAST(col AS VARCHAR)`. The rules below apply to DuckDB only.

These rules were learned during v0.2 development. Violating them causes runtime errors, not compile errors.

**Rule D1 — No implicit TIMESTAMP reads.**
DuckDB `TIMESTAMP` columns cannot be read directly as Rust `String`. Always cast in the query:
```sql
SELECT CAST(created_at AS VARCHAR) as created_at FROM my_table
```
Applies to any column of type `TIMESTAMP`, `DATE`, or `INTERVAL` being mapped to a String field.

**Rule D2 — Unix seconds need to_timestamp() on INSERT.**
DuckDB will not implicitly cast a `BIGINT` (Unix epoch seconds) to `TIMESTAMP`. Use `to_timestamp()`:
```sql
INSERT INTO my_table (created_at) VALUES (to_timestamp(?))
```

**Rule D3 — Explicit conflict target on upsert.**
If a table has multiple UNIQUE or PRIMARY KEY constraints, `INSERT OR REPLACE` will fail. Always specify the conflict column explicitly:
```sql
INSERT INTO my_table (path, ...) VALUES (?, ...)
ON CONFLICT (path) DO UPDATE SET col = excluded.col
```

**Rule D4 — No auto-increment without SEQUENCE.**
DuckDB does not auto-increment `INTEGER PRIMARY KEY` like SQLite. Define a sequence and use `DEFAULT nextval()`:
```sql
CREATE SEQUENCE IF NOT EXISTS seq_my_table;
CREATE TABLE my_table (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_my_table'),
    ...
);
```

**Rule D5 — Use now() not CURRENT_TIMESTAMP in expressions.**
`CURRENT_TIMESTAMP` is not recognised as a keyword in DuckDB `DO UPDATE SET` clauses. Use `now()` instead:
```sql
ON CONFLICT (path) DO UPDATE SET last_scanned = now()
```

**Rule D6 — sysinfo 0.30 API.**
The correct method names for sysinfo 0.30 are:
- Use `sys.refresh_cpu()` (not `refresh_cpu_all()`)
- Use `sys.global_cpu_info().cpu_usage()` (not `global_cpu_usage()`)

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Tauri commands | snake_case | `f2_get_duplicates`, `f2_get_corpus_summary` |
| React components | PascalCase | `CorpusOverview`, `ClassificationReview` |
| Custom hooks | camelCase, `use` prefix | `useDuplicates`, `useClassifications` |
| DB tables | `<module>_<table>` | `f2_file_index`, `f2_watched_folders` |
| DB sequences | `seq_<table>` | `seq_f2_file_index` |
| Files (frontend) | PascalCase for components | `CorpusOverview.tsx` |
| Files (backend) | snake_case | `corpus.rs` |
| Context files | PascalCase + Context suffix | `AppContext.tsx` |
| Tauri events | kebab-case | `classification-updated` |

---

## Running the App

```bash
# Set DB path before running
export PROVENANCE_DB_PATH=/path/to/corpus.duckdb

# Dev mode
cargo tauri dev

# Production build
cargo tauri build
# Output: src-tauri/target/release/bundle/
```

---

## Adding a New Module

1. Create `src/components/modules/<n>/` with React views
2. Add module definition to `src/modules/registry.ts`
3. Create `src-tauri/src/commands/<n>.rs` with command handlers
4. Register commands in `src-tauri/src/lib.rs`
5. Add DB migrations in `src-tauri/src/db/migrations.rs`
6. Tables must be prefixed `<module>_`
7. Create sequences for all integer primary keys (Rule D4)

---

## What Not To Do

- **Don't add Redux or Zustand.** React context + hooks is sufficient.
- **Don't access the filesystem from the frontend.** All file operations go through Rust commands.
- **Don't load entire files into memory for hashing.** Use streaming SHA-256.
- **Don't add a second database.** DuckDB handles everything.
- **Don't poll or auto-refresh from the frontend.** Use Tauri events from the backend.
- **Don't perform destructive file operations without user confirmation.**
- **Don't use `any` in TypeScript.** Type all Tauri command responses.
- **Don't hardcode paths.** Use `PROVENANCE_DB_PATH` env var for corpus DB.
- **Don't use `INSERT OR REPLACE` on tables with multiple unique constraints.** Use `ON CONFLICT (col) DO UPDATE SET` (Rule D3).
- **Don't read TIMESTAMP columns as String without CAST.** Always `CAST(col AS VARCHAR)` (Rule D1).
- **Don't use `INTEGER PRIMARY KEY` without a sequence.** DuckDB won't auto-increment it (Rule D4).
- **Don't use `BrowserRouter`.** Tauri requires `MemoryRouter`.
- **Don't render F2Operations or F2Viewer as JSX.** Call them as functions.
- **Don't add explicit `@radix-ui/*` sub-packages to package.json.** The `radix-ui` meta-package already includes all of them.
- **Don't restore scan triggering or file hashing.** The scanner lives in `aetheris-agents/provenance/scanner/`. Rig reads scan results from DuckDB; it does not produce them.
- **Don't write to corpus tables other than `classifications`.** All other writes are owned by Aetheris.

---

## Current Focus

### Provenance dashboard (active)
- [ ] Corpus overview — total files, unique, duplicates, size by client/FY (F2O)
- [ ] Classification review UI — approve/reject proposed classifications (F2O)
- [ ] Migration status view — what's been moved, what's pending, what failed (F2O)
- [ ] Scan run history — last scan, files scanned, duplicates found (F2O)
- [ ] Virtual corpus browser — navigate client/FY/doc_type tree (F2V)
- [ ] Zip inventory view — zip processing status and backlog (F2O)
- [ ] Agent run history — Aetheris trajectory index surfaced in UI (F2O)

### Deferred
- [ ] F2O — move duplicates to duplicates folder (superseded by Provenance migration)
- [ ] F2O — right panel file detail view
- [ ] F2V — labels (apply, remove, persist)
- [ ] F2V — file actions (open, show in files, terminal here)
- [ ] Settings — OS folder picker dialog (Tauri dialog plugin)
- [ ] Settings — theme persistence to DuckDB

### Completed
- [x] App shell — TopBar, Sidebar, MainArea, RightPanel
- [x] DuckDB setup + migrations (f2 tables + sequences)
- [x] F2O — background scanner (extracted to aetheris-agents/provenance/scanner/)
- [x] F2O — Index tab with real data
- [x] F2O — Duplicates tab with real data
- [x] Settings — Watched Folders UI
