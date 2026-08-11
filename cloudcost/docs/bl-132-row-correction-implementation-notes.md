# BL-132 — the row-correction round (implementation notes)

`Dated 2026-08-11. A reviewer-directed round, not a ticket round: per **R20** it gets no review
file, and this file is its committed record — the reviewer's findings land here, appended as a
dated "## Review" section with the findings verbatim and the dispositions beneath, which is the
shape R20 requires. BL-132 is not reopened: the row is DONE, its census stands, and what changes is
a claim made inside its records plus one record the sweep never wrote.`

**Filename convention, checked rather than assumed.** `ls cloudcost/docs/` → **36** files, **34**
ending `-implementation-notes.md`; the two exceptions are `m3-linode-scout.md` and
`m5-scoping-landing-notes.md`. The stem follows the shape `bl-132-anatomy-implementation-notes.md`
established for a reviewer edit whose subject is a row — `bl-NNN-{edit-name}-` — leaving
`bl-132-implementation-notes.md` to the ticket, which is where the row's `Source:` still points.

**Measurement stamp.** Every count, line number and quotation below was derived at agents
`d4696c4` and harness `6241972`, before this round's own edits. Both repos were level with
`origin/main` at that commit (`git rev-list --left-right --count origin/main...HEAD` → `0 0` in
each), so **HEAD is published**, which decides the form every correction here takes: per
`../aetheris/CLAUDE.md`, a published record is corrected **in place and dated**.

---

## 0. The gate on the prompt

The prompt's claims were resolved before acting. Four held; **two did not**, and the round did not
act on the wrong parts.

**Held.** (a) BL-132's row carries C2's superseded wording — it does, at
`docs/backlog-2026-06.md:7842–7843`. (b) `cloudcost/milestone.md` carries the corrected sibling — it
does, at `:391–394`. (c) The sweep has no implementation-notes record — verified two ways:
`git log --oneline -- cloudcost/docs/bl-132-implementation-notes.md` returns `88fa5f4` and `a690014`
and nothing later, and `git show --stat 8f36e45` returns one path, `cloudcost/milestone.md`. (d) The
contract refs are correctly numbered — `docs/milestones/hc-consolidation.md` `:385` R15, `:468` R19,
`:528` R20, `:546` R21, with R1–R21 unbroken and non-duplicated. One paraphrase in the prompt is
loose without being wrong in substance: R20's subject is a reviewer-authored **section-scoped edit**,
and its whole point is that such an edit is *not a round*, so "reviewer-authored round" inverts the
term R20 exists to exclude.

**Did not hold — 1. "C2's exercise claim."** C2's correction was not an exercise claim and was not
an over-breadth narrowing. `8f36e45`'s message says of it: *"The claim is now stated over what was
measured and is stronger."* The **exercise** corrections in that sweep were **C1**
(*"exercised on every invocation"*) and **C6** (*"computed on every run"*); **C3** was set
conflation. C2 was the one of the four whose population grew.

**Did not hold — 2. "over-broad by the same ground that corrected its sibling."** There is no such
single ground to apply, because the sibling's ground was not over-breadth. The round therefore ruled
on the test the prompt's own next sentence names — *whether the claim it makes is true at HEAD* —
and reports the mislabel rather than following it. §1b is that ruling.

**One instruction collision, named rather than resolved silently.** §1d says to correct any further
site that is over-broad; Do-not-generate says **no edits to `cloudcost/milestone.md`**. The
constraint wins: milestone sites are reported as observations and left alone, and this round does not
re-litigate the file it was told is its source of truth.

---

## 1a. The ground — three quotations, verbatim

**(i) The row, `docs/backlog-2026-06.md:7839–7843`**, inside BL-132's DONE disposition, §*Method —
the entry point was run, not read* — as it stood at `d4696c4`:

> **The result that could not have come from reading**: **C2**'s X1 clause says the ~fifteen raw
> provider state strings *"reach the rendered report verbatim"* via evidence text — at HEAD both
> interpolation sites are gated on `STOPPED_STATES`, so only the canonical value can, and the
> composed payload carries no `state` field at all. Zero in either payload and either rendered
> report, against **18** in the inventory those runs consumed.

**(ii) `cloudcost/milestone.md:391–394`**, C2's reachability sentence as it stands now — the text
this round adopts:

> Measured over three chains of the orchestrator's own STEP 3 forms across recorded DO and Linode
> artifacts — DO at both arg forms and Linode at the first: **zero** `"state"` across **all three
> composed payloads and all three rendered reports**, against a control of **18** in the DO inventory
> those chains consumed.

**(iii) The stated ground for the correction**, from the commit that made it. The commit was
identified from the file's own history — `git log --oneline -- cloudcost/milestone.md` → `8f36e45`
(full: `8f36e4567cb86e6289439be6bf04cce827a6edfc`), `Tue Aug 11 10:09:30 2026 +0530`, one file,
+38/−13 — not taken from the prompt, which named no SHA for it. Its C2 paragraph, verbatim:

> C2 "zero in either payload and either rendered report" — "either" is two, which
> contradicted the same sentence's "three runs", and was the honest count: form
> B's payload and report were not in the original check. Re-measured over all six
> artifacts, all zero. The claim is now stated over what was measured and is
> stronger.

and the message's opening paragraph, which is the sentence the episode is cited for:

> The earlier sweep covered a literal string, not a class: grep for "every detect
> pass" over cloudcost/ and docs/. It found C8 only because C8 shared the wording,
> not because the class was searched. Stated plainly because the population a
> sweep covered is the thing that makes its result mean anything.

---

## 1b. The ruling

**The row's sentence does not hold at HEAD, and one of its two clauses is over-broad — so the unit
is replaced, though not for the reason the prompt gives.** Read against (ii) and (iii) rather than
against a supersession label: *"Zero in either payload and either rendered report"* fails by
**understatement**, since *"either"* is two and `8f36e45` re-measured all six artifacts of the three
chains with every one zero, so the row states its result over a third of the evidence that supports
it and is weaker than the record it summarises; that half is stale-but-true and is not over-broad.
*"against **18** in the inventory those runs consumed"* fails the other way and **is** over-broad:
those three chains consumed **two** inventories carrying different counts — 18 DO and 15 Linode, the
figures C6's own basis states at `cloudcost/milestone.md:587` — so attributing one control to *the*
inventory those runs consumed conflates two populations into one, which is precisely the defect
`8f36e45` corrected in **C3** ("called two different sets 'the three runs'"). A claim that is
simultaneously too narrow about what it measured and too broad about where its control came from is
not repairable by trimming a word, which is why the whole unit is replaced with (ii)'s text rather
than edited clause-wise. The verdict — guarantee reachable, X1's clause source-only — is untouched
by this and was never in question.

---

## 1c. The edit to the row

**Unit at HEAD:** the §*Method* paragraph quoted at §1a(i). **Replaced** — not scoped by naming a
sentence — with (ii)'s text carried over verbatim, plus a dated block at its position.

**The shape was established from an existing instance in the same file, and the instance is named:**
`docs/backlog-2026-06.md:3096–3102`, BL-077's Done-when correction —
`> **`[corrected 2026-08-09 (hc-d, G5). The population is 29, not 31 — derived, not inherited.]`**`
followed by the derivation beneath, inside the blockquote. That instance was chosen over the other
shape the file uses — the heading-prefixed `**`[corrected 2026-08-06]` Done when:**` marker at
`:2287`, `:5897`, `:5910`, `:5919`, `:5938` — because the unit here is a **measurement claim** and
`:3096` is the file's only correction of a count, which is the same job. The superseded wording is
quoted in the block, per the convention `:2274` and `:5873` both state explicitly (*"the original
text below is left intact except where marked"*).

Note for a later reader: `grep -n "corrected 2026-08-1" docs/backlog-2026-06.md` returned **nothing**
before this round — the file carried no August-11-dated in-place correction, so the shape is
inherited from August 9 rather than from a same-day sibling.

---

## 1d. The class sweep

**The vocabulary, published before it was run.** Derived from the sentence's own claim, which has
two parts — a measured population and a control attributed to one inventory — plus the
exercise-class terms the prompt names, so that framing is *tested* rather than assumed:

| | term | what it is for |
|---|---|---|
| T1 | `either payload` | the payload population |
| T2 | `either rendered` | the report population |
| T3 | `rendered report` | the artifact the claim is about |
| T4 | `consumed inventory` | the control's source |
| T5 | `the inventory those` | the control's attribution |
| T6 | `those runs consumed` / `those chains consumed` | which passes the control came from |
| T7 | `every invocation` | exercise class (the prompt's framing) |
| T8 | `every run` | exercise class |
| T9 | `on every` | exercise class, widest form |
| T10 | `every detect pass` | the **earlier** sweep's literal, to see what it would and would not have caught |

**Negative controls, minted fresh for this sweep:** `either inventory`, `19 in the inventory`,
`both rendered reports`. Fresh rather than reused deliberately — m5's §Open for the next cycle
carries the finding that *"a negative-control token stops being a negative control once a record
quotes it"* (`cloudcost/m5-n1-compose.md:1079–1084`), and the tokens a prior edit used for this job
now appear in that edit's own committed record. **All three returned 0.** No control was discarded.

**Hit counts over `cloudcost/` and `docs/`:** T1 **3**, T2 **3**, T3 **19**, T4 **1**,
T5 (`the inventory those`) **1**, T6 **2** (one each form), T7 **6**, T8 **49**, T9 **124**,
T10 **3**. All figures are at the `d4696c4` stamp and are re-derivable against it with
`git grep -c -F -e '<term>' <this commit>^ -- cloudcost docs`.

**A finding this round produced about itself, and it is a precision on m5's carried entry rather
than a new finding.** Re-running the three controls over the tree **after** this round's commit
returns **1 each**, and every hit is the one line of this file that lists them. Minting fresh
satisfied m5's finding for *this* sweep and did nothing for the next: **the act of recording a
control is what spends it**, and recording is a step every round performs by rule. So the carried
entry's remedy — *"controls are minted fresh per sweep"* — is necessary and not sufficient, and a
round that mints fresh still hands its successor three dead tokens. **Destination named rather than
acted on:** m5's `### Open for the next cycle` entry in `cloudcost/m5-n1-compose.md`, which is
already open, is already what the next cycle's §7 reads, and is **not in this round's `Touches`** —
so this is relayed to the reviewer for that entry, and no new row is filed. The premise terms
inflate the same way and for the same reason (the dated blocks quote the superseded wording, as the
convention requires), so a reader re-running this vocabulary at HEAD will not reproduce the counts
above and should not expect to.

**Every site carrying the premise — three, of which two were live:**

| site | verdict |
|---|---|
| `docs/backlog-2026-06.md:7842–7843` | **live and wrong** → corrected at §1c |
| `cloudcost/docs/bl-132-implementation-notes.md:62` (§2's C2 basis cell) | **live and wrong** — `0 state in either payload and either rendered report against 18 in the consumed inventory`; the same understatement and the same singular-inventory over-breadth → corrected in place, dated, in this commit. **BL-140's note named only the backlog copy; this cell is a second recurrence it did not name** |
| `cloudcost/milestone.md:395` | **not a live claim** — it is *inside* the `[Corrected …]` block, quoting the superseded text so the correction has a before. Editing it would destroy the record it exists to keep, and the file is read-only this round. **Reported, not edited** |

**The exercise class, filtered.** T7–T9 return **179** raw hits; the class the prompt named is not
where the defect is. Filtered to sites carrying a BL-132 reachability premise, every hit is either
already-corrected text (`milestone.md:346`), text inside a correction block (`:348`), a sentence the
sweep judged accurate **with its basis stated** (`:734` C9 — the AWS chain did write its orphan file;
`:776` C10 — `prior_period` on all four compose payloads; `:924` C14 — already qualified *"every run
with a cost snapshot"*), or a generic methodological sentence making no per-contract claim
(`bl-132-implementation-notes.md:55`). The remaining hits are other use cases and unrelated review
files. **No further site is over-broad by §1b's ground**, and no milestone edit was made.

**What T10 shows, which is the point of including it.** `every detect pass` returns 3 — and none is
a live over-broad claim: `milestone.md:588` is post-sweep and correct as stated, and the other two
(`bl-132-implementation-notes.md:78`, and BL-140's `Source:` block in `docs/backlog-2026-06.md`,
`:8288` at the stamp and `:8313` after this commit's insertion) are records *quoting* the literal. A term-for-term repeat of the earlier sweep would find nothing today and would have missed
both live sites, which is the literal-vs-class distinction reproducing itself one round on.

---

## 1e. The missing record

**The claim was verified before anything was appended, and it holds.**
`git log --oneline -- cloudcost/docs/bl-132-implementation-notes.md` → `88fa5f4`, `a690014`, nothing
later; `git show --stat 8f36e45` → one path. No section of the file mentioned the class sweep.

Appended as **§8**, *The exercise sweep — appended 2026-08-11, one round after the row closed*,
carrying the sweep's date, the literal-vs-class distinction quoted as the commit message states it,
the four-narrowed / five-held split with the message's own basis for each of the nine, and what the
sweep did not reach. **The vocabulary is recorded as not recoverable**: the message states the
*earlier* sweep's term exactly and names the class the second covered, but records no term list, and
the diff carries none — so a vocabulary written there now would be this round's presented as the
sweep's. What is recoverable and recorded instead is the population and instrument (all nine
sentences, checked against what the five chains produced rather than against source).

---

## 2. The four verifications — report only, nothing fixed

### 2a. Dialyzer's deferral

**The file, resolved rather than assumed.** `cloudcost/docs/` holds four `t3`-matching files;
the m5 one is **`cloudcost/docs/m5-t3-implementation-notes.md`** (771 lines). The others —
`t3-implementation-notes.md` (m1 era), `m2-t3-`, `m3-t3-` — are different cycles.

**Recorded as deferred, and it names a firing trigger.** The gate table at `:468` reads
`| `mix dialyzer` | **Deferred — see below** |`, and `:485–491`:

> **`mix dialyzer` is deferred, not skipped, and the deferral names a trigger that can fire.**
> Skipping silently makes *"we skipped dialyzer"* the precedent, and the gate that never runs is
> the gate that rots — which is the rule's whole reason for existing. **Trigger: the next
> harness ticket whose `Touches` names any `.ex` or `.exs` file runs it; and if no such ticket
> runs before the next cycle's close, that close runs it.** Recorded here. **No home was
> invented for it in the round document** — this document has no cross-cycle obligations section
> and the ticket's instruction was to name one only if it exists.

**Verdict: present, essentially verbatim.** The instructed trigger and the recorded one differ by
one word — the recorded text inserts `and` after the semicolon. Both arms are otherwise identical.

**Whether the round document carries a home: it does, and the notes' claim that it does not is
wrong.** `cloudcost/m5-n1-compose.md` has `## Carried in` at `:931`, whose own preamble
(`:933–934`) describes it as *"Inherited from `docs/milestones/hc-consolidation.md` §Milestone
summary → §Open for the next cycle"*, and `### Open for the next cycle` at `:1035` — which the same
document calls *"the subsection the next cycle's §7 reads"* at `:1067–1068`, and which **t3 itself
wrote** under §Close criteria clause 6. `## Not established` (`:809`) is a second candidate: R21's
kind **(b)**, a carried unknown naming what would settle it and inventing no owner, is the shape of
a deferred gate with a firing trigger. The obligation is instead recorded in three places that are
*not* that subsection — the notes above, the summary narrative at `:1006–1008`, and the t3 ticket-set
row at `:47`. **Reported, not added:** the prompt says if absent, do not add it, and what is absent
is the obligation from the subsection, not the trigger from the record.

### 2b. The correction-rule reading

**(a) `../aetheris/CLAUDE.md:956–966`** — the authority, quoted from the file:

> - **An artifact's kind decides how a correction is made; its push state decides only whether the
>   correction may be silent.** Correcting an unpushed record in place is sound: its claims become
>   meaningful when someone reads them, so a dated supersession block would preserve a reading
>   history no reader ever had. A published record is the third case, and it is stated here rather
>   than left to be entailed: correct it in place, and date the correction — the licence to be
>   silent lapsed when the record acquired readers, which is the same reason that granted it while
>   it had none. A ratified decision is different in kind. Its authority is the act of ratification
>   rather than its publication, so a reader citing it later is entitled to know its text is what
>   was ratified — and cannot learn that from a notes file they have no reason to open. Correct it
>   with a dated block that quotes the superseded wording in the position it occupied, never
>   silently, however few people have read it.

**(b) `cloudcost/docs/m5-t3-implementation-notes.md:630–634`:**

> **Not corrected, and the reason is this round's own promoted entry.**
> `docs/reviews/m5-cloudcost-t2-review.md` is a committed and **pushed** review record of a closed
> round. The entry promoted at clause 1 — *an unpushed artifact may be corrected in place; a
> ratified one may not* — puts an in-place edit there out of bounds, and r1's `Touches` does not
> name it either. Recorded here and in the review file so the next reader of that sentence knows.

**(c) `docs/reviews/m5-cloudcost-t3-review.md:122–125`:**

> **Not corrected here**: that file is
> a committed, pushed review record of a closed round, and this round's own promoted entry says a
> ratified artifact is superseded with a dated block rather than edited. Recorded so the next
> reader of that sentence knows.

**Both (b) and (c) state a narrower rule than (a), and the divergence is exact.** (a) governs *how*
a correction is made and holds every case correctable: kind picks the method, push state decides
only whether the method may be silent. (b) converts that into *whether*: **"puts an in-place edit
there out of bounds"** — a prohibition where (a) states a method — and it reaches that by sorting a
**pushed** record into the ratified case, making push state the operative axis (a) reserves for
silence alone. (c) narrows twice: **"superseded with a dated block rather than edited"** treats the
dated block as an *alternative* to correcting where (a) makes it the correction's form, and it
applies the ratified case to a *"committed, pushed review record"*, which by (a) is a record whose
publication requires only that its correction be dated. Both divergences are already annotated in
place — (b) at `:636–675`, (c) at `:127–134` — and (a)'s own dated block at `:986–987` names the
failure in the same terms: *"a reader resolving the ambiguity the cheaper way got a prohibition
where the rule means a method."* **Nothing proposed.**

### 2c. The two carried findings

**`### Open for the next cycle` exists**, `cloudcost/m5-n1-compose.md:1035`, under §Milestone summary
(`:951`) alongside `What shipped`, `What the close's six clauses found`, and `What stays open, and
why that is correct`. **Both expected entries are there**, at `:1064–1084`, and there is more than
was expected — the subsection also carries two earlier practices (`:1037–1043`) and a dated
supersession block over them (`:1045–1062`). The two entries in full:

> **Two findings carried forward for the next cycle's §7**, appended 2026-08-11 at the
> body-addition edit. Both are below §7's bar and **neither gets an exception: this round has
> excepted the bar twice already, and a third would make it a formality.** They are recorded
> here because this is the subsection the next cycle's §7 reads, and it is the subsection m5
> itself inherited its own carried candidates through.
>
> **§7's distillation can lose what the candidate got right.** The correction-rule entry was
> distilled from a §Promotion candidates entry that carried the disambiguation the promoted
> headline dropped — the candidate said *"The rule is not never correct in place"*, and the
> headline compressed from it kept the ambiguous phrase and lost the clause that resolved it.
> §7's verification step confirms an entry can be **read out of** its destination file; it
> does not compare the entry against the candidate it came from, so a distillation that loses
> a clause passes verification. Carried rather than promoted: one instance, and the round has
> excepted §7's bar twice already.
>
> **A negative-control token stops being a negative control once a record quotes it.** A
> sweep at the record-correction edit reused the token a prior edit had used for the same job
> and it returned three hits — the prior edit's own committed record, quoting its control
> table. Controls are minted fresh per sweep, or a sweep over records of prior sweeps finds
> its own instruments and reads them as content. Carried rather than promoted: one instance,
> found by the sweep it broke.

Both match what was expected, in substance and in framing (*"Carried rather than promoted"*, one
instance each, no exception taken). **What is not there is the dialyzer obligation from 2a** — the
subsection the document itself calls the one the next cycle reads does not carry it.

### 2d. drift_check's exemption

**Declared in four places, all in this repo; `../aetheris/CLAUDE.md` has zero hits for
`project_knowledge`.** Quoted in their own words:

`scripts/drift_check.py:24–30` — the canonical statement:

> --strict promotes WARN to FAIL, with one exemption: project_knowledge
> manifest-STALENESS WARNs stay WARN and do not affect the exit code (mid-cycle
> staleness is expected truth between export boundaries). The uncommitted-edit WARN
> is exempt on the same terms — it reports that this run cannot answer the staleness
> question yet, not that something regressed. Structural manifest problems (missing
> file, unknown repo, git failure) are NOT exempt and still FAIL.
> So under --strict the invariant is "zero UNEXPLAINED WARNs", not "zero WARNs".

`scripts/drift_check.py:78–80` — the implementation site: *"--strict promotes WARN to FAIL, EXCEPT
for strict_exempt WARNs (currently only project_knowledge manifest-staleness). Mid-cycle manifest
staleness is expected truth between export boundaries, not a regression — see BL-009."* The other
two are `CLAUDE.md:245–254` (§Definition of done) and BL-009 itself at
`docs/backlog-2026-06.md:4180–4189`, the originating decision of 2026-07-15.

**What would refresh the manifest.** `docs/project-knowledge-manifest.md:13` — *"Refresh trigger:
milestone end, or before any handoff session."* The procedure is
`prompts/bl-002-refresh-project-knowledge.md:3–4`, same trigger, with the upload half explicitly the
human's (`:11–13`). The manifest's own header (`:15–21`) records the blind direction: the check
detects the repo moving ahead of an export, never a file uploaded without a regen.

**Whether anything schedules such a refresh: no.** No cron, timer or CI job — every `cron`/`scheduled`
hit in either repo concerns the harness's `scheduled_runs` table, not export. No open row owns it:
BL-002 and BL-009 are both `Done 2026-07-15`. The trigger is event-based and human-owned, and it
**has fired** on the m5 close, which that round recorded while explicitly filing nothing —
`cloudcost/docs/m5-t3-implementation-notes.md:727–731`: *"No manifest was refreshed, no row was
filed, and no file was edited for this question — the instruction reserves that decision to the
reviewer."* That reserved decision does not appear in `docs/reviews/m5-cloudcost-t3-review.md`
either. **No ruling offered here; the exemption's soundness is the reviewer's call.**

---

## 3. Deviations

**None from the round's scoping.** `Touches` named `docs/backlog-2026-06.md` (BL-132's disposition
plus any site 1d surfaces), `cloudcost/docs/bl-132-implementation-notes.md`, and this round's own
notes file. The sweep surfaced one further site and it was inside a `Touches` file already, so no
path outside `Touches` changed. `cloudcost/milestone.md` was not edited.

**Two prompt claims were not acted on**, per §0: the "exercise claim" mislabel and the
"same ground" framing. Both are reported rather than followed.

---

## 4. Done-check

- **Item 1** — vocabulary published before hit counts, with three fresh negative controls, all
  returning 0. §1d.
- **Item 2** — every edit shown in the diff as the HEAD unit replaced, with a dated block at its
  position; no edit scoped by naming a sentence.
- **Item 3** — Part 2 answered in full with verbatim quotes. §2.
- **Item 4** — `python3 -m pytest cloudcost/tests/ -v` and `python3 scripts/drift_check.py --strict`
  run, counts recorded in the packet. Neither expected to move; `drift_check --strict` is run
  **post-commit** as well, because check 8 compares the manifest against committed history and a
  pre-commit run cannot see the staleness a manifest-tracked edit introduces.
- **Item 5** — one commit, push held.
