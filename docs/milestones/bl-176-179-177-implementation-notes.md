# BL-176 / BL-179 / BL-177 — implementation notes

**Date:** 2026-08-23. **A batch, not a cycle** — no census, no new instrument, no new row.
**Commits:** harness `82a12cd` (BL-176), `0783e3f` (BL-179), `9b76009` (BL-177); agents, the commit
carrying this file.
**Baseline:** harness `77ab709`, agents `22ac9f5`, both clean and level with `origin/main`.
**Not pushed.** All three harness commits and this one are local at the time of writing.

---

## 1. What the batch is

Three harness rows filed at BL-174 stage 2, all config and tree hygiene. Two of them — BL-179 and
BL-177 — change what CI caches, which is why they share one run and why the cold-run expectation is
published as one prediction across both (§4).

They also turn out to be less independent than their filings suggest. **BL-176 and BL-177 are one
fact seen twice:** the escript BL-176 removes bundles `rustler`, and the lock entry BL-177 removes
resolves `rustler`. Both are residue of `e977af0` (2026-05-20), the commit that deleted the NIF
crate. Neither row noticed the other; the connection surfaced only when the removed binary was run
and its application shutdown listed `rustler` among the applications it stopped.

---

## 2. BL-176 — the reference search is the ticket

The ruling (remove) came in the prompt. The work was **the check that could have stopped it**, and
it is the part worth reading.

### 2a. The search, and a defect in it

The first two attempts were wrong and both were caught by their own output being absurd:

1. `git grep -n -- './aetheris'` — `git grep` is a **regex** by default, so `.` is a wildcard and
   the pattern matched every `../aetheris-agents/` in either tree. ~988KB of output.
2. `git grep -n -F -- './aetheris'` — fixed-string, and still wrong for a reason worth recording:
   **`../aetheris-agents/` literally contains the substring `./aetheris`.** ~587KB.

The working form is `git grep -n -P -- '(^|[^.])\./aetheris'` — the dot not preceded by another
dot. This is a small instance of a large class in this repo: a recorded command that does not mean
what its author intended, which is **BL-182**'s subject, and **BL-180**'s worked example is a
`grep -nE` whose escapes were eaten by Markdown so that `\.\./aetheris` rendered as
`../aetheris`. The same two characters, the same failure, from the other direction.

### 2b. What it found

Five live sites, repointed in `82a12cd`; everything else a frozen record. The full disposition is
in the row, now in `docs/backlog-2026-06-closed.md`. The judgement that carries risk is this one:

> **The Done-when's "a document you may not edit" case WAS reached, and was answered rather than
> treated as a blocker.**

Roughly a dozen hits sit in `runbook-m11.md`, `runbook-m12.md`, the m08 milestone docs, five review
files and various backlog rows. Read literally, "stop and report rather than remove" could have
stopped the row. It did not, because this repo declares the class in its own words, twice, and both
statements are about instruction-status rather than about editability:

- `.github/copilot-instructions.md:24-31` — *"that document is a record and not an instruction to
  you"*, explicitly covering *"every dated record in the repository, wherever it sits"*.
- `docs/aetheris/runbook.md:6-25` — the three runbook categories **enumerated, not
  pattern-matched**, with `runbook-m11.md` and `runbook-m12.md` in the never-retro-updated list and
  `runbook.md` canonical.

So the removal breaks no instruction, and no record was edited. **If a later reader thinks that
reading was wrong, this paragraph is the thing to argue with** — it is the only step in the batch
where a stop condition was met on the letter and declined on the reasoning.

### 2c. The staleness, demonstrated

The row asserted the binary "runs May's code silently". That was a hypothesis; it is now an
observation, and the route to it is not the obvious one.

Run bare, the escript does not start: the exqlite NIF fails to load and it exits 1 before
dispatching anything. That looks like a clean answer — *nobody could have been relying on it* — and
it is **wrong**, which is why it is recorded. The frozen m11/m12 runbooks document a workaround,
`ERL_LIBS=_build/dev/lib`, and **under it the binary works**:

```
$ ERL_LIBS="_build/dev/lib" ./aetheris list --limit 2
Type  ID          Label  Status  Started
run   run_ORIURw         failed  2026-08-22T03:07:12.562037Z
run   run_wsj6pg         failed  2026-08-20T14:38:02.844643Z
EXIT=0
```

`ERL_LIBS` supplies current **deps**; the escript's own archive supplies `aetheris`. So it ran, and
ran the wrong CLI. Its `--help` lists neither `schedule` nor `server`:

```
$ ERL_LIBS="_build/dev/lib" ./aetheris server --help
Error: unknown command: server
EXIT=1
```

`server` was added at `be43092` (2026-05-21) and `schedule` at `f018b5f` (2026-05-20); both
dispatch in the current `lib/aetheris/cli/main.ex`. **A working binary that silently answers "no
such command" for a command that exists is a worse artifact than a broken one**, and it is the
strongest available argument for the ruling — stronger than the file's age, which is all the row
had.

### 2d. What is owed: nothing, and that is stated

No gate observes this file's disappearance and **none was added**. `ci.yml`, `sprint.sh`,
`drift_check.py` and the harness seven do not read it — checked, with a control, in the closed row.
A gate asserting the absence of a build output is a rebuild trigger by another name, which is the
branch the ruling declined.

---

## 3. BL-179 — enumerate all four, not the two in the annotation

`runs.using` read from each action's own `action.yml` at the pinned ref via the GitHub contents
API. Two of the four never needed a bump: `erlef/setup-beam@v1` **already declares `node24`**, and
`dtolnay/rust-toolchain@stable` is a **composite** action with no Node runtime at all. Had the row
been worked from the annotation text alone, both would have been bumped or investigated for
nothing.

**The corroboration is the part to reuse.** The census is a claim about which actions can annotate;
the annotation's own distribution in run `32611562210` is the same claim read from live data, and
they agree exactly — all 12 hits on `checkout` and `Cache *` steps and their `Post` halves, none on
the other two. That is a positive control on the census's *completeness* obtained for free, from a
log the row already cited for another purpose. **R34's new appended line is about exactly this
shape**: where a known member of the class exists, it is the control.

`gh` was bound with `-R vishal-h/aetheris` throughout, per **R33** — `gh run view` resolves the
repository from the working directory otherwise.

---

## 4. The combined cache expectation — published before the push

Both rows point the same way, so a cold run must not read as a surprise, and the prediction is
published so it can be falsified rather than described afterwards. The table is in **BL-177**'s
dated block and is not restated here.

**The one design decision worth carrying:** `check / Cache Cargo` is **left unpredicted**. Its key
does not move, so it goes cold only if the v4→v6 bump moves the derived entry *version* — and no
`actions/cache` release note between `v4.3.0` and `v6.1.0` says anything about version derivation,
compression or zstd. Predicting it cold anyway would have made the prediction unfalsifiable in the
direction that matters. Leaving it open makes it the step that **separates** the two mechanisms,
which is the only thing this run can contribute to **BL-175**.

The three certain-cold steps read the same question a second time through their `restore-keys`: a
partial restore from the prefix means the entry version did not move; a complete miss means it did.
**The two readings must agree with each other and with Cache Cargo.** A disagreement is a finding
about BL-175's mechanism and belongs in that row.

---

## 5. BL-177 — nothing surprising, recorded for the ordering

`--check-unused` exists in Elixir 1.17.2, so the set was **established before** the removal rather
than inferred from the diff after it. One entry, `:rustler`; one deleted line. `deps/rustler`
exists in the working tree, is untracked (`/deps/` is gitignored), and was left alone.

---

## 6. Gates

Harness seven, run on the tree after all three harness changes, each under an explicit cap
(`timeout 540` for the first five, `timeout 560` for dialyzer and test) — **no run hit its cap**.
All exit 0. `mix test`: `972 tests, 0 failures, 133 excluded`, 90.5s. `mix dialyzer`:
`Total errors: 0`. **BL-135 did not fire.** Full output in the packet.

Agents gates in the packet: the Python whole-suite gate, `drift_check.py --strict` **after** the
agents commit (check 8 reads committed history), and both hermetic sprint arms.

---

## 7. Defects in this session's own work

1. **Two wrong searches before the working one** (§2a). Caught by output size, not by review.
2. **A claim written before it was checked.** The BL-176 closure block asserted that
   `drift_check.py` does not read the escript; that had not been verified when written. Checked
   immediately afterwards, found true, and the row now carries the command and its control rather
   than the assertion. The gap between writing and checking was about one minute — which is the
   point: the assertion was already committed to prose and would have travelled had the check not
   been run.
3. **`mix aetheris server --help` was run and blocked to its 120s tool timeout** while establishing
   §2c. It starts a server. Not a failure of anything, and not reported as one; the escript half of
   that comparison stands on its own output.

---

## 8. What the next reader is owed

- **BL-179 and BL-177 each keep exactly one open clause, and both are the same run.** One push
  discharges both: `grep -c 'Node 20 is being deprecated'` → 0, and the four cache steps against
  §4's table. Neither row can close without it.
- **BL-176 is closed outright** and is in `docs/backlog-2026-06-closed.md`.
- **BL-178 is next** (a `cargo` gate against the two surviving crates) and was deliberately not
  touched here.
- **Not filed as a row, reported instead** — see the packet: the canonical `runbook.md` §Option C
  tells an operator to `mix escript.build` and then run `./aetheris <command>`, and the `ERL_LIBS`
  requirement that makes that work lives **only** in the two frozen m11/m12 runbooks. Removing the
  committed binary makes §Option C the only path to an escript, so the canonical document is now
  the sole instruction for a procedure whose missing half is recorded only in files this repo says
  are not instructions.
