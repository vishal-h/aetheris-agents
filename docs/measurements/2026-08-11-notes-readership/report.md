<!-- PRESERVATION HEADER — added 2026-08-11 at the rescue edit. NOT part of the report. -->

# PRESERVED — notes-readership measurement (2026-08-11)

**This header was added when the artifact was committed. Everything below the marker line is the
report exactly as it was written, byte-for-byte, and was not edited, reformatted, or corrected —
including anything in it now believed wrong.** It is preserved as the evidence a decision rested
on, not published as current truth.

| | |
|---|---|
| **Produced** | 2026-08-11, file mtime `13:45:25 +0530` |
| **Repos stood at** | agents `4caa671`, harness `6241972` — both clean and level with `origin/main`, as the report's own gate line states |
| **Preserved at** | 2026-08-11, from `/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad/` |
| **Source md5** | `f90de0d50d0300d55470773c5f3fb26d` (of the body below, unchanged) |

**The decision it grounded.** It answered the question three deferred items were waiting on —
whether implementation-notes files are ever read — and its answer un-deferred two of them and
decided a third by its own number. The promotion candidate that rests on it is landed at
`cloudcost/m5-n1-compose.md` §Milestone summary → §Open for the next cycle, at agents `a5381ee`.

**The producing round wrote no record and filed no row**, by instruction; the report's own opening
line states it (*"Read-only round. No edits, no commit, no row, no notes file for this round."*).
That is why this artifact was in neither repo and had to be rescued a round later. The obligation
this case raises is **BL-144**.

**The derivation scripts are preserved beside this file**, verbatim and without headers of their
own so that each stays byte-identical to what was found: `pop.py`, `scan.py`, `scan2.py`, `q.py`,
`q2.py`, `rebuild.py`, `final.py`, `m3.py`, `m3b.py`, `tab.py`, `ex.py`. **Two caveats for anyone
re-running them.** They hardcode the now-gone scratch directory as `S = '/tmp/claude-1000/…'` and
absolute repo paths, so the constants must be repointed first — not edited here, because editing
them would forfeit the byte-identity this preservation is for. And the ~23 MB of intermediate
`.json` they wrote is **not** committed: it is regenerable by these scripts, which is the same
rule `docs/.sections/` follows for the capability matrix (`.gitignore:10`).

<!-- ===== END PRESERVATION HEADER — verbatim report begins on the next line ===== -->
# Measurement — do the implementation-notes files ever get read?

**Read-only round.** No edits, no commit, no row, no notes file for this round.
Gate: agents `4caa671`, harness `6241972`, both clean and level with `origin/main`.

**THE ANSWER: mostly no — and where yes, only by the very next round.** 73% of the files
(51% of the lines) have no evidence of ever being read by anything. Of the 27% that were,
the median lag between writing and reading is **1 day**, and 18 of 27 opens are on day+1.
Past a week the record is effectively inert. The files work as a hand-off buffer between
adjacent rounds, not as a durable record.

---

## A. INSTRUMENT COVERAGE AND CONTROLS — read this before any number below

### A1. Instrument B (transcripts) — coverage

Session transcripts are at `~/.claude/projects/<project-dir>/<session-uuid>.jsonl`, plus
**nested subagent transcripts** at `<session-uuid>/subagents/*.jsonl` which the prompt did not
mention and which I included, attributed to the parent session.

| | |
|---|---|
| Transcript files scanned | **164** (92 top-level + 72 subagent) |
| Sessions with timestamps | 92/92 top-level |
| Earliest timestamp | **2026-06-12T13:32:47Z** |
| Latest timestamp | **2026-08-11T08:01:51Z** |
| Projects | agents 87 · harness 4 · eduloka 1 |

**The unmeasurable part, named rather than reported as a zero.** **27 of 163 population files
(17%) were created before 2026-06-12**, the first transcript. For those, instrument B has **no
data** — a zero there means "not observed", not "never opened". They are small: **1,909 of
32,434 lines (6%)**. Affected trees: `api/`, `docs/`, `drive/`, `email/`, `payslip/`. Every
`cloudcost/`, `docbuilder/` m3+ and `hc-*` file is inside the window.

### A2. Schema, derived not assumed

Each line is a JSON object. `type` ∈ {`user`, `assistant`, `system`, `attachment`, `mode`,
`file-history-snapshot`, …}. A tool call appears on an `assistant` line as a block in
`message.content[]` with `{"type":"tool_use","name":<tool>,"input":{…}}`. **The target path is
not one field:** `Read`/`Edit`/`Write` carry `input.file_path` (absolute); `Bash` carries
`input.command` (a shell string that may contain the path); `Grep`/`Glob` carry
`input.pattern`/`input.path`. Timestamps are top-level `timestamp`; session identity is the
filename UUID.

**So "opened" is split into two tiers rather than merged:**
- **Strong** — a `Read`/`Edit`/`Write` whose `file_path` *is* the file. An actual open.
- **Weak** — a `Bash`/`Grep` whose command text merely names it. Could be an enumeration
  (`ls`, a census, a `git log --`) rather than a read.

This split exists because **this measurement session greps notes paths wholesale** and would
otherwise register as a reader of everything. Excluding this session changes the file counts by
**zero** (18/163 and 46/163 either way) — the files it opened already had other readers.

### A3. Controls — minted fresh, stated before running

| Control | Expectation | agents | harness | Verdict |
|---|---|---|---|---|
| `zqf-notes-readership-probe` | 0 everywhere | **0** | **0** | as expected |
| `implementation-notes were read` | 0 (phrase never used) | **0** | **0** | as expected |
| `implementation notes` | hundreds | **211** | **38** | as expected |
| `Source:` | hundreds | **382** | **66** | as expected |

Both negatives are silent and both positives fire, so the corpus is searchable and the zeros
below are absence rather than a broken search. **These four tokens are now spent** — they appear
in this report, so a later round re-using them will find this file and read its own instruments
as content. Stated rather than performed: a successor should mint its own, or scope with
`':!<this file>'`.

### A4. Three defects in my own instruments, found and fixed mid-round

Reported because each would have inflated the answer in the flattering direction:

1. **Basename collision.** `t3-implementation-notes.md` exists **5×** (payslip, drive, email,
   api, cloudcost); `t1`/`t2`/`t4`/`t5` 3× each — **17 files across 5 colliding basenames**. A
   basename-keyed index credited all five with each other's hits. Rebuilt keyed by `(repo, path)`.
2. **Substring matching.** `t3-implementation-notes.md` matches inside
   `m5-t3-implementation-notes.md`. Added a left-boundary guard `(?<![A-Za-z0-9_/-])`. This alone
   removed the four largest apparent hit-counts.
3. **No after-filter.** My first pass counted commits *before* the file existed — the notes file's
   own sources, not its readers. Hits with negative day-offsets were being read as citations.
   Fixed to `commit_time > creation_time`; **29 full-path hits were of this kind.**

A fourth was fixed in instrument B: subagent transcripts were being attributed to the project
directory rather than the parent session (`parts[-4]` vs `parts[-3]`), collapsing 72 transcripts
into 3 pseudo-sessions.

---

## B. M1 — THE POPULATION

**Convention established by inspection, not assumed.** 160 of 163 match
`*-implementation-notes.md`. **Three record files do not** and are included:

- `cloudcost/docs/m5-scoping-landing-notes.md` (854L) — *"# m5 — scoping landing record"*
- `docbuilder/docs/tickets/fix-docbuilder-currency-rendering-notes.md` (63L)
- `../aetheris/docs/aetheris/milestones/mcp-worker-start-fix-notes.md` (61L)

**Three `*notes.md` files excluded as not round records**, with their first lines as the ground:
`agents/notes.md` (28L, *"Two halves, clean separation:"*), `../aetheris/docs/aetheris/claude-notes.md`
(301L, a standing doc), `../aetheris/docs/aetheris/notes.md` (292L).

| | |
|---|---|
| **Files** | **163** — agents 137, harness 26 |
| **Total lines** | **32,434** |
| **Date span** | **2026-05-19 .. 2026-08-11** (85 days) |
| By tree | docs 56 · docbuilder 53 · cloudcost 38 · api 5 · rig 5 · payslip 3 · boxy-pipeline 1 · email 1 · drive 1 |

---

## C. M2 — CITATION IN COMMITTED HISTORY

**1,533 commits scanned** (agents 930, harness 603), added lines only, both repos.

**Exclusions applied, counted** (full-path matches): **299 excluded** — same day as creation
**224**, own creating commit **34**, commit predates creation **29**, inside the file itself
**12**. **142 full-path hits kept**, plus unique-basename hits → **164 hit lines** classified.

### The classification criterion, stated before applying it

**R (reasoning)** if the text *following the reference* attributes content — a `§` section, a
line number, a figure, or quoted text. **P (pointer)** otherwise: the path in a `Source:`/
`Record:`/`Touches`/`Predecessor:`/`Section:` field, a bare list or table cell, or inside a shell
command.

- **R example (counted):** `docs/backlog-2026-06.md` at `e1a1830` —
  *"`cloudcost/docs/m4-t4a-implementation-notes.md` — **54 items** from a structural AST
  extraction over **518 nodes**, with a recorded completeness argument."* A figure attributed to
  the file's content.
- **Near-miss excluded (counted P):** `cloudcost/docs/m4-t4b-implementation-notes.md` at
  `d62e817` — *"**Predecessor:** m4 t4a, the seam census
  (`cloudcost/docs/m4-t4a-implementation-notes.md`)."* Names the file and characterises the
  *ticket*, not the file's content. Structural.

### Results

| Kind | Hit lines | Files with ≥1 |
|---|---|---|
| **P — pointer** (named, not read) | **89** | **38** |
| **R — reasoning** (content attributed) | **75** | **27** |
| **Q — quotation** (raw) | **54** | **17** |

**Q needs a discount and gets one.** Of the 17 Q files, **7 are false positives of a single
shape**: the notes file recorded text that the *same arc* then wrote into code, so the later
commit is the implementation, not a reader. All the `docbuilder` Q hits are this — the rig
replay fixtures at `dc024d1` contain a recorded agent prompt the notes had quoted; likewise
`api/docs/t1` → `at1cmd.exs`, `m-docbuilder-m1-t7` → `docbuilder_orchestrator.exs`. **~10 files
carry genuine Q.**

**R and Q lag is short.** Median R-citation lag **1 day**; 54 of 75 R hits land within a day of
the file's creation; only 6 land more than a week later (max 48 days).

---

## D. M3 — WHAT SESSIONS ACTUALLY OPENED

| | Files (of 163) |
|---|---|
| Opened later by a **`Read`/`Edit`/`Write`** (strong) | **18 — 11%** |
| Named later in a **command** (weak) | **46 — 28%** |

**The lag is the finding.** 27 strong later opens across those 18 files:

| Lag | Opens |
|---|---|
| **1 day** | **18** |
| 2–3 days | 6 |
| 4–7 days | 2 |
| 8–30 days | 1 |
| >30 days | **0** |

Median **1 day**, max **22** (`payslip/docs/t3c-implementation-notes.md`, 2026-05-22 → a
2026-06-13 session). **Nothing in the population was opened more than 22 days after it was
written.**

The 18, with distinct later sessions: `m5-t3` **3**, `cloudcost/t1` **4**, `m5-t2` **2**,
`bl-007-t4` **2**, `m2-t1` **2**, and **1 each** for `hc-e`, `m5-ruling-edit`, `m5-t1`,
`m5-scoping-landing`, `m5-pin-edit`, `bl-084`, `cloudcost/t3`, `cloudcost/t2`, `bl-007-t1`,
`bl-003-startup-sweep`, `t3c`, `bl-016-payslip-orchestrator-test`, `m-tenant-data-layer-t1`.

---

## E. M4 — CROSS-TAB AND ANSWERS

### E1. The table (top 22 by line count; full population measured)

| lines | days old | P | R | Q | later sessions | path |
|---:|---:|---:|---:|---:|---:|---|
| 1820 | 2 | 4 | 3 | 0 | 1 | `docs/milestones/hc-e-implementation-notes.md` |
| 1632 | 1 | 2 | 3 | 0 | 1 | `cloudcost/docs/m5-ruling-edit-implementation-notes.md` |
| 1474 | 5 | 5 | 11 | 3 | **0** | `cloudcost/docs/m4-t4a-implementation-notes.md` |
| 869 | 1 | 1 | 0 | 0 | 1 | `cloudcost/docs/m5-t1-implementation-notes.md` |
| 854 | 2 | 13 | 6 | 16 | 1 | `cloudcost/docs/m5-scoping-landing-notes.md` |
| 804 | 1 | 9 | 19 | 0 | 3 | `cloudcost/docs/m5-t3-implementation-notes.md` |
| 767 | 2 | 1 | 0 | 0 | **0** | `docs/milestones/hc-d-implementation-notes.md` |
| 678 | 4 | 0 | 2 | 0 | **0** | `cloudcost/docs/m4-t4b-implementation-notes.md` |
| 610 | 22 | **0** | **0** | **0** | **0** | `docs/rig/milestones/bl-007/bl-007-t5-implementation-notes.md` |
| 606 | 1 | 2 | 1 | 0 | **0** | `cloudcost/docs/m5-close-anatomy-implementation-notes.md` |
| 578 | 2 | 6 | 2 | 1 | 1 | `cloudcost/docs/m5-pin-edit-implementation-notes.md` |
| 555 | 1 | 5 | 2 | 0 | 2 | `cloudcost/docs/m5-t2-implementation-notes.md` |
| 538 | 23 | 0 | 1 | 0 | 2 | `docs/rig/milestones/bl-007/bl-007-t4-implementation-notes.md` |
| 519 | 6 | **0** | **0** | **0** | **0** | `cloudcost/docs/m3-t1-implementation-notes.md` |
| 519 | 0 | **0** | **0** | **0** | **0** | `cloudcost/docs/m5-obligation-landing-implementation-notes.md` |
| 511 | 2 | **0** | **0** | **0** | **0** | `docs/milestones/hc-d-anatomy-edit-implementation-notes.md` |
| 499 | 5 | **0** | **0** | **0** | **0** | `cloudcost/docs/t1b-implementation-notes.md` |
| 488 | 2 | **0** | **0** | **0** | **0** | `docs/milestones/hc-e-anatomy-edit-implementation-notes.md` |
| 462 | 5 | 1 | 1 | 0 | **0** | `cloudcost/docs/m4-t3-implementation-notes.md` |
| 424 | 2 | **0** | **0** | **0** | **0** | `docs/milestones/hc-c-implementation-notes.md` |
| 405 | 5 | **0** | **0** | **0** | **0** | `cloudcost/docs/m4-t2-implementation-notes.md` |
| 396 | 0 | **0** | **0** | **0** | **0** | `cloudcost/docs/bl-132-row-correction-implementation-notes.md` |

### E2. The four questions

**1. What fraction of the total notes lines sits in files with zero Q, zero R, and zero later
opens?**
**119 of 163 files (73%), holding 16,531 of 32,434 lines — 51%.** Half of everything written
has no trace of ever having been read by anything.

**2. Is there a relationship between length and being read?**
**Yes, and it is confounded.** Files ≥400 lines: **12/21 read (57%)**. Files <400 lines:
**32/142 (23%)**. But the long files are almost all recent `cloudcost/` and `hc-*` records, and
recency is the stronger predictor: created **on/after 2026-08-01 → 44% read**; before →
**20%**. Length is a proxy for "written in the last three weeks under review discipline", not an
independent cause. And the counter-example is decisive: the **longest** file in the population
with zero later opens is `m4-t4a` at **1,474 lines**, and `bl-007-t5` at **610 lines** has zero
on **every** instrument.

**3. Which files were read, and what do they have in common?**
44 files by some instrument. By tree: **cloudcost 22 of its 38**, docs 11 of 56, docbuilder 7 of
53, api 2, payslip 1, rig 1. Two things in common, and neither is "importance":
- **Adjacency.** The reader is nearly always the *immediately following round in the same arc* —
  m4 t4b reading m4 t4a, m5 pin-edit reading m5 scoping-landing, hc-e reading hc-b, the
  disposition-ground round reading m5 t3. Median lag 1 day.
- **Correction over census.** The read files are disproportionately those a *later round had to
  correct or build directly on*. The three biggest census files — `m4-t4a` (1,474L),
  `hc-d` (767L), `bl-007-t5` (610L) — have **zero** later opens between them. A census is
  consulted once by its own successor, if at all; a correction is chased.

**4. For files that were read, what was read out of them?**
The strongest instance in the population — `m4-t4b` (2026-08-07) using `m4-t4a` (2026-08-06),
one day later, **not by citation but by machine-reading the file**:

```
$ F=cloudcost/docs/m4-t4a-implementation-notes.md
$ grep -cE "^#### (X|N|D|F|P|R)[0-9]+" "$F"
54
$ for g in X N D F P R; do printf "  %s = %s\n" "$g" "$(grep -cE "^#### $g[0-9]+ " "$F")"; done
  X = 5
  N = 9
  D = 21
```

and, in the same file, `blocks = re.split(r"^#### ", Path("cloudcost/docs/m4-t4a-implementation-notes.md").read_text(), flags=re.M)[1:]`.
What was read out was **the census itself as data** — 54 items, class counts, re-derived rather
than trusted. That is the one unambiguous case of a notes file functioning as a durable record
rather than as prose, and it happened **one day** after the file was written, by the ticket
that split from it.

A second, different in kind — `m5-pin-edit` (2026-08-10) grepping `bl-067-implementation-notes.md`
**11 days** after its creation and pasting the hit line verbatim:
`docs/milestones/bl-067-implementation-notes.md:74:| M1 | Summary undercounts agents by one | …`.

### E3. The strongest argument against this conclusion

**Made properly, because it is not weak.**

The measurement can only see traces that survive into a commit or a tool call. It cannot see the
thing the notes may actually be for: **that writing them forced a check that caught an error at
the time.** This round is itself the evidence. Writing this report forced four instrument
defects into the open — the basename collision, the substring match, the missing after-filter,
the subagent misattribution — every one of which would have produced a *more flattering* number,
and none of which would have left any trace if I had not been writing the derivation down. On
the same logic, `m4-t4a`'s 1,474 lines with zero later opens may have been worth writing because
producing the census is what established the 54 items — and the file is the artifact that proves
the census was done rather than asserted. Deleting the notes would not have saved the work; it
would have saved only the typing, and lost the auditability.

There is a sharper version. **`P = 89` is the convention discharging itself, and I have counted
it as such — but the R class may be doing the same thing one level up.** Many R hits sit in the
*next* round's record, written by a session that had the prior round in its context window rather
than on disk. The transcript instrument partly separates these (18 strong opens vs 27 R-bearing
files), and the gap suggests **some R citations were written from memory of the round, not from
the file.** If so the true read rate is *lower* than reported here, not higher — the
counter-argument cuts against the flattering reading in one direction and against my own
headline in the other.

**Against the null specifically:** 6% of the lines are in files created before the transcript
window, and for those instrument B is blind. That is small enough not to move the 51%.

---

## F. WHAT IN THE PROMPT TURNED OUT TO BE WRONG

1. **"Claude Code session transcripts are on this machine under `~/.claude/projects/` as
   `.jsonl`"** — true but **incomplete in a way that matters**. It omits the 72 **nested subagent
   transcripts** under `<session-uuid>/subagents/`, 44% of all transcript files. A measurement
   that took the prompt's description as the population would have missed them.
2. **"Establish the naming convention by inspection rather than assuming the
   `*-implementation-notes.md` suffix"** — correct instruction, and it paid: **3 record files do
   not match**. But the prompt did not anticipate the **opposite** problem, which was the larger
   one: the suffix is not merely incomplete as a filter, it is **ambiguous as a key** — 17 files
   share 5 basenames, and keying on the basename silently merges five different `t3` records.
3. **"For each file in M1, search all commits AFTER its creating commit"** — the instruction is
   right and I initially failed to implement it; noting it here because the prompt was *not*
   wrong and my first pass was. 29 full-path hits were pre-creation commits.

**Not wrong:** both repos were clean and level; the transcript schema is as loosely described
(no field name was assumed); a null was indeed the majority outcome.

**One thing the prompt got exactly right and is worth naming:** the instruction not to go looking
for a weaker sense of "used". The weak instrument (command-text mentions) returns **46/163 = 28%**
against the strong instrument's **18/163 = 11%**, and most of that gap is censuses enumerating
filenames — including this round's own. Reporting the weak number as the answer would have
roughly tripled the apparent readership while measuring nothing but `ls`.
