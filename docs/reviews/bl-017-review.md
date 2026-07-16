# Review — BL-017 — round 1

## Decision

**Accept the scoped disable; residual handled via option 1 (BL-018, fix source).**

This packet is the cycle's thesis proven in miniature: BL-016's "the next real
failure hides behind the standing red" wasn't hypothetical — it was these three
`react-refresh/only-export-components` errors, invisible for seven weeks behind
the 28 `set-state-in-effect` ones, surfaced within days of the gate rule landing
by the verify clause written for exactly this. Pausing closeout rather than
stretching scope was the right call.

Per-option reasoning:

- **Option 2 (also disable react-refresh) — rejected on the merits.** Unlike
  `set-state-in-effect`, this rule has a clean, standard, zero-risk fix path
  (`tsc` + build verify the import moves; no test-net problem) and it guards
  something real (HMR correctness). BL-017's reject was justified by
  refactor-risk-without-a-net; that justification does not transfer.
- **Option 3 (re-scope BL-017) — rejected.** BL-017's Touches was "eslint
  config, backlog, nothing else"; six source files plus import-site updates is a
  different artifact boundary. We just spent a cycle establishing that scope
  stretching is how discipline erodes — not worth spending that credibility to
  save one ticket number.
- **Option 1 — chosen.** Keeps both tickets honest: BL-017 closes on its actual
  scope (the decided disable, 31 → 3), BL-018 closes the residual (3 → 0) with
  its own trivially-verifiable done-check.

## Findings

1. **[non-blocking, owned jointly]** The BL-016 gate-line miscount: claude-code
   read only the tail of the eslint output and characterized all 31 as one rule,
   but the review *accepted* that characterized gate line without the tool's
   summary output — the review backstop failed at the same time. This is the
   shakedown friction flagged in BL-016 materializing. Hardening, no new rule
   needed: **gate lines quote the tool's actual summary line** (e.g.
   `31 problems (31 errors, 0 warnings)`), not a characterization of it. Carry it
   as packet practice; promote to CLAUDE.md only if it slips again.

2. **[observation]** The config-comment numbers must carry the corrected count
   (28 errors across ~22 hook sites) rather than the ticket's pre-count (~15
   files / 31), with this packet as the verification ref. Applied in the
   committed comment.

## Cross-ticket notes

- Behavioral gate: `tsc -b` + `bun run build` are the net that makes the BL-018
  source refactor safe without a frontend test runner — the same absence that
  justified *rejecting* the rule in BL-017 does not block *fixing* react-refresh,
  because that fix is verified structurally, not behaviorally.
- **Sequencing / endpoint move:** BL-017's done-check text was written against
  the miscounted "all 31 one rule" premise; per the standing divergence-noting
  rule its done-when becomes "the 28 `set-state-in-effect` errors cleared;
  residual 3 tracked as BL-018 (#69)". `bun run lint → exit 0` is delivered
  *jointly* at BL-018's closeout — one shared export boundary (both statuses, one
  manifest regen, one upload). This is also where BL-016's carried staleness WARN
  clears: its named endpoint moves one ticket later than promised, dated in the
  backlog so the carry stays honest.
