# Review — m-docbuilder-m6 t4b — round 1

Reviewer: claude-ui
Subject: DOCX pipeline wiring — offer-letter end-to-end (commit `93c400b`)

---

## Findings

1. [non-blocking] The t4b done-check prompt uses `compute_doc.py --template <bundle>`
   but the script takes the template as a positional argument. The implementation
   notes document this correctly: "ran the positional form." The corrected command
   should be folded into the t6 docs pass when the milestone doc's t4b smoke command
   is referenced. Carry to t6 Touches: fix the smoke command in the milestone doc's
   §t4b done-check to use the positional form `compute_doc.py <template>` (no
   `--template` flag).

2. [non-blocking] The orchestrator render-steps branch for `docx + narrative? +
   has_jinja?` emits two sequential sub-steps (`C{i}a` and `C{i}b`). The LLM must
   execute these in order — C{i}a writes `output/{prefix}.html`, which C{i}b reads.
   The system prompt instruction "two commands in order" is present. Confirm in t5's
   live run that the LLM correctly executes both steps sequentially and that the
   `<CONTEXT>` substitution in C{i}a's `generate_html.py` call works (same pattern as
   D1 rename and D2 run_log — proven for those, should hold here). If the LLM skips
   or reorders the steps, the orchestrator system prompt needs a stronger ordering
   instruction. No action before t5 — the live run is the gate.

3. [non-blocking] `generate_html.py --spec output/pipeline_spec.json` is passed even
   though the offer letter template uses no `spec.sheets` (the offer letter has no
   table partials). This is harmless — `generate_html.py` passes `spec` to the
   template and the template simply doesn't reference it. Noting for the record;
   confirmed by the smoke (zero `{{` leaks).

## Cross-ticket notes

- F1 (positional arg correction) → t6 Touches: update the milestone doc's t4b
  done-check smoke command.
- F2 (LLM ordering) → t5 watch item: confirm both C{i}a and C{i}b steps execute
  in the `docbuilder_offer_letter` sprint run, and that the final `.docx` file is
  present in `renamed.json`.
- (e) confirmed non-change — `generate_pdf.py` correctly unreachable for docx-only
  bundles. No guard needed.
- The `title` adjudication (d) is correctly recorded: title is required for
  offer_letter because it is the `<h1>` in the template.

Excellent packet. Script-chain smoke passes end-to-end, orchestrator eval confirms the
DOCX-jinja branch fires and the legacy `generate_docx.py` is bypassed, (e) is a confirmed
non-change.

---

## Disposition

**t4b clear to merge as-is** (code unchanged from `93c400b`). All three findings non-blocking.
Carries:
- **F1 → t6:** the milestone doc's §t4b smoke command (and the t6 review-scan range) updated
  to use the positional `compute_doc.py <template>` form. Recorded in the t6 section now.
- **F2 → t5:** the `docbuilder_offer_letter` live run must show both `C{i}a` (generate_html)
  and `C{i}b` (generate_docx_from_html) executing in order, with the `.docx` in `renamed.json`.
  If the LLM reorders/skips, strengthen the ordering instruction in the orchestrator prompt.
- (d)/(e) confirmed; no further action.
