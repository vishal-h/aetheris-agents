# Review — m-docbuilder-m1 t6 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/doc-spec-schema.md; docbuilder/docs/milestones/m-docbuilder-m1-t5-implementation-notes.md §"t6 notes"

---

## Packet assessment

Ticket ID + scope: ✅ provided  
Diff — all 8 files: ✅ provided (4 scripts + 4 test files)  
Implementation notes: ✅ `m-docbuilder-m1-t6-implementation-notes.md` — present, detailed, and notably includes a "Known limitations" section  
Done-check output: ✅ 44/44 tests pass (0.79s), all four format pipelines confirmed  
Pipeline file listing: ❌ missing — the done-check script runs `ls -lh output/proposal.{fmt}` for each format, but those lines are not in the packet. Minor — the test output provides sufficient confidence, but the file listing is part of the specified done-check.

---

## Findings

1. **[non-blocking]** Pipeline file listing absent from done-check output. The t6 done-check script includes `echo "$fmt: $(ls -lh output/proposal.${fmt} 2>/dev/null || echo MISSING)"` for each format, but these lines don't appear in the packet. 44/44 tests passing (including CLI integration tests that verify file existence) provides sufficient correctness confidence — not returning the packet for this alone. Note for t7: include all done-check output lines, not just the pytest block.

2. **[non-blocking]** `generate_json.py` does not preserve row type (`header`, `data`, `aggregate`) in the output. The implementation notes document this explicitly: "Consumers cannot distinguish aggregate rows from data rows." This is a documented design choice (clean data contract). However for the JSON format specifically, where the consumer is likely a developer or another system, preserving row type as metadata alongside the values would add useful context at near-zero cost (one extra key per row). Worth revisiting in m2 when the registry and delivery features land — template authors will want to know what they can extract programmatically. Non-blocking — the current choice is deliberate and documented.

3. **[non-blocking]** `test_special_chars_quoted` in `test_generate_csv.py` has a three-way `or` assertion:
   ```python
   assert '"say ""hello"""' in text or '"say \\"hello\\""' in text or 'say "hello"' in text
   ```
   The third branch (`'say "hello"' in text`) is always true since the raw value appears in the input and `csv.writer` would quote it. This makes the assertion effectively always pass regardless of quoting behaviour. The intent (verify CSV quoting of embedded quotes) is correct but the test doesn't actually distinguish between correct quoting (`"say ""hello"""`) and no quoting at all. Non-blocking — csv.writer is stdlib and handles quoting correctly, but the test's third branch makes it weaker than intended.

4. **[non-blocking]** `generate_md.py` has an unused variable: `ncols` is computed on line 25 (`ncols = len(sheet["columns"]) if sheet["columns"] else (len(rows[0]["cells"]) if rows else 0)`) but never referenced anywhere in the function. The separator is generated from `len(row["cells"])` directly. Non-blocking — dead code, no functional impact. Clean-up candidate.

---

## Cross-ticket notes

- **merge_ranges silently dropped across t4, t6** — now four renderers (docx, csv, json, xml, md) silently drop merge_range data. Only xlsx and pdf preserve it. The t6 implementation notes document this in a "Known limitations" section — this is the right place and the right level of detail. t8 docs sync should consolidate the per-renderer merge_range behaviour into a single reference table in the README.
- **JSON row type not preserved (finding 2)** — worth a one-line note in `docs/doc-spec-schema.md` §"Renderer contract" or a new §"Format characteristics" table recording which formats preserve which doc spec features (merge ranges, row types, bold, alignment). This would be a useful addition in t8.
- **Implementation notes quality** — the t6 notes are the strongest of the milestone so far: each renderer has a dedicated design section, the known limitations section is explicit and honest, and the t7 notes give the orchestrator author a clear starting point. This sets a good standard for t7/t8.
- **"done-check output first" instruction worked** — packet opened with the full pytest -v block. The only gap is the pipeline file listing (finding 1). Pattern is established.
- **Zero blocking findings. t6 is clear to merge and t7 is clear to start.**
