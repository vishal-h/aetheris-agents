# Drive Workflow Runbook

## Overview

uc-drive automates the monthly payslip file exchange with Google Drive.

**One-time setup**

1. Create a service account in Google Cloud Console, download the JSON key to
   `drive/data/service_account.json` (gitignored).
2. Set the required environment variables:
   ```bash
   export GOOGLE_SERVICE_ACCOUNT=/path/to/drive/data/service_account.json
   export DRIVE_PAYROLL_FOLDER_ID=<folder-id>   # Drive folder containing payroll.csv
   export DRIVE_OUTPUT_FOLDER_ID=<folder-id>    # Drive folder for uploaded payslips
   ```
   Both folder IDs can be the same folder. Per-employee subfolders (`BTL_999/` etc.)
   are created automatically on first upload.
3. Share the Drive folder with the service account email — **Viewer** for download,
   **Editor** for upload. If both IDs point to the same folder, grant **Editor**.
   To find the service account email:
   ```bash
   python3 -c "
   import json, os
   key = json.load(open(os.environ['GOOGLE_SERVICE_ACCOUNT']))
   print(key['client_email'])
   "
   ```
4. The output folder must be a **Shared Drive** (formerly Team Drive) — service
   accounts do not have storage quota and cannot create files in regular My Drive
   folders. Create a Shared Drive in Google Drive, add the service account email
   as a Contributor, and use the Shared Drive folder ID as `DRIVE_OUTPUT_FOLDER_ID`.
   The payroll source folder (download only) can be a regular folder.

---

**Monthly run**

1. Finance drops `payroll.csv` into the configured Drive folder.
2. Download it locally:
   ```bash
   python3 drive/scripts/drive_download.py
   ```
3. Generate payslips:
   ```bash
   cd ~/sandbox/elixirws/aetheris
   mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
   ```
4. Upload PDFs and CSVs to Drive:
   ```bash
   python3 drive/scripts/drive_upload.py
   ```

Or run all three steps via the sprint script:
```bash
./scripts/sprint.sh drive
```

The Drive folder after a successful run:
```
{DRIVE_OUTPUT_FOLDER_ID}/
  payroll.csv          ← source, unchanged
  BTL_999/
    2026-04-Payslip.pdf
    2026-04-Payslip.csv
  BTL_998/
    2026-04-Payslip.pdf
    2026-04-Payslip.csv
```

---

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

## `HttpError 403: storageQuotaExceeded`

Service Accounts do not have storage quota.

The output folder is a regular My Drive folder. Service accounts cannot create
files there. Move the output folder to a Shared Drive, add the service account
as a Contributor, and update `DRIVE_OUTPUT_FOLDER_ID` to the Shared Drive
folder ID.


