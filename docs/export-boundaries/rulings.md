# Project-knowledge manifest — inclusion rulings
Moved from docs/project-knowledge-manifest.md at 1592c95, 2026-09-15. Body verbatim, lines 154–466 of that file; corrections append below.

---

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

> **THE CLOSED BACKLOG HALF — ruled 2026-08-25. One row added, and a question reserved at three
> boundaries is settled.** Placed here, in the inclusion-rule family, beside the DESIGN BRIEFS
> block whose test this applies. Nothing above is rewritten and no existing block's argument is
> amended.
>
> **What was reserved.** `docs/backlog-2026-06-closed.md` was created at `f9328aa` (ds t1b) when
> the backlog split, taking the then-closed rows with it, and has carried no row since. The ds
> close of 2026-08-21 adjudicated the export set two days later without considering it; the
> 2026-08-22 boundary filed the question on **BL-150** and reserved it; the 2026-08-24
> design-brief edit recorded it as out of scope; the 2026-08-25 boundary reserved it again. A
> ruling was owed either way — a row, or a stated refusal.
>
> **Ruled: it earns a row.** The test is the DESIGN BRIEFS block's, applied unchanged — *a
> document earns a manifest row when a STORE-SIDE actor must read it to do its work.*
>
> **The argument, in one sentence: promotion carries RULES forward and does not carry
> DISPOSITIONS.** Methodology §7's ritual moves a closed row's durable rule into `CLAUDE.md`, the
> methodology, or `docs/milestones/hc-consolidation.md`, and it works — BL-161's branch-1 detail
> was needed store-side on 2026-08-25 and was reachable from a promoted paragraph. But a row's
> **Done-when, its closure basis, and the arbiter's reasoning at closure** are promoted nowhere.
> BL-047's Done-when was needed store-side the same day and no promoted surface carried it; it
> had to be read out of the row by a repo-side session. *Was this settled, and on what basis* is
> the question a reviewer asks most often, and it is the one question the store cannot answer for
> the closed half.
>
> **The precedent, which makes this an application rather than a new rule.** `docs/use-cases.md`
> earned its row at the ds close of 2026-08-21 partly because the exported `CLAUDE.md` pointed at
> a document the store did not hold — recorded in that block as *"the store currently carries a
> pointer to a document the store does not have"*. The exported `backlog-2026-06.md` references
> closed rows by id throughout, and the 2026-08-25 boundary measured it: a heading search for
> `BL-161`, `BL-152`, `BL-002`, `BL-069` and `BL-135` returns **0** in the exported half and
> finds each in the unexported one, with an open row as the positive control. Same
> dangling-pointer shape, larger population, and it grows with every close.
>
> **Why this does NOT overturn the `ds-milestone.md` refusal**, stated because the two would
> otherwise read as in tension. That document was refused on the `cloudcost/m3-milestone.md`
> reasoning — it holds derived reasoning *about* rules whose normative text lives elsewhere, and
> its conclusions did land elsewhere. A closed row holds derived reasoning too, but it also holds
> **the disposition itself**, which lands nowhere else. That is the distinguishing feature, and
> it is why both rulings stand.
>
> **The adjudication test, applied to this ruling.** The occasion is BL-047's close, which put
> the last UNRULED row into the invisible half. The reason is the precedent above and the
> inclusion test — both of which predate the occasion by four days, and either of which would
> have produced this ruling on 2026-08-21 had anyone asked the question then. *The hit is the
> occasion, never the reason.*
>
> **BORN GREEN, and the green says less than it looks.** The row is pinned by hand at the commit
> that last touched the file, so check 8 compares pinned against current, finds them equal, and
> the row emits no WARN — on its first boundary as on every one after. A currency check cannot
> distinguish *exported at this commit* from *never exported, pinned at this commit*. **The
> document is NOT in the store and will not be until the next export runs**; this paragraph is
> the only thing in either repo recording that. Same trap as `use-cases.md` at the 2026-08-21
> close, stated again because it applies again.
>
> **One thing the arbiter could not weigh, recorded rather than omitted.** The closed half's size
> against the store's capacity. The two figures available disagree about what they measure — the
> 2026-08-25 bundle lists `backlog-2026-06.md` at 504,295 bytes while the store reports its whole
> knowledge size as 402,078 — so no capacity conclusion is derivable from here. If the closed
> half proves large enough to matter against the store's cap, that is a fact that reopens this
> ruling, and it belongs in the next boundary's record.


> **THE SURFACE COLUMN — the design note's D-B applied, 2026-09-08. Every row assigned, four
> rows added.** The hybrid-context design (`aetheris/docs/aetheris/research/hybrid-context-design-2026-08.md`,
> r2; D-B ratified in r1) makes project knowledge the KERNEL and everything else an on-demand
> corpus reached at HEAD; the `surface` column is how this table says which is which. The
> header's **Surfaces** paragraph defines the three values; this block records the assignment
> and why, in the family of the inclusion-rule blocks above — it does not amend any of them.
>
> **Assignment.** `export`: the members of the D-B kernel table that carry rows — this
> manifest (the map of maps), `rig--current-state-2026-06.md` (the current-state doc),
> `backlog-2026-06.md` (the queue, pre-split), `capability-matrix.md`, the two methodology
> rows, and the two `ROADMAP.md` rows added here. `both`: `aetheris--research-index.md` — the
> retrieval map itself, which a store-side reader needs before knowing what to fetch and which
> must also be readable at HEAD, where it is truth — and `aetheris--bl-008-synthesis.md`, the
> design note's one named `both` candidate, *while under ratification; demote after*.
> `on-demand`: every other row. The six research briefs and the research README keep their
> rows and lose nothing: the manifest is the top-level map and they are reached through the
> index at HEAD, which is the direction the D-B table sends the whole research tree first.
>
> **Four rows added, pinned by hand at each file's last-touching commit in its own repo.**
> `aetheris-agents--ROADMAP.md` and `aetheris--ROADMAP.md` (the D-B table: *orientation before
> any fetch*, both repos), `aetheris--research-index.md` (generated at harness `a950ca9` by
> `scripts/gen_index.py`; 23 entries), `aetheris--bl-008-synthesis.md`. All four are **BORN
> GREEN** in exactly the sense the block above states: pinned current, in no store until the
> next export runs. The fourteen briefs filed at harness `2c1a6b6` get no rows of their own —
> they are `on-demand` by construction, reached through the index, and a row per on-demand
> document would re-create the enumeration the index exists to replace.
>
> **What this block does NOT decide, said so the after-run can decide it.** The three
> `CLAUDE.md` rows, `use-cases.md` and `backlog-scale-2026-09.md` are `on-demand` because the
> D-B table does not name them, not because a reader was found who does not need them. If the
> probe after-run (design §3, against `hybrid-probe-baseline-2026-09-08.md`) regresses on a
> question those documents answer, the surface to reassign is named here.
>
> **Two consequences elsewhere.** The post-upload completeness check (BL-002, check 1) now
> compares the store against the KERNEL rows only — an `on-demand` row has no store copy by
> design, and the design note retires the store-set≡manifest check for that surface (§1.1).
> And this table's row count is no longer the bundle's file count: the assembler prints how
> many rows it left out and why, so a bundle smaller than the table reads as the rule working.
>
> **What this does not do.** It uploads nothing. The kernel budget line in the header is
> recorded and measured, and it is over; the arm that would warn on it is **BL-201**, filed
> beside this edit rather than landed with it, because a warning that fires on every run from
> the day it lands is BL-009's alarm-fatigue class and the figure is dominated by one row the
> backlog split removes.

> **THE TRIAGE RECORD — one row added, 2026-09-14.** `backlog-triage-2026-09.md` is the record
> the next planning conversation reads, and until this row it was covered by no check and
> reachable from no index. `on-demand`, so nothing is uploaded and the kernel budget is
> unchanged; check 8 does not compare it (`check_project_knowledge` skips `on-demand` before any
> git read). Pinned by hand at the file's last-touching commit, `29ed2a2`, and that commit's date.
> `docs/` has no `index.md`, so like `backlog-scale-2026-09.md` this row is the document's only
> map entry.

> **THE EVIDENCE TREE — on-demand by construction, 2026-09-14 (BL-252).** `docs/evidence/<ID>.md`
> holds each open backlog row's body, moved verbatim when `backlog-2026-06.md` became an index of
> field lists. The path is derived from the row id, so the tree gets no row per file and no
> generated `index.md`: a reader holding an id holds the path. Nothing is uploaded or re-pinned by
> this block; the backlog row's staleness WARN is expected until the next export, a separate
> BL-002 round.

> **THE STREAMING CONTRACT AND ITS BRIEF — two rows added, 2026-09-20.**
> `aetheris/docs/aetheris/playground-api.md` is the normative wire contract for
> every `/api/playground/*` route, including the two run-event stream endpoints
> (§3.5, §3.6) by which a non-Rig client connects. It carried no row, so the
> kernel pointed a store-side session at no copy of it and a session needing the
> contract had to already know the path. Added `on-demand`.
> `aetheris-agents/docs/aetheris/backlog/bl-266-run-event-streaming.md` is the
> ratified design contract the streaming implementation is cited against by item
> number; it meets the DESIGN BRIEFS rule of 2026-08-24 — a store-side actor
> reasoning about stream behaviour must read it. Added `on-demand`.
> Both are `on-demand` deliberately: neither enters the kernel, so the ceiling is
> untouched and no row is displaced. `on-demand` buys addressability, not drift
> detection — `drift_check.py:681` exempts the surface from staleness by
> construction, and contract-vs-code drift for the stream envelope is the
> `stream_envelope` arm's job, not this manifest's.

> **THE SYNTHESIS DEMOTION — `aetheris--bl-008-synthesis.md` goes from `both` to `on-demand`,
> 2026-09-21 (R2).** Demoting `aetheris--bl-008-synthesis.md` from `both` to `on-demand` executes
> the deferred transition already specified and justified by ratified D-B; it does not make a new
> surface-assignment decision. Therefore BL-202 does not require a new probe. BL-203 continues to
> gate surface assignments not already determined by a ratified ruling. D-B was ratified in the
> design note's r1 (`aetheris/docs/aetheris/research/hybrid-context-design-2026-08.md` §2). It
> assigned the synthesis
> `both` *"while under ratification; demote after"*, so the demotion and its condition were decided
> together. The condition was met on 2026-09-11, when the arbiter ratified the synthesis: see its
> frontmatter `status: ratified` and the dated block at line 43. Reachability is unchanged. The
> synthesis lives under `docs/aetheris/research/`, and
> `aetheris--research-index.md` indexes that tree and is itself a kernel row. The index carries the
> synthesis's entry, so a session working from the store reaches the synthesis at HEAD through it.
> The row keeps its pin. The kernel goes from ten rows to nine, and the research index is now the
> only `both` row.

> **THE CEILING RATCHET MOVES TO THE BOUNDARY, 2026-09-21 (R3).** At each export boundary, with
> the measured sum taken after all of that boundary's manifest edits:
>
> ```
> candidate   = ceil_1000(measured_kernel_bytes + 10,000)
> new_ceiling = min(current_ceiling, candidate)
> ```
>
> An increase requires a separate recorded inclusion ruling in this file. A new kernel row still
> names what it displaces, or it triggers a probe re-run (design §3). The 10,000 is the margin at
> the boundary that sets the ceiling, not a standing guarantee: a boundary that leaves the ceiling
> unchanged can leave less. Why: the margin stops ordinary filings between boundaries from failing
> `--strict` on the ratchet alone (**BL-255**). The ratchet moves to the boundary step because the
> previous trigger, *"a round that shrinks the kernel"*, went unapplied at the second 2026-09-15
> boundary and at 2026-09-17.

> **THE BACKLOG ROW IS D-B'S QUEUE, 2026-09-21 (R5).** Today's `docs/backlog-2026-06.md` is D-B's
> *"backlog queue (`queue.md` post-split)"*, and its row stays `export`. Why: the index split of
> **BL-252**, which reduced open rows to field lists, is the split D-B anticipated, and `queue.md`
> was a name, not a requirement.

---

