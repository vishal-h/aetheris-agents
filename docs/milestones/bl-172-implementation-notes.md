# BL-172 — implementation notes

Written for the next round in this arc: the arbiter pushing harness `203dec8`, and whoever reads
the first push-triggered run. Harness `203dec8`, agents at the commit carrying this file.

---

## What this ticket was, in one line

`ci.yml` gains a `push:` trigger, `mix hex.audit` joins it as an advisory step, and the
concurrency group stops collapsing to one group on every non-pull-request event. Two rows are
disposed (**BL-169** DONE, **BL-172** stays OPEN), two are filed (**BL-173**, **BL-174**), and one
standing row gains an append (**BL-150**).

---

## The dispositions, and the one that is not what the prompt assumed

**BL-169 — DONE, disjunct 1.** Wiring plus the recorded judgement. The disposition is in the row
itself, now in `docs/backlog-2026-06-closed.md`.

**BL-172 — OPEN.** The ticket prompt characterised this row's Done-when as *"about the trigger,
not about a run"* and asked for a disposition on the evidence the commit produces. That phrase is
the row's own, and in the row it does a narrower job than the paraphrase does: it refuses a
`workflow_dispatch` run staged to look like closure. Disjunct 1 reads, in full, *"either the
workflow fires on the path work actually takes — a `push:` trigger on `main`, or a stated
requirement that changes land through pull requests — **with one run on the record proving it
fires**"*. Nothing is pushed, so there is no such run, and the row cannot close. The prompt's own
§D3 says the same thing from the other side — *"the push trigger itself remains unverified until
something is pushed … that run is BL-172's actual evidence"* — so the two halves of the prompt
disagree and the row's text settles it.

The row therefore carries a dated block recording what landed, what is owed, and what the arbiter
should look for in the first push run.

---

## Corrections this ticket makes to earlier claims of mine

**One, and it is a correction of an omission rather than of a statement.** Nothing in an earlier
packet or notes file of mine is contradicted here; what follows is recorded because the prompt
asked for corrections to land in the notes and not only in the packet, and a nil return to that
question is itself worth writing down.

**The gate-declaration census on BL-150, filed at ds t3 on 2026-08-21, is short.** It reads *"Four
surfaces declare the harness gate set and no two agree"* and enumerates four. Five more standing
surfaces declare one — `.github/copilot-instructions.md`, `README.md`,
`docs/aetheris/runbook.md`, `docs/aetheris/elixir-agent-instructions.md` and
`docs/aetheris/test-plan.md`, the last carrying two disagreeing sets on one page. The four that
were named are correctly read; the entry's error is in its enumeration, not in its readings, so
BL-150 gains an **append** extending the population and the original entry is left standing. That
is the repair the harness rule prescribes — *"a wiring list's clause can be right while its
enumeration is short — repair it as an incomplete enumeration, not as a missing clause"* — and
adding a second entry that re-stated the same claim would have created two surfaces to disagree at
the next addition.

The claim that entry makes about `mix hex.audit` survives the widening: none of the five names it
either. Verified by `git -C ../aetheris grep -n 'hex\.audit' -- <the five>`, which returns nothing,
against `git -C ../aetheris grep -c 'mix credo' -- <the same five>`, which returns a hit in each.

---

## What is verified, and what is not

**Verified.**

- The step's two arms, run against the step body **extracted from the committed YAML** rather than
  retyped, with a stub `mix` on `PATH`: exit 0 → `### Supply-chain audit: clean`; exit 1 → the
  advisory text under `### Supply-chain audit: ADVISORIES FOUND — and this job did NOT fail`, and
  the step still exits 0.
- The workflow parses, and its `on:` block yields all three triggers with `push` carrying
  `branches: [main]`. Both halves of that check were mutation-tested: a syntax break is caught by
  the parse, and a structurally valid mis-indent that silently removes the push trigger is caught
  by the structural read. The file was restored from a sha-verified working-copy backup after each.

**Not verified, and stated as such.**

- **The push trigger.** Nothing is pushed. No push-triggered run exists.
- **A red advisory's behaviour on a real runner.** The lock is green at `bandit 1.12.5`, so the
  step passes; the non-blocking property is implemented and locally exercised, not demonstrated in
  CI. Its closing condition is recorded on BL-169: the first time `mix hex.audit` goes red after
  this lands, someone is looking at that run, because the standing gate rule requires that red to
  get a tracked ticket the day it is found.
- **The concurrency group's value under any event.** It is not observable from a read — the run
  object returned by `gh api repos/vishal-h/aetheris/actions/runs/<id>` carries no concurrency or
  group field. The expression was evaluated by GitHub's documented semantics and the table is in
  the review packet; that is an evaluation, not an observation, and it is labelled so.

---

## Why no dispatch run was performed

The prompt's §D2 asks for a `workflow_dispatch` run after the edit, on the ground that *"the
dispatch is the only way to see the new `hex.audit` step behave"*. It is not: a dispatch runs the
workflow file at a **ref on the remote**, and this commit is held for review. The remote's copy is
`7ea1a3a`'s, which has no `hex.audit` step and no `push` trigger, so a dispatch now would exercise
the old file and produce a run in the record that a later reader could easily mistake for evidence
of this change. The four conditions §D2 lists are all still satisfiable — no side effect outside
the runner, no secret, no cost beyond enabling the workflow, nothing that deploys or writes — and
they are not the reason it was declined. The reason is that the run would carry no information
about the subject and some risk of being read as though it did.

The dispatch that already exists — `32553802996`, `2026-08-22T05:13:54Z`, `success`, both jobs
green — was run at stage 1 against the same `7ea1a3a` tree and is the baseline this ticket used
for the `sandbox` job's named skip and for the cache steps' silence.

---

## Anchors

- Harness `203dec8` — `.github/workflows/ci.yml`, the only file it touches.
- `docs/backlog-2026-06-closed.md` — BL-169, moved under the split rule: a row is in that file iff
  its title section says `**Status:** DONE`, every section its id owns travels with it, and the
  `## ` container heading above it is reproduced. BL-169 owned one section, sat under
  `## Suggested order`, and appends beneath the same heading in the archive.
- `docs/backlog-2026-06.md` — BL-172's dated block, BL-150's append, BL-173 and BL-174.
- The review packet, `bl-172-review.md`, is in a session scratchpad and is not committed; the two
  transcripts it carries (the step's two arms, the two mutation runs) exist nowhere else.

---

# Close round — 2026-08-22, after the push

Written into this file rather than a new one: it is the record the next round in this arc opens,
and a close recorded elsewhere would have to be found rather than read.

## What changed between the two rounds

Nothing in the repository except the push itself. Harness `203dec8` and agents `7792e19` went to
`origin/main` in that order, harness first, and the push of `203dec8` triggered run
`32563924592` — event `push`, branch `main`, sha `203dec8`, conclusion `success`, both jobs green.

**The trigger fired on the commit that introduced it.** GitHub reads the workflow file from the
pushed head, so no second commit was needed to exercise it. The first round's notes recorded the
push trigger as unverified; that is now discharged and the sentence above is where the discharge is
recorded.

## What this round did

- **BL-172 → DONE**, first disjunct, both halves — the trigger and the run. Moved to
  `docs/backlog-2026-06-closed.md` under the split rule, which was re-read from the archive's own
  header for this move rather than carried from the earlier one.
- **BL-173 and BL-174** each gained a sentence saying BL-172 is now closed and where it lives. The
  id is the address and the path is never load-bearing, so neither reference was broken; the
  sentences exist so a reader is not left checking.
- **BL-169** gained a dated block **narrowing** its unverified remainder. Its two existing
  paragraphs are unedited and were true when written.

## The narrowing, because it is the one substantive finding of this round

The first round said *"a red advisory's behaviour on a real runner is UNVERIFIED"*. After the run
that is too broad in one direction and correctly worried in another.

- **No longer unverified: the shell.** The runner reports `shell: /usr/bin/bash -e {0}` for the
  step, which is the interpreter and the flag the local two-arm exercise used. The step's
  `set +e` / `status=$?` / `set -e` construction depends on exactly that, and it is now observed
  rather than assumed.
- **Still unverified: the `else` branch's content.** The text under
  `### Supply-chain audit: ADVISORIES FOUND` has executed nowhere but against a stub. The lock is
  green, so both the runner and the local exercise took the `status -eq 0` arm.

The closing condition on BL-169 is unchanged by this: the first real red after this lands.

## Not demonstrated, and it is not a Done-when item

The conditional `cancel-in-progress`. One push happened, so no competing run existed. The group
value is also unreadable after the fact — the run object carries no concurrency field. Recorded on
BL-172's disposition under (a) so that a later reader seeing two pushes both complete knows nobody
has yet watched that happen.

## Anchors

- Run `32563924592` — <https://github.com/vishal-h/aetheris/actions/runs/32563924592>.
- `docs/backlog-2026-06-closed.md` — BL-169 (with its dated narrowing) and BL-172.
- `docs/backlog-2026-06.md` — BL-173 and BL-174, both still open, both now pointing at the archive.
- The close packet is `bl-172-close-review.md`, in a session scratchpad, not committed.
