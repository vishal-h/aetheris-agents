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
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `99a46df` | 2026-08-04 |
| `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `c0977c2` | 2026-07-25 |
| `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `7d6013a` | 2026-07-26 |
| `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` | 2026-06-11 |
| `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `f723ee5` | 2026-07-20 |
| `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` | 2026-07-20 |
| `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
| `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `7a7b7ec` | 2026-08-02 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `0fc9396` | 2026-08-03 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `b7cb6ca` | 2026-08-02 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `9b5da48` | 2026-08-04 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `710ecd2` | 2026-08-03 |
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
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `265d336` | 2026-08-03 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-07-30 |

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

> **BL-066/067/068 export — the rule applied unchanged, no adds, no drops.** The three
> tickets produced eleven working artifacts, all out by the standing rule: three
> `docs/reviews/*.md` (the BL-066, BL-067 and BL-068 reviews), two
> `docs/milestones/bl-06{7,8}-implementation-notes.md`, and the harness-side gate
> evidence carried inside the packets. Their *specifications* are the BL-0xx rows,
> already exported inside `backlog-2026-06.md`.
>
> **`docs/capability-matrix-runbook.md` stays out**, on the precedent this manifest
> already records: the two exported runbooks are the Rig and harness *system* runbooks,
> and every artifact-specific how-to-run (docbuilder, eduloka, boxy-pipeline, cloudcost)
> has stayed out. It governs regenerating an artifact from inside the repo, which is
> repo-side work; the artifact it produces — `capability-matrix.md` — is exported and
> re-pinned below. `docs/capability-matrix-overrides.json` is data read by
> `assemble_matrix.py`, not a reference doc, and is out for the same reason.

---

Exported: 2026-08-03 at aetheris-agents `0fc9396` / aetheris `265d336` (m2-cloudcost CLOSED —
AWS as provider two, contract-proof held; t4 optimization spike; the §7 promotion of seven
learnings). 25 rows: **25 carried, none added, none dropped.** Six rows re-pinned, clearing
every standing staleness WARN: `cloudcost--milestone.md` (`9afd8e7`→`7a7b7ec`),
`aetheris-agents--CLAUDE.md` (`9afd8e7`→`0fc9396`), `capability-matrix.md`
(`e60bcfd`→`b7cb6ca`), `backlog-2026-06.md` (`63f48e1`→`f12dfa6`), `aetheris--CLAUDE.md`
(`57d90d2`→`710ecd2`) and `methodology--triad-loop.md` (`602bdf5`→`265d336`). The other
nineteen data rows are unchanged since the previous export.

**This export is cross-repo on both sides**, which the previous one was not: the §7 promotion
put learnings in *both* `CLAUDE.md`s (four in the harness, three in agents), and the
triad-loop mirror sync moved the canonical harness copy. Both repos' rows were therefore
re-pinned from their own histories, and both repos must be pushed together — a manifest
pinning a hash that exists only locally in the sibling describes an export nobody else can
reproduce.

**What the two re-pinned rows carry.** `capability-matrix.md` is a different artifact than
the copy in project knowledge today: its whole derived block — Summary counts, unique-tools
line, Overlap Report — is now script-counted rather than LLM-asserted (BL-067), which
corrected three standing Overlap Report defects; it gained a ninth use case (eduloka, 1
agent / 14 scripts, totals 26/67 → **27/81**); and its curated cells now survive a regen via
`docs/capability-matrix-overrides.json` (BL-068). A reviewer reading the exported copy would
otherwise reason from counts that were wrong and a use-case list that was short one entry.
`backlog-2026-06.md` carries the three closes (BL-066 **and** its duplicate BL-060, BL-067,
BL-068) — without it the review side still reads `hex.audit` as expected-red and BL-068 as
open, which is the same half-closed asymmetry the m1-cloudcost export described.

**Upload is remove-all then upload-all against the full 25-row set** — not a diff of the two
re-pinned rows. Twenty-two data rows are unchanged and would look like "nothing to
re-upload" to any hash-driven shortcut; do not optimise the upload down. This is the
standing discipline that also covers the manifest-blind direction the header warns about (a
file uploaded without a regen leaves the record silently under-describing project knowledge).

**Ordering invariant held.** The manifest is the only tracked file this task wrote and the
last tracked write; nothing manifest-tracked was edited after the table was regenerated, so
the two re-pinned rows are not born stale. (BL-034's hazard, verified fixed in
`prompts/bl-002-refresh-project-knowledge.md` at HEAD last export, remains fixed — the
prompt still carries the invariant and no baseline append.)

**Repo push state.** Both repos are synced at the exported content commits —
aetheris-agents `bd37e90`, aetheris `fd9ac48` — and the manifest regen commit on top of
them is pushed too, so nothing about this export is held locally. (Deliberately no
self-hash here: a line naming the manifest's own commit is stale the moment it is
committed.)

Previous export: 2026-07-29 at aetheris-agents `9afd8e7` / aetheris `57d90d2` (m1-cloudcost
close — t1–t5, the §7 promotion, and the operator runbook; four rows re-pinned, one added).

---

**Export boundary — 2026-08-04, cloudcost-in-Rig batch close.** Two rows advanced:
`rig--specs.md` (`b5e8eee`→`99a46df`, BL-073's `harness_run_artifacts` +
`harness_open_artifact` §4 entries) and `backlog-2026-06.md` (`f12dfa6`→`9b5da48`, the BL-083 / BL-073 /
BL-095 / BL-096 DONE sections, the BL-093..BL-097 satellite rows, and BL-090's appended second
staleness).

> Re-pinned once within this boundary. The first regen pinned `064664a`, which snapshotted the
> batch **one step before its last two rows closed** — BL-073 and BL-095 were merged but not yet
> marked DONE, so the exported backlog would have read them as open. Caught by reading the pinned
> hash against the repo rather than trusting the 0-WARN result: `drift_check` verifies the pin is
> *current*, never that it is *complete*. Fixed by marking both rows DONE and re-pinning; the
> ordering rule held both times (backlog written first, manifest last).

> Mirror-pair check run before regen per the BL-002 convention: `triad-loop.md` canonical
> (`aetheris/docs/methodology/`) and its `aetheris-agents/docs/` mirror are byte-identical, so
> no canonical sync was needed this boundary. `drift_check` cannot see that class — the `diff -q`
> is the only thing that catches it.

> Not exported, per the inclusion rule: this batch's `docs/rig/milestones/bl-0*-implementation-notes.md`
> (BL-073, BL-083, BL-086, BL-095, BL-097) and
> `docs/handoffs/handoff-cloudcost-rig-batch-close-2026-08-04.md` are milestone *working*
> artifacts, not specifications.

**Upload is remove-all then upload-all against the full 25-row set** — not a diff of the two
re-pinned rows. Twenty-three data rows are unchanged and would look like "nothing to re-upload"
to any hash-driven shortcut; do not optimise the upload down. This is the standing discipline
that covers the manifest-blind direction the header warns about: `drift_check` compares
manifest-vs-git, so it catches the repo running ahead (the stale WARN that cleared at this
boundary) but cannot see a partial or under-described upload — an incremental upload can leave
project knowledge silently wrong while drift still reports green.

> Recorded because it was nearly got wrong here: this session first proposed staging only the
> two advanced rows plus the manifest. That is exactly the shortcut this paragraph forbids, and
> the tooling would not have caught it — 9 PASS / 0 FAIL / 0 WARN either way.

**All 25 rows verified against their owning repos at regen** — every pinned commit equals
`git log -1 --format=%h -- <path>` in the owning repo (`../aetheris` for the 12 harness rows),
and all 25 files exist on disk. Only the two named above moved since the previous boundary.

**Ordering invariant held.** The manifest is the last tracked write of this export; nothing
manifest-tracked was edited after the table was regenerated, so the two re-pinned rows are not
born stale. Verified by the post-commit `drift_check --strict`: 9 PASS / 0 FAIL / **0 WARN** —
the manifest-staleness class cleared, which is what an export boundary is supposed to produce.

**Repo push state.** `aetheris-agents` is synced at the exported content commits; the harness
repo was not written this batch, so its 12 rows carry their prior hashes unchanged.

Previous export: 2026-08-03 (m2-cloudcost close).
