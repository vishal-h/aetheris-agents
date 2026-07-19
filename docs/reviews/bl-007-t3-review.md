# Review — BL-007 t3 — round 1

Reviewed against: README §t3 as landed at `cb3574f` (incl. done-check
correction), t2 conventions (fork_from identity, :record mode), specs §4
conventions, methodology §§1–6, standing CLAUDE.md rules.
Reviewer note: orchestrate.rs was not relayed to me — findings 2 and 6 below
are questions to repo state, not assertions about it.

## Findings

1. [blocking] Implementation notes are cited
   (`bl-007-t3-implementation-notes.md`) but not included in the packet.
   They are a required packet section — the packet-integrity rule exists
   precisely so review doesn't proceed against a summary of a deliverable.
   Fix: paste the notes verbatim into the disposition round. I specifically
   need to see recorded there: (a) the trajectory.rs shared-helper refactor
   (finding 6), (b) the synchronous-command decision and its relation to
   the orchestrate pattern (finding 2), (c) the real-provider avoidance in
   the e2e (good call — but it's a verification-scope decision, so it's
   recorded, not just narrated), (d) the label finding, (e) the watermark
   line (`cb3574f`/`eef174f`).

2. [question] §t3's scope names "the orchestrate.rs spawn pattern," but
   `fork_run` uses blocking `Command::output()` and is documented
   **Synchronous**. Two sub-questions, answers determine escalation:
   (a) Does `orchestrate_start` spawn-and-return (background + poll/cancel,
   as `orchestrate_cancel`'s existence suggests)? If so, t3 diverged from
   the ticket's named pattern — that's ratifiable, but it's a deviation
   needing a record and the human's sign-off, not a doc footnote.
   (b) Where does Rig execute non-async Tauri commands? If sync commands run
   on the main thread, a real-provider fork (minutes) freezes the entire UI
   for its duration — which t4 inherits the moment it wires a button to
   this. If it's thread-pooled, the freeze concern drops to
   "UI can't show progress," which the specs note already covers.
   Answer with file:line evidence for (a) and the concrete dispatch fact
   for (b). Cited-means-read applies.

3. [question] Non-`done` terminal status is undefined. `parse_run_id`
   ignores `status`; `fork_run` errors only on nonzero exit. If the CLI
   exits 0 with `{"status":"failed","run_id":...}` (does it? — demonstrate,
   don't infer), `fork_run` reports success and t4 will surface a failed
   fork as a fresh run with no signal. Acceptable outcomes: error on
   non-done; or return run_id and document that status is the caller's to
   check. Pick one, demonstrate the CLI's actual exit-code behavior for a
   failing fork if cheaply constructible, and record it in specs §4 + notes.

4. [non-blocking] The label backlog rec (`harness.rs:82,196` → read
   `r.label`) lives only in packet prose. F4 precedent this milestone:
   a deferred finding gets a backlog row, not silence — add it to README
   §t5 carries (one line, with the file:line cites) in this round's doc
   edits. Note it also retroactively benefits non-fork runs, so frame it
   as a Rig defect row, not a fork feature row.

5. [non-blocking] specs §4 wording: "the post-t2 CLI's **replay**" — in a
   doc where Replay is a defined execution mode (LLM not called), calling a
   fork a replay is a terminology collision. One-word fix: "the post-t2
   CLI's fork" or "re-execution from step N."

6. [non-blocking] The trajectory.rs refactor (traj_path → aetheris_root,
   both now pub(crate)) is within the letter of dir-scoped Touches but
   repurposes a helper on the load/export path of an existing command, and
   the only gate covering it is `cargo build`. The transformation reads
   behavior-identical, but since fork.rs established an in-crate unit-test
   home, add one trivial test pinning traj_path's output shape
   (suffix `priv/runs/<id>/trajectory.json` under a set env var, or factor
   the pure join) so the shared helper's contract is asserted, not assumed.

## Positive findings (no action)

- Demonstration-not-citation, satisfied where it counts: the `--json` seam
  was executed against the real CLI, log-noise reality observed, and
  parse_run_id's last-line scan matches that observation rather than an
  assumption about clean stdout.
- The label finding is the named-open-item instruction working as designed:
  durable-but-unreadable is a better answer than either silent wiring or
  silent omission, and the one-line-per-site fix rec is actionable.
- Declining to run real-provider runs inside a verification step was
  correct scope hygiene.
- Sweep reported against the criterion, not "zero output" — the §t3
  correction is already earning its commit.

## Cross-ticket notes

- t4 inherits two facts from this round once findings 2–3 resolve: the
  invoke-side blocking semantics (button UX depends on it) and the
  non-done-status contract. Whichever way they resolve, the resolution
  belongs in README §t4's text before t4 starts — same doc-first carry as
  F3 last round. Flagging now so the round's doc edits can include it.
- Packet-integrity watch: t2 inlined notes, t3 referenced them. If a third
  packet arrives partial, that's a promotion candidate against the packet
  format itself ("a packet section referenced is a packet section absent").

---

## Dispositions (claude-code, round 1)

Verified against agents `bl-007-t3` (off `cb3574f`) + harness `eef174f` — fresh reads.

1. **[blocking] Notes not inlined — fixed.** The implementation notes are pasted
   verbatim into the disposition relay (and updated with the finding-2/3/6
   resolutions below). Packet-integrity restored.
2. **[question] Sync shape — answered; resolved to `async`, one deviation for
   sign-off.** (a) Yes — `orchestrate_start` spawns-and-returns (`orchestrate.rs:80`
   thread, `:107` `Ok(job_id)`); `fork_run` blocks. But the deviation is *forced*:
   the CLI reveals the run id only at completion (`await_run`), so there is no early
   id to return — and `fork_run` matches the other precedent, `tools_run_script`
   (`tools.rs:636`, a command wrapping a blocking `Command::output()`). (b) Tauri v2
   runs **sync commands on the main thread** (v2.tauri.app/develop/calling-rust,
   quoted in notes) → a sync `fork_run` would freeze the UI for a real-provider fork.
   **Resolution:** made `fork_run` `async` + `spawn_blocking` (off the UI thread,
   Tauri's recommended shape, matching `trajectory_export`/`f2_trigger_scan`). The
   residual — it still **blocks to completion** (invoke promise resolves only when the
   fork finishes; cannot spawn-and-return early) — is the forced deviation carried into
   README §t4 and **flagged for human ratification** (per the finding's "human's
   sign-off" instruction).
3. **[question] Non-`done` status — answered + hardened.** Demonstrated: `mix aetheris
   --json fork` exits 0 even on error (mix discards the CLI exit code), and `await_run`
   turns `failed`/`cancelled` into a *stderr* error (`run_helpers.ex:67-74`) — so a
   non-`done` fork produces **no** stdout run_id and `fork_run` already returned `Err`,
   never false success. Hardened: `fork_run` now surfaces the CLI's stderr in that
   `Err` (was generic). Recorded in specs §4 + notes. Chosen contract: **error on
   non-`done`** (never return an id for a failed fork).
4. **[non-blocking] Label backlog row — added.** README §t5 entry (g): the Rig
   label-read defect (`harness.rs:82,196` read `config_json.$.label`, stripped by
   `encode_config`; real value in `runs.label`), framed as a Rig defect benefiting all
   runs, with file:line cites.
5. **[non-blocking] "replay" wording — fixed.** specs §4 now reads "the post-t2 CLI's
   fork — re-execution from step N", removing the collision with the defined Replay mode.
6. **[non-blocking] `traj_path` contract — pinned.** Factored the pure joins
   (`root_from_db_path`, `traj_path_under`) and added two `trajectory.rs` unit tests
   (no env-var flakiness). `cargo test` now 11 passed.

**Cross-ticket carry (done this round):** README §t4 now carries the `fork_run`
contract t4 must build against — `async`, blocks-to-completion (needs a pending/progress
affordance, not instant), and non-`done` → `Err`.

**Open for the human (finding 2 sign-off):** ratify the `async` + blocks-to-completion
shape (the forced deviation from `orchestrate`'s spawn-and-return), or direct otherwise.

---

# Review — BL-007 t3 — round 2 (dispositions)

## Disposition verification

1. F1 — verified fixed. Notes inlined, complete, watermark line present,
   all five requested records (helper refactor, sync decision, e2e scope
   decision, label finding, watermark) present.
2. F2 — verified answered with evidence (`orchestrate.rs:80,:107`;
   `tools.rs:636`; Tauri v2 dispatch fact quoted). Code resolution
   (async + spawn_blocking) is correct and matches the cited in-repo
   precedents. Residual shape → human ratification, recommendation below.
3. F3 — verified answered + demonstrated. The removal of the exit-status
   branch is correct given the demonstration (mix always exits 0; every
   failure path ends in no-stdout-id → Err carrying stderr). Note for the
   record: parse_run_id accepts any run_id-bearing JSON without checking
   status — safe today because the demonstrated CLI contract routes all
   non-done outcomes to stderr, and specs §4 now documents that contract.
   If the CLI ever emits error JSON on stdout, this assumption breaks with
   it; the specs wording is the guard. No action.
4. F4 — verified. §t5 row (g) framed as a Rig defect with cites. Done.
5. F5 — verified. Collision removed. Done.
6. F6 — verified. Pure joins pinned by two tests, env-var flakiness
   avoided by factoring rather than setting. Done.

## New findings

7. [non-blocking] In-flight fork vs. app quit: fork_run's subprocess is
   parented to Rig; if Rig exits mid-fork, the mix process is orphaned or
   killed with the run mid-flight. The harness orphan sweep (observed in
   this round's own e2e stdout) mitigates the DB side, but the behavior is
   undesigned rather than decided. One line into README §t4's inherited-
   contract block ("quit-during-fork behavior is unspecified; sweep
   recovers the DB row") so t4 designs the affordance knowing it — or a
   backlog row if preferred. Doc edit only; no code action in t3.

## Round status

Zero blocking findings. Round closes pending two human acts (below).

## Cross-ticket notes

- The §t4 inherited-contract block is this milestone's doc-first carry
  mechanism working on the third consecutive occasion (F3 at t2, the
  done-check correction, now the fork_run contract). The mechanism is
  earning promotion consideration at §7 in its own right — as a positive
  pattern, not a defect class: "decisions that constrain ticket N+1 land
  in ticket N+1's README section before its session starts."

## Dispositions (claude-code, round 2)

- **F7 — done.** README §t4's inherited-contract block now carries the
  quit-during-fork line: the `mix` subprocess is parented to Rig, so a
  mid-fork quit orphans/kills the run; the harness orphan sweep recovers the
  DB row; the UX (warn-on-quit / detach) is t4's to design. Doc edit only,
  no t3 code change.
- **F3 record note — acknowledged.** `parse_run_id` intentionally does not
  gate on `status`; the safety rests on the CLI contract (all non-`done`
  outcomes → stderr), which specs §4 now documents as the guard. If the CLI
  ever emits error JSON on stdout, that specs wording is where the assumption
  is pinned. No code change.
- **Round 2 closed** — zero blocking. Proceeding to the two human acts:
  finding-2 ratification (received) and commit+push (structure below).
