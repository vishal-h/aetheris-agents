# BL-068 — durable home for capability-matrix curation, and eduloka wired (implementation notes)

**Date:** 2026-07-30 · **Touches:** `aetheris-agents/` (assembler, overrides file, tests, docs,
backlog, eduloka section agent), `aetheris/scripts/sprint.sh` (the ninth section-agent line)

---

## The mechanism

`docs/capability-matrix-overrides.json` is committed; `docs/.sections/` is gitignored scratch the
section agents rewrite on every run. `assemble_matrix.py` merges the overrides into the section's
**own table rows** — rewriting the row's source line — *before* any derived value is computed.
That ordering is the whole design: the emitted table and the derived block are computed from the
same post-override rows, so BL-067's claimed == counted invariant is untouched, and an overridden
Tools cell participates in the unique-tools line and the overlap grouping exactly as a generated
one does (proved by `test_override_changes_tool_set_grouping`, which moves an overlap group by
overriding a cell).

Keys: use case → `agents`/`scripts` → row key → field. Agent row key is the file name, or
`file.exs::Label` where one file contributes several rows (the `at1cmd.exs` OrbConfig case);
fields `label`, `tools`. Script row key is the file name; field `purpose`. Top-level keys starting
with `_` are comments.

**An override that matches no row fails the run (exit 1).** A renamed script would otherwise take
its curated purpose out of the matrix silently — precisely the failure the file exists to prevent,
so it is loud and it reddens the sprint. Same reasoning one level up: an *unreadable* overrides
file drops every override at once, so it fails too; an *absent* one only warns (a repo may
legitimately curate nothing).

## Demonstration, not unit-green

The done-check for this ticket is a live regen, and it was run twice (the first exposed the
eduloka defect below):

- Nine section agents ran; the agents reworded **all twelve** curated cells — every m3/m4/m5/m6
  and rig-p9 marker rewritten away, and provenance's Tools cell changed shape again
  (`(MCP servers: corpus_search, lattice)` this time; `(MCP: corpus_search, lattice)` at BL-067).
  So the overrides were load-bearing on 12 of 12, and the check is not vacuous.
- The emitted matrix is byte-identical to `HEAD` in all twelve cells.
- The committed matrix is **the regen's own output**. No restore-from-HEAD, which is the ritual
  this ticket set out to retire.
- Re-running the assembler over the same sections reproduces the file byte for byte.

## Eduloka: wired, and it had never run

`eduloka/` has `eduloka_orchestrator.exs` + 14 scripts — a real surface — so the fact-driven
branch was to wire it, not delete the agent. `SECTIONS` gained `("eduloka", "eduloka")`, sprint.sh
gained the ninth `run_agent` line, and the matrix gained `eduloka 1 / 14` (totals 26/67 → 27/81).

Its first live run ended `run_complete reason: max_steps_reached` at step 15 without writing its
section (read from the trajectory, not inferred): 1 agent + 14 scripts is ~18 tool calls against
`max_steps: 15`. The wired agents already scale this with their surface — provenance 16 scripts →
30, docbuilder 24 → 50 — so eduloka went to 30. The defect had been latent since the file was
written: an agent that is wired nowhere is never run, and an agent that is never run is never
wrong. That is the second half of what BL-068 was really about.

## Mutation checks

Six defects injected into the merge path, each confirmed to fail its intended tests, script
restored pristine afterwards (`38 passed`):

| # | Injected defect | Tests that failed |
|---|-----------------|-------------------|
| N1 | overrides never merged | replaces-cell, tools-flow, grouping, disambiguation, unmatched-fails |
| N2 | derived value updated but the emitted row left generated | replaces-cell, tools-flow, disambiguation |
| N3 | unmatched override no longer fails the run | unmatched-fails |
| N4 | `file::label` key ignored | disambiguation |
| N5 | unreadable overrides treated as no overrides | unreadable-fails |
| N6 | curated Tools cell not re-parsed into the derived tools | tools-flow, grouping |

N2 is the one worth keeping in mind: it is the state where the document's own table and its
derived block disagree, and it is caught because the tests count from the *emitted* document.

## Decisions worth recording

**Overrides carry only hand-written text, not every cell.** Freezing all 24 docbuilder purposes
would stop the section agents from ever updating them. The file holds the eleven rows that carry
milestone provenance plus the one prose Tools cell; everything else stays generated.

**The curated text was extracted from the committed matrix, not retyped** — the artifact that
already held it is the authority, so a transcription slip could not enter the file.

**Sections are no longer strictly verbatim.** They are verbatim *except* overridden cells, which
is a deliberate narrowing of BL-067's rule; the row rewrite preserves every other cell and the
surrounding lines byte for byte, so an un-overridden section is unchanged.

## Forward

- The runbook's "Full regen loses curation" limitation is **deleted** (the done-when required
  removing it, not documenting it), replaced by a **Curated cells** section; "Re-running a single
  section" is now framed as a cost/diff-size convenience rather than a safety measure.
- If a curated script is renamed, the assembler fails until the overrides key is renamed with it.
  That is intended, and the runbook says so.
