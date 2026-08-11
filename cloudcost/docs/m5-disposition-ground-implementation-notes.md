# m5 disposition-ground edit — implementation notes

`Reviewer-directed round, 2026-08-11. Not a ticket round: per R20 it gets no review file, and this
file is its committed record, written to receive the reviewer's findings as a dated "## Review"
section. No ticket's state changes, so R19 is not engaged and §Ticket set is untouched.`

**Subject.** One correction, to the ground of one disposition, in the subsection the next cycle
reads. The disposition itself — carried, not promoted — stands and is not weakened.

---

## 0. Gate — both repos level with origin/main

```
agents   HEAD = origin/main = 9a2ae4790788b7d4ec7b0700e0e63dcd9da8e684 · left-right 0 0 · tree clean
harness  HEAD = origin/main = 624197275358d29e2bb18f7e2bafcbc998e2ddf9 · left-right 0 0 · tree clean
```

The target is committed **and pushed**, so the correction takes the published-record form: in
place, dated, superseded wording quoted at its position.

**Contract refs read, none misnumbered:** R19 `docs/milestones/hc-consolidation.md:468`, R20
`:528`, R21 `:546`. R20 governs this round's form.

---

## 1. The unit at HEAD, quoted in full before replacement

`cloudcost/m5-n1-compose.md` §Milestone summary → `### Open for the next cycle`, `:1079–1092` at
`9a2ae47`:

> **A negative-control token stops being a negative control once a record quotes it.** A
> sweep at the record-correction edit reused the token a prior edit had used for the same job
> and it returned three hits — the prior edit's own committed record, quoting its control
> table. Controls are minted fresh per sweep, or a sweep over records of prior sweeps finds
> its own instruments and reads them as content. **And minting fresh is necessary without being
> sufficient: the act of *recording* a control is what spends it, and recording is a step every
> round performs by rule — so a round that mints fresh still hands its successor dead tokens.**
> The instance is this entry's own successor. The BL-132 row-correction edit minted three fresh
> controls precisely because this entry told it to, published them, and they all returned 0
> (`cloudcost/docs/bl-132-row-correction-implementation-notes.md:156–160` at `0587bf3`);
> re-running those same three over the tree *after* that commit returns **1 each**, every hit the
> one line of its own record that lists them (`:167–179`). The remedy held for the sweep that
> applied it and was already spent for the next one. Carried rather than promoted: one instance,
> found by the sweep it broke.

**The closing sentence's exact wording**, which the instruction asked to be read rather than
trusted: *"Carried rather than promoted: one instance, found by the sweep it broke."* It spans two
lines (`:1091–1092`), breaking after *"one instance,"*. **The instruction's paraphrase was
accurate** — it matches word for word.

---

## 2. The arithmetic, established from committed evidence before the edit

**The count is two.** The entry narrates two instances of one shape — a negative-control token
spent by being recorded, so a later sweep finds its own instruments and reads them as content.

**Instance 1 — a sweep reused a token a prior edit had already spent, and got three hits.**
Established from `cloudcost/docs/m5-headline-correction-implementation-notes.md:222–229`:

> `[The negative control had to be replaced mid-sweep, and the reason is worth recording. The first
> one used was "zzz-not-a-real-rule" — the token the record-correction edit used for the same job —
> and it returned **3**, because that edit's committed record quotes its own control table.]`

**Instance 2 — a round minted three fresh controls and spent them in the act of publishing them.**
`cloudcost/docs/bl-132-row-correction-implementation-notes.md:156–160` (three minted fresh, all
returning 0) and `:167–179` (re-run after that commit: **1 each**, every hit its own control
table). This is the instance the clause appended at the obligation-landing edit added.

**Neither is a ticket.** Instance 1 belongs to the headline-correction edit (`244e49e`); instance 2
to the BL-132 row-correction edit (`0587bf3`). Both are reviewer-directed edits inside the m5
cycle. m5's §Ticket set holds t1, t2 and t3, and neither instance is any of them.

### 2a. FINDING — the entry misattributes instance 1, and it is inside `Touches`

**The entry says** *"A sweep at **the record-correction edit** reused the token a prior edit had
used for the same job and it returned three hits."* **The sweep was not at the record-correction
edit.** Derived by command, not by reading:

```
$ git log --oneline --reverse d0fb25a..0587bf3
d025971  (t3 r1)
9b24b77  docs(m5): correct two claims in the round's records …   ← the RECORD-correction edit
244e49e  docs(m5): record the headline correction                ← the HEADLINE-correction edit
…
$ grep -n "control" cloudcost/docs/m5-record-correction-implementation-notes.md
120: negative control    "zzz-not-a-real-rule"  harness=0  agents=0
```

At the **record-correction** edit the token returned **0/0** — it was that edit that *minted and
spent* `zzz-not-a-real-rule`. The sweep that reused it and got **3** was the **headline-correction**
edit, which is the later commit and which recorded the episode in its own notes (quoted in §2
above). So the entry names the spender as the sweeper: the record-correction edit is the *prior
edit* whose committed record supplied the three hits, not the round that tripped over them.

**Reported, not acted on.** The entry is inside this round's `Touches`, so declining is a judgement
and not a scoping constraint, and it is recorded as such. The instruction scopes *what changes* —
*"What changes is the ground"* — and a second, undirected correction to the entry's opening
sentence would exceed it. **The ruling this round executes is unaffected either way:** both
candidate edits (record-correction and headline-correction) are reviewer-directed edits and
neither is a ticket, so the corrected ground holds under either attribution. The correction landed
below is worded so that it does not propagate the misattribution — it describes instance 1 by what
happened rather than by which edit it happened at. **This is for the reviewer to rule on.**

---

## 3. §7's bar, in its own words

`../aetheris/docs/methodology/milestone-methodology.md:218–225`, read at harness `6241972`:

> 1. Human or claude-ui scans the milestone's review files for findings that
>    recurred on ≥2 tickets.
>    **The review files are not the only input.** A defect that a sync or sweep
>    ticket *discovers* appears in no review file, because no reviewer ever saw
>    it — so the scan also reads the milestone's doc/runbook sweep and the final
>    ticket's implementation notes. BL-007's runbook-update misses (t2 and t4)
>    were surfaced only by t5's sweep and would have been invisible to a
>    review-files-only scan, despite clearing the ≥2-ticket bar.

**The bar is recurrence across ≥2 *tickets*, so the ruling's ground holds and the gate does not
stop.** Step 1's own qualification strengthens it rather than weakening it: it widens the *input
channels* the scan reads — sweeps and implementation notes, not only review files — while leaving
the *unit of counting* explicitly at tickets, which is what *"despite clearing the ≥2-ticket bar"*
says of an instance pair (t2 and t4) that were themselves tickets. An instance found outside a
review file still counts only if it happened on a ticket. Neither of this entry's does.

---

## 4. The edit

**Form taken from:** the supersession block at `cloudcost/m5-n1-compose.md:1045–1062` — **the
existing instance in the same subsection**, the t3 r1 block over *"Neither is promoted here"*. Its
shape: a blockquote opening with a **bolded backticked bracket stamp** naming the date, the round,
what triggered it, what stands unrewritten and what the block supersedes; the substance inline
after the stamp; and a closing paragraph giving the reason it was corrected rather than left
standing. All four elements are reproduced.

**Per decision 7**, which that instance also follows, the superseded sentence is **left standing
unrewritten** and the block supersedes it in position, immediately after the paragraph it
corrects. The disposition — *carried, not promoted* — is restated in the block in its own words
and is not weakened; only the count offered as its ground is withdrawn.

**Consistency with the annotation below it, checked rather than assumed.** The `[Clause appended
…]` bracket asserts that the disposition line *"is left byte-unchanged"*. It still is: decision 7
supersedes by addition, so that assertion remains true after this edit rather than being quietly
falsified by it.

---

## 5. The sweep

**Vocabulary published before counts**, and run in the **reach-based form** the previous round
established, so the result does not depend on any token surviving publication:

```
git grep -c -F -e '<term>' -- . ':!cloudcost/docs/m5-disposition-ground-implementation-notes.md'
```

**Terms.** S1 `one instance, found by the sweep it broke` (the superseded sentence verbatim);
S2 `rests on one instance` (the premise restated); S3 `Carried rather than promoted: one instance`
(the disposition+count pairing); S4 `one instance` (widest form).
**Negative controls, first attempt:** `rests on a single instance`, `one-instance ground`.

| Term | Hits |
|---|---|
| S1 `one instance, found by the sweep it broke` | 1 |
| S2 `rests on one instance` | 1 |
| S3 `Carried rather than promoted: one instance` | 7 |
| S4 `one instance` | 20 |
| N `one-instance ground` | **0** |
| N `rests on a single instance` | **1 — control failed, discarded** |

**A control failed and is reported rather than replaced silently.** `rests on a single instance`
returned **1**, at `cloudcost/m4-consolidation.md:765`. It is not a spent token from a prior sweep
— nothing had ever used it — it is a phrase a *different cycle* already wrote about a *different*
entry. **This is the reach problem in a form freshness cannot reach:** a token can be unused and
still be ordinary English that some other document has independently said. Discarded, and three
replacements minted and **verified 0 before being relied on** — `one instance and no ticket`,
`sweep it broke twice`, `disposition-ground premise`. **Positive control:** `negative-control
token` → **8**, so the corpus is searchable and the zeros are absence.

**What the sweep found: nothing owed.** No site outside the entry carries the corrected premise as
a live assertion.

- **S2's single hit** (`m4-consolidation.md:632`) and the failed control's hit (`:765`) are both
  about **m4's own promotion rows and the harness Silent-wrong-answer entry** — a different entry
  truthfully stating *its* one instance. Not this premise.
- **S3's seven** decompose cleanly: `m5-n1-compose.md:1076` is **the other entry** in the same
  subsection (*§7's distillation can lose what the candidate got right*), whose own *"one
  instance"* is still true and is not this round's subject; `:1091` is the superseded sentence,
  standing per decision 7; `:1096` is this round's block quoting it as superseded. The remaining
  four (`bl-132-row-correction:321, :328`; `m5-obligation-landing:62, :147`) are stamped
  quotations of the entries as they stood, which a stamped quotation may do.
- **S1's single hit** (`m5-obligation-landing-implementation-notes.md:177`) quotes the sentence in
  the course of reporting that it reads false as arithmetic — a premise quoted while being refuted
  is not a premise carried.

---

## 6. Reported, not acted on — three deferred items

**The deferral reason, stated once and applying to all three:** each is a defect in an
implementation-notes or review file, and all three are **deferred pending a measurement of whether
implementation-notes and review files are ever read by a later round.** Correcting a record no
later round opens spends effort on an artifact whose readership is assumed rather than known; the
measurement decides whether these are worth correcting at all, and that decision is upstream of
each of them. None is edited here and no row is filed for any.

### D1 — the t3 r1 block quotes the rule's pre-correction headline

**The characterisation is accurate, and verified rather than accepted.** The two texts:

*At harness `0ed9068`* (`CLAUDE.md:956–957`), which the block names as its source:

> **An unpushed artifact may be corrected in place; a ratified one may not — the licence comes from
> the artifact's kind, not from its push state.**

*At harness HEAD `6241972`* (`CLAUDE.md:956–957`):

> **An artifact's kind decides how a correction is made; its push state decides only whether the
> correction may be silent.**

The pre-correction headline returns **0** hits at HEAD, so it was replaced rather than joined. The
block's *"correct reading"* paragraph — *"governs how each is corrected, never whether"* — does
argue **against** the headline it quotes, and only the HEAD headline states it.

**One qualification the instruction's framing omits, and it changes what the item is.** The
headline correction landed at harness `3dd2927`, which is **after** `0ed9068` (`git log
0ed9068..HEAD -- CLAUDE.md` returns it). So when the block was written the corrected headline **did
not yet exist**: the block quoted the entry accurately as it stood, argued from the entry's **body**
— which was never wrong and is unchanged — against its headline, and **that argument is what caused
the headline correction.** The harness entry's own dated block says so and dates the order
deliberately: *"the correction was made after and because of a misreading that quoted the headline
and not the body — …m5-t3-implementation-notes.md §r1"*. So the defect is a **stale citation**, not
a wrong argument: the block cites a superseded text as its authority without a note that it has
since been superseded. Deferred on the reason above.

### D2 — the "FIRST of three occurrences" count: **verified TRUE**

The block asserts the misreading is the first of three occurrences and that the other two carry
pointers to it. **Enumerated by command**, vocabulary published first: `out of bounds`,
`out of reach`, `rather than edited` over both repos.

**Population — three occurrences, and the record-correction edit had already published exactly
this population** at `cloudcost/docs/m5-record-correction-implementation-notes.md:73–80`, with its
own stated vocabulary (`out of bounds|ratified-artifact rule|ratified artifact|unpushed
artifact|…`):

| # | Site | Carries a pointer to #1? |
|---|---|---|
| **1** | `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → *The one claim that does not hold* (`:666`) | — it *is* #1 |
| **2** | `docs/reviews/m5-cloudcost-t3-review.md` §*F1 — accepted* (`:124`) | **Yes** — *"Full correction … at `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → The one claim that does not hold"* (`:132–134`) |
| **3** | `cloudcost/m5-n1-compose.md` §Ticket set, t3's row, the r1 clause (`:47`) | **Yes** — *"Full correction at `cloudcost/docs/m5-t3-implementation-notes.md` §r1 → The one claim that does not hold"* |

**Control:** the positive control `ratified` fires across **54** files in the searched corpus, so
the three-member result is a filtered population and not a failed search; the reach-based negative
control `prohibition-misreading-token` → **0**.

**Result: the count is correct and both non-first occurrences do carry pointers.** The
instruction's characterisation of it as *"an unverified count inside a correction"* is **wrong** —
it was verified when written, in that edit's own record, with a published population table. It is
re-derived here independently and confirmed. Nothing to correct, and nothing was.

### D3 — the general-present-tense remedy statement

**Anchor resolved rather than trusted:** `cloudcost/docs/m5-headline-correction-implementation-notes.md:225–226`
is correct — `:226` reads *"have to be minted fresh per sweep, or a sweep over records of prior
sweeps will find its own"*, and the sentence begins on `:225`. It states the remedy in general
present tense with no quotation frame, so it now carries the premise this cycle qualified — that
minting fresh is sufficient. **BL-140 holds the general question** of whether a correction owes a
same-commit sweep for recurrences. Deferred on the reason above; not edited, no row filed.

---

## 7. Deviations

**None from the instruction's scoping.** Two paths changed, both named in `Touches`:
`cloudcost/m5-n1-compose.md` (§Open for the next cycle, the negative-control entry only) and this
file. No backlog row, no review file, nothing in `cloudcost/milestone.md`, either `CLAUDE.md`, any
review file or any methodology document, and no edit to any file named under *reported, not acted
on*.

**One judgement recorded rather than left implicit:** §2a's misattribution finding lies **inside**
`Touches` and was still not acted on, because the instruction scopes what changes to the
disposition's ground. That is a decision, not a constraint, and it is the reviewer's to overturn.

---

## 8. Done-check

`Both items run post-commit. Recorded here and folded into the same commit by amend, so the round
stays one commit; the drift figures were taken at the pre-amend SHA and re-run after the amend,
and the only difference between the runs is the SHA in the backlog row's WARN.`

### 8a. `python3 -m pytest cloudcost/tests/ -q`

```
........................................................................ [ 93%]
..........................                                               [100%]
386 passed in 143.43s (0:02:23)
exit 0
```

**386 passed — unmoved**, the same figure t1, t2 (both rounds), t3, and the obligation-landing
edit recorded. This round changed no executable line; a move would have been a finding.
`-q` was used rather than `-v`: the per-test names carry no information this round does not
already have, and the progress dots plus the summary establish the same count. Stated so the
difference from the previous round's `-v` capture is declared rather than noticed.

### 8b. `python3 scripts/drift_check.py --strict`

```
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
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=7dbdb7d current=9a2ae47
[WARN] project_knowledge: CLAUDE.md stale — manifest=2ef0517 current=6241972
[PASS] command_fields: 11 documented §4 structs (56 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  4 WARN  7 INFO
exit 0
```

**Full output, nothing elided. 8 PASS · 0 FAIL · 4 WARN · 7 INFO, exit 0 — neither count moved**,
which was the stated expectation.

**All four WARNs are the declared `project_knowledge` staleness exemption, named and not chased —
and this round all four are byte-identical to the previous round's, including the SHAs.** Neither
path this round touches is manifest-tracked, so unlike the obligation-landing edit there is no
row advanced to this commit: `docs/backlog-2026-06.md` still reads `current=9a2ae47`, the previous
commit, because this round did not touch it. **The `--amend` therefore moved nothing in this
output**, and the post-amend re-run is identical in every field rather than differing in one; the
caveat in the preamble above is stated for form and did not arise.

That these four have no clearing schedule remains **BL-143**'s subject, filed by the previous
round and not touched here.

### 8c. State

**Agents:** one commit, working tree clean, **push held**. **Harness:** untouched — no commit,
nothing staged, level with `origin/main` at `6241972`. The harness methodology and `CLAUDE.md`
were read and quoted, not edited.
