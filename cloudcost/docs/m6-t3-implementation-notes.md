# m6 t3 — the seat orphan rule, and what a saving is a figure of

**Ticket:** `cloudcost/m6-github.md` §Ticket set → §t3. **Built:** 2026-08-14.
**Measured at:** agents `a252d4b`, harness `d19f4b6` (both level with origin, trees clean).

**Deliverables.** `scripts/detect_orphans.py` (the seventh rule, its threshold, its declaration),
`scripts/fetch_github.py` (`seat_monthly_cost` only, by ruling), `tests/test_detect_orphans.py`,
`tests/test_fetch_github.py`, two new fixtures, `milestone.md` §C8, `runbook.md`,
`m6-github.md` (§t3 anatomy + the §Ticket set bullets re-pointed), `docs/backlog-2026-06.md`
(the prepended BL-153 annotation), these notes.

Closes m6's ticket set.

---

## 1. The gate, and the four things it found

**(i)** Both repos level with origin, trees clean, at t2c's commits — agents `a252d4b`, harness
`d19f4b6`.

**(ii)** Read and taken as the brief rather than re-derived: `m6-t2-implementation-notes.md`
§S2 (including §For t3, plainly), `m6-t2c-implementation-notes.md` §7a, §8 and §5c's boxed
obligation. No disagreement with the prompt.

**(iii)** `RULE_KEYED_TYPES` existed at `detect_orphans.py:379–388` with six entries covering
seven type values, and **`seat` was absent** — confirmed by reading before any edit. AE4's guard
is `compose_report_data.py:636–658`: it walks `orphans["candidates"]` and flags any candidate
whose `type` the artifact does not declare. **It would not have caught me**, and this is worth
saying plainly rather than discovering later: the guard needs a *fired candidate*, and no live
GitHub run produces one (§3). The assertion that actually holds the declaration in place is
`test_the_catalog_declares_seat_now_that_a_rule_keys_on_it`, added here, plus the pre-existing
`fired_types <= RULE_KEYED_TYPES` in `test_the_artifact_declares_which_types_the_catalog_keys_on`
— which bites only because a *fixture* fires.

**(iv) What C8 says a new rule owes it**, read in full: a **global cross-provider prior**, not a
per-provider one (an adapter guarantees nothing here — it supplies facts, not policy); a **stated
ground for the threshold**, because C8 already records *two* thresholds whose rationale is
unestablished and names that as a gap rather than reconstructing it; an entry in the **declared
parameter block** if the threshold is settable; additive-then-clamped scoring, whose clamp
silently absorbs overshoot; a **band** — and the HIGH/MEDIUM cutoffs sit exactly on two existing
base confidences by deliberate calibration, so a base of 0.7 lands MEDIUM *by equality* rather
than by margin, which is a property to state rather than rediscover; and a **re-open trigger**
plus a **billing assumption**, which C8's own F1/F4 practice hoists out of the rule's docstring
**into the contract**. The last of those is why `milestone.md` joined Touches (§7).

**(v) Companion artifacts.** `scripts/detect_orphans.py` → `tests/test_detect_orphans.py`;
`scripts/fetch_github.py` → `tests/test_fetch_github.py`. Both within the work. The composer,
the renderer and the template are untouched and needed to be: t2c §5d made the fix type-agnostic
and `test_compose_and_render_key_on_no_type_value` enforces it, so a new rule-keyed type flows
through as data. Checked rather than assumed: no test or fixture hard-codes
`sorted(RULE_KEYED_TYPES)` — the only reads are `result["rule_keyed_types"] ==
sorted(detect_orphans.RULE_KEYED_TYPES)` and a synthesized `["volume"]` in a compose fixture.

**Four paths sit outside any Touches list the prompt states, all reported as reviewer defects
rather than taken as deviations** — `cloudcost/m6-github.md` (W6 requires it),
`docs/backlog-2026-06.md` (the prepended item), `cloudcost/milestone.md` (admitted by the C8
ruling, which recorded the list as short) and `cloudcost/runbook.md` (§7's runbook rule fires;
see below).

**(vi) The lifecycle signal — both halves verified, and the ruling stands.**

*Half one, live.* `GET /orgs/<org>/copilot/billing/seats`, read-only, HTTP 200, 2026-08-14.
**Scrubbed per U2** — see §11; `<seat-N>` is the same index the committed fixture assigns as
`user-N`, so the two documents can be read against each other:

```
seat                 pending_cancellation_date    last_activity_at
<seat-1>             null                         "2026-08-13T23:15:16+05:30"
<seat-2>             null                         "2026-08-13T18:14:24+05:30"
<seat-3>             null                         "2026-08-13T05:25:00+05:30"
<seat-4>             null                         "2026-08-06T11:09:27+05:30"
<seat-5>             null                         "2026-08-13T23:27:54+05:30"
<seat-6>             null                         "2026-08-13T19:11:44+05:30"
non-null pending_cancellation_date: NONE — all null
```

*Half two, by construction.* The rule keys on `type`, `last_activity_at` and — in its null branch
— `created_at`. All three are first-class. It never needs `pending_cancellation_date` and **could
not read it if it wanted to**: the inventory envelope is frozen at five keys with no
`provider_extra` (§S2's enforcement evidence), and `detect_orphans` consumes the inventory only.

**Recorded, not filed**, in the house form: no current provider exhibits a non-null
`pending_cancellation_date`, so the false positive it would prevent — flagging an
already-cancelled seat as recoverable — is unreachable. **Trigger:** the first seat carrying one.
At that point §S2's reopening condition applies unchanged — the inventory-shape change is its own
ticket, ahead of whatever rule needs it, and a canonical *state value* is enumerated in
§Normalized first.

**(vii)** Options reported, ruled O2. §2.

---

## 2. The cost model — options, ruling, and what the ruling did not authorise

### 2a. The constraint that decided it

Reported at the gate and worth keeping: **`detect_orphans` consumes the inventory only** (one
positional argument, no cost file), and `pricePerUnit` lives in the *cost* artifact's
`provider_extra`, which §Normalized forbids downstream from keying on generically. So **no rule
can derive a rate**, whatever else is true. That kills the two options that would have left the
adapter alone, and it is a fact about the pipeline's shape rather than about this ticket.

### 2b. The options, as reported

| | Option | Blast radius | Same meaning as the other three? |
|---|---|---|---|
| O1 | Accept; state it in the evidence | none | **no** |
| O2 | Adapter emits `pricePerUnit` | that function, its tests, t2 §C14's notes, the untagged table's arithmetic | **yes** |
| O3 | Rule derives the rate | a new cross-stage input into the one provider-agnostic module; breaks `assert "provider_extra" not in source` by design | n/a — makes the *rule* provider-aware |
| O4 | Carry the rate on the resource | the schema seam three adapters pin as `==`; §S2 refused it three days earlier | yes, eventually |
| O5 | Defer to m6's close | none now, a wrong number shipped meanwhile | not yet |

### 2c. The ruling, and its ground

**O2 — the adapter emits the rate.** Ruled 2026-08-14. The ground, as ruled: **a saving is
forward-looking.** `monthly_cost_estimate` feeds an orphan's `monthly_saving_estimate`, and a
saving is what stops being paid next month rather than what has already been spent this one — a
seat reclaimed on the 14th saves the full monthly rate from then on. That holds independently of
any consistency argument. And **O2 is a correction, not a redefinition**: §Normalized already
says *"the per-resource dollar figure — the provider's own price where given"*, GitHub gives one
in the same row, and DigitalOcean takes `price_monthly` for exactly this reason. The MTD product
was a departure from the contract rather than a permitted reading of it.

### 2d. What changed, and the one thing that reached past the function body

```python
-    if not seat_count:
-        return unknown("the organisation reports no assigned seats to divide the SKU across")
-
     price = row.get("pricePerUnit")
-    quantity = row.get("netQuantity")
-    if price is None or quantity is None:
-        return unknown(f"the `{SEAT_SKU}` row states no pricePerUnit/netQuantity pair")
-
-    # One multiplication, at full precision, rounded once at the end (D4).
-    return money(float(price) * (float(quantity) / seat_count))
+    if price is None:
+        return unknown(f"the `{SEAT_SKU}` row states no pricePerUnit")
+
+    return money(float(price))
```

**The `seat_count` parameter went with the divisor it existed for, and that is the one place the
change reached past the function body** — one call site, `fetch_inventory:832`. Reported rather
than removed quietly, per the ticket's own instruction. The alternative was keeping the zero-seat
arm, and it was rejected because it would have become **false**: that arm returns `0.00` with a
warning ending *"the figure is unknown, not zero"*, and under O2 the figure is perfectly well
known — there are simply no seats for it to reach. A run with zero seats emits zero resources, so
nothing consumes the estimate either way; the choice was between a silent correct value and a
loud wrong sentence. No adapter behaviour outside this function changed, which is the boundary
the ruling drew.

### 2e. D4 no longer binds this adapter, and the pin was replaced rather than deleted

`test_the_seat_estimate_multiplies_before_it_rounds` asserted D4's property — aggregate at full
precision, round after — with a rate whose two-decimal rounding is lossy (`money(rate × qty)` =
`50.40` against a round-first `0.00`). **`seat_monthly_cost` was this adapter's only site that
multiplies a unit price by a quantity**, and it no longer multiplies, so D4 has nothing left to
hold here. The test is now
`test_the_seat_estimate_does_not_move_with_the_quantity_consumed`, pinning the property that
replaced it, and it records two consequences deliberately:

- the estimate is the rate whatever the quantity says (mutation rows O and Q);
- **a sub-cent monthly rate rounds to `0.00`, silently and with no warning.** That is C4/D3's
  two-decimal contract applied at ingest, identical to what DO's `price_monthly` gets, and not a
  choice this adapter makes — but the retired multiplication happened to mask it, so it is
  recorded rather than left to be found. Unreachable for a seat, whose price is a per-user-month
  entitlement.

### 2f. Nothing is lost (AI3), stated rather than implied

The consumed user-months the old figure encoded are still carried, twice: the cost line item's
`usage_qty` (`2.709677376` on the run below) and `provider_extra.usage_items[].netQuantity`. The
quantity moved to where quantities belong.

### 2g. The consequence to report, not to fix (AI4)

The untagged-spender table sums per-resource **estimates**. Before and after, from the two runs'
own artifacts:

| | seats × estimate | table total | billed `copilot_for_business` |
|---|---|---|---|
| before (t2b, 2026-08-13) | 6 × 7.97 | **47.82** | 47.81 |
| after (this run, 2026-08-14) | 6 × 19.00 | **114.00** | 51.48 |

The old pair read as agreeing and the new one does not. The divergence is correct: a rate and a
month-to-date bill are different quantities, and the report already says so where the table sits
— *"monthly_cost_estimate is a per-resource estimate used for ranking only; it is not billed cost
and is not part of any cost total (D4)"*. It also makes GitHub behave as DigitalOcean already
does, whose estimates are true monthly rates against an in-flight bill.

**One confound named so it is not read into the table:** the billed figure moved 47.81 → 51.48
between the two runs because the month advanced and more Copilot was consumed
(`netQuantity` 2.516128992 → 2.709677376). That is the bill changing, not this change. Under the
retired formula this run would have estimated **8.58** per seat, not 7.97 — the two variables are
independent and both moved.

---

## 3. The live run produces no candidate — a result, not a gap

**The ticket's SCOPE says a GitHub run produces candidates for the first time, and against live
data that is false.** Found at the gate, before any edit, from the committed live inventory:

| seat | last activity | idle at 2026-08-14 |
|---|---|---|
| `<seat-1>` | 2026-08-13T13:15:00Z | 1d |
| `<seat-2>` | 2026-08-13T12:44:24Z | 1d |
| `<seat-3>` | 2026-08-12T23:55:00Z | 1d |
| **`<seat-4>`** | **2026-08-06T05:39:27Z** | **8d** ← the stalest |
| `<seat-5>` | 2026-08-13T13:20:55Z | 1d |
| `<seat-6>` | 2026-08-13T09:42:43Z | 1d |

Nothing fires at 30 days, and nothing fires at 14 either. Tuning a threshold below 8 to make a
done-check green would be fabrication and was not offered.

**AJ4 — the zero stated as a result.** Six seats, the stalest eight days idle, none reaching the
threshold: **this organisation's Copilot seat inventory carries no recoverable spend today.**
That is a measurement, and it is a different statement from the one the same figure made a day
earlier, when it meant *no rule could evaluate these six resources at all*. It belongs in m6's
close beside the scout's finding — one recovery by inspection before any code existed, one
measured zero from code — each with its basis.

**A property of the pair, recorded because it is invisible in either half alone:** with any
threshold ≥ 14 the seat rule and `modifier_recent_activity` are **mutually exclusive** — the rule
needs idle > N ≥ 14 and the modifier matches idle ≤ 14. So no seat candidate can ever carry that
modifier while the threshold stays above the window. This is not a defect: the report's modifier
sentence keys on how many resources carry `last_activity_at`, not on an applied modifier, so it
renders correctly either way (§6b proves it). But the *applied-to-a-candidate* state remains
unreachable through this rule, and `test_the_seat_rule_and_the_recent_activity_modifier_cannot_both_apply`
pins it so a later threshold change is a visible decision rather than a silent one.

---

## 4. W1 — the rule

**The shape the six existing rules share**, reported before writing: a module-level
`rule_*(resource, ctx)`; a docstring opening with the rule and its confidence; early returns
first, the `type` check always first; age arithmetic through `ctx.age_days(...)`, which returns
`None` for an absent *and* an unparseable value alike; a `fired(name, CONFIDENCE_*, [...])`
return, with the optional `saving=` override used by exactly one rule; evidence as full sentences
naming the fact **and** the threshold, built through `ctx.age_phrase`; registration in `RULES` in
catalog order.

`rule_idle_seat` follows all of it. The saving is the `score()` default — the resource's own
`monthly_cost_estimate` — with no override, which is now the right figure because of §2.

**`Context.activity_phrase`, a sibling rather than a widened `age_phrase`.** That helper's
sentence hard-codes the word *created*; it has five call sites and every one is pinned by a
mutation row. An idleness sentence is a different sentence, not a parameterisation of that one.

### 4a. The null case, which is not the old case

`ctx.age_days` cannot distinguish absent from unparseable, and every existing rule treats both as
silence. **For a seat, null is not an unknown — it is the strongest form of the signal.** GitHub
nulls `last_activity_at` past a rolling 90-day retention (*"If your data's `last_activity_at`
exceeds 90 days, its value will be set to `nil`"*, GitHub changelog 2025-01-17), and it is also
null for a seat never exercised since assignment. Both readings mean **at least** as idle as any
non-null value, so silence would hide the purest case of the waste this rule exists to find.
GitHub's own published inactive-user workflow resolves it the same way, falling back to the
assignment date. `created_at` is sound under both readings — a seat whose activity has aged out
of retention was necessarily created before that.

**The fallback is keyed on the value being ABSENT, never on `age_days` returning `None`.** An
unparseable timestamp means the rule cannot tell how idle the seat is, which is a different thing
from knowing it was never exercised, so it stays silent and `timestamp_warnings` names it — as it
does for every other rule. The near-miss fixture carries `seat-broken-1` with a two-year-old
`created_at` and `"last Tuesday"` as its activity: a fallback written the wrong way fires on it
loudly, which is mutation row D.

### 4b. This rule's idleness is the first that is not C7's

C7 makes `attached_to is null` the universal idle signal, keyed by four rules, where idle means
*attached to nothing*. A seat is never unattached — the adapter emits `user:{login}` deliberately
(§W6 of t2) — so that signal cannot reach this case at all. The waste here is an entitlement that
**has** an owner and still produces nothing: assigned, billed, unexercised. The evidence says so
in the candidate itself rather than only here, because an operator reading a seat candidate needs
to know it is not the same claim the other six rules make.

---

## 5. W2 — the threshold, and W3 — the declaration

**Configurable, following `--snapshot-age-days` rather than the two hard-coded constants.** C8
records the existing override asymmetry as an *accident* of m1's §t2 Scope wording, with the
origin established and the rationale not. This threshold has the reason that one never had: how
long an assigned-but-unexercised entitlement may sit before it counts as recoverable is an
organisation's **policy**, not a property of the resource — unlike the age at which a detached
disk becomes waste. `DEFAULT_SEAT_INACTIVE_DAYS = 30`, `--seat-inactive-days N`, threaded through
`detect()` → `Context` → the rule, and echoed in the declared `parameters` block (which C8/D21
says covers the age thresholds and the coverage threshold — this is an age threshold, so the
block's description still holds).

**Thirty, and the two required sources agree — so no stop.**
- **GitHub publishes 30** for this exact decision: its inactive-user guidance is written against
  *"you haven't used your assigned license for GitHub Copilot in 30 days"*, and its licence-change
  policy revokes a licence inactive for 30 days plus a further 30.
- **The catalog's register is {14, 30}**, where 30 is already the shared
  stopped-compute/stopped-database threshold and the snapshot default.

Both give 30, and no new number enters the model. Recorded with its ground because C8 names two
thresholds whose rationale is unestablished, and a third would be a pattern rather than an
oversight.

**Confidence 0.7 → MEDIUM by equality with the cutoff.** Ground: like the aged snapshot, also
0.7, elapsed time is the whole signal and the thing may still be wanted; unlike an unattached
volume at 0.9, the resource has a human owner who may come back to it. C8 records that the band
cutoffs sitting on base confidences is deliberate calibration, so landing on one by equality is
stated rather than left to be noticed — the shifted render (§6c) shows all six in MEDIUM.

**W3 — `RULE_KEYED_TYPES` gains `TYPE_SEAT`**, in this commit, with the `# rule_idle_seat`
comment the other entries carry. One consequence recorded in the declaration's own docstring:
**the rule-keyed set and `CANONICAL_TYPES` are equal again**, every canonical type now having a
rule. That is a fact about today's catalog, not a property to rely on, and the equality is still
asserted nowhere — deliberately, since the next canonical type introduced ahead of its rule must
be able to reopen the divergence.

---

## 6. Verification

**Both pytest scopes** (BL-152: neither covers the other) — `cloudcost/tests/` **465 passed**,
`tests/` **129 passed, 7 xfailed**.

**The baseline, established rather than quoted.** t2c's notes report 451 for `cloudcost/tests/`;
that figure does not reproduce at `a252d4b`, where the suite collects **453**. Derived rather than
asserted: `def test_` counts against `git show HEAD:` are identical file-by-file except
`test_fetch_github.py` (53 → 54), and 465 − 12 added functions = 453. Flagged as a stale figure in
a notes file, not chased.

### 6a. The mutation matrix (the t1 hazard)

**Seventeen rows, one mutation each, all seventeen RED, each naming a distinct raising
statement** — which is what shows every assertion was exercised individually rather than one
shadowing the rest. Every restore verified with a control on both sides.

| | mutation | test it failed | raising statement |
|---|---|---|---|
| A | `!= TYPE_SEAT` → `!= TYPE_DATABASE_SNAPSHOT` | `test_idle_seat_fires_past_the_inactivity_threshold` | `hit = result["seat-idle-1"]` |
| B | `age <=` → `age <` | `…is_silent_when_recently_exercised_or_exactly_on_the_threshold` | `assert result["candidates"] == []` |
| C | null branch disabled | `…anchored_on_its_assignment_date` | `hit = by_id(...)["seat-never-1"]` |
| D | fallback keyed on `age_days(...) is None` | `…unparseable_does_not_fall_back` | `assert [c["resource_id"] …] == []` |
| E | `CONFIDENCE_IDLE_SEAT` 0.7 → 0.55 | `test_idle_seat_fires_past_the_inactivity_threshold` | `assert hit["base_confidence"] == 0.7` |
| F | `DEFAULT_SEAT_INACTIVE_DAYS` 30 → 45 | `…default_seat_inactivity_threshold_is_thirty_days` | `assert …DEFAULT_SEAT_INACTIVE_DAYS == 30` |
| G | `TYPE_SEAT` removed from the declaration | `test_the_catalog_declares_seat_now_that_a_rule_keys_on_it` | `assert _normalized.TYPE_SEAT in …RULE_KEYED_TYPES` |
| H | saving dropped from the evidence | `…evidence_names_the_activity_date_the_threshold_and_the_saving` | `assert "$19.00/mo" in evidence` |
| I | `attached_to is not None` → `is None` | `…idleness_is_not_the_unattached_signal…` | `assert "not idle in the unattached sense…" in evidence` |
| J | `activity_phrase` reworded | `…evidence_names_the_activity_date…` | `assert "idle 87d at ref 2026-07-27" in evidence` |
| K | `rule_idle_seat` removed from `RULES` | `test_every_rule_in_the_catalog_fires_on_the_positive_fixture` | `assert len(detect_orphans.RULES) == 7` |
| L | `seat_inactive_days` dropped from `parameters` | `test_the_seat_inactivity_threshold_is_a_parameter` | `assert split["parameters"]["seat_inactive_days"] == 100` |
| M | CLI flag default → 999 | `test_cli_seat_inactive_flag_changes_the_verdict` | `assert sorted(…payload["candidates"]) == [` |
| N | `RECENT_ACTIVITY_WINDOW_DAYS` 14 → 60 | `…modifier_cannot_both_apply` | `assert (` |
| O | rate → the retired MTD product | `…same_on_a_settled_month_and_an_in_flight_one` | `assert settled_estimate == in_flight_estimate == 19.0` |
| P | rate → `netQuantity` | `test_a_seat_costs_the_rate_the_organisations_own_bill_states` | `assert unit == _normalized.money(row["pricePerUnit"]) == 19.0` |
| Q | rate × 2 | `…does_not_move_with_the_quantity_consumed` | `assert fetch_github.seat_monthly_cost(priced, []) == 19.0` |

**Two rows are caught by a lookup rather than an `assert`** (A and C raise `KeyError` on the
candidate the mutation removed). They are still the statement pytest marks `>`, and they still
show the test detecting the mutation — but they are named here as what they are rather than
counted as assertion failures.

**Three rows failed setup on the first run, and the corrections are the point.** Row A's first
mutant was `!= TYPE_VOLUME`, which is **already** `rule_unattached_volume`'s spelling, so the
"mutant absent beforehand" control refused it — the A3 hazard caught by its own guard. Rows G, K
and L are **deletions**, whose mutant is `""` or a bare `)`; the harness counted those as
"already present" (`"".count()` is `len(text)+1`) and refused them. The mutant-side control exists
only to catch a mutant containing its original, which a deletion cannot do, so those three are
controlled on the original alone and **the matrix says `1->0->1 (deletion)` rather than
reproducing the other rows' control string**. Row D's first form did fail its row, but by an
`AttributeError` inside `day()` rather than by the test's own assertion — it proved the mutation
was caught without showing which assertion caught it, and was reshaped until it reached the
assertion.

**Residue sweep, with a positive control and a named limit.** Zero mutation strings survive in
`cloudcost/scripts`, `cloudcost/tests` or `cloudcost/templates`. **The sweep covers 14 of the 17
rows** — G, K and L are the deletions above and have no sweepable string, which is stated by the
sweep itself rather than left as a silent 17. The positive control finds 11 of those 14 patterns
in the mutation driver; the three it misses (C, D, I) are the multi-line mutants whose spelling in
the driver's own source differs byte-wise through escaping, so for those the control is silent and
the restore rests on the matrix's two-sided check. **Done-check 1 was then re-run after the whole
matrix and returned 465 passed**, which is where "the tree is restored" is actually discharged.

### 6b. The three first-time-live readings — done-check 3

`CLOUDCOST_PROVIDER=github ./scripts/sprint.sh cloudcost`, run `cloudcost-orch-github-8VjoDw`,
**exit 0** (checked before any artifact was read, BL-153), 76 lines, **zero `[FAIL]`**, one WARN —
the ambient credential-shadow notice, unchanged from t2c and stripped by the prefix. Source-tree
mtime hash identical before and after the run (`dfd92e3d…`), so no input moved under it.

**(1) The coverage sentence for a type that now has a rule.** The pair reverts to its
pre-t2c wording — *and this time it is true*, which is the whole arc:

| | |
|---|---|
| before t2c (false) | Of 6 usable resource(s), every type is one the rule catalog evaluates — 0 carried a type outside it, so the totals above cover the whole inventory. |
| t2c (true, and saying so) | Of 6 usable resource(s), 6 carry a canonical type no rule keys on yet … **A candidate count of 0 is therefore a result over 0 resource(s), not 6.** |
| t3 (true) | Of 6 usable resource(s), every type is one the rule catalog evaluates — 0 carried a type outside it, so the totals above cover the whole inventory. |

`unevaluated_count` is `0` where t2c's run had `6`. The tag-section half likewise reads *"Every
resource in this denominator carries a type the rule catalog evaluates; none is counted here and
evaluated nowhere."* **The sentence being byte-identical to the false one is the point, not a
regression**: t2c did not reword a sentence that was wrong in general, it made the report say
which of three states it is in, and this run is in the third.

**(2) The modifier's arm — it takes `no_candidate_fired`, not the applied arm:**

> No rule fired on this inventory, so the recent-activity modifier **never ran**: modifiers adjust
> the confidence of a candidate, and there is no candidate to adjust. This says nothing about
> whether the modifier would have matched — the stage was not reached. 6 of 6 resource(s) carry
> `last_activity_at`, which is what it keys on.

Correct, and unchanged from t2c's run, because no candidate fired (§3).

**(3) A fired candidate — none on this leg.** §6c is where it is exercised.

**Done-check 4, DigitalOcean:** exit 0, 76 lines, zero `[FAIL]`. The coverage pair is
**byte-identical** to t2c's (*"Of 18 usable resource(s), every type is one the rule catalog
evaluates…"*), the modifier sentence is unchanged, and the rule-legibility arm reads *18 resources
evaluated, 0 skipped; types [compute_instance, load_balancer, volume]* exactly as before.
Unregressed in AF3's sense.

### 6c. Ruling B — the fired path, over live data, labelled

**This is not a sprint run.** It is a hand-invoked `detect → compose → render` chain in a scratch
directory outside the repo, run twice over the **same live inventory bytes** the sprint leg wrote
(md5 `40a7f1190b54cef31355f30769d4eecd`, printed for the source and both copies, so the chain
demonstrably ran on the sprint's own file and not an edited one). **The threshold is untouched in
both legs** — 30, the default, echoed in each artifact's `parameters`. The only thing that differs
is `--reference-date`.

| leg | `--reference-date` | candidates | saving | modifier state |
|---|---|---|---|---|
| **CONTROL** | `2026-08-14` (the real date) | **0** | 0 | `no_candidate_fired` |
| **SHIFTED** | `2026-10-01` | **6** | **114.00** | `applicable` |

**The control is what makes the shifted leg mean anything**: the same chain, same bytes, same
threshold, at today's date reproduces the sprint leg's zero exactly. So the reference date is the
only variable. And the shift needed is 48 days, not an implausible one — the rule fires at the
ruled threshold or not at all (AJ2d), and nothing was tuned.

A candidate, in full, from the shifted render's own artifact:

```
idle_seat  <seat-4>  conf 0.7  saving 19.0
  - last activity 2026-08-06 — idle 55d at ref 2026-10-01; threshold >30d
  - attached_to is 'user:<seat-4>' — the seat is assigned, so it is not idle in the
    unattached sense the other rules key on; it is an entitlement nobody is exercising
  - monthly_cost_estimate is $19.00/mo and a seat bills for as long as it is assigned
    regardless of use — so reclaiming it saves that whole figure
```

All six land in **MEDIUM**, by equality with the 0.7 cutoff, at `114.00 USD / month estimated` —
the rate, not the month-to-date figure, which is §2 visible in a rendered report.

**And the modifier's applied arm, rendered for the first time on any provider:**

> 6 resource(s) carry `last_activity_at`, so the recent-activity modifier **was applied**; where
> it does not appear on a candidate it did not match.

**AJ3 — the obligation is split, not declared closed.** What this discharges: that the
fired-candidate arm, the modifier's applied arm and the coverage sentence for a now-ruled type
**render correctly with real data**. What it does **not** discharge: that they have been exercised
by a live *sprint* run. That closes on its own the first time a seat on this account crosses 30
days idle. **No ticket owns it and none should** — it is a condition, recorded here and in
§t3's anatomy, not a work item.

---

## 7. The C8 entry, and the runbook

**Why the contract and not these notes** (the ruling's ground, recorded because it decides where
future entries of this kind go): an implementation-notes file is read by the next round in its arc
or by nobody, and **Google Workspace is not in this arc**. It is the next member of this class, it
is close to pure seats, it will meet these assumptions, and it will never open m6's notes. A
contract crosses arcs; notes do not. The Touches list that omitted `milestone.md` is recorded as a
reviewer defect rather than a deviation taken.

**Form.** F1 and F4 were read in full and the paragraph follows F4's shape — the bolded claim,
then the ground, then the explicit statement that the assumption is hoisted so a new adapter meets
it as an obligation rather than discovering it. Where F1 differs (it closes with *"the deliverable
for F1 is the documentation, not a threshold"*, because there was no threshold to give) the
paragraph follows F4 instead, since this rule does have one. It states **obligations**, not what
the rule does.

**Three things**, as ruled: the threshold with both of its sources named; the billing assumption
(*a seat bills for as long as it is assigned, regardless of whether anyone exercises it*); the
re-open trigger (*a provider whose seats are not billed per seat*).

**AK4 — the trigger is written outside the register used for a hypothetical one.** C7's and C10's
*"no current provider exhibits it, so recorded rather than filed"* is true of those. This one is
waiting on a provider **this milestone's own first paragraph names**: `m6-github.md` opens by
naming AI-provider spend as the third member of the class, and AI spend is metered rather than
billed per seat. The paragraph says that, in those terms.

**AK5 — the stamp clause.** C8 carries a BL-132 reachability stamp dated 2026-08-11. The new
paragraph postdates that census and says so in one clause, so its lack of a reachability verdict
reads as *never censused* rather than *censused and found unreachable* — the ambiguity BL-147
records. **No reachability verdict of my own is offered and BL-147 is not advanced.**

**One adjacent clause, not a fourth thing.** The X4/D4 paragraph above quantifies over *"all three
adapters"*, which has been three of four since t2 — GitHub populates `last_activity_at`. The claim
is scoped as written and is **not amended**; a bracket records the scope so *"all three adapters"*
is not read as *"every adapter"*.

**The runbook rule fires, and the runbook is owed an entry.** Two operator-facing changes: a new
CLI flag (`--seat-inactive-days`, a command semantic) and a change in what a zero-candidate GitHub
run *means* — from "nothing could be evaluated" to "nothing qualified". §What a zero-orphan account
means carries both, its "three live accounts" corrected to four, and the knob named with a warning
against lowering it to make a candidate appear.

---

## 8. The prepended item — BL-153's second mechanism

Annotated, not filed as a new row, so this ticket's exclusions do not reach it. Placed **before
`**Owes:**`** so the arm-ordering question it poses is left visibly untouched. Recorded: the
mechanism (inputs changing under a run rather than a credential gate skipping the guard); that
**the run exited 0**, so the exit-code check that catches the credential arm does not catch this
one; that the output was indistinguishable by content from the frozen-tree run that replaced it,
and what caught it was knowing an edit had happened; and that the mitigation — freezing the tree
and recording source mtimes — is **a discipline, not an enforced check**, since nothing in the
sprint reads a source mtime or stamps the tree a run was produced from. **No scope widening, no
fix proposed**, and the outstanding ruling is named as still outstanding.

Sourced as the m6 t2c session's own account, relayed through this ticket's prompt, and marked as
**not reconstructible from the tree** — the discarded run left no artifact and t2c's notes do not
record it.

*(This session applied the discipline the annotation describes, which is how it can be reported
rather than only described: the source-tree mtime hash was captured before and after each sprint
leg and is identical, and the mutation matrix was held until no suite was in flight — running it
concurrently would have been exactly this mechanism.)*

---

## 8a. The U2 lapse — what happened, and what was done

**The U2 discipline held for two packets and lapsed on the third, with nothing detecting it.**
That is the fact worth recording; the remediation is the smaller half.

**What leaked.** Six live seat logins and the organisation login, unredacted, in the t3 review
packet — §1.5's chain evidence including the `attached_to` strings, §2's gate (vi) table pairing
each login with its Copilot last-activity timestamp to the second, and §4's idle table. **And in
this file**, at the same three places plus the candidate block, which is worse: the packet is a
scratch artifact, this file was committed. The sensitive item is not the logins but **login
against Copilot last-activity timestamp** — per-person work-behaviour data about identifiable
individuals. U2's own text is unambiguous and was read during this ticket: *"The class binds this
document, the tests and the packet — not only the fixtures."*

**How it happened.** The scrub was applied where the ticket's work made it salient — the fixtures
are pseudonymised and the tests carry no real identifier — and was simply not applied to the
prose reporting the live reads. t2 and t2c both applied it to their prose; this session read the
sentence that requires it and did not act on it. No mechanism was in place that would have
caught that, which is §8b.

**Blast radius, established before anything was changed** (each stated even where the answer is
none, because a clean answer stated is worth more than one assumed):

| | |
|---|---|
| the packet's paths | one, in the session scratchpad; no copy anywhere on the filesystem |
| tracked in either repo, any branch, any commit | **no** — `git log --all` over its path returns 0 in both |
| in the t3 commit's tree | **yes — this file only.** Fixtures, tests, ticket anatomy and the commit message are clean; the six numeric user ids appear nowhere at all |
| earlier commits, either repo | **none for the six logins** — `git log --all -S` names exactly one commit, this ticket's. The org string also appears in one earlier commit, `ed63058` (2026-06), as part of a `rig/docs` clone URL for a different product — see §8c |
| sprint captures, scratchpad | `aetheris/sprint/` **clean** for all seven strings (positive control: 56 files carry `cloudcost-orch`). The scratchpad held them in the Ruling B chain's artifacts and the packet |

**What was done.** This file's four leaking passages were rewritten with the U2 map applied at
authoring — not sed'd — and the commit amended; it was never pushed, and it is the only commit in
either repo that has ever carried the logins, so the amend removes them from reachable history.
The packet was **regenerated** rather than patched, since a sed over a leaked file leaves the leak
in whatever it was derived from. The map is stable and relational: `<seat-N>` uses the same index
the committed fixture assigns as `user-N` (verified by matching `created_at` across the two), so
month-on-month and cross-document reading survives. Timestamps are **not** scrubbed — U2 puts them
in the keep class, and with the identity gone they carry the rule's meaning without the pairing.

**The redactor is one of the unredacted copies, not a tool standing outside them.** The filter
this regeneration ran through held the six logins and the organisation as **literals** in a
substitution table — so it was itself an artifact in the scrub class, and it is counted among the
copies destroyed rather than among the instruments that destroyed them. It was untracked scratch,
never committed in either repo (`git log --all` over `redact.py`, `*redact*`, `u2map*` and `*u2*`
returns 0 commits in both, and 0 tracked paths at HEAD), and it was shredded with the rest.

**A literal table was the wrong shape and the right one already exists in this repo.**
`record_github_fixtures.py`'s `Scrubber` **derives** its map: it walks the recorded bodies,
*learns* each identity from the keys that carry one, and assigns `user-N` in first-seen order —
`grep` for the seven strings over that file returns **0**, because it hardcodes none of them. A
redactor built that way is not itself a disclosure. This one was written for a single
regeneration and took the shortcut; that it then had to be destroyed like the leak it was fixing
is the cost of the shortcut, and is recorded rather than tidied away.

## 8b. The finding underneath it — the check's scope

t2's packet ran a U2 leak check over all tracked files and the untracked notes, and it **passed**.
The packet itself was outside that scope. **The packet is the artifact most likely to leave the
repo** — it is pasted into a review conversation by design, which is the one channel none of the
repo-scoped checking touches.

So a leak check that excludes the one artifact that travels is not a partial check; it is a check
aimed away from the highest-exposure path. And its passing was **not evidence about the packet**,
though it reads as though it were. Appended to **BL-150** as a dated entry, because it is a finding
about how the record-keeping system works rather than a code defect. **No fix proposed** — that
is the row's to decide.

## 8c. A pre-existing occurrence of the organisation string, and a t2 claim that was false when written

The blast-radius sweep turned up something this ticket did not cause and does not fix. **The
organisation login is committed in four `rig/docs` files** — three milestone headers and a
`git clone` URL — as the owner segment of a repository path for a different product, landed at
`ed63058` in 2026-06, two months before this milestone opened.

That makes **t2's §W7 claim *"the organisation is named nowhere in the repo"* false at the moment
it was written**, and it was written as a verified statement. What was actually verified was the
fixtures and this use case's own files; the sweep behind the sentence did not reach `rig/`. It is
the same shape as §8b — a check whose scope was narrower than the claim it was used to support —
and it is recorded here rather than filed, because the occurrence itself is a repository URL for
an unrelated product and whether U2's class should reach a repo-owner segment at all is a
question for whoever owns that ruling, not one this ticket should answer on the way past.
**Nothing in `rig/` was changed.**

*(This document names the organisation nowhere; §8a's blast-radius table describes the
occurrence without spelling it. The first draft of that table did spell it — caught by this
ticket's own post-amend sweep, which is the same way t2 caught the same mistake in its own
gate heading.)*

**The reflex recurred three times inside the remediation itself, and that is the part worth
keeping.** Once in §8a's blast-radius table, which named the organisation while describing the
leak; once in the packet's own verification table, which spelled all seven strings as its row
labels — the section reporting the leak leaking it again; and once in the scratchpad, where the
redaction map was about to be left sitting beside the redacted packet, which is a
deanonymisation key filed next to the thing it deanonymises. Each was caught by a sweep run
**after** the step rather than by the writing of it. Redaction is not something a careful author
does reliably at the keyboard; it needs a check that runs over the artifact afterwards — which
is exactly §8b's finding, arriving a second time from the inside.

## 9. SURPRISES

**The coverage sentence's correct form is byte-identical to the false one it replaced.** t2c
corrected a sentence that claimed completeness over six unevaluated resources; t3 makes the
original claim true, so the report prints the pre-t2c words again. Anyone diffing the two runs'
HTML sees t2c's change reverted. It is not — the composer is choosing between three states and
this run is in a different one. Recorded because it is exactly the shape a future reader
misreads.

**`CANONICAL_TYPES` and `RULE_KEYED_TYPES` coincide again**, four days after t1 ended the
coincidence that made t2c necessary. The mechanism t2c built is now dormant on every provider,
and its tests are the only thing exercising it. That is the correct outcome — the mechanism exists
for the *next* type introduced ahead of its rule — but it means t2c's live defect is currently
unreproducible from any committed artifact.

**t2c's own reported test count does not reproduce.** 451 in the notes, 453 at the commit they
describe (§6). Not chased.

## 10. UNREAD

- **AWS and Linode did not run.** Their credentials were not sourced and their legs are not in
  this ticket's done-checks. The rule reaches them — it is provider-agnostic and their inventories
  carry no `seat`, so it can only be silent there — and their committed artifacts (2026-08-04,
  2026-08-05) were not regenerated. The `parameters` block on their next run will gain
  `seat_inactive_days`.
- **`optimization_signals` / `detect_optimization_signals.py`** — not read. It is a separate stage
  with its own artifact and this ticket does not touch it.
- **The Rig side** — untouched and unread. No harness file was opened or changed, and the
  conclusion that none was needed held.
- **The rendered PDF path** (`render_report.py --pdf`) was not exercised; only the HTML.

---

## 11. The U2 map used by this document and the t3 packet

Stable and relational, so the two documents and the committed fixture can be read against each
other. `<seat-N>`'s index is the same one `record_github_fixtures.py` assigned as `user-N`,
established by matching `created_at` across the live inventory and
`tests/fixtures/github_copilot_seats.json` rather than by re-deriving an order:

| redaction | what it stands for | fixture's own pseudonym |
|---|---|---|
| `<seat-1>` … `<seat-6>` | the six Copilot seat logins, in ascending `created_at` | `user-1` … `user-6` |
| `<org>` | the organisation login | — |

**Not redacted, per U2's keep class:** timestamps, monetary figures, quantities, `plan_type` /
`size`, and the period fields. With the identity replaced, a timestamp carries the rule's meaning
and no longer carries the pairing.

**The six numeric user ids** are in U2's scrub class and were checked separately: they appear
nowhere in the commit tree and nowhere in the packet, before or after the regeneration. Stated
because an unchecked absence and a checked one look the same.
