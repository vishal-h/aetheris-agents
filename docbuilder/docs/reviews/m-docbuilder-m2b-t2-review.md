# Review — m-docbuilder-m2b t2 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/drive-structure.md; docbuilder/docs/context-schema.md; drive/scripts/drive_download.py (reference pattern)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 9/9 list_templates, 5/5 + 1 skipped fetch_template, 175/175 + 1 skipped full suite, CLI sanity for both scripts
Diff: ✅ included (text diffs; binary base files in --stat only, acceptable)
Implementation notes: ✅ committed — `_drive.py` addition justified, env-var reconciliation flagged, Option A confirmed, testing-without-creds documented

---

## Findings

1. **[non-blocking]** `_drive.py` is a deliberate addition beyond the listed Touches,
   justified via the `_table_html.py` precedent (three scripts need the same Drive
   plumbing). Lazy google imports are the right call — unit tests import the scripts
   without `googleapiclient`. **Actioned:** added `_drive.py` to the t2 Touches; added a
   t8 capability-matrix note to list it as a shared helper.

2. **[non-blocking]** Env-var reconciliation correctly flagged for t8. Canonical name
   should be `GOOGLE_SERVICE_ACCOUNT_FILE` (the explicit m2b name); the `drive/` scripts
   should align to it, not the other direction. **Actioned:** recorded in the t8 Touches.

3. **[non-blocking]** Nested bundle JSON has repo-root-relative `data_sources[].path`
   (`docbuilder/data/...`). A t7 concern when the orchestrator consumes the cache dir.
   Recommend **Option (a):** strip the `docbuilder/` prefix at eval time (same as the m2a
   source-path strip), no on-disk rewrite. **Actioned:** recorded in the t7 prompt.

4. **[non-blocking]** `@pytest.mark.integration` is informational only — the actual skip
   is the explicit `pytest.skip` when `DRIVE_DOCBUILDER_ID` is absent. Consistent with
   the m2a weasyprint integration tests. No action.

5. **[confirmed]** Nested bundle gitignore: `templates/*/` (one wildcard) only excludes
   `templates/demo/` one level deep; the three-level `demo/proposal/v1/` files are not
   caught and committed correctly. ✅

---

## Cross-ticket notes

- **t5:** add `find_or_create_folder` to `_drive.py` (RW scope) for the `{tenant}/output/`
  target — in the shared helper, not inline in `upload_output.py`. **Recorded in t5 Touches.**
- **t7:** Option (a) for `data_sources` path resolution. **Recorded in t7 prompt.**
- **t8:** capability matrix includes `_drive.py` (shared helper) + the new m2b scripts;
  reconcile the env-var name; `requirements.txt` gains `google-api-python-client`.
  **Recorded in t8 Touches.**

---

**Outcome: zero blocking findings. t2 clear to merge. t3 clear to start.**
F1–F3 forward items folded into the t2/t5/t7/t8 tickets; F4/F5 are confirmations.
