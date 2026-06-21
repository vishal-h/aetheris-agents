# Review — m-docbuilder-m2b t7 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Agent file conventions", §"Orchestrator patterns", §"Pre-flight checklist"; aetheris-agents--CLAUDE.md §"Implementation notes" (eval-time resolution; --output FILE; no write_file); docbuilder/docs/context-schema.md; docbuilder/docs/drive-structure.md

---

## Packet assessment

Ticket ID + scope: ✅ provided (two commits: b33baea aetheris-agents + 308ddb2 aetheris)
Done-check output: ✅ opens packet — syntax check (eval OK, tools=["run_command"], max_steps=40), full sprint (status done, three [OK] renamed outputs), exhaustive scratch check (EMPTY — 0), full suite (202 + 3 skipped)
Diff — aetheris-agents (b33baea): ✅ full orchestrator diff
Diff — aetheris (308ddb2): ✅ sprint.sh diff
Implementation notes: ✅ committed — eval-time resolution, conditional PHASE E/F, PHASE E pre-computed paths, PHASE F runtime dependency, two sprint.sh bugs documented

---

## Findings (all non-blocking)

1. The `${VAR:-{...}}` brace-append bug was latent since m2a (manifests when
   `DOCBUILDER_CONTEXT` is already set). Fix (if-guard + single-quoted literal) is correct.
   **CLAUDE.md candidate (recorded in t8):** for a JSON env default in sprint.sh, use
   `if [ -z ]` + single-quoted literal, not `${VAR:-{...}}`.

2. PHASE E renamed paths are pre-computed in Elixir (replicates `slugify`/`safe_segment`/
   `doc_type_base`) — bounded dual-maintenance. Future fix: a `rename_output.py --dry-run`
   that prints the would-be names, so the orchestrator reads them deterministically.
   Documented in the t7 notes; non-blocking for m2b.

3. PHASE F is the single step where the LLM reads a file's contents (`uploaded.json`) and
   passes them inline as `--drive-links`. Bounded (2–3 entries), only runs when a review
   alias is set, and degrades to `(none)`. Acceptable for m2b; `--drive-links-file` would
   remove it (deferred).

4. Sprint default now uses an ISO date → predictable renamed filenames in the verify step
   (`acme_corp_proposal_2026-06-20.*`) and a cleaner filename convention. Positive change.

5. `DOCBUILDER_DATA_PATH`/`DOCBUILDER_DOC_TYPE`/`DOCBUILDER_VERSION` retired from the
   orchestrator (now fully `DOCBUILDER_CONTEXT`-driven; data-source paths come from the
   template). `runbook.md` updated in this commit. **Confirm `docs/rig/runbook.md` matches
   at t8** (recorded in the t8 ticket).

---

## Cross-ticket notes

- **Scratch artifacts: 0** — third consecutive sprint; the `--output` + no-`write_file`
  pattern holds.
- **Conditional PHASE E/F** — eval-time `deliver_upload?`/`deliver_email?` flags emit the
  concrete step or a `(skipped: …)` notice. Clean and verifiable.
- **t8 confirmed Touches:** capability matrix regen (new scripts `fetch_template`,
  `rename_output`, `upload_output`, `email_send_review` + `_drive` shared helper);
  `requirements.txt` + `google-api-python-client`; `GOOGLE_SERVICE_ACCOUNT_FILE` vs
  `GOOGLE_SERVICE_ACCOUNT` reconciliation; two CLAUDE.md candidates (sprint.sh JSON
  default, remove `write_file`); `docs/rig/runbook.md` m2b additions + DATA_PATH
  retirement; milestone summary.

---

**Outcome: zero blocking findings. t7 clear to merge. t8 clear to start.**
F1/F5 forward items folded into the t8 ticket; F2/F3/F4 are confirmations / future notes.
