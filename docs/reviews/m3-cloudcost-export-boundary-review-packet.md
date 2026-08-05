# Review packet — m3-cloudcost project-knowledge export boundary (BL-002)

**Deliverable:** the export half of the m3-cloudcost boundary — mirror-pair check,
full row verification, manifest regen, export note. The upload half was the human's
and is **done** (25/25 verified in-store, one-second upload window).

**Filed at close.** §§1–4 are the packet as reviewed, when the two boundary commits were
held and unpushed; §5 is the post-boundary addenda. Read §§1–4 in that tense. Final ledger,
all pushed:

| commit | repo | what |
|---|---|---|
| `de71e2b` | agents | backlog DONE sections (BL-090, BL-092) — the boundary's first tracked write |
| `29a51fa` | agents | the manifest, alone and last — 4 rows re-pinned, 0 WARN |
| `c41199b` | agents | BL-102 — sweep at batch closes too (deferred past the boundary by design) |
| `1db6797` | agents | BL-002 prompt §Post-upload verification |
| `455b45a` | agents | BL-103 — non-manifest documents in the store |
| `082b37c` | **harness** | `CLAUDE.md` — never authenticate a credential of unknown provenance |
| `59bec3f` | agents | BL-104 — invert the hermetic prefix to an allowlist |
| `80c801c` | agents | BL-104 — citations anchored, verified at `aetheris@082b37c` |

**Contract sections referenced:**
`docs/project-knowledge-manifest.md` (header + inclusion-rule notes) ·
`prompts/bl-002-refresh-project-knowledge.md` (row format, ordering invariant) ·
`aetheris-agents/CLAUDE.md` §Definition of done — doc sync (strict-mode exemption;
post-commit ordering; *pin-is-current-never-complete*; *export is remove-all-upload-all*) ·
`aetheris/docs/methodology/milestone-methodology.md` §5 (this packet's shape) ·
BL-034 (the self-staling ordering hazard) · BL-002 (the refresh convention).

---

## 1. Done-check output

### 1a. Pre-commit baseline — `python3 scripts/drift_check.py --strict`

```
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 50 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[WARN] project_knowledge: CLAUDE.md stale — manifest=0fc9396 current=13fc8c4
[WARN] project_knowledge: docs/capability-matrix.md stale — manifest=b7cb6ca current=4d98ec2
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=9b5da48 current=b0030e7
[WARN] project_knowledge: CLAUDE.md stale — manifest=710ecd2 current=1743e75
[PASS] command_fields: 11 documented §4 structs (56 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  4 WARN  7 INFO
```

The four standing `project_knowledge` WARNs — the strict-exempt class — and nothing else.

### 1b. Mirror-pair check (step 1, before anything was written)

```
$ diff -q ../aetheris/docs/methodology/triad-loop.md docs/triad-loop.md
$ echo $?
0
$ wc -l ../aetheris/docs/methodology/triad-loop.md docs/triad-loop.md
  188 ../aetheris/docs/methodology/triad-loop.md
  188 docs/triad-loop.md
  376 total
```

Byte-identical. No canonical sync. This is also what establishes that the **harness repo
takes no tracked write this boundary** — it was the only thing that could have produced one.

### 1c. Full 25-row verification — `git log -1 --format=%h -- <path>` in each row's OWN repo

Run after `de71e2b` landed, so these are the values the manifest was committed against.
All 25 files confirmed present on disk (`exists` column true for every row).

```
export name                              repo             pinned    git       exists  status
rig--specs.md                            aetheris-agents  99a46df   99a46df   True    ok
rig--architecture.md                     aetheris-agents  c0977c2   c0977c2   True    ok
rig--runbook.md                          aetheris-agents  7d6013a   7d6013a   True    ok
rig--protocol.md                         aetheris-agents  d82cf7e   d82cf7e   True    ok
rig--current-state-2026-06.md            aetheris-agents  f723ee5   f723ee5   True    ok
rig--bl-007-milestone.md                 aetheris-agents  675a5c2   675a5c2   True    ok
rig--CLAUDE.md                           aetheris-agents  5a5089b   5a5089b   True    ok
cloudcost--milestone.md                  aetheris-agents  7a7b7ec   7a7b7ec   True    ok
aetheris-agents--CLAUDE.md               aetheris-agents  13fc8c4   13fc8c4   True    ok
agent-creation-guide.md                  aetheris-agents  18b9b01   18b9b01   True    ok
capability-matrix.md                     aetheris-agents  4d98ec2   4d98ec2   True    ok
backlog-2026-06.md                       aetheris-agents  de71e2b   de71e2b   True    ok
aetheris--CLAUDE.md                      aetheris         1743e75   1743e75   True    ok
aetheris--runbook.md                     aetheris         ae0c510   ae0c510   True    ok
aetheris--architecture.md                aetheris         915d582   915d582   True    ok
aetheris--determinism-contract.md        aetheris         1ab24d8   1ab24d8   True    ok
aetheris--jiyi-brief.md                  aetheris         41ff2cf   41ff2cf   True    ok
aetheris--skill-mining-brief.md          aetheris         da8fb4d   da8fb4d   True    ok
aetheris--dirge-brief.md                 aetheris         b9a1cdb   b9a1cdb   True    ok
aetheris--coming-loop-brief.md           aetheris         934add8   934add8   True    ok
aetheris--weng-harness-brief.md          aetheris         ff971a8   ff971a8   True    ok
aetheris--activegraph-brief.md           aetheris         c195cbb   c195cbb   True    ok
methodology--milestone-methodology.md    aetheris         0a0439f   0a0439f   True    ok
methodology--triad-loop.md               aetheris         265d336   265d336   True    ok
project-knowledge-manifest.md            aetheris-agents  —         29a51fa   True    (self — skipped by design)

25 rows · 24 checkable · 0 mismatches · 0 missing files
```

Movers, all four predicted, no fifth:

| row | repo | was | now |
|---|---|---|---|
| `aetheris-agents--CLAUDE.md` | aetheris-agents | `0fc9396` | `13fc8c4` |
| `capability-matrix.md` | aetheris-agents | `b7cb6ca` | `4d98ec2` |
| `backlog-2026-06.md` | aetheris-agents | `9b5da48` | `de71e2b` |
| `aetheris--CLAUDE.md` | aetheris | `710ecd2` | `1743e75` |

### 1d. Post-commit — `python3 scripts/drift_check.py --strict` (the meaningful run)

```
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 50 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[PASS] project_knowledge: 24 manifest entries all match git HEAD
[PASS] command_fields: 11 documented §4 structs (56 fields) match commands/*.rs

Summary: 9 PASS  0 FAIL  0 WARN  7 INFO
exit=0
```

**9 PASS / 0 FAIL / 0 WARN.** The four standing `project_knowledge` WARNs cleared — which is
what an export boundary is supposed to produce, and the reason this run had to come after the
commit: check 8 reads committed history (`git log -1 -- <file>`), so a pre-commit run compares
against pre-edit hashes and passes vacuously.

### 1e. Push state

```
$ git status -sb          # aetheris-agents (before this boundary)
## main...origin/main
$ git status -sb          # aetheris (before and after)
## main...origin/main
```

Both repos were level with `origin/main` at `a596697` / `5e7935f`, so every pinned hash —
including the harness's `1743e75` — is already public and reproducible. The two commits below
are **held for review, not pushed.**

### 1f. Bundle assembly (BL-002 Step 3) — `/tmp/claude-project-export/`

Built after the commits, from the manifest table rather than a hand-typed list. Three
assertions run per file, not just the copy: source exists; export name does not collide; the
copy is byte-identical to the source (`filecmp.cmp(shallow=False)`); and the worktree source is
byte-identical to `git show <pinned>:<path>` in the owning repo — so the bundle is provably the
content the manifest pins, not merely the content on disk.

```
$ rm -rf /tmp/claude-project-export && mkdir -p /tmp/claude-project-export
$ python3 <assemble-from-manifest>
copied 25 files from 25 manifest rows
problems: none
```

Content spot-check on the four re-pinned files (each expects 1 except the backlog, 2):

```
$ grep -c 'drift_check` verifies a pin is current' aetheris-agents--CLAUDE.md   -> 1
$ grep -c 'self-falsifying'                        aetheris--CLAUDE.md          -> 1
$ grep -c '| cloudcost | 1 | 8 |'                  capability-matrix.md         -> 1
$ grep -c 'BL-09[02] — DONE 2026-08-05'            backlog-2026-06.md           -> 2
$ grep -c 'm3-cloudcost close (Linode as ...)'     project-knowledge-manifest.md-> 1
```

**The three-way `CLAUDE.md` collision — the reason the rename is mandatory.** Three rows resolve
to files all literally named `CLAUDE.md`, from two repos and two directories. They cannot be
uploaded as themselves, and a hand rename across 25 files is where a remove-all-upload-all goes
quietly wrong. Verified distinct, and each against its own source and no other:

```
aetheris-agents--CLAUDE.md      41211 bytes  sha256=5d0fe8d4a223167d
aetheris--CLAUDE.md             50763 bytes  sha256=1949cc3cb5a03666
rig--CLAUDE.md                  21125 bytes  sha256=dc9822c5a58ac16f

aetheris-agents--CLAUDE.md   <- aetheris-agents/CLAUDE.md       IDENTICAL
aetheris--CLAUDE.md          <- aetheris/CLAUDE.md              IDENTICAL
rig--CLAUDE.md               <- aetheris-agents/rig/CLAUDE.md   IDENTICAL

duplicate-content pairs across all 25 bundle files: 0
```

The zero-duplicates line is the check that a wrong-source copy would fail: two export names
resolving to the same file would collide on content hash even when both copies "succeeded".

**Set comparison, bundle vs manifest — neither direction may have a remainder:**

```
manifest export names: 25
files in bundle      : 25
in manifest, missing from bundle: none
in bundle, not in manifest      : none
```

### 1g. BL-002 Step 5 — the listing

```
$ ls -1 /tmp/claude-project-export | tee /tmp/claude-project-export.listing
aetheris--activegraph-brief.md
aetheris-agents--CLAUDE.md
aetheris--architecture.md
aetheris--CLAUDE.md
aetheris--coming-loop-brief.md
aetheris--determinism-contract.md
aetheris--dirge-brief.md
aetheris--jiyi-brief.md
aetheris--runbook.md
aetheris--skill-mining-brief.md
aetheris--weng-harness-brief.md
agent-creation-guide.md
backlog-2026-06.md
capability-matrix.md
cloudcost--milestone.md
methodology--milestone-methodology.md
methodology--triad-loop.md
project-knowledge-manifest.md
rig--architecture.md
rig--bl-007-milestone.md
rig--CLAUDE.md
rig--current-state-2026-06.md
rig--protocol.md
rig--runbook.md
rig--specs.md

$ wc -l < /tmp/claude-project-export.listing
25
```

The count is read out of the listing, not asserted beside it.

---

## 2. The diff

```
 docs/backlog-2026-06.md            | 64 +++++++++++++++++++++++++
 docs/project-knowledge-manifest.md | 97 ++++++++++++++++++++++++++++++++++++--
 2 files changed, 157 insertions(+), 4 deletions(-)
```

Two commits, in order:

- `de71e2b` — docs(backlog): BL-090 + BL-092 — DONE sections (m3 close)
- `29a51fa` — BL-002: project-knowledge manifest — m3-cloudcost export boundary

```diff
diff --git a/docs/backlog-2026-06.md b/docs/backlog-2026-06.md
index e2b64c3..c5d7b49 100644
--- a/docs/backlog-2026-06.md
+++ b/docs/backlog-2026-06.md
@@ -3229,6 +3229,35 @@ the second one afterwards.
 
 `Source: BL-084, 2026-08-03; label drift appended by BL-083, 2026-08-04.`
 
+### BL-090 — DONE 2026-08-05
+
+Regenerated in `4d98ec2` (m3-cloudcost t3), merged `8dca843`. **Both** stale cells this row
+accumulated reconcile in the one pass it asked for:
+
+| cell | before | after | filed by |
+|---|---|---|---|
+| Agent Label | `Cloudcost Orchestrator` | `Cloudcost · {provider}` | BL-083, 2026-08-04 |
+| Scripts | 6 listed, `detect_optimization_signals.py` absent | 8 listed | BL-084, 2026-08-03 |
+
+Summary row `| cloudcost | 1 | 6 |` → `| 1 | 8 |`; totals `27 | 82` → `27 | 84`.
+
+**Eight, not the seven §t3 predicted.** The "seven" figure is the scout's §A9 count, written
+against `dc8c077` — six on the matrix plus `detect_optimization_signals.py` — and it predates
+t1 adding `fetch_linode.py`. So the doc was the stale side of its own staleness ticket: t3
+reported the count the regen produced and flagged the prediction rather than reconciling
+down to it (`m3-milestone.md` rev 7 corrected §t3). This is the m3 learning about documents
+that quote repo state, fired on the row whose subject *is* a document quoting repo state.
+
+Regenerated by the §A9 ritual — the cloudcost section agent alone
+(`cap-matrix-cloudcost-BEWzHw`), then `assemble_matrix.py` over all nine sections. Never a
+full nine-agent regen (BL-068: `docs/.sections/` is gitignored, so a full re-run destroys the
+eight sections it does not regenerate), never a hand-edit — the artifact is generated, which
+is the reason this row exists rather than a one-line fix. The regen also rewrote the six
+carried script descriptions from current docstrings; that is regen output, not a curation.
+
+`Source: BL-084 (filed 2026-08-03), label drift appended by BL-083 (2026-08-04), closed by
+m3-cloudcost t3 done-when 5, 2026-08-05.`
+
 ### BL-091 — exportConfig() drops every manifest-derived env key (#TBD)
 **Size:** S · **Priority:** low-medium · **Section:** aetheris-agents (`rig/`)
 
@@ -3254,6 +3283,41 @@ but fails serde is dropped to None with every script going amber and nothing say
 
 `Source: BL-084, 2026-08-03.`
 
+### BL-092 — DONE 2026-08-05
+
+Landed `f28b817` (m3-cloudcost t2), merged `f552094`. A `#[cfg(test)] mod tests` at the end of
+`rig/src-tauri/src/commands/tools.rs` — 157 insertions, 0 deletions, one hunk; the file is
+byte-identical outside `cfg(test)`.
+
+**Coverage is by walk, not by list.** `committed_manifests()` reads the agents root and takes
+every `<use_case>/tools.json`, mirroring `tools_list_inventory`'s own exclusions, so a manifest
+added later is guarded without editing the test. Four tests over that set:
+
+- `every_committed_manifest_round_trips_into_tools_manifest` — the property the row exists for.
+  `tools_list_inventory` does `serde_json::from_str(&raw).ok()`, so a schema violation is not an
+  error but a `None`: the use case silently falls back to all-undeclared, every script amber and
+  nothing saying why. Also re-serializes and re-parses, catching a field that deserializes only
+  because serde defaulted it away.
+- `a_manifest_missing_an_env_dep_field_is_rejected` — **the negative control.** Without it the
+  round-trip has only ever been seen passing, so it is not yet a check. Drops `"masked"` from
+  cloudcost's first `EnvDep` (a bool, so removal is a schema violation rather than a coercion),
+  asserts the mutation applied, and asserts the mutant fails to deserialize.
+- `discovery_finds_every_committed_manifest` — anti-vacuity for all of the above: a walk that
+  silently returned nothing would pass a round-trip over zero manifests. Asserts the *set*
+  (`api, cloudcost, drive, eduloka, email, payslip`), not a count, so adding a use case fails
+  where the expectation lives instead of silently widening coverage.
+- `env_deps_dedup_walk_keeps_the_first_occurrence_only` — the first-occurrence-wins dedup,
+  anchored on `CLOUDCOST_AWS_ACCESS_KEY_ID`, which genuinely repeats across `fetch_aws` and
+  `detect_optimization_signals`; the anchor's repetition is itself asserted, so the dedup is
+  doing work rather than passing over an already-unique list. Also asserts
+  `CLOUDCOST_LINODE_TOKEN` is masked in the Rig config surface.
+
+This is the standing offline guard `tests/test_tools_manifests.py` structurally cannot be: the
+pytest suite transcribes these structs, only this test runs serde. Seed was
+`cloudcost/docs/bl-084-implementation-notes.md` §"What is proven offline", as the row directed.
+
+`Source: BL-084 (filed 2026-08-03), closed by m3-cloudcost t2 done-when 5, 2026-08-05.`
+
 ### BL-093 — runbook drift: PAYSLIP_MONTH described as non-persistent (#TBD)
 **Size:** XS · **Priority:** low · **Section:** aetheris-agents (`rig/docs/`)
 
diff --git a/docs/project-knowledge-manifest.md b/docs/project-knowledge-manifest.md
index b90f806..8c14b83 100644
--- a/docs/project-knowledge-manifest.md
+++ b/docs/project-knowledge-manifest.md
@@ -32,11 +32,11 @@ discipline is what covers it. Source: BL-022 filing, 2026-07-17.
 | `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` | 2026-07-20 |
 | `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` | 2026-06-11 |
 | `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `7a7b7ec` | 2026-08-02 |
-| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `0fc9396` | 2026-08-03 |
+| `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `13fc8c4` | 2026-08-05 |
 | `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` | 2026-06-19 |
-| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `b7cb6ca` | 2026-08-02 |
-| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `9b5da48` | 2026-08-04 |
-| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `710ecd2` | 2026-08-03 |
+| `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `4d98ec2` | 2026-08-05 |
+| `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `de71e2b` | 2026-08-05 |
+| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `1743e75` | 2026-08-05 |
 | `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `ae0c510` | 2026-07-26 |
 | `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `915d582` | 2026-07-25 |
 | `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `1ab24d8` | 2026-07-26 |
@@ -233,3 +233,92 @@ the manifest-staleness class cleared, which is what an export boundary is suppos
 repo was not written this batch, so its 12 rows carry their prior hashes unchanged.
 
 Previous export: 2026-08-03 (m2-cloudcost close).
+
+---
+
+**Export boundary — 2026-08-05, m3-cloudcost close (Linode as provider three).** Four rows
+advanced, and only four: `aetheris-agents--CLAUDE.md` (`0fc9396`→`13fc8c4`) and
+`aetheris--CLAUDE.md` (`710ecd2`→`1743e75`), the milestone's §7 promotions — two doc-sync rules
+in agents, five m3 learnings in the harness; `capability-matrix.md` (`b7cb6ca`→`4d98ec2`),
+BL-090's regen; and `backlog-2026-06.md` (`9b5da48`→`de71e2b`), BL-098..BL-101, the BL-069
+went-green-and-reverted append, and the two DONE sections described below. 25 rows: **25
+carried, none added, none dropped.** The other 21 data rows are unchanged since the previous
+boundary.
+
+> **Mirror-pair check run first, per the BL-002 convention** — and it is what establishes
+> whether the harness repo takes a write at all this boundary. `triad-loop.md` canonical
+> (`aetheris/docs/methodology/`) and its `aetheris-agents/docs/` mirror are **byte-identical**
+> (188 lines each, `diff -q` clean), so no canonical sync was needed and the harness took no
+> tracked write. `drift_check` cannot see that class — it compares the manifest against git
+> history and has no byte-identity check between mirrors, so the `diff -q` is the only thing
+> that catches it. It is not a formality: at the 2026-08-03 boundary the same check found
+> canonical 26 lines short of its mirror, and the export would otherwise have shipped without
+> a rule claude-ui operates under.
+
+> **`cloudcost/m3-milestone.md` gets no row — ratified by the human at the m3 close.** m1's
+> `cloudcost/milestone.md` is exported because its §Normalized *is* the frozen contract every
+> adapter is written to, which is the milestone-*specification* test that also admits
+> `rig--protocol.md` and `rig--bl-007-milestone.md`. m3 does not meet it: it holds derived
+> reasoning *about* a contract that lives in m1's file — its §Milestone summary reports that
+> no §Normalized extension was needed and that the four shared scripts are byte-identical at
+> close, i.e. the contract m3 reasons against is m1's, unchanged. m2's milestone doc set the
+> precedent by staying out on the same reading.
+
+> **Working artifacts stay out as always — eight this milestone:**
+> `cloudcost/docs/m3-linode-scout.md`, the three
+> `cloudcost/docs/m3-t{1,2,3}-implementation-notes.md`, the three
+> `docs/reviews/m3-cloudcost-t{1,2,3}-review.md`, and
+> `docs/handoffs/handoff-linode-provider-three-kickoff-2026-08-04.md` (handoffs have never
+> carried a row). `cloudcost/runbook.md` changed this milestone — the Linode posture
+> subsection — and stays out on the standing precedent this manifest already records: no
+> use-case runbook has ever carried a row; the two exported runbooks are the Rig and harness
+> *system* runbooks. As at every prior boundary, this milestone's specifications are the
+> BL-0xx rows, already carried inside `backlog-2026-06.md`.
+
+> **Why the backlog row pins at `de71e2b` rather than the milestone's last content commit
+> (`b0030e7`).** m3's done-when 5 reads "BL-090 both cells reconciled, BL-092 landed over every
+> manifest ✓", and both had landed — the matrix regen at `4d98ec2` (t3), the `tools.rs` serde
+> guard at `f28b817` (t2) — but neither row carried a DONE section, so an export pinned at
+> `b0030e7` would have shipped project knowledge reading two closed rows as open. Written in
+> `de71e2b`, *before* the table was regenerated, so the row pins the corrected file. This is
+> the same mid-flight correction the 2026-08-04 boundary made for BL-073/BL-095, and it is now
+> covered by a standing rule rather than by noticing twice: `CLAUDE.md` §Definition of done —
+> doc sync, *"`drift_check` verifies a pin is current, never that it is complete — read the
+> pinned content against what it should say, do not trust the green."* Four movers matching the
+> four predicted is a hash result; it says nothing about whether the pinned content is
+> finished. The correction was **enumerated, not patched**: m3's §Done-when and §Milestone
+> summary were swept for every row they claim complete, which confirmed BL-096 already carries
+> its DONE (2026-08-04, `32933d8`) and that BL-069 must *not* be marked — its Linode leg went
+> green on 2026-08-05 and reverted when the plant was deleted, so it stays armed. Two rows
+> found by observation are not a census.
+
+**All 25 rows verified against their owning repos at regen** — every pinned commit equals
+`git log -1 --format=%h -- <path>` run in the owning repo (`../aetheris` for the 12 harness
+rows), and all 25 files exist on disk. The re-verification was run again after `de71e2b`
+landed, so the four re-pins are read from the tree the manifest is committed against.
+
+**Upload is remove-all then upload-all against the full 25-row set** — not a diff of the four
+re-pinned rows. Twenty-one data rows are unchanged and would look like "nothing to re-upload"
+to any hash-driven shortcut; do not optimise the upload down. `drift_check` compares
+manifest-vs-git, so it catches the repo running ahead of an export (the staleness WARN that
+clears at this boundary) but is blind to the reverse — a partial or under-described upload
+leaves project knowledge silently wrong while drift still reports green. The procedure is the
+only thing covering that direction, which is why it is now a standing rule in `CLAUDE.md`
+§Definition of done — doc sync rather than a paragraph re-derived each boundary.
+
+**Ordering invariant held.** `docs/backlog-2026-06.md` was written first and committed alone
+(`de71e2b`); the manifest is the boundary's **last** tracked write and commits alone. Nothing
+manifest-tracked was edited after the table was regenerated, so no row is born stale — BL-034's
+hazard, which is also why the post-commit `drift_check --strict` below is the meaningful one:
+check 8 reads committed history, so run before the commit it would have compared against
+pre-edit hashes and passed vacuously.
+
+**Repo push state.** Both repos were level with `origin/main` at the exported content commits
+(`a596697` / `5e7935f`) when this export began, so every pinned hash — including the harness's
+`1743e75` — is already public and reproducible. The harness took no tracked write this
+boundary, so its 12 rows carry hashes from its own pushed history. This boundary's two agents
+commits are **held for review, not pushed**. (Deliberately no self-hash: a line naming the
+manifest's own commit is stale the moment it is committed.)
+
+Previous export: 2026-08-04 (cloudcost-in-Rig batch close — two rows advanced, re-pinned once
+within the boundary).
```

---

## 3. Implementation notes

### 3.1 Order was the ticket, and it produced the one finding

Step 1 first, step 5 last, both held. The mirror check came back clean, which is a result
rather than an assumption — at the 2026-08-03 boundary the same check found canonical 26 lines
short of its mirror. Because it was clean, the harness needed no write, and the manifest's
twelve harness rows pin hashes from that repo's already-pushed history.

The row verification then produced exactly the four predicted movers and no fifth. That is
where the ticket could have ended, and where the finding is: **four movers matching four
predictions is a hash result and says nothing about whether the pinned content is finished.**
Reading the content — the rule m3 itself promoted into `CLAUDE.md` at `13fc8c4`, one of the
rows being pinned — showed the backlog was current but not complete.

### 3.2 Finding: BL-090 and BL-092 were complete-but-unmarked

`cloudcost/m3-milestone.md` §Milestone summary, done-when 5: *"BL-090 both cells reconciled,
BL-092 landed over every manifest ✓"*. Both had landed — the matrix regen at `4d98ec2` (t3),
the `tools.rs` serde guard at `f28b817` (t2) — and neither row carried a `### BL-0xx — DONE`
section. Pinned at `b0030e7`, the exported backlog would have read two closed rows as open.

Same shape as the previous boundary's mid-flight re-pin (`064664a`, BL-073/BL-095 merged but
unmarked). It recurring one boundary later, after being promoted to a standing rule, is the
useful part: the rule fired and caught it, which is the difference between this instance and
that one.

**Enumerated, not patched.** m3's §Done-when and §Milestone summary were swept for every row
they claim complete, rather than fixing the two noticed by eye:

| row | m3's claim | DONE section | disposition |
|---|---|---|---|
| BL-090 | done-when 5 ✓ · regen `4d98ec2` | absent | written |
| BL-092 | done-when 5 ✓ · guard `f28b817` | absent | written |
| BL-096 | t2 notes: landed `32933d8` | **present**, 2026-08-04 | verified, untouched |
| BL-069 | went green 2026-08-05 and **reverted** | absent | correct — stays armed |
| BL-070, BL-074, BL-078, BL-098–BL-101 | open by design | absent | correct |
| BL-071, BL-077, BL-087 | referenced, not claimed | absent | correct |
| BL-073, BL-083 | prior batch | present, 2026-08-04 | correct |

The two DONE sections were committed **first and alone** (`de71e2b`), so the backlog row pins
the corrected file rather than the manifest being written twice.

### 3.3 The two decisions recorded in the export note

**`cloudcost/m3-milestone.md` gets no row** (ratified by the human at the close). m1's
`cloudcost/milestone.md` is exported because its §Normalized *is* the frozen contract every
adapter is written to — the milestone-*specification* test that also admits `rig--protocol.md`
and `rig--bl-007-milestone.md`. m3 fails that test on its own evidence: §Milestone summary
reports that no §Normalized extension was needed and that the four shared scripts are
byte-identical at close, i.e. the contract m3 reasons against is m1's, unchanged. m2's
milestone doc set the precedent by staying out on the same reading.

**Working artifacts stay out — eight this milestone.** `cloudcost/docs/m3-linode-scout.md`;
`cloudcost/docs/m3-t{1,2,3}-implementation-notes.md`;
`docs/reviews/m3-cloudcost-t{1,2,3}-review.md`;
`docs/handoffs/handoff-linode-provider-three-kickoff-2026-08-04.md`. Also out, and noted
because it changed this milestone: `cloudcost/runbook.md` (the Linode posture subsection) — no
use-case runbook has ever carried a row; the two exported runbooks are the Rig and harness
*system* runbooks. m3's specifications are the BL-0xx rows, already inside `backlog-2026-06.md`.

### 3.4 Ordering invariant

`docs/backlog-2026-06.md` written and committed alone (`de71e2b`) → table regenerated →
`docs/project-knowledge-manifest.md` committed alone (`29a51fa`), the boundary's last tracked
write. No manifest-tracked file edited after the table. Verified by 1d rather than asserted.

### 3.5 The bundle — skipped, then run; the skip was wrong twice over

Steps 3 and 5 were initially skipped on the reading that the kickoff scopes this task to
verify/regen/note/hand-over, with the row set standing in for the bundle. Wrong on both counts,
and the two reasons are independent.

**It is not a staging convenience — it is what makes the upload correct.** The manifest's export
names are not the source filenames, and **three rows resolve to files all literally named
`CLAUDE.md`** (agents root, harness root, `rig/`). They cannot all be uploaded as themselves, so
the rename to the export name is mandatory, not cosmetic — and performing it by hand across 25
files drawn from two repos is precisely where a remove-all-upload-all goes quietly wrong. That
the session cannot upload is true and does not make the staging optional; it makes the staging
the only part of the upload the session *can* get right. Verified in §1f: three distinct hashes,
each matching its own source and no other, zero duplicate-content pairs across all 25.

**And skipping did not leave a neutral absence.** The directory still held the **2026-08-04
bundle** — 25 files at the prior export's timestamps, complete and plausible. An upload driven
from it would have re-published the previous boundary's content while the manifest described
this one: the manifest-blind direction check 8 cannot see, arriving through the one step I had
argued was skippable.

Generated **from the manifest table**, not a hand-typed list: the script parses the 25 rows,
resolves each `repo` to its root, and copies `<root>/<repo path>` → `<DEST>/<export name>`, so
the bundle cannot disagree with the row set about names, paths, or membership. Four assertions
per file (source exists · no name collision · copy byte-identical to source · source
byte-identical to `git show <pinned>:<path>` in the owning repo), plus a set comparison in both
directions and a listing whose count is read out of the listing (§1f, §1g).

### 3.6 Deferred to after the push — a backlog row, not an edit here

**BL-084 and BL-085 carry implementation notes on disk**
(`cloudcost/docs/bl-08{4,5}-implementation-notes.md`) **and no DONE section.** They belong to
the cloudcost-in-Rig batch, not m3, and no m3 document claims them complete — outside this
census by construction. The class this boundary found suggests the complete-but-unmarked sweep
should run at a *batch's* close too, not only a milestone's, with these two as the standing
instance.

**Filed after the push, not now** — adjudicated by the reviewer. Filing it edits
`docs/backlog-2026-06.md`, which the manifest pinned at `de71e2b` two commits ago, so it would
re-stale the row this boundary just cleared and reopen a WARN *inside* the boundary that exists
to close it. After the push it is ordinary mid-cycle staleness, which clears at the next
boundary. Recorded here and in session memory so it survives the gap — prose in a packet files
nothing, so the row is owed once the push lands.

---

## 4. Hand-off — the upload half (human)

**Bundle:** `/tmp/claude-project-export/` — 25 files, named by export name, listing at §1g.
Upload from here, not from the repos: three rows are files named `CLAUDE.md` and only the
bundle carries them under names that can coexist in one knowledge store.

**Procedure: remove ALL existing project-knowledge files, then upload ALL 25.** Never a diff
of the four re-pinned rows. Twenty-one rows are unchanged and would look like
"nothing to re-upload" to any hash-driven shortcut. `drift_check` check 8 compares
manifest-vs-git: it catches the repo running ahead of an export, and is structurally blind to
a partial upload — project knowledge can be silently wrong while drift reports green. This is
now the standing rule in `CLAUDE.md` §Definition of done — doc sync.

| # | export name | source file | repo | commit |
|---|---|---|---|---|
| 1 | `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `99a46df` |
| 2 | `rig--architecture.md` | `docs/rig/architecture.md` | aetheris-agents | `c0977c2` |
| 3 | `rig--runbook.md` | `docs/rig/runbook.md` | aetheris-agents | `7d6013a` |
| 4 | `rig--protocol.md` | `docs/rig/milestones/p3/protocol.md` | aetheris-agents | `d82cf7e` |
| 5 | `rig--current-state-2026-06.md` | `docs/rig/current-state-2026-06.md` | aetheris-agents | `f723ee5` |
| 6 | `rig--bl-007-milestone.md` | `docs/rig/milestones/bl-007/README.md` | aetheris-agents | `675a5c2` |
| 7 | `rig--CLAUDE.md` | `rig/CLAUDE.md` | aetheris-agents | `5a5089b` |
| 8 | `cloudcost--milestone.md` | `cloudcost/milestone.md` | aetheris-agents | `7a7b7ec` |
| 9 | `aetheris-agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `13fc8c4` **←re-pinned** |
| 10 | `agent-creation-guide.md` | `docs/agent-creation-guide.md` | aetheris-agents | `18b9b01` |
| 11 | `capability-matrix.md` | `docs/capability-matrix.md` | aetheris-agents | `4d98ec2` **←re-pinned** |
| 12 | `backlog-2026-06.md` | `docs/backlog-2026-06.md` | aetheris-agents | `de71e2b` **←re-pinned** |
| 13 | `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `1743e75` **←re-pinned** |
| 14 | `aetheris--runbook.md` | `docs/aetheris/runbook.md` | aetheris | `ae0c510` |
| 15 | `aetheris--architecture.md` | `docs/aetheris/architecture.md` | aetheris | `915d582` |
| 16 | `aetheris--determinism-contract.md` | `docs/aetheris/determinism-contract.md` | aetheris | `1ab24d8` |
| 17 | `aetheris--jiyi-brief.md` | `docs/aetheris/research/jiyi-memory-service-2026-06.md` | aetheris | `41ff2cf` |
| 18 | `aetheris--skill-mining-brief.md` | `docs/aetheris/research/skill-mining-2606.20363-2026-06.md` | aetheris | `da8fb4d` |
| 19 | `aetheris--dirge-brief.md` | `docs/aetheris/research/dirge-agent-2026-06.md` | aetheris | `b9a1cdb` |
| 20 | `aetheris--coming-loop-brief.md` | `docs/aetheris/research/coming-loop-ronacher-2026-06.md` | aetheris | `934add8` |
| 21 | `aetheris--weng-harness-brief.md` | `docs/aetheris/research/weng-harness-2026-07.md` | aetheris | `ff971a8` |
| 22 | `aetheris--activegraph-brief.md` | `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` | aetheris | `c195cbb` |
| 23 | `methodology--milestone-methodology.md` | `docs/methodology/milestone-methodology.md` | aetheris | `0a0439f` |
| 24 | `methodology--triad-loop.md` | `docs/methodology/triad-loop.md` | aetheris | `265d336` |
| 25 | `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | `this export` |

Harness rows resolve against `../aetheris`; the rest against `aetheris-agents`. The manifest
row uploads as itself — its own commit is deliberately not recorded (a line naming it is stale
the moment it commits).

**Refresh rule (BL-002).** Re-run this task at milestone end or before any handoff session. The
manifest commit hash is how a future session detects staleness; `/tmp/claude-project-export/` is
ephemeral and is rebuilt each boundary from the regenerated table.

**Then:** push is held pending this review. Once pushed, the boundary is closed, the §3.6 row
gets filed, and the next `drift_check --strict` stays at 0 WARN until the next
manifest-tracked edit lands — at which point the staleness is ordinary mid-cycle truth.

> **Outcome.** All three happened in that order. The upload was verified in-store: 25/25 by
> name, no duplicates, the three `CLAUDE.md` files coexisting under distinct export names, and
> every document timestamped inside one second at 11:57:4x — the signature of a genuine
> remove-all-upload-all rather than an incremental patch. That check had no home in the
> procedure when this packet was written; it does now (`1db6797`), and it found a 26th document
> on its first run (§5.3).

---

## 5. Post-boundary addenda (after the push; ordinary mid-cycle staleness)

### 5.1 `aetheris/CLAUDE.md` — credential-provenance rule (`082b37c`, pushed)

Confirmed **by opening the file at its committed state**, not by asserting the edit landed —
the rule immediately above it is what requires this. `git show 082b37c:CLAUDE.md`, lines
733–753, quoted with the preceding entry's closing `Source:` line for placement:

```
  distilled; it is complete when the entry is in the file, verified by opening it.
  `Source: m3-cloudcost close — census of handoff-linode-provider-three-kickoff-2026-08-04.md
  §Review-discipline learnings promoted (:83-91) and handoff-cloudcost-rig-batch-close-2026-08-04.md
  §Review learnings promoted (:127-135) against both CLAUDE.md files: four of four absent.`

- **A credential of unknown provenance is never authenticated as a diagnostic — destroy it and
  re-mint.** Testing whether an unidentified secret works transmits it to a party you have not
  identified, authenticates as an identity you do not own, and writes an entry into an audit
  trail belonging to someone you cannot name — none of which is undoable, and none of which
  buys much: a rejection is equally consistent with expired, revoked, and never-a-credential-
  for-that-service. Delete the copy, mint a scoped replacement, and record the disposition. This
  is promoted on a single instance deliberately: the ≥2-ticket bar assumes a missed rule costs
  another review finding, and where the violation is irreversible the second instance *is* the
  incident the rule exists to prevent.
  `Source: m3-cloudcost t1 preflight, 2026-08-05 — a 64-character credential-shaped
  LINODE_BILLING found in the session environment, read by no Linode library; the probe was
  declined and the value destroyed unread, with the target account's empty PAT list settling
  what it could not have been.`

- **Nil-key-guard.** When adding a nil guard to an adapter's `call/2` …
```

**Cluster placement verified independently of the read-back**: nearest preceding heading of any
level is `### Workflow patterns` (CLAUDE.md:520), inside `## Continuous learning` (:485) — the
same cluster as the m3 promotions. (A first check that matched only `^## ` reported
`Continuous learning` and looked like a miss; the any-level query is the correct one.)

`aetheris--CLAUDE.md` is manifest-tracked at `1743e75`, so this commit stales that row —
expected post-boundary mid-cycle staleness, strict-exempt, clearing at the next export.

### 5.2 BL-104 — filed verbatim (`59bec3f`), citations then anchored (`80c801c`)

The row's text reached the session two turns after it was first referenced; filed unchanged,
including the held standing-rule paragraph, which the text already carried. Its own logic is why
it belongs there rather than in a packet: the trigger should live where someone acting on it will
be standing.

**Three `sprint.sh` citations have shifted and were NOT silently corrected** — the standing rule
is that divergence between ticket text and repo reality is noted, never followed and never
quietly patched. Verified at `aetheris@082b37c`:

| cited | actual | site |
|---|---|---|
| `:2371-2373` | **`:2383-2386`** | `CC_HERMETIC=(env -u …` array |
| `:2453-2487` | **`:2480-2560`** | poison-control block (`CC_POISON=` at `:2487`) |
| `:2465` | **`:2512`** | `[[ "$CC_PROVIDER" == "aws" ]]` in-block (`:2651`, `:2671` also match) |

`:2465` currently lands on a Linode `env -u CLOUDCOST_LINODE_TOKEN` invocation and `:2453` on the
tail of the no-silent-fallback assertion, so the numbers do not merely point loosely — they point
at other code. The prose identifies every site unambiguously (`CC_HERMETIC`, the poison-control
block, the AWS arm's gate), so the row is actionable as filed and this is a docs defect rather
than a blocking one.

**Amended at `80c801c`.** claude-ui replaced all three with anchors naming the construct and the
line number as a parenthetical against a stated commit — the fix the m3 *cite by anchor*
promotion prescribes, rather than a renumber that re-rots on the next insert (which is how these
three drifted). A `Citations verified at aetheris@082b37c` line was added under the `Source:`.

**One correction to the supplied wording, applied rather than filed-and-flagged.** It attributed
`:2651` to the D2 credential grep and `:2671` to the region assertions; at `082b37c` they are
reversed (`:2652` = *"A4: the report states the swept-region set"*, `:2672` = *"D2, the
trajectory half"*). Written in verified order. The stale *numbers* were filed as given and
flagged, because a wrong number under no claim is a docs defect; a transposed pair **under a
line asserting the citations were verified** makes the row misstate its own provenance, which is
worse than the drift being fixed. Note what the transposition is: a two-part phrase collapsed
onto the wrong number — the exact failure the m3 promotion was drawn from, recurring inside the
amendment that implements it. All eight citations re-verified against
`git show 082b37c:scripts/sprint.sh` after the edit; paragraph reflowed, no words changed.

### 5.3 What the boundary produced downstream

Four rows and two rules, none of which existed when §§1–4 were written. The boundary's method —
read the pinned content rather than trust the green — is what generated each:

- **BL-102** (`c41199b`) — the complete-but-unmarked sweep runs at milestone closes only, so
  batch closes leave rows silently open. From this boundary's own finding recurring one boundary
  after the rule that catches it was promoted.
- **BL-002 §Post-upload verification** (`1db6797`) — three store-side checks, the third being
  *no document predates the upload window*. The upload half had no detector at all before this.
- **BL-103** (`455b45a`) — that check's first run found 26 documents against a 25-row manifest.
  The benign branch is the uncomfortable one: if non-manifest docs may legitimately coexist,
  Step 5's remove-all is destructive against a document this repo does not own, and has been
  running unscoped at every boundary to date.
- **BL-104** (`59bec3f`, `80c801c`) — invert `sprint.sh`'s hermetic prefix from denylist to
  allowlist, on the `LINODE_BILLING` instance.
- **`aetheris/CLAUDE.md`** (`082b37c`) — never authenticate a credential of unknown provenance;
  promoted on one instance because where the violation is irreversible, the second instance *is*
  the incident the rule prevents.

Standing drift after all of it: **8 PASS / 0 FAIL / 2 WARN** — `backlog-2026-06.md` and
`aetheris/CLAUDE.md` against their boundary pins. Ordinary mid-cycle staleness, strict-exempt,
clearing at the next export. The 0-WARN state belongs to the boundary, not to the weeks after
it.
