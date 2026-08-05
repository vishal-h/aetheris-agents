# m3-cloudcost t1 — `fetch_linode.py` + recorded fixtures

**Branch:** `m3-t1-fetch-linode` (off `main@9930aa7`).
**Ticket:** `cloudcost/m3-milestone.md` §t1 (RATIFIED rev 3).
**Live reads:** 2026-08-05, read-only, against the account's own PAT. Every figure below is
either a recorded response or a repo `file:line`; nothing is inferred from Linode's rendered
docs.

---

## 1. §Prerequisites item 2 — `LINODE_BILLING` closure record

The earlier `env -i bash -lc` check was **superseded**: `env -i` clears the environment and
then reads init files, so it tests init files only and is blind to the systemd user manager's
environment block — which is where `LINODE_BILLING` actually lived on this machine. That check
would have reported clean on a session that still carried the value.

`LINODE_BILLING` had **three carriers**, found and cleared in sequence — not one source with
two failed checks:

1. **`~/.profile`** — the original export. Removed. This is what every grep was looking for,
   and why every grep came back empty afterwards.
2. **The systemd user manager environment block** — a copy taken by import at session start,
   which survived the profile edit and which `source ~/.profile` could not retract. Confirmed
   present by `systemctl --user show-environment | rg LINODE` **before** the fix, and cleared
   by `systemctl --user unset-environment LINODE_BILLING`. Check 1 below reads clean because
   this was cleared, **not** because the block was never a carrier — the revised check's
   rationale was not wrong.
3. **`gnome-terminal-server` (pid 12673)** — snapshotted the value at launch and hands it to
   every shell it spawns, including new tabs. Unreachable by any file edit or by
   `unset-environment`; cleared only by the process exiting.

**The generalisable finding.** A uniqueness claim about where an environment value "lives" is
an *observation, not a census* — the same class `CLAUDE.md` records for code seams
(*Adjacent-case: "the one X" is an observation, not a census*), here applying to the process
environment. Environment is copied at fork/exec with **no retraction channel**, so each carrier
must be cleared on its own terms: a file edit cannot reach an imported copy, and
`unset-environment` cannot reach a process that already forked.

**The value was never read, printed, transmitted or hashed at any point.**

Checks re-run in the t1 session (names and set/unset only; check 1 is now informational):

```
=== CHECK 1: systemd user manager environment block ===
manager block: no LINODE names

=== CHECK 2: this session's own environment, as inherited ===
LINODE_BILLING unset
LINODE_TOKEN unset
LINODE_CLI_TOKEN unset
CLOUDCOST_LINODE_TOKEN unset

=== CHECK 3: what a normally-spawned child sees ===
child: LINODE_BILLING unset
child: LINODE_TOKEN unset
child: LINODE_CLI_TOKEN unset
```

`CLOUDCOST_LINODE_TOKEN` reading unset is expected and correct: it lives in
`~/.secrets/linode-cloudcost.env` (present; key name confirmed as `CLOUDCOST_LINODE_TOKEN`,
value not read) and is loaded with `set -a` only at the point of use. A bare `source` would
leave it shell-local and invisible to exactly the child in check 3 — the failure mode
`runbook.md:51-61` already records for AWS.

**Disposition of the value itself is the human's and is not recorded here** — §Prerequisites 2
asks for it, and this session was not in a position to determine what the variable held
(deliberately, having never read it). Carried to the packet as the one open prerequisite.

---

## 2. The three evidence-gated findings

All three were settled from live reads recorded as fixtures, reproducible via
`tests/record_linode_fixtures.py`.

### §D-L4 / U1 — the state mapping: **`offline`**

The account holds 11 instances. Observed `status` values: `running` ×10, `offline` ×1. **No
instance reports `stopped`.** The powered-off instance is id `19294655`, tagged `test server`,
created 2020-02-04.

So `offline` is the customer powered-off state and is what maps onto `STATE_STOPPED`
(`fetch_linode.py` `POWERED_OFF_STATUS`). `stopped` and `billing_suspension` pass through
verbatim — both terminal, neither "the operator turned this off and forgot it".

Why this needed observing rather than reading: the enum holds **two** terminal powered-off
spellings, and `stopped` collides *literally* with the canonical value while the spec
documents it as what **maintenance mode** produces. Mapping by spelling would have produced a
rule that fires for maintenance and never for the ordinary powered-off case — well-formed,
wrong, and silent.

**Corroboration that the mapping is load-bearing rather than cosmetic:** instance 19294655
appears on invoice 32251471 at **$48.00**, and the adapter independently derives $48.00 for it
from `/linode/types`. §Seam 3 is confirmed live — Linode bills a powered-off instance, so
`rule_stopped_compute_with_attached_storage`'s own-cost term is non-zero (DO-shaped, not
AWS-shaped) and must not be zeroed the way `fetch_aws.instance_compute_estimate` zeroes a
stopped EC2 instance.

### §D-L9 / U2 — the static-IP rule is **reachable**, and the spec is stale

**This reverses the scout's provisional reading, and the reversal is the finding.** OpenAPI
`4.215.0` declares an IP object's complete field set as
`{address, gateway, interface_id, linode_id, prefix, public, rdns, region, subnet_mask, type,
vpc_nat_1_1}` — no `reserved` flag anywhere. That is what led §D-L9 to pre-authorise recording
the rule as *not-reachable-on-Linode*.

The live response carries **three fields the spec does not declare**: `reserved`,
`assigned_entity` and `tags`. Two consequences, both load-bearing:

1. **`reserved` is the discriminator, so the rule is reachable.** Only addresses with
   `reserved: true` are emitted as `static_ip`. An automatically-assigned primary is
   inseparable from its instance and can never be an orphan; emitting one would flag
   primaries, the exact false positive §D-L9 forbids. The spec's own request-body prose
   contrasts "a reserved or an automatically assigned IP", so the two-way distinction is the
   provider's, not this adapter's.
2. **`linode_id` alone is NOT the attachment signal.** Of 26 addresses, two carry
   `linode_id: null` while `assigned_entity` names the **NodeBalancer** each belongs to.
   Keying attachment on `linode_id` would have reported two in-service NodeBalancer addresses
   as unassociated orphans. This is the defect the live read caught; a spec-faithful adapter
   would have shipped it.

**Survey of the account:** 26 addresses read, 0 reserved, 0 emitted as `static_ip`, **11
undetermined**. The class is legitimately empty, and the counts are reported in the run summary
under `surveyed` so an observed zero is distinguishable from a class nobody looked at (*absent
is unknown, not zero*).

> **Correction (r1).** The round-0 packet said "every address carries `reserved: false`". That
> is true of the **15 IPv4 rows only**; the **11 IPv6 rows carry neither `reserved` nor
> `assigned_entity`**. The field set is not uniform across address types. This matters
> operationally, not just for accuracy: it is why the determinability gate keys on *no row
> carries it* rather than *every row carries it* — the stricter reading would mark a perfectly
> readable class UNKNOWN on every real run. The rows that cannot be assessed are counted as
> `undetermined` rather than folded into the zero.

This is the `CLAUDE.md` **resolved-versus-advertised** rule in a new carrier: a specification
states what an API is *declared* to return, the wire states what it *does* return, and the two
diverge exactly where the declaration is stale. Recorded as a correction the arbiter may want
to fold into §D-L9; `m3-milestone.md` is outside §t1's Touches and was **not** edited.

### U11 — the volume rate is **per-GB**, confirmed twice

`/volumes/types` row `id: "volume"` carries `price.hourly 0.00015`, `price.monthly 0.1`.
Volume 9022878 is 10 GB in `ap-west`; its invoice line
`"Storage Volume - pvc-0a8dce06b486430a (9022878) - 10 GiB"` carries `unit_price "0.0015"` and
`amount 1.00`.

- `0.00015 × 10 GB == 0.0015` — the billed hourly unit price. ✓
- `0.1 × 10 GB == 1.00` — the billed monthly amount. ✓

Both axes agree and both are exact. `VOLUME_PRICE_BASIS = "per_gb"` carries this citation in
the source. Had it stayed unsettled the adapter would have emitted `0.0` plus a named warning
rather than a plausible per-GB multiply — `rule_unattached_volume` fires on attachment and age,
not on a non-zero estimate (`detect_orphans.py:165-181`), so an unknown basis costs the saving
figure, never the rule.

---

## 3. Design decisions implemented

| Decision | How |
|---|---|
| **D-L1** | `totals.amount = invoice.total` (post-tax, per the spec's own wording), with `invoice.tax` emitted as its own `Tax` line so Σ lines reconciles. `subtotal`/`tax`/`tax_summary`/identity go verbatim into `provider_extra`. The live account is **zero-rated** (`tax: 0.0` on all 140 invoices), so this path is exercised by the one synthetic invoice fixture — clearly marked. |
| **D-L2** | `CURRENCY = "USD"`, adapter-asserted, and `provider_extra.currency_basis` names the spec version `4.215.0` and ETag. Third instance of an established posture, not a new concession. |
| **D-L3** | `source_granularity: "service"`, `resource_id: null` on every line. See §4 on the grouping key. |
| **D-L6** | A non-200 on a class endpoint becomes an `errors[]` entry **and** a `not_inventoried[]` entry; `status: partial`, exit 1. The marker lives in the stdout summary, not the artifact — see §5. |
| **D-L10** | `line_items[].region` populated from `invoice-item.region`; `null` when a service's items span regions, because the schema's rule is a real value or `null`, never a guess. |
| **D-L11** | Images emit `attached_to: null` (an image records no source, so the aged-snapshot rule's second signal has no field to read) and `monthly_cost_estimate: 0.0` **plus a named warning** — Linode publishes no image pricing endpoint at all. Per-instance backups excluded. |
| **D-L5** | No `rate_basis` on the inventory resource. The basis is recorded here and in `warnings[]`, never as a schema field. Asserted by `test_the_inventory_shape_matches_the_frozen_contract`. |
| **D-L7** | Managed Databases excluded, with the reason, in the summary's `exclusions[]`. |
| **D-C** | **Unused, as designed** — every in-scope class maps onto an existing canonical type. No §Normalized extension was needed. |

Excluded classes are recorded as exclusions with reasons in the run summary (done-when 8), not
left as absences.

---

## 4. Decisions the ticket did not pre-settle

### The invoice-item grouping key

Linode labels invoice items **per resource** (`"Linode 8GB - zz-ct-ravendb (19294655)"`).
Grouping on the raw label would have emitted 19 `line_items[]` rows — one per resource — while
every row carried `resource_id: null`: the *shape* of resource-level attribution without the
attribution. §D-L1 says "one row per service (grouped from invoice items)", so `service_of()`
takes the label's leading segment and **discards** the resource-identifying remainder.

Explicitly: this extracts no identifier. §D-L3 forbids parsing a resource id out of the label
and using it as attribution; this function throws that text away and `resource_id` stays `None`
unconditionally. The parse narrows towards the service, never towards the resource. 19 items →
10 service rows, Σ = 422.00 = `invoice.total`.

### `period` is the **covered** month — corrected at r1 (review F1)

An invoice carries a `date` and no period field. The live read shows the two are a month apart:
invoice 32251471 is dated `2026-08-01T04:36:37` and every item runs
`from 2026-07-01T04:00:00` `to 2026-08-01T03:59:59`. **The invoice issued in month M bills
month M-1.**

`period` is the **covered** month on every provider — m1's §Normalized meaning, whose own
example pairs `"period": "2026-07"` with a July fetch. The r0 implementation selected by
*issue* month, which labelled a snapshot `2026-08` while it contained July's charges. Nothing
would ever have errored: a per-provider history tree stays internally consistent under a
constant offset, so the MoM delta is unaffected and only the label is wrong — the quietest
possible silent-wrong-answer, and in a first-class contract field.

What pushed it the wrong way was §t1's own done-check reading
`linode_costs_$(date -u +%Y-%m).json`, which presumes covered ≡ current. That holds on DO
(whose live *preview* invoice makes it true) and on AWS, and is false on Linode. The arbiter has
confirmed it as a doc defect under correction; the implementation now follows §Normalized.

Two consequences, both stated in the output rather than left to a reader:

- **A Linode cost snapshot is structurally one month behind**, because Linode publishes no
  preview invoice. With no `--period`, the newest *settled* invoice is selected, so a bare run
  produces a correctly-labelled report instead of degrading to partial every day of every
  month. The in-flight month survives only as `balance_uninvoiced`, which the `balance` block
  already carries — and which the provider documents as excluding transfer charges.
- **Coverage is read off the items, never derived from a hard-coded "issue month minus one".**
  That offset is one account's observed billing behaviour, not a documented rule; an adapter
  that encoded it would be asserting something the provider never stated. Candidates are
  *ordered* by that observation (a cheap heuristic) and *confirmed* by their items.

`period_basis` states which of `invoice-covered` / `requested` / `fallback-current-month`
produced the label. It is on **both** the run summary and the cost artifact
(`provider_extra.period_basis`, symmetric with `currency_basis` — r1 Q1), so a reader holding
only the JSON can tell an invoice-backed month from any other kind.
`provider_extra.invoice` carries both `issued` and `period_covered`.

### What each `period_basis` value emits (r1 F4)

| Value | When | What is written |
|---|---|---|
| `invoice-covered` | an invoice covering the period was found | **both** artifacts; this is the only value that can appear on a cost snapshot |
| `requested` | `--period` was given and billing failed | **inventory only**, `status: partial`, exit 1 |
| `fallback-current-month` | no `--period` and billing failed | **inventory only**, `status: partial`, exit 1, plus a `warnings[]` entry saying the label is not invoice-confirmed |

**There is no empty-cost-snapshot case, so the ambiguity F4 asks about cannot arise.** A run
that could not read an invoice writes **no cost document at all** — `costs` stays `None` and
only the inventory is emitted. So a zero-spend month (a real invoice whose items total 0.00) and
a failed-billing month are never both "a cost snapshot with empty `line_items`": the first is a
cost snapshot, the second is the *absence* of one, alongside `status: partial`, a non-zero exit
and an `errors[]` entry naming the cause. `test_a_period_no_invoice_covers_is_reported_not_invented`
asserts the explicit-`--period` half, including that no `linode_costs_*.json` is written.

The orchestrator needs no change: it passes no `--period`
(`cloudcost_orchestrator.exs:200`) and reads the period back from STEP 1's summary (`:249`), so
the adapter is the authority on which month it reported.

### `balance` maps two Linode figures onto three schema fields

`month_to_date_balance` and `month_to_date_usage` both take `balance_uninvoiced`;
`account_balance` takes `balance`. That is the AWS precedent exactly
(`fetch_aws.py:751-755` sets both from one figure), not a new concession — a synthesised third
figure would be a number with no provider behind it. Note `balance_uninvoiced` is documented as
**excluding transfer charges**, i.e. incomplete by the provider's own statement.

### NodeBalancer `type` is not a price key

The object carries `type: "common"`; `/nodebalancers/types` keys its rows `nodebalancer` /
`nodebalancer-pr100` / `nodebalancer-40GB-pr100`. Reading the object's value as a price key
yields `None` and would have silently priced **every** load balancer at $0.00.

`NODEBALANCER_TYPE_PRICE_ID` states the one mapping evidence supports: NodeBalancer 1343674 is
`type: "common"` and its invoice line carries `unit_price 0.015` / `amount 10.00`, exactly the
`nodebalancer` row. **`premium` is deliberately absent** — this account holds none, so there is
no evidence for which `-pr100` row it bills at, and an unmapped type yields `0.0` plus a named
warning rather than a guess by name.

---

## 4b. Round-1 changes (review `docs/reviews/m3-cloudcost-t1-review.md`)

| Finding | Change |
|---|---|
| **F1** blocking | `period` is now the covered month (§4 above), with `period_basis`, `issued`, and covered-period invoice selection. |
| **F2** blocking | Reservability branches on **presence**, not truthiness (§4c). Absent `assigned_entity` + null `linode_id` → attachment **undetermined**, never unattached. |
| **F3** blocking | Answered in §5 — all five keys are stdout-only; no unratified extension exists. |
| **F4** | Σ`line_items` == `totals.amount` is now checked at **runtime**, appending a `warnings[]` entry on mismatch, not only over fixtures. |
| **F5** | `surveyed` now covers **every filtered class** — images as well as IPs — in a uniform `read` / `retained` / `emitted` shape. |
| **F6** | Positive control added: the unchanged engine **fires** on Linode-shaped input (§8). |
| **F7** | Carried to t3 (§10). |

**One consequence beyond the findings.** F2's presence gate can populate `not_inventoried`
without any request having failed, and `status`/exit were keyed on `errors` alone — so a run
with an entire class UNKNOWN reported `ok` and exit 0. That is the same silent-success shape
§D-L6 exists to prevent, one level up, so completeness is now `not errors and not
not_inventoried`. Mutation M18 covers it.

## 4c. §D-L9's fields are undeclared, so presence is the gate

`reserved`, `assigned_entity` and `tags` are returned live and declared nowhere in OpenAPI
`4.215.0`. **An undeclared field is not contractual**: nothing obliges Linode to keep returning
it, and a truthiness test would then read false for every address and report a confident zero
for a question it could no longer answer.

- **`reserved`.** If *no* address carries the key, the class is `not_inventoried` with the
  reason "reservability not determinable — field absent from the live response". Never an empty
  emission. The threshold is *no* row rather than *every* row because the field is not uniform
  (IPv4 has it, IPv6 does not); rows lacking it are counted as `undetermined`.
- **`assigned_entity`.** Absent, with `linode_id` null → attachment is **undetermined**, not
  unattached. A false orphan is the costlier error: it invites a human to delete an address that
  is in service. Where the provider actively says the address is assigned to nothing
  (`assigned_entity` present and null), that remains the orphan shape — the two cases must not
  collapse.

Both are asserted against `linode_ips_no_reserved_field.json`, a fixture carrying the spec's
declared field set and nothing more.

## 5. Where the not-inventoried marker lives, and why

**Answer to review F3 — the exact JSON location of each key.** All five are keys of the
`summary` dict built in `main()` (`fetch_linode.py`, the block ending `print(json.dumps(summary,
indent=2))`) and are printed to **stdout only**:

| Key | Location |
|---|---|
| `surveyed` | stdout summary — top-level key |
| `not_inventoried` | stdout summary — top-level key |
| `exclusions` | stdout summary — top-level key |
| `warnings` | stdout summary — top-level key |
| `duration_ms` | stdout summary — top-level key |

**Neither emitted document carries any of them**, so the second horn of F3 does not arise and
there is no unratified §Normalized extension. Verified rather than asserted — the two artifacts
from the live run carry exactly the m1 contract sets:

```
linode_costs_2026-07.json     top-level: account balance currency generated_at line_items
                                         period provider provider_extra source_granularity totals
                              provider_extra: currency_basis invoice
linode_inventory_2026-07.json top-level: account generated_at period provider resources
```

This also matches both predecessors: in `fetch_aws.py`, `"warnings"`, `"errors"` and
`"regions_swept"` each occur exactly **once** in the file — in its own stdout summary
(`fetch_aws.py:1113-1128`). So stdout-only is the established behaviour of the use case, not
something t1 introduced.

**The gap F3 identifies is real, and it is pre-existing rather than Linode's.** The
not-inventoried marker does not reach the rendered report; it is consumed by the orchestrator
and then lost. Making it durable means putting it on an artifact, and the inventory envelope is
frozen with **no extras key at all** — so that is a §Normalized extension and belongs to §D-C's
doc-first path (arbiter-applied, before the adapter emits it), not to this ticket. Flagged for
the arbiter with the note that ratifying one would not disturb the milestone's negative proof,
which constrains the four shared *scripts*, not the schema. Until then it lives in the
**stdout summary**, beside `errors[]`, `warnings[]` and `exclusions[]` — the adapter's own
contract with the orchestrator.

The summary gives the three cases distinct homes, so they cannot collapse into each other:

| Case | Where it renders |
|---|---|
| A class was read and returned rows | `resources[]` |
| A class was read and legitimately returned nothing | `surveyed{}` — with the counts behind the zero |
| A class could not be read | `errors[]` + `not_inventoried[]`, `status: partial`, exit 1 |
| A class was never swept, by decision | `exclusions[]`, with the reason |

---

## 6. Deviations from §t1's Touches list — declared

1. **`cloudcost/tests/record_linode_fixtures.py`** (new). §t1's Touches does not name a
   recorder; the AWS precedent (`tests/record_aws_fixtures.py`) is the reason it exists here.
   It reads `CLOUDCOST_LINODE_TOKEN` explicitly through the adapter's own loader, scrubs in
   **code** (account identity, addresses, hostnames, `rdns`, token-shaped strings → stable
   placeholders in the RFC 5737 / RFC 3849 documentation ranges), writes to `--out` and never
   over `tests/fixtures/`, and records the §D-L4 and §D-L9 responses so both findings are
   reproducible from the repo rather than resting on a transcript.
2. **`cloudcost/tests/conftest.py`** (edit, +65 lines, **purely additive**). `LinodeStub` and
   the two stub fixtures live where the DO and AWS stubs already live.

**Not imported, duplicated on purpose** (the CLI-to-CLI anti-pattern, `_normalized.py:35-37`):
`current_period`, `iso_now`, `write_json`, `warn_shadowing_env`, `tags_of` — each already
exists twice in the predecessors. `record_linode_fixtures.py` duplicates rather than imports
from `record_aws_fixtures.py`.

**One deliberate convergence:** `money` is **imported from `_normalized`** rather than
duplicated. That module is where the shared definition lives; the predecessors' private copies
predate it and disagree with each other — `fetch_do`'s **raises** on an uncoercible value,
`fetch_aws`'s **swallows to 0.0**, and `_normalized`'s swallows. Importing avoids a third
copy, and the swallow is the right default for an adapter that must degrade rather than break
its stdout contract.

But the swallow has a cost, and it is paid explicitly: Linode states `unit_price` as a
**string**, so a malformed amount coerces to 0.0 and drops out of the sum with no exception
anywhere. That is why Σ`line_items` == `totals.amount` is now a **runtime** check (r1 F4) and
not only a fixture assertion — the choice to import is what makes the runtime guard necessary,
so the two are recorded together.

**Fixture stability.** Re-running the recorder against the same account reproduces the fixtures
except where the account changed. What is *not* stable by construction:
`created`/`updated`/`date` timestamps, `balance`/`balance_uninvoiced`, and the in-flight
month's amounts. The committed fixtures therefore pin a **settled** invoice (32251471), not the
current month. Trimmed recordings state what was dropped in `_comment`; synthetic fixtures say
`SYNTHETIC` and say why the live account cannot supply the shape.

---

## 7. Two defects found by the work's own checks

Recorded because both are instances of classes `CLAUDE.md` already names, and both were caught
by a check rather than by review.

1. **The scrubber corrupted every timestamp.** The IPv6 regex matched the `04:20:01` inside an
   ISO timestamp and rewrote `2026-08-01T04:20:01` to `2026-08-01T042001:db8::86`. The regex
   was written to over-match deliberately — a scrub must never let a real address through —
   but over-matching without a parser is not a scrub, it is corruption. Fixed by validating
   every candidate with `ipaddress.ip_address()` before replacing it, and mutation-checked in
   both directions (timestamp survives; real address still replaced; subnet mask survives;
   placeholder assignment stable across repeats). Caught because the recorder prints the
   invoice it recorded, and the date read `2026-08-01T042001:db8::86`.

2. **A `return aws_stub` was dropped from `conftest.full_aws_stub`.** My edit anchored on a
   window that ended one line short of the function, so the fixture returned `None` and **43
   AWS tests failed**. Caught by running the whole cloudcost suite off-territory, then
   localised by running `test_fetch_aws.py` in a clean worktree at `main` — green there, red on
   the branch, which identified the shared file as the cause rather than the new code. The
   `conftest.py` diff is now `65 insertions(+)`, 0 deletions, asserted in the packet. This is
   the *off-territory gate* rule earning its keep: the AWS suite is not t1's territory and
   nothing in the ticket would have run it.

---

## 8. Mutation record

Every load-bearing check was watched failing in the state it guards, then restored (the
Silent-wrong-answer rule: a check only ever seen passing is not yet a check).

| # | Broken state constructed | Guard that fired |
|---|---|---|
| M1 | `POWERED_OFF_STATUS` → the colliding `"stopped"` | D-L4 mapping + own-cost tests |
| M2 | `VOLUME_PRICE_BASIS` → `per_volume` | per-GB tests (both, incl. the invoice cross-check) |
| M3 | NodeBalancer priced off its own `type` value | `nodebalancer_common_prices_through…` |
| M4 | `assigned_entity` ignored (linode_id only) | `nodebalancer_address_is_not_read_as_unattached` |
| M5 | `is_reservable_address` → always True | `only_reserved_addresses_are_emitted` |
| M6 | unknown backend count rendered as zero | `configs_could_not_be_read_is_not_reported_idle` |
| M7 | `not_inventoried` never appended | `failing_class_is_an_error_plus_not_inventoried` |
| M8 | `service_of` → the whole label | service-granularity tests |
| M9 | synthetic `Tax` row never added | `tax_is_its_own_line` |
| M10 | `TYPE_LOAD_BALANCER` → a local literal | vocabulary guard |
| M11 | `_redact` returns text unchanged | `error_body_echoing_the_token` |
| M12 | period taken from the invoice's **issue** month (r1 F1) | covered-period tests |
| M13 | reservability gate → always determinable (r1 F2) | `vanished_reserved_field` |
| M14 | absent `assigned_entity` read as unattached (r1 F2) | `attachment_is_undetermined…` |
| M15 | runtime reconciliation check disabled (r1 F4) | `reconciliation_is_checked_at_RUNTIME` |
| M16 | `surveyed["images"]` never recorded (r1 F5) | `images_survey…` |
| M17 | an unattached volume reports as attached (r1 F6) | `shared_rule_engine_FIRES` |
| M18 | `complete` ignores `not_inventoried` | `vanished_reserved_field` |
| M19 | `period_basis` dropped from the artifact (r1 Q1) | `period_is_the_covered_month…` |

**M10 was re-run after the guard was narrowed.** The guard initially failed on a true positive:
Linode's price-table id is `"volume"`, spelled identically to the canonical `TYPE_VOLUME` and
meaning something entirely different (a wire value versus schema vocabulary). Narrowing a guard
is exactly where one makes it vacuous, so the exemption is a single named assignment, the guard
asserts that literal appears **once**, and M10 was replayed afterwards to confirm the narrowed
guard still catches a real local spelling. The collision is recorded at `VOLUME_TYPE_ID`.

---

## 9. Measured latency — the BL-096 input for t2

Two live runs: **4441 ms** and **4097 ms** wall clock, reported as `duration_ms` in the stdout
summary (neither predecessor reports one).

Against the shared `fetch_timeout_ms = 300_000` (`cloudcost_orchestrator.exs:116`) that is a
margin of roughly **73×**. Per `runbook.md:420-428` this is **recorded, not acted on** — t2
consumes the measurement and the number changes only if the margin is inadequate. It is not.

---

## 10. Carried forward

- **§Prerequisites 2 disposition** — what `LINODE_BILLING` held, and revoke-or-record, remains
  the human's call (§1).
- **t3's BL-069 plant must be a `common` NodeBalancer, or an unattached volume** (r1 F7).
  `premium` is deliberately unmapped and prices at `0.0` plus a warning, so a premium plant
  would satisfy the ≥1-orphan assertion with a $0.00 saving — a candidate with no dollar figure
  is a weak proof of a cost report. The unattached volume remains the cheapest certain choice
  (§Rule reachability), and at the live per-GB rate a 20 GB volume carries a real $2.00.
- **Persisting `not_inventoried` onto an artifact** is a §D-C doc-first extension and is not
  t1's to make (§5). **Filed as BL-098** — prose in a packet files nothing.

### Obligations t2 inherits (r1 F2, F3)

**1. `sprint.sh` constructs the report filename from the current month, and that is now wrong
for Linode — CONFIRMED, not predicted.** `../aetheris/scripts/sprint.sh:2504` reads:

```bash
  # The report is named for the billing period — the current UTC month, which is what
  # both adapters default to.
  CLOUDCOST_PERIOD=$(date -u +%Y-%m)
  CLOUDCOST_REPORT="${CLOUDCOST_OUT}/cloudcost_report_${CLOUDCOST_PERIOD}.html"
```

That comment is true of DO and AWS and **false of Linode as of t1**: a Linode run on 2026-08-05
writes `cloudcost_report_2026-07.html`, so the existence assertion at `:2511` fails for a reason
that has nothing to do with the report, and `report_data_${PERIOD}.json` at `:2506` misses too.
Verified by reading the file at t1 rather than left for t3's run to discover. The fix belongs to
t2 (`sprint.sh` is in §t2's Touches, not §t1's): take the period from STEP 1's reported
`period` — the orchestrator already passes no `--period` (`cloudcost_orchestrator.exs:200`) and
reads the period back (`:249`) — or glob, but do not construct it from the wall clock.

**2. The runbook owes a line on run-level completeness.** `not_inventoried` non-empty now makes
the run `partial` and exit 1, so a transient 500 on one class stops the pipeline instead of
producing a report with a quiet hole. That is changed observable semantics, which methodology §6
puts in the runbook; it belongs in t2's `### Linode` subsection beside the credential posture.
- **§D-L9 is stated against a stale spec** — the milestone text says the rule may be
  unreachable; the live API says otherwise (§2). Arbiter's call whether to amend the doc.
- **`period` semantics differ from DO** — issue month versus covered month (§4).
- **NodeBalancer `premium` is unpriced** — no evidence in this account; emits 0.0 + warning.
- **Zero orphans on this account today.** `detect_orphans.py` runs unchanged over the live
  inventory and reports 0 candidates, 0 skipped — correctly: the sole volume is attached, both
  NodeBalancers serve backends, no image is private, no address is reserved, and the offline
  instance carries no attached storage. This is direct confirmation that t3's BL-069 plant is
  genuinely required for the ≥1-orphan done-when, not a formality.
- **`is_public` images are skipped** — all 39 images on the account are Linode distribution
  images. If the account ever owns a private image the aged-snapshot rule becomes live; the
  path is covered by a synthetic fixture today.
