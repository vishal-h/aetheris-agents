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


def get_earnings_cols(fieldnames):
    """All e_* columns except e_sal (includes arrears)."""
    return [f for f in fieldnames if f.startswith('e_') and f != 'e_sal']


def get_deductions_cols(fieldnames):
    return [f for f in fieldnames if f.startswith('d_')]


def get_arrears_cols(fieldnames):
    return [f for f in fieldnames if f.startswith('e_') and 'arrears' in f.lower()]


def col_label(col, label_map):
    if col in label_map:
        return label_map[col]
    name = col[2:] if col.startswith(('e_', 'd_')) else col
    return name.replace('_', ' ').title()


def load_config(config_path):
    try:
        with open(config_path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)


def parse_month(month_str):
    return datetime.strptime(month_str.strip(), "%b %Y")


def month_file(month_str):
    dt = parse_month(month_str)
    return f"{dt.year}-{dt.month:02d}"


def sanitise_id(employee_id):
    return employee_id.replace("/", "_")


def compute_month(row, config, extra_cols, deductions_cols, arrears_cols):
    """
    extra_cols     — non-sal, non-arrears e_* columns (e.g. e_bonus)
    deductions_cols — d_* columns
    arrears_cols   — e_arrears* columns
    """
    label_map       = config.get('labels', {})
    sal             = _float(row.get('e_sal', ''))
    emp_type        = row.get('employee_type', '').strip()
    threshold       = config.get('stipend_threshold', 25000)
    consultant_val  = config.get('consultant_type_value', 'consultant')
    bd              = config['regular_breakdown']

    if sal <= threshold:
        earnings_type = 'stipend'
        earnings = [{'label': 'Stipend', 'amount': sal}]
    elif emp_type.lower() == consultant_val.lower():
        earnings_type = 'consultant'
        earnings = [{'label': 'Consultant Fee', 'amount': sal}]
    else:
        earnings_type = 'regular'
        basic     = round(sal * bd['basic_pct'], 2)
        hra       = round(basic * bd['hra_pct'], 2)
        lta       = bd['lta_fixed']
        wfh       = bd['wfh_fixed']
        flexi_pay = round(sal - basic - hra - lta - wfh, 2) if bd['flexi_residual'] else 0.0
        earnings = [
            {'label': 'Basic',         'amount': basic},
            {'label': 'HRA',           'amount': hra},
            {'label': 'LTA',           'amount': lta},
            {'label': 'WFH Allowance', 'amount': wfh},
            {'label': 'Flexi Pay',     'amount': flexi_pay},
        ]

    for col in extra_cols:
        val = _float(row.get(col, ''))
        if val:
            earnings.append({'label': col_label(col, label_map), 'amount': val})

    for col in arrears_cols:
        val = _float(row.get(col, ''))
        if val:
            earnings.append({'label': 'Arrears', 'amount': val})

    deductions = []
    for col in deductions_cols:
        val = _float(row.get(col, ''))
        if val:
            deductions.append({'label': col_label(col, label_map), 'amount': val})

    total_earnings    = round(sum(e['amount'] for e in earnings), 2)
    total_deductions  = round(sum(d['amount'] for d in deductions), 2)
    net_pay           = round(total_earnings - total_deductions, 2)

    return {
        'month':            row['month'].strip(),
        'paid_in':          row['paid_in'].strip(),
        'month_file':       month_file(row['month']),
        'earnings_type':    earnings_type,
        'earnings':         earnings,
        'deductions':       deductions,
        'total_earnings':   total_earnings,
        'total_deductions': total_deductions,
        'net_pay':          net_pay,
        'previous_balance': 0.00,
    }


def group_by_employee(rows, config, extra_cols, deductions_cols, arrears_cols):
    employees = {}
    for row in rows:
        raw_id  = row['employee_id'].strip()
        safe_id = sanitise_id(raw_id)
        if safe_id not in employees:
            employees[safe_id] = {
                'employee_id_safe': safe_id,
                'employee_id_raw':  raw_id,
                'employee_type':    row['employee_type'].strip(),
                'name':             row['name'].strip(),
                'designation':      row['designation'].strip(),
                'email':            row['email'].strip(),
                'pan':              row['pan'].strip(),
                'doj':              row['doj'].strip(),
                'work_mode':        row['work_mode'].strip(),
                'account_number':   row['account_number'].strip(),
                'months':           [],
            }
        employees[safe_id]['months'].append(
            compute_month(row, config, extra_cols, deductions_cols, arrears_cols)
        )

    for emp in employees.values():
        emp['months'].sort(key=lambda m: parse_month(m['month']), reverse=True)

    return employees


def build_output(rows, config, extra_cols, deductions_cols, arrears_cols, filter_id=None):
    employees = group_by_employee(rows, config, extra_cols, deductions_cols, arrears_cols)

    if filter_id is not None:
        safe_filter = sanitise_id(filter_id)
        if safe_filter not in employees:
            print(f"Employee '{filter_id}' not found.", file=sys.stderr)
            sys.exit(1)
        result = [employees[safe_filter]]
    else:
        result = list(employees.values())

    return {'employees': result}


def load_rows(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
    return rows, fieldnames


def main():
    parser = argparse.ArgumentParser(description="Compute payslip JSON from a payroll CSV.")
    parser.add_argument("csv_path", help="Path to payroll CSV file.")
    parser.add_argument("--employee-id", dest="employee_id",
                        help="Filter to a single employee ID.")
    parser.add_argument("--config", dest="config_path",
                        default="data/payroll_config.json",
                        help="Path to payroll config JSON (default: data/payroll_config.json).")
    args = parser.parse_args()

    config = load_config(args.config_path)
    rows, fieldnames = load_rows(args.csv_path)

    if not any(f.startswith(('e_', 'd_')) for f in fieldnames):
        print("No e_/d_ columns found. Did you rename the CSV headers?", file=sys.stderr)
        sys.exit(1)

    all_e_cols      = get_earnings_cols(fieldnames)
    arrears_cols    = get_arrears_cols(fieldnames)
    extra_cols      = [c for c in all_e_cols if c not in set(arrears_cols)]
    deductions_cols = get_deductions_cols(fieldnames)

    output = build_output(rows, config, extra_cols, deductions_cols, arrears_cols,
                          filter_id=args.employee_id)
    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
