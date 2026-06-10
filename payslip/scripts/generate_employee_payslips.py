#!/usr/bin/env python3
import argparse
import csv
import datetime
import json
import os
import re
import subprocess
import sys


def run_compute(employee_id_safe, csv_path):
    result = subprocess.run(
        ["python3", "scripts/payslip_compute.py",
         csv_path,
         "--config", "data/payroll_config.json",
         "--employee-id", employee_id_safe],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return json.loads(result.stdout)


def read_template():
    with open("data/payslip_template.html", encoding="utf-8") as f:
        return f.read()


def build_tbody(earnings, deductions):
    n = max(len(earnings), len(deductions))
    rows = []
    for i in range(n):
        e = earnings[i] if i < len(earnings) else None
        d = deductions[i] if i < len(deductions) else None
        e_label = e["label"] if e else ""
        e_amount = f'{e["amount"]:.2f}' if e else ""
        d_label = d["label"] if d else ""
        d_amount = f'{d["amount"]:.2f}' if d else ""
        rows.append(
            f"            <tr>\n"
            f"                <td>{e_label}</td>\n"
            f'                <td class="right-align">{e_amount}</td>\n'
            f"                <td>{d_label}</td>\n"
            f'                <td class="right-align">{d_amount}</td>\n'
            f"            </tr>"
        )
    return "\n".join(rows)


def build_tfoot(month_data):
    te = f'{month_data["total_earnings"]:.2f}'
    td = f'{month_data["total_deductions"]:.2f}'
    pb = f'{month_data["previous_balance"]:.2f}'
    np_ = f'{month_data["net_pay"]:.2f}'
    return (
        "        <tfoot>\n"
        '            <tr class="highlight">\n'
        "                <td>Total Earnings</td>\n"
        f'                <td class="right-align">{te}</td>\n'
        "                <td>Total Deductions</td>\n"
        f'                <td class="right-align">{td}</td>\n'
        "            </tr>\n"
        '            <tr class="highlight">\n'
        "                <td>Previous Balance</td>\n"
        f'                <td class="right-align">{pb}</td>\n'
        "                <td>Net Pay</td>\n"
        f'                <td class="right-align">{np_}</td>\n'
        "            </tr>\n"
        "        </tfoot>"
    )


def generate_html(template, employee, month_data):
    html = template

    tbody_html = build_tbody(month_data["earnings"], month_data["deductions"])
    tfoot_html = build_tfoot(month_data)

    html = re.sub(r"<tbody>.*?</tbody>",
                  f"<tbody>\n{tbody_html}\n        </tbody>",
                  html, flags=re.DOTALL)
    html = re.sub(r"<tfoot>.*?</tfoot>", tfoot_html, html, flags=re.DOTALL)

    html = html.replace("Payslip - March 2024", f"Payslip - {month_data['month']}")
    html = html.replace("EMP_001", employee["employee_id_raw"])
    html = html.replace("John Doe", employee["name"])
    html = html.replace("January 1, 2020", employee["doj"])
    html = html.replace("Software Engineer", employee["designation"])
    html = html.replace("Work mode: Hybrid", f"Work mode: {employee['work_mode']}")
    html = html.replace("BANK_CODE / ACCOUNT_NUMBER", employee["account_number"])

    return html


def write_csv(csv_path, employee, month_data):
    earnings = month_data["earnings"]
    deductions = month_data["deductions"]
    n = max(len(earnings), len(deductions))

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["Field", "Value"])
        writer.writerow(["Employee ID", employee["employee_id_raw"]])
        writer.writerow(["Name", employee["name"]])
        writer.writerow(["Designation", employee["designation"]])
        writer.writerow(["DOJ", employee["doj"]])
        writer.writerow(["Work Mode", employee["work_mode"]])
        writer.writerow(["Account Number", employee["account_number"]])
        writer.writerow(["Month", month_data["month"]])
        writer.writerow(["Paid In", month_data["paid_in"]])

        writer.writerow([])

        writer.writerow(["Earnings", "Amount", "Deductions", "Amount"])
        for i in range(n):
            e = earnings[i] if i < len(earnings) else None
            d = deductions[i] if i < len(deductions) else None
            writer.writerow([
                e["label"] if e else "",
                f'{e["amount"]:.2f}' if e else "",
                d["label"] if d else "",
                f'{d["amount"]:.2f}' if d else "",
            ])
        writer.writerow([
            "Total Earnings", f'{month_data["total_earnings"]:.2f}',
            "Total Deductions", f'{month_data["total_deductions"]:.2f}',
        ])
        writer.writerow([
            "Previous Balance", f'{month_data["previous_balance"]:.2f}',
            "Net Pay", f'{month_data["net_pay"]:.2f}',
        ])


def convert_to_pdf(html_path, pdf_path):
    result = subprocess.run(
        ["wkhtmltopdf", html_path, pdf_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML payslips and per-month PDFs for one employee."
    )
    parser.add_argument("employee_id_safe", help="Employee ID (safe form, e.g. BTL_999)")
    parser.add_argument("--output-dir", dest="output_dir", default="output",
                        help="Base output directory (default: output)")
    parser.add_argument("--csv", dest="csv_path", default="data/sample_payroll.csv",
                        help="Path to payroll CSV (default: data/sample_payroll.csv)")
    args = parser.parse_args()

    data = run_compute(args.employee_id_safe, args.csv_path)
    employees = data.get("employees", [])
    if not employees:
        print(f"No data returned for {args.employee_id_safe}.", file=sys.stderr)
        sys.exit(1)
    employee = employees[0]

    template = read_template()

    emp_dir = os.path.join(args.output_dir, args.employee_id_safe)
    os.makedirs(emp_dir, exist_ok=True)

    months_written = []
    month_files = []
    for month_data in employee["months"]:
        stem = f"{month_data['month_file']}-Payslip"
        html_path = os.path.join(emp_dir, f"{stem}.html")
        pdf_path = os.path.join(emp_dir, f"{stem}.pdf")
        csv_path = os.path.join(emp_dir, f"{stem}.csv")

        html = generate_html(template, employee, month_data)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        convert_to_pdf(html_path, pdf_path)
        write_csv(csv_path, employee, month_data)

        months_written.append(stem)
        month_files.append(month_data["month_file"])

    if months_written:
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        month_range = f"{month_files[-1]}:{month_files[0]}" if len(month_files) > 1 else month_files[0]
        log_line = (
            f"{timestamp}"
            f"\tmonths={month_range}"
            f"\temployee={args.employee_id_safe}"
            f"\tfiles={len(months_written) * 3}"
            f"\toutput={emp_dir}"
        )
        log_path = os.path.join(args.output_dir, "runs.log")
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(log_line + "\n")

    print(f"Generated {len(months_written)} payslip(s) for {args.employee_id_safe}.")
    print(f"Files in {os.path.join(args.output_dir, args.employee_id_safe)}{os.sep}:")
    for stem in months_written:
        print(f"  {stem}.html")
        print(f"  {stem}.pdf")
        print(f"  {stem}.csv")


if __name__ == "__main__":
    main()
