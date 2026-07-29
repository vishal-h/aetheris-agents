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
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `b5e8eee` | 2026-07-26 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `c0977c2` | 2026-07-25 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `7d6013a` | 2026-07-26 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `f723ee5` | 2026-07-20 |
| `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` | 2026-07-20 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `9afd8e7` | 2026-07-29 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `9afd8e7` | 2026-07-29 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `6abc3e8` | 2026-07-29 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `013c09d` | 2026-07-29 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `57d90d2` | 2026-07-29 |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `ae0c510` | 2026-07-26 |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `915d582` | 2026-07-25 |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `1ab24d8` | 2026-07-26 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` | 2026-07-17 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `0a0439f` | 2026-07-20 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `602bdf5` | 2026-06-19 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-07-29 |

> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical
> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit
> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.
> Mirror re-verified byte-identical at this export (`diff -q`, 2026-07-29); the
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

> **Re-applied unchanged at this (fork-arc) export.** The cycle added **fifteen**
> working artifacts and no standing reference doc: nine `docs/reviews/*.md` in agents
> (the BL-030 scout, review and three packets; the BL-038 review; the BL-039 scout,
> review and packet), four `*-implementation-notes.md` in agents
> `docs/rig/milestones/` (BL-038 and BL-030 r0/r1/r2), and two in the harness
> `docs/aetheris/milestones/` (BL-030, BL-039). The harness also gained
> `docs/reviews/bl-039-contract-draft.md` — **RATIFIED contract wording, and still
> out**: §8's artifact is the *record of ratification*; the ratified text itself
> lives in `determinism-contract.md`, which is exported and re-pinned below. Two
> handoffs (`handoff-containment-cluster-close-2026-07-25.md`,
> `handoff-fork-arc-close-2026-07-26.md`) are out as always. As at BL-007 and b1–b3,
> this cycle's specifications are the BL-0xx rows, already carried inside
> `backlog-2026-06.md`.

> **m1-cloudcost export — the rule applied in both directions, one add.** The
> milestone produced fourteen working artifacts, all out: five
> `cloudcost/docs/t*-implementation-notes.md`, and nine `docs/reviews/*.md` (the t1–t5
> reviews, the t4 browser-gate record, and the close's §7 promotion draft — *promotion
> wording is review history; the ratified text itself lives in `aetheris--CLAUDE.md`,
> which is exported and re-pinned below*, the same call made for
> `bl-039-contract-draft.md` last export).
>
> **Added: `cloudcost--milestone.md`** — the third milestone-tree exception, on the same
> test as `rig--protocol.md` and `rig--bl-007-milestone.md`: it is a milestone
> *specification later work is written against*, not review history. Its §Normalized
> schemas freezes the two-schema adapter contract that the AWS/GCP/Linode adapters will
> be written to, and its D1–D6 and §Open items (multi-currency, `STOPPED_STATES`) are
> the constraints on that fan-out. A reviewer reasoning about provider two needs it and
> would otherwise be reading a stale sketch from memory.
>
> **`cloudcost/runbook.md` stays out**, and not as an oversight: no use-case runbook has
> ever carried a row (docbuilder, eduloka and boxy-pipeline all have one; none is
> exported). The two exported runbooks are the Rig and harness runbooks — system-level
> operator docs, a different category from a single use case's how-to-run.

---

Exported: 2026-07-29 at aetheris-agents `9afd8e7` / aetheris `57d90d2` (m1-cloudcost
close — t1–t5, the §7 promotion, and the operator runbook). 25 rows: **24 carried, one
added (`cloudcost--milestone.md`), none dropped.** Four rows re-pinned, clearing all
four standing staleness WARNs: `aetheris-agents--CLAUDE.md` (`1013a95`→`9afd8e7`),
`capability-matrix.md` (`eeb37a1`→`6abc3e8`), `backlog-2026-06.md`
(`c27dee4`→`013c09d`), and `aetheris--CLAUDE.md` (`1ebe971`→`57d90d2`). The other
twenty data rows are unchanged since the previous export.

**Why this export matters beyond the WARNs.** The four re-pinned rows are all m1's own
output, and one of them carries the milestone's marquee learning: the §7 rewrite of
**Silent-wrong-answer** landed in `aetheris--CLAUDE.md` (`57d90d2`). Implementer
sessions read that from the repo and already have it; the review side reads the
*exported* copy and is served the superseded wording until this export lands. Until
then the §7 loop is half-closed — live for the author, stale for the reviewer. That
asymmetry, not the drift cosmetics, is what the export closes.

**Upload is remove-all then upload-all against the full 25-row set** — not a diff of
the four re-pinned rows plus the add. Twenty data rows are unchanged and would look
like "nothing to re-upload" to any hash-driven shortcut; do not optimise the upload
down. This is the standing discipline that also covers the manifest-blind direction
the header warns about (a file uploaded without a regen leaves the record silently
under-describing project knowledge).

**BL-034 — closed; the paragraph this replaces was stale.** Previous manifests
carried BL-034 forward as a *latent* vacuity: the refresh prompt closed by appending
a drift baseline to `docs/rig/current-state-2026-06.md` — a tracked file — *after*
Step 2, which would born-stale that row the moment it landed. **That is fixed.**
BL-034 is Done 2026-07-22 ("resolved by dropping the baseline append"), and
`prompts/bl-002-refresh-project-knowledge.md` at HEAD no longer contains the step: it
now states the invariant directly ("the manifest is the ONLY tracked file this task
writes, and it is the LAST tracked write") and records the removal. Verified at HEAD
this export, not carried on faith. `current-state-2026-06.md` stays pinned `f723ee5`,
matching HEAD.

**Repo push state.** Both repos are synced at the exported commits — aetheris-agents
`origin/main` = `9afd8e7`, aetheris `origin/main` = `57d90d2`; all of m1-cloudcost is
on origin. Only this manifest regen commit is unpushed, held for the human.

Previous export: 2026-07-26 at aetheris-agents `53c97cb` / aetheris `f79365a` (the
fork arc — BL-039 then BL-030 r0/r1/r2 — plus BL-038; six rows re-pinned, none added).
