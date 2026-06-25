# Review — m-docbuilder-m4 t1 — round 1

Reviewer: claude-ui
Subject: `validate_fields.py` — schema validation + normalisation (commit `0479188`)

---

## Decision — `amount_due` display string (flagged divergence)

**Accepted.** `amount_due` is a render-substituted display string (`"$1,000.00"`) —
coercing to float would regress the invoice render to `"1000.0"`. Correct boundary:
LLM-extracted numeric intermediates (`unit_price`, `line_item_qty`) → numbers; context
schema strings substituted verbatim into the rendered document (`amount_due`) → validated
for parseability, kept as the display string. **Actioned (doc):** updated the milestone
doc normalisation rule in three places (D1 amount-normalisation note, t1 scope, t1 prompt)
to: "amount_due → validated as a monetary value, kept as display string (verbatim render
substitution); unit_price/line_item_qty → numeric (extraction intermediates, not in the
final context schema)." Recorded before t2 per the m3 doc-divergence learning.

## Findings

1. **[non-blocking, no action] `test_client_code_optional_absent_ok` assertion is weak.**
   On exit 0, `result` is the normalised context (no `"missing"` key), so the
   `isinstance(... )` guard short-circuits to `True` — the test passes but proves little
   about the exit-0 case. Acceptable: `test_valid_invoice_exit0` covers the base case, and
   this test's value is documenting open-question #2. Noted.

2. **[non-blocking → carried to t5] `CURRENCIES` allowlist is hardcoded** (`{GBP, USD, EUR,
   AED, INR}`). Tenant-agnostic for now; extend when multi-currency support broadens. Low
   priority — noted for the t5 docs sync (no t1 change).

## Cross-ticket notes

- The accepted `amount_due` divergence is now recorded in the milestone doc (this commit),
  so t2 is prompted against the correct rule.
- 20 tests, 324/3 suite — clean foundation for t2.
- Open questions #1 (invoice_number not fabricated), #2 (client_code optional), #3 (output/
  gitignored) all resolved + tested. No forward items.

## Outcome

No t1 **code** changes. One doc fix (milestone normalisation rule → `amount_due`
display-string decision), committed alongside this review. F1/F2 non-blocking, no action
(F2 carried to t5). **t1 clear.**
