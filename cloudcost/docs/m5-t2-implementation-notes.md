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
