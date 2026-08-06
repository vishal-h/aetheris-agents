# t1b — implementation notes

**One extraction mechanism for `--json` output; the chaos gate starts evaluating.**
Rows: BL-100 (closed), BL-107 (closed), BL-110 (filed). Cycle: `cloudcost/m4-consolidation.md`.

**HEADs at open:** agents `c5b63ae23c985bcdb9f4c9c592dc8756a58a6e74`,
harness `f6fbd822db9281cea30fbf8e2450e330d95017df`. Both trees clean, both level with origin.

---

## 1. Step-1 gate

| Gate | Result |
|---|---|
| **G0** fresh session, not in plan mode | pass |
| **G1** both repos clean; origin relationship in the applicable form | pass — `status --porcelain` empty in both; `## main...origin/main` with no `[ahead N]`/`[behind N]`, i.e. **level with origin, before implementation** (carry 4's pre-implementation form) |
| **G2** census resolves; every asserting site assigned or excluded with reason | pass — §2 |
| **G3** multiple-payload question settled | pass — §3, settled **both ways** |
| **G4** all commands cwd-independent | pass — `git -C` / absolute paths throughout |
| **G5** cloudcost shared scripts byte-still by blob hash | pass, with a discrepancy recorded — §7 |

**G5 discrepancy, recorded rather than reconciled.** The ticket and `m4-consolidation.md` §Scope
both say "the four shared scripts" under `cloudcost/scripts/`. **Eight exist.** All eight were
pinned by blob hash, which is a superset of whatever four was intended. Nothing in this ticket
touches any of them; §7 shows them unchanged at close.

---

## 2. The census

**Method.** Derived fresh; no prior list inherited. Searched the claim's *substance* — every read
of a harness `--json` document, by any mechanism — not a token, per the method t1a ratified after
four rounds of a token-keyed search missing sites.

**Terms run.**

| # | Term / expression | Purpose |
|---|---|---|
| T1 | `jq` | the named mechanism |
| T2 | `--json` | every harness invocation whose stdout is a JSON document |
| T3 | `tail -1` / `head -1` | the positional workaround |
| T4 | `grep -o '"` | the string-matching workaround |
| T5 | `python3 -c "import json` / `import json,sys` | the Python-parse workaround |
| T6 | `no-json` / `no_json`, both repos, `*.md *.sh *.py *.ex *.rs` | assert-vs-retract classification |
| T7 | `runbook*.md` (both repos) × `orb_id=n/a\|no-json\|Run ID: n/a\|step count\|mixes stderr\|log noise\|jq` | the runbook obligation |

**Breadth, recorded as a negative result.** `grep -rln 'aetheris --json'` over
`../aetheris/scripts/`, `../aetheris/.github/` and all of `aetheris-agents` (`*.sh`, `*.py`,
`*.exs`) returns **`scripts/sprint.sh` only**. No other script in either repo consumes harness
`--json`. (Rig's Rust consumer is out of scope by the ticket's Do-not-generate list.)

### Asserting — 29 reads, all assigned to the helper

> **Corrected at review round 1.** The first version of this table listed **10** Group A sites and
> a total of **19**, both wrong. Three Group A sites — `:686` (payslip), `:754` (drive), `:826`
> (email) — were **converted and verified but omitted from the census table**; they appear in the
> done-check's SITE CLASS 2 throughout. The "19 distinct sites" figure was worse than a
> miscount: it was derived by "pairing" `:69`/`:70` and `:79`/`:81`, which is not a real
> operation — `:69` and `:70` are two separate reads, and `:81` is in Group D, so pairing it
> against a Group A line cannot reduce a Group A+B+C total. **No site's treatment changed**; the
> defect was in the record. It matters because carry 2 exists precisely because censuses in this
> territory are compared against each other, and this one is the baseline for the next.

Line numbers are pre-edit, at harness `f6fbd82`.

**Derivation of the total, not an assertion of it.** The count is read off the two artifacts that
can contradict each other, and they agree:

```
# every read of a --json document, pre-edit
git -C /home/it/sandbox/elixirws/aetheris show HEAD~1:scripts/sprint.sh \
  | grep -nE "jq -r '\.|jq '\[|tail -1 \"|grep -o '\"run_id|--json (inspect|trajectory)"
# → 13 (A) + 5 (B) + 7 (C) + 4 (D) = 29, plus :1113/:1197 which are excluded (trajectory --export)

# every conversion, post-edit — the call sites of the helper
grep -nE '(^|[^_a-z])json_read(_cmd)? ' scripts/sprint.sh   # minus :120, json_read_cmd's own body
# → 29 call sites
```

**29 reads censused, 29 converted.** The two numbers are derived independently and match; a
mismatch either way would mean a site converted without being censused, or censused without being
converted.

**Group A — `jq` over a `--json` output file (13).**

| Line | Read | Kind |
|---|---|---|
| `:53` | `.status`, `run_agent()` | display |
| `:69` | `.orb_id`, `run_orb()` | display |
| `:70` | `.status`, `run_orb()` | display |
| `:79` | `.run_id`, `extract_step_count()` | feeds a read |
| `:248` | `.run_id`, uc_auto | feeds a branch |
| **`:297`** | **`.status`, chaos maxsteps** | **gate** |
| `:463` | `.run_id`, news day 1 | feeds a branch |
| `:563` | `.run_id`, news day 3 | feeds a branch |
| `:605` | `.run_id`, `schedule_trigger.txt` | feeds a branch |
| `:686` | `.run_id`, payslip | feeds a branch |
| `:754` | `.run_id`, drive | feeds a branch |
| `:826` | `.run_id`, email | feeds a branch |
| `:2573` | `.status`, cloudcost inline `ok` line | display |

**Group B — `tail -1 | jq` (5).** Works today on single-payload files; wrong on the three captures
carrying worker output after the payload. `:1000`, `:1020`, `:1034`, `:1105`, `:1189` — each
`.agent_run_ids[] | select(endswith("-…"))`.

**Group C — `grep -o '"run_id":"[^"]*"' | tail -1 | cut` (7).** Works today. Folded in per the
one-mechanism invariant — two mechanisms for one job is how the class regenerates (decision 14).
`:1738`, `:1866`, `:1941`, `:2063`, `:2182`, `:2320` (six docbuilder cases), `:2687` (cloudcost).

**Group D — `jq` over a `--json` *pipe* (4).** In class by decision 14: Logger contaminates a pipe
exactly as it does a file. Confirmed live — `mix aetheris --json inspect <id>` emits resume
warnings on stdout ahead of the payload, so the bare `| jq` fails identically. `:81`, `:1022`,
`:1036` (`--json inspect` → `.step_count`), `:615-616` (`--json trajectory` → `.event_types`).

**Total: 13 + 5 + 7 + 4 = 29 reads.** Some occupy two source lines pre-edit (the Group B
`tail -1 … \ | jq …` continuations, and Group D's `:615-616`, `:1022-1023`, `:1036-1037`), so a
line count is larger than a read count and is not the figure quoted anywhere here.

### The inverse census — completeness, checked from the other end

Added at review round 2. Both counts above enumerate **reads by known mechanism**, which is the
same shape as the search that missed three sites at round 0. That miss was a transcription error
rather than a search error, but the shape makes the question fair: *could a read exist by a
mechanism nobody enumerated?* Starting from the **invocations** rather than the reads is what
answers it.

**Method.** List every `--json` invocation in `sprint.sh`; for each, resolve its output sink and
enumerate every subsequent mention of that sink in the file. A read by an unenumerated mechanism
would appear as a mention that is neither a helper call nor a declared exclusion.

**11 invocations**, resolving to **36 distinct sinks** (30 path expressions passed to
`run_agent`/`run_orb`, plus `maxsteps.json`, `badpath.json`, `concurrent_${i}.json`,
`schedule_trigger.txt`, cloudcost's `run.json`, and the three `--json inspect`/`trajectory` pipes).
Every one resolves:

| Disposition | Count | Notes |
|---|---|---|
| Read directly through the helper | 12 sinks | the `.run_id`/`.orb_id`/`agent_run_ids` sites |
| Read through the helper **indirectly** | 4 sinks | uc1 `:232`, uc2 `:253`, uc3 `:294`, uc_auto `:356` bind the path to `$f`, then `extract_step_count "$f"` — which is Group A `:79` + Group D `:81` |
| Read via `json_read_cmd` at the invocation | 3 pipes | `--json inspect` ×2, `--json trajectory` |
| Payload reaching only `run_agent`/`run_orb`'s own `status`/`orb_id` lines | 16 sinks | capability_matrix ×9, the two docbuilder `builder.json`, `news/day2.json`, `uc4/orb_run_${i}.json`, uc_api t1 / t2-steady / t2-greenfield orbs. **Each has exactly one mention in the file — the call that writes it.** Their payloads still pass through the helper, at `:141`/`:157`-`:158`; they simply have no additional per-case read |
| Declared exclusions, unchanged | 2 | `chaos/badpath.json` and `chaos/concurrent_${i}.json` are written and named in an `ok` line for a human to open — never parsed. The cloudcost D2 credential grep (`:2762-2763`) reads `run.json` by design |

**Negative result, recorded as a result: no read by an unenumerated mechanism exists.** The inverse
enumeration returns nothing the forward census missed, which is the confirmation the forward census
alone could not give.

**One clarification it did surface**, not an error but worth stating: `extract_step_count`'s two
reads are counted **once each** (`:79`, `:81`) because they live in the function, not at its call
sites. The function is called from four cases, so the *coverage* of those two reads is wider than
the count suggests.

### Excluded — 13 sites, each with a reason

| Site(s) | Reason |
|---|---|
| `:1113`, `:1197` | `jq` over a trajectory file produced by `mix aetheris trajectory --export` — a clean file export, not a `--json` stdout capture. No contamination path. |
| `:1400`, `:1410`, `:1462`, `:1472`, `:1552` | `grep -o` over **curl HTTP response bodies** from the playground API server. Not harness CLI stdout. |
| `:1080`, `:1170` | Python-parse of `notify_at1qry.py` stdout — a use-case script, not the harness. |
| `:1596`, `:1632`, `:1640`, `:1660` | eduloka: Python-parse of a use-case script's merged stdout+stderr. Same shape, different root cause — **BL-108**, out of scope by decision 16. |
| `:830` | `grep -q "Sent:"` over `run.json` — a content grep over agent prose, not a payload-field read. |
| `:2674-2675` | The D2 credential grep. Do-not-generate. |
| `:206`, `:1728` | `head -1` over `ls` output. Not JSON. |

### Assert vs retract — carry 2

t1a seeded this territory with retractions that quote the claim they retract, so a term-match
census returns corrections as carriers. Every `no-json` hit outside `sprint.sh` was classified:

- **Retracting** (quote the claim to refute it) — `docs/backlog-2026-06.md` BL-100's correction
  block and BL-107's body; `cloudcost/docs/t1a-implementation-notes.md`;
  `cloudcost/m4-consolidation.md:123`; `../aetheris/docs/aetheris/claude-notes.md:214`; the two
  dated superseded notes in `../aetheris/docs/aetheris/runbook-m10b.md` (`:95`, `:241`).
- **Dated records, left intact** per t1a's ruling — `docbuilder/docs/reviews/*`, `docs/reviews/*`,
  `cloudcost/docs/m2-t3-…`, `m3-t3-…`, `cloudcost/m3-milestone.md:600`,
  `docs/handoffs/handoff-m3-close-…`, `../aetheris/docs/aetheris/milestones/*`.
- **Neither** — the two docbuilder open-items (carry 5). They characterise the label as cosmetic
  rather than asserting or retracting a cause. Treated in §6.

**No asserting site was left standing anywhere in either repo.** t1a corrected all seven; t1b
corrected the two whose *content* the fix falsified (`claude-notes.md`, twice) and appended to the
two runbook notes.

### The runbook obligation — T7, with the negative recorded

Re-confirmed across **all** use cases via `find . ../aetheris -name 'runbook*.md'`:

- **`../aetheris/docs/aetheris/runbook-m10b.md` is the only runbook describing these lines** — two
  sections (`:106` "Parse the actual result", `:241` "Sprint output shows `orb_id=n/a
  status=no-json`"), both prescribing the `grep -v '^\[sandbox\]'` workaround the fix retires.
  Treatment: **appended to t1a's existing dated notes**, not rewritten. It is milestone-named and
  a current equivalent exists (`runbook.md`), so it is a closed record by decision 10 → note, not
  in-place rewrite (decisions 7/9). The manual workaround is left below each note as the record.
- **Negative result for every other runbook** — `api/runbook.md`, `cloudcost/runbook.md`,
  `docbuilder/runbook.md`, `eduloka/runbook.md`, `boxy-pipeline/docs/runbook.md`,
  `docs/rig/runbook.md`, and the harness's `runbook.md`, `-m09-sandbox`, `-m11`, `-m12`,
  `-model-comparison`, `-m10-autonomous-agent-tooling`. Their `jq`/step-count hits are user-facing
  `mix aetheris` recipes, not descriptions of the sprint's reads. **No edit owed.**

---

## 3. G3 — the multiple-payload question, settled

Carry 3, and the whole mechanism rests on it: if one invocation can emit more than one parsing
JSON object, "the last that parses" may take the wrong one.

**Answer: yes, but for exactly one command — `fork` — and recency is still correct.**

*From source, at harness `f6fbd82`.* `Formatter.print/2` is called **once** per CLI invocation
(`lib/aetheris/cli/main.ex:46`) and is one of only two `IO.puts(Jason.encode!(…))` sites in `lib/`.
The other is `Fork.emit_fork_started/2` (`lib/aetheris/cli/commands/fork.ex:71`), whose own comment
states the consequence: *"Fork is consequently the only command that writes to stdout before
dispatch returns. Any consumer scanning for a single result line must account for two."* The early
document is written **first** and the result **last** — so the last that parses is the result
document, which is what a consumer wants. `sprint.sh` never invokes the `fork` subcommand.

*From the captured record.* A sweep of all **319** files under `../aetheris/sprint/` (`*.json` and
`*.txt`), counting lines parsing as JSON **objects**: **0** with more than one, 219 with exactly
one, **100 with none**. This widens claude-notes' prior "50 `run.json` captures, zero" and returns
the same answer.

Both halves are recorded deliberately. Either alone would be a claim reaching past what its author
checked — the defect this cycle keeps finding, and the reason §Open for the close asks whether the
step-1 gate should become standing.

---

## 4. The mechanism

`json_read <file> <jq-filter> [absent]` in `../aetheris/scripts/sprint.sh`, beside `run_agent`.
Scans the file's lines in reverse; takes the first that parses as a JSON object; applies the
filter. Correct whether contamination lands before or after the payload, on either stream, and
whatever the store contains. `tail -1` is not sufficient — three captures carry worker output
after the payload.

**Design decisions, and why.**

- **One function, not two.** A filter argument covers `.status`, `.run_id`, `.orb_id`,
  `.step_count` and the Group B `.agent_run_ids[] | select(…)` projections with the same
  extraction. A `json_payload` + `json_field` split would leave two entry points for one job.
- **Python for the scan**, matching the reference implementation in claude-notes; `python3` is
  already used throughout `sprint.sh` and is exec-allowlisted. A `try/except OSError` guard makes a
  missing file yield the absent value rather than a traceback — the `schedule_trigger.txt` site can
  be handed a file that was never written.
- **`json_read_cmd <filter> <absent> <cmd…>`** for the four Group D pipe sites: captures the
  command's stdout to a `mktemp` file so the same scan applies, then removes it. No new sprint
  output state. **The path is `mktemp`-derived, never fixed** — two of these run for different run
  ids inside the t3 case, and a fixed path would collide. **Cleanup is unconditional**, hardened at
  review r1: the result is captured into a variable with `|| true` so a non-zero return cannot skip
  the `rm` under `set -euo pipefail`, and a failed `mktemp` yields the absent value rather than
  writing to a stray path. Verified with a successful command, a failing command (`false`) and a
  non-existent one — `/tmp` entry count unchanged across all three, values `9` / `n/a` / `n/a`.
- **The absent token is caller-supplied, and it must be.** Sites feeding `[[ -n "$RUN_ID" ]]` take
  **empty** on absence; a token there would push a garbage id into `mix aetheris inspect` and turn
  a skipped branch into a wrong one. Display and gate sites pass `no-payload`.
- **`no-payload`, not `no-json`.** It names *the read* — no line parsed — rather than the run. It
  cannot be confused with a run status now (`handle_run_status/5`,
  `../aetheris/lib/aetheris/cli/commands/run_helpers.ex:112-130`, admits only `done`) nor later if
  BL-106's failure-document row lands, which would add `failed`/`cancelled`/`error`. `no-json`
  named a mechanism — `jq` failed — that no longer describes what happens.

**Not changed, deliberately:** stream topology (every redirect byte-identical), the D2 credential
grep, `CC_HERMETIC`, the poison-control arms, the orphan-count assertion, `fail()`'s effect on exit
status, any `lib/` or `src-tauri/` code, the eduloka site, and any output line's field set.

### 4.1 Deviations from the declared Touches — two, declared

The Touches list names `sprint.sh`, the two docbuilder documents, the backlog, *"any runbook
section describing these lines"*, and `cloudcost/docs/`. Two files were edited outside it. Both are
recorded here rather than disclosed in passing, so the calls are auditable.

**(a) `../aetheris/docs/aetheris/claude-notes.md`** — live guidance, not a runbook, so outside the
list. Two of its paragraphs were falsified by the fix, and both were standing guidance a reader
would act on:

1. §"One case it does not resolve" said the multiple-payload question was unverified and that
   *"anything that ports this scan into an assertion (rather than a human read) owes that question
   an answer first."* This ticket **is** that port, and G3 is that answer. Leaving the paragraph
   would have left the repo's own guidance saying the thing t1b had just done was not yet
   permissible.
2. §"Sprint script `no-json` display" told the reader these reads do not parse and to read the
   payload by hand. That is now false at every site.

Leaving either standing is the defect class t1a closed — a document asserting a cause the repo has
since refuted — so correcting them in place (decision 8: live operational guidance is corrected in
place) was judged to be within the ticket's intent even though outside its letter.

**(b) `../aetheris/docs/aetheris/milestones/handoff-m09-m10.md.md:145`** — a dated record, so it
takes a **note, not a rewrite** (decision 7). Found while verifying this ticket's own Group D
conversion, and edited under the standing rule that *a correction chases the corrected claim into
every doc that adopted it, in the same round*. It is the only document carrying the claim.

The claim: step counts show `n/a` *"because the script reads step count from `--json` run output
but it's not in that payload. Fix: read from `mix aetheris inspect <run_id>`."* **It is wrong, and
unusually for this cycle the ordering is recoverable rather than same-day-ambiguous:**
`extract_step_count` already read from `mix aetheris inspect` at `fafa17f` (2026-05-16 12:40
+0530); the claim text was written at `2a5dc59` (2026-05-17 09:58 +0530), **21 hours later**. It
prescribed a fix already in place, so it was wrong when written rather than superseded since.

The real cause is BL-100's: both of the function's reads were contaminated — `.run_id` from the
merged run file, and `.step_count` from a `--json inspect` **pipe**, which carries Logger output
exactly as a file does. Group A `:79` and Group D `:81` fix both. Verified live:
`extract_step_count → 2 steps` against the post-edit chaos capture, whose run had `max_steps: 2`.

This closes a §Not established item in `cloudcost/m4-consolidation.md` — *"whether the step-count
diagnosis in an m09→m10 handoff is correct"* — which is why the finding is recorded there too.

### 4.2 How each absent-value is consumed — no site treats a default as a value

Checked rather than assumed, because `json_read` makes a previously-dead branch reachable: with
the old `jq … || echo`, a `jq` failure fired the `||` arm outright, so `.status // "unknown"`
**never evaluated its default**. Now a payload that parses but lacks the field yields `unknown` —
a third state between a real value and `no-payload`.

| Default | Sites | Consumed as |
|---|---|---|
| `unknown` (`.status`) | `:53`, `:70`, `:2573` | interpolated into an `ok` line — display only |
| `unknown` (`.status`) | **`:297`, the gate** | operand of `[[ "$status" == "done" ]]` → fails → `warn`. Treated as absence, correctly |
| `no-payload` (`.status`) | same four | same as above |
| empty (`.run_id`) | 13 sites | every one guarded by `[[ -n "$RUN_ID" ]]` |
| empty (`.orb_id`) | `:69` | `${orb_id:-n/a}` — display only |
| `n/a` (`.step_count`) | `:81`, `:1022`, `:1036` | `info` lines only (`:1104`, `:1118`, `:1120`); never compared |
| empty (`.event_types`) | `:615` | `echo "$EVENTS" \| grep -q "context_summarised"` → fails on empty → `warn` |

**No site treats any default as a value**, and the gate's new `unknown` state fails its comparison
exactly as `no-payload` does.

---

## 5. Done-check

### 5.1 Per-site, correct value on clean **and** noisy

Behaviour-neutrality as carry 1 redefines it: a site's *current* output depends on ambient
run-store state, so "reproduce it exactly" is undefined. The check is the correct value on both
shapes, per converted site, against the capture history.

The check binds to the **real** `json_read`/`json_read_cmd` by extracting them from `sprint.sh` at
run time — a re-typed copy would verify the copy. Expected values are **pinned literals** obtained
independently of `json_read` (`grep -o '"run_id":"[^"]*"' | cut`, and reading payload lines
directly); deriving them with `json_read` would let the check satisfy itself.

**23 checks, 23 pass, 0 fail**, over six site classes × four capture shapes:

| Shape | Capture |
|---|---|
| clean, single line | `sprint/20260521_075730/news/day1.json` |
| noise **before** the payload | `sprint/20260805_134754/cloudcost/run.json` |
| worker output **after** the payload | `sprint/20260522_090058/payslip/run.json` |
| **no payload at all** | `sprint/20260521_191506/payslip/run.json` |

No single-line orb capture exists in `sprint/` — every orb capture is noisy — so the clean
counterpart for the `.orb_id` and `.agent_run_ids` classes is that same capture's own payload line,
isolated. Stated rather than passed over: it is constructed, not found.

Group B and C sites (the workarounds that work today) are included, as the ticket requires.

### 5.2 Mutation postures — against states that occur in the captured record

Construct, observe, restore, record. Each posture drives the **real** chaos-gate expression.

| Posture | Constructed from | Gate before | Gate after | Restored |
|---|---|---|---|---|
| **non-JSON after the payload** | the exact worker line from `20260522_090058/payslip` appended to the live chaos capture | `OK` | `OK` (unchanged — correct) | `OK` |
| **no parseable payload at all** | payload removed, the real `Error: run … failed` line from `20260521_191506/payslip` appended | `OK` | `WARN status=no-payload` | `OK` |
| **anti-vacuity: can the gate still fail?** | payload's `status` flipped `done` → `failed` | `OK` | `WARN status=failed` | `OK` |

The first posture also records the contrast that motivates the whole mechanism: on that same
mutated file, the **old** `tail -1 | jq` yields `no-json`, where `json_read` yields `done`.

The third posture is the anti-vacuity one. A gate that cannot report red is not a gate, and this
gate has never in its life reported anything but the fallback — so proving it *can* now go red
matters more than the green run.

**The multiple-payload posture is not constructed, and is recorded as settled rather than
skipped.** §3 establishes no site in the census can reach that state; constructing it would test a
shape the mechanism is never handed.

### 5.3 Live sprint runs

Three, full output captured, run from `/home/it/sandbox/elixirws/aetheris`.

**Chaos — the gate, before and after.** The before-run is **the first chaos output ever captured in
this repo** (`find ../aetheris/sprint -path '*chaos*'` previously returned nothing).

```
BEFORE  sprint/20260806_172144   [WARN]  Chaos 1: status=no-json (investigate)
AFTER   sprint/20260806_172825   [OK]    Chaos 1: agent exhausted max_steps → :done (expected)
```

Its capture (9 lines) carries two `failed to resume run` warnings, an orphan-sweep line and two
`[sandbox]` lines ahead of an intact payload — the noisy-store shape BL-107's premise assumed,
now confirmed rather than presumed.

**Cloudcost, DO leg, with credentials.** `CLOUDCOST_DO_TOKEN` set; AWS and Linode unset, so
digitalocean is the leg with credentials available.

```
[OK]    uc-cloudcost orchestrator → done (707 bytes)
[OK]    report: digitalocean/cloudcost_report_2026-08.html (14K), period 2026-08
[OK]    report_data.providers = [digitalocean] — the selected provider, and only it
[FAIL]  orphan candidates: 0 (expected ≥1 — BL-069 armed: …)
[INFO]  Run ID: cloudcost-orch-digitalocean-PL5Vug
```

The first line has read `no-json` on **every cloudcost run ever recorded** (0 of 10 captures
parsed). The `Run ID:` line is a Group C conversion. Both D2 hermetic arms and both poison controls
ran and passed, unchanged.

**Payslip, through the shared `run_agent` helper** — chosen because payslip parsed in **0 of 8**
prior captures.

```
[OK]    uc-payslip orchestrator → done (687 bytes)
[INFO]  Orchestrator run_id: payslip-orch-TLpSbA
[FAIL]  BTL_999 output directory not found: ../aetheris-agents/payslip/output/BTL_999
```

### 5.4 Red gates — named with their ticket refs, not re-triaged, left red

Per the tracked-carry clause. Neither was relaxed, re-pointed or downgraded.

- **BL-069** — `[FAIL] orphan candidates: 0 (expected ≥1)`. Deliberately armed, tracked, **t2 owns
  it** (decision 12 retires the plant practice in favour of a rule-legibility assertion). Named,
  not re-triaged.
- **BL-110** — `[FAIL] BTL_999 output directory not found`. **Found by t1b, filed by t1b, the same
  day.** Pre-existing and *not* lit by this change: the assertion block is byte-identical at
  `f6fbd82` and is not gated on `RUN_ID`, verified by diffing the block against `git show HEAD:`.
  The orchestrator reads `data/payroll.csv` (`payslip_orchestrator.exs:23`) while `BTL/999` exists
  only in `data/sample_payroll.csv`; `payroll.csv` is gitignored and the sprint copies the sample
  in *only if it is absent*, so the verdict is decided by ambient state — the same defect class
  BL-100 just closed.

`fail()` only prints (BL-077), so neither changes an exit status. That is precisely why both were
invisible until a gate was run off-territory.

### 5.5 The consequence this ticket priced, and what it actually cost

Six `.run_id` sites previously yielded empty whenever the read failed, and their callers are
guarded by `[[ -n "$RUN_ID" ]]` — so those branches had been **silently skipped** on every run
where the read failed. Making the reads deterministic makes them execute. That is the chaos gate's
situation repeated across the sprint, and it was expected.

Observed cost: the newly-executing branches are `info` lines (`Orchestrator run_id:`, `Run ID:`,
`Agent tree`) and step-count reads. **No assertion changed verdict because of it.** BL-110 is *not*
an instance — its block is ungated, verified above.

---

## 6. Carry 5 — the two docbuilder notes

Both paths and their byte-identical text verified at HEAD before writing:
`docbuilder/milestone.md:88` and `docbuilder/docs/m1-milestone.md:680` —
*"Sprint case `run_id` extraction now fixed but the underlying `no-json` label in sprint output is
cosmetic noise — trace to the log line prefix in run.json format"*.

Neither carries the `2>&1` claim, which is why t1a's census did not correct them, and why an
earlier draft asserting they did would have written a false correction into a ticket about a false
claim. The note added to each states both required things, and a third the text also gets wrong:

1. **The "cosmetic" characterisation is false for the class** — one affected site (`:297`) is a
   gate whose operand was the fallback token, so it had never evaluated its subject.
2. **The open TODO is discharged by the fix, not by a document edit** — cited to t1b.
3. The stated *cause* ("the log line prefix in run.json format") is also wrong: Logger output
   shares stdout with the payload, so the payload had to be found, not un-prefixed.

t1a deferred this rather than writing "discharged" in the same commit as the thing that would make
it true. The fix has now landed, so the note is written against a true statement.

---

## 7. G5 close — cloudcost shared scripts unchanged

`git -C /home/it/sandbox/elixirws/aetheris-agents ls-tree HEAD cloudcost/scripts/`, at open and at
close. Eight files, all byte-identical:

```
f6589c6870ad7d66161d6f5ffe954c081362599d  _normalized.py
ee6027707a95f5d4046ef1ffac34eb9dab72efd1  compose_report_data.py
c756e414bb68e3c73d61bb469aea231f56de7768  detect_optimization_signals.py
fe8622f80d5a0b8adc8c3e3c86bdba539cf28106  detect_orphans.py
4c4db7393e20cb011f5e67f0435ad50fa273fbcf  fetch_aws.py
5a3ba664cb099f920f6f314babd33fdd8d7abd19  fetch_do.py
e4693617f8b7da3b9d73a3aede601106dca61d2c  fetch_linode.py
d14d8e3132aca3178509a1b68c37463c8d2a4601  render_report.py
```

---

## 8. Forwarded

- **BL-110** is filed, not fixed. It needs a decision (key the check to an id read from the CSV the
  orchestrator was given, or run the leg against `sample_payroll.csv` explicitly) — not a deletion.
- **Whether the chaos gate would parse in a clean-store environment** is still open. t1b produced
  the first chaos capture, but in a noisy store; `m4-consolidation.md` §Not established keeps the
  clean-store half.
- **`[sandbox]` line stream routing** remains unestablished and is untouched here. The chaos run
  *does* spawn a worker, so the command that would settle it now exists — but establishing it was
  not in scope and no claim is made.
