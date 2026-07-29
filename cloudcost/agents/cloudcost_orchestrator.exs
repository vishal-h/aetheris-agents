# cloudcost/agents/cloudcost_orchestrator.exs
#
# m1-cloudcost t5 — the report pipeline orchestrator.
#
# Linear, four stages, one provider (DigitalOcean):
#   fetch_do.py → detect_orphans.py → compose_report_data.py → render_report.py
#
# Record-and-deliver: `run_command` is a :contained effect, so there is no verify
# support here (D1). No spawn_agent/wait_for_all — a single provider needs no fan-out.
# No write op, no scheduling. The read-only DO token is env-only (D2): it is read by
# fetch_do.py from CLOUDCOST_DO_TOKEN and never appears in a prompt, an argument, or
# the trajectory.
#
#   cd ~/sandbox/elixirws/aetheris
#   mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

# provider/model are literals rather than the AETHERIS_MODEL/AETHERIS_PROVIDER env
# override the sibling agents use: sprint.sh sources aetheris-agents/.env, so an
# override there would silently change what the stub-guard done-check asserts
# `resolved_model` against. §t5 names both literally; keep them that way.

system_prompt = """
You are the cloudcost orchestrator. Run the DigitalOcean cost-report pipeline by
executing the four steps below in order, then report the report file and the orphan
count. Every step is a `run_command` call; each script writes its own output file and
prints a JSON summary to stdout containing the path it wrote.

---

STEP 1 — Fetch the DO cost snapshot and inventory.
  run_command  command: "python3"
               args: ["scripts/fetch_do.py", "--output-dir", "output"]

  Parse the JSON on stdout. Keep three values for later steps:
    - `period`           (e.g. "2026-07")
    - `files.costs`      the cost snapshot path
    - `files.inventory`  the inventory path

  `files.costs` is absent when the billing API was unavailable. That is a partial run,
  not a failure — note it and carry on; STEP 3 has a second arg form for that case.

STEP 2 — Detect orphan candidates from the inventory.
  run_command  command: "python3"
               args: ["scripts/detect_orphans.py", "<INVENTORY>", "--output-dir", "output"]

  Replace "<INVENTORY>" with the `files.inventory` path from STEP 1.
  Parse the JSON on stdout and keep `file` — the orphan-candidates path.

STEP 3 — Compose the report data (merges cost + inventory + orphans, adds the MoM delta).

  If STEP 1 printed `files.costs`, use this form:
    run_command  command: "python3"
                 args: ["scripts/compose_report_data.py", "--cost", "<COSTS>", "--inventory", "<INVENTORY>", "--orphans", "<ORPHANS>", "--output-dir", "output"]

  If STEP 1 did NOT print `files.costs`, use this form instead — drop the flag and its
  value together, and change nothing else:
    run_command  command: "python3"
                 args: ["scripts/compose_report_data.py", "--inventory", "<INVENTORY>", "--orphans", "<ORPHANS>", "--output-dir", "output"]

  Replace "<COSTS>" with `files.costs` from STEP 1, "<INVENTORY>" with `files.inventory`
  from STEP 1, and "<ORPHANS>" with the `file` path from STEP 2.
  Parse the JSON on stdout and keep `file` — the report-data path.

STEP 4 — Render the HTML report.
  run_command  command: "python3"
               args: ["scripts/render_report.py", "<REPORT_DATA>", "--output-dir", "output"]

  Replace "<REPORT_DATA>" with the `file` path from STEP 3.
  Parse the JSON on stdout and keep `file` (the HTML report) and
  `counts.orphan_candidates`.

STEP 5 — Report, in plain text:
    - the HTML report path from STEP 4
    - the orphan-candidate count from STEP 4
    - the period from STEP 1
    - any step that reported `"status": "partial"`, and what it said was degraded

---

Rules:
- Execute the commands exactly as written. Do not add, drop, or reorder arguments.
  The only permitted variation is the two arg forms offered in STEP 3.
- Do not pass "python3" inside the args array — it is already the command field.
- All paths are relative to the sandbox root. overlay_base_dir is nil, so the output
  files persist on disk and are the deliverable.
- Use the path each step printed. Never construct, guess, or reconstruct a filename,
  and never edit a path a script gave you.
- `"status": "partial"` is NOT a failure. These scripts exit non-zero on a partial run
  by design; the output file was still written. Note what was degraded and continue to
  the next step.
- A step fails only when its stdout carries `"status": "error"`, or when the output
  path that step is documented to print is absent from its stdout. In that case report
  which step failed, quote its stderr, and STOP.
- After a failure, stop completely. Do not retry the step, do not re-run a script to
  inspect its output, do not read or list files, and do not run any other command.
- Do not compute, adjust, or restate any figure from the report data. The scripts
  produce every number; you orchestrate and report paths and counts only.
"""

%Aetheris.RunConfig{
  run_id:           "cloudcost-orch-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         "anthropic",
  model:            "claude-haiku-4-5-20251001",
  label:            "Cloudcost Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        20,
  # :full, not :rolling/6 (§t5, corrected in the t5 commit). Four steps is well under the
  # guide's ~10-step threshold, and the workflow threads file paths from STEP 1 through
  # STEP 4 — a rolling window would truncate them out of context mid-pipeline.
  context_strategy: :full,
  tools:            ["run_command"],
  system_prompt:    system_prompt,
  user_prompt:      "Run the cloudcost report pipeline."
}
