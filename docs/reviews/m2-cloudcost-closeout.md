# m2-cloudcost — close-out

**Status: CLOSED 2026-08-03.** Every done-when met. Spec: `cloudcost/m2-milestone.md`.
**Closing artifact:** the ≥1-orphan core done-when closed at sprint `20260803_062310`, run
`cloudcost-orch-aws-oFbapA` — the AWS pipeline end-to-end on the real bill with one real orphan
(a planted unassociated Elastic IP, since released; BL-069 re-armed for AWS).

## What m2 tested, and the finding

m2 added AWS as the second provider to test m1's claim that the frozen adapter contract makes
provider fan-out **mechanical**. It held. A new provider was a new adapter (`fetch_aws.py`) +
recorded fixtures + its own solo run, with `detect_orphans.py`, the frozen normalized schemas,
and `compose_report_data.py` **unchanged**. `render_report.py` was touched exactly twice, both
deliberate, enumerated, provider-agnostic additive fields — the A4 region-coverage field (t3) and
t4's isolated optional optimization section — each guarded so an absent input leaves the core
report byte-identical.

The claim was not free. m1 called `STOPPED_STATES` "the one seam"; the real count was three —
`state` vocabulary, `type` vocabulary, and the flat-billed cost-model assumption, all provider
specifics that had leaked into shared machinery. m2 closed them at the **schema level** (canonical
`type`/`state` homed in `_normalized.py`; the stopped-with-storage saving made own+attached) rather
than working around them per-provider. That correction *is* the contract-proof: the shared
machinery is now genuinely provider-agnostic, shown by AWS data flowing through it untranslated.

## Ticket ledger

| Ticket | Scope | Landed | Review |
|---|---|---|---|
| t1 | AWS adapter — cost (all services) + inventory (EC2-family + RDS) | `3bc970b` | m2-cloudcost-t1-review.md |
| t2 | Contract adjustments (state/type vocab, RDS rule, own+attached) + negative proof | `b74b1d8` | t2-review.md `ba623b1` |
| t3 | AWS solo run — orchestrator by `CLOUDCOST_PROVIDER`, A4, per-provider dirs, hermetic sprint | `fb4dfe3` | t3-review.md `ff03d1f` |
| t4 | Optimization-signals spike (S3/ECR/Secrets), isolated render section — non-gating | `e20e33e` | m2-cloudcost-t4-review.md |

All reviews r0 APPROVE, merge-clean. Nothing pushed without review.

## Done-when — final

Core (all green at the closing run): AWS pipeline end-to-end via the orchestrator as its own solo
run; report reviewable without the console (service totals, tag coverage, MoM against AWS's own
prior, orphan section with evidence + saving); ≥1 real orphan (the planted EIP); `fetch_aws.py`
re-emits both frozen schemas with downstream unchanged but for the §t2 enumerated adjustments;
scripts pytest-covered offline (287 tests) + `sprint.sh cloudcost` green; AWS in the capability
matrix. Spike (non-gating): t4 emits `optimization_signals_aws_{period}.json` + an isolated
exploratory section; the live read produced 18 signals across 17 regions and seeded BL-072.

## §7 learnings promoted (m2 ratification packet, 2026-08-03)

| # | Learning | Kind | Home |
|---|---|---|---|
| P1 | Resolved-value over advertised-value | new | aetheris-agents/CLAUDE.md |
| P2 | Absent is unknown, not zero | new | aetheris-agents/CLAUDE.md |
| P3 | Section-scoped edits from the no-repo party | new | triad-loop.md (Phase 2) |
| P4 | Adjacent-case: "the one X" is an observation, not a census | refinement | Adjacent-case learning |
| P5 | Cited-means-read: an inherited citation is still uncited | refinement | Cited-means-read learning |
| P6 | Tracked-carry + the coupling constraint | refinement + new | aetheris-agents/CLAUDE.md |
| P7 | A figure carries its basis or it does not exist | new | aetheris-agents/CLAUDE.md |

Authoritative text lands in each home on ratification; this table is the index. The packet itself
is `docs/reviews/m2-cloudcost-section7-promotion.md`, landed as a file before any promotion commit
(BL-007: promotion wording travels as an artifact, not as chat). **P3 is confirmed already landed**
(`7328755`, verified at HEAD); P1/P2/P4/P5/P6/P7 await per-item ratification.

## Backlog filed during m2

BL-069 (DO/AWS ≥1-orphan tripwire, armed) · BL-070 (retire dormant cross-provider merge; converge
slug) · BL-071 (resource-level cost) · BL-072 (Cost Optimization Hub engine milestone — t4 seeded
its scope) · BL-073 (surface reports against runs in Rig) · BL-074 (seam sweep) · BL-075 (`mix
test` flake) · BL-076 (compose sums every provider's prior snapshot — silent-wrong-answer,
mitigated by per-provider `--history-dir`) · BL-077 (sprint `fail` sets no exit status; coupled to
BL-069) · BL-078 (converge AWS plumbing into `scripts/_aws.py`) · BL-079 (no `ap-south-1` S3 rate)
· BL-080 (`partial` reported for intentional figure-omission, not only a read gap) · BL-081
(`s3_no_lifecycle_policy` fires on an observably empty bucket) · BL-082 (the gated orchestrator
path is proven link-by-link, never end-to-end).

> **Correction applied on landing.** The packet's list ended at BL-079. BL-080/BL-081/BL-082 were
> filed from the t4 review's own N1/N2/N3 (commit `f12dfa6`), after the packet was drafted, so the
> list under-counted by three. Recorded rather than silently extended: the packet quoted repo
> state, the repo had moved, and the divergence is a deviation to note.

## Open after m2

None gating. Live tripwire: BL-069 (re-plant a resource before any run that must assert ≥1).
Cleanups that share a file and should batch on the next compose/fetch_aws edit: BL-070 + BL-076 +
BL-078. t4 review tidy-ups that share a file and batch together: BL-080 + BL-081. Coverage
watch-item: BL-082 (sequence after BL-069 if the sprint route is taken). Engine successor: BL-072.
Everything else forwarded on its own trigger.
