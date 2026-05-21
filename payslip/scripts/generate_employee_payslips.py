#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys


def run_compute(employee_id_safe):
    result = subprocess.run(
        ["python3", "scripts/payslip_compute.py", "data/payroll.csv",
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML payslips and merged PDF for one employee."
    )
    parser.add_argument("employee_id_safe", help="Employee ID (safe form, e.g. BTL_999)")
    parser.add_argument("--output-dir", dest="output_dir", default="output",
                        help="Base output directory (default: output)")
    args = parser.parse_args()

    data = run_compute(args.employee_id_safe)
    employees = data.get("employees", [])
    if not employees:
        print(f"No data returned for {args.employee_id_safe}.", file=sys.stderr)
        sys.exit(1)
    employee = employees[0]

    template = read_template()

    emp_dir = os.path.join(args.output_dir, args.employee_id_safe)
    os.makedirs(emp_dir, exist_ok=True)

    written = []
    for month_data in employee["months"]:
        html = generate_html(template, employee, month_data)
        out_path = os.path.join(emp_dir, f"{month_data['month_file']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(out_path)

    result = subprocess.run(
        ["python3", "scripts/merge_payslips.py", emp_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print(f"Generated {len(written)} payslip(s) for {args.employee_id_safe}.")
    print(f"PDF: {os.path.join(args.output_dir, args.employee_id_safe, 'merged.pdf')}")


if __name__ == "__main__":
    main()
