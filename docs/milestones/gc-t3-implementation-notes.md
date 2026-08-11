# gc t3 — the correction sweep and the deferred rows (implementation notes)

`Record of gc t3, run 2026-08-12. Round document: docs/milestones/gc-stale-claims.md §t3, which is
the authority for what this ticket did. The diffs are in the commit; this file carries the
per-destination shape determinations and their evidence, the decisions, the deviations, and what is
owed.`

---

## The three shape determinations, established before any edit

The ticket named three kinds and one lead per kind, every lead to be verified rather than followed.
All three were verified; **one lead was confirmed and it is the one that could have held half the
ticket.**

### Q1 — live operational guidance → hc decision 8, corrected in place

Verified at `docs/milestones/hc-consolidation.md:585`:

```
| 8 | Live operational guidance is corrected in place | **carries** |
```

**And the destination's own established practice agrees**, which decides the *form* the decision
leaves open. `cloudcost/runbook.md:623–625` already carries a correction in exactly this shape — an
in-place rewrite with a dated parenthetical quoting the superseded wording:

> *"**BL-070's cross-provider deletions are not taken** *(corrected m5 t2, 2026-08-10 — this
> sentence read "and **BL-070**, which retires the now-unreachable cross-provider merge code in
> `compose_report_data.py`")*."*

So: in place, with a dated note quoting what it replaced. Not silent — a silent correction to a
gating instruction loses the reason a reader most needs.

### Q2 — do hc's decisions bind harness-side files? **Yes. The harness half was not held.**

This was the determination that could have stopped a third of arm 1. Five independent legs, none of
them the lead the ticket offered:

```
1  hc-consolidation.md:21 — "**Repos:** `aetheris-agents` and `aetheris` (harness)". The round
   declares both repos in its own header.
2  hc's subject WAS the harness: BL-105 + BL-106 (the `--json` contract) and BL-077 (the sprint's
   exit contract) are harness surfaces.
3  hc's tickets committed to the harness NINE times — e8889c3, 1b09b23 (hc-c); 2d76a65, 5782cbb,
   2ebc59c, 48f59e7 (hc-d); 02db6bb, 712d434, 2ef0517 (hc-e).
4  hc-c's own record tabulates harness paths in its scope tables — ../aetheris/scripts/sprint.sh,
   ../aetheris/lib/aetheris/cli/commands/run_helpers.ex, four ../aetheris/test/... files.
5  Decision 6 itself — "a cross-citing repo pair lands together, **harness first**" — is
   unintelligible unless the decisions reach harness files. A decision about the order in which
   two repos land cannot be agents-only.
```

Leg 5 is the strongest and is structural rather than evidential: the decision set contains a
decision *about* harness landings, so it cannot be a decision set that stops at the agents boundary.

**The lead the ticket offered — that hc's own tickets edited harness files — is leg 3, and it is
confirmed.** It was offered as *"bears on the question but does not settle it"*; that reading is
right, and legs 1 and 5 are what settle it.

### Q3 — the closed round document → hc decision 7, dated superseding block

`cloudcost/m5-n1-compose.md` closed 2026-08-10. Decision 7, verified at
`docs/milestones/hc-consolidation.md:584`:

```
| 7 | A closed record gets a dated superseded note; original text not rewritten | **carries** |
```

**The lead's "third case" was read and does not apply here.** m5 itself distinguishes the two
decisions at `cloudcost/m5-n1-compose.md:503–510`, where a paragraph was corrected **in place under
decision 8** because *"This paragraph is neither: it tells a reader what this section contains, so
leaving it would leave a wrong instruction standing as the primary text."* That test is *does the
unit instruct a current reader*. None of t3's three m5 destinations does:

```
:30    a §Sequence line — a record of what m5 sequenced, not an instruction
:1226  a §Milestone summary closing line — the same
:852   an [OPEN] §Not established item body — a record of an open question
```

So all three take decision 7. **And for the third, §Close criteria clause 3 is explicit and
governs:** *"its `[OPEN]` prefix is not flipped, m5 being a closed round."* The block appended to
item 1 is a dated record beside it; the prefix and the item's text are byte-unchanged.

---

## Arm 1 — the six corrections

```
1  cloudcost/runbook.md              decision 8, in place + dated note        BL-074 (2026-08-07)
2  ../aetheris/ROADMAP.md  Horizon 0 decision 8, in place + dated note        BL-007 (2026-07-20)
3  ../aetheris/ROADMAP.md  E4        decision 8, in place + dated note        BL-003 (2026-07-15)
   — BOTH halves: the stale gate clause AND the "(already Active)" parenthetical
4  cloudcost/m5-n1-compose.md:30     decision 7, dated superseding block      BL-132 (2026-08-11)
5  cloudcost/m5-n1-compose.md:1226   decision 7, dated superseding block      BL-132 (2026-08-11)
6  cloudcost/m5-n1-compose.md:852    decision 7, dated block, prefix UNTOUCHED BL-074; BL-105+106
```

Every unit was quoted at HEAD before replacement, per methodology §11's *A surgical edit is scoped
by unit and quoted before it is replaced* — the entry whose reverse pointer t2 landed.

**Destination 1 changed more than the stale clause, and the reason is recorded.** The sentence sent
an adapter author to BL-074 *"for any remaining value, threshold or spelling a provider could differ
on"*. Deleting the pointer would leave the author with nothing; BL-074's output is the 54-item
census and `cloudcost/milestone.md` §Contracts. The correction **repoints rather than removes** —
read §Contracts, not the row — because the reader's need survived the row's closure.

**Destination 3 is the one the round exists to close.** Its parenthetical *"(already Active)"* and
its clause *"E-cluster is not done until BL-003 is"* were stale **together**, and correcting one
would have left the other. The ticket named this explicitly; both are corrected.

**Destination 6 records what the item got right, not only that it is discharged.** m5 §Not
established item 1 observed that two documents stated non-identical gates and neither superseded the
other — a true and useful observation. What the `gc` round adds is that the disagreement is an
**equivocation on *live*** (D2) rather than a contradiction, and that all three named gates are now
closed, so it no longer selects between live conditions. The block says both.

---

## Arm 2 — the five rows

**BL-145 – BL-149**, filed at `docs/backlog-2026-06.md:8526`, `:8569`, `:8606`, `:8645`, `:8687`.

```
BL-145  the backlog's two disagreeing status surfaces          (t1 §X.1 item 5)
BL-146  a status marker that quotes another row's disposition  (t1 §X.1 item 6)
BL-147  a stamp's absence encoding three dispositions          (t1 addendum A; D5)
BL-148  C7 and C13's obligations with no exemplar              (t1 addendum B)
BL-149  the two senses of "live"                               (t1 §X.1 item 3; D2)
```

**The convention was read from neighbouring rows, not imported.** BL-144 was read in full as the
nearest and most recent instance; the shape taken from it is: heading as a lowercase statement of
the problem with `(#TBD)`; a `**Kind:** … · **Census items:** … · **Contract:** …` line; `**Size:**`
and `**Priority:**`; `**Section:**`; a *filed at* line with *this row poses the question; it does not
settle it*; `**What happened.**`; `**Why the existing rules do not cover it.**`; a bolded
`**Determine …**`; `**Done when:**`; `**Costs:**`; and a backtick `Source:` block. All five follow it.

**No row states a fix.** Each ends at a `Determine …` and a `Done when:` that admits *"or declined
with the reason recorded"* — the shape BL-144 uses. **BL-145** does not say which status surface to
keep; **BL-147** does not say to add six stamps; **BL-149** does not say which sense of *live* to
retire.

**No row carries a closure marker**, verified after filing — the agents-side rule that a finding
recorded inside a row the same commit closes has a record and not an executor.

---

## Deviations, with reasons

**Two claims inside the round document had gone stale while this ticket ran, and were corrected in
the same commit.** §Carried in item 3's bracket said *"this round has produced no implementation-notes
file and no review file"* — true when written at Phase C, false from Phase D. And the `**Status:**`
line said *"t3 authored, not opened"*. Both are the round's own subject appearing inside the round's
own document; leaving either would have been a stale claim in the artifact convened to remove stale
claims. Corrected with a dated block and in place respectively.

**The t1 and t2 ticket-set rows pointed at review packets rather than committed records.** They read
*"Record: the t1 review packet"* — a scratchpad artifact — while committed records now exist.
Repointed at `docs/milestones/gc-t{1,2}-implementation-notes.md` and `docs/reviews/gc-t{1,2}-review.md`.
Outside `Touches` as written; taken because R19 already had this session in that table and a pointer
to an uncommitted file is the defect class this ticket is closing.

---

## What is owed

```
OWED  A review file for this ticket — docs/reviews/gc-t3-review.md. NOT claude-code's to author:
      methodology §10 assigns review files to claude-ui, saved verbatim by the human.
OWED  The close. §Close criteria's seven clauses; clause 5 is `mix dialyzer` per D1, clause 7 is
      §7's ritual with the candidate-comparison §Carried in item 4 imports. Not authored here.
OPEN  BL-145 – BL-149, all five, by construction.
OPEN  D6's write-back question — whether decision 10's interpretation belongs in hc's own document.
```

## Anchors

```
the ticket        docs/milestones/gc-stale-claims.md §t3
decision 7 / 8    docs/milestones/hc-consolidation.md:584, :585
hc's reach        docs/milestones/hc-consolidation.md:21 (Repos), :583 (decision 6)
m5's third case   cloudcost/m5-n1-compose.md:503–510
clause 3          docs/milestones/gc-stale-claims.md §Close criteria
quote-then-replace ../aetheris/docs/methodology/milestone-methodology.md §11
row convention    docs/backlog-2026-06.md §BL-144
```
