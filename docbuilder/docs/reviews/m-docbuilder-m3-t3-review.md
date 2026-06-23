# Review — m-docbuilder-m3 t3 — round 1

Reviewer: claude-ui
Subject: `resolve_last_run.py` + `context_builder.exs` prompt edit (commit `ad41aa5`)

---

## Findings

1. **[blocking → adjudicated, actioned] Absent run log: degrade vs exit 1.**
   `test_cli_missing_log_is_no_prior_run` treats a missing run log as
   `{"status": "no_prior_run"}` (exit 0); the milestone doc t3 note implied
   "Absent run_log.json (exit 1, distinct message)".
   **Human adjudication: accept the degrade behaviour** — a missing log on a fresh
   checkout is an expected state; the agent falls back to a fresh request. **Actioned:**
   updated `docs/m3-milestone.md` §t3 to state "Absent run_log.json → treated as empty
   log → no_prior_run, exit 0". No code change.

2. **[non-blocking → actioned] `_parse_target_month` unpack hardening.**
   `year_s, month_s = s.split("-")` raises an unhandled `ValueError: too many values to
   unpack` for a 3-part value like `"2026-06-01"`, bypassing the clean error/exit-1 path.
   **Actioned:** `s.split("-", 1)` → `"2026-06-01"` unpacks to `("2026", "06-01")`, then
   `int("06-01")` raises `ValueError` which is already caught and reported as
   `{"status": "error"}` / exit 1. Added a unit test (`_parse_target_month` raises) and a
   CLI test (`--target-month 2026-06-01` → exit 1).

---

## Cross-ticket notes

- F1 (doc-only) lands before t4 so the t5 runbook seed-instructions are written against
  the correct missing-log behaviour.
- F2 is a one-line fix + two tests, both in the round-2 packet.
- The byte-identical confirmation (agent output == direct script output) is strong
  evidence the "scripts do, agents decide" invariant holds. **Flagged for the t5
  CLAUDE.md learning scan** — if it recurs in t4 it qualifies as a standing instruction.

---

## Outcome

One blocking finding (F1) adjudicated to the degrade behaviour + doc updated; F2
hardened with tests. Round-2: `split("-", 1)`, two new tests, milestone-doc missing-log
note. **t3 clear after round-2 re-verify.**
