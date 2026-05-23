# uc-email — Payslip Email Delivery

Sends per-employee payslip emails with PDF attachments to a finance alias.
Final step in the monthly payroll pipeline:

```
drive_download.py
  ↓
payslip_orchestrator.exs
  ↓
drive_upload.py
  ↓
email_download_template.py   ← sync template from Drive (when it changes)
  ↓
email_send.py --month 2026-04
```

## Prerequisites

- Python 3.10+
- Drive SDK already installed (`pip install -r drive/requirements.txt`)
- `email/data/smtp.cfg` — copy from `email/data/smtp.cfg.example` and fill in credentials
- `GOOGLE_SERVICE_ACCOUNT` — path to service account JSON key (for template download)
- `DRIVE_OUTPUT_FOLDER_ID` — Shared Drive folder containing `payslip_email_template.html`

No additional Python dependencies — `smtplib`, `email.mime`, and `configparser`
are all stdlib.

## SMTP setup

`smtp.cfg` has two address fields:

| Field | Purpose |
|---|---|
| `username` | Google account that owns the app password |
| `from_address` | Alias shown to recipients (configure in Gmail → Settings → "Send mail as") |

These are often different: `username` is the underlying account; `from_address`
is a `payroll@` alias. Obtain an app password at
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
(requires 2FA on the account).

## Standalone usage

All commands run from `aetheris-agents/`.

```bash
# Sync email template from Drive (only needed when Finance updates it)
python3 email/scripts/email_download_template.py

# Send payslip emails for a month
python3 email/scripts/email_send.py --month 2026-04

# Optional flags
python3 email/scripts/email_send.py \
  --month 2026-04 \
  --template email/data/payslip_email_template.html \
  --config email/data/smtp.cfg \
  --output-dir payslip/output/ \
  --payroll-csv payslip/data/payroll.csv
```

## Running via orchestrator

```bash
export PAYSLIP_MONTH=2026-04
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/email/agents/email_orchestrator.exs
```

## Running via sprint script

```bash
export PAYSLIP_MONTH=2026-04
cd ~/sandbox/elixirws/aetheris
./scripts/sprint.sh email
```

## Tests

```bash
python3 -m pytest email/tests/ -v
```
