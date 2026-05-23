# uc-drive — Google Drive Payroll Workflow

Automates the monthly payslip cycle: download payroll data from Drive, generate
per-employee payslip PDFs and CSVs, then upload the results back to Drive.

## Workflow

```
Drive (payroll CSV)
      │
      ▼
drive/scripts/drive_download.py   ← downloads payroll.csv to payslip/data/
      │
      ▼
payslip/agents/payslip_orchestrator.exs  ← generates per-employee PDF+CSV
      │
      ▼
drive/scripts/drive_upload.py     ← uploads payslip/output/ to Drive
```

The three steps are orchestrated by `drive/agents/drive_orchestrator.exs`, which
runs them sequentially via the `run_command` tool and halts on any non-zero exit.

## Prerequisites

- Python 3.10+
- `google-api-python-client` and `google-auth` (`pip install -r drive/requirements.txt`)
- `wkhtmltopdf` in PATH (for payslip PDF generation)
- A Google service account with Drive API access (see `drive/runbook.md`)

## Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT` | Absolute path to the service account JSON key file |
| `DRIVE_PAYROLL_FOLDER_ID` | Drive folder ID containing the monthly payroll CSV |
| `DRIVE_OUTPUT_FOLDER_ID` | Drive folder ID where payslip files will be uploaded |

## Running

### Full orchestrated run (via Aetheris)

```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/drive/agents/drive_orchestrator.exs
```

### Individual steps

```bash
# Download payroll CSV
python3 drive/scripts/drive_download.py

# Generate payslips (from aetheris-agents root)
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs

# Upload payslip files
python3 drive/scripts/drive_upload.py
```

## Tests

```bash
python3 -m pytest drive/tests/ -v
```
