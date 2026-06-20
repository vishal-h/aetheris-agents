# Review — m-docbuilder-m2a t10 — round 1 (MILESTONE CLOSE)

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6, §7 (milestone-end ritual); aetheris-agents--CLAUDE.md §"Doc-sync DoD"; docbuilder/docs/m2a-milestone.md

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check: ✅ capability matrix grep (render_template + list_templates present), 168/168 full suite, sprint re-run (run docbuilder-orch-8x3XkQ, three [OK] outputs), requirements.txt
Diff: ✅ included (focused code/key-doc diffs)
Implementation notes: ✅ committed
Milestone summary: ✅ written
CLAUDE.md learning promotions: ✅ committed

---

## §7 milestone-end checklist

| Condition | Status |
|---|---|
| All tickets t1–t10 pass done-checks | ✅ 168/168, sprint confirmed |
| All blocking findings resolved | ✅ zero blocking across t1–t10 |
| Capability matrix regenerated, new scripts present | ✅ render_template.py + list_templates.py |
| Learning promotions committed | ✅ verified (finding 1) |
| Milestone summary written | ✅ |
| `compute_doc.py --output FILE` + orchestrator simplification | ✅ scratch 8→1 |
| `_table_html.py` shared helper, both import it | ✅ |
| `requirements.txt` pinned | ✅ |
| `rig/runbook.md` m2a additions | ✅ verified (finding 2) |
| drift checker zero FAIL | ✅ 7 PASS / 0 FAIL / 4 WARN / 12 INFO |

---

## Findings

1. **[verified]** CLAUDE.md m2a learning promotions present and concretely worded — four
   rules: (a) large stdout → `--output FILE` (write-side complement to m1 `--input FILE`);
   (b) two-step optional-field rollout (renderer default → compute_doc pass-through);
   (c) demo/tenant base files must carry named styles + per-sheet branding before the
   sprint; (d) verify a carried finding is actually open before re-flagging.
   *Note:* the reviewer's scan suggested (c) is arguably a tenant-onboarding/runbook item
   rather than a CLAUDE.md rule. Kept in CLAUDE.md as a ≥2-ticket build-process learning
   (recurred t1–t3, actionable for any future base-file agent); the m2b tenant-onboarding
   runbook section should also capture it. Defensible either way; recorded.

2. **[verified]** `rig/runbook.md` m2a additions are in commit abeb977: `DOCBUILDER_CONTEXT`
   env var, multi-source behaviour, base-file/narrative mode, updated expected-output
   listing (per-source `pipeline_raw_*.json`, three branded outputs).

3. **[non-blocking]** Residual sprint scratch: 8 (t8) → 1 (t10). The remaining file ran
   `compute_doc` bare to *inspect* the spec (over-eager investigation), not a functional
   failure — `--output` resolved the t8 large-blob root cause. m2b follow-up recorded in
   the milestone summary (strengthen the rule / add `fetch_data.py --output`; re-verify).

4. **[non-blocking]** Full suite 168 (was 167): +1 from the `--output FILE` test. The
   `_table_html.py` refactor adds no new tests — the existing `generate_pdf`/`render_template`
   tests cover the shared markup. Correct.

---

## Milestone-close status

m2a (t1–t10) is **done**: all done-checks pass, zero blocking findings across the
milestone, capability matrix regenerated, learning promotions committed, milestone summary
written, drift checker zero FAIL.

**Remaining housekeeping (not a blocker, manual):** the drift checker's 4 `project_knowledge`
WARN flag that the Claude.ai project-knowledge copies of `docs/rig/runbook.md`, `CLAUDE.md`,
`docs/capability-matrix.md` (changed in m2a), and `docs/agent-creation-guide.md` (already
stale from m1) need re-export per BL-002 (refresh trigger: milestone end). Advance
`docs/project-knowledge-manifest.md` once the docs are re-uploaded. This requires the
manual export and is owned by the human.

---

## Open items for m2b

- Wire `list_templates.py` into the orchestrator; LLM selection (Options A/B).
- Drive registry + `fetch_template.py`; delivery (Drive upload, email).
- Orchestrator over-inspection: strengthen "don't investigate" rule / add `fetch_data.py --output FILE`.
- Tenant onboarding: base files must include named styles (runbook section).
- Narrative context as injection point once LLM-selected (sanitise before substitution).
