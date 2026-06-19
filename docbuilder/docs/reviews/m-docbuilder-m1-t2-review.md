# Review — m-docbuilder-m1 t2 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/template-schema.md; docbuilder/docs/doc-spec-schema.md

---

## Packet assessment

Ticket ID + scope: ✅ provided in submission  
Diff: ✅ provided  
Implementation notes: ✅ `m-docbuilder-m1-t2-implementation-notes.md` committed  
Done-check output: ✅ 32/32 tests pass, sheet structure + row counts + aggregate values validated  
t1 implementation notes (backfill): ❌ not present in diff — `m-docbuilder-m1-t1-implementation-notes.md` was listed as first Touch in the t2 prompt but does not appear in the diff. See finding 1.

---

## Findings

1. **[blocking]** `m-docbuilder-m1-t1-implementation-notes.md` is missing from the diff. The t2 prompt stated this as the first action: "write `docbuilder/docs/milestones/m-docbuilder-m1-t1-implementation-notes.md` — backfilling the t1 audit trail." This was the resolution to the blocking finding from the t1 review (t1-review finding 1). The file does not appear in the committed diff. The t1 design decisions (summary_rows vs aggregate_rows distinction, source_key: null pattern) remain in chat only — not in the repo. Contract: aetheris-agents--CLAUDE.md §"Implementation notes"; milestone-methodology.md §1.6. **Fix: write and commit the t1 notes file. Content is already established — see t1-review finding 3 for what it must cover.**

2. **[non-blocking]** The t2 implementation notes (committed) document that `compute_doc.py` accepts `-` as source path (stdin), enabling piped usage. However the t2 done-check in the milestone doc uses a two-step file approach (`> /tmp/raw.json`), and t3–t7 done-checks still reference the old pipe pattern (`fetch_data.py ... | compute_doc.py ... -`). These need to stay consistent — either both use the temp file approach or both use stdin. The `-` support is correct to include; the done-checks just need to agree on which form to use. Non-blocking because the pipeline works either way, but worth aligning before t3 runs.

3. **[non-blocking]** `_run_aggregate` for `count` counts non-empty values (`str(v).strip() != ""`). For `sum` and `avg`, non-numeric values are silently skipped. This asymmetry is reasonable but undocumented — a `count` on a column with blanks returns a different result from what a user might expect ("count of rows" vs "count of non-empty values"). The implementation notes mention the `_fmt` int/float decision but not the count semantics. Worth a one-line note in the doc-spec-schema.md §"Renderer contract" or template-schema.md §"Aggregate" for future template authors. Non-blocking because the behaviour is defensible and the tests cover it.

4. **[question]** The `doc_spec["columns"]` array in the spec carries `{name, type, width}` only — `bold` and `align` are dropped at the column level because they're encoded per-cell. The t3 done-check for `generate_xlsx.py` references "numeric column formatting" by `type`. Renderers will need `type` to apply `#,##0.00` formatting — this is in the spec. But the t3 prompt also says "apply bold and alignment per cell from doc spec flags" — confirm that cell-level `bold`/`align` in the `rows` array is the sole source for those, and column-level `bold`/`align` (from the template) are not needed by any renderer. The implementation notes confirm this is intentional, but the doc-spec-schema.md §"Column" section doesn't explicitly state that `bold` and `align` are intentionally absent at the column level. A one-line note there would prevent a future renderer author from wondering if they're reading a truncated spec. **Not a design question — just a doc gap.**

---

## Cross-ticket notes

- The t1 notes backfill (finding 1) is a process gap that has now appeared across two tickets (t1 and t2). If it appears in t3, it becomes a candidate for CLAUDE.md promotion at milestone end: "implementation notes file is a required deliverable, not optional — write it before submitting the review packet."
- Finding 2 (done-check pipe vs temp-file inconsistency) will affect t3–t7 prompts if not resolved. The milestone doc's done-checks for t3 onward use the old pipe form. If the t2 session confirmed `-` stdin works, the pipe form is fine — but it should be explicit that the t3 done-check pipe form is intentional, not a copy-paste from before `-` was added.
- The two-pass architecture shipped cleanly. The `aggregate_store` approach (re-compute on demand from raw rows rather than pre-keying all combinations) is a good call — worth noting in t1 implementation notes as a design decision that informed the two-pass structure.
