# Project Knowledge Manifest

This file records which documents are uploaded to the Claude.ai project and at
what commit they were exported. Its purpose is drift detection: a future session
can compare the `commit` column against `git log -1 --format=%h -- <path>` in
the owning repo to determine whether the project knowledge is stale.

Check 8 of `scripts/drift_check.py` (`project_knowledge`) parses this table
automatically and emits WARN for any stale entry. See **BL-002** in
`docs/backlog-2026-06.md` for the refresh convention and
`prompts/bl-002-refresh-project-knowledge.md` for the exact row format.

Refresh trigger: milestone end, or before any handoff session.

**Uploads happen only as part of an export boundary — the manifest is regenerated
and included in the same set.** The check compares this file against git, so it
detects the repo moving ahead of an export (expected mid-cycle staleness, a
strict-exempt WARN). It cannot detect the reverse: a file uploaded without a regen
leaves the manifest silently under-describing project knowledge, and drift reports
green while the record is wrong. The tooling is blind in that direction; the
discipline is what covers it. Source: BL-022 filing, 2026-07-17.

---

| export name | repo path | repo | commit | last changed |
|-------------|-----------|------|--------|--------------|
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `c39bf7e` | 2026-07-20 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `d0690a6` | 2026-07-21 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `f723ee5` | 2026-07-20 |
| `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` | 2026-07-20 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `c2729ac` | 2026-07-21 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `eeb37a1` | 2026-06-27 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `f0df85a` | 2026-07-21 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `1ebe971` | 2026-07-21 |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `a935038` | 2026-07-21 |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `9b2b102` | 2026-07-21 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` | 2026-07-17 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `0a0439f` | 2026-07-20 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `602bdf5` | 2026-06-19 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-07-22 |

> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical
> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit
> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.
> Mirror re-verified byte-identical at this export (`diff -q`, 2026-07-22); the
> mirror's own last change is `b1fd73f`, which is why it carries no manifest row —
> the row tracks the canonical copy, and a second row would drift against it.

> **What this table does not include, by rule.** Milestone working artifacts —
> `docs/reviews/*.md`, `*-implementation-notes.md`, scan files — are not exported.
> They are the record of *how* a decision was reached and are read from the repo by
> the sessions that need them; project knowledge carries standing reference docs.
> The two milestone-tree exceptions (`rig--protocol.md`, `rig--bl-007-milestone.md`)
> are milestone *specifications* that later work is written against, not review
> history. Applied at BL-007: the milestone README is in; the §7 scan file
> (`bl-007-t5-section7-scan.md`) and the six t*-notes/review files are out.
> Re-applied unchanged at the b1–b3 export: all eleven docs the batch added are
> working artifacts — seven `docs/reviews/*.md` (the BL-028/029/031 reviews, the
> promotion review and notes, and the §7 draft/adjudication pair, which is review
> history rather than specification) and four `*-implementation-notes.md` (three in
> `docs/rig/milestones/`, one in the harness at
> `docs/aetheris/milestones/bl-028-implementation-notes.md`). The batch produced no
> milestone *specification* doc to sit beside the two exceptions — its specifications
> are the BL-0xx backlog rows, already exported inside `backlog-2026-06.md`.
> `docs/handoffs/handoff-bl007-close-2026-07-20.md` is also out: handoffs have never
> carried a manifest row.

---

Exported: 2026-07-22 at aetheris-agents `d11d4fb` / aetheris `1ebe971` (b1–b3 batch close —
BL-028, BL-029/BL-004, BL-031, §7 promotion). 24 rows: **24 carried, none added, none
dropped.** Seven rows re-pinned, clearing the seven standing staleness WARNs: `rig--specs.md`,
`rig--runbook.md`, both `CLAUDE.md`s, `backlog-2026-06.md`, `aetheris--runbook.md`,
`aetheris--determinism-contract.md`.

**Reconciliation from the previous export (§t5 D6) — resolved by procedure.** Six entries
were listed as exported but absent from the live project knowledge: the five research briefs
(`jiyi`, `skill-mining`, `dirge`, `coming-loop`, `weng`) and `rig--architecture.md`. This
export closes that gap without needing to track it, because the upload instruction is
**remove-all then upload-all against the full 24-row set**, not a diff-based re-upload of
changed rows. That is the standing discipline, and it is what covers the manifest-blind
direction the header warns about — four of those six are unchanged since the last export and
would look like "nothing to re-upload" to any hash-driven shortcut. Do not optimise the
upload down to the seven re-pinned rows.

**BL-034 observed at this export, not fixed (deliberate).** `prompts/bl-002-refresh-project-knowledge.md`
closes by appending a drift-baseline line to `docs/rig/current-state-2026-06.md` — a file
this table tracks — *after* the manifest is written, so that row would be born stale. At
this export `current-state-2026-06.md` was pinned `f723ee5` and matched HEAD exactly (it was
not among the seven WARNs); following that step literally would have made it a born-stale
eighth, reproducing the 2026-07-17 instance at `628f15f`. The append was therefore not
performed and remains BL-034's to fix; the manifest write was this session's only write.

Previous export: 2026-07-20 at aetheris-agents `d57c61b` / aetheris `7e77951`
(BL-007 #48 closeout, Phase B).
