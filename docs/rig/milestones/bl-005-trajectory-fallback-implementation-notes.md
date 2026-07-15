# BL-005 — TrajectoryView fallback for live runs — implementation notes

## What shipped

`TrajectoryView` no longer errors when `trajectory.json` is absent. On a
`trajectory_load` failure it rebuilds the same step-grouped view from the live
SQLite event stream (`harness_get_events`) plus `runs.config_json`
(`harness_get_run`), behind a banner naming the source. New pure module
`src/lib/reconstructTrajectory.ts` holds the parse/derive logic; the component
holds only orchestration.

## Design decisions

- **Fallback lives in the component, not `useTrajectory`.** The file hook stays
  a pure file loader. `TrajectoryView` calls `useRunEvents` + `useRunDetail`
  with the run_id **gated to `null` until the file load has failed**
  (`fileMissing ? runId : null`), so a completed run with a file never issues
  the extra DB queries — no perf regression on the common path. This also let me
  reuse the p2 polling hook wholesale rather than re-implementing live append.

- **Prop changed `runId` → `run: RunSummary | null`.** The banner varies by
  status, so the component needs the status. `RunSummary` also supplies
  provider / model / started_at / finished_at directly, so meta reconstruction
  only reaches into `config_json` for the fields the run row lacks
  (mode / max_steps / tools / prompts / sandbox_path / seed).

- **Polling: IN.** Free via the existing `useRunEvents(runId, { polling })`
  hook, which already stops on `run_complete`. Running runs append live; the
  banner shows the same pulsing dot the Events tab uses.

- **Export JSON hidden in reconstructed mode.** `trajectory_export` copies the
  file; there is none, so the button would only ever error. Gated behind a
  `showExport` prop (true only on the file path).

## Deviations from the ticket

- **Scope widened past "for a running run"** — per the ticket's own written
  recommendation. BL-003 swept 66 orphaned runs to `failed` with no
  `trajectory.json` either, so the fallback triggers on **any** `trajectory_load`
  failure. Banner varies: `live — reconstructed from events` (running) vs
  `trajectory file unavailable — reconstructed from events` (terminal). This was
  not materially more work — the widening is a single status-dependent banner
  string on one shared code path. Verified against real swept run `run_YchSWw`
  (`failed`, 3 events, no run directory).

- **Terminal banner reads "trajectory file unavailable", not the ticket's
  literal "no trajectory file"** (BL-005 review round 1, finding 2; adopted).
  The fallback fires on *any* load failure, which includes a completed run whose
  file is corrupt or a truncated `.tmp` — "no trajectory file" would be false
  there. "unavailable" is accurate for both absent and unreadable. The original
  `trajectory_load` error is `console.warn`'d once when the fallback engages
  (a `useEffect` keyed on `fileError`), so the interrupted-write signal the
  runbook documents is not lost behind the generic banner.

- **`config_json` is richer than specs §7's sketch.** It actually carries
  `system_prompt` / `user_prompt` (when `store_prompts: true`, the default), so
  the reconstructed meta populates the prompt panels rather than leaving them
  blank as the ticket allowed for. Falls back to `''` when absent
  (`store_prompts: false`). Only `overlay_changes` is genuinely unavailable
  pre-completion and is left `[]`.

- **No new Tauri command.** `harness_get_events` and `harness_get_run` already
  exist, so **specs §4 is unchanged** (the ticket anticipated this; a new
  command would have been a §4 touch). `drift_check` still counts 47 commands.

## Gotchas for later work

- **Branch-switch stale render.** `useTrajectory` does not null its `trajectory`
  on `runId` change — on a failed load it keeps the previously-selected run's
  value. The branch order therefore matters: `fileMissing` (reconstruct) is
  checked **before** `fileTrajectory` (file present), and `fileLoading` before
  both, so a failed load never renders the prior run's file data. If anyone
  reorders these, that latent stale-render returns.

- **Completion-while-viewing (ticket transition note).** A run that finishes
  while its reconstructed view is open does not crash and does **not**
  auto-switch to the file: polling stops (the pulse disappears), the complete
  events remain shown, and the banner text stays `live —` until the user
  reselects/reopens the run — at which point `useTrajectory` reloads, the file
  now exists, and the view flips to the file-backed path (no banner). This
  matches the ticket's "flips on next load/poll — no special handling required".
  The only cosmetic imperfection is the frozen `live —` banner on a
  just-completed run until reselect; deemed acceptable per the note.

- **`step_count`** in reconstructed meta is the count of distinct `step` indices
  seen so far (progress at read time), not a recorded final count — live runs
  have none.

## Verification

Rig has no test runner, so the reconstruction is guarded by a standalone Bun
script over committed real-harness fixtures:
`rig/scripts/verify-reconstruct-trajectory.ts` (fixtures under
`rig/scripts/fixtures/reconstruct/`). Run `bun run
rig/scripts/verify-reconstruct-trajectory.ts`. Test A is the byte-fidelity
property (58-event completed run: reconstructed-from-DB events equal the real
`trajectory.json` field-for-field) — the guard that a future TrajectoryView /
fork-UX (BL-007) refactor cannot silently break it. Added per review round 1
finding 1 (durable artifact, same principle as BL-009 finding 1).

## Out of scope / flagged

- **Pre-existing build blocker (not BL-005), fixed in a separate commit.**
  `bun run build` runs `tsc -b` over the whole project, which failed on
  `DocbuilderView.tsx:42` — an unused `const running` introduced by p9-t4
  (2026-06-24); `main` had been red on this for three weeks. Per review round 1
  (explicit out-of-Touches approval), the one-line dead-`const` deletion lands
  as its **own commit** citing p9-t4 as the origin — not folded into BL-005's
  diff. All three BL-005 files typecheck clean in isolation regardless.
