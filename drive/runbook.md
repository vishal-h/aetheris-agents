# Drive Workflow Runbook

## Overview

uc-drive automates the monthly payslip file exchange with Google Drive.

**One-time setup**

1. Create a service account in Google Cloud Console, download the JSON key to
   `drive/data/service_account.json` (gitignored).
2. Set the required environment variables:
   ```bash
   export GOOGLE_SERVICE_ACCOUNT=/path/to/drive/data/service_account.json
   export DRIVE_ROOT_FOLDER_ID=<folder-id>   # the payslips root; one YYYY-MM/ folder per month under it
   ```
   Both scripts resolve the month's period folder (`YYYY-MM/`) under this root.
   Upload creates the period folder and the per-employee subfolders (`BTL_999/` etc.)
   when absent; download requires the period folder to exist already.
3. Share the root folder with the service account email as **Editor** — upload
   creates folders and files under it.
   To find the service account email:
   ```bash
   python3 -c "
   import json, os
   key = json.load(open(os.environ['GOOGLE_SERVICE_ACCOUNT']))
   print(key['client_email'])
   "
   ```
4. The root folder must be in a **Shared Drive** (formerly Team Drive) — service
   accounts do not have storage quota and cannot create files in regular My Drive
   folders. Create a Shared Drive in Google Drive, add the service account email
   as a Contributor, and use the root folder's ID as `DRIVE_ROOT_FOLDER_ID`.

---

**Monthly run**

1. Finance creates the month's period folder under the root (e.g. `2026-04/`) and
   drops `payroll.csv` into it.
2. Download it locally:
   ```bash
   export PAYSLIP_MONTH=2026-04
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
{DRIVE_ROOT_FOLDER_ID}/
  2026-04/
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
   export DRIVE_ROOT_FOLDER_ID=<folder-id>
   export PAYSLIP_MONTH=2026-04
   ```

2. Run the orchestrator:
   ```bash
   cd ~/sandbox/elixirws/aetheris
   mix aetheris run ../aetheris-agents/drive/agents/drive_orchestrator.exs
   ```

3. Verify output: check `payslip/output/<employee_id>/` for PDF and CSV files,
   and confirm the upload summary shows 0 failures.

---

## Common failures

### `GOOGLE_SERVICE_ACCOUNT` not set

```
GOOGLE_SERVICE_ACCOUNT_FILE (or GOOGLE_SERVICE_ACCOUNT) is not set.
```

Set either variable to the absolute path of the service account JSON key.

### `DRIVE_ROOT_FOLDER_ID` not set

```
DRIVE_ROOT_FOLDER_ID environment variable is not set.
```

Both `drive_download.py` and `drive_upload.py` read it. Obtain the folder ID from
the Drive URL: `https://drive.google.com/drive/folders/<ID>`.

### Period folder not found

```
Period folder '2026-04' not found under folder <root-id>. Create the folder in Drive before running this script.
```

`drive_download.py` does not create the period folder. Create `YYYY-MM/` under the
root for `PAYSLIP_MONTH` and put the payroll file in it.

### No payroll file found

```
No payroll file found in Drive folder.
```

Confirm a file whose name contains `payroll` exists in the month's period folder
and the service account has access to it.

### Upload failures

```
Failed <employee_id>: <error>
N uploaded, M failed.
```

Individual employee failures are reported but do not abort other uploads. The script
exits 1 at the end if any employee failed. Re-run to retry; uploads are idempotent
(existing files are updated in place, not duplicated).

### `HttpError 403: storageQuotaExceeded`

```
HttpError 403: storageQuotaExceeded
```

Service accounts do not have storage quota. The root folder is in a regular
My Drive — service accounts cannot create files there. Move the root folder to a
Shared Drive, add the service account as a Contributor, and update
`DRIVE_ROOT_FOLDER_ID` to the Shared Drive folder ID.

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
PAYSLIP_MONTH=2026-04 python3 drive/scripts/drive_download.py --dest /tmp/payroll_check.csv
```

Expected output:
```
Downloaded: payroll.csv (modified 2026-04-30T...)
Saved to: /tmp/payroll_check.csv
```

Inspect the file before proceeding:
```bash
head -5 /tmp/payroll_check.csv
```

If this succeeds, the service account can read the `2026-04/` period folder under
`DRIVE_ROOT_FOLDER_ID` and the download path resolves correctly.

---

## Validate upload standalone

Confirm Editor access on `DRIVE_ROOT_FOLDER_ID` against existing payslip output:

```bash
cd ~/sandbox/elixirws/aetheris-agents
python3 drive/scripts/drive_upload.py --source payslip/output/ --month 2026-04
```

`--month` selects which month to upload, as `YYYY-MM`. It falls back to the
`PAYSLIP_MONTH` env var when omitted, and the script exits 1 when neither is
set. The month is a filter as well as a destination: only
`{month}-Payslip.pdf` and `{month}-Payslip.csv` are collected, so the other
months in each employee's `payslip/output/` archive stay where they are.

Expected output:
```
N uploaded, 0 failed.
```

That summary is the script's only stdout line; there is no per-file line. A
per-employee failure goes to stderr as `Failed <employee_id>: <error>`.

Requires `payslip/output/` to contain at least one employee directory with
`{month}-Payslip.pdf` or `{month}-Payslip.csv` files. Run the payslip
orchestrator first if output is empty for that month. Uploads are idempotent —
re-running overwrites existing Drive files rather than duplicating them.

Verify in Drive: open
`https://drive.google.com/drive/folders/{DRIVE_ROOT_FOLDER_ID}`, then the `2026-04/` folder.
