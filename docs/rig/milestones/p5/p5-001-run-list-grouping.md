# rig/p5: Run list grouping

## Context

The run list currently shows a flat table of up to 50 runs ordered by
started_at descending. With 444 runs in the DB this is unusable — most runs
are invisible, and there's no way to find runs by use case. This issue
replaces the flat list with collapsible use-case groups derived from run
label prefixes.

All work is in `aetheris-agents/rig/`. No new Tauri commands.

---

## What to build

### Label parsing

Run labels follow the convention `{use-case-slug}-{AgentLabel}-{RunId}`.
Extract the use case from the label prefix by matching against a known set:

```typescript
// src/components/modules/harness/RunList.tsx (or a shared util)

const USE_CASE_PREFIXES: Array<{ prefix: string; label: string }> = [
  { prefix: 'payslip',      label: 'Payslip' },
  { prefix: 'drive',        label: 'Drive' },
  { prefix: 'email',        label: 'Email' },
  { prefix: 'api-tenant',   label: 'API / Tenant' },
  { prefix: 'api-gateway',  label: 'API / Gateway' },
  { prefix: 'provenance',   label: 'Provenance' },
  { prefix: 'cap-matrix',   label: 'Capability Matrix' },
];

function classifyRun(label: string): string {
  const lower = label.toLowerCase();
  for (const { prefix, label: groupLabel } of USE_CASE_PREFIXES) {
    if (lower.startsWith(prefix)) return groupLabel;
  }
  return 'Unclassified';
}
```

Order matters — check more specific prefixes before less specific ones if
any overlap exists.

### Grouped run list component

Replace the current flat table in `RunList.tsx` with a grouped layout.

**Data shape:**
```typescript
interface RunGroup {
  label:    string;           // e.g. "Provenance"
  runs:     RunSummary[];
  expanded: boolean;          // collapse state
  showAll:  boolean;          // show more state
}
```

**Group rendering:**

Each group is a collapsible section:

```tsx
// Group header
<div
  className="flex items-center gap-2 px-4 py-2 bg-muted/50 border-b
             cursor-pointer hover:bg-muted/80 transition-colors select-none"
  onClick={() => toggleGroup(group.label)}
>
  {group.expanded
    ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
    : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
  <span className="text-sm font-medium">{group.label}</span>
  <span className="text-xs text-muted-foreground ml-1">
    ({group.runs.length})
  </span>
</div>

// Runs within group — only when expanded
{group.expanded && (
  <>
    {visibleRuns(group).map((run) => (
      <RunRow key={run.run_id} run={run} ... />
    ))}
    {group.runs.length > DEFAULT_SHOW && (
      <div className="px-4 py-2 border-b">
        <button
          className="text-xs text-muted-foreground hover:text-foreground
                     transition-colors"
          onClick={() => toggleShowAll(group.label)}
        >
          {group.showAll
            ? 'Show less'
            : `Show ${group.runs.length - DEFAULT_SHOW} more…`}
        </button>
      </div>
    )}
  </>
)}
```

**Constants:**
```typescript
const DEFAULT_SHOW = 10;
```

**`visibleRuns`:**
```typescript
function visibleRuns(group: RunGroup): RunSummary[] {
  return group.showAll ? group.runs : group.runs.slice(0, DEFAULT_SHOW);
}
```

**Group order:** use the order defined in `USE_CASE_PREFIXES`, with
"Unclassified" always last.

**All groups start expanded.** User can collapse any group. State is local
to the component — no persistence needed.

### Status filter interaction

The existing status filter (`All | Running | Done | Failed | Paused`) applies
before grouping — filter the full run list first, then group. This means a
group may disappear entirely when filtered (e.g. filtering to "Running" hides
all "Done" groups). That's correct behaviour.

```typescript
const filtered = runs.filter(
  (r) => statusFilter === 'all' || r.status === statusFilter
);
const groups = groupRuns(filtered);
```

### `harness_list_runs` limit

The current query has `LIMIT 50`. Remove the limit or raise it significantly
(e.g. 500) so all runs are available for grouping. With grouping, visual
overload is controlled by the collapse/show-more mechanism rather than a
hard DB limit.

This change is in `commands/harness.rs`:
```rust
// Before
"SELECT ... LIMIT 50"

// After
"SELECT ... LIMIT 500"
```

500 is a reasonable ceiling — if runs exceed this, the matrix-as-grouping-source
backlog item (which will add proper pagination per use case) addresses it.

### Handling the existing `selectedRun` state

The current `HarnessRoute` holds `selectedRun: RunSummary | null`. Clicking
a run row sets it. This doesn't change — `RunRow` still calls
`onSelect(run)` the same way. The grouping is purely a visual layer on top
of the same interaction model.

---

## Acceptance criteria

- [ ] Runs grouped by use case; group order matches `USE_CASE_PREFIXES`
- [ ] "Unclassified" group appears last, only if there are unclassified runs
- [ ] Each group shows run count in header
- [ ] Groups start expanded; clicking header collapses/expands
- [ ] Default 10 runs shown per group; "Show N more…" expands to all
- [ ] "Show less" collapses back to 10
- [ ] Status filter applies before grouping; empty groups are hidden
- [ ] `LIMIT 50` raised to `LIMIT 500` in `harness_list_runs`
- [ ] Clicking a run row still selects it and enables Events/Trajectory tabs
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0, zero TypeScript errors

---

## Files to modify

- `src-tauri/src/commands/harness.rs` — raise LIMIT to 500
- `src/components/modules/harness/RunList.tsx` — replace flat table with
  grouped layout; add `classifyRun`, `groupRuns`, `RunGroup` type,
  `DEFAULT_SHOW` constant

No new files, no new hooks, no registry changes.

---

## Notes

**`cap-matrix` prefix.** Capability matrix runs (e.g.
`cap-matrix-assemble-DLXNfA`) should appear in their own group, not
"Unclassified". The prefix `cap-matrix` is in `USE_CASE_PREFIXES`.

**Group state shape.** `expanded` and `showAll` per group can be stored as
`Record<string, boolean>` maps keyed by group label, rather than embedding
them in the `RunGroup` struct. Either approach compiles — use whichever
keeps the component cleaner.

**RunRow extraction.** If the existing run table renders rows inline in the
map, extract a `RunRow` component first to keep the grouped layout readable.
The row content (label, status badge, model, started, duration, steps, events)
doesn't change.

**Empty state.** If all groups are empty after filtering, show the existing
"No runs found" empty state centred in the content area.
