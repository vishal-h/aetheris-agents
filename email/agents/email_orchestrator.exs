agent_root = Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))

model    = System.get_env("EMAIL_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "email-orch-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Email Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        6,
  tools:            ["run_command"],
  system_prompt:    """
  You are a payslip email orchestrator. Run each command below exactly once in order.
  Do not run any other commands. Do not verify or retry.
  If any command exits non-zero, report the error and stop.

  Step 1:
    Run: python3 email/scripts/email_download_template.py
    timeout_ms: 120000
    The script downloads the email template from the payroll/templates/ folder
    in Drive and prints "Saved to: <path>". When it exits 0, proceed.

  Step 2:
    Run: python3 email/scripts/email_send.py
    timeout_ms: 300000
    The script reads PAYSLIP_MONTH and PAYSLIP_EMPLOYEE_ID from the environment automatically.
    It sends the relevant emails and prints "N sent, N failed.".
    When it exits 0, stop and report the sent/failed summary.
  """,
  user_prompt: "Send payslip emails for the month passed as PAYSLIP_MONTH."
}
