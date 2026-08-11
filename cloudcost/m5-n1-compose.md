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
| **t1** | Establish the N>1 compose surface, read-only, to the point where the ruling can be made | **Opened and stopped at the gate stop** 2026-08-10, r0. Step-1 gate ran: (b) unmoved; (a) **diverges from BL-131 and is not temporal** — three routes reach N>1, not one, and the route-bearing code is byte-unchanged since `6832159`. Continued under the reviewer's mid-ticket ruling of 2026-08-10 that the stop condition is temporal. **E1–E8 all answered**; no ruling made, no behaviour changed. Record: `cloudcost/docs/m5-t1-implementation-notes.md`. **r1** 2026-08-10: verdict on r0 was **APPROVE**; both findings closed without re-running E1–E8 — **F1**, E4(6)'s document sweep run over the harness's full tracked population (2 hits, both LLM-provider, **zero in scope**, three controls plus a case-insensitive guard); **F2**, r0's packet §1/§2 diffed byte-for-byte against the committed file — identical, and the elision's basis corrected to 577 of 634 lines. **F1a** recorded not repaired: E4(6)'s stated `.md` population and its own distribution disagree by one file. Review file: `docs/reviews/m5-cloudcost-t1-review.md`. Still **waits on** the BL-131 ruling, which §Ratified decisions says the reviewer authors into this document at the gate stop, per R12; the resolver is unchanged. **`[Terminal state appended 2026-08-10 at the close (t3), on §Close criteria clause 4, which found this row understated.]` t1 is CLOSED — approved at r1 and pushed at `40c2d58`, its gate stop reached as designed.** The closing clause above was true when written and false from the moment **m5-D2** was ratified at `a2d63d1`; it is left standing per decision 7 and superseded here rather than rewritten. What t1 waited on has arrived: the ruling was authored at t1's gate stop per R12, t2 applied it, and nothing about t1 is outstanding. |
| **t2** | Apply the ruling; amend §Contracts; dispose the rows that resolve with it | **State — opened and applied 2026-08-10 (r0), reviewed and corrected 2026-08-10 (r1); closed, approved at r1 and pushed at `f6acc9c`.** **Step-1 gate (r0), passed on both arms:** (a) the orchestrator's two STEP 3 forms each pass at most one of `--cost`/`--inventory`/`--orphans`, so one bundle on both, and `git diff a2d63d1 HEAD` on the agent file is empty; (b) both m4 t5b pointer blocks present in §Contracts, and the same diff over `cloudcost/milestone.md` is empty. **Nothing had moved since m5-D2 was ratified**, so the ruling's factual basis held and t2 continued rather than being re-scoped. **What landed (r0) — m5-D2's four declaration requirements:** **C4** and **C11** each gain a *Source-only by ruling* paragraph, with each one's pointer block **discharged in place, not deleted**; `compose_report_data.py`'s module docstring declares one-bundle invocation with **no executable line changed**, proven by AST equality outside the docstring rather than by reading the diff; `cloudcost/runbook.md`'s *now-unreachable* sentence corrected to reachable-and-uninvoked. **Five rows disposed:** **BL-070** not taken — its Done-when clause 4 corrected in place, since nothing is resolved-by-deletion; **BL-121** framing resolved and closed; **BL-131** closed on the ruling; **BL-132** and **BL-119** annotated and left open, **BL-119** gaining the **BL-136** cross-reference and no other row gaining one. **r1 — verdict APPROVE, one finding.** **F1:** §Open items still carried *"unreachable while DO is the only provider"*, restating as a premise the *"live at the first fan-out"* reading t1's **E1** killed; r0 was right to decline it as outside `Touches`, and recording it in BL-070 did not discharge it, BL-070 being DONE. **The reviewer amended `Touches`** — the `cloudcost/milestone.md` bullet gains **§Open items**, the scoping gap being the reviewer's — and the claim is corrected in that authority: reachable and uninvoked, **reachability not a function of provider count**, the eyeball still owed by the first ticket making either path reachable *from the pipeline*. **The second-claim sweep** owed on that file — 18-term vocabulary, 42 hits, control by re-finding both known sites — returned **one further hit on the same premise**, the cross-currency aggregation item's *"live at the first fan-out"* over BL-070's own four deferred sites, corrected in the same commit; and **two staleness items reported not fixed**, outside the premise and so outside what the amended bullet authorises. Review file: `docs/reviews/m5-cloudcost-t2-review.md`. **Done-check, both rounds: 386 passed**, identical to t1's recorded figure, as a docs-and-docstring ticket requires; no executable line changed at r1 either. Record: `cloudcost/docs/m5-t2-implementation-notes.md`. **Provenance of the ticket text itself:** anatomy authored 2026-08-09 and **completed 2026-08-10** at the ruling edit — **no slot R13-marked, no `Resolver:` left in the subsection** — with all seven §6 fields plus the step-1 gate written: the gate stops on *moved* and says so, `Touches` names six paths, the runbook rule states why a docs-only ticket still touches the runbook, and the done-check pins the same pytest spine t1 ran against t1's recorded **386 passed**; the ticket applies **m5-D2** and carries no ruling of its own (record: `cloudcost/docs/m5-ruling-edit-implementation-notes.md`). **Amended 2026-08-10 at the reviewer edit, four fields** — `Scope` rewritten to name the four artifacts the ruling lands in and to state the manifest out of scope by decision rather than by omission; `Contract refs` re-tensed and extended with **m5-D2**, decision H, **BL-132** and **BL-136**; the `docs/backlog-2026-06.md` bullet in `Touches` gains **BL-136** (still six paths); and the `Claude-code prompt`'s backlog paragraph gains the BL-136 cross-reference instruction (record: the same file, §r1). **Further amended at t2 r1**, one field, as above. |
| **t3** | The close: §7's ritual, the close criteria, and the milestone summary | **State — opened and closed 2026-08-10 (r0); both pushes held pending review.** **Step-1 gate, passed on both arms, stop condition temporal against t2 r1:** (a) every m5 commit returns `origin/main` under `git branch -r --contains`, and `HEAD` equals `origin/main` — t2's row states a terminal state, **t1's does not**, but the row is byte-unchanged since before t2 r1, so this is a *differs* and not a *moved*; the gate continued and clause 4 took it; (b) zero of the three §Promotion candidates entries carries a disposition, established by a positive-vocabulary grep with its control in `docs/milestones/hc-e-implementation-notes.md`, and §Carried in still names the preceding cycle's entries item-for-item. **What landed — the six clauses in order:** **1** three candidates promoted on three separately-stated grounds (analogy; bar-does-not-apply; below-bar-by-ratification), the last two ruled by the reviewer on the human's referral; **2** two carried-in candidates promoted and one already promoted, and the prior-claims census run over a command-derived population — **seven of seven present, nothing absent, no census promotion owed**; **3** §Not established passed on all four arms, result recorded in the section; **4** **t1's row corrected** — its terminal state appended, the superseded clause left standing per decision 7; **5** `drift_check --strict` post-commit **8 PASS · 0 FAIL · 4 WARN** (pre-commit 2), all four the declared `project_knowledge` exemption and named, with a finding that `cloudcost/runbook.md` states no invocation; **6** §Milestone summary written. **One row filed: BL-137**, the §Open items freshness census. **Beyond the done-check:** the harness gate set ran off-territory at `2ef0517` and is green — `deps.get`, `hex.audit`, `compile --warnings-as-errors`, `format --check-formatted`, `credo --strict`, `test` (972 tests, 0 failures) — with **`mix dialyzer` deferred, not skipped**, on a stated trigger. **Done-check: 386 passed**, identical to t1's and t2's recorded figure; no executable line changed anywhere. Record: `cloudcost/docs/m5-t3-implementation-notes.md`. **Provenance of the ticket text:** anatomy authored 2026-08-10 by the reviewer before t3 opened, per R12, with no slot R13-marked. **r1** 2026-08-10: verdict on r0 was **APPROVE**, one finding, and the six clauses were not re-run. **F1** — r0's §8 flag half accepted: *a ticket's scoping is authoritative over a ticket's judgement* **stays declined** on a checked premise (§6's `Touches` field and §9's failure-mode table carry it in the methodology's own words), and *a finding recorded inside a closed row is a record, not an executor* is **promoted as one clause on the existing deferred-finding entry**, with that entry's `Source:` extended rather than joined by a second — a precision on a rule never engages §7's bar. **The parent rule is in the agents `CLAUDE.md` only, not both repos**, established with a control; that falsifies a sentence in `docs/reviews/m5-cloudcost-t2-review.md`, which is committed, pushed and a closed round's record, so it is recorded rather than edited — this round's own ratified-artifact rule applied to itself. **`[Corrected by pointer 2026-08-11 at the m5 record-correction edit, which does not reopen m5.]` The ratified-artifact rule was not what put that edit out of reach** — it governs *how* a record is corrected, never *whether*, and a review file is a record; `Touches` is what put it out of reach, and declining was right on that ground alone. Full correction at `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → *The one claim that does not hold*; the location claim it also names is corrected at `cloudcost/docs/m5-t2-implementation-notes.md`. **§Milestone summary corrected** in the same commit, its *"Neither is promoted here"* superseded by a dated block, since leaving it would have been this round's recurring one-artifact-corrected-another-not shape a fourth time. **G2, read-only and changing nothing:** the manifest refresh is **(a) a documented procedure with an owner** — `prompts/bl-002-refresh-project-knowledge.md`, trigger *"milestone end, or before any handoff session"*, upload half explicitly the human's — **no generator script exists** in either repo, and persistent staleness is **by design up to the export boundary**, which is the enforcement point. **The trigger has therefore fired on this round**, and whether a row is owed is the reviewer's call, reserved by the instruction. **Done-check items 1 and 5 re-run: 386 passed**, unchanged; items 2–4 are r0's and were not re-run. Review file: `docs/reviews/m5-cloudcost-t3-review.md`. **Both repos pushed at r1.** |

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

**A review file is not a `Touches` path, and landing one is not a deviation.** It is a
standing obligation on every ticket round in this document, discharged in the round's
own commit, and both t1 and t2 named it as a deviation because this sentence did not
exist. Declared once here rather than re-declared per round. A ticket's `Touches` still
governs everything else, and the round that established the distinction is the round
that proved why: t2 r1 declined to widen its own scoping unasked, correctly.

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

**Scope.** After this ticket the BL-131 ruling is implemented where a reader meets
it: `cloudcost/milestone.md` §Contracts **C4** and **C11** state that their
cross-provider clauses describe behaviour no orchestrator invocation reaches;
`compose_report_data.py`'s module docstring says the pipeline invokes it at one
bundle; `cloudcost/runbook.md` no longer asserts the merge is unreachable; and the
backlog rows that resolve with BL-131 carry their dispositions. **No executable line
changes, and the declared interface does not change** — the manifest is out of scope
by decision, not by omission, per `Do not generate`.

**Contract refs.** This document's §Ratified decisions — **m5-D2**, which this
ticket applies · t1's implementation notes,
`cloudcost/docs/m5-t1-implementation-notes.md`, for the establishment m5-D2 rests on
· `cloudcost/m2-milestone.md` §H · `cloudcost/milestone.md` §Contracts **C4**,
**C11** · `docs/backlog-2026-06.md` — **BL-070**, **BL-119**, **BL-121**,
**BL-131**, **BL-132**, and **BL-136**, the row filed at the reviewer edit of
2026-08-10 · `docs/milestones/hc-consolidation.md` — **R13**, **R19**. Normative for
this ticket and not restated in the prompt.

**Touches.**

- `cloudcost/milestone.md` — §Contracts **C4** and **C11**: the cross-provider clause
  in each, and each one's m4 t5b pointer block. **And §Open items**: any claim there
  resting on the reachability premise **m5-D2** overturns.
  *(§Open items added 2026-08-10 by the reviewer at t2 r1, on t2 r0's flag. The field
  as authored named §Contracts only and missed a third site in the same file carrying
  the same premise — the reviewer's scoping gap, not the ticket's.)*
- `cloudcost/scripts/compose_report_data.py` — **the module docstring only.** No
  executable line changes.
- `cloudcost/runbook.md` — the sentence asserting the cross-provider merge is
  now-unreachable pending BL-070.
- `docs/backlog-2026-06.md` — the **BL-070**, **BL-119**, **BL-121**, **BL-131**,
  **BL-132** and **BL-136** rows.
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
> Then cross-reference **BL-136** — the cross-provider summary row filed 2026-08-10 —
> from **BL-119**'s row, since BL-119's subject is what BL-136 surfaces, and from
> nowhere else. **Do not** cross-reference it from BL-070 or BL-131: this ticket
> disposes both, and a new pointer into a disposed row is noise.
>
> **m5-D1 governs every citation you write**: section name plus quotation, a line
> number only for a claim about a line, positional claims stamped with the commit
> they were measured at.
>
> Run the done-check and include its output in the review packet. Update t2's row
> in §Ticket set in the same commit, per R19. Do not push.

### t3 — the close

**Step-1 gate** *(m4 decision 3, carried by R8 — run before any other work).* **This
gate's stop condition is temporal, and says so.** It stops on *moved*, not on *differs*.
Reference point: t2 r1, the last commit before this ticket.

Re-derive at HEAD:

- **(a)** that t1's and t2's rows in §Ticket set both state a terminal state, and that
  both tickets' commits are on the remote;
- **(b)** that no entry in §Promotion candidates already carries a promotion
  disposition, and that §Carried in still names the entries inherited from the
  preceding cycle.

Name each section and quote it; state how any zero was established as absence. **If
either has moved since t2 r1, stop and report** — the close's input set has changed and
t3 is re-scoped rather than continued.

**Scope.** After this ticket the round is closed: every promotion candidate — this
round's and the ones carried in — is promoted or dropped with §7's test applied and its
result stated, every promoted entry has been read back out of its destination file, the
preceding cycle's promotion claims have been censused against both `CLAUDE.md` files, the
drift checker has run, and §Milestone summary states what shipped and what stays open. No
behaviour changes and no contract is amended.

**Contract refs.** `../aetheris/docs/methodology/milestone-methodology.md` **§7** —
the ritual, all five steps, and the *"review files are not the only input"* clause ·
this document's **§Close criteria**, **§Promotion candidates**, **§Carried in**,
**§Not established**, **§Ratified decisions** (m5-D1, m5-D2) ·
`docs/milestones/hc-consolidation.md` — **R19**, **R20**, **R21** · both repos'
`CLAUDE.md` learning sections. Normative and not restated in the prompt.

**Touches.**

- `cloudcost/m5-n1-compose.md` — §Promotion candidates (dispositions), §Not established
  (clause 3's result), §Ticket set (t3's row per R19, and any row clause 4 finds
  understated), §Milestone summary *(new)*.
- `CLAUDE.md` — the learning section, for entries promoted into the agents repo.
- `../aetheris/CLAUDE.md` — the learning section, for entries promoted into the harness.
- `docs/backlog-2026-06.md` — **one new row**, the §Open items freshness census
  described in the prompt.
- `cloudcost/docs/m5-t3-implementation-notes.md` *(new)*.

Nothing else. Any other path that changes is a deviation and is named. The round's
review file is not a `Touches` path — see §Ticket set's conventions.

**Do not generate.** No amendment to any contract in `cloudcost/milestone.md`; no change
to any executable line anywhere; no reachability work over C1–C15; no edit to a
disposed backlog row; no new `m5-D<n>` decision — the round's decisions are ratified and
the close records, it does not rule. **Do not fix the two §Open items staleness findings
t2 r1 reported** — they are the new row's subject, and fixing them needs adapter reads
this ticket does not do.

**Runbook update rule.** t3 introduces no environment variable, startup step,
configuration key or operational procedure, and changes the observable semantics of no
command, flag or UI affordance. **No runbook section is in `Touches`, and that is stated
rather than left to inference.** If the close surfaces an operator-visible gap, record it
as a finding and file it; do not fix it here.

**Done-check.**

```bash
# 1. The offline pytest spine — the same pin t1 and t2 ran. Re-resolve both anchors at
#    HEAD before running (cloudcost/runbook.md §Offline tests for the command,
#    CLAUDE.md §Commands for the root), quote each, and if either has moved report it
#    and run what the anchors say now. A count differing from t1's and t2's recorded
#    figure is a FINDING, not a pass — t3 changes no executable line.
python3 -m pytest cloudcost/tests/ -v

# 2. Every promoted entry reads out of its destination file. For each entry promoted,
#    grep its rule's opening words in the file it was promoted into and quote the hit
#    WITH ITS SURROUNDING LINES — from the file, never from the packet. State the
#    pattern you used per entry. A promotion that cannot be read back is not promoted.

# 3. The drift checker. DERIVE its invocation from cloudcost/runbook.md or CLAUDE.md
#    and record the exact command beside its output. Do not invent one; if neither
#    document states it, report that as a finding and record what you ran and why.

# 4. Every §Promotion candidate carries a dated disposition. State the count of entries
#    in the section and the count carrying a disposition; they must be equal, and both
#    are derived by enumeration with the enumeration printed.

# 5. Nothing outside Touches changed.
git status --short
```

**Claude-code prompt.**

> Read this ticket's `Contract refs` and do not restate them. Run the step-1 gate above
> first and report its result before continuing.
>
> Then run §Close criteria's six clauses in order, reporting each clause's result
> whether or not it produced an edit.
>
> **On clause 1 and clause 2 together.** §7's input is not only the review files — its
> own text says so. The population you weigh is: this document's §Promotion candidates,
> the entries §Carried in names from the preceding cycle, this round's two review files,
> and the implementation-notes files of t1, t2 and the reviewer edits. Derive that
> population with a command and print the enumeration before weighing it. For each
> candidate state its instances, whether §7's ≥2 bar is met, and the disposition. Where
> instances are reviewer-edit rounds rather than tickets, **say so and rule explicitly**
> — a round is not a ticket and the difference is the reviewer's to be told about, not
> yours to smooth.
>
> **On the promotion format.** §7 step 2 fixes it: a bold one-line rule, one to three
> sentences of why, and a `Source:` naming where it came from. Read the destination
> section's own established shape before writing and follow it. **§Carried in's first
> rule binds you here more than anywhere** — an insertion between a claim and its
> `Source:` re-attributes both, and the preceding cycle recorded three promotions
> landing inside the wrong entry. State where each insertion point falls relative to the
> surrounding entry's boundaries, and assert what the surrounding context is rather than
> quoting it.
>
> **On the prior-claims census.** Every item in the preceding cycle's promotion block is
> checked against both `CLAUDE.md` files, not the ones that look unfamiliar. Two found by
> eye is not a census — enumerate the block and check each member.
>
> **File one backlog row**: a freshness census over `cloudcost/milestone.md` §Open items.
> Its subject is items whose trigger has already fired or whose framing predates adapters
> that have since shipped — t2 r1 reported two, the recency-modifier item and the
> orphan-filename item, and named the shape. The row states that neither rests on the
> premise m5-D2 overturned, that settling either needs adapter reads, and that the two
> reported instances are a starting population and not the census. Derive the row number
> and the placement from the file. **m5-D1 governs every citation you write.**
>
> **Write §Milestone summary** as clause 6 requires. It states what shipped, what each of
> the six clauses found, and what stays open with why that is correct. It carries no
> total over §Not established — the per-item prefixes are authoritative.
>
> Run the done-check and include its output in the review packet. Update t3's row per
> R19 in the same commit. **Land the harness commit first if the harness is touched**, per
> the round's cross-repo ordering, and hold both pushes.

`Anatomy authored 2026-08-10 by the reviewer, before t3 opens, per R12. No slot is
R13-marked: every field is authorable now, because the close's inputs are all committed.`

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
left in place before without being declared, and each silence produced a row:
BL-070 assumed it dead, BL-131 assumed one route, BL-132 found two contracts
describing a path nothing takes. **Another silent retention is the failure this
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

`[Corrected 2026-08-10 at the reviewer edit r1 (Y3b), on the day of ratification and
before t2 opened. The text above read *"has been left in place three times without
being declared"* and *"A fourth silent retention is the failure this ruling exists to
prevent."* The count was a characterisation rather than a countable fact — the rows
named beside it are the evidence and are checkable, the number was not — and removing
it applies the reviewer's own standing rule that an authored spec asserts no checkable
specific. The claim is unchanged; only the count is gone. Original wording recorded
here per decision 7, and in full at §r1 of
cloudcost/docs/m5-ruling-edit-implementation-notes.md.]`

**What this does not decide.** Whether a cross-provider aggregator is ever built —
H places it outside the pipeline, **E7** establishes it does not exist, and H's own
precondition is satisfied today. Whether N>1 should later become an operator
surface — **E5** is the costing if that is ever asked. C4's minor-unit exponent and
currency-relative tolerance stay filed; they bite only at N>1, which the pipeline
does not reach. **The first of those now has an owner:** **BL-136**, filed at the
reviewer edit of 2026-08-10, carries H's consequent — a read-only reader over the
per-provider snapshots `persist_history` already writes — as a backlog row rather
than as an undecided, unowned question.

`Ratified 2026-08-10 by the reviewer at t1's gate stop, per R12. Evidence: t1 r0's
implementation notes — the step-1 gate and E1–E8 — and t1 r1's harness-side
population. Source: BL-131, filed 2026-08-07 from m4 t5b's G2 gate-stop.`

`[Appended 2026-08-10 at the reviewer edit r1, after this decision was ratified
earlier the same day. The sentence naming BL-136 is not part of what was ratified at
t1's gate stop: the ruling recorded the aggregator question as undecided and unowned,
and the row that owns it was filed afterwards. The clause's own date does not
distinguish it — the ruling and the row share 2026-08-10 — which is why this note
exists rather than being redundant with it. Recorded per decision 7; the before and
after are at §r1 of cloudcost/docs/m5-ruling-edit-implementation-notes.md.]`

---

## Close criteria

Six clauses. Each is checkable, and the close reports the result of each whether or not
it produced an edit — a clause that produced nothing is a result, not a silence.

1. **Every entry in §Promotion candidates is promoted or dropped**, with §7's
   *recurred on ≥2 tickets* test applied and its result stated per entry. **Where an
   entry's instances are reviewer-edit rounds rather than tickets, say so** and state
   whether the bar is met, met by analogy, or not met — do not silently count a round
   as a ticket. A candidate deliberately left recorded is a decision and is marked as
   one, not left unmarked.
2. **The entries carried in from the preceding cycle are weighed on the same terms.**
   §Carried in names them and says they are in force for this round's §7; they are its
   input, not its background. And §7's prior-claims census runs: any document from the
   preceding cycle claiming learnings were promoted is checked against **both**
   `CLAUDE.md` files, and anything absent is promoted now with a `Source:` naming the
   cycle it came from and the fact that it was found absent.
3. **Every §Not established item's state reads from its own prefix**, each `[OPEN]`
   item names what would settle it, and each `[OPEN]` (a) item's resolver names
   something that exists. The section carries no total.
4. **Every row in §Ticket set states its terminal state**, and no row's state is
   inferable only from a record file.
5. **The drift checker runs and its result is recorded** — the command derived, not
   invented, and published with its output.
6. **§Milestone summary is written**: what shipped, what the close's clauses found,
   what stays open and why that is correct.

`Authored 2026-08-10 by the reviewer, before t3 opens, per R12.`

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

`[A second instance, recorded 2026-08-10 at r3. The reviewer's r2 instruction derived
a sweep population from a single diff across a commit range in which the text being
swept was created. A range diff renders text created inside it as added, never as
changed, so the derivation was structurally unable to see any change within that text
— including the instance the sweep was commissioned to find. Run as written it would
have returned a clean "no second instance". claude-code corrected the granularity to
a per-commit extraction over the same endpoints, reported the correction, and found
two. Same shape as the entry above, one level over: the check was blind not to a file
it could not read but to a kind of change its method could not represent.]`

**`[PROMOTED 2026-08-10 at the m5 close (t3), under §Close criteria clause 1.]`**
**Instances: three, and all three are reviewer-edit rounds rather than tickets** — the
scoping landing r4 (the gitignored `git status`), the ruling edit r3 (the range diff,
recorded in the block above), and the close-anatomy edit r2 (a grep for one word standing
in for a flag), which that record's §*The third instance, and where it goes* routed here as
further input rather than filing as a fourth candidate. A fourth item is an **application,
not an instance**: m5 t1 r0's done-check item 4 substituted an mtime capture for a
`git status` structurally blind to `cloudcost/output/`, and named the substitution — the
rule binding a ticket, which is evidence it reaches ticket work.
**§7's ≥2-*ticket* bar: met by analogy, and the analogy is ruled rather than smoothed** —
a reviewer-edit round is a session that changes the repo on the same terms a ticket does,
and the count above is a count of rounds. Had the bar been read literally the entry would
have been dropped on a technicality about the word *ticket*, which is not what the bar is
for. **Destination:** `../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns →
*Silent-wrong-answer*, as a sub-entry placed after *Sibling state* and before that entry's
through-line paragraph — the candidate's own text puts it one level above the positive
control, and the positive-control rule lives inside that entry.

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

**`[PROMOTED 2026-08-10 at the m5 close (t3), under §Close criteria clause 1. The bar does
not apply.]`** **One recorded instance** — t1 r0's packet — **and the count is not the
basis.** §7's ≥2 is a *recurrence* filter, and this is not a recurrence-derived rule: it
extends the already-promoted packet rule in the agents `CLAUDE.md` §Learning — BL-007,
*"A packet's sprint section shows the run's full output, or states what it elided and
why"*, whose own `Source:` records it as *"promoted as a packet rule, not as a
recurrence-derived learning entry"*. The bar is therefore **not met because it does not
apply**, and that is what is recorded — **not an exception to it**. The distinction is not
pedantry: an entry written as an override teaches that the bar bends, and this one does not
bend it. **Destination:** that same section, immediately after the parent entry, so a
reader meets the extension where the rule it extends already is. Duplication into the
harness file was considered and declined — the packet-rule family lives agents-side, and
the two files are near-duplicates with no byte-identity check in either the repos or
`drift_check`. Ruled by the reviewer on the human's referral of the question at the m5
close.

**An unpushed artifact may be corrected in place; a ratified one may not, and the
difference is what the artifact's authority rests on.** This round corrected several
unpushed records in place, arguing each time that a dated supersession block would
preserve a reading history no reader ever had. That argument is sound for a record of
a session's own work, whose claims become meaningful when someone reads them. It does
not reach a ratified decision: its authority is the act of ratification rather than
its publication, so a reader citing it later is entitled to know its text is what was
ratified, and cannot learn that from a notes file they have no reason to open. The
rule is not *never correct in place* — it is that the licence comes from the
artifact's kind, not from its push state. Origin: claude-code at the m5 reviewer edit
r1, flagging its own compliance with a reviewer instruction that pointed the other
way.

`[Filed by the reviewer at r2, 2026-08-10, on that flag. The flag is the harder kind
to raise — the session had done exactly what it was told, and said so anyway.]`

**`[PROMOTED 2026-08-10 at the m5 close (t3), under §Close criteria clause 1. Below §7's
bar, by explicit ratification.]`** **One recorded instance** — the m5 reviewer edit r1 —
**and the honest word is one.** A later round reading this rule and finding it silent on a
case would be an application, not a second finding, and the `Source:` must not blur the
two. **The ground, stated because "the human said so" is not a reason:** §7's bar is a
frequency test, and frequency is the wrong filter for a rule whose whole subject is a
failure that bites rarely and irreversibly. Silently altering a ratified decision is not a
defect that recurs its way to attention — it recurs by going unnoticed. A rule costing three
sentences that forecloses a class of undetectable failure earns an entry at one instance;
the same argument would not carry a finding about a *subject*, which is what the bar is
there to filter. Recorded on **BL-007's exception form** so the override is auditable, with
the ground written into the entry itself rather than only here.
**Destination:** `../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns, in the
record-integrity cluster immediately after *A claim that lands in the same commit as the
thing that would make it true…*; the credential-provenance rule further down that section
carries the same below-bar ground from the other direction and is named there as the form
precedent. Placement is by subject, the precedent by form. Duplication into the agents file
was considered and declined on the same mirror grounds as the entry above. Ruled by the
reviewer on the human's referral of the question at the m5 close.

`[Pointer added 2026-08-11 at the headline-correction edit. **This candidate's headline
and its closing clause state the rule in wording the promoted entry no longer uses.**
The entry's headline now reads *"An artifact's kind decides how a correction is made;
its push state decides only whether the correction may be silent"* — because *"in
place"* carried two senses, and because denying push state any force is true of a
ratified decision and false of a record. **The candidate is not rewritten**: it is what
was filed, and a candidate that changes to match what it became stops being evidence of
what was ratified. Read the promoted entry in harness `CLAUDE.md` for the operative
wording, and its dated block for the diagnosis. **One thing this candidate got righter
than the promotion did**, worth noting rather than burying: its body already said *"The
rule is not never correct in place"* — the disambiguation was present at filing and was
lost in the headline it was compressed into.]`

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
> not what they all still are — read each item's own prefix for its current state.
> Corrected rather than left standing because it is live guidance telling a reader
> how to read this section.]`

> `[amended 2026-08-10 at the reviewer edit, as the vocabulary sweep owed by item
> 3's prefix change. The block above closed *"— item 2 is resolved"*, and item 3
> resolved in the same section on the same day, so the clause named a state of the
> section that had already moved. It now reads *"read each item's own prefix for its
> current state"* — the form `docs/milestones/hc-consolidation.md` §Not established
> uses, and one that carries no count to decay. Nothing else in the block changed.]`

> `[§Close criteria clause 3 ran over this section at the close, 2026-08-10 (t3), and
> **passed on all four arms**. Recorded because a clause that produced no edit is a result,
> not a silence. **(i) Every item's state reads from its own prefix** — the four entries
> carry `[OPEN]` (b), `[RESOLVED]` (b), `[RESOLVED]` (a), `[DECIDED]` (c), each stating its
> kind per R21, enumerated from the section rather than counted from memory. **(ii) The one
> `[OPEN]` item names what would settle it** — item 1's *"a ruling that reconciles them,
> authored wherever provider four is scoped"* — and, being kind (b), correctly invents no
> owner. **(iii) `[OPEN]` (a) items: zero**, and the zero is read off the same enumeration
> as (i) rather than from a search that found nothing, so it is absence and not a failed
> query; the section's only (a)-kind entry is item 3, and it is `[RESOLVED]`, so the
> population the arm quantifies over is empty rather than unexamined. **Arm (iii) is the one
> that could have passed for the wrong reason** — a grep for `[OPEN]` (a) returning nothing
> is indistinguishable from a broken grep, which is why it is derived from the printed
> prefix enumeration instead. **(iv) The section carries no total**, per its own preamble,
> and this block adds none — it states what was checked, not how many items exist.]`

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

3. **`[RESOLVED]` (a)** **Whether decision H's re-derivability clause is satisfied
   today.** Decision H drops the merge-across-clouds while stating that a
   cross-provider total stays later re-derivable from per-provider normalized
   history. Whether that history is written on the invocations the pipeline
   actually makes has not been established, and *removed* forecloses more if it
   is not.
   **Resolver:** t1's **E7**, in this document.

   > **`[RESOLVED 2026-08-10 — by t1 r0's E7, ratified at m5-D2, and owned onward by
   > the row filed at this edit.]`** The item named its resolver as t1's **E7**, and E7
   > has reported. H's precondition is satisfied today by the live pipeline for all
   > three providers: the per-provider normalized snapshots H names are written on
   > every orchestrator run, in the layout H specifies, established by execution rather
   > than by reading.
   >
   > **Both halves are answers, and only one was ever the question.** The item asked
   > whether the clause is *satisfied*, and the precondition is. That H's consequent —
   > the thin read-only aggregator — is not built is not an unresolved question but an
   > unbuilt artifact, and it now has a backlog row, **BL-136**, rather than an open
   > item. m5-D2's *what this does not decide* names that row.

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

---

## Milestone summary

`Written at t3, 2026-08-10, per §Close criteria clause 6 and §7's final step. Placement
derived: this section closes the document, which is where`
`docs/milestones/hc-consolidation.md` `puts its own §Milestone summary — after
§Promotion candidates and last in the file. It carries no total over §Not established;
the per-item prefixes there are authoritative.`

### What shipped

**The BL-131 ruling, and the declaration that makes it conditional.** **m5-D2**: the N>1
compose surface is **retained and bounded** — a library-and-CLI capability the pipeline does
not invoke, declared as such where a reader meets it. Not removed, and not made an operator
surface.

- **t1** established the surface read-only at HEAD: **three** routes to N>1 where BL-131
  named one, the route-bearing code byte-unchanged since the commit the row cites, and E1–E8
  answered with each population named and each enumeration printed. It made no ruling, which
  was its design.
- **The ruling edit** authored m5-D2 at t1's gate stop per R12, took BL-131's three verbs
  apart — *advertised* false, *tested* false, only *invoked* surviving — and established that
  decision H forecloses the fan-out BL-131 borrowed its urgency from.
- **t2** applied m5-D2's four declaration requirements: C4 and C11 declared **source-only by
  ruling** with their m4 t5b pointer blocks discharged in place, `compose_report_data.py`'s
  module docstring stating one-bundle invocation with **no executable line changed**, the
  runbook's *now-unreachable* claim corrected to reachable-and-uninvoked, and five backlog
  rows disposed. Its r1 corrected two further §Open items claims resting on the same premise.
- **t3** closed the round: three promotion candidates and two carried-in candidates disposed
  into both `CLAUDE.md` files, the prior-claims census run, and this summary.
- **Two rows filed**, both owning questions this round surfaced rather than settled:
  **BL-136** (decision H's consequent — a read-only cross-provider summary over the
  per-provider snapshots `persist_history` already writes) and **BL-137** (the §Open items
  freshness census).

**Behaviour is unchanged end to end.** `python3 -m pytest cloudcost/tests/ -v` returns
**386 passed** at t1, at t2 both rounds, and at t3 — the same figure a docs-and-docstring
arc requires, and the one number that would have caught an accidental edit.

### What the close's six clauses found

| Clause | Result |
|---|---|
| **1** — §Promotion candidates | **Three entries, three promotions, three different grounds** — stated per entry rather than applied uniformly. *Blind check*: three instances, **all reviewer-edit rounds rather than tickets**, §7's bar met **by analogy** and the analogy ruled explicitly. *Packet elision*: one instance, and the **bar does not apply** — a packet rule is not recurrence-derived, so this is not an exception to §7. *Unpushed-vs-ratified*: one instance, **below the bar and promoted by explicit ratification** on BL-007's exception form, with the ground written into the entry. Entry count 3, disposition count 3. |
| **2** — carried-in entries + prior-claims census | **Two promoted, one already promoted.** *An entry's attribution is structural* and *promote mid-cycle* both clear the bar and landed harness-side; *a vocabulary change owes a sweep* was promoted at hc-e and needed no action — stated as a result, and this round applied it twice. **The census: population derived by command, not by eye** — the preceding cycle produced **no handoff**, so the carrier that bit at the m3 close does not exist here; the two documents claiming promotion are `hc-consolidation.md` §Milestone summary and `hc-e-implementation-notes.md` §37/§38. **All seven claims present, each in the file its claim names, with a positive and a negative control. Nothing absent, so the census produced no promotion.** |
| **3** — §Not established | **Passed on all four arms**, recorded in the section itself because a clause that produced no edit is a result. The load-bearing arm — *zero `[OPEN]` (a) items* — is derived from the printed prefix enumeration, not from a grep that found nothing. |
| **4** — §Ticket set terminal states | **One row understated, and it was t1's.** The row closed *"Still waits on the BL-131 ruling"* — true when written, false from the moment m5-D2 was ratified at `a2d63d1`, and byte-unchanged since, so the step-1 gate correctly did not stop on it. Terminal state appended, superseding rather than rewriting. t2's row already terminal; t3's written per R19. |
| **5** — the drift checker | **Post-commit: 8 PASS · 0 FAIL · 4 WARN · 7 INFO, exit 0** (pre-commit: 2 WARN). All four WARNs are `project_knowledge` manifest staleness — the declared strict-mode exemption — and are **named, not chased**; zero FAIL and no *unexplained* WARN, which is what `--strict` actually asserts. **The 2 → 4 difference is the ordering rule firing**: the two added are both `CLAUDE.md` files, invisible to a pre-commit run because check 8 reads committed history, so a pre-commit-only report would have been a green over a gap. **A finding on the derivation, not the result:** `cloudcost/runbook.md` states no drift-check invocation at all (one unrelated `drift` hit), so the command was derived from the root `CLAUDE.md` §Definition of done — doc sync. A runbook that does not state its own gate is worth knowing about. |
| **6** — this summary | Written. |

**Beyond the six clauses: the harness gate set ran off-territory and is green.**
`mix deps.get`, `mix hex.audit`, `mix compile --warnings-as-errors`,
`mix format --check-formatted`, `mix credo --strict` (228 files, no issues), `mix test`
(972 tests, 0 failures, 133 excluded) — all at harness `2ef0517` with a clean tree. **A green
here is evidence of gate liveness, not of this change**: the harness tree is byte-identical
to HEAD but for one markdown file, so nothing in this round could have moved any of them.
**`mix dialyzer` is deferred, not skipped**, with a trigger that can fire — the next harness
ticket whose `Touches` names any `.ex`/`.exs` file runs it, and if none runs before the next
cycle's close, that close runs it.

### What stays open, and why that is correct

- **BL-132** — the reachability census over C1–C15. Its two known instances, C4 and C11, are
  answered by m5-D2 so its census need not re-derive them. Open because the other thirteen
  contracts were never in this round's scope, and taking them here would have mis-scoped both.
- **BL-119** — a cost snapshot with a declared total and no line items. **Unambiguously in
  scope now** precisely because the route it concerns is retained; cross-referenced from
  **BL-136**, whose subject it surfaces.
- **BL-136** — decision H's consequent. **E7** established H's precondition satisfied by the
  live pipeline for all three providers and its consequent unbuilt. An unbuilt artifact with
  a row is the correct state; an undecided, unowned question was not.
- **BL-137** — the §Open items freshness census, filed here. Correct as a row rather than as
  a fix: settling either reported instance needs adapter reads, which is establishment work.
- **§Not established item 1** — provider four's two non-identical gate statements. `[OPEN]`
  **(b)**, no owner invented, and correctly so: provider four is not open, and this round
  declined to take BL-074 with BL-131.
- **BL-075 arm 2** remains unsatisfiable as written, carried from the preceding cycle so it is
  not rediscovered rather than re-litigated here.
- **t1 F2's residue** — the elision check establishes that the on-disk packet matches the
  committed file, and cannot establish that the on-disk packet is what the reviewer
  *received*. Named at t1 r1 and unchanged; the rule promoted at clause 1 is what the residue
  produced.
- **t1 F1a** — E4(6)'s stated `.md` population and its own distribution disagree by exactly
  the file the ticket was writing. Recorded not repaired at t1 r1, and left so.

### Open for the next cycle

The two `Touches`-scoping questions this round answered are worth carrying as practice
rather than as rules: **a ticket's scoping is authoritative over a ticket's judgement**
(t2 r0 declined to edit outside `Touches` and was vindicated, the fix being a scoping
amendment rather than a licence to exceed one), and **a finding recorded inside a closed row
is a record, not an executor** — BL-070 was DONE in the same commit that recorded a residue
inside it. Neither is promoted here: the first is already carried by the standing deferred-
finding rule, and the second is that rule's failure mode rather than a new rule.

> **`[Corrected 2026-08-10 at t3 r1, on the reviewer's F1. The paragraph above stands
> unrewritten per decision 7; this block supersedes its second half.]`** *"Neither is
> promoted here"* is now false for the second practice. The reviewer accepted half the
> flag: *a ticket's scoping is authoritative over a ticket's judgement* **stays declined**,
> and on a checked premise — §6's `Touches` field and §9's failure-mode table carry it in
> the methodology's own words, so a learning entry would be a second copy of it. *A finding
> recorded inside a closed row is a record, not an executor* **is promoted**, and the ground
> is that the paragraph above got the classification right and the consequence wrong:
> **a named failure mode is often what makes a rule work**, and this one is not derivable
> from its parent — t2 r0 followed every instruction the parent gives and still produced the
> failure. **It landed as one clause on the existing entry, not as a new one**, so it never
> engages §7's bar; a precision on a rule is not a rule. Destination: agents `CLAUDE.md`
> §Learning — BL-007, the deferred-finding entry, with that entry's `Source:` extended
> rather than joined by a second.
>
> Corrected rather than left standing because leaving it would be this round's own recurring
> shape a fourth time — a correction landing in one artifact while the same claim survives in
> another, which is what §Promotion candidates' first entry describes one level over.

**Two findings carried forward for the next cycle's §7**, appended 2026-08-11 at the
body-addition edit. Both are below §7's bar and **neither gets an exception: this round has
excepted the bar twice already, and a third would make it a formality.** They are recorded
here because this is the subsection the next cycle's §7 reads, and it is the subsection m5
itself inherited its own carried candidates through.

**§7's distillation can lose what the candidate got right.** The correction-rule entry was
distilled from a §Promotion candidates entry that carried the disambiguation the promoted
headline dropped — the candidate said *"The rule is not never correct in place"*, and the
headline compressed from it kept the ambiguous phrase and lost the clause that resolved it.
§7's verification step confirms an entry can be **read out of** its destination file; it
does not compare the entry against the candidate it came from, so a distillation that loses
a clause passes verification. Carried rather than promoted: one instance, and the round has
excepted §7's bar twice already.

**A negative-control token stops being a negative control once a record quotes it.** A
sweep at the record-correction edit reused the token a prior edit had used for the same job
and it returned three hits — the prior edit's own committed record, quoting its control
table. Controls are minted fresh per sweep, or a sweep over records of prior sweeps finds
its own instruments and reads them as content. Carried rather than promoted: one instance,
found by the sweep it broke.

**Sequence from here:** BL-132 → provider four, which still carries §Not established item 1's
two non-identical gate statements and needs them reconciled wherever it is scoped.
