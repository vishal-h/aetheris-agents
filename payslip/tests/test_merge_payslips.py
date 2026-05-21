import os
import sys
from unittest import mock
import pytest

from payslip.scripts.merge_payslips import main


class FakeResult:
    def __init__(self, returncode=0, stderr=b""):
        self.returncode = returncode
        self.stderr = stderr


def test_html_sorted_descending_before_conversion(tmp_path):
    for name in ["2025-03.html", "2026-04.html", "2025-12.html"]:
        (tmp_path / name).write_text("")

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return FakeResult()

    with mock.patch("payslip.scripts.merge_payslips.subprocess.run", side_effect=fake_run):
        with mock.patch("sys.argv", ["merge_payslips.py", str(tmp_path)]):
            main()

    wk_html_args = [c[1] for c in calls if c[0] == "wkhtmltopdf"]
    basenames = [os.path.basename(p) for p in wk_html_args]
    assert basenames == ["2026-04.html", "2025-12.html", "2025-03.html"]


def test_wkhtmltopdf_called_once_per_html(tmp_path):
    for name in ["2026-04.html", "2025-03.html"]:
        (tmp_path / name).write_text("")

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd[0])
        return FakeResult()

    with mock.patch("payslip.scripts.merge_payslips.subprocess.run", side_effect=fake_run):
        with mock.patch("sys.argv", ["merge_payslips.py", str(tmp_path)]):
            main()

    assert calls.count("wkhtmltopdf") == 2


def test_gs_called_with_temp_pdfs_in_descending_order(tmp_path):
    for name in ["2025-03.html", "2026-04.html"]:
        (tmp_path / name).write_text("")

    all_calls = []

    def fake_run(cmd, **kwargs):
        all_calls.append(list(cmd))
        return FakeResult()

    with mock.patch("payslip.scripts.merge_payslips.subprocess.run", side_effect=fake_run):
        with mock.patch("sys.argv", ["merge_payslips.py", str(tmp_path)]):
            main()

    wk_temp_pdfs = [c[2] for c in all_calls if c[0] == "wkhtmltopdf"]
    gs_call = next(c for c in all_calls if c[0] == "gs")
    # gs args: gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=... <pdfs...>
    gs_pdf_args = gs_call[6:]
    assert gs_pdf_args == wk_temp_pdfs


def test_wkhtmltopdf_failure_exits_nonzero(tmp_path):
    (tmp_path / "2026-04.html").write_text("")

    def fake_run(cmd, **kwargs):
        if cmd[0] == "wkhtmltopdf":
            return FakeResult(returncode=1, stderr=b"conversion error")
        return FakeResult()

    with mock.patch("payslip.scripts.merge_payslips.subprocess.run", side_effect=fake_run):
        with mock.patch("sys.argv", ["merge_payslips.py", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc:
                main()

    assert exc.value.code != 0


def test_empty_directory_exits_zero(tmp_path):
    with mock.patch("payslip.scripts.merge_payslips.subprocess.run") as mock_run:
        with mock.patch("sys.argv", ["merge_payslips.py", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc:
                main()

    assert exc.value.code == 0
    mock_run.assert_not_called()


def test_output_pdf_path_is_merged_pdf(tmp_path):
    (tmp_path / "2026-04.html").write_text("")

    all_calls = []

    def fake_run(cmd, **kwargs):
        all_calls.append(list(cmd))
        return FakeResult()

    with mock.patch("payslip.scripts.merge_payslips.subprocess.run", side_effect=fake_run):
        with mock.patch("sys.argv", ["merge_payslips.py", str(tmp_path)]):
            main()

    gs_call = next(c for c in all_calls if c[0] == "gs")
    output_file_arg = next(a for a in gs_call if a.startswith("-sOutputFile="))
    assert output_file_arg == f"-sOutputFile={tmp_path}/merged.pdf"
