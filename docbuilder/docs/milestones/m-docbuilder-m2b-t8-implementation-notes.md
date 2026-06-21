# Implementation notes — m-docbuilder-m2b t8

Ticket: docs sync + capability matrix + milestone close.

---

## What shipped

- **Capability matrix regenerated** — `docs/.sections/docbuilder.md` + `docs/capability-matrix.md`
  (docbuilder now 1 agent / 17 scripts; total 24 agents / 55 scripts). Orchestrator tools
  are now just `run_command` (write_file dropped at t3).
- **`requirements.txt`** — added `google-api-python-client==2.196.0` (Drive: `_drive.py`).
- **Env-var reconciliation** — `drive/scripts/drive_download.py` `build_service` now reads
  `GOOGLE_SERVICE_ACCOUNT_FILE` first, falling back to legacy `GOOGLE_SERVICE_ACCOUNT`
  (matches `_drive.py`). `drive_upload.py` imports `build_service`, so it's covered too.
- **`README.md`** m2b → done; **`docs/rig/runbook.md`** m2b env vars + phases + DATA_PATH
  retirement; **CLAUDE.md** `## Learning — m2b-docbuilder` (3 promotions); **milestone
  summary** in `m2b-milestone.md`.
- `capability_matrix_docbuilder.exs` `max_steps` 30 → 50 (script count grew to 17).
- docbuilder suite: 202 passed, 3 skipped. drive suite: 34 passed (reconcile safe).

---

## Decisions / notes

**Capability matrix regen via the two real agents** (`capability_matrix_docbuilder.exs` then
`capability_matrix_assemble.exs`) — the done-check's `agents/capability_matrix.exs` is a
non-existent monolith (same as m1/m2a). Bumped `max_steps` 30 → 50 first: with 17 scripts
the agent needs ~21 tool calls (1 list-agents + 1 read-agent + 1 list-scripts + 17
read-scripts + 1 write) plus reasoning; 30 was too tight.

**Hand-added the two underscore helper rows.** The LLM agent listed 15 of 17 scripts —
it skipped the underscore-prefixed helpers (`_drive.py`, `_table_html.py`) as "private".
Per the t8 requirement to list them as shared helpers, I added the two rows to
`docs/.sections/docbuilder.md` before assemble (deterministic; the LLM is inconsistent
about underscore files). Final: 17 scripts.

**Env-var reconciliation kept backward-compatible.** `GOOGLE_SERVICE_ACCOUNT_FILE` is now
canonical; legacy `GOOGLE_SERVICE_ACCOUNT` still works as a fallback (the env in use sets
the legacy one — drive tests stay green, 34 passed). The drive use-case docs still mention
the legacy name; they remain valid via the fallback and a full doc rename is out of this
milestone's scope (noted).

**CLAUDE.md promotions (≥2-ticket recurrences):**
1. Remove `write_file` from an orchestrator's tools once every phase uses `--output FILE`
   (m2b t3 raised, t7 confirmed scratch 0).
2. JSON env-var default in shell: `if [-z]` + single-quoted literal, not `${VAR:-{...}}`
   (m2b t7; latent since m2a).
3. Shared cross-script `_helper.py` with lazy heavy imports (m2a t10 `_table_html.py`,
   m2b t2/t5 `_drive.py`).

---

## Milestone close

m2b is complete (t1–t8). The milestone summary (what shipped / deferred / surprises / m3
+ follow-up items) is at the bottom of `m2b-milestone.md`. Deferred to m3: Option C (NL
requests) + conversational editing. Follow-ups: `email_send_review --drive-links-file`,
`rename_output.py --dry-run`, multi-variant runtime selection.

**Project-knowledge refresh (manual, BL-002):** the drift checker will WARN that
`CLAUDE.md`, `docs/capability-matrix.md`, `docs/rig/runbook.md`, and
`docs/agent-creation-guide.md` (if touched) are stale vs the Claude.ai project export.
Re-upload them and advance `docs/project-knowledge-manifest.md` — owned by the human, same
as the m2a close.
