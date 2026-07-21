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
  on the same evidence the sweep and the operator-visible badge call dead.

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

## Forward

- The `:not_found` asymmetry between `RunHelpers` (fail fast) and `Eval.Runner`
  (retry until deadline) is now the only unbounded-ish divergence left between the
  two await paths. It is deliberate on both sides today and was explicitly out of
  scope here; noting it as an observation, not a defect — no backlog row cut, since
  neither behaviour is currently wrong.
