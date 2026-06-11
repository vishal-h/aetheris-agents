# BL-002 — Refresh Claude.ai project knowledge

**Trigger:** milestone end, before any handoff session, or when
`docs/project-knowledge-manifest.md` commit hashes diverge from HEAD.

**Issue:** https://github.com/vishal-h/aetheris-agents/issues/43

---

Execute BL-002 from docs/backlog-2026-06.md: prepare the Claude.ai
project-knowledge export and its manifest. You cannot upload to
Claude.ai — your job is to assemble the bundle, write the manifest,
and print upload instructions for the human.

Step 1 — Verify the file set. Confirm each candidate exists; report
any that don't and proceed without them:
  Rig:    docs/rig/specs.md, docs/rig/architecture.md,
          docs/rig/runbook.md, docs/rig/milestones/p3/protocol.md,
          docs/rig/current-state-2026-06.md, rig/CLAUDE.md
  Agents: CLAUDE.md (repo root), docs/agent-creation-guide.md,
          docs/capability-matrix.md, docs/backlog-2026-06.md
  Harness: ../aetheris/CLAUDE.md (verify it exists — if not, check for
          an equivalent like ../aetheris/README.md and report; do not
          substitute source files)
Before including rig/CLAUDE.md, report its line count — if it's very
large, flag it for a human include/exclude decision but include it in
the bundle by default.

Step 2 — Create docs/project-knowledge-manifest.md. A short header
explaining purpose (drift detection for Claude.ai project knowledge;
see BL-002), then one table with EXACT formatting (check 8 of
drift_check.py parses this; deviation = FAIL on zero rows):

  | export name | repo path | repo | commit | last changed |
  |-------------|-----------|------|--------|--------------|
  | `<export-name>` | `<repo/path>` | <repo-name> | `<short-hash>` | <YYYY-MM-DD> |

Formatting rules:
- export name in backticks; repo path in backticks; repo name BARE
  (aetheris-agents or aetheris); commit as backticked short hash.
- The manifest's own row uses _(this export)_ in the commit column
  (unbackticked, not a hash) — drift_check skips it by design.
- Per file: commit = git log -1 --format=%h -- <path> run in the
  OWNING repo (use ../aetheris for the harness file — its hashes come
  from that repo's history, not this one's); last changed = the
  commit date.
- Add a final line after the table: "Exported: <today's date> at
  aetheris-agents <HEAD short hash> / aetheris <HEAD short hash>."
- After writing, run: python3 scripts/drift_check.py --check project_knowledge
  Confirm PASS before proceeding to Step 3. If it FAILs on zero rows,
  the formatting is wrong — fix the table before continuing.

Step 3 — Assemble the bundle at /tmp/claude-project-export/ (fresh
directory, delete if exists). Copy each file with a FLATTENED,
COLLISION-FREE name that preserves origin:
  aetheris-agents--CLAUDE.md
  aetheris--CLAUDE.md
  rig--CLAUDE.md
  rig--specs.md, rig--architecture.md, rig--runbook.md,
  rig--protocol.md, rig--current-state-2026-06.md
  agent-creation-guide.md, capability-matrix.md,
  backlog-2026-06.md, project-knowledge-manifest.md
The manifest's "export name" column must match these names exactly.
Do NOT modify file contents — copies only. The manifest itself is
part of the bundle (copy it in after writing it).

Step 4 — Commit the manifest only if its content changed. Run:
  git diff --quiet docs/project-knowledge-manifest.md
If the diff is non-empty, stage and commit docs/project-knowledge-manifest.md
only (not the bundle) with message "BL-002: project-knowledge manifest".
If the diff is empty, print "manifest unchanged — nothing to commit" and
skip the commit. The bundle in /tmp is ephemeral either way.

Step 5 — Print for the human:
  - the bundle path and an ls of it
  - upload instructions: in the Claude.ai project, REMOVE the old
    knowledge files (stale handoff, old specs/architecture/runbook/
    protocol/README, old CLAUDE.md), then upload everything in
    /tmp/claude-project-export/
  - the refresh rule: re-run this same task at milestone end or
    before any handoff; the manifest commit hash is how a future
    session detects staleness.

Constraints: read-only outside docs/project-knowledge-manifest.md and
/tmp/claude-project-export/. Run drift_check.py (with AETHERIS_DB_PATH
set) once at the end to confirm exit 0 and zero WARN. The project_knowledge
check (check 8) now covers the manifest — a PASS there is also the BL-001
clean baseline capture. Append the summary line to
docs/rig/current-state-2026-06.md as:
  "Drift baseline <YYYY-MM-DD>: <summary line from drift_check output>"
