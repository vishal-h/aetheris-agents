# Handoff — BL-007 closed / next design session — 2026-07-20

Date: 2026-07-20 · From: claude-ui (BL-007 t2→t5 design session, opened from
handoff-bl007-t2-design-2026-07-18) · For: fresh claude-ui design session, same
project.

Watermark at handoff: agents `main` (Phase B merged; last relayed pre-Phase-B
HEAD `675a5c2`), harness `main` (`7e77951`). Verify with git as first move —
Phase B's final HEADs were committed after the last relay to the closing
session. Project knowledge uploaded 2026-07-20 (full 24-file bundle,
remove-all/upload-all; manifest is the checkable invariant) and spot-verified.

## State: BL-007 is CLOSED

All six tickets (t0–t5) merged to main in both repos, zero blocking findings,
milestone summary RATIFIED 2026-07-20 (bl-007/README.md bottom), §7 ritual
complete, Phase B export done, project knowledge reconciled. Feature branches
deleted. Issues were waived (epic #48); BL-024–BL-033 carry (#TBD) — issue
backfill is optional post-milestone housekeeping (grep "#TBD" in the backlog).

What shipped, one line: fork end to end — `caused_by` field (t0), determinism
contract NORMATIVE at `../aetheris/docs/aetheris/determinism-contract.md` (t1),
seed-carry + CLI convergence on `Fork.from_step/3` (t2), `fork_run` Tauri
command (t3), "Fork from here" + provenance banner (t4), docs/boundary (t5).
Plus two defects fixed on the way: harness store `:busy` crash (`059c92e`) and
a StrictMode-dead mount guard (t4's actual GUI hang cause, six review rounds).

## Facts the next session must not relearn

- A fork is provenance-carried (`meta.fork_from`), never mode-carried; forks
  run in `:record`. `:fork` stays in the mode union, vestigial → BL-033.
- Only tool-call steps are forkable; a terminal text step emits `run_complete`,
  never `step_complete`.
- Two fork-provenance shapes coexist in the store: `Fork.from_step` writes
  integer `fork_step`; older `replay-source-*`/`verify-*` write null (540/1201).
  Null-`fork_step` banner render is verified-by-code only — its e2e rides
  whichever ticket makes file-only runs listable (trigger in BL-024).
- `fork_run` blocks to completion (BL-030 is the early-return path); `await_run`
  is unbounded (BL-031); WAL is opportunistic-only under Rig's read handle
  (BL-032).
- The fork CLI accepts bare run ids as well as trajectory paths; its "expected
  a path" error fires only on a missing positional (runbook documents this).

## Standing rules that changed (both repos' CLAUDE.md + methodology)

Seven promotions under "Learning — BL-007" in aetheris-agents/CLAUDE.md
(packet-inline rewrite; gate-before-action; deferred→backlog-row; N+1-doc-carry;
correction-chasing incl. citation decay; one-symptom-several-mechanisms with a
ratified bar exception; promotion-wording-as-review-file-artifact). P8(c) lines
in BOTH CLAUDE.mds: cross-repo sessions read both repos' learning sections at
start — that includes you. Methodology §6 gained the changed-semantics runbook
trigger; §7 gained the sweep-input clause. Read these before drafting anything.

## Open decisions / dispositions on record

- BL-026/BL-027 (verify robustness): PARKED ON TRIGGER (first verify of a
  multi-agent/orb trajectory), human-ratified 2026-07-19. Not ready work.
- BL-033 (`:fork` union removal): ratified no-code-change-now; architecture.md
  footnote documents the discrepancy.
- Fork-of-a-fork semantics: representable, unexercised (summary open Q4).
- uc-provenance-validation: still ready, still competing only for human hours —
  carried unresolved from the previous handoff; re-surface if the taxonomy
  session remains unscheduled.

## Next work candidates (no commitment made)

Backlog Suggested order rows 12–19: BL-029 (label read, batch with BL-004) →
BL-028 (silent-empty tool_result) → BL-031 → BL-025 (the one carry with
blast radius outside the repo) → BL-030 → BL-032 → BL-033 → BL-024. Or
BL-008 (self-improvement loop; research basis: weng brief + activegraph brief,
both in project knowledge). Milestone-sized work is docs-first per methodology.

## Session hygiene (unchanged, plus one)

Fresh claude-code session per ticket; full restart after any CLAUDE.md change;
pushes held for the human; every gate at every boundary; recover specifics from
repos and docs/reviews/bl-007-t*-review.md, not from memory of this closed
session. New: your §7 promotion drafts land in docs/reviews/ as files before
any promotion commit — the transport rule was minted on this boundary's own
double failure.
