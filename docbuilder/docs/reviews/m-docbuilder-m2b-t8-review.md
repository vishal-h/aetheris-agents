# Review — m-docbuilder-m2b t8 — round 1 (MILESTONE CLOSE)

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6, §7 (milestone-end ritual); aetheris-agents--CLAUDE.md §"Doc-sync DoD"; docbuilder/docs/m2b-milestone.md

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — capability matrix grep (all 4 new m2b scripts + _drive helper), 202/202 + 3 skipped docbuilder suite, 34/34 drive suite, drift_check 0 FAIL / 3 WARN (project-knowledge re-export, BL-002)
Diff: ✅ included (9 files, 222 insertions, 55 deletions)
Implementation notes: ✅ committed — max_steps bump, hand-added underscore helpers, reconciliation, 3 CLAUDE.md promotions
Milestone summary: ✅ written
CLAUDE.md learning promotions: ✅ 3 in `## Learning — m2b-docbuilder`

---

## §7 milestone-end checklist

| Condition | Status |
|---|---|
| All tickets t1–t8 pass done-checks | ✅ 202 + 3 integration skips, sprint confirmed |
| All blocking findings resolved | ✅ zero blocking across t1–t8 |
| Capability matrix regenerated, new scripts present | ✅ 4 new + _drive helper |
| Learning promotions committed | ✅ 3 |
| Milestone summary written | ✅ |
| `requirements.txt` updated | ✅ google-api-python-client==2.196.0 |
| env-var reconciliation | ✅ drive_download.py; drive suite 34 passed |
| `rig/runbook.md` m2b + retirement | ✅ |
| README m2b → done | ✅ |
| drift_check 0 FAIL | ✅ 0 FAIL / 3 WARN (project-knowledge, human-owned) |

---

## Findings (all non-blocking)

1. The capability matrix agent dropped `_drive.py` / `_table_html.py` (underscore →
   treated as private). Hand-addition before assemble is the right fix. **Actioned:**
   added a line to `capability_matrix_docbuilder.exs` Step 3 — "Collect ALL .py filenames,
   INCLUDING underscore-prefixed shared helpers … Skip only __init__.py and conftest.py."
   Prevents the same manual fix at m3.

2. `drive_upload.py` imports `build_service` from `drive_download.py`, so the
   `GOOGLE_SERVICE_ACCOUNT_FILE` fallback applies automatically. Confirmed (it imports,
   doesn't redefine); drive suite 34 passed. ✅

3. The `_helper.py` CLAUDE.md promotion mentions "lazy heavy imports inside functions" —
   `_table_html.py` is stdlib-only (no lazy imports), so that clause applies to `_drive.py`
   (canonical example). The general guidance is correct; `_table_html.py` is the simpler
   structural case. No change.

---

## Milestone-close assessment

**m-docbuilder-m2b is done.** All t1–t8 pass; zero blocking across the milestone;
capability matrix correct; 3 CLAUDE.md promotions committed; milestone summary written;
drift 0 FAIL.

**Remaining housekeeping (manual, human-owned — same as m2a):** the 3 project-knowledge
WARNs flag the Claude.ai project copies of `CLAUDE.md`, `docs/capability-matrix.md`,
`docs/rig/runbook.md` are stale. Re-upload + advance `docs/project-knowledge-manifest.md`
(BL-002).

---

## Open items for m3 / follow-up (carried)

- Option C (NL request → extraction → confirmation gate → render)
- Conversational template editing (patch schema + JSONL edit log)
- `email_send_review --drive-links-file` (remove PHASE F runtime dependency)
- `rename_output.py --dry-run` (remove the orchestrator's Elixir slug replica)
- Multi-variant runtime template selection
- `${VAR:-{...}}` audit across other sprint.sh use-case defaults
- Drive base-file checklist enforcement at tenant onboarding

---

**Outcome: zero blocking findings. m-docbuilder-m2b is done.**
F1 actioned (cap-matrix prompt); F2/F3 are confirmations.
