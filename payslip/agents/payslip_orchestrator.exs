agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

model    = System.get_env("PAYSLIP_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:            "payslip-orch-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          provider,
  model:             model,
  label:             "Payslip Orchestrator",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         20,
  max_spawn_depth:   2,
  context_strategy:  :full,
  tools:             ["run_command", "spawn_agent", "wait_for_all"],
  system_prompt: """
  You are a payslip generation orchestrator for Bitloka Solutions Private Limited.

  Workflow — follow these steps in order:

  1. Run: python3 scripts/payslip_compute.py data/payroll.csv

     The script reads PAYSLIP_EMPLOYEE_ID from the environment automatically.
     If set, it returns only that employee. If not set, it returns all employees.

     Parse the JSON output. Extract the list of employees.
     Each employee has an "employee_id_safe" field (e.g. "BTL_999").

  2. For each employee, call spawn_agent with:
     - tools: ["run_command"]
     - max_steps: 10
     - task_prompt: construct one per employee using the template below.
       Replace {id} with the employee's employee_id_safe.

     Task prompt template:
     ---
     Generate payslips for employee {id}.

     Call run_command with:
       command: "python3"
       args: ["scripts/generate_employee_payslips.py", "{id}", "--csv", "data/payroll.csv"]

     Wait for the command to complete and report its output.
     ---

  3. Collect all run_ids returned by spawn_agent calls.
     Call wait_for_all with the full list and timeout_ms: 300000.

  4. Report: total employees processed, total months generated, any failures.

  Rules:
  - All paths are relative to the sandbox root — no absolute paths in tool calls.
  - overlay_base_dir is nil by design. Output files must persist on disk.
  """,
  user_prompt: "Generate payslips. Check PAYSLIP_EMPLOYEE_ID to determine scope — single employee if set, all employees if not."
}
