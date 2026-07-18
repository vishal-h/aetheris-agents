# Review — bl-007 t0 — round 1

## Findings

1. [question] Single-serializer confirmation. The packet proves `caused_by`
   round-trips through `Trajectory.File.event_to_map/1` / `map_to_event/1`. Does
   any *other* path serialize `%Event{}`? Two candidates visible from here:
   (a) `Trajectory.Log`'s persistence (the pre-existing "survive a Log restart"
   test suggests it writes via File.write/3 — confirm it has no serializer of its
   own); (b) whatever DB path the drift checker's `payload_fields` check samples
   ("sampled DB payload fields consistent with specs.md §6" implies event payloads
   reach the store somewhere). If a second serializer exists, `caused_by` silently
   drops on that path. No data can be lost today (nothing populates the field —
   this is why the finding is a question, not blocking), but the answer decides
   whether t2 gains a one-line rider or specs gains a "trajectory-file-only" note.
   Answer with file:line either way.

2. [non-blocking] Specs §6 invariant wording. The new bullet sits in an invariants
   list but its example chain (`tool_result ← tool_called ← llm_responded`) reads
   as implemented emit behavior, which t0 deliberately does not ship. Suggested
   fix: mark the chain illustrative — e.g. "(e.g., once populated: tool_result ←
   tool_called ← llm_responded)" — so the invariant that *holds* (round-trip,
   nil-back-compat) is not blended with the convention that is future work.

3. [non-blocking] Same done-check defect is still live in t1 and t2. Commit
   10c0f2a corrected the drift-step repo-qualification in t0's two blocks only;
   `milestone.md` t1 and t2 done-checks still read
   `cd ../aetheris && … && python3 scripts/drift_check.py` — the exact form
   reproduced as file-not-found. Sweep both blocks (and re-check t3–t5) in the
   same correction style before the t1 issue is generated, or the defect recurs
   next ticket by construction.

4. [non-blocking, pre-existing — disposition recommendation for §5b] The
   `milestone_status` WARN traces to my own naming choice (`milestone.md`) against
   the checker's convention (`README.md` with a `Status:` line, as every other
   milestone dir has). Recommend: rename `milestone.md` → `README.md` (one
   status-bearing file, matches convention) rather than adding a second file;
   sweep internal references (`bl-007-t0-caused-by.md` backlink, issue backlinks)
   in the same commit. Small tracked ticket, must land before t5's
   `drift_check --strict`. Human ratifies — the original naming was claude-ui's.

## Cross-ticket notes

- Learning-promotion candidate (watch for recurrence): *done-check commands must
  be repo-qualified and existence-verified the same way Touches paths are* — a
  command referencing a script that exists only in the other repo is the same
  defect class as an unqualified path. Bit once (t0); finding 3 is the test of
  whether it bites twice.
- Finding 1's answer belongs in t2's contract refs if it produces a rider:
  t2 touches fork's config assembly, and if a second serializer exists it is
  fork-adjacent (checkpoint/store writes during live runs).
- The specs invariant's chain example, once corrected per finding 2, becomes the
  reference wording for t2+ when fork provenance starts populating `caused_by` —
  keep the two consistent.

---

## Disposition (claude-code, round 1)

t0 merged as-is (reviewer: mergeable once the diff is eyeballed; no blocking findings).

1. **Answered — file:line evidence.** A second serializer exists: the SQLite index.
   `Trajectory.Log` has no file serializer; on every append it calls `Store.insert_event/1`
   (`../aetheris/lib/aetheris/trajectory/log.ex:105`). `do_insert_event/2`
   (`../aetheris/lib/aetheris/store.ex:1006-1023`) writes only
   `id, run_id, step, seq, type, payload_json, timestamp` (`store.ex:1008`); the `events`
   DDL (`store.ex:803-812`) has no `caused_by` column, so it drops on the DB path — by
   design. Nothing populates the field yet, and the trajectory **file** is canonical for
   replay (`file.ex` moduledoc). Resolved as a specs "trajectory-file-only" note (harness
   `specs.md` §6), **not** a t2 rider — t2 touches neither event persistence nor the
   `events` table, and the SQLite `caused_by` column composes with D4's deferred lineage
   queries as a future backlog item.
2. **Fixed** — harness `specs.md` §6 chain marked *illustrative, once populated*.
3. **Fixed** — `milestone.md` t1 + t2 done-checks repo-qualified; t5 annotated; t3/t4 carry
   no drift command. Defect class closed across the milestone.
4. **Done** — operator ratified the rename. `git mv milestone.md README.md`; Status line
   reformatted to the `**Status: <STATE>** —` convention; in-repo backlinks swept (incl. the
   stale `milestone.md:114-144` line range → `README.md:115-158`). No GitHub re-sync needed
   (no separate t0 issue; epic #48 already says "Milestone README", not a hardcoded path).
   Drift: `milestone_status` WARN → PASS.
