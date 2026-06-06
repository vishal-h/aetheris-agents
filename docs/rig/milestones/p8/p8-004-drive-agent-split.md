# p8-004 — Drive agent split: download + upload orchestrators

## Context

`drive_orchestrator.exs` is a monolithic agent that downloads the payroll
CSV, runs the payslip orchestrator, and uploads the results — all in one.
Now that the top-level orchestrator handles sequencing, the payslip step
inside drive_orchestrator causes it to be run twice and fails because
`mix aetheris run` cannot be found inside the sandbox working directory.

This ticket splits `drive_orchestrator.exs` into two focused agents:
- `drive_download_orchestrator.exs` — download payroll CSV only
- `drive_upload_orchestrator.exs` — upload payslip PDFs only

The top-level orchestrator sequences them: download → payslip →
upload → email.

---

## Files to create

### `drive/agents/drive_download_orchestrator.exs`

```elixir
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
  You are a Drive download orchestrator. Execute this single step.
  Stop and report the error if the step exits non-zero.

  Step 1 — Download payroll CSV from Drive:
    command: "python3"
    args: ["drive/scripts/drive_download.py"]
  Confirm: exits 0 and prints "Saved to:".

  Report the filename downloaded and the destination path.
  """,
  user_prompt: "Download the payroll CSV from Google Drive."
}
```

### `drive/agents/drive_upload_orchestrator.exs`

```elixir
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
```

---

## Files to modify

### `drive/agents/drive_orchestrator.exs`

Keep the file — rename the label and remove step 2 (mix aetheris run).
This preserves backward compatibility for anyone running the monolithic
workflow manually. Update system_prompt to only do download + upload:

```
system_prompt: """
You are a Drive workflow orchestrator. Execute these two steps in order.
Stop and report the error if any step exits non-zero.

Step 1 — Download payroll CSV from Drive:
  command: "python3"
  args: ["drive/scripts/drive_download.py"]
Confirm: exits 0 and prints "Saved to:".

Step 2 — Upload payslip files to Drive:
  command: "python3"
  args: ["drive/scripts/drive_upload.py"]
Confirm: exits 0 and prints "uploaded".

Report: files downloaded, upload summary.
""",
```

### `agents/orchestrator.exs`

Update the few-shot example for the email payslips request to use the
4-step sequence and update `STEP_CONFIG_HINTS`:

```
Request: "email payslips to all employees for May 2026"
{
  "steps": [
    {
      "id": "step-1",
      "agent": "drive/agents/drive_download_orchestrator.exs",
      "description": "Download payroll CSV from Google Drive",
      "context": "Downloads payroll.csv from the configured Google Drive folder to payslip/data/"
    },
    {
      "id": "step-2",
      "agent": "payslip/agents/payslip_orchestrator.exs",
      "description": "Compute and generate payslips for May 2026",
      "context": "Reads payslip/data/payroll.csv, generates PDFs to payslip/output/{employee_id}/2026-05-Payslip.pdf"
    },
    {
      "id": "step-3",
      "agent": "drive/agents/drive_upload_orchestrator.exs",
      "description": "Upload payslip PDFs to Google Drive",
      "context": "Uploads payslip/output/ PDFs to the May 2026 period folder in Drive"
    },
    {
      "id": "step-4",
      "agent": "email/agents/email_orchestrator.exs",
      "description": "Email payslips to all employees",
      "context": "Sends May 2026 payslip PDFs to the configured delivery address"
    }
  ],
  "params": { "PAYSLIP_MONTH": "2026-05" }
}
```

### `rig/src/components/modules/orchestrator/OrchestratorView.tsx`

Update `STEP_CONFIG_HINTS` — replace the single `drive_orchestrator.exs`
entry with entries for both new agents:

```typescript
const STEP_CONFIG_HINTS: Record<string, string[]> = {
  'drive/agents/drive_download_orchestrator.exs': ['GOOGLE_SERVICE_ACCOUNT', 'DRIVE_ROOT_FOLDER_ID'],
  'drive/agents/drive_upload_orchestrator.exs':   ['GOOGLE_SERVICE_ACCOUNT', 'DRIVE_ROOT_FOLDER_ID'],
  'drive/agents/drive_orchestrator.exs':          ['GOOGLE_SERVICE_ACCOUNT', 'DRIVE_ROOT_FOLDER_ID'],
  'email/agents/email_orchestrator.exs':          ['SMTP_TO', 'SMTP_FROM'],
  'provenance/agents/scan_orchestrator.exs':      ['PROVENANCE_NAS_PATH'],
  'provenance/agents/classification_orchestrator.exs': [],
};
```

Keep `drive_orchestrator.exs` entry for backward compatibility.

---

## Acceptance criteria

- [ ] `drive_download_orchestrator.exs` created — download only, max_steps 4
- [ ] `drive_upload_orchestrator.exs` created — upload only, max_steps 4
- [ ] `drive_orchestrator.exs` updated — step 2 (mix aetheris run) removed
- [ ] `orchestrator.exs` few-shot example updated to 4-step sequence
- [ ] `STEP_CONFIG_HINTS` updated for both new agents
- [ ] Running "email payslips for may 2026" through Rig produces a 4-step plan
- [ ] No TypeScript any
- [ ] `bun run build` exits 0

---

## Notes

**`drive_orchestrator.exs` kept.** The monolithic agent is kept for manual
use — someone may want to run the full drive workflow (download + upload)
without going through the top-level orchestrator. Removing step 2 makes
it safe to use in either context.

**`PAYSLIP_MONTH` injected for upload.** The top-level orchestrator
injects `PAYSLIP_MONTH` for all steps via `System.put_env`. The upload
agent gets it automatically — `drive_upload.py` reads it to navigate to
the correct period folder.

**Capability matrix.** Re-run `./scripts/sprint.sh capability_matrix`
after this change to update `docs/capability-matrix.md` with the two new
agent files. The Agents view in Rig will then show them correctly.
