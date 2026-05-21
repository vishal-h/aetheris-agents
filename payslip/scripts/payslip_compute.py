#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from datetime import datetime


def _float(val):
    if not val or not str(val).strip():
        return 0.0
    try:
        return float(str(val).strip())
    except ValueError:
        return 0.0


def detect_arrears_columns(fieldnames):
    return [col for col in fieldnames if col.strip().lower().startswith("arrears")]


def parse_month(month_str):
    return datetime.strptime(month_str.strip(), "%b %Y")


def month_file(month_str):
    dt = parse_month(month_str)
    return f"{dt.year}-{dt.month:02d}"


def sanitise_id(employee_id):
    return employee_id.replace("/", "_")


def compute_month(row, arrears_cols):
    sal = _float(row.get("sal", ""))
    bonus = _float(row.get("bonus", ""))
    pt = _float(row.get("pt", ""))
    tds = _float(row.get("tds", ""))
    tds_94j = _float(row.get("tds_94j", ""))
    loan_recovery = _float(row.get("loan_recovery", ""))
    emp_type = row.get("employee_type", "").strip()

    if sal <= 25000:
        earnings_type = "stipend"
        earnings = [{"label": "Stipend", "amount": sal}]
        tds_value = tds
    elif emp_type.lower() == "consultant":
        earnings_type = "consultant"
        earnings = [{"label": "Consultant Fee", "amount": sal}]
        tds_value = tds_94j
    else:
        earnings_type = "regular"
        basic = round(sal * 0.50, 2)
        hra = round(basic * 0.50, 2)
        lta = 3000.00
        wfh = 3000.00
        flexi_pay = round(sal - basic - hra - lta - wfh, 2)
        earnings = [
            {"label": "Basic", "amount": basic},
            {"label": "HRA", "amount": hra},
            {"label": "LTA", "amount": lta},
            {"label": "WFH Allowance", "amount": wfh},
            {"label": "Flexi Pay", "amount": flexi_pay},
        ]
        tds_value = tds

    if bonus:
        earnings.append({"label": "Bonus", "amount": bonus})

    for col in arrears_cols:
        val = _float(row.get(col, ""))
        if val:
            earnings.append({"label": "Arrears", "amount": val})

    deductions = []
    if pt:
        deductions.append({"label": "PT", "amount": pt})
    if tds_value:
        deductions.append({"label": "TDS", "amount": tds_value})
    if loan_recovery:
        deductions.append({"label": "Loan Recovery", "amount": loan_recovery})

    total_earnings = round(sum(e["amount"] for e in earnings), 2)
    total_deductions = round(sum(d["amount"] for d in deductions), 2)
    net_pay = round(total_earnings - total_deductions, 2)

    return {
        "month": row["month"].strip(),
        "paid_in": row["paid_in"].strip(),
        "month_file": month_file(row["month"]),
        "earnings_type": earnings_type,
        "earnings": earnings,
        "deductions": deductions,
        "total_earnings": total_earnings,
        "total_deductions": total_deductions,
        "net_pay": net_pay,
        "previous_balance": 0.00,
    }


def group_by_employee(rows, arrears_cols):
    employees = {}
    for row in rows:
        raw_id = row["employee_id"].strip()
        safe_id = sanitise_id(raw_id)
        if safe_id not in employees:
            employees[safe_id] = {
                "employee_id_safe": safe_id,
                "employee_id_raw": raw_id,
                "employee_type": row["employee_type"].strip(),
                "name": row["name"].strip(),
                "designation": row["designation"].strip(),
                "email": row["email"].strip(),
                "pan": row["pan"].strip(),
                "doj": row["doj"].strip(),
                "work_mode": row["work_mode"].strip(),
                "account_number": row["account_number"].strip(),
                "months": [],
            }
        employees[safe_id]["months"].append(compute_month(row, arrears_cols))

    for emp in employees.values():
        emp["months"].sort(key=lambda m: parse_month(m["month"]), reverse=True)

    return employees


def build_output(rows, arrears_cols, filter_id=None):
    employees = group_by_employee(rows, arrears_cols)

    if filter_id is not None:
        safe_filter = sanitise_id(filter_id)
        if safe_filter not in employees:
            print(f"Employee '{filter_id}' not found.", file=sys.stderr)
            sys.exit(1)
        result = [employees[safe_filter]]
    else:
        result = list(employees.values())

    return {"employees": result}


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
    return rows, fieldnames


def main():
    parser = argparse.ArgumentParser(description="Compute payslip JSON from a payroll CSV.")
    parser.add_argument("csv_path", help="Path to payroll CSV file.")
    parser.add_argument("--employee-id", dest="employee_id", help="Filter to a single employee ID.")
    args = parser.parse_args()

    rows, fieldnames = load_rows(args.csv_path)
    arrears_cols = detect_arrears_columns(fieldnames)
    output = build_output(rows, arrears_cols, filter_id=args.employee_id)
    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
