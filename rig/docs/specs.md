# Rig — Specifications

## Document Scope

This document defines the functional and UI specifications for:
1. The App Shell (host-level layout and features)
2. The F2 module — File & Folder (first module)
   - F2O: File & Folder Operations (dedup)
   - F2V: File & Folder Viewer (virtual views)

---

## Part 1 — App Shell

### 1.1 TopBar

**Layout:** Full-width horizontal bar, fixed at top. Height: 48px.

**Left region**
- App icon (small, 20px) + app name "Rig"
- Clicking has no action in v1

**Center region**
- Reserved for Global Search — deferred to post-MVP

**Right region** (left to right)
- **Sync button** `↻` — triggers on-demand refresh for the active module. Shows spinner while in flight. Subtle success/error indicator on completion
- **Settings button** `⚙` — opens Settings panel (see 1.4)

**Behavior**
- Always visible regardless of active module
- Sync behavior is delegated to the active module
- Sync button disabled if no module is active

---

### 1.2 Sidebar

**Layout:** Fixed left panel. Default width: 240px. Not resizable in v1.

**Structure**
```
▼ F2                   ← Module section header (collapsible)
    Operations         ← F2O sub-item
    Viewer             ← F2V sub-item

───────────────────
＋  Add Module      ← Always visible, placeholder in v1
```

**Behavior**
- Module sections are collapsible
- One sub-item always active (highlighted)
- Active item persisted — app restores last position on reopen
- "Add Module" placeholder in v1

---

### 1.3 Main Content Area

**Layout:** Fills remaining horizontal space between sidebar and optional right panel.

**Tabs**
- Each sidebar sub-item can have one or more tabs
- Horizontal tab strip at the top of the main area
- Tab state is local to the sidebar selection
- Tabs are module-defined, not user-opened

**Content**
- Each tab renders a React component owned by the module
- Loading: skeleton loaders
- Empty states: friendly message + call to action
- Error states: inline error banner with retry

---

### 1.4 Right Panel

**Layout:** Optional, right edge. Default width: 320px. Not resizable in v1.

**Behavior**
- Hidden by default
- Toggled by module logic
- Close button (`✕`) in header
- Main area reflows when panel opens/closes (no overlay)
- Opt-in per module

---

### 1.5 Settings

Full-screen overlay or dedicated route. Not a modal.

**v1 Settings sections**

| Section | Contents |
|---|---|
| Appearance | Light / Dark / System theme toggle |
| Data | Path to DuckDB file (read-only), Export DB, Import DB |
| Watched Folders | View/manage folders registered for background scanning |
| About | App version |

---

### 1.6 Theming

- Light and dark mode from day one
- System default on first launch
- Preference stored in DuckDB settings table
- Tailwind `dark:` classes throughout

---

## Part 2 — F2 Module

### 2.1 Overview

F2 is the File & Folder module. It has two sub-sections:

- **F2O** — File & Folder Operations. Starts with deduplication.
- **F2V** — File & Folder Viewer. Virtual views of the filesystem.

Both sub-sections share the same underlying file metadata scan — one scan populates data for both.

---

### 2.2 Sidebar Structure

```
▼ F2
    Operations     ← F2O (dedup, file management)
    Viewer         ← F2V (virtual views)
```

---

## Part 2A — F2O: Operations

### 2A.1 Purpose

Scan designated folders, detect duplicate files by SHA-256 hash, present them for review, and allow safe removal.

---

### 2A.2 Watched Folders

The user designates one or more root folders to watch. Rig scans these folders while the app is open.

**Managed in:** Settings → Watched Folders

**Per folder config:**
- Path (selected via OS folder picker)
- Enabled toggle (pause scanning without removing)
- Ignore list (custom glob patterns, e.g. `*.tmp`, `node_modules/`)

**Default system ignores (always applied):**
```
.git/
node_modules/
.cache/
*.sock
*.pid
/proc/
/sys/
/dev/
```

---

### 2A.3 Scan Behavior

**Trigger:** Scan runs automatically while the app is open, during low system utilization.

**Utilization check (via `sysinfo` crate):**
- CPU usage < 30% for 10 seconds → begin or resume scan
- CPU usage > 50% → pause scan
- Scan is chunked — processes N files then yields, checks utilization again

**Scan process per file:**
1. Walk directory tree (`walkdir` crate)
2. Skip ignored paths and system files
3. For each file: read metadata (path, size, modified date, mime type)
4. Compute SHA-256 hash (streaming, not loading full file into memory)
5. Write to `f2_file_index` table in DuckDB (upsert by path)

**Rescan logic:**
- On subsequent scans, only reprocess files where `modified_at` has changed
- Deleted files are marked as `status = 'missing'` in the index

**Background nature:**
- Runs in a Tokio async task in Rust
- Does not block the UI
- Scan progress is emitted as Tauri events → frontend shows a subtle progress indicator in the TopBar or sidebar

---

### 2A.4 Operations View

**Tabs:** `Duplicates` | `Index`

#### Duplicates Tab

Shows all detected duplicate groups — sets of files that share the same SHA-256 hash.

**Layout:** Grouped list. Each group is a collapsible card showing:
- SHA-256 (truncated) as the group identifier
- File size (same for all in group, shown once)
- List of file paths in the group

**Per file in a group:**

| Column | Description |
|---|---|
| Path | Full file path |
| Modified | Last modified date |
| Action | Keep / Move to duplicates folder |

**Behavior:**
- One file per group is auto-suggested as "Keep" (the oldest by modified date, or the one in the shallowest path — configurable in v2)
- User can change which file to keep
- "Move Duplicates" button — moves all non-kept files to the duplicates folder
- No file is ever deleted automatically. Only moved on explicit user action.

#### Index Tab

A searchable, sortable table of all indexed files.

| Column | Description |
|---|---|
| Path | Full path |
| Size | File size |
| Modified | Last modified |
| Type | MIME type |
| Hash | SHA-256 (truncated) |
| Status | `ok` / `duplicate` / `missing` |

Useful for browsing what Rig knows about your filesystem.

---

### 2A.5 Duplicates Folder

When the user moves duplicates, files go to a designated duplicates folder.

**Default location:** `~/rig-duplicates/`  
**Configurable in:** Settings → Watched Folders

**File naming in duplicates folder:**
```
<sha256>.<extension>
```
e.g. `a3f2c1d4e5b6...7890.pdf`

Not human-readable by design. The app is the interface for reviewing these files.

**Right Panel — Duplicate File Detail:**
Clicking any file in the duplicates folder view opens the right panel showing:
- Original path(s) it came from
- Preview (image thumbnail, or text snippet for text files)
- File size, modified date, mime type
- Actions: **Delete permanently** | **Restore to original path**

---

### 2A.6 Sync Button Behavior (F2O active)

Clicking `↻` in the TopBar while F2O is active triggers an immediate full rescan of all watched folders, regardless of system utilization.

---

## Part 2B — F2V: Viewer

### 2B.1 Purpose

The filesystem is a tree, but files belong to multiple conceptual dimensions simultaneously (client, type, label, date, project). F2V provides alternative virtual views of the same files — without moving anything.

---

### 2B.2 What a View Is

A view is a saved DuckDB query over file metadata, rendered as a navigable tree in the UI.

The user picks a view from a predefined list. Rig queries `f2_file_index` and `f2_file_labels`, groups the results by the view's dimensions, and renders a virtual folder tree.

The actual files are never moved. The tree is a projection.

---

### 2B.3 Predefined Views (v1)

| View Name | Primary Group | Secondary Group | Description |
|---|---|---|---|
| By Type | MIME category | — | Groups files by type: Images, Documents, Code, Video, Audio, Other |
| By Date | Year | Month | Groups by when files were last modified |
| By Size | Size bucket | — | Large (>100MB), Medium (1–100MB), Small (<1MB) |
| By Label | Label | — | Groups by user-applied labels (see 2B.4) |
| By Type + Label | MIME category | Label | Two-level grouping |
| By Date + Type | Year | MIME category | Two-level grouping |

User selects a view from a dropdown in the Viewer toolbar. Design should support user-defined views in v2 (i.e., the view definition is a data structure, not hardcoded UI).

---

### 2B.4 Labels

Users can apply one or more labels to any file or folder in the index.

**Examples:** `client-acme`, `invoice`, `important`, `archive`, `util`

**How to apply:**
- Right-click a file in any view → "Add Label"
- Or via the right panel when a file is selected

Labels are stored in `f2_file_labels` table. They do not touch the filesystem.

---

### 2B.5 Viewer Layout

```
┌─────────────────────────────────────────────────────────┐
│  View: [By Type ▾]     [Search...]      [↻ Rescan]      │  Viewer toolbar
├──────────────────────────────────────────────────────────┤
│  ▼ Documents (142)                                       │
│      ▼ 2024 (38)                                         │
│          report-q3.pdf                                   │
│          invoice-acme.pdf                                │
│          ...                                             │
│      ▼ 2023 (104)                                        │
│          ...                                             │
│  ▶ Images (891)                                          │
│  ▶ Code (2,341)                                          │
│  ▶ Other (57)                                            │
└──────────────────────────────────────────────────────────┘
```

File count shown per group. Groups are collapsible. Search filters the tree in real time.

---

### 2B.6 File Actions (Non-destructive only)

Right-clicking a file in any view shows:

| Action | Behavior |
|---|---|
| Open | Forwards to OS — equivalent to double-click |
| Show in Files | Opens the parent folder in the system file manager (Nautilus/Dolphin etc.) |
| Open Terminal Here | Opens a terminal at the file's parent directory |
| Add Label | Adds a label to this file |
| Remove Label | Removes a label |
| View Details | Opens right panel with file detail |

No move, copy, rename, or delete from F2V. F2V is read + label only.

---

### 2B.7 Right Panel — File Detail (F2V)

Opens when user clicks a file or selects "View Details".

**Contents:**
- Filename + full path
- Size, modified date, mime type
- SHA-256 hash (from index)
- Labels (editable inline)
- Preview: image thumbnail, first N lines for text files, icon for others
- Duplicate indicator: "2 other copies exist" (links to F2O duplicates view)
- Quick actions: Open, Show in Files, Open Terminal Here

---

## Part 3 — Data Model

### Tables

```sql
-- Indexed file metadata (populated by scanner)
CREATE TABLE f2_file_index (
    id            INTEGER PRIMARY KEY,
    path          VARCHAR NOT NULL UNIQUE,
    size_bytes    BIGINT,
    modified_at   TIMESTAMP,
    mime_type     VARCHAR,
    sha256        VARCHAR(64),
    status        VARCHAR DEFAULT 'ok',  -- 'ok' | 'duplicate' | 'missing'
    last_scanned  TIMESTAMP DEFAULT now()
);

-- User-applied labels
CREATE TABLE f2_file_labels (
    id        INTEGER PRIMARY KEY,
    file_id   INTEGER NOT NULL,  -- FK to f2_file_index.id
    label     VARCHAR NOT NULL,
    added_at  TIMESTAMP DEFAULT now(),
    UNIQUE(file_id, label)
);

-- Watched folder configuration
CREATE TABLE f2_watched_folders (
    id            INTEGER PRIMARY KEY,
    path          VARCHAR NOT NULL UNIQUE,
    enabled       BOOLEAN DEFAULT true,
    ignore_globs  VARCHAR,  -- JSON array of glob patterns
    added_at      TIMESTAMP DEFAULT now(),
    last_scan     TIMESTAMP
);

-- Saved virtual views (v1: predefined, v2: user-defined)
CREATE TABLE f2_views (
    id            INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    primary_dim   VARCHAR NOT NULL,  -- 'mime' | 'date' | 'size' | 'label'
    secondary_dim VARCHAR,           -- optional second grouping
    is_builtin    BOOLEAN DEFAULT true,
    created_at    TIMESTAMP DEFAULT now()
);

-- App-wide settings
CREATE TABLE settings (
    key        VARCHAR PRIMARY KEY,
    value      VARCHAR NOT NULL,
    updated_at TIMESTAMP DEFAULT now()
);
```

---

---

## Part 5 — Harness Module: Tauri Commands and TypeScript Interfaces

### 5.1 Tauri Command Shapes

#### `usage_stats_load`

No arguments. Returns `UsageStats`. Uses `HarnessState` connection to `aetheris.db`.
Runs three `json_extract` aggregate queries against the `events` and `runs` tables.
Filters all queries with `json_extract(payload_json, '$.cost_usd') IS NOT NULL` to
exclude pre-instrumentation events.

---

### 5.2 TypeScript Interfaces

```typescript
// Token / cost summary — computed client-side in TrajectoryView.tsx
interface TokenSummary {
  input_tokens:  number | null;  // null for pre-instrumentation runs
  output_tokens: number | null;
  cost_usd:      number | null;
  llm_calls:     number;
}

// Usage stats — returned by usage_stats_load
interface ModelUsageRow {
  model:          string;   // resolved_model from llm_responded payload
  run_count:      number;
  input_tokens:   number;
  output_tokens:  number;
  total_cost_usd: number;
  avg_cost_usd:   number;  // total_cost_usd / run_count, computed in Rust
}

interface UseCaseUsageRow {
  use_case:       string;  // prefix-matched label or "Unclassified"
  run_count:      number;
  total_cost_usd: number;
}

interface UsageStats {
  total_cost_usd:      number;
  total_runs:          number;  // all runs in runs table
  instrumented_runs:   number;  // runs with at least one cost_usd IS NOT NULL event
  total_input_tokens:  number;
  total_output_tokens: number;
  by_model:            ModelUsageRow[];   // sorted by total_cost_usd DESC
  by_use_case:         UseCaseUsageRow[]; // sorted by USE_CASE_PREFIXES order
}
```

---

### 5.3 Harness Module Structure

```
src/
  components/modules/harness/
    RunList.tsx           — run list grouped by use case (/harness)
    TrajectoryView.tsx    — event stream + meta panel with token/cost summary
    DiffView.tsx          — two-run comparison with token/cost/latency rows
    CapabilityMatrixView.tsx — agent/script catalogue (/capability-matrix)
    UsageView.tsx         — aggregate usage stats (/usage)
  hooks/
    useHarness.ts         — useHarnessStatus, useRunList, useRunEvents, useRunDetail
    useTrajectory.ts      — useTrajectory
    useRunDiff.ts         — useRunDiff
    useCapabilityMatrix.ts — useCapabilityMatrix
    useUsageStats.ts      — useUsageStats
    useSessionRecord.ts   — sessionStorage-backed expand/collapse state
```

---

## Part 4 — Out of Scope for v1

- User-defined views in F2V (v2)
- File rename, move, copy from within Rig
- Full-text content search (search inside files)
- Watch for filesystem changes in real time (inotify) — v1 scans periodically
- Auto-delete duplicates without review
- Cloud backup of duplicates folder
- Second unrelated module