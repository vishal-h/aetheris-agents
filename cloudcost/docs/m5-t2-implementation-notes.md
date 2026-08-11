# m5 t2 — apply the ruling: implementation notes

`Authored 2026-08-10 at t2 r0, on top of 0b8804b (the r4 reviewer edit). Every figure is
derived in this session and says where. Line numbers appear only for claims about lines,
per m5-D1; every other citation names its section and quotes its text.`

**t2 applies m5-D2 and carries no ruling of its own.** Where this record reasons, it reasons
about *how* a requirement was discharged, never about whether it should have been.

---

## 1. Step-1 gate — ran first, passed on both arms

The gate stops on **moved**, not on **differs** — its own text says so, and t1's did not,
which is why t1 needed a mid-ticket ruling. The reference point is m5-D2's ratification,
**agents `a2d63d1`**, 2026-08-10.

### (a) The orchestrator still passes exactly one bundle on both STEP 3 forms

`cloudcost/agents/cloudcost_orchestrator.exs` §STEP 3 — *"Compose the report data (merges
cost + inventory + orphans, adds the MoM delta)"* — carries two mutually-exclusive forms,
introduced by *"If STEP 1 printed `files.costs`, use this form:"* and *"If STEP 1 did NOT
print `files.costs`, use this form instead — drop the flag and its value together, and
change nothing else:"*.

Flag counts, derived at HEAD `0b8804b` by counting each quoted flag token in each form's
`args:` array:

| Form | `--cost` | `--inventory` | `--orphans` | Bundles |
|---|---|---|---|---|
| full triple | 1 | 1 | 1 | **1** |
| degraded (no costs) | 0 | 1 | 1 | **1** |

Each passes **at most one of each flag**, so each yields exactly one bundle. The second
form is a pair rather than a triple — it passes no `--cost` at all — which t1's E2 already
recorded and which does not change the bundle count.

**Temporal test:** `git diff a2d63d1 HEAD -- cloudcost/agents/cloudcost_orchestrator.exs`
produces **0 lines**. The file has not moved since m5-D2 was ratified.

**Completeness of the search, stated because a zero is being relied on.**
`grep -rn "compose_report_data" cloudcost/agents/` returns four hits and only two are
invocations — the two `args:` arrays above; the other two are a pipeline comment and a
`load_prior_snapshots` note. So the two forms are the whole invocation surface in
`agents/`, and there is no third form the table omits.

### (b) C4's and C11's m4 t5b pointer blocks, present and unamended

Both present in `cloudcost/milestone.md` §Contracts at HEAD, found by the anchor
*"Pointer added m4 t5b"* — two hits, one in **C4** (*"read this paragraph with BL-131
beside it"*) and one in **C11** (*"same caveat as C4, and the fix has landed regardless"*).

**Temporal test:** `git diff a2d63d1 HEAD -- cloudcost/milestone.md` produces **0 lines**.
Unamended since m5-D2 was ratified.

### How a zero was established as absence

Three zeros are load-bearing in this ticket: the two temporal diffs above, and the
pre-edit `grep -n 'm5-D2'` over the three declaration artifacts (0, 0, 0). A zero from a
check that cannot reach its subject is worth nothing — §Promotion candidates' first entry
in `cloudcost/m5-n1-compose.md` is the standing rule.

- **The diffs**: the same `git diff a2d63d1 HEAD` invocation over
  `cloudcost/milestone.md` returns **non-empty** for other paths in the same range, so the
  command reaches the tree and an empty result is absence of change, not absence of
  reach. The path spellings are the same strings the edits later matched.
- **The greps**: the identical `grep -n` over each of the three files, with a control
  pattern known present in each (`C4|C11|^def |^## `), returned 22, 15 and 9 hits. So
  each file was opened and read, and `m5-D2: 0` is absence in a file the grep reached.
  After the edits the same greps return 1, 5 and 1 — the done-check's requirement.

**Both arms pass. Nothing has moved since m5-D2 was ratified**, so the ruling's factual
basis holds and t2 continued. No repair was attempted from inside the gate; nothing needed
one.

---

## 2. What changed, and where

| # | File | Change |
|---|---|---|
| 1 | `cloudcost/milestone.md` §Contracts **C4** | *Source-only by ruling* paragraph added; m4 t5b pointer block discharged in place |
| 2 | same, §Contracts **C11** | same pair |
| 3 | `cloudcost/scripts/compose_report_data.py` | module docstring only — one paragraph; **no executable line** |
| 4 | `cloudcost/runbook.md` | the *now-unreachable* sentence corrected |
| 5 | `docs/backlog-2026-06.md` | **BL-070**, **BL-121**, **BL-131** disposed; **BL-132**, **BL-119** annotated and left open |
| 6 | `cloudcost/m5-n1-compose.md` | **t2's row only**, per R19 |
| 7 | `cloudcost/docs/m5-t2-implementation-notes.md` | this file *(new)* |

**Seven changes across six paths** — rows 1 and 2 are both `cloudcost/milestone.md`, C4 and
C11 being separate contracts in one file. Nothing else: `git status --short` at the close
carries exactly those six paths, five modified and one untracked, and no other.
**No executable line changes anywhere**, and the declared interface does not change — the
manifest is untouched, out of scope by decision per `Do not generate`.

---

## 3. The contracts — amended, and their pointers discharged

**Both contracts' guarantees are unchanged.** C4 still withholds the grand total where
bundles disagree on currency; C11's cap still reports its truncation at any N. What each
now says differently is only what it claims about **reachability**. This is the ticket's
own instruction — *"Neither contract's guarantee changes; only what it says about
reachability"* — and it is the line the amendment was written against.

### C4

The amendment lands as a new **Source-only by ruling, not by accident** paragraph
immediately after the one-currency-scalar paragraph — that is, after
*"That is the honest output; it is also a surprise, and this sentence is the deliverable"*
— and immediately before the pointer block. It states the reachability finding, quotes the
orchestrator's two STEP 3 forms as the truth-maker, names **m5-D2** with its ruling
sentence quoted, and closes on the unchanged guarantee.

**Insertion point, per §Carried in's first carried rule.** The paragraph lands *between*
the policy paragraph and the pointer block, which is where it belongs: it is the amendment
the pointer deferred, so a reader meets the pointer's condition and its discharge in
sequence. No `Source:` or truth-maker unit is severed — C4's truth-maker blockquote sits
earlier in the contract, above the adapter-guarantee paragraph, and is untouched.

### C11

The same pair, in the same order, after the **Caps report their truncation** paragraph.
The amendment quotes the clause that makes the failure mode cross-provider —
*"capped after a global sort across all providers, so one provider can be absent from the
table entirely while another fills every row"* — and refers to C4's paragraph of the same
name rather than restating the derivation, so the two cannot drift apart.

### The pointers are discharged in place, not deleted

Per decision 7 and the ticket's explicit instruction. Each keeps its original text
verbatim and gains a dated `[Discharged 2026-08-10 at m5 t2 …]` block **inside the same
blockquote**, so the pointer and its discharge travel as one unit and a reader cannot meet
one without the other.

**One correction recorded in C4's discharge rather than left to be inherited.** The pointer
says the cross-provider path is *"reachable only through a CLI flag the orchestrator never
passes"*. m5 t1's **E1** established **three** routes, not one. That changes the route
count, **not** the reachability finding the pointer rests on — no orchestrator invocation
reaches any of the three — so the pointer is discharged rather than corrected, with the
route count named. The same wrong route count appears in BL-131's own derivation and is
corrected there too (§5).

---

## 4. The code — docstring only, proven twice

The module docstring gains one paragraph after *"Written to merge N providers; N=1 is the
DO-only m1 case…"* and before `Usage:`. It states the three things m5-D2 requires: that the
pipeline invokes the script at one bundle, that N>1 is a library-and-CLI capability the
pipeline does not use, and where the ruling lives.

**No executable line changed — established two ways, because the diff alone is the weaker
claim.**

1. **Line containment.** The module docstring spans lines **2–49** (from `ast`, not by
   eye). The diff's changed lines are **28–38**, eleven lines, all inside that span.
2. **AST equality.** Parsing HEAD's version and the working-tree version, dropping the
   docstring node from each, and comparing `ast.dump` output: **identical**. This is the
   stronger check — it would catch an edit that stayed inside the line range but changed
   code, and it makes the assertion independent of how the diff happened to hunk.

`[Both figures are claims about lines and about a specific tree state, stamped at the
working tree of this ticket's commit.]`

The offline spine confirms it behaviourally: **386 passed**, before and after.

---

## 5. The backlog — five rows, and the shape derived from the file

**The closure shape was derived, not invented**, as the ticket requires. The file uses two
shapes and this ticket used both, each where the file already uses it:

- **A sibling `### BL-NNN — DONE <date> (<ticket>) — <how>` heading** after the row's
  closing `---`, for a substantive cloudcost closure. Precedent: **BL-069**'s
  *"DONE 2026-08-06 (m4 t2) — closed by **retirement**, neither branch its Done-when
  offered"*. Used for **BL-070** and **BL-131**.
- **An inline bold `**<verb>ed <date> (<ticket>).**` block** appended inside the row, for
  an annotation or a partial disposition. Precedent: the rows' own
  *"**Annotated 2026-08-07 (m4 t5b).**"* and *"**DONE 2026-08-07 (m4 t5b).**"*. Used for
  **BL-121**, **BL-132** and **BL-119**.

Every disposition names **m5-D2**.

| Row | Disposition | State after |
|---|---|---|
| **BL-070** | cross-provider deletions **not taken** | **DONE** |
| **BL-121** | framing resolved — the consequence is correctly stated and source-only | **DONE** |
| **BL-131** | closed on the ruling: retained and bounded | **DONE** |
| **BL-132** | keeps its row; two known instances answered so the census need not re-derive them | **open** |
| **BL-119** | stays open, now unambiguously in scope; gains the BL-136 cross-reference | **open** |

### BL-070's Done-when clause 4 — the one place this ticket had to decide something

The row's Done-when had four clauses. Three dispose cleanly: the deletions are not taken;
the slug convergence was already discharged at m4 t5b independently; the
behaviour-unchanged test is moot, since it existed to bracket a deletion that is not
happening.

**Clause 4 does not.** It reads *"the four m1 open items those paths carried are marked
resolved-by-deletion"* — and with nothing deleted, nothing is resolved by deletion. The
clause is **unsatisfiable as written**, which is a state the row must not be left in.

It is **corrected in place inside BL-070's own disposition**, which is precedented in this
very row — its Done-when was amended once before, at m4 t5b, *"before any deletion was
made"*, on the same reasoning. The correction records that those items **stay open** with a
status they did not have before: the paths they name are reachable, uninvoked and declared.

**One of the four changes character and is named rather than buried.**
`cloudcost/milestone.md` §Open items carries *"Two of t4's rendered paths have never been
looked at by a human"* — the new-provider caveat and the multi-currency *"No combined
total"* rendering — and calls them *"unreachable while DO is the only provider"*. Under
m5-D2 they are **not unreachable; they are uninvoked**, and the eyeball is still owed by the
first ticket that makes either reachable from the pipeline.

**Why §Open items was not edited.** It is not in `Touches` — the ticket names
`cloudcost/milestone.md` *"§Contracts C4 and C11 only"*. Editing it would have been a
deviation. The correction is recorded in **BL-070**, which owns the clause, so the finding
has an executor rather than living in prose. **This is flagged for the reviewer as the one
item this ticket could see and could not itself close** (§8).

### The BL-136 cross-reference, and where it is not

Added to **BL-119**'s row only, per the ticket. BL-119's subject — a declared total with no
line items, silently dropped — is what BL-136's third requirement must handle in a reader
that never invokes compose, so the two are related and neither closes the other. The
cross-reference says exactly that, so a later reader does not treat one as duplicating the
other.

**Not added to BL-070 or BL-131**, per the instruction, and the reason holds on inspection:
this ticket disposes both, and a pointer into a disposed row is noise. Verified after the
edits — the only occurrences of `BL-136` in the five touched rows are the two inside
BL-119's new annotation.

---

## 6. The runbook, and the second-claim check the update rule demands

The corrected sentence is in the pre-provider-four paragraph. Before:

> DO's) — and **BL-070**, which retires the now-unreachable cross-provider merge
> code in `compose_report_data.py`.

After: the same paragraph, with the claim replaced by **reachable and uninvoked**, the
correction dated and the superseded wording quoted in place, and **m5-D2** named.

**The update rule requires a check for a second operator-visible claim resting on the same
premise.** It was run over the whole runbook — `grep -in "unreachable|cross-provider|merge"`
— and returned three sites. Two are **not** on this premise and were left alone, which is a
result rather than an omission:

- *"**One provider per run** (m2 decision H). … There is no cross-provider run and no
  combined report — two providers means two runs."* This rests on decision **H** — what the
  pipeline *does* — which m5-D2 leaves untouched. Still true.
- *"The history tree is per-provider on purpose. `load_prior_snapshots` globs every
  snapshot … which is m1's N-provider merge assumption."* A description of what that
  function does, and accurate. Not a reachability claim.

So one claim, one correction. **No second claim was found, and the search that would have
found one is stated here rather than asserted.**

---

## 7. Done-check

| # | Check | Result |
|---|---|---|
| 1 | `python3 -m pytest cloudcost/tests/ -v` | **386 passed**, 144.65s — identical to t1's recorded 386 |
| 2 | `grep -n 'm5-D2'` × 3 artifacts | **1 / 5 / 1** hits — all non-zero |
| 3 | `git diff HEAD -- …/compose_report_data.py` | 11 added lines, **all inside the module docstring**; AST outside it identical |
| 4 | `git status --short` | the **six** `Touches` paths — 5 `M`, 1 `??` — nothing else |

**Both anchors re-resolved at HEAD before running, per the check's own instruction.**
`cloudcost/runbook.md` §Offline tests reads
*"`python3 -m pytest cloudcost/tests/ -v      # no credentials; recorded DO + AWS + Linode fixtures`"*
and `CLAUDE.md` §Commands reads *"# From the aetheris-agents/ root"*. **Neither has moved**;
the command was run as the anchors say, from the repo root.

**On the test count.** t2 changes no executable line, so a differing count would be a
finding. It does not differ: **386 before the edits and 386 after**, both measured in this
session, and 386 is the figure t1's notes record. The pre-edit run is what makes the
post-edit run evidence rather than a coincidence.

---

## 8. Deviations, and one item flagged for the reviewer

**No deviations.** Every path that changed is in `Touches`; no executable line changed; the
manifest is untouched; nothing under `eduloka/`, `rig/` or `../aetheris/` was opened; no
contract other than C4 and C11 was amended; no reachability work was done over C1–C15.

**One item this ticket could see and could not close, flagged rather than carried
silently.** `cloudcost/milestone.md` §Open items describes the new-provider-caveat and
multi-currency rendering paths as *"unreachable while DO is the only provider"*. m5-D2
makes that wording wrong — they are uninvoked, not unreachable. §Open items is **not in
`Touches`**, so correcting it here would have been a deviation, and filing a new backlog row
would also have been outside `Touches`, which names five existing rows and BL-136.

It is recorded inside **BL-070**'s disposition, which owns the clause that pointed at those
items, so it has an owner and is not prose in a notes file. **The reviewer's call** is
whether that is sufficient or whether §Open items should be corrected in a follow-up. Named
here because a standing rule in both repos is that a deferred finding gets an executor in
the round it is deferred, and BL-070 is the executor this ticket could reach.

> **`[Corrected 2026-08-11 at the m5 record-correction edit. This is the FIRST of two
> occurrences of this claim in the round's records; the other carries a pointer here rather
> than a second full correction. The superseded wording is quoted below in the position it
> occupied and is not rewritten above, per decision 7 — this file is pushed, which is the
> condition the promoted correction rule's "however few people have read it" clause covers.]`**
>
> **Superseded:** *"a standing rule in both repos is that a deferred finding gets an executor
> in the round it is deferred"*.
>
> **The fact.** The rule stands in **one** repo — the agents `CLAUDE.md`, §Learning — BL-007,
> *"A deferred finding gets a backlog row in the same round it's deferred — prose in a packet
> or notes files nothing."* It is **not** in the harness `CLAUDE.md`, in that or any wording.
>
> **Truth-maker, re-derived at this edit rather than carried from any packet** — agents
> `d025971`, harness `0ed9068`, `grep -c` over each repo's `CLAUDE.md`:
>
> ```
> "deferred finding"                        harness=0   agents=1
> "backlog row"                             harness=0   agents=1
> "gets a backlog row in the same round"    harness=0   agents=1
>
> positive controls   "Source:"             harness=55  agents=35
>                     "CLAUDE.md"           harness=11  agents=8
>                     "ratified"            harness=7   agents=1
> negative control    "zzz-not-a-real-rule" harness=0   agents=0
> ```
>
> The positive controls fire in both files and the negative control in neither, so the three
> harness zeros are **absence** and not a broken search.
>
> **What this does not withdraw.** The claim's *point* is untouched: **a rule standing in one
> repo is still standing**, and it still bound this ticket — the session that wrote the
> sentence above works in the agents repo, where the rule is. Nothing that followed from it
> here changes. What was wrong is the rule's *reach*, asserted as two repos on no derivation;
> only the count is corrected.

---

## r1 — the claim corrected, the Touches amended, the review file

`Authored 2026-08-10 at t2 r1, on top of 305b3a1 (r0). Verdict on r0 was APPROVE with one
finding; nothing in §1–§7 above is re-run and no figure there is restated. Figures below are
derived at 305b3a1 or in the working tree this round produces, and each says which.`

### Gate on the instruction

| Claim | Resolved |
|---|---|
| `305b3a1` is t2 r0 and is held | ✓ HEAD at gate time, `docs(m5 t2): apply m5-D2 …` |
| Both trees clean | ✓ agents and `../aetheris` both `git status --porcelain` → empty |
| The harness is read-only and not committed to | ✓ `2ef0517057e4eda991a8da10ccba66650d1e65a2`, clean; r1 opens no harness file |
| agents will be **two ahead** of origin after r1 | ✓ `origin/main` is `0b8804b` (the r4 edit); one ahead at gate time, two after this commit |
| §Open items carries *"unreachable while DO is the only provider"* | ✓ quoted verbatim at W2 below, in the two-t4-rendered-paths item |
| t2's `Touches` names `cloudcost/milestone.md` *"§Contracts C4 and C11 only"* | ✓ quoted verbatim at W1 below |
| `docs/reviews/` convention | ✓ `m{N}-cloudcost-t{N}-review.md` across m2, m3 and m5 → `m5-cloudcost-t2-review.md` |

**All hold. Nothing in this prompt was wrong about repo state.**

### W1 — the reviewer amends `Touches`

**Bullet at HEAD, before:**

> - `cloudcost/milestone.md` — §Contracts **C4** and **C11** only: the cross-provider
>   clause in each, and each one's m4 t5b pointer block.

**After** — the instruction's replacement, verbatim:

> - `cloudcost/milestone.md` — §Contracts **C4** and **C11**: the cross-provider clause
>   in each, and each one's m4 t5b pointer block. **And §Open items**: any claim there
>   resting on the reachability premise **m5-D2** overturns.
>   *(§Open items added 2026-08-10 by the reviewer at t2 r1, on t2 r0's flag. The field
>   as authored named §Contracts only and missed a third site in the same file carrying
>   the same premise — the reviewer's scoping gap, not the ticket's.)*

**No other field changed.** The bullet keeps its position — first in the list, before
`cloudcost/scripts/compose_report_data.py` — so nothing is re-attributed and the list's order
still tracks the order the ticket applies them in. `Do not generate`, `Scope`, `Contract refs`,
the runbook rule, the done-check and the claude-code prompt are untouched.

**This is the authority for W2 and W3, and it is dated before them.** r0 declined to edit §Open
items because it was outside `Touches`; that refusal is not reversed here, it is made unnecessary.
A ticket's scoping stays authoritative over a ticket's judgement — what changed is the scoping.

### W2 — the claim corrected

**Unit at HEAD, quoted before the edit** (the clause, in the two-t4-rendered-paths item):

> browser. Correct for m1 — both are unreachable while DO is the only provider — but the
> flex-`gap` defect was invisible to every assertion and to one of two rendering engines, so
> the first ticket that makes either path reachable owes it the same two-minute look.

**After** — same shape as r0 gave the runbook: superseded wording quoted in place, correction
dated, **m5-D2** named, accurate claim stated, and the status carried.

> browser. **Both are reachable and uninvoked** *(corrected m5 t2 r1, 2026-08-10 — this
> clause read "Correct for m1 — both are unreachable while DO is the only provider —")*: the
> flex-`gap` defect was invisible to every assertion and to one of two rendering engines, so
> the first ticket that makes either path reachable **from the pipeline** owes it the same
> two-minute look.

followed by two new paragraphs and an extended `Source:` line — the reachability paragraph
(*"Reachability here is not a function of provider count"*), the status paragraph (*"The item
stays open and the eyeball is still owed"*), and the stamp naming the r1 correction and the
`Touches` amendment that authorised it.

**Three things the correction does that a wording fix would not**, which is why the item grew:

1. **It names the mechanism.** The old clause made reachability a function of **provider count**.
   It is not: all three routes to the N>1 surface are open today with three providers shipping,
   and none is taken by an orchestrator invocation. Provider count and reachability are
   independent, and the old wording tied them.
2. **It kills the schedule, not just the adjective.** *"View them at fan-out"* implied a fan-out
   would arrive and open these paths. Under decision **H** provider four is a fourth solo run, so
   no future provider opens them. The superseded clause restated the *"live at the first fan-out"*
   reading that **E1** killed, as a premise — which is the reviewer's F1 in one sentence.
3. **It carries the obligation forward rather than closing it.** The eyeball is still owed. What
   changes is the trigger: **the first ticket that makes either path reachable from the pipeline**,
   which is no ticket now scheduled. An item whose trigger can never fire would be worse than the
   wrong wording, so the trigger is stated in terms that can.

**Insertion points, per §Carried in's first carried rule.** The correction is in-clause; the two
new paragraphs land **after the item's prose and before its `Source:` line**, and the `Source:`
line itself is **extended, not replaced** — its original sentence (*"t4 review r0, human browser
check"*) stands first and the r1 stamp follows it. No attribution is severed and the item's
original provenance still reads first.

**Nothing else in §Open items changed at W2, and no other section of the file was opened at W2.**

### W3 — the second-claim sweep over `cloudcost/milestone.md`

**(a) Population and vocabulary.** The premise m5-D2 overturns is *the cross-provider compose
surface is not reachable*. Claims can spell that eighteen ways, swept case-insensitively over the
whole file:

`unreachabl` · `reachabl` · `dormant` · `dead code` · `latent` · `fan-out`/`fanout` · `N>1` ·
`N≥2` · `cross-provider` · `cross-currency` · `multi-currency` · `combined total` · `N-merge` ·
`N provider` · `input-dir` · `discover_bundles` · `second provider` · `first fan-out`

**42 hits.** The enumeration is printed in full in the review packet; it is not reproduced here,
because a list published twice is a list that can diverge.

**(b) Positive control.** No arm of this sweep returned zero, so the zero-control question does not
arise in its usual form. The control that does apply is whether the vocabulary can **reach a claim
of the kind sought**: it independently re-found both sites already known to rest on the premise —
C4's and C11's paragraphs corrected at r0, and the §Open items clause F1 names — without either
being searched for by name. A vocabulary that missed those would have been reporting its own
blind spot as a clean sweep.

**(c) Classification.** Of 42 hits, **one** rests on the overturned premise and was not already
corrected. The rest divide into four kinds, none of them reachability claims about the compose
surface:

| Kind | Example | Why it is not on the premise |
|---|---|---|
| **Schema vocabulary** | *"Every **first-class** (top-level) field is part of the cross-provider contract"*; *"cross-provider priors"* | Says which fields are canonical, not what any invocation reaches |
| **Decision H, what the pipeline *does*** | §Ticket set t3's *"merge **N providers** (trivial at N=1)"*; t4's *"At N≥2, the MoM headline must render its new-provider caveat"* | Describes the code's capability, which m5-D2 retains — still true |
| **Already corrected at r0 or r1** | C4's and C11's *Source-only by ruling* paragraphs and discharged pointers; the W2 clause | Same premise, already handled |
| **Unrelated reachability** | *"It is unreachable on all three current adapters"* (`generated_at` fallback, D17); *"latent on a hypothetical provider, exhibited by none of the three"* (C8 note) | Adapter data coverage and provider divergence — different subject, same words |

**The one hit, corrected** — §Open items, the cross-currency aggregation item. Quoted before:

> Options: withhold like `grand_total` does, or emit each per currency. **Latent while m1 is
> DO-only single-currency; live at the first fan-out.**

This is F1's finding a second time and in a sharper form: *"live at the first fan-out"* is not a
description here but a **premise about four named code sites**, and those four sites are exactly
BL-070's *"four cross-currency aggregation sites"* whose deletion this ticket disposed **not
taken**. Corrected in place, same shape, naming m5-D2 and decision H, and recording that the
single-currency condition now holds for a different reason than the one given — not *"m1 is
DO-only"* (three adapters ship) but all three declaring `USD`, which §Contracts **C4** states.
That is a fact about adapters, not about reachability, and the correction says so rather than
letting a true conclusion keep resting on a false premise. **In §Open items, so inside the amended
`Touches`.**

**(d) Reported, not fixed — two, and the reviewer's call.** Both are in §Open items and both are
staleness, but **neither rests on the premise m5-D2 overturns**, which is the only thing the
amended bullet authorises correcting. Fixing them would be exceeding the scoping at the very round
whose subject is that scoping is authoritative.

1. **The recency-modifier item** — *"Unreachable while DO is the only provider (the field is
   null), so it lands with the first adapter that populates it"*
   (`detect_orphans.py`, `modifier_recent_activity`). The **wording collides** with F1's, and the
   mechanism does not: this is unreachable because DO emits no `last_activity_at`, which is
   adapter data coverage. m5-D2 says nothing about it. **But *"while DO is the only provider"* is
   stale on its own terms** — AWS and Linode ship — and whether either populates the field is not
   established in this file and was not established here, because doing so means reading two
   adapters, which is outside this ticket in every direction.
2. **The orphan-filename item** — *"`detect_orphans.py` writes `orphan_candidates_{period}.json`,
   which collides at N≥2 in one directory … **Lands with the second adapter.**"* The collision
   analysis is about output filenames under one directory, not about the compose surface. The
   **schedule** is stale in the same way as (1): the second adapter landed at m2 and the third at
   m3. Whether the collision was handled by per-provider output dirs in the interim is not
   established here.

**Both are the same shape** — an item whose trigger has already fired, or whose framing predates
two adapters — and both would be found by a §Open items freshness census that nothing currently
owns. Named together so the reviewer can decide once rather than twice.

### W5(a) — t2's row, rebuilt for readability

The row had accreted across four edits — authored, completed at the ruling edit, amended at the
reviewer edit, opened-and-applied at r0 — and was the longest in the table.

**No fact is dropped.** The rebuild is structural: the row is reorganised into labelled clauses in
the order **state → gate → what landed → r1 → provenance**, and phrasing is compressed where two
sentences carried one fact.

**What was compressed, named rather than left to be diffed:**

- The four authoring/amendment events are stated once as a provenance clause rather than
  re-narrated in sequence; every date, editor and record-file reference survives.
- The r0 gate result keeps both arms and both empty diffs, stated as one clause instead of two
  sentences.
- The five backlog dispositions keep all five row identifiers and all five outcomes, as a list
  rather than as prose.
- The r1 additions are appended as their own clause rather than interleaved into r0's.

**Nothing in the row is new information** except r1's own clause. Every figure it carries — the
386, the route counts, the row outcomes — is unchanged from r0's row and is not re-derived by the
rebuild.

### r1 — deviations

**One, named because `Touches` requires exactly that.** The field ends *"Nothing else. Any other
path that changes is a deviation and is named in the implementation notes"* — so this is the named
form, not an unnamed one.

`docs/reviews/m5-cloudcost-t2-review.md` **is not in `Touches`** and is created by this round. It
lands on two authorities, neither of them this ticket's judgement: the reviewer's explicit W4
instruction at r1, and the standing review-file obligation the round document states in its own
§Review files — methodology **§1 principle 4** and **§8**, both unscoped, *"which are the sections
R2 grounds itself in"*, R2's own text being scoped to `hc-*` tickets and so not literally reaching
this round.

**Precedent in this round, checked rather than assumed:** t1's `Touches` names two paths and
neither is a review file, yet t1 r1 produced `docs/reviews/m5-cloudcost-t1-review.md` and t1's row
records it. So a review file landing outside `Touches` is this round's established practice, and
r1 follows it rather than setting it.

**Why it is not folded into `Touches` here.** r1's one authorised amendment is the §Open items
addition at W1, and the instruction says *"Change no other field."* Adding a seventh path would be
a second amendment, and the round whose subject is that a ticket's scoping is authoritative over a
ticket's judgement is the wrong round to widen a scoping unasked. **The reviewer's call** whether
`Touches` should carry it.

**No other deviation.** No executable line changed at r1 — `compose_report_data.py` is
**byte-identical** to `305b3a1`, confirmed by an empty diff and by AST equality; the harness was
not opened; no contract other than C4 and C11 is amended; no reachability work was done over
C1–C15; and the two staleness items W3(d) surfaced are reported rather than fixed, being outside
what the amended `Touches` authorises.
