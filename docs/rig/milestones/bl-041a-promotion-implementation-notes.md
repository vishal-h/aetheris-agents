# BL-041(a) — implementation notes

§7 promotion: the manifest-staleness done-check runs **post-commit**. Docs-only edit to
`aetheris-agents/CLAUDE.md` — a new learning rule + a one-line reconciliation of the doc-sync
"When to run" line. Human-ratified wording from `docs/reviews/bl-041a-promotion-draft.md`.

Applied at agents HEAD `f624337`, harness `af56a57`.

## What landed

Two edits, both in `aetheris-agents/CLAUDE.md`'s "Definition of done — doc sync" section,
verbatim from the ratified draft:

- **Edit 1** — the new rule, inserted immediately after the strict-mode exemption paragraph
  (the `--strict` / `project_knowledge` exemption its own text points at with "the strict-mode
  exemption above").
- **Edit 2** — "When to run" reconciled: "zero *unexplained* WARN findings", with the
  `project_knowledge` (check 8) portion meaningful only post-commit, cross-referencing the new
  rule ("see the learning rule below").

Both cross-references resolve in place: Edit 2's "below" and Edit 1's "above" both point at the
correct adjacent paragraphs.

## The one divergence, caught before editing

The draft's first version placed Edit 1 "immediately after the **Silent-wrong-answer** rule in
the current learning section." Verified at HEAD: that rule lives in the **harness**
`aetheris/CLAUDE.md` "Continuous learning" section (line 550), **not** in this repo — the agents
`CLAUDE.md` learning sections are `m1-docbuilder … BL-007`, none carrying it. Following the
literal anchor would have (a) made BL-041(a) a two-repo edit, contradicting "docs-only edit to
aetheris-agents/CLAUDE.md"; (b) dangled the rule's own "strict-mode exemption above"
cross-reference (no such section in harness); and (c) put the manifest staleness WARN on
`aetheris--CLAUDE.md` instead of the `aetheris-agents--CLAUDE.md` the done-check names.

Reported rather than forced (the doc-sync section's own "divergence between ticket text and
repo reality — a deviation to note, never to silently follow" rule, applied to the ticket
landing it). Human chose the doc-sync-section placement; the draft was corrected to match and
the Silent-wrong-answer reference kept as an explicit **harness** cross-reference, discoverable
because both `CLAUDE.md` learning sections are read together.

Edit 2's "When to run" Before block was confirmed to match HEAD **verbatim** (unchanged since
`c2729ac`) — no divergence there.

## Done-check ordering — the rule governs its own landing

`aetheris-agents/CLAUDE.md` is manifest-tracked (`aetheris-agents--CLAUDE.md` → `CLAUDE.md`,
manifest `c2729ac`), so this edit re-stales that manifest entry. Per the rule just landed, the
`drift_check --strict` done-check is run **post-commit** (a pre-commit run would read the
pre-edit hash and miss the staleness — the vacuity the rule names). The expected
`project_knowledge` staleness WARN for `CLAUDE.md` is **named, not chased**; it clears at the
next export boundary. Post-commit `--strict` output is in the review packet
(`docs/reviews/bl-041a-review.md`) and exits 0 (staleness is strict-exempt).

## Scope held

Untouched, per the ticket: the strict-mode `project_knowledge` exemption and its rationale,
`drift_check.py`, and every other learning rule. The tooling guard that would make the vacuity
mechanically detectable is **BL-041(b)** (deferred, batched with BL-036) — out of scope.

## Next (not this session)

This is a CLAUDE.md learning-section change, so a **full restart** is due after it commits. The
manifest/export refresh (BL-002-style, whose own done-check this rule now governs) and authoring
the withdrawn `628f15f` born-stale narrative fresh so it is not copied forward are the **next
session's** work — explicitly not started here. Push held.
