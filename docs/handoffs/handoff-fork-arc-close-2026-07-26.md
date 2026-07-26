# Handoff — fork arc shipped (BL-039 → BL-030) + BL-038 / next: BL-032 (WAL-or-not) — 2026-07-26

Date: 2026-07-26 · From: claude-ui (design session, opened from
`handoff-containment-cluster-close-2026-07-25.md`) · For: a fresh claude-ui design session, same
project — **the BL-032 session, resuming the pre-arc mainline.**

> **Note added at commit (claude-code) — two cited artifacts do not resolve, three name the wrong
> repo.** Checked at commit time and flagged rather than silently corrected, per the precedent this
> handoff's predecessor set.
>
> 1. **`bl-038-review-packet.md` is not in either repo.** `docs/reviews/` holds
>    `bl-038-review.md` and nothing else matching `038`; `git log --all` finds no packet file. The
>    review itself is present. Either the packet was inlined into the review or it never landed as
>    a file — recover BL-038 detail from `bl-038-review.md` and the backlog row, and do not go
>    looking for a packet.
> 2. **BL-039's artifacts are split across both repos**, which the artifacts section as drafted did
>    not say. `bl-039-fork-continuation-scout.md`, `bl-039-review.md` and `bl-039-review-packet.md`
>    are in **agents** `docs/reviews/`; **`bl-039-contract-draft.md` (RATIFIED) is in the harness**,
>    `../aetheris/docs/reviews/`. Corrected inline below.
> 3. **`bl-048-closeout-review.md` is in the harness**, `../aetheris/docs/reviews/`, not agents.
>    Corrected inline in *Open human calls carried*.
> 4. **BL-030's milestone notes are not symmetric across the repos.** Agents has three
>    (`bl-030-early-return-fork-`, `bl-030-r1-completion-transition-`,
>    `bl-030-r2-source-seeded-selection-implementation-notes.md`); the harness has **one**
>    (`bl-030-implementation-notes.md`, covering r0 and amended for r1's F1), because r1 and r2 were
>    Rig-only. "under each repo's milestones/ … (r0/r1/r2)" reads as three per repo; it is 3 + 1.
>
> Everything else cited was verified present at commit: the BL-030 scout, review and all three
> packets; the BL-039 scout, review and packet; `bl-038-review.md`; both repos' BL-039/BL-030
> milestone notes; the predecessor handoff; commit `b1d9ccc`; and backlog rows BL-058, BL-060,
> BL-061, BL-062, BL-064, BL-065.

**Watermark at handoff:** harness `f79365a`, agents `c27dee4` — **both = `origin/main`, synced,
clean.** The only thing held is **this handoff commit itself**, unpushed per the standing rule;
push it and the two repos are level again. `drift_check --strict`: **0 FAIL, exit 0, 6 exempt
`project_knowledge` staleness WARNs** — `docs/rig/specs.md` (manifest `c39bf7e` / current
`b5e8eee`), `docs/rig/architecture.md` (`d82cf7e` / `c0977c2`), `docs/rig/runbook.md` (`d0690a6` /
`7d6013a`), `docs/backlog-2026-06.md` (`6a8a32e` / `c27dee4`), `docs/aetheris/runbook.md`
(`915d582` / `ae0c510`), `docs/aetheris/determinism-contract.md` (`dd12dbb` / `1ab24d8`) — all
named in the r1/r2 packets; they clear at the next export boundary, which is human-owned.
`hex.audit` is **expected-red on BL-060** (upstream bandit advisory), named not re-triaged.
**Verify via relay as your first move, and read both repos' `CLAUDE.md` learning sections before
your first edit.** Recover specifics from repos + review files, not from this handoff.

## What shipped this session (three tickets — the whole fork arc plus the run-list search)

**BL-038** (agents `b1d9ccc`) — Rig run list gets server-side search (`WHERE runs.label/run_id
LIKE`, metacharacters escaped, both reads in one deferred read-txn so the count can't disagree with
the rows) + honest "N of M" window disclosure. `harness_list_runs` now returns
`RunListResult {runs, total_count}`. Spawned **BL-058** (specs §5 TS interfaces unchecked by drift
+ already stale — BL-036 check-9's shape one section down). Review: `docs/reviews/bl-038-review.md`.

**BL-039** (harness `1ab24d8`, §4 ratified in `1ab24d8`) — Design A structured fork
reconstruction. An assistant tool-call turn rebuilds as a `tool_use` block paired with a user
`tool_result` block, synthesised per-step `tool_use_id`, built through
`Aetheris.Execution.CanonicalMessage` (extracted from `loop.ex` so the live loop and fork share one
definition). **Part C:** the CLI surfaces the fork's terminal error reason. Real-provider arm ran
against Anthropic (PASS; mutated → the field's byte-identical HTTP 400 `Unexpected role "tool"`).
Spawned **BL-060** (hex.audit), **BL-061** (Gemini `thought_signature` omitted from reconstruction —
§4-scoped, trigger = first fork of a Gemini tool run, confirm-before-record). Scout
`bl-039-fork-continuation-scout.md`, contract draft
`../aetheris/docs/reviews/bl-039-contract-draft.md` (RATIFIED — **harness repo**), review
`bl-039-review.md`.

**BL-030** (harness `f79365a`, agents `06b333e`) — early-return fork, three rounds. **r0:** harness
emits the `run_id` at fork-start (additive, blocking unchanged); Rig owns the piped subprocess
(`orchestrate.rs` pattern), returns at the first `run_id` line, drains both pipes and reaps;
`handleForked` sets `status:'running'` so BL-005 polling streams the child. **r1:** completion
transition — the in-place running→done reload is **status-gated (no retry)**, because the
`run_complete` event precedes the file write but the terminal status follows it. **r2:**
source-seeded selection — killed the synthesized post-fork summary (the Adjacent-case leak behind
"Invalid Date"); `handleForked` now seeds from the real `runs` row via `runSummaryFromDetail`. GUI
pass confirmed both tabs end-to-end. Spawned **BL-062, BL-064, BL-065**. Scout
`bl-030-fork-early-return-scout.md`; reviews r0/r1/r2.

## Facts the next session must not relearn

- **A harness-side early-return fork is impossible without the daemon** (deferred). The fork run is
  a Task in the CLI process's own supervision tree, so the CLI must keep blocking on `await_run` to
  keep it alive; **Rig owns the subprocess and returns early instead.** `orchestrate_start` does
  **not** emit a harness run id — it's a Rig-side owned-subprocess pattern. Don't send anyone
  looking for a harness early-return mechanism.
- **The run row exists by the time Rig has the forked id, by construction:** `start_run` →
  `Server.run/1` is a synchronous `GenServer.call` whose `handle_call(:run, …)` upserts the row
  (real `started_at`, `config_json`, `label`) before returning, and the fork-start emit happens
  after. That's why r2's source-seeding is race-free. `runs.config_json` carries
  `fork_from`/`fork_step` (`encode_config` strips only 5 fields).
- **Fork reconstruction is Design A canonical blocks with synthesised per-step `tool_use` ids.**
  Positional one-tool-per-step pairing is sound **only while the adapter keeps one `tool_use` per
  step** — §4 names the dependency, **BL-059** carries the reciprocal (its disposition (a) must move
  fork pairing to N-to-N in the same commit). §4 also scopes the Gemini `thought_signature`
  omission to **BL-061**.
- **BL-030's r1 reload is best-effort** and depends on `server.ex:680`/`:952` reporting `done` even
  on a failed write (**BL-065**). Don't "fix" BL-065 without updating the reload's degradation.
- **determinism-contract §4 D2 (`fork_run/3` ≡ CLI) untouched**; §4's *"the CLI and Rig entry points
  pass a label only (BL-030)"* is now a **dangling ref** — BL-030 didn't deliver overrides; BL-062
  repoints it under §8. **Re-verify any §4/§5 citation at HEAD before it's load-bearing.**

## Open human calls carried

- **BL-048 — CI dispatch, still pending (your move).** Trigger the sandbox job on `ubuntu-latest`
  (PR or `workflow_dispatch`), read the containment probe's verdict, branch: **capable** → closes as
  a CI job; **skips** → confirm the sprint runs on a schedule/capable runner before calling Part B
  done ("wired to a sprint nobody runs" is the rot it exists to kill —
  `../aetheris/docs/reviews/bl-048-closeout-review.md` obs #2, **harness repo**). Sub-decision: wire
  the residual-red `requires_worker` set in as expected-red-named, or hold. Steps are in the BL-048
  exchange this session.
- **BL-057 — product decision** (a `provider:"stub"` run that declares tools starts no worker yet
  reports `:done`): stay tool-inert / start a worker / reject the config. Blocks un-skipping
  `OverlayAutonomousTest`. Design-led (claude-ui frames the three options → scout the 6-test blast
  radius → you adjudicate). Not scheduled.
- **BL-064 needs its scope written by claude-ui before anyone picks it up.** It's an honest stub;
  the design seed is in this session's BL-030 thread (the instruction lands as a trailing user turn
  after the replayed prefix, which collides with the trailing `tool_result` turn → **merge into that
  turn's content, not a second user turn**; plus the fork-guarantee implication).

## Next work + sequencing

**BL-032 is next** — decide WAL-or-not, unblocked now that BL-030 settled the fork call pattern:
Rig holds a polling read connection through a fork's whole streaming life, which changes the
read-while-write contention profile BL-032 was parked on. Decision ticket (WAL made deterministic
via connection lifecycle, or opportunistic-WAL ratified permanent, with the three follow-ups:
`-wal` growth, dirty-`-wal` recovery under a read-only conn, observability). Likely wants a small
scout first: current live `journal_mode` behaviour, and whether fork-streaming actually stresses
the conversion.

The three new rows are slotted in `## Suggested order`: **BL-065 @ 15e** (record-path correctness
cluster with BL-039/BL-059), **BL-062 @ 16a** (unblocked by BL-030), **BL-064 @ 16b** (after
BL-062, shares its seam; not-startable-as-filed). BL-030 is ✔; the sweep this round also ticked
BL-028/BL-031, so the Order column now matches the sections.

**Sequencing note.** This session's Order-table sweep ticked **15 stale rows** (Done in their
sections but still ranked) — the queue was overstating by 15, not 2 — so the Order column now
matches the sections: **24 ✔, 19 sequence-ranked, 4 trigger-parked (`—`)**. Next in sequence is
BL-032; the three fork-arc spawns sit at 15e/16a/16b.

Then per the table: **BL-037** (before BL-024) → **BL-024** (design-led, compose with `caused_by`,
handle both fork-provenance shapes) → **BL-033** (trivial `:fork`-union deletion, after BL-024).
BL-035/BL-036 area and BL-058 ride the next frontend/drift cleanup.

## Parked / newly filed (recorded, not scheduled — full set in `backlog-2026-06.md`)

- **BL-058** — specs §5 TS interfaces unchecked + `RunSummary` stale since BL-004. Do with/after
  BL-036; decide §5's scope rule first.
- **BL-060** — `hex.audit` red on `bandit 1.11.1`/EEF-CVE-2026-65623; 1.12.3 exists and the
  constraint admits it — **confirm the fix is in the 1.12 line (read the changelog, not the version
  list)** before bumping. Expected-red-named until then.
- **BL-061** — Gemini `thought_signature` lost on fork; trigger = first Gemini tool-run fork;
  confirm-before-record (recording it is a schema change); done-when updates §4's Gemini scoping
  either way.
- **BL-062** — fork provider/model overrides (CLI `--provider`/`--model` + Rig picker + the §4 §8
  repoint). Low.
- **BL-064** — fork-with-instructions. Low, **STUB** — claude-ui owes the scope.
- **BL-065** — `server.ex:680`/`:952` discard the trajectory write result → a failed write reports
  `done` (Silent-wrong-answer); both call sites named; done-when exercises the gap case. Harness.

Still carried from prior arcs: **BL-054** (`requires_worker` flake slot), **BL-052** (drift check-9
ghost scope), **BL-046** (payload-key convention), **BL-045** (`mode: :verify` misnomer),
**BL-044** (`mix aetheris` exit codes), **BL-026** (verify vs orb trajectory), **BL-051**
(unreproduced flake). **BL-048/BL-057** open (above).

## §7 milestone-scan candidates (single-instance, not promoted — logged so a second sighting is countable)

- **Numberless-gate** (BL-038): a gate instruction with no assertable value — Silent-wrong-answer,
  gate-instruction carrier. Match-shape: *an instruction with no assertable value in it*, not the
  specific number.
- **`rm -f` no-op** (BL-030 closure): success and no-op indistinguishable by exit code under the
  suppression flag — Silent-wrong-answer, destructive-command carrier. Verify a removal with
  `test ! -e` / `git ls-files`, never the removal's own exit code.
- **Coincidence-in-contract-text** (BL-039): a load-bearing coincidence one clause from becoming
  normative — Adjacent-case/load-bearing-coincidence in a contract-text carrier, with the
  sharpening that a coincidence *written into the contract* is sanctioned, not merely undetected,
  so this carrier inverts the rule's usual remedy. A second contract-text instance is the argument
  to restate the class to cover documents.

## Standing rules (session hygiene — unchanged)

Fresh claude-code session per ticket; full restart after any `CLAUDE.md` change; **§8** governs
determinism-contract edits (contract-draft artifact + human-ratified exact wording, landed as a
review file not chat); **§7** governs `CLAUDE.md` promotions; every existing gate at every boundary
even off-territory, and a red gate gets a tracked ticket the day it's found; `drift --strict`
**post-commit** for manifest-tracked edits, naming the exempt `project_knowledge` WARNs rather than
chasing them; **pushes held for the human**; recover from repos + review files, not memory of a
closed session. **Rig has no frontend test runner (BL-017)**, so any Rig-frontend ticket's merge is
gated on a manual GUI pass.

## Review-file artifacts produced this session (recover from the repo)

**agents `docs/reviews/`:** `bl-038-review.md`; `bl-039-fork-continuation-scout.md`,
`bl-039-review.md`, `bl-039-review-packet.md`; `bl-030-fork-early-return-scout.md`,
`bl-030-review.md`, `bl-030-review-packet.md`, `bl-030-r1-review-packet.md`,
`bl-030-r2-review-packet.md`.

**harness `../aetheris/docs/reviews/`:** `bl-039-contract-draft.md` (RATIFIED).

**Milestone notes** — agents `docs/rig/milestones/`:
`bl-030-early-return-fork-implementation-notes.md`,
`bl-030-r1-completion-transition-implementation-notes.md`,
`bl-030-r2-source-seeded-selection-implementation-notes.md`. Harness
`../aetheris/docs/aetheris/milestones/`: `bl-030-implementation-notes.md`,
`bl-039-implementation-notes.md`.

**New backlog rows:** BL-058, BL-060, BL-061, BL-062, BL-064, BL-065.
