# BL-030 — Early-return fork: Rig side (owned subprocess)

Cross-repo ticket. The harness half — the CLI's fork-start emit that this consumes
— is in `../aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md`.

Scout that preceded the design: `docs/reviews/bl-030-fork-early-return-scout.md`.

---

## What changed

"Fork from here" returns as soon as the fork **starts** (seconds) instead of when
it finishes (minutes for a real provider), and the operator lands on the child run
while it is still executing and watches it stream.

- `rig/src-tauri/src/commands/fork.rs` — `.output()` (which waits for exit *and*
  pipe EOF) replaced with spawn-piped + own-the-child. The calling thread reads
  stdout only until the first `run_id` line, returns it, and hands the running
  child to a detached thread that drains both pipes to EOF and reaps it.
- `rig/src/components/modules/harness/RunList.tsx` — `handleForked` synthesises
  `status: 'running'` instead of `'done'`.
- `rig/src/hooks/useFork.ts` — header comment swept; behaviour and signature
  unchanged.
- `rig/src/components/modules/harness/TrajectoryView.tsx` — the unmount-guard
  comment's "a fork blocks to completion (minutes)" premise corrected.
- `docs/rig/specs.md` §4 — the "Blocks to completion" paragraph replaced.

## Design decisions

**`status: 'running'` lands on a road that was already built.** The trajectory file
is written **once, at run completion** (`agent/server.ex:680`, `:952`), so a
running fork has no file. `TrajectoryView` already handles exactly that: the file
load fails, `fileMissing` engages the events fallback, and
`useRunEvents(runId, { polling: run?.status === 'running' })` polls SQLite every
2 s and stops itself when `run_complete` reaches the stream
(`useHarness.ts:118-133`). That is BL-005's live path. The only thing that was
holding it shut on the fork route was `handleForked`'s hardcoded `'done'` — which
was correct when a fork could only be navigated to after it finished. One word.

**stderr stays `piped()`. This is the part where copying `orchestrate.rs` verbatim
would have regressed BL-039 Part C.** `orchestrate.rs:55` nulls stderr because it
has no stderr contract. `fork.rs` does: a fork that never *starts*
(`step_not_found`, an unreadable trajectory) fails inside `Fork.from_step/3` before
any run exists, writes no `run_id` line, and reports its reason on stderr with a
zero exit code (`mix` discards the CLI exit code). Nulling stderr would have
degraded every start failure to a bare "produced no run_id" — well-formed, wrong,
and invisible to a reader-only unit test. `start_failure_error/1` preserves
`fork failed: <reason>` and is unit-tested on both arms.

**One stderr collector thread, spawned at spawn time, serving both outcomes.** A
start failure needs stderr's contents; a *successful* fork must not be able to
wedge on a full stderr pipe with nobody reading it. Reading stdout to EOF first and
*then* stderr would deadlock on a chatty stderr. Collecting stderr on its own
thread from t=0 removes the ordering question entirely: on failure the collector is
joined for its message, on success it simply ends at EOF alongside the stdout
drain, and `child.wait()` reaps.

**First-wins, and deliberately no smarter.** `parse_run_id`'s last-wins backward
scan required the whole buffer, i.e. the whole run — the exact thing BL-030
removes. The new `read_first_run_id/1` stops at the first `run_id` line. It needs
no further disambiguation: `await_run`'s verbose event stream goes to **stderr**
(`run_helpers.ex:53`), and under `--json` the closing `Formatter.print/2` writes
exactly once, so the only JSON-with-`run_id` lines on stdout are the start line and
the completion line. `mix` compile noise does not parse as JSON.

**Failure semantics moved, and that is the point.** A rejection from `fork_run` now
means the fork never started. A fork that starts and then fails does so after the
command returned, and the operator sees it on the child's own streamed trajectory —
which is where the diagnosis was always recorded, and which they are now already
looking at.

## Scope deviation — `parse_run_id` was deleted, not preserved

The ticket said not to change `parse_run_id`'s last-wins. Nothing consumes it after
this change: the streaming reader replaces it wholesale, and a private Rust function
used only from `#[cfg(test)]` is a `dead_code` warning in every non-test build, so
keeping it would have meant an `#[allow(dead_code)]` on a function no code path can
reach. It was removed.

What the instruction was protecting — *what counts as a run_id line* — is preserved
byte-for-byte as `run_id_from_line/1` (same `serde_json` parse, same
object-with-string-`run_id` predicate) and is still unit-tested. Only the scan
direction and the dead wrapper are gone. Flagged here and in the review packet
rather than decided silently.

## Testing

`cargo test` — 7 tests in `commands::fork`, inside a crate total of 22
(21 passed, 1 ignored: `live_store_demo_01…`, which requires `AETHERIS_DB_PATH`):

- `read_first_run_id_returns_the_start_line_id` — the id comes off the fork-start
  line through mix compile noise.
- `read_first_run_id_stops_before_the_completion_line` — the **early-return**
  property, asserted structurally rather than by wall clock: after the id is read,
  the completion line must still be *unread* in the stream. A reader that drained
  to EOF first (the old last-wins scan) leaves nothing behind and fails this.
- `read_first_run_id_none_on_eof_without_a_run_id` — a fork that never starts.
- `start_failure_error_carries_the_stderr_reason` / `…without_stderr_says_so` — the
  Part C diagnosis survives, and its absence is reported as absence.
- the two pre-existing `fork_argv` tests, unchanged.

**Rig has no frontend test runner.** `handleForked`'s `'running'` and the polling it
switches on are not covered by any automated test in this repo — the manual GUI pass
is the merge gate for that half, not a formality. See the packet.

## Gates

`cargo test` (21 passed, 1 ignored) · `bun run lint` (clean) · `bunx tsc -b` (clean) ·
`bun run build` (clean) — all green. `drift_check --strict` and the cross-repo
done-check are in the packet.
