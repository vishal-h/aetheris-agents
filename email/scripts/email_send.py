#!/usr/bin/env python3
"""Send per-employee payslip emails with PDF attachments via SMTP."""
import argparse
import configparser
import json
import os
import re
import smtplib
import subprocess
import sys
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Ensure aetheris-agents/ is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def load_config(config_path):
    """Read SMTP credentials from config_path, falling back to env vars.

    Priority: smtp.cfg file (if it exists) → environment variables.
    This allows Rig-launched agents to inject credentials via env vars
    without requiring smtp.cfg to be present on disk.

    Exits 1 if neither the file nor the required env vars are available.
    """
    path = Path(config_path)
    if path.exists():
        cfg = configparser.ConfigParser()
        cfg.read(path)
        if "smtp" not in cfg:
            print(f"[smtp] section missing from {config_path}", file=sys.stderr)
            sys.exit(1)
        return cfg["smtp"]

    # Fall back to environment variables
    host      = os.getenv("SMTP_HOST")
    port      = os.getenv("SMTP_PORT", "587")
    username  = os.getenv("SMTP_USER")
    password  = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM") or username
    to_addr   = os.getenv("SMTP_TO")   or username

    missing = [
        k for k, v in {
            "SMTP_HOST": host,
            "SMTP_USER": username,
            "SMTP_PASSWORD": password,
        }.items()
        if not v
    ]
    if missing:
        print(
            f"smtp.cfg not found at {config_path} and env vars not set: "
            f"{', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    return {
        "host":         host,
        "port":         port,
        "username":     username,
        "password":     password,
        "from_address": from_addr,
        "to_address":   to_addr,
    }


def get_employees(payroll_csv_path):
    """Run payslip_compute.py and return the list of employee dicts.

    Calls payslip/scripts/payslip_compute.py via subprocess with the given CSV
    path. Parses stdout as JSON. Each dict contains at minimum employee_id_safe,
    name, and email (matching payslip_compute.py output).

    Exits 1 if the subprocess returns a non-zero exit code or stdout is not
    valid JSON.
    """
    result = subprocess.run(
        ["python3", "payslip/scripts/payslip_compute.py", payroll_csv_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"payslip_compute.py failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"payslip_compute.py output is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    return data["employees"]


def render_template(template_path, variables):
    """Read the HTML template and substitute {{variable}} placeholders.

    Replaces {{employee_name}}, {{employee_id}}, {{employee_email}},
    {{month_display}}, and {{month}} with values from variables.

    Raises KeyError if a required variable is missing from variables.
    """
    html = Path(template_path).read_text(encoding="utf-8")
    for key in re.findall(r"\{\{(\w+)\}\}", html):
        if key not in variables:
            raise KeyError(key)
    for key, value in variables.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def find_pdf(output_dir, employee_id, month):
    """Return the Path to the employee's payslip PDF for the given month.

    Constructs {output_dir}/{employee_id}/{month}-Payslip.pdf.
    Returns the Path if the file exists.

    When called directly, exits 1 with a clear message if the file is not
    found. In main(), the return-None path is used instead — callers that
    need the exit-1 behaviour should call this function directly without
    catching SystemExit.

    Returns None only when called via the internal _find_pdf_or_none helper
    in main() to allow skipping missing employees without aborting the run.
    """
    path = Path(output_dir) / employee_id / f"{month}-Payslip.pdf"
    if path.exists():
        return path
    print(f"PDF not found: {path}", file=sys.stderr)
    sys.exit(1)


def _find_pdf_or_none(output_dir, employee_id, month):
    """Return the PDF path, or None if not found (suppresses the sys.exit(1))."""
    path = Path(output_dir) / employee_id / f"{month}-Payslip.pdf"
    return path if path.exists() else None


def send_email(config, subject, html_body, pdf_path):
    """Send a single email with an HTML body and a PDF attachment.

    Builds a MIMEMultipart message with From, To, Subject headers, an HTML
    body part, and the PDF file as an attachment. Connects via SMTP, calls
    starttls(), logs in, sends, then closes the connection.

    Raises on any SMTP error.
    """
    msg = MIMEMultipart("mixed")
    msg["From"] = config["from_address"]
    msg["To"] = config["to_address"]
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with open(pdf_path, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
    pdf_part.add_header(
        "Content-Disposition", "attachment", filename=Path(pdf_path).name
    )
    msg.attach(pdf_part)

    with smtplib.SMTP(config["host"], int(config["port"])) as smtp:
        smtp.starttls()
        smtp.login(config["username"], config["password"])
        smtp.sendmail(config["from_address"], config["to_address"], msg.as_string())


def main():
    """Parse arguments and send one payslip email per employee."""
    parser = argparse.ArgumentParser(
        description="Send payslip emails with PDF attachments."
    )
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format")
    parser.add_argument(
        "--template",
        default="email/data/payslip_email_template.html",
        help="Path to HTML email template",
    )
    parser.add_argument(
        "--config",
        default="email/data/smtp.cfg",
        help="Path to SMTP config file",
    )
    parser.add_argument(
        "--output-dir",
        default="payslip/output/",
        help="Root directory containing per-employee payslip output",
    )
    parser.add_argument(
        "--payroll-csv",
        default="payslip/data/payroll.csv",
        help="Path to payroll CSV file",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    employees = get_employees(args.payroll_csv)
    month_display = datetime.strptime(args.month, "%Y-%m").strftime("%B %Y")

    sent = 0
    failed = []

    for emp in employees:
        employee_id = emp["employee_id_safe"]
        employee_name = emp["name"]
        employee_email = emp["email"]

        pdf_path = _find_pdf_or_none(args.output_dir, employee_id, args.month)
        if pdf_path is None:
            print(
                f"Warning: PDF not found for {employee_id} ({args.month}), skipping.",
                file=sys.stderr,
            )
            continue

        variables = {
            "employee_name": employee_name,
            "employee_id": employee_id,
            "employee_email": employee_email,
            "month_display": month_display,
            "month": args.month,
        }
        html_body = render_template(args.template, variables)
        subject = f"Payslip — {employee_name} — {month_display}"

        try:
            send_email(config, subject, html_body, pdf_path)
            print(f"Sent: {employee_id} → {config['to_address']}")
            sent += 1
        except Exception as exc:
            print(f"Failed {employee_id}: {exc}", file=sys.stderr)
            failed.append(employee_id)

    print(f"{sent} sent, {len(failed)} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
