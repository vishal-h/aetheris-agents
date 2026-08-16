# The project-knowledge export mechanism — implementation notes

`2026-08-16, at agents e3cf24d / aetheris d19f4b6. Every citation below is measured at that
pair unless it names another commit.`

Ticket: *commit the project-knowledge export mechanism*. It fixes one thing — that nothing
existed to execute — and settles nothing about who owns the boundary, on what schedule, what
belongs in the export set, or the check-1/check-3 contradiction. **BL-143** owns all of those
and is untouched.

---

## 1. Gate

### (i) Both repos clean and level

```
aetheris-agents  git status --short → (empty)   rev-list --left-right --count origin/main...HEAD → 0  0   HEAD e3cf24d
aetheris         git status --short → (empty)   rev-list --left-right --count origin/main...HEAD → 0  0   HEAD d19f4b6
```

The manifest's pass-2 commit is `e3cf24d`, pushed and public.

### (ii) Companion artifacts, from what the repo already attaches

Four classes were named; each was read rather than assumed.

| companion | what `assemble_matrix.py` / `drift_check.py` carry | owed here | landed |
|---|---|---|---|
| tests | `tests/test_assemble_matrix.py`, `tests/test_drift_check.py` — one file per script | yes | `tests/test_export_bundle.py`, `tests/test_repin_manifest.py` |
| runbook section | `docs/capability-matrix-runbook.md` for the matrix; `CLAUDE.md` §Definition of done for the drift checker | yes | the operator procedure is `prompts/bl-002-refresh-project-knowledge.md` (W3), plus a pointer paragraph in `CLAUDE.md` §Definition of done — doc sync |
| `tools.json` entry | **neither has one** | **no** | — |
| root discovery count | `cloudcost/docs/m5-rescue-edit-implementation-notes.md:54` | yes | de-numeralised |

**Why no `tools.json` entry is owed, established rather than assumed.** `tools.json` is
per-use-case and Rig's walker globs `<use_case>/scripts/*.py`
(`tests/test_tools_manifests.py:71`, mirroring `tools.rs:551-575`). `test_tools_manifests.py`'s
`_discover()` sweeps top-level directories for one holding `scripts/*.py` or a `tools.json`;
repo-root `scripts/` has neither a nested `scripts/` nor a manifest, so it is not swept, and
neither `assemble_matrix.py` nor `drift_check.py` is declared anywhere. Confirmed by
`test_discovery_sweep_intact`, whose asserted directory list does not contain `scripts`. A
manifest entry here would be a new convention, not a companion.

**The root discovery count.** `cloudcost/docs/m5-rescue-edit-implementation-notes.md` §2 read
*"repo-root `scripts/` holds exactly three curated standing tools (`assemble_matrix.py`,
`check_run_classifier.py`, `drift_check.py`)"*. This ticket falsifies it. Per `CLAUDE.md`
§Learning — m6-cloudcost the count is **de-numeralised, not corrected**: correcting three to
four re-arms the same trap for the next tool, and the sentence's argument — that eleven one-off
`q.py`/`ex.py` files would degrade a directory of curated standing tools — never needed the
figure. The enumeration went with it, being the second surface. The edit is one line inside a
historical notes file and preserves its proposal unchanged; that judgement is flagged for the
reviewer rather than buried.

**One companion is owed and cannot land here: a sprint case.** Both comparators have one
(`sprint.sh` `capability_matrix` and `drift_check`, `aetheris/scripts/sprint.sh:1533` and
`:1594`). `sprint.sh` lives in the harness, which this ticket's REPOS clause puts out of bounds,
so the export mechanism ships with tests and no sprint arm. Reported rather than quietly
dropped; it is a gap for whoever takes BL-143, not a defect this ticket may fix.

### (iii) One job per script, versus one script with modes

**The convention is one job per script, and it is stated rather than implied.** `CLAUDE.md`
§Python script conventions: *"One responsibility per script. Compute scripts → JSON. Generation
scripts → files. No mixing."* The tree agrees — `assemble_matrix.py` assembles and does not
check, `drift_check.py` checks and does not write, and cloudcost runs one script per pipeline
stage. `drift_check.py --check NAME` is not a counter-example: it selects among sub-checks of
one job, it does not switch jobs.

**Followed: two scripts**, because the ticket names two operations that share nothing but a
parser — assembling a bundle (reads git, writes a directory) and rewriting the manifest's commit
column (reads git, writes one file).

The parser they share is the third file, `scripts/_manifest.py`, per `CLAUDE.md` §Learning —
m2b-docbuilder (*"factor cross-script plumbing into a shared `_helper.py` module"*). It is
import-only and has no `__main__`, so it is not a fourth CLI.

### (iv) The known-good target, established

The bundle at `/tmp/claude-project-export` was built at `4d33048`; HEAD is now `e3cf24d`.

```
$ git log --oneline 4d33048..HEAD
e3cf24d docs(export boundary): the upload as performed, and the deviation's condition replaced
$ git diff --name-only 4d33048..HEAD
docs/project-knowledge-manifest.md
```

Intersected with the manifest's own source list, **exactly one of the exported sources has
moved**: `docs/project-knowledge-manifest.md` → export name `project-knowledge-manifest.md`.
The harness took no commit in the window (`d19f4b6` then and now), so none of its twelve rows
moved. That one file is compared against `git show HEAD:<path>`; the other twenty-four must
reproduce the preserved bundle byte for byte. The row count itself was derived by parsing the
table, not taken from the prompt: **25**.

---

## 2. W1a — the destination

**Choice: refuse a non-empty destination; `--replace` moves it aside; nothing is ever deleted.**

The ground has two halves. The first is the ticket's: the last export found a complete bundle
from a previous boundary sitting at the target, and writing into it would have produced
correctly-named, parseable files from two exports with nothing distinguishing them — a merged
bundle is not detectably wrong from the inside, which is why the refusal has to be structural
rather than a warning.

The second is why `--replace` **moves** rather than deletes: the previous bundle is the only
surviving record of what was last uploaded, and this ticket's own done-check depends on exactly
that — the reproduction is measured against a bundle a delete-and-recreate implementation would
have destroyed. The aside directory is `<dest>.superseded.<n>`, `n` the lowest free integer, so
a second replace cannot overwrite the first.

Visible in the output rather than only in the code: the refusal prints the entry count and the
first entries it found and exits 1; the move prints `previous bundle moved aside to … (not
deleted)`.

## 3. W1b — the U2 sweep

**Choice: the bundle is written unswept and says so — in the bundle, not only on the terminal —
and the sweep is runnable through the same script when the operator supplies the needles.**

**What was established.** The sweep cannot be run unaided by a committed script, and the reason
is not effort. U2's needles *are* the identifiers: the organisation login, seat logins, numeric
user ids, node ids, emails, token-shaped strings
(`cloudcost/docs/m6-t2-implementation-notes.md` §U2). m6 t3 recorded what happens when a
redactor carries them — *"a redactor built that way is not itself a disclosure"* is said of one
that **learns** the identities at runtime, and the one that hardcoded them *"had to be destroyed
like the leak it was fixing"* (§8a). A committed sweep script with a needle list would be the
disclosure it exists to prevent, and it would be in the export set's own repo.

So: default is the notice. `_UNSWEPT-DO-NOT-UPLOAD.txt` is written **into the bundle**, because
the terminal scrolls and the directory is what the operator uploads; its name is uppercase and
not `.md`, so it does not read as an export document, and if it were uploaded blind it would
break the store-side name check — an unswept bundle fails loudly rather than passing quietly.
The marker names U2's class, names why the script cannot check it, and gives the invocation that
clears it.

`--needles FILE` (untracked, one per line) runs the sweep here instead: any hit fails the run
and keeps the marker; a clean sweep writes no marker at all. That makes the marker's removal a
**consequence of the sweep passing** rather than an operator's discretion, which is the part
worth having. An empty or comment-only needle file is refused rather than read as a clean sweep
— a sweep over zero needles passes trivially and would clear the marker.

**The cost, stated once.** The marker is a file in a directory whose contents an operator is
told to upload. That is a real cost and the alternative is worse: a silent unswept bundle is how
six live seat logins reached a review (BL-150, `2026-08-14`). Step 5 of the prompt now requires
the marker's absence to be reported before upload instructions are printed.

**What this does not do.** It does not run U2 at the export boundary, and it is not a fix for
BL-150's finding that the leak check's scope excludes the artifact most likely to leave the
repo. It makes the gap say its own name.

---

## 4. W2 — the pin updater

`scripts/repin_manifest.py` reads `git log -1 --format=%h -- <path>` per row **in that row's own
repo** — the exact command check 8 compares against — and rewrites the commit cell in place,
anchored on the row's own line and its two neighbouring cells.

Untouched, deliberately: the prose, the deviation section, the per-boundary sections, the
`last changed` column, and the self-referential row (`_(this export)_` is a placeholder by
design; it is what stops the manifest restaling itself).

**Idempotence is pinned three ways** — `test_a_current_manifest_is_left_byte_identical`
(hermetic, whole-file), `test_running_twice_changes_nothing_the_second_time`, and
`test_the_live_manifest_converges_in_one_pass` (the real 25 rows in the two real repos, on a
copy). The live one asserts **convergence, not currency**: the manifest is *expected* to be
stale mid-cycle — that is the strict-exempt WARN class — so a test asserting the pins are
current would go red on the next `CLAUDE.md` edit and train exactly the alarm fatigue BL-009
exists to prevent. It plants a stale hash first, because over a manifest that happens to be
current `repin` writes nothing and every defect in the rewriter is invisible to a convergence
assertion.

Against the live manifest, `--dry-run` reports **25 rows, all current, manifest unchanged**.

**What it cannot tell you**, said in the script's own docstring: check 8 and this script both
establish that a pin is *current*, never that the pinned content is *complete*. That remains
`CLAUDE.md` §Definition of done's rule, and no script can discharge it.

---

## 5. W3 — the prose that duplicated the manifest

`prompts/bl-002-refresh-project-knowledge.md` carried the export set **twice**: Step 1 as a
list of source paths, Step 3 as a list of flattened export names. Both are **replaced by a
pointer at the manifest's table**, not updated — updating re-arms the trap (BL-145's ruled
shape, and this milestone's own promoted rule on enumerations).

**How stale they were, derived rather than quoted.** The ticket says "eleven rows stale"; that
figure does not reproduce. Step 3 named 12 export names against the manifest's 25 — **13
absent**; Step 1 named 11 source paths (plus one conditional fallback) — **14 of the 25 sources
absent**. Nothing in either list was *wrong*, which is the point: a stale enumeration reads as a
complete one. The replacement carries no count of its own.

Step 3 also recorded the invocation as prose — *"copy each file with a FLATTENED,
COLLISION-FREE name"* — with no command to run. It now names the real path:
`python3 scripts/assemble_export_bundle.py /tmp/claude-project-export`, and Step 2 names
`python3 scripts/repin_manifest.py`.

One addition beyond the ticket's two, and it is forced by W1b: Step 5 now requires the U2
marker's presence to be reported, and forbids printing upload instructions under it. Without
that line the prompt would tell an operator to upload everything in the directory, marker
included.

---

## 6. W4 — the tests, and the mutation matrix

**28 tests, 28 mutations, 28 RED**, the matrix re-run against the committed tree at `67b1127`
with the working tree clean before and after. Every assertion is in its own function; each was
exercised individually under a mutation that should fail it; every restore is verified with a
control on both sides — the mutant absent before the edit and present after, and each of the
three source files' sha256 identical to its pristine snapshot at the end.

Green-side control, on pristine source, before any mutation: `28 passed in 2.41s`.

Pristine sha256 (first 12): `_manifest.py 22c4bc502dd0`, `assemble_export_bundle.py
3e95d6cb17a5`, `repin_manifest.py 20237fa8d3cd` — all three identical after the last restore.

| | mutation | test it failed | raising statement |
|---|---|---|---|
| E1 | rows with no hash dropped from the parse | `…every_manifest_row_including_the_self_referential_one` | `assert sorted(_bundle_docs(dest)) == [` |
| E2 | read the working tree instead of `git show` | `…committed_history_not_the_working_tree` | `assert (dest / name).read_bytes() == expected` |
| E3 | export name derived from the path basename | `…names_come_from_the_manifest_not_from_the_path` | `assert (dest / "renamed-brief.md").exists()` |
| E4 | dirty-manifest warning disabled | `…uncommitted_manifest_edit_bundles_the_committed_copy` | `assert "has uncommitted edits" in capsys.readouterr().out` |
| E5 | duplicate-name guard disabled | `…duplicate_export_name_is_refused…` | `assert (` |
| E6 | `git show` failure returns `b""` | `…missing_from_history_writes_no_partial_bundle` | `assert (` |
| E7 | non-empty destination not refused | `…non_empty_destination_is_refused_and_left_untouched` | `assert _assemble(bundle_world, dest) == 1` |
| E8 | `--replace` empties the directory instead of moving it | `…moves_the_previous_bundle_aside_and_deletes_nothing` | `assert aside.is_dir()` |
| E9 | aside name fixed at `.superseded.1`, prior one removed | `…second_replace_does_not_overwrite_the_first_aside` | `assert (dest.with_name("out.superseded.1") / …).read…` |
| E10 | refusal keyed on existence rather than content | `…empty_existing_destination_is_accepted` | `assert _assemble(bundle_world, dest) == 0` |
| E11 | marker write removed | `…unswept_bundle_says_so_in_the_bundle` | `assert marker.exists()` |
| E12 | marker written even after a clean sweep | `…clean_sweep_writes_no_marker` | `assert not (dest / …MARKER_NAME).exists()` |
| E13 | sweep made case-sensitive | `…needle_in_the_bundle_fails_the_run_and_marks_it` | `assert _assemble(…, needles_file=needles) == 1` |
| E14 | empty needle file accepted | `…empty_needles_file_is_refused…` | `assert _assemble(…, needles_file=needles) == 1` |
| E15 | a timestamp added to the marker's head line | `…two_runs_into_two_directories_are_byte_identical` | `assert {p.name: p.read_bytes() for p in a.iterdir()} == {` |
| E16 | last byte dropped from every source | `…live_bundle_reproduces_every_manifest_row_at_head` | `assert (dest / row.export_name).read_bytes() == git_show(` |
| R1 | pin read from repo HEAD instead of the path's history | `…current_manifest_is_left_byte_identical` | `assert manifest.read_bytes() == before` |
| R2 | rewritten cell padded with a second space | `…running_twice_changes_nothing_the_second_time` | `assert _repin(repin_world) == 0` |
| R3 | the cell replacement made a no-op | `…stale_row_is_repinned_to_what_git_log_returns` | `assert f"\| \`agents--CLAUDE.md\` \| … \`{new…` |
| R4 | `-- <path>` dropped from `git log` | `…row_pins_its_own_paths_history_not_the_repos_head` | `assert f"\`{hashes['agents--CLAUDE.md']}\`" in text` |
| R5 | every row read in the agents repo | `…harness_row_is_read_in_the_harness_repo` | `assert _repin(repin_world) == 0` |
| R6 | the `last changed` cell rewritten too | `…only_the_commit_cell_changes` | `assert [i for i, (b, a) in enumerate(zip(…))] == [4]` |
| R7 | self-referential row not skipped | `…self_referential_row_keeps_its_placeholder` | `assert _repin(repin_world) == 0` |
| R8 | parse continues past the end of the table | `…per_boundary_prose_table_is_not_rewritten` | `assert _repin(repin_world) == 0` |
| R9 | `--dry-run` writes anyway | `…dry_run_reports_the_move_and_writes_nothing` | `assert manifest.read_bytes() == before` |
| R10 | undeterminable rows no longer block the write | `…underivable_row_writes_nothing_at_all` | `assert _repin(repin_world) == 1` |
| R11 | an unparseable row skipped instead of raised | `…malformed_row_is_a_failure_not_a_skip` | `assert _repin(repin_world) == 1` |
| R12 | a newline appended on every write | `…live_manifest_converges_in_one_pass` | `assert copy.read_text(…) == settled` |

**Three rows are caught by an exit code rather than by the assertion they were written for**
(R7, R8, and E5/E6's `assert (`-wrapped exit-code checks): their mutants make the run fail
before the containment assertion is reached. They are named as what they are rather than counted
as containment failures — the same call m6 t3's matrix made for its two `KeyError` rows.

**One mutant survived on the first pass, and it is the finding worth keeping.** E4 —
`test_an_uncommitted_manifest_edit…` — passed with the warning it names deleted. The assertion
was `"uncommitted" in capsys.readouterr().out`, and `tmp_path` is named after the test, so the
destination path the run prints (`…/test_an_uncommitted_manifest_edit0/out`) contained the
needle. **The assertion had never once been executed against the thing it claimed to check**,
and it read as coverage. Narrowed to `"has uncommitted edits"`, which the path cannot supply;
RED thereafter. This is m6 t2's M10 in another costume, and it was found only by running the
mutation rather than by reading the test.

**A second mutant survived when the matrix was re-run against the committed tree, and the
reason is worth more than the fix.** E16's first mutant read the sources at `HEAD~1`. That was
RED before the commit — `e3cf24d` had moved an exported document — and **went inert the moment
the ticket's own second commit landed**, because that commit touches only an
implementation-notes file, which is not in the export set: at that HEAD every exported document
is identical at `HEAD` and `HEAD~1`, so the mutant changed nothing. A mutant whose bite depends
on what the repo's last commit happened to contain is not a mutant, it is a coincidence, and it
would have reported coverage forever after. Replaced with a code-intrinsic one — the assembler
drops the last byte of each source — which cannot go quiet. Note also what did *not* work: a
mutant inside `_manifest.git_show` is invisible here, because the test computes its expected
value through the same helper and both sides move together.

**One setup was refused by its own control**, correctly: R3's first mutant was
`lines[…] = line`, which is a *prefix* of the original `lines[…] = line.replace(old_cell,
new_cell)`, so the "mutant absent beforehand" control counted 1 and refused the row. Replaced
with `line + ""`.

Two fixtures were strengthened when the matrix showed they could hide a mutation: the repin
fixture now takes **a later unrelated commit in each repo** (without it, repo HEAD and the
pinned path's last commit are the same hash and R1/R4's class is invisible) and **commits the
manifest inside the agents repo**, as the real one is.

---

## 7. Done-check

```
$ python3 -m pytest cloudcost/tests/ -q
465 passed in 156.35s (0:02:36)

$ python3 -m pytest tests/ -q
157 passed, 7 xfailed in 3.78s
```

Both scopes, on BL-152's ground: the repo-root `python3 -m pytest -q` collects nothing, so the
whole-suite gate is these two invocations. The 7 xfails are pre-existing and strict
(`test_tools_manifests.py` — BL-087, BL-089).

**The reproduction, both comparisons, run against the committed assembler at `5dae22b`.**

```
bundle built at: agents 5dae22b / aetheris d19f4b6
exported sources moved since agents 4d33048 / aetheris d19f4b6: 2
   aetheris-agents--CLAUDE.md      (aetheris-agents:CLAUDE.md)
   project-knowledge-manifest.md   (aetheris-agents:docs/project-knowledge-manifest.md)

A. moved sources vs `git show HEAD:<path>`         : 2/2 identical
B. unmoved sources vs the preserved 4d33048 bundle : 23/23 byte-identical
   accounted: 25 of 25 rows; unchecked: 0
   mismatches: none
```

**The moved list is two here and was one at gate (iv), and the difference is this ticket's own
commit.** At `e3cf24d` exactly one exported source had moved since `4d33048`
(`docs/project-knowledge-manifest.md`); `5dae22b` adds `CLAUDE.md` (§1(ii)'s pointer paragraph).
Both are stated rather than one of them quietly replacing the other.

A first pass of this comparison keyed the moved set on the repo *path* alone and reported 3
movers — `CLAUDE.md` is the path of **two** rows, the agents one and the harness one, and the
harness row was swept into the moved bucket where it did not belong. It compared clean either
way (that row is identical at `HEAD` and in the preserved bundle), so the arithmetic was right
and the classification was wrong. Re-run keyed on `(repo, path)`, which is what the figures
above are. Recorded because a check whose own classifier is loose is the shape that hides a real
mismatch behind a passing total.

Every one of the 25 rows is accounted for in one comparison or the other; nothing is left
unchecked.

**Determinism.**

```
$ python3 scripts/assemble_export_bundle.py <fresh-1> ; python3 scripts/assemble_export_bundle.py <fresh-2>
$ diff -rq <fresh-1> <fresh-2>
no differences
```

**`drift_check.py --strict`, pre-commit: 8 PASS / 0 FAIL / 1 WARN / 7 INFO, exit 0**, the WARN
being `CLAUDE.md has uncommitted working-tree changes` — the check saying it cannot answer yet.
**Post-commit at `5dae22b`, which is the meaningful run (BL-034/BL-025): 8 PASS / 0 FAIL / 1
WARN / 7 INFO, exit 0**, the WARN now
`project_knowledge: CLAUDE.md stale — manifest=4d33048 current=5dae22b`. That is the
strict-exempt manifest-staleness class, named rather than chased: mid-cycle staleness is
expected truth and clears at an export boundary, which this ticket is not. The 7 INFO are the
standing env-var and payload-field notes.

**`repin_manifest.py --dry-run` post-commit** reports the same single row —
`aetheris-agents--CLAUDE.md 4d33048 -> 5dae22b`, *would be re-pinned, nothing written* — and
leaves the tree clean. The two independent derivations of what this commit staled agree.

---

## 8. SURPRISES

**`CLAUDE.md`'s export rule and the manifest's ruling now contradict each other, and this ticket
does not touch either.** `CLAUDE.md` §Definition of done carries *"Export is
remove-all-upload-all against the full manifest set, never a hash-driven diff"* as a standing
rule. The manifest's 2026-08-12 deviation block, ruled 2026-08-14, says the opposite:
*"Remove-all-upload-all is not performed, and must not be"* — the store holds documents the
manifest cannot describe, so the remove half would delete them silently. Both are live text in
two exported documents. It is BL-143's ground (the replaced condition it poses is exactly this),
and the pointer paragraph added to `CLAUDE.md` says so rather than restating either rule.

**The assembler's own copy of the manifest can differ from the manifest that drove the run.**
The table is read from the path given (working tree); the document is bundled from `HEAD`. That
is right — a bundle carries committed documents — and it is precisely what the 2026-08-14
boundary shipped and had to explain afterwards. The script now says it at assembly time, and
`test_an_uncommitted_manifest_edit_bundles_the_committed_copy_and_says_so` pins both halves.

---

## 9. UNREAD

- The Claude.ai project store. Nothing in this repo can see it; the assembler makes no claim
  about what it holds, and neither do these notes.
- `rig/` and the harness's `sprint.sh` beyond the two case blocks cited in §1(ii).
- The check-1/check-3 contradiction in `prompts/bl-002-refresh-project-knowledge.md`
  §Post-upload verification — read, deliberately not touched, BL-143's.
