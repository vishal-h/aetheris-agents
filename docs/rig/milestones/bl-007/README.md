# BL-007 — Fork: Rig UX + provenance/determinism contract (#48)

**Status: PARTIALLY RATIFIED** — D3 ratified 2026-07-18 (`caused_by` folds as t0; t0
implemented, in review). D1, D2, D4, D6 still awaiting ratification (they gate t1–t5, not t0).
**Size:** L · docs-first per `docs/methodology/milestone-methodology.md`.
**Drafted:** 2026-07-17, against aetheris `19c08be` / aetheris-agents `d11464f`.
Every repo-state claim herein was source-verified this cycle (BL-007 recon +
verification relay, 2026-07-17); citations name the lines read.

**Home:** `docs/rig/milestones/bl-007/README.md` (aetheris-agents — the Rig milestone
convention, cf. `docs/rig/milestones/p3/`; renamed from `milestone.md` to the
status-bearing `README.md` the drift checker expects). Harness paths below are
`../aetheris/`-qualified per the cross-repo Touches rule.

**Research basis:** `../aetheris/docs/aetheris/research/activegraph-log-is-agent-2026-07.md`
(the brief; paper arXiv:2605.21997). Referenced by section below, never restated.

---

## What this milestone is

Fork already has a working transcript-replay core in the harness
(`Aetheris.fork_run/3` → `Fork.from_step/3`, shipped 2026-05-17). BL-007 is **not**
that build. It is four things on top of it: (1) the `caused_by` lineage field the
roadmap orders before fork UX; (2) a written determinism contract that states —
honestly, per source — what a fork guarantees; (3) convergence of the CLI onto the
real replay path (Finding F1); (4) the Rig surface: one Tauri command and a "Fork
from here" affordance in TrajectoryView, plus provenance display.

## Current state

Adopt the recon report (`recon-task-not-a-iridescent-snail.md` §§1–6) verbatim as
this section's body, **with one amendment**: strike §5's incremental-checkpointing
row ("Absent — only wait-triggered today"). Superseded by the verification relay's
second pass at the same commit: per-step checkpoint writes ship today
(`../aetheris/lib/aetheris/execution/loop.ex:292` in the `:step_complete` path;
unconditional write at `../aetheris/lib/aetheris/agent/server.ex:429-443`;
`wait_condition` labels the row, it does not gate the write). Residual roadmap work
is at most a configurable cadence — **out of scope here, no forcing function**
(brief, Part 7).

Summary of the verified core (details in recon §1):

- Programmatic path rebuilds the conversation transcript to step N from recorded
  trajectory events; no prefix re-execution; fresh `fork-` run id; provenance
  (`fork_from`/`fork_step`) persisted into trajectory meta. Cost parity with
  ActiveGraph's cached-prefix fork (brief, Part 3 table).
- Transcript-only determinism: seed dropped (`fork.ex:110-122`), overlay fresh
  (`supervisor.ex:86-95`), wall-clock start (`server.ex:226`).
- CLI `--step N` is provenance-only — full re-run from original prompt (F1).
- Fork-point selection requires exact `:step_complete` match; docstrings say "at or
  before" (F2).
- Verified absent: any Rig fork surface; `fork_event_id` anywhere; `caused_by`
  anywhere; fork↔checkpoint interaction.

---

## Open decisions (ratify before t-issues are generated)

**D1 — Fork guarantee wording (gates t1, t2).**
Recommended: contract states *identical transcript prefix + seed carried; filesystem
and clock re-initialized* — i.e. adopt shipped behavior **plus** seed-carry (a small
additive change: `assemble_config/5` reads `meta["seed"]` into its base map; the CLI
path already preserves seed by struct-clone). Filesystem snapshot and virtual time
are **excluded** — genuinely new subsystems with no current consumer, listed in the
contract as explicit non-guarantees (brief, Part 2: "silence is the only wrong
option"). Alternative: document transcript-only (drop seed-carry) — weaker for one
saved line; not recommended.

**D2 — F1 disposition (gates t2, t3).**
Recommended: converge the CLI onto `Fork.from_step` — `start_fork/4` calls the real
replay path, with a test that **asserts reconstructed context**, not just status.
This is load-bearing for the Rig design: Rig's command layer spawns `mix` processes
(cf. `orchestrate.rs` pattern), so a correct CLI is the natural Rig entry point;
"deprecate `--step`" would force t3 to grow a bespoke harness entry instead.

**D3 — `caused_by` placement (gates t0).**
Recommended: fold as t0 of this milestone — only the `caused_by` field itself, not
the rest of roadmap Horizon 0 (observation convention and token-cost query stay on
the roadmap). Rationale: it is this milestone's ordered prerequisite
(`../aetheris/ROADMAP.md:48-53`), and folding keeps the sequencing visible in one
canonical doc. Reference shape: brief Part 4 / paper Listing 1 — single nullable
pointer; per-object provenance stays a payload convention.

**D4 — `fork_event_id` / lineage queries.**
Recommended: **defer**. BL-007 ships parent-link *display* (Rig reads
`fork_from`/`fork_step` from the forked run's trajectory meta — already persisted,
readable via `file.ex:90`). "List forks of run X" needs an index or a
`config_json`-deserializing scan (recon §2); with `caused_by` landing in t0, a future
lineage query should compose with general causal lineage rather than grow a parallel
fork-only mechanism (brief, Parts 3–4). Deferral gets a backlog entry, not silence.

**D5 — checkpoint cadence:** parked (recommended above; ratify by not objecting).

**D6 — doc home + export reconciliation.** Confirm the proposed home. At this
milestone's export boundary: manifest rows for this doc, the determinism contract,
and the activegraph brief; fix the weng brief's dangling cite; **and reconcile the
six files absent from project knowledge** (five research briefs +
`rig--architecture.md`) — the manifest-blind direction, observed live this session.

---

## Out of scope (named, with reasons)

Filesystem/overlay snapshot at fork point; virtual time (both: new subsystems, no
consumer — contract lists as non-guarantees). Checkpoint cadence (D5). ActiveGraph's
log-identity lineage (brief Part 3: storage redesign, no forcing function — ours is
metadata, stated as such). Frames (brief Part 3: no need; the frames-vs-forks rule is
imported as UX copy only). `fork_event_id` (D4, deferred with backlog entry).
Reactive/no-workflow coordination (brief Part 5: does not transfer).

---

## Tickets

### t0 — `caused_by` event lineage field (harness)

**Scope.** Every trajectory event gains an optional `caused_by` field (nullable
event-id pointer to the triggering event; null for user/runtime-initiated events).
Serialization round-trips it; existing trajectory files without the field load
cleanly (back-compat: absent ⇒ nil). After this ticket, new events can carry causal
lineage; nothing is yet required to set it beyond what the ticket wires (fork's
`run_started`-equivalent event should name the fork's causing context if one exists).

**Contract refs.** Brief Part 4 (reference shape; paper Listing 1). Harness rule 14
(three-place change). Specs §6.

**Touches.** `../aetheris/lib/aetheris/trajectory/event.ex` ·
`../aetheris/lib/aetheris/trajectory/file.ex` ·
`../aetheris/docs/aetheris/specs.md` (§1 Event Schema typespec + §6 Trajectory File
Format JSON — the harness-owned schema doc) · matching tests.

> **t0 specs-target adjudication (2026-07-18).** The event struct is harness-owned,
> so the normative schema statement lands in the harness specs (`§1` typespec + `§6`
> JSON), keeping the Rule-14 change in one harness commit. The original `../aetheris/docs/…
> specs §6` (ellipsis) is corrected here to the concrete path. Rig's mirror doc
> (`docs/rig/specs.md` §6, the drift-checked one) is **not** touched in t0: `caused_by`
> is a top-level field (not an event type or payload key), so it is not a drift-checked
> row, and t0 gives Rig no consumer (D4 defers lineage queries). The mirror row lands
> with t5's sync sweep (earlier only if a Rig ticket starts reading the field).

**Do not generate.** No emit-site sweep across the codebase — only the field, its
round-trip, and back-compat. Populating `caused_by` broadly is future work.

**Done-check.** (The drift step runs from `aetheris-agents/`; there is no
`drift_check.py` in the harness repo — the original single-`cd` form failed
file-not-found.)
```bash
cd ../aetheris && mix test test/aetheris/trajectory/ && mix test && mix hex.audit
cd ../aetheris-agents && python3 scripts/drift_check.py
```

**Claude-code prompt.**
> t0, BL-007. Add optional `caused_by` (nullable event-id) to the trajectory event
> struct per brief Part 4's reference shape. Rule-14 three-place change in one
> commit: event.ex + Trajectory.File map + harness specs (§1 + §6). Back-compat test:
> pre-existing trajectory file without the field loads with nil. Run the done-check;
> include output in the packet. Touch nothing outside Touches.

### t1 — Determinism contract doc + F2 semantics fix (harness)

**Scope.** A new contract doc, `../aetheris/docs/aetheris/determinism-contract.md`
(claude-ui drafts post-D1; this ticket commits and aligns code to it): what record /
replay / verify / fork each guarantee; replay policy as a **per-tool** property
(effectful ⇒ record-and-serve; brief Part 2); fork guarantee per D1; the brief's
Part 3 divergence table included so ActiveGraph's guarantees are never cited as ours.
F2 resolved in the same ticket: exact-`:step_complete` match is the intended
semantic (Rig offers fork only on completed steps); docstrings at `fork.ex:15-16`
and `aetheris.ex:64-69` corrected to match code.

**Contract refs.** Brief Parts 2–3. D1 as ratified. Recon §1c.

**Touches.** `../aetheris/docs/aetheris/determinism-contract.md` (new) ·
`../aetheris/lib/aetheris/execution/fork.ex` (docstring only) ·
`../aetheris/lib/aetheris.ex` (docstring only) · manifest row at boundary.

**Do not generate.** No behavior changes in this ticket — docstrings only. Seed-carry
is t2.

**Done-check.**
```bash
cd ../aetheris && mix test && mix hex.audit
cd ../aetheris-agents && python3 scripts/drift_check.py
```

### t2 — Fork core alignment: seed-carry + CLI convergence (harness)

**Scope.** Per D1: `assemble_config/5` carries `meta["seed"]` into the fork config
(overridable). Per D2: `CLI.Commands.Fork.start_fork/4` routes through
`Fork.from_step/3`; `--step N` now actually replays to step N. Tests assert the
reconstructed context (message list content at the fork point) and seed equality —
closing the recon §4 gap where the CLI test inspected only status/run_id. Exercise
the `tool_result` rebuild path (`fork.ex:99-103`, currently never tested).

**Contract refs.** Determinism contract (t1) — normative for what must carry.
Recon §1a/§1b, F1.

**Touches.** `../aetheris/lib/aetheris/execution/fork.ex` ·
`../aetheris/lib/aetheris/cli/commands/fork.ex` ·
`../aetheris/test/aetheris/execution/fork_test.exs` ·
`../aetheris/test/aetheris/cli/commands/fork_test.exs`.

**Do not generate.** No fs/time carry. No changes to `loop.ex` consumption.

**Done-check.**
```bash
cd ../aetheris && mix test test/aetheris/execution/fork_test.exs \
  test/aetheris/cli/commands/fork_test.exs && mix test && mix hex.audit
cd ../aetheris-agents && python3 scripts/drift_check.py
```

### t3 — Rig Tauri command: fork a run (rig/src-tauri)

**Scope.** One Tauri command, `fork_run(run_id, step, label?)`, spawning the (now
correct, post-t2) CLI `mix aetheris fork <trajectory> --step N`, following the
`orchestrate.rs` spawn pattern; resolves the trajectory path from the run id;
returns the new run id / error. Specs §4 command entry in the same commit.

**Contract refs.** t2's CLI behavior. `docs/rig/specs.md` §4 (command table
conventions). Determinism contract (what the command may claim in its docs).

**Touches.** `rig/src-tauri/src/commands/` (new or extended file per Rig module
conventions) · `rig/src-tauri/src/lib.rs` (registration) · `docs/rig/specs.md` §4.

**Do not generate.** No UI in this ticket. No direct harness-DB writes — Rig stays
read-only on SQLite; the fork happens through the spawned process.

**Done-check.** `cargo build` + the Rig test convention for commands —
**[PROMPT GAP: claude-code confirms the exact test command from `rig/CLAUDE.md` /
repo state and records it in the implementation notes; an unverifiable done-check
is a prompt defect to be corrected in the doc before t3 starts.]**

### t4 — TrajectoryView: "Fork from here" + provenance display (rig/src)

**Scope.** A "Fork from here" affordance on step groups in `TrajectoryView.tsx`,
**offered only on steps with a `:step_complete` event** (t1's semantics); invokes
t3's command; surfaces the new run. A provenance banner on forked runs ("Forked from
&lt;run&gt; @ step N") read from trajectory meta. UX copy basis: the frames-vs-forks
decision rule (brief Part 3) — the affordance explains that a fork is a durable,
independently-inspectable branch. Sits on BL-005's reconstruction path in
TrajectoryView (per handoff).

**Contract refs.** t3's command contract. Determinism contract (banner wording must
not overclaim — transcript+seed, fresh environment). `rig/CLAUDE.md` UI conventions.

**Touches.** `rig/src/components/modules/harness/TrajectoryView.tsx` ·
`rig/src/components/modules/harness/shared.tsx` (if shared UI needed) ·
`docs/rig/specs.md` (if UI-visible state shapes change).

**Do not generate.** No fork-list/lineage-tree view (D4 deferred). No RunList
changes beyond what surfacing the new run requires.

**Done-check.** Rig test convention per t3's resolution + manual sprint-style check:
fork a completed run from the UI, confirm the child run appears with the banner and
its transcript prefix matches to step N.

### t5 — Docs sync + boundary (cross-repo)

**Scope.** Runbook entries (harness runbook: fork CLI semantics change; Rig runbook:
the affordance) — per the runbook-update rule these land with t2/t4 where
operator-visible, this ticket sweeps for completeness, it does not recover.
`architecture.md` fork section refreshed. `rig--current-state-2026-06.md` §C
corrected (its "no fork API" text predates the discovery). Backlog entry for D4's
deferral. Export boundary per D6: manifest regen including this doc, the contract,
the brief; weng cite fix; six-file project-knowledge reconciliation.

**Contract refs.** Mirror-vs-record convention (runbook header). Manifest header
discipline. D6.

**Touches.** `../aetheris/docs/aetheris/runbook.md` ·
`../aetheris/docs/aetheris/architecture.md` · `docs/rig/runbook.md` ·
`docs/rig/current-state-2026-06.md` · `docs/backlog-2026-06.md` ·
`docs/project-knowledge-manifest.md` ·
`../aetheris/docs/aetheris/research/weng-harness-2026-07.md` (one-line cite fix).

**Done-check.**
```bash
# run from aetheris-agents/ (drift_check.py lives here, not in the harness)
python3 scripts/drift_check.py --strict   # exit 0 at the closeout export
```

---

## Sequencing

t0 → t1 → t2 → t3 → t4 → t5. t0 is the roadmap-ordered prerequisite; t1 before t2
because the contract is normative for what t2 carries; t2 before t3 because the Rig
command rides the fixed CLI. Fresh claude-code session per ticket; full restart
after any CLAUDE.md change. Pushes held for the human; every gate at every boundary.

## Done

All tickets pass done-checks; zero blocking findings across
`docs/reviews/bl-007-t*-review.md`; drift check zero FAIL at the boundary export;
learning promotion per methodology §7 (candidate already visible: the
stale-recon-row class — a verification pass's own output goes stale the moment a
second pass corrects it; corrections must chase the report into every doc that
adopted it).
