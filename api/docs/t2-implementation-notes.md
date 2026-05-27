# T2 Implementation Notes — cot1 Executes Against ct-api

## What T2 adds

T1 used `cot1_stub` to generate a mock TAP result. T2 replaces it with a real `cot1` that:

1. Validates the intent against `ct.stu.vocabulary.jsonl`
2. Resolves execution context (inst_id, course_map, term_name)
3. Builds an ETL job list, uploads it to S3, submits the S3 path to RabbitMQ
4. Writes the TAP result packet to the blackboard

`cot1_stub.exs` is retained as a standalone file for eval-check purposes only. The OrbConfig in `at1cmd.exs` now inlines the real cot1 RunConfig.

---

## CT API Auth — Two Headers Required

The API returns `InvalidAccessCodeException` if only `Authorization: Bearer` is sent. A second header is required:

```
AccessCode: {AppId}
```

`AppId` is extracted from the nested JWT claim:

```python
outer_payload = base64.b64decode(token.split(".")[1] + "==")
inner = json.loads(json.loads(outer_payload)["token"])
app_id = inner["AppId"]   # e.g. "00ed8512-2b45-4853-a962-d2423ef61fb1"
inst_id = inner["ClientId"]  # e.g. "0c250000-2425-11e7-89e2-1cbdb9e7fd04"
```

This pattern is in `_auth_headers()` in every gateway script that makes HTTP calls.

---

## CT_API_BASE_URL — No `/api` Suffix

`CT_API_BASE_URL` must be the bare domain: `https://svc.campustrack.net`. All scripts append `/api/...` paths themselves. A URL with a trailing `/api` causes doubled paths and returns 200 HTML (the web app) instead of the API.

---

## UUID v5 Namespace

Student GUIDs are UUID v5 keyed on `{inst_id}|{course_name}|{name}|{discriminator}` against namespace:

```
f435adac-82f1-4894-beee-0c6128fa9216
```

This is a project-specific namespace committed to `build_etl_job.py`. Never substitute the DNS namespace (`6ba7b810-...`) — that would silently produce different GUIDs for the same students.

If a student has neither `dob` nor `admissionNumber`, `build_etl_job.py` falls back to UUID v4 and marks the record as `identity_state: "non_idempotent"`. The gap analysis step surfaces these for operator action.

---

## ETL Pipeline: S3 Then RabbitMQ

The ETL pipeline is:

```
build_etl_job.py  →  upload_etl_to_s3.py  →  submit_to_rmq.py
```

RabbitMQ receives only the S3 path, not the ETL content:

```json
{"title": "etl_run_script", "payload": {"s3_path": "s3://...", "queue": []}, "client_id": "<inst_id>"}
```

Queue: `ct_r_etl_worker` (durable). Library: `pika`.

ETL filename format: `{CT_ENV}_{seq}_{CT_INST_SHORT_CODE}_{acad_year}_students.etl`
Academic year is extracted from `ClientId` in the JWT: `inst_id.split("-")[1]` → `"2425"` for `"0c250000-2425-..."`

S3 key: `{CT_INST_SHORT_CODE}/etls/{filename}`

---

## on_duplicate Behaviour for Direct Mode

`direct_call.py` handles 409 responses per the `on_duplicate` field in `ct.stu.behaviour.jsonl`:

| Value | Behaviour |
|-------|-----------|
| `return_existing_id` | GET list → client-side match by name → return id |
| `ignore` | Return `status: ok` with empty result |
| `fail` | Return `status: failed` |

Both `create_institution` and `create_course` use `return_existing_id` so greenfield runs are idempotent on retry.

---

## Server-Side flatData Name Filter Unavailable

`GET /api/stu/Student/flatData` accepts a `name` query parameter but returns all records regardless. `lookup_existing.py` compensates with client-side case-insensitive filtering over the full result set (up to 500 records per `pageSize`). Confirmed against live BTLCOL data.

---

## Accessible vs. Blocked Endpoints (BTLCOL Token)

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/stu/_Monitor/ping` | 200 | Confirmed working |
| `GET /api/stu/Student` | 200 | Full student list |
| `POST /api/stu/Student/flatData` | 200 | Returns all records (name filter ignored) |
| `GET /api/stu/Course` | 403 | Cannot fetch course list via API |
| `GET /api/auth/Institution` | 403 | Cannot verify institution |
| `POST /api/auth/Institution` | 403 | Greenfield scenario blocked |
| `POST /api/stu/Course` | 403 | Greenfield scenario blocked |
| `GET /api/stu/Etl` | 403 | Cannot poll ETL job status |

Course IDs must be pre-seeded in `domain/ct.stu.vocabulary.jsonl`. Only "SSLC" (`09242481-2425-4f10-9f4a-9a6251465c04`) with sections A and B is known for BTLCOL.

---

## T2 Sample Data

`tenant/data/sample_enrollments_t2.csv` uses the real SSLC course (matches vocabulary). T1's `sample_enrollments.csv` used "Standard I" / "Standard II" which don't exist in ct-api and would produce `unresolved_courses` errors in `resolve_context.py`.

Ravi Agent has no `date_of_birth` and no `admissionNumber` → UUID v4 → `non_idempotent` gap flagged by at1qry. This is intentional and validates the gap analysis path end-to-end.

---

## OrbConfig Change: cot1_stub → cot1

`at1cmd.exs` now inlines the real cot1 RunConfig. Key differences from T1:

- `orb_id` prefix changed from `uc-api-t1-` to `uc-api-t2-`
- `context_strategy: :rolling` on at1cmd replaced with `:full` (all three agents now `:full`)
- CSV input changed from `sample_enrollments.csv` to `sample_enrollments_t2.csv`
- cot1 RunConfig has `max_steps: 30` (ETL pipeline is deeper than the stub)
- `send_message` targets are `cot1_id` and `at1qry_id` (pre-established from `orb_id`)

---

## What T3 Must Know

- `direct_call.py` endpoint list will need updating if token scope expands to include institution/course management.
- The UUID v5 namespace `f435adac-82f1-4894-beee-0c6128fa9216` is permanent — never change it.
- `domain/ct.stu.vocabulary.jsonl` course entries are manually maintained until `GET /api/stu/Course` becomes accessible.
- The greenfield sprint case (`uc_api_agent_t2_greenfield`) documents the intended flow but currently fails at direct-mode steps due to 403 responses.
