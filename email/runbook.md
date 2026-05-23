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
   export DRIVE_OUTPUT_FOLDER_ID=<shared-drive-folder-id>
   ```

4. Upload `email/data/payslip_email_template.html` to the Shared Drive folder
   identified by `DRIVE_OUTPUT_FOLDER_ID` (once, or whenever Finance updates it).

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

### `payslip_email_template.html not found in Drive folder`

```
payslip_email_template.html not found in Drive folder.
```

The template has not been uploaded to the Shared Drive folder. Upload
`email/data/payslip_email_template.html` manually to the folder identified
by `DRIVE_OUTPUT_FOLDER_ID`, then re-run `email_download_template.py`.
