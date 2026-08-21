# ds — the close (implementation notes)

`2026-08-21. Two commits, harness first: harness `2050c04` (parent `d648aa8`) and the agents commit
carrying this file (parent `b56a6b2`). Both baselines were clean and level with `origin/main` —
`git rev-list --left-right --count HEAD...origin/main` → `0	0` in each. Neither commit is pushed by
this session, by instruction. Every figure below carries the command that produced it. Written for
the next round in this arc per harness `CLAUDE.md`, *"an implementation-notes file is read by the
next round in its arc or by nobody"* — and the next round in this arc is whoever runs the export
boundary that this close deliberately did not run.`

---

## 1. Criterion 5's instrument — was the GitHub Project consulted?

**NO — and this close is the one ticket where the answer needs its distinction stated, because it
is also the session that read the board.**

`gh project item-list 6 --owner vishal-h` was run by this session, before either commit, to derive
verdict A's corroborating evidence. The retirement acts — moving the five items to `Done`, closing
the four open issues, closing the Project — are performed AFTER both commits, and their outputs are
in this close's packet rather than here: a notes file asserting them would be making a claim in the
same commit as the thing that would make it true. Neither the read nor the retirement is a
consultation in criterion 5's sense. The criterion distinguishes two lists — decisions
taken **by consulting** the Project, and acts taken **to keep it current** — and every act here
belongs to the second: the item-list read produced *evidence about the board's own state* for
verdict A, and the closing acts are maintenance and then retirement. No decision in this close was
taken from something the Project told us. The decision to retire it came from the five tickets'
implementation notes and the arbiter's ruling, both of which are outside it.

**Recording it as `yes` because a `gh project` command appeared would be the failure the instrument
exists to prevent, running the other way.** Criterion 5's ground is that a criterion answered from
recollection reports clean in the state it was built to catch; an instrument that counts *any*
contact with the Project as consultation is the mirror defect — it would report the trial a success
on the strength of the session that ended it. The two lists are the criterion's own vocabulary and
they separate these acts cleanly.

**So: six of six.** ds t0, t1a, t1b, t2, t3 and this close all answer `no`, verified by opening each
file rather than carried from t3's roll-up.

---

## 2. What landed

| repo | commit | artifact | change |
|---|---|---|---|
| harness | `2050c04` | `docs/methodology/milestone-methodology.md` §6 | three fields optional; ticket-time prompt authoring permitted; `**Done-check.**` required, with its clause |
| harness | `2050c04` | `docs/methodology/triad-loop.md` | the §6 field list de-enumerated into a pointer |
| agents | this | `docs/milestones/hc-consolidation.md` | `### R28`, `### R29`, `### R30`; a dated entry on `### R25` |
| agents | this | `CLAUDE.md` | `## Learning — ds`; the `(#TBD)` convention declared |
| agents | this | `docs/milestones/ds-milestone.md` | status CLOSED; §Open at open answered; §The close |
| agents | this | `docs/project-knowledge-manifest.md` | one row added, one refused, no re-pin, no boundary |
| agents | this | `docs/backlog-2026-06.md` | two appends on BL-150 |
| agents | this | `docs/triad-loop.md` | mirror re-synced to canonical |
| agents | this | this file | — |

---

## 3. Two edits outside the prompt's stated scope, with their ground

**`docs/methodology/triad-loop.md` (harness, commit 1).** Its Phase 1 summary re-enumerated §6's
field list — *"Scope / Contract refs / Touches / Do-not-generate / Done-check / Claude-code prompt
sections per methodology §6"* — as if every field were required. Commit 1 would have made that
sentence false. The vocabulary-sweep rule requires the sweep in the same commit, and the wiring-list
rule says repair the enumeration rather than add a clause; here the enumeration is over-strong, so
it is replaced by a pointer. De-enumerated rather than corrected, on the de-numeralisation rule's
own ground: a copy of the list disagrees at the next amendment.

**`docs/triad-loop.md` (agents, commit 2).** Forced, not chosen. The manifest's own convention holds
that the harness copy is canonical and the agents copy a byte-identical mirror, checked by `diff -q`
at every boundary. The pair was byte-identical at the ds boundary — the manifest records sha256
`847b107e…` on both sides, which is exactly the sha of the file this session backed up before
editing — and commit 1 broke it. Re-synced by copying canonical over the mirror; `diff -q` reports
identical, 205 lines, sha256 `16432ded…` on both sides.

**Neither is scope creep in the sense the rule guards against.** Both are the mechanical consequence
of the edit the prompt did authorise, and leaving either would have shipped a document this commit
made false.

---

## 4. What was found and NOT fixed

Two, both appended to **BL-150**, which is append-only and stays open, so each has an executor
rather than a record.

1. **`prompts/bl-002-refresh-project-knowledge.md` contradicts itself across Step 0 and Step 3.**
   Ruled a BL-150 append at the close; the three false Step 3 claims were re-derived at HEAD against
   `scripts/assemble_export_bundle.py`, and claim 1 was **demonstrated** — a plain run into a
   `mktemp` destination swept clean by default and wrote no `_UNSWEPT-DO-NOT-UPLOAD.txt` — rather
   than argued from the source.
2. **`CLAUDE.md` §Definition of done names a root `conftest.py` that does not exist.** Found by
   criterion 4's census. `pytest.ini` records the mechanism's real placement in `tests/conftest.py`
   and states the absence is deliberate. BL-152's promotion is substantively intact; this is a wrong
   path inside a true rule.

**Why the close does not fix either.** A close audits the standing rules; a repair made in passing
during that audit makes the audit inseparable from the thing audited, and the next reader cannot
tell which sentences the close was judging and which it was writing. Both have an executor.

---

## 5. A negative I got wrong, recorded because the class is this cycle's own promotion

Census step 1(b) checked that the export-boundary entry's named harness counterpart exists. The
first grep returned **zero**, and the entry would have been reported as resting on a rule that is
not in the file. The zero was a defect in my command: the pattern was lower-cased and the rule opens
a sentence. Re-run with `-i` it returns harness `CLAUDE.md:617`, and a positive control with the
same flags over the same file returns hits.

This is `## Learning — ds`'s second sub-class arriving from the other direction — not a negative
asserted from memory, but a negative asserted from a search that could not have succeeded. The
positive control is what separated them, and it cost one command.

---

## 6. What this close did not do

No export boundary. No re-pin of any row but the one added. No push, in either repo. No close
criterion edited, including the two now recorded as vacuous in shape. No `(#TBD)` heading edited.
Nothing on either tracker beyond the five ds issues and Project 6 — and those are acted on after
these commits, with the commands and the resulting state published in the packet, which is the
record for them.

`[The tracker acts are deliberately not narrated here. This file is committed before they run, so
any statement of their outcome would be false in its own commit whatever it says an hour later —
the class harness `CLAUDE.md` names as *a claim that lands in the same commit as the thing that
would make it true*. The packet carries them.]`
