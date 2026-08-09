# hc-d — implementation notes

**Ticket.** `docs/milestones/hc-consolidation.md` §Ticket set → hc-d. **Repos.** agents `eee5fed`,
harness `1b09b23`. **Date.** 2026-08-09.

**Outcome: the opening edit landed; the ticket stopped at the step-1 gate, which is unauthored.**
No contract work was done. That is the correct outcome, not a setback.

> `[superseded 2026-08-09 — the stop was lifted and the ticket ran to completion. The original
> stands, per decision 7: it was the correct outcome for that session, and the gate it stopped at
> was authored by the reviewer's anatomy edit afterwards.]` **Current outcome: G0–G5 all pass and
> the contract landed.** BL-077 closed, BL-133 face 2 discharged, R3 answered (BL-044 stays filed),
> R-iii and R-iv discharged. §§7–15 below are the later sessions; §§1–6 are the original stop and
> are unchanged.

---

## 1. D1 — the R12 narrowing was offered conditionally, and its premise fails

D1 gave reviewer-authored narrowing text to be written **only if** hc-b2's scope was recorded
verbatim in a committed repo artifact **before hc-b2 opened**. It was not, so the narrowing is not
written and item 7 stays open.

**Method and result.** hc-b2 opened and closed at agents `6c61393`; the tree immediately before it
is `a581a8c`. (1) The only `hc-*` review file at `a581a8c` is `docs/reviews/hc-b-review.md`.
(2) `docs/reviews/hc-b2-review.md` was **first added by `6c61393` itself**. (3) Six wordings of
hc-b2's findings over the **entire committed tree** at `a581a8c`: *"exactly two slots"*,
*"inconclusive"*, *"two invocations"*, *"the gate's home"*, *"Finding B"* → **0 files**;
*"stub-provider run with a worker"* → **1**, which is hc-b's own gate text, the premise hc-b2
refuted rather than hc-b2's finding. (*"placeholder"* matches 115 unrelated files — not a
discriminator, and recorded so the term list is not read as five clean hits plus one.) (4)
`hc-b-review.md` §Round 1 at `a581a8c` is about the decision-count split and clause 2.

**The structural reason matters more than the instance.** The narrowing's premise was that R2
supplies a pre-dating artifact. **R2 requires a review file to be *committed*, not to *pre-date* the
ticket** — and a ticket's own review file is committed **by** that ticket. So this process does not
currently produce the condition the narrowing needs, for hc-b2 or for any repair ticket. Writing the
narrowing would have installed a rule over a condition that is never met.

---

## 2. D3 — answered by running it (R-i), and it falsifies an hc-c claim

**The suites were green before hc-c.** Harness checked out at `b4d782a` (the commit before hc-c's
`e8889c3`), detached, with a positive control confirming the fix was absent
(`route_logging_to_stderr` 0 occurrences, the `:json` error clause 0). Five suites: **41 passed** —
the same 41 that pass after. Restored to `main`, control run in reverse (3 and 1).

**So D3's second horn is the true one, and the mechanism it demanded is this.** hc-c r2 enumerated
stdout reads **per file**. Per **invocation** — the unit the question is actually about — the five
files make **17** `subprocess.run` calls: **7 spawn the harness** (`["mix","run","--eval",…]`) and
**10 spawn a Python CLI** (`[sys.executable, SCRIPT]`). **All four `json.loads(result.stdout.strip())`
parses belong to the Python CLIs.** No harness invocation in those files reads stdout at all; the
seven read `returncode` and `stderr`.

**hc-c's *"the change helps them"* is therefore wrong.** They are **unaffected**. F8's conclusion —
no broken consumer — stands; only its rationale falls. Corrected in all three documents that
adopted it (`hc-consolidation.md` item 6, `hc-c-implementation-notes.md` §8c,
`hc-c-review.md` §Round 2), each as a dated note beside the original rather than a rewrite, per
decision 7.

**The error's class:** a census keyed on the wrong unit. Two subprocess families share a file, and
counting by file merged them — the adjacent-case shape, one level above the code it was written
about.

---

## 3. R-ii — BL-044 against R3's own wording, not hc-c's characterisation

**R3 asks:** *"establish whether `expected_fail()`'s design needs a real exit code from `run_agent`
to key on."* **hc-c's notes characterise it** as *"BL-044 … is R3's question for hc-d"*.

**Related, but not the same question, and the difference matters.** BL-044 is the *defect*
(`Mix.Tasks.Aetheris.run/1` discards `Aetheris.CLI.run/1`'s code, so a failed run exits 0). R3 asks
whether hc-d's design **needs that fixed**. One input, established here rather than left for the
audit to re-derive: `run_agent` already keys on the exit status —
`if run_aetheris --json run "${args[@]}" > "$output_file" 2>&1; then … else fail "$label → non-zero
exit"; fi` — so BL-044 makes that `else` branch **unreachable today**. That is an input to R3, not
an answer to it.

**Not settled, and why.** `expected_fail()` does not exist: `grep -c 'expected_fail\|KNOWN_RED'` over
`../aetheris/scripts/sprint.sh` returns **0**. R3's question is about *that design's* needs, and the
design is hc-d's own — which the step-1 gate is written against, and the gate is unauthored (§4).
Settling R3 now would mean inventing the design in order to answer a question about it.

---

## 4. The stop: hc-d's step-1 gate is unauthored, and its resolver points at this edit

**The resolver, quoted.** hc-d's `Step-1 gate` slot reads: *"`[R13: not authorable. hc-d's design is
not done, and a gate is written against a design. Resolver: hc-d's own opening section-scoped edit,
per R12 — the gate is authored there, before the ticket opens, and it answers R3 above.]`"*

**`per R12` is load-bearing.** R12's closing line: *"Authoring is the reviewer's (decision 11) via a
section-scoped edit; the edit is dated and lands before the ticket does."* So the resolver names
**reviewer-authored gate text carried in hc-d's opening edit**. This opening edit is D1, D2 and D3 —
a conditional R12 narrowing, a promotion candidate, and a §Not established entry. **None of them
authors the gate.**

**And it is not only the gate.** Against §6's seven fields, named by this document's own
§What the methodology owes (*"seven sections and no more"*):

```
AUTHORED      Scope
AUTHORED      Contract refs
NOT AUTHORED  Touches
NOT AUTHORED  Do not generate
NOT AUTHORED  Runbook update rule
NOT AUTHORED  Done-check
NOT AUTHORED  Claude-code prompt

authored = 2 of 7      not authored = 5 of 7
```

hc-d's section still carries its catch-all: *"Everything else is `[R13: deferred to the
section-scoped edit that opens this ticket, per R12.]`"* — and that edit has now happened without
authoring them.

**So this is the stop the rider names, not a substitution.** Authoring the gate myself would be
exactly what hc-b2 found and what R13 was sharpened to forbid: hc-b completed hc-c's gate
confidently, and **every defect was in the one slot completed confidently** — a placeholder agent, a
transcript that could not distinguish its outcomes, and a premise the harness does not permit
(`supervisor.ex:62`). Every R13-marked slot was sound. Writing five §6 fields and a gate on my own
authority would reproduce that failure with five times the surface, and would also break decision
11's split — content is the reviewer's, formatting is the destination file's.

**What would unblock it:** a reviewer-authored section-scoped edit carrying hc-d's `Touches`,
`Do not generate`, `Runbook update rule`, `Done-check`, `Claude-code prompt`, and the step-1 gate —
the gate written against the design those fields describe, and answering R3.

**Two constraints the document already records for that edit**, restated so the author does not
rediscover them: **the population is 29, not 31** (BL-077's Done-when says *"Audit all 31 cases"*;
derive it again and correct the row), and **BL-077's §Suggested order entry is stale** — BL-069
closed by retirement, so only the `expected_fail()` disjunct is live, and R9 forbids reading the
first as licence.

---

## 5. R-iii and R-iv — not reached, and why that is not a silent omission

**R-iii** (fail-safe defaults must state what happens when input is missing, malformed or empty) and
**R-iv** (whether the `tee`/`pipefail` coupling really makes BL-077 and BL-133 face 2 one ticket)
are both riders on design work that did not start. **Neither is discharged and neither is dropped**
— they belong to the round that authors the gate. R-iv in particular is a finding *about R1* and
can only be made after the design exists; asserting it now would be the guess R13 forbids.

---

## 6. For whoever opens hc-d next

- **§Not established item 7 is still open** and now carries a second question: whether repair
  tickets should commit their findings *before* opening, which would make D1's premise true rather
  than assumed.
- **Item 8 is resolved** (§2 above) and hc-c's *"helps them"* rationale is corrected in three
  documents.
- **`Five tickets.`** in §Ticket set still needs revisiting with item 7.
- **BL-044's status is unchanged**, with one new input on the record: `run_agent`'s `else fail`
  branch is unreachable while BL-044 stands.
- **No code changed in this ticket**, in either repo. The harness tree is byte-identical to the one
  hc-c's gates passed on — it was checked out to `b4d782a` for §2's experiment and restored, with a
  positive control both ways.

---

# hc-d's opening edit — 2026-08-09

Four reviewer amendments (E1–E3, and E1(e)'s list append) land here as a section-scoped edit, then
G0–G5 run. **E1 is a finding against the anatomy edit r1 and is upheld.**

## 7. E1 — the negative that could not match, re-derived

### 7a. The three defects, adjudicated separately

**Defect 1 — upheld against the packet, and it is worse than a wrong flag.** r1 §1d published
`grep -c "uncommitted|dirty|…"` with **no `-E`**. In BRE `|` is an ordinary character, so the
command as printed searches for one literal string. Its own control:

```
$ sed -n '1,262p' <anatomy notes> | grep -c 'uncommitted|dirty|porcelain|working tree|config.exs|playground_tokens'
0
$ grep -c   <same BRE pattern>   <anatomy notes>          # corpus that DOES contain the terms
1
```

The BRE form returns **1** over the whole file, and the single line it matches is r1.6's own
*quotation of the pattern* — the one place those characters appear with literal pipes. So the
published command was inert as evidence about the corpus, exactly as E1 says, and its only hit is
the sentence describing it.

**The command that ran, however, carried `-E`.** The packet's echoed line and its executed line
were different text; the `0` was a real observation published with a false transcript. That is not
the lesser defect — it is **Packet-integrity** (harness `CLAUDE.md`: *"Review packets are generated
artifacts, not retyped ones"*), and it is why the standing rule offers two options, *transcribe the
command that ran* or *re-run and publish the re-run*. Retyping is the third, and it is the one that
failed. **Nothing in the packet could have exposed the divergence** — the reader sees one command
and one number, and both were individually plausible.

**Defect 2 — upheld.** The control line read `grep -Ec "same pattern" whole file`: a prose
placeholder, not a command. What *ran* was in fact the same pattern and flags over the whole file,
a valid superset control — but nothing in the packet showed that, and a control a reader cannot
re-run is not a control. It is replaced below with a **disjoint** corpus, which is stronger than
the superset the run used.

**Defect 3 — upheld, and it is carrier 2 of the count rule.** The packet printed `10` beneath prose
saying `8`.

### 7b. E1(a) — the negative, re-run with `-E`, same range

```
$ sed -n '1,262p' <anatomy notes> | grep -Ec 'uncommitted|dirty|porcelain|working tree|config\.exs|playground_tokens'
0
$ ... ; echo $?      # exit captured from the invocation
1                    # 1 = no match, the expected shape of a true negative
```

**0. E1(d) does not fire** — the anatomy edit's own §1–§6 do not record the observation, so item 9's
*"only durable record"* clause is not refuted and needs no correction on that ground.

### 7c. E1(b) — a real positive control: same pattern, same flags, disjoint corpus

Lines 263–end are the r1 sections: known to contain the terms, and sharing no line with the
negative's range. A non-zero here is what makes the zero above readable as absence rather than as a
broken pattern.

```
$ sed -n '263,$p' <anatomy notes> | grep -Ec <same pattern, same flags>
10

$ sed -n '263,$p' <anatomy notes> | grep -En <same>      # enumeration printed beside the count
82:A2 asked for the `config/config.exs` block to be recorded verbatim and then reverted so the tree
87:| `09:03:07` | block present, uncommitted | mtime; `git diff` shows +4 |
89:| `09:24:05` | block **gone** | mtime moved; `grep -c playground_tokens` → 0 |
90:| `09:26` | tree clean | `git status --porcelain` → **0 lines** |
98:**G0 is transcribed as authored** and is the standing consequence: hc-d stops on a dirty harness
126:consumers, 7 hc-b2's anatomy (resolved), 8 the provenance suites (resolved), 9 the `config.exs`
156:  harness working tree is clean at the ticket's start, `git status --porcelain` zero lines, HEAD
158:  run on an uncommitted tree cannot be re-derived from any commit. Plus the §Not established entry,
188:the cause — the operator added the `config.exs` block while setting up Rig to authenticate against
192:`uncommitted|dirty|porcelain|working tree|config.exs|playground_tokens` over this file's §1–§6
```

Ten lines, listed. The pattern works; the zero in 7b is absence.

### 7d. E1(c) — 8 against 10, reconciled

**They count the same file at different commits, and each is right about its own.**

```
$ git show d29f5c6:<anatomy notes> | grep -Ec <same>
8
$ git show 149c1a8:<anatomy notes> | grep -Ec <same>
10

$ diff <(git show d29f5c6:… | grep -E <same>) <(git show 149c1a8:… | grep -E <same>)
> the cause — the operator added the `config.exs` block while setting up Rig to authenticate against
> `uncommitted|dirty|porcelain|working tree|config.exs|playground_tokens` over this file's §1–§6

$ diff <(git show d29f5c6:… | sed -n '1,262p') <(git show 149c1a8:… | sed -n '1,262p')
(identical)
```

**The document's figure is the wrong one.** `8` was measured at `d29f5c6` and then written into
`149c1a8`, so it was already stale in the commit that carries it — the self-falsifying-claim shape.
The two added lines are r1.6's own prose about the block and its quotation of the search pattern:
**the count was moved by the sentences describing it.** That is why a count must name its commit,
and both sites are now amended with theirs. The negative's corpus, by contrast, is byte-identical
across the two commits, so the **0** holds at both.

### 7e. The clause E1 was protecting — derived over both repos, not inferred

The negative never established *"the only durable record"*; it established that one range of one
file lacks the observation. The claim quantifies over both repos, so it is derived that way:

```
$ git grep -l 'playground_tokens, \["tok-abc"\]' -- .                    # agents, all tracked files
docs/milestones/hc-consolidation.md
$ git -C ../aetheris grep -l 'playground_tokens, \["tok-abc"\]' -- .     # harness
(no match)
```

**One file, one repo.** §Not established item 9 is the only durable copy of the four lines. The
clause stands, now derived rather than inferred. **Item 9 stays `[RESOLVED]` either way** — its
resolution rests on the operator's attribution, never on any of these searches.

### 7f. What it cost, and the rule it lands under

F9 ratified the positive-control rule **in this same round**, and r1 then applied it in form and not
in substance: a check trusted because it was shaped like a check. That is instance **(vii)** on the
promotion candidate's open list — the first entry there that is claude-code's rather than the
reviewer's, which is why the candidate's heading was widened off *"The reviewer…"* under E1(e). The
narrow operational residue: **a packet publishes the invocation, never a retyped `echo` of it.**

## 8. E2 — §Not carried's count, replaced by a pointer

Authorised by the reviewer after being reported without authority at r1.4 Finding 1 and again at
r1.6. The `[V]` asked for the sentence exactly; it read *"the open questions are §Not established's
**four**"* (`hc-consolidation.md` §Not carried, §Open for the close bullet) — confirmed verbatim.
The replacement points at the `[OPEN]` markers A7 introduced rather than restating a number, so the
two mechanisms are now coupled: the marker convention is what makes the pointer resolvable.

## 9. E3 — resource failure and findings failure are different results

Appended to hc-d's Done-check item 1, generalising the dialyzer elision this round reported: a green
`mix dialyzer` reporting *"PLT is up to date"* establishes findings and not memory headroom, and if
headroom is the question a cold-PLT build is what answers it. The distinction now lives in the
anatomy rather than only in a packet, which is where E3 says it belongs.

## 10. Scope of this edit

Four documents' worth of amendment across **two files**, both docs. No `sprint.sh` change and no
code — those belong after G0–G5. R-iii and R-iv remain undischarged and are carried into the gate
(G3 is R-iv's resolver).

---

## 11. The step-1 gate — G0–G5, every verdict explicit

Run before any edit past the opening section-scoped one. Harness at `1b09b23` throughout.

| Gate | Verdict | What was established |
|---|---|---|
| **G0** | **clean → proceed** | `git -C ../aetheris status --porcelain` → **0 lines**; HEAD `1b09b23` |
| **G1** | **R16 holds → proceed** | A failing run's capture carries `"status":"failed"`, read by `sprint.sh`'s own `json_read` (sourced from `:87–110`, not re-implemented). It is the **only** parsing object in the capture and its last non-blank line. Positive control: a stub run reads `done` |
| **G2** | **BL-044's reach CONFIRMED** | `run_aetheris()` is `mix aetheris "$@"` (`:40–42`) — the mix task, never the escript. Exit **0** on a run whose payload says `failed`. So R16 is load-bearing |
| **G3** | **same status both ways → proceed** | With and without a `tee`, the caller sees **0** on the same failing case; captures content-identical (timestamps only). Positive control: `false` under `pipefail` yields **1** with and without `tee` |
| **G4** | **absent → this ticket authors them** | `expected_fail`/`KNOWN_RED`/`FAILURES` → **0 matches**. Positive control: the same anchored form finds `ok()` `:35` and `fail()` `:37` |
| **G5** | **derived 29, matches one of the two → proceed, correct the row** | See §12 |

**G2's qualification, which R16 anticipated and this run confirms.** `run_agent`'s `else fail` arm
is dead to *run* failure and live to *harness* failure: every failing run above exited 0 and took
the `if` branch, while the malformed-fixture run (§13) exited 0 too but only after stalling. The arm
survives as a second signal, never the only one.

## 12. G5 — the population, derived under one pattern

**Pattern, stated once:** `^if \[\[ "\$TARGET" ==` — the line that opens a case block.

**30 blocks, 29 distinct case names.** `uc4` opens twice (`:202`, `:303`); `all` is the selector,
not a case. Enumerated: `capability_matrix chaos cloudcost docbuilder docbuilder_context
docbuilder_fresh docbuilder_fresh_render docbuilder_invoice_jinja docbuilder_offer_letter
drift_check drive eduloka email eval m12 news payslip playground_api uc1 uc2 uc3 uc4
uc_api_agent_t1 uc_api_agent_t2_greenfield uc_api_agent_t2_steady uc_api_agent_t3 uc_api_agent_t4
uc_api_agent_t5 uc_auto`.

**Every `$TARGET` line the pattern does NOT match is accounted for**, not dropped: `:192` is the
credential preflight's `!=` guard, `:1467` an inner exit inside the `playground_api` case. Those are
the only two.

**The figures are identical at `fa158a4` — the commit BL-077 cites — and at `1b09b23`.** So the row
was wrong when filed, not overtaken by drift.

**The "31" provenance is NOT established, and is therefore not offered.** `grep -c 'section "'`
returns exactly **31** at both commits (29 indented + 2 unindented), making it the only quantity in
the file equal to 31 and a live candidate. It is not evidence: a plausible explanation for a wrong
number is not a truth-maker, and nothing in either repo settles what the row's author counted.
**R1's parenthetical is corrected in the same edit** — the count of two was right, the members were
not. The unindented hits are `:176` and `:3161`; `:38` is the `section()` definition and matches the
pattern **0** times.

## 13. The contract — what landed, and how each clause was observed

**Posture (R7).** Fail-safe with per-arm promotion. `fail()` keeps its name and every call site;
what changed is that its red is now **counted** (`NOT_DECLARED`) instead of vanishing. Promotion is
`blocking_fail`/`blocking_ok`, per arm. **One arm is promoted** — the `drift_check` case, the only
one individually verifiable here without credentials or network. Every other arm stays undeclared
**by design**, and the count is printed, which is R7's non-optional constraint rather than an
omission.

**Four counters, all printed on every run including when zero.** Observed on a real run:

```
Exit contract (BL-077):
  arms declared blocking .......... 1
  arms tracked KNOWN_RED .......... 0
  reds NOT YET DECLARED ........... 0   (printed, non-blocking — R7 fail-safe)
  blocking failures ............... 0
  → sprint will exit 0
```

**The mutation check, on a genuinely broken state rather than a simulated one.** A phantom event
type (`hcd_phantom_event`) added to `docs/rig/specs.md` §6 — `git status` confirming the tree really
changed — made `drift_check` emit `[FAIL] … (ghost)`. `./scripts/sprint.sh drift_check` exited
**1**, `blocking failures = 1`. Restored via `git checkout --`, tree clean, exited **0** again.
**A first mutation was insufficient and is reported rather than dropped:** deleting a documented
payload field produced only INFO, so the arm never went red and the sprint still exited 0 — the
first attempt did not exercise the check, and a second was constructed until it did.

**R17's three arms, each constructed and observed** (helpers sourced verbatim out of `sprint.sh`):

| Arm | Input | Result |
|---|---|---|
| red + **unlisted** | `fail …` | `[FAIL]`, `NOT_DECLARED=1`, `FAILURES=0` — printed, counted, non-blocking |
| red + **listed** | `expected_fail BL-069 …` | `[KNOWN-RED] … (tracked: BL-069)`, `FAILURES=0` |
| **(a)** promoted arm red | `blocking_fail …` | `[FAIL] … [blocking]`, `FAILURES=1` |
| **(b)** entry with no valid row | `expected_fail "" …` / `expected_fail not-a-row …` | both `[FAIL] … [blocking]`, `FAILURES=3` |
| **(c)** known-red that PASSED | `known_red_healed BL-069 …` | `[FAIL] … stale; delete it [blocking]`, `FAILURES=4` |

**R18(a), demonstrated not argued.** The capture is `exec > >(tee -a "$SPRINT_CONSOLE") 2>&1`, which
creates **no pipeline**, so the status the counter drives is untouched by capturing. G3 measured the
alternative directly rather than reasoning about it.

**R18(b), the streams stay merged.** `2>&1` follows the stdout redirect. On a real capture: 29
`[INFO]`/`[OK]` lines and 11 `[PASS]`/`[WARN]` lines from the tool, interleaved in one file. No
split, so R11's payload-specific `grep -q run_id` guard is unaffected.

**R1's provenance stamp and bound, on an artifact the run produced** (`sprint/20260809_121954/`):
all four required elements plus a dirty flag for each repo, and the bound **enforced**, not merely
printed — the sweep runs at the start of every sprint and reports what it pruned.

```
harness_commit: 1b09b237d5689880aaf48c4e640ebe4217614dcb
harness_dirty:  yes
agents_commit:  05a4cdb5a1e9c995f03d6f5964f72a61553cdde9
agents_dirty:   no
target:         drift_check
command:        ./scripts/sprint.sh drift_check
retention:      30 days — STATED AND BOUNDED, and enforced by the sweep below
```

**Why 30 days:** long enough for BL-075's *"three further full-output runs come back clean"* to be
counted across a review cycle, short enough that a gitignored directory on one machine does not grow
without bound. `SPRINT_RETENTION_DAYS` overrides it.

## 14. R3's named question, answered

**Does `expected_fail()`'s design need a real exit code from `run_agent` to key on? — No.** It keys
on the assertion's own outcome at the call site, which is a shell condition, not a child process's
status. G1 and G2 confirm the status word is available where a verdict does need one. **So BL-044
stays filed with the finding recorded, `../aetheris/lib/mix/tasks/aetheris.ex` does not join
`Touches`, and no file under `../aetheris/lib/` was touched** — which is also what
`Do not generate` requires.

## 15. R-iii and R-iv, discharged

**R-iii — fail-safe defaults, stated for missing/malformed/empty input, not only wrong input.**
`expected_fail` with an **empty** ref, a **malformed** ref, and a ref that is merely absent all take
the same branch: `[FAIL] … [blocking]`. That is R17(b) and it is deliberate — absent input is
unknown, not benign, and a default that treated absent as green is the defect this ticket removes.
The counters initialise to `0` and are only ever incremented, so a counter that was never touched
prints `0` as a **status**, and the summary prints it whether or not anything happened.

**R-iv — the `tee`/`pipefail` coupling, and whether BL-077 and BL-133 face 2 are really one
ticket.** G3 is its resolver and the answer is nuanced: **the coupling is real but avoidable**, and
avoiding it is what makes the two separable *in implementation* while still needing to be decided
together. A `tee` in a pipeline does propagate correctly under `pipefail` (positive control: `1`
both ways), and the chosen `exec > >(tee …)` form creates no pipeline at all. **So the work did
separate cleanly after the gate — that is a finding about R1, reported here rather than taken as
licence to have split mid-ticket.** They still belong in one ticket for the reason R1 gives: the
decision about the capture's *shape* is what determines whether the counter's status survives, and
that decision cannot be made in a ticket that does not own both.
