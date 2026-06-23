# Review — m-docbuilder-m3 t2 — round 1

Reviewer: claude-ui
Subject: `context_builder.exs` — NL request → confirmed_context.json (commit `ed96049`)

---

## Findings

1. **[blocking → actioned] `run_command` absent from the tools list.** The milestone
   doc §Design-decisions table specifies the agent's tools as
   `read_file` / `write_file` / `run_command`. `run_command` must be present so t3's
   change (calling `resolve_last_run.py`) is a prompt edit only, not a tools-list edit.
   The agent does not call it in t2; listing it is harmless and keeps the t2→t3 delta
   minimal. **Actioned:** added `run_command` to `tools:` (and aligned the t2 ticket
   bullet's tools line in the milestone doc).

2. **[blocking → adjudicated, actioned] Confirmation gate vs the milestone spec.** The
   doc described an interactive loop ("Confirm? / tell me what to change" → loop →
   write on confirm). The implementation is single-shot: emit a "PROPOSED
   DOCBUILDER_CONTEXT" block AND write `confirmed_context.json`; the operator reviews
   the trajectory before invoking the orchestrator.
   **Human adjudication: accept the single-shot model** — a true interactive loop needs
   a conversational harness not yet built (deferred, out of m3 scope). **Actioned:**
   updated the milestone doc (canonical user story in §Goal, §Design-decisions
   "Confirmation gate" row, t2 scope bullet) to describe the single-shot gate. No code
   change required for this finding.

3. **[non-blocking → actioned] `request` interpolated into the system prompt.** Embedding
   `"#{request}"` inside the `"""` heredoc is safe for embedded `"` but a literal `"""`
   in the request would close the heredoc early; it also forces re-evaluation per
   request. **Actioned (F3 was discretionary):** removed the request interpolation from
   the system prompt — the request now travels solely in `user_prompt`; the system
   prompt refers to "the request in the user message" and is request-independent/reusable.

4. **[no action] `max_steps: 15` + `context_strategy: :full`.** Correct per the
   agent-creation-guide; a ceiling (the builder finishes in ~4–6 steps). Noted. ✅

---

## Cross-ticket notes

- F1 keeps the t2→t3 delta to a prompt edit only.
- F2 milestone-doc edits ensure t3's implementation notes and the t5 sprint runbook are
  written against the correct (single-shot) gate model.
- The interactive confirmation loop ("conversational harness") is explicitly deferred to
  a future milestone — NOT a t4/t5 open item, out of m3 scope.

---

## Outcome

Two blocking findings: **F1 actioned** (tools list), **F2 adjudicated + actioned**
(milestone doc → single-shot gate, no code change). F3 actioned (system-prompt no longer
interpolates the request). F4 no action. **t2 clear after round-2 re-verify.**
