# m1-cloudcost §t2 — review (r0, approve)

**Ticket:** m1-cloudcost §t2 — `detect_orphans.py` (provider-agnostic heuristics).
**Commit reviewed:** `cc2bf05`. **Reviewer:** claude-ui. **Date:** 2026-07-29.
**Verdict:** approved, push. No blocking finding; one non-blocking forward.

Reviewer's message, verbatim:

---

Approved — push. I swept it by invariant and re-derived the load-bearing numbers myself rather than trusting the packet, and it holds.

Independently confirmed (not taken on the packet's word):
- **The cross-stage seam.** Recomputed the fired set from the *t1* fixtures against the rules: `vol-orphan-1`→unattached, `203.0.113.11`→unassociated_rip, `snap-0001`+`snap-0002`→aged, `lb-orphan-1`→idle, and `lb-tagged-1` silent because t1 emits `attached_to: "tag:web"`. Matches. The reserved-IP with `created_at: null` correctly fires with no age line and raises no warning — that's the one spot a null could have silently degraded, and it doesn't.
- **The arithmetic behind every assertion.** Ages (87d / 148d / 193d), the boundary (exactly 14.0d stays silent, `>` not `>=`), the confidence math (`0.9−0.2+0.1=0.8`; `0.95+0.1=1.05→clamp 1.0`), the 51.58 saving sum, the descending-confidence order, and the 5/7=71% coverage line. All correct.
- **The two decisions are honored honestly, and failably.** A: recency keys on `last_activity_at` only — the M2 mutation that ORs in `created_at` flips the 7-day reserved IP 0.95→0.75 and reddens the suite, so the no-op isn't vacuous. B: `"off"` is provably confined to the one `STOPPED_STATES` line and `state` is read only inside the stopped-droplet rule, both mechanically asserted. The `provider_extra`-absent guard closes the D5 seam.
- **The negative fixture genuinely fires nothing** — I walked all 11 entries; the trap is `drop-active-1`, which *does* have attached storage but is `active`, so the state guard (not an attachment guard) is what holds it silent. Good discriminating fixture.

One minor forward, non-blocking: the recency modifier's window is one-sided — `age > window` rejects, but a *future* `last_activity_at` (negative age) passes and would fire −0.2. Unreachable on DO (null) and untested-because-absent, but when a provider populates the field, bound it both ends (`0 ≤ age ≤ window`) so activity stamped after the reference date doesn't read as "recent." Fold into the same forward as `RECENT_ACTIVITY_WINDOW_DAYS`.

The packet's own forwards (storage-summing, tag-with-zero-backends rule, `STOPPED_STATES` schema normalization, Prereq-2 orphan) are correctly parked. The t2-is-byte-deterministic / t1-isn't divergence is intentional and owned — t3 authors just need to know the two stages differ there.

**t2 verdict: approved, push.** What I did *not* do: re-run the suite or the mutations myself — I take 79-green and the six mutation reddenings as reported, having independently checked the assertion arithmetic and the seam logic (the parts where a silent-wrong-answer would hide).

---

## Disposition

| Item | Where it landed |
|---|---|
| Recency window is one-sided (non-blocking forward) | `cloudcost/docs/t2-implementation-notes.md` §Open items forwarded, folded into the `RECENT_ACTIVITY_WINDOW_DAYS` bullet; plus a row in `cloudcost/milestone.md` §Open items carried forward, so the forward has an executor-visible location and not only a notes file. |
| t1/t2 determinism divergence — "t3 authors just need to know" | `cloudcost/milestone.md` §t3 **Contract refs**, before the t3 session starts (implementation notes do not travel forward on the prompt path — BL-007). |
| Packet's own forwards (storage-summing, tag-with-zero-backends, `STOPPED_STATES` normalization, Prereq-2 orphan) | Already parked in t2's notes; reviewer confirms parked correctly. No action. |

No change to `scripts/detect_orphans.py` or `tests/test_detect_orphans.py` — the approval is
unconditional and the one forward is provider-conditional, so implementing it now would be
untestable on DO (the field is null) and would add an unreachable branch.

**Reviewer scope note, recorded as stated:** the suite and the six mutation reddenings were
taken as reported, not re-run. The independent work was the assertion arithmetic and the seam
logic.
