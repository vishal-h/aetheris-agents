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
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `e324b11` | 2026-06-13 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `06a1c92` | 2026-06-13 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `4afb21f` | 2026-06-13 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `ae26e28` | 2026-06-16 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `e91820c` | 2026-05-24 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `6e54fa6` | 2026-06-16 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `201dcc2` | 2026-06-14 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `cdb6a21` | 2026-06-13 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-06-11 |

---

Exported: 2026-06-11 at aetheris-agents `ff60ebb` / aetheris `bd2c3d8`.
