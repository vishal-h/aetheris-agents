# hc-consolidation — the cycle document

> Not a feature milestone. This round clears the harness-side apparatus debt that the
> m4-cloudcost cycle found and deliberately did not pull in: the `--json` contract, the
> sprint's exit contract, and the retention gap under both. Created at the round's second
> ticket, because the first was a read that by design produced no repo artifact.

> This is the `hc` round. Its predecessor is `cloudcost/m4-consolidation.md`, which is a
> cloudcost-series document; this one is not, and a sweep looking under `cloudcost/` will
> not find it. Named for what it is: milestone `hc`, subject `consolidation`.

**Status:** **OPEN** — hc-a, hc-b and hc-c closed; **hc-d opened 2026-08-09 and stopped at its
step-1 gate**, and reopens against the anatomy this edit lands. **Opened:** 2026-08-08.
**Document created:** 2026-08-08 (hc-b). **Repos:** `aetheris-agents` and `aetheris`
(harness). **Preceding cycle:** m4-cloudcost, closed 2026-08-08.

---

## Why this exists

hc-a was this round's scoping read: read-only by design, no commit, no repo artifact. It
produced the ruling questions, a naming decision, and the finding that the work it scoped
cannot be one ticket. All of that lived only in conversation until this file.

**BL-102 is the standing row for exactly that gap** — the complete-but-unmarked sweep at a
close reads a milestone doc's done-when table, and a batch has none. m4-consolidation was
written to be that artifact for its cycle; this is the same artifact for this one, and
§Close criteria states what a sweep of it reads.

The decision log below is the part with no other source. The repo recovers everything else.

---

## Scope

**In scope.**

- **The harness `--json` contract** — **BL-105** (the payload shares stdout with Logger
  output) and **BL-106** (`--json` emits no JSON document on a non-success run). One
  contract, two mechanisms; the rows declare themselves siblings and are taken as one.
- **The sprint exit contract** — **BL-077**. `fail()` is a printer, so a sprint whose
  assertions all fail exits 0.
- **BL-133 face 2** — the sprint's console output is retained nowhere, so no past run's
  greenness is checkable after the fact.
- **I0** — the harness copy of the repos rule, widened. Landed at harness `b4d782a`.

**Not in scope, and deliberately so.**

- **BL-075 / BL-054's fix.** R4. The fix is a polling rewrite of fixed-ms windows in the
  test suite — a different verification shape from sprint apparatus — and the fold alone
  closes neither row. **R1 nonetheless discharges BL-075 arm 2's blocker**; see §Not
  established and R4.
- **BL-108.** R10, decided freshly rather than inherited. A status-extraction defect in a
  different case with a different root cause; taking it means auditing a second use case's
  semantics inside a ticket about the sprint's exit contract.
- **BL-044**, conditionally. R3: hc-d's step-1 gate decides it, and this document records
  the question and its resolver rather than pre-deciding it.

---

## What the methodology owes this round

Reproduced from hc-a Part 7(a) **with its authorities re-read out of
`../aetheris/docs/methodology/milestone-methodology.md` at `aaf0f9a`**, not carried from the
summary. One divergence found by doing so; it is recorded below the table.

| Obligation | Authority |
|---|---|
| §6 ticket anatomy per ticket | §6 |
| Repo-qualified `Touches` in cross-repo tickets; an unprefixed path is a prompt defect, repo-qualified from repo state with the deviation noted, never guessed | §6, Touches clause |
| Runbook update rule, **including the changed-semantics clause** | §6 |
| A machine-checkable done-condition per ticket, run by claude-code before presenting work | **§1.3** |
| Review findings written verbatim to a review file in the repo | §1.4 |
| Review files, implementation notes and milestone summaries committed | §8, third bullet |
| A review packet opening with done-check command(s) and their actual output | §5, review-packet spec |
| The §7 ritual: the distillation, the **verification step**, and its **prior-claims census** | §7 |
| Drift checker zero FAIL | §4 |
| A milestone summary — what shipped, what was deferred, open questions | §7's final step |

> **The divergence, recorded rather than followed.** hc-a Part 7(a)'s table named
> `Done-when` and a step-1 gate as §6 obligations. **§6 has neither.** Its anatomy is
> **seven** sections and no more — `Scope`, `Contract refs`, `Touches`,
> `Do not generate`, `Runbook update rule`, `Done-check`, `Claude-code prompt` — followed
> by the sizing rule. The machine-checkable done-condition is **§1.3**, a principle, not a
> ticket section. The **step-1 gate is not in the methodology at all**: it is m4 decision 3,
> cycle-local practice, and R8 carries it on that basis and no other. A document that listed
> it as a methodology obligation would be manufacturing an authority.
>
> This is decision 1's class and decision 2's remedy working as intended — a reviewer-authored
> summary carrying a checkable specific, verified before ratification rather than after.
> `Source: hc-b, 2026-08-08, against ../aetheris/docs/methodology/milestone-methodology.md §6, §1.3.`

**Cite §7's steps by name, never by ordinal** — the m3-cloudcost close renumbered step 4 to
5 and left two BL-007 records citing a step that had moved.

---

## Ratified decisions

Numbered fresh for this round. Each carries its authority, so a later reader sees what it
rests on rather than that it was decided. Authored by the reviewer; recorded here by
claude-code.

### R1 — BL-133's ruling: the record is a **debugging aid, with provenance**. Not an audit trail, not a gate input.

BL-133's *"Do not skip to a mechanism"* paragraph names three rulings about what the record
is **for** — (a) an audit trail, (b) a debugging aid, (c) a gate input — and says picking a
mechanism before the ruling builds the wrong thing cheaply. Ruled: **(b), plus one element
of (a): a provenance stamp.**

The run directory gets the sprint's own console output — every arm, in order, untruncated —
**and** a small stamp naming both repos' commits, the target, and the command. Retention is
**stated and bounded**, not indefinite; hc-d picks the bound and prints it.

**Why (b).**

1. **It is the only purpose that closes an open row's arm.** BL-075's second arm asks for
   *three further full-output runs come back clean*, and needs only that those runs' output
   survive long enough to be counted. Nothing else in the three does that.
2. **The failure case is the whole point.** A `mix test` run that goes red should have its
   output preserved automatically, because BL-075's entire history is *"the run was gone by
   the time anyone noticed"* — and that history has now repeated twice, the `tail -12` at
   filing and the `| tail -60` at m4 t5b, both carriers of a rule this project promoted.
3. **The provenance stamp is what makes a retained log interpretable.** Without the two
   commits and the target, a console log months later is a log of an unknown tree.

**Why not (a) as stated.** `sprint/` is **gitignored** — verified at
`../aetheris/.gitignore:64`, the bare entry `sprint/`, against run directories that exist
under `../aetheris/sprint/`. So an audit trail living there is an audit trail for one
machine. (a) therefore forces a commit-what decision — repo size, review noise, what a run's
record is worth keeping forever — which is a separate and much larger question. **Not taken,
and the reason is recorded so it is not re-litigated as an oversight.**

**Why not (c), and what would re-open it.** A machine-readable verdict document creates a
permanent schema contract: every new sprint arm must register with it, across a population
this document derives rather than inherits (below). **And no consumer exists** — no CI job,
no close sweep, no checker keys on a verdict document today. Building a gate input with no
gate is building a contract for a consumer that does not exist.

> **The two counts in this ruling's cost argument, derived rather than carried.** hc-a's
> ticket text put the cost at *"29 section blocks and 41 invocation sites"*.
>
> **29 is right, on a named population.** `grep -c '  *section "' ../aetheris/scripts/sprint.sh`
> → **29** (indented calls; the two unindented hits are the `section()` definition at `:38`
> and the `Prerequisites` call at `:176`, which is outside any case). The independent
> population agrees: `$TARGET == "…"` takes **30** distinct values, of which one is `all`,
> leaving **29** cases.
>
> **41 does not reproduce.** `run_agent` invocations **28**, `run_orb` **8**, one direct
> `mix aetheris run` — **37** on that population. No population this document can construct
> yields 41. **The number is not carried forward.** Whether 41 was taken over a wider set
> (helper call sites, assertion sites) is not established here; what is established is that
> the argument does not need it — 29 cases and 37 launch sites carry it identically.
>
> This is the *count is a claim about a population* form promoted at the m4 close, arriving
> in the first document that would have cited it. Naming the population is the fix; deleting
> the sentence is not.
> `Source: hc-b, 2026-08-08, against ../aetheris/scripts/sprint.sh at 288c8ef.`

**The trigger, recorded so the deferral is checkable:** when a consumer for a
machine-readable verdict exists — a close sweep that keys on it, or CI — (c) is small,
because BL-077's counter will already hold each arm's name and verdict and only needs a
serializer. **Re-open it then, not before.**

**And the coupling, which is a design constraint and not a preference.** `tee` in a
`set -euo pipefail` script changes exit-status propagation, which collides with BL-077's
counter. **The console capture and the counter are designed together, in one ticket** —
which is why hc-d takes both.

### R2 — BL-133 face 1 is not scope. It is a methodology obligation this round simply meets.

hc-a put face 1 out as *"agents-repo process convention, different approver."* **Part 7(a)
refutes that from the methodology's own text:** §1.4 and §8 already require review files
committed, verbatim. m4 committed **one** — `docs/reviews/t1a-review.md` — across a twelve-row
ticket set.

So face 1 is not a convention to be decided and not a mechanism to be built. **Every `hc-*`
ticket commits its review file.** That is compliance, it is free, and it makes this round's
close assessable where m4's head-1 was not — without anything being scoped.

**It does not retroactively fix m4**, and m4 stays closed.

### R3 — BL-044: conditionally in, and the condition is answered by the design, not here.

hc-a is right that it is unknowable now. **hc-d's step-1 gate answers it:** establish whether
`expected_fail()`'s design needs a real exit code from `run_agent` to key on. If it does,
BL-044 is in hc-d. If it does not, it stays filed with the finding recorded. **Not
pre-decided here; the question and its resolver are.**

BL-044's own row already carries two audit inputs hc-d inherits — one site where the
discarded exit code makes an existing cloudcost assertion vacuous, and three `mix run --eval`
guards recorded as *not* affected so the audit does not re-derive them.

### R4 — BL-075 / BL-054: out — and R1 unblocks BL-075 without taking it.

The *fix* is a polling rewrite of fixed-ms windows in the test suite, a different verification
shape from sprint apparatus. The *fold* alone closes neither row.

**But R1 discharges BL-075 arm 2's blocker.** That arm has been unsatisfiable because no place
existed to retain three full-output runs; R1 creates one. **So this round unblocks a row it
does not take** — recorded here because a blocker cleared is worth recording where a closure is
not.

### R5 — BL-105's arm and BL-106's `run_id`: one question, answered by evidence before it is answered by choice.

hc-a's ruling items 4 and 6 are the same question asked twice. If the streams split, the
failure document goes to the payload stream and Rig's `read_first_run_id` reads that stream —
item 6 dissolves. If they do not split, item 6 is live.

**So the order is fixed:**

1. **hc-c's step-1 gate establishes `[sandbox]` routing** — a stub-provider run with a worker,
   cheap and needing no API key. m4 §Not established has carried this open since t1a and every
   downstream choice has been waiting on it.
2. **Then the arm is chosen**, not before. BL-105's Done-when offers two: move the payload to
   a stream the Logger does not share, or state in the contract that consumers scan for the
   last parsing JSON object and make every in-repo consumer do so. hc-a proposed a third —
   **suppress boot logging on the boot path**, given the contaminant is per-command and gated
   on `ensure_started/0` — which neither Done-when contemplates and which, if sufficient, is
   materially cheaper than either.
3. **Then item 6 is answered**, or dissolved.

**hc-c chooses the arm, from the routing evidence. Not this document.**

### R6 — decision 13 is **under review** by this round, and is amended in it if overturned.

hc-a is right that it belongs in none of carry / lapse / unclear. Recorded as under-review,
with **R5 as its resolver**: if the round splits streams, decision 13 is amended **in the
round, with its own dated record** — decision 7's shape applied to a decision rather than a
document — and never silently superseded.

### R7 — I5's shape: fail-safe defaults with per-arm promotion, and the undeclared set is printed.

hc-a's second shape, taken, and the reason is that the first is not achievable: the audit's
question — *which arms are red today* — cannot be answered from source, and the arms needing
credentials or network cannot be swept for free. **So "complete audit first" means either an
audit declared complete that is not, or a counter that never lands.** The first is the
enumerate-before-hardening rule's own failure mode.

**Fail-safe satisfies that rule's intent**: no arm becomes blocking without being individually
verified.

**With one constraint, and it is not optional.** Arms defaulting to non-blocking silently would
let the sprint report green over an unaudited set — the silent-wrong-answer shape, in the
mechanism built to stop it. **The summary block prints how many arms are blocking and how many
are not yet declared.** A zero in the second column is a claim; a number is a status. Both
printed explicitly, never by omission.

> **BL-077's own Done-when says *"Audit all 31 cases"*. The population is 29.** Derived above
> under R1, two ways. hc-d derives the number and names the population; it does not inherit 31,
> and it does not silently substitute 29 either — the divergence is recorded on the row when
> hc-d touches it. Whether the count was right when the row was filed (2026-08-02) is not
> established here.

### R8 — decision 3 (the step-1 gate) carries, and carrying it forecloses nothing.

hc-a's "against" argument is that carrying it pre-empts m4 §Open item 1's settling condition —
*a run of tickets where authors catch their own*. **That argument does not hold, and the
distinction is worth writing down.**

A step-1 gate is a **reviewer-specified** check the implementer runs. §Open item 1's evidence is
about **unspecified** self-catching — close-b's D4, close-a's two discarded parser passes,
hc-a's own *"I could not re-verify either capture."* Those are not gate results; no gate asked
for them. **The two populations are disjoint, so the gate cannot foreclose the evidence.**

Decision 3 carries. Every `hc-*` ticket has one.

### R9 — decision 12 carries, as a negative constraint.

hc-a found the harness-side referent: BL-069's retired assertion lives in `sprint.sh`'s
cloudcost case, and hc-d touches every `fail()` call site in that file.

**Ratified:** the counter and the `KNOWN_RED` declaration **must not re-arm, re-point, or
resurrect a planted-resource assertion**, and hc-d's audit must not "fix" the rule-legibility
arm by restoring the old one.

> **A stale pointer hc-d will meet.** BL-077's §Suggested order entry reads *"Blocked in
> practice until BL-069 is re-armed or the `expected_fail()` half is designed."* **BL-069 will
> never be re-armed** — it closed by retirement at m4 t2, which is decision 12. Only the second
> disjunct is live. Correct the entry when hc-d touches the row; do not read it as licence.

### R10 — BL-108 is out, freshly and not by inheritance.

Decision 16 lapsed with m4's scope, and hc-a established that BL-108's section is the same file
BL-077 edits. **So its out-ness is a decision this round makes.** Made here: BL-108 is a
status-extraction defect in a different case with a different root cause, and taking it means
auditing a second use case's semantics inside a ticket about the sprint's exit contract.

**And the collision is recorded rather than left to be discovered:** hc-d's audit will touch
eduloka's arms. **It must not fix eduloka's status read in passing.**

hc-a's read-only establishment — `EDUX_DATABASE_URL` unset in this environment, **by
name-presence only, scoped to this machine** — is **recorded, not filed and not closed**, as
hc-a had it. BL-108's Done-when still owes the settled answer.

### R11 — decision 15 is refuted, narrowly, and hc-c carries the finding.

The array is configuration; **the guard is not.**

Verified at `../aetheris/scripts/sprint.sh`, the D2 anti-vacuity block's
`for cc_file in "${CC_D2_FILES[@]}"` loop (`:3125–3136` at `288c8ef`). `CC_D2_FILES` is an
array — decision 15's claim holds for it. The per-file gate is not:

```bash
      if [[ -s "$cc_file" ]] && grep -q run_id "$cc_file"; then
        …
      else
        fail "$(basename "$cc_file") is empty or carries no run_id — the ${cc_name} grep would be vacuous"
      fi
```

`grep -q run_id` is **payload-specific**, and a stderr capture carries no `run_id`. So a stream
split makes the anti-vacuity guard `[FAIL]` on a clean run — the guard firing not because the
search was vacuous but because the file it was pointed at is the other stream.

**This goes in hc-c's ticket text with that anchor**, so a split does not discover it at sprint
time.

### R12 — a ticket's §6 anatomy is written into this document **before that ticket opens**.

Never after it closes, and never only in relayed ticket text. This is §6's requirement made
operational.

**The evidence is m4's own.** m4 kept purpose/state in §Ticket set and the actual anatomy in
relayed ticket text — which is conversation, which is in neither repo. That is precisely why
its Part 7(b) method could not assess decisions 1 and 2, and why its §2 carries a *"what the
census cannot reach"* paragraph. Reproducing the practice would carry a known gap forward on
the first round after it was named.

Authoring is the reviewer's (decision 11) via a section-scoped edit; the edit is dated and
lands before the ticket does.

### R13 — a slot that cannot be authored yet is marked with its resolver: never blank, never guessed.

Name what is unresolved, name the gate that resolves it, cite the ruling. **A blank reads as an
oversight; a guess reads as a specification.** The second is the worse failure — a guessed
`Done-check` written against an assumed runtime shape is the m7-docbuilder class, and a check
that can pass without exercising the thing it checks is worse than no check.

**A resolver names something that exists.** A pointer to an unauthored artifact is a guess wearing
a citation's clothes, and R13 already forbids guesses — this is R13 read properly, not a new rule.
Where the resolving artifact does not exist yet, the correct mark names **who authors it and
when** (*"hc-d's own opening section-scoped edit, per R12"*), never the artifact as though it were
already there.
`Source: hc-b2, 2026-08-08 — hc-d's R3 paragraph resolved to "this ticket's step-1 gate", which
existed in no document.`

> **An observed property of R13's first application, recorded 2026-08-08 (hc-b2).** hc-c's anatomy
> was reviewed before hc-c opened, and every defect found was in the **one slot hc-b completed
> confidently** — the gate half of `Done-check`, called *"authorable now"* and written out in full.
> Its named agent was a placeholder, its transcript could not distinguish its outcomes, and its
> premise — *a stub-provider run with a worker* — was a configuration the harness does not permit
> (`../aetheris/lib/aetheris/agent/supervisor.ex:62`). **Every R13-marked slot was sound.**
>
> So: **R13 flags known uncertainty, and known uncertainty is safe.** What needs review is the
> opposite — the slot an author was sure enough about to complete. This generalises past this
> round and past this document: a marked deferral advertises where to look, and a confident
> completion advertises nothing. Review effort follows confidence, not deferral.

### R14 — a gate whose precondition is an operator-run service is a gate only that operator can run.

A gate whose precondition is a service the operator must be running is a gate only that operator
can run. Name the dependency in §Not established as well as in the gate's precondition text: the
precondition tells this operator how to run it, the §Not established entry tells the next reader
what the round did not settle.

`Added 2026-08-09 (hc-c's opening edit), authored by the reviewer.`

### R15 — a repair of a ticket's own output is a further **round** of that ticket, not a new ticket.

A new ticket is for new scope.

hc-b2 is the instance that produced this rule. It was opened to repair hc-c's specification, which
hc-b had authored — that is hc-b's output, so it was hc-b r2. Classifying it as a new ticket
engaged R12, which requires anatomy in this document before a ticket opens, and no anatomy was ever
written. Item 7 is the residue of that misclassification.

The mechanism the misclassification bypassed is the one that already works: review findings are
committed to the ticket's review file by the round that raised them, before the next round opens
(R2). So a repair round's scope is committed and pre-dates the round, without R12 being engaged at
all. A repair opened as a new ticket has neither — its scope lives in conversation until the ticket
itself commits it, which is why claude-code's hc-d §1 search found hc-b2's findings nowhere in the
tree at `a581a8c`.

R15 does not renumber or unwind hc-b2. It is recorded as having run, under the classification it
was given, with this rule as what it produced.

> **The mechanism was checked against this round's own practice, not only argued.** hc-c's r1
> findings were committed at agents `3d5a8da` (*"docs(hc-c r1)"*) **before** r2 opened at
> `eee5fed`, and `docs/reviews/hc-b-review.md` carries Round 0 and Round 1 and no more — so an
> hc-b r2 would have opened with its scope already in the repo. The counterfactual in item 7's
> resolution is a counterfactual about classification, not about whether the mechanism works.

### R16 — the sprint's per-case verdict keys on the payload's terminal status word, not on the process exit code.

BL-044 stands: `Mix.Tasks.Aetheris.run/1` discards `Aetheris.CLI.run/1`'s code, so a failed run
exits 0. `run_agent` already branches on exit status, which makes its `else fail` arm unreachable
while BL-044 stands. hc-c put a real terminal status into the `--json` payload of every terminal
outcome precisely so a machine consumer need not wait on BL-044. hc-d reads that. BL-044 is not
fixed here and is not a blocker; the exit-code branch stays as a second signal, never as the only
one.

R16's resolver is hc-d's step-1 gate G1. If G1 refutes it, R16 is refuted and the ticket stops
rather than being redesigned mid-session.

> **Both of R16's premises derived from source at harness `1b09b23`, since hc-c asserted the first
> and did not observe it.** `../aetheris/lib/mix/tasks/aetheris.ex` is `_ = Aetheris.CLI.run(argv)`
> then `:ok`; `Aetheris.CLI.run/1` returns `Formatter.print(result, mode)` and its own
> `System.halt` is **commented out** (`../aetheris/lib/aetheris/cli/main.ex`, `:46`–`:48`) — only
> the escript's `main/1` halts on the value. `Formatter.print({:error, _}, :json)` returns **1**
> (`../aetheris/lib/aetheris/cli/output/formatter.ex`, `:78`–`:82`), and a failed solo run reaches
> it: `RunHelpers.handle_run_status/5` returns `{:error, %{run_id:, status: :failed}}`
> (`../aetheris/lib/aetheris/cli/commands/run_helpers.ex`, `:119`–`:121`). So the code exists, is
> 1, and is discarded. The status word is there on every terminal outcome as R16 says — `done`,
> `failed`, `cancelled`, and `error` for a bare-string reason.
>
> **One qualification on *unreachable*, which G2 should not be surprised by.** `run_agent`'s `else`
> arm is unreachable for a run that **reaches** `Formatter.print`. A `mix` compile failure or an
> uncaught raise still exits non-zero and trips it, so the arm is dead to run failure and live to
> harness failure — which is exactly why R16 keeps it as a second signal.

### R17 — fail-safe posture, three arms, all of which resolve to FAILURE.

- **(a)** a case with no `KNOWN_RED` entry that is red → failure. The ordinary case.
- **(b)** a `KNOWN_RED` entry whose evidence is missing, empty, or unparseable → failure, not
  "known red". Absent-is-unknown, applied to the gate's own input.
- **(c)** a `KNOWN_RED` entry whose case PASSES → failure. A known-red that healed is a stale
  entry, and a gate that silently accepts its own staleness is the defect this round exists to
  remove. The remedy is deleting the entry, which is a code change, which is reviewable.

Every `KNOWN_RED` entry carries the backlog row that justifies it. An entry naming no row is
arm (b).

### R18 — capturing the console must not change what the gate reads.

BL-133 face 2 adds a durable console capture; R1 couples it to BL-077 through `tee`/`pipefail`,
because a `tee` in the pipeline changes which command's status the caller sees. Two constraints:

- **(a)** The exit status the gate keys on after the capture is added must be the same status it
  keyed on before, for the same case. Demonstrated, not argued — gate item **G3**.
- **(b)** The capture keeps the streams **merged**. R11's finding fires on a capture-side stream
  split (`sprint.sh`'s D2 anti-vacuity block guards with a payload-specific `grep -q run_id`, which
  a stderr-only capture would fail on a clean run). If hc-d's design requires a split, that is a
  stop, not a widening.

> **R11's guard re-derived at harness `1b09b23`**, since R11 cited it at `288c8ef` and a verified
> citation decays when the file moves. It has not moved: the loop and its guard are still
> `../aetheris/scripts/sprint.sh` `:3125`–`:3136`, and the per-file gate is still
> `if [[ -s "$cc_file" ]] && grep -q run_id "$cc_file"; then` (`:3128`). hc-c did not touch
> `sprint.sh`, which is why the anchor survived.

### R19 — a session that changes a ticket's state updates that ticket's row in the same commit.

This document has now gone stale on its own ticket states three times: hc-c's closure left hc-b's
row saying *In review* (hc-c r2 F7), hc-c's own row claimed closure at r1 while r2 was open (hc-c
r2 F7(c), found by census rather than by the finding), and hc-d's row said *Not started* after
hc-d had run and stopped. Each was caught downstream by a reviewer or a census rather than by the
session that caused it.

The state is part of what the session did, not bookkeeping after it. A session that opens, stops,
or closes a ticket writes that into §Ticket set before it commits — and if a reviewer's ticket
text did not authorise that edit, the session makes it anyway and names it in the packet, because
R19 is the standing authorisation. Closing rounds still write their own row, as hc-c r2 did.

R19 does not extend to a ticket the session did not touch.

`Added 2026-08-09 (hc-d's opening anatomy edit) — R15 through R19, authored by the reviewer and
recorded here by claude-code. The three blockquoted verification notes above are claude-code's,
per decision 2: every checkable claim the authored text marked for verification was confirmed
before transcription, and none was withheld.`

---

### The m4 decisions, by reference

`cloudcost/m4-consolidation.md` §Ratified decisions holds sixteen. They are **not**
re-transcribed here; each is listed with its number, one-line subject, and this round's
disposition. Read the wording there.

| # | Subject | Here |
|---|---|---|
| 1 | The reviewer asserts no checkable specifics in specs it authors; anchors only, ticket says *verify and record* | **carries** — and fired twice in hc-b's own ticket text (the 41, the ten) |
| 2 | A claude-code verification pass over any reviewer-authored doc **before** ratification | **carries** — it is what found both |
| 3 | A step-1 gate inside the ticket | **carries** (R8) |
| 4 | Ticket names are historical and are not tidied | **carries** — it is why `hc-*` is final |
| 5 | The §7 promotion runs mid-cycle when the rules bind the cycle's own remaining tickets | **carries** |
| 6 | Pushes held for review; a cross-citing repo pair lands together, harness first — amended 2026-08-08 for bounded closure pre-authorisation | **carries, with its bound** |
| 7 | A closed record gets a dated superseded note; original text not rewritten | **carries** — R6 applies its shape to a decision |
| 8 | Live operational guidance is corrected in place | **carries** |
| 9 | Where liveness is genuinely undecidable, take the note | **carries** |
| 10 | A milestone-named document is a closed record **if a current equivalent exists** — established, never inferred from the filename | **carries** |
| 11 | Content is authored by the reviewer; formatting belongs to the destination file | **carries** — R12 names it |
| 12 | No planted cloud resources, on any provider | **carries, as a negative constraint** (R9) |
| 13 | Payload extraction, not stream splitting | **carries, not overturned** — resolved at hc-c, 2026-08-09; see the note below the table |
| 14 | The class is every `jq`-over-`--json` read, not the `.status` reads alone; one shared extraction mechanism | **carries** — hc-c's contract is this |
| 15 | BL-099's credential grep is written so covering a second file is configuration, not a rewrite | **carries as amended** — refuted narrowly by R11: the array is configuration, the guard is not |
| 16 | The eduloka status extraction is out of scope | **lapsed** with m4's scope; R10 re-decides freshly |

> **The count, derived rather than carried.** hc-b's ticket text says *"plus the ten carried m4
> decisions by reference."* **The enumeration above yields fourteen in force**, against one under
> review (13) and one lapsed (16). Sixteen accounted for, none dropped.
>
> The split of the fourteen, with its members printed beside each figure so the two can disagree:
>
> ```
> population        : m4 §Ratified decisions, decisions 1–16                        = 16
> in force here     : 1 2 3 4 5 6 7 8 9 10 11 12 14 15                              = 14
>   of which amended:                6              15                              =  2
>   of which unchanged: 1 2 3 4 5   7 8 9 10 11 12 14                               = 12
> not in force      : 13 (under review, R6) · 16 (lapsed, R10)                      =  2
> ```
>
> **The two amendments are not the same kind and the enumeration should say which is which.**
> Decision **6** was amended **before this round**, at m4 close-b — its date cell reads
> *"standing, reaffirmed; amended 2026-08-08"* — and carries in its amended form; that amendment
> is the bounded closure pre-authorisation this round operates under. Decision **15** is amended
> **by this round**, by R11. Derived by reading the **date cell** of each of the sixteen rows,
> which is the field that records an amendment: decision 6's is the only one of the sixteen that
> carries one. Reading instead for the *word* "amended" anywhere in a row returns 6, 7, 8 and 9 —
> the last three because *superseded* and *corrected in place* are their subject matter, not
> markers on themselves. Match by field, not by substring.
>
> **Ten does not reproduce on any population this document can construct.** It is not a
> subtraction from sixteen that lands on ten, and no subset here is naturally ten. The number is
> not carried; the table above is the record.
>
> `[corrected 2026-08-08 (hc-b r1). This paragraph first read "thirteen carrying unchanged (1–12
> and 14) and one carrying as amended (15)". **The total was right and the sub-clause's predicate
> was false**: decision 6 is inside the enumerated range 1–12 and was amended at close-b, so
> "unchanged" did not hold over its own members. Twelve and two, not thirteen and one. This is a
> count printed beside an enumeration that contradicts it — the carrier promoted at the m4 close
> — occurring inside the paragraph correcting a different instance of the same class, which is
> why it is corrected in place with the superseded wording quoted rather than replaced silently.
> Nothing else moves: the fourteen, the sixteen, and every disposition in the table stand.]`
>
> **This is the second instance of the class in one ticket's text**, which is why decision 1 is
> listed above as *firing*, not merely as carried — and, with the correction above, the third in
> this document's own lineage.
> `Source: hc-b, 2026-08-08, against cloudcost/m4-consolidation.md §Ratified decisions at agents 8490362.`

> **Decision 13's disposition, recorded 2026-08-09 (hc-c). R6 asked for one of two outcomes and
> this is the second: the round did not overturn it.**
>
> Decision 13 reads *"payload extraction, not stream splitting, **for the sprint's `--json`
> reads**"* (`cloudcost/m4-consolidation.md` §Ratified decisions, row 13). Its subject is what the
> sprint does when it reads, and **hc-c changed nothing there**: `sprint.sh` captures with `2>&1`
> and reads through BL-100/t1b's backward-scanning `json_read` helper, both untouched by this
> ticket.
>
> What hc-c changed is where the *harness emits*: log output moved off stdout, so stdout carries
> the payload alone. That is not the "stream splitting" decision 13 was contrasted with — that
> phrase named a **capture-side** choice (stop merging with `2>&1` and read stdout alone), which
> BL-105's own table scores as insufficient by itself. Payload extraction remains the contract
> the sprint reads by; the harness merely stopped contaminating the stream it reads from.
>
> **And decision 13's own unestablished clause is now established.** It ended *"whether it sufficed
> in an earlier era depends on `[sandbox]` routing, which is unestablished"* — §Not established
> item 1, resolved above: they route to stderr.
>
> **R11's guard was therefore evaluated, not ignored.** Its condition is a stream split at the
> capture; none happened, so the finding does not fire. Checked rather than argued: the guard's own
> predicate, `[[ -s "$cc_file" ]] && grep -q run_id "$cc_file"`, was run verbatim against a real
> merged `2>&1` capture taken from the changed harness and **passes** — the payload, and its
> `run_id`, are still in the merged file. `sprint.sh` is consequently **not** in hc-c's Touches.

---

## Ticket set

Five tickets, and a sixth session. Per **R12**, anatomy is authored here before the ticket opens;
per **R13**, a slot that cannot yet be authored is marked with its resolver rather than left blank
or guessed. **hc-b2 is the sixth session**; under **R15** it is hc-b **r2** — a repair of hc-b's
own output — and a round carries no row, so it has **none by design**.

> **Five is the planned set, and it is not a census of what ran.** A sixth ticket, **hc-b2**,
> opened and closed on 2026-08-08 to repair hc-c's specification, and it has no row and no
> subsection here. That is a live R12 gap; it is recorded at **§Not established item 7** rather
> than papered over by a row written after the fact. `[added 2026-08-09 (hc-c r2, F7(b)).]`
>
> `[amended 2026-08-09 (hc-d's opening anatomy edit). **Not a live R12 gap.** hc-b2 is classified
> under **R15** as **hc-b r2**: a repair of a ticket's own output is a further round of that
> ticket, a round carries no row, and no R12 obligation was ever engaged. §Not established item 7
> is resolved by ruling on that basis. The wording above stands unrewritten, per decision 7.]`

| | Scope | State |
|---|---|---|
| **hc-a** | The scoping read | **Closed.** Produced no repo artifact by design |
| **hc-b** | This document, and I0 — the harness copy of the repos rule | **Closed** 2026-08-08 at r1. Its specification of hc-c was then repaired by **hc-b2**, which has no row here — see §Not established item 7. agents `e8cd5cd`→`a581a8c`, harness `b4d782a` |
| **hc-c** | The `--json` contract: BL-105 + BL-106 as one contract, both consumer verifications, both mutation postures. Gated on `[sandbox]` routing (R5) | **Closed** 2026-08-09 at **r2**. Gate passed — routes to stderr; BL-105 and BL-106 closed; decision 13 not overturned. agents from `599747e`, harness from `e8889c3` |
| **hc-d** | The sprint exit contract: BL-077's counter and `KNOWN_RED` with fail-safe defaults (R7), **and** BL-133 face 2's console capture — together, because of the `tee`/`pipefail` coupling (R1) | **Opened and stopped** 2026-08-09 at agents `240eb59`. Its opening edit landed — D1's narrowing refuted at its premise, D2 filed, D3 filed and resolved — and the ticket then stopped at its step-1 gate, which was R13-marked and unauthored, with 2 of 7 §6 fields written. No contract work; BL-077 and BL-133 untouched. Anatomy and gate authored by the reviewer's section-scoped edit of 2026-08-09 (this commit); hc-d reopens against it |
| **hc-e** | The close: §7's ritual including its prior-claims census over m4's seven promoted entries, the export boundary, the milestone summary | Not started |

### hc-a — the scoping read

Closed. Read-only, no commit, by design. It produced the ruling questions R1–R11 answer, the
`hc-*` naming (§0 and decision 4), and the Part 7(a) finding that set this round's shape. Its
findings are not in either repo; where this document rests on one, it says so — see §Not
established.

### hc-b — the canonical document, and the round's first edit

**Scope.** This document, carrying the ticket set, the decision log, the close criteria and the
round's open questions; and **I0**, the harness copy of the repos rule widened to match the
agents copy, with its own dated note. After this ticket the round has a canonical record and a
harness file that requires the both-repos read itself.

**Contract refs.** methodology §6, §1.3, §1.4, §7, §8; `cloudcost/m4-consolidation.md`
§Ratified decisions, §Close criteria, §Promotion candidates (close-d's fourth item);
`CLAUDE.md` (agents) §What this repo is, the repos-rule block; **BL-102**.

**Touches.** `../aetheris/CLAUDE.md`; `docs/milestones/hc-consolidation.md`;
`docs/milestones/hc-b-implementation-notes.md`; `docs/reviews/hc-b-review.md`.

**Do not generate.** No implementation. No `--json` change. No `sprint.sh` change. No export
boundary. No backlog row filed or closed. No manifest edit.

**Runbook update rule.** Not engaged: no environment variable, startup step, configuration key,
operational procedure, or changed command/flag/UI semantics. I0 changes a standing instruction
to sessions, not an operator-facing behaviour.

**Done-check.**
```bash
cd /home/it/sandbox/elixirws/aetheris-agents && python3 scripts/drift_check.py --strict
cd /home/it/sandbox/elixirws/aetheris && mix test
git -C /home/it/sandbox/elixirws/aetheris diff --stat HEAD~1
git -C /home/it/sandbox/elixirws/aetheris-agents diff --stat HEAD~1
```
Run `drift_check --strict` **post-commit**; expect exactly one WARN,
`aetheris--CLAUDE.md` staleness from I0, named and not chased. A red `mix test` is **BL-075**
and is not re-triaged.

**Claude-code prompt.** Recorded as executed: hc-b's ticket text, 2026-08-08, with its step-1
gate G1–G5 and its eight Done-when clauses.

### hc-c — the `--json` contract

**Scope.** BL-105 and BL-106 closed as one contract. After this ticket a `--json` consumer gets
a parseable payload separable from log output on every terminal outcome, success or not; Rig's
fork path is verified against the change on both the success and failure paths; and both rows'
mutation postures are on the record.

**Contract refs.** **BL-105** (`docs/backlog-2026-06.md`) — its Done-when's two arms and its two
unconditional riders. **BL-106** — its four clauses. **Decision 13**, *under review* (R6), with
R5 as resolver. **Decision 14** — the class is every `jq`-over-`--json` read. **R11's finding**,
below, which is this ticket's and not hc-d's.

> **R11, restated where the ticket will read it.** `../aetheris/scripts/sprint.sh`, the D2
> anti-vacuity block's `for cc_file in "${CC_D2_FILES[@]}"` loop (`:3125–3136` at `288c8ef`):
> the per-file gate is `[[ -s "$cc_file" ]] && grep -q run_id "$cc_file"`, and `grep -q run_id`
> is payload-specific. **A stderr capture carries no `run_id`, so a stream split makes this
> `[FAIL]` on a clean run.** Decision 15 said covering a second file is configuration; that is
> true of the array and false of the guard.

**Touches.**

- `../aetheris/lib/aetheris/cli/output/formatter.ex` — **certain**. BL-105's
  `IO.puts(Jason.encode!(data))` and BL-106's `print({:error, reason}, _mode)`.
- `../aetheris/config/runtime.exs` **or** `../aetheris/lib/aetheris/application.ex`'s boot-log
  path — **`[R13: arm-dependent. Resolver: R5. Which file, or whether either, follows from the
  arm chosen after the step-1 gate establishes [sandbox] routing.]`**
- `../aetheris/scripts/sprint.sh` — **`[R13: conditional on whether the streams split.
  Resolver: R5. If they do, R11's guard is in this ticket's Touches and BL-099's
  generalisation lands with it, not after — BL-105's own row says a credential grep that stops
  covering stderr is a strictly worse trade than a wrong status word.]`**
- `rig/src-tauri/src/commands/fork.rs` — read for verification; edited only if the arm requires
  the consumer to migrate. BL-106's Done-when says *migrated or verified still correct*.
- `docs/rig/specs.md` and/or `../aetheris/docs/aetheris/runbook.md` — see the Runbook update
  rule below.

**Do not generate.** No `sprint.sh` exit-contract change — that is hc-d. No eduloka status
fix (R10). No planted cloud resource (R9, decision 12). No `--json` schema beyond what BL-105
and BL-106 name.

**Runbook update rule. This bites here.** `--json`'s observable semantics change: a consumer
that got nothing on a failed run now gets a document, and — depending on the arm — the stream
the payload arrives on changes. §6 puts the entry in **this** ticket's `Touches` and done-check,
not deferred. Identify the operator-facing surface that documents `--json` before writing, and
if none exists, say so and create one.

**Done-check.** **`[R13: not authorable until the arm is chosen. Resolver: R5, step 2. It must
include — BL-105's mutation posture against a run whose store emits boot output and one whose
store does not (note that `config :aetheris, :sweep_on_start` defaults to true, so the second run
needs the config toggled, not the store arranged); BL-106's mutation posture, a genuinely failing
run producing parseable output naming the failure; and Rig's fork path exercised on both
paths.]`**

**Claude-code prompt.**

> Execute hc-c as specified in `docs/milestones/hc-consolidation.md` §Ticket set → hc-c.
> Read that specification in full before anything else; it is the ticket.
>
> **The step-1 gate runs first and its failure stops the ticket without an edit** — including the
> `inconclusive` verdict, which is a failure and not a licence to proceed on the likelier reading.
>
> **The arm is chosen from the gate's evidence and is not pre-selected.** Three candidates are
> live: BL-105's two Done-when arms, and the third arm hc-a established — suppress boot logging on
> the boot path, given the contaminant is per-command and gated on `ensure_started/0`. Which is
> sufficient depends on what the gate finds. If the streams split, **decision 13 is amended by this
> ticket with its own dated record** (R6), never silently superseded.
>
> **Carry R11's finding with its anchor.** `../aetheris/scripts/sprint.sh`, the D2 anti-vacuity
> block's per-file loop at `:3125–3136` (at `288c8ef`): the guard is
> `[[ -s "$cc_file" ]] && grep -q run_id "$cc_file"`, and `grep -q run_id` is payload-specific. A
> stderr capture carries no `run_id`, so a stream split makes this `[FAIL]` on a clean run. **If
> the arm splits the streams, that guard is in this ticket's Touches and lands with the split, not
> after.**
>
> **The Runbook update rule bites.** `--json`'s observable semantics change; §6 puts the
> operator-facing entry in this ticket's Touches and done-check. If no such surface exists, say so
> and create one.
>
> Both mutation postures are Done-when clauses, not options.

**Step-1 gate — decision 3, not a §6 field.**

Placed here rather than inside `Done-check` because the two run at opposite ends: a `Done-check`
runs **after** the work and reports; a gate runs **before** and stops **without an edit**. Its
authority is m4 decision 3 (R8), which is a real authority and simply not §6's — and §6 governs
what §6 owes, not what this document may contain.

***(a) The run — one invocation, streams separated.***

```bash
cd /home/it/sandbox/elixirws/aetheris
mkdir -p /tmp/hc-c-gate
mix aetheris --json run agents/ollama_smoke.exs \
  > /tmp/hc-c-gate/stdout.txt 2> /tmp/hc-c-gate/stderr.txt
```

**The agent is named and its worker-spawn is derived, not assumed.**
`../aetheris/agents/ollama_smoke.exs` is `provider: "ollama"`, `tools: ["list_dir"]`,
`model: "llama3.2:latest"`. `../aetheris/lib/aetheris/agent/supervisor.ex:62–63` decides the
spawn with two negative clauses before the catch-all:

```elixir
defp worker_child_spec(%{provider: "stub", mcp_servers: []}), do: []
defp worker_child_spec(%{tools: [], mcp_servers: []}), do: []
```

This config matches neither — provider is not `"stub"`, `tools` is not `[]` — so it falls to the
catch-all and a `Worker.Supervisor` child is started.

**Precondition, checked first.** A local Ollama must be serving `llama3.2:latest` at
`localhost:11434`. If it is not, **the gate cannot run at all** — that is distinct from a gate
verdict, and the ticket stops with the precondition named rather than recording a result.

**One invocation, not two.** Two `mix aetheris run` invocations are two runs with two `run_id`s
and store-dependent boot output (BL-105's own row), so a difference between them is not
attributable to routing. The streams are separated by redirection within a single run.

***(b) The positive control — run first, and separately from the question.***

Both must hold before (c) is asked:

1. **A worker started.** The trajectory meta's `"containment"` key is **non-nil**.
   `../aetheris/lib/aetheris/agent/server.ex:962` is `defp worker_containment(nil), do: nil`, and
   `:678` writes `"containment" => containment` into the meta — so nil means *no worker ran at
   all*, which the code comment at `:960` states in those words. This is a durable trajectory
   fact, not a log line.
2. **At least one `[sandbox]` line was emitted somewhere.**
   `cat /tmp/hc-c-gate/stdout.txt /tmp/hc-c-gate/stderr.txt | grep -c '\[sandbox\]'` ≥ 1.

***(c) The question, asked only after (b) holds.*** Which stream carried the `[sandbox]` lines —
`grep -c '\[sandbox\]'` over each capture separately.

***(d) A verdict for every observation.***

| Control | Observation | Verdict |
|---|---|---|
| `containment` **nil** | — | **Gate failure — no worker ran.** The config or the precondition is wrong. Stop without an edit; the question stays open and is recorded as still open |
| `containment` non-nil | total `[sandbox]` count **0** | **`inconclusive` — gate failure.** Stop without an edit. This is the m4 outcome and it answers nothing: it is consistent with *routes to stderr and none fired*, and the routing question stays open in §Not established |
| `containment` non-nil, total ≥ 1 | all in `stderr.txt`, none in `stdout.txt` | **Routes to stderr.** Decision 13 stands unamended on this evidence; the payload stream carries no `[sandbox]` contaminant |
| `containment` non-nil, total ≥ 1 | any in `stdout.txt` | **Routes to stdout** — a second contaminant on the payload stream beside Logger's. BL-105's arm must cover it, and R11's guard is live |
| `containment` non-nil, total ≥ 1 | present in **both** | **Two emitters.** Enumerate them before choosing an arm; an arm that moves one and not the other leaves the defect |

***The anti-vacuity property, stated in the gate's own text.*** **The positive control is the only
thing that makes *routes to stderr* distinguishable from *nothing was emitted*.** Without (b),
an empty `stdout.txt` and an empty `stderr.txt` read exactly like a clean negative — which is
precisely what the m4 demonstration produced and why this question has been open since t1a. The
gate is required to be able to return `inconclusive`, and `inconclusive` is a failure.

***What the source already says, and why the gate runs anyway.*** Every `[sandbox]` line is an
`eprintln!` in the Rust worker (`../aetheris/native/aetheris_worker/src/sandbox.rs` and
`main.rs`), and `Port.open` is called with
`[:binary, :exit_status, {:packet, 4}, {:cd, …}]` — **no `:stderr_to_stdout`**
(`../aetheris/lib/aetheris/worker/client.ex:133–140`) — so the worker's stderr is *inherited*
rather than captured by the port, and should land on the CLI's fd 2. **That is a derivation from
source, not an observation**, which is the distinction this round exists to hold. The gate can
refute it, and a refutation is the more interesting result.

### hc-d — the sprint exit contract

**Scope.** BL-077 closed and BL-133 face 2 discharged, in one ticket because R1's `tee` /
`pipefail` coupling makes them one design. After this ticket a sprint exits non-zero when an
undeclared assertion fails, tracked known-reds are declared with their ticket ref and do not
flip the exit, the summary block prints the tally **and the not-yet-declared count**, and each
run's console output is retained beside its payload with a provenance stamp.

**Contract refs.** **BL-077** — its four Done-when clauses and its two-halves-together
constraint. **BL-133** face 2. **R1** (the ruling, the provenance stamp, the bounded retention,
the coupling). **R7** (fail-safe defaults, per-arm promotion, the printed undeclared count).
**R9** (decision 12 as a negative constraint). **R3** (BL-044's conditional inclusion).
**R10** (the eduloka collision). Plus `CLAUDE.md` (agents) §Definition of done — *before making
a soft failure hard, enumerate what else that gate holds*.

**The named question that gates the rest — R3.** *Does `expected_fail()`'s design need a real
exit code from `run_agent` to key on?* If yes, **BL-044 is in this ticket** and
`../aetheris/lib/mix/tasks/aetheris.ex` joins `Touches`. If no, BL-044 stays filed with the
finding recorded. Do not pre-decide it; BL-044's row already carries the audit inputs either
answer needs.

**Touches.** `../aetheris/scripts/sprint.sh`; `../aetheris/docs/aetheris/runbook.md`;
`docs/backlog-2026-06.md` (BL-077, BL-133, and any row a `KNOWN_RED` entry cites);
`docs/milestones/hc-consolidation.md`; `docs/milestones/hc-d-implementation-notes.md`;
`docs/reviews/hc-d-review.md`. No file under `../aetheris/lib/`, `native/`, or `config/`.

**Do not generate.** No fix to BL-044 — R16 makes it unnecessary and R3's question is answered by
reading the status word. No change to `json_read` or to BL-100/t1b's backward scan. No new sprint
stage, no new agent file, no planted cloud resource (R9). No `KNOWN_RED` entry without a backlog
row. No stream split at the capture (R18(b)). No change to the D2 anti-vacuity block's guard: R11
established the array is configuration and the guard is not, so touching the guard is new scope,
not this ticket's.

**Runbook update rule.** The sprint's exit semantics are operator-facing and change in this
ticket, so `../aetheris/docs/aetheris/runbook.md` states them here, in this ticket, not later:
what a green sprint now asserts, what `KNOWN_RED` means to a reader, and all three of R17's
failure arms including (c), the healed-entry arm, which is the one an operator will meet first and
find surprising. Harness first.

**Done-check.**

1. The full harness gate set — `mix format --check-formatted`,
   `mix compile --warnings-as-errors`, `mix hex.audit`, `mix credo --strict`, `mix dialyzer`,
   `mix test` — full output, no `tail`, elisions stated. `sprint.sh` is a harness file; the gates
   apply even with no `lib/` change.
2. `shellcheck` on `sprint.sh`. It is absent on this machine as of 2026-08-09; attempt the install
   first. If the install fails, say so with the failure output, and record the absence in
   §Not established rather than omitting the line.
3. The changed stage exercised in BOTH postures, with the broken state observed rather than
   simulated: a case that is red and listed, and a case that is red and unlisted. Plus at least
   one of R17's arms (b) and (c), constructed.
4. The full sprint run if it can run in this environment. If it cannot, say why, record it in
   §Not established, and do not let item 3's success stand in for it.
5. `drift_check.py --strict` from the agents repo, located by finding it, bound by absolute path,
   exit code captured from that invocation.
6. Push both repos, harness first, held for review.
7. **The summary block's printed counts, both of them, including the zero case.** R7 makes this
   non-optional — *"**With one constraint, and it is not optional.** … **The summary block prints
   how many arms are blocking and how many are not yet declared.** A zero in the second column is a
   claim; a number is a status. Both printed explicitly, never by omission"* — and hc-d's
   `Contract refs` cites R7. Observe on a real run, not by reading the code: the summary block
   prints a blocking count and a not-yet-declared count, and both appear when their value is
   **zero**. An omitted line is the defect — a missing number reads as *"nothing to report"*, which
   is the claim R7 forbids making silently.
8. **The provenance stamp and the retention bound, on a real artifact.** R1's wording: *"The run
   directory gets the sprint's own console output — every arm, in order, untruncated — **and** a
   small stamp naming both repos' commits, the target, and the command. Retention is **stated and
   bounded**, not indefinite; hc-d picks the bound and prints it."* Observe on a capture the run
   actually produced: the stamp is present and names what produced it — **all four of R1's
   elements, both repos' commits, the target and the command** — and the bound is printed. If hc-d
   states the bound without enforcing it, that is a permitted outcome and it is **stated as
   unenforced** in the runbook and in §Not established — an unenforced bound recorded as a bound is
   the same shape as the zero that does not print.

**Claude-code prompt.**

> Implement hc-d per this section. Read `docs/milestones/hc-consolidation.md` §Ratified decisions
> R1–R19 and both repos' CLAUDE.md learning sections before the first edit. Run the step-1 gate
> below before writing anything; any of its items coming back unestablished stops the ticket
> without an edit. Standing rules: every claim has a truth-maker; a count names its population and
> prints its enumeration; commands are bound to their targets explicitly and exit codes captured
> from the invocation; a negative needs a positive control; cite by anchor with the line number as
> a parenthetical.

**Step-1 gate — decision 3, not a §6 field.** Placed last for the same reason hc-c's is: a
`Done-check` runs **after** the work and reports, a gate runs **before** and stops **without an
edit**.

Run before any edit. Each item gets an explicit verdict. Any `unestablished` verdict stops the
ticket without an edit — that is the correct outcome.

**G0 — the harness working tree is clean at the ticket's start.**
`git -C ../aetheris status --porcelain` returns zero lines, and `git -C ../aetheris log -1
--format=%h` is recorded.
**VERDICTS:** clean → proceed. Not clean → **stop and report**, whatever the modification is and
however harmless it looks. hc-d's evidence is a sprint run, and a sprint run on an uncommitted tree
cannot be re-derived by anyone else from any commit.

**G1 — R16's resolver.** Establish that a failing agent run's captured file carries a readable
terminal status. Run one failing case through `run_agent`'s own path and read the capture with
`json_read`. Record: the status value read, and whether it is the last parsing object in the
merged capture.
**VERDICTS:** a readable terminal status → R16 holds, proceed. No status, or a status that does
not distinguish failure from success → **R16 REFUTED, stop.** Capture unreadable or absent →
unestablished, stop.

**G2 — what `run_aetheris` resolves to, and what it exits with.** Establish whether it invokes
`mix aetheris`, the escript, or something else, and observe its exit code on the same failing
case. This is what makes BL-044's reach a fact rather than an inference: the escript returns
`Aetheris.CLI.run/1`'s code, `mix aetheris` discards it.
**VERDICTS:** exit 0 on a failed run → BL-044's reach confirmed, R16 is load-bearing. Non-zero →
BL-044 does not reach this path; record it, and R16 still holds but is no longer the only option —
report before proceeding.

**G3 — R18(a)'s resolver, the `tee`/`pipefail` coupling.** Establish `sprint.sh`'s current shell
options (`set -e`, `set -o pipefail`, and where they are set). Then, on the same failing case,
compare the status the caller observes with and without a `tee` in the pipeline.
**VERDICTS:** same status both ways → proceed. Different → the coupling is live; record exactly
how, and it becomes a constraint on the design rather than a stop. Options unreadable →
unestablished, stop.

**G4 — establish that `expected_fail()` and `KNOWN_RED` do not already exist** in `sprint.sh`,
with a positive control so the zero reads as absence rather than as a broken pattern.
**VERDICTS:** absent → this ticket authors them. Present in any form → stop and report; the design
is being written over something that already exists.

**G5 — BL-077's population.** Its Done-when says *"Audit all 31 cases"*; a constraint recorded
elsewhere in this document says the population is 29, not 31. Derive the number from the source
the row is about. Name the population, print the enumeration beside the count.
**VERDICTS:** a derived number matching one of the two → proceed, and correct the row in this
ticket. A third number → proceed, correct the row, and record both prior numbers as wrong. Cannot
be derived → unestablished, stop.

G5 also reconciles three figures recorded at the anatomy edit and at R1 which do not sum: 29
indented `section "` calls, 3 unindented hits (`:38`, `:176`, `:3161`), and 31 for a whole-file
`grep -c 'section "'`. State ONE pattern, derive the population with it, print the full enumeration
beside the count, and account for every line the pattern matches and every line it does not. Then
correct R1's parenthetical — which currently says **two** unindented hits — in the same edit, and
record whether the whole-file figure is BL-077's *"31"* provenance or a coincidence. **A provenance
is established or it is not offered**; a plausible explanation for a wrong number is not a
truth-maker.

> **The arithmetic reconciled at anatomy edit r1, so G5 inherits a smaller job than the paragraph
> above describes — and the error it exposes is claude-code's, not R1's.** `2026-08-09`.
>
> **The three figures were keyed on two different patterns.** `sprint.sh:38` is
> `section() { echo -e … }` — it contains **no** `section "` at all (`sed -n '38p' … | grep -c
> 'section "'` → **0**). The *"3 unindented hits"* came from `grep -n '^section'`, which matches the
> definition; the 29 and the 31 come from `section "`, which does not. Under the one pattern the
> counts actually use: **`grep -c '^section "'` → 2** (`:176` `Prerequisites`, `:3161`
> `Sprint Complete`), **`grep -c '  *section "'` → 29**, **`grep -c 'section "'` → 31**. **29 + 2 =
> 31.** They sum.
>
> **So R1's parenthetical is right about the count and wrong about the members.** There are exactly
> **two** unindented `section "` hits, as it says — but they are `:176` and `:3161`, not `:38` and
> `:176`: it named the definition, which the pattern does not match, and omitted `Sprint Complete`.
> **Not corrected here, per r1's own instruction** — the correction lands in G5's edit, with the
> derivation beside it.
>
> **The error is the anatomy edit's §1e**, which reported *"three unindented hits, not two"* against
> a pattern different from the one whose count it was checking. That is a count over the wrong
> population, inside a verification of a count — one level up from the class it was verifying, and
> the second time this round that counting by the wrong unit produced a wrong claim (hc-d's R-i
> found the first, reads-per-file where the question was reads-per-invocation).
>
> **What G5 still owes, undiminished:** one stated pattern, the population derived with it, the full
> enumeration printed beside the count, R1's parenthetical corrected, and the *"31"* provenance
> **established or not offered**. The whole-file figure being a real count of `section "` makes it a
> live candidate and nothing more.

**Precondition: none.** Every item is a read or a local run; nothing here needs an API key, a
model server, or network.

> **`[superseded 2026-08-09 (hc-d's opening anatomy edit)]`** — this edit is the resolver the mark
> named, so the mark is discharged rather than deleted. The slot previously read, in full:
> *"**Step-1 gate — decision 3, not a §6 field.** `[R13: not authorable. hc-d's design is not done,
> and a gate is written against a design. Resolver: hc-d's own opening section-scoped edit, per
> R12 — the gate is authored there, before the ticket opens, and it answers R3 above.]`"* — and it
> carried the hc-b2 correction below. Both are kept, per decision 7. **R13's mark did its job**:
> hc-d stopped at the unauthored gate rather than completing it confidently, which is the outcome
> the mark was for.

> `[corrected 2026-08-08 (hc-b2). The R3 paragraph previously ended "**Resolver: this ticket's
> step-1 gate.**" — a resolver pointing at an artifact that existed nowhere in this document or
> any other. R13 already forbids it: **a resolver names something that exists; a pointer to an
> unauthored artifact is a guess wearing a citation's clothes.** The repair is to mark the gate,
> not to author it — authoring it now would be the guess R13 forbids, one level up.]`

**The catch-all is discharged.** It read: *"Everything else is `[R13: deferred to the
section-scoped edit that opens this ticket, per R12.]`"* — that edit is this one, and the five §6
fields and the gate above are what it deferred. `[discharged 2026-08-09 (hc-d's opening anatomy
edit).]` **Its two constraints stay live**, and are not absorbed by being restated in a gate:

- **The population is 29, not 31.** BL-077's Done-when says *"Audit all 31 cases"*; derived above
  under R1, two independent ways, the answer is 29. Derive it again at the ticket and name the
  population; correct the row rather than working around it. **This is G5**, which adds the
  third-number branch.
- **BL-077's §Suggested order entry is stale.** It reads *"Blocked in practice until BL-069 is
  re-armed or the `expected_fail()` half is designed."* BL-069 closed by retirement (decision 12),
  so only the second disjunct is live. R9 forbids reading the first as licence. **No gate item
  covers this one** — it is carried here and nowhere else, and `Touches` reaches it via
  `docs/backlog-2026-06.md`.

### hc-e — the close

**Scope.** The round's close. After this ticket the §7 ritual has run with its verification step
and its **prior-claims census**, the export boundary is complete, the milestone summary is
written, and §Close criteria's reads are all performed and recorded.

**Contract refs.** methodology §7 (by name, never by ordinal) and §4. §Close criteria below.
`CLAUDE.md` (agents) §Definition of done — the post-commit `--strict` ordering, remove-all-upload-all,
and *a green pin proves currency, never completeness*. **BL-102**, which asked for §Close criteria
and consumes its answer.

**The named question that gates the rest.** *What hc-c and hc-d actually did* — which arm landed,
whether decision 13 was overturned, whether BL-044 came in, which rows closed and which were
filed. None of it is knowable now, and guessing it would be R13's worse failure.

> `[partly falsified 2026-08-09 (anatomy edit r1). "None of it is knowable now" no longer holds for
> hc-c: its arm landed, decision 13 was not overturned, and both rows closed. hc-d's half stands —
> it has not run. Revised in full at hc-e's own opening anatomy edit; the original wording stands,
> per decision 7.]`

**Two obligations recorded now so hc-e does not rediscover them.**

1. **The prior-claims census population is m4's seven promoted entries** — three at t1a-p, four
   at close-b — read out of both `CLAUDE.md` files, plus any document from the m4 cycle claiming
   learnings were promoted. hc-b's G4 re-derived the four close-b entries and found all four
   present; **that is a G4 result, not the census**, and hc-e runs the census over the full seven
   with the terms it used recorded.
2. **The manifest inclusion note owes a sentence about `docs/milestones/`, and it owes both
   halves.** See §Close criteria, clause 6.

**Everything else is `[R13: deferred, per R12.]`**

---

## Close criteria

This round is done when hc-b through hc-e have closed with zero blocking findings, the drift
checker reports zero FAIL and no unexplained WARN, and the §7 ritual has run.

**What a close sweep of this document reads.** Written on the merits. m4's five clauses were each
assessed for an analogue rather than copied; the assessment is in the right-hand column, and where
hc-b's ticket text offered a hypothesis about a clause, the assessment records what was found
rather than what was expected.

| | Clause | m4 analogue |
|---|---|---|
| **1** | Every ticket in §Ticket set, checked against the backlog rows it closes. A row closed in the repo and open here, or the reverse, is the defect the clause exists to catch | **m4 clause 1.** Direct. hc-c closes BL-105 and BL-106; hc-d closes BL-077 and BL-133 (or its face 2, if the row is split) and conditionally BL-044 |
| **2** | Every row in §Rows filed, checked for a closure record if it closed. **This backlog records closure in two shapes and a sweep must read both** — see the note below | **m4 clause 2**, carried with its population widened, **not with its wording faulted.** m4's *"a DONE section"* is accurate for the rows m4 itself closed; what it does not cover is the older shape. The widening is additive |
| **3** | §Not established, item by item: resolved, still open, or superseded — and if resolved, where | **m4 clause 3.** hc-b's ticket text offered *"m4's clause 3 may have none here"* as a hypothesis; **it does not hold.** This round opens with four §Not established entries, one of which — `[sandbox]` routing — is the gate hc-c turns on. The clause has more to do here than it had at m4, not less. Recorded as a refutation |
| **4** | The decision log, for any decision the implementation diverged from. A divergence is closed by changing the code or the decision, never left silent | **m4 clause 4**, and it has live work before the round starts: **R6 puts decision 13 under review.** The close either amends it with its own dated record (decision 7's shape) or records that the round did not overturn it. Silence is the one disposition unavailable |
| **5** | Anything §7 does not itself verify about the promotions | **m4 clause 5, partly superseded.** m4's clause said *"§Rules promoted, read out of the two `CLAUDE.md` files rather than trusted"*. That is now **§7's own verification step**, and its prior-claims census besides. Carrying it as a full clause would put one obligation in two places, where they can drift. Kept only as a residual |
| **6** | The manifest's inclusion note, for the sentence `docs/milestones/` now owes — **both halves** | **No m4 analogue.** New, created by this round's placement decision. See below |

**Clause 6, in full, because half of it invites the error the other half prevents.**

1. `docs/milestones/` holds working artifacts and is out of the manifest — stated over its
   **contents at that date**, so the claim quantifies a named population rather than a directory
   name. Before hc-b it held **four** files, zero tracked — `bl-067-implementation-notes.md`,
   `bl-068-implementation-notes.md`, `m-eduloka-discovery-kickoff.md`,
   `m-eduloka-discovery-summary.md`. hc-b adds two (`hc-consolidation.md` and
   `hc-b-implementation-notes.md`), giving **six**; hc-e restates the population as it stands
   at the boundary rather than reusing this number.
2. **`docs/rig/milestones/` is the counter-example.** Same path segment, **two tracked files** —
   `docs/rig/milestones/p3/protocol.md` and `docs/rig/milestones/bl-007/README.md` — admitted on
   the *specification* test the manifest's inclusion note already states. **So the inclusion rule
   reads the artifact's kind and never its directory.**

> **Why both halves.** The placement of this document was first justified on the ground that a
> `milestones/` directory makes the inclusion rule *structural* — everything under it is a
> working artifact and out. **That is false**, and `docs/rig/milestones/` is the counter-example
> in this repo. What survives is weaker and sufficient: `docs/milestones/` is **homogeneous
> today**, and the `m-eduloka-discovery-*` pair is direct precedent for a milestone-level
> document living there untracked; flat `docs/` holds exported standing docs
> (`backlog-2026-06.md`, `capability-matrix.md`, `agent-creation-guide.md`) among which a working
> artifact would sit as a different kind.
>
> **The corrected premise is recorded, attributed, and not smoothed over.** It is a checkable
> specific asserted rather than verified — decision 1's class — and it is the reviewer's. Stating
> half 1 alone at the boundary would re-install exactly the generalisation the check refuted.
> `Source: hc-b, 2026-08-08 — the placement check, against docs/project-knowledge-manifest.md's
> inclusion note and its 25 parsed rows.`

**Clause 2's two shapes, and what is and is not a defect here.**

`docs/backlog-2026-06.md` records a closure two ways, and neither replaced the other:

| Shape | Form | Count today |
|---|---|---|
| **A — in-row paragraph** | `**DONE <date> (<ticket>).**` as a bold paragraph inside the open row, which is left intact | **9**, and **every one is m4-cycle-dated** (t1b, t2, t3, t4a/b/c, t5b) |
| **B — sibling heading** | `### BL-0NN — DONE <date> …` as its own heading near the open row | **15 headings**, one of which — `### BL-050 + BL-055 + BL-056 — DONE 2026-07-25` — covers three rows, so 17 rows. Dated 2026-07-23 to 2026-08-05 |

The shapes are **not exclusive**: BL-069 carries both, an in-row paragraph and a sibling heading,
because its closure record was written at the m4 close rather than at t2 when the work landed.

> **`[corrected 2026-08-08 (hc-b r1)]` This clause first read: *"In this backlog closure is a
> separate sibling row … not a section inside the row. Sixteen such sibling rows exist today"*,
> with the reason *"m4's wording said 'a DONE section', which is how the record is spoken of and
> not how it is stored; a sweep looking for a heading inside a row would find nothing and report
> clean."* **That was wrong, and wrong in the direction that faults m4.***
>
> **m4's wording is accurate for the rows m4 closed.** All three rows its clause 2 swept —
> BL-107, BL-121, BL-127 — use shape **A**, an in-row `**DONE` paragraph, which is exactly what
> *"a DONE section"* describes. So there was no wording defect to find and no vacuous
> satisfaction available: the clause named the shape its own population uses.
>
> **And m4's execution was sound**, verified rather than assumed. Its clause 2 verdict reads
> *"Three closed (BL-107 at t1b, BL-121 and BL-127 at t5b) and all three carry DONE sections;
> the other 27 are open by design"*, over a population it stopped hand-counting and derived —
> `BL-105..BL-134` = 30, in four blocks. Its clause 1 reverse direction matched the rows carrying
> cycle-dated DONE sections. Nothing in either run depended on ignoring the clause's wording.
>
> **What was actually true, and all that was:** the backlog holds a second, older shape that
> m4's clause never had occasion to name, because no m4-cycle row uses it. Widening the clause to
> read both is worth doing — a future round closing an old row would meet shape B — and it is a
> **widening, not a correction of m4**.
>
> **The r0 error's own class.** It generalised *"closure is a sibling row"* from an enumeration of
> shape-B rows without checking the shape the rows under discussion actually use — an observation
> over one subset stated as a claim about the class. That is the carrier this round has now hit
> three times, and this instance is the author's rather than the reviewer's.
> `Source: hc-b r1, 2026-08-08 — both shapes enumerated against docs/backlog-2026-06.md at agents
> e8cd5cd; m4's clause 2 and clause 1 verdicts read out of cloudcost/m4-consolidation.md §The
> close §1.`

**And `## Suggested order` is a second status surface that must agree.** Rows carry a `✔` /
numeric-rank / `—` column there as well as their own state. **Whether it currently agrees with the
row states was not checked by this round** — it is named as a surface a sweep must read, not
reported as one found disagreeing.

---

## Rows filed

**Empty at hc-b**, and the population is named so the emptiness is a status rather than a claim:
this ticket files no backlog row and closes none, by its own *Not this ticket*.

The backlog is `docs/backlog-2026-06.md`, single-file. **The highest row filed is BL-134**, so
anything this round files begins at **BL-135**. hc-c and hc-d populate this section; hc-e sweeps
it under clause 2.

> **A note for whoever writes the first entry.** The backlog has no `## DONE` section and rows are
> not moved on closure. A closed row acquires a closure record **in one of two shapes** — an
> in-row `**DONE <date> (<ticket>).**` paragraph, which is what every m4-cycle closure used and
> what a row filed by this round should use, or an older sibling `### BL-0NN — DONE <date> …`
> heading. §Close criteria clause 2 enumerates both; read it before sweeping. Rows BL-098 onward
> also sit *after* the `## Suggested order` heading with no section heading of their own, and
> `## Suggested order` is a **second status surface** with its own `✔` / rank / `—` column, which
> a sweep must read alongside the row.
>
> `[corrected 2026-08-08 (hc-b r1) — this note first said closure is a sibling row and named only
> that shape. See clause 2's correction block for what was wrong and why it mattered.]`

---

## Not established

Carried forward rather than resolved. Each is a question this round opens and has not closed.

1. **`[sandbox]` line stream routing.** Carried unresolved from `cloudcost/m4-consolidation.md`
   §Not established, open since t1a: the command that demonstrated BL-105 spawns no worker, so
   whether `[sandbox]` lines go to stdout or stderr has never been observed. **R5 makes hc-c's
   step-1 gate its resolver**, and every downstream choice in this round — the arm, BL-106's
   `run_id` item, decision 13's fate, R11's guard — has been waiting on it.

   > **`[RESOLVED 2026-08-09 (hc-c).]` They route to stderr — part observed, part derived, and
   > the two are separated here because the observation alone does not carry the class.**
   >
   > **Observed.** The gate ran `mix aetheris --json run agents/ollama_smoke.exs` once with the
   > streams separated by redirection. Positive control first: the trajectory meta's
   > `containment` was **non-nil** (`priv/runs/ollama-cqyzBw/trajectory.json`,
   > `.meta.containment` — `seccomp: true`, `exec_server: true`), so a worker ran. Then the
   > count: **2** `[sandbox]` lines, **2 in `stderr.txt`, 0 in `stdout.txt`** — verdict-table
   > row 3. Those two are the **success-path pair**; a clean run emits no others.
   >
   > **Derived, not observed — and this is what carries the class.** The emission sites are
   > **16**, derived from source rather than carried from hc-b2 or from the ticket text:
   > `../aetheris/native/aetheris_worker/src/sandbox.rs` (**11** — the `unshare` failure at
   > `:177`, the namespace-entry line at `:214`, the overlay pair at `:264`/`:269`, and the
   > seven cgroup sites `:537`–`:574`) and `main.rs` (**5** — `:88`, `:94`, `:114`, `:117`,
   > `:153`, all failure paths). **16 of 16 are `eprintln!`; 0 are `println!`** — including the
   > three whose format string sits on a continuation line (`sandbox.rs:177`, `:214`, `:264`,
   > each opened by an `eprintln!(` on the line above). They therefore write to the worker's
   > fd 2, and `Aetheris.Worker.Client.port_options/1`
   > (`../aetheris/lib/aetheris/worker/client.ex`, `:132`–`:139`, used by the `Port.open` call
   > at `:243`) sets **no `:stderr_to_stdout`**, so that fd is inherited rather than folded into
   > the port. The other 14 sites route identically to the 2 that fired.
   >
   > **The run itself failed** — Ollama could not load `llama3.2:latest` in 2.1 GiB of available
   > memory — which the control was written to be independent of, and is: the `[sandbox]` lines
   > are emitted at worker startup, which `containment` proves happened.
   >
   > `[amended 2026-08-09 (hc-c r1, F2). The block first read "They route to stderr" over an
   > observation of two lines and called the derivation "confirmed rather than refuted" — a
   > resolution that read as fully observed when the class-wide half of it was derived. Same
   > shape as the resolved-versus-advertised finding this ticket recorded about its own config
   > read. The verdict is unchanged; its basis is now stated in two parts.]`

2. **Whether the chaos gate has ever run in a clean-store environment.** m4 t1b partly resolved
   this: the first chaos capture in the harness repo
   (`../aetheris/sprint/20260806_172144/chaos/maxsteps.json`) exists and *did* warn, in a
   **noisy**-store environment, so that behaviour is observed rather than inferred. **The
   clean-store question itself is untouched** — no chaos run has been made in a clean store, and
   nothing established what one would do.

3. **The transition claim in hc-a Part 4 rests on a transcription, not a file read.** hc-a was
   read-only and produced no repo artifact, so the claim's basis is a session capture in neither
   repo. **It has not been re-derived here**, and hc-b does not act on it. Whoever needs it opens
   the file; hc-a's own record is not a truth-maker for it. This is BL-133's subject arriving
   inside the round that scopes BL-133.

4. **No harness-side pointer to this document exists, and none is being created.** The round's
   subject and nearly all its code edits are harness-side; its canonical record is in the sibling.
   A pointer file would be a second artifact to keep in sync — the mirror problem this project
   already has one instance of, with `drift_check` having no byte-identity check between mirrors.
   **Recorded rather than fixed.** The mitigation is that I0's dated note in
   `../aetheris/CLAUDE.md` names this round and this path, which is the one place a harness-side
   reader will already be looking.

5. **hc-c's gate requires a live local Ollama serving `llama3.2:latest` at `localhost:11434`.**
   Whether `[sandbox]` routing can be established without a model server is not established. A
   `stub`-provider agent with a non-empty `mcp_servers:` list would spawn a worker under
   `../aetheris/lib/aetheris/agent/supervisor.ex:62-63` and would remove the dependency, but no
   such agent file exists in `../aetheris/agents/` (hc-b2 §G3(4)) and this round did not write
   one. Carried to BL-133's territory.

6. **Whether any consumer outside these two repos reads harness *log* output on stdout.**
   hc-c moved Logger to stderr for **every** invocation and every mode, not only `--json`, so the
   population at risk is wider than the row that motivated it. **The in-repo sweep is clean and
   its population is named** — every file in both repos with an executable extension
   (`.sh .py .rs .ts .tsx .exs .ex`, excluding `node_modules`, `target`, `_build`, `deps`,
   `priv`, `.git`) containing a harness invocation: **39 files, of which 5 actually spawn the
   harness and read a stream**, and **0 of the 5 read log text from stdout**. The enumeration is
   in `docs/milestones/hc-c-implementation-notes.md` §7.

   **What the sweep cannot reach**, and therefore what stays open: an operator's own shell
   pipeline or ad-hoc command; any consumer outside these two repos; and any invocation whose
   spelling none of the search terms matched. **The sweep is clean, not exhaustive**, and
   the distinction is recorded rather than allowed to read as completeness. The mitigation is
   that the change is announced in the operator-facing runbook rather than only in the backlog.

   > **`[amended 2026-08-09 (hc-c r2, F8). The first term list was found incomplete — by this
   > entry's own sibling analysis, before any reviewer read it.]`** The four terms above were all
   > spellings of `aetheris`, while the sprint.sh analysis in the same sweep already argued that
   > **`mix run --eval` boots the app and is therefore in scope** — a term the file-level sweep
   > never searched for. So the residue sentence was written as a hypothetical about a gap the
   > work had already demonstrated. **It is not left reading as though it anticipated it.**
   >
   > **The terms are now derived from what boots the app**, which is the property that matters
   > (`route_logging_to_stderr/0` runs in `Aetheris.Application.start/2`): `mix aetheris`,
   > `mix run`, `mix test`, `mix eval`, `iex -S mix`, `./aetheris`, and the argv constructions
   > `["mix", …]`, `System.cmd("mix", …)`, `Command::new("mix")`, `subprocess … "mix"`.
   >
   > **Population 39 → 48; nine files the first list missed**, enumerated with the old beside the
   > new in `docs/milestones/hc-c-implementation-notes.md` §8c. **Four are prose** (harness `.exs`
   > tests whose comments mention `mix test`). **Five are real consumers** — the provenance
   > pytest suites, which spawn `["mix", "run", "--eval", …]` with `capture_output=True`. **None
   > is broken; the change helps them**: their four stdout reads are
   > `json.loads(result.stdout.strip())`, whole-stdout parses that boot output on stdout would
   > have broken, and their three stderr assertions are substring tests that more stderr content
   > cannot falsify. All 41 tests pass on the changed harness.
   >
   > **The residue is unchanged in kind and smaller in size**: an operator's own pipeline, and
   > anything outside these two repos. Still clean, still not exhaustive.
   >
   > `[corrected 2026-08-09 (hc-d, R-i). The sentence above reading "None is broken; the change
   > helps them" is **wrong in its second half**. The four whole-stdout parses it cites belong to
   > **Python-CLI** subprocesses in those files, not to the harness invocations: enumerated per
   > invocation, the five files make 17 subprocess calls — 7 harness, 10 Python — and **no harness
   > invocation reads stdout at all**. The suites are **unaffected**, not helped, and they were
   > green on the pre-hc-c tree (41 passed at `b4d782a`). **"None is broken" stands**; only the
   > rationale falls. Established at §Not established item 8's resolution; original text left
   > standing per decision 7.]`

7. **hc-b2's §6 anatomy was never written into this document — an R12 gap, recorded rather than
   back-filled.** R12 requires a ticket's anatomy here **before that ticket opens**. hc-b2 opened
   and closed on 2026-08-08 (agents `6c61393`) and appears in this document only as six source
   citations; §Ticket set has **no `hc-b2` row and no `### hc-b2` subsection** — established by
   search, not assumed.

   **Why it is recorded and not fixed here.** Authoring the anatomy now would place it *after* the
   ticket closed, which is the one thing R12 exists to prevent, and would make the document assert
   a sequence that did not happen. Anatomy is also the reviewer's to author (decision 11, R12), not
   claude-code's. **So the gap is named, and the choice of remedy — a row authored by the reviewer,
   or a ruling that a mid-round repair ticket needs none — is left to whoever takes it up.**
   Whichever way it goes, `Five tickets.` above needs revisiting with it.

   > **`[STAYS OPEN. 2026-08-09 (hc-d, D1). A narrowing of R12 was offered conditionally; its
   > premise was tested first and does not hold, so the narrowing is not written.]`**
   >
   > The offered narrowing would have applied to *"a repair ticket whose scope is exactly a prior
   > round's committed review findings"* — on the premise that hc-b2's scope existed **verbatim, in
   > a committed repo artifact, before hc-b2 opened**. **It did not.**
   >
   > **What was checked, and how.** hc-b2 opened and closed at agents `6c61393`; the tree
   > immediately before it is `a581a8c`. (1) The only `hc-*` review file present at `a581a8c` is
   > `docs/reviews/hc-b-review.md`. (2) `docs/reviews/hc-b2-review.md` was **first added by
   > `6c61393` itself** — hc-b2's own commit — so it does not pre-date the ticket. (3) Six wordings
   > of hc-b2's findings were searched over the **entire committed tree** at `a581a8c`:
   > *"exactly two slots"*, *"inconclusive"*, *"two invocations"*, *"the gate's home"* and
   > *"Finding B"* return **0 files**; *"stub-provider run with a worker"* returns **1**, and that
   > one is hc-b's own gate text — the premise hc-b2 refuted, not hc-b2's finding about it.
   > (*"placeholder"* matches 115 unrelated files and is not a discriminator.) (4) `hc-b-review.md`
   > §Round 1 at `a581a8c` is about the decision-count split and clause 2 — hc-b's own artifact,
   > nothing about hc-c's gate.
   >
   > **The structural reason, which matters more than this instance.** **R2 requires a ticket's
   > review file to be *committed*, not to *pre-date* the ticket** — and a ticket's own review file
   > is committed **by** that ticket. So R2 cannot supply the pre-dating artifact the narrowing
   > needs; for hc-b2 the findings lived in conversation until hc-b2 itself committed them. A
   > narrowing resting on *"already satisfies that purpose"* would therefore have been written over
   > a condition this process does not currently produce.
   >
   > **Item 7 stays open, and `Five tickets.` still needs revisiting with it.** What a future
   > remedy now also has to decide: whether repair tickets should commit their findings *before*
   > opening — which would make the narrowing's premise true rather than assumed.

   > **`[RESOLVED 2026-08-09 (hc-d's opening anatomy edit), by ruling — R15.]` The gap is real and
   > its cause is a misclassification, not a missing row.** hc-b2 was a repair of hc-b's output and
   > therefore hc-b r2; as a round it would have had no R12 obligation, and its scope would have
   > been committed to `docs/reviews/hc-b-review.md` by hc-b before it opened, per R2. No anatomy is
   > back-filled: authoring it now would place it after the ticket closed, which is the failure R12
   > exists to prevent, and claude-code was right to decline it at hc-c r2 F7(b) and again here.
   >
   > The second question D1's refutation raised — whether repair tickets should commit their
   > findings before opening — is answered by R15 rather than by a new obligation: as rounds, they
   > already do.

8. **Whether the five provenance pytest suites passed on the harness *before* hc-c is not
   established.** They spawn `["mix", "run", "--eval", …]` with `capture_output=True` and read
   stdout with `json.loads(result.stdout.strip())` — a whole-stdout parse. hc-c r2 established they
   pass on the changed harness (41 tests) and that the boot path is real (stdout 0 bytes, three
   `[Aetheris.Application]` lines on stderr). **It did not run them pre-fix.** If boot output
   reached their stdout before hc-c, those parses should have raised, which would mean the suites
   were red and unnoticed; if they were green, the r2 claim that *"the change helps them"* rests on
   a mechanism not yet identified. **Exactly one of those is true and neither is established.**
   Carried to hc-d, whose subject is gates that pass without looking.

   > **`[RESOLVED 2026-08-09 (hc-d, R-i), by running them. The second horn is the true one, and the
   > r2 claim it tests was wrong.]`**
   >
   > **Run.** The harness was checked out at `b4d782a` — the commit before hc-c's `e8889c3` —
   > detached, with a positive control confirming the fix was absent (`route_logging_to_stderr`: 0
   > occurrences; the `:json` error clause: 0). The five suites were run against that tree:
   > **41 passed**, the same 41 that pass on the changed harness. The tree was restored to `main`
   > with the same control run in reverse (3 and 1 occurrences). **They were green before hc-c.**
   >
   > **The mechanism, which the r2 claim got wrong.** r2 enumerated stdout reads **per file** and
   > put them on the harness's account. Enumerated **per invocation** instead — the unit that
   > actually matters — the five files make **17** `subprocess.run` calls: **7 spawn the harness**
   > (`["mix", "run", "--eval", …]`) and **10 spawn a Python CLI** (`[sys.executable, SCRIPT]`).
   > **All four `json.loads(result.stdout.strip())` calls belong to the Python CLIs**, which never
   > touch the harness. **No harness invocation in these files reads stdout at all** — the 7 read
   > `returncode` and `stderr` only.
   >
   > **So hc-c neither helps nor risks them: they are unaffected.** F8's conclusion — no broken
   > consumer — stands; the *"the change helps them"* rationale does not, and is corrected wherever
   > it landed rather than left to propagate.
   >
   > **The error's class.** A census keyed on the wrong unit: reads-per-file where the question was
   > reads-per-invocation. Two subprocess families live in one file, and counting by file merged
   > them. This is the adjacent-case shape, one level up from the code it was written about.

9. **What wrote — and then unwrote — the uncommitted `config/config.exs` block is not established.**
   Found at the anatomy edit (2026-08-09) by its own done-check, which had claimed the harness would
   show no change and reported the divergence instead of asserting green. The block, **recorded
   verbatim here because the working-tree copy no longer exists to re-read** — this is the
   `git diff -- config/config.exs` output captured at that done-check, added lines only:

   ```diff
   +
   +if config_env() == :dev do
   +  config :aetheris, :playground_tokens, ["tok-abc"]
   +end
   ```

   **Never committed, anywhere.** `git show HEAD:config/config.exs | grep -c playground_tokens` → 0
   while the working tree read 1, and `git log --all -S'playground_tokens, ["tok-abc"]'` returns no
   commit on any ref.

   **`mix test` is refuted as the writer, by a positive control.** The file's mtime was
   `09:03:07`, inside the first `mix test` window — but a second `mix test` (09:08–09:10) left the
   mtime **unchanged at `09:03:07`**. A full-tree search found no writer: the path appears only in
   docs (`--exclude-dir` on `.git`, `_build`, `deps`, `node_modules`, `target`), `mix.exs` has no
   aliases, `.git/hooks/` holds only samples, and `sprint.sh`'s `playground_tokens` use is a runtime
   `Application.put_env`, not a file write.

   **It then reverted itself, which is the second half of the finding.** r1 asked for the block to be
   recorded and then reverted so the tree would be clean for G0. **No revert was performed and none
   was needed**: by `09:26` the block was gone, `git status --porcelain` returned zero lines, and the
   mtime had moved to `09:24:05` — a second external write, removing what the first added, with no
   action from the session in between. r1's *"if it reappears, that reappearance is the finding"*
   therefore already has its mirror: **the writer is external to these repos and was active during
   this session, in both directions.** Nothing was committed and nothing was reverted by hand, so no
   claim about the cause is made.

   **G0 is the standing consequence** — hc-d stops on a dirty harness tree rather than running a
   sprint whose results no commit can reproduce.

---

## Promotion candidates

Candidates recorded here are promoted or dropped at hc-e under the methodology's milestone-end
ritual; recording one is not promoting it.

**The promoted count rule's carrier 1 has a sub-shape.** A prediction about an artifact that has
not been written yet, later carried as though it had been counted. Distinct from the earlier
instances, which were counts over populations that existed and were miscounted — a prediction has
no population to enumerate, so the operational close ("name the population and print the
enumeration") cannot be applied to it at all. Mark it as a prediction when made, or do not make
it. Origin: claude-ui's hc-c ticket text ("exactly two slots marked under R13"; four marks across
three fields); named by claude-code at hc-b2.

**The packet is the artifact that travels, and packet assembly is itself a place claims are made.**
At hc-c r1 a correctly-bound `drift_check --strict` ran in-session and reported real hashes; the
packet published a different invocation — one that had failed under a persisting `cd` — beside an
`exit=` literal bound to nothing, and a WARN count the published command had not produced. The
verification was sound; the artifact was false. So: a packet transcribes the command that ran and
the status that command returned, or it re-runs and publishes the re-run. It never re-runs to
illustrate a result obtained some other way, because a re-run can bind differently than the
original and the difference is invisible in the output. Origin: claude-code's own diagnosis at
hc-c r2 §8a, which corrected the reviewer's finding — the result was not carried from r0.

**The reviewer asserting a document's state from memory of prior packets rather than from the
document.** Each instance was caught by claude-code rather than by the reviewer.

**Instances, an open list** — later ones append rather than restate a total, since the count was
wrong one commit after it was written and that is carrier 1: **(i)** hc-c's A3 named two sections
that live in `cloudcost/m4-consolidation.md`; **(ii)** hc-c's F3 scoped a status fix to two surfaces
and left a third contradicting them; **(iii)** hc-d's opening claimed its anatomy was authored when
2 of 7 §6 fields were; **(iv)** the anatomy edit cited `hc-d §1a` and `§1d`, letter sub-anchors that
file does not have; **(v)** the anatomy edit called an `hc-c r2` note *"its hc-d r2 note"*, and hc-d
has no r2.

The carrier is not the sibling document —
it is that a packet reports enough of a document to make re-reading it feel unnecessary, and a
reported document is not a read one. Cited-means-read binds the reviewer identically. Origin:
claude-ui, named here.

---

## Not carried, and why

Two of m4's sections are deliberately absent. Stated, because a section missing without a note
reads as an oversight.

- **§Sequence.** m4 had one because its ticket set grew mid-cycle (t5 became t5a/t5b/t5c) and the
  order stopped being derivable from the set. **A five-ticket round's sequence is its ticket
  set**, in the order §Ticket set lists them. If this round splits a ticket, the split is recorded
  in §Ticket set and this note is what says a §Sequence would then be owed.
- **§Open for the close.** m4 distinguished decisions the close must *take* from reads it must
  *perform*. At this size the distinction costs a section and buys nothing: **the open questions
  are §Not established's four**, each with its resolver named, and §Close criteria clause 3 is the
  read that sweeps them.

---

`Document created 2026-08-08 (hc-b), at agents 8490362 / harness b4d782a. Decisions R1–R13
authored by the reviewer; §What the methodology owes, the derived counts, and the repo-state
sections composed by claude-code and verified at those two commits.`
