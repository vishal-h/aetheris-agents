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
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `1013a95` | 2026-07-25 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `eeb37a1` | 2026-06-27 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `f624337` | 2026-07-24 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `1ebe971` | 2026-07-21 |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `8021a59` | 2026-07-23 |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `af56a57` | 2026-07-24 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` | 2026-07-17 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `0a0439f` | 2026-07-20 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `602bdf5` | 2026-06-19 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-07-25 |

> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical
> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit
> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.
> Mirror re-verified byte-identical at this export (`diff -q`, 2026-07-25); the
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

Exported: 2026-07-25 at aetheris-agents `aad8415` / aetheris `af56a57` (post-arc export — the
verify-effect-classes arc: BL-049, the BL-047 cluster, BL-041(a)). 24 rows: **24 carried, none
added, none dropped.** Four rows re-pinned, clearing the four standing staleness WARNs:
`backlog-2026-06.md` (`f0df85a`→`f624337`), `aetheris-agents--CLAUDE.md` (`c2729ac`→`1013a95`),
`aetheris--determinism-contract.md` (`9b2b102`→`af56a57`), and `aetheris--runbook.md`
(`a935038`→`8021a59`).

**Two watermark fields, kept distinct.** The `Exported:` line names the boundary commit
`aad8415` — aetheris-agents HEAD, the BL-041(a) light review packet, a
non-manifest-tracked artifact (`docs/reviews/bl-041a-review.md`) that moves no row. The
`aetheris-agents--CLAUDE.md` *row* pins `1013a95`, CLAUDE.md's last touch (the BL-041(a)
promotion, `HEAD~1`). The boundary commit and the row's last-touch are different fields and are
not the same hash this cycle.

**Repo push state.** The harness is synced: `origin/main` = HEAD = `af56a57`; the whole
verify-effect-classes cluster (`a926631` BL-049 through `af56a57` BL-047) was pushed in the
BL-047 session. The determinism-contract content exported here is HEAD = origin = `af56a57`
(carrying BL-049's and BL-047's §5/§3 edits) — the harness is **not** behind. Only
aetheris-agents carries unpushed local commits: 2 ahead of `origin` (`f624337`) before this
regen, 3 after, push held for the human.

**Upload is remove-all then upload-all against the full 24-row set** — not a diff of the four
re-pinned rows. Nineteen data rows are unchanged since the previous export and would look like
"nothing to re-upload" to any hash-driven shortcut; do not optimise the upload down. This is the
standing discipline that also covers the manifest-blind direction the header warns about (a file
uploaded without a regen leaves the record silently under-describing project knowledge).

**BL-034 — corrected finding, authored fresh; not fixed (deliberate).** The prior manifest
claimed that following the refresh prompt's closing append step would reproduce a "born-stale
instance at `628f15f`". **That claim is withdrawn as false.** A clean check-8 sweep of all 38
committed manifests found **no** born-stale instance — `628f15f` never born-staled a row. BL-034
remains a **latent** vacuity: `prompts/bl-002-refresh-project-knowledge.md` closes by appending a
drift-baseline line to `docs/rig/current-state-2026-06.md` — a file this table tracks — *after*
the manifest is written, which *would* born-stale that row **if the step were followed
literally**. It has not been observed to fire and is not asserted to have; it remains BL-034's to
fix. At this export the append was **not performed** (the manifest write is this session's only
write to a tracked file), so `current-state-2026-06.md` stays pinned `f723ee5`, matching HEAD.

Previous export: 2026-07-22 at aetheris-agents `d11d4fb` / aetheris `1ebe971` (b1–b3 batch close —
BL-028, BL-029/BL-004, BL-031, §7 promotion).
