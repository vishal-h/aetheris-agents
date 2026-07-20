# BL-007 t5 — implementation notes: docs sync + boundary (Phase A)

**Ticket:** BL-007 t5 — docs sync + boundary (cross-repo), README §t5 as landed at `f3d5ef8`.
**Watermark:** agents `f3d5ef8`, harness `059c92e` (both main, both clean at session start).
Branches `bl-007-t5` cut off main in each repo. Anything cited below was fresh-read this
session unless marked otherwise.

**Phase split (operator decision).** This session is **Phase A: every edit**. Manifest
regeneration and the project-knowledge export are **Phase B, a separate session**, because
manifest hashes must be taken after the last edit lands. Nothing here touches the manifest.

---

## Deviations from §t5

| # | Deviation | Reason |
|---|---|---|
| D1 | `docs/project-knowledge-manifest.md` is in §t5 Touches but **not edited** | Phase B owns it; hashes must postdate the last edit |
| D2 | Done-check run **without** `--strict`; the `project_knowledge` staleness WARN **persists** | `--strict` is the Phase-B closeout gate; zero FAIL is the Phase-A bar |
| D3 | Item 6 (`b6fd983` provenance note) — **no edit made** | Already resolved; see below |
| D4 | `README.md` edited (milestone summary) though not in §t5 Touches | Required by methodology §7 step 4 and the operator's item 8 |
| D5 | §t5 prose names the current-state file `rig--current-state-2026-06.md` | That is its *export* name; the real path is `docs/rig/current-state-2026-06.md`, which the Touches list has right |
| D6 | Backlog row **(f) not filed** — recorded as already-resolved instead | See "Row (f) was already discharged at t4" |
| D7 | current-state edits extended beyond the §C text and the §3.1 `seed` row | Two adjacent claims in the same table were verifiably false; see "Scope extension" |
| D8 | New file `bl-007-t5-section7-scan.md` (not in Touches) | The §7 scan table is claude-ui's input; a packet-only table would not survive the session. Written as a doc so the ritual has a durable, citable source |

### D3 — the `b6fd983` provenance note was already closed

The pre-BL-007 handoff carried this for t5 and §t5 as landed omits it, so the instruction was
to check the t0/t1 record before adding anything. **It is resolved, in the t0 record**:
`bl-007-t0-implementation-notes.md:147-158`. That passage states `b6fd983` **is** t0's fifth
doc commit and fires the watermark, and the "Realized (loop closed)" paragraph records that
the watermark was **honored, not slid** — the next milestone-doc change went to a dedicated
branch `bl-007-t1-prep` (`1d48ff3`) cut off the t0 tip, rather than a sixth commit on t0's
branch. That answers the open question in
`docs/handoffs/handoff-bl007-t2-design-2026-07-18.md:57` verbatim ("was it t0's fifth doc
commit pre-cut?"). **No line added to the t1 notes**; the Touches deviation the operator
pre-authorized was not needed.

### The t0 watermark rule, considered and cleared

t0 recorded that any *further* milestone-doc change must be a dedicated correction round with
its own branch, not another commit on t0's branch. This ticket edits `README.md` (the
milestone summary, D4). That is consistent: t5 is its own ticket on its own branch
`bl-007-t5`, which is exactly the "dedicated round" shape the watermark demanded. Recorded so
the boundary reads as considered rather than ignored.

---

## Work delivered

### 1. Runbook sweep — both entries were **missing**, and both were written

§t5 says this ticket "sweeps for completeness, it does not recover." The sweep found nothing
to complete: **both operator-visible entries were absent entirely**, so both were recovered
here. Verified at HEAD before writing:

- **Harness** (`../aetheris/docs/aetheris/runbook.md`) — `## Forking a run` held only the bare
  command, and `## CLI commands` repeated it. **Nothing** documented t2's change (`eef174f`).
- **Rig** (`docs/rig/runbook.md`) — `grep -i fork` returned **zero hits**. The t4 affordance
  was wholly undocumented.

What the harness entry now covers, verified against `lib/aetheris/cli/commands/fork.ex` and
`lib/aetheris/execution/fork.ex` at HEAD rather than from the t2 notes alone:

- `--step N` **replays to step N** via `Fork.from_step/3` (was: re-ran from the original
  prompt — the F1 bug). Called out as a changed semantic, because notes and scripts written
  against the old behaviour are now wrong.
- Forks run in **`:record`** mode; `Mode: record` in `inspect`/Rig is correct, not a lost fork.
  Identify by `meta.fork_from`, never mode or the `fork-` id prefix.
- **Seed carries** from source `meta["seed"]` unless overridden; absent → `nil`.
- `--name <label>`.
- **Only completed steps are forkable, and only tool-call steps complete** — a run that
  answered in one text response has no forkable step and returns `:step_not_found`. This is
  the operator-facing footgun, so it is stated as expected behaviour, not an error to debug.
- The command **blocks to completion** (`fork.ex:37` → `RunHelpers.await_run/1`), with the
  early-return variant pointed at BL-030.
- The four error strings, from source.

The Rig entry covers the three-state affordance (button only on completed steps; **absence**
is the signal, there is no disabled control), file-backed-only rendering, the minutes-long
in-flight block with no cancel, auto-navigation on resolve **and** the two caveats that
routinely read as bugs — navigating away suppresses the auto-navigate by design, and the
child's **row** does not appear in the Runs list until a manual Refresh — plus `Mode: record`
and the error strip.

**Defect-class instance, named for the §7 scan — not absorbed silently.** The runbook-update
rule (methodology §6, `../aetheris/docs/methodology/milestone-methodology.md:180-185`) puts
these entries in the `Touches` and done-check of the ticket that introduced them: the harness
entry belonged to **t2**, the Rig entry to **t4**. Neither was written there, and §t5's sweep
was explicitly not chartered to recover them. Two tickets, same rule, same milestone — a
≥2-ticket class by §7's own threshold. It is class (I) in the scan table relayed with this
packet. Note the rule's own failure mode is visible here: it fires on "new env var, startup
step, config key, or operational procedure," and *a changed semantic on an existing command*
(t2) does not obviously match any of those four nouns.

### 2. architecture.md — Execution Modes Fork row

Target is the **harness** repo (`../aetheris/docs/aetheris/architecture.md:445-456`), per §t5's
Touches. The agents-repo `docs/rig/architecture.md` has no fork content at all — worth stating
because "architecture.md" alone is ambiguous across these two repos.

The `Fork` row now carries a `†` footnote: fork is **provenance-carried via `fork_from`**, and
forked runs execute in **`:record` mode, not a `:fork` mode**. Verified at HEAD before editing,
per the ticket's instruction:

- `run_config.ex:115` — `@type mode :: :record | :replay | :verify | :explore | :fork`.
- `run_config.ex:82-83` (struct) / `:196-197` (typespec) — `fork_from` / `fork_step`.
- `agent/server.ex:717-721` — `maybe_add_fork_meta/2`, gating on `fork_from` being non-nil,
  **not** on mode; called at `:671`.
- No code path in `run_config.ex` sets or matches `:fork`; `mode` is behaviourally significant
  only for `:replay` / `:verify`.

The footnote also states the negative rule directly — consumers must not key off
`meta["mode"] == "fork"` or the `fork-` prefix — because that is the mistake the vestigial
union member invites.

**Union-removal disposition: RATIFIED — backlog row (k) / BL-033, no code change now.**
Deleting `:fork` is a harness code change outside the milestone that surfaced it. The
architecture footnote documents the discrepancy in the meantime, so the union does not read as
truth.

### 3. current-state corrections

`docs/rig/current-state-2026-06.md`:

- **§C** — struck the two false claims and dated the correction, following the in-place
  convention already used at `:492` (`- **Rig-side addressed:** …`). The claim that
  `Aetheris.fork_run` "is not visible in the harness public API from a search of
  `lib/aetheris.ex:111`" was **false when written**: `fork_run/3` is at `lib/aetheris.ex:73`
  and `Fork.from_step/3` has existed since 2026-05-17. The search missed the function and the
  report generalised the miss into an absence. The corrected bottom line records what BL-007
  actually built (only the Rig exposure was genuinely absent) and points at both runbooks.
- **§3.1 `seed` row** — was `null (always seen as null)`. Retyped `integer | null` with the
  provenance: the writer persists `config.seed` (`server.ex:668`, `:939`), and t2's CLI test
  demonstrates `4242` surviving the real writer **and** the fork round-trip. The original
  reflected the sample set, not the contract — stated as such, since that distinction is the
  reusable lesson.

**Scope extension (D7).** Two adjacent claims in the same table were verifiably false and were
corrected rather than left standing:

- The `mode` row listed only `record`/`replay`/`verify`; it now notes that a fork records as
  `"record"` and never `"fork"` — the same fact §t5 mandates for architecture.md, in the doc
  a Rig developer actually reads.
- The note under the table asserting **"`TrajectoryMeta` in `types.ts:193-207` does not
  declare `resumed`"** was resolved by t4's sweep (`6dd2d55`) and is now struck with its
  resolution.
- `fork_from` / `fork_step` rows added, carrying the key-co-presence vs. value-nullability
  distinction.

Justification for exceeding the letter of §t5: the file is in Touches, and this milestone's
own named learning candidate is that *corrections must chase the report into every doc that
adopted it*. Knowingly leaving false lines in a file being edited for falseness is that exact
defect. Recorded as a deviation rather than done quietly.

### 4. Backlog

`docs/backlog-2026-06.md`, following the file's own entry contract (`### BL-0NN — Title
(#issue)` → `**Size:** · **Priority:**` → prose → `**Done when:**` → `---`). Highest
pre-existing entry was BL-023 (#74).

**Ten rows filed as BL-024…BL-033 with `(#TBD)`** — operator-decided this session: BL numbers
assigned now so the entries are first-class and sortable, GitHub issue numbers backfilled
later (BL-007's issues are waived and pushes are held, so no issue exists to cite). Filed into
the existing topical sections, which is how BL-015–BL-023 were appended, not at the end.

| Row | BL | Subject | Section |
|---|---|---|---|
| (a) | BL-024 | D4 deferral — fork lineage queries | Harness |
| (b) | BL-025 | Verify effect-class / record-and-serve | Harness |
| (c) | BL-026 | Verify divergence report — no first diverging event | Harness |
| (d) | BL-027 | Verify `KeyError` on paired in-process tools | Harness |
| (e) | BL-028 | Fork reconstruction drops `"result"`-keyed tool output | Harness |
| (g) | BL-029 | Rig label-read defect | Rig |
| (h) | BL-030 | Early-return `fork_run` | Harness |
| (i) | BL-031 | `await_run` no timeout/cap | Harness |
| (j) | BL-032 | WAL connection-lifecycle follow-ups | Harness |
| (k) | BL-033 | Remove `:fork` from the mode union | Harness |

Citations were re-verified at HEAD, not copied from §t5 — which caught two drifts worth
recording:

- §t5 cites `store.ex:794` for the `runs.label` column; it is now **`:807`** (plus
  `ensure_runs_label_column/1` at `:989`). t4's store edit shifted the file.
- §t5 cites `harness.rs:82,196` for the label reads. Both are real, but `:82` is a multi-line
  `COALESCE` spanning `:82-84` — a single-line grep misses it and could have been written up
  as "only one site exists."

Also verified rather than assumed: `verifier.ex:133` is exactly the `Map.fetch!("output")`
hard fetch; `verifier.ex:176-186` `build_report` carries no first-divergence field;
`fork.ex:101-105` reads `Map.get(payload, "output", "")` — the **`""` default** is why a
`"result"`-keyed writer reconstructs silently-empty rather than failing, which is the part of
(e) that makes it dangerous and is now the row's emphasis.

**Rows (c)/(d) — disposition PARKED ON TRIGGER**, human-ratified 2026-07-19. Both rows are
worded so the trigger is the row's **activation condition**, in bold, with an explicit "do not
pick this up as ready work" — rather than as a standalone harness ticket. The trigger (first
`verify` against a multi-agent/orb trajectory) is also *why* (d) is currently unreachable: the
crashing tools are the orb ones, so no existing trajectory can hit it.

**Two-fork-provenance-shapes fact — attached to (a)/BL-024** as required, with its deferred
verification trigger: BL-007's `Fork.from_step` writes an **integer** `fork_step` (661 metas)
while the older `replay-source-*` / `verify-*` producers write `fork_from` with **null**
`fork_step` (540 metas of 1,201). Key always co-present; only the value varies. The row states
the trigger as the row's own condition: **when file-only runs become listable, the
null-`fork_step` banner render joins that ticket's e2e** — not a standalone e2e, since those
runs are unreachable in the runs list today.

Cross-links recorded where they change sequencing: (d)/BL-027 and (e)/BL-028 share one root
cause (two consumers assume `"output"`; a family of writers uses `"result"`), noted in both so
they are considered as one convention rather than two point patches; (h)/BL-030 and
(i)/BL-031 are paired in the ordering.

**Also landed** (operator-decided this session):

- Ten rows appended to `## Suggested order` (12–19 plus a `—` trigger row for BL-026/BL-027,
  following the file's existing `| — | BL-006 | Fires on its own trigger |` convention).
  BL-029 is paired with BL-004, which already says "batch with any harness.rs touch."
- The BL-007 entry's stale Rig sketch bullet struck in the 2026-07-17 style (it still read
  *"(Verified absent — this is the real work.)"*), and the blockquote's "Verified absent: the
  Rig side" line closed with what now exists.
- **No `**Status:** Done` added to the BL-007 entry** — the milestone summary is DRAFT pending
  human approval at close, so asserting Done would claim a close that has not happened.

### Row (f) was already discharged at t4 (D6)

§t5 enumerates (f) — the `TrajectoryMeta` type drift — as a backlog carry, to be corrected "at
whichever Rig ticket first touches `types.ts` or standalone." **t4 was that ticket.** It swept
the whole interface against the harness meta writer and landed the corrections in `6dd2d55`;
verified at HEAD in `rig/src/hooks/types.ts:196-219` — `seed: number | null`, `sandbox_path:
string | null`, `resumed?`, `fork_from?`, `fork_step?: number | null`, each with a
writer-citing comment. So (f) is **closed, not deferred**, and filing it as an open backlog row
would have created a fake open item. Recorded here instead, and in the milestone summary.

### 5. weng cite fix

`../aetheris/docs/aetheris/research/weng-harness-2026-07.md:208` cited
`activegraph-log-is-agent-2026-**06**.md`; the file is `-07`. Fixed. Before editing, the other
three sibling cites in the same list (`:201`, `:205`, `:212`) were checked against
`ls docs/aetheris/research/` — all resolve, so this is genuinely a one-line fix and not the
visible instance of a broader rot. The reciprocal cite
(`activegraph-log-is-agent-2026-07.md:240`) was already correct.

---

## Done-check

Per D2, run without `--strict` (Phase A bar: zero FAIL). From `aetheris-agents/`:

```
$ python3 scripts/drift_check.py
Rig doc-drift checker — 8 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 48 commands checked: lib.rs / .rs files / specs.md §4
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
[WARN] project_knowledge: docs/rig/specs.md stale — manifest=fe34af4 current=6dd2d55

Summary: 7 PASS  0 FAIL  1 WARN  7 INFO
```
```
$ python3 scripts/drift_check.py >/dev/null 2>&1; echo $?
0
```

**Defect in this block's first version, recorded as a named instance (t5 review F3).** The
exit code was originally captured as `printf 'EXIT: %s' "$?"` at the end of a
`python3 … | sed …` pipeline, so `$?` was **`sed`'s** status, not `drift_check.py`'s. The
reported value (0) happened to be correct — confirmed by measuring the script directly, which
is the second block above — but the assertion was not measuring the thing it named. A
pipeline-tail `$?` is green whenever the last filter succeeds, so that form **cannot fail** on
the script's behalf: it is a check that passes without exercising what it checks.

This is the **Complete-output / measure-what-you-claim** class (K-adjacent in the scan table),
and it is the same shape as the m7 learning already in CLAUDE.md — *"A done-check that can pass
without exercising the thing it checks is worse than no check."* Recorded rather than quietly
corrected, because it occurred **in the done-check block of the ticket whose own scan table
lists that class**. Correct forms: `${PIPESTATUS[0]}`, or measure the script directly as above.

**0 FAIL — the Phase-A bar is met.** The single WARN is the expected `project_knowledge`
manifest-staleness one, and it **persists by design**: it is cleared only by Phase B's export,
which is the enforcement point per the CLAUDE.md strict-mode rule. It is `strict_exempt` in
`drift_check.py` (`:73-81`, `:629-635`), so it would not fail `--strict` either — deferring
`--strict` to Phase B is a sequencing choice about the *manifest regen*, not an avoidance of a
gate this session could not pass.

No code changed in either repo this session (docs only), so the Elixir/Rust/TS gate set is not
re-run; the harness and Rig gates were green at the t4 boundary (`059c92e` / `6dd2d55`).

---

## §7 scan input (prepared for claude-ui; not promoted here)

Per the sequencing rule, **no CLAUDE.md edits this session** — promotions land after the human
adjudicates claude-ui's draft, and trigger a session restart. This session supplies the *input*
only, in the review packet:

- The **t0 and t1 review files inlined verbatim** (authored pre-this-session; the reviewer has
  not seen them).
- A **finding-class scan table** across all five review files: class → tickets/rounds → already
  promoted? Written to `bl-007-t5-section7-scan.md` (D8) so it is durable and citable, and
  inlined in the packet. Eleven classes (A–K). **Six clear §7's ≥2-ticket bar** — A, B, C, D,
  F, I — of which five are unpromoted (A, B, D, F, I) and **C is already promoted**
  (corrected at review F2; see dispositions). Below the bar but notable: **E**, a single
  ticket here but *already promoted twice* and recurring as **blocking** anyway — the
  highest-signal row by §7's own test; **G/H**, strongly evidenced but recurring across
  *rounds* of t4 rather than across tickets; **J/K**, single-ticket and already promoted or
  adjacent.

**Framing note.** Methodology §7
(`../aetheris/docs/methodology/milestone-methodology.md:207-220`) specifies only the *input*
("the milestone's review files") and the ≥2-ticket threshold. It prescribes **no table
format** — the scan table is a structure built for this packet, not one §7 mandates. Recorded
so the packet is not read as following a format that does not exist.

Two observations handed over without promotion wording, both bearing on §7's own test ("the
same finding class should not appear as blocking in two consecutive milestones — if it does,
the promoted rule was too vague"):

1. **Class (E), packet integrity, is already promoted and recurred anyway.** Two m1 learnings
   cover it. It still arrived as t3 **F1 [blocking]**. That is precisely the signal §7 says to
   read as "the promoted rule was too vague," and it deserves the human's attention more than
   any unpromoted class here.
2. **Class (F), acting ahead of an unexecuted gate, has reached its own stated promotion
   threshold.** t4's notes said "third instance at t5 promotes it" and counted two instances.
   The t2 review's positive-findings section records a third, earlier one ("the sequencing slip
   against the session's own instruction"), so the count is met **within** the milestone,
   without needing a t5 instance. Flagged as a counting correction, not a promotion.

---

## Review round 1 — dispositions (all accepted; zero blocking)

**F1 [question] — "path, not a bare run id" was false. Fixed, and demonstrated.** The
reviewer's field artifacts were right and my runbook line was wrong. `extract_run_id/1`
(`../aetheris/lib/aetheris/cli/commands/run_helpers.ex:244-259`) does
`Path.basename(path, ".json")`, then takes the parent directory's name **only** when the
basename is `trajectory`; every other value is used as the run id verbatim. So a bare id
falls through and *becomes* the run id — both forms resolve to the same run.

Demonstrated rather than only re-cited:

```
$ mix aetheris fork definitely-not-a-real-run-id --step 0
Error: could not read trajectory for run definitely-not-a-real-run-id: :not_found

$ mix aetheris fork --step 0
Error: expected a path to a trajectory file
```

The bare id is accepted **as an id** — the failure is a missing trajectory, not a rejected
argument shape. `expected a path to a trajectory file` fires only when there is **no
positional argument at all** (`fork.ex:40-41`), so the CLI's own message is misleading; the
runbook now says so explicitly rather than repeating it. Runbook corrected: both forms shown
in the examples, the resolution rule stated with its citation, and the error list rewritten
with the actual message strings.

**Root cause, named honestly:** I wrote that line from the `@moduledoc` usage string
(`fork.ex:3`, `aetheris fork <trajectory.json> --step N`) without opening
`extract_run_id/1` — a usage string is a *planning-style* artifact, describing intended
shape rather than implemented behaviour. This is **class C**, committed in the same session
whose scan table lists class C, and while writing the runbook entry recovered under class I.

**F2 [question] — class C's "already promoted?" column was wrong. Corrected.** The entry
exists at HEAD: `../aetheris/CLAUDE.md:530-532`, "Cited-means-read (author side)"
(`Source: BL-021, BL-022`), including *"Grep proving the absence of X is not evidence for the
presence of Y"* — and its BL-022 paragraph is itself an absence claim about `fork_run`
asserted from planning documents, i.e. BL-007's founding error. The reviewer's mirror was
accurate and current.

Scan-table row C corrected to **"YES — substantially promoted already,"** and a new
observation 4 sorts each of this milestone's C instances against the promoted rule. The
sorting supports the reviewer's read: the two instances the promoted rule does **not** cover
(the t2 project-knowledge-mirror citation, and the `store.ex:794`→`:807` drift) are both
cases of a claim that *was* verified and later decayed — which is **class D**, not C. **C's
residual folds into D**, as the reviewer proposed.

**Structural fact surfaced while confirming this** (recorded in scan observation 4): the
Cited-means-read entry lives in the **harness** repo's CLAUDE.md. `aetheris-agents/CLAUDE.md`
has no such entry — verified by grep at HEAD. Milestone sessions run with `aetheris-agents/`
as the working directory, so the harness rule was **not in this session's loaded context**
while its own class was being violated (F1). Whether promoted rules need duplicating or
cross-referencing across the two repos is a question about the promotion mechanism, handed to
the human with the scan.

**F3 [non-blocking] — EXIT-capture defect folded into the notes. Done.** The done-check
section above now carries the named instance and a directly-measured exit block, replacing
the pipeline-tail `$?`. Disclosed in chat originally; it belongs in the record.

**F4 [non-blocking] — lesson trimmed out of the reference doc. Done.** current-state §C's
closing paragraph reduced to a one-clause provenance note pointing at the §7 scan file, which
is where the lesson belongs. The correction itself is unchanged.

---

## §7 adjudication (round 2 close)

The human delegated adjudication with *"go by claude-ai recommendation; let me know if
human feedback is required."* The four unrelayed wordings (P3–P6) were requested and
supplied. **P1–P5 and P7 landed; P6, P8 and the summary approval remain open for the
human** — see "What actually landed, and what is held".

| Item | Class | Adjudication |
|---|---|---|
| **P1** | E — packet integrity | **ACCEPT — LANDED.** Already-promoted class that recurred as blocking; a rewrite of the m1 pair, not a third rule |
| **P2** | F — acting ahead of an unexecuted gate | **ACCEPT — LANDED.** Three instances across two tickets; threshold met on the existing record |
| **P3** | A — deferred finding gets a backlog row | **ACCEPT — LANDED.** Wording relayed on request |
| **P4** | B — decisions constraining ticket N+1 | **ACCEPT — LANDED.** Wording relayed on request |
| **P5** | D — verified claims decay | **ACCEPT — LANDED.** Wording relayed; Source line carries t5's two decayed-citation instances per the C-residual fold |
| ~~C~~ | Cited-means-read | **WITHDRAWN** by the reviewer; exists at HEAD. Residual absorbed by P5. No action |
| **P6** | G+H — bar exception | **RATIFIED 2026-07-20 — LANDED.** Human ratified the bar exception with its date; claude-ui's wording relayed as a paste (third attempt) and landed verbatim. Bar exception visible in the entry body, not only here |
| **P7** | methodology §6 + §7 amendment | **ACCEPT — LANDED** in the harness methodology doc, including the second §7-input clause from observation 3 |
| **P8** | reachability mechanism | **RATIFIED option (c) 2026-07-20 — LANDED.** One standing line in each repo's CLAUDE.md; no rule duplicated, no rule rehomed |
| **P9** | E applied to the §7 pipeline | **LANDED with P6.** New transport rule: promotion wording travels as a review-file artifact, not chat. Filed by claude-ui in the same round the gap recurred |
| Summary | milestone summary | **APPROVED 2026-07-20** as it stood at the t5 round-2 state, no edits requested. DRAFT marker removed |

**P6 reasoning (recorded for the human's decision; NOT acted on).**
The recommendation is to promote **H** (*one symptom, several mechanisms — separate symptom from mechanism by direct
capture in the operator's own environment*), which t4's own notes record as subsuming G.
The exception is explicit: H recurred across three **rounds of a single ticket**, not across
two tickets, so it does **not** meet §7's stated bar. Promoting anyway is justified because
§7's bar is a filter against noise, and H is the opposite of noise — a complete worked
example that cost this milestone three review rounds and produced a real fix mistaken for
closure of a symptom it did not cause. Recording the exception matters as much as the
promotion: the bar is being consciously overridden on evidence quality, not quietly
ignored, so the precedent is auditable rather than erosive.

**P8 reasoning.** Option (c) over (a) and (b). (a) duplicates rules into both files and
invites exactly the copy-divergence this project spends its drift apparatus preventing.
(b) centralises correctly but depends on a session following a reference it has no reason
to prioritise. (c) puts the cost once at session start, changes no rule's home, and creates
no second copy to drift.

### What actually landed, and what is held

The four missing wordings (P3–P6) were relayed on request. **P1–P5 + P7 landed** in the
promotion commit. **P6 and P8 are held**, per claude-ui's own rider: they arrive only with
the human's explicit ratification, and the relay carried the wordings and riders but **not**
those adjudications. P6's entry text demands *"explicit human ratification, [date]"* — a
placeholder only the human can fill, and inventing it would be the exact failure P2 names.
The summary approval is likewise still open, so the summary stays **DRAFT**.

Note the diagnosis embedded in the gate itself (claude-ui's, and it is correct): P3–P6
existed only in chat, never in a relayed artifact. That is **class E's mechanism —
referenced, not inlined — landing on the reviewer's own deliverable.** It is recorded in the
promotion commit message.

**Placement mechanics (claude-code's call, recorded here as instructed).** P1–P5 landed in
**`aetheris-agents/CLAUDE.md` only**, under a new `## Learning — BL-007` section. They were
*not* duplicated into the harness CLAUDE.md, because duplication is P8 **option (a)** — the
option P8 exists to reject, on the grounds that two copies drift. Landing them in both repos
now would pre-empt the mechanism decision by silently implementing its worst branch. When P8
is ratified, option (c) adds one standing line to each repo's CLAUDE.md and requires no
duplication at all. Until then, these rules are reachable from the repo where milestone
sessions actually run — which is the status quo the reachability finding describes, now
consciously chosen rather than accidental.

P7 is **not** a CLAUDE.md change and so is P8-independent: it amended
`../aetheris/docs/methodology/milestone-methodology.md`, where the methodology doc lives —
§6's trigger list gains "changes the observable semantics of an existing command, flag, or UI
affordance," and §7 step 1 gains the second-input clause from observation 3.

### The gate that stopped the promotion commit (round 1 of this exchange)

**Four of the eight promotion wordings were never relayed to this session.** P1 arrived
verbatim and P2's is inferable from its one-line gist. **P3, P4, P5 and P6 are described
only as "unchanged" from an earlier claude-ui draft that was not included in any message
here** — the packet instruction for t5 was explicitly *"do NOT draft promotion wording —
that's claude-ui's deliverable."*

Composing substitute wording from the scan-table class definitions is entirely possible,
and it is precisely what the class being promoted as **P2** forbids: *no action past a gate
until that gate has run and its result is on the record.* The gate here is claude-ui's
authored wording. Reconstructing it would put five standing instructions — rules that shape
every future session in both repos — into CLAUDE.md on text this session invented while
claiming to land text that was adjudicated elsewhere.

So the promotion commit is **held**, and the hold is itself an instance of the discipline
being promoted rather than an obstacle to it. Phase A is committed and complete; the
promotion commit needs either the four relayed wordings or explicit authorisation to
compose them.

### How the gate closed (2026-07-20, post-restart session)

The hold held twice more before it cleared, which is why the transport rule exists.

1. **Restart session, round 1.** The close-out instruction said P6's wording was "per the
   wording in the t5 review record." It was not there — `bl-007-t5-review.md` was read in
   full (135 lines) and carries only F1–F4 and the round-2 dispositions. The substance
   survived in four committed places (`bl-007-t4-implementation-notes.md:294-305` is the
   fullest), but claude-ui's *authored entry prose* had never reached an artifact. Offered
   three routes — assemble from the record, relay the paste, or decline P6 — and held.
2. **Route chosen: relay the paste**, on the ground that assembling from the record would
   be action past an unrun gate, which is P2. The gate here is claude-ui's authored
   wording, and P2 does not exempt the rule-writing itself.
3. **Third relay attempt succeeded** — pasted verbatim, with the bar-exception clause in
   the entry body and the `[date]` placeholder as the only field left to fill.

The human's own framing on accepting the correction: the text "has existed only in chat
through two relay attempts now." That is the whole case for the transport rule, and it is
why claude-ui filed the §7 promotion draft into `docs/reviews/bl-007-t5-review.md` in the
same commit — the milestone retroactively satisfies the rule it just wrote.

**Style note, flagged rather than normalised (per the pre-check offered before landing).**
The two new entries are relayed as markdown list items with an inline `Source:` sentence;
P1–P5 are unbulleted paragraphs followed by a backticked `` `Source:` `` line. The text was
landed **verbatim**, since "verbatim" was the instruction and the divergence is cosmetic.
Normalising the six entries to one form is available as a follow-up if wanted; it is not
done here because silently restyling relayed wording is the failure mode this whole
exchange existed to avoid.

---

## Open items / carries

- **Phase B (separate session):** manifest regen including this doc, the determinism contract,
  and the brief; the six-file project-knowledge reconciliation; `drift_check.py --strict` at
  exit 0 as the closeout gate. The `project_knowledge` WARN above is the marker for it.
- ~~**Milestone summary is DRAFT**~~ — **closed 2026-07-20**: approved as-is, DRAFT marker
  removed from the README.
- **BL-024…BL-034 carry `(#TBD)`** — GitHub issue numbers to backfill when issues are cut.
- **Commit and push held** for the human, per the milestone's standing discipline.

---

# Phase B — manifest regen + export (final milestone act)

**Watermark:** agents `675a5c2`, harness `7e77951` (both main, clean). Branch
`bl-007-t5-phase-b` off agents main. **No harness edits** — the manifest lives in the
agents repo and no harness file needed an export-name copy refreshed.

## Ordering, which turned out to be the whole ticket

The manifest records the commit at which each exported file *last changed*. So every
edit to a manifest-tracked file must land **before** the manifest is written, or the row
is born stale. Three of this session's four edits touch tracked files, so the commit
order was forced:

1. `d89641f` — the rider (`CLAUDE.md`, tracked).
2. `<this commit>` — BL-034 row (`docs/backlog-2026-06.md`, tracked) + these notes
   (untracked by the manifest).
3. `<manifest commit>` — the regen, last, recording (1) and (2)'s hashes.

Doing the regen first and the rider second would have produced a manifest that fails its
own check on the commit that wrote it.

## Deviations

| # | Deviation | Reason |
|---|---|---|
| B1 | Drift-baseline append to `current-state-2026-06.md` (BL-002 prompt's closing constraint) **not done** | It is the self-staling step BL-034 documents; doing it after the regen re-stales the row, and the Phase B step list does not call for it. Filed, not silently skipped |
| B2 | New backlog row BL-034 filed, though Phase B's step list is regen + export only | P3 — a deferred finding gets a backlog row in the same round it is deferred. Prose in these notes would file nothing |
| B3 | Stale `last changed` dates corrected beyond the stale-hash set | `methodology--triad-loop.md` read `2026-07-15`; the commit's actual date is `2026-06-19`. The column was carrying export dates, not commit dates, for at least one row |

## What the regen found beyond the nine

The Phase A relay named nine stale files. At Phase B's HEAD there were **ten** — the
harness `CLAUDE.md` joined the set when the P8 line landed at `7e77951`, after the count
was taken. Recorded because it is the milestone's own class-D shape in miniature: a
verified count decayed between the verification and its reuse, one commit later.

## Export set and the reconciliation

24 manifest rows (23 checked + the self-referencing manifest row). **3 added** per §t5
D6's export clause: `rig--bl-007-milestone.md`, `aetheris--determinism-contract.md`,
`aetheris--activegraph-brief.md`. **None dropped.**

Inclusion rule, written into the manifest itself rather than left implicit: milestone
*working artifacts* (reviews, implementation notes, scan files) are not exported;
milestone *specifications* that later work is written against are. That is what admits
`rig--protocol.md` and the BL-007 README while excluding `bl-007-t5-section7-scan.md`
and the six t*-notes/review files.

**The six-file reconciliation is the part the tooling cannot help with.** Five research
briefs plus `rig--architecture.md` are listed in the manifest but absent from the live
project knowledge. Their hashes match git, so the check reports them green — this is
exactly the manifest-blind direction the manifest header has warned about since BL-022,
now observed live. Four of the six are unchanged since the last export and so would look
like "nothing to re-upload" to anyone reading the diff rather than the reconciliation.
They must be uploaded regardless. Carried into the export table in the packet.

## Done-check

`python3 scripts/drift_check.py --strict` — **8 PASS, 0 FAIL, 0 WARN, 7 INFO**, exit `0`
measured directly (`>/dev/null 2>&1; echo $?`, not a pipeline tail — the t5 F3 defect).
`project_knowledge: 23 manifest entries all match git HEAD`. The staleness WARN class that
marked Phase B as outstanding is now clear, which is the closeout gate §t5 named.

Docs-only in both repos, so the Elixir/Rust/TS gate set is not re-run; green at the t4
boundary (`059c92e` / `6dd2d55`).

## Open after this

- **Upload is human-owned.** The manifest now asserts an export at `d89641f` / `7e77951`.
  Until the files are actually uploaded, the manifest over-describes project knowledge —
  the blind direction. The export table in the packet is the upload list.
- **BL-024…BL-034 carry `(#TBD)`.**
- **BL-034** — fix the BL-002 prompt's step order before the next export.
