# m4 t2 — implementation notes

**Ticket:** retire the planted-orphan practice; assert that the live inventory was legible.
**Rows:** BL-069 (closed by retirement), BL-074 and BL-044 (appended).
**Date:** 2026-08-06.
**HEAD at open:** aetheris-agents `914adde`, aetheris `871a720`. Both trees clean, both level
with `origin/main`.

> **Filename deviation, declared.** These notes are `m4-t2-implementation-notes.md`, not
> `t2-implementation-notes.md`, because `cloudcost/docs/t2-implementation-notes.md` already exists
> from m1 (2026-07-29) and would have been clobbered. This matches the `m2-t1-` / `m3-t1-` series
> convention and breaks with t1a/t1b's unprefixed names, which had no collision. Decision 4 —
> ticket names are historical and are not tidied — is unaffected: the *ticket* is still `t2`.

---

## 1. Step-1 gate

| Gate | Result |
|---|---|
| **G0** fresh session; not in plan mode | Fresh session. The session opened in harness-imposed **plan mode**, which forbids writes; the gate was run and reported there, and implementation began only after exiting it. Stated rather than absorbed silently. |
| **G1** both repos clean; origin relationship | Clean, **level with origin** at open (the pre-implementation form). |
| **G2** assertion constructible without editing `cloudcost/scripts/` | Yes. Prototyped read-only against four real artifacts before any edit. |
| **G3** third arm's precondition | Established in its *"say what would"* branch — see §3. |
| **G4** every census site resolves to a ratified treatment | Yes — decisions 7, 8 and 10 reach every site. Two judgment calls were put to the arbiter (§4). |
| **G5** commands cwd-independent | `git -C <abs>`, absolute paths, or an explicit subshell `cd`. |

---

## 2. What changed

### The retired assertion

`../aetheris/scripts/sprint.sh` no longer asserts `orphan candidates ≥ 1`. The assertion and its
KNOWN-RED comment block are removed; a comment stands in their place recording why, and warning
the next reader off reinstating a count-based orphan check:

> *"Do not reinstate a count-based orphan assertion here — an account with no waste is the desired
> state, and an assertion that fails on it can only be satisfied by spending money."*

### The replacement — rule legibility, three arms

Sited **outside** the `CLOUDCOST_PERIOD` guard. This is a change from the retired assertion, not
an inheritance: the old check sat inside the guard, so an empty period skipped it with a warning
and it emitted no line at all. The replacement asserts something about the adapter's output rather
than about the report, so it has no reason to depend on the report's existence. The precedent is
the D2 credential grep, placed outside the same guard for the same reason; the guard's own comment
was extended to name both.

**Placement verified, not assumed.** The provider output directory is emptied before the run
(`find "$CLOUDCOST_OUT" -mindepth 1 -delete`), so a run leaves exactly one `*_inventory_*.json`
and one `*_orphan_candidates_*.json` — both findable by pattern, neither needing the period.

| Input | Source |
|---|---|
| emitted `type` values | the one `*_inventory_*.json` — the adapter's output |
| `skipped`, `totals.resources` | the one `*_orphan_candidates_*.json` — the catalog's own verdict |
| canonical vocabulary | `from _normalized import CANONICAL_TYPES` — **imported**, never restated in shell |

Reading **both** artifacts is what makes this *the inventory reached the catalog* rather than
*the inventory would have been readable*. It also means the two failure modes land in different
places by construction: an entry the catalog could not read appears in its `skipped` set, while an
out-of-vocabulary `type` does **not** — `usable_resources()` checks that `type` is present, never
that it is canonical — so the type check has to be done against the inventory. That gap is
forwarded to BL-074.

| Arm | Condition | Output |
|---|---|---|
| legible | resources evaluated, every emitted `type` canonical, nothing skipped, catalog count agrees with the inventory | `[OK]` |
| illegible | a `type` outside the closed set, a non-empty skip set, or a count disagreement | `[FAIL]` |
| not applicable | zero resources | `[WARN]`, stated as an unknown — never a pass |
| vacuity guard | either artifact missing, or not exactly one | `[FAIL]` |

The not-applicable arm is tested **first**: a zero-resource inventory satisfies the subset test
vacuously, which is the exact vacuity the third arm exists to prevent.

**Constraints honoured.** No new sprint output state — `[OK]` / `[WARN]` / `[FAIL]` only, all of
which the case already emitted. `fail()`'s effect on exit status untouched. `CC_HERMETIC`, both
poison-control blocks, the D2 credential grep and `json_read` untouched. Nothing under
`cloudcost/scripts/` edited.

---

## 3. G3 — the third arm's precondition

The ticket asked whether the case's existing orchestrator-exit assertion already discharges the
precondition that a run reaching the not-applicable arm had complete coverage. **It does not**, for
two independent reasons, and the coverage signal is not available anywhere else the sprint can
read.

1. **`mix aetheris` discards every command's exit code.** Verified at harness `871a720`:
   `lib/mix/tasks/aetheris.ex` is `_ = Aetheris.CLI.run(argv); :ok`, and `CLI.run/1`'s
   `System.halt(exit_code)` is commented out on that path. So the case's `fail "… non-zero exit"`
   branch is reachable only when the Mix task *raises*; a run that ends `:failed` exits 0 and the
   case prints `[OK]`. This is BL-044, still open — appended to that row as audit input.
2. **Even a propagating exit code would not settle it.** A `run_command` returning non-zero inside
   an agent run is a tool result, not a run failure; the LLM decides what to do next.
3. **The coverage signal reaches no artifact.** The inventory envelope is exactly five keys on all
   three adapters — `provider`, `account`, `period`, `resources`, `generated_at` — with no
   `not_inventoried` and no status (BL-098). `fetch_linode.py` writes the inventory **before** it
   computes `complete = not errors and not not_inventoried`, so a partial run leaves a
   complete-looking artifact. The adapter's summary, which does carry `not_inventoried`, goes to
   its own stdout: **0 occurrences across all 13 archived `sprint/*/cloudcost/run.json` captures**,
   for both `not_inventoried` and `regions_swept`.

**What would discharge it: BL-098** — a sanctioned extras key on the §Normalized inventory
envelope. That row is explicitly out of scope for this cycle (`m4-consolidation.md` §Scope).

### Declared deviation

The ticket specifies the third arm as *"not applicable, stated as such"* and requires that a run
whose coverage was incomplete **must not reach that arm at all**. Because coverage is not
establishable from any artifact, that guarantee cannot be built today. The arm is therefore worded
as an **unknown that names its own limit** rather than as a clean not-applicable:

```
[WARN]  rule legibility not applicable: aws_inventory_2026-08.json carries 0 resources, and the
        catalog evaluated 0 — neither a pass nor a failure. Adapter coverage is not recorded in
        the inventory envelope (BL-098), so this is an unknown, not a clean empty account
```

It still cannot read as a pass, and the three homes — a value, an unknown, a failure — stay
distinct. Reported rather than papered over.

---

## 4. The retirement census

Method: `git grep -n -i -E` over tracked files, run from each repo root with `git -C <abs>` so no
command depended on the shell's cwd. Two passes — a term sweep and a substance sweep — because a
census keyed on a token finds the token, not the class.

### Terms run

**Pass 1 (both repos):** `plant`, `planted`, `planting`, `reserved.?ip`, `elastic.?ip`,
`nodebalancer`, `orphan`, `BL-069`, `prerequisite`, `pre-requisite`, `PENDING`, `fixture`,
`unattached`, `teardown`, `tear ?down`, `≥1[- ]orphan`, `>=1 orphan`, `at least one orphan`,
`delete it after`, `delete after the run`, `remember to delete`, `detached volume`,
`unused volume`.

**Pass 2 (both repos), added because the claim propagates without the word "plant":** `re-plant`,
`replant`, `expected-red`, `expected red`, `known-positive`, `arm the assertion`, `re-arm`,
`rearm`, `console →`, `Allocate`, `Reserve in Datacenter`, `before the run`, `must be deleted`,
`human-owned`, `billable`.

Pass 2 found one site pass 1 had not: `docs/reviews/m2-cloudcost-closeout.md:98`
(*"Live tripwire: BL-069 (re-plant a resource before any run that must assert ≥1)"*), classified
as a record.

**Notable negatives, recorded as results.** `>=1 orphan`, `at least one orphan`,
`remember to delete`, `delete after the run`, `detached volume`, `unused volume`, `pre-requisite`,
`replant`, `arm the assertion`: **zero hits in both repos**. `teardown` / `tear down`: no relation
to cloud-resource cleanup in either repo. `orphan` in `../aetheris` is ~95% the unrelated
orphaned-*run* sweep subsystem. And `../aetheris/CLAUDE.md` carries **no** plant, BL-069 or
reserved-IP hit at all — the harness repo's only carrier is `sprint.sh` itself.

### Classification and treatment

**(a) Live instructions — treated.**

| Site | Treatment | Route |
|---|---|---|
| `cloudcost/runbook.md` §"Exercising the ≥1-orphan path" — the canonical how-to, with the DO, AWS and Linode recipes | **Corrected in place**, retitled §"What a zero-orphan account means, and what the sprint asserts instead". The recipes are gone; the section now states that a zero is the desired state, that the practice is retired, and what replaced it. The offline check snippets that followed are kept — they are not plant material. | decision 8 |
| `docs/backlog-2026-06.md` BL-069 Done-when | **Step 0, before any implementation** — dated `[corrected 2026-08-06]`, superseded text kept beneath, per the row-editing pattern established on BL-100. Then a DONE section recording closure **by retirement**. | §Close criteria item 4, prospectively |
| `../aetheris/scripts/sprint.sh` — the assertion and its KNOWN-RED block | Replaced; see §2. | the ticket |
| `CLAUDE.md` (agents) §Definition of done — the gate rule's closing exemplar | **Corrected in place, minimal.** The rule is preserved verbatim in force (carry red, name it, never quietly relax or re-point it); only the closure claim is fixed, with the superseded sentence quoted in the correction marker. | decision 8 — **arbiter-ruled** |
| `docs/handoffs/handoff-cloudcost-rig-batch-2026-08-03.md` §Live tripwire; `…-close-2026-08-04.md` and `handoff-linode-provider-three-kickoff-2026-08-04.md` §Live tripwires | **Dated superseded note, original text intact**, one per file. | **decision 7** — see the routing note below |
| `cloudcost/milestone.md` §Prerequisites 2; `cloudcost/m2-milestone.md` status line, §Prerequisites 3 (**`Status: PENDING`**) and the rows-filed summary; `cloudcost/m3-milestone.md` §Prerequisites 3, §Rule reachability and both §t3 imperatives | **One dated note per document**, scoped to the document and enumerating its carriers; original text not rewritten. | decision 10, then decision 7 |

> **The handoff route, corrected by the arbiter.** These were first routed through **decision 9**
> (undecidable liveness → take the note). That was wrong, and the treatment being identical does
> not make the routing harmless. A handoff is a record of a moment *by construction* — which is
> why handoffs carry no manifest row and never travel as current — so it lands cleanly as a closed
> record and **decision 7** applies directly. Reaching for the undecidable default where a rule
> decides cleanly is how the default becomes the path of least resistance and the rules stop
> discriminating.

**What each note carries**, uniformly: what replaced the practice and where the live description
now lives; **no claim about what the new assertion reports** on any leg — it has not run on all
three, and one leg will legitimately read not-applicable indefinitely; and it supersedes **the
imperative**, not the record that a tripwire was armed. The record is the thing an in-place rewrite
would have destroyed.

**Establishing the closed-record status rather than inferring it from the filename** (decision 10):
`cloudcost/milestone.md` states `CLOSED 2026-07-29`, `m2-milestone.md` states `CLOSED 2026-08-03`,
`m3-milestone.md` is closed per `m4-consolidation.md` §Ticket set and the m3 close of 2026-08-05.
The current equivalent for cloudcost operational prerequisites is `cloudcost/runbook.md`
§Prerequisites, which is live and was corrected in place.

**(b) Historical records — left intact.** Every `cloudcost/docs/*implementation-notes*.md` hit
(m1 t1–t5, m2 t1–t4, m3 t1–t3); every `docs/reviews/*` hit including the m1/m2/m3 review files and
`m2-cloudcost-closeout.md:98`; the m1/m2/m3 close-out narratives inside the milestone documents;
`docs/project-knowledge-manifest.md` (a dated record of the m3 export-boundary regen reasoning, not
live guidance, and regenerated at the next export boundary in any case);
`cloudcost/tests/test_compose_report_data.py` and `docs/reviews/m1-cloudcost-t3-review.md`, which
use "planted" in an unrelated sense (a value planted in a test fixture).

**(c) Retractions — the territory t1a seeded.** `cloudcost/m4-consolidation.md:87` (decision 12)
and `:146-152` (§What t2 inherits, which quotes the Done-when it retracts) were returned by the
term census as hits and are not sites to treat — they are the retraction. Distinguishing these
from live instructions was t1b's carry 2, and it applies unchanged here.

### One record I could not verify, stated as a record

`cloudcost/docs/m3-t3-implementation-notes.md` carries *"The plant must be deleted —
`aetheris-m3-bl069-plant` (`2405879`, us-southeast), a console write, human-owned. The agent stays
read-only and did not delete it."* Two independent records state the deletion happened: BL-069's
own row (*"The plant is deleted after the run … the Linode leg reverts to red"*) and
`docs/project-knowledge-manifest.md` (*"reverted when the plant was deleted"*). This session holds
no Linode credential, so nothing here is an observation of the live account. Left intact as a
discharged obligation; if an operator wants certainty, the check is a console read, not a run.

---

## 5. Mutation posture — all arms

Owed by the author, and constructed rather than argued. The block under test was **extracted
verbatim** from `sprint.sh` (identity proven by a `grep -F` of the extracted text back against the
file, not by retyping) and driven against staged directories with the same `ok`/`warn`/`fail`
helpers the sprint defines. Arm 1 was additionally observed in a real live sprint run.

Both `[FAIL]` fixtures are **real artifacts**, not invented ones — the out-of-vocabulary case in
particular is a surviving pre-m2 inventory that genuinely carries the provider vocabulary the
assertion exists to catch.

| # | State constructed | Arm observed |
|---|---|---|
| 1 | live DO run, 18 resources, all canonical | `[OK] rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set` |
| 2a | `cloudcost/output/do_inventory_2026-07.json` — real, pre-m2, carries `droplet` / `reserved_ip` | `[FAIL] … type(s) outside the canonical set reached the catalog: droplet, reserved_ip (canonical: compute_instance, database, database_snapshot, load_balancer, snapshot, static_ip, volume)` |
| 2b | `type` removed from one resource of the live DO inventory; catalog re-run over it | `[FAIL] … the catalog could not read 1 of 18 entries: [{"index": 0, "reason": "resource entry has no type"}]` |
| 2c | catalog's `totals.resources` set to 11 against an 18-resource inventory | `[FAIL] … the catalog evaluated 11 + skipped 0 of the 18 resources the adapter emitted — the inventory did not reach it intact` |
| 3 | `cloudcost/output/aws/aws_inventory_2026-08.json` — real, 0 resources | `[WARN] rule legibility not applicable: … 0 resources, and the catalog evaluated 0 — neither a pass nor a failure. Adapter coverage is not recorded in the inventory envelope (BL-098), so this is an unknown, not a clean empty account` |
| guard a | inventory present, orphan-candidates artifact absent | `[FAIL] … inventory=…do_inventory_2026-08.json orphan_candidates=MISSING` |
| guard b | empty output directory | `[FAIL] … inventory=MISSING orphan_candidates=MISSING` |
| guard c | two inventories (a stale artifact surviving the clear) | `[FAIL] … inventory=MISSING orphan_candidates=…` (cardinality ≠ 1) |

**Arm 3 does not read as a pass** — separately confirmed: its label is `[WARN]`, its text opens
"not applicable", and it names the unknown. That was the specific misreading the ticket named.

**The incomplete-coverage case is demonstrated from source, not from a run.** `fetch_linode.py`
writes the inventory before it computes `complete`, so a partial run leaves an artifact
indistinguishable from a complete one. No Linode credential was available to run a real partial,
and no artifact would have carried the difference if one had been. This is the reason arm 3 names
its own limit rather than claiming a clean not-applicable — see §3.

---

## 6. Done-check

### Legs run

**digitalocean — run.** `CLOUDCOST_DO_TOKEN` is set. Two full runs, pre- and post-edit.

**aws — not runnable.** `CLOUDCOST_AWS_ACCESS_KEY_ID` and `CLOUDCOST_AWS_SECRET_ACCESS_KEY` are
unset in this session; the case's credential preflight `exit 1`s without them. A stated gap.

**linode — not runnable.** `CLOUDCOST_LINODE_TOKEN` unset; same preflight.

Both AWS and Linode **poison-control arms (i) and (ii) still executed** on the DO leg — they are
provider-independent — and both passed. Only arm (iii), the credential-survives check, is
provider-gated and therefore unexercised for those two.

### BL-069's assertion outcome, before and after

Same leg, same day, forty minutes apart. Pre-edit, `sprint/20260806_182514`, run
`cloudcost-orch-digitalocean-XApoxQ` — the carried red, quoted from the live run rather than from
a prior record:

```
[FAIL]  orphan candidates: 0 (expected ≥1 — BL-069 armed: the DO reserved IP was deleted
        2026-07-30; the AWS Elastic IP is Prereq 3, PENDING; the Linode plant is m3 §t3)
```

Post-edit, `sprint/20260806_182911`, run `cloudcost-orch-digitalocean-OK48Sw`:

```
[OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance,
        load_balancer, volume] all drawn from the canonical set
```

The case is otherwise unchanged, and the leg is now fully green: **15 `[OK]`, 0 `[FAIL]`,
0 `[WARN]`** post-edit, against 14 `[OK]` / 1 `[FAIL]` pre-edit (counted over the case's own
section of the output, not the whole sprint).

### `cloudcost/scripts/` blob hashes — unchanged across the ticket

Verified at open and at close, `git -C /home/it/sandbox/elixirws/aetheris-agents ls-tree HEAD
cloudcost/scripts/`:

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

All eight, including the four shared scripts the cycle's scope names. `detect_orphans.py` was
*run* during the mutation work, writing only into a scratch directory.

### `drift_check.py --strict`, post-commit

Run after the commit, not before — check 8 reads committed history, so a pre-commit run cannot see
the staleness the edit introduces. **8 PASS, 0 FAIL, 5 WARN, 7 INFO, exit 0.** All five WARNs are
`project_knowledge` manifest staleness, the one class the strict-mode exemption covers. Named:

| WARN | This ticket? |
|---|---|
| `cloudcost/milestone.md` manifest=`7a7b7ec` current=`9bb09b4` | **yes** — the dated note |
| `CLAUDE.md` (agents) manifest=`13fc8c4` current=`9bb09b4` | **yes** — the gate-rule correction |
| `docs/backlog-2026-06.md` manifest=`de71e2b` current=`9bb09b4` | **yes** — BL-069, BL-074, BL-044 |
| `CLAUDE.md` (harness) manifest=`1743e75` current=`f6fbd82` | no — carried from t1a-p |
| `docs/methodology/milestone-methodology.md` manifest=`0a0439f` current=`aaf0f9a` | no — carried |

**Three, and exactly three, are attributable to this ticket** — which is the count of
manifest-tracked files it touched. Established rather than inferred: the manifest's path column
was matched exactly, after a substring grep had wrongly reported `cloudcost/runbook.md` and
`cloudcost/m3-milestone.md` as tracked (it was matching the `docs/rig/runbook.md` and
`docs/aetheris/runbook.md` rows). Both are untracked, as are `m2-milestone.md`,
`m4-consolidation.md`, the three handoffs and these notes. The mismatch was noticed only because
check 8 not warning about a file I had just edited was implausible — the same shape as a gate
pointed at the wrong target returning a clean result.

### `mix test`, off-territory

```
Finished in 90.2 seconds (2.5s async, 87.7s sync)
969 tests, 0 failures, 133 excluded
```

Green. No harness code was touched — the only harness change is `scripts/sprint.sh`, which the
suite does not cover — so this is the boundary run the gate rule asks for, not a regression check.

---

## 7. Forwarded

- **BL-074** — coupling appended: the sprint case is now a consumer of `_normalized.CANONICAL_TYPES`,
  plus two observations for the sweep (no public accessor; `usable_resources()` validates presence
  but not membership).
- **BL-044** — audit input appended: `sprint.sh`'s cloudcost orchestrator-exit assertion is vacuous
  because the Mix task discards the code.
- **BL-077** — nothing forwarded. Recorded as a negative: the placement residual the ticket
  anticipated did not arise, because the assertion sites outside the period guard.
- **BL-098** — named as the thing that would let the third arm claim a clean not-applicable. No
  change to the row; it already says what it needs to.

## 8. Deviations from the ticket

1. **The third arm reports an unknown, not a clean not-applicable** — §3, with evidence.
2. **Notes filename prefixed `m4-`** — declared at the top of this file.
3. **`cloudcost/m4-consolidation.md` edited though not in Touches** — its §Ticket set row for t2
   said "not started", which is false the moment this work lands, and §What this cycle established
   is the only home for what t2 established. Both are cycle-record duties no other document
   performs.
