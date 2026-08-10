# m5 — the BL-131 ruling edit (m5-D2) — implementation notes

`Authored 2026-08-10 by claude-code, on the reviewer's section-scoped edit instruction, on
top of 40c2d58 (t1 r1). Under R20 this edit is not a ticket round and gets no review file;
this file is its committed record.`

## Measurement stamp

Every figure, count, offset and quotation in this file was derived at agents **`40c2d58`**
(this edit's parent) or in the working tree this edit produces, and each says which. Line
numbers appear only for claims about lines, per **m5-D1**; everywhere else a section is
named and its text quoted. Positional claims carry the commit they were measured at.

**The harness is not edited by this round** and was not read for any figure below except
`../aetheris/docs/methodology/milestone-methodology.md`, cited in W3.

## Filename

Derived, not estimated. `ls cloudcost/docs/` before this file was written returns **27**
entries, of which **25** end `-implementation-notes.md`. The two that do not are
`m3-linode-scout.md` and `m5-scoping-landing-notes.md`, enumerated rather than counted
away. **So the dominant pattern is `*-implementation-notes.md`, 25 of 27, and this file
matches it** — with the file present the figures are 26 of 28.

The direct precedent for a reviewer-authored section-scoped edit's record is
`cloudcost/docs/m5-pin-edit-implementation-notes.md` — same round, same R20 basis, same
suffix.

---

## Gate on the instruction

The round instruction states its own claims are unverified and asks that each be resolved
before it is acted on. Every claim was resolved at `40c2d58`. **All hold except one**,
recorded below with what was done instead.

| Claim in the instruction | Resolved as |
|---|---|
| `70addd3`, `5db4585`, `40c2d58` held at HEAD | ✓ `git log --oneline -6` — present, in that order, with `a9639de` beneath |
| Working tree clean | ✓ `git status --short` → empty |
| agents ahead of origin such that this commit makes three | ✓ `git rev-list --count origin/main..HEAD` → **2** before this edit |
| Harness unedited and clean | ✓ `../aetheris` at `2ef0517`, `git status --short` → empty |
| C4 and C11 carry m4 t5b pointer blocks naming BL-131 | ✓ both present in `cloudcost/milestone.md` §Contracts, each opening *"Pointer added m4 t5b, 2026-08-07"* |
| The runbook asserts the merge is now-unreachable pending BL-070 | ✓ *"**BL-070**, which retires the now-unreachable cross-provider merge code in `compose_report_data.py`"* |
| Five backlog rows exist — BL-070, BL-119, BL-121, BL-131, BL-132 | ✓ all five present in `docs/backlog-2026-06.md` |
| BL-131 sequences itself *"before provider four — the first fan-out is exactly when the wrong answer starts costing"* | ✓ verbatim, in the row's closing paragraph |
| BL-131's `Source:` names m4 t5b's G2 gate-stop, 2026-08-07 | ✓ *"Source: m4 t5b G2 gate-stop and G7, 2026-08-07. Reachability derived at agents 6832159"* |
| E4/E5/E7 support m5-D2's characterisations of them | ✓ see *Claims in m5-D2 checked against t1's record*, below |
| R2 binds *"Every `hc-*` ticket"*; methodology §1 principle 4 and §8 are unscoped | ✓ — W3's correction is right |
| R12, R13, R19, R20, R21 exist as cited in `docs/milestones/hc-consolidation.md` | ✓ all five, as `### R<n>` headings |
| Decisions 7 and 8 are as relied on | ✓ `cloudcost/m4-consolidation.md` §Ratified decisions, rows 7 and 8 — quoted under W1b |

### The one claim that does not hold

**W4 says to write the resolution block *"in the shape that section's resolved items use —
read one and report the shape before writing."*** **§Not established in
`cloudcost/m5-n1-compose.md` has no resolved item.** At `40c2d58` its four items are
`` `[OPEN]` (b) ``, `` `[OPEN]` (b) ``, `` `[OPEN]` (a) `` and `` `[DECIDED]` (c) ``.
There was no resolved item to read.

**What was done instead, and not silently.** The shape is taken from
`docs/milestones/hc-consolidation.md` §Not established — the section this one inherits
from, and the section **R21** itself was authored in. Two things were read there:

- **An item resolved in place.** Its item 7 heads `` 7. **`[RESOLVED]`** **hc-b2's §6
  anatomy was never written into this document…** `` — prefix on the head, original prose
  beneath unrewritten, dated block appended as a nested blockquote.
- **A prefix re-labelled in place.** Its item 4 went `[OPEN]` → `[DECIDED]` and records the
  change in its own appended block: *"Corrected in place, original prefix named here, per
  decision 7."*

That is the shape adopted. **It is a precedent, not an invention**, and the substitution is
reported here rather than left to read as compliance with the instruction as written.

### Two consequences of that, decided rather than assumed

1. **Item 2 keeps its kind letter: `` **`[RESOLVED]` (b)** ``.** This section's preamble
   requires that *"Each entry states its kind"*, and R21's kinds are (a), (b), (c).
   `[RESOLVED]` is a **state**, not a fourth kind — in the precedent an (a) or (b) item
   keeps its kind and gains the state, and only (c) has a prefix of its own. Item 2 is
   still a carried unknown whose settling route named no owner; resolving it did not
   change that.
2. **The prefix changes in place; the prose does not.** Decision 7 — *"A closed record gets
   a dated superseded note; its original text is not rewritten"* — governs the body. The
   instruction's own wording (*"Its original text stands, per decision 7"*, and *"the
   vocabulary sweep **this prefix change** owes"*) requires both halves, and both were done.

---

## W1 — §Ratified decisions

### W1a — m5-D2 appended

**Unit at HEAD, quoted before the edit.** The section ended with m5-D1's second bracketed
note, followed by the section rule:

> ``[Extended 2026-08-09 at r6 with the stamping clause, on claude-code's r5 flag that the
> exemption covers a whole document's anchors and said nothing about their tense.]``
>
> `---`

**How the section separates entries.** §Ratified decisions held exactly one entry at
`40c2d58`, so the separator had to be read off the boundary that existed: a blank line
between the opening paragraph and `### m5-D1`, with entries as `### ` headings and the
trailing `---` closing the section rather than separating entries within it.

**After.** `### m5-D2 — BL-131: the N>1 compose surface is retained and bounded…` inserted
between m5-D1's `[Extended …]` note and the closing `---`, separated by a blank line on
both sides, so the entry sits inside the section and the rule still closes it. The text is
the instruction's, landed verbatim; nothing was paraphrased, reordered or abridged.

### W1b — the opening paragraph replaced

**Unit at HEAD, quoted in full before replacement** (the whole opening paragraph, replaced
as a unit — not scoped by naming sentences):

> **The BL-131 ruling is not here yet.** It lands in this section, authored by the
> reviewer at the gate stop between t1 and t2 per R12, with its own date. The
> decision below is methodological and was made in the course of opening the
> round. The BL-131 slot standing open and saying so is the correct state before
> t1 runs, and is stated rather than omitted.

**After** — a paragraph plus a dated correction block:

> **Both decisions in this section are ratified, and the BL-131 ruling is one of
> them.** **m5-D1** is methodological and was made in the course of opening the
> round. **m5-D2** is the BL-131 ruling, authored by the reviewer at the gate stop
> between t1 and t2 per R12, with its own date, on t1's committed establishment.

followed by a `[corrected in place 2026-08-10 …]` block that quotes what the paragraph
said and states why it was corrected rather than left standing.

**What was built, and why.** Three things were carried over from the quoted text because
they remained true and are the reader's orientation: that m5-D1 is methodological and was
made while opening the round; that the ruling is the reviewer's, authored at the gate stop
per **R12**; and the dating discipline. Two things were dropped because m5-D2 landing made
them false: *"is not here yet"*, and *"the correct state before t1 runs"* — t1 has run.
One thing was added: that m5-D2 rests on t1's committed establishment, which is what makes
the ruling citable rather than asserted.

**Why corrected in place rather than superseded.** `cloudcost/m4-consolidation.md`
§Ratified decisions, rows 7 and 8, verbatim:

| 7 | **A closed record gets a dated superseded note; its original text is not rewritten.** |
| 8 | **Live operational guidance is corrected in place.** A superseded note on a how-to leaves wrong instructions standing as the primary text. |

This paragraph is not a closed record — it is a statement about what the section a reader
is currently in contains. Left standing, it sends a reader looking elsewhere for a ruling
that is directly beneath it, which is decision 8's named failure in navigational form. The
replaced wording is quoted verbatim inside the correction block, so nothing is lost.

---

## W2 — t2's anatomy completed

**Four §6 fields plus the gate — five units, not five slots.** The instruction heads this
*"complete the four R13-marked slots"* and supplies five blocks. Both are right: this
document's own anatomy paragraph holds that *"Ticket anatomy in this document is §6's seven
fields plus a step-1 gate. **The gate is not a §6 field.**"* So the four **slots** are
`Touches`, `Runbook update rule`, `Done-check` and `Claude-code prompt`; the gate is the
fifth unit and is separate by the document's own definition. Recorded because a reader
counting five replacements against a heading that says four would otherwise read a
discrepancy.

Each unit was replaced whole, marker and all. **No `R13-marked` or `Resolver:` text
survives anywhere in t2's subsection** — verified below.

### Step-1 gate

**Before:** *"**Step-1 gate** *(m4 decision 3, carried by R8).* **R13-marked.** The gate's
content depends on the ruling's direction. `Resolver: authored by the reviewer into this
section by a dated section-scoped edit after the ruling and before t2 opens, per R12.`"*

**After:** the instruction's gate verbatim — a temporal stop condition stated as such,
arms (a) the orchestrator still passing one bundle on both STEP 3 forms and (b) C4's and
C11's pointer blocks present and unamended since m5-D2, each to be named, quoted, and its
zeros controlled.

### Touches

**Before:** *"**Touches.** **R13-marked.** The path set is one of two disjoint sets and the
ruling selects which. `Resolver: t1's E4 and E5 enumerate the two blast radii with
path:line; the reviewer selects one and authors this field into this section by a dated
section-scoped edit before t2 opens, per R12.` **Not guessed from here** — a guessed
`Touches` is a specification, which R13 names as the worse failure."*

**After:** the instruction's six-path list verbatim — `cloudcost/milestone.md` (C4 and C11
only), `cloudcost/scripts/compose_report_data.py` (module docstring only),
`cloudcost/runbook.md`, `docs/backlog-2026-06.md` (five named rows),
`cloudcost/m5-n1-compose.md` (t2's row only, per R19), and a new
`cloudcost/docs/m5-t2-implementation-notes.md`, closing with the deviation clause.

### Runbook update rule

**Before:** *"**Runbook update rule.** **Partly R13-marked, and a runbook change is in
scope either way** — that much is authorable now, because both directions are
operator-visible: *removed* deletes a declared tool interface an operator can read today,
and *supported* adds an invocation an operator must be told about. Which runbook text
changes is the ruling's. `Resolver: same as Touches.`"*

**After:** the instruction's rule verbatim — no observable semantics change, the runbook is
in `Touches` because it carries a *claim* the ruling overturns rather than a procedure the
ruling alters, stated rather than left to inference, with a second-instance clause.

### Done-check

**Before:** *"**Done-check.** **R13-marked, deliberately.** Anchor: the offline pytest
spine over the cloudcost suite, at the exact invocation t1 records under its own done-check
item 1. `Resolver: the ruling, plus t1's recorded invocation; authored by the reviewer
before t2 opens, per R12.` Marked rather than completed on purpose — R13's own recorded
observation is that every defect found in a reviewed anatomy sat in the slot its author
completed confidently, and a done-check written against an assumed post-ruling shape is
exactly that slot."*

**After:** the instruction's four-item bash block verbatim.

**The anchor it names resolves.** t1's own done-check item 1 records
`python3 -m pytest cloudcost/tests/ -v` → **386 passed in 145.23s, exit 0**; 0 FAILED, 0
ERROR, 0 SKIPPED (`cloudcost/docs/m5-t1-implementation-notes.md` §Done-check). That is the
recorded figure item 1's comment tells t2 to compare against, and it exists — the
done-check does not point at a number that has to be invented.

### Claude-code prompt

**Before:** *"**Claude-code prompt.** **R13-marked.** `Resolver: authored by the reviewer
after the ruling and before t2 opens, per R12.`"*

**After:** the instruction's prompt verbatim — gate first, then m5-D2's four numbered
declaration requirements, m5-D1 governing citations, R19 on t2's row, no push.

### Verification of the completion

```
$ sed -n '210,333p' cloudcost/m5-n1-compose.md | grep -n 'R13-marked\|Resolver:'
(no output; exit 1)
```

Lines 210–333 are t2's subsection in the working tree, bounded by `### t2 — apply the
ruling` and the `---` that opens §Ratified decisions. **Zero hits.**

The grep is scoped rather than whole-file **because the whole file is not zero**, and
saying so is the point: `grep -n 'R13-marked\|Resolver:'` over the file returns **two**
lines — t2's row in §Ticket set, which contains the strings inside a negation (*"no slot is
R13-marked and no `Resolver:` remains"*), and §Not established item 3's own
`**Resolver:** t1's **E7**`, which is a different section and not this edit's subject. A
whole-file zero was never available and was not claimed.

**All seven §6 fields present**, enumerated from the subsection by `grep -n '^\*\*'`:
`Step-1 gate` (not a field), `Scope`, `Contract refs`, `Touches`, `Do not generate`,
`Runbook update rule`, `Done-check`, `Claude-code prompt` — seven fields plus the gate.

---

## W3 — the anatomy paragraph

**Unit at HEAD, quoted before the edit** (the paragraph beginning *"Ticket anatomy in this
document is §6's seven fields plus a step-1 gate"*):

> **Ticket anatomy in this document is §6's seven fields plus a step-1 gate. The
> gate is not a §6 field.** §6 defines seven fields and no gate. The gate is m4
> decision 3, carried by hc-consolidation **R8**. Stated here so that no ticket in
> this round cites it as a methodology obligation — `docs/reviews/hc-b-review.md`
> Round 0 recorded that citation as a manufactured authority.

**After:** the same paragraph unchanged, with the instruction's two blocks appended to that
unit — **A step-1 gate states the tense of its stop condition**, and **Review files**.

**The second block's substance was verified, not carried.**
`docs/milestones/hc-consolidation.md` **R2** heads *"BL-133 face 1 is not scope. It is a
methodology obligation this round simply meets"* and binds *"**Every `hc-*` ticket** commits
its review file."* That is scoped to `hc-*` and does not literally reach an `m5-*` ticket.
The obligation R2 grounds itself in does:
`../aetheris/docs/methodology/milestone-methodology.md` **§1 Principles**, principle 4 —
*"Feedback travels as files, not relay"* — and **§8 Sync rules (canonical-doc
discipline)**, both unscoped by ticket prefix. R2's own text says so: *"Part 7(a) refutes
that from the methodology's own text: §1.4 and §8 already require review files committed,
verbatim."*

---

## W4 — §Not established item 2 resolved

**Unit at HEAD, quoted before the edit:**

> 2. **`[OPEN]` (b)** **BL-131's `Source:` line cites gate items that exist as no
>    committed text.** The row attributes its derivation to two gate items of a
>    ticket that produced no implementation-notes file; the only in-repo records of
>    that ticket are its cycle-document passages and two backlog annotations.
>    **Settled by:** nothing in-repo — the derivation is re-run at HEAD instead,
>    which is t1's step-1 gate and E1/E2. Recorded so that a later reader does not
>    cite those gate items as though they were a document. **No owner.**

**After:** the same text, prose unrewritten, with the head prefix changed
`` `[OPEN]` (b) `` → `` `[RESOLVED]` (b) `` and the instruction's dated resolution block
appended as a nested blockquote, plus a bracketed note recording the prefix change, the
retention of the kind letter, decision 7's governance of the prose, and the borrowed shape.

**The item's own settling route did run.** Its `Settled by:` names t1's step-1 gate and
E1/E2; `cloudcost/docs/m5-t1-implementation-notes.md` §Gate disposition and §Bearing on
§Not established item 2 record the re-run, and §Bearing states the result the resolution
block now ratifies: *"the re-run the item names as its settling route has now happened, and
it did **not** reproduce the cited derivation — it contradicted part of it."* t1 correctly
declined to resolve it (*"settling it is a disposition, and disposing rows is not t1's"*);
this edit is where the disposition belongs.

---

## The vocabulary sweep

Owed by §Carried in's second carried rule: *"**A vocabulary change owes a sweep of
everything that speaks it.** When a label, status set, field name or prefix changes, derive
the population that speaks it and check each member in the same commit."* Item 2's prefix
change introduced `[RESOLVED]` to a document that had never used it, so the sweep is owed
and is run here. **Reported whether or not it found anything — it found one.**

**Population, derived not assumed.** `grep -n 'RESOLVED\|\[OPEN\]\|\[DECIDED\]'` over
`cloudcost/m5-n1-compose.md` at **`40c2d58`** (read from `git show HEAD:…`, not the working
tree, so the population is the pre-edit one):

```
317:it and invents no owner; **(c)** a decision not to fix, marked `[DECIDED]`.
321:1. **`[OPEN]` (b)** **Provider four carries two non-identical gate statements at
330:2. **`[OPEN]` (b)** **BL-131's `Source:` line cites gate items that exist as no
338:3. **`[OPEN]` (a)** **Whether decision H's re-derivability clause is satisfied
346:4. **`[DECIDED]` (c)** **Four self-scoped statements in the two m5 record files
count: 5
```

**Five members, all in §Not established** — the preamble (`:317`, the line of that unit
that speaks the vocabulary) and the four items. No other section of the document speaks
these tokens, so the sweep does not reach §Ticket set, §Ratified decisions, §Promotion
candidates or §Carried in. `[Line numbers are a claim about lines and are stamped at
40c2d58, per m5-D1.]`

| Member | Check | Result |
|---|---|---|
| **The preamble** (`:317`'s unit) | Does it still describe the section after one item resolves? | **No — fixed.** See below |
| **Item 1** `` `[OPEN]` (b) `` | Provider-four gate statements — untouched by this edit, no resolver delivered | Correct as it stands |
| **Item 2** `` `[RESOLVED]` (b) `` | The member this sweep is owed for | Changed by W4; consistent |
| **Item 3** `` `[OPEN]` (a) `` | **Its resolver has delivered.** See the finding below | **Reported, not changed** |
| **Item 4** `` `[DECIDED]` (c) `` | A decision not to fix, unaffected by a resolution elsewhere | Correct as it stands |

### The preamble — the sweep's one fix

**Before:** *"Carried rather than resolved. Per **R21**, this section holds three kinds of
entry — **(a)** … **(b)** … **(c)** a decision not to fix, marked `[DECIDED]`. Each entry
states its kind. The per-item prefix is authoritative; this section carries no total."*

Two clauses stopped describing the section the moment item 2 resolved: *"Carried rather
than resolved"*, over a section one of whose items is now resolved; and the kind list,
which names exactly one prefix and so gives a reader no way to read `[RESOLVED]` when they
meet it three items down.

**Fixed** by an appended `[corrected in place 2026-08-10 …]` block, in the form
`docs/milestones/hc-consolidation.md` uses for the same situation (*"Items are added here
open and resolved in place… Read each item's `[RESOLVED]` / `[OPEN]` / `[DECIDED]` prefix
for its current state — the preamble describes how items arrive, not what they all still
are"*). The original sentences stand; the block states that items arrive open and resolve
in place, that a resolved item keeps its kind letter and gains the state prefix, that the
three state prefixes in use are `[RESOLVED]` / `[OPEN]` / `[DECIDED]` of which only
`[DECIDED]` marks a kind, and that the opening sentence describes arrival rather than
current state. Corrected in place under **decision 8**: it is live guidance telling a
reader how to read the section.

**Post-edit population**, working tree: **9** lines — the five above, relocated, plus four
introduced by this edit, split **2 and 2**: two in the preamble's correction block (the
line naming the three state prefixes, and the line distinguishing state from kind) and two
in item 2 (its resolution block head, and its bracketed prefix-change note). The growth is
entirely explanatory text *about* the vocabulary; **no item's prefix changed except item
2's**, which is the change the sweep is owed for.

### Finding — item 3's resolver has delivered, and the item still reads `[OPEN]`

**Not repaired here, deliberately.** §Not established item 3 is `` `[OPEN]` (a) ``
**Whether decision H's re-derivability clause is satisfied today**, and its
`**Resolver:**` is *"t1's **E7**, in this document."* **E7 has run and answered it.**
`cloudcost/docs/m5-t1-implementation-notes.md` §E7 concludes: *"H's precondition —
normalized per-provider snapshots persisted in the layout it names — **is satisfied today,
by the live pipeline, for all three providers**. H's consequent — the thin read-only
aggregator — **is not built**."* m5-D2's own *What this does not decide* paragraph relies
on exactly that: *"**E7** establishes it does not exist, and H's own precondition is
satisfied today."*

So the document now ratifies E7's answer in §Ratified decisions while §Not established
still carries the question as open with a resolver that has reported.

**Why it is reported rather than resolved.** W4 scopes this edit to item 2 by name.
Resolving item 3 is a disposition, and dispositions in this section are the reviewer's to
author (**decision 11**, **R12**) — the same reasoning under which t1 declined to resolve
item 2 from inside a ticket. Landing an unrequested resolution would be the guessed-slot
failure **R13** exists to prevent, in a different section. It is named here and in the
packet so the reviewer can take it in a line.

---

## W5 — §Promotion candidates

**Section at HEAD, quoted before the edit:** a preamble (*"Candidates recorded here are
promoted or dropped at this round's close under the methodology's §7 ritual; recording one
is not promoting it…"*) and one entry, **A check that structurally cannot observe the
failure it stands in for returns green for the wrong reason**, closing *"Origin:
claude-code at m5 r4, against a check the reviewer specified."*

**The shape the first entry establishes**, read off it before writing: a **bold rule
sentence** as the entry's first words, in the imperative-general voice; then the worked
case in past tense with the specific artifact named; then the generalisation, usually
*"The rule is not X: it is that…"*; then `Origin: <who> at <round>, <against what>`. No
heading, no bullet — entries are separated by a blank line.

**After:** the instruction's second entry appended verbatim, following that shape (bold
rule sentence → t1 r0's packet as the worked case → *"The close is not *do not elide*: it
is that…"* → `Origin: claude-code at m5 t1 r1…`), plus its dated bracketed filing note.
The one departure from the first entry's shape is that filing note, which the first entry
lacks — it is the instruction's, and it records who filed and on what flag, which the first
entry carries inside its `Origin:` clause instead.

---

## Findings for the reviewer — two anatomy fields not in this edit's scope

Both are in t2 §6 fields that were **not** R13-marked and that the instruction did not
authorise replacing. Reported, not edited, for the same reason item 3 is: anatomy is the
reviewer's to author, and the instruction named its five units exactly.

### A — `Scope` says the ruling is implemented in the script's *declared interface*

t2's `Scope` reads: *"the BL-131 ruling is implemented in `compose_report_data.py` **and
its declared interface**…"*. It was authored 2026-08-09, before the ruling. The declared
interface is `cloudcost/tools.json` — BL-131's own row calls `--input-dir` *"declared in
`cloudcost/tools.json` (`args[3]`) with a worked example"*. Under m5-D2 the code change is
**the module docstring only**, and the `Touches` landed at W2 does not include
`cloudcost/tools.json`. So `Scope` reads wider than `Touches` allows.

**Bounded, not urgent.** `Scope`'s own last sentence defers — *"What 'implemented' means is
the ruling's content and is not assumed here"* — `Touches` is authoritative on paths, and
the new `Claude-code prompt` says *"Your work is its four numbered declaration requirements
and nothing beyond them."* A t2 session following the prompt will not edit `tools.json`.
The tension is a reader's, not an executor's.

### B — `Contract refs` says §Ratified decisions *"will hold"* the ruling

t2's `Contract refs` reads *"this document's §Ratified decisions, **which will hold the
ruling**"*. Future tense, stale as of this commit — the section holds it. The same field
omits `cloudcost/m2-milestone.md` decision H, which m5-D2 reasons from throughout, and
omits BL-132, whose row the new `Touches` names.

**Also bounded:** the new `Claude-code prompt` points a t2 session at §Ratified decisions
directly (*"Apply **m5-D2**, which is ratified in this document's §Ratified decisions"*),
so the stale tense misleads a reader rather than misrouting an executor.

---

## Claims in m5-D2 checked against t1's record

The ruling is the reviewer's and was landed verbatim. Its factual claims about t1's
evidence were nonetheless checked, because landing them makes this commit assert them.
**All hold.**

| m5-D2 says | t1's record |
|---|---|
| Three routes to N>1, not the one BL-131 names | §E1 and §Step-1 gate (a): three routes established |
| The route-bearing code byte-unchanged since the commit the row cites | §Step-1 gate: *"that code is byte-unchanged across the range `6832159..70addd3`"*, and BL-131's `Source:` cites `6832159` |
| *advertised* false — three primary flags declare the repeatable form, the docstring advertises it | §E2, and the module docstring reads *"Written to merge N providers… given either as a repeatable triple or discovered from a directory"* |
| *tested* false — N>1 exercised across all three routes | §E3 |
| Only *invoked* survives | §E2: no invocation outside the test suite produces N>1 |
| Multi-bundle machinery through **six** section builders | §E4(3) enumerates `service_totals`, `month_on_month`, `coverage_section`, `orphan_section`, `region_coverage_section`, `persist_history` — six, beside `compose` itself |
| E5's costs: sprint leg, runbook recipe, manifest form, orchestrator-level test | §E5 (a)–(d), each with a positive control |
| The manifest has no argument kind that can supply more than one | §E5(c) |
| E7 establishes the aggregator does not exist; H's precondition satisfied today | §E7, verbatim as quoted under the item-3 finding above |
| The orchestrator passes a single bundle on both STEP 3 forms | §E2, and §Step-1 gate (b) |

**One claim in m5-D2 is not checkable from the repo and was not checked:** that this
surface *"has been left in place three times without being declared"*. BL-070, BL-131 and
BL-132 each exist and each rests on a different reading of the surface, which is what the
sentence is about; whether that constitutes three *retentions* is the reviewer's
characterisation, not a countable fact. Named rather than silently ratified.

---

## Deviations

**None from the instruction's five units.** Each was replaced whole, and each replacement
text is the instruction's verbatim except W1b's opening paragraph, which the instruction
directed be *built* from the quoted text and reported — done above.

**One substitution, reported:** W4's *"read one and report the shape"* could not be
satisfied as written (no resolved item existed), and the shape was taken from the
precedent section instead. Recorded under *The one claim that does not hold*.

**No file outside this edit's scope was changed.** `docs/backlog-2026-06.md`,
`cloudcost/milestone.md`, `cloudcost/runbook.md`, `cloudcost/tools.json` and everything
under `cloudcost/scripts|tests|templates|agents` are untouched — they are t2's work. The
harness is unedited.

**No push.** t2 is not opened.

---

## Review

`Dated 2026-08-10. Per R20 this edit gets no review file; the reviewer's findings on t1 r1
land here, verbatim, with dispositions beneath.`

### F3 — the review-file authority was mis-cited

*Finding, raised by claude-code at t1 r1: the round instruction cited R2, whose own text
binds `hc-*` tickets and does not literally reach m5. The obligation holds on methodology
§1 principle 4 and §8, both unscoped.*

**Disposition: accepted; corrected at W3** in §Ticket set, so the round states its own
authority correctly rather than carrying the mis-citation forward into t2. Both halves were
re-verified before landing: R2's binding clause reads *"Every `hc-*` ticket commits its
review file"*, and methodology §1 principle 4 (*"Feedback travels as files, not relay"*)
and §8 carry no ticket-prefix scope.

### F4 — the elision rule had no owner

*Finding, raised by claude-code at t1 r1: the rule bound every remaining packet in the
round and lived only in a notes file, which the next session reads as evidence rather than
as instruction.*

**Disposition: accepted; filed at W5** in §Promotion candidates. The flag named the repo's
own standing rule against itself — *a deferred finding gets a backlog row in the same round
it's deferred; prose in a packet or notes files nothing* — which is the right way to raise
it.

### F1a — two published figures in E4(6) disagree by one file

*Finding, raised by claude-code at t1 r1 and recorded there rather than repaired.*

**Disposition: left standing, deliberately.** The ruling does not turn on E4's count — it
turns on the *kinds* of thing removal would reach, which the enumeration establishes
regardless of whether the population was 466 or 467. The discrepancy is recorded with both
readings and a settling route that does not exist in-repo, which is the correct terminal
state for a disputed figure. Re-running E4 to settle a number the ruling does not use would
cost more than the number is worth.

**Confirmed at this edit:** m5-D2's *Why not removed* paragraph cites E4 for the
enumeration of kinds and cites no count, so the ruling does not inherit the disputed
figure.
