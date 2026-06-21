# Review — m-docbuilder-m2b t3 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes" (--output FILE pattern from m2a learning); docbuilder/docs/milestones/m-docbuilder-m2a-t10-implementation-notes.md (compute_doc --output reference pattern)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — fetch_data --output verified, 9/9 tests, sprint run confirmed (docbuilder-orch-kW_70A, status done, 3 [OK] outputs), exhaustive scratch check EMPTY, output/ listing
Diff: ✅ included (5 files, 110 insertions, 10 deletions)
Implementation notes: ✅ committed — write_file removal decision documented, scratch trajectory table, strengthened rule, forward notes

---

## Findings

1. **[non-blocking]** Dropping `write_file` from the orchestrator tools is the right call
   — it was the last user, and removing dead capability reduces the LLM's misuse surface.
   The negative reminders in the step text ("Do NOT write_file it yourself") now reference
   a tool the LLM no longer has — harmless (can't call an absent tool) and reinforces the
   behaviour. Leave as-is.

2. **[non-blocking]** `test_cli_output_flag_writes_file` uses a minimal CSV rather than the
   committed `sample_data.csv` — the right choice for a fast, deterministic unit test;
   `test_cli_sample_data_has_10_rows` covers the real file. No action.

3. **[positive — CLAUDE.md candidate for t8]** The scratch arc 8 → 1 → 0 is a complete,
   verifiable fix: m2a t8 (problem), m2a t10 (`compute_doc --output`, 1 remained), m2b t3
   (`fetch_data --output` + drop `write_file` from tools + strengthened rule → 0). The
   combined intervention was necessary — `--output` alone left 1 (the LLM re-ran compute to
   inspect); the explicit rule was the final piece. **Candidate for a t8 CLAUDE.md
   promotion:** "Remove `write_file` from an orchestrator's tools once every phase uses
   `--output FILE` — dead capability increases the LLM's misuse surface." **Recorded in the
   t8 prompt.**

---

## Cross-ticket notes

- **t7:** `tools: ["run_command"]` must be preserved in the full orchestrator rebuild; the
  PHASE 0/D/E/F delivery scripts (`rename_output.py`, `upload_output.py`,
  `email_send_review.py`) all use `--output`/stdout, not `write_file` (per t4/t5/t6 scope).
- **Scratch trajectory** table in the t3 notes is the artifact to reference in the t8
  milestone summary.

---

**Outcome: zero blocking findings. t3 clear to merge. t4 clear to start.**
F3's CLAUDE.md candidate recorded in the t8 prompt; F1/F2 are confirmations.
