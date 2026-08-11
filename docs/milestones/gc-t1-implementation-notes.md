# gc t1 — the gate-claim census (implementation notes)

`Record of gc t1, run 2026-08-11, reviewed 2026-08-11. Written at Phase D, after the round's records
were found absent. Round document: docs/milestones/gc-stale-claims.md. The derivation is in the
commit and in the re-run below; this file carries the findings, what is owed, what is uncertain, and
the anchors.`

**Structure is machine-readable by intent** — per §Carried in item 2 and the record-shape consequence
m5 draws from it, *a census earns machine-readable structure, and prose around it earns nothing*.
Countable headings: `^#### [A-Z]` for sections, `^R\|` for census rows, `^G\d+\t` for the class list,
`^T\d+\t` for description tokens.

---

#### A — WHAT THE CENSUS FOUND

```
rows_total            143
rows_closed            48
rows_open              95
status_surfaces         2      row bodies (33) + `## Suggested order` ✔ table (28); union 48
idform_hits           640
descform_hits         162
retrospective_dropped  94
live_read_idform      199
archival_idform       441
stale_live_idform       5
stale_live_descform     1
method_defects_found    3      all by this ticket's own controls
```

#### B — THE ADJUDICATED STALE GATE CLAIMS

Six sentences, three destinations. These are t3's arm-1 scope.

```
R| cloudcost/runbook.md:619-620              | G1+G2      | BL-074(2026-08-07)            | operational guidance | LIVE
R| ../aetheris/ROADMAP.md:52                 | G2         | BL-007(2026-07-20)            | operational guidance | LIVE
R| ../aetheris/ROADMAP.md:109-112            | G10+G3     | BL-003(2026-07-15)            | operational guidance | LIVE
R| cloudcost/m5-n1-compose.md:30             | G8         | BL-132(2026-08-11)            | round document       | LIVE
R| cloudcost/m5-n1-compose.md:1226           | G11+G3+G8  | BL-132(2026-08-11)            | round document       | LIVE
R| cloudcost/m5-n1-compose.md:852-856        | descform   | BL-074(08-07);BL-105+106(08-09)| round document      | LIVE
```

`../aetheris/ROADMAP.md:109` additionally carries a stale parenthetical — `(already Active)` — about
the gating row's own state. Both halves are in t3's scope.

#### C — THE CLASS LIST, VERBATIM AND RE-RUNNABLE

`B = (?:\*\*)?(BL-\d+)(?:\*\*)?` · `W = [^\n]` · window = the id's line ±1 · hit anchored to the
line carrying the id.

```
G1	read-imperative	\bread\s+(?:the\s+)?B
G2	before	\bbefore\bW{0,120}?B  |  BW{0,120}?\bbefore\b
G3	gate	\bgate[sd]?\bW{0,90}?B  |  BW{0,90}?\bgate[sd]?\b
G4	blocks	\bblock(?:s|ed|ing)\bW{0,60}?B  |  BW{0,60}?\bblock(?:s|ed|ing)\b
G5	depends/prereq	\b(?:depends?\s+on|dependent\s+on|prerequisite|precondition)\bW{0,80}?B
G6	after/once	\b(?:after|once)\s+B
G7	first	BW{0,70}?\b(?:runs|lands|goes|comes|closes|ships|done)\s+first\b | \bfirst\bW{0,60}?B
G8	sequence-arrow	(?:→|->)\s*(?:\*\*)?BL-\d+  |  (?:\*\*)?BL-\d+(?:\*\*)?\s*(?:→|->)
G9	pending/await	\b(?:pending|awaits?|awaiting|waits?\s+(?:for|on)|blocked\s+until)\bW{0,70}?B
G10	until	\b(?:until|not\s+startable)\bW{0,70}?B
G11	sequenced	\bsequenc(?:e|ed|ing|es)\bW{0,80}?B
```

Corpus: both repos; extensions `.md .sh .py .exs .ex .rs .ts .tsx .json`; excluded directories
`.git node_modules _build deps target __pycache__ .pytest_cache priv`.

Retrospective discriminator (94 dropped): `\b(?:before|until|after|since|pre-)\s+(?:\*\*)?BL-\d+`
with no prospective marker — the id follows the preposition, so the sentence describes the world
before that row landed.

#### D — DESCRIPTION TOKENS, DERIVED FROM CLOSED ROWS' OWN HEADINGS

```
T1	BL-074	\bseam sweep\b
T2	BL-074	\bthe sweep'?s? (?:result|method)\b|\bBL-074'?s? sweep\b
T3	BL-105+BL-106	\bharness (?:consolidation )?round\b
T4	BL-131	\bN>1 compose (?:path|surface)\b
T5	BL-132	\breachability census\b
T6	BL-070	\bcross-provider (?:merge|deletions)\b
T7	BL-003	\bstartup sweep\b
T8	BL-002	\brefresh (?:the )?(?:claude )?project knowledge\b|\bexport boundary\b
T9	BL-069	\b(?:≥1-orphan|>=1-orphan) assertion\b
T10	BL-073	"View report"|\bView report\b
T11	BL-009	\bdrift_check --strict\b|\bpromote sprint drift_check\b
T12	BL-042	\bcapability-shaped containment\b
T13	BL-048	\brequires_worker test set\b
T14	BL-104	\bhermetic prefix\b
```

#### E — PER-CLASS AND PER-TOKEN COUNTS

```
class   count   t1   delta
G1          8     8      0
G2        251   251      0
G3        161   161      0
G4         65    65      0
G5          5     5      0
G6         48    48      0
G7         92    92      0
G8         47    47      0
G9         17    17      0
G10        56    56      0
G11        59    59      0
TOTAL     640   640      0

token   count   t1   delta
T1         26    26      0
T2          4     4      0
T3         33    33      0
T4         10    10      0
T5          0     0      0
T6         10    10      0
T7          1     1      0
T8         33    33      0
T9          0     0      0
T10         9     9      0
T11        23    23      0
T12         5     5      0
T13         0     0      0
T14         8     8      0
TOTAL     162   162      0
```

#### F — LIVE-READ CENSUS ROWS

Archival rows are given as per-file counts under §G; they are reproducible from the class list above
and none is live-read.

```
R| path:line | classes | closed-rows(date) | kind | retrospective?
R| aetheris-agents/agents/fixture_unlabelled_fork.exs:4 | G3 | BL-029(2026-07-20) | code | prospective
R| aetheris-agents/agents/fixture_unlabelled_fork.exs:18 | G7+G10 | BL-039(2026-07-26) | code | prospective
R| aetheris-agents/rig/src-tauri/src/commands/harness.rs:733 | G3 | BL-073(2026-08-04) | code | prospective
R| aetheris-agents/rig/src/components/modules/harness/RunList.tsx:492 | G2 | BL-029(2026-07-20) | code | retro
R| aetheris-agents/rig/src/components/modules/harness/RunList.tsx:590 | G10 | BL-005(2026-07-15) | code | prospective
R| aetheris-agents/rig/src/components/modules/harness/TrajectoryView.tsx:141 | G2 | BL-073(2026-08-04) | code | prospective
R| aetheris-agents/rig/src/components/modules/harness/TrajectoryView.tsx:333 | G2 | BL-003(2026-07-15) | code | prospective
R| aetheris-agents/rig/src/components/modules/harness/TrajectoryView.tsx:335 | G2 | BL-005(2026-07-15) | code | prospective
R| aetheris-agents/scripts/drift_check.py:690 | G3 | BL-041(2026-07-25) | code | prospective
R| aetheris-agents/scripts/drift_check.py:691 | G3 | BL-041(2026-07-25) | code | prospective
R| aetheris-agents/tests/test_drift_check.py:475 | G5 | BL-041(2026-07-25) | code | prospective
R| aetheris/lib/aetheris/cli/commands/fork.ex:53 | G2 | BL-030(2026-07-26) | code | prospective
R| aetheris/lib/aetheris/execution/verifier.ex:306 | G2 | BL-042(2026-07-23) | code | prospective
R| aetheris/lib/aetheris/execution/verifier.ex:341 | G2 | BL-049(2026-07-24) | code | retro
R| aetheris/lib/aetheris/execution/volatile_metadata.ex:25 | G2 | BL-049(2026-07-24) | code | retro
R| aetheris/lib/aetheris/run_pause.ex:12 | G2 | BL-031(2026-07-21) | code | retro
R| aetheris/lib/aetheris/store.ex:1067 | G2 | BL-031(2026-07-21) | code | retro
R| aetheris/lib/aetheris/worker/client.ex:165 | G2 | BL-055(2026-07-25) | code | prospective
R| aetheris/native/aetheris_worker/src/main.rs:73 | G2 | BL-050(2026-07-25) | code | retro
R| aetheris/native/aetheris_worker/src/main.rs:97 | G2 | BL-050(2026-07-25) | code | prospective
R| aetheris/native/aetheris_worker/src/sandbox.rs:331 | G10 | BL-043(2026-07-25) | code | retro
R| aetheris/scripts/containment_probe.exs:3 | G3 | BL-048(2026-07-25) | code | prospective
R| aetheris/scripts/containment_probe.exs:5 | G3 | BL-050(2026-07-25) | code | prospective
R| aetheris/scripts/sprint.sh:1602 | G4 | BL-009(2026-07-15) | code | prospective
R| aetheris/scripts/sprint.sh:3001 | G4 | BL-104(2026-08-06) | code | prospective
R| aetheris/test/aetheris/cli/commands/fork_test.exs:48 | G2 | BL-039(2026-07-26) | code | prospective
R| aetheris/test/aetheris/cli/commands/fork_test.exs:125 | G2 | BL-030(2026-07-26) | code | prospective
R| aetheris/test/aetheris/cli/commands/fork_test.exs:184 | G9 | BL-106(2026-08-09) | code | retro
R| aetheris/test/aetheris/cli/commands/run_helpers_timeout_test.exs:131 | G2 | BL-031(2026-07-21) | code | retro
R| aetheris/test/aetheris/execution/effect_class_test.exs:7 | G2 | BL-025(2026-07-23) | code | retro
R| aetheris/test/aetheris/execution/fork_test.exs:57 | G2 | BL-039(2026-07-26) | code | retro
R| aetheris/test/aetheris/execution/verify_effects_test.exs:194 | G10 | BL-049(2026-07-24) | code | retro
R| aetheris/test/aetheris/execution/verify_effects_test.exs:285 | G10 | BL-043(2026-07-25) | code | retro
R| aetheris/test/aetheris/execution/verify_verdict_test.exs:6 | G2 | BL-049(2026-07-24) | code | retro
R| aetheris/test/aetheris/execution/volatile_metadata_test.exs:54 | G2 | BL-049(2026-07-24) | code | retro
R| aetheris/test/aetheris/worker/containment_gate_test.exs:3 | G3 | BL-056(2026-07-25) | code | prospective
R| aetheris/test/aetheris/worker/containment_gate_test.exs:101 | G3 | BL-042(2026-07-23) | code | prospective
R| aetheris-agents/docs/project-knowledge-manifest.md:76 | G2 | BL-002(2026-07-15) | manifest | prospective
R| aetheris-agents/docs/project-knowledge-manifest.md:226 | G2 | BL-073(2026-08-04) | manifest | prospective
R| aetheris-agents/docs/project-knowledge-manifest.md:232 | G2 | BL-002(2026-07-15) | manifest | prospective
R| aetheris-agents/docs/project-knowledge-manifest.md:279 | G7 | BL-002(2026-07-15) | manifest | prospective
R| aetheris-agents/CLAUDE.md:24 | G7 | BL-031(2026-07-21) | opguide | prospective
R| aetheris-agents/CLAUDE.md:292 | G2 | BL-003(2026-07-15) | opguide | retro
R| aetheris-agents/CLAUDE.md:294 | G3 | BL-029(2026-07-20) | opguide | prospective
R| aetheris-agents/CLAUDE.md:304 | G3 | BL-069(2026-08-06) | opguide | prospective
R| aetheris-agents/CLAUDE.md:473 | G2 | BL-007(2026-07-20) | opguide | prospective
R| aetheris-agents/CLAUDE.md:511 | G10 | BL-007(2026-07-20) | opguide | prospective
R| aetheris-agents/CLAUDE.md:512 | G10 | BL-007(2026-07-20) | opguide | prospective
R| aetheris-agents/cloudcost/runbook.md:620 | G1+G2 | BL-074(2026-08-07) | opguide | prospective
R| aetheris-agents/docs/rig/runbook.md:85 | G2 | BL-029(2026-07-20) | opguide | retro
R| aetheris-agents/docs/rig/runbook.md:123 | G2+G4 | BL-039(2026-07-26) | opguide | prospective
R| aetheris/CLAUDE.md:13 | G7 | BL-031(2026-07-21) | opguide | prospective
R| aetheris/CLAUDE.md:745 | G2+G3 | BL-029(2026-07-20),BL-039(2026-07-26) | opguide | prospective
R| aetheris/ROADMAP.md:52 | G2 | BL-007(2026-07-20) | opguide | prospective
R| aetheris/ROADMAP.md:76 | G3 | BL-007(2026-07-20) | opguide | prospective
R| aetheris/ROADMAP.md:112 | G3+G10 | BL-003(2026-07-15) | opguide | prospective
R| aetheris/docs/aetheris/determinism-contract.md:19 | G2 | BL-043(2026-07-25) | opguide | prospective
R| aetheris/docs/aetheris/determinism-contract.md:370 | G10 | BL-043(2026-07-25) | opguide | retro
R| aetheris/docs/aetheris/runbook.md:218 | G2 | BL-031(2026-07-21) | opguide | retro
R| aetheris/docs/aetheris/runbook.md:612 | G2 | BL-039(2026-07-26) | opguide | retro
R| aetheris/docs/methodology/milestone-methodology.md:188 | G6 | BL-007(2026-07-20) | opguide | retro
R| aetheris-agents/cloudcost/m5-n1-compose.md:3 | G2 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:10 | G8 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:30 | G8 | BL-132(2026-08-11) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:45 | G3+G7+G9 | BL-070(2026-08-10),BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:46 | G2+G3+G7+G9 | BL-070(2026-08-10),BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:47 | G2+G3+G7 | BL-070(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:92 | G2 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:105 | G4 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:266 | G9 | BL-070(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:267 | G9 | BL-070(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:327 | G4+G9 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:337 | G9 | BL-070(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:498 | G3 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:502 | G3 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:556 | G3 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:576 | G2 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:591 | G2 | BL-070(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:605 | G9 | BL-070(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:635 | G3 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:855 | G11 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:861 | G3 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:970 | G3 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:996 | G9 | BL-131(2026-08-10) | round | prospective
R| aetheris-agents/cloudcost/m5-n1-compose.md:1226 | G3+G8+G11 | BL-132(2026-08-11) | round | prospective
# backlog-file live rows withheld from this listing: 114 (same file, same shape; grep the registry)
# live-read total 199  archival total 441
```

#### G — ARCHIVAL HITS BY FILE

```
count  file
   47  aetheris-agents/docs/reviews/bl-025-review.md
   35  aetheris-agents/docs/reviews/bl-042-review.md
   31  aetheris-agents/cloudcost/m4-consolidation.md
   19  aetheris-agents/cloudcost/docs/m5-scoping-landing-notes.md
   17  aetheris-agents/cloudcost/docs/m5-ruling-edit-implementation-notes.md
   13  aetheris-agents/docs/handoffs/handoff-bl025-bl042-close-2026-07-23.md
   12  aetheris-agents/docs/milestones/hc-consolidation.md
   11  aetheris-agents/cloudcost/m3-milestone.md
    9  aetheris-agents/docs/handoffs/handoff-b1b3-close-2026-07-22.md
    9  aetheris-agents/cloudcost/m2-milestone.md
    8  aetheris-agents/docs/reviews/bl-049-review-r1.md
    8  aetheris-agents/docs/reviews/bl-039-review-packet.md
    6  aetheris-agents/docs/handoffs/handoff-containment-cluster-close-2026-07-25.md
    6  aetheris-agents/docs/handoffs/handoff-bl007-close-2026-07-20.md
    6  aetheris-agents/docs/handoffs/handoff-cloudcost-rig-batch-close-2026-08-04.md
    6  aetheris-agents/docs/reviews/m2-cloudcost-closeout.md
    6  aetheris-agents/docs/reviews/bl-029-review.md
    6  aetheris-agents/docs/reviews/bl-049-review.md
    6  aetheris-agents/cloudcost/docs/m5-t1-implementation-notes.md
    5  aetheris-agents/docs/handoffs/handoff-fork-arc-close-2026-07-26.md
    5  aetheris-agents/docs/rig/milestones/bl-007/bl-007-t5-implementation-notes.md
    5  aetheris-agents/docs/reviews/bl-015-review.md
    5  aetheris-agents/cloudcost/docs/m4-t4b-implementation-notes.md
    4  aetheris-agents/docs/milestones/hc-d-implementation-notes.md
    4  aetheris-agents/docs/handoffs/handoff-m3-close-2026-08-05.md
    4  aetheris-agents/docs/reviews/t1a-review.md
    4  aetheris-agents/cloudcost/docs/t1a-implementation-notes.md
    4  aetheris-agents/cloudcost/docs/m5-t3-implementation-notes.md
    4  aetheris-agents/cloudcost/docs/m4-t2-implementation-notes.md
    4  aetheris/docs/reviews/bl-043-contract-draft.md
    4  aetheris/docs/reviews/bl-050-055-056-review.md
    3  aetheris-agents/docs/milestones/hc-c-implementation-notes.md
    3  aetheris-agents/docs/handoffs/handoff-cloudcost-rig-batch-2026-08-03.md
    3  aetheris-agents/docs/handoffs/handoff-linode-provider-three-kickoff-2026-08-04.md
    3  aetheris-agents/docs/reviews/bl-042-contract-draft.md
    3  aetheris-agents/docs/reviews/bl-047-review-r1.md
    3  aetheris-agents/docs/reviews/hc-c-review.md
    3  aetheris-agents/docs/reviews/bl-030-r2-review-packet.md
    3  aetheris-agents/docs/reviews/bl-030-review-packet.md
    3  aetheris-agents/docs/reviews/bl-005-review.md
    3  aetheris-agents/docs/reviews/bl-batch-2026-07-section7-draft.md
    3  aetheris-agents/docs/reviews/bl-025-contract-draft.md
    3  aetheris-agents/cloudcost/docs/m4-t4c-implementation-notes.md
    3  aetheris-agents/cloudcost/docs/bl-132-anatomy-implementation-notes.md
    3  aetheris/docs/aetheris/milestones/bl-025-implementation-notes.md
    3  aetheris/docs/aetheris/milestones/bl-042-implementation-notes.md
    3  aetheris/docs/reviews/bl-055-bl-056-containment-decisions.md
    3  aetheris/docs/reviews/bl-048-closeout-review.md
    2  aetheris-agents/docs/rig/milestones/bl-038-run-list-search-implementation-notes.md
    2  aetheris-agents/docs/rig/milestones/bl-batch-2026-07-promotion-implementation-notes.md
    2  aetheris-agents/docs/reviews/bl-030-fork-early-return-scout.md
    2  aetheris-agents/docs/reviews/bl-039-fork-continuation-scout.md
    2  aetheris-agents/docs/reviews/bl-030-r1-review-packet.md
    2  aetheris-agents/docs/reviews/bl-007-t5-review.md
    2  aetheris-agents/docs/reviews/bl-047-review.md
    2  aetheris-agents/docs/reviews/m3-cloudcost-export-boundary-review-packet.md
    2  aetheris-agents/docs/reviews/bl-041a-promotion-draft.md
    2  aetheris-agents/docs/reviews/bl-028-review.md
    2  aetheris-agents/docs/reviews/bl-batch-2026-07-section7-adjudication.md
    2  aetheris-agents/docs/reviews/m5-cloudcost-t3-review.md
    2  aetheris-agents/cloudcost/milestone.md
    2  aetheris-agents/cloudcost/docs/m3-t3-implementation-notes.md
    2  aetheris-agents/cloudcost/docs/m3-linode-scout.md
    2  aetheris/docs/reviews/bl-050-055-056-contract-draft.md
    1  aetheris-agents/docbuilder/milestone.md
    1  aetheris-agents/docbuilder/docs/m1-milestone.md
    1  aetheris-agents/docbuilder/docs/milestones/m-docbuilder-m6-t6-implementation-notes.md
    1  aetheris-agents/docbuilder/docs/milestones/m-tenant-data-layer.md
    1  aetheris-agents/docbuilder/docs/reviews/m-docbuilder-m3-t5-review.md
    1  aetheris-agents/docbuilder/docs/reviews/m-docbuilder-m6-t6-review.md
    1  aetheris-agents/docs/milestones/hc-b-implementation-notes.md
    1  aetheris-agents/docs/milestones/hc-e-implementation-notes.md
    1  aetheris-agents/docs/handoffs/handoff-bl007-t2-design-2026-07-18.md
    1  aetheris-agents/docs/rig/milestones/bl-031-await-inactivity-bound-implementation-notes.md
    1  aetheris-agents/docs/rig/milestones/bl-086-trajectory-stage-labels-implementation-notes.md
    1  aetheris-agents/docs/rig/milestones/bl-095-plan-card-secret-values-implementation-notes.md
    1  aetheris-agents/docs/rig/milestones/bl-007/bl-007-t4-implementation-notes.md
    1  aetheris-agents/docs/reviews/bl-001-review.md
    1  aetheris-agents/docs/reviews/m2-cloudcost-section7-promotion.md
    1  aetheris-agents/docs/reviews/bl-022-review.md
    1  aetheris-agents/docs/reviews/bl-038-review.md
    1  aetheris-agents/docs/reviews/bl-003-review.md
    1  aetheris-agents/docs/reviews/m1-cloudcost-t3-review.md
    1  aetheris-agents/docs/reviews/m1-cloudcost-t2-review.md
    1  aetheris-agents/docs/reviews/bl-002-review.md
    1  aetheris-agents/docs/reviews/bl-031-review.md
    1  aetheris-agents/docs/reviews/bl-047-contract-draft.md
    1  aetheris-agents/docs/reviews/bl-049-contract-draft.md
    1  aetheris-agents/docs/reviews/m3-cloudcost-t1-review.md
    1  aetheris-agents/docs/reviews/bl-016-review.md
    1  aetheris-agents/docs/reviews/bl-041b-bl-036-review.md
    1  aetheris-agents/cloudcost/docs/m5-body-addition-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/m5-record-correction-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/m5-t2-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/t1b-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/m4-t3-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/bl-132-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/t1a-p-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/m3-t2-implementation-notes.md
    1  aetheris-agents/cloudcost/docs/m5-pin-edit-implementation-notes.md
    1  aetheris/docs/aetheris/claude-notes.md
    1  aetheris/docs/aetheris/milestones/bl-016-payslip-orchestrator-test-implementation-notes.md
    1  aetheris/docs/aetheris/milestones/bl-047-implementation-notes.md
    1  aetheris/docs/aetheris/milestones/bl-028-implementation-notes.md
    1  aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md
    1  aetheris/docs/aetheris/milestones/bl-003-startup-sweep-implementation-notes.md
    1  aetheris/docs/aetheris/milestones/bl-049-implementation-notes.md
    1  aetheris/docs/reviews/bl-043-review.md
    1  aetheris/docs/reviews/bl-053-contract-draft.md
# files: 109   hits: 441
```

#### H — CONTROLS

t1's own, minted fresh at t1, published, each verified 0 **before** reliance. None discarded.

```
qqzx-gate-control-alpha      0
wibblefrotz-precondition     0
zarquon-before-provider      0
positive: read \*\*BL-074\*\*      1  (cloudcost/runbook.md:620)
positive: Before provider four     2
```

**They are spent.** Re-run at Phase D over the same corpus they now return **1 each**, the single hit
being `docs/milestones/gc-stale-claims.md` §Carried in, which publishes them. That is §Carried in
item 3 demonstrated on its own instruments; any later sweep mints its own.

#### I — THE THREE METHOD DEFECTS

Each found by this ticket's own controls, corrected in the open, none patched over.

```
D1  `^` without re.MULTILINE over a joined body string.
    Symptom: 22 closed / 121 open; BL-131 and BL-132 classified OPEN despite carrying
    `### BL-1xx — DONE` headings. Caught by: positive control.
D2  Row span bounded by the next `### BL-` heading only, so `## Suggested order` (:5662)
    fell inside BL-014's span and a table about other rows supplied it a closure marker.
    Caught by: negative control, after adding BL-014 to it. Fixed by bounding on `^#{1,2} `,
    fence-aware.
D3  Proximity classes used `[^.\n]{0,N}`, forbidding the gate relation from crossing a
    sentence boundary. Suppressed 136 hits — 504 -> 640, 21.25% of the class.
    Caught by: the five-member subset check, on its fifth member only
    (cloudcost/m4-consolidation.md:362). The other four passed under the defective pattern.
```

#### J — WHAT THE METHOD CANNOT ANSWER FROM INSIDE ITSELF

```
1  Complete relative to its class list, not to the class. Gate voice using none of the
   25 patterns is invisible; no AST analogue exists for prose.
2  Cannot see a gate on work that is not a backlog row — which is how
   cloudcost/m5-n1-compose.md:854 names its two components.
3  Window is ±1 line. A relation spanning 3+ lines is missed.
   cloudcost/runbook.md:619->620 spans two and is anchored at :620.
4  The live/archival call is a judgement per document against hc decision 10, not a measurement.
5  The prospective/retrospective discriminator is syntactic. No counter-instance found;
   cannot be bounded from inside the method.
```

#### K — RE-RUN AT PHASE D, AND WHAT IT ESTABLISHES

The census was **re-run from the class list and tokens exactly as printed above**, not transcribed.

```
idform  gc artifacts EXCLUDED   640   == t1's 640
idform  gc artifacts INCLUDED   648   (+8, all in docs/milestones/gc-stale-claims.md)
descform gc artifacts EXCLUDED  162   == t1's 162
descform gc artifacts INCLUDED  165   (+3, same file)
per-class deltas                  0   all 11 classes identical
per-token deltas                  0   all 14 tokens identical
```

**Corpus boundary, decided explicitly.** The round's own artifacts are **out of corpus** for the
comparable figure. Reason: t1's corpus did not contain them — they did not exist — and this round's
record now quotes the stale sentences verbatim and cites closed rows in gate voice, so including them
counts the round's own record as content. Both counts are reported so the choice is visible and
reversible; it moves the number by 8 and 3.

**This establishes §Close criteria clause 1's "re-runnable as printed".** Every pattern and every
token ran as printed, with no repair, and every count reproduced. Recorded as a result, not a
silence: the clause is satisfiable and satisfied.

#### L — WHAT IS OWED, AND WHAT IS UNCERTAIN

```
OWED  t3 arm 1: the six sentences at §B, per-destination correction shape.
OWED  t3 arm 2: five backlog rows — status surfaces; the quoted-marker row; the
      unstamped-contract dispositions (D5); the adapter obligations with no exemplar;
      the two senses of `live` (D2).
OWED  Review files for t1 and t2. NOT claude-code's to author — methodology §10 assigns
      them to claude-ui, saved verbatim by the human.
UNCERTAIN  Whether hc's decisions bind harness-side files (t3 must establish; the hc round's
      own tickets edited harness files, which bears on it without settling it).
UNCERTAIN  Whether `operational content` is the right general name for decision 10's test,
      or merely its usual carrier — D6 reserves it for the close.
```

#### M — ANCHORS

```
round document        docs/milestones/gc-stale-claims.md
row registry          docs/backlog-2026-06.md  (sole registry; 7 other files carry `### BL-` headings, none a registry)
second status surface docs/backlog-2026-06.md  `## Suggested order`  :5662
the class rule        aetheris/CLAUDE.md:760-777  Adjacent-case, and the "the one X" tell
control rule          aetheris/CLAUDE.md:599-607  a negative needs a positive control
carried-in source     cloudcost/m5-n1-compose.md:1035-1227  §Open for the next cycle
```
