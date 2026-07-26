# BL-030 r2 — seed the post-fork selection from the real run row

Rig-only. Closes the r1 residual: the Events tab still showed "Invalid Date"
until the run was re-selected.

Follows `bl-030-r1-completion-transition-implementation-notes.md`.

---

## The residual, and why r1 missed it

r1 taught `TrajectoryView` / `reconstructTrajectory` to prefer the real `runs`
row over the synthesized summary's `started_at: ''`. The Events tab header does
not go through `reconstructTrajectory` at all — it reads the selected summary
directly:

```tsx
Started: {new Date(selectedRun.started_at).toLocaleString()}   // RunList.tsx:474 (pre-r2)
```

`new Date('')` is an invalid Date, so the header rendered the literal string
"Invalid Date". Two more fields on the same header were blank from the same
cause: `selectedRun.label` (`''`) and `selectedRun.model` (`''`).

This is the **Adjacent-case** class from the harness `CLAUDE.md`: r1's blast
radius was one consumer wider than the view it was written against, and r1's
per-consumer approach is what made it leaky — fixing consumers means every
consumer must be enumerated, and this one was not.

## The fix: remove the invention, don't chase its consumers

`RunList.handleForked` now fetches the real row and seeds the selection from it,
via a new pure mapper `lib/runSummary.ts` → `runSummaryFromDetail/1`. The
synthesized literal is gone from the normal path.

**The row is guaranteed to exist by then**, which is what makes this safe rather
than a race traded for a bug. `Aetheris.start_run/1` calls `Server.run/1`, a
**synchronous** `GenServer.call` (`../aetheris/lib/aetheris/agent/server.ex:70-72`),
whose `handle_call(:run, …)` upserts the row — `status`, a real `started_at`,
`config_json`, `label` — before returning (`server.ex:229-235`). The CLI's
fork-start emit happens *after* that call returns, so by the time Rig has parsed
the forked id off stdout the row is already committed. Awaiting one local SQLite
read in `handleForked` cannot race the insert, and costs nothing beside the
seconds `fork_run` just spent.

This was the r1 scout's finding taken one step further: that scout established
`config_json` + the `runs` row already carry everything the views need. r1 used
that to enrich one view. r2 uses it to delete the placeholder.

### Every consumer of the selected run, enumerated

The point of a source fix is that this list needs no per-item work — but it is
enumerated rather than assumed, since "the fix reaches them all" is exactly the
claim r1 got wrong:

| consumer | field | before | after |
|---|---|---|---|
| `RunList:440` events polling | `status` | `'running'` (seed) | row status |
| `RunList:456` status badge | `status` | seed, else `isComplete` | row status, else `isComplete` |
| `RunList:473` header label | `label` | `''` — blank | row label |
| `RunList:481` header run_id | `label` vs `run_id` | always shown (`'' !== id`) | shown iff genuinely unlabelled |
| `RunList:491` header model | `model` | `''` — blank | from `config_json` |
| `RunList:494` header started | `started_at` | `''` → **"Invalid Date"** | row timestamp |
| `TrajectoryView:355` parentLabel | `label` | `''` → always undefined | real label inherited |

The last row is an incidental **resolution of a documented compromise**, not just
a fix. That guard's comment recorded that forking a fork before a Refresh "drops
a real label rather than passing it on", accepted because the placeholder could
not know the label. With the row seeded, a labelled fork now hands its label to a
grandchild immediately. The comment is updated to say so rather than left
describing a cost that no longer exists.

## Failure path, and the one guard added beyond the ticket

If `harness_get_run` fails, the fork itself still succeeded — the id came off the
CLI's stdout — so losing navigation would be worse than a sparse header. The
fallback selects the run with what is certain (its id, as both `run_id` and
`label`) and leaves `started_at` empty rather than inventing one; the views read
the row independently and fill themselves in.

That fallback is a path *this change introduces*, and it is the only remaining
way an empty `started_at` reaches the Events header — so the header's render is
guarded: `formatTimestamp/1` returns `—` for an absent or unparseable timestamp.
This is deliberately **not** the localized fix the review argued against: it does
not teach the header to fetch the row, and it adds no second source of truth. It
makes a degraded render honest instead of broken. Named here so it can be
rejected on its own terms.

## Verification

Rig still has no frontend test runner, so the GUI pass remains the gate. What
could be verified without one:

`runSummaryFromDetail` is pure, so it was executed under `bun` against the row
shape `harness_get_run` returns for a just-started fork. 13 checks, all passing —
including the symptom asserted the way the consumer actually renders it:

```ts
check('Events header renders a real date, not "Invalid Date"',
  new Date(s.started_at).toLocaleString() !== 'Invalid Date', …);
```

Covered: row timestamp, label, provider/model parsed from `config_json`, status,
`finished_at` null passthrough, cost/tokens `null` (not `0`, so Cost renders "—"),
counts `0`, the unlabelled-fork `label === run_id` case the `parentLabel` guard
depends on, and malformed `config_json` degrading without throwing or losing the
timestamp.

**Mutation-checked:** reverting the mapper to `started_at: ''` reproduces the
reported symptom verbatim — `got: "Invalid Date"`.

r1's `reconstructTrajectory` script was re-run unchanged: 11/11 still green, so
the r1 fix is not regressed by the r2 change beneath it.

Both scripts are scratch, not committed; reproduced in the packet.

**Not verified without the GUI:** that the Events tab header shows the real date,
label and model on the first landing after a fork, with no re-select.

## Gates

`bun run lint` (clean) · `bunx tsc -b` (clean) · `bun run build` (clean) ·
`cargo test` (21 passed, 1 pre-existing ignored) — all green. Rust untouched.
