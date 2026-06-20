# Review — m-docbuilder-m2a t5 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md §"Top-level object"; docbuilder/docs/template-schema.md

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 30/30 tests, pass-through pipeline check (all three fields present), 145/145 full suite
Diff: ✅ included (4 files, 94 insertions, 0 deletions — pure addition)
Implementation notes: ✅ committed — the "template values now authoritative" framing is clear, json renderer behaviour confirmed, pass-through list explicitly closed

---

## Findings

1. **[non-blocking]** The `doc-spec-schema.md` note says renderers can "read them
   unconditionally" because the fields are always present — accurate for what renderers
   *receive*. `generate_json.py` strips top-level metadata, so the new fields do not appear
   in its *output*. The note is correctly worded ("read them from the doc spec") and the
   impl notes acknowledge the json behaviour. No change needed.

2. **[non-blocking]** The two new pass-through tests don't assert that `sheets` content is
   unaffected by adding the new top-level keys. The full suite (145 passed) covers this
   implicitly since all existing sheet-content tests run the same code path. No action.

---

## Cross-ticket notes

- **Pass-through list officially closed.** `table_style`, `data_col_start`, `narrative`
  all flow template → doc spec → renderer. The t2/t3/t4 notes that flagged this list are
  satisfied. t10 summary should note the closure.
- **t8 orchestrator simplification:** does not need to pass `data_col_start`/`table_style`
  as flags (renderers read from the doc spec); only `--base-file` (xlsx/docx) and
  `--template-dir`/`--context` (pdf). Worth stating explicitly in the t8 prompt.
- **`narrative` is now live in the demo doc spec.** t6 (`render_template.py`) and t7
  (`generate_pdf.py` narrative mode) can rely on it flowing through — t6's CLI done-check
  can use the real pipeline doc spec rather than injecting `narrative` manually.
- **t4 F1** (declared-but-unconsumed source note in template-schema.md): flagged here as
  possibly still open — **correction: already resolved in commit 6d1d382** (the
  `data_sources` field description now reads "A source not referenced by any sheet is
  permitted — it is fetched by the orchestrator but not consumed"). No t10 carry needed.

---

**Outcome: zero blocking findings. t5 is clear to merge. t6 is clear to start.**
