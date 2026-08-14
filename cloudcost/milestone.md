# m1-cloudcost — DigitalOcean cost report + orphan detection (report-only)

**Status:** **CLOSED 2026-07-29** — t1–t5 all landed and reviewed (t5: agents `6abc3e8`
+ `013c09d`, harness `ba49d06` + `4147b9d`). Done-when met on the real DO bill: the
pipeline ran end-to-end via `cloudcost_orchestrator.exs` (`cloudcost-orch-qPCKmw`,
re-proven at `cloudcost-orch-mhmohw`) and produced a local HTML report carrying **1 real
orphan** — an unassociated reserved IP, HIGH confidence 0.95, ~$4.38/mo — with its evidence
trail, reviewable without the DO console. The planted orphan has since been deleted and the
account is back to clean read-only. §7 promotion pass folded into `../aetheris/CLAUDE.md`
(`57d90d2`). Carried forward: **BL-067** (capability-matrix assembler derives its whole
Step-2 block in the LLM). First milestone of the cloudcost use case; DO-only vertical slice.
**Origin:** uc-cloudcost proposal (2026-07-26) + claude-ui review + Phase-1 iteration.
**Repo:** `aetheris-agents/cloudcost/` (new use case). Runs in its own session, parallel
to the harness backlog.

> **Superseded 2026-08-06 (m4 t2) — the plant instruction only.** §Prerequisites 2 (*"Confirm one
> exists, or plant one, before t5's end-to-end run"*) is retired, along with every other
> instruction in this document to create a cloud resource so the `≥1`-orphan assertion fires.
> **Decision 12** (`m4-consolidation.md` §Ratified decisions → Technical) rules out planted cloud
> resources on every provider, and **BL-069 closed by retiring the practice** rather than by
> swapping in another fixture. In its place the cloudcost sprint case asserts **rule legibility** —
> that the adapter's inventory reached the rule catalog in a shape the catalog could read, with the
> canonical `type` vocabulary imported from `scripts/_normalized.py` rather than restated. The live
> description is `runbook.md` §"What a zero-orphan account means, and what the sprint asserts
> instead"; that section, not this one, is where an operator should now look.
>
> What is superseded is the **instruction**. This milestone's record — that a reserved IP was
> planted, that it carried the end-to-end proof, and that it was deleted afterwards — is history
> and stands as written below, unedited.

---

## Goal

Prove the full cloudcost pipeline end-to-end on **DigitalOcean** — fetch → normalize →
detect orphans → compose → report → deliver — on the real DO bill, **read-only**, and
establish the adapter contract (normalized schemas) so later providers are near-mechanical
adds.

## Done-when (milestone)

- The pipeline runs end-to-end via `cloudcost_orchestrator.exs` against the real DO account
  (read-only) and produces a **report (PDF/HTML, local file)**.
- The report is reviewable **without opening the DO console**: totals by service, tag
  coverage + top untagged spenders, MoM delta (from month two), and an **orphan-candidates
  section** with per-candidate `evidence[]` and `monthly_saving_estimate`.
- **≥1 real orphan** surfaced on the actual account with its evidence trail (unattached
  volume / unassociated reserved IP / aged snapshot are the likely DO hits).
- All scripts standalone-runnable and pytest-covered against **recorded DO fixtures**
  (offline, no token needed); sprint case green.

*(The two-billing-cycle before/after evidence is the mainstream-candidacy gate — it accrues
over time and is not a coding blocker. The milestone completes on the first correct
end-to-end run.)*

## NOT in scope (this milestone)

- Any provider but DO (AWS/GCP/Workspace/Linode/GitHub are later milestones; the schema
  absorbs them).
- Any **write** credential or cleanup execution (the P3 cleanup milestone, gated).
- The review/approve queue (the P2 milestone).
- Email/Drive delivery (m1 delivers to a **local file**; productionized delivery is later).
- Automated scheduling (the first evidence runs are manual; scheduling is a later small
  ticket).
- GCP BigQuery, currency conversion, and a SQLite/DuckDB trend store — deferred per the
  brief (flat-file history + original-currency for now).
- The DO **MCP** server — see D6.

---

## Prerequisites (human-owned — provide before the loop reaches its live steps)

The build runs mostly on offline fixtures, but three things are the human's to supply, and
t1 needs the first before it can record real fixtures — so treat the token as effectively a
**t1-start dependency**, not a late one.

1. **Read-only DO API token → `CLOUDCOST_DO_TOKEN`.** A **full-account Read-Only PAT is
   sufficient** — DO's "list and retrieve information about all resources" read scope covers
   both the inventory GETs and the billing GETs (balance/invoices/history; confirmed by DO's
   own read-only billing MCP tools `balance-get`/`billing-history-list`/`invoice-list`), so
   there is no need to fine-grain it to billing. Read-only is the security property that
   matters, and it trivially satisfies **D2**: a token that cannot write has nothing to
   separate at P1: the read/write split becomes real only at P3. Export it in the harness
   process environment *before* `mix aetheris run`. The reporting run's environment must hold
   `CLOUDCOST_DO_TOKEN` and **no other DO token** — not only for **D2**'s write-exclusion, but
   because `pydo`/`doctl` default to reading `DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN`, so a
   stray write token left in the environment can silently shadow the read-only one and do the
   run. If `~/.profile` (or `~/.bashrc`, `~/.zshrc`, `/etc/profile`, …) exports any other DO
   token, relocate it out of the harness login shell (e.g. a `~/.secrets/` file sourced only
   where that token is used) and confirm in a fresh shell before the run:
   `[ -z "$DO_TOKEN" ] && [ -z "$DIGITALOCEAN_ACCESS_TOKEN" ] && [ -n "$CLOUDCOST_DO_TOKEN" ]`.
   Gates: t1 (recording real fixtures + the live `--output` done-check)
   and t5 (the end-to-end run). The offline unit tests (t1–t4) do **not** need it — so
   structural work can start before the token lands, but t1 can't *complete* (real fixtures)
   without it.

2. **A real DO account carrying a genuine orphan.** The ≥1-orphan done-when needs the account
   to actually contain one — an unattached volume / unassociated reserved IP / aged snapshot.
   Confirm one exists, or plant one, before t5's end-to-end run.

3. **Environment tooling.** `pydo` (or `requests`) installed; and, if t4 renders PDF via the
   Docbuilder path, `wkhtmltopdf`/`pandoc` present (rendering HTML instead avoids that system
   dep). `mix aetheris doctor` should read ✅/⚠ (not ❌) for what's required.

**Not needed for m1** (deferred): any DO *write* token, and email/Drive credentials —
delivery is a local file.

---

## Design decisions

**D1 — Record-and-deliver, NOT a verify-target.** Fetches run through `run_command`
(python3 → DO REST), which the harness classifies **`:contained`**; verify *re-executes*
contained tools (under BL-042's netns), so a recorded cloudcost run cannot be cleanly
verified — the fetch re-executes and either fails (no network under the netns) or re-fetches
live and diverges on changed billing data. Cloudcost trajectories are therefore **not
verify-targets**: record-and-deliver only, and the adapters' `--output` JSON files (captured
in record mode) are the run's evidence. The build session must not add or claim verify
support. *(This corrects the proposal's `:uncontained`/record-and-serve framing, which was
inaccurate for the `run_command` path.)*

**D2 — Credential separation is operational, not config-enforced.** Trivial here (one
read-only `CLOUDCOST_DO_TOKEN`), but the pattern is set: read and write tokens live in
disjoint process environments; the reporting run's environment never holds a write token
(this becomes load-bearing at P3). The token is passed via env only — never in `config_json`,
never echoed to stdout/stderr (the trajectory captures both). Set `store_prompts: false` if
provider context is ever sensitive.

**D3 — Scripts do, agents decide.** All DO API calls, pagination, retry, cost math, orphan
heuristics, and confidence scoring live in pytest-covered Python. The orchestrator LLM only
sequences the script calls, routes exceptions, and composes narrative. No cost figure or
orphan selection is ever the LLM's.

**D4 — Honest granularity.** DO's Billing API is invoice/service-level, so cost line items
carry `source_granularity: "service"` and `resource_id: null` — the report renders
service-level cost and never fabricates resource attribution DO's API doesn't give. Per-
resource dollars live as `monthly_cost_estimate` on the **inventory** side (derived from
size/type), which feeds the orphan `monthly_saving_estimate`. Actual-at-service-level,
estimated-at-resource-level.

**D5 — Shared machinery is provider-agnostic; only the adapter is DO-specific.**
`detect_orphans.py` and `compose_report_data.py` operate on the normalized schema (tested on
DO fixtures), so fan-out is a new adapter + fixtures with nothing downstream changing. The
m1 orchestrator is a **linear `run_command` pipeline** (one provider); fan-out to
`spawn_agent × N + wait_for_all` is a later change, noted not built (single-provider
`spawn_agent` is the OrbConfig-overkill the guide warns against).

**D6 — DO integration is REST, not the DO MCP.** DO's REST API has a dedicated Billing API
(balance/invoices/history) and list endpoints for droplets/volumes/reserved-IPs/snapshots/
load-balancers — everything the read-only reporter needs. The DO **MCP** server *also*
exposes read-only billing tools (`balance-get`, `billing-history-list`, `invoice-list`,
`account-get-information`) and likely the inventory reads, so tool *coverage* is not the
deciding factor. REST wins for m1 on **fit**: the MCP returns raw DO shapes, so normalization
to the schema still needs a script — or, worse, the LLM, breaking D3; the fetch is a fixed,
paginated, multi-resource sweep a deterministic script does in one pass, where MCP is many
LLM tool-call round-trips; and only the script path is offline-pytest-testable against
recorded fixtures, which is the testing strategy the whole milestone rests on and the adapter
contract m1 exists to prove. The MCP's genuine upside is *less plumbing* (DO maintains the
surface, auth, pagination); against it, the MCP tool set also carries **write** tools
(`key-create`/`key-delete`) — a broader capability surface than a read-only reporter wants,
where a scoped read-only DO token calling only `list`/`get` is tighter. REST via DO's
official Python client (`pydo`) or `requests` is the integration. *(If MCP is ever
reconsidered at fan-out: it's `:uncontained`/record-and-served — which would make the
proposal's original determinism framing correct — but D1's not-a-verify-target conclusion
holds either way, so it changes nothing m1 needs.)*

---

## Normalized schemas (the adapter contract — this is what m1 proves)

Two JSON shapes every adapter emits and every downstream script consumes — the contract the
milestone exists to freeze; t1 emits *these exact shapes*. Later providers re-emit them, which
is what makes fan-out mechanical. Every **first-class** (top-level) field is part of the
cross-provider contract: a later adapter emits it with a real value, or `null`/`[]`/`{}` where
its provider lacks the concept — never by omission. Provider-specific payload lives under
`provider_extra`, which downstream scripts must **not** key on generically.

**Cost snapshot** — `do_costs_{YYYY-MM}.json`:

```json
{
  "provider": "digitalocean",
  "account": "<account id / email>",
  "period": "2026-07",
  "currency": "USD",
  "source_granularity": "service",
  "line_items": [
    { "service": "Droplets", "resource_id": null, "region": null, "amount": 42.00,
      "usage_qty": null, "usage_unit": null, "tags": [] }
  ],
  "totals": { "amount": 42.00 },
  "balance": {
    "month_to_date_balance": 42.00, "account_balance": 0.00,
    "month_to_date_usage": 42.00, "generated_at": "2026-07-27T04:41:53Z"
  },
  "generated_at": "2026-07-27T04:41:53Z",
  "provider_extra": {
    "invoice": { "invoice_uuid": "…", "invoice_id": "…", "status": "preview" },
    "billing_history": [
      { "date": "2026-07-01T06:22:06Z", "type": "Invoice", "description": "Invoice for June 2026",
        "amount": 186.22, "invoice_uuid": "…" }
    ]
  }
}
```

- **First class** (cross-provider; downstream may key on these): `provider`, `account`,
  `period`, `currency`, `source_granularity`, `line_items`, `totals`, `balance`,
  `generated_at`.
- `source_granularity` is `"service"` for DO (invoice/service-level billing), so `resource_id`
  is `null` on every cost line — the report never fabricates resource-level cost attribution
  DO's API doesn't give (**D4**). `region`/`usage_qty`/`usage_unit` are populated only when the
  provider's billing surfaces them; DO leaves them `null`. Repeated service rows on one invoice
  aggregate to one line per service, preserving `totals.amount`.
- `totals.amount` is the period total in `currency` (no conversion — original currency).
  `balance` is the account-level month-to-date position (cross-provider concept).
  `generated_at` is the fetch timestamp (UTC).
- **`provider_extra`** holds the DO-shaped billing provenance — `invoice` (period invoice
  identity + status; `preview` for the live current month) and `billing_history` (the
  chronological invoice/payment ledger that seeds MoM context at t3; amounts signed, payments
  negative). Downstream scripts read cross-provider fields from the top level and treat
  `provider_extra` as opaque unless they are provider-aware.

**Resource inventory** — `do_inventory_{YYYY-MM}.json`:

```json
{
  "provider": "digitalocean",
  "account": "<account id / email>",
  "period": "2026-07",
  "resources": [
    { "resource_id": "vol-123", "type": "volume", "name": "detached-data-vol",
      "region": "blr1", "size": "100GiB", "state": "available",
      "created_at": "2026-05-01T00:00:00Z", "last_activity_at": null, "attached_to": null,
      "monthly_cost_estimate": 10.00, "tags": [], "raw_ref": "do://volumes/vol-123" }
  ],
  "generated_at": "2026-07-27T04:41:53Z"
}
```

- Every resource carries, first class: `resource_id`, `type`, `name`, `region`, `size`,
  `state`, `created_at`, `last_activity_at`, `attached_to`, `monthly_cost_estimate`, `tags`,
  `raw_ref`.
- **`type` — the canonical vocabulary (schema-level, closed set).** *Amendment-to-complete,
  m2 t2 a′: m1 froze the field but never enumerated its allowed values, so the DO adapter's
  `droplet` / `reserved_ip` were provider vocabulary that `detect_orphans.py`'s rules keyed
  on — the second seam (BL-074), beside `STOPPED_STATES`. These values are part of the
  contract, not of any provider: every adapter emits from this set and nothing else, and the
  shared machinery keys on these values. They are defined once in `scripts/_normalized.py`
  (`TYPE_*`, `CANONICAL_TYPES`) and imported by every adapter.*

  | Canonical `type` | DigitalOcean emits for | AWS emits for |
  |---|---|---|
  | `compute_instance` | droplet | EC2 instance |
  | `volume` | volume | EBS volume |
  | `static_ip` | reserved IP | Elastic IP |
  | `snapshot` | snapshot | EBS snapshot |
  | `load_balancer` | load balancer | ELB / ALB / NLB |
  | `database` | — | RDS instance |
  | `database_snapshot` | — | RDS manual snapshot |
  | `seat` | — | — |

  `seat` is **GitHub's**, added at m6 t1 and emitted by nothing yet. It is named in prose
  rather than given a column because this table's columns are not sparse — every row carries
  a cell in each, and `—` means *this provider emits nothing for this type* — so a GitHub
  column would assert what GitHub emits for every infrastructure row above, which is outside
  the ticket that added the row. **A Linode column is absent for the same reason** and is
  not added here: it would require the same assertion per row for Linode. Linode's one
  recorded mapping lives in prose in §Contracts C1 instead.

  A provider lacking a concept simply emits no resource of that type; a provider with a
  concept the set does not name needs the set extended here first, never a local spelling.
  The provider's own name for the thing survives in `raw_ref` (`do://droplets/…`), which is
  provenance rather than vocabulary.
- **`state` — the canonical value for stopped compute is `"stopped"`** (`STATE_STOPPED`,
  same module; m2 t2 a). Each adapter maps its own idiom onto it — DO's `off`, EC2's and
  RDS's `stopped` — and `detect_orphans.STOPPED_STATES` is that one value. Other states have
  no canonical spelling yet and pass through as the provider reports them; the moment a rule
  needs one, it is enumerated here first.
- `monthly_cost_estimate` is the per-resource dollar figure — the provider's own price where
  given (DO droplets carry a real `price_monthly`), else derived from size/type (**D4**); it
  feeds the orphan `monthly_saving_estimate`.
- `attached_to` is `null` for an unattached/unassociated resource (the primary orphan signal).
  For a load balancer that targets backends **by tag**, `attached_to` is `"tag:<name>"` — a
  tag-targeted LB has backends and must not read as unattached (**B2**). A snapshot's
  `attached_to` is the source it was taken from; `null` there means the source is gone (the
  aged-orphan case).
- `name`, `region`, `size` are the human-facing identity fields — the orphan section shows
  these so the report is reviewable without opening the DO console; a provider lacking one
  emits `null`.
- `raw_ref` (`do://…`) is the evidence-trail pointer back to the source object.
- `state`, `created_at`, `attached_to`, `last_activity_at`, `tags` are the fields the t2
  heuristics key on — all provider-normalized, so `detect_orphans.py` never touches a DO shape.
  `last_activity_at` is `null` for every DO resource type (DO exposes no such field), so t2 age
  rules key on `created_at`, never `last_activity_at`.

**Orphan-heuristic catalog** — enumerated inline in **§t2 Scope**; that list is the
authoritative catalog for m1 (no external doc).

---

## Contracts (C1–C15 — what shared machinery guarantees, and what an adapter must guarantee)

> **Established at m4 t4b, 2026-08-07, from the t4a seam census**
> (`cloudcost/docs/m4-t4a-implementation-notes.md`, 54 items in groups X/N/D/F/P/R). §Normalized
> schemas above states the *shapes*; this section states the *contract over their values* — the
> thing BL-074 found was large, real and almost entirely undocumented.
>
> **Every one of the census's 54 items is cited below by id, in exactly one contract.** An item id
> is the stable reference; line numbers are not, and are omitted deliberately.
>
> **The ruling test**, applied to each item's Consumers field: *a value is schema-level if shared
> machinery may key a decision on it; adapter-owned if shared machinery may only carry it.* To
> **key** is to test in a predicate, select in a branch, match in a join, derive a filename or
> persisted path from, or make a section appear or not appear. To **carry** is to copy into the
> payload, interpolate into evidence text, or render — with nothing branching.
>
> The result is lopsided — **48 schema-level, 4 adapter-owned, 2 neither** — and that is the
> finding, not a failure of the test. These four scripts *are* the shared machinery; almost nothing
> in them should move to an adapter.
>
> **A schema-level ruling is not a promise to change code.** Most of what follows is a statement of
> what was already true and undocumented. Where a code change genuinely follows, it is marked
> **[code consequence]** and is owed a backlog row by m4 t4c — it is not taken here.

### C1 — Resource type vocabulary  *(N1, N8, D11)*

**Shared machinery guarantees** that `type` is drawn from a closed set, enumerated once in
`_normalized.py` as `CANONICAL_TYPES` and in §Normalized schemas in prose. An out-of-vocabulary
`type` is a **contract violation, not a pass-through**. The set spans two provider classes —
infrastructure resources, where a type names a provisioned thing, and consumption resources,
where a type names an assigned entitlement — and it is extended across both rather than split
into a per-class vocabulary (m6 t1).

**An adapter must guarantee** that every resource it emits carries a `type` from that set, and must
import the value rather than spell it locally. An adapter that declares its own vocabulary re-opens
seam #1; an adapter importing from a *sibling adapter* is the cross-import anti-pattern.

**The set has a declared public surface.** Today adapters import the `TYPE_*` constants
individually and never the set, so `CANONICAL_TYPES` is used without being declared as API (N1).
**A cross-repo consumer imports it by name**: `../aetheris/scripts/sprint.sh` reads
`CANONICAL_TYPES` from this module in its rule-legibility assertion, deliberately, so the vocabulary
is never restated in shell. Relocating or renaming it breaks the sprint — loudly, which is the
intended posture — and any change to this contract is therefore a **cross-repo** change.

**Today the guarantee is unenforced.** `usable_resources()` validates that `type` is *present*,
never that it is *canonical* (N8), so an out-of-vocabulary type is counted in `totals.resources`
and in the tag-coverage denominator and is evaluated by nothing. **[code consequence]** — and it
**collides with the sprint's rule-legibility arm**, whose `illegible` branch exists precisely
because this validation is absent. The row must be sequenced with a sprint change; taken alone it
changes what the sprint's third arm means without touching the sprint.

**Positive example, recorded as the shape to copy**: Linode maps its images onto `TYPE_SNAPSHOT` in
its own adapter, not in the rule engine (D11). That is a mapping decision made in the right place.

**Reachability (BL-132, 2026-08-11) — guarantee reachable, the gap clause source-only.** Every
orchestrator run composes from adapter output and all three adapters import the `TYPE_*`
constants, so the closed-set guarantee is exercised by every invocation that types a resource.
`[Corrected 2026-08-11 at the exercise sweep, one commit after landing at a690014, where it read
"exercised on every invocation". Of the five chains this census ran, the AWS one consumed a
recorded inventory of **zero** resources and therefore typed nothing, so universality over
invocations is not what the runs showed. The source half is unchanged and was verified: all three
adapters import from `_normalized` and reference the `TYPE_*` constants. **The verdict is
unchanged — reachable**; this narrows a claim about exercise, not about reachability.]` The unenforced-validation
clause is **source-only**: an out-of-vocabulary `type` counted in `totals.resources` and evaluated
by nothing requires an adapter that spells its own vocabulary, and none does. **Kept, qualified
here** — the clause describes a real hole in `usable_resources`, reachable the moment a fourth
adapter declares a type locally, which is the obligation C1's adapter arm already states.

### C2 — Resource state vocabulary  *(X1, N2, D10)*

**Shared machinery guarantees** exactly one canonical state value today — `STATE_STOPPED` — and
keys exactly one decision on it, via `STOPPED_STATES` in the two stopped rules.

**An adapter must guarantee** that a stopped compute or database resource maps onto that value.
All three do: DigitalOcean's `off`, AWS's `stopped`, Linode's `offline` via its own
`POWERED_OFF_STATUS`. That is seam #1, closed at m2 t2 a, and it is **confirmed here, not
re-opened** (N2).

**Every other state value is provider vocabulary, and it reaches the rendered report verbatim**
(X1). The schema defines no canonical value for running, available, attached, associated or
in-use; the adapters pass roughly fifteen raw strings straight through, and `detect_orphans`
interpolates the value into evidence text which the renderer then displays. This is the largest
undocumented surface the census found.

**No rule may key on a non-stopped state until the set is enumerated.** Enumerating it is a schema
extension and belongs with the provider that needs it (BL-098 remains filed); until then, a rule
written against `state == "available"` would be keying on one provider's spelling inside shared
machinery, which is the defect this whole contract exists to prevent.

**A caution for anyone editing this**: a test asserts the **source text** of the predicate
`resource.get("state") not in STOPPED_STATES`, so renaming that constant breaks a test that reads
source rather than behaviour (D10). The test is doing its job; the surprise is only that the
breakage will not look like a behaviour change.

**Reachability (BL-132, 2026-08-11) — the `STOPPED_STATES` guarantee reachable; X1's clause
source-only, and the route it names does not carry.** X1 says the other ~fifteen raw strings
*"reach the rendered report verbatim"* via `detect_orphans` interpolating them into evidence text.
At HEAD there are exactly two interpolation sites, and **each is gated on
`resource.get("state") not in STOPPED_STATES` returning false**, so the only value that can reach
evidence text is the canonical one. No other route exists: the composed payload carries **no
`state` field at all** — `top_untagged_spenders` does not carry it and the template never reads it.
Measured over three chains of the orchestrator's own STEP 3 forms across recorded DO and Linode
artifacts — DO at both arg forms and Linode at the first: **zero** `"state"` across **all three
composed payloads and all three rendered reports**, against a control of **18** in the DO inventory
those chains consumed. `[Corrected 2026-08-11 at the exercise sweep. As landed at a690014 this read
"zero in either payload and either rendered report" — "either" is two, which contradicted the same
sentence's "three runs" and was the honest count of what had been measured: form B's payload and
report were not in that check. The sweep measured all six artifacts and every one is zero, so the
claim is now stated over what was actually measured and is stronger, not weaker. **The verdict is
unchanged.**]` The raw strings are real and reach the *inventory
artifact*; they stop there. **Qualified, not superseded** — the vocabulary gap X1 names is real and
the prohibition it grounds (*no rule may key on a non-stopped state until the set is enumerated*)
is unaffected; what does not hold is the claim that a reader meets those strings in the report.

### C3 — Timestamps and age  *(N3, N4, D12, D17, D20)*

**Shared machinery guarantees** that age is computed as **float days** (`/ 86400.0`) and compared
**strictly greater** — a rule fires on age *greater than* its threshold, so a resource at exactly
the threshold does not fire (D12). It guarantees that emitted timestamps use a
**second-precision UTC** grammar, `%Y-%m-%dT%H:%M:%SZ` for instants and `%Y-%m-%d` for days (N4);
sub-second precision is truncated, not rounded.

**An adapter must guarantee** ISO-8601 **with offset** for `created_at`, `last_activity_at` and
`generated_at`. A **naive timestamp is rejected**, not assumed UTC — the current code silently
assumes UTC for a naive stamp (N3), which on a provider emitting local time produces age errors of
up to a day in the direction that *suppresses* rule firings: a silent wrong answer, not a parse
failure. **[code consequence]**

**`generated_at` is required.** `resolve_reference_date` falls back to the wall clock when it is
absent (D17), which is the one place an otherwise-deterministic module is not: `detect()` documents
itself as producing byte-identical output for the same inputs, and that claim holds for the
*arguments* but not for the *file* if this branch is reached. It is unreachable on all three
current adapters, so the defect is **recorded here, not filed**. **[code consequence]** when taken.

**The timestamp field set is named once.** `timestamp_warnings` hardcodes the pair
`("created_at", "last_activity_at")` (D20) — a hand-maintained restatement of what the schema's
timestamp fields are. A third timestamp added to the schema is unchecked unless someone remembers
that line. The field set belongs in `_normalized.py`, read by both the function and this contract.
**[code consequence]**

**Closed arms.** N4's and D20's adapter-owned arms are **closed**: the emitted grammar and the
timestamp field set are properties of the schema and of shared machinery's own output, so no adapter
can own them. D12's is closed for the same reason — age arithmetic is over already-normalized
timestamps and belongs to no adapter; only the *thresholds* it compares against are open, and those
are C8.

**Reachability (BL-132, 2026-08-11) — arithmetic and grammar reachable; D17 and N3 source-only,
and this contract's own unreachability claim is confirmed rather than inherited.** Age
arithmetic and the strict-greater comparison are exercised by every pass over a non-empty
inventory, and the second-precision UTC grammar by every compose: all four composed payloads
carried an `as_of` of the `%Y-%m-%dT%H:%M:%SZ` form. **D17's wall-clock fallback is source-only,
and C3's assertion that it is unreachable on all three adapters holds under check**: every adapter
stamps `generated_at` with `iso_now()` at every emission site, and the three **STEP 2** runs — one
per provider — resolved reference dates of `2026-08-07T16:56:59Z` (DO), `2026-08-04T04:29:40Z`
(AWS) and `2026-08-05T08:18:08Z` (Linode), each its recorded fetch timestamp and none the wall
clock of the day they were run. `[Corrected 2026-08-11 at the exercise sweep. As landed at
a690014 this said the arithmetic and grammar were "produced by every run" and then called two
different sets "the three runs" — the compose runs that emitted `as_of` (DO at both forms, Linode)
and the STEP 2 runs that resolved reference dates (DO, AWS, Linode). The AWS chain never reached
compose, its inventory being empty, so it belongs to the second set only. Both halves are now
scoped to the passes that produced them. **The verdict is unchanged**, and D17's confirmation
rests on the STEP 2 set, which is complete at one run per adapter.]` **N3's naive-timestamp rejection is likewise source-only**, no
adapter emitting a naive stamp. Both kept: each states an obligation on the next adapter.

### C4 — Money and currency  *(N5, P3, P5, R2)*

**Shared machinery guarantees** that every amount is coerced through one function and rounded to
**two decimal places** (N5), and that a cost total is built only from service-level
`line_items[].amount` — never from a resource's `monthly_cost_estimate`, which is an estimate used
for ranking and for an orphan's saving and is never summed into a cost total.

> *Truth-maker for that second clause, which no census field establishes* (added m4 t4b r2): read
> of `compose_report_data.py` at agents `a25f72f`. `service_totals` is the only function building a
> cost total (`:150`) and reads exactly `line_items`, `amount` and `totals` — never
> `monthly_cost_estimate`. The three reads of `monthly_cost_estimate` in that module are all in
> `coverage_section` (`:390`, `:404`, `:419`), the untagged-spender ranking. **Precision that
> matters**: `:419` *does* sum it, into `untagged_monthly_cost_estimate` — so "never summed" would
> be false, and "never summed **into a cost total**" is what holds.

**An adapter must guarantee** a `currency` on its cost snapshot. All three declare `USD` today, and
the 2dp rounding is correct *only because they agree*: two decimals is wrong for a zero-decimal
currency and wrong for sub-cent unit pricing, of which Linode's own price surface already carries an
instance. **The minor-unit exponent belongs in the cost snapshot beside `currency`**, and `money()`
should take it. **[code consequence]**

**The reconcile tolerance is currency-relative, or stated per currency** alongside that exponent
(P3). It is an absolute one-hundredth today, which is one cent only in a two-decimal currency.
Record also that Linode carries a `Tax` service line: where a declared total includes tax the line
items do not, the difference is **structural rather than arithmetic**, and no tolerance is the right
answer to it.

**The one-currency-scalar policy is stated with its blast radius** (P5). When bundles disagree on
currency, the grand total is withheld and per-currency figures are reported instead — correct, and
m1's stated position. The consequence that is recorded nowhere an operator sees: **adding a single
non-USD provider blanks the report's headline number for every provider**, because the scalar total
becomes null and renders as an em dash. That is the honest output; it is also a surprise, and this
sentence is the deliverable.

**Source-only by ruling, not by accident** *(added m5 t2, 2026-08-10)*. The one-currency-scalar
policy and its blast radius both describe **cross-provider** behaviour, and **no orchestrator
invocation reaches it**: `cloudcost/agents/cloudcost_orchestrator.exs` §STEP 3 offers two
mutually-exclusive arg forms — *"If STEP 1 printed `files.costs`, use this form"* and *"If STEP 1
did NOT print `files.costs`, use this form instead"* — and each passes at most one of
`--cost`/`--inventory`/`--orphans`, so every pipeline run composes exactly one bundle and no run
can make two disagree on currency. **m5-D2** (`cloudcost/m5-n1-compose.md` §Ratified decisions —
*"the N>1 compose surface is retained and bounded. It is a library-and-CLI capability the pipeline
does not invoke, and it is declared as such"*) rules that surface **retained and declared**, so
this paragraph is a true description of the source that states no behaviour the live pipeline
produces. **The guarantee is unchanged** — where bundles do disagree on currency the grand total is
still withheld and per-currency figures reported; what this contract now says differently is only
what it claims about reachability.

> **Pointer added m4 t5b, 2026-08-07 — read this paragraph with BL-131 beside it.** The policy
> above and its blast radius both describe **cross-provider** behaviour, and the cross-provider
> compose path is reachable only through a CLI flag the orchestrator never passes. The paragraph is
> **not false** — it describes the source accurately — but it states as current a behaviour nothing
> in the live pipeline produces, so **no amendment is owed and no authority should be taken from it
> until BL-131 rules.** m4 t5b's ruling to delete these paths was withdrawn on exactly that reading.
> **BL-132** is the row for whether other contracts share the property; two instances are not a
> census.
>
> `[Discharged 2026-08-10 at m5 t2. Its condition is met: BL-131 has ruled, as **m5-D2**, and the
> amendment this pointer deferred is the *Source-only by ruling* paragraph above. Kept rather than
> deleted, per decision 7 — it was true when written, and it records why the paragraph went
> un-amended for three days rather than leaving that gap to read as an oversight. One correction it
> earns in passing: the pointer says the path is *"reachable only through a CLI flag the
> orchestrator never passes"*, and m5 t1's **E1** established three routes rather than one — the
> repeatable flags, `--input-dir`, and the directory route — which changes the route count, not the
> reachability finding this pointer rests on. **BL-132** is untouched: whether the other thirteen
> contracts share the property is still its census to run, and two instances are still not a
> census.]`

**Presentation reads the exponent from the payload** (R2). **Closed arm**: R2's adapter-owned arm is
closed because the renderer must not learn provider identity — asserted by
`tests/test_render_report.py::test_the_region_block_names_no_provider_and_no_provider_payload_key`
(`:436`), read at `a25f72f`. It can read a currency descriptor, which is this contract's schema arm;
it cannot read a provider name.

### C5 — Percentages and ratios  *(N9, P9, R3)*

**Shared machinery guarantees** that the tag-coverage ratio is **per-resource, unweighted, to four
decimal places**, with an empty list yielding `0.0` (N9); and that a percent change is computed
against the prior figure, rounded to two decimals, with a **zero base yielding null** rather than a
number (P9) — there is no meaningful ratio against zero, so a service appearing for the first time
reports no percentage while one disappearing reports −100. That asymmetry is correct arithmetic and
is documented here so it is not read as an inconsistency.

**An adapter must guarantee** nothing here; both figures are computed by shared machinery over
already-normalized data.

**A naming discipline, so the renderer's filter choice is derivable rather than remembered** (R3):
the payload carries percentages in **two different units** — a *fraction* (coverage) and an
*already-percent* value (delta). Two filters exist for that reason, and applying the wrong one
produces a well-formed, plausible, wrong number that nothing can detect, because both inputs are
floats. **A field whose name ends `_pct` is already a percentage; a field named `coverage` or
ending `_ratio` is a fraction.** Then the correct filter follows from the name.

**Closed arms.** N9's, P9's and R3's adapter-owned arms are all **closed**, and for one reason:
these are computations over normalized data, not properties any provider supplies. N9's is closed
more strongly still — the whole reason `tag_coverage` lives in the shared module is that t2's and
t3's coverage figures are *required to be equal*, so a per-adapter definition would break the
equality the module exists to enforce.

### C6 — Tags  *(X3, N7, D6, D7)*

**Shared machinery guarantees** that `tags` is a **flat list of strings**, and keys two decisions on
it: the keep-tag exclusion and the coverage ratio.

**An adapter must guarantee** that list, and — where its own tag surface is key/value — must flatten
to the **`k=v` grammar**, with a bare key where the value is empty (X3). AWS constructs that
grammar; DigitalOcean and Linode pass native flat strings through and **cannot express a key/value
pair natively at all**. The grammar is therefore part of the contract, not an implementation detail
of one adapter — which is the census's adapter-arm text reached here as a schema statement.

**A non-`str` element is a counted skip, not a silent drop** (N7). Today it vanishes with no warning
and no `skipped` entry; an adapter emitting the wrong element type would take coverage to zero and
switch off the governance rule, reporting a clean-looking zero. It should surface the way
`usable_resources` surfaces a malformed resource. **[code consequence]**

**The keep marker is a first-class normalized field, not a tag spelling** (D6). It is
`keep=true` today, matched case-folded against the flat list — and BL-074's own phrase is the
argument: *an adapter convention masquerading as a shared constant*. The `k=v` spelling is native
only on AWS; on the other two it must be typed literally as a tag name. Each adapter should decide
how its own tag surface expresses the exclusion, and shared machinery should read a boolean.
**[code consequence]**

**The coverage threshold's distortion is recorded** (D7). The governance rule fires only above a
coverage cliff, and coverage is depressed structurally on a provider whose resource classes cannot
carry tags at all — Linode's IP addresses, backups and managed databases carry none — so on such a
provider the rule can **never** fire. **The denominator change is not taken here.** Restricting the
denominator to taggable resources would move `tag_coverage` itself, which C5 records as
contractually shared between two stages, so it is not a local edit. The open question — whether the
denominator should be taggable-resources-only — is stated and left to the ticket that can move both
stages together.

**Reachability (BL-132, 2026-08-11) — the flat-list guarantee and both keyed decisions reachable;
two clauses narrower than they read.** The coverage ratio is computed by every run that reaches
compose (`tag_coverage` 0.8889 over 18 DO resources, 0.4 over 15 Linode) and the keep-tag exclusion
is evaluated per resource in every detect pass — it excluded nothing in any of these runs, both
providers reporting `excluded: 0`, which is the rule finding no keep-tagged resource rather than
the rule not running. `[Corrected 2026-08-11 at the exercise sweep. As landed at a690014 this read
"computed on every run", which the AWS chain does not support — it reached STEP 2 only, over an
empty inventory, and never composed a coverage figure. The two clauses are also exercised by
different stages, which the single verb obscured. **The verdict is unchanged.**]` **X3's `k=v`
construction is reachable only under `CLOUDCOST_PROVIDER=aws`** — the contract already says DO and
Linode pass native flat strings and cannot express a pair, so on two of three provider selections
the grammar clause describes nothing the run produces. **N7's counted-skip for a non-`str` element
is source-only**: no adapter emits one, so the silent drop it describes is unreachable and the
remedy it asks for is unexercised. Both kept — X3 binds the adapter that needs it, N7 states the
obligation before an adapter breaks it.

### C7 — Attachment  *(D15, D16)*

**Shared machinery guarantees** that `attached_to` is a **single opaque string**, that a null value
is the universal idle signal keyed by four rules, and that the volume-to-instance join matches
`attached_to` against another entry's `resource_id`.

**An adapter must guarantee** one attachment only, and **must declare its reduction rule** — first,
or most significant — where the provider permits several (D15). The adapters differ today in how
they reduce; the reduction is currently an accident of each implementation rather than a stated
obligation. A provider with genuine many-to-many attachment cannot be expressed, and the join would
under-report attached storage, which silently *lowers* the stopped-compute saving. No current
provider exhibits it, so that is **recorded, not filed**.

**The tag-targeting grammar is part of the field's definition** (D16). A load balancer that targets
backends by tag carries `attached_to == "tag:<name>"`, and `rule_idle_load_balancer` is correct
**only** because such a load balancer therefore never reaches it. That convention originates in one
adapter's normalizer, is emitted by no other adapter, is enforced by nothing and asserted by no
test. Stating it here makes it an obligation a new adapter meets rather than a premise it silently
breaks — and breaking it makes every tag-targeted load balancer a HIGH-band false positive.

### C8 — Thresholds and the scoring model  *(D1, D2, D3, D4, D8, D9, D21, F1, F2, F3, F4, P1, X4)*

**Shared machinery guarantees** a single global rule catalog: age thresholds, confidence priors, two
additive modifiers, a clamp, and three confidence bands. **An adapter must guarantee** nothing here
— it supplies facts, not policy. These are **cross-provider priors**, and that is the ruling.

**The age thresholds are global** — unattached volume at 14 days, stopped compute and stopped
database sharing one at 30, snapshot at 30 (D1, D2, D3). The compute/database sharing is deliberate
and its rationale already exists in a code comment: a per-type fork would be *a provider assumption
wearing a type's clothes* (D2). **That comment is promoted here**, because a rationale in a comment
does not travel to the next adapter's author. **The rationale for 14-versus-7-or-30 is not
established**: a search of `cloudcost/` and `docs/` for `14 ?d(ays)?|fourteen` returns 27 hits, every
one of which either restates the value or uses it, and none of which gives a reason. Named as a gap
rather than reconstructed — the next provider that wants to argue against it has nothing to argue
with.

**The CLI-override asymmetry, from the record.** Only the snapshot threshold is overridable. The
**origin is established**: m1's §t2 Scope specifies the catalog as *"unattached volume >14d …
snapshot older than **N days** … stopped droplet with attached storage >30d"* — the snapshot rule
alone was written with a symbolic threshold and the other two with literals, and the implementation
rendered that faithfully as one CLI flag and two constants. **The rationale is not established**: a
search of `cloudcost/` and `docs/` for
`snapshot.age.days|snapshot_age_days|older than N|why N|symbolic` returns the value, the flag and
this ticket's own restatements, and no reason. The origin is a fact; the reason is a gap, recorded
as unexplained rather than filled by inference.

**The scoring model is additive-then-clamped** (D9): a base confidence, plus modifier deltas,
clamped to `[0,1]`. **The clamp silently absorbs overshoot**, so a modifier set that is too strong
is invisible rather than erroneous — nothing reports that a value was clipped.

**The bands are calibrated against the base confidences, and the coincidence is intentional** (P1,
D8). The HIGH and MEDIUM cutoffs sit **exactly** on two of the six base confidences, so those two
rules land in their bands by equality rather than by margin, and any per-provider confidence
adjustment of even one hundredth would move a whole rule's output down a band. Stated here as
deliberate calibration so it is not rediscovered as a coincidence — and so that anyone changing
either number knows they are changing both.

**The re-open trigger for the confidences is named** (D8): a provider that does **not** charge for
the thing a rule assumes is waste. An unassociated static IP is near-certain waste where
unassociated IPs bill, and means nothing where they do not.

**Two rules carry no age gate, and only one of them says why** (F1, F4). The static-IP rule's
absence is deliberate and documented — an unassociated static IP bills from the moment it is
unassociated — and **that billing assumption is moved out of the rule's docstring and into this
contract**, so a new adapter meets it as an obligation rather than discovering it (F4, the positive
control). The idle-load-balancer rule's absence is **supported by the record** — the census
establishes that both DigitalOcean and AWS bill a load balancer from creation, from those adapters'
own price constants — but was never documented. It is documented here. **The deliverable for F1 is
the documentation, not a threshold.**

**Two asymmetries in the catalog are recorded as defects rather than resolved** (F2, F3). A
non-zero-cost predicate gates the stopped-database rule and not the stopped-compute rule, which
leaves uncovered the case that costs the most money on a provider billing stopped compute in full
(F2). And the aged-snapshot rule's docstring describes *age plus a source that is gone* while its
code requires only age, so a snapshot of a live volume fires at the same confidence as one whose
source is deleted (F3). Both are owed backlog rows by m4 t4c; neither is decided here.

**The activity window is recorded together with its universal-null status** (D4, X4).
`last_activity_at` is `None` at every emission site on all three adapters, so
`modifier_recent_activity` and its fourteen-day window **have never fired against any real
inventory on any provider**. The field stays — a provider exposing last-access would make it live —
but the constant must not be read as tuned, and the modifier must not be read as exercised
behaviour. Owed a row by t4c: whether a permanently-dead scoring path stays. `[The three
adapters that paragraph quantifies over are three of four since m6 t2: GitHub populates
`last_activity_at` on every seat. The claim above is scoped as written and is not amended —
recorded here so "all three adapters" is not read as "every adapter".]`

**The consumption class carries one obligation of its own, and it is a billing assumption
before it is a threshold** (m6 t3, the idle-seat rule). An adapter emitting a
consumption-class entitlement must guarantee that **the entitlement bills for as long as it is
assigned, regardless of whether anyone exercises it** — that is what makes an unexercised one
recoverable spend rather than merely unused, and it is the assumption the rule rests on
entirely. Stated here rather than in the rule's docstring for the reason F4 records: a new
adapter in this class meets it as an obligation instead of discovering it. **The threshold is
thirty days of inactivity, and both of its sources are named** so it does not join the two
above whose rationale this contract records as unestablished: the provider that first exhibited
the class publishes thirty for exactly this decision (GitHub's inactive-licence guidance and
its revocation policy), and thirty is already in this catalog's register as the
stopped-compute/stopped-database threshold and the snapshot default. It is **overridable**,
unlike the two age thresholds and like the snapshot one — how long an assigned entitlement may
sit unexercised is an organisation's policy rather than a property of the resource, which is
the reason the snapshot flag never had. **The re-open trigger is a provider whose seats are not
billed per seat** — and unlike C7's and C10's, this trigger is **not hypothetical and must not
be read in that register**: `m6-github.md`'s opening names AI-provider spend as the third
member of this class, and AI spend is metered rather than billed per seat. The trigger is
waiting on a provider this milestone has already named, not on an unlikely one.
`[Added 2026-08-14 at m6 t3. It POSTDATES BL-132's census (2026-08-11, stamped below), so its
lack of a reachability verdict means it was never censused — not that it was censused and
found unreachable. No verdict is offered here.]`

**The declared parameter block covers the age thresholds and the coverage threshold, and nothing
else** (D21). The six confidences, the two modifier deltas, the keep-tag spelling, the ephemeral
pattern and the band cutoffs are **not** echoed, so a report cannot state the full parameterization
it was produced under. **The block is also write-only** — no consumer reads it: not the compose
stage, not the renderer, not the sprint. Both facts are recorded, and the gap is left open rather
than closed.

**Reachability (BL-132, 2026-08-11) — the catalog reachable; X4 source-only and self-confirmed;
D21's write-only status confirmed, its enumeration not.** The band definitions and the declared
parameter block are emitted by **every** detect pass, including one that finds nothing — a
zero-candidate run still carries all three bands. The priors, the modifiers and the clamp produce
a score only for a **scored candidate**: a Linode run scored one at base `0.85`, no modifiers,
landing MEDIUM by margin. `[Corrected 2026-08-11, one commit after this sentence landed at
a690014, where it read "Bands, priors and the additive-clamped model are produced by every detect
pass". Over-broad for two of its three subjects, and the same error corrected in C15's basis cell
in` `cloudcost/docs/bl-132-implementation-notes.md` `— chased here in the same round rather than
left one file over. The verdict is unchanged: the catalog is reachable.]` **X4 is source-only and this contract's own claim about it
holds under check**: `last_activity_at` is `None` at all **eighteen** emission sites across the
three adapters, so `modifier_recent_activity` and its fourteen-day window cannot fire — and the
pipeline now says so in its own payload, which carries the marker
`cannot_fire_no_last_activity_at`. That marker is the one place a self-reporting contract is
checkable from output rather than from source, and it agrees. **D21's block is reachable and its
write-only status confirmed** — no consumer in compose, the renderer, the template or the sprint
reads it. Its *enumeration* is recorded as drifted in `cloudcost/docs/bl-132-implementation-notes.md`
and is not amended here, under this row's findings threshold.

### C9 — Identity, slugs and filenames  *(N6, D18, P10)*

**Shared machinery guarantees** that a provider's output filename is derived from a filesystem-safe
slug of its `provider` value and its `period`, so two providers writing into one output directory do
not collide.

**An adapter must guarantee** a `provider` value that is **slug-safe and unique** among the
providers in a run (N6). The slug function lowercases and collapses everything outside `[a-z0-9]`,
so a name that is entirely non-ASCII collapses to a constant fallback and two such providers slug
identically. Constraining the value makes the function a validator rather than a rescuer.

**The collision routes, both of them** (D18). A slug collision in the sprint fails **loudly**: the
sprint's artifact discovery requires *exactly one* match and its guard arm fires otherwise. The
residual quiet case is `period` — a document carrying none writes to an `unknown` filename, and a
second such document overwrites the first with nothing reported.

**One duplicate is a held position, not an oversight** (P10). The compose stage carries its own
private slug function, byte-identical in behaviour to the shared one. It was frozen deliberately so
that an earlier milestone's *"compose ran unchanged"* result stayed a clean negative proof, and
**BL-070 owns the convergence**, to be taken when that file is next legitimately edited. Recorded
here so it is not re-flagged as a finding by the next reader.

**Reachability (BL-132, 2026-08-11) — derivation reachable; both collision routes source-only.**
The slug-and-period filename derivation runs on every invocation: the recorded runs wrote
`digitalocean_orphan_candidates_2026-08.json` and `linode_orphan_candidates_2026-07.json`, each
name derived rather than passed. **Both of D18's collision routes are source-only.** The loud one
needs two providers writing into one output directory, which the orchestrator never arranges — it
runs one provider per invocation, selected by `CLOUDCOST_PROVIDER`. The quiet one needs a document
carrying no `period`, and every adapter emits one. **Kept** — D18 is a statement about what a
second concurrent provider would meet, and its value is that it is written before anything
arranges that.

### C10 — Document shape and discovery  *(P4, P6, P8, P11)*

**Shared machinery guarantees** that it discovers normalized artifacts by **shape**, groups them
per provider, and derives the prior period from the period itself rather than from a clock.

**An adapter must guarantee** a `period` that is a **calendar month**, `YYYY-MM` (P4). A
non-conforming value should warn. Today it is silent, and the silence is compound: no
month-on-month section, no persisted history, forever, with nothing reported — so a provider on a
non-calendar billing cycle would produce a permanently degraded report that never says so. No
current provider exhibits it, so this is **recorded, not filed**.

**Service identity needs a stable identifier beside the display name** (P6). Service names are raw
provider strings, grouped by exact string match and keyed by the month-on-month delta as
`(provider, service)`. So **any** change in a provider's service naming between two months reports
the old name as removed and the new one as new, a full swing in both directions with nothing
indicating they are the same service. This is expensive to fix — prior snapshots already on disk
carry the old names — and is stated with that cost. **[code consequence]**

**Documents carry an explicit type** (P8). Classification is by presence of a list-valued key, in a
fixed order, and two modules in this repo **disagree about what a valid cost document is**: a
snapshot carrying a declared total and no line items is legitimate to the totals function and
unclassifiable to the classifier, so it is silently dropped from discovery — the run composes a
report missing that provider's costs entirely and exits clean. Owed a row by t4c; the minimum owed
is a warning and a skip entry, ahead of the explicit-type change. **[code consequence]**

**`source_granularity` is enumerated and actually checked** (P11). It exists to make the
cost-granularity honesty claim checkable, is copied into the payload, and is **compared or validated
nowhere**. A provider emitting account-level costs would have them grouped by service exactly as if
they were service-level, with the only trace a string in the report. The totals function should warn
on a granularity coarser than service. Owed a row by t4c. **[code consequence]**

**Reachability (BL-132, 2026-08-11) — discovery and prior-period derivation reachable; P8 and P11
source-only.** Shape discovery, per-provider grouping and the clock-free prior period are produced
on every run: a two-month DO pair resolved `prior_period` `2026-07` from the period `2026-08` and
reported `delta_amount -145.76`, `delta_pct -78.58`. **P8's silent drop is source-only** — it needs
a snapshot with a declared total and no line items, which no adapter emits — and **P11's unvalidated
`source_granularity` is reachable as a carried value and source-only as a defect**: the field is
composed into the payload (`"source_granularity": "service"` on the DO provider row) and compared
against nothing, but no adapter emits a granularity coarser than service, so the mis-grouping it
warns of cannot arise today. Both kept; each is the obligation a coarser-grained provider meets.

### C11 — Optionality and presentation  *(R1, P2, P7)*

**Shared machinery guarantees** a **required/optional split** over the report payload's top-level
sections: a required section absent costs a rendering note and a non-zero exit; an optional field
absent costs nothing at all.

**An adapter must guarantee** the required sections' inputs, and may supply optional ones.

**This is the positive control for the whole census** (R1). A provider-differing section — region
coverage, which only one adapter produces — is handled by putting it in the **right tuple**, not by
teaching the renderer about providers; and the renderer's ignorance of where a field came from is
asserted by
`tests/test_render_report.py::test_the_region_block_names_no_provider_and_no_provider_payload_key`
(`:436`), read at `a25f72f` rather than taken from the code comment beside `OPTIONAL_FIELDS` that
claims it. Putting that field in the required tuple instead would have made every run by a
provider without the concept exit non-zero, forever. **This is the shape every other item in this
census is ruled toward**: the difference between a provider-differing value handled structurally and
one handled by a special case.

**The sanctioned provider-extra read is promoted to a first-class optional field** (P7). One named
key is lifted out of the otherwise-opaque provider payload block, and the region-coverage section
**keys on its presence** — the section appears or does not appear because of it — so the ruling test
puts it in the schema rather than leaving it as a sanctioned exception. Promoting it to a
first-class optional envelope field makes the exception unnecessary and removes the precedent for a
second such read, which today only a comment prevents. **[code consequence]**

**Caps report their truncation** (P2). The untagged-spenders table is capped **after a global sort
across all providers**, so one provider can be absent from the table entirely while another fills
every row — and nothing reports it. The same file argues against silent caps elsewhere, for the
region list, on the same reasoning. The payload should record how many were dropped. Owed a row by
t4c.

**Source-only by ruling, not by accident** *(added m5 t2, 2026-08-10)*. The clause that makes this
cap's failure mode cross-provider — *"capped **after a global sort across all providers**, so one
provider can be absent from the table entirely while another fills every row"* — describes
behaviour **no orchestrator invocation reaches**, for the reason C4's paragraph of the same name
gives: every pipeline run composes exactly one bundle, and at one bundle the cap drops rows without
dropping a provider. **m5-D2** (`cloudcost/m5-n1-compose.md` §Ratified decisions) rules that
surface retained and declared rather than removed. **The guarantee is unchanged** — the cap still
reports its truncation at any N, which is what P2 required and what landed at m4 t5b independently
of this ruling; what changes is only what this contract claims about reachability.

> **Pointer added m4 t5b, 2026-08-07 — same caveat as C4, and the fix has landed regardless.** The
> dropped count is now in the payload (`untagged_not_shown`, `tags_not_shown`) and renders in both
> states, so the cap reports its truncation at any N. But *"across all providers … one provider can
> be absent from the table entirely"* describes the **cross-provider** path BL-131 decides the
> support of. **Not false, not yet amendable** — see C4's pointer and **BL-132**.
>
> `[Discharged 2026-08-10 at m5 t2, with C4's. BL-131 has ruled, as **m5-D2**, and the amendment
> this pointer deferred is the *Source-only by ruling* paragraph above. Kept rather than deleted,
> per decision 7. The distinction it drew holds and is worth keeping visible: the **fix** — the
> dropped count in the payload — never depended on BL-131 and landed at m4 t5b, while the **stated
> consequence** did. Only the second is what this discharge settles.]`

**Closed arm**: P2's adapter-owned arm is **closed** because the ranking is cross-provider by
construction — no single adapter can own a cap applied across all of them.

### C12 — Encoding  *(X5)*

**Shared machinery guarantees** **UTF-8** at every file read and write across all four scripts.

**An adapter must guarantee** UTF-8 on the artifacts it writes.

Today the guarantee does not hold: one script specifies the encoding at all four of its I/O sites,
and two others specify none at five sites and take the platform default. No current artifact
differs, because every value the three adapters emit is ASCII — which is exactly why it has gone
unnoticed. Under a non-UTF-8 locale a non-ASCII resource name would either raise through the stdout
contract that the stage-CLI rule exists to protect, or mis-decode silently into the candidate
identity, the evidence text and the rendered report.

**The asymmetry is worse than a plain absence**: the one stage that would *display* the corruption
is the one that already specifies the encoding, so corruption enters upstream of the only correct
site. **Adjacent to BL-112 — the same locale, one layer up, and neither row guards the other.**
Owed a row by t4c; the row's real cost is a non-ASCII fixture, without which the change is
unverifiable.

**Closed arm.** X5's adapter-owned arm is **closed**, and for a reason particular to it: the
encoding here governs how shared machinery *decodes* a file an adapter has **already written**, so
there is no adapter-side lever that could own it. (Whether the adapters specify an encoding when
they *write* is a separate question, outside BL-074's four-file scope and not swept by the census —
stated as a limit rather than assumed either way.)

**Reachability (BL-132, 2026-08-11) — the contract's own report that its guarantee does not hold is
confirmed at HEAD; the corruption it describes is source-only.** Counted at `8845d85`:
`render_report.py` has **four** I/O sites and specifies UTF-8 at all four — three explicit
`encoding="utf-8"` arguments plus the Jinja `FileSystemLoader`, whose own default is UTF-8;
`detect_orphans.py` (2 sites) and `compose_report_data.py` (3) specify **none**, which is the
five this contract names. So the asymmetry is real and unchanged. **The corruption is
source-only**: it needs a non-UTF-8 locale *and* a non-ASCII value, and every value the three
adapters emit is ASCII — which is this contract's own explanation for why it has gone unnoticed,
restated here as a reachability verdict rather than as a reason to relax it. **Kept unqualified**;
the fixture this needs is what makes the row it is owed real work.

### C13 — Carry-only fields (adapter-owned)  *(X2, D19)*

**Shared machinery may carry these and must never key on them.** Sorting, comparing, summing,
branching and joining on them are **foreclosed**.

**An adapter owns them entirely**, and must reduce its own richer structure into the single value
the schema carries.

**`size` is a free-form human label** (X2). The same physical quantity is spelled three ways today —
`GiB` on two providers, `GB` and `MB` on the third — and both of its consumers are display-only: one
interpolates it into an evidence sentence, the other copies it into the spenders table. The
divergence is therefore harmless *and permanently so*, provided nothing ever keys on it.

**The five identity fields are carried, not keyed** (D19). None of `resource_id`, `type`, `name`,
`region` or `raw_ref` is tested by a rule in its identity role. **`region` is a single opaque
display string**: a provider with a region/zone hierarchy must flatten it, and that flattening is
the adapter's obligation. `raw_ref` is a provider-console URL and is provider-shaped by
construction, correctly built in each adapter.

> `type` is carried *here*, in the identity block, and keyed elsewhere under C1. The distinction is
> per-role, not per-field name — noted so the two contracts are not read as contradicting.

### C14 — Adapter cost-model obligations (adapter-owned)  *(D13, D14)*

**Shared machinery guarantees** that it performs no provider-specific cost reasoning: it sums what
the adapters priced.

**Each adapter must guarantee its own cost model, and must assert it in its own tests.**

**The stopped-compute saving is the model the rest of this census is ruled against** (D13). It sums
an instance's own estimate and its separately-inventoried volumes', and that single sum is correct
for a provider billing a stopped instance in full *and* for one billing no compute for it — because
each adapter already encoded its own answer in `monthly_cost_estimate`. That is seam #3, closed at
m2 t2 c, and it is the worked example of a provider difference resolved in the right place.

**The surviving assumption becomes a stated obligation**: *only separately-inventoried storage is
summed.* A provider that inventories storage separately **and** folds its cost into the instance's
estimate would be double-counted, and nothing detects it. All three satisfy the assumption today, so
this is an obligation to be met rather than a defect to be fixed — but it must be met explicitly,
and asserted per adapter.

**The stopped-database inference is likewise an obligation** (D14): *a stopped database's estimate is
exactly its still-billing storage.* The rule infers "storage still bills" from a non-zero estimate on
a stopped resource, which holds for the one provider that emits the type. Recorded plainly:
**this makes one adapter's cost model load-bearing for a shared rule's correctness.**

**Reachability (BL-132, 2026-08-11) — the no-provider-reasoning guarantee reachable; D14's
inference source-only.** Shared machinery summing what the adapters priced is exercised on every
run with a cost snapshot: the DO run built `grand_total 39.74` from three service line items and
nothing else, and the reconcile arm fired against the declared total in the same pass. **D13's
stopped-compute saving is reachable** in shape and was not exercised by these runs, no stopped
instance appearing in the recorded inventories. **D14's stopped-database inference is source-only
on the current three** — it fires only for a provider emitting the database type in a stopped
state, and none of the recorded artifacts carries one. Kept: D14's point is that it makes one
adapter's cost model load-bearing, and that is a statement about the obligation, not the run.

### C15 — Neither arm  *(D5, R4)*

Two items are recorded with their reason rather than forced into an arm. Both were reached by the
ruling test returning *neither*, and that outcome is reported rather than resolved by picking.

**The ephemeral-name pattern is operator configuration** (D5). It matches resource names beginning
`tmp-`, `ci-` or `test-` and raises confidence. Naming conventions are an **account** property, not
a provider property and not the schema's — a tenant chooses them, and two accounts on the *same*
provider may differ. This is the only item in the census where a **third home is established rather
than asserted**, and it is the reason C15 exists at all.

A residual is carried, not decided: this matcher is **case-sensitive** while the keep-tag matcher
**case-folds**, two adjacent string matches in one module with opposite policies and no stated
reason for either.

> **Precondition run at m4 t4c, 2026-08-07. It failed, so no row was filed — the residual is
> recorded here as the note the ruling called for.** Two checks:
>
> **1. Does it bite? No, on every name in the record — and *the record* is the scope of that
> claim.** Across **118** distinct resource-name strings drawn from the **recorded corpus** —
> committed fixtures, `data/` and `output/`, plus adapter source, at agents `1779368` — **zero**
> match the ephemeral pattern case-insensitively but not case-sensitively.
>
> **This is not evidence about production accounts, and the distinction matters here more than it
> usually would.** The concern being tested is that one adapter's names arrive from a `Name` tag
> and are capitalised **in practice**; fixtures are *authored*, so they are precisely where
> real-world capitalisation is under-represented. *Established from the record* is the correct
> filing standard and the record is what was checked — but a later reader must not take the zero
> as a statement about live inventories. **That is why the re-run guidance below is not optional.** Five match as written and the modifier fires
> correctly (`ci-runner-cache`, `test-fixture-vol`, `tmp-egress-ip`, `tmp-orphan-disk`,
> `tmp-scratch-vol`). Eleven strings are capitalised and **all eleven are cost line-item service
> labels** — `Droplets`, `Taxes`, `Product usage charges` — not resource names, and none begins
> with an ephemeral prefix in any casing. The AWS `Name`-tag path that motivated the concern
> (`fetch_aws.py:442`) yields eight recorded values, **all lowercase**.
>
> **2. Does it cross a band? Yes, and exactly.** Verified from the constants rather than reasoned:
> both stopped rules carry base confidence `0.6`; `MODIFIER_EPHEMERAL_NAME` is `+0.1`;
> `BAND_MEDIUM_MIN` is `0.7`. So for those two rules the ephemeral modifier is **precisely** the
> LOW→MEDIUM boundary — `0.6` bands LOW, `0.7` bands MEDIUM. A missed match is a band change, not
> a rounding difference.
>
> **Why that combination is a note and not a row.** Check 1 is the trigger and check 2 is the
> severity. The severity is real and the trigger is unobserved on every provider in the record —
> which is the same shape as the three items this cycle excluded (D15, D17, P4): *latent on a
> hypothetical provider, exhibited by none of the three.* Filing it would put an unreproducible
> row beside ten reproducible ones.
>
> **What a later reader needs.** If the case policies are ever reconciled, reconcile them
> **toward case-folding**, matching the keep-tag predicate — and know that doing so can only move
> candidates **up** a band, never down. If a provider is added whose resource names arrive
> capitalised, check 1 must be re-run before that provider's first report is trusted.
>
> *(The ticket's two branch instructions conflict for this outcome — "if check 1 negative, file no
> row" and "if either is positive, file the row". Ruled here on trigger-versus-severity, and the
> conflict is reported rather than resolved silently.)*

**The PDF binary is an environment dependency** (R4). It is a named external tool on the optional
output path, and it differs by *machine*, not by provider. **It cannot be ruled by BL-074's
dichotomy at all.** It is censused and reported as unrulable rather than forced into an arm — an
item recorded as outside the question is a better answer than an item filed under the wrong half of
it.

---

## Contract refs (read, do not restate)

- `agent-creation-guide.md` (authoritative build reference + pre-flight checklist) and its
  conventions: `__ENV__.file` sandbox, `--output` flag, standalone + pytest with recorded
  fixtures, no `python3 -c` inline, dir-name stdlib-collision check.
- `capability-matrix.md` and both `CLAUDE.md` learning sections.
- **§Normalized schemas** (above) for the cost-snapshot and resource-inventory shapes, and
  **§t2 Scope** for the orphan-heuristic catalog with base confidences and modifiers. Both are
  inlined in this milestone doc — there is no separate proposal doc in the repo.
- DO Billing API reference (`/platform/billing/reference/` — balance, invoices, billing
  history) and the DO API reference list endpoints for droplets, volumes, reserved IPs,
  snapshots, load balancers. `docs.digitalocean.com/llms.txt` is the index.
- Docbuilder `generate_pdf.py` / `generate_html.py` for the report-render reuse (t4).

---

## Ticket set

### t1 — Use-case scaffold + DO adapter (`fetch_do.py`)

**Scope.** Create the `cloudcost/` use-case tree and the DO adapter. `fetch_do.py` fetches
(a) DO billing — balance, current-period invoice/billing-history — and (b) resource
inventory — droplets, volumes, reserved IPs, snapshots, load balancers, with `state`,
`attached_to`, `created_at`, size/type — and emits **two normalized JSON files** per
**§Normalized schemas**: `do_costs_{YYYY-MM}.json` and `do_inventory_{YYYY-MM}.json`. Auth via
read-only `CLOUDCOST_DO_TOKEN`, read from the env and **passed to the DO client explicitly** —
never rely on `pydo`/`requests` default `DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN` env pickup, so a
stray token cannot shadow the intended read-only one. Pagination + retry + rate-limit handling
live in the adapter. `source_granularity: "service"`, `resource_id: null` on cost items;
`monthly_cost_estimate` derived from size/type on inventory items. `raw_ref` (`do://…`) on
each resource for the evidence trail.

**Contract refs.** agent-creation-guide (adapter conventions); **§Normalized schemas** (this
milestone doc, not an external proposal); DO Billing API + resource list endpoints (via
`llms.txt`); `pydo` (confirm its billing-endpoint coverage; fall back to `requests` for any
endpoint it doesn't expose).

**Touches.** `cloudcost/` scaffold (`agents/ scripts/ data/ tests/ docs/ output/.gitkeep`);
`cloudcost/.gitignore` (excludes real data + `output/`); `scripts/fetch_do.py`;
`tests/conftest.py`; `tests/test_fetch_do.py`; `tests/fixtures/do_*.json` (recorded
responses); `requirements.txt` (`pydo`/`requests`).

**Do-not-generate.** The DO MCP path (REST only); any write/management call (list/get only —
never create/modify/delete); resource-level *cost* fabrication (cost stays service-level;
resource $ is the inventory estimate); reliance on the DO client's default token env lookup
(construct with `CLOUDCOST_DO_TOKEN` explicitly); any other provider; `python3 -c` inline
logic.

**Done-check.**
- `cd /tmp && python3 -c "import cloudcost"` must fail (dir name is stdlib-safe). Run it from
  a cwd that does not contain `cloudcost/`: from the repo root Python's implicit namespace
  packages make the bare directory importable, so the check would report the cwd rather than
  the name — and would pass for a genuinely colliding name too.
- With `CLOUDCOST_DO_TOKEN` set: `python3 scripts/fetch_do.py --output-dir /tmp/cc` writes
  both files, each schema-valid, with real balance + a populated inventory.
- `python3 -m pytest cloudcost/tests/test_fetch_do.py -v` green against recorded fixtures
  (offline — no token).
- The token appears in neither stdout nor stderr on success or on an auth failure.

**Claude-code prompt.**
> Build the `cloudcost` use-case scaffold and the DO adapter per `cloudcost/milestone.md`
> §t1. Read `agent-creation-guide.md` and both `CLAUDE.md` learning sections first.
> `fetch_do.py` fetches DO billing (balance/invoice/history) and resource inventory
> (droplets/volumes/reserved-IPs/snapshots/load-balancers with state + attachment + age) via
> the DO REST API (`pydo` or `requests`, read-only `CLOUDCOST_DO_TOKEN` from env — passed to
> the client explicitly, never the default `DO_TOKEN` pickup), and emits
> the two normalized JSON files per §Normalized schemas — `source_granularity:"service"`,
> `resource_id:null` on cost items; `monthly_cost_estimate` and `raw_ref` on inventory items.
> Pagination/retry in the adapter. Standalone-runnable; pytest against recorded fixtures
> (offline). Do NOT use the DO MCP, do NOT make any write/management call, do NOT let the
> token reach stdout/stderr. Done-check per §t1.

---

### t2 — `detect_orphans.py` (provider-agnostic heuristics)

**Scope.** Apply the deterministic orphan catalog to a normalized inventory and emit
candidates with `confidence`, `evidence[]` (the specific facts that fired), and
`monthly_saving_estimate`. DO-relevant rules from the proposal: unattached volume >14d
(0.9), unassociated reserved IP (0.95), snapshot older than N days (0.7), stopped droplet
with attached storage >30d (0.6), idle load balancer / zero backends (0.85); untagged-in-
tagged-account → **reported-only, never queued**. Modifiers (additive, capped): recent tag
activity −0.2; ephemeral name pattern (`tmp-`/`ci-`/`test-`) +0.1; `keep=true` tag →
excluded outright. All rules and modifiers are reviewable code, keyed to the **normalized
schema** (not DO shapes).

**Contract refs.** The heuristic catalog enumerated inline in this ticket's **Scope** (rules,
base confidences, modifiers) — authoritative for m1; plus the normalized inventory schema
(**§Normalized schemas**).

**Touches.** `scripts/detect_orphans.py`; `tests/test_detect_orphans.py`;
`tests/fixtures/inventory_*.json` (crafted edge cases).

**Do-not-generate.** Any LLM in the detection loop; DO-specific field access (operate on the
normalized schema so it's reusable); queuing of a reported-only rule; a hardcoded "now" (take
a reference date param so age rules are testable deterministically).

**Done-check.** Fixtures produce the expected candidates and confidences; a `keep=true`
resource is excluded; an untagged resource is **reported, not queued**; each modifier is
exercised; `evidence[]` names the facts that fired; `pytest` green.

**Claude-code prompt.**
> Build `detect_orphans.py` per `cloudcost/milestone.md` §t2 — deterministic heuristics over
> the **normalized** inventory schema (not DO-specific), emitting candidates with
> `confidence` + `evidence[]` + `monthly_saving_estimate`. Implement the §t2 Scope rule
> catalog and modifiers; reported-only rules are never queued; `keep=true` excludes. Take a
> reference-date parameter so age rules test deterministically. pytest over crafted fixture
> inventories including a `keep=true` case, a reported-only untagged case, and each modifier.
> Done-check per §t2.

---

### t3 — `compose_report_data.py`

**Scope.** Merge the cost snapshot + inventory + orphan candidates into one report-data
structure: totals by service; **MoM delta** vs the prior month's snapshot read from
`cloudcost/history/{YYYY-MM}/`; tag-coverage % + top untagged spenders; the orphan section
(candidates grouped by confidence, each with `evidence[]` + saving). First run has no prior
snapshot → the MoM section renders "no prior month" gracefully, not an error. Written to
merge **N providers** (trivial at N=1). **Persist this run's cost snapshot** into
`history/{YYYY-MM}/` for next month.

**Contract refs.** The normalized schemas; the report-data shape the t4 template consumes.

> **The two inputs do not share an envelope.** t1's cost snapshot carries a wall-clock
> `generated_at`; t2's `orphan_candidates_{period}.json` deliberately does **not** — it is
> byte-deterministic, carrying only `reference_date` (what the age rules were evaluated
> against) and `inventory_generated_at` (passed through from the adapter). Intentional and
> owned, not drift: it makes t2's output diffable across runs. t3 must not assume a uniform
> envelope across the files it merges, and should decide explicitly which timestamp the report
> is stamped "as of". `Source: t2 notes §Decisions; confirmed at t2 review.`

**Touches.** `scripts/compose_report_data.py`; `tests/test_compose_report_data.py`;
`tests/fixtures/cost_*.json` + `inventory_soc_*.json` + `orphans_soc_*.json`;
`cloudcost/history/.gitkeep`; `.gitignore` updated to exclude `history/*` (real cost data).
*Widened at build (recorded, not silent):* `scripts/_normalized.py` — the shared
normalized-schema helpers (`tags_of`/`usable_resources`/`tag_coverage` + timestamp/money
coercion) extracted verbatim out of `scripts/detect_orphans.py`, which now imports them, so
the tag-coverage figure t3 must report *equal* to t2's has one definition rather than two
(m2b rule: shared plumbing goes in a `_helper.py`, not duplicated or cross-imported between
CLIs). `tests/test_detect_orphans.py`'s provider-agnostic source guard was extended to read
`_normalized.py` alongside the rule module so the extraction cannot shrink its reach.
t2's 54 tests pass unchanged. `Source: t3 notes §Scope note.`

**Do-not-generate.** LLM in the merge/delta; a crash on a missing prior month; committing
history data (gitignored); resource-level cost totals (totals are service-level per D4).

**Done-check.** Correct report data on DO fixtures (totals, tag coverage, orphan section);
first-run no-prior-month path clean; the run's snapshot is written to `history/`; the merge
is N-provider-shaped (a two-provider fixture composes without code change).

**Claude-code prompt.**
> Build `compose_report_data.py` per `cloudcost/milestone.md` §t3 — merge cost + inventory +
> orphan candidates into report data: service totals, MoM delta vs the prior-month snapshot
> in `cloudcost/history/{YYYY-MM}/` (graceful "no prior month" first run), tag-coverage % +
> top untagged, and the confidence-grouped orphan section with evidence + saving. Persist
> this run's cost snapshot to `history/` (gitignored). Write it to merge N providers. pytest
> including the first-run path and a two-provider merge fixture. Done-check per §t3.

---

### t4 — Custom report template + render (local file)

**Scope.** A **custom** cloudcost report layout and a render script that turns t3's report
data into a report document (PDF/HTML) written to a **local file** (no email/Drive this
milestone). Sections: cost summary (service totals + MoM), tag coverage + top untagged
spenders, and the **orphan candidates** section — each candidate showing its evidence and
`monthly_saving_estimate`, grouped by confidence. Reuse Docbuilder's `generate_pdf.py` /
`generate_html.py` render path if it fits the custom layout cleanly; otherwise a purpose-
built renderer.

**Contract refs.** Docbuilder `generate_pdf.py` / `generate_html.py`; the report-data shape
from t3.

> **Carried into t4 from the t3 review — two requirements, one of them a correctness one.**
>
> 1. **The MoM headline must render its new-provider caveat adjacent to the number.** At N≥2,
>    when a provider has no prior-month snapshot, `mom_delta.delta_amount` / `delta_pct` fold
>    that provider's *entire* spend into "growth": the t3 packet's two-provider run reads
>    +74.21 / +46.97 %, which is DO's real +14.21 plus someothercloud's first-time $60. t3
>    labels this honestly and machine-readably — `mom_delta.providers_without_prior_snapshot`,
>    per-service `change: "new"`, and a `warnings[]` entry — so nothing is hidden, but a
>    template that prints the headline percentage without the caveat beside it converts an
>    honest payload into a misleading report. Render the caveat next to the figure whenever
>    that list is non-empty. `Source: t3 review r0 F2 (non-blocking, carried).`
> 2. **The template computes nothing.** Everything t4 needs is already in
>    `report_data_{period}.json` — the band cutoffs (`orphans.bands[]`), the `top_k` actually
>    applied, the per-provider `reconciled` flags, and the two "estimate, not billed cost"
>    notes. If a figure seems to be missing, it is a t3 change, not a template calculation.
>    `Source: t3 notes §Open items forwarded.`

**Touches.** `scripts/render_report.py`; `cloudcost/templates/` (the custom layout);
`tests/test_render_report.py`.

**Do-not-generate.** Email/Drive delivery (local file only for m1); any data not present in
t3's report data (render-only — the report never computes or invents a figure).

**Done-check.** t3 report data → a local PDF/HTML with all sections, the orphan section
showing per-candidate evidence + saving; visually reviewable; renders cleanly on the
first-run (no-MoM) data too.

**Claude-code prompt.**
> Build the custom cloudcost report per `cloudcost/milestone.md` §t4 — a render script taking
> t3's report data to a **local-file** PDF/HTML (no email/Drive), with a custom layout: cost
> summary + MoM, tag coverage + top untagged, and a confidence-grouped orphan-candidates
> section showing each candidate's evidence and saving estimate. Reuse Docbuilder's
> generate_pdf/html path if it fits, else a purpose-built renderer. Render-only — never
> compute a figure. pytest including the first-run no-MoM data. Done-check per §t4.

---

### t5 — Orchestrator `.exs` + sprint case + end-to-end

**Scope.** `agents/cloudcost_orchestrator.exs` — `%Aetheris.RunConfig{}` with
`tools: ["run_command"]`, `sandbox_path` via `__ENV__.file`, `overlay_base_dir: nil`,
`context_strategy: :full` (corrected at t5 from `:rolling`/6 — four steps is well under the
guide's ~10-step `:full` threshold, and the workflow threads file paths from step 1 through
step 4, which a rolling window would truncate mid-pipeline), `provider: "anthropic"`,
`model: "claude-haiku-4-5-20251001"`, `label: "Cloudcost Orchestrator"`. System prompt = the
**linear** workflow: `run_command python3 fetch_do.py` → `detect_orphans.py` →
`compose_report_data.py` → `render_report.py`, each with the exact `command:`/`args:` format,
plus a Rules section ("all paths relative to the sandbox root; `overlay_base_dir` is nil,
outputs persist; if any step fails, report which and stop — do not investigate or retry").
Add a `cloudcost` case to `aetheris/scripts/sprint.sh` (prereqs: `python3` +
`CLOUDCOST_DO_TOKEN`; run the orchestrator; verify the report file exists). Finally,
**regenerate the capability matrix** (`agents/capability_matrix.exs`) so cloudcost registers
in `docs/capability-matrix.md` and Rig's matrix view — the matrix is a generate step, not a
live scan, so it needs the re-run to surface the new use case.

**Contract refs.** agent-creation-guide (orchestrator conventions, run_command format,
"report failures and stop"); the sprint.sh pattern; `agents/capability_matrix.exs` (the
matrix generator) and how Rig's `CapabilityMatrix` command sources it.

**Touches.** `cloudcost/agents/cloudcost_orchestrator.exs`; `aetheris/scripts/sprint.sh`
(new case); `cloudcost/docs/t5-implementation-notes.md`; `docs/capability-matrix.md`
(regenerated — manifest-tracked, so its staleness is an exempt WARN until the next export;
do not chase it).

**Do-not-generate.** `spawn_agent`/`wait_for_all` (single provider — linear `run_command`);
`write_file`/`read_file` in the orchestrator tools (not needed); any scheduling; any write op.

**Done-check.**
- `cd aetheris && mix run --eval 'Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")'`
  evaluates without error.
- `./scripts/sprint.sh cloudcost` runs the pipeline and finds the report file.
- **End-to-end on the real DO bill** (record mode): a report is produced and **≥1 orphan** is
  surfaced with its evidence; the report is reviewable without opening the DO console.
- `CLOUDCOST_DO_TOKEN` appears nowhere in the trajectory.
- `agents/capability_matrix.exs` re-run; `docs/capability-matrix.md` now lists cloudcost
  (its orchestrator + scripts). Confirm the Rig `CapabilityMatrix` command's data source: if
  it reads the regenerated matrix artifact, cloudcost surfaces in Rig's matrix view; if it
  re-scans agent files, confirm it appears there. (This is the only "surfaces on Rig" step —
  runs already appear in Harness → Runs automatically; a dedicated cloudcost *panel* is out of
  scope, a separate Rig ticket.)

**Claude-code prompt.**
> Build the orchestrator and sprint case per `cloudcost/milestone.md` §t5. Read both
> `CLAUDE.md` learning sections first (cross-repo: the sprint case is in `aetheris/`).
> `cloudcost_orchestrator.exs` is a `RunConfig` with `tools:["run_command"]`, `__ENV__.file`
> sandbox, `overlay_base_dir: nil`, `:rolling`/6, anthropic/haiku, and a system prompt
> sequencing fetch_do → detect_orphans → compose_report_data → render_report with exact
> run_command formats and a "report failures and stop" rule. Linear only — no spawn_agent
> (single provider). Add a `cloudcost` sprint case. Then re-run
> `agents/capability_matrix.exs` so cloudcost registers in `docs/capability-matrix.md` (and
> Rig's matrix view) — confirm the Rig `CapabilityMatrix` command reads the regenerated
> artifact vs re-scans, and note it in the packet. Verify the token never reaches the
> trajectory. Done-check per §t5, including the real-bill end-to-end run producing a report
> and ≥1 orphan.

---

## Sequencing

t1 → t2 → t3 → t4 → t5, mostly linear (t2 and t4 can overlap once t1's schema is fixed and
t3's report-data shape is agreed). t5 is the integration + the milestone done-when.

## Open items carried forward (not this milestone)

- Fan-out to AWS/GCP/Workspace/Linode/GitHub — each a new adapter + fixtures against the
  frozen schema; the resource-level cost path gets its first real proof at AWS/GCP.
- P2 review/approve queue (Provenance migration-queue pattern, resource IDs).
- P3 gated cleanup — separate agent + write tokens + the effect-class re-execution decision
  (a `:contained`-but-non-reproducible marker for the cleanup `run_command`, BL-047-style,
  is a *harness* ticket if we want verify to enforce "never re-execute a delete").
- Email/Drive delivery, automated monthly scheduling, currency conversion, DuckDB trend
  store.
- **Give t2's output file a provider prefix before the first multi-provider run.**
  `detect_orphans.py` writes `orphan_candidates_{period}.json`, which collides at N≥2 in one
  directory. t3 is unaffected — it groups by document shape and by the `provider` field inside
  the file, and its explicit `--cost/--inventory/--orphans` triples take any paths — so this is
  a naming decision (per-provider output dirs, or
  `{provider}_orphan_candidates_{period}.json`), not a defect. Lands with the second adapter.
  `Source: t3 notes §Open items forwarded.`
- **Spot-check t1's list-price rates against a resource-granular bill — re-forwarded past t3.**
  t1 parked this on t3 "where invoice items are already in hand"; they are not, in the sense
  that matters. DO bills at *service* granularity (D4), so its invoice carries no per-resource
  line to check the volume/snapshot/reserved-IP/LB rates against, and only the volume rate was
  invoice-derivable (t1 already did it). The check belongs to the first adapter whose provider
  bills per resource (AWS/GCP). Until then the orphan section's saving subtotals inherit those
  estimates and are labelled as estimates in the payload.
  `Source: t3 notes §Open items forwarded.`
- **Two of t4's rendered paths have never been looked at by a human — view them at
  fan-out, before the first N≥2 report goes to anyone.** The browser check that cleared t4
  (human, 2026-07-29) covered the **N=1 DO report**, which is the only path m1 ships. The
  **new-provider caveat** and the **multi-currency "No combined total"** rendering exist only
  in test fixtures: structurally tested (adjacency asserted by index, the withheld scalar
  asserted absent) and rendered to PDF during the build, but no eyeball has hit them in a
  browser. **Both are reachable and uninvoked** *(corrected m5 t2 r1, 2026-08-10 — this
  clause read "Correct for m1 — both are unreachable while DO is the only provider —")*: the
  flex-`gap` defect was invisible to every assertion and to one of two rendering engines, so
  the first ticket that makes either path reachable **from the pipeline** owes it the same
  two-minute look.

  **Reachability here is not a function of provider count**, which is what the superseded
  wording got wrong and what makes this more than a wording fix. Both paths sit on the N>1
  compose surface, which **m5-D2** (`cloudcost/m5-n1-compose.md` §Ratified decisions — *"a
  library-and-CLI capability the pipeline does not invoke"*) retains: three routes reach it
  today with DO as one of three providers, and no orchestrator invocation takes any of them.
  So the paths were never gated on a second provider arriving, and a second provider does not
  open them — decision **H** makes provider four a fourth solo run. The superseded clause
  restated the *"live at the first fan-out"* reading that m5 t1's **E1** killed, as a premise.

  **The item stays open and the eyeball is still owed** — that is the substance, and it is
  unchanged. What changes is who owes it and when: not the arrival of a second provider, but
  **the first ticket that makes either path reachable from the pipeline**, which under H and
  m5-D2 is no ticket now scheduled. Until then the two renderings remain exercised only by
  fixtures and by the CLI surface m5-D2 declares.
  `Source: t4 review r0, human browser check. Reachability claim corrected at m5 t2 r1,
  2026-08-10, under m5-D2 and on t2 r0's flag; §Open items added to t2's Touches by the
  reviewer at r1 to authorise it.`
- **`STOPPED_STATES` normalisation — a place where a provider's own vocabulary reached shared
  machinery, and ~~the one seam~~ ~~*one of three seams*~~ *one of 54 values censused for provider
  divergence at m4 t4a*. RESOLVED at m2 t2 a.**
  `detect_orphans.py:71` was `STOPPED_STATES = {"off"}  # DO vocabulary`, read by
  `rule_stopped_droplet_with_attached_storage` and pinned by three tests precisely so a
  second provider could not widen it silently. m2 t2 shrank it to the schema-level
  `{STATE_STOPPED}` and moved the mapping into each adapter.
  *Correction (m2 t1/t2, BL-074): "the one seam" was observation, not enumeration — the
  **Adjacent-case** rule's failure mode. There were at least three: (1) this one; (2) the
  `type` vocabulary, un-enumerated by m1 so DO's `droplet`/`reserved_ip` sat inside the rules
  (resolved at t2 a′ — see §Normalized schemas); (3) the assumption that a provider bills a
  resource regardless of state, which made the stopped-with-storage saving under-report
  (resolved at t2 c). BL-074 sweeps for the rest; the rule-catalog age thresholds and the
  `keep=true` tag spelling are the named next candidates.*
  *Corrected again (m4 t4a/t4b, BL-074, 2026-08-07). **"At least three" was itself an observation**,
  for the same reason "the one seam" was: nobody had enumerated. The m2 correction fixed the count
  and left the method — which is why it needed correcting a second time. m4 t4a swept the four
  scripts structurally and **censused 54 values**; the adjudication ruled **48 schema-level, 4
  adapter-owned, 2 neither**, and all 54 are now stated as contracts in **§Contracts (C1–C15)**,
  each cited there by census item id.*
  *Two things this correction does **not** claim. It does not say all 54 are seams: the census
  swept for provider divergence and censused some values it then found **not** to be seams — **at
  least four** (D8, D21, F1, R4), and R4 is recorded explicitly as unrulable by this row's own
  schema-level-or-adapter-owned dichotomy. **That four is a floor, not a count**: it comes from a
  match on the census's own **Meets** field, so it finds items whose Meets field *says* it meets
  nothing and misses items that meet nothing in substance. **N4 is a known case it does not reach**
  — its Meets field names a value, while its *Diverges today* field reads *"Output-side only; no
  adapter reads them."* The sentence's claim is that **not all 54 are seams**, and that needs a
  counterexample, not a census. **A seam count, as distinct
  from a censused count, is not established by t4a and is not asserted here.** Nor does it restate
  what m2's candidates would have amounted to in census terms; mapping that prose onto a definite
  number of census ids is inference, not reading. The substantive finding is that this was never a
  handful of seams to close but a large, mostly undocumented contract — so the deliverable was a
  contract section, not a migration. The census's method, and the argument for why it is an
  enumeration rather than a fourth observation, is
  `cloudcost/docs/m4-t4a-implementation-notes.md` §2.* Raised in
  `docs/t2-implementation-notes.md:170`; promoted here at m1 close because it gates the
  fan-out and an implementation-notes file does not travel to the next ticket's session.
- **Cross-currency aggregation is handled in one place and unhandled in four —
  `compose_report_data.py`.** When the bundles disagree on currency, `service_totals`
  withholds `cost_summary.grand_total`, reports `totals_by_currency` and warns (`:220–236`) —
  the right behaviour, and m1's stated position (no conversion, original currency). Four
  sibling aggregates sum straight across providers with no currency partition and no currency
  field on the result:
  `mom_delta.prior_total`/`current_total`/`delta_amount` (`:333–342`, with
  `mom_delta.currency` null, so the withheld scalar reappears one section down without a
  unit), `tag_coverage.untagged_monthly_cost_estimate` (`:419`),
  `orphans.by_band[].monthly_saving_estimate` (`:487`) and
  `orphans.totals.monthly_saving_estimate` (`:500`, derived from the former, so it follows
  whatever that does). The fix is t3's and must cover **all four** — a partial fix leaves the
  same class alive in the sections it skipped. Options: withhold like `grand_total` does, or
  emit each per currency. **Reachable and uninvoked; not gated on a fan-out that decision H
  forecloses** *(corrected m5 t2 r1, 2026-08-10 — this clause read "**Latent while m1 is
  DO-only single-currency; live at the first fan-out.**")*. All four sites sum across bundles,
  so they are on the N>1 compose surface **m5-D2**
  (`cloudcost/m5-n1-compose.md` §Ratified decisions) retains as *"a library-and-CLI capability
  the pipeline does not invoke"* — three routes reach them and no orchestrator invocation takes
  any. **There is no first fan-out to go live at:** under decision **H** provider four is a
  fourth solo run, so no future provider brings these sites into the pipeline. The
  single-currency condition also no longer holds for the reason the superseded wording gave —
  m1 is not DO-only, three adapters ship — but the exposure is still nil because all three
  declare `USD` (§Contracts **C4**), which is a fact about the adapters and not about
  reachability. **These are BL-070's four cross-currency aggregation sites, whose deletion is
  disposed *not taken*, so they stay** — and the fix above stays owed, on the surface rather
  than on a schedule. t4 mitigates on the render side only, which is the most a render-only stage may
  do: the MoM headline carries a "this change spans more than one currency" caveat beside the
  figure, and the three estimate aggregates print with no currency code rather than a wrong
  one. `Source: t4 notes §Open items; t4 review r0 F1 (claude-code named the MoM site only —
  the sweep was incomplete; the reviewer found the other three).`
- **Decide whether the report carries t2's `reported` (reported-only) list — a scope
  question, not a done-when gap.** `detect_orphans.py` emits a `reported` block (the
  untagged-in-tagged-account governance rule, reported-only by §t2 design, each entry with its
  own `evidence[]`); `compose_report_data.orphan_section` carries `candidates` only, so
  `report_data` has no key for it and t4 cannot render it — the rule fires in the pipeline and
  is invisible in its output (2 such resources on `inventory_tagged_account.json` today).
  Not a done-when gap: the milestone's stated report sections are cost summary + MoM, tag
  coverage + top untagged spenders, and orphan candidates — and tag coverage *is* the
  governance surface t3/t4 already render. So the question is whether a separate governance-
  flags section is wanted (t3 fast-follow / P2), not whether something is missing.
  **`excluded` (`keep=true`) staying invisible is correct and not part of this** — those are
  resources the operator asked to keep, and suppressing them is the intent.
  `Source: t4 review r0 F3 (refining t4's own forward, which wrongly bundled `excluded` in).`
- **Bound the recency modifier's window at both ends** (`detect_orphans.py`,
  `modifier_recent_activity`): today it rejects on `age > RECENT_ACTIVITY_WINDOW_DAYS` only, so
  a `last_activity_at` in the future relative to the reference date reads as "recent" and takes
  the −0.2. Unreachable while DO is the only provider (the field is null), so it lands with the
  first adapter that populates it — together with making the window a parameter.
  `Source: t2 review (docs/reviews/m1-cloudcost-t2-review.md).`
