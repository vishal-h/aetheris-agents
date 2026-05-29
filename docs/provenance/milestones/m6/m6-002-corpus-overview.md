# hai-rig/m6: Corpus overview tab

## Context

The main Provenance dashboard view. Shows stakeholders the current state of the
corpus at a glance: how much data exists, how much is duplicated, which clients
have files, and when the last scan ran. Read-only.

## What to build

### `src/hooks/useCorpusOverview.ts`

Two hooks:
- `useCorpusSummary()` — calls `provenance_corpus_summary`, returns summary stats
- `useClientBreakdown()` — calls `provenance_client_breakdown`, returns per-client rows
- `useScanRuns(limit?: number)` — calls `provenance_scan_runs`, returns recent runs

### `src/components/modules/provenance/CorpusOverview.tsx`

A tab factory function `CorpusOverview(): Tab[]` returning three tabs:

**Tab 1 — Summary**

Cards row at top:
| Total files | Unique files | Duplicates | Wasted space | Classified | Migrated |
|------------|-------------|------------|-------------|------------|---------|
| N          | N           | N          | X GB        | N          | N       |

Below: client breakdown table.

Columns: Client | Files | Size | Migrated | Doc types

**Tab 2 — Scan history**

Table of recent scan runs ordered by `started_at DESC`.

Columns: Run ID (truncated) | Root path | Status | Files scanned | Duplicates | Started | Duration

Status badge: `complete` → green, `running` → amber, `failed` → red.

**Tab 3 — Storage breakdown**

Horizontal stacked bar: unique content vs wasted space vs zip files.
Simple `div`-based bar with Tailwind — no chart library needed.

Below: top-10 duplicate groups table (from `duplicate_groups` view):
Columns: SHA-256 prefix | Copies | Size each | Wasted

### Registration

In `src/modules/registry.ts`:
```typescript
import { CorpusOverview } from "../components/modules/provenance/CorpusOverview"
// Add to module list:
{ id: "provenance", label: "Provenance", tabs: CorpusOverview() }
```

In `src-tauri/src/lib.rs`: no changes needed (commands already registered in m6-001).

### "Not connected" state

When `useProvenanceStatus()` returns `connected: false`, all three tabs render:
```
Corpus not connected.
Set PROVENANCE_DB_PATH to the corpus DuckDB path and restart.
```

## Acceptance criteria

- [ ] Summary cards show correct values from fixture DB (seeded via `seed_search_fixture.py`)
- [ ] Client breakdown table renders one row per client
- [ ] Scan history shows at least one row when scan_runs is populated
- [ ] Storage breakdown bar renders (no crash if wasted_bytes is 0)
- [ ] Duplicate groups table renders correctly
- [ ] "Not connected" placeholder renders when corpus_conn is None
- [ ] `CorpusOverview()` called as function, not JSX (CLAUDE.md rule)
- [ ] No `any` TypeScript types
- [ ] `cargo tauri dev` starts without errors with PROVENANCE_DB_PATH set

## Files to create

- `src/hooks/useCorpusOverview.ts`
- `src/components/modules/provenance/CorpusOverview.tsx`
- `src/modules/registry.ts` (update)

## Notes

**`formatBytes` is already in `src/lib/utils.ts`.** Use it for all size display.

**`formatDate` is already in `src/lib/utils.ts`.** Use it for timestamps.

**Empty states.** If scan_runs is empty (corpus exists but no scan has run),
show "No scans yet. Run the scan orchestrator." rather than an empty table.

**Tailwind only.** No new CSS files. All styling via Tailwind utility classes.
No shadcn components needed for this tab beyond what exists.

**Polling.** No auto-refresh. A manual "Refresh" button triggers a re-fetch
via the hooks' refetch function. Do not use `setInterval` or `useEffect`
polling.
