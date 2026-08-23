# m5 obligation-landing edit — implementation notes

`Reviewer-directed round, 2026-08-11. Not a ticket round: per R20 it gets no review file, and
this file is its committed record. The reviewer's findings on it land here, appended as a dated
"## Review" section with the findings verbatim and the dispositions beneath. No ticket is
reopened and no ticket's state changes, so R19 is not engaged and §Ticket set is untouched.`

**Subject.** Three landings and one row, executing what the preceding round
(`cloudcost/docs/bl-132-row-correction-implementation-notes.md` §2a–§2d) verified read-only and
relayed to the reviewer without acting on: the dialyzer obligation had no home in the subsection
the next cycle reads (§2a, §2c); the negative-control finding's remedy was shown insufficient by
the round that applied it (§1); a claim in a pushed record was shown false (§2a); and the
manifest refresh was shown to have no owner (§2d).

---

## 0. The opening gate — both repos level with origin/main

Every edit below is to a **committed and pushed** record, so every one takes the published-record
form. Established before the first edit:

```
$ git rev-parse HEAD; git rev-parse origin/main          (agents)
0587bf383afe9ece803d2ad1fcd4bf84ca4b238c
0587bf383afe9ece803d2ad1fcd4bf84ca4b238c
$ git rev-list --left-right --count origin/main...HEAD   → 0   0
$ git status --short                                     → (empty)

$ git rev-parse HEAD; git rev-parse origin/main          (harness ../aetheris)
624197275358d29e2bb18f7e2bafcbc998e2ddf9
624197275358d29e2bb18f7e2bafcbc998e2ddf9
$ git rev-list --left-right --count origin/main...HEAD   → 0   0
$ git status --short                                     → (empty)
```

**The rule applied, quoted from the harness `CLAUDE.md` at `6241972` (read-only; not edited):**

> **An artifact's kind decides how a correction is made; its push state decides only whether the
> correction may be silent.** … A **published record** is the third case, and it is stated here
> rather than left to be entailed: **correct it in place, and date the correction** — the licence
> to be silent lapsed when the record acquired readers, which is the same reason that granted it
> while it had none.

So each edit below quotes its HEAD unit, replaces that unit, and lands a dated block at the
unit's own position. No edit is scoped by naming a sentence.

**Contract refs read, and none is misnumbered:** R12 (`hc-consolidation.md:335`), R15 (`:385`),
R19 (`:468`), R20 (`:528`), R21 (`:546`). R20 is the one that governs this round's form.

---

## 1. A1 — the shape of `### Open for the next cycle`, reported before anything was appended

`cloudcost/m5-n1-compose.md` §Milestone summary → `### Open for the next cycle`, read in full at
`0587bf3` where it occupied `:1035–1087`. It holds **five** things, not one uniform entry type:

| # | Lines at `0587bf3` | What it is |
|---|---|---|
| 1 | `:1037–1043` | Two **practices** — bolded headlines inline, parenthetical basis, one closing disposition covering both (*"Neither is promoted here…"*) |
| 2 | `:1045–1062` | A **dated supersession block** over half of (1): `[Corrected 2026-08-10 at t3 r1, on the reviewer's F1…]` |
| 3 | `:1064–1068` | A **dated group preamble** stamping what follows — *"appended 2026-08-11 at the body-addition edit"* — carrying the bar-exception reasoning and the why-here rationale |
| 4 | `:1070–1084` | Two **findings**, each: bold headline sentence → explanation → basis → §7 disposition (*"Carried rather than promoted: one instance…"*) |
| 5 | `:1086–1087` | **`Sequence from here:`** — a forward-looking directive. No basis, **no §7 disposition** |

**How an entry opens:** with a **bolded headline in sentence form**, in every case.
**Whether entries carry a basis:** the practices and the findings do; item 5 does not.
**How the appended-later entries are stamped:** by a **dated group preamble naming the edit that
appended them** (item 3), not per-entry — and that preamble sits *before* item 5, so the file's
own demonstrated append point is **before** the `Sequence from here` closer, not after it.
**What kind of entries they are:** a **mix** — two practices, two findings, one sequencing
directive.

### A2 — the stop condition does not fire, and why

**The shape accommodates a standing obligation.** The demonstrating instance is **item 5**: a
forward-looking item with no basis and no §7 disposition already lives in the subsection under
its own bolded lead. The heading is *"Open for the next cycle"*, not *"Candidates for §7"*.

**And the document's counterpart section settles it independently.** `## Carried in`
(`:931–947`) is the inbound half of the same channel, described in its own preamble as inherited
*"from `docs/milestones/hc-consolidation.md` §Milestone summary → §Open for the next cycle"*.
What it carried into m5 is not only candidates: it carried a directive (*"This round does not
defer promotion to its close"*) and a standing carried item (BL-075 arm 2). A channel whose
inbound half demonstrably transports directives is not one whose outbound half holds candidates
only.

**The one thing that would have been bent, and was not.** Item 3's preamble is §7-scoped —
*"Two findings carried forward for the next cycle's §7"*. Joining the obligation to that group
would have misfiled it. So it landed under **its own dated stamp**, and it carries **no**
*"Carried rather than promoted"* line, because that line is a §7 disposition and an obligation is
not a §7 candidate. The subsection gained a third stamp, which is exactly the shape item 3
established for an append.

**The alternative home the preceding round named, not taken.**
`bl-132-row-correction-implementation-notes.md:250–252` offered `## Not established` as a second
candidate — R21 kind **(b)**, a carried unknown naming what would settle it and inventing no
owner. The reviewer's ruling names `### Open for the next cycle`; §Not established is untouched
and no view is offered on it here.

---

## 2. A3 — the obligation, as landed

**Form taken from:** the dated group preamble at `:1064–1068` **in the same file** (item 3
above) — a bolded lead naming what is carried, the date, and the edit that appended it, followed
by the entries.

**Position:** immediately before `Sequence from here`, which is where the body-addition edit put
its own append and which leaves the sequencing closer last.

**Substance quoted from the record, not paraphrased from the instruction** —
`cloudcost/docs/m5-t3-implementation-notes.md:485–491` at `0587bf3`, whose trigger reads
*"the next harness ticket whose `Touches` names any `.ex` or `.exs` file runs it; and if no such
ticket runs before the next cycle's close, that close runs it."*

**On the count.** The round instruction said the obligation is already recorded in **three**
other places. It is now **four**, and the entry states four. Three was true when
`bl-132-row-correction-implementation-notes.md` §2a enumerated them on 2026-08-11 — *"the notes
above, the summary narrative at `:1006–1008`, and the t3 ticket-set row at `:47`"* — and the act
of recording that enumeration created the fourth, `:231–240` of that same file, which quotes the
obligation verbatim while verifying it. The population, derived rather than assumed:

```
$ grep -rn -F "deferred, not skipped" --include=*.md . ../aetheris/
cloudcost/m5-n1-compose.md:47                            ← t3 ticket-set row
cloudcost/m5-n1-compose.md:1006                          ← summary narrative
cloudcost/m5-n1-compose.md:1104                          ← THIS ROUND's entry
cloudcost/docs/m5-t3-implementation-notes.md:485         ← the t3 record
cloudcost/docs/bl-132-row-correction-implementation-notes.md:234   ← the verification
```

> **[Corrected 2026-08-23 at BL-182's close.** The command in the block above was **wrong when
> written**; the population it reports was **right**, and it stands. `grep -r` rooted at `.` and
> `../aetheris/` descends into `../aetheris/priv/runs/*/overlay/work/work`, which is not readable.
> GNU grep reports `Permission denied` on stderr and **exits 2**; ugrep never goes there and
> **exits 0**. The matched lines are the same either way, so the difference is **invisible in the
> output and visible only in the status** — anything keying on exit code reads success for the
> author and failure for a reader. Re-run at this close: ten matching lines under both, `rc=0`
> with empty stderr under ugrep, `rc=2` with 1201 bytes of stderr under GNU grep. **The corrected
> form, byte-identical under either tool:**
>
> ```
> git grep -nF 'deferred, not skipped' -- '*.md'
> git -C ../aetheris grep -nF 'deferred, not skipped' -- '*.md'
> ```
>
> `git grep` searches tracked files, so the unreadable run directory is never entered and there is
> no error to swallow. Verified both ways at this close: byte-identical stdout, zero stderr on both
> sides, identical exit code. Recorded per **R32** — neither the original command nor its recorded
> output is rewritten. See **BL-182**. **]**

Four before, five after. That the count moved by being written down is the same mechanism §B
below is about, arriving on a different quantity.

---

## 3. B2 — the precision, and B3's report

### The HEAD unit, quoted before replacement

`cloudcost/m5-n1-compose.md:1079–1084` at `0587bf3`:

> **A negative-control token stops being a negative control once a record quotes it.** A
> sweep at the record-correction edit reused the token a prior edit had used for the same job
> and it returned three hits — the prior edit's own committed record, quoting its control
> table. Controls are minted fresh per sweep, or a sweep over records of prior sweeps finds
> its own instruments and reads them as content. Carried rather than promoted: one instance,
> found by the sweep it broke.

**Form taken from:** the G1 clause landing recorded at
`cloudcost/docs/m5-t3-implementation-notes.md:689–699` — one clause appended **inside** the
existing claim in the entry's own voice, not a second entry beside it. That landing extended the
entry's `Source:` line; this entry has no `Source:` line, so the dated attribution lands as a
bracket beneath the entry instead, and the disposition line keeps its place as the entry's close.

**Evidence named, from the record and not from the instruction:**
`cloudcost/docs/bl-132-row-correction-implementation-notes.md:156–160` (three controls minted
fresh *because this entry told that round to*, published, all three returning 0) and `:167–179`
(re-run over the tree after that commit: **1 each**, every hit the one line of its own record
that lists them).

### B3 — reported, not settled

**Does the entry now hold two instances of the underlying shape?** Yes. The original instance is
a sweep reusing a *prior* edit's token; the appended instance is a sweep minting *fresh* tokens
and spending them in the same act. They are the same shape at two depths: recording a control
publishes it, and publication is what disqualifies it.

**Does that change its §7 standing?** On a literal reading of §7's ≥2 bar, two instances of one
shape would clear it. **But the bar is not engaged**, and not because the count is short: what
landed is a **precision on an existing finding**, and a precision on a rule is not a rule — the
same ground on which the closed-row clause landed at t3 r1 (`m5-t3-implementation-notes.md`
§G1) without engaging §7. The second instance is evidence *for the entry*, not a second entry.

**Does *"carried rather than promoted"* still read true?** It reads true as a disposition and
false as an arithmetic. The finding is still carried and still unpromoted, which is what the
phrase disposes of. But *"one instance, found by the sweep it broke"* now sits under a paragraph
narrating a second one, so a reader meeting the line cold will find the entry counting against
itself.

**Left unchanged deliberately.** The disposition is the reviewer's and this round does not touch
it. The mitigation used instead: the appended clause names its instance explicitly and stamps
itself, so the entry is self-describing even while the count line is stale — and this paragraph
is where the discrepancy is recorded rather than left for a later reader to find.

---

## 4. C — the false claim

### C2 — the verification, run before the edit and independent of the preceding round's report

**The claim, at `cloudcost/docs/m5-t3-implementation-notes.md:485–491`:** *"**No home was
invented for it in the round document** — this document has no cross-cycle obligations section
and the ticket's instruction was to name one only if it exists."*

**It is false, and it was false in its own commit:**

```
$ git log --oneline -S"no cross-cycle obligations section" -- cloudcost/docs/m5-t3-implementation-notes.md
d0fb25a docs(m5 t3): the close — six clauses, five promotions, BL-137, §Milestone summary

$ git show d0fb25a:cloudcost/m5-n1-compose.md | grep -n "Carried in\|Open for the next cycle\|dialyzer"
918:## Carried in
993:**`mix dialyzer` is deferred, not skipped**, with a trigger that can fire — the next harness
1022:### Open for the next cycle

$ git log --oneline -S"### Open for the next cycle" -- cloudcost/m5-n1-compose.md
d0fb25a  (the same commit)
```

**t3 wrote the section, wrote the obligation into the summary, and wrote the sentence denying the
section existed — in one commit.** This is not a claim that went stale; it was wrong when
written. The preceding round reached the same conclusion at
`bl-132-row-correction-implementation-notes.md:245–255`; that was read **after** this derivation
and corroborates it rather than being relied on.

**What the round document carries, and at which anchors** (all at `0587bf3`, and all preceding
this round's append, so unmoved by it): `## Carried in` `:931`, the inbound half; `### Open for
the next cycle` `:1035`, the outbound half, which the document itself calls *"the subsection the
next cycle's §7 reads"* at `:1067–1068`; the obligation's own text `:1006–1008`; the t3
ticket-set row `:47`.

**The referent, reported rather than smoothed.** *"this document"* reads grammatically as the
notes file, which genuinely has no such section. The correction is written on the
round-document reading, which is the only one on which the clause does the work the sentence
before it asks of it — it is offered as the ground for *"No home was invented for it in the round
document"*. On the notes-file reading the sentence is true and supports nothing. Both readings
are named in the landed block.

### C3 — as landed

**Form taken from:** the dated correction block at `:636–675` **in the same file** (the
record-correction edit's block: bracket-stamp → **Superseded:** → the correct reading → what
follows from it). **Unchanged, per the instruction and on the merits:** the trigger's wording and
the deferral's reasoning. Only the claim about the round document is withdrawn.

---

## 5. D — BL-143 filed

### D1 — the derivation

```
$ grep -rhoE "BL-[0-9]{3}" . ../aetheris/ --exclude-dir=.git --exclude-dir=deps \
      --exclude-dir=_build --exclude-dir=node_modules --exclude-dir=target | sort -u | tail -3
BL-140
BL-141
BL-142
$ grep -rhoE "BL-[0-9]{4,}" … | sort -u        → (no output)
```

**Highest existing: BL-142.** 143 distinct three-digit refs; no four-digit refs. **`BL-999`
appears and is not a row** — it is the deliberately dangling ref in hc-d's `expected_fail` shape
test (`docs/reviews/hc-d-review.md:137`; `../aetheris/docs/aetheris/runbook.md:479` calls it
*"a row that does not exist in `docs/backlog-2026-06.md`"*). Backlog headings confirm
`### BL-142` is the tail. **Next free: BL-143.** The instruction's *"do not assume it follows
BL-142"* was right to demand the derivation and wrong about the outcome: it does follow BL-142.

### D2 — the row

Filed at the file's tail in the field shape the four most recent rows use
(`### BL-NNN — … (#TBD)` / Kind · Census items · Contract / Size · Priority / Section / body /
**Done when** / **Costs** / **Collides with** / `Source:` / `---`), minus their *"The item as
agreed and parked, verbatim"* clause, which belongs to BL-139–BL-142's parked-item provenance and
not to this row. `Kind: decision` is drawn from the vocabulary already in the file.

**Every `Source:` claim was verified before it was written.** The two that were re-derived at
HEAD for this round rather than taken from the preceding round's report:

- **No review file carries the reserved decision.**
  `docs/reviews/m5-cloudcost-t2-review.md` and `docs/reviews/m5-cloudcost-t3-review.md` each
  return **0** for a case-insensitive `manifest|G2|project_knowledge|export boundary`. **Control:**
  the same `manifest` term over `docs/reviews/` returns **35 files**, so the two zeros are absence
  and not a broken search.
- **Nothing schedules a refresh.** The agents repo has **no `.github` directory at all**; the
  harness's only workflow (`../aetheris/.github/workflows/ci.yml`) triggers on
  `workflow_dispatch` and `pull_request` — **no `schedule:` key**, and no manifest or
  `drift_check` step; no `cron`/`scheduled` hit in either repo concerns export; `sprint.sh` runs
  `drift_check` but no refresh.

---

## 6. The sweep

Run over both repos after A, B and C landed, in the same commit. **Vocabulary published before
counts**, per the standing rule.

**Terms — the premise A and C correct** (that the round document lacks a cross-cycle home):
`no cross-cycle obligations`, `cross-cycle obligations`, `home was`, `invented for it`.
**Terms — the premise B qualifies** (minting fresh as the remedy): `minted fresh`,
`fresh per sweep`, `negative-control token`.
**Term — A's population:** `deferred, not skipped`.
**Negative controls, minted fresh for this sweep:** `obligations subsection`, `dialyzer is owed`,
`unowned exemption`.

**Counts** (working tree, post-edit, this file excluded):

| Term | Hits | | Term | Hits |
|---|---|---|---|---|
| `no cross-cycle obligations` | 4 | | `minted fresh` | 5 |
| `cross-cycle obligations` | 4 | | `fresh per sweep` | 4 |
| `home was` | 5 | | `negative-control token` | 5 |
| `invented for it` | 5 | | `deferred, not skipped` | 5 |
| **`obligations subsection`** | **0** | | **`dialyzer is owed`** | **0** |
| **`unowned exemption`** | **0** | | | |

**What the sweep found.**

- **The A/C premise is asserted in exactly one place besides the unit corrected**, and it needs
  no correction: `bl-132-row-correction-implementation-notes.md:239` quotes the false sentence
  inside a block quote whose surrounding text (`:245–255`) states *"the notes' claim that it does
  not is wrong"*. A premise quoted in the course of refuting it is not a premise carried.
  `docs/milestones/hc-e-implementation-notes.md:506` (*"was invented for items 2, 3, 5 or 6"*) is
  the term's one false positive — R21 owner-invention, an unrelated subject.
- **The B premise is carried, uncorrected, at one site outside this round's `Touches`:**
  `cloudcost/docs/m5-headline-correction-implementation-notes.md:225–226` states the remedy in
  general present tense — *"Controls have to be minted fresh per sweep, or a sweep over records of
  prior sweeps will find its own instruments and read them as content"* — with no quotation frame
  around it. **Reported, not edited.** It is a committed, pushed record outside `Touches`, and a
  ticket's scoping is authoritative over a ticket's judgement. The general question of whether a
  correction owes a same-commit sweep for recurrences already has an executor in **BL-140**, so
  no second row is filed. The other B-term sites need nothing: `bl-132-row-correction:172` already
  states *"necessary and not sufficient"* (it is the source of the precision);
  `bl-132-row-correction:324–329` and `m5-body-addition:179` quote or list the entry as it stood,
  which a stamped quotation is entitled to do.

**On the controls, and what was done about B2's own point.** Minting them fresh is exactly the
step the clause above calls necessary and not sufficient, so performing it silently would have
been the ritual the finding is about. The three tokens returned 0 here and will return **1 each**
for the next round, from the vocabulary block in this file. The mitigation is to make the
re-run reproducible rather than to pretend the tokens survive: a successor re-deriving these
figures runs

```
git grep -c -F -e '<term>' -- . ':!cloudcost/docs/m5-obligation-landing-implementation-notes.md'
```

and gets this round's numbers back. What has to be fresh is the sweep's **reach**, not only the
token; the token is spent the moment this sentence is committed, and the pathspec is what
outlives it. This is stated rather than performed, per the round instruction.

---

## 7. E — read-back, no edit

Two annotations already sit on the narrowed readings of the correction rule. **Anchors resolved
rather than trusted:** both line ranges in the instruction were correct at `0587bf3`. The first
has since **shifted to `:669–708`** by the 33 lines §C3 inserted above it in the same file; the
second is unmoved. **Neither file is edited by this round** — the second is a review file, which
`Touches` does not name and R20 does not reach.

### E1 — `cloudcost/docs/m5-t3-implementation-notes.md:636–675` at `0587bf3`, verbatim

> **`[Corrected 2026-08-11 at the m5 record-correction edit. This is the FIRST of three
> occurrences of this misreading; the other two carry pointers here. Superseded wording left
> standing above per decision 7.]`**
>
> **Superseded:** *"The entry promoted at clause 1 … puts an in-place edit there out of
> bounds"*, and the sentence's framing that the promoted entry is what declined the edit.
>
> **The entry, quoted verbatim from the file rather than from memory of it** — harness
> `CLAUDE.md` §Continuous learning → Workflow patterns, read at harness `0ed9068`:
>
> > **An unpushed artifact may be corrected in place; a ratified one may not — the licence
> > comes from the artifact's kind, not from its push state.** Correcting an unpushed record
> > in place is sound: its claims become meaningful when someone reads them, so a dated
> > supersession block would preserve a reading history no reader ever had. A ratified
> > decision is different in kind. Its authority is the act of ratification rather than its
> > publication, so a reader citing it later is entitled to know its text is what was
> > ratified — and cannot learn that from a notes file they have no reason to open. Correct
> > it with a dated block that quotes the superseded wording in the position it occupied,
> > never silently, however few people have read it.
>
> **The correct reading.** The entry sorts artifacts by **kind**, and governs *how* each is
> corrected — never *whether*. A **record** is corrected in place. A **ratified** artifact is
> corrected too, with a dated block quoting the superseded wording in the position it
> occupied. **Publication withdraws the licence to correct silently, not the licence to
> correct** — which is what *"however few people have read it"* is doing in that sentence.
> **A review file is a record**, not a ratified decision: its authority is that someone reads
> it, which is the entry's own test for the in-place case. Nothing in the entry put this edit
> out of bounds.
>
> **The outcome was right and the ground was wrong, and both belong in the correction.**
> Declining to edit `docs/reviews/m5-cloudcost-t2-review.md` at t3 r1 was **correct** — it is
> not in t3's `Touches`, and a ticket's scoping is authoritative over a ticket's judgement.
> §Ticket set's conventions exempt *the round's own* review file, which is t3's, not t2's. So
> the decision stands and only its stated reason is withdrawn. The two were not distinguished
> at the time, and stacking a sound scoping ground under an unsound rule-reading is what let
> the misreading pass review.
>
> **The entry itself is not edited here** — see this round's record,
> `cloudcost/docs/m5-record-correction-implementation-notes.md` §H3(e), which reports one
> observation about its wording and deliberately leaves the promoted rule alone.

**What it does.** It **corrects** the narrow reading — it does not merely record that one was
taken. It names the superseded wording and the framing behind it; quotes the governing entry
verbatim from the file with a harness stamp; states the correct reading in its own paragraph; and
separates the decision (which stands) from its stated reason (which is withdrawn). Two further
things it does, reported as facts about the text: it **classifies the misreading as the first of
three occurrences** and asserts the other two carry pointers to it; and the entry it quotes as the
authority is the rule's **pre-correction headline**, stamped `0ed9068` — the same headline the
harness `CLAUDE.md` corrected on the same date, which the block's own *"correct reading"*
paragraph is arguing against rather than from.

### E2 — `docs/reviews/m5-cloudcost-t3-review.md:127–134`, verbatim

> `[Corrected by pointer 2026-08-11 at the m5 record-correction edit. **The promoted entry did
> not put that edit out of bounds** — it sorts artifacts by kind and governs *how* each is
> corrected, never *whether*; publication withdraws the licence to correct **silently**, not
> the licence to correct, and a review file is a **record**. **Declining was still right**, on
> the ground the sentence above also gives: the file is not in t3's `Touches`. Only the
> rule-reading half is withdrawn. Full correction, with the entry quoted verbatim, at
> `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → *The one claim that does not hold* —
> the first of this misreading's three occurrences.]`

**What it does.** It **corrects by pointer**, which is what it calls itself: it states the
correction's substance in compressed form — the kind/push-state distinction, the *how*-not-*whether*
reading, the review-file-is-a-record classification — withdraws the rule-reading half explicitly,
preserves the decline on its surviving ground, and routes to the full correction by document,
section and heading. It carries no quotation of the governing entry, which is what it delegates.
It does **not** restate the superseded wording; the sentence it corrects sits immediately above
it in the same file and is left standing.

**No judgement is offered on whether either is sufficient, and nothing here is acted on.** The
ruling is the reviewer's.

---

## 8. Deviations

**None from the round instruction's scoping.** Four paths changed, all named in `Touches`:
`cloudcost/m5-n1-compose.md` (§Milestone summary → `### Open for the next cycle` only),
`cloudcost/docs/m5-t3-implementation-notes.md` (the false claim's unit only),
`docs/backlog-2026-06.md` (one new row at the tail only), and this file. Nothing in
`cloudcost/milestone.md`, either `CLAUDE.md`, any review file, or any methodology document. No
review file. No second backlog row. Nothing acted on from §7.

**One item reported rather than fixed, named here so it is not read as an omission:** the B
premise at `m5-headline-correction-implementation-notes.md:225–226` — §6 above.

**Three inaccuracies in the round instruction**, each acted on in its corrected form: the
obligation's other homes are **four**, not three (§2); the next free row **does** follow BL-142
(§5); and *"this document"* in the corrected claim is **ambiguous**, false only on the
round-document reading (§4). E's two line ranges were correct, and the contract refs are not
misnumbered.

---

## 9. Done-check

`Both items run post-commit, which is where check 8 can compare this commit against the manifest.
Recorded here and then folded into the same commit by amend, so the round stays one commit; the
drift figures below were taken at the pre-amend SHA and re-run after the amend, and the only
difference between the two runs is the SHA in the backlog row's WARN — reported below rather than
left for a reader to reconcile.`

### 1. The offline pytest spine

```
$ python3 -m pytest cloudcost/tests/ -v
…
======================= 386 passed in 143.47s (0:02:23) ========================
exit 0
```

**386 passed — unchanged**, and it is the same figure t1, t2 (both rounds) and t3 recorded. This
round changed no executable line, so a move here would have been a finding; there is none.

### 2. `drift_check.py --strict`

```
$ python3 scripts/drift_check.py --strict
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
[WARN] project_knowledge: cloudcost/milestone.md stale — manifest=eae14d4 current=8f36e45
[WARN] project_knowledge: CLAUDE.md stale — manifest=dcf1d42 current=d025971
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=7dbdb7d current=ec9e1bf
[WARN] project_knowledge: CLAUDE.md stale — manifest=2ef0517 current=6241972
[PASS] command_fields: 11 documented §4 structs (56 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  4 WARN  7 INFO
exit 0
```

**8 PASS · 0 FAIL · 4 WARN · 7 INFO, exit 0. Neither count moved**, which is what was expected
and is stated as the expectation being met rather than as a result discovered.

**All four WARNs are the declared `project_knowledge` staleness exemption, named and not chased.**
Three are inherited unchanged from the m5 close; **one advanced to this commit** —
`docs/backlog-2026-06.md`, `manifest=7dbdb7d current=ec9e1bf` — because it is the only
manifest-tracked path this round touches. The other three touched paths
(`cloudcost/m5-n1-compose.md`, `cloudcost/docs/m5-t3-implementation-notes.md`, this file) carry no
manifest row, which is why the count stayed at four rather than rising. **That these four have no
owner and no clearing schedule is the subject of BL-143**, filed by this round; naming them here
is the exemption working as declared, and is not a claim that anything will clear them.

**The strict invariant asserted is "zero *unexplained* WARNs", not "zero WARNs"** — zero FAIL,
and every WARN accounted for above. Post-amend re-run: **identical, 8 PASS · 0 FAIL · 4 WARN ·
7 INFO, exit 0**, with the backlog row reading `current=<amended SHA>`.

### 3. Both repos' state

**Agents:** one commit, working tree clean, **push held**. **Harness:** untouched — no commit,
nothing staged, still level with `origin/main` at `6241972`. The round is agents-only by
`Touches`, and the harness `CLAUDE.md` was read and quoted but not edited.
