"""Tests for validate_fields.py (m4 t1).

Pure stdlib — runs in the standard `-m "not integration"` done-check.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from validate_fields import validate

USE_CASE_ROOT = Path(__file__).parent.parent


def _invoice(**overrides):
    base = {
        "title": "Invoice 2627/ACME/01",
        "client_name": "Acme Corp",
        "client_email": "ops@acme.example",
        "date": "2026-06-20",
        "doc_type": "invoice",
        "invoice_number": "2627/ACME/01",
        "client_address": "1 Test St, Testville",
        "amount_due": "$1,000.00",
    }
    base.update(overrides)
    return base


def _offer_letter(**overrides):
    base = {
        "title": "Offer Letter — Ajay Rao",
        "doc_type": "offer_letter",
        "candidate_name": "Ajay Rao",
        "candidate_email": "ajay.rao@example.com",
        "candidate_phone": "980 000 1234",
        "candidate_address": "123, Main Street, Bengaluru, Karnataka - 560012",
        "role": "Software Engineer",
        "date": "2026-07-01",
        "annual_ctc": "₹9,00,000",
        "basic_monthly": "37,500.00",
        "hra_monthly": "18,750.00",
        "lta_monthly": "3,000.00",
        "wfh_allowance_monthly": "3,000.00",
        "flexi_pay_monthly": "12,750.00",
        "total_earnings_monthly": "75,000.00",
        "professional_tax_monthly": "200.00",
        "tds_monthly": "7,500.00",
        "total_deductions_monthly": "7,700.00",
        "net_take_home_monthly": "₹67,300.00",
    }
    base.update(overrides)
    return base


# --- success + normalisation ---

def test_valid_invoice_exit0():
    result, code = validate(_invoice())
    assert code == 0
    assert result["client_name"] == "Acme Corp"
    assert all(k in result for k in ("title", "client_name", "client_email", "date",
                                     "invoice_number", "client_address", "amount_due"))


def test_date_normalised_to_iso():
    result, code = validate(_invoice(date="31-May-2026", order_effective_date="01-Feb-2024"))
    assert code == 0
    assert result["date"] == "2026-05-31"
    assert result["order_effective_date"] == "2024-02-01"


def test_iso_date_passthrough():
    result, code = validate(_invoice(date="2026-06-20"))
    assert code == 0 and result["date"] == "2026-06-20"


def test_currency_uppercased():
    result, code = validate(_invoice(currency="gbp"))
    assert code == 0 and result["currency"] == "GBP"


@pytest.mark.parametrize("raw,expected", [("sgd", "SGD"), ("cad", "CAD"), ("aud", "AUD")])
def test_currency_extended_allowlist(raw, expected):
    # m5 t2: SGD/CAD/AUD added to CURRENCIES — normalised to uppercase, exit 0.
    result, code = validate(_invoice(currency=raw))
    assert code == 0 and result["currency"] == expected


def test_numeric_intermediates_coerced():
    result, code = validate(_invoice(unit_price="1200", line_item_qty="40"))
    assert code == 0
    assert result["unit_price"] == 1200
    assert result["line_item_qty"] == 40


def test_amount_due_kept_as_display_string():
    # m4 t1 divergence: amount_due is render-substituted verbatim → kept a string,
    # NOT coerced to a bare float (which would render "1000.0").
    result, code = validate(_invoice(amount_due="$1,000.00"))
    assert code == 0
    assert result["amount_due"] == "$1,000.00"
    assert isinstance(result["amount_due"], str)


def test_unknown_fields_passthrough():
    result, code = validate(_invoice(deal_type="project", weird_field="kept"))
    assert code == 0
    assert result["deal_type"] == "project"
    assert result["weird_field"] == "kept"


def test_non_invoice_doctype_skips_invoice_fields():
    # proposal: only the 4 base fields are required; invoice-only fields absent → still ok.
    raw = {"title": "B2B Proposal", "client_name": "Acme Corp",
           "client_email": "ops@acme.example", "date": "2026-06-20", "doc_type": "proposal"}
    result, code = validate(raw)
    assert code == 0
    assert "invoice_number" not in result


# --- failures: missing ---

def test_missing_required_field():
    raw = _invoice()
    del raw["client_email"]
    result, code = validate(raw)
    assert code == 1
    assert "client_email" in result["missing"]
    # only the error payload — no normalised fields leak
    assert set(result.keys()) == {"missing", "invalid"}


def test_empty_string_required_is_missing():
    result, code = validate(_invoice(client_name="   "))
    assert code == 1 and "client_name" in result["missing"]


def test_invoice_missing_invoice_number_not_fabricated():
    # open question #1: a fresh invoice missing invoice_number → flagged missing,
    # never defaulted/fabricated.
    raw = _invoice()
    del raw["invoice_number"]
    result, code = validate(raw)
    assert code == 1
    assert "invoice_number" in result["missing"]


# --- failures: invalid ---

def test_invalid_date():
    result, code = validate(_invoice(date="sometime in June"))
    assert code == 1 and "date" in result["invalid"]


def test_unknown_currency():
    result, code = validate(_invoice(currency="XYZ"))
    assert code == 1 and "currency" in result["invalid"]


def test_invalid_email():
    result, code = validate(_invoice(client_email="not-an-email"))
    assert code == 1 and "client_email" in result["invalid"]


def test_unparseable_amount_due():
    result, code = validate(_invoice(amount_due="lots"))
    assert code == 1 and "amount_due" in result["invalid"]


# --- optional fields ---

def test_client_code_optional_absent_ok():
    # open question #2: client_code is optional — absence must NOT force a clarifying round.
    result, code = validate(_invoice())
    assert code == 0
    assert "client_code" not in result["missing"] if isinstance(result.get("missing"), list) else True


def test_client_code_passthrough_when_present():
    result, code = validate(_invoice(client_code="ACME"))
    assert code == 0 and result["client_code"] == "ACME"


# --- CLI (exit codes + file I/O) ---

def _run(input_obj, tmp_path):
    inp = tmp_path / "raw.json"
    out = tmp_path / "validated.json"
    inp.write_text(json.dumps(input_obj))
    r = subprocess.run(
        [sys.executable, "scripts/validate_fields.py", "--input", str(inp), "--output", str(out)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT))
    payload = json.loads(out.read_text()) if out.exists() else None
    return r.returncode, payload


def test_cli_valid_exit0(tmp_path):
    code, payload = _run(_invoice(), tmp_path)
    assert code == 0
    assert payload["client_name"] == "Acme Corp"


def test_cli_missing_exit1(tmp_path):
    raw = _invoice()
    del raw["client_email"]
    code, payload = _run(raw, tmp_path)
    assert code == 1
    assert "client_email" in payload["missing"]
    assert "client_name" not in payload   # error payload only


def test_cli_malformed_input_exit1(tmp_path):
    inp = tmp_path / "raw.json"
    out = tmp_path / "validated.json"
    inp.write_text("{not json")
    r = subprocess.run(
        [sys.executable, "scripts/validate_fields.py", "--input", str(inp), "--output", str(out)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT))
    assert r.returncode == 1
    assert "_input" in json.loads(out.read_text())["invalid"]


# --- offer_letter doc_type (m6 t4) ---

def test_valid_offer_letter_exit0():
    result, code = validate(_offer_letter())
    assert code == 0
    assert result["candidate_name"] == "Ajay Rao"
    assert all(k in result for k in (
        "candidate_name", "candidate_email", "role", "annual_ctc",
        "net_take_home_monthly"))


def test_offer_letter_missing_candidate_name():
    raw = _offer_letter()
    del raw["candidate_name"]
    result, code = validate(raw)
    assert code == 1
    assert "candidate_name" in result["missing"]


def test_offer_letter_missing_net_take_home():
    raw = _offer_letter()
    del raw["net_take_home_monthly"]
    result, code = validate(raw)
    assert code == 1
    assert "net_take_home_monthly" in result["missing"]


def test_offer_letter_invalid_candidate_email():
    result, code = validate(_offer_letter(candidate_email="not-an-email"))
    assert code == 1
    assert "candidate_email" in result["invalid"]


def test_offer_letter_optional_internship_absent_ok():
    # internship_acknowledgement is optional — its absence must not fail validation.
    raw = _offer_letter()
    assert "internship_acknowledgement" not in raw
    result, code = validate(raw)
    assert code == 0


def test_offer_letter_does_not_require_client_fields():
    # Regression guard for the BASE_REQUIRED exclusion: offer letters use candidate_*,
    # so client_name / client_email / title-as-base must NOT be required.
    raw = _offer_letter()
    assert "client_name" not in raw and "client_email" not in raw
    result, code = validate(raw)
    assert code == 0
    assert "client_name" not in result.get("missing", [])
    assert "client_email" not in result.get("missing", [])
