# Docbuilder m4 — Handoff & Conversation Starter

## State at session close (2026-06-24)

**Repos:** aetheris-agents @ `c14a0e4` · aetheris @ `155edca`
**Drift:** 8 PASS / 0 FAIL / 0 WARN (15 project_knowledge entries all match HEAD)

---

## What closed in this session

**m-docbuilder-m3 (closed @ `80f2b26` → `c14a0e4`):**
- `run_log_writer.py` + orchestrator PHASE D2 — every run appended to `data/run_log.json`
- `context_builder.exs` — NL request → `confirmed_context.json`, single-shot gate
- `resolve_last_run.py` — deterministic "same as last month": month-end date + `{FY}/{client_code}/{seq+1}` FY-rolling invoice increment
- Orchestrator context source (`DOCBUILDER_CONTEXT` env > `DOCBUILDER_CONTEXT_FILE` / default file > `{}`)
- `docbuilder_context` sprint case — chains builder → orchestrator end-to-end

**rig-p9 (closed @ `c14a0e4`):**
- `orchestrate_start` per-run env vars (`extra_env`) + collapsible form in OrchestratorView
- `DOCBUILDER_TENANT` stored config + `STEP_CONFIG_HINTS` for docbuilder agents
- `chain_docbuilder.py` — top-level chained run emitting the orchestrator protocol
- `orchestrate_start` `.py` heuristic (`script_path: Option<String>`) + `/docbuilder` panel
- Two CLAUDE.md promotions: `run_command` no-env / sh-blocked → python script; no nested `mix aetheris run` → top-level/sequential

**Capability matrix:** docbuilder 2 agents / 21 scripts; repo total 25 / 59.

---

## m4 Scope — Option C: Freeform NL Field Extraction

**Primary goal:** extend `context_builder.exs` (or a new extraction layer) so a
freeform request like "a formal quote for Acme Corp, 40 days of consulting at
£1,200/day, standard payment terms" produces a valid `DOCBUILDER_CONTEXT` without
the user needing prior runs in the log.

The recurring/"same as last month" path (m3) is already handled. m4 adds the
complementary path: open-ended extraction from a single request.

### What already exists (do not rebuild)

- `context_builder.exs` — reads the tenant catalogue + run log; detects recurring
  requests and calls `resolve_last_run.py`; writes `confirmed_context.json`
- `resolve_last_run.py` — deterministic date/invoice bumping for recurring requests
- `run_log_writer.py` + PHASE D2 — every run appended to the log automatically
- `confirmed_context.json` → orchestrator pipeline — fully wired (m3 + rig-p9)
- Rig Docbuilder panel — drives the chain end-to-end from the UI

### What m4 adds

The current `context_builder.exs` system prompt has a `3b. FRESH request` path:
"build from the request + catalogue — if a required field is missing, list what's
missing and STOP." m4 makes this path actually work for a rich open-ended request:

1. **Field extraction prompt** — structured extraction from freeform text:
   parse client name, line items, amounts, dates, doc_type/variant from a single
   NL sentence. The LLM does this; no new script needed (derived values like
   month-end dates still go through scripts).

2. **Ambiguity handling** — if required fields are missing or ambiguous after
   extraction, the builder asks clarifying questions (a short follow-up loop)
   rather than stopping dead.

3. **Confirmation gate** — unchanged from m3: single-shot, the operator reviews the
   `PROPOSED DOCBUILDER_CONTEXT` block before the orchestrator runs.

4. **Run log integration** — the rendered run is appended by PHASE D2 as usual, so
   a freeform run for a new client becomes the seed for "same as last month" next
   time.

### What is NOT in scope for m4

- Conversational template editing (patch schema + JSONL edit log) — deferred
- Multi-tenant support beyond the existing tenant layout
- New document types or template variants
- Changes to the Rig Docbuilder panel (rig-p9 is closed)
- The interactive confirm/amend loop (needs a conversational harness)

---

## Key design questions to resolve before drafting the milestone doc

**1. Extraction in the agent vs a new extraction script.**
The m3 learnings say "derived values → deterministic script". But field extraction
from NL is fundamentally LLM work — there's no deterministic rule for parsing
"40 days at £1,200/day" into `{line_item_qty: 40, unit_price: 1200, currency: GBP}`.
The LLM extracts; the script then formats/validates the result. Where does the
boundary sit?

**2. Ambiguity loop depth.**
How many clarifying-question rounds before the builder gives up and asks for a full
context JSON? One round is probably right for m4 — the goal is a usable first pass,
not a full conversational design tool.

**3. `context_builder.exs` extension vs a new `field_extractor.exs` agent.**
Option A: extend the existing system prompt with a richer extraction section.
Option B: a new `field_extractor.exs` sub-agent called by the context builder for
fresh requests.
Option A is simpler and keeps the single-agent model; Option B is cleaner if the
extraction logic grows complex. m3's "scripts do, agents decide" learning suggests
keeping agents simple — Option A is probably right for m4.

**4. `extract_fields.py` — a validation/normalisation script.**
Even if the LLM does the extraction, a small Python script that validates the
extracted fields against the context schema (required fields present, date format
correct, amount parseable) and returns a clean JSON object would allow a
byte-identical-style assertion in tests. Worth it?

---

## Relevant prior state for the m4 milestone doc

**`context_builder.exs` current system prompt (step 3b, the fresh path):**
```
3b. FRESH request (not recurring, or no prior run) → build the DOCBUILDER_CONTEXT from
    the request + catalogue. Required for every context: title, client_name,
    client_email, date. For invoices ALSO: invoice_number, client_address, amount_due.
    Do NOT invent client data — if a required field is in neither the request nor a
    prior run, LIST what is missing and STOP. write_file the context (a single JSON
    object, not wrapped) to "output/confirmed_context.json".
```

m4 replaces the "LIST what is missing and STOP" behaviour with extraction +
clarifying questions.

**Context schema required fields (from `docbuilder/docs/context-schema.md`):**
- Required for all: `title`, `client_name`, `client_email`, `date`
- Required for invoices: additionally `invoice_number`, `client_address`, `amount_due`
- Optional: `client_code`, `order_ref`, `order_effective_date`, `terms`

**`data/run_log.json` seed entry (for testing the fresh → subsequent-recurring path):**
A fresh m4 run for a new client (e.g. "Acme Corp") that completes successfully will
have its context appended to the run log by PHASE D2. The next run for Acme can then
use "same as last month" — m3 handles it from there.

---

## Conversation starter for the m4 session

Paste this at the start of the new session:

---

We're starting m4 of the docbuilder pipeline. Read `CLAUDE.md` and the project
knowledge before we begin.

**State:** aetheris-agents @ `c14a0e4`, drift clean (8 PASS / 0 FAIL / 0 WARN).
m1, m2a, m2b, m3, rig-p9 are all done.

**m4 goal:** extend `context_builder.exs` so a freeform open-ended request like
"a formal quote for Acme Corp, 40 days of consulting at £1,200/day, standard
payment terms" produces a valid `DOCBUILDER_CONTEXT` — without requiring a prior
run in the log. The recurring/"same as last month" path is already handled (m3);
m4 adds the complementary freeform extraction path.

**What already exists (do not rebuild):**
- `context_builder.exs` — reads catalogue + run log; recurring requests call
  `resolve_last_run.py`; fresh requests have a stub "list missing fields and stop"
  path (m4 replaces this)
- Full orchestrator pipeline, `chain_docbuilder.py`, Rig Docbuilder panel — all wired

**Four design questions to resolve before drafting the milestone doc:**
1. Extraction in the agent system prompt vs a new `extract_fields.py` validation
   script — where does the LLM/script boundary sit for field extraction?
2. Ambiguity loop depth — one clarifying-question round before fallback?
3. `context_builder.exs` extension vs a new `field_extractor.exs` sub-agent?
4. `extract_fields.py` for validation/normalisation — worth it for testability?

The handoff doc with full context is at `docbuilder/docs/milestones/m4-handoff.md`.
Ready to draft the m4 milestone doc once the four design questions are resolved.
