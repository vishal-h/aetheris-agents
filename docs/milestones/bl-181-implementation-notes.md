# BL-181 — implementation notes

`Measured at harness `77ab709` and agents at the commit carrying this file, 2026-08-23. Every
figure below carries the command that produced it. Harness commands run from
`~/sandbox/elixirws/aetheris`; agents commands from `~/sandbox/elixirws/aetheris-agents`.`

---

## 1. The hinge: is zero a legal state?

The ticket posed two readings and made everything downstream depend on which held. They are not
symmetric — one says repair the test, the other says repair the code, and a wrong answer produces
a green suite over an unrepaired system.

**Determination: zero is a LEGAL receiver step. The code is right; the test's expectation was
wrong.** Established from the coordinator's and the agent server's code, not from the test.

The evidence, in the order it forces the conclusion:

1. **A loop's first iteration is step 0, not step 1.** `Loop.run/5` ends at
   `do_run(opts, 0, {initial_messages, []})` — `lib/aetheris/execution/loop.ex:88`. Every event that
   iteration appends carries step 0: `:prompt_built` at `:183`, `:llm_called` at `:185`,
   `:step_complete` at `:298`.
2. **`current_step/1` returns the last event's step, and 0 for an empty log** —
   `lib/aetheris/agent/server.ex:616-626`.
3. **`state.step` starts at 0 and the run loop never writes it.** `init/1` sets `step: 0`
   (`:214`); the only writes are the two message-delivery clauses (`:369`, `:414`).
4. **`status: :running` is true before the first log append.** `handle_call(:run, ...)` sets
   `status: :running` and spawns execution in a `Task`, returning immediately — `:224-264`. So a
   receiver can be `:running` with an empty log, and also `:running` inside step 0 with step-0
   events already appended.
5. **Delivery records `max(state_step, current_step(log_pid))`** — `:404`. With the receiver in its
   first iteration this is `max(0, 0) = 0`.
6. **The read is not stale.** `Log.append/2` is a synchronous `GenServer.call` —
   `lib/aetheris/trajectory/log.ex:52` — so `current_step` cannot lag behind a receiver that has
   actually advanced.

So 0 is **not** a default standing in for a value the coordinator failed to read. It is the value
the read returns, and it is the receiver's true step. The second reading the ticket posed — an
uninitialised field or a read-before-write — is **false**, and had the test been repaired by
synchronising it, correct behaviour would have been hidden behind a barrier.

**What `> 0` was actually asserting.** Agent A's stub queue is `echo`, `send_message`, `text`, so A
issues `send_message` at its step 1. Agent B's is three `echo`s. `> 0` therefore asserted that B
finished one whole loop iteration before A finished two — a scheduling outcome, not a contract.

**What the original "step fix" fixed, for the record.** `bc6e981` changed
`step = current_step(log_pid)` to `step = max(state_step, current_step(log_pid))` and added
`state.step`. That is a **monotonicity** guard — a second message delivered inside one log step
cannot report a step below one already reported. It has nothing to do with `> 0`, which was the
test author's proxy for "a real step, not a constant" and happened to hold on fast machines.

**The sibling at `:124` is a different shape and is left alone.** `assert sent_event.step > 0` reads
the *sender*'s step, which is 1 by construction. Same for `orb_blackboard_test.exs:87`.

---

## 2. The forced reproduction

Repetition was not used as evidence and the row forbids it. The receiver is **held**: `:sys.suspend/1`
on B's stub LLM adapter blocks B's loop on its first `pop_response`, so B can never leave step 0.

The hold is a hold, not a starvation. At delivery B is `:running` and has already appended its own
`prompt_built` and `llm_called`, **both at step 0** — printed by the harness on every run. That is
the fact that decides the repair: the message did not arrive before B started, it arrived while B
was **working inside step 0**. A barrier that waited for B to "have started" would not have helped.

**Result, before the repair — `mix test test/aetheris/orb/bl181_force_test.exs`, five runs of five:**

```
[FORCE] B status=:running, log has 2 event(s):
[FORCE]   step=0 type=prompt_built
[FORCE]   step=0 type=llm_called
[FORCE] :agent_message_received carried step=0

  1) test FORCED: receiver held inside step 0 records :agent_message_received with step 0
     Assertion with > failed, both sides are exactly equal
     code: assert received.step > 0
     left: 0
```

That is the CI failure text, reproduced on demand in 0.06 s.

**A note on what the control showed, because it is stronger than expected.** Removing the hold did
**not** make the failure go away: the harness delivers as soon as B's step-0 events land, and five
runs of five still recorded step 0. `step: 0` is not an exotic race — it is the normal state
whenever a message is delivered during the receiver's first iteration. The positive control had to
be built the other way round: hold B **after** it reaches step 1, and the assertion passes. Five
runs of five, recording steps 13, 20, 2, 11 and 18. The instrument reports both outcomes, so the
failures are not an artifact of it.

---

## 3. The repair, and the proof it is stricter

The repair pins the step to the receiver's own preceding event rather than admitting any positive
number. The diff is in `../aetheris` at `77ab709`.

**Mutation control.** An off-by-one injected into `deliver_message`
(`max(state_step, current_step(log_pid)) + 1`), then `mix test test/aetheris/orb/coordinator_test.exs`:

| assertion under the same mutation | result |
|---|---|
| OLD `assert received_event.step > 0` | `10 tests, 0 failures` — **misses it** |
| NEW `assert received_event.step == reached_step` | `10 tests, 1 failure` — `left: 2  right: 1` |

So the replacement is **not** a relaxed bound in any sense the row forbids; it catches a defect the
original could not. Both the mutation and the test swap were restored from working-copy backups and
verified by `sha256sum -c`, never by `git checkout --`, per the standing rule.

**Fails before, passes after — same harness, same hold, same conditions.** With the repaired
assertion the forced harness reports `1 test, 0 failures`, five runs of five, printing
`carried step=0` and `B had actually reached step=0` on each.

---

## 4. The forcing harness, verbatim

**Scratch, and not committed.** The repaired assertion is scheduling-independent, so a permanent
held-receiver test would add a `:sys.suspend` dependency on an internal registry key for no
coverage the mutation control does not already give. It is reproduced here so a later session — or
BL-183 — can re-run it without rebuilding it. Drop it at
`../aetheris/test/aetheris/orb/bl181_force_test.exs`.

```elixir
defmodule Aetheris.Orb.BL181ForceTest do
  @moduledoc """
  BL-181 SCRATCH — forced reproduction. Not for commit.

  Holds receiver B inside its FIRST loop step by suspending B's stub LLM
  adapter, then delivers a coordinator message. B is provably running and has
  provably appended events when the message lands.
  """
  use ExUnit.Case, async: false

  alias Aetheris.Orb.Coordinator
  alias Aetheris.RunConfig
  alias Aetheris.Trajectory.Log

  test "FORCED: receiver held inside step 0 records :agent_message_received with step 0" do
    orb_id = "bl181-force-#{System.unique_integer([:positive])}"
    run_id_b = "#{orb_id}-run-b"

    config_b = %RunConfig{
      run_id: run_id_b,
      orb_id: orb_id,
      mode: :record,
      provider: "stub",
      model: "stub-v1",
      system_prompt: "Agent B",
      max_steps: 3,
      stub_responses: [
        tool_call_response("echo", %{"message" => "ack"}),
        tool_call_response("echo", %{"message" => "still running"}),
        tool_call_response("echo", %{"message" => "keep alive"})
      ]
    }

    coordinator = start_supervised!({Coordinator, orb_id: orb_id})
    agent_sup = start_supervised!({Aetheris.Agent.Supervisor, config_b})

    server_b = lookup!({:server, run_id_b})
    stub_b = lookup!({:stub, run_id_b})
    log_b = lookup!({:log, run_id_b})

    # THE HOLD. B's loop blocks on its first pop_response and can never leave step 0.
    :sys.suspend(stub_b)

    :ok = Coordinator.register_agent(coordinator, run_id_b, server_b)
    :ok = Aetheris.Agent.Server.run(run_id_b)

    # Prove B is RUNNING and WORKING, not merely un-started: wait for its own
    # step-0 events to land in the log before the message is delivered.
    wait_for_events(log_b, 2)
    events_before = Log.all(log_b)
    assert {:ok, :running} = Aetheris.Agent.Server.status(run_id_b)

    IO.puts("\n[FORCE] B status=:running, log has #{length(events_before)} event(s):")

    Enum.each(events_before, fn e ->
      IO.puts("[FORCE]   step=#{e.step} type=#{e.type}")
    end)

    # THE DELIVERY, while B is provably inside step 0.
    {:ok, _msg_id} = Coordinator.send_message(coordinator, "run-a", run_id_b, "hello")

    events = Log.all(log_b)
    received_index = Enum.find_index(events, &(&1.type == :agent_message_received))
    refute is_nil(received_index)
    received = Enum.at(events, received_index)
    IO.puts("[FORCE] :agent_message_received carried step=#{received.step}")

    reached_step =
      events
      |> Enum.take(received_index)
      |> Enum.map(& &1.step)
      |> then(&Enum.max([0 | &1]))

    IO.puts("[FORCE] B had actually reached step=#{reached_step}")

    # BEFORE the repair this was `assert received.step > 0` and it failed here.
    assert received.step == reached_step

    :sys.resume(stub_b)
    _ = agent_sup
  end

  defp lookup!(key) do
    [{pid, _}] = Registry.lookup(Aetheris.Registry, key)
    pid
  end

  defp wait_for_events(log_pid, n) do
    deadline = System.monotonic_time(:millisecond) + 2_000
    do_wait_for_events(log_pid, n, deadline)
  end

  defp do_wait_for_events(log_pid, n, deadline) do
    if length(Log.all(log_pid)) >= n do
      :ok
    else
      if System.monotonic_time(:millisecond) < deadline do
        Process.sleep(5)
        do_wait_for_events(log_pid, n, deadline)
      else
        flunk("B never appended #{n} events")
      end
    end
  end

  defp tool_call_response(tool_name, tool_input) do
    {:ok,
     %{
       type: :tool_call,
       tool_name: tool_name,
       tool_input: tool_input,
       tool_use_id: "tc-#{System.unique_integer([:positive])}",
       latency_ms: 0,
       input_tokens: 10,
       output_tokens: 5
     }}
  end
end
```

---

## 5. The census

**Scope.** Every assertion in the harness suite whose result depends on elapsed time, or on another
process having advanced, with nothing synchronising it. The population, with the commands that
reproduce it — both verified identical under the shell's shimmed `grep` and under the binary, per
BL-182's discipline:

```bash
git ls-files test/ | /usr/bin/grep -cE '\.exs?$'                                    # 121 files
git grep -c -E '^\s*(assert|refute)' -- 'test/*.exs' | /usr/bin/awk -F: '{s+=$2} END {print s}'   # 2544 assertions
```

**The instrument is structural, not lexical**, because the row required it to reach a dependency
expressed without any of the obvious search terms. It taints variables bound from a time source or
a cross-process read, propagates the taint through further bindings, and reports assertions
mentioning a tainted name. It lives in the session scratchpad as `census3.py`; it is scratch and is
not committed, and the classes below are the deliverable.

### 5a. The R34 control, and the two under-reports it caught first

**The plant**, in the shape the row named — a bound computed into a variable and asserted several
lines later, carrying no `Process.sleep`, no `assert_receive`, no `> 0` and no literal at the
assert. Planted into `test/aetheris/id_test.exs`:

```elixir
  test "generate/0 stays within its per-call budget" do
    budget_us = 500 * 100
    started = System.monotonic_time(:microsecond)
    ids = Enum.map(1..100, fn _ -> ID.generate() end)
    assert length(ids) == 100
    spent = System.monotonic_time(:microsecond) - started
    assert spent < budget_us
  end
```

**Found**, at `test/aetheris/id_test.exs:37`, `kind=time`, tainted var `spent`, bound var
`budget_us`, unsynchronised. Discrimination check: that file then held 8 assertions and **1** was
flagged. The plant was removed by restoring the working-copy backup and verifying with
`sha256sum -c`; `git status --porcelain test/aetheris/id_test.exs` is empty.

**But the instrument under-reported twice before it passed, and both are recorded because a census
that under-reports produces exactly the "one test, not a class" verdict this row was written to
prevent.** A second control found them: **BL-135** is a known member of this class, so an instrument
that misses its site is under-reporting by demonstration rather than by argument.

- **Under-report 1 — no feeder rule.** v1 flagged 1 line in
  `test/aetheris/cli/commands/run_helpers_timeout_test.exs` and missed the `await_bounded` sites
  entirely. Fixed by adding two rules derived from the class definition: a process the test starts
  which advances on its own (`Task.async`/`spawn`) makes later assertions depend on it, and an
  assertion against a bounded-wait deadline is a hit when the block delays or feeds.
- **Under-report 2 — single-line scanning.** v2 still missed the site, because
  `assert {:ok, ...} =` / `await_bounded(...)` **spans two physical lines** and the scanner read one
  line at a time. Fixed with a logical-line pre-pass. v1 found `[135]` in that file; v3 finds
  `[31, 46, 71, 98, 117, 135, 144, 155, 178, 197]`.

**And a correction to my own reading along the way:** I first reported the census as "missing
BL-135's site at `:84`". `:84` is the **test declaration** line — ExUnit reports tests by their
`test "..." do` line, exactly as BL-181's own header says `coordinator_test.exs:127` for an
assertion at `:168`. The assertion inside BL-135's test is at `:98`, and v3 finds it. The
under-reports were real; my line number for them was not.

### 5b. The classes found

**Reported as classes, per the row.**

- **Class A — assertion on a value another process is concurrently producing, with no barrier at
  all.** 11 members. Mostly benign on inspection: `Task.yield` with a generous timeout, and
  `:agent_waiting`/`:agent_resumed` event-presence checks that are structural rather than timed.
  The two live ones are BL-135's own, `run_helpers_timeout_test.exs:71` and `:98` — a feeder
  sleeping against a bound. **BL-135 is DONE and carried no repair here**; this row does not
  re-triage it.
- **Class B — assertion on mid-run state behind a COMPLETION-ONLY barrier.** 15 members. **This is
  BL-181's class, and the census's `synced` flag actively hid it**: the block *does* contain a
  barrier — `assert_orb_done` / `assert_run_done` — so a naive filter marks it synchronised. But
  those barriers wait for the run to *finish*; they cannot constrain an interleaving that already
  happened. Any assertion on the *value* of a field recorded mid-run inherits that run's
  scheduling. Found by a second, targeted pass rather than by the general instrument, which is
  itself worth recording: **the general instrument's notion of "synchronised" was too coarse for
  the very class the row existed to find.**
- **Class C — wall-clock values supplied as parameters.** Numerically the largest group in the raw
  output (`Sweep.sweep(now: DateTime.utc_now())` and friends) and **not a member of the class at
  all**: the value is injected, so the call is deterministic. Recorded so a later reader does not
  re-derive it as a finding.

**Class B, member by member**, with the ruling on each:

| site | assertion | ruling |
|---|---|---|
| `coordinator_test.exs:168` | `received_event.step > 0` | **THE FAILURE. Repaired at `77ab709`.** |
| `coordinator_test.exs:124` | `sent_event.step > 0` | Sound — sender, step 1 by construction. |
| `orb_blackboard_test.exs:87` | `sent.step > 0` | Sound — sender, `broadcast_message` at A's step 1. |
| `orb_blackboard_test.exs:73` | `read_result.payload["result"] == "42"` | **Real member. One-step margin, no barrier. → BL-183.** |
| `orb_blackboard_test.exs:82`, `:89` | payload identity | Sound — content, not scheduling. |
| `orb_test.exs:89`, `:92`, `:97` | event presence + `message_id` identity | Sound. |
| `broadcast_message_test.exs:255`, `:259`, `:260` | payload identity | Sound. |
| `fork_test.exs:445`, `:446`, `:447` | `e.step == 0` / `== 1` over a fork | Sound — deterministic replay, not scheduling. |

**Verdict on the row's own question — "one test or a class?"** It is **one failing assertion, but a
real class**. The class is Class B, it has 15 members, and 13 of them are sound on inspection for
reasons that are properties of what they assert rather than luck. The one member beyond this
ticket's repair scope is `orb_blackboard_test.exs:73`, filed as **BL-183** and explicitly **not
forced** — it is a mechanism read off two stub queues, which is the same status BL-181's own reading
had before it was forced, and BL-181 is the reason that status is stated rather than glossed.

### 5c. Repair scope actually taken

The failing assertion, and nothing else. No other Class B member shares its identical mechanism as a
one-line change: the sender-side `> 0` assertions are correct as written, and `:73` needs real
synchronisation rather than a corrected expectation. Per the ticket's scope rule, that one went to a
row and everything else to the packet.

---

## 6. Gates

All seven, from `~/sandbox/elixirws/aetheris`, each under an inner `timeout` below the tool cap:

| gate | result |
|---|---|
| `mix deps.get` | exit 0 |
| `mix hex.audit` | exit 0 |
| `mix compile --warnings-as-errors` | exit 0 |
| `mix format --check-formatted` | exit 0 |
| `mix credo --strict` | exit 0 |
| `mix dialyzer` | `Total errors: 0` — exit 0 |
| `MIX_ENV=test mix test --exclude requires_worker --exclude integration` | `972 tests, 0 failures, 133 excluded` — exit 0 |

The test totals are the same `972` / `133` as the red run `32618789914`, which reported
`972 tests, 1 failure, 133 excluded`. One assertion moved, and nothing else did.

**No gate is carried red.** BL-135 is DONE, and `main`'s only open red was this row.

---

## 7. Deviations and defects in this session's own work

Each with the command that caught it, per the ticket's §I7.

1. **`Agent.Server.get_status/1` does not exist.** The first forcing harness called it; the public
   accessor is `status/1` by run id. Caught by `mix test test/aetheris/orb/bl181_force_test.exs`
   — `(UndefinedFunctionError) function Aetheris.Agent.Server.get_status/1 is undefined or private`.
2. **Census under-report 1 (no feeder rule)** and **3. under-report 2 (single-line scanning)**, both
   above in §5a. Caught by the BL-135 acid test, not by the R34 plant — the plant passed against v1,
   which was already under-reporting. **The plant alone would have certified a broken instrument**,
   and that is the most useful thing this census produced about censuses.
4. **My own wrong line number for BL-135**, `:84` for `:98`, corrected in §5a. Caught by running the
   logical-line joiner and printing what it produced at that offset.
5. **The first "control" tested the wrong direction.** Removing the hold did not make the failure go
   away, so it isolated nothing; the useful control was the opposite one. Caught by running it five
   times and reading the output rather than assuming it.

---

## 8. What this ticket did not do

- **Not pushed.** Both commits are local. The corroborating workflow run is the arbiter's.
- **The permitted single re-run of `32618789914` was not used**, and remains available.
- **`ci.yml`, `mix.lock` and cache-key inputs untouched** — `git -C ../aetheris show --stat 77ab709`
  lists one file.
- **BL-175 to BL-180, BL-048 and BL-150 untouched.**
- **One row filed**, BL-183, from the census, per the ticket's limit.
