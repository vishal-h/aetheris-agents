# m2 t1 — AWS adapter (`fetch_aws.py`) — implementation notes

**Ticket:** m2-cloudcost §t1. **Built:** 2026-08-01. **Revised:** r0 review, same day.
**Deliverables:** `scripts/fetch_aws.py`, `tests/test_fetch_aws.py` (**62** tests, offline),
`tests/aws_wire.py`, `tests/record_aws_fixtures.py`, `tests/fixtures/aws_*.json` (28),
`tests/conftest.py` (`AWSStub` + fixtures), `requirements.txt` (`+= boto3`).
**Suite:** 219 passed (157 m1 baseline unchanged + 62 new). **Mutations:** 28/28.

---

## Decisions

**Canonical `type` vocabulary — adjudicated during this ticket, and it is the ticket's main
finding.** `detect_orphans.py` keys every rule on `type`, and the m1 values are DO's
(`droplet`, `reserved_ip`). §Normalized schemas never enumerated them, so nothing said what a
second provider should emit — and §t2's ratified adjustments (state enum, filename prefix, RDS
rules) did not cover it. The choice was between emitting `droplet` for an EC2 instance (a
literally-unchanged downstream, but provider vocabulary sitting in shared machinery and
`droplet` printed in an AWS report) and treating `type` the way `state` is being treated.
Adjudicated to the latter: the adapter emits a **schema-level** vocabulary.

| Canonical | AWS | DO (renamed at t2 a′) |
|---|---|---|
| `compute_instance` | EC2 instance | `droplet` → |
| `static_ip` | Elastic IP | `reserved_ip` → |
| `volume` | EBS volume | unchanged |
| `snapshot` | EBS snapshot | unchanged |
| `load_balancer` | ELB / ALB / NLB | unchanged |
| `database` | RDS instance | — (new at t2 c) |
| `database_snapshot` | RDS manual snapshot | — (new at t2 c) |

t1 emits canonical **from its first line**, deliberately: t1 is the one moment the AWS
fixtures do not yet exist, so emitting DO values now and renaming at t2 would mean
re-recording fixtures created hours earlier. The consequence is that **AWS orphan detection
does not fire between t1 and t2** — the rules still key on `droplet`/`reserved_ip`. That is
harmless and is the same ordering already ratified for `state`: detection is not run
end-to-end until t3, and t2 precedes it. DO keeps working throughout.

**The seam count was wrong, and the way it was wrong is the lesson.** m1's open items call
`STOPPED_STATES` *"the one seam where a provider's own vocabulary reaches shared machinery."*
Three are now known — `state`, `type`, and the cost-model assumption below. The claim was not
false because someone mis-read the code; it was produced by **observation rather than
enumeration**, which is the harness's existing **Adjacent-case** rule (*"enumerate every site
of that exact class before filing or fixing the first one"*). The actionable output is a seam
sweep and a backlog row, not three separate fixes.

**Pricing: a static list-price block, and only the load-bearing part of it is load-bearing.**
`pricing:GetProducts` is not in the ratified read-only IAM policy (§Prereqs 1) and was not
added — that would widen the credential's surface to remove a hole that a labelled constant
already closes honestly. `AWS_LIST_PRICES` (us-east-1 on-demand) splits in two:

- **Closed, load-bearing set** — EBS by volume type, EBS snapshot, unassociated Elastic IP,
  ALB/NLB/GWLB/classic, RDS storage. Every orphan saving comes from these, and each is a flat
  well-known rate.
- **Best-effort compute** (`COMPUTE_MONTHLY`) — EC2/RDS instance classes, an open-ended table
  by nature. It feeds *running-instance display only*. An unknown type yields
  `monthly_cost_estimate: 0.0` plus a `warnings[]` entry naming the type — never an invented
  figure. Because it is non-load-bearing, the open-endedness cannot threaten the headline.

This keeps **BL-071** meaningful: there is a labelled figure for a resource-level bill to
spot-check against, which is the whole point of deferring it.

**A stopped instance bills no compute, and that belongs in the adapter.** DO bills a droplet
whether it is on or off; AWS does not bill a stopped instance's compute, only its storage —
which the inventory already carries on the volume rows. So `instance_compute_estimate(...,
stopped=True)` returns `0.0`, and a stopped RDS instance's estimate is storage only. The
alternative — leaving the running rate on the resource and teaching
`rule_stopped_droplet_with_attached_storage` a per-provider cost model — would have put a
third provider assumption into shared machinery. Under D5 the adapter owns its provider's cost
model, so the seam dissolves rather than moving. **t2 still owes the other half**: the rule's
saving must sum the attached storage, which is m1's own forward (`detect_orphans.py:250` —
*"attached storage is named but not summed (m1)"*). That is structural, not a rule edit:
`score()` derives `monthly_saving_estimate` uniformly from `resource["monthly_cost_estimate"]`
for every rule and `fired()` carries no saving, so `fired()` gains an optional saving and
`score()` honours it.

**`AWS_PROFILE` had to be neutralized for decision C's "suspenders" clause to be true.**
Verified on boto3 1.43.14: with `AWS_PROFILE` naming a profile that does not exist,
`boto3.session.Session(aws_access_key_id=…, aws_secret_access_key=…, region_name=…)` raises
`ProfileNotFound` from `get_scoped_config` — **before** it looks at the explicit credentials it
was handed. The operator's workstation legitimately carries `AWS_PROFILE`, so without the fix
a run supplying a perfectly good read-only key would die. The fix is one kwarg:
`botocore.session.Session(session_vars={"profile": (None, None, None, None)})`. It fails loud
rather than silently, so it was never a correctness hazard — but the milestone states the
adapter needs no launch hygiene to be safe, and for that arm it did. See Deviation 1.

**The offline seam is a local HTTP stub reached through `--endpoint-url`, not `Stubber`.**
`botocore.stub.Stubber` registers on `before-call`, and `botocore/client.py` returns the
stubbed response before `_make_request` — endpoint resolution and SigV4 signing never execute,
so there is no credential on any wire to assert against and the poison guard cannot be
expressed at all. `--endpoint-url` is the direct analogue of `fetch_do.py`'s `--api-base` and
gives real, observable wire facts. Two properties make it work, both verified rather than
assumed:

- boto3 signs with the **client's configured region**, not the URL's host, so every request
  carries `Credential=<key id>/<date>/<region>/<service>/aws4_request` even though all 3
  regions hit one URL. That is how the stub observes which region a call was made for.
- Requests carry `Action=` and `Version=` in the form body (`X-Amz-Target` for Cost Explorer).
  `Version` is what disambiguates `elb` (2012-06-01) from `elbv2` (2015-12-01) — they share
  the action name `DescribeLoadBalancers`, the signing name, *and* the result wrapper.

**Fixtures are stored parsed and re-serialized at serve time.** `aws_wire.py` turns a parsed
response dict into wire XML/JSON using botocore's own shape metadata — element names, item
tags and result wrappers all come from `get_service_model(...)`, never a hand-typed table.
This keeps fixtures auditable and directly reusable by the normalizer unit tests (mirroring
`load_fixture("do_volumes")["volumes"]`), at the cost of one extra piece of test machinery.
That cost is bought off by `test_every_fixture_round_trips_through_botocore`, which encodes
every fixture, hands it to the **real** botocore parser, and asserts equality — so a green
adapter test cannot be an artifact of a lenient encoder. See Deviation 2.

**`attached_to` semantics, per resource.** Following m1: null is the primary orphan signal and
must never be emitted for something in service.

- EC2 instance → always null (m1 emits null for droplets too; the storage side carries the join).
- EBS volume → the attached instance id, null when `Attachments` is empty.
- Elastic IP → `InstanceId` **or** `NetworkInterfaceId`. An EIP fronting an NLB or NAT gateway
  is in service and would false-positive the static-IP rule if only `InstanceId` were checked.
- EBS / RDS snapshot → the source, **cross-referenced against the resources the sweep actually
  found**. AWS keeps `VolumeId`/`DBInstanceIdentifier` on a snapshot long after the source is
  deleted, so trusting the field verbatim would make every snapshot read as live and destroy
  the aged-orphan signal entirely.
- ELBv2 → the first registered target across the LB's target groups, null when there are none.
  Classic ELB → the first entry of `Instances[]`, null when empty.
- RDS instance → null when stopped-idle (it serves nothing — the m2 field-mapping note), the
  identifier itself when running.

**Region sweep.** `describe_regions()` **without** `AllRegions`, so only opted-in regions are
returned and a disabled region is never touched. `CLOUDCOST_AWS_REGIONS` is the documented
comma-separated override. Cost Explorer is pinned to `us-east-1` — built with the sweep region
it would be queried once per region and the bill would be multiply counted.

**Degrade, don't crash** (m1 convention, unchanged). Auth failure → fatal, exit 1, no files.
One failing region/service → an `errors[]` entry naming **source and region**, sweep
continues. Cost half fails → `errors[]` and no cost file at all, because a zero bill would
read as a real $0.00 month. Exit 0 clean, 1 on error *or* partial.

---

## Deviations from ticket text (noted, not silently followed)

1. **§t1's "the adapter's explicit-session construction means the default chain is never
   consulted even without the belt" is true only after the profile fix.** Decision C offers
   the adapter guarantee as suspenders to the launch prefix's belt. As stated it does not hold
   for the `AWS_PROFILE` arm — see the decision above for the verification both ways. The
   *invariant* the milestone encodes is right and is what t1 implements; the mechanism claim
   was incomplete. Suggested doc fix at the next milestone-doc touch: note that the profile
   config var must be removed from botocore's resolution, not merely left unread. (Same shape
   as m1 t1 Deviation 1, where the milestone attributed default-token pickup to `pydo`.)

2. **"Recorded fixtures" is satisfied at the parsed layer, not the wire layer.** §t1 Touches
   says `tests/fixtures/aws_*.json (recorded, multi-region, incl. RDS)`. The fixtures are
   recordings of real responses stored *post-parse* and re-serialized deterministically from
   botocore's models, rather than captured HTTP bodies. Chosen for auditability, for direct
   reuse by the normalizer tests, and for consistency with the `do_*.json` convention; made
   safe by the round-trip self-check (mutation M9 confirms that check can fail).
   `tests/record_aws_fixtures.py` is the refresh path and has been run against the live
   account.

3. **§t1's poison-guard rationale is true live and vacuous offline — and the guard turned out
   to have three teeth, not one.** §t1 says *"a green run proves it never fell back (a
   fallback would use the bogus key and fail auth)."* Against real AWS that holds: AWS is the
   oracle, and the decoy key was confirmed rejected (`exit=1`, `InvalidClientTokenId`). Offline
   it holds only because `AWSStub` **enforces** the access key id. The mutation run isolated
   each arm (M1b-i/ii/iii):
   - the **exit-code** arm goes *green* under a fallback if the stub is permissive — vacuous,
     exactly as the milestone's wording would have it;
   - the **wire-observation** arm (`access_keys_seen() == {CLOUDCOST}`) catches the fallback
     even with the oracle disabled;
   - the **profile** arm catches it too, because a fallback dies on `ProfileNotFound` first —
     which is why the first attempt at this check-the-check read as a failure and had to be
     re-run with the profile poison removed to isolate the credential arm.

   Suggested doc fix: §t1's done-check should say the offline half requires an
   access-key-enforcing stub, and keep the "green run proves it" wording for the live half
   only.

4. **`UnauthorizedOperation` was initially mapped to "region not enabled".** Found while
   reviewing the live run's empty result. It is EC2's *"you lack the IAM permission"*, not a
   disabled region — so a missing `ec2:Describe*` would have produced an empty inventory on a
   **green** run under a reason that reads plausibly and is wrong. Corrected: only
   `OptInRequired` is region-disabled; `UnauthorizedOperation` and `AccessDenied` fall through
   to `errors[]` (partial, exit 1). Pinned by
   `test_a_missing_iam_permission_is_an_error_not_a_region_warning` and mutation M20.

---

## Live evidence (real account, read-only, D2 hermetic prefix)

The `aetheris-ro` user on the milestone's AWS account (id withheld here for the same reason
the fixtures scrub it to `111122223333`). Run under
`env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE AWS_SHARED_CREDENTIALS_FILE=/dev/null`.

- **Full sweep, 2026-08:** exit 0, **17 regions swept**, 0 resources, 0 line items, no
  warnings, no errors, empty stderr.
- **Cost path proven on real data:** the same adapter for **2026-07** returns **9 service line
  items totalling $4.99** — Secrets Manager $4.14, Tax $0.77, S3 $0.05, ECR $0.03, and Glue /
  KMS / ECR-Public / RDS / SNS at $0.00. August is empty because the run happened on
  2026-08-01: Cost Explorer returns a `ResultsByTime` entry for the period with no groups yet.
- **The zero inventory is real, not masked.** A well-formed zero is the one thing not to take
  on trust, so it was checked independently of the adapter: direct `describe_instances` /
  `describe_volumes` / `describe_addresses` in us-east-1, ap-south-1 and eu-west-1, and
  `describe_db_instances` in us-east-1, all return 0. The account genuinely carries no
  orphan-shaped resources today.
- **Live poison guard:** with `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` /
  `AWS_PROFILE` set to decoys and `AWS_SHARED_CREDENTIALS_FILE=/dev/null`, the run is green and
  returns the identical 9 lines / $4.99. Its counter-check: feeding the decoy as
  `CLOUDCOST_AWS_*` gives exit 1, `InvalidClientTokenId`, and **no files written** — so AWS
  really is the oracle and a fallback would have failed.
- **Credentials:** absent from stdout, stderr and both emitted files on every live run. The
  shadow warning names `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_PROFILE` without
  printing any value.

**Mutation plan: 28/28 behaved as specified** (22 at r0, plus M21–M26 for the review
findings), sources restored byte-identical afterwards (diffed), suite green. Every guard, asserted value and displayed figure in this ticket has
been observed failing in its broken state.

---

## r0 review findings — dispositions

**F1 — a failed volume/DB sweep asserted "source is gone" on every snapshot in the region.
FIXED in t1.** `attached_to: null` on a snapshot is not "unattached"; it is the positive claim
*the source it was taken from is gone*. That claim rests on a cross-reference against the
region's volume (or DB) sweep, and the cross-reference is only meaningful if the sweep
completed. When it errored, `live_volumes` was empty or short and **every** snapshot in the
region came out null — a well-formed positive claim standing where the truth is simply
unknown, on the run that is already degraded. Fixed by `resolve_source(source, live,
resolved)`: with the sweep unresolved the provider's own field is taken at face value, which
under-claims (a genuinely orphaned snapshot reads as attached) rather than fabricating evidence
a human would act on. `guard()` now returns whether its source completed, and the run warns
per region and per kind rather than degrading silently. Pinned by four tests, mutated M21/M22.

*One correction to the finding's blast radius, per reviewer-claims-verified.* The finding says
this "fabricates aged-snapshot orphans". `rule_aged_snapshot` (`detect_orphans.py:168`) fires
on **age alone** — `attached_to is None` only appends the evidence line *"attached_to is null —
the source the snapshot was taken from is gone"*. So the candidate would have fired either
way; what was fabricated is the **evidence sentence inside it**, which is what a human reads
before deleting a snapshot. The invariant is exactly right and is what the fix implements; the
mechanism is one step narrower than stated — and it widens again the moment t2 (c) writes an
RDS snapshot rule that keys on `attached_to`, which is precisely the shape §t2 asks for.

**F2 — the zero that actually occurs was neither tested nor distinguished. FIXED (test +
comment), behaviour deliberately unchanged.** There are two zeros and the suite only covered
the one that does not happen: `ResultsByTime: []` (CE has nothing for the period → raise,
withhold the cost file, because a $0.00 snapshot reads as a real zero bill) versus
`ResultsByTime: [{…no Groups}]` (CE *has* the period and reports no spend in it → a real
$0.00 snapshot, written). The second is what the live 2026-08 run returned. Cost Explorer
cannot distinguish "$0 so far" from "$0 total", so neither can this adapter — documenting
rather than guarding is the honest call, which is what the reviewer accepted. Now both zeros
are named in `fetch_costs`, and
`test_a_period_cost_explorer_reports_no_spend_in_yet_is_a_real_zero_bill` pins the intended
behaviour against a fixture of the real shape (mutation M23), so the outcome is a decision
rather than an accident of which empty CE happened to return.

**F3 — CE page metadata duplicated across group-pages. FIXED.** CE repeats the same
`TimePeriod` on every page, so a multi-page bill emitted one identical `results_by_time` entry
per page. Deduplicated on append. Covered by
`test_cost_explorer_page_metadata_is_deduplicated`, which also proves the dedup is
metadata-only — both pages' groups are still summed. Two new fixtures make CE's hand-rolled
`NextPageToken` loop exercised at all, which it previously was not. Mutation M24.

**F4 — every load balancer read as untagged. FIXED by fetching the tags.** Neither
`DescribeLoadBalancers` returns tags, so the original call-budget shortcut did not leave the
figure incomplete — it left it **wrong**: t3's tag-coverage percentage and its top-untagged
table would have mis-counted a tagged LB. `describe_tags()` batches at AWS's 20-identifier
limit (one extra call per 20 load balancers), handles both API shapes
(`ResourceArns`/`ResourceArn` for ELBv2, `LoadBalancerNames`/`LoadBalancerName` for classic),
and makes no call at all when a region has no load balancers. Covered by two tests including
the batch boundary; mutations M25/M26. `elasticloadbalancing:Describe*` already covers
`DescribeTags`, so §Prereqs 1 needs no change. **Not exercised live** — the account carries no
load balancers, so this path is fixture-proven only; worth a look at t3 if any LB ever appears.

## Gates at the ticket boundary (run off-territory, per the gate rule)

| Gate | Result |
|---|---|
| `pytest cloudcost/tests/` | **219 passed** (157 m1 baseline unchanged + 62 new) |
| `drift_check.py --strict` | **8 PASS / 0 FAIL / 2 WARN** — both the exempt `project_knowledge` staleness class, and both pre-existing (manifest `9afd8e7`/`63f48e1` vs HEAD `72fd505`); checks 1–7 green |
| `mix test` | 969 tests, **0 failures**, 133 excluded |
| `mix format --check-formatted` | clean |
| `mix credo --strict` | 2047 mods/funs, no issues |
| `mix dialyzer` | 0 errors, passed |
| `mix hex.audit` | no retired or advisory packages |
| `bun run build` | ✓ built |
| `bun run lint` | clean |
| `sprint.sh cloudcost` | **known-red, tracked as BL-069** — not re-triaged. Verified rather than presumed: a read-only `fetch_do.py` + `detect_orphans.py` run against the live DO account today returns 18 resources and **0 orphan candidates**, so the case's `≥1` assertion fails. Independent of t1, which touches no DO code and no sprint file. |

**Do not run the real-bill done-check on the first day of a month.** Both adapters degrade
correctly and both degrade to nothing useful: AWS's Cost Explorer returns a `ResultsByTime`
entry with no groups (0 line items, $0.00), and DO's `select_invoice` finds no invoice for the
new period at all (`status: partial`, `"no DigitalOcean invoice found for period 2026-08"`, no
cost file written). Neither is a defect — it is the degrade-don't-crash path working — but a
t3 report generated on the 1st carries no cost section to review, which would read as a
failure of the report rather than of the calendar.

## Open items forwarded

- **`swept_regions` has no contract-legal home in the rendered report — t3 decision.** The
  frozen inventory envelope is five keys, and §t2 (d) holds `compose_report_data.py` /
  `render_report.py` literally unchanged. t1 emits and proves the set in two places: the
  stdout summary (`regions_swept`) and the cost snapshot's `provider_extra.swept_regions` (the
  block downstream must not key on generically). Decision D's *"the report states the swept
  region set"* needs one of those surfaced by t3 — which is either a t2/t3 enumerated
  adjustment or a contract-leak finding, and should be adjudicated as such rather than done
  quietly.
- **The seam sweep + backlog row.** `state`, `type`, and the flat-billed cost assumption. m1's
  "one seam" claim needs correcting where it appears, and the sweep should ask what *else*
  shared machinery assumes about a provider — the rule catalogue's age thresholds and the
  `keep=true` tag spelling are the obvious next candidates.
- **t2 (a′)** — rename `fetch_do.py`'s two types onto the canonical values, re-key the two
  DO-specific rules, enumerate the vocabulary in §Normalized schemas. Until it lands, AWS
  orphan detection does not fire.
- **t2 (c) cost model** — `fired()` gains an optional saving; `score()` honours it; the
  stopped-instance rule sums attached storage. Closes m1's own forward.
- **The ≥1-orphan done-when is unreachable until Prereq 3 is planted.** Independently
  confirmed above: there is nothing on this account for the orphan lane to find. Note the
  live bill is Secrets Manager / S3 / ECR — i.e. entirely **non-orphan-shaped** waste, which is
  exactly t4's lane. On this account the optimization spike is where the value is, and the core
  lane's ≥1-orphan proof rests wholly on the planted Elastic IP.
- **`last_activity_at` stays null** (§t1). Populating it would make t2's recency modifier live
  and expose its unfixed one-sided window bound (m1 open item, still latent).
- **Load balancer tags are fetched but never exercised live** (F4) — the account has no load
  balancers. Fixture-proven only; confirm at t3 if one appears.
- **Rate spot-check (BL-071)** — every rate in `AWS_LIST_PRICES` is an unverified us-east-1
  list price. None could be checked against this bill: at service granularity there is no
  per-resource line, and the account carries none of the priced resource types anyway.
