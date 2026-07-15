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

### uc-provenance-validation

End-to-end validation of the Provenance pipeline against the test
sandbox before the real corpus run.

Tasks — complete in order:

1. Taxonomy session — run `taxonomy_session.py` interactively,
   produce `provenance/agents/taxonomy.md`
2. Classification — run `classify_orchestrator.exs` against sandbox,
   validate batches, confidence scores, needs_review handling
3. Review cycle — export → human edit → import → confirm migration_queue
4. Migration — run `migration_agent.exs` against sandbox,
   confirm SHA-256 verification and rollback
5. Zip archaeology — run `zip_orchestrator.exs` against sandbox,
   confirm new-to-corpus finds and encrypted escalation
6. Search validation — `validate_search.py`, pass rate ≥ 85%
7. Eval sprint — `./scripts/sprint.sh eval`, all tasks pass

**Depends on:** uc-payslip (complete), all Provenance milestones m1–m6
(complete)

**Blocks:** real corpus run

**Status:** Ready to start. Test sandbox available at
`~/sandbox/provenance-test/`. Run
`python3 provenance/scripts/create_test_sandbox.py --overwrite`
to reset between validation runs.

---

### uc-ingestion

Universal inbound document pipeline: ingest → extract → validate →
generate → deliver. Extends Docbuilder (outbound-only today) with an
inbound leg. Full design:
`../aetheris/docs/aetheris/research/universal-ingestion-extraction-pipeline-2026-06.md`.

Core abstraction: the **artefact manifest** — every source adapter
(pdf, docx, xlsx, email, slack, …) produces the same typed JSON shape;
the extraction agent consumes it without knowing the source format.
Every element carries a confidence score; low-confidence extractions
block generation pending human review (single-shot model, same pattern
as Docbuilder m4).

Phases — complete in order:

1. **Single-source, text + tables** — `pdf_extract.py`, `docx_extract.py`,
   `xlsx_extract.py`; `ingestion_agent.exs` (file-type router),
   `extraction_agent.exs` (hardcoded schema), `validation_agent.exs`;
   wire to existing `docbuilder_orchestrator.exs` for generation/delivery.
   Proves the manifest contract.
2. **Second source type** — `email_extract.py` or `slack_extract.py`
   through the unchanged pipeline. Proves format-agnosticism.
3. **Schema registry** — schemas move from hardcoded prompt to a
   `schemas/` directory; extraction agent takes `--schema`; add a second
   schema. (First consumer of the harness semantic-facts table if that
   lands — see Cross-repo dependencies.)
4. **Vision sub-agents** — rasterise image elements; `vision_agent.exs`
   spawned per image element, results merged into extracted JSON.
5. **Multi-source synthesis** — one concrete scenario only (e.g.
   contract DOCX + Slack approval thread → procurement record). No
   generalisation until this works.

Reused unchanged from Docbuilder: all generation scripts
(`generate_docx.py`, `generate_pdf.py`, …), `rename_output.py`,
`upload_output.py`, `email_send_review.py`, `validate_fields.py`,
`_drive.py`.

**Depends on:** Docbuilder (complete); ETXTBSY answer from the harness
(see Cross-repo dependencies) before the orchestrator is designed.

**Blocks:** nothing.

**Status:** Design complete (research brief). Phase 1 ready to scope
once the ETXTBSY question is answered.

---

## Cross-repo dependencies

Items where the harness repo is upstream or downstream. Keep in sync with
the matching section in `../aetheris/ROADMAP.md`.

| Item | Agents side | Harness side |
|---|---|---|
| ETXTBSY / `spawn_agent` worker sharing | uc-ingestion orchestrator design blocked on the answer (proper `.exs` vs Python chain, as in `chain_docbuilder.py`) | Harness answers: does a spawned sub-agent re-copy the worker binary? |
| `caused_by` event field | Rig causal-tree view; Provenance audit lineage ("which passage caused this classification?") | Harness Horizon 0 ticket |
| `observation` convention | Lands in `docs/agent-creation-guide.md`: emit a structured observation at each significant decision point | Motivated by coming-loop brief |
| BL-008 skills | Agent files gain `skill_injected` visibility; sprint runs leave skill rows; possible convention edits proposed by extraction | Harness Horizon 2 milestone |
| Semantic facts table | uc-ingestion phase 3 schema registry is the first consumer | Optional harness Horizon 3 pre-work |
| E5 — IP sweep | Owns client-specific material by design; confirm nothing needs relocating *into* it from harness | Sweep harness repo + research briefs + eval fixtures |
| Pilot delivery (Tier A) | Pilot agents/scripts authored per client engagement; live in a per-client directory or private branch, never in the shared use-case tree | No harness work required |

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
- Harness roadmap: ../aetheris/ROADMAP.md
- Research briefs: ../aetheris/docs/aetheris/research/
