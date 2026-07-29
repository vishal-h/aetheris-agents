# m1-cloudcost §t3 — review (r0, approve)

**Ticket:** m1-cloudcost §t3 — `compose_report_data.py` (N-provider merge + MoM delta).
**Commit reviewed:** `8526e67`. **Reviewer:** claude-ui. **Date:** 2026-07-29.
**Verdict:** approved, push. No blocking finding; two non-blocking (one packet correction,
one carried into t4).

Reviewer's message, verbatim:

---

Approved — push. I swept it and re-derived the merge numbers independently rather than trusting the packet; it holds. Where I could confirm against source, I did.

Independently verified:
- **D4, both directions.** Resource estimates for the positive inventory sum to 56.58; the grand total is the billed 172.21 — and the structural guard asserts the estimate-read patterns are *absent* from `service_totals`/`month_on_month` **and present** in `coverage_section`/`orphan_section`, so it can't pass by matching nothing. `grand_total` is the sum of declared `totals.amount`, never a resource sum.
- **Tag-coverage single-source (the decision).** 1 tagged / 6 = 0.1667, equal to t2's figure by shared definition — and the "planted 0.99 in the orphan file" test proves the report ignores it. Mutation 2 confirms the guard fails if it ever reads coverage from the orphan file.
- **The N=2 merge, by hand.** Top-untagged ranking across providers (vm-2 80 → disk-1 40 → lb-idle-1 12 → … → snap-aged-1 1.2, with the tagged vm-1 at $120 correctly excluded), `untagged_monthly_cost_estimate` 155.58, HIGH band `[disk-1, 203.0.113.10, vol-orphan-1]`, saving 91.58 — all match.
- **MoM honesty.** Both sides go through the same grouping function; appeared/removed are labelled not zero-differenced; `delta_pct` is null off a zero base, never fabricated; two currencies withhold the scalar. The 12.33% / 23.67% / +46.97% arithmetic checks.
- **The t2-file edit is legitimate and behavior-preserving.** The `_normalized.py` extraction is verbatim (I compared the moved bodies), declared in Touches + notes, and t2's 54 tests pass unchanged. The real risk — the provider-agnostic guard silently shrinking when the reads it watches move out — was caught: the guard now greps `detect_orphans.py` + `_normalized.py`, and the new module's docstring deliberately avoids the `provider_extra` literal so it doesn't false-positive. That's the correct way to touch approved code.

Two findings, neither blocking:

1. **Count slip in §1b (Complete-output).** The breakdown says "t1 = 23"; t1 is **25** (25 + 54 + 47 = 126, which is the total actually reported). The 126 is right and the suite is green — the "23" was pulled from t1's pre-r1 notes before the shadow-guard tests bumped it to 25. Cosmetic, but it's a committed artifact and a wrong count is the exact thing that gets cited later — worth correcting in the packet/notes.

2. **MoM headline blends real growth with a new provider's first appearance (→ t4, not a t3 defect).** At N≥2 when a provider has no prior snapshot, `delta_amount`/`delta_pct` fold that provider's entire spend into "growth" — the §1d +74.21 / +46.97% is DO's real +14.21 plus someothercloud's first-time $60. t3 labels it honestly (`providers_without_prior_snapshot`, per-service `new`, a warning), so it isn't silent — but the headline % misleads unless t4 renders that caveat adjacent to it. Carry into t4 as a rendering requirement.

What I did **not** do: re-run the 126-test suite or the three mutations myself — I take those outputs as reported, having independently checked the arithmetic behind the assertions and the seam logic (where a silent-wrong-answer would hide). Also flagging that claude-code's re-forward of t1's rate-check is correct — t1 parked it "for t3 where invoice items are in hand," but DO bills service-level (D4) so there's no per-resource line to check against; re-forwarding it to the first resource-granular provider is the honest call, not a silent drop.

**t3 verdict: approved, push.** t4 is next — the custom report render to a local PDF/HTML. It inherits one carried requirement (the MoM new-provider caveat must render next to the delta) and t3's own forward that everything t4 needs is already in `report_data_{period}.json` (band cutoffs, `top_k`, reconciliation flags, the estimate/billed notes) so the template computes nothing. Push t3 and say the word — I'll hand you the t4 prompt, and there's no open design decision blocking it this time.

---

## Disposition

| Item | Where it landed |
|---|---|
| **F1** — the "t1 = 23" count slip | Re-derived from source before acting (`--collect-only`: 25 / 54 / 47 = 126); the reviewer's count is correct. Fixed at the **source of the stale claim**, `cloudcost/docs/t1-implementation-notes.md` §Deliverables — the packet quoted it faithfully, so correcting only the packet would have left the next quoter to make the same slip. The line now carries the real count, the history (23 at first submission, two shadow-guard tests added in review), and the citation. |
| **F2** — MoM headline blends new-provider spend into growth (→ t4) | `cloudcost/milestone.md` **§t4 Contract refs**, as a numbered rendering requirement with the +74.21 / +46.97 % worked example — in t4's own section *before* its session starts, because implementation notes do not travel forward on the prompt path (BL-007). Filed alongside the "template computes nothing" forward, so t4 reads both from one place. |
| Reviewer's confirmation of the t1 rate-check re-forward | Already filed at t3 in `milestone.md` §Open items carried forward. No action. |
| The `_normalized.py` extraction, confirmed legitimate | No change. The approval is unconditional; the guard extension the reviewer names as the deciding safeguard is already in `tests/test_detect_orphans.py`. |

**No change to `scripts/compose_report_data.py` or `tests/test_compose_report_data.py`.**
Neither finding is a code defect: F1 is a stale count in a t1 doc and F2 is a t4 rendering
requirement over a payload that already carries the caveat machine-readably
(`providers_without_prior_snapshot`, per-service `change: "new"`, a `warnings[]` entry).

**Reviewer scope note, recorded as stated:** the 126-test suite and the three mutation
reddenings were taken as reported, not re-run. The independent work was the merge arithmetic,
the D4 and coverage guards, and the verbatim comparison of the extracted function bodies.
