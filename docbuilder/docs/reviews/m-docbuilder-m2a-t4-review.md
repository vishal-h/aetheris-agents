# Review — m-docbuilder-m2a t4 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/template-schema.md §"Validation rules", §"DataSource"; docbuilder/README.md §"Design decisions" (multi-source)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 28/28 tests, multi-source pipeline check passes, 143/143 full suite
Diff: ✅ included (5 files, 174 insertions, 27 deletions)
Implementation notes: ✅ committed — the Summary-keeps-summary_rows decision is documented clearly with rationale

---

## Findings

1. **[non-blocking]** "A declared-but-unconsumed source is allowed by design" is the
   right contract (in code + notes) but was not in `template-schema.md`. A one-liner
   in the `data_sources` field description would make it explicit for template authors.
   **Actioned in this commit** — added "A source not referenced by any sheet is
   permitted — it is fetched by the orchestrator but not consumed." to the field
   description.

2. **[non-blocking]** `test_cli_multi_source_succeeds` passes both raw source files and
   asserts `["Line Items", "Summary"]` — it verifies that passing two source files
   doesn't break the pipeline, but does not verify the `summary` source data was
   consumed (Summary uses `summary_rows`). The unit test `test_multi_source_two_sheets`
   is what proves actual two-source consumption. Both are correct and useful; noting the
   distinction.

3. **[question — t8]** The forward note ("the `summary` file being fetched but not
   rendered is intentional — not a bug") should be explicit in the t8 prompt so it isn't
   flagged as an error. **Actioned in this commit** — added an explicit note to the t8
   `Claude-code prompt` in `m2a-milestone.md`: fetch every declared source regardless of
   whether a sheet reads it; do not skip the unconsumed source.

---

## Cross-ticket notes

- **The Summary-keeps-summary_rows decision is the right call.** The two-pass
  `aggregate_ref` demo is the highest-value thing the demo template shows. The second
  source being declared-but-not-consumed is a correct design pattern: the orchestrator
  fetches infrastructure, templates decide what to render. **Carry to t10:** highlight
  this declared-but-unconsumed-source pattern in the milestone summary.
- **t5 pass-through list unchanged:** `table_style`, `data_col_start`, `narrative`. No
  new fields in t4 need passing through.
- **t8 orchestrator:** fetch both `main` and `summary`, pass both to `compute_doc.py`;
  `summary` being unused by any sheet is intentional (now stated in the t8 prompt).

---

**Outcome: zero blocking findings. t4 is clear to merge. t5 is clear to start.**
Both non-blocking doc items (F1, F3) actioned in the same commit as this review.
