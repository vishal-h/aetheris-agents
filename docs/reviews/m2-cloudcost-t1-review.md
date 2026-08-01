# m2-cloudcost §t1 — review (r0 + r1, merge)

**Ticket:** m2-cloudcost §t1 — AWS adapter `fetch_aws.py` (cost + full-region inventory).
**Reviewed:** the r0 packet at the pre-commit working tree over agents `72fd505`; the r1 packet
after F1–F4 were folded. Harness untouched (single-repo ticket).
**Reviewer:** claude-ui. **Date:** 2026-08-01.
**Verdict:** **r0** — zero blocking, four non-blocking (F1–F4), four adjudications (A1–A4),
deviations 1–4 accepted. **r1** — all four fixed in t1, zero remaining findings, **approved to
merge**.

---

## r0 — reviewer's message, verbatim

---

# m2-cloudcost t1 — review (r0)

**Verdict:** strong packet, done-check substantively met, stays in scope, emits the frozen contract, auth/leak discipline is thorough and mutation-verified. **Zero blocking findings.** Four non-blocking findings claude-code did not raise (F1–F4), my rulings on the four items the packet asks me to adjudicate (A1–A4), and the doc folds I own. Deviations 1–4 accepted.

The offline suite, the parsed-fixture-pinned-by-real-botocore approach, the three-teeth poison guard, and catching Deviation 4 by interrogating a zero are all exactly the posture this milestone asks for. Good work.

---

## Non-blocking findings (not raised in the packet)

**F1 — Silent-wrong-answer: a failed volume/DB sweep fabricates aged-snapshot orphans.** `fetch_region_inventory` runs `guard("ec2:DescribeVolumes", volumes)` before `guard("ec2:DescribeSnapshots", snapshots)` so `live_volumes` seeds the source cross-ref; `normalize_snapshot` sets `attached_to = str(source) if source in live_volumes else None`, and null there *is* the aged-orphan signal. If `DescribeVolumes` errors (partial run), `live_volumes` is empty or partial, so **every snapshot in that region resolves `attached_to=null` — reads as source-gone — when the truth is unknown**. Same shape for `DescribeDBInstances` → `live_databases` → RDS snapshots. It only fires on a partial run (exit 1, flagged) and only bites when detect_orphans runs at t3, but the wrong signal is already in the emitted inventory. This is the exact class the milestone keeps hitting: a well-formed positive value where a gap exists. Cheap, contained fix in t1 (preferred): when a region's volume/DB sweep errored, don't emit that region's snapshot `attached_to` as null-meaning-gone — mark the source unresolved (or drop those snapshots) so t3's aged rule can't fire on an unknown. Mutation-check the failure state. If deferred instead of fixed, it needs a backlog row.

**F2 — the first-of-month zero-groups case is unguarded *and* untested; the empty fixture tests a different shape.** Live evidence 1c-i (2026-08) shows CE returning `ResultsByTime:[{…no groups}]` → `line_items:0`, `$0.00`, **status ok**, cost file written. But the zero-bill guard and `test_a_missing_cost_period_degrades` use `ResultsByTime:[]`, which raises and suppresses the cost file — a *different* shape. So the case that actually occurs (their own evidence) is neither tested nor suppressed, and "don't run on the 1st" is documented, not enforced. I accept that `$0-real` vs `$0-not-yet` are indistinguishable at the API, so documenting rather than guarding is defensible — but the test must cover the real zero-groups shape and assert the *intended* behavior, so the choice is conscious rather than an accident of which empty-shape CE returns. Add that test; state in the code which zero is suppressed and which sails through.

**F3 — CE `provider_extra.results_by_time` duplicates across pages (minor).** `fetch_costs` appends a `{time_period, estimated}` entry per page, and CE repeats the same `TimePeriod` across group-pages, so a multi-page bill emits duplicate metadata entries. Opaque/cosmetic (single-month bills are usually one page), but dedup by `time_period` or scope the append to the first page.

**F4 — every load balancer emits `tags: []`, so a tagged LB reads as untagged.** `describe_tags` is not called (noted in the notes as a call-budget choice). Acceptable for m2, but it means t3's tag-coverage % and "top untagged spenders" will always count LBs as untagged, which is a silently-wrong figure for a tagged LB. Decide: fetch LB tags, or have t3's report note that LB tag coverage is not measured. Flag so the untagged figure isn't quietly wrong.

---

## Adjudications (the four the packet raised)

**A1 — canonical `type` vocabulary + t2(a′) + schema enumeration: ratified, doc is mine.** t1 emitting canonical from line one is correct and is what we agreed. I will write §t2 (a′) (rename `fetch_do.py`'s two values, re-key the two DO-specific rules, regen DO fixtures) and enumerate the canonical `type` vocabulary in §Normalized schemas. The t1→t2 detection gap is the ratified `state` ordering. No finding against t1.

**A2 — Decision C "suspenders" caveat: accepted, doc is mine.** The `AWS_PROFILE`→`ProfileNotFound`-before-explicit-creds behavior is real and well-verified (both-ways test + version-pinned). The one-kwarg fix is correct. I'll amend Decision C: the profile config var must be *neutralized* in botocore's resolution, not merely left unread — same shape as m1 t1's `pydo` correction. Adapter is right; doc catches up.

**A3 — poison guard offline-vacuous without an enforcing stub: accepted, doc is mine.** The mutation isolation (M1b-i/ii/iii) is exactly the right check-the-check. The *test* is non-vacuous because it also asserts `access_keys_seen() == {CLOUDCOST}` and `POISON not in requests` (the wire arm catches a fallback even against a permissive stub), so the guard holds — it's only the doc's *rationale wording* that's live-only. I'll amend the §t1 done-check: the offline half requires an access-key-enforcing stub; "a green run proves it" is the live half, where AWS is the oracle.

**A4 — `swept_regions` has no contract-legal render home: real, forwarded to t3, with a recommended resolution.** Correct tension: Decision D wants the report to state the swept set; §t2(d) holds compose/render unchanged; `provider_extra` is opaque so compose can't key on it without going provider-aware (breaking D5). Recommended resolution for t3 (not forced now): surface it as a **deliberate, enumerated compose/render adjustment** — a named "region coverage" field compose lifts from the snapshot into report_data, rendered generically — i.e. a t3 contract-adjustment, *not* a leak. That's clean under per-provider reporting (H) where the report is already single-provider. The alternative — relaxing Decision D to "the run output states the swept set" — is weaker and I'd avoid it. t3 adjudicates; I'll note both in the doc so t3 isn't stuck.

---

## Deviations — all accepted

1. Profile neutralization → A2. 2. Parsed-not-wire fixtures, pinned by `test_every_fixture_round_trips_through_botocore` against the real botocore parser — good engineering; the round-trip test is the demonstration that makes it safe, so "recorded" is satisfied in substance. 3. Poison-guard wording → A3. 4. `UnauthorizedOperation` mis-map — found, fixed, tested, mutation-checked (M20). This is a clean Silent-wrong-answer catch (empty inventory on a green run under a plausible-wrong reason); exactly right to fix inline and record.

**Seam count:** I agree it's three (`state`, `type`, flat-billed cost model), and that the root cause is observation-not-enumeration (Adjacent-case). I'll correct the "one seam" text where it appears and file a **seam-sweep backlog row** (enumerate every field/assumption shared machinery makes about a provider — the age thresholds and `keep=true` spelling are the next candidates). Strong §7 promotion candidate at m2 close.

---

## Doc folds I'll make (so the packet's asks land)

§t2 (a′) + §Normalized schemas `type` enumeration (A1); Decision C profile caveat (A2); §t1 done-check poison-guard offline/live split (A3); "one seam"→three-seams correction + seam-sweep backlog row; A4 recorded as a t3 decision with the recommended enumerated-adjustment resolution.

---

## Merge posture

No blocking findings, so this can merge once F1 and F2 have dispositions (F1: fix-in-t1 preferred given it's cheap and it's the milestone's recurring class; F2: add the real-shape test + conscious decision) and F3/F4 are fixed-or-tracked. BL-069 is correctly named-not-re-triaged; the empty-account observation (core lane rests wholly on the planted Elastic IP; t4 is where this account's value is; don't run t3 on the 1st) is important and I'll carry it into t3's scoping.

Send me the updated packet with the F1–F4 dispositions and I'll close r1. In parallel I'll cut the doc rev (t2 a′, schema enumeration, the three caveats, seam-sweep row) so t2 starts against the corrected contract.

---

## r1 — reviewer's message, verbatim

---

m2-cloudcost t1 — review (r1): merge ✓

r1 closes clean. F1–F4 all fixed in t1, each with tests and a dedicated mutation (M21–M26), none trusted on a green test alone. Zero remaining findings, no blocking, no non-blocking. t1 is approved to merge.

Spot-verified against the inlined r1 code, not just the dispositions:

F1 — resolve_source(source, live, resolved) takes the provider field at face value when the source sweep didn't complete, so it under-claims (a genuinely-orphaned snapshot reads as attached) instead of asserting "source gone" over an unknown; guard() returns completion, and the per-region/per-kind warning makes the conservatism visible rather than silent. This is the right direction — the failure mode is now "we didn't verify" not "we fabricated." M21/M22 pin both halves.
F2 — the real shape (ResultsByTime:[{no groups}]) is now a fixture and pinned to status ok, cost file written, period on record, distinct from the withheld [] case; the two zeros are documented in fetch_costs. Behaviour deliberately unchanged, per the ruling. M23 pins the decision.
F3 — dedup on append, and it incidentally gave CE's hand-rolled paging loop its first coverage (both pages summed, one metadata entry). M24.
F4 — batched DescribeTags across both API shapes, no call when a region has no LBs, and you're right that elasticloadbalancing:Describe* already covers it so §Prereqs 1 is untouched. Fixture-only (no live LB) is the honest caveat; noted for t3. M25/M26.

On your F1 blast-radius correction — accepted, and it's the discipline working the way it should. You verified my mechanism against detect_orphans.py:168 and found the invariant right but the sketch one step off: rule_aged_snapshot fires on age alone, so the candidate fired either way — what my null-attached_to fabricated was the evidence sentence inside it ("the source it was taken from is gone"), which is the line a human reads before deleting. That's reviewer-claims-verified running in reverse (a finding binds by its invariant, not its sketch), and it actually strengthens the fix-in-t1 call: the moment t2(c) writes an RDS-snapshot rule keyed on attached_to, the mechanism widens back to what I described. Good catch; the fix is correct regardless.

A4 recorded as t3's starting position (enumerated compose/render adjustment, not a leak, Decision D intact) — agreed, nothing re-opened.

Merge t1. Nice work across both rounds — the mutation-per-finding posture and catching Deviation 4 by interrogating a zero are exactly the bar this milestone sets.

---

## Disposition

All four findings were **fixed in t1**; none was deferred or traded for a backlog row. Each
carries its own tests *and* a dedicated mutation, so no fix is trusted on a green test alone.
Full reasoning is in `cloudcost/docs/m2-t1-implementation-notes.md` §"r0 review findings";
summarised here so the review file stands alone.

### F1 — a failed volume/DB sweep asserted "source is gone" — FIXED

`attached_to: null` on a snapshot is not "unattached"; it is the positive claim *the source is
gone*. That claim rests on a cross-reference against the region's volume (or DB) sweep, and the
cross-reference only means anything if the sweep completed. When it errored, `live_volumes` was
empty or short and **every** snapshot in the region came out null — a well-formed positive
claim standing where the truth was unknown, on a run already degraded.

```python
def resolve_source(source, live: set, resolved: bool):
    if not source:
        return None
    if not resolved:
        return str(source)
    return str(source) if str(source) in live else None
```

`guard()` now returns whether its source completed; `resolved["volumes"]` /
`resolved["databases"]` gate the cross-reference; and the run warns per region and per kind so
the conservatism is visible rather than silent. The failure mode is now *"we didn't verify"*
rather than *"we fabricated"*. Four tests; **M21** (cross-reference regardless of resolution →
red), **M22** (degradation silent → red).

**Blast-radius correction, accepted by the reviewer at r1.** The finding said this "fabricates
aged-snapshot orphans". `rule_aged_snapshot` (`detect_orphans.py:168`) fires on **age alone** —
`attached_to is None` only appends the evidence sentence *"attached_to is null — the source the
snapshot was taken from is gone"*. The candidate fired either way; what was fabricated is the
evidence sentence *inside* it, which is the line a human reads before deleting a snapshot. The
invariant was right and is what the fix implements; the mechanism was one step narrower than
stated — and widens back to the finding's original wording the moment t2 (c) adds an
RDS-snapshot rule keyed on `attached_to`, which is the shape §t2 asks for. Reviewer-claims-
verified running author→reviewer: a finding binds by its invariant, not its sketch.

### F2 — the zero that actually occurs was neither tested nor distinguished — FIXED (test + comment); behaviour deliberately unchanged

Two zeros, and the suite covered only the one that does not happen:

- `ResultsByTime: []` — CE has nothing for the period → raise, withhold the cost file, because
  a $0.00 snapshot would be read as a real zero bill.
- `ResultsByTime: [{…no Groups}]` — CE *has* the period and reports no spend in it. This is
  what the live 2026-08 run returned, and it is also what a genuinely idle month looks like.

Cost Explorer cannot distinguish "$0 so far" from "$0 total", so neither can the adapter;
documenting rather than guarding is the honest call, which is the ruling. Both zeros are now
named in `fetch_costs`, and
`test_a_period_cost_explorer_reports_no_spend_in_yet_is_a_real_zero_bill` pins the intended
behaviour against a fixture of the real shape — so the outcome is a decision rather than an
accident of which empty CE happened to return. **M23**.

### F3 — CE page metadata duplicated across group-pages — FIXED

CE repeats the same `TimePeriod` on every page, so a multi-page bill emitted one identical
`results_by_time` entry per page. Deduplicated on append. Two new fixtures gave CE's hand-rolled
`NextPageToken` loop its first coverage at all, and the test proves the dedup is metadata-only
— both pages' groups are still summed. **M24**.

### F4 — every load balancer read as untagged — FIXED by fetching the tags

Neither `DescribeLoadBalancers` returns tags, so the call-budget shortcut did not leave the
figure incomplete — it left it **wrong**: t3's tag-coverage percentage and its top-untagged
table would have mis-counted a tagged LB. `describe_tags()` batches at AWS's 20-identifier
limit, handles both API shapes (`ResourceArns`/`ResourceArn` for ELBv2,
`LoadBalancerNames`/`LoadBalancerName` for classic), and makes no call when a region has no
load balancers. `elasticloadbalancing:Describe*` already covers `DescribeTags`, so §Prereqs 1
is untouched. **Caveat carried to t3:** the account has no load balancers, so this path is
fixture-proven only and was never exercised live. Two tests including the batch boundary;
**M25**, **M26**.

### A1–A4 — adjudicated at r0; doc folds owned by claude-ui

Recorded here so the ticket's record is complete, not re-opened: **A1** canonical `type` +
§t2 (a′) + §Normalized schemas enumeration; **A2** Decision C's profile-neutralization caveat;
**A3** the §t1 poison-guard offline/live split; **A4** `swept_regions` forwarded to t3 with the
enumerated compose/render adjustment as the recommended resolution and Decision D intact.
Deviations 1–4 accepted. The "one seam" → three-seams correction and the seam-sweep backlog row
are claude-ui's to file.

---

## Evidence at merge

| Gate | Result |
|---|---|
| `pytest cloudcost/tests/test_fetch_aws.py` | 62 passed |
| `pytest cloudcost/tests/` | **219 passed** — 157 m1 baseline unchanged + 62 new |
| Mutation plan | **28/28** behaved as specified; sources restored byte-identical (diffed) |
| `drift_check.py --strict` | 8 PASS / 0 FAIL / 2 WARN — both the exempt `project_knowledge` staleness class, pre-existing |
| `mix test` | 969 tests, 0 failures |
| `mix format` / `credo --strict` / `dialyzer` / `hex.audit` | clean |
| `bun run build` / `bun run lint` | clean |
| `sprint.sh cloudcost` | known-red, **BL-069**, named not re-triaged — verified: live DO run gives 18 resources, 0 orphan candidates |
| Live AWS (D2 hermetic prefix) | 17 regions, exit 0, clean streams; cost path proven on 2026-07 (9 services, $4.99); poison guard green with its counter-check red (`InvalidClientTokenId`, no files); 89-file credential scan clean |

Carried into t3's scoping, per the reviewer: the core lane's ≥1-orphan done-when rests wholly
on the planted Elastic IP (Prereq 3, still PENDING); this account's live bill is entirely
non-orphan-shaped (Secrets Manager / S3 / ECR / Tax), i.e. t4's lane; and the real-bill
done-check must not run on the first day of a month, when both providers return no cost data.
