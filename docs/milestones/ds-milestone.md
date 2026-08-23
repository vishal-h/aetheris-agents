# ds — declared status

**Status:** CLOSED 2026-08-21. Opened 2026-08-17. The close is §The close, below.

> Canonical for this cycle. Scope changes are edited here first. This document is
> AUTHORITY; the two `claude/`-namespaced briefs that produced it are demoted to
> history and keep superseded-by pointers.

`Measurement stamp: every claim in this document about repository state was
resolved at agents df2600f. A claim here is a snapshot with no invalidation;
re-verify at HEAD before relying on one. Where a figure would be needed, this
document names the command instead. Stage 1 of this cycle's open re-resolved
every claim in this document against the tree and found five wrong; those five
are corrected here, and the corrections are the only content in this file not
authored before the tree was read.`

## What this cycle is

Four places in this project infer status from shape rather than declaring it: a
use case's dormancy from whether a directory scan still finds it, a backlog row's
disposition from three different prose forms, an artifact's provenance from
whatever ran last, and a cancelled run's state from a killed child process. Each
inference is indistinguishable from the mechanism being broken. `ds` — declared
status — replaces inference with a declared, checkable field in the first three.

The key is deliberately not `m7`. That key is taken in this repo by docbuilder's
closed offer-letter milestone, and the milestone namespace is use-case-keyed while
this cycle spans no use case. The established form for a cycle of that kind is a
short opaque key: `hc`, `gc`, both in this directory.

## Authority and history

Three documents in the project-knowledge store produced this one. **None of
them resolves from either repository, and nothing in this document depends
on reading them.** They are `claude/`-namespaced, which BL-143's ruling of
2026-08-16 establishes is outside the export set by construction; the store
is claude-ui's surface and the tree is claude-code's, and there is no path
between them except a prompt. They are listed as provenance, not as
contract refs — a normative pointer into a surface the reader cannot open
is the unresolvable-reference defect BL-162 was filed for.

- `claude/aetheris-agents--m7-shape-brief.md` — how this cycle's shape was
  reached, including the rulings of 2026-08-16/17 and the amendments made
  at the open. Superseded by this document; not deleted, demoted.
- `claude/aetheris-agents--use-case-registry-brief.md` — the registry
  ruling. **Its content is landed in t1a below rather than cited**, for the
  reason above and because the brief itself ruled that its content lands in
  t1a's section.
- `claude/aetheris-agents--m7-scout-findings.md` — a read-only scout's
  findings, recorded because a finding that exists only in a conversation
  is the same defect class. Discharged by the appends to BL-150 and BL-151
  in this cycle's opening commit; nothing in it is load-bearing after that.

## How the cycle is run — the GitHub trial

This cycle is the trial of the sprint model. It is not a ticket; it is how the
cycle is run, and process changes get no round of their own.

- **Issues for this cycle's ticket set only. Nothing historical is migrated.**
- **A GitHub Project spanning both repos is the container.** No GitHub milestones
  are used. Milestones are per-repo, and the first ticket that sections the
  harness while another sections agents has no single milestone that can hold
  both. A Project and a milestone both claiming to be the boundary would be two
  surfaces that must agree.
- **Issues are filed in the repo whose code changes.** Held for the trial rather
  than consolidated into one repo. Consolidating them would make a single-repo
  milestone sufficient, which dissolves the constraint the Project exists to
  answer — a trial run in the arrangement you would fall back to says nothing
  about the arrangement being tested. Whether to consolidate is decided AT THE
  CLOSE, on the evidence of verdicts A and B. **Tiebreak for a ticket that
  changes both repos:** the issue is filed in the repo carrying the ticket's
  primary artifact, the ticket's Touches repo-qualifies every path in both, and
  any commit in the other repo references the issue in the fully qualified
  `owner/repo#N` form, because a bare `#N` does not resolve across
  repositories. **t1b is the first live test of this tiebreak** — its primary
  artifact is the backlog, in agents, while its breaking change is in the
  harness. If the tiebreak proves unworkable there, that is evidence for verdict
  A and it is recorded, not patched around.
- **A Project is addressed owner-qualified, `--owner vishal-h`. The constraint
  that forced `@me` is discharged.** It arose from two authenticated `gh` tokens
  with disjoint gaps — one carrying `project` without `read:org`, the other the
  reverse — so no single token could both address the owner and read the org.
  What resolved it was not a new personal access token. `GITHUB_TOKEN` was
  removed from the shell profile, so `gh` stopped being shadowed by it and fell
  back to the keyring OAuth token; that token was then refreshed additively —
  `gh auth refresh -h github.com -s project`, 2026-08-19 — and now holds `gist`,
  `project`, `read:org`, `repo`, `workflow`. Recorded rather than left to resolve:
  `gh project list --owner vishal-h` returns rows, where it previously returned
  `unknown owner type` and then, after a first partial re-mint, a `read:project`
  scope error. `@me` resolves to the same owner and is no longer the required
  form.
- **Keep the Project minimal.** Fields and automation are their own maintenance
  surface and nothing yet justifies them.
- **R23 is preserved, not relaxed.** GitHub Issues has no shape for a thing that
  is true, filed, and deliberately not scheduled. Findings during this cycle land
  on the standing rows — BL-150 for documentation-system findings (R23), BL-151
  for code findings (R26) — and get an issue only if someone schedules them. If
  the trial cannot hold that, the trial has failed and the finding is worth more
  than the tooling.

## Close criteria

1. Every ticket passes its done-check.
2. Zero unresolved blocking findings.
3. `drift_check --strict` run POST-COMMIT for any manifest-tracked edit, with the
   expected `project_knowledge` staleness WARNs named rather than chased.
4. The §7 learning promotion committed and **verified by opening the file**,
   including the census of prior cycles' promotion claims.
5. **Trial verdict A — did anything read the Project?** At the close, name each
   decision taken during this cycle by consulting the Project rather than this
   document. If that list is empty while the list of acts taken solely to keep
   the Project current is not, the Project is a second surface with no reader and
   the trial has failed on this criterion.
   **Its instrument:** each ds ticket's implementation notes carry one line
   stating whether the Project was consulted and for what, and that line is this
   criterion's evidence. The ground is that a criterion whose evidence is nobody's
   recollection is answered "no finding" by default at the close — which is
   precisely the failure this criterion exists to detect, so it would report clean
   in the one state it was written to catch. One line per ticket, written when the
   ticket runs and not reconstructed at the close; "not consulted" is a valid and
   expected value, and a ticket that omits the line leaves the criterion
   unanswerable rather than answered no.
6. **Trial verdict B — did the mirror drift, and did anything catch it?** At
   the close, compare each issue body against its ticket section **at HEAD**,
   with one exclusion on each side: the body's trailing backlink block, and the
   section's `**Issue.**` field. Both are the join between this document and
   the tracker rather than ticket content, and excluding them symmetrically is
   what makes the comparison answerable in both directions — an issue edited
   away from the document fails it, and the document edited without re-syncing
   the issue fails it too. Any other divergence fails it.
   `[Defined this way at the container's landing, 2026-08-19, replacing "the
   section at this document's commit". That earlier form was answerable only
   against the commit each backlink pins, so it detects an issue-side edit and
   is structurally blind to the document moving ahead — which is the drift
   methodology §8's re-sync rule exists for, and the likelier of the two. The
   five bodies were cut before the `**Issue.**` fields existed and cannot carry
   their own numbers, so the exclusion is also what lets a pre-E1 body and a
   post-E1 section compare clean without re-syncing five issues to say nothing
   new.]`
   No executable in either repo invokes `gh` — no script, test, CI workflow or
   agent file; the hits that exist are prose and operator instructions — so
   this sync is by hand throughout, and a by-hand mirror with no keeper is
   methodology §9's own anti-pattern.
7. **The R23 verdict.** Count findings that landed on BL-150/BL-151 against
   findings that became issues. A finding that became an issue only because the
   tooling had no other shape for it fails this criterion.
8. **The cross-repo arm.** Two tickets are harness-side: t3, whose whole
   subject is a harness write, and t1b, which must edit harness `sprint.sh` or
   break it. That is what exercises the Project's cross-repo claim. If neither
   runs, the close states that the cross-repo arm was never exercised and that
   the trial says nothing about it. Silence on it is forbidden.

Criteria 5, 6 and 7 are decided by the arbiter at the close and recorded as dated
lines in `docs/milestones/hc-consolidation.md`, per R25.

## What is not checked, stated rather than worked around

`drift_check.py`'s `milestone_status` check globs `docs/rig/milestones/` and only
its subdirectories. This document is invisible to it. It is not relocated under a
Rig tree to acquire a check it has no business passing. Nothing checks the Project
either. Verdicts A and B are therefore human observations by construction, which
is why they are written down before the cycle runs rather than after it.

## Deviation from methodology §6, stated with its reason

§6 requires each ticket section to carry the literal claude-code prompt. This
document does not. Five prompts authored before any of the five sessions runs are
five prompts written at maximum distance from their evidence, and §11's own
finding is that a round's defects sit in the sentences its author stated flat.
Each cc:prompt is authored at ticket time instead. A divergence is closed by
changing the document or the practice and is never left standing — agents
`CLAUDE.md` §Learning — m3-docbuilder, *"a divergence is closed by changing
code *or* the doc, never left as a silent mismatch"* — so this is a candidate
for disposition at the close. `[The pointer here read "§1.1" until stage 1
resolved it: §1 item 1 states that the milestone doc is canonical and that
scope changes are edited into it first. It does not state the divergence
rule. Cited-means-read; the invariant held and the pointer did not.]`

## Tickets

### t0 — the backlog gets a status field

**Issue.** `vishal-h/aetheris-agents#75`

**Scope.** Every `### BL-` row carries an explicit status field at a fixed
position — its own line, immediately after the row's title heading. Rows whose
status cannot be derived unambiguously are adjudicated by the arbiter, never
guessed. What exists after this ticket: a machine-readable predicate for
*terminal*, which t1b requires and which does not exist today.

**The status expressions this file already has — five, and the enumeration is
what was short.** An earlier draft of this section named three ("a heading
suffix, an inline bold on the Priority line, and nothing at all"). The clause was
right and its enumeration short, which agents `CLAUDE.md` §Learning —
m6-cloudcost rules is repaired **by extending the enumeration, not by adding a
second clause**. Four are in-row and the fifth is not in a row at all:

1. a status word in the `###` heading, after the em dash;
2. a standalone `**Status:**` line in the body, at an unbounded offset from the
   heading (BL-151, `2026-08-17` — BL-001's sits nineteen lines below it);
3. a bold `**DONE …**` / `**CLOSED …**` body paragraph;
4. a status bolded onto the `**Size:** · **Priority:**` metadata line;
5. the **`## Suggested order` ✔ table** — a second *surface*, not a fifth in-row
   form. BL-145 filed it and the arbiter **ruled it retired on 2026-08-12**:
   the row bodies are authoritative.

And most rows express status none of these ways at all. Absence is the sixth
thing a reader meets and the reason two derivations over this file return a
bracket rather than a number.

**ADD, never MOVE.** No legacy status expression is removed, reworded or
relocated by this ticket. The field is the **declaration**; the body keeps the
**record**. The ground is that the two do different work: a normalisation that
rewrote the bodies would destroy the dated prose that says *how* a row closed, in
the same commit that claims only to have made the file queryable — and a reader
could not afterwards tell a lossless move from a lossy one. That is also why the
field can be coarse. It answers *is this row terminal*, and nothing else; the body
answers everything else and is not asked to.

**The vocabulary, closed.** `OPEN`, `DONE`, `UNRULED`. **`DONE` is the only
terminal value.** `CLOSED` merges into `DONE` — the file uses both for one state
and a two-word vocabulary for one state is the trap this ticket exists to remove.
`folded` maps to `DONE`. Absence of any legacy expression means `OPEN`.
**`UNRULED` is for a row the arbiter has not settled, and it is NOT terminal** —
a row with an open remainder must not archive at t1b, which is the whole reason
the value exists rather than being rounded to either neighbour.
**`OPEN` is adopted with zero precedent in this file**: at the commit this
section is written against there is no `OPEN` in any heading and no
`**Status:** Open` anywhere, from
`grep -cE '^### BL-[^—]*— *OPEN' docs/backlog-2026-06.md` and
`grep -cE '^\*\*Status:\*\* *Open' docs/backlog-2026-06.md`. It is a new word,
and it is named as new so a later reader does not go looking for the convention
it came from.

**Why it is its own ticket.** t1b is specified as a purely mechanical
open-versus-archive split. Two derivations over the current file bracket the open
set rather than returning it, so the predicate the split turns on is undefined.
Normalisation is a third kind of change — neither the structural rejig nor the
triage pass — and folding it into the commit that must also carry the `BL-nnn`
resolution check is how *"if the check cannot land with the split, do not split"*
gets satisfied on paper while failing in substance. Labelled t0 rather than
renumbering, on the precedent of BL-153 s0 and BL-007 t0, so no already-issued
label changes what it refers to.

**Contract refs.** `hc-consolidation.md` R23, R26. Agents `CLAUDE.md` §Learning —
BL-152, the rule that a count in prose carries the command that reproduces it.
Agents `CLAUDE.md` §Learning — m6-cloudcost, the incomplete-enumeration rule this
section's own first paragraph is an instance of. BL-145's ruling of 2026-08-12,
BL-146, BL-150 and BL-151 for the parser constraints.

**Touches.** `docs/backlog-2026-06.md`. Plus whatever parses that file — RESOLVE
before editing, by kind of change and not by file class: scripts, tests, checks,
sprint cases, docs that quote a command against it, and anything that depends on
the row-heading shape. An unlisted toucher is the recurring defect here.

**Do not generate.** No re-prioritising, no merging, no superseding, no re-reading
of a row's merits. That is the triage pass and it runs after t1b. A row that moves
in the same pass that re-judges it cannot later be told apart.

**The ✔ table gets a retirement marker, not a removal.** This ticket adds one line
at the head of `## Suggested order` pointing at BL-145's ruling and naming the
row `**Status:**` field as authoritative. It does not touch the table. **Retiring
the table is BL-145's execution and stays BL-145's** — that row also owes a
decision about the sequencing opinion the table carries and the bodies do not,
and a ticket that deleted the table here would take that decision by default
while claiming to have taken none.

**Done-check.** A **test under `tests/`**, not a standalone script. It (a) fails
if any row id lacks the field or carries it more than once, (b) fails on a value
outside the vocabulary rather than passing it silently, and (c) prints the open
set as a single number with the command that reproduces it — derived by the same
parser the test uses, never a hardcoded literal (BL-164's class). The bracket
collapsing to a number IS the done-check. `[The wording here was "a committed
script" until this commit — a third form beside this section's other two, closed
in favour of the test. The ground is BL-150's `2026-08-17` off-territory-gate
entry: a new standalone gate is one more thing *every existing gate runs at
ticket boundaries* binds and that nothing routinely runs, whereas a test under
`tests/` is inside the whole-suite gate — `python3 -m pytest -q -m "not
integration and not dormant"` from the repo root — for free, and is not
`integration` by `pytest.ini`'s own criterion, since it does its work in a fresh
clone at this commit, offline, with no sibling repo present.]`

**What this commit costs, stated rather than discovered later.** Inserting a line
into every row shifts every absolute line-number citation **into**
`docs/backlog-2026-06.md` below the first insertion — which is all of them. Two
populations, and only one is mechanically derivable:

- **External**, filename-anchored: **31** citation tokens on **30** lines across
  **17** files, from
  `grep -rInE 'backlog-2026-06\.md:[0-9]+' --include=*.md --include=*.py --include=*.sh --include=*.exs --include=*.ex --include=*.rs --include=*.ts --include=*.tsx . ../aetheris | grep -v '^docs/backlog-2026-06\.md:'`
  (tokens from `| grep -oE 'backlog-2026-06\.md:[0-9]+' | wc -l`, files from
  `| sed -E 's/:.*//' | sort -u | wc -l`), derived at agents `1deb832`.

  > **[Corrected 2026-08-23 at BL-182's close.** The command above was **wrong when written**;
  > the figures it produced were **right**, and they stand. Its last stage removes
  > self-references with `grep -v '^docs/backlog-2026-06\.md:'`, anchored at `^docs/`. A recursive
  > search rooted at `.` emits matched paths **unprefixed** under ugrep and **`./`-prefixed** under
  > GNU grep — so that filter removes the backlog file's own citations under one tool and silently
  > removes nothing under the other. Re-run at this close it returns **31** lines under ugrep and
  > **33** under GNU grep, **both exiting 0 with empty stderr**: a reader gets a different
  > population than the author did, and nothing tells them. The recorded figures were derived
  > under the tool where the filter worked, so they are not in question; the command's
  > reproducibility is. **The corrected form, which returns byte-identical output under either
  > tool because git's search engine is not reached through a shell name:**
  >
  > ```
  > git grep -InE 'backlog-2026-06\.md:[0-9]+' -- '*.md' '*.py' '*.sh' '*.exs' '*.ex' '*.rs' '*.ts' '*.tsx' ':!docs/backlog-2026-06.md'
  > git -C ../aetheris grep -InE 'backlog-2026-06\.md:[0-9]+' -- '*.md' '*.py' '*.sh' '*.exs' '*.ex' '*.rs' '*.ts' '*.tsx'
  > ```
  >
  > The self-reference exclusion moves out of a fragile output filter and into git's own pathspec,
  > so there is no path prefix left to anchor against. Verified both ways at this close:
  > byte-identical stdout, identical md5, identical exit code. Recorded per **R32** — the original
  > command is not rewritten. See **BL-182**. **]**
- **In-file, and NOT derivable by any command.** The file carries **169** bare
  `` `:NNN` `` anchors (`` grep -oE '`:[0-9]+' docs/backlog-2026-06.md | wc -l ``)
  plus **2** filename-qualified self-references, but a bare anchor binds to
  whichever file was last named, which is frequently **not** this one — **most
  `:NNN`-shaped tokens in the file point at some other source**, so a count of
  colon-number tokens bounds the self-anchor population from above and does not
  measure it (`` grep -oE ':[0-9]+' <file> | wc -l `` against the backticked form
  above, for whatever the two return today). **154** bare
  anchors sit on lines naming no other file, which is an upper bound on the
  self-anchors and a loose one, since a continuation's antecedent can be on a
  previous line. Stated as a bound rather than a count, per agents `CLAUDE.md`
  §Learning — BL-007, *a count is a claim about a population*.

  `[De-numeralised at ds t1b, 2026-08-19. This clause read "— of **448**
  `:NNN`-shaped tokens in the file most target other sources", and **448 does not
  reproduce**: at t0's own stamped commit `1deb832` the eight nearest patterns return
  520 / 520 / 517 / 509 / 503 / 499 / 169 / 120 / 8 and none of them 448. The
  argument never needed the figure — it is that a token count over-counts — so the
  figure is replaced by the argument, per BL-152's **a count recorded in prose
  carries the command that reproduces it, or it decays into a claim**. The
  demonstration sits inside this one paragraph: the neighbouring **169** shipped with
  its command and reproduces exactly at both `1deb832` and `b98be4d`; **448** shipped
  without one and cannot be recovered. **Not a claim that 448 was wrong** — only that
  nothing published makes it checkable.]`

  `[Superseded as a measurement at ds t1b, 2026-08-19, and t0's stamped figures are
  kept rather than restated. t1b split the backlog, so the command above addresses
  the OPEN file alone and the population now lives across two files. Over the union
  at this commit it returns **132** for `backlog-2026-06.md`, **59** for
  `backlog-2026-06-closed.md` and **191** concatenated — more than 169 because this
  same commit's BL-150 and BL-133 appends added anchors of their own. That is *a
  census recorded inside the document it censuses*, live. Re-derive over the union
  rather than reading any of these three.]`

**t1b's relocation will invalidate the path-based citations too**, so the cost is
taken **once** here rather than twice: this ticket does not re-pin anything, and
the re-pinning belongs to whichever ticket moves the file. Recorded so the next
reader knows the staleness is expected rather than a regression.

### t1a — the use-case registry

**Issue.** `vishal-h/aetheris-agents#76`

**Scope.** Five items: the registry file; the drift check that every use-case
directory has a row and every row a directory; the doc-enumeration check, which
CHECKS documents against the registry and never regenerates prose into them; gc
t1's census carrying gc t3's discharge predicate; and boxy-pipeline's dormancy
beyond the test apparatus as the registry's first consumer.

**The ruling, landed here rather than cited.** *Declare status in a committed
registry; do not encode it in the directory layout.* The identifier is the
address and the path is never load-bearing — the same ruling already given for
the backlog split, applied to a second object. A directory move makes the shape
of the tree the declaration, and nothing checks the shape of the tree; it works
by accident rather than by declaration, since anything that discovers use cases
by scanning directories silently stops seeing a moved one, which is
indistinguishable from the discovery being broken. Dormancy also ends, and a
status flip is one line where a move back is a second wall of renames. **The
move is demoted, not forbidden**: once status lives in the registry, relocating
a dormant use case is cosmetics and can be taken on its own merits for the
ergonomics of `ls`. It must never be taken as the mechanism.

**What the registry carries.** One row per use case: status, the date the status
was set, the reason stated as business state rather than test mechanics, and
**the condition for return** — something a future reader can evaluate. Not
"disabled"; "dormant since <date>, runs again when <x>."

**Three constraints, binding.**

1. **Dormant tests must still collect.** Deselect at run time; never stop
   importing. A use case whose tests no longer collect is one nobody notices has
   rotted. Collectability requires the code to stay somewhere `sys.path`
   reaches, so any later directory move is designed against whatever BL-152
   established about rootdir and `sys.path` resolution.
2. **Check first; generate only what is wholly derived.** A purely derived
   document — a use-case index — may be generated. A document mixing prose and
   enumeration, such as a runbook or a `CLAUDE.md`, is **checked and failed**,
   never rewritten by a script that has to locate a list inside paragraphs. The
   precedent is the capability matrix, which as a generated artifact with
   consumers and no gate went not merely stale but unstable.
   **The precedent has moved, and only half of it is still live.** `BL-067` (the
   derived block computed in the LLM) and `BL-068` (a full regen destroying
   hand-curated sections) are both **DONE** — the arithmetic and destructive-regen
   halves are fixed, and citing the precedent whole would cite a fixed defect. What
   remains is the **ungated input**: nothing compares `assemble_matrix.SECTIONS`
   against the tree, so the matrix can be internally consistent and enumerate the
   wrong set. That half is what t1a closes, and it is the only half constraint 2
   should be read as resting on.
3. **Dormancy and test-mechanics exclusions do not share a mechanism.** The two
   markers mean different things and have different re-entry conditions, and a
   reader must be able to tell them apart without asking. The registry is the
   dormancy marker's source, or at minimum the check proves the two agree.

**The `SECTIONS` predicate, ruled.** `assemble_matrix.SECTIONS` is compared against the
registry **filtered to agent-bearing use cases** — those with at least one `<uc>/agents/*.exs` —
not against the registry whole. **The ground, and it is not convenience:** the capability
matrix's unit is an *agent*. Each section is produced by an `agents/capability_matrix_<key>.exs`
run, and the assembled document is read whole into the planner's system prompt. Comparing
`SECTIONS` to the full registry would oblige someone to author a section agent for a **dormant**
use case — adding planner capability for paused work, and asserting a capability nothing can
currently exercise. Under the predicate, `boxy-pipeline`'s omission from the matrix becomes
**declared rather than accidental**, which is the whole point of a registry. The predicate is
named in the check's failure message so a red arm says which set it is comparing. Authoring
`agents/capability_matrix_boxy_pipeline.exs` is not forbidden — it is a different ticket, and it
would be a matrix ticket, not this one.

**The proof case is a reconciliation, not a sweep.** Of the surfaces originally
named for boxy-pipeline's dormancy declaration, several do not name it at all —
verify and record which. Its absence from the generated capability matrix means
absence from the planner's system prompt and from Rig's matrix view. The
registry brief's own argument therefore already holds without any directory move:
*anything that discovers use cases by scanning directories silently stops seeing
it, which is indistinguishable from the discovery being broken.* Enumerate the
surfaces that carry a use-case list, verify and record how many disagree with
each other, and reconcile against the registry.

**Contract refs.** **This section's constraints 1–3**, above. Agents `CLAUDE.md` §Definition
of done, the two-markers rule and the `dormant` marker's registered statement in `pytest.ini`.
Agents `CLAUDE.md` §Learning — m6-cloudcost, the incomplete-enumeration rule.

`Provenance, not a contract ref: the ruling and the three constraints above were drafted in
claude/aetheris-agents--use-case-registry-brief.md, which §Authority and history records as not
resolving from either repository. Its content is landed in this section rather than cited, so the
contract is the section. Corrected at t1a stage 2, 2026-08-19: this line previously read "The
registry brief.", a normative pointer into a surface the reader cannot open — the
unresolvable-reference defect BL-162 was filed for, and the thing §Authority and history forbids
in this document in terms.`

**Touches.** The new registry file — RESOLVE its path; `scripts/drift_check.py`;
`tests/test_drift_check.py`; the surfaces the doc-enumeration check names —
RESOLVE which subset is in scope. Repo-qualify every path.

**Do not generate.** No document is regenerated into prose; check and fail only,
per the registry brief's constraint 2. No directory move. Dormant tests keep
collecting — deselect at run time, never at import.

**Done-check.** The new checks addressable via `--check`; the whole-suite gate
command from `CLAUDE.md` §Definition of done; `drift_check --strict` post-commit
with expected WARNs named.

**RESOLVED at ticket time, t1a stage 1 → stage 2, 2026-08-19.** *(This block was two open
resolvers; both are discharged and it is kept, with its answers, rather than deleted — a resolver
that vanishes leaves the next reader unable to tell a decided question from one nobody asked.)*

- **The registry's file, format and location.** `docs/use-cases.md`, a markdown table under the
  anchor `## The registry`. Options B (JSON), C (`pytest.ini` as the source) and D (a
  per-use-case declaration) were considered and rejected — C because it makes dormancy and
  test-mechanics share a mechanism, which constraint 3 forbids in terms; D because a use case
  with no file would then be indistinguishable from one nobody declared, which is
  inference-from-shape, the defect the ruling above exists to remove. **No manifest row**, which
  is decided at the cycle's close on the standing specification test, as this document's own row
  is.
- **Which enumerating surfaces the check covers, and on what criterion.** *A surface is in scope
  iff its enumeration can be extracted by a parser that never has to decide what a sentence
  means.* Applied out loud to twenty-six surfaces before it was argued; it separates the two
  disagreeing lists inside agents `CLAUDE.md` — the §Key docs **table** in, the "current use
  cases" **sentence** out — which is the discrimination it was written for, and it does not
  exempt them both. It also discharges gc t3's predicate **structurally**: a table row and a Rust
  literal cannot be confused with an enumeration quoted inside a dated correction block, and
  prose is out of scope, so no live-vs-quoted distinction is left for the check to get wrong.

### t1b — the backlog split

**Issue.** `vishal-h/aetheris-agents#77`

**Blocked by t0.** Scope per the shape brief: the reorganisation, the tombstone at
the old path, and the `BL-nnn` resolution check, in ONE commit — the check is the
precondition, not a follow-up. If the check cannot land with the split, do not
split. Terminal-only, one-way moves; the ID is the address and the path is never
load-bearing. Inherits the check file's shape from t1a.

**Touches.** `docs/backlog-2026-06.md`, the tombstone at the old path,
`scripts/drift_check.py` and `tests/test_drift_check.py` for the `BL-nnn`
resolution check — and **`../aetheris/scripts/sprint.sh`**. **t1b is
cross-repo.** `sprint.sh` binds `SPRINT_BACKLOG` to a fixed relative path and
consumes it as an anchored `grep` on the row heading; a split that relocates the
backlog turns every `expected_fail` declaration into a blocking FAIL, and it
fails on the arm that reports the backlog unreadable rather than on anything
about the split. Verify the line numbers at HEAD; do not carry them from this
document.

**Do not generate.** No triage. See t0.

**RESOLVE at ticket time.** Whether backlog issue references need repo-qualifying
— the file spans both repos and its existing references are unqualified, so
whether any already points across is unverified. Routed to BL-150 as a question.

**RESOLVED at ticket time — ds t1b, 2026-08-19, harness `a6464f4` and this commit.**
*(The agents sha is not named here: a commit cannot cite itself, and a hash written
into the commit that would make it true is self-falsifying when written.)*
The four resolvers above are answered here and their original wording is kept, not
edited, so a later reader can see what was open and what settled it.

- **"the tombstone at the old path" — there is none, and none is owed.** The
  ratified layout keeps `docs/backlog-2026-06.md` as the OPEN file and moves terminal
  rows to a new `docs/backlog-2026-06-closed.md`. The old path never dies, so a
  tombstone would mark a grave that does not exist. What the scope brief was reaching
  for is supplied instead by a **header on the open file** naming the archive, stating
  that the id is the address, and stating that the export set carries the open file
  only — so the manifest gap is a documented property rather than a silence.
- **"turns every `expected_fail` declaration into a blocking FAIL" — the conditional
  is sound and the quantifier is empty.** There are **zero** `expected_fail` and
  `known_red_healed` call sites at harness `8eb960d`; both helpers have never fired.
  So the split turned nothing into a FAIL on the day it landed, and the breakage this
  clause names would first have appeared whenever someone wrote the first KNOWN_RED
  arm, with the split long merged. That is a **sharper** statement of the risk, not a
  softer one, and it is why the harness edit shipped with a hermetic exercise of all
  four arms — the positive control the gate had never had.
- **"Verify the line numbers at HEAD" — done, and they held.** `SPRINT_BACKLOG` at
  `:104`, the readability arm at `:122`, the anchored `grep` at `:127`, and the
  reservation block at `:161-167`, all at harness `8eb960d`.
- **"whether backlog issue references need repo-qualifying" — no, and the reason is
  that the backlog names issues almost nowhere.** Answered on **BL-150**, where the
  ticket routed it. The `(#nnn)` heading suffixes are `vishal-h/aetheris-agents` issue
  refs and `(#TBD)` is much the commonest value; the file carries no `owner/repo#n`
  form and no bare `#n` naming a harness issue, so nothing in it resolves to the wrong
  object. What is **not** settled is the rule itself — a bare `#77` written in a
  *harness* artifact resolves to `vishal-h/aetheris#77`, which is why the harness
  commit spells the ref in full.

**One ruling the ticket did not anticipate, recorded because it was taken.** After the
split, does `sprint.sh` resolve a KNOWN_RED ref against the open file or the **union**?
It resolves against the union, preserving current behaviour. Open-file-only is arguably
better — a known-red tracked by a row already archived as terminal is by definition a
stale carry, and resolving against the open file alone would make that a loud failure
for free — but it is a behaviour change riding on a path edit, and `sprint.sh:161-167`
reserves adjacent design questions to the first KNOWN_RED arm. The alternative is
recorded **inside that reservation block**, next to the question already there, rather
than in this document, so whoever writes that arm finds it.

### t2 — the artifact/run stamp

**Issue.** `vishal-h/aetheris-agents#78`

**Scope.** BL-153's Owes is discharged and the row is ready to scope: arm ordering
NOT changed, the stamp written script-side, the identifier pipeline-minted,
coverage including the history tree, and ~~a writer that runs last unconditionally —
which no current step is~~ **per-step attestation across all six producers**.

`[Amended 2026-08-20 at ticket time. The struck clause is kept rather than deleted,
on t1b's precedent: it is what the cycle believed when the section was written, and
the reason it moved is the ticket's main finding. **Run-level completion is not
satisfiable agents-side and is now BL-167.** Under an LLM orchestrator every step is
prompt-invoked, so a "final step" is a line the model may skip — and two of the six
producers have no last-writer position at all: eduloka's writers are N concurrent
sub-agents joined only at `wait_for_all`, and boxy-pipeline has no program that knows
a run occurred. It needs a harness post-run hook. **t2 did not build it, did not stub
it, and does not pretend to it.** The other four scope items stand as written and all
four landed.]`

**The unit correction, landed here rather than cited.** BL-153's two rulings are
inconsistent: ruling 1 speaks of "an unstamped or mismatched DIRECTORY" while ruling
2 requires coverage of an accumulating tree no guard clears. A directory-level stamp
cannot express the second — cloudcost's `history/` is a *different* directory from
the guarded one and one run writes into both — so **the attestable unit is the step,
not the directory**: the record enumerates artifacts and attests the step that wrote
them. Restated as the reader's rule, replacing ruling 1's directory form: *an artifact
not named in an attested step record is not that step's output.* Ruling 1's substance
is preserved whole — absence still carries the meaning — because `attested_at` is
written only after every artifact write for that step has returned.

**The writer is code, never a prompt line.** Ruling 1 forbids a reader free to ignore
the stamp; a writer free to skip it is the same defect one step earlier. Docbuilder's
own PHASE D2 was that shape and is filed (BL-151): D2 wrote the run log at PHASE D
while PHASE E wrote `output/uploaded.json` afterwards.

**RESOLVE at ticket time.** ~~Format, file and reader.~~ **Resolved:**
`<use_case>/data/run-records.json` — gitignored, and never under `output/`, because
payslip's `output/runs.log` dies with the tree the sprint `rm -rf`s. A JSON array,
one entry per step: `{run_id, step, started_at, attested_at?, artifacts[]}`, each
artifact `{path, sha256, bytes}` relative to the use-case root and **including
artifacts outside `output/`**. Timestamps UTC with a `Z` suffix, so the lexicographic
sort readers already perform is chronological. Idempotent replace by `(run_id, step)`;
writes atomic; recording best-effort at the point of write, but a malformed record
file never silently overwritten. The reader is specified and **deliberately not
built** — no reader that refuses an unattested artifact, no `drift_check` arm, no
`sprint.sh` change, no harness change.

**Touches.** `scripts/run_record.py` and `tests/test_run_record.py`; the six
producers' instrumented scripts, their agent files where one exists, their
`.gitignore`s and their adoption tests; `docs/backlog-2026-06.md` for six filings;
this section; and `docs/milestones/ds-t2-implementation-notes.md`. Agents repo only.

### t3 — BL-161, the deferred sprint arm

**Issue.** `vishal-h/aetheris#85`

**Scope.** Per BL-161. **Its subject is entirely a harness write, so its issue
is filed in the harness repo** — unlike t1b, which is cross-repo with an
agents-side primary. Between them they exercise both sides of the Project's
cross-repo claim and both arms of the filing tiebreak; close criterion 8 depends
on at least one running.

**It is in this cycle on its own merits.** BL-161 is an open row worth
discharging independently; the trial is its occasion, not its reason. BL-153 was
rejected for this slot precisely because taking it would have required reversing
the not-changed ruling on its arm ordering, which would be a change made to get
past a test.

**Touches.** `../aetheris/scripts/sprint.sh` and whatever the arm needs. Every
path repo-qualified.

**RESOLVE at ticket time.** Everything below scope.

**RESOLVED at ticket time — ds t3, 2026-08-21, harness `d648aa8` and this commit.**
*(The agents sha is not named here, on t1b's ground: a commit cannot cite itself.)*
The original wording above is kept, not edited, so a later reader can see what was open
and what settled it. Three units were below scope; each is answered.

- **"whatever the arm needs" — it needed nothing outside `sprint.sh`.** No new script,
  no fixture, no env var, no `mix` task. Both export scripts already carry the flags the
  arm drives (`--dry-run`, `--manifest`, the positional `dest`, `--replace`), and the two
  refusal paths that make the exit-code assertions possible already return 1. The arm is
  116 lines of `sprint.sh` and one word added to the usage line at `:6`.
- **"Per BL-161" — the row has two Done-when branches and this took the first.** Branch 1
  is the arm; branch 2 is a ruling that the tests suffice. Branch 1's second clause,
  *"named in a boundary record"*, could not be performed as worded — a boundary record here
  is a dated entry in `docs/project-knowledge-manifest.md`'s export-boundary log, and this
  ticket runs no export boundary. The naming landed in `CLAUDE.md` §Definition of done
  beside the mechanism's pointer instead, which is where branch 2 places its own outcome
  and what the next boundary record's author reads. **A substitution of surface, recorded
  as one**, and the arbiter's to accept or reverse.
- **"both arms of the filing tiebreak" — only one arm ran, and criterion 8 cannot see it.**
  The Scope paragraph above says t3 and t1b between them exercise both arms and that
  criterion 8 *"depends on at least one running"*. Both did run, so the criterion is
  satisfied — but it is phrased *"If neither runs"*, a disjunction over what was built as a
  conjunction, so it would also have reported satisfied on a cycle where only one arm ran.
  **Recorded, not fixed:** editing a close criterion during the cycle it governs is the
  change-made-to-get-past-a-test this section's own third paragraph refuses. Full statement
  in `docs/milestones/ds-t3-implementation-notes.md`.

## Open at open — all five ANSWERED at the close

The items as opened, each with where its answer landed. None is carried forward.

- **The registry's file, format and location (t1a).** ANSWERED at ticket time.
  `docs/use-cases.md`, a markdown table, with the membership rule and the
  extraction criterion stated in the file itself. Landed in §t1a's `RESOLVED at
  ticket time` block and in the file; `drift_check.py`'s `use_case_registry`
  check reads it.
- **t2's format, file and reader.** ANSWERED at ticket time, in §t2's `RESOLVE at
  ticket time` block, which carries the resolution rather than the question.
  `scripts/run_record.py` is the writer, the reader's rule is *an artifact not
  named in an attested step record is not that step's output*, and the unit is
  the step rather than the directory — see
  `docs/milestones/ds-t2-implementation-notes.md` §A1.
- **Whether issues consolidate into one repo.** DISSOLVED, not decided. It was
  reserved for the close on verdicts A and B; verdict A retires the Project, and
  the question was *"does the cross-repo container justify issues living in two
  repos"*. With no container the question has no subject. `hc-consolidation.md`
  R28 carries the retirement; the tiebreak ran in both directions before it did,
  which is recorded at `docs/milestones/ds-t3-implementation-notes.md` §2, so the
  arrangement was tested rather than abandoned untested.
- **Whether this document earns a project-knowledge manifest row.** ANSWERED: it
  does NOT, and `docs/use-cases.md` does. Both are recorded with their reasoning
  in `docs/project-knowledge-manifest.md` §2026-08-21, beside that file's other
  refusals — the ground is the one that refused `cloudcost/m3-milestone.md`, that
  a cycle document holds derived reasoning about contracts living elsewhere. The
  deferral to the close was honoured: the test needed the finished document, and
  it was applied to it.
- **Whether §6's literal-prompt requirement or this document's practice changes.**
  ANSWERED: **§6 changes.** `**Contract refs.**`, `**Do not generate.**` and
  `**Runbook update rule.**` are now optional and §6 permits the claude-code
  prompt to be authored at ticket time; `**Done-check.**` stays required.
  Harness `2050c04`, `docs/methodology/milestone-methodology.md` §6, which carries
  the dated bracket. §Deviation from methodology §6 above is thereby discharged —
  a divergence is closed by changing the document or the practice, and the
  document changed.

## The close

`2026-08-21. Two commits, harness first: harness 2050c04 and the agents commit carrying this
section. Every figure below carries the command that produced it; figures over the repositories
were derived at agents b56a6b2 / harness d648aa8, the baseline both commits were cut from.`

### The eight close criteria

**1 — every ticket passes its done-check. NOT SATISFIED.** Three of the five ticket sections
declare no `**Done-check.**` field at all — t1b, t2 and t3 — so for those three there is no
declared done-condition to have passed. That breaches methodology §1 item 3, *every ticket has a
machine-checkable done-condition*, and this document declared only its `**Claude-code prompt.**`
divergence, so the other four dropped fields were an **undeclared divergence**. It is closed by the
§6 amendment at harness `2050c04`: the three fields it makes optional are dropped without loss, and
`**Done-check.**` is the one absence that was a real gap, which is why that field alone stays
required. Recorded as NOT SATISFIED rather than repaired retroactively — the tickets did run checks,
but a check run and a done-condition declared are different objects and only the second is what this
criterion tests.

**2 — zero unresolved blocking findings. SATISFIED.** The arbiter holds the five tickets' packets
and no blocking finding is unresolved at this close.

**3 — `drift_check --strict` run POST-COMMIT for any manifest-tracked edit, WARNs named not chased.
SATISFIED per ticket, and for this close's own commit its subject is the post-commit strict run
published in this close's packet.** Not a further commit: the ordering this criterion encodes is
that check 8 reads committed history, so the run must follow the commit it audits — it does not
require a commit to follow the run.

**4 — the §7 promotion committed and verified by opening the file, including the census of prior
cycles' promotion claims. SATISFIED.** The promotion is `## Learning — ds` in agents `CLAUDE.md`,
verified by reading it out of the file rather than by asserting the edit landed. The census read the
two preceding promotion sections — `## Learning — BL-152` and `## Learning — the 2026-08-16 export
boundary` — against the files each claim names: three promotion entries, all three present and
readable, and both harness counterparts they name present in harness `CLAUDE.md`. One defect found,
and it is a wrong path inside a true rule rather than a failed promotion — §Definition of done names
a root `conftest.py` that does not exist, where `pytest.ini` records the mechanism's placement in
`tests/conftest.py` and calls the absence deliberate. Appended to **BL-150**, unfixed.

**5 — trial verdict A. FAILED, and the Project is retired.** The consulted-list is empty across five
of five tickets and the keep-current list is not, under either reading of *"the Project"*. Ruled at
`docs/milestones/hc-consolidation.md` **R28**, which carries the evidence and the retirement.

**6 — trial verdict B. PASSED, five of five at HEAD**, run before and after this close's tracker
acts with the same result. Ruled at **R29**, which also ratifies the two comparison boundaries as
criterion 6's reading and records the three-state negative control.

**7 — the R23 verdict. PASSED substantively**, and the criterion is recorded as sharing criterion
8's vacuous shape. Ruled at **R30**.

**8 — the cross-repo arm. SATISFIED ON BOTH ARMS.** t3's primary artifact is a harness write and its
issue is `vishal-h/aetheris#85`; t1b's primary artifact is the agents backlog while its breaking
change is harness `sprint.sh`, and its issue is `vishal-h/aetheris-agents#77`. Both ran, so the
criterion is not answered by its silence-is-forbidden clause. **The latent defect is stated and not
fixed:** the pair was built as a conjunction — the filing tiebreak is exercised only if *both* arms
run — while the criterion is a disjunction that fires only at zero, so a cycle in which exactly one
arm ran would satisfy it with the tiebreak half-exercised. Full statement at
`docs/milestones/ds-t3-implementation-notes.md` §2. Not fixed here: editing a close criterion at the
close it governs is a change made to get past a test.

### What the cycle produced

Five tickets, all complete and pushed before this close. The cycle's durable outputs live in the
documents that carry them rather than in this file: the backlog's status field and its open/closed
split, `docs/use-cases.md` and its drift check, `scripts/run_record.py` and the artifact/step
record, and the harness `export_mechanism` sprint arm. The rulings are `hc-consolidation.md`
R28–R30 and the dated entry on R25; the §7 promotion is `## Learning — ds` in agents `CLAUDE.md`;
the §6 amendment is harness `2050c04`.

### What this close did NOT do

No export boundary was run. `docs/project-knowledge-manifest.md` gains one row and loses none, no
other row is re-pinned, nothing was assembled and nothing uploaded — so `docs/use-cases.md` is
manifest-tracked and unexported, and the store holds a `CLAUDE.md` pointing at a document it does
not have. Recorded in the manifest's own narrative. No close criterion was edited. Neither of the
two vacuous-shaped criteria was repaired. Nothing was pushed.

## Rows this cycle might promote, none scheduled

BL-154 is the first candidate if there is room — Rig's Cancel kills the direct
child and transitions nothing, it is the mechanism that made BL-153's subject
visible, and it fires for every agent. Note that it does NOT serve close criterion
8: Rig lives in the agents repo, so BL-154 is agents-side.
