# BL-030 r1 — completion transition (folded BL-063)

Rig-only. Follows the BL-030 early-return fork
(`docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md`).

**Invariant:** a fork's real metadata — id, provenance banner, `started_at`,
duration — must appear without a manual re-mount once the run completes in place.

---

## Scout: the data-availability seam

Both questions the ticket posed were answered from source and confirmed against
live data before a mechanism was chosen.

### (a) Does `runs.config_json` carry `fork_from` / `fork_step`? — **Yes.**

`encode_config` (`../aetheris/lib/aetheris/agent/server.ex:759-768`) strips
exactly five fields:

```elixir
    |> Map.delete(:stub_responses)
    |> Map.delete(:coordinator_pid)
    |> Map.delete(:blackboard_pid)
    |> Map.delete(:label)
    |> Map.delete(:max_duration)
```

`fork_from` and `fork_step` are `RunConfig` fields and are not among them.
Confirmed against a real row (`fork-d0b6042bcb44c369`): `fork_from =
fixture-unlabelled-fork-CbZX6w`, `fork_step = 0`, both present from the moment
the run is inserted.

So provenance **and** the real `started_at` are available from `harness_get_run`
during streaming, with no wait for the file. `RunDetail.config` is already the
raw `config_json` string (`harness.rs:280-287`) — the data was on the wire the
whole time; nothing consumed it.

### (b) Is the trajectory file written before or after `run_complete`? — **The event precedes it; the status follows it.**

The ordering at run end, read end-to-end:

| # | what | where |
|---|---|---|
| 1 | `run_complete` **event** appended to SQLite | `loop.ex:267` |
| 2 | loop returns | |
| 3 | `trajectory.json` written — tmp file, then **atomic rename** | `server.ex:680` → `file.ex:37-38` |
| 4 | `runs.status` set to a terminal value | `server.ex:456-465` |

This is the decisive finding. **A reload fired on the `run_complete` event races
the file write** — exactly the hazard the ticket suspected, and it is real, not
theoretical: the event is durable in SQLite before `File.rename/2` has been
called. **A reload gated on the run row's terminal status cannot race**, because
the status flip strictly follows the completed atomic rename.

So the mechanism is status-gated, and **no retry is needed or used**. The ticket
offered "a short retry if it's written just after the event" as a fallback; the
ordering makes it unnecessary, and a retry would have been an untestable code
path papering over a trigger chosen one step too early.

One asymmetry worth recording: `server.ex:680` **discards** the write's return
value (`result` in the following `case` is the *loop's* result, not the write's),
so a failed file write still flips the status to `done`. Terminal status
therefore means "the harness is finished writing", not "the file exists" — which
is why the reload is best-effort and failure keeps the reconstructed view.

## What changed

- `hooks/useTrajectory.ts` — new `reload()`, deliberately **silent** (does not
  touch `loading`, since `TrajectoryView` renders `Loading…` off it and a reload
  that blanked the streamed view would be no better than the tab-out this
  removes). Clears `error` on success — that is what flips the view to
  file-backed; keeps the prior error on failure.
- `hooks/useHarness.ts` — `useRunDetail` takes `{ polling }` and self-terminates
  on a terminal status, mirroring `useRunEvents`. The ordering rationale lives in
  its doc comment so the next reader does not "simplify" the trigger back to the
  event.
- `lib/reconstructTrajectory.ts` — takes the `RunDetail` row instead of a bare
  config string; prefers the row's `started_at`/`finished_at`; emits
  `fork_from`/`fork_step` into meta when the config carries them.
- `components/modules/harness/TrajectoryView.tsx` — polls the row while the
  fallback is engaged, derives `liveStatus` from the row, and reloads the file
  once the status is terminal. The reconstructed banner now reads the row's
  status too.

### The `??` → `||` fix is the whole "Invalid Date" symptom

```ts
- started_at: run?.started_at ?? stringField(config, 'started_at'),
+ started_at: detail?.started_at || run?.started_at || '',
```

A run navigated to straight from a fork carries a *synthesized* summary whose
`started_at` is `''` (`RunList.handleForked`). `''` is neither `null` nor
`undefined`, so `??` kept it and the view rendered "Invalid Date" — and the
duration row vanished, since `TrajectoryBody` gates it on
`meta.started_at && meta.finished_at`. `||` falls through the empty string to
the row's real timestamp. `config_json` has no timestamps (they are run-row
columns), so the old second operand could never have supplied one either.

## Scope held

BL-005's "completed runs unaffected" gating is intact: the fallback queries stay
behind `fallbackRunId`, which is null whenever the file loaded, so a completed
run opened directly still issues **zero** extra queries and takes the unchanged
file-backed path. The row poll is gated on the same value.

The fix is deliberately **not** fork-specific — it triggers on any run watched
through its own completion, which is what the ticket asked for. The synthesized
summary's `status` is left as the `'running'` seed rather than being mutated on
completion: the real row supersedes it as soon as it arrives, which covers every
run rather than only the one path that synthesizes a summary.

## Verification

Rig has no frontend test runner (`package.json` has no test script and no
vitest/jest dependency), so **the GUI pass is the gate**. What could be verified
without one was:

`reconstructTrajectory` is a pure function with type-only imports, so it was
executed directly under `bun` against the exact summary `handleForked`
synthesizes. 11 checks, all passing: the row's `started_at` wins over the
synthesized `''`; it parses to a valid `Date`; `finished_at` likewise; the
duration formula yields 12s; `fork_from`/`fork_step` are present *while running*
so the banner renders pre-file; the `isFork` gate is true; a non-fork grows no
`fork_from`; and a null detail row degrades without throwing.

Mutation-checked: reverting the operand order to `run?.started_at ?? …`
reproduces the original defect exactly — `started_at: ""`, invalid `Date`,
duration `undefined`.

The script is scratch, not committed — adding a test runner is outside this
ticket. It is reproduced in the packet so the reviewer can re-run it.

**Not verified without the GUI:** that the reload actually fires in the browser
on the status transition, that the banner disappears in place, and that the
polling stops. Those are the GUI pass, arm 2.

## Gates

`bun run lint` (clean) · `bunx tsc -b` (clean) · `bun run build` (clean) ·
`cargo test` (21 passed, 1 pre-existing ignored) — all green. Rust untouched this
round.
