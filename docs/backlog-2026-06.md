# Backlog — 2026-06

Distilled from the reality-check / drift-apparatus work of 2026-06-11.
All file references verified against code as of `docs/rig/current-state-2026-06.md`
(plus subsequent commits: stale-run/cost `88705f1`/`0eddf20`, drift checker
`66566b6` + `bd2c3d8` and follow-ups).

Sizes: **S** < half a day · **M** a day or two · **L** milestone-sized (gets its
own `docs/rig/milestones/` directory and issue docs before implementation).

GitHub issues: #42–#50 on vishal-h/aetheris-agents.

---

## Housekeeping (do first, near-zero effort)

### BL-001 — Capture clean drift baseline (#42)
**Size:** S · **Priority:** now

Every drift_check output recorded so far predates at least one parser fix
(paren-depth, payload `?` marker, `_evaluate_payload_fields` extraction).
There is no recorded genuinely-clean run.

- Run `python3 scripts/drift_check.py` with `AETHERIS_DB_PATH` set.
- Expected: 7 PASS, 0 FAIL, 0 WARN; INFOs only for event types with zero
  DB rows (`observation`, `run_cancelled`, …). The phantom
  `runs.finished_at` and `llm_responded.stop_reason` INFOs must be gone.
- Append the summary line to `docs/rig/current-state-2026-06.md` as
  "Drift baseline 2026-06-XX: …".

**Done when:** baseline recorded; any unexpected finding triaged.

---

### BL-002 — Refresh Claude project knowledge files (all three scopes) (#43)
**Size:** S · **Priority:** now

The Claude.ai project still carries the 2026-05-31 snapshot (superseded
handoff, pre-fix specs/architecture/runbook). This staleness is what
triggered the entire reality-check exercise. The refresh must cover all
three scopes, not just Rig:

**Rig** (replaces current stale set):
- `docs/rig/specs.md`, `docs/rig/architecture.md`, `docs/rig/runbook.md`,
  `docs/rig/milestones/p3/protocol.md`, `docs/rig/current-state-2026-06.md`
- `rig/CLAUDE.md` if conversations will touch Rig implementation
  (it is the authoritative Claude Code context for that subtree)

**aetheris-agents repo** (mostly new additions):
- Repo-root `CLAUDE.md` (refresh — now carries the doc-sync DoD)
- `docs/agent-creation-guide.md` (CLAUDE.md names it the authoritative
  agent-building reference; currently absent from project knowledge)
- `docs/capability-matrix.md` (what agents exist; orchestrator plans
  from it; needed for any "which agent does X" conversation)
- `docs/backlog-2026-06.md` (this file)

**aetheris (harness)** (currently zero representation):
- `aetheris/CLAUDE.md` if it exists (verify) — the harness-side Claude
  Code contract. Harness *source* facts (schema, event types, trajectory
  format) are deliberately NOT exported raw; they live verified in
  `current-state-2026-06.md` §7/§8/3.1 and the corrected specs.md.

**Drops:** the superseded handoff (banner already redirects) and
`docs/rig/README.md` (redundant with architecture + current-state).

**Manifest:** add `docs/project-knowledge-manifest.md` — one table:
file → commit hash at export. Refresh the manifest with every export.
This makes project-knowledge staleness mechanically detectable: the
next reality-check (or a future drift_check check) compares manifest
hashes against `git log -1 --format=%h -- <file>`.

- Convention going forward: refresh at the same boundaries the
  reality-check prompt runs at (milestone end / before handoff), and
  the manifest is part of the export, not optional.

**Done when:** project knowledge matches HEAD for all three scopes and
the manifest exists in-repo.

---

## Harness (aetheris/)

### BL-003 — Startup sweep for orphaned `running` runs (watchdog, cure side) (#44)
**Size:** M · **Priority:** high

Rig's "stalled?" marker (commit `0eddf20`) is the *detector*; the DB still
lies forever. Five orphaned `status='running'` rows from May 2026 exist in
`priv/aetheris.db` — use them as test fixtures, then let the sweep clean
them.

- On harness application start (and/or a `mix aetheris sweep` task), find
  runs where `status='running'` and the owning process is provably gone
  (no live GenServer for the run_id; last event older than a threshold).
- Mark them `failed`, emit a terminal event (`run_complete` with
  `reason: "orphaned"` or a new `run_orphaned` type — if a new type,
  update `event.ex` **and** specs §6, then run drift_check).
- Must not touch legitimately paused runs: a run whose latest event is
  `agent_waiting` with an unexpired `wait_condition` in `run_checkpoints`
  is paused, not dead (distinction already documented in runbook.md's
  stalled? entry).
- Write `finished_at` when sweeping (note: Rig's `TrajectoryMeta` treats
  missing `finished_at` as `""`).

**Done when:** the five May rows are swept on first run; a kill-9'd run is
swept on next harness start; a `wait_for_event` run survives the sweep;
drift_check passes.

---

### BL-004 — Per-run token totals in RunSummary (#45)
**Size:** S · **Priority:** low

Gap A residual ("Rig-side addressed" note in current-state doc): cost
landed in the run list; token totals did not.

- Same pattern as `total_cost_usd` in `harness.rs` `harness_list_runs`:
  correlated subquery `SUM(json_extract(payload_json,'$.input_tokens'))` /
  `'$.output_tokens'` over `type='llm_responded'` (tokens live ONLY in
  `llm_responded` — see specs §6 / report errata).
- `RunSummary` + `types.ts` + optional column or tooltip in `RunList.tsx`
  (the table is at 8 columns; consider folding tokens into the Cost
  cell's tooltip instead of a 9th column).
- Update specs §3; run drift_check.

**Done when:** token totals visible per run; NULL stays NULL for stub runs.

---

## Rig (aetheris-agents/rig/)

### BL-005 — TrajectoryView fallback for live runs (#46)
**Size:** S–M · **Priority:** medium

`trajectory.json` is written atomically at run end (`server.ex:673,944`
via `file.ex:37-38`) — the file does not exist while a run is live, so
TrajectoryView errors for `status='running'`.

- On `trajectory_load` failure for a running run, build the same view from
  `harness_get_events`: `EventRow.payload` is a JSON *string* (SQLite) vs
  the file's inlined object — parse per row; payloads are complete/
  untruncated in both stores, so fidelity is identical.
- Reuse the existing step-grouping; show a "live — reconstructed from
  events" banner; optionally reuse the p2 polling hook for live append.
- `meta` is unavailable pre-completion except via `runs.config_json` —
  render what's derivable, leave the rest blank.
- Update the runbook troubleshooting entry ("use the Events tab for live
  runs") to reflect the new behavior.

**Done when:** opening Trajectory on a running run shows events instead of
an error; completed runs unchanged.

---

### BL-006 — Document `stop_reason` when first observed (#47)
**Size:** S · **Priority:** tracked (event-triggered, not scheduled)

Confirmed absent from all current DB events (count = 0). The trigger is
mechanical: when drift_check emits
`INFO payload_fields: llm_responded.stop_reason in DB events but not
listed in specs.md §6`, add `stop_reason` to the §6 `llm_responded` row —
no `?` suffix needed, since by then it is observed. The `?` convention
exists for the general case; this ticket just records the trigger.

**Done when:** the INFO fires once and the field is promoted.

---

## Milestones (L — issue docs first, per repo convention)

### BL-007 — Replay / fork from step (Rig p9 candidate) (#48)
**Size:** L · **Priority:** medium

Feasibility confirmed (report Gap C + §3.1): trajectory files store full
untruncated prompts (`meta.system_prompt`/`user_prompt`) and complete
tool-call/tool-result payloads, so the conversation at step N is
mechanically reconstructable for completed runs — `run_checkpoints` is
only needed for live ones. No recording changes required.

Scope sketch for the milestone docs:
- Harness: `Aetheris.fork_run(run_id, step)` — rebuild messages up to
  step N from the trajectory, start a new run with provenance back-link
  (consider reusing `agent_trees` for the parent/child relation).
- Rig: one Tauri command + a "Fork from here" affordance on a step group
  in TrajectoryView.
- Decide divergence semantics up front: forked run gets a fresh run_id
  and records normally; original is never mutated.
- New event types or config fields → event.ex/specs §6 in the same
  commit (drift_check enforces).

**Done when:** milestone README + issue docs exist; implementation gated
on them, per the p3 pattern (docs → mock/real split if useful → UI).

---

### BL-008 — Skills auto-extraction + Rig skills view (compounding) (#49)
**Size:** L · **Priority:** medium-low

The "compounding/dreaming" idea from the Burr HN thread, grounded in what
exists: `skills` table schema-complete (`store.ex:817`), write path live
(`insert_skill`, `store.ex:132/619`), public API `Aetheris.extract_skill`
(`lib/aetheris.ex:111`) — but nothing calls it automatically and nothing
reads the table. Operationally empty.

Scope sketch:
- Harness: post-run hook (opt-in via RunConfig flag) that calls
  `extract_skill` for successful runs matching criteria (e.g. ≥N steps,
  `reason: agent_finished`); populate `source_run_ids_json`.
- Dedup/quality gate before insert (don't accumulate near-identical
  skills from repeated sprint runs).
- Rig: read-only Skills section under Harness (one command, one view —
  follow the harness.rs / RunList.tsx pattern per runbook's "Adding a
  new module" steps).
- Relation to `api/tenant/scripts/extract_skill_hints.py` (separate,
  domain-specific): document the distinction or unify deliberately.
- Schema/command/doc changes → drift_check in the same commit.

**Done when:** milestone docs exist; a normal sprint run leaves at least
one skill row behind and Rig can show it.

---

## Drift apparatus (optional hardening)

### BL-009 — Promote sprint drift_check to `--strict` (#50)
**Size:** S · **Priority:** after BL-001

Zero standing WARNs was achieved (f2/provenance command tables added).
Once the BL-001 baseline confirms it holds, flip the sprint.sh case to
`drift_check.py --strict` so new WARNs fail the sprint instead of
accumulating into the next alarm-fatigue cycle.

**Done when:** sprint runs `--strict` and passes; CLAUDE.md doc-sync
section mentions strict mode.

**Depends on:** BL-001 (#42)

---

## Suggested order

| Order | Ticket | Why first |
|-------|--------|-----------|
| 1 | BL-001, BL-002 | Minutes each; locks in everything just built |
| 2 | BL-003 | The five orphaned rows are sitting test fixtures; pairs with shipped stalled? marker |
| 3 | BL-005 | Small, immediate daily-use value |
| 4 | BL-009 | One-line change once baseline holds |
| 5 | BL-004 | Trivial, batch with any harness.rs touch |
| 6 | BL-007 → BL-008 | Milestone-sized; docs-first per repo convention |
| — | BL-006 | Fires on its own trigger |
