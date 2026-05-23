# TAP — Tenancy Agency Protocol

**Tap in.**
*Intelligent flow across trust boundaries.*

---

## Status

v0 — Design. Pre-implementation. All names, schemas, and flows are provisional.

---

## What is TAP?

TAP is a protocol for structured, trusted, tenant-scoped communication
between autonomous agents across organisational boundaries.

It defines how a tenant-side agent pair communicates with an
application-side tenant gateway — exchanging structured intent,
receiving aggregated results, learning over time — without either
side knowing the other's internal implementation.

TAP is not an API specification. It is a protocol for agent-to-agent
interaction that sits above the transport layer and below the
application domain.

---

## Core principles

**Tenancy.** Every connection is scoped to a specific tenant. `cot1`
serves T1 exclusively. `cot2` serves T2. There is no cross-tenant
communication, no shared state, no capability bleed between tenants.

**Agency.** Agents act independently, make decisions, and learn from
outcomes. TAP does not prescribe what agents do — it prescribes how
they communicate. The intelligence is in the agents, not the protocol.

**Opacity.** The tenant side does not know how the application routes
or executes intent internally. The application side does not know how
the tenant produces or interprets intent. Each side owns its own
implementation.

**Portability.** A tenant agent implementing TAP can connect to any
application that implements TAP. The protocol is the contract — not
the application's internal API.

**Progressive autonomy.** Early runs are supervised. Trust is earned
through successful exchanges. Approval gates thin over time as both
sides accumulate learned patterns.

---

## Participants

### Tenant side (T1 infrastructure)

**`at1cmd` — Tenant Dispatcher**
- Reads structured data from local filesystem
- Reconciles data with user intent using a local or small model
- Packages intent packets and dispatches to `cot1`
- Stateless between dispatches — fires and moves on
- Short-lived: spawned per run, terminates on completion

**`at1qry` — Tenant Collector**
- Receives result packets from `cot1` asynchronously
- Maintains correlation state across multiple dispatches
- Detects partial completion and gaps
- Suggests or initiates follow-up actions
- Updates tenant-side skill store
- Escalates to human when required
- **Persistent** — long-lived, configurable lifetime

### Application side (C infrastructure)

**`cot1` — Tenant Gateway (tenant-scoped)**
- One instance per tenant — `cot1` for T1, `cot2` for T2
- Holds T1's contract, field mappings, approval thresholds, history
- Receives intent from `at1cmd`, routes internally to `cat1`/`bat1`
- Aggregates internal results before surfacing to tenant
- Returns consolidated result packets to `at1qry`
- Uses frontier model — most complex reasoning in the system
- **Persistent** — lives as long as the tenant relationship

**`cat1`, `bat1` — Application Workers**
- Internal to the application — invisible to the tenant
- Each handles a specific domain or capability
- Report results to `cot1`, not directly to the tenant
- Implementation detail of the application

---

## Topology

```
Tenant T1 infrastructure          Application C infrastructure
─────────────────────────         ──────────────────────────────────
                                  
User prompt                       
    ↓                             
at1cmd                            
  reconcile (small model)         
  package intent                  
    ↓                             
    ──── TAP intent packet ──────→ cot1
                                      ↓
                                    route + decompose
                                  cat1    bat1    ...
                                      ↓     ↓
                                    execute execute
                                      ↓     ↓
                                    cot1 aggregates
                                      ↓
at1qry  ←─── TAP result packet ───────
  aggregate
  gap analysis
  skill update
  escalate if needed
```

No cross-tenant communication. `cot2` (for T2) is a completely
separate instance with no visibility into T1's intents or results.

---

## Message types

### 1. Handshake

Initiated by `at1cmd` on first connection or credential refresh.

**Request (at1cmd → cot1):**
```json
{
  "tap_version":   "0",
  "message_type":  "handshake_request",
  "tenant_id":     "t1",
  "agent_id":      "at1cmd",
  "timestamp":     "2026-05-22T10:00:00Z",
  "credentials":   { "type": "jwt", "token": "..." }
}
```

**Response (cot1 → at1cmd):**
```json
{
  "tap_version":   "0",
  "message_type":  "handshake_response",
  "tenant_id":     "t1",
  "gateway_id":    "cot1",
  "schema_version": "1.2",
  "ttl_seconds":   86400,
  "capability_manifest": {
    "intent_types": ["enroll_students", "update_records", "query_status"],
    "batch_limit":  100,
    "rate_limit":   { "requests_per_minute": 60 },
    "approval_required_above": { "enroll_students": 50 },
    "reporter":     "cot1"
  }
}
```

The capability manifest is cached by `at1cmd` until TTL expires or
`schema_version` changes. Re-handshake on either condition.

---

### 2. Intent Packet

Sent by `at1cmd` to `cot1` after reconciliation.

```json
{
  "tap_version":    "0",
  "message_type":   "intent",
  "intent_id":      "int-550e8400-e29b",
  "correlation_id": "cor-2026-05-t1",
  "from":           "at1cmd",
  "to":             "cot1",
  "tenant_id":      "t1",
  "timestamp":      "2026-05-22T10:01:00Z",
  "intent_type":    "enroll_students",
  "payload":        [ ... ],
  "user_intent":    "Enroll the new students from this month's CSV",
  "confidence":     0.92,
  "flags": [
    { "record": "STU-047", "reason": "missing email field" }
  ],
  "provenance": {
    "source_file":    "payroll-2026-05.csv",
    "record_count":   47,
    "validated_at":   "2026-05-22T09:58:00Z",
    "model_used":     "local-small-v2"
  },
  "requires_approval": false
}
```

`confidence` is the reconciliation model's self-assessment. `cot1`
uses this as a routing signal — low confidence or novel intent type
may trigger human approval regardless of batch size.

`correlation_id` is shared across all intent packets that belong to
the same logical operation. Used by `at1qry` to aggregate results.

---

### 3. Acknowledgement

Sent by `cot1` immediately on receipt.

```json
{
  "tap_version":   "0",
  "message_type":  "acknowledgement",
  "intent_id":     "int-550e8400-e29b",
  "correlation_id":"cor-2026-05-t1",
  "status":        "accepted",
  "requires_approval": false,
  "estimated_completion_ms": 5000
}
```

`status` values: `accepted`, `queued_for_approval`, `rejected`.

Rejected intents include a `reason` field and never proceed to
execution. `at1qry` handles rejected intents as a gap.

---

### 4. Result Packet

Sent by `cot1` to `at1qry` on completion or partial completion.

```json
{
  "tap_version":    "0",
  "message_type":   "result",
  "intent_id":      "int-550e8400-e29b",
  "correlation_id": "cor-2026-05-t1",
  "from":           "cot1",
  "to":             "at1qry",
  "tenant_id":      "t1",
  "timestamp":      "2026-05-22T10:01:06Z",
  "status":         "partial",
  "summary": {
    "total":     47,
    "succeeded": 45,
    "skipped":   2,
    "failed":    0
  },
  "executed": [
    { "record": "STU-001", "action": "enrolled", "app_id": "APP-9001" }
  ],
  "skipped": [
    { "record": "STU-012", "reason": "duplicate_id" },
    { "record": "STU-031", "reason": "course_not_found" }
  ],
  "flags": [
    {
      "record":    "STU-012",
      "suggested": "re-submit with dedup_override: true",
      "requires_human": false
    }
  ],
  "contributors": ["cat1"],
  "reporter":     "cot1",
  "pending_contributors": []
}
```

`status` values: `done`, `partial`, `pending_contributor`, `rejected`.

`flags` carry `cot1`'s suggestions for gap resolution. `at1qry`
uses these as inputs to its own gap analysis — it may accept,
modify, or override the suggestion.

---

### 5. Skill Sync (optional)

Post-result exchange for mutual learning. Either side may initiate.

```json
{
  "tap_version":   "0",
  "message_type":  "skill_sync",
  "correlation_id":"cor-2026-05-t1",
  "from":          "cot1",
  "to":            "at1qry",
  "tenant_id":     "t1",
  "learned": [
    {
      "pattern":     "duplicate_id on enroll_students",
      "resolution":  "dedup_override: true resolves in 100% of cases",
      "confidence":  0.98
    }
  ]
}
```

`at1qry` incorporates learned patterns into the tenant skill store.
Future `at1cmd` runs are injected with these skills, reducing
escalation frequency over time.

---

### 6. Revocation

Either side may terminate the trust relationship.

```json
{
  "tap_version":  "0",
  "message_type": "revocation",
  "from":         "cot1",
  "tenant_id":    "t1",
  "reason":       "contract_expired",
  "effective_at": "2026-06-01T00:00:00Z"
}
```

On receipt of revocation, the receiving side ceases communication
and invalidates cached credentials and capability manifests.

---

## Approval gates

Both sides may require human approval. Gates are independent.

**Tenant side (`at1cmd`):**
- Configured per intent type and volume threshold
- `at1cmd` pauses before dispatch, awaits human confirmation
- Uses Aetheris `ask_human` + checkpoint resume

**Application side (`cot1`):**
- Declared in capability manifest (`approval_required_above`)
- `cot1` queues the intent, notifies designated human
- Returns `acknowledgement.status: queued_for_approval`
- Proceeds on approval, returns `rejected` on denial

**Progressive thinning:**
Both gates thin over time as approved patterns accumulate in the
skill store. The human becomes an exception handler, not a
checkpoint for every operation.

---

## Trust and transport

**Transport:** HTTP/HTTPS (default), WebSocket for conversational
exchanges, Erlang distribution for trusted same-cluster deployments.

**Authentication:** JWT (default) or API key. Credentials scoped to
the tenant — `at1cmd`'s credentials cannot reach `cot2`.

**Integrity:** Intent and result packets are signed. `cot1` rejects
unsigned or invalid packets. Signature verification is the first
check on receipt.

**Isolation:** `cot1` and `cot2` share no state. Tenant data never
crosses tenant boundaries at any layer.

---

## Model tiers

| Agent | Model tier | Reason |
|-------|-----------|--------|
| `at1cmd` reconciliation | Local / small | Structured output, cost-sensitive, tenant-controlled |
| `at1cmd` judge | Small–medium | Pattern matching against known approvals |
| `at1qry` | Medium–frontier | Gap analysis, inference, recommendation |
| `cot1` | Frontier | Complex routing, error interpretation, domain knowledge |
| `cat1`, `bat1` | Frontier | Actual API execution work |

Tenants without frontier budget use smaller models on the tenant
side. Frontier cost is incurred at the application side (`cot1`)
which the application operator controls.

---

## Progressive autonomy arc

```
Phase 1 — Supervised
  Both approval gates active.
  Almost everything escalates to human.
  Trust is being established.
  Skill store is empty.

Phase 2 — Selective escalation
  Known patterns execute without approval.
  Novel intent types or low-confidence packets escalate.
  Skill store accumulates approved patterns.
  Gates thin on both sides independently.

Phase 3 — Autonomous
  Both agents act confidently on established patterns.
  Human approval is exception handling, not standard flow.
  Post-run report replaces mid-run escalation.
  Skill sync keeps both sides current.
```

The transition between phases is not manual — it emerges from
skill extraction and confidence thresholds, both configurable.

---

## Open questions (to resolve in v0.1)

1. **Intuitive names.** `at1cmd`, `at1qry`, `cot1` are working names.
   Candidates: Envoy/Consul/Steward or Dispatcher/Collector/Gateway.
   Decision deferred to v0.1 when roles are fully stable.

2. **Schema versioning.** When `cot1` upgrades its capability manifest
   schema, how does `at1cmd` detect and handle the mismatch? Options:
   strict reject, graceful degradation, re-handshake trigger.

3. **Multi-application fan-out from tenant side.** Can `at1cmd` hold
   connections to multiple `cot` instances simultaneously (e.g. `cot1`
   for EdTech app C and `dot1` for a different app D)? If so, does
   `at1qry` aggregate across applications or maintain separate state?

4. **Skill sync frequency.** On every result packet, on a schedule,
   or on explicit request? Too frequent adds overhead; too infrequent
   delays learning.

5. **`pending_contributor` timeout.** If a contributor never reports,
   how long does `cot1` wait before closing the result as `:partial`?
   Configurable per intent type or global?

6. **Transport selection.** When does WebSocket or Erlang distribution
   become preferable to HTTP? Trigger conditions and negotiation flow
   not yet defined.

7. **Revocation grace period.** What happens to in-flight intents when
   revocation is received? Complete and report, or abort immediately?

---

## What TAP is not

- Not an API specification for any specific application
- Not a replacement for application-level auth or access control
- Not a guarantee of execution — only a guarantee of structured,
  trusted communication
- Not Aetheris-specific — any agent framework can implement TAP

---

## Version history

| Version | Status | Notes |
|---------|--------|-------|
| v0 | Design | Initial architecture. Working names. Pre-implementation. |
```

