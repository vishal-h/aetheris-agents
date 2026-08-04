# BL-083 — classify the unclassified use cases; provider in the cloudcost label (implementation notes)

Patches the label classifier and adds a standing guard so the two ways it rots cannot re-arm
silently. 128 runs moved out of Unclassified. These notes carry the approach adjudication
(superseding handoff §Corrections 3), three ticket/row claims that did not survive re-derivation,
and one hazard neither document mentioned.

---

## Approach: label-patch, not run_id re-keying — superseding handoff §Corrections 3

The handoff (`docs/handoffs/handoff-cloudcost-rig-batch-2026-08-03.md:51-68`) recorded the open
question as **answered** in favour of re-keying `classifyRun` on the run_id prefix, calling it
"strictly better" on three grounds: self-maintaining (first segment is the use case), fixes the
legacy provenance label for free, and decouples grouping from the label this row rewrites.

**Reversed after verifying the run_id shapes at HEAD.** The argument holds for three of the four
affected use cases and fails on the fourth, which is the one that decides it:

| label | run_id at HEAD | prefix-keying verdict |
|---|---|---|
| `Cloudcost Orchestrator` | `cloudcost-orch-aws-3KU2NQ` | works, carries the provider too |
| `Docbuilder Context Builder` | `docbuilder-ctx-wuEDrA` | works |
| `Capability Matrix -- Provenance` | `cap-matrix-provenance-FJ-U8A` | works — and is cleaner than the label |
| `at1cmd — TAP Tenant Dispatcher` | `uc-api-t2-AeGOtw-at1cmd` | **fails** |
| `at1qry — TAP Tenant Collector` | `uc-api-t2-tuquiQ-at1qry` | **fails** |
| `cot1 — TAP Gateway` | `uc-api-t2-tuquiQ-cot1` | **fails** |

Three things break at once on the api rows, and none is cosmetic:

1. **The first segment is not the use case.** It is `uc`, and the meaningful prefix is
   `uc-api-t2` — a *milestone* name. `SELECT count(*) FROM runs WHERE run_id LIKE 'api%'` returns
   **0**. The "self-maintaining" property the handoff rests on does not hold here.
2. **The discriminator is a suffix, not a prefix.** Tenant vs gateway is `…-at1cmd` / `…-cot1` at
   the *end* of the id. Prefix-keying collapses both into a single `uc-api-t2` group, destroying
   exactly the API/Tenant ÷ API/Gateway split this row is required to restore. Recovering it needs
   substring or suffix matching — a different algorithm, not a different key.
3. **The shared prefix embeds a milestone number.** `t2` → `t3` unfiles every api run. That is the
   same coupling the handoff objected to in labels, relocated rather than removed.

Two further facts weaken the "decoupling" argument on its own terms. `classifyRun`'s input is
`COALESCE(r.label, r.run_id)` (`rig/src-tauri/src/commands/harness.rs:161`), so the label path
**already falls back to run_id** for the 299 unlabelled runs — label-keying is a superset of
run_id-keying, not an alternative to it. And the legacy-provenance win is real but small: one
label, 14 runs, handled here by one extra prefix string.

**Decision: patch the label list.** run_id re-keying remains attractive for a future in which
run_ids are made regular by construction (that is a harness convention change, not a Rig change),
and the api ids are the specific thing that would have to change first.

**Residual, conceded rather than hidden.** Label-keying is safe for *suffix* appends — the
`Cloudcost · AWS` change in this very ticket proves it, since `startsWith('cloudcost')` is unaffected
by anything after the prefix. It is **not** safe against a change to a label's *leading* word: renaming
`Docbuilder Context Builder` to `Context Builder` would silently unfile 23 runs. That residual is
what the standing guard below exists to catch, and it is why the guard checks declared agent labels
rather than only observed runs.

---

## Three claims that did not survive re-derivation

The ticket said to re-derive rather than copy. It mattered three times.

**1. The docbuilder multi-label warning was wrong.** Both the row and the ticket state that
docbuilder runs appear under `Docbuilder Orchestrator` *and* bare `Context Builder` /
`Context Orchestrator`, and that "the latter two don't start with `docbuilder`, so one prefix won't
catch them." At HEAD there is no bare label:

| label | runs |
|---|---|
| `Docbuilder Orchestrator` | 32 |
| `Docbuilder Context Builder` | 23 |
| `Docbuilder Context Orchestrator` | 2 |

All three start with `Docbuilder`, so the single `docbuilder` prefix catches all 57. No special
handling was added. Acting on the warning would have produced dead prefixes for labels that do not
exist — the very defect this row fixes.

**2. Two counts were stale and one label was missed entirely.** The row's table says the legacy
capability-matrix label has 5 runs; it has **14**. It also omits `Capability matrix generator`
(1 run), which falls through identically and shares no prefix with `cap-matrix:`. Both are covered
by the added `capability matrix` prefix. Cloudcost is 12, not 9, as the ticket anticipated.

**3. `eduloka` is not a "live orchestrator falling through" — it has never run.**
`eduloka/agents/eduloka_orchestrator.exs:131` declares `label: "Eduloka Orchestrator"`, but
`SELECT count(*) … WHERE lower(coalesce(label,run_id)) LIKE 'eduloka%'` returns **0**. This puts
deliverable 1 ("add eduloka") in direct tension with deliverable 2 and the Done-when ("every
remaining entry must match ≥1 real label") — added naively, `eduloka` *is* a new dead entry.

Resolved by making "real label" mean **declared agent labels ∪ observed run labels**, rather than
observed runs alone. Under that definition `eduloka` is live (a real agent declares it) and
`api-tenant` / `api-gateway` are dead (nothing declares or emits them). This is the more useful
definition anyway: a prefix should be judged against what the system *can* produce, not against who
happened to run what, or the first eduloka run lands in Unclassified and the guard has already been
told the prefix was deletable.

---

## The hazard neither document mentioned

`groupRuns` (`RunList.tsx:141-157`) builds its ordered output by iterating `USE_CASE_PREFIXES` and
pushing **one group per entry**. The obvious shape for this fix — several entries mapping to one
group, e.g. `at1cmd` and `at1qry` both → `API / Tenant` — would therefore have rendered the same
runs under two identical headings.

Fixed structurally rather than by de-duplicating downstream: the entry shape changed from
`{ prefix: string }` to `{ prefixes: string[] }`, one entry per group. `classifyRun` becomes
`prefixes.some((p) => lower.startsWith(p))`. A regression test asserts no group label is declared
twice, because the failure is visual and a reader diffing the array would not see it.

---

## What changed

| file | change |
|---|---|
| `rig/src/components/modules/harness/RunList.tsx` | `prefixes: string[]` shape; added `cloudcost`, `docbuilder`, `eduloka`, `capability matrix`; replaced dead `api-tenant`/`api-gateway` with `at1cmd`/`at1qry`/`cot1`; `classifyRun` uses `.some()` |
| `cloudcost/agents/cloudcost_orchestrator.exs` | `label: "Cloudcost · #{provider_name}"` → `Cloudcost · AWS` / `Cloudcost · DigitalOcean` |
| `scripts/check_run_classifier.py` | new — parses the live `USE_CASE_PREFIXES` and checks both rot directions |
| `tests/test_run_classifier.py` | new — 15 tests making the guard standing under `pytest tests/` |

Ordering was checked, not assumed: `cap-matrix: cloudcost` must group as **Capability Matrix**, not
Cloudcost. It does, because matching is `startsWith` and the label begins `cap-matrix:` — but that
is a coincidence of the algorithm, so it is pinned by a test. If anyone ever changes `startsWith`
to `includes`, that test fails rather than nine capability-matrix runs quietly migrating.

---

## Verification

**No JS/TS test harness exists** in `rig/` — no vitest, jest, or testing-library in
`package.json`, no config file, scripts are `dev`/`build`/`lint`/`preview` only. Per the ticket, this
is reported rather than worked around: no framework was introduced. The guard is Python, in the
same family as `drift_check.py` and BL-084's manifest suite, and the classifier logic is **parsed
out of `RunList.tsx`** rather than re-typed, so the guard cannot pass while the real classifier is
broken.

**Store check — 957 runs, before vs after:**

| group | before | after |
|---|---|---|
| API / Gateway | 0 | 15 |
| API / Tenant | 0 | 29 |
| Capability Matrix | 85 | 100 |
| Cloudcost | 0 | 12 |
| Docbuilder | 0 | 57 |
| Drive / Email / Payslip / Provenance | 89 / 33 / 55 / 2 | unchanged |
| **Unclassified** | **693** | **565** |

128 runs rescued. The 565 remaining are evals, smoke tests, forks and unlabelled `run_*` ids —
no use case with a live orchestrator is among them, which is asserted directly by the
"every declared agent label classifies" test rather than eyeballed.

**Mutation-checked, both directions.** A check only ever seen passing is not yet a check:

- added a `zzz-nonexistent` prefix → `[FAIL] prefix 'zzz-nonexistent' … matches NO known label`;
- removed the `cloudcost` prefix → `[FAIL] declared label 'Cloudcost · X' falls through to Unclassified`.

Both restored and confirmed byte-identical afterwards. The guard also caught a real defect in its
own first draft: an unanchored `label:\s*"…"` regex matched *prose inside a system_prompt* (the
capability-matrix agents document `- The label: "..." value`), yielding a phantom declared label
named `...`. The pattern is now anchored to struct fields.

`bun run lint` clean · `bun run build` clean · `pytest tests/` 129 passed, 7 xfailed · the new file
passes hermetically with `AETHERIS_DB_PATH` unset.

**Not done:** the Rig visual glance. The run list renders through Tauri `invoke('harness_list_runs')`,
which does not resolve in a plain browser, so the grouping was verified against the same data by
computation rather than by looking at the UI. The group *headings* are the one thing that check
cannot see.
