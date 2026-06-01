# rig/p6: Diff cost row

## Context

The diff metadata table already computes `total_latency` from `llm_responded`
events. This issue adds three more rows: total input tokens, total output
tokens, and total cost. No new Tauri commands — the trajectories are already
loaded by `useRunDiff`.

All work is in `aetheris-agents/rig/`. Implement after p6-001 is merged
(shares `formatCost`, `formatTokens` helpers).

---

## What to build

### Updates to `useRunDiff.ts`

Add three helper functions (or import from a shared util if p6-001 extracted
them — check first):

```typescript
function computeTotalInputTokens(traj: TrajectoryFile): number | null {
  const events = traj.events.filter((e) => e.event_type === 'llm_responded');
  const hasData = events.some((e) => e.payload['input_tokens'] != null);
  if (!hasData) return null;
  return events.reduce(
    (sum, e) => sum + ((e.payload['input_tokens'] as number | null) ?? 0), 0
  );
}

function computeTotalOutputTokens(traj: TrajectoryFile): number | null {
  const events = traj.events.filter((e) => e.event_type === 'llm_responded');
  const hasData = events.some((e) => e.payload['output_tokens'] != null);
  if (!hasData) return null;
  return events.reduce(
    (sum, e) => sum + ((e.payload['output_tokens'] as number | null) ?? 0), 0
  );
}

function computeTotalCost(traj: TrajectoryFile): number | null {
  const events = traj.events.filter((e) => e.event_type === 'llm_responded');
  const hasData = events.some((e) => e.payload['cost_usd'] != null);
  if (!hasData) return null;
  return events.reduce(
    (sum, e) => sum + ((e.payload['cost_usd'] as number | null) ?? 0), 0
  );
}
```

Add three rows to the `fields` array in `computeDiff`:

```typescript
const fields: Array<[string, string, string]> = [
  ['Model',           a.meta.model,                b.meta.model],
  ['Provider',        a.meta.provider,             b.meta.provider],
  ['Mode',            a.meta.mode,                 b.meta.mode],
  ['Step count',      String(a.meta.step_count),   String(b.meta.step_count)],
  ['Max steps',       String(a.meta.max_steps),    String(b.meta.max_steps)],
  ['Total latency',   latA ? `${latA.toLocaleString()} ms` : '—',
                      latB ? `${latB.toLocaleString()} ms` : '—'],
  ['Terminal reason', terminalReason(a),           terminalReason(b)],
  ['Tools',           formatTools(a.meta.tools),   formatTools(b.meta.tools)],
  // ── new rows ──
  ['Input tokens',
    computeTotalInputTokens(a) !== null
      ? computeTotalInputTokens(a)!.toLocaleString() : '—',
    computeTotalInputTokens(b) !== null
      ? computeTotalInputTokens(b)!.toLocaleString() : '—'],
  ['Output tokens',
    computeTotalOutputTokens(a) !== null
      ? computeTotalOutputTokens(a)!.toLocaleString() : '—',
    computeTotalOutputTokens(b) !== null
      ? computeTotalOutputTokens(b)!.toLocaleString() : '—'],
  ['Total cost',
    (() => { const c = computeTotalCost(a); return c !== null ? (c >= 1 ? `$${c.toFixed(2)}` : `$${c.toFixed(4)}`) : '—'; })(),
    (() => { const c = computeTotalCost(b); return c !== null ? (c >= 1 ? `$${c.toFixed(2)}` : `$${c.toFixed(4)}`) : '—'; })()],
];
```

**Note on the IIFE cost formatting:** if `formatCost` has been extracted to a
shared util in p6-001, import and use it instead of the inline IIFE.

---

## Acceptance criteria

- [ ] Diff metadata table has three new rows: Input tokens, Output tokens,
      Total cost
- [ ] Rows show `—` for pre-instrumentation runs (null token/cost data)
- [ ] Rows are highlighted when values differ between Run A and Run B
- [ ] Cost format matches p6-001: `$0.0155` sub-$1, `$1.24` over $1
- [ ] No new Tauri commands
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0, zero TypeScript errors

---

## Files to modify

- `src/hooks/useRunDiff.ts` — add three helper functions, three rows to
  `fields` array in `computeDiff`

No new files. No route or registry changes.

---

## Notes

**Shared formatting.** If p6-001 extracted `formatCost` and `formatTokens`
to `src/lib/format.ts` or similar, import from there. If they're local to
`TrajectoryView.tsx`, duplicate them in `useRunDiff.ts` for now — a shared
util can be extracted in a cleanup pass.

**Null handling.** A run may have some `llm_responded` events with token data
and some without (mixed instrumented/pre-instrumentation steps). The `hasData`
check returns `null` only if no events have data at all. If some do and some
don't, the sum uses `?? 0` for missing values — partial sums are displayed
as-is. This matches the p6-001 behaviour.

**Row order.** The three new rows appear after "Tools" — cost-related
information grouped at the bottom of the metadata table.
