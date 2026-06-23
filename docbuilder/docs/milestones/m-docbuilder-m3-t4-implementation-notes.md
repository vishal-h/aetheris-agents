# Implementation notes — m-docbuilder-m3 t4

Ticket: orchestrator reads `confirmed_context.json` + `docbuilder_context` sprint case
(context_builder → orchestrator end-to-end).

---

## What shipped

- **`agents/docbuilder_orchestrator.exs`** — context-source resolution at eval time, with
  precedence:
  1. `DOCBUILDER_CONTEXT` env var (non-empty) — explicit/legacy runs always win.
  2. `output/confirmed_context.json` (when present) — the context-builder handoff.
  3. `"{}"`.
  The chosen source is surfaced in the prompt's "Configuration resolved at startup" block
  (`Context source: …`). The resolved context is re-encoded to compact single-line JSON
  (`Jason.encode!`) before prompt interpolation, since the file source is pretty-printed
  and the `<CONTEXT>` "one arg, verbatim" steps (D1 rename, D2 run-log, narrative PDF)
  need a single line.
- **`aetheris/scripts/sprint.sh`** — new `docbuilder_context` case (also under `all`):
  eval-checks context_builder, runs it (NL request → `confirmed_context.json`), then runs
  the orchestrator with `DOCBUILDER_CONTEXT` **unset** so it reads the file, and verifies
  the rendered `xyz_inc_invoice_30-Jun-2026.{xlsx,docx,pdf}`. Usage line updated.

---

## Design decisions

- **Env var wins over the file.** The handoff doc said "reads it instead of the env var";
  I made the env var take precedence when set so (a) the legacy/direct `docbuilder` sprint
  and m2b runs are unaffected, and (b) a stale `output/confirmed_context.json` can never
  hijack an explicit run. The file is used precisely in the canonical flow where the
  operator never sets the env var (they talk to the context builder). Net: the canonical
  "same as last month" flow is unaffected, legacy is protected.
- **`unset DOCBUILDER_CONTEXT` in the sprint case.** The `docbuilder` case sets
  `DOCBUILDER_CONTEXT` as a *shell* variable (its if-guard default), which would leak into
  `docbuilder_context` under `TARGET=all`. The new case unsets it to force the file path.
  (`run_agent` is a shell function, so `env -u … run_agent` can't be used — an explicit
  `unset` is the correct mechanism.)
- **Compact re-encode.** Without it, a pretty-printed file context would be interpolated
  as multi-line into the "one arg, verbatim" steps and the LLM could mis-split it.

---

## Done-check

- Orchestrator eval: EXIT 0 in both modes (env-var present; env-var absent with
  `confirmed_context.json` present).
- Full docbuilder suite: **292 passed, 3 skipped** (no regression).
- End-to-end `docbuilder_context` sprint → context-builder run + orchestrator run
  `docbuilder-orch-5HD1Eg`, both `done`. Request "Invoice for XYZ for June 2026, same as
  last month":
  - `confirmed_context.json` written by the builder (June, 2627/XYZ/03).
  - Orchestrator rendered `xyz_inc_invoice_30-Jun-2026.{xlsx,docx,pdf}` — the `30-Jun`
    filename proves it used the file context (no env var set).
  - PDF: invoice `2627/XYZ/03`, date `30-Jun-2026`, `$1,000.00` line item + Total, **logo
    embedded** (1 image).
  - PHASE D2 appended the June run to `run_log.json` (now 3 entries) — it becomes "last
    month" for a future July request, closing the loop.

---

## t5 watch item (carried)

The "scripts do, agents decide" invariant held again end-to-end: the deterministic context
came from `resolve_last_run.py` and the orchestrator rendered it verbatim; the LLM computed
no values. With t3's byte-identical evidence, this has now recurred across tickets and
**qualifies as a CLAUDE.md standing-instruction promotion at t5** (per the reviewer's
cross-ticket flag).

## Forward to t5

- Capability matrix: `resolve_last_run.py` + `run_log_writer.py` (→ 20 scripts),
  `context_builder.exs` (→ 2 agents); confirm `_format.py` already present.
- Milestone summary; CLAUDE.md learning scan (incl. the invariant above); README m3 line;
  drift_check; BL-002 project-knowledge re-export.
- The new `docbuilder_context` sprint case lives in the **aetheris** repo's `sprint.sh`
  (committed there, not in aetheris-agents).
