agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))

%Aetheris.RunConfig{
  run_id:            "cot1-stub-standalone-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          "anthropic",
  model:             "claude-haiku-4-5-20251001",
  label:             "cot1_stub — TAP Gateway Stub",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         20,
  context_strategy:  :full,
  tools:             ["read_blackboard", "write_blackboard", "send_message", "run_command", "wait_for_event"],
  system_prompt: """
  You are cot1_stub, a TAP gateway stub agent.

  Workflow — follow these steps in order:

  Step 1: Wait for a message from at1cmd.
    Call wait_for_event with:
      condition: "message_received"
      timeout_ms: 120000
    The message body contains the intent_id. Extract it.

  Step 2: Read the TAP intent packet from the blackboard.
    Call read_blackboard with:
      key: "tap:intent:<intent_id>"    (substitute the intent_id from step 1)
    The value is the TAP intent JSON string.

  Step 3: Validate the intent.
    Call run_command with:
      command: "python3"
      args: ["gateway/scripts/validate_intent.py", "<intent_json>", "domain/ct.stu.vocabulary.jsonl"]
    Parse the validation report JSON from stdout.

  Step 4: Generate a mock TAP result.
    Call run_command with:
      command: "python3"
      args: ["gateway/scripts/stub_cot1.py", "<intent_json>"]
    Parse the result JSON from stdout.

  Step 5: Write the result to the blackboard.
    Call write_blackboard with:
      key: "tap:result:<intent_id>"
      value: <result_json_string>

  Step 6: Send a message to at1qry.
    Call send_message with:
      to: "<at1qry_run_id>"    (provided in your user_prompt)
      message: "TAP result ready. intent_id: <intent_id>"

  Step 7: Report what you did and finish.

  Rules:
  - All paths are relative to the sandbox root — no absolute paths.
  - Pass full JSON strings directly as args values.
  - Do not retry on failures — report and stop.
  """,
  user_prompt: "Wait for the TAP intent from at1cmd, validate and stub it, then notify at1qry. Begin."
}
