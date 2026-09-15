# Email Workflow Runbook

## Overview

uc-email is the final step of the monthly payroll pipeline. It sends one
personalised email per employee to the configured finance alias, with the
month's payslip PDF attached.

Full pipeline position:
```
drive_download.py → payslip_orchestrator.exs → drive_upload.py
  → email_download_template.py → email_send.py --month YYYY-MM
```

---

## One-time setup

1. Copy the example config and fill in real values:
   ```bash
   cp email/data/smtp.cfg.example email/data/smtp.cfg
   ```

2. Edit `email/data/smtp.cfg`:
   - `host` / `port`: `smtp.gmail.com` / `587`
   - `username`: the Google account that owns the app password (e.g. `vishal@bitloka.com`)
   - `password`: a 16-character app password — obtain at
     [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
     (requires 2FA enabled on the account)
   - `from_address`: the alias recipients will see (e.g. `payroll@bitloka.com`);
     must be configured in Gmail → Settings → "Send mail as"
   - `to_address`: the finance alias all emails are sent to

3. Set environment variables:
   ```bash
   export GOOGLE_SERVICE_ACCOUNT=/path/to/drive/data/service_account.json
   export DRIVE_TEMPLATES_FOLDER_ID=<templates-folder-id>
   ```

4. Upload `email/data/payslip_email_template.html` to the Shared Drive folder
   identified by `DRIVE_TEMPLATES_FOLDER_ID` (once, or whenever Finance updates it).

---

## Monthly run

**Prerequisites:**

```bash
# smtp.cfg must exist
ls email/data/smtp.cfg

# Payslip output must exist for the target month
ls payslip/output/

# Set the month
export PAYSLIP_MONTH=2026-04
```

**Steps:**

```bash
# Step 1 — sync template (only needed when Finance updates it in Drive)
python3 email/scripts/email_download_template.py

# Step 2 — send emails
python3 email/scripts/email_send.py --month 2026-04
```

Or run both steps via the orchestrator:

```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/email/agents/email_orchestrator.exs
```

Or via the sprint script:

```bash
./scripts/sprint.sh email
```

---

## Validate standalone

**Template download:**

```bash
python3 email/scripts/email_download_template.py
```

Expected output:
```
Downloaded: payslip_email_template.html
Saved to: email/data/payslip_email_template.html
```

**Email send (no dry-run flag):**

There is no `--dry-run` flag. To validate the SMTP connection and rendering
without sending to Finance, temporarily set `to_address` in `smtp.cfg` to a
personal address, run `email_send.py` against a single test employee, then
restore `to_address`.

---

## Environment variables and worker restart

The Aetheris worker (`aetheris_worker`) and exec server (`aetheris_exec_server`)
are spawned once when `mix aetheris run` starts and inherit the shell environment
at that point. Updating env vars in the shell after the worker is running has no
effect — the worker does not see the new values.

**Always set all required env vars before running `mix aetheris run`:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_SERVICE_ACCOUNT=/path/to/drive/data/service_account.json
export DRIVE_TEMPLATES_FOLDER_ID=<templates-folder-id>
export PAYSLIP_MONTH=2026-04

cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/email/agents/email_orchestrator.exs
```

---

### If env vars were set incorrectly or changed mid-session

Kill any stale worker processes and start fresh:

```bash
pkill -f aetheris_worker 2>/dev/null || true
pkill -f aetheris_exec_server 2>/dev/null || true
```

Confirm they are gone:

```bash
ps aux | grep aetheris_worker
ps aux | grep aetheris_exec_server
```

Then re-export all env vars in the same shell and re-run.

---

### Monthly folder ID update

None is needed. The folder IDs are set once: the drive steps read
`DRIVE_ROOT_FOLDER_ID` and resolve the month's `YYYY-MM/` folder under it from
`PAYSLIP_MONTH`; the template download reads `DRIVE_TEMPLATES_FOLDER_ID`.

Workflow for a new month:

1. Create the period folder under the root, e.g. `2026-05/`, and upload
   `payroll.csv` for that month into it.

2. Set the month:
   ```bash
   export PAYSLIP_MONTH=2026-05
   ```

3. Run the pipeline — per-employee subfolders (`BTL_999/` etc.) and uploaded
   PDFs will appear inside the period folder automatically.

The `payslip_email_template.html` only needs to be re-uploaded when Finance
updates it — it does not move with the monthly folder.

---

### Diagnosing env var issues mid-run

If a run fails with a folder-not-found or file-not-found error, read the
script's own message in the trajectory:

```bash
mix aetheris trajectory <run_id> --step 0
```

Look at the `tool_result` event's `stderr` field. The scripts do not print the
folder ID they received, so compare the variables in the shell that started the
run; a value changed after the worker started is not seen by it — kill and
restart. If the values are current and the error is "not found", the variable
holds the wrong folder ID. Verify with:

```bash
env | grep DRIVE
```

---

## Common failures

### `Config file not found: email/data/smtp.cfg`

```
Config file not found: email/data/smtp.cfg
```

Copy the example and fill in credentials:
```bash
cp email/data/smtp.cfg.example email/data/smtp.cfg
```

### `[smtp] section missing`

```
[smtp] section missing from email/data/smtp.cfg
```

The config file exists but is missing the `[smtp]` header. Check the file
against `smtp.cfg.example`.

### `payslip_compute.py failed`

```
payslip_compute.py failed:
...
```

The payroll CSV is missing or malformed. Confirm `payslip/data/payroll.csv`
exists and is the correct format for the target month.

### `PDF not found for {employee_id}`

```
Warning: PDF not found for BTL_999 (2026-04), skipping.
```

The payslip PDF was not generated for that employee and month. Run the payslip
orchestrator first:
```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
```

### `SMTP AUTH extension not supported`

```
SMTP AUTH extension not supported by server.
```

Wrong host or port. Confirm `host = smtp.gmail.com` and `port = 587` in
`smtp.cfg`.

### `Username and Password not accepted`

```
(535, b'5.7.8 Username and Password not accepted...')
```

App password is incorrect, or 2FA is not enabled on the account. Generate a
new app password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

### `payslip_email_template.html not found in templates folder`

```
payslip_email_template.html not found in templates folder.
```

The template has not been uploaded to the templates folder. Upload
`email/data/payslip_email_template.html` manually to the folder identified
by `DRIVE_TEMPLATES_FOLDER_ID`, then re-run `email_download_template.py`.
