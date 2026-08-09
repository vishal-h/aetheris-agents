# hc-e — implementation notes

**Ticket.** `docs/milestones/hc-consolidation.md` §Ticket set → hc-e. **Repos.** agents `f8ed90f`,
harness `48f59e7`. **Date.** 2026-08-09.

**Outcome: the opening edit E1–E4 landed; the ticket then STOPPED at its anatomy census.** hc-e has
**2 of 7** §6 fields authored and **no step-1 gate slot at all**. No close work was done. That is the
correct outcome, not a setback — and it is the second time this round, which is itself the finding.

---

## 1. E1 — hc-d's row, closed at r3

R19 scopes a row edit to the session that changed the state; hc-d's session is over, so this carry
was authorised explicitly rather than taken.

**The `[V]` — the commit range is derived from the repos, not from the packets.**
`git log --oneline --grep='hc-d'` over each repo:

```
agents   240eb59 → f8ed90f   (13 commits matched; the hc-c pair at the head of the range excluded
                              by their own subject lines, leaving hc-d's 11)
harness  2d76a65 → 48f59e7   (4 commits: the contract landing plus r1, r2, r3)
```

The row now reads **Closed 2026-08-09 at r3**, in hc-c's shape: gate G0–G5 passed, BL-077 closed,
BL-133 face 2 discharged, R3 answered, four rounds. The prior *"Opened and stopped"* text is kept
verbatim inside the cell per **decision 7**, not overwritten — a row that silently replaces its own
history is a row whose earlier state cannot be checked.

## 2. E2 — the recency-selection candidate, transcribed

Added to §Promotion candidates verbatim as authored, above the restore-verified entry. Its sharp
edge is the part I would not have written myself: **an artifact can be correct and still be the
wrong artifact, and nothing in its contents distinguishes the two.** That is why the corrupted
provenance stamp survived review — it was inspected, and inspection was the wrong instrument.

## 3. E3 — BL-135 and BL-075 are the same defect

**Established from the rows and the source, not from resemblance.** BL-075's m4 close-b annotation
already carries the full identity, and every field matches BL-135's observation:

| | BL-075 (2026-08-08) | BL-135 (2026-08-09) |
|---|---|---|
| module | `Aetheris.CLI.Commands.RunHelpersTimeoutTest` | same |
| file:line | `…/run_helpers_timeout_test.exs:84` | same |
| stacktrace | `:98` | same |
| assertion | `await_bounded(run_id, await_inactivity_timeout_ms: 300)` | same |
| error | `stalled: … for 300ms … last event seq: -1` | same |
| run id | `await-status-activity-7139` | `-8610` |

The run id is `System.unique_integer` and distinguishes nothing. **One test, one assertion, two
observations** — not two tests in one module, and not two failures of different assertions.

**So BL-135 is a duplicate and the error is mine.** The gate rule requires a tracked row *the day a
red is found*; it does not license filing without looking. I filed BL-135 at hc-d r3 without
searching the backlog, and BL-075 not only existed but already carried the identical stack trace.
**The count error is over a population of size two** — filing two rows for one defect, which is the
same class as filing one row for two.

**Folded, not deleted, both ways.** BL-075 gains the third observation with its date and evidence;
BL-135 records that it was folded and why, and remains as the record of the duplication. What
BL-135 genuinely contributes is carried across: the **nine non-reproductions**, which are the first
probe of the trigger rather than another count of failures.

## 4. E4 — arm 2's blocker is PARTLY lifted, and the remaining gap is a different shape

**The `[V]`, quoted.** BL-075's blocking clause: *"Three further full-output runs come back clean"
requires that those runs' full output be **retained somewhere durable**, and **BL-133** establishes
that no such place exists: `../aetheris/sprint/` archives `run.json` alone, and `mix test` output is
archived nowhere at all.*

**Two halves, and hc-d falsified exactly one.**

**Half 1 — "no such place exists" — is now false.** Every sprint run retains `console.log` (every
arm, in order, untruncated, streams merged) beside `provenance.txt` (both repos' commits, target,
command), under a stated, bounded and *enforced* 30-day retention.

**Half 2 — "`mix test` output is archived nowhere at all" — still holds**, and it is the half arm 2
needs. Derived, each with its control:

- `sprint.sh` invokes `mix test` **once**, at `:1517`, on **two named files** — not the suite.
- `grep -c 'run_helpers_timeout_test' ../aetheris/scripts/sprint.sh` → **0**.
  *Positive control:* `grep -c 'server_checkpoint_test'` → **3**, so the pattern finds referenced
  test files where they exist.
- The boundary-gate `mix test` is a **direct invocation** outside any sprint process, and
  `SPRINT_CONSOLE` exists only inside one.
- Over the retained corpus: `grep -rlE '[0-9]+ tests, [0-9]+ failures' sprint/*/console.log` →
  **0 files**. *Positive control:* the same pattern over a direct `mix test` capture → **1**.

**The place exists; the routing does not.** The blocker has changed shape rather than lifted — from
*"no durable place exists"* (a ruling) to *"the full suite is never run where the durable place
would capture it"* (a routing decision). That is smaller and cheaper, and it is recorded on the row
so the next reader does not re-derive it. **Face 1 is untouched and is not what arm 2 needed** — arm
2 is about run output, not reviews.

**And one thing recorded against hc-d's own reasoning, since hc-d is mine too.** hc-d chose 30 days
*citing BL-075's "three further full-output runs"* as the justification. **That citation reached one
step further than the mechanism does** — the bound was set for a consumer the capture does not yet
serve. The bound is not wrong; its stated rationale was.

**Arm 2 is not started.** Establishing the blocker's status was E4's whole scope, and counting runs
toward arm 2 was explicitly excluded.

## 5. The stop — hc-e's anatomy census

**Population: the seven §6 fields named by this document's own §What the methodology owes**
(*"seven sections and no more — `Scope`, `Contract refs`, `Touches`, `Do not generate`,
`Runbook update rule`, `Done-check`, `Claude-code prompt`"*), plus the step-1 gate slot, which
decision 3 makes a requirement rather than a §6 field.

```
AUTHORED      Scope
AUTHORED      Contract refs
NOT AUTHORED  Touches
NOT AUTHORED  Do not generate
NOT AUTHORED  Runbook update rule
NOT AUTHORED  Done-check
NOT AUTHORED  Claude-code prompt

population = 7      authored = 2      not authored = 5
Step-1 gate slot:   ABSENT — not even R13-marked
```

**Positive control**, the same pattern over hc-d's section, which has all seven: `1` for every
field, and `2` for the gate slot. So a zero reads as absence rather than as a broken pattern.

**hc-e is hc-d's shape, and worse in one respect.** hc-d stopped at **2 of 7** with an R13-marked
gate whose resolver named a reviewer-authored section-scoped edit. hc-e is **2 of 7** with **no gate
slot at all** — its catch-all is `**Everything else is `[R13: deferred, per R12.]`**`, which defers
the gate along with the five fields and names its resolver only by reference to R12.

**Why this is a stop and not a substitution.** R12 assigns authoring to the reviewer (decision 11);
hc-d's precedent is that **every defect in hc-b's version of hc-c's specification sat in the one
slot completed confidently, and every R13-marked slot was sound.** Authoring five fields and a gate
here would reproduce that failure across the same surface, in the ticket that closes the round —
where an unnoticed defect has no later ticket to catch it.

**What would unblock it:** a reviewer-authored section-scoped edit carrying hc-e's `Touches`,
`Do not generate`, `Runbook update rule`, `Done-check`, `Claude-code prompt`, and a step-1 gate
written against the design those fields describe.

**Three things already on the record for that edit**, restated so its author does not rediscover
them: §7's prior-claims census is over **m4's seven promoted entries**, not only this round's;
**hc-b's G4 discharged four of them** and that is a G4 result rather than the census; and the
**export boundary is the last content operation**, clearing all three standing `project_knowledge`
WARNs.

**And one field that will need care rather than transcription:** hc-e's *"named question that gates
the rest"* is already marked `[partly falsified]`, and the half that stood — *"hc-d has not run"* —
is now false too. Both halves are knowable at the moment hc-e's anatomy is authored, which changes
what that slot should say rather than merely dating it.

## 6. Not reached, not dropped

- **The §7 ritual, the export boundary, the milestone summary, §Close criteria's reads** — all of
  hc-e's actual work. Untouched.
- **No row filed or closed by this edit.** BL-075 and BL-135 are *annotated*; neither changes state.
  BL-135 is folded, which is a disposition recorded on both rows, not a close.
- **hc-e's own row in §Ticket set is untouched**, as instructed — the census may change what it
  should say, and that is the authoring session's call.

---

# Reopening — 2026-08-09, and a second stop, this time at G4

**Repos.** agents from `3d79a6f`, harness `48f59e7` (untouched, clean). **Date.** 2026-08-09.

> **Outcome: the held push was released, C1 and C2 landed, the step-1 gate ran G1–G4, and the
> ticket STOPPED at G4.** No close work. §7's ritual, the export boundary, the milestone summary
> and §Close criteria's reads are all untouched. G5 and G6 were not run — named below, not
> silently omitted.

---

## 7. The push, released — and the harness leg was a genuine no-op, reported as one

Divergence was checked against the **remote**, not against a local `@{u}` ref: both repos were
fetched first, then pushed harness-first, then the remote heads were read back with `ls-remote`.

```
harness  local=48f59e7  remote=48f59e7  ahead=0 behind=0   -> "Everything up-to-date"
agents   local=3d79a6f  remote=f8ed90f  ahead=3 behind=0   -> f8ed90f..3d79a6f  main -> main
read back: harness refs/heads/main = 48f59e7 ; agents refs/heads/main = 3d79a6f
post-push: both ahead=0 behind=0 dirty=0
```

The three released are `9fbba09`, `e047dd1`, `3d79a6f`. The harness push moved nothing and that is
stated rather than skipped.

## 8. C1 and C2

**C1** — instance **(viii)** appended to §Promotion candidates' reviewer-assertion open list,
verbatim, with its operational close: *an identifier is resolved, never transcribed*.

**C2** — the anchor-staleness note appended beneath F3's disposition in
`hc-e-anatomy-edit-implementation-notes.md` §Review. Derived over both commits rather than
asserted, and the derivation shows the shift is **not uniform**: `+37`, `+48`, `0`. Nothing was
renumbered. The standing form is recorded there for hc-e's own citations.

**And hc-e's own row, under R19 as amended by A3.** This session reopened the ticket, so the row
was owed at the moment the state changed — not once the outcome was known. The row and the header
`Status:` line record *reopened, in progress, gate has not yet returned*, with the earlier states
kept per decision 7. **This is the first session bound by A3's ruling**, whose whole subject is a
reviewer instruction that told a session to leave a row until its wording settled.

## 9. G0-equivalent hygiene

```
agents  HEAD=e77a530  status --porcelain = 0 lines
harness HEAD=48f59e7  status --porcelain = 0 lines
```

**VERDICT: both zero → proceed.**

## 10. G1 — §7's own steps. **PROCEED.**

Read from `../aetheris/docs/methodology/milestone-methodology.md` §7 itself, not from any packet.
**The document has not moved since `aaf0f9a`** — `git diff --quiet aaf0f9a HEAD --` on that path
returns clean, and `aaf0f9a` is the commit whose subject is *"§7 gains a promotion-verification
step; cite steps by name"*. So R-b's finding condition does not fire.

§7's steps, **by name, taken from §7's own text**: the **scan** (*"scans the milestone's review
files for findings that recurred on ≥2 tickets"*, with its own widening — *"The review files are
not the only input"*); the **distillation** (*"Each is distilled to one standing instruction in the
relevant `CLAUDE.md` learning section"*); the **commit** (*"claude-code commits the promotion in
its own PR"*); the **verification step**; and the **drift-checker-and-milestone-summary** step.

The two this round depends on, quoted:

> **Verify each promoted entry is in the file, by opening it.** The promotion is not complete
> when the finding is distilled or when the commit lands — it is complete when the entry can be
> read out of `CLAUDE.md`. The packet quotes each new entry with its surrounding lines, not a
> claim that the edit was made. A section elsewhere headed "learnings promoted" is a record of
> intent; only the file is the promotion.

> **And census the prior claims, not only this milestone's.** Any document from the preceding
> cycle that says learnings were promoted — a handoff's review-discipline section, a close
> note — is checked against both `CLAUDE.md` files, and anything absent is promoted now with a
> `Source:` naming the cycle it came from and the fact that it was found absent. Two found by
> eye is not a census: check every item in the block, not the ones that look unfamiliar.

**One structural note, and it is not a divergence.** The prior-claims census is **not a step of its
own** — it is a paragraph *inside* the verification step. This document already says so
(§Close criteria clause 5: *"§7's own verification step, and **its** prior-claims census besides"*),
and hc-e's `Contract refs` matches. Recorded because "the two this round depends on" could be
misread as two steps, and citing it as one would be citing a step that does not exist.

## 11. G2 — m4's seven promoted entries. **PROCEED, and the seven holds.**

R-a expected this one to move. **It does not** — but the number was checked at its source rather
than carried, which is what R-a asked for.

`cloudcost/m4-consolidation.md` §Rules promoted this cycle says **three, at t1a-p** and **four more
at close-b** = **7**. It also carries an eighth bullet, *"And one amendment, not a promotion"* — the
repos rule — so **a naive count of the bullets gives 8**, and the seven is right only because m4
classifies the amendment out explicitly. That is the trap in the number, and it is the reason the
count had to be read rather than inherited.

**All seven located at HEAD**, each by anchor with its line as a parenthetical, stamped with the
commit each file was last changed at (harness `CLAUDE.md` at `b4d782a`, agents `CLAUDE.md` at
`080ad24`):

| # | Where | Entry |
|---|---|---|
| 1 | harness §Continuous learning → Workflow patterns (`:730`) | *"Every claim has a truth-maker — name what you checked, or write "not established" and stop."* |
| 2 | harness → Silent-wrong-answer (`:642`) | *"A check that reads the wrong thing reports a clean result, not an error — so bind every command to its target explicitly."* |
| 3 | agents §Learning — BL-007 (`:472`) | *"The packet is the artifact that travels; content in any other channel does not exist."* |
| 4 | harness, inside the truth-maker rule (`:752`) | *"A count is a claim about a population — name the population and show the enumeration…"* |
| 5 | harness → Silent-wrong-answer (`:653`) | *"Match structured data by field, not by substring…"* |
| 6 | harness → Silent-wrong-answer (`:667`) | *"Sibling state — a check whose own setup injects state that changes what an adjacent check can observe."* |
| 7 | agents §Learning — BL-007 (`:475`) | *"A packet's sprint section shows the run's full output, or states what it elided and why."* |

**Positive control**: the same grep form against a phrase deliberately absent returns **0** in both
files, so the seven hits read as presence rather than as a pattern that matches anything.

**The four/three split, derived from hc-b's G4 rather than assumed.** hc-b's notes §1 read:
*"G4 was re-derived, not cited … All four read out at `288c8ef`: harness `:717` (the truth-maker's
third operational form), `:618` (substring-versus-field), `:632` (sibling state), agents `:475`
(the packet full-output rule)."* Those are **entries 4–7, the close-b four**. **The three hc-b's G4
did not discharge are the t1a-p three — entries 1, 2 and 3** — which is exactly the population
§7's prior-claims census still owes.

**And hc-b's G4 anchors have moved, which C2's rule predicts.** Three of its four harness numbers
are stale at HEAD — `:717→:752`, `:618→:653`, `:632→:667` — while agents `:475` did not move. Both
readings are right at their own commit; the numbers are not corrected here, because hc-b's notes
are a dated record.

## 12. G3 — §Promotion candidates. **PROCEED.** Six candidates.

Pattern `^\*\*[A-Z(]` over the section, bounds derived from the headings (`## Promotion candidates`
→ `## Not carried, and why`). It returns **10** paragraph-leading bold sentences, of which **6 are
candidates** and **4 are the internal structure of candidate 5**:

```
CANDIDATES (6)
  1  The promoted count rule's carrier 1 has a sub-shape.
  2  The packet is the artifact that travels, and packet assembly is itself a place claims are made.
  3  An artifact selected by recency is not bound to its purpose.
  4  A restore is verified, not assumed.
  5  Asserting a document's or a check's state from memory of prior packets rather than from the thing itself.
  6  A census recorded inside the document it censuses goes stale as that document grows.

NOT CANDIDATES (4) — candidate 5's own structure
     Instances, an open list  ·  (viii)  ·  Operational close for (viii)  ·  (vi) is the list's first append
```

**Controls, because a bare enumeration is a count without a truth-maker.** Same pattern, same
flags, over §Ratified decisions → **15**; over §Rows filed → **1**. Both non-zero, so the pattern
finds bold leads where they exist and the classification above is a reading of real hits.

Each is promoted or dropped at this close. **None is promoted here** — that is §7's distillation
and verification work, which the stop below prevents reaching.

## 13. G4 — §Not established, every item. **STOP AND REPORT.**

**The enumeration, derived not copied.** Population `^[0-9]\+\. \*\*` over the section → **12**,
identical at `e047dd1` and at HEAD. **4 `[RESOLVED]` (1, 7, 8, 9), 8 `[OPEN]` (2, 3, 4, 5, 6, 10,
11, 12)**, tallied independently of the enumeration.

**The resolver check is what stops the ticket.** G4 requires that every `[OPEN]` item's resolver
name something that exists. Derived over the section:

```
$ grep -cE '\*\*Resolver:\*\*'  over §Not established   ->  3
   item 10  "an operator with sudo runs `shellcheck scripts/sprint.sh` and records the result"
   item 11  "whoever rules whether an invalid stub_responses entry should fail fast or stall"
   item 12  "that arm's author" — the first KNOWN_RED arm
POSITIVE CONTROL: 'resolver' anywhere in the document -> 21, so the token is not the problem.
```

**Three of the eight open items name a resolver. Five do not** — and all three that do were added
by hc-d, which is the ticket that introduced the label:

| Item | Open question | Resolver as written |
|---|---|---|
| **2** | Whether the chaos gate has ever run in a clean-store environment | **none named.** The item ends *"nothing established what one would do"* |
| **3** | hc-a Part 4's transition claim rests on a transcription | *"Whoever needs it opens the file"* — **no file named and no agent named** |
| **4** | No harness-side pointer to this document exists | **none named** — *"Recorded rather than fixed"*, a decision not to resolve, with a mitigation |
| **5** | hc-c's gate requires a live local Ollama | *"Carried to BL-133's territory."* BL-133 **exists** (`docs/backlog-2026-06.md:7584`) — but **hc-d discharged its face 2** and **R2 put face 1 out of scope**, so whether that territory still has an open carrier is itself unadjudicated |
| **6** | Whether any consumer outside these two repos reads log output on stdout | **none named.** The residue is described; nobody is named to close it |
| 10, 11, 12 | — | named, and each names something that exists |

**And the document asserts otherwise.** §Not carried §Open for the close reads:
*"the open questions are §Not established's, whichever carry `[OPEN]` … **Each has its resolver
named**, and §Close criteria clause 3 is the read that sweeps them."* **That claim is false for
five of the eight.** It is a documented claim contradicted by the section it describes — and it is
load-bearing, because §Close criteria clause 3 is the close's own sweep and it was written trusting
that sentence.

**Why this is a stop and not a fix.** G4's own words: *"An open item whose resolver names nothing →
stop and report; that is R13's own failure and it is not hc-e's to paper over."* Naming resolvers
for items 2, 3, 4, 5 and 6 is **authoring** — it decides who owns five open questions — and
authoring belongs to the reviewer under decision 11, R12 and R13. hc-e's own `Do not generate`
forbids the alternative in terms: *"No relaxation, rewording or quiet resolution of any `[OPEN]`
§Not established item to make the close read complete."* Closing over a false completeness claim is
exactly the silent-green shape this round has spent twelve rounds learning to catch.

**One qualification, so the report is not overstated.** Items **4** and **2** may not need a
resolver at all: item 4 is an explicit decision *not* to fix, and item 2 may be a question nobody
in this round owns. If so the remedy is not five resolvers — it is a ruling that some §Not
established items are *carried observations* rather than *open questions with owners*, and a
correction to §Not carried's sentence to match. **That ruling is not mine to make**, which is why
this stops here.

## 14. G5 and G6 — **not run**, and named rather than omitted

G4 stopped the ticket, so **G5 (§Close criteria, clause by clause) and G6 (the export set's
population) were not run.** No verdict is claimed for either. They are not blocked by anything
found here and should run in the session that reopens after G4's stop is resolved.

Recording this because a gate report that simply ends after its last executed item is
indistinguishable from one whose remaining items passed.

## 15. What unblocks this

A reviewer ruling on the five open items without resolvers — either a named resolver for each, or
a ruling that some §Not established entries are carried observations rather than owned questions —
**and**, either way, a correction to §Not carried's *"Each has its resolver named"*, which is false
as written and which §Close criteria clause 3 depends on.

Nothing else in the gate is outstanding: G1, G2 and G3 all returned **proceed**, and the seven, the
four/three split, and the six candidates are all derived and on the record above, so the session
that reopens does not re-derive them.

## 16. Not reached, not dropped

- **§7's ritual** — the scan, the distillation, the commit, the verification step and its
  prior-claims census over the **t1a-p three** — untouched.
- **The export boundary** — untouched. The manifest is not regenerated, nothing is staged for
  upload, and the Done-check's step 6 hand-off has not been reached. **hc-e is not closed.**
- **The milestone summary** — not written.
- **§Close criteria's six clauses** — not read; that is G5's work.
- **No backlog row filed or closed.** §Rows filed still reads *"Empty at hc-b"*.
