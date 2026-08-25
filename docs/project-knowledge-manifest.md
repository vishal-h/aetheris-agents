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
| `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `97c61a0` | 2026-08-14 |
| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `767f1e7` | 2026-08-25 |
| `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `e0c1ee2` | 2026-08-14 |
| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `fda1466` | 2026-08-23 |
| `use-cases.md` | `docs/use-cases.md` | aetheris-agents | `9cf3689` | 2026-08-19 |
| `aetheris-agents--inbox-brief.md` | `docs/aetheris/backlog/uc-inbox.md` | aetheris-agents | `a1f8daf` | 2026-08-24 |
| `aetheris-agents--ravenmigrate-brief.md` | `docs/aetheris/backlog/uc-ravenmigrate.md` | aetheris-agents | `b56aed3` | 2026-08-24 |
| `aetheris-agents--almanac-brief.md` | `docs/aetheris/backlog/uc-almanac.md` | aetheris-agents | `b56aed3` | 2026-08-24 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `a49d05a` | 2026-08-23 |
| `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `c171a78` | 2026-08-23 |
| `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `915d582` | 2026-07-25 |
| `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `1ab24d8` | 2026-07-26 |
| `aetheris--research-README.md` | `docs/aetheris/research/README.md` | aetheris | `bcf3b65` | 2026-08-24 |
| `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` | 2026-06-24 |
| `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` | 2026-06-24 |
| `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` | 2026-06-24 |
| `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` | 2026-06-24 |
| `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` | 2026-07-20 |
| `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` | 2026-07-17 |
| `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `2050c04` | 2026-08-21 |
| `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `2050c04` | 2026-08-21 |
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

> **DESIGN BRIEFS — the inclusion rule stated, 2026-08-24. Four rows added, two refused.**
> Placed here, at the end of the inclusion-rule blocks and before the section break, because
> this is the family it joins: the block above rules on runbooks and generated data, the one
> above that on working artifacts and milestone specifications. Nothing above is rewritten and
> no existing block's argument is amended; this adds the kind those blocks never reached.
>
> **The silence being closed.** Six design-brief rows have sat in the table since 2026-06-24,
> and `git grep -in "research\|brief" -- docs/project-knowledge-manifest.md` returned only
> those six table rows and no prose line at all. So the six rested on no written rule, and any
> new decision about a brief would have extended a silence rather than applied a rule.
>
> **The rule, ruled by the arbiter.** *A design brief earns a manifest row when a STORE-SIDE
> actor must read it to do its work.* The row is not a judgement about a document's importance;
> it is the mechanism by which the project store carries a document, and the store is
> claude-ui's only surface. Applied: claude-ui drafts milestone documents from design briefs,
> so a parked use-case brief awaiting milestone drafting is read store-side and earns a row.
> **A document whose reader is repo-side — reviews, implementation notes, the record of how a
> rule was reached — does not earn a row, whatever its kind.** The six research briefs already
> carry rows on exactly this ground, retroactively stated: they are the design prior art a
> milestone doc cites, and the actor citing them drafts store-side.
>
> **This is beside the rule above, not in place of it.** That block reads: *"Milestone working
> artifacts — `docs/reviews/*.md`, `*-implementation-notes.md`, scan files — are not exported.
> They are the record of *how* a decision was reached and are read from the repo by the
> sessions that need them; project knowledge carries standing reference docs."* Both tests are
> live and they agree wherever they overlap — that block asks what kind of artifact it is, this
> one asks which side of the seam its reader sits on, and the working-artifact exclusions hold
> under either. Where the earlier block is silent is on a document that is a working artifact by
> kind and unreachable to its actual reader by placement, which is what a parked brief is.
>
> **§8.3 of `aetheris/docs/methodology/prose-conventions-brief-2026-08-23.md` is OVERRULED, and
> is named so a later reader meets both positions.** That section argues the opposite: that a
> parked design brief is a working artifact on this manifest's own test, that committing briefs
> to the repo *"returns them to where the rule already places their kind — out of the manifest
> by kind, exactly as reviews and implementation notes are"*, and that the store copy becomes
> mere convenience. The commit half of that is adopted and is why the briefs are now tracked.
> The no-row half is overruled: it reasons from the artifact's kind alone and so cannot see that
> the actor who needs a brief has no way to read the repo. Under §8.3 as written, committing a
> brief would take it away from claude-ui — the one reader the document exists for — the moment
> the next remove-all-upload-all ran. **§8.1 of the same brief is ACCEPTED**, and it is this same
> rule applied rather than an exception to it: that brief gets no row because its reader is
> repo-side, being the record of how an adoption decision was reached.
>
> **Four rows added.**
> `aetheris-agents--inbox-brief.md`, `aetheris-agents--ravenmigrate-brief.md` and
> `aetheris-agents--almanac-brief.md` are the three parked use-case design briefs in
> `docs/aetheris/backlog/`, each self-declaring `**Type:** design brief` and each carrying a
> section on what a milestone doc drafted from it would contain. `uc-inbox.md` was already
> committed and is added now rather than left as the odd one out; the other two were committed
> at `b56aed3`, having existed only in the store until then. Export names follow the six research
> rows' convention, `<repo>--<short>-brief.md`, which is also the store's own name for the one
> brief whose store path either repository records — `claude/aetheris-agents--inbox-brief.md`,
> cited in the prose-conventions brief §1 — so when the `claude/` originals are deleted at a
> later boundary the replacements are legible as the same documents.
> `aetheris--research-README.md` is the fourth and is a different case: it is the only document
> that states what a brief in `aetheris/docs/aetheris/research/` IS, and without it the store has
> carried the six briefs and not the sentence defining the kind. A store-side reader needs it to
> know what it is reading.
>
> **Two refusals, recorded with their reason so the rule is seen to have a boundary.**
> `docs/aetheris/backlog/litellm-migration.md` and `docs/aetheris/backlog/payslip-view-report.md`
> sit in the same directory as the three added briefs and get **no row**. Neither is a design
> brief a store-side actor would draft a milestone from, and this is settled from each file's own
> header rather than by impression: neither carries a `**Type:**` line, neither contains the
> string *design brief* anywhere, and neither has a milestone-shape section, where all three
> added briefs have all three. What they have instead is ticket furniture — litellm declares
> `**Status:** Backlog — implement after P6`, scopes itself in three implementation phases and
> ends in `## References`; payslip-view-report declares `**Candidate backlog row:** unnumbered`,
> `**Size:** XS–S`, and ends in `## Decision points (if it becomes a ticket)` and
> `## Done-when (if filed)`. Both are specifications for repo-side work, and this manifest has
> carried specifications inside `backlog-2026-06.md` since BL-007. If either is later re-drafted
> as a design brief, the rule above reaches it and the ruling is the arbiter's.
>
> **What this edit does NOT do.** It uploads nothing. Adding a row changes what the *next*
> boundary exports and leaves the store exactly as it was, still holding its `claude/` copies of
> the three briefs; deleting those is the arbiter's act at that boundary, not this commit's.
> Only the four new rows are pinned. The four rows standing stale at this commit
> (`aetheris-agents--CLAUDE.md`, `backlog-2026-06.md`, `aetheris--CLAUDE.md`,
> `aetheris--runbook.md`) are deliberately left stale — clearing them here would assert an export
> that did not happen, which is the born-green failure the 2026-08-22 block records. Their cells
> were derived and discarded rather than never computed; see this change's implementation notes.
>
> **2026-08-24 — the first export under this rule fired the U2 sweep, and the ruling was to
> change the DOCUMENT, not the gate.** Adding `aetheris-agents--inbox-brief.md` put
> `docs/aetheris/backlog/uc-inbox.md` into the bundle for the first time and
> `assemble_export_bundle.py`'s sweep matched a live email address in its §4. The arbiter ruled
> the address substituted for an RFC 2606 documentation placeholder, **on a ground independent
> of the hit**: a design brief specifies a MECHANISM, and a live intake address is DEPLOYMENT
> CONFIGURATION — the local part and the plus-addressing scheme are the design content, the
> domain is not, and a brief naming a live endpoint is the same category error as a brief
> hardcoding a token. That argument holds whether or not the sweep ever fired, which is what
> makes it an adjudication rather than a gate being bent around an inconvenient result. A
> full-file sweep then found a SECOND occurrence, a bare domain in §8 that the email pattern
> structurally cannot match, and the same ground reached it. **`scripts/u2_patterns.txt` was not
> edited, the U2 class was not narrowed, and the row was not dropped** — the hit was the
> occasion, never the reason. Substituted at `deeb441`. The
> inclusion rule above is unchanged by this: it answers who must READ a document, while U2
> answers what may LEAVE this machine, and the two are independent gates a document can pass
> one of and fail the other.
> And the same export produced a **BL-180** instance in the very document it added: the dated note
> recording that substitution was written as a single-backtick wrapper carrying inner backticked
> terms, which inverts, and it was repaired to the blockquote form at `a1f8daf` before any of this
> was pushed — the arc's own two instances found by sweeping all seven files it touched, and the
> standing population left to BL-180. The file's row is pinned at `a1f8daf`, the repair, which is
> simply the commit that last touched it.

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

`[Re-pinned again 2026-08-12, after the export note above was written: `methodology--milestone-methodology.md`
`6bc49fc`→`66a9ca5`, the §5 pointer at the ratified-decisions registry. **R25 itself moved no tracked
row** — it lands in `docs/milestones/hc-consolidation.md`, which is `docs/milestones/` and out of the
manifest by kind, so a ruling produced no re-pin and the absence is expected rather than an omission.
Only the harness pointer that cites it is tracked.]`

**Row count 25, derived by parsing the table rather than assumed** — unchanged from the hc
boundary's 25; no row was added or removed, and the nineteen not listed above were each verified
current by the same command.

**Uploaded 2026-08-12 by claude-ui.** The mirror-pair check ran **before** the upload, per the
BL-002 convention: `diff -q` over `aetheris/docs/methodology/triad-loop.md` and its
`aetheris-agents/docs/` mirror returned byte-identical, at sha256
`1b9cbf57c6864cdaecc3a07c431d51d34ee69f1ebc6afc1a664d8e167ea46f8a` on both. `drift_check` cannot
see that class; the `diff -q` is the only thing that catches it.

> **DEVIATION, ruled 2026-08-14 — and the ruling is not the one this row was waiting for.** The
> 2026-08-12 upload was a diff of the six stale rows rather than the remove-all-then-upload-all the
> header paragraph above the table requires, and it stood OPEN against a stated condition: *the
> next boundary either performs the full remove-all-upload-all or carries a ruling that the diff
> form is permitted, with its bound*. The 2026-08-14 boundary performed a by-path rewrite again,
> deliberately, and what it established **retires that condition rather than satisfying it**.
>
> **Remove-all-upload-all is not performed, and must not be.** The store holds documents this
> manifest cannot describe — agent-written documents land under `claude/` and carry no row — so the
> procedure's remove half would delete them, silently, with no record anywhere of what was lost. A
> procedure whose first step destroys what the record cannot name is not one this manifest can
> require of an operator.
>
> **Check 1 and check 3 cannot both be applied, and this pass is what established it.**
> `prompts/bl-002-refresh-project-knowledge.md` §Post-upload verification asks for both: **check 1**,
> that the store's document set equals this table's export-name column *in both directions*, a name
> in one and not the other being the finding; and **check 3**, that a document older than the upload
> window is either an incremental-upload finding **or** a deliberate non-manifest document under
> `claude/`, out of scope. Check 3's own escape clause names a document that check 1 reads as a
> finding. They are not two checks with a hard case between them — they are two rules that
> contradict on the documents that actually exist.
>
> **The condition is therefore replaced, not discharged.** It is no longer *perform the full
> replace*. It is: **rule which of check 1 and check 3 governs, and give this manifest vocabulary
> for a document that is in the store and out of the export set.** No such word exists here today,
> which is why check 1 cannot simply be rewritten to permit one — the permission would have nothing
> to name.
>
> **The cost the diff route accepts, stated once so it is not later restated as an argument.** A
> by-path rewrite proves nothing about what else the store contains. That is precisely what check 1
> was for, and this route does not buy it back by other means: what replaces check 1 is a ruling,
> not a check. Until that ruling lands the store's completeness is **unverified**, not
> verified-some-other-way.
>
> **Still OPEN, under the replaced condition.** The contradiction is posed here, not settled.

Previous export: 2026-08-09 (the hc round's close — four rows advanced).

---

**Export boundary — 2026-08-14, the m6-cloudcost close (GitHub as provider four).** **Four rows
advanced**, each pin derived by `git log -1 --format=%h -- <path>` run in that row's own repo and
**re-derived against HEAD in the pass that wrote this section**, rather than carried from the
staging file that proposed them — the proposal was written before the upload, so its hashes were
claims about a tree that had had two days to move. It had not: the re-derivation produced the same
four.

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `cloudcost--milestone.md` | aetheris-agents | `8f36e45` | `97c61a0` | 2026-08-14 |
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `d025971` | `4d33048` | 2026-08-14 |
| `capability-matrix.md` | aetheris-agents | `4d98ec2` | `e0c1ee2` | 2026-08-14 |
| `backlog-2026-06.md` | aetheris-agents | `124707f` | `4d33048` | 2026-08-14 |

**Row count 25 — none added, none dropped.** The twenty unmoved rows were each verified current by
field in the owning repo, the twelve harness rows read in `../aetheris` at `d19f4b6`. The harness
took no tracked write this boundary.

> **What the upload actually was, recorded as performed and not as the procedure above describes
> it.** Four documents were **rewritten in place by path**. Twenty were **left untouched** as
> unchanged. `project-knowledge-manifest.md` was **deliberately not uploaded in that pass**: the
> bundle's copy of it was the pre-update one, which is what byte-identical-to-HEAD meant at
> assembly time, and putting a manifest about to be superseded into the store would have set a
> stale assertion beside twenty-four current documents while rewriting a project document
> invalidates the cached context of every chat there. So the store keeps the previous manifest
> until the next boundary re-exports this one. It **under-claims** — it says the documents are
> older than they are — which is the right way to be wrong while a change is in flight.
>
> **This is not the remove-all-then-upload-all the header paragraph above the table requires, and
> the divergence is ruled rather than carried.** See the 2026-08-12 deviation block above, whose
> condition this boundary replaced: the store holds documents this manifest cannot describe, and
> the remove half would delete them silently, so the full replace is not merely skipped here but
> ruled out.
>
> **What is not recorded here, said rather than left as a silent gap.** Check 2 of
> `prompts/bl-002-refresh-project-knowledge.md` §Post-upload verification — content on the movers
> only, read the uploaded document rather than trust the name — was **not reported back to this
> pass**, so this section makes no claim about it. The four rows above are pinned on the repo-side
> derivation, which is a different thing from having read what the store now holds.

**Mirror-pair check run per the BL-002 convention**, before this table was touched: `diff -q` over
`aetheris/docs/methodology/triad-loop.md` (canonical) and its `aetheris-agents/docs/triad-loop.md`
mirror returned **byte-identical** — 199 lines each, sha256
`1b9cbf57c6864cdaecc3a07c431d51d34ee69f1ebc6afc1a664d8e167ea46f8a` on both — so no canonical sync
was owed and that is the second reason the harness took no write. `drift_check` still has no
byte-identity check between mirrors; the `diff -q` remains the only thing covering that class.

**Why this section is dated two days before the commit that carries it.** The upload happened
2026-08-14; this manifest commit lands 2026-08-16. The gap is the ordering rule working rather than
lag — the manifest is a pointer at an export state, written last, after the state it points at has
stopped moving, so it was **held** until the project side was confirmed written. A manifest
committed on the 14th would have asserted an export that had not yet occurred. The
self-referential row keeps its 2026-08-09 date and is **not** advanced in this pass.

**Ordering invariant held.** The manifest is this boundary's only tracked write and its last;
nothing manifest-tracked was edited after the table was updated, so no row is born stale. This is
also why the meaningful `drift_check --strict` is the **post-commit** one — check 8 reads committed
history, so a run before this commit compares against pre-edit hashes and passes vacuously
(BL-034/BL-025).

Previous export: 2026-08-12 (the gc round's close — six rows advanced, uploaded as a diff).

---

**Export boundary — 2026-08-16, the BL-152 / BL-153-s0 / export-mechanism arc.** **Two rows
advanced.** Each pin was derived twice, independently and by field: once by hand with
`git log -1 --format=%h -- <path>` run in that row's **own** repo (`../aetheris` for the twelve
harness rows), and once by `scripts/repin_manifest.py`, which is new this cycle and had never
been run at a live boundary before. **The two derivations agree on all twenty-five rows** — same
two movers, same was→now, same twenty-two current — which is the point of running both rather
than trusting either.

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `4d33048` | `900662f` | 2026-08-16 |
| `backlog-2026-06.md` | aetheris-agents | `4d33048` | `8bfa5f3` | 2026-08-16 |

**Row count 25, derived by parsing the table** and not carried from the previous boundary's
figure — none added, none dropped. The parse is bound to the export table by its header row
rather than to any `|`-line in the file: a naive sweep over every pipe-delimited line returns
**37**, because the 2026-08-12 and 2026-08-14 boundary sections each carry a movers table of
their own. Twelve rows are harness, thirteen agents, one of the thirteen being the
self-referential row. All twenty-five paths exist on disk in their owning repo.

> **The `last changed` column was corrected by hand, and it is not something the re-pinner can
> do.** `scripts/repin_manifest.py` has authority over the commit cell only — stated in its own
> docstring — so it moved both movers' hashes and left both dates reading `2026-08-14`, the
> previous boundary's. Both commits are dated 2026-08-16 (`git log -1 --format=%ad --date=short`).
> Nothing checks this column: check 8 parses the commit cell and ignores the date, so a stale
> date here is invisible to `drift_check` in exactly the way the mirror pair is. Recorded so the
> next boundary knows the correction is owed by the operator rather than by the script.

> **Mirror-pair check run first, per the BL-002 convention, and it is what establishes that the
> harness takes no write at this boundary.** `diff -q` over `aetheris/docs/methodology/triad-loop.md`
> (canonical) and `aetheris-agents/docs/triad-loop.md` (mirror) returned **byte-identical** — 199
> lines and 9532 bytes each, sha256
> `1b9cbf57c6864cdaecc3a07c431d51d34ee69f1ebc6afc1a664d8e167ea46f8a` on both sides, unchanged from
> the 2026-08-14 boundary's recorded value. So no canonical sync was owed, and cross-citing pairs
> landing harness-first did not arise. `drift_check` still has no byte-identity check between
> mirrors; the `diff -q` remains the only thing covering that class, and at the 2026-08-03
> boundary it is what caught canonical running 26 lines short of its mirror.

> **The pinned content was read against what it should say, not merely confirmed current.** The
> arc closed and ruled a good deal in two days, and a correct hash over a document missing any of
> it would export the world as it was mid-flight. Verified present in `backlog-2026-06.md` at
> `8bfa5f3`: BL-152's `CLOSED 2026-08-16` marker **and** its arbiter closure block; BL-153's two
> rulings on its Owes — the arm-ordering ruling and the later placement ruling that closed what
> the first left open; BL-157, BL-158 and BL-159 filed with their rows; BL-076's 2026-08-16
> annotation; and BL-151's three seeded standing findings. Verified present in `CLAUDE.md` at
> `900662f`: the `## Learning — BL-152` block with both promoted lessons, the whole-suite gate
> restated **as a command**, and the two-marker table. Nothing closed or ruled in this window was
> found missing from a tracked file, and the harness closed nothing — its only commit since its
> last pin is `d19f4b6` (m6 t2b), which touches no manifest-tracked path.

> **Nothing was added and nothing dropped, and the inclusion rule did the deciding.** The arc
> produced no standing reference document. Out as milestone *working artifacts*, by kind rather
> than by directory: `docs/milestones/bl-152-implementation-notes.md`,
> `docs/milestones/bl-153-s0-implementation-notes.md`,
> `docs/milestones/export-mechanism-implementation-notes.md`, and the edit to
> `cloudcost/docs/m5-rescue-edit-implementation-notes.md`. Out as code and test apparatus, which
> has never carried a row: `pytest.ini`, `scripts/_manifest.py`, `scripts/repin_manifest.py`,
> `scripts/assemble_export_bundle.py`, `tests/test_export_bundle.py`,
> `tests/test_repin_manifest.py`, `tests/conftest.py` and the per-use-case test edits. Out on its
> own standing precedent: `prompts/bl-002-refresh-project-knowledge.md`, the operator procedure,
> which has never carried a row and is not a reference doc. **`capability-matrix.md` needed no
> regen and that was checked rather than assumed** — the matrix is generated per *use case*
> (`agents/capability_matrix_*.exs` + `scripts/assemble_matrix.py`), and repo-root `scripts/` is
> outside its population: `drift_check.py` and `assemble_matrix.py`, both long-standing, appear in
> it nowhere either. This arc's specifications are the BL-0xx rows, already carried inside
> `backlog-2026-06.md`.

> **Store-side census, reported by claude-ui 2026-08-16 and not verifiable from this side.**
> Recorded here as an observation with its author named, because this session has repo access only
> and cannot see the store: *the store holds thirty documents; twenty-five are exactly this
> table's export-name column, in both directions, with no name in one and not the other; the
> remaining five are all `claude/`-namespaced.* If that holds, the population the 2026-08-12
> deviation block says this manifest has no vocabulary for is precisely the `claude/` namespace,
> and the namespace is the vocabulary.
>
> **This boundary does not rule on it, and the order is deliberate.** The 2026-08-12 and
> 2026-08-14 deviation blocks are left exactly as they stand; BL-143 is **open**; and check 1
> versus check 3 of `prompts/bl-002-refresh-project-knowledge.md` §Post-upload verification
> remains the contradiction those blocks pose rather than settle. The ruling is the arbiter's and
> lands **after** this boundary is performed, not before — a boundary that ruled on its own
> deviation would be the artifact under review writing its own disposition, and the census above
> is the input to that ruling rather than its conclusion. The prompt file is untouched for the
> same reason: it is edited after the ruling, not during the boundary that supplies the evidence.

**Ordering invariant held.** The manifest is this boundary's **only** tracked write and its last;
the content sweep found nothing owed, so there was no earlier commit to make, and nothing
manifest-tracked was edited after the table was regenerated. No row is born stale. This is also
why the meaningful `drift_check --strict` is the **post-commit** one — check 8 reads committed
history, so a run before this commit compares against pre-edit hashes and passes vacuously
(BL-034/BL-025).

**Repo push state.** Both repos were level with `origin/main` (`0 0` by
`git rev-list --left-right --count`) at the exported content commits — aetheris-agents `8bfa5f3`,
aetheris `d19f4b6` — when this boundary began, so both pinned hashes are already public and
reproducible. The harness took no tracked write. **This boundary's manifest commit is held, not
pushed**, by instruction. (Deliberately no self-hash: a line naming the manifest's own commit is
stale the moment it is committed.)

Previous export: 2026-08-14 (the m6-cloudcost close — four rows advanced, uploaded by path).

---

**Export boundary — 2026-08-16, amendment pass.** The section above stands and its commit
`a2df7b5` is not rewritten; this is the second pass of the same boundary, in the sequence that
pass's own packet named — file the rows, re-pin, re-assemble, re-sweep. **Two rows advanced**, and
they are this pass's own two earlier commits rather than anything the world did:

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `backlog-2026-06.md` | aetheris-agents | `8bfa5f3` | `8653546` | 2026-08-16 |
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `900662f` | `ef651f9` | 2026-08-16 |

**Row count 25**, re-derived by parsing the table bound to its header row, not carried from the
first pass. Both derivations — by hand, by field, in each row's own repo, and
`scripts/repin_manifest.py` — agree on all 25: the same two movers, the same was→now, the same **22
rows current** on both cells, the self row untouched. That is the whole table, and it adds up in
public: **2 + 22 + 1 = 25.** The twelve harness rows were read in `../aetheris` at
`d19f4b6`, and **the mirror pair was checked again before anything was written** and is still
byte-identical (199 lines, sha256 `1b9cbf57…ea46f8a` both sides), so the harness took no write at
this pass either.

> **R-F1 — the three strings the first pass's sweep hit are NOT in class, ruled 2026-08-16, and
> they are named here so the next boundary spends seconds on them rather than a round.** They are
> `168.144.13.150` (a reserved IP, NYC1), `2405879` (a NodeBalancer id) and
> `aetheris-m3-bl069-plant` (the label this project invented for it) — the m3 BL-069 Linode plant,
> deleted, its row retired at m4 t2. **U2 is a person-and-account identity class**; it exists
> because per-person logins were paired with activity timestamps. A released reserved IP for a
> deleted resource, an instance id and a label named after our own ticket identify no one. They
> have been in eight tracked files since m2/m3 and shipped in the bundle that uploaded. **No
> scrub, and no file was edited to remove them.**
>
> **This is not a gate being narrowed to pass, and the distinction is the whole of it.** The first
> pass's needle set was *wider than the class by that pass's own statement*, so its three hits were
> never evidence about U2 — the gate did not fire, a wider net did. Under the pattern set this
> boundary commits they match nothing at all. **This paragraph is a record for a human, not an
> exclusions file for a script**: nothing reads it, nothing applies it, and no exclusion mechanism
> exists to grow — which is deliberate, because an exclusions list that can grow is how a gate
> dies quietly.

> **The sweep's basis changed at this boundary, from operator-derived values to a committed
> pattern set.** `scripts/u2_patterns.txt` is new and holds both the class's authoritative
> statement and one documented regex per class member; `assemble_export_bundle.py` reads it by
> **default**, so a sweep no longer needs a raw-capture corpus that nothing in either repo
> locates. The old `--needles` value sweep survives beside it, additive, for an operator who holds
> captures.
>
> **What that buys and what it does not is owned by BL-160, which is open and is not answered
> here.** Stated once so no later reader has to reconstruct it: a clean pattern sweep claims **no
> text in the bundle matches these patterns** — never *no identifying content*. The class members
> with no lexical signature (logins, display names, organisation and repository names, numeric ids
> **in prose**) are reachable only next to a key that names them, and that under-reach is
> enumerated in the pattern file itself. The reason the change was needed at all is BL-160's
> finding: the value sweep **never returned information in either direction, at any boundary,
> including the one that uploaded**, because the only corpus available to derive needles from is
> normalized adapter output carrying none of the class's identity fields — and nothing detected
> that, because a green from a sweep that cannot see the class is indistinguishable from a green.

> **The bundle assembled at this pass is REFUSED, and the marker is in it.** The first run of the
> committed pattern set over the live bundle returned **3 hits in `rig--runbook.md`**, all matched
> by the `email address` pattern. They are reported and **not adjudicated here** — per this pass's
> own bound, a pattern that fires is a thing for a human to rule on, and a pattern removed because
> it fired is the move R-F1 has just said this is not. `_UNSWEPT-DO-NOT-UPLOAD.txt` is present in
> the bundle and names the count.

> **Also corrected at this pass, and it was invisible to everything.** `last changed` is now
> `repin_manifest.py`'s, derived from the commit it has already resolved rather than independently
> from the path, so the two cells are two readings of one object. Until 2026-08-16 the script owned
> the commit cell and disclaimed the date, check 8 read the commit cell and ignored the date, and
> the first pass of this boundary duly re-pinned two rows to 2026-08-16 commits while both rows
> still read `2026-08-14` — corrected there by hand, and by the script from here on. Seeded to
> **BL-151** as a class rather than a defect: *a column a script owns half of is a column nobody
> owns.*

**Two rows filed, before the re-pin because the backlog is tracked.** **BL-160** — the U2 export
gate has never returned information in either direction; owns whether pattern-sweeping is
sufficient, what it misses, and whether a raw-capture corpus should exist at all. **BL-161** — the
export-mechanism round deferred a sprint arm and filed no row, recoverable only because its notes
file is committed and attributed; the omission is the arbiter's. Both cross-reference **BL-143**,
which remains open, remains the arbiter's, and is **not** ruled here. The 2026-08-12 and
2026-08-14 deviation blocks are **untouched**, and
`prompts/bl-002-refresh-project-knowledge.md` was not edited — check 1 versus check 3 is BL-143's
question and the prompt is revised after that ruling, not during a boundary that supplies its
evidence.

**Ordering invariant held, twice over.** `docs/backlog-2026-06.md` (`8653546`) and the stage-2
script and `CLAUDE.md` changes (`ef651f9`) landed in their own earlier commits; the manifest is
this pass's **last** tracked write and commits **alone**. Nothing manifest-tracked was edited after
the table was regenerated, so neither re-pinned row is born stale — and the meaningful
`drift_check --strict` is again the post-commit one, check 8 reading committed history
(BL-034/BL-025).

**Repo push state.** Nothing is pushed. `aetheris-agents` is ahead of `origin/main` by this
boundary's commits, held by instruction; `aetheris` is level at `d19f4b6` and took no write at
either pass. Every hash this table pins for an agents row therefore exists **only locally** until
those commits are pushed — stated plainly because the 2026-08-03 boundary's note is the standing
rule here: a manifest pinning a hash nobody else has describes an export nobody else can
reproduce.

Previous export: 2026-08-16, first pass (two rows advanced; bundle refused on a wider-than-class
needle set, adjudicated at this pass as R-F1).

---

**Export boundary — 2026-08-16, second amendment.** Appended; nothing above is rewritten. **Two
rows advanced**, both this pass's own single content commit:

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `ef651f9` | `fd03bf3` | 2026-08-16 |
| `backlog-2026-06.md` | aetheris-agents | `8653546` | `fd03bf3` | 2026-08-16 |

Row count **25**, re-derived by parsing the table bound to its header — 2 movers + 22 current on
**both** cells + 1 self row, and **2 + 22 + 1 = 25**. Both derivations agree: by hand, by field, in
each row's own repo, and `scripts/repin_manifest.py`. The mirror pair was checked again before
anything was written and is still byte-identical (199 lines, sha256 `1b9cbf57…ea46f8a` both sides),
so the harness took no write at this pass either.

> **R-S1 — the three hits are CLEARED, ruled 2026-08-16.** The first amendment's pattern sweep hit
> three addresses in **`rig--runbook.md`** (lines 568, 588, 651), all matched by the **`email
> address`** pattern, all inside `DOCBUILDER_CONTEXT` example values: two at `acme.example` and one
> at `northwind.example`, companies that runbook invents. **RFC 2606 §2** reserves the `.test`,
> `.example`, `.invalid` and `.localhost` TLDs and the `example.com` / `example.net` /
> `example.org` second-level names for documentation, and **RFC 6761 §6** gives three of them their
> special-use registrations. An address at a reserved documentation domain is the standard's
> **designated non-address** — definitionally nobody's — and so is not an email address in the
> sense U2 means. All three cleared. **No file was edited to remove them.**
>
> **This is an adjudication of documented OVER-REACH, not a narrowing of the class.** The
> over-reach was written down before it fired: the pattern file's own OVER-REACH paragraph already
> said the email pattern *"likewise matches `someone@example.com`"*. The class is unchanged — email
> addresses are still scrubbed — and what changed is the pattern's expression of it. **The test
> that separates this from removing an inconvenient pattern is now carried in `CLAUDE.md` and in
> `u2_patterns.txt`, so the record explains itself rather than resting on precedent:** *an
> adjudication may change a gate ONLY when the change is derivable from the class definition, or
> from a standard independent of the hit, such that you would have written it had you thought of it
> first. The hit is the OCCASION, never the REASON.* The exclusion passes it — `@example.com` is
> the canonical placeholder by a standard predating any hit here. It is scoped to exactly the
> reserved list: a reserved name used as a *subdomain* of a real domain still matches, and so does
> `examples.com`, both pinned by a test.
>
> Recorded because the order is the rule working: the session that found the hits **refused to
> clear them and named the candidate fix without making it**, on the ground that at that moment the
> only argument for the change was that it would turn the run green.

> **The class statement moved to `CLAUDE.md`, and the reason is governance rather than tidiness.**
> The first amendment established that U2 had **no committed standing definition** — it was written
> at m6-cloudcost t2 and lived only in `cloudcost/docs/m6-t2-implementation-notes.md` §U2, a
> milestone working artifact this manifest excludes **by kind**. So the rule governing what may
> leave the machine was unreachable from the export it governs, which is the same defect as a
> deferred finding living in a notes file, one level up. It was put into `scripts/u2_patterns.txt`
> at that pass, which fixed **reachability and not governance**: a script's data file is not a
> governing document. It now lives in `CLAUDE.md` §Definition of done — which **is** manifest-tracked
> and exported — with `u2_patterns.txt` holding the patterns and the under/over-reach enumeration
> and pointing back rather than restating. That is the split **BL-152** set for the `integration`
> marker: the criterion in `CLAUDE.md`, the mechanism in the file that implements it. The notes file
> is untouched and is now the historical record of how the class was reached.

**Ordering invariant held.** `CLAUDE.md` and `docs/backlog-2026-06.md` moved together in one
earlier content commit (`fd03bf3`); the manifest is this pass's **last** tracked write and commits
**alone**. Nothing manifest-tracked was edited after the table was regenerated.

**Repo push state.** Unchanged and still nothing pushed: `aetheris-agents` is ahead of
`origin/main` by this boundary's commits, held by instruction, so every agents hash this table pins
exists only locally until they are pushed; `aetheris` is level at `d19f4b6` and took no write at any
of the three passes.

Previous export: 2026-08-16, first amendment (two rows advanced; bundle refused on three
documentation addresses, cleared here as R-S1).

---

**Export boundary — 2026-08-18, the ds boundary.** Appended; nothing above is rewritten. **Four
rows advanced:**

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `fd03bf3` | `43e63e0` | 2026-08-17 |
| `backlog-2026-06.md` | aetheris-agents | `fd03bf3` | `6436b25` | 2026-08-18 |
| `methodology--milestone-methodology.md` | aetheris | `66a9ca5` | `8eb960d` | 2026-08-18 |
| `methodology--triad-loop.md` | aetheris | `b400b12` | `9ba6c8c` | 2026-08-17 |

Every one moved **both** cells, and none moved a date without its commit — the date is
`repin_manifest.py`'s from the 2026-08-16 second amendment on, derived from the commit it has
already resolved rather than independently from the path. The other twenty rows reported current.
Row count **25**, re-derived by parsing the table bound to its header row rather than carried from
the previous boundary: 4 movers + 20 current + 1 self row, and **4 + 20 + 1 = 25**; thirteen agents
rows, twelve harness. The naive pipe-line sweep the 2026-08-16 section warns about now returns
**53** where that section recorded **37** — the figure moves with the movers table every boundary
adds, which is exactly why the parse is bound to the header row and not to the pipe character.

> **The re-pin's changed-row set was compared against check 8's WARN set, and the two instruments
> had never been run against each other.** Stage A read check 8's WARNs at `559199b`, before
> anything was edited, and `scripts/repin_manifest.py` then moved four rows: **the same four**, in
> the same direction, with no row in one set and not the other. The comparison is worth recording
> because the two answer one question by different routes and neither was written as a control on
> the other — check 8 compares each row's pinned hash against that file's own last-touching commit
> and *reports*; the re-pinner resolves the same commit and *writes*. Their agreement is the first
> evidence either is sound against the other, and a disagreement would have been a defect in one of
> them rather than in the manifest.

> **The bundle.** Twenty-five documents, assembled by `scripts/assemble_export_bundle.py` from
> `git show HEAD:<path>` and not from the working tree, at aetheris `8eb960d` and aetheris-agents
> `9b9b274`. Manifest ↔ bundle set equality was checked **in both directions** with **both control
> arms fired**, and the U2 sweep returned clean. In the narrow words the standing rule requires:
> **no text in the bundle matched the patterns in `scripts/u2_patterns.txt`** — never *no
> identifying content*, the class members with no lexical signature being reachable only beside a
> key that names them (`CLAUDE.md` §Definition of done; BL-160, open). These are **stage A's
> figures, carried on attribution rather than re-derived here**: this stage is under a standing
> prohibition on re-running the assembler, because re-running it would restart a boundary whose
> store side is already verified.

> **Who performed the upload, and that the first attempt failed.** claude-ui attempted the
> remove-all-upload-all against the store and **could not complete it.** It removed all twenty-five
> documents and was then unable to write any of them back: its Projects tool forces a **new bare
> filename into the `claude/` namespace**, so deleting a top-level document destroys the only
> handle that permits writing to that path. The store was left empty of the manifest set, and **the
> human uploaded the bundle by hand.** Recorded plainly because it is how this boundary actually
> ran, and because it is evidence BL-143's ownership question needs: the actor the procedure
> addresses cannot perform the procedure's first half, which is a fact about the tool rather than
> about the operator. The finding is BL-165's and is appended there in the same commit as this
> section.

> **The three post-upload checks, run by claude-ui against the store on 2026-08-18 and reported —
> attributed, not asserted.** Nothing in this repository can see the store, and a packet reporting
> a store is not the store; what follows is claude-ui's report with its author named, on the idiom
> the 2026-08-16 store-side census established for exactly this reason.
> **Check 1** — twenty-five names, set equality against the manifest's export-name column in both
> directions, with both controls fired. **Check 2** — all **five** movers carry new content,
> verified by one full read and by targeted content checks, the bundle having been verified
> byte-exactly beforehand at **25/25 sha256** with a negative control. **Check 3** — all twenty-five
> created inside a **3.6-second** window, the only older documents `claude/`-namespaced.
>
> **Check 2's five against this table's four is not a discrepancy, and it is derivable from this
> side.** The manifest's own row carries `_(this export)_` and can therefore never appear as a mover
> in a movers table, while the document itself is in the bundle and its content did change.
> Derived here rather than taken on the report's word: comparing the blob of each of the twenty-five
> tracked paths between the previous export's endpoints (agents `84c24c7`, harness `d19f4b6`) and
> this one's (`9b9b274`, `8eb960d`) returns exactly **five** — the four rows above plus
> `project-knowledge-manifest.md`. Four rows advanced; five documents changed; the two figures count
> different things and both are right.

> **Two firsts, and they are why this section runs longer than its movers table warrants.** This is
> the first boundary whose **three post-upload checks were performed by an instrument rather than by
> convention** — every previous boundary either recorded them as done on the operator's word, or
> recorded (2026-08-12, 2026-08-14) that they could not be applied at all; the nearest precedent is
> the 2026-08-16 store-side census, which is where the attribution idiom above comes from and which
> was a census rather than the checks. And it is the **first run of BL-163's corrected check 3**,
> with its namespace clause stated, so *"the only older documents are `claude/`-namespaced"* is a
> verdict the check can express rather than an exception a reader has to supply. BL-163 closed at
> `7e8602d`; the ruling it implements is BL-143's of 2026-08-16.

> **Mirror-pair check, per the BL-002 convention.** `diff -q` over
> `aetheris/docs/methodology/triad-loop.md` (canonical) and `aetheris-agents/docs/triad-loop.md`
> (mirror) → **byte-identical**: **203 lines** and sha256
> `847b107e4063db61a2510b2b174d8adf36ae1670d053dc33366cb2f8353dcb5a` on both sides. Both figures
> **moved** from the 2026-08-16 boundary's 199 lines and `1b9cbf57…ea46f8a`, canonical having
> changed at `9ba6c8c` — and they moved **together**, which is the whole of what this check buys.
> Re-derived at this stage rather than carried from stage A: neither repo has taken a write to
> either copy since, both being clean at the commits named above. `drift_check` still has no
> byte-identity check between mirrors, and the `diff -q` remains the only thing covering that class.

**Ordering invariant held at stage A, and this commit deliberately breaks the pin.** The manifest
was stage A's **only** tracked write and its last, landing alone at `9b9b274`; two of the four
values it pins are that session's own earlier commits (`7e8602d`, `6436b25`), which is why it had
to. **The commit carrying this section is post-boundary work and re-stales one row on purpose** —
`docs/backlog-2026-06.md` moves again for the filings it lands — and it is **not** re-pinned.
Re-pinning to chase the WARN would silently restart a boundary whose store side is already
verified, and the store would then describe a commit the manifest no longer pins. The resulting
`project_knowledge` staleness WARN is the one the strict-mode exemption exists for (`CLAUDE.md`
§Definition of done), and it is expected truth until the next export, not a regression.

No **Repo push state** paragraph, and the omission is deliberate: per the standing note below, no
boundary record written from here on asserts push state.

Previous export: 2026-08-16, second amendment (two rows advanced; the three documentation addresses
cleared as R-S1).

---

**2026-08-16 — the replaced condition is DISCHARGED, by BL-143's ruling of the same date**
(`docs/backlog-2026-06.md`, BL-143): check 1 and check 3 both govern and were never in conflict,
the namespace divides their populations, and remove-all-upload-all is rehabilitated scoped to the
manifest set. Neither deviation block is amended — the 2026-08-12 block set the condition, the
2026-08-14 block replaced it, both are point-in-time records, and their reason was right at the
scope either could establish. Standing form: `CLAUDE.md` §Definition of done.

---

**2026-08-21 — one row ADDED, one row REFUSED, and NO BOUNDARY WAS RUN.** This is not an export
pass. Nothing was assembled, nothing was uploaded, no other row was re-pinned, and the three
post-upload checks were not performed and are not owed. The commit carrying this section is the ds
cycle's close.

> **`docs/use-cases.md` EARNS a row.** It is the committed registry of the use cases — one row per
> use case with its status, the date that status was set, and its condition for return — and
> `drift_check.py`'s `use_case_registry` check compares `CLAUDE.md`'s key-docs table against it, so
> it is a checked enumeration rather than a document about one. It meets the milestone-*specification*
> test that admits `cloudcost--milestone.md`, `rig--protocol.md` and `rig--bl-007-milestone.md`:
> what it carries is the thing other documents are written against, not derived reasoning about
> something that lives elsewhere. It is also the document `CLAUDE.md` now points at instead of
> naming the use cases in a sentence — the exported `CLAUDE.md` de-numeralised that enumeration into
> a pointer, and a pointer whose target is outside the export set points out of the store.

> **`docs/milestones/ds-milestone.md` gets NO row — on the `cloudcost/m3-milestone.md` reasoning,
> applied at the close as that question was reserved for.** ds is a cycle document: it holds derived
> reasoning *about* rules whose normative text lives elsewhere — methodology §6 and §11, R22–R27 in
> `docs/milestones/hc-consolidation.md`, and the two `CLAUDE.md` files — and its own close records
> that its outputs landed in those documents rather than in it. m3's file was refused on exactly
> this: it reasons against a contract that is m1's, unchanged. m2's milestone doc set the precedent
> by staying out on the same reading. The rulings this cycle produced are exported through the
> documents that carry them, which is the correct shape; a row here would export the reasoning and
> duplicate the conclusions. The question was deliberately deferred to the close on the ground that
> deciding it earlier would pre-empt a test that needs the finished document — the document is now
> finished, and the test says no.

> **The new row is UNEXPORTED until the next boundary, and the consequence is stated rather than
> left to be discovered.** `docs/use-cases.md` has never been uploaded. The store does not hold it.
> The exported `aetheris-agents--CLAUDE.md` points a reader at it — *"The current use cases are the
> rows of `docs/use-cases.md`"* — so **the store currently carries a pointer to a document the store
> does not have**, and it will until the next export runs. That is the manifest's known-blind
> direction, from the other side: the header paragraph above says check 8 detects the repo moving
> ahead of an export and cannot detect a file uploaded without a regen; this is a row regenerated
> without an upload, which check 8 also cannot see, and for the same structural reason — it compares
> the manifest against git and never against the store.

> **What check 8 does with this row, said plainly because a green here means less than it looks.**
> The row is pinned at `9cf3689` / 2026-08-19, which is `git log -1 --format=%h -- docs/use-cases.md`
> and that commit's own date — the two readings of one object that `repin_manifest.py` performs, done
> by hand here because no re-pin was run. The file has not moved since. So check 8 compares pinned
> against current, finds them equal, and the row is **born green and emits no WARN** — on its first
> boundary as on every one after. A currency check cannot distinguish *"exported at this commit"*
> from *"never exported, pinned at this commit"*, because both present as a pin equal to HEAD's last
> touch of the file. The green is evidence about the pin. The paragraph above is the only thing in
> either repo recording that the document behind it is not in the store.

No **Repo push state** paragraph, per the standing note below.

Previous export: **2026-08-18, the ds boundary** (four rows advanced; its two firsts recorded in
that block). **This entry is not an export** and does not advance that line.

---

**Export boundary — 2026-08-22.** Appended; nothing above is rewritten. **Four rows advanced:**

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `43e63e0` | `38009fd` | 2026-08-21 |
| `backlog-2026-06.md` | aetheris-agents | `6436b25` | `eb5442d` | 2026-08-22 |
| `methodology--milestone-methodology.md` | aetheris | `8eb960d` | `2050c04` | 2026-08-21 |
| `methodology--triad-loop.md` | aetheris | `9ba6c8c` | `2050c04` | 2026-08-21 |

Row count **26**, parsed bound to the table's header row rather than carried from the previous
boundary: 4 movers + 21 current + 1 self row, and **4 + 21 + 1 = 26**; fourteen agents rows, twelve
harness. The previous boundary recorded 25 — the ds close added `docs/use-cases.md` and nothing has
been dropped, so the set grew by exactly that row.

**What the movers carry.** `aetheris-agents--CLAUDE.md` gains the whole ds cycle: the use-case
registry pointer that replaced a hand-maintained enumeration, the corrected cap-rule example, the
`export_mechanism` arm's description, and §`## Learning — ds`. `backlog-2026-06.md` carries BL-172's
close, BL-171, BL-169, the ds close's own filings, and the two BL-150 appends this boundary made
(below). Both harness rows move to the same commit, `2050c04` — §6's three fields going optional
with Done-check staying required — which is why they share a hash and a date.

> **Step 0 ran, and its verdict was PASS.** The arm is
> `cd ~/sandbox/elixirws/aetheris && ./scripts/sprint.sh export_mechanism`, run before anything was
> written. Six assertions, six green, exit 0: `repin_manifest.py --dry-run` exits 0 leaving the
> tracked manifest byte-identical at sha256 `ef1cc626c037`, compared across the run rather than
> assumed; `repin_manifest.py` against an unreadable `--manifest` exits 1 into the shell;
> `assemble_export_bundle.py DEST` exits 0 writing a bundle carrying the manifest's own row; the U2
> sweep left no `_UNSWEPT-DO-NOT-UPLOAD.txt`; a non-empty destination without `--replace` exits 1;
> the temp destination was removed and no tracked file was written. **This is the first boundary to
> execute Step 0**, which landed at agents `b56a6b2` (ds t3) after the previous boundary had already
> run. Recorded here because the procedure requires it: this sentence is BL-161's branch 1 reaching
> an executor rather than remaining a promise, and it is what makes the arm *named in a boundary
> record* rather than merely existing.

> **`docs/use-cases.md` is EXPORTED FOR THE FIRST TIME at this boundary, and its green says less
> than it looks.** The row was added at the ds close (`38009fd`) and pinned by hand at `9cf3689`,
> the commit that last touched the file. The file has not moved since, so check 8 compares pinned
> against current, finds them equal, and the row has emitted no WARN on any run — **born green**, on
> its first boundary as on every one after. A currency check cannot distinguish *exported at this
> commit* from *never exported, pinned at this commit*: both present as a pin equal to HEAD's last
> touch. **So the row's silence was never evidence the document was in the store, and it is not
> evidence now that it arrived.** What establishes arrival is a content check, and this boundary ran
> one: `use-cases.md` is present in the bundle under its manifest export name, and its bytes equal
> `git show HEAD:docs/use-cases.md` — sha256 `9e8aabb23a56…` on both sides, `cmp` exit 0, with a
> negative control against another bundle document returning exit 1 so the comparison is known to
> discriminate. Until the upload half completes, the exported `aetheris-agents--CLAUDE.md` still
> points a store reader at a document the store does not hold.

> **What stayed out, and on what rule.** `docs/milestones/ds-milestone.md` stays out on the ds
> close's ruling, unchanged and not revisited here: it is a cycle document holding derived reasoning
> about rules whose normative text lives elsewhere, which is the `cloudcost/m3-milestone.md`
> reasoning. Nothing else was added or removed, and no row was dropped. The manifest's table is the
> sole authority for the set; this boundary did not edit it except through `repin_manifest.py`.

> **One export-set question is OPEN and this boundary does not settle it.**
> `docs/backlog-2026-06-closed.md` carries **no row**. It was created at `f9328aa` (ds t1b) when the
> backlog split, taking 80 closed rows with it, and the ds close adjudicated the export set two days
> later — *"one row ADDED, one row REFUSED"* — without considering it. From this export the store
> holds the open half only. **Check 8 cannot see this**: it compares each *existing* row's pin
> against that file's last-touching commit, so a file with no row is not a row it can find missing —
> the same structural blindness as the born-green case above, arriving from a third direction, a
> tracked document splitting in two with one half keeping the row. It is **not settled here**
> deliberately: Step 1 of `prompts/bl-002-refresh-project-knowledge.md` reserves adding or removing a
> document to a deliberate edit with its reason recorded in this prose, and a session executing the
> procedure is the wrong actor to widen the set it is uploading. **A ruling is owed either way** — a
> row, or a stated refusal on the reasoning that keeps `ds-milestone.md` out. Filed at agents
> `eb5442d` on BL-150.

> **The procedure disagrees with `repin_manifest.py` in Step 2, and that was found by running Step
> 0.** Step 2 says the re-pinner rewrites the commit cell *"touching nothing else — not the prose,
> not the `last changed` column, not the self-referential row"*. Two of those three exclusions hold
> and were observed to hold at this boundary; the `last changed` exclusion is false and has been
> since 2026-08-16, when that cell stopped being unowned. The dry-run prints a date move beside every
> commit move. Filed at agents `fa65516` on BL-150, as an extension of that row's `2026-08-21` append
> — which is right in its clause and short in its enumeration, having recorded the false claims as
> *"all in Step 3"*. **No fix**: the procedure is not this boundary's to edit.

> **Mirror-pair check, per the BL-002 convention.** `diff -q` over
> `aetheris/docs/methodology/triad-loop.md` (canonical) and `aetheris-agents/docs/triad-loop.md`
> (mirror) → **byte-identical**: **205 lines** and sha256
> `16432ded5f3117459c4f0b9f88271903c7b3d3eec227442fedad52982f0ab50b` on both sides, with a negative
> control against `milestone-methodology.md` returning exit 1 so `diff -q` is known to discriminate.
> Both figures **moved** from the previous boundary's 203 lines and `847b107e…3dcb5a`, canonical
> having changed at `2050c04` — and they moved **together**, which is the whole of what this check
> buys. The exported copy is canonical: the bundle's `methodology--triad-loop.md` carries the same
> `16432ded5f31` prefix. `drift_check` still has no byte-identity check between mirrors, and the
> `diff -q` remains the only thing covering that class.

> **The bundle, and the fixed point this record cannot reach.** Assembled by
> `scripts/assemble_export_bundle.py` from `git show HEAD:<path>` and never from the working tree,
> both repos clean. Twenty-six documents. Manifest ↔ bundle set equality was checked **in both
> directions** with **both control arms fired** — dropping a manifest name surfaced it in one
> direction, adding a phantom bundle name surfaced it in the other — and the U2 pattern sweep
> returned clean. In the narrow words the standing rule requires: **no text in the bundle matched the
> patterns in `scripts/u2_patterns.txt`** — never *no identifying content*, the class members with no
> lexical signature being reachable only beside a key that names them (`CLAUDE.md` §Definition of
> done; BL-160, open). Those figures are from the verification assembly at agents `78c81a3`. **The
> delivered bundle is assembled at the commit carrying this record, and no record can state a
> verified result about a bundle that contains it** — the manifest is itself a row, so a claim about
> the delivered artifact's sweep would have to be written before the run that produces it. The
> delivered run's own output is published in this boundary's review packet,
> `export-boundary-2026-08-22-packet.md`. The previous boundary shipped its bundle at stage A and its
> record at stage B, so the store's manifest there does not carry that boundary's own record; this
> one does, at the cost of the paragraph you are reading.

**Ordering, and why the re-pin ran twice.** Four agents commits. `fa65516` and `eb5442d` are the two
BL-150 appends; each moves `docs/backlog-2026-06.md`, which is manifest-tracked, so each lands
**before** a re-pin rather than after — landing either after Step 2 would stale that row the instant
it landed, which is the BL-034 invariant this file's Constraints section states. `78c81a3` carried
the re-pinned table alone, so the table could reach the bundle through `git show HEAD:`. This commit
carries the second re-pin, of the `backlog-2026-06.md` row only (`fa65516` → `eb5442d`), together
with this record — the record states the bundle's facts, which are not facts until the run that
produces them has exited. Commits touching only this file stale nothing: the self-referential row is
`_(this export)_` and check 8 skips it by design. Nothing was written in the harness repository at
this boundary; the two harness rows move to a commit that already existed there.

No **Repo push state** paragraph, per the standing note below.

Previous export: **2026-08-18, the ds boundary** (four rows advanced; 25 rows; its two firsts
recorded in that block).

**Export boundary — 2026-08-25, the design-brief boundary.** Appended; nothing above is
rewritten. **Four rows advanced:**

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `38009fd` | `767f1e7` | 2026-08-25 |
| `backlog-2026-06.md` | aetheris-agents | `eb5442d` | `fda1466` | 2026-08-23 |
| `aetheris--CLAUDE.md` | aetheris | `fdb1d64` | `a49d05a` | 2026-08-23 |
| `aetheris--runbook.md` | aetheris | `2ebc59c` | `c171a78` | 2026-08-23 |

Row count **30**, parsed bound to the table's header row rather than carried from the previous
boundary: 4 movers + 25 current + 1 self row, and **4 + 25 + 1 = 30**; seventeen agents rows,
thirteen harness. The previous boundary recorded 26 — the design-brief edit of 2026-08-24 added
four rows and nothing has been dropped, so the set grew by exactly those four.

**THESE FOUR MOVERS ARE THE FOUR THAT STOOD STALE, and clearing them is what makes this
commit different from the last three re-pins.** Each of the three preceding rounds re-pinned
against a scratch copy, or re-pinned and deliberately left these four alone, because no export
was happening and clearing them would have asserted one that had not — the born-green failure
the 2026-08-22 block records. **An export IS happening here**, so `repin_manifest.py` was run
against the tracked manifest **unrestricted**, with no scratch-copy splice, and the four
cleared. That switch is deliberate and is stated because the habit of the last three rounds is
the opposite and a later reader would otherwise read this as a slip.

**And the four rows added on 2026-08-24 were BORN CURRENT, not moved.**
`aetheris-agents--inbox-brief.md` (`a1f8daf`), `aetheris-agents--ravenmigrate-brief.md` and
`aetheris-agents--almanac-brief.md` (both `b56aed3`), and `aetheris--research-README.md`
(`bcf3b65`) were pinned by hand when the rows were added and none has moved since, so they do
not appear in the movers table above. **Their absence from it is not evidence they were
exported** — that is the born-green trap the 2026-08-22 block states in full for
`use-cases.md`, and it applies to all four here for the same reason: a currency check cannot
distinguish *exported at this commit* from *never exported, pinned at this commit*. What
establishes arrival is the upload and the post-upload content check, not this table.

**This is the FIRST EXPORT CARRYING THE DESIGN-BRIEF ROWS, and the first run of any kind under
the inclusion rule the DESIGN BRIEFS block above states.** That block was written on 2026-08-24
and added its four rows; it uploaded nothing, by its own terms. So the rule — *a design brief
earns a manifest row when a STORE-SIDE actor must read it to do its work* — has until now
determined only what the table says. This boundary is the first time it determines what the
store holds. Three parked use-case briefs and the research README reach the store here for the
first time; two documents in the same directory as the three briefs
(`docs/aetheris/backlog/litellm-migration.md`, `docs/aetheris/backlog/payslip-view-report.md`)
were refused rows by that block and are correctly absent.

**The U2 class boundary landed at `767f1e7` and is cited, not restated.** `CLAUDE.md`
§Definition of done now scopes the U2 class to THIRD PARTIES and records the instrument's
bare-domain gap. Read it there. Two consequences for this record and no more: the operator's
own company name or domain inside the operator's own reference documents is out of the class,
so no document in this bundle is owed a substitution on that ground; and the `uc-inbox.md`
address substituted at `deeb441` stands on a SEPARATE ground — a live endpoint is deployment
configuration, not specification — which never depended on U2 and did not move with the
scoping. That is why `aetheris-agents--inbox-brief.md` exports with a placeholder domain while
this record declines to scrub anything else.

> **Step 0 ran, and its verdict was PASS.** The arm is
> `cd ~/sandbox/elixirws/aetheris && ./scripts/sprint.sh export_mechanism`, run before anything
> was written. Six assertions, six green, exit 0: `repin_manifest.py --dry-run` exits 0 leaving
> the tracked manifest byte-identical at sha256 `d0dd6974e2fe`, compared across the run rather
> than assumed; `repin_manifest.py` against an unreadable `--manifest` exits 1 into the shell;
> `assemble_export_bundle.py DEST` exits 0 writing a bundle of **30** documents carrying the
> manifest's own row; the U2 pattern sweep returned `[PASS]` over 19 patterns and left no
> `_UNSWEPT-DO-NOT-UPLOAD.txt`; a non-empty destination without `--replace` exits 1; the temp
> destination was removed and no tracked file was written. Recorded here because the procedure
> requires it: this sentence is BL-161's branch 1 reaching an executor rather than remaining a
> promise, and it is what makes the arm *named in a boundary record* rather than merely
> existing. The arm ran a **second** time as a post-commit gate; both runs and any difference
> between them are published in this boundary's review packet.

> **Mirror-pair check, per the BL-002 convention.** `diff -q` over
> `aetheris/docs/methodology/triad-loop.md` (canonical) and `aetheris-agents/docs/triad-loop.md`
> (mirror) → **byte-identical**: **205 lines** and sha256
> `16432ded5f3117459c4f0b9f88271903c7b3d3eec227442fedad52982f0ab50b` on both sides, with a
> negative control against `milestone-methodology.md` returning exit 1 so `diff -q` is known to
> discriminate. Both figures are **unmoved** from the previous boundary, canonical not having
> changed since `2050c04`. `drift_check` still has no byte-identity check between mirrors, and
> the `diff -q` remains the only thing covering that class.

> **`docs/backlog-2026-06-closed.md` STILL CARRIES NO ROW, and this boundary does not settle it
> either.** The question was filed on **BL-150**, reserved rather than ruled at the 2026-08-22
> boundary, and left untouched by the 2026-08-24 design-brief edit, which recorded it as *"a
> different question from this one"* and out of that scope. It is reserved here for the reason
> the 2026-08-22 block gives and which has not weakened: Step 1 of
> `prompts/bl-002-refresh-project-knowledge.md` reserves adding a document to a deliberate edit
> with its reason recorded in this prose, and a session executing the procedure is the wrong
> actor to widen the set it is uploading. **A ruling is still owed either way** — a row, or a
> stated refusal.
>
> **The measured consequence has NOT changed, and it has grown.** It remains that a search of
> the exported backlog returns nothing for a closed row's id. Re-measured at this commit rather
> than carried: for `BL-161`, `BL-152`, `BL-002`, `BL-069` and `BL-135`, a heading search over
> the exported `docs/backlog-2026-06.md` returns **0** for every one, while the same search over
> the unexported `docs/backlog-2026-06-closed.md` finds each. A positive control — `BL-160`, an
> open row — returns a hit in the exported half, so the search discriminates rather than being
> blind. The population is larger than when the question was filed: the file held **80** closed
> rows at the split and the count is reproducible with
> `command grep -cE '^###* .*BL-[0-9]+ —' docs/backlog-2026-06-closed.md`, so a later reader
> replaces the figure rather than trusting it. Every row closed since the split has joined the
> set the store cannot see.

> **The store will hold `claude/` COPIES OF THREE BRIEFS that this export also delivers under
> their row names, and deleting the originals is the arbiter's act after the upload — not this
> commit's.** The three paths, named so the deletion needs no reconstruction:
>
> - `claude/aetheris-agents--inbox-brief.md`
> - `claude/aetheris-agents--ravenmigrate-brief.md`
> - `claude/aetheris-agents--almanac-brief.md`
>
> **Only the first is a path this repository has ever read; the other two are inferred and are
> flagged as such rather than presented as observed.** A sweep for `claude/…` paths across both
> repositories returns exactly one brief path, the inbox one, cited in
> `aetheris/docs/methodology/prose-conventions-brief-2026-08-23.md` §1; the ravenmigrate name is
> additionally corroborated by the 2026-08-09 store read-back recorded in
> `docs/milestones/hc-consolidation.md`, which enumerated `aetheris-agents--ravenmigrate-brief`
> among the three `claude/` documents then present. The almanac name is inferred from the
> `<repo>--<short>-brief.md` convention alone. If a store name differs the mismatch surfaces
> when the arbiter goes to delete, and it is cosmetic. **These are check-3 population, not
> check-1 findings**: a `claude/`-namespaced document carries no row and is out of the export set
> by construction, per BL-143's ruling and `CLAUDE.md` §Definition of done. They are enumerated,
> not judged, and the remove-all half of this upload does not touch them.

> **The bundle, and the fixed point this record cannot reach.** Assembled by
> `scripts/assemble_export_bundle.py` from `git show HEAD:<path>` and never from the working
> tree, both repositories clean. **Thirty documents.** The harness HEAD at assembly is
> `bcf3b65`, unmoved through this boundary — nothing was written in that repository. The agents
> HEAD at assembly is **the commit carrying this record**, whose hash this paragraph cannot
> state from inside itself: the manifest is itself a row, so any claim here about the delivered
> bundle would have to be written before the run that produces it. That is the same fixed point
> the 2026-08-22 block names, and it is paid the same way — the delivered run's own output, its
> file count and its U2 sweep result are published in this boundary's review packet,
> `export-boundary-2026-08-25-packet.md`. What this record does assert is the property, not the
> result: the bundle is deterministic given the two HEADs, and its membership is derived from
> the table above rather than from any list a session holds.

**Ordering.** Two agents commits, and the split is forced. `CLAUDE.md` is manifest-tracked, so
the U2 class edit lands in the FIRST commit and the re-pin in the second: a row cannot pin to
the commit that moves it, and landing the edit after Step 2 would stale that row the instant it
landed, which is the BL-034 invariant this file's Constraints section states. The second commit
carries the re-pinned table and this record together — the record states the bundle's facts,
which are not facts until the run that produces them has exited. Commits touching only this file
stale nothing: the self-referential row is `_(this export)_` and check 8 skips it by design.
Nothing was written in the harness repository at this boundary; its two rows move to commits
that already existed there.

No **Repo push state** paragraph, per the standing note below.

Previous export: **2026-08-22** (four rows advanced; 26 rows; the Step 0 first and the
`use-cases.md` born-green case recorded in that block).

---

`[2026-08-18 — the Repo push state paragraphs in this file are point-in-time
claims and are not maintained. Every one that asserts a boundary's commits are
held and unpushed now reads false: each commit they name is on its repo's
origin/main. Some went false the same day they were written, with nothing
noting the change — the measured figure is on BL-151 and is deliberately not
restated here, both to keep one surface for it and because it is not
re-derivable from a clone: `git branch -r --contains <sha>` answers whether a
commit is public now and never when it became public, and the only local
evidence of timing is a reflog that is machine-local and depth-limited. The
paragraphs are left as written because they are a record rather than an
instruction. A reader asking whether a named commit is public runs
`git branch -r --contains <sha>`. No boundary record written from here on
asserts push state. The class is BL-151's; this note is not a new filing.]`
