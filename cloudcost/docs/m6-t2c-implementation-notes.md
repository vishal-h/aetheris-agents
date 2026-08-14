# m6 t2c — the evaluation-coverage statement, made true or made to say something else

**Ticket:** `cloudcost/m6-github.md` §Ticket set → §t2c. **Built:** 2026-08-13.
**Measured at:** agents `bcb63e6`, harness `d19f4b6` (both level with origin, trees clean).

**Deliverables.** `scripts/detect_orphans.py` (a declaration and one output key —
no rule, no change to `RULES` or `MODIFIERS`), `scripts/compose_report_data.py`,
`templates/report.html.j2`, `tests/test_detect_orphans.py`,
`tests/test_compose_report_data.py`, `tests/test_render_report.py`,
`m6-github.md` (§t2c anatomy + the §Ticket set bullet re-pointed), these notes.

Written for the next round in this arc — t3, which adds the seat rule and inherits an
obligation named in §5.

---

## 1. The gate, and the two places the prompt was wrong

**(i)** Both repos level with origin, trees clean, at t2b's commits. **(ii)** t2b §10/§10a
read and verified at HEAD rather than taken: `compose_report_data.py:578`, the N8/BL-117
comment at `:594–596`, `TYPE_SEAT`'s presence in `CANONICAL_TYPES` and absence from every
rule, and §10a's six-resource claim against `report_data_2026-08.json`. No disagreement with
the prompt. **(iii)** §2. **(iv)** §7.

**Two deviations, both in the prompt's done-check block, both recorded in §t2c's anatomy.**

**(a) is now BL-153.** Filed at the review's direction — it produced false evidence inside this
session, so it is the BL-152 class (a verification mechanism that can silently yield a wrong
answer) rather than the BL-151 class (defects that break nothing today). **Not fixed here:** it is
harness-side, outside this ticket, and the arm ordering is a reviewer decision — the row records
three defensible shapes and the trade between them.

**(a) Done-check 4 could not run as written.** `./scripts/sprint.sh cloudcost` with no
credential prefix fails at the DO credential gate. **The failure mode is the dangerous
one**: the leg bails *before* the stale-artifact guard clears
`cloudcost/output/digitalocean/`, so the previous run's report and JSON are still sitting
there, with the right names, the right period, and content that parses. A first pass took
them for a live capture; what caught it was checking the exit and diffing against the
preserved baseline, not reading the artifacts — they are indistinguishable from a real run
by content alone. The command is recorded in §t2c with `set -a && . ~/.secrets/do-cloudcost.env`.

**(b) Done-check 4's expectation does not hold literally** — §4.

---

## 2. Gate (iii) — the before-state, from a live run

Captured from `CLOUDCOST_PROVIDER=github ./scripts/sprint.sh cloudcost` at HEAD **before any
edit**, run `cloudcost-orch-github-qNrMIQ`, 2026-08-13 17:52, exit 0, 76 lines, zero `[FAIL]`,
one WARN (the ambient credential-shadow notice, which the prefix strips). The three sentences
§10a names, verbatim from the rendered report:

> Every resource in this denominator carries a type the rule catalog evaluates; none is
> counted here and evaluated nowhere.

> Of 6 usable resource(s), every type is one the rule catalog evaluates — 0 carried a type
> outside it, so the totals above cover the whole inventory.

> 6 resource(s) carry last_activity_at, so the recent-activity modifier was applied; where it
> does not appear on a candidate it did not match.

t2b's own artifacts were preserved to scratchpad first, because the sprint clears the output
directory it writes into and done-check 4 quotes against them.

---

## 3. W1 — the seam, and why the other three were refused

The rule-keyed type set exists only as seven `if resource.get("type") != …: return None` lines
inside rule bodies. Four options were reported with their blast radius; the arbiter ruled
**B1 — a new top-level key on the orphans artifact** (riders AE1–AE5). The ground was positive
rather than eliminative: the fact lives where the catalog lives, travels the way the pipeline
already moves data, needs no import, and is legible to a human reading the JSON.

**The three refusals are recorded here because a later round will reach for one of them.**

- **A — `compose_report_data` imports the set from `detect_orphans`.** Ruled out by the repo's
  own rule, not by taste: both are CLIs, and `_normalized.py:8–9` names cross-importing between
  CLIs as the anti-pattern. `docs/t3-implementation-notes.md` §Scope note is the precedent —
  seven functions were moved *out* of `detect_orphans.py` into `_normalized.py` rather than
  cross-imported, for exactly this reason.
- **C — declare it in `_normalized.py`.** Refused on the strongest ground available: that module
  is the **schema** seam, and which types have rules is a property of the rule **catalog**.
  Declaring it there would say the schema knows which of its types are evaluated — *precisely
  the conflation that caused this defect*. C is the same mistake one layer up, and recording
  that is worth more than recording the choice.
- **B2 — inside the artifact's `parameters` block.** Mislabels it. A parameter is something a
  run can be configured with; this is derived from the catalog and is not settable.
- **E — per-rule metadata on `RULES`, so the keying is a declaration rather than an early
  return.** Not wrong, **early**. Nothing needs per-rule granularity yet, and it couples this
  fix to a refactor of `RULES` that t3 also touches. **This is the natural evolution if a need
  appears** — recorded so it is not re-derived from scratch.

---

## 4. AF4 — the adjacent-case sweep, run before any edit

The recent-activity sentence was the second member of its class found *by accident*. The
arbiter ordered the class enumerated rather than the second instance fixed.

**Class:** any sentence whose truth depends on a stage having run, or on candidates having
fired, and which renders the same way when neither happened.
**Population:** 53 prose blocks in `report.html.j2`'s body (after `</style>`) — 16 `note`,
16 `empty`, 10 `caption`, 6 `from-to`, 5 `caveat` — plus the 3 prose strings the composer
composes (`granularity_note`, `estimate_note`, `mom_delta.reason`). **56, every member read.**
**Positive control:** the enumeration returns the three already-known sentences, so the search
reaches its target.

**Thirteen in the class. Five defective, and two of those were new:**

| Line | On a zero-candidate inventory | |
|---|---|---|
| `:402` | **FALSE** — "Every resource in this denominator carries a type the rule catalog evaluates" | known |
| `:522` | **FALSE** — "so the totals above cover the whole inventory" | known |
| `:532` | **FALSE** — "so the recent-activity modifier was applied" | known |
| `:505` | **VACUOUS** — caption "the cutoffs **these candidates were grouped by**"; the band table renders and nothing was grouped | **new** |
| `:599` | **VACUOUS** — "**They are shown** so a candidate can be judged"; nothing is shown | **new** |

**Eight sound, and three of them are the register the fix was written to** — `:466` (the
untagged-in-tagged rule declining to run, with its threshold arithmetic), `:473` ("whether it
ran, and what it found, is unknown here"), `:632` ("refused, so the signals they would have
produced are **unknown, not zero**"). `:687` already self-qualifies — *"No signals were raised
**by the calls that ran**"* — which is this exact class, handled correctly, five years of
report-writing before anyone named it. Also sound: `:542`, `:463`, `:592`, `:496`.

**Forty-three not in the class**, each read: cost summary, granularity, service groups, MoM
headline and caveats, tag-coverage headline, cap notes, per-candidate blocks, optimization
figures, data notes, and the three composed strings.

**Disposition.** Both new hits are in `report.html.j2`, inside Touches, so both were fixed
here and **no backlog row is owed** — nothing in the class fell outside Touches. Minimal
rewords rather than gates: present-tense generic caption, and "shown, **where present**".
Both change DigitalOcean's output too; §6 quotes them.

**The sweep is not clean, and that is its finding.** Two accidental discoveries became five
class members once the class was enumerated instead of fixed one instance at a time.

---

## 5. What was built

### 5a. `detect_orphans.py` — a declaration and one key (AE5)

`RULE_KEYED_TYPES` sits beside `RULES`; `detect()`'s return gains
`"rule_keyed_types": sorted(RULE_KEYED_TYPES)` at top level. No rule, no change to `RULES`,
`MODIFIERS`, or any rule body.

### 5b. `compose_report_data.py` — three states and a fourth reading

| State | Field | |
|---|---|---|
| (a) | `uncatalogued` *(unchanged)* | outside `CANONICAL_TYPES` — a contract violation |
| (b) | `unevaluated` / `unevaluated_count` | canonical, no rule keys on it — **not** a violation |
| (c) | remainder | canonical and rule-keyed |
| unknown | `rule_coverage_known: false` + `providers_without_rule_coverage` | AE3 |
| guard | `rule_keyed_contradictions` | AE4 |

**AE3 — the unknown is a fourth reading, not a fallback.** A bundle whose artifact declares
nothing has its resources classified into neither (b) nor (c): nothing here knows which they
are. A *malformed* declaration is treated identically to an absent one — asserting over it
would be asserting over whatever shape happened to arrive. `orphans_soc_2026-07.json`, a
committed fixture produced by the real t2 CLI before this key existed, is a genuine instance
rather than a constructed one, and a test pins that.

**The modifier's third state.** `MODIFIERS` run inside `score()`, which the engine reaches only
for a resource a rule already fired on. With zero candidates the stage never ran — regardless
of what the inventory carries. That state was previously reported as `applicable`, i.e. *applied
and did not match*, over an empty candidate set.

### 5c. AE4's guard, and the residual stated honestly

A candidate whose type the artifact does not declare is a contradiction: some rule evidently
keyed on it, so the declaration is stale. The composer detects it, raises a warning into the
report's own warnings channel, and the template **withholds the coverage sentences entirely** —
a figure computed from a known-wrong set is worse than no figure.

**What the guard does not catch, said plainly rather than implied: a rule added without
updating `RULE_KEYED_TYPES`, which then fires on nothing.** The guard covers the other
direction only. Its error direction is conservative — the report **understates** coverage
rather than overstating it — and after this ticket understating is the safe side.

> **OBLIGATION FOR t3.** t3 adds the seat rule and is the first test of whether the set gets
> updated. Adding a rule without adding its type to `RULE_KEYED_TYPES` produces a report that
> silently under-reports coverage and a green suite. **Update `RULE_KEYED_TYPES` in the same
> commit as the rule.** This is written here so t3's author meets the obligation rather than
> discovering it.

### 5e. The inline lists are capped, in the house form (AG3)

The corrected coverage sentence lists offending resources **inline, inside a sentence** — six
seats read fine, but Google Workspace is close to pure seats and is the next member of this class,
where a few hundred unruled resources would render as a paragraph-length list mid-sentence.

The rendering did **not** already cap: `uncatalogued` had been uncapped since m4 t5c, and
`unevaluated` and `rule_keyed_contradictions` inherited that. The house form exists —
C11 / BL-121, *"caps report their truncation"*, as the untagged-spenders table does with
`top_k` + `untagged_not_shown` and its *"the cap of 10 dropped none"* — so all three lists now
follow it, via a `cap_note()` macro that states the form once rather than three times.

Two properties worth naming because they are what make the cap safe:

- **The cap bounds what is SHOWN, never what is CLAIMED.** `uncatalogued_count` and
  `unevaluated_count` stay the full counts, so the sentence's arithmetic — *"a result over N
  resource(s), not M"* — is unchanged by truncation. A capped list cannot make the report
  understate.
- **A payload with no `*_not_shown` says nothing about a cap** rather than claiming one. An older
  `report_data.json` predates these keys; the macro emits nothing for it. Absent is unknown, not
  "nothing was dropped".

`COVERAGE_LIST_CAP = 10` is its own constant, ten by convention with the spenders table rather
than by coupling — a shared knob would tie two unrelated caps to one CLI flag.

**A cap was taken rather than declined.** The argument for leaving it uncapped is that the list is
the evidence and a partial list is worse than a count. It does not hold here: the *count* is
carried separately and in full, the truncation is stated with its cap, and the sentence's purpose
is to establish that a set exists and is not evaluated — which a bounded sample plus an exact
count does as well as an exhaustive list, and which an unreadable paragraph does worse.

### 5d. W4 — generality, and why the tests do not name a real type

Nothing in the fix names `seat`, GitHub, or any type: the composer compares two sets and the
template branches on counts and a boolean. `test_compose_and_render_key_on_no_type_value`
already enforces this — it asserts the composer, the renderer **and the template** contain no
canonical type literal — and it passes unchanged.

**B1 is what made W5 testable without naming a real type.** Because the set travels as *data*,
a fixture declares `rule_keyed_types: ["volume"]` over an inventory carrying `compute_instance`
and the rest: the divergence is synthesized from two ordinary canonical types. No test needs to
know which type currently lacks a rule, so none goes stale when t3 adds the seat rule.

---

## 6. Verification

**Both pytest scopes** (BL-152: neither covers the other) — `cloudcost/tests/` **451 passed**,
`tests/` **129 passed, 7 xfailed**.

### 6a. The mutation matrix (the t1 hazard)

t1 recorded that `test_the_rules_key_only_on_canonical_type_values` opens with an exact
set-equality that short-circuits everything after it, so an assertion appended there can ship
having never run against a failing state. **The new detect_orphans assertions were therefore
put in their own function**, where nothing precedes them — the structural answer rather than a
procedural one.

Sixteen rows, one mutation each, each expected to fail one named test. **All sixteen RED**, each
naming a *distinct* raising assertion — which is what shows each assertion was exercised
individually rather than one of them shadowing the rest. Every restore verified as its own claim
with a control on both sides (original `1→0→1`, mutant `0→1→0`).

Two rows needed correcting before they meant anything, and the corrections are the point:
- **A3's first form was a false control.** The mutant string *contained* the original, so the
  "original absent" check read `1→1→1` and the harness said RESTORE UNVERIFIED. A control whose
  pattern matches its own replacement is not a control.
- **E's target spanned two lines**, and `grep -cF` treats an embedded newline as two alternative
  patterns, so it reported a count of 2 and the row never ran. It reported SETUP-FAIL rather than
  passing quietly, which is the only reason it was noticed.
- **The "which assertion raised" capture was itself wrong on first run** — it matched pytest's
  *context* lines, which include assertions that passed. Only the line pytest marks with `>` is
  the failing statement. Before the fix, three rows were credited to the wrong assertion.

**The negative assertions were exercised separately**, outside the test function, under the
mutation that reinstates the original defect (`{% elif ec.uncatalogued_count or
ec.unevaluated_count %}` → `{% elif ec.uncatalogued_count %}`, so a (b)-only inventory falls
through to the completeness claim). Both
`assert "so the totals above cover the whole inventory" not in body` and
`assert "every type is one the rule catalog evaluates" not in body` **failed** under it, and the
restore was verified on both sides. That mutation is the closest thing to the live defect, and
the tests catch it.

**Residue sweep:** zero mutation strings survive in `cloudcost/scripts` or `cloudcost/templates`
— with a **positive control** (the same patterns over the mutation driver itself return 9), so
the zero is an observation about the tree rather than about the command.

### 6b. One pre-existing vacuous assertion, found and fixed

`test_several_uncatalogued_resources_are_all_listed` asserted
`[...] == sorted([...], key=...) or True`, which parses as `(A == B) or True` — always true. The
list's contents had never been asserted. **It is in this ticket's Touches and was one line, so
it was fixed rather than filed.** De-vacuuming it immediately failed: the composer sorts by
`(provider, resource_id)`, which for that fixture is *not* the order the three names were
assigned in. The expectation is now derived from the fixture rather than hand-typed, so it
cannot go stale against a re-recorded inventory, and a guard asserts the two orders really do
differ.

### 6c. The one test the change broke, and why that was correct

`test_several_uncatalogued_resources_render_as_a_punctuated_list` writes `evaluation_coverage`
**whole** rather than merging into a composed one, so its payload lacked the new keys — a
payload from before t2c. The template correctly rendered the *unknown* sentence instead of the
list. That is the new behaviour working, not a regression in it; the fixture gained the keys the
composer now emits, and a comment says why.

### 6d. The two sprint legs, and the pairing that is the deliverable

Both live, both after the change, both `exit 0`, 76 lines each, **zero `[FAIL]`**. GitHub carries
one WARN — the ambient credential-shadow notice, unchanged from the before-run and stripped by
the prefix. The rule-legibility arm is unchanged on both legs: *6 resources evaluated, 0 skipped;
types [seat]* and *18 resources evaluated, 0 skipped; types [compute_instance, load_balancer,
volume]*. Seat logins are scrubbed below per **U2**, whose class binds this document and the
packet, not only the fixtures.

**GitHub — all five in-class sentences corrected.**

| | |
|---|---|
| before | Every resource in this denominator carries a type the rule catalog evaluates; none is counted here and evaluated nowhere. |
| after | The 6 resource(s) above include 6 carrying a canonical type no rule keys on yet. They count toward this coverage ratio and are evaluated by no rule — see Orphan candidates. |
| before | Of 6 usable resource(s), every type is one the rule catalog evaluates — 0 carried a type outside it, so the totals above cover the whole inventory. |
| after | Of 6 usable resource(s), 6 carry a canonical type no rule keys on yet — also counted in the totals above and in the tag-coverage denominator, and evaluated by nothing — `<seat-1>` (seat), … `<seat-6>` (seat). That is a stated boundary of the catalog rather than a fault in this inventory — a canonical type may exist before any rule keys on it, and until one does, its resources are counted everywhere and evaluated nowhere. **A candidate count of 0 is therefore a result over 0 resource(s), not 6.** |
| before | 6 resource(s) carry last_activity_at, so the recent-activity modifier was applied; where it does not appear on a candidate it did not match. |
| after | No rule fired on this inventory, so the recent-activity modifier never ran: modifiers adjust the confidence of a candidate, and there is no candidate to adjust. This says nothing about whether the modifier would have matched — the stage was not reached. 6 of 6 resource(s) carry last_activity_at, which is what it keys on. |
| before | Confidence bands — the cutoffs **these candidates were grouped by** |
| after | Confidence bands — the cutoffs **candidates are grouped by** |
| before | … **They are shown** so a candidate can be judged … |
| after | … **They are shown, where present,** so a candidate can be judged … |

**DigitalOcean — unregressed, in the sense AF3 defines: no *unintended* change.** Two claims,
proved separately.

*The coverage pair is byte-identical*, which is the arm done-check 4 exists for:

> Every resource in this denominator carries a type the rule catalog evaluates; none is counted
> here and evaluated nowhere.

> Of 18 usable resource(s), every type is one the rule catalog evaluates — 0 carried a type
> outside it, so the totals above cover the whole inventory.

*Three sentences change, every one of them intended.* DO's 2026-08 run also has **zero
candidates**, so its modifier sentence was vacuous for the same reason GitHub's was false — it
quantified over "every candidate below" where there were none:

| | |
|---|---|
| before | No resource carries last_activity_at, so the recent-activity modifier could not fire on this inventory — **its absence from every candidate below means it was inapplicable**, not that it was applied and found nothing. The window in the parameters block is therefore not a tuned setting here. |
| after | No rule fired on this inventory, so the recent-activity modifier never ran: modifiers adjust the confidence of a candidate, and there is no candidate to adjust. This says nothing about whether the modifier would have matched — the stage was not reached. 0 of 18 resource(s) carry last_activity_at, which is what it keys on. |

The other two are the AF4 sweep rewords, which change on every provider by design — a sentence
wrong everywhere is fixed everywhere.

---

## 7. Companion artifacts (gate iv) — no omission to report

`scripts/compose_report_data.py` → `tests/test_compose_report_data.py`;
`scripts/detect_orphans.py` → `tests/test_detect_orphans.py`;
`templates/report.html.j2` → `tests/test_render_report.py`. All three within Touches, which
named `cloudcost/tests/` and asked for the modules to be established.

**Two negatives, checked rather than assumed.** *Runbook rule does not fire* —
`grep -rn "evaluation_coverage\|uncatalogued"` over every `*.md` outside `cloudcost/docs/`
returns two hits, both `docs/backlog-2026-06.md`; `cloudcost/runbook.md` and
`cloudcost/milestone.md` carry neither term, so no operator-facing document quotes these
sentences. *Harness untouched, and not concluded otherwise* — the sprint's rule-legibility arm
reads `orphans["skipped"]`, `orphans["totals"]["resources"]` and `CANONICAL_TYPES`. This ticket
adds no skip category, changes no total, and does not touch `CANONICAL_TYPES`, so **BL-117's
cross-repo coupling is not engaged and BL-117 is not advanced** — `usable_resources` is
untouched and the uncatalogued resource is still usable and still counted, exactly as at m4 t5c.
Both sprint legs re-ran green after the change, which is where that claim is discharged rather
than asserted.

---

## 7a. What this ticket did NOT exercise live (AG4)

**Neither live run in this ticket had a candidate fire.** DigitalOcean's 2026-08 inventory
produced 0 candidates and GitHub's produced 0, so **both legs rendered the zero-candidate arm** of
the modifier sentence. Its other two states — *fired, activity present → applied* and *fired, no
activity → could not fire* — are covered by tests in both stages and by mutation rows E and J, and
have **never been rendered by a live run in this ticket**. The same holds for the AE4 contradiction
state, which no committed artifact exhibits, and for the AG3 cap's truncating arm: every live list
here is under the cap of 10.

**AWS and Linode did not run at all.** Their legs are not in this ticket's done-checks and their
credentials were not sourced in this session, but **the template change reaches them** — their
coverage and modifier sentences will change on their next run exactly as DigitalOcean's did. Their
committed artifacts are from 2026-08-04 and 2026-08-05 and were not regenerated.

**What closes it, and whose it is.** t3 adds the seat rule, which produces the first seat
candidates — so **t3's live GitHub run is the first exercise of the fired path**, and the first
run in which a modifier can be applied to a real candidate on any provider. That makes this an
obligation t3 inherits rather than a gap belonging to nobody. It is named again in §8.

---

## 8. Forward

- **t3 owes `RULE_KEYED_TYPES` an update in the same commit as the seat rule** — §5c.
- **t3's live run is the first exercise of the modifier sentence's fired path** — §7a. Quote the
  rendered sentence in t3's packet: it is the first time any provider's report can say the
  modifier was *applied* rather than that it never ran.
- **Option E** (per-rule metadata on `RULES`) is the natural evolution and t3 is the round that
  would most naturally take it, since it touches `RULES` anyway — §3.
- The report now has a state it has never rendered in production: `rule_keyed_contradictions`
  is non-empty only when the declaration is stale, which no committed artifact exhibits. It is
  covered by tests in both stages and by the mutation matrix, and has not been seen live.
