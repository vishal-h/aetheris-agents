# Review — m-docbuilder-m2b t1 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/README.md §"Design decisions" (DOCBUILDER_CONTEXT schema, Drive structure, tenant-first layout)

---

## Packet assessment

Ticket ID + scope: ✅ provided (docs-only, flagged correctly)
Done-check output: ✅ opens packet — wc -l (94 + 121 lines), required-field grep (16), folder-tree grep (27)
Diff: ✅ included (both docs + impl notes)
Implementation notes: ✅ committed — two judgment calls documented, t2 carry-forward flagged proactively

---

## Findings

1. **[non-blocking]** The `context-schema.md` "consumed by" column is a strong addition
   — the field→script fan-out is exactly what t2–t7 implementers need. The `doc_type`
   field documented as the Option A/B switch is correct and keeps the schema as the
   single source of truth. Both judgment calls are the right ones.

2. **[non-blocking]** The per-script validation table creates a maintenance surface. Add
   a one-liner: "Scripts are the authoritative source — consult the script's `main()`
   validation block if in doubt." **Actioned in this commit.**

3. **[non-blocking — carry to t2, decision resolved]** The nested Drive bundle vs flat
   m2a demo layout mismatch is a real t2 concern, surfaced correctly at t1.
   **Resolved: Option A.** Add a nested demo bundle at
   `data/templates/demo/proposal/v1/proposal_v1.*` (copies of the flat files) for
   `fetch_template.py`'s local fallback; leave the flat files untouched (m2a orchestrator
   uses them directly). Clean separation: flat = m2a direct path, nested = m2b
   fetch_template local fallback. **Recorded in the t2 ticket (Touches + Pre-flight).**

---

## Cross-ticket notes

- **`drive-structure.md` §"Tenant onboarding" carries the base-file checklist** from the
  m2a retrospective (`Heading 1`/`Table Grid` styles, per-sheet branding, CSS `@page`
  footer matching docx footer). Right place — the onboarding doc.
- **`GOOGLE_SERVICE_ACCOUNT_FILE`** documented in `drive-structure.md` — needed by
  `fetch_template.py` / `upload_output.py`.
- **t2 pre-flight (recorded in the t2 ticket):** (1) install `google-api-python-client`
  in the mise env; (2) create the nested demo bundle (Option A).

---

**Outcome: zero blocking findings. t1 clear to merge. t2 clear to start.**
F2 actioned in this commit; F3 (Option A) recorded in the t2 ticket.
