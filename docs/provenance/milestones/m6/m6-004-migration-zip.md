# hai-rig/m6: Migration + zip status tabs

## Context

Two operational status views. Auditors and operators check these to understand
how far migration has progressed and whether zip archaeology is complete.
Both are read-only.

## What to build

### `src/hooks/useMigration.ts`

```typescript
function useMigrationSummary():
  { data: MigrationSummary | null, loading: boolean, error: string | null, refetch: () => void }
```

### `src/hooks/useZipInventory.ts`

```typescript
function useZipInventory():
  { data: ZipInventory | null, loading: boolean, error: string | null, refetch: () => void }
```

### `src/components/modules/provenance/MigrationStatus.tsx`

`MigrationStatus(): Tab[]` returning two tabs:

**Tab 1 — Migration overview**

Progress bar at top:
```
Migrated: [████████████░░░░░░] 1,247 / 1,560 files (80%)
```

Summary cards row:
| Migrated | Pending | Failed | Total |
|---------|---------|--------|-------|

Per-client breakdown table:

| Client | Migrated | Pending | Failed | Progress |
|--------|---------|---------|--------|---------|

Progress column: a narrow inline bar per row.

**Tab 2 — Failed migrations**

Table of `migrations` rows with `status = 'failed'`:

| Source path | Destination | Error | Attempted at |
|------------|-------------|-------|-------------|

If no failures: "No failed migrations."

### `src/components/modules/provenance/ZipStatus.tsx`

`ZipStatus(): Tab[]` returning two tabs:

**Tab 1 — Zip inventory**

Status summary cards:
| Total zips | Processed | Encrypted | Pending | Failed |
|-----------|---------|-----------|---------|--------|

Below: counts row:
```
New-to-corpus files found: N
```

Largest zips table (top 10):

| Path (truncated) | Size | Status | Contents | New finds |
|-----------------|------|--------|---------|-----------|

Status badge: `processed` → green, `encrypted` → amber,
`pending` → blue, `failed` → red.

**Tab 2 — Encrypted backlog**

Table of zips with `status = 'encrypted'`:

| Path | Size | Parent zip | Depth |
|------|------|-----------|-------|

Instruction banner at top:
```
These zips require a password to extract. Provide passwords to your
Aetheris operator and re-run the zip orchestrator.
```

If no encrypted zips: "No encrypted zips pending."

### Registration

Add both to the Provenance module alongside `CorpusOverview` and
`ClassificationReview`. All four are tabs within the single `provenance` module:

```typescript
// In registry.ts, the provenance module returns all tabs from all four components:
{
  id: "provenance",
  label: "Provenance",
  tabs: [
    ...CorpusOverview(),
    ...ClassificationReview(),
    ...MigrationStatus(),
    ...ZipStatus(),
  ]
}
```

## Acceptance criteria

- [ ] Migration progress bar shows correct percentage
- [ ] Per-client breakdown table renders (empty state if no migrations yet)
- [ ] Failed migrations tab shows error column content
- [ ] Zip summary cards show correct counts from `zip_inventory`
- [ ] Encrypted backlog tab shows instruction banner
- [ ] Largest zips table renders top 10
- [ ] "Not connected" placeholder in both components
- [ ] All tabs registered and reachable via the Provenance module
- [ ] No `any` TypeScript types
- [ ] Refresh button works on all tabs

## Files to create

- `src/hooks/useMigration.ts`
- `src/hooks/useZipInventory.ts`
- `src/components/modules/provenance/MigrationStatus.tsx`
- `src/components/modules/provenance/ZipStatus.tsx`
- `src/modules/registry.ts` (update to include all four components)

## Notes

**Progress bar.** Use a simple Tailwind `div` approach:
```tsx
<div className="w-full bg-gray-200 rounded-full h-3">
  <div
    className="bg-green-500 h-3 rounded-full transition-all"
    style={{ width: `${pct}%` }}
  />
</div>
```
No chart library needed.

**Pending count.** `pending` in `MigrationSummary` = classifications with
`status = 'approved'` that have no corresponding `migrations` row with
`status = 'migrated'`. This is the `migration_queue` view count. The Tauri
command `provenance_migration_summary` should query this directly.

**Empty state for new installs.** Both tabs should show meaningful empty
states when tables are empty — not blank screens. "No migrations yet —
run the migration agent to begin." and "No zips found in corpus."

**Tab ordering.** Stakeholders will use tabs in the order they work through
the pipeline: Overview → Classification review → Migration → Zips.
The `registry.ts` tab array should reflect this order.
