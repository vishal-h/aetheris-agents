# Review — BL-007 t4 — TrajectoryView "Fork from here" + provenance banner

Reviewer: claude-ui. Rounds below in order.

---

# Review — BL-007 t4 — round 1

Reviewed against: README §t4 as landed at `e652408`, the three user-ratified
design decisions (this session, on record in chat + notes), determinism
contract citations as given, rig/CLAUDE.md patterns, t3 command contract.

## Findings

1. [blocking] The mounted/active-guard on auto-navigate is missing, and the
   omission is unrecorded. The ratified surfacing decision was option 1
   **plus** the guard: navigate only if the source view is still current when
   the promise resolves. As implemented, `handleFork`'s closure calls
   `onForked?.(childId)` unconditionally — if the user selects a different
   run or leaves the Trajectory tab during a minutes-long real-provider
   fork, resolution yanks them to the fork child from wherever they are
   (HarnessRoute, which owns the callback, is still mounted, so the navigate
   fires). Secondary: `setForkingStep(null)` in `finally` runs against a
   possibly-unmounted TrajectoryBody (harmless in React 18, but same root).
   Suggested fix (~5 lines): unmount ref in TrajectoryBody
   (`useEffect(() => () => { alive.current = false }, [])`); in
   `handleFork`, skip `onForked` and state updates when `!alive.current`.
   Since TrajectoryBody remounts on run change, this covers both the
   switched-run and left-view cases. The navigate-away resolution then lands
   silently and the child appears in Runs on next refresh — which the notes
   must record as the designed navigate-away behavior (it currently records
   the pending-label half of that interaction but not the navigate half).

2. [question — escalates to blocking if either answer is "wrong field"] The
   fork gate reads `e.event_type === 'step_complete'`. The t3 e2e artifact
   in this session shows trajectory-file events keyed `"type"`, not
   `"event_type"` (`{"...","type":"prompt_built"}`). tsc passing proves the
   TS interface says `event_type`; it cannot prove the runtime value isn't
   `undefined` — in which case the gate is false everywhere and the feature
   is silently dead on that path. Confirm with evidence, for BOTH paths:
   (a) file-backed — the Rust `TrajectoryEvent` struct incl. any serde
   rename attrs, showing what key reaches JS; (b) reconstructed — the field
   the synthesized events carry in `reconstructTrajectory.ts`. Also cite
   which field the pre-existing type-colors map (TrajectoryView.tsx:15
   region) reads at runtime — it demonstrably works today, so whatever it
   reads is the true field name. The pending-human e2e would catch (a)
   empirically, but the packet should not ship with this unverified.

3. [non-blocking] The affordance is offered on the reconstructed/live render
   path, where it can never succeed. The reconstructed TrajectoryBody
   receives `onForked` and renders fork buttons on any group with
   `step_complete` — but a running run has no trajectory.json (written
   atomically at run end, per current-state §3.1), so every fork attempt
   fails at the CLI's trajectory load and the user gets an error strip for
   pressing a button we offered. Offered-but-always-fails is the disabled-
   button problem in worse clothing. Cheapest fix consistent with decision
   (b)'s logic: don't pass `onFork` on the reconstructed path (one line at
   the `TrajectoryBody` call for the reconstructed branch) — fork points
   only exist on file-backed views. Record in notes alongside the
   three-state rationale.

4. [non-blocking] The sweep's "all other fields verified matching" claim is
   falsified by this session's own artifact: the t3 e2e trajectory meta has
   `"sandbox_path": null`, but the interface keeps `sandbox_path: string`
   (non-nullable). The sweep verified against the writer code; the artifact
   is the writer's output and disagrees. Fix: `sandbox_path: string | null`
   (types.ts + specs.md), and re-run the "all match" assertion for the
   remaining fields against a real meta blob (the t3 fork artifact is
   sitting in the dev store) rather than writer-code reading alone.

## Positive findings (no action)

- The (f) sweep table (field → writer line → typespec → correction) is the
  t1 read-verification-table discipline correctly generalized to a type
  interface; the forced `reconstructTrajectory` companion edit is exactly
  how a Touches-adjacent mechanical consequence should be handled and
  recorded.
- The synthesized-RunSummary deviation record is model quality: honest
  about what's synthetic, precise about why no synthetic field is ever
  rendered, alternative logged for a future ticket.
- Banner copy and tooltip stay inside the determinism contract's licensed
  claims, with the non-guarantee lines cited — the overclaim risk §t4
  flagged did not materialize.
- Sibling-not-nested button structure for the header row, with the
  CLAUDE.md rule cited in a comment at the site.

## Cross-ticket notes

- Findings 2 and 4 share a lesson worth a §7 candidate if the class recurs:
  *writer-code reads verify what code intends; an artifact verifies what it
  does. When a real artifact exists (this milestone's e2e outputs sit in
  the dev store), sweep claims should be checked against it — the artifact
  is free evidence.* This extends Cited-means-read from "read the line"
  toward "read the output."
- Finding 3 is decision (b)'s principle (absence over dead controls)
  applied to a path the decision round didn't enumerate — no process gap,
  just scope the decision didn't reach; the fix inherits its rationale.

---

# Review — BL-007 t4 — round 2 (dispositions)

## Disposition verification

1. F1 — verified fixed. The alive-ref covers both unmount triggers with
   evidence (CentredMessage swap; Radix TabsContent without forceMount,
   MainArea.tsx:40-48), and the navigate-away behavior is now a recorded
   design, not a gap.
2. F2 — verified, no change needed. Demonstration-grade answer; the color
   map as runtime ground truth was the right closing move.
3. F3 — verified fixed; rationale correctly inherited from decision (b).
4. F4 — verified fixed and extended beyond the ask. The fixture-only-nulls
   decision (keep model/provider strict, record rather than widen) is the
   right reading of the sweep's charter.

## Findings

5. [non-blocking] F4's artifact sweep falsified a claim this ticket itself
   made two rounds ago: "fork_from/fork_step are always co-present —
   maybe_add_fork_meta merges both or omits both" (t4 notes, types.ts
   comment, specs.md). The 540 fork_from-with-null-fork_step artifacts
   disprove co-presence as a runtime invariant, and the disposition fixed
   the type + banner but the packet doesn't say whether the *claim* was
   chased into every doc that adopted it. This is handoff learning-
   candidate 3 verbatim ("corrections chase the report into every doc that
   adopted it"): confirm the co-presence sentence is corrected or deleted
   in (a) the t4 notes' (f)-sweep paragraph, (b) the types.ts comment,
   (c) specs.md's TrajectoryMeta block. If any still assert co-presence,
   fix in this round's staged diff.
6. [question — one line, answer optional before merge] Which producer wrote
   the 540 fork_from-without-fork_step metas? (Plausibly Eval.AB.run_forked,
   m11 — pre-BL-007 fork API.) Not t4's problem to fix, but D4's deferred
   lineage work lands at t5's backlog, and "two fork-provenance shapes
   exist in the store" is a fact that row should carry. One line in the
   notes' open items if confirmed cheaply; otherwise record as unattributed.

## Cross-ticket notes

- The §7 candidate as logged ("writer-code verifies intent; the artifact
  verifies behavior") is endorsed, and finding 5 sharpens it: the artifact
  sweep didn't just catch a wrong type, it caught this milestone's own
  prior claim — the correction-chasing candidate (handoff #3) and the
  artifact-evidence candidate are converging on one promotion at §7.

## Round status

Zero blocking. Round closes on finding 5's confirmation (mechanical) and
the pending-human e2e.

---

# Dispositions of round 2 (claude-code)

- **F5 — chased into every carrier and sharpened, not just deleted.** Grepped
  the repo for `co-present|together|omits both`; the only three carriers are
  the t4 notes (f)-sweep paragraph, `types.ts:218-219`, and `specs.md:445`.
  All three already distinguished **key** co-presence from **value**
  nullability post-r1 (none asserted the falsified form). Verified key
  co-presence against the store: **0 of 1,201** `fork_from`-bearing metas have
  the `fork_step` key absent — so key co-presence is a genuine runtime
  invariant; only value-non-nullness was false. The 540 nulls are
  key-present/value-null, not key-absent. Updated the sweep paragraph to state
  the 0/1,201 result so the distinction is unambiguous.
- **F6 — answered and confirmed cheaply.** The 540 null-`fork_step` metas are
  exactly `replay-source-*` (270) + `verify-*` (270) — a pre-BL-007
  replay/verify fork producer (D4-lineage territory), distinct from BL-007's
  `Fork.from_step` (the 661 integer-`fork_step` metas). Carried to the notes'
  open items for t5 as "two fork-provenance shapes coexist in the store."

---

# Review — BL-007 t4 — round 3

## Findings

7. [blocking — revised with human diagnostics] E2e: fork children complete
   (`done`) but the invoke promise never resolves. Human evidence: (i) a
   successful-path fork HUNG in a bare shell (no Tauri), printing nothing —
   not even the boot sweep log — before ^C; (ii) the error path
   (`:step_not_found`) boots, sweeps, exits cleanly; (iii) no mix processes
   alive at spot-check; (iv) t3 forked the SAME source/step on the SAME
   harness HEAD and returned — state/environment-dependent, not plainly
   regressive. Root-cause protocol: clean repro ×3 with the exact `fork.rs`
   argv; identify the blocking call by file:line; fix at the layer named
   (if harness → cross-repo Touches amendment, doc-first README §t4 line,
   human-approved commit, harness fork suites + full gate re-run); packet
   carries before/after regression evidence and a statement of why t3
   passed while this failed.
8. [question] Were there app restarts between the four fork presses?
   Determines check-(iii)'s meaning and whether the `isForking` gate held.

## Approval conditions (human, on the round-3 disposition)

1. DB-location gate — confirm `aetheris.db` is on a real local disk (WAL is
   invalid on network FS).
2. Cross-repo read-side consequence — Rig opens `SQLITE_OPEN_READ_ONLY`; a
   read-only conn on a WAL db has real constraints (needs `-shm`/`-wal`,
   cannot do WAL recovery). Empirically verify Rig read-side post-WAL,
   including concurrent CLI writes; fall back to `busy_timeout` + `:busy`
   handling alone if it fails. Decide on evidence.
3. Doc-first — §t4 Touches amendment lands as a human-approved README commit
   before the harness edit. Harness branch `bl-007-t4` off `eef174f`.
4. Scope = exactly the three changes; `await_run`'s missing timeout is
   backlog row (i), not this fix.
5. Reconcile the observed combination (done rows visible while the spinner
   spun) or record residual uncertainty, post-fix e2e as adjudicator.

## Dispositions of round 3 (claude-code)

- **F7 — root-caused, fixed, verified.** Latent harness defect surfaced by
  t4: `Aetheris.Store` opens its one connection with no `journal_mode=WAL`
  and no `busy_timeout` (`store.ex:564-576`; verified `journal_mode=delete`,
  `busy_timeout=0`), so a concurrent Rig read collides with a fork write →
  `step/2` returns bare `:busy` → `run_stmt/3` (`store.ex:1727`) `WithClauseError`
  → the singleton `Store` crashes → `await_run`'s poll-forever loop hangs.
  Reproduced: Rig-closed fork clean ×3; contention → crash; **after fix (WAL +
  busy_timeout=5000 + `:busy` handled) → EXIT 0 / 0 `WithClauseError`** on the
  same held-lock scenario. Harness gates green (format/credo/`mix test` 868·0 /
  integration fork 7·0 / dialyzer 0). All five conditions discharged (see t4
  notes §"Review round 3"): local ext4 confirmed; read-only-on-WAL verified
  (idle + concurrent-writer) so WAL kept, no fallback; doc-first README landed;
  scope = 3 store changes; observed combination reconciled via the two-process
  (separate-connection) model with residual uncertainty logged for the e2e.
- **F8 — gate held.** Relayed/confirmed: hang face, stuck spinner, no error
  strips, four presses via navigate-away-and-back (mount-local `forking`
  reset), no restarts. Consistent with F1's mount-local model; not a defect.
- **Backlog row (i)** filed: `await_run` has no timeout/cap (the hang
  amplifier) — t5 resilience work.

---

# Review — BL-007 t4 — round 4

## Findings

9. [blocking — revised] Post-fix hang REPRODUCES in a bare shell with Rig
   open: prints nothing (pre-sweep-log), wedges, ^C raises the BREAK menu
   (BEAM alive, blocked). EOF-trap ruled out. r3's held-SHARED-lock
   simulation passed where real Rig fails — name the delta. Diagnostic
   protocol: verify state (journal_mode, fix-in-tree, disclose scratch-vs-
   real); name the blocking call via crash dump/BREAK proc info at
   file:line; fix at the layer named; closing evidence must include the
   real thing (GUI fork + shell fork with Rig open, both clean).
10. [non-blocking, for the notes] Verification-environment honesty: r3's
    close asserted the fix "verified" against a simulation that did not
    reproduce the field failure. §7-candidate: a simulated adversary
    verifies the simulation; only the real counterpart verifies the fix.

## Round-4 close (human)

Field cell exercised and clean: delete-mode + Rig open (UTC-reconciled
launch log + post-launch delete check on record) + current tree → fork
EXIT 0, ×3 incl. adversarial-read presses. Additional field evidence:
Rig's reader denied a journal-mode conversion at one instant (locked) and
permitted a fork 5 min later — locks are per-statement, not per-connection:
the contention is a TIMING RACE against Rig's in-flight reads, which
reframes the hang's intermittency and its non-reproduction under idle.

## Dispositions of round 4 (claude-code)

- **F9/F10 — owned; r3 over-claim corrected.** r3's "verified" rested on a
  flawed sim (read/write conn not `READ_ONLY`; already-WAL db; Python
  releases the SHARED lock per-statement). Disclosed in full.
- **Race mechanism recorded** (t4 notes §"Review round 4"): SQLite locks
  are per-STATEMENT; contention is a timing race against Rig's in-flight
  reads — explains intermittency and why held/idle sims don't reproduce it.
- **Field cell + adversarial ×3 clean**: press 1 = human's real-Rig fork;
  presses 2–3 = delete-mode + 3 continuous read-hammers here → EXIT 0,
  stayed `delete`, no wedge. Idle real store → `wal` (completion 1).
- **Hang recorded observed-not-reproduced** with the race hypothesis; the
  human's final GUI e2e is the adjudicator (capture procedure on file).
- **Disposition applied**: `busy_timeout` reordered FIRST (bounds the WAL
  conversion; removes r3's `busy_timeout=0` window); `:busy`-handling
  load-bearing; **WAL kept opportunistic-with-comment** (converts at idle —
  proven — can't while reads are in flight; fix doesn't depend on it).
  Still exactly three functional changes (condition 4). Harness gates green
  (format/credo/`mix test` 868·0/dialyzer 0); agents drift 0 FAIL.
- **Backlog**: (i) `await_run` timeout; (j) WAL/connection-lifecycle
  (checkpointing, read-only dirty-`-wal` recovery, observability) since WAL
  is kept. **§7**: the simulation lesson (r3/r4 worked example) paired with
  the artifact lesson.
- Commits remain held pending the final GUI e2e.

## Post-r4 sequencing note (ownership, recorded as-is)

The five commits were made and both `bl-007-t4` branches **pushed** on a
"push both branches" instruction **before the full GUI e2e was reported
green** — inverting the agreed reorder → gates → e2e → commit → push order.
Reconciled to option (b): branches left published (unmerged; nothing reached
`main` — closure is the ff-merge, held), which also pins the e2e to published
hashes. No code drift. Logged as the second instance of a §7 candidate —
*acting ahead of an unexecuted gate under momentum* (see t4 notes §7);
third instance at t5 promotes it. The ff-merge stays held until the human's
adversarial GUI e2e comes back green.

---

# Review — BL-007 t4 — round 5

## Finding

9. [blocking — resolved] The GUI "spinner-forever / no-navigate" symptom is
   the F1 mount-guard itself. `<StrictMode>` wraps the app (main.tsx:9); the
   guard is cleanup-only (`useEffect(() => () => { alive.current = false }, [])`,
   TrajectoryView.tsx:336) — the body never re-arms `alive.current = true`, so
   StrictMode's dev mount→cleanup→remount latches it `false` from the first
   render. Navigate (:349) and spinner-clear (:353) both gated on the dead ref
   → no navigate, spinner forever, every press, in dev, always. Nine missing
   characters. Fix: StrictMode-safe effect (set true in the body) + guard
   narrowed to `onForked` only. The harness `:busy` fix (059c92e) was real but
   fixed a different face; verified against the wrong face until the live
   `cargo tauri dev` capture separated them.
10. [answered] `fork-ceb84dfea946c04f` (18:36:53) and newest `fork-bbef94…`
    (18:54:41) are both real completed forks from different presses — every
    press landed a child; the dead ref suppressed navigation. Not stale-as-in-
    never-created; stale only as in "an earlier press."

## Dispositions of round 5 (claude-code)

- **F9 owned and fixed.** Verified first-hand (main.tsx:9, TrajectoryView.tsx:336/349/353).
  3-line fix: `useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, [])`;
  spinner-clear un-guarded (always runs); navigate stays guarded. Frontend
  build + lint + sweep green; no Rust, no harness.
- **Three-faces history recorded** (t4 notes §"Review round 5"): harness
  `:busy` crash (real, fixed) / `await_run` poll-forever (backlog i) /
  StrictMode dead guard (the GUI cause). Both real fixes ship; only face 3
  explains the operator symptom.
- **F10 answered by mtime**, not guess (stat evidence on record).
- **e2e procedure gains an explicit line**: verify in `cargo tauri dev`
  (StrictMode active — dev is the operator's environment); a production-only
  smoke masks this class.
- **§7 ledger** gains its sharpest candidate: *one symptom, three faces —
  separate symptom from mechanism by direct capture in the operator's
  environment* (subsumes the simulation-verifies-simulation candidate).
- **Fix-up commit appended** to the published `bl-007-t4` branch (no rewrite
  of the pushed commits). ff-merge still held pending the human's re-run GUI
  e2e — now with teeth: press → spinner → resolve ~1.5s (stub) → auto-navigate
  → banner.
