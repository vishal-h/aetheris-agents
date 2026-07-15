# Review — BL-015 — round 1

## Findings

1. **[non-blocking]** Legacy trio (`key`, `content`, `type`): **leave as documented-legacy INFOs; do not schedule a cleanup ticket yet.** Rationale: the errata note in §6 changes their character — a standing INFO that specs explains is signal, not noise, and BL-009's `--strict` gates WARNs only, so nothing breaks. More importantly, the legacy rows date from the same May-2026 window as the five orphaned `running` runs that are BL-003's test fixtures — a dev-DB reset now would destroy fixtures BL-003 hasn't consumed. Suggested fix: BL-006-pattern tracked entry (event-triggered, not scheduled) in the backlog: *"Dev-DB reset clears the three BL-015 documented-legacy payload INFOs. Gated on BL-003 completion (May rows are its fixtures)."* Deferred-with-entry, not silence, per §5.

2. **[non-blocking, process]** Commits were pushed before review round 1 completed. BL-001 held the push for the human; the methodology gives merge/push decisions to the human. No harm here — the content passes — but if this recurs on a third ticket it's a §7 promotion candidate for CLAUDE.md. Disposition requested: acknowledge, no rework.

3. **[question]** Do any of the 61 legacy rows (5× `prompt_built.key`, 56× `llm_responded.content`) live inside the five orphaned runs? Doesn't change any disposition, but if yes, BL-003's sweep will touch those runs' status while leaving events intact — worth one line in BL-003's implementation notes so a future payload-INFO count change isn't mistaken for drift.

## Cross-ticket notes

- The 3 manifest-staleness WARNs are BL-001 review finding 2 materializing exactly as predicted — the sequencing logic (every doc commit re-stales the manifest; BL-002 refreshes last) is now empirically confirmed. This also hardens the ordering constraint: **BL-002 must land before BL-009**, or `--strict` fails the sprint on manifest WARNs immediately. Already the plan; now it's a dependency, not a preference.
- Renumbering to BL-015/#66 accepted; collision noted. Review file should follow: `bl-015-review.md`.

---

## Resolution notes (claude-code)

- **Finding 1:** accepted — option (b), documented-legacy INFOs. Event-triggered tracked entry added to backlog under BL-015 (dev-DB reset gated on BL-003), landed via BL-002.
- **Finding 2:** acknowledged, no rework. Pushes will be held for the human going forward.
- **Finding 3:** answered **No** — zero of the 61 legacy rows (`prompt_built.key`, `llm_responded.content`) intersect any `running`-status run (SQL join, intersection = 0). They belong to `test-*`/`demo`/`replay-tmp`/`fork` fixture runs, disjoint from the orphaned set. Incidental: the DB currently holds **76** `running` rows, not five — the "five orphaned May rows" framing is itself stale; flagged for BL-003 scope, not acted on here.
