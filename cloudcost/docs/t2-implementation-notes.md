# t2 — `detect_orphans.py` (provider-agnostic heuristics) — implementation notes

**Ticket:** m1-cloudcost §t2. **Built:** 2026-07-29.
**Deliverables:** `scripts/detect_orphans.py`, `tests/test_detect_orphans.py` (54 tests,
offline), `tests/fixtures/inventory_*.json` (6 crafted fixtures).

---

## Decisions

**The payload carries no wall clock, so the whole file is byte-deterministic.** §t2 forbids
a hardcoded "now" and asks for a reference-date parameter; the natural next step is that
nothing else in the output moves either. `detect()` is pure — same
`(inventory, reference_date, snapshot_age_days)` in, byte-identical JSON out — so it
deliberately does *not* emit t1's `generated_at`. The two timestamps it does carry are both
inputs: `reference_date` (what the age rules were evaluated against) and
`inventory_generated_at` (passed through from the adapter). This makes
`test_the_same_inputs_produce_a_byte_identical_payload` a real assertion rather than a
subtree comparison, and it means a t3/t4 regression diff on this file shows only real
changes. Deviation from t1's convention, taken knowingly.

**`--reference-date` defaults to the inventory's `generated_at`, not to `datetime.now()`.**
An explicit flag always wins. Absent it, the reference date is the adapter's own fetch
timestamp, so `detect_orphans.py inventory.json` is reproducible on a given file — re-running
last month's inventory next week yields last month's answer, which is the correct reading of
"as of when this inventory was taken". The wall clock is reached only for an inventory with
no usable `generated_at`, which no adapter emitting the frozen schema produces.

**One rule per firing, and the m1 catalog is type-disjoint.** The engine emits one candidate
per (resource, rule) pair; because every rule in §t2 leads with a `type` guard, at most one
fires per resource today. Written this way so a later overlapping rule (e.g. an idle-droplet
rule) needs no engine change — it will just produce a second candidate for the same resource.

**Reported-only is enforced structurally, not by convention.** The untagged-in-tagged-account
entries live under `reported.untagged_in_tagged_account.resources` and carry **no
`confidence` and no `monthly_saving_estimate`** — only `monthly_cost_estimate`. A downstream
script cannot accidentally queue one, because the fields a queue would key on do not exist on
it. `test_reported_entries_carry_no_confidence_and_no_saving_estimate` pins that shape.

**A resource can be a candidate *and* a governance flag, by different rules.** `keep=true`
excludes outright, but "untagged" does not exclude: an untagged unattached volume is queued
by the volume rule and separately reported for governance. What §t2 forbids is the *untagged
rule* queuing anything, which is what the structural split above prevents. The fixture
carries both faces (`vol-untagged-orphan-1` = both; `drop-legacy-1` = reported only, fires no
rule) so the distinction is asserted, not assumed.

**Tag coverage threshold is 50 %, strictly above.** §t2 says "coverage above a documented
threshold" without naming it; `TAGGED_ACCOUNT_COVERAGE_THRESHOLD = 0.5` is the documented
value, and the evidence line quotes both the observed coverage and the threshold ("account
tag coverage is 71 % of 7 resources, above the 50 % threshold"), so a reader can re-derive the
verdict from the report without reading the code. Negative fixture at 25 % proves silence.

**Age thresholds are strictly greater (`>`), including at the boundary.** "unattached volume
> 14d" is read literally: exactly 14.0 days does not fire.
`vol-orphan-exactly-14d-1` in the negative fixture pins the boundary, and the `>=` mutation
fails the suite (M3 below).

**The one place a provider's vocabulary is read is `STOPPED_STATES`, and a test enforces
that.** `test_the_only_provider_state_vocabulary_is_the_stopped_states_constant` asserts the
literal `"off"` occurs on exactly one line of the module — the constant, with its
normalize-before-provider-2 comment — and that `state` is read only inside the stopped-droplet
rule. A second test asserts the full set of resource fields the module reads is a subset of
the normalized schema's first-class fields, and that `provider_extra` appears nowhere. So
"provider-agnostic" is checked mechanically rather than claimed in a docstring.

**The recency modifier keys on `last_activity_at` and nothing else (Decision A).** DO emits
null for every resource type, so the modifier is inert on DO — the correct outcome, and one
that must not be papered over with `created_at`. The no-op is asserted both ways: a null
`last_activity_at` yields `modifiers: []` even though the resource is 207 d old, and a crafted
resource with `last_activity_at` set 2 d before the reference date takes the −0.2. The
substitution is not merely untested — it is *failable*: the mutation that ORs in `created_at`
turns the 7-day-old reserved IP from 0.95 into 0.75 and fails the suite (M2).

**The ephemeral-name pattern is matched case-sensitively, as §t2 writes it.**
`^(tmp-|ci-|test-)` verbatim; `TMP-scratch` does not match. Deliberate literal reading of the
ticket rather than a helpful generalisation — flagged here so a later widening is a decision,
not a drift.

**Degrade, don't crash (repo rule).** A non-object resource entry, or one missing
`resource_id`/`type`, is skipped and counted in `skipped[]`. A structurally valid resource
whose `created_at`/`last_activity_at` will not parse is *kept* (rules that need no age can
still fire) and named in `warnings[]` — an unparseable date must not silently suppress a rule
with a well-formed empty answer. Either condition yields `{"status": "partial"}` on stdout
and exit 1, matching t1; the file it can produce is still written.

---

## Additive fields beyond the §t2 field list (noted, not silent)

§t2 specifies each candidate carries `resource_id`, `type`, `rule`, `confidence`,
`evidence[]`, `monthly_saving_estimate`. Three additions, on the t1 Deviation-3 precedent
(where `name`/`region`/`size` were promoted for exactly this reason):

- **`name`, `region`, `raw_ref`** — the milestone's "reviewable without opening the DO
  console" done-when. Without them the t4 orphan section either prints opaque IDs or re-joins
  against the inventory to recover the identity fields the schema already froze as first class.
- **`base_confidence` and `modifiers[]`** — `confidence` alone cannot be audited: a 0.7 could
  be an aged snapshot at base or an unattached volume with recent activity. Carrying the base
  and the applied deltas makes the arithmetic reviewable in the artifact, which is what
  "reviewable code" means at the output boundary too. The evidence line for each modifier is
  also appended to `evidence[]`, so a reader who ignores these fields loses nothing.

---

## Fixtures

Six crafted inventories (no recordings — t1 owns those), all written against reference date
**2026-07-27**, each with a `_comment` naming what it is for:

| Fixture | Purpose |
|---|---|
| `inventory_rules_positive.json` | one resource per rule, each past its threshold |
| `inventory_rules_negative.json` | the near-miss counterpart of every one of them |
| `inventory_modifiers.json` | every modifier path on resources firing the same base rule |
| `inventory_tagged_account.json` | 71 % coverage → two governance flags, one also a candidate |
| `inventory_untagged_account.json` | 25 % coverage → nothing reported, catalog still fires |
| `inventory_malformed.json` | four unusable entries + an unparseable date + one clean orphan |

The negative fixture is the one that carries the weight: it holds an attached volume, a 7-day
orphan, a **14.0-day** orphan (boundary), an assigned reserved IP, a 3-day snapshot, a
**tag-targeted** load balancer, a droplet-targeted load balancer, a stopped-but-young droplet
with storage, a stopped-and-old droplet *without* storage, and a running droplet with storage —
and asserts `candidates == []` for the lot. Tag coverage in the rule fixtures is deliberately
kept below 50 % so governance flags never contaminate a rule assertion.

The modifier fixture parks every case on the *same* base rule (unattached volume, 0.9), so any
confidence difference between its entries can only have come from a modifier. The clamp case
is the exception by necessity: 0.9 + 0.1 = 1.0 does not clamp, so the >1.0 case uses a reserved
IP (0.95 + 0.1 = 1.05 → 1.0).

---

## Cross-stage check (t1 → t2)

Per the m6 learning — a per-ticket unit done-check goes green while the pipeline seam is
broken — the suite runs the **real t1 adapter** against the recorded DO fixtures (over the
`DOStub` HTTP server from t1's `conftest.py`), then feeds *its emitted*
`do_inventory_2026-07.json` to the t2 **CLI as a subprocess** and asserts the exact rule set
that fires:

```
vol-orphan-1  → unattached_volume        203.0.113.11 → unassociated_reserved_ip
snap-0001     → aged_snapshot            snap-0002    → aged_snapshot
lb-orphan-1   → idle_load_balancer       lb-tagged-1  → (silent — B2 survives the seam)
```

This is what catches a rename or a shape drift across the adapter contract; the crafted
fixtures alone would not, because they are written by the same hand as the consumer.

---

## Known limitation (noted, not built)

**A backend *tag* matching zero live instances is an idle load balancer, and t2 cannot see
it.** `attached_to == "tag:web"` is treated as attached — correct per B2, and the only choice
available from the inventory alone. Proving the tag resolves to nothing needs an
instance-side cross-reference (does any resource carry tag `web`?), which is a real
enhancement rather than a bug: it is a *second* rule, not a change to this one, and it needs a
decision on whether "no instance carries the tag" is enough evidence to queue. Forwarded.

---

## Open items forwarded

- **Sum attached storage into the stopped-droplet saving.** m1 emits the droplet's own
  estimate and merely *names* the attached volumes and their cost in the evidence. Whether the
  volumes should be summed is a policy call (they may be intentionally retained past the
  droplet), so it wants a decision, not just code.
- **The tag-with-zero-live-backends rule**, above.
- **`STOPPED_STATES` normalisation.** Before the second provider lands, the *adapter* should
  emit a common state enum and this constant should shrink to a schema-level value. Today it
  is the single documented seam where DO vocabulary reaches shared machinery.
- **`RECENT_ACTIVITY_WINDOW_DAYS = 14` is a chosen constant, not a parameter — and its window
  is one-sided.** §t2 asked for the snapshot threshold to be tunable and said nothing about
  this one, so it stays a documented module constant. If a provider that actually populates
  `last_activity_at` lands, it likely wants a flag. **Bound the window at both ends when that
  happens:** `modifier_recent_activity` rejects on `age > RECENT_ACTIVITY_WINDOW_DAYS` only, so
  a `last_activity_at` stamped *after* the reference date yields a negative age, passes the
  guard, and reads as "recent" — taking the −0.2 it should not. Unreachable on DO (the field is
  null everywhere) and therefore untested rather than mistested; the fix is `0 <= age <=
  RECENT_ACTIVITY_WINDOW_DAYS`, landed together with the flag.
  `Source: t2 review (docs/reviews/m1-cloudcost-t2-review.md), non-blocking forward.`
- **t1's open item stands:** the live account still carries no genuine orphan
  (§Prerequisites 2), so t5's "≥1 real orphan" done-when still needs one planted. t2's
  detection of it is exercised only against crafted and recorded fixtures until then.
