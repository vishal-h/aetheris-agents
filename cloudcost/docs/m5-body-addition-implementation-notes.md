# m5 — naming the published-record case, and carrying two findings forward — implementation notes

`Dated 2026-08-11. A reviewer-authored edit adding one sentence to a promoted rule's body in the
harness CLAUDE.md, and appending two carried findings to this round's §Milestone summary. Per R20
this is not a ticket round and gets no review file; this file is its committed record. Declared
the last edit on this entry. m5 is not reopened — the round is closed and its work stands.`

## Filename

`m5-body-addition-implementation-notes.md`. **Checked, not assumed:** `ls cloudcost/docs/` → 33
files, **31** ending `-implementation-notes.md`; the exceptions are `m3-linode-scout.md` and
`m5-scoping-landing-notes.md`. The stem continues the directory's m5 non-ticket-edit series —
`m5-close-anatomy-`, `m5-pin-edit-`, `m5-ruling-edit-`, `m5-record-correction-`,
`m5-headline-correction-` — each naming the edit rather than a ticket.

## Measurement stamp

Derived at harness `3dd2927` and agents `244e49e`, before this edit's changes. **The entry was
read from the harness file, not from the instruction describing it.** That guard has now paid out
three times on this entry and is not dropped at the last edit on it.

---

## Gate on the instruction

Five claims checked. **Four hold; one needs a precision that does not change the action.**

1. **`3dd2927` / `244e49e` pushed and unchanged.** **Holds** — each equal to `origin/main`,
   `origin/main..main` 0, both trees clean.
2. **The body names two cases and leaves the third to entailment.** **Holds** — established at the
   headline-correction edit and re-read here at HEAD.
3. **The insertion point exists as described** — an unpushed-record sentence, then *"A ratified
   decision is different in kind"*. **Holds.**
4. **The added sentence would contradict nothing already there** (K3(d)'s hold condition).
   **Holds; no hold.** It says *record → correct in place* (the headline's *kind decides how*) and
   *published → dated, not silent* (the headline's *push state decides only whether the correction
   may be silent*). It is the body's own case-1 reason run in the other direction, and it matches
   the reading r4 had already taken.
5. **"The published-record case arose at the BL-131 ruling edit r4, and that session had to reason
   it out from the entry's silence and record a *conservative reading*."** **Substance holds; one
   precision.**

### The precision

**The literal phrase *"conservative reading"* does not occur.** `grep -i 'conservative reading'`
over `cloudcost/docs/` and `docs/reviews/` returns nothing; `grep -ci 'conservative'` over the
ruling-edit notes returns **1**, and that hit is the passage meant. The wording is *"The reading
taken, **conservatively**, and recorded so the choice is auditable"*. The claim is a fair
paraphrase, and it is named here because a later reader searching the quoted phrase would find
nothing and conclude the citation was wrong.

**And what r4 read was the candidate, not this entry.** r4 is agents `0b8804b`, **2026-08-10
12:22**; the entry was promoted into the harness at `0ed9068`, **18:15** the same day; the
candidate was filed at `4cdd31f`, **11:34**. So at r4 the promoted entry did not exist, and the
passage says so in its own words — *"§Promotion candidates' third entry holds that…"*.

**This strengthens the correction rather than weakening it.** The gap was in the candidate, was
carried through §7's distillation into the promoted entry unchanged, and cost a derivation before
the promotion and a flag after it. It is also the first carried finding at K2, arriving with a
second instance.

---

## K1 — the published-record case is named

### K1(a) — the body at HEAD, quoted in full

> **An artifact's kind decides how a correction is made; its push state decides only whether the
> correction may be silent.** Correcting an unpushed record in place is sound: its claims become
> meaningful when someone reads them, so a dated supersession block would preserve a reading
> history no reader ever had. A ratified decision is different in kind. Its authority is the act
> of ratification rather than its publication, so a reader citing it later is entitled to know its
> text is what was ratified — and cannot learn that from a notes file they have no reason to open.
> Correct it with a dated block that quotes the superseded wording in the position it occupied,
> never silently, however few people have read it.

### K1(b) — the sentence added

Placed after the unpushed-record sentence and before *"A ratified decision is different in
kind"*, verbatim as instructed:

> A published record is the third case, and it is stated here rather than left to be entailed:
> correct it in place, and date the correction — the licence to be silent lapsed when the record
> acquired readers, which is the same reason that granted it while it had none.

### K1(c) — proof no existing sentence changed

By text comparison, not line ranges — the method the last round's own failed check taught:

```
added sentence present exactly once               : True
new entry == old entry + the one added sentence   : True
  entry chars 1805 -> 2071,  delta +266

preserved verbatim  "Correcting an unpushed record in place is sound"          True
                    "A ratified decision is different in kind"                 True
                    "Correct it with a dated block that quotes the superseded" True
                    "however few people have read it"                          True
                    "Source: m5-cloudcost, the BL-131 ruling edit r1"          True

headline unchanged by this edit                   : True
the prior dated block still present, exactly once : True
```

**The whole entry equals its prior text plus one sentence.** `Source:` untouched.

**The body's lines re-wrapped and its sentences did not**, and the difference is the point. The
insertion falls mid-sentence-boundary inside a hand-wrapped paragraph, so every following line
moves; a line-range check would call that a changed body and be wrong, exactly as one did at the
headline correction. The text comparison above is what the claim is actually about. *(A side
effect worth naming: the short ~74-character line the headline correction left behind is gone,
because the paragraph re-wrapped around the insertion. Not a separate edit — a consequence of
this one.)*

### K1(d) — the dated block, as landed

> `[Added 2026-08-11: the published-record sentence. **This is an addition; the block above is a
> replacement — two dated blocks on one entry, and they did different things.** That one swapped a
> headline and changed no other sentence; this one adds a sentence and changes none. Before it,
> the body named two cases — the unpushed record and the ratified decision — and left the third,
> a *published* record, to be entailed from the first's own stated reason: silence is licensed
> because a supersession block "would preserve a reading history no reader ever had", a reason
> that lapses exactly when readers exist. **Entailment was sound and had already cost.** At the
> BL-131 ruling edit r4 a session met the case and had to derive it from scratch, recording the
> derivation because the rule did not carry it: *"The rule and its gap. §Promotion candidates'
> third entry holds that 'the licence comes from the artifact's kind, not from its push state' …
> The entry rules on kind versus push state for the licence to correct in place; it is silent on
> whether publication changes what a correction must carry."* — and then *"The reading taken,
> conservatively, and recorded so the choice is auditable: kind licenses the in-place correction,
> and publication withdraws the licence to make it undated."*
> (`../aetheris-agents/cloudcost/docs/m5-ruling-edit-implementation-notes.md` §r4 → *B2 — the
> dated note, and the reading taken*.) The sentence now in the body states that reading, so the
> next reader inherits it instead of re-deriving it. **What r4 read was the §Promotion candidates
> candidate, not this entry** — r4 is 2026-08-10 12:22 and the promotion 18:15 — which matters
> only in that the gap was in the candidate first and survived distillation into here. **The two
> existing cases are byte-unchanged**, and so is the `Source:`: the whole entry equals its prior
> text plus this one sentence, checked by comparison of the text rather than of line ranges.]`

**Insertion point.** After the headline-correction block, before the next top-level claim
(*For any ticket whose Done-when names a user-facing action…*), indented two spaces so it sits
inside this bullet. **Both dated blocks now follow the `Source:` in date order**, and neither is
between a claim and its attribution.

### K1(e) — read back out of the file

`grep -n -B3 -A12 "An artifact's kind decides how a correction is made"` over
`../aetheris/CLAUDE.md`. **One hit**, the three cases readable in sequence at `:957`–`:966`, with
the preceding entry's closed `Source:` above. Quoted in the packet.

---

## K2 — two findings carried forward, not promoted

**Both below §7's bar, and neither gets an exception.** This round excepted the bar twice —
the packet-elision rule (*bar does not apply*) and the unpushed-vs-ratified rule (*below the bar,
by explicit ratification*). **A third would make the bar a formality**, which is the instruction's
reasoning and it is right: two exceptions are a judgement about two rules, three is a policy about
the bar.

**Destination and why it is the right one.** `cloudcost/m5-n1-compose.md` §Milestone summary →
*Open for the next cycle*. That is the subsection the next cycle's §7 reads, and it is the
subsection **m5 itself inherited its carried candidates through** — §Carried in names
`docs/milestones/hc-consolidation.md` §Milestone summary → *Open for the next cycle* as its
source. Carrying them here puts them exactly where this round found its own.

**Where the insertion falls**, per §Carried in's first rule. Inside `### Open for the next cycle`,
**after** its existing paragraph and that paragraph's dated `[Corrected 2026-08-10 at t3 r1…]`
block, and **before** the subsection's closing *"**Sequence from here:** BL-132 → provider four…"*
line. **The unit above is a complete claim-plus-correction pair and is byte-unchanged**; the
closing sequence line is byte-unchanged and remains last, which keeps it reading as the
subsection's close rather than as a fourth item. Neither carried finding carries a `Source:` line —
the subsection's existing items carry none either, and inventing one here would have made these
two look like a different kind of entry from the ones beside them.

**The two, as landed** — verbatim from the instruction, under one lead paragraph stating the
bar-exception reasoning:

1. **§7's distillation can lose what the candidate got right.**
2. **A negative-control token stops being a negative control once a record quotes it.**

**The first now has its second instance, and it is in this file's gate.** The candidate's gap on
the published-record case survived distillation into the promoted entry, which is the same failure
the finding describes — §7 verified the entry could be read out of its file and never compared it
against the candidate. **Not used to promote it**: a second instance found while writing the
finding down is exactly the evidence a later cycle should weigh with fresh eyes, and the carried
text says *one instance* because that is what was recorded when it was raised.

---

## Deviations

**None.** Four paths changed: `../aetheris/CLAUDE.md` (harness commit, first),
`cloudcost/m5-n1-compose.md`, and this record *(new)* — three, not four. No ticket opened, no
`Touches` amended, no gate re-run, no existing sentence of the promoted entry changed.

`[Corrected in place before commit: the sentence above said four paths and named three. Left
visible rather than silently fixed — this file is unpushed, which is the case the entry's own
first sentence licenses correcting in place, and the count was wrong for the ten seconds between
writing it and re-reading it.]`

---

## Review

`Dated 2026-08-11. Per R20 this edit gets no review file; the reviewer's finding lands here,
verbatim, with the disposition beneath.`

- **The body named two of three cases and entailed the third.** *Finding, raised by
  claude-code at the headline correction and flagged rather than acted on, since naming
  it is a body change.* **Disposition: accepted; the case is named.** Entailment was
  sound and insufficient — a reader had already derived it once from the entry's
  silence and recorded doing so, which is the cost that decides it. The two findings
  the same round surfaced are **carried, not promoted**: below §7's bar, and a bar
  excepted three times in one round is not a bar.

**Accepted, and the disposition's middle clause is the part I did not have.** I flagged the gap
as a structural observation — *the body states two cases and entails the third* — and offered no
evidence that entailment had ever failed anyone. **The r4 derivation is that evidence, and it was
in the tree the whole time.** A gap argued from structure is a prediction; a gap with a session
that paid for it is a finding, and the second is what justifies changing a promoted rule. I had
the weaker version and did not go looking for the stronger one.

**On the bar.** Declining to except it a third time is right, and the reason generalises past
this round: **the two exceptions this round did take were each argued from the rule's own
subject** — a packet rule is not recurrence-derived, and an irreversible failure does not recur
its way to attention. Neither carried finding has an argument of that shape. They are ordinary
one-instance observations, and the honest place for those is a carry.

**This entry, closed.** Three edits in three commits — promoted at the close, headline corrected,
body completed — and each was found by quoting it from the file rather than from a description of
it. **The rule the sequence demonstrates is not in the entry and is not proposed here**: that the
newest rule in a section is the one most likely to be wrong, because it has been read fewest
times. Recorded in this record only, since the round's carried findings are already two and the
instruction closed the entry.
