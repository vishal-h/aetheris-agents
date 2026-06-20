# Review — m-docbuilder-m2a t8 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Agent file conventions", §"Orchestrator patterns", §"Pre-flight checklist"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/runbook.md

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — syntax check exit 0, LLM sprint run confirmed (run_id docbuilder-orch-3qwZ9g, status done), all three [OK] verify lines (xlsx 6.3K, docx 38K, pdf 18K), output/ listing showing per-source intermediates + three branded outputs
Diff — aetheris-agents (b7117e6): ✅ orchestrator, runbook, impl notes (236 insertions, 53 deletions)
Diff — aetheris (390d306): ✅ sprint.sh
Implementation notes: ✅ committed — eval-time template resolution decision documented clearly

---

## Findings

1. **[non-blocking]** Source-path strip (`String.replace_prefix(s["path"] || "",
   "docbuilder/", "")`) handles the demo correctly. On a non-matching prefix
   `replace_prefix/2` returns the original string (pass-through), not a crash —
   acceptable for m2a; the limitation (sources outside `docbuilder/`) is documented.

2. **[non-blocking]** The `<CONTEXT>` placeholder approach (literal JSON shown below the
   args array, substituted verbatim) is confirmed working by the sprint run. Edge case:
   m2b LLM-selected context with arbitrary quote/brace sequences could interact with the
   prompt string — flag as a potential injection point for m2b. Developer-supplied only
   in m2a, so non-blocking.

3. **[non-blocking]** `max_steps` 20 → 30 with documented rationale (9 tool calls +
   reasoning). Appropriate; revisit if a template grows more sources/formats (m2b).

4. **[non-blocking]** sprint.sh `DOCBUILDER_CONTEXT` default uses `\"`-escaped JSON inside
   `${VAR:-default}`. Correct (verified by the run). **Actioned:** added a comment in
   sprint.sh explaining the escaping for future editors.

5. **[question — t9]** t9 (`list_templates.py` + `catalogue.json`) is standalone, no
   orchestrator dependency. Confirmed.

---

## Cross-ticket notes

- **Eval-time template resolution is the right architectural decision** — Elixir
  eval-time code "decides" (which sources to fetch, which renderers get base files); the
  LLM "executes" the concrete step list. A clear evolution from the m1 orchestrator
  (LLM read the doc spec at runtime). **Carry to t10 summary** as a named pattern.
- **Declared-but-unconsumed source fetching enforced in the prompt** ("do not skip any")
  — addresses the t4 risk. ✅
- **t7-review F4 (`DOCBUILDER_CONTEXT` default)** resolved in both the orchestrator
  (Elixir `case → "{}"`) and sprint.sh (`${DOCBUILDER_CONTEXT:-…}`). ✅
- **Runbook updated in-ticket** (methodology runbook-update rule): `DOCBUILDER_CONTEXT`,
  multi-source, base-file/narrative, expected output. ✅
- **t10 Touches confirmed:** capability matrix, `requirements.txt` (pinned),
  `_table_html.py` shared helper, `rig--runbook.md` m2a additions, milestone summary.
  (Note: the `template-schema.md` declared-but-unconsumed note / t4 F1 is already
  resolved — committed 6d1d382 — so it is **not** an outstanding t10 item.)

---

**Outcome: zero blocking findings. t8 clear to merge. t9 clear to start.**
F4 actioned in this push; F1–F3/F5 are confirmations.
