# Review — m-docbuilder-m3 t1 — round 1

Reviewer: claude-ui
Subject: `run_log_writer.py` + orchestrator PHASE D2 hook (commit `5ce5e8b`)

---

## Findings

**1. [non-blocking → actioned] Idempotency semantics diverge from the milestone spec.**
The milestone doc implied "idempotent on the same `run_id`" = exit 0 without appending.
The implementation **replaces** the existing entry (update-in-place). Replacing is the
better behaviour (the log stays accurate), but it deviates from the implied contract.
**Actioned:** recorded the decision in the milestone doc's design-decisions table
("Replace-in-place by `run_id`") so t3's reader knows entries may be updated in-place
and must pick the latest matching entry by order/timestamp.

**2. [no action] Two-level error contract is intentional and correctly tested.**
`_load_log` raises `json.JSONDecodeError` / `ValueError`; `main()` catches and exits 1.
`test_load_malformed_raises` covers the library level; `test_cli_corrupt_existing_log_exits_1`
covers the CLI. Both present. ✅

**3. [withdrawn] `--output FILE` flag missing.** Re-reading the design-decisions table,
`--output FILE` is attributed to `resolve_last_run.py` (t3), not `run_log_writer.py`.
The writer already has `--log-file`. Not a finding.

**4. [no action] Pre-established `run_id` pattern is correct.**
`run_id = "docbuilder-orch-#{Aetheris.ID.generate()}"` at the top, referenced in both
`RunConfig` and the PHASE D2 args. Future-proof for t3 cross-referencing. ✅

**5. [withdrawn] `test_build_entry_default_timestamp` fragility.** On review, `isoformat`
on an aware datetime always produces `±HH:MM`, so `[-6] in "+-"` is the sign character.
Fine for the implementation. Not a finding.

**6. [non-blocking] t5 capability-matrix callout.** Confirm at t5 that `_format.py` is
already in the matrix (it is — added post-m2b in `8613302`) before re-adding; add
`run_log_writer.py` then (→ 19 scripts). Noted for t5.

**7. [blocking → resolved] D2 context-substitution evidence.** The reviewer asked for the
written `run_log.json` entry to confirm the `<CONTEXT>` placeholder was substituted with
the real `DOCBUILDER_CONTEXT` (not a literal string / truncation). **Evidence below** —
entry `docbuilder-orch-iV7NXA` carries the full context object and all 3 renamed outputs.

```json
{
  "tenant": "bitloka",
  "doc_type": "invoice",
  "variant": "v1",
  "run_id": "docbuilder-orch-iV7NXA",
  "timestamp": "2026-06-23T07:33:53+05:30",
  "context": {
    "title": "Invoice 2627/XYZ/02",
    "client_name": "XYZ Inc",
    "client_email": "accounts@xyz.example",
    "date": "31-May-2026",
    "doc_type": "invoice",
    "invoice_number": "2627/XYZ/02",
    "client_address": "1234 Stevens Creek Blvd",
    "order_ref": "Agreement-240201",
    "order_effective_date": "01-Feb-2024",
    "terms": "Discounted rates for May 26",
    "amount_due": "$1,000.00"
  },
  "outputs": [
    "output/xyz_inc_invoice_31-May-2026.xlsx",
    "output/xyz_inc_invoice_31-May-2026.docx",
    "output/xyz_inc_invoice_31-May-2026.pdf"
  ]
}
```

Asserted: `context` is a dict (not `"<CONTEXT>"`), `invoice_number`/`client_name`/
`amount_due` present, `outputs` length 3. ✅

---

## Cross-ticket notes

- Idempotency-as-replace (F1) is now recorded in the milestone doc before t3 starts;
  `resolve_last_run.py` must handle in-place-updated entries and pick the latest match.
- Forward-to-t3 note in the impl notes ("pick the latest by order/timestamp, not assume
  uniqueness of `{client_name, date}`") is correct and reinforced by F1.

---

## Outcome

Two blocking findings, both resolved: **F3 withdrawn** (not applicable), **F7 satisfied**
by the substitution evidence above. F1 actioned (milestone doc updated). F2/F4/F5 are
confirmations/withdrawals; F6 carried to t5. **t1 clear to push.**
