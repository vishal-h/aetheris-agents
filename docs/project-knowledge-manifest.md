# Project Knowledge Manifest

This file records which documents are uploaded to the Claude.ai project and at
what commit they were exported. Its purpose is drift detection: a future session
can compare the `commit` column against `git log -1 --format=%h -- <path>` in
the owning repo to determine whether the project knowledge is stale.

See **BL-002** in `docs/backlog-2026-06.md` for the refresh convention.
Refresh trigger: milestone end, or before any handoff session.

---

| export name | repo path | repo | commit | last changed |
|-------------|-----------|------|--------|--------------|
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `7ded982` | 2026-06-11 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `88705f1` | 2026-06-11 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `7ded982` | 2026-06-11 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `e91820c` | 2026-05-24 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `b4a0eb8` | 2026-06-10 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `d825ddd` | 2026-06-11 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `a6ef3e8` | 2026-05-31 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-06-11 |

---

Exported: 2026-06-11 at aetheris-agents `d825ddd` / aetheris `bd2c3d8`.
