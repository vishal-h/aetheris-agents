# Implementation notes — m-docbuilder-m4 t2

Ticket: `context_builder.exs` step-3b — freeform extraction + one-round clarification.

---

## What shipped

`context_builder.exs` step-3b (the FRESH path) replaced "LIST what is missing and STOP"
with extract → validate → self-correct-once → gate-or-clarify:

- **i.** Extract a raw field map from the freeform request (title, client_name,
  client_email, date, doc_type, invoice fields, and `unit_price`/`line_item_qty`/`currency`
  the text states) → `write_file output/raw_extraction.json`. Extract only what the text
  says; omit rather than guess.
- **ii.** `run_command python3 scripts/validate_fields.py --input output/raw_extraction.json
  --output output/validated_extraction.json` (with the explicit `command:"python3"` /
  no-`python3`-in-args guard).
- **iii.** Exit 0 → `read_file` the validated output and `write_file` its exact contents to
  `output/confirmed_context.json` → step 4 (the unchanged confirmation gate).
- **iv.** Exit 1 → read the `{missing, invalid}` payload, re-read the original request for
  the named fields, re-extract (no fabrication), repeat validation ONCE.
- **v.** Still failing → emit one clarifying request naming the still-missing/invalid
  fields; do NOT write `confirmed_context.json`; STOP.

The recurring path (3a) and the confirmation gate (step 4) are unchanged. Rules updated:
the agent now calls `validate_fields.py` (fresh) as well as `resolve_last_run.py`
(recurring); never writes `confirmed_context.json` from an exit-1 validation; never
fabricates a value a script rejected.

## Divergence from the t2 prompt — flagged for review

**No in-run human clarification round; the "one round" is a self-correction re-pass.** The
t2 prompt says "ask the operator one clarifying question, **wait for the reply**, re-extract
incorporating the reply." But `context_builder` runs single-shot via `mix aetheris run`
(the Rig panel and the t4 chain both invoke it that way), there is no in-run channel for a
human reply, and the prompt explicitly forbids adding an `ask_human` tool. This is the same
constraint as the m3 single-shot confirmation gate. So step-3b's second pass is the agent
**re-reading the original request** for fields the first extraction missed (real
under-extraction recovery); if a required field is genuinely absent, validation fails again
and the agent emits the clarifying question and stops — the operator's "reply" is a
**re-run with the field included** (out-of-run). Verified: a missing `client_email` produced
exactly that message and no `confirmed_context.json`. **Adjudicate:** accept this
single-shot interpretation and update the m4 doc's D2 / step-3b wording (per the m3
doc-divergence learning), or direct otherwise.

## Done-check

- Eval: `mix run --eval Code.eval_file(...)` → EXIT 0.
- **Case A** (freeform invoice, all required fields) — run `docbuilder-ctx-PQ2tdg` → done;
  `confirmed_context.json` written: client Acme Corp, email present, `date` normalised to
  `2026-06-30`, invoice `2627/ACME/01`, `amount_due` kept as `"$2,000.00"` (string, per the
  t1 decision). Intermediates `raw_extraction.json` + `validated_extraction.json` present.
- **Case B** (invoice missing `client_email`) — run `docbuilder-ctx-11czdw` → done;
  `validated_extraction.json` = `{"missing":["client_email"],"invalid":{}}`; agent emitted
  "I need the following to proceed: client_email. Please re-run with this included.";
  **no** `confirmed_context.json` written (correct — the chain/orchestrator won't render an
  incomplete context).
- Full docbuilder suite: **324 passed, 3 skipped** (no Python changed in t2).

## Notes

- `confirmed_context.json` from the fresh path may include passthrough intermediates
  (`unit_price`/`line_item_qty`/`currency`) — harmless; the schema says unknown fields are
  ignored downstream by all scripts.
- t3 automates the fresh-path assertions (the deterministic core via `validate_fields.py`)
  + the `docbuilder_fresh` sprint case.
