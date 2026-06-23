# Implementation notes — m-docbuilder-m3 t1

Ticket: `run_log_writer.py` + orchestrator PHASE D hook (run-log foundation for the
m3 context builder).

---

## What shipped

- **`scripts/run_log_writer.py`** (new) — appends one entry per run to a JSON-array
  log (`data/run_log.json` by default). Entry shape:
  `{tenant, doc_type, variant, run_id, timestamp, context, outputs}`.
  - `timestamp` = `datetime.now().astimezone().isoformat(timespec="seconds")` — ISO8601
    with local tz offset, matching the seed (`2026-06-21T07:27:00+05:30`).
  - `context` = parsed `--context` JSON (the run's `DOCBUILDER_CONTEXT`).
  - `outputs` = the `renamed` paths read from PHASE D's `output/renamed.json`
    (`--renamed`).
  - Module-level functions (`build_entry`, `append_run`, `_load_log`, `_read_outputs`)
    are importable so unit tests exercise them directly (init_db design pattern).
- **`agents/docbuilder_orchestrator.exs`** — `run_id` is now pre-established as a
  variable (used in both the `RunConfig` and the prompt). PHASE D gained **D2**: after
  the rename (D1), the LLM calls `run_log_writer.py` with the resolved
  `tenant/doc_type/variant/run_id`, `--renamed output/renamed.json`, and the verbatim
  context JSON, writing `data/run_log.json`.
- **`tests/test_run_log_writer.py`** (new, non-integration) — 21 tests.
- `data/.gitignore` already lists `run_log.json` (committed in `42871e6`); the log file
  itself stays local/gitignored.

---

## Design decisions

- **Idempotent re-runs.** `append_run` replaces any existing entry with the same
  `run_id` rather than duplicating, so re-running a run_id is safe.
- **Hard-fail vs degrade split** (per CLAUDE.md "stage CLIs degrade" + exit-code rules):
  - Invalid `--context` JSON → exit 1 (the entry would be meaningless).
  - Existing log file malformed / not a JSON array → exit 1 (must never silently
    overwrite run history).
  - Missing / malformed `--renamed` file → degrade to `outputs: []` with a stderr
    warning, exit 0 (run logging is a best-effort side effect; a logging hiccup must
    not fail the pipeline).
- **`to_string(resolved_version)`** in the orchestrator args guards against a non-binary
  version value at eval time (same defensiveness as elsewhere).

---

## Done-check

- `test_run_log_writer.py`: 21 passed (append / preserve / idempotent / no-mutate;
  load missing/empty/array/malformed/non-array; build_entry shape + default timestamp;
  `_read_outputs` from-file/none/missing/malformed; CLI append/second/idempotent/
  invalid-context/corrupt-log/missing-renamed).
- Full docbuilder suite: **256 passed, 3 skipped**.
- Orchestrator evaluates clean (bitloka context).
- End-to-end sprint `docbuilder-orch-iV7NXA` → **`done`** (10 steps). `data/run_log.json`
  gained the second entry — full context + the three renamed outputs — confirming the
  PHASE D2 hook fires after rename.

---

## Forward to later m3 tickets

- t3 (`resolve_last_run.py`) reads this log, matching by `{tenant, doc_type,
  client_name}` and taking the last entry. The idempotent-by-run_id behavior means the
  log is append-only history; t3 must pick the latest by order/timestamp, not assume
  uniqueness of `{client_name, date}`.
- `run_log.json` needs a capability-matrix row at the t5 docs-sync (new script →
  19 scripts). Note alongside `_format.py` (added post-m2b).
