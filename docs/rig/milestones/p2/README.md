# Phase 2 — Live Monitoring

**Status: IMPLEMENTED**

**Goal:** Watch an active agent run's events update in real time, without
leaving the Events tab or clicking Refresh.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Polling hook](p2-001-polling-hook.md) | — | Add polling support to useRunEvents |
| 002 | [Live events UI](p2-002-live-events-ui.md) | 001 | Auto-scroll, live indicator, status update |

001 first — it has no UI component. 002 consumes it.

---

## Completion gate

- Selecting a running run in the Events tab causes new events to appear
  automatically every ~2s
- Events scroll to the bottom as they arrive (if the user hasn't scrolled up)
- A pulsing "Live" indicator is visible while polling is active
- When the run completes, polling stops and the status badge updates to 'done'
- Selecting a completed run shows no indicator and triggers no polling
- Existing behaviour for the Runs tab and all other routes is unchanged

---

## Key decisions

**Polling, not websockets.** 2-second `setInterval` inside a `useEffect`.
Sufficient for the event volumes involved. SQLite reads are fast.

**Smart auto-scroll.** Only scroll to bottom if the user is already within
50px of the bottom. If they've scrolled up to review older events, don't
hijack their position.

**Stop signal: `run_complete` event.** No separate poll of `harness_get_run`.
When `run_complete` appears in the event stream, stop the interval and update
the displayed status badge. Zero extra network calls.

**Scope: Events tab only.** The Runs list does not auto-refresh. The manual
Refresh button handles it. Auto-refreshing the Runs list is deferred to p3.
