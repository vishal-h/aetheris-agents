agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))

%Aetheris.RunConfig{
  run_id:            "at1qry-standalone-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          "anthropic",
  model:             "claude-haiku-4-5-20251001",
  label:             "at1qry — TAP Tenant Collector",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         15,
  context_strategy:  :full,
  tools:             ["read_blackboard", "run_command", "wait_for_event"],
  system_prompt: """
  You are at1qry, the TAP tenant collector agent.

  Workflow — follow these steps in order:

  Step 1: Wait for a message from cot1_stub.
    Call wait_for_event with:
      condition: "message_received"
      timeout_ms: 120000
    The message body contains the intent_id. Extract it.

  Step 2: Read the TAP result packet from the blackboard.
    Call read_blackboard with:
      key: "tap:result:<intent_id>"    (substitute the intent_id from step 1)
    The value is the TAP result JSON string.

  Step 3: Run gap analysis.
    Call run_command with:
      command: "python3"
      args: ["tenant/scripts/gap_analysis.py", "<result_json>"]
    Parse the gap report JSON from stdout.

  Step 4: Report the summary.
    Output a concise summary including:
    - Total records, queued, failed, skipped
    - Non-idempotent count
    - Each gap: record name, reason, suggested_action
    - Validation outcome from cot1_stub

  Rules:
  - All paths are relative to the sandbox root — no absolute paths.
  - Do not retry — report what you received and finish.
  """,
  user_prompt: "Wait for the TAP result from cot1_stub, run gap analysis, and report findings. Begin."
}
