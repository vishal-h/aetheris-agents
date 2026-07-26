# BL-030 — Early-return fork (Rig use case) — review

**Reviewer:** claude-ui · **Round:** r1 · **Date:** 2026-07-26

**Packet:** `docs/reviews/bl-030-review-packet.md` (r0, agents `e58599c`).
**Under review:** harness `aetheris` @ `ae0c510` · agents/Rig `aetheris-agents` @
`b5e8eee`.
**F1 resolution:** harness `f79365a`.

---

## Verdict

**Approve. No blocking findings.** One non-blocking finding (F1), fixed in this
cycle. Merge is gated on the manual GUI pass (§1h of the packet), which is
genuinely outstanding.

The stderr / Part-C contract is preserved and deadlock-safe, the mode seam is
clean, the Rig early-return property is asserted structurally (the strong way),
and — the thing worth leading with — **the vacuous done-check the ticket
specified was caught and replaced rather than shipped.**

## Reviewer's own error, owned first

The harness done-check named in the ticket — "`capture_io` asserts a
`{"status":"forked","run_id":…}` line precedes the completion line" — **was
vacuous, and it was the reviewer's sketch.** It cannot fail: both writes happen
inside `Aetheris.CLI.run/1`, so their ordering is fixed by code position, not by
the emit being ahead of the await. That is the **Silent-wrong-answer** class.

Correctly caught, correctly mutation-verified (emit-after-await → still green),
and correctly replaced with a test of the real property rather than shipped as
specified.

---

## F1 — non-blocking, resolved — the replacement timing test was BL-054's class, and its rationale was backwards

**Raised against r0.** The replacement test asserted `lead ≥ 100 ms`, where the
lead is created by `await_run/2`'s 200 ms poll floor. Two problems, both latent:

**(a) The coupling the comment denied.** The comment said the threshold
"deliberately does not encode the poll interval, which is free to change". That
is the wrong way round. A fixed 100 ms threshold sitting *below* the interval
breaks — false-negative, "the emit is not ahead of await" — the moment anyone
drops `@poll_interval_ms` below ~106 ms. Decoupling the threshold from the
interval is precisely what makes an interval change break it *silently*. If the
interval is free to change, the threshold should track it, not sit under it.

**(b) A low-probability race.** The lead exists only because the stub fork
finishes *during* `await_run`'s first 200 ms sleep rather than *before* its first
check. The measured 197–200 ms window held across five runs, but a schedule that
let the run reach `run_complete` before the first status check would collapse the
lead to ~0 and false-fail correct code — the fixed-ms-window-in-an-unbounded-
schedule shape **BL-054** tracks, and what the "poll for events, not time" rule
exists to prevent.

**Suggested mechanism (did not hold).** The review proposed seeding a multi-step
stub on the source — a couple of `type: :tool_call` responses, as in BL-039's
continuation arm — so the fork is *observably* in-flight.

**This was checked against source before adoption and is wrong.** A forked run
does not inherit the source's stub responses: `Fork.assemble_config/5` builds its
config from the source trajectory's `meta`, which carries no `stub_responses`
key, and does not set one. Verified against a real fork trajectory — meta keys
are `containment, finished_at, fork_from, fork_step, max_steps, mode, model,
overlay_changes, provider, sandbox_path, seed, started_at, step_count,
system_prompt, tools, user_prompt`, and the fork's own event stream is
`prompt_built → llm_called → llm_responded → run_complete`, a single
stub-exhausted step. Seeding the source lengthens the *source*, not the *fork*.

Per the **finding-binds-by-its-invariant** rule (harness `CLAUDE.md`), the
invariant was implemented and the sketch was not.

**Resolution (harness `f79365a`).** The wall-clock threshold is gone. The test now
asserts structurally: the moment the fork-start line appears in the buffer,
`Task.yield(task, 0)` must be nil. "Not returned" is monotone backwards in time,
so a nil yield read *after* the line was observed proves the line preceded the
return. No millisecond constant survives, and nothing is coupled to the poll
interval — **(a) is closed outright.**

**(b) is named, not closed, because it cannot be closed from the test side.** The
window still exists only because `await_run/2` finds the run non-terminal at its
first check; a fork that completed sooner would fail the test on correct code.
The forked run cannot be made observably long-running for the reason above. The
failure message therefore names both possible causes rather than asserting one,
and the notes record the residual against BL-054's class.

One correction to the finding's framing, from measurement: the risk direction is
a **fast** machine, not a loaded one. Load slows the forked run more than it slows
the CLI's first status check, so it *widens* the window. Measured 30/30 green
across seeds and 8/8 green with every core saturated.

**Also added, unprompted and worth noting:** a deterministic companion test with
no clock at all — a fork whose *run* fails still emits its id, and the await's
error names that same id. This covers the "emit inside the success branch" /
"emit derived from the await's result" family, which the structural test
structurally cannot see, since both would leave its window intact. Better
coverage than the finding asked for.

---

## Endorsements (no action)

**`parse_run_id` deletion is right, and the do-not was the thing at fault.** "No
`parse_run_id` change" was premised on the blocking path staying — but the
ticket's own Rig bullet *replaces* `.output()`, which removes its only consumer,
so keeping a private `cfg(test)`-only function would be `dead_code` under a clean
gate. The invariant it protected (what counts as a run_id line) is preserved
byte-for-byte as `run_id_from_line/1` and still tested. Correctly named as a
deviation rather than done silently.

**The two off-Touches files are the *right* touches.** `runbook.md`'s fork section
and `TrajectoryView`'s unmount-guard comment both became false-in-place; a change
that falsifies adjacent prose must sweep it. Named, not absorbed.

**stderr design is sound and preserves Part C.** Piped (not nulled), a collector
thread from t=0 serving both the start-failure read and the successful-fork
anti-wedge, `start_failure_error` keeping `fork failed: <reason>`, both arms
unit-tested. The "one collector from spawn removes the ordering question"
reasoning is correct; no pipe can deadlock.

**Mode seam.** `resolve_mode/1` moved to `Formatter` — right dependency direction
(the command must not reach back into the dispatcher), and the type gets one home.

**The dangling-§4 note** landed exactly as asked: still-true sentence, stale
`(BL-030)` ref, BL-062 repoints, D2 precedent cited.

---

## Merge gate

**The manual GUI pass (packet §1h) gates merge — it is the real gate, not a
formality.** The frontend half (`handleForked`'s `status: 'running'` plus the
BL-005 polling it switches on) has zero automated coverage; Rig has no frontend
test runner (BL-029 / BL-038 precedent). Four arms:

1. Immediate open — "Fork from here" on a completed step of a real (non-stub) run
   opens the child in seconds, not at completion.
2. Streams as `running` — events appear progressively, and the poll stops itself
   when `run_complete` lands.
3. Header run_id matches the forked run.
4. Start-failure surfaces on the click (`fork failed: …`); a fork that starts and
   then fails surfaces on the child, not the click.

`mix hex.audit` red is **BL-060** — expected, named, not re-triaged.

## At closure

- File **BL-062** — the split-out `--provider`/`--model` override row, with its §8
  determinism-contract edit repointing §4's `(BL-030)` ref.
- Carried and untouched, still open: **BL-048** (CI dispatch), **BL-057**.
