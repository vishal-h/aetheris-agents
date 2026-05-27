## Runbook

### Environment Setup

Source credentials before running any gateway script or sprint:

```bash
source api/.env
```

Required environment variables:

| Variable | Purpose |
|----------|---------|
| `CT_API_BASE_URL` | ct-api base URL, e.g. `https://svc.campustrack.net` (no `/api` suffix) |
| `CT_API_TOKEN` | JWT bearer token; must include nested `AppId` (AccessCode) and `ClientId` (InstId) claims |
| `CT_RABBITMQ_URL` | amqps RabbitMQ URL for ETL job submission |
| `CT_S3_BUCKET` | S3 bucket for ETL file uploads |
| `CT_S3_REGION` | AWS region for the bucket (default `ap-south-1`) |
| `CT_INST_SHORT_CODE` | Short code used in ETL filenames and S3 key prefix |
| `CT_ENV` | Deployment environment label used in ETL filenames (e.g. `dev`, `prod`) |
| `AWS_ACCESS_KEY_ID` | AWS credentials for S3 upload |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for S3 upload |
| `AETHERIS_API_BASE` | Aetheris webhook server URL, e.g. `http://localhost:4001`; read by `notify_at1qry.py` |

Token rotation: `CT_API_TOKEN` expires. If scripts return `410 TokenExpiredException`, update `.env` with a fresh token and re-source.

---

### Ping Check

Always confirm ct-api is reachable before running orbs:

```bash
source api/.env
python3 api/gateway/scripts/ping_ct.py
# Expected: {"status": "ok", "latency_ms": <N>}
```

If ping fails, do not proceed. Check `CT_API_BASE_URL` (must not end with `/api`) and token validity.

---

### T1 Sprint — TAP Plumbing

**Scenario**: End-to-end TAP flow using a stub gateway. No real ct-api calls. Validates intent
packet format, orb messaging, result packet, and gap analysis.

```bash
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t1
```

Expected outcome:
- 57 Python tests pass
- All 3 agents reach `agent_finished`
- at1qry gap report identifies Ravi Kumar as `non_idempotent` (no DOB, no admissionNumber)

---

### T2 Steady-State Sprint

**Scenario**: Institution and courses already exist in ct-api. The enroll_students intent is sent
directly without setup steps. All students are enrolled in SSLC (the only active course in BTLCOL).

```bash
source api/.env
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t2_steady
```

Expected outcome:
- Python tests pass
- All 3 agents reach `agent_finished`
- ETL file uploaded to `s3://{CT_S3_BUCKET}/btlcol/etls/dev_{seq}_btlcol_2425_students.etl`
- RabbitMQ job submitted to `ct_r_etl_worker` queue
- at1qry gap report: Ravi Agent → `non_idempotent` (no DOB, no admissionNumber)

---

### T2 Greenfield Sprint

**Scenario**: Institution and courses do not exist. The OrbConfig runs setup_institution →
setup_courses → enroll_students in sequence (three intent packets, three TAP round-trips).

```bash
source api/.env
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t2_greenfield
```

**Note**: The current BTLCOL token does not have scope for `POST /api/auth/Institution` or
`POST /api/stu/Course` (both return 403). The greenfield sprint documents the intended flow but
will fail at the direct-mode steps until a broader-scope token is available. `direct_call.py`
exits 0 with `{"status": "failed", "reason": "HTTP 403: ..."}` so the orb reports the failure
rather than crashing.

---

### T3 Sprint — Skill Extraction and Clarification

**Scenario**: Two-run case. Run 1 starts cold (no skill hint). After run 1, the cot1 trajectory
is exported and `extract_skill_hints.py` generates a skill hint. Run 2 uses the hint — at1cmd
recognises the intent type without full natural language interpretation.

```bash
source api/.env
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t3
```

Expected outcome:
- Python tests pass
- Both orbs complete with all 3 agents at `agent_finished`
- `api/tenant/data/skill_hint.json` written after run 1
- Run 2 at1cmd step count is reported alongside run 1 (expect equal or fewer steps)

To inspect the skill hint after a sprint:

```bash
cat ../aetheris-agents/api/tenant/data/skill_hint.json | python3 -m json.tool
```

To clear the skill hint and force a cold start:

```bash
rm -f ../aetheris-agents/api/tenant/data/skill_hint.json
```

---

### T4 Sprint — at1qry Persistence via Webhook

**What changed in T4**: cot1 now notifies at1qry via `POST /api/runs/:run_id/resume` (webhook)
as the primary resume path, with `send_message` retained as fallback. This requires the Aetheris
API server to be running before the orb starts.

#### Starting the Aetheris API server

```bash
cd /home/it/sandbox/elixirws/aetheris
mix aetheris server --port 4001
```

Leave this running in a separate terminal. Confirm it is up:

```bash
curl -s http://localhost:4001/api/runs/no-such-run/resume \
  -X POST -H "Content-Type: application/json" -d '{"message":"test"}'
# Expected: 404 response (not connection refused)
```

#### Running the T4 sprint

```bash
source api/.env
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t4
```

Expected outcome:
- All 3 agents reach `agent_finished`
- at1qry trajectory contains an `agent_message_received` event with `from_run_id: "webhook"`
- Webhook call precedes the `send_message` in cot1's trajectory

#### BEAM Restart Verification (manual, not in sprint)

To verify that at1qry survives a BEAM restart while waiting:

1. Start the API server and orb as above.
2. After cot1 writes the result to the blackboard (before Step 7b), kill and restart the Aetheris node:
   ```bash
   # In the aetheris terminal: Ctrl+C to stop, then re-run
   mix aetheris server --port 4001
   ```
3. The at1qry run will have been lost from in-memory state. The webhook POST will return 404.
4. cot1 falls back to `send_message`, which also fails (run gone). cot1 reports and finishes.
5. Recovery: re-run the orb from scratch with the same correlation_id (idempotent records produce same GUIDs).

This is the expected behavior — T4 does not implement durable persistence across BEAM restarts.
That is deferred to T5 (pending m13 durable state).

---

### Operator Replay Procedure

When a TAP result shows failures or non-idempotent records that need re-submission:

1. Retrieve the original intent from the blackboard: `tap:intent:<intent_id>`
2. Check `identity_state` in the result records — `non_idempotent` records may create duplicates on replay.
3. For non-idempotent records, add `dob` or `admissionNumber` to the source data before re-packaging.
4. Re-run at1cmd with the corrected CSV. The new intent will have a new `intent_id`.
5. Monitor the new result at `tap:result:<new_intent_id>` for `queued` status.

---

### Non-Idempotent Capabilities

The following conditions produce UUID v4 (non-idempotent) student GUIDs, meaning duplicate
records may be created on replay:

- Student row has no `date_of_birth` AND no `admissionNumber`
- Both fields are empty/null in the source CSV

Idempotent GUIDs (UUID v5) are generated when either `dob` or `admissionNumber` is present,
keyed on `{inst_id}|{course_name}|{name}|{discriminator}` against namespace
`f435adac-82f1-4894-beee-0c6128fa9216`.

---

### Known Limitations

**ct-api endpoint access (BTLCOL token)**
- `GET /api/stu/Course` returns 403 — course IDs must be pre-seeded in `domain/ct.stu.vocabulary.jsonl`.
- `GET /api/auth/Institution` returns 403 — cannot verify institution existence via API.
- `GET /api/stu/Student/flatData` server-side `name` filter does not work; `lookup_existing.py`
  uses client-side filtering over up to 500 records.
- `GET /api/stu/Etl` returns 403 — ETL job status cannot be polled via API; job progress is
  tracked only through RabbitMQ ack and S3 artifact presence.

**ETL family detail updates (T2)**
- `update_father_details`, `update_mother_details`, `update_guardian_details` are excluded from
  the ETL job list pending confirmation of the correct endpoint format (PUT path param vs POST
  body) with the CT dev team. The TODO is in `build_etl_job.py`.

**Context ordering on webhook resume (T4)**
- `Server.inject_message/2` for `message_received` waits prepends the webhook message to the
  context list rather than appending it. This means the injected message appears at position 0
  of the conversation history rather than at the end. The agent resumes correctly in practice but
  the context ordering is semantically wrong. Fix: change `[context_entry | state.context]` to
  `state.context ++ [context_entry]` in `lib/aetheris/agent/server.ex`.

**BEAM restart (T4)**
- at1qry does not survive a BEAM restart while waiting. Durable persistence is deferred to T5.
  Recovery requires re-running the full orb from scratch.
