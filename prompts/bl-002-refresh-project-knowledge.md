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
/tmp/claude-project-export/. The manifest is the ONLY tracked file this
task writes, and it is the LAST tracked write — do NOT append to, or
otherwise edit, any manifest-tracked doc (current-state-2026-06.md, the
CLAUDE.mds, backlog, specs, runbook, architecture, …) after Step 2. Any
such edit moves that file's commit hash past the value the manifest just
recorded, staling the row the instant it lands. (This invariant is
BL-034: the prompt used to close by appending a drift baseline to the
manifest-tracked current-state-2026-06.md, which would stale that row the
moment the append landed after Step 2. This is a latent hazard, not an
observed one — a check-8 sweep of every committed manifest (38/38 clean)
confirms it never actually fired; historical runs happened to avoid it.
The append is removed so it cannot. BL-001 owns the one-time clean
baseline and is Done.)

Run drift_check.py (with AETHERIS_DB_PATH set) once at the end to confirm
exit 0 and zero WARN. Because Step 2 regenerated the manifest at HEAD and
nothing tracked was written after it, zero WARN is reachable. (Under
--strict the binding invariant is zero *unexplained* WARN —
project_knowledge staleness is strict-exempt — but a freshly regenerated
manifest at an export boundary should carry no staleness WARN at all.)

---

## Post-upload verification (the boundary's last step, and it is not the uploader's)

The upload half has no detector. `drift_check` check 8 compares the manifest against git
history, so it catches the repo running ahead of an export and is structurally blind to a
partial, misnamed or under-described upload — project knowledge can be silently wrong while
drift reports green. Nothing in this repo can see the store; the verification is run by a
surface that can read project knowledge (claude-ui's Projects tool, or the human in the UI) and
handed back.

Three checks, and the third is the one that catches an incremental upload:

1. **Count and names.** The store's document set equals the manifest's export-name column
   exactly — set comparison in both directions, not a count. A name in one and not the other is
   the finding.
2. **Content, on the movers only.** For each row re-pinned this boundary, read the uploaded doc
   and confirm it carries the new content rather than trusting the name. A stale file uploaded
   under a current name passes every other check here.
3. **No document predates the upload window.** A genuine remove-all-upload-all leaves every
   manifest doc created inside one narrow window. A doc with an older timestamp survived the
   remove — either it is a deliberate non-manifest document (agent-written docs land under
   `claude/`), in which case the manifest should say such documents may coexist and are out of
   scope, or the upload was incremental and the store now under-describes itself.
   Same-window-among-themselves is not sufficient: a partial upload of four files shares a
   window too. The discriminator is that *nothing is older*.

`Source: m3-cloudcost export boundary, 2026-08-05 — the store-side check that found the
manifest describing 25 documents while the store held 26.`
