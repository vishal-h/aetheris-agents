# Roadmap

## Completed

### uc-payslip
Generate monthly payslips from a payroll CSV. Per-employee HTML, PDF,
and CSV output. Parallel sub-agents via spawn_agent + wait_for_all.
Scripts handle all computation and file generation; agent orchestrates.

Established the core pattern: **scripts do, agents decide.**

---

## Active

### uc-drive
Download payroll CSV from Google Drive before the monthly run. Upload
generated PDFs and CSVs back to Drive after. Bookends uc-payslip
without touching its internals.

- Service account authentication (google-api-python-client + google-auth)
- drive_download.py — pulls payroll.csv from configured Drive folder
- drive_upload.py — pushes *-Payslip.pdf and *-Payslip.csv per employee
- HTML files are local build artefacts — not uploaded
- Technical brief: protocol/TAP-v0-design.md (context), docs/

**Status:** Technical brief written. Ready to start.

---

## Planned

### uc-email
Email each employee their monthly payslip PDF as an attachment.
Completes the payslip pipeline: generate → upload → deliver.

- One sub-agent per employee, parallel
- Attaches {YYYY-MM}-Payslip.pdf directly (per-month file, clean attachment)
- SMTP or email API; credentials from environment
- Input: payslip/output/{employee_id_safe}/{YYYY-MM}-Payslip.pdf
- Composes with uc-payslip output directly

**Depends on:** uc-payslip (complete)

---

### uc-api-agent
Agent-to-API communication for the EdTech platform. Structured data
from local filesystem posted to a well-defined API. Foundation for
the TAP protocol implementation.

Phases:
1. Structured data (CSV/JSON) against test database
2. at1cmd + at1qry split — dispatcher and persistent collector
3. Unstructured data and PDF extraction
4. cot1 minimal implementation — first TAP exchange

**Depends on:** TAP v0 design (complete)

---

## Protocol

### TAP — Tenancy Agency Protocol
*Tap in. Intelligent flow across trust boundaries.*

Agent-to-agent communication protocol for tenant-scoped, trusted
interaction between autonomous agents across organisational boundaries.

- v0 design: protocol/TAP-v0-design.md — architecture, message types,
  participant roles, progressive autonomy arc
- v0.1: intuitive names, refined schemas, open questions resolved
  (emerges from uc-api-agent implementation experience)

TAP is not Aetheris-specific. Any agent framework can implement it.

---

## Pipeline view

### Payslip pipeline (monthly, automated)

```
Drive (download)     uc-drive      ← active
      ↓
Payslip (generate)   uc-payslip    ✅ complete
      ↓
Drive (upload)       uc-drive      ← active
      ↓
Email (deliver)      uc-email      ← planned
```

### TAP implementation track

```
TAP v0 design        ✅ complete
      ↓
uc-api-agent T1      at1cmd + at1qry skeleton
      ↓
uc-api-agent T2      cot1 minimal
      ↓
TAP v0.1             refined from implementation experience
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
["run_command"] if possible. Add read_file or write_file only
when genuinely needed.

**Output structure is stable.**
{YYYY-MM}-Payslip.{html,pdf,csv} per employee per month.
Downstream use cases (uc-drive, uc-email) depend on this structure.
Do not change without updating all dependents.

**Test before sprint.**
Scripts must run standalone before the agent runs.
pytest passes before sprint.sh runs.
sprint.sh passes before merge.

---

## Reference

- Agent creation guide: docs/agent-creation-guide.md
- TAP v0 design: protocol/TAP-v0-design.md
- Aetheris harness: ../aetheris
- Milestone docs: {use_case}/milestone.md
