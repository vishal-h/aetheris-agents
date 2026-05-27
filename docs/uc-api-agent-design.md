# uc-api-agent — Design Document

**Status:** Pre-implementation. Captures architecture decisions from design session 2026-05-25.
**Depends on:** Aetheris m12 complete, m13 planned
**API:** ct.stu (`CT_API_BASE_URL=https://svc.campustrack.net/api`)

---

## What this is

An agent-to-agent communication system implementing TAP (Tenancy Agency Protocol) for
structured, trusted interaction between a tenant-side agent pair and an application-side
gateway agent. The first use case is student enrollment via the ct.stu API.

The system is not a wrapper around ct-api. It is a protocol layer that lets tenant agents
express intent in their own vocabulary, with the application-side gateway doing the
translation, validation, and execution.

---

## Participants

```
Tenant side                          Application side
────────────────────────────────     ────────────────────────────────
at1cmd  Dispatcher                   cot1  Gateway / Steward
        - stateless, per-run                - API-aware, tenant-aware
        - packages TAP intent               - executes against ct-api
        - fire and forget                   - persistent / checkpointed

at1qry  Collector
        - persistent (m13 T1)
        - receives results
        - gap analysis
        - human escalation

at1hook (deferred — see below)
```

All active participants are Aetheris agents. In T1 (plumbing), all run together.
In production, tenant side and application side run in separate environments.

---

## Responsibility split

| Concern | at1cmd | cot1 |
|---------|--------|------|
| Parse local data (CSV) | ✅ | ✗ |
| Understand user intent | ✅ | ✗ |
| Split multi-intent prompts | ✅ | ✗ |
| Package TAP intent packet | ✅ | ✗ |
| Know ct-api capabilities | ✗ | ✅ |
| Map TAP fields → API DTOs | ✗ | ✅ |
| Know tenant defaults (termName etc.) | ✗ | ✅ |
| Generate GUIDs for new records | ✗ | ✅ |
| Build and submit ETL jobs | ✗ | ✅ |
| Execute direct API calls | ✗ | ✅ |
| Maintain execution context across intents | ✗ | ✅ |
| Post-setup domain doc update | ✗ | ✅ |
| Gap analysis | at1qry | ✅ |
| Human escalation | at1qry | ✗ |
| Domain doc updates, skill sync | at1hook (deferred) | ✅ |

**at1cmd does not know about ct-api.** It knows the user's data and the TAP intent
schema. cot1 owns all API knowledge, tenant configuration, and execution strategy.

---

## TAP intent packet (at1cmd output)

at1cmd produces a TAP intent packet in its own vocabulary — original field names and
values from the source data, not mapped to API format. cot1 does the translation.

```json
{
  "tap_version": "0",
  "message_type": "intent",
  "intent_id": "int-550e8400",
  "correlation_id": "cor-2026-05-t1",
  "seq": 1,
  "depends_on": [],
  "intent_type": "enroll_students",
  "user_intent": "Enroll students from data/enrollments.csv",
  "payload": [
    {
      "name": "Priya Sharma",
      "dob": "2010-06-15",
      "gender": "Female",
      "course": "Standard I",
      "section": "A",
      "roll_no": "1",
      "father": { "name": "Rajesh Sharma", "email": "rajesh.sharma@gmail.com", "mobile": "9876543210" }
    }
  ],
  "flags": [
    { "record": "row_1", "reason": "dob absent from source" }
  ],
  "provenance": {
    "source_file": "data/enrollments.csv",
    "record_count": 1,
    "batch": 1,
    "of": 1
  }
}
```

---

## Multi-intent requests

A single user prompt may express multiple intents:
"upload student data, set up fee structure and send welcome email"

at1cmd splits these into separate TAP intent packets sharing a `correlation_id`.
Each packet carries `seq` and `depends_on` so cot1 can enforce ordering and
skip dependent intents when a prerequisite fails.

```json
{"intent_id": "int-001", "correlation_id": "cor-may-001", "intent_type": "enroll_students", "seq": 1, "depends_on": []}
{"intent_id": "int-002", "correlation_id": "cor-may-001", "intent_type": "setup_fee_structure", "seq": 2, "depends_on": ["int-001"]}
{"intent_id": "int-003", "correlation_id": "cor-may-001", "intent_type": "send_welcome_email", "seq": 3, "depends_on": ["int-001"]}
```

at1qry aggregates results by `correlation_id`. Gap analysis runs across all intents
in the group as a unit.

When source data exceeds `max_batch_size` for an intent, at1cmd splits into multiple
packets under the same `correlation_id`, chaining via `depends_on`:

```json
{"intent_id": "int-001", "correlation_id": "cor-1", "intent_type": "enroll_students",
 "seq": 1, "depends_on": [], "provenance": {"batch": 1, "of": 2, "record_count": 500}}
{"intent_id": "int-002", "correlation_id": "cor-1", "intent_type": "enroll_students",
 "seq": 2, "depends_on": ["int-001"], "provenance": {"batch": 2, "of": 2, "record_count": 147}}
```

Known intent combinations and their confirmation policy are declared in the vocabulary
doc via `intent_combo` records.

---

## Institute scenarios

The system handles two scenarios with the same design — different entry points, not
different code paths.

### Scenario A — New institute (greenfield)

```
intent 1: setup_institution   seq:1  depends_on: []        direct mode
intent 2: setup_courses       seq:2  depends_on: [int-001] direct mode
intent 3: enroll_students     seq:3  depends_on: [int-002] ETL mode
```

cot1 has no prior knowledge of this institute. Execution context threads InstId and
CourseMap forward from setup intents to enrollment. Domain vocabulary doc has no
course lookups yet — populated after setup_courses completes via post-setup update.

setup_institution and setup_courses run in **direct mode** — low-volume, one-time
operations that must return results synchronously so downstream intents can use them.

### Scenario B — Existing institute (steady-state)

```
intent 1: enroll_students
```

JWT carries InstId. Vocabulary doc already has course lookups. Execution context
empty; resolution falls back to vocabulary doc and JWT.

### Hybrid — Existing institute, new courses

```
intent 1: setup_courses       seq:1  depends_on: []        direct mode
intent 2: enroll_students     seq:2  depends_on: [int-001] ETL mode
```

New courses from execution context, existing courses from vocabulary doc. Context
takes precedence.

---

## Field resolution priority

For any field cot1 needs to resolve:

```
1. Execution context        (output of a prior intent in this correlation)
2. Vocabulary doc lookup    (static, published by cot1)
3. JWT claim                (InstId only)
4. Clarification → at1qry  (structured, max 2 rounds)
5. Fail                     (flag record, exclude from execution)
```

This order handles all three scenarios without special-casing.

---

## Execution context threading

cot1 maintains an execution context keyed by `correlation_id` across sequential
intents. Each completed intent may contribute values downstream intents consume.

```
setup_institution result  → context["inst_id"] = "generated-guid"
setup_courses result      → context["course_map"] = {"Standard I": "guid-1", ...}
enroll_students           → reads from context; bypasses vocabulary doc where available
```

Context is in-memory for the duration of the multi-intent run. Not persisted between
separate runs. Known limitation for T2 — see resolved questions.

---

## Post-setup vocabulary doc update

After a successful `setup_courses` run, cot1 updates the vocabulary doc with new
course lookups and publishes the updated version. Subsequent standalone enrollment
runs (Scenario B) can resolve CourseIds from the static doc.

Update trigger: any intent that creates new lookup-resolvable entities. cot1 appends
new `lookup` records and bumps `version` in `meta`.

Push mechanism: at1hook (deferred). For T2: cot1 writes the updated vocabulary doc
directly to `domain/ct.stu.vocabulary.jsonl` as post-execution cleanup.

---

## Execution model

### Pre-execution validation (not mid-execution)

```
cot1 receives intent
  → validate entire batch against vocabulary doc (no API calls)
  → if ambiguities: send ONE structured clarification request to at1qry
  → at1qry validates human response against clarification schema
  → cot1 resumes with resolved context
  → execute full batch (direct or ETL)
  → send result packet to at1qry
```

### Clarification protocol

- Maximum 2 clarification rounds total (valid + invalid responses both consume a round)
- Requests are structured, not free text:
  ```json
  {
    "field": "termName",
    "clarification_type": "select_one",
    "options": ["Annual", "Term 1", "Term 2"],
    "context": "required for all 47 records"
  }
  ```
- at1qry validates human responses before forwarding:
  - `select_one`: value must be in declared `options`
  - `confirm`: must be boolean
  - Invalid response → re-present with error note, round consumed
  - Round limit reached with no valid response → escalate or fail intent with
    `reason: "clarification_unresolved"`
- Human intervention always structured — options presented, not free text
- Clarification goes to at1qry (not at1cmd — at1cmd is already done)

### Pipeline staging enforcement

No ETL job is staged for intent N until all direct-mode intents in N's dependency
chain are confirmed complete. Direct-mode results populate execution context; ETL
job building cannot begin until that context is available.

Valid transition: `direct_confirmed → etl_staged`
Invalid: `direct_in_flight → etl_staged` (prevented by pipeline staging rule)

### Two execution modes

Defined in the behaviour doc, not the vocabulary doc. cot1 chooses based on
`execution` records in `ct.stu.behaviour.jsonl`.

**ETL mode** — bulk write operations:
1. Pre-generate GUIDs for all new records
2. Build ETL job list (one line per API call, all capabilities bundled)
3. Upload ETL file to S3 → receive s3_path
4. Push `{title, s3_path, client_id}` to RabbitMQ queue `"ct_r_etl_worker"`
5. Return result packet: `{job_ref, s3_path, records: [...], status: "queued"}`

**Direct mode** — setup operations and queries:
1. Call ct-api via `http_call`
2. Capture result into execution context if downstream intents need it
3. Return result in result packet

### ETL job format (cot1 internal)

Each line: `METHOD\tENDPOINT\tJSON_PAYLOAD`

```
post\t/api/stu/student\t{"AadharNumber":null,"AdmissionNumber":null,"ApplicationNumber":null,"CourseId":"<course_guid>","CourseName":"SSLC","DOA":"0001-01-01T00:00:00","DOB":"0001-01-01T00:00:00","Email":null,"Gender":0,"Mobile":null,"Name":"Priya Sharma","SecName":"A","StudentId":null,"Branch":"","TermName":"Annual","Id":"<student_guid>","InstId":"<inst_id>"}
```

Field names in the ETL JSON are **PascalCase** (API format), not the CSV's snake_case.
`build_etl_job.py` maps explicitly:

| CSV field | ETL JSON field | Notes |
|-----------|---------------|-------|
| `name` | `Name` | |
| `gender` | `Gender` | integer: 0=Female, 1=Male, 90=Other |
| `course` | `CourseName` | human label |
| resolved CourseId | `CourseId` | GUID from context/vocabulary |
| `section` | `SecName` | |
| `date_of_birth` | `DOB` | ISO8601 or sentinel |
| `date_of_admission` | `DOA` | sentinel when absent |
| `email` | `Email` | |
| `mobile` | `Mobile` | |
| generated GUID | `Id` | UUID v5 or v4 fallback |
| extracted InstId | `InstId` | from JWT claim |
| `branch` | `Branch` | empty string when absent |
| `termName` | `TermName` | defaulted to "Annual" |

GUIDs pre-generated. ETL worker receives complete payloads — no chaining.

### ETL file naming convention

```
{env}_{seq}_{inst_short_code}_{acad_year}_{entity}.etl
dev_05_btlcol_2425_students.etl
```

Academic year extracted from InstId — second group of the UUID:
```python
def acad_year_from_inst_id(inst_id: str) -> str:
    return inst_id.split("-")[1]   # "0c250000-2425-11e7-..." → "2425"
```

S3 path: `s3://{CT_S3_BUCKET}/{inst_short_code}/etls/{filename}.etl`

### RabbitMQ payload (cot1 internal)

```json
{
  "title": "etl_run_script",
  "payload": {
    "s3_path": "s3://s3-btl-ct-test/btlcol/etls/dev_05_btlcol_2425_students.etl",
    "queue": []
  },
  "client_id": "<inst_id>"
}
```

Queue name: `"ct_r_etl_worker"`

### Record identity

New records: UUID v5 from stable fields (see idempotency section).
Existing records: also have `studentId` (human-assigned). Both returned in result packet.

### Missing field handling

`DOB`/`DOA` default to sentinel `"0001-01-01T00:00:00"` when absent. Advisory only.

---

## Domain documents

**The vocabulary doc and behaviour doc are separate files with different audiences.**

The drift of orchestration semantics into a shared document was identified as a
DSL risk. Splitting by audience prevents this:

| Concern | Vocabulary doc | Behaviour doc |
|---------|---------------|---------------|
| Who reads it | at1cmd + cot1 | cot1 only |
| Distributed via TAP handshake | ✅ | ✗ — gateway internal |
| Changes when | Domain changes | System changes |
| Contains | Intents, fields, rules, lookups, combos, max_batch_size | Execution ordering, modes, capabilities, outcomes, pipeline rules |

### `ct.stu.vocabulary.jsonl` — tenant-visible

at1cmd reads this to understand what intents exist, what fields they need, and what
valid values look like. Distributed to tenants during the TAP handshake.

#### record_type values

| record_type | Purpose |
|-------------|---------|
| `meta` | File header — domain, version, intent count |
| `section` | Intent group boundary marker |
| `intent` | Intent definition — requires, optional, max_batch_size |
| `field` | Lightweight type definition |
| `rule` | Conditional validation rule |
| `lookup` | Valid values for a field |
| `intent_combo` | Multi-intent combinations and confirmation policy |

#### Example

```jsonl
{"record_type": "meta", "domain": "ct.stu", "version": "1", "published_at": "2026-05-25", "intent_count": 3, "gateway": "cot1.stu"}

{"record_type": "section", "intent": "setup_institution", "seq": 1}
{"record_type": "intent", "name": "setup_institution", "description": "Create a new institution", "requires": ["name"], "optional": ["address", "email", "phone"], "max_batch_size": 1}

{"record_type": "section", "intent": "setup_courses", "seq": 2}
{"record_type": "intent", "name": "setup_courses", "description": "Create courses for an institution", "requires": ["courseName", "termName"], "optional": ["section"], "max_batch_size": 50}

{"record_type": "section", "intent": "enroll_students", "seq": 3}
{"record_type": "intent", "name": "enroll_students", "description": "Create new student records", "requires": ["name", "gender", "courseName", "secName", "termName"], "optional": ["dob", "doa", "email", "mobile", "rollNo", "admissionNumber"], "max_batch_size": 500}
{"record_type": "field", "name": "dob", "type": "date", "format": "ISO8601", "if_missing": "use_sentinel", "sentinel": "0001-01-01T00:00:00", "advisory_only": true}
{"record_type": "field", "name": "doa", "type": "date", "format": "ISO8601", "if_missing": "use_sentinel", "sentinel": "0001-01-01T00:00:00", "advisory_only": true}
{"record_type": "field", "name": "gender", "type": "enum", "clarify_from": "lookup.gender"}
{"record_type": "field", "name": "termName", "type": "string"}
{"record_type": "rule", "intent": "enroll_students", "field": "termName", "if_missing": "use_default", "default_from": "current_term", "clarify_as": "select_one", "clarify_from": "lookup.terms"}
{"record_type": "rule", "intent": "enroll_students", "if": {"field": "fatherName", "present": true}, "then": {"require_one_of": ["fatherMobile", "fatherEmail"]}}
{"record_type": "rule", "intent": "enroll_students", "if": {"field": "guardianName", "present": true}, "then": {"require": ["guardianGender"]}}
{"record_type": "lookup", "name": "terms", "id": "annual", "label": "Annual", "current": true}
{"record_type": "lookup", "name": "terms", "id": "t1-2026", "label": "Term 1 2026", "current": false}
{"record_type": "lookup", "name": "gender", "id": "0", "label": "Female"}
{"record_type": "lookup", "name": "gender", "id": "1", "label": "Male"}
{"record_type": "lookup", "name": "gender", "id": "90", "label": "Other"}
{"record_type": "lookup", "name": "courses", "id": "a1b2c3d4-e5f6-...", "label": "Standard I", "active": true}
{"record_type": "lookup", "name": "sections", "course_id": "a1b2c3d4-e5f6-...", "section": "A"}

{"record_type": "intent_combo", "intents": ["setup_institution", "setup_courses", "enroll_students"], "requires_confirmation": true}
{"record_type": "intent_combo", "intents": ["enroll_students", "send_welcome_email"], "requires_confirmation": false}
{"record_type": "intent_combo", "intents": ["enroll_students", "setup_fee_structure"], "requires_confirmation": true}
```

### `ct.stu.behaviour.jsonl` — gateway internal

cot1 reads this to know how to execute each intent. Never sent to tenants. Changes
when the system changes, independently of domain vocabulary changes.

#### record_type values

| record_type | Purpose |
|-------------|---------|
| `meta` | File header — domain, version |
| `section` | Intent group boundary marker |
| `execution` | Capability-based execution step with mode and duplicate handling |
| `outcome` | Success criteria and context contributions |

#### `on_duplicate` values (direct-mode only)

| Value | Behaviour |
|-------|-----------|
| `return_existing_id` | 409 → query for existing record → extract ID → push to context. Safe for replay. |
| `fail` | 409 → fail the intent, surface reason to at1qry. Use when duplicates are never acceptable. |
| `ignore` | 409 → treat as success, no ID extraction needed. Use for idempotent writes with no downstream dependency. |

ETL-mode capabilities do not carry `on_duplicate` — student-level deduplication
is handled by deterministic GUIDs and the job idempotency key.

#### Example

```jsonl
{"record_type": "meta", "domain": "ct.stu.behaviour", "version": "1", "published_at": "2026-05-25"}

{"record_type": "section", "intent": "setup_institution", "seq": 1}
{"record_type": "execution", "intent": "setup_institution", "step": 1, "capability": "create_institution", "mode": "direct", "on_duplicate": "return_existing_id"}
{"record_type": "outcome", "intent": "setup_institution", "success_when": "inst_id_returned", "contributes_to_context": ["inst_id"]}

{"record_type": "section", "intent": "setup_courses", "seq": 2}
{"record_type": "execution", "intent": "setup_courses", "step": 1, "capability": "create_course", "mode": "direct", "on_duplicate": "return_existing_id"}
{"record_type": "outcome", "intent": "setup_courses", "success_when": "all_courses_created", "contributes_to_context": ["course_map"]}

{"record_type": "section", "intent": "enroll_students", "seq": 3}
{"record_type": "execution", "intent": "enroll_students", "step": 1, "capability": "create_student", "mode": "etl", "fields": "core"}
{"record_type": "execution", "intent": "enroll_students", "step": 2, "capability": "update_father_details", "mode": "etl", "when": {"field": "fatherName", "present": true}}
{"record_type": "execution", "intent": "enroll_students", "step": 3, "capability": "update_mother_details", "mode": "etl", "when": {"field": "motherName", "present": true}}
{"record_type": "execution", "intent": "enroll_students", "step": 4, "capability": "update_guardian_details", "mode": "etl", "when": {"field": "guardianName", "present": true}}
{"record_type": "execution", "intent": "enroll_students", "step": 5, "capability": "set_roll_no", "mode": "etl", "when": {"field": "rollNo", "present": true}}
{"record_type": "outcome", "intent": "enroll_students", "success_when": "all_records_queued", "partial_success_when": "at_least_one_queued"}
```

### Versioning

Vocabulary doc: distributed via TAP handshake. at1cmd re-fetches when `domain_version`
in the handshake response differs from its cached version.

Behaviour doc: gateway internal. Versioned independently. No tenant notification needed.

Both docs bump `version` in their `meta` record on any change.

---

## Multi-domain routing

The architecture is domain-agnostic. The container (TAP message format, JSONL
record_type structure, participant roles, execution model, lifecycle states,
idempotency mechanisms) works identically for ct.fees, ct.calendar, or any future
domain. Only the content inside the container changes per domain.

### What changes per domain

Thin, domain-specific layers over a generic structure:

```
ct.fees.vocabulary.jsonl    → collect_fees, setup_fee_structure, waive_fee
ct.fees.behaviour.jsonl     → create_fee_record (direct), process_payment (direct),
                               send_receipt (etl)

ct.calendar.vocabulary.jsonl → create_event, schedule_class, book_resource
ct.calendar.behaviour.jsonl  → create_calendar_entry (direct), notify_participants (etl)
```

Same at1cmd, same at1qry, same execution model. Different vocabulary docs, different
behaviour docs, different agent system prompts, different CSV parsers per domain.

### Gateway routing via `meta.gateway`

at1cmd reads the `gateway` field from the vocabulary doc `meta` record and routes
the TAP intent to the named gateway. It does not know about ct-api internals — it
knows only which gateway handles which domain.

```jsonl
{"record_type": "meta", "domain": "ct.stu",      "gateway": "cot1.stu",      ...}
{"record_type": "meta", "domain": "ct.fees",     "gateway": "cot1.fees",     ...}
{"record_type": "meta", "domain": "ct.calendar", "gateway": "cot1.calendar", ...}
```

The TAP capability manifest (TAP handshake response) declares which domains are
available to a given tenant. at1cmd fetches only the vocabulary docs for its
enabled domains.

### One cot1 per domain vs. one for all (deferred)

For a small number of domains (2–4), one cot1 per domain is clean — independent
versioning, independent deployment. For a full ERP with many domains, a single
cot1 routing internally may be preferable. The `gateway` field keeps both options
open — whether `"cot1.stu"` and `"cot1.fees"` are separate processes or named
routes within a single process is a deployment decision, invisible to at1cmd.

Not worth solving now. Revisit when the second domain is being built.

### Script reusability across domains

| Script | Generic? | Notes |
|--------|----------|-------|
| `gap_analysis.py` | ✅ fully | Works for any domain — no domain knowledge |
| `package_intent.py` | ✅ mostly | Generic if it reads field mapping from vocabulary doc |
| `parse_csv.py` | ⚠ thin layer | One per domain — knows source CSV columns |
| `build_etl_job.py` | ⚠ thin layer | One per domain — knows ETL format for that API |

Target: make `package_intent.py` and `gap_analysis.py` genuinely reusable shared
utilities. `parse_csv.py` and `build_etl_job.py` are thin domain-specific adapters.

---

## Intent lifecycle states

### State machine

```
[before pending] ──→ skipped    depends_on not met; never enters pending
pending          ──→ validated  passed pre-execution validation
pending          ──→ failed     validation error
validated        ──→ queued     ETL job submitted to RabbitMQ
validated        ──→ failed     submission error
queued           ──→ confirmed  ETL worker completed (future — via at1hook)
queued           ──→ failed     ETL error (future)
```

### State definitions

| State | Terminal | Meaning |
|-------|----------|---------|
| `pending` | No | Intent received, validation not yet run |
| `validated` | No | Passed validation, ready to execute |
| `queued` | No | ETL job submitted, worker processing |
| `confirmed` | Yes | ETL worker completed (future, via at1hook) |
| `failed` | Yes | Error at any stage — carries `reason` and `stage` |
| `skipped` | Yes | depends_on prerequisite failed or skipped |

at1qry runs gap analysis only when all intents in a correlation reach terminal state.

### Result packet

```json
{
  "correlation_id": "cor-may-001",
  "intents": [
    {
      "intent_id": "int-001",
      "intent_type": "setup_institution",
      "status": "failed",
      "stage": "validation",
      "reason": "name field missing"
    },
    {
      "intent_id": "int-002",
      "intent_type": "setup_courses",
      "status": "skipped",
      "reason": "depends_on int-001 failed"
    },
    {
      "intent_id": "int-003",
      "intent_type": "enroll_students",
      "status": "skipped",
      "reason": "depends_on int-002 skipped"
    }
  ]
}
```

---

## Idempotency — separated concerns

| Concern | Mechanism | T2 status |
|---------|-----------|-----------|
| Student identity | UUID v5 from stable student fields | ✅ implemented |
| Queue dedupe | Job idempotency key passed to RabbitMQ | ✅ simple addition |
| Intent replay detection | Intent fingerprint (hash of correlation_id + intent_type + payload) | ⏭ deferred T3+ |
| ETL exactly-once | Worker-level replay protection | ⚠ outside our control |

### Student identity — UUID v5

```python
import uuid

# Fixed namespace — generate once with uuid.uuid4(), commit, never change
CT_STU_NAMESPACE = uuid.UUID("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

def student_guid(inst_id: str, course_name: str, student_name: str,
                 dob: str, admission_number: str | None) -> tuple[str, bool]:
    sentinel = "0001-01-01T00:00:00"
    if admission_number:
        discriminator = admission_number.strip()
        idempotent = True
    elif dob != sentinel:
        discriminator = dob.strip()
        idempotent = True
    else:
        return str(uuid.uuid4()), False  # flag as non_idempotent

    name = "|".join([
        inst_id.strip().lower(),
        course_name.strip().lower(),
        student_name.strip().lower(),
        discriminator
    ])
    return str(uuid.uuid5(CT_STU_NAMESPACE, name)), True
```

Namespace must be stable. Changing it invalidates all previously generated GUIDs.

### Deduplication guard for non-idempotent records

Before assigning a random v4 UUID, cot1 queries ct-api to check if a matching
student already exists. If found, use their existing GUID.

```
non_idempotent record detected
  → direct API call: search by name + courseName + secName
  → found:     use existing GUID, status: "matched_existing"
  → not found: assign random v4, non_idempotent: true in result packet
  → search unavailable: assign random v4, flag gap
```

**Conditional on ct-api search capability.** Verify in T2 that
`POST /api/stu/Student/flatData` or `POST /api/stu/Student/getFilters` supports
reliable name + course lookup. If not, document the gap and accept random v4.

Three identity states in the result packet:

| State | Meaning |
|-------|---------|
| `deterministic` | UUID v5 — fully idempotent |
| `matched_existing` | Found in ct-api — safe, no duplicate |
| `non_idempotent` | Random v4 — tenant must fix source data |

### Queue dedupe — job idempotency key

```python
import hashlib, json

def job_idempotency_key(intent: dict) -> str:
    stable = {
        "correlation_id": intent["correlation_id"],
        "intent_type":    intent["intent_type"],
        "payload":        intent["payload"]
    }
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True).encode()
    ).hexdigest()[:64]
```

Passed to RabbitMQ on submission. Deduplicates within RabbitMQ's deduplication
window. Complements student identity GUIDs — does not replace them.

### Intent replay detection (deferred T3+)

Requires persisting `{intent_fingerprint → result}` in cot1. Workflow engine
territory. Known gap for T2: deterministic GUIDs + job idempotency key cover the
common cases. Outside the RabbitMQ deduplication window, a retried intent may
submit a second job — ETL worker processes it but deterministic GUIDs mean the
outcome is the same.

---

## Natural language → structured progression

| Run | Mode | at1cmd behaviour |
|-----|------|-----------------|
| First | Fully natural | LLM interprets intent, maps to TAP vocabulary |
| Second | Semi-structured | Skill extracted from first run |
| Recurring | Structured | Known intent type, known field mapping |
| Scheduled | Fully automated | m13 scheduler; no human input per run |

Skill extraction after a successful run (T3). Human intervention always structured.

---

## at1hook (deferred)

- at1qry: run-scoped messages (results, clarifications)
- at1hook: tenant-scoped messages (vocabulary doc updates, skill sync, ETL completion
  callbacks, system notifications, third-party webhooks)

Build trigger: T3 or T4, when cot1 starts pushing proactively.

---

## Persistence

at1cmd is stateless. at1qry is persistent via m13:
- m13 T1: checkpoint/resume — survives BEAM restarts
- m13 T3: webhook trigger — cot1 POSTs to `/api/runs/{run_id}/resume`; at1qry
  wakes, processes, exits

Note: m13 T3 `inject_message` must satisfy a live `wait_for_event` condition —
verify during m13 T3 implementation.

---

## Delivery sequence

```
T1  TAP plumbing — orb messaging, intent packet format, basic flow (no real API calls)
T2  cot1 executes against ct-api; vocabulary + behaviour docs; pre-execution
    validation; ETL + direct modes; execution context threading; both scenarios
T3  Skill extraction; structured clarification; second-run uses skill
T4  at1qry persistence via m13; full async round-trip; webhook resume
T5  BEAM durability — resume_from_checkpoint re-establishes message_received waits
```

T1 does not require m13. T4 depends on m13 T1 + T3. T5 depends on T4.

---

## Execution sequences

### T4 — Normal webhook flow

```mermaid
sequenceDiagram
    participant at1cmd
    participant Blackboard
    participant cot1
    participant S3
    participant RabbitMQ
    participant AetherisAPI as Aetheris API
    participant at1qry

    %% Flow
    at1cmd->>Blackboard: write tap:intent:{id}
    at1cmd->>cot1: send_message(intent_id)

    cot1->>cot1: wait_for_event → message_received
    cot1->>Blackboard: read tap:intent:{id}

    cot1->>S3: upload ETL file
    cot1->>RabbitMQ: push job (job_ref)
    cot1->>Blackboard: write tap:result:{id}

    cot1->>AetherisAPI: POST /api/runs/{run_id}/resume
    Note over cot1,AetherisAPI: Primary path<br/>Unblocks at1qry via WaitRegistry.notify

    cot1->>at1qry: send_message(intent_id, fallback)

    at1qry->>at1qry: wait_for_event → message_received (unblocked)
    at1qry->>Blackboard: read tap:result:{id}
    at1qry->>at1qry: gap_analysis → report
```

### T5 — BEAM restart recovery

```mermaid
sequenceDiagram
    participant at1qry
    participant Store as SQLite Store
    participant Application
    participant WaitRegistry
    participant cot1
    participant AetherisAPI as Aetheris API

    %% Initial wait and checkpoint
    at1qry->>at1qry: wait_for_event(message_received)
    at1qry->>Store: save_checkpoint(wait_condition: message_received)

    %% Crash & Restart
    Note over at1qry, Application: BEAM process killed
    Note over at1qry, Application: BEAM process restarted

    Application->>Store: scan for :running checkpoints
    Application->>at1qry: resume_from_checkpoint()

    %% Re-registration
    at1qry->>WaitRegistry: register({:message_received, run_id})
    Note over at1qry: run status → :running<br/>Re-enters wait loop

    %% Resume from external trigger
    cot1->>AetherisAPI: POST /api/runs/{run_id}/resume
    AetherisAPI->>WaitRegistry: notify({:message_received, run_id})
    WaitRegistry->>at1qry: {:resume, :message_received, payload}

    at1qry->>at1qry: gap_analysis → done
```

---

## Auth and environment

**ct-api:**
```
CT_API_BASE_URL=https://svc.campustrack.net    ← no /api suffix
CT_API_TOKEN=<jwt>                              ← Authorization: Bearer <token>
```

**AWS S3:**
```
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
CT_S3_BUCKET=s3-btl-ct-test                    ← test bucket; prod bucket separate
CT_S3_REGION=ap-south-1
CT_INST_SHORT_CODE=btlcol                       ← 6-letter institute code (SMS id)
CT_ENV=dev                                      ← dev | prod; used in ETL filename
```

**RabbitMQ:**
```
CT_RABBITMQ_URL=amqp://user:pass@host:5672/vhost
```

Token held by cot1. at1cmd never holds credentials. Token lifetime days/months
via internal service account. No mid-run refresh needed.

---

## Repository structure

```
uc-api-agent/
  tenant/                         ← runs in tenant environment
    agents/
      at1cmd.exs                  ← dispatcher
      at1qry.exs                  ← collector (persistent)
    scripts/
      parse_csv.py                ← CSV → normalised rows
      package_intent.py           ← rows + user_intent → TAP intent JSON
      gap_analysis.py             ← TAP result → gap report JSON
    tests/
      conftest.py
      test_parse_csv.py
      test_package_intent.py
      test_gap_analysis.py
    data/
      sample_enrollments.csv      ← committed (anonymised)
      .gitignore                  ← excludes real data

  gateway/                        ← runs in application environment
    agents/
      cot1.exs                    ← gateway / steward
      cot1_stub.exs               ← T1 stub for plumbing tests
    scripts/
      validate_intent.py          ← TAP intent + vocabulary doc → validation report
      build_etl_job.py            ← TAP intent + context → ETL job list (PascalCase)
      upload_etl_to_s3.py         ← ETL job list → S3 file → s3_path
      submit_to_rmq.py            ← s3_path + inst_id → RabbitMQ → job_ref
      direct_call.py              ← single direct-mode API call with on_duplicate
      lookup_existing.py          ← deduplication guard: search ct-api by name+course
      resolve_context.py          ← execution context threading helpers
      stub_cot1.py                ← T1: intent → mock TAP result JSON
      ping_ct.py                  ← connectivity check
    tests/
      conftest.py
      test_validate_intent.py
      test_build_etl_job.py
      test_upload_etl_to_s3.py
      test_submit_to_rmq.py
      test_resolve_context.py
      test_lookup_existing.py
      test_stub_cot1.py

  domain/                         ← owned by gateway
    ct.stu.vocabulary.jsonl       ← tenant-visible; distributed via TAP handshake
    ct.stu.behaviour.jsonl        ← gateway internal; never sent to tenants

  docs/
    uc-api-agent-design.md        ← this document
  milestone.md
  README.md
  runbook.md
```

---

## Resolved questions

**Record identity**
Pre-generated GUIDs as `Id` in ETL payloads. Existing records also have `studentId`
(human-assigned). Both returned in result packet.

**Throughput and latency**
No rate limiting. RabbitMQ queue. cot1 returns `status: "queued"` immediately.
Confirmation is a future at1hook signal.

**JWT token lifetime**
Days/months. No mid-run refresh needed.

**termName default**
`"Annual"` when absent from source and no `current: true` term in vocabulary doc.

**GenderEnum**
`0 = Female`, `1 = Male`, `90 = Other`. Opposite of initial assumption — corrected
throughout.

**DOB/DOA sentinel**
`"0001-01-01T00:00:00"` when absent. Advisory only — enrollment proceeds.

**RabbitMQ job reference**
Returns a job_ref. Included in result packet for at1qry tracking.

**InstId source**
JWT claim, decoded at cot1 run start. Falls back to execution context when
setup_institution ran earlier in the same correlation.

**CourseId resolution**
Execution context first (after setup_courses), then vocabulary doc lookups.
Context takes precedence. Unresolvable CourseName → validation failure, record
flagged and excluded.

**`depends_on` semantics**
Skip dependents on prerequisite failure. Report partial results per intent.
Fail-fast on entire correlation is too aggressive for real institutional data.

**ETL job build sequence**

```
1. Decode JWT → extract InstId + acad_year (cached)
2. Validate entire batch against vocabulary doc
3. Resolve CourseIds: execution context → vocabulary doc lookups
4. Flag unresolvable records; send clarifications if needed (max 2 rounds)
5. Pre-generate GUIDs (deterministic where possible, guarded random v4 fallback)
6. Build ETL job list (PascalCase field names, per field mapping table)
7. Generate ETL filename: {CT_ENV}_{seq}_{CT_INST_SHORT_CODE}_{acad_year}_students.etl
8. Upload ETL file to s3://{CT_S3_BUCKET}/{CT_INST_SHORT_CODE}/etls/{filename}
9. Push to RabbitMQ queue "ct_r_etl_worker":
     {title: "etl_run_script", payload: {s3_path, queue: []}, client_id: inst_id}
10. Return result packet: s3_path + job_ref + per-record {guid, name, identity_state, status}
```

**Execution context loss on crash (known limitation, T2)**
Context is in-memory. Crash between setup_courses and enroll_students loses the
CourseMap. Recovery: operator re-runs the full correlation. m13 T1 checkpoint/resume
fixes this in T4.

**T2 recovery path — operator replay procedure**

Re-running the full correlation is safe only if direct-mode capabilities are
idempotent. `on_duplicate: "return_existing_id"` in the behaviour doc makes this
explicit: cot1 catches 409 responses, retrieves the existing record's ID, and pushes
it into execution context exactly as if setup had just succeeded.

Before replaying a failed greenfield correlation:

```
1. Confirm connectivity:
     GET /api/stu/_Monitor/ping → expect 200

2. Check institution state:
     If setup_institution failed before completing → no cleanup needed, re-run
     If setup_institution succeeded → cot1 will receive 409, extract existing
     InstId via on_duplicate: return_existing_id, carry forward automatically

3. Check course state:
     If setup_courses failed before completing → no cleanup needed, re-run
     If some courses were created → cot1 will receive 409 per existing course,
     extract existing CourseIds, carry forward automatically

4. If ct-api does NOT support graceful 409 for a capability (no search endpoint,
   creates duplicates silently):
     → Manual database cleanup required before replay
     → Document the specific capability in the T2 runbook under
       "Non-idempotent capabilities requiring manual cleanup"
     → Do not re-run until cleanup is confirmed

5. Re-run using the same correlation_id and identical intent payloads
   (same correlation_id ensures at1qry aggregates correctly)
```

Capabilities where `on_duplicate: "return_existing_id"` requires a search endpoint:
verify `POST /api/stu/Student/flatData` or `POST /api/stu/Student/getFilters`
supports lookup by name + course in T2. If not available, downgrade to
`on_duplicate: "fail"` and document as requiring manual cleanup before replay.

**ETL failure semantics (T2)**
Submission fails → `status: "failed"` in result packet, no retry. Fresh at1cmd
run is the recovery path. Dead-letter queue handling deferred.
