# m5 — the close-anatomy edit (§Close criteria, t3) — implementation notes

`Authored 2026-08-10 by claude-code, on the reviewer's section-scoped edit instruction, on
top of f6acc9c (t2 r1). Under R20 this edit is not a ticket round and gets no review file;
this file is its committed record.`

## Measurement stamp

Every figure, count, quotation and positional claim in this file was derived at agents
**`f6acc9c`** (this edit's parent) or in the working tree this edit produces, and each says
which. Line numbers appear only for claims about lines, per **m5-D1**; everywhere else a
section is named and its text quoted. Positional claims carry the commit they were measured
at.

**The harness is not edited by this round.** `../aetheris` was read for two things only —
`docs/methodology/milestone-methodology.md` §7, to resolve C4's `Contract refs` claim about
it, and `git status` / `git rev-parse`, to confirm it is clean and unmoved. No harness file
was written.

## Filename

**Checked, not assumed.** `git ls-tree --name-only HEAD cloudcost/docs/` at `f6acc9c`
returns 29 files. **27 end `-implementation-notes.md`**; the two exceptions are
`m3-linode-scout.md` and
`m5-scoping-landing-notes.md`, enumerated rather than counted so the residual is legible.
The suffix is therefore the directory's dominant pattern and this file matches it.

**Closer precedent, in this round.** The two prior reviewer-authored section-scoped edits —
`cloudcost/docs/m5-pin-edit-implementation-notes.md` and
`cloudcost/docs/m5-ruling-edit-implementation-notes.md` — carry the same R20 basis and the
same suffix. `m5-scoping-landing-notes.md` is the one same-round record that does not, and
it is the odd one out rather than the pattern.

---

## Gate on the instruction

Run before any edit. Every claim the prompt makes about repo state was resolved; seven
hold, one does not.

| Claim | Result |
|---|---|
| `f6acc9c` is pushed and is HEAD | **Holds.** `git rev-parse HEAD` → `f6acc9cd95af108e6bff89e9e1f34b7d345352a3`; `git rev-list --left-right --count origin/main...HEAD` → `0	0`; `git status --short` empty |
| The harness is not edited by this round | **Holds.** `../aetheris` `git status --short` empty at `2ef0517` |
| §Ticket set's **Review files** block establishes that R2's text binds `hc-*` tickets and that the obligation is methodology §1 principle 4 and §8 | **Holds.** Quoted in full at C1 below |
| C1's new text: *"both t1 and t2 named it as a deviation"* | **Holds.** `cloudcost/docs/m5-t1-implementation-notes.md` §Deviation — *"One, declared rather than glossed. `docs/reviews/m5-cloudcost-t1-review.md` is outside…"*; `cloudcost/docs/m5-t2-implementation-notes.md` §*r1 — deviations* — *"One, named because `Touches` requires exactly that"* |
| t2 is approved and pushed, and its row's state clause reads *in review* | **Holds.** Row quoted at C5; r1's verdict is APPROVE per the row's own *"**r1 — verdict APPROVE, one finding.**"*; `git branch -r --contains` returns `origin/main` for both `305b3a1` (r0) and `f6acc9c` (r1) |
| C4's ref: methodology **§7** has five steps and a *"review files are not the only input"* clause | **Holds.** `../aetheris/docs/methodology/milestone-methodology.md` §7 is numbered 1–5 and step 1 carries *"**The review files are not the only input.**"* |
| C4's `Touches` names `docs/backlog-2026-06.md` | **Holds**, the file exists |
| C4's done-check: t1 and t2 ran the same pytest spine, one recorded figure | **Holds** — **386 passed**, recorded in both tickets' notes and in t2's row |

### The one claim that does not hold

**C6a's first disposition says t2 r1 *"flagged that correcting the cross-currency item might
exceed the amended bullet."* t2 r1 raised no such flag.** What it did was the opposite: at
**W3(c)** it corrected the item and asserted its authority in place, closing that paragraph
*"**In §Open items, so inside the amended `Touches`.**"*
(`cloudcost/docs/m5-t2-implementation-notes.md` §*W3 — the second-claim sweep over
`cloudcost/milestone.md`*, part (c)).

The two things r1 did reserve for the reviewer are dispositions two and three, both of which
the instruction states accurately: **W3(d)** — *"Reported, not fixed — two, and the
reviewer's call"* — and **§r1 — deviations** — *"**The reviewer's call** whether `Touches`
should carry it."* A `grep` for `exceed` over the whole file returns one hit, and it is in
W3(d), about the two staleness items.

**What was done about it.** The disposition's *ruling* — that the correction did not exceed
the bullet — is sound and is the reviewer's to make, so it lands **verbatim**, unedited.
What does not land unqualified is the characterisation: the `## Review` section below
carries the disposition as written and, beneath it, a dated resolution note quoting what t2
r1 actually says. Rewriting a ratification to fit the file would be the error m5's own
§Promotion candidates entry on ratified-vs-unpushed artifacts describes; letting the record
assert a flag that is not in the file would be a different one. Neither is taken.

---

## C1 — §Ticket set conventions: the review file stops being a per-ticket deviation

### The unit, before

Quoted at `f6acc9c`, the **Review files** block of §Ticket set's conventions paragraph, in
full:

> **Review files.** R2's own text binds *"every `hc-*` ticket"*, so it does not
> literally reach this round. The obligation is
> `../aetheris/docs/methodology/milestone-methodology.md` §1 principle 4 and §8, both
> unscoped, which are the sections R2 grounds itself in. Cited correctly here after
> t1 r1 established it against a round instruction that cited R2 as the source.

This is the block the instruction names: it establishes both halves — that R2's text binds
`hc-*` tickets, and that the obligation rests on methodology §1 principle 4 and §8.

### Where the insertion falls

**Between two whole paragraph units, and inside neither.** The **Review files** block ends
at the sentence quoted above; the next unit in the file is the **R19 applies.** block, which
opens *"**R19 applies.** A session that changes a ticket's state updates its row in the
table above in the same commit."* The new paragraph is appended after the former's final
sentence and before the latter's opening, separated by a blank line on both sides — the same
separator every other convention block in this run uses.

**No claim is separated from its attribution.** The **Review files** block carries no
`Source:` line and no trailing citation; its authority is stated inline (*"the obligation is
… §1 principle 4 and §8"*), which the insertion sits after rather than inside. §Carried in's
first carried rule — *"An insertion between a claim and its `Source:` re-attributes both"* —
is therefore satisfied by construction, not by luck.

### The unit, after

> **Review files.** R2's own text binds *"every `hc-*` ticket"*, so it does not
> literally reach this round. The obligation is
> `../aetheris/docs/methodology/milestone-methodology.md` §1 principle 4 and §8, both
> unscoped, which are the sections R2 grounds itself in. Cited correctly here after
> t1 r1 established it against a round instruction that cited R2 as the source.
>
> **A review file is not a `Touches` path, and landing one is not a deviation.** It is a
> standing obligation on every ticket round in this document, discharged in the round's
> own commit, and both t1 and t2 named it as a deviation because this sentence did not
> exist. Declared once here rather than re-declared per round. A ticket's `Touches` still
> governs everything else, and the round that established the distinction is the round
> that proved why: t2 r1 declined to widen its own scoping unasked, correctly.

**The appended text's own factual claim was checked**, not transcribed — see the gate table:
t1 and t2 each declared the review file as a deviation in their own notes, and each cited a
different authority for landing it anyway. The new sentence removes the need for a third.

---

## C2 — the new §Close criteria section

### Placement derivation — reported before writing, per the instruction

Both siblings were read. They **diverge**, and on exactly the relation that decides this
placement.

**`cloudcost/m4-consolidation.md`.** Its section order is §Why this exists → §Scope →
§Ratified decisions → §Ticket set → §Sequence → §What this cycle established → §Not
established → §Open for the close → §Promotion candidates → **§Close criteria** → §The
close. The criteria section sits *after* every section it reads and immediately *before*
the close's own report, opening *"This cycle is done when t1b through t5c have closed with
zero blocking findings…"*.

**`docs/milestones/hc-consolidation.md`.** Its order is §Why this exists → §Scope → §What
the methodology owes this round → §Ratified decisions → §Ticket set → **§Close criteria** →
§Rows filed → §Not established → §Promotion candidates → §Not carried, and why → §Milestone
summary. Here the criteria section sits immediately after the ticket anatomies and *before*
every section it reads, opening *"This round is done when hc-b through hc-e have closed with
zero blocking findings…"*.

**So there is no single convention to follow, and saying so is part of the report.** m4 puts
the criteria after the sections it reads; hc puts it before them. Three invariants they do
share:

1. after §Ticket set;
2. after §Ratified decisions;
3. before the close's own report section (§The close in m4, §Milestone summary in hc).

**Landed: between §Ratified decisions and §Promotion candidates** — after the `---` that
closes §Ratified decisions and before `## Promotion candidates`. This satisfies all three
shared invariants. The divergent relation is settled **for hc**, on the ground that this
document already treats hc as its shape authority rather than m4: §Not established's three
kinds and prefix set are **R21**'s; that section's resolved-item shape was taken from hc's
§Not established as, in its own words, *"the section R21 came from and the only in-repo
precedent"*; §Carried in is inherited from hc's §Milestone summary → §Open for the next
cycle; and the round's R-numbers are normative throughout its ticket anatomies.

**The runner-up, recorded rather than dropped.** Appending §Close criteria after §Carried in
— m4's relation, last before the close's report — satisfies invariants 1–3 equally. It was
rejected on the tiebreaker above and on nothing else. If a later round prefers m4's shape
for a cloudcost cycle document, this note is where the choice is, not buried in a diff.

### Where the insertion falls

**Between two section boundaries, inside neither.** The unit before it ends with §Ratified
decisions' final block, whose closing line is *"…the before and after are at §r1 of
cloudcost/docs/m5-ruling-edit-implementation-notes.md.]`"*, followed by the file's `---`
rule. The unit after it is the `## Promotion candidates` heading and its opening paragraph,
*"Candidates recorded here are promoted or dropped at this round's close under the
methodology's §7 ritual…"*. The new section is placed after that `---` and is followed by a
`---` of its own, so both neighbouring sections keep the separator shape they had.

**No claim was separated from its attribution**: the m5-D2 dated block that ends §Ratified
decisions closes with its own pointer to the record file, and that pointer stays inside its
own block, above the new heading.

### The unit, after

The section landed verbatim as instructed, six clauses, closing with the dated authorship
line:

> ## Close criteria
>
> Six clauses. Each is checkable, and the close reports the result of each whether or not
> it produced an edit — a clause that produced nothing is a result, not a silence.
>
> 1. **Every entry in §Promotion candidates is promoted or dropped**, with §7's
>    *recurred on ≥2 tickets* test applied and its result stated per entry. …
> 2. **The entries carried in from the preceding cycle are weighed on the same terms.** …
> 3. **Every §Not established item's state reads from its own prefix** …
> 4. **Every row in §Ticket set states its terminal state** …
> 5. **The drift checker runs and its result is recorded** …
> 6. **§Milestone summary is written** …
>
> `Authored 2026-08-10 by the reviewer, before t3 opens, per R12.`

Clause openings are elided above **and the full text is in the diff published with this
edit's packet**, unelided; this is a pointer to a landed section, not a substitute for it.
The two cross-references the clauses make were resolved against the file rather than
assumed: §Carried in does say *"and in force for this round's §7"* (clause 2's premise), and
§Not established's preamble does say *"The per-item prefix is authoritative; this section
carries no total"* (clause 3's premise).

---

## C3 — t3's row in §Ticket set

### The unit, before

§Ticket set's table at `f6acc9c` has the header `| Ticket | Subject | State |` and two body
rows, **t1** and **t2**. There is no t3 row; the absence was established by reading the
table's full extent — the row after t2's is the blank line that ends the table, not another
row.

### The unit, after

Appended after t2's row, in the table's own three-column shape:

> `| **t3** | The close: §7's ritual, the close criteria, and the milestone summary | **Not opened.** Anatomy authored 2026-08-10 |`

The ticket cell is bolded, as t1's and t2's are; the state cell opens with a bolded state
word, as both others do.

---

## C4 — t3's anatomy

### Heading level, derived

t1's anatomy is `### t1 — establish the N>1 compose surface (read-only)` and t2's is
`### t2 — apply the ruling`; both are `###` inside `## Ticket set`. t3's landed as
`### t3 — the close`, at the same level.

### Where the insertion falls

**After t2's anatomy in full, before §Ratified decisions.** The unit before it is t2's
`Claude-code prompt` block, whose final line is *"> Run the done-check and include its output
in the review packet. Update t2's row > in §Ticket set in the same commit, per R19. Do not
push."* The unit after it is the `---` rule that closes §Ticket set, followed by
`## Ratified decisions`. t3's anatomy is inserted between the end of t2's prompt block and
that `---`, so it lands inside §Ticket set — where t1's and t2's are — rather than after the
section boundary.

**Nothing was inserted inside t2's anatomy.** t2's seven fields and its gate are untouched
by this edit; the only change anywhere in t2's material is C5's state clause in the table
row, which is a different unit.

### The unit, after

Landed verbatim as instructed: the step-1 gate (temporal, stated), `Scope`, `Contract refs`,
`Touches` (five paths plus the review-file sentence pointing at C1's new convention),
`Do not generate`, `Runbook update rule`, a five-item `Done-check`, and the `Claude-code
prompt` — **seven §6 fields plus the gate**, matching the count this document's own
conventions paragraph states. It closes with:

> `Anatomy authored 2026-08-10 by the reviewer, before t3 opens, per R12. No slot is
> R13-marked: every field is authorable now, because the close's inputs are all committed.`

**The R13 claim was checked before landing it.** Every field names something that exists at
`f6acc9c`: §Close criteria (landed by C2 in this same commit), §Promotion candidates,
§Carried in, §Not established and §Ratified decisions all exist in this document; R19, R20
and R21 exist in `docs/milestones/hc-consolidation.md`; methodology §7 exists with the five
steps and the clause the field quotes; `docs/backlog-2026-06.md` and both `CLAUDE.md` files
exist. No field carries a `Resolver:` and none is blank.

The full text is in the published diff.

---

## C5 — t2's row marked terminal

### The unit, before

The state clause only, quoted at `f6acc9c`:

> `**State — opened and applied 2026-08-10 (r0), reviewed and corrected 2026-08-10 (r1); in review.**`

### The unit, after

> `**State — opened and applied 2026-08-10 (r0), reviewed and corrected 2026-08-10 (r1); closed, approved at r1 and pushed at `f6acc9c`.**`

**Nothing else in the row changed.** The row was rebuilt for readability at t2 r1 (its
§W5(a)) and is not rebuilt again; `git diff` shows one changed line in the table, and the
change within that line is confined to the clause quoted above — the gate clause, the
what-landed clause, the r1 clause, the done-check figure and the provenance clause are
byte-identical.

**Both identifiers were resolved, not transcribed.** The approving round is **r1**, whose
verdict the row itself records as *"**r1 — verdict APPROVE, one finding.**"* The pushed SHA
is **`f6acc9c`**, confirmed on the remote by `git branch -r --contains f6acc9c` →
`origin/main`; `305b3a1` (r0) is on the remote too, but the row's terminal state is r1's, so
r1's commit is the one named.

---

## Deviations

**None.** The instruction's `Touches` is `cloudcost/m5-n1-compose.md` and this edit's own
record; `git status --short` before the commit lists exactly those two paths and nothing
else. No review file is created — under **R20** this edit is not a ticket round, and C1's
new convention is about *ticket rounds*, which this is not.

No executable line changed anywhere, so no test gate is implicated. The drift checker is
clause 5 of the criteria this edit *authors*; running it is t3's obligation under that
clause, not this edit's, and it is not run here.

---

## Review

`Dated 2026-08-10. Per R20 this edit gets no review file; the reviewer's dispositions on t2
r1 land here, verbatim, with the record's own resolution beneath where one is owed.`

### W3(c) was authorised

*t2 r1 flagged that correcting the cross-currency item might exceed the amended bullet.*
**Disposition: it did not.** The bullet reads *any claim resting on the reachability premise
m5-D2 overturns*, and *"live at the first fan-out"* is that premise verbatim. The flag was
right to be raised and the correction is right to stand.

> **`[Resolved against the file, 2026-08-10 at this edit. The disposition's ruling stands
> verbatim and is not edited — it is the reviewer's to make, and it is correct on the
> merits. Its characterisation of t2 r1 is not what the file says, and that is recorded
> here rather than smoothed.]`**
>
> **t2 r1 raised no flag on this item.** Its §*W3 — the second-claim sweep over
> `cloudcost/milestone.md`*, part (c), corrected the cross-currency aggregation item and
> asserted the same authority the disposition now confirms, closing *"**In §Open items, so
> inside the amended `Touches`.**"* The word *exceed* occurs once in that file, in **W3(d)**
> — *"Fixing them would be exceeding the scoping at the very round whose subject is that
> scoping is authoritative"* — which is about the two staleness items, disposition two
> below. The other reserved call is in §*r1 — deviations*, about the review file,
> disposition three below.
>
> **The ruling is unaffected**, and so is what follows from it: the correction landed inside
> the amended bullet, on the reading the disposition gives. What changes is only the
> provenance of the question — the session settled it in place rather than referring it up.

### The two staleness items get a row, not a third `Touches` amendment

*Reported at t2 r1 and correctly not fixed.* **Disposition: filed at t3.** Neither rests on
m5-D2's premise, and settling either needs adapter reads — that is establishment work, not a
wording fix, and it belongs to a row rather than to a ticket already scoped elsewhere.
claude-code named the right shape itself.

**Carried into t3's anatomy at C4**, in two places that bind rather than describe: `Touches`
names `docs/backlog-2026-06.md` — **one new row** — and `Do not generate` closes *"**Do not
fix the two §Open items staleness findings t2 r1 reported**"*. The two instances the
disposition refers to are t2 r1's W3(d) items 1 and 2, the recency-modifier item and the
orphan-filename item, and t3's `Claude-code prompt` names both and states that they are a
starting population rather than the census.

### The review file's deviation status

*t2 r1 declined to widen `Touches` to include it, on the ground that the round whose subject
is scoping is the wrong round to widen scoping unasked.* **Disposition: accepted, and the
declaration is moved up a level at C1.** Declining was right; the fix is a convention, not a
seventh path.

**Landed at C1**, in §Ticket set's conventions, where it binds every round in the document
rather than one ticket's field. t3's `Touches` closes by pointing at it — *"The round's
review file is not a `Touches` path — see §Ticket set's conventions"* — so the next session
meets the convention in the field that would otherwise have made it a deviation.
