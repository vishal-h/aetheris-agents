# BL-002 — Refresh Claude.ai project knowledge

**Trigger:** milestone end, before any handoff session, or when
`docs/project-knowledge-manifest.md` commit hashes diverge from HEAD.

**Issue:** https://github.com/vishal-h/aetheris-agents/issues/43

---

Execute BL-002 from docs/backlog-2026-06.md: prepare the Claude.ai
project-knowledge export and its manifest. You cannot upload to
Claude.ai — your job is to assemble the bundle, write the manifest,
and print upload instructions for the human.

Step 1 — The file set is the manifest's table, and only the manifest's
table. `docs/project-knowledge-manifest.md` is the sole authority for
which documents are exported, from which repo, and under what export
name — some of those names are editorial and no path rule regenerates
them. This prompt used to carry a second copy of that list and it went
stale; the copy is gone rather than corrected, because two surfaces
disagree at the next addition (BL-145's shape, and `CLAUDE.md`
§Learning — m6-cloudcost on enumerations).

Existence is verified by the assembler in Step 3, per row, by reading
each source out of committed history: a row whose path is not in HEAD
fails the run and no bundle is written. Nothing is silently dropped.

Adding or removing a document is an edit to that table, made
deliberately and with its reason recorded in the manifest's prose — not
a change to this prompt.

Step 2 — Re-pin the manifest's commit column:

    python3 scripts/repin_manifest.py            # --dry-run to preview

It runs `git log -1 --format=%h -- <path>` per row in that row's OWN
repo (../aetheris for the harness rows) and rewrites the commit cell,
touching nothing else — not the prose, not the `last changed` column,
not the self-referential row. Run against a manifest already current it
writes nothing at all.

The manifest's narrative — what moved this boundary and why, what stayed
out and on what rule — is still written by hand, in the same commit.

The table's format is the contract (check 8 of drift_check.py parses it;
deviation = FAIL on zero rows):

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

Step 3 — Assemble the bundle:

    python3 scripts/assemble_export_bundle.py /tmp/claude-project-export

One file per manifest row, named by the table's export-name column, its
content read from `git show HEAD:<path>` in the owning repo — never the
working tree, so an uncommitted edit does not reach the store. The
manifest is itself a row and lands in the bundle like any other
document. Deterministic given the two HEADs: two runs into two
directories are byte-identical.

Two refusals, both deliberate:
- A destination that already has content is REFUSED, not merged. The
  2026-08-14 boundary found a complete bundle from the previous export
  sitting at that path; merging would have produced correctly-named,
  parseable files from two exports with nothing telling them apart.
  `--replace` moves the existing directory aside to
  `<dest>.superseded.<n>` — it is never deleted, being the only record
  of what was last uploaded.
- The bundle is written UNSWEPT and says so, in a
  `_UNSWEPT-DO-NOT-UPLOAD.txt` file inside it, because the U2 scrub
  class is what stands between it and a project and this script cannot
  check it unaided (U2's needles are the real identifiers themselves;
  a committed script carrying them would be the disclosure). Run the
  sweep with `--replace --needles FILE` over an untracked needle file,
  one per line — a clean sweep writes no marker. Delete the needle file
  afterwards.

Step 4 — Commit the manifest only if its content changed. Run:
  git diff --quiet docs/project-knowledge-manifest.md
If the diff is non-empty, stage and commit docs/project-knowledge-manifest.md
only (not the bundle) with message "BL-002: project-knowledge manifest".
If the diff is empty, print "manifest unchanged — nothing to commit" and
skip the commit. The bundle in /tmp is ephemeral either way.

Step 5 — Print for the human:
  - the bundle path and an ls of it
  - whether the U2 marker is still present. If it is, the bundle is
    unswept and the upload cannot proceed on it — say so rather than
    printing upload instructions under it.
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

1. **Count and names, over the manifest namespace.** The store's document set — every store
   path **not** under `claude/` — equals the manifest's export-name column exactly: set
   comparison in both directions, not a count. A name in one and not the other is the finding.
   A `claude/`-namespaced document carries no row and is out of the export set **by
   construction**: it is not a check-1 finding, and check 3 is where it is accounted for.
2. **Content, on the movers only.** For each row re-pinned this boundary, read the uploaded doc
   and confirm it carries the new content rather than trusting the name. A stale file uploaded
   under a current name passes every other check here.
3. **No manifest-namespace document predates the upload window; `claude/` is enumerated, not
   judged.** A genuine remove-all-upload-all — *remove-all* reading *all of the manifest set*,
   never *everything in the store* — leaves every manifest doc created inside one narrow window.
   A doc with an older timestamp survived the remove, and the namespace decides what that means.
   **Under `claude/`**: an agent-written document, out of the export set **by construction** and
   never removed by this procedure — enumerate those and move on. No condition on the manifest is
   owed, and it is not a check-3 exception either. **Outside `claude/`**: the upload was
   incremental and the store now under-describes itself, which is the finding.
   Same-window-among-themselves is not sufficient: a partial upload of four files shares a
   window too. The discriminator is that *nothing is older*.

   The namespace boundary between checks 1 and 3 is **BL-143**'s ruling of 2026-08-16
   (`docs/backlog-2026-06.md`); its standing form is `CLAUDE.md` §Definition of done. Neither
   check treats the other's population as a finding.

`Source: m3-cloudcost export boundary, 2026-08-05 — the store-side check that found the
manifest describing 25 documents while the store held 26.`
