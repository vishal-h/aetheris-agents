# Review — m5-cloudcost t2

**Name derived, not chosen.** `docs/reviews/` runs `m{N}-cloudcost-t{N}-review.md` —
`m2-cloudcost-t1-review.md` through `m2-cloudcost-t4-review.md`, `m3-cloudcost-t1..t3`, and
`m5-cloudcost-t1-review.md`. This ticket is m5 t2, so the file is
`docs/reviews/m5-cloudcost-t2-review.md`.

**Format** is `../aetheris/docs/methodology/milestone-methodology.md` §5 → *Review file format
(claude-ui → claude-code)*, in the shape `m5-cloudcost-t1-review.md` established for this round:
one `## Round <R>` section, appended, never rewritten; reviewer findings verbatim; claude-code's
disposition beneath them. Committed per methodology §1 principle 4 and §8, both unscoped — **not**
per R2, whose own text binds *"every `hc-*` ticket"* and so does not literally reach this round.
That correction was established at t1 r1 and is not re-derived here.

**Adaptations to the §5 format, named rather than left to be noticed.** Three, all inherited from
this round's t1 file rather than invented here:

- The round lives in a `## Round <R>` section rather than in the H1, so later rounds append to one
  file — `hc-*` practice, against the `bl-047`/`bl-049` alternative of a second `-r1` file.
- The findings are **not** re-tagged `[blocking]`/`[non-blocking]`/`[question]`. The reviewer's
  text carries `APPROVE` and its own `F1` label and no tags; adding them would be authoring.
- There is no `## Cross-ticket notes` section, because the reviewer's text carried none. Stated
  rather than filled.

**One adaptation that is this file's own.** The reviewer's *"Not findings, recorded because they
were done right"* block is theirs and stays **inside** the verbatim block under its own heading —
it is not lifted into a disposition, and nothing is written beneath its five items. A disposition
on a non-finding would be this file answering praise, which is not what §5's disposition slot is
for.

---

## Round 1 — the review of r0 (`305b3a1`)

### Findings, verbatim

**Verdict: APPROVE, with one finding for r1.** All four of m5-D2's declaration
requirements landed, the step-1 gate passed on both arms with each load-bearing zero
controlled, and the done-check is green.

**F1 — a live document still carries the claim the ruling overturned, and its recorded
executor is a closed row.** `cloudcost/milestone.md` §Open items describes the
new-provider-caveat and multi-currency rendering paths as *"unreachable while DO is the
only provider"*. m5-D2 makes that false in exactly the way the runbook's
*now-unreachable* sentence was false — and worse, because it restates the *"live at the
first fan-out"* reading that t1's **E1** killed, as a premise. **Declining to edit it
was correct**: §Open items is not in `Touches`, and a ticket's scoping is authoritative
over a ticket's judgement — that is what makes a `Touches` worth having. Recording it
in BL-070's disposition was the right instinct and does not discharge it: **BL-070 is
now DONE, and a finding recorded inside a closed row is a record, not an executor.**
The gap is the reviewer's — `Touches` named §Contracts only and missed a third site in
the same file carrying the same premise. Amended at r1.

**Not findings, recorded because they were done right.**

- **The pre-edit pytest run.** A post-edit green proves nothing on its own; the pair is
  what makes 386 evidence rather than coincidence. The check did not ask for it.
- **Proving *no executable line changed* by AST equality outside the docstring**, not
  by reading the diff — a check that would catch an edit staying inside the line range
  while changing code, and that does not depend on how the diff happened to hunk.
- **Both pointer blocks discharged inside the same blockquote as the pointer**, so a
  reader cannot meet one without the other — and C4's discharge naming the route count
  it inherited wrong rather than quietly carrying it forward.
- **The closure shapes derived from the file with a precedent named for each**, rather
  than one shape applied uniformly to five rows that are not in the same state.
- **The runbook's second-claim check run over the whole file**, returning two sites
  deliberately left alone with the reason each is not on the same premise. A sweep that
  reports what it declined is a sweep; one that reports only what it changed is a diff.

### Dispositions

#### F1 — accepted; corrected at W2, and the sweep it implies run at W3

**The finding's own diagnosis is the part worth acting on.** *"A finding recorded inside a closed
row is a record, not an executor"* is exactly right, and it is the reason r0's disposition was
insufficient rather than merely incomplete. BL-070 was marked **DONE** in the same commit that
recorded the residue inside it, so the residue had no executor from the moment it was written. The
standing rule in both repos — *a deferred finding gets a backlog row in the same round it's
deferred; prose in a packet or notes files nothing* — was satisfied in letter and defeated in
substance, and the defeat was invisible because the row it lived in was the row being closed.

> `[Corrected by pointer 2026-08-11 at the m5 record-correction edit. **"in both repos" is
> wrong — the rule stands in the agents `CLAUDE.md` only.** The full correction, with the
> re-derivation and its controls, is in `cloudcost/docs/m5-t2-implementation-notes.md` at the
> paragraph closing *"BL-070 is the executor this ticket could reach"* — the first of this
> claim's two occurrences. Pointer rather than a second full correction, so the derivation has
> one home. The surrounding argument is untouched and unwithdrawn: the rule bound this round
> either way, a rule standing in one repo being still standing.]`

**What landed.** §Open items' unit is corrected in place, in the shape r0 gave the runbook: the
superseded wording quoted verbatim in the position it occupied, the correction dated, **m5-D2**
named, and the accurate claim stated — **reachable and uninvoked**, with reachability explicitly
**not a function of provider count**. The status the paths now have is carried rather than left to
be inferred: the human-eyeball item stays open, and it is owed by the first ticket that makes
either path reachable **from the pipeline**, which under decision H and m5-D2 is no ticket now
scheduled.

**The authority for the edit is the reviewer's amendment, not this ticket's judgement.** §Open
items was added to t2's `Touches` at r1 before the correction was made, and the bullet records
whose gap it was. r0's refusal to edit outside `Touches` is not reversed by this — it is
vindicated, and the fix is a scoping change rather than a licence to exceed one.

#### The sweep F1 implies, run at W3 and reported whether or not it changed anything

F1 names one site. The runbook rule's own logic — *if the correction surfaces a second
operator-visible claim resting on the same premise, correct it in the same commit and name it* —
transfers to `cloudcost/milestone.md`, which is the larger file and now carries three m5-D2
declarations. The sweep found **one further hit on the overturned premise**, in §Open items and so
inside the amended `Touches`: the cross-currency aggregation item's
*"**Latent while m1 is DO-only single-currency; live at the first fan-out.**"* — the same *"live at
the first fan-out"* reading F1 names, stated as a premise about four code sites that are BL-070's
own deferred deletion targets. Corrected in the same commit.

**Two further observations are reported and not fixed**, because they do not rest on the premise
m5-D2 overturns and the amended `Touches` authorises only claims that do. Both are in §Open items
and both are staleness of a different kind — a *"while DO is the only provider"* framing and a
*"lands with the second adapter"* schedule, in a repo that now ships three adapters. Neither is
m5-D2's to settle. **The reviewer's call** whether they want a round of their own.

`Round 1 dispositions written at t2 r1, 2026-08-10, against agents 305b3a1. Full record:
cloudcost/docs/m5-t2-implementation-notes.md §r1.`
