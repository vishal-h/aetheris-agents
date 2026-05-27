# uc-api-agent — Milestone

**Status:** ✅ Complete (T1–T5)
**Design doc:** `docs/uc-api-agent-design.md`
**Depends on:** Aetheris m12 complete, m13 planned (T4 only)
**API:** ct.stu (`CT_API_BASE_URL=https://svc.campustrack.net/api`)

---

## Goal

Implement the TAP (Tenancy Agency Protocol) agent pair for structured,
trusted communication between a tenant-side dispatcher and an application-side
gateway. First use case: student enrollment via the ct.stu API.

---

## Exit criterion

- at1cmd reads a student CSV, packages a valid TAP intent packet, dispatches to cot1
- cot1 validates the intent against the vocabulary doc, executes via ETL or direct
  mode, returns a structured result packet
- at1qry receives the result, performs gap analysis, surfaces structured clarifications
  to humans when needed
- Greenfield (setup_institution → setup_courses → enroll_students) and steady-state
  (enroll_students only) scenarios both work end-to-end against ct-api
- Skill extracted after first successful run; second run uses it
- at1qry survives BEAM restarts (m13 T1); resumes via cot1 webhook (m13 T3) ✅
- All scripts have passing tests; all checks pass

---

## Delivery sequence

```
T1 (TAP plumbing — no real API calls)
  └── T2 (cot1 executes against ct-api; both scenarios)
        └── T3 (skill extraction; structured clarification)
              └── T4 (at1qry persistence via m13; webhook resume)
                    └── T5 (BEAM durability: resume_from_checkpoint for message_received waits)
```

T1 and T2 are the critical path. T3 and T4 layer on top without rework.

---

## Tickets

---

### T1 — TAP plumbing

**Branch:** `t1-tap-plumbing`
**Layer:** Python scripts + Elixir agent files
**Depends on:** nothing

**What to build:**

Establish the full TAP message flow using a 3-agent orb with a stub cot1.
No real ct-api calls. Validates intent packet format, orb messaging, result
packet structure, and gap analysis end-to-end.

**Repository structure to create:**

```
uc-api-agent/
  tenant/
    agents/
      at1cmd.exs          ← reads CSV, packages intent, dispatches to cot1_stub
      at1qry.exs          ← waits on blackboard, runs gap analysis, reports
    scripts/
      parse_csv.py        ← CSV → normalised row dicts
      package_intent.py   ← rows + user_intent → TAP intent JSON
      gap_analysis.py     ← TAP result JSON → gap report JSON
    tests/
      conftest.py
      test_parse_csv.py
      test_package_intent.py
      test_gap_analysis.py
    data/
      sample_enrollments.csv   ← anonymised, committed
      .gitignore               ← excludes real data

  gateway/
    agents/
      cot1_stub.exs       ← receives intent, returns mock result
    scripts/
      validate_intent.py  ← TAP intent + vocabulary doc → validation report JSON
      stub_cot1.py        ← intent JSON → mock TAP result JSON
      ping_ct.py          ← GET /api/stu/_Monitor/ping → ok/fail
    tests/
      conftest.py
      test_validate_intent.py
      test_stub_cot1.py

  domain/
    ct.stu.vocabulary.jsonl    ← enroll_students intent, fields, rules, lookups
    ct.stu.behaviour.jsonl     ← execution steps, modes, on_duplicate, outcomes
```

**Sample enrollment CSV (`tenant/data/sample_enrollments.csv`):**

```csv
name,date_of_birth,gender,email,mobile,course,section,roll_no,father_name,father_email,father_mobile,mother_name,mother_email,mother_mobile,guardian_name,guardian_gender,guardian_email,guardian_mobile
Priya Sharma,2010/06/15,Female,,,Standard I,A,1,Rajesh Sharma,rajesh.sharma@gmail.com,9876543210,Sunita Sharma,sunita.sharma@gmail.com,9876543211,,,
Arjun Patel,2011/03/22,Male,,,Standard I,A,2,,,,Meena Patel,,9876543212,,,
Ravi Kumar,,Male,,,Standard II,B,,,,,,,,,,
```

Row 3 (Ravi Kumar) has no DOB and no admissionNumber — exercises the
non-idempotent fallback path in gap analysis.

**TAP message flow (T1):**

```
at1cmd
  step 0: run_command parse_csv.py data/sample_enrollments.csv
          run_command package_intent.py → TAP intent JSON
  step 1: write_blackboard tap:intent:{intent_id}
          send_message → cot1_stub

cot1_stub
  step 0: read_blackboard tap:intent:{intent_id}
          run_command validate_intent.py intent.json domain/ct.stu.vocabulary.jsonl
          run_command stub_cot1.py intent.json → mock result JSON
  step 1: write_blackboard tap:result:{intent_id}
          send_message → at1qry

at1qry
  step 0: wait_for_event blackboard_key = tap:result:{intent_id}
          read_blackboard tap:result:{intent_id}
          run_command gap_analysis.py result.json
  step 1: report summary → agent_finished
```

**Script contracts:**

`parse_csv.py <csv_path>`
- Output (stdout): JSON array of normalised row dicts
- Normalises: dates to ISO8601, gender strings preserved as-is, empty strings → null
- Exit 0 on success, exit 1 on file not found or parse error

`package_intent.py <rows_json> <user_intent> [--correlation-id CID] [--seq N]`
- Output (stdout): TAP intent JSON conforming to the packet schema in design doc
- Flags rows with missing required fields in `flags` array
- Includes `provenance.record_count` and `provenance.batch`

`validate_intent.py <intent_json> <vocabulary_jsonl>`
- Output (stdout): validation report JSON
  `{"valid": true/false, "errors": [...], "warnings": [...], "flags": [...]}`
- Checks required fields, enum values against lookups, conditional rules
- Exit 0 whether valid or not (errors are in the report, not exit code)

`stub_cot1.py <intent_json>`
- Output (stdout): mock TAP result JSON with intent lifecycle states
- All records → `status: "queued"`, `identity_state: "deterministic"` (except
  Charlie Test row → `identity_state: "non_idempotent"`)
- Includes `job_ref: "stub-job-ref-001"` and per-record `{name, guid, status}`

`gap_analysis.py <result_json>`
- Output (stdout): gap report JSON
  `{"total": N, "queued": N, "failed": N, "skipped": N, "non_idempotent": N, "gaps": [...]}`
- Each gap entry: `{record, reason, suggested_action}`
- Exit 0 always

`ping_ct.py`
- GET `{CT_API_BASE_URL}/api/stu/_Monitor/ping`
- Output (stdout): `{"status": "ok", "latency_ms": N}` or `{"status": "error", "reason": "..."}`
- Uses `CT_API_TOKEN` from environment for auth header
- Exit 0 on 200, exit 1 on failure

**Agentic instructions:**

1. Read `docs/agent-creation-guide.md` and `docs/uc-api-agent-design.md` in full
2. Create branch `t1-tap-plumbing`
3. Create the full folder structure above — all directories and placeholder files
4. Write `tenant/data/sample_enrollments.csv` with the three rows above
5. Write `domain/ct.stu.vocabulary.jsonl` — enroll_students intent only (setup_institution
   and setup_courses added in T2); include all fields, rules, lookups from design doc
6. Write `domain/ct.stu.behaviour.jsonl` — enroll_students section only
7. Write `tenant/scripts/parse_csv.py` to contract above; write tests
8. Write `tenant/scripts/package_intent.py` to contract; write tests
9. Write `gateway/scripts/validate_intent.py` to contract; write tests
10. Write `gateway/scripts/stub_cot1.py` to contract; write tests
11. Write `tenant/scripts/gap_analysis.py` to contract; write tests
12. Write `gateway/scripts/ping_ct.py` to contract
13. Run all Python tests: `python3 -m pytest tenant/tests/ gateway/tests/ -v`
14. Write `gateway/agents/cot1_stub.exs` — stub agent file per flow above
15. Write `tenant/agents/at1cmd.exs` — use `__ENV__.file` for sandbox_path
16. Write `tenant/agents/at1qry.exs` — use `wait_for_event` on blackboard key
17. Evaluate agent files without error:
    `mix run --eval 'Code.eval_file("uc-api-agent/tenant/agents/at1cmd.exs")'`
18. Add `uc_api_agent_t1` case to `scripts/sprint.sh`
19. Run sprint: `./scripts/sprint.sh uc_api_agent_t1`
20. Verify orb completes: all three agents reach `agent_finished`
21. Run all checks: format, credo, dialyzer, mix test

**Sprint script case:**

```bash
if [[ "$TARGET" == "uc_api_agent_t1" ]]; then
  section "uc-api-agent T1 — TAP plumbing"

  command -v python3 &>/dev/null || { fail "python3 not found"; exit 1; }
  ok "python3 found"

  [[ -f "uc-api-agent/tenant/data/sample_enrollments.csv" ]] \
    || { fail "sample_enrollments.csv missing"; exit 1; }
  ok "sample data present"

  info "Running Python tests"
  python3 -m pytest uc-api-agent/tenant/tests/ uc-api-agent/gateway/tests/ -q \
    || { fail "Python tests failed"; exit 1; }
  ok "Python tests passed"

  run_orb "uc-api-agent-t1" "$OUT_DIR/uc_api_agent_t1/orb.json" \
    "uc-api-agent/tenant/agents/at1cmd.exs" \
    "uc-api-agent/gateway/agents/cot1_stub.exs" \
    "uc-api-agent/tenant/agents/at1qry.exs"

  ok "T1 orb complete"
fi
```

**Acceptance criteria:**

- `python3 -m pytest` passes across all T1 scripts
- at1cmd produces a valid TAP intent packet (validated by validate_intent.py returning `valid: true`)
- cot1_stub returns a result packet with correct lifecycle states
- at1qry produces a gap report identifying the Ravi Kumar row as `non_idempotent`
- Orb completes with all three agents at `agent_finished`
- `mix test` passes with no new failures

---

### T2 — cot1 executes against ct-api

**Branch:** `t2-cot1-execution`
**Layer:** Python scripts + Elixir agent files
**Depends on:** T1 merged

**What to build:**

Replace cot1_stub with a real cot1 agent that executes against ct-api. Implements
both execution modes (ETL and direct), execution context threading, the full
vocabulary and behaviour docs, pre-execution validation, idempotency mechanisms,
and the greenfield and steady-state scenarios.

**New files:**

```
gateway/
  agents/
    cot1.exs                   ← real gateway agent
  scripts/
    resolve_context.py         ← execution context threading helpers
    build_etl_job.py           ← TAP intent + context → ETL job list
    submit_etl_job.py          ← ETL job list → RabbitMQ → job_ref
    direct_call.py             ← single direct-mode API call wrapper
    lookup_existing.py         ← deduplication guard: search ct-api by name+course
  tests/
    test_build_etl_job.py
    test_resolve_context.py
    test_lookup_existing.py

domain/
  ct.stu.vocabulary.jsonl      ← extended: setup_institution + setup_courses added
  ct.stu.behaviour.jsonl       ← extended: direct-mode intents with on_duplicate
```

**Script contracts:**

`build_etl_job.py <intent_json> <context_json> <behaviour_jsonl>`
- Resolves CourseIds from context then vocabulary doc lookup
- Generates deterministic GUIDs (UUID v5) where possible
- Falls back to deduplication guard (lookup_existing.py) for non-idempotent records
- Falls back to random UUID v4 if search unavailable, flags `non_idempotent: true`
- Output (stdout): ETL job list (one line per `METHOD\tENDPOINT\tJSON`)
- Output includes job idempotency key header

`submit_etl_job.py <etl_job_list>`
- Posts job list to RabbitMQ with job idempotency key
- Output (stdout): `{"job_ref": "...", "status": "queued"}`
- Reads `CT_RABBITMQ_URL` from environment

`direct_call.py <capability> <payload_json> <on_duplicate>`
- Calls ct-api for the named capability
- Handles `on_duplicate: return_existing_id` — catches 409, queries existing record,
  returns its ID
- Output (stdout): `{"status": "ok"|"duplicate_resolved"|"failed", "result": {...}}`

`lookup_existing.py <name> <course_name> <sec_name>`
- Queries ct-api for existing student matching name + course + section
- Output (stdout): `{"found": true/false, "guid": "..."|null}`
- Used by build_etl_job.py for deduplication guard
- If endpoint unavailable: `{"found": false, "search_unavailable": true}`

**cot1.exs flow:**

```
step 0: read vocabulary + behaviour docs
        read_blackboard tap:intent:{intent_id}
        run_command validate_intent.py → validation report
        if invalid: write result (failed/validation), send to at1qry, finish

step 1: send clarification if needed (max 2 rounds)
        wait_for_event blackboard_key = tap:clarify_response:{intent_id}

step 2: pipeline staging check — confirm all direct-mode ancestors confirmed
        run_command resolve_context.py → resolved context JSON

step 3: for direct-mode intents (setup_institution, setup_courses):
          run_command direct_call.py capability payload on_duplicate
          update execution context with result
          write_blackboard tap:context:{correlation_id}

step 4: for ETL-mode intents (enroll_students):
          run_command build_etl_job.py intent.json context.json behaviour.jsonl
          run_command submit_etl_job.py job_list → job_ref

step 5: write_blackboard tap:result:{intent_id}
        send_message → at1qry
```

**Environment variables required for T2:**

```
CT_API_BASE_URL=https://svc.campustrack.net/api
CT_API_TOKEN=<jwt>
CT_RABBITMQ_URL=<rabbitmq connection string>
```

**Verify in T2:**

- Does `POST /api/stu/Student/flatData` or `POST /api/stu/Student/getFilters`
  support reliable name + course lookup? If yes: implement full deduplication guard.
  If no: document as "Non-idempotent capabilities requiring manual cleanup" in runbook,
  downgrade `on_duplicate` to `"fail"` for affected capabilities.
- Does `POST /api/stu/Student` respond with the created record's GUID? Confirm the
  ETL pre-generation approach is correct (GUID sent in payload, not returned).

**T2 runbook additions (write to `runbook.md`):**

- Environment setup for T2
- How to run greenfield scenario (setup_institution → setup_courses → enroll_students)
- How to run steady-state scenario (enroll_students only)
- Operator replay procedure (verbatim from design doc — the 5-step pre-replay checklist)
- Non-idempotent capabilities list (populated after verifying lookup endpoint)

**Agentic instructions:**

1. Read `docs/agent-creation-guide.md` and `docs/uc-api-agent-design.md` in full
2. Create branch `t2-cot1-execution`
3. Run `./scripts/sprint.sh uc_api_agent_t1` — confirm T1 still passes
4. Extend `domain/ct.stu.vocabulary.jsonl` with setup_institution and setup_courses
5. Extend `domain/ct.stu.behaviour.jsonl` with direct-mode intents and `on_duplicate`
6. Write `gateway/scripts/build_etl_job.py` and tests
7. Write `gateway/scripts/submit_etl_job.py`
8. Write `gateway/scripts/direct_call.py`
9. Write `gateway/scripts/lookup_existing.py` — verify search endpoint first via ping
10. Write `gateway/scripts/resolve_context.py`
11. Run Python tests: `python3 -m pytest gateway/tests/ -v`
12. Run ping test: `python3 uc-api-agent/gateway/scripts/ping_ct.py`
    If it fails, stop — do not proceed without connectivity confirmed
13. Write `gateway/agents/cot1.exs`
14. Test steady-state scenario first (enroll_students only — simpler)
15. Test greenfield scenario (full 3-intent chain)
16. Add `uc_api_agent_t2_steady` and `uc_api_agent_t2_greenfield` sprint cases
17. Write T2 runbook additions to `runbook.md`
18. Run all checks

**Acceptance criteria:**

- `ping_ct.py` exits 0 before any other T2 work proceeds
- Steady-state enrollment: at1cmd → cot1 → RabbitMQ → result packet → at1qry
- Greenfield enrollment: setup_institution (direct, on_duplicate handled) →
  setup_courses (direct, on_duplicate handled) → enroll_students (ETL)
- Intent lifecycle states correct in all result packets
- Replay of failed greenfield correlation is safe (on_duplicate: return_existing_id)
- Deduplication guard implemented or documented as gap with manual cleanup procedure
- Runbook covers both scenarios and operator replay procedure
- All checks pass

---

### T3 — Skill extraction and structured clarification

**Branch:** `t3-skill-clarification`
**Layer:** Elixir agent files + Python scripts
**Depends on:** T2 merged

**What to build:**

After the first successful run, extract a skill from the trajectory. Second run
uses the skill — at1cmd recognises the intent type without full natural language
interpretation. Implements the structured clarification round-trip with at1qry
validation loop.

**New files:**

```
tenant/
  scripts/
    extract_skill_hints.py     ← trajectory → skill hint JSON for at1cmd
  tests/
    test_extract_skill_hints.py
```

**Skill extraction flow:**

After T2's first successful enrollment run, `Aetheris.extract_skill/3` is called
on the run trajectory. The extracted skill is injected into at1cmd on the next run
via `Aetheris.inject_skill/2`. at1cmd's second-run prompt recognises `enroll_students`
directly rather than reasoning from scratch about the user's intent.

`extract_skill_hints.py <trajectory_json>`
- Reads a trajectory JSON export
- Extracts: intent_type used, field mapping decisions made, flags raised
- Output (stdout): hint JSON for injection into at1cmd system prompt
- Used by at1cmd on subsequent runs if skill file exists

**Structured clarification round-trip:**

cot1 → at1qry clarification request:
```json
{
  "tap_version": "0",
  "message_type": "clarification_request",
  "intent_id": "...",
  "correlation_id": "...",
  "field": "termName",
  "clarification_type": "select_one",
  "options": ["Annual", "Term 1 2026", "Term 2 2026"],
  "context": "required for 47 records",
  "round": 1,
  "max_rounds": 2
}
```

at1qry validation before forwarding:
- `select_one`: response value must be in `options`
- `confirm`: response must be boolean
- Invalid → re-present with error note, round consumed
- Round limit reached → fail intent with `reason: "clarification_unresolved"`

**at1cmd second-run behaviour:**

```elixir
# at1cmd.exs — second run detects existing skill
skill_hint_path = Path.join(agent_root, "tenant/data/skill_hint.json")
skill_context = if File.exists?(skill_hint_path) do
  "Previous run skill:\n" <> File.read!(skill_hint_path)
else
  ""
end
```

**Agentic instructions:**

1. Read `docs/uc-api-agent-design.md` — natural language → structured progression section
2. Create branch `t3-skill-clarification`
3. Confirm T2 sprint passes before starting
4. Write `extract_skill_hints.py` and tests
5. Add skill extraction call to sprint script after successful T2 run
6. Update `tenant/agents/at1cmd.exs` to inject skill hint if present
7. Implement clarification request/response in `gateway/agents/cot1.exs`:
   - Detect fields requiring clarification after validation
   - Write clarification request to blackboard
   - Send message to at1qry
   - Wait for response via `wait_for_event`
8. Implement clarification handling in `tenant/agents/at1qry.exs`:
   - Receive clarification request
   - Validate response schema before forwarding
   - Re-present on invalid response (consuming round)
   - Fail intent if round limit reached
9. Add `uc_api_agent_t3` sprint case:
   - Run 1: natural language, no skill hint
   - Extract skill after run 1
   - Run 2: with skill hint injected
   - Verify run 2 reaches `validated` state faster (fewer LLM steps)
10. Run all checks

**Acceptance criteria:**

- Skill extracted from T2 trajectory and written to `tenant/data/skill_hint.json`
- Second run with skill hint reaches intent dispatch in fewer steps than first run
- Clarification round-trip works: cot1 asks, at1qry validates, human picks, cot1 resumes
- Invalid human response is rejected and round consumed (not a free retry)
- Round limit reached → intent fails with `clarification_unresolved`
- All checks pass

---

### T4 — at1qry persistence via m13

**Branch:** `t4-at1qry-persistence`
**Layer:** Elixir agent files
**Depends on:** T3 merged, m13 T1 merged, m13 T3 merged

**What to build:**

at1qry survives BEAM restarts while waiting for cot1 results. cot1 resumes at1qry
via webhook when results are ready. Full async round-trip: at1cmd dispatches and
exits; cot1 executes (potentially minutes later); at1qry wakes on webhook, processes,
exits.

**Changes to existing files:**

`tenant/agents/at1qry.exs`:
- Add `context_strategy: :rolling, max_context_steps: 6` — prevents context
  overflow on long-running waits
- at1qry starts, registers wait condition for `tap:result:{correlation_id}`,
  checkpoints to SQLite (m13 T1), and suspends
- On BEAM restart: m13 Application resume scan restores at1qry from checkpoint
- On cot1 webhook `POST /api/runs/{run_id}/resume`: at1qry wakes, reads result,
  runs gap analysis, exits

`gateway/agents/cot1.exs`:
- After writing result to blackboard, POST to at1qry's resume endpoint:
  `POST {AETHERIS_API_BASE}/api/runs/{at1qry_run_id}/resume`
  with result packet as message body
- `at1qry_run_id` passed via environment or blackboard at orb start

**New environment variables:**

```
AETHERIS_API_BASE=http://localhost:4001   ← m13 T3 webhook API
```

**Agentic instructions:**

1. Read `docs/uc-api-agent-design.md` — persistence section and m13 T3 note
2. Confirm m13 T1 and m13 T3 are merged before starting
3. Create branch `t4-at1qry-persistence`
4. Verify m13 T3 `inject_message` satisfies `wait_for_event` — check
   `WaitRegistry.notify` is called on webhook resume. If not, raise before proceeding.
5. Update `tenant/agents/at1qry.exs` with context strategy and checkpoint behaviour
6. Update `gateway/agents/cot1.exs` to POST to at1qry resume endpoint after result
7. Add `uc_api_agent_t4` sprint case:
   - Start orb
   - After at1cmd dispatches, kill and restart the BEAM
   - Confirm at1qry resumes automatically from checkpoint
   - Confirm cot1 webhook wakes at1qry after ETL (simulated with stub)
   - Confirm gap report produced correctly
8. Run all checks

**Acceptance criteria:**

- at1qry checkpointed to SQLite after registering wait condition
- BEAM restart automatically resumes at1qry — no manual intervention
- cot1 webhook resumes at1qry within one execution cycle
- Gap report produced correctly after webhook resume
- Injected message from webhook appears in at1qry trajectory
- All checks pass

---

### T5 — BEAM durability

**Layer:** Aetheris harness (`lib/aetheris/agent/server.ex`)
**Depends on:** T4 merged
**Status:** ✅ Complete

**What was built:**

`resume_from_checkpoint` was silently abandoning at1qry runs that had checkpointed
while waiting for the cot1 webhook. Three independent guards each prevented resume:
(1) `decode_checkpoint` returned `:unresumable` for `{:message_received, _}` conditions;
(2) `handle_call(:resume_from_checkpoint)` discarded the decoded `wait_condition` with `_`;
(3) `do_resume` unconditionally set `wait_condition: nil` in the resumed server state.

All three were fixed. On resume, `{:message_received, _}` waits are now restored in server
state and the server process pre-registers in `WaitRegistry` before the Task starts,
ensuring the run is wakeable immediately after `resume_from_checkpoint/1` returns `:ok`.
All other wait conditions (`{:agent_done, _}`, `nil`) remain cleared on resume.

**Acceptance criteria:**

- ✅ `resume_from_checkpoint/1` returns `:ok` for a `{:message_received, _}` checkpoint
- ✅ `WaitRegistry.notify` unblocks a resumed run to terminal state
- ✅ `:blackboard_key` checkpoint still returns `:unresumable` (regression guard)
- ✅ T4 regression: webhook path intact after T5 changes (sprint Part A)
- ✅ All checks pass (676 tests, 0 failures)

---

## Repository structure (complete at T2)

```
uc-api-agent/
  tenant/
    agents/
      at1cmd.exs
      at1qry.exs
    scripts/
      parse_csv.py
      package_intent.py
      gap_analysis.py
      extract_skill_hints.py       ← T3
    tests/
      conftest.py
      test_parse_csv.py
      test_package_intent.py
      test_gap_analysis.py
      test_extract_skill_hints.py  ← T3
    data/
      sample_enrollments.csv
      skill_hint.json              ← T3, generated not committed
      .gitignore

  gateway/
    agents/
      cot1.exs
      cot1_stub.exs
    scripts/
      validate_intent.py
      stub_cot1.py
      ping_ct.py
      build_etl_job.py             ← T2
      submit_etl_job.py            ← T2
      direct_call.py               ← T2
      lookup_existing.py           ← T2
      resolve_context.py           ← T2
    tests/
      conftest.py
      test_validate_intent.py
      test_stub_cot1.py
      test_build_etl_job.py        ← T2
      test_resolve_context.py      ← T2
      test_lookup_existing.py      ← T2

  domain/
    ct.stu.vocabulary.jsonl
    ct.stu.behaviour.jsonl

  docs/
    uc-api-agent-design.md
  milestone.md
  README.md
  runbook.md
```

---

## Claude Code prompts

**T1:**
```
Read docs/agent-creation-guide.md and docs/uc-api-agent-design.md in full.
We are building uc-api-agent. Begin ticket T1 only.

Before writing any code:
- Create branch t1-tap-plumbing
- Read the T1 ticket in full including script contracts and TAP message flow
- Confirm python3 is available: python3 --version

Follow the T1 agentic instructions in order.
Write tests before agent files.
Run python3 -m pytest after each script is complete.
Evaluate agent files with mix run --eval before running the sprint.
Run ./scripts/sprint.sh uc_api_agent_t1 to validate.
Do not proceed to T2, T3, or T4.
```

**T2:**
```
Read docs/agent-creation-guide.md and docs/uc-api-agent-design.md in full.
We are building uc-api-agent. Begin ticket T2 only.
T1 must be merged before starting.

Before writing any code:
- Create branch t2-cot1-execution
- Run ./scripts/sprint.sh uc_api_agent_t1 to confirm T1 still passes
- Run ping_ct.py first: python3 uc-api-agent/gateway/scripts/ping_ct.py
  If it fails, stop and report — do not proceed without connectivity

Follow the T2 agentic instructions in order.
Test steady-state scenario before greenfield.
Write the runbook additions before marking T2 done.
Do not proceed to T3 or T4.
```

**T3:**
```
Read docs/agent-creation-guide.md and docs/uc-api-agent-design.md in full.
We are building uc-api-agent. Begin ticket T3 only.
T2 must be merged before starting.

Before writing any code:
- Create branch t3-skill-clarification
- Confirm T2 sprint passes

Follow the T3 agentic instructions in order.
The clarification validation loop is critical — test the invalid-response path
explicitly (verify round is consumed, not a free retry).
Do not proceed to T4.
```

**T4:**
```
Read docs/agent-creation-guide.md and docs/uc-api-agent-design.md in full.
We are building uc-api-agent. Begin ticket T4 only.
T3 AND m13 T1 AND m13 T3 must all be merged before starting.

Before writing any code:
- Create branch t4-at1qry-persistence
- Verify m13 T3 inject_message satisfies wait_for_event (step 4 in agentic instructions)
  If it does not, stop and raise before writing any code

Follow the T4 agentic instructions in order.
The BEAM restart test is mandatory — do not mark T4 done without running it.
```
