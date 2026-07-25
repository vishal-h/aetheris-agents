# BL-041(b) + BL-036 — implementation notes

Two backlog rows closing two `drift_check` blind spots, batched because they land on one file
surface (`scripts/drift_check.py` + `tests/test_drift_check.py`).

Applied at agents HEAD `7fa5c16`, harness `af56a57` (both trees clean at start).
Implementation commit `11675cc`; the backlog DONE sections follow in a second commit so they
can cite it.

## What landed

**BL-041(b) — the uncommitted-edit guard (check 8).** `check_project_knowledge` resolves each
manifest row's "actual" hash with `_git_head_hash` → `git log -1 --format=%h -- <path>`, which
reads **committed** history. An uncommitted edit to a tracked doc creates no commit, so it is
invisible to the check: a pre-commit `--strict` run reports the manifest clean whether or not
the edit was made. New `_git_is_dirty` runs `git status --porcelain -- <path>` per row and
emits a per-path **strict-exempt** WARN when the path is dirty, naming the vacuity and saying
to re-run after committing. Structural arms stay **non-exempt**: missing manifest, unknown
repo, `git log` failure, and now a `git status` failure.

**BL-036 — check 9, `command_fields`.** Parses the ` ```rust ` fenced blocks under specs §4 for
`pub struct NAME { pub field: Type }` and compares against the same-named struct in
`rig/src-tauri/src/commands/*.rs`. WARN on documented-but-absent (the phantom-field case),
struct-field-undocumented, type mismatch, and ghost struct; FAIL only on the structural "zero
structs parsed from §4". `check_tauri_commands` is untouched and stays names-only, three-way —
the ratified shape was a new check, not field logic folded into check 2.

## Decisions

**The porcelain runs in the row's owning repo.** `_git_is_dirty` takes the same
`(repo_dir, path)` shape as `_git_head_hash` and is called after `_REPO_DIR_MAP` resolution, so
the harness rows are queried against `../aetheris`. Running porcelain from `REPO_ROOT` for them
would report every harness path clean — the same blindness the ticket exists to close, one
layer down, and it would have been invisible in a green run. A dedicated test records the
`(repo_dir, path)` pairs and asserts the `aetheris` row is queried with `HARNESS_ROOT`.

**The PASS is suppressed while any tracked path is dirty.** `if not stale` became
`if not stale and not uncommitted`. "23 manifest entries all match git HEAD" is a well-formed,
authoritative answer to a question the run cannot yet answer — exactly the Silent-wrong-answer
carrier BL-041 was filed against. Leaving the PASS beside the new WARN would have let the guard
land and the misleading headline survive.

**A `git status` failure is structural, not exempt.** It reports that the guard itself could not
run, which is a different fact from "there is an uncommitted edit" and belongs with the existing
`git log failed` arm. Only the dirty-path WARN is exempt, on the same terms as staleness: it
says this run cannot answer the staleness question yet, not that something regressed.

**Struct name is check 9's join key**, not command name. It is present verbatim on both sides,
and one fenced block may declare two structs (`TrajectoryEvent` + `TrajectoryFile`), which a
command-keyed mapping could not express.

**One shared field parser for both sides.** The doc blocks and the Rust source are the same
syntax, so `_parse_rust_struct_fields` serves both: it drops `///` doc comments, trailing
`// …` notes and `#[…]` attributes, and matches one field per line rather than splitting on
commas — a type may itself contain a comma (`HashMap<String, String>`). Both live shapes need
this: the doc's two-line `// COALESCE(...)` continuation comment under `RunSummary.label`, and
the `///` doc comment above `RunSummary.total_input_tokens` in `harness.rs`.

**`?`-suffix optionality reused from §6.** A documented `field?: T` is satisfied by `Option<T>`.
`?` relaxes the **type**, not existence — a `field?` absent from the struct still warns, and
that has its own test. §4 documents `Option<T>` directly today and uses no `?`; the convention
is forward-compatible rather than currently exercised by the repo.

## Check 9's result at HEAD: clean, nothing to reconcile

9 documented §4 structs, 52 fields, all matching: `RunSummary`, `EventRow`, `RunDetail`,
`HarnessStatus` (`commands/harness.rs`), `TrajectoryEvent`, `TrajectoryFile`
(`trajectory.rs`), `PollResult` (`orchestrate.rs`), `CapabilityMatrix`
(`capability_matrix.rs`), `UsageStats` (`usage.rs`). The phantom `RunDetail.events` that
prompted BL-036 was already corrected in the BL-029 commit, and nothing else had drifted — so
**`docs/rig/specs.md` was not touched**. The row closes with nothing to find rather than with a
silent fix; no §4 correction was warranted and none was made, and nothing was filed.

The green is mutation-checked, not asserted (Silent-wrong-answer: a check that cannot fail is
not a check). Neutering the dirty branch and the absent-field branch turns exactly their six
tests red; restoring returns 49 green.

## Numbering — nothing to renumber

`check_command_fields` is **appended** to `CHECKS`, so it is check 9 and `project_knowledge`
stays check 8 — the manifest header's "Check 8 … `project_knowledge`" reference is unaffected.
The `N check(s)` header and the `Summary:` line were already computed from
`len(selected)`/`FINDINGS` and read 9 with no edit, and no test asserted a check count
(`test_integration_no_fail` iterates `drift_check.CHECKS`). What did need editing was the
module docstring's `Checks:` list and its `--strict` paragraph. `sprint.sh` needs no change:
its `drift_check` case invokes `--strict` with no hardcoded count.

## Tests: 33 → 49

Both directions for each guard. BL-041(b): dirty tracked path warns (and no PASS is emitted);
the same under `--strict` stays WARN and is not promoted; clean tree is silent and passes; a
dirty path that is *not* a manifest row produces no signal; a `git status` failure FAILs under
`--strict`; and the cross-repo routing assertion above. BL-036: matching struct passes; phantom
documented field caught; undocumented source field warns; type mismatch warns; `field?` ↔
`Option<T>` accepted; `field?` absent still warns; ghost struct warns; zero-structs and
missing-anchor FAIL; plus a direct parser test for comment/attribute/`HashMap<String, String>`
handling.

**The four existing `project_knowledge` tests were made hermetic.** They patched
`_git_head_hash` only, so once the guard landed they would have shelled out to real `git status`
and taken their answer from the ambient working tree —
`test_project_knowledge_fresh_entries_pass` asserts `not warns_of(...)` and would have flipped
red the moment `docs/rig/specs.md` or `CLAUDE.md` was dirty. Each now patches `_git_is_dirty`
too. Note this is one more than the three the ticket anticipated: the structural-FAIL test
needed it as well.

## Done-check ordering — the ticket exercises its own guard

`docs/backlog-2026-06.md` is manifest-tracked, so marking these two rows done re-stales it, and
the done-check runs **post-commit** per the rule landed at `1013a95`. That makes this ticket its
own worked example of the boundary, in both directions.

**Pre-commit** (`11675cc` in, backlog edit uncommitted) — the new guard fires and the staleness
WARN cannot:

```
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 48 commands checked: lib.rs / .rs files / specs.md §4
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
[WARN] project_knowledge: docs/backlog-2026-06.md has uncommitted working-tree changes — this check compares committed history, so its staleness reading for this path is vacuous; re-run --strict after committing
[PASS] command_fields: 9 documented §4 structs (52 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  1 WARN  7 INFO
EXIT=0
```

**Post-commit** — the uncommitted WARN clears and the exempt staleness WARN takes its place;
the full output is in the review packet. Both runs exit 0, and the two WARNs are the expected,
named signals: the uncommitted one is this ticket's own guard reporting on itself, the staleness
one is mid-cycle truth cleared at the next export boundary, **not** this ticket's to clear.

Before the guard existed, the pre-commit run would have printed
`9 PASS 0 FAIL 0 WARN` — indistinguishable from a run where the backlog had never been edited.
That is the whole finding, reproduced by the fix.

## Scope held

Checks 1–7 untouched. `check_tauri_commands` untouched. The strict-mode staleness exemption and
its rationale untouched. No `CLAUDE.md` edit (disposition (a) landed at `1013a95` — **no
restart due**). No export / manifest regen — the backlog staleness it introduces is expected
mid-cycle staleness, cleared at the next export boundary. The 7 standing INFOs untouched.
`docs/rig/specs.md` untouched (see above). Push held for the human.
