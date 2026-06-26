# Review — m-docbuilder-m5 t2 — round 1

Reviewer: claude-ui
Subject: validate_fields CURRENCIES + test housekeeping + client-agnostic sprint
(commits `6407be9` aetheris-agents, `ff574e2` aetheris/sprint.sh)

---

## Findings

1. [blocking — missing evidence, no code change] The done-check output did not show
   the `docbuilder_fresh` sprint result (the client-agnostic assertion hardening), one
   of three changes in t2's Touches. The original packet covered the pytest suite and
   grep checks but not the live sprint case. Confirm the sprint still passes with the
   hardened assertion and include the `[OK]` line.

## Cross-ticket notes

- All three t2 changes are small and correctly scoped. The CURRENCIES comment source
  reference `(m4 t1 F2, m5 t2)` is helpful provenance — correct.
- The client-agnostic sprint assertion from t2 is a prerequisite for the
  `docbuilder_fresh_render` sprint case in t3, which reuses the same pattern. Confirm
  it works before t3 is started.

Clean. 23 tests pass (332/3 suite), docstring fixed, CURRENCIES comment present.

---

## Resolution — F1 evidence (live sprint run)

Ran `DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh` (live LLM agent).
**PASS** — run `docbuilder-ctx-pY_r7g`:

```
[OK]    context_builder.exs evaluates
[INFO]  Request: Invoice for Northwind Traders at billing@northwind.example, ...
[OK]    uc-docbuilder context-builder (fresh) → no-json (225 bytes)
[OK]    confirmed_context.json written + parseable (client: Northwind Traders)
{
  "title": "Invoice 2627/NWT/01",
  "client_name": "Northwind Traders",
  "client_email": "billing@northwind.example",
  "client_address": "12 Harbour Rd",
  "invoice_number": "2627/NWT/01",
  "amount_due": "$3,400.00",
  "date": "2026-06-30",
  "doc_type": "invoice"
}
[OK]    run log not appended (fresh builder run does not trigger PHASE D2)
```

The `[OK]` line now interpolates the parsed `client_name` (`client: Northwind Traders`),
confirming both that (a) the client-agnostic non-empty check passes and (b) the message
correctly reports the actual parsed client rather than the prior hardcoded literal. The
prerequisite for t3's `docbuilder_fresh_render` is satisfied. No code change — F1 was a
missing-evidence item only.

**Disposition: t2 clear to merge.** Code unchanged from `6407be9`/`ff574e2`; this round
adds the sprint evidence the finding requested.
