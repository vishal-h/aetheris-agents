# BL-173 + BL-174 — implementation notes

**Landed:** harness `7ccfc6a` (one commit, four files), agents at the commit carrying this file.
**Baseline:** harness `203dec8`, agents `80de78e`, both clean and level with `origin/main`
(`git -C <repo> rev-list --left-right --count origin/main...HEAD` → `0 0` in each).
**Why one commit:** the two rows share a census member — `native/aetheris_nif/target` is a BL-173
cache path and a BL-174 census hit — and both are harness documentation-and-config edits.

---

## 1. What the census actually holds

`git -C ../aetheris grep -c 'aetheris_nif' -- .` returns hits in eleven files at `203dec8`,
confirming BL-174's figure. Positive control: the same command and flags for
`aetheris_exec_server` returns hits across the tree; negative control: a freshly minted token
(`aetheris_zzqx_nonexistent_token`) returns nothing, so the search is neither blind nor
indiscriminate.

**The triage test, written down before it was applied**, because a classification rule that is
only stated after the fact is indistinguishable from a rationalisation of what was already done:

> Does the document address a reader in the present about what to do now, or does it describe
> what a past ticket asked for at its own time?

- present-tense standing guidance, audience *whoever is working now* → **INSTRUCTION** → fixed
- a dated unit of past work, audience *that unit's reader* → **RECORD** → not edited
- a compiled binary → **ARTIFACT** → not editable
- a dated record carrying a present-tense instruction block → **BOTH** → referred, not decided

The per-surface result is the table appended to BL-174 and is not repeated here.

## 2. §E2 — the surfaces classed RECORD, by filename and line, with the test that put them there

These were read and deliberately not edited. The sweep that edits four files and says nothing
about the six it left is indistinguishable from the sweep that missed them, so:

Line numbers below are `aetheris_nif` hits at `203dec8`, resolved by
`git -C ../aetheris grep -n 'aetheris_nif' -- <file>`. **The first draft of this table carried
different numbers**, transcribed from the wider `rustler|rust nif|nif\.ex` grep rather than from
the census this row is scoped by — an inherited citation, caught by resolving each file before
publishing. The per-file totals agree with `git grep -c`.

| file | `aetheris_nif` lines at `203dec8` | why RECORD |
|---|---|---|
| `docs/aetheris/milestones/m01-core-harness.md` | 62, 63, 98, 119, 121, 122, 349, 350, 358, 370, 372, 389, 400, 401 (14) | m01's ticket document. Dated unit of past work; its audience was m01's implementer, and its instruction blocks describe what m01 was asked to build. |
| `docs/aetheris/milestones/m03-replay-diff.md` | 281, 284, 285, 301, 324, 403, 404 (7) | m03's ticket document. Same test, same answer. |
| `docs/aetheris/milestones/remove-nif.md` | 14, 26, 59, 61, 67, 85, 97, 101, 102, 123, 132, 147, 161 (13) | The ticket that performed the deletion. Editing it would erase the record of what was removed — the one document whose subject *is* the removal. |
| `docs/aetheris/milestones/remove-nif-implementation-notes.md` | 15 (1) | That ticket's own notes file. Same. |
| `docs/aetheris/milestones/milestone-reference.md` | none — `7` on the *extended* census only | The milestone index; m03's row records that m03 shipped a Rust NIF, which is true of m03. Not reachable by the `aetheris_nif` command at all. |
| `aetheris` (committed escript) | 2, in compiled data | **ARTIFACT**, not RECORD. A zip archive whose entry table holds `aetheris_nif.so`, embedded at build time (`f43c905`, 2026-05-16). No text edit reaches it. |

**Referred, not classed** — `docs/aetheris/notes-m09.md:91` and
`docs/aetheris/milestones/m10-autonomous-agent-tooling.md:868`. Both are dated records carrying a
live-shaped `cargo` instruction block. Ruling `m10` an INSTRUCTION needs a reason that does not
also reach `m01` and `m03` in the same directory; none was found, and BL-174's own Costs line
already names m10 as the ambiguous one. **This is why BL-174 does not close.**

## 3. BL-173 — two paths, two different defects

They are not the same kind of wrong, and the row reads them as one kind.

**`priv/plts` was never true.** Listed since `ci.yml`'s first commit (`0982a74`, 2026-05-15). No
commit on any branch has ever contained `plt_local_path` or `plt_file` — pickaxe over all history
returns nothing for both, against a positive control on `plt_add_apps` returning `56a79ea`. It is
the cache half of the standard dialyxir recipe whose `mix.exs` half was never written. **This
answers the Done-when's open question directly:** removing the path and removing the intent are
not different fixes, because no intent was ever recorded.

**`native/aetheris_nif/target` went stale in two steps, not one.** The row reads the deletion
(`e977af0`, 2026-05-20) as the staling event; it is the second. `190eb39`
(2026-05-17T14:43:52Z) made `native/` a cargo workspace, and a workspace member's build output
goes to the shared `native/target` — so the path stopped naming cargo's output three days before
the crate went. That is **33 minutes after** the last workflow run before this month
(`2026-05-17T14:10:29Z`, run `25993150988`; `190eb39` is not an ancestor of that run's `80a846b`).
The row's *"three days after the last CI run"* is right about the deletion and understates how
fast the declaration went wrong.

**`native/target` was not added.** In scope terms this row is about declarations that name
nothing; caching real build output is a performance change owing its own measurement. The
omission is recorded in `ci.yml` beside the step so it reads as a decision.

**The silence, confirmed more precisely than the row states.** Both paths appear in the logs of
both 2026-08-22 runs exactly twice each — as `actions/cache` echoing its own `with:` inputs, never
as a warning. A naive "the logs never mention these paths" would have been **false**; the true
claim is that they are mentioned only as the declaration being read back. The row's quoted
`Cache saved with key:` lines are from run `32553802996` (job `96984722921`), the cold-cache
`workflow_dispatch`; the push run `32563924592` reports `Cache hit occurred on the primary key …,
not saving cache.` for both steps. Neither warns.

## 4. The check, and its mutation test

No instrument existed that could report a phantom cache path, which is the row's actual finding.
One was built for this ticket: it parses `ci.yml` and flags any `actions/cache` path that is
neither `~`-rooted nor present in the tree.

- against `203dec8`: **2 phantom paths**, both named — the defect, demonstrated rather than cited
- against `7ccfc6a`: **0**
- mutated (both paths re-added to the working copy): **fails, naming both**
- restored **from a sha-verified working-copy backup**, never `git checkout --` (the file held
  uncommitted work at the time); mutation confirmed absent afterwards by count, and the check
  re-run green

It is a scratchpad instrument and is **not committed**. Wiring a standing gate for phantom
workflow paths is a real candidate and is not this row's; it is named in BL-174's append rather
than left in a packet.

## 5. Corrections to earlier claims

- **BL-150's 2026-08-22 append undercounts `test-plan.md` §CI.** It says *"seven numbered items
  including `mix test --cover` and two `cargo` commands"*. The section has **eight** numbered items
  and **three** `cargo` commands (6, 7, 8). Not corrected in place: the de-numeralisation rule this
  ticket applied elsewhere says a count over a set someone will edit is the wrong surface, and
  BL-150 is explicitly append-only. Recorded here.
- **The prompt for this ticket called BL-150's disagreement *seven-way*.** BL-150 carries a
  four-surface entry (2026-08-21) extended by a five-surface append (2026-08-22) — nine surfaces,
  ten declarations counting `test-plan.md`'s two disagreeing sets on one page. The figure is not
  restated with a better number, for the same reason.
- **A count in this ticket's own first draft was falsified by this ticket's own commit.** The
  positive control written into BL-174's append said *45 files*; the commit made it 46 by adding
  one `aetheris_worker` mention to `README.md`. Replaced with the command. Caught before landing,
  and recorded because it is the cleanest instance of the rule the ticket was applying all day.

## 6. Owed, and to whom

- **The arbiter:** rule `notes-m09.md` and `m10-autonomous-agent-tooling.md`. BL-174 closes on that
  ruling and on nothing else.
- **The arbiter:** whether `native/aetheris_worker` and `native/aetheris_exec_server` should have
  `fmt`/`clippy`/`test` gates. `README.md` §Running checks now declares **no** Rust checks, which
  is true and is a smaller claim than it used to make; no workflow runs any today. C5 of the
  prompt reserved this and it is reserved.
- **The first push-triggered run** is this commit's evidence, and it happens after review. If the
  `ci.yml` edit is correct, the run reaches `check` and `sandbox` as before; `Cache Dialyzer PLTs`
  and `Cache Cargo` each restore and save with the same keys, no step names a path it could not
  find, and the seven-command set is unaffected because no `run:` step was touched. If the edit is
  wrong, it is wrong at parse time — a malformed `path:` block fails the `actions/cache` step
  immediately and the job dies before `mix deps.get`. There is no failure mode here that is quiet,
  which is the one respect in which this edit is safer than the declaration it replaced.

---

# Stage 2 — BL-174 closes

**Landed:** harness `a49d05a`, agents at the commit carrying this section.
**Baseline:** harness `7ccfc6a`, agents `b3b6069`, **both on origin** — established by fetch,
`merge-base --is-ancestor HEAD origin/main` (YES in both), `ls-remote` reading the remote directly,
and `gh` as a system that does not share git's state. Two earlier stage 2 prompts asserted this
push had happened when it had not; both were stopped at the baseline gate rather than acted on.

## 7. BL-173's outstanding evidence, discharged

Run **`32611562210`**, `push` on `7ccfc6a`, conclusion **success**. `check` 360s, `sandbox` 87s.
Stage 1 §8 made four predictions. Three held; **one missed, and the miss is the useful part.**

**MISSED — "both cache steps restore under the same keys as run `32563924592`, since neither
lockfile was touched."** The *keys* were byte-identical, exactly as predicted. The *restore* missed:

```
32563924592   path: ~/.cargo/registry ~/.cargo/git native/aetheris_nif/target
              key:  Linux-cargo-e6bffd8c9ec09bb283de1a8e49dbdc400fc7a6bca8ba1e0bd07a7cea4ae5431c
              →     Cache hit for: Linux-cargo-e6bffd8c…  /  Cache restored from key: …

32611562210   path: ~/.cargo/registry ~/.cargo/git            ← one line shorter
              key:  Linux-cargo-e6bffd8c9ec09bb283de1a8e49dbdc400fc7a6bca8ba1e0bd07a7cea4ae5431c
              →     Cache not found for input keys: Linux-cargo-e6bffd8c…, Linux-cargo-
              →     Cache saved with key: Linux-cargo-e6bffd8c…
```

Same for `Cache Dialyzer PLTs`. **The mechanism:** `actions/cache` identifies an entry by key **and
version**, where the version is derived from the path list and the compression tool. Stage 1
reasoned about the key — which is `hashFiles('**/mix.lock')` / `hashFiles('**/Cargo.lock')` and
genuinely unchanged — and did not know the path list participates. So *removing a phantom path
invalidates the cache that phantom path was never in*. One cold run, self-healing, and it lands on
the commit that does the removal.

**Elapsed time cannot detect this, which is why it needed the log.** `check` took 360s here against
372s at `32563924592` — *faster*, despite two cold caches, because the untouched `deps`/`_build`
cache still hit and the two cold ones are 12 MB and 3 MB. A reader reasoning from duration would
have concluded the caches hit. Filed as part of **BL-175**, and it is the reason **BL-177** states
its own cold-run cost as measured rather than assumed.

**HELD — both jobs reached.** `check` and `sandbox`, both `success`.

**HELD — no step names a path it could not find.** `grep -icE 'no such file|cannot find|path does
not exist|could not be found|ENOENT'` → 0, against a positive control of 2 on the same command form
for `Cache not found for input keys`. And the two removed paths appear **zero** times in the log,
where at `203dec8` they appeared twice each as the action echoing its own inputs.

**HELD — the seven `run:` steps behave as at `203dec8`.** All seven present in the step list;
`972 tests, 0 failures, 133 excluded` (identical to the local gate) and `No retired or security
advisory packages found`.

**BL-135 did not fire** in this run or in the local `mix test`.

## 8. Two observations from that run — attributed, not fixed

**The `sandbox` job passes without running the set, and has never run it.** `Run the deterministic
sandbox set` is absent from the step list of **all three** runs — `32611562210`, `32563924592` and
`32553802996` — and `Report skipped sandbox set` is present in all three. The probe's verdict is
identical each time:

```
[sandbox] namespace entry failed: Permission denied (os error 13)
  network namespace : false      seccomp filter : false      exec server : false
  verdict: NOT CAPABLE
  missing: seccomp, exec_server, network_namespace
  worker refused to start: :containment_unavailable
```

**An existing row owns this: BL-048**, `**Status:** UNRULED`, in the open backlog. Its own DONE
section states the pending question in terms — *"the attestation only reports on `ubuntu-latest`
once a job runs there… If it reports capable, BL-048 closes as a CI job. If it reports *not*
capable… the harness sprint is the standing home and **BL-048 still closes**, just wired there…
which gate is what the first dispatch decides."* The first dispatch has now happened three times
and the answer is **not capable**, so BL-048's question is answered and its disposition is
available. **No new row filed; not edited either** — attributing is this ticket's job and deciding
BL-048 is not.

**Every job is forced off a deprecated Node runtime.** `actions/cache@v4` and `actions/checkout@v4`
declare Node 20; the runner reports it is overriding them onto Node 24, 12 times per run, in
`32563924592` as well as `32611562210`. **No row owned this.** The only apparent hit in the backlog
was a substring collision — `li`**`node 20`**`26-07` in a cloudcost sentence — and the only
`actions/cache@` mention is BL-173's own closed row, about missing-path silence rather than
runtimes. Filed as **BL-179**.

## 9. Stage 2's own work

**C1a, the reach question, answered rather than assumed.** The sentence as committed said *"If you
are reading a **milestone document**…"*. `notes-m09.md` is at `docs/aetheris/notes-m09.md`, not
under `milestones/`. Semantically it is a milestone document; by location it is not. A reader
resolving the phrase by location excludes precisely the file the ruling was about, so the sentence
was widened to bind *any* document, to enumerate where records live, and to name `notes-m09.md`.

**C1b, the arrival set, established not assumed.** `CLAUDE.md` (self-declared mandatory),
`.github/copilot-instructions.md` (GitHub's convention), `README.md` (front door). Excluded with
reasons: `AGENTS.md` does not exist; `elixir-agent-instructions.md` is titled `# AGENTS.md` but
governs a `scheduler` service and nothing points at it; `playbook.md` is linked rather than
mandatory and has no NIF content.

**C2's dependency check, before the edit.** §5 and §14 of `specs.md` both still speak of NIFs —
named in the repointed §10, not edited. `determinism-contract.md` does not depend on §10: 0 hits,
positive controls 2 (`hash`) and 9 (`determinis`). Nothing in the harness reads `specs.md`; the
`specs.md` `drift_check` reads is the **agents** repo's `docs/rig/specs.md`, a different file with
the same basename — a substring collision of exactly the class this arc keeps producing.

**C3's patterns, proved untouched** by diffing the comment-stripped `.gitignore` against `HEAD`.

## 10. Corrections and defects, stage 2

- **`remove-nif-implementation-notes.md` says "each of the four call-site modules" carries a private
  `hash_content/1`. There were three, and there were three at `e977af0` itself** —
  `git grep -c 'defp hash_content' e977af0 -- lib/` returns one hit in each of three files. Wrong
  when written, not superseded. It is a **RECORD**, so it is not edited; recorded here.
- **A `gh api` check bound to the wrong repository.** At the baseline I queried
  `repos/:owner/:repo/commits/b3b6069` — an agents SHA — from the harness directory, where `:repo`
  resolves to `vishal-h/aetheris`. The 422 was expected regardless of push state, so it was
  evidence of nothing while reading exactly like evidence. Caught with
  `gh repo view --json nameWithOwner`, re-run from the agents directory, and paired with a positive
  control on `80de78e` that resolves. The command-binding class, in a tool where the binding is
  implicit rather than a flag.
- **A mislabelled line that never changed directory.** In the same block, a line printed as
  `cwd aetheris-agents -> :repo` had no `cd` before it and ran in the harness; its output was
  correct for where it ran and wrong for what it claimed. No conclusion rested on it.
- **A wrong claim written into BL-178 and corrected before the commit.** Its Source line first said
  `git grep -n cargo -- ci.yml sprint.sh` "returns only the toolchain action". It returns cache
  paths, a cache key and a comment; `dtolnay/rust-toolchain` does not contain the string. Replaced
  with the claim that is actually checkable —
  `git grep -ln 'cargo fmt\|cargo clippy\|cargo test' -- scripts/ .github/ mix.exs lib/` returns
  `.github/copilot-instructions.md` alone, a file that prescribes the commands and runs nothing.
- **An exactly-once replacement refused, correctly.** The C6 append's first `old_str` omitted the
  two-space indentation of the lines it matched and the helper reported `0 occurrences, need
  exactly 1` rather than editing something adjacent. The guard did its job; recorded because a
  refusal is evidence the instrument works.
