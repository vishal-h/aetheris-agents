# m4-consolidation — the cycle document

> Not a feature milestone. This cycle clears accumulated infrastructure debt in the cloudcost
> sprint case and the shared scripts, so that the decision about a fourth provider is made against
> working apparatus rather than on top of it. Created after two tickets had already closed,
> because the cycle opened without one — see §Why this exists.

> This is the m4 entry in the cloudcost series (`milestone.md`, `m2-milestone.md`,
> `m3-milestone.md`), named for what it is rather than to the series pattern. A sweep looking for
> `m4-milestone.md` will not find it.

**Status:** open. **Opened:** 2026-08-05 (first move ratified). **Document created:** 2026-08-06.
**Repos:** `aetheris-agents` and `aetheris` (harness). **Preceding cycle:** m3-cloudcost, closed
2026-08-05.

---

## Why this exists

The cycle's first move was explicitly *not* a milestone doc. That was right at the time — the work
was a backlog batch, not a feature milestone — but it meant the ticket set, the ratified decisions
and the sequence lived only in conversation. Two tickets closed that way.

**BL-102 is the standing row for this exact gap**: the complete-but-unmarked sweep at a close reads
a milestone doc's done-when table, and a batch has none. This document is that artifact for this
cycle, and §Close criteria states what a sweep of it reads.

The decision log below is the part with no other source. Everything else is recoverable from the
repos; the decisions were not.

---

## Scope

**In scope.** The cloudcost sprint case in `../aetheris/scripts/sprint.sh`; the four shared scripts
under `cloudcost/scripts/` — **`detect_orphans.py`, `_normalized.py`, `compose_report_data.py`,
`render_report.py`**; the documents that describe either; the backlog rows covering them.

> **Enumerated 2026-08-06 (t1b review r1).** "The four shared scripts" was an unenumerated count
> in a directory holding **eight** `.py` files, which is the *"the one X"* tell — in the document
> that holds this cycle's decisions. It names the **provider-agnostic** subset, and BL-074's
> Scope paragraph is the authority: it sweeps exactly these four and calls them *"shared
> machinery"*. The other four — `fetch_aws.py`, `fetch_do.py`, `fetch_linode.py` (adapters) and
> `detect_optimization_signals.py` — are not shared machinery and were never what "the four"
> meant. t1b pinned all eight by blob hash rather than guess, and all eight are byte-unchanged.

**Not in scope, and deliberately so.**

- **The harness `--json` contract** — BL-105 and BL-106. Found during this cycle and the most
  consequential thing in it, filed rather than pulled in. Scheduled as its own round; see §Sequence.
- **Provider four.** Gated on this cycle's seam sweep and on the harness round.
- **Any §Normalized extension.** BL-098 remains filed; extending the contract belongs with the
  provider that needs it, not before.

---

## Ratified decisions

Every entry is a decision taken in this cycle that no other document records. Dated; the arbiter
ratified all of them unless marked otherwise.

### How the cycle is run

| # | Decision | Date |
|---|---|---|
| 1 | **The reviewer asserts no checkable specifics in specs it authors.** Anchors only; where a value is needed the ticket says *verify and record*. | 2026-08-05 |
| 2 | **A claude-code verification pass runs over any reviewer-authored doc before ratification**, not after. | 2026-08-05 |
| 3 | **A step-1 gate inside the ticket.** Verification conditions the implementer checks before writing; any failure stops without an edit. Allowed once as an exception, retained as practice after it stopped a ticket whose census had not converged. | 2026-08-06 |
| 4 | **Ticket names are historical and are not tidied.** `t1a`, `t1a-p`, `t1b` are cited in committed documents in both repos. | 2026-08-06 |
| 5 | **The §7 promotion runs mid-cycle when the rules bind the cycle's own remaining tickets**, rather than waiting for the close. | 2026-08-06 |
| 6 | **Pushes are held for review; a cross-citing repo pair lands together**, harness first so the agents citations resolve on the remote. | standing, reaffirmed |

### Document handling

| # | Decision | Date |
|---|---|---|
| 7 | **A closed record gets a dated superseded note; its original text is not rewritten.** | 2026-08-06 |
| 8 | **Live operational guidance is corrected in place.** A superseded note on a how-to leaves wrong instructions standing as the primary text. | 2026-08-06 |
| 9 | **Where liveness is genuinely undecidable, take the note.** Asymmetric: a note on a live document still delivers the correction; an in-place rewrite of a record falsifies it irreversibly. | 2026-08-06 |
| 10 | **A milestone-named document is a closed record if a current equivalent exists** — established, never inferred from the filename. | 2026-08-06 |
| 11 | **Content is authored by the reviewer; formatting belongs to the destination file.** | 2026-08-06 |

### Technical

| # | Decision | Date |
|---|---|---|
| 12 | **No planted cloud resources, on any provider.** BL-069 closes by retiring the practice, not by swapping fixtures. The live check becomes a rule-legibility assertion — that the adapter's inventory reached the catalog in a shape it could read — which is free and covers the seam that has historically produced defects. | 2026-08-06 |
| 13 | **Payload extraction, not stream splitting**, for the sprint's `--json` reads. Later re-grounded: splitting is not sufficient wherever the harness emits Logger output on stdout, which is every capture from 2026-07 onward; whether it sufficed in an earlier era depends on `[sandbox]` routing, which is unestablished. | 2026-08-06 |
| 14 | **The class is every `jq`-over-`--json` read**, not the `.status` reads alone. One shared extraction mechanism; leaving a sibling field broken on the adjacent line of the same helper is how the class regenerates. | 2026-08-06 |
| 15 | **BL-099's credential grep is written so that covering a second file is configuration, not a rewrite** — because a later harness round may split the streams, and the grep is the only thing blocking that. | 2026-08-06 |
| 16 | **The eduloka status extraction is out of scope** — same shape, different root cause, possibly working today. Filed as BL-108. | 2026-08-06 |

---

## Ticket set

Full §6 anatomy is authored per ticket at the time it starts, not here. This section records what
each ticket is for, its state, and what it carries.

Commit ranges are `first-commit^..head`, so each pastes into `git log` and returns the whole
ticket; the count states how many commits that is.

| Ticket | Subject | Rows | State |
|---|---|---|---|
| **t1a** | Correct the false `2>&1` causal claim in every standing carrier | BL-100 rescoped, not closed; filed BL-105–BL-109 | **Closed** — agents `6a2c012^..13eac9f` (5 commits), harness `9c676ef^..e6687f1` (2) |
| **t1a-p** | §7 promotion of the cycle's findings | none — the promotion is a `CLAUDE.md` edit, not a row | **Closed** — harness `e98448a^..f6fbd82` (2 commits), agents `0371d75^..009f666` (2) |
| **t1a-c** | This document | BL-102, answered for this cycle by §Close criteria | you are reading it |
| **t1b** | One extraction mechanism for `--json` output; repair the chaos gate | BL-100 **closed**, BL-107 **closed**; filed BL-110 | **Closed** — see §What this cycle established → *What t1b established* |
| **t2** | Retire the plant practice; rule-legibility assertion | BL-069 **closed by retirement**; BL-074 and BL-044 appended | **Closed** — see §What this cycle established → *What t2 established* |
| **t3** | Hermetic allowlist inversion; credential-grep generalisation | BL-104, BL-099 | not started |
| **t4** | The seam sweep; gates provider four | BL-074 | not started |
| **t5** | The report value pass, with the evaluated-versus-not-evaluated rider | BL-101, BL-070 | not started |

### What t1b inherits

Five items. The first four are method rather than scope; the fifth is an obligation t1a deferred
into t1b and is the reason this list is canonical rather than convenient — all cheap to state and
expensive to rediscover:

1. **Its behaviour-neutrality premise is refuted.** A converted site's *current* output depends on
   ambient run-store state, so "reproduce it exactly" is undefined. The check is that the helper
   yields the correct value on both clean and noisy captures.
2. **Census classification must distinguish assert from retract.** t1a seeded its own territory
   with retractions that quote the claim they retract; a term-match census now returns them as
   hits.
3. **The multiple-payload question is unsettled** — whether one invocation can emit more than one
   parsing JSON object, which decides whether "the last that parses" is the right selector.
4. **G1 states both forms** — level-with-origin before implementation, ahead-by-N-unpushed after.
   As first written it would have failed a correct tree.
5. **Two docbuilder documents are owed a note, deferred to t1b by t1a and due when the fix lands.**
   `docbuilder/milestone.md:88` and `docbuilder/docs/m1-milestone.md:680` carry byte-identical
   text — *"the underlying `no-json` label in sprint output is cosmetic noise — trace to the log
   line prefix in run.json format"*. Neither carries the `2>&1` claim, which is why t1a's census
   did not correct them, and an earlier draft that asserted they did would have written a false
   correction into a ticket about a false claim. The note must state both things: the **cosmetic**
   characterisation is false for the class, because one affected site is a gate; and the open TODO
   is discharged by the **fix**, not by a document edit. t1a deferred it rather than writing
   "discharged" in the same commit as the thing that would make it true — which leaves the
   obligation live, and recorded here because a closed ticket's implementation notes have no
   executor.

### What t2 inherits

One item, recorded here rather than left to be found mid-ticket:

1. **BL-069's Done-when and decision 12 disagree, and the row does not know it.** The row
   (`docs/backlog-2026-06.md:2182`) offers two ways to close — *"either a fresh DO orphan is
   planted, or the assertion is re-pointed to a recorded fixture rather than the live account"*.
   Decision 12 rules out the first outright and reframes the second as a rule-legibility assertion.
   **The row is edited at t2's opening, before any implementation**, so the ticket is not written
   against a Done-when the cycle has already superseded. This is §Close criteria item 4 discharged
   prospectively, which is cheaper than catching it at the close.

---

### What t3, t4 and t5 inherit

Two constraints, recorded at t2's close because both are known now and expensive to hit mid-ticket.

1. **Implementation notes take an `m4-` prefix, for every remaining ticket.** m1 wrote its notes
   unprefixed, so `cloudcost/docs/` already holds `t1-`, `t2-`, `t3-`, `t4-` and
   `t5-implementation-notes.md`. **t3, t4 and t5 each collide**; t1a, t1a-p and t1b escaped only
   because m1 had no ticket by those names, which is why the collision surfaced at t2 rather than
   earlier. Write `m4-t3-implementation-notes.md` and so on — the `m2-t1-` / `m3-t1-` series
   convention, already used by both preceding cycles. Decision 4 is untouched: the *ticket* is
   still `t3`. Do not rename m1's files to make room.
2. **This document belongs in every remaining ticket's `Touches` list.** t1b and t2 both edited it
   outside `Touches` and both declared the same deviation for the same reason — its §Ticket set row
   and §What this cycle established are duties no other document performs, and leaving a row
   reading "not started" after the work lands is false in its own commit. A deviation that recurs
   by design is a `Touches` omission, not a deviation.

## Sequence

t1b → t2 → t3 → t4 → t5 → **harness consolidation round** → **provider four**.

**The harness round runs before provider four**, and for the same reason the seam sweep does. BL-074
tells you whether the next adapter is mechanical on the agents side; BL-105 and BL-106 tell you
whether the apparatus a new provider lands on works. Every new provider adds a leg to the sprint
case, and a leg added to non-deterministic reads inherits the flakiness — m3 already paid that cost
three times.

**The harness round's shape:** BL-105 and BL-106 are one contract with two mechanisms and are
scoped together; **BL-077** folds in, because by then the chaos gate will have been repaired and its
real state — the input BL-077's known-red declaration needs and does not have today — will be known.

**Provider-four design work is not blocked by any of this.** The GitHub issue-doc is design-only and
touches no code. What the harness round buys is that *implementing* provider four lands on
apparatus that works.

---

## What this cycle established

Stated as findings, not as rules — the rules are in the two `CLAUDE.md` files and are not restated
here.

- **The sprint's `--json` reads are non-deterministic, not broken.** Identical expressions succeed
  or fail on ambient state. Across the captures in `../aetheris/sprint/`, the news set parses in
  **4 of 4**, payslip in **0 of 8**, cloudcost in **0 of 10** — same helper (`run_agent`), same
  `> file 2>&1` redirect.
- **The cause everyone had recorded was wrong.** The harness's Logger output shares stdout with the
  payload, so merging the streams is irrelevant to parseability. The claim had propagated into
  **six documents across both repos** as standing guidance (**seven sites**), with a further
  **thirteen** historical mentions left intact as dated records, and was refutable from the Rig
  source for the ten days before it was filed: `rig/src-tauri/src/commands/fork.rs:137` has read
  *"`mix` compile and log noise shares stdout and does not parse as JSON"* since `b5e8eee`
  (2026-07-26, BL-030), and BL-100's row was filed at `cdc8f08` (2026-08-05).
- **A gate in the chaos case has never evaluated its subject.** Its operand is a fallback token that
  the equality test cannot match.
- **`--json` emits no JSON on a non-success run**, so a programmatic consumer receives nothing on
  exactly the runs it most needs.
- **Two stream routings are now established:** Logger on stdout, worker output on stderr — a third,
  `[sandbox]` line routing, remains open below. This makes
  the harness fix and stream-splitting complementary rather than alternative, and is why decision 15
  exists.

### What t1b established

- **The class had four mechanisms, not one, and 29 members.** Derived fresh at t1b (no prior list
  inherited): 13 × `jq` over the output file, 5 × `tail -1 | jq`, 7 × `grep -o '"run_id":…' |
  tail -1 | cut`, 4 × `jq` over a `--json` *pipe*. All now call one helper. 13 further sites were
  classified out with reasons. Breadth check, recorded as a negative: `sprint.sh` is the **only**
  consumer of harness `--json` in either repo's scripts. *(First stated as 19; corrected at review
  round 1 — three converted sites were missing from the census table and the total rested on a
  bogus pairing step. Now derived two independent ways — censused reads and helper call sites —
  which agree at 29.)*
- **The chaos gate evaluates, and it passes.** `WARN status=no-json` → `OK … → :done (expected)`,
  both quoted from live runs on the pre- and post-edit trees. The gate line's comparison and both
  message texts are unchanged; only the operand became real. BL-107 closed without exercising its
  carried-red branch.
- **The first chaos output ever captured in this repo now exists.** It carries two resume warnings,
  an orphan-sweep line and two `[sandbox]` lines ahead of an intact payload — the noisy-store shape
  BL-107's premise assumed, confirmed rather than presumed.
- **A red gate was found off-territory and filed the same day** — BL-110, the payslip case's
  `BTL_999` assertion, which names a reference employee the run cannot produce because the
  orchestrator reads `payroll.csv` while `BTL/999` exists only in `sample_payroll.csv`. Same
  ambient-state defect class as BL-100, pre-existing, left red per the tracked-carry clause.
- **BL-069 remains armed and red**, named rather than re-triaged: the live cloudcost leg reported
  `[FAIL] orphan candidates: 0 (expected ≥1 …)`. t2 owns it.

### What t2 established

- **BL-069 closed by retirement — the third branch.** Its Done-when offered plant-or-re-point;
  decision 12 ruled out both as written. The ≥1-orphan assertion is gone, replaced by a three-arm
  rule-legibility check that imports `CANONICAL_TYPES` rather than restating it, sited **outside**
  the period guard on the D2 grep's precedent. Live, same leg, same day: `[FAIL] orphan candidates:
  0` at 18:25 → `[OK] rule legibility: 18 resources evaluated, 0 skipped` at 18:29. All arms
  mutation-checked, the two failing ones against real artifacts rather than invented fixtures.
- **The run's coverage is not knowable from any artifact the sprint can read, and the check that
  looks like it establishes it does not.** The inventory envelope is five keys and carries no
  `not_inventoried` (BL-098); the adapter's summary, which does carry it, appears in **0 of 13**
  archived `sprint/*/cloudcost/run.json` captures. And the orchestrator-exit assertion cannot
  discharge it either: `mix aetheris` discards every command's exit code (BL-044, verified at
  harness `871a720`), so that assertion is reachable only when the Mix task *raises* — a run that
  ends `:failed` prints `[OK]`. Appended to BL-044 as audit input. This is why the not-applicable
  arm reports an **unknown** rather than a clean zero, a declared deviation from the ticket's
  wording.
- **The retirement census found the claim in one repo only, and mostly in prose that never says
  "plant".** `../aetheris` carries exactly one carrier (the assertion itself); `../aetheris/CLAUDE.md`
  carries none. On the agents side the live carriers were the runbook's recipe section, three
  handoff "Live tripwires" blocks, three closed milestone documents — one of them reading
  `Status: PENDING`, an instruction awaiting execution rather than a record — and **`CLAUDE.md`'s
  own gate rule**, which offered planting as the exemplar of correct known-red discipline. That
  last one is the site a token-keyed census would have found and a reader would have trusted most.
- **The BL-077 placement residual did not arise.** Recorded as a negative: the assertion sites
  outside the period guard, so the skipped-assertion-indistinguishable-from-passing finding gains
  no second instance from it.

### Rows filed this cycle

Read from `docs/backlog-2026-06.md` at agents `009f666`:

| Row | Subject, as the row heading states it |
|---|---|
| **BL-105** | `--json` mode's payload shares stdout with the harness's Logger output |
| **BL-106** | `--json` emits no JSON document on a non-success run |
| **BL-107** | the chaos-case gate has never evaluated its subject |
| **BL-108** | the eduloka sink gate parses a merged stream: same shape, different root cause |
| **BL-109** | two `milestone-reference.md` files, canonical by different measures |

**BL-100 rescoped, not closed.** Heading, cause, scope, fix and Done-when revised under a dated
*"Rescoped and corrected 2026-08-06 (t1a)"* note, each change marked `[corrected 2026-08-06]` with
the superseded text kept beneath, and **Size raised XS → S–M**. The fix has not landed; t1b carries
it.

### Rules promoted this cycle

Three, at t1a-p. **Named here, not restated** — they are normative in the files below and a copy
here would be a second source of truth.

- `../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns — the truth-maker rule, with its
  two operational forms.
- `../aetheris/CLAUDE.md` §Continuous learning → Silent-wrong-answer — the command-binding carrier.
- `CLAUDE.md` (agents) §Learning — BL-007 — the packet rule, superseding its earlier wording.

---

## Not established

Carried forward rather than resolved. Each is a question this cycle opened and did not close.

- `[sandbox]` line stream routing. The available test command spawns no worker.
- Which document first carried the false causal claim — three harness documents acquired it on one
  day and same-day ordering is not recoverable.
- ~~Whether the step-count diagnosis in an m09→m10 handoff is correct.~~ **Resolved 2026-08-06
  (t1b review r1): it is wrong, and the ordering is recoverable.**
  `../aetheris/docs/aetheris/milestones/handoff-m09-m10.md.md:145` says step counts show `n/a`
  *"because the script reads step count from `--json` run output but it's not in that payload.
  Fix: read from `mix aetheris inspect <run_id>`."* `extract_step_count` **already read from
  `mix aetheris inspect`** — that line landed at `fafa17f` (2026-05-16 12:40 +0530) and the claim
  text was written at `2a5dc59` (2026-05-17 09:58 +0530), **21 hours later**. So this is not a
  diagnosis later superseded; it prescribed a fix that was already in place. Unlike the false
  causal claim, same-day ordering did not have to be guessed here.
  **The actual cause was the same one this cycle has been chasing**: both of the function's reads
  were contaminated — `.run_id` from the merged run file, and `.step_count` from a
  `mix aetheris --json inspect` *pipe*, which carries Logger output exactly as a file does. t1b
  converted both (Group A `:79`, Group D `:81`). Verified live against the post-edit chaos capture:
  `extract_step_count → 2 steps`, against a `max_steps: 2` run.
- Whether the chaos gate has ever run in a clean-store environment. No chaos output had ever been
  captured, so "it has always warned" was inference. **Partly resolved 2026-08-06 (t1b):** the
  first chaos capture in this repo (`../aetheris/sprint/20260806_172144/chaos/maxsteps.json`)
  exists and *did* warn, in a noisy-store environment — so the behaviour is now observed rather
  than inferred for that case. **The clean-store question itself is still open**: no chaos run has
  been made in a clean store, and nothing in t1b established what one would have done.
- Whether `EDUX_DATABASE_URL` is set in the sprint's ambient environment — decides BL-108.
- Which `milestone-reference.md` survives — BL-109.
- ~~Whether one `--json` invocation can emit more than one parsing JSON object — t1b's carry 3.~~
  **Resolved 2026-08-06 (t1b), both from source and from the record.** Yes, but for exactly one
  command: `fork`. `Formatter.print/2` is called once per invocation
  (`../aetheris/lib/aetheris/cli/main.ex:46`) and is one of only two `IO.puts(Jason.encode!(…))`
  sites in `lib/`; the other is `Fork.emit_fork_started/2`
  (`../aetheris/lib/aetheris/cli/commands/fork.ex:71`), whose own comment names it as the only
  command writing to stdout before dispatch returns. It writes the early document **first** and
  the result **last**, so "the last that parses" remains the correct selector, and `sprint.sh`
  never invokes `fork`. Empirically: of **319** files under `../aetheris/sprint/`, **zero** carry
  more than one parsing JSON object (219 exactly one, 100 none). Recorded in
  `../aetheris/docs/aetheris/claude-notes.md`, which previously carried this as the scan's one
  unresolved case.

---

## Open for the close

Decisions the close must **take**, as distinct from §Close criteria below, which lists reads it
must **perform**.

1. **Whether the step-1 gate becomes standard practice rather than per-ticket.** Decision 3
   admitted it once as an exception and retained it for this cycle's tickets; nothing makes it
   standing, and every ticket since has restated it in its own text.

   *The evidence for asking.* Claims that reach past what their author could check recurred
   throughout this cycle, most often in the documents written to correct them, and on both sides
   of the loop rather than only the implementer's. Instances that resolve in committed artifacts:
   `docs/reviews/t1a-review.md` §"The reviewer's closing observation" (`:56–63`) records four
   inside t1a alone; `cloudcost/docs/t1a-p-implementation-notes.md` §3 records one in t1a-p's own
   promotion `Source:` line, caught before commit, and one in edit C's citation, corrected at
   round 1. **Further instances are observed rather than recorded** — several occurred in review
   packets, which are session artifacts and not in either repo — so the full set has never been
   enumerated, and no count of it appears here. Enumerating it is work for the close if the close
   wants a number; the pattern does not depend on one.

   *What would settle it either way.* The reviewer records catching one such claim in their own
   draft before it landed — the first time in this cycle the defect was stopped by its author
   rather than by a gate or a round. A gate that becomes standard is an admission that authorship
   alone has not been sufficient; a run of tickets where authors catch their own would be the
   evidence for not making it standing.

   *A second face of the same question: **the last change of a ticket is never reviewed.*** The
   loop's closing instruction has been *apply and close, then push*, so every round's dispositions
   land unreviewed by construction — including the ones that correct a review finding. The trade
   has been made deliberately several times this cycle and judged right each time; the alternative
   is a round-trip per one-line fix. But it is a trade, and it is the same shape as the gate
   question: **where the discipline sits — before the edit, or after it.** At t2 it had teeth
   twice. The r1 marker was itself wrong and was caught only because r2 read it; and had r2 not
   run, the r1 dispositions — a `CLAUDE.md` edit among them — would have shipped unread. Recorded
   here so the close weighs it rather than meeting it as a surprise.

2. **Whether *match structured data by field, not by substring* is worth promoting.** Carried to
   the close rather than acted on, per the t2 review.

   *The evidence.* Twice in this cycle a defect was caught by **implausibility rather than by a
   check**, and both would have passed had the wrong answer been plausible. At t1a-p a verification
   step running with a persisting `cd` compared one repo's `CLAUDE.md` against itself and reported
   every phrase present in both files — caught only because a phrase cannot be in two files at
   once. At t2 a `grep -qF` over `docs/project-knowledge-manifest.md` reported
   `cloudcost/runbook.md` and `cloudcost/m3-milestone.md` as manifest-tracked; it was matching the
   `docs/rig/runbook.md` and `docs/aetheris/runbook.md` rows, and it was caught only because check
   8 staying silent about a file just edited was implausible. Had the manifest happened to track
   the runbook, the same broken grep would have returned the right answer and taught nothing.

   *Why it may not need its own rule.* This is the same family as the **command-binding** carrier
   already promoted under Silent-wrong-answer (*a check that reads the wrong thing reports a clean
   result, not an error*) — the manifest case is that rule with a table column in place of a repo
   path. The close decides whether the substring-vs-field form is a distinct enough carrier to name,
   or whether naming it dilutes the rule it belongs to.

3. **What governs durable instruction surfaces outside git.** The cycle has no standing answer, and
   **BL-111** is the row that will need one.

   *The evidence for asking.* t2's retirement census was correct and complete over both repos and
   still missed the stalest carrier of the practice it was retiring, because that carrier —
   this project's session memory — is in no repo. It is per-project-directory, unversioned, partly
   loaded into every session by instruction, and **13 of its 22 files are typed `feedback`**, which
   its own schema defines as guidance on how to work. So it is normative, durable, and reachable by
   no census, review, gate or drift check. Every other travel-failure this cycle has closed —
   BL-007's packet channels, the handoff-is-not-a-promotion finding — concerned content that at
   least *existed in a repo*.

   *What the close has to decide, and what it must not decide first.* Whether such a surface is a
   private scratchpad whose staleness is nobody's problem, or an untracked normative document that a
   retirement, a promotion or a correction owes an update. Only after that ruling does a mechanism
   make sense — "export it into the repo", "grep it in the census", "keep normative content out of
   it" answer three different rulings, and choosing one early creates a second surface to keep in
   sync. BL-111 is written to characterise, not to fix, for exactly this reason.

---

## Close criteria

This cycle is done when t1b through t5 have closed with zero blocking findings, the drift checker
reports zero FAIL and no unexplained WARN, and the milestone-end ritual has run.

**What a close sweep of this document reads** — the answer BL-102 asks for, for a batch that has no
done-when table:

1. Every ticket in §Ticket set, checked against the backlog rows it closes. A row closed in the
   repo and open here, or the reverse, is the defect the sweep exists to catch.
2. Every row in §Rows filed, checked for a DONE section if it closed.
3. §Not established, item by item: resolved, still open, or superseded — and if resolved, where.
4. The decision log, for any decision the implementation diverged from. A divergence is closed by
   changing the code or the decision, never left silent.
5. §Rules promoted, read out of the two `CLAUDE.md` files rather than trusted — a promotion is
   complete only when the entry can be read where it lives.

`Source: this cycle, 2026-08-05 to date. Decision log authored by claude-ui from the cycle's own
ratifications; repo-state sections composed by claude-code at aetheris-agents 009f666 /
aetheris f6fbd82.`
