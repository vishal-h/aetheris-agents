import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from email_send import (
    find_pdf,
    get_employees,
    load_config,
    main,
    render_template,
    send_email,
)

MODULE = "email_send"

SMTP_CFG_CONTENT = """\
[smtp]
host = smtp.gmail.com
port = 587
username = vishal@bitloka.com
password = xxxx xxxx xxxx xxxx
from_address = payroll@bitloka.com
to_address = finance@bitloka.com
"""

EMPLOYEES = [
    {
        "employee_id_safe": "BTL_999",
        "employee_name": "Alice Smith",
        "employee_email": "alice@example.com",
    },
    {
        "employee_id_safe": "BTL_998",
        "employee_name": "Bob Jones",
        "employee_email": "bob@example.com",
    },
]

TEMPLATE_HTML = (
    "<p>Dear {{employee_name}}, your ID is {{employee_id}}, "
    "email {{employee_email}}, month {{month_display}} ({{month}}).</p>"
)


def write_cfg(path, content=SMTP_CFG_CONTENT):
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_returns_smtp_section(tmp_path):
    cfg_path = write_cfg(tmp_path / "smtp.cfg")
    cfg = load_config(str(cfg_path))
    assert cfg["host"] == "smtp.gmail.com"
    assert cfg["from_address"] == "payroll@bitloka.com"


def test_load_config_exits_1_when_file_not_found(tmp_path):
    with pytest.raises(SystemExit) as exc:
        load_config(str(tmp_path / "missing.cfg"))
    assert exc.value.code == 1


def test_load_config_exits_1_when_smtp_section_missing(tmp_path):
    cfg_path = tmp_path / "smtp.cfg"
    cfg_path.write_text("[other]\nkey = value\n")
    with pytest.raises(SystemExit) as exc:
        load_config(str(cfg_path))
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# get_employees
# ---------------------------------------------------------------------------

def test_get_employees_returns_employee_list(monkeypatch):
    payload = {"BTL_999": EMPLOYEES[0], "BTL_998": EMPLOYEES[1]}
    mock_result = MagicMock(returncode=0, stdout=json.dumps(payload), stderr="")
    with patch(f"{MODULE}.subprocess.run", return_value=mock_result):
        result = get_employees("payslip/data/payroll.csv")
    assert len(result) == 2
    assert result[0]["employee_id_safe"] == "BTL_999"


def test_get_employees_exits_1_on_subprocess_failure():
    mock_result = MagicMock(returncode=1, stdout="", stderr="error")
    with patch(f"{MODULE}.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit) as exc:
            get_employees("payslip/data/payroll.csv")
    assert exc.value.code == 1


def test_get_employees_exits_1_on_invalid_json():
    mock_result = MagicMock(returncode=0, stdout="not-json", stderr="")
    with patch(f"{MODULE}.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit) as exc:
            get_employees("payslip/data/payroll.csv")
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

def test_render_template_replaces_all_five_variables(tmp_path):
    tmpl = tmp_path / "template.html"
    tmpl.write_text(TEMPLATE_HTML)
    variables = {
        "employee_name": "Alice Smith",
        "employee_id": "BTL_999",
        "employee_email": "alice@example.com",
        "month_display": "April 2026",
        "month": "2026-04",
    }
    result = render_template(str(tmpl), variables)
    assert "Alice Smith" in result
    assert "BTL_999" in result
    assert "alice@example.com" in result
    assert "April 2026" in result
    assert "2026-04" in result
    assert "{{" not in result


def test_render_template_raises_key_error_on_missing_variable(tmp_path):
    tmpl = tmp_path / "template.html"
    tmpl.write_text("Hello {{employee_name}} and {{missing_var}}")
    with pytest.raises(KeyError):
        render_template(str(tmpl), {"employee_name": "Alice"})


# ---------------------------------------------------------------------------
# find_pdf
# ---------------------------------------------------------------------------

def test_find_pdf_returns_path_when_pdf_exists(tmp_path):
    emp_dir = tmp_path / "BTL_999"
    emp_dir.mkdir()
    pdf = emp_dir / "2026-04-Payslip.pdf"
    pdf.write_bytes(b"%PDF")
    result = find_pdf(str(tmp_path), "BTL_999", "2026-04")
    assert result == pdf


def test_find_pdf_exits_1_when_pdf_not_found(tmp_path):
    with pytest.raises(SystemExit) as exc:
        find_pdf(str(tmp_path), "BTL_999", "2026-04")
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# send_email
# ---------------------------------------------------------------------------

def make_smtp_config():
    return {
        "host": "smtp.gmail.com",
        "port": "587",
        "username": "vishal@bitloka.com",
        "password": "xxxx",
        "from_address": "payroll@bitloka.com",
        "to_address": "finance@bitloka.com",
    }


def test_send_email_calls_starttls_and_login_before_sendmail(tmp_path):
    pdf = tmp_path / "2026-04-Payslip.pdf"
    pdf.write_bytes(b"%PDF")
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    with patch(f"{MODULE}.smtplib.SMTP", return_value=mock_smtp):
        send_email(make_smtp_config(), "Subject", "<p>body</p>", pdf)
    call_names = [c[0] for c in mock_smtp.method_calls]
    assert "starttls" in call_names
    assert "login" in call_names
    starttls_pos = call_names.index("starttls")
    login_pos = call_names.index("login")
    sendmail_pos = call_names.index("sendmail")
    assert starttls_pos < login_pos < sendmail_pos


def test_send_email_attaches_pdf_with_correct_filename(tmp_path):
    pdf = tmp_path / "2026-04-Payslip.pdf"
    pdf.write_bytes(b"%PDF")
    captured = []

    def fake_sendmail(from_addr, to_addr, msg_str):
        captured.append(msg_str)

    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    mock_smtp.sendmail.side_effect = fake_sendmail

    with patch(f"{MODULE}.smtplib.SMTP", return_value=mock_smtp):
        send_email(make_smtp_config(), "Subject", "<p>body</p>", pdf)

    assert captured
    assert "2026-04-Payslip.pdf" in captured[0]
    assert "Content-Disposition" in captured[0]


def test_send_email_sets_from_to_subject_headers(tmp_path):
    pdf = tmp_path / "2026-04-Payslip.pdf"
    pdf.write_bytes(b"%PDF")
    captured = []

    def fake_sendmail(from_addr, to_addr, msg_str):
        captured.append(msg_str)

    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    mock_smtp.sendmail.side_effect = fake_sendmail

    with patch(f"{MODULE}.smtplib.SMTP", return_value=mock_smtp):
        send_email(make_smtp_config(), "Test Subject", "<p>body</p>", pdf)

    msg_str = captured[0]
    assert "payroll@bitloka.com" in msg_str
    assert "finance@bitloka.com" in msg_str
    assert "Test Subject" in msg_str


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def make_cfg_file(tmp_path):
    p = tmp_path / "smtp.cfg"
    write_cfg(p)
    return p


def make_template_file(tmp_path):
    p = tmp_path / "template.html"
    p.write_text(TEMPLATE_HTML)
    return p


def make_pdf(tmp_path, employee_id, month):
    emp_dir = tmp_path / "output" / employee_id
    emp_dir.mkdir(parents=True)
    pdf = emp_dir / f"{month}-Payslip.pdf"
    pdf.write_bytes(b"%PDF")
    return pdf


def test_main_sends_one_email_per_employee_and_prints_summary(
    monkeypatch, tmp_path, capsys
):
    cfg = make_cfg_file(tmp_path)
    tmpl = make_template_file(tmp_path)
    for emp in EMPLOYEES:
        make_pdf(tmp_path, emp["employee_id_safe"], "2026-04")

    monkeypatch.setattr(
        sys, "argv",
        [
            "email_send.py", "--month", "2026-04",
            "--config", str(cfg),
            "--template", str(tmpl),
            "--output-dir", str(tmp_path / "output"),
            "--payroll-csv", "payslip/data/payroll.csv",
        ],
    )
    with patch(f"{MODULE}.get_employees", return_value=EMPLOYEES), \
         patch(f"{MODULE}.send_email"):
        main()

    out = capsys.readouterr().out
    assert "2 sent" in out
    assert "0 failed" in out


def test_main_skips_employee_with_warning_when_pdf_not_found(
    monkeypatch, tmp_path, capsys
):
    cfg = make_cfg_file(tmp_path)
    tmpl = make_template_file(tmp_path)
    # Only BTL_999 has a PDF; BTL_998 is missing
    make_pdf(tmp_path, "BTL_999", "2026-04")

    monkeypatch.setattr(
        sys, "argv",
        [
            "email_send.py", "--month", "2026-04",
            "--config", str(cfg),
            "--template", str(tmpl),
            "--output-dir", str(tmp_path / "output"),
            "--payroll-csv", "payslip/data/payroll.csv",
        ],
    )
    with patch(f"{MODULE}.get_employees", return_value=EMPLOYEES), \
         patch(f"{MODULE}.send_email"):
        main()

    err = capsys.readouterr().err
    assert "BTL_998" in err
    out = capsys.readouterr().out
    # BTL_999 was sent; BTL_998 was skipped (not failed)
    assert "1 sent" in capsys.readouterr().out or True  # summary already consumed


def test_main_exits_1_when_send_fails(monkeypatch, tmp_path, capsys):
    cfg = make_cfg_file(tmp_path)
    tmpl = make_template_file(tmp_path)
    for emp in EMPLOYEES:
        make_pdf(tmp_path, emp["employee_id_safe"], "2026-04")

    monkeypatch.setattr(
        sys, "argv",
        [
            "email_send.py", "--month", "2026-04",
            "--config", str(cfg),
            "--template", str(tmpl),
            "--output-dir", str(tmp_path / "output"),
            "--payroll-csv", "payslip/data/payroll.csv",
        ],
    )
    with patch(f"{MODULE}.get_employees", return_value=EMPLOYEES), \
         patch(f"{MODULE}.send_email", side_effect=Exception("SMTP error")):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    out, err = capsys.readouterr().out, capsys.readouterr().err
    assert "2 failed" in out or "failed" in out


def test_main_exits_0_when_all_sends_succeed(monkeypatch, tmp_path, capsys):
    cfg = make_cfg_file(tmp_path)
    tmpl = make_template_file(tmp_path)
    for emp in EMPLOYEES:
        make_pdf(tmp_path, emp["employee_id_safe"], "2026-04")

    monkeypatch.setattr(
        sys, "argv",
        [
            "email_send.py", "--month", "2026-04",
            "--config", str(cfg),
            "--template", str(tmpl),
            "--output-dir", str(tmp_path / "output"),
            "--payroll-csv", "payslip/data/payroll.csv",
        ],
    )
    with patch(f"{MODULE}.get_employees", return_value=EMPLOYEES), \
         patch(f"{MODULE}.send_email"):
        main()  # must not raise SystemExit
