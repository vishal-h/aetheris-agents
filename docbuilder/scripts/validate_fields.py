"""Validate + normalise a raw extracted-field map against the DOCBUILDER_CONTEXT schema.

m4 t1. The freeform path of context_builder.exs has the LLM extract a raw field map from
a natural-language request; this script then deterministically validates + normalises it
(no LLM, no network). On success it writes a clean normalised context JSON to --output and
exits 0. On failure it writes ONLY a structured error payload
  {"missing": [...], "invalid": {field: reason, ...}}
to --output and exits 1 (no partial normalised JSON). The agent reads the payload to
formulate exactly one clarifying question — it never re-derives the rejected values.

Schema (docbuilder/docs/context-schema.md): required for all doc types — title,
client_name, client_email, date; for `invoice` additionally invoice_number,
client_address, amount_due. Fields not in the schema pass through unchanged.

Normalisation:
  - date, order_effective_date  → ISO 8601 (YYYY-MM-DD)
  - currency                    → upper-cased, validated against {GBP,USD,EUR,AED,INR}
  - unit_price, line_item_qty   → numeric (extraction intermediates)
  - amount_due                  → validated as a monetary value but KEPT as its display
                                  string (it is substituted verbatim into the rendered
                                  document — coercing to a bare float regresses the invoice
                                  render). See the m4 t1 implementation notes (divergence
                                  from the doc's "amount fields → float").
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_REQUIRED = ["title", "client_name", "client_email", "date"]
INVOICE_REQUIRED = ["invoice_number", "client_address", "amount_due"]
# offer_letter uses candidate_* aliases (not client_*), so this is the COMPLETE
# required list for the doc type — it replaces BASE_REQUIRED, it is not added to it (m6 t4).
OFFER_LETTER_REQUIRED = [
    "candidate_name", "candidate_email", "candidate_phone", "candidate_address",
    "role", "date", "annual_ctc",
    "basic_monthly", "hra_monthly", "lta_monthly", "wfh_allowance_monthly",
    "flexi_pay_monthly", "total_earnings_monthly",
    "professional_tax_monthly", "tds_monthly", "total_deductions_monthly",
    "net_take_home_monthly",
]
# Hardcoded; extend manually when currency support broadens (m4 t1 F2, m5 t2).
CURRENCIES = {"GBP", "USD", "EUR", "AED", "INR", "SGD", "CAD", "AUD"}
DATE_FIELDS = ("date", "order_effective_date")
NUMERIC_FIELDS = ("unit_price", "line_item_qty")

_DATE_FORMATS = (
    "%Y-%m-%d", "%d-%b-%Y", "%d %b %Y", "%d %B %Y",
    "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%m/%d/%Y",
)


def _present(ctx, key):
    v = ctx.get(key)
    return v is not None and not (isinstance(v, str) and v.strip() == "")


def _normalise_date(value):
    """Parse a date string in any accepted format → ISO 8601; None if unparseable."""
    if not isinstance(value, str):
        return None
    s = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _coerce_number(value):
    """int/float passthrough; numeric string → int (if integral) or float; None if not numeric."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        s = value.replace(",", "").strip()
        try:
            f = float(s)
            return int(f) if f.is_integer() else f
        except ValueError:
            return None
    return None


def _parse_money(value):
    """Float value of a monetary string/number, or None. Used to VALIDATE amount_due only;
    the field itself is kept as its display string."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"[^\d.\-]", "", value.replace(",", ""))
    if cleaned in ("", "-", ".", "-.", "."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _valid_email(value):
    return isinstance(value, str) and "@" in value and "." in value.split("@")[-1]


def validate(raw):
    """Validate + normalise a raw extracted-field map.

    Returns (result, exit_code): success → (normalised_context, 0);
    failure → ({"missing": [...], "invalid": {field: reason}}, 1)."""
    ctx = dict(raw)  # copy; preserves insertion order
    missing = []
    invalid = {}

    doc_type = ctx.get("doc_type") or "invoice"
    if doc_type == "invoice":
        required = BASE_REQUIRED + INVOICE_REQUIRED
    elif doc_type == "offer_letter":
        # Complete list — offer letters use candidate_* fields, NOT client_name/client_email,
        # so BASE_REQUIRED must not apply.
        required = OFFER_LETTER_REQUIRED
    else:
        required = BASE_REQUIRED

    for key in required:
        if not _present(ctx, key):
            missing.append(key)

    # Validate whichever email field is present (client_email for invoice/base,
    # candidate_email for offer_letter).
    for email_key in ("client_email", "candidate_email"):
        if _present(ctx, email_key) and not _valid_email(ctx[email_key]):
            invalid[email_key] = f"not a valid email: {ctx[email_key]!r}"

    for key in DATE_FIELDS:
        if _present(ctx, key):
            iso = _normalise_date(ctx[key])
            if iso is None:
                invalid[key] = f"unparseable date: {ctx[key]!r}"
            else:
                ctx[key] = iso

    if _present(ctx, "currency"):
        cur = str(ctx["currency"]).strip().upper()
        if cur not in CURRENCIES:
            invalid["currency"] = (
                f"unknown currency: {ctx['currency']!r} "
                f"(expected one of {sorted(CURRENCIES)})"
            )
        else:
            ctx["currency"] = cur

    for key in NUMERIC_FIELDS:
        if _present(ctx, key):
            n = _coerce_number(ctx[key])
            if n is None:
                invalid[key] = f"not numeric: {ctx[key]!r}"
            else:
                ctx[key] = n

    if _present(ctx, "amount_due") and _parse_money(ctx["amount_due"]) is None:
        invalid["amount_due"] = f"not a monetary value: {ctx['amount_due']!r}"

    if missing or invalid:
        return {"missing": missing, "invalid": invalid}, 1
    return ctx, 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate + normalise extracted docbuilder context fields.")
    parser.add_argument("--input", required=True, help="raw extracted-field JSON file")
    parser.add_argument("--output", required=True,
                        help="normalised context JSON (exit 0) or error payload (exit 1)")
    args = parser.parse_args()

    out = Path(args.output)

    try:
        raw = json.loads(Path(args.input).read_text())
    except (json.JSONDecodeError, OSError) as e:
        out.write_text(json.dumps(
            {"missing": [], "invalid": {"_input": f"could not read --input: {e}"}},
            indent=2) + "\n", encoding="utf-8")
        sys.exit(1)

    if not isinstance(raw, dict):
        out.write_text(json.dumps(
            {"missing": [], "invalid": {"_input": "input is not a JSON object"}},
            indent=2) + "\n", encoding="utf-8")
        sys.exit(1)

    result, code = validate(raw)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sys.exit(code)


if __name__ == "__main__":
    main()
