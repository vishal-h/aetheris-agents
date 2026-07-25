# Review — BL-038: Run list — server-side search + honest window disclosure — round 1

**Verdict:** No blocking code findings — the implementation is correct, the load-bearing arm is genuinely non-vacuous (absent-first, mutation-checked both directions), check 2 + check 9 green, gates clean. One real correction (F1) lands on the *merge gate itself*, not the code. Both in-cycle additions endorsed; backlog edit endorsed; BL-058 well-filed.

---

**F1 — non-blocking, but fix before you run the GUI pass. The badge will read 500, not 250.**
The default limit is 500 (`DEFAULT_LIMIT`, `harness_list_runs` → `limit.unwrap_or(DEFAULT_LIMIT)`), and `useRunList({ search })` passes **no** limit, so the production run list windows at **500**. The `250` appears only in the live *test*, which hardcodes it. So GUI arm (b) / §1.5 / the packet summary all say "Showing 250 of 896"; the app will show **"Showing 500 of 896 runs."** `architecture.md` correctly documents default 500 — so the packet is internally inconsistent (doc 500 vs gate 250), and the doc is the right one. Two corrections:
- (i) Change the GUI-gate expected value to **500** before executing it — otherwise a correct 500 reads as a failure and false-fails the one open gate.
- (ii) Point the live test at `DEFAULT_LIMIT` rather than a literal 250, so it exercises the real production window. Its conclusion is unchanged (`demo-01` rank 879 > 500, still absent), but the number it prints should be the one operators actually see.

**F2 — endorse (Q1, escaping). Keep.** LIKE-metacharacter escaping binds by the ticket's own invariant, not its sketch: an unescaped `_`/`%` silently widens the result set — the exact silent-wrong-answer class BL-038 exists to remove, and `run_zS6XSQ` is a real id. This is invariant-serving, not gold-plating (per the "finding binds by invariant, not sketch" rule). `like_metacharacters_are_literal` covers it.

**F3 — endorse (Q1, transaction). Keep.** The ticket explicitly wanted "count cannot disagree with rows"; one command does *not* deliver that alone — two statements on one connection straddle a harness `INSERT`. `unchecked_transaction()` on the `READ_ONLY` connection pins one snapshot, rollback-on-drop is a no-op. Correct and minimal. Note for the record: the pre-existing `SQLITE_BUSY` exposure under rollback-journal mode is unchanged from the old single SELECT — not introduced here.

**F4 — endorse (Q2, two-form badge). Keep.** `statusFilter` is a pre-existing client-side narrowing; a single server-numbers badge over a client-filtered table would misdescribe the visible rows — the same class again. Minor coherence note, no action required: the empty-search/no-match text sources store size from `status.data.run_count` while the badge uses `total_count` — two sources for "store size" that can disagree if status is cached. It's prose-only and `total_count` is 0 in that branch, so `run_count` is the pragmatic pick. Acceptable as-is.

**F5 — endorse. The backlog edit (`c1dd116`) stays; not relay-only.** The implementation prompt cites `§BL-038` as its authority, and the row as filed offered client-side-filter/pagination that didn't ship. Leaving it makes the cited authority describe something other than what shipped — the standing "divergence is closed by editing the doc, never left silent" rule. Written-in with rationale is correct.

**F6 — accept the deferral (BL-058). No now-fix.** §5's `RunSummary` is 4 fields behind `types.ts` since BL-004, and §5 is unchecked. The 4-field correction is cheap, but §5 isn't drift-checked, so patching it now just re-drifts until the check exists — bundling the correction *with* the check in BL-058 is right. Confirming the deferral, not requesting a now-fix. BL-058 is BL-036's shape one section down; well-filed.

**F7 — coherence, no action.** BL-024's inheritance holds at the command level (`list_runs(conn, limit, search)` is the find-run-by-id primitive). DiffView's picker deliberately stays windowed with a comment citing BL-024 — correct scope boundary, not a gap.

---

**Merge gate:** still open on the manual GUI pass. Correct F1's number to 500 first, then run both arms (and the suggested status-filter arm). Nothing else blocks.

Two carried items unchanged and not BL-038's: **BL-048 CI dispatch** and **BL-057** (blocks un-skipping `OverlayAutonomousTest`).

---

**F1 disposition (claude-code):** In `rig/src-tauri/src/commands/harness.rs`, change the live arm `live_store_demo_01_absent_from_window_then_found_by_search` to call `list_runs(&conn, DEFAULT_LIMIT, …)` instead of the literal `250` (both call sites in that test), and correct the "N of M" GUI-pass number from `250` to `500` in `docs/rig/milestones/bl-038-run-list-search-implementation-notes.md` (the "Open / forwarded" GUI arms) — the production default is 500, and the demo-01-absent conclusion is unchanged since rank 879 > 500. No behaviour change; test-fidelity + gate-instruction correction only. Re-run `cargo test -- --ignored` (expect `window 500 of 896`) and `drift_check --strict` post-commit; then execute the GUI pass against the corrected 500.

---

## Round 1 disposition (claude-code, 2026-07-25)

| Finding | Disposition |
|---|---|
| F1 | **Applied** — `e4baddf`. Both live-arm call sites now take `DEFAULT_LIMIT`; the failure message interpolates it rather than naming a literal window. Live output is now `live: window 500 of 896 runs; search 'demo-01' → 1 match(es)`. The notes' GUI arms carry the expected `Showing 500 of 896 runs` explicitly, with the 250 provenance named. |
| F2, F3, F4, F5, F6, F7 | **Acknowledged**, no code change. |

**F1 correction, precisely.** The notes' "Open / forwarded" GUI arms carried *no* number at all —
which is how the wrong one reached the packet unchallenged: the gate instruction was written in
prose ("confirm the badge shows the truncation") and the number was supplied later, from the test
literal, at packet-writing time. The fix is therefore not a 250→500 substitution in the notes but
the addition of the explicit expected values (`Showing 500 of 896 runs`, and the filtered form
`Showing F of 500 loaded · 896 runs in store`), so the executable number lives in the committed
gate rather than being re-derived per packet. A numberless gate instruction is the same
silent-wrong-answer carrier one level up: it cannot be checked, so it cannot be wrong, so nothing
catches the number that fills it in.

**F4's two-sources note, recorded not fixed.** `status.data.run_count` and `total_count` are
independent reads of store size; in the no-match branch `total_count` is 0 by construction, so
`run_count` is the only usable source there. Left as-is per the review. If the pair ever needs to
agree in a branch where both are non-zero, that is a `harness_connection_status` / `RunListResult`
reconciliation, not a display fix.

**Re-run after F1** (post-commit `e4baddf`): `cargo test --lib` 18 passed / 0 failed / 1 ignored;
live arm `live: window 500 of 896 runs; search 'demo-01' → 1 match(es)`; `tsc -b`, `bun run build`,
`bun run lint` exit 0; `drift_check --strict` exit 0 — 8 PASS / 0 FAIL, three exempt
`project_knowledge` staleness WARNs, unchanged from the round-1 packet (`specs.md` `c0977c2`,
`architecture.md` `c0977c2`, `backlog-2026-06.md` `c1dd116`). The notes file is not manifest-tracked,
so `e4baddf` adds no fourth WARN.

**Merge gate: still open.** The manual GUI pass is the human's to execute, now against 500.
