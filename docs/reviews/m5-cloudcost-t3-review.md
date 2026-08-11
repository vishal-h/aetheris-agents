# Review — m5-cloudcost t3

**Name derived, not chosen.** `docs/reviews/` runs `m{N}-cloudcost-t{N}-review.md` —
`m1-cloudcost-t2-review.md` through `m1-cloudcost-t5`, `m2-cloudcost-t1..t4`,
`m3-cloudcost-t1..t3`, and this round's `m5-cloudcost-t1-review.md` and
`m5-cloudcost-t2-review.md`. This ticket is m5 t3, so the file is
`docs/reviews/m5-cloudcost-t3-review.md`. (The directory also holds four
non-`t{N}` files — two §7 promotion records, a closeout, and an export-boundary packet —
which are a different artifact kind and do not bear on the convention.)

**Format** is `../aetheris/docs/methodology/milestone-methodology.md` §5 → *Review file format
(claude-ui → claude-code)*, in the shape `m5-cloudcost-t1-review.md` established for this round:
one `## Round <R>` section, appended, never rewritten; reviewer findings verbatim; claude-code's
disposition beneath them. Committed per methodology §1 principle 4 and §8, both unscoped — **not**
per R2, whose own text binds *"every `hc-*` ticket"*. That correction was established at t1 r1 and
is not re-derived here.

**Adaptations to the §5 format**, all inherited from this round's t1 and t2 files rather than
invented here: the round lives in a `## Round <R>` section rather than in the H1; the findings are
**not** re-tagged `[blocking]`/`[non-blocking]`/`[question]`, the reviewer's text carrying
`APPROVE` and its own `F1` label and no tags; and there is no `## Cross-ticket notes` section
because the reviewer's text carried none. The *"Not findings, recorded because they were done
right"* block is the reviewer's and stays **inside** the verbatim block under its own heading,
with nothing written beneath its six items.

**One divergence between this round's own two files, named rather than silently resolved.** t1's
section is headed *"Round 0 — the review of r0"* and t2's *"Round 1 — the review of r0"* — the
first numbers the section by the round **reviewed**, the second by the round **doing the
reviewing**. They cannot both be the convention. This file follows **t2**, the later precedent and
the one whose numbering matches the round that writes the section; t1's heading is not restated
here and is not a defect worth a correction commit.

---

## Round 1 — the review of r0 (`d0fb25a` agents, `0ed9068` harness)

### Findings, verbatim

**Verdict: APPROVE, with one finding.** The six clauses ran, each reporting its result
whether or not it produced an edit, and the two that could most easily have passed for the
wrong reason did not.

**F1 — the closed-row finding deserves a clause on an existing rule, not a candidate and
not a summary paragraph.** §Milestone summary records *a finding recorded inside a closed
row is a record, not an executor* and declines to promote it because it is the
deferred-finding rule's failure mode. That is right about what it is and wrong about what
follows. **A named failure mode is often exactly what makes a rule work**, and this one is
not derivable from the parent: t2 r0 satisfied the parent in letter, by recording the
residue inside BL-070, and defeated it in substance because the same commit closed BL-070.
Someone applying the parent correctly can repeat it. The fix costs one clause on the entry
that already exists and never engages §7's bar, because it is a precision rather than a
rule. **The other declined practice stays declined** — *a ticket's scoping is authoritative
over a ticket's judgement* is already carried by §6's `Touches` field in its own words, and
a learning section that restates methodology fields becomes a second copy of the
methodology.

**Not findings, recorded because they were done right.**

- **Clause 3's arm (iii).** A zero derived from the printed prefix enumeration rather than
  from a search that found nothing — at the one arm of four that could have passed for the
  wrong reason, and named as that arm before it was run. The round's first promoted entry,
  applied to the close's own check.
- **The drift checker's pre/post pair.** Two WARN before the commit and four after, because
  check 8 reads committed history and structurally could not see this round's own edits
  before they were committed. Publishing only the pre-commit run would have been a green
  over a gap the run could not see.
- **The drift transcript's provenance block.** A hash from a since-amended commit, sitting
  beside output no run had produced, caught before publication and replaced by a fresh run
  at a clean tree — the packet rule this round promoted, applied against the packet that
  promotes it.
- **Deriving the harness gate set from the CI contract** rather than from the reviewer's
  three-command list, and reporting the greens as **gate liveness** rather than as
  validation of a change that was never in the gates' territory.
- **Clause 4's handling of t1's row.** *Differs* but has not *moved*, so the gate does not
  stop and the clause takes it — the tense distinction added after t1's own gate was
  ambiguous, earning its place one ticket later, on t1's own row.
- **BL-137's count with its enumeration**, correcting a figure the session had itself taken
  as ten. A ratio with one side unstated is not checkable, and it said so.

### Dispositions

#### F1 — accepted; landed as one clause on the parent, and the parent is in one repo, not two

**The finding's diagnosis is what makes the fix the right size.** *"Not derivable from the
parent"* is the load-bearing claim, and it is checkable rather than rhetorical: the parent says
*where* a deferred finding goes (a backlog row, not prose), and says nothing about the row's own
state. t2 r0 chose a row, wrote the residue into it, and closed that row in the same commit — a
sequence in which every instruction the parent gives was followed. **A rule whose correct
application still produces the failure needs the failure named in it**, which is what a clause
does and what a second entry would not do better.

**What landed.** One clause appended to the claim at agents `CLAUDE.md` §Learning — BL-007, in
the entry's own voice, and the existing `Source:` **extended rather than joined by a second**:

> **And the row must be one that stays open: a finding recorded inside a row the same commit
> closes has a record, not an executor.** That satisfies the rule in letter and defeats it in
> substance, and the defeat is invisible precisely because the row it lives in is the row being
> closed — so name the row you are putting it in, and if that row is being disposed in this
> commit, file a new one.

The `Source:` now reads `BL-007 t1, t2, t3;` followed by the m5 instance, **named as one
instance and as a precision on the parent rather than as a rule of its own** — the honest count,
and the reason it does not engage §7's bar stated in the line itself.

**Where the insertion falls, per §Carried in's first rule.** Entirely **inside** the unit the
claim and its `Source:` form. The unit above is *No action past a gate until that gate has run
and its result is on the record*, complete with its own `Source:` line (`BL-007 t2, t4 (×2); b1
post-push correction`); the unit below is *Decisions that constrain ticket N+1 land in N+1's
README section before its session starts*, complete with its own (`BL-007 t2, t3, t4`). **Both
are asserted to be complete claim+`Source:` pairs and both are byte-unchanged.** No claim was
separated from its attribution, and no new `Source:` line was introduced that a later insertion
could be misread against — the file's line count across this edit is unchanged, two lines
modified in place.

**One correction to the finding's premise, reported rather than smoothed. The parent rule lives
in the agents `CLAUDE.md` only — not in both repos.** `grep -n "deferred finding"` returns one
hit agents-side and **zero** harness-side; control, `grep -c "backlog row"` → agents 1, harness
**0**, so the harness zero is absence and not a broken search. This matters twice. It confirms
G1(a)'s stop condition was **not** met — the parent is in a `CLAUDE.md` t3 already touches, so
the clause landed without a `Touches` question. And it falsifies a claim in this round's own t2
review file, which describes it as *"The standing rule in both repos"*
(`docs/reviews/m5-cloudcost-t2-review.md` §*F1 — accepted*). **Not corrected here**: that file is
a committed, pushed review record of a closed round, and this round's own promoted entry says a
ratified artifact is superseded with a dated block rather than edited. Recorded so the next
reader of that sentence knows.

> `[Corrected by pointer 2026-08-11 at the m5 record-correction edit. **The promoted entry did
> not put that edit out of bounds** — it sorts artifacts by kind and governs *how* each is
> corrected, never *whether*; publication withdraws the licence to correct **silently**, not
> the licence to correct, and a review file is a **record**. **Declining was still right**, on
> the ground the sentence above also gives: the file is not in t3's `Touches`. Only the
> rule-reading half is withdrawn. Full correction, with the entry quoted verbatim, at
> `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → *The one claim that does not hold* —
> the first of this misreading's three occurrences.]`

**§6's `Touches` field carries the declined practice, verified rather than accepted.** The
finding's ground for keeping *a ticket's scoping is authoritative over a ticket's judgement*
unpromoted is that §6 already says it. It does, in two places:
`../aetheris/docs/methodology/milestone-methodology.md` §6 → **Touches** — *"files/dirs expected
to change. Anything outside this list needs a note in the implementation notes"* — and §9's
failure-mode table, which is nearly the literal form: *"claude-code 'improves' something outside
`Touches` | Unreviewed scope creep; violates do-not-generate discipline | §6"*. The decline
stands on a checked premise.

**§Milestone summary corrected in the same commit.** Its *Open for the next cycle* paragraph
said *"Neither is promoted here"*, which this disposition makes false for one of the two. Left
uncorrected it would be this round's own recurring shape a fourth time — a correction landing in
one artifact while the same claim survives in another. `cloudcost/m5-n1-compose.md` is in t3's
`Touches` and §Milestone summary is a named sub-target of it, so this is inside the ticket's
scoping rather than an extension of it.

**The six non-findings are read and carried; none asks for work and none is re-litigated here.**

`Round 1 dispositions written at t3 r1, 2026-08-10, against agents d0fb25a and harness 0ed9068.
Full record: cloudcost/docs/m5-t3-implementation-notes.md §r1.`
