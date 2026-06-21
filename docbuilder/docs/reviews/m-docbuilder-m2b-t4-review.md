# Review — m-docbuilder-m2b t4 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/context-schema.md (required fields: client_name, date); docbuilder/docs/drive-structure.md §"Output filename convention"

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 15/15 tests, standalone rename confirmed (before/after with correct `acme_corp_proposal_2026-06-20.*`), 191/191 + 1 skipped full suite
Diff: ✅ included (3 files, 289 insertions, 0 deletions — pure addition)
Implementation notes: ✅ committed — five decisions documented, t5/t7 forward notes

---

## Findings

1. **[non-blocking]** `slugify` strips non-ASCII silently (`"Béta-Co!"` → `"bta-co"`,
   `"Müller GmbH"` → `"mller_gmbh"`) — no transliteration (stdlib only, no `unidecode`).
   Correct and tested. **Actioned:** added a note under `client_name` in
   `context-schema.md` ("non-ASCII stripped — provide an ASCII-safe name if accents matter").

2. **[non-blocking]** `doc_type_base` regex `_v\d+$` is correct for the simple-noun
   doc_type convention (`proposal_v1` → `proposal`). Edge case: a doc_type containing
   `_v\d` near the end (e.g. `revenue_vs_cost_v1`) could mis-strip. Practically
   unreachable given the convention. No action.

3. **[non-blocking]** The standalone done-check renames the live `output/` files in place
   (slightly destructive, but regenerable by any sprint run). No action.

4. **[non-blocking]** `pairs` returned in `KNOWN_EXTS` order, not filesystem order.
   Deterministic; order is irrelevant for the `upload_output.py --files` use. No action.

---

## Cross-ticket notes

- **Full path strings confirmed correct for t5** — `renamed` values pass directly to
  `upload_output.py --files`, no re-join.
- **t7 PHASE D pattern confirmed:** `rename_output.py --output-dir output --filename-prefix
  {doc_type}_{variant} --context '{json}' --output output/renamed.json`.
- **t5 reminder:** add `find_or_create_folder` to `_drive.py` (not inline in
  `upload_output.py`), per the t2 review F-note — already recorded in the t5 Touches.

---

**Outcome: zero blocking findings. t4 clear to merge. t5 clear to start.**
F1 actioned in this commit; F2–F4 are confirmations.
