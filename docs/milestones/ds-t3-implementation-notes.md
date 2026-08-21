# ds t3 — BL-161, the deferred sprint arm (implementation notes)

Two commits, harness first: harness `d648aa8` (parent `a6464f4`) and this one. Baseline
was agents `3129521` and harness `a6464f4`, both clean and both level with `origin/main`
(`git rev-list --left-right --count origin/main...HEAD` → `0  0` in each).

Stage 1's derivation packet lived in a session scratchpad this session cannot open.
Nothing was inherited: every claim the prompt marked CARRIED was re-run here, and the
four that came back wrong are named in §6 below.

---

## 1. Criterion 5's instrument — was the GitHub Project consulted?

**NO.**

No `gh project` command was run at any point in this ticket, and no decision here was
taken by consulting the Project. `gh issue view 85` was run for the verdict-B re-sync;
that reads an issue, not the Project.

**That is five consecutive tickets — ds t0, ds t1a, ds t1b, ds t2, ds t3 — answering
`no`**, verified by opening each one's notes rather than recalled: `ds-t0` §Trial verdict A
(*"No. It was not consulted, for anything."*), `ds-t1a` §1, `ds-t1b` §1, `ds-t2` §Criterion 5
(*"Not consulted."*), and this. **Every ticket in the cycle, with no exception.** The
accumulation is the evidence verdict A asks for: an empty consulted-list beside a
non-empty kept-current list. A consultation staged for the record would destroy the
answer rather than improve it.

---

## 2. Criterion 8 is a disjunction over what was built as a conjunction

**Recorded, not fixed.** No close criterion is edited by this ticket.

Criterion 8 reads: *"If neither runs, the close states that the cross-repo arm was never
exercised and that the trial says nothing about it."* The t3 section says the pair was
built for more than that: *"Between them they exercise both sides of the Project's
cross-repo claim and both arms of the filing tiebreak; close criterion 8 depends on at
least one running."*

Those are different tests. The pair is a **conjunction** — one arm each, and the tiebreak
is only exercised if both run. The criterion is a **disjunction** — it fires only when the
count reaches zero. A cycle in which exactly one arm ran would satisfy the criterion while
leaving the tiebreak half-exercised, and the criterion would report clean in that state.
It is the same shape as the defect recorded under `## Learning — BL-152` in `CLAUDE.md`: a
criterion that returns a well-formed verdict on every input and the wrong one on the
population that motivated it.

**Why it is not edited.** The t3 section's own third paragraph rejects BL-153 for this
slot *"precisely because taking it would have required reversing the not-changed ruling on
its arm ordering, which would be a change made to get past a test."* Editing a close
criterion during the cycle it governs is that move applied to the test itself.

### Which arms actually ran

| arm | ticket | issue | ran? |
|---|---|---|---|
| harness-side primary → issue filed in the harness repo | **t3** (this ticket) | `vishal-h/aetheris#85` | **yes** |
| cross-repo with an agents-side primary → issue filed in the agents repo | **t1b** | `vishal-h/aetheris-agents#77` | **yes** |

**Both ran, so the criterion is satisfied on the facts.** It is satisfied for a reason
weaker than the one the pair was built to supply, and that is the point of §2.

A consequence worth naming, because it is what makes the two arms real rather than
cosmetic: t3's commit message writes a **bare `#85`**, and t1b's harness commit writes
`vishal-h/aetheris-agents#77` **in full**. A bare `#n` resolves against the repository the
commit is in. t3's subject is in the harness and its issue is in the harness, so bare is
correct; t1b's harness commit had to reach an agents-repo issue, so bare would have
resolved to a different object.

---

## 3. The arm

`../aetheris/scripts/sprint.sh`, target `export_mechanism`, placed immediately after
`drift_check`'s `fi` — beside the two comparators BL-161 names. Boundaries resolved at
harness `a6464f4` rather than carried: `capability_matrix` at `:1549-1608` and
`drift_check` at `:1610-1634`. The insert begins at the old `:1636` and is far below
`sprint.sh:1006`, which `scripts/run_record.py:65` and
`tests/test_run_record_adoption.py:161` both cite by line number for payslip's `rm -rf`;
that line is unmoved.

**Six assertions, every one through a command line.** That is the whole of branch 1: both
scripts end in `if __name__ == "__main__": sys.exit(main())`, and the 37 tests across
`tests/test_export_bundle.py` and `tests/test_repin_manifest.py` contain **zero**
occurrences of `main(` — their only subprocess helper runs `git`. So the entry point, the
argument parser, the flag translation and the propagation of `main()`'s return into a
process exit code were exercised by nothing.

The two exit-1 assertions are the ones an imported-function call could not make: they
observe the **process exit code**, not a return value.

**It never writes a tracked file.** `repin_manifest.py` runs under `--dry-run`, which
returns before the single `write_text` in the script, and the manifest's sha256 is
compared across the run rather than assumed. The bundle goes to a `mktemp -d` destination
the arm creates and removes, under a trap set and cleared inside the block —
`playground_api`'s EXIT trap is set later in the file, so the two never overlap.

**It is not promoted.** Every assertion uses `fail`. R7 makes promotion per-arm and
requires the promoting ticket's own verification on the record; this ticket creates the
arm. The arm's comment says so, and the sprint's own counters show it: under the mutation
below, `reds NOT YET DECLARED` was `1` and `blocking failures` `0`, exit 0.

**It is in `all`,** on the reason written into the arm: it needs no credential, no
network, no LLM and no writable tracked path — `drift_check`'s profile, which is in `all`
too. An arm outside `all` runs when someone remembers it, which is the shape BL-161 was
filed about.

### The mutation control

Mutating `sys.exit(main())` to `main()` in `scripts/repin_manifest.py`:

- `python3 -m pytest -q tests/test_export_bundle.py tests/test_repin_manifest.py` →
  **`37 passed`**, exit 0. The existing tests do not notice.
- `./scripts/sprint.sh export_mechanism` → `[FAIL] repin_manifest.py returned 0 for an
  unreadable --manifest — the CLI is not propagating main()'s exit code`.

That is the coverage gap demonstrated rather than argued. Restored from a sha256-verified
working-copy backup — never `git checkout --`, which would restore to HEAD and silently
discard uncommitted work — and verified three ways: sha against the backup,
`git status --porcelain` empty, and the construct present again. The arm was re-run and
returned to six green.

---

## 4. BL-161's disposition, and the half of branch 1 that could not be performed

Branch 1 reads *"the sprint arm exists and is named in a boundary record"*. In this
repository a **boundary record** is a dated entry in
`docs/project-knowledge-manifest.md`'s export-boundary log; ds t3 runs no export boundary,
so no such entry can honestly be written here.

The naming landed in `CLAUDE.md` §Definition of done instead, in the paragraph that
already carries the mechanism's pointer and its `Tests:` line. That is where branch 2
places *its* outcome, on the stated ground that a reader of that pointer will meet it, and
it is the surface the next boundary record's author reads.

**This is a substitution of surface and is the arbiter's to accept or reverse.** The row
is marked DONE rather than held open because what remained was a naming with no executor
and no trigger — the precise failure BL-161 was filed about.

**The row's `Collides with` clause is superseded**, per §A4 of the ticket. It said closing
branch 1 was *"naturally part of BL-143's work"*; BL-143's scope note of 2026-08-16
refuses that routing in terms, and its Done-when — ownership and trigger — is *"unchanged
and open"*. BL-143 is untouched.

**The move.** BL-161 owns exactly one section; it carries `**Status:** DONE` and travelled
to `docs/backlog-2026-06-closed.md`. The invariants relied on were read from the archive's
own header rather than remembered: a row is there **iff** its title section carries
`**Status:** DONE`; every section an id owns travels with it; the id is the address and
the path is never load-bearing; `## ` container headings are the only non-verbatim lines.
BL-161 sits past the retired `## Suggested order` table in the open file's appended tail,
so it reproduces no container heading, matching the archive's own tail.

---

## 5. Filings

| where | what |
|---|---|
| **BL-151** (append) | Two of the split's four published invariants have no keeper; both broken states derived, with a positive control. **No fix** — the row holds where the check belongs. |
| **BL-151** (append) | provenance's `run_record` adoption is verified by AST parse only, and nothing schedules the execution that would verify it — a second ds t2 deferral naming its own missing executor. |
| **BL-150** (append) | The dormant set is off-territory by **cost**, a different mechanism from the gate rule's other cases; its contents are reachable and only the whole-set run is not. |
| **BL-150** (append) | Four surfaces declare the harness gate set and no two agree; the differences published. |
| **BL-169** (new) | `mix hex.audit` is a declared merge gate that no workflow runs. Out of ds scope; filed, not fixed. |
| **BL-170** (new) | The concurrency detector is probabilistic — 15/20 with the lock disabled — so a single green is not evidence the lock is present. |

**A seventh landed in commit 3**, after the gate run: **BL-171**, `mix hex.audit` red on two
bandit advisories. It is not in the table above because it is not commit 2's, and §8 below
is its record.

Six in commit 2, not the five the ticket named. The extra is the second BL-151 append: it is the same
class as BL-170 and it names its own missing executor in the same file, so leaving it
would have reproduced this ticket's own subject one document over. It went to BL-151
rather than to a row of its own because it is a coverage gap with a small fix, which is
BL-151's stated class.

**One thing the filings could not say literally.** BL-151's positive control describes
appending a well-formed dangling `BL-nnn` and omits the literal id, because
`docs/backlog-2026-06.md` is inside `backlog_resolution`'s own corpus — writing the id
would fail the check the sentence describes. `drift_check.py`'s allowlist comment records
the same self-reference about itself. The alternative was to add an allowlist entry, which
would have been a mechanism edit made to accommodate this prose.

---

## 6. Corrections — four CARRIED claims were wrong, and one document falsified itself

These go here and not only in the packet.

1. **"no sprint arm today writes a tracked file" — FALSE.** The `capability_matrix` arm
   runs `python3 ../aetheris-agents/scripts/assemble_matrix.py` with no `--output`, and
   that script's default `OUTPUT_MD` (`scripts/assemble_matrix.py:49`) is
   `docs/capability-matrix.md`, which `git ls-files` reports tracked. That arm is in `all`.
   The design rule the claim was offered to support is unaffected and was applied: **this**
   arm writes no tracked file. Only the justification was false, and it is not repeated in
   the arm's comment, which states the property of this arm and names the counter-example.

2. **"review packets are not committed in either repository" — FALSE.**
   `git ls-files | grep -i packet` returns **five** committed packets in the agents repo,
   all under `docs/reviews/`, and **zero** in the harness. Separately, `docs/reviews/` is
   tracked in both (22 files harness, 81 agents), though those are review files rather than
   packets. The default is uncommitted and the narrow claim holds for the packets the rule
   in `CLAUDE.md` rests on — so that sentence was **narrowed** rather than deleted, and the
   BL-150 filing states the narrow form.

3. **The `Source:` anchor for BL-159 is `:6098-6099`, not `:6096-6097`.** Within the
   prompt's "about", and recorded because line citations in this cycle have decayed twice.

4. **The positive control in `CLAUDE.md` returned a different figure than it claims.**
   `git grep -inE '52m21s|10m17s' -- '*.md'` returns **12 lines across 5 files**, not
   *"8 lines across 4 files"*. Not corrected to 12: **de-numeralised**, because the
   population grows every time a document quotes those figures, and a corrected number
   re-arms the same trap for the next quoter — `CLAUDE.md` §Learning — m6-cloudcost.

5. **A `CLAUDE.md` claim was self-falsifying in its own commit.** The same `Source:` block
   asserted that `git grep -inE '82%|63%|1h50|19m58|150k' -- '*.md'` *"returns 0"*. It
   returns three hits, **all inside `CLAUDE.md`**, one of them the line making the claim.
   Restated rather than narrowed-to-hide: the search is not restricted to exclude that file;
   the claim is restricted to what the search actually establishes.

### Corrections landed on the three superseded surfaces named by the ticket

- **`pytest.ini`** — *"did not finish under either of two caps"* replaced. Neither run was
  ended by its cap; both were ended by hand and the first outlived its own 2700s SIGTERM.
- **`docs/backlog-2026-06.md` BL-159** — *"Two capped runs"* at the claim, and *"the two
  capped runs … recorded per the cap correction that a cap-kill is a complete result"* in
  its `Source:`. The second was the worse of the two: it invoked the cap-kill rule over
  runs that were not cap-killed. Both replaced; `grep -n "capped runs"` now returns nothing.
- **agents `CLAUDE.md`** — items 4 and 5 above, plus item 2 as a fourth instance of the same
  class found in the same file.

---

## 7. A committed example of the run record's format

`payslip/data/run-records.json.example`, and `scripts/run_record.py`'s module docstring now
names it.

**Why it was missing.** The schema is prose in three `.md` files and code in
`scripts/run_record.py` and `tests/test_run_record.py`, and the real file is gitignored in
every use case that writes one (`docbuilder/data/.gitignore`, `eduloka/.gitignore`,
`payslip/.gitignore`, `provenance/.gitignore`), so no committed file held a rendered
instance and a reader had nothing to check an implementation against.

**The convention, and where it came from.** `<real filename>.example`, committed beside the
gitignored file it exemplifies — taken from **`email/data/smtp.cfg.example`**, whose first
line is *"Copy to smtp.cfg and fill in real values. smtp.cfg is gitignored."* The same
suffix is used by `.env.example` and `provenance/agents/taxonomy.md.example`. JSON carries
no comment, so the pointer lives in `run_record.py`'s docstring instead of in the file.

**It is produced, not typed.** The two entries were written by `run_record` itself against
a real committed artifact, and both facts in the artifact block are reproducible:
`sha256sum payslip/data/sample_payroll.csv` →
`dc332309c31c544ce51fe79af0b26f0e34377483f8845cbfeb742f3b15c9afbc`, and
`stat -c%s` → `842`. It shows **both** states the schema encodes — one attested step, and
one opened and never attested, which is the interrupted-step state the module's docstring
says the format exists to make visible.

**The residue, stated rather than left.** Those two values are a second surface: if
`payslip/data/sample_payroll.csv` ever changes, the example goes stale and nothing checks
it. The two commands above are the check, and they are written here so a reader has them.

---

## 8. A third commit, and why

**The ticket said two commits. There are three, and the third is `BL-171`.**

The ticket-boundary gate run found `mix hex.audit` **red**: bandit 1.12.4 carries
EEF-CVE-2026-75484 (MEDIUM) and EEF-CVE-2026-74836 (HIGH). Neither is BL-060's advisory —
that row is DONE and its subject was bandit 1.11.1 / EEF-CVE-2026-65623 — and no open row
named `bandit` or `hex.audit` before this one. `CLAUDE.md` §Definition of done is explicit:
*"A red gate gets a tracked ticket the day it's found — never carried silently"*, and
§Learning — BL-007 is equally explicit that *"prose in a packet or notes files nothing"*.
So the red had to become a row, and a row is a commit.

**Why not an amendment to commit 2.** By the time the gate ran, the verdict-B re-sync had
already published `f003e4a` to `vishal-h/aetheris#85` as that issue's backlink. `CLAUDE.md`
§Definition of done: amend while a commit is private and uncited, **append** once something
cites it. Amending would have left a published backlink pointing at a tree that never
existed. The backlink is excluded from verdict B by construction, and commit 3 does not
touch `ds-milestone.md`, so the comparison is unaffected.

**The deviation is the arbiter's to accept.** The two-commit instruction is a ticket-shape
instruction; the red-gate rule is standing. Where they conflicted, the standing rule was
followed and the conflict is named here rather than resolved silently.

**It is also BL-169 arriving as an instance rather than an argument.** BL-169 was filed
earlier the same day from a static census: `mix hex.audit` is a declared merge gate that no
workflow runs. This red was found only because a human-directed ticket-boundary run typed
the command; nothing in CI would have reported it.

**No bump was made.** `mix hex.info bandit` reports 1.12.5 (2026-08-20) against a locked
1.12.4, and `mix.exs:30` already admits it — but whether 1.12.5 fixes both CVEs was
inferred from a release date, not read, and a dependency change belongs to a ticket that
can run the full harness gate set against it.

---

## 9. The dormant set was run, and something other than its cap ended it

Recorded here and not only in the packet, because **what ended a run is the fact the cap
rule says a later session will otherwise trust wrongly.**

```
$ timeout 2400 python3 -m pytest -q -m dormant          # agents df659e8
................................................................F....... [ 34%]
................F....................................................... [ 68%]
...........
```

**It did not hit its cap.** The cap was 2400s; the run was **killed by the session harness
at 1470s**, well inside it, and reported `[killed]` rather than a `timeout` exit. So this
is not a cap-kill and must not be recorded as one — it is the same distinction the cap
rule's own example was corrected for at ds t2 stage 4, arriving as a fresh instance in the
opposite direction: there a run *outlived* its SIGTERM, here a run was ended *before* its
cap by something the cap does not describe.

**What it did emit.** `python3 -m pytest -q -m dormant --collect-only` reports **211**
tests collected. The partial output above carries **155 results — 153 passes and 2
failures** — so the run reached roughly 73% and stopped. **Neither failure is identified**:
`-q` names a failing test only in the summary, and the summary never printed.

**This corroborates BL-159 and identifies nothing.** That row already states that one test
is red deliberately and that a second failure exists and is not identified; two `F` marks
at 73% is consistent with exactly that and adds no name to either. A dated observation is
appended to BL-159 rather than kept here alone, so a reader of that row meets it.

**It also sharpens the BL-150 filing made earlier the same day.** That entry says the
dormant set is off-territory by **cost**. This run is the demonstration: 24.5 minutes of
wall clock bought 73% of a set and zero identified failures, and no session cap in use here
reaches the roughly four hours BL-159 projects.

**Not retried with a longer cap**, per the standing rule. The result above is the result.

---

## 10. Gates and the WARN prediction

In the packet, with exit codes. The WARN prediction was derived as a **set** before the run
and is reproduced there: the manifest was read by `(repo, path)`, intersected with both
commits' touched paths, and the answer was that **this commit introduces no new
`project_knowledge` WARN** — `CLAUDE.md` and `docs/backlog-2026-06.md` were already stale
at `43e63e0` and `6436b25` against `3129521` and `c8aa4e3` before either commit, so their
WARNs are standing, not introduced. Nothing was re-pinned.
