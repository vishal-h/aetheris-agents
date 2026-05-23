# Drive Workflow Runbook

## Monthly payslip run

**Prerequisites:** `payslip/output/` must contain generated payslips. If running
for the first time or after clearing output, run the payslip orchestrator first —
see [payslip/runbook.md](https://github.com/vishal-h/aetheris-agents/blob/main/payslip/runbook.md)

1. Ensure environment variables are set:
   ```bash
   export GOOGLE_SERVICE_ACCOUNT=/path/to/service_account.json
   export DRIVE_PAYROLL_FOLDER_ID=<folder-id>
   export DRIVE_OUTPUT_FOLDER_ID=<folder-id>
   ```
   
> [!NOTE]
> DRIVE_PAYROLL_FOLDER_ID and DRIVE_OUTPUT_FOLDER_ID can point to the same folder

2. Run the orchestrator:
   ```bash
   cd ~/sandbox/elixirws/aetheris
   mix aetheris run ../aetheris-agents/drive/agents/drive_orchestrator.exs
   ```

3. Verify output: check `payslip/output/<employee_id>/` for PDF and CSV files,
   and confirm the upload summary shows 0 failures.

---

## Service account setup

1. In Google Cloud Console, create a service account with no roles.
2. Generate and download a JSON key. Save to `drive/data/service_account.json`
   (excluded from git by `.gitignore`).
3. Share the payroll folder and output folder with the service account email,
   granting **Viewer** on the payroll folder and **Editor** on the output folder.

---

## Common failures

### `GOOGLE_SERVICE_ACCOUNT` not set

```
GOOGLE_SERVICE_ACCOUNT environment variable is not set.
```

Set the variable to the absolute path of the service account JSON key.

### `DRIVE_PAYROLL_FOLDER_ID` not set

```
DRIVE_PAYROLL_FOLDER_ID environment variable is not set.
```

Obtain the folder ID from the Drive URL: `https://drive.google.com/drive/folders/<ID>`.

### No payroll file found

```
No payroll file found in Drive folder.
```

Confirm a file whose name contains `payroll` exists in the configured folder and
the service account has Viewer access to that folder.

### `DRIVE_OUTPUT_FOLDER_ID` not set

```
DRIVE_OUTPUT_FOLDER_ID environment variable is not set.
```

Set to the Drive folder where payslip files should be uploaded.

### Upload failures

```
Failed <employee_id>: <error>
N uploaded, M failed.
```

Individual employee failures are reported but do not abort other uploads. The script
exits 1 at the end if any employee failed. Re-run to retry; uploads are idempotent
(existing files are updated in place, not duplicated).

### `wkhtmltopdf` not found

Install via system package manager:
```bash
# Debian/Ubuntu
sudo apt-get install wkhtmltopdf

# macOS
brew install wkhtmltopdf
```

---

## Locating Drive folder IDs

Open the folder in Drive and copy the last path segment from the URL:
`https://drive.google.com/drive/folders/<FOLDER_ID>`


---

## Validate download standalone

Confirm credentials and folder access before running the full orchestrator:

```bash
cd ~/sandbox/elixirws/aetheris-agents
python3 drive/scripts/drive_download.py --dest /tmp/payroll_check.csv
```

Expected output:
```
Found: payroll_2026-04.csv (modified 2026-04-30T...)
Downloaded to: /tmp/payroll_check.csv
```

Inspect the file before proceeding:
```bash
head -5 /tmp/payroll_check.csv
```

If this succeeds, the service account has Viewer access to `DRIVE_PAYROLL_FOLDER_ID`
and the download path resolves correctly.

---

## Validate upload standalone

Confirm Editor access on `DRIVE_OUTPUT_FOLDER_ID` against existing payslip output:

```bash
cd ~/sandbox/elixirws/aetheris-agents
python3 drive/scripts/drive_upload.py --source payslip/output/
```

Expected output:
```
Uploaded BTL_001/2026-04-Payslip.pdf → <file_id>
Uploaded BTL_001/2026-04-Payslip.csv → <file_id>
...
N uploaded, 0 failed.
```

Requires `payslip/output/` to contain at least one employee directory with
`*-Payslip.pdf` or `*-Payslip.csv` files. Run the payslip orchestrator first
if output is empty. Uploads are idempotent — re-running overwrites existing
Drive files rather than duplicating them.

Verify in Drive:
`https://drive.google.com/drive/folders/{DRIVE_OUTPUT_FOLDER_ID}`
