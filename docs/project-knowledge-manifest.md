# Project Knowledge Manifest

This file records which documents are uploaded to the Claude.ai project, at
what commit they were exported, and — since 2026-09-08 — on which **surface** each
document is served. Its purpose is drift detection: a future session
can compare the `commit` column against `git log -1 --format=%h -- <path>` in
the owning repo to determine whether the project knowledge is stale.

Check 8 of `scripts/drift_check.py` (`project_knowledge`) parses this table
automatically and emits WARN for any stale entry. See **BL-002** in
`docs/backlog-2026-06.md` for the refresh convention and
`prompts/bl-002-refresh-project-knowledge.md` for the exact row format.

Refresh trigger: milestone end, or before any handoff session.

**Surfaces (hybrid-context design, 2026-09-08).** The `surface` column says how a document
reaches its reader. `export` — the kernel: uploaded to the project store at each BL-002
boundary. `on-demand` — git only, never uploaded; reached at HEAD through the generated
`index.md` of its tree, and that index is itself a kernel row. `both` — exported AND fetchable;
on any conflict **the copy fetched at HEAD wins**, the export being a convenience cache; used
sparingly. The kernel is the set of `export` and `both` rows: `scripts/_manifest.py`'s
`export_rows()` is the one place that rule is applied, and `assemble_export_bundle.py` bundles
nothing else. Kernel composition follows the design note's ratified D-B table
(`aetheris/docs/aetheris/research/hybrid-context-design-2026-08.md` §2); the assignment made
here and its reasons are the dated **THE SURFACE COLUMN** block after the table.

**Kernel budget: 120 KB** — the design note's §2.1 figure, over the committed sizes of the
`export` and `both` rows. Exceeding it is a drift warning `[not yet mechanised — BL-201]`.
Measured at agents `799ddc9` / harness `a950ca9`, before the commit that added this line:
**869 KiB, over budget by more than seven times**, and two rows carry almost all of it —
`backlog-2026-06.md` (617 KB, the pre-split queue the D-B table names as `queue.md
post-split`) and this manifest (134 KB, mostly boundary records). Reproduce:
`python3 scripts/assemble_export_bundle.py $(mktemp -d)/bundle` prints every kernel document's
size beside its name. A new kernel row names what it displaces, or triggers a probe re-run
(design §3) to justify the growth.

**Connector notice — the corpus is fetch-only.** Everything on the `on-demand` surface, and
every document reachable through an indexed tree's `index.md`, lives in git only and is served
to claude-ai by the **GitHub connector** on the claude.ai project, granted for BOTH
repositories (`aetheris-agents` and `aetheris`); claude-code reads the sibling checkouts. **If a
fetch returns nothing, check the connector grant before anything else**: a lapsed grant fails
as *no connector*, never as *no results*, and no session should re-derive this architecture
from that confusion. The index a fetch starts from is `aetheris--research-index.md`
(`aetheris/docs/aetheris/research/index.md`), the only indexed tree as of 2026-09-08.
`[2026-09-08, after the bare-condition after-run — the OWNER MAPPING, stated so a fetch can be
addressed without re-deriving it: `aetheris` = `vishal-h/aetheris`; `aetheris-agents` =
`vishal-h/aetheris-agents`. The connector is `github-mcp`, read-only; branch `main`; path as
written in this manifest's `repo path` column or in the index entry.]`
`[2026-09-08, same finding — the WRONG-INSTRUMENT FINGERPRINT: a session that searches memory or
Drive and never mentions project knowledge is running OUTSIDE the project; discard it and restart
in-project. The after-run detected one such session by exactly this fingerprint and discarded it
before probe 1.]`

**Uploads happen only as part of an export boundary — the manifest is regenerated
and included in the same set.** The check compares this file against git, so it
detects the repo moving ahead of an export (expected mid-cycle staleness, a
strict-exempt WARN). It cannot detect the reverse: a file uploaded without a regen
leaves the manifest silently under-describing project knowledge, and drift reports
green while the record is wrong. The tooling is blind in that direction; the
discipline is what covers it. Source: BL-022 filing, 2026-07-17.

**The store also holds documents under the `claude/` namespace that sessions wrote directly
and that have no repo copy.** They are outside the manifest by design and are never removed by
a remove-all-upload-all pass — *remove-all* reads *all of the manifest set*, never *everything
in the store*. As of the 2026-09-07 export there are six such documents, and nothing under
`claude/` carries a row: every manifest-tracked document sits in the store at its bare export
name. Stated here so the blind spot the paragraph above records is a declared exclusion rather
than an undetectable gap. The figure is the store's, as read by the claude-ui session at that
export, and is not re-derivable from either repository; that `claude/` holds nothing else is
the same session's report after its same-day correction, recorded at the end of the 2026-09-07
boundary record below.
`[Corrected 2026-09-07, after the boundary closed. As committed at `675829d` this paragraph
also named two rows the export had added *under the same prefix*, `claude/m-payslip-release.md`
and `claude/backlog-scale-2026-09.md`, *"which ARE manifest-tracked despite it"*. They no longer
have the prefix: the store was corrected the same day and the two rows re-pinned to their bare
export names. The dated block at the end of the 2026-09-07 boundary record says what changed
and why; the procedural gap it exposed is **BL-196**.]`

---

| export name | repo path | repo | commit | last changed | surface |
|-------------|-----------|------|--------|--------------|---------|
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `95b1161` | 2026-09-12 | on-demand |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `c0977c2` | 2026-07-25 | on-demand |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `7d6013a` | 2026-07-26 | on-demand |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 | on-demand |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `f723ee5` | 2026-07-20 | export |
| `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` | 2026-07-20 | on-demand |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 | on-demand |
| `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `97c61a0` | 2026-08-14 | on-demand |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `718bbc5` | 2026-09-10 | on-demand |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 | on-demand |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `e0c1ee2` | 2026-08-14 | export |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `3973748` | 2026-09-15 | export |
| `use-cases.md` | `docs/use-cases.md` | aetheris-agents | `9cf3689` | 2026-08-19 | on-demand |
| `backlog-2026-06-closed.md` | `docs/backlog-2026-06-closed.md` | aetheris-agents | `3973748` | 2026-09-15 | on-demand |
| `aetheris-agents--inbox-brief.md` | `docs/aetheris/backlog/uc-inbox.md` | aetheris-agents | `a1f8daf` | 2026-08-24 | on-demand |
| `aetheris-agents--ravenmigrate-brief.md` | `docs/aetheris/backlog/uc-ravenmigrate.md` | aetheris-agents | `b56aed3` | 2026-08-24 | on-demand |
| `aetheris-agents--almanac-brief.md` | `docs/aetheris/backlog/uc-almanac.md` | aetheris-agents | `b56aed3` | 2026-08-24 | on-demand |
| `m-payslip-release.md` | `docs/milestones/m-payslip-release.md` | aetheris-agents | `bec45d0` | 2026-09-07 | on-demand |
| `backlog-scale-2026-09.md` | `docs/backlog-scale-2026-09.md` | aetheris-agents | `bec45d0` | 2026-09-07 | on-demand |
| `backlog-triage-2026-09.md` | `docs/backlog-triage-2026-09.md` | aetheris-agents | `29ed2a2` | 2026-09-14 | on-demand |
| `aetheris-agents--ROADMAP.md` | `ROADMAP.md` | aetheris-agents | `4339ba7` | 2026-07-16 | export |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `2845995` | 2026-09-14 | on-demand |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `2bb9ff7` | 2026-09-13 | on-demand |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `603b7d5` | 2026-09-14 | on-demand |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `603b7d5` | 2026-09-14 | on-demand |
| `aetheris--ROADMAP.md` | `ROADMAP.md` | aetheris | `481ae2a` | 2026-08-12 | export |
| `aetheris--research-README.md` | `docs/aetheris/research/README.md` | aetheris | `324584c` | 2026-09-09 | on-demand |
| `aetheris--research-index.md` | `docs/aetheris/research/index.md` | aetheris | `6c62345` | 2026-09-10 | both |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `49e9ebf` | 2026-09-08 | on-demand |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `49e9ebf` | 2026-09-08 | on-demand |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `49e9ebf` | 2026-09-08 | on-demand |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `49e9ebf` | 2026-09-08 | on-demand |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `49e9ebf` | 2026-09-08 | on-demand |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `49e9ebf` | 2026-09-08 | on-demand |
| `aetheris--bl-008-synthesis.md` | `docs/aetheris/research/bl-008-synthesis-2026-08.md` | aetheris | `19ba133` | 2026-09-14 | both |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `58991d5` | 2026-09-14 | export |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `2050c04` | 2026-08-21 | export |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-08-09 | export |

> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical
> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit
> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.
> Mirror re-verified at this export (`diff -q`, 2026-08-03) — and it had **drifted**: the
> P3 section-scoped rule landed in the *mirror* only (agents `7328755`, 2026-08-02), so
> canonical was 26 lines short of it and would have been exported without the rule
> claude-ui operates under. Synced canonical (`265d336`, purely additive: 26 insertions,
> 0 deletions) and the pair is byte-identical again. Note what this means for the check
> itself: `drift_check` compares the manifest against git history and has **no
> byte-identity check between mirrors**, so this class is invisible to it — the `diff -q`
> at the export boundary is the only thing that catches it. Edit the harness copy.
> The mirror's own last change is `7328755`, which is why it carries no manifest row —
> the row tracks the canonical copy, and a second row would drift against it.

