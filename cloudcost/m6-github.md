# m6 — GitHub: provider four, and the first consumption-class adapter

`Opened 2026-08-13. Canonical document for GitHub as provider four. Authored by
the reviewer; recorded here by claude-code.`

Providers one to three are IaaS: a resource is a thing that was provisioned,
and waste is a thing still provisioned that nobody uses. GitHub is the first
member of a different class, where a resource is an entitlement that was
assigned and waste is an entitlement nobody exercises. Google Workspace is the
same class and comes after; AI-provider spend is the same class again.

GitHub goes first because its surface is the richest. Workspace is close to
pure seats and would force the class decision on too thin a case. So the
decisions this milestone makes belong to the class, not to GitHub, and the
cost of getting them wrong is paid three times.

## Ratified decisions

Numbered fresh for this milestone. Each is one entry carrying its ground, per
R25 — a ruling earns a section only when it changes code.

- **D1 — Currency is an adapter-declared constant carrying a recorded basis,
  never a captured provider field. No conversion anywhere in the pipeline or
  the report; multiple currencies are surfaced side by side.** `Ruled by the
  arbiter 2026-08-13. Ground: no provider supplies a currency field — all
  three existing adapters declare it, and one records the check as provenance
  rather than leaving the declaration bare. Reconciliation against amounts
  actually deducted by the bank is a later, separate concern.`

- **D2 — Reporting granularity is monthly aggregates only. Daily, hourly and
  per-SKU detail are out of scope.** `Ruled by the arbiter 2026-08-13. Ground:
  a reader wanting finer detail goes to the provider's own console; recorded
  so it is not re-litigated per provider.`

- **D3 — C4's two-decimal precision clause stays deferred. Rounding happens at
  ingest, immediately after aggregation, and never before a multiplication.**
  `Ruled by the arbiter 2026-08-13, replacing a draft whose stated ground was
  false. Ground: normalized amounts are aggregates, granularity is monthly,
  and every currency in use is two-decimal — all three verified by reading.
  The draft claimed rounding was render-only; it is not, and the corrected
  statement is what the deferral now rests on. If any of the three changes,
  the deferral reopens.`

- **D4 — An adapter that multiplies a unit price by a quantity aggregates at
  full precision and rounds after. One clause in the adapter's ticket and one
  test assertion; not a schema field and not a retrofit.** `Ruled by the
  arbiter 2026-08-13. Ground: C14 territory. One existing adapter already does
  this at four sites and is the exemplar; another rounds its unit rate before
  multiplying, which is latent rather than live and is recorded here as the
  counter-example rather than opened as work.`

- **D5 — BL-136's report, when built: one line item per provider,
  alphabetical, for a given period, currency as a column. No total row.**
  `Ruled by the arbiter 2026-08-13. Ground: with no conversion there is no
  single number. A later column carries the bank deduction, and that column is
  where a defensible single figure will come from.`

- **D6 — The consumption class gets a real inventory with new canonical types,
  not a cost-only lane — bounded to entities carrying all three of an activity
  signal, a derivable per-instance cost, and a stable identifier.** `Ruled by
  the arbiter 2026-08-13. Ground: an unexercised entitlement is recoverable
  spend in the same sense an orphaned disk is, so the pipeline's optimisation
  half extends to this class. The three-part bound is what keeps it from
  extending to everything a provider happens to enumerate.`

- **D7 — GitHub's cost snapshot is built from the billing usage summary
  endpoint, with the detail endpoint retained as an independent reconcile
  source.** `Ruled by the arbiter 2026-08-13. Ground: the two were verified
  equal to within floating-point summation noise across two closed months, at
  aggregate and per-SKU level, lossless in both directions. The summary
  endpoint is natively monthly, echoes the period it served, and rejects an
  out-of-range one outright; the detail endpoint does none of the three and
  answers 200 to an out-of-range month and to an empty one alike, so it is
  there that the two are indistinguishable. That asymmetry is why the summary
  endpoint is the source, not a property both share. Per-repo Actions
  attribution was available and is declined: the detail endpoint carries a
  repository the summary does not, Copilot spend is repo-attributable under
  neither, and the field stays on the detail endpoint if it is ever wanted.`
  `[Corrected 2026-08-13 at t2 r1: the indistinguishability sentence was wrong
  as published at e4fabb7. The conclusion is unchanged.]`

## Ticket set

- **t1 — extend the canonical type vocabulary by one member.** Scoped below.
  Ships no adapter and no rule.
- **t2 — the GitHub adapter.** Unscoped. Scoped from t1's packet. Carries D1,
  D3, D4 and D7, the five-place wiring, the credential convention including
  its refusal half, and the period echo assertion.
- **t2c — the report's evaluation-coverage statement is false whenever a
  canonical type has no rule keying on it.** Scoped below.
  `compose_report_data` derives what the rule catalog did *not* cover
  from membership of `CANONICAL_TYPES`, which stood in for *matched by some
  rule* only while those two sets coincided — **t1 ended that coincidence** by
  adding `seat` ahead of any rule keyed on it. **Live now, on every GitHub
  run:** the report tells an operator that every type is one the catalog
  evaluates and that the totals cover the whole inventory, over six resources
  no rule can match. The claim it makes is one of **completeness**, which is
  why it is worse than a report that reads as broken — a broken-looking report
  gets investigated, and this one reports a clean zero. Detail, mechanism and
  the exact sentences are in `docs/m6-t2b-implementation-notes.md`.
- **t3 — the seat orphan rule.** Unscoped. Scoped from t2's packet. First rule
  in the catalog to key on an activity timestamp rather than an age. It also
  **decides what `monthly_cost_estimate` means for a consumption provider
  rather than discovering it**: its saving figure comes from that field, and
  for GitHub the field is month-to-date on an in-flight month rather than a
  monthly rate — `fetch_github.seat_monthly_cost` returns
  `pricePerUnit × (netQuantity / seat_count)` and `netQuantity` is user-months
  consumed so far, so the same six seats estimate at **7.97** for the in-flight
  `2026-08` against **19.00** for the settled `2026-07`, while `pricePerUnit`
  is `19.00`/user-month in both — the monthly rate is in hand, and what varies
  is the quantity it is multiplied by. DigitalOcean's
  equivalent is a true monthly price, so a seat orphan's saving is understated
  mid-month by a shrinking margin. Not an adapter defect — t2 reports consumed
  spend faithfully; a question about the field's meaning.

**t2c precedes t3** because t3 papers over the instance and leaves the
mechanism.

`[t2c added 2026-08-13 at the t2b review, by arbiter ruling, and t3's line
gained its `monthly_cost_estimate` clause in the same edit. The two figures were verified
against artifacts before being written: 2026-08 from t2b's own sprint run
(cloudcost/output/github/github_inventory_2026-08.json), 2026-07 from t2's
direct invocation (cloudcost/output/github_inventory_2026-07.json, generated
2026-08-13T06:43:09Z) — six seats each, identical resource-id sets, and the
arithmetic reproduced from the cost artifacts' own line items.]`

Storage-class entities — Actions artifacts, Actions caches, and packages — are
deferred as a group, on grounds that differ by entity and are recorded so a
later round does not re-derive them. Artifacts and caches are enumerable per
repository rather than per organisation, and their lifetime is governed by a
retention policy rather than by neglect. Packages are neither: they are
listable at organisation level and persist until deleted, so accumulation is
real. What defers them is that the credential form reaching them is not the
one this milestone's adapter uses, and that no packages product appears on
this organisation's bill — so their cost is unestablished rather than known to
be zero. All three share the one ground that matters: none carries a
per-instance cost. They return when that stops holding, or when packages' cost
is established — not when someone remembers them.

### t1 — extend the canonical type vocabulary by one member

**Scope.** The canonical resource-type vocabulary gains an eighth member,
`TYPE_SEAT = "seat"`, in `cloudcost/scripts/_normalized.py` and in
`CANONICAL_TYPES`. After this ticket the closed set can name a consumption-class
entitlement, and `cloudcost/milestone.md` records that the set spans two provider
classes rather than one. Nothing emits the new type: it is deliberately inert
until t2, and widening a closed set breaks no existing consumer, which is why it
lands first and alone. This ticket also lands the milestone document that owns
m6's tickets, because a ticket with no milestone document has nowhere to live.

**Contract refs.** `cloudcost/milestone.md` §Normalized schemas (the canonical
`type` table) and §Contracts **C1** — resource type vocabulary, including its
cross-repo clause. This document's §Ratified decisions **D6**, which grounds the
consumption class getting real canonical types rather than a cost-only lane.
`../aetheris/docs/methodology/milestone-methodology.md` §6 (ticket anatomy) and
§11 (reviewer-authoring discipline). `docs/milestones/hc-consolidation.md`
**R25**, which is why §Ratified decisions above is entries rather than sections.

**Touches.**
- `cloudcost/m6-github.md` (new)
- `cloudcost/scripts/_normalized.py`
- `cloudcost/milestone.md`
- `cloudcost/tests/test_detect_orphans.py`
- `../aetheris/scripts/sprint.sh` — **VERIFY ONLY, no edit.** Widening an
  imported set should require no harness edit; if it does, that turns this into
  a cross-repo pair with a landing order, which is a reviewer decision and a
  stop condition.

Anything outside this list needs a note in the implementation notes.

**Do not generate.** No adapter, no `fetch_github.py`, no GitHub API code of any
kind. No orphan rule; no change to `detect_orphans.py`, `RULES` or `MODIFIERS`.
No new schema **field** — this adds a type, not a field; concluding a field is
needed is a stop condition. No runbook §GitHub section, no credential
documentation, no `tools.json` entry — those are t2's. No canonical `state`
value for seats. No backlog row. No new milestone or specification document
beyond `cloudcost/m6-github.md` — this ticket's own implementation notes are a
required deliverable and are expressly not covered by that exclusion.
No t2 or t3 ticket anatomy: they are named and unscoped, deliberately.

**Runbook update rule.** This ticket introduces no environment variable, no
startup step, no configuration key, and changes no observable command semantics
— the new type is emitted by nothing — so it owes no runbook entry. Recorded
here explicitly rather than left as an unexplained absence. If that conclusion
turns out to be wrong, the runbook section joins `Touches` rather than deferring.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest cloudcost/tests/ -q
cd ~/sandbox/elixirws/aetheris && ./scripts/sprint.sh cloudcost
```

The sprint's rule-legibility arm must not change verdict. That arm is
non-blocking by construction — its failure path increments a counter and does
not halt — so a green summary is **not** sufficient evidence. The arm's own line
is quoted before and after the change.

**Claude-code prompt.** Carried by the ticket prompt of the claude-code session
of 2026-08-13 that landed this document, rather than copied here. Its record is
`cloudcost/docs/m6-t1-implementation-notes.md`; the reviewer amendments it was
executed under (the docstring edit's width, the count sweep, and this document's
provenance block) are recorded there with their grounds.

### t2c — the report's evaluation-coverage statement is false for a canonical type with no rule

**Scope.** `compose_report_data` gains a third evaluation state and a fourth
reading. It could previously distinguish only a type **outside** `CANONICAL_TYPES`
(a contract violation) from everything else, and used the second as a proxy for
*matched by some rule* — sound only while the canonical and rule-keyed sets
coincided, which t1 ended. After this ticket the report separates a contract
violation, a canonical type no rule keys on, and a canonical type some rule keys
on; says so where it previously claimed completeness; and says it does **not
know** where the orphan artifact declares nothing. `detect_orphans` gains a
declaration of what its catalog keys on and emits it on every artifact, so the
fact travels as data rather than being inferred across a CLI boundary. Ships no
orphan rule — t3 would make these sentences true for one type while leaving the
mechanism that reproduces them for the next.

**Contract refs.** `cloudcost/milestone.md` §Contracts **C1** (resource type
vocabulary) and **C5** (a figure shared across stages needs one home or one
assertion). `cloudcost/scripts/_normalized.py`'s module docstring — the repo rule
against cross-importing between CLIs, which decides where the rule-keyed set may
live. `aetheris-agents/CLAUDE.md` §Learning — m2b-docbuilder (that rule's home)
and `../aetheris/CLAUDE.md` **Silent-wrong-answer** (*absent is unknown, not
zero*) and **Adjacent-case**. `cloudcost/docs/m6-t2b-implementation-notes.md` §10a,
which established the defect. `../aetheris/docs/methodology/milestone-methodology.md`
§6 and §11.

**Touches.**
- `cloudcost/scripts/detect_orphans.py` — the declaration and its one output key
  **only**. No rule, no change to `RULES`, `MODIFIERS`, or any rule body.
- `cloudcost/scripts/compose_report_data.py`
- `cloudcost/templates/report.html.j2`
- `cloudcost/tests/test_compose_report_data.py`
- `cloudcost/tests/test_detect_orphans.py`
- `cloudcost/tests/test_render_report.py`
- `cloudcost/m6-github.md`
- `cloudcost/docs/m6-t2c-implementation-notes.md` (new)

Anything outside this list needs a note in the implementation notes.

**Do not generate.** No orphan rule of any kind, and no seat rule — t3. No new
canonical type, no schema change, no new first-class field on the normalized
resource schema. No change to any adapter. No harness change: concluding one is
needed is a stop condition. No backlog row — this ticket's originating finding
has a ticket, which is this one; a **new** finding follows the standing rule. No
new document beyond this ticket's implementation notes.

**Runbook update rule.** No environment variable, startup step, configuration key
or command semantic changes. The report's own wording changes, and no runbook
section quotes it — verified by census rather than assumed — so no runbook entry
is owed. Recorded explicitly rather than left as an unexplained absence.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest cloudcost/tests/ -q
cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest tests/ -q
cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/github-cloudcost.env && set +a && CLOUDCOST_PROVIDER=github ./scripts/sprint.sh cloudcost
cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/do-cloudcost.env && set +a && ./scripts/sprint.sh cloudcost
```

Both pytest scopes, because BL-152 means neither covers the other. **The third is
the deliverable**: the corrected sentences quoted against the false ones from a
run captured before the change, verbatim. A green suite is not the deliverable.
The fourth proves DigitalOcean unregressed, where **unregressed means no
unintended change rather than no change** — a sentence wrong on every provider is
fixed on every provider. The coverage pair must be byte-identical there; any
sentence that does change is quoted as its own intended before/after pair.

`[The fourth command's credential prefix was absent from the ticket as issued and
is recorded here as executed: without it the leg fails at the DO credential gate
and leaves the previous run's artifacts in place, which read as a pass to anything
that inspects the output directory rather than the exit. Found at t2c.]`

**Claude-code prompt.** Carried by the ticket prompt of the claude-code session of
2026-08-13 that landed this change, rather than copied here. Its record is
`cloudcost/docs/m6-t2c-implementation-notes.md`; the two arbiter rulings it was
executed under — the seam ruling with riders AE1–AE5, and the recent-activity
ruling with riders AF1–AF4, including the adjacent-case sweep AF4 ordered before
any edit — are recorded there with their grounds.

## Close criteria

Verify and record: t1, t2 and t3 landed with their done-checks clean; the
sprint's cloudcost arms report the same verdicts as at m6's open or better;
the runbook's provider list and wiring section include GitHub; what this
milestone **recovered** — spend eliminated or waste found — is recorded with
its basis alongside what it built; and every decision above is either applied
or carries a recorded reason it was not.

`[Clause added 2026-08-13 at t2b, by arbiter ruling. Ground: m6's scout found
unfilled paid seats before any adapter shipped, and a milestone whose subject
is recoverable spend should state its own. The criterion is that the figure is
recorded with its basis, not that any particular figure was achieved — a
recorded zero with its basis satisfies it.]`
