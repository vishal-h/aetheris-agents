# BL-067 — review (r0, approve)

**Ticket:** BL-067 — make the capability-matrix assembly deterministic (no LLM arithmetic).
**Commits reviewed:** agents `de685fe` (assembler + tests + docs) and `cd960ba` (backlog close +
BL-068), harness `27bcd94` (sprint wiring) — cross-repo triple.
**Reviewer:** claude-ui. **Date:** 2026-07-30.
**Verdict:** approved — done-when met, built to the stronger whole-assemble form. No findings.
One correction to the *reviewer's own ticket text* (nine section-agent lines → eight), caught by
claude-code against repo state and folded into BL-068. One residual named and tracked (BL-068:
the sprint's full regen still destroys curation and exits 0).

Reviewer's message, verbatim:

---

Approved — BL-067 closed. Built to the whole-assemble form (the row's "LLM pastes verbatim" would've left the fallible actor in the transcription seat), and it's a clean piece of work. Notably, it's the first ticket built under the §7 rule that just landed, and it visibly obeys it: every derived-value test was watched failing under a mutation before being trusted, and the tests re-parse the emitted doc with a parser written independently of the script's, so a shared bug can't green both sides. The rule promoted itself into practice on its first outing.

What I verified by reading:
- **The 10 mutations each fail their intended tests** (§1b) — undercounts, order-sensitivity, silent-drop, missing-section-as-success, timestamp-in-header all caught; restore is clean.
- **The invariance check is honest about its one leak** (§1e): derived values identical over regenerated vs curated sections *except* the prose Tools cell (`MCP servers (corpus_search, lattice)` → `(MCP: corpus_search, lattice)`), correctly attributed to BL-068 (a cell that's simultaneously curation and data is regen-fragile), not laundered as a rounding difference.
- **The premise is vindicated concretely:** the script exposed three real defects the LLM assembler had left standing in the committed Overlap Report — the 5-tool group listing 4 of 7 agents, the dispatcher group missing entirely, `docbuilder_orchestrator` absent from the run_command group. Never checked until a script counted. That's the whole reason BL-067 existed, shown rather than argued.
- Degrade paths, byte-stability, and the agent-identity fix (the old matrix printed `cot1` for a row whose *file* is `at1cmd.exs` — label mistaken for filename) all check out.

One correction to **my** prompt, which claude-code caught against repo state: I wrote "the nine cap-matrix-{uc} section-agent lines stay" — there are **eight** wired; `capability_matrix_eduloka.exs` exists but is wired nowhere and has no section. My sketch, its repo reality — correctly folded into BL-068 (wire eduloka or delete it) rather than touched here.

One residual worth naming, already correctly scoped to BL-068: the sprint case still runs a full eight-agent regen that destroys curation, and it exits 0 / "capability-matrix.md written" — so anyone who runs `./scripts/sprint.sh capability_matrix` to "refresh the matrix" and commits its output silently loses the curated prose. The runbook now documents "re-run only the changed section" as the normal path and flags the full-regen loss, and BL-068's overrides-file direction retires it. So it's a documented, tracked trap, not a BL-067 defect — but it's why BL-068 is load-bearing (`next` priority), not optional polish. The restore-from-HEAD dance stays a manual ritual until it lands.

Coverage boundary: I read the code, tests, and mutation table; I didn't run them, and I trusted the packet's Rig-source citation (`capability_matrix.rs:44-60`) that the document shape Rig parses is unchanged — low risk, since the per-section tables Rig reads are pasted verbatim and only the derived block changed.

**BL-067 done.** The backlog now carries **BL-068** (give curation a home the section agents can't clobber, and resolve the unwired eduloka agent) and **BL-066** (the bandit bump). Both trees have the manifest/staleness WARNs from this ticket's own commits — exempt, and they'll clear at the next export boundary, which is now the trigger whenever you next refresh project knowledge. Push the three commits when ready and BL-067 is wrapped.
