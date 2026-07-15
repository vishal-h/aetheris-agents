# Review — BL-001 — round 1

## Findings

1. **[non-blocking]** The canonical backlog text is stale in two places claude-code correctly triaged: "7 PASS" (actual: 8, since the project_knowledge check landed) and "INFOs only for event types with zero DB rows" (actual INFO categories: env_vars and agent-side payload_fields). Per §1.1, the doc gets corrected, not just noted in a packet. Suggested fix: edit BL-001's expectation lines in `docs/backlog-2026-06.md` to match observed reality, in the same push as the status update.

2. **[non-blocking]** Sequencing: the drift run predates commit `d24e482`, and that commit modified `current-state-2026-06.md` — a file with a manifest entry. The `project_knowledge: 16 entries match HEAD` PASS is therefore already stale as of the commit. Not a defect in this ticket, but it means the "clean baseline" line was true at run time, not at HEAD. Suggested fix: fold the manifest refresh into BL-002 (already its job) and re-run drift_check as BL-002's done-check so the baseline claim is re-verified at the new HEAD.

3. **[question]** Nine `payload_fields` INFOs report observed-in-DB fields absent from specs §6 (`prompt_built.key`, `llm_responded.content`, `tool_result.is_error`, etc.). BL-006's own logic says: once observed, promote to §6. Should these nine get the same treatment — either batched into BL-002's doc touch or as a new S ticket (BL-010)? Leaving them as standing INFOs re-creates the noise floor that BL-009's `--strict` promotion is trying to protect against, even though `--strict` only gates WARNs.

## Cross-ticket notes

- The stale-expectation finding (1) is the second instance of ticket text drifting from checker reality (the first being the pre-fix drift outputs that motivated this backlog). If it recurs on one more ticket, it's a §7 promotion candidate: *"Ticket expectations that quote checker output must cite the baseline date they were written against."*
