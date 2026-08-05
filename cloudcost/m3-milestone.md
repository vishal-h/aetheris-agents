# m3-cloudcost — Linode as provider three (report-only)

**Status:** **RATIFIED 2026-08-04** — approved by the human and committed per
`milestone-methodology.md` §4 (rev 7). t1 DONE — `fetch_linode.py`, fixtures and offline suite;
three review rounds, merged at `cb3ca63`. t2 DONE — orchestrator literal and credential raise,
manifest, sprint case, runbook, BL-092. t3 DONE — the live run
(`cloudcost-orch-linode-h5lltQ`, 18 `[OK]` / 0 `[FAIL]`), the negative proof, BL-090, the PAT
expiry; see §Milestone summary. **Click-through gate PASSED 2026-08-05** at `m3-t3-run@14489aa`,
observed by the human on both surfaces: "View report" opened the Linode HTML showing the planted
NodeBalancer with its evidence and a $10.00 saving, and the capability-matrix view showed the
regenerated cloudcost section.
**Drafted:** 2026-08-04 by claude-ui, against aetheris-agents `main@dc8c077`, harness `265d336`.
**Scout basis:** `cloudcost/docs/m3-linode-scout.md` — Linode OpenAPI `4.215.0`,
ETag `290888161afda3d3566f755d664856fb937fbafbf817838587bb2be6e77ef6cd`, retrieved
2026-08-04 14:19 UTC. Every seam claim below is cited to that file or to repo `file:line`.
Nothing here is inferred from Linode's rendered docs.
**Predecessors:** m1-cloudcost (`cloudcost/milestone.md` — §Normalized schemas is the frozen
contract this adapter is written to); m2-cloudcost (`cloudcost/m2-milestone.md`, AWS).

**Rev 2 (2026-08-04):** §Prerequisites 2 gains its closure test (removal from one init file
is not closure); §t2 Done-check gains the `CC_HERMETIC` Linode arm and the `set -a` load
requirement. Both from the t1-kickoff review; neither changes scope, tickets or done-when.

**Rev 3 (2026-08-04):** one citation corrected in §t2 — the `*)` arm is `sprint.sh:2393`;
`:2394` is its fail line. The rev-2 text attached the arm's identity to the body's line
number. No scope, ticket or done-when change.

**Rev 4 (2026-08-05):** §Prerequisites 3 and §Rule reachability corrected — the BL-069 plant
is a zero-backend NodeBalancer, not an unattached volume, because every other reachable rule
carries an age threshold a same-day plant cannot satisfy. §t3's done-check and prompt follow.
Found at t1 kickoff; the rev-1 text would have produced an expected-red ≥1-orphan assertion.

**Rev 5 (2026-08-05):** from the t1 r0/r1 reviews — §t1's done-check no longer constructs the
artifact filename from the clock; D-L9 records that the live API contradicts the spec and how
the determinability gate is shaped; §Seam analysis gains seam 7 (no preview invoice → the
snapshot is a month behind); §t2's done-check gains the report-filename verification and the
partial-run runbook line. No scope or ticket-set change.

**Rev 6 (2026-08-05):** from the t2 review — §Done-when 5 corrected from "three manifests" to
every committed manifest; §t2's unsound "or from STEP 1's reported period" alternative removed;
seven `runbook.md` references corrected after t2's insert — six line citations re-pinned,
and §t2's insert-position pointer re-anchored to the surrounding headings, which was the
same decay from the other direction: a number that was a target when written and a claim
once the work landed; the two stale `fetch_linode.py` strings
recorded in §Open items. No scope or ticket-set change.

**Rev 7 (2026-08-05):** §t3's expected matrix Summary count corrected from seven to eight —
the earlier figure predated `fetch_linode.py`. Found at t3 by the regen producing the right
answer against a stale expectation. No scope or ticket-set change.

---

## Goal

Prove the frozen-adapter-contract bet a **third** time: a new provider is a new adapter plus
its fixtures plus its own run, with `detect_orphans.py`, `compose_report_data.py`,
`render_report.py` and the m1 §Normalized schemas unchanged. Linode is deliberately the
smaller adapter, so this is the faster second proof that the contract generalizes past AWS
rather than the bigger coverage win.

## Done-when (milestone)

1. **Positive.** The pipeline runs end-to-end via `cloudcost_orchestrator.exs` with
   `CLOUDCOST_PROVIDER=linode` against the real account (read-only) and produces a report
   carrying **≥1 orphan** with its evidence trail, reviewable without the Linode console.
2. **Negative proof — the actual claim of this milestone.** At close,
   `scripts/detect_orphans.py`, `scripts/compose_report_data.py` and
   `scripts/render_report.py` are **byte-identical to `dc8c077`**, and
   `scripts/_normalized.py` is unchanged unless a §Normalized extension was ratified
   doc-first (§D-C). Assert this with `git diff --stat dc8c077 -- <the four paths>` in the
   t3 packet; a non-empty diff is a blocking finding, not a note.
3. Offline pytest green for `fetch_linode` against recorded fixtures, **no token needed**.
4. **Click-through merge gate** (not a residual): "View report" opens the Linode report from
   Rig. The hand-off names the branch under test.
5. **BL-090** regenerated — both stale cloudcost cells reconciled (`detect_optimization_signals`
   omission and the pre-BL-083 `Cloudcost Orchestrator` label). **BL-092** serde guard landed,
   covering **every committed manifest** — discovered by walk rather than listed, so the figure
   cannot go stale.
6. The tax ruling (§D-L1), the currency basis (§D-L2) and the fetch-timeout margin
   confirmation (`cloudcost/runbook.md:553-566`) are each recorded in the repo.
7. `CLOUDCOST_LINODE_TOKEN` appears in neither stdout, stderr, nor the trajectory.
8. **Every excluded resource class is recorded as an exclusion**, with its reason — never left
   as an absence. *Absent is unknown, not zero.*

## NOT in scope

Object Storage, LKE, Firewalls, VPCs (never scouted); **Managed Databases** (§D-L7); **per-instance
backups** (§D-L11); `last_activity_at` (§D-L8); a `rate_basis` field on the inventory schema
(§D-L5); resource-level cost (§D-L3); recorded-path (scrape stays — BL-073's resolver is already
provider-agnostic); BL-074's remaining sweep; the cold set BL-087–094 except BL-090 and BL-092,
which fold into this arc.

---

## Prerequisites (human-owned)

1. **A read-only PAT → `CLOUDCOST_LINODE_TOKEN`.** Read Only on exactly: **Account** (this is the
   billing surface — there is no separate Billing scope), **Linodes**, **Volumes**, **IPs**,
   **NodeBalancers**, **Images**. No Access on everything else, **including Databases** (§D-L7)
   and **Events** (§D-L8). Record the token's expiry date in `cloudcost/runbook.md` alongside the
   posture: an unrecorded expiry becomes a failed run months from now with no obvious cause.
2. **Resolve `LINODE_BILLING`.** The build machine carried a 64-character,
   credential-shaped environment variable under that name (scout §B8, U12). No Linode
   library reads it. If it is a PAT under a non-standard name it is a live instance of the
   exact shadowing class this milestone writes a guard for. **Removing it from one init
   file is not closure.** Two checks and one decision close it:
   - **Fresh login shell, all three shadow names absent.** `~/.bashrc`, `~/.zshrc`,
     `/etc/profile` and `/etc/profile.d/*` can each re-export it, and an already-running
     shell keeps the old value:
     ```bash
     env -i bash -lc '[ -z "$LINODE_BILLING" ] && [ -z "$LINODE_TOKEN" ] \
       && [ -z "$LINODE_CLI_TOKEN" ] && echo SHADOW-CLEAN'
     ```
   - **The run environment carries the intended token, and only it.** Loaded from
     `~/.secrets/linode-cloudcost.env` with `set -a` (see §t2), a child process must see
     `CLOUDCOST_LINODE_TOKEN` set and the three names above unset.
   - **Decide what it was.** If it held a live Linode PAT, revoke it rather than relocate
     it: a credential of unknown provenance that reached a login shell under an
     undocumented name has an unknown exposure history, and the replacement PAT is being
     created for this milestone anyway. Record the disposition in t1's implementation
     notes. If it held something else, record that instead — an unexplained
     credential-shaped variable is not closed by deleting the line that set it.
3. **Two account actions, and they are not the same one.**
   - **A powered-off Linode instance**, for t1's D-L4 fixture. Any instance, no age
     requirement; a throwaway nano is fine if you would rather not disturb a real one.
     Powering off costs nothing — Linode bills a powered-off instance the same (§Seam 3).
     If the account holds no instances at all, D-L4 and both compute rules are untestable
     and that is a scope conversation, not a fixture problem.
   - **A zero-backend NodeBalancer**, for t3's BL-069 plant. Create it before the run or the
     ≥1-orphan assertion is expected-red. **Not** an unattached volume — see §Rule
     reachability.

---

## Design decisions

**D-L1 — `totals.amount` is post-tax, with tax as its own service line, matching AWS.**
The scout settled the comparability question the existing two adapters left open. AWS's total is
the adapter's own sum over Cost Explorer `SERVICE` groups, and Cost Explorer returns `Tax` as one
of those groups, unfiltered (`fetch_aws.py:741`, `:728-740`; fixture
`aws_ce_cost_and_usage.json` shows a `['Tax'] 8.40 USD` group). Linode's invoice carries
`subtotal` / `tax` / `tax_summary[]` / `total` as four separate fields with explicit
before/after-tax descriptions. So the adapter emits one `line_items[]` row per service (grouped
from invoice items) **plus a synthetic `Tax` row taken from `invoice.tax`**, and
`totals.amount = invoice.total`. Σ`line_items[].amount` must reconcile to `totals.amount` — assert
it in the fixture tests. `subtotal`, `tax`, `tax_summary[]` and the invoice identity go verbatim
into `provider_extra`. This is not a synthesised figure: the tax number is the provider's own, and
the shape mirrors what AWS already ships. **DO's treatment remains undetermined** (its adapter
reads one scalar, `fetch_do.py:306`, and the recorded fixture has `taxes.amount == 0.00`, so it
cannot discriminate) — file it, do not assume it.

**D-L2 — `currency: "USD"` is adapter-asserted with a stated basis.** Two independent sweeps of
the 7.9 MB spec found **no currency field anywhere**, billing surface included; USD appears 100
times, exclusively in `description` strings. This is the same posture both predecessors already
take (`fetch_do.py:55-56`, `fetch_aws.py:70-71`), so it is the third instance of an established
pattern rather than a new concession. The constant carries its basis as a comment naming the spec
version and ETag. The m1 multi-currency §Open item **stays parked**: all three providers are USD,
and per-provider solo runs mean the cross-provider path cannot fire regardless.

**D-L3 — service granularity is forced, not chosen.** `invoice-item` has exactly ten properties
and none is a machine-readable resource identifier (`additionalProperties: false` on both the
named schema and the endpoint's inline copy). A resource appears only inside the human `label`
string. Parsing an id out of that label is fabricated attribution of exactly the kind D4 forbids.
So `source_granularity: "service"`, `resource_id: null` on every cost line. **Record in BL-071
that its trigger — "the first provider actually billed per resource" — does not fire on Linode**,
so the next reader does not re-derive it.

**D-L4 — the state mapping is evidence-gated, and is the sharpest test in this milestone.**
Linode's instance `status` enum has **fourteen** values and **two** terminal powered-off spellings:
`offline`, and `stopped` — which *literally collides with the canonical value* `STATE_STOPPED`
(`_normalized.py:62`) while the spec documents it as what **maintenance mode** produces. A naive
pass-through therefore yields a rule that fires for the maintenance case and never for the ordinary
powered-off one: a well-formed wrong answer with no error anywhere. DO needed a rename
(`off`→`stopped`), AWS an identity map; Linode needs a **decision between two candidates**, a third
kind of mapping this seam has never had to express. **t1 settles it from a recorded fixture taken
against a deliberately powered-off Linode, not from the spec and not from the coincidence of
spelling.** `billing_suspension` and whichever of the two is *not* the customer-off state pass
through verbatim — they are terminal but they are not "the operator turned this off and forgot it".

**D-L5 — no new first-class field on the frozen inventory schema.** The premise that `fetch_aws`
emits `rate_basis` is **false**: neither adapter emits it and it is not part of §Normalized. It
belongs to `detect_optimization_signals.py`, the m2 t4 spike. Linode *could* carry real per-class
prices honestly and cheaply — the four `types` endpoints are **unauthenticated** (`security: null`),
so a Linode adapter can read live prices where both predecessors hard-code a table — but adding a
basis field to the inventory resource is a §Normalized change, and making one inside the milestone
whose entire purpose is proving §Normalized doesn't change would confound the proof. So: read live
prices, record their provenance in the implementation notes and in `provider_extra`, and **file the
uniform retro-fit** (a `rate_basis` companion on `monthly_cost_estimate`, applied to all three
adapters at once) as a backlog row for a later milestone.

**D-L6 — a resource class never degrades silently to `[]`.** The spec declares only `200` and
`default` on every in-scope operation and defers status codes to an external page, so there is no
documented discriminator for a scope denial; and the `/profile/tokens` scope read-back is
self-defeating (it needs `account:read_only`, and identifying which row is the calling token means
comparing a prefix of the secret, which the D2 posture forbids handling). The instrument is
therefore the one the adapters already have: **any non-200 on a class endpoint becomes an
`errors[]` entry and that class is marked not-inventoried — never an empty list.** The precedent is
explicit and already adjudicated once: `fetch_aws.py:98-102` records why `UnauthorizedOperation` is
deliberately not treated as a benign warning, because it would "produce an empty inventory on a
green run, with a reason that reads plausibly and is wrong."

**D-L7 — Managed Databases are excluded, on three independent grounds.** No attachment field
(`rule_stopped_database_with_storage` requires `attached_to is None`, `detect_orphans.py:323`);
no price object on `/databases/types` at all, so `monthly_cost_estimate > 0` (`:326`) can never be
satisfied honestly; and the spec **contradicts itself** on whether the scope even exists —
`/databases/instances` requires `databases:read_only`, which is absent from the 29 scopes in
`components.securitySchemes`. Managed Databases also carry no `tags` field, so including them would
drag `tag_coverage` down and could flip `account_uses_tags` (`detect_orphans.py:500`) — a governance
figure moved by a schema gap rather than by the account's practice. Excluded, recorded, not silently
absent.

**D-L8 — `last_activity_at` stays `null`, and the reason is correctness, not scope minimalism.**
`/account/events` exists, but its `action` enum is control-plane operations, so the newest event's
timestamp answers "when was this resource last **changed**", not "when was it last **used**" — a
different quantity from what `modifier_recent_activity` (`detect_orphans.py:364-383`) reads it as.
Retention is 90 days, and Managed Databases have no `entity.type` at all. Populating it would also
arm m1's open defect (the recency window rejects only on `age > window`, so a future-dated value
takes the −0.2). Both predecessors emit `null` and `detect_orphans.py:76-77` calls that "the correct
outcome, not a gap". **Trigger for revisiting:** an adapter with a genuine last-*used* signal, which
owes the window fix as a prerequisite.

**D-L9 — the static-IP rule may be unreachable on Linode; do not approximate it.** No IP response
schema carries a `reserved` flag, no endpoint lists reservations, and an IP object has no
`created` timestamp. Attachment is expressible (`linode_id`); **reservation is not**. t1 establishes
from one live read whether an extra/unassigned address is distinguishable from the free primary
address every Linode has. If it is not, the rule is **recorded as not-reachable-on-Linode** — never
approximated by treating every unattached address as an orphan, which would flag primaries.

**Resolved at t1, and the spec was incomplete rather than merely stale.** The live API returns
three fields OpenAPI 4.215.0 does not declare — `reserved`, `assigned_entity` and `tags` — so
the rule **is** reachable: only `reserved: true` addresses are emitted. Two consequences the
spec could not have given. First, `linode_id` alone is not the attachment signal: addresses
serving a NodeBalancer carry `linode_id: null` with `assigned_entity` naming the balancer, and
a spec-faithful adapter would have reported them as orphans. Second, the field set is **not
uniform across address types** — IPv4 rows carry `reserved`, IPv6 rows carry neither it nor
`assigned_entity` — so the determinability gate gates on *no row carrying the field*, not on
every row carrying it, and unassessable rows are counted as `undetermined` rather than folded
into the zero. Absence of the field is "cannot assess", never "none found".

**D-L10 — populate `line_items[].region`.** `invoice-item.region` is non-null for hourly items.
Nothing downstream reads it today (verified: `service_totals` reads only `service` and `amount`;
no template expression touches it), but §Normalized's rule is emit-with-a-real-value-or-`null`,
never by omission — and Linode is the first provider that has the concept.

**D-L11 — per-instance backups are excluded; Images are in.** Backups are an N+1 call gated on
`backups.enabled`, carry no tags and no region, and — decisively — exist only while their parent
Linode does, so the aged-orphan semantics (a snapshot whose source is gone) is structurally
unavailable. Images are a flat collection with `created`, `status` and `tags`. Note for t1: an image
also records **no source**, so the aged-snapshot rule's second evidence signal (`attached_to is
None` meaning the source is gone, `detect_orphans.py:220-223`) has no field to read on Linode; emit
`attached_to: null` and let the rule fire on age alone, which is its primary signal.

**D-C — canonical-type extension.** Pre-authorized doc-first: an extension lands as a section-scoped
edit to `cloudcost/milestone.md` §Normalized, applied against HEAD and diffed by the arbiter,
**before** the adapter emits the new value. A local spelling inside the adapter or a rule is a
contract break, not an extension. **As designed, m3 needs no extension** — every in-scope class maps
onto an existing canonical type (§Seam 2). That the pre-authorization goes unused is itself a
result: it is evidence for the bet, and the t3 packet should say so explicitly.

---

## §Seam analysis — where the bet is won or lost

| # | Seam | Linode's answer | Ruling |
|---|---|---|---|
| 1 | `state` → `STATE_STOPPED` | 14-value enum, **two** terminal powered-off spellings (`offline`, `stopped`), one colliding with the canonical value; `stopped` documented as maintenance mode | §D-L4 — settled by fixture at t1, not by design |
| 2 | `type` → `CANONICAL_TYPES` | instance→`compute_instance`, volume→`volume`, NodeBalancer→`load_balancer`, image→`snapshot`, IP→`static_ip` (conditional, §D-L9) | No extension needed; every value imported from `_normalized`, never spelled locally |
| 3 | Bills-regardless-of-state (BL-074's third seam) | **DO-shaped, not AWS-shaped** — Akamai/Linode accrues charges for a service "even if it is powered off". A stopped Linode's own `monthly_cost_estimate` is **non-zero** | Adapter carries the cost model (D5); `rule_stopped_compute_with_attached_storage` sums own + attached volumes and needs no change |
| 4 | `attached_to` | Volume→`linode_id` (nullable, clean). NodeBalancer backends are **not on the object**: `nodes_status.{up,down}` lives on each config, so zero-backends ⇔ Σ(up+down)==0 across configs, including zero configs. **1 + N requests.** No tag-targeting concept exists, so DO's `"tag:<name>"` carve-out has no Linode analogue | Adapter-owned; record the absent tag-targeting as *checked and absent*, not unmentioned |
| 5 | Granularity | No resource identifier on invoice items | §D-L3 — service-level, forced |
| 6 | **Tax / what `totals.amount` means** — new, surfaced by Linode | `subtotal` / `tax` / `tax_summary[]` / `total` are four explicit fields | §D-L1 — post-tax with a synthetic `Tax` line, matching AWS's observed shape |
| 7 | **What "the current period" means** — new, surfaced by Linode | No preview invoice: the in-flight month exists only as `balance_uninvoiced`, and the newest settled invoice covers the previous month | `period` is the **covered** period on every provider (m1's semantics); a Linode snapshot is structurally one month behind, and the basis is recorded on the artifact, not inferred |

**Adjacent seams checked, not carried:** `KEEP_TAG` — Linode tags are flat strings like DO's, so
`"keep=true"` is writable by hand and the constant needs no change (it remains the adapter
convention BL-074 already names, unresolved and untouched here). Pagination differs in kind
(page-number with a total, versus DO's follow-the-URL), so `_same_origin`'s re-rooting guard has no
Linode analogue and must not be copied. Rate limits are **not in the spec** — an absence of a
*special* limit, not evidence of no limit.

## §Rule reachability — which of the six rules can actually fire on Linode

This section exists because "the adapter emits the schema" does not imply "the rules find
anything", and the ≥1-orphan done-when depends on the difference.

| Rule | Reachable | Basis |
|---|---|---|
| `rule_unattached_volume` | **Yes** | `linode_id` nullable, `created` present, live price from `/volumes/types` |
| `rule_idle_load_balancer` | **Yes** | `nodes_status.{up,down}` per config; live price from `/nodebalancers/types` |
| `rule_stopped_compute_with_attached_storage` | **Yes**, gated on §D-L4 | Linode bills powered-off instances, so `own` is non-zero (DO-shaped) |
| `rule_aged_snapshot` (Images) | **Partly** | `created` + `status` present; **no pricing endpoint for images**, so the saving is unknown — emit `0.0` plus a named `warnings[]` entry, the `fetch_aws.py:474-482` precedent. Never an invented figure |
| `rule_unassociated_static_ip` | **Yes**, reserved addresses only | §D-L9 resolved at t1: the live API returns an undeclared `reserved` flag, so a reserved unassigned address is the orphan shape and an automatically-assigned primary is never emitted. No age threshold (`:187-199`) |
| `rule_stopped_database_with_storage` | **No** | §D-L7 — class excluded |

**Consequence for the plant (BL-069) — the age thresholds decide this, not the confidence
scores.** Of the rules reachable on Linode, `rule_unattached_volume` requires `created_at`
age **> 14 days** and `rule_stopped_compute_with_attached_storage` **> 30 days**
(`detect_orphans.py:165-184`, `:248-303`), so a resource planted the same day produces no
candidate. `rule_aged_snapshot`'s threshold is overridable via `--snapshot-age-days`, but
lowering a threshold to make an orphan appear games the assertion rather than satisfying it.
**Two reachable rules carry no age requirement** — `rule_idle_load_balancer` (`:227-245`,
keying on type and `attached_to is None` alone) and `rule_unassociated_static_ip`
(`:187-199`), the latter reachable only because t1 found the undeclared `reserved` flag
(§D-L9). Either is plantable the same day. **The plant is a `common` NodeBalancer**, for a
reason that is about the evidence rather than the rule: it is the option that yields a real
dollar figure. Linode publishes no per-address price endpoint, so a reserved IPv4 prices at
`0.0` plus a named warning (`fetch_linode.py:865`) — satisfying the ≥1-orphan assertion with no saving,
which is a weak proof for a cost report, and the same trap as a `premium` NodeBalancer.
It also exercises the 1+N configs read, which is Linode's most distinctive inventory path.

*The static-IP saving is structurally zero today, not incidentally so.* `fetch_linode.py:865`
emits `monthly_cost_estimate: 0.0` for every `static_ip` unconditionally, with the warning at
`:1266-1267` stating that Linode publishes no pricing endpoint for addresses, so the saving is
**unknown, not zero**. A reserved unassigned address is therefore a valid orphan with no dollar
figure, which is why it is not the plant. This changes only if an address rate becomes
derivable with provenance — the DO precedent is `RESERVED_IP_UNASSIGNED_MONTHLY = 4.38`
(`fetch_do.py:67`), confirmed against a real invoice line — and no such line can exist on this
account until it bills an address. Revisit then, not before.

*What m1's recipe would have cost:* DO's planted orphan was an unassociated reserved IP, and
that rule transfers to Linode only because of an undocumented field. Had the spec been
complete, a same-day plant would have had exactly one option.

---

## Ticket set

### t1 — `fetch_linode.py` + recorded fixtures

**Scope.** A read-only Linode cost + inventory adapter emitting the two frozen §Normalized
artifacts, plus its offline pytest suite against recorded fixtures. Billing from
`/account` + `/account/invoices` + `/account/invoices/{id}/items`; inventory from
`/linode/instances`, `/volumes`, `/networking/ips`, `/nodebalancers` (+ `/{id}/configs`),
`/images`; prices from the four unauthenticated `types` endpoints. Implements §D-L1, L2, L3, L6,
L10, L11 and settles §D-L4 and §D-L9 from live reads recorded as fixtures. Measures and reports
its own wall-clock latency (the BL-096 input).

**Contract refs.** `cloudcost/milestone.md` §Normalized schemas; `scripts/_normalized.py`
(`CANONICAL_TYPES`, `STATE_STOPPED`, and the helpers — import them, never re-spell them);
`agent-creation-guide.md`; both `CLAUDE.md` learning sections; this doc's §Design decisions and
§Seam analysis; `cloudcost/docs/m3-linode-scout.md` for the API surface.

**Touches.** `cloudcost/scripts/fetch_linode.py`; `cloudcost/tests/test_fetch_linode.py`;
`cloudcost/tests/fixtures/linode_*.json`; `cloudcost/requirements.txt` if a dependency is added.

**Do not generate.** Any write/management call (list/get only). A `linode_api4` or `linode-cli`
dependency whose credential arrives by default env pickup — the token is passed explicitly (the SDK
reads **no** environment variable, which makes this trivially satisfiable). Any read of
`LINODE_CLI_API_HOST` / `_VERSION` / `_SCHEME` — those redirect *where a credential is sent*, a
hazard class neither predecessor has; the adapter constructs its own base URL and warns if they are
set. Any import from `fetch_do.py` or `fetch_aws.py` (the cross-import anti-pattern named at
`_normalized.py:35-37`) — duplicate the small helpers as both predecessors already do, and note
which. Any invented price, rate or saving; any parsing of a resource id out of an invoice label; any
`rate_basis` field on the inventory resource (§D-L5); any Managed Database, backup, Object Storage,
LKE, Firewall or VPC read.

**Done-check.**
```bash
python3 -m pytest cloudcost/tests/test_fetch_linode.py -v          # offline, no token
CLOUDCOST_LINODE_TOKEN=… python3 cloudcost/scripts/fetch_linode.py --output-dir /tmp/cc-linode
python3 -c "import json;d=json.load(open('/tmp/cc-linode/linode_costs_<covered period>.json'));\
print(round(sum(i['amount'] for i in d['line_items']),2), d['totals']['amount'])"   # must match
```
**The filename is the covered period, not today's month.** Linode publishes no preview
invoice, so a run reads the newest settled invoice and its snapshot is structurally one month
behind (§Seam 7). Read the filename from the adapter's summary rather than constructing it
from the clock — the rev-1 text constructed it, which is what pushed the first implementation
to label `period` with the issue month.

Plus: the token appears in neither stdout nor stderr on success **or** on an auth failure; both
files are schema-valid per §Normalized; every canonical `type`/`state` value is imported from
`_normalized`, not spelled locally (assert with a source guard, the
`test_detect_orphans.py` provider-agnostic-guard precedent); the powered-off fixture settles §D-L4
and the packet states which value was observed; the static-IP finding settles §D-L9 either way;
measured latency is reported in the packet.

**Claude-code prompt.**
> Build `cloudcost/scripts/fetch_linode.py` and its offline pytest suite per
> `cloudcost/m3-milestone.md` §t1. Read both `CLAUDE.md` learning sections, `agent-creation-guide.md`,
> `cloudcost/milestone.md` §Normalized schemas and `cloudcost/docs/m3-linode-scout.md` first.
> Emit the two frozen normalized artifacts, importing every canonical type/state value from
> `scripts/_normalized.py`. Implement §Design decisions D-L1 (post-tax totals with a synthetic Tax
> line that reconciles), D-L2 (USD asserted with its basis), D-L3 (service granularity,
> `resource_id: null`), D-L6 (a class never degrades to an empty list — non-200 becomes an
> `errors[]` entry and the class is marked not-inventoried), D-L10 and D-L11. **Settle D-L4 from a
> recorded fixture taken against a deliberately powered-off Linode — the enum contains both
> `offline` and `stopped`, and `stopped` collides with the canonical value while denoting
> maintenance mode; do not choose by spelling.** Settle D-L9 from a live read of
> `/networking/ips` and report the finding either way. Read live prices from the unauthenticated
> `types` endpoints; never invent a rate, and where no price exists (images) emit `0.0` with a named
> `warnings[]` entry. Do not import from `fetch_do.py` or `fetch_aws.py`. Measure and report the
> adapter's wall-clock latency. Done-check per §t1; include its full output in the packet.

### t2 — Wiring: orchestrator literal, manifest, sprint case, runbook, BL-092

**Scope.** Make `CLOUDCOST_PROVIDER=linode` a first-class selection everywhere it is currently
enumerated, and land the serde guard alongside the new manifest.

**Contract refs.** `cloudcost_orchestrator.exs:42-49` (the provider literal table) and `:93-116`
(the BL-096 timeout rationale); `rig/src-tauri/src/commands/tools.rs:6-46` (the serde structs);
`tests/test_tools_manifests.py`; `cloudcost/runbook.md:17-137` and `:538-580`; methodology §6's
runbook-update rule.

**Touches.** `cloudcost/agents/cloudcost_orchestrator.exs`; `cloudcost/tools.json`;
`cloudcost/tests/test_tools_manifests.py`; `../aetheris/scripts/sprint.sh`;
`cloudcost/runbook.md`; `rig/src-tauri/src/commands/tools.rs` (BL-092's `#[cfg(test)]` module only);
`cloudcost/docs/m3-t2-implementation-notes.md`.

**Do not generate.** A fifth provider arm anywhere. A hand-edit to `docs/capability-matrix.md`
(generated — t3 regenerates it). Any change to `tools.rs` beyond adding the test module — it must
stay byte-identical outside `#[cfg(test)]`. A new `timeout_ms` on any step other than STEP 1.

**Done-check.**
```bash
cd aetheris && CLOUDCOST_PROVIDER=linode mix run --eval \
  'Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")'
CLOUDCOST_PROVIDER=bogus mix run --eval '…'      # must still raise
python3 -m pytest cloudcost/tests/test_tools_manifests.py -v
cd rig/src-tauri && cargo test tools::            # BL-092: every committed manifest round-trips
```
Plus: the run-id slug is `cloudcost-orch-linode-…` and the label is `Cloudcost · Linode`, so
BL-083's `classifyRun` still groups it; **`sprint.sh` gains a fourth arm in the credential
preflight `case`** (`sprint.sh:2378-2397`; without it the `*)` arm at `:2393` kills the run
at its `fail` + `exit 1` on `:2394`); **and the hermetic machinery gains its Linode
analogue, which the fourth arm alone does not provide.**
`CC_HERMETIC` (`sprint.sh:2371-2373`) is AWS-shaped — it unsets `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE` and neutralises the shared-credentials file — so a
Linode run today inherits any `LINODE_CLI_TOKEN` or `LINODE_TOKEN` in the ambient
environment. Add `-u LINODE_CLI_TOKEN -u LINODE_TOKEN` to the array, and extend the
poison-control block (`:2453-2487`) with the Linode arm it already performs for AWS: the
probe must see the poison **without** the prefix, see nothing **through** it, and
`CLOUDCOST_LINODE_TOKEN` must survive the prefix. Without this the hermetic proof passes
while covering a provider it never tested. `cloudcost/runbook.md` gains a `### Linode`
posture subsection, between the `### AWS` subsection and the "credentials gate only the
*live* steps" line that closes §Prerequisites (landed at `:65`),
recording the read-only PAT scope set, the credential file path
(`~/.secrets/linode-cloudcost.env`), **the `set -a` load requirement** — a `KEY=value` file
sourced bare leaves the variables shell-local, so the operator's shell reports them present
while the child preflight reports them unset, with no error in between (`runbook.md:53-63`
records the AWS instance of exactly this, and both the sprint and the orchestrator run as
children) — the token expiry date, the `LINODE_CLI_TOKEN` shadowing note and the
`LINODE_CLI_API_*` endpoint-redirection hazard.
Verify how the cloudcost sprint case locates the report file: a Linode run's artifacts are
named for the **covered** month, so a check that builds `cloudcost_report_$(date +%Y-%m).html`
passes for AWS and DO and fails for Linode on a reason unrelated to the report. Locate it by
glob over what the run actually wrote. **Not** from STEP 1's reported period: that value reaches
the sprint only through the model's closing prose, so parsing it would put a deterministic check
back on model output. Record in the `### Linode` runbook subsection that a
class going `not_inventoried` now makes the run partial and exit 1 — a transient failure on one
resource class stops the pipeline rather than producing a report with a silent hole
(methodology §6: changed observable semantics belong in the runbook of the ticket that changes
them).
The BL-096 confirmation is **recorded** —
`fetch_linode`'s measured duration against the shared `fetch_timeout_ms = 300_000`, per
`runbook.md:553-566` — and the number changes only if the margin is inadequate.

**Claude-code prompt.**
> Wire Linode as the third provider per `cloudcost/m3-milestone.md` §t2. Add the `"linode"` arm to
> the provider literal table in `cloudcost/agents/cloudcost_orchestrator.exs` (name/short/slug/script),
> declare `fetch_linode` plus a masked `CLOUDCOST_LINODE_TOKEN` in `cloudcost/tools.json`, add the
> fourth arm to the credential preflight `case` in `../aetheris/scripts/sprint.sh`, and add the
> `### Linode` posture subsection to `cloudcost/runbook.md` in the same commit (methodology §6's
> runbook-update rule — not deferred). Record, do not re-derive, the BL-096 timeout confirmation from
> t1's measured latency. Land **BL-092** in the same ticket: a `#[cfg(test)]` module in
> `rig/src-tauri/src/commands/tools.rs` round-tripping every committed `tools.json` into
> `ToolsManifest` and asserting Ok plus the env_deps dedup walk — `tools.rs` stays byte-identical
> outside that module. Done-check per §t2; include full output.

### t3 — The run, the click-through gate, and BL-090

**Scope.** The live Linode run, the merge-gate click-through, the matrix regen, and the milestone's
negative proof.

**Contract refs.** This doc's §Done-when; `cloudcost/runbook.md:283-346` (the BL-069 planting
procedure) and `:538-580`; the regen ritual at scout §A9.

**Touches.** `cloudcost/docs/m3-t3-implementation-notes.md`; `docs/.sections/cloudcost.md`
(gitignored, regenerated); `docs/capability-matrix.md` (regenerated); `cloudcost/m3-milestone.md`
(the milestone summary at close).

**Do not generate.** A hand-edit to `docs/capability-matrix.md`. A **full** nine-agent matrix regen
— `docs/.sections/` is gitignored, so a missing section is silently replaced by
`_Section not available._` and the matrix ships partial. Any edit to the four shared scripts.

**Done-check.**
```bash
# 1. plant a zero-backend NodeBalancer first (BL-069) — see §Rule reachability;
#    a same-day volume cannot fire, its rule needs 14 days
CLOUDCOST_PROVIDER=linode ./scripts/sprint.sh cloudcost   # READ [OK]/[FAIL] LINES, NOT $?  (BL-077)
# 2. the negative proof
git diff --stat dc8c077 -- cloudcost/scripts/detect_orphans.py \
  cloudcost/scripts/compose_report_data.py cloudcost/scripts/render_report.py \
  cloudcost/scripts/_normalized.py          # must be empty
# 3. matrix: regenerate the ONE section, then re-assemble from all nine
ls docs/.sections/                                        # confirm nine present first
cd ../aetheris && mix aetheris run ../aetheris-agents/agents/capability_matrix_cloudcost.exs
python3 ../aetheris-agents/scripts/assemble_matrix.py
```
Plus: **the click-through is a merge gate** — from the completed run's detail in Rig, "View report"
opens the Linode HTML; the hand-off to the human names **the branch under test**, and the gate is
only valid if that build holds the change. The report shows ≥1 orphan with its evidence and is
reviewable without the Linode console. BL-090's two stale cells are both reconciled at regen
(`detect_optimization_signals` added; the Label cell now reading `Cloudcost · <provider>`), and the
Summary row updates to **eight** scripts — the seven runnable CLIs plus the
import-only `_normalized.py`, which the section agent collects like any other `.py`
(`agents/capability_matrix_cloudcost.exs:41-45`). Earlier drafts said seven, carried from a
scout count taken at `dc8c077`, before t1 added `fetch_linode.py`.
`CLOUDCOST_LINODE_TOKEN` appears nowhere in `run.json`.

**Claude-code prompt.**
> Run and close m3 per `cloudcost/m3-milestone.md` §t3. Plant a zero-backend NodeBalancer first
> (BL-069 — `cloudcost/runbook.md:283`; a same-day unattached volume cannot fire, since its rule
> requires 14 days of age), then run the sprint case with
> `CLOUDCOST_PROVIDER=linode`. **`sprint.sh`'s `fail` sets no exit status (BL-077) — read the
> `[OK]`/`[FAIL]` lines, never `$?`.** Produce the milestone's **negative proof**: `git diff --stat`
> against `dc8c077` for the four shared scripts must be empty, and that output goes in the packet.
> Regenerate the capability matrix by the §A9 ritual — the cloudcost section agent alone, then
> `assemble_matrix.py` over all nine sections; never a full nine-agent regen, never a hand-edit —
> reconciling both stale cells (**BL-090**). Then hand the human a click-through: "View report" from
> the run detail in Rig, **naming the branch under test** — this is a merge gate, not an owed
> residual. Done-check per §t3; include full output.

---

## Sequencing

t1 → t2 → t3, strictly linear: t2's timeout confirmation consumes t1's measurement, and t3's run
consumes both. BL-092 rides t2 (it lands with the manifest it guards); BL-090 rides t3 (the matrix
counts scripts on disk, so it regenerates after `fetch_linode.py` exists).

## Open items carried forward

- **DO's `totals.amount` tax treatment is undetermined** (`fetch_do.py:306` reads one scalar; the
  fixture's `taxes.amount == 0.00` cannot discriminate). Until settled, only AWS and Linode are
  known-comparable. File it; do not assume it.
- **`rate_basis` as a uniform §Normalized companion to `monthly_cost_estimate`**, retro-fitted to all
  three adapters at once (§D-L5). Linode's unauthenticated price endpoints make it cheap; doing it
  here would confound the proof.
- **The provider-prefix convention is two conventions.** Adapter output prefixes are hand-written
  literals (`do_`, `aws_`); orphan and history prefixes are `provider_slug(provider)` — they already
  disagree in the shipped DO tree (`do_costs_…` beside `digitalocean_orphan_candidates_…`). Linode
  masks the divergence by coincidence (`provider_slug("linode") == "linode"`), which is exactly how
  it survives another milestone. Recorded here so it is not rediscovered at provider four.
- **Rate limits are undocumented in the spec** and were not read off the external page. The sweep's
  request profile (1 + N NodeBalancer configs) is small, but this is an absence of information, not
  an absence of limits.
- **BL-074's remaining sweep** (age thresholds, `KEEP_TAG` spelling, `EPHEMERAL_NAME_PATTERN`,
  `TAGGED_ACCOUNT_COVERAGE_THRESHOLD`) is untouched here. Linode confirms the `KEEP_TAG` finding —
  flat string tags, so `k=v` remains an adapter convention wearing a shared constant's clothes.
- **Two stale strings in `cloudcost/scripts/fetch_linode.py`**, both outside any m3 ticket's
  Touches: the `--period` help at `:1291` still says "default: current UTC month", which is
  the billing-failed fallback rather than the real default (the newest settled invoice's
  covered month); and `:1386` cites `runbook.md:420-428`, shifted by t2 to `:553-566`. Fix
  both the next time someone is legitimately in that file — trigger, not calendar, per the
  BL-078 precedent.

---

## Milestone summary (methodology §7)

Written at t3 close from the three tickets' implementation notes, not from the diffs.

### What shipped

**The bet, proved a third time.** A new provider was a new adapter plus its fixtures plus its own
run. `detect_orphans.py`, `compose_report_data.py`, `render_report.py` and `_normalized.py` are
**byte-identical to `dc8c077`** at close, and the shared engine produced a real candidate from
Linode-shaped input on the live run. No §Normalized extension was needed: every in-scope class
mapped onto an existing canonical type. Linode was the smaller adapter, so this was the faster
proof — and it generalises past AWS, which was the point.

- **t1** — `fetch_linode.py`, recorded fixtures, offline suite (no token). Three review rounds,
  merged `cb3ca63`. Three evidence-gated findings settled by live read rather than by design:
  the state mapping is `offline` (§D-L4); the static-IP rule *is* reachable, via a `reserved`
  flag the OpenAPI spec does not declare (§D-L9); the volume rate is per-GB.
- **t2** — orchestrator provider literal and credential raise, `tools.json`, the sprint case,
  the runbook posture, BL-092's serde guard over every committed manifest. Merged `f552094`.
  Zero blocking findings.
- **t3** — the live run (`cloudcost-orch-linode-h5lltQ`, 18 `[OK]` / 0 `[FAIL]`), the negative
  proof, BL-090's regen, the PAT expiry, the click-through gate.

**Done-when, at close:** 1 positive run with ≥1 orphan and its evidence trail ✓ · 2 negative proof
empty, mutation-checked ✓ · 3 offline suite green, 351 tests, no token ✓ · 4 click-through gate ✓ ·
5 BL-090 both cells reconciled, BL-092 landed over every manifest ✓ · 6 §D-L1 tax, §D-L2 currency
and the timeout margin all recorded ✓ · 7 credential absent from stdout, stderr and trajectory,
verified with a control ✓ · 8 six excluded classes each recorded as an exclusion with its reason ✓.

### What was deferred, with refs

- **`rate_basis` as a uniform §Normalized companion** (§D-L5, §Open items) — retro-fit to all three
  adapters at once, not here, where it would confound the proof.
- **BL-098** — persisting `not_inventoried` onto an artifact; a §D-C doc-first extension (t1 §5).
- **BL-074's remaining sweep** — age thresholds, `KEEP_TAG` spelling, `EPHEMERAL_NAME_PATTERN`,
  `TAGGED_ACCOUNT_COVERAGE_THRESHOLD`. Linode confirmed the `KEEP_TAG` finding.
- **BL-070** — retire the now-unreachable cross-provider merge code in `compose_report_data.py`.
- **Two stale `fetch_linode.py` strings** (`:1291`, `:1386`) — §Open items, BL-078 trigger shape.
- **The sprint's D2 credential grep is AWS-only** (t3 §3.3) — done-when 7 was met by a hand-run arm
  with its own anti-vacuity control, because no sprint assertion covers it on the Linode leg.
- **`run.json` is unparseable by `jq`** — `2>&1` prepends harness boot output, so the sprint's
  status line reads `no-json` on every provider (t3 §4). Display only; the assertion is the exit
  status.

### Surprises

- **The spec was wrong in the direction that mattered.** §D-L9's rule was written as probably
  unreachable; the live API returns an undeclared `reserved` flag that makes it reachable. Had the
  spec been complete, a same-day plant would have had exactly one option instead of two — and the
  one it would have forced (a reserved IP) prices at `0.00`, which is a weak proof for a cost
  report. The milestone's best evidence exists because a scouted document was incomplete.
- **`period` means the *covered* month, and Linode is structurally a month behind.** No preview
  invoice exists (§Seam 7). This was a t1 **blocking** finding on a first-class contract field, and
  it propagated: the sprint had been locating the report by `date -u +%Y-%m`, right for two
  providers and wrong for the third. t1 found it by reading the file; t2 replaced construction with
  discovery; t3's run confirmed it in production (invoice `#32251471`, issued 2026-08-01, covering
  July, read on 2026-08-05, artifacts named `2026-07`).
- **An environment variable has no retraction channel.** `LINODE_BILLING` had **three** carriers —
  `~/.profile`, the systemd user manager's imported block, and a `gnome-terminal-server` process
  that had snapshotted it at launch. A file edit cannot reach an imported copy;
  `unset-environment` cannot reach a process that already forked. The check that would have
  declared it clean (`env -i bash -lc`) tested init files only. "Where does this value live" is an
  observation, not a census.
- **The wiring is five places, not one.** §"Adding a provider" had said "plus a clause in the
  orchestrator's provider `case`". t2 found the other four one at a time and enumerated them in the
  runbook — the first prospective application of enumerate-the-class in this milestone rather than
  a retrospective one.
- **`main` was red for a suite no ticket's done-check ran.** t1 added the seventh cloudcost CLI;
  declaring it was t2's. Two tests in the repo-root `tests/` suite failed at `main` for a day. The
  suite asserts *about* a use case from outside its directory, so it belonged in the done-check of
  the ticket that changed the script inventory, not only the one that edited the manifest.
- **The plant was the milestone's one hard dependency on a human, and it was absent at t3.** The
  first live read found zero zero-backend NodeBalancers. Stopping there — rather than running the
  sprint and reading the answer off a `[FAIL]` — is what kept the `≥1` assertion meaningful.

### Open items for the next milestone

- **BL-069 is still armed.** t3 discharged the Linode leg only, and only while the plant lives; the
  plant is deleted after the run. The DO reserved IP was deleted 2026-07-30 and the AWS Elastic IP
  (`m2-milestone.md` §Prereqs 3) is still pending. What t3 proves is that the assertion *can* go
  green on real account state with a real dollar figure through an unchanged engine.
- **DO's `totals.amount` tax treatment is undetermined** (`fetch_do.py:306`). Only AWS and Linode
  are known-comparable. File it; do not assume it.
- **The provider-prefix convention is two conventions**, and Linode masks the divergence by
  coincidence (`provider_slug("linode") == "linode"`). Provider four is where it stops being masked.
- **Rate limits are undocumented** in the spec and were not read off the rendered page. An absence
  of information, not an absence of limits.
- **Before provider four:** read BL-074 and BL-070, and read §"Adding a provider"'s five-place
  enumeration instead of rediscovering it.

### Not part of this milestone's close

The **project-knowledge export boundary** (manifest regen, remove-all-upload-all) and the **§7
learning promotions** both follow the merge. The promotions come from the reviewer's scan of the
three review files plus this summary — §7 step 1 is explicit that review files are not the only
input, and at least two classes here (the `main`-red suite, the environment-carrier census) were
found by work rather than by a reviewer.
