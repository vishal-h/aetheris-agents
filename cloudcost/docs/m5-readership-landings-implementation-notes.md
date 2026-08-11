# m5 — readership-landings edit: record

**This file is written in the shape this round's own promotion candidate argues for, and it is
that candidate's first test.** The candidate (`cloudcost/m5-n1-compose.md` §Open for the next
cycle, appended by this edit) holds that a notes file is read by the next round in its arc or by
nobody, so a record should carry what a successor opens it for — findings, what is owed, what is
uncertain, the anchors — and point at the commit for the derivation rather than re-narrating it.
Everything below is written to that rule. **Where the derivation is not here, it is in the commit**,
and the commit is the one this file lands in.

Reviewer-directed section-scoped edit. **Per R20 no review file.** No backlog row. Harness
read-only. Gate at open: agents `4caa671`, harness `6241972`, both clean.

**Measurement source.** The figures quoted in the candidate come from the readership measurement
round, which was read-only by design and committed no record; its report is at
`/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad/notes-readership-measurement.md`.
**That path is not durable and the report is not in either repo** — see §4, where this is the one
thing this round leaves owed.

---

## 1. The two items that decided their own edits, decided before editing

### 1b — the attribution was wrong; corrected

Established from committed history before the edit, not from the instruction.

| Edit | Commit | What it did with `zzz-not-a-real-rule` |
|---|---|---|
| record-correction | `9b24b77` | **minted and spent** it — `m5-record-correction-implementation-notes.md:120`: `harness=0 agents=0` |
| headline-correction | `244e49e`, one commit later | **reused it and got 3** — `m5-headline-correction-implementation-notes.md:222–227` |

`m5-n1-compose.md:1080` named the record-correction edit as the reuser. That edit is the one that
got the zero. The three hits the headline-correction sweep got are three published control tables
(`m5-record-correction:120`, `m5-t2:330`, `m5-t3:290`). **Attribution only** — the finding and the
disposition are untouched.

### 3 — the readership figure, published before the branch was taken

`cloudcost/docs/m5-headline-correction-implementation-notes.md`, created `244e49e` (2026-08-11),
measured on the two instruments the measurement round used:

- **Later commits citing it: 2, both R-class** by that round's own criterion (a line number or
  figure with content attributed) — `9a2ae47` (*"`:225–226` states the remedy in…"*) and `4caa671`
  (*"Established from `…:222–229`"*; *"Anchor resolved rather than trusted: `…:225–226`"*).
- **Later sessions opening it: 0 strong, 2 weak** (`1f7f9fbc`, `90489c34`), after excluding the
  creating session `f546c110` and this one, as the measurement excluded its own.

**Branch taken: it has later readers on both instruments, so it was corrected in place, dated.**
Not the null branch. Note what the number actually shows: both readers arrived the same day, which
is the candidate's own claim about adjacency rather than a counter-example to it.

---

## 2. What landed, with anchors

| # | File · position | What |
|---|---|---|
| 1b | `cloudcost/m5-n1-compose.md` §Open for the next cycle, the negative-control entry's 2nd sentence | Sentence **replaced**; dated block quotes the superseded wording at its position |
| 1a | same entry, clause before the disposition line | **Third failure mode**, landed as a clause inside the entry, not a new entry |
| 4a | same subsection, own preamble | The promotion candidate |
| 2 | `cloudcost/docs/m5-t3-implementation-notes.md`, after the quoted entry at `:679–687` | Dated note: citation superseded. **Argument untouched** |
| 3 | `cloudcost/docs/m5-headline-correction-implementation-notes.md`, after `:227` | Dated qualification on the remedy |

**Shapes taken, and the instances they were taken from.** The in-entry clause (1a) follows the
obligation-landing edit at `9a2ae47`, which inserted its clause into the entry body, left the
disposition line byte-unchanged, and stamped it with a `` `[Clause appended …]` `` block after the
entry. The in-place correction with a quoted supersession (1b) follows the disposition-ground edit
at `4caa671`. 4a is separately preambled rather than joined to the two findings above it, following
the obligation block's precedent — the *"Two findings carried forward"* preamble is scoped to the
edit that wrote it, so a later addition does not make that count read false.

**1a is a clause, not an entry, and therefore never engages §7's bar** — a precision on a finding
is not a finding. It is also the mode the entry's own headline does not reach: the token was never
reused and never recorded, it collided with ordinary English. Episode verified against
`m5-disposition-ground-implementation-notes.md:163–178` before landing.

---

## 3. Sweep — vocabulary and controls published before the counts

Reach-based, both repos, `':!cloudcost/docs/m5-readership-landings-implementation-notes.md'`.

**Negative controls, minted fresh and each verified 0 in both repos *before* being relied on** —
this round is the first application of the rule 1a lands, and it is the reason the rule exists:
`readership-landings-nullprobe` **0/0**, `qvx-sweep-control-4417` **0/0**,
`zzq-attribution-nullprobe` **0/0**. **No control fired; no re-mint was needed.**

**Positive controls.** `negative control` → agents **32**, harness **0**. The harness zero would
have made every harness zero below unreadable, so two harness-reaching positives were added before
the terms were run: `in place` → 225/14, `ratified` → 296/47.

| Term | Premise | agents | harness |
|---|---|---:|---:|
| `sweep at the record-correction edit` | 1b | 3 | 0 |
| `record-correction edit reused` | 1b | 4 | 0 |
| `` read at harness `0ed9068` `` | D1 | 3 | 0 |
| `An unpushed artifact may be corrected in place` | D1 | 9 | 0 |
| `minted fresh per sweep` | D3 | 9 | 0 |
| `Controls are minted fresh` | D3 | **3** | 0 |

**Two things the post-commit re-run showed that the pre-commit run could not.**

**(1) `Controls are minted fresh` fell from 4 to 3, and no text was deleted.** The 1b rewrite
reflowed the entry's paragraph, and the phrase now breaks across `m5-n1-compose.md:1082–1083`, so
the entry's own sentence stops matching a term that quotes it. This is the same line-wrap artifact
flagged for the harness below, appearing in this round's own sweep: **a fixed-string sweep term is
sensitive to rewrapping, so a count that moves after a reflow is not evidence that content moved.**
Both counts are published rather than the convenient one.

**(2) All three negative controls return 1 when this record is *not* excluded** — each hit is the
one line of this file that lists it. That is the entry's second mode firing on schedule: the act of
recording a control spends it. The three tokens above are now **dead for any successor**, which is
why the pathspec exclusion is stated with them and not assumed.

**Nothing owed.** Every hit read rather than pattern-matched, and each falls in one class: a
**stamped quotation of the unit as it stood** at a named commit (`bl-132-row-correction:324–329`,
`m5-disposition-ground:32–35` at `9a2ae47`, `m5-obligation-landing:143–146` at `0587bf3`,
`m5-obligation-landing:362–364`), which a stamped quotation may do; a site **already carrying its
pointer or qualification** (`m5-n1-compose.md:758`, pointered at the headline-correction edit
`:794`; `m5-headline-correction:271`, which says the `0ed9068` stamp makes the text *"accurate as
history"*; `bl-132-row-correction:172`, which already states the remedy is *"necessary and not
sufficient"*; `m5-obligation-landing:317`, which is D3's filing); or **the corrected site itself**.

**One harness zero is an artifact, not an absence.** `An unpushed artifact may be corrected in
place` returns 0 in the harness because the sentence **wraps mid-phrase** at `CLAUDE.md:980–981`.
The text is there. A reader re-running this term must not read that 0 as the headline being gone.

---

## 4. What is owed, and what is uncertain

**Owed — one item, and it is this round's own.** The measurement report the candidate rests on
lives only in a session scratchpad under `/tmp`. Every figure in the candidate is quoted inline
precisely because the path will not survive, but **the derivation behind those figures is not in
either repo and cannot be pointed at by a commit** — which is the one thing the candidate's own
shape rule assumes is always possible. Whoever acts on the candidate should decide whether the
report is committed or the candidate is re-grounded. **No row filed**: this round was directed to
file none, so this is recorded here as an open item rather than tracked, and it has no executor.

**Uncertain — the candidate's scope.** It is argued from one population measurement across two
repos, and §7 has no channel for evidence of that kind. Left as an open question in the entry, not
as a proposed amendment.

**Not uncertain, and worth saying so:** items 1a, 1b, 2 and 3 were each verified against committed
history or against the harness tree at HEAD before their edits, not accepted from the instruction.

---

## 5. Line count — the candidate's first test

Against the last three **reviewer-directed (R20)** rounds' records. `bl-132-row-correction` (396)
is excluded: it is a ticket round carrying a backlog row, not an R20 edit.

| Record | Lines |
|---|---|
| `m5-body-addition-implementation-notes.md` | 234 |
| `m5-obligation-landing-implementation-notes.md` | 519 |
| `m5-disposition-ground-implementation-notes.md` | 358 |
| mean | 370 |
| **this record** | **179** |

**179 against a mean of 370 — 48%, and below the shortest of the three.** The count is stamped last,
after the file settled. It took four passes — 159, 162, 164, then this, the last forced by the
post-commit sweep addendum above — each stamp falsified by the lines that stated it. That is the
rev-note-last hazard in its smallest form: a self-referential count has to be driven to its fixed
point, not measured once.

**The shape fits, with one strain worth reporting as a finding about the candidate rather than
hidden.** Four of the five things this round had to hand forward — the two decision figures, the
anchors, the sweep disposition, the owed item — compressed without loss, because each is a fact
with a citation. The one that resisted is **§3's "nothing owed" disposition**: it is a judgement
over sixteen hits, and the candidate's rule ("point at the commit for the derivation") does not
work for it, because the derivation is a *reading* of each hit and git stores the hits, not the
reading. Compressing it to "nothing owed" would have made the sweep unauditable. **So the candidate
needs a carve-out it does not currently state: a judgement over a population is carried, not
pointed at** — the same shape as its own census exception, arrived at from the other direction.
That is a finding about the candidate produced by testing it, and it is recorded here rather than
by padding the file.
