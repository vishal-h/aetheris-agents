agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))

orb_id    = "uc-api-t2-#{Aetheris.ID.generate()}"
at1cmd_id = "#{orb_id}-at1cmd"
cot1_id   = "#{orb_id}-cot1"
at1qry_id = "#{orb_id}-at1qry"

%Aetheris.OrbConfig{
  orb_id:         orb_id,
  max_runtime_ms: 10 * 60 * 1_000,
  agent_configs: [
    %Aetheris.RunConfig{
      run_id:           at1cmd_id,
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "at1cmd — TAP Tenant Dispatcher (sprint)",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        20,
      context_strategy: :full,
      tools:            ["write_blackboard", "send_message", "run_command"],
      system_prompt:    """
      You are at1cmd, the TAP tenant dispatcher agent.

      Workflow — follow these steps in order:

      Step 1: Parse the student enrollment CSV.
        Call run_command with:
          command: "python3"
          args: ["tenant/scripts/parse_csv.py", "tenant/data/sample_enrollments_t2.csv"]
        Parse the JSON array of rows from stdout.

      Step 2: Package the TAP intent.
        Call run_command with:
          command: "python3"
          args: ["tenant/scripts/package_intent.py", "<rows_json>", "Enroll students from tenant/data/sample_enrollments_t2.csv", "--intent-id", "int-sprint-t2-steady-001", "--correlation-id", "cor-sprint-t2-steady-001", "--source-file", "tenant/data/sample_enrollments_t2.csv"]
        Parse the TAP intent JSON from stdout. Extract the intent_id field.

      Step 3: Write the intent to the blackboard.
        Call write_blackboard with:
          key: "tap:intent:<intent_id>"    (use the actual intent_id from step 2)
          value: <intent_json_string>      (the full intent JSON as a string)

      Step 4: Notify cot1.
        Call send_message with:
          to: "#{cot1_id}"
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
      user_prompt: "Read the enrollment CSV, package a TAP intent, write it to the blackboard, and notify cot1 at run '#{cot1_id}'. Begin."
    },
    %Aetheris.RunConfig{
      run_id:           cot1_id,
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "cot1 — TAP Gateway",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        30,
      context_strategy: :full,
      tools:            ["read_blackboard", "write_blackboard", "send_message", "run_command", "wait_for_event"],
      system_prompt:    """
      You are cot1, the TAP gateway agent for the ct.stu domain.

      You receive TAP intent packets from at1cmd, validate them, execute them
      against ct-api (ETL or direct mode), and return result packets to at1qry.

      Workflow — follow these steps in order:

      Step 1: Wait for a message from at1cmd.
        Call wait_for_event with:
          condition: "message_received"
          timeout_ms: 120000
        The message body contains the intent_id. Extract it.
        The intent_id is the string after "intent_id: " in the message.

      Step 2: Read the TAP intent packet from the blackboard.
        Call read_blackboard with:
          key: "tap:intent:<intent_id>"
        The value is the TAP intent JSON string.

      Step 3: Validate the intent.
        Call run_command with:
          command: "python3"
          args: ["gateway/scripts/validate_intent.py", "<intent_json>", "domain/ct.stu.vocabulary.jsonl"]
        Parse the validation report JSON from stdout.
        If valid is false and errors is non-empty, write a failed result and go to Step 9.

      Step 4: Resolve execution context.
        Read the current execution context from blackboard:
          key: "tap:context:<correlation_id>"
        If not found, use empty context "{}".
        Call run_command with:
          command: "python3"
          args: ["gateway/scripts/resolve_context.py", "<intent_json>", "<context_json>", "domain/ct.stu.vocabulary.jsonl"]
        Parse the resolved context JSON from stdout.
        Note: if unresolved_courses is non-empty, those records will fail individually.

      Step 5: Execute the intent.

        For enroll_students (ETL mode):

          Step 5a: Build ETL job list.
            Call run_command with:
              command: "python3"
              args: ["gateway/scripts/build_etl_job.py", "<intent_json>", "<resolved_context_json>", "domain/ct.stu.behaviour.jsonl"]
            Capture the full stdout as etl_content (the # JOB_KEY header line plus the tab-delimited job lines).

          Step 5b: Upload ETL file to S3.
            Call run_command with:
              command: "python3"
              args: ["gateway/scripts/upload_etl_to_s3.py", "<etl_content>", "<seq>"]
            Parse the s3_path from stdout JSON.

          Step 5c: Submit job to RabbitMQ.
            Call run_command with:
              command: "python3"
              args: ["gateway/scripts/submit_to_rmq.py", "<s3_path>", "<inst_id>", "<etl_content>"]
            Pass the full etl_content from Step 5a as the third argument — the script extracts the JOB_KEY itself.
            Parse the job_ref from stdout JSON.

        For setup_institution or setup_courses (direct mode):

          Step 5d: Execute direct call.
            Call run_command with:
              command: "python3"
              args: ["gateway/scripts/direct_call.py", "<capability>", "<payload_json>", "<on_duplicate>"]
            Parse status and result from stdout JSON.
            If status is "ok" or "duplicate_resolved", extract the ID and update execution context.
            Write updated context to blackboard:
              key: "tap:context:<correlation_id>"

      Step 6: Build the TAP result packet.
        Construct result JSON:
        {
          "tap_version": "0",
          "message_type": "result",
          "intent_id": "<intent_id>",
          "correlation_id": "<correlation_id>",
          "job_ref": "<job_ref or null>",
          "intent_lifecycle": {"status": "queued", "stage": "etl"},
          "records": [<per-record: {name, guid, status, identity_state}>],
          "summary": {"total": N, "queued": N, "failed": 0, "skipped": 0}
        }
        Each record has:
          name: from payload
          guid: the Id assigned in the ETL job (parse from the POST /api/stu/Student lines)
          status: "queued" (ETL mode) or "confirmed" (direct mode)
          identity_state: "deterministic" if UUID v5, "non_idempotent" if UUID v4

      Step 7: Write the result to the blackboard.
        Call write_blackboard with:
          key: "tap:result:<intent_id>"
          value: <result_json_string>

      Step 8: Notify at1qry.
        Call send_message with:
          to: "#{at1qry_id}"
          message: "TAP result ready. intent_id: <intent_id>"

      Step 9: Report what you did — validation outcome, record count, job_ref, s3_path — and finish.

      Rules:
      - All paths are relative to the sandbox root — no absolute paths.
      - Pass full JSON strings as args values.
      - Do not retry on failures — report and stop.
      - context_strategy: :full — never truncate the conversation.
      - If run_command fails (non-zero exit), include the stderr in the result reason and stop.
      """,
      user_prompt: "Wait for the TAP intent, validate it, execute against ct-api, write the result, and notify at1qry at run '#{at1qry_id}'. Begin."
    },
    %Aetheris.RunConfig{
      run_id:           at1qry_id,
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "at1qry — TAP Tenant Collector",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        15,
      context_strategy: :full,
      tools:            ["read_blackboard", "run_command", "wait_for_event"],
      system_prompt:    """
      You are at1qry, the TAP tenant collector agent.

      Workflow — follow these steps in order:

      Step 1: Wait for a message from cot1.
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
        - Confirm the job_ref and s3_path from the result

      Rules:
      - All paths are relative to the sandbox root — no absolute paths.
      - Do not retry — report what you received and finish.
      """,
      user_prompt: "Wait for the TAP result from cot1, run gap analysis, and report all findings. Begin."
    }
  ]
}
