# m5 — the record-correction edit — implementation notes

`Dated 2026-08-11. A reviewer-authored edit correcting two claims in m5's committed records.
Per R20 this edit is not a ticket round and gets no review file; this file is its committed
record, and the reviewer's finding lands here in a dated ## Review section.`

## m5 is not reopened

**The round is closed and its work stands.** Every clause of §Close criteria, every promotion,
BL-137, and §Milestone summary are untouched by this edit. What changes is two *claims made
about* that work inside its records. A later reader meeting this commit after the close should
read it as a correction to a record, not as a reopened round — no ticket was opened, no
`Touches` was amended, no gate was re-run, and no promoted rule was edited.

## Filename

`m5-record-correction-implementation-notes.md`. **The suffix matches the directory's dominant
pattern**: `ls cloudcost/docs/` returns 31 files, **29** ending `-implementation-notes.md`. The
two exceptions are `m3-linode-scout.md` and `m5-scoping-landing-notes.md`. The stem follows the
m5 non-ticket-edit convention already in the directory — `m5-close-anatomy-`, `m5-pin-edit-`,
`m5-ruling-edit-` — which names the edit rather than a ticket.

## Measurement stamp

Every count and `path:line` here was derived at **agents `d025971`** and **harness `0ed9068`**,
before this edit's own changes. The harness was opened **read-only**, to quote its `CLAUDE.md`;
it is not written this round. Per **m5-D1**, a line number appears only where the claim is about
a line.

---

## H1 — the sweep, run before any edit

**Population, derived by command** (`ls -1 docs/reviews/m5-* cloudcost/docs/m5-*
cloudcost/m5-n1-compose.md`) — **11 files**, enumerated:

```
cloudcost/docs/m5-close-anatomy-implementation-notes.md
cloudcost/docs/m5-pin-edit-implementation-notes.md
cloudcost/docs/m5-ruling-edit-implementation-notes.md
cloudcost/docs/m5-scoping-landing-notes.md
cloudcost/docs/m5-t1-implementation-notes.md
cloudcost/docs/m5-t2-implementation-notes.md
cloudcost/docs/m5-t3-implementation-notes.md
cloudcost/m5-n1-compose.md
docs/reviews/m5-cloudcost-t1-review.md
docs/reviews/m5-cloudcost-t2-review.md
docs/reviews/m5-cloudcost-t3-review.md
```

### H1(a) — the location claim: 2 genuine occurrences

Vocabulary: `both repos|in both \`?CLAUDE|standing rule in both|rule in both|harness.{0,40}deferred
finding|deferred finding.{0,60}harness`. **11 raw hits, 2 genuine.**

| # | File · section | The sentence |
|---|---|---|
| **1** | `cloudcost/docs/m5-t2-implementation-notes.md` · the r0 section, the paragraph closing *"BL-070 is the executor this ticket could reach"* | *"a standing rule in **both repos** is that a deferred finding gets an executor in the round it is deferred"* |
| **2** | `docs/reviews/m5-cloudcost-t2-review.md` · §*F1 — accepted* | *"The standing rule in **both repos** — a deferred finding gets a backlog row in the same round it's deferred; prose in a packet or notes files nothing"* |

**Nine raw hits discarded, each read rather than pattern-matched away**: five are `both repos`
about something else entirely — a scratchpad *"outside both repos"*, two `git status --short`
**in both repos** done-check lines, a *"grepped across both repos"*, and two file-population
counts (*"204 git-tracked `.py` files in both repos"*, *"every git-tracked file in both
repos"*). One is `cloudcost/m5-n1-compose.md`'s `Contract refs` naming *"both repos' `CLAUDE.md`
learning sections"* — a normative pointer, not this claim. **Two are statements *about* the wrong
claim rather than instances of it** — `m5-t3-implementation-notes.md` and
`docs/reviews/m5-cloudcost-t3-review.md` each quote *"The standing rule in both repos"* in the
course of correcting it, and correcting a claim is not repeating it.

### H1(b) — the rule-reading claim: 3 genuine occurrences

Vocabulary: `out of bounds|ratified-artifact rule|ratified artifact|unpushed artifact|
unpushed-vs-ratified|corrected in place; a ratified`. **9 raw hits, 3 genuine.**

| # | File · section | The sentence |
|---|---|---|
| **1** | `cloudcost/docs/m5-t3-implementation-notes.md` · §r1 → *The one claim that does not hold* | *"The entry promoted at clause 1 … **puts an in-place edit there out of bounds**, and r1's `Touches` does not name it either."* |
| **2** | `docs/reviews/m5-cloudcost-t3-review.md` · §*F1 — accepted* | *"this round's own promoted entry says a **ratified artifact is superseded with a dated block rather than edited**"* |
| **3** | `cloudcost/m5-n1-compose.md` · §Ticket set, t3's row, the r1 clause | *"so it is recorded rather than edited — **this round's own ratified-artifact rule applied to itself**"* |

**Six raw hits discarded.** Three are the rule's *own text* or bookkeeping about it —
§Promotion candidates' third entry, the §Milestone summary clause-1 table row, and t3's
read-back table and candidate enumeration. **Two are `m5-close-anatomy-implementation-notes.md`
using the rule correctly** and predating its promotion: *"Rewriting a ratification to fit the
file would be the error m5's own §Promotion candidates entry on ratified-vs-unpushed artifacts
describes"* — that is about rewriting a **ratification**, which is what the entry actually
governs, so it is a right reading and is left alone. **This is the discrimination the sweep
existed to make**: a vocabulary sweep finds the words, and only reading each hit separates an
instance of the error from a correct use of the same vocabulary.

### The harness, swept with the same vocabulary

```
../aetheris/CLAUDE.md:935  "…of this class across both repos, five of them into §7's own list…"   → not the claim
../aetheris/CLAUDE.md:956  the promoted entry itself                                              → source text, not a reading
```

**No occurrence of either corrected claim in the harness**, and it is not written this round.
Controls for the zeros are in H2's derivation below — `ratified` 7 and `in place` 3 in that
file, so the vocabulary is present and the absence is real.

---

## H2 — the location claim

### H2(a) — the fact, re-derived at HEAD

Not carried from the last packet. `grep -c` over each repo's `CLAUDE.md`, agents `d025971` /
harness `0ed9068`:

```
"deferred finding"                        harness=0   agents=1
"backlog row"                             harness=0   agents=1
"gets a backlog row in the same round"    harness=0   agents=1

positive controls   "Source:"             harness=55  agents=35
                    "CLAUDE.md"           harness=11  agents=8
                    "ratified"            harness=7   agents=1
negative control    "zzz-not-a-real-rule" harness=0   agents=0
```

**The positive controls fire in both files and the negative control in neither**, so the three
harness zeros are absence, not a broken search. The single hit is agents `CLAUDE.md`,
**§Learning — BL-007**: *"A deferred finding gets a backlog row in the same round it's deferred
— prose in a packet or notes files nothing."*

### H2(b) — the full correction, and why that occurrence

**Occurrence 1, `cloudcost/docs/m5-t2-implementation-notes.md`.** *First in document order on
both available orderings, which agree*: it comes first in the derived population enumeration,
and it is the earlier by authorship — it sits in that file's **r0** section, above the `## r1`
heading, whereas occurrence 2 was written at t2 **r1**. Stated because "document order" over a
multi-file population needs a criterion.

**The unit, before** — the closing sentence of the paragraph on BL-070's disposition:

> Named here because a standing rule in both repos is that a deferred finding gets an executor
> in the round it is deferred, and BL-070 is the executor this ticket could reach.

**The unit, after** — the sentence is **left byte-unchanged**, and a dated block is appended
beneath it carrying: the superseded wording quoted in the position it occupied, the correct
fact, H2(a)'s derivation as its truth-maker, and the scope of the withdrawal.

**Where the insertion falls.** Immediately after that paragraph's final sentence and **before
the `---` rule** that closes the r0 section and precedes the `## r1 — the claim corrected, the
Touches amended, the review file` heading. It lands **inside** the paragraph's own subsection
rather than at the head of §r1. The paragraph carries no `Source:` line — it cites its evidence
inline and keeps it — so nothing was separated from an attribution, and the block carries its
own dated stamp rather than borrowing one.

### H2(c) — the pointer

**Occurrence 2, `docs/reviews/m5-cloudcost-t2-review.md` §*F1 — accepted*.** Sentence left
byte-unchanged; a short dated pointer appended, in the shape
`m5-close-anatomy-implementation-notes.md` §r2 uses — a backticked `[Corrected by pointer
<date> at <edit>, …]` block naming what is wrong, where the full correction lives, and why a
pointer rather than a rewrite. **Where it falls:** after that paragraph's last sentence, before
the `**What landed.**` paragraph that follows; both neighbours byte-unchanged.

**One full correction and one pointer, not two full corrections** — so the derivation has a
single home and cannot come to disagree with itself.

### H2(d) — what is not withdrawn

**A rule standing in one repo is still standing.** Both corrections say so explicitly. The
sentences' *point* — that BL-070 was a real executor and the rule bound that ticket — is
untouched, and it bound it either way: the session that wrote it works in the agents repo,
which is where the rule is. Only the reach, asserted as two repos on no derivation, is
corrected. No surrounding argument is rewritten.

---

## H3 — the rule-reading claim

### H3(a) — the entry, quoted verbatim from the file

Read from harness `CLAUDE.md` §Continuous learning → Workflow patterns at `0ed9068`, **not
taken from the instruction** — the correction's whole subject is a reading taken at second
hand, so taking the text at second hand again would reproduce the error inside its own fix.

> - **An unpushed artifact may be corrected in place; a ratified one may not — the licence comes
>   from the artifact's kind, not from its push state.** Correcting an unpushed record in place
>   is sound: its claims become meaningful when someone reads them, so a dated supersession
>   block would preserve a reading history no reader ever had. A ratified decision is different
>   in kind. Its authority is the act of ratification rather than its publication, so a reader
>   citing it later is entitled to know its text is what was ratified — and cannot learn that
>   from a notes file they have no reason to open. Correct it with a dated block that quotes the
>   superseded wording in the position it occupied, never silently, however few people have read
>   it.
>   `Source: m5-cloudcost, the BL-131 ruling edit r1, 2026-08-10 — claude-code flagging its own
>   compliance with a reviewer instruction that pointed the other way. One recorded instance, and
>   the word is one: a later round reading this rule and finding it silent on a case is an
>   application, not a second finding. Below §7's ≥2-ticket bar and promoted anyway by explicit
>   ratification at the m5 close, on the human's referral of the question to the reviewer. The
>   ground, because "the human said so" is not one: §7's bar is a frequency filter, and frequency
>   is the wrong filter for a failure that bites rarely and irreversibly — silently altering a
>   ratified decision does not recur its way to attention, it recurs by going unnoticed. Same
>   exception form as the credential rule below, which states the same ground from the other
>   direction. Harness rather than agents because the record-integrity family it belongs beside
>   lives in this file; duplication into both files was considered and declined — the two
>   preambles are near-duplicates with no byte-identity check, and drift_check has none either.`

### H3(b) — the correct reading, against that text

**The entry sorts artifacts by kind and governs *how* each is corrected — never *whether*.**

- **A record** is corrected **in place**: *"Correcting an unpushed record in place is sound."*
- **A ratified artifact** is corrected too, and differently: *"Correct it with a dated block
  that quotes the superseded wording in the position it occupied, never silently."*
- **Publication withdraws the licence to correct *silently*, not the licence to correct.** That
  is the work *"however few people have read it"* does in the final sentence — it forecloses the
  argument *nobody has read it, so a silent fix loses nothing*, which is the argument the
  session that wrote the entry had itself made and flagged.
- **A review file is a record**, not a ratified decision. Its authority is that someone reads
  it, which is precisely the entry's own test for the in-place case.

**Nothing in the entry put the t2 review file's correction out of bounds.** The misreading
inverted the rule: it read a rule about *method* as a rule about *permission*.

### H3(c) — the outcome was right, the ground was wrong, and both are recorded

**Declining to edit `docs/reviews/m5-cloudcost-t2-review.md` at t3 r1 was correct.** It is not
in t3's `Touches`, and **a ticket's scoping is authoritative over a ticket's judgement** — the
very practice t3 r1 had, in the same commit, argued was already carried by §6. §Ticket set's
conventions exempt *the round's own* review file, which is t3's, not t2's.

**So the decision stands and only its stated reason is withdrawn.** The failure worth naming is
not the decline; it is that a sound scoping ground and an unsound rule-reading were stacked
together and presented as one reason. A correct outcome makes a wrong ground very hard to see —
nothing downstream was wrong, so nothing downstream flagged it.

### H3(d) — first plus pointers

**Occurrence 1 — `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → *The one claim that does
not hold*.** First in the derived population order (all three were written in the same commit,
`d025971`, so authorship does not order them and the enumeration does). Sentence left
byte-unchanged; a dated block appended carrying the superseded wording, the verbatim entry, the
correct reading, and the right-outcome/wrong-ground split. **Where it falls:** after that
paragraph, before the `### G1 — the clause` heading — inside the subsection it qualifies.

**Occurrence 2 — `docs/reviews/m5-cloudcost-t3-review.md` §*F1 — accepted*.** Dated pointer
appended after the paragraph, before `**§6's `Touches` field carries the declined practice…**`.

**Occurrence 3 — `cloudcost/m5-n1-compose.md` §Ticket set, t3's row.** Dated pointer appended
inline within the row's r1 clause, immediately after the superseded phrase, since a table row
has no sub-units to insert between. **It also carries the phrase *"which does not reopen
m5"***, because §Ticket set is the one place a reader meets the round's state and a post-close
correction there is the most likely thing to be misread as a reopening.

### H3(e) — the promoted entry needs no change; one observation, reported not acted on

**Confirmed: no change to the entry, and it is not edited this round.** The correct reading is
recoverable from its text, which is the test.

**But quoting it did show something worth reporting, and this is the reserved case.** The
entry's **headline** says *"a ratified one may **not** [be corrected in place]"*, while its
**body** instructs *"Correct it with a dated block that quotes the superseded wording **in the
position it occupied**"* — which is an in-place correction. The headline reads as a prohibition
on correcting in place; the body means *may not be corrected in place **silently***. **The
headline is the shorter thing, and the shorter thing is what gets remembered** — the misreading
one commit later quoted the headline and not the body.

**Not edited, deliberately.** The instruction reserves this: report rather than edit a promoted
rule inside a correction round, and the reason is good — an entry rewritten inside the round
correcting a misreading of it cannot afterwards be distinguished from an entry rewritten *to
make the misreading wrong*. **It is the reviewer's call** whether the headline is worth a
clause. Recorded here so the option is owned rather than lost.

---

## Deviations

**None.** Five paths changed, all inside this edit's own scope as the instruction defines it:
`cloudcost/docs/m5-t2-implementation-notes.md`, `cloudcost/docs/m5-t3-implementation-notes.md`,
`cloudcost/m5-n1-compose.md`, `docs/reviews/m5-cloudcost-t2-review.md`,
`docs/reviews/m5-cloudcost-t3-review.md`, plus this record *(new)*.

**The harness is read-only this round** — opened only to quote `CLAUDE.md` at H3(a). Its HEAD is
`0ed9068`, unchanged, and its tree is clean. There is nothing to push there.

**No ticket was opened**, no `Touches` amended, no gate re-run, and no promoted rule edited.

---

## Review

`Dated 2026-08-11. Per R20 this edit gets no review file; the reviewer's finding lands here,
verbatim, with the disposition beneath it.`

- **A rule misread one commit after promoting it.** *Finding, raised by the reviewer:
  t3 r1 declined to correct a pushed record on the ground that this round's own
  promoted entry put the edit out of bounds. The entry says the opposite for a record —
  correct it, but never silently.* **Disposition: corrected at this edit.** The outcome
  was right on scoping and the ground was wrong on the rule, and the two were not
  distinguished. Worth the round on its own terms: a rule read narrowly one commit
  after it lands is a rule that means something narrower next cycle, and the misreading
  was recorded in the same file that promotes it.

**Accepted in full, and one thing the finding's last clause makes sharper.** *"The misreading
was recorded in the same file that promotes it"* is the part that decides this was worth a
round rather than a note. `cloudcost/m5-n1-compose.md` carries both the entry's candidate text
in §Promotion candidates **and**, in t3's row, the misreading of it — so the document a later
session opens to learn what m5 ruled would have taught the narrow reading in the same breath as
the rule. That is the *"content in any other channel does not exist"* failure inverted: not a
claim that failed to travel, but a wrong claim travelling in the best-carried channel there is.

**And the misreading was self-serving in a way worth naming rather than glossing.** The narrow
reading produced the cheaper action — record it and move on, instead of correcting two pushed
files. A misreading that happens to license less work is the kind that survives review, because
nothing downstream of it looks wrong. That is the same shape as this round's first promoted
entry, one level over: not a check blind to its subject, but a *reading* whose blind spot fell
exactly where the work was.
