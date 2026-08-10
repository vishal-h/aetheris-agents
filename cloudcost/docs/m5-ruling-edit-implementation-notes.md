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

## r1 — the aggregator row filed, item 3 resolved, and three findings closed

`Authored 2026-08-10 at r1, the second commit of the ruling edit, on top of a2d63d1 (r0),
itself on 40c2d58 (t1 r1), 5db4585 (t1 r0) and 70addd3. Under R15 this is a further round
of the ruling edit and appends here rather than opening a fourth record file; under R20 it
is likewise not a ticket round and gets no review file. Every figure and quotation below
was derived at agents a2d63d1 or in the working tree this round produces, and each says
which. Line numbers appear only for claims about lines, per m5-D1.`

**The R15 classification, and where it differs.** R15 is written about a ticket; this
repairs r0's own output, one level down, exactly as `m5-pin-edit-implementation-notes.md`
r5 did. It differs from R15's supporting mechanism in the same way r5 did: r0 held its
findings in a packet, and a packet travels as a claim about its content, so the three
findings this round closes are committed by r1 rather than pre-dating it. Recorded rather
than smoothed.

### Gate on the instruction

The round instruction states its own claims are unverified. **All hold.**

| Claim | Resolved |
|---|---|
| The m5-D2 ruling edit is at HEAD | ✓ `a2d63d1` — *docs(m5): ratify m5-D2 — BL-131 retained and bounded; t2's anatomy completed* |
| Commits beneath it unamended | ✓ `git log --oneline -6` → `40c2d58`, `5db4585`, `70addd3`, `b648867`, `a9639de`, in that order — the sequence r0's own gate table names |
| agents three ahead of origin, tree clean | ✓ `git rev-list --count origin/main..HEAD` → **3**; `git status --porcelain` → empty |
| harness clean at unchanged HEAD | ✓ `../aetheris` at `2ef0517`, `git status --porcelain` → empty |
| r0's packet flagged *"three times"* as a characterisation | ✓ §*Claims in m5-D2 checked against t1's record*, closing paragraph: *"whether that constitutes three retentions is the reviewer's characterisation, not a countable fact"* |
| §Not established item 3 reads `[OPEN]` with a delivered resolver | ✓ at a2d63d1 the item heads `` **`[OPEN]` (a)** `` and its `**Resolver:**` is *"t1's **E7**, in this document"* |
| t2's `Scope` and `Contract refs` are as the findings describe | ✓ both quoted verbatim under Y5 below |

### What r1 changed, and where

| Y | file | change |
|---|---|---|
| Y2 | `docs/backlog-2026-06.md` | **BL-136** filed, appended at EOF |
| Y3a | `cloudcost/m5-n1-compose.md` §Ratified decisions, m5-D2 *What this does not decide* | one dated sentence appended, giving the aggregator question its owner |
| Y3b | same, m5-D2 *What bounded requires* | two substitutions — the count removed, the enumeration left carrying the claim |
| Y4 | same, §Not established item 3 | `[OPEN]` → `[RESOLVED]`, kind letter (a) kept, resolution block appended |
| Y4 | same, §Not established preamble correction block | the sweep's one fix — a count-of-one clause replaced with the count-free pointer |
| Y5 | same, t2's `Scope` and `Contract refs` | each field replaced whole |
| Y6a/b | same, t2's `Touches` and `Claude-code prompt` | the backlog bullet gains BL-136; the prompt gains one cross-reference instruction |
| Y6c | same, §Ticket set t2 row | R19 update recording all four field amendments |
| Y7 | this file | this section, and four dispositions appended to §Review |

`cloudcost/milestone.md`, `cloudcost/runbook.md`, `cloudcost/tools.json` and everything
under `cloudcost/scripts|tests|templates|agents` are untouched — they are t2's work. **t2
is not opened. The harness is unedited** (HEAD `2ef0517`, clean, nothing to push).

---

### Y2 — BL-136 filed

**a. The number, derived over a named population.** Population: every `BL-<n>` token in
`docs/backlog-2026-06.md`, at a2d63d1 — **136 distinct numbers**, and the range `1..135`
is **dense**: the set difference against `seq 1 135` is empty, so the numbering is not
sparse and the highest is the next free one minus one. The highest few, enumerated rather
than asserted: `…131, 132, 133, 134, 135`.

Two exclusions, both checked rather than assumed. **`BL-999`** appears in the repo but is
not a row — `../aetheris/docs/aetheris/runbook.md` §*(the dangling-ref check)* defines it
as *"**dangling** — `BL-999`, a row that does not exist in `docs/backlog-2026-06.md`"*, a
deliberate sentinel. And the **harness repo's** highest `BL-` token is `BL-133`, below the
agents maximum, so it constrains nothing. **Next free: `BL-136`.**

**b. The placement convention, derived from the file's own history and reported before
writing.** Three commits filed cloudcost rows into this file, and all three appended at
**EOF**: `e1a1830` (17 rows) at `@@ -6400,3 +6427,528 @@`, `080ad24` (2 rows) at
`@@ -7226,3 +7287,122 @@`, and the earlier filing of BL-131/BL-132 in the same tail. The
tail at a2d63d1 reads `…BL-130, BL-131, BL-132, BL-133, BL-134` — ascending, so appending
satisfies both readings of the convention at once.

**The one counter-example, named rather than averaged away.** `f8ed90f` inserted **BL-135**
at the *top* (`@@ -12,6 +12,54 @@`). It is a harness gate-red row filed hot at a ticket
boundary, and it was subsequently folded into BL-075 as a duplicate. It is the outlier, not
the convention. **BL-136 appends at EOF**, after BL-134's closing `---`.

**c. The row.** Body landed verbatim from the instruction. **The header line is the only
field derived**, since the instruction's body already carries `Kind` / `Census items` /
`Contract` / `Size` / `Priority` / `Section`:

```
### BL-136 — decision H's consequent: a read-only cross-provider cost summary over the persisted per-provider snapshots (#TBD)
```

Shape taken from the rows around it — `### BL-<n> — <descriptive lowercase clause> (#TBD)`,
as BL-131 (*"decide whether the N>1 compose path is a supported surface"*) and BL-119
(*"a cost snapshot with a declared total and no line items is silently dropped from
discovery"*) both read. The `(#TBD)` suffix is every recent row's.

**The row's own factual claims, checked before landing them** — the row asks a later reader
to verify field names against a snapshot, and does not itself assert them, but its framing
claims were checked here:

| Row says | Checked |
|---|---|
| H states consolidation stays re-derivable by *"a thin read-only aggregator — a separate optional read-layer, never coupled to the pipeline"* | ✓ verbatim, `cloudcost/m2-milestone.md` §H — *Per-provider reporting; no cross-provider roll-up (ratified 2026-07-30, rev 3)* |
| E7 established the layout by execution, snapshots for three providers on disk | ✓ `cloudcost/docs/m5-t1-implementation-notes.md` §E7 — *"Four snapshots across three providers"*, written by `persist_history` on every orchestrator run |
| BL-119 records a declared-total-no-line-items snapshot silently dropped from discovery | ✓ BL-119's title and its *"The consequence is a silent omission, not an error"* paragraph |
| The snapshots carry a generation timestamp and no run identifier | ✓ a live snapshot's keys are `provider, account, period, currency, source_granularity, line_items, totals, balance, generated_at, provider_extra` — a `generated_at` and no run id, which is E7's *"Which run wrote each file is not established"* |
| C1–C15 is the contract population the row defers to | ✓ `cloudcost/milestone.md` §*Contracts (C1–C15 …)*, fifteen `### C<n>` headings |

**d. The `Source:` line**, in the file's own shape — a single backticked block at the row's
foot, as BL-130's and BL-131's are — naming m5 t1 r0 §E7 (2026-08-10) with its file,
decision H with its section and ratification stamp, and the filing direction at the m5-D2
ruling, where H's consequent was named neither decided nor owned.

---

### Y3a — m5-D2's *What this does not decide*

**Unit at HEAD, quoted before the edit:**

> **What this does not decide.** Whether a cross-provider aggregator is ever built —
> H places it outside the pipeline, **E7** establishes it does not exist, and H's own
> precondition is satisfied today. Whether N>1 should later become an operator
> surface — **E5** is the costing if that is ever asked. C4's minor-unit exponent and
> currency-relative tolerance stay filed; they bite only at N>1, which the pipeline
> does not reach.

**After** — the same paragraph, with one dated sentence appended and nothing else touched:

> … which the pipeline does not reach. **The first of those now has an owner:**
> **BL-136**, filed at the reviewer edit of 2026-08-10, carries H's consequent — a
> read-only reader over the per-provider snapshots `persist_history` already writes — as a
> backlog row rather than as an undecided, unowned question.

*"The first of those"* resolves to the paragraph's own first clause, *"Whether a
cross-provider aggregator is ever built"* — the sentence is appended to that paragraph and
names it by position within it, so no second identifier is introduced. `persist_history` is
named because it is what E7 establishes writes the snapshots the row reads.

---

### Y3b — m5-D2's *What bounded requires*

**Unit at HEAD, quoted before the edit:**

> **What *bounded* requires, and this is the operative half.** This surface has been
> left in place three times without being declared, and each silence produced a row:
> BL-070 assumed it dead, BL-131 assumed one route, BL-132 found two contracts
> describing a path nothing takes. **A fourth silent retention is the failure this
> ruling exists to prevent.** Retention is therefore conditional on the declaration
> landing, and the declaration must be reachable from the artifacts a reader actually
> opens:

**After** — the two instructed substitutions, and nothing else in the paragraph:

> **What *bounded* requires, and this is the operative half.** This surface has been
> left in place before without being declared, and each silence produced a row:
> BL-070 assumed it dead, BL-131 assumed one route, BL-132 found two contracts
> describing a path nothing takes. **Another silent retention is the failure this
> ruling exists to prevent.** Retention is therefore conditional on the declaration
> landing, and the declaration must be reachable from the artifacts a reader actually
> opens:

`three times` → `before`; `A fourth silent retention` → `Another silent retention`. **The
three named rows are unchanged** — they are the evidence, they are checkable, and after the
edit they are the only thing carrying the claim. The four numbered declaration requirements
beneath the colon are untouched.

**One thing landed as instructed that a reader may want to overturn, named rather than
buried.** This rewrites text inside a **ratified** decision and lands no dated correction
block beneath it, because the instruction says *"Change nothing else in the paragraph."*
Decision 7 — *"A closed record gets a dated superseded note; its original text is not
rewritten"* — points the other way, and r0 landed exactly such a block at W1b when it
replaced a paragraph in this same section. The reading taken: m5-D2's author is correcting
their own ruling within a day of ratifying it and before the ticket that applies it opens,
and the before/after is committed here, which under R20 is this edit's record. **If the
reviewer wants the note in the document itself, it is a one-block addition and this section
holds the original text verbatim.**

---

### Y4 — §Not established item 3 resolved

**Unit at HEAD, quoted entire before the edit:**

> 3. **`[OPEN]` (a)** **Whether decision H's re-derivability clause is satisfied
>    today.** Decision H drops the merge-across-clouds while stating that a
>    cross-provider total stays later re-derivable from per-provider normalized
>    history. Whether that history is written on the invocations the pipeline
>    actually makes has not been established, and *removed* forecloses more if it
>    is not.
>    **Resolver:** t1's **E7**, in this document.

**After:** the same text, prose unrewritten per decision 7, with the head prefix changed
`` `[OPEN]` (a) `` → `` `[RESOLVED]` (a) `` and the instruction's dated block appended as a
nested blockquote. The `**Resolver:**` line stays — it names something that exists and has
delivered, which is what kind (a) requires.

**The kind letter is kept, on r0's own reasoning for item 2**, not re-derived: *"`[RESOLVED]`
is a **state**, not a fourth kind — in the precedent an (a) or (b) item keeps its kind and
gains the state, and only (c) has a prefix of its own"* (§*Two consequences of that, decided
rather than assumed*). Item 3 is still an open question whose resolver named something that
exists; resolving it did not change that. **No bracketed prefix-change note was added here**,
unlike item 2's: item 2's note existed to record a borrowed precedent, and after item 2 the
precedent is in-document.

**One fill, reported.** The instruction's block reads *"it now has a backlog row rather than
an open item"* with the number to be filled from Y2. Landed as *"it now has a backlog row,
**BL-136**, rather than an open item."* That is the only departure from the block verbatim.

**The item's own resolver did report.** `cloudcost/docs/m5-t1-implementation-notes.md` §E7
concludes: *"H's precondition — normalized per-provider snapshots persisted in the layout it
names — **is satisfied today, by the live pipeline, for all three providers**. H's
consequent — the thin read-only aggregator — **is not built**."* r0 found this and reported
it rather than acting on it, correctly: the disposition is the reviewer's.

---

### Y4 — the vocabulary sweep this prefix change owes

Owed by §Carried in's second carried rule: *"**A vocabulary change owes a sweep of
everything that speaks it.** When a label, status set, field name or prefix changes, derive
the population that speaks it and check each member in the same commit."* **Reported whether
or not it found anything — it found one.**

**Population, derived not assumed.** `grep -n 'RESOLVED\|\[OPEN\]\|\[DECIDED\]'` over
`cloudcost/m5-n1-compose.md` at **`a2d63d1`** (read via `git show HEAD:…`, so the population
is the pre-edit one): **9 lines**, all in §Not established — `:510` (the preamble's kind
list), `:518`/`:519` (r0's correction block), `:524` (item 1), `:533` (item 2), `:541`
(item 2's resolution-block head), `:554` (item 2's prefix-change note), `:563` (item 3),
`:571` (item 4). No other section of the document speaks these tokens, so the sweep does not
reach §Ticket set, §Ratified decisions, §Promotion candidates or §Carried in.
`[Line numbers are a claim about lines and are stamped at a2d63d1, per m5-D1.]`

| Member | Check against the section as it now reads | Result |
|---|---|---|
| **The preamble's kind list** | Names the three R21 kinds; a second resolution changes no kind | Correct as it stands |
| **r0's correction block** | Closed *"— item 2 is resolved"*, a count of one | **Mis-describes — fixed.** See below |
| **Item 1** `` `[OPEN]` (b) `` | Provider-four gate statements; no resolver, none delivered | Correct as it stands |
| **Item 2** `` `[RESOLVED]` (b) `` + its two blocks | Unaffected by a second resolution elsewhere; its blocks are scoped to itself by name | Correct as it stands |
| **Item 3** `` `[RESOLVED]` (a) `` | The member this sweep is owed for | Changed by Y4; consistent |
| **Item 4** `` `[DECIDED]` (c) `` | A decision not to fix, unaffected | Correct as it stands |

**The one fix.** r0's correction block ended *"The opening sentence describes how items
arrive, not what they all still are — **item 2 is resolved**. Corrected rather than left
standing because it is live guidance telling a reader how to read this section."* That
clause is a count of one over a section that now holds two resolved items — **the same shape
as the count Y3b removes**, one section down and one day later. Replaced in place with
*"read each item's own prefix for its current state"*, which is the form
`docs/milestones/hc-consolidation.md` §Not established uses (*"Read each item's `[RESOLVED]`
/ `[OPEN]` / `[DECIDED]` prefix for its current state"*) and which carries no count to
decay. A dated `[amended 2026-08-10 …]` block beneath records the change and states that
nothing else in the block moved. Corrected in place under **decision 8** — it is live
guidance telling a reader how to read the section, which is exactly why r0 corrected it in
the first place.

**Post-edit population, working tree: 10 lines.** The nine above, relocated, plus **one**
introduced by this round — item 3's resolution-block head, `` `[RESOLVED 2026-08-10 — by t1
r0's E7, …]` ``. **No item's prefix changed except item 3's**, which is the change the sweep
is owed for; the preamble fix and its amendment note deliberately carry **no** state token,
which is the point of the fix.

---

### Y5 — t2's `Scope` and `Contract refs`

Both were authored 2026-08-09, before the ruling, and neither was among r0's five authorised
units — which is why r0 reported them (§*Findings for the reviewer — two anatomy fields not
in this edit's scope*) rather than editing them. Each is replaced whole here.

**`Scope` at HEAD, quoted before the edit:**

> **Scope.** After this ticket, the BL-131 ruling is implemented in
> `compose_report_data.py` and its declared interface; `cloudcost/milestone.md`
> §Contracts C4 and C11 state the post-ruling position rather than the
> pre-ruling one; and the rows that resolve with BL-131 carry their dispositions.
> What "implemented" means is the ruling's content and is not assumed here.

**After** — the instruction's text verbatim:

> **Scope.** After this ticket the BL-131 ruling is implemented where a reader meets
> it: `cloudcost/milestone.md` §Contracts **C4** and **C11** state that their
> cross-provider clauses describe behaviour no orchestrator invocation reaches;
> `compose_report_data.py`'s module docstring says the pipeline invokes it at one
> bundle; `cloudcost/runbook.md` no longer asserts the merge is unreachable; and the
> backlog rows that resolve with BL-131 carry their dispositions. **No executable line
> changes, and the declared interface does not change** — the manifest is out of scope
> by decision, not by omission, per `Do not generate`.

The finding was that *"and its declared interface"* read wider than `Touches` allows — the
declared interface is `cloudcost/tools.json`, which `Touches` does not name. The replacement
closes it by saying the opposite explicitly and pointing at the field that makes it a
decision. Cross-checked: t2's `Do not generate` is *"Authorable now, and complete as
written"* and lists no manifest work, and `Touches`'s script bullet reads *"the module
docstring only. No executable line changes"* — both now agree with `Scope`.

**`Contract refs` at HEAD, quoted before the edit:**

> **Contract refs.** t1's implementation notes · this document's §Ratified
> decisions, which will hold the ruling · `cloudcost/milestone.md` §Contracts C4,
> C11 · `docs/backlog-2026-06.md` — BL-131, BL-070, BL-119, BL-121 ·
> `docs/milestones/hc-consolidation.md` — R13, R19.

**After** — the instruction's text, with two resolutions reported below:

> **Contract refs.** This document's §Ratified decisions — **m5-D2**, which this
> ticket applies · t1's implementation notes,
> `cloudcost/docs/m5-t1-implementation-notes.md`, for the establishment m5-D2 rests on
> · `cloudcost/m2-milestone.md` §H · `cloudcost/milestone.md` §Contracts **C4**,
> **C11** · `docs/backlog-2026-06.md` — **BL-070**, **BL-119**, **BL-121**,
> **BL-131**, **BL-132**, and **BL-136**, the row filed at the reviewer edit of
> 2026-08-10 · `docs/milestones/hc-consolidation.md` — **R13**, **R19**. Normative for
> this ticket and not restated in the prompt.

**Two resolutions, both reported rather than silent.** The number was filled from Y2. And
the instruction's *"the row filed at this edit"* was anchored to its date: inside t2's own
anatomy, which a t2 session reads as instructions for itself, *"this edit"* resolves to
t2's edit and names the wrong thing. Everywhere the phrase sits under a dated head — as in
Y4's `[RESOLVED 2026-08-10 …]` block — it was left verbatim.

The finding's three parts all close: the future tense is gone, `cloudcost/m2-milestone.md`
§H is present (m5-D2 reasons from H in three paragraphs), and BL-132 is present (`Touches`
names its row).

---

### Y6 — `Touches`, the `Claude-code prompt`, and t2's row

**a. `Touches`, the backlog bullet at HEAD:**

> - `docs/backlog-2026-06.md` — the **BL-070**, **BL-119**, **BL-121**, **BL-131** and
>   **BL-132** rows.

**After:**

> - `docs/backlog-2026-06.md` — the **BL-070**, **BL-119**, **BL-121**, **BL-131**,
>   **BL-132** and **BL-136** rows.

The bullet only. **`Touches` still names six paths** — the row count inside one bullet
changed, not the path count — so t2's §Ticket set row keeps that figure.

**b. The `Claude-code prompt`'s backlog paragraph at HEAD:**

> **The backlog.** Dispose the five rows as m5-D2 states: BL-070's cross-provider
> deletions **not taken**; BL-121's framing resolved; BL-131 closed on the ruling;
> BL-132's two known instances answered so its census need not re-derive them;
> BL-119 stays open and in scope. Use the closure shape the file itself uses —
> derive it from the rows, do not invent one. Each disposition names **m5-D2**.

**After** — the same paragraph, with one instruction appended:

> … Each disposition names **m5-D2**.
> Then cross-reference **BL-136** — the cross-provider summary row filed 2026-08-10 —
> from **BL-119**'s row, since BL-119's subject is what BL-136 surfaces, and from
> nowhere else. **Do not** cross-reference it from BL-070 or BL-131: this ticket
> disposes both, and a new pointer into a disposed row is noise.

*"Dispose the five rows"* is left standing and is still correct: BL-136 is
cross-referenced, not disposed, so the disposal population is unchanged at five.

**c. t2's §Ticket set row, updated per R19.** The row's state changed at this edit, so R19
binds. The update records **all four** field amendments — Y5's two included. The
instruction's Y6(c) conditions the update on (a) or (b) alone, which is narrower than R19;
both conditions are met either way, so there is no conflict to resolve, but the row is
written to R19's requirement rather than the narrower one. Appended to the existing row,
which is otherwise unchanged:

> … Record of the completing edit: `cloudcost/docs/m5-ruling-edit-implementation-notes.md`.
> **Amended 2026-08-10 at the reviewer edit, four fields** — `Scope` rewritten to name the
> four artifacts the ruling lands in and to state that the manifest is out of scope by
> decision rather than by omission; `Contract refs` re-tensed and extended with **m5-D2**,
> decision H, **BL-132** and **BL-136**; the `docs/backlog-2026-06.md` bullet in `Touches`
> gains **BL-136** (still six paths); and the `Claude-code prompt`'s backlog paragraph gains
> the BL-136 cross-reference instruction. Record of that edit: the same file, §r1

**t1's row is not touched** — this round changes nothing about t1's state, and R19 does not
extend to a ticket the session did not touch.

---

### Deviations

**None from the instruction's units.** Each of Y3a, Y3b, Y4, Y5 and Y6 was quoted at HEAD
and replaced by unit, none by naming sentences. Three fills and one resolution are reported
in place above: BL-136 into Y4's block and into Y5's `Contract refs`, and *"the row filed at
this edit"* → *"the row filed at the reviewer edit of 2026-08-10"* in `Contract refs` only.

**One judgment landed as instructed and flagged for overturn:** Y3b's rewrite inside a
ratified decision without a decision-7 note. Recorded under Y3b with the original text
verbatim.

**No file outside the three named above was changed.** `cloudcost/milestone.md`,
`cloudcost/runbook.md`, `cloudcost/tools.json` and everything under
`cloudcost/scripts|tests|templates|agents` are t2's work and are untouched. The harness is
unedited. **No push. t2 is not opened.**

---

## r2 — the dated block m5-D2 was owed, and the distinction it rests on

`Authored 2026-08-10 at r2, the third commit of the ruling edit, on top of 3f66353 (r1)
and a2d63d1 (r0). Under R15 a further round of the ruling edit; under R20 not a ticket
round and no review file. Figures derived at agents 3f66353 or in the working tree this
round produces, and each says which. Line numbers appear only for claims about lines,
per m5-D1.`

**The last round before t2 opens.**

### Gate on the instruction

| Claim | Resolved |
|---|---|
| `3f66353` at HEAD with five commits beneath | ✓ `3f66353`, `a2d63d1`, `40c2d58`, `5db4585`, `70addd3`, `b648867` — six, in that order, with `a9639de` beneath |
| Both trees clean | ✓ agents and `../aetheris` both `git status --porcelain` → empty |
| The harness has nothing to push | ✓ `../aetheris` at `2ef0517`, `git rev-list --count origin/main..HEAD` → **0** |
| *"all five m5 commits"* to push | ✓ `git rev-list --count origin/main..HEAD` on agents → **4** before r2; origin/main is at `70addd3`, so r2 makes five |
| m5-D2's *What bounded requires* reads at HEAD as the prompt assumes | ✓ quoted verbatim below |
| §Ratified decisions uses a plain backticked bracketed block for m5-D1's `[Extended …]` note | ✓ *"`[Extended 2026-08-09 at r6 with the stamping clause, on claude-code's r5 flag that the exemption covers a whole document's anchors and said nothing about their tense.]`"* — left-margin, blank line either side, not a blockquote |
| §Promotion candidates' first entry establishes a shape r2's entry follows | ✓ bold rule sentence → worked case → *"The rule is not X: it is that…"* → `Origin: <who> at <round>` |

**All hold. Nothing in this prompt was wrong about repo state.**

### What r2 changed, and where

| Z | file | change |
|---|---|---|
| Z1 | `cloudcost/m5-n1-compose.md` §Ratified decisions, m5-D2 | the dated correction block appended beneath *What bounded requires* |
| Z2 | same, §Promotion candidates | the third entry appended, with its filing note |
| Z3 | this file | this section, and one disposition appended to §Review |

`docs/backlog-2026-06.md` is not edited, neither ticket is opened, and the harness is
untouched (HEAD `2ef0517057e4eda991a8da10ccba66650d1e65a2`, clean, nothing to push).

---

### Z1 — the block m5-D2 was owed

**Unit at HEAD, quoted before the edit:**

> **What *bounded* requires, and this is the operative half.** This surface has been
> left in place before without being declared, and each silence produced a row:
> BL-070 assumed it dead, BL-131 assumed one route, BL-132 found two contracts
> describing a path nothing takes. **Another silent retention is the failure this
> ruling exists to prevent.** Retention is therefore conditional on the declaration
> landing, and the declaration must be reachable from the artifacts a reader actually
> opens:

**After:** the unit is **unchanged**. The instruction's block is appended beneath it,
verbatim, as a plain left-margin backticked block in the form m5-D1's `[Extended …]`
note uses.

**Where the insertion point falls, stated per §Carried in's first carried rule.** The
block lands **after the fourth numbered requirement and before *What this does not
decide***, not between the paragraph and its enumeration. The paragraph ends on a colon
that introduces those four requirements; inserting there would sever a claim from the
list it introduces, which is the re-attribution hazard that rule names. So *"the text
above"* in the block spans the paragraph and its enumeration, and the four requirements
are byte-unchanged either way.

**Why the block belongs, recorded because r1 argued the other way and was told to.** The
instruction at r1 said *"change nothing else in the paragraph"*, and r1 complied and
flagged it. The reviewer's ruling at r2: decision 7 governs, and the distinction that
makes this round's three earlier in-place corrections consistent rather than arbitrary
is that **an unpushed session record may be corrected in place and a ratified decision
may not** — a record's claims become meaningful when someone reads them and no one had;
a ratified decision's authority is the act of ratification, not its publication. Filed
as a promotion candidate at Z2.

---

### Z1 — the sweep of §Ratified decisions

**The instructed derivation has a blind spot, and it was corrected rather than run as
written.** The instruction says to derive the population from *"the section's diff across
`b648867..HEAD`"*. **m5-D2 was created inside that range**, at `a2d63d1`. A
`b648867..HEAD` diff therefore renders the whole of m5-D2 as added lines and can show no
*change* within it — including Z1's own subject, which that diff reports as part of a
92-line addition rather than as a 2-line edit. **A derivation that cannot see the instance
it was commissioned to find is not a sweep**, so the population was derived per-commit
across the same range instead. The endpoints are the instruction's; only the granularity
changed.

**Method.** The section (`## Ratified decisions` up to `## Promotion candidates`) extracted
at each of the six commits in `b648867..HEAD` and diffed consecutively:

```
b648867 -> 70addd3 : 3 removed / 11 added
70addd3 -> 5db4585 : 0 removed /  0 added
5db4585 -> 40c2d58 : 0 removed /  0 added
40c2d58 -> a2d63d1 : 5 removed / 92 added
a2d63d1 -> 3f66353 : 3 removed /  6 added
```

`[The counts are a claim about lines and are stamped at the commits named, per m5-D1.]`

**Population: four changed units**, across three commits. t1 (`5db4585`) and t1 r1
(`40c2d58`) touched the section not at all, which is the positive control that the
extraction reaches — a run that reported change everywhere would be reporting its own
noise.

| # | Unit | Changed at | Dated note beside it? |
|---|---|---|---|
| 1 | The section's **opening paragraph**, closing sentence | r6 (`70addd3`) | **No at the time**; superseded whole at `a2d63d1`, which carries a block |
| 2 | **m5-D1**, second paragraph — the stamping clause | r6 (`70addd3`) | ✓ *"`[Extended 2026-08-09 at r6 with the stamping clause…]`"* |
| 3 | The section's **opening paragraph**, replaced whole | ruling edit (`a2d63d1`) | ✓ *"`[corrected in place 2026-08-10 at the ruling edit…]`"* |
| 4 | **m5-D2**, *What bounded requires* | r1 (`3f66353`) | **No** — Z1's subject, fixed at this round |
| 5 | **m5-D2**, *What this does not decide* | r1 (`3f66353`) | **No — second instance. Reported, not fixed.** |

**Unit 1 is not the Z1 class, and the reason is the distinction itself.** The section's
opening paragraph is not a ratified decision; it is the section preamble, and `a2d63d1`'s
block reasons explicitly that it falls under **decision 8** (*"Live operational guidance
is corrected in place"*) rather than decision 7. It does carry one residue worth naming:
that block quotes the **r6** wording it displaced, not the **r5** wording r6 itself
displaced, so the r5 sentence (*"An empty section at open is the correct state and is
stated rather than omitted"*) survives only in `m5-pin-edit-implementation-notes.md` §T1.
Named, not fixed — it is a preamble, not a decision.

**Unit 5 is the second instance, and I believe it needs a block.** At r1 the *What this
does not decide* paragraph gained a sentence — *"**The first of those now has an owner:**
**BL-136**, filed at the reviewer edit of 2026-08-10…"* — appended inside a ratified
decision, after ratification, with no bracketed note. **Not fixed, per the instruction's
"do not fix a second instance"**; whether a given change needs a block is the reviewer's
to apply.

**The argument for a block, and the argument against, both stated:**

- **For.** Z1's own principle reaches it without modification: a reader citing m5-D2's
  *What this does not decide* is entitled to know that clause is not what was ratified at
  the gate stop. It is an addition rather than a rewrite, but the reader's question is the
  same one.
- **Against.** The appended sentence **self-dates** — *"filed at the reviewer edit of
  2026-08-10"* — which the *"three times"* rewrite did not. A reader can see the clause
  postdates the ruling. What it does not say is that it was **added after ratification**,
  which is the fact a block would carry.

I read the *for* as stronger, which is why this round **holds rather than pushes**.

---

### Z2 — §Promotion candidates, third entry

**Section at HEAD, quoted before the edit:** the preamble (*"Candidates recorded here are
promoted or dropped at this round's close under the methodology's §7 ritual; recording one
is not promoting it…"*), then two entries — **A check that structurally cannot observe the
failure it stands in for returns green for the wrong reason**, closing *"Origin:
claude-code at m5 r4, against a check the reviewer specified"*; and **An elision justified
by "this is inlined above" carries the check that establishes it, or the diff is not
elided**, closing *"Origin: claude-code at m5 t1 r1…"* followed by its
`[Filed by the reviewer at the m5-D2 ruling edit, 2026-08-10…]` note.

**After:** the instruction's third entry appended verbatim beneath the second entry's
filing note, separated by a blank line, following the shape the first entry establishes —
bold rule sentence in the imperative-general voice → the worked case in past tense with
the specific artifact named → the generalisation in *"The rule is not X — it is that…"*
form → `Origin: <who> at <round>, <against what>` — plus its own dated filing note, which
is the shape the second entry established.

**Its worked case is checkable in this file.** *"This round corrected several unpushed
records in place"* resolves to three: §Not established's preamble correction block
(`a2d63d1`, W4's sweep), that block's own *"item 2 is resolved"* clause (`3f66353`, §r1's
sweep), and §Ratified decisions' opening paragraph (`a2d63d1`, W1b). Each argued decision
8 or a no-reader-yet ground. **None of the three is a ratified decision**, which is why
the entry says the licence comes from the artifact's kind and not from its push state, and
why fixing them is not what it asks for.

---

### Deviations

**One, reported above and not silent:** Z1's sweep was derived per-commit rather than from
a single `b648867..HEAD` diff, because the single diff structurally cannot see a change to
text created inside its own range — including the change the sweep exists to find. Same
endpoints, finer granularity.

**Everything else landed as instructed.** Z1's block and Z2's entry are the instruction's
text verbatim; the only judgement exercised was Z1's insertion point, stated above.

**No file outside `cloudcost/m5-n1-compose.md` and this one was changed. t2 is not opened.
The harness is unedited.**

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

### r1 — the reviewer's dispositions on r0's own findings

`Dated 2026-08-10 at r1. The §Review preamble above is scoped to "the reviewer's findings
on t1 r1", which was the whole population when it was written; this group is a second and
different one — the reviewer's dispositions on the findings **this file** raised at r0.
Added as its own group rather than by rewriting that preamble, which is a closed record
under decision 7.`

**Identifier resolution.** The instruction labels these *Finding 1*, *Finding 2*, *Finding
3* and *the flagged line*. This file does not number them, so each is resolved to the text
it names before its disposition is recorded, rather than transcribed:

| Instruction's label | Resolves to, in this file |
|---|---|
| **Finding 1** | §*The vocabulary sweep* → *"Finding — item 3's resolver has delivered, and the item still reads `[OPEN]`"* |
| **Finding 2** | §*Findings for the reviewer* → **A** — *"`Scope` says the ruling is implemented in the script's declared interface"* |
| **Finding 3** | §*Findings for the reviewer* → **B** — *"`Contract refs` says §Ratified decisions *will hold* the ruling"* |
| **The flagged line** | §*Claims in m5-D2 checked against t1's record*, closing paragraph — *"One claim in m5-D2 is not checkable from the repo and was not checked"* |

#### Finding 1 — item 3 open while its resolver had reported

*Raised at r0: the document ratified E7's answer in §Ratified decisions while §Not
established carried the same question open with a resolver that had reported.*

**Disposition: accepted; resolved at Y4.** Declining to resolve it from inside the ruling
edit was right — it is the same reasoning under which t1 declined to resolve item 2 from
inside a ticket, and the disposition belongs to the reviewer.

#### Finding 2 — t2's `Scope` read wider than its `Touches`

*Raised at r0 as finding **A**.*

**Disposition: accepted; `Scope` rewritten at Y5.** The packet was right that the tension
was a reader's rather than an executor's, and right not to leave it standing: an anatomy
whose `Scope` and `Touches` disagree is how a later `Touches` gets written wrong.

#### Finding 3 — t2's `Contract refs` in the future tense, omitting decision H and BL-132

*Raised at r0 as finding **B**.*

**Disposition: accepted; rewritten at Y5.**

#### Flagged line — m5-D2's *"three times"*

*Raised at r0 in §Claims in m5-D2 checked against t1's record: the count was named rather
than silently ratified, on the ground that whether the surface's three rows constitute
three retentions is a characterisation and not a countable fact.*

**Disposition: accepted; the count is removed at Y3(b).** The flag was correct and is the
reviewer's own standing rule applied to the reviewer: a spec asserts no checkable specific,
and a count of retentions is a characterisation wearing a number's clothes. The enumeration
that follows it — BL-070, BL-131, BL-132 — was always the evidence, and it stays exactly as
it was.

**A second instance of the same shape, found by the sweep this round owes and fixed with
it:** r0's §Not established preamble correction block closed *"— item 2 is resolved"*, a
count of one that item 3's resolution falsified within the day. Recorded under Y4's sweep.

### r2 — the reviewer's disposition on r1's flagged line

`Dated 2026-08-10 at r2. One entry, on the line r1 flagged against its own instructed
behaviour.`

#### The flagged line — a ratified decision corrected without a dated block

*Finding, raised by claude-code at r1 against its own instructed behaviour: Y3(b) rewrote
text inside m5-D2 and landed no correction note, which decision 7 points against and which
r0 had itself done differently at W1b in the same section.*

**Disposition: accepted; the block lands at r2 (Z1), and the distinction the earlier
in-place corrections rested on is recorded as a promotion candidate (Z2).** The
instruction was the reviewer's and was wrong; the session followed it and flagged it,
which is the behaviour that makes a wrong instruction recoverable.
