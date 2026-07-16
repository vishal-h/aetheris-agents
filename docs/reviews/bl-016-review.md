# Review — BL-016 — round 1

## Findings

1. **[non-blocking]** The three-signal evidence chain (stated intent, co-landed replacement mechanism, alignment with a documented principle) is the standard this fork needed — and the *defect motive* in 5abd4b9's message (LLM mangling `BTL_010 → BTL_10`) makes the sequential design self-justifying in the record. The evidence comment in the test citing 5abd4b9 + BL-016 means the assertion can never silently regress to the stale expectation. No action; on record as the bar for evidence-based forks.

2. **[non-blocking]** The two deliberate non-touches are correctly reasoned, and the distinction drawn — `milestone.md` is a *point-in-time as-built record* (true when written), ROADMAP is a *current-state mirror* (stale the moment the refactor landed) — is worth keeping: historical documents don't get rewritten to match the present; mirrors do.

3. **[observation, no action]** The rot mechanism here is worth naming: 5abd4b9 changed an agents-repo file whose assertion lived in the *harness* repo — the refactor couldn't see the test it was breaking, and territory-local gates meant nobody ran `mix test` until BL-003's boundary. The gate rule now covers exactly this: a cross-repo refactor today would surface the red the same day. BL-016 is retroactive proof the promotion was correctly aimed.

## Cross-ticket notes

- Behavioral sprint check correctly skipped — the prompt made it conditional on the restore branch, and `Code.eval_file` proves RunConfig validity for the test-is-stale branch. Right reading, not a shortcut.
- Gate-line shakedown: agreed the clause worked and agreed no wording change — the "author cites the right ref" dependency is checkable at review (I can verify #68 exists and matches the named errors), so the review step is the backstop. Watching, not fixing.

---

**Post-commit bookkeeping:** the backlog edit will register as 1 staleness WARN at the next drift run. Carry it with a named endpoint — **BL-017's closeout export** — rather than a micro-boundary now; BL-017 is next and imminent, consistent with precedent. Close #67 with backlinks after push.
