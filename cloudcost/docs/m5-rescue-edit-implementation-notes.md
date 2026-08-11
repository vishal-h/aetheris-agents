# m5 — rescue edit: record

Written in the shape the readership candidate describes — findings, what is owed, what is
uncertain, anchors — with the derivation in the commit. Reviewer-directed section-scoped edit;
**per R20 no review file**. Gate at open: agents `a5381ee`, harness `6241972`, both clean and level.
**Harness untouched.**

---

## 1. Findings

**F1 — the artifact survived, and so did its scripts.** Found at
`/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad/`:
`notes-readership-measurement.md`, **17,895 bytes**, mtime **2026-08-11 13:45:25 +0530**, md5
`f90de0d50d0300d55470773c5f3fb26d`. Beside it, **eleven derivation scripts** the prompt only
guessed at (`pop.py`, `scan.py`, `scan2.py`, `q.py`, `q2.py`, `rebuild.py`, `final.py`, `m3.py`,
`m3b.py`, `tab.py`, `ex.py`, 21,970 bytes total) and **thirteen intermediate `.json` files**
totalling **23,102,414 bytes**. Nothing was reconstructed.

**F2 — `/tmp` here is not a tmpfs.** `findmnt /tmp` shows no separate mount; `/tmp` is on
`/dev/nvme0n1p2`, **ext4**, the root filesystem. The systemd rule for it is `D /tmp 1777 root root -`,
an age-less cleanup entry. So the loss risk was real but **reboot- and cleaner-driven, not
memory-driven** — the prompt's stated urgency mechanism is wrong, and the correct one gives no
guarantee either way about how long the window was.

**F3 — the scripts are preserved but not portable.** Every one hardcodes the scratch directory as
`S = '/tmp/claude-1000/…'` and both repo paths as absolutes. They are re-runnable only after
repointing those constants. **Not fixed here**, deliberately: editing them would forfeit the
byte-identity this preservation exists to establish. Recorded in the preservation header and made
part of BL-144's subject.

**F4 — no precedent exists for a preserved measurement.** See §2.

---

## 2. Where it landed, and on what precedent

**Searched:** `git ls-files` across both repos for `census|analysis|measure|survey|audit|/data/|.json`,
plus `docs/` and `scripts/` by hand. **No committed measurement or census artifact exists.** Every
census this project has run — `m4-t4a`'s 54-item structural census, the BL-132 reachability census
— was written as a **notes file**, which is precisely the practice BL-144 questions.

**Nearest structural analogue, and the one this follows: the capability matrix.**

| Role | Capability matrix | This measurement |
|---|---|---|
| derived document | `docs/capability-matrix.md` | `docs/measurements/2026-08-11-notes-readership/report.md` |
| generator | `scripts/assemble_matrix.py` | the 11 `.py`, beside the report |
| intermediates | `docs/.sections/` — **gitignored**, `.gitignore:10` | the 23 MB of `.json` — **not committed** |

**Location proposed, not inherited:** `docs/measurements/2026-08-11-notes-readership/`. Reasons:
(1) the report and its scripts travel as one unit, which is the whole of a measurement's re-run
value, and splitting them across `docs/` and `scripts/` would break that; (2) repo-root `scripts/`
holds exactly three curated standing tools (`assemble_matrix.py`, `check_run_classifier.py`,
`drift_check.py`) and eleven one-off files named `q.py`, `ex.py`, `tab.py` would degrade it;
(3) the date in the path matches the artifact's kind — a one-off snapshot, unlike the matrix, which
is regenerated in place. **This is a proposal and BL-144 owns ratifying or replacing it.**

**Header rule, and where it was applied.** 2b's "commit verbatim" and "add a header block" are
satisfiable together only if the header is delimited and the identity check runs below it — that is
what was done. The header is in `report.md` alone; **the scripts carry no headers**, because a
per-file header would make their byte-identity check impossible, and the header covers them by
name instead. Stated because it is an interpretation, not a reading the prompt forces.

---

## 3. The identity check (2d), as run

```
REPORT BODY  source 17895 bytes  md5 f90de0d50d0300d55470773c5f3fb26d
             preserved 17895     md5 f90de0d50d0300d55470773c5f3fb26d   IDENTICAL: True
SCRIPTS      11/11 md5-identical; `diff -r` over the .py set → no differences
```

The report check compares the bytes **after** the end-of-header marker against the source file, not
the whole committed file, for the reason in §2.

---

## 4. BL-144, and how its number was derived

```
git grep -ohE '\bBL-[0-9]{3}\b'  over BOTH repos, sorted unique  → 144 distinct ids
highest: BL-143 (docs/backlog-2026-06.md:8397)     next free: BL-144
```

**`BL-999` was excluded, on a checked ground rather than by eye.** It is the deliberate dangling
reference in `scripts/sprint.sh:117`, used to test that R17(b) checks a row's *existence* and not
only its shape; it names no row. The exclusion is not new — `m5-ruling-edit-…:557–559` and
`m5-obligation-landing-…:252` each established it before.

Row filed at `docs/backlog-2026-06.md:8461`, in BL-143's field shape, with the trailing `---`
separator restored so the next row inherits one.

---

## 5. What is owed

**Nothing by this round.** The row is filed, the artifact and its scripts are committed, and the
identity check is published.

**Owed by BL-144, and named there:** whether `docs/measurements/` is the convention or a one-off;
whether scripts must be committed at all; and whether an obligation on scripts must also require
portability, since these eleven are preserved but not runnable without repointing.

**No longer owed:** the previous round's record left one open item — that the candidate's evidence
was in neither repo and could not be pointed at by a commit. **That is discharged by this commit**,
and `cloudcost/docs/m5-readership-landings-implementation-notes.md` §4 is the record that named it.
It is not edited here; this round's `Touches` excludes it and the item was reported, not tracked.

---

## 6. What is uncertain

**The instruction's authorship, in part.** BL-144's `Source:` claims the measurement round was
instructed to produce no record and no row. What is **verified** is that the report's own first
line says so, and that the round reached this session through the reviewer-directed prompt channel.
What is **not** independently verified is who composed that instruction — no separate authorship
record exists in either repo, and none was sought. The row says exactly this rather than more.

**How long the window was.** F2 establishes the mechanism but not the deadline: an age-less
`tmpfiles` entry means cleanup is reboot- or policy-driven, so "it might already have been gone" was
true and "it was about to go" is not something this round can claim either way.

---

## 7. Anchors

| What | Where |
|---|---|
| preserved report + scripts | `docs/measurements/2026-08-11-notes-readership/` |
| the row | `docs/backlog-2026-06.md:8461` |
| the candidate that rests on the report | `cloudcost/m5-n1-compose.md:1188` |
| the shape rule this case breaks | `cloudcost/m5-n1-compose.md:1202` |
| the previous round's open item | `cloudcost/docs/m5-readership-landings-implementation-notes.md` §4 |
| `BL-999` decoy | `scripts/sprint.sh:117` |
| intermediates-not-committed precedent | `.gitignore:10` |

**Contract refs check.** R12 (`:335`), R19 (`:468`), R20 (`:528`) in
`docs/milestones/hc-consolidation.md` — all three numbered as cited, **no misnumbering**. R12 (a
ticket's §6 anatomy precedes its opening) and R19 (a session changing a ticket's state updates its
row) are cited but do not bind here: this is not a ticket round and BL-144 is newly filed, not
state-changed.

---

## 8. Line count

**This record: 151 lines**, against the readership-landings record's 179 and the three before it
(234 / 519 / 358, mean 370). The count is stamped last, after the file settled, and was driven to
its fixed point rather than measured once — the hazard the previous record recorded.
