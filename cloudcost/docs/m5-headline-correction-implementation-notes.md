# m5 — the headline correction on the correction rule — implementation notes

`Dated 2026-08-11. A reviewer-authored edit correcting one sentence of a promoted rule in the
harness CLAUDE.md, plus two pointers in the agents repo. Per R20 this is not a ticket round and
gets no review file; this file is its committed record. m5 is not reopened — the round is closed
and its work stands; this edit changes a rule's wording, not the round's findings.`

## Filename

`m5-headline-correction-implementation-notes.md`. **Convention checked, not assumed:** `ls
cloudcost/docs/` → 32 files, **30** ending `-implementation-notes.md`; the two exceptions are
`m3-linode-scout.md` and `m5-scoping-landing-notes.md`. The stem follows the directory's m5
non-ticket-edit series — `m5-close-anatomy-`, `m5-pin-edit-`, `m5-ruling-edit-`,
`m5-record-correction-` — each naming the edit rather than a ticket.

## Measurement stamp

Derived at harness `0ed9068` and agents `9b24b77`, before this edit's own changes. The entry was
read **from the harness file**, not from the instruction that describes it — that guard is what
surfaced the finding in the first place, and dropping it here would reproduce the error inside
its own fix.

---

## Gate on the instruction

Four claims checked. **Three hold; one needs a precision, and it is the one the instruction rests
its "change no other sentence" on.**

1. **Both SHAs pushed and unchanged** — harness `0ed9068`, agents `9b24b77`, each equal to
   `origin/main`, `origin/main..main` at 0, both trees clean. **Holds.**
2. **Defect 1: *"in place"* is used in two senses.** **Holds.** The headline's *"may be corrected
   in place; a ratified one may not"* excludes the ratified case, so there *in place* must mean
   **the text is rewritten** — otherwise the ratified case, which does place a dated block at that
   position, would not be excluded. The body's *"a dated block that quotes the superseded wording
   in the position it occupied"* means **a block added at that position, text preserved.** The
   entry never says which sense is in play.
3. **Defect 2: denying push state any force is true of a ratified decision and false of a
   record.** **Holds.** Ratified: *"never silently, however few people have read it"* — push state
   is explicitly given no force. Record: *"Correcting an **unpushed** record in place is sound:
   its claims become meaningful when someone reads them, so a dated supersession block would
   preserve a reading history no reader ever had"* — the entire licence for silence turns on
   *unpushed*.
4. **"The body already states all three cases correctly."** **Needs a precision. The body states
   two cases and entails the third.**

### The precision, and why it does not stop the edit

**Stated in the body:** the *unpushed record* case, and the *ratified decision* case.
**Not stated:** a **published record** as its own case. The body never names one.

```
$ grep -c 'Correcting an unpushed record in place is sound'  → 1     (case 1, stated)
$ grep -c 'A ratified decision is different in kind'         → 1     (case 3, stated)
$ grep -oE '(published|pushed) record'                       → 1 hit, and it is a SUBSTRING
                                                                of "unpushed record" at :957
```

`[The one apparent hit for case 2 is the substring trap — "pushed record" inside "unpushed
record". Caught by locating it rather than counting it, which is the field-not-substring rule
applied to this edit's own check. Case 2 is genuinely unnamed.]`

**The third case is *entailed*, not stated.** The body's licence for silence is that a
supersession block *"would preserve a reading history no reader ever had"* — a reason that lapses
exactly when readers did have one. So publication withdrawing the licence to be silent follows
from the body's own stated reason; the body just never spells the case out.

**This does not require changing the body, and the edit proceeds.** The new headline claims
*kind → how* and *push state → only whether silent*. Both are supported: the two stated cases give
the first, and case 1's stated reason plus the ratified clause's *"however few people have read
it"* give the second. **The headline does not overreach the body, and it introduces no gap that
was not already there** — case 2 was entailed-not-stated before this edit and is entailed-not-
stated after it. Spelling case 2 out would be changing a body sentence, which the instruction
forbids at J2(c) and reserves at J2(d). **Reported here rather than acted on.**

---

## J1 — the diagnosis, as the instruction sharpens it

Both defects are **one failure: a two-axis rule compressed into a one-axis headline.** The rule
runs on *kind* (what method a correction uses) and on *push state* (whether it may be silent). The
old headline named one axis and denied the other, and used a phrase — *in place* — that means
different things on each side of it.

**Why an ambiguity is worse here than a falsehood would be.** A false headline gets caught by
anyone who reads the body. An ambiguous one does not: **both readings are ordinary English, so a
reader who resolves it wrongly has no signal that they resolved anything at all.** The misreading
one commit later took the cheaper resolution — a prohibition, which licensed less work — and
nothing downstream looked wrong, which is why it survived a review.

---

## J2 — the correction

### J2(a) — the entry as it stood, quoted from the file at harness `0ed9068`

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

### J2(b) — the headline replaced, and nothing else

**Before:**

> **An unpushed artifact may be corrected in place; a ratified one may not — the licence comes
> from the artifact's kind, not from its push state.**

**After:**

> **An artifact's kind decides how a correction is made; its push state decides only whether the
> correction may be silent.**

### J2(c)/(d) — proof that no other sentence changed

Asserted by check, not by reading the diff. Both versions of the entry were joined, hand-wrap
collapsed, and the headline stripped from each:

```
old entry starts with the old headline : True
new entry starts with the new headline : True
BODY + Source, headline stripped, identical : True     (1680 chars vs 1680)
old headline present anywhere in the new file's entry : False
new headline count : 1
```

**`Source:` untouched** — it is the rule's provenance; this wording's provenance is the dated
block below. Whole-file delta: **+22 lines**, all of them the new block plus the headline's
re-wrap.

`[A first check reported the body as changed and was wrong: it compared line ranges, and line 957
carries the headline's second line *and* the body's first sentence, so a headline edit moves it
whatever the body does. Replaced by the text comparison above, which is what the claim is actually
about. Named rather than dropped — a check that answers a different question than the claim is
the shape this whole round is about.]`

### J2(e) — the dated block, as landed

> `[Corrected 2026-08-11, the headline sentence only. It previously read "An unpushed artifact may
> be corrected in place; a ratified one may not — the licence comes from the artifact's kind, not
> from its push state." Two compressions, one failure — a two-axis rule stated on one axis.
> **(1) "in place" carried two senses and the headline never said which**: there, the text is
> rewritten; in the body — "a dated block that quotes the superseded wording in the position it
> occupied" — a block is added at that position and the text is preserved. Both are ordinary
> English, so the headline was not false but ambiguous, and a reader resolving the ambiguity the
> cheaper way got a prohibition where the rule means a method. **(2) Denying push state any force
> is true of a ratified decision — never silently, however few have read it — and false of a
> record**, where push state is the operative fact: the body licenses silence for an *unpushed*
> record precisely because no reader had a reading history to lose, so publication withdraws that
> licence. One axis was named and the other denied, when the rule runs on both.
> **The body is unchanged and was never wrong** — it is the authority this correction was derived
> from, and rewriting it to match a new headline would have destroyed the evidence that it was
> right all along. **The sequence, on the page rather than left to be reconstructed:** the
> correction was made *after* and *because of* a misreading that quoted the headline and not the
> body — `../aetheris-agents/cloudcost/docs/m5-t3-implementation-notes.md` §r1, where the entry was
> read as putting an in-place edit "out of bounds", corrected at the m5 record-correction edit
> (agents `9b24b77`), whose §H3(e) reserved this wording question to the reviewer rather than
> settling it inside the round that found it. A rule clarified after a misreading and a rule
> reshaped to defeat one are indistinguishable unless the order is dated, so it is.]`

**On the objection this block answers.** My §H3(e) held that an entry rewritten inside the round
correcting a misreading of it cannot afterwards be told apart from an entry rewritten to make the
misreading wrong. **That objection is answered rather than overridden, and the answer is the
block**: the sequence is dated on the page — misread at t3 r1, misreading corrected at the
record-correction edit, wording question *reserved* there and settled here by the reviewer. The
objection was about an unrecoverable ordering; an ordering that is written down is recoverable.

### J2(f) — where the insertion falls

**After the entry's `Source:` line and before the next top-level claim** (*For any ticket whose
Done-when names a user-facing action…*), indented two spaces so it sits **structurally inside this
bullet** rather than orphaned between two entries. **Both neighbours byte-unchanged**, checked:

```
neighbour ABOVE (A claim that lands in the same commit… + its Source) identical : True
neighbour BELOW (the click-through merge-gate entry)               identical : True
```

**No claim was separated from its attribution.** The block is placed *after* the `Source:`, not
between the claim and it — the arrangement §Carried in's first rule exists to protect.

`[One cosmetic residue, named rather than left to be noticed: line 957 now runs ~74 characters
where the file wraps at ~98, because the new headline is shorter than the old one and the body's
first sentence continues on the same line. Re-wrapping would have touched body lines to no
purpose; byte-identical body text is the stronger property and was kept.]`

### J2(g) — read back out of the file

Performed after landing, from the file, pattern
`grep -n -B4 -A45 "An artifact's kind decides how a correction is made"` over
`../aetheris/CLAUDE.md`. **One hit**, with the preceding entry's closed `Source:` visible above it
and the following entry's claim visible below. Quoted in the packet.

---

## J3 — the sweep for the old headline

**Population, 14 files**, derived by command: the round's committed records
(`docs/reviews/m5-*`, `cloudcost/docs/m5-*`), `cloudcost/m5-n1-compose.md`, and **both** repos'
`CLAUDE.md`.

**Controls.** Positive: `m5-D2` → 6 of 14 files, so the corpus is searchable.
Negative: `qqx-nonexistent-token-8831` → 0.

`[The negative control had to be replaced mid-sweep, and the reason is worth recording. The first
one used was "zzz-not-a-real-rule" — the token the record-correction edit used for the same job —
and it returned **3**, because that edit's committed record quotes its own control table. **A
negative-control token stops being a negative control the moment a record quotes it.** Controls
have to be minted fresh per sweep, or a sweep over records of prior sweeps will find its own
instruments and read them as content.]`

`[Qualified 2026-08-11 at the readership-landings edit. The sentence above stands; what follows is
a qualification it does not carry, added in place because this file **has later readers** — two
later commits cite these lines by number and attribute their content (`9a2ae47`, `4caa671`), which
is the test that decided this edit should happen at all. **The remedy as stated is stated too
generally.** *"Controls have to be minted fresh per sweep"* is necessary and this cycle has since
qualified it twice. **(1) Minting fresh is not sufficient**: recording a control is what spends it,
and recording is a step every round performs by rule, so a round that mints fresh still hands its
successor dead tokens — established at the obligation-landing edit against the BL-132
row-correction sweep, whose three fresh controls returned 0 when published and 1 each afterwards.
**(2) A freshly minted, never-published token can still fail**, by colliding with ordinary English
another document independently wrote — the disposition-ground edit's `rests on a single instance`
returned 1 at `cloudcost/m4-consolidation.md:765` with nothing having ever used it. **What survives
both qualifications is not freshness but verification**: run the control and confirm it returns 0
*before* relying on it. Both qualifications and their sources are carried in
`cloudcost/m5-n1-compose.md` §Open for the next cycle, on this finding's entry.]`

### The split: 16 hits, **2 pointered, 14 left**

**Pointered — quotes the old headline as authority:**

| File · unit | What it does |
|---|---|
| `cloudcost/docs/m5-ruling-edit-implementation-notes.md` · the *"Its worked case is checkable in this file"* paragraph | *"which is why **the entry says the licence comes from the artifact's kind and not from its push state**, and why fixing them is not what it asks for"* — leans on the superseded clause to reach a conclusion. |
| `cloudcost/m5-n1-compose.md` · §Promotion candidates, third entry | The candidate's own headline, plus its closing *"the licence comes from the artifact's kind, not from its push state"* — states the rule in superseded wording. Named by the instruction. |

**Where each pointer falls.** In the ruling-edit notes, after that paragraph's last sentence and
before the `---` closing the section, inside the unit it qualifies. In §Promotion candidates,
**after the entry's `[PROMOTED 2026-08-10 …]` disposition block, as the entry's last block** —
not between the `[Filed …]` note and the disposition, where it first landed. **Corrected before
commit**: an 2026-08-11 block above a 2026-08-10 one reads as out of sequence, and the pointer
referred to *"the promoted entry"* above the block that records the promotion. Both neighbours
byte-unchanged either way.

Both pointers say **what is superseded and what is not**. The ruling-edit conclusion is
explicitly **not withdrawn**: none of the three artifacts it discusses is a ratified decision, so
the *kind* axis governs them, which is what that paragraph concludes — only the clause it leans on
was reworded. The candidate is **not rewritten**: it is what was filed, and a candidate edited to
match what it became stops being evidence of what was ratified.

**Left — 14 hits, each read rather than pattern-matched:**

- **Quotations of the headline *as the superseded wording under correction*** — `m5-t3-…:632` and
  the block at `:646` (which is stamped *read at harness `0ed9068`*, so it is accurate as
  history), `m5-record-correction-…:182` (§H3(a)'s verbatim quotation of the subject), and the
  new dated block in harness `CLAUDE.md` itself. **Correcting a correction's quotation of what it
  corrects is how this goes circular** — the instruction's own words, and they are right.
- **Labels and identifiers, not quotations of meaning** — `m5-n1-compose.md:980`
  (*"Unpushed-vs-ratified"* in a summary table), `m5-t3-…:72` (the candidate enumeration),
  `m5-record-correction-…:73-74, 80, 86` (a sweep-vocabulary line and its result table).
- **Records of a check that ran** — `m5-t3-…:530`, the read-back table whose grep *pattern* is the
  old headline. **Left deliberately**, and with a consequence recorded rather than fixed: that
  pattern would now return **0** against the corrected file. The row is a true record of a check
  performed at `0ed9068`; editing it would falsify the record, and the block in the harness file
  is what tells a later reader why the pattern no longer matches.
- **Correct uses of the rule under a descriptive label** — `m5-close-anatomy-…:72` and `:472`,
  *"the error m5's own §Promotion candidates entry on ratified-vs-unpushed artifacts describes"*,
  used about rewriting a **ratification**, which is what the entry governs. **Right reading, and
  it survives the correction unchanged.**
- **Already pointered last round** — `m5-n1-compose.md:47`, t3's row.

**One thing the sweep found that is worth more than the pointers.** The candidate text at
§Promotion candidates already contained the disambiguation the promoted headline lost: *"The rule
is not **never correct in place** — it is that the licence comes from the artifact's kind."* **The
compression happened at promotion, not at filing.** The candidate said what *in place* did not
mean; the headline distilled from it dropped that clause and kept the ambiguous phrase. Recorded
in that pointer, because it locates where the defect entered.

---

## Deviations

**None.** Four paths changed: `../aetheris/CLAUDE.md` (the harness commit),
`cloudcost/docs/m5-ruling-edit-implementation-notes.md`, `cloudcost/m5-n1-compose.md`, and this
record *(new)*. Harness commit lands first, agents second.

**No ticket was opened, no `Touches` amended, no gate re-run**, and no body sentence of the
promoted entry changed.

---

## Review

`Dated 2026-08-11. Per R20 this edit gets no review file; the reviewer's finding lands here,
verbatim, with the disposition beneath.`

- **A promoted rule's headline used one phrase in two senses.** *Finding, raised by
  claude-code at the record-correction edit and reserved to the reviewer: the entry's
  headline and body disagree about whether a ratified artifact may be corrected in
  place.* **Disposition: accepted, and the diagnosis sharpened before acting.** Not a
  contradiction but an ambiguity — *"in place"* means *rewritten* in the headline and
  *annotated at that position* in the body — compounded by a second compression that
  named one axis and denied the other. The headline is corrected, the body is not, and
  the sequence is dated on the page so a later reader can see the rule was clarified
  after a misreading rather than reshaped to defeat one. **Finding it required quoting
  the entry rather than working from the reviewer's summary of it**, which is the guard
  the correction round carried and the reason this surfaced at all.

**Accepted, and the sharpening is the part I got wrong.** My §3e reported *"headline contradicts
body"*. It does not contradict it — **it is ambiguous**, and the distinction is not pedantry: a
contradiction is a defect anyone reading both halves would catch, whereas an ambiguity is
invisible to a reader who resolves it, because resolving it feels like reading it. I diagnosed
the symptom I could see from one side and stopped there. **Had the fix followed my diagnosis it
would have been wrong** — I would have edited the headline to remove a contradiction that was not
there, most likely by making it agree with the body's *in place* sense, which leaves the second
compression untouched and the rule still one-axis.

**And the second defect I did not see at all.** *"The licence comes from the artifact's kind, not
from its push state"* was the clause I had **quoted approvingly** at the record-correction edit —
I read it as the entry's correct half while arguing the headline's other half was wrong. It is the
half that is false for records. Reading a sentence to check one clause and treating the rest as
given is the *cited-means-read* failure at sub-sentence scale.

**On the guard the finding's last clause names.** It is right that quoting the entry rather than
working from a summary is what surfaced this. Worth adding: **the guard has now paid out twice in
three commits, and both times on the same entry** — once at the record-correction edit, where
quoting the entry showed the headline problem the summary would have hidden, and once here, where
quoting it again showed that my own diagnosis of that problem was wrong. A guard that keeps
finding things in the same place is evidence about the place, not just about the guard: this
entry was compressed once at promotion and misread twice since, and it is the newest rule in the
section.
