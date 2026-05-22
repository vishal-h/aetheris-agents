import os
import subprocess
import sys
import pytest

PAYSLIP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(PAYSLIP_ROOT, "scripts", "generate_employee_payslips.py")


def run_script(employee_id, tmp_path):
    return subprocess.run(
        [sys.executable, SCRIPT, employee_id, "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=PAYSLIP_ROOT
    )


@pytest.mark.integration
def test_btl_999_exits_zero_and_produces_files(tmp_path):
    result = run_script("BTL_999", tmp_path)
    assert result.returncode == 0, result.stderr
    emp_dir = tmp_path / "BTL_999"
    for stem in ["2026-04-Payslip", "2026-03-Payslip"]:
        assert (emp_dir / f"{stem}.html").exists()
        assert (emp_dir / f"{stem}.pdf").exists()
        assert (emp_dir / f"{stem}.csv").exists()


@pytest.mark.integration
def test_btl_999_apr_2026_html_content(tmp_path):
    result = run_script("BTL_999", tmp_path)
    assert result.returncode == 0, result.stderr
    html = (tmp_path / "BTL_999" / "2026-04-Payslip.html").read_text()
    assert "Anil Rao" in html
    assert "BTL/999" in html
    assert "Basic" in html
    assert "50000.00" in html


@pytest.mark.integration
def test_btl_999_apr_2026_csv_content(tmp_path):
    result = run_script("BTL_999", tmp_path)
    assert result.returncode == 0, result.stderr
    csv_text = (tmp_path / "BTL_999" / "2026-04-Payslip.csv").read_text()
    assert "Anil Rao" in csv_text
    assert "50000.00" in csv_text


@pytest.mark.integration
def test_btl_999_mar_2026_contains_bonus(tmp_path):
    result = run_script("BTL_999", tmp_path)
    assert result.returncode == 0, result.stderr
    html = (tmp_path / "BTL_999" / "2026-03-Payslip.html").read_text()
    assert "Bonus" in html
    csv_text = (tmp_path / "BTL_999" / "2026-03-Payslip.csv").read_text()
    assert "Bonus" in csv_text


@pytest.mark.integration
def test_btl_998_stipend_html_and_csv(tmp_path):
    result = run_script("BTL_998", tmp_path)
    assert result.returncode == 0, result.stderr
    html = (tmp_path / "BTL_998" / "2026-04-Payslip.html").read_text()
    assert "Stipend" in html
    assert "20000.00" in html
    assert "Basic" not in html
    assert "HRA" not in html
    csv_text = (tmp_path / "BTL_998" / "2026-04-Payslip.csv").read_text()
    assert "Stipend" in csv_text


@pytest.mark.integration
def test_btl_997_consultant_html_and_csv(tmp_path):
    result = run_script("BTL_997", tmp_path)
    assert result.returncode == 0, result.stderr
    html = (tmp_path / "BTL_997" / "2026-04-Payslip.html").read_text()
    assert "Consultant Fee" in html
    assert "Arrears" in html
    csv_text = (tmp_path / "BTL_997" / "2026-04-Payslip.csv").read_text()
    assert "Consultant Fee" in csv_text


@pytest.mark.integration
def test_unknown_employee_exits_nonzero(tmp_path):
    result = run_script("BTL_000", tmp_path)
    assert result.returncode != 0
