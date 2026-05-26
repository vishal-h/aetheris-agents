agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))

orb_id       = "uc-api-t1-#{Aetheris.ID.generate()}"
at1cmd_id    = "#{orb_id}-at1cmd"
cot1_stub_id = "#{orb_id}-cot1-stub"
at1qry_id    = "#{orb_id}-at1qry"

%Aetheris.OrbConfig{
  orb_id:          orb_id,
  max_runtime_ms:  10 * 60 * 1_000,
  agent_configs: [
    %Aetheris.RunConfig{
      run_id:            at1cmd_id,
      mode:              :record,
      provider:          "anthropic",
      model:             "claude-haiku-4-5-20251001",
      label:             "at1cmd — TAP Tenant Dispatcher",
      sandbox_path:      agent_root,
      overlay_base_dir:  nil,
      max_steps:         20,
      context_strategy:  :rolling,
      max_context_steps: 6,
      tools:             ["write_blackboard", "send_message", "run_command"],
      system_prompt:     """
      You are at1cmd, the TAP tenant dispatcher agent.

      Workflow — follow these steps in order:

      Step 1: Parse the student enrollment CSV.
        Call run_command with:
          command: "python3"
          args: ["tenant/scripts/parse_csv.py", "tenant/data/sample_enrollments.csv"]
        Parse the JSON array of rows from stdout.

      Step 2: Package the TAP intent.
        Call run_command with:
          command: "python3"
          args: ["tenant/scripts/package_intent.py", "<rows_json>", "Enroll students from tenant/data/sample_enrollments.csv", "--source-file", "tenant/data/sample_enrollments.csv"]
        Parse the TAP intent JSON from stdout. Extract the intent_id field.

      Step 3: Write the intent to the blackboard.
        Call write_blackboard with:
          key: "tap:intent:<intent_id>"    (use the actual intent_id from step 2)
          value: <intent_json_string>      (the full intent JSON as a string)

      Step 4: Notify cot1_stub.
        Call send_message with:
          to: "#{cot1_stub_id}"
          message: "TAP intent ready. intent_id: <intent_id>"

      Step 5: Report what you dispatched and finish.
        Include: intent_id, correlation_id, record count, any flags raised.

      Rules:
      - All paths are relative to the sandbox root — no absolute paths.
      - Pass the rows_json as a single string argument (JSON-encoded array).
      - Exact command format: command field is "python3", args is a list starting with the script path.
      - overlay_base_dir is nil — output files must persist.
      - If run_command fails, report the error and stop.
      """,
      user_prompt: "Read the enrollment CSV, package a TAP intent, write it to the blackboard, and notify cot1_stub at run '#{cot1_stub_id}'. Begin."
    },
    %Aetheris.RunConfig{
      run_id:            cot1_stub_id,
      mode:              :record,
      provider:          "anthropic",
      model:             "claude-haiku-4-5-20251001",
      label:             "cot1_stub — TAP Gateway Stub",
      sandbox_path:      agent_root,
      overlay_base_dir:  nil,
      max_steps:         20,
      context_strategy:  :full,
      tools:             ["read_blackboard", "write_blackboard", "send_message", "run_command", "wait_for_event"],
      system_prompt:     """
      You are cot1_stub, a TAP gateway stub agent.

      Workflow — follow these steps in order:

      Step 1: Wait for a message from at1cmd.
        Call wait_for_event with:
          condition: "message_received"
          timeout_ms: 120000
        The message body contains the intent_id. Extract it.
        The intent_id is the string after "intent_id: " in the message.

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

      Step 6: Notify at1qry.
        Call send_message with:
          to: "#{at1qry_id}"
          message: "TAP result ready. intent_id: <intent_id>"

      Step 7: Report what you did — validation outcome, record count, job_ref — and finish.

      Rules:
      - All paths are relative to the sandbox root — no absolute paths.
      - Pass full JSON strings as args values; use the exact string from stdout without modification.
      - Do not retry on failures — report and stop.
      """,
      user_prompt: "Wait for the TAP intent from at1cmd, validate it, stub a result, write to blackboard, and notify at1qry at run '#{at1qry_id}'. Begin."
    },
    %Aetheris.RunConfig{
      run_id:            at1qry_id,
      mode:              :record,
      provider:          "anthropic",
      model:             "claude-haiku-4-5-20251001",
      label:             "at1qry — TAP Tenant Collector",
      sandbox_path:      agent_root,
      overlay_base_dir:  nil,
      max_steps:         15,
      context_strategy:  :full,
      tools:             ["read_blackboard", "run_command", "wait_for_event"],
      system_prompt:     """
      You are at1qry, the TAP tenant collector agent.

      Workflow — follow these steps in order:

      Step 1: Wait for a message from cot1_stub.
        Call wait_for_event with:
          condition: "message_received"
          timeout_ms: 120000
        The message body contains the intent_id. Extract it.
        The intent_id is the string after "intent_id: " in the message.

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
        Include:
        - Total records, queued, failed, skipped counts
        - Non-idempotent count and which records are affected
        - Each gap: record name, reason, suggested_action
        - Confirm the job_ref from the result

      Rules:
      - All paths are relative to the sandbox root — no absolute paths.
      - Do not retry — report what you received and finish.
      """,
      user_prompt: "Wait for the TAP result from cot1_stub, run gap analysis, and report all findings. Begin."
    }
  ]
}
