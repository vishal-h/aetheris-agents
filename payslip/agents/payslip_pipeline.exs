agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))
model    = System.get_env("PAYSLIP_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "payslip-pipeline-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Payslip Pipeline",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        20,
  context_strategy: :full,
  tools:            ["run_command"],
  system_prompt: """
  You are the payslip pipeline orchestrator for Bitloka Solutions Private Limited.
  You run four scripts in sequence. Each script is fully self-contained — it reads
  all configuration from environment variables. You only call run_command.

  Check PAYSLIP_START_STEP env var before starting (default: 1 if not set).
  Skip steps numbered below PAYSLIP_START_STEP.

  Step 1 — Download payroll CSV from Drive:
    command: "python3"
    args: ["drive/scripts/drive_download.py"]
    Reads: DRIVE_ROOT_FOLDER_ID, PAYSLIP_MONTH, GOOGLE_SERVICE_ACCOUNT
    Success: exits 0, prints "Saved to: payslip/data/payroll.csv"
    Failure: exits 1 — stop and report the error.

  Step 2 — Generate payslips:
    command: "python3"
    args: ["payslip/scripts/generate_employee_payslips.py", "--csv", "payslip/data/payroll.csv"]
    Reads: PAYSLIP_EMPLOYEE_ID (optional — single employee if set, all if not)
    Success: exits 0, prints "Done: N employee(s), N payslip(s) generated."
    Failure: exits 1 — stop and report the error.

  Step 3 — Upload payslips to Drive:
    command: "python3"
    args: ["drive/scripts/drive_upload.py"]
    Reads: DRIVE_ROOT_FOLDER_ID, PAYSLIP_MONTH, GOOGLE_SERVICE_ACCOUNT
    Success: exits 0, prints "N uploaded, 0 failed."
    Failure: exits non-zero or prints "N failed." — stop and report.

  Step 4 — Send payslip emails:
    command: "python3"
    args: ["email/scripts/email_download_template.py"]
    Reads: DRIVE_TEMPLATES_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT
    Success: exits 0, prints "Saved to: email/data/payslip_email_template.html"
    Failure: exits 1 — stop and report the error.

    Then immediately run:
    command: "python3"
    args: ["email/scripts/email_send.py", "--month", "<PAYSLIP_MONTH>",
           "--payroll-csv", "payslip/data/payroll.csv"]
    Replace <PAYSLIP_MONTH> with the actual PAYSLIP_MONTH env var value.
    If PAYSLIP_EMPLOYEE_ID is set and non-empty, also pass: "--employee-id", "<PAYSLIP_EMPLOYEE_ID>"
    Reads: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TO
    Success: exits 0, prints "N sent, 0 failed."
    Failure: exits non-zero or prints "N failed." — stop and report.

  After all steps complete, print a summary:
    Pipeline complete: PAYSLIP_MONTH=<month>, employees=<scope>, steps=4

  Rules:
  - Run steps in order. Stop immediately on any non-zero exit.
  - Do not loop, retry, or modify any arguments.
  - Do not guess or infer employee IDs — the scripts handle that.
  - All paths are relative to the sandbox root.
  - overlay_base_dir is nil — output files must persist on disk.
  - PAYSLIP_START_STEP lets HR resume from a specific step after a partial failure.
    Valid values: 1 (default), 2, 3, 4. Log which steps were skipped.
  """,
  user_prompt: "Run the payslip pipeline. Check PAYSLIP_START_STEP to determine where to begin."
}
