# hc-e's opening anatomy edit — implementation notes

**Ticket.** The reviewer-authored section-scoped edit hc-e's stop asked for — *"a reviewer-authored
section-scoped edit carrying the five fields plus a step-1 gate"*
(`hc-e-implementation-notes.md` §5). **Repos.** agents from `9fbba09`, harness `48f59e7`
(untouched, and clean — `git -C ../aetheris status --porcelain` → 0 lines). **Date.** 2026-08-09.

**Not hc-e.** hc-e's stop stands as a stop. This edit lands the anatomy hc-e stopped for; hc-e
opens in a later session against it. Documents only — no code in either repo, no `sprint.sh`
change, no backlog row filed or closed, no close work.

**Landed:** hc-e's five previously-unauthored §6 fields, its step-1 gate G1–G6, and a `STANDING`
block; block A's revision of the named question; A2's two status surfaces under R19; A3's
amendment to R19 itself; A4's correction of §Not established's census block; and two promotion
candidates — one appended to the packet-integrity entry, one new (A5).

---

## 1. Phase 1 — the verification pass, in full

Every claim the authored text marked `[V]` was checked **before transcription**, at agents
`9fbba09` / harness `48f59e7`. **All confirmed. Nothing was refuted, so no sentence was withheld.**
Every command was bound to its target by absolute path or `git -C`, and the binding is printed
beside each result.

### 1a. Block A's `[V]` — the named-question slot, quoted in full first

**Confirmed**, `docs/milestones/hc-consolidation.md:1019–1026` pre-edit, verbatim:

```
**The named question that gates the rest.** *What hc-c and hc-d actually did* — which arm landed,
whether decision 13 was overturned, whether BL-044 came in, which rows closed and which were
filed. None of it is knowable now, and guessing it would be R13's worse failure.

> `[partly falsified 2026-08-09 (anatomy edit r1). "None of it is knowable now" no longer holds for
> hc-c: its arm landed, decision 13 was not overturned, and both rows closed. hc-d's half stands —
> it has not run. Revised in full at hc-e's own opening anatomy edit; the original wording stands,
> per decision 7.]`
```

**The stop condition did not fire.** Block A instructed: *"If the original's wording makes that
replacement incoherent rather than merely longer, stop and report instead of reconciling."* It does
not. The original declares a question and asserts it unknowable; the replacement answers both
halves and demotes the slot to a record of what was open. That is supersession, which decision 7
already has a shape for — not a contradiction needing reconciliation. **Both** the original body
and the r1 mark are kept beneath, because the r1 mark is itself part of what the revision
supersedes: its surviving half, *"hc-d's half stands — it has not run"*, was false by the time this
edit ran. hc-d closed at r3 (`f8ed90f`).

### 1b. Block A2's `[V]` — the header `**Status:**` line, quoted in full first

**Confirmed**, `:12–15` pre-edit, verbatim:

```
**Status:** **OPEN** — hc-a, hc-b and hc-c closed; **hc-d opened 2026-08-09 and stopped at its
step-1 gate**, and reopens against the anatomy this edit lands. **Opened:** 2026-08-08.
**Document created:** 2026-08-08 (hc-b). **Repos:** `aetheris-agents` and `aetheris`
(harness). **Preceding cycle:** m4-cloudcost, closed 2026-08-08.
```

**One formatting decision, named rather than made silently.** The block is four lines and carries
more than the status sentence. A2's authored replacement covers the status sentence only, so the
trailing metadata — `Opened:`, `Document created:`, `Repos:`, `Preceding cycle:` — is left
untouched and unmoved. Decision 11: the content is the reviewer's, the fit to the destination
file is claude-code's.

### 1c. Block A2's second `[V]` — hc-e opened and stopped at agents `9fbba09`

**Confirmed, and the cell's four factual claims were re-derived from the commit itself rather than
read off hc-e's packet.**

```
$ git -C <agents> log -1 --date=short --format='%h %ad %s' 9fbba09
9fbba09 2026-08-09 docs(hc-e): the opening edit E1-E4, and a stop at 2 of 7 fields with no gate slot
```

| Claim in the cell | Verdict | Where it was derived from |
|---|---|---|
| hc-d's row closed under R19 | **Confirmed** | `git show 9fbba09 -- …hc-consolidation.md` — the only ticket-set hunk is `@@ -596,7 +596,7 @@`, rewriting the **hc-d** row alone |
| The recency-selection candidate filed | **Confirmed** | the same diff, `@@ -1546,6 +1546,21 @@` — *"An artifact selected by recency is not bound to its purpose."* added whole |
| BL-135 established as a duplicate of BL-075 and folded | **Confirmed** | `git show 9fbba09 -- docs/backlog-2026-06.md` — `[FOLDED into BL-075, 2026-08-09 (hc-e's opening edit, E3)…]`, `**Status:** folded`, and the *"a third observation, folded in from BL-135"* annotation on BL-075 |
| BL-075's arm-2 blocker partly lifted — *the durable place exists; the routing does not* | **Confirmed, and the phrase is the row's own** | same diff: *"**So: the place exists; the routing does not.**"*, under *"arm 2's blocker is PARTLY lifted"* |
| 2 of 7 §6 fields, no step-1 gate slot at all | **Confirmed by derivation, with a positive control** | over `### hc-e` at `9fbba09` → **2**; **positive control** over `### hc-d`, same pattern and flags → **7**; `Step-1 gate` under hc-e → **0**, under hc-d → 1. The zero therefore reads as absence, not as a broken pattern |

### 1d. Done-check item 8's `[V]` — `hc-consolidation.md` carries no manifest row

**Confirmed, by parsing the field and not by grepping the line** — the substring-versus-field
carrier is a promoted rule (harness `CLAUDE.md`, **Silent-wrong-answer**) and a manifest lookup is
exactly its shape: a `grep -qF` over this table once reported `cloudcost/runbook.md` as tracked
because it matched a different row's substring.

```
rows parsed from column 2 (repo path)                              : 25
docs/milestones/hc-consolidation.md                        (exact) :  0
docs/milestones/hc-e-anatomy-edit-implementation-notes.md  (exact) :  0
docs/backlog-2026-06.md                  (POSITIVE CONTROL, exact) :  1
```

The 25 agrees with the document's own *"its 25 parsed rows"* (§Close criteria clause 6's source
line). **Consequence for this commit:** neither file this edit touches is manifest-tracked, so
check 8's committed-history dependency does not bite and the pre-commit `--strict` run is
meaningful in full — see §4.

### 1e. Two checkable specifics inside A5 and A4, not marked `[V]` but verified anyway

Decision 1's class, decision 2's remedy. Both **confirmed**:

- **A5's first instance** — *"the promotion candidate's own 'three instances in this round', wrong
  one commit after it was written."* §Promotion candidates, the note under the open list: *"The
  form was chosen at A4 because "Three instances in this round" went stale one commit after it was
  written."*
- **A5's second** — *"§Not carried's 'four' … fixed that way at hc-d's opening edit."* §Not carried
  §Open for the close now reads *"the open questions are §Not established's, whichever carry
  `[OPEN]`"* with a dated block recording that *"the original said 'four'"* and that *"the
  replacement drops the number rather than correcting it."* A5's reading of that fix is the fix's
  own stated reasoning.
- **A4's provenance, derived rather than assumed.** The census block was introduced by
  `149c1a8`, and the same pattern over each commit's tree shows where it staled — so the block was
  correct in its own commit and was staled by hc-d adding items, which is the candidate's whole
  point:

```
149c1a8  (the commit that wrote the block)   ->  9      ← true here
05a4cdb                                      ->  9
88183b8  (hc-d's gate: items 10, 11)         -> 11      ← staled here
2b62192  (hc-d r2: item 12)                  -> 12
f8ed90f                                      -> 12
9fbba09  (this edit's parent)                -> 12
```

### 1f. Block A3's closing sentence — transcribed verbatim, with the tension reported

A3 ends: *"Three surfaces have now gone stale under a rule written to stop it: hc-b's row at hc-c,
hc-c's own row at r1, and hc-e's row here."* It carries no `[V]`, so the withholding protocol does
not reach it and it is transcribed as authored. **The tension is recorded rather than smoothed,
because a later census will meet it:**

R19 was added at `3971121` (hc-d's anatomy edit, 2026-08-09) — established by
`git log -S'### R19 — a session that changes'`. Of A3's three, only **hc-e's row went stale after
R19 existed**; hc-b's and hc-c's predate the rule they are said to have gone stale under. And R19's
own preamble already counts three, with **hc-d's row** as its third where A3 has hc-e's — so the
document now carries *"three"* twice, over overlapping but different members, one section apart.
That is the count-beside-a-contradicting-enumeration carrier, and A5 — landing in this same commit
— is the candidate about exactly this shape.

**Not corrected.** It is reviewer-authored text and the sentence has a defensible reading (*three
in total, now that the rule exists*). Named here so the next reader adjudicates it rather than
re-derives it.

---

## 2. Divergences and self-corrections, recorded rather than smoothed

**1. The discharge sentence, wrong twice — claude-code's, both caught by this edit's own
done-check before publication.** Worth the space, because the second error is the exact defect A5
lands in the same commit.

- **First form.** The discharge read *"…and no `[R13]` mark remains in this subsection."* The census
  returned **1**: the discharge note's own quotation of the catch-all it discharges. The structural
  claim was true; the sentence, read as a claim about the text, was false against the grep that
  checks it. That is the substring-versus-structure carrier (harness `CLAUDE.md`,
  **Silent-wrong-answer**) firing on its author.
- **Second form, and it falsified itself.** The fix substituted the count — *"a `grep` … returns
  **1**, and that one hit is this sentence's own quotation"*. Re-running the census returned **2**:
  the new sentence contains the `[R13:` token as well, so it entered the population it was
  counting. **The count was moved by the sentence describing it** — `hc-d`'s opening edit E1 in
  miniature, inside the commit that lands A4's *stamp the census with its commit* and A5's *where a
  pointer will do, do not carry a number at all*.
- **Third and final form: a pointer, no count.** *"Every remaining occurrence of the `[R13:` token
  in this subsection is a quotation inside this discharge note."* That claim is stable under its own
  presence, which the two counts were not.

Both errors were caught because the census ran **before** the packet was written rather than after,
which is the only reason this is a note and not a finding.

**2. Done-check item 8's `[V]` annotation dropped in transcription.** As authored the item reads
*"`hc-consolidation.md` is not manifest-tracked `[V: confirm it carries no manifest row]`, which is
what makes that legal"*. The `[V]` is discharged at §1d, so the landed item carries the claim
without the annotation. Precedent: the hc-d anatomy edit's r1.5, which transcribed A1–A6
*"abbreviated only by dropping the `[V]` annotations that r1.1 discharges."*

**3. `STANDING` is new to the template, and that is stated rather than normalised.** No ticket in
this document has had one: the positive control over `### hc-d` returns **0** for the `STANDING`
pattern and **7** for the §6 fields, so hc-d's zero is a real absence rather than a pattern that
does not match. It lands because it is reviewer-authored; it is named because a later reader
comparing hc-c, hc-d and hc-e will otherwise read it as a slot the others are missing.

**4. No review file was created.** This is a reviewer edit, not an `hc-*` ticket round.
`docs/reviews/hc-e-review.md` keeps its Round 0 and its empty Round 1. Precedent: `599747e`
(hc-c's opening edit) and hc-d's own anatomy edit, neither of which wrote one. The open ruling
behind this — whether reviewer edits acquire review files at all — is hc-d anatomy r1.4 Finding 2,
still unresolved; §5 below is this round's stand-in, as r1.5 was hc-d's.

---

## 3. What is transcription and what is claude-code's

Decision 11's split, stated so a reviewer can audit it.

**Transcribed verbatim** — the packet-integrity candidate's appended paragraph; block A's
replacement body; A2's header sentence and hc-e's state cell; A3's amendment text; A5's candidate
in full; and hc-e's `Touches`, `Do not generate`, `Runbook update rule`, `Done-check` (items 1–9),
`Claude-code prompt`, the step-1 gate G1–G6 with its precondition, and `STANDING`.

**Claude-code's, and named as such:**

1. **Block A's `[revised]` wrapper** and the arrangement that keeps the original body *and* the r1
   mark beneath it. A4 and A5 specify their content; decision 7 specifies the shape; the join is
   claude-code's.
2. **A4's correction block in full.** A4 specified three requirements — re-derive at this commit,
   stamp the block with its commit, state that the prefixes govern. The wording, the two-tree
   derivation, and the provenance table in §1e are claude-code's execution of them.
3. **The catch-all discharge note**, in hc-d's shape (`:993–1006`), including the correction at
   §2.1.
4. **Placement and formatting.** The five §6 fields sit after the *Two obligations recorded now*
   block and before the gate, with the gate last — hc-c's precedent, carried by hc-d's anatomy
   edit. `STANDING` sits between the gate and the discharge notes, so the reviewer's ordering is
   preserved and claude-code's dated notes remain last, as in hc-d.

---

## 4. The done-check, and what it establishes

Run before this file was written, each command bound to its target. Full output is in the packet.

| # | Check | Result |
|---|---|---|
| 1 | Anatomy census over `### hc-e`, stated pattern, enumeration printed | **7 of 7** §6 fields; gate slot **1**; `G1`–`G6` **6** with **6** `VERDICTS:` lines; `STANDING` **1** |
| 2 | **Positive control** — same pattern, same flags, over `### hc-d` | **7** fields, gate **1**, `STANDING` **0**. The hc-e counts read as presence, and hc-d's `STANDING` zero as real absence |
| 2b | Live `[R13:` marks under `### hc-e`, i.e. outside the discharge note | **0**. **Positive control**, same token over `### hc-c` → **3** and `### hc-d` → **2**, so the zero is absence and not a pattern that fails to match |
| 3 | §Not established population, **both trees** | `9fbba09` → **12**; working tree → **12**. Invariant. **4 RESOLVED (1, 7, 8, 9), 8 OPEN (2–6, 10–12)**, tallied independently of the enumeration |
| 4 | Manifest, parsed by field | 25 rows; both touched files **0**; positive control **1** (§1d) |
| 5 | `drift_check.py --strict`, absolute-bound, exit from the invocation | `8 PASS  0 FAIL  3 WARN  7 INFO`, **exit=0** |
| 6 | Harness state | `48f59e7`, `git status --porcelain` → **0 lines**. Untouched |

**The three WARNs are named, not chased** — all three are `project_knowledge` manifest-staleness,
the one strict-exempt class: `docs/backlog-2026-06.md` (manifest `384656c`, current `9fbba09`),
harness `CLAUDE.md` (`288c8ef` / `b4d782a`), `docs/aetheris/runbook.md` (`ae0c510` / `2ebc59c`).
None is a file this edit touches, and neither file this edit touches is manifest-tracked (§1d), so
**a post-commit re-run would return the same three** — the check-8 ordering caveat has nothing to
bite on here. They clear at hc-e's export boundary, which is where they are supposed to clear.

**Why the two-tree derivation is the point, not belt-and-braces.** hc-d's opening edit E1 is the
worked case: an **8** measured at `d29f5c6` and written into `149c1a8`, which gives **10** — *the
count was moved by the sentences describing it*. A4 asks for a count written into the very section
it counts. Every line this edit adds to §Not established sits inside a blockquote and so cannot
match `^[0-9]\+\. \*\*`; running the pattern against both the parent tree and the post-edit tree
turns that argument into an observation. **The invariance is the derivation.** A difference between
the two would have been a stop, not a number to choose between.

---

## 5. A2–A5 verbatim, so this round's scope is committed and not only conversational

Recorded per §2.4. The reviewer's text as received, abbreviated only by dropping the `[V]`
annotations §1 discharges. The anatomy's own blocks (the append, A, B–G, STANDING) are not repeated
here — they land in `hc-consolidation.md` and are committed by this same commit.

- **A2 — both status surfaces, under R19.** The header `**Status:**` line quoted in full first,
  then replaced with *"hc-a, hc-b and hc-c closed; hc-d closed 2026-08-09 at r3; hc-e opened
  2026-08-09 and stopped at its anatomy census, and reopens against the anatomy this edit lands."*
  hc-e's §Ticket set row: `Not started` replaced, in hc-d's shape, by the opened-and-stopped cell
  naming `9fbba09`, the four things its opening edit landed, the 2-of-7-with-no-gate stop, *"No
  close work"*, and `**Earlier state, kept per decision 7:** "Not started"`. **Do not touch any
  other row.**
- **A3 — amend R19, dated, in R19's own block.** *"R19 has now been evaded once by the mechanism
  meant to serve it."* hc-e's opening session **did** change hc-e's state, so R19 applied and the
  row was owed in that commit; it was not written because the reviewer's ticket text said to leave
  the row untouched on the grounds that the census might change what it should say. *"That
  instruction was wrong."* The general form: **a ticket instruction cannot suspend R19** — not
  knowing the final wording is never a reason to leave a false one standing; where an instruction
  and R19 conflict, R19 governs the fact and the instruction governs only the wording; a session
  receiving such an instruction writes the row anyway and names the conflict in its packet.
- **A4 — §Not established's census block.** Correct in place, dated, keeping the original per
  decision 7. Three parts: **(1)** re-derive at *this* commit, not from the finding, printing the
  enumeration beside the count with resolved and open named by item number; **(2)** stamp the block
  with its commit — what it read, at which commit that was true, at which commit the new figures
  were derived, *"your own rule from the 8-against-10 reconciliation at hc-d's opening edit — a
  count must name its commit — applied to the block that most needs it"*; **(3)** state that the
  block is a snapshot, that the per-item prefixes are authoritative, and that *"these totals are a
  convenience that goes stale the moment an item is added, and have done so once already."*
- **A5 — a new promotion candidate**, authored by the reviewer, landed verbatim: *"A census
  recorded inside the document it censuses goes stale as that document grows."*

**Scope held.** Documents only, two files, one repo. No `sprint.sh` change, no code, no hc-e close
work, no backlog row filed or closed. hc-e opens in the next session against the anatomy this edit
lands.

---

## 6. Not reached, not dropped

- **hc-e's own work is untouched**: §7's ritual and its prior-claims census, the export boundary,
  the milestone summary, and §Close criteria's reads all belong to hc-e. Its `Done-check` above is
  a specification, not a run.
- **§Not established items 10, 11 and 12 stay `[OPEN]`.** Their resolvers are not this edit and not
  hc-e; the round closes with them open, which the `Do not generate` field states is correct.
- **§Rows filed is untouched** and still reads *"Empty at hc-b"* — this edit files and closes no
  backlog row.
- **The packet-assembly catch has no truth-maker inside either repo.** The appended paragraph's
  *"69 of 184 lines"* describes hc-e's opening-edit packet preamble; a search over
  `hc-e-implementation-notes.md` and `hc-e-review.md` for `184|69 of|still running|mid-stream`
  returns nothing, and no other repo file records it. It is transcribed as the reviewer's account
  of an artifact this session cannot inspect — which is precisely why the instruction was to put it
  on the record. Named so the next reader does not go looking for the capture.
- **hc-d anatomy r1.4 Finding 2 is still open** — reviewer edits have no review-file carrier, so
  whether their notes file *is* the committed record remains a ruling nobody has made. §5 above is
  the same stand-in r1.5 used, applied a second time.

---

## Review

Per **R20**, recorded 2026-08-09 at this edit's r1: a reviewer-authored section-scoped edit gets no
review file, and this notes file is its committed record. Findings verbatim; dispositions beneath.
This section is r1's own record.

**Raised at:** agents `e047dd1`, harness `48f59e7`. **Round 1**, narrowly scoped and
pre-authorised to close.

---

### F1 — MUST FIX. A3's closing sentence is wrong twice, and your §1f is right.

> The sentence is mine and it does not survive your check. Two defects:
>
> 1. **It misattributes.** *"Three surfaces have now gone stale under a rule
>    written to stop it"* — hc-b's row at hc-c and hc-c's own row at r1 both went
>    stale **before R19 existed** (`3901121`-era; you dated it at `3971121` by
>    `git log -S`). They are the instances that *caused* R19, not instances of it
>    failing. Only hc-e's row went stale after the rule existed.
> 2. **It double-counts.** R19's own preamble already enumerates three, ending
>    with **hc-d's row**; A3's three ends with **hc-e's**. Two totals over
>    overlapping-but-different members, one section apart, in the commit that
>    lands A5 — the candidate about exactly this shape.
>
> Replace the sentence, keeping the original beneath per decision 7:
>
>   R19 was written after three surfaces had already gone stale — the three its
>   own preamble enumerates. hc-e's row is the **first since**, and it is the one
>   that matters most: it did not go stale because anyone forgot, but because a
>   reviewer instruction told a session to leave it, and nothing in the loop
>   flagged that an instruction was overriding a standing rule. That is what this
>   amendment is for. No total is carried here; the preamble's enumeration and
>   this instance are the record, per the candidate one section below.
>
> The point gets sharper by being accurate: R19 did not fail three times. It
> failed once, in the way rules of its kind actually fail — overridden from above
> rather than forgotten from below.

**Disposition: APPLIED**, `hc-consolidation.md` §Ratified decisions → R19, inside the A3
amendment block. The replacement is transcribed verbatim; the original sentence is quoted beneath
it in a nested `[corrected]` block per decision 7, together with both defects named as the finding
names them.

**One transcription note, and it is the finding's own instance re-appearing.** F1's text dates R19
two ways in one sentence — *"(`3901121`-era; you dated it at `3971121` by `git log -S`)"*, the
first digit-string differing from the second. Only the second resolves:

```
$ git cat-file -t 3901121   -> fatal: Not a valid object name 3901121
$ git cat-file -t 3971121   -> commit
```

The correction block therefore carries `3971121` alone, with the commands above as its
truth-maker, and no reference to a hash that does not exist. Flagged rather than silently
normalised, because a hash in a correction inherits the correction's authority — the rule the
harness `CLAUDE.md` states as *a correction inherits the authority of the claim it replaces*.

**And this note was itself wrong on its first draft**, which is why the commands are printed
rather than described: it rendered the resolving hash as `3971141` while quoting a sentence that
says `3971121` — a mis-transcribed hash inside the paragraph about a mis-transcribed hash, caught
by running `git cat-file` against both rather than by re-reading. Recorded for the same reason the
discharge sentence's three forms are (§2.1): the check that catches this class is running the
command, never reading the number again.

---

### F2 — MUST FIX. The packet-integrity append rests on figures no repo can check. Your §6 named it; it needs to be in the candidate, not only in the notes.

> *"69 of 184 lines, four gates green and the fifth cut mid-stream"* describes
> hc-e's opening-edit packet preamble. Packets are not committed here, so a
> promoted candidate now carries specifics that are unreconstructible from either
> repo — and §7's promotion-verification step will ask that entry to be quoted
> from its destination file with its surrounding lines, which will succeed while
> its evidence remains unverifiable.
>
> That is not a reason to drop the candidate. Its substance — a partial capture is
> indistinguishable from a complete one by content alone — is sound and was
> established by a line count, not by inspection. It is a reason to say where the
> figures come from.
>
> Append to that paragraph:
>
>   The figures are claude-code's account, given in hc-e's opening-edit packet
>   preamble and recorded here; packets are not committed in either repo, so they
>   are not reconstructible from the tree. The claim they support does not depend
>   on them — a capture read before its producer exits is partial whatever the
>   line counts were.

**Disposition: APPLIED**, `hc-consolidation.md` §Promotion candidates → the packet-integrity
candidate. The appended text is verbatim, followed by a dated `[appended]` block recording what
the paragraph carried at `e047dd1` and why the provenance was stated rather than the figures
dropped. The finding is upheld against my own §6, which named the gap and left it in the notes —
where §7's verification step would never have looked.

---

### F3 — RULING, closing hc-d anatomy r1.4 Finding 2. Reviewer edits' review trail.

> Your §2.4 and §6 both note the same open question, stood in for twice now:
> reviewer-authored edits write no review file, so whether their notes file is
> their committed record has never been ruled. Ruling, to land in §Ratified
> decisions as R20:
>
>   R20 — a reviewer-authored section-scoped edit is not a ticket round and gets
>   no review file. Its implementation-notes file is its committed record, and the
>   reviewer's findings on it land there, appended as a dated `## Review` section
>   with the findings verbatim and the dispositions beneath — the same shape R2
>   requires of a review file, in the artifact the edit already has. R2 is
>   unchanged for `hc-*` ticket rounds.
>
>   The reason is that R2's purpose is a committed trail for every session that
>   changes the repo, not a particular filename. Inventing a review file for a
>   session with no rounds would make the file's own `## Round N` structure a
>   fiction; putting the findings in the notes keeps the trail and keeps the
>   structure honest.
>
>   Recorded 2026-08-09, closing hc-d anatomy r1.4 Finding 2, which had been
>   stood in for at that edit's r1.5 and again at hc-e's anatomy edit §5.
>
> Then apply it to this edit: append F1–F3 verbatim, with your dispositions, to
> `docs/milestones/hc-e-anatomy-edit-implementation-notes.md` as its `## Review`
> section. That section is r1's own record.

**Disposition: APPLIED, and applied to itself.** R20 landed in §Ratified decisions between R19 and
the m4-decisions table, transcribed verbatim with its reason and its closing stamp. This section
is R20's first application. §2.4 and §6 above are superseded by it and left standing per decision
7 — both said the ruling was unmade, which was true when written.

**One consequence, derived not assumed, and it is the only edit r1 makes beyond F1–F3.** R20's
landing stales any live citation of the decision range. A census over the whole document for
`R1[–-]R(1[0-9]|20)` and `R[0-9]+ through R[0-9]+` returns **five** hits; **four are historical
records and are correctly left alone** — `:477` (*"R15 through R19"*, the provenance stamp for
what hc-d's anatomy edit added), `:624` (hc-a's row, *"the ruling questions R1–R11 answer"*),
hc-**d**'s Claude-code prompt (`R1–R19`, and hc-d is closed: its prompt records what hc-d was
told), and the document-created stamp (*"Decisions R1–R13"*). **One is live**: hc-**e**'s
Claude-code prompt, for a ticket that has not reopened. Transcribed as **`R1–R20`**.

Precedent, and it is exact: hc-d's anatomy edit met this at its own §2 item 4 — authored `R1–R18`
where R19 landed in the same commit — and the reviewer ratified the change at r1's A6, *"a prompt
shipping stale at birth is worse than a transcription divergence."* Named here rather than made
quietly, because r1's authorisation is scoped to F1–F3 and this is the one edit outside it.

**R20 does not otherwise bind hc-e**, which is a ticket round and keeps `docs/reviews/hc-e-review.md`
under R2 unchanged. That file is untouched by this round.
