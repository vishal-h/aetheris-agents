# m3-cloudcost — Linode as provider three (report-only)

**Status:** **RATIFIED 2026-08-04** — approved by the human and committed per
`milestone-methodology.md` §4 (rev 3). Not started; t1 next.
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
   covering three manifests.
6. The tax ruling (§D-L1), the currency basis (§D-L2) and the fetch-timeout margin
   confirmation (`cloudcost/runbook.md:420-428`) are each recorded in the repo.
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
3. **A plantable orphan.** An **unattached Block Storage volume** is the cheapest and the most
   certainly-detectable choice — see §Rule reachability. Plant it before t3's run (BL-069) or the
   ≥1-orphan assertion is expected-red.

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
| `rule_unassociated_static_ip` | **Unestablished** | §D-L9 — settled by live read at t1, or recorded as not-reachable |
| `rule_stopped_database_with_storage` | **No** | §D-L7 — class excluded |

**Consequence for the plant (BL-069):** an unattached volume is the only candidate that is both
certainly reachable and cheap to create. Plant that, not a static IP — the DO milestone's headline
orphan type is the one Linode may not be able to express.

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
python3 -c "import json;d=json.load(open('/tmp/cc-linode/linode_costs_$(date -u +%Y-%m).json'));\
print(round(sum(i['amount'] for i in d['line_items']),2), d['totals']['amount'])"   # must match
```
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
`tests/test_tools_manifests.py`; `cloudcost/runbook.md:15-63` and `:414-437`; methodology §6's
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
subsection inserted at `:62` (before the "credentials gate only the live steps" line),
recording the read-only PAT scope set, the credential file path
(`~/.secrets/linode-cloudcost.env`), **the `set -a` load requirement** — a `KEY=value` file
sourced bare leaves the variables shell-local, so the operator's shell reports them present
while the child preflight reports them unset, with no error in between (`runbook.md:51-61`
records the AWS instance of exactly this, and both the sprint and the orchestrator run as
children) — the token expiry date, the `LINODE_CLI_TOKEN` shadowing note and the
`LINODE_CLI_API_*` endpoint-redirection hazard; the BL-096 confirmation is **recorded** —
`fetch_linode`'s measured duration against the shared `fetch_timeout_ms = 300_000`, per
`runbook.md:420-428` — and the number changes only if the margin is inadequate.

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

**Contract refs.** This doc's §Done-when; `cloudcost/runbook.md:197-232` (the BL-069 planting
procedure) and `:414-437`; the regen ritual at scout §A9.

**Touches.** `cloudcost/docs/m3-t3-implementation-notes.md`; `docs/.sections/cloudcost.md`
(gitignored, regenerated); `docs/capability-matrix.md` (regenerated); `cloudcost/m3-milestone.md`
(the milestone summary at close).

**Do not generate.** A hand-edit to `docs/capability-matrix.md`. A **full** nine-agent matrix regen
— `docs/.sections/` is gitignored, so a missing section is silently replaced by
`_Section not available._` and the matrix ships partial. Any edit to the four shared scripts.

**Done-check.**
```bash
# 1. plant an unattached volume first (BL-069) — see §Rule reachability
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
Summary row updates to seven scripts. `CLOUDCOST_LINODE_TOKEN` appears nowhere in `run.json`.

**Claude-code prompt.**
> Run and close m3 per `cloudcost/m3-milestone.md` §t3. Plant an unattached Block Storage volume
> first (BL-069 — `cloudcost/runbook.md:197`), then run the sprint case with
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
