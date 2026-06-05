# rig/p8-001: Plan view enrichment

## Context

The Orchestrator plan view shows description and agent path per step but no
runtime context. This issue adds a `context` field per step from the LLM
planner, a params strip below the request line, and relevant Agent Config
values surfaced per step.

---

## Part 1 — Orchestrator prompt change

### `agents/orchestrator.exs`

Extend the output format to include `context` per step. Update all four
few-shot examples.

---

## Part 2 — Protocol type update

### `src/hooks/types.ts`

Add `context?` to `PlanStep`:

```typescript
export interface PlanStep {
  id:          string;
  agent:       string;
  description: string;
  context?:    string;
}
```

---

## Part 3 — UI changes

### `src/hooks/useOrchestrator.ts`

Add `params` state, extract from plan message, return from hook.

### `src/components/modules/orchestrator/OrchestratorView.tsx`

- `ParamsStrip` — shows extracted params below request line
- `StepCard` — replaces all inline step rendering in both plan_ready and executing
- `STEP_CONFIG_HINTS` — static map of agent file → relevant config keys
- Call `useAgentConfig().values` inside `OrchestratorView`

`GOOGLE_CREDENTIALS` always masked as `••• configured •••` — never shown raw.

---

## Acceptance criteria

- [ ] `context` field in output format and all four few-shot examples
- [ ] `PlanStep` has optional `context?: string`
- [ ] `useOrchestrator` stores and returns `params`
- [ ] Params strip shown when params are non-empty
- [ ] Step card shows `context` line when present (italic, muted)
- [ ] Email step shows SMTP_TO/SMTP_FROM when set
- [ ] Drive step shows `••• configured •••` when GOOGLE_CREDENTIALS set
- [ ] Provenance scan step shows NAS path when set
- [ ] StepCard used in both plan_ready and executing — no duplication
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0, zero TypeScript errors
