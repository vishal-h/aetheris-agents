# T3d Implementation Notes — On-Demand Annual Merge

## Why merge is a separate on-demand script, not part of the monthly orchestrator

The monthly orchestrator runs against one month's CSV and produces per-month files for all
employees. Merging months together is an audit operation that spans multiple monthly runs —
it cannot be done in the same pass because only one month's data exists at the time the
orchestrator runs.

Merging is also run far less often than generation. An auditor might request a full-year
merged PDF once a year; every employee gets a payslip every month. Keeping the merge as a
standalone script means:

- The monthly run has no Ghostscript dependency. `generate_employee_payslips.py` only needs
  `wkhtmltopdf`. gs is only pulled in when an auditor explicitly requests a merged file.
- The merge can be re-run at any time against whatever per-month PDFs are on disk, without
  re-running the orchestrator or re-fetching data.
- Filters (`--year`, `--from`, `--to`) make sense for an on-demand audit tool, not for a
  monthly generation script.

## Ascending sort for audit vs descending for monthly

`generate_employee_payslips.py` processes months in newest-first order (matching the JSON
output from `payslip_compute.py`) because the most recent payslip is the most relevant when
reviewing a batch. `merge_employee_payslips.py` sorts ascending (oldest month first) because
a merged PDF read for audit purposes should read chronologically — January before February,
April 2025 before March 2026.

## Why --from/--to uses string comparison

The per-month PDF filenames follow ISO 8601 format: `YYYY-MM-Payslip.pdf`. ISO 8601 dates
are lexicographically ordered — "2025-04" < "2026-01" alphabetically in the same order as
chronologically. The filter:

```python
os.path.basename(f) >= f"{from_month}-Payslip.pdf"
```

works correctly because the filename prefix `YYYY-MM` sorts before the `-Payslip.pdf` suffix
identically for all files. No datetime parsing is needed, and the comparison cannot produce
incorrect results as long as filenames follow the `YYYY-MM-Payslip.pdf` convention established
by `generate_employee_payslips.py`.

## gs stays as a dependency but only for on-demand audit use

After T3c removed `merge_payslips.py`, Ghostscript was no longer required for monthly runs.
T3d re-introduces `gs` as a dependency of `merge_employee_payslips.py`, but with a narrower
scope:

- Monthly generation: requires only `wkhtmltopdf`
- On-demand audit merge: additionally requires `gs`

The `conftest.py` integration test skip condition remains `wkhtmltopdf`-only — the merge
employee tests use mocked subprocess and do not require `gs` to be installed.

## Deviations from spec

None. The implementation matches the T3d spec exactly:
- `merge_employee_payslips.py` with ascending sort, `--year`, `--from`, `--to` filters ✓
- Output filename logic for all three cases ✓
- 11 unit tests (spec required 6 cases; the additional 5 cover from-only, to-only, and
  individual output_filename variants for completeness) ✓
- Runbook section added; stale T3b-era references to `merged.pdf` and old filenames
  corrected in the same commit ✓
