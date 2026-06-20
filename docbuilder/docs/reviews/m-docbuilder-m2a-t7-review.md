# Review — m-docbuilder-m2a t7 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/README.md §"PDF rendering modes"; docbuilder/docs/doc-spec-schema.md §"Renderer contract"

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 17/17 tests, narrative PDF confirmed (19K, %PDF magic bytes), narrative-path verification shows genuine template rendering (Acme Corp, Net 30, Terms & Conditions, `<table>`), 160/160 full suite
Diff: ✅ included (3 files, 202 insertions, 3 deletions)
Implementation notes: ✅ committed — subprocess/temp-file decision documented, t6-review F4 addressed, fallback-path behaviour explained, narrative path genuinely verified

---

## Findings

1. **[non-blocking]** Temp file pattern reviewed: `mkstemp()` → `os.fdopen(fd, ...)`
   in a `with` block inside `try` → `finally: os.unlink`. The fd is closed before
   `subprocess.run()` and the temp file removed regardless. Confirmed clean.

2. **[non-blocking]** The existing PDF CLI tests now exercise the `narrative present,
   no --template-dir → fallback + warning` path (the demo spec carries `narrative`
   from t5). None assert `stderr == ""`, so they pass. The new
   `test_structured_mode_no_warning` provides explicit structured-path coverage
   (no narrative block → structured, no warning, `%PDF`). Coverage adequate.

3. **[non-blocking]** `Terms &amp; Conditions` in the done-check output is
   python-markdown's correct HTML escaping of `&` in prose, not a bug in `_esc()`.

4. **[question — t8]** `DOCBUILDER_CONTEXT` should resolve to `"{}"` at the orchestrator
   level when unset, not pass an empty string (`render_template.py` would fail
   `json.loads("")`). **Actioned:** the t8 prompt now states this explicitly
   (`System.get_env("DOCBUILDER_CONTEXT") || "{}"`, treat `""` as absent; always pass
   `--context "{}"` not empty).

---

## Cross-ticket notes

- **Narrative path genuinely verified** via the done-check HTML inspection (prose +
  substituted vars + `<table>`), proving the `render_template.py` subprocess output is
  used, not the structured fallback.
- **t6-review F4 addressed:** the `--spec` (not `--input`) temp-file approach is
  implemented and documented.
- **t10 items outstanding (confirmed):** (a) `docbuilder/requirements.txt` pinned;
  (b) `_table_html.py` shared helper to dedupe `_build_html` / `render_template._render_table`.
  Both are already in the t10 Touches (added at t6).
- **t4 F1** (declared-but-unconsumed source note in template-schema.md): flagged here as
  "still open" — **correction: already resolved in commit 6d1d382** (the t5 review
  recorded the same correction). The `data_sources` field description already carries
  the note; verified present. No t10 carry needed.

---

**Outcome: zero blocking findings. t7 is clear to merge. t8 is clear to start.**
F4 actioned in this commit; F1–F3 are confirmations (no action).
