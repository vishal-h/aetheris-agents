# rig/p6: Trajectory summary

## Context

The Trajectory tab already loads the full `TrajectoryFile` including all
`llm_responded` event payloads, which now contain `input_tokens`,
`output_tokens`, and `cost_usd`. This issue adds a token/cost summary to the
meta panel — computed client-side from the already-loaded data. No new Tauri
commands.

All work is in `aetheris-agents/rig/`.

---

## What to build

### Summary computation (in `TrajectoryView.tsx`)

Add a helper that reduces the events array to a summary:

```typescript
interface TokenSummary {
  input_tokens:  number | null;
  output_tokens: number | null;
  cost_usd:      number | null;
  llm_calls:     number;
}

function computeTokenSummary(events: TrajectoryEvent[]): TokenSummary {
  const llmEvents = events.filter((e) => e.event_type === 'llm_responded');

  if (llmEvents.length === 0) {
    return { input_tokens: null, output_tokens: null, cost_usd: null, llm_calls: 0 };
  }

  // Check if any event has instrumented data
  const hasData = llmEvents.some(
    (e) => e.payload['cost_usd'] != null
  );

  if (!hasData) {
    return { input_tokens: null, output_tokens: null, cost_usd: null, llm_calls: llmEvents.length };
  }

  const input_tokens = llmEvents.reduce(
    (sum, e) => sum + ((e.payload['input_tokens'] as number | null) ?? 0), 0
  );
  const output_tokens = llmEvents.reduce(
    (sum, e) => sum + ((e.payload['output_tokens'] as number | null) ?? 0), 0
  );
  const cost_usd = llmEvents.reduce(
    (sum, e) => sum + ((e.payload['cost_usd'] as number | null) ?? 0), 0
  );

  return { input_tokens, output_tokens, cost_usd, llm_calls: llmEvents.length };
}
```

### Cost formatting helpers

```typescript
function formatCost(usd: number | null): string {
  if (usd === null) return '—';
  if (usd >= 1) return `$${usd.toFixed(2)}`;
  return `$${usd.toFixed(4)}`;
}

function formatTokens(n: number | null): string {
  if (n === null) return '—';
  return n.toLocaleString();
}
```

### Summary bar in the meta panel

Add a summary row to the meta panel grid, below the existing `MetaRow`
entries and above the system/user prompt expandable texts. Only render
when `llm_calls > 0`:

```tsx
// Inside the metaOpen block, after the Tools row:
{(() => {
  const summary = computeTokenSummary(events);
  if (summary.llm_calls === 0) return null;
  return (
    <>
      <MetaRow
        label="LLM calls"
        value={String(summary.llm_calls)}
      />
      <MetaRow
        label="Input tokens"
        value={formatTokens(summary.input_tokens)}
      />
      <MetaRow
        label="Output tokens"
        value={formatTokens(summary.output_tokens)}
      />
      <MetaRow
        label="Cost"
        value={formatCost(summary.cost_usd)}
      />
    </>
  );
})()}
```

If `summary.input_tokens` is `null` (pre-instrumentation run), `MetaRow`
shows `—` via `formatTokens`. Same for cost.

---

### New TypeScript types (add to `src/hooks/types.ts`)

```typescript
export interface TokenSummary {
  input_tokens:  number | null;
  output_tokens: number | null;
  cost_usd:      number | null;
  llm_calls:     number;
}
```

Export from `src/hooks/index.ts`.

---

## Acceptance criteria

- [ ] `computeTokenSummary` correctly sums `input_tokens`, `output_tokens`,
      `cost_usd` from `llm_responded` events
- [ ] Returns all-null summary for pre-instrumentation runs (no `cost_usd`
      in any event)
- [ ] Meta panel shows LLM calls, Input tokens, Output tokens, Cost rows
      when the run has LLM events
- [ ] Cost format: `$0.0155` for sub-$1, `$1.24` for over $1
- [ ] Token counts formatted with `toLocaleString()` (e.g. `12,519`)
- [ ] `—` displayed for null values — not `$0.0000` or `0`
- [ ] No new Tauri commands
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0, zero TypeScript errors

---

## Files to modify

- `src/components/modules/harness/TrajectoryView.tsx` — add
  `computeTokenSummary`, `formatCost`, `formatTokens`, summary rows in
  meta panel
- `src/hooks/types.ts` — add `TokenSummary`
- `src/hooks/index.ts` — export `TokenSummary`

No new files needed.

---

## Notes

**IIFE pattern for conditional multi-row render.** The `{(() => { ... })()}`
pattern avoids introducing a named sub-component for a small conditional
block. Acceptable here since the block is short. If it grows, extract a
`TokenSummaryRows` component instead.

**`cost_usd` accumulation.** Some `llm_responded` events may have
`cost_usd: null` even within an instrumented run (e.g. a tool-call response
from a model not in the pricing table). The `?? 0` fallback in the reduce
handles this — the sum is based on whatever cost data is available. If
`hasData` is true but some events have null cost, the total is a partial
sum. This is acceptable — display as-is.

**No per-step breakdown.** This issue adds run-level totals only. Per-step
token counts are visible by expanding individual `llm_responded` event rows
(already implemented). No new per-step UI needed.
