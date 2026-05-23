# uc-email — Technical Brief

## Context

uc-payslip generates per-employee payslip PDFs. uc-drive uploads them to a
Shared Drive folder. uc-email is the final bookend: it sends each employee's
PDF as an email attachment to a finance alias for forwarding.

Full monthly pipeline:

```
drive_download.py
  ↓
payslip_orchestrator.exs
  ↓
drive_upload.py
  ↓
email_download_template.py
  ↓
email_send.py --month 2026-04
```

---

## What uc-email adds

Two standalone Python scripts:

**`email_download_template.py`**
- Downloads `payslip_email_template.html` from the Shared Drive folder
  (same folder as `DRIVE_OUTPUT_FOLDER_ID`) to `email/data/`
- Run once when the template changes; not required every month

**`email_send.py`**
- Reads employee list and data from `payslip_compute.py`
- Renders the HTML template per employee
- Sends one email per employee to the finance alias via SMTP
- Attaches `{YYYY-MM}-Payslip.pdf` for the specified month
- Exits non-zero on any failure

---

## Email design

**To:** `SMTP_TO_ADDRESS` (e.g. `finance@bitloka.com`) — one email per employee,
not one batch. Finance forwards each individually.

**From:** `SMTP_FROM_ADDRESS` (e.g. `payroll@bitloka.com`) — alias configured
in "Send mail as" on the underlying account.

**Subject:** `Payslip — {employee_name} — {month_display}`
e.g. `Payslip — Alice Smith — April 2026`

**Body:** Personalised HTML from template. Template variables:
- `{{employee_name}}`
- `{{employee_id}}`
- `{{employee_email}}` — included so Finance can copy it when forwarding
- `{{month_display}}` — human-readable, e.g. `April 2026`
- `{{month}}` — ISO format, e.g. `2026-04`

**Attachment:** `payslip/output/{employee_id_safe}/{YYYY-MM}-Payslip.pdf`

---

## Authentication

SMTP with app password. Config file at `email/data/smtp.cfg` (gitignored).

```ini
[smtp]
host     = smtp.gmail.com
port     = 587
username = vishal@bitloka.com
password = xxxx xxxx xxxx xxxx
from_address = payroll@bitloka.com
to_address   = finance@bitloka.com
```

`username` is the underlying Google account that owns the app password.
`from_address` is the alias configured in that account's "Send mail as" settings.
These are intentionally separate fields.

---

## Employee data source

`email_send.py` calls `payslip_compute.py` via subprocess to get the full
employee list with names and emails:

```bash
python3 payslip/scripts/payslip_compute.py payslip/data/payroll.csv
```

Parses the JSON output. Does not read `payroll.csv` directly — reuses the
existing parsing and normalisation logic.

---

## Template download

`email_download_template.py` searches `DRIVE_OUTPUT_FOLDER_ID` for a file
named exactly `payslip_email_template.html`. Uses `build_service` imported
from `drive.scripts.drive_download` (same pattern as `drive_upload.py`).
Requires `supportsAllDrives=True` since the folder is a Shared Drive.

No new env var needed — `DRIVE_OUTPUT_FOLDER_ID` is the same Shared Drive
folder that already holds the uploaded payslips.

---

## Design principle

Scripts do, agents decide — same as uc-payslip and uc-drive.

`email_send.py` handles all SMTP logic. The orchestrator's only job is to
call the two scripts in order and report results. No sub-agents needed —
sending is fast and sequential is fine for typical employee counts.

---

## Repo structure

```
aetheris-agents/
  email/
    agents/
      email_orchestrator.exs
    data/
      smtp.cfg                      # gitignored — SMTP credentials
      payslip_email_template.html   # gitignored — downloaded from Drive
      .gitignore
    docs/
      t*-implementation-notes.md
    scripts/
      __init__.py
      email_download_template.py
      email_send.py
    tests/
      __init__.py
      conftest.py
      test_email_download_template.py
      test_email_send.py
    requirements.txt                # no new deps — stdlib smtplib + existing Drive SDK
    README.md
    runbook.md
    milestone.md
```

No new Python dependencies. `smtplib`, `email.mime`, and `configparser` are
all stdlib. Drive SDK already installed from uc-drive.

---

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | LLM orchestration |
| `GOOGLE_SERVICE_ACCOUNT` | Yes | Template download from Drive |
| `DRIVE_OUTPUT_FOLDER_ID` | Yes | Shared Drive folder containing template |

SMTP credentials come from `email/data/smtp.cfg`, not env vars.

---

## Open questions resolved

**Month format** — `--month 2026-04` maps directly to the PDF filename
`2026-04-Payslip.pdf`. Month display in the email body is derived:
`2026-04` → `April 2026` via `datetime.strptime`.

**Template variable delimiters** — `{{variable}}` (double braces) avoids
collision with Python's `str.format` and HTML content.

**Sequential vs parallel sending** — sequential. No `spawn_agent` needed.
SMTP rate limits and typical employee counts (tens, not thousands) make
parallel sending unnecessary complexity.

**Template freshness** — `email_download_template.py` is a separate step,
not called inside `email_send.py`. Finance updates the template in Drive;
operator runs the download step when the template changes. Template is
gitignored (not committed) so Drive is the source of truth.

---

## Milestone exit criterion

| Criterion | Check |
|-----------|-------|
| `email_download_template.py` downloads template from Shared Drive | standalone run |
| `email_send.py --month 2026-04` sends one email per employee to alias | standalone run |
| PDF attached, template rendered with correct variables | inspect received email |
| All Drive and SMTP calls mocked in tests | `python3 -m pytest email/tests/` |
| `email_orchestrator.exs` evaluates without error | `mix run --eval` |
| `./scripts/sprint.sh email` passes | sprint run |

---

## Delivery sequence

| # | Ticket | What |
|---|--------|------|
| 1 | T1 | `email_download_template.py` + `test_email_download_template.py` |
| 2 | T2 | `email_send.py` + `test_email_send.py` |
| 3 | T3 | `email_orchestrator.exs`, config, `.gitignore`, sprint case, `README.md`, `runbook.md` |
