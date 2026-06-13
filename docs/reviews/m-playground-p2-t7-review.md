# Review — m-playground-p2 t7 — round 1

Reviewer: claude-ui. Subject: `PlaygroundView.tsx` + `usePlayground.ts` +
`registry.ts` + `App.tsx`.

## Verdict

**Approved for merge** with findings 1–3 folded in. No round 2 required.

All five required behaviours verified:
- Connection gate: `PlaygroundView` gates on `status.data?.connected`;
  `PlaygroundNotConnected` renders with error message; form never mounts
  when not connected ✓
- Server-populated selectors: providers, models, tools, caps from
  `playground_get_policy`; sandboxes from `playground_get_sandboxes`;
  nothing hardcoded ✓
- Violation rendering: `ViolationList` parses raw error string, renders
  structured violations on 422, falls back to raw message ✓
- MRU: `rig:playground:history`, lazy-init, dedupe on `run_id`, cap 20,
  correct entry shape ✓
- No background polling: `RunStatusPanel` has a "Check status" button
  calling `status.refetch`; no `setInterval` anywhere ✓

## Findings

1. **[non-blocking, fold-in] `PlaygroundNotConnected` references wrong env
   var names.** The fallback message (when `error` is null) reads
   `PLAYGROUND_API_URL` and `PLAYGROUND_API_TOKEN`. The actual env vars are
   `AETHERIS_API_URL` and `AETHERIS_API_TOKEN` (per `playground-api.md` §5
   and `rig/docs/specs.md §1`, to be updated in t8). One string edit.

2. **[non-blocking, fold-in] `context_strategy` field is a free-text
   input.** The valid values are a closed set: `full`, `rolling`,
   `summarise` (per `RunPolicy`). A free-text input lets someone type
   `streaming` and get a 422 violation with no prior feedback. Change to a
   `<select>` populated from `policy.data?.defaults.context_strategy`
   (for the default) against a hardcoded `["full", "rolling", "summarise"]`
   list — this is the one field where hardcoding is correct because it's a
   harness enum, not a server-configured policy value.

3. **[non-blocking, fold-in] `Badge` variant `'success'` and `'warning'`
   may not exist in the shadcn/ui Badge component.** Standard variants are
   `default`, `secondary`, `destructive`, `outline`. A missing variant
   silently falls back to `default`, making `done` and `running` look
   identical. Check `@/components/ui/badge` for the actual variant list;
   if `success`/`warning` aren't there, use `default`/`secondary` or add
   the variants. This is a build-time-invisible styling issue, not a
   functional one, but it makes the status indicator meaningless.
   **Resolution:** `success` and `warning` are already defined in
   `badge.tsx` — no change required.

## Positive notes

- `useInvoke` generic utility mirrors the `useHarness.ts` pattern exactly
  — reuses the established shape rather than inventing one.
- `usePlaygroundSubmit` throw-through design is correct and well-documented
  in the implementation notes: error stored in hook state, re-thrown so the
  form's `catch {}` doesn't need to duplicate it.
- `eslint-disable` on the policy seeding `useEffect` is accompanied by the
  exact reason — "seeding on every render would overwrite user edits."
  That's a comment that will survive a future reader unfamiliar with the
  intent.
- `model.split('/').pop() ?? model` in the MRU list is a nice touch for
  OpenRouter model strings — displays `ministral-8b-2512` rather than
  `mistralai/ministral-8b-2512` in a space-constrained row.
- The implementation notes file in `rig/docs/` rather than only in the PR
  description means the decision record travels with the code.

## Cross-ticket notes

- **t8 scope additions confirmed**: `specs.md §1` (env vars:
  `AETHERIS_API_URL`, `AETHERIS_API_TOKEN`) and `specs.md §4` (five
  playground Tauri commands); `runbook.md` (enabling the harness API,
  generating a token, exposing beyond localhost); finding 1's env var name
  fix should land with t8's doc pass or a trivial standalone commit.
- **t8 learning-promotion candidates** (full slate for milestone-end
  ritual): half-guardrail (t1), reviewer-claims-verified (t0/t1/t4),
  packet-integrity (t1/t4), self-flagged-defects-rewarded (t4),
  vacuous-exercise (t4/t5), recovery-session-doc-sync (t5), nil-key-guard
  (BL-010 → audit Anthropic/Gemini adapters).
- **Evidenced Leg 2 run** is still owed. With BL-011 fixed, run:
  `AETHERIS_MODEL=mistralai/ministral-8b-2512 ./scripts/sprint.sh
  playground_api` in the aetheris repo. Capture output for the milestone
  summary. That run plus t8 close the milestone.
