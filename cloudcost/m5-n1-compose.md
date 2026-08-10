# m5 — the N>1 compose surface

`Opened 2026-08-09. Canonical document for BL-131. Authored by the reviewer
before t1 opens, per hc-consolidation R12.`

## Why this exists

**What this round decides.** BL-131: whether the N>1 compose path is a supported
surface. The row owes a ruling — supported, or removed — and the §Contracts
amendment that follows it. Read `docs/backlog-2026-06.md` → BL-131 for the
subject; it is not restated here.

## Scope

**Shape: two tickets with a gate stop between them.** t1 establishes, read-only,
and stops. The reviewer rules. t2 applies the ruling. **The ruling is not
claude-code's to make, and t1 does not make it.**

> `[Deviation, recorded rather than glossed. R20 covers a reviewer-authored
> **section-scoped** edit; this document's creation is not one, because there was
> no document to scope into. Recorded here as a divergence-with-record, on the
> same footing as m4-5's clause-4 entries: the authoring is the reviewer's per
> R12 and decision 11, and only the edit's shape differs.]`

---

## Sequence

harness consolidation round (closed 2026-08-09, hc-e r9) → **m5 t1** → **the
ruling** → **m5 t2** → BL-132 → provider four.

**BL-074 is not in this round.** BL-131 alone, by the reviewer's scoping ruling
of 2026-08-09. The seam sweep keeps its own row.

**Provider four carries two non-identical gate statements at HEAD** — §Not
established item 1. This round does not reconcile them and does not act on
either.

---

## Ticket set

| Ticket | Subject | State |
|---|---|---|
| **t1** | Establish the N>1 compose surface, read-only, to the point where the ruling can be made | **Opened and stopped at the gate stop** 2026-08-10, r0. Step-1 gate ran: (b) unmoved; (a) **diverges from BL-131 and is not temporal** — three routes reach N>1, not one, and the route-bearing code is byte-unchanged since `6832159`. Continued under the reviewer's mid-ticket ruling of 2026-08-10 that the stop condition is temporal. **E1–E8 all answered**; no ruling made, no behaviour changed. Record: `cloudcost/docs/m5-t1-implementation-notes.md`. **r1** 2026-08-10: verdict on r0 was **APPROVE**; both findings closed without re-running E1–E8 — **F1**, E4(6)'s document sweep run over the harness's full tracked population (2 hits, both LLM-provider, **zero in scope**, three controls plus a case-insensitive guard); **F2**, r0's packet §1/§2 diffed byte-for-byte against the committed file — identical, and the elision's basis corrected to 577 of 634 lines. **F1a** recorded not repaired: E4(6)'s stated `.md` population and its own distribution disagree by one file. Review file: `docs/reviews/m5-cloudcost-t1-review.md`. Still **waits on** the BL-131 ruling, which §Ratified decisions says the reviewer authors into this document at the gate stop, per R12; the resolver is unchanged. |
| **t2** | Apply the ruling; amend §Contracts; dispose the rows that resolve with it | **Not opened, and ready to open.** Anatomy authored 2026-08-09; **completed 2026-08-10** at the ruling edit — **no slot is R13-marked and no `Resolver:` remains in the subsection.** All seven §6 fields plus the step-1 gate are written: the gate stops on *moved* and says so, `Touches` names six paths, the runbook rule states why a docs-only ticket still touches the runbook, and the done-check pins the same pytest spine t1 ran against t1's recorded **386 passed**. The ticket applies **m5-D2** and carries no ruling of its own. Record of the completing edit: `cloudcost/docs/m5-ruling-edit-implementation-notes.md` |

**Ticket anatomy in this document is §6's seven fields plus a step-1 gate. The
gate is not a §6 field.** §6 defines seven fields and no gate. The gate is m4
decision 3, carried by hc-consolidation **R8**. Stated here so that no ticket in
this round cites it as a methodology obligation — `docs/reviews/hc-b-review.md`
Round 0 recorded that citation as a manufactured authority.

**A step-1 gate states the tense of its stop condition.** t1's did not: *"if either
has moved"* admits a temporal reading and a divergence reading, and the ambiguity
was invisible until a divergence appeared that was not temporal. The reviewer ruled
mid-ticket that the temporal reading governed, and added a narrower test on whether
the surface itself differed. t1's gate text stands as written, with the ruling
recorded in `cloudcost/docs/m5-t1-implementation-notes.md`; every gate authored in
this document after 2026-08-10 says whether it stops on *moved* or on *differs*.

**Review files.** R2's own text binds *"every `hc-*` ticket"*, so it does not
literally reach this round. The obligation is
`../aetheris/docs/methodology/milestone-methodology.md` §1 principle 4 and §8, both
unscoped, which are the sections R2 grounds itself in. Cited correctly here after
t1 r1 established it against a round instruction that cited R2 as the source.

**R19 applies.** A session that changes a ticket's state updates its row in the
table above in the same commit.

### t1 — establish the N>1 compose surface (read-only)

**Step-1 gate** *(m4 decision 3, carried by R8 — run before any other work in
the ticket).*

Re-derive at HEAD, from source, the two things BL-131's premise rests on:

- **(a)** the set of routes by which `cloudcost/scripts/compose_report_data.py`
  can receive more than one provider bundle;
- **(b)** how many `--cost` / `--inventory` / `--orphans` triples
  `cloudcost/agents/cloudcost_orchestrator.exs` passes.

Record both with `path:line`. State how a zero result was established as absence
rather than as a failed search. **If either has moved from what BL-131 states,
stop and report before doing anything else** — the row's premise has changed and
the ticket is re-scoped rather than continued. Do not repair the row from inside
the gate.

**Scope.** After this ticket, the evidence the BL-131 ruling needs exists as a
committed artifact in this repo rather than as a derivation inside a closed
cycle's prose. Eight enumerated questions are answered at HEAD, each with its
population named and its enumeration printed. No ruling is made, no behaviour
changes, and no file outside `Touches` is edited.

**Contract refs.**
`cloudcost/milestone.md` §Contracts — C4, C11, and the two pointer blocks that
name BL-131 · `cloudcost/m2-milestone.md` — decision H ·
`docs/backlog-2026-06.md` — BL-131, BL-132, BL-070, BL-119, BL-121 ·
`../aetheris/docs/methodology/milestone-methodology.md` §6 ·
`docs/milestones/hc-consolidation.md` — R8, R12, R13, R19, R21.
These are normative for this ticket and are **not** restated in the prompt.

**Touches.**

- `cloudcost/docs/m5-t1-implementation-notes.md` *(new)*
- `cloudcost/m5-n1-compose.md` — the **t1 row only** in §Ticket set, per R19

Nothing else. Any other path that changes is a deviation and is named in the
implementation notes.

**Do not generate.** No change to any file under `cloudcost/scripts/`,
`cloudcost/tests/`, `cloudcost/templates/`, `cloudcost/agents/`, or to
`cloudcost/tools.json`, `cloudcost/milestone.md`, `cloudcost/runbook.md`,
`docs/backlog-2026-06.md`, or anything in `../aetheris/`. **No ruling, no
recommendation, and no disposition** — including in the notes' own prose. Where
the evidence points one way, say what the evidence is; do not name the direction.

**Runbook update rule.** t1 introduces no environment variable, no startup step,
no configuration key, no operational procedure, and changes the observable
semantics of no command, flag or UI affordance. **No runbook section is in this
ticket's `Touches`, and that is stated here rather than left to inference.** If
the establishment work surfaces an operator-visible gap, record it in the notes
as a finding and leave it; fixing it is not this ticket.

**Done-check.**

```bash
# 1. The offline pytest spine over the cloudcost suite, as a HEAD baseline.
#    Pinned 2026-08-09 by the reviewer. Command: cloudcost/runbook.md
#    §Offline tests. Working directory: the aetheris-agents/ root, per
#    CLAUDE.md §Commands — the runbook's block states no cd and every cd in
#    that file points elsewhere, so the root is not inferable from the
#    runbook alone.
#    RE-RESOLVE BOTH ANCHORS AT HEAD BEFORE RUNNING. Quote each. If either
#    has moved, report it and run what the anchors say now — the pin is an
#    anchor, not an assertion.
python3 -m pytest cloudcost/tests/ -v

# 2. The notes file exists and is non-empty.
test -s cloudcost/docs/m5-t1-implementation-notes.md && echo NOTES_PRESENT

# 3. All eight questions have a section. Must print 8.
grep -c '^### E[1-8] ' cloudcost/docs/m5-t1-implementation-notes.md

# 4. Nothing outside Touches changed.
git status --short
```

**Claude-code prompt.**

> Read this ticket's `Contract refs` and do not restate them. Run the step-1
> gate above first and report its result before continuing.
>
> Then answer the eight questions below in
> `cloudcost/docs/m5-t1-implementation-notes.md`, one `### E<n> — <title>`
> section each, in order. **Every answer is derived at HEAD.** Name the
> population before you count it and print the enumeration beside the count; a
> count without its enumeration is not an answer. Every claim carries
> `path:line`. Every zero carries a positive control. Bind each artifact to the
> command that produced it, never to its position in a listing. Where you cannot
> establish something, say so and say what would settle it — do not fill the gap.
>
> **E1 — Route census.** Every code path by which `compose_report_data.py` can
> receive more than one provider bundle. Source-derived, not carried from any
> document.
>
> **E2 — Invocation census.** Every in-repo invocation of
> `compose_report_data.py` — the orchestrator, the sprint script, the runbook,
> `tools.json`, the test suite, any CI or helper script. For each: the bundle
> count it can produce, and whether it uses the multi-bundle route.
>
> **E3 — Test coverage.** Which tests, if any, exercise more than one bundle.
> Distinguish *a test that passes several bundles* from *a test of the discovery
> function with one bundle* — these are different and the difference is the
> answer. Name the population of test files searched.
>
> **E4 — Blast radius of REMOVE.** Everything that deletes if the multi-bundle
> surface goes: functions, branches, the declared argument and its manifest
> entry, tests, and every sentence in every document that describes
> cross-provider behaviour. Enumerate with `path:line`. Include documents outside
> `cloudcost/`.
>
> **E5 — Blast radius of SUPPORT.** Everything that must be *added* for the
> surface to be supported rather than merely present: tests, a sprint leg,
> runbook text, and the semantics the currency and cap behaviours would then
> have to state. Enumerate what does not exist today; this is a census of
> absences and each one needs its own positive control.
>
> **E6 — The three-state contradiction.** BL-131 tabulates three assertions
> about this surface, each attributed to a different document. For each: locate
> its current text at HEAD with `path:line`, quote it, and state whether HEAD
> still supports it. **Adjudicate nothing** — three quotations and three
> yes/no/moved readings.
>
> **E7 — Decision H's re-derivability clause.** Quote decision H's own sentence
> about a cross-provider total being later re-derivable from the per-provider
> normalized history path, and establish whether that path is written today —
> by which code, on which invocation. This bears on whether *removed* forecloses
> anything, so the answer matters more than its length.
>
> **E8 — Reachability of C4's and C11's stated behaviour.** For each of the two
> contracts separately: **reachable**, **source-only**, or **untested**, with the
> basis stated. This is the two known instances only. **Do not extend the check
> to C1–C15** — that is BL-132's row and taking it here mis-scopes both.
>
> Run the done-check and include its output in the review packet. **End at a
> gate stop**: report, and stop. Do not rule, do not propose t2's shape, and do
> not edit any row in `docs/backlog-2026-06.md`.

### t2 — apply the ruling

**Step-1 gate** *(m4 decision 3, carried by R8 — run before any other work).*
**This gate's stop condition is temporal, and says so.** It stops if something has
*moved* since **m5-D2** was ratified, not if something differs from a document's
description of it.

Re-derive at HEAD:

- **(a)** that the orchestrator still passes exactly one bundle on both of its
  STEP 3 forms;
- **(b)** that C4's and C11's m4 t5b pointer blocks are present in
  `cloudcost/milestone.md` §Contracts and unamended since m5-D2.

Name each section and quote it; state how a zero was established as absence. **If
either has moved since m5-D2, stop and report before doing anything else** — the
ruling's factual basis has changed and t2 is re-scoped rather than continued. Do
not repair the ruling from inside the gate.

**Scope.** After this ticket, the BL-131 ruling is implemented in
`compose_report_data.py` and its declared interface; `cloudcost/milestone.md`
§Contracts C4 and C11 state the post-ruling position rather than the
pre-ruling one; and the rows that resolve with BL-131 carry their dispositions.
What "implemented" means is the ruling's content and is not assumed here.

**Contract refs.** t1's implementation notes · this document's §Ratified
decisions, which will hold the ruling · `cloudcost/milestone.md` §Contracts C4,
C11 · `docs/backlog-2026-06.md` — BL-131, BL-070, BL-119, BL-121 ·
`docs/milestones/hc-consolidation.md` — R13, R19.

**Touches.**

- `cloudcost/milestone.md` — §Contracts **C4** and **C11** only: the cross-provider
  clause in each, and each one's m4 t5b pointer block.
- `cloudcost/scripts/compose_report_data.py` — **the module docstring only.** No
  executable line changes.
- `cloudcost/runbook.md` — the sentence asserting the cross-provider merge is
  now-unreachable pending BL-070.
- `docs/backlog-2026-06.md` — the **BL-070**, **BL-119**, **BL-121**, **BL-131** and
  **BL-132** rows.
- `cloudcost/m5-n1-compose.md` — **t2's row only** in §Ticket set, per R19.
- `cloudcost/docs/m5-t2-implementation-notes.md` *(new)*.

Nothing else. Any other path that changes is a deviation and is named in the
implementation notes.

**Do not generate.** Authorable now, and complete as written: no reachability
work over C1–C15 (BL-132's row); no new provider adapter or provider-four
scaffolding; no edits under `eduloka/`, `rig/`, or `../aetheris/`; no
amendment to any contract other than C4 and C11.

**Runbook update rule.** t2 changes the observable semantics of no command, flag or
UI affordance — no executable line changes. `cloudcost/runbook.md` is nonetheless in
`Touches`, because it carries a *claim* this ruling overturns rather than a
procedure this ruling alters, and a runbook that asserts a superseded premise
misleads an operator exactly as a stale procedure does. **Stated here rather than
left to inference.** If the correction surfaces a second operator-visible claim
resting on the same premise, correct it in the same commit and name it.

**Done-check.**

```bash
# 1. The offline pytest spine — the same pin t1 ran. Re-resolve both anchors at
#    HEAD before running: cloudcost/runbook.md §Offline tests for the command,
#    CLAUDE.md §Commands for the root. Quote each. If either has moved, report it
#    and run what the anchors say now.
python3 -m pytest cloudcost/tests/ -v
#    t2 changes no executable line, so a test count differing from t1's recorded
#    figure is a FINDING, not a pass. Compare against t1's notes and say so either way.

# 2. The declaration is discoverable from all three artifacts a reader opens.
#    Each must return at least one line; a zero is a failed declaration, not a
#    passed check.
grep -n 'm5-D2' cloudcost/scripts/compose_report_data.py
grep -n 'm5-D2' cloudcost/milestone.md
grep -n 'm5-D2' cloudcost/runbook.md

# 3. No executable line of the script changed. Publish this diff and assert that
#    every changed line falls inside the module docstring.
git diff HEAD -- cloudcost/scripts/compose_report_data.py

# 4. Nothing outside Touches changed.
git status --short
```

**Claude-code prompt.**

> Read this ticket's `Contract refs` and do not restate them. Run the step-1 gate
> above first and report its result before continuing.
>
> Apply **m5-D2**, which is ratified in this document's §Ratified decisions. Read it
> there; it is not restated here. Your work is its four numbered declaration
> requirements and nothing beyond them.
>
> **The contracts.** Amend C4's cross-provider currency clause and C11's
> cross-provider cap clause so each states that it describes behaviour no
> orchestrator invocation reaches — source-only by ruling, naming **m5-D2**.
> Discharge each one's m4 t5b pointer block: the pointer said the paragraph was
> *not yet amendable* pending BL-131, and BL-131 has now ruled. **Do not delete the
> pointer blocks** — discharge them in place with a dated note, per decision 7.
> Neither contract's *guarantee* changes; only what it says about reachability.
>
> **The code.** Add to `compose_report_data.py`'s module docstring a statement that
> the cloudcost pipeline invokes this script at one bundle, that N>1 is a
> library-and-CLI capability the pipeline does not use, and where the ruling lives.
> **No executable line changes**, and the done-check publishes the diff to prove it.
>
> **The runbook.** Correct the sentence asserting the cross-provider merge is
> now-unreachable pending BL-070. Reachable-and-uninvoked is the accurate claim.
>
> **The backlog.** Dispose the five rows as m5-D2 states: BL-070's cross-provider
> deletions **not taken**; BL-121's framing resolved; BL-131 closed on the ruling;
> BL-132's two known instances answered so its census need not re-derive them;
> BL-119 stays open and in scope. Use the closure shape the file itself uses —
> derive it from the rows, do not invent one. Each disposition names **m5-D2**.
>
> **m5-D1 governs every citation you write**: section name plus quotation, a line
> number only for a claim about a line, positional claims stamped with the commit
> they were measured at.
>
> Run the done-check and include its output in the review packet. Update t2's row
> in §Ticket set in the same commit, per R19. Do not push.

---

## Ratified decisions

**Both decisions in this section are ratified, and the BL-131 ruling is one of
them.** **m5-D1** is methodological and was made in the course of opening the
round. **m5-D2** is the BL-131 ruling, authored by the reviewer at the gate stop
between t1 and t2 per R12, with its own date, on t1's committed establishment.

> `[corrected in place 2026-08-10 at the ruling edit. This paragraph read "The
> BL-131 ruling is not here yet", said the slot would be filled at the gate stop,
> and called the slot standing open "the correct state before t1 runs". It was
> true when written and false the moment m5-D2 landed below it. **Corrected in
> place under decision 8** — *"Live operational guidance is corrected in place"* —
> rather than left standing under decision 7, whose subject is *"a closed
> record"*. This paragraph is neither: it tells a reader what this section
> contains, so leaving it would leave a wrong instruction standing as the primary
> text, which is the failure decision 8 names. The replaced wording is quoted here
> in full, so the correction loses nothing.]`

### m5-D1 — a citation into a document still being edited names its section and quotes its text; a line number is only for a claim about a line.

A line number into a moving document rots silently. The citation still
resolves — to whatever now occupies the offset — so nothing fails and the
reader is misdirected rather than stopped. This round produced the worked
case: a sweep corrected one anchor after an insert shifted part of a file, and
the correction falsified a standing caveat that had declared every anchor in
that record to be from an earlier commit. The caveat was the workaround; the
citation form is the fix.

A line number is correct where the claim is itself about a line — a count, a
diff hunk, a position, a `file:count` grep output. Everywhere else, name the
section and quote enough text that a reader finds it by search rather than by
offset. This is the form already required of t1's `Done-check` pin. Where the
exempt claim is positional — where an insertion fell, what a count was taken
over — it is stamped with the commit it was measured at, so it reads as history
rather than as a statement about HEAD. An unstamped positional claim is the
census-staleness shape with offsets in place of the total.

**Binds t1 and t2**, whose implementation notes cite into this document and
into the backlog while both are still being edited. Promoted mid-cycle rather
than at the close, per §Carried in's third item.

`Ratified 2026-08-09 at r5 by the reviewer, on claude-code's r4 hold.
Source: the m5 scoping landing, r4's stale-anchor sweep.`

`[Landed as m5-D1, not M1 as specified: M1 is taken as an identifier in
cloudcost/m2-milestone.md (mutations M1–M8) and in
docs/milestones/bl-067-implementation-notes.md. The fallback and its condition
are the reviewer's own, at r5 S4(a).]`

`[Extended 2026-08-09 at r6 with the stamping clause, on claude-code's r5 flag
that the exemption covers a whole document's anchors and said nothing about
their tense.]`

### m5-D2 — BL-131: the N>1 compose surface is retained and bounded. It is a library-and-CLI capability the pipeline does not invoke, and it is declared as such.

**The ruling.** N>1 stays in `compose_report_data.py`. It is not removed, and it is
not made an operator surface. What changes is that it stops being undeclared: the
contracts that describe its behaviour say that no orchestrator invocation reaches
it, and the code says so where a reader meets it.

**Why not removed.** The row's premise does not hold at HEAD, and did not hold when
it was written. t1's step-1 gate and **E1** establish three routes to N>1, not the
one route BL-131 names, and the route-bearing code is byte-unchanged since the
commit the row cites — so the cited derivation was incomplete rather than
overtaken. **E2** and **E3** take the row's three verbs apart: *advertised* is
false, since the three primary flags each declare the repeatable form and the
module's own docstring advertises it; *tested* is false, since N>1 is exercised
across all three routes; and only *invoked* survives — no invocation outside the
test suite produces N>1.

Removal is also not the change the row costed. **E4** enumerates it: not one flag
and a manifest entry, but the repeatable action on the three primary flags, the
directory route entire, and multi-bundle machinery threaded through six section
builders and the payload's own shape — together with the tests that currently
constrain those builders, and two contracts rewritten as superseded.

**Decision H does not require removal.** H forbids a cross-provider roll-up in the
pipeline. The pipeline performs none: the orchestrator passes a single bundle on
both of its STEP 3 forms (**E2**), so H is satisfied at HEAD whether or not
`compose` can accept more. H constrains what the pipeline does, not what the script
can do.

**And the urgency in the row was borrowed from an event H forecloses.** BL-131
sequences itself *"before provider four — the first fan-out is exactly when the
wrong answer starts costing."* Under H there is no fan-out: provider four is a
fourth solo run, and nothing about a fourth provider brings the N>1 path into the
pipeline. This row gates provider four on a decision, not on a risk.

**Why not supported.** **E5** costs it: a sprint leg at N>1, a runbook recipe, a
manifest form that can *supply* more than one — which the manifest has no argument
kind for — an orchestrator-level N>1 test, and settled semantics for C4 and C11
that are unimplemented today. Those are real costs against no invoked use, and a
pipeline capable of a cross-provider report would sit against H rather than beside
it.

**What *bounded* requires, and this is the operative half.** This surface has been
left in place three times without being declared, and each silence produced a row:
BL-070 assumed it dead, BL-131 assumed one route, BL-132 found two contracts
describing a path nothing takes. **A fourth silent retention is the failure this
ruling exists to prevent.** Retention is therefore conditional on the declaration
landing, and the declaration must be reachable from the artifacts a reader actually
opens:

1. **§Contracts.** C4's cross-provider currency clause and C11's cross-provider cap
   clause are amended to state that they describe behaviour no orchestrator
   invocation reaches — **source-only by ruling**, not by accident. Each one's m4
   t5b pointer block is discharged, naming this decision.
2. **The code.** `compose_report_data.py`'s module docstring states that the
   cloudcost pipeline invokes it at one bundle, and points at §Contracts. A reader
   who opens the script to ask whether N>1 is live gets the answer there.
3. **The runbook.** Its sentence asserting the cross-provider merge is
   *now-unreachable* pending BL-070 is corrected. Reachable-and-uninvoked is a
   different claim, and the difference is this round's whole subject.
4. **The backlog.** BL-070's cross-provider deletions are disposed **not taken**.
   BL-121's framing resolves. BL-131 closes on this ruling. BL-132 keeps its row
   with its two known instances already answered, so its census does not re-derive
   them. **BL-119 stays open and is now unambiguously in scope**, because the route
   it concerns is retained.

**What this does not decide.** Whether a cross-provider aggregator is ever built —
H places it outside the pipeline, **E7** establishes it does not exist, and H's own
precondition is satisfied today. Whether N>1 should later become an operator
surface — **E5** is the costing if that is ever asked. C4's minor-unit exponent and
currency-relative tolerance stay filed; they bite only at N>1, which the pipeline
does not reach.

`Ratified 2026-08-10 by the reviewer at t1's gate stop, per R12. Evidence: t1 r0's
implementation notes — the step-1 gate and E1–E8 — and t1 r1's harness-side
population. Source: BL-131, filed 2026-08-07 from m4 t5b's G2 gate-stop.`

---

## Promotion candidates

Candidates recorded here are promoted or dropped at this round's close under
the methodology's §7 ritual; recording one is not promoting it. Where a
candidate binds work that has not run yet, it is promoted mid-cycle instead —
see §Carried in's third item and **m5-D1**.

**A check that structurally cannot observe the failure it stands in for
returns green for the wrong reason.** r4 was told to confirm the harness tree
was clean after running pytest against it, using `git status`. That path is
gitignored in the harness, so `git status` could not have seen the artifact it
was watching for — it would have returned clean whether or not one appeared.
claude-code substituted an mtime capture on both sides of the run, which can
see it. The rule is not *use mtime*: it is that a check states what it can and
cannot observe, and a check standing in for a failure mode outside its own
visibility is reported as a substitution rather than as a pass. Same shape as
a positive control one level up — a positive control shows the search works;
this shows the search can reach. Origin: claude-code at m5 r4, against a check
the reviewer specified.

**An elision justified by "this is inlined above" carries the check that
establishes it, or the diff is not elided.** t1 r0's packet elided a new file's diff
on the ground that its content was inlined verbatim earlier in the same packet. The
assertion was true of most of the file and read as true of all of it: the omitted
remainder included that file's own measurement stamp — the paragraph binding every
citation in the inlined sections to a commit — so the reviewer ratified hundreds of
verbatim lines without the sentence saying what they were measured at, and no reader
of the packet could have told. The close is not *do not elide*: it is that an
elision names the ranges it covers and the lines it does not, and carries the check
that establishes the correspondence. Origin: claude-code at m5 t1 r1, closing a
reviewer finding and finding the stronger form of it.

`[Filed by the reviewer at the m5-D2 ruling edit, 2026-08-10, on t1 r1's flag that
the rule bound every remaining packet in this round and had no owner in this
document. The flag was correct: prose in a packet or a notes file owns nothing.]`

---

## Not established

Carried rather than resolved. Per **R21**, this section holds three kinds of
entry — **(a)** an open question with an owner, which carries a resolver naming
something that exists; **(b)** a carried unknown, which names what would settle
it and invents no owner; **(c)** a decision not to fix, marked `[DECIDED]`.
Each entry states its kind. The per-item prefix is authoritative; this section
carries no total.

> `[corrected in place 2026-08-10 at the ruling edit, under decision 8, as the
> vocabulary sweep owed by §Carried in's second carried rule. Items arrive here
> open and are resolved **in place**: a resolved item keeps its original text and
> its kind letter, gains a dated resolution block, and takes the prefix
> `[RESOLVED]`. So the state prefixes in use are `[RESOLVED]` / `[OPEN]` /
> `[DECIDED]`, of which only `[DECIDED]` marks a *kind*; the other two are states
> an (a) or (b) entry can be in. The opening sentence describes how items arrive,
> not what they all still are — item 2 is resolved. Corrected rather than left
> standing because it is live guidance telling a reader how to read this section.]`

1. **`[OPEN]` (b)** **Provider four carries two non-identical gate statements at
   HEAD.** `cloudcost/m4-consolidation.md` states in one place that provider four
   is gated on the cycle's seam sweep and the harness round, and sequences it in
   another as following BL-131 with no seam sweep named. Neither supersedes the
   other and both are live.
   **Settled by:** a ruling that reconciles them, authored wherever provider four
   is scoped. **No owner** — provider four is not open, and this round declined
   to take BL-074 with BL-131.

2. **`[RESOLVED]` (b)** **BL-131's `Source:` line cites gate items that exist as no
   committed text.** The row attributes its derivation to two gate items of a
   ticket that produced no implementation-notes file; the only in-repo records of
   that ticket are its cycle-document passages and two backlog annotations.
   **Settled by:** nothing in-repo — the derivation is re-run at HEAD instead,
   which is t1's step-1 gate and E1/E2. Recorded so that a later reader does not
   cite those gate items as though they were a document. **No owner.**

   > **`[RESOLVED 2026-08-10 — by t1 r0's step-1 gate and E1/E2, ratified at m5-D2.]`**
   > The item named its own settling route — *"the derivation is re-run at HEAD
   > instead, which is t1's step-1 gate and E1/E2"* — and that re-run has happened. It
   > did not reproduce the uncommitted derivation BL-131 cites: three routes reach
   > N>1, not one, and the route-bearing code is byte-unchanged across the range the
   > row names, so the cited derivation was **incomplete when written** rather than
   > overtaken.
   >
   > **Resolved by replacement, not by recovery.** The gate items the row's `Source:`
   > names still exist as no committed text and never will. What settles the item is
   > that nothing now depends on them: the ruling rests on t1's committed
   > establishment, and the row's own derivation is superseded rather than recovered.
   >
   > `[The prefix changed in place, `[OPEN]` → `[RESOLVED]`, and the kind letter (b)
   > is kept: the item is still a carried unknown whose settling route named no
   > owner, and this section's preamble requires each entry to state its kind.
   > Resolution is a state, not a fourth kind. The original text above stands
   > unrewritten, per decision 7. Shape taken from
   > `docs/milestones/hc-consolidation.md` §Not established, which is the section
   > R21 came from and the only in-repo precedent — this section had no resolved
   > item before now.]`

3. **`[OPEN]` (a)** **Whether decision H's re-derivability clause is satisfied
   today.** Decision H drops the merge-across-clouds while stating that a
   cross-provider total stays later re-derivable from per-provider normalized
   history. Whether that history is written on the invocations the pipeline
   actually makes has not been established, and *removed* forecloses more if it
   is not.
   **Resolver:** t1's **E7**, in this document.

4. **`[DECIDED]` (c)** **Four self-scoped statements in the two m5 record files
   predate content later appended above them.** `cloudcost/docs/m5-scoping-landing-notes.md`
   opens by saying it records the landing *"across two rounds"* and names r1 as
   *"this commit"*; its §Closing note says every figure above was *"derived in this
   session at r1's tree"*; `cloudcost/docs/m5-pin-edit-implementation-notes.md` closes
   with *"Every figure above was derived in this session at the HEAD it names"*,
   enumerating four r3 figures; and that file's r5 section publishes a sweep
   transcript whose offsets are positional claims carrying no stamp of the kind
   **m5-D1** now requires. Each is scoped by its own text to the round that wrote it,
   and every later insertion above them carries its own dated mark, so none states
   something false — but a reader taking the quantifier at face value reads it wider
   than its author meant, and the r5 transcript is the first population m5-D1's
   stamping clause does not reach.
   **Not fixed, deliberately:** r6 repairs false claims only, and there is no further
   round of the scoping landing. Recorded so a later reader knows the scoping was
   read and left, not missed.

---

## Carried in

Inherited from `docs/milestones/hc-consolidation.md` §Milestone summary → §Open
for the next cycle, and in force for this round's §7:

- **An entry's attribution is structural.** An insertion between a claim and its
  `Source:` re-attributes both. An edit that inserts into a structured document
  states where the insertion point falls relative to the surrounding unit's
  boundaries, and a verification that quotes context asserts what the context is.
- **A vocabulary change owes a sweep of everything that speaks it.** When a
  label, status set, field name or prefix changes, derive the population that
  speaks it and check each member in the same commit.
- **m4-5's divergence: promote mid-cycle when a rule binds work that has not run
  yet.** This round does not defer promotion to its close.

**BL-075 arm 2 remains unsatisfiable as written** and is not this round's
subject; carried so it is not rediscovered.
