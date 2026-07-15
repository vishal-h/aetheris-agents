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

---

| export name | repo path | repo | commit | last changed |
|-------------|-----------|------|--------|--------------|
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `fe34af4` | 2026-07-15 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `dc024d1` | 2026-07-15 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `d24e482` | 2026-07-15 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `acf9a13` | 2026-07-15 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `eeb37a1` | 2026-06-27 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `acf9a13` | 2026-07-15 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `cdb6a21` | 2026-06-13 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `e373092` | 2026-07-15 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `aca62e5` | 2026-07-15 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `602bdf5` | 2026-07-15 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-07-15 |

> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical
> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit
> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.

---

Exported: 2026-07-15 at aetheris-agents `acf9a13` / aetheris `aca62e5` (BL-005 #46 closeout).
