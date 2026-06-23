# Docbuilder m3 — Context Builder (milestone)

> Canonical m3 milestone doc (single source of truth, methodology §1/§8). Named to match
> the m1/m2a/m2b convention (`docs/m{N}-milestone.md`); originally drafted as the m3
> handoff/conversation-starter, retained below.

## State at session close (2026-06-22)

**Repos:** aetheris-agents @ `3341a71` · aetheris @ `308ddb2` · drift: 8 PASS / 0 FAIL / 0 WARN

> Note: this handoff was written at `3341a71`; two further fixes landed afterward on
> `main` — the weasyprint `base_url` fix (`d43dcf6`) and this handoff commit. The
> bitloka invoice now also embeds its logo.

**What shipped in this session (post-m2b):**

- Bitloka invoice template bundle (`data/templates/bitloka/invoice/v1/`) — production-ready
- Orchestrator nested-bundle eval fix (`1eb0f27`) — prefers nested bundle, falls back to flat
- Currency rendering fix across xlsx/docx/pdf — `_format.py` shared helper, reviewed, merged
- weasyprint `base_url` fix — narrative-mode relative `<img>` (logo) now resolves against the bundle dir
- `context-schema.md` updated — `invoice_number`, `client_address`, `order_ref`,
  `order_effective_date`, `terms`, `amount_due` added as documented fields
- `docbuilder/data/run_log.json` seeded with the May 2026 XYZ invoice entry (m3 bootstrap)
- Capability matrix: 1 agent / 18 scripts / 56 total; project-knowledge manifest clean

---

## m3 Scope — Context Builder Agent

**Primary goal:** a conversational agent that builds `DOCBUILDER_CONTEXT` from natural
language and hands off to the orchestrator, with a confirmation gate before rendering.

**The canonical user story:**

> "Invoice for XYZ for Jun 2026 — same as last month"
> → agent resolves last run, bumps date and invoice number, and writes the resolved
>   context, presenting it as a "PROPOSED DOCBUILDER_CONTEXT" block (the confirmation view)
> → operator reviews that block in the trajectory before invoking the orchestrator
> → orchestrator runs

> **Confirmation gate is single-shot** (t2 decision, review F2): the agent always writes
> `output/confirmed_context.json` and emits the proposal block for review; the "gate" is
> the operator inspecting it before triggering rendering, and t4 only renders when the
> file exists. A true interactive "Confirm? / tell me what to change" loop needs a
> conversational harness that is **not built** and is **deferred out of m3 scope**.

### Key design decisions (resolved)

| Decision | Choice |
|---|---|
| Run log storage | Option B — local `docbuilder/data/run_log.json` (gitignored) |
| Run log format | JSON array, one entry per run (see seeded entry below) |
| Run log idempotency | **Replace-in-place by `run_id`** (t1 decision, refining the original "skip if exists"): re-running a `run_id` overwrites that entry rather than skipping or duplicating, so the log stays accurate. The log is append-only *history* across distinct run_ids; `resolve_last_run.py` (t3) must pick the latest matching `{tenant, doc_type, client_name}` by order/timestamp — it must **not** assume `{client_name, date}` is unique. |
| "Same as last month" | Find last matching `{tenant, doc_type, client_name}` entry in run_log; bump date + increment invoice sequence |
| Invoice number increment | `{FY}/{client_code}/{seq+1}` where the FY code is the last two digits of each year (`{start%100:02d}{end%100:02d}`), rolling on April 1: month ≥ 4 → `{year}-{year+1}` (e.g. 2026-06 → `2627`), else `{year-1}-{year}` (e.g. 2026-03 → `2526`). Matches the committed Bitloka invoice `2627/XYZ/02`. (t3: corrected from the original `{year}{…}` shorthand, which would have produced `202627`.) `seq+1` does not reset on FY change. |
| Confirmation gate | **Single-shot** (t2 / review F2): the agent always writes `output/confirmed_context.json` and emits a "PROPOSED DOCBUILDER_CONTEXT" block; the operator reviews that block before invoking the orchestrator, and t4 only renders when the file exists. An interactive confirm/amend loop needs a conversational harness — deferred, out of m3 scope. |
| Agent type | Conversational Elixir agent (new `context_builder.exs`) with `read_file`/`write_file`/`run_command` tools |

### Proposed ticket structure

**t1 — `run_log_writer.py` + orchestrator PHASE D hook**
- New script: appends a run_log entry after PHASE D (rename), writing
  `{tenant, doc_type, variant, run_id, timestamp, context, outputs}` to `data/run_log.json`
- Orchestrator: call `run_log_writer.py` at the end of PHASE D
- `data/.gitignore`: add `run_log.json` to gitignore *(already done — `42871e6`)*
- Tests: append, read-back, idempotent on missing file

**t2 — `context_builder.exs` — NL → context → confirmation gate**
- Reads the tenant's catalogue + run_log
- Understands: "invoice for XYZ for Jun 2026", "same as last month", explicit field overrides
- Resolves to a concrete `DOCBUILDER_CONTEXT` JSON
- Presents it as a "PROPOSED DOCBUILDER_CONTEXT" block (single-shot confirmation view —
  see the Confirmation-gate decision above) and writes it to
  `output/confirmed_context.json`
- Tools: `read_file` (catalogue, run_log), `write_file` (confirmed_context.json),
  `run_command` (listed but unused in t2; t3 calls `resolve_last_run.py` via it — F1)

**t3 — "Same as last month" resolution + FY invoice number increment**
- `resolve_last_run.py` — finds last matching entry in run_log by
  `{tenant, doc_type, client_name}`; returns the context with date bumped to the
  current month-end and invoice sequence incremented
- FY logic: `{FY}/{client_code}/{seq+1}` with April 1 rollover
- `context_builder.exs` calls this script when "same as last month" is detected
- **Missing run log** (t3 / review F1): an absent `run_log.json` is treated as an empty
  log → `{"status": "no_prior_run"}`, **exit 0** (a missing log on a fresh checkout is an
  expected state; the agent falls back to a fresh request). Hard-fail (exit 1) is reserved
  for a malformed/non-array log or a bad `--target-month`.
- Tests: FY rollover (March→April), sequence increment, no prior run (graceful),
  missing/empty/corrupt log, `--target-month` parsing (incl. 3-part value → exit 1)

**t4 — Orchestrator integration: context_builder → orchestrator handoff**
- When `confirmed_context.json` exists, the orchestrator reads it instead of the
  `DOCBUILDER_CONTEXT` env var (or the context_builder passes it as the env var directly)
- Sprint case: `./scripts/sprint.sh docbuilder_context` — runs the context builder
  conversationally, then hands off to the orchestrator
- End-to-end: "invoice for XYZ for Jun 2026, same as last month" → Jun invoice rendered

**t5 — Docs sync + capability matrix + milestone close**

---

## Seeded run_log.json entry

Located at `docbuilder/data/run_log.json` (gitignored). This is the bootstrap entry
for "same as last month" to work on the first m3 run:

```json
[
  {
    "tenant": "bitloka",
    "doc_type": "invoice",
    "variant": "v1",
    "run_id": "docbuilder-orch-1QIcVg",
    "timestamp": "2026-06-21T07:27:00+05:30",
    "context": {
      "title": "Invoice 2627/XYZ/02",
      "client_name": "XYZ Inc",
      "client_email": "accounts@xyz.example",
      "date": "31-May-2026",
      "doc_type": "invoice",
      "invoice_number": "2627/XYZ/02",
      "client_address": "1234 Stevens Creek Blvd, Suite 123, Santa Clara, California 95051, USA",
      "order_ref": "Agreement-240201",
      "order_effective_date": "01-Feb-2024",
      "terms": "Discounted rates for May 26",
      "amount_due": "$1,000.00"
    },
    "outputs": [
      "output/xyz_inc_invoice_31-May-2026.xlsx",
      "output/xyz_inc_invoice_31-May-2026.docx",
      "output/xyz_inc_invoice_31-May-2026.pdf"
    ]
  }
]
```

---

## Items to commit before starting m3

1. `docbuilder/docs/context-schema.md` — updated schema (invoice_number, client_address, etc.) — **done `7ac70f8`**
2. `docbuilder/data/run_log.json` — seeded entry (gitignored; commit only the .gitignore entry) — **done `42871e6`**
3. `docbuilder/data/.gitignore` — add `run_log.json` — **done `42871e6`**

---

## Conversation starter for the m3 session

Paste this at the start of the new session:

> We're starting m3 of the docbuilder pipeline. Read `CLAUDE.md` and the project
> knowledge before we begin.
>
> **State:** aetheris-agents @ `3341a71`, drift clean (8 PASS / 0 FAIL / 0 WARN).
> m1, m2a, m2b are done. The Bitloka invoice is production-ready.
>
> **m3 goal:** a context builder agent — the user says "invoice for XYZ for Jun 2026,
> same as last month" and the agent resolves the context, shows it for confirmation, and
> hands off to the orchestrator.
>
> **Already resolved before this session:**
> - Run log: local `docbuilder/data/run_log.json` (gitignored), JSON array, seeded with
>   the May 2026 XYZ invoice entry
> - Invoice number increment: `{FY}/{client_code}/{seq+1}`, FY rolls on April 1
> - Confirmation gate: mandatory before rendering
> - Ticket structure: t1 (run_log_writer), t2 (context_builder agent), t3 (same-as-last-month
>   resolution + FY increment), t4 (orchestrator integration), t5 (docs sync / milestone close)
>
> Ready to draft the m3 milestone doc. Start by reading
> `docbuilder/docs/m2b-milestone.md` (for the format convention) and
> `docbuilder/docs/context-schema.md` (for the field list), then let's plan.
