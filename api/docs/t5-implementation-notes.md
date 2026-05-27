# T5 Implementation Notes — BEAM Durability

## What T5 Delivers

at1qry can now survive a BEAM restart while waiting for the webhook from cot1. If the node
restarts after cot1 writes the TAP result but before the webhook fires, at1qry's checkpoint is
found by `list_resumable_checkpoints` on the next startup and resumed via
`resume_from_checkpoint`. The run picks up in its `message_received` wait state and completes
normally when `notify_at1qry.py` is called (either by a retry or manually).

---

## Source Audit: Three Independent Failure Points

Before T5, `resume_from_checkpoint` for a `{:message_received, _}` wait condition failed at
three independent layers. Fixing any one in isolation would still leave the resume broken.

### Failure 1 — `decode_checkpoint` returned `:unresumable` immediately

```elixir
case wc do
  {:message_received, _} -> {:error, :unresumable}   # ← T5 removes this
  {:blackboard_key, _, _} -> {:error, :unresumable}
  _ -> ...
end
```

`decode_checkpoint` is called inside a `with` chain in `handle_call(:resume_from_checkpoint)`.
The `{:error, :unresumable}` short-circuits to `{:reply, {:error, :unresumable}, state}` before
`do_resume` is ever invoked. The checkpoint exists in SQLite and is found — it is silently
abandoned here.

### Failure 2 — `handle_call(:resume_from_checkpoint)` discarded the wait condition

Even if Failure 1 were fixed, the `with` binding used `_wait_condition`:

```elixir
{:ok, step, messages, tool_history, _wait_condition} <- decode_checkpoint(checkpoint) do
  do_resume(state, step, messages, tool_history)
```

The decoded wait condition was thrown away before reaching `do_resume`. `do_resume` received no
information about what the run was waiting for.

### Failure 3 — `do_resume` set `wait_condition: nil` in the resumed server state

Even if Failure 2 were fixed (by passing the value), `do_resume` unconditionally cleared it:

```elixir
%{state | status: :running, wait_condition: nil, ...}
```

The execution loop reads `wait_condition` from server state at the start of each `do_run` call
via `apply_wait_condition`. With `nil`, it would skip the `WaitRegistry` re-registration and
proceed as if there were no pending wait — the resumed Task would run steps rather than re-enter
the blocking receive.

---

## Fix

Three coordinated changes in `lib/aetheris/agent/server.ex`:

**1. `decode_checkpoint`** — remove the `{:message_received, _}` guard; `:blackboard_key`
remains `:unresumable` (no replay mechanism exists for blackboard waits):

```elixir
case wc do
  {:blackboard_key, _, _} -> {:error, :unresumable}
  _ -> ...
end
```

**2. `handle_call(:resume_from_checkpoint)`** — rename `_wait_condition` to `wait_condition`,
pass as fifth argument to `do_resume`.

**3. `do_resume`** — restore `{:message_received, _}` only; all other wait conditions
(`:agent_done`, `nil`) are cleared:

```elixir
restored_wait =
  case wait_condition do
    {:message_received, _} ->
      WaitRegistry.register({:message_received, state.config.run_id})
      wait_condition
    _ ->
      nil
  end
```

`WaitRegistry.register` is called on the **server process** before the Task starts. This covers
the window between `resume_from_checkpoint` returning `:ok` and the Task's `handle_blocking_wait`
registering. If a webhook fires in that window, the server receives the notify and drops it via
the `handle_info` catch-all. Once the Task registers (`:duplicate` keys), future notifies reach
it. The `send_message` fallback in cot1 covers the production race if the server-only window is
hit.

`{:agent_done, _, _}` is deliberately not restored. Restoring it would cause the resumed loop to
re-enter a blocking wait for a child run that may have already finished, hanging indefinitely.
The pre-T5 test `"resume_from_checkpoint restores state and continues execution"` creates an
`agent_done` checkpoint and expects the loop to resume cleanly — restoring that wait would break it.

---

## Tests Added (`test/aetheris/agent/server_inject_test.exs`)

Three new tests guard the three failure points:

1. **`resume_from_checkpoint/1` returns `:ok` for a `message_received` checkpoint** — verifies
   Failure 1 is fixed; previously returned `{:error, :unresumable}`.

2. **After resuming a `message_received` checkpoint, `WaitRegistry.notify` unblocks the run** —
   verifies Failures 2 and 3 are fixed; after resume the Task re-enters the blocking wait, and
   `WaitRegistry.notify` wakes it so the run reaches a terminal state.

3. **`resume_from_checkpoint/1` returns `:unresumable` for a `blackboard_key` checkpoint** —
   regression guard confirming the deliberate restriction is preserved.

676 tests, 0 failures after the fix.

---

## Sprint Case

`./scripts/sprint.sh uc_api_agent_t5` (from `aetheris/`):

- **Part A**: T4 regression — full orb with API server, checks for `agent_message_received` from
  webhook in at1qry trajectory.
- **Part B**: Runs `server_checkpoint_test.exs` and `server_inject_test.exs` to verify the harness
  fix in-process.

Actual BEAM process kill + restart is a manual procedure (see `api/runbook.md`, T5 section).
The unit tests cover the fix code paths without requiring a live restart.

---

## What T6 Must Know

- `{:blackboard_key, _, _}` is still `:unresumable`. Any ticket that needs blackboard-wait
  durability requires a separate replay mechanism.
- The `{:agent_done, _, _}` case is intentionally cleared on resume. If at1qry ever uses
  `agent_done` waits, those will not survive a restart.
- `notify_at1qry.py` is reusable as a manual wake tool: `python3 gateway/scripts/notify_at1qry.py
  <run_id> "TAP result ready. intent_id: <id>"`.
