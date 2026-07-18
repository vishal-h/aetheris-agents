# Handoff — BL-007 t2+ / design session 2026-07-18

Date: 2026-07-18 · From: claude-ui (BL-007 planning/design session) · For: fresh
claude-ui design session, same project.
Branch state at handoff (verify with git as first move — merges/pushes were held
for the human throughout, so this list may be partially landed):
aetheris-agents `bl-007-t1-prep` (superset of t0 docs) and `bl-007-t1`; harness
`bl-007-t0-caused-by` (t0 code) and `bl-007-t1` (contract + F2 docstrings).

## What this session produced (all reviewed, zero blocking findings open)

1. **Research brief** — `../aetheris/docs/aetheris/research/activegraph-log-is-agent-2026-07.md`
   (committed). Weng brief's dangling cite to `…-2026-06.md` still needs its
   one-line fix — t5's list.
2. **Milestone doc** — `docs/rig/milestones/bl-007/README.md` (renamed from
   milestone.md in t0's round; drift `milestone_status` PASS). Six tickets t0–t5.
   Per-ticket issues **waived** for BL-007 (recorded in README; #48 tracks).
3. **t0 shipped** — `caused_by` on trajectory events (harness `f80521e` + specs
   note `2ab87b5`). Trajectory-file-only: SQLite events table drops it by design
   (`store.ex:1006-1023`, DDL `:803-812`).
4. **t1 shipped** — determinism contract committed NORMATIVE at
   `../aetheris/docs/aetheris/determinism-contract.md` + three F2 docstring fixes
   (incl. a third uncited "at or before" at `fork.ex:22-23`). The `[t1-verify]`
   table caught three safety-relevant divergences in the verify claims; §3/§5
   rewritten descriptively under human approval. Full table + effect-class map:
   `docs/rig/milestones/bl-007/bl-007-t1-implementation-notes.md`.

## Decisions ratified (all 2026-07-18, on record in README/commits)

- **D1** fork guarantee: transcript prefix + seed carried; fs/clock explicitly
  fresh. **D2** CLI converges onto `Fork.from_step/3`. **D3** `caused_by` folded
  as t0 (done). **D4** lineage queries deferred → backlog at t5. **D5** checkpoint
  cadence parked. **D6** boundary at t5; issues waiver recorded.
- Verify divergences: descriptive rewrite over normative-aspiration (operator
  call) — the effect-class mechanism is backlog, not commitment.
- Verify KeyError bug: tracked today (review file + notes + t5 scope); backlog
  row at t5; standalone-ticket vs trigger-parked (trigger: first verify of an
  orb trajectory) = **human's call at the t5 boundary, still open**.

## Next work, in order

- **t2** (fresh claude-code session): seed-carry in `assemble_config/5` + CLI
  convergence + context/seed-asserting tests + `tool_result` rebuild path
  exercised. Contract §4 is normative for it; both current gaps are named there
  as defects-against-contract. Optional rider needing human ratification before
  t2 starts: rename `find_last_step_complete` (mildly false "last") — one line
  in t2's ticket text if wanted.
- **t3–t4** (Rig command + affordance): t3's done-check is still a marked
  PROMPT GAP — claude-code resolves the Rig test convention from repo state at
  t3 start and the README gets corrected then.
- **t5 boundary carries** (all already named in README t5 scope): four backlog
  entries (D4; effect-class/record-and-serve, hazard `http_call`; verify
  first-diverging-event report gap; verify KeyError crash) · manifest regen incl.
  contract + brief + README · weng cite fix · six-file project-knowledge
  reconciliation (five research briefs + rig--architecture.md, observed absent
  from project knowledge this session) · rig--current-state §C correction ·
  `b6fd983` watermark provenance note in the implementation notes (was it t0's
  fifth doc commit pre-cut? one line, so the watermark history reads true).

## Learning-promotion candidates for milestone-end (§7 ritual)

1. Done-check commands repo-qualified + existence-verified like Touches paths
   (t0; class swept across README in t1-prep/t1).
2. **Normative claims about code require a read-verification table in the
   authoring ticket's packet** (t1 — first use caught three divergences; the
   missing-citation row was the one hiding a defect — "the tell").
3. A verification pass's own output goes stale when a second pass corrects it;
   corrections chase the report into every doc that adopted it (recon
   checkpointing row).

## Standing context

Fork-vs-provenance sequencing: never explicitly ratified; BL-007 Phase 1 + two
tickets completed regardless. uc-provenance-validation remains ready, competing
only for human hours — re-surface if the human hasn't scheduled the taxonomy
session. Session hygiene unchanged: fresh claude-code session per ticket; design
reviews land here; recover specifics from repos and
`docs/reviews/bl-007-t*-review.md`, not from memory of the closed session.
