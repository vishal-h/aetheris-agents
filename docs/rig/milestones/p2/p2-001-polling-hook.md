# rig/p2: Polling hook

## Context

`useRunEvents` currently fetches once when `runId` changes. For live
monitoring it needs to poll every 2s when a run is active, and stop
automatically when `run_complete` appears in the event stream.

## What to build

### Modify `src/hooks/useHarness.ts`

Add an optional second argument to `useRunEvents`:

```typescript
export function useRunEvents(
  runId: string | null,
  options?: { polling?: boolean },
): AsyncState & { isPolling: boolean }
```

**Add internal state:**

```typescript
const [activelyPolling, setActivelyPolling] = useState(false);
```

**Three new effects (add alongside the existing fetch effect):**

Effect 1 — sync `activelyPolling` with caller's intent:
```typescript
useEffect(() => {
  setActivelyPolling(options?.polling ?? false);
}, [options?.polling]);
```

Effect 2 — stop polling when `run_complete` appears:
```typescript
useEffect(() => {
  if (!data || !activelyPolling) return;
  const done = data.some((ev) => ev.event_type === 'run_complete');
  if (done) setActivelyPolling(false);
}, [data, activelyPolling]);
```

Effect 3 — run the interval:
```typescript
useEffect(() => {
  if (!activelyPolling || !runId) return;
  const id = setInterval(fetch, 2000);
  return () => clearInterval(id);
}, [activelyPolling, runId, fetch]);
```

**Update the return value to expose `isPolling`:**
```typescript
return { data, loading, error, refetch: fetch, isPolling: activelyPolling };
```

### No other files change

Existing callers that omit the second argument are unaffected — `activelyPolling`
starts `false`, no interval is set.

## Acceptance criteria

- [ ] `useRunEvents` accepts optional `{ polling?: boolean }` second argument
- [ ] When `polling: true`, fetches every 2000ms
- [ ] Polling stops automatically when `run_complete` event appears in data
- [ ] Interval is cleared on unmount and when `runId` becomes null
- [ ] `isPolling: boolean` exposed in return value
- [ ] Existing callers with no second argument are unaffected
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0

## Notes

**Why `activelyPolling` internal state rather than just `options?.polling`?**
The hook needs to stop itself when `run_complete` appears, independently of
what the parent passes. If the interval effect depended on `options?.polling`
directly, only the parent could stop polling — the hook couldn't self-terminate.

**`setInterval` vs `setTimeout` loop.** `setInterval` is correct here.
A `setTimeout` loop allows drift compensation but 2s polling of a SQLite
read doesn't need sub-second precision.
