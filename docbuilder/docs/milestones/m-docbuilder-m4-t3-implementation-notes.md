# Implementation notes — m-docbuilder-m4 t3

Ticket: tests + `docbuilder_fresh` sprint case for the freeform path.

---

## What shipped

- **`tests/test_context_builder_fresh.py`** (new) — 3 tests exercising `validate_fields.py`,
  the deterministic core of the fresh path, via the script CLI (the same invocation the
  agent makes), no live LLM:
  - complete freeform invoice → exit 0, all required fields present, `date` → ISO,
    `amount_due` kept as display string;
  - missing `client_email` → exit 1, `client_email` in `missing`, error payload only;
  - **F2 watch (t2 review):** extraction intermediates (`unit_price`/`line_item_qty`/
    `currency`) pass through normalised (coerced number / upper-cased) — harmless, the
    orchestrator ignores fields not in the context schema.
- **`aetheris/scripts/sprint.sh`** — new `docbuilder_fresh` case (also under `all`): resets
  `data/run_log.json` to `[]` (forces the fresh path for a client not in the log), runs
  ONLY `context_builder.exs`, and asserts: eval ok; `confirmed_context.json` written +
  parseable + client matches; **run log NOT appended** (builder-only — PHASE D2 runs with
  the orchestrator). Usage line updated.
- **`docbuilder/runbook.md`** — `docbuilder_fresh` sprint-case entry under "How to run"
  (points at the t4 m4 section for full detail).
- **`docs/rig/runbook.md`** — `docbuilder_fresh` paragraph in the m3 context-builder section.

## Done-check

- `test_context_builder_fresh.py`: **3 passed**. Full docbuilder suite: **327 passed, 3
  skipped** (+3 over t2's 324).
- `docbuilder_fresh` sprint (run `docbuilder-ctx-zSSFmQ` → done): `confirmed_context.json`
  written for "Northwind Traders" (client_name/email/address extracted); run log stayed `[]`
  → "run log not appended" assertion green.

## Notes

- **Scope split:** t3 adds only the *sprint-case entries* to the runbooks; the full
  "### m4 — freeform NL field extraction" narrative section in `docbuilder/runbook.md` +
  the docbuilder-module m4 paragraph in `docs/rig/runbook.md` are **t4's** job (docs sync).
- **F2 disposition:** the unit test confirms intermediates pass through `validate_fields.py`
  normalised. A full *render-with-intermediates* end-to-end is not in `docbuilder_fresh`
  (builder-only, by design — needed to assert the run-log gate). The orchestrator ignoring
  unknown fields is the context-schema contract; a fresh-render chain check can be a t4/m5
  follow-up if desired.
- **`docs/rig/runbook.md` is a project-knowledge-tracked doc** — this t3 edit advances it
  past the manifest, so a `project_knowledge` WARN appears after commit (BL-002, cleared at
  m4 close alongside the t4 capability-matrix change).
- `aetheris/scripts/sprint.sh` lives in the **aetheris** repo (committed there, not in
  aetheris-agents).
