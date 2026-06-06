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


@pytest.mark.integration
def test_runs_log_created_with_correct_fields(tmp_path):
    result = run_script("BTL_999", tmp_path)
    assert result.returncode == 0, result.stderr

    log_path = tmp_path / "runs.log"
    assert log_path.exists(), "runs.log was not created in output dir"

    line = log_path.read_text().strip().splitlines()[0]
    fields = line.split("\t")
    assert len(fields) == 5, f"expected 5 tab-separated fields, got: {line!r}"

    timestamp, month_field, employee_field, files_field, output_field = fields
    assert timestamp.endswith("Z") and "T" in timestamp
    assert month_field == "month=2026-04"
    assert employee_field == "employee=BTL_999"
    # BTL_999 has 2 months → 2 × 2 files (PDF + CSV)
    assert files_field == "files=4"
    assert output_field == f"output={os.path.join(str(tmp_path), 'BTL_999')}"
