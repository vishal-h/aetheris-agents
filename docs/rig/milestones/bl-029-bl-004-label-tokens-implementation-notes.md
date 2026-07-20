# BL-029 + BL-004 — Rig run label + per-run token totals

**Ticket:** b1 (BL-029 + BL-004, batched — same artifact boundary, per the backlog
sequencing table `docs/backlog-2026-06.md:1463,1468`).
**Repo:** `aetheris-agents/` · **Touches:** `rig/src-tauri/src/commands/harness.rs`,
`rig/src/hooks/types.ts`, `rig/src/components/modules/harness/RunList.tsx`,
`rig/src/components/modules/harness/TrajectoryView.tsx`, `docs/rig/specs.md` §4,
`docs/rig/runbook.md`, `docs/backlog-2026-06.md`.
**Citations verified at:** c374db2 (agents) / 7e77951 (harness).

---

## What shipped

**BL-029.** Both harness queries now read the `runs.label` column instead of
`json_extract(config_json, '$.label')`, keeping the `COALESCE(..., run_id)` fallback
for genuinely unlabelled runs.

**BL-004.** `RunSummary` gained `total_input_tokens` / `total_output_tokens`, two
correlated subqueries mirroring `total_cost_usd` exactly. Surfaced in the Cost cell's
`title` tooltip — the runs table stays at 8 columns.

**Rider.** The t4 fork invoke now passes `label`, inheriting the parent's verbatim.

---

## The bug, measured

Run against the live `AETHERIS_DB_PATH` before the fix:

```
total_runs  labelled  unlabelled  label_in_config_json
878         596       282         0
```

596 runs carry a real label; **zero** carry one in `config_json`. So the old
`json_extract` returned NULL for all 878 rows and the `COALESCE` always took the
fallback — Rig showed the run_id for every run, including the 596 that were properly
named. This is why it read as "labels aren't set" rather than as a bug. After the
fix those 596 show their real labels (`Docbuilder Orchestrator`,
`Docbuilder Context Builder`, …) and the other 282 still show run_id.

---

## Design decisions

**Token columns appended, not inserted.** The ticket flagged that adding SELECT
columns shifts `row.get(N)` indices. Appending both after `total_cost_usd` leaves
indices 0–10 untouched and adds only 11/12. A mid-list insert would have shifted
every subsequent index — the churn is avoidable, so it was avoided. Full sweep of all
`row.get` in the file confirmed post-edit (`harness_get_events` and `harness_get_run`
mappings unchanged).

**No `COALESCE` on the token subqueries.** NULL stays NULL, so stub/Ollama and
pre-instrumentation runs stay distinguishable from a genuine zero — the
`json_extract IS NOT NULL` rule in `rig/CLAUDE.md`. Cross-checked one run's totals
against `usage.rs`'s differently-shaped aggregation (`IS NOT NULL` filter rather than
`CASE`): both return 57591 input tokens for `docbuilder-orch-iDGIIQ`.

**`harness_get_run` stays unqualified.** That query is `FROM runs` with no alias, so
the fix is `COALESCE(label, run_id)`, not `r.label`. Deliberately not "harmonised"
with the list query's aliasing — that would have been an unrequested rewrite of a
query the ticket scoped to one line.

**Tooltip over a 9th column.** The ticket asked for the tooltip if feasible and impl
notes if not. It was feasible: the plain `title` attribute is the established idiom in
this exact file (`:141` truncated label, `:146` stalled badge). `tokenTooltip` returns
`undefined` — not `''` — when both totals are null, so React omits the attribute and
no blank tooltip appears on stub runs.

**`formatTokens` copied locally, matching `toLocaleString()`.** The plan sketched a
`12.3K` abbreviation; the existing helper (`TrajectoryView.tsx:60`) uses
`n.toLocaleString()`, so the local copy matches the repo idiom instead. See the
deferred-findings section for why it is a copy.

---

## The fork rider, and the trap inside it

Resolved per the designer's direction: **inherit the parent's label verbatim, or pass
nothing.** No synthesis, no `(fork)`, no `@ step N` suffix. An unlabelled fork is
correct-and-legible; a synthesized label is neither.

Threading cost was within budget: `run: RunSummary | null` is in scope at
`TrajectoryView` (`:213`), and `canFork` is true only on the file-backed path
(`:302`) where `run` is present — one optional prop through one layer. So the rider
did *not* degrade to omit-entirely.

**Two ways `label` is not a real label**, both of which had to degrade to an
unlabelled fork rather than to a synthesized one:

1. **The COALESCE trap.** After this very fix, `RunSummary.label` is
   `COALESCE(runs.label, run_id)` — so for an unlabelled parent, `label` *is* the
   run_id string. Inheriting it verbatim would write a run_id into the child's label:
   the synthesized-label outcome arriving by another door, and one that BL-029's own
   fix creates.
2. **The empty-string trap.** `RunList.tsx` `handleForked` synthesizes a placeholder
   `RunSummary` with `label: ''` for the just-forked child (so the UI can jump to its
   trajectory before the next Refresh). Forking *that* child before refreshing would
   have passed `Some("")` to Rust — an empty label, not `None`.

Guard covers both: `run && run.label && run.label !== run.run_id ? run.label : undefined`.

The second trap was found by the type-checker, not by inspection: widening
`RunSummary` broke the synthetic literal at `RunList.tsx:483`, which is what surfaced
the `label: ''` placeholder. Worth recording — the BL-004 half of this batch is what
exposed a latent edge in the BL-029 half.

---

## Divergences from ticket text

Noted rather than silently followed, per the CLAUDE.md rule on ticket text that
quotes repo state.

1. **specs §3 → §4.** Ticket and backlog BL-004 both say "specs §3". §3 is
   *Trajectory File Schema*; the Tauri command shapes are §4 (`specs.md:146`), which
   is also what `drift_check.py:194` parses. Edited §4. The backlog's own "Update
   specs §3" line is stale and is the likely source of the ticket's wording.
2. **RunList.tsx path.** Ticket says `rig/src/components/RunList.tsx`; the file is
   `rig/src/components/modules/harness/RunList.tsx`.
3. **The fork hook already accepted `label`.** `useFork.ts:25` is
   `fork(runId, step, label?)` and already documented that omitting it maps to
   `Option::None`. Only the call site omitted it, so the rider was a one-argument
   change plus the guard — not new plumbing.
4. **Phantom field in the block being edited.** `specs.md` §4 documented `RunDetail`
   with an `events: Vec<EventRow>` field the real struct has never had. Corrected
   here — leaving a known-false line inside the exact block being edited was the worse
   option — and the blind spot that hid it is filed as BL-036.

---

## Deferred findings — filed, not left as prose

Per the BL-007 promoted rule (a deferred finding gets a backlog row in the same round
it is deferred; prose has no executor):

- **BL-035** — extract `formatCost`/`formatTokens` to `src/lib/format.ts`.
  `rig/CLAUDE.md` sets the trigger at a *fourth* site. This ticket added the third
  `formatTokens` copy — at the threshold, not past it — and extracting would have
  touched `TrajectoryView.tsx`, `UsageView.tsx`, and `useRunDiff.ts`, none of them in
  the Touches list. Row records the signature divergence between the copies.
- **BL-036** — field-level drift checking for specs §4 command structs. `drift_check`
  compares command *names* only, which is how the phantom `RunDetail.events` field
  survived indefinitely.

Both added to the Suggested-order table (rows 21, 22).

---

## On new unit tests

None added, and that is the convention holding rather than a gap.

t3's resolution (`bl-007-t3-implementation-notes.md:24`) is: extract the pure logic,
unit-test the pure part, do not test the IO wrapper. This ticket introduces no new
pure Rust logic — the changes are SQL string edits and two `row.get` additions inside
the IO wrappers, and the SQL is an inline string literal with nothing to factor out.
Inventing a helper solely to have something to test would be the tail wagging the dog.

The frontend has no test infrastructure at all (no vitest/jest, zero `*.test.*` under
`rig/src`), so `tokenTooltip` and the fork-label guard are covered by `tsc -b` +
`eslint` + the manual checks. `tokenTooltip` and the guard are both pure and would be
the natural first frontend unit tests if that infrastructure ever lands.

The SQL itself *was* verified directly against the live DB rather than left to the
manual GUI pass — see the evidence section in the packet.

---

## Doc sync

- `specs.md` §4 — `RunSummary.label` and `RunDetail.label` provenance comments now
  name `COALESCE(runs.label, run_id)` instead of the wrong `from config_json.label`;
  two token fields added with the NULL contract stated; phantom `events` field removed.
- `runbook.md` — "Run list tab → What you see" updated. It listed neither Cost (which
  predates this ticket) nor tokens, so both landed together, plus a note that a
  pre-BL-029 conclusion of "labelling is broken" was a display bug worth retrying, and
  the fork-inherits-or-omits behaviour. Per methodology §6 the runbook line lands in
  this commit, not later — labels becoming real and tokens becoming visible are
  operator-visible changes.
- `drift_check.py --strict` — 8 PASS / 0 FAIL / 0 WARN / 7 INFO. The strict-exempt
  project_knowledge staleness WARN did **not** fire at check time (the manifest
  matched HEAD); it is expected to re-appear on the next run now that these doc edits
  are committed, which is the normal re-stale cycle, not a regression.

---

## Open items

- The manual GUI pass (labelled run displays its label; fork of a labelled run
  inherits it; fork of an *unlabelled* run stays unlabelled; tooltip on hover) needs
  an operator with the app running. The SQL underneath each is verified; what is
  unverified is the render path. The unlabelled-parent fork is the case worth not
  skipping — it is the one that exercises the COALESCE guard.
