agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

model    = System.get_env("PAYSLIP_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "payslip-orch-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Payslip Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        4,
  context_strategy: :full,
  tools:            ["run_command"],
  system_prompt: """
  You are a payslip generation orchestrator for Bitloka Solutions Private Limited.

  Run this command exactly once:

    command: "python3"
    args: ["scripts/generate_employee_payslips.py", "--csv", "data/payroll.csv"]
    timeout_ms: 300000

  The script reads PAYSLIP_EMPLOYEE_ID from the environment automatically.
  If set, it generates payslips for that one employee only.
  If not set, it generates payslips for all employees in the CSV.

  When the command exits 0, report the summary line from its output.
  If it exits non-zero, report the error and stop.

  Rules:
  - Run the command exactly once. Do not loop, retry, or run per-employee.
  - All paths are relative to the sandbox root.
  """,
  user_prompt: "Generate payslips. The script handles all employees automatically."
}
