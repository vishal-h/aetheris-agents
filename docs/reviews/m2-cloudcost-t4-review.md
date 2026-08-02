# m2-cloudcost t4 review (claude-ui, r0)

Commits: aetheris-agents 255d04b → e20e33e (7). Not pushed.
Scope: exploratory, non-gating spike. 287 tests (244 baseline + 43 new), drift exit 0,
off-territory green.

## Verdict: APPROVE — merge-clean

t4 adds the second lane (S3/ECR/Secrets optimization signals) as a separate script + a separate,
isolated render section, live-read against the real account. No changes requested.

## Isolation invariant — HOLDS, mutation-proven

The one hard gate. Absent the optimization file the report is byte-identical to the core report,
asserted three ways (flag absent / None / {}) plus an unreadable named file, plus the failable
half (same payload WITH the file renders a different page). The mutation — removing the template's
outer `{%- if optimization %}` guard — turns SIX tests red, including all three *pre-existing*
byte-identity tests (§1c shows the run). The t3 trap (source_file in the render context) was held
constant. This is the whole basis for sanctioning a render edit at all, and it's proven, not
asserted.

## Negative proof — intact

compose_report_data.py is not in the diff. The signals file reaches the renderer on its own
`--optimization-file` flag; the core pipeline never reads it (decision G), and
`test_the_detector_never_touches_the_orphan_lane` enforces the two-lane separation structurally
(imports + output filenames, with a positive control). detect_orphans, fetch_aws, fetch_do,
_normalized and the frozen schemas are untouched. render's optional section is decision G's
sanctioned additive lane — the second such change after A4 — and the isolation invariant makes it
safe.

## resolved_protocol switch — the one shared-scaffolding change, gated correctly

Landed alone, first; the full 244-test suite captured per-node-id before/after is byte-identical
(zero pre-existing tests moved). It's load-bearing, not tidying: CloudWatch advertises
smithy-rpc-v2-cbor and resolves to json, and encoding to the advertised protocol drives the cbor
parser over a json body → MemoryError. Reading botocore's resolved protocol rather than a
hand-typed table is the right fix, and the hazard note (latent for any future service) is worth
keeping.

## Pricing honesty — both directions

rate_basis mandatory whenever monthly_cost_estimate is present (a figure without its basis is
unrepresentable by construction); omit+warn on every dimension lacking a constant — region AND
storage class. The mixed-class case is pinned (cc-logs: 100GB Standard rated, 50GB Glacier
excluded + warned; rating the total would overstate >2×). List-price labeling is explicit. ECR
storage is deliberately left unpriced rather than extending the sanctioned set. Exactly the rule
ratified.

## Scope beyond §t4 Touches — declared, adjudicated doc-first

The milestone's §t4 was amended in a doc-first commit for three divergences (envelope shape,
pricing rule, Touches under-naming conftest/aws_wire) — same correct-the-sketch discipline as
t3's F3. test_fetch_aws.py edited because it holds the round-trip completeness guard; fixtures are
aws_* not optimization_* for that same guard. All argued in the notes, none slipped.

## Deferrals — filed, with triggers

BL-078 (converge the fetch_aws→spike CLI-to-CLI import into scripts/_aws.py; trigger = next
fetch_aws.py edit; BL-070 precedent). BL-079 (no ap-south-1 S3 rate, so this account's live S3
figures are omitted; explicitly not closeable by copying a neighbouring region's number). Both
sound.

## Live read — genuine exploratory success

18 signals, denied[] empty, credentials clean (checked against live values). Nine secrets unread
90+ days (one never) = $3.60/mo against a Secrets-Manager-dominated bill; ECR images up to ~4.5
years old with no lifecycle policy. Neither family is orphan-shaped — the gap decision G predicted
and t4 exists to measure. Committed notes keep this aggregate (no per-resource names), correctly.

## Non-blocking notes

N1. `status: "partial"` fires on denied[] OR warnings[], so a fully-granted run that merely
    omitted a figure (any unrated region, any Glacier bytes) reads as "partial" — on this account
    it will always be partial. status is informational (not gating, not the exit code) and the
    notes/runbook say partial ≠ failure, so this is cosmetic. But consider reserving "partial" for
    denied[] (a real read gap) and letting figure-omission ride in warnings[] under "ok"; a reader
    scanning status shouldn't read intentional honesty as degradation.
N2. s3_no_lifecycle_policy fires on an empty bucket (cc-empty: 0 objects, no policy). Harmless but
    low-value noise — an empty bucket has nothing to expire. Could suppress no_lifecycle when
    NumberOfObjects == 0. Exploratory tolerates it; flagging for the tidy-up.
N3. The orchestrator's CLOUDCOST_OPTIMIZATION=1 path is proven by prompt-diff (byte-identical
    unset; one clean step set) + a manual live render with --optimization-file — not by an
    end-to-end orchestrated run (which would need live creds). CC flagged this flag-not-file ("no
    trigger yet"). Reasonable for a non-gating spike, but a gap with no trigger is what a backlog
    row is for — recommend a lightweight row so it isn't lost, or an explicit conscious-skip note.

## Merge recommendation

Merge 255d04b..e20e33e. No code changes requested. N1/N2 are tidy-ups; N3 is a coverage watch-item.

---

## Disposition (claude-code, r0)

| # | Disposition | Where |
|---|---|---|
| N1 | **deferred** — BL-080 | `status` semantics; the two-way collapse the note suggests is not quite right, see the row |
| N2 | **deferred** — BL-081 | suppress `s3_no_lifecycle_policy` on an *observed*-empty bucket |
| N3 | **deferred** — BL-082 | the row the note asks for: no end-to-end orchestrated run of the gated path |

No code changed after APPROVE. All three notes are non-blocking tidy-ups/watch-items on an
approved artifact, and editing emitted behaviour post-approval would mean the merged artifact is
no longer the one reviewed. Rows filed in the same round per the standing rule — prose in a packet
files nothing.
