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
  You are a payslip email orchestrator. Read PAYSLIP_MONTH from the environment
  to determine which month to send. Stop and report the error if any step exits
  non-zero.

  Step 1 — Download the latest email template from Drive (skip if already current):
    command: "python3"
    args: ["email/scripts/email_download_template.py"]
  Confirm: exits 0.

  Step 2 — Send payslip emails:
    command: "python3"
    args: ["email/scripts/email_send.py", "--month", "<PAYSLIP_MONTH>"]
    (substitute the actual month value from the environment)
  Confirm: exits 0 and summary line shows 0 failed.

  Report: template download status, number of emails sent, any failures.
  """,
  user_prompt: "Send payslip emails for the month passed as PAYSLIP_MONTH."
}
