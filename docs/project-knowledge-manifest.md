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
| `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `8f36e45` | 2026-08-11 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `d025971` | 2026-08-10 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `4d98ec2` | 2026-08-05 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `124707f` | 2026-08-12 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `fdb1d64` | 2026-08-12 |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `2ebc59c` | 2026-08-09 |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `915d582` | 2026-07-25 |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `1ab24d8` | 2026-07-26 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` | 2026-07-17 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `6bc49fc` | 2026-08-11 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `b400b12` | 2026-08-11 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-08-09 |

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

> **Regenerated 2026-08-09 at the hc round's export boundary (hc-e r8).** Row count **25**,
> derived — and compared against the **25** hc-e's step-1 gate G6 derived before any regen, both
> printed: **they agree, and no row was added or removed.** **Four rows re-pinned**, all four this
> cycle's own edits: `aetheris-agents--CLAUDE.md` `080ad24`→`dcf1d42`, `backlog-2026-06.md`
> `384656c`→`7dbdb7d`, `aetheris--CLAUDE.md` `288c8ef`→`2ef0517`, `aetheris--runbook.md`
> `ae0c510`→`2ebc59c`. The other twenty were verified current against
> `git log -1 --format=%h -- <path>` in each row's own repo, by field rather than by grep, and the
> self-referential row carries `_(this export)_` as the convention requires.
>
> **Mirror-pair check run before the regen, per BL-002:** `diff -q` over
> `aetheris/docs/methodology/triad-loop.md` and its `aetheris-agents/docs/` mirror →
> **byte-identical**, so no canonical sync was needed this boundary. `drift_check` cannot see that
> class; the `diff -q` is the only thing that catches it.
>
> **Upload is remove-all then upload-all against the full 25-row set**, never a diff of the four
> re-pinned rows. Twenty-one rows are unchanged and would read as "nothing to re-upload", which is
> exactly the direction check 8 is blind in.

> **`docs/milestones/` is out of the manifest, and it is out as a *kind* rather than as a
> directory.** Added 2026-08-09 at the hc round's close (hc-e), per its §Close criteria clause 6,
> which requires both halves because half 1 alone re-installs the error half 2 refutes.
> **Half 1** — everything `docs/milestones/` holds today is a milestone working artifact: cycle
> documents, `*-implementation-notes.md`, and the `m-eduloka-discovery-*` pair, which is direct
> precedent for a milestone-level document living there untracked. **Half 2, and it is the half
> that keeps the rule honest** — `docs/rig/milestones/` is the counter-example. Same path segment,
> **two tracked files** (`docs/rig/milestones/p3/protocol.md`,
> `docs/rig/milestones/bl-007/README.md`), admitted on the *specification* test stated below. **So
> the inclusion rule reads the artifact's kind and never its directory**, and a future session must
> not generalise "everything under a `milestones/` directory is out" from half 1 — that
> generalisation was asserted once, checked, and refuted.
>
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

---

**Export boundary — 2026-08-05, m3-cloudcost close (Linode as provider three).** Four rows
advanced, and only four: `aetheris-agents--CLAUDE.md` (`0fc9396`→`13fc8c4`) and
`aetheris--CLAUDE.md` (`710ecd2`→`1743e75`), the milestone's §7 promotions — two doc-sync rules
in agents, five m3 learnings in the harness; `capability-matrix.md` (`b7cb6ca`→`4d98ec2`),
BL-090's regen; and `backlog-2026-06.md` (`9b5da48`→`de71e2b`), BL-098..BL-101, the BL-069
went-green-and-reverted append, and the two DONE sections described below. 25 rows: **25
carried, none added, none dropped.** The other 21 data rows are unchanged since the previous
boundary.

> **Mirror-pair check run first, per the BL-002 convention** — and it is what establishes
> whether the harness repo takes a write at all this boundary. `triad-loop.md` canonical
> (`aetheris/docs/methodology/`) and its `aetheris-agents/docs/` mirror are **byte-identical**
> (188 lines each, `diff -q` clean), so no canonical sync was needed and the harness took no
> tracked write. `drift_check` cannot see that class — it compares the manifest against git
> history and has no byte-identity check between mirrors, so the `diff -q` is the only thing
> that catches it. It is not a formality: at the 2026-08-03 boundary the same check found
> canonical 26 lines short of its mirror, and the export would otherwise have shipped without
> a rule claude-ui operates under.

> **`cloudcost/m3-milestone.md` gets no row — ratified by the human at the m3 close.** m1's
> `cloudcost/milestone.md` is exported because its §Normalized *is* the frozen contract every
> adapter is written to, which is the milestone-*specification* test that also admits
> `rig--protocol.md` and `rig--bl-007-milestone.md`. m3 does not meet it: it holds derived
> reasoning *about* a contract that lives in m1's file — its §Milestone summary reports that
> no §Normalized extension was needed and that the four shared scripts are byte-identical at
> close, i.e. the contract m3 reasons against is m1's, unchanged. m2's milestone doc set the
> precedent by staying out on the same reading.

> **Working artifacts stay out as always — eight this milestone:**
> `cloudcost/docs/m3-linode-scout.md`, the three
> `cloudcost/docs/m3-t{1,2,3}-implementation-notes.md`, the three
> `docs/reviews/m3-cloudcost-t{1,2,3}-review.md`, and
> `docs/handoffs/handoff-linode-provider-three-kickoff-2026-08-04.md` (handoffs have never
> carried a row). `cloudcost/runbook.md` changed this milestone — the Linode posture
> subsection — and stays out on the standing precedent this manifest already records: no
> use-case runbook has ever carried a row; the two exported runbooks are the Rig and harness
> *system* runbooks. As at every prior boundary, this milestone's specifications are the
> BL-0xx rows, already carried inside `backlog-2026-06.md`.

> **Why the backlog row pins at `de71e2b` rather than the milestone's last content commit
> (`b0030e7`).** m3's done-when 5 reads "BL-090 both cells reconciled, BL-092 landed over every
> manifest ✓", and both had landed — the matrix regen at `4d98ec2` (t3), the `tools.rs` serde
> guard at `f28b817` (t2) — but neither row carried a DONE section, so an export pinned at
> `b0030e7` would have shipped project knowledge reading two closed rows as open. Written in
> `de71e2b`, *before* the table was regenerated, so the row pins the corrected file. This is
> the same mid-flight correction the 2026-08-04 boundary made for BL-073/BL-095, and it is now
> covered by a standing rule rather than by noticing twice: `CLAUDE.md` §Definition of done —
> doc sync, *"`drift_check` verifies a pin is current, never that it is complete — read the
> pinned content against what it should say, do not trust the green."* Four movers matching the
> four predicted is a hash result; it says nothing about whether the pinned content is
> finished. The correction was **enumerated, not patched**: m3's §Done-when and §Milestone
> summary were swept for every row they claim complete, which confirmed BL-096 already carries
> its DONE (2026-08-04, `32933d8`) and that BL-069 must *not* be marked — its Linode leg went
> green on 2026-08-05 and reverted when the plant was deleted, so it stays armed. Two rows
> found by observation are not a census.

**All 25 rows verified against their owning repos at regen** — every pinned commit equals
`git log -1 --format=%h -- <path>` run in the owning repo (`../aetheris` for the 12 harness
rows), and all 25 files exist on disk. The re-verification was run again after `de71e2b`
landed, so the four re-pins are read from the tree the manifest is committed against.

**Upload is remove-all then upload-all against the full 25-row set** — not a diff of the four
re-pinned rows. Twenty-one data rows are unchanged and would look like "nothing to re-upload"
to any hash-driven shortcut; do not optimise the upload down. `drift_check` compares
manifest-vs-git, so it catches the repo running ahead of an export (the staleness WARN that
clears at this boundary) but is blind to the reverse — a partial or under-described upload
leaves project knowledge silently wrong while drift still reports green. The procedure is the
only thing covering that direction, which is why it is now a standing rule in `CLAUDE.md`
§Definition of done — doc sync rather than a paragraph re-derived each boundary.

**Ordering invariant held.** `docs/backlog-2026-06.md` was written first and committed alone
(`de71e2b`); the manifest is the boundary's **last** tracked write and commits alone. Nothing
manifest-tracked was edited after the table was regenerated, so no row is born stale — BL-034's
hazard, which is also why the post-commit `drift_check --strict` below is the meaningful one:
check 8 reads committed history, so run before the commit it would have compared against
pre-edit hashes and passed vacuously.

**Repo push state.** Both repos were level with `origin/main` at the exported content commits
(`a596697` / `5e7935f`) when this export began, so every pinned hash — including the harness's
`1743e75` — is already public and reproducible. The harness took no tracked write this
boundary, so its 12 rows carry hashes from its own pushed history. This boundary's two agents
commits are **held for review, not pushed**. (Deliberately no self-hash: a line naming the
manifest's own commit is stale the moment it is committed.)

Previous export: 2026-08-04 (cloudcost-in-Rig batch close — two rows advanced, re-pinned once
within the boundary).

---

**Export boundary — 2026-08-08, m4-cloudcost close (the consolidation cycle).** **Five rows
advanced**, one more than m3's four, and the fifth is the interesting one:

- `aetheris-agents--CLAUDE.md` (`13fc8c4`→`080ad24`) and `aetheris--CLAUDE.md`
  (`1743e75`→`288c8ef`) — the cycle's §7 promotions, landed at close-b. Harness: a **third
  operational form** of the truth-maker rule (*a count is a claim about a population*) plus two
  widenings of Silent-wrong-answer. Agents: the packet rule's sprint-output sibling, and the
  **repos rule widened to bind every session**, which is what made rule placement editorial.
- `backlog-2026-06.md` (`de71e2b`→`384656c`) — BL-105..BL-113 and BL-114..BL-134 filed across the
  cycle, eight DONE sections, and close-c's BL-069 correction.
- `cloudcost--milestone.md` (`7a7b7ec`→`eae14d4`) — **§Contracts C1–C15**, written at t4b from the
  t4a census. This row had not advanced since 2026-08-02 and carries the cycle's largest single
  addition to a tracked document.
- `methodology--milestone-methodology.md` (`0a0439f`→`aaf0f9a`) — §7's promotion-verification step
  and the census-the-prior-claims clause, landed 2026-08-05. **This row was stale across the whole
  m4 cycle and was not m4's edit**; it is carried here because an export boundary re-pins the
  manifest against the tree, not against one milestone's diff.

**25 rows: 25 carried, none added, none dropped.** The other 19 data rows are unchanged.

**Mirror-pair check ran first**, per the m3 precedent: `docs/methodology/triad-loop.md` (canonical,
harness) and `docs/triad-loop.md` (mirror, agents) are byte-identical — 188 lines each, `diff -q`
clean — so no canonical sync was owed and the harness took no tracked write at this boundary.
`drift_check` still has no byte-identity check between mirrors; the diff remains the only thing
covering that class.

**Ordering, which this cycle had a name for.** The boundary is the **last content operation**:
`backlog-2026-06.md` and both `CLAUDE.md`s settled in earlier commits, and the manifest commits
alone (BL-034). The close statement in `cloudcost/m4-consolidation.md` lands *after* this commit
and cannot restale it, because that file is **not manifest-tracked** — re-derived at close-c's G3
rather than inherited. This is the BL-034 ordering hazard in its milestone-close form, which is
why check 8's meaningful run is the post-commit one.

**On the manifest tracking itself (close-c G2).** Row 25 is `docs/project-knowledge-manifest.md`,
so the manifest **is** in the export set — but its commit column is the literal `_(this export)_`,
and `drift_check`'s check 8 requires a backticked hex hash to parse a row at all
(`scripts/drift_check.py:580–584`, with the skip stated in a comment). So the self-row is exempt
by construction and the regen cannot restale itself. The hazard was real to check; the mechanism
that answers it already existed.

**Upload half is the human's**, unchanged: remove-all then upload-all against the full 25-row set,
never a diff of the five movers — check 8 cannot see a partial upload, and that blindness is what
the procedure covers.

Previous export: 2026-08-05 (m3-cloudcost close — four rows advanced).

---

**Export boundary — 2026-08-12, the gc round's close (stale gate claims).** **Six rows advanced**,
each pin derived by field with `git log -1 --format=%h -- <path>` run in that row's **own** repo,
never taken from the instruction that named them — and the derivation independently produced the
same six:

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `methodology--milestone-methodology.md` | aetheris | `aaf0f9a` | `6bc49fc` | 2026-08-11 |
| `methodology--triad-loop.md` | aetheris | `265d336` | `b400b12` | 2026-08-11 |
| `aetheris--CLAUDE.md` | aetheris | `2ef0517` | `fdb1d64` | 2026-08-12 |
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `dcf1d42` | `d025971` | 2026-08-10 |
| `cloudcost--milestone.md` | aetheris-agents | `eae14d4` | `8f36e45` | 2026-08-11 |
| `backlog-2026-06.md` | aetheris-agents | `7dbdb7d` | `124707f` | 2026-08-12 |

**Row count 25, derived by parsing the table rather than assumed** — unchanged from the hc
boundary's 25; no row was added or removed, and the nineteen not listed above were each verified
current by the same command.

**Uploaded 2026-08-12 by claude-ui.** The mirror-pair check ran **before** the upload, per the
BL-002 convention: `diff -q` over `aetheris/docs/methodology/triad-loop.md` and its
`aetheris-agents/docs/` mirror returned byte-identical, at sha256
`1b9cbf57c6864cdaecc3a07c431d51d34ee69f1ebc6afc1a664d8e167ea46f8a` on both. `drift_check` cannot
see that class; the `diff -q` is the only thing that catches it.

> **DEVIATION, recorded and not absorbed. The upload was a diff of the six stale rows, not the
> remove-all-then-upload-all this manifest requires.** The header paragraph above the table states
> the procedure and states why: **check 8 detects the repo moving ahead of an export, and never a
> file uploaded without a regen**, so a partial upload is invisible to the tooling by construction
> and the procedure is the only thing covering it.
>
> **What is different here, stated as mitigation and not as a defence.** The six were identified by
> **check 8 itself** — the `project_knowledge` WARNs standing at the gc close — rather than by eye,
> so the *selection* was mechanical rather than a judgement about which files had changed. That
> addresses the failure mode where a mover is missed; it does **not** address the one the procedure
> is actually written for, which is a file present in the store that no longer belongs there, or one
> whose stored content diverged without its commit moving. Against that, a full re-upload churns
> every chat in the project.
>
> **The arbiter has not ruled on this deviation. It is recorded as OPEN.** The next boundary either
> performs the full remove-all-upload-all or carries a ruling that the diff form is permitted, with
> its bound.

Previous export: 2026-08-09 (the hc round's close — four rows advanced).
