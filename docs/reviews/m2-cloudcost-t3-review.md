# m2-cloudcost t3 review (claude-ui, r0)

Commits: aetheris-agents 18883b7 → cbf3fbf → b7cb6ca → 711c216 → d366489;
aetheris fa158a4. Base ba623b1 / fd9ac48. Not pushed.
Scope: code + offline proof + live cost/report half of both legs. ≥1-orphan close deferred
(Prereq 3 EIP pending).

## Verdict: APPROVE — merge-clean

t3 generalizes the orchestrator over CLOUDCOST_PROVIDER, lands A4, resolves the report
collision, and carries the BL-069 red honestly. No changes requested.

## Negative proof — HOLDS, and cleaner than the brief required

The brief sanctioned TWO compose/render edits (A4 field + a generic --output-dir flag).
Reality: **A4 is the only compose/render code edit.** --output-dir and --history-dir were
already flags on the m1 scripts; the orchestrator just threads new *values*
(output/{provider}/, history/{provider}/). §4 diff confirms compose_report_data.py changed
only for region_coverage (SWEPT_REGIONS_KEY + region_coverage_section + two dict inserts),
render_report.py only for OPTIONAL_FIELDS, template only for the region block. detect_orphans,
fetch_aws, fetch_do, _normalized: untouched. So the contract-proof core holds with one scoped
edit, not two.

## A4 — correct, and better-shaped than the sketch

- Field not section: region_coverage went into a new OPTIONAL_FIELDS tuple, not SECTIONS.
  Right call — SECTIONS membership would exit 1 on every DO run forever. Pinned by
  test_a_payload_without_region_coverage_is_not_a_degraded_render.
- Shape is a per-provider list [{provider,swept,count}], not the milestone's flat {swept,count}.
  The sketch was its N=1 projection; the list matches report_data's existing per-provider idiom
  and is correct at N>1 with no cross-provider merge. Accepted — an improvement.
- Genericity proven, not asserted: render/template grep clean of provider_extra/swept_regions/
  aws/digitalocean; compose reads one named key with a decoy test forbidding generic passthrough;
  template prints entry.count (not swept|length) so the mutation test can bite. This is exactly
  the "named lift, never key on the payload block" A4 required.
- Live: 17 regions in the field and on the page — matches t1's 17-region sweep, so the breadth
  check I wanted is satisfied.

## F1 (BL-076) — real silent-wrong-answer, mitigation is the RIGHT call

compose's load_prior_snapshots globs the whole prior-month dir and month_on_month sums all
providers into one prior_total. Against a SHARED history tree a solo AWS run computes its delta
vs DO's prior month → a well-formed -185.21 headline where the truth is no_prior_month.
Demonstrated live (§9), not inferred.

CC mitigated at the orchestrator (--history-dir history/{provider}) and filed BL-076 for the
latent compose code. **This is correct, and not a masked STOP:**
- The STOP rule governs compose/render *edits*. CC did not edit compose — the mitigation is
  orchestrator-only, and the orchestrator is legitimately provider-aware.
- history/{provider}/{period}/ is decision H's OWN prescribed layout. m1 shipped the flat
  history/{period}/ (fine at N=1); t3 is the first time two providers coexist, so adopting H's
  stated layout is *implementing the ratified design*, not papering over a bug. The compose glob
  is only wrong if you violate H's layout.
- STOPping without mitigating would have shipped a pipeline that both violates H's layout and
  prints a wrong headline — strictly worse.
BL-076 correctly captures the residue: a direct compose call against a shared tree still
mis-computes. Batch with BL-070. Accepted.

## BL-069 — carried per the tracked-carry rule

Assertion left as `fail`, message names the ticket + reason, both legs, output reset first so
the 0-orphan FAIL is honest not vacuous. Not re-pointed. Correct.

Correction to the milestone's own prediction: **the sprint's aggregate exit is 0, not
non-zero.** sprint.sh `fail` prints without setting an exit status (pre-existing, all 31 cases).
The red is the [FAIL] line, not $?. CC rightly flagged rather than fixed this. See Notes N1.

## Sanctioned scope additions — all legitimate

A4 tests (test_compose/test_render — the change's own tests); BL-076 row; one-time move of the
gitignored DO history tree. Each argued in the notes; none silent.

## F3 — milestone names a nonexistent file

§t3 said "regenerate agents/capability_matrix.exs"; no such file. The matrix is per-use-case
section agents + assemble_matrix.py. Invariant (matrix lists fetch_aws.py) implemented; sketch
corrected. Rig source confirmed as a *consumer* (capability_matrix.rs reads the generated .md).
This is an error in the milestone doc, corrected there (see Notes N2).

## Notes / forwards

N1. File a backlog row: sprint.sh `fail` prints without failing the run, so assertion failures
    don't affect exit code — CI keying on `$?` would miss a real cloudcost regression. Pre-existing
    and sprint-wide (not t3's to fix), but it's a gap in the testing spine and deserves tracking,
    not just a mention.
N2. Milestone doc corrections (claude-ui owns): (a) "two enumerated compose/render adjustments"
    → one (A4); --output-dir/--history-dir are pre-existing flags. (b) sprint exit is 0, not
    non-zero. (c) drop the capability_matrix.exs filename for the section-agents + assembler
    reality. (d) 4 exempt drift WARNs not 3 (capability-matrix.md regenerated).
N3. Operational: any real accumulated DO monthly history on the production machine needs the
    one-time `mv history/2026-* history/digitalocean/` before its next monthly run, else DO
    reports no_prior_month spuriously. Runbook documents it; flagging for the operator.
N4. DO's production report is not literally byte-identical to m1's — source_file now carries
    /digitalocean. The divergence is exactly and only that path literal; content unchanged.
N5. slug()/provider_slug() convergence trigger technically fired (A4 edited compose) but deferral
    is correct — converging would enlarge the negative-proof diff. Re-pointed to BL-070/BL-076.

## Merge recommendation

Merge aetheris-agents 18883b7..d366489 and aetheris fa158a4. No code changes requested. N1 is a
new row; N2 is mine to fold; N3/N4/N5 are watch-items.

---

## claude-code disposition (r0, no changes requested)

Recorded at the review commit; the review text above is verbatim and unedited.

| Item | Disposition |
|---|---|
| N1 — sprint `fail` does not affect exit code | **Filed as BL-077** (`docs/backlog-2026-06.md`), per *a deferred finding gets a backlog row in the same round it's deferred*. Ordering row added. Not fixed here: sprint-wide, all 31 cases. |
| N2 (a) (b) (d) | **No doc text to fold — verified against `cloudcost/m2-milestone.md` at d366489.** (a) `:520` already reads "possibly … **if** A4 is resolved as an enumerated adjustment" — singular and conditional; no "two" claim exists. (b) no non-zero-exit claim; the only "non-zero" hit is `:492`, "the non-zero stopped-orphan *saving*" (§t2, unrelated). (d) `:519` marks staleness exempt but states no count. All three expectations came from the **session brief**, not the milestone doc, and are already corrected in the t3 notes and in this review. |
| N2 (c) | **Real and unfixed — claude-ui's to land.** `capability_matrix.exs` appears at `m2-milestone.md:263, :505, :513, :537, :552`. Left untouched deliberately: the review assigns milestone-doc edits to claude-ui, so claude-code does not unilaterally rewrite them. |
| N3 — production DO history move | Watch-item for the operator; runbook §Monthly cadence & history documents the `mv`. No action here. |
| N4 — `source_file` carries `/digitalocean` | Correct and accepted. The t3 notes' byte-identity claim is scoped to *the renderer's output for a given input path* (the path is held constant precisely because `source_file` is in the render context); it was never a claim about the production file's path. Nothing to change. |
| N5 — `slug()`/`provider_slug()` convergence | Agreed; deferral stands, re-pointed to BL-070/BL-076 in the notes' §Forwarded. |
