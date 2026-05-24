agent_root = Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))
month = System.get_env("PAYSLIP_MONTH") || raise "PAYSLIP_MONTH not set"

system_prompt = """
You are a payslip email orchestrator. Stop and report if any step exits non-zero.

Step 1 — Download the latest email template from Drive:
  command: "python3"
  args: ["email/scripts/email_download_template.py"]
Confirm: exits 0.

Step 2 — Send payslip emails:
  command: "python3"
  args: ["email/scripts/email_send.py", "--month", "#{month}"]
Confirm: exits 0 and summary line shows 0 failed.

Report: template download status, number of emails sent, any failures.
"""

%Aetheris.RunConfig{
  run_id:           "email-orch-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         "anthropic",
  model:            "claude-haiku-4-5-20251001",
  label:            "Email Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        6,
  tools:            ["run_command"],
  system_prompt:    system_prompt,
  user_prompt: "Send payslip emails for #{month}."
}
