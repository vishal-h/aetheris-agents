# rig/p8-002: Drive folder convention refactor

## Context

Three drive scripts currently use two separate folder ID env vars
(`DRIVE_PAYROLL_FOLDER_ID`, `DRIVE_OUTPUT_FOLDER_ID`). This ticket
replaces both with a single `DRIVE_ROOT_FOLDER_ID` and derives the
period subfolder from `PAYSLIP_MONTH`. Future artifact types (form16
etc.) can follow the same convention under the same root.

---

## Folder convention

```
payroll/                              ← DRIVE_ROOT_FOLDER_ID
  payslips/
    {YYYYMM}-{monthname}/             ← derived from PAYSLIP_MONTH
      payroll.csv                     ← download source
      payslip_email_template.html     ← email template source
      {employee_id}/                  ← upload destination
        {YYYYMM}-Payslip.pdf
```

Period folder name derivation:
- `PAYSLIP_MONTH=2026-05` → `202605-may`
- `PAYSLIP_MONTH=2026-04` → `202604-april`
- Pattern: `strftime("%Y%m-") + strftime("%B").lower()`

---

## Acceptance criteria

- [ ] `drive/scripts/drive_utils.py` created with `period_folder_name`,
      `find_folder`, `resolve_period_folder`
- [ ] `drive_download.py` uses `DRIVE_ROOT_FOLDER_ID` + `PAYSLIP_MONTH`,
      calls `resolve_period_folder`, fails clearly if folder absent
- [ ] `drive_upload.py` uses `DRIVE_ROOT_FOLDER_ID` + `PAYSLIP_MONTH`,
      creates `payslips/{period}` if needed
- [ ] `email_download_template.py` uses `DRIVE_ROOT_FOLDER_ID` +
      `PAYSLIP_MONTH`, calls `resolve_period_folder`
- [ ] `DRIVE_PAYROLL_FOLDER_ID` and `DRIVE_OUTPUT_FOLDER_ID` removed
      from all scripts and from `agentConfigDefs.ts`
- [ ] `DRIVE_ROOT_FOLDER_ID` in `agentConfigDefs.ts` with correct
      placeholder
- [ ] `STEP_CONFIG_HINTS` updated in `OrchestratorView.tsx`
- [ ] `runbook.md` updated — single root folder var, convention note
- [ ] `test_drive_utils.py` — all 5 tests pass
- [ ] `python3 -m pytest drive/tests/ -v` exits 0
- [ ] `bun run build` exits 0
