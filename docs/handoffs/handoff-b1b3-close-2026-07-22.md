# Handoff — b1–b3 small-ticket batch closed / next design session — 2026-07-22

Date: 2026-07-22 · From: claude-ui (b1–b3 batch design session, opened from
handoff-bl007-close-2026-07-20) · For: fresh claude-ui design session, same project.

Watermark at handoff: agents `main` `420b1ad` (manifest regen; push ordered at
handoff authoring — verify it reached origin), harness `main` `1ebe971`. Verify both
via relay as first move. Project knowledge exported 2026-07-22 (24-file bundle,
remove-all/upload-all; 23 manifest entries, all matching HEAD at export —
`drift_check --strict` 8 PASS / 0 WARN on the closing relay; the manifest is the
checkable invariant). Read both repos' CLAUDE.md learning sections **before your
first edit** — see "Standing rules that changed" for why that wording is new.

## State: the batch is CLOSED

Three tickets shipped, reviewed, merged, pushed, exported:
- **b1 — BL-029 + BL-004** (+ fork-label rider): Rig reads `runs.label` (596 runs
  had real labels displayed as run_ids); token totals in the Cost tooltip; forks
  inherit the parent's label verbatim or stay unlabelled (never synthesized); run
  detail header shows the run_id beside a real label.
- **b2 — BL-028**: fork reconstruction reads `"output"` then `"result"`, through
  `normalize_content/1` — message content is always a string (nil → `""`,
  non-binary → JSON-encoded).
- **b3 — BL-031**: `await_run` bounds on **inactivity** (`{status, max_event_seq}`
  pair), config `:await_inactivity_timeout_ms` default 300 000; paused runs exempt
  via `Aetheris.RunPause`, shared with Sweep **by construction**.

Reviews: `docs/reviews/bl-029-review.md`, `bl-028-review.md`, `bl-031-review.md`
(all rounds + addenda). Recover specifics from those and the implementation notes,
not from memory of this closed session.

## Facts the next session must not relearn

- **Real-provider fork continuation has never worked** (BL-039): `fork.ex` emits a
  `"tool"` role Anthropic rejects (HTTP 400 at the first call), and relabeling
  cannot fix it — assistant `tool_use` turns are never reconstructed (contract §4,
  now annotated). Three reproductions, two parents, 100% failure. Stub forks
  "complete" **vacuously**: `encode_config` strips `stub_responses`, so every stub
  fork runs an empty queue. No fork on any provider has ever had a meaningful
  continuation. Both runbooks say so.
- There is **no `"paused"` run status** — `runs.status` holds only
  running/done/failed/cancelled. A pause is last-event `:agent_waiting` + an
  unexpired `waiting` checkpoint (`Aetheris.RunPause`, the single definition).
- Event types: canonical literal list is `Event.known_types/0`; `Store` derives its
  deserialization map from it (a bare `String.to_existing_atom` crashed boot when a
  refactor removed the only literal — the coincidence class, see promotions).
  `Trajectory.File` still holds its own copy → BL-040, which has a **live**
  instance: `:run_started` accepted by File's map, absent from the `@type` union,
  emitted by nothing.
- `RunSummary.label` is `COALESCE(runs.label, run_id)` — consumers needing
  real-vs-fallback re-derive by string comparison until BL-037 makes it nullable
  (sequenced before BL-024's lineage view).
- **BL-034's mechanism is now demonstrated**: the export prompt's Step 5 appends a
  drift baseline to manifest-tracked `current-state-2026-06.md` *after* Step 2
  writes the manifest — making the prompt's own "zero WARN" done-check
  unsatisfiable if followed literally (fired in production at `628f15f`; avoided
  this export by scope omission). Loose ends owned by BL-034's fix ticket: the
  2026-07-22 baseline was **not appended**, and the row is **not yet annotated**
  with this evidence (annotating would have re-staled the export — the trap
  generalized; evidence lives in the export/promotion notes meanwhile). Do BL-034
  **before the next export**.

## Standing rules that changed (§7 promotion, both CLAUDE.mds — commits `1ebe971` / `c2729ac`)

Harness: **Vacuous-exercise rewritten → Silent-wrong-answer** (a well-formed value
where a gap exists asserts, not reports — ask what green would look like if broken);
**Adjacent-case / load-bearing-coincidence added** (a fix's blast radius is one case
wider than its frame; a removed coincidence breaks code the diff never touched);
**Reviewer-claims-verified rewritten** to cover suggested mechanisms (a finding
binds by its invariant, not its sketch — five sketch failures this batch, all
one mechanism: vocabulary matched, family unread). Agents: **gate rule** gained the
cross-repo done-check clause (a one-repo gate silently passes sibling omissions);
**Repos/P8 rule amended**: *packet-producing* sessions (not just milestone),
*before the first edit* (not "at session start") — because BL-031 ran three packets
without ever opening the harness CLAUDE.md under the old wording, re-breaking
Complete-output (`tail -3`) while its session had never read the rule. The
instruction without its incident did not carry; that is why this paragraph carries
the incident. Draft/adjudication/review at
`docs/reviews/bl-batch-2026-07-section7-*` + `-promotion-review.md`.

**Freshness gate, worked example**: the session that edited both CLAUDE.mds refused
to run the manifest regen it was handed, citing the rule it had itself written —
"the rule's value is that it doesn't get relitigated per-case by the session that
wants the exception." Any session predating `1ebe971`/`c2729ac` is stale by
construction.

## Packet norms now standing (bind future tickets; encoded in b3's prompt, proven in b1–b3)

Every section inlined verbatim; red-first evidence for fixes (demonstrate the
defect before the cure); gates that go red mid-round are reported, never silently
repaired; cross-repo claims verified in each repo they're about; complete output or
a stated truncation (the `tail -3` casualty).

## Dispositions on record — do not reopen

- BL-026/BL-027 parked on trigger (first verify of a multi-agent/orb trajectory).
  BL-027's row now carries an evidence annotation: `record_tool_error/6` makes the
  crash reachable on **any** trajectory with a tool error — reachability widened,
  trigger unchanged.
- BL-033 no-code-change-now. **Do not conflate with BL-040**: BL-033 is the
  RunConfig *mode* union; BL-040 is the *event-type* triplication. Different unions
  (the conflation was itself a recorded sketch-failure instance).
- §1f flake: one unattributed full-suite failure, ~13 clean runs since. Escalation
  trigger: a **second** unattributed failure → row + seed-preserving chase, timing
  tests first.
- Source-line formatting of older learning entries: normalization declined,
  standing answer — opportunistic only.
- Fixture `agents/fixture_unlabelled_fork.exs`: reusable unlabelled+forkable run.

## Next work candidates (no commitment made)

**BL-034 first** is the cheap high-leverage pick (S; before any export; absorbs the
demonstrated evidence + baseline loose end into its fix). Then per suggested order:
BL-025 (verify effect containment — the carry with external blast radius) → BL-038
(15b) → **BL-039** (15c; M, docs-first; must build atop BL-028's landed state; its
fix needs a test path where a fork *actually continues* — no more vacuous green) →
BL-030 → BL-032 → BL-037 → BL-024 → BL-040. Or **BL-008** milestone planning
(docs-first; weng + activegraph briefs in project knowledge). Issue backfill
(#TBD, now BL-024–BL-040) remains optional housekeeping.

## Open human calls carried

None pending at close. Loose ends (owned, not open): BL-034's two (above); the
optional export-notes commit if not yet taken; `420b1ad` push if the relay shows it
still ahead.

## Session hygiene (unchanged, plus the sharpenings)

Fresh claude-code session per ticket; full restart after any CLAUDE.md change (two
changed this batch); both learning sections **before the first edit** of any
packet-producing session; pushes held for the human; every gate at every boundary;
recover from repos and review files, not from memory of this closed session.
