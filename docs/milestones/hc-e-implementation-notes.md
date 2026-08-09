# hc-e — implementation notes

**Ticket.** `docs/milestones/hc-consolidation.md` §Ticket set → hc-e. **Repos.** agents `f8ed90f`,
harness `48f59e7`. **Date.** 2026-08-09.

**Outcome: the opening edit E1–E4 landed; the ticket then STOPPED at its anatomy census.** hc-e has
**2 of 7** §6 fields authored and **no step-1 gate slot at all**. No close work was done. That is the
correct outcome, not a setback — and it is the second time this round, which is itself the finding.

---

## 1. E1 — hc-d's row, closed at r3

R19 scopes a row edit to the session that changed the state; hc-d's session is over, so this carry
was authorised explicitly rather than taken.

**The `[V]` — the commit range is derived from the repos, not from the packets.**
`git log --oneline --grep='hc-d'` over each repo:

```
agents   240eb59 → f8ed90f   (13 commits matched; the hc-c pair at the head of the range excluded
                              by their own subject lines, leaving hc-d's 11)
harness  2d76a65 → 48f59e7   (4 commits: the contract landing plus r1, r2, r3)
```

The row now reads **Closed 2026-08-09 at r3**, in hc-c's shape: gate G0–G5 passed, BL-077 closed,
BL-133 face 2 discharged, R3 answered, four rounds. The prior *"Opened and stopped"* text is kept
verbatim inside the cell per **decision 7**, not overwritten — a row that silently replaces its own
history is a row whose earlier state cannot be checked.

## 2. E2 — the recency-selection candidate, transcribed

Added to §Promotion candidates verbatim as authored, above the restore-verified entry. Its sharp
edge is the part I would not have written myself: **an artifact can be correct and still be the
wrong artifact, and nothing in its contents distinguishes the two.** That is why the corrupted
provenance stamp survived review — it was inspected, and inspection was the wrong instrument.

## 3. E3 — BL-135 and BL-075 are the same defect

**Established from the rows and the source, not from resemblance.** BL-075's m4 close-b annotation
already carries the full identity, and every field matches BL-135's observation:

| | BL-075 (2026-08-08) | BL-135 (2026-08-09) |
|---|---|---|
| module | `Aetheris.CLI.Commands.RunHelpersTimeoutTest` | same |
| file:line | `…/run_helpers_timeout_test.exs:84` | same |
| stacktrace | `:98` | same |
| assertion | `await_bounded(run_id, await_inactivity_timeout_ms: 300)` | same |
| error | `stalled: … for 300ms … last event seq: -1` | same |
| run id | `await-status-activity-7139` | `-8610` |

The run id is `System.unique_integer` and distinguishes nothing. **One test, one assertion, two
observations** — not two tests in one module, and not two failures of different assertions.

**So BL-135 is a duplicate and the error is mine.** The gate rule requires a tracked row *the day a
red is found*; it does not license filing without looking. I filed BL-135 at hc-d r3 without
searching the backlog, and BL-075 not only existed but already carried the identical stack trace.
**The count error is over a population of size two** — filing two rows for one defect, which is the
same class as filing one row for two.

**Folded, not deleted, both ways.** BL-075 gains the third observation with its date and evidence;
BL-135 records that it was folded and why, and remains as the record of the duplication. What
BL-135 genuinely contributes is carried across: the **nine non-reproductions**, which are the first
probe of the trigger rather than another count of failures.

## 4. E4 — arm 2's blocker is PARTLY lifted, and the remaining gap is a different shape

**The `[V]`, quoted.** BL-075's blocking clause: *"Three further full-output runs come back clean"
requires that those runs' full output be **retained somewhere durable**, and **BL-133** establishes
that no such place exists: `../aetheris/sprint/` archives `run.json` alone, and `mix test` output is
archived nowhere at all.*

**Two halves, and hc-d falsified exactly one.**

**Half 1 — "no such place exists" — is now false.** Every sprint run retains `console.log` (every
arm, in order, untruncated, streams merged) beside `provenance.txt` (both repos' commits, target,
command), under a stated, bounded and *enforced* 30-day retention.

**Half 2 — "`mix test` output is archived nowhere at all" — still holds**, and it is the half arm 2
needs. Derived, each with its control:

- `sprint.sh` invokes `mix test` **once**, at `:1517`, on **two named files** — not the suite.
- `grep -c 'run_helpers_timeout_test' ../aetheris/scripts/sprint.sh` → **0**.
  *Positive control:* `grep -c 'server_checkpoint_test'` → **3**, so the pattern finds referenced
  test files where they exist.
- The boundary-gate `mix test` is a **direct invocation** outside any sprint process, and
  `SPRINT_CONSOLE` exists only inside one.
- Over the retained corpus: `grep -rlE '[0-9]+ tests, [0-9]+ failures' sprint/*/console.log` →
  **0 files**. *Positive control:* the same pattern over a direct `mix test` capture → **1**.

**The place exists; the routing does not.** The blocker has changed shape rather than lifted — from
*"no durable place exists"* (a ruling) to *"the full suite is never run where the durable place
would capture it"* (a routing decision). That is smaller and cheaper, and it is recorded on the row
so the next reader does not re-derive it. **Face 1 is untouched and is not what arm 2 needed** — arm
2 is about run output, not reviews.

**And one thing recorded against hc-d's own reasoning, since hc-d is mine too.** hc-d chose 30 days
*citing BL-075's "three further full-output runs"* as the justification. **That citation reached one
step further than the mechanism does** — the bound was set for a consumer the capture does not yet
serve. The bound is not wrong; its stated rationale was.

**Arm 2 is not started.** Establishing the blocker's status was E4's whole scope, and counting runs
toward arm 2 was explicitly excluded.

## 5. The stop — hc-e's anatomy census

**Population: the seven §6 fields named by this document's own §What the methodology owes**
(*"seven sections and no more — `Scope`, `Contract refs`, `Touches`, `Do not generate`,
`Runbook update rule`, `Done-check`, `Claude-code prompt`"*), plus the step-1 gate slot, which
decision 3 makes a requirement rather than a §6 field.

```
AUTHORED      Scope
AUTHORED      Contract refs
NOT AUTHORED  Touches
NOT AUTHORED  Do not generate
NOT AUTHORED  Runbook update rule
NOT AUTHORED  Done-check
NOT AUTHORED  Claude-code prompt

population = 7      authored = 2      not authored = 5
Step-1 gate slot:   ABSENT — not even R13-marked
```

**Positive control**, the same pattern over hc-d's section, which has all seven: `1` for every
field, and `2` for the gate slot. So a zero reads as absence rather than as a broken pattern.

**hc-e is hc-d's shape, and worse in one respect.** hc-d stopped at **2 of 7** with an R13-marked
gate whose resolver named a reviewer-authored section-scoped edit. hc-e is **2 of 7** with **no gate
slot at all** — its catch-all is `**Everything else is `[R13: deferred, per R12.]`**`, which defers
the gate along with the five fields and names its resolver only by reference to R12.

**Why this is a stop and not a substitution.** R12 assigns authoring to the reviewer (decision 11);
hc-d's precedent is that **every defect in hc-b's version of hc-c's specification sat in the one
slot completed confidently, and every R13-marked slot was sound.** Authoring five fields and a gate
here would reproduce that failure across the same surface, in the ticket that closes the round —
where an unnoticed defect has no later ticket to catch it.

**What would unblock it:** a reviewer-authored section-scoped edit carrying hc-e's `Touches`,
`Do not generate`, `Runbook update rule`, `Done-check`, `Claude-code prompt`, and a step-1 gate
written against the design those fields describe.

**Three things already on the record for that edit**, restated so its author does not rediscover
them: §7's prior-claims census is over **m4's seven promoted entries**, not only this round's;
**hc-b's G4 discharged four of them** and that is a G4 result rather than the census; and the
**export boundary is the last content operation**, clearing all three standing `project_knowledge`
WARNs.

**And one field that will need care rather than transcription:** hc-e's *"named question that gates
the rest"* is already marked `[partly falsified]`, and the half that stood — *"hc-d has not run"* —
is now false too. Both halves are knowable at the moment hc-e's anatomy is authored, which changes
what that slot should say rather than merely dating it.

## 6. Not reached, not dropped

- **The §7 ritual, the export boundary, the milestone summary, §Close criteria's reads** — all of
  hc-e's actual work. Untouched.
- **No row filed or closed by this edit.** BL-075 and BL-135 are *annotated*; neither changes state.
  BL-135 is folded, which is a disposition recorded on both rows, not a close.
- **hc-e's own row in §Ticket set is untouched**, as instructed — the census may change what it
  should say, and that is the authoring session's call.
