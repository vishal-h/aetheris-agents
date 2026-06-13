# m-playground-p2 t7 — Implementation Notes

## Flows verified

**Connection gate:** The `PlaygroundView` component calls `usePlaygroundStatus()` on mount. If `status.data?.connected` is false (or null/undefined while loading), `PlaygroundNotConnected` is rendered instead of `ComposerForm`. The error message from `PlaygroundStatus.error` is displayed verbatim in a monospace block. The form is never mounted when not connected — no data fetching for policy or sandboxes happens at all until the connection gate passes. Verified by reading the conditional rendering logic in `PlaygroundView`.

**Violation rendering:** On `playground_submit_run` error, the error string flows from `usePlaygroundSubmit` into `ViolationList`. The component attempts `JSON.parse` on the raw error string. If it parses as a `PlaygroundApiError` object (i.e. has an `error.violations` array with at least one entry), each violation's `field` and `message` are rendered as a list item. For non-422 or non-structured errors, the raw message is shown directly. The `violations.length > 0` guard prevents rendering an empty violations block for 422 errors that only carry a top-level message. Verified by reading the `ViolationList` component logic.

## Non-obvious decisions

**`usePlaygroundSubmit` throws through to the caller.** The hook re-throws the error after setting state so the `handleSubmit` callback can silence it with a bare `catch {}` — the error is already stored in hook state and surfaced via `submitError`. This avoids duplicating error state between the hook and the component.

**Form defaults seeded once from policy.** The `useEffect` that seeds `maxSteps`, `maxSpawnDepth`, `contextStrategy`, and `tools` from `policy.data.defaults` uses `// eslint-disable-next-line react-hooks/exhaustive-deps` so it only runs when `policy.data` changes, not on every form-state change. Seeding on every render would overwrite user edits.

**Model reset on provider change.** `setModel('')` fires in a `useEffect` on `provider`, and a second `useEffect` seeds the first model of the new provider. This avoids an invalid (provider, model) pair surviving a provider switch.

**No background polling.** The `RunStatusPanel` renders a "Check status" button that calls `status.refetch` on demand. There is no `setInterval`. The Harness → Runs tab is the canonical place to watch a running job.

**MRU key.** The localStorage key is `rig:playground:history`, consistent with the `rig:orchestrator:history` convention. Entry shape is `{run_id, label, provider, model, submitted_at}` exactly as spec'd — sufficient to locate the run in the Harness view.

**`invoke` camelCase keys.** `playground_run_status` takes a `run_id` Rust parameter, so the invoke call passes `{ runId }` per the CLAUDE.md camelCase-only rule. `playground_submit_run` takes a `request` struct, so `{ request }` (single-word key, no conversion needed).

## Deviations from spec

None. The five required behaviours are all present: connection gate, server-populated selectors, violation rendering, MRU, no background polling.
