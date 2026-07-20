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
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `6dd2d55` | 2026-07-19 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `f723ee5` | 2026-07-20 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `f723ee5` | 2026-07-20 |
| `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` | 2026-07-20 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `d89641f` | 2026-07-20 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `eeb37a1` | 2026-06-27 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `d57c61b` | 2026-07-20 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `7e77951` | 2026-07-20 |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `7ccdccf` | 2026-07-18 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` | 2026-07-17 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `0a0439f` | 2026-07-20 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `602bdf5` | 2026-06-19 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-07-20 |

> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical
> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit
> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.
> Mirror re-verified byte-identical at this export (`diff -q`, 2026-07-20); the
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

---

Exported: 2026-07-20 at aetheris-agents `d57c61b` / aetheris `7e77951` (BL-007 #48 closeout,
Phase B). 24 rows: 21 carried, **3 added** — `rig--bl-007-milestone.md`,
`aetheris--determinism-contract.md`, `aetheris--activegraph-brief.md` (§t5 D6's export
clause). None dropped.

**Reconciliation carried into this export (§t5 D6).** Six manifest entries were listed as
exported but are **absent from the live project knowledge** — the five research briefs
(`jiyi`, `skill-mining`, `dirge`, `coming-loop`, `weng`) and `rig--architecture.md`. That is
the manifest-blind direction this file's header warns about, and the tooling cannot see it:
their hashes match git, so the check reports them green. Four of the six are unchanged since
the last export and would otherwise look like "nothing to re-upload" — they must be uploaded
regardless. The discipline is what covers this, not the drift check.

Previous export: 2026-07-17 at aetheris-agents `628f15f` / aetheris `19c08be`
(BL-022 #73 closeout).
