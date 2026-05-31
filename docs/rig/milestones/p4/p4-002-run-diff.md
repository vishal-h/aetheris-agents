# rig/p4: Run diff

## Context

With `trajectory_load` in place (p4-001), this issue builds the diff view:
select two runs, compare their metadata and step paths side by side. The
primary use case is understanding how a change in model, provider, or prompt
affects agent behaviour across otherwise equivalent runs.

All work is in `aetheris-agents/rig/`.

---

## What to build

No new Tauri commands — `trajectory_load` (p4-001) is called twice, once per
run. The diff computation lives entirely on the frontend.

---

### TypeScript types (add to `src/hooks/types.ts`)

```typescript
export interface MetaDiffRow {
  field:    string;
  a:        string;
  b:        string;
  differs:  boolean;
}

export interface StepDiffEntry {
  step:       number;
  tools_a:    string[];   // tool_called event tool_name values in this step, run A
  tools_b:    string[];   // same for run B
  differs:    boolean;    // true if tool lists differ
  only_in_a:  boolean;    // step exists in A but not B
  only_in_b:  boolean;    // step exists in B but not A
}

export interface RunDiff {
  meta_rows:  MetaDiffRow[];
  step_rows:  StepDiffEntry[];
  any_differs: boolean;
}
```

Export all three from `src/hooks/index.ts`.

---

### `src/hooks/useRunDiff.ts`

Loads both trajectories and computes the diff. All diff logic is in this hook
— the view is purely presentational.

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { TrajectoryFile, RunDiff, MetaDiffRow, StepDiffEntry } from './types';

function formatTools(tools: string[]): string {
  return tools.length ? tools.join(', ') : '—';
}

function computeTotalLatency(traj: TrajectoryFile): number {
  return traj.events
    .filter((e) => e.event_type === 'llm_responded')
    .reduce((sum, e) => sum + ((e.payload['latency_ms'] as number) ?? 0), 0);
}

function toolsForStep(traj: TrajectoryFile, step: number): string[] {
  return traj.events
    .filter((e) => e.step === step && e.event_type === 'tool_called')
    .map((e) => (e.payload['tool_name'] as string) ?? '?');
}

function terminalReason(traj: TrajectoryFile): string {
  const e = traj.events.find((e) => e.event_type === 'run_complete');
  return (e?.payload['reason'] as string) ?? '—';
}

function computeDiff(a: TrajectoryFile, b: TrajectoryFile): RunDiff {
  // ── Metadata rows ────────────────────────────────────────────────────────
  const latA = computeTotalLatency(a);
  const latB = computeTotalLatency(b);

  const fields: Array<[string, string, string]> = [
    ['Model',           a.meta.model,                          b.meta.model],
    ['Provider',        a.meta.provider,                       b.meta.provider],
    ['Mode',            a.meta.mode,                           b.meta.mode],
    ['Step count',      String(a.meta.step_count),             String(b.meta.step_count)],
    ['Max steps',       String(a.meta.max_steps),              String(b.meta.max_steps)],
    ['Total latency',   latA ? `${latA.toLocaleString()} ms` : '—',
                        latB ? `${latB.toLocaleString()} ms` : '—'],
    ['Terminal reason', terminalReason(a),                     terminalReason(b)],
    ['Tools',           formatTools(a.meta.tools),             formatTools(b.meta.tools)],
  ];

  const meta_rows: MetaDiffRow[] = fields.map(([field, va, vb]) => ({
    field,
    a: va,
    b: vb,
    differs: va !== vb,
  }));

  // ── Step path ────────────────────────────────────────────────────────────
  const stepsA = new Set(a.events.map((e) => e.step));
  const stepsB = new Set(b.events.map((e) => e.step));
  const allSteps = Array.from(new Set([...stepsA, ...stepsB])).sort((x, y) => x - y);

  const step_rows: StepDiffEntry[] = allSteps.map((step) => {
    const inA = stepsA.has(step);
    const inB = stepsB.has(step);
    const tools_a = inA ? toolsForStep(a, step) : [];
    const tools_b = inB ? toolsForStep(b, step) : [];
    const differs = !inA || !inB || JSON.stringify(tools_a) !== JSON.stringify(tools_b);
    return {
      step,
      tools_a,
      tools_b,
      differs,
      only_in_a: inA && !inB,
      only_in_b: inB && !inA,
    };
  });

  return {
    meta_rows,
    step_rows,
    any_differs: meta_rows.some((r) => r.differs) || step_rows.some((r) => r.differs),
  };
}

export function useRunDiff(runIdA: string | null, runIdB: string | null) {
  const [trajectoryA, setTrajectoryA] = useState<TrajectoryFile | null>(null);
  const [trajectoryB, setTrajectoryB] = useState<TrajectoryFile | null>(null);
  const [diff,        setDiff]        = useState<RunDiff | null>(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  useEffect(() => {
    if (!runIdA || !runIdB) {
      setTrajectoryA(null);
      setTrajectoryB(null);
      setDiff(null);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([
      invoke<TrajectoryFile>('trajectory_load', { run_id: runIdA }),
      invoke<TrajectoryFile>('trajectory_load', { run_id: runIdB }),
    ])
      .then(([a, b]) => {
        setTrajectoryA(a);
        setTrajectoryB(b);
        setDiff(computeDiff(a, b));
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, [runIdA, runIdB]);

  return { trajectoryA, trajectoryB, diff, loading, error };
}
```

Export from `src/hooks/index.ts`.

---

### `src/components/modules/harness/DiffView.tsx`

Standalone component — not a tab. Renders in the `/diff` route.

Two phases: **selection** (pick Run A and Run B) and **comparison** (metadata
table + step path).

```tsx
import { useState } from 'react';
import { GitCompare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useHarness } from '@/hooks/useHarness';
import { useRunDiff } from '@/hooks/useRunDiff';

export function DiffView() {
  const { runs } = useHarness();

  const [runIdA, setRunIdA] = useState('');
  const [runIdB, setRunIdB] = useState('');
  const [comparing, setComparing] = useState(false);
  const [activeA,   setActiveA]   = useState<string | null>(null);
  const [activeB,   setActiveB]   = useState<string | null>(null);

  const { diff, loading, error } = useRunDiff(
    comparing ? activeA : null,
    comparing ? activeB : null,
  );

  function handleCompare() {
    setActiveA(runIdA);
    setActiveB(runIdB);
    setComparing(true);
  }

  function handleReset() {
    setComparing(false);
    setDiff_internal();
  }

  // ── Selection phase ────────────────────────────────────────────────────
  const selectionPanel = (
    <div className="flex flex-col gap-6 max-w-xl">
      <div className="flex items-center gap-2 text-lg font-semibold">
        <GitCompare className="h-5 w-5" />
        Compare runs
      </div>

      <RunPicker
        label="Run A"
        value={runIdA}
        onChange={setRunIdA}
        runs={runs ?? []}
        exclude={runIdB}
      />
      <RunPicker
        label="Run B"
        value={runIdB}
        onChange={setRunIdB}
        runs={runs ?? []}
        exclude={runIdA}
      />

      <Button
        onClick={handleCompare}
        disabled={!runIdA || !runIdB || runIdA === runIdB}
      >
        Compare
      </Button>
    </div>
  );

  // ── Comparison phase ───────────────────────────────────────────────────
  if (comparing) {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          Loading trajectories…
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6 flex flex-col gap-3">
          <p className="text-sm text-red-600">{error}</p>
          <Button variant="outline" onClick={handleReset}>Back</Button>
        </div>
      );
    }

    if (!diff) return null;

    return (
      <div className="p-6 flex flex-col gap-6 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold">
            <GitCompare className="h-5 w-5" />
            <span className="font-mono text-sm">{activeA}</span>
            <span className="text-muted-foreground">vs</span>
            <span className="font-mono text-sm">{activeB}</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleReset}>
            New comparison
          </Button>
        </div>

        {/* Metadata table */}
        <section>
          <h3 className="text-sm font-semibold mb-2">Metadata</h3>
          <div className="rounded-md border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground w-36">
                    Field
                  </th>
                  <th className="text-left px-3 py-2 font-medium">Run A</th>
                  <th className="text-left px-3 py-2 font-medium">Run B</th>
                </tr>
              </thead>
              <tbody>
                {diff.meta_rows.map((row) => (
                  <tr
                    key={row.field}
                    className={`border-b last:border-b-0 ${
                      row.differs ? 'bg-amber-50' : ''
                    }`}
                  >
                    <td className="px-3 py-2 text-muted-foreground">{row.field}</td>
                    <td className={`px-3 py-2 font-mono ${row.differs ? 'font-medium' : ''}`}>
                      {row.a}
                    </td>
                    <td className={`px-3 py-2 font-mono ${row.differs ? 'font-medium' : ''}`}>
                      {row.b}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Step path */}
        <section>
          <h3 className="text-sm font-semibold mb-2">Step path</h3>
          <div className="rounded-md border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground w-20">
                    Step
                  </th>
                  <th className="text-left px-3 py-2 font-medium">Run A — tools</th>
                  <th className="text-left px-3 py-2 font-medium">Run B — tools</th>
                </tr>
              </thead>
              <tbody>
                {diff.step_rows.map((row) => (
                  <tr
                    key={row.step}
                    className={`border-b last:border-b-0 ${
                      row.differs ? 'bg-amber-50' : ''
                    }`}
                  >
                    <td className="px-3 py-2 text-muted-foreground font-mono">
                      {row.step}
                    </td>
                    <td className={`px-3 py-2 font-mono text-xs ${
                      row.only_in_b ? 'text-muted-foreground italic' : ''
                    }`}>
                      {row.only_in_b ? '—' : (row.tools_a.join(', ') || 'no tools')}
                    </td>
                    <td className={`px-3 py-2 font-mono text-xs ${
                      row.only_in_a ? 'text-muted-foreground italic' : ''
                    }`}>
                      {row.only_in_a ? '—' : (row.tools_b.join(', ') || 'no tools')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    );
  }

  return <div className="p-6">{selectionPanel}</div>;
}

// ── Run picker ────────────────────────────────────────────────────────────────
interface RunPickerProps {
  label:    string;
  value:    string;
  onChange: (id: string) => void;
  runs:     Array<{ run_id: string; label: string; model: string; status: string }>;
  exclude:  string;
}

function RunPicker({ label, value, onChange, runs, exclude }: RunPickerProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium">{label}</label>
      <select
        className="rounded-md border border-input bg-background px-3 py-2 text-sm
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select a run…</option>
        {runs
          .filter((r) => r.run_id !== exclude)
          .map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.run_id} — {r.label} ({r.model}, {r.status})
            </option>
          ))}
      </select>
    </div>
  );
}
```

**Note:** `handleReset` references `setDiff_internal` which is not needed —
the diff is controlled by `activeA`/`activeB` via `useRunDiff`. Remove the
`setDiff_internal()` call; just call `setComparing(false)` and optionally
clear `setActiveA(null)` / `setActiveB(null)`.

---

### Route + registry

In `src/App.tsx`:
```tsx
import { DiffView } from '@/components/modules/harness/DiffView';

<Route path="/diff" element={
  <div className="flex flex-1 flex-col h-full bg-background overflow-y-auto">
    <DiffView />
  </div>
} />
```

In `src/modules/registry.ts` — extend `harnessModule` with a second section:
```typescript
const harnessModule: Module = {
  id: 'harness',
  label: 'Harness',
  icon: 'Activity',
  sections: [
    { id: 'runs',  label: 'Runs',  icon: 'Activity',    path: '/harness' },
    { id: 'diff',  label: 'Diff',  icon: 'GitCompare',  path: '/diff'    },
  ],
};
```

Add `GitCompare` to `iconMap` in `Sidebar.tsx`:
```typescript
import { Activity, GitCompare, /* existing imports */ } from 'lucide-react';
// …
GitCompare,
```

---

## Acceptance criteria

- [ ] `useRunDiff` loads both trajectories in parallel via `Promise.all`
- [ ] `computeDiff` produces correct `MetaDiffRow[]` for all 8 fields
- [ ] `computeTotalLatency` sums `latency_ms` from all `llm_responded` events
- [ ] `terminalReason` reads `reason` from `run_complete` event payload
- [ ] `toolsForStep` returns `tool_name` values from `tool_called` events for
      that step
- [ ] Rows where A ≠ B are highlighted (`bg-amber-50`)
- [ ] Steps present only in A show `—` in the Run B column (and vice versa)
- [ ] "New comparison" resets to the selection phase
- [ ] Diff section appears in Harness sidebar entry (GitCompare icon, `/diff`)
- [ ] `GitCompare` added to `iconMap` in `Sidebar.tsx`
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0, zero TypeScript errors

---

## Files to create/modify

**Create:**
- `src/hooks/useRunDiff.ts`
- `src/components/modules/harness/DiffView.tsx`

**Modify:**
- `src/hooks/types.ts` — add `MetaDiffRow`, `StepDiffEntry`, `RunDiff`
- `src/hooks/index.ts` — export `useRunDiff` and new types
- `src/modules/registry.ts` — add Diff section to `harnessModule`
- `src/App.tsx` — add `/diff` route
- `src/components/shell/Sidebar.tsx` — add `GitCompare` to `iconMap`

---

## Notes

**`useHarness` for run list.** `DiffView` calls `useHarness()` to get the
run list for the pickers. Check the existing hook's return shape — the runs
array is likely returned as `runs` with `RunSummary` elements. Use the same
hook, do not add a new Tauri call.

**`handleReset` cleanup.** The spec above has a `setDiff_internal()` artefact
— remove it. Reset is: `setComparing(false)`. The `useRunDiff` effect clears
when `comparing` is false (because `activeA`/`activeB` passed as null). You
may also clear `setActiveA(null)` / `setActiveB(null)` on reset for tidiness.

**Amber highlight.** `bg-amber-50` on differing rows is deliberately subtle —
it shows contrast without alarming the user. Applies to both the metadata
table and the step path table.

**Tool list comparison.** `toolsForStep` returns tools in seq order. The
comparison uses `JSON.stringify` equality — order matters. Two steps that
call the same tools in different order will show as differing. This is
intentional: order reflects the actual decision sequence.

**No event-level diff.** This issue covers metadata + tool path only. Full
event-level structural diff (aligning payloads across runs) is deferred to
a future issue.

**Dark mode.** `bg-amber-50` is a light-mode colour. If the app uses a dark
theme, substitute `dark:bg-amber-900/20` or similar. Check the existing
provenance components for the convention used.
