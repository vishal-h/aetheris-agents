#!/usr/bin/env python3
import argparse
import glob
import os
import subprocess
import sys


def find_pdfs(employee_dir):
    return sorted(glob.glob(os.path.join(employee_dir, "*-Payslip.pdf")))


def apply_filters(pdf_files, year=None, from_month=None, to_month=None):
    result = pdf_files
    if year:
        result = [f for f in result if os.path.basename(f).startswith(f"{year}-")]
    if from_month:
        result = [f for f in result if os.path.basename(f) >= f"{from_month}-Payslip.pdf"]
    if to_month:
        result = [f for f in result if os.path.basename(f) <= f"{to_month}-Payslip.pdf"]
    return result


def output_filename(employee_id_safe, year=None, from_month=None, to_month=None):
    if year:
        return f"{employee_id_safe}-{year}-Payslips.pdf"
    elif from_month or to_month:
        from_str = from_month or "start"
        to_str = to_month or "end"
        return f"{employee_id_safe}-{from_str}-to-{to_str}-Payslips.pdf"
    else:
        return f"{employee_id_safe}-Annual-Payslips.pdf"


def merge_pdfs(pdf_files, output_path):
    result = subprocess.run(
        ["gs", "-dBATCH", "-dNOPAUSE", "-q",
         "-sDEVICE=pdfwrite",
         f"-sOutputFile={output_path}"] + pdf_files,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Merge per-month payslip PDFs for one employee into a single file."
    )
    parser.add_argument("employee_id_safe", help="Employee ID (safe form, e.g. BTL_999)")
    parser.add_argument("--year", help="Filter to a single calendar year (e.g. 2025)")
    parser.add_argument("--from", dest="from_month",
                        help="Keep PDFs from this month onwards (e.g. 2025-04)")
    parser.add_argument("--to", dest="to_month",
                        help="Keep PDFs up to and including this month (e.g. 2026-03)")
    parser.add_argument("--output-dir", dest="output_dir", default="output",
                        help="Base output directory (default: output)")
    args = parser.parse_args()

    employee_dir = os.path.join(args.output_dir, args.employee_id_safe)
    pdf_files = find_pdfs(employee_dir)
    pdf_files = apply_filters(pdf_files, args.year, args.from_month, args.to_month)

    if not pdf_files:
        print(f"No PDFs found matching filter in {employee_dir}.")
        sys.exit(0)

    out_name = output_filename(args.employee_id_safe, args.year, args.from_month, args.to_month)
    output_path = os.path.join(employee_dir, out_name)

    merge_pdfs(pdf_files, output_path)
    print(f"Merged {len(pdf_files)} payslip(s) → {output_path}")


if __name__ == "__main__":
    main()
