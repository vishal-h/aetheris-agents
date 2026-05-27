# T4 Implementation Notes — at1qry Persistence via Webhook

## What T4 Delivers

cot1 now notifies at1qry via the Aetheris HTTP API (`POST /api/runs/:run_id/resume`) as the
**primary** resume path after writing the TAP result to the blackboard. The existing
`send_message` call is retained as a **fallback** (Step 8). The webhook call is non-fatal:
if it returns an error or the server is unreachable, cot1 logs the reason and proceeds to
`send_message`.

---

## inject_message Gap — Confirmed and Fixed

**Finding**: `Server.inject_message/2` had no handler for `%{status: :running, wait_condition: {:message_received, _}}`.
When at1qry calls `wait_for_event condition: "message_received"`, the agent is `:running`
(not `:paused`) — it blocks in `Execution.Loop.do_wait_receive/7` waiting for
`WaitRegistry.notify`. The existing clauses only handled the `:paused` (ask_human) path and
returned `{:error, :not_resumable}` for all other `:running` states.

The design doc noted this path ("verify during m13 T3 implementation that webhook resume fires
WaitRegistry.notify") — it was shipped without verification. T4 surfaces and fixes the gap.

**Fix** (`lib/aetheris/agent/server.ex`): Added a new `handle_call` clause matching
`%{status: :running, wait_condition: {:message_received, _}}` that:
1. Appends an `:agent_message_received` event to the run log (`:agent_message_received` was
   already registered in `trajectory/file.ex` — no new type needed).
2. Prepends a `[Message from webhook]: <message>` user turn to the context.
3. Calls `WaitRegistry.notify({:message_received, run_id}, {:resume, :message_received, message})`.

The clause is placed **before** the generic `:running` + non-nil `wait_condition` clause that
returns `:not_resumable`, so `blackboard_key` and `agent_done` waits still return `:not_resumable`.

**Tests** (`test/aetheris/agent/server_inject_test.exs`):
- Existing `:not_resumable` test updated: switched fixture from `{:message_received, 5_000}` to
  `{:blackboard_key, "some:key", 5_000}` since `message_received` now succeeds.
- Added: `"inject_message/2 wakes a run blocked on message_received wait condition"` — asserts `:ok`.
- Added: `"inject_message/2 appends :agent_message_received event for message_received wait"` —
  verifies event type, `from_run_id: "webhook"`, `content` match.
- All 661 tests pass (7 in the inject test module, 0 regressions).

---

## notify_at1qry.py

`gateway/scripts/notify_at1qry.py <at1qry_run_id> <message>` POSTs to
`{AETHERIS_API_BASE}/api/runs/{at1qry_run_id}/resume`. Uses stdlib `urllib` only. Exit 0
always — webhook failure is non-fatal. Outputs `{"status": "ok"}` or
`{"status": "failed", "reason": "..."}` to stdout.

`AETHERIS_API_BASE` defaults to `http://localhost:4001` if not set.

5 unit tests (all pass without a live server), 2 integration tests (skipped unless env vars set).

---

## at1qry Timeout: 120_000 → 300_000

`wait_for_event timeout_ms` in at1qry was raised to `300_000` (5 minutes) across all three
locations: `at1qry.exs` standalone, inline in `at1cmd.exs`, inline in `at1cmd_sprint.exs`.
The 120s window was too tight for real-world ETL pipeline latency and human-in-the-loop scenarios.

---

## cot1 Workflow: Step 7b Added

Ordering after writing the result:

```
Step 7:  write_blackboard  tap:result:<intent_id>
Step 7b: run_command        notify_at1qry.py <at1qry_run_id> "TAP result ready. intent_id: <intent_id>"
         → if failed: log reason, continue
Step 8:  send_message       to: <at1qry_run_id>   (fallback)
```

This order means at1qry is guaranteed to see the result on the blackboard before either
notification path fires (result written before Step 7b).

The change appears in three files: `cot1.exs` (standalone), `at1cmd.exs` (inline cot1
RunConfig), `at1cmd_sprint.exs` (inline cot1 RunConfig). The `at1qry_run_id` placeholder in
`cot1.exs` remains a literal `<at1qry_run_id>`; in `at1cmd.exs` and `at1cmd_sprint.exs` it is
the Elixir string interpolation `#{at1qry_id}` resolved at eval time.

---

## BEAM Restart Behavior (Manual Verification)

If the BEAM node restarts after cot1 writes the result but before the webhook fires:
- The webhook POST returns 404 (run not found in new node's Registry).
- `send_message` also fails (run gone).
- cot1 reports and finishes.
- Recovery: re-run the orb with the same correlation_id; idempotent records produce the same GUIDs.

This is expected behavior. Durable persistence across BEAM restarts is deferred to T5.

---

## Sprint Case

`./scripts/sprint.sh uc_api_agent_t4` (from `aetheris/`):
- Checks `AETHERIS_API_BASE` env var is set.
- Starts `mix aetheris server --port 4001` in background.
- Waits up to 15s for the server to respond (probe via `notify_at1qry.py` — a 404 confirms readiness).
- Runs the orb (`at1cmd_sprint.exs` + `cot1.exs` + `at1qry.exs`).
- Stops the API server.
- Exports at1qry trajectory and checks for `agent_message_received` events with `from_run_id: "webhook"`.

---

## What T5 Must Know

- The inject_message fix is in `aetheris/lib/aetheris/agent/server.ex`. The `{:message_received, _}`
  clause is the third pattern (after `:paused` and before the generic `:not_resumable` catch-all).
- `notify_at1qry.py` is reusable for any run that is waiting on `message_received`.
- The `AETHERIS_API_BASE` env var must be set before any sprint that uses the webhook path.
- T5 work: durable state (checkpoint/restore across BEAM restarts) requires `resume_from_checkpoint`
  — see `m13` primitives in the design doc.
