# uc-drive — Google Drive Integration

**Status:** In progress (T1, T2, T3)
**Repo:** `aetheris-agents`
**Goal:** Bookend the payslip workflow with Drive I/O — download the
monthly payroll CSV from Drive before generation, upload the resulting
PDFs and CSVs back to Drive after.

---

## Why uc-drive

The payslip pipeline produces auditable, reproducible output, but the Finance
team still copies files manually into and out of Google Drive each month.
Two standalone Python scripts close that gap without changing anything in the
payslip logic.

The design is intentionally minimal. Drive is a transport layer, not an agent
concern. Neither script contains business logic — they do one thing (get file
/ put files) and exit. The payslip orchestrator runs unchanged between them.
This also establishes the composition pattern for the full monthly pipeline:

```
drive_download.py → payslip_orchestrator.exs → drive_upload.py → (uc-email)
```

Each step is independently runnable, testable, and replaceable.

---

## What this enables

```bash
# Full monthly run via sprint
./scripts/sprint.sh drive

# Or step by step
python3 drive/scripts/drive_download.py
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
python3 drive/scripts/drive_upload.py
```

Drive folder layout after upload:

```
{DRIVE_OUTPUT_FOLDER_ID}/
    BTL_001/
        2026-04-Payslip.pdf
        2026-04-Payslip.csv
    BTL_002/
        2026-04-Payslip.pdf
        2026-04-Payslip.csv
```

---

## Open questions resolved

**Drive folder structure** — flat per employee (`Drive/output/{employee_id}/file`),
not nested by month. Matches local output structure; simpler to navigate in the
Drive UI; month is already encoded in the filename.

**Duplicate handling** — overwrite. Re-runs must be idempotent. If a correction
is issued and payslips are regenerated, the Drive copy must reflect the correction.
Skipping on existing files would silently leave stale data. Implementation:
`drive_upload.py` searches for an existing file by name in the employee folder and
calls `files.update` if found, `files.create` otherwise.

**HTML files** — not uploaded. They are local build artefacts used only as input
to the PDF/CSV generation step. Upload filter: `glob("*-Payslip.pdf")` +
`glob("*-Payslip.csv")`.

**Payroll CSV filename** — search by name, not fixed path. Finance may name the
file differently each month (e.g. `payroll-Apr-2026.csv`). `drive_download.py`
queries for the most recently modified file in the folder whose name contains
`"payroll"` (case-insensitive). If the folder contains exactly one matching file
this is unambiguous; if multiple exist the newest is used and the filename is
logged.

---

## Exit criterion

| Criterion | Check |
|-----------|-------|
| `drive_download.py` downloads payroll CSV to `payslip/data/payroll.csv` | standalone run |
| `drive_upload.py` uploads `*-Payslip.pdf` and `*-Payslip.csv`, skips HTML | standalone run |
| Uploading twice is idempotent — second run overwrites, no duplicates | manual verify |
| All Drive API calls mocked in tests — no credentials needed | `python3 -m pytest drive/tests/` |
| `drive_orchestrator.exs` evaluates without error | `mix run --eval 'Code.eval_file(...)'` |
| `./scripts/sprint.sh drive` passes | sprint run |

---

## Delivery sequence

| # | Ticket | Repo | What |
|---|--------|------|------|
| 1 | T1 | aetheris-agents | `drive_download.py` + `test_drive_download.py` |
| 2 | T2 | aetheris-agents | `drive_upload.py` + `test_drive_upload.py` |
| 3 | T3 | aetheris-agents + aetheris | `drive_orchestrator.exs`, `requirements.txt`, `.gitignore`, sprint case, `README.md`, `runbook.md` |

No aetheris repo changes required beyond the sprint case in `scripts/sprint.sh`.

---

## Tickets

---

### T1 — drive_download.py

**What to build:**

`drive/scripts/drive_download.py` — authenticates using the service account
key at `GOOGLE_SERVICE_ACCOUNT`, queries the folder at `DRIVE_PAYROLL_FOLDER_ID`
for the most recently modified file whose name contains `"payroll"` (case-insensitive),
and downloads it to `payslip/data/payroll.csv` (or `--dest` override). Parent
directories are created as needed. Exits non-zero with a clear message if the
env var is absent, no matching file is found, or the download fails.

**Scope:**
- `build_service()` — constructs authenticated Drive v3 service from
  `GOOGLE_SERVICE_ACCOUNT`; exits 1 if var not set
- `find_payroll_file(service, folder_id)` — list query with
  `name contains 'payroll'`, `orderBy modifiedTime desc`; returns file metadata
  or `None`
- `download_file(service, file_id, dest_path)` — `MediaIoBaseDownload` into
  `BytesIO`, then `write_bytes` to dest (avoids partial writes)
- `main()` — arg parse (`--dest`), env checks, call above, print summary

**Tests (`test_drive_download.py`):**
- `find_payroll_file` returns most recent match
- `find_payroll_file` returns `None` on empty folder
- query string includes folder ID and `"payroll"`
- query orders by `modifiedTime desc`
- `download_file` writes correct bytes to dest
- `download_file` creates parent directories
- `download_file` calls `get_media` with correct file ID
- `main` exits 1 when `DRIVE_PAYROLL_FOLDER_ID` missing
- `main` exits 1 when no file found (stderr message)
- `main` exits 0 on success and prints destination path

All Drive API calls mocked via `unittest.mock`. No credentials or network needed.

---

### T2 — drive_upload.py

**What to build:**

`drive/scripts/drive_upload.py` — authenticates using the same service account,
walks `payslip/output/` (or `--source` override), and for each employee directory
uploads all `*-Payslip.pdf` and `*-Payslip.csv` files to
`{DRIVE_OUTPUT_FOLDER_ID}/{employee_id}/`. Per-employee subfolders are created
if absent. Existing files with the same name are updated in place (not duplicated).
HTML files are skipped. Partial failures are reported to stderr; the script
continues to remaining employees and exits 1 if any upload failed.

**Scope:**
- `build_service()` — same pattern as T1, scope `drive.file`
- `collect_upload_files(source_dir)` — walk `source_dir`, for each employee subdir
  return `[(employee_id, path), ...]` for all `*-Payslip.pdf` and `*-Payslip.csv`;
  skip HTML; sort by `(employee_id, path.name)` for deterministic order
- `find_or_create_folder(service, parent_id, name)` — list query for existing
  subfolder; create if absent; return folder ID
- `upload_file(service, folder_id, file_path)` — list for existing file by name;
  `files.update` if found, `files.create` otherwise; return Drive file ID
- `main()` — arg parse, env checks, collect files, call above per employee,
  print summary, exit 1 on any failure

**Tests (`test_drive_upload.py`):**
- `collect_upload_files` finds PDFs and CSVs
- `collect_upload_files` skips HTML files
- `collect_upload_files` skips dirs with no matching files
- `collect_upload_files` skips non-directory entries
- `collect_upload_files` returns sorted order
- `collect_upload_files` returns empty list for empty dir
- `find_or_create_folder` returns existing folder ID without creating
- `find_or_create_folder` creates folder when not found
- `find_or_create_folder` query scopes to correct parent
- `upload_file` creates new file when none exists
- `upload_file` updates existing file (no duplicate)
- `upload_file` uses correct MIME type for PDF
- `upload_file` uses correct MIME type for CSV
- `main` exits 1 when `DRIVE_OUTPUT_FOLDER_ID` missing
- `main` exits 1 when source dir not found
- `main` exits 1 when no uploadable files found
- `main` exits 0 on full success, prints summary
- `main` exits 1 on partial failure, reports failed employees

All Drive API calls mocked.

---

### T3 — Orchestrator, sprint, docs

**`drive/agents/drive_orchestrator.exs`:**

Minimal agent — three `run_command` calls in sequence, no spawning needed.
Uses `__ENV__.file` for `sandbox_path`. `overlay_base_dir: nil` (scripts write
to real filesystem; output must persist).

```
system_prompt:
  You are a Drive workflow orchestrator.

  Step 1: Call run_command to run drive_download.py.
          Confirm it exits 0 and reports the downloaded path.

  Step 2: Call run_command to run the payslip orchestrator.
          Confirm it exits 0.

  Step 3: Call run_command to run drive_upload.py.
          Confirm it exits 0 and reports the number of files uploaded.

  Report: files downloaded, payslip run status, files uploaded.
  If any step exits non-zero, stop and report the failure.
```

Tools: `["run_command"]`. `max_steps: 8`.

**`scripts/sprint.sh drive` case (aetheris repo):**

Prerequisite checks: `GOOGLE_SERVICE_ACCOUNT`, `DRIVE_PAYROLL_FOLDER_ID`,
`DRIVE_OUTPUT_FOLDER_ID`, `ANTHROPIC_API_KEY`, `python3`.

Steps:
1. `python3 drive/scripts/drive_download.py` — verify exit 0
2. `run_agent` payslip orchestrator — verify exit 0
3. `python3 drive/scripts/drive_upload.py` — verify exit 0
4. Check `payslip/output/` contains at least one `*-Payslip.pdf`

**`drive/requirements.txt`:**
```
google-api-python-client>=2.120.0
google-auth>=2.29.0
```

**`drive/data/.gitignore`:** `service_account.json`

**`drive/.gitignore`:** `data/service_account.json`, `output/*`, `!output/.gitkeep`

**`drive/README.md`:** use case description, prerequisites, env vars, folder layout,
standalone usage, test instructions.

**`drive/runbook.md`:** monthly run procedure, download-only, upload-only, re-running
one employee, finding folder IDs, service account setup, common failures.

**`drive/docs/t3-implementation-notes.md`**

---

## Repository structure

```
aetheris-agents/
  drive/
    .gitignore
    __init__.py
    requirements.txt
    README.md
    runbook.md
    milestone.md
    agents/
      drive_orchestrator.exs
    data/
      .gitignore                  ← excludes service_account.json
    output/
      .gitkeep
    scripts/
      __init__.py
      drive_download.py
      drive_upload.py
    tests/
      __init__.py
      conftest.py
      test_drive_download.py      ← 10 tests
      test_drive_upload.py        ← 18 tests
    docs/
      t1-implementation-notes.md
      t2-implementation-notes.md
      t3-implementation-notes.md
```

aetheris repo: `scripts/sprint.sh` drive case only.

---

## Notes for uc-email

uc-email is the next bookend. Its input is the per-employee merged PDF already
in `payslip/output/{employee_id}/` and the employee email address from the
payroll CSV (surfaced by `payslip_compute.py`).

Shape: one `email_send.py` script, one sub-agent per employee via `spawn_agent`
+ `wait_for_all`. Open question before starting: SMTP or transactional API
(SendGrid, SES)? That determines the only external dependency.