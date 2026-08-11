# BL-132 — the reachability census over C1–C15 (implementation notes)

The row's question, once per contract: *is the behaviour this states produced by any invocation
the orchestrator makes?* Answered by **running the entry point** over recorded artifacts and
reading the output, not by reading source for what it implies — the row's method refinement 1.

`Touches: cloudcost/milestone.md §Contracts (nine reachability sentences); this file (new). The
BL-132 row in docs/backlog-2026-06.md is in the row's Touches but was not edited — see §Deviations.`

**Branch taken: push.** None of the four hold conditions fired. Stated before acting and checked
again at the end: no verdict required amending a **guarantee** (every sentence landed qualifies a
reachability claim, which `Do not generate` permits); the population split **is** the row's twelve;
the one finding that could have needed a call does not clear the row's already-cost filter and is
recorded here rather than acted on; and **all three self-reporting contracts' own claims survived
check** — the condition that would have forced a hold is the one that came closest to firing, and
it did not.

---

## 1. Population, derived at HEAD

Derived from the file, not from the row:

```
$ grep -c '^### C[0-9]' cloudcost/milestone.md
15
$ grep -n '^### C[0-9]' cloudcost/milestone.md
317:### C1 — Resource type vocabulary  *(N1, N8, D11)*
344:### C2 — Resource state vocabulary  *(X1, N2, D10)*
370:### C3 — Timestamps and age  *(N3, N4, D12, D17, D20)*
402:### C4 — Money and currency  *(N5, P3, P5, R2)*
476:### C5 — Percentages and ratios  *(N9, P9, R3)*
501:### C6 — Tags  *(X3, N7, D6, D7)*
533:### C7 — Attachment  *(D15, D16)*
553:### C8 — Thresholds and the scoring model  *(D1, D2, D3, D4, D8, D9, D21, F1, F2, F3, F4, P1, X4)*
624:### C9 — Identity, slugs and filenames  *(N6, D18, P10)*
646:### C10 — Document shape and discovery  *(P4, P6, P8, P11)*
677:### C11 — Optionality and presentation  *(R1, P2, P7)*
734:### C12 — Encoding  *(X5)*
759:### C13 — Carry-only fields (adapter-owned)  *(X2, D19)*
781:### C14 — Adapter cost-model obligations (adapter-owned)  *(D13, D14)*
805:### C15 — Neither arm  *(D5, R4)*
```

`Positional claim, per m5-D1: line numbers above measured at 8845d85, before this ticket's edits.`

**Fifteen identifiers, C1–C15, contiguous — no gap, no duplicate, no C16.** Less **C4** and
**C11**, answered at m5 t2; less **C13**, not applicable. **Twelve to answer.** The row's figure is
confirmed, not inherited.

---

## 2. The census

**Verdict scope.** Most contracts are not uniform: a guarantee that runs on every invocation sits
beside a clause describing a hole nothing currently reaches. The verdict column gives the
contract's own shape; the basis column says what each rests on.

| | contract | verdict | what it rests on |
|---|---|---|---|
| **C1** | Resource type vocabulary | guarantee **reachable**; unenforced-validation clause **source-only** | all three adapters import the `TYPE_*` constants, so no run emits an out-of-vocabulary `type` for `usable_resources` to miss |
| **C2** | Resource state vocabulary | guarantee **reachable**; X1's clause **source-only, and its named route does not carry** | 0 `state` in either payload and either rendered report against 18 in the consumed inventory; both interpolation sites gated on `STOPPED_STATES` |
| **C3** | Timestamps and age | **reachable**; D17 and N3 **source-only** — *self-report confirmed* | three runs resolved reference dates to their recorded fetch timestamps, none the wall clock; every adapter stamps `generated_at` via `iso_now()` |
| **C4** | Money and currency | **source-only** — *answered m5 t2, not re-derived* | m5-D2; the *Source-only by ruling* paragraph already in the contract |
| **C5** | Percentages and ratios | **reachable**, whole | coverage `0.8889` and `0.4` at four decimals; zero-base `delta_pct: null` on a real service row beside `-78.58` on two others |
| **C6** | Tags | guarantee **reachable**; X3 **reachable under aws only**; N7 **source-only** | DO and Linode cannot express `k=v` natively; no adapter emits a non-`str` tag element |
| **C7** | Attachment | **reachable**, whole | a real Linode candidate's evidence carries both D16 clauses verbatim, including the `tag:<name>` exclusion |
| **C8** | Thresholds and the scoring model | catalog **reachable**; X4 **source-only** — *self-report confirmed*; D21 write-only **confirmed** | 18 `last_activity_at: None` emission sites across three adapters; the payload's own `cannot_fire_no_last_activity_at` marker; no consumer reads `parameters` |
| **C9** | Identity, slugs and filenames | derivation **reachable**; both D18 collision routes **source-only** | filenames derived per run; the orchestrator runs one provider per invocation, and every adapter emits a `period` |
| **C10** | Document shape and discovery | **reachable**; P8 and P11 **source-only** | prior period `2026-07` derived from `2026-08` with no clock; `source_granularity: "service"` composed and compared against nothing |
| **C11** | Optionality and presentation | **source-only** in its P2 clause — *answered m5 t2, not re-derived* | m5-D2; the *Source-only by ruling* paragraph already in the contract |
| **C12** | Encoding | self-report **confirmed**; the corruption **source-only** | 4 sites specified in `render_report.py`, 5 unspecified across the other two; every adapter value is ASCII |
| **C13** | Carry-only fields | **not applicable** | states field ownership and a keying prohibition, not behaviour an invocation produces — the row's method refinement 3 |
| **C14** | Adapter cost-model obligations | guarantee **reachable**; D14 **source-only** on the current three | `grand_total 39.74` built from three service line items; no recorded artifact carries a stopped database |
| **C15** | Neither arm | **reachable** | the ephemeral matcher runs on every detect pass; it matched no name in these runs, which is a result and not an absence of exercise |

**Sentences landed: nine** — C1, C2, C3, C6, C8, C9, C10, C12, C14, each closing its own contract.
**None landed in C4, C11** (answered; the row forbids re-editing them), **C13** (not applicable),
or **C5, C7, C15** (reachable whole, nothing to qualify).

---

## 3. The instrument

The row's method refinement 1: run the entry point's own forms and check contracts against what
came out.

**Both STEP 3 arg forms were run**, transcribed from
`cloudcost/agents/cloudcost_orchestrator.exs` §STEP 3 — *"If STEP 1 printed `files.costs`, use this
form"* and *"If STEP 1 did NOT print `files.costs`, use this form instead"*:

```
# form A — the full triple
python3 scripts/compose_report_data.py --cost <COSTS> --inventory <INV> --orphans <ORPH> \
        --output-dir <OUT> --history-dir <HIST>
# form B — --cost and its value dropped together, nothing else changed
python3 scripts/compose_report_data.py --inventory <INV> --orphans <ORPH> \
        --output-dir <OUT> --history-dir <HIST>
```

preceded by STEP 2 (`detect_orphans.py <INVENTORY> --output-dir …`) and followed by STEP 4
(`render_report.py <REPORT_DATA> --output-dir …`), in the orchestrator's order.

**Five chains ran:** DO 2026-08 form A and form B; Linode 2026-07 form A; AWS 2026-08 STEP 2 only
(its recorded inventory holds zero resources, so it constrains nothing downstream and is reported
as such rather than counted as coverage); and a **two-month DO pair** into one history directory,
which is the only way to reach the month-on-month arm.

**Form B is worth naming.** It produced `cost_grand_total: null, currency: null` at one bundle —
the blanked headline. That is C4's em dash *reachable by a route C4 does not describe*, and it is
consistent with m5 t1's E8, which already drew the distinction: *"the em dash is reachable; the em
dash for the reason C4 gives is not."* Recorded because it is the one place this census could have
contradicted the two contracts it was forbidden to re-derive, and it does not.

**Artifact provenance, stated as a limit.** The recorded artifacts live under `cloudcost/output/`,
which is **gitignored** — `git ls-files cloudcost/output/` returns only `.gitkeep`. They are real
prior-run output, not committed fixtures, so a reader cannot reproduce these runs byte-for-byte
from the tree. All execution wrote to a session scratchpad; nothing was written under `cloudcost/`.

---

## 4. The three self-reporting contracts

The row's method refinement 2 — *those are claims to check, not answers to inherit.* **All three
hold**, and each was checked by a different instrument.

**C3 — checked from output.** Three runs resolved reference dates of `2026-08-07T16:56:59Z`,
`2026-08-04T04:29:40Z` and `2026-08-05T08:18:08Z`. Every one is the artifact's recorded fetch
timestamp; none is the wall clock of the day they ran, 2026-08-11. The fallback branch is
unreached, exactly as C3 says, and this is an observation about a run rather than a reading of a
branch.

**C8 — checked from output, then from source.** The composed payload carries the string
`cannot_fire_no_last_activity_at`. That is the pipeline reporting X4's status about itself, and it
agrees with the source: `last_activity_at` is `None` at **eighteen** emission sites — five in
`fetch_do.py`, five in `fetch_linode.py`, eight in `fetch_aws.py`. The modifier cannot fire.

**C12 — checked from source, since no run can show it.** At `8845d85`: `render_report.py` has four
I/O sites, three carrying `encoding="utf-8"` explicitly and the fourth the Jinja2
`FileSystemLoader`, whose own default is UTF-8 — which is how the contract's *"all four of its I/O
sites"* reconciles. `detect_orphans.py` has two and `compose_report_data.py` three, none specified:
the five the contract names. `_normalized.py` performs no file I/O.

**Why this is the section that mattered.** BL-131's whole cost was a reachability claim taken on a
document's word, and the hold conditions single these three out for that reason. Had any of them
been false, this ticket would have stopped and relayed rather than landed a sentence.

---

## 5. Findings

**One finding, recorded and not acted on, under the row's own threshold.**

**C8's D21 enumeration has drifted.** The contract says the declared parameter block *"covers the
age thresholds and the coverage threshold, and nothing else"*. At HEAD the block emits **five**
keys — `snapshot_age_days`, `unattached_volume_min_age_days`, `stopped_compute_min_age_days`,
`tagged_account_coverage_threshold`, and **`recent_activity_window_days`**. The fifth is a
modifier's window, not an age threshold and not the coverage threshold, and C8's own next sentence
lists *"the two modifier deltas"* among what is **not** echoed — the deltas indeed are not, but this
modifier's window is.

**Not acted on, deliberately.** The row's findings threshold: *"A finding earns its own action only
if it has already cost something pointable — a session that derived it, a ruling that rested on it,
a check that passed for the wrong reason."* This has cost nothing pointable: no session derived
from the clause, no ruling rests on it, and D21's operative claim — the block is **write-only**,
read by no consumer — is confirmed and unaffected. It is a gap argued from structure, which the
threshold routes here and sweeps at the end rather than acting on. **The swept result is this
paragraph.** C8's landed sentence names it and points here.

**Non-findings, recorded so they are not rediscovered as findings.** C4's `reconcile` arm fired on
the DO artifact (`declared period total 39.74 does not match the sum of its service line items
39.73`), and `reconciled: false` is in the payload — that is P3's tolerance behaving as documented,
not a defect. C11's `region_coverage` was `[]` on all three runs because only `fetch_aws.py` emits
`swept_regions`; the section is reachable under `CLOUDCOST_PROVIDER=aws` and C11's own text already
says one adapter produces it, so nothing is owed.

---

## 6. Deviations

**One, and it is a scoping under-run rather than an over-run.** The row's `Touches` names three
paths; **two changed**. `docs/backlog-2026-06.md` — *"this row only"* — was **not edited**: the row
authorises editing it, and nothing in the census needed to. The census's product is the table in §2
and the nine sentences in `cloudcost/milestone.md`; amending the row's own text would restate a
record that already exists here, and the row is not a place this ticket owes an answer. Named
because an unexercised `Touches` entry is as much a divergence from the ticket as an extra path,
and the row said to name any.

No executable line changed. No contract's guarantee was amended. No new contract, no renumbering,
no edit to a `Closed arm` ruling. C4 and C11 were neither re-derived nor re-edited.

---

## 7. Done-check

Run from the `aetheris-agents/` root; both of item 1's anchors re-resolved at HEAD before running,
per the row. **Neither has moved:** `cloudcost/runbook.md` **§Offline tests** carries the command,
and `CLAUDE.md` **§Commands** carries the root.

- **Item 1** — `python3 -m pytest cloudcost/tests/ -v` → **386 passed**, the figure m5 t1, t2 and
  t3 each recorded. No executable line changed, so a differing count would have been a finding.
- **Item 2** — §Contracts' enumeration printed in §1 above and set against the §2 table: **15
  identifiers, 15 rows, no member on either side alone.**
- **Item 3** — `grep -n 'BL-132' cloudcost/milestone.md` read back from the file: **nine
  `Reachability (BL-132, 2026-08-11)` sentences**, plus the three pre-existing BL-132 mentions
  inside C4's and C11's m4 t5b pointer blocks, which this ticket did not touch.
- **Item 4** — `git status --short`: the two paths in §Deviations and nothing else.

Full output in the packet.
