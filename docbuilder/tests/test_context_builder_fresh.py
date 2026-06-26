"""Script CLI tests for the freeform fresh path — exercises validate_fields.py via CLI subprocess (no live LLM). m4 t3.

Exercises `validate_fields.py` — the deterministic core of `context_builder.exs`
step-3b — via the script CLI (the same invocation the agent makes through run_command).
No live LLM. Pure stdlib; runs in the standard `-m "not integration"` done-check.
"""

import json
import subprocess
import sys
from pathlib import Path

USE_CASE_ROOT = Path(__file__).parent.parent
SCRIPT = "scripts/validate_fields.py"


def _validate(raw, tmp_path):
    """Run validate_fields.py on a raw extracted-field map; return (exit_code, payload)."""
    inp = tmp_path / "raw_extraction.json"
    out = tmp_path / "validated_extraction.json"
    inp.write_text(json.dumps(raw))
    r = subprocess.run(
        [sys.executable, SCRIPT, "--input", str(inp), "--output", str(out)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT))
    payload = json.loads(out.read_text()) if out.exists() else None
    return r.returncode, payload


def test_fresh_complete_invoice_validates(tmp_path):
    # The map context_builder would extract from a complete freeform invoice request.
    raw = {
        "title": "Invoice 2627/ACME/01", "client_name": "Acme Corp",
        "client_email": "ops@acme.example", "date": "30 June 2026", "doc_type": "invoice",
        "invoice_number": "2627/ACME/01", "client_address": "1 Test St, Testville",
        "amount_due": "$2,000.00",
    }
    code, payload = _validate(raw, tmp_path)
    assert code == 0
    for k in ("title", "client_name", "client_email", "date",
              "invoice_number", "client_address", "amount_due"):
        assert k in payload
    assert payload["date"] == "2026-06-30"        # normalised to ISO 8601
    assert payload["amount_due"] == "$2,000.00"   # display string kept (t1 decision)


def test_fresh_missing_client_email_flags(tmp_path):
    raw = {
        "title": "Invoice 2627/BETA/01", "client_name": "Beta LLC",
        "date": "30 June 2026", "doc_type": "invoice",
        "invoice_number": "2627/BETA/01", "client_address": "9 Side Rd",
        "amount_due": "$500.00",
    }
    code, payload = _validate(raw, tmp_path)
    assert code == 1
    assert "client_email" in payload["missing"]
    assert "client_name" not in payload   # error payload only — no partial context leaks


def test_fresh_intermediates_passthrough(tmp_path):
    # F2 watch (t2 review): extraction intermediates pass through normalised — harmless,
    # the orchestrator ignores fields not in the context schema.
    raw = {
        "title": "Quote", "client_name": "Acme Corp", "client_email": "ops@acme.example",
        "date": "2026-06-30", "doc_type": "proposal",
        "unit_price": "1200", "line_item_qty": "40", "currency": "gbp",
    }
    code, payload = _validate(raw, tmp_path)
    assert code == 0
    assert payload["unit_price"] == 1200          # coerced to number
    assert payload["line_item_qty"] == 40
    assert payload["currency"] == "GBP"           # upper-cased
    # proposal doc_type → invoice-only fields not required
    assert "invoice_number" not in payload
