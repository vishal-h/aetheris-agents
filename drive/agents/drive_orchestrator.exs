agent_root = Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))

model    = System.get_env("DRIVE_MODEL") || Application.get_env(:aetheris, :default_model)
provider = Application.get_env(:aetheris, :default_provider)

%Aetheris.RunConfig{
  run_id:           "drive-orch-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Drive Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        8,
  tools:            ["run_command"],
  system_prompt:    """
  You are a Drive workflow orchestrator. Execute these three steps in order.
  Stop and report the error if any step exits non-zero.

  Step 1 — Download payroll CSV from Drive:
    command: "python3"
    args: ["drive/scripts/drive_download.py"]
  Confirm: exits 0 and prints "Saved to:".

  Step 2 — Generate payslips:
    command: "mix"
    args: ["aetheris", "run", "payslip/agents/payslip_orchestrator.exs"]
  Confirm: exits 0.

  Step 3 — Upload payslip files to Drive:
    command: "python3"
    args: ["drive/scripts/drive_upload.py"]
  Confirm: exits 0 and prints "uploaded".

  Report: files downloaded, payslip run status, upload summary.
  """,
  user_prompt: "Run the monthly Drive workflow."
}
