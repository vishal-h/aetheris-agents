# m2-cloudcost t3 — AWS solo run: implementation notes

**Session scope:** code + offline proof, plus the live cost/report portion of both provider
runs. The **≥1-orphan real-bill close is deferred** to the operator — it is gated on
`m2-milestone.md` §Prereqs 3 (a planted unassociated Elastic IP), still PENDING. No orphan was
planted and 0 orphans was not treated as a failure.

**Commits.** `18883b7` (orchestrator) → `cbf3fbf` (A4) → aetheris `fa158a4` (sprint) →
`b7cb6ca` (matrix) → `711c216` (runbook + BL-076) → this file.
**Not pushed** — both branches handed back for the operator.

---

## Done-check

| # | Check | Result |
|---|---|---|
| 1 | `Code.eval_file` on the orchestrator | **PASS** — default (DO) and `CLOUDCOST_PROVIDER=aws` both evaluate clean |
| 2 | `CLOUDCOST_PROVIDER=aws ./scripts/sprint.sh cloudcost` | **PASS** — hermetic prefix, provider-scoped reset, report found; every assertion green except #7 |
| 3 | DO regression leg, live | **PASS** — pipeline green end-to-end, report at `output/digitalocean/`, AWS report untouched; every assertion green except #7 |
| 4 | A4 field in report_data and rendered; render keys on no payload block generically | **PASS** — 17 regions in `region_coverage`, present on the page; genericity asserted by test |
| 5 | `pytest cloudcost/tests/` | **PASS** — 244 passed (229 baseline + 15 new) |
| 6 | `drift_check.py --strict` | **PASS** — exit 0, 8 PASS / **0 FAIL** / 4 WARN, all four the exempt `project_knowledge` class |
| 7 | ≥1 orphan, both providers | **FAIL — BL-069 firing as predicted**, see below |
| 8 | Capability matrix lists the AWS adapter; Rig source confirmed | **PASS** — `fetch_aws.py` present; source noted below |
| 9 | `CLOUDCOST_AWS_*` absent from trajectory / config_json / committed files | **PASS**, with positive controls |

### Sprint output, verbatim

AWS leg (`CLOUDCOST_PROVIDER=aws ./scripts/sprint.sh cloudcost`):

```
=== uc-cloudcost — aws cost report + orphan detection ===
[OK]    python3 found
[OK]    CLOUDCOST_AWS_* set (read-only key)
[OK]    cleared ../aetheris-agents/cloudcost/output/aws (stale-artifact guard, scoped to this provider)
[OK]    cloudcost_orchestrator.exs evaluates (provider=aws)
[OK]    CLOUDCOST_PROVIDER=aws + no key → eval raises (no-silent-fallback guard)
[OK]    unknown CLOUDCOST_PROVIDER → eval raises
[OK]    poison control: the default chain is visible without the prefix
[OK]    hermetic prefix strips the default chain (AWS_* unset, credentials file → /dev/null)
[OK]    CLOUDCOST_AWS_ACCESS_KEY_ID survives the strip
[INFO]  Starting: uc-cloudcost orchestrator (provider=aws)
[OK]    uc-cloudcost orchestrator → no-json (695 bytes)
[OK]    report: aws/cloudcost_report_2026-08.html (13K)
[OK]    report_data.providers = [aws] — the selected provider, and only it
[FAIL]  orphan candidates: 0 (expected ≥1 — BL-069 armed: the DO reserved IP was deleted 2026-07-30; the AWS Elastic IP is Prereq 3, PENDING)
[OK]    region coverage: 17 region(s) stated in report_data (A4)
[OK]    the rendered HTML states the swept region set
[OK]    no AWS key id in the run output (searched a file with content and a run_id)
[INFO]  Run ID: cloudcost-orch-aws-cwB8KA
```

DO leg (`./scripts/sprint.sh cloudcost`):

```
=== uc-cloudcost — digitalocean cost report + orphan detection ===
[OK]    python3 found
[OK]    CLOUDCOST_DO_TOKEN set
[OK]    cleared ../aetheris-agents/cloudcost/output/digitalocean (stale-artifact guard, scoped to this provider)
[OK]    cloudcost_orchestrator.exs evaluates (provider=digitalocean)
[OK]    CLOUDCOST_PROVIDER=aws + no key → eval raises (no-silent-fallback guard)
[OK]    unknown CLOUDCOST_PROVIDER → eval raises
[OK]    poison control: the default chain is visible without the prefix
[OK]    hermetic prefix strips the default chain (AWS_* unset, credentials file → /dev/null)
[INFO]  Starting: uc-cloudcost orchestrator (provider=digitalocean)
[OK]    uc-cloudcost orchestrator → no-json (704 bytes)
[OK]    report: digitalocean/cloudcost_report_2026-08.html (14K)
[OK]    report_data.providers = [digitalocean] — the selected provider, and only it
[FAIL]  orphan candidates: 0 (expected ≥1 — BL-069 armed: the DO reserved IP was deleted 2026-07-30; the AWS Elastic IP is Prereq 3, PENDING)
[INFO]  Run ID: cloudcost-orch-digitalocean-jgiMaw
```

Live figures: AWS 2026-08 = 8 services / $0.29 / 17 regions swept / 0 resources.
DO 2026-08 = 18 resources, MoM `ok` against its own July ($185.50 → $6.71).

```
244 passed in 84.10s          # pytest cloudcost/tests/
Summary: 8 PASS  0 FAIL  4 WARN  7 INFO     # drift_check.py --strict, exit 0
```

That drift summary is the **post-commit** run, which is the only one whose check 8 means
anything: `project_knowledge` compares the manifest against *committed* history, so a pre-commit
run reads each file's pre-edit hash and cannot see the staleness the edit introduces. Run before
committing it reported the same 0 FAIL but listed `docs/capability-matrix.md` under the
uncommitted-working-tree WARN (the BL-041b class) instead of as stale.

The four WARNs, all `project_knowledge` staleness and all strict-exempt:

```
[WARN] project_knowledge: cloudcost/milestone.md stale     — manifest=9afd8e7 current=7a7b7ec
[WARN] project_knowledge: CLAUDE.md stale                  — manifest=9afd8e7 current=72fd505
[WARN] project_knowledge: docs/capability-matrix.md stale  — manifest=e60bcfd current=b7cb6ca
[WARN] project_knowledge: docs/backlog-2026-06.md stale    — manifest=63f48e1 current=711c216
```

Mid-cycle staleness is expected truth, cleared at the export boundary, not a regression to
chase. None is a structural manifest problem — those are **not** exempt and would have failed.
(The brief anticipated three; the fourth is `docs/capability-matrix.md`, which t3 regenerates.)

### The known-red, named rather than re-triaged

**`[FAIL] orphan candidates: 0` is BL-069 firing exactly as that row predicts**, on both
providers, and is independent of t3. The DO reserved IP that armed the tripwire was deleted
2026-07-30; the AWS Elastic IP is §Prereqs 3, PENDING. t1 had already confirmed the live AWS
account carries no EC2/EBS/EIP/RDS at all, and this run confirms it again (`resources: 0`).

The assertion was left **unchanged and still a `fail`**. Re-pointing or relaxing it is BL-069's
own work; a tripwire quietly downgraded to a warning is how a real regression becomes
unnoticeable later. Only the message changed, to name the ticket and the reason.

Because the sprint reset clears the provider's output *before* the run, this FAIL is honest —
it is 0 orphans from this run, not a green off a stale artifact. That was the m1 t5 r0 F1
lesson and it is what makes the red trustworthy.

**Correction to the brief's expectation:** the aggregate sprint exit is **0**, not non-zero.
`fail` in `sprint.sh` prints without setting an exit status or a failure flag — pre-existing
behaviour shared by all 31 cases, not something t3 introduced. The red is visible as the
`[FAIL]` line above, not in `$?`. Changing that is a sprint-wide behavioural change well
outside §t3; flagging it rather than doing it.

---

## Findings

### F1 — a solo run's month-on-month reads every other provider's prior snapshot (**BL-076**)

`load_prior_snapshots` globs the prior month's directory indiscriminately
(`compose_report_data.py:711`) and `month_on_month` sums the result into one `prior_total`
(`:334`, `:342`). Under decision H that is false: a solo run's report is about the providers in
*that* run.

Demonstrated by composing the real AWS output twice, changing only `--history-dir`:

| history tree | `mom_delta.status` | headline |
|---|---|---|
| shared `history/2026-07/` | `ok` | prior 185.50 (DO, July) vs current 0.29 (AWS, Aug) → **`delta_amount −185.21`** |
| per-provider `history/aws/` | `no_prior_month` | — |

The first row is a **Silent-wrong-answer**: well-formed, plausible, and contradicting §t3's own
done-check sentence ("first AWS run → the m1-tested 'no prior month' path").

**Resolved at the orchestrator, not in compose.** Each run threads
`--history-dir history/{provider}` — decision H's own `history/{provider}/{period}/` layout —
which scopes the lookup with no script change, so `compose` stays unedited outside A4 as §t2 (d)
requires. The shipped AWS run takes the `no_prior_month` path; the DO run still computes its own
MoM correctly ($185.50 → $6.71) after a one-time move of the existing snapshots.

The mitigation is a **caller convention**, so the underlying defect is filed (BL-076) rather
than declared closed: a direct `compose` call against an m1-shaped shared tree still produces
the wrong figure. BL-076 batches with BL-070.

### F2 — `report_data` and the report HTML carry no provider prefix

t2 prefixed the orphan-candidates file only. `report_data_{period}.json` and
`cloudcost_report_{period}.html` are unprefixed, so two providers writing into one `output/`
overwrite each other's report.

**Resolved by the per-provider output directory** (`output/{provider}/`), which the corrected
brief mandates. No script rename, so compose/render stay unchanged outside A4, and the sprint's
stale-artifact reset had to become provider-scoped for the same reason — a whole-tree wipe would
have each leg delete the other's report. Verified: after the AWS leg then the DO leg, both
reports are present.

### F3 — §t3 names a file that does not exist

The ticket says "Regenerate `agents/capability_matrix.exs`". There is no such file. The matrix
is nine per-use-case section agents plus a deterministic assembler:

```
mix aetheris run ../aetheris-agents/agents/capability_matrix_cloudcost.exs
python3 ../aetheris-agents/scripts/assemble_matrix.py
```

The ticket's *invariant* (the matrix lists cloudcost's AWS adapter) held; its *sketch* did not.
Implemented the invariant; correcting the sketch here so the next reader does not re-adjudicate
it. Result: cloudcost 1 agent / 6 scripts, `fetch_aws.py` present, totals 27/82, diff confined
to the Cloudcost block plus the derived counts.

**Rig `CapabilityMatrix` source, confirmed as the done-check asks:**
`rig/src-tauri/src/commands/capability_matrix.rs` — `capability_matrix_load()` reads
`$AETHERIS_AGENTS_PATH/docs/capability-matrix.md` and line-scans the Markdown into
`CapabilityMatrix { use_cases, generated_at }`. It is a **consumer** of the generated artifact,
not a producer of it. Registered at `rig/src-tauri/src/lib.rs:85`; the only other references are
the TS caller (`rig/src/hooks/useCapabilityMatrix.ts`) and its mirror types. Nothing in t3
changes its parse surface — no new column, no renamed heading.

---

## Design decisions

**A4 is a field in the header, not a section.** Adding `region_coverage` to `render_report`'s
`SECTIONS` tuple would emit a rendering note *and* exit 1 for any provider without a swept set —
i.e. every DigitalOcean run, forever. It went into a new `OPTIONAL_FIELDS` tuple instead, where
absence is not degradation. Consequences worth knowing: the renderer's hardcoded stdout
`sections` list and the test suite's `SECTION_IDS` are both **untouched**, and not needing to
touch them is the evidence that A4 landed as a field rather than as a new section.

**A4's shape is a per-provider list**, `region_coverage: [{provider, swept, count}]`, `[]` when
nobody sweeps. The milestone sketched `{swept, count}`; that is its N=1 projection. The list
matches report_data's existing per-provider idiom (`accounts`, `cost_summary.by_provider`) and
is correct at N>1 without any cross-provider merge — which the ticket forbids and which a flat
dict would have forced (union or silent cap).

**Compose reads one *named* key**, `SWEPT_REGIONS_KEY = "swept_regions"`, and never iterates or
copies the provider payload block. A decoy test asserts the distinction rather than describing
it: extra keys placed beside `swept_regions` must appear nowhere in the payload, so a
`context.update(extra)` implementation fails.

**Compose derives nothing.** The region list is carried in the adapter's own order, duplicates
and all (it already sorts and dedupes), and `count` is taken once so the template computes
nothing — m1 §t4's render contract. A test pins the order, and the template prints
`entry.count` rather than `entry.swept | length` so the mutation test can actually fail.

**No symmetric DO credential raise.** The orchestrator raises at eval time when
`CLOUDCOST_PROVIDER=aws` lacks the key pair, and on an unknown provider value. It does *not*
raise on a missing DO token: DO is the *default* sink rather than a selected one, and §t3's own
offline done-check (`Code.eval_file`) has to keep passing on a machine with no DO token.
`sprint.sh` preflights it instead. Recorded because a reviewer will reasonably ask.

**The hermetic prefix is block-local in the sprint, not folded into `run_agent`.** A global env
prefix would be inherited by every other case under `TARGET=all` — the leak the docbuilder cases
already had to `unset` their way out of. Four duplicated lines is the right price; the array is
unset at the end of the block.

**`regions_swept` is not threaded through the LLM.** The adapter prints it on stdout, but the
orchestrator does not carry it into STEP 5. It reaches the report through the file, via compose.
Threading it would violate the prompt's own "do not compute, adjust, or restate any figure" rule
for no gain.

---

## Evidence that the checks can fail

Every new guard was watched failing in the state it guards against, then restored.

| Mutation | Guard that caught it |
|---|---|
| `region_coverage` moved into `SECTIONS` | `test_a_payload_without_region_coverage_is_not_a_degraded_render` |
| template counts with `\| length` | `test_a_mutated_region_figure_reaches_the_html` |
| compose splats the payload block | `test_the_lift_copies_one_named_key_and_nothing_else…` |
| compose re-sorts the region list | `test_the_region_list_is_the_adapters_own_order…` |
| compose drops the key entirely | `test_the_swept_region_set_is_lifted_into_a_named_report_field` |
| a provider named in renderer prose | `test_the_region_block_names_no_provider…` |
| `CLOUDCOST_AWS_*` stripped, provider=aws | orchestrator raise (sprint guard + REPL) |
| unknown `CLOUDCOST_PROVIDER` | orchestrator raise (sprint guard + REPL) |
| env poisoned with fake `AWS_*` | sprint poison probe (i)/(ii)/(iii) |

Two of these fired for real rather than only under a deliberate mutation:

- **the renderer-prose guard fired on this ticket's own first draft**, which named DigitalOcean
  in the comment explaining why the field is optional. Comment reworded.
- **the poison probe's control arm is what makes arm (ii) non-vacuous.** Without first proving a
  bare probe *sees* the poison, "the prefix stripped everything" and "there was nothing to
  strip" are indistinguishable. Arm (iii) is the half people forget: a prefix that stripped
  `CLOUDCOST_AWS_*` too would pass (ii) and break the run.

**DO byte-identity, measured.** Rendering the same DO `report_data` with the input path held
constant (`source_file` is part of the context, so it must not vary):

```
m1 code, key absent    81ab5c7e7ac90b389a134484b041b4945660b8a19b70f26c32ec9684f3cbc960
new code, key absent   81ab5c7e…  identical
new code, key == []    81ab5c7e…  identical
```

A populated field changes the page, so the identity is a result and not a no-op. *First attempt
at this measurement was wrong* — it compared renders from two different filenames and reported a
spurious mismatch. Recorded because the same trap will catch the next person: `source_file` is
in the render context.

**Rendered-prompt diff.** The DO system prompt differs from m1's in exactly five lines, all of
them the `--output-dir`/`--history-dir` literals; the AWS prompt differs from DO's in seven —
provider name, short name, fetch script, and the same directory literals. Nothing else in the
five steps or the rules block is provider-shaped.

---

## Credential hygiene (D2)

`CLOUDCOST_AWS_*` values appear in **none** of: the AWS run's trajectory (40,854 bytes searched),
its `config_json` (4,864 bytes), the tracked files of either repo, or the gitignored report
artifacts. Each grep ran with a positive control first — the searched files were confirmed
non-empty and a string known to be present was confirmed findable — because a grep over an empty
file passes identically whether or not a leak exists.

*One process note:* the first sweep reported false LEAKs. `git grep -l … | head && echo LEAK`
masks `git grep`'s exit code behind `head`'s, so the `&&` always fired. Caught by the control,
which reported "found" for a string that could not have been there. The corrected sweep drops
the pipe.

---

## Forwarded

- **BL-076** (new) — the compose defect F1 mitigates by convention. Batch with **BL-070**.
- **BL-069** — still armed and now fired on both providers. The ≥1-orphan close needs a planted
  resource, not a code change.
- **§Prereqs 3** — the planted AWS Elastic IP. Until it exists, the milestone's ≥1-orphan
  done-when cannot close; everything else in §t3's done-check is green.
- **`slug()` / `provider_slug()` convergence** — t2 deferred it to keep `compose` unedited, and
  named "the next time compose is legitimately edited" as the trigger. A4 *is* that edit, so the
  trigger technically fired. Deliberately not taken: §t3 permits the A4 lift and nothing else in
  that file, and converging would enlarge the diff the negative proof is read from. Re-attach the
  trigger to BL-070/BL-076, which will be in the file anyway.
- **`fail` does not fail the sprint** — noted above; sprint-wide, not cloudcost's to change.
- **The section agent re-infers purpose lines on every matrix regen**, so five unrelated
  cloudcost rows churned in wording this run. Curate via
  `docs/capability-matrix-overrides.json` if the churn ever matters.

## Real-bill end-to-end — DEFERRED, operator step

The cost/report half was run live this session and works: the AWS pipeline produced its own
report from the real bill, reviewable without the console, with the swept-region set stated. The
**≥1-orphan half is not closable here** and was not faked. Once the Elastic IP is planted, the
operator runs:

```
cd ~/sandbox/elixirws/aetheris
CLOUDCOST_PROVIDER=aws ./scripts/sprint.sh cloudcost
```

and the existing `[FAIL] orphan candidates: 0` line becomes `[OK] … (≥1 — milestone done-when)`
with no code change. That assertion is the done-when; it is already in place and already
watching.
