# Milestone: v0.3 — F2O Actions

## Milestone Description
Completes the F2O deduplication workflow by adding the file action layer: moving duplicate files to a staging folder, the right panel file detail view, and restoring/permanently deleting staged files. Also fixes the Tabs uncontrolled/controlled warning introduced in v0.1.

At the end of this milestone, a user can: review duplicate groups, select which file to keep, move the rest to the duplicates staging folder, inspect any file in the right panel, and either restore or permanently delete staged files.

**No virtual filesystem (F2V) work in this milestone.** That is v0.4.

## Metadata
- **Repo:** swiftekin/hai-rig
- **Milestone:** v0.3 — F2O Actions
- **Labels to create before importing:** `rust`, `backend`, `frontend`, `f2`, `shell`, `dx`

---
---

## TICKET-01: Tauri fs permissions and duplicates folder config

**Labels:** `rust`, `backend`, `dx`
**Depends on:** none

### Summary
Configure Tauri's filesystem permissions to allow file move operations, and add the duplicates folder path to the settings table on first run.

### Context
Tauri v2 uses a capability system — filesystem access must be explicitly declared in `src-tauri/capabilities/`. Without this, `std::fs::rename` will be blocked. The duplicates folder defaults to `~/rig-duplicates/` and is stored in the `settings` table so the user can change it later.

### Scope
**Modify:**
- `src-tauri/capabilities/default.json` — add fs permissions
- `src-tauri/src/db/migrations.rs` — seed default duplicates folder path in migration 003

**No other files should be touched.**

### Acceptance Criteria
- [ ] `src-tauri/capabilities/default.json` includes `"fs:allow-rename"`, `"fs:allow-mkdir"`, `"fs:allow-read-file"`, `"fs:allow-remove-file"`
- [ ] Migration 003 seeds `settings` table with key `duplicates_folder`, value `~/rig-duplicates/` if not already set
- [ ] `cargo check` passes

### Agentic Instructions
**Follow:**
- Tauri v2 capability format — add to the `permissions` array in `default.json`
- Migration 003 uses `INSERT INTO settings (key, value) VALUES ('duplicates_folder', '~/rig-duplicates/') ON CONFLICT DO NOTHING`
- The `~` in the path will be resolved at runtime in the Rust command handler using `dirs` crate or manual expansion — do not resolve it here

**Do not:**
- Implement any Rust commands in this ticket
- Add the `dirs` crate in this ticket — path expansion is TICKET-02's responsibility

### References
- [docs/specs.md — §2A.5 Duplicates Folder](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-02: Rust commands — move to duplicates folder and restore

**Labels:** `rust`, `backend`, `f2`
**Depends on:** TICKET-01

### Summary
Implement the Rust command handlers for the file action operations: moving duplicate files to the staging folder, restoring them to their original path, and permanently deleting them.

### Context
These are the only destructive operations in F2O. All three require explicit user confirmation in the UI (handled by the frontend, not here). The Rust layer just executes the operation and updates the database. See docs/specs.md §2A.5.

### Scope
**Modify:**
- `src-tauri/src/commands/f2.rs` — add new commands
- `src-tauri/Cargo.toml` — add `dirs = "5"` dependency
- `src-tauri/src/lib.rs` — register new commands

### Acceptance Criteria
- [ ] `dirs = "5"` added to `[dependencies]`
- [ ] New commands implemented and registered:

  **`f2_get_duplicates_folder() -> Result<String, String>`**
  - Reads `duplicates_folder` from `settings` table
  - Expands `~` to the actual home directory using `dirs::home_dir()`
  - Creates the folder if it doesn't exist
  - Returns the resolved absolute path

  **`f2_move_to_duplicates(file_ids: Vec<i64>) -> Result<Vec<MoveResult>, String>`**
  - For each file id: reads path from `f2_file_index`
  - Resolves duplicates folder path
  - Destination filename: `<sha256>.<extension>` (e.g. `a3f2c1d4.pdf`)
  - If destination already exists: skip (already staged)
  - Moves file using `std::fs::rename` — falls back to copy+delete if rename fails (cross-device)
  - Updates `f2_file_index`: sets `status = 'staged'`, adds `staged_path` column value
  - Returns `MoveResult` per file: `{ file_id, original_path, staged_path, success, error }`

  **`f2_restore_from_duplicates(file_id: i64) -> Result<(), String>`**
  - Reads `path` (original) and `staged_path` from `f2_file_index`
  - Moves file back from staged path to original path
  - Creates parent directories if needed
  - Updates `f2_file_index`: sets `status = 'ok'`, clears `staged_path`

  **`f2_delete_staged(file_id: i64) -> Result<(), String>`**
  - Reads `staged_path` from `f2_file_index`
  - Permanently deletes the file with `std::fs::remove_file`
  - Removes the row from `f2_file_index`

- [ ] Migration 004 adds `staged_path VARCHAR` column to `f2_file_index` and `'staged'` as a valid status value (comment only — DuckDB has no CHECK constraints enforcement needed, just document it)
- [ ] `MoveResult` struct derives `Serialize`
- [ ] `cargo check` passes

### Agentic Instructions
**Follow:**
- Cross-device move fallback:
  ```rust
  if std::fs::rename(&src, &dst).is_err() {
      std::fs::copy(&src, &dst)?;
      std::fs::remove_file(&src)?;
  }
  ```
- Extension extraction: `Path::new(&path).extension().and_then(|e| e.to_str()).unwrap_or("")`
- If `staged_path` already has a file at destination, return success with a note — don't error
- All file errors returned as `Result<_, String>`, never panic

**Do not:**
- Show confirmation dialogs from Rust — that is the frontend's responsibility
- Delete files without the user explicitly calling `f2_delete_staged`

### References
- [docs/specs.md — §2A.5 Duplicates Folder](docs/specs.md)
- [CLAUDE.md — DuckDB Rules](CLAUDE.md)

---
---

## TICKET-03: Frontend hooks — useMoveActions

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-02

### Summary
Add the frontend hook that wraps the file action commands, and extend the shared types to include the new structs.

### Scope
**Create:**
- `src/hooks/useMoveActions.ts`

**Modify:**
- `src/hooks/types.ts` — add `MoveResult` type, add `staged_path` to `FileEntry`
- `src/hooks/index.ts` — export new hook and type

### Acceptance Criteria
- [ ] `FileEntry` in `types.ts` gains `staged_path: string | null`
- [ ] `MoveResult` type added: `{ file_id: number, original_path: string, staged_path: string, success: boolean, error: string | null }`
- [ ] `useMoveActions` hook exports:
  - `moveToduplicates(fileIds: number[]) => Promise<MoveResult[]>`
  - `restoreFromDuplicates(fileId: number) => Promise<void>`
  - `deleteStaged(fileId: number) => Promise<void>`
  - `getDuplicatesFolder() => Promise<string>`
  - `loading: boolean`
  - `error: string | null`
- [ ] All functions call the appropriate `invoke()` command
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Keep the hook thin — no UI logic, just invoke wrappers with loading/error state
- `moveToduplicates` sets `loading = true` for the duration, clears on completion
- Errors are stored in `error` state and also re-thrown so calling components can react

**Do not:**
- Add confirmation dialogs here — that is the component's responsibility
- Trigger refetches here — the calling component will call `refetch()` on its own hook after action completes

### References
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-04: Duplicates tab — action buttons

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-03

### Summary
Add action buttons to the Duplicates tab: a "Move to Duplicates Folder" button per group that moves all non-kept files, and per-file action buttons for staged files.

### Context
The Duplicates tab currently shows groups read-only. This ticket makes it actionable. The user reviews a group, confirms which file to keep (the auto-suggested one or their own choice), and clicks "Move" to stage the duplicates. See docs/specs.md §2A.4.

### Scope
**Modify:**
- `src/components/modules/f2/DuplicateGroup.tsx`
- `src/components/modules/f2/DuplicatesTab.tsx`

### Acceptance Criteria
- [ ] Each `DuplicateGroup` card (when expanded) shows a **"Move duplicates"** button in the footer
- [ ] Clicking "Move duplicates": shows `window.confirm` with count and paths of files to be moved, on confirm calls `moveToduplicates(nonKeptFileIds)`, on success calls `refetch()` on `useDuplicates`
- [ ] While moving: button shows a spinner and is disabled
- [ ] Per-file: user can click a different file to designate as "Keep" (overrides the auto-suggestion) — local state only, not persisted
- [ ] After move: groups with all files staged are removed from the list (they will no longer appear as duplicates)
- [ ] Error shown inline per group if move fails
- [ ] Summary bar updates after moves
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Keep selection state local to `DuplicateGroup` component with `useState<number | null>(selectedKeepId)`
- `nonKeptFileIds` = all `file.id` values in the group where `file.id !== selectedKeepId`
- After successful move, call the `refetch` function passed down from `DuplicatesTab`
- Pass `refetch` from `useDuplicates()` down to each `DuplicateGroup` as a prop

**Do not:**
- Implement restore or delete in this ticket — those are in the right panel (TICKET-06)
- Open the right panel from here — that is TICKET-06

### References
- [docs/specs.md — §2A.4 Duplicates Tab](docs/specs.md)

---
---

## TICKET-05: Fix Tabs uncontrolled/controlled warning

**Labels:** `shell`, `frontend`, `dx`
**Depends on:** none (independent)

### Summary
Fix the React warning: `Tabs is changing from uncontrolled to controlled`. This appears on every route transition and pollutes the console.

### Context
The warning occurs in `MainArea.tsx` because `activeTab` state initialises as `undefined` (uncontrolled) and then transitions to a string value (controlled) when tabs load. The fix is to initialise `activeTab` with the first tab's id immediately, or pass a stable default to the `Tabs` component.

### Scope
**Modify:**
- `src/components/shell/MainArea.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] No `Tabs is changing from uncontrolled to controlled` warning in the browser console
- [ ] Tab behaviour unchanged — first tab selected by default, resets on route change
- [ ] TypeScript — no `any`

### Agentic Instructions
The fix is to ensure `activeTab` is never `undefined` when passed to `<Tabs value={...}>`. Options:
- Initialise state as `tabs?.[0]?.id ?? ''` instead of `undefined`
- Or use a derived value: `const activeTabValue = activeTab ?? tabs?.[0]?.id ?? ''`

Either approach is acceptable. Keep the change minimal.

**Do not:**
- Change routing logic
- Touch any other component

---
---

## TICKET-06: Right panel — file detail view

**Labels:** `frontend`, `f2`
**Depends on:** TICKET-03, TICKET-04

### Summary
Implement the right panel file detail view. Clicking a file in the Index tab or the Duplicates tab opens the right panel showing full file metadata, and for staged files, restore/delete actions.

### Context
The right panel component exists and works (open/close). It currently shows placeholder content. This ticket gives it real content for F2O. See docs/specs.md §2A.5 Right Panel.

### Scope
**Create:**
- `src/components/modules/f2/FileDetailPanel.tsx`

**Modify:**
- `src/components/modules/f2/IndexTable.tsx` — clicking a row opens the right panel with that file
- `src/components/modules/f2/DuplicateGroup.tsx` — clicking a file path opens the right panel
- `src/App.tsx` — pass selected file state down to RightPanel

**Create or modify:**
- `src/context/AppContext.tsx` — add `selectedFile: FileEntry | null` and `setSelectedFile` to context

### Acceptance Criteria
- [ ] `AppContext` gains `selectedFile: FileEntry | null` and `setSelectedFile`
- [ ] Clicking a row in `IndexTable` sets `selectedFile` in context and sets `rightPanelOpen = true`
- [ ] Clicking a file path in `DuplicateGroup` does the same
- [ ] `FileDetailPanel` renders inside `RightPanel` via `App.tsx`, receives `selectedFile` from context
- [ ] `FileDetailPanel` shows:
  - Filename (last path segment)
  - Full path
  - Size (formatted)
  - Modified date (formatted)
  - MIME type (or `—`)
  - SHA-256 hash (full, selectable)
  - Status badge
  - For `status = 'staged'`: **Restore** button (calls `restoreFromDuplicates`, then refetches) and **Delete permanently** button (calls `deleteStaged`, then refetches) with a `window.confirm` guard on delete
- [ ] When `selectedFile` is null: RightPanel renders nothing (already handled by `rightPanelOpen = false`)
- [ ] When a new file is selected while panel is open: panel updates to show new file
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- `FileDetailPanel` is a pure display component — it reads from context and calls hook functions
- SHA-256 should be displayed in a `<code>` block with `user-select: all` so it can be copied
- Restore/Delete buttons: use `variant="outline"` for Restore and `variant="destructive"` for Delete
- After Restore or Delete: call `setSelectedFile(null)` and `setRightPanelOpen(false)`

**Do not:**
- Add file preview (image thumbnail, text preview) in this ticket — deferred to v0.4
- Add "Open in Files" or "Open Terminal Here" actions — deferred to v0.4

### References
- [docs/specs.md — §2A.5 Right Panel](docs/specs.md)

---
---

## TICKET-07: v0.3 integration QA

**Labels:** `dx`, `frontend`, `f2`
**Depends on:** TICKET-04, TICKET-05, TICKET-06

### Summary
End-to-end QA pass for v0.3. Verify the full duplicate review → move → inspect → restore/delete flow works, and that the Tabs warning is gone.

### Scope
**Modify (as needed):**
- Any file from this milestone

**Do not create new files unless fixing a discovered bug.**

### Acceptance Criteria
- [ ] **Full flow:** Scan a folder with duplicates → Duplicates tab shows groups → expand group → change Keep selection → click Move → confirm → files move to `~/rig-duplicates/` → group disappears from list
- [ ] **Right panel:** Click a file in Index tab → right panel opens with correct metadata → close works
- [ ] **Staged file detail:** Click a staged file entry (if visible) → right panel shows Restore and Delete buttons
- [ ] **Restore:** Click Restore → file returns to original path → status back to `ok`
- [ ] **Delete:** Click Delete → confirm → file removed from disk and from index
- [ ] **No Tabs warning** in browser console
- [ ] **No console errors** during normal use
- [ ] **Dark mode** — all new UI elements render correctly in both themes
- [ ] `~/rig-duplicates/` folder created automatically on first move

### Agentic Instructions
**Follow:**
- Test with a folder that has at least one duplicate pair
- If a bug is found: fix it in the appropriate file with a comment

**Do not:**
- Add new features
- Implement file preview
- Add OS file picker

### References
- [docs/specs.md](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)
