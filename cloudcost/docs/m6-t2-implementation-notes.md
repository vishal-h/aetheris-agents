# m6 t2 — the GitHub adapter

Landed 2026-08-13, agents `e4fabb7` → this commit. Harness untouched at `66a9ca5`; this
ticket touches it nowhere, and the conclusion that it must not was never reached.

---

## Gate (§11), seven verdicts

| # | Verdict |
|---|---|
| i | **TRUE** — agents `e4fabb7`, level with `origin/main`, tree clean; harness `66a9ca5`, clean |
| ii | **TRUE** — `TYPE_SEAT = "seat"` at `_normalized.py:47`, and `CANONICAL_TYPES` at `:50–61` has eight members with `TYPE_SEAT` last |
| iii | **TRUE** — `cloudcost/m6-github.md` exists; §Ratified decisions at `:17` carries D1–D7. All five named decisions read before anything was written |
| iv | **TRUE** — `docs/m6-t1-implementation-notes.md:268–297`, *"HAZARD FOR t2 AND t3 — the `==` at `:840` masks every assertion after it"*. Read, and its procedure applied — see §W7 |
| v | **TRUE** — `set -a; source ~/.secrets/github-cloudcost.env; set +a`, the convention `runbook.md:56` states and `:96` back-references. `CLOUDCOST_GITHUB_TOKEN` non-empty. The file exports that one name and **nothing else** — there is no org variable in it, which is why `--org`/discovery exists |
| vi | **TRUE — isolation proved before any live call** |
| vii | **TRUE — D7 verified live** |

**Gate (vi), the isolation proof.** One call under `env -u CLOUDCOST_GITHUB_TOKEN` with the
same `Authorization: Bearer` header form returned **HTTP 401** `{"message": "Bad credentials"}`.
The control with the token, same header form, same URL, returned **HTTP 200**. Both ambient
names are set on this workstation — `GITHUB_TOKEN` and `GITHUB_PERSONAL_ACCESS_TOKEN`, each 40
characters — and neither was picked up. Every live call in this ticket used the explicit header;
`gh` was never invoked to make a request.

**Gate (vii), D7 made live.** For the closed month `2026-07`, on the organisation this
credential bills (named nowhere in this repo — U2's class below covers it):

| source | sum of `netAmount` |
|---|---|
| detail endpoint, 255 items | `133.999998176` |
| summary endpoint, 5 items | `133.99999817600002` |
| **difference** | **`-2.842170943040401e-14`** |

Gross agrees exactly — `318.840339695` on both, difference `0.0`. The net difference is
float-summation noise over 255 terms: about 2.8e-14 against C4's tolerance of 1e-2, twelve
orders of magnitude of headroom. **D7 holds.** Two further closed months were checked unasked
and both agree at `difference == 0.0`: 2026-06 (`97.533332358`, 324 detail items) and 2026-08
(`47.806450848`, 102 items).

---

## Touches widening, and why (T4)

Four files landed beyond the ticket's `Touches` list. Two are reviewer decisions taken in the
amendments to this session's prompt; two follow from them.

| File | Ground |
|---|---|
| `cloudcost/tests/record_github_fixtures.py` | **Reviewer decision (amendment T1).** Both existing providers commit a `record_<provider>_fixtures.py` beside their fixtures, and both state that *"scrubbing is code, not a manual pass"*. W7 requires captured, consistently-pseudonymised fixtures; the recorder is what makes "consistently" a property of the repo rather than of one session. The reviewer ruled the `Touches` list incomplete rather than deliberately narrow |
| `cloudcost/tests/conftest.py` | Follows from the fixture convention: every stub in this suite lives in `conftest.py`, and a stub local to one test file would be the first exception. `GitHubStub(DOStub)` + `GITHUB_FULL_ROUTES` + two fixtures, appended; nothing existing was modified |
| `cloudcost/tests/fixtures/github_*.json` | Six files. The ticket's `Touches` says *"`cloudcost/tests/fixtures/` or wherever the existing adapters keep theirs"*, so this is the list resolving rather than widening — recorded here because the count and the shapes were not stated in advance |
| `cloudcost/output/…` | Gitignored (`cloudcost/.gitignore:6`), written by the live smoke run. Not a repo change |
| `.gitignore` (repo root) | **Reviewer decision (amendment X1).** One entry, `/output/`, closing the hazard SURPRISE 6 found. See §The repo-root output hazard below |

**Not widened, and each a deliberate non-edit:**

- **`cloudcost/milestone.md`** — untouched, by ruling V4. No schema field, no canonical state
  value, no widened key set. See §S2 below.
- **`runbook.md`'s §Adding a provider five-place list** (`:567`) — t2b's, per the ticket.
- **`runbook.md`'s opening provider list** (*"currently DigitalOcean, AWS and Linode"*, `:3–4`)
  — **deliberately not updated.** That sentence describes which providers a *run* can select,
  and `CLOUDCOST_PROVIDER=github` selects nothing until t2b. Adding GitHub there would be false
  today. m6's close criteria require the runbook's provider list to include GitHub; that is
  satisfied at t2b, and this note is here so the omission reads as timing rather than oversight.
- **`../aetheris/scripts/sprint.sh`** and everything else in the harness — untouched.

---

## W1 — the shape the three adapters share, and where this one follows which

Read in full first: `fetch_do.py` (602 lines), `fetch_aws.py` (1136), `fetch_linode.py` (1406),
`_normalized.py` (173). The shared skeleton is one file in ten sections with right-aligned
`# ---- section` rules: docstring → `from __future__` → imports → constants → two exception
classes → client → helpers → normalizers → fetchers → main. `fetch_github.py` reproduces it.

| Element | The shared form | Followed |
|---|---|---|
| Module docstring | `"<Provider> read-only cost + inventory adapter (cloudcost <m>, t<n>)."`, the two artifact paths indented, *"Read-only by construction"*, an `Auth (…)` paragraph naming the one variable and the refused ones, `Usage:` | **Linode** — it alone adds per-adapter paragraphs after `Auth`, and GitHub has three to add |
| Credential read | `load_token(env=None)`, `env = os.environ if env is None else env` inside the body, `.strip()`, raising the Auth error naming both the accepted and the refused names | DO and Linode are identical here; followed verbatim |
| Shadowing refusal | `warn_shadowing_env(env=None, stream=None)`, presence-only predicate `(env.get(name) or "").strip()`, value never printed, returns the names found | **Linode** — the only one with a `stream=` parameter and with two classes |
| Error classes | `<P>AuthError` / `<P>APIError`, both `RuntimeError`. Auth is fatal (exit 1, no file); API degrades into `errors[]` | identical across all three |
| CLI | `--output-dir output`, `--period` (`YYYY-MM`, default current UTC month), `--api-base`, `--timeout 30`, `--max-retries 4`, `--retry-base-delay 1.0` | DO/Linode. AWS's `--endpoint-url` is boto-specific. `--org` is new and is GitHub's own |
| Emit | `write_json` byte-identical in all three (`.tmp` + `replace`, `indent=2`, trailing newline). Cost artifact **conditional** on `costs is not None`; inventory **unconditional** | identical |
| `money` | DO's private copy raises on a bad value, AWS's swallows | **Linode** — imports `money` from `_normalized` (`fetch_linode.py:284-291` states why). `iso` and `parse_timestamp` imported the same way; `current_period`/`iso_now`/`write_json`/`warn_shadowing_env` duplicated, never cross-imported |

### The provider slug, per position — reported because the do/digitalocean split has no stated rule

| Position | DO | AWS | Linode | **GitHub** |
|---|---|---|---|---|
| filename prefix | `do_costs_` / `do_inventory_` | `aws_` | `linode_` | **`github_`** |
| `provider` field | `digitalocean` | `aws` | `linode` | **`github`** |
| `raw_ref` scheme | `do://` | `aws://` | `linode://` | **`github://`** |
| env infix | `DO` | `AWS` | `LINODE` | **`GITHUB`** |

**The choice, and its ground, stated rather than left to fall out.** The do/digitalocean split
exists because DigitalOcean has a universally-used short form that is not its name — the
filename took the short form, the `provider` field took the name. AWS and Linode have no such
pair and use one token in both positions. GitHub is the AWS/Linode case, not the DO one: `gh`
exists as the name of a *tool*, never as an abbreviation of the company, so borrowing it would
invent a split the provider does not offer — and it would put the CLI's name on the artifacts of
an adapter whose entire credential posture exists to refuse that CLI's credentials. One token,
`github`, in every position.

---

## W2 — credential and shadowing

`CLOUDCOST_GITHUB_TOKEN`, read explicitly, and nothing else. **Membership of both classes was
established from `gh help environment`** (gh 2.90.0 on this workstation), not from the prompt
and not from memory.

**Class A — shadowing CREDENTIAL names.** gh's own text, in the precedence order it states:
`GH_TOKEN`, `GITHUB_TOKEN` for github.com and `*.ghe.com`; `GH_ENTERPRISE_TOKEN`,
`GITHUB_ENTERPRISE_TOKEN` for a GitHub Enterprise Server host. Plus
`GITHUB_PERSONAL_ACCESS_TOKEN`, which appears **nowhere** in gh's list and is warned about on
convention grounds alone — the same honesty clause `fetch_linode.py:64-68` records for
`LINODE_TOKEN`. This is the first provider where the refusal is load-bearing rather than
precautionary: two of the five are set on this workstation, and the shadowing credential is
broader-scoped (write) than the read-only one the adapter uses.

**Class B — endpoint-REDIRECT names.** `GH_HOST`, gh's own — *"specify the GitHub hostname …
If this host was previously authenticated with, the stored credentials will be used"* — which
redirects where a credential is sent. Plus `GITHUB_API_URL`, which is **not** gh's: it is read
by `@actions/github`, and it is named with that provenance rather than folded in as though gh
honoured it.

**`GH_CONFIG_DIR` is excluded, and the exclusion is recorded rather than silent.** It redirects
which *stored* credential gh picks up, which is a hazard only for a caller that reads gh's
credential store; this adapter reads none. Padding a shadow list is the thing Linode's comment
argues against, so leaving it out needed a reason and this is it. `test_the_shadow_list_is_ghs_
own_precedence_chain` pins both the membership and the exclusion.

Implementation follows `fetch_linode.warn_shadowing_env` exactly: one function, two loops, two
distinct remedy sentences (*"authenticates with `CLOUDCOST_GITHUB_TOKEN` only"* against *"it
redirects where a credential is sent, and cloudcost constructs its own GitHub base URL"*),
returning `present + redirects`.

---

## W3 — the cost snapshot

Source is `GET /organizations/{org}/settings/billing/usage/summary?year=&month=` (D7). The
detail endpoint is fetched too, for the reconcile gate only.

**Mappings.** Ruled: `amount ← netAmount`, `usage_qty ← netQuantity`. Derived and reported here:
`usage_unit ← unitType`; `service ← sku`; `resource_id`, `region` → `null` and `tags` → `[]`
(the summary surfaces none of the three); `account ← organization`; `period` from the echoed
`timePeriod`; `source_granularity = "service"`. `grossQuantity`, `discountQuantity`,
`grossAmount`, `discountAmount` and `pricePerUnit` go under `provider_extra.usage_items`.

**W3b's premise, checked rather than taken.** The detail endpoint's `quantity` sums to
`grossQuantity`, never to net — `actions_linux` detail quantity `806.0` = summary
`grossQuantity` `806.0`, against a `netQuantity` of `0.0`. Net-to-net is what keeps
`amount / usage_qty` an effective unit price.

**The two endpoints spell every product, SKU and unit differently, and it is not a case
transform.** Recorded because a human comparing this report against the detail endpoint or the
console will see different strings for the same thing:

| summary `product` / `sku` / `unitType` | detail `product` / `sku` / `unitType` |
|---|---|
| `Copilot` / `copilot_for_business` / `user-months` | `copilot` / `Copilot Business` / `UserMonths` |
| `Copilot` / `copilot_ai_unit` / `ai-units` | `copilot` / `Copilot AI Credits` / `AICredits` |
| `Copilot` / `coding_agent_ai_unit` / `ai-units` | `copilot` / `Copilot Cloud Agent` / `AICredits` |
| `Actions` / `actions_linux` / `minutes` | `actions` / `Actions Linux` / `Minutes` |
| `Actions` / `actions_storage` / `gigabyte-hours` | `actions` / `Actions storage` / `GigabyteHours` |

`copilot_ai_unit` ↔ `Copilot AI Credits` is not recoverable by any casing rule. The two SKU sets
are disjoint, which `test_the_two_endpoints_spell_the_same_thing_differently_and_not_as_a_case_
transform` asserts.

**W3c — currency, verified over the full response rather than taken from the prompt.** Both
bodies were swept structurally (every object at every depth) and textually (the raw body). The
complete key set across the two is `{date, discountAmount, discountQuantity, grossAmount,
grossQuantity, month, netAmount, netQuantity, organization, organizationName, pricePerUnit,
product, quantity, repositoryName, sku, timePeriod, unitType, usageItems, year}` — no currency
key at any depth — and the substrings `currenc` and `usd` appear in neither. `CURRENCY = "USD"`
is declared with `provider_extra.currency_basis` recording that check, in the form
`fetch_linode.py:583-586` established.

**And the basis has an invalidation, which Linode's does not.** A recorded finding about a live
API is a claim with no expiry. `currency_field_names()` re-runs the structural half of the sweep
on **every fetch** and warns if the endpoint has grown a currency-shaped key. Finding one would
not change the emitted value — D1 makes currency adapter-declared, never captured — it would
mean `currency_basis` now states something false, and the operator is told so.

**W3d — D3/D4.** Every aggregation is at full precision with `money()` applied once after. The
one multiplication site is the per-seat estimate; see §C14 below.

---

## W4 — the reconcile gate

Per run, not per scout: the detail endpoint is summed over the period and compared against the
summary total. Two months agreeing at scout time does not guarantee the third.

**The tolerance is C4's, used rather than invented.** C4 states *"The reconcile tolerance is
currency-relative, or stated per currency … **It is an absolute one-hundredth today**, which is
one cent only in a two-decimal currency."* `RECONCILE_TOLERANCE = 0.01`, absolute, applied to
the **full-precision** sums before `money()` (D3: rounding follows aggregation).

*A correction to the prompt's framing:* C4 contains no phrase *"known weakness"* — the word
`weakness` does not occur in `milestone.md`. What it records as the tolerance's defects are the
currency-relativity gap above, and the note that a declared total including tax against line
items excluding it is *"structural rather than arithmetic, and no tolerance is the right answer
to it"*. Neither reaches this arm: both sides here are net-of-tax sums of the same rows.

**Why not the existing arm's form.** `fetch_linode.normalize_cost:535-547` tests *exact
equality after `money()`* — an implicit half-cent. That is right for what it checks: one
payload's own parts against its own declared total, where any difference at all means an amount
failed to parse. This arm compares **two independent aggregations**, one of them over 255 float
terms, so the residual is summation noise rather than evidence, and an explicit epsilon is the
honest form. Recorded as a deliberate divergence with its ground, rather than a silent one.

**It raises, and this is the one place this adapter departs from the existing arm.** Linode
warns because its declared total stays authoritative whatever its line items do. Here the
agreement between the two endpoints **is** the entire ground on which D7 chose the summary
endpoint as the source; if they disagree, the figure has no basis, and a snapshot written anyway
is a well-formed wrong answer. The precedent is `fetch_aws.py:859-874` — *"a $0.00 snapshot
would be read as a real zero bill"* — and the posture matches it: `GitHubAPIError`, caught into
`errors[]`, **no cost file**, inventory still written, `status: partial`, exit 1. Loud, and the
run still yields what it legitimately established.

The result is also recorded on the artifact (`provider_extra.reconcile`) and in the run summary,
so a reader holding only the JSON can tell a reconciled figure from an unreconciled one.

---

## W5 — period: validated, and the echo verified

**W5a — this adapter is the first to validate deliberately, confirmed by reading all three.**
`fetch_do.select_invoice` matches the period string literally against `invoice_period` and
validates nothing. `fetch_aws.month_bounds` calls `strptime(period, "%Y-%m")`, which raises
`ValueError` uncaught — a check incidental to a conversion. `fetch_linode.month_of` slices
`timestamp[:7]` and compares. None validates on purpose. `PERIOD_RE` does, before the client is
built, so a rejected period costs no request at all —
`test_a_malformed_period_costs_no_request_at_all` asserts the stub saw zero requests.

**W5b — the echo is asserted.** `assert_period_echo` compares the summary's `timePeriod`
`{year, month}` against the request and rejects a mismatch *and* an absence. Following
`fetch_linode.resolve_billing`, whose docstring names the failure this prevents: *"a
per-provider history tree stays internally consistent under a constant offset, so nothing ever
errors and the report simply states a month it is not about."* The reconcile arm inherits the
summary's verified period rather than asserting its own, because the detail endpoint carries no
`timePeriod` to assert against — asserted as its own premise in
`test_the_recorded_detail_body_carries_no_period_echo_to_assert_against`.

**W5c — an empty month writes no snapshot.** `fetch_aws.py:859-874`'s posture in its own words:
an echoed period with no usage rows raises rather than writing `totals.amount: 0.00`, because a
bill of zero and no spend recorded are different claims and only one of them is true. The
inventory is still written. The fixture is a real month (`2025-01`), not a synthesised one.

### The prompt's W5 premise, corrected against live behaviour

The prompt states the API *"returns HTTP 200 with an empty array for a month that predates the
data, AND returns January's data for month=13"*. Both are true of the **detail** endpoint and
neither is true of the **summary** one:

| request | summary endpoint | detail endpoint |
|---|---|---|
| `month=13` | **400** `Invalid date specified.` | **200**, 509 items, every one dated `2026-01` |
| `month=0` | **400** `Invalid date specified.` | — |
| `year=2019` | **400** `Time period cannot be more than 2 years in the past.` | **200**, `usageItems: []` |
| `2025-01` (real, empty) | **200**, period echoed, `usageItems: []` | **200**, `usageItems: []` |

**This strengthens W5a/W5b rather than weakening them.** The hazard is real and it lives on the
endpoint that carries no echo — and the detail endpoint is fetched on every run, so an
unvalidated period would reconcile one month's summary against another month's detail. D7's
ground says *"an out-of-range month is otherwise indistinguishable from an empty one"*; live,
that is true of the detail endpoint and false of the summary one. **D7's conclusion is
unaffected and if anything better supported** — the asymmetry is exactly why the summary
endpoint is the source. Reported rather than edited: W8 authorises one clause on D7 and no other
change to it.

---

## W6 — the inventory: Copilot seats as `TYPE_SEAT`

`GET /orgs/{org}/copilot/billing/seats`. Every first-class field is emitted, with `null` where
the concept is absent — never by omission.

| Field | Value | Ground |
|---|---|---|
| `resource_id` | `str(assignee.id)` | The numeric id is immutable; the login is a display name its owner can change. Keying on the login would make a renamed user look like one resource that vanished and a different one that appeared, in a report whose month-on-month section is built on exactly that comparison |
| `type` | `TYPE_SEAT`, imported | C1 |
| `name` | `assignee.login` | the human-facing identity field the schema asks for |
| `region` | `null` | no concept |
| `size` | `plan_type` (`"business"`) | C13 carry-only human label — sorting, comparing, summing, branching and joining on it are foreclosed |
| `state` | **`null`** | §S2 below |
| `created_at` | `iso_utc(created_at)` | provider's own, normalized |
| `last_activity_at` | `iso_utc(last_activity_at)` | **the first non-null instance of this field in the pipeline's history** |
| `attached_to` | `f"user:{login}"` | C7 single opaque string; prefixed-marker grammar |
| `monthly_cost_estimate` | `money(pricePerUnit × (netQuantity / seats))` | D4; see §C14 |
| `tags` | `[]` | GitHub exposes none for seats — the empty form, not omission |
| `raw_ref` | `github://orgs/{org}/copilot/billing/seats/{id}` | provider-shaped provenance |

**`last_activity_at` is populated, and it is the first time.** The field has existed since m1 and
is `null` in all seventeen normalizers across the three predecessors. All six recorded seats
carry a value. t3's rule is the first in the catalog to key on an activity timestamp rather than
an age, and this is what makes it possible.

**Timestamps are normalized to UTC `Z`, unlike the predecessors' pass-through.** GitHub states
seat timestamps at the account's own offset — `+05:30` on this organisation — where §Normalized's
example is `Z`. DO and Linode pass provider ISO strings through untouched because theirs already
end in `Z`; AWS normalizes because boto3 hands it `datetime` objects. This is the third case:
the string is ISO but not in the schema's spelling, and t3 will compare it against a reference
date. `iso_utc` uses `_normalized.parse_timestamp` + `iso`, so the conversion is the shared one.

**`attached_to` is never null, and that is deliberate.** C7 makes `null` the universal idle
signal keyed by four rules; a seat assigned to somebody is not idle, and an *unexercised* one is
t3's business by way of `last_activity_at`. The `user:` prefix follows the grammar
`fetch_do.py:431` (`tag:`) and `fetch_linode.py:835/845` (`<entity type>:`, `unknown:…`) already
use, and it is what stops C7's `attached_to`-against-`resource_id` join from matching a person
to a resource that happens to share the number.

**Only Copilot seats are emitted.** Organisation members are not: the live `/orgs/{org}/members`
read returns 15 rows carrying `login` and `id` and **no** activity field and **no** per-instance
cost, failing two of D6's three legs. `/orgs/{org}/copilot/billing`'s `seat_breakdown` (live:
`{total: 6, active_this_cycle: 6, inactive_this_cycle: 0, pending_invitation: 0,
pending_cancellation: 0, added_this_cycle: 0}`) is a class-level figure; **no resources are
synthesised from it**, and the adapter does not call that endpoint at all. All four exclusions —
members, Actions artifacts, Actions caches, packages — are carried in `EXCLUSIONS` with their
reasons and emitted in the run summary, because an excluded class is an exclusion and never an
absence.

---

## S2 — `state` is null, and the seat lifecycle signal is carried nowhere

**Ruled by the reviewer (V1) after this session reached the stop condition S2c.** t2 emits
`state: null` and carries `pending_cancellation_date` nowhere. No canonical state value, no new
field, no widened key set, and `cloudcost/milestone.md` §Normalized schemas untouched (V4).

**Why `state` is null rather than derived.** The seat object carries no lifecycle field at all —
its complete property set is `{created_at, assignee, pending_cancellation_date, plan_type,
last_authenticated_at, updated_at, last_activity_at, last_activity_editor}`. §Normalized's rule
for a concept the provider lacks is a `null` value, never omission. Deriving
`active`/`pending_cancellation` from `pending_cancellation_date` would be this adapter **minting
a state vocabulary locally**, which is seam #1 with `state` standing where `type` stood;
§Normalized says other states *"pass through as the provider reports them; the moment a rule
needs one, it is enumerated here first"* — enumerated in the schema, not invented in an adapter
— and m6 t1's *Do not generate* already forbade a canonical seat state. `plan_type` was
considered and rejected on a simpler ground: it is a tier, not a lifecycle position, and W6
already assigns it to `size` as a C13 carry-only label. One field cannot mean two things.

### The enforcement evidence, recorded so t3 does not re-derive it (V3)

The question S2a asked was whether §Normalized's **inventory** shape admits a `provider_extra`
at document level, resource level, both, or neither. Established by reading; the answer is
**neither**.

| Where | What it says |
|---|---|
| preamble, `milestone.md:176` | *"Provider-specific payload lives under `provider_extra`, which downstream scripts must **not** key on generically."* — general, governing the section |
| cost snapshot example, `:197` | carries `provider_extra` at document level |
| cost bullets, `:218`, `:222` | describe it, cost-shaped throughout |
| **inventory example, `:227–238`** | **five document keys and no `provider_extra`; its resource carries the twelve fields and no `provider_extra`** |
| **inventory bullet, `:241–243`** | *"Every resource carries, first class: resource_id, type, name, region, size, state, created_at, last_activity_at, attached_to, monthly_cost_estimate, tags, raw_ref."* |

All four occurrences of `provider_extra` in `milestone.md` are the preamble and the cost
snapshot. The inventory half of the section mentions it nowhere.

**The enforcement is stronger than the prose — exact set-equality, not containment:**

- **resource key set, all three adapters**: `test_fetch_aws.py:117, 157, 218, 229, 892`;
  `test_fetch_do.py:346`; `test_fetch_linode.py:911`
- **inventory envelope, two of three**: `test_fetch_aws.py:889` and `test_fetch_linode.py:909`,
  both `set(inventory) == {"provider", "account", "period", "resources", "generated_at"}`
- `fetch_aws.py:760-763` records the envelope as *"frozen at five keys"* in source
- the only consumer reads it off a **cost** document: `compose_report_data.py:657`,
  `cost.get("provider_extra")`. Nothing reads `provider_extra` off an inventory

**The ruling's ground.** Extending the inventory shape is a high-blast-radius change to a pinned
seam — the same class as the canonical type set, which m6 deliberately gave its own ticket
**ahead of** the adapter precisely so it could not be smuggled in as something the adapter did on
the way past. Doing here what t1 refused to do there would make the reason t1 exists incoherent.
At resource level it would make GitHub the first provider diverging from a key set three adapters
pin as `==`; at document level it breaks no test only because every existing test is
provider-scoped, so GitHub's envelope would silently differ from the other three's with nothing
asserting against it — worse than a red test, not better. Either way it is an adapter declaring
its own shape, which is C1's anti-pattern applied to shape rather than to vocabulary.

**Nothing is lost, and this says so rather than implying it (V2).** The committed fixture
captures the **whole** seat object, so t3 can read `pending_cancellation_date`'s shape without
re-fetching, and the live API still carries current lifecycle state for any future run. What is
deferred is carrying it *through the pipeline*, not knowing it exists. The signal is also not
yet load-bearing: all six live seats carry `pending_cancellation_date: null`, so the false
positive it would prevent — flagging an already-cancelled seat as recoverable waste — is
**unreachable today**. That is the contracts' settled form for exactly this case: recorded, not
filed, with the obligation stated for the provider that first exhibits it.

### For t3, plainly (S3)

1. `state` is `null` on every seat, and the adapter will not derive one.
2. The lifecycle signal is carried **nowhere** in the pipeline. It is in the fixture and in the
   live API, and nowhere else.
3. **The reopening condition:** if t3's rule needs a lifecycle signal to avoid flagging an
   already-cancelled seat, the inventory shape change lands as **its own ticket ahead of t3**,
   the way t1 landed ahead of t2. It is not t3's to do on the way past either. And if t3 needs a
   canonical *state value*, §Normalized schemas is where it is enumerated first — not the rule
   and not the adapter.

---

## C14 — this adapter's cost model, asserted in its own tests

GitHub's model is neither of the two the census already records. DO bills a droplet whether it
is on or off; AWS bills no compute for a stopped instance. A seat is neither: it is an
**entitlement**, it bills for as long as it is assigned regardless of whether anyone uses it,
and its price is **not derived from a rate table at all**. It is read off the organisation's own
bill — the summary endpoint's `copilot_for_business` row — and divided across the seats that row
is charged for.

`test_a_seat_costs_what_the_organisations_own_bill_says_it_costs` checks the derived figure
against that billed line rather than against a constant: `19.0 × (5.999999904 / 6)` =
`18.999999696` → `19.00`, and `19.00 × 6` = `114.00`, which is `money(netAmount)` of the row.

**The obligation C14 leaves standing is met trivially, and it is worth saying why rather than
leaving it as an absence.** C14: *"only separately-inventoried storage is summed"* — a provider
that inventories storage separately **and** folds its cost into the instance's estimate would be
double-counted, and nothing detects it. This adapter inventories **no storage of any kind**, so
nothing it emits can be double-counted against a folded-in cost. Recorded as met, not as
inapplicable.

**Never an invented figure.** An absent `copilot_for_business` row, a zero seat count and a
price-less row each yield `0.00` plus one named, deduplicated warning ending *"the figure is
unknown, not zero"*. The `business` plan's list price is public and reaching for it here would
be exactly the fabrication the milestone forbids —
`test_a_billing_failure_leaves_seats_priced_zero_and_says_so_rather_than_guessing` drives that
through a real 500 on the billing endpoint and asserts every seat prices at `0.0`.

**D4, and the assertion that actually pins it.** The multiplication happens once, on unrounded
operands, with `money()` applied to the result. The test uses a rate whose two-decimal rounding
is **lossy** — `0.00033602`, a real GitHub unit price — so the two orders give genuinely
different answers: multiply-first gives `50.40`, round-first gives `0.00`. Asserting only against
the live `19.0` rate would have passed under either order and proved nothing.

---

## W7 — fixtures, the scrub class, and the mutation work

**The fixture convention, established by reading and reported.** Flat files in
`cloudcost/tests/fixtures/`, no subdirectories, stem
`{provider}_{surface}[_{variant}][_pageN].json`, loaded only through `conftest.load_fixture`
(bare stem, no `.json`). `_comment` is the **first key**, carrying what the fixture proves —
introduced at m2 and applied forward, which is why DO's m1 fixtures lack it and these carry it.
HTTP is **never** monkeypatched: a real `ThreadingHTTPServer` serves the fixtures and records
what was sent, which is what makes the credential guards assertions about the wire rather than
about test wiring. `GitHubStub(DOStub)` overriding `api_base`, exactly as `LinodeStub` does.

**One fixture cannot carry `_comment` and is exempted by name.** `/user/orgs` answers with a bare
JSON array, and the stub replays a fixture verbatim as the response body — a wrapper object would
change the shape the adapter parses, which is the one thing a recording must not do.
`LIST_BODIED_FIXTURES` names it; the test is not weakened to containment.

**Six fixtures, all captured live, none hand-written.** `github_billing_usage_summary`,
`github_billing_usage_detail`, `github_billing_usage_summary_empty`,
`github_billing_usage_detail_empty`, `github_copilot_seats`, `github_user_orgs`.

**The detail fixture is kept whole at 255 rows (92 KB), deliberately.** The reconcile test sums
every row against the summary's own total, so a trimmed capture would not reconcile and would
prove nothing. Its `_comment` says so, because a large fixture with no stated reason reads as
carelessness.

### T2 — determinism, and where the two recorders differ

`record_aws_fixtures.py` scrubs by substituting a **single literal** (`\b\d{12}\b` →
`111122223333`). Stable, and right for an account id, of which there is one — but it collapses
distinct values onto one, which here would make six seats belonging to six people into one
person and every relational assertion vacuous. `record_linode_fixtures.py` uses a `Scrubber`
with **stable, first-seen-order** assignment and states the guarantee: *"re-recording the same
account produces byte-identical fixtures except where the account itself changed."*

**This follows Linode's**, and the difference from AWS's is deliberate and recorded here rather
than left to be rediscovered. Verified rather than asserted: two independent recordings, run
back to back into separate directories, are **byte-identical** (`diff -rq`, no differences).

### U2 — the scrub class, defined rather than enumerated

**This is the boundary this provider establishes**, and it is written here because Google
Workspace and the AI providers are the same consumption class and will hit the same question.

**Scrubbed** — anything identifying the account, the people in it, or its internal structure:
organisation (`organization`, `organizationName`), repositories (`repositoryName`), logins,
display names, numeric user and organisation ids, `node_id`, profile and avatar URLs, every one
of the fifteen `*_url` fields, email addresses, and any token-shaped string.

**Not scrubbed, because these carry the tests' meaning:** monetary figures, `product` / `sku` /
`unitType` strings, quantities, timestamps, and the period fields.

**The class binds this document, the tests and the packet — not only the fixtures.** Recorded
because it was got wrong once and caught by the packet's own leak check rather than by reading:
an earlier draft of these notes named the organisation in its gate (vii) heading, and the M17
description below quoted a **real** user id in full while explaining that the recorder had left
it standing. `test_fetch_github.py`'s scrub self-check carried the same real id as its planted
decoy. All three were replaced before this commit landed — the organisation is named nowhere in
the repo, the notes say `<real-id>`, and the test plants `77777777`, which stands for a real id
without being one. A decoy does not need to be genuine to prove a guard fires, and a class that
covers committed recordings but not the prose describing them is not a boundary.

**Examined and placed in neither class:** `last_activity_editor`
(`vscode/1.132.1/copilot-chat/0.60.0`) is a tool version, not an identity — kept. The `+05:30`
offset on seat timestamps is retained because it is the exact shape `iso_utc` must convert, and
a test asserts the fixture still carries it.

Repository and organisation names are **not** human identities and the prompt's list did not
reach them; the reviewer ruled (U1) that Linode's wholesale account-identity posture governs,
and that the cost of scrubbing them is zero — D7 declined per-repo attribution, so no test keys
on a repository name and the reconcile test sums across all rows without reading one.

**Verified, not asserted.** Twenty-one real identifiers taken from the unscrubbed live captures
were searched for across every recorded fixture, with node ids base64-decoded first: **none
survives**.

### The two defects this ticket's own verification caught

Both are recorded because each is the failure mode the t1 hazard section describes, and each was
found only by running the mutation rather than by reading the code.

1. **The scrub let a real id through, base64-encoded.** A node id is base64 of `04:User<id>`.
   The first `_node_id` rewrote the **first run of digits** — the `04` type prefix — leaving
   `10000001:User<real-id>` with the real id intact inside a value that a plain-text sweep reads
   as opaque, and that sweep reported clean. Fixed to target the id, with a guard that drops the
   node id entirely if the real id still appears after substitution.
2. **The scrub-verification test then failed to catch a planted version of exactly that.** It
   decoded node ids, appended the plaintext, and checked the result for token shapes and emails
   — but never for a *number*. A planted real id passed. The check is now the
   internal-consistency one: a node id must decode to a string carrying its own object's `id`
   and no other number beyond the type prefix. Under the planted mutation it now fails; a
   control on the unmutated fixtures passes.

The second of these is the sharper one: the test's own docstring claimed decoding was the point
of it, and the decoding was real while the check on the decoded value was absent. That is
**Silent-wrong-answer one level in**, in the same shape t1 recorded — a check runs, and the
check under test does not.

### The mutation exercises (the t1 hazard procedure)

t1's hazard is about `test_detect_orphans.py:840`'s short-circuiting `==`. **This ticket adds no
canonical type and touches that function not at all**, so the specific hazard is not engaged —
but the *procedure* binds every new assertion, and it was applied to all of them.

Nineteen mutations, each applied to the adapter or a fixture, each run against the single test
that should catch it, each restored with the restore verified as its own claim. Controls on both
sides: the mutated text absent before and present after the edit, and the adapter's sha256 after
the final restore identical to the pristine snapshot (`c038d6d78c70`).

| # | Mutation | Test | Verdict |
|---|---|---|---|
| M1 | `RECONCILE_TOLERANCE` → 1000.0 | reconcile gate FIRES | failed at the right assertion |
| M2 / M2b | `assert_period_echo` → no-op | mismatched / missing echo | both failed |
| M3 | empty-month raise removed | empty month writes no snapshot | failed |
| M4 | round the rate before multiplying | D4 multiply-then-round | failed (`0.0 == 50.4`) |
| M5 | `load_token` falls back to `GITHUB_TOKEN` | credential refusal | failed |
| M6 | derive `state` from `pending_cancellation_date` | seat state is null | failed (`'active' is None`) |
| M7 | key `resource_id` on the login | immutable id, not login | failed |
| M8 | `attached_to` → `None` | prefixed marker, never null | failed |
| M9 | `usage_qty` ← `grossQuantity` | amount and qty both net | failed (`806.0 == 0.0`) |
| M10 | sum the rounded amounts | total full-precision | **PASSED — see below** |
| M11 | pass timestamps through unnormalized | normalized to UTC Z | failed |
| M12 | add `GH_CONFIG_DIR` to the shadow list | shadow list is gh's own | failed |
| M13 | currency sweep → no-op | currency field warns | failed |
| M14 | org discovery picks the first | discovery refuses to choose | failed |
| M15 | period validation → no-op | rejected period costs no request | failed |
| M16 | plant an unpseudonymised login | fixture scrub | failed |
| M17 | plant a real id inside `node_id` only | fixture scrub | **PASSED — see above** |
| M18 | remove a `_comment` | fixtures document themselves | failed |
| M19 | plant a real id in the `id` field | fixture scrub | failed |

**M10 is the third self-caught defect, and it is worth its own paragraph.** The first version of
`test_the_total_is_summed_at_full_precision_and_rounded_once` asserted only against the recorded
month — and that month's five rows total `134.0` under **either** order, so the test passed
cleanly under the very mutation it names. An assertion shipped having never been executed against
a failing state, in a test whose whole subject is rounding order. It now pins the order on a
constructed set where the two answers differ (three rows of `0.004`: `0.01` summed-first,
`0.00` rounded-first), and keeps the fixture beside it as the live-value check it actually is.
Under M10 it now fails at `assert 0.0 == 0.01`.

After all restores: `test_fetch_github.py` **54 passed**, and the adapter is byte-identical to
its pre-mutation state.

---

## W8 — the D7 clause

D7 was quoted at HEAD (`m6-github.md:66–73`, the whole list item including its backticked
ground, bounded by the blank lines around it) and the unit replaced — §11's quote-then-replace,
not a scope-by-naming. One clause appended inside the existing ground; no new decision line, no
change to the decision sentence, wrapping at ~72 columns hanging-indented two spaces to match
D1–D6.

Added: *"Per-repo Actions attribution was available and is declined: the detail endpoint carries
a repository the summary does not, Copilot spend is repo-attributable under neither, and the
field stays on the detail endpoint if it is ever wanted."*

**Verified live before writing**, rather than transcribed from the prompt: the detail endpoint
attributes `actions` spend across **8 distinct `repositoryName` values**; every `copilot` row
carries `repositoryName: ""`; and the summary endpoint has no such field at any depth.

---

## W9 — the runbook

`### GitHub` landed as a fourth `###` subsection under `## Prerequisites`, after `### Linode`
and before the closing *"The credentials gate only the live steps…"* line. The three existing
subsections are **not uniform in depth** — DO one bullet, AWS two, Linode eight — so depth
follows content, and GitHub's is Linode-shaped: two credential classes, a credential file, and a
permission set.

**The permissions were read off the API, not inferred.** GitHub states the permission each
endpoint accepts in an `x-accepted-github-permissions` response header:
`organization_administration=read` on both billing endpoints, and
`organization_copilot_seat_management=read; organization_administration=read` on the seats
endpoint. The runbook records both and recommends granting Copilot Business rather than leaning
on Administration for both, so the inventory survives a later narrowing of the billing grant.

The subsection also carries one thing the other three do not need: **GitHub is unwired until
t2b**, so `CLOUDCOST_PROVIDER=github` selects nothing and the adapter is invoked directly. Stated
so the absence reads as a boundary rather than as a defect.

---

## The repo-root output hazard, fixed here (X1)

**The defect.** All four adapters default `--output-dir` to the bare string `"output"`, which
resolves against the **current working directory**. Run from a use-case directory that is where
the per-use-case `.gitignore` covers it; run from the repo root — which is what this ticket's
own done-check command does — it lands at the repo root, where until this commit **nothing
ignored it**. `git status` reported `?? output/` over a directory holding the real monthly bill
and, for GitHub, six real people's logins.

**The hazard predates this adapter and is common to all four.** `fetch_do.py`, `fetch_aws.py`
and `fetch_linode.py` carry the identical `parser.add_argument("--output-dir", default="output")`
and have since m1; none of them is at fault and neither is this one. What changed at m6 is only
the *consequence*: GitHub is the first provider whose inventory carries human identities, which
moves an untracked directory of JSON from untidy to a disclosure one `git add -A` wide. **A
later reader should not conclude this was a GitHub problem** — the fix is repo-wide and the
adapter that surfaced it is incidental to it.

**The fix**, `.gitignore:26–27` at the repo root:

```
# Adapter output landing at the repo root (--output-dir defaults to "output")
/output/
```

**Why that spelling.** The root file's convention is *anchored* paths — `api/.env`,
`docs/.sections/`, `payslip/output/runs.log`, `rig/node_modules/` — anchored because each
contains a separator, with directories carrying a trailing `/`. A single-component root-level
directory needs a **leading** slash to get the same anchoring, so `/output/` is that convention
applied rather than a departure from it. `cloudcost/.gitignore`'s `output/*` + `!output/.gitkeep`
spelling was **not** imported: that form exists to keep a `.gitkeep` tracked inside an otherwise
ignored directory, and there is no `.gitkeep` here to keep. A **bare** `output/` was rejected as
over-broad — with no separator it would match a directory of that name at any depth, reaching
into six use cases that already govern their own.

**Verified as a paired control**, with the directory identical on disk and only the rule
differing: `?? output/` present with the entry backed out, absent with it restored, and each
use-case output directory still resolved by its own `.gitignore` rather than by the new entry.

**Nothing leaked.** Verified explicitly rather than left to inference: commit `4df0672` touches
thirteen files, all under `cloudcost/`, none an artifact; neither `github_costs_2026-07.json`
nor `github_inventory_2026-07.json` appears anywhere in its tree; and repo-root `output/` has
never been tracked in any commit on any branch (`git log --all -- output/` → 0 commits).

## D7's ground, corrected (X2)

SURPRISE 2 reported that D7's ground was imprecise and did not edit it, W8 having authorised
one clause and no other change. The reviewer directed the correction at review. Quote-then-
replace on the whole list item; **only** the indistinguishability sentence changed, and the
decision sentence, the reconciliation ground and the W8 per-repo clause were each verified
word-identical against `4df0672` afterwards rather than assumed untouched.

The sentence said an out-of-range month is *"otherwise indistinguishable from an empty one"* —
true of the detail endpoint, false of the summary one, which answers 400 to `month=13` and 400
to a year beyond retention. It now attributes the hazard to the detail endpoint and names the
summary endpoint's rejection as the asymmetry the decision rests on. D7's conclusion is
unchanged and better supported than the old sentence claimed.

**The dated correction marker was added at r2 (Y1–Y4), having been withheld at r1.** The r1
reasoning was that *"change nothing else"* excluded a marker, with the choice recorded here so
it could be overruled cheaply. It was, and the ground it missed is the one that decides the
form: **D7's imprecise ground was published, not merely committed.** It landed at m6 t1 in
`e4fabb7`, which is on `origin/main`, so this corrects text that has been read from the remote.
An unpushed draft is simply rewritten; a published ground that was wrong records that it was.

**Which precedent, and why not the other.** Two were in view. D3 in this document carries its
provenance woven into the ruling sentence — *"Ruled by the arbiter 2026-08-13, replacing a draft
whose stated ground was false"* — which reads as a correction made **at ruling time, before
publication**, and cannot express a later dated correction without conflating the two dates.
`cloudcost/milestone.md` carries the wider precedent for published text: C1's
`` `[Corrected 2026-08-11 at the exercise sweep, one commit after landing at a690014, …]` `` and
C4's `` `[Discharged 2026-08-10 at m5 t2. …]` ``, each a bracketed dated clause in its own
backticked span, appended after the text it governs. That is the form D7 takes, compressed from
their paragraph scale to a clause per R25 — a ruling earns no rationale block, and a correction
to one earns less:

```
`[Corrected 2026-08-13 at t2 r1: the indistinguishability sentence was wrong
as published at e4fabb7. The conclusion is unchanged.]`
```

It states the date, what was corrected, and that the conclusion stands. It says nothing about
which endpoint does what, because the corrected sentence two lines above it now does.

**The Y3 check was re-run and is stronger than X2's**, covering four units rather than three —
the decision sentence, the reconciliation ground, the **corrected asymmetry sentence** and the
W8 per-repo clause, all word-identical to `40f05fd`. And in its strongest form: the new D7 with
the clause removed is byte-identical to the old one, so the added clause is provably the *only*
change. That check caught a silent falsification once in this edit's first attempt; it earned
its second run.

## SURPRISES

1. **W5's month=13 / empty-month premise is true of the detail endpoint, not the summary one.**
   Full table in §W5 above. Strengthens the obligation rather than weakening it.
2. **D7's ground sentence is imprecise in the same way**, and its conclusion is unaffected.
   Reported, not edited — W8 authorised one clause and no other change.
3. **C4 contains no phrase "known weakness"**; the word does not occur in `milestone.md`. §W4
   records what it does say.
4. **§Adding a provider is `runbook.md:567`, not `milestone.md`** — the heading returns zero
   hits there.
5. **The detail endpoint ignores `per_page`** — 255 items with and without it, and no `Link`
   header. Unpaginated; no pagination loop was written speculatively for it.
6. **The ticket's own done-check command deposits real billing data into an unignored
   directory.** `python3 cloudcost/scripts/fetch_github.py --period 2026-07`, run from the repo
   root as written, resolves `--output-dir`'s default `"output"` against the **repo root**, not
   against `cloudcost/`. `cloudcost/.gitignore:6` ignores `output/*` only within `cloudcost/`, so
   the run creates an untracked, **unignored** `output/` at the repo root containing the real
   monthly bill and — for GitHub, uniquely — real people's logins. `git status` showed `?? output/`.
   The directory was removed and the run repeated with `--output-dir cloudcost/output`, which is
   the form the new runbook section documents. **This is not GitHub-specific** — all four
   adapters default the same way — but GitHub is the first whose inventory carries human
   identities, which sharpens it from untidy to a disclosure risk one `git add -A` wide.
   **Fixed here at the reviewer's direction (X1), not filed** — see §The repo-root output
   hazard below. A finding fixed in the commit that surfaced it is not deferred, so the
   deferred-finding rule has nothing to bite on.
7. **`conftest.py:724` carries a dead `return aws_stub`** after `full_linode_stub`'s own
   `return` — pre-existing, unreachable, harmless. Left untouched as unrelated to this ticket.

## UNREAD

None. Every contract ref named by the ticket was read at HEAD before use: `milestone.md`
§Normalized schemas and C1/C4/C7/C10/C13/C14, `m6-github.md` D1/D3/D4/D6/D7 (and D2/D5 in
passing), `m6-t1-implementation-notes.md`'s hazard section, `runbook.md`'s three provider
subsections and §Adding a provider, and
`../aetheris/docs/methodology/milestone-methodology.md` §6 and §11.

The one thing this ticket did **not** establish, and states as unestablished rather than
inferring it: whether any *other* organisation's Copilot seat object carries a lifecycle field.
The finding is about this organisation's six seats. `record_github_fixtures.py`'s findings report
prints `seat_fields_present` on every recording, so the next capture answers it without anyone
having to remember the question.

---

## Done-check

All three run in full at r0. Output quoted verbatim in the review packet.

**At r1 (X1/X2) and again at r2 (Y1–Y4) only pytest was re-run, and each is an exemption with
a stated ground rather than a waiver — stated in full both times rather than the second
back-referencing the first.** Between them the amendments touch a `.gitignore` entry, a prose
clause in a milestone document, a dated correction clause beside it, and this record; **no `.py`
file is touched in either round**, so neither the live smoke run nor the sprint can observe any
of it. The distinction is the one t1 drew and is checkable rather than
assumed: at t1 the sprint *was* re-run for a change to a Python **comment**, because the file
was executable and the sprint loads it. The r1 diff contains no executable file of any kind
(three paths: `.gitignore` and two markdown documents), and **the r2 diff is one markdown file**
— `cloudcost/m6-github.md`, plus this record of it. `git diff --stat` over each is the
truth-maker, and both are quoted in the packet.

- `python3 -m pytest cloudcost/tests/ -q` → **440 passed**, exit 0. The 386 t1 recorded, plus
  54 new. No existing test was modified.
- `python3 cloudcost/scripts/fetch_github.py --period 2026-07` → exit 0, `status: ok`,
  5 line items, 6 resources, `totals.amount 134.0`, reconcile `reconciled` over 255 detail items
  at a difference of `-2.842170943040401e-14`. Artifacts:
  `cloudcost/output/github_costs_2026-07.json` (3 870 bytes) and
  `cloudcost/output/github_inventory_2026-07.json` (2 733 bytes).
- `./scripts/sprint.sh cloudcost` → exit 0, **23 `[OK]` · 0 `[FAIL]` · 0 `[WARN]`**, 76 lines —
  identical to the figures t1 recorded.

**The rule-legibility arm, byte-identical across the change.** The arm is non-blocking by
construction — its failure path increments a counter and does not halt — so the green summary is
not what is being relied on. The **before** capture was taken against a genuinely clean tree
(`git stash push -u`, verified at `e4fabb7` with `fetch_github.py` absent), and the stash was
popped and the restoration verified before the after capture:

```
BEFORE: [OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set
AFTER : [OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set
```

`diff` of the two lines reports no difference. A whole-run `diff` of the two captures (ANSI
stripped) differs **only** in the sprint's own output-directory timestamp, its provenance and
console-log paths, the artifact `ls` timestamps and the run id — that is, in nothing that is not
a clock or a nonce. GitHub emits nothing into that path yet: it is unwired, the sprint still
runs DigitalOcean, and the arm reads the DO inventory.
