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
  You are a Drive upload orchestrator. Run the command below exactly once.
  Do not run any other commands. Do not verify or retry.
  If the command exits non-zero, report the error and stop.

  command: "python3"
  args: ["drive/scripts/drive_upload.py"]
  timeout_ms: 300000

  The script uploads all files and prints a summary line ending in "uploaded, N failed."
  When it exits 0, report the summary and stop immediately.
  """,
  user_prompt: "Upload payslip PDFs to Google Drive."
}
