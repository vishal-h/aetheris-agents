# Review — m-docbuilder-m4 t2 — round 1

Reviewer: claude-ui
Subject: `context_builder.exs` step-3b — freeform extraction + clarification (commit `0418ce2`)

---

## Decision — single-shot clarification (flagged divergence)

**Accepted.** `context_builder.exs` runs single-shot via `mix aetheris run` — no in-run
human-reply channel, and `ask_human` is intentionally excluded from tools (identical to the
m3 confirmation-gate decision, t2/F2). The "one round" is a **self-correction re-pass**:
the agent re-reads the original request for under-extracted fields and re-validates once; if
a required field is genuinely absent it emits one clarifying message and stops without
writing `confirmed_context.json` — the operator's "reply" is a re-run with the field.
**Actioned (doc-only):** updated the milestone doc —
- §D2 rewritten as "Ambiguity loop depth (single-shot self-correction)" with the full
  rationale and a pointer to the step-iv parenthetical.
- §t2 Scope step-3b wording → "self-correct once; re-read the original request; no in-run
  human reply".
- §t2 Claude-code prompt branches 3b/3c → aligned (removed "wait for the reply").

(No separate "Design decisions table" exists in the m4 doc — it uses prose D1–D4; the model
is captured in D2.)

## Findings

1. **[no action] Gate behaviour.** `confirmed_context.json` is NOT written on validation
   failure (Case B verified) — correct; the chain/orchestrator won't render an incomplete
   context. Noted.

2. **[no action → t3 watch] Passthrough intermediates.** Fresh-path `confirmed_context.json`
   may carry `unit_price`/`line_item_qty`/`currency` (harmless — schema ignores unknown
   fields downstream). t3 should confirm they appear in `raw_extraction.json` /
   `validated_extraction.json` and don't break the orchestrator. No t2 action.

3. **[verified] step-iv parenthetical survives.** The agent prompt's "this run cannot pause
   for a human reply; the second pass is your own re-read" is intact in
   `context_builder.exs`, and the milestone doc's D2 + prompt 3b now both reference/encode
   it. Confirmed.

## Cross-ticket notes

- The single-shot adjudication is recorded in the milestone doc before t3 is prompted.
- **t5 learning-scan candidate:** the single-shot harness constraint has now resolved an
  interactive-loop design question identically in **m3 (confirmation gate)** and **m4
  (clarification round)**. If it recurs in t3/t4, promote to CLAUDE.md as a standing
  instruction ("single-shot `mix aetheris run`: no interactive loops / `ask_human`;
  resolve as self-correction + stop-and-re-run").

## Outcome

No t2 **code** changes. Doc-only fix (D2 + t2 scope + t2 prompt wording) recording the
accepted single-shot model. F1/F2/F3 no action. **t2 clear.**
