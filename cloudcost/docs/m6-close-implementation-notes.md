# m6 close — implementation notes

**A verification pass and a ritual. Nothing was built. Three findings; at r0 none was fixed, and
at r1 the reviewer authorised fixing one of them.**

Measured at agents `e0c1ee2`, harness `d19f4b6`, both clean and level with origin at the start
of the session and unchanged in the harness at the end. Every figure below was derived in this
session at those commits unless a line names a different one.

**Two rounds, and this file records both.** **r0** ran the gate, the close criteria, §7's scan and
census, and both sprint legs, disposing nothing — the ticket reserved the promotion and R24
verdicts for the reviewer, and reported rather than fixed what it found. **r1** landed the review's
rulings: the recovered-spend register's first entry rewritten on an established account (the two
readings r0 left open were both wrong), three promotions and five declines, gc's five carried
candidates dropped under R24, §Ticket set's two missing entries added under an explicit
authorisation, and §7's closing-test finding carried to BL-150. **r0's text stands where it was
superseded** and each supersession is a dated block at the position it occupied, per decision 7 —
the searches and controls are load-bearing even where the inference drawn from them was not.

---

## 1. Gate

**(i) Both repos level, trees clean.** `git status --porcelain` empty in both;
`git status -sb` returns `## main...origin/main` with no ahead/behind marker in both. Agents
`e0c1ee2` (m6 t4), harness `d19f4b6` (m6 t2b). The harness is untouched by this ticket and no
conclusion to the contrary was reached.

**(ii) §7 read in full** (`../aetheris/docs/methodology/milestone-methodology.md:220-255`).
**Four things §7 requires that this prompt does not say**, reported because a close run to a
prompt rather than to §7 is the wrong artefact:

| # | §7 requirement | prompt | disposition here |
|---|---|---|---|
| 1 | step 4 ¶2 — **census the prior cycle's promotion claims** against both `CLAUDE.md` files; *"Two found by eye is not a census"* | absent | **RUN** — §4b |
| 2 | step 5 — **run the drift checker** | the done-check omits it | **RUN**, post-commit — §7 |
| 3 | step 4 ¶1 — verify a promoted entry **by opening the file**, quoting it with surrounding lines | absent | **RUN** — §9. Three entries promoted at the close review and each quoted from `CLAUDE.md` after the edit, with line numbers, plus the candidate-comparison the census's own promoted rule requires |
| 4 | closing test — the same finding class should not appear as `blocking` in two consecutive milestones | absent | **ASSESSED**, and it **cannot be run** — §4d |

**And one deviation from §7, which the close review closed.** Step 3 says claude-code commits the
promotion in its own PR. As first written this close promoted nothing — the ticket reserved the
ruling on §4a's enumeration for the reviewer, and Do-not-generate forbade landing one first — so
§7 ran to step 2 for m6's own candidates and completed only for the census.
`[Closed 2026-08-14 at the close review: the ruling landed, three candidates were promoted, five
declined and gc's five dropped. §7 is now complete for this milestone, and the deviation was one
of sequencing rather than of substance — the ritual's steps ran in the order the review process
imposes, not in §7's own.]`

**(iii) R24's bar** (`docs/milestones/hc-consolidation.md:627-636`), quoted:

> **a promotion candidate expires: carried at two consecutive closes without promotion, it is
> dropped at the second.** … **So: promoted or dropped at the second close, and the drop is
> recorded once and not re-litigated.** A dropped candidate may return only as a fresh finding
> from fresh evidence, not as the same entry carried a third time.

Where it bites is §4c.

**(iv) Companion artifacts and practices.** Established by reading how the two preceding closes
closed — `docs/milestones/gc-stale-claims.md:832-944` and `cloudcost/m5-n1-compose.md:971-1168`
— rather than from this prompt. Both produce, appended to the milestone document in this order:
**§Dispositions** (every candidate and carried-in item, disposition count equal to entry count)
→ **§Close criteria — the per-clause assessment** (a table; *"a clause satisfied by nothing is
stated unmet, not omitted"*) → **§Milestone summary** with `### What shipped`,
`### What the close found`, `### What stays open, and why that is correct`,
`### Open for the next cycle`, last in the file. Plus a committed implementation-notes file.
**This close follows that shape**, which is wider than the prompt's W3a/W3b — the prompt names
the last two subsections only, and the per-clause table is what its W1 actually asks for.

**One divergence from both predecessors, and it changes the method.** `cloudcost/m6-github.md`
carries **no §Promotion candidates, §Carried in, §Not established or §Dispositions section**,
and **no m6 review file is committed** anywhere in the repo (`git log --name-only` over
`e4fabb7..e0c1ee2` lists none; the cycle's packets are scratch artifacts). m5 and gc both
accumulated candidates during the cycle and disposed a standing list at the close. m6 did not,
so §7 step 1's scan had to be run from scratch over the six implementation-notes files and the
runbook/`milestone.md` sweeps those tickets performed. That is exactly the channel step 1's
second paragraph exists to cover — *"the review files are not the only input"* — and here they
are not an input at all.

---

## 2. The close criteria, quoted and discharged

`cloudcost/m6-github.md:379-392`, quoted at HEAD before anything was assessed:

> ## Close criteria
>
> Verify and record: t1, t2 and t3 landed with their done-checks clean; the
> sprint's cloudcost arms report the same verdicts as at m6's open or better;
> the runbook's provider list and wiring section include GitHub; what this
> milestone **recovered** — spend eliminated or waste found — is recorded with
> its basis alongside what it built; and every decision above is either applied
> or carries a recorded reason it was not.
>
> `[Clause added 2026-08-13 at t2b, by arbiter ruling. Ground: m6's scout found
> unfilled paid seats before any adapter shipped, and a milestone whose subject
> is recoverable spend should state its own. The criterion is that the figure is
> recorded with its basis, not that any particular figure was achieved — a
> recorded zero with its basis satisfies it.]`

The per-clause assessment is in `m6-github.md` §Close criteria — the per-clause assessment.
What follows is the derivation behind the two clauses that needed work.

### 2a. Recovered spend — the register, and what the evidence actually supports

**Two entries with different bases, as the criterion's own *verify and record* asks.** Entry 2 is
settled by measurement. **Entry 1 took three passes to settle and the first two were wrong in
different directions** — run under arbiter ruling AS1–AS4 at this ticket's gate, then superseded
at the close review by the established account in AS3 below. The searches, their controls and the
live read are recorded as they ran, because what they established is load-bearing even where the
inference drawn from them was not.

**AS1 — the search for a before-state. Nothing, with both controls.**

| search | corpus | result |
|---|---|---|
| `filled_seats` | agents tree, excl. `.git` | **0** |
| `filled_seats` | every session scratchpad under this project | **1**, and it is **this session's own AS1 command echo** in its background-task output file (`…/931b7a74-…/tasks/bgwgdozui.output`, empty of content), not a record of anything |
| `seat_breakdown` *(positive control)* | agents tree | **1** — `cloudcost/docs/m6-t2-implementation-notes.md`; the apparatus is live |
| `zzq-as1-control-m6close-3318` *(negative control, minted fresh, verified before use)* | agents tree | **0** |

No committed m6 scout document exists. **The nearest thing found is not the before-state**, on
two independent grounds: `m6-t2-implementation-notes.md:320-322` records a live
`/orgs/{org}/copilot/billing` `seat_breakdown` of
`{total: 6, active_this_cycle: 6, inactive_this_cycle: 0, pending_invitation: 0,
pending_cancellation: 0, added_this_cycle: 0}` — which is the **Copilot** product's breakdown,
not the organisation plan's `plan.seats`/`plan.filled_seats` pair an unfilled-seat count would
come from; and it was read at **t2, 2026-08-13**, *after* the scout, so if seats had been
removed before t2 it would already be an after-state.

**The scratchpad self-hit is the promoted negative-control rule firing on this close's own
instrument.** *A negative control is spent by publication* (harness `CLAUDE.md`, promoted at
gc t4) describes a token spent by a record quoting it. Here the searched-for term was spent by
**the search itself**, one tool call earlier in the same session, before any record existed.
Recorded as a third demonstration; **not filed and not promoted** — the rule already covers it,
and this is an instance rather than a new claim.

**AS2 — the present state, read live.** One read-only `GET /orgs/{org}` under the isolation
discipline: `Authorization: Bearer` built from `CLOUDCOST_GITHUB_TOKEN` only, the seven ambient
shadow/redirect names (`GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`,
`GITHUB_ENTERPRISE_TOKEN`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `GH_HOST`, `GITHUB_API_URL`)
stripped with `env -u` before the interpreter started, no `gh` credential resolution, no token
value read or printed. The organisation login is **not recorded here or in the packet** (U2).

```
read at: 2026-08-14T09:01:53+00:00
plan.name         : team
plan.seats        : 19
plan.filled_seats : 16
```

**Three unfilled organisation seats, today.**

**AS3 — as first written this close recorded shape (c) with both readings of the live number left
open. Both are now closed, and neither was correct.**

> **`[Superseded 2026-08-14 at the close review, by arbiter ruling and a correction to it. The
> paragraphs this block replaces stood on an inference from the live read, which was sound and
> incomplete: the read was taken before the operator acted. What follows is the established
> account. AS3's shape (c) was the right disposition for the wrong reason — the figure was not
> established *by this close's searches*, and it was establishable all along from the provider's
> own billing page, which no search here reached.]`**

**What happened, established.** The operator had reached GitHub's Remove-seats confirmation page
for a 19→16 reduction and **had not submitted it** at the time this close's live read was taken.
After the read, the operator submitted it; the provider acknowledged — *"You have successfully
downgraded to 16 licenses"* — and the organisation's People view reads **16 of 19 seats used**.
So the live read's `plan.seats 19` is explained twice over, and **both explanations are true
rather than one of them**: the read **predates the submission**, and **purchased seats do not
fall until the effective date** in any case. Recording only one would leave a reader thinking the
other had been ruled out.

**The register entry, in four parts** — `m6-github.md` §Milestone summary → *What m6 recovered*
carries the same four and this is the derivation:

1. **The waste, and it now has a basis it did not have before.** **Three unfilled purchased
   seats**, **Team** plan, **4 USD per seat per month** — **12 USD per month**. Sourced from the
   provider's own billing page rather than from anyone's recollection. **The figure three now
   enters the register on that footing, and only on it**: AS1's searches did not establish it and
   nothing in this repo does.
2. **The action.** Downgrade **19 → 16 licences**, confirmed by the operator **2026-08-14** and
   acknowledged by the provider. **Effective 2026-08-20**, the next billing cycle.
3. **Why this close's own live read shows 19.** Both facts above, stated as two.
4. **The check that closes the entry, with its date.** A read of `plan.seats` **on or after
   2026-08-20** returning **16**. **Not performed by this close and not performable by it** — the
   value cannot move before that date, so an earlier read would confirm nothing. **No row is
   opened for it**: it is a dated line in the register with a stated condition, which is what the
   criterion's *verify and record* means. Opening a row would convert a scheduled reading into
   work, and there is no work.

**AS4 — the criterion worked, and this is the strongest evidence it earns its place.** The clause
was added at t2b so a milestone states what it recovered *with a basis*. **Its first exercise
found the milestone's own headline recovery unperformed** — the seats still purchased, the figure
with no source in any artefact, and the action staged but not submitted. **That it was then
performed does not soften the finding.** The recovery existed as a belief for two days, from the
scout to this close, and nothing checked it in between; what checked it was this criterion being
run rather than asserted. A milestone whose subject is recoverable spend had, until the clause
fired, not recovered the spend it opened by naming.

**What the searches were still right about.** AS1's result stands unchanged and is not softened
either: **no before-state was recorded in any committed file, fixture or scratchpad**, with a
positive and a negative control. The figure was recoverable from the provider and from nothing
this repo holds — which is a fact about the repo, and the reason the entry above names its source
explicitly rather than stating a number.

**Entry 2 is clean and needs no such work.** `cloudcost/docs/m6-t3-implementation-notes.md:200-222`:
six Copilot seats, the stalest 8 days idle at reference date 2026-08-14, nothing firing at the
ruled threshold of 30 and nothing at 14 either. AJ4's own words — *"this organisation's Copilot
seat inventory carries no recoverable spend today"*. Re-confirmed live by this close's own
GitHub sprint leg: `github_orphan_candidates_2026-08.json` at reference date
`2026-08-14T08:59:51Z` reports `totals.candidates 0`, `monthly_saving_estimate 0`, over
`totals.resources 6`, with `seat_inactive_days 30` untouched. **A measured zero with its basis**,
which the criterion's own clause says satisfies it.

### 2b. The operator gate — discharged

t4's notes state it outstanding (`m6-t4-implementation-notes.md` §9), which was true when
written. It has since been run and passed. **Observed by the operator, not by a session** —
nothing in this session or t4's could perform it, which is §9's own point.

| leg | observed |
|---|---|
| 1 | Rig's **Agents** view lists `fetch_github.py`, with the agent label reading `Cloudcost` |
| 2 | An **Orchestrator** run with `CLOUDCOST_PROVIDER=github` in *Additional env vars* planned `cloudcost_orchestrator.exs` as a GitHub run and produced a report |

Both are the two legs §9 names. **Discharged 2026-08-14.** t4's §9 carries a dated discharge
block appended in this commit — the section stands unrewritten, per decision 7.

**What the same click-through found while passing.** The approval card claimed the run *"detects
orphans and optimization signals"*. **Appended to BL-156, and nothing opened** — that row was
filed for exactly this class one day earlier. Checked at HEAD rather than relayed:
`cloudcost/scripts/detect_optimization_signals.py:1-13` is scoped to *"AWS S3 / ECR / Secrets
Manager"* and its own docstring records decision G — *"the core pipeline never reads it"*. So
the claim is wrong twice: the script cannot run on GitHub, and no provider's pipeline invokes it
at all. **That second half is tree-checkable**, which the row's first instance was not, and the
appended paragraph says so.

### 2c. D1–D7, individually

Every decision was traced to where it landed. **All seven are discharged; none is unapplied.**
The table is in `m6-github.md` §Close criteria — the per-clause assessment. Two need a note.

**D4 was applied at t2 and stopped binding at t3, inside the same milestone.** t2 applied it —
`money(pricePerUnit × (netQuantity / seats))` with the multiplication at full precision and
`money()` after, pinned by mutation row M4 (*"round the rate before multiplying"* → failed,
`0.0 == 50.4`), which is the one test assertion D4 asks for. **t3's cost-model ruling removed the
multiplication**: `seat_monthly_cost` now returns `money(float(pricePerUnit))`, the rate. The
function's own docstring states the consequence rather than leaving it as an absence — *"m6 D4 no
longer binds here… `seat_monthly_cost` was its only such site in this adapter"* — and replaces
D4's pin with the opposite property, that the estimate does not move with `netQuantity`
(`tests/test_fetch_github.py:738`, `:812`). **D4's §Ratified decisions entry stands unamended**
while §t3 carries the change. Reported, not edited: amending a ratified decision is the arbiter's,
and the two documents do not contradict — D4 says what it governs, and t3 says the site is gone.

**D5 is the criterion's *carries a recorded reason it was not* arm, not a finding.** D5 governs
*"BL-136's report, **when built**"*. BL-136 is unbuilt and was never in m6's scope; the decision
is a standing constraint on work that has not happened. Recorded as **not applicable yet**, with
that reason, rather than as applied or as a gap.

**D2 and D3 were checked against code, not against the notes claiming them**, because they are
the two with no dedicated call site. D2: `--period` is `YYYY-MM` only
(`fetch_github.py:864`, validated at `:391`), and the single `per-day` mention in the module is
the detail endpoint used as a reconcile source, not an emitted granularity. D3: `money()` is
`round(float(value), 2)` (`_normalized.py:92`) and its three call sites in `fetch_github.py` are
`:484` (a provider's own per-item amount), `:497` (**the sum taken at full precision, rounded
once after** — pinned by `test_the_total_is_summed_at_full_precision_and_rounded_once`,
`tests/test_fetch_github.py:396`) and `:598` (the rate). Nothing rounds before a multiplication,
because after t3 nothing multiplies.

---

## 3. Done-check

Exit codes read before any artifact was opened (**BL-153**). Both pytest scopes, because
**BL-152** means neither covers the other.

```
$ cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest cloudcost/tests/ -q
465 passed in 155.27s (0:02:35)                                          exit 0

$ cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest tests/ -q
129 passed, 7 xfailed in 1.38s                                           exit 0
```

Both figures identical to t4's (`m6-t4-implementation-notes.md:337-341`, `:470-476`) — the
number that would have caught an accidental edit in a ticket that changes no executable line.

```
$ cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/github-cloudcost.env && set +a \
    && CLOUDCOST_PROVIDER=github ./scripts/sprint.sh cloudcost
exit 0   ·  76 lines  ·  0 [FAIL]  ·  1 [WARN]  ·  run cloudcost-orch-github-yvXVsQ

$ cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/do-cloudcost.env && set +a \
    && ./scripts/sprint.sh cloudcost
exit 0   ·  76 lines  ·  0 [FAIL]  ·  0 [WARN] ·  run cloudcost-orch-digitalocean-DubQyw
```

The GitHub leg's single WARN is the ambient credential-shadow notice — unchanged from t2c and
t3, non-blocking by construction, and the run is unaffected because the hermetic prefix strips
those names (the leg's own poison controls and default-deny arms assert it in the same run).

**The tree did not move under either run.** Source-tree mtime hash over `cloudcost/scripts`,
`cloudcost/agents`, `cloudcost/templates` and `cloudcost/tools.json`:
`3c0937f21b12eb01a385cbc72094cf36` **before the first leg and after the second, identical** —
BL-153's second mechanism, applied as the discipline it is rather than assumed away. `git status`
clean after both; the sprints write only to gitignored `cloudcost/output/`.

**On completeness of the capture — nothing is elided, and the published capture is larger than
the run's own.** Each leg was redirected whole to a file, never viewed through `tail`. Diffed
ANSI-stripped against the run's saved `sprint/<ts>/console.log`: my capture is **76 lines**, the
saved capture **62**, and my capture is a **superset** — it holds the 13 prerequisite lines that
print before the capture stream opens, plus the `console capture drained complete` line, and it
carries the `[OK]`/`[INFO]` prefixes the saved file writes without. **No line of the saved
capture is missing from the published one.** This is the inverse of t4's situation, where a
`tail -60` of a 62-line capture had to be topped up from the saved file.

### 3z. r1 — both pytest scopes re-run, and the sprint legs exempt with their truth-maker

`Ruled at the close review (AT7): re-run both pytest scopes only. The sprint legs are exempt on
t2's ground, and the ground is stated rather than assumed.`

```
$ cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest cloudcost/tests/ -q
465 passed in 152.62s (0:02:32)                                          exit 0

$ cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest tests/ -q
129 passed, 7 xfailed in 1.34s                                           exit 0
```

**Both identical to r0's, which are identical to t4's.** Three consecutive measurements of the
same figure across a close that changes no executable line — which is the only thing that would
have caught an accidental edit while r1 rewrote four documents.

**The exemption, with `git diff --stat` as its truth-maker** rather than an assertion:

```
$ git diff --stat                    # r1 working tree against 04ce9bc
 CLAUDE.md                                       |  18 ++
 cloudcost/docs/m6-close-implementation-notes.md | 285 ++++++++++++++++++------
 cloudcost/m6-github.md                          | 148 +++++++++---
 docs/backlog-2026-06.md                         |  19 ++
 4 files changed, 376 insertions(+), 94 deletions(-)

$ git diff --name-only | grep -vE '\.md$'
(no output)
```

**Every changed path is `.md`.** No executable, no agent file, no adapter, script, template,
manifest, matrix, sprint script or harness file — so neither sprint leg can observe this round,
and re-running them would re-derive r0's result at the cost of two live provider runs. **Nor is
`drift_check` re-run**, on the separate ground stated in §7.

**Leak check over the r1 diff**, since one round of this milestone already lapsed on U2: the
organisation login, `ghp_`, `github_pat_` and `Bearer` each return **0**; positive control
`plan.seats` returns **10**, so the search is live over the diff it claims to cover.

---

### 3a. The rule-legibility arm, quoted against **m6's open**

That arm is non-blocking by construction, so a green summary is not sufficient evidence and the
line itself is quoted. **m6's open baseline** is `cloudcost/docs/m6-t1-implementation-notes.md:316`,
the r0 *before* reading — the sprint as it stood when m6 opened.

**DigitalOcean — byte-identical to m6's open:**

```
m6 open  : [OK]  rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance,
                 load_balancer, volume] all drawn from the canonical set
this close: [OK]  rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance,
                 load_balancer, volume] all drawn from the canonical set
```

**GitHub — and it has no m6-open baseline, which is stated rather than papered over:**

```
this close: [OK]  rule legibility: 6 resources evaluated, 0 skipped; types [seat] all drawn
                 from the canonical set
```

**The GitHub leg did not exist at m6's open** — it arrived at t2b (`bcb63e6`). So the criterion's
*same verdicts as at m6's open or better* is satisfied for this leg in the *better* direction, by
the arm existing at all, and **there is no like-for-like line to quote**. Its within-m6 baseline
is t3's live run (`m6-t3-implementation-notes.md:385-419`: exit 0, 76 lines, zero `[FAIL]`, six
usable resources), against which this run is unchanged. Offering a comparison against a baseline
that never existed is precisely what this criterion is trying to prevent, so it is not offered.

### 3b. The harness gate set — the check, not the conclusion

Ruled by the arbiter as AR1–AR5 at this ticket's gate. The offered premise — *"the harness is
byte-unchanged since `d19f4b6`, and gc t4 discharged `mix dialyzer`"* — is two true sentences
that **do not connect**: gc closed 2026-08-12 with the harness at `66a9ca5`, and m6 t2b moved it
to `d19f4b6`. **The harness has changed once since that discharge**, and the citation covered a
tree that is no longer the tree.

**AR2a — what changed.** `git diff 66a9ca5 d19f4b6 --name-only` in the harness:

```
scripts/sprint.sh
```

One path; `1 file changed, 36 insertions(+), 5 deletions(-)`. **No `.ex` and no `.exs`**, so
AR4's stop condition does not fire.

**AR2b — does any harness gate read it?** `compile`, `format --check-formatted`, `credo` and
`dialyzer` read `.ex`/`.exs`; `deps.get` and `hex.audit` read `mix.exs`/`mix.lock`. None of those
paths moved. `mix test` is the one that could surprise, and it was checked directly:

| search | scope | result |
|---|---|---|
| literal `sprint.sh` | `lib/`, `test/`, `mix.exs`, `config/` | **0** |
| `System.cmd` / `System.shell` / `Port.open` / `:os.cmd` | `test/` | present, and every target is `kill`, `git` or `python3` — no shell script, none reaching `scripts/` |
| `defmodule` *(positive control)* | `test/` | **124** — the apparatus is live in that scope |
| literal `sprint.sh` *(positive control)* | whole repo excl. `_build`/`deps` | **present in 10+ files**, all `docs/` and `CLAUDE.md` — so the zero above is a real absence, not a broken pattern |

**Verdict: no gate runs.** Not *"the harness is unchanged"* — it changed once, in a file no gate
reads, and that was checked. `mix dialyzer` is not re-run on either arm: gc discharged it clean
and nothing since has touched Elixir.

**AR5 — why the reasoning and not the outcome.** The standing rule that every gate runs at ticket
boundaries exists to catch a gate going red for a reason the change did not cause. Where the tree
provably has not moved in anything a gate reads, re-running is ceremony — and *provably* is the
load-bearing word. **This close is the first time that premise was checked rather than asserted.**
The next close inherits the check, not the conclusion: it must re-derive the diff from its own
predecessor's discharge commit, because the answer depends entirely on what has moved since.

---

## 4. §7's ritual

### 4a. Promotion candidates — enumerated with evidence, no proposals

The population and why it is what it is: no m6 review file is committed, and `m6-github.md`
holds no §Promotion candidates section, so the scan ran over the six implementation-notes files
(`m6-t1`, `m6-t2`, `m6-t2b`, `m6-t2c`, `m6-t3`, `m6-t4`) and the runbook/`milestone.md` sweeps
those tickets performed. §7 step 1 ¶2 is the authority.

**The bar is ≥2 tickets.** Following the precedent m5 and gc both recorded and applied,
instances inside a single ticket, or in reviewer-directed edits within one cycle, are **not**
ticket recurrences however many there are. Each entry below states which it is. **The reviewer
rules; nothing is proposed and nothing is landed.**

| # | candidate | tickets | evidence | bar | repo if promoted |
|---|---|---|---|---|---|
| 1 | **A count in prose about a growing set is de-numeralised, not corrected** — correcting *seven* to *eight* re-arms the same trap for the next member | **t1, t2b, t4** | t1 minted it and ran the sweep that found it (`m6-t1:113-157`, the (a)/(b)/(c) classification, two count-bearing lines the ticket had itself just written, de-numeralised before the edit landed); t2b applied it by name (`m6-t2b:252-256` — *"Correcting five to seven would have re-armed the same trap for provider five"*); t4 fired it on two units the ticket named and found two more of the class beside them (`m6-t4:194-200`) | **MET — 3 tickets** | **agents** — it is a doc-sync/runbook-discipline rule, and its whole population is this repo's prose. Its nearest siblings are §Definition of done — doc sync |
| 2 | **A wiring list's clause can be right while its enumeration is short; repair it as an incomplete enumeration, not as a missing clause** | **t2b, t4** | t2b followed the list and found two places it did not name — `KNOB_CONSTANTS` and *every prose enumeration of the provider set* (`m6-t2b:257-267`); t4 found the same clause four instances short and took it to eight, and added the matrix regen as a place in its own right (`m6-t4:222-244`) | **MET — 2 tickets** | **agents** — the artefact is `cloudcost/runbook.md` §Adding a provider, and the family is doc-sync |
| 3 | **A generated artefact with consumers is itself a wiring place** | **t4** (with t2b as the cost) | `m6-t4:228-231`; `docs/capability-matrix.md` is `File.read!` into the planner's system prompt (`agents/orchestrator.exs:17-18`, `:34`), so a script absent from it is a script the planner cannot plan. BL-090 closed this for provider three without adding the regen to the list, and it was stale again nine days into provider four | **NOT MET — 1 ticket**; the second data point is a prior milestone, not a second m6 ticket | **agents** |
| 4 | **A live run exercises only the arm its data happens to be in; the other arms need a named owner or a stated condition** | **t2c, t3** | t2c enumerated what neither of its live legs had rendered and named t3 as the ticket that inherits it rather than leaving it a gap belonging to nobody (`m6-t2c:364-382`, §7a/§8); t3 discharged the render half by a labelled hand-invoked chain with a control, and **split** the obligation rather than declaring it closed — the live-sprint half *"closes on its own the first time a seat on this account crosses 30 days idle. No ticket owns it and none should"* (`m6-t3:460-465`) | **MET — 2 tickets** | **agents** — it is about what a done-check can and cannot establish over this pipeline; it sits beside the end-to-end/pipeline-integration family |
| 5 | **An LLM-written cell in a generated document is unstable, not stale** | **t4** | `m6-t4:133-152` — three regenerations of one section over an unchanged tree produced three different agent labels, and reworded every script purpose on each run; `docs/capability-matrix-runbook.md:79-80` claimed byte-identical output, true of the assembler and false of the ritual | **NOT MET — 1 ticket**, and **BL-155 owns it** | **agents** |
| 6 | **A report sentence that is true in one state and false in another must say which state it is in** | **t2c, t3** | t2c replaced a completeness claim with three evaluation states and a fourth reading (`m6-t2c:148-169`); t3's live run rendered the third state, byte-identical to the sentence t2c had found false — *"The sentence being byte-identical to the false one is the point, not a regression"* (`m6-t3:390-403`) | **MET as a pair — but both instances are one arc**, t2c authoring and t3 exercising, rather than the same defect recurring independently. The reviewer's call | **agents** |
| 7 | **The U2 discipline held for two packets and lapsed on the third, with nothing detecting it** | **t3** | `m6-t3:536-549` — six live logins paired with per-person Copilot activity timestamps, in the review packet **and in a committed file**. U2's text is unambiguous and was read during the ticket | **NOT MET — 1 ticket.** Recorded rather than promoted on severity; assessed honestly rather than excepted | **agents** if it ever clears the bar — U2 is a cloudcost-side class |
| 8 | **A gate step done out of order, recorded rather than smoothed** | **t4** | `m6-t4:55-60` — `../aetheris/CLAUDE.md` read after W1–W3 had landed, not before the first edit. Nothing in it contradicted the work, so no rework followed, *"but the rule was not followed and the reason it exists is that this is not knowable in advance"* | **NOT MET — 1 ticket**, and the rule it violates is already promoted (agents `CLAUDE.md`, the Repos rule). An instance of an existing rule, not a new one | n/a |

**Three clear the bar (1, 2, 4), one clears it as a pair whose independence is doubtful (6), and
four do not.** No disposition was offered on any of them at r0 — the ticket reserved that ruling.

`[Disposed 2026-08-14 at the close review. **1, 2 and 4 promoted** into agents `CLAUDE.md`, quoted
from the destination in §9. **6 declined** — one arc, t2c authoring and t3 exercising, not two
independent recurrences, so the bar is not reached however the instances are counted; it may
return as a fresh finding. **3 and 5 declined**, single-ticket, BL-155 owning both. **7 declined
on the bar and explicitly not excepted upward on severity**, its mitigation already on BL-150.
**8 declined** as an instance of a rule already in the file. Eight entries, eight dispositions;
the table above is unchanged and this bracket carries the verdicts.]`

### 4b. The prior-claims census — §7 step 4 ¶2, which the prompt omits

The preceding cycle is **gc**. Its close claims four promotions, all into harness `CLAUDE.md`
(`docs/milestones/gc-stale-claims.md:842-845`, `:882`, and commit `fdb1d64` *"four §Learning
promotions — the gate-claim rule, and three carried in from m5"*). The population was derived
from those records, not chosen by eye.

**Run twice, deliberately.** Whitespace-normalised and case-insensitive on both passes, so the
difference between them is wording and nothing else.

| # | claim | exact search on gc's candidate wording | substance search |
|---|---|---|---|
| 1 | the gate-claim rule | `a stale gate claim` → **ABSENT** | `a gate claim is corrected by repointing at what discharged it` → **PRESENT**, harness `CLAUDE.md` |
| 2 | notes are read by the next round in its arc or by nobody | **PRESENT** | **PRESENT** |
| 3 | a negative control is spent once a record quotes it | **ABSENT** | `a negative control is spent by publication` → **PRESENT** |
| 4 | §7's distillation can lose what the candidate got right | **ABSENT** | `does not check the entry against the candidate it came from` → **PRESENT** |

Controls: negative `qqx-census-control-m6close-9174` → **0** in both repos, verified before use;
positive `source:` → **60** harness, **35** agents.

**Result: 4 of 4 present. Nothing absent. No census promotion owed.** All four are harness-side;
none appears in agents `CLAUDE.md`, which is what gc's own record says.

**And the instrument reproduced the defect its own fourth entry describes.** The exact-string
pass reported **3 of 4 ABSENT**; all three were present with drifted headlines. That is gc
§Carried in item 4 — *§7's verification step … does not check the entry against the candidate it
came from, so a distillation that loses or rewords a clause passes* — firing on the very census
run to check it, one cycle after it was promoted for firing on gc's census of m5. **Second
consecutive demonstration on a close's own instrument.** Recorded as a result; not filed, not
promoted, because the rule that predicts it is already in the file.

### 4c. R24 — what arrives here undisposed

`docs/milestones/gc-stale-claims.md:847-860` records **five** promotion candidates, every one
marked **first carry**, and `:932-935` forwards them: *"Five §Promotion candidates, all first
carry. Under R24 each is promoted or dropped at the next close and cannot be carried a third
time. They are the subsection the next round opens."*

**m6's close is that next close.** Each is at **carry count 2**. R24 forbids a third.

| # | entry | gc's recorded bar | carry count here |
|---|---|---|---|
| 1 | a round whose first ticket runs in the session that creates the round document has no reviewable ticket anatomy | one instance (gc t1), ratified as a one-off at gc D3 | **2** |
| 2 | two documents can use one word in incompatible senses and neither is wrong | one instance; ruled at gc D2, owned by **BL-149** | **2** |
| 3 | a five-instance positive control caught a defect suppressing a fifth of the class | one instance (gc t1); gc had no second census to test it against | **2** |
| 4 | a reverse pointer that restates the rule it points at is a second copy of that rule | one instance (gc t2) | **2** |
| 5 | a discrimination required of one ticket is not required of its sibling unless the reviewer writes it twice | two instances, **neither a ticket recurrence** | **2** |

**Reported, not disposed** at r0 — the ticket reserved the verdict for the reviewer, and R24
requires one on each at this close.

`[Disposed 2026-08-14 at the close review: **all five DROPPED.** Each is at carry count 2, none
meets §7's ≥2-ticket bar on gc's own recorded evidence, and R24 forbids a third carry. Dropped on
that evidence rather than on any re-derivation, **recorded once and not re-litigated**, and each
free to return as a fresh finding from fresh evidence — what R24 forbids is the same entry carried
a third time, not the subject being raised again by something new. **One distinction stated
because the two are easy to conflate: dropping a promotion candidacy does not close a row that
owns the same subject.** Entry 2's subject is owned by BL-149, which stays open on its own terms
and is untouched by this drop — a row asks what to do, a candidate asks whether a rule should bind
future work, and answering the second no leaves the first alone.]`

**gc's §Carried in is clear and re-carries nothing.** All four items were disposed at gc t4
(`:838-845`): three promoted, and item 1 — m5's deferred `mix dialyzer` obligation —
**DISCHARGED by running the gate**, `Total errors: 0`, exit 0. Nothing from that section arrives
here undisposed, and the dialyzer obligation is not re-carried. §3b establishes why it is not
re-run.

### 4d. §7's closing test

*The same finding class should not appear as `blocking` in two consecutive milestones.* **No m6
review file is committed**, so no finding in this milestone carries a `blocking` label that this
close can read; the test cannot be run on its own terms, and that is stated rather than answered
green. What can be said from the records that do exist: **no m6 implementation-notes file records
a blocking finding at all** — the reviewer findings they record are amendments, widenings and
corrections, and the two defects that did stop work (t2b's gate item (vi), t2c's live coverage
claim) were found by the tickets themselves, not by a review. **This is itself the observation
worth carrying**: a close whose milestone commits no review files cannot perform §7's own success
test, and the test's absence is invisible from inside the close. Reported here; **no row opened**,
per Do-not-generate, and it is offered to the reviewer as material rather than filed.

`[Carried 2026-08-14 at the close review, by arbiter ruling: **appended to BL-150** as one dated
entry, in this section's own wording. R23's routing applies — it is an observation about how the
documentation system works, not a unit of work — so it appends to the standing row rather than
opening one, and BL-150 does not close on it. **No fix is proposed**, deliberately: whether the
remedy is committing review files, re-keying the test on something the tree keeps, or accepting
that the test binds only cycles that commit them, is the collection question that row exists to
hold rather than answer.]`

---

## 5. What this close wrote

| file | change | round |
|---|---|---|
| `cloudcost/m6-github.md` | §Dispositions, §Close criteria — the per-clause assessment, §Milestone summary, appended last | r0 |
| `cloudcost/docs/m6-t4-implementation-notes.md` | §9 — a dated discharge block appended; the section stands unrewritten | r0 |
| `docs/backlog-2026-06.md` | **BL-156** — one appended instance. No row opened, none closed | r0 |
| `cloudcost/docs/m6-close-implementation-notes.md` | this file | r0 |
| `cloudcost/m6-github.md` | §Ticket set gains **t2b** and **t4**; the register's entry 1 rewritten; §Dispositions gains thirteen dispositions | **r1** |
| `CLAUDE.md` *(agents)* | **`## Learning — m6-cloudcost`** — three promoted entries, §9 | **r1** |
| `docs/backlog-2026-06.md` | **BL-150** — one dated entry, §7's closing test | **r1** |

**No adapter, script, template, manifest, matrix, Rig file or harness file was touched in either
round**, and no executable line changed anywhere — which is why both pytest figures are identical
to t4's across both.

---

## 6. What the close found, and what became of each

1. **The recovered-spend register's first entry.** As first written: the live read returned three
   unfilled organisation seats, the same count attested as removed, and the entry recorded *count
   not established* with both readings of that number left open. **Closed at the review, and
   neither reading was correct** — the operator had reached the confirmation page without
   submitting, then submitted after the read. Entry 1 now records the waste (three seats, 4
   USD/seat/month, **12 USD/month**, from the provider's billing page), the action (19→16,
   confirmed 2026-08-14, **effective 2026-08-20**), why the read shows 19 (two facts, not one),
   and the closing check (a `plan.seats` read on or after 2026-08-20 returning 16 — **no row
   opened**). §2a. **The finding stands and is not softened**: the criterion's first exercise
   found the milestone's own headline recovery unperformed.
2. **§Ticket set named four of the six tickets that shipped.** t2b appeared only in prose
   cross-references, t4 nowhere, though both shipped (`bcb63e6`, `e0c1ee2`) and t4 discharged
   close criterion 3. Reported at r0 and **not fixed**, on the ground that adding a ticket entry
   is a scoping act and the document is the reviewer's. **Authorised and fixed at r1**: at a
   close such an entry records what shipped rather than scoping anything, and a ticket set
   omitting two of its own tickets is wrong on its face. Both written from the tickets' own notes,
   matching the surrounding entries' form, with a dated bracket recording the ruling.
3. **§7's closing test cannot be performed by a milestone that commits no review file** — §4d.
   **Carried to BL-150** at r1 as a dated entry, per R23; no fix proposed.

---

## 7. Doc-sync gate — post-commit

§7 step 5 requires the drift checker and the prompt's done-check omits it. Run **after** the
commit, because check 8 (`project_knowledge`) compares the manifest against committed history: a
pre-commit run reads the pre-edit hash and cannot see the staleness this commit introduces, so it
would be a green over a gap.

**Of this close's four files, exactly one is manifest-tracked**: `docs/backlog-2026-06.md`.
`cloudcost/m6-github.md` and both files under `cloudcost/docs/` are not — checked against
`docs/project-knowledge-manifest.md` before the commit, so the expected WARN set was known in
advance rather than read off the result.

```
$ cd ~/sandbox/elixirws/aetheris-agents && python3 scripts/drift_check.py --strict
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 50 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[WARN] project_knowledge: cloudcost/milestone.md stale — manifest=8f36e45 current=97c61a0
[WARN] project_knowledge: docs/capability-matrix.md stale — manifest=4d98ec2 current=e0c1ee2
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=124707f current=e960db0

[PASS] command_fields: 11 documented §4 structs (56 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  3 WARN  7 INFO                                  exit 0
```

**Nothing is elided.** The output above is the run's own, complete; the only edit is the removal
of ANSI colour codes.

**One citation in it decayed while this file was being written, and it is re-run rather than
patched.** The block above was produced at commit `e960db0`. Filling this section in and amending
the commit moved HEAD to `924b049`, which changes the very hash the third WARN prints — so the
transcript above became a true record of a run against a commit that no longer exists. Per the
standing rule, the fix is to re-run and publish the re-run, never to edit a published figure into
agreement:

```
$ python3 scripts/drift_check.py --strict          # at HEAD 924b049
[WARN] project_knowledge: cloudcost/milestone.md stale — manifest=8f36e45 current=97c61a0
[WARN] project_knowledge: docs/capability-matrix.md stale — manifest=4d98ec2 current=e0c1ee2
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=124707f current=924b049
Summary: 8 PASS  0 FAIL  3 WARN  7 INFO                                  exit 0
```

**Identical but for that one hash**, which is the check reporting the amend correctly. The amend
touched only this file, which is not manifest-tracked, so the WARN *set* could not have moved —
and that was predicted before the re-run rather than read off it.

**And this paragraph lands as a second commit rather than a second amend, deliberately.** Amending
again would move HEAD off `924b049` and falsify the re-run block the same way the first amend
falsified the block above it — a loop with no terminating condition, since every amend invalidates
the transcript recording the previous one. A separate commit leaves `924b049` a real commit, leaves
`docs/backlog-2026-06.md`'s last-touching commit at `924b049` where the WARN prints it, and ends
the regress. **The close is therefore two commits**, and this is the only reason.

> **`[Terminated 2026-08-14 at the close review, by arbiter ruling. The two transcripts above
> stand as published and no further run was made. The paragraph above got the mechanism right and
> the remedy wrong: a separate commit does not end the regress, it only delays it one commit —
> the amendment round landing after this one touches `docs/backlog-2026-06.md` again and moves the
> hash again. What ends it is the invariant, stated once.]`**
>
> **Both transcripts are stamped with the commit they ran at — `e960db0` and `924b049` — and that
> is all a transcript of this check can be.** The third WARN **is** the staleness indicator, and
> its `current=` column is `git log -1 --format=%h -- <file>` — a function of the commit being
> made. So **any commit touching a manifest-tracked file re-stales it by construction**: a run
> before the commit cannot see that commit's staleness, and a run after it is falsified by the
> next commit touching the same file, **including the commit that publishes the run itself**.
> There is no fixed point to converge on, which is why three rounds of re-running produced three
> transcripts and no additional information.
>
> **What the two runs establish, and it is not currency:** the check is green at both commits it
> was taken at — **8 PASS · 0 FAIL · 3 WARN · 7 INFO, exit 0**, twice — and all three WARNs are
> the declared `project_knowledge` strict-mode exemption on both. Zero FAIL and no *unexplained*
> WARN is what `--strict` asserts, and that holds at both. **A later reader wanting currency runs
> it at their own HEAD**; this record is evidence about the export boundary, not a claim about now.

**All three WARNs are `project_knowledge` manifest staleness — the declared strict-mode exemption
— and they are named, not chased.** Two predate this close (`cloudcost/milestone.md` stale since
t3 at `97c61a0`; `docs/capability-matrix.md` since t4 at `e0c1ee2`). **The third is this commit's
own**: `docs/backlog-2026-06.md`, manifest `124707f` against current `e960db0`. Zero FAIL and no
*unexplained* WARN, which is what `--strict` actually asserts.

**And the third WARN is the ordering rule firing, visibly.** A pre-commit run would have compared
the manifest against `e0c1ee2` — the hash this file carried *before* the BL-156 append — and
reported two WARNs, not three, passing green over the staleness the commit was about to
introduce. That is why check 8 runs after the commit and checks 1–7 do not need to.

**The seven INFOs are unchanged and unrelated**: four env vars documented in Rig's specs but read
agent-side, and three payload fields present in DB events and not yet listed in §6. Neither set
was touched by this close.

---

## 8. Open items forwarded

Everything m6 leaves behind, with its owner, is in `m6-github.md` §Milestone summary →
*Open for the next cycle*, each row verified at HEAD before being listed. The verification is a
per-row check against **row bodies**, which BL-145's ruling made the authoritative surface:
155 rows parsed from anchored `^### BL-NNN ` headings, the eight listed rows each carrying **zero**
closure markers, with a positive control on four rows known closed (BL-069, BL-074, BL-131,
BL-132 — 1, 3, 1 and 1 markers respectively). A close that lists a row as open when it is closed
is the defect BL-145 ruled on, and a zero without a control is an observation about the command.

---

## 9. The three promotions, read back out of the destination — §7 step 4 ¶1

`Landed 2026-08-14 at the close review, by arbiter ruling on §4a's enumeration. Candidates 1, 2 and
4. §7 step 4 requires the entry be readable out of the file rather than claimed from the commit, so
each is quoted below from` `CLAUDE.md` `after the edit, with its surrounding lines and its line
number. The commit is not the evidence; the file is.`

**Destination: agents `CLAUDE.md`, a new `## Learning — m6-cloudcost` section at `:519`**, placed
last in the file after `## Learning — BL-007`. All three land agents-side because **destination
follows which family an entry joins, not which file the ticket's `Touches` named** — 1 and 2 join
the doc-sync family whose population is this repo's prose, and 4 joins the family about what a
done-check establishes over this pipeline. That is the correction gc's close owes, recorded on
BL-150 and applied rather than restated.

**The section header and preamble, `:517-524`:**

```
517  ---
518
519  ## Learning — m6-cloudcost (GitHub: provider four, the first consumption-class adapter)
520
521  Findings that recurred across ≥2 tickets in the m6 milestone, promoted per methodology §7 and
522  ruled at the close, 2026-08-14. All three land here rather than harness-side because destination
523  follows **which family an entry joins**, not which file a ticket's `Touches` happened to name —
524  the correction gc's close owes, recorded on BL-150.
```

**Candidate 1 → `:526-527`**, headline and `Source:` (body elided at the ellipsis, which is marked
rather than silent):

```
526  **A count in prose about a growing set is de-numeralised, not corrected — correcting *seven*
     to *eight* re-arms the same trap for the next member.** … **Distinguish three shapes before
     editing**: a *count claim* whose argument the number does not carry (de-numeralise), a *data
     enumeration* such as a table row or a literal set (extend it; it is not a count), and a count
     whose argument genuinely needs the figure (keep it, and say why).
527  `Source: m6-cloudcost t1 (the sweep that minted the rule, and two count-bearing lines the
     ticket had just written, de-numeralised before the edit landed), t2b (*"Correcting five to
     seven would have re-armed the same trap for provider five"*), t4 (fired on both units the
     ticket named and found two more of the class beside them).`
```

**Candidate 2 → `:529-530`:**

```
529  **A wiring list's clause can be right while its enumeration is short — repair it as an
     incomplete enumeration, not as a missing clause.** … **And a generated artefact with consumers
     is a wiring place in its own right**: a document read by a program is not documentation, and
     the one place a list of this kind reliably forgets.
530  `Source: m6-cloudcost t2b (followed the list, found `KNOB_CONSTANTS` and *every prose
     enumeration of the provider set* unnamed), t4 (found the same clause four instances short,
     took it to eight, and added the capability-matrix regeneration as a place — … BL-090 closed
     exactly this for provider three without adding the regen to the list, and it was stale again
     nine days into provider four).`
```

**Candidate 4 → `:532-533`:**

```
532  **A live run exercises only the arm its data happens to be in; every other arm needs a named
     owner or a stated closing condition — never silence.** … **And a hand-invoked demonstration
     discharges the render half only**: run it with a control at the real inputs reproducing the
     live result, label it as not-a-sprint, and split the obligation rather than declaring it
     closed.
533  `Source: m6-cloudcost t2c (enumerated what neither of its live legs rendered and named t3 as
     the inheriting ticket rather than leaving a gap belonging to nobody), t3 (discharged the
     render half by a labelled hand-invoked chain whose control at the real date reproduced the
     sprint's zero exactly, and split the rest: *"That closes on its own the first time a seat on
     this account crosses 30 days idle. No ticket owns it and none should."*).`
```

**Each is compared against the candidate it came from, not only against the file** — the
distillation check gc promoted at its own close, applied here to its first successors. All three
headlines are wider than §4a's one-line statements and none loses a clause: candidate 1's entry
adds the three-shapes discrimination that t1's sweep produced and §4a compressed away; candidate
2's adds the generated-artefact clause, **which is candidate 3's subject folded in as a clause
rather than promoted as an entry** — recorded here because that is a substantive choice and not a
wording one; candidate 4's adds the hand-invoked-demonstration clause that t3's control produced.
**Nothing in the promoted wording is absent from the candidate's evidence**, which is the direction
the check runs.

**The five declines, each recorded once with its ground**, in `m6-github.md` §Dispositions:
**3** and **5** single-ticket, BL-155 owning both; **6** two instances but **one arc** — t2c
authoring and t3 exercising — so the bar is not reached however they are counted, and it may
return as a fresh finding; **7** single-ticket, **declined on the bar and explicitly not excepted
upward on severity**, its mitigation already on BL-150; **8** an instance of a rule already in the
file. Eight entries, eight dispositions.

**And gc's five carried candidates are dropped, all of them**, at carry count 2 under R24 — none
meeting §7's bar on gc's own recorded evidence, recorded once and not re-litigated, each free to
return as a fresh finding from fresh evidence. **One distinction stated in the section itself
because the two are easy to conflate: dropping a promotion candidacy does not close a row that
owns the same subject.** Entry 2's subject is owned by **BL-149**, which stays open on its own
terms. Thirteen entries, thirteen dispositions.

---

