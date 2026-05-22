# T3c Implementation Notes — Per-Month PDF and CSV Output

## Why per-month files replace merged.pdf

The previous structure produced one `merged.pdf` per employee per run, merging all months into
a single file using Ghostscript. This created several practical problems:

- **Drive organisation.** A Drive folder organised by month requires one file per month. A
  merged file spanning multiple months does not map cleanly onto that structure.
- **Email attachments.** Attaching a single month's payslip to an email requires extracting
  it from the merged PDF. Per-month files are ready to attach directly.
- **Re-generation.** If one month's HTML needs to be corrected, re-running the script would
  overwrite all months' PDFs in the merged file. Per-month files are independently regeneratable.
- **Auditability.** Each file has an unambiguous name (`2026-04-Payslip.pdf`). The merged PDF
  has no month in its name, making archival and retrieval less reliable.

The naming convention `{YYYY-MM}-Payslip.{ext}` is sortable, unambiguous, and maps directly
onto the expected Drive folder organisation.

## Why CSV is included alongside each PDF

The CSV (`{YYYY-MM}-Payslip.csv`) is the source of truth for that month's numbers in a form
that does not require opening a PDF or re-running `payslip_compute.py`:

- **Self-contained record.** A finance reviewer can open the CSV in a spreadsheet and verify
  every number without tooling. The PDF is for the employee; the CSV is for the records.
- **Drive integration.** Google Sheets can import the CSV directly. uc-drive can upload it
  alongside the PDF as a machine-readable companion.
- **No duplication of computation.** The CSV is written from the same in-memory `month_data`
  dict that generates the HTML, so there is no risk of divergence.

The CSV format is two sections separated by a blank line: employee metadata (label/value pairs)
and then a four-column earnings/deductions table matching the payslip layout. The totals rows
at the bottom of the table mirror the payslip footer exactly.

## wkhtmltopdf call moved into generate_employee_payslips.py

Previously `merge_payslips.py` called `wkhtmltopdf` per HTML file and then merged with `gs`.
Now `generate_employee_payslips.py` calls `wkhtmltopdf` immediately after writing each HTML
file, producing a PDF in the same loop iteration. This means:

- **Faster feedback on failure.** If wkhtmltopdf fails for month N, the script stops before
  processing subsequent months rather than discovering the failure only at the merge step.
- **No merge step, no Ghostscript dependency.** `gs` is no longer required. `conftest.py`
  has been updated to remove the `gs` check from the integration skip condition.

## Why merge_payslips.py is deleted rather than kept unused

Keeping `merge_payslips.py` alongside `generate_employee_payslips.py` would create a
misleading impression that merging is still part of the workflow. The script's only callers
were `generate_employee_payslips.py` (removed) and `sprint.sh` (references to merged.pdf
should be updated separately). Deleting it and its test suite removes ambiguity and
eliminates the Ghostscript dependency from the project entirely.

The `test_merge_payslips.py` suite (6 mocked subprocess tests) is also deleted. Those tests
covered the now-deleted merge logic; the integration tests in
`test_generate_employee_payslips.py` cover the full end-to-end output including PDF production.

## Deviations from spec

None. The implementation matches the T3c spec exactly:
- Per-month `{YYYY-MM}-Payslip.html`, `{YYYY-MM}-Payslip.pdf`, `{YYYY-MM}-Payslip.csv` ✓
- `merge_payslips.py` and `test_merge_payslips.py` deleted ✓
- `conftest.py` updated to check only `wkhtmltopdf` (gs removed) ✓
- README updated: folder structure, prerequisites, scripts section, How to run example ✓
- 7 integration tests covering all employee types and all new file types ✓

## What uc-drive and uc-email should know

**Output structure per employee:**
```
output/{employee_id_safe}/
  {YYYY-MM}-Payslip.html    # keep as build artefact; not for upload
  {YYYY-MM}-Payslip.pdf     # upload to Drive; attach to email
  {YYYY-MM}-Payslip.csv     # upload to Drive as companion record
```

**File naming:** `{YYYY-MM}-Payslip.{ext}` — the month prefix sorts lexicographically,
so `glob("*.pdf")` on the employee directory returns files in month order without custom
sort logic.

**One run, one month's files.** The orchestrator runs all employees in parallel for whatever
months are in `data/payroll.csv`. A monthly run against a CSV containing only the current
month produces exactly one set of three files per employee. uc-drive can upload everything
in `output/` after the run completes.

**No merged.pdf.** There is no longer a combined file. uc-email should attach
`{YYYY-MM}-Payslip.pdf` for the relevant month directly.
