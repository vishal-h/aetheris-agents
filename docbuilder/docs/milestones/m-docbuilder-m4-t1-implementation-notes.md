# Implementation notes — m-docbuilder-m4 t1

Ticket: `validate_fields.py` — schema validation + normalisation for the freeform path.

---

## What shipped

- **`scripts/validate_fields.py`** — `validate(raw) -> (result, exit_code)` (importable) +
  a `--input FILE` / `--output FILE` CLI. Success → writes the normalised context JSON,
  exit 0. Failure → writes ONLY `{"missing": [...], "invalid": {field: reason}}`, exit 1
  (no partial normalised JSON). No LLM, no network. Malformed/unreadable `--input` →
  exit 1 with an `{"invalid": {"_input": …}}` payload (stage-CLI degrade, no traceback).
  - Required (presence, per `doc_type`, default `invoice`): all → title, client_name,
    client_email, date; invoice also → invoice_number, client_address, amount_due.
  - Normalise: `date`/`order_effective_date` → ISO 8601; `currency` → upper + validate
    against `{GBP,USD,EUR,AED,INR}`; `unit_price`/`line_item_qty` → number; `client_email`
    format-checked. Unknown fields pass through unchanged.
- **`tests/test_validate_fields.py`** — 20 tests (logic via `validate()` + CLI via
  subprocess): valid invoice; ISO normalisation + passthrough; currency upper/unknown;
  numeric coercion; missing/empty required; invalid date/email/amount; non-invoice doc_type
  skips invoice-only fields; unknown-field passthrough; the two open-question cases; CLI
  exit 0 / exit 1 / malformed-input.

## Divergence from the t1 spec — flagged for review

**`amount_due` is validated as money but KEPT as a display string — NOT coerced to a
float.** The t1 prompt says "amount fields → float", but `amount_due` is a context-schema
**string** (`"$1,000.00"`) that `render_template.py` substitutes verbatim into the invoice
(`{{amount_due}}`). Coercing it to `1000.0` would regress the rendered invoice to "1000.0"
(the m3-verified render shows "$1,000.00"). So `amount_due` is validated as a parseable
monetary value (rejects "lots") but its string form is preserved. The true numeric
*intermediates* `unit_price`/`line_item_qty` (extraction fields, not in the final context
schema) ARE coerced to numbers per the spec. **Adjudicate:** accept this divergence and
update the m4 doc's normalisation rule (per the m3 doc-divergence learning), or direct
otherwise.

## Open questions (from the milestone doc) — resolved + tested

- **#1 `invoice_number` for fresh invoices.** A fresh invoice missing `invoice_number` is
  flagged in `missing` — never defaulted or fabricated (D1). Tested:
  `test_invoice_missing_invoice_number_not_fabricated`.
- **#2 `client_code`.** Optional — absence does NOT trigger a clarifying round; present →
  passes through unchanged. Tested: `test_client_code_optional_absent_ok`,
  `test_client_code_passthrough_when_present`.
- **#3 `output/` gitignore.** `output/raw_extraction.json` + `output/validated_extraction.json`
  are already gitignored (`git check-ignore` confirms). No action.

## Done-check

- `test_validate_fields.py`: **20 passed**. Full docbuilder suite: **324 passed, 3 skipped**
  (+20). Spot-checks: valid → exit 0 (date → `2026-05-31`); missing email → exit 1
  `{"missing":["client_email"]}`; bad date → exit 1 `invalid:["date"]`.

## Notes

- Date parsing uses a fixed set of `strptime` formats (stdlib only — no `dateutil`):
  ISO, `DD-Mon-YYYY`, `DD Mon YYYY`, `Month DD, YYYY`, etc. A date without a day (e.g.
  "June 2026") is rejected → the operator clarifies (no fabrication).
- The script intentionally does NOT read the tenant catalogue or run log — it validates
  only what it is given (t2 supplies the raw extraction).
