# rig/p1: Run list UI

## Context

With harness commands in place, this issue builds the Harness module UI:
a run list and an event log. Read-only, no auto-refresh yet (that's p2).

## What to build

### `src/components/modules/harness/RunList.tsx`

Tab factory function `RunList(): Tab[]` returning two tabs.

**Tab 1 — Runs**

Filter bar:
- Status filter dropdown: All | Running | Done | Failed | Paused
- Refresh button (right-aligned)

Run table, ordered by `started_at DESC`:

| Label | Status | Model | Started | Duration | Steps | Events |
|-------|--------|-------|---------|---------|-------|--------|

- Label: truncated to 45 chars, full label on hover (`title`)
- Status: `Badge` component with colour per status (see below)
- Model: truncated, just the model name not the provider
- Started: formatted as `YYYY-MM-DD HH:mm` local time
- Duration: computed from `started_at` and `finished_at`; "—" if no `finished_at`
- Steps: `step_count` from RunSummary
- Events: `event_count` from RunSummary

Clicking a row selects it and switches to the Events tab.

Empty state: "No runs found. Run an agent via `mix aetheris run`."

**Tab 2 — Events**

Shows events for the selected run. If no run selected:
"Select a run from the Runs tab to view its events."

Selected run header:
```
{label}  [{status badge}]  {model}  Started: {started_at}
```

Event table, ordered by `seq ASC`:

| Seq | Step | Type | Timestamp | Payload preview |
|-----|------|------|-----------|----------------|

- Seq: right-aligned, monospace
- Step: right-aligned
- Type: coloured text per event type (see below)
- Timestamp: time only (`HH:mm:ss.SSS`)
- Payload preview: first 120 chars of raw JSON, truncated

Event type colours (Tailwind text classes):
- `prompt_built` → `text-slate-500`
- `llm_called` → `text-purple-600`
- `llm_responded` → `text-purple-800`
- `tool_called` → `text-blue-600`
- `tool_result` → `text-blue-800`
- `error` → `text-red-600`
- `run_complete` → `text-green-600`
- `step_complete` → `text-slate-400`
- all others → `text-slate-600`

Status badge colours:
- `done` → `success`
- `running` → `warning`
- `failed` → `destructive`
- `paused` → `default`
- `idle` → `default`

### `src/hooks/useHarnessModule.ts`

Local state hook for the Harness module:

```typescript
function useHarnessModule() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [activeTab, setActiveTab]         = useState<'runs' | 'events'>('runs')
  const [statusFilter, setStatusFilter]   = useState<string>('all')
  // ...
}
```

Or manage state directly in the tab content components — whichever is cleaner.

### Not connected state

When `useHarnessStatus()` returns `connected: false`, both tabs render:

```
Not connected to Aetheris harness.
Set AETHERIS_DB_PATH to the path of aetheris/priv/aetheris.db and restart.
```

Use `NotConnected` from `components/modules/provenance/shared.tsx` but with
the correct env var name. Either extend the shared component to accept a
custom message, or create `components/modules/harness/shared.tsx` with a
harness-specific version.

### Route + registry

In `src/App.tsx`:
```tsx
import { RunList } from '@/components/modules/harness/RunList'

<Route path="/harness" element={<MainArea tabs={RunList()} />} />
```

In `src/modules/registry.ts`:
```typescript
import { Activity } from 'lucide-react'
// Add to Sidebar icon map: Activity

const harnessModule: Module = {
  id: 'harness',
  label: 'Harness',
  icon: 'Activity',
  sections: [
    {
      id: 'harness-runs',
      label: 'Runs',
      icon: 'Activity',
      path: '/harness',
    },
  ],
}

export const modules: Module[] = [harnessModule, f2Module, provenanceModule]
```

Place `harnessModule` first — it's the primary new feature.

## Acceptance criteria

- [ ] Harness module appears in sidebar
- [ ] Runs tab shows all past runs from `aetheris.db`
- [ ] Status filter works (client-side filter on fetched data)
- [ ] Clicking a run row switches to Events tab and shows that run's events
- [ ] Event type colours applied correctly
- [ ] Duration computed and formatted (e.g. "12s", "2m 4s")
- [ ] Payload preview truncated to 120 chars
- [ ] Empty state shown when no runs
- [ ] "Select a run" message shown when no run selected in Events tab
- [ ] "Not connected" shown when `AETHERIS_DB_PATH` absent
- [ ] Refresh button re-fetches run list
- [ ] No `any` TypeScript types
- [ ] No form tags — onClick handlers only (CLAUDE.md rule)
- [ ] Existing Provenance module unaffected

## Files to create/modify

- `src/components/modules/harness/RunList.tsx` (new)
- `src/hooks/useHarness.ts` (from p1-002, extend if needed)
- `src/modules/registry.ts` (add harnessModule)
- `src/App.tsx` (add /harness route)
- `src/components/shell/Sidebar.tsx` (add Activity icon)
- `src/hooks/types.ts` (already updated in p1-002)
- `src/hooks/index.ts` (export new hooks)

## Notes

**Duration formatting.** Compute from `started_at` and `finished_at`:
```typescript
function formatDuration(startedAt: string, finishedAt: string | null): string {
  if (!finishedAt) return '—'
  const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime()
  const secs = Math.round(ms / 1000)
  if (secs < 60) return `${secs}s`
  return `${Math.floor(secs / 60)}m ${secs % 60}s`
}
```

**Timestamp display.** `started_at` from SQLite is ISO 8601 UTC.
Use `new Date(ts).toLocaleString()` for the run list (date + time).
Use `new Date(ts).toISOString().slice(11, 23)` for the event log (time only).

**Payload preview.** The payload is raw JSON — don't try to parse it for
the preview. Just trim whitespace and truncate:
```typescript
const preview = row.payload.replace(/\s+/g, ' ').trim().slice(0, 120)
```

**Tab switching on row click.** The two tabs need shared state for the
selected run. Either lift state to the `RunList()` factory level (tricky
since tabs are static objects), or use a React context, or use a simple
module-level variable. The simplest: use a `useRef` or `useState` at the
component level with a callback passed down. See how `ClassificationReview`
handles its two-tab state for reference.

**Status filter is client-side.** Fetch all runs (up to limit), filter
in the component. No need for a server-side status filter parameter.
