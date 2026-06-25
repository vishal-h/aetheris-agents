# Review — m-docbuilder-m4 t3 — round 1

Reviewer: claude-ui
Subject: fresh-path tests + `docbuilder_fresh` sprint case (aetheris-agents `5998323`,
aetheris `1a8eb08`)

---

## Findings (all non-blocking — no t3 code change)

1. **Client-match assertion hardcodes `'Northwind'`.** The sprint case checks
   `'Northwind' in client_name`, which is correct for the default `DOCBUILDER_REQUEST` but
   would fail if an operator overrides the request with a different client. Acceptable for
   the default; **carried to t4** — the m4 runbook entry should note: "the `docbuilder_fresh`
   client-match assertion uses the default request's client name; override `DOCBUILDER_REQUEST`
   accordingly for a different client."

2. **`docs/rig/runbook.md` → `project_knowledge` WARN after commit.** Expected (BL-002,
   cleared at m4 close with t4's capability-matrix change). No action.

3. **`test_context_builder_fresh.py` docstring says "Integration tests"** but they are
   non-integration script-CLI tests (same category as `test_run_log_writer`/`resolve_last_run`).
   Misleading label. Low priority — **optional tidy at t4** (no t3 change).

## Cross-ticket notes

- **F1** → note the default-request dependency in the t4 `docbuilder_fresh` runbook entry.
- **F2 (t2 watch) closed:** the unit test confirms intermediates normalise + pass through;
  the orchestrator ignores unknown fields per the context-schema contract. No further action.
- **t4 confirm:** the full m4 narrative sections must reference the **single-shot
  self-correction** model (t2 adjudication), not the original "wait for reply" wording.
- Scope split (t3 = sprint-case entries; t4 = full m4 narrative) is clean.

## Outcome

3 tests pass, full suite 327/3, `docbuilder_fresh` verified end-to-end (Northwind context
written, run log not appended). No t3 code changes. **t3 clear.** Carried to t4: F1 runbook
note, F3 docstring tidy, the single-shot-wording confirm.
