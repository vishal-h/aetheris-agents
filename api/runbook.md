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

### T2 Steady-State Sprint

**Scenario**: Institution and courses already exist in ct-api. The enroll_students intent is sent directly without setup steps. All students are enrolled in SSLC (the only active course in BTLCOL).

```bash
source api/.env
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t2_steady
```

Expected outcome:
- Python tests pass
- Orb completes with all 3 agents reaching `agent_finished`
- ETL file uploaded to `s3://{CT_S3_BUCKET}/btlcol/etls/dev_{seq}_btlcol_2425_students.etl`
- RabbitMQ job submitted to `ct_r_etl_worker` queue
- at1qry gap report: Ravi Agent → `non_idempotent` (no DOB, no admissionNumber)

---

### T2 Greenfield Sprint

**Scenario**: Institution and courses do not exist. The OrbConfig runs setup_institution → setup_courses → enroll_students in sequence (three intent packets, three TAP round-trips).

```bash
source api/.env
cd /home/it/sandbox/elixirws/aetheris
./scripts/sprint.sh uc_api_agent_t2_greenfield
```

**Note**: The current BTLCOL token does not have scope for `POST /api/auth/Institution` or `POST /api/stu/Course` (both return 403). The greenfield sprint documents the intended flow but will fail at the direct-mode steps until a broader-scope token is available. `direct_call.py` exits 0 with `{"status": "failed", "reason": "HTTP 403: ..."}` so the orb reports the failure rather than crashing.

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

The following conditions produce UUID v4 (non-idempotent) student GUIDs, meaning duplicate records may be created on replay:

- Student row has no `date_of_birth` AND no `admissionNumber`
- Both fields are empty/null in the source CSV

Idempotent GUIDs (UUID v5) are generated when either `dob` or `admissionNumber` is present, keyed on `{inst_id}|{course_name}|{name}|{discriminator}` against namespace `f435adac-82f1-4894-beee-0c6128fa9216`.

---

### Known Limitations (T2)

- `GET /api/stu/Course` returns 403 — course IDs must be pre-seeded in `domain/ct.stu.vocabulary.jsonl`.
- `GET /api/auth/Institution` returns 403 — cannot verify institution existence via API.
- `GET /api/stu/Student/flatData` server-side `name` filter does not work; `lookup_existing.py` uses client-side filtering over up to 500 records.
- `GET /api/stu/Etl` returns 403 — ETL job status cannot be polled via API; job progress is tracked only through RabbitMQ ack and S3 artifact presence.
