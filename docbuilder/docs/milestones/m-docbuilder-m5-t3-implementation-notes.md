# Implementation notes — m-docbuilder-m5 t3 (`docbuilder_fresh_render` sprint case)

Ticket: add a sprint case that chains the fresh path end-to-end (context builder →
orchestrator → render) and asserts the rendered PDF has zero `{{placeholder}}` artifacts —
the end-to-end proof that m5 t1's `_sub_var` fix holds for fresh-path invoices that omit
optional fields.

---

## What shipped

- **`aetheris/scripts/sprint.sh`** — new `docbuilder_fresh_render` case (also under `all`),
  usage line updated. Structure, combining the `docbuilder_fresh` (fresh extract) and
  `docbuilder_context` (orchestrator + `renamed.json` verification) patterns:
  - **Setup.** `unset DOCBUILDER_CONTEXT`; reset `run_log.json` to `[]`; clear
    `confirmed_context.json`, `raw_extraction.json`, `validated_extraction.json`,
    `renamed.json`. Default `DOCBUILDER_REQUEST` = the Northwind all-fields invoice (same as
    `docbuilder_fresh`). `CONFIRMED_CTX` resolved to an absolute path.
  - **Step 1 — context builder (fresh).** Eval check + `run_agent`; assert
    `confirmed_context.json` written + parseable + `client_name` non-empty (the m5 t2
    client-agnostic check), interpolating the parsed client into the `[OK]` line.
  - **Step 2 — orchestrator.** `DOCBUILDER_CONTEXT` unset + `DOCBUILDER_CONTEXT_FILE` set to
    the confirmed-context path → orchestrator reads the file, renders, runs PHASE D2.
    `DOCBUILDER_CONTEXT_FILE` unset on exit.
  - **Step 3 — verify rendered output.** Loop `renamed.json` (PHASE D's authoritative
    record): each listed file must exist + be non-empty. For the `.pdf` output, run
    `pdftotext <file> - | grep -c '{{'` → must be `0`; if `pdftotext` is absent, emit
    `[INFO]` and skip (degrade, don't fail).
  - **Step 4 — PHASE D2.** `run_log.json` must have exactly 1 entry (seeded `[]` →
    orchestrator appended this run).

## Done-check (live run)

`DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh_render` → **all PASS**, run
`docbuilder-orch-h2yeTQ`:

```
[OK]  context_builder.exs evaluates
[OK]  confirmed_context.json written + parseable (client: Northwind Traders)
[OK]  rendered: northwind_traders_invoice_2026-06-30.xlsx (5.2K)
[OK]  rendered: northwind_traders_invoice_2026-06-30.docx (37K)
[OK]  rendered: northwind_traders_invoice_2026-06-30.pdf (85K)
[OK]  no {{placeholders}} in northwind_traders_invoice_2026-06-30.pdf
[OK]  run log appended (PHASE D2 fired: 0 → 1 entry)
```

The `confirmed_context.json` for Northwind contains **no** `order_ref`, `order_effective_date`,
or `terms` — exactly the optional fields the bitloka invoice template references. Before m5 t1
those would have rendered as literal `{{order_ref}}` etc. in the PDF; the
`no {{placeholders}}` assertion passing is the end-to-end confirmation that t1's fix works on
a real fresh-path render. `bash -n` clean.

## Notes

- `pdftotext` is present in this environment (poppler 22.02.0); the case degrades to `[INFO]`
  where it is absent, so it never fails for a missing optional tool. The m5 doc's m6 open
  questions note a possible future prerequisite check for `pdftotext`.
- `sprint.sh` lives in the sibling `aetheris` repo and is committed there separately.
- The runbook entry for this case was added in this ticket (`docbuilder/runbook.md`), per the
  milestone's runbook-update rule (sprint-case docs belong with the introducing ticket).
