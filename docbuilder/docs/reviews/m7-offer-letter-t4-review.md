# Review — m7 t4 — round 1 (milestone close sign-off)

Reviewer: claude-ui
Subject: m7 close — command-shape learning, milestone summary, drift (commit `728d124`)

> Filed at `docbuilder/docs/reviews/` (m7 convention).

---

## Findings

**1. [non-blocking] Stale done-check snippet in the milestone doc not fixed, only noted.**
The t4 notes correctly identify that the §t4 done-check's `docbuilder/docs/runbook.md`
manifest-grep is wrong (wrong path + the file isn't manifest-tracked), but the snippet was
left in `m7-offer-letter.md`. The doc is the canonical source (§1.1) — same class as the t3
`removal is m7` fix. Correct/remove it in this commit, don't note-and-leave.
*No re-review needed for that change.*

## Cross-ticket notes

The learning entry is well-formed — four concrete instances, the "passes trivially" failure
mode (worse than a hard fail), the "before writing the command" checklist; the m5/m6/m7 source
citation correctly signals a recurring class. The milestone summary represents the arc
accurately (pre-t1 doc correction as methodology-working; t2 de-risk → t3 failure-surface
narrowing; concrete m8 open items). Drift 0 FAIL / 1 WARN is the correct expected state; the
WARN clears with the human-owned BL-002 re-upload.

t4 clean modulo the one non-blocking doc fix.

---

## Resolution (actioned)

**F1 — fixed.** Replaced the stale snippet in **both** places it appeared:
- §t4 Done-check block — the `git log … docbuilder/docs/runbook.md … manifest` snippet →
  `git diff --name-only eeb37a1 HEAD -- CLAUDE.md docs/capability-matrix.md docs/rig/runbook.md`
  (expected: `CLAUDE.md` only), with a note that `docbuilder/runbook.md` is not manifest-tracked.
- t4 prompt step 4 — reworded to "only manifest-tracked files need a row advance; m7 changed
  one (`CLAUDE.md`); the runbook is `docbuilder/runbook.md` (not `…/docs/runbook.md`) and is not
  tracked; do not pre-advance." The t4 notes updated to record the correction (not "moot").

Drift unchanged (the milestone doc is not manifest-tracked): **0 FAIL / 1 WARN** (`CLAUDE.md`,
BL-002).

## Disposition

**m7 complete. t1–t4 merged.** The offer letter renders a faithful PDF (primary) + DOCX
(secondary) from the HTML+inline-CSS Jinja2 template; live PASS `docbuilder-orch-iDGIIQ`. One
learning promoted (command-shape). **BL-002 (human-owned):** re-upload `aetheris-agents--CLAUDE.md`,
then advance its manifest row to HEAD → drift 0 FAIL / 0 WARN.
