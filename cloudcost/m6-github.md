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
- **t3 — the seat orphan rule.** Scoped below. First rule
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
  spend faithfully; a question about the field's meaning. **Ruled at t3's gate:
  the adapter emits the rate.** Ground and blast radius in §t3 below.

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

### t3 — the seat orphan rule

**Scope.** The orphan catalog gains a seventh rule, `rule_idle_seat`: an assigned seat whose
last activity is older than a threshold is recoverable spend. It is the first rule in the
catalog keyed on an **activity timestamp** rather than on an age, and the first whose notion of
idleness is not C7's — `attached_to` is never null on a seat, so the universal unattached signal
cannot reach the case at all. `RULE_KEYED_TYPES` gains `seat` in the same commit (t2c §5c's
obligation), which makes the coverage sentences t2c corrected report the new state; after this
ticket the rule-keyed set and `CANONICAL_TYPES` coincide again, and that is not asserted
anywhere, deliberately. The ticket also **rules what `monthly_cost_estimate` means for a
consumption provider** rather than discovering it, and lands the correction the ruling names.

**The cost-model ruling (arbiter, 2026-08-14) — the adapter emits the rate.**
`fetch_github.seat_monthly_cost` returned `pricePerUnit × (netQuantity / seat_count)`, which is
month-to-date consumed spend; it now returns `pricePerUnit`. Ground: **a saving is
forward-looking** — this field feeds an orphan's `monthly_saving_estimate`, and a saving is what
stops being paid next month rather than what has already been spent this one; a seat reclaimed on
the 14th saves the full monthly rate from then on. And this is a **correction, not a
redefinition**: `milestone.md`'s §Normalized already defines the field as *"the provider's own
price where given"*, GitHub gives one in the same row, and DigitalOcean takes `price_monthly` for
exactly this reason. The alternatives were foreclosed by a constraint recorded at the gate:
`detect_orphans` consumes the **inventory only**, and `pricePerUnit` lives in the *cost*
artifact's `provider_extra`, which §Normalized forbids downstream from keying on generically — so
no rule can derive a rate, and carrying one on the resource is the inventory-shape ticket §S2
refused. The ruling authorises that one function, its tests and t2's §C14 notes, and nothing else.
Nothing is lost: the consumed user-months are still carried, in the cost line item's `usage_qty`
and in `provider_extra.usage_items`.

**Contract refs.** `cloudcost/milestone.md` §Contracts **C8** (thresholds and the scoring model —
what a new rule owes), **C7** (attachment, and the idle signal this rule is *not*), **C14**
(adapter cost-model obligations) and §Normalized schemas' `monthly_cost_estimate` bullet.
`docs/m6-t2-implementation-notes.md` §S2 (the seat lifecycle signal, carried nowhere, and its
reopening condition) and §C14. `docs/m6-t2b-implementation-notes.md` §10b (the month-to-date
finding this ticket rules on). `docs/m6-t2c-implementation-notes.md` §5c (the
`RULE_KEYED_TYPES` obligation), §7a and §8 (the fired-path obligation).
`../aetheris/docs/methodology/milestone-methodology.md` §6 and §11.

**Touches.**
- `cloudcost/scripts/detect_orphans.py`
- `cloudcost/scripts/fetch_github.py` — **`seat_monthly_cost` only**, per the ruling.
- `cloudcost/tests/test_detect_orphans.py`
- `cloudcost/tests/test_fetch_github.py`
- `cloudcost/tests/fixtures/inventory_seats_positive.json`, `…_negative.json` (new)
- `cloudcost/milestone.md` — §C8 gains the class's obligation entry
- `cloudcost/runbook.md` — the zero-orphan section, and the new knob
- `cloudcost/m6-github.md`
- `docs/backlog-2026-06.md` — BL-153 annotation, carried by this ticket's prompt and
  independent of its scope
- `cloudcost/docs/m6-t3-implementation-notes.md` (new)

Anything outside this list needs a note in the implementation notes. `[The list as issued named
neither this document, nor the backlog, nor `milestone.md`, nor the runbook; all four were
reported at the gate and three admitted by ruling. Recorded as a reviewer defect rather than a
deviation taken.]`

**Do not generate.** No schema change, no new first-class field, no new canonical type, no
canonical `state` value for seats. No adapter change beyond the one the cost ruling names —
concluding another is needed is a stop condition. No harness change. No change to
`compose_report_data.py` or the template: t2c made those sentences general, and a sentence that
reads wrongly for a type that now has a rule is a t2c defect to report, not to fix here. No
backlog row unless a genuinely new finding appears.

**Runbook update rule.** This ticket adds a CLI flag (`--seat-inactive-days`), which is a
command semantic, and it changes what a zero-candidate GitHub run *means* — from "nothing could
be evaluated" to "nothing qualified". Both are operator-facing, so the runbook **is** owed an
entry and gets one in §What a zero-orphan account means. Recorded explicitly rather than left as
an unexplained absence.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest cloudcost/tests/ -q
cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest tests/ -q
cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/github-cloudcost.env && set +a && CLOUDCOST_PROVIDER=github ./scripts/sprint.sh cloudcost
cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/do-cloudcost.env && set +a && ./scripts/sprint.sh cloudcost
```

Both credentialed legs check the **exit code before reading any artifact** (BL-153). The third
is where the report's coverage and modifier sentences are read against t2c's.

**The live run produces no candidate, and that is a result rather than a gap.** The stalest of
this organisation's six seats was last exercised 8 days before the run, against a 30-day
threshold, so the fired path is not reachable from live data at any defensible threshold — and
tuning one to reach it would be fabrication. Ruled at the gate: the sprint legs run as written
and their zero is the primary evidence, and the fired path is additionally exercised by a
**hand-invoked chain over the same live inventory with an explicit `--reference-date`**, in a
scratch directory, labelled at every point it is quoted, with a control run at the real current
date reproducing the sprint's zero. What that discharges is that the arm **renders correctly with
real data**; that it has been exercised by a live *sprint* run is not discharged and closes on
its own the first time a seat crosses the threshold. No ticket owns that, and none should.

**Claude-code prompt.** Carried by the ticket prompt of the claude-code session of 2026-08-14
that landed this change, rather than copied here. Its record is
`cloudcost/docs/m6-t3-implementation-notes.md`; the three arbiter rulings it was executed under —
the cost model with riders AI1–AI6, the fired-candidate exercise with AJ1–AJ4, and the C8 entry
with AK1–AK5 — are recorded there with their grounds.

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

---

## Dispositions — every candidate and every carried-in item

`Written at the close, 2026-08-14. Thirteen entries: eight promotion candidates this milestone
produced, and five carried in from gc's close. Every entry carries a state; the eight are
enumerated with their evidence and are the reviewer's to rule on, and the five are reported at
their carry count under R24 rather than disposed here — the close ticket reserves both verdicts.
Derivation in` `cloudcost/docs/m6-close-implementation-notes.md` `§4.`

### §Promotion candidates — eight entries, enumerated, none disposed

**The population is derived, not inherited.** m6 committed no review file and this document
carries no §Promotion candidates section, so §7 step 1's scan ran over the six
implementation-notes files and the runbook/`milestone.md` sweeps those tickets performed —
step 1's second paragraph being the authority for a scan whose review files are not merely
incomplete but absent. **The bar is ≥2 tickets**, and per the precedent m5 and gc both recorded,
instances inside one ticket or in reviewer-directed edits are not ticket recurrences however
many there are.

| # | candidate | tickets | bar | repo if promoted |
|---|---|---|---|---|
| 1 | a count in prose about a growing set is **de-numeralised, not corrected** | t1, t2b, t4 | **MET — 3** | **agents** — doc-sync family; its whole population is this repo's prose |
| 2 | a wiring list's **clause can be right while its enumeration is short**; repair it as an incomplete enumeration, not a missing clause | t2b, t4 | **MET — 2** | **agents** — the artefact is `cloudcost/runbook.md` §Adding a provider |
| 3 | a **generated artefact with consumers is itself a wiring place** | t4 | not met — 1 ticket; the second data point is a prior milestone | agents |
| 4 | a live run exercises **only the arm its data happens to be in**; the others need a named owner or a stated condition | t2c, t3 | **MET — 2** | **agents** — what a done-check can and cannot establish over this pipeline |
| 5 | an **LLM-written cell is unstable, not stale** | t4 | not met — 1 ticket; **BL-155 owns it** | agents |
| 6 | a report sentence true in one state and false in another **must say which state it is in** | t2c, t3 | met as a pair, but both instances are **one arc** — t2c authoring, t3 exercising — rather than an independent recurrence. The reviewer's call | agents |
| 7 | the **U2 discipline held for two packets and lapsed on the third**, with nothing detecting it | t3 | not met — 1 ticket. Recorded rather than excepted on severity | agents |
| 8 | a gate step **done out of order, recorded rather than smoothed** | t4 | not met — 1 ticket, and an instance of an already-promoted rule | n/a |

**Repo placement is decided by which family an entry joins, not by which file a ticket happens
to touch.** That is the correction gc's close owes: three of its entries landed harness-side
because t4's `Touches` named that file, while the packet-and-record family sits agents-side —
recorded on **BL-150**, and not repeated here.

### §Carried in from gc — five entries, all at carry count 2 under R24

`docs/milestones/gc-stale-claims.md:847-860` marks all five **first carry** and `:932-935`
forwards them to this close. **R24 forbids a third carry**, so each needs a verdict here; the
close ticket reserves that verdict for the reviewer, so they are reported rather than disposed.

| # | entry | gc's recorded bar | carry |
|---|---|---|---|
| 1 | a round whose first ticket runs in the session that creates the round document has no reviewable ticket anatomy | one instance (gc t1), ratified as a one-off at gc D3 | **2** |
| 2 | two documents can use one word in incompatible senses and neither is wrong | one instance; ruled at gc D2, owned by **BL-149** | **2** |
| 3 | a five-instance positive control caught a defect suppressing a fifth of the class | one instance (gc t1) | **2** |
| 4 | a reverse pointer that restates the rule it points at is a second copy of that rule | one instance (gc t2) | **2** |
| 5 | a discrimination required of one ticket is not required of its sibling unless the reviewer writes it twice | two instances, neither a ticket recurrence | **2** |

**gc's own §Carried in re-carries nothing.** All four of its items were disposed at gc t4 —
three promoted, and m5's deferred `mix dialyzer` obligation **discharged by running the gate**
(`Total errors: 0`, exit 0). It is not re-carried here.

### The prior-claims census — §7 step 4, and it is owed every close

gc's close claims four promotions, all into harness `CLAUDE.md`. Population derived from those
records rather than chosen by eye; run whitespace-normalised and case-insensitive on both passes.
**4 of 4 present. Nothing absent. No census promotion owed.** Negative control
`qqx-census-control-m6close-9174` returned 0 in both repos, verified before use.

**And the instrument reproduced the defect gc's own fourth entry describes** — the exact-string
pass on gc's candidate wording reported 3 of 4 ABSENT, all three present with drifted headlines.
Second consecutive demonstration on a close's own instrument. Recorded as a result; the rule that
predicts it is already in the file.

---

## Close criteria — the per-clause assessment

`Assessed at the close, 2026-08-14. Every clause individually, each pointed at the artifact that
satisfies it. A clause satisfied by nothing is stated unmet, not omitted.`

| # | clause | verdict | satisfied by |
|---|---|---|---|
| 1 | t1, t2 and t3 landed with their done-checks clean | **MET** | Each ticket's own record: t1 `docs/m6-t1-implementation-notes.md` §Done-check; t2 `docs/m6-t2-implementation-notes.md`; t3 `docs/m6-t3-implementation-notes.md:380-381` (465 passed after the full mutation matrix, *"which is where the tree is restored is actually discharged"*). Re-confirmed at this close: **465 passed** and **129 passed, 7 xfailed**, both exit 0 and both identical to t4's figures — the number that would have caught an accidental edit in a close that changes no executable line |
| 2 | the sprint's cloudcost arms report the same verdicts as at m6's open or better | **MET, and the two legs are met differently** | **DigitalOcean: byte-identical to m6's open.** `18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume]` — the same line as `docs/m6-t1-implementation-notes.md:316`, the r0-before reading. **GitHub: *better*, and it has no like-for-like baseline** — the leg did not exist at m6's open, arriving at t2b (`bcb63e6`); it reads `6 resources evaluated, 0 skipped; types [seat]`, unchanged against its within-m6 baseline at t3. Both legs exit 0, 76 lines, zero `[FAIL]`; the GitHub leg's single WARN is the ambient credential-shadow notice, non-blocking and unchanged since t2c. Offering a comparison against a baseline that never existed is what this clause exists to prevent, so it is not offered |
| 3 | the runbook's provider list and wiring section include GitHub | **MET** | `cloudcost/runbook.md:4` (provider list), `:154` §GitHub, `:221-231` (wired into the pipeline, with its invocation), `:271-280` §Run it, `:325` sprint cases, `:535-536` credential rows, `:550-554` the selector and its `case` citation. Landed by t2b and completed by t4, which is the ticket this criterion had been failing against for nine days |
| 4 | what this milestone **recovered** is recorded with its basis | **MET as to the record; one of its two entries records a *non-*recovery** | §Milestone summary → *What m6 recovered*. **Entry 2 is a measured zero with its basis** — six seats, stalest 8 days idle, threshold 30 untouched — which the clause's own ground says satisfies it, re-confirmed live at this close (`totals.candidates 0` over `totals.resources 6`). **Entry 1 records that the figure is not established**: no before-state exists anywhere, and a live read at 2026-08-14T09:01:53Z returns three unfilled organisation seats — the same count the attestation names as removed. The removal is operator-attested; the recovery is not established. Derivation and controls: `docs/m6-close-implementation-notes.md` §2a |
| 5 | every decision above is either applied or carries a recorded reason it was not | **MET — seven of seven, none unapplied** | **D1** `scripts/fetch_github.py:97-111`, `:503`, `:537-540`, and the staleness guard at `:790-795`. **D2** `--period YYYY-MM` only (`:864`, validated `:391`); no daily, hourly or per-SKU emission. **D3** `money()` = `round(float(v), 2)` (`_normalized.py:92`), its sum site taking full precision and rounding once after (`fetch_github.py:497`), pinned at `tests/test_fetch_github.py:396`. **D4** applied at t2 and pinned by mutation row M4 — and it **stopped binding at t3**, whose ruling removed the multiplication that was its only site in this adapter; the function's docstring states that rather than leaving it an absence, and replaces the pin with the opposite property (`tests/test_fetch_github.py:738`, `:812`). D4's entry above stands unamended while §t3 carries the change. **D5** is **not applicable yet, with its reason**: it governs *"BL-136's report, when built"*, and BL-136 is unbuilt and was never in m6's scope — this is the clause's *carries a recorded reason it was not* arm, not a gap. **D6** t1's `TYPE_SEAT` and `CANONICAL_TYPES`, t2's seat resources, and the three-part bound applied against `seat_breakdown` and organisation members, both refused for failing two of three legs. **D7** `fetch_github.py:4-5`, `:29-34`, `:144`, the period echo at `:706-711` and `reconcile_detail` at `:717-745`; its published ground was corrected at t2 r1 with the conclusion unchanged |
| — | *(the operator gate — not a close criterion, and discharged here)* | **DISCHARGED 2026-08-14, by the operator** | Rig's Agents view lists `fetch_github.py` with the label `Cloudcost`; an Orchestrator run with `CLOUDCOST_PROVIDER=github` in *Additional env vars* planned `cloudcost_orchestrator.exs` as a GitHub run and produced a report. Both legs of `docs/m6-t4-implementation-notes.md` §9, which carries a dated discharge block appended at this close. Observed by the operator rather than by a session, which is §9's own point |

---

## Milestone summary

`Written at the close, 2026-08-14, per §7 step 5. Placement derived: last in the file, after the
dispositions and the per-clause assessment, which is where` `docs/milestones/gc-stale-claims.md`
`and` `cloudcost/m5-n1-compose.md` `both put theirs.`

### What shipped

**A class, not a provider.** m6's first paragraph says the decisions belong to the consumption
class rather than to GitHub, and the milestone was built that way: an eighth canonical type, an
adapter, a rule keyed on activity rather than age, and a cost-model ruling that will bind Google
Workspace and AI spend before either has an adapter.

- **t1** extended the canonical vocabulary by one member, `TYPE_SEAT`, and ran the count sweep
  that found — and de-numeralised — prose stating the set's size, including two count-bearing
  lines the ticket had itself just written.
- **t2** shipped `fetch_github.py`: provider four, and the first consumption-class adapter.
  D7's summary-endpoint choice was verified live against the detail endpoint across closed
  months, and its published ground was corrected at r1 with the conclusion unchanged.
- **t2b** made it selectable — `CLOUDCOST_PROVIDER=github` runs the four-stage pipeline end to
  end, `tools.json` declares it, and the sprint gained a GitHub leg. It also established that
  the ambient shadow arm warns rather than fails, so the next round in this class does not pay
  to re-derive it.
- **t2c** made a false claim true. The report told an operator that every type was one the rule
  catalog evaluates, over six resources no rule could match, and it reported a clean zero — a
  completeness claim, which is worse than a report that looks broken. Replaced with three
  evaluation states and a fourth reading.
- **t3** added the seat orphan rule, the first in the catalog to key on an activity timestamp,
  and **decided what `monthly_cost_estimate` means for a consumption provider rather than
  discovering it**: the adapter emits the rate. It also demonstrated the fired path over live
  data with a control, and split the obligation rather than declaring it closed.
- **t4** repaired the provider-set enumerations m6 was short — including the capability matrix,
  which is read whole into the planner's system prompt, so a script absent from it is a script
  the planner cannot plan — and extended the wiring list that had not named them.

**Behaviour is unchanged by the close itself.** `465 passed` and `129 passed, 7 xfailed`, both
identical to t4's figures; no executable line changed anywhere in this close.

### What m6 recovered

Two entries, with different bases, per §Close criteria clause 4.

| # | figure | basis |
|---|---|---|
| 1 | **unfilled paid seats — count not established** | Found by inspection during m6's scout, before any adapter existed; the operator's removal is **attested**, dated to the attestation (2026-08-14) rather than to an inferred action date, which is not established. **No before-state exists in any committed file, fixture or scratchpad** — searched with a positive and a negative control. And the strongest check available **does not corroborate a recovery**: `GET /orgs/{org}` at 2026-08-14T09:01:53Z returns `plan.seats 19`, `plan.filled_seats 16` — three unfilled organisation seats, the same count the attestation names as removed, still unfilled. Two readings remain open and this close settles neither: the removal did not reduce purchased seats, or it did and three further seats have since become unfilled. **The offered figure is not carried into this register**, on the ruling that a figure entering it must be independently established |
| 2 | **zero recoverable Copilot seats — a measurement** | The rule t3 built, over live data. Six seats; the stalest 8 days idle at reference date 2026-08-14; nothing fires at the ruled threshold of 30 and nothing at 14 either, and no threshold was moved to produce a candidate. Re-confirmed by this close's own GitHub sprint leg: `totals.candidates 0`, `monthly_saving_estimate 0`, over `totals.resources 6`, `seat_inactive_days 30`. **This is a different statement from the same figure a day earlier**, when it meant no rule could evaluate those six resources at all — which is the whole of t2c and t3's arc |

**The pair is the better first exercise of this criterion than either half would have been**,
because the two figures were established by different means — one by inspection, one by code —
and because the one established by inspection is the one that did not survive checking.

### What the close found

- **The recovered-spend clause worked on its first run by failing to confirm its own first
  entry.** It was added so a milestone states what it recovered *with a basis*; its first entry
  turned out to carry a figure that lives in a conversation and nowhere else, and the one live
  check available returned the same number still outstanding. A register reading *count not
  established*, beside an observation that contradicts the claim, is a better artefact than a
  confident three nobody can check. Reported; nothing opened and nothing fixed.
- **This §Ticket set names four of the six tickets that shipped.** t1, t2, t2c and t3 have
  entries; **t2b and t4 do not** — t2b appears only in prose cross-references, t4 nowhere in
  this document, though both shipped and t4 is the ticket that discharged close criterion 3.
  Reported and **not added**: adding a ticket entry after the fact is a scoping act and this
  document is the reviewer's.
- **§7's own success test cannot be run on this milestone.** The test is that a finding class
  should not appear as `blocking` in two consecutive milestones — and **m6 committed no review
  file**, so no finding here carries a label this close can read. Stated rather than answered
  green. The two defects that did stop work were found by the tickets themselves.
- **The harness-gate premise was checked rather than asserted, for the first time.** The
  harness *has* moved once since gc discharged `mix dialyzer` — `scripts/sprint.sh` at t2b, and
  nothing else. No Elixir gate reads that path, established with two positive controls, so no
  gate is re-run. The next close inherits the check, not the conclusion.
- **§7's prior-claims census returned 4 of 4 present** — and its exact-string pass returned 3 of
  4 falsely absent, reproducing the defect gc promoted for exactly this, on this close's own
  instrument.

### What stays open, and why that is correct

- **Entry 1 of the recovered-spend register.** Open as a question about a figure, not as work.
  Settling it needs billing history across the period, which is establishment work no row owns
  and this close does not invent one for.
- **BL-153's arm-ordering ruling.** A reviewer call rather than an obvious fix, and t3
  deliberately prepended its second mechanism *before* the row's `**Owes:**` line so the
  question stayed visibly untouched.
- **BL-155's stated unknown.** Eight of nine capability-matrix sections were not regenerated at
  t4 and have not been checked against their source trees; the byte-identity t4 established says
  the on-disk sections match the committed document and says nothing about whether either matches
  the code. Last full regen `4d98ec2`, 2026-08-05.
- **BL-114.** Its state moved in m6 — t3 rendered the modifier's *applied* arm for the first time
  on any provider — but only through a labelled hand-invoked chain at a shifted reference date,
  never a live sprint. The row's question, whether a permanently-dead scoring path stays, is
  untouched by that.
- **t2c's split obligation, and it has no owner by design.** What t3 discharged: the
  fired-candidate arm, the modifier's applied arm and the coverage sentence for a now-ruled type
  render correctly over real data. What it did not: that a live *sprint* run has exercised them.
  **That closes on its own the first time a seat on this account crosses 30 days idle. No ticket
  owns it and none should** — it is a condition, not a work item. This close's GitHub leg did not
  close it: 0 candidates at reference date 2026-08-14T08:59:51Z, the stalest seat still 8 days
  idle against a threshold of 30.

### Open for the next cycle

**Eight promotion candidates, first carry** — §Dispositions. Under **R24** each is promoted or
dropped at the next close and cannot be carried a third time. Three clear §7's ≥2-ticket bar
(1, 2, 4), one clears it as a pair whose independence is doubtful (6), and four do not.

**gc's five candidates, at carry count 2, awaiting a verdict that R24 requires at this close.**
They are reported in §Dispositions and are not disposed there; the close ticket reserved that
verdict for the reviewer, so **this entry is conditional on that ruling** and is the one line in
this section that is.

**Six backlog rows, verified open at HEAD** against row bodies — the surface BL-145's ruling made
authoritative — with a positive control on four rows known closed:

- **BL-150** (documentation-system findings) and **BL-151** (code findings) are **standing and
  append-only**; neither closes on any single item, and a finding of either kind in the next
  round appends there rather than opening a row. m6 appended to both.
- **BL-152** — the repo-root `pytest` invocation cannot collect, which is why every m6
  done-check runs both scopes.
- **BL-153**, **BL-154**, **BL-155**, **BL-156** — the four rows t4 filed or annotated. BL-156
  gained a second observed instance at this close, from the same click-through that discharged
  the operator gate; it does not close the row.

**BL-114** carries forward with what m6 changed about it, above.

**Nothing sequences after this milestone.** The next member of the consumption class is Google
Workspace, named in this document's first paragraph and holding no ticket; the decisions it will
meet are D1–D7 and C8's entry in `cloudcost/milestone.md`, which is where t3 put them precisely
because a contract crosses arcs and an implementation-notes file does not.
