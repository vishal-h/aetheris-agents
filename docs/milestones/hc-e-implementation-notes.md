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
