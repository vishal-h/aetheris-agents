# rig/p2: Live events UI

## Context

With the polling hook in place, `EventsContent` in `RunList.tsx` needs to
use it and surface live updates: new events appearing automatically, the
table scrolling to follow, a visible "Live" indicator, and the status badge
updating when the run completes.

## What to build

### Modify `src/components/modules/harness/RunList.tsx`

**`EventsContent` only.** No other components change.

#### 1. Polling

```typescript
const events = useRunEvents(
  selectedRun?.run_id ?? null,
  { polling: selectedRun?.status === 'running' },
);
const { isPolling } = events;
```

#### 2. Smart auto-scroll

Add a `ref` to the scrollable container and scroll to bottom on new events —
only if the user is already within 50px of the bottom:

```typescript
const scrollRef = useRef(null);

useEffect(() => {
  const el = scrollRef.current;
  if (!el) return;
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
  if (nearBottom) el.scrollTop = el.scrollHeight;
}, [events.data]);
```

Apply `ref={scrollRef}` to the `div` that wraps the events table.

#### 3. Live indicator

In the selected-run header row, show a pulsing dot when `isPolling` is true:

```tsx
{isPolling && (
  <span className="flex items-center gap-1.5 text-xs text-green-600">
    <span className="relative flex h-2 w-2">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
    </span>
    Live
  </span>
)}
```

#### 4. Status badge update on completion

Detect `run_complete` locally — no prop drilling required:

```typescript
const isComplete = (events.data ?? []).some(
  (ev) => ev.event_type === 'run_complete',
);
const displayStatus = isComplete ? 'done' : (selectedRun?.status ?? '');
```

Use `displayStatus` in the header badge instead of `selectedRun.status`.

## Acceptance criteria

- [ ] `EventsContent` passes `{ polling: selectedRun.status === 'running' }` to
      `useRunEvents`
- [ ] New events appear every ~2s when a running run is selected
- [ ] Scroll container has a `ref`; auto-scrolls to bottom on new events if
      within 50px of bottom
- [ ] Pulsing dot + "Live" label visible in header while `isPolling` is true
- [ ] When `run_complete` detected: polling stops (hook), status badge shows
      'done'
- [ ] When a non-running run is selected: no indicator, no polling
- [ ] Runs tab behaviour unchanged
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0

## Files to modify

- `src/components/modules/harness/RunList.tsx` — `EventsContent` only

## Notes

**Why not update `selectedRun` in the parent?** `selectedRun` lives in
`HarnessRoute`. Updating it on completion would trigger a full `useRunList`
refetch — unnecessary noise for a status badge. The local `isComplete`
override is sufficient; the Runs list reflects the true status next time
the user clicks Refresh.

**`animate-ping` is Tailwind built-in.** No extra dependency needed.
