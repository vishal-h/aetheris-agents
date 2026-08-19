# ds t1b — the backlog split (implementation notes)

Two commits, harness first: harness `a6464f4` (parent `8eb960d`) and this one.
Stage 1's derivation packet was the input; nothing in it was inherited uncited —
every claim this stage rests on was re-run here, and the gate table in the review
packet records each verdict.

---

## 1. Criterion 5's instrument — was the GitHub Project consulted?

**NO.**

No `gh project` command was run at any point in this ticket. No decision here was
taken by consulting the Project. `gh issue view 77` and `gh issue view 75` were run,
because the two re-syncs need the issue bodies; those read issues, not the Project.

**That is now three consecutive tickets — ds t0, ds t1a, ds t1b — answering `no`, and
the accumulation is the evidence.** Verdict A's failure condition is an empty
consulted-list beside a non-empty kept-current list; three honest `no`s are three data
points toward settling it, and a consultation staged for the record would destroy the
answer rather than improve it. The instrument is working as designed: it is producing
a legible negative rather than a default "no finding".

---

## 2. What decided each row's side, and why the key is the field

The unit is the **id**; the key is `**Status:** DONE` on the **title** section; every
section an id owns travels with it; `UNRULED` stays.

The key matters because two surfaces disagree. **BL-047** and **BL-048** carry
`**Status:** UNRULED` on their titles and own closure sections whose *headings* read
`— DONE (impl) …` and `— DONE (pending first CI dispatch) …`. A split keyed on the
heading word archives those two closure sections and strands their titles; a split
keyed on the field moves neither. They are the only two rows in the file where the
surfaces disagree, and they are exactly why t0 minted the field.

Adjacency could not have been the mechanism either. **5 of the 20 ids that own closure
sections carry that closure BEFORE their title** — BL-047, BL-048, and BL-050 / BL-055
/ BL-056, which share one closure section sitting 52, 102 and 630 lines above their
three separate titles. *"The closure section is the one following the title"* is false
for a quarter of the population, so the pair is resolved by id, by the parser, or not
at all.

---

## 3. The multi-id rule has no instance, and is asserted in both directions anyway

`### BL-050 + BL-055 + BL-056 — DONE 2026-07-25 (one reorder, three rows)` is the only
multi-id section in the file, and **all three owners are terminal**, so it moves. Had
any one been non-terminal, the section could not move without either splitting it or
dragging a live row's record into the archive.

The rule is therefore: **a section owned by more than one id moves only if every owner
is terminal; otherwise it stays in the open file and each archived owner carries a
one-line pointer to it.** No instance exists, which is precisely the condition under
which a rule ends up correct by coincidence — `CLAUDE.md`'s *"the one X is an
observation, not a census"*.

So the verification asserts it in both directions and the arms were exercised on a
**synthetic fixture**, because a green over a corpus with no instance proves nothing:

- a mixed-status multi-id section in the archive → the non-terminal-owner arm FAILS;
- a multi-id section whose owners are all terminal left in the open file → the
  only-terminal-owners arm FAILS;
- a mixed-status section kept in the open file **without** the pointer → FAILS;
  **with** the pointer → PASSES.

The last pair is the one that could not be exercised on real data at all. It is
recorded because a future instance must fail loudly rather than be decided by accident.

---

## 4. Container scaffolding is not owned by a row, and that took two attempts

A section's line range naively runs to the next `### BL-` heading, which swallows any
`## ` container heading that happens to sit between two rows — so the row preceding a
container would drag that container's heading into the archive with it. The generator
therefore ends a section at the structural run (`---`, blank, `## …`, blank) that
introduces a container, and routes that run to whichever file keeps the container's
rows.

Two consequences fell out, both found by looking at the output rather than by
reasoning:

- **`## Housekeeping` empties completely** — all three of its rows are DONE. Its
  scaffolding travels to the archive with them, so the open file carries no empty
  container heading and the archive needs no reproduced one. The other four containers
  with archived rows get their heading reproduced (enumerated, and subtracted by the
  invariant check).
- **The open file's inserted header must not end with `---`**, or the scaffold rule
  that follows renders as a second horizontal rule immediately after the first.

---

## 5. The check, and the two things it found about itself

`drift_check.py`'s `backlog_resolution`: every strict-form `BL-nnn` in the scoped
corpus names a row in the **union**. FAIL, never WARN — a WARN here would sit beside
the two strict-exempt `project_knowledge` staleness WARNs and inherit their
expected-truth reading, which is the one thing this check must not do.

**Scope is the two backlog files plus every `*.py` / `*.sh` in both repos.** Not the
mode bit: `git ls-files -s` records **zero** files as `100755` in aetheris-agents, so a
bit-keyed corpus would exclude every script the check exists to cover. The extension
reading is confirmed rather than assumed — under it the unresolvable population comes
out as exactly the three groups the ratified decision names (`BL-063`, `BL-999`, the
`BL-9xx` fixtures) and nothing else. `*.exs` was checked and adds nothing.

Two things the check found about its own situation, both kept explicit:

- **The split moved `BL-063`.** Before it, both occurrences sat in one file and one
  allowlist key covered them; after it, one is in the open file's retired
  `## Suggested order` table and one is inside BL-030's archived body. That is why the
  allowlist is keyed by **(id, file)** and not by id, and it is a small demonstration
  that the check had to be written against post-split state — the ticket's *"the check
  is the precondition, not a follow-up"*.
- **The checker is inside its own corpus.** Its allowlist excuses ids by naming them,
  so the reason strings are themselves references — *a census recorded inside the
  document it censuses*. The remedy taken is explicit self-entries rather than
  excluding the checker from its own scope; excluding it would blind the check to a
  genuinely dangling id written into it later. Same for the test file: an early draft
  used `BL-101` / `BL-102` as fixtures, which **happen to be real rows**, so the live
  arm would have passed on a coincidence. The fixtures were moved into a range no real
  row uses and allowlisted with that reason recorded.

---

## 6. What the union preserves, measured

`backlog_status.py` reads both files and merges by id. The census over the union
reproduces the pre-split figures **exactly** — 165 rows, 103 OPEN, 60 DONE, 2 UNRULED,
and the same legacy occurrence counts (19 / 191 / 11 / 4). Nothing the parser can see
changed, which is the intended result of a move keyed on the id being the address.

`--file` is now repeatable and the default is the union. A single `--file` still works
for testing one side; the **default is never one side**, because reading the open file
alone reports a real archived row as absent — a well-formed answer to the wrong
question.

---

## 7. Open, and forwarded

- **No manifest row for the archive**, by ratified decision. The consequence is that an
  uploaded backlog describes the open set and not the closed one — the manifest's one
  blind direction. Stated in the open file's own header so the gap is a documented
  property rather than a silence, and **not** filed as a row, because it is a decision
  rather than a defect.
- **The union-versus-open-file question for `sprint.sh`** is reserved to the first
  KNOWN_RED arm, recorded inside `sprint.sh`'s existing reservation block rather than
  here, so the person who writes that arm finds it beside the question already there.
- **BL-150 gained four appends and BL-133 one**, all filed in this commit. The
  `gc-stale-claims.md` append is wider than the finding stage 1 carried: eleven stale
  citations, not one.
- **`cargo check` cleared in 17.59s warm** at this ticket's gate boundary, against the
  `target/` the operator's 2026-08-19 run had left. Recorded on BL-133, because it turns
  that append's mechanism claim from an inference into a measurement — the 570s
  cap-kills were cold-build-state, not gate cost. It does **not** establish that
  `c7180a8` compiles: the run was at this HEAD, and a gate covers the tree it ran
  against.
- **t0's `154` and `2` figures** are left as t0's stamped values. Only the `448` was
  de-numeralised, and a second dated bracket records that the split moved the
  population the `169` command addresses. Re-derive over the union; do not read any of
  the three numbers in that bracket as current.
