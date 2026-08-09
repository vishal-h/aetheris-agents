# hc-d's opening anatomy edit — implementation notes

**Ticket.** The reviewer-authored section-scoped edit that hc-d's R13 resolver names — *"hc-d's own
opening section-scoped edit, per R12"*. **Repos.** agents `240eb59`, harness `1b09b23` (harness
untouched). **Date.** 2026-08-09.

**Not hc-d.** hc-d's stop stands as a stop. This edit lands the anatomy hc-d stopped for; hc-d
opens in a later session against it. Documents only — no `sprint.sh` change, no code in either
repo, no contract work.

**Landed:** R15–R19; hc-d's five previously-unauthored §6 fields and its step-1 gate G1–G5;
§Not established item 7 resolved by ruling; the `Five tickets.` revision; a re-run status census
with every stale surface fixed; one promotion candidate.

---

## 1. Phase 1 — the verification pass, in full

Every claim the authored text marked `[V]` was checked **before transcription**, at agents
`240eb59` / harness `1b09b23`. **All confirmed. Nothing was refuted, so no sentence was withheld.**

### 1a. Block A — hc-b2's findings are nowhere in the tree at `a581a8c`

**Confirmed, re-derived rather than read off claude-code's hc-d packet.**

- The only `hc-*` review file at `a581a8c` is `docs/reviews/hc-b-review.md`
  (`git ls-tree -r a581a8c -- docs/reviews/`).
- `docs/reviews/hc-b2-review.md` was **first added by `6c61393` itself**
  (`git log --diff-filter=A`), so it does not pre-date the ticket.
- Six wordings over the **entire committed tree** at `a581a8c`:

```
exactly two slots                      0 files
inconclusive                           0 files
two invocations                        0 files
the gate's home                        0 files
Finding B                              0 files
stub-provider run with a worker        1 file
```

  The single hit is `docs/milestones/hc-consolidation.md:211` at that tree — R5's step 1, **hc-b's
  own gate text**: the premise hc-b2 refuted, not hc-b2's finding about it.

### 1b. Block B — the `Five tickets.` line and its note

**Confirmed: both still read as claude-code left them.** `git blame`: `:466–467` unmodified since
`e8cd5cd` (hc-b), the note at `:469–472` unmodified since `eee5fed`.

### 1c. R16 — both premises, derived from source

**Confirmed end-to-end.** The authored text asked for derivation because *"hc-c asserted it and did
not observe it"*:

| Link | Source | What it says |
|---|---|---|
| The Mix task drops the code | `../aetheris/lib/mix/tasks/aetheris.ex` | `_ = Aetheris.CLI.run(argv)` then `:ok` |
| `run/1` returns a code and does not halt | `../aetheris/lib/aetheris/cli/main.ex:46–48` | returns `Formatter.print(result, mode)`; its own `System.halt` is **commented out**. Only the escript's `main/1` halts on the value |
| The code is 1 on failure | `../aetheris/lib/aetheris/cli/output/formatter.ex:78–82` | `print({:error, reason}, :json)` → payload on stdout, prose on stderr, **returns 1** |
| A failed run reaches that clause | `../aetheris/lib/aetheris/cli/commands/run_helpers.ex:119–121` | `"failed"` → `{:error, %{run_id:, status: :failed, error: …}}` |

So the exit code **exists, is 1, and is discarded** — a failed run under `mix aetheris` exits 0.
The status word is present on every terminal outcome, as R16 relies on: `done`, `failed`,
`cancelled`, and `error` for a bare-string reason (`error_payload/1`, same file).

`run_agent` branches on exit status — `sprint.sh:139–145`, verbatim
`if run_aetheris --json run "${args[@]}" > "$output_file" 2>&1; then … else fail "$label →
non-zero exit"; fi` — and `run_aetheris()` (`:40–42`) is `mix aetheris "$@"`, so BL-044 reaches
this path.

**One qualification, recorded in the document beneath R16 rather than only here.** The `else` arm
is unreachable *for a run that reaches `Formatter.print`*. A `mix` compile failure or an uncaught
raise still exits non-zero and trips it. hc-d's own notes §3 carry the same *"today"* hedge; G2 is
the item that will observe it.

### 1d. R18(b) — R11's wording and the guard

**Confirmed verbatim at harness HEAD**, which matters because R11 cited `288c8ef` and a verified
citation decays when the file moves. It has not moved: `../aetheris/scripts/sprint.sh`
`:3125`–`:3136`, guard at `:3128`:

```bash
      if [[ -s "$cc_file" ]] && grep -q run_id "$cc_file"; then
```

hc-c did not touch `sprint.sh` (its own §Ticket set row says so), which is why the anchor survived.

### 1e. G5 — the two numbers

- **BL-077's Done-when says *"Audit all 31 cases"*** — confirmed, `docs/backlog-2026-06.md:2903–2904`
  verbatim; the row's header paragraph (`:2865`) says *"all 31 cases"* too.
- **The 29-not-31 constraint is recorded in this document in three places** — R1's derivation note
  (`:143–152`), **R7's note (`:249–252`)**: *"**BL-077's own Done-when says "Audit all 31 cases".
  The population is 29.** Derived above under R1, two ways. hc-d derives the number and names the
  population; it does not inherit 31, and it does not silently substitute 29 either"*, and hc-d's
  own catch-all constraint (`:714–716` pre-edit).
- **Re-derived at HEAD, both of R1's ways:** `grep -c '  *section "'` → **29**; `$TARGET" == "…"`
  takes **30** distinct values of which one is `all` → **29**.

> **One observation for G5, which is not a `[V]` and is left for hc-d to use or discard.** R1's
> parenthetical says *"the two unindented hits are the `section()` definition at `:38` and the
> `Prerequisites` call at `:176`"*. There are **three** unindented hits, not two: `section
> "Sprint Complete"` at `:3161` is the third, and also outside any case — true at `288c8ef` as
> well as at HEAD. **29 is unaffected** (it counts indented calls). What this adds is a candidate
> provenance for BL-077's 31: `grep -c 'section "'` over the whole file, indented or not, returns
> exactly **31**. G5 asks for a derivation, not for an explanation of the wrong number, so this is
> an input and not a finding.

> **`[corrected at r1 — see §r1.2.]`** The blockquote above is **wrong, and wrong in the class it
> was verifying.** There are **two** unindented `section "` hits, not three: `:38` is
> `section() { … }` and contains no `section "` at all, so it is matched by `grep -n '^section'` —
> the pattern this observation used — and not by the pattern the 29 and the 31 come from. Under one
> pattern, 29 + 2 = 31. **R1's parenthetical is right about the count and wrong about its members**
> (`:176` and `:3161`, not `:38` and `:176`), which is a different correction from the one this
> blockquote proposed. Original text left standing per decision 7; the correction itself lands in
> G5's edit, per r1's A3.

### 1f. Block E2 — hc-d's own state

| Claim | Verdict | Evidence |
|---|---|---|
| Opened and stopped 2026-08-09 at agents `240eb59` | **Confirmed** | `git log -1 --date=short 240eb59` → `2026-08-09` |
| No contract work; BL-077 and BL-133 untouched | **Confirmed** | `240eb59` touches five files, all docs; `docs/backlog-2026-06.md` is **not** among them. The harness has no hc-d commit at all — `b4d782a..HEAD` is hc-c's two |
| D1 refuted at its premise, D2 filed, D3 filed **and** resolved | **Confirmed, all three, at that commit** | D1 → the `[STAYS OPEN … its premise was tested first and does not hold]` block; D2 → the packet-assembly candidate; D3 → §Not established **item 8 added and its `[RESOLVED … by running them]` block added in the same commit** |
| 2 of 7 §6 fields authored | **Confirmed from the document at `240eb59`, not from the packet** | Over `### hc-d` in `git show 240eb59:…hc-consolidation.md`, the only §6 field headings present are `**Scope.**` and `**Contract refs.**`; the five others → **0**. **Positive control:** the same pattern over `### hc-c` → **5 of 5**, so the zero reads as absence, not as a broken pattern |
| The header line reads *"hc-a, hc-b and hc-c closed; hc-d next"* | **Confirmed** | `:12`, verbatim |

**The final clause of the authored cell was written only after reading this commit's own tree** —
the five §6 fields → 5, `### hc-c` positive control → 5, G1–G5 → 5, all under `### hc-d`. It is a
claim this commit makes true, and it is verifiable by reading the same commit.

### 1g. Checked against hc-d's authored `Scope` and `Contract refs`: no contradiction

`Do not generate`'s *"No fix to BL-044"* does not violate R3's *"do not pre-decide it"*: R3's own
text provides *"If no, BL-044 stays filed with the finding recorded"*, R16 supplies the design
basis for that branch, and R16 is itself refutable by G1 — which stops the ticket rather than
proceeding on the likelier reading. `Touches`'s exclusion of `../aetheris/lib/` is consistent with
that same branch. The operator-facing surface the Runbook update rule points at **exists**
(`../aetheris/docs/aetheris/runbook.md` §Validation sprint, `:415–435`), so nothing must be created
there. `shellcheck` is **absent on this machine**, which Done-check item 2 already anticipates.

---

## 2. Reviewer divergences this edit corrects

Four, all recorded rather than silently smoothed:

1. **The anatomy-state claim.** hc-d's opening was framed as landing its anatomy; **2 of 7** §6
   fields were authored. Established by claude-code at the stop, re-derived here from the document
   itself with a positive control (§1f), and now stated in hc-d's own State cell.
2. **`hc-d §1a` and `hc-d §1d` do not resolve.** The A-block cites *"claude-code's hc-d §1a
   search"* and R16 cites *"claude-code's hc-d §1d finding"*. `hc-d-implementation-notes.md` has no
   letter sub-anchors: the search is **§1**, the `run_agent` input is **§3** (R-ii). Transcribed
   with the anchors that resolve — R15 now cites §1, and R16's paragraph carries the derivation
   inline rather than an anchor. `hc-d §4` resolved correctly and was used as given.
3. **"its hc-d r2 note".** The note revised under block B is tagged `[added 2026-08-09 (hc-c r2,
   F7(b))]` — **hc-c** r2. hc-d has no r2 at all: `docs/reviews/hc-d-review.md` carries Round 0 and
   an empty Round 1. The `[V]` itself — *both still read as claude-code left them* — is confirmed.
4. **The Claude-code prompt's decision range.** As authored it read *"§Ratified decisions R1–R18"*.
   R19 lands in this same commit and binds hc-d directly (hc-d closes rows and changes its own row),
   so a prompt shipping with `R1–R18` would be stale at birth. Transcribed as **`R1–R19`**.

---

## 3. The status census, re-derived

E2 asked for a re-run over all seven surfaces, using hc-c r2 §8b's own population definition —
*every place this document states an `hc-*` ticket's state* — **re-derived, not copied**. Matched
on state vocabulary (`Status:`, `closed`/`Closed`, `In review`, `Not started`, `In progress`,
`opened`, `stopped`, `underway`) over the whole file, then classified by hand.

**§8b found 7. The re-derivation finds 10.** §8b's population omitted **hc-b2** — a ticket whose
state this document states in three places — because the round running the census was adding one of
them. E2's warning that *"the same is possible here"* was correct, in the population rather than in
the verdicts.

| # | Surface | Verdict |
|---|---|---|
| 1 | Header `**Status:**` line (`:12`) | **STALE** — *"hc-d next"* does not describe a ticket that opened and stopped. **Fixed here**, under R19 |
| 2 | §Ticket set, `hc-a` row | current |
| 3 | §Ticket set, `hc-b` row | current |
| 4 | §Ticket set, `hc-c` row | current |
| 5 | §Ticket set, `hc-d` row | **STALE** — `Not started`. **Fixed here** by E2's authored cell |
| 6 | §Ticket set, `hc-e` row | current — `Not started`, and true |
| 7 | §hc-a's opening prose | current — hc-a's second surface, as §8b noted |
| 8 | The `Five tickets.` note | **STALE in its gap clause** — *"a live R12 gap"* is false under R15. **Fixed here** by block B's dated amendment |
| 9 | §Not established item 7's head | **STALE in its gap and owed-action clauses** — *"an R12 gap, recorded rather than back-filled"* and *"`Five tickets.` above needs revisiting"*. **Closed here** by block B's `[RESOLVED]` block; the original text stands unrewritten, per decision 7 |
| 10 | Item 7's D1 block | current — a dated finding whose facts are unchanged |

**Four adjacent surfaces, reported and deliberately not fixed.** A census that does not say what it
declined to touch is the thing this round keeps promoting rules about:

- **hc-e's named question** (§Ticket set → hc-e) — *"What hc-c and hc-d actually did … None of it
  is knowable now"* is **partly falsified**: hc-c's arm landed, decision 13 was not overturned,
  both rows closed. **Not fixed.** It is hc-e's reviewer-authored ticket text, and R19 states it
  *"does not extend to a ticket the session did not touch"*. Carried for hc-e's author.
- **§Not established's preamble** — *"Each is a question this round opens and has not closed"* is
  false for items 1 and 8 (resolved) and for item 7 after this edit. **Out of the census
  population**: it states an item's state, not a ticket's. Named, not fixed.
- **§Rows filed's *"Empty at hc-b"*** — still true; hc-c closed rows and filed none. §8b named the
  same adjacent surface as checked-and-still-true.
- **§Not carried's *"A five-ticket round's sequence is its ticket set"*** — still true under R15:
  hc-b2 is a round, not a sixth ticket.

---

## 4. What is transcription and what is claude-code's

Decision 11's split, stated so a reviewer can audit it:

**Transcribed verbatim** — R15, R16, R17, R18, R19; hc-d's `Touches`, `Do not generate`,
`Runbook update rule`, `Done-check` (items 1–6), `Claude-code prompt` (with §2's item 4 change);
G1–G5 and the precondition; item 7's `[RESOLVED]` block; the promotion candidate.

**Claude-code's, and named as such:**

1. **The `Five tickets.` sentence.** The reviewer stated three facts and not the words — *hc-b2 ran
   as a sixth session, is classified under R15 as hc-b r2, has no row by design*. The sentence
   assembles exactly those three and adds nothing.
2. **The header `Status:` line's new text**, under R19's standing authorisation.
3. **Three blockquoted verification notes** in §Ratified decisions (under R15, R16, R18), recording
   the derivations the `[V]` marks asked for — per decision 2, so a later reader sees what the
   ratification rested on.
4. **Placement and formatting.** The five §6 fields sit after the R3 paragraph and before the gate,
   which is hc-c's precedent for an extra block between `Contract refs` and `Touches` with the gate
   last. The discharged R13 mark and the discharged catch-all are kept beneath the gate as dated
   notes rather than deleted, per decision 7 — and the catch-all's **second** constraint (BL-077's
   stale §Suggested order entry) is flagged as covered by **no** gate item, because G5 absorbs only
   the first.

---

## 5. One flagged observation, reported and not fixed

**hc-d's authored `Scope` promises four post-conditions; the authored `Done-check` exercises two.**
Nothing in items 1–6 covers:

- **the summary block's printed blocking / not-yet-declared counts** — R7 calls that constraint
  *"not optional"* (*"A zero in the second column is a claim; a number is a status"*), and hc-d's
  `Contract refs` cites R7; and
- **the provenance stamp and the stated retention bound** — R1: *"Retention is **stated and
  bounded**, not indefinite; hc-d picks the bound and prints it."*

Done-check items 3 and 4 pass with both absent. **Not fixed**: the fields are the reviewer's, and
adding a done-check item is authoring one. Recorded here and in the packet so the next author sees
it before hc-d's gate runs rather than after its packet is written.

---

## 6. Not reached, not dropped

- **hc-d's R-iii and R-iv** remain undischarged, as its own notes §5 left them. R-iv (*whether the
  `tee`/`pipefail` coupling really makes BL-077 and BL-133 face 2 one ticket*) is now partly
  addressable: G3 is its resolver, and R18(a) is the constraint it becomes if the coupling is live.
- **BL-077's row is not corrected here.** G5 corrects it *in hc-d*, which is where `Touches`
  reaches `docs/backlog-2026-06.md`. This edit files and closes no backlog row, so §Rows filed is
  untouched and still reads *"Empty at hc-b"*.
- **No review file was touched.** This is a reviewer edit, not an `hc-*` ticket round; `599747e`
  (hc-c's opening edit, which added R14) is the precedent for a doc-only commit with no review-file
  entry. hc-d's own review file keeps Round 0 and its empty Round 1.

---

# Round 1 — six reviewer additions

**Accepted at agents `3971121`.** r1 is a **round of the anatomy edit, not a new session-ticket** —
per **R15**, which the anatomy edit itself ratified one commit earlier. **Repos.** agents from
`3971121`, harness `1b09b23` (untouched, and clean). **Date.** 2026-08-09.

**Landed:** hc-d Done-check items 7 and 8, and item 2 amended; **G0** before G1; a G5 reconciliation
clause; §Not established **item 9**; the promotion candidate's count replaced by an open list; and a
`[partly falsified]` marker on hc-e's named question.

---

## r1.1 Phase 1 — the two `[V]`s

**Both confirmed. Neither differs from the authority it points at, so both items transcribe.**

**Item 7's `[V]` — R7's own wording.** Quoted from `hc-consolidation.md` §Ratified decisions → R7,
verbatim:

> **With one constraint, and it is not optional.** Arms defaulting to non-blocking silently would
> let the sprint report green over an unaudited set — the silent-wrong-answer shape, in the
> mechanism built to stop it. **The summary block prints how many arms are blocking and how many
> are not yet declared.** A zero in the second column is a claim; a number is a status. Both
> printed explicitly, never by omission.

The phrase r1 offered for comparison — *"A zero in the second column is a claim; a number is a
status"* — is **character-for-character R7's**. **No difference to report.** R7's *"it is not
optional"* is also its own words, so item 7's opening clause is quoting, not paraphrasing. Both are
now quoted inside the item so a later reader is not sent to R7 to check it.

**Item 8's `[V]` — R1's wording.** Quoted verbatim:

> The run directory gets the sprint's own console output — every arm, in order, untruncated — **and**
> a small stamp naming both repos' commits, the target, and the command. Retention is **stated and
> bounded**, not indefinite; hc-d picks the bound and prints it.

**Transcribed against it, with one sharpening the `[V]` instruction required.** r1's item 8 said the
stamp *"names what produced it"*; R1 names **four** elements — both repos' commits, the target, the
command. *"Transcribe against R1's wording"* therefore means the item must carry the four, or it
would license a stamp naming one of them. The item now does, and the substitution is named here
rather than made silently.

---

## r1.2 A3 — the figures reconcile, and the error is mine

**A3 was right that the three figures were in tension and right to forbid a correction written on
them. The reconciliation is now on the record, and it shows the tension was an artefact of my own
§1e.**

`sprint.sh:38` is `section() { echo -e … }` and contains **no `section "` at all** —
`sed -n '38p' scripts/sprint.sh | grep -c 'section "'` → **0**. My §1e's *"3 unindented hits"* came
from `grep -n '^section'`, which matches the **definition**; the 29 and the 31 come from
`section "`, which does not. Under the one pattern the counts actually use:

```
$ grep -c '^section "'   scripts/sprint.sh    →  2      (:176 Prerequisites, :3161 Sprint Complete)
$ grep -c '  *section "' scripts/sprint.sh    →  29
$ grep -c 'section "'    scripts/sprint.sh    →  31     ← 29 + 2
```

**They sum.** A3's second disjunct is the true one.

**Consequences, stated rather than acted on.** R1's parenthetical is **right about the count and
wrong about the members**: there are exactly two unindented `section "` hits, as it says, but they
are `:176` and `:3161` — it named the definition, which the pattern does not match, and omitted
`Sprint Complete`. **Not corrected here**, per A3's instruction: the correction lands in G5's edit
beside the derivation. G5's paragraph is transcribed as authored, with the reconciliation recorded
as a dated blockquote beneath it so the document does not carry an open tension that is closed.

**The error's class, and it is the round's second instance.** A count over the wrong population,
inside a verification of a count — one level above what it was verifying. hc-d's R-i found the
first (reads-per-file where the question was reads-per-invocation). Mine is reads-of-one-pattern
where the question was about another. **What G5 still owes is undiminished:** one stated pattern, the
enumeration printed beside the count, R1's parenthetical corrected, and the *"31"* provenance
**established or not offered**.

---

## r1.3 A2 — no revert was performed, because none was needed

A2 asked for the `config/config.exs` block to be recorded verbatim and then reverted so the tree
would be clean for G0. **It reverted itself, and that is the finding's second half.**

| Time | State | Evidence |
|---|---|---|
| `09:03:07` | block present, uncommitted | mtime; `git diff` shows +4 |
| `09:08–09:10` | a second `mix test` runs | mtime **unchanged** → `mix test` refuted as the writer |
| `09:24:05` | block **gone** | mtime moved; `grep -c playground_tokens` → 0 |
| `09:26` | tree clean | `git status --porcelain` → **0 lines** |

No session action touched that file at any point. **Nothing was reverted by hand and nothing was
committed**, so no claim about the cause is made in either direction. The four lines are recorded
verbatim in §Not established item 9 from the `git diff` captured at the anatomy edit's done-check —
the working-tree copy no longer exists to re-read, which is itself why recording it first was the
right instruction.

**G0 is transcribed as authored** and is the standing consequence: hc-d stops on a dirty harness
tree rather than producing a sprint result no commit can reproduce.

---

## r1.4 Two findings, reported and not fixed

**Finding 1 — §Not carried's count of §Not established is stale, and this commit is what staled
it.** It reads *"the open questions are **§Not established's four**, each with its resolver named"*.
The section holds **nine** items, enumerated: 1 `[sandbox]` routing (resolved), 2 the chaos gate, 3
hc-a Part 4's transcription, 4 no harness-side pointer, 5 hc-c's Ollama dependency, 6 stdout log
consumers, 7 hc-b2's anatomy (resolved), 8 the provenance suites (resolved), 9 the `config.exs`
writer — added by this round. It was true at hc-b, when there were four. **Not fixed**: it is a
count inside reviewer-authored §Not carried prose, and R19 is scoped to ticket rows, not to every
count. Named so the next edit does not have to rediscover it.

**Finding 2 — R15's mechanism has no carrier for reviewer edits, and r1 is the first case.** R15
credits R2's committed review file with making a repair round's scope *"committed and pre-date the
round"*. **R2 binds `hc-*` tickets, and the anatomy edit is a reviewer edit with no review file** —
so r1's scope (A1–A6) lived in conversation until this commit, which is precisely the condition D1
established for hc-b2 and R15 was written to rule about. **Not resolved here**, and no review file
created unilaterally: whether reviewer edits acquire review files, or whether their notes file *is*
the committed record, is a ruling. **What this round does instead** is transcribe A1–A6 verbatim in
r1.5 below, so r1's scope is committed by the round that ran it even if the mechanism naming that
obligation does not yet reach here.

---

## r1.5 A1–A6, verbatim, so this round's scope is committed and not only conversational

Recorded per Finding 2. The reviewer's text as received, abbreviated only by dropping the `[V]`
annotations that r1.1 discharges.

- **A1** — hc-d's Done-check gains items **7** (the summary block's printed counts, both, including
  the zero case; R7 non-optional; observed on a real run, an omitted line being the defect) and
  **8** (the provenance stamp and retention bound on a real artifact; a bound stated but unenforced
  is permitted and must be *stated as unenforced* in the runbook and §Not established). Item **2**
  amended: `shellcheck` is absent as of 2026-08-09, attempt the install, and on failure publish the
  failure output and record the absence in §Not established rather than omitting the line. Nothing
  renumbered.
- **A2** — **G0** added *before* G1 so G1–G5 keep the numbers the document already references: the
  harness working tree is clean at the ticket's start, `git status --porcelain` zero lines, HEAD
  recorded; not clean → stop and report, however harmless the modification looks, because a sprint
  run on an uncommitted tree cannot be re-derived from any commit. Plus the §Not established entry,
  the verbatim record, and the revert.
- **A3** — G5 also reconciles the three non-summing figures under **one** stated pattern, prints the
  full enumeration, accounts for every line the pattern matches and does not, then corrects R1's
  parenthetical in the same edit and records whether the whole-file figure is BL-077's *"31"*
  provenance or a coincidence. *"A provenance is established or it is not offered."* R1's
  parenthetical is **not** to be corrected now.
- **A4** — the promotion candidate's *"Three instances in this round"* replaced by an open list
  (i)–(v) with **no total**, later ones appending; the rest of the candidate unchanged.
- **A5** — hc-e's named question **marked, not rewritten**, with the `[partly falsified 2026-08-09
  (anatomy edit r1)]` block; revised in full at hc-e's own opening anatomy edit; original wording
  stands per decision 7.
- **A6** — the anatomy edit's four recorded divergences accepted with no action; its (2) and (3) are
  now **(iv)** and **(v)** in A4's list; its (4), transcribing `R1–R19` where `R1–R18` was written,
  confirmed correct — *"a prompt shipping stale at birth is worse than a transcription divergence"*.

**Scope held.** Documents only. No `sprint.sh` change, no code, no hc-d contract work, no backlog
row filed or closed. hc-d opens in the next session against the anatomy after this round.
