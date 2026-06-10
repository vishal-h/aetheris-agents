agent_root = Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))

model    = System.get_env("DRIVE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "drive-download-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Drive Download Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        4,
  tools:            ["run_command"],
  system_prompt:    """
  You are a Drive download orchestrator. Run the command below exactly once.
  Do not run any other commands. Do not verify or retry.
  If the command exits non-zero, report the error and stop.

  command: "python3"
  args: ["drive/scripts/drive_download.py"]
  timeout_ms: 120000

  The script downloads the payroll CSV and prints "Saved to: <path>".
  When it exits 0, report the filename and destination path and stop immediately.
  """,
  user_prompt: "Download the payroll CSV from Google Drive."
}
