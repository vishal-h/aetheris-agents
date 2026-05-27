# T5 Implementation Notes — BEAM Durability

## What T5 delivers

at1qry can now survive a BEAM restart while waiting for the webhook from cot1. Previously,
`resume_from_checkpoint` returned `{:error, :unresumable}` for any run blocked on a
`{:message_received, _}` wait condition — the checkpoint existed in SQLite but was silently
abandoned on startup.

---

## Q1: Did T5 require a harness fix?

**Yes.** Three changes in `lib/aetheris/agent/server.ex`:

### 1. `decode_checkpoint` — remove the `:unresumable` guard for `message_received`

Before:
```elixir
case wc do
  {:message_received, _} -> {:error, :unresumable}
  {:blackboard_key, _, _} -> {:error, :unresumable}
  _ -> ...
end
```

After:
```elixir
case wc do
  {:blackboard_key, _, _} -> {:error, :unresumable}
  _ -> ...
end
```

`:blackboard_key` remains `:unresumable` — there is no replay mechanism for blackboard waits.

### 2. `handle_call(:resume_from_checkpoint)` — pass `wait_condition` to `do_resume`

Before: `_wait_condition` (discarded)
After: `wait_condition` passed as fifth argument

### 3. `do_resume` — re-establish message_received waits on resume

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

Only `{:message_received, _}` is restored; `{:agent_done, _, _}` and `nil` are cleared. This
preserves the existing behavior for `{:agent_done, _}` checkpoints (the pre-T5 test
`"resume_from_checkpoint restores state and continues execution"` creates an `agent_done` wait
and expects the loop to resume cleanly without re-entering the wait).

The server pre-registers in WaitRegistry before the Task starts. This covers the window between
`resume_from_checkpoint` returning `:ok` and the Task's `handle_blocking_wait` registering.
If a webhook fires in that window, the server receives the notify and drops it via `handle_info`.
Once the Task registers (`:duplicate` keys), subsequent notifies reach the Task. The `send_message`
fallback in cot1 covers the production race.

---

## Tests added (`test/aetheris/agent/server_inject_test.exs`)

Three new tests:

1. **`resume_from_checkpoint/1` returns `:ok` for a `message_received` checkpoint** — regression
   guard for the primary fix; previously returned `{:error, :unresumable}`.

2. **After resuming a `message_received` checkpoint, `WaitRegistry.notify` unblocks the run** —
   verifies the Task re-registers and receives the notify; run reaches terminal state.

3. **`resume_from_checkpoint/1` returns `:unresumable` for a `blackboard_key` checkpoint** —
   regression guard for the deliberate restriction on blackboard waits.

---

## Sprint case

`uc_api_agent_t5` in `aetheris/scripts/sprint.sh`:

- **Part A**: T4 regression — runs the full at1cmd + cot1 + at1qry orb with the Aetheris API
  server, verifies the webhook path (`agent_message_received` from webhook) is intact.
- **Part B**: Runs `server_checkpoint_test.exs` and `server_inject_test.exs` to verify the fix
  in-process. Actual BEAM process kill + restart requires the manual procedure in `api/runbook.md`.

---

## Manual BEAM restart test result

Tested manually following the procedure in `api/runbook.md` (T5 section):

1. Launched the orb; confirmed at1qry entered `wait_for_event`.
2. Killed the Aetheris server while at1qry was waiting.
3. Confirmed checkpoint row in SQLite with `status='waiting'` and
   `wait_condition_json={"type":"message_received","timeout_ms":300000}`.
4. Restarted the server; at1qry was auto-resumed on Application startup.
5. Sent `notify_at1qry.py <at1qry_run_id>` manually (cot1 had already finished).
6. at1qry woke, ran `gap_analysis.py`, and reached `agent_finished`.

---

## Deviations from spec

None. The three-change fix exactly matched the pre-analysis.
