# m5 t3 — the close — implementation notes

`Round r0, 2026-08-10. Ticket: cloudcost/m5-n1-compose.md §Ticket set → t3.`

---

## Measurement stamp

**Every `path:line` and every count in this file was derived at agents `d36b8e9` and harness
`2ef0517`**, before this round's own edits, except where a claim is explicitly about this
round's output — those are marked and were re-derived after the last edit. Per **m5-D1**, a
line number appears only where the claim is itself about a line; everywhere else a section is
named and its text quoted. Positional claims carry the commit they were measured at.

---

## Step-1 gate

**Stop condition is temporal and the ticket says so** — it stops on *moved* since t2 r1, not
on *differs*. Reference point: t2 r1, `f6acc9c`.

### Arm (a) — terminal states, and both tickets' commits on the remote

**On the remote — established, not assumed.**

```
$ git rev-parse HEAD origin/main
d36b8e91f655af9b884283b56aaadb36362491d1
d36b8e91f655af9b884283b56aaadb36362491d1
```

and per-commit, over all twelve commits of this round:

```
5db4585 : origin/main      305b3a1 : origin/main
40c2d58 : origin/main      f6acc9c : origin/main
a2d63d1 : origin/main      ed36d22 : origin/main
3f66353 : origin/main      a2ae6bf : origin/main
4cdd31f : origin/main      d36b8e9 : origin/main
c26095a : origin/main
0b8804b : origin/main
```

`git branch -r --contains <sha>` per commit rather than one `rev-parse` comparison, because
`HEAD == origin/main` establishes the *tip* and says nothing about whether an individual
commit is an ancestor of the remote branch — it would be equally true of a force-pushed
history that dropped one. The per-commit form is the claim the gate actually makes.

**Terminal states — one arm of two.** t2's row states one verbatim: *"closed, approved at r1
and pushed at `f6acc9c`."* **t1's row does not.** It closes:

> Still **waits on** the BL-131 ruling, which §Ratified decisions says the reviewer authors
> into this document at the gate stop, per R12; the resolver is unchanged.

That is not a terminal state, and it has been false since **m5-D2** was ratified at
`a2d63d1`.

**Why the gate did not stop, and this is the whole reason the tense clause exists.** The stop
condition is *moved since t2 r1*. `git diff f6acc9c d36b8e9 -- cloudcost/m5-n1-compose.md`
touches §Ticket set's conventions, §Close criteria, t2's row and t3's row — **t1's row is
byte-unchanged across that range**. So the row *differs* from what arm (a) asserts and has not
*moved*, which is exactly the distinction t1's own gate lacked and this document added after
it. Continued, and **§Close criteria clause 4 took it** — which is where `Touches` sends it
(*"any row clause 4 finds understated"*), so no scoping was exceeded to fix it.

### Arm (b) — no candidate carries a disposition; §Carried in still names the inherited entries

**Three entries in §Promotion candidates**, enumerated by bold opener rather than counted:

1. *A check that structurally cannot observe the failure it stands in for…*
2. *An elision justified by "this is inlined above"…*
3. *An unpushed artifact may be corrected in place; a ratified one may not…*

**Zero dispositions.** Established as absence, not as a failed search:

```
$ grep -nEi '\[(PROMOTED|DROPPED|RECORDED)\]|Disposition:|promoted 2026|dropped 2026' \
      cloudcost/m5-n1-compose.md
(no output)
```

**Positive control for that vocabulary:** the same terms over
`docs/milestones/hc-e-implementation-notes.md` §37 return the outcome table's `**PROMOTED**`
and `**MERGED**` cells. The search works; the section has nothing to find.

**§Carried in matches its source item-for-item.**
`docs/milestones/hc-consolidation.md` §Milestone summary → *Open for the next cycle* names
three carried promotion candidates — *an entry's attribution is structural*, *a vocabulary
change owes a sweep* (parenthesised as already promoted), **m4-5's divergence** — and closes
with *"**BL-075 arm 2 remains unsatisfiable as written**, its blocker changed shape rather
than lifted"*. §Carried in carries all four. Nothing inherited is missing and nothing is
invented.

**Gate result: passed on both arms; continue.**

---

## §Close criteria clause 1 — the three promotion candidates

All three promoted. **The grounds are three different things and are stated separately**, per
the reviewer's ruling on the human's referral of the question at this close; recording them
identically would blur the distinction this round exists to sharpen.

### Candidate 1 — the blind check. Promoted; §7's bar met by analogy, and the analogy ruled

**Instances: three, and all three are reviewer-edit rounds rather than tickets.**

| # | Round | The blindness |
|---|---|---|
| 1 | m5 scoping landing **r4** | `git status` over a **gitignored** harness path — could not have seen the artifact it watched for, so its green was independent of it. Substituted with an mtime capture on both sides of the run, and the substitution *named*. |
| 2 | m5 ruling edit **r3** | A sweep population derived from a **single diff across a commit range in which the swept text was created** — a range diff renders such text as added, never as changed, so the method could not represent the change it was commissioned to find. Corrected to a per-commit extraction; found two. |
| 3 | m5 close-anatomy edit **r2** | A search for one *word* stood in for *"was this flagged?"* — a flag not using that word can neither fail nor pass it. |

Instance 3 arrives here by its own record's routing:
`cloudcost/docs/m5-close-anatomy-implementation-notes.md` §*The third instance, and where it
goes* closes *"t3 weighs it under §Close criteria clause 1 as further input to §Promotion
candidates' first entry, not as a fourth candidate."* It is weighed as instructed.

**A fourth item is an application, not an instance.** m5 **t1 r0**'s done-check item 4
substituted an mtime capture for a `git status` structurally blind to `cloudcost/output/` and
`cloudcost/history/`, both gitignored, and named the substitution rather than letting it read
as a pass. The t1 review file records it under *"Not findings, recorded because they were done
right"* — *"§Promotion candidates' first entry applied one round after it was recorded, by the
session that had no part in recording it."* **Counted as evidence the rule reaches ticket
work, and not as an instance**, because a rule being obeyed is not a rule recurring.

**The bar, ruled explicitly rather than smoothed.** §7's test is *recurred on ≥2 **tickets***.
Three reviewer-edit rounds are not three tickets, and the ticket's own prompt requires this be
said and ruled rather than quietly counted. **Ruling: met by analogy.** A reviewer-edit round
is a session that changes the repo, produces a committed record, and is reviewed — the same
terms on which a ticket recurs. The bar exists to keep one-offs out of an accumulating
section, and three independent occurrences in one cycle is not a one-off whatever the sessions
are called. Reading *ticket* literally would have dropped the entry on a word.

**Destination: harness `CLAUDE.md`** § Continuous learning → Workflow patterns →
**Silent-wrong-answer**, as a sub-entry. **Where the insertion falls:** after the
*Sibling state* sub-entry **and its own `Source:` line**, and before the parent entry's
through-line paragraph (*"well-formedness is exactly what lets a wrong answer survive
review…"*) and its terminal `Source:`. **No claim was separated from its attribution** — the
insertion point is between one sub-entry's closed `Source:` and the start of the parent's
closing prose, so nothing above it lost its Source and nothing below it gained one. **Basis
for the destination:** the candidate's own text says *"Same shape as a positive control one
level up"*, and the positive-control rule lives **inside** that entry, promoted there by
hc-e's own prior-claims census. A sub-entry carrying its own `Source:` is that entry's
established shape — six of its existing sub-entries do exactly that.

### Candidate 2 — the packet elision. Promoted; the bar does not apply

**One recorded instance** — t1 r0's packet — **and the count is not the basis.**

**Ruled: this is not an exception to §7's test; it is a rule of a kind the test does not
measure.** §7's ≥2 is a **recurrence** filter, and a packet rule is not recurrence-derived.
The repo says so in its own words about the entry this one extends —
agents `CLAUDE.md` §Learning — BL-007, *"A packet's sprint section shows the run's full
output, or states what it elided and why"*, whose `Source:` reads:

> **Promoted as a packet rule, not as a recurrence-derived learning entry** — it lands beside
> the packet rule above rather than in a §Learning source list, and it is the one m4 promotion
> candidate that was never a recurrence claim.

So the bar is **not met because it does not apply**, and that is what the disposition and the
entry both say. **Not written as an override**, per the reviewer's ruling — an entry written
as an override teaches that the bar bends.

**The relation to the parent is substantive, not just adjacent.** The parent allows elision
and forbids *silent* elision. This is what goes wrong once you have said what you cut: t1 r0's
packet said what it cut and why, truthfully for 577 of 634 lines, and the omitted remainder
carried that file's **§Measurement stamp** — the paragraph binding every citation in the
inlined sections to a commit. The assertion was true of most of the file and read as true of
all of it.

**Destination: agents `CLAUDE.md`** §Learning — BL-007, **immediately after the parent entry
and its `Source:` line**, before *A packet publishes the invocation…*. **Where the insertion
falls:** between two complete claim+`Source:` units, so neither is re-attributed. **One repo,
and why:** the packet-rule family lives agents-side; duplication into the harness file was
**considered and declined** — the two preambles are near-duplicates with no byte-identity
check in either repo, and `drift_check` has none either, so a duplicated rule is a mirror that
will silently diverge.

### Candidate 3 — unpushed vs ratified. Promoted below the bar, by explicit ratification

**One recorded instance** — the m5 reviewer edit r1 — **and the honest word is one.** A later
round reading this rule and finding it silent on a case would be an *application*, not a
second finding, and the `Source:` does not blur the two.

**The ground, recorded because "the human said so" is not one.** §7's bar is a frequency test,
and frequency is the wrong filter for a rule whose subject is a failure that bites rarely and
irreversibly: silently altering a ratified decision does not recur its way to attention — it
recurs by going *unnoticed*. A rule costing three sentences that forecloses a class of
undetectable failure earns an entry at one instance. The same argument would not carry a
finding about a *subject*, which is what the bar is there to filter.

**Form: BL-007's exception form**, so the override is auditable. The file already carries the
same argument once — the credential-provenance rule, promoted *"on a single instance
deliberately: the ≥2-ticket bar assumes a missed rule costs another review finding, and where
the violation is irreversible the second instance **is** the incident the rule exists to
prevent."* That entry is named in the new one as the form precedent.

**Destination: harness `CLAUDE.md`** §Continuous learning → Workflow patterns, in the
record-integrity cluster. **Where the insertion falls:** after *A claim that lands in the same
commit as the thing that would make it true is self-falsifying…* **and its complete
`Source:`**, before *For any ticket whose Done-when names a user-facing action…*. Both
neighbours are complete claim+`Source:` units; neither is re-attributed.

**Placement is by subject; the precedent is by form.** The credential rule shares the *ground*
but not the subject, and a reader looking for record-discipline rules looks in the
record-integrity cluster. **One repo, and why:** the record-integrity family lives harness-side;
duplication declined on the same mirror grounds as candidate 2.

### The count check

**Entries in §Promotion candidates: 3. Entries carrying a dated disposition: 3.** Both derived
by enumeration; the enumeration is printed under the gate's arm (b) above and in §Done-check
item 4 below.

---

## Clause 2 — the carried-in entries, and the prior-claims census

### The three carried-in entries, weighed on the same terms

**(1) *An entry's attribution is structural.*** → **PROMOTED.** Bar met:
`docs/milestones/hc-consolidation.md` §Milestone summary → *What the close's six sweeps found*
records that **three of that round's six promotions orphaned the provenance of the entry above
them**, and *"the check that would have caught it did not exist"*. Three instances in the
preceding cycle, and this round applied the rule in every edit it made. Destination: harness
`CLAUDE.md`, the §7-verification cluster — inserted after *A learning exists only where a
session will read it* and its `Source:`, before the credential rule. **Why harness:** the
entry it belongs beside — §7's verification step and what that step does *not* assert — is
harness-side.

**(2) *A vocabulary change owes a sweep of everything that speaks it.*** → **NO ACTION;
already promoted**, at harness `CLAUDE.md` §Continuous learning → Workflow patterns →
*Adjacent-case and load-bearing coincidence*, by hc-e. Read out of the file below.
**Recorded as a result rather than a silence**, per §Close criteria's own framing. §Carried
in's own text calls it *"promoted, with its first application recorded"*, and this round
applied it twice: the §Not established preamble sweep at the ruling edit, and the prefix-change
sweep at that edit's r1.

**(3) *m4-5's divergence — promote mid-cycle when a rule binds work that has not run yet.***
→ **PROMOTED.** Bar met across cycles: m4-5 (the origin), hc-e (which did the same and
recorded the cost as a carried candidate — `hc-consolidation.md` §Promotion candidates,
*"This round did not, and the workaround worked well enough to hide the cost"*), and
m5-cloudcost, which **complied** — m5-D1 was ratified at r5 and made binding on t1 and t2
immediately rather than held for this close. Destination: harness `CLAUDE.md`, immediately
after (1), the two being the same subject at different distances.

**BL-075 arm 2** is not a promotion candidate — it is carried so it is not rediscovered, and
it is restated in §Milestone summary → *What stays open* on that footing.

### §7's prior-claims census

**Population derived by command, not by eye.**

```
$ grep -rln -iE 'learnings promoted|promoted into|PROMOTED|MERGED|promotion (landed|commit)' \
      docs/milestones/hc-*.md docs/reviews/hc-*.md
```

Nine files matched. **Six of them do not make a promotion claim** — they cite rules promoted
in *earlier* cycles (hc-b's *"the carrier promoted at the m4 close"*), or match `merged` in an
unrelated sense (hc-c's merged stdout/stderr captures), or discuss candidates without
disposing them. Each was opened and read; the exclusions are by substance, not by token.

**The preceding cycle produced no handoff.** `ls docs/handoffs/` — the latest is
`handoff-m3-close-2026-08-05.md`, which predates the hc round. **This matters**: the failure
§7's census clause was written for is a handoff's *"learnings promoted"* block that promoted
nothing, and this cycle has no such carrier. Stated so a reader does not read its absence as
an unsearched population.

**Two documents carry an actual claim**, and only one carries an enumerated block:
`docs/milestones/hc-consolidation.md` §Milestone summary (a narrative claim of six entries
across both files) and `docs/milestones/hc-e-implementation-notes.md` **§37's outcome table**
plus **§38's verification table** and **§33**'s census-produced promotion.

**Every member of the block checked against both files — not the ones that looked
unfamiliar.**

```
token                                                harness  agents
a count names the commit it was derived at              1        0
Bind an artifact to what produced it                    1        0
the restore is the second one                           1        0
An identifier is resolved, never transcribed            1        0
A vocabulary change owes a sweep of everything…         1        0
A packet publishes the invocation that produced it      0        1
positive control                                        2        0

POSITIVE CONTROL   'CLAUDE.md'                         10        8
NEGATIVE CONTROL   'zzz-not-a-real-rule'                0        0
```

**Seven of seven present, each in exactly the file its claim names.** The two controls are
what make the zeros in the wrong-file column readable as absence rather than as a broken
search: a token the search *should* find returns non-zero in both files, and a token it should
not returns zero in both.

**Nothing absent, so the census produced no promotion.** §7's *"anything absent is promoted
now"* clause has an empty population this cycle, and that is the result — not a step skipped.

---

## Clause 3 — §Not established

**Passed on all four arms.** Recorded **in the section itself** as a dated block, per
`Touches` (*"§Not established (clause 3's result)"*), because a clause that produced no edit
is a result and not a silence.

| Arm | Result |
|---|---|
| Every item's state reads from its own prefix | **Yes.** Four entries: `[OPEN]` (b), `[RESOLVED]` (b), `[RESOLVED]` (a), `[DECIDED]` (c). Each states its kind per R21. |
| Each `[OPEN]` item names what would settle it | **Yes.** One `[OPEN]` item — item 1 — naming *"a ruling that reconciles them, authored wherever provider four is scoped"*, and being kind (b) it correctly invents no owner. |
| Each `[OPEN]` **(a)** item's resolver names something that exists | **Vacuously.** Zero `[OPEN]` (a) items; the section's only (a)-kind entry is item 3, and it is `[RESOLVED]`. |
| The section carries no total | **Yes**, per its own preamble, and the recorded result adds none. |

**The third arm is the one that could have passed for the wrong reason**, and the block says
so. A grep for `[OPEN]` (a) returning nothing is indistinguishable from a broken grep, so the
zero is read off the **printed prefix enumeration** of all four items instead — the population
is empty rather than unexamined. This is §Promotion candidates' first entry applied to this
ticket's own checking, which is the point of promoting it.

---

## Clause 4 — §Ticket set terminal states

**One row understated: t1's.** Corrected as `Touches` provides for. **The correction is an
append, not a rewrite** — the superseded clause stands, per decision 7, with the terminal
state appended beneath it and dated:

> **`[Terminal state appended 2026-08-10 at the close (t3), on §Close criteria clause 4, which
> found this row understated.]` t1 is CLOSED — approved at r1 and pushed at `40c2d58`, its gate
> stop reached as designed.**

**t2's row** already states one and is unedited. **t3's row** written per R19 in this commit.

**The second half of the clause — *no row's state is inferable only from a record file* —
holds for all three.** Each row states its own state in the row: t1 now closes with CLOSED,
t2 with *"closed, approved at r1 and pushed at `f6acc9c`"*, t3 with *"opened and closed
2026-08-10 (r0); both pushes held pending review"*. Each also *names* its record file, which
is the correct relation — the row is the state and the file is the evidence.

---

## Clause 5 — the drift checker

**The invocation is derived, and the derivation produced a finding.**

**`cloudcost/runbook.md` states no drift-check invocation at all.** `grep -in 'drift'` over
that file returns exactly one hit, and it is unrelated — a table cell saying a value is
*"read from the adapter itself, so this table cannot drift from it"*. **Reported as a
finding**, per the check's own instruction to report if neither document states it: one of the
two named sources is silent, and a runbook that does not state the gate its own repo runs at
every ticket boundary is worth knowing about. Not fixed — `Runbook update rule` puts no runbook
section in this ticket's `Touches`.

**The command comes from the other named source**, root `CLAUDE.md` §Definition of done — doc
sync: `python3 scripts/drift_check.py`, run from the `aetheris-agents/` root, with `--strict`
per that section's strict-mode paragraph and the ticket-boundary gate rule.

**Run post-commit, per the standing rule** that check 8 compares the manifest against
*committed* history, so a pre-commit run cannot see the staleness this commit introduces.
**Both runs are published, because the pair is the evidence**:

```
$ python3 scripts/drift_check.py --strict     # pre-commit
Summary: 8 PASS  0 FAIL  2 WARN  7 INFO          exit=0

$ python3 scripts/drift_check.py --strict     # post-commit
[WARN] project_knowledge: cloudcost/milestone.md   stale — manifest=eae14d4 current=f6acc9c
[WARN] project_knowledge: CLAUDE.md (agents)       stale — manifest=dcf1d42 current=<this commit>
[WARN] project_knowledge: docs/backlog-2026-06.md  stale — manifest=7dbdb7d current=<this commit>
[WARN] project_knowledge: CLAUDE.md (harness)      stale — manifest=2ef0517 current=0ed9068
Summary: 8 PASS  0 FAIL  4 WARN  7 INFO          exit=0
```

`[Two of the four "current" values are transcribed as <this commit> rather than as the literal`
`hash the run printed, and the substitution is declared rather than silent. The run printed`
`afb4ade; this commit was then amended to correct the WARN count recorded in two other files,`
`which moved the hash. Re-running and re-pasting cannot terminate — each amend that fixes the`
`transcript invalidates the transcript — so the two values that track this commit are written as`
`what they are. The other two are literal and stable: cloudcost/milestone.md's f6acc9c is t2 r1,`
`and the harness CLAUDE.md's 0ed9068 is this round's harness commit, which was not amended. The`
`summary line and every manifest= value are the run's own output, unaltered. Per m5-D1 a`
`positional claim carries the commit it was measured at; here the commit it was measured at is`
`the commit it is written in, and saying so is more durable than a hash that is wrong by the`
`time it is read.]`

**All four WARNs are `project_knowledge` manifest staleness**, which is the **declared
strict-mode exemption**, not a regression. **Named, not chased**: mid-cycle staleness is
expected truth and clears only at the export boundary. **Zero FAIL, and no unexplained WARN**,
which is the invariant `--strict` actually states.

**The pre/post difference is itself the standing rule firing, and is recorded as such.**
Pre-commit **2**, post-commit **4** — the two new ones being both `CLAUDE.md` files, which this
round edits and which the pre-commit run could not see, since check 8 read their *pre-edit*
commit hashes. `docs/backlog-2026-06.md` also re-stales, moving from `7dbdb7d` to `afb4ade`.
Had only the pre-commit run been published it would have reported a green over a gap, which is
the vacuity the ordering rule exists to prevent — and this is the second recorded instance of
it firing on a session that knew the rule.

---

## Clause 6 — §Milestone summary

Written. **Placement derived, not chosen:** `docs/milestones/hc-consolidation.md` puts its own
§Milestone summary **last in the file**, after §Promotion candidates, and this document's
sections run Ticket set → Ratified decisions → Close criteria → Promotion candidates → Not
established → Carried in. The append point is therefore after §Carried in, closing the
document. **It carries no total over §Not established** — the section's per-item prefixes are
authoritative, and the summary points at them rather than counting them.

---

## The backlog row — BL-137

**One row, as `Touches` provides for.** Number and placement derived from the file: rows run in
unbroken ascending order to EOF, BL-136 is the highest in use and the last block, so **BL-137
appends after it**. Shape taken from BL-136 — the current three-line header form, the
`**Owes:** / **Costs:** / **Collides with:**` closing triple, and a backticked `Source:` block.

**Subject, as the prompt specifies:** the two reported instances are named, **neither rests on
the premise m5-D2 overturned** (which is why they were correctly left unfixed at t2 r1 and why
they get a row rather than a third `Touches` amendment), **settling either needs adapter
reads**, and **the two are a starting population and not the census**.

**Two things the row carries beyond those three, both flagged rather than slipped in:**

1. **A count, with its enumeration.** §Open items carries **eleven** top-level items — seven
   bold carried items and four plain forward-looking bullets — derived at `d36b8e9` by
   enumerating `^- ` within the section. The row states it because *"a starting population"*
   is a claim about a ratio, and a ratio with one side unstated is not checkable. **This
   corrects a figure I had earlier taken as ten**; the enumeration is what settled it, which
   is the rule the count was cited under.
2. **A lead on the orphan-filename item, offered as a lead and not as a finding.**
   `cloudcost/m2-milestone.md` §*m1 open items — final triage after A–H* records a row
   *t2 output filename collision* as **CLOSED — t2 b**, *"Each provider writes
   `{provider}_orphan_candidates_{period}.json`"*. If that holds at HEAD the item's trigger
   fired **and** was discharged, and the item is a residue rather than an open question. **Not
   verified here** — verifying it means reading `detect_orphans.py`, which is establishment
   work this ticket does not do — and the row says *"Read `detect_orphans.py`, not the record
   — the record is the lead."*

**`Do not generate` observed:** neither §Open items instance is fixed, and no adapter was read.

---

## Harness boundary gates — run off-territory

**The ticket's done-check names pytest, the read-backs and `drift_check`, and its silence is
not authority.** A done-check is the ticket's completion criteria; *"every existing gate runs
at ticket boundaries, even off-territory"* is a repo-wide boundary obligation. They are
different instruments and the first does not scope the second. This ticket touches
`../aetheris/CLAUDE.md`, so the harness boundary is entered and its gates are owed.

**Invocations derived, not assumed** — harness `CLAUDE.md` §CI contract states the set
verbatim (*"Every change must pass all of these before merge"*) as a seven-command block.
**Tree state stamped, per m5-D1:** harness `2ef0517`, `git status --short` empty, before the
`CLAUDE.md` edit.

| Gate | Result |
|---|---|
| `mix deps.get` | `All dependencies are up to date`, exit 0 |
| `mix hex.audit` | `No retired or security advisory packages found`, exit 0 |
| `mix compile --warnings-as-errors` | exit 0, no output |
| `mix format --check-formatted` | exit 0, no output |
| `mix credo --strict` | `228 source files`, `2056 mods/funs, found no issues`, exit 0 |
| `mix test` | `972 tests, 0 failures, 133 excluded`, 91.0s, exit 0 |
| `mix dialyzer` | **Deferred — see below** |

**What the green establishes, and it is not what a green usually establishes.** The harness
tree is byte-identical to HEAD except one markdown file, so **nothing in this change could
have moved any of these gates**. The result is evidence of **gate liveness** — that each gate
still runs and still passes — and evidence of nothing about this change. Reported in those
words deliberately: a gate run off-territory and presented as validating the change would be a
green for the wrong reason, which is this round's own first promotion candidate with its sign
flipped — not a check that cannot see its subject, but a check whose subject was never in
scope.

**And no before/after pair was taken, unlike t1's and t2's pytest runs.** Those needed a
baseline because the tree changed under them. Here the argument from tree state is stronger
than a pair would be: a pair proves the two runs agreed, whereas byte-identity proves there
was nothing for them to disagree about. Stated so the absence does not read as a lapse from
the discipline t1 and t2 established.

**`mix dialyzer` is deferred, not skipped, and the deferral names a trigger that can fire.**
Skipping silently makes *"we skipped dialyzer"* the precedent, and the gate that never runs is
the gate that rots — which is the rule's whole reason for existing. **Trigger: the next
harness ticket whose `Touches` names any `.ex` or `.exs` file runs it; and if no such ticket
runs before the next cycle's close, that close runs it.** Recorded here. **No home was
invented for it in the round document** — this document has no cross-cycle obligations section
and the ticket's instruction was to name one only if it exists.

**No gate came back red**, so the contingency the reviewer specified — record, file a row, name
it in §Milestone summary, do not fix — did not arise.

---

## Done-check

`Run at the tree this round produced. Item 3 is run post-commit; every other item pre-commit,
and the ones whose subject is this round's own output were re-derived after the last edit.`

### 1. The offline pytest spine

**Both anchors re-resolved at HEAD before running, per the check's own instruction.**

- **Anchor 1**, `cloudcost/runbook.md` §Offline tests — present, and its block reads
  `python3 -m pytest cloudcost/tests/ -v`, commented *"no credentials; recorded DO + AWS +
  Linode fixtures"*. **Unmoved.**
- **Anchor 2**, root `CLAUDE.md` §Commands — present, its block headed
  *"# From the aetheris-agents/ root"*. **Unmoved.** (It lists payslip and api suites, not
  cloudcost; it is the anchor for the *working directory*, which is what the pin cites it for.)

```
386 passed in 142.07s (0:02:22)
```

**386 — identical to t1's recorded figure and to t2's, both rounds.** t3 changes no executable
line, so this is the expected result and a different one would have been a finding. Said either
way, as the check requires.

### 2. Every promoted entry read out of its destination file

Five entries promoted. Each read back **from the file**, with surrounding lines, using a
stated pattern. Full quotations with context in the packet; the patterns and hits:

| Entry | File | Pattern | Hits |
|---|---|---|---|
| blind check | `../aetheris/CLAUDE.md` | `A check that cannot observe the failure it stands in for` | 1 |
| unpushed vs ratified | `../aetheris/CLAUDE.md` | `An unpushed artifact may be corrected in place` | 1 |
| attribution is structural | `../aetheris/CLAUDE.md` | `An entry's attribution is structural` | 1 |
| promote mid-cycle | `../aetheris/CLAUDE.md` | `Promote a rule mid-cycle when it binds work` | 1 |
| packet elision | `CLAUDE.md` (agents) | `An elision justified by "this is inlined above"` | 1 |

**Plus the seven prior-claims census tokens**, tabulated under clause 2 above with their two
controls.

**Where each insertion falls is stated in clause 1 and clause 2 above, not here**, and in each
case relative to the surrounding unit's *boundaries* — after a closed `Source:` line, before
the next claim — because §Carried in's first rule binds this ticket more than anywhere.

### 3. The drift checker

Derived, published, run post-commit. See clause 5.

### 4. §Promotion candidates — entries vs dispositions

**3 and 3.** Both by enumeration, both enumerations printed (gate arm (b) for the entries;
clause 1's three subsections for the dispositions).

### 5. Nothing outside `Touches`

`git status --short` in both repos, in the packet.

---

## Deviations

**None.** `Touches` names five paths and exactly five changed, one for one:
`cloudcost/m5-n1-compose.md`, `CLAUDE.md`, `../aetheris/CLAUDE.md`,
`docs/backlog-2026-06.md`, and `cloudcost/docs/m5-t3-implementation-notes.md` *(new)*.
`git status --short` in both repos returns those five and nothing else.

**No review file at r0.** The round's review file lands when the reviewer's findings arrive.
§Ticket set's conventions already declare it is not a `Touches` path and that landing one is
not a deviation, so nothing is declared here.

**Cross-repo ordering observed:** the harness commit lands first, the agents commit second,
**and both pushes are held.**

---

## Flagged for the reviewer

**One.** §Milestone summary's *Open for the next cycle* records two practices this round
established — *a ticket's scoping is authoritative over a ticket's judgement*, and *a finding
recorded inside a closed row is a record, not an executor* — and **declines to promote
either**, on the ground that the first is already carried by the standing deferred-finding rule
and the second is that rule's failure mode rather than a new rule. Neither was a §Promotion
candidates entry, so neither was clause 1's to dispose; recording them in the summary rather
than filing them as candidates is a judgement, and it is the reviewer's to overturn.
