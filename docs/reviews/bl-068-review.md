# BL-068 — review (r0, ship)

**Ticket:** BL-068 — durable home for capability-matrix curation + resolve eduloka.
**Commits reviewed:** agents `e60bcfd` (overrides mechanism, tests, docs, regenerated matrix,
eduloka `max_steps` fix) and `63f48e1` (row closed), harness `fd9ac48` (ninth section-agent line).
**Reviewer:** claude-ui. **Date:** 2026-07-30.
**Verdict:** ship — done-when met by demonstration (full nine-agent regen, 12/12 curated cells
reworded by the agents and 12/12 shipped byte-identical to HEAD, matrix is the regen's own
output). No findings against the commit. One forward note (bare-file override keys), actioned
below.

Reviewer's message, verbatim:

---

Read complete — full packet through §7. The one thing that had to be shown is shown.

## BL-068 review — Ship

**Done-check opens with the demonstration, not an assertion.** §1a: a full nine-agent regen ran, the matrix committed *is that run's own output*, and all **12/12** curated cells were reworded by the section agents this round (the "agent wrote vs shipped" table shows every milestone marker — m3/m4/m5/m6/rig-p9, the Jinja2/Pandoc/deprecation prose — present in *shipped*, absent in *agent-wrote*), yet `curated_cells.py` diff of the regen against HEAD is `IDENTICAL — 12/12 survived`. So every override was load-bearing on every cell: survival is the mechanism, not the agents happening to agree. The restore-from-HEAD ritual BL-067 needed is genuinely retired, which was the done-when. This is exactly the claim I said I'd only accept by diff, and it's carried by diff.

**The mechanism is load-bearing and fail-loud.** Overrides merge into the section's own table lines *before* any derived value is counted (`apply_overrides` rewrites `lines[row["line"]]`), so a curated Tools cell flows into the unique-tools line and the overlap tables — claimed == counted is untouched (test_counts_still_claimed_equals_counted_with_overrides, and the 24 BL-067 tests unchanged-green). An override matching no row **exits 1** — a renamed script can no longer drop its curation silently, which is BL-068's own bug turned into a gate. Unreadable-but-present overrides → exit 1 (drops *all* curation, the exact failure the file exists to prevent); absent → warn + assemble; `_comment` keys skipped.

**Tests are non-vacuous.** N1–N6 each fail their intended tests; N2 is the one that matters — derived block updated but emitted row left generated is caught *only because the tests count from the emitted document*, so the table-vs-derived-block disagreement can't hide. Byte-stable (§1b), 38/38, whole suite 89.

**Eduloka: wired, not deleted — and wiring found a real defect.** Correct call per your earlier question: it had a real surface (orchestrator + 14 scripts), so it joins SECTIONS with an appropriate section; functionality was never required. Wiring exposed why it had never appeared — `max_steps: 15` against ~18 tool calls, so its first-ever live run hit `max_steps_reached` before writing. Bumped to 30, matching the scaling the other agents already carry. Fact-driven, not asserted.

**My earlier "nine lines stay" error is resolved here** — there were eight wired; fd9ac48 adds the ninth (eduloka) run_agent line and the assembler message goes 8/8 → 9/9. Consistent across sprint.sh, the assembler output, and the backlog close.

**Gates green both repos, and hex.audit is genuinely green** — BL-066 landed first, so there's no tracked-red carry to name; the only difference from BL-067's gate table, correctly called out. The two `project_knowledge` WARNs are this ticket's own manifest-staleness, exempt under BL-009.

**One forward note (not a finding against the commit).** A *bare*-file agent key (no `::label`) applies to **every** row sharing that filename — the inner loop re-matches `agent["file"]` on each row without consuming the key. Harmless today (the one keyed agent cell, provenance `search_agent.exs`, is single-row), but if a bare-keyed file later gains a second RunConfig, one curated cell would silently land on both rows. Multi-row files should always use `file::label` keys; worth a line in the overrides-file doc so it's a rule, not a trap.

**Coverage boundary:** read, not run. `curated_cells.py` source not in the packet — but its output isn't taken on faith: the independent "differ: True" table plus the milestone markers (which exist only in the overrides file) plus N2 corroborate that the shipped matrix genuinely carries the curated text, so the IDENTICAL result isn't vacuous.

**Recommendation:** file this review verbatim to `docs/reviews/bl-068-review.md`, commit, push. That closes the last open m1-cloudcost follow-up. After it, the only outstanding non-ticket item is the batched export/manifest refresh (clears the two standing `project_knowledge` staleness WARNs at the next export boundary) — and confirm the reserved IP 168.144.13.150 is deleted if you haven't already, since t5's live run is long done.

---

**Action taken on the forward note.** Confirmed against `apply_overrides` — the bare key is not
consumed, so it re-matches on every row with that file name. Two changes in the same commit as
this review: the runbook's **Curated cells** key rules now state that a bare file key applies to
every row of that file and that multi-row files must use `file.exs::Label`; and
`test_bare_file_key_applies_to_every_row_of_that_file` pins the semantics, so a future change to
per-row matching has to be deliberate rather than accidental. Suite 90 passed.
