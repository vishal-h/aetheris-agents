# Reality Check — Rig Current State

**Trigger:** milestone boundary, or returning to the project after an
extended gap (more than ~2 weeks since last session).

**Output file:** `docs/rig/current-state-<DATE>.md`
Replace `<DATE>` with today's date in YYYY-MM format (e.g. `2026-07`).
If a current-state file already exists for this month, overwrite it.

---

Produce a ground-truth snapshot of the Rig desktop app by reading
actual source files and git history — NOT from prior docs or memory.
Write the result to `docs/rig/current-state-<DATE>.md`. The document
must be reproducible: every claim cites a file:line or commit hash so
a future session can verify it independently.

The document has three parts.

---

## Part 1 — Milestone and Feature Status

For each Rig milestone directory under `docs/rig/milestones/`, read its
README.md Status: line, then verify the claim against source code:

- **IMPLEMENTED:** confirm the key commands exist in `rig/src-tauri/src/commands/`,
  the Tauri handler is registered in `lib.rs`, and the primary React
  component exists in `rig/src/components/`. Cite file:line for each.
- **PARTIAL / IN PROGRESS:** enumerate what exists vs what's missing,
  with evidence.
- **NOT STARTED:** confirm the relevant files do not exist.

Also check for undocumented features: commands registered in
`lib.rs generate_handler!` that have no corresponding milestone doc.
List them in a table with their source file and line count.

---

## Part 2 — Inventory Tables

### 2.1 Tauri Command Inventory
Read `rig/src-tauri/src/lib.rs` and extract all entries from
`invoke_handler(tauri::generate_handler![...])`. Group by module
(`commands/<module>.rs`). For each command note the line in lib.rs
and whether it appears in `docs/rig/specs.md §4`.

### 2.2 Module and Route Inventory
Read `rig/src/modules/registry.ts`. For each registered module list:
module id, sidebar sections, routes. Cross-check each route against
`rig/src/App.tsx`. Note any route in registry.ts missing from App.tsx
or vice versa (excluding known exceptions: `/`, `/settings`).

### 2.3 DB Schema vs specs.md §2
Read `../aetheris/lib/aetheris/store.ex`. Extract every `CREATE TABLE`
and `ALTER TABLE ADD COLUMN`. Compare against `docs/rig/specs.md §2`.
Report: columns in code but not in specs (INFO), columns in specs but
not in code (FAIL-equivalent). List tables present in store.ex but
absent from specs.md.

### 2.4 Event Types vs specs.md §6
Read `../aetheris/lib/aetheris/trajectory/event.ex`. Extract all atoms
in `@type event_type`. Compare against specs.md §6 table. Note which
types are undocumented and which documented types have no events in
`priv/aetheris.db` (run `SELECT DISTINCT type FROM events` if
`AETHERIS_DB_PATH` is set).

### 2.5 Environment Variables
Read all `std::env::var("...")` calls across `rig/src-tauri/src/`.
Cross-check against specs.md §1 and `docs/rig/runbook.md`. Report
vars read in code but undocumented, and vars documented but not read.

---

## Part 3 — Reference Snapshot

### 3.1 trajectory.json Format
Read `../aetheris/lib/aetheris/agent/server.ex` and
`../aetheris/lib/aetheris/trajectory/file.ex`. Document:
- Where and when the file is written (cite line numbers).
- Top-level structure: `schema_version`, `run_id`, `meta`, `events`.
- All fields of the `meta` object (cite server.ex lines where built).
- Per-event fields as written to file vs SQLite `events` table
  (key difference: `payload` is an inlined object in the file, a
  JSON string in SQLite).

### 3.2 Stale Docs — Ordered by Mislead Severity
For each claim in `docs/rig/specs.md`, `docs/rig/architecture.md`,
and `docs/rig/runbook.md` that is contradicted by source code, write
one row:

| # | Doc | Claim | Reality | Impact |
|---|-----|-------|---------|--------|

Order by how badly a contributor would be misled. Include only genuine
contradictions — omissions (doc is silent) are lower priority than
false claims (doc asserts something wrong).

---

## Gap Analysis

For each item below, determine current state from source code and note
any Rig-side or harness-side progress since the prior current-state doc:

**A. Token/cost rollups in run list** — does `harness_list_runs` include
`total_cost_usd` and/or token totals in `RunSummary`? Check
`rig/src-tauri/src/commands/harness.rs` and `rig/src/hooks/types.ts`.

**B. Stale/stuck run detection** — does the harness have a startup sweep
for orphaned `running` rows? Does Rig show a staleness marker? Check
`../aetheris/lib/aetheris/application.ex` and `RunList.tsx`.

**C. Replay/fork from step** — does `Aetheris.fork_run` exist in
`../aetheris/lib/aetheris.ex`? Does any Tauri command expose it?

**D. Skills extraction** — does anything call `Aetheris.extract_skill`
automatically post-run? Does Rig have a skills view?

---

## Constraints

- Read source files directly; do not rely on prior docs for facts.
- Every claim must cite `file:line` or `git log --oneline -1 -- <file>`.
- Do not summarise or editorialize beyond what the code shows.
- If a file cannot be found, state that explicitly rather than
  inferring from docs.
- Keep the document self-contained: a reader with no prior context
  should be able to verify every assertion.
- After writing the file, run `python3 scripts/drift_check.py`
  (with `AETHERIS_DB_PATH` set if available) and append the summary
  line to the document under a "Drift check at snapshot time:" heading.
