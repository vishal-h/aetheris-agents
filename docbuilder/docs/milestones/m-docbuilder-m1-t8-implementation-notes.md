# Implementation notes — m-docbuilder-m1 t8

Ticket: docs sync + capability matrix update + learning promotions (milestone close).

---

## Decisions made

**Capability matrix mechanism was sub-agent based, not a single file.**
The t8 done-check referenced `mix aetheris run agents/capability_matrix.exs` but
no such monolithic file exists. The actual mechanism is individual sub-agents
(`capability_matrix_{uc}.exs`) assembled by `capability_matrix_assemble.exs`,
run via `./scripts/sprint.sh capability_matrix`. Created
`agents/capability_matrix_docbuilder.exs` following the payslip pattern.

**Format characteristics table source.**
The seven-format × seven-feature table in `doc-spec-schema.md` §"Format
characteristics" was compiled from t3–t6 implementation notes and reviews.
The key finding: `merge_ranges` values survive faithfully only in xlsx and pdf.
All other formats silently drop or substitute the value.

**rig--runbook.md carry-over (deferred from t7).**
The t7 milestone scope included a "Runbook update rule" requiring the docbuilder
section to be added to `docs/rig/runbook.md`. It was not added at t7 (only
`docbuilder/runbook.md` was written). Added at t8 as the F5 gap closure — see
`docbuilder/docs/reviews/m-docbuilder-m1-t8-review.md`.

**Third CLAUDE.md promotion (impl notes required).**
The t8 commit (18b9b01) included only 2 of the 3 CLAUDE.md learning promotions.
The third — "implementation notes are a required deliverable" — was missing and
added post-review per F3 verification.

## Open items forwarded to m2

All open items from `docbuilder/milestone.md` §"Open items for m2" apply. No
new items from t8.
