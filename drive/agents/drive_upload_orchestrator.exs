agent_root = Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))

model    = System.get_env("DRIVE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "drive-upload-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Drive Upload Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        4,
  tools:            ["run_command"],
  system_prompt:    """
  You are a Drive upload orchestrator. Execute this single step.
  Stop and report the error if the step exits non-zero.

  Step 1 — Upload payslip files to Drive:
    command: "python3"
    args: ["drive/scripts/drive_upload.py"]
  Confirm: exits 0 and prints "uploaded".

  Report the number of files uploaded and any failures.
  """,
  user_prompt: "Upload payslip PDFs to Google Drive."
}
