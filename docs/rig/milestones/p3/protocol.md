# Orchestrator Protocol

Newline-delimited JSON over stdin/stdout between Rig and the orchestrator
script. One JSON object per line. All messages are UTF-8.

---

## Script → Rig (stdout)

### `plan`

Emitted once after the planning delay. Rig transitions from `planning` to
`plan_ready`.

```json
{
  "type": "plan",
  "request": "the original user request",
  "steps": [
    { "id": "step-1", "agent": "scan_agent.exs",   "description": "Scan corpus for relevant files" },
    { "id": "step-2", "agent": "report_agent.exs",  "description": "Generate summary report" }
  ]
}
```

### `step_started`

Emitted when a step begins executing. Rig marks that step as `running`.

```json
{ "type": "step_started", "step_id": "step-1" }
```

### `step_complete`

Emitted when a step finishes. Rig marks that step as `done` or `failed`.

```json
{ "type": "step_complete", "step_id": "step-1", "status": "done" }
```

On failure, an optional `error` field contains the stderr from the failed
tool invocation:

```json
{ "type": "step_complete", "step_id": "step-1", "status": "failed",
  "error": "Folder '202605-may' not found under payslips/." }
```

`status` is either `"done"` or `"failed"`. `error` is present only when
`status` is `"failed"`.

### `orchestration_complete`

Emitted after all steps finish. Rig transitions to `done`. The script exits
after this message.

```json
{ "type": "orchestration_complete", "status": "done" }
```

### `orchestration_cancelled`

Emitted when the user rejects the plan. Rig transitions to `cancelled`. The
script exits after this message.

```json
{ "type": "orchestration_cancelled" }
```

---

## Rig → Script (stdin)

### `approval`

Written to stdin after the user approves or rejects the plan.

```json
{ "type": "approval", "approved": true }
{ "type": "approval", "approved": false }
```

---

## Request delivery

The user's request string is passed to the script via the `ORCHESTRATOR_REQUEST`
environment variable (not as a command-line argument, to avoid Mix arg
parsing ambiguity).

---

## Message sequence

```
[Rig sets ORCHESTRATOR_REQUEST, spawns script]
Script: sleeps 2s
Script → Rig: plan
[Rig shows plan, waits for user action]
Rig → Script: approval (approved: true or false)

If approved:
  Script → Rig: step_started (step-1)
  Script → Rig: step_complete (step-1)
  Script → Rig: step_started (step-2)
  Script → Rig: step_complete (step-2)
  Script → Rig: orchestration_complete
  [Script exits]

If rejected:
  Script → Rig: orchestration_cancelled
  [Script exits]
```

---

## TypeScript types

Add to `src/hooks/types.ts`:

```typescript
export interface PlanStep {
  id:          string;
  agent:       string;
  description: string;
}

export interface OrchestratorPlan {
  type:    'plan';
  request: string;
  steps:   PlanStep[];
}

export interface PollResult {
  messages: Record<string, unknown>[];  // raw parsed JSON objects; check 'type' field
  done:     boolean;                    // true when script process has exited
}

export type OrchestratorPhase =
  | 'idle'
  | 'planning'
  | 'plan_ready'
  | 'executing'
  | 'done'
  | 'cancelled'
  | 'error';

export type StepStatus = 'pending' | 'running' | 'done' | 'failed';
```
