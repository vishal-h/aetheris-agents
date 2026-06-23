# Implementation notes — m-docbuilder-m3 t2

Ticket: `context_builder.exs` — NL request → resolved `DOCBUILDER_CONTEXT` →
confirmation view + `output/confirmed_context.json`.

---

## What shipped

- **`agents/context_builder.exs`** (new) — a conversational `RunConfig` agent.
  - Inputs (env, eval-time): `DOCBUILDER_TENANT` (required, raises if unset),
    `DOCBUILDER_REQUEST` (the NL request; empty → the agent reports it's required and stops).
  - Tools: `read_file` (catalogue + run log), `write_file` (confirmed_context.json) — no
    `run_command` (the deterministic resolution script lands in t3).
  - Workflow baked into the system prompt: read the tenant catalogue → pick doc_type/variant;
    read `data/run_log.json` → find the most recent entry matching the requested
    `client_name` + `doc_type` for "same as last month"; carry stable fields forward
    verbatim (client_name/email/address, order_ref, order_effective_date, terms); set
    `date` to the requested period; update title/invoice_number/amount_due; present a
    "PROPOSED DOCBUILDER_CONTEXT" confirmation view; write `output/confirmed_context.json`.
  - Refuses to fabricate: if a required field is in neither the request nor a matching
    prior run, it lists what's missing and stops.

---

## Design decisions

- **Confirmation gate in a single-shot harness.** Aetheris RunConfig agents run to
  completion (no mid-run human input outside multi-agent send/wait). So the gate is
  modelled as: the agent emits a clearly-headed "PROPOSED … (review before rendering)"
  block AND writes `output/confirmed_context.json`. The operator reviews the run output
  before t4 renders; t4 only acts when the file exists. A stricter interactive
  proposed→confirmed handshake is a conversational-/remote-control-layer concern, noted
  for later if needed.
- **Invoice number / amount are PROVISIONAL in t2.** Per the ticket split, the exact
  FY-rolling sequence increment is t3's `resolve_last_run.py` (deterministic). t2's agent
  does best-effort LLM resolution and the prompt explicitly flags these fields as
  provisional. (In the e2e run the LLM did bump `2627/XYZ/02` → `2627/XYZ/03` correctly
  for a June-2026 / FY26-27 invoice — t3 will make this deterministic regardless.)
- **No Python script in t2** (tools are read_file/write_file per the handoff), so there is
  no pytest. Verification is the eval check + an end-to-end run asserting the produced
  `confirmed_context.json`. `resolve_last_run.py` + its unit tests arrive in t3.

---

## Done-check

- Eval: `mix run --eval Code.eval_file(...)` → **EXIT 0** with a request, and with an
  empty request (still a valid RunConfig).
- Full docbuilder pytest suite unchanged: 256 passed / 3 skipped (no Python added).
- End-to-end run `docbuilder-ctx-g5cd5A` → **`done`**. `output/confirmed_context.json`:
  - date `30-Jun-2026` (June month-end) ✅
  - client_name `XYZ Inc`, address/email/order_ref/order_effective_date/terms carried
    verbatim from the last run ✅
  - doc_type `invoice`, invoice_number `2627/XYZ/03` (provisional bump) ✅
  - all invoice-required fields present (title, client_name, client_email, date,
    invoice_number, client_address, amount_due) ✅

---

## Forward to later m3 tickets

- **t3** — `resolve_last_run.py` replaces the LLM's provisional invoice-number/date math
  with deterministic FY-rolling logic; `context_builder.exs` gains `run_command` and calls
  it when "same as last month" is detected. The run log may contain in-place-updated
  entries (idempotency-as-replace, t1/F1) — the resolver picks the latest matching
  `{tenant, doc_type, client_name}` by order/timestamp, not by `{client_name, date}`.
- **t4** — orchestrator reads `output/confirmed_context.json` instead of the
  `DOCBUILDER_CONTEXT` env var; sprint case `docbuilder_context` chains builder → orchestrator.
- **t5** — capability matrix: add `context_builder.exs` (→ 2 agents) and `run_log_writer.py`
  (→ 19 scripts), plus `resolve_last_run.py` from t3; confirm `_format.py` already present.
