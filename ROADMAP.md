# Roadmap

## Completed

### uc-payslip
Generate monthly payslips from a payroll CSV. Per-employee HTML, PDF,
and CSV output. Parallel sub-agents via spawn_agent + wait_for_all.
Scripts handle all computation and file generation; agent orchestrates.

Established the core pattern: **scripts do, agents decide.**

---

### uc-drive
Download payroll CSV from Google Drive before the monthly run. Upload
generated PDFs and CSVs back to Drive after. Bookends uc-payslip
without touching its internals.

- Service account authentication (google-api-python-client + google-auth)
- drive_download.py / drive_upload.py
- Sprint case: `drive`

---

### uc-email
Email each employee their monthly payslip PDF as an attachment.
Completes the payslip pipeline: generate → upload → deliver.

- One send per employee; attaches `{YYYY-MM}-Payslip.pdf`
- Sprint case: `email`

---

### Capability matrix
Auto-generated inventory of all agents and scripts across use cases, with
tool-set overlap analysis. Produced by `agents/capability_matrix.exs`; output
at `docs/capability-matrix.md`. Sprint case: `capability_matrix`.

---

### uc-api-agent — T1 through T5
Agent-to-API communication for the EdTech platform via the TAP protocol.

| Ticket | What it delivered |
|--------|------------------|
| T1 | at1cmd + cot1_stub + at1qry skeleton; TAP intent/result packet format; 3-agent orb |
| T2 | cot1 executes against ct-api: ETL pipeline (parse → validate → build job → S3 → RabbitMQ); direct-mode for setup_institution and setup_courses |
| T3 | Skill extraction (extract_skill_hints.py → skill_hint.json → inject on next run); structured clarification round-trip for unresolved termName |
| T4 | Webhook resume: cot1 POSTs to `POST /api/runs/:run_id/resume` as primary path; send_message retained as fallback; inject_message harness fix (WaitRegistry.notify for message_received wait) |
| T5 | BEAM durability: `resume_from_checkpoint` re-establishes `{:message_received, _}` wait; at1qry survives a node restart while waiting for the webhook |

Sprint cases: `uc_api_agent_t1`, `uc_api_agent_t2_steady`, `uc_api_agent_t2_greenfield`, `uc_api_agent_t3`, `uc_api_agent_t4`, `uc_api_agent_t5`

---

### Ollama provider with XML tool calling (aetheris harness)
Small models (3B–8B) served via Ollama are supported as a local development
path. XML mode injects tool definitions into the system prompt and parses
`<tool_call>` blocks from the response, sidestepping the unreliable native
JSON function-calling output of small models. Enabled by default via
`config/runtime.exs`; use `provider: "ollama"` in any RunConfig.
See `aetheris/docs/aetheris/runbook-ollama-xml.md`.

---

## Active

*(Nothing active at this time.)*

---

## Planned

*(Nothing formally scoped.)*

---

## Pipeline view

### Payslip pipeline (monthly, automated)

```
Drive (download)     uc-drive      ✅ complete
      ↓
Payslip (generate)   uc-payslip    ✅ complete
      ↓
Drive (upload)       uc-drive      ✅ complete
      ↓
Email (deliver)      uc-email      ✅ complete
```

### TAP implementation track

```
TAP v0 design        ✅ complete
      ↓
T1 — TAP skeleton    ✅ at1cmd + cot1_stub + at1qry; orb wired
      ↓
T2 — cot1 execution  ✅ ETL pipeline + direct mode against ct-api
      ↓
T3 — skill / clarify ✅ skill hint injection; clarification round-trip
      ↓
T4 — webhook resume  ✅ primary POST path; inject_message harness fix
      ↓
T5 — BEAM durability ✅ resume_from_checkpoint for message_received waits
```

---

## Design principles (established)

**Scripts do, agents decide.**
Python handles computation, file I/O, API calls, arithmetic.
Agents handle orchestration, routing, synthesis.
LLMs are never asked to generate file content programmatically.

**One script per responsibility.**
Separate compute from generation. Each script is independently
runnable and testable without Aetheris.

**Minimal sub-agent tools.**
Sub-agents get the smallest tool set that lets them do their job.
`["run_command"]` if possible. Add `read_blackboard`, `write_blackboard`,
`send_message` only when the agent genuinely participates in an orb.

**context_strategy: :full on all orb agents.**
`:rolling` truncates old messages and leaves orphaned tool_use_id references,
causing HTTP 400. Use `:full` for any agent running fewer than ~10 steps.

**`__ENV__.file` for sandbox_path in cross-repo agents.**
Never use `File.cwd!()` in `.exs` agent files — it resolves to wherever
`mix aetheris run` was invoked, not to the agent file's location. Use
`Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))` (adjusting
`..` depth to reach the use-case root). This is the only reliable anchor
in a cross-repo setup where the harness and the agents live in sibling
directories.

**Sequential over parallel for independent agents.**
`OrbConfig` implies coupled supervision — all agents share an orb lifecycle,
a blackboard, and a coordinator. Use it only when agents genuinely need to
communicate mid-run (blackboard, send_message, wait_for_event). Agents that
run independently and hand off results via files or env vars should be
separate `run_agent` calls in sprint.sh, not co-tenants of an orb.

**Output structure is stable.**
`{YYYY-MM}-Payslip.{html,pdf,csv}` per employee per month.
Downstream use cases (uc-drive, uc-email) depend on this structure.

**Test before sprint.**
Scripts must run standalone before the agent runs.
pytest passes before sprint.sh runs.
sprint.sh passes before merge.

---

## Reference

- Agent creation guide: docs/agent-creation-guide.md
- TAP v0 design: docs/uc-api-agent-design.md
- Aetheris harness: ../aetheris
- Implementation notes: `{use_case}/docs/t*-implementation-notes.md`
