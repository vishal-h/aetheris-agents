# hc-b — implementation notes

**Ticket.** The canonical document, and I0 — the harness copy of the repos rule.
**Commits.** harness `b4d782a` (I0); agents — this commit.
**Base.** agents `8490362`, harness `288c8ef`.

---

## 1. The step-1 gate

All five passed before any edit. Commands and output are in the review packet §Gate. Two
things worth keeping here rather than only there.

**G5 was run by parsing the manifest table by field, not by grepping it.** The manifest has
five columns and a `grep` over it matches anywhere in a line, which answers a question about
text while you read it as a question about structure — the carrier promoted at the m4 close
(harness `CLAUDE.md`, Silent-wrong-answer, the substring-versus-field widening), whose own
source instance was a manifest grep. The check parsed 25 rows, skipped the self-referential
`_(this export)_` row, and compared each `commit` cell against
`git log -1 --format=%h -- <path>` in the row's own repo. **24 checkable, 0 stale.** That is
what makes Done-when 5's *exactly one WARN* a prediction rather than a hope.

**G4 was re-derived, not cited**, because I0 edits one of the two files the four m4 promotions
live in. All four read out at `288c8ef`: harness `:717` (the truth-maker's third operational
form), `:618` (substring-versus-field), `:632` (sibling state), agents `:475` (the packet
full-output rule, inside §Learning — BL-007 at `:467`).

## 2. I0 — three decisions the plan left open, and one it got wrong

**The BL-031 sentence is repointed, not copied — and the plan's wording would have falsified
the record.** The plan said to repoint the sentence so that harness-side the unread sibling is
`../aetheris-agents/`. That is wrong: BL-031's session ran *from* `aetheris-agents/` and never
opened the harness file. Inverting the sentence would have inverted a historical fact to fix a
presentational problem. The real problem is narrower — inside `../aetheris/CLAUDE.md`, the
string `` `../aetheris/CLAUDE.md` `` is self-referential. The fix keeps the fact and changes
the referent: *"BL-031 was a cross-repo ticket, **run from `../aetheris-agents/`**, whose
session never opened **this file**."* Recorded because the plan is the thing a reviewer reads
against the diff.

**The working-directory paragraph is inverted rather than omitted.** The plan allowed either
and asked which. Inverted: the agents copy's *"Edits default to this repo"* becomes *"Edits
default to the sibling; touching the harness is explicit and called out in the ticket's
`Touches` list"*, and the path-frame sentence gains *"— so a ticket naming `../aetheris/lib/…`
means a file in **this** repo."* Kept rather than dropped because that frame is the whole
argument for the canonical document living agents-side, and a harness-side reader is exactly
who needs it stated.

**Two dated notes, not one.** The first carries the sibling's editorial-placement paragraph
verbatim, with a sentence saying so: *"That paragraph is carried verbatim from the sibling
copy, where it was ratified; its counts are not re-derived here."* Its internal counts (*two
of the five repo-directed promotions*) were ratified at the m4 close and re-deriving them is
not this ticket's job — but an inherited claim that does not say it is inherited is a rumor
with a number, so it says. The second note is this copy's own: which copy was widened when
(`080ad24`, 2026-08-08 07:50 +0530), why the gap was deferred, that the two copies are
near-duplicates rather than a byte-identical mirror, and that `drift_check` has no
byte-identity check between them.

**One observation, not fixed.** The dated notes are wrapped in single backticks and contain
nested backticks — so as rendered markdown the code span closes early. **The sibling copy has
the same shape**, and these files are read as source by sessions rather than rendered. Matching
the established form was preferred to diverging the two copies further over a rendering
concern. Named here so it is a choice on the record and not an oversight.

## 3. The canonical document — where it landed and why

`docs/milestones/hc-consolidation.md`, agents repo.

**Agents-side because the repos rule fixes one frame.** *Paths in tickets and docs are relative
to `aetheris-agents/` unless prefixed `../aetheris/`.* A canonical document in the harness would
either write `../aetheris/scripts/sprint.sh` to name a file in its own repo, or carry a second
frame — and a document whose job is to be cited unambiguously is the worst place for two. m4's
cycle document cited `../aetheris/…` throughout a twelve-row ticket set with no path defect.

**`docs/milestones/` rather than flat `docs/`, on a corrected premise.** The first argument was
that a `milestones/` directory makes the manifest's inclusion rule structural. **The check
refuted it**: `docs/rig/milestones/` holds two *tracked* files — `p3/protocol.md` and
`bl-007/README.md` — the manifest's two named exceptions, admitted because they are milestone
*specifications later work is written against*. The inclusion rule reads the artifact's kind,
never its directory. What survives is weaker and sufficient: `docs/milestones/` is homogeneous
today (four files, zero tracked), the `m-eduloka-discovery-*` pair is direct precedent for a
milestone-level document living there untracked, and flat `docs/` holds exported standing docs
among which a working artifact sits as a different kind. **The refuted premise is recorded in
§Close criteria clause 6, attributed** — it is decision 1's class and it is the reviewer's — and
clause 6 carries *both* halves, because stating half 1 alone re-installs the generalisation the
check removed.

**No harness-side pointer file**, and the gap is §Not established item 4 rather than a second
artifact to keep in sync.

## 4. Two counts in the ticket's own text that do not reproduce

Both recorded in the document at the point they would have been cited, with the enumeration
printed beside them. Both are the *count is a claim about a population* form promoted at the m4
close, arriving in the first document that would have carried it — which is why decision 1 is
listed in the carried-decisions table as **firing**, not merely as carried, and why decision 2's
pre-ratification verification pass is what found them.

**"29 section blocks and 41 invocation sites"** (R1's cost argument for BL-133 ruling (c)).
**29 is right**, two ways: `grep -c '  *section "'` → 29, and `$TARGET == "…"` takes 30 distinct
values of which one is `all`. **41 does not reproduce**: `run_agent` 28 + `run_orb` 8 + one
direct `mix aetheris run` = **37**. No population this ticket could construct yields 41. The
number is dropped; the argument does not need it.

**"the ten carried m4 decisions"** (§Ratified decisions' carry instruction). The enumeration
yields **fourteen in force** — **twelve unchanged (1–5, 7–12, 14) and two amended (6, 15)** —
against one under review (13, per R6) and one lapsed (16, per R10). Sixteen accounted for, none
dropped. Ten is not a subtraction from sixteen that lands anywhere natural. The table is printed
and the count is derived from it.

`[corrected 2026-08-08 (hc-b r1). This read "thirteen unchanged (1–12, 14) plus one as amended
(15)". The total was right; the sub-clause's predicate was false, because decision 6 sits inside
the range 1–12 and was amended at close-b — the very amendment this round's closure
pre-authorisation rests on. Derived by reading each row's **date cell**, the field that records
an amendment; decision 6's is the only one of the sixteen that carries one. Grepping for the word
"amended" instead returns 6, 7, 8 and 9, the last three because superseded-notes and
correct-in-place are their subject matter. Match by field, not by substring.]`

**A third, forwarded rather than acted on.** BL-077's Done-when says *"Audit all 31 cases"*;
the population is 29 by both derivations above. Recorded under R7 and in hc-d's ticket text, to
be corrected on the row when hc-d touches it. Whether 31 was right when the row was filed
(2026-08-02) is **not established** — this ticket did not check the file's history at that date,
and says so rather than assuming drift.

## 5. Deviations from the milestone/ticket text, and one hypothesis refuted

**hc-a Part 7(a)'s table named `Done-when` and a step-1 gate as §6 obligations. §6 has
neither.** Its anatomy is seven sections; the machine-checkable done-condition is §1.3, a
principle; the step-1 gate is m4 decision 3, cycle-local practice, which is the sole basis R8
carries it on. The document records the divergence rather than following it — listing the gate
as a methodology obligation would have manufactured an authority. The ticket asked for §6 to be
read directly and its own field names used; doing so is what surfaced this.

**The ticket offered *"m4's clause 3 may have none here"* as a hypothesis about §Close criteria.
It does not hold.** This round opens with four §Not established entries, one of which is the
gate hc-c turns on. Clause 3 has more to do here than at m4, not less. The document records the
refutation, not the hypothesis.

**Two rulings gained a recorded consequence the ticket did not name.** R9's stale pointer:
BL-077's §Suggested order entry still reads *"until BL-069 is re-armed"*, which decision 12
makes impossible — only the second disjunct is live, and R9 forbids reading the first as
licence. And §Rows filed gained a note on the backlog's closure convention, which turns out to be
**two shapes**: an in-row `**DONE <date> (<ticket>).**` paragraph (**9**, every one m4-cycle-dated)
and an older sibling `### BL-0NN — DONE <date> …` heading (**15 headings covering 17 rows**, dated
2026-07-23 to 2026-08-05). Not exclusive — BL-069 carries both. §Close criteria clause 2 is
**widened** to read both, and `## Suggested order` is named as a second status surface a sweep
must read; whether it currently agrees was **not checked** by this round.

`[corrected 2026-08-08 (hc-b r1). This paragraph read: "closure is a **sibling row**, not a
section inside a row … because m4's wording — *'checked for a DONE section'* — describes how the
record is spoken of rather than how it is stored, and a sweep looking for a heading inside a row
would find nothing and report clean." **Wrong, and wrong in the direction that faults m4.** All
three rows m4's clause 2 swept — BL-107, BL-121, BL-127 — use the **in-row** shape, which is
exactly what *"a DONE section"* describes. There was no wording defect and no vacuous
satisfaction available; m4's clause named the shape its own population uses, and its run was
sound. What is true is only that a second, older shape exists that no m4-cycle row uses. The r0
claim generalised from an enumeration of that older shape without checking the shape the rows
under discussion actually use — an observation over one subset stated as a claim about the class,
this time the author's rather than the reviewer's.]`

## 6. Anatomy authored ahead, per R12/R13

hc-c has all seven §6 sections with **exactly two** slots marked under R13 — the arm-dependent
half of `Touches`, and the post-arm half of `Done-check`. The gate half of hc-c's `Done-check`
**is** authored, in full, because it is authorable now and is owed regardless of which arm
lands: a stub-provider run **that spawns a worker**. The m4 demonstration of BL-105 used `list`,
which spawns none — which is exactly why `[sandbox]` routing has been unestablished since t1a,
and writing the gate against `list` again would reproduce the vacuity.

hc-c's `Runbook update rule` is written as engaged rather than as boilerplate: `--json`'s
observable semantics change, so §6 puts the entry in that ticket's `Touches`, not deferred.

hc-d and hc-e carry `Scope`, `Contract refs`, and the named question that gates the rest with
its resolver, plus the constraints recorded above so they are not rediscovered. Everything else
is `[R13: deferred to the section-scoped edit that opens the ticket, per R12]`.

## 7. Open, forwarded

- **`[sandbox]` routing** — §Not established 1. hc-c's gate.
- **The chaos gate in a clean store** — §Not established 2. Unowned; no ticket in this round
  needs it.
- **hc-a Part 4's transition claim** — §Not established 3. Rests on a transcription in neither
  repo; not re-derived, not acted on. BL-133's subject arriving inside the round that scopes
  BL-133.
- **The manifest inclusion sentence** — §Close criteria clause 6, owed at hc-e's boundary, both
  halves.
- **BL-102** asked for §Close criteria and is not closed by this ticket; its other two Done-when
  clauses (BL-084/BL-085 adjudication, the `CLAUDE.md` wording) are untouched.
