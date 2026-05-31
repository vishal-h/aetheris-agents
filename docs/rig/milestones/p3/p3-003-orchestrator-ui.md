# rig/p3: Orchestrator UI

## Context

With the mock script and Rust backend in place, this issue builds the
Orchestrator module: a single-view workflow UI with five states.

## What to build

### `src/hooks/useOrchestrator.ts`

A single hook that owns all orchestrator state and drives the polling loop.

```typescript
import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import {
  OrchestratorPhase, OrchestratorPlan, PollResult, StepStatus
} from './types';

export function useOrchestrator() {
  const [phase,        setPhase]        = useState<OrchestratorPhase>('idle');
  const [jobId,        setJobId]        = useState<string | null>(null);
  const [plan,         setPlan]         = useState<OrchestratorPlan | null>(null);
  const [stepStatuses, setStepStatuses] = useState<Record<string, StepStatus>>({});
  const [error,        setError]        = useState<string | null>(null);

  // Process one message from the poll buffer
  const processMessage = useCallback((msg: Record<string, unknown>) => {
    switch (msg.type) {
      case 'plan':
        setPlan(msg as unknown as OrchestratorPlan);
        setStepStatuses(
          Object.fromEntries(
            (msg.steps as { id: string }[]).map((s) => [s.id, 'pending' as StepStatus])
          )
        );
        setPhase('plan_ready');
        break;
      case 'step_started':
        setStepStatuses((prev) => ({ ...prev, [msg.step_id as string]: 'running' as StepStatus }));
        break;
      case 'step_complete':
        setStepStatuses((prev) => ({
          ...prev,
          [msg.step_id as string]: (msg.status === 'done' ? 'done' : 'failed') as StepStatus,
        }));
        break;
      case 'orchestration_complete':
        setPhase('done');
        break;
      case 'orchestration_cancelled':
        setPhase('cancelled');
        break;
    }
  }, []);

  // Poll while a job is active and not in a terminal phase
  useEffect(() => {
    const terminal: OrchestratorPhase[] = ['idle', 'done', 'cancelled', 'error'];
    if (!jobId || terminal.includes(phase)) return;

    const id = setInterval(async () => {
      try {
        const result = await invoke<PollResult>('orchestrate_poll', { job_id: jobId });
        result.messages.forEach(processMessage);
      } catch (e) {
        setError(String(e));
        setPhase('error');
      }
    }, 1000);

    return () => clearInterval(id);
  }, [jobId, phase, processMessage]);

  const start = useCallback(async (request: string) => {
    setPhase('planning');
    setPlan(null);
    setStepStatuses({});
    setError(null);
    try {
      const id = await invoke<string>('orchestrate_start', { request });
      setJobId(id);
    } catch (e) {
      setError(String(e));
      setPhase('error');
    }
  }, []);

  const approve = useCallback(async (approved: boolean) => {
    if (!jobId) return;
    if (approved) setPhase('executing');
    try {
      await invoke('orchestrate_approve', { job_id: jobId, approved });
      if (!approved) setPhase('cancelled');
    } catch (e) {
      setError(String(e));
      setPhase('error');
    }
  }, [jobId]);

  const cancel = useCallback(async () => {
    if (!jobId) return;
    await invoke('orchestrate_cancel', { job_id: jobId }).catch(() => {});
    setPhase('cancelled');
  }, [jobId]);

  const reset = useCallback(() => {
    setPhase('idle');
    setJobId(null);
    setPlan(null);
    setStepStatuses({});
    setError(null);
  }, []);

  return { phase, plan, stepStatuses, error, start, approve, cancel, reset };
}
```

### `src/components/modules/orchestrator/OrchestratorView.tsx`

Single-view component. No tabs — renders directly into the route.

**Layout:** centred column, max-width ~600px, padded.

**State rendering:**

`idle` — textarea + Run button:
```tsx
<div className="flex flex-col gap-4">
  <h2 className="text-lg font-semibold">Orchestrator</h2>
  <textarea
    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm
               placeholder:text-muted-foreground focus-visible:outline-none
               focus-visible:ring-2 focus-visible:ring-ring resize-none"
    rows={3}
    placeholder="Describe what you want to do…"
    value={request}
    onChange={(e) => setRequest(e.target.value)}
  />
  <Button onClick={() => start(request)} disabled={!request.trim()}>
    Run
  </Button>
</div>
```

`planning` — spinner:
```tsx
<div className="flex items-center gap-3 text-muted-foreground">
  <Loader2 className="h-5 w-5 animate-spin" />
  <span>Planning…</span>
</div>
```

`plan_ready` — plan steps + Approve / Cancel:
```tsx
<div className="flex flex-col gap-4">
  <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
  <div className="flex flex-col gap-2">
    {plan.steps.map((step, i) => (
      <div key={step.id} className="rounded-md border p-3">
        <span className="text-xs text-muted-foreground">Step {i + 1}</span>
        <p className="font-medium">{step.description}</p>
        <p className="text-xs text-muted-foreground">{step.agent}</p>
      </div>
    ))}
  </div>
  <div className="flex gap-3">
    <Button onClick={() => approve(true)}>Approve</Button>
    <Button variant="outline" onClick={() => approve(false)}>Cancel</Button>
  </div>
</div>
```

`executing` — same step list with live status indicators:
- `pending` → muted bullet (`·`)
- `running` → `animate-spin` Loader2
- `done`    → green CheckCircle2
- `failed`  → red XCircle

`done`:
```tsx
<div className="flex flex-col items-center gap-4">
  <CheckCircle2 className="h-10 w-10 text-green-600" />
  <p className="font-medium">Done</p>
  <Button variant="outline" onClick={reset}>Run another</Button>
</div>
```

`cancelled`:
```tsx
<div className="flex flex-col items-center gap-4">
  <p className="text-muted-foreground">Cancelled.</p>
  <Button variant="outline" onClick={reset}>Run another</Button>
</div>
```

`error`:
```tsx
<div className="flex flex-col gap-3">
  <p className="text-sm text-red-600">{error}</p>
  <Button variant="outline" onClick={reset}>Run another</Button>
</div>
```

### Route + registry

In `src/App.tsx`:
```tsx
import { OrchestratorView } from '@/components/modules/orchestrator/OrchestratorView';

<Route path="/orchestrator" element={
  <div className="flex flex-1 flex-col h-full bg-background overflow-y-auto p-8">
    <OrchestratorView />
  </div>
} />
```

In `src/modules/registry.ts` (add after harnessModule):
```typescript
const orchestratorModule: Module = {
  id: 'orchestrator',
  label: 'Orchestrator',
  icon: 'Sparkles',
  sections: [
    { id: 'orchestrator', label: 'Orchestrator', icon: 'Sparkles', path: '/orchestrator' },
  ],
};

export const modules: Module[] = [harnessModule, orchestratorModule, f2Module, provenanceModule];
```

Add `Sparkles` to `iconMap` in `Sidebar.tsx`.

Export `useOrchestrator` from `src/hooks/index.ts`.

## Acceptance criteria

- [ ] Orchestrator module appears in sidebar (Sparkles icon, second entry)
- [ ] `idle` → textarea + Run button
- [ ] `planning` → spinner for ~2s
- [ ] `plan_ready` → two steps listed + Approve / Cancel
- [ ] Approve → `executing` → steps animate through pending → running → done
- [ ] After last step → `done` with CheckCircle2
- [ ] Cancel from `plan_ready` → `cancelled`
- [ ] "Run another" resets to `idle` from any terminal state
- [ ] `error` state renders error message + "Run another"
- [ ] No TypeScript `any`
- [ ] No `<form>` tags — onClick/onChange handlers only
- [ ] `bun run build` exits 0

## Files to create/modify

- `src/hooks/useOrchestrator.ts` (new)
- `src/components/modules/orchestrator/OrchestratorView.tsx` (new)
- `src/hooks/index.ts` (export useOrchestrator)
- `src/modules/registry.ts` (add orchestratorModule)
- `src/App.tsx` (add /orchestrator route)
- `src/components/shell/Sidebar.tsx` (add Sparkles to iconMap)

## Notes

**`OrchestratorView` manages local `request` string state.** The request
textarea is local to the component — `useOrchestrator` only receives it
via `start(request)`. Keep the hook free of UI concerns.

**Poll only while active.** The effect's dependency on `phase` ensures
polling stops the moment a terminal phase is set — no extra messages
processed after `done` or `cancelled`.

**No `<textarea>` inside a `<form>`.** Use `onChange` + local state.
The Run button calls `start(request)` directly via `onClick`.
