# gc-stale-claims — the cycle document

> Not a feature milestone. This round enumerates the class of **stale gate claims** — sentences
> that instruct a reader to complete some named prior work before some future work, where that
> prior work is closed at HEAD — corrects the live-read members of that class, and lands the two
> unfiled pointer defects the preceding read-and-report established. t1 enumerates and corrects
> nothing; t2 lands the pointer pair; t3 corrects and files.

> This is the `gc` round. Its predecessor is `cloudcost/m5-n1-compose.md`, which is a
> cloudcost-series document; this one is not, and a sweep looking under `cloudcost/` will not
> find it. Named for what it is: round `gc`, subject `stale-claims`. The directory follows
> `docs/milestones/hc-consolidation.md` and `milestone-methodology.md` §3. **The id `gc` is
> ratified as minted; the subject was re-ruled from `census` at the t1 review** — see §Naming
> derivation.

**Status:** **OPEN.** t1 run and reviewed 2026-08-11; t2 run 2026-08-11; t3 authored, not opened.
**Opened:** 2026-08-11. **Document created:** 2026-08-11 (at t1, the round's first session).
**Renamed** 2026-08-11 at the t1 review, from `gc-census.md`.
**Repos:** `aetheris-agents` and `aetheris` (harness).
**Preceding cycle:** m5-cloudcost, closed 2026-08-10.

---

## Why this exists

BL-074 closed 2026-08-07 (`docs/backlog-2026-06.md:2786`, `:2811`). Live documents still instruct
readers to run it before provider four. The preceding read-and-report found such sentences by
reading four documents it had been pointed at — which is **observation, not enumeration**, and is
the exact failure mode BL-074's own §7 promotion candidate names
(`aetheris/CLAUDE.md:770–777`, *"Tell: 'the one X' is an observation, not a census"*).

So this round enumerates the class before anything is corrected. **Correcting the sentences found
by accident is out of scope at t1 by design**; t3 corrects what t1 adjudicated, and only that.

The class is deliberately wider than BL-074 and wider than provider four: it is every sentence, in
either repo, at HEAD, that gates future work on a named prior row that is closed.

---

## Carried in

From `cloudcost/m5-n1-compose.md` §Open for the next cycle, which m5 records as the subsection the
next cycle opens and reads. Four items are live for this round; the rest were disposed inside m5
itself. Verify each against m5's own text and record where it sits.

1. **The deferred `mix dialyzer` obligation.** Discharged by D1; the run is §Close criteria
   clause 5.
2. **An implementation-notes file is read by the next round in its arc or by nobody.** m5 carries
   it as a candidate, not promoted. It is the finding D5 rests on, and it also governs how this
   round writes its own records.
3. **A negative-control token stops being a negative control once a record quotes it.** m5 carries
   it as a candidate. It was in force at t1, which minted fresh controls, published them, and
   verified each at zero before relying on it — verify that against t1's own record and cite it.
   t1's controls are spent by publication; any later sweep in this round mints its own and verifies
   them at zero before use.
4. **§7's distillation can lose what the candidate got right.** m5 carries it as a candidate. It
   binds this round's §7 at the close: an entry promoted out of §Promotion candidates is compared
   against the candidate it came from, not only read out of its destination file.

Items 2–4 arrive carried rather than promoted, and this round inherits that disposition rather than
re-opening it. What this round owes them is application, not a verdict.

> `[Verified and recorded 2026-08-11 at the t2 review, per this section's own instruction. Where
> each sits in m5, read from that file:`
>
> - **Item 1** — `cloudcost/m5-n1-compose.md:1157–1167`, the *"One standing obligation carried
>   forward"* block, whose preamble states it is *"**not** a §7 candidate and carries no promotion
>   disposition — it is a gate this cycle deferred and still owes"*. Narrated a second time at
>   `:1006–1008` and in m5's t3 ticket-set row at `:47`; the block itself is the channel this
>   section reads.
> - **Item 2** — `cloudcost/m5-n1-compose.md:1188–1199`, with its consequence for record shape at
>   `:1201–1210` and its open question at `:1212–1224`. Ground: **163 files, 32,434 lines**, of
>   which **119 (73%)** have no trace of ever having been read. Preambled at `:1183–1186` as *"One
>   promotion candidate carried forward"*.
> - **Item 3** — `cloudcost/m5-n1-compose.md:1079–1104`, with two dated corrections to its ground
>   and attribution at `:1106–1125` and `:1133–1148`, and a third failure mode appended inside the
>   entry at `:1150–1155`.
> - **Item 4** — `cloudcost/m5-n1-compose.md:1070–1077`, under the *"Two findings carried forward
>   for the next cycle's §7"* preamble at `:1064–1068`.
>
> **Item 3 against t1's own record.** t1 minted three controls fresh, published them, and verified
> each returned **0 before** anything was relied on: `qqzx-gate-control-alpha` → 0,
> `wibblefrotz-precondition` → 0, `zarquon-before-provider` → 0, over both repos. None was
> discarded, so t1 recorded no discard. Its positive control fired in the same corpus with the same
> flags (`read \*\*BL-074\*\*` → 1 hit at `cloudcost/runbook.md:620`). **The citation is the t1
> review packet**, which at the time of writing has **no in-repo home**: this round has produced no
> implementation-notes file and no review file, so item 3's own instruction to *cite* t1's record
> cannot be satisfied by a committed path. Raised at the t2 review and not resolved here.`

---

## Naming derivation

Stated before the file was created, per the instruction that an ambiguous convention stops the
round.

**Files read:** `cloudcost/milestone.md`, `cloudcost/m2-milestone.md`, `cloudcost/m3-milestone.md`,
`cloudcost/m4-consolidation.md`, `cloudcost/m5-n1-compose.md`, `docs/milestones/hc-consolidation.md`,
`docs/milestones/m-eduloka-discovery-kickoff.md`,
`../aetheris/docs/methodology/milestone-methodology.md` §3.

**The convention, as the documents state it about themselves:**

- **Directory = the series the round belongs to.** `cloudcost/m4-consolidation.md:8–10` — *"This is
  the m4 entry in the cloudcost series … named for what it is rather than to the series pattern."*
  `docs/milestones/hc-consolidation.md:7–9` — *"This is the `hc` round. Its predecessor is
  `cloudcost/m4-consolidation.md`, which is a cloudcost-series document; **this one is not, and a
  sweep looking under `cloudcost/` will not find it.**"* `milestone-methodology.md:59` gives the
  normative path as `docs/milestones/m-<name>.md`, which agrees for non-series rounds.
- **Filename = `<round-id>-<subject>.md`, named for what the round is.**
  `hc-consolidation.md:9` — *"Named for what it is: milestone `hc`, subject `consolidation`."*

**Application.** This round is **not** a cloudcost-series round: t2 touches `docbuilder/` and the
harness methodology and carries zero cloudcost paths; t1's class spans both repos. Directory is
therefore `docs/milestones/`, on which both authorities agree.

**What was derived and what was minted.** The directory and the `<id>-<subject>` shape are derived.
The **round id `gc` was minted** — no rule for minting an id exists in either repo, and
`hc-consolidation.md:29` records that hc's own naming was *"a naming decision"* produced by a
scoping read and ruled on by the reviewer. `gc` follows hc's derivation (id abbreviates the round,
subject names the work): **g**ate-**c**laim round.

**Provenance of the name, added 2026-08-11 at the t1 review.** The id `gc` was **minted by
claude-code at t1** and **ratified by the reviewer at the t1 review**. The subject was
**re-ruled at that same review**, from `census` to `stale-claims`: `census` names t1 only, and the
round also carries t2, which is not census work. The file was renamed `gc-census.md` →
`gc-stale-claims.md` at the review.

---

## Round rules in force

Carried from `docs/milestones/hc-consolidation.md`, which `cloudcost/m5-n1-compose.md` cites by
number and therefore treats as standing. Only those that bind this round are listed.

| Rule | Where | How it binds this round |
|---|---|---|
| **R12** | `hc-consolidation.md:335–347` | Ticket anatomy is written into this document before the ticket opens, and **authoring is the reviewer's (decision 11)**. This document was authored by claude-code on the round prompt's explicit instruction — a **recorded deviation**, not a silent one; see the note below, **narrowed and ratified at D3**. |
| **R13** | `hc-consolidation.md:349–360` | A slot that cannot be authored yet is marked with its resolver, never blank and never guessed. t3's `Touches` was R13-marked at t1 and is **unblocked at the t1 review**; the resolver arrived. |
| **R19** | `hc-consolidation.md:468–481` | A session that changes a ticket's state updates that ticket's row in the same commit. This session changed t1's, t2's and t3's states and updated all three. |
| **R20** | `hc-consolidation.md:528–542` | A reviewer-authored section-scoped edit is not a ticket round and gets no review file. |
| **R21** | `hc-consolidation.md:546–…` | §Not established holds three kinds of entry; only one owes a resolver. Item 1 is `[RESOLVED]` at D1. |
| **decision 6** | `hc-consolidation.md:583` | Pushes held for review; a cross-citing repo pair lands together, **harness first**. t2 landed to that shape. |
| **decision 7** | `hc-consolidation.md:584` | A closed record gets a dated superseded note; original text not rewritten. Bears on t3's m5 destination. |
| **decision 8** | `hc-consolidation.md:585` | Live operational guidance is corrected in place. Bears on t3. |
| **decision 10** | `hc-consolidation.md:587` | A milestone-named document is a closed record if a current equivalent exists — established, never inferred from the filename. The basis for every live/archival call t1 made, and for D2. |
| **decision 11** | `hc-consolidation.md:588` | Content is authored by the reviewer; formatting belongs to the destination file. |

> **Deviation, recorded rather than glossed (R12 / decision 11).** This document's creation and its
> ticket anatomy were authored by **claude-code**, on the round prompt's explicit and repeated
> instruction. R12 assigns authoring to the reviewer, and `cloudcost/m5-n1-compose.md:19–25`
> records the nearest precedent — a fresh round document created by the *reviewer*, with the
> deviation there being only the edit's shape. Here the deviation is in the **author**, which is
> the substantive half. Recorded here so the round opens with it visible; the reviewer's ratifying
> edit is what closes it.

> `[Narrowed 2026-08-11 at the t1 review. The paragraph above stands unrewritten per decision 7;
> **D3 supersedes its characterisation.** The deviation is not that claude-code authored the ticket
> content — decision 11 splits content from formatting, and the content was the reviewer's, in the
> round prompt. It is that t1's anatomy was written and t1 executed in one session, so no reviewer
> saw t1's §6 before it ran. Ratified as a one-off at D3.]`

---

## Decisions

Authored by the reviewer at the t1 review. Each is a ruling on an item t1 raised for arbitration;
none is a finding of fact, and each rests on evidence t1 recorded rather than on anything asserted
here.

**D1 — This round's close runs `mix dialyzer`, discharging m5's deferred obligation.** The
trigger's second arm fires on "the next cycle's close". m5's own usage settles what that names: it
calls §Open for the next cycle the subsection the next cycle opens and reads, and this round opened
and read it — verify both citations and record them. The argument against, which t1 recorded
fairly, is that a records round changes no Elixir and so the run exercises nothing this round
touched. It does not carry. Arm 1 already covers the code-touching case; if arm 2 fires only for
code-touching rounds it is arm 1 restated and the deferral has no backstop at all — which is the
precedent the deferral's own stated reason refuses to set. Verify and record that reason verbatim
from m5's record. The run's cost is one command; its output is a baseline the provider-four round
can diff against.

> `[Verified and recorded at the t1 review, 2026-08-11, per the block's own instruction.
> **Citation 1** — `cloudcost/m5-n1-compose.md:1067–1068`: *"They are recorded here because this is
> the subsection the next cycle's §7 reads, and it is the subsection m5 itself inherited its own
> carried candidates through."* **Citation 2** — `cloudcost/m5-n1-compose.md:1173–1174`: *"**None of
> the four is this subsection**, and this subsection is the one the next cycle opens."* Both resolve
> and both say what D1 relies on. **The deferral's stated reason, verbatim from m5's own record**
> (`cloudcost/docs/m5-t3-implementation-notes.md:485–487`, read from that file and not from m5's
> quotation of it): *"**`mix dialyzer` is deferred, not skipped, and the deferral names a trigger
> that can fire.** Skipping silently makes *"we skipped dialyzer"* the precedent, and the gate that
> never runs is the gate that rots — which is the rule's whole reason for existing."*]`

**D2 — `cloudcost/m4-consolidation.md` is archival. t3 does not correct it.** It is a closed round
document with a successor, and a current equivalent exists for its provider-four sequencing text —
verify both and record where the current equivalent lives. m5's §Not established item 1 calling its
two statements "live" is not a contradiction of this: m5 uses *live* to mean unretracted-at-HEAD,
and hc decision 10's live/archival distinction is about whether a document is read for current
guidance. Two senses of one word, and the equivocation is itself a finding this round records
rather than resolves — see §Promotion candidates.

> `[Verified and recorded at the t1 review, 2026-08-11. **Closed:** `cloudcost/m4-consolidation.md:12`
> — *"**Status:** **CLOSED 2026-08-08** — see §The close."* **Successor:** `cloudcost/m5-n1-compose.md`,
> whose §Sequence at `:29–30` places the hc round and then m5 after it, and whose own header names
> m5-cloudcost as this round's preceding cycle. **The current equivalent lives at
> `cloudcost/runbook.md` §Adding a provider (`:567–631`)** — it carries the live five-place wiring
> enumeration (`:573–579`) and the provider-four instruction (`:619–631`), and it is the file
> `cloudcost/m3-milestone.md:682` sends a reader into. That is the document an adapter author
> actually opens; m4-consolidation is not.]`

**D3 — The R12 deviation is narrower than t1 recorded, and is ratified as a one-off.** Decision 11
splits content from formatting: t1's and t2's ticket content was authored by the reviewer in the
round prompt and formatted into §6 anatomy by claude-code, which is the split working as written.
What R12 actually forbids happened anyway, and to t1 alone: t1's anatomy was written and t1 was
executed in one session, so no reviewer saw t1's §6 before it ran. That is ratified as a one-off,
with its reason recorded — the round document did not exist, and creating it and running its first
ticket in one session was the reviewer's instruction. It does not recur: t2's anatomy is ratified
at this review and opens after it; t3's is authored at A.3 below and opens in a later session.

**D4 — What this round corrects, and what it defers to a row.** t3 corrects the live-read stale
gate claims t1 adjudicated, and nothing else. Every other finding t1 surfaced is deferred, and
under the agents-side deferred-finding rule a deferred finding gets a backlog row in the round that
defers it — so t3 files them. Prose in this document files nothing. The rows are enumerated at A.3.

**D5 — Absence of a stamp is not a verdict, and a verdict that lives only in an
implementation-notes file is not recorded.** t1 established that six contracts carry no reachability
stamp and that the silence encodes three different dispositions — answered-elsewhere,
not-applicable, and reachable-with-nothing-to-qualify — which a reader of the contract file cannot
tell apart. Two of the three verdicts exist only in a notes file. §Carried in item 2 carries m5's
measurement finding that such a file is read by the next round in its arc or by nobody, so a verdict
parked there is a verdict with no reader. Deferred to a row, not fixed here: the fix is a
contract-file edit and this round has no contracts ticket.

> `[Repointed 2026-08-11 at the t2 review; the error was the reviewer's and is corrected rather
> than left standing, this document being live and the edit pre-dating any reader of D5. The
> sentence read *"This round's own §Promotion candidates carries the measurement finding…"* — and
> **no such entry existed there**: §Promotion candidates as authored at the t1 review held three
> entries, none of them the measurement. **The finding is m5's**, at
> `cloudcost/m5-n1-compose.md:1188–1199`, carried into this round at §Carried in item 2, which is
> what D5 now names. D5's other sentences are byte-unchanged.]`

**D6 — hc decision 10's "current equivalent" means equivalence of operational content, not of the
whole document.** t2's archival finding on the docbuilder m4 milestone rests on one leg — a runbook
section carrying that milestone's operational content — and asks whether decision 10 demands more.
It does not. A milestone document is never wholly equivalent to anything: it carries its own ticket
anatomy, its own done-checks and its own record, and nothing succeeds those. Read as whole-document
equivalence, decision 10 could never be satisfied by any document and no milestone document could
ever be archival, which would make the decision a dead letter — verify that reading against decision
10's own text and against how t1 applied it across the census, and record what you find. The test
the decision states is where a reader seeking current guidance goes. The archival finding stands and
the dated note stays. This is an interpretation of a standing decision, not an amendment to it;
whether it should be written back into `hc-consolidation.md` is a question for this round's close and
not settled here.

> `[Verified and recorded 2026-08-11 at the Phase D edit, per D6's own instruction.`
>
> **Decision 10's own text**, `docs/milestones/hc-consolidation.md:587`: *"A milestone-named document
> is a closed record **if a current equivalent exists** — established, never inferred from the
> filename"*. It says *a current equivalent*, not *an equivalent of the whole*; and the clause it
> emphasises is **established, never inferred**, which is about the standard of proof, not the scope
> of the equivalence. The dead-letter reading holds: every milestone document carries ticket anatomy,
> done-checks and a per-ticket record that no successor reproduces, so under whole-document
> equivalence the antecedent is never satisfiable and the decision would classify nothing.
>
> **How t1 applied it across the census.** t1 used decision 10 as the basis for every live/archival
> call it made, and in each one the thing it looked for was a **current place a reader goes**, not a
> full replacement: `cloudcost/m3-milestone.md`'s provider-four bullet was called archival because
> *"a current equivalent exists in `cloudcost/runbook.md` §Adding a provider"*, and
> `docs/handoffs/handoff-m3-close-2026-08-05.md` because it is *"superseded by m4-consolidation and
> m5"*. Neither successor reproduces the whole of what it succeeds. **So the operational-content
> reading is not new here — it is the one already applied 441 times in t1's archival set**, and D6
> states what that practice already assumed rather than changing it.
>
> **One thing D6 does not settle and this bracket does not either:** whether *operational content* is
> the right general name for the test, or whether the decision is better read as *where a reader
> seeking current guidance goes* with operational content merely the usual carrier. D6's own last
> sentence reserves the write-back question for the close, and this is part of it.]`

---

## Ticket set

| Ticket | Purpose | State |
|---|---|---|
| **t1** | The gate-claim census — enumerate the class across both repos | **RUN 2026-08-11; REVIEWED 2026-08-11.** Census complete: 640 id-form hits and 162 description-form hits over a 143-row population, 48 closed; five live-read stale gate claims adjudicated in id form plus one in description form. Three method defects found by the ticket's own controls and corrected in the open. Record: the t1 review packet. **Reviewed at the t1 review, which authored §Decisions, §Close criteria, t3's body and §Promotion candidates, and renamed this document.** |
| **t2** | The two pointer defects — one citation, one missing reverse pointer | **RUN 2026-08-11.** Both edits landed, cross-repo, harness-first per decision 6; mirror pair re-verified byte-identical after the sync. Pushes held. Record: the t2 review packet. |
| **t3** | The stale-gate correction sweep, and the rows this round defers | **AUTHORED 2026-08-11 at the t1 review, NOT OPENED.** `Touches` unblocked — the resolver t1 named arrived. Two arms: corrections (D4) and rows (D4, D5). |

---

### t1 — the gate-claim census

**Scope.** After this ticket the class of stale gate claims is enumerated rather than observed:
every sentence in either repo, at HEAD, that gates future work on a named backlog row that is
closed at HEAD, is on the record with its path, line, gate-voice class, referenced row, that row's
close date, the kind of document it sits in, and whether that document is live-read or archival.
The row population and every row's status are derived programmatically from the backlog, with the
extraction inlined and its controls published. Nothing is corrected.

**Contract refs.**
- `aetheris/CLAUDE.md` — **Adjacent-case and load-bearing coincidence**, and its *"the one X"*
  tell; **Every claim has a truth-maker**; **Silent-wrong-answer**, specifically the
  positive-control clause owed by whoever reports a negative; **Complete-output**.
- `aetheris/docs/methodology/milestone-methodology.md` §11 entry 4 — every prompt gates on itself.
- `aetheris-agents/CLAUDE.md` — *Ticket text that quotes repo state*.
- `docs/backlog-2026-06.md` — the row population. Not restated here.

**Touches.** Nothing. This ticket is read-only over both repos; its only artifact is the review
packet and this document's row.

**Do not generate.** No correction to any stale sentence found. No backlog row, opened or edited.
No repair of either pointer defect. No ruling on any item the census surfaces.

**Runbook update rule.** Not engaged — no environment variable, startup step, configuration key,
operational procedure, or observable semantics changes.

**Done-check.**
```bash
# 1. Both repos clean, HEADs stamped, before anything else.
git -C ~/sandbox/elixirws/aetheris-agents status --porcelain
git -C ~/sandbox/elixirws/aetheris        status --porcelain

# 2. Row population and status, derived — not counted by eye. The extraction is
#    inlined verbatim in the packet and must publish BOTH controls:
#    positive (rows known closed from committed text classify CLOSED) and
#    negative (rows with no closure text classify OPEN).

# 3. Negative controls for the sweep: minted fresh this session, published,
#    and each verified to return 0 BEFORE anything is relied on.
#    A control returning non-zero is discarded and the discard recorded.

# 4. Subset check — the five sentences the preceding read-and-report reported,
#    each individually present-or-absent in the census output. Any miss is a
#    finding about the method and is diagnosed, not patched over.

# 5. The offline spine, unchanged — this ticket changes no executable line.
#    Re-resolve both anchors at HEAD first: cloudcost/runbook.md §Offline tests
#    for the command, CLAUDE.md §Commands for the root. A differing count is a
#    finding, not a pass.
python3 -m pytest cloudcost/tests/ -q
```

**Claude-code prompt.** Superseded by the round prompt of 2026-08-11, which is what ran. Recorded
here per R12's requirement that anatomy live in this document rather than only in relayed ticket
text; the prompt's own text is the authority for what t1 was asked to do.

---

### t2 — the two pointer defects

**Scope.** After this ticket two pointers resolve to what they claim. (a) The docbuilder m4
milestone's citation names the section that actually contains the text it quotes. (b) The
`triad-loop.md` section that `milestone-methodology.md` §11 entry 2 declares itself a continuation
of carries a reverse pointer back, landed in the canonical harness copy and synced to the agents
mirror. Both defects were established by the read-and-report of 2026-08-11 and **re-verified at
HEAD** at `aetheris-agents 160da89` / `aetheris 6bc49fc` before this ticket was written.

**(a) The citation.** `docbuilder/docs/m4-milestone.md:409–410` reads:

> `- `milestone-methodology.md` §9 anti-pattern: "Recovery sessions are where`
> `  doc-first discipline slips" — re-verify canonical-doc sync explicitly`

The quoted text is the **final bullet of §8**, `../aetheris/docs/methodology/milestone-methodology.md:267–271`.
§9 exists and resolves (`:275`, *"## 9. Anti-patterns (each observed at least once)"*), so the
citation is **silently wrong rather than visibly broken** — and it is plausible in both directions,
since §9's title is *Anti-patterns* and the cited bullet is written in anti-pattern voice.
**Note for whoever makes the edit: `:406` of the same `Contract refs` block already cites §8**
(*"§7 (milestone-end ritual) and §8 (sync rules)"*), so the corrected citation collapses into a
sibling of a reference three lines above it, and the edit should say so rather than produce two
adjacent §8 citations that read as a duplication.

**(b) The reverse pointer.** `../aetheris/docs/methodology/milestone-methodology.md:327–328`:

> `  Continues `triad-loop.md` § **Doc edits are section-scoped (claude-ui never replaces a`
> `  whole file)**, which requires the scope — *"claude-ui emits **section-scoped edits`

The named section is `docs/triad-loop.md:115–139` (and its harness counterpart at the same offsets).
A grep of **both copies** for `§11`, `Reviewer-authoring` and `surgical edit` returns **no hits in
either**; the block's only outbound reference is the file preamble at `:6`, which names
`milestone-methodology.md` generally and not §11.

**This is one content gap present in both copies, not a drift between mirrors.** Re-verified at
HEAD: `diff -q` exits 0, `md5 2bd1afbcf7ad82ebbccce647505ffbfa`,
`sha256 cd8d675293be114c43047625ddc54e1b2e1ff6fff59352c0c9bbce1521a27112`, **188 lines / 8802 bytes**
on both.

**Landing order is CROSS-REPO, HARNESS-FIRST**, per hc decision 6 and the manifest's own
designation. `docs/project-knowledge-manifest.md:53–55`:

> `> `methodology--triad-loop.md`: the harness copy is canonical. A byte-identical`
> `> mirror lives at `aetheris-agents/docs/triad-loop.md`; keep them in sync, edit`
> `> the harness copy. `milestone-methodology.md` is single-copy in the harness repo.`

So: (1) harness canonical edit to `../aetheris/docs/methodology/triad-loop.md`; (2) agents mirror
sync of `docs/triad-loop.md`; (3) the manifest's standing `diff -q` mirror-pair check re-run and
its result published, per `docs/project-knowledge-manifest.md:76–79`, which states that
`drift_check` **cannot** see this class and the `diff -q` is the only thing that catches it.

**Contract refs.**
- `docs/project-knowledge-manifest.md:53–55` (canonical designation) and `:76–79` (the mirror-pair
  check and drift_check's blindness to this class).
- `hc-consolidation.md:583` — decision 6, cross-citing repo pair lands together, harness first.
- `aetheris/CLAUDE.md` — **Cite by anchor with the line number as a parenthetical**; the corrected
  citation names its section, not a line.
- `aetheris-agents/CLAUDE.md` §Definition of done — doc sync.

**Touches.**
- `docbuilder/docs/m4-milestone.md` (the `Contract refs` bullet at `:409–410` only)
- `../aetheris/docs/methodology/triad-loop.md` (canonical; the *Doc edits are section-scoped*
  section only)
- `docs/triad-loop.md` (mirror; sync only, byte-identical to canonical after the edit)
- `docs/project-knowledge-manifest.md` (**only if** the mirror-pair check's result is recorded
  there; the row's commit column is an export-boundary concern and is **not** in scope)

**Do not generate.** No re-ordering or re-numbering of `milestone-methodology.md`'s sections — the
methodology's own §11 preamble (`:306–308`) states the position is chosen because four documents
cite §9 and §10 by number. No edit to §11 entry 2 itself; the gap is the missing reverse pointer,
not the entry. No other citation in `docbuilder/docs/m4-milestone.md` touched.

**Runbook update rule.** Not engaged.

**Done-check.**
```bash
# 1. The corrected citation resolves: the quoted string is in the section now cited.
grep -n "Recovery sessions are where" ../aetheris/docs/methodology/milestone-methodology.md
grep -n "milestone-methodology.md.*§8" docbuilder/docs/m4-milestone.md

# 2. The reverse pointer reads out of the CANONICAL file, quoted with its
#    surrounding lines — from the file, never from the packet.
grep -n -A3 -B3 "§11" ../aetheris/docs/methodology/triad-loop.md

# 3. Mirror-pair check, the manifest's standing check and the only thing that
#    catches this class. Must exit 0 and the checksums must match.
diff -q docs/triad-loop.md ../aetheris/docs/methodology/triad-loop.md
sha256sum docs/triad-loop.md ../aetheris/docs/methodology/triad-loop.md

# 4. Doc-sync gate, post-commit (check 8 reads committed history).
python3 scripts/drift_check.py --strict

# 5. Nothing outside Touches changed.
git -C ~/sandbox/elixirws/aetheris-agents status --porcelain
git -C ~/sandbox/elixirws/aetheris        status --porcelain
```

**Claude-code prompt.**
> Make the two pointer edits scoped above and nothing else. Both defects are re-verified at
> `aetheris-agents 160da89` / `aetheris 6bc49fc`; **re-verify both at HEAD before editing** and
> report any divergence rather than following this text (§11 entry 4). Land the `triad-loop.md`
> pair harness-first and hold both pushes for review. Quote the unit at HEAD before replacing it
> (§11 entry 2 — the rule this ticket exists to make readable from the other side). Run the
> done-check and include its full output in the packet; the `drift_check --strict` run goes
> **after** the commit, and name the expected `project_knowledge` staleness WARNs rather than
> chasing them.

---

### t3 — the stale-gate correction sweep, and the rows this round defers

**Scope — two arms.** After this ticket every live-read stale gate claim t1 adjudicated has been
corrected in the artifact that carries it, in the shape that artifact's kind requires; and every
finding this round defers carries a backlog row rather than prose. Nothing t1 adjudicated archival
is touched.

**Arm 1, the corrections.** Every live-read stale gate claim in t1's adjudication table — five in
id form — plus the one description-form claim t1 surfaced in the current round document. Six
sentences across three destinations:

| # | destination | claim | referenced row (closed) |
|---|---|---|---|
| 1 | `cloudcost/runbook.md:619–620` | *"Before provider four, / read **BL-074** — the seam sweep…"* | BL-074 (2026-08-07) |
| 2 | `../aetheris/ROADMAP.md:52` | *"Must land **before** BL-007 so fork ships with a causal-tree view"* | BL-007 (2026-07-20) |
| 3 | `../aetheris/ROADMAP.md:109–112` | *"**E4 — BL-003 promoted to prerequisite** (already Active) … just a gate: E-cluster is not done until BL-003 is."* | BL-003 (2026-07-15) |
| 4 | `cloudcost/m5-n1-compose.md:30` | *"→ **m5 t2** → BL-132 → provider four."* | BL-132 (2026-08-11) |
| 5 | `cloudcost/m5-n1-compose.md:1226` | *"**Sequence from here:** BL-132 → provider four…"* | BL-132 (2026-08-11) |
| 6 | `cloudcost/m5-n1-compose.md:852–856` (description form) | *"provider four is gated on the cycle's **seam sweep** and the **harness round**"* | BL-074 (2026-08-07); BL-105 + BL-106 (2026-08-09) |

**Establish the correction shape PER DESTINATION before editing any of them.** Do not assume one
shape covers all three kinds.

- **Live operational guidance** (`cloudcost/runbook.md`). hc decision 8 is reported to require
  in-place correction — `hc-consolidation.md:585`. **Verify it**, and **verify separately whether
  hc's decisions bind harness-side files at all**, since the harness destinations
  (`../aetheris/ROADMAP.md`) are in a different repo from the document that ratified them. If they
  do not, **report what governs there and stop before editing the harness files.** Note for that
  check, offered as a lead and not as a finding: the hc round's own tickets edited harness files,
  which bears on the question but does not settle it — read the round document, not this sentence.
- **The closed round document** (`cloudcost/m5-n1-compose.md`). m5's own correction practice is
  reported to be a stamped superseding block that leaves the original sentence unrewritten, under a
  numbered decision. **Verify that decision and its shape, and apply it.** Do not rewrite m5's
  sentences in place unless the decision you find says to. Lead, to be verified rather than
  followed: m5 itself distinguishes the two decisions at `cloudcost/m5-n1-compose.md:503–510`,
  where a paragraph that was *"neither"* a closed record nor live guidance was corrected in place
  with the superseded wording quoted — read that passage before choosing, because item 6 above sits
  inside an `[OPEN]` §Not established item and may be that third case.
- **The ROADMAP entries** (`../aetheris/ROADMAP.md`). Entry 3 carries a **stale parenthetical about
  the gating row's own state** — *"(already Active)"* at `:109` — alongside the stale gate clause at
  `:112`. **Both halves are in scope**; correcting one and leaving the other is the shape this round
  exists to close.

**For every correction: quote the unit at HEAD, then replace the unit**, per
`../aetheris/docs/methodology/milestone-methodology.md` §11 entry 2. Naming sentences from memory
is the failure that entry records.

**Arm 2, the rows.** File one backlog row for each finding this round defers — five, from t1's own
§X.1 and §X.4:

| # | the finding |
|---|---|
| a | The backlog's two disagreeing status surfaces — row bodies and the `## Suggested order` ✔ table — and the fact that nothing in the file says there are two |
| b | The row whose status marker is a quotation of a different row's disposition, which any marker-keyed extraction misreads |
| c | Absence of a reachability stamp encoding three different dispositions, with two of the verdicts living only in an implementation-notes file (**D5**) |
| d | The adapter obligations t1 found stated with no exemplar and no verdict in the contract file, which a fourth adapter's author would meet first |
| e | The two senses of *live* (**D2**), which two live documents currently use incompatibly |

**Each row per the backlog's own row convention** — establish it by reading neighbouring rows; do
not import a shape from this ticket. **No row states a fix; each states the question.**

**Contract refs.**
- `hc-consolidation.md:585` — decision 8, live operational guidance is corrected in place.
- `hc-consolidation.md:584` — decision 7, a closed record gets a dated superseded note.
- `hc-consolidation.md:587` — decision 10, the live/archival test; the basis for D2.
- `../aetheris/docs/methodology/milestone-methodology.md` §11 entry 2 — quote the unit, then
  replace the unit.
- `aetheris-agents/CLAUDE.md` §Learning — BL-007 — *A deferred finding gets a backlog row in the
  same round it's deferred*, and its closing clause: the row must be one that stays open.
- `aetheris/CLAUDE.md` — *An artifact's kind decides how a correction is made; its push state
  decides only whether the correction may be silent.*
- **D2**, **D4**, **D5** in this document.

**Touches.** Repo-qualified from repo state; every path verified to resolve at
`aetheris-agents 160da89` / `aetheris 6bc49fc`.
- `cloudcost/runbook.md` — arm 1, destination 1
- `../aetheris/ROADMAP.md` — arm 1, destinations 2 and 3 (**harness**)
- `cloudcost/m5-n1-compose.md` — arm 1, destinations 4, 5 and 6
- `docs/backlog-2026-06.md` — arm 2, the five rows

Every file named in t1's adjudication table appears above; none is absent.

**Do not generate.** Any correction to a document t1 adjudicated archival — in particular
`cloudcost/m4-consolidation.md` (**D2**), `cloudcost/m3-milestone.md` and
`docs/handoffs/handoff-m3-close-2026-08-05.md`. Any row for a finding t1 did not raise. Any edit to
`cloudcost/milestone.md` §Contracts.

**Runbook update rule.** Engaged for `cloudcost/runbook.md` only, and satisfied by arm 1 itself:
the correction *is* the runbook edit. No new environment variable, startup step, configuration key
or command semantics is introduced.

**Done-check.**
```bash
# 1. Every corrected sentence reads back out of its own file, with surrounding
#    lines, from the file and never from the packet — §7's verification step
#    applied to a sweep. Six destinations; print each.

# 2. The rows exist and are open. Print each new row's heading and confirm it
#    carries no closure marker — a finding filed inside a row that closes in the
#    same commit has a record, not an executor.
grep -n '^### BL-' docs/backlog-2026-06.md | tail -8

# 3. Re-run t1's census over the six corrected destinations only. Each must now
#    return zero stale gate claims; publish the pattern and a positive control
#    proving the pattern still fires elsewhere. A zero without a control is an
#    observation about the command.

# 4. The offline spine — this ticket changes no executable line. Re-resolve both
#    anchors at HEAD first. A differing count is a finding, not a pass.
python3 -m pytest cloudcost/tests/ -q

# 5. Doc-sync gate, POST-commit (check 8 reads committed history).
python3 scripts/drift_check.py --strict

# 6. Nothing outside Touches changed.
git -C ~/sandbox/elixirws/aetheris-agents status --porcelain
git -C ~/sandbox/elixirws/aetheris        status --porcelain
```

**Claude-code prompt.**
> Run t3's two arms in order, arm 1 then arm 2. **Establish the correction shape per destination
> before editing any of them** — the ticket names three kinds and one lead per kind, and every lead
> is to be verified rather than followed. **If hc's decisions turn out not to bind harness-side
> files, report what governs there and stop before editing `../aetheris/ROADMAP.md`**; land the
> agents-side corrections and say plainly that the harness half is held. Quote the unit at HEAD
> before replacing it. File the five rows per the backlog's own convention, read from neighbouring
> rows; each row states the question, not a fix. Hold all pushes. Run the done-check and include
> its full output; item 5 goes after the commit, and name the expected `project_knowledge`
> staleness WARNs rather than chasing them.

---

## Not established

Per R21, each entry states its kind. This section carries no total; read each item's own prefix.

1. **`[RESOLVED]` (b)** **Whether a records round of this kind is "the next cycle" for the deferred
   `mix dialyzer` trigger.** `cloudcost/m5-n1-compose.md:1165–1167` defers dialyzer on the trigger
   *"the next harness ticket whose `Touches` names any `.ex` or `.exs` file runs it; and if no such
   ticket runs before the next cycle's close, that close runs it."* No ticket in this round names
   any `.ex` or `.exs` file in its `Touches`, so arm 1 is not engaged; whether this round's close
   is "the next cycle's close" and therefore owes the run under arm 2 is not settled by anything
   read. **Settled by:** a ruling on what counts as a cycle for that trigger. **No owner** — the
   trigger is m5's and this round did not author it. Evidence gathered and reported, not ruled;
   see the round's t1 packet, §Addendum C.

   > **`[RESOLVED 2026-08-11 at the t1 review, by D1.]`** The item named its settling route — *"a
   > ruling on what counts as a cycle for that trigger"* — and that ruling has been made. **D1: this
   > round's close runs `mix dialyzer`**, on m5's own usage of *the next cycle* as the round that
   > opens and reads §Open for the next cycle, and on the ground that an arm 2 firing only for
   > code-touching rounds is arm 1 restated and leaves the deferral with no backstop.
   >
   > `[The prefix changed in place, `[OPEN]` → `[RESOLVED]`, and the kind letter (b) is kept: the
   > item was a carried unknown whose settling route named no owner, and resolution is a state, not
   > a fourth kind. The original text above stands unrewritten, per decision 7. Shape taken from
   > `cloudcost/m5-n1-compose.md:869–889`, which is the in-repo precedent for resolving an item of
   > this kind in place.]`

---

## Promotion candidates

Recorded here and disposed at this round's close, per §Close criteria clause 7. Authored by the
reviewer at the t1 review.

- **A round whose first ticket runs in the session that creates the round document has no
  reviewable ticket anatomy.** R12 requires a ticket's §6 anatomy to land before the ticket opens;
  a round that is born and executes its first ticket in one session satisfies the letter — the
  anatomy is written first — while giving no reviewer the interval the rule exists to create. One
  instance, this round's own t1, ratified as a one-off at D3. Carried, not promoted.
- **Two documents can use one word in incompatible senses and neither is wrong.** *Live* means
  unretracted-at-HEAD in the current round document and read-for-current-guidance under hc decision
  10. t1 surfaced the collision as a contradiction between two documents; it is an equivocation, and
  the instrument that found it — a census cross-joining claims against current state — cannot tell
  the two apart. Carried, not promoted; see D2.
- **A five-instance positive control caught a defect suppressing a fifth of the class.** t1's
  subset check held five known instances; four passed under the defective pattern and the fifth did
  not, and the delta on fixing it was large — verify and record the two hit counts from t1's own
  record. A control set sized to what a prior packet happened to name is not sized to the method's
  error rate. Carried, not promoted: one instance, and the round has no second census to test it
  against.

> `[Verified and recorded at the t1 review, 2026-08-11, per the third entry's own instruction. The
> two hit counts from t1's record: the defective pattern (`[^.\n]{0,N}`, which forbids the gate
> relation from crossing a sentence boundary) returned **504** hits; the corrected pattern
> (`[^\n]{0,N}`) returned **640**. Delta **+136**, which is **21.25%** of the corrected total. The
> instance the five-member control caught is `cloudcost/m4-consolidation.md:362`; the other four
> members passed under both patterns.]`

`[Two entries appended 2026-08-11 at the t2 review. They sit below the bracket above because that
bracket is bound to the third entry and names it; moving it would leave it reading as though it
were about the fifth.]`

- **A reverse pointer that restates the rule it points at is a second copy of that rule.** t2's
  reverse pointer landed with a précis of the entry it names, inside a file that is a mirrored pair
  — so a later amendment to that entry would leave a stale restatement in two places, and nothing
  would catch it: the mirror check compares the copies to each other, never to their source. Caught
  at the t2 review and trimmed to the relation alone. One instance. Carried, not promoted.
- **A discrimination required of one ticket is not required of its sibling unless the reviewer
  writes it twice.** t3's body requires the live/archival test per destination; t2's does not, and
  t2 had a destination of the same kind — established at the t2 review rather than before it. The
  gap is in the authoring, which is what §11 governs. One instance. Carried, not promoted.

---

## Close criteria

Authored by the reviewer at the t1 review.

1. t1's census is ratified and its method record is re-runnable as printed — patterns, tokens,
   per-class counts, and the controls with their published values.
2. t2 has landed harness-first per hc decision 6: harness canonical, then the agents mirror, then
   the manifest's standing `diff -q`, recorded byte-identical at the end.
3. t3 has corrected every live-read stale gate claim t1 adjudicated, each in the shape its
   destination document requires — established per destination, not assumed uniform. For m5 §Not
   established item 1 that shape is a dated record that the gate its two statements describe is
   discharged; **its `[OPEN]` prefix is not flipped**, m5 being a closed round. Whether that record
   is a decision-7 superseding block or the third case m5 itself names is established at t3, not
   presumed here.
4. Every finding this round defers carries a backlog row, per the agents-side deferred-finding
   rule, and the rows are named here by id at the close.
5. `mix dialyzer` has been run at this close per D1. Its command, exit status and output are
   recorded, with any elision named.
6. The offline suite is green at the figure the m5 round pinned, and no executable line changed
   anywhere in this round. Verify and record both.
7. §7's ritual has been performed per the methodology, including a disposition on every entry in
   §Promotion candidates. Per §Carried in item 4, an entry promoted out of §Promotion candidates is
   compared against the candidate it came from — not only read out of its destination file — and the
   comparison is recorded.

> `[Clause 3 amended 2026-08-11 at the t2 review. **What changed:** the original required that
> *"m5 §Not established item 1 is resolved rather than carried forward again"*. **Why:** that
> presumed a resolution shape a closed round does not admit. m5 closed 2026-08-10, and hc
> decision 7 governs a closed record — a dated superseding note, original text not rewritten — so
> the item's `[OPEN]` prefix cannot be flipped the way this round's own §Not established item 1
> was. What is reachable is a dated record that the gate is discharged, and which shape that record
> takes is left to t3 rather than presumed here. The clause's other requirement — per-destination
> establishment — is unchanged in substance and re-worded from *per document* to *per destination*,
> since one document carries three of the six claims.]`
