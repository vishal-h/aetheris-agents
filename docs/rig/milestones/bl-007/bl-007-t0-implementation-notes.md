# BL-007 / t0 — implementation notes: `caused_by` event lineage field

**Ticket:** [bl-007-t0-caused-by.md](./bl-007-t0-caused-by.md) · **Milestone:** [BL-007](./milestone.md)
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

## Ticket-text corrections landed with t0 (Rider 1)

Both are doc defects in the committed t0 ticket text, corrected in `milestone.md` and
`bl-007-t0-caused-by.md` per the §8 doc-sync rule:

1. **Vague Touches path.** `../aetheris/docs/… specs §6` (ellipsis — the vague-path defect the
   methodology names) → concrete `../aetheris/docs/aetheris/specs.md` (§1 + §6).
2. **Broken done-check step (verified live).** `drift_check.py` exists only in
   `aetheris-agents/scripts/` (`REPO_ROOT = Path(__file__).parent.parent`); the harness
   `../aetheris/scripts/` holds only `sprint.sh`. The ticket's
   `cd ../aetheris && … && python3 scripts/drift_check.py` fails **file-not-found**
   (reproduced this session). The done-check is repo-qualified: the drift step runs from
   `aetheris-agents/`.

## Open item flagged (not fixed in t0 — out of scope)

`drift_check` emits a **pre-existing** WARN: `milestone_status: bl-007/README.md not found`.
The `bl-007/` milestone dir (created by `e733b3c` on main, before this ticket) names its doc
`milestone.md`, whereas the drift checker's convention expects a `README.md` with a `Status:`
line (every other milestone dir has one). This is non-strict WARN only (drift exits 0 for
t0's non-strict done-check) but would **fail t5's `drift_check --strict`** gate. Not caused by
the t0 code branch and out of t0's scope — flagged here and in the review packet so it is
tracked, not silently carried into t5.

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
- `python3 scripts/drift_check.py` (from `aetheris-agents/`) — 0 FAIL, 1 pre-existing WARN
  (milestone_status, above), 7 INFO; exit 0
