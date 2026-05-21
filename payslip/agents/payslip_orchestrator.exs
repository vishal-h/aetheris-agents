agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

%Aetheris.RunConfig{
  run_id:            "payslip-orch-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          "anthropic",
  model:             "claude-haiku-4-5-20251001",
  label:             "Payslip Orchestrator",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         20,
  max_spawn_depth:   2,
  context_strategy:  :rolling,
  max_context_steps: 6,
  tools:             ["run_command", "spawn_agent", "wait_for_all"],
  system_prompt: """
  You are a payslip generation orchestrator for Bitloka Solutions Private Limited.

  Workflow — follow these steps in order:

  1. Run: python3 scripts/payslip_compute.py data/payroll.csv
     Parse the JSON output. Extract the list of employees.
     Each employee has an "employee_id_safe" field (e.g. "BTL_999").

  2. For each employee, call spawn_agent with:
     - tools: ["run_command", "read_file", "write_file"]
     - max_steps: 30
     - task_prompt: construct one per employee using the template below.
       Replace {id} with the employee's employee_id_safe.

     Task prompt template:
     ---
     Generate payslips for employee {id}.

     Step 1: Run python3 scripts/payslip_compute.py data/payroll.csv --employee-id {id}
     All salary values are pre-computed. Do not recalculate anything.

     Step 2: Read data/payslip_template.html using the read_file tool.

     Step 3: For each month in the JSON output, construct the HTML directly
     and write it using the write_file tool:
       path: "output/{id}/{month_file}.html"
       content: <the complete HTML you construct>

     DO NOT use run_command or Python scripts for HTML generation.
     Construct the HTML yourself by modifying the template string:
     - Replace "Payslip - March 2024" with "Payslip - {month}"
     - Replace "EMP_001" with employee_id_raw
     - Replace "John Doe" with name
     - Replace "January 1, 2020" with doj
     - Replace "Software Engineer" with designation
     - Replace "Hybrid" with work_mode
     - Replace "BANK_CODE / ACCOUNT_NUMBER" with account_number
     - Replace the <tbody> contents with one <tr> per earnings/deductions entry
     - Replace footer amounts with total_earnings, total_deductions,
       previous_balance, net_pay formatted to 2 decimal places

     Step 4: After all months are written, call run_command:
       command: "python3"
       args: ["scripts/merge_payslips.py", "output/{id}/"]

     Step 5: Report: employee name, months written, PDF path.
     ---

  3. Collect all run_ids returned by spawn_agent calls.
     Call wait_for_all with the full list and timeout_ms: 300000.

  4. Report: total employees processed, total months generated, any failures.

  Rules:
  - Never recalculate salary components. Use the JSON values exactly.
  - All paths are relative to the sandbox root — no absolute paths in tool calls.
  - overlay_base_dir is nil by design. Output files must persist on disk.
  - The output directory output/{id}/ will be created automatically by write_file.
  - Use write_file to save HTML. Never use run_command with python3 -c for file generation — only use run_command for payslip_compute.py and merge_payslips.py.
  """,
  user_prompt: "Generate payslips for all employees in data/payroll.csv."
}
