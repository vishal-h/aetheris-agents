import pytest
from payslip.scripts.payslip_compute import (
    col_label,
    compute_month,
    month_file,
    group_by_employee,
    build_output,
)


DEFAULT_CONFIG = {
    'stipend_threshold': 25000,
    'consultant_type_value': 'consultant',
    'regular_breakdown': {
        'basic_pct':      0.50,
        'hra_pct':        0.50,
        'lta_fixed':      3000.00,
        'wfh_fixed':      3000.00,
        'flexi_residual': True,
    },
    'labels': {
        'e_sal':           'Base Salary',
        'd_pt':            'Professional Tax',
        'd_tds':           'TDS',
        'd_tds_94j':       'TDS (94J)',
        'd_loan_recovery': 'Loan Recovery',
    },
}

EXTRA_COLS      = ['e_bonus']
DEDUCTIONS_COLS = ['d_loan_recovery', 'd_pt', 'd_tds_94j', 'd_tds']
ARREARS_COLS    = ['e_arrears_jan_feb_2025']


def make_row(**overrides):
    base = {
        "employee_id":             "BTL/001",
        "employee_type":           "Regular",
        "designation":             "Engineer",
        "name":                    "Test User",
        "email":                   "test@example.com",
        "pan":                     "ABCDE1234F",
        "doj":                     "01-Jan-2020",
        "month":                   "Apr 2026",
        "paid_in":                 "May 2026",
        "e_sal":                   "100000",
        "e_bonus":                 "0",
        "e_arrears_jan_feb_2025":  "0",
        "d_loan_recovery":         "",
        "d_pt":                    "200",
        "d_tds_94j":               "",
        "d_tds":                   "10000",
        "work_mode":               "Hybrid",
        "account_number":          "BANK1234 / 123456",
    }
    base.update(overrides)
    return base


# ─── Earnings breakdown ────────────────────────────────────────────────────

def test_regular_earnings_breakdown():
    row = make_row(e_sal="100000", d_pt="200", d_tds="10000")
    result = compute_month(row, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, [])
    labels = {e["label"]: e["amount"] for e in result["earnings"]}
    assert labels["Basic"] == 50000.0
    assert labels["HRA"] == 25000.0
    assert labels["LTA"] == 3000.0
    assert labels["WFH Allowance"] == 3000.0
    assert labels["Flexi Pay"] == 19000.0
    assert result["earnings_type"] == "regular"


def test_stipend_single_entry():
    row = make_row(employee_type="Regular", e_sal="20000", d_pt="0", d_tds="0")
    result = compute_month(row, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, [])
    assert result["earnings_type"] == "stipend"
    assert len(result["earnings"]) == 1
    assert result["earnings"][0]["label"] == "Stipend"
    assert result["earnings"][0]["amount"] == 20000.0


def test_stipend_zero_deductions():
    row = make_row(employee_type="Regular", e_sal="20000", d_pt="0", d_tds="0", d_loan_recovery="")
    result = compute_month(row, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, [])
    assert result["deductions"] == []


def test_consultant_fee_and_tds_94j():
    row = make_row(
        employee_type="Consultant",
        e_sal="80000",
        d_tds="",
        d_tds_94j="8000",
        d_pt="0",
    )
    result = compute_month(row, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, [])
    assert result["earnings_type"] == "consultant"
    assert len(result["earnings"]) == 1
    assert result["earnings"][0]["label"] == "Consultant Fee"
    tds_entry = next((d for d in result["deductions"] if d["label"] == "TDS (94J)"), None)
    assert tds_entry is not None
    assert tds_entry["amount"] == 8000.0


def test_bonus_separate_entry():
    row = make_row(e_sal="100000", e_bonus="25000")
    result = compute_month(row, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, [])
    labels = [e["label"] for e in result["earnings"]]
    assert "Bonus" in labels
    assert labels.index("Bonus") > labels.index("Basic")
    bonus_entry = next(e for e in result["earnings"] if e["label"] == "Bonus")
    assert bonus_entry["amount"] == 25000.0


def test_arrears_detected_and_appended():
    arrears_col = "e_arrears_jan_feb_2025"
    row = make_row(**{arrears_col: "5000"})
    result = compute_month(row, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, [arrears_col])
    labels = [e["label"] for e in result["earnings"]]
    expected_label = col_label(arrears_col, {})
    assert expected_label in labels
    arrears_entry = next(e for e in result["earnings"] if e["label"] == expected_label)
    assert arrears_entry["amount"] == 5000.0


# ─── Sorting & filtering ───────────────────────────────────────────────────

def test_multiple_months_sorted_newest_first():
    rows = [
        make_row(employee_id="BTL/001", month="Jan 2026", paid_in="Feb 2026"),
        make_row(employee_id="BTL/001", month="Apr 2026", paid_in="May 2026"),
        make_row(employee_id="BTL/001", month="Mar 2026", paid_in="Apr 2026"),
    ]
    employees = group_by_employee(rows, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, ARREARS_COLS)
    months = [m["month"] for m in employees["BTL_001"]["months"]]
    assert months == ["Apr 2026", "Mar 2026", "Jan 2026"]


def test_employee_id_filter():
    rows = [
        make_row(employee_id="BTL/001"),
        make_row(employee_id="BTL/002"),
    ]
    output = build_output(rows, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, ARREARS_COLS, filter_id="BTL_001")
    assert len(output["employees"]) == 1
    assert output["employees"][0]["employee_id_safe"] == "BTL_001"


def test_employee_id_not_found():
    rows = [make_row(employee_id="BTL/001")]
    with pytest.raises(SystemExit) as exc:
        build_output(rows, DEFAULT_CONFIG, EXTRA_COLS, DEDUCTIONS_COLS, ARREARS_COLS, filter_id="BTL_999")
    assert exc.value.code != 0


# ─── month_file helper ─────────────────────────────────────────────────────

def test_month_file_apr_2026():
    assert month_file("Apr 2026") == "2026-04"


def test_month_file_dec_2024():
    assert month_file("Dec 2024") == "2024-12"
