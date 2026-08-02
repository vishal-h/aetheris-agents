# m2-cloudcost t2 review (claude-ui, r0)

Commits: 163e059 (doc-only rev 5.1) → 7a7b7ec, b74b1d8
Base: 1170747 · Tests: 229 pass (219 t1 + 10 new) · Mutations: 8/8 caught

## Verdict: APPROVE — merge-clean

t2 does exactly what the ticket set out to do: it relocates the type/state
vocabulary to a single home, closes the two vocabulary seams and the
cost-model seam, and proves the AWS adapter now feeds detection without a
translation layer. The negative proof survives. Merge.

## Negative proof — HOLDS

§4 diff shows no edit to compose_report_data.py or render_report.py or any
template. The three moved compose test expectations (LOW 24.00→29.00, total
91.58→96.58, filename digitalocean_orphan_candidates_2026-07.json) are the
honest downstream consequence of the stage above no longer under-reporting —
the cross-stage path previously yielded 0 candidates. Moving an *expectation*
because the input legitimately changed is not editing the machinery; the
machinery ran unchanged and produced different, correct output. This is the
distinction the ticket exists to demonstrate. Accepted.

## Seam closures — 3/3

1. state vocabulary → STATE_STOPPED in _normalized.py; adapters map inward
   (DO off→stopped, others pass through).
2. type vocabulary → 7 canonical TYPE_* + CANONICAL_TYPES frozenset in
   _normalized.py; both adapters and detect_orphans import from there.
3. cost-model → own+attached additive formula, ratified rev 5.1. Adapters
   encode their own cost model in monthly_cost_estimate (AWS stopped own=0.0,
   DO droplet own=full, RDS storage baked into own); the shared rule never
   assumes which.

## own+attached — correct

DO stopped droplet 24+5=29.00; AWS EC2 stopped 0+16=16.00; AWS RDS stopped
0+23=23.00. M6 pins 46.00 (the double-count / replace-not-add error) as
caught. The saving evidence sentence names both terms. Good.

## Mutations — adequate

M1–M8 cover each seam and the formula. One property to record (note, not a
gap): M1 does not fail the AWS cross-stage test because adapter and engine
import the *same* constant — a rename moves both sides together. That is
correct behavior, but it makes the DO mapping test (test_fetch_do canonical
vocabulary) load-bearing: it is the only test binding a string value to the
schema. If that test is ever weakened, a silent vocabulary drift becomes
possible. Keep it.

## Sanctioned deviations — all legitimate

1. cost-model correction (own+attached) — ratified rev 5.1 this session.
2. fetch_aws.py touched — constant relocation only; byte-identical output,
   t1's 62 tests stay green (the relocation proof). Not scope creep.
3. provider_slug duplicated vs compose's private slug() — deliberate;
   converging would edit compose and spoil the negative proof. Tracked
   BL-070. See note below.
4. three compose test expectations moved — covered under negative proof.
5. crafted RDS fixtures as new files — additive, no existing fixture
   semantics changed.

## Non-blocking notes

N1. slug divergence latency. detect_orphans writes
    {provider}_orphan_candidates_{period}.json via provider_slug; compose
    reads via its own slug(). For live providers (aws, digitalocean) both
    transforms agree, so there is no current divergence. The risk is latent
    only for a future provider slug containing characters the two functions
    treat differently — at which point compose would silently find no file
    and under-report. BL-070 already tracks the convergence; recording here
    so the resolver knows the risk class is silent-wrong-answer, not tidiness.

N2. DO mapping test is load-bearing (see Mutations).

## BL-075

Correctly filed under Complete-output discipline: a flake observed
(red-once-green-thrice) is recorded even though the failing test name was
lost to tail -12, with the BL-054 twelfth-slot hypothesis noted. Filing an
under-specified flake beats dropping it. Accepted.

## Merge recommendation

Merge 163e059..b74b1d8. No changes requested. N1/N2 are watch-items on
existing backlog rows, not merge blockers.
