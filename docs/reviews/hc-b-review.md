# Review — hc-b — the canonical document, and the round's first edit

**This file is the round's first, per R12/R2.** Methodology §1.4 and §8 already require review
findings written verbatim to a review file in the repo; m4 committed one across a twelve-row
ticket set, which is why *"the ticket closed with zero blocking findings"* was derivable there
only as *"the row says Closed"*. Every `hc-*` ticket commits its review file so that this
round's §Close criteria clause 1 has something to read.

**Shape, for hc-c/hc-d/hc-e to follow.** One `## Round <R>` section per round, appended, never
rewritten. The reviewer's findings land **verbatim** — §1.4's *paraphrase is the lossy step* —
in §5's format (`[blocking]` / `[non-blocking]` / `[question]`, each with its contract ref and
suggested fix). claude-code appends a per-finding disposition table
(`fixed | disagree (reason) | deferred (backlog ref)`) beneath them, in a later commit than the
findings themselves. Disagreements go to the human.

---

## Round 0 — packet submitted

**Submitted at:** agents — the commit that adds this file
(`git log -1 --format=%h -- docs/reviews/hc-b-review.md`) / harness `b4d782a`. Named that way
rather than by a hash typed before it exists, which would be a claim landing in the commit that
makes it true.
**Base:** agents `8490362` / harness `288c8ef`.

**What the packet carries.** The step-1 gate G1–G5 with commands and full output; the canonical
document `docs/milestones/hc-consolidation.md`; I0's before and after verbatim with its dated
note; this file; `docs/milestones/hc-b-implementation-notes.md`; and the done-check output —
`drift_check --strict` run post-commit, `mix test` in full, and the blob-hash check.

**Findings: none yet.** This section is the packet's identity, not a verdict on it. The
reviewer's findings land here verbatim in the next commit, and the disposition table beneath
them in the one after.

> **Why this is not a claim that lands in the same commit as the thing that would make it
> true.** The rule forbids writing ✓ beside a gate that has not run. This section asserts only
> what is true when committed: that a packet was submitted, and at which two commits. It does
> not assert that the ticket closed, that findings were zero, or that the review passed — those
> are what Round 1 will carry, on the reviewer's authority and after the reviewer has read it.
> **No closure pre-authorisation is available for this ticket**: decision 6's bound permits it
> only after a round has been reviewed, naming that round's scope, and hc-a — this round's
> opening ticket — has had none.

**Three things the packet flags for the reviewer's attention**, each already recorded in the
document at the point it would have been cited:

1. **Two counts in the ticket's own text do not reproduce.** *"41 invocation sites"* (37 on the
   population this ticket could construct; the companion *"29 section blocks"* is right, two
   ways) and *"the ten carried m4 decisions"* (the enumeration yields fourteen in force). Both
   are decision 1's class and both were caught by decision 2's pre-ratification pass. Neither
   number is carried; both enumerations are printed.
2. **hc-a Part 7(a)'s table named `Done-when` and a step-1 gate as §6 obligations; §6 has
   neither.** The step-1 gate is m4 decision 3 — cycle-local practice — which is the sole basis
   R8 carries it on. Listing it as a methodology obligation would have manufactured an
   authority.
3. **The placement premise for `docs/milestones/` was refuted by its own check** and the
   corrected version is recorded in §Close criteria clause 6, attributed to the reviewer, with
   both halves — because stating half 1 alone re-installs the generalisation the check removed.
