# BL-007 / t0 — implementation notes: `caused_by` event lineage field

**Ticket:** [bl-007-t0-caused-by.md](./bl-007-t0-caused-by.md) · **Milestone:** [BL-007](./README.md)
**Date:** 2026-07-18 · **Repos:** harness `../aetheris/` (code) + `aetheris-agents/` (milestone-doc corrections)

## What was built

A Rule-14 three-place change on the harness, in one harness commit:

1. **`../aetheris/lib/aetheris/trajectory/event.ex`** — `:caused_by` added to `defstruct`
   (not to `@enforce_keys`, so it defaults to `nil`) and to the `@type t` typespec as
   `String.t() | nil`. `new/5` is unchanged: it builds the struct without `caused_by`, so the
   `nil` default applies — no emit-site wiring, per scope.
2. **`../aetheris/lib/aetheris/trajectory/file.ex`** — `event_to_map/1` serialises
   `"caused_by" => event.caused_by`; `map_to_event/1` reads `Map.get(data, "caused_by")`
   (`Map.get`, not `Map.fetch!`) so a pre-existing file lacking the key deserialises to `nil`.
3. **`../aetheris/docs/aetheris/specs.md`** — §1 Event Schema typespec gains the `caused_by`
   line; §6 Trajectory File Format JSON example gains `"caused_by": null` and a lineage
   invariant paragraph.
4. **Tests** — `event_test.exs`: `new/5` leaves `caused_by` nil; a struct built with an
   explicit `caused_by` holds it. `file_test.exs`: a round-trip test (one triggered event
   points back at its cause id, one nil) and a **back-compat** test that writes a legacy
   trajectory JSON with no `caused_by` key at all and asserts it loads as `nil`.

## Decisions

**Specs target — harness specs, not the Rig mirror (adjudicated with the operator).** The
event struct is harness-owned, so the normative schema statement lives in
`../aetheris/docs/aetheris/specs.md` (§1 + §6), which also keeps the Rule-14 change in one
harness commit. Rig's `docs/rig/specs.md` §6 is a *mirror* of the wire shape for Rig's
consumption; t0 gives Rig no consumer (**D4** defers lineage queries, and no Rig ticket reads
`caused_by` this milestone). `caused_by` is a top-level field — not an event type or payload
key — so it is **not a drift-checked row** in any doc; adding it keeps `drift_check` green
regardless. The Rig mirror row is deferred to **t5's sync sweep** (earlier only if a Rig
ticket starts reading the field). Recorded, not silent.

**Rig JSON-parser tolerance — verified, PROCEED (Rider 2).**
`rig/src-tauri/src/commands/trajectory.rs` `trajectory_load` (lines 44-70) parses the
trajectory file into a `serde_json::Value` and extracts fields **by key** into
`struct TrajectoryEvent` (`e["id"].as_str()…`, `e["payload"].clone()`). There is **no strict
deserialisation and no `#[serde(deny_unknown_fields)]`** — the additive nullable `caused_by`
key is silently ignored by the reader. So the JSON shape change does not break Rig's
trajectory view. (Had the parser been strict, that would have been a blocking scope-addition
back to the milestone doc — it was not.)

## Review round 1 — second-serializer audit (finding 1, answered with evidence)

**Question:** does any path other than `Trajectory.File` serialize `%Event{}`, silently
dropping `caused_by`?

**Answer: yes — the SQLite index path, and the drop is by-design / in-scope-excluded.**
- `Trajectory.Log` keeps events in ETS and has **no file serializer of its own**; on every
  append it calls `Store.insert_event/1`
  (`../aetheris/lib/aetheris/trajectory/log.ex:105`).
- `Store.insert_event/1` → `do_insert_event/2`
  (`../aetheris/lib/aetheris/store.ex:1006-1023`) writes exactly seven columns:
  `INSERT INTO events (id, run_id, step, seq, type, payload_json, timestamp)`
  (`store.ex:1008`); only `event.payload` is JSON-encoded (`store.ex:1018`). The `events`
  table DDL (`store.ex:803-812`) has **no `caused_by` column**, so `caused_by` is dropped on
  the DB path.
- This loses nothing today: nothing populates `caused_by` yet, and the trajectory **file**
  (which round-trips it) is canonical — `file.ex` moduledoc: *"The trajectory file is the
  canonical source of truth for a run. SQLite is an index; replay reads from this file."*
  The index reconstructs events with `caused_by == nil` (struct default) — no crash.
- The drift `payload_fields` check samples `payload_json` keys only, so a top-level field is
  invisible to it — this is why drift stays green.

**Disposition (per the reviewer's fork): a specs "trajectory-file-only" note, NOT a t2 rider.**
t2 (fork seed-carry + CLI convergence) touches neither event persistence nor the `events`
table, and **D4 defers the lineage queries** that would justify a SQLite `caused_by` column.
Indexing the field in SQLite (a DB migration + `do_insert_event`/`events_for_run`/`row_to_event`
wiring) composes with D4's deferred work as a future backlog item. The scope note is added to
harness `specs.md` §6 (finding 1) in the same review-fix commit.

**Rider for t5's D4 backlog entry (carry forward).** When t5 writes the D4 deferral entry, it
must capture explicitly that D4 is not merely index/API work: the `events` table has **no
`caused_by` column** (`../aetheris/lib/aetheris/store.ex:803-812`), and `do_insert_event/2`
(`store.ex:1006-1023`) persists only seven columns — the field lives in trajectory files only
today. So a lineage-query consumer needs a store-side migration first. Recording the citations
here so the deferred ticket inherits the gap instead of rediscovering it from scratch.

## Ticket-text corrections landed with t0 (Rider 1)

Both are doc defects in the committed t0 ticket text, corrected in the milestone doc (now
`README.md`) and `bl-007-t0-caused-by.md` per the §8 doc-sync rule:

1. **Vague Touches path.** `../aetheris/docs/… specs §6` (ellipsis — the vague-path defect the
   methodology names) → concrete `../aetheris/docs/aetheris/specs.md` (§1 + §6).
2. **Broken done-check step (verified live).** `drift_check.py` exists only in
   `aetheris-agents/scripts/` (`REPO_ROOT = Path(__file__).parent.parent`); the harness
   `../aetheris/scripts/` holds only `sprint.sh`. The ticket's
   `cd ../aetheris && … && python3 scripts/drift_check.py` fails **file-not-found**
   (reproduced this session). The done-check is repo-qualified: the drift step runs from
   `aetheris-agents/`.

## Pre-existing `milestone_status` WARN — resolved in review round 1 (finding 4)

`drift_check` was emitting a **pre-existing** WARN: `milestone_status: bl-007/README.md not
found`. The `bl-007/` milestone dir (created by `e733b3c` on main, before this ticket) named
its doc `milestone.md`, whereas the drift checker's convention (`drift_check.py:558-565`)
expects a `README.md` containing a `Status:` line — every other milestone dir has one. Non-strict
WARN only (t0's done-check exits 0), but it would have **failed t5's `drift_check --strict`**.
Operator ratified the rename (the naming was claude-ui's): `git mv milestone.md README.md`,
Status line reformatted to the `**Status: <STATE>** —` convention the other dirs use, backlinks
swept. Drift now reports `milestone_status: PASS`. (No t0 *code*-branch involvement — this was a
docs-only correction, its own commit on the ticket branch.)

## Verified-against note

Ticket recon was against harness `19c08be`; current HEAD is `c195cbb`. The intervening commit
is `c195cbb` "Add research brief on ActiveGraph architecture" — a docs-only commit — so the
harness *code* is identical to the recon commit. `caused_by` reconfirmed absent from `lib/`
and `test/` at HEAD.

## Gate results (all green)

- `mix format --check-formatted` — OK
- `mix test test/aetheris/trajectory/` — 34 tests, 0 failures
- `mix test` (full) — 865 tests, 0 failures
- `mix hex.audit` — no retired/advisory packages
- `mix credo --strict` (touched files) — no issues
- `mix dialyzer` — passed, 0 errors
- `python3 scripts/drift_check.py` (from `aetheris-agents/`) — 0 FAIL, 0 WARN after the
  finding-4 rename (was 1 pre-existing milestone_status WARN, now PASS), 7 INFO; exit 0

## Review round 1 — dispositions

Review at `docs/reviews/bl-007-t0-review.md`. No blocking findings; t0 merged as-is.

1. **[question] Single-serializer confirmation** — answered above with file:line; the SQLite
   index (`Store.insert_event/1`) is the second serializer and drops `caused_by` by design.
   Resolved as a specs "trajectory-file-only" note (harness `specs.md` §6), not a t2 rider.
2. **[non-blocking] Specs §6 invariant wording** — fixed: the `tool_result ← tool_called ←
   llm_responded` chain is now marked *illustrative, once populated* so the holding invariant
   (round-trip, nil-back-compat) is not blended with future-work emit convention.
3. **[non-blocking] Done-check defect still live in t1/t2** — swept: the milestone doc's
   (now `README.md`) t1 and t2 done-checks repo-qualified; t3/t4 carry no drift command; t5's
   bare `drift_check --strict` annotated to run from `aetheris-agents/`. Defect class closed
   across the milestone.
4. **[non-blocking, pre-existing] `milestone_status` WARN / `README.md` naming** — **DONE**
   (operator ratified the rename). `git mv milestone.md README.md`; Status line reformatted to
   convention; backlinks swept (in-repo refs + the stale `milestone.md:114-144` line range →
   `README.md:115-158`). No GitHub issue re-sync needed: no separate t0 issue exists, and epic
   #48 already refers to it generically as "Milestone README" (not a hardcoded path). Drift:
   `milestone_status` WARN → PASS.

**Boundary observation (per the operator's note) — watermark fired.** t0's branch carried
**four** doc-correction commits (`10c0f2a` ticket-text; `ae01b44` review round 1; `2ab87b5`
harness specs note; `6d4bf1f` finding-4 rename) alongside the single code commit (`f80521e`).
The operator's rule: a **fifth** signals the BL-007 milestone doc wanted its own correction
round rather than riding t0. The **round-1-closeout commit `b6fd983` is that fifth** (this notes update +
the README issue-tracking decision + t5 D4 rider) — the two items were operator-requested at
round close, so it lands here, but it **fires the signal**: any *further* milestone-doc change
must be a dedicated correction round (its own BL-xxx / branch), not a sixth commit on t0's
branch. Recorded so the boundary is explicit at milestone-end.

**Realized (loop closed).** The watermark fired at `b6fd983` (the fifth) and was **honored,
not slid**: the next milestone-doc change — the t1 pre-flight ticket-text edits (verification
table + read-only Touches) — went to a **dedicated branch `bl-007-t1-prep` (`1d48ff3`)**, cut
off the t0 tip, rather than a sixth commit on t0's branch. So the history reads true: four
clean → fifth fires → sixth-and-beyond diverted to their own round.

**Learning-promotion candidate (watch for recurrence):** *done-check commands must be
repo-qualified and existence-verified the same way Touches paths are* — a command referencing
a script that exists only in the sibling repo is the same defect class as an unqualified path.
Bit once at t0 (drift step); finding 3's sweep is the pre-emptive fix.
