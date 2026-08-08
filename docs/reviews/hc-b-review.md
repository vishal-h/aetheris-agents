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

---

## Round 1 — closing round

**Reviewed:** agents `e8cd5cd` / harness `b4d782a`. **Round scope named by the reviewer:** items
1–2 only.

**Closure pre-authorised, and the bound is satisfied.** Decision 6 as amended at m4 close-b
permits pre-authorisation *only after a round has been reviewed, naming that round's scope, and
never in an opening ticket*. hc-a was this round's opening ticket, r0 has been reviewed, and this
round's scope is named — so: *"if r1 contains only items 1–2 and its done-check is clean, hc-b is
closed on that commit."* Recorded here because the authorisation is the row's truth-maker; the
commit is not predicting its own review. **The cost decision 6 states applies:** this round's own
changes ship unreviewed by design.

### Findings, verbatim

> **Item 1 — "thirteen unchanged" includes a decision that was amended**
>
> §3b's correction of my *"ten"* reads: **Fourteen in force — thirteen unchanged (1–12, 14) plus
> one amended (15)**.
>
> **Decision 6 is in `1–12`, and it was amended at close-b** — hc-a's own Part 7(e) table names
> it *"6 (as amended close-b)"*, and the amendment is the closure-pre-authorisation permission
> this very round is operating under. So the predicate *unchanged* is false for one member of its
> enumeration.
>
> The **count is right**: fourteen in force, sixteen accounted for. Only the sub-clause's
> predicate fails, which is carrier 2 in the smaller register — and it sits inside the paragraph
> correcting my count, which is why it is worth one round rather than a note.
>
> **Do:** re-derive the split and restate it so the predicate holds over its members — *twelve
> unchanged, two amended (6, 15)* is the shape I expect, but **derive it rather than taking it
> from here**, and print the members beside each figure so the two can disagree.
>
> **Check whether the phrasing landed in the canonical document or only in the packet**, and say
> which. If only the packet, record the correction anyway where the fourteen is stated in the
> document.

> **Item 2 — the rewritten clause 2 must not read as a finding against m4**
>
> §3e is careful — *"a sweep looking for a heading inside a row finds nothing and reports clean"*
> is conditional, not a claim about m4's run. **The document should be equally careful**, because
> clause 2's rewrite will be read as a defect discovered after the fact.
>
> **m4's own sweep read the stored shape correctly.** close-c's clause 2 returned
> `BL-107:DONE BL-121:DONE BL-127:DONE` against 23 open, and its clause 1 direction 2 matched
> nine rows by their actual `**DONE` text. The execution was sound.
>
> **Do:** where the rewritten clause records its reason, state that **the defect is in the
> clause's wording and not in m4's execution** — the clause described the record as it is spoken
> of rather than as it is stored, and m4's implementer happened to sweep the stored shape. A
> criterion that works only because its implementer ignored its wording is worth recording as
> exactly that, and no more.
>
> Same treatment for `## Suggested order` as the second status surface: name it as a surface that
> must agree, not as one found disagreeing, unless it was.

### Dispositions

| Finding | Disposition |
|---|---|
| **Item 1** | **fixed.** Split re-derived from the **date cell** of each of the sixteen rows — the field that records an amendment — and the reviewer's expected shape confirmed: **twelve unchanged (1–5, 7–12, 14), two amended (6, 15)**. Members printed beside every figure, as a derivation block. The two amendments are distinguished by kind: 6 was amended *before* this round (m4 close-b) and carries in amended form; 15 is amended *by* this round (R11). **The phrasing was in the canonical document, not only the packet** — `hc-consolidation.md` §Ratified decisions and `hc-b-implementation-notes.md` §4; corrected in place in both with the superseded wording quoted, per decision 7. The review file's own line said only *"fourteen in force"* and needed no change. Nothing else moved |
| **Item 2** | **fixed, and further than asked — the finding understated it in the direction that favoured me.** See below |

**Item 2, extended.** Checking m4's execution before restating it turned up that the **r0 claim
itself was wrong**, not merely uncharitable. `docs/backlog-2026-06.md` records closure in **two**
shapes: an in-row `**DONE <date> (<ticket>).**` paragraph (**9**, every one m4-cycle-dated) and an
older sibling `### BL-0NN — DONE <date> …` heading (**15 headings covering 17 rows**, dated
2026-07-23 to 2026-08-05, not exclusive — BL-069 carries both).

**All three rows m4's clause 2 swept — BL-107, BL-121, BL-127 — use the in-row shape**, which is
precisely what *"a DONE section"* describes. So there was **no wording defect**, and the finding's
own framing — *"a criterion that works only because its implementer ignored its wording"* — does
not apply either: m4's clause named the shape its own population uses and its implementer read it
straight. What is true is only that a second, older shape exists that no m4-cycle row uses. Clause
2 is therefore **widened, not corrected**, and the r0 claim is retracted in place in both files.

The r0 error's class is the one this ticket promoted: an observation over one subset stated as a
claim about the class. **Third instance in this document's lineage, and the first that is the
author's rather than the reviewer's.**

### Two checkable specifics in the finding text, reconciled rather than disputed

Both verify once their population is named, and neither changes the finding.

- ***"against 23 open"*** — m4's clause 2 as finally derived reads **30 filed, 3 closed, 27
  open**. 23 is correct over the clause's **first** run, whose population read 26 (26 − 3 = 23);
  r1 restated it to 28 and r2 to 30. A count correct over one set, cited against another — the
  same carrier, in the finding that raises it.
- ***"matched nine rows by their actual `**DONE` text"*** — m4's clause 1 verdict says **eight**.
  Nine is right **today**: the ninth is BL-069's in-row paragraph, written at close-c *after*
  clause 1's verdict. Both correct at their own moment.

`Source: hc-b r1, 2026-08-08 — both closure shapes enumerated against docs/backlog-2026-06.md at
agents e8cd5cd; m4's clause 1 and clause 2 verdicts read out of cloudcost/m4-consolidation.md
§The close §1; the decision date cells read out of §Ratified decisions.`
