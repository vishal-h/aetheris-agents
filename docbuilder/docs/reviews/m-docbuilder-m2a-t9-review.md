# Review — m-docbuilder-m2a t9 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/README.md §"Template model" (catalogue.json structure)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 7/7 tests, catalogue JSON valid and fully printed, structure verify passes, gitignore tracked OK, 167/167 full suite
Diff: ✅ included (5 files, 203 insertions, 0 deletions — pure addition)
Implementation notes: ✅ committed — standalone-in-m2a decision documented, m2b seam (`--templates-dir`) explicitly noted

---

## Findings (t9 — all non-blocking)

1. **[non-blocking]** Explicit `!templates/demo/catalogue.json` whitelist is
   belt-and-suspenders (already un-ignored by `!templates/demo/`). Correct and
   acknowledged.

2. **[non-blocking]** Error messages surface the internal filesystem path in the JSON
   stderr output. Fine for m2a (developer-facing); worth noting for m2b when
   `list_templates.py` may run in a multi-tenant context where the path could appear in
   logs.

3. **[non-blocking]** TOCTOU between `path.exists()` and `path.read_text()` in
   `load_catalogue()` — a file vanishing in between would escape as an unhandled
   exception caught by `main()`'s `except Exception`. Practically unreachable.

---

## t8 robustness signal — assessment & decision

The 8 LLM scratch files found during t9 are a meaningful signal: the t8 orchestrator
could not reliably round-trip the ~8K doc-spec JSON through `write_file content: <exact
stdout>`, and improvised `/tmp`-writing shell scripts. The run still reached
`status: done` with all three outputs, but not via the intended path.

**Root cause:** reproducing a large opaque JSON string verbatim as a `write_file`
`content:` field is awkward for an LLM.

**Fix (accepted):** add `--output FILE` to `compute_doc.py` — when provided, write the
doc spec JSON to the file and print only the path to stdout (stdout default preserved,
backward-compatible). The orchestrator then computes straight to
`output/pipeline_spec.json` with no `write_file` for the spec, removing the large-blob
round-trip. Consistent with "scripts do"; reduces orchestrator step count.

**Timing decision:** absorbed into **t10** (recorded in the t10 Touches + scope). t10
will add `--output FILE` to `compute_doc.py`, simplify the orchestrator prompt (drop the
spec `write_file`), and re-run the sprint to confirm the cleaner path.

---

## Cross-ticket notes

- **t9 is clean and correctly scoped** — standalone, m2b seam explicit, `load_catalogue()`
  factored for testing.
- **t10 Touches (confirmed/updated):** capability matrix regen (new scripts
  `render_template.py`, `list_templates.py`), `requirements.txt` (pinned),
  `_table_html.py` shared helper, `rig--runbook.md` m2a additions, milestone summary,
  **and `compute_doc.py --output FILE` + orchestrator simplification** (this review).
  (The `template-schema.md` declared-but-unconsumed note / t4 F1 is already resolved in
  6d1d382 — not outstanding.)
- **Zero blocking findings. t9 clear to merge. t10 clear to start.**
