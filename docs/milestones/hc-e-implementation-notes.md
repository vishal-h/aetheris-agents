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

---

# Round 2 — R21, the re-labelling, and a stop at G5

**Repos.** agents from `83ef305`, harness `48f59e7` (untouched, clean). **Date.** 2026-08-09.

> **Outcome: R21 landed, the five entries were re-labelled, §Not carried was corrected, G4 was
> amended and re-run PROCEED — and the ticket STOPPED at G5, on §Close criteria clause 3.**
> G6 not run. Still no close work.

---

## 17. The two `[V]`s, checked before transcription

### 17a. Item 3's `[V]` — name the file. **It cannot be named, and that is the answer.**

The `[V]` asked which file hc-a Part 4's transition claim concerns, and said that if it cannot be
identified from any committed artifact, saying so *"makes the item stronger, not weaker."* **It
cannot be.**

**Three in-repo mentions exist and every one refers to the claim without stating its content:**
this entry; `docs/milestones/hc-b-implementation-notes.md` §7 *Open, forwarded*
(*"Rests on a transcription in neither repo; not re-derived, not acted on"*); and hc-e's own notes
quoting the entry. The harness returns **0** files for `hc-a Part 4` — **positive control**,
`hc-consolidation` over the same repo returns **2 files**, so the harness is searchable and the
zero is absence rather than a broken search. §Ticket set → hc-a states it directly: *"Its findings
are not in either repo."*

So the settling condition is **two-part**, and the transcribed entry says so: recover what the
claim was about — which no repo search can do — and only then open the file it names.

### 17b. Item 5's checkable specifics — both confirmed, and one observation reported

**The supervisor clause, read rather than cited.** `worker_child_spec/1`'s first head is
`defp worker_child_spec(%{provider: "stub", mcp_servers: []}), do: []` —
`../aetheris/lib/aetheris/agent/supervisor.ex:62`, read at harness `48f59e7`, the file last
changed at `36326d7`. A stub provider short-circuits to no worker **only when `mcp_servers` is
empty**, so a non-empty list falls through and a worker is spawned. The settling condition is
sound.

**"No such agent file exists" — verified, not carried.** The three files under
`../aetheris/agents/` mentioning `mcp_servers` are `research_orb.exs` and `research_orb_v3.exs`
(`provider: "anthropic"`) and `research_orb_local.exs` (`provider: "ollama"`). None is `stub`.
**Positive control:** 20 `.exs` files in that directory, so the search reaches them.

**One observation, reported and not folded into the settling condition, which is the reviewer's.**
`provenance/agents/search_agent.exs` **in this repo** takes
`provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"` (`:24`) and builds `mcp_servers`
non-empty when `CORPUS_SEARCH_MCP_ENABLED=true` with `PROVENANCE_DB_PATH` set (`:5`–`:21`, `:37`),
read at agents `83ef305`. **`AETHERIS_PROVIDER=stub` over that existing file satisfies the same
predicate**, so the configuration is reachable today without writing anything. It sits outside the
entry's stated directory, which is why the entry's literal claim holds — recorded in the entry so
a later round knows before writing a new agent.

## 18. R21, and the five re-labelled

R21 transcribed verbatim into §Ratified decisions between R20 and the m4 table. Each of the five
entries keeps its body unchanged and gains a dated block, per decision 7:

| Item | Was | Now | What the block adds |
|---|---|---|---|
| 2 | `[OPEN]` | `[OPEN] (b)` | settled by a chaos run in a clean store, output retained. No owner |
| 3 | `[OPEN]` | `[OPEN] (b)` | settled by opening the file — **and the file cannot be identified**; §17a |
| 4 | `[OPEN]` | **`[DECIDED]`** | never an open question; carried mislabelled from A7 and inflating every count by one |
| 5 | `[OPEN]` | `[OPEN] (b)` | the BL-133 pointer withdrawn; settled by a stub+`mcp_servers` agent, clause cited and read |
| 6 | `[OPEN]` | `[OPEN] (b)` | **unresolvable in principle** — the population is outside both repos; mitigation only |

Items 10, 11 and 12 gain `(a)`; they already carried `**Resolver:**` labels.

**And A7's census block, which R21 staled inside the same commit.** The block read *4 resolved,
8 open, 12 total*. Item 4 leaving `[OPEN]` makes that **4 resolved, 1 decided, 7 open**. A further
dated block re-derives it, stamped, with the enumeration printed — the block's own rule applied to
the block a third time. **The `8 open` that G4 stopped on was one too large**, and one of its
eight was a decision mislabelled since A7. The stop stands on its own ground regardless: five of
those eight named no resolver.

## 19. §Not carried, corrected

*"Each has its resolver named"* replaced by R21's two kinds, with **no universal claimed** and a
dated block quoting the original. Per A5's lesson, the fix is not a better universal — it is to
stop carrying one.

## 20. G4 amended — and the amendment is **not** a relaxation, tested rather than asserted

The transcribed amendment carries its own `[amended]` block and quotes the original beneath. The
reviewer's caution — *"a gate that stopped a ticket, edited so the ticket passes, is the exact
shape this round exists to catch"* — is answered with two runs, not with a claim.

**Test 1 — run the AMENDED G4 against the PRE-EDIT tree (`83ef305`).** If the amendment were a
relaxation it would pass there.

```
[DECIDED] prefixes present            : 0
OPEN items carrying a kind            : 0  of 8 open
'Settled by' clauses                  : 0
```

**It stops, on two conditions the original G4 could not express:** item 4 is a decision carrying
`[OPEN]`, and every carried unknown lacks a settling condition. **The amended gate is strictly
harder to pass on the very tree the original stopped on.**

**Test 2 — run the ORIGINAL G4 against the CORRECTED tree.** If the amendment were what made the
defect go away, the original would now pass.

```
OPEN items now             : 7
'**Resolver:**' labels now : 3
```

**It still stops.** The original's requirement is unmet and was never made to be met — no owner
was invented for items 2, 3, 5 or 6. **The defect survives the amendment**, which is the test the
reviewer named.

## 21. G4 as amended, re-run at HEAD. **PROCEED.**

```
population                    : 12   (unchanged; this round adds no numbered item)
OPEN with no kind (must be 0) :  0
(a) items : 3   '**Resolver:**' labels : 3
(b) items : 4   'Settled by' clauses   : 4
[DECIDED] : 1
```

- **Every (a) resolver names something that exists.** 10 → `scripts/sprint.sh` and an operator
  with sudo; 11 → whoever rules on invalid `stub_responses`; 12 → the first `KNOWN_RED` arm's
  author, and `expected_fail`/`known_red_healed` exist in `sprint.sh` (`:106`, `:142`) with zero
  call sites, which is what item 12 records.
- **Every (b) item names what would settle it** — four clauses, four items.
- **No `[DECIDED]` item is mislabelled `[OPEN]`, and no `[OPEN]` item is a decision in disguise.**
  Checked one by one: 2, 3, 5 and 6 are genuine unknowns; 10 is blocked on tooling; 11 needs a
  ruling; 12 needs a design decision or a first arm. None is a considered choice not to act.

## 22. G5 — §Close criteria, clause by clause. **STOP AND REPORT, on clause 3.**

The check that would settle each clause at HEAD:

| Clause | The check at HEAD | Form |
|---|---|---|
| **1** | For each row in §Ticket set, read the backlog rows it claims to close and confirm each is closed there, and the reverse | checkable |
| **2** | Read §Rows filed's population and confirm each filed row has a closure record in one of the two shapes | checkable — **and it will find a defect**; see §24 |
| **3** | Sweep §Not established item by item and record each as *resolved, still open, or superseded* — and if resolved, where | **NOT checkable as written** |
| **4** | For each decision in the log, confirm no divergence is left silent; R6/decision 13 already has its dated record | checkable |
| **5** | Residual only — §7's verification step and its prior-claims census carry it | checkable |
| **6** | Restate `docs/milestones/`'s population at the boundary, **both halves**, with `docs/rig/milestones/` as the counter-example | checkable |

**Why clause 3 stops.** Its disposition set is *"resolved, still open, or superseded"* — **three**
values. **R21, landed in this same round, added a fourth**: `[DECIDED]`. Item 4 now carries it,
and clause 3's own vocabulary cannot express item 4's standing. A sweep run as written must either
report item 4 under a heading that is false for it, or silently omit it — and an omitted item in a
close sweep is exactly the silence this section exists to prevent.

```
clause 3 mentions 'resolver'  : 0    <- so it does NOT inherit the §Not carried defect
POSITIVE CONTROL, 'resolver' document-wide : 32   <- the token is findable; the zero is real
clause 3 mentions 'decided'   : 0
```

**The `[V]` result, stated separately from the stop.** The authorised check was whether clause 3
*assumes every open item has a resolver*. **It does not** — zero occurrences, against a control of
32. So the authorised correction does not fire and **clause 3 was not edited.**

**Why the defect was not fixed anyway.** The gap is real, the fix is one word, and it is *this
round's own doing* — R21 changed the section's vocabulary without updating the one close criterion
that enumerates it. But the authorisation to edit clause 3 was conditional on the resolver defect,
which does not hold, and *"changing a close criterion during a close needs saying out loud."*
Editing it on my own authority would be the same class as inventing a resolver to clear G4: making
the gate pass rather than reporting what it found. **Proposed correction, not applied:** clause 3's
disposition set becomes *"resolved, still open, decided, or superseded"*.

## 23. G6 — **not run.** G5 stopped the ticket. No verdict is claimed for it.

## 24. Findings reported, not fixed

**§Rows filed is stale, and clause 2's sweep is what will meet it.** It reads *"**Empty at hc-b**
… hc-c and hc-d populate this section; hc-e sweeps it under clause 2."* **hc-d filed BL-135** at
`f8ed90f`, and hc-e's opening edit folded it onto BL-075. The section was never populated, so a
row exists that §Rows filed does not name. Not fixed here: populating it is close work under
clause 2, and this round is stopped.

## 25. Not reached, not dropped

- **§7's ritual** — the scan, the distillation, the commit, the verification step and its
  prior-claims census over the **t1a-p three** — untouched.
- **The export boundary** — untouched; the manifest is not regenerated and nothing is staged.
  **hc-e is not closed.**
- **The milestone summary** — not written.
- **G6** — not run; §23.
- **No backlog row filed or closed** by this round.

---

# Round 3 — clause 3 corrected, the vocabulary sweep, G5/G6 proceed, and a stated stop inside §7

**Repos.** agents from `8082e40`; harness from `48f59e7` — **the harness is touched this round**,
for the one promotion §7's census produced. **Date.** 2026-08-09.

> **Outcome: A, B, C, D applied; G5 re-run PROCEED; G6 PROCEED; §7's prior-claims census run and
> its one absent rule promoted and verified. The ticket then STOPS at a stated point inside §7** —
> before the distillation of this round's own seven candidates, and before the Done-check. hc-e is
> not closed and the export boundary was not approached.

---

## 26. A — clause 3 corrected, with the more-or-less test on the record

Disposition set now reads *"resolved, still open, **decided**, or superseded"*. The dated block
beneath the table carries the justification verbatim: **more, not less** — a fourth disposition
means item 4 must be *reported* rather than omitted or misfiled, no item leaves the sweep, and one
that had no truthful heading now has one. The contrast case is named so the shape is legible:
dropping `superseded` to make a sweep shorter would have been a relaxation. Original kept per
decision 7.

## 27. B — the vocabulary sweep. Population derived, four verdicts, one refutation

**Pattern** `\[RESOLVED\]|\[OPEN\]|\[DECIDED\]` over the whole file → **33 hits**, of which **12
are §Not established's own item heads**, leaving **21 across 14 sites**. Second pattern for prose
enumerations (`resolved, still open|…or superseded`) → clause 3 alone. **Positive control:**
`Not established` → **25**.

**Corrected — three members that enumerated an incomplete set:**

| Member | Read | Now |
|---|---|---|
| §Close criteria clause 3 | *resolved, still open, or superseded* | + `decided` (block A) |
| A7's preamble instruction | *Read each item's `[RESOLVED]` / `[OPEN]` prefix* | + `[DECIDED]` |
| A4's block: *the per-item prefixes are authoritative* | two values, *"once already"* | three values, *"twice already"* |

The last two are corrected **in place under decision 8** — *live operational guidance is corrected
in place* — because both tell a reader **how to determine an item's state** rather than recording
what a figure was. The dated blocks that record past figures are untouched.

**Correctly incomplete, left alone:** G4's quoted original inside its `[amended]` block. A
historical quotation that gained a value it never had would stop being a quotation.

**Refuted rather than assumed:** hc-e's `Contract refs` was named as an expected member. It
carries **0** prefix tokens and enumerates nothing. **It is not a member** — recorded, because the
instruction was to confirm expected members rather than assume them, and one did not hold.

**Reported ambiguous, not decided:** hc-e's `Do not generate` forbids *"relaxation, rewording or
quiet resolution of any `[OPEN]` item"*. R21 introduced a move the wording does not obviously
reach — re-labelling `[OPEN]` → `[DECIDED]`, which removes an item from the open count without
touching a word of its body. Done openly it is a correction (item 4). Done quietly it is the
prohibited act wearing R21's clothes. The note is in the document; the ruling is not mine.

## 28. C — item 5's settling condition, sharpened, anchors re-derived not carried

Transcribed verbatim, with the current condition kept beneath per decision 7. The `[V]` required
re-derivation rather than carrying the r2 packet's numbers: at agents **`8082e40`**, file last
changed **`bda1fef`** — `:3`, `:6`, `:21`, `:24`, `:37`; and `supervisor.ex:62` at harness
**`48f59e7`**, file last changed **`36326d7`**. **All five agents-side anchors and the harness one
resolve unchanged**, which is a result and not a formality: the alternative was a silent carry.

## 29. D — the vocabulary-sweep candidate, landed, with its first application recorded

Transcribed verbatim into §Promotion candidates, followed by a dated block recording that the
sweep it asks for was **then run** — population, control, and the four verdicts above. The
candidate's own instrument, exercised in the commit that files it.

## 30. G5 re-run. **PROCEED.**

Every clause's check restated at HEAD:

| Clause | The check | Form |
|---|---|---|
| 1 | For each §Ticket set row, read the backlog rows it claims to close and confirm both directions | checkable |
| 2 | Read §Rows filed's population; confirm each filed row has a closure record in one of the two shapes | checkable — and it will find §24's defect |
| 3 | Sweep §Not established item by item: resolved / still open / decided / superseded, and if resolved, where | **checkable** — the states in use are `[RESOLVED]`, `[OPEN]`, `[DECIDED]`, and clause 3 now has a heading for each |
| 4 | For each decision, confirm no divergence is left silent; decision 13 already has its dated record | checkable |
| 5 | Residual only; §7's verification step and its census carry it | checkable |
| 6 | Restate `docs/milestones/`'s population at the boundary, both halves, with `docs/rig/milestones/` as counter-example | checkable |

## 31. G6. **PROCEED.** The export set's population, derived before any regen

**25 rows**, enumerated in full in the packet: **13 `aetheris-agents`, 12 `aetheris`**.
**Positive control:** `grep -c '^|'` over the table → **27** = 25 + header + separator, so the
row pattern is not silently dropping lines. The regen's count is compared against this with both
printed, when the boundary is reached.

## 32. §7's prior-claims census — run, and it found one

**Population, derived.** Documents claiming learnings were promoted, searched by substance across
both repos (`learnings promoted|rules promoted|review-discipline learnings|promotions? landed|complete`):
**10 agents-side, 2 harness-side**. Of these, three carry an actual promotion-claim block from the
preceding cycle, and **every item in every block was checked — not the ones that looked
unfamiliar**, which is §7's explicit warning.

**Block 1 — `handoff-linode-provider-three-kickoff-2026-08-04.md` §Review-discipline learnings
promoted (4 items).** All four present. Re-verified rather than inherited from the m3 close's
census: click-through merge gate (harness 1), name-the-branch (harness 1), `drift_check`
current-not-complete (agents 1), remove-all-upload-all (harness 1 / agents 1), primitive-known-good
(harness 1).

**Block 2 — `handoff-cloudcost-rig-batch-close-2026-08-04.md` §Review learnings promoted (4
items). Never censused before, and this is where the census earns itself.** By token, three
returned zero. By **substance** — several wordings each, terms recorded — two of the three are
present after all:

- **"Rebuild Rig after each frontend merge"** — its *invariant* is present: *"a gate is only valid
  if the build under test holds the change"* (harness `:844`). The Tauri-specific mechanism is not,
  and does not need to be. **Not absent.**
- **"Re-derive, don't copy; the live store is the oracle"** — present as *"A document that quotes
  repo state is a snapshot with no invalidation — verify before acting… when they disagree the
  source wins"*, *"An inherited citation is still uncited"* (harness `:787`), and *"enumerate
  before fixing the class"* (`:710`). **Not absent.**
- **"Anti-vacuity — every all-empty/degrade assertion needs a positive control."** **ABSENT from
  both files**, and absent in substance, not only by token. The harness carries the **mutation
  test** (`:594`–`:596`) — *construct the broken state and watch the check fail* — which is a
  **different instrument**: the mutation test proves a check *can* fail; a positive control proves
  a *zero* means absence rather than a broken search. `grep -c 'positive control'` over both files
  → **0** and **0**. **Positive control for that search:** the same phrase over
  `hc-consolidation.md` → **12**, so the term is findable and the zeros are real.

**Block 3 — `handoff-m3-close-2026-08-05.md`.** Carries **no learnings section by design** and says
so, pointing at both `CLAUDE.md` files instead. Its claim — *"the four are promoted, along with
five m3 learnings and a credential-provenance rule"* — is the claim Block 1 verifies above. **A
document that makes no restatement makes no unverifiable claim**; it is the shape the m3 close
adopted after its own census, and it works.

## 33. The promotion the census produced, and its verification

§7: *"anything absent is promoted now with a `Source:` naming the cycle it came from and the fact
that it was found absent."*

**Landed in `../aetheris/CLAUDE.md`** §Continuous learning → Workflow patterns → Silent-wrong-answer,
immediately after the mutation-test paragraph, because it is that paragraph's mirror. Harness
rather than agents: it sits inside an existing harness entry it completes, and hc-e's `Touches`
provides for either with **harness first**.

**§7's verification step, performed by opening the file** — the entry quoted with its surrounding
lines in the packet, at `../aetheris/CLAUDE.md` §Silent-wrong-answer (`:599`), read after the edit.
`grep -c 'positive control'` over that file → **2** where it was **0**. The promotion is complete
because the entry can be read out of the file, not because the edit was made.

## 34. **The stated stop, and where it falls**

The reviewer authorised a partial close that **names its boundary**. This is the boundary.

**Complete and recorded:** blocks A–D; G5 re-run; G6; §7's prior-claims census over all three
blocks, every item; the one promotion it produced, verified by reading the destination file.

**Not done, and not started:**

1. **§7's scan and distillation over this round's own seven §Promotion candidates.** Each must be
   promoted or dropped, and a promotion authors a standing rule in a `CLAUDE.md`. Seven of those is
   the largest single piece of hc-e and it deserves its own round and its own review — doing it
   quickly is how a vague rule gets promoted, which §7's own closing test warns about.
2. **The Done-check, items 1–9.** In particular item 1's full harness gate set
   (`format`, `compile --warnings-as-errors`, `hex.audit`, `credo --strict`, `dialyzer`, `test`)
   has **not** been run this round, and it should run over the *complete* content edit set rather
   than a partial one — the export boundary is the last content operation by design, and content
   is not complete.
3. **The export boundary** (Done-check 4–7) — untouched. The manifest is **not** regenerated,
   nothing is staged, and the operator hand-off at step 6 has not been reached.
4. **The milestone summary** — not written.
5. **§Close criteria's six sweeps** — G5 established each has a checkable form; **none has been
   run**. Clause 2 will meet §24's §Rows filed defect, and the reviewer's two carried questions
   (record BL-135 as *filed and folded*, and rule whether a folded row counts toward the
   population) belong to that sweep.

**hc-e is not closed.** `drift_check --strict` is green at 0 FAIL with the three expected
staleness WARNs, which is the state to expect mid-cycle, not the boundary's own truth-maker.

---

# Round 4 — F11, the re-labelling ruling, and §7's distillation

**Repos.** agents from `088f9c2`; harness from `02db6bb` — **cross-repo, harness first.**
**Date.** 2026-08-09.

> **Outcome: F11 reconciled (all three pairs, no stop); the `Do not generate` ruling applied; §7's
> distillation run over all seven candidates — one promoted, five merged, one general claim
> dropped, every entry verified by reading it out of its destination file.** The Done-check, the
> six sweeps, the boundary and the milestone summary remain untouched. **hc-e is not closed.**

---

## 35. F11 — the three pairs, reconciled. **No stop.**

**(a) Which commit each figure was derived at.** §27's and §32's figures were derived **before**
this round's own commit: the vocabulary sweep ran against the clean tree at **`8082e40`**, and the
`positive control` count ran mid-edit against a working tree whose hc-consolidation.md content
matched `8082e40` for that token. §1's figures were derived **post-commit**, at **`088f9c2`**, when
the packet was generated.

**(b) Stamped, with both trees printed.** Same pattern, same flags, one command per row:

```
figure                                        8082e40   088f9c2   reconciles
prefix tokens [RESOLVED|OPEN|DECIDED]              33        41     yes  (+8)
'Not established'  (the control)                   25        30     yes  (+5)
'positive control'                                 12        13     yes  (+1)
§Not established item heads (invariant)            12        12     yes  ( 0)
```

**Each pair is one count at two trees, not a contradiction.** The item-head row is the control on
the reconciliation itself: a figure this round did **not** move stays put across the same two
trees, so the three that moved moved because of content and not because of a drifting pattern.

**(c) Nothing failed to reconcile**, so there is nothing to stop on. And the `+1` is worth naming
rather than absorbing: the extra `positive control` hit is **this round's own §Ticket set row
saying *"found one rule absent in substance — a negative needs a positive control"***. The count
was moved by the sentence describing the census that produced it — the same shape as hc-d's
8-against-10, arriving in the packet that files the candidate about it. That is now a promoted
standing rule (§36, candidate 1+6) and this is its first instance under the rule rather than
before it.

## 36. §7's distillation — the population, re-derived

**Not carried from G3.** Pattern `^\*\*[A-Z(]` over §Promotion candidates → **11** bold leads at
`088f9c2`+worktree, where G3 recorded 10; the section has grown by D's candidate. **4 of the 11 are
candidate 5's internal structure** (*Instances, an open list*; *(viii)*; *Operational close for
(viii)*; *(vi) is the list's first append*), leaving **7 candidates**. **Positive controls**, same
pattern and flags: §Ratified decisions → 18, §Rows filed → 1.

**Scan inputs** per §7's own widening — *"the review files are not the only input"*: this round's
`docs/reviews/hc-*-review.md`, the four `hc-*` implementation-notes files, and this file's own
Rounds 1–3, which is where the sweep-discovered defects live that no reviewer ever saw.

## 37. The outcome table

| # | Candidate | Outcome | Destination | Verification |
|---|---|---|---|---|
| 1 | The promoted count rule's carrier 1 has a sub-shape (a prediction carried as a count) | **MERGED with 6** | harness → *a count is a claim about a population* | `0 → 1` |
| 2 | The packet is the artifact that travels, and packet assembly is itself a place claims are made | **PROMOTED** | agents → §Learning — BL-007 | `0 → 1` |
| 3 | An artifact selected by recency is not bound to its purpose | **MERGED** | harness → the command-binding carrier | `0 → 1` |
| 4 | A restore is verified, not assumed | **MERGED** | harness → the mutation test | `0 → 1` |
| 5 | Asserting a document's or a check's state from memory of prior packets | **MERGED** (its operational close only); **general claim DROPPED** | harness → *an inherited citation is still uncited* | `0 → 1` |
| 6 | A census recorded inside the document it censuses goes stale as that document grows | **MERGED with 1** | harness → same entry as 1 | (entry 1) |
| 7 | A vocabulary change owes a sweep of everything that speaks it | **MERGED** | harness → *the class is not only code* | `0 → 1` |

**Seven candidates → six entries.** Five new paragraphs in the harness, one in agents.

**Why each landed where it did.** 1+6, 3, 4, 5 and 7 all extend rules whose subject already lives
in the harness `CLAUDE.md` — counts, command binding, the mutation test, citations, the class
census — and each is written as a continuation of the entry it belongs to rather than as a sibling
that will be read as unrelated. **2 is the exception and goes agents-side**, because the packet-rule
family lives in `CLAUDE.md` §Learning — BL-007 and this is a packet rule; it cites harness
`Packet-integrity` rather than duplicating it.

**The one drop, recorded rather than avoided.** Candidate 5's *general* claim — asserting a
document's state from memory of prior packets — is **already covered** by the harness's *"An
inherited citation is still uncited"*, which says the same thing in the same file. Promoting it
again would have produced two entries a reader must reconcile. What was **not** covered is its
operational close from instance (viii): **an identifier is resolved, never transcribed** — the
sub-shape where the identifier was *invented* rather than copied, so no re-reading can refute it
and only resolving can. That is the part promoted, and the drop is stated in its own `Source:`
line so the next reader knows the general claim was considered and why it did not land again.

**Two merges of two candidates into one rule.** 1 and 6 are the same rule at different distances:
a figure whose population you could not enumerate when you stated it (a prediction), and a figure
whose population moved after you stated it (a census inside its own subject). Both close the same
way — stamp the commit, prefer a pointer — so they became one addition rather than two entries
that would be read as unrelated. 7 merges into the class-census rule as its *change-triggered*
half, since the existing rule fires on finding a defect and this one fires on making a change,
which is easier to miss because nothing has gone wrong yet.

**Nothing was promoted to avoid the appearance of dropping.** Each of the seven produced a
standing instruction someone could follow without the narrative; where one did not, it was dropped
and said so. **No candidate was left as prose**: none had to be held back as "not yet statable in
one instruction".

## 38. §7's verification step — every entry read out of its destination file

Performed **after** the edits, with a before/after count for a token unique to each entry. Full
quotations with surrounding lines are in the packet.

```
unique token                                      before  after  file
a count names the commit it was derived at             0      1  aetheris/CLAUDE.md
Bind an artifact to what produced it…                  0      1  aetheris/CLAUDE.md
…the restore is the second one                         0      1  aetheris/CLAUDE.md
An identifier is resolved, never transcribed           0      1  aetheris/CLAUDE.md
A vocabulary change owes a sweep…                      0      1  aetheris/CLAUDE.md
A packet publishes the invocation…                     0      1  aetheris-agents/CLAUDE.md
POSITIVE CONTROL — a token deliberately absent         0      0  both
```

**Six of six can be read out of the file**, which is what makes the promotion complete rather than
the edit having been made.

## 39. Not reached — unchanged from §34, minus the distillation

The Done-check items 1–9 including the harness gate set; §Close criteria's six sweeps and their two
carried questions about BL-135 as *filed and folded*; the export boundary; the milestone summary.
**hc-e is not closed and the manifest is not regenerated.**

---

# Round 5 — F12, and a stop after it

**Repos.** agents from `04a329a`; harness from `712d434` — **cross-repo, harness first.**
**Date.** 2026-08-09.

> **Outcome: F12 fixed in both files, with a discriminating instrument rather than the one I first
> wrote; the carry candidate filed. The ticket then STOPS before r5's remaining items.** The six
> sweeps, the milestone summary, the Done-check and the boundary are untouched. **hc-e is not
> closed.**

---

## 40. F12 (a) — the three moves

Each inserted paragraph now follows the preceding entry's complete claim-plus-`Source:` unit. **No
prose was edited**; the blocks were moved whole, with their own `Source:` lines attached.

| Site | Entry | Was between | Now follows |
|---|---|---|---|
| harness | the restore rule | the positive-control paragraph and its `Source:` | that `Source:` block, complete |
| harness | *a count names the commit* | *a count is a claim about a population* and its `Source: t1a…` | **both** of the truth-maker entry's `Source:` lines |
| agents | *a packet publishes the invocation* | the full-output rule and its `Source: m4-cloudcost t5c…` | that `Source:` line |

The harness count-stamp case needed care the other two did not: the truth-maker entry carries
**two** `Source:` lines by design, so "after the entry's Source" means after the second, not the
first. Moving it after only the first would have reproduced the defect one line down.

## 41. F12 (b) — the check, and **the first check I wrote was wrong**

**Recorded because it is the round's own subject.** My first instrument asked whether the line
above each insertion *starts* with `` `Source: ``. It reported **4 of 6 misplaced after the fix**,
including two that were correct — because `Source:` blocks in these files **wrap across lines**, so
the last line of one ends with a backtick and starts with prose. **A check keyed on a line prefix
where the structure is a multi-line block**: the substring-versus-structure carrier, inside the
check written to catch a structural defect.

**The control is what refuted it.** Run over every paragraph-initial bold entry in both files, that
check reported **34 of 55** harness and **28 of 50** agents as "misplaced". A pattern that fires on
two-thirds of a file is not finding a defect; it is describing the file. **A check that cannot
distinguish the defect from house style is not a check** — which is the instruction (b) gave, and
it is what made the wrong instrument visible.

**The instrument that discriminates: two `Source:` blocks back to back.** That is the visible
symptom — a `Source:` whose preceding non-blank run also ends a `Source:` — and it is exactly what
the packet printed at site 1 and I did not read.

```
harness @712d434 (pre-fix)   -> 4   :619 (site 1)  :846 (site 2)  :851  :917
harness @worktree (post-fix) -> 2                                  :830  :917
agents  @04a329a (pre-fix)   -> 1   :494 (site 3)
agents  @worktree (post-fix) -> 0
```

**The two survivors are not residue and are not fixed.** `:830` is the truth-maker entry's t1a +
m4-cloudcost pair; `:917` is the cite-by-anchor entry's m3-close + m3-t2 pair. Both are **one entry
carrying two sources**, which is legitimate. **Positive control on the baseline:** the same
instrument over `288c8ef` and `b4d782a` — the harness `CLAUDE.md` as it stood before this round
touched it — returns **2** at both. So the file's baseline is 2, this round pushed it to 4 + 1, and
the fix returns it to **exactly the baseline**. A zero would have been the wrong target.

## 42. F12 (c) — §7's verification re-run, **asserting** what surrounds rather than quoting it

The distinction (c) asked for: the quotation surfaced this defect and the reading of it did not, so
the check now states the structural fact instead of printing lines for a human to notice.

| Entry | Above ends | Entry begins | Own `Source:` |
|---|---|---|---|
| count-stamp (1+6), harness `:839` | the `Source:` block opened at `:830` | its own claim | `:849` |
| recency-binding (3), harness `:682` | the `Source:` block opened at `:678` | its own claim | `:690` |
| restore (4), harness `:617` | the `Source:` block opened at `:608` | its own claim | `:624` |
| identifier (5), harness `:874` | an **inline** `Source:` | its own claim | `:881` |
| vocab sweep (7), harness `:772` | the `Source:` block opened at `:768` | its own claim | `:780` |
| packet (2), agents `:478` | the `Source:` block opened at `:476` | its own claim | `:489` |

**Six of six**: the entry above ends with its own attribution, the entry below opens with its own
claim, and each carries its own `Source:`. The identifier entry's neighbour ends with an *inline*
Source rather than a block — stated rather than smoothed, because a check that only recognised
blocks would have called it a defect.

## 43. The carry candidate, filed and marked as arriving after the distillation

Transcribed verbatim into §Promotion candidates with its `[filed after hc-e r4's distillation
completed; carried to the next cycle rather than reopening §7's distillation step, which is done.]`
mark. **§7's distillation is not reopened** — the candidate is recorded for the next cycle's ritual,
which is what the mark exists to say.

## 44. The stop, and where it falls

**Complete and recorded:** F12 (a), (b) and (c) in both files; the carry candidate.

**Not started, and named:** §Close criteria's six sweeps with their results — including clause 2's
§Rows filed defect, BL-135 recorded as **filed and folded**, and the ruling on whether a folded row
counts toward the population; the milestone summary; Done-check items 1–3 (the harness gate set,
`shellcheck`, the pre-boundary `drift_check`); items 4–5 (content complete, the manifest regen with
its count printed beside G6's derived **25**); and item 6's operator hand-off.

**The boundary is the one r5's instruction named** — the sweeps and the summary sit ahead of the
gate set and the regen — except that F12 alone consumed the round, because the first instrument I
wrote for it was wrong and the control was what showed it. **hc-e is not closed**, the manifest is
not regenerated, and nothing is staged for upload.

## 45. One live instance of a rule this round promoted, in the act of committing it

The agents-side commit for F12 was issued in a shell whose `cd` had persisted into the **harness**
repo. `git add docs/milestones/` failed there with *"pathspec did not match any files"*, and the
`git status --porcelain` that followed reported **`agents=0 dirty`** — a clean result about the
wrong repo, which is *"a check that reads the wrong thing reports a clean result, not an error"*
(harness `CLAUDE.md`), the exact carrier the recency-binding entry landed beside one commit
earlier.

**No damage: the harness commit `2ef0517` is correct and complete** — one file, the two moves, 22
insertions and 22 deletions — and the agents tree was simply left uncommitted rather than partially
committed. **Caught by the pathspec error, not by the status line**, which would have read the same
had the work been lost. Re-issued with `git -C <repo>` on every command, which is what the rule
says and what the rest of this round's checks already did.

---

# Round 6 — the six sweeps, run

**Repos.** agents from `dcf1d42`; harness `2ef0517`, **untouched this round**. **Date.** 2026-08-09.

> **Outcome: all six clauses run and recorded.** Two false claims about the repos fixed (BL-133's
> unrecorded discharge; clause 2's shape enumeration), the rulings applied, clause 6's sentence
> authored. **The bound held** — presentational defects found on the way were carried, not fixed.
> The milestone summary, the Done-check and the boundary are r7. **hc-e is not closed.**

---

## 46. Clause 1 — every ticket against the rows it claims, both directions

**Direction A — what §Ticket set claims, checked on the rows.**

| Ticket | Claims | On the row |
|---|---|---|
| hc-a, hc-b | closes nothing | — |
| hc-c | BL-105, BL-106 closed | **both**, shape A: `**DONE 2026-08-09 (hc-c).**` (`:6335`, `:6423`) |
| hc-d | BL-077 closed | **yes**, and **in a third shape** — `**Status:** Done 2026-08-09 — hc-d.` (`:3073`) |
| hc-d | BL-133 **face 2 discharged** | **NOT RECORDED — the sweep's one repo-side defect. Fixed.** |
| hc-d | BL-044 stays filed | correct: no closure record, and none owed |

**The defect and its fix.** BL-133 carried no disposition of any kind — no `Status:`, no `DONE`, no
note — while this document has said since `88183b8` that hc-d discharged its face 2. A reader of
the row could not have learnt it. **Fixed on the row**, not here: a `**Face 2 discharged 2026-08-09
(hc-d).**` paragraph naming the mechanism, the harness range `2d76a65`→`48f59e7`, and **why the row
stays open** (face 1 is untouched and R2 ruled it out of scope), with a pointer to what face 2 does
not cover — `mix test` output still routed nowhere, per hc-e's E4 and BL-075. **The work was hc-d's;
only the record was missing**, and that is said in the row's own provenance line.

**Direction B — every hc-* closure record on any row, checked against §Ticket set.** Derived across
**all three** shapes: shape A → 2 (BL-105, BL-106), shape B → **0**, shape C → 1 (BL-077).
**Three records, all three claimed here. No orphans.** **Positive controls**, the same three
patterns without the `hc-`/date filter: **11 / 16 / 26**, all non-zero, so a zero in shape B reads
as absence rather than as a pattern that never matches.

## 47. Clause 2 — §Rows filed, and a third closure shape the clause never named

**The clause's own subject was wrong, so it is fixed rather than carried** — the exception r6
names. Clause 2 enumerated **two** shapes at **9** and **15**. Derived at `dcf1d42`, one stated
pattern per shape:

```
A  ^\*\*DONE                          = 11   (clause said 9)
B  ^### BL-[0-9]+.*— DONE             = 16   (clause said 15)
C  ^\*\*Status:\*\* *(Done|Closed)     = 26   ← never named, and the most common of the three
```

**Shape C is how BL-077's closure is recorded**, so a sweep reading only A and B would have
reported **this round's own hc-d closure as missing**. All three counts stale, one shape absent;
the original table stands with a dated correction beneath it.

**§Rows filed, superseded with a derived population.** *"Empty at hc-b"* was true when written.
Derived now: the highest row is **135**, and **BL-135 is the only row at or above this round's
starting number** — population **one**.

| Row | Filed | Disposition |
|---|---|---|
| **BL-135** | 2026-08-09 (hc-d r3), agents `f8ed90f` | **folded onto BL-075** 2026-08-09 (hc-e's opening edit, E3) |

**Per the ruling: the fold is a disposition, not an erasure**, and hiding it would make the
duplication invisible to exactly the reader who needs it. **hc-c filed nothing** — it closed two
rows, and closures live on the rows.

## 48. Clause 3 — §Not established, all twelve

| | | | |
|---|---|---|---|
| 1 `[RESOLVED]` — resolved at hc-c | 2 `[OPEN] (b)` | 3 `[OPEN] (b)` | 4 `[DECIDED]` |
| 5 `[OPEN] (b)` | 6 `[OPEN] (b)` | 7 `[RESOLVED]` — by ruling, R15 | 8 `[RESOLVED]` — hc-d, R-i |
| 9 `[RESOLVED]` — anatomy edit r1 | 10 `[OPEN] (a)` | 11 `[OPEN] (a)` | 12 `[OPEN] (a)` |

**Four resolved, one decided, seven open (3 owned, 4 carried).** **Each resolved item's "where" is
its own dated block**, and the four blocks found — `hc-c`, `hc-d's opening anatomy edit`,
`hc-d, R-i`, `anatomy edit r1` — match items 1, 7, 8, 9 exactly. **The prefixes were read, not
assumed**, and every one is confirmed against its entry's body. Nothing is superseded.

## 49. Clause 4 — the decision log

**Twenty-one ratified R-decisions and sixteen m4 decisions by reference.** Divergences, enumerated
rather than assumed to be one:

- **Decision 13** — under review by R6, **resolved not overturned**, with its own dated disposition
  block (`:633`). The record clause 4 demands exists.
- **Decision 15** — **refuted narrowly by R11**, and the m4 table's own cell says *"carries as
  amended"*. Recorded, not silent.
- **Decision 16** — lapsed with m4's scope; R10 re-decides freshly. Recorded in the table.
- **R19** — amended by this round at A3 (a ticket instruction cannot suspend it), dated in R19's
  own block.
- **R13** — its resolver requirement was applied too widely by G4; **R21 corrects the application,
  not the decision**, and says so in its own closing line.

**No divergence is silent.** Every one carries a dated record in the document, which is the one
disposition clause 4 says is unavailable.

## 50. Clause 5 — the residual, and it is **not** empty

Clause 5 covers *"anything §7 does not itself verify about the promotions"*. §7's verification step
verified that each promoted entry **can be read out of its file**, and the prior-claims census
verified the preceding cycle's claims. **What neither covers is where an entry landed relative to
its neighbours** — and that is exactly the gap F12 found: three entries readable out of the file,
each orphaning the provenance of the entry above it. §7's step quoted the surrounding lines; it
does not assert what they are.

**So the residual is one item, it is real, and it is already carried** — the *an entry's
attribution is structural* candidate in §Promotion candidates, filed after r4's distillation. **The
residual is stated as non-empty rather than confirmed as nothing**, which is what the clause asks.

## 51. Clause 6 — the sentence, authored, both halves

Landed in `docs/project-knowledge-manifest.md` immediately above the existing *what this table does
not include* note, so a reader meets both together. **Half 1**: everything `docs/milestones/` holds
today is a working artifact, with the `m-eduloka-discovery-*` pair as precedent. **Half 2**:
`docs/rig/milestones/` is the counter-example — same path segment, two tracked files admitted on the
specification test — **so the rule reads the artifact's kind and never its directory**, and the
generalisation from half 1 is named as one that was asserted, checked and refuted.

**This is a content edit and it precedes the boundary**, as clause 6 requires.

## 52. The bound held — what was found and carried rather than fixed

- **Clause 2's counts for shapes A and B were stale (9→11, 15→16)** as well as the shape being
  missing. Fixed **only because** the shapes are clause 2's own subject; the staleness of the two
  numbers rode along with the correction rather than being chased separately.
- **No sibling sweep was run** for other stale figures in this document, and none was fixed.
- **§Rows filed's note about "the two shapes"** now under-describes the backlog in a second place.
  **Carried, not fixed** — it is presentational residue in this round's own paperwork, which the
  bound says to record and move past.

## 53. Not reached — r7

The milestone summary; Done-check items 1–3 (the harness gate set, `shellcheck`, the pre-boundary
`drift_check`); items 4–5 (content complete and committed, the manifest regen with its count
printed beside G6's derived **25**); and item 6's operator hand-off. **hc-e is not closed**, the
manifest is not regenerated, and nothing is staged for upload.

---

# Round 7 — F14 settled, F13 re-run, and a stop at clause 4

**Repos.** agents from `7dbdb7d`; harness `2ef0517`, untouched. **Date.** 2026-08-09.

> **Outcome: F14 settled in one command. F13's re-run STOPS the round** — the enumeration over all
> thirty-seven decisions finds **four divergences the five did not name**, per F13(d). The
> milestone summary, the Done-check and the boundary do not run. **hc-e is not closed.**

---

## 54. F14 — shape B's 15 → 16, settled in one command

```
$ diff <(git -C <agents> show e8cd5cd:docs/backlog-2026-06.md | grep -E '^### BL-[0-9]+.*— DONE' | sed 's/ —.*//') \
       <(git -C <agents> show HEAD:docs/backlog-2026-06.md    | grep -E '^### BL-[0-9]+.*— DONE' | sed 's/ —.*//')
  -> identical sets
  counts: e8cd5cd = 16    HEAD = 16
```

**The cause is named, not left unexplained.** Shape B was **already 16 at `e8cd5cd`** — the commit
whose ticket text asserted 15 — and the two enumerations are **identical, member for member**. So
**no heading appeared this round**, and the +1 is not a change in the corpus at all: the m4-era
**15** was derived with a pattern that differs from `^### BL-[0-9]+.*— DONE`. **Which** pattern is
not established, and is not worth a second command: the correction block's figure is derived at this
commit and stands on that, and the claim *"was 15"* is amended to say the prior figure counted
something else.

**Corrected in the block**: A's `9 → 11` is this round's doing (hc-c's two closures); **B's
`15 → 16` is not** — it is one count replaced by another over an unchanged set.

## 55. F13 — clause 4, re-run over the whole population

### 55a. The method, stated before it was run

**A decision diverges when the implementation does something the decision forbids, or fails to do
something it requires, and the document does not record it.** Three verdicts, and the third is a
real answer rather than an evasion:

- **NO DIVERGENCE** — this round's work engaged the decision's subject and followed it.
- **DIVERGENCE WITH RECORD** — the work departed, and a dated record exists in this document.
- **N/A** — this round's work never engaged the subject. Expected for decisions about tickets and
  scopes that never ran here.

The previous sweep's *"silent divergences: 0"* was a claim about thirty-two decisions nobody had
looked at. It is withdrawn and replaced by the enumeration below.

### 55b. The enumeration — all thirty-seven, printed beside the count

| # | Verdict | Where the record is, or why N/A |
|---|---|---|
| R1 | no divergence | retention + provenance stamp landed at hc-d |
| R2 | no divergence | a review file committed per round |
| R3 | no divergence | answered by the design; BL-044 stayed filed |
| R4 | no divergence | arm 2 not started; E4 established the blocker only |
| R5 | no divergence | hc-c's gate ran and answered by evidence |
| R6 | no divergence | one of its two outcomes, with its dated disposition block |
| R7 | no divergence | counter + `KNOWN_RED` + printed undeclared set |
| R8 | no divergence | every ticket that ran carried a step-1 gate |
| R9 | no divergence | no planted-resource assertion re-armed |
| **R10** | **N/A** | BL-108 out; never engaged |
| R11 | no divergence | hc-c carries the finding |
| **R12** | **DIVERGENCE WITH RECORD** | **not among the five.** Anatomy written before the ticket opens — **hc-d opened at 2 of 7 fields and hc-e at 2 of 7 with no gate slot**. Recorded: both stops, both anatomy edits, and §Not established item 7 for hc-b2 |
| **R13** | divergence with record | hc-e's catch-all deferred the gate with no resolver named; the stop and the discharge |
| R14 | no divergence | hc-c's gate ran on the operator's service |
| R15 | no divergence | applied to hc-b2 and to both anatomy-edit rounds |
| R16 | no divergence | the verdict keys on the status word |
| **R17** | **DIVERGENCE WITH RECORD** | **not among the five.** Three arms all resolving to FAILURE — **arm (c) is available but not automatic**, nothing pairs `known_red_healed` with the arm that declared the red. Recorded at §Not established **item 12** |
| R18 | no divergence | verified at hc-d |
| **R19** | divergence with record | hc-e's opening session did not write its own row; A3's amendment |
| R20 | no divergence | r1's findings landed in the notes, no review file created |
| R21 | no divergence | applied to all twelve items |
| **m4-1** | **DIVERGENCE WITH RECORD** | **not among the five.** The reviewer asserts no checkable specifics — fired repeatedly: the 41 and the ten (hc-b), *"exactly two slots"* (hc-c), and **F1's invented `3901121`**. Recorded in the m4 table's own cell and as instances (i)–(viii) |
| m4-2 | no divergence | a verification pass every round |
| m4-3 | no divergence | carried by R8 |
| m4-4 | no divergence | `hc-*` names final |
| **m4-5** | **DIVERGENCE WITH RECORD** | **not among the five.** *"The §7 promotion runs mid-cycle when the rules bind the cycle's own remaining tickets."* Rules that bound remaining tickets — recency-binding, restore-verified, positive-control — were **not** promoted mid-cycle; they were carried in §Promotion candidates and in each ticket's `STANDING` block, and promoted only at r3/r4. **Recorded**: §Promotion candidates' preamble states the deferral in terms — *"Candidates recorded here are promoted or dropped at hc-e … recording one is not promoting it"* |
| m4-6 | no divergence | pushes held; the one cross-repo pair landed harness-first |
| m4-7 | no divergence | used throughout |
| m4-8 | no divergence | used at r3's block B |
| m4-9 | no divergence | item 9's attribution |
| **m4-10** | **N/A** | no milestone-named-document classification arose |
| m4-11 | no divergence | named at every anatomy edit |
| m4-12 | no divergence | none planted |
| m4-13 | no divergence | reviewed, not overturned, dated |
| m4-14 | no divergence | hc-c's contract is this |
| **m4-15** | divergence with record | refuted narrowly by R11 |
| **m4-16** | **N/A** | lapsed with m4's scope; R10 re-decides |

```
population        : R1–R21 (21) + m4's 1–16 (16)              = 37
no divergence     : 27
divergence w/ rec : R12 R13 R17 R19 m4-1 m4-5 m4-15           =  7
not applicable    : R10 m4-10 m4-16                           =  3
                                                     27+7+3   = 37
```

### 55c. **The stop.** Four divergences the five did not name

F13(d): *"If the sweep finds a divergence the five did not name, that is a stop — report it, do not
fix it, and r7 waits."*

**R12, R17, m4-1 and m4-5.** All four carry dated records already — none is silent — but none was
named by §49's five, and §49's *"silent divergences: 0"* was reached without looking at them. **The
count was right by luck about the property it asserted and wrong about the work behind it.**

**Nothing is fixed.** Clause 4's result is now the table above rather than a total, and the round
stops here.

> **`[adjudicated 2026-08-09 (hc-e r8) — the stop is lifted, and the condition was the
> reviewer's and malformed. §55c's text above is unedited.]`**
>
> **The stop fired as written.** F13(d) said a divergence the five did not name is a stop, and the
> sweep found four. That is what the condition asked for and it was applied literally rather than
> read past.
>
> **The condition was malformed.** It was written expecting a **silent** divergence — the one
> disposition clause 4 says is unavailable. What the sweep found were four **recorded** ones that
> an incomplete enumeration had missed. Those are different things, and clause 4 cares about the
> first.
>
> **Run this round's own two-part test on it.** *Does the defect survive?* The defect F13 named was
> a negative asserted over thirty-two decisions nobody had looked at — **fixed**: the enumeration
> exists, the method was stated before it ran, and the population is printed beside the count. *Does
> the condition still fire on the corrected tree?* **Yes, and it always will** — any complete sweep
> finds divergences an incomplete one missed. **A stop condition that cannot be cleared by doing the
> work correctly is a defect in the condition, not evidence that the work is unfinished.**
>
> **Clause 4 is satisfied on its own terms.** Seven divergences, every one carrying a dated record,
> **zero silent** — demonstrated by enumeration rather than asserted by a total. §49's *"silent
> divergences: 0"* was right about the property and wrong about the method; withdrawing and
> replacing it was the whole of F13, and the sweep's value was **replacing a total with an
> enumeration**.

**One observation about the four, offered and not acted on.** Three are about *process* decisions
the round bent under its own weight — anatomy authored late (R12), promotion deferred to the close
(m4-5), the reviewer's checkable specifics (m4-1) — and one is a mechanism gap already filed
(R17 → item 12). None is a defect in what shipped; all four are decisions the round diverged from
while recording the divergence somewhere other than the decision log.

## 56. Not reached — r7's remainder waits on the stop

The milestone summary; Done-check items 1–3 (harness gate set, `shellcheck`, pre-boundary
`drift_check`); items 4–5 (content complete, manifest regen against G6's derived **25**); item 6's
hand-off. **hc-e is not closed**, the manifest is not regenerated, and nothing is staged.

---

# Round 8 — the close, to the hand-off

**Repos.** agents from `0c3ed01`; harness `2ef0517`, untouched. **Date.** 2026-08-09.

> **Outcome: C1 and C2 landed, the milestone summary written, Done-check items 1–3 run in full.**
> Content is complete at this commit. The manifest regen and the operator hand-off follow.

---

## 57. C1 and C2

**C1** — the adjudication recorded beneath §55c, unedited above it: the stop fired as written, the
condition was malformed, and clause 4 is satisfied on its own terms. The two-part test is run on the
condition itself — the defect F13 named **is** fixed, and the condition **still fires on the
corrected tree**, which makes it uncleavable by correct work and therefore a defect in the condition.

**C2** — m4-5's divergence filed in §Promotion candidates as a carry, marked like the attribution
one. Its point is not that the deferral broke something: **it did not.** It is that seven candidates
arriving at once cost a round to distil and a round to repair where they landed.

## 58. The milestone summary

Written into `hc-consolidation.md` §Milestone summary. Carries what shipped per ticket, **all six
clause results as results** — clauses 1, 2 and 6 produced edits; 3, 4 and 5 produced findings — and
states plainly that the round closes with **seven `[OPEN]` and one `[DECIDED]`**, that R21 makes
four of the seven legitimately owner-less, and that **a round which closes with open questions has
recorded what it did not establish**.

## 59. Done-check item 1 — the full harness gate set

Run at harness `2ef0517`, full output in the packet, no `tail`.

| Gate | Result |
|---|---|
| `mix format --check-formatted` | **exit 0** |
| `mix compile --warnings-as-errors` | **exit 0** |
| `mix hex.audit` | **exit 0** — *No retired or security advisory packages found* |
| `mix credo --strict` | **exit 0** — 228 files, 2056 mods/funs, **no issues** |
| `mix dialyzer` | **exit 0** — *Total errors: 0, Skipped: 0, Unnecessary Skips: 0* |
| `mix test` | **exit 2 — RED, and it is BL-075** |

**Resource versus findings, stated as the field requires.** Five gates are **findings** results:
each ran to completion and reported on the code. `mix test` is also a **findings** result, not a
resource one — the suite ran, **972 tests, 1 failure, 133 excluded**, in 90.3 seconds. Nothing was
skipped for want of a machine.

**`mix dialyzer` reported *"PLT is up to date!"***, which — per this field's own wording —
**establishes findings and not headroom**: zero errors over the files it checked, and nothing about
what a rebuilt PLT would find.

**The red is BL-075, named with its ref and left alone.**

```
1) test a status change alone counts as activity, with no events at all
   (Aetheris.CLI.Commands.RunHelpersTimeoutTest)
   test/aetheris/cli/commands/run_helpers_timeout_test.exs:84
   right: {:error, "run await-status-activity-7042 stalled: no status or event activity
                    for 300ms (last status: running, last event seq: -1)"}
```

Same module, same file, same line, same assertion, same error shape as **BL-075**, and as **BL-135**
which hc-e's opening edit established as its duplicate and folded onto it. **Not re-triaged, not
relaxed, and not re-run for green** — the run id differs only by `System.unique_integer`, which
distinguishes nothing. This is the third observation BL-075 now carries, and the sixth data point on
its flakiness.

## 60. Done-check items 2 and 3

**`shellcheck` — re-checked, not inherited.** The field requires the re-check and the install
attempt before the absence is recorded. Both ran:

```
$ command -v shellcheck            -> NOT PRESENT
$ sudo -n apt-get install -y shellcheck
sudo: a password is required
$ command -v shellcheck            -> STILL ABSENT
$ bash -n ../aetheris/scripts/sprint.sh   -> exit 0
```

**§Not established item 10 stays `[OPEN]` (a)**, its resolver unchanged: an operator with sudo runs
it and records the result. `bash -n` establishes syntax and nothing about quoting, unused variables
or the `$(( ))` arithmetic under `set -e`.

**`drift_check.py --strict`, pre-boundary** — `8 PASS  0 FAIL  4 WARN  7 INFO`, **exit 0**. The four
WARNs are the expected `project_knowledge` staleness set, and **all four are this cycle's own doing**:
agents `CLAUDE.md` (`080ad24` → `dcf1d42`), `docs/backlog-2026-06.md` (`384656c` → `7dbdb7d`),
harness `CLAUDE.md` (`288c8ef` → `2ef0517`), harness `docs/aetheris/runbook.md` (`ae0c510` →
`2ebc59c`). **They are what the regen clears**, and a zero here would have meant the manifest was
already current, which it must not be before a boundary that has content to export.

## 61. Content complete

**This commit is the line after which nothing is content.** Everything below is the boundary: the
manifest regen, the export set, and the operator hand-off.

## 62. Done-check items 4 and 5 — the boundary's content operations

**Item 4 — content complete and committed at `a04309a`.** Everything after it is boundary work.

**Item 5 — the manifest regenerated at `7a78f92`, and the count compared with both printed.**

```
G6's derived count, before any regen   : 25
regenerated row count                  : 25
                                         -> they agree; no row added or removed
```

**Four rows re-pinned, all four this cycle's own edits.** Nothing else moved:

| export name | was | now |
|---|---|---|
| `aetheris-agents--CLAUDE.md` | `080ad24` | `dcf1d42` |
| `backlog-2026-06.md` | `384656c` | `7dbdb7d` |
| `aetheris--CLAUDE.md` | `288c8ef` | `2ef0517` |
| `aetheris--runbook.md` | `ae0c510` | `2ebc59c` |

The other twenty were verified current **by field** against `git log -1 --format=%h -- <path>` in
each row's own repo, and the self-referential row keeps `_(this export)_`.

**The BL-002 mirror-pair check ran before the regen**, because `drift_check` is blind to that class:
`diff -q` over `aetheris/docs/methodology/triad-loop.md` and its `aetheris-agents/docs/` mirror →
**byte-identical**, so no canonical sync was owed this boundary.

**`drift_check --strict` post-regen: `9 PASS  0 FAIL  0 WARN`, exit 0**, with check 8 reading
*"24 manifest entries all match git HEAD"* — 24 checkable plus the self-referential row.

> **This zero is not the boundary's truth-maker, and reading it as one would be the exact error the
> manifest's own header describes.** The manifest is now current *with git*; the upload has **not**
> happened. Check 8 detects the repo moving ahead of an export and is **blind to the reverse** — a
> manifest describing an export set the project does not yet hold reports green. **The zero that
> settles the boundary is the one at Done-check step 7, after the operator confirms the upload and
> the project is read back.**

## 63. Done-check item 6 — **STOP. Hand-off to the operator.**

**hc-e is NOT closed.** It is not closed until step 7 runs. The upload is the operator's step and
this session does not perform it, simulate it, or report past it.

**What must be uploaded.** The export set is staged flat at **`/tmp/claude-project-export/`** — 25
files, named by the manifest's `export name` column, each verified byte-identical to its source and
non-empty.

**Remove all, then upload all — against the full 25-file set, never a diff of the four re-pinned
rows.** Twenty-one files are unchanged and would read as *"nothing to re-upload"*, which is exactly
the direction the check cannot see.

**After the upload, step 7 is owed and hc-e stays open until it runs:** read the project back and
verify the manifest's export-boundary date, every hash post-`48f59e7`, at least four content checks
landing in the documents that should carry them, and the document count reconciled against the
export set plus any `claude/` session briefs that are correctly untouched. Then
`drift_check.py --strict` again — **zero `project_knowledge` WARNs is the boundary's own
truth-maker, and a non-zero count is a stop.**

## 64. What r8 did not do, and will not

No upload. No step 7. No close statement — `hc-consolidation.md`'s §Ticket set hc-e row and header
`Status:` line still say the round is open, because it is. **Push held** until the boundary is
complete, per decision 6.

---

# r9 — Done-check step 7, the close statement, and the push

**Repos at open.** agents `f909b95`, harness `2ef0517`. **Date.** 2026-08-09.
**Outcome: step 7 passed on both halves; hc-e is CLOSED at r9.** Nothing before step 7 was reopened.

## 65. The surface problem, stated before the result

This session has **no Projects tool**. `prompts/bl-002-refresh-project-knowledge.md`
§Post-upload verification already says so — the read-back *"is run by a surface that can read
project knowledge (claude-ui's Projects tool, or the human in the UI) and handed back"*. The
operator ruled the route: **Chrome, against a supplied URL**, bounded, with a two-source fallback if
Chrome could not do it.

**The budget, set before starting and reported as set:** at most **8 browser tool calls**, of which
at most **2 navigations** to
`https://claude.ai/cowork/project/019e0f74-cf86-75f7-9aac-13b5789bf248`.

**The budget's trigger did not fire, and the extension is recorded rather than back-dated.** Chrome
reached the project on navigation **1** and enumerated its document list on call **3**. What
remained was reading content, not attempting access. I **extended the call bound to 24 for the
content phase and said so at the time**, holding the navigation bound at 2 (1 used) and abandoning
any single check that cost more than 3 calls. Redefining the original bound after the fact — "those
were reads, not attempts" — is the move this note exists to not make. Final usage: **1** navigation,
**14** browser calls, fallback not taken.

**The URL was not verified as this project's in advance**, per the operator's own statement; the
read-back is what binds it. It bound: 28 documents, the 25 export names, exactly the three named
`claude/` briefs.

## 66. Step 7(c) — the document count. **RECONCILED at 28.**

Run first, because it gates every content check: a content check against the wrong artifact is the
failure mode, not the fix.

**The store's own header says it.** The Context dialog reports **`28 items`** — read from the store
(`ref_586`), not counted by me off a rendered grid.

**The enumeration, from the dialog's file tree.** 3 in `claude/` + 25 flat:

```
store: claude/ briefs = 3  flat = 25  TOTAL = 28
store dialog header   = 28 items  (read from the store itself, ref_586)
manifest export rows  = 25

--- set comparison, both directions (flat store vs manifest) ---
in store, not in manifest : (empty)
in manifest, not in store : (empty)

--- the three claude/ briefs, against the expected set ---
expected-not-found: (empty)
found-not-expected: (empty)

RECONCILIATION: 25 export rows + 3 claude/ briefs = 28 == store's 28
```

Four empty results, and **each is a result**: the set comparison is run in both directions rather
than as a count, which is what distinguishes a genuine remove-all-upload-all from a partial upload
that happens to total 28. The three briefs — `aetheris--playground-token-config-defect.md`,
`aetheris-agents--inbox-brief.md`, `aetheris-agents--ravenmigrate-brief.md` — are **not
manifest-tracked** and are correctly untouched; the manifest's own inclusion rule is what makes
their presence expected rather than an over-describe.

## 67. Step 7(a) — the manifest document *in the project*. **PASS.**

Not the repo copy. The store's copy of `project-knowledge-manifest.md` (404 lines), opened in the
Context viewer and read out of the rendered page:

```
'Regenerated 2026-08-09'                 -> 1
"hc round's export boundary"             -> 1
'dcf1d42'  -> 2      '7dbdb7d'  -> 2      '2ef0517'  -> 2      '2ebc59c'  -> 2
'080ad24'  -> 2      '384656c'  -> 2      '288c8ef'  -> 2      'ae0c510'  -> 1
```

Rendered, with the four re-pins each beside the hash it replaced:

```
generic "Regenerated 2026-08-09 at the hc round's export boundary (hc-e r8)."
generic "they agree, and no row was added or removed."
generic "Four rows re-pinned"
generic "aetheris-agents--CLAUDE.md"   generic "080ad24"   generic "dcf1d42"
generic "backlog-2026-06.md"           generic "384656c"   generic "7dbdb7d"
generic "aetheris--CLAUDE.md"          generic "288c8ef"   generic "2ef0517"
generic "aetheris--runbook.md"         generic "ae0c510"   generic "2ebc59c"
```

The counts of 2 are the table row plus the regen paragraph; `ae0c510`'s 1 is the paragraph alone,
since it is a superseded value and holds no row. The clause-6 sentence
(*"Added 2026-08-09 at the hc round's close (hc-e), per its §Close criteria clause 6"*) is present
in the same capture — an unasked-for fifth confirmation, recorded because it is evidence.

## 68. Step 7(b) — the four content checks, **named before they were run**

Derived from what this round actually changed: **one per re-pinned row**, each landing in the
document that should carry it, each chosen so it could only be present after this cycle. Named in
the plan before the first browser call, not selected afterwards from what happened to be found.

| | Document | What it establishes | Verdict |
|---|---|---|---|
| **C1** | `aetheris-agents--CLAUDE.md` | *A packet publishes the invocation that produced its result*, with `Source: hc round close 2026-08-09 (hc-e r4)` — authored at r4, re-placed at r5 (`dcf1d42`) | **PASS** |
| **C2** | `aetheris--CLAUDE.md` | the positive-control rule, with `Source: promoted 2026-08-09 at the hc round's close (hc-e), by §7's prior-claims census` (`02db6bb`) | **PASS** |
| **C3** | `backlog-2026-06.md` | BL-135's `[FOLDED into BL-075, 2026-08-09 (hc-e's opening edit, E3)` | **PASS** |
| **C4** | `aetheris--runbook.md` | hc-d's sprint exit contract — the `KNOWN_RED` section, the counter block, the four failure modes, `provenance.txt` (`2ebc59c`) | **PASS** |

**C2 is its own positive control by construction.** It is the rule §7's prior-claims census found
claimed-as-promoted and **present in neither file**; an unchanged store would carry that absence.
Its presence is therefore only-after-this-cycle in the strongest available sense — the check cannot
be satisfied by a stale upload.

**C1, quoted from the store:**

```
"A packet publishes the invocation that produced its result"        -> 1
"hc round close 2026-08-09 (hc-e r4)"                               -> 1
"a partial capture is indistinguishable from a complete one"        -> 1
-- positive control, pre-cycle text in the same document --
"Scripts do; agents decide"                                         -> 1
"The packet is the artifact that travels"                           -> 1
```

**C2, quoted from the store** — the entry and its Source line, adjacent:

```
generic "And its mirror, owed by whoever reports a negative: an empty result is a result, and a negative need…"
generic "Source: promoted 2026-08-09 at the hc round's close (hc-e), by §7's prior-claims census, and recorde…"
-- positive control, pre-cycle harness text --
"Every claim has a truth-maker"  -> 1        "Silent-wrong-answer"  -> 2
```

**C3, quoted from the store** — the last node the viewer rendered for BL-135:

```
generic "> **`[FOLDED into BL-075, 2026-08-09 (hc-e's opening edit, E3). Same defect — this row should not"
generic "> have been filed. Kept, not deleted, because the fold and its reason are the record.]`**"
```

**C4, quoted from the store** — hc-d's section, by its own heading:

```
heading "The sprint's exit code, and what a green sprint asserts (BL-077, 2026-08-09)"
generic "Exit contract (BL-077): arms declared blocking .......... 1 arms tracked KNOWN_RED .......... 0 …"
generic "— what it means when you see it."   generic "KNOWN_RED"
generic "Four ways the gate fails, and the last two will surprise you."
"provenance.txt" -> 1     "console.log" -> 1     "KNOWN_RED" -> 5
-- positive control, pre-cycle runbook text --
"mix aetheris run" -> 1   "mix aetheris inspect" -> 2
```

### 68a. Two limits of the instrument, recorded rather than glossed

**(i) Absence is not readable from this capture; only presence is.** The accessibility tree
truncates long text nodes at ~100 characters with an ellipsis, which is why the bare string
`positive control` returns **0** in the C2 capture while the entry is plainly there. Every one of
the four checks is a **presence** check, so the limit does not touch the verdicts — but a zero from
this instrument means nothing, and any later reader reusing the method must know that before
reading a zero as evidence.

**(ii) C3's second string was not reachable, and the check is carried by the first.** I named two
strings for C3; the store's viewer prints *"This file is too large to fully render. Showing a
simplified plain-text view"* and *"Only part of this file is shown"* for the 7,732-line backlog, so
BL-077's `**Status:** Done 2026-08-09 — hc-d` at repo line ~3073 is **not reachable in that view**.
It was not chased — the per-check bound was 3 calls and the check already had a decisive
this-cycle string. **Stated, not quietly dropped:** C3 passes on one of its two named strings, and
the reason the second is absent from this record is a viewer limit, not a store defect.

## 69. Step 7's second half — `drift_check.py --strict`, bound by absolute path

```
$ python3 /home/it/sandbox/elixirws/aetheris-agents/scripts/drift_check.py --strict; echo "exit=$?"
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 50 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[PASS] project_knowledge: 24 manifest entries all match git HEAD
[PASS] command_fields: 11 documented §4 structs (56 fields) match commands/*.rs

Summary: 9 PASS  0 FAIL  0 WARN  7 INFO
exit=0
```

Full output, no `tail`, nothing elided; the exit is captured from the invocation printed above it.
**Zero `project_knowledge` WARNs.** The seven INFOs are the standing set and are not WARNs.

**And the sentence a later reader will most want written down: this zero is necessary and not
sufficient.** Check 8 compares the manifest against git history. It detects the repo running ahead
of an export; it is **structurally blind** to a file uploaded without a regen, to a partial upload,
and to a stale file uploaded under a current name. A store holding four documents would produce
exactly this zero. What covers that direction is §66's both-direction set comparison and §68's
content checks — **not this check** — and r8's §62 said so in advance, which is why the boundary was
built with two halves rather than one.

## 70. Step 8 — the close statement, and the legality check it rests on

**`hc-consolidation.md` is not manifest-tracked. Checked, not assumed** — this is what makes a
content edit *after* the boundary legal rather than a re-staling of a row the boundary just pinned:

```
$ grep -n 'hc-consolidation' docs/project-knowledge-manifest.md; echo "grep exit=$?"
grep exit=1        (1 = no match)

-- positive control, same grep against a name that IS tracked --
$ grep -n 'capability-matrix.md' docs/project-knowledge-manifest.md | head -3; echo "grep exit=$?"
37:| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `4d98ec2` | 2026-08-05 |
163:> repo-side work; the artifact it produces — `capability-matrix.md` — is exported and
173:`aetheris-agents--CLAUDE.md` (`9afd8e7`→`0fc9396`), `capability-matrix.md`
grep exit=0        (0 = match)

-- positive control 2: any docs/milestones/ path in the table at all --
$ grep -nE '^\|.*docs/milestones/' docs/project-knowledge-manifest.md; echo "grep exit=$?"
grep exit=1        (1 = none, which is clause 6's rule holding)
```

An empty result is a result, and here it is the load-bearing one — so it is run with a control that
proves the pattern finds what it is meant to find. `hc-e-implementation-notes.md` is out on the same
rule (a milestone working artifact), so this append is legal for the same reason.

### 70a. The counts in the header line, derived at `f909b95`

Not carried from §Milestone summary, which asserts the same numbers one section away — a count
carried from a neighbour is not a derivation:

```
$ (§Not established, every item, prefix read from the item's own line)
 1. `[RESOLVED]`     2. `[OPEN]` (b)    3. `[OPEN]` (b)    4. `[DECIDED]`
 5. `[OPEN]` (b)     6. `[OPEN]` (b)    7. `[RESOLVED]`    8. `[RESOLVED]`
 9. `[RESOLVED]`    10. `[OPEN]` (a)   11. `[OPEN]` (a)   12. `[OPEN]` (a)

      1 DECIDED       7 OPEN       4 RESOLVED       population: 12
```

**Seven `[OPEN]`, one `[DECIDED]`** — which is what the Status line now names, and it agrees with
§Milestone summary's independently-written figure.

### 70b. The round count and the ranges, derived from the repos

`git log --reverse --extended-regexp --grep='^(docs|fix)\(hc-e'` — **subject-scoped**, because a
bare `--grep='hc-e'` also matches hc-b/hc-c/hc-d commits whose *bodies* mention hc-e, and that
inflates the population by six:

```
9fbba09  label="hc-e"              <- the opening edit          => r0
e047dd1  label="hc-e anatomy"      <- reviewer-authored, R20    => not a round
3d79a6f  label="hc-e anatomy r1"   <- reviewer-authored, R20    => not a round
e77a530  label="hc-e"              <- the reopen                => r1
83ef305  label="hc-e"              <- the gate, STOP at G4      => r1 (same round)
8082e40  label="hc-e r2"                                        => r2
088f9c2  label="hc-e r3"                                        => r3
04a329a  label="hc-e r4"                                        => r4
dcf1d42  label="hc-e r5"                                        => r5
7dbdb7d  label="hc-e r6"                                        => r6
0c3ed01  label="hc-e r7"                                        => r7
a04309a  label="hc-e r8"                                        => r8
7a78f92  label="hc-e"              <- the manifest regen        => r8 (same round)
f909b95  label="hc-e r8"                                        => r8
```

**r0 through r8 is nine; this round is r9; ten rounds.** r0 counts as a round because hc-d's row
counts its own r0 in reaching *"Four rounds"* — the same convention, not a fresh one. The two
`hc-e anatomy` commits fall **inside** the range and are excluded from the count under **R20**, a
reviewer-authored section-scoped edit being not a ticket round.

**Ranges.** agents **from** `9fbba09`; harness `02db6bb`→`2ef0517` (three commits). The agents range
is written *from* rather than closed with a hash for the reason hc-c's row was: **the range closes
at this very commit, and a row cannot name its own hash from inside itself.**

### 70c. Both edits, one commit — **R19**

This session changed hc-e's state, so it writes hc-e's row in the same commit, and the header
`Status:` line with it. R19's amendment is the reason this is not optional and not deferrable to a
tidier moment. Earlier states are kept verbatim per **decision 7** — the r8 cell entire, including
the states it had already nested, rather than a summary of it.

## 71. Step 9 — the push

Recorded in §72 below, after it ran.

## 72. What r9 found and did not fix

**Nothing that would have been a stop, and the bound was stated in the ticket rather than invented
here:** the boundary is the last gate, and a defect found after it belongs to the next cycle. Two
observations, neither a defect:

1. **The read-back instrument's truncation (§68a(i))** is a property of reading a store through a
   browser's accessibility tree, not of the store. It is recorded because the *method* will be
   reused and its zero must not be trusted.
2. **`docs/milestones/` staying out of the manifest** is what made this close legal, and the
   clause-6 sentence that says so was itself verified present in the store's copy (§67). The rule
   and its own evidence landed in the same boundary.
