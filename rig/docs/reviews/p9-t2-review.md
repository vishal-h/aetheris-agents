# Review — rig-p9 t2 — round 1

Reviewer: claude-ui
Subject: Docbuilder stored config (`DOCBUILDER_TENANT`) + `STEP_CONFIG_HINTS` — commit `7c9aa6c`

---

## Findings

1. **[non-blocking, no action] t3-agent hint added early.** The `STEP_CONFIG_HINTS` entry
   for `docbuilder_context_orchestrator.exs` is added before that agent exists (t3). The
   implementation notes correctly note this is harmless — `STEP_CONFIG_HINTS` is a lookup
   keyed by agent path; an entry with no matching plan step is never read. Noted for the
   record.

2. **[non-blocking → merge gate] `cargo tauri dev` Settings smoke not run** (no display).
   Expected for the automated done-check. **Manual smoke pass is the t2 merge gate
   (operator-owned):** Settings → a "Docbuilder" section with a `Tenant` field
   (placeholder `bitloka`).

---

## Outcome

No code changes required. Scope held — only `DOCBUILDER_TENANT` in stored config;
per-run vars (`DOCBUILDER_REQUEST` / `DOCBUILDER_CONTEXT_FILE`) intentionally excluded.
**t2 clear once the manual Settings smoke pass is confirmed.**
