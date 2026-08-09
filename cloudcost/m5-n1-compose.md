# m5 — the N>1 compose surface

`Opened 2026-08-09. Canonical document for BL-131. Authored by the reviewer
before t1 opens, per hc-consolidation R12.`

## Why this exists

**What this round decides.** BL-131: whether the N>1 compose path is a supported
surface. The row owes a ruling — supported, or removed — and the §Contracts
amendment that follows it. Read `docs/backlog-2026-06.md` → BL-131 for the
subject; it is not restated here.

## Scope

**Shape: two tickets with a gate stop between them.** t1 establishes, read-only,
and stops. The reviewer rules. t2 applies the ruling. **The ruling is not
claude-code's to make, and t1 does not make it.**

> `[Deviation, recorded rather than glossed. R20 covers a reviewer-authored
> **section-scoped** edit; this document's creation is not one, because there was
> no document to scope into. Recorded here as a divergence-with-record, on the
> same footing as m4-5's clause-4 entries: the authoring is the reviewer's per
> R12 and decision 11, and only the edit's shape differs.]`

---

## Sequence

harness consolidation round (closed 2026-08-09, hc-e r9) → **m5 t1** → **the
ruling** → **m5 t2** → BL-132 → provider four.

**BL-074 is not in this round.** BL-131 alone, by the reviewer's scoping ruling
of 2026-08-09. The seam sweep keeps its own row.

**Provider four carries two non-identical gate statements at HEAD** — §Not
established item 1. This round does not reconcile them and does not act on
either.

---

## Ticket set

| Ticket | Subject | State |
|---|---|---|
| **t1** | Establish the N>1 compose surface, read-only, to the point where the ruling can be made | **Not opened.** Anatomy authored 2026-08-09 |
| **t2** | Apply the ruling; amend §Contracts; dispose the rows that resolve with it | **Not opened.** Anatomy authored 2026-08-09, most slots R13-marked |

**Ticket anatomy in this document is §6's seven fields plus a step-1 gate. The
gate is not a §6 field.** §6 defines seven fields and no gate. The gate is m4
decision 3, carried by hc-consolidation **R8**. Stated here so that no ticket in
this round cites it as a methodology obligation — `docs/reviews/hc-b-review.md`
Round 0 recorded that citation as a manufactured authority.

**R19 applies.** A session that changes a ticket's state updates its row in the
table above in the same commit.

### t1 — establish the N>1 compose surface (read-only)

**Step-1 gate** *(m4 decision 3, carried by R8 — run before any other work in
the ticket).*

Re-derive at HEAD, from source, the two things BL-131's premise rests on:

- **(a)** the set of routes by which `cloudcost/scripts/compose_report_data.py`
  can receive more than one provider bundle;
- **(b)** how many `--cost` / `--inventory` / `--orphans` triples
  `cloudcost/agents/cloudcost_orchestrator.exs` passes.

Record both with `path:line`. State how a zero result was established as absence
rather than as a failed search. **If either has moved from what BL-131 states,
stop and report before doing anything else** — the row's premise has changed and
the ticket is re-scoped rather than continued. Do not repair the row from inside
the gate.

**Scope.** After this ticket, the evidence the BL-131 ruling needs exists as a
committed artifact in this repo rather than as a derivation inside a closed
cycle's prose. Eight enumerated questions are answered at HEAD, each with its
population named and its enumeration printed. No ruling is made, no behaviour
changes, and no file outside `Touches` is edited.

**Contract refs.**
`cloudcost/milestone.md` §Contracts — C4, C11, and the two pointer blocks that
name BL-131 · `cloudcost/m2-milestone.md` — decision H ·
`docs/backlog-2026-06.md` — BL-131, BL-132, BL-070, BL-119, BL-121 ·
`../aetheris/docs/methodology/milestone-methodology.md` §6 ·
`docs/milestones/hc-consolidation.md` — R8, R12, R13, R19, R21.
These are normative for this ticket and are **not** restated in the prompt.

**Touches.**

- `cloudcost/docs/m5-t1-implementation-notes.md` *(new)*
- `cloudcost/m5-n1-compose.md` — the **t1 row only** in §Ticket set, per R19

Nothing else. Any other path that changes is a deviation and is named in the
implementation notes.

**Do not generate.** No change to any file under `cloudcost/scripts/`,
`cloudcost/tests/`, `cloudcost/templates/`, `cloudcost/agents/`, or to
`cloudcost/tools.json`, `cloudcost/milestone.md`, `cloudcost/runbook.md`,
`docs/backlog-2026-06.md`, or anything in `../aetheris/`. **No ruling, no
recommendation, and no disposition** — including in the notes' own prose. Where
the evidence points one way, say what the evidence is; do not name the direction.

**Runbook update rule.** t1 introduces no environment variable, no startup step,
no configuration key, no operational procedure, and changes the observable
semantics of no command, flag or UI affordance. **No runbook section is in this
ticket's `Touches`, and that is stated here rather than left to inference.** If
the establishment work surfaces an operator-visible gap, record it in the notes
as a finding and leave it; fixing it is not this ticket.

**Done-check.**

```bash
# 1. The offline pytest spine over the cloudcost suite, as a HEAD baseline.
#    DERIVE the exact invocation from cloudcost/runbook.md or CLAUDE.md and
#    record the command verbatim beside its summary line. Do not invent one;
#    if neither document states it, report that as a finding and record what
#    you ran and why.

# 2. The notes file exists and is non-empty.
test -s cloudcost/docs/m5-t1-implementation-notes.md && echo NOTES_PRESENT

# 3. All eight questions have a section. Must print 8.
grep -c '^### E[1-8] ' cloudcost/docs/m5-t1-implementation-notes.md

# 4. Nothing outside Touches changed.
git status --short
```

**Claude-code prompt.**

> Read this ticket's `Contract refs` and do not restate them. Run the step-1
> gate above first and report its result before continuing.
>
> Then answer the eight questions below in
> `cloudcost/docs/m5-t1-implementation-notes.md`, one `### E<n> — <title>`
> section each, in order. **Every answer is derived at HEAD.** Name the
> population before you count it and print the enumeration beside the count; a
> count without its enumeration is not an answer. Every claim carries
> `path:line`. Every zero carries a positive control. Bind each artifact to the
> command that produced it, never to its position in a listing. Where you cannot
> establish something, say so and say what would settle it — do not fill the gap.
>
> **E1 — Route census.** Every code path by which `compose_report_data.py` can
> receive more than one provider bundle. Source-derived, not carried from any
> document.
>
> **E2 — Invocation census.** Every in-repo invocation of
> `compose_report_data.py` — the orchestrator, the sprint script, the runbook,
> `tools.json`, the test suite, any CI or helper script. For each: the bundle
> count it can produce, and whether it uses the multi-bundle route.
>
> **E3 — Test coverage.** Which tests, if any, exercise more than one bundle.
> Distinguish *a test that passes several bundles* from *a test of the discovery
> function with one bundle* — these are different and the difference is the
> answer. Name the population of test files searched.
>
> **E4 — Blast radius of REMOVE.** Everything that deletes if the multi-bundle
> surface goes: functions, branches, the declared argument and its manifest
> entry, tests, and every sentence in every document that describes
> cross-provider behaviour. Enumerate with `path:line`. Include documents outside
> `cloudcost/`.
>
> **E5 — Blast radius of SUPPORT.** Everything that must be *added* for the
> surface to be supported rather than merely present: tests, a sprint leg,
> runbook text, and the semantics the currency and cap behaviours would then
> have to state. Enumerate what does not exist today; this is a census of
> absences and each one needs its own positive control.
>
> **E6 — The three-state contradiction.** BL-131 tabulates three assertions
> about this surface, each attributed to a different document. For each: locate
> its current text at HEAD with `path:line`, quote it, and state whether HEAD
> still supports it. **Adjudicate nothing** — three quotations and three
> yes/no/moved readings.
>
> **E7 — Decision H's re-derivability clause.** Quote decision H's own sentence
> about a cross-provider total being later re-derivable from the per-provider
> normalized history path, and establish whether that path is written today —
> by which code, on which invocation. This bears on whether *removed* forecloses
> anything, so the answer matters more than its length.
>
> **E8 — Reachability of C4's and C11's stated behaviour.** For each of the two
> contracts separately: **reachable**, **source-only**, or **untested**, with the
> basis stated. This is the two known instances only. **Do not extend the check
> to C1–C15** — that is BL-132's row and taking it here mis-scopes both.
>
> Run the done-check and include its output in the review packet. **End at a
> gate stop**: report, and stop. Do not rule, do not propose t2's shape, and do
> not edit any row in `docs/backlog-2026-06.md`.

### t2 — apply the ruling

**Step-1 gate** *(m4 decision 3, carried by R8).* **R13-marked.** The gate's
content depends on the ruling's direction. `Resolver: authored by the reviewer
into this section by a dated section-scoped edit after the ruling and before t2
opens, per R12.`

**Scope.** After this ticket, the BL-131 ruling is implemented in
`compose_report_data.py` and its declared interface; `cloudcost/milestone.md`
§Contracts C4 and C11 state the post-ruling position rather than the
pre-ruling one; and the rows that resolve with BL-131 carry their dispositions.
What "implemented" means is the ruling's content and is not assumed here.

**Contract refs.** t1's implementation notes · this document's §Ratified
decisions, which will hold the ruling · `cloudcost/milestone.md` §Contracts C4,
C11 · `docs/backlog-2026-06.md` — BL-131, BL-070, BL-119, BL-121 ·
`docs/milestones/hc-consolidation.md` — R13, R19.

**Touches.** **R13-marked.** The path set is one of two disjoint sets and the
ruling selects which. `Resolver: t1's E4 and E5 enumerate the two blast radii
with path:line; the reviewer selects one and authors this field into this
section by a dated section-scoped edit before t2 opens, per R12.` **Not guessed
from here** — a guessed `Touches` is a specification, which R13 names as the
worse failure.

**Do not generate.** Authorable now, and complete as written: no reachability
work over C1–C15 (BL-132's row); no new provider adapter or provider-four
scaffolding; no edits under `eduloka/`, `rig/`, or `../aetheris/`; no
amendment to any contract other than C4 and C11.

**Runbook update rule.** **Partly R13-marked, and a runbook change is in scope
either way** — that much is authorable now, because both directions are
operator-visible: *removed* deletes a declared tool interface an operator can
read today, and *supported* adds an invocation an operator must be told about.
Which runbook text changes is the ruling's. `Resolver: same as Touches.`

**Done-check.** **R13-marked, deliberately.** Anchor: the offline pytest spine
over the cloudcost suite, at the exact invocation t1 records under its own
done-check item 1. `Resolver: the ruling, plus t1's recorded invocation; authored
by the reviewer before t2 opens, per R12.` Marked rather than completed on
purpose — R13's own recorded observation is that every defect found in a
reviewed anatomy sat in the slot its author completed confidently, and a
done-check written against an assumed post-ruling shape is exactly that slot.

**Claude-code prompt.** **R13-marked.** `Resolver: authored by the reviewer after
the ruling and before t2 opens, per R12.`

---

## Ratified decisions

**None yet.** The round's ruling lands here, authored by the reviewer at the gate
stop between t1 and t2 per R12, with its own date. An empty section at open is
the correct state and is stated rather than omitted.

---

## Not established

Carried rather than resolved. Per **R21**, this section holds three kinds of
entry — **(a)** an open question with an owner, which carries a resolver naming
something that exists; **(b)** a carried unknown, which names what would settle
it and invents no owner; **(c)** a decision not to fix, marked `[DECIDED]`.
Each entry states its kind. The per-item prefix is authoritative; this section
carries no total.

1. **`[OPEN]` (b)** **Provider four carries two non-identical gate statements at
   HEAD.** `cloudcost/m4-consolidation.md` states in one place that provider four
   is gated on the cycle's seam sweep and the harness round, and sequences it in
   another as following BL-131 with no seam sweep named. Neither supersedes the
   other and both are live.
   **Settled by:** a ruling that reconciles them, authored wherever provider four
   is scoped. **No owner** — provider four is not open, and this round declined
   to take BL-074 with BL-131.

2. **`[OPEN]` (b)** **BL-131's `Source:` line cites gate items that exist as no
   committed text.** The row attributes its derivation to two gate items of a
   ticket that produced no implementation-notes file; the only in-repo records of
   that ticket are its cycle-document passages and two backlog annotations.
   **Settled by:** nothing in-repo — the derivation is re-run at HEAD instead,
   which is t1's step-1 gate and E1/E2. Recorded so that a later reader does not
   cite those gate items as though they were a document. **No owner.**

3. **`[OPEN]` (a)** **Whether decision H's re-derivability clause is satisfied
   today.** Decision H drops the merge-across-clouds while stating that a
   cross-provider total stays later re-derivable from per-provider normalized
   history. Whether that history is written on the invocations the pipeline
   actually makes has not been established, and *removed* forecloses more if it
   is not.
   **Resolver:** t1's **E7**, in this document.

---

## Carried in

Inherited from `docs/milestones/hc-consolidation.md` §Milestone summary → §Open
for the next cycle, and in force for this round's §7:

- **An entry's attribution is structural.** An insertion between a claim and its
  `Source:` re-attributes both. An edit that inserts into a structured document
  states where the insertion point falls relative to the surrounding unit's
  boundaries, and a verification that quotes context asserts what the context is.
- **A vocabulary change owes a sweep of everything that speaks it.** When a
  label, status set, field name or prefix changes, derive the population that
  speaks it and check each member in the same commit.
- **m4-5's divergence: promote mid-cycle when a rule binds work that has not run
  yet.** This round does not defer promotion to its close.

**BL-075 arm 2 remains unsatisfiable as written** and is not this round's
subject; carried so it is not rediscovered.
