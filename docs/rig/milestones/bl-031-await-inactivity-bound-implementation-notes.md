# BL-031 — `await_run` inactivity bound — implementation notes

Harness-side ticket; all code edits in `../aetheris/`. Citations re-verified at
harness HEAD `9b2b102` (the ticket's `7e77951` had advanced by BL-028's `fork.ex`
change, which does not touch this ticket's files — confirmed, no impact).

## What shipped

`RunHelpers.await_run/2` (`../aetheris/lib/aetheris/cli/commands/run_helpers.ex`) is
no longer a poll-forever loop. Each poll observes the run's
`{status, max_event_seq}` pair; the inactivity clock resets whenever that pair
advances, and only a pair that has been unchanged for the threshold produces:

```
run <id> stalled: no status or event activity for <threshold>ms (last status: <status>, last event seq: <seq>)
```

Threshold: `config :aetheris, :await_inactivity_timeout_ms` (default `300_000`),
overridable per call via the existing opts keyword
(`await_inactivity_timeout_ms:`). Runbook section
`## Waiting for a run to finish` lands in the same commit.

## Design decisions

- **Inactivity, never absolute.** The ticket's hard constraint. `watch.since` is
  reset on every observed change, so total elapsed time is never consulted — a run
  stepping for six hours completes normally. Both halves of this are *positively*
  tested (see below), not just asserted in prose.

- **Activity signal is `Store.max_event_seq/1`, not the existing `last_seq`.**
  `last_seq` is threaded through `do_await` but only advanced under `verbose: true`
  (via `stream_new_events/2`), so it is blind in the default non-verbose path — the
  exact path Rig's `invoke` uses. `Store.max_event_seq/1`
  (`lib/aetheris/store.ex:94`) is one indexed `COALESCE(MAX(seq), -1)` aggregate and
  is faithful to live progress: `Trajectory.Log.append/2`
  (`lib/aetheris/trajectory/log.ex:105`) writes through to the store on **every**
  append, so store seq cannot lag behind a live run. `Sweep` already uses this
  idiom (`lib/aetheris/sweep.ex:290`). Its `-1` empty-run sentinel happens to match
  `@uninitialized_seq`.

- **Status is half the key, not just seq.** A run can change status without
  emitting an event (and vice versa); either counts as progress. Covered by its own
  test ("a status change alone counts as activity").

- **A store error on the seq probe is neutral, not progress.** `activity_key/3`
  falls back to the last known seq on `{:error, _}`. Treating a failed probe as a
  *new* value would reset the clock on every failing poll and re-hide exactly the
  class of hang this ticket exists to surface — a store that has started erroring is
  the likeliest future cause of a stuck status (cf. the BL-007 t4 `:busy` crash).

- **Default kept at 300_000 — the ticket invited pushback; declining it.** Polling
  cost: the added probe is one GenServer call per 200 ms poll (5/s) against a store
  already serving `get_run` at that same rate, i.e. a 2× on an already-negligible
  base. No throttling (probe every Nth poll) is worth the extra state, and
  throttling would blur the threshold's meaning. The value matches
  `:sweep_liveness_threshold_ms` and Rig's `stalled?` detector, so the CLI gives up
  on the same evidence the sweep calls dead — **and exempts what the sweep exempts**
  (round 2, finding 18; before that fix the symmetry claim was false in the
  direction that mattered).

- **`eval/runner.ex:131-158` mirrored in idea, not unified** (per ticket). It is
  deadline-shaped (absolute), which is correct for eval — a graded task *should*
  have a wall-clock cap — and wrong here. Two other divergences make unification
  actively undesirable: eval treats `:not_found` as retryable-until-deadline where
  `RunHelpers` fails immediately, and eval returns error atoms where `RunHelpers`
  returns operator-facing strings. Both behaviours are left untouched on both sides.

- **Terminal / `:not_found` / store-error branches unchanged.** The bound lives
  solely in the previously-unbounded `_other` branch, now `continue_or_timeout/5`.

## Callers — verified, no edits needed

The ticket asked to verify the four callers render the message rather than swallow
it. All four do; **zero caller edits**. Verified by reading *and* empirically:

| Caller | Shape | Renders as |
|---|---|---|
| `fork.ex:37` | final expr of a bare `with`, no `else` | `Error: run … stalled: …` |
| `replay.ex:25` | same | `Error: run … stalled: …` |
| `run.ex:107-110` | explicit `{:error, reason} -> {:error, reason}` pass-through | `Error: run … stalled: …` |
| `verify.ex:33-39` | wraps: `"verification failed: #{reason}"` | `Error: verification failed: run … stalled: …` |

All reach `CLI.Output.Formatter.print/2`
(`lib/aetheris/cli/output/formatter.ex:37`) → stderr, exit code 1. The `verify`
prefix is pre-existing behaviour, is not swallowing (the full message survives), and
is documented in the runbook section rather than changed.

## Red-first evidence

Method, as required by the done-check: the new tests were written **first** and run
against the unmodified unbounded `await_run`. Because that call never returns, each
assertion runs inside `await_bounded/2` — a `Task.async` + `Task.yield(10_000)` +
`Task.shutdown(:brutal_kill)` harness that converts "never returned" into an explicit
`flunk("… did not return within 10000ms — the wait is unbounded")` instead of hanging
the suite. Pre-fix, the opt is simply ignored and all four timeout tests flunk that
way in 42.3s of harness timeouts; post-fix the same file is 6/6 green in 3.8s. Both
runs are inlined verbatim in the review packet.

The two progressing-run tests pass in *both* runs, by design — they cannot go red
pre-fix, because pre-fix there is no bound to falsely trip. Their job is the converse
regression: they fail if the bound is ever made absolute rather than inactivity-based
(each runs ~1.5s of steady progress against a 300–400ms threshold).

## Deviations

None from the ticket's scope. Nothing generated from the "do not generate" list: no
BL-030 early-return work (the fork call shape is untouched), no `eval/runner.ex`
changes, no absolute cap.

## Round 2 — paused-run exemption (finding 18)

The round-1 bound killed legitimately paused runs. Confirmed on a real fixture
before fixing: on the *same* run, `Sweep.sweep(threshold_ms: 0)` reported
`skipped_paused: 1` (alive, leave it alone) while `await_run` returned a `stalled:`
error. Because the CLI and the run share the BEAM, that error kills a run the
harness considers alive — strictly worse than the pre-fix hang, which at least left
`wait_for_event`'s own expiry to resolve it.

**The review's suggested mechanism does not hold, and the correction matters.** The
finding proposed exempting `"paused"` from the timeout branch. There is no `"paused"`
run status: `runs.status` only ever holds `running`, `done`, `failed`, `cancelled`
(writers are `Agent.Server`, `Sweep`, `Application`; the live dev store has
`%{"done" => 728, "failed" => 163}`). A status match would have been dead code — the
bound would still kill paused runs, with a test passing beside it. A pause is an
**event + checkpoint** condition: last event `:agent_waiting` plus a `waiting`
checkpoint whose wait is unexpired, exactly as `Sweep.paused?/3` computed it.

- **Extracted the predicate to `Aetheris.RunPause` rather than duplicating it.**
  Finding 18's substance is that a claim of symmetry with the sweep must be *true*;
  two copies would make it false again at the first divergence. `Sweep` now calls
  `RunPause.paused?/3` with the events it already holds; `RunHelpers` calls
  `paused?/2`, which fetches them.
- **Consulted lazily — only once the threshold has already expired**, never per
  poll. `paused?/2` calls `events_for_run` (no cheap last-event query exists), so the
  hot path stays exactly as cheap as round 1 and the extra cost is at most once per
  threshold.
- **Expiry preserved, and negatively tested.** An expired pause and a `waiting`
  checkpoint whose last event is not `:agent_waiting` both still time out. Without
  those two tests the exemption would be an unbounded escape hatch.
- **Accepted consequence, per the finding:** a stuck-forever paused run hangs the CLI
  again. That is the sweep's position too; bounding a pause belongs to
  `wait_for_event`'s `timeout_ms`. Stated in the `await_run/2` moduledoc and given
  its own runbook subsection.

**Touches deviation:** `lib/aetheris/sweep.ex` and the new `lib/aetheris/run_pause.ex`
are outside the ticket's `Touches` list. Recorded here per methodology §6. Sweep's
change is mechanical (private predicate → delegated call, plus a moduledoc line); its
behaviour is unchanged and its existing tests cover it.

### Findings 20 and 21

- **20 (test used `paused` as an intermediate status).** Correct that the test was
  weak, and weaker than diagnosed: with no `"paused"` status, *no* non-terminal status
  transition occurs in the current harness, so there is nothing real to swap to. Kept
  the test as an explicitly-labelled defensive guard on the key's status component,
  renamed and commented to say so, with a synthetic status value that cannot be
  mistaken for a real one. The paused semantics now live in their own tests.
- **21 (global-env hazard).** Comment added to both env-mutating tests naming why
  their `async: false` is load-bearing and what to do before a future async caller of
  `await_run` lands.

## Round 2 — a boot-crashing regression the extraction caused (self-found, reported not buried)

Extracting `paused?` out of `Sweep` broke the harness's startup: three
`ArgumentError`/`Store` crashes on every `mix run` boot, taking the whole
application down with `(EXIT) exited in: Aetheris.Application.start/2`.

**Mechanism.** `Store.row_to_event/1` deserialised the event-type column with a bare
`String.to_existing_atom/1` (unchanged since m01, `e4bfa24`). An atom that appears
only inside a `@type` union does not exist at runtime. The startup sweep is the first
thing to deserialise events, and it worked **only because `sweep.ex` itself
pattern-matched `%Event{type: :agent_waiting}` literally** — that literal was the
sole reason the atom existed. Moving the predicate to `RunPause` (which the sweep
calls only *after* `events_for_run` has already deserialised) removed the literal
from the load path, and the store began crashing on any stored `:agent_waiting`
event.

**Isolation, before fixing.** 3 crashes per boot on the round-2 tree; 0 at the
round-1 commit (`4392194`); 0 pre-BL-031 (`9b2b102`). So: mine, not pre-existing —
though the *fragility* it exposed is pre-existing and was one unlucky refactor away
from firing for anyone.

**Fix — remove the coincidence, do not restore it.** The tempting one-line fix is to
keep a literal `:agent_waiting` somewhere in `sweep.ex`. That re-creates exactly the
load-bearing coincidence, which is the class this batch has been promoting. Instead:
`Trajectory.Event` now carries `@event_types` as literal atoms with a `known_types/0`
accessor, and `Store` builds a compile-time `@event_type_map` from it (mirroring the
in-tree precedent already in `Trajectory.File`, `file.ex:95`, which got this right),
raising a named error on an unknown type rather than crashing on a missing atom. The
atoms now live in the constant pool of the module that does the deserialising, so
their existence depends on nothing external.

**Why no gate caught it.** `mix test` was green (881, 0 failures) throughout — in the
test environment the modules are all loaded, so the atom always exists. It is visible
only on a real boot against a store containing such an event, which is why it
surfaced from a manual demo run rather than the suite. Worth noting as a coverage
blind spot, not just an anecdote.

**Touches deviation (second):** `lib/aetheris/trajectory/event.ex` and
`lib/aetheris/store.ex`. Outside the ticket, and unavoidable — shipping the round-2
extraction without it means shipping a harness that crashes on boot.

**Carried, needs a backlog row (flagging, not filing — b3's row is not mine to cut):**
the event-type list now exists in three places — `Event.@type event_type`,
`Event.@event_types`, and `Trajectory.File.@event_type_map`. `Store` now derives from
the canonical one; `Trajectory.File` still has its own copy, and the `@type` union
cannot be derived from the list. A drift between them is silent. Suggest a row to
collapse `File`'s copy onto `known_types/0` and add a test asserting the union and
the list agree.

## Forward

- The `:not_found` asymmetry between `RunHelpers` (fail fast) and `Eval.Runner`
  (retry until deadline) is now the only unbounded-ish divergence left between the
  two await paths. It is deliberate on both sides today and was explicitly out of
  scope here; noting it as an observation, not a defect — no backlog row cut, since
  neither behaviour is currently wrong.
