# uc-api-agent

Agent-to-agent communication between a tenant dispatcher and an application gateway,
implementing the TAP (Tenancy Agency Protocol). First use case: student enrollment
via the ct.stu API.

Full design: [`docs/uc-api-agent-design.md`](../docs/uc-api-agent-design.md)
Protocol: [`protocol/TAP-v0-design.md`](../protocol/TAP-v0-design.md)

---

## What it does

A tenant operator says: *"Enroll students from this CSV into ct."*

Three agents handle it:

```
at1cmd  →  cot1  →  at1qry
```

- **at1cmd** (tenant) — reads the CSV, packages a TAP intent packet, dispatches to cot1
- **cot1** (gateway) — validates the intent, builds an ETL job, uploads to S3, submits to
  RabbitMQ, notifies at1qry
- **at1qry** (tenant) — receives the result, runs gap analysis, surfaces any data quality issues

at1cmd and at1qry run in the tenant environment. cot1 runs in the application environment.
In T1–T4 all three run together for development.

---

## Structure

```
api/
  tenant/          ← at1cmd, at1qry agents and scripts
  gateway/         ← cot1 agent and scripts
  domain/          ← vocabulary + behaviour JSONL docs
  docs/            ← implementation notes per ticket
  data/            ← sample CSVs (.gitignore excludes real data)
```

---

## Quick start

**Prerequisites:** aetheris harness running in sibling repo (`../aetheris`).

```bash
# 1. Copy and fill in credentials
cp api/.env.example api/.env   # edit with real values

# 2. Confirm ct-api is reachable
source api/.env
python3 api/gateway/scripts/ping_ct.py

# 3. Run Python tests
python3 -m pytest api/tenant/tests/ api/gateway/tests/ -v

# 4. Run T1 plumbing sprint (no credentials needed)
cd ../aetheris
./scripts/sprint.sh uc_api_agent_t1

# 5. Run T2 steady-state sprint (credentials required)
source ../aetheris-agents/api/.env
./scripts/sprint.sh uc_api_agent_t2_steady
```

See [`api/runbook.md`](runbook.md) for full sprint instructions and environment setup.

---

## Status

| Ticket | What it delivers | Status |
|--------|-----------------|--------|
| T1 | TAP plumbing — orb messaging, intent packet, stub gateway | ✅ |
| T2 | Real ct-api execution — ETL via S3 + RabbitMQ, steady-state scenario | ✅ |
| T3 | Skill extraction — second run uses hints from first run | ✅ |
| T4 | Webhook resume — cot1 notifies at1qry via Aetheris HTTP API | ✅ |
| T5 | Durable at1qry state across BEAM restarts (depends on m13) | ⏭ deferred |

**Known gaps:**
- Greenfield scenario (create institution + courses) blocked by 403 on BTLCOL token
- Family detail updates (father/mother/guardian) excluded from ETL pending CT dev team confirmation
- BEAM restart recovery requires re-running the full orb (T5 will fix this)

---

## Domain document

Two JSONL files in `domain/` define what cot1 knows:

- `ct.stu.vocabulary.jsonl` — tenant-visible: intent types, field rules, valid values
- `ct.stu.behaviour.jsonl` — gateway-internal: execution modes, API capabilities, on_duplicate

When courses or institutions change, update `ct.stu.vocabulary.jsonl` and bump the version.
See the design doc for the full record_type reference.

---

## Key files

| File | Purpose |
|------|---------|
| `tenant/agents/at1cmd.exs` | Production OrbConfig (all three agents) |
| `tenant/agents/at1cmd_sprint.exs` | Sprint variant with stable intent/correlation IDs |
| `gateway/agents/cot1.exs` | Standalone cot1 for eval checks |
| `gateway/agents/cot1_stub.exs` | T1 stub — returns mock results without calling ct-api |
| `domain/ct.stu.vocabulary.jsonl` | Intent definitions and valid values |
| `domain/ct.stu.behaviour.jsonl` | Execution steps and API capability mapping |
