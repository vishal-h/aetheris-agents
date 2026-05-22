import os
from unittest.mock import call, patch
import pytest
from payslip.scripts.merge_employee_payslips import (
    apply_filters,
    find_pdfs,
    merge_pdfs,
    output_filename,
    main,
)

# Paths in ascending (oldest-first) order — the expected output of find_pdfs.
SORTED_PDFS = [
    "output/BTL_999/2025-03-Payslip.pdf",
    "output/BTL_999/2025-04-Payslip.pdf",
    "output/BTL_999/2026-01-Payslip.pdf",
    "output/BTL_999/2026-04-Payslip.pdf",
]


class FakeResult:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.stderr = ""


# --- find_pdfs ---

def test_pdfs_sorted_ascending():
    reversed_pdfs = list(reversed(SORTED_PDFS))
    with patch("payslip.scripts.merge_employee_payslips.glob.glob", return_value=reversed_pdfs):
        result = find_pdfs("output/BTL_999")
    assert result == SORTED_PDFS


# --- apply_filters ---

def test_year_filter_keeps_only_matching_year():
    result = apply_filters(SORTED_PDFS, year="2025")
    assert result == [
        "output/BTL_999/2025-03-Payslip.pdf",
        "output/BTL_999/2025-04-Payslip.pdf",
    ]


def test_from_to_filter_applies_correctly():
    result = apply_filters(SORTED_PDFS, from_month="2025-04", to_month="2026-01")
    assert result == [
        "output/BTL_999/2025-04-Payslip.pdf",
        "output/BTL_999/2026-01-Payslip.pdf",
    ]


def test_from_only_filter():
    result = apply_filters(SORTED_PDFS, from_month="2026-01")
    assert result == [
        "output/BTL_999/2026-01-Payslip.pdf",
        "output/BTL_999/2026-04-Payslip.pdf",
    ]


def test_to_only_filter():
    result = apply_filters(SORTED_PDFS, to_month="2025-04")
    assert result == [
        "output/BTL_999/2025-03-Payslip.pdf",
        "output/BTL_999/2025-04-Payslip.pdf",
    ]


# --- output_filename ---

def test_output_filename_no_filter():
    assert output_filename("BTL_999") == "BTL_999-Annual-Payslips.pdf"


def test_output_filename_year():
    assert output_filename("BTL_999", year="2025") == "BTL_999-2025-Payslips.pdf"


def test_output_filename_from_to():
    assert (
        output_filename("BTL_999", from_month="2025-04", to_month="2026-03")
        == "BTL_999-2025-04-to-2026-03-Payslips.pdf"
    )


# --- merge_pdfs / gs integration ---

def test_gs_called_with_sorted_pdfs_in_correct_order():
    with patch("payslip.scripts.merge_employee_payslips.subprocess.run",
               return_value=FakeResult()) as mock_run:
        merge_pdfs(SORTED_PDFS, "output/BTL_999/BTL_999-Annual-Payslips.pdf")

    gs_args = mock_run.call_args[0][0]
    assert gs_args[0] == "gs"
    assert gs_args[-4:] == SORTED_PDFS


def test_empty_result_after_filter_exits_zero_no_gs(monkeypatch):
    monkeypatch.setattr("sys.argv",
                        ["merge_employee_payslips.py", "BTL_999", "--year", "2099"])
    with patch("payslip.scripts.merge_employee_payslips.glob.glob", return_value=[]):
        with patch("payslip.scripts.merge_employee_payslips.subprocess.run") as mock_run:
            with pytest.raises(SystemExit) as exc:
                main()
    assert exc.value.code == 0
    mock_run.assert_not_called()


def test_output_dir_flag_is_used_as_base(monkeypatch, tmp_path):
    emp_dir = tmp_path / "BTL_999"
    emp_dir.mkdir()
    for stem in ["2026-03-Payslip.pdf", "2026-04-Payslip.pdf"]:
        (emp_dir / stem).write_text("")
    monkeypatch.setattr("sys.argv",
                        ["merge_employee_payslips.py", "BTL_999",
                         "--output-dir", str(tmp_path)])
    with patch("payslip.scripts.merge_employee_payslips.subprocess.run",
               return_value=FakeResult()) as mock_run:
        main()
    gs_args = mock_run.call_args[0][0]
    expected_output = str(emp_dir / "BTL_999-Annual-Payslips.pdf")
    assert any(expected_output in arg for arg in gs_args)


def test_gs_failure_exits_nonzero():
    with patch("payslip.scripts.merge_employee_payslips.subprocess.run",
               return_value=FakeResult(returncode=1)):
        with pytest.raises(SystemExit) as exc:
            merge_pdfs(SORTED_PDFS, "output/BTL_999/BTL_999-Annual-Payslips.pdf")
    assert exc.value.code != 0
