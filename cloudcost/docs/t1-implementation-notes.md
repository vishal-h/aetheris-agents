# t1 — cloudcost scaffold + DO adapter (`fetch_do.py`) — implementation notes

**Ticket:** m1-cloudcost §t1. **Built:** 2026-07-27.
**Deliverables:** `cloudcost/` scaffold, `scripts/fetch_do.py`, `tests/` (**25** tests, offline
— 23 at first submission; two shadow-guard tests were added in review and this line was not
chased. Corrected at t3, where the stale 23 was quoted into a packet: `t3 review r0 F1`),
`tests/fixtures/do_*.json`, `.gitignore`, `requirements.txt`.

---

## Decisions

**`requests`, not `pydo` — and the fallback clause does not apply.** §t1 Contract refs says
"`pydo` (confirm its billing-endpoint coverage; fall back to `requests` for any endpoint it
doesn't expose)". Coverage was confirmed rather than assumed: in a throwaway venv, `pydo`
0.39.0 exposes `balance.get`, `billing_history.list`, and
`invoices.list / get_by_uuid / get_summary_by_uuid`, plus every inventory type. So pydo covers
everything and the stated fallback trigger never fires. `requests` was still chosen, on three
grounds: (a) §t1 requires pagination, retry and rate-limit handling to *live in the adapter* —
pydo's azure-core transport carries its own retry policy underneath, which would make the
adapter's own layer partly untestable; (b) §Prerequisites 3 is satisfied by what the harness
environment actually has — `requests` 2.34.2 is installed, `pydo` is not, so choosing pydo would
introduce an install step the ticket does not ask for; (c) a plain HTTP client lets the offline
suite assert on the real outgoing `Authorization` header, which is what makes the shadow guard
an assertion rather than a mock inspection. D6 sanctions either client. Reversible: the choice
is confined to `DOClient`.

**Auth is explicit, and the shadowing risk is inverted from the doc's framing.** The token is
read from `CLOUDCOST_DO_TOKEN` by `load_token()` and passed to `DOClient`, which sets the
`Authorization` header itself. `DO_TOKEN` / `DIGITALOCEAN_ACCESS_TOKEN` are never read. Beyond
that, `warn_shadowing_env()` *names* any stray DO token found in the environment (never its
value) on stderr, so the shadow condition is visible instead of silent. Note the milestone's
mechanism claim is only half right — see Deviation 1.

**Cost is service-granular by construction (D4).** Line items come from the invoice summary's
`product_charges.items[]`, which is exactly service-level. Every line carries
`resource_id: null` and `region`/`usage_qty`/`usage_unit: null`. DO returns *repeated* rows for
one service (three separate "Kubernetes Clusters" rows on the live invoice); these are
aggregated to one line per service, which preserves the total (168.50 + 3.71 + 0.00 = 172.21 =
invoice amount) and matches what "totals by service" needs downstream.

**Resource dollars are estimates, and only one of them is real.** Droplets use the API's own
`size.price_monthly` — exact. Volumes ($0.10/GiB), snapshots ($0.06/GiB), unassigned reserved
IPs ($4.38/mo) and load-balancer nodes ($12/24/48 by size) are list-price constants in one
labelled block at the top of the script. The volume rate was cross-checked against a real
invoice line (1 GiB volume, 624 h, $0.09 → $0.107/mo full-month); the other three are
unverified list prices and should be spot-checked against an invoice at t3. Live sanity: the
estimate sums to $182.50 against an actual invoice of $172.21 — the right order, not a
reconciliation.

**A tag-targeted load balancer is not unattached.** DO load balancers select backends either by
explicit `droplet_ids` or by `tag`. A tag-targeted LB has an empty `droplet_ids` but is fully in
service, so `attached_to` falls back to `tag:{tag}` before it falls back to `null`. Emitting
`null` there would false-positive t2's idle-LB rule, and — because the normalized schema freezes
at m1 — the signal could not be recovered downstream: the tag would already be gone. Covered by
`test_tag_targeted_load_balancer_is_not_reported_unattached` and a dedicated fixture
(`lb-tagged-1`: `droplet_ids: []`, `tag: "web"`).

**`state` for volumes is derived, not read.** The `/volumes` response has no status field
(confirmed against the live response keys), so state is `attached` / `available` from
`droplet_ids`. **`attached_to` for snapshots** is the source `resource_id`, not null — a
snapshot is *associated* with what it was taken from, and setting it null would make every
snapshot look unattached to t2's primary orphan signal. A snapshot whose source is gone
(`resource_id: null`) is the aged-orphan case, and is covered by a fixture.

**Pagination links are re-rooted onto the configured host.** DO returns fully-qualified
`links.pages.next` URLs; `_same_origin()` keeps the path and query but forces the configured
scheme/host. This stops pagination being walked to a foreign host, and is what lets the offline
suite replay recorded pages against a local stub.

**Degrade, don't crash.** A failing inventory source becomes an entry in `errors[]`; the sweep
continues, both files are still written where possible, and the run emits
`{"status": "partial"}` with exit 1. An auth failure is fatal (exit 1, no files). Covered by
two tests.

---

## Deviations from ticket text (noted, not silently followed)

1. **"`pydo`/`doctl` default to reading `DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN`" is false for
   `pydo`.** Verified, not inferred: `pydo.Client()` with no token raises
   `TypeError: token or api_key is required` — it has no env fallback at all. `doctl` does read
   `DIGITALOCEAN_ACCESS_TOKEN`, so the hazard is real for the CLI and for any hand-rolled
   `os.environ.get("DO_TOKEN")` client. The *invariant* the milestone encodes — construct the
   client with `CLOUDCOST_DO_TOKEN` explicitly, never rely on default pickup — is correct and is
   what t1 implements; only the named mechanism is over-broad. Suggested doc fix at the next
   milestone-doc touch: attribute the default pickup to `doctl` (and to default-pickup clients
   generally) rather than to `pydo`.

2. **The `import cloudcost` done-check does not test what it says, from the repo root.**
   §t1 says ``python3 -c "import cloudcost"`` should *fail*, proving the dir name is
   stdlib-safe. Run from the repo root it **succeeds** (exit 0) — Python 3's implicit namespace
   packages make any directory on `sys.path` importable, so the check reports the cwd, not the
   name. It fails correctly only from a cwd that does not contain `cloudcost/`. Both forms are
   run in the packet; the meaningful one is pinned as a test
   (`test_cloudcost_is_not_an_importable_stdlib_or_site_package`, `cwd=tmp_path`). Note the
   check would also have passed for a genuinely colliding name (`email/` → stdlib `email`
   imports fine), so from the repo root it cannot distinguish safe from unsafe at all.

3. **Additive keys on the cost snapshot — raised at t1 review, since adjudicated (closed).**
   §Normalized schemas is the frozen contract and t1 must emit "these exact shapes"; §t1's own
   done-check requires "real balance", and its Scope requires billing *history* to be fetched.
   The schema example had nowhere to put either, so the first cut emitted them as flat
   additive keys and flagged the question: additive, or nested under `provider_extra`?
   **Adjudicated: both.** The cross-provider fields are promoted to first class and the
   DO-shaped payload is nested:

   - cost snapshot, first class: `provider`, `account`, `period`, `currency`,
     `source_granularity`, `line_items`, `totals`, **`balance`**, **`generated_at`**
   - cost snapshot, `provider_extra: {}`: **`invoice`**, **`billing_history`**
   - inventory items, first class: the schema fields plus **`name`**, **`region`**, **`size`**
     (without a name the orphan section lists opaque UUIDs, against the "reviewable without
     opening the DO console" done-when)

   The split is the point: a downstream script may key on anything at the top level across
   providers, and must not key on `provider_extra` generically. Pinned by
   `test_cost_snapshot_top_level_shape_matches_the_frozen_contract`, which asserts the exact
   top-level key set rather than a subset, so a future stray addition fails the suite.
   §Normalized schemas was rewritten to match and is now the frozen contract; the doc's two
   JSON blocks were diffed key-for-key against the live emitted files and against the tests'
   assertions at every nesting level (`doc == emitter == tests`) before the doc landed, so the
   contract and the code cannot have shipped disagreeing.

---

## Fixtures

Recorded from the live account this session, then sanitized: every account/team/invoice/droplet
/volume/LB identifier replaced with a shape-valid fake, and the invoice summary's
`user_billing_address`, `user_email`, `user_company`, `user_name` **dropped entirely** (DO
returns a full postal address on that endpoint; the adapter never reads it and it must not sit
in a committed fixture). Each response is trimmed to the keys the adapter consumes plus the
pagination envelope — §t1 states the emitted-schema assertions are the contract, not the raw DO
shapes.

The live account has **0 reserved IPs, 0 snapshots and 0 unattached resources of any kind**, so
those normalizers would have been untested against a pure recording. The fixtures add clearly
marked synthetic entries: an unattached volume, an assigned + an unassigned reserved IP, an aged
snapshot with and without a live source, and a load balancer with no backends. Droplets are
split across `do_droplets_page1/page2` to exercise `links.pages.next` following. Reconcile the
synthetic entries against a real recording once the account carries a genuine orphan
(§Prerequisites 2).

---

## How the two guards are implemented (and that they can fail)

Both run against a local `ThreadingHTTPServer` stub (`tests/conftest.py: DOStub`) that serves
the recorded fixtures over real HTTP and **records every request it receives**. The adapter's
true request path — headers, pagination, retry — is exercised; nothing is mocked out.

- **Shadow guard**, both halves.
  *Presence*: `test_adapter_authenticates_with_cloudcost_token_not_the_decoys` sets
  `CLOUDCOST_DO_TOKEN` plus decoy `DO_TOKEN` and `DIGITALOCEAN_ACCESS_TOKEN` to three different
  values, runs a full sweep, and asserts the set of `Authorization` headers the stub actually
  received is exactly `{"Bearer <cloudcost value>"}` and that neither decoy appears anywhere in
  the recorded headers.
  *Absence*: `test_missing_cloudcost_token_raises_rather_than_falling_back_to_a_decoy` asserts
  that with only the decoys set, `load_token` raises rather than authenticating.
- **Leak guard**: `test_auth_failure_does_not_leak_the_token_to_stdout_or_stderr` drives a real
  401 through the CLI as a subprocess and asserts a distinctive sentinel token appears in
  neither stream, while `CLOUDCOST_DO_TOKEN` (the *name*) does appear in the error.

**Mutation-checked, not assumed.** Injecting the token into the 401 message fails the leak guard
(`1 failed`); making `load_token` fall back to `DO_TOKEN` fails the shadow guard
(`DID NOT RAISE`). Both pass again on restore. Output is in the t1 review packet.

A third guard is defence in depth: `DOClient._redact()` strips the token from any API error text
before it is raised, so a DO error body that ever echoed a credential still could not reach a
stream. The leak guard is failable independently of it (mutation 1 proves that).

---

## Open items forwarded

- **`monthly_cost_estimate` rates for volumes/snapshots/reserved IPs/LBs are list prices.**
  Only the volume rate is invoice-checked. Spot-check the rest at t3, where invoice items are
  already in hand.
- **Prerequisite 2 is unmet.** The account currently carries no orphan of any kind (0 unattached
  volumes, 0 reserved IPs, 0 snapshots). t5's "≥1 real orphan" done-when needs one planted.
- **Deviation 3 needs adjudication** — additive keys, or a nested `provider_extra`.
- **`agents/` and `data/` are empty** (`.gitkeep` only). The orchestrator lands at t5.
