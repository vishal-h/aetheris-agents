# BL-132 — the anatomy edit (implementation notes)

A reviewer edit, not a ticket. It authors BL-132's §6 anatomy into the row itself before the
row is worked, per **R12**, and marks one paragraph that had been carrying the wrong
attribution. **The ticket is not opened and no census work is done here.**

`Touches: docs/backlog-2026-06.md — the BL-132 row only — and this file. git status --short
showed those two paths and nothing else.`

**Filename convention, checked rather than assumed.** `cloudcost/docs/` holds 34 files in two
shapes: `bl-NNN-implementation-notes.md` for a row worked directly (BL-084, BL-085, BL-096) and
`{round}-{edit-name}-implementation-notes.md` for a reviewer edit inside a round (m5's ruling,
record-correction, body-addition, headline-correction, close-anatomy, pin edits). This edit is
both — a reviewer edit whose subject is a row — so it takes `bl-132-anatomy-`, which reads in
both conventions and leaves `bl-132-implementation-notes.md` free for the ticket, where the
row's own `Touches` now names it.

---

## The gate on the prompt

Four claims resolved before editing; three hold, one does not.

**R12 holds, with one nuance worth recording.** `docs/milestones/hc-consolidation.md:335` —
*"a ticket's §6 anatomy is written into this document **before that ticket opens**… Authoring
is the reviewer's (decision 11) via a section-scoped edit; the edit is dated and lands before
the ticket does."* Both operative clauses are satisfied here. The nuance: R12's stated
destination is *"this document"* — the round document — and BL-132 deliberately has none. So
this edit applies R12's requirement to a backlog row, which is an extension of its letter and
not a citation of it. Recorded rather than resolved; the shape is the human's ruling and the
anatomy is the reviewer's text, and neither is mine to adjudicate.

**§Carried in's attribution rule holds.** `cloudcost/m5-n1-compose.md:936–939` — *"An entry's
attribution is structural. An insertion between a claim and its `Source:` re-attributes both.
An edit that inserts into a structured document states where the insertion point falls relative
to the surrounding unit's boundaries."* That is the rule M1 invokes and the rule M2's placement
statement answers.

**The runbook anchor exists.** `cloudcost/runbook.md:377`, `## Offline tests` — so the
done-check's item 1 names a section that is there to re-resolve.

**One claim is false, and it is inside the anatomy block itself.** Method refinement 1 was
given as ending *"m5 t1 settled in one run what three documents had disagreed about **for two
months**."* The final clause does not survive any reading:

| measured from | to | span |
|---|---|---|
| the runbook's *now-unreachable* claim, `711c216` 2026-08-02 | m5 t1, 2026-08-10 | **8 days** |
| BL-070's filing, m2 (2026-08-02/03) | m5 t1, 2026-08-10 | **~8 days** |
| the first cloudcost commit at all, `f8399e3` 2026-07-27 | m5 t1, 2026-08-10 | **14 days** |

The widest available reading is two weeks. **The clause was excised and nothing was
substituted** — the sentence lands as *"m5 t1 settled in one run what three documents had
disagreed about."* Its two surviving claims were checked and hold: the three documents are the
three rows `cloudcost/m5-n1-compose.md:591` names — *"BL-070 assumed it dead, BL-131 assumed one
route, BL-132 found two contracts describing a path nothing takes"* — and *settled by execution*
is what m5 t1's **E8** actually did (`compose([a])` and `compose([a, b_eur])` run, `grand_total`
and the multi-currency warning read off the output, the cap demonstrated at N=1 and N=2). Nothing
else in the block was altered. **If the duration was load-bearing, restore it with a corrected
figure — this edit does not choose one.**

---

## M1 — the unannounced paragraph

**Before**, at HEAD (`docs/backlog-2026-06.md:7721`), the paragraph opened the way any original
body paragraph does:

```
**One thing m5 t1 supplies that this row's method should use.** BL-132 names the entry point as
```

It landed at `305b3a1` (m5 t2), located by `git log -L 7721,7726:docs/backlog-2026-06.md`, in
the same commit as the `**Annotated 2026-08-10 (m5 t2)**` block above it — but carrying no
marker, it read as text filed 2026-08-07.

**After** — a marker line inserted above it, in the shape the row's two existing blocks use:

```
**Annotated 2026-08-10 (m5 t2), marked as such 2026-08-11.** The paragraph below landed at
`305b3a1`, in the same commit as the annotation block above it, and until now carried no opening
marker — so it read as text filed 2026-08-07. Its wording is unchanged.
```

**The paragraph is byte-unchanged, and so are both existing annotation blocks.** The proof is
structural rather than by inspection: `git diff --stat` reports **82 insertions, 0 deletions**,
and `git diff -U0 | grep '^-'` returns nothing. A pure insertion cannot have altered a byte of
any pre-existing line.

---

## M2 — the anatomy

**Where the insertion falls, per §Carried in's first rule.** Entirely **inside** the BL-132
unit, which is bounded above by `### BL-132 …` (`:7665`, unmoved) and below by the `---`
separator that precedes `### BL-133` (now `:7815`). Within that unit it falls **after the last
body paragraph** — the m5 t1 method paragraph M1 just marked — and **before the row's closing
`Source:` line**, which is unchanged and still reads *"m4 t5b G2 gate-stop, 2026-08-07 …"*.

**That is exactly the position §Carried in warns about**: an insertion between a claim and its
`Source:` re-attributes both, and left bare this block would have read as sourced from the m4
t5b gate-stop — the same defect M1 was repairing one paragraph earlier. It is defused by the
block carrying **its own dated authorship line**, which closes it immediately above the
`Source:` line and says so in terms:

```
`Anatomy authored 2026-08-11 by the reviewer, before the row is worked, per R12. Shape ruled
light by the human on the BL-084 / BL-085 / BL-096 precedent — row taken directly, one
implementation-notes file, no round document, no review file. Those three carried no anatomy at
all, so Touches and Done-check are new fields here rather than §6 fields relocated into the
light shape. This block attributes to this date and not to the row's Source line below.`
```

**What the block contains** — the reviewer's text, landed verbatim but for the excision above:
the shape statement; `Touches` (three paths, `cloudcost/milestone.md` §Contracts-only, this row
only, and the new notes file); a `Do not generate` fence; a four-item `Done-check`; three method
refinements; the refined population; and the findings threshold.

---

## The L3 finding the shape rests on, and why two fields are new

The human ruled the light shape on a precedent I was asked to verify in the scoping read, and
the verification changed what the anatomy had to say about itself.

`cloudcost/docs/bl-084-`, `bl-085-` and `bl-096-implementation-notes.md` — **none had a round
document**; all three were taken directly as rows, sequenced by a batch handoff
(`docs/handoffs/handoff-cloudcost-rig-batch-2026-08-03.md`), which is a kickoff and not a round
document. **None had a review file** in `docs/reviews/` or anywhere in the tree. And their §6
anatomy did not live in the notes file, the row, or a milestone document — **it did not exist**:

```
$ grep -ncE "Touches|Done-check|Contract refs|step-1 gate|Step-1 gate|Claude-code prompt" \
    cloudcost/docs/bl-084-implementation-notes.md \
    cloudcost/docs/bl-085-implementation-notes.md \
    cloudcost/docs/bl-096-implementation-notes.md
cloudcost/docs/bl-084-implementation-notes.md:0
cloudcost/docs/bl-085-implementation-notes.md:0
cloudcost/docs/bl-096-implementation-notes.md:0
```

Each row carries `Size · Priority · Section`, prose, a `Done when:` clause and a `Source:` line —
and a `Done when:` is a backlog-row field, not a §6 `Done-check`.

**So the precedent supports the light shape and does not supply `Touches` or `Done-check`.**
Writing them into BL-132 is an addition to that shape, not a relocation of §6's fields into it,
and the row now says so in its own text rather than leaving a later reader to infer that three
predecessors had them. That distinction is the whole reason the shape paragraph opens the
anatomy: *"light, and one part of it is new."*

---

## Deviations

**None.** Two paths changed, both named in this edit's `Touches`: the BL-132 row in
`docs/backlog-2026-06.md` and this file (new). No executable line changed anywhere; no contract,
no milestone document, no harness file was touched. The ticket is not opened and no contract's
reachability was examined.
