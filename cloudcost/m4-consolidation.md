# m4-consolidation — the cycle document

> Not a feature milestone. This cycle clears accumulated infrastructure debt in the cloudcost
> sprint case and the shared scripts, so that the decision about a fourth provider is made against
> working apparatus rather than on top of it. Created after two tickets had already closed,
> because the cycle opened without one — see §Why this exists.

> This is the m4 entry in the cloudcost series (`milestone.md`, `m2-milestone.md`,
> `m3-milestone.md`), named for what it is rather than to the series pattern. A sweep looking for
> `m4-milestone.md` will not find it.

**Status:** open. **Opened:** 2026-08-05 (first move ratified). **Document created:** 2026-08-06.
**Repos:** `aetheris-agents` and `aetheris` (harness). **Preceding cycle:** m3-cloudcost, closed
2026-08-05.

---

## Why this exists

The cycle's first move was explicitly *not* a milestone doc. That was right at the time — the work
was a backlog batch, not a feature milestone — but it meant the ticket set, the ratified decisions
and the sequence lived only in conversation. Two tickets closed that way.

**BL-102 is the standing row for this exact gap**: the complete-but-unmarked sweep at a close reads
a milestone doc's done-when table, and a batch has none. This document is that artifact for this
cycle, and §Close criteria states what a sweep of it reads.

The decision log below is the part with no other source. Everything else is recoverable from the
repos; the decisions were not.

---

## Scope

**In scope.** The cloudcost sprint case in `../aetheris/scripts/sprint.sh`; the four shared scripts
under `cloudcost/scripts/` — **`detect_orphans.py`, `_normalized.py`, `compose_report_data.py`,
`render_report.py`**; the documents that describe either; the backlog rows covering them.

> **Enumerated 2026-08-06 (t1b review r1).** "The four shared scripts" was an unenumerated count
> in a directory holding **eight** `.py` files, which is the *"the one X"* tell — in the document
> that holds this cycle's decisions. It names the **provider-agnostic** subset, and BL-074's
> Scope paragraph is the authority: it sweeps exactly these four and calls them *"shared
> machinery"*. The other four — `fetch_aws.py`, `fetch_do.py`, `fetch_linode.py` (adapters) and
> `detect_optimization_signals.py` — are not shared machinery and were never what "the four"
> meant. t1b pinned all eight by blob hash rather than guess, and all eight are byte-unchanged.

**Not in scope, and deliberately so.**

- **The harness `--json` contract** — BL-105 and BL-106. Found during this cycle and the most
  consequential thing in it, filed rather than pulled in. Scheduled as its own round; see §Sequence.
- **Provider four.** Gated on this cycle's seam sweep and on the harness round.
- **Any §Normalized extension.** BL-098 remains filed; extending the contract belongs with the
  provider that needs it, not before.

---

## Ratified decisions

Every entry is a decision taken in this cycle that no other document records. Dated; the arbiter
ratified all of them unless marked otherwise.

### How the cycle is run

| # | Decision | Date |
|---|---|---|
| 1 | **The reviewer asserts no checkable specifics in specs it authors.** Anchors only; where a value is needed the ticket says *verify and record*. | 2026-08-05 |
| 2 | **A claude-code verification pass runs over any reviewer-authored doc before ratification**, not after. | 2026-08-05 |
| 3 | **A step-1 gate inside the ticket.** Verification conditions the implementer checks before writing; any failure stops without an edit. Allowed once as an exception, retained as practice after it stopped a ticket whose census had not converged. | 2026-08-06 |
| 4 | **Ticket names are historical and are not tidied.** `t1a`, `t1a-p`, `t1b` are cited in committed documents in both repos. | 2026-08-06 |
| 5 | **The §7 promotion runs mid-cycle when the rules bind the cycle's own remaining tickets**, rather than waiting for the close. | 2026-08-06 |
| 6 | **Pushes are held for review; a cross-citing repo pair lands together**, harness first so the agents citations resolve on the remote. `[amended 2026-08-08 — closure pre-authorisation is permitted, bounded; see the note below. Original text above is unchanged.]` | standing, reaffirmed; amended 2026-08-08 |

> **Decision 6 amended 2026-08-08 (m4 close-b), on the human's ruling — closure
> pre-authorisation is permitted, and it is bounded.** §Close criteria item 4 asks for any
> decision the implementation diverged from, and this is one: from t4b r3 onward every closing
> round was pre-authorised — *"if r_n contains only these edits and its done-check is clean, the
> ticket is closed on that commit"* — which decision 6 as written did not contemplate. It is
> closed by changing the decision, not by pretending the practice did not happen.
>
> **The permission.** Closure may be pre-authorised: the reviewer may name in advance the
> conditions under which a closing round closes its ticket, and the row may read `Closed` on that
> authority. That authorisation is the row's truth-maker; the commit is not predicting its own
> review.
>
> **The bound, from t4c r1, learned by crossing it.** Closure may be pre-authorised **only after a
> round has been reviewed, naming that round's scope. It cannot be issued in an opening ticket** —
> there its condition, *the done-check is clean*, can only mean the implementer's own checks
> passed, which is not the same as the reviewer finding nothing.
>
> **The cost, stated rather than glossed: the last change of a ticket stays unreviewed by design.**
> That is what this amendment ratifies, not a tension it resolves. At t2 it had teeth twice — the
> r1 marker was itself wrong and was caught only because r2 read it, and had r2 not run, the r1
> dispositions (a `CLAUDE.md` edit among them) would have shipped unread.
>
> **Origin, named rather than smoothed over.** The device was introduced by **the reviewer
> (claude-ui)**, written into the t4b r3 ticket as an authority deliberately placed outside the
> loop, and re-issued by the reviewer at t4c, t5b r2, t5c r1 and close-b. **claude-code never
> proposed it.** It was in use for four tickets before anyone recorded that decision 6 did not
> sanction it; close-a found the divergence. The record should say that rather than present the
> practice as having always been authorised.
>
> `[corrected 2026-08-08 (close-b r1). The paragraph first read "introduced by claude-code without
> asking" — **wrong when written**, and wrong in the one sentence whose whole purpose is to be
> honest about origin. §Sequence's t4b r3 note, twenty lines above in this same document, already
> read "**The reviewer supplied one at r3, authorising closure in advance**", and the t4c r1 note
> beneath it is marked "authored by the reviewer". So the claim was refuted by the record it sits
> beside — the count-beside-the-enumeration shape, one level up and about a party rather than a
> number.]`

### Document handling

| # | Decision | Date |
|---|---|---|
| 7 | **A closed record gets a dated superseded note; its original text is not rewritten.** | 2026-08-06 |
| 8 | **Live operational guidance is corrected in place.** A superseded note on a how-to leaves wrong instructions standing as the primary text. | 2026-08-06 |
| 9 | **Where liveness is genuinely undecidable, take the note.** Asymmetric: a note on a live document still delivers the correction; an in-place rewrite of a record falsifies it irreversibly. | 2026-08-06 |
| 10 | **A milestone-named document is a closed record if a current equivalent exists** — established, never inferred from the filename. | 2026-08-06 |
| 11 | **Content is authored by the reviewer; formatting belongs to the destination file.** | 2026-08-06 |

### Technical

| # | Decision | Date |
|---|---|---|
| 12 | **No planted cloud resources, on any provider.** BL-069 closes by retiring the practice, not by swapping fixtures. The live check becomes a rule-legibility assertion — that the adapter's inventory reached the catalog in a shape it could read — which is free and covers the seam that has historically produced defects. | 2026-08-06 |
| 13 | **Payload extraction, not stream splitting**, for the sprint's `--json` reads. Later re-grounded: splitting is not sufficient wherever the harness emits Logger output on stdout, which is every capture from 2026-07 onward; whether it sufficed in an earlier era depends on `[sandbox]` routing, which is unestablished. | 2026-08-06 |
| 14 | **The class is every `jq`-over-`--json` read**, not the `.status` reads alone. One shared extraction mechanism; leaving a sibling field broken on the adjacent line of the same helper is how the class regenerates. | 2026-08-06 |
| 15 | **BL-099's credential grep is written so that covering a second file is configuration, not a rewrite** — because a later harness round may split the streams, and the grep is the only thing blocking that. | 2026-08-06 |
| 16 | **The eduloka status extraction is out of scope** — same shape, different root cause, possibly working today. Filed as BL-108. | 2026-08-06 |

---

## Ticket set

Full §6 anatomy is authored per ticket at the time it starts, not here. This section records what
each ticket is for, its state, and what it carries.

Commit ranges are `first-commit^..head`, so each pastes into `git log` and returns the whole
ticket; the count states how many commits that is.

| Ticket | Subject | Rows | State |
|---|---|---|---|
| **t1a** | Correct the false `2>&1` causal claim in every standing carrier | BL-100 rescoped, not closed; filed BL-105–BL-109 | **Closed** — agents `6a2c012^..13eac9f` (5 commits), harness `9c676ef^..e6687f1` (2) |
| **t1a-p** | §7 promotion of the cycle's findings | none — the promotion is a `CLAUDE.md` edit, not a row | **Closed** — harness `e98448a^..f6fbd82` (2 commits), agents `0371d75^..009f666` (2) |
| **t1a-c** | This document | BL-102, answered for this cycle by §Close criteria; **no row closed** — BL-102 is *answered*, not closed | **Closed** — agents `4b79d8f^..` this commit. Created at `4b79d8f`, amended by every ticket since, and closed at close-c by the commit carrying §The close below. Its deliverable is this document and the document is complete |
| **t1b** | One extraction mechanism for `--json` output; repair the chaos gate | BL-100 **closed**, BL-107 **closed**; filed BL-110 | **Closed** — see §What this cycle established → *What t1b established* |
| **t2** | Retire the plant practice; rule-legibility assertion | BL-069 **closed by retirement**; BL-074 and BL-044 appended | **Closed** — see §What this cycle established → *What t2 established* |
| **t3** | Hermetic allowlist inversion; credential-grep generalisation | BL-104 **closed**, BL-099 **closed**; BL-044 appended; filed BL-112, BL-113 | **Closed** — see §What this cycle established → *What t3 established* |
| **t4a** | The seam census: enumerate every provider-differing value in shared machinery, and record the sweep's method | BL-074 — **enumerated, not discharged**; no DONE section | **Closed** — the census is `cloudcost/docs/m4-t4a-implementation-notes.md`: 518 nodes extracted structurally, 54 censused, seven leads confirmed and none refuted |
| **t4b** | Write the rulings as contracts: **§Contracts (C1–C15)** in `cloudcost/milestone.md` | BL-074 **not closed** — its Done-when clause 2 amended here, before assessment, to name §Contracts; m1's "one seam" text corrected here | **Closed** — 54 items ruled 48 schema-level / 4 adapter-owned / 2 neither, each cited by census item id in exactly one contract; see the closure note under §Sequence |
| **t4c** | File the rows the rulings created, and close BL-074 | **BL-074 CLOSED**; **17 rows filed** (BL-114–BL-130): 10 defect + 7 contract consequence; 3 exclusions confirmed already recorded, not re-filed; 1 candidate dropped on a failed precondition | **Closed** — see the closure note under §Sequence; the count correction is below |
| **t5a** | Scope the report value pass — read-only, no commit | none | **Closed** — the scoping report; it produced no repo artifact by design |
| **t5b** | The report value pass: BL-101 in full, BL-070's slug convergence, BL-121, BL-127 | **BL-101 closed**, **BL-121 closed**, **BL-127 closed**; BL-070 **partly** (slug only, Done-when amended); filed **BL-131**, **BL-132** | **Closed** — see the deferral note under §Sequence |
| **t5c** | The rider: the report distinguishes *not found* from *not looked at* | **three surfaced** — X4, N8, P11 (rows annotated, none closed); **X5 ruled *needs its row*** — the report cannot mark a mis-decode it never detects. P2 was discharged at t5b, F3 is blocked on BL-116 | **Closed** — the four rows annotated, BL-114's discharge question assessed and declined |

**Why t4 became t4a and t4b (2026-08-06).** BL-074's output is a set of **rulings** — for each
provider-differing value, schema-level or adapter-owned — and a ruling is an adjudication, not an
implementation. A single ticket would have had its implementer both enumerate and rule, which is
the shape decision 1 exists to prevent: the party that produces a finding is not the party that
decides what it means. So **t4a enumerates and reports; the arbiter and reviewer rule; t4b
implements**. t4a edits none of the four shared scripts and closes no row — its `Do not generate`
list names the ruling itself, and its step-1 gate pins all eight `cloudcost/scripts/` blob hashes
so the read-only claim is proven rather than asserted. BL-074 is **not** discharged by the census;
its Done-when also requires the rulings landed and m1's "one seam" text corrected, and both are
t4b's.

> **And t4b became t4b and t4c (2026-08-07).** The split ran once more, for the same reason and one
> level down. t4b's rulings are **contracts**, and the census's own output separated into two kinds
> of item: values whose ruling is a sentence about which side of the seam they live on, and values
> that **stay broken whichever arm they land in** — a scoring modifier that has never fired, a
> billing case neither stopped rule covers, a validation the sprint's own gate presumes absent.
> Ruling the second kind does not fix it. So **t4b writes the contracts and t4c files the defect
> rows**, and BL-074 closes at t4c rather than t4b — the row's Done-when is discharged by the
> rulings *and* by the rows those rulings created having somewhere to live.
>
> **Count corrected 2026-08-07 at t4c.** This row and t4c's stub both said *"11 rows filed"*. That
> counted the defect list only. §Contracts' own preamble commits more broadly — *"where a code
> change genuinely follows, it is marked `[code consequence]` and is owed a backlog row by m4
> t4c"* — and a derivation of those markers returns **11**, of which 3 are already on the defect
> list and 1 (D17) is an exclusion, leaving **7** that the defect list does not reach. **A
> specification gap in the t4b ticket**, resolved at t4c by filing both sets with a `Kind` field
> distinguishing them: a **defect** row states what is broken today; a **contract consequence**
> row states what §Contracts now requires that the code does not yet do. **17 rows**, and the
> defect list ships **10**, not 11 — D5's candidate row was dropped when its precondition failed. **The lopsided result
> is the finding**: 48 of 54 are schema-level, because these four scripts *are* the shared
> machinery, so the deliverable was a contract section rather than a migration.

### What t1b inherits

Five items. The first four are method rather than scope; the fifth is an obligation t1a deferred
into t1b and is the reason this list is canonical rather than convenient — all cheap to state and
expensive to rediscover:

1. **Its behaviour-neutrality premise is refuted.** A converted site's *current* output depends on
   ambient run-store state, so "reproduce it exactly" is undefined. The check is that the helper
   yields the correct value on both clean and noisy captures.
2. **Census classification must distinguish assert from retract.** t1a seeded its own territory
   with retractions that quote the claim they retract; a term-match census now returns them as
   hits.
3. **The multiple-payload question is unsettled** — whether one invocation can emit more than one
   parsing JSON object, which decides whether "the last that parses" is the right selector.
4. **G1 states both forms** — level-with-origin before implementation, ahead-by-N-unpushed after.
   As first written it would have failed a correct tree.
5. **Two docbuilder documents are owed a note, deferred to t1b by t1a and due when the fix lands.**
   `docbuilder/milestone.md:88` and `docbuilder/docs/m1-milestone.md:680` carry byte-identical
   text — *"the underlying `no-json` label in sprint output is cosmetic noise — trace to the log
   line prefix in run.json format"*. Neither carries the `2>&1` claim, which is why t1a's census
   did not correct them, and an earlier draft that asserted they did would have written a false
   correction into a ticket about a false claim. The note must state both things: the **cosmetic**
   characterisation is false for the class, because one affected site is a gate; and the open TODO
   is discharged by the **fix**, not by a document edit. t1a deferred it rather than writing
   "discharged" in the same commit as the thing that would make it true — which leaves the
   obligation live, and recorded here because a closed ticket's implementation notes have no
   executor.

### What t2 inherits

One item, recorded here rather than left to be found mid-ticket:

1. **BL-069's Done-when and decision 12 disagree, and the row does not know it.** The row
   (`docs/backlog-2026-06.md:2182`) offers two ways to close — *"either a fresh DO orphan is
   planted, or the assertion is re-pointed to a recorded fixture rather than the live account"*.
   Decision 12 rules out the first outright and reframes the second as a rule-legibility assertion.
   **The row is edited at t2's opening, before any implementation**, so the ticket is not written
   against a Done-when the cycle has already superseded. This is §Close criteria item 4 discharged
   prospectively, which is cheaper than catching it at the close.

---

### What t3, t4 and t5 inherit

Two constraints, recorded at t2's close because both are known now and expensive to hit mid-ticket.

1. **Implementation notes take an `m4-` prefix, for every remaining ticket.** m1 wrote its notes
   unprefixed, so `cloudcost/docs/` already holds `t1-`, `t2-`, `t3-`, `t4-` and
   `t5-implementation-notes.md`. **t3, t4 and t5 each collide**; t1a, t1a-p and t1b escaped only
   because m1 had no ticket by those names, which is why the collision surfaced at t2 rather than
   earlier. Write `m4-t3-implementation-notes.md` and so on — the `m2-t1-` / `m3-t1-` series
   convention, already used by both preceding cycles. Decision 4 is untouched: the *ticket* is
   still `t3`. Do not rename m1's files to make room.
2. **This document belongs in every remaining ticket's `Touches` list.** t1b and t2 both edited it
   outside `Touches` and both declared the same deviation for the same reason — its §Ticket set row
   and §What this cycle established are duties no other document performs, and leaving a row
   reading "not started" after the work lands is false in its own commit. A deviation that recurs
   by design is a `Touches` omission, not a deviation.

## Sequence

t1b → t2 → t3 → **t4a → t4b → t4c** → **t5a → t5b → t5c** → **harness consolidation round** →
**BL-131** → **provider four**.

> **Updated 2026-08-06 (t4a review r2), on the reviewer's ruling.** t4a's `Touches` named two
> changes to this document and closed *"Nothing else."*, so t4a left this line reading `t4` and
> flagged the mismatch rather than editing it. The ruling: §Sequence and §Ticket set are two
> sections of one document disagreeing about what happens next, and **§Sequence is the one a reader
> consults to find out** — so the fix is owed in the round that creates the mismatch, not a ticket
> later. This is the same Touches-omission-by-design that §What t3, t4 and t5 inherit item 2 already
> records about this document.
>
> **t4b is gated on the rulings**, which is why the arrow is not a plain continuation: t4a
> enumerated, the arbiter rules, t4b implements. A t4b started before the ruling table exists has
> nothing to implement.
>
> **t4c added 2026-08-07** and gated the same way — held until t4b is closed **and pushed**. It
> files the rows for the census items a ruling cannot fix; see §Ticket set.

> **t5 became t5a, t5b and t5c — and the N>1 deferral, 2026-08-07.** t5a scoped the pass read-only,
> because t4c's seventeen rows had changed the ground under the cycle document's t5 row. t5b
> implemented; t5c takes the rider, for the reason t5a's own sweep established — five of the six
> rows that fit the rider's shape surface in the two functions t5b restructures, so they are
> **cheaper after it, not concurrent with it**.
>
> **The rider was defined, not recovered.** *"The evaluated-versus-not-evaluated rider"* occurs
> exactly once in either repo — in the t5 row that used it, introduced by the commit that created
> this document. t5b's predecessor established that nothing defines it; **the reviewer, who wrote
> it, could not recover what they meant and decided it afresh rather than reconstructing it**:
> *the report must distinguish not found from not looked at.* It is the report-side case of
> **absent-is-unknown** (`../aetheris/CLAUDE.md:587`), not a new rule.
>
> **The N>1 deferral, and why it is a deferral rather than a ruling.** t5b's step-1 gate stopped the
> ticket: BL-070 proposed deleting the cross-provider merge as *unreachable*, and **§Contracts C4
> ratifies the currency policy that path implements** — a policy m2's decision H had already
> superseded, cited four tickets later as authority by a chain in which **no step checked the
> decision record**. The multi-currency path is reachable only through the N-merge, so the two
> cannot be taken separately. **The human ruled: defer.** N>1 is neither confirmed nor deleted in
> m4; **BL-131** decides it after the harness round, before provider four, where it bites.
>
> **BL-132** is the general form: the census swept code, §Contracts stated code as contract, and
> neither established reachability. C4 and C11 are the two known instances, and two is not a census.

> **t5c closed the cycle's implementation work, 2026-08-07.** Three of the four remaining rider
> items were surfaceable from data the report already had or that `compose` could derive without
> changing what any stage detects or validates — **X4** (whether the recent-activity modifier could
> fire at all), **N8** (resources counted in every total and evaluated by no rule) and **P11** (the
> granularity column is declared, not checked). **X5 was ruled *needs its row*** and is the useful
> negative: **the report cannot mark a mis-decode it never detects**, and `compose` is contractually
> pure of the environment, so there is no payload fact for a statement to read. An item ruled out
> with a reason beats a statement gesturing at a risk the report cannot observe.
>
> **No row was closed by surfacing.** BL-114's own text offers *keep it with the status documented*
> as a closing basis, and the status is now documented in both §Contracts C8 and the report — **and
> it was still not closed**, because the row's Done-when asks for a *decision* on whether a
> permanently-dead scoring path stays, and documenting a thing is not deciding it.

> **On the t4b row's state — the regress, and how it was broken (r2/r3, 2026-08-07).** At r1 the row
> read `Closed` in a commit that was itself under review, so it was false from the moment r1 landed
> until r2 passed — the same class as the observation this ticket raised at r0, applied to the row
> this ticket wrote.
>
> **r2 introduced `In review (r2)` as an interim state, and that was a fourth form.** §Ticket set had
> exactly three — `Closed`, `not started`, and t1a-c's `you are reading it` — so the r2 packet's
> claim *"I did not invent a review-state vocabulary"* was false; inventing one was the right call
> and the claim not to have done it was the only thing wrong. Recorded rather than quietly dropped,
> because a self-description that contradicts the row beside it is the same defect one layer up.
>
> **The regress itself.** A row that reads `Closed` only in the commit that closes it can never be
> written, because that commit is under review when it is written. Breaking it needs an authority
> outside the loop. **The reviewer supplied one at r3, authorising closure in advance**: *if r3
> contains only its four named edits and its done-check is clean, t4b is closed on that commit.*
> That authorisation is this row's truth-maker, and the row reads `Closed` because of it — not
> because the commit predicted its own review.

> **The same applies to t4c's row, 2026-08-07.** It reads `Closed` under the same
> pre-authorisation, granted in the t4c ticket in the same form: *if this ticket contains only
> Parts 1–5 and its done-check is clean, t4c is closed on that commit.* The regress and its break
> are unchanged from t4b; only the ticket differs.

> **The device misfired at t4c, and the rule it needs — recorded 2026-08-07 (t4c r1), authored by
> the reviewer.** Closure pre-authorisation worked at t4b r3 because the reviewer **had already
> reviewed r2** and was naming a closing round of known scope: *"only these edits, done-check
> clean"* was checkable against a set they had just fixed. At t4c it was issued in the **opening**
> ticket, before any work existed to scope it against — and there its condition, *the done-check is
> clean*, can only mean **the implementer's own checks passed**, which is not the same as the
> reviewer finding nothing. So §Ticket set's t4c row read `Closed` from r0's landing and **was
> false until r1**, which is the regress the device exists to break, reappearing one level up.
>
> **The rule: closure may be pre-authorised only *after* a round has been reviewed, naming that
> round's scope. It cannot be issued in an opening ticket.** The t4b note above is correct as
> written and is untouched; this is the boundary condition it did not state, learned by crossing
> it. **Ratified into decision 6 at close-b, 2026-08-08** — see the note under §Ratified decisions,
> which also records what the device costs and that it was introduced without being asked for.

> **t1a-c's state, and a fifth form — 2026-08-08 (m4 close-b).** §Ticket set's t1a-c row read
> `you are reading it`, which was true in the commit that wrote it and false in every commit since:
> a reader consulting the table at this close is not reading t1a-c, and §Close criteria's clause 1
> — *"every ticket in §Ticket set"* — had one of twelve with no assessable state. It now reads
> **`Live`**, which is true in the commit it lands in: the document is still being amended, by this
> close among others, and cannot read `Closed` while close-c is still to edit it.
>
> **`Live` is a fifth form and is declared as one**, not slipped in. The column held four —
> `Closed`, `not started`, `you are reading it`, and `In review (r2)`. The t4b r2 note above
> established the standard being followed here: inventing a state form was the right call, and the
> only thing wrong was the claim not to have invented one.
>
> **`Live` resolved at close-c, 2026-08-08 — it was an interim form and is now spent**, the same
> treatment `In review (r2)` got. close-b set it because the document was still being amended and
> could not read `Closed` while close-c was still to edit it. **close-c is that edit**, so the row
> now reads `Closed` with its commit range, and the column is back to the three durable forms plus
> two retired interim ones. Neither `Live` nor `In review (r2)` should be read as vocabulary
> available to a future cycle without the same declaration.

**The harness round runs before provider four**, and for the same reason the seam sweep does. BL-074
tells you whether the next adapter is mechanical on the agents side; BL-105 and BL-106 tell you
whether the apparatus a new provider lands on works. Every new provider adds a leg to the sprint
case, and a leg added to non-deterministic reads inherits the flakiness — m3 already paid that cost
three times.

**The harness round's shape:** BL-105 and BL-106 are one contract with two mechanisms and are
scoped together; **BL-077** folds in, because by then the chaos gate will have been repaired and its
real state — the input BL-077's known-red declaration needs and does not have today — will be known.

**Provider-four design work is not blocked by any of this.** The GitHub issue-doc is design-only and
touches no code. What the harness round buys is that *implementing* provider four lands on
apparatus that works.

---

## What this cycle established

Stated as findings, not as rules — the rules are in the two `CLAUDE.md` files and are not restated
here.

- **The sprint's `--json` reads are non-deterministic, not broken.** Identical expressions succeed
  or fail on ambient state. Across the captures in `../aetheris/sprint/`, the news set parses in
  **4 of 4**, payslip in **0 of 8**, cloudcost in **0 of 10** — same helper (`run_agent`), same
  `> file 2>&1` redirect.
- **The cause everyone had recorded was wrong.** The harness's Logger output shares stdout with the
  payload, so merging the streams is irrelevant to parseability. The claim had propagated into
  **six documents across both repos** as standing guidance (**seven sites**), with a further
  **thirteen** historical mentions left intact as dated records, and was refutable from the Rig
  source for the ten days before it was filed: `rig/src-tauri/src/commands/fork.rs:137` has read
  *"`mix` compile and log noise shares stdout and does not parse as JSON"* since `b5e8eee`
  (2026-07-26, BL-030), and BL-100's row was filed at `cdc8f08` (2026-08-05).
- **A gate in the chaos case has never evaluated its subject.** Its operand is a fallback token that
  the equality test cannot match.
- **`--json` emits no JSON on a non-success run**, so a programmatic consumer receives nothing on
  exactly the runs it most needs.
- **Two stream routings are now established:** Logger on stdout, worker output on stderr — a third,
  `[sandbox]` line routing, remains open below. This makes
  the harness fix and stream-splitting complementary rather than alternative, and is why decision 15
  exists.

### What t1b established

- **The class had four mechanisms, not one, and 29 members.** Derived fresh at t1b (no prior list
  inherited): 13 × `jq` over the output file, 5 × `tail -1 | jq`, 7 × `grep -o '"run_id":…' |
  tail -1 | cut`, 4 × `jq` over a `--json` *pipe*. All now call one helper. 13 further sites were
  classified out with reasons. Breadth check, recorded as a negative: `sprint.sh` is the **only**
  consumer of harness `--json` in either repo's scripts. *(First stated as 19; corrected at review
  round 1 — three converted sites were missing from the census table and the total rested on a
  bogus pairing step. Now derived two independent ways — censused reads and helper call sites —
  which agree at 29.)*
- **The chaos gate evaluates, and it passes.** `WARN status=no-json` → `OK … → :done (expected)`,
  both quoted from live runs on the pre- and post-edit trees. The gate line's comparison and both
  message texts are unchanged; only the operand became real. BL-107 closed without exercising its
  carried-red branch.
- **The first chaos output ever captured in this repo now exists.** It carries two resume warnings,
  an orphan-sweep line and two `[sandbox]` lines ahead of an intact payload — the noisy-store shape
  BL-107's premise assumed, confirmed rather than presumed.
- **A red gate was found off-territory and filed the same day** — BL-110, the payslip case's
  `BTL_999` assertion, which names a reference employee the run cannot produce because the
  orchestrator reads `payroll.csv` while `BTL/999` exists only in `sample_payroll.csv`. Same
  ambient-state defect class as BL-100, pre-existing, left red per the tracked-carry clause.
- **BL-069 remains armed and red**, named rather than re-triaged: the live cloudcost leg reported
  `[FAIL] orphan candidates: 0 (expected ≥1 …)`. t2 owns it.

### What t2 established

- **BL-069 closed by retirement — the third branch.** Its Done-when offered plant-or-re-point;
  decision 12 ruled out both as written. The ≥1-orphan assertion is gone, replaced by a three-arm
  rule-legibility check that imports `CANONICAL_TYPES` rather than restating it, sited **outside**
  the period guard on the D2 grep's precedent. Live, same leg, same day: `[FAIL] orphan candidates:
  0` at 18:25 → `[OK] rule legibility: 18 resources evaluated, 0 skipped` at 18:29. All arms
  mutation-checked, the two failing ones against real artifacts rather than invented fixtures.
- **The run's coverage is not knowable from any artifact the sprint can read, and the check that
  looks like it establishes it does not.** The inventory envelope is five keys and carries no
  `not_inventoried` (BL-098); the adapter's summary, which does carry it, appears in **0 of 13**
  archived `sprint/*/cloudcost/run.json` captures. And the orchestrator-exit assertion cannot
  discharge it either: `mix aetheris` discards every command's exit code (BL-044, verified at
  harness `871a720`), so that assertion is reachable only when the Mix task *raises* — a run that
  ends `:failed` prints `[OK]`. Appended to BL-044 as audit input. This is why the not-applicable
  arm reports an **unknown** rather than a clean zero, a declared deviation from the ticket's
  wording.
- **The retirement census found the claim in one repo only, and mostly in prose that never says
  "plant".** `../aetheris` carries exactly one carrier (the assertion itself); `../aetheris/CLAUDE.md`
  carries none. On the agents side the live carriers were the runbook's recipe section, three
  handoff "Live tripwires" blocks, three closed milestone documents — one of them reading
  `Status: PENDING`, an instruction awaiting execution rather than a record — and **`CLAUDE.md`'s
  own gate rule**, which offered planting as the exemplar of correct known-red discipline. That
  last one is the site a token-keyed census would have found and a reader would have trusted most.
- **The BL-077 placement residual did not arise.** Recorded as a negative: the assertion sites
  outside the period guard, so the skipped-assertion-indistinguishable-from-passing finding gains
  no second instance from it.

### What t3 established

- **Default-deny cannot be spelled `env -i NAME=value` without breaking D2.** That form puts the
  credential in **argv**, readable from `/proc` by any user on the box, and D2 is *"env-only —
  never an argument"*. The prefix is therefore a function that unsets everything unlisted inside a
  subshell and `exec`s; no value is re-typed, copied, or placed in an argv. The obvious spelling
  of the fix was the one that had to be rejected.
- **`env -i` removes `AWS_SHARED_CREDENTIALS_FILE`, and absent is not `/dev/null`.** Absent
  restores boto3's default `~/.aws/credentials` lookup, and `HOME` has to be on the allowlist, so
  the file is reachable. Inverting naively would have re-opened the exact arm the denylist closed
  — a load-bearing coincidence in the old spelling, visible only by reading what the *assignment*
  did as distinct from what the *unsets* did.
- **Default-deny silences a warning the denylist deliberately preserved.** The Linode
  endpoint-redirect names were knowingly left unstripped so the adapter would *warn* when they were
  set; stripped, the hazard is neutralised for the run and never reported to the operator. The
  signal was restored parent-side, before the strip, from the adapter's own constants. Adjacent-case
  in its exact form: the fix's blast radius was one case wider than the case it was written against.
- **The passthrough list is seven entries and two of them were invisible until the run was
  measured.** `LANG` — without it the BEAM falls back to latin1 and the `--json` payload's `·` is
  written as a bare `0xB7` instead of `0xC2 0xB7`, and **the line still parses**, so nothing
  downstream would ever have noticed (filed as **BL-112**, harness-wide and pre-existing).
  `CLOUDCOST_OPTIMIZATION` — without it the orchestrator's own fail-fast guard silently stops
  firing, `exit 0` where it should raise. A prefix that disables another component's guard is the
  ticket's own defect class, one layer down.
- **The credential grep now runs on the leg it was filed about.** Before this ticket the
  DigitalOcean leg had no D2 assertion at all and was green either way; it now prints
  `[OK] no CLOUDCOST_DO_TOKEN in run.json`. The anti-vacuity control the AWS arm lacked is in
  place: the same matcher, against a file built to contain the credential, must find it.
- **The three no-silent-fallback guards are not BL-044-shaped — but they have a different
  defect.** `mix run --eval` propagates a raise (verified both directions; `mix aetheris` does
  not, which is BL-044). What all three actually lack is any assertion about *which* raise fired,
  so any raise passes — the chaos-gate shape. Guard 2, the only one whose environment this ticket
  moved, now matches the raise message; the other two were **considered and kept**, recorded as a
  negative, because their failure direction is safe (a missed name makes the eval *succeed*, so
  they fail loudly).
- **Guard 2's change was forced, and proven so rather than asserted.** With a token present in
  the parent, the old outer `env -u` spelling exits 0 — the raise does not fire — because the
  prefix re-exports every allowlisted name. Demonstrated with a synthetic token.
- **Legs, stated as a limit.** Only DigitalOcean was runnable; AWS and Linode credentials are not
  present in this environment and none was minted or probed. Their adapter env surface, guard
  raises and knob behaviour were verified without a run; the AWS region-sweep consequence is the
  one claim in the ticket resting on a read rather than a run, and is labelled as such. **The
  passthrough list carries the same limit**: demonstrated end to end on digitalocean,
  category-derived for the other two, and said so beside the list rather than only in the notes.
- **A sufficient list is not a minimal one, and the difference is a removal test (review r1).**
  Additive derivation proves an entry fixed the failure in front of it *at the time*; it does not
  prove the entry is still load-bearing once the list has grown, and an over-large allowlist is
  the denylist defect with the sign flipped. Every entry was re-observed with itself removed from
  the **final** list, and all six hold. The specification gap was the ticket's, not the
  implementation's — the subtractive constraint was ratified in answer to the derivation question
  and never reached the ticket text.
- **A row filed against the half of its surface that fails loudly is filed against the safe half
  (review r1).** BL-113 first said a missed *credential* constant is missed silently. Mutating the
  bridge established the opposite: a missed mandatory credential is the one case that fails loudly
  (empty-list guard at preflight, or the adapter at fetch). The silent cases are a missed knob, a
  missed *optional* credential, a missed hazard, and — the costly one — a credential
  **mis-categorised as a knob**, which is allowlisted but never grepped, so it is a D2 hole every
  leg reports green. Corrected before the row was ever acted on.
- **Hermetic against names is not deterministic in values.** `LANG` passes through, so two
  operators can get different bytes out of the same sprint, one silently corrupted. The prefix
  guarantees no *unlisted name* reaches the run; it guarantees nothing about the *values* of the
  listed ones. Recorded so "hermetic" is not read as "reproducible"; BL-112 is the fix.

### Rows filed this cycle

Read from `docs/backlog-2026-06.md` at agents `009f666`:

| Row | Subject, as the row heading states it |
|---|---|
| **BL-105** | `--json` mode's payload shares stdout with the harness's Logger output |
| **BL-106** | `--json` emits no JSON document on a non-success run |
| **BL-107** | the chaos-case gate has never evaluated its subject |
| **BL-108** | the eduloka sink gate parses a merged stream: same shape, different root cause |
| **BL-109** | two `milestone-reference.md` files, canonical by different measures |
| **BL-112** | the BEAM's latin1 fallback silently corrupts non-ASCII in `--json` payloads |
| **BL-113** | the sprint's adapter env bridge selects by constant name, so a new credential constant is missed silently |

**BL-100 rescoped, not closed.** Heading, cause, scope, fix and Done-when revised under a dated
*"Rescoped and corrected 2026-08-06 (t1a)"* note, each change marked `[corrected 2026-08-06]` with
the superseded text kept beneath, and **Size raised XS → S–M**. The fix has not landed; t1b carries
it.

**Rows filed at t4c, 2026-08-07** — read from `docs/backlog-2026-06.md` at this commit. Seventeen,
in two kinds. A **defect** row states what is broken or missing today, established from the record;
a **contract consequence** row states what §Contracts now requires that the code does not yet do.

| Row | Kind | Item | Subject |
|---|---|---|---|
| **BL-114** | defect | X4 | the recent-activity modifier has never fired against any real inventory, on any provider |
| **BL-115** | defect | F2 | a stopped instance with no attached storage and a non-zero own estimate yields no candidate |
| **BL-116** | defect | F3 | the aged-snapshot rule's docstring requires a gate its code does not apply |
| **BL-117** | defect | N8 | an out-of-vocabulary `type` is counted everywhere and evaluated by nothing |
| **BL-118** | defect | X5 | five I/O sites decode adapter JSON under the platform default encoding |
| **BL-119** | defect | P8 | a cost snapshot with a declared total and no line items is silently dropped from discovery |
| **BL-120** | defect | D16 | the idle-load-balancer rule rests on a `tag:` convention nothing enforces |
| **BL-121** | defect | P2 | the untagged-spenders cap truncates across all providers and reports nothing |
| **BL-122** | defect | P11 | `source_granularity` is carried into the report and validated nowhere |
| **BL-123** | defect | D12 | `age_phrase` truncates, so the evidence sentence contradicts its own threshold |
| **BL-124** | contract consequence | N3 | C3: reject a naive timestamp rather than assuming UTC |
| **BL-125** | contract consequence | D20 | C3: name the timestamp field set once instead of hardcoding the pair |
| **BL-126** | contract consequence | N5 | C4: carry the currency's minor-unit exponent and round to it |
| **BL-127** | contract consequence | N7 | C6: a non-`str` tag element is a counted skip, not a silent drop |
| **BL-128** | contract consequence | D6 | C6: the keep marker becomes a first-class field, not a tag spelling |
| **BL-129** | contract consequence | P6 | C10: service identity needs a stable identifier beside the display name |
| **BL-130** | contract consequence | P7 | C11: promote `swept_regions` to a first-class optional envelope field |

**Three exclusions confirmed, not filed** — D15 (C7), D17 (C3), P4 (C10), each already recorded in
§Contracts with its reason, each latent on a hypothetical provider and exhibited by none of the
three. **One candidate dropped**: D5's case-policy row, whose precondition was run at t4c and
failed — zero of 118 recorded resource names bite — with the residual recorded as a note under C15.

**BL-074 closed at t4c**, all five Done-when clauses assessed per clause in the row's DONE section.

**Rows filed at close-b, 2026-08-08** — both from close-a's read, both open by design.

| Row | Kind | Subject |
|---|---|---|
| **BL-133** | method | the loop's evidence is not retained, so no past run's greenness is checkable after the fact |
| **BL-134** | verification | the comment-as-truth-maker check over the t4a census — seven claims to verify, eight entries to hand-classify |

**BL-075 annotated, not closed and not amended** at the same commit, and **its flake reproduced at
close-b's own gate run**. An off-territory `mix test` — close-b edits four markdown files and no
code — reproduced the 2026-08-02 shape exactly (1 failure, then 3 clean on the same tree), and
**the failing test's identity was captured for the first time since the row was filed**:
`Aetheris.CLI.Commands.RunHelpersTimeoutTest`, a fixed 300 ms inactivity window missed under load.
The row's *"likely home"* guess is **refuted** — BL-054 is the `requires_worker` twelfth-slot flake
and this is neither — though both are fixed-ms windows and share the polling rewrite BL-054's order
entry already names. **Not closed and not folded**: the fold-or-file *is* the closing action, and
this close closes no row. Its second arm stays blocked on BL-133, and the Done-when is left exactly
as written — amending it before the retention question is decided would be writing a clause around
a gap instead of naming it.

### Rules promoted this cycle

Three, at t1a-p. **Named here, not restated** — they are normative in the files below and a copy
here would be a second source of truth.

- `../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns — the truth-maker rule, with its
  two operational forms. **A third form was added at close-b; see below.**
- `../aetheris/CLAUDE.md` §Continuous learning → Silent-wrong-answer — the command-binding carrier.
- `CLAUDE.md` (agents) §Learning — BL-007 — the packet rule, superseding its earlier wording.

**Four more at close-b, 2026-08-08.** Same convention — named here, normative in the files. Where
each landed and why is in §Promotion candidates' closing note; **placement is editorial**, and the
repos rule was widened in the same commit so that it can be.

- `../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns, inside the truth-maker rule —
  its **third operational form**: *a count is a claim about a population*, carrying three named
  carriers (a count replaced without re-checking the claim it hung on; a count printed beside an
  enumeration that contradicts it; a count taken over a partial capture and reported as the whole).
- `../aetheris/CLAUDE.md` §Continuous learning → Silent-wrong-answer — **match structured data by
  field, not by substring**, a widening of the command-binding carrier.
- `../aetheris/CLAUDE.md` §Continuous learning → Silent-wrong-answer — **sibling state**, a widening
  whose entry states that it rests on one instance.
- `CLAUDE.md` (agents) §Learning — BL-007 — **a packet's sprint section shows the run's full output,
  or states what it elided and why**, whose entry states that it is a packet rule rather than a
  recurrence-derived learning entry.

**And one amendment, not a promotion:** `CLAUDE.md` (agents) §What this repo is — the **repos rule**
now binds every session, not only cross-repo and packet-producing ones.

---

## Not established

Carried forward rather than resolved. Each is a question this cycle opened and did not close.

- `[sandbox]` line stream routing. The available test command spawns no worker.
- Which document first carried the false causal claim — three harness documents acquired it on one
  day and same-day ordering is not recoverable.
- ~~Whether the step-count diagnosis in an m09→m10 handoff is correct.~~ **Resolved 2026-08-06
  (t1b review r1): it is wrong, and the ordering is recoverable.**
  `../aetheris/docs/aetheris/milestones/handoff-m09-m10.md.md:145` says step counts show `n/a`
  *"because the script reads step count from `--json` run output but it's not in that payload.
  Fix: read from `mix aetheris inspect <run_id>`."* `extract_step_count` **already read from
  `mix aetheris inspect`** — that line landed at `fafa17f` (2026-05-16 12:40 +0530) and the claim
  text was written at `2a5dc59` (2026-05-17 09:58 +0530), **21 hours later**. So this is not a
  diagnosis later superseded; it prescribed a fix that was already in place. Unlike the false
  causal claim, same-day ordering did not have to be guessed here.
  **The actual cause was the same one this cycle has been chasing**: both of the function's reads
  were contaminated — `.run_id` from the merged run file, and `.step_count` from a
  `mix aetheris --json inspect` *pipe*, which carries Logger output exactly as a file does. t1b
  converted both (Group A `:79`, Group D `:81`). Verified live against the post-edit chaos capture:
  `extract_step_count → 2 steps`, against a `max_steps: 2` run.
- Whether the chaos gate has ever run in a clean-store environment. No chaos output had ever been
  captured, so "it has always warned" was inference. **Partly resolved 2026-08-06 (t1b):** the
  first chaos capture in this repo (`../aetheris/sprint/20260806_172144/chaos/maxsteps.json`)
  exists and *did* warn, in a noisy-store environment — so the behaviour is now observed rather
  than inferred for that case. **The clean-store question itself is still open**: no chaos run has
  been made in a clean store, and nothing in t1b established what one would have done.
- Whether `EDUX_DATABASE_URL` is set in the sprint's ambient environment — decides BL-108.
- Which `milestone-reference.md` survives — BL-109.
- ~~Whether one `--json` invocation can emit more than one parsing JSON object — t1b's carry 3.~~
  **Resolved 2026-08-06 (t1b), both from source and from the record.** Yes, but for exactly one
  command: `fork`. `Formatter.print/2` is called once per invocation
  (`../aetheris/lib/aetheris/cli/main.ex:46`) and is one of only two `IO.puts(Jason.encode!(…))`
  sites in `lib/`; the other is `Fork.emit_fork_started/2`
  (`../aetheris/lib/aetheris/cli/commands/fork.ex:71`), whose own comment names it as the only
  command writing to stdout before dispatch returns. It writes the early document **first** and
  the result **last**, so "the last that parses" remains the correct selector, and `sprint.sh`
  never invokes `fork`. Empirically: of **319** files under `../aetheris/sprint/`, **zero** carry
  more than one parsing JSON object (219 exactly one, 100 none). Recorded in
  `../aetheris/docs/aetheris/claude-notes.md`, which previously carried this as the scan's one
  unresolved case.

---

## Open for the close

Decisions the close must **take**, as distinct from §Close criteria below, which lists reads it
must **perform**.

1. **Whether the step-1 gate becomes standard practice rather than per-ticket.** Decision 3
   admitted it once as an exception and retained it for this cycle's tickets; nothing makes it
   standing, and every ticket since has restated it in its own text.

   *The evidence for asking.* Claims that reach past what their author could check recurred
   throughout this cycle, most often in the documents written to correct them, and on both sides
   of the loop rather than only the implementer's. Instances that resolve in committed artifacts:
   `docs/reviews/t1a-review.md` §"The reviewer's closing observation" (`:56–63`) records four
   inside t1a alone; `cloudcost/docs/t1a-p-implementation-notes.md` §3 records one in t1a-p's own
   promotion `Source:` line, caught before commit, and one in edit C's citation, corrected at
   round 1. **Further instances are observed rather than recorded** — several occurred in review
   packets, which are session artifacts and not in either repo — so the full set has never been
   enumerated, and no count of it appears here. Enumerating it is work for the close if the close
   wants a number; the pattern does not depend on one.

   *What would settle it either way.* The reviewer records catching one such claim in their own
   draft before it landed — the first time in this cycle the defect was stopped by its author
   rather than by a gate or a round. A gate that becomes standard is an admission that authorship
   alone has not been sufficient; a run of tickets where authors catch their own would be the
   evidence for not making it standing.

   *A second face of the same question: **the last change of a ticket is never reviewed.*** The
   loop's closing instruction has been *apply and close, then push*, so every round's dispositions
   land unreviewed by construction — including the ones that correct a review finding. The trade
   has been made deliberately several times this cycle and judged right each time; the alternative
   is a round-trip per one-line fix. But it is a trade, and it is the same shape as the gate
   question: **where the discipline sits — before the edit, or after it.** At t2 it had teeth
   twice. The r1 marker was itself wrong and was caught only because r2 read it; and had r2 not
   run, the r1 dispositions — a `CLAUDE.md` edit among them — would have shipped unread. Recorded
   here so the close weighs it rather than meeting it as a surprise.

   > **Disposed 2026-08-08 (m4 close-b) — the *second face only*. The first face is untouched.**
   > Nothing at this close rules on whether the step-1 gate becomes standard practice rather than
   > per-ticket; that question stands exactly as written above, and decision 3 still admits the gate
   > per-ticket. **What was ruled is the push-trade**, on the human's authority: decision 6 is
   > amended to permit closure pre-authorisation, bounded by t4c r1 — *only after a round has been
   > reviewed, naming that round's scope; never in an opening ticket*. See the note under §Ratified
   > decisions.
   >
   > **The ruling ratifies the trade with a bound; it does not dissolve it.** *The last change of a
   > ticket stays unreviewed by design* — that is now the recorded cost of a sanctioned device
   > rather than an unrecorded consequence of a convention, and it is not a resolved tension. A
   > reader who takes this note as closing the question would be reading it wrong in the direction
   > that matters.

2. **Whether *match structured data by field, not by substring* is worth promoting.** Carried to
   the close rather than acted on, per the t2 review.

   *The evidence.* Twice in this cycle a defect was caught by **implausibility rather than by a
   check**, and both would have passed had the wrong answer been plausible. At t1a-p a verification
   step running with a persisting `cd` compared one repo's `CLAUDE.md` against itself and reported
   every phrase present in both files — caught only because a phrase cannot be in two files at
   once. At t2 a `grep -qF` over `docs/project-knowledge-manifest.md` reported
   `cloudcost/runbook.md` and `cloudcost/m3-milestone.md` as manifest-tracked; it was matching the
   `docs/rig/runbook.md` and `docs/aetheris/runbook.md` rows, and it was caught only because check
   8 staying silent about a file just edited was implausible. Had the manifest happened to track
   the runbook, the same broken grep would have returned the right answer and taught nothing.

   *Why it may not need its own rule.* This is the same family as the **command-binding** carrier
   already promoted under Silent-wrong-answer (*a check that reads the wrong thing reports a clean
   result, not an error*) — the manifest case is that rule with a table column in place of a repo
   path. The close decides whether the substring-vs-field form is a distinct enough carrier to name,
   or whether naming it dilutes the rule it belongs to.

   > **Disposed 2026-08-08 (m4 close-b) — promoted, in the *dilute* direction.** It landed as a
   > **widening of Silent-wrong-answer**, immediately after the command-binding carrier this item
   > itself names as its family, and **not** as a sibling rule: naming it separately would have
   > diluted the rule it belongs to, which is the answer this item framed as the choice. Read it at
   > `../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns, under Silent-wrong-answer.
   >
   > **Decided together with §Promotion candidates row 1, and decided the same way** — both are
   > widenings, both name their parent, and row 1's entry states that it rests on a single instance.
   > That pairing is what this item and row 1 both asked for.

3. **What governs durable instruction surfaces outside git.** The cycle has no standing answer, and
   **BL-111** is the row that will need one.

   *The evidence for asking.* t2's retirement census was correct and complete over both repos and
   still missed the stalest carrier of the practice it was retiring, because that carrier —
   this project's session memory — is in no repo. It is per-project-directory, unversioned, partly
   loaded into every session by instruction, and **13 of its 22 files are typed `feedback`**, which
   its own schema defines as guidance on how to work. So it is normative, durable, and reachable by
   no census, review, gate or drift check. Every other travel-failure this cycle has closed —
   BL-007's packet channels, the handoff-is-not-a-promotion finding — concerned content that at
   least *existed in a repo*.

   *What the close has to decide, and what it must not decide first.* Whether such a surface is a
   private scratchpad whose staleness is nobody's problem, or an untracked normative document that a
   retirement, a promotion or a correction owes an update. Only after that ruling does a mechanism
   make sense — "export it into the repo", "grep it in the census", "keep normative content out of
   it" answer three different rulings, and choosing one early creates a second surface to keep in
   sync. BL-111 is written to characterise, not to fix, for exactly this reason.

   > **Noted 2026-08-08 (m4 close-b) — still open, and BL-111 consumes the answer.** This is not a
   > §Close criteria change: the question is recorded here, where the close reads it, and the row
   > that will need it is not named in §Close criteria's five reads. So the pointer goes on the
   > question instead — **whoever decides this updates BL-111**, whose Done-when asks for exactly
   > this ruling and explicitly forbids skipping to a mechanism.
   >
   > **What the repos-rule widening at this close did and did not do.** Ruling 1 amended the repos
   > rule so every session reads both `CLAUDE.md` files before its first edit. That is a durable
   > instruction surface **inside** git; this item's subject is surfaces **outside** it. The two are
   > adjacent and the widening does not dispose of this question — if anything it sharpens it, since
   > raising what the tracked surface is relied on to carry raises what it costs for an untracked
   > one to diverge from it silently.

---

## Promotion candidates

Instances noticed mid-cycle that the §7 promotion at the close should weigh. **This is a list, not
a set of rules** — nothing here is normative, and an entry earns promotion only if the close rules
it does. The section exists so §7 reads a list rather than a memory: the cycle has already
established that content living only in a session or a packet does not travel (§Rules promoted,
the packet rule), and a promotion candidate carried in someone's head is the same failure with a
shorter fuse.

Recorded here **without** their supporting evidence duplicated — each cites where the evidence
lives, and the close reads it there.

> **The list's own limit, stated 2026-08-08 (m4 close-b) — it is a list of *noticed* recurrences,
> not of all of them.** Every entry here exists because someone described a finding *as* recurring,
> in a notes file or a packet. A finding that recurred and was never described that way is
> invisible to any sweep of self-reports, including the one that produced rows 4 and 5 below. **No
> exhaustive re-sweep has been attempted**, at this close or before it, so absence from this table
> is not evidence that a class did not recur. The **Instances** column is added for the same
> reason: candidate 1's *one* and candidate 2's *two, two tickets* are different claims, and the
> table previously printed them as if they were the same kind of entry.

| # | Candidate | Instances | Instance | Where the evidence is |
|---|---|---|---|---|
| 1 | **Widen Silent-wrong-answer's stale-state carrier to cover *sibling* state** — a check whose own setup injects state that changes what an *adjacent* check can observe, so the sibling reports a clean result about a condition it never actually tested | **one** — t3 only. Swept for a second at close-a and none found; **below §7's ≥2 bar as a new rule**, which is why it landed as a widening | t3's allowlist matrix: `CLOUDCOST_OPTIMIZATION=1` was exported so entry 5's row would have something to detect; on a DO leg that makes the orchestrator raise at *eval* time, so the `− ANTHROPIC_API_KEY` row never reached the LLM call and reported "still succeeded" — a **false negative in the verification's own matrix**, found only because the result was implausible | `cloudcost/docs/m4-t3-implementation-notes.md:132–136` |
| 2 | **A count taken from a truncated capture, reported as the whole run's.** | **two, two tickets** — the §7 threshold | **(i)** BL-075: a `mix test` result piped through `tail -12`, so *"1 failure"* was recorded with no name and the run was gone (`docs/backlog-2026-06.md:2669`, the row's own *"What is not known — and why"*). **(ii)** m4 t5b r0: a sprint captured with `\| tail -60`, so the packet's *"21 OK, 0 FAIL, 0 WARN"* was a tally over a fragment reported as the run's own — established at m4 t5c's addendum by diffing that capture against `sprint/20260807_213810`. **What unites them:** the count is arithmetically correct *over what was captured*, and nothing in either packet showed the capture was partial. A truncated capture that happened to hide a `[FAIL]` would read identically. | `docs/backlog-2026-06.md:2669` (BL-075); m4 t5c addendum §A |
| 3 | **A packet's sprint section shows the run's full output, or states what it elided and why.** | **n/a — not a recurrence claim.** It governs what a packet carries, so §7's ≥2 bar does not apply to it and it is the only entry here that is not a learning candidate | Every sprint report in this cycle quoted only the `[OK]` lines; the log at `sprint/20260807_213810` shows the run also emits a containment probe, two harness warnings, an orphan-sweep line and an artifact listing that no packet has ever carried. **The arms are the assertions; the output is the evidence.** Candidate 2 is this one's argument in a single instance — the number that was wrong was wrong because the capture was partial, and no reader could have told from the packet. | m4 t5c addendum §C; first applied at m4 t5c r0 packet §7 |
| 4 | **A count replaced without re-checking the claim it hung on** — the *"uniqueness claim produced by observation"* form of Adjacent-case / enumerate-the-class. **Added 2026-08-08 (close-b); it was never entered here** | **three, one lineage** | *"the one seam"* (m1) → *"at least three"* (m2) → a t4b correction asserting a seam predicate over all 54 which the census denies. Each replaced the **number** and inherited the **sentence** it hung on. Carried on BL-074's own row from its filing and read by nothing else | `docs/backlog-2026-06.md` §BL-074, the DONE section's closing paragraph (`:2654–2658`) — its only home before this close |
| 5 | **A count printed beside an enumeration that contradicts it.** **Added 2026-08-08 (close-b); it was never entered here** | **four, two tickets** | t4a §6 — *"Four"* over a list of eight; t4a §2.1 — *"50 items … 21 named / 29 not"*, all three hand-counted, actual 54 and 19/35; t4a §4b — *"the 43"* over rows summing 46, in a file holding 53 items against a stated 50; t4b r2 Edit B — *"12 citations"* where the command returns **13**, the thirteenth being the sentence asserting the count, matching itself. **A fifth instance exists in a t5a session report that is in neither repo and is therefore not evidence** | `cloudcost/docs/m4-t4a-implementation-notes.md:60` and `:41–44`, and §4b **as committed at `53e3c9b`** (corrected in place, so HEAD reads the fixed 46); `cloudcost/docs/m4-t4b-implementation-notes.md:478–481`; the class is named at `:354` |

> **Where candidates 2 and 3 land is itself an open question at this close, and they join it rather
> than assume its answer.** G5b (m4 t5b) established that **absent-is-unknown** was directed to
> `aetheris-agents/CLAUDE.md` by its promotion draft and landed in `../aetheris/CLAUDE.md` — a
> deliberate re-homing, recorded in the closeout's *"Home as landed"* column, but one that leaves an
> agents-side session reading only its own file without the rule. Candidate 3 is a rule about what a
> **packet** must carry, which suggests the agents `CLAUDE.md` beside the packet rule; candidate 2 is
> a Complete-output refinement, which suggests the harness file where that rule already lives.
> **The ritual decides both, and decides them together with where promoted rules land at all.**


**Why this is a widening and not a new rule.** Silent-wrong-answer already covers a check that
reads the wrong thing and reports clean rather than erroring (the command-binding carrier, promoted
at t1a-p). The t3 instance is that shape with the carrier being **state a sibling row injected**
rather than a mis-bound command — the check reads the right thing, in an environment a neighbour
silently changed. The close decides whether that is a distinct enough carrier to name, or whether
naming it dilutes the rule it belongs to — the same question already open for the
substring-vs-field form under §Open for the close item 2, and the two are best decided together.

> **The ritual decided, 2026-08-08 (m4 close-b). All five landed; where they landed, and why the
> "where" stopped being a question.**
>
> The block above says *"The ritual decides both, and decides them together with where promoted
> rules land at all."* It did, and the answer to the third part is that **placement is editorial**.
> No document states a criterion for choosing a repo, and the two recorded divergences (P2 and P7,
> both agents→harness) are what happens in its absence — a criterion inferred from them would be
> inferred from exactly the two data points that went wrong. Instead the **repos rule was widened**
> so that every session reads both files before its first edit (`CLAUDE.md`, §What this repo is).
> With the read universal, a rule living in one repo only is reachable from either, so a promotion
> lands **beside its siblings** and nothing turns on the choice. The promotion record's *landed*
> column is authoritative; a draft's *directed* column is a proposal, and a recorded re-homing is a
> filing choice rather than a defect.
>
> **Five candidates, four entries — the three carriers of rows 2, 4 and 5 are one rule, not three.**
>
> | | Landed | As |
> |---|---|---|
> | rows **2, 4, 5** | `../aetheris/CLAUDE.md` → `Every claim has a truth-maker` | **one third operational form** — *a count is a claim about a population* — carrying all three as named carriers. Three mechanisms, one family; five siblings were not promoted |
> | **§Open item 2** (substring-versus-field) | `../aetheris/CLAUDE.md` → Silent-wrong-answer | a **widening**, immediately after the command-binding carrier the record itself says it belongs to |
> | row **1** (sibling state) | `../aetheris/CLAUDE.md` → Silent-wrong-answer | a **widening**, stating in the entry that it rests on **one** instance |
> | row **3** (packet full output) | `CLAUDE.md` (agents) → §Learning — BL-007 | a **packet rule**, beside the packet rule, stating in the entry that it is not a recurrence-derived learning entry |
>
> Rows 1 and §Open item 2 were **decided together and identically**, which is what both texts asked
> for: named as widenings of the rule they belong to, rather than as siblings that would dilute it.

---

## Close criteria

This cycle is done when t1b through t5c have closed with zero blocking findings, the drift checker
reports zero FAIL and no unexplained WARN, and the milestone-end ritual has run.

**What a close sweep of this document reads** — the answer BL-102 asks for, for a batch that has no
done-when table:

1. Every ticket in §Ticket set, checked against the backlog rows it closes. A row closed in the
   repo and open here, or the reverse, is the defect the sweep exists to catch.
2. Every row in §Rows filed, checked for a DONE section if it closed.
3. §Not established, item by item: resolved, still open, or superseded — and if resolved, where.
4. The decision log, for any decision the implementation diverged from. A divergence is closed by
   changing the code or the decision, never left silent.
5. §Rules promoted, read out of the two `CLAUDE.md` files rather than trusted — a promotion is
   complete only when the entry can be read where it lives.

`Source: this cycle, 2026-08-05 to date. Decision log authored by claude-ui from the cycle's own
ratifications; repo-state sections composed by claude-code at aetheris-agents 009f666 /
aetheris f6fbd82.`
