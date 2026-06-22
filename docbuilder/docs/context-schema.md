# DOCBUILDER_CONTEXT Schema

`DOCBUILDER_CONTEXT` is the single input blob for a docbuilder run — an inline JSON
object passed as an environment variable. It is the source of truth for all per-run
fields: narrative PDF variable substitution, LLM template selection (Option A/B),
output file renaming, and delivery (email recipient).

> Scripts are the authoritative source for which fields each requires — consult the
> script's `main()` validation block if in doubt. This table reflects m2b + the
> Bitloka invoice use case.

---

## How it is passed

```bash
DOCBUILDER_CONTEXT='{"title":"Invoice 2627/XYZ/02","client_name":"XYZ Inc",...}'
```

Unset or empty resolves to `{}` at the orchestrator (never passed empty to scripts).

---

## Field table

| Field | Type | Required | Description | Consumed by |
|-------|------|----------|-------------|-------------|
| `title` | string | ✅ | Document title — used as the narrative PDF heading and in the email subject | `render_template.py`, `email_send_review.py` |
| `client_name` | string | ✅ | Client's display name — slugified for the output filename | `rename_output.py`, `render_template.py`, `email_send_review.py` |
| `client_email` | string | ✅ | External recipient email — appears in the review email body for the ops team to forward to | `email_send_review.py` |
| `date` | string | ✅ | Run date — used in the output filename and narrative PDF. ISO (`2026-06-20`) or display (`31-May-2026`) both accepted; ISO is preferred for predictable filenames | `rename_output.py`, `render_template.py` |
| `doc_type` | string | optional | Explicit doc type for LLM selection (Option A). When set, the LLM picks the variant only; when absent, the LLM picks both doc type and variant (Option B) | Orchestrator eval-time resolution |
| `deal_type` | string | optional | Deal classification hint for LLM template selection (e.g. `"retainer"`, `"project"`, `"support"`) | Orchestrator PHASE 0 LLM prompt |
| `tone` | string | optional | Tone hint: `"formal"` / `"standard"` / `"informal"` | Orchestrator PHASE 0 LLM prompt |
| `amount` | string or number | optional | Deal value — for LLM selection context | Orchestrator PHASE 0 LLM prompt |
| `invoice_number` | string | optional* | Pre-formed invoice number in the tenant's convention (e.g. `"2627/XYZ/02"` for Bitloka: `{FY}/{client_code}/{sequence}`). Required for invoice doc type. | `render_template.py` (via `{{invoice_number}}` in the template) |
| `client_address` | string | optional* | Client's full mailing address. Required for invoice doc type. | `render_template.py` (via `{{client_address}}` in the template) |
| `order_ref` | string | optional | Order or agreement reference number | `render_template.py` |
| `order_effective_date` | string | optional | Date the agreement became effective | `render_template.py` |
| `terms` | string | optional | Payment or engagement terms (e.g. `"Discounted rates for May 26"`) | `render_template.py` |
| `amount_due` | string | optional* | Total amount due on the invoice (e.g. `"$1,000.00"`). Required for invoice doc type. Passed explicitly rather than derived from line items for v1. | `render_template.py` (via `{{amount_due}}` in the template) |

> \* "Required for invoice doc type" means these fields must be present in
> `DOCBUILDER_CONTEXT` when running the Bitloka invoice template. Other doc
> types may not need them.

---

## Complete example — Bitloka invoice (XYZ Inc, May 2026)

```json
{
  "title": "Invoice 2627/XYZ/02",
  "client_name": "XYZ Inc",
  "client_email": "accounts@xyz.example",
  "date": "31-May-2026",
  "doc_type": "invoice",
  "invoice_number": "2627/XYZ/02",
  "client_address": "1234 Stevens Creek Blvd, Suite 123, Santa Clara, California 95051, USA",
  "order_ref": "Agreement-240201",
  "order_effective_date": "01-Feb-2024",
  "terms": "Discounted rates for May 26",
  "amount_due": "$1,000.00"
}
```

## Minimal example — demo proposal

```json
{
  "title": "B2B Proposal",
  "client_name": "Acme Corp",
  "client_email": "ops@acme.example",
  "date": "2026-06-20"
}
```

---

## Validation

- Unknown fields are silently ignored by all scripts.
- `client_name` slugification: lowercase, spaces → underscores, non-ASCII stripped
  (no transliteration — provide an ASCII-safe name if accents matter, e.g.
  `"Muller GmbH"` not `"Müller GmbH"`).
- `date` is filename-sanitised by `rename_output.py`: spaces → underscores, ISO dates
  pass through unchanged. Display dates like `"31-May-2026"` become `"31-May-2026"` in
  the filename (hyphens kept).

---

## Per-script validation summary

| Script | Required fields |
|--------|----------------|
| `rename_output.py` | `client_name`, `date` |
| `email_send_review.py` | `client_name`, `client_email`, `date` |
| `render_template.py` | whichever `{{variable}}` placeholders the template uses |
| Orchestrator (eval) | none required — missing fields degrade gracefully |
