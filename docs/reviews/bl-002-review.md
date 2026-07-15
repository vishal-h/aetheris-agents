# Review — BL-002 — round 1

## Findings

1. **[non-blocking]** Flag 1 (harness ROADMAP touch): deviation accepted, correctly executed and correctly noted. The defect was in my prompt — "ROADMAP.md" unprefixed the same week we instituted the prefix rule. No rework; the finding exists so the pattern is on record.

2. **[blocking — for BL-003, not this ticket]** 76 orphaned `running` rows vs the canonical "five May rows" is a material scope change, not a footnote. Per §1.1 the backlog BL-003 text must be corrected *before* BL-003 is prompted: fixture framing, sweep-threshold expectations, and the done-condition ("the five May rows are swept on first run") are all written against stale reality. Also changes the risk profile — at 76 rows the sweep's paused-run exclusion logic (`agent_waiting` + unexpired `wait_condition`) is protecting real state, not an edge case. Suggested fix: I draft the corrected BL-003 section, human approves, then prompt.

3. **[question]** Manifest coverage: `milestone-methodology.md` and `triad-loop.md` are in the claude-ui project knowledge (I'm reading them now) but don't appear in the 16-entry export set. If they're not manifest entries, staleness detection has a blind spot on the two docs governing the process itself. Are they manifest-tracked?

4. **[question]** The export includes 5 research briefs, but the harness roadmap cites 7 — `activegraph` and `universal-ingestion-extraction` are absent, and activegraph is the cited basis for Horizon 0 (`caused_by`) and Horizon 1 (fork), i.e. the next design conversations claude-ui will be asked to have. Deliberate exclusion or gap?

## Cross-ticket notes

- **Third instance of ticket text diverging from repo state** (BL-001 expectations, BL-015 numbering collision, BL-002 Touches path). §7 threshold met. Proposed standing rule for CLAUDE.md, to land with BL-009's doc touch: *"Ticket text that quotes repo state (counts, paths, expected outputs) cites the commit it was verified against; claude-code treats divergence as a deviation to note, never silently follow."* Source: BL-001, BL-015, BL-002.

---

## Resolution notes (claude-code)

- **Finding 1:** acknowledged, no rework.
- **Finding 2:** corrected BL-003 draft produced for human approval (below / in packet). Not committed until approved — a backlog edit re-stales the just-regenerated manifest, so it batches with the BL-003 prompt or a deliberate re-export.
- **Finding 3:** confirmed — see packet (manifest-tracked status of the two process docs).
- **Finding 4:** confirmed — see packet (file-existence check for the two cited briefs).
- **Cross-ticket rule:** accepted as a BL-009 doc-touch item.
