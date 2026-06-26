# Review — m-docbuilder-m5 t4 — sign-off (milestone close)

Reviewer: claude-ui
Subject: m5 close — docs sync, milestone summary, learning scan, t1/F1 smoke fix
(commit `7d79b27`)

---

## Checklist verification

| Item | Verified |
|------|----------|
| t1–t3 all closed; review files committed | ✅ |
| `docs/capability-matrix.md` — `render_template.py` description updated with m5 note | ✅ grep confirms |
| `docs/rig/runbook.md` — `docbuilder_fresh_render` mention in m4 section | ✅ grep confirms |
| Milestone summary appended | ✅ confirmed in `7d79b27` ("Status: complete. Closed 2026-06-26") |
| `## Learning — m5-docbuilder` in `CLAUDE.md` | ✅ confirmed in `7d79b27` ("No recurring findings in this milestone") |
| t1/F1 smoke command correction in milestone doc | ✅ confirmed in `7d79b27` — see note below |
| Drift: 0 FAIL (3 `project_knowledge` WARNs = BL-002 re-upload, expected) | ✅ |

## Note on the t1/F1 smoke-command form

The checklist expected `--spec '{"sheets":[]}'`. Claude-code correctly diverged: `--spec`
is a **path or `-` (stdin)**, not inline JSON, so `--spec '{"sheets":[]}'` would be read as a
(nonexistent) filename. The committed correction uses the script's stdin contract —
`echo '{"sheets":[]}' | … --spec -` — with the real `invoice_v1.*` asset filenames. Verified
runnable: `grep -c '{{'` = 0 and the renderer actually executes (no longer a trivial 0 from a
failed JSON-parse). The t4 Touches note was updated to match. **Accepted — the divergence is
the correct invocation.**

## Observations

- 3 WARNs are all BL-002 (CLAUDE.md, capability-matrix.md, docs/rig/runbook.md ahead
  of manifest). Expected; cleared by re-upload + manifest advance.
- No recurring findings across t1–t3 — `## Learning — m5-docbuilder` records exactly that.
- Beyond-Touches doc-accuracy fix accepted: t2's client-agnostic change made a "Known
  limitation" claim false in *both* runbooks; t4 corrected `docbuilder/runbook.md` as well as
  `docs/rig/runbook.md`. Correct call — the close is the place to sweep doc drift.

## BL-002 (human-owned — required to clear drift WARNs)

Re-upload to the Claude.ai project:
- `aetheris-agents--CLAUDE.md` (advanced by the pre-milestone single-shot promotion)
- `docs/capability-matrix.md`
- `docs/rig/runbook.md` (advanced by t3 + t4)

Then advance `docs/project-knowledge-manifest.md` to `7d79b27` and re-run drift_check
to confirm 0 FAIL / 0 WARN.

## Outcome

**m5 complete. t1–t4 merged.** The freeform fresh→render chain ships with zero `{{`
artifacts, proven end-to-end (run `docbuilder-orch-h2yeTQ`). All three "to confirm" items
verified present in `7d79b27`. Clear to merge; BL-002 re-upload is the remaining human-owned
step.
