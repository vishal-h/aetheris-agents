# Milestone: v0.2 — F2O Scanner

## Milestone Description
Builds the Rust backend for F2O: DuckDB initialisation, migrations, file scanner (walkdir + sha2 + sysinfo), Tauri command bridge, and wires the frontend Index and Duplicates tabs to real data. At the end of this milestone, Rig will scan a watched folder, hash every file, store results in DuckDB, and display the file index and duplicate groups in the UI.

**No file move/delete operations in this milestone.** The Duplicates tab shows groups for review only. Moving files is v0.3.

## Metadata
- **Repo:** swiftekin/hai-rig
- **Milestone:** v0.2 — F2O Scanner
- **Labels to create before importing:** `rust`, `backend`, `f2`, `frontend`, `dx`

---
---

## TICKET-01: Rust dependencies — Cargo.toml

**Labels:** `rust`, `backend`, `dx`
**Depends on:** none (Rust side)

### Summary
Add all Rust crate dependencies required for the F2O scanner to `src-tauri/Cargo.toml`.

### Context
The scanner needs `walkdir` for directory traversal, `sha2` for streaming SHA-256 hashing, `sysinfo` for CPU utilisation checks, and `duckdb` for the embedded database. These must be added before any Rust implementation tickets run.

### Scope
**Modify:**
- `src-tauri/Cargo.toml`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `walkdir = "2"` added to `[dependencies]`
- [ ] `sha2 = "0.10"` added to `[dependencies]`
- [ ] `digest = "0.10"` added to `[dependencies]` (required by sha2)
- [ ] `sysinfo = "0.30"` added to `[dependencies]`
- [ ] `duckdb = { version = "1", features = ["bundled"] }` added to `[dependencies]`
- [ ] `hex = "0.4"` added to `[dependencies]` (for SHA hex encoding)
- [ ] `mime_guess = "2"` added to `[dependencies]` (for MIME type detection)
- [ ] `serde = { version = "1", features = ["derive"] }` added (if not already present)
- [ ] `tokio = { version = "1", features = ["full"] }` added (if not already present — Tauri uses it)
- [ ] `cargo check` passes with no errors after adding deps

### Agentic Instructions
**Follow:**
- Use `features = ["bundled"]` for duckdb — this compiles DuckDB from source and avoids system library dependency. Build will be slower first time but produces a fully self-contained binary.
- Check existing `[dependencies]` entries before adding — `serde` and `tokio` may already be present from the Tauri scaffold.

**Do not:**
- Add any `.rs` source files in this ticket
- Modify frontend files
- Change Tauri configuration

### References
- [CLAUDE.md](CLAUDE.md)
- [docs/architecture.md](docs/architecture.md)

---
---

## TICKET-02: DuckDB init and migrations

**Labels:** `rust`, `backend`
**Depends on:** TICKET-01

### Summary
Create the Rust database module that initialises DuckDB on app start, runs schema migrations in order, and exposes a connection pool to the rest of the backend.

### Context
DuckDB is initialised once when the app starts. The database file lives in the OS app data directory (resolved at runtime via Tauri's `app_data_dir()`). Migrations are applied in version order using a `schema_migrations` table. See docs/architecture.md — Data Layer and docs/specs.md — Part 3 for the full schema.

### Scope
**Create:**
- `src-tauri/src/db/mod.rs`
- `src-tauri/src/db/migrations.rs`

**Modify:**
- `src-tauri/src/main.rs` — add db module declaration and init call on app setup

### Acceptance Criteria
- [ ] `src-tauri/src/db/mod.rs` exports:
  - `DbConn` type alias (wrapping `duckdb::Connection`)
  - `init(app_data_dir: &Path) -> Result<DbConn, String>` — creates/opens the DB file, runs migrations, returns connection
- [ ] `src-tauri/src/db/migrations.rs`:
  - `schema_migrations` table created if not exists (version INTEGER PRIMARY KEY, applied_at TIMESTAMP)
  - Migration 001 creates all F2 tables:
    ```sql
    f2_file_index (id, path, size_bytes, modified_at, mime_type, sha256, status, last_scanned)
    f2_file_labels (id, file_id, label, added_at)
    f2_watched_folders (id, path, enabled, ignore_globs, added_at, last_scan)
    f2_views (id, name, primary_dim, secondary_dim, is_builtin, created_at)
    settings (key, value, updated_at)
    ```
  - Migration 002 seeds the 6 predefined F2V views into `f2_views`
  - Migrations are idempotent — running twice is safe
  - Applied migrations are recorded in `schema_migrations`
- [ ] `main.rs` calls `db::init()` during app setup and stores the connection via `tauri::Manager::manage()`
- [ ] App still opens with `cargo tauri dev` after this change
- [ ] No panics — DB errors are returned as `Result<_, String>` not unwrapped

### Agentic Instructions
**Follow:**
- DB file path: use `app_handle.path().app_data_dir()` to resolve the OS-appropriate path. Create the directory if it doesn't exist.
- DuckDB connection is not `Send + Sync` by default — wrap it in `Arc<Mutex<duckdb::Connection>>` for use as Tauri managed state
- Migration runner pattern: `SELECT MAX(version) FROM schema_migrations` → apply any migrations with version > current max
- `f2_views` seed data (6 rows): By Type, By Date, By Size, By Label, By Type + Label, By Date + Type — see SPECS.md §2B.3 for definitions
- Use `INTEGER PRIMARY KEY` for IDs — DuckDB auto-increments this

**Do not:**
- Store the DB connection in a global static
- Use `unwrap()` or `expect()` in production paths — return `Result`
- Create any Tauri commands in this ticket (that is TICKET-04)

### References
- [docs/specs.md — Part 3: Data Model](docs/specs.md)
- [docs/architecture.md — Data Layer](docs/architecture.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-03: F2 scanner — walkdir + sha2 + sysinfo

**Labels:** `rust`, `backend`, `f2`
**Depends on:** TICKET-02

### Summary
Implement the core F2O file scanner in Rust: directory traversal, metadata collection, streaming SHA-256 hashing, system utilisation checks, and writing results to DuckDB. The scanner runs as a background Tokio task and emits Tauri events for progress.

### Context
The scanner is the engine of F2O. It walks watched folders, hashes each file, and upserts results into `f2_file_index`. It respects system CPU load (via sysinfo) and pauses when the machine is busy. Progress and completion are communicated to the frontend via Tauri events, not command responses. See docs/specs.md §2A.3.

### Scope
**Create:**
- `src-tauri/src/modules/f2/mod.rs`
- `src-tauri/src/modules/f2/scanner.rs`

**Modify:**
- `src-tauri/src/main.rs` — add modules::f2 module declaration

### Acceptance Criteria
- [ ] `scanner.rs` exports:
  - `ScannerConfig` struct: `{ root_path: PathBuf, ignore_globs: Vec<String> }`
  - `ScanProgress` struct (serialisable): `{ scanned: u64, total_estimate: u64, current_path: String, duplicates_found: u64 }`
  - `scan_directory(config: ScannerConfig, db: Arc<Mutex<Connection>>, app_handle: AppHandle) -> Result<(), String>`
- [ ] Scanner behaviour:
  - Walks directory tree using `walkdir`, respecting depth and following symlinks off by default
  - Default ignore list always applied: `.git/`, `node_modules/`, `.cache/`, `*.sock`, `*.pid`, `/proc/`, `/sys/`, `/dev/`
  - User ignore globs from `ScannerConfig.ignore_globs` also applied
  - For each file: reads `path`, `size_bytes`, `modified_at` from fs metadata
  - MIME type guessed from extension via `mime_guess`
  - SHA-256 computed by streaming the file in 64KB chunks (never reads entire file into memory)
  - Upserts into `f2_file_index`: if path exists and `modified_at` unchanged, skip hashing (use cached hash)
  - After each file: sets status to `'duplicate'` for all paths sharing a hash with >1 entry, `'ok'` for unique hashes
  - Files in index that no longer exist on disk: set `status = 'missing'`
- [ ] CPU utilisation check via `sysinfo`:
  - Before processing each batch of 50 files: check CPU usage
  - If CPU > 50%: `tokio::time::sleep(Duration::from_secs(5))` then recheck
  - If CPU < 30%: proceed
- [ ] Progress events emitted via `app_handle.emit("scan-progress", &ScanProgress {...})` every 50 files
- [ ] Completion event emitted via `app_handle.emit("scan-complete", ())` when done
- [ ] No panics — file read errors (permissions, deleted mid-scan) are logged and skipped, not fatal

### Agentic Instructions
**Follow:**
- Streaming SHA-256 pattern:
  ```rust
  use sha2::{Sha256, Digest};
  use std::io::{Read, BufReader};
  let mut hasher = Sha256::new();
  let file = File::open(&path)?;
  let mut reader = BufReader::new(file);
  let mut buf = [0u8; 65536];
  loop {
      let n = reader.read(&mut buf)?;
      if n == 0 { break; }
      hasher.update(&buf[..n]);
  }
  let hash = hex::encode(hasher.finalize());
  ```
- sysinfo CPU check: `let mut sys = System::new_all(); sys.refresh_cpu_all(); let usage = sys.global_cpu_usage();`
- `scan_directory` should be called inside a `tokio::spawn` block from the command handler (TICKET-04)
- DuckDB upsert: `INSERT OR REPLACE INTO f2_file_index ...` pattern

**Do not:**
- Call `scan_directory` directly from `main.rs`
- Use `std::thread::sleep` — use `tokio::time::sleep` to avoid blocking the async runtime
- Load entire files into memory for hashing

### References
- [docs/specs.md — §2A.3 Scan Behavior](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-04: Tauri commands — F2O command bridge

**Labels:** `rust`, `backend`, `f2`
**Depends on:** TICKET-03

### Summary
Expose the F2O scanner and database queries to the frontend via Tauri commands. This is the IPC bridge between the React UI and the Rust backend.

### Context
All frontend data access goes through Tauri commands. This ticket creates the command handlers in `src-tauri/src/commands/f2.rs` and registers them in `main.rs`. See CLAUDE.md — Key Architectural Rules.

### Scope
**Create:**
- `src-tauri/src/commands/f2.rs`

**Modify:**
- `src-tauri/src/main.rs` — declare commands module, add all F2 commands to `generate_handler![]`

### Acceptance Criteria
- [ ] `commands/f2.rs` implements and exports these commands:

  **Watched folders:**
  - `f2_get_watched_folders() -> Result<Vec<WatchedFolder>, String>`
  - `f2_add_watched_folder(path: String) -> Result<WatchedFolder, String>`
  - `f2_toggle_watched_folder(id: i64, enabled: bool) -> Result<(), String>`
  - `f2_remove_watched_folder(id: i64) -> Result<(), String>`

  **Scan:**
  - `f2_trigger_scan(app_handle: AppHandle) -> Result<(), String>` — spawns a background Tokio task that runs `scan_directory` for each enabled watched folder; emits `scan-progress` and `scan-complete` events

  **File index:**
  - `f2_get_file_index(limit: Option<i64>, offset: Option<i64>) -> Result<Vec<FileEntry>, String>`
  - `f2_get_file_count() -> Result<i64, String>`

  **Duplicates:**
  - `f2_get_duplicate_groups() -> Result<Vec<DuplicateGroup>, String>` — returns groups of 2+ files sharing the same sha256; each group includes all file entries and total wasted space

- [ ] `WatchedFolder`, `FileEntry`, `DuplicateGroup` structs defined in `commands/f2.rs` (or a shared types module), all with `#[derive(serde::Serialize, serde::Deserialize)]`
- [ ] `WatchedFolder`: `{ id: i64, path: String, enabled: bool, last_scan: Option<String> }`
- [ ] `FileEntry`: `{ id: i64, path: String, size_bytes: i64, modified_at: String, mime_type: Option<String>, sha256: Option<String>, status: String }`
- [ ] `DuplicateGroup`: `{ sha256: String, size_bytes: i64, files: Vec<FileEntry>, wasted_bytes: i64 }`
- [ ] All commands registered in `generate_handler![]` in `main.rs`
- [ ] `cargo check` passes

### Agentic Instructions
**Follow:**
- Each command receives `db: State<'_, Arc<Mutex<Connection>>>` as a parameter — Tauri injects this via managed state
- `f2_trigger_scan` spawns with `tokio::spawn` so it returns immediately to the frontend; the scan runs in the background
- `DuplicateGroup.wasted_bytes` = `size_bytes * (files.len() - 1)` — all but one copy is waste
- For `f2_get_duplicate_groups`: query as `SELECT sha256, COUNT(*) as cnt FROM f2_file_index WHERE status = 'duplicate' AND sha256 IS NOT NULL GROUP BY sha256 HAVING cnt > 1` then fetch the file entries for each group

**Do not:**
- Put business logic in command handlers — delegate to `modules/f2/scanner.rs`
- Return raw DuckDB row types to the frontend — always map to serialisable structs
- Block the async runtime with synchronous DB calls — wrap DB access in `tokio::task::spawn_blocking` if needed

### References
- [docs/architecture.md — Frontend → Backend Communication](docs/architecture.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-05: Frontend scan events — progress listener

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-04

### Summary
Add a Tauri event listener to the frontend that tracks scan progress and exposes it via a React context or hook. The TopBar sync button triggers a scan and shows a spinner while it is in progress.

### Context
The scanner emits `scan-progress` and `scan-complete` events from Rust. The frontend needs to listen for these and update UI accordingly. The TopBar already has a `syncing` prop and `onSync` handler — these need to be wired up. See CLAUDE.md — Rule 7 (background scanner).

### Scope
**Create:**
- `src/hooks/useScanStatus.ts`

**Modify:**
- `src/App.tsx` — wire `onSync` and `syncing` to the scan hook
- `src/context/AppContext.tsx` — optionally add `scanProgress` state if needed

### Acceptance Criteria
- [ ] `useScanStatus.ts` exports a hook that:
  - Returns `{ scanning: boolean, progress: ScanProgress | null, triggerScan: () => Promise<void> }`
  - `ScanProgress` type: `{ scanned: number, totalEstimate: number, currentPath: string, duplicatesFound: number }`
  - `triggerScan` calls `invoke('f2_trigger_scan')` and sets `scanning = true`
  - Listens to Tauri event `scan-progress` via `listen()` from `@tauri-apps/api/event` and updates `progress`
  - Listens to `scan-complete` and sets `scanning = false`, clears progress
  - Cleans up listeners on unmount
- [ ] `App.tsx` uses `useScanStatus` and passes `onSync={triggerScan}` and `syncing={scanning}` to `TopBar`
- [ ] TopBar spinner is visible during an active scan
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Tauri event listener pattern:
  ```typescript
  import { listen } from '@tauri-apps/api/event';
  useEffect(() => {
    const unlisten = listen<ScanProgress>('scan-progress', (event) => {
      setProgress(event.payload);
    });
    return () => { unlisten.then(fn => fn()); };
  }, []);
  ```
- `@tauri-apps/api` is already installed by Tauri scaffold — do not add it again
- `scanning` state: set to `true` on `triggerScan`, set to `false` on `scan-complete` event

**Do not:**
- Poll via `setInterval` — use Tauri events exclusively
- Show a full-screen loading overlay — the TopBar spinner is sufficient
- Add scan progress details to the UI in this ticket (that is a future enhancement)

### References
- [CLAUDE.md — Rule 7: Background scanner is non-blocking](CLAUDE.md)
- [docs/specs.md — §2A.3 Background nature](docs/specs.md)

---
---

## TICKET-06: Frontend data hooks — useFileIndex and useDuplicates

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-05

### Summary
Create the custom React hooks that fetch file index and duplicate data from the Rust backend via Tauri `invoke()`. These hooks are what the Index and Duplicates tabs will consume.

### Context
Custom hooks wrap all `invoke()` calls. The tabs themselves should not call `invoke()` directly — they use hooks. Hooks also re-fetch after a scan completes, so the UI updates automatically. See CLAUDE.md — Naming Conventions and Rule 1.

### Scope
**Create:**
- `src/hooks/useFileIndex.ts`
- `src/hooks/useDuplicates.ts`
- `src/hooks/useWatchedFolders.ts`
- `src/hooks/types.ts` — shared TypeScript types matching Rust structs

### Acceptance Criteria
- [ ] `types.ts` exports:
  - `WatchedFolder`, `FileEntry`, `DuplicateGroup`, `ScanProgress` interfaces matching the Rust command return types exactly
- [ ] `useFileIndex.ts`:
  - Returns `{ entries: FileEntry[], total: number, loading: boolean, error: string | null, refetch: () => void }`
  - Fetches via `invoke<FileEntry[]>('f2_get_file_index', { limit: 500, offset: 0 })`
  - Re-fetches when Tauri `scan-complete` event fires
- [ ] `useDuplicates.ts`:
  - Returns `{ groups: DuplicateGroup[], loading: boolean, error: string | null, refetch: () => void }`
  - Fetches via `invoke<DuplicateGroup[]>('f2_get_duplicate_groups')`
  - Re-fetches on `scan-complete`
- [ ] `useWatchedFolders.ts`:
  - Returns `{ folders: WatchedFolder[], loading: boolean, error: string | null, addFolder: (path: string) => Promise<void>, toggleFolder: (id: number, enabled: boolean) => Promise<void>, removeFolder: (id: number) => Promise<void> }`
  - Mutating operations call the appropriate invoke commands and refetch
- [ ] All hooks handle loading and error states
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Standard hook data-fetching pattern with `useState` + `useEffect`
- Error state: catch invoke errors and store the message string
- `refetch` function: increment a counter state to re-trigger the useEffect

**Do not:**
- Add pagination UI in this ticket — `limit: 500` is sufficient for now
- Add caching — refetch fresh from DuckDB each time
- Import Tauri APIs at the component level — always via hooks

### References
- [CLAUDE.md](CLAUDE.md)
- [docs/specs.md — Part 3: Data Model](docs/specs.md)

---
---

## TICKET-07: F2O Index tab — real data table

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-06

### Summary
Replace the placeholder content in the Index tab of F2Operations with a real, searchable, sortable table of indexed files sourced from DuckDB via `useFileIndex`.

### Context
The Index tab is one of two tabs in F2Operations (the other is Duplicates). It should show all files that Rig has indexed, with their path, size, type, hash, and status. The first run will show an empty state until a watched folder is added and a scan is triggered.

### Scope
**Modify:**
- `src/components/modules/f2/F2Operations.tsx`

**Create:**
- `src/components/modules/f2/IndexTable.tsx`

### Acceptance Criteria
- [ ] `IndexTable.tsx` renders a table with columns: Path, Size, Modified, Type, Hash (truncated to 12 chars), Status
- [ ] Size formatted as human-readable (e.g. `1.2 MB`, `340 KB`) — not raw bytes
- [ ] Modified date formatted as `YYYY-MM-DD`
- [ ] Hash truncated with a `title` attribute showing the full hash on hover
- [ ] Status shown as a badge: `ok` (neutral), `duplicate` (amber), `missing` (red)
- [ ] Search input above the table filters by path (client-side, no re-fetch)
- [ ] Empty state when no entries: `Database` icon + "No files indexed yet. Add a watched folder and click Sync."
- [ ] Loading state: skeleton rows while fetching
- [ ] Error state: inline error banner with a Retry button that calls `refetch()`
- [ ] `F2Operations.tsx` uses `useFileIndex` and passes data to `IndexTable`
- [ ] Responsive to light/dark theme
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Use Tailwind for the table layout — a standard `<table>` with `w-full text-sm` is fine
- Truncate long paths: show only the last 2 path segments with full path in a `title` tooltip
- Status badge: use Tailwind `rounded-full px-2 py-0.5 text-xs font-medium` with appropriate background colours per status
- Human-readable file size utility: write a simple `formatBytes(bytes: number): string` helper inline or in a `src/lib/format.ts` utility file

**Do not:**
- Add server-side pagination — limit 500 rows is enough for now
- Add column sorting in this ticket
- Import any charting or heavy libraries

### References
- [docs/specs.md — §2A.4 Index Tab](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-08: F2O Duplicates tab — real data

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-06

### Summary
Replace the placeholder content in the Duplicates tab with real duplicate groups sourced from DuckDB via `useDuplicates`.

### Context
The Duplicates tab shows groups of files that share the same SHA-256 hash. Each group is a collapsible card. The user can review which file to keep. No file operations happen in this ticket — that is v0.3. The tab is read-only here.

### Scope
**Modify:**
- `src/components/modules/f2/F2Operations.tsx`

**Create:**
- `src/components/modules/f2/DuplicatesTab.tsx`
- `src/components/modules/f2/DuplicateGroup.tsx`

### Acceptance Criteria
- [ ] `DuplicatesTab.tsx` renders a list of `DuplicateGroup` cards, grouped by sha256
- [ ] Summary bar above the list: "N duplicate groups — X MB wasted"
- [ ] Each `DuplicateGroup.tsx` card shows:
  - SHA-256 (truncated) as the group header
  - File size (shown once, applies to all)
  - Number of copies
  - Collapsible list of file paths with modified date per file
  - `[Keep]` badge on the auto-suggested file to keep (oldest by modified date) — visual only, no action yet
- [ ] Groups are collapsed by default, expandable on click
- [ ] Empty state: `ScanSearch` icon + "No duplicates found. Add a watched folder and click Sync."
- [ ] Loading state: skeleton cards
- [ ] Error state: inline error banner with retry
- [ ] Wasted space formatted as human-readable bytes (reuse `formatBytes` from TICKET-07)
- [ ] Responsive to light/dark theme
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Auto-suggest "Keep" = the file with the earliest `modified_at` in the group (oldest = most likely original)
- Collapsible state managed with local `useState` per group — store a `Set<string>` of expanded sha256s
- `[Keep]` badge: subtle, e.g. `text-xs text-muted-foreground border rounded px-1` — it is a suggestion, not an action

**Do not:**
- Add move/delete buttons in this ticket — read-only only
- Add a "Resolve all" bulk action
- Open the RightPanel on file click (that is v0.3)

### References
- [docs/specs.md — §2A.4 Duplicates Tab](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-09: Watched folders UI

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-06

### Summary
Add a watched folders management UI to the Settings route, allowing the user to add folders (via OS path input), toggle them enabled/disabled, and remove them.

### Context
Without a watched folder, no scan can run and the Index and Duplicates tabs will always show empty state. This is the minimum UI needed to make the scanner usable. The full Settings panel is out of scope — this ticket adds only the Watched Folders section to the existing `/settings` placeholder route.

### Scope
**Create:**
- `src/components/modules/f2/WatchedFoldersSettings.tsx`

**Modify:**
- `src/App.tsx` — replace the `/settings` placeholder with a tab-based settings view that includes the Watched Folders section

### Acceptance Criteria
- [ ] Settings route renders a `MainArea` with a single tab: "Watched Folders"
- [ ] `WatchedFoldersSettings.tsx`:
  - Lists current watched folders with: path, enabled toggle, remove button
  - "Add Folder" input: a text field for typing a path + "Add" button (no OS file picker in this ticket)
  - Enabled toggle calls `toggleFolder(id, !enabled)`
  - Remove button calls `removeFolder(id)` with a confirmation (`window.confirm` is acceptable)
  - Add button calls `addFolder(path)` and clears the input on success
  - Empty state: "No watched folders. Add a folder path above to start scanning."
- [ ] Input validates that the path is non-empty before enabling the Add button
- [ ] Error messages shown inline if `addFolder` or `removeFolder` rejects
- [ ] Responsive to light/dark theme
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Use `useWatchedFolders` hook from TICKET-06
- Toggle: a simple shadcn `Switch` component (install via `bunx shadcn@latest add switch` if not present)
- Layout: a clean list with each folder as a row — path on the left, toggle + remove on the right
- The "Add Folder" path input is a plain text field — OS file picker requires Tauri dialog plugin which is a separate ticket

**Do not:**
- Implement the OS folder picker dialog (deferred)
- Add any other settings sections (Appearance, About, etc.) — those are future tickets
- Use a modal for the add form — inline is fine

### References
- [docs/specs.md — §1.5 Settings / Watched Folders](docs/specs.md)
- [docs/specs.md — §2A.2 Watched Folders](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-10: v0.2 integration QA

**Labels:** `dx`, `frontend`, `f2`
**Depends on:** TICKET-07, TICKET-08, TICKET-09

### Summary
End-to-end QA pass for the v0.2 milestone. Verify the full scan → index → display flow works, fix any integration issues found.

### Context
This is the integration verification ticket. By the end, a user should be able to: add a watched folder, trigger a scan, see files appear in the Index tab, and see duplicate groups in the Duplicates tab.

### Scope
**Modify (as needed):**
- Any file from this milestone

**Do not create new files unless fixing a discovered bug.**

### Acceptance Criteria
- [ ] **Full flow test:** Add a path via Settings → Watched Folders → click Sync → TopBar spinner shows → scan completes → Index tab populates with real files
- [ ] **Duplicates:** If the watched folder contains duplicate files, they appear in the Duplicates tab with correct grouping and wasted space calculation
- [ ] **Incremental scan:** Trigger scan a second time → only modified files are rehashed (no full rescan of unchanged files) — verified by scan completing faster
- [ ] **Empty watched folders:** Settings shows empty state, Index and Duplicates show their empty states — no errors
- [ ] **Error handling:** Add an invalid/nonexistent path → error is shown inline, no crash
- [ ] **Scan events:** TopBar spinner appears on scan start, disappears on scan-complete
- [ ] **Dark mode:** Index table and Duplicates cards render correctly in both themes
- [ ] **No console errors:** Browser devtools console is clean during normal use
- [ ] **No panics:** `cargo tauri dev` log shows no Rust panics

### Agentic Instructions
**Follow:**
- Test with a real directory that has at least a few hundred files and at least one pair of duplicates
- If a bug is found: fix it in the appropriate file, add a comment explaining the issue
- Keep fixes minimal and targeted

**Do not:**
- Add new features
- Implement the OS folder picker (deferred)
- Add file move/delete functionality (v0.3)

### References
- [docs/specs.md](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)