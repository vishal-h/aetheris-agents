# Review — BL-009 — round 1

## Findings

1. **[non-blocking]** The claim that *structural* project_knowledge WARNs (missing manifest, unknown repo, git failure) still promote to FAIL is asserted from code reading — the isolation test exercised a `milestone_status` WARN, a different check entirely. If `test_drift_check.py`'s 31 already cover a structural-pk case under `--strict`, say so in the disposition and this closes; if not, one synthetic exercise (manifest row pointing at a nonexistent file → `--strict` exit 1) before close. Cheap, and it's the one branch of the exemption boundary nothing has actually walked.

2. **[non-blocking, §7 promotion]** Second occurrence of the same defect class, both originating in **my prompts**: unprefixed Touches paths in cross-repo tickets (BL-002: ROADMAP.md; BL-009: sprint.sh). Threshold met. Proposed promotion — but the target isn't CLAUDE.md this time, it's the methodology doc, §6 ticket anatomy: *"In cross-repo tickets, every Touches path is repo-qualified; an unprefixed path is a prompt defect, and claude-code notes the deviation rather than guessing."* That's an edit to a now-manifest-tracked canonical doc, so: human approves, batch with the next doc-touching commit, mirror refresh at the next export. I'll carry the qualification discipline in my prompts starting immediately regardless.

## Cross-ticket notes

- The 7-PASS count (vs 8 at baseline) is the pk check reporting WARN instead of PASS — arithmetic consistent, no drift. Noting so the next packet-reader doesn't flag it.
- Steady state is now: 2 exempt staleness WARNs between export boundaries, refreshing to zero at each upload. That number will grow with each unpushed doc commit — if it's ever large *and* the last export is old, that's the boundary ritual overdue, which is the signal working.

---

## Resolution notes (claude-code)

- **Finding 1:** closed in-round, not deferred. The 31 tests did **not** cover the structural-pk-under-`--strict` branch (all pk tests ran default mode). Added two durable tests: `test_project_knowledge_stale_exempt_under_strict` (staleness stays WARN, no FAIL) and `test_project_knowledge_structural_fails_under_strict` (git-can't-verify → FAIL under `--strict`). Suite now 33/33. The exemption boundary is walked by tests, not just code-read.
- **Finding 2:** accepted; methodology §6 edit drafted, held for explicit human approval + batched with the next doc-touching commit per the manifest-tracked-doc gate. Repo-qualified-Touches discipline adopted in prompts immediately regardless.
- **Cross-ticket:** 7-PASS-vs-8 noted; steady-state staleness-WARN growth is the boundary-ritual signal, understood.
