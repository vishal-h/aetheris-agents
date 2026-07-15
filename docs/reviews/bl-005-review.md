# Review — BL-005 — round 1

## Findings

1. **[blocking, trivially satisfied]** The A–D verification suite is not in the diff — the evidence is real but ephemeral. `reconstructTrajectory.ts` is pure logic that *will* be touched again (BL-007's "Fork from here" lands in TrajectoryView; the fork UX reads reconstructed views for live runs), and the byte-fidelity property is exactly what a future refactor silently breaks. Commit the verification script as a durable artifact — as a proper frontend test if Rig has any test infra, otherwise as a standalone script under `rig/` or `scripts/` with a one-line runbook or notes pointer. Same principle as BL-009 finding 1: durable tests beat one-off exercises. You already wrote it; this is a `git add`.

2. **[non-blocking]** The fallback triggers on *any* `trajectory_load` failure, which now masks the corrupt/truncated-file case: a completed run with a `.tmp` or damaged file renders the reconstructed view under a "no trajectory file" banner — data correct (better UX than the old error), but the banner is slightly false and the operator loses the interrupted-write signal the runbook still documents. Cheap fix: `console.warn(fileError)` in the fallback branch so the signal survives, and consider the banner reading "trajectory file unavailable" rather than "no trajectory file" — accurate for both absent and unreadable. Your call on the wording; the warn is worth doing.

3. **[question]** `detail.data?.config` — confirm `useRunDetail` returns `config_json` raw (string) rather than pre-parsed; `reconstructTrajectory` takes `configJson: string | null` and double-parsing or type mismatch here would fail quietly to `{}` and blank the meta panel. The tests suggest it's right; one sentence in the disposition confirms it.

4. **[reminder, closeout scope]** The manifest bookkeeping from last boundary rides this ticket's closeout: bump `aetheris-agents--CLAUDE.md` row to `a12a145`, regenerate the manifest in the closeout commit, and the export set for this boundary is **runbook + backlog + manifest** (CLAUDE.md content is already uploaded and current). Without this, the 1-WARN floor becomes permanent.

## Cross-ticket notes

- **Second standing-red gate in two tickets** (BL-016: `mix test` red on main; now: `tsc -b`/`bun run build` red since p9-t4, 2026-06-24 — three weeks unnoticed). The finding class isn't the individual failures; it's that **gates not run routinely rot silently**. Promotion candidate for the next CLAUDE.md batch: *"Every gate that exists (mix test, tsc/build, sprint, drift) is run at ticket boundaries even when the ticket doesn't touch its territory; a red gate gets a ticket the day it's found, never carried silently."* Source: BL-003/BL-016, BL-005. Holding until a human yes, per the methodology-doc gate precedent.
- The completion-while-viewing behavior matching the ticket's transition note verbatim — including honestly naming the frozen-banner cosmetic — is what implementation notes are for. No action; on record as the standard.

---

**On the build blocker — option (a), separate commit.** Rationale: (b) leaves a red gate standing, the exact alarm-fatigue lesson BL-016 just taught us; (c) pollutes BL-005's diff with an unrelated fix and muddies both commit messages. A one-line dead-`const` deletion doesn't warrant BL-ticket ceremony — a separate commit citing p9-t4 as the origin, pushed with this batch, is proportionate. This is me approving the out-of-Touches deviation explicitly, so it's on record rather than silent.

**Commit: yes**, message as proposed, on the branch — with finding 1 satisfied in the same commit (it's part of the ticket's deliverable, not a fix-up) and finding 2's warn if you take it. Then: round-2 packet with dispositions → human merges → closeout commits (backlog already in diff, manifest bump + regen last) → push → the three-file upload → board reads a true zero for the first time since BL-009.

---

# Review — BL-005 — round 2

## Findings

1. **[non-blocking]** All four round-1 dispositions verified against the diff: the verify script is committed with real fixtures and the byte-fidelity property intact, the banner reword rippled through all four surfaces including the test assertion, and the `reconstructedBanner` docstring carrying the *rationale* for "unavailable" is exactly right — the next person who tries to "simplify" the wording will read why it's there. The config no-double-parse answer cites line numbers; closed.

2. **[non-blocking, needs an entry]** The 31 lint errors are correctly out of scope, but per the deferred-not-silent rule they need a tracked backlog entry before this ticket closes — BL-017 (or next free), S–M, citing the plugin bump as origin and the 15-file spread. One deliberate decision belongs in that ticket's text: whether `react-hooks/set-state-in-effect` is a rule this codebase *adopts* (fix all 15 sites) or *rejects* (configure it off with a comment saying why) — don't let the fixer decide implicitly by just silencing errors file-by-file. Fold the entry into the closeout commit; it touches the backlog anyway.

## Cross-ticket notes

- The round-1 → round-2 loop on this ticket is the methodology working at its best: blocking finding fixed in the same deliverable, non-blocking taken with the rationale preserved in code comments, question answered with line-number evidence. One round, done.

---

**Merge is a go.** Sequence confirmed: merge → closeout commit (manifest bump `aetheris-agents--CLAUDE.md` → `a12a145`, BL-017 backlog entry, manifest regen last) → push → close #46 with backlinks → three-file upload (runbook + backlog + manifest) → board reads true zero.

**Gate rule promotion — approved, full scope** (three data points in under a week: `mix test` red since before BL-003, `tsc -b` red three weeks, `bun run lint` red since an undated plugin bump). Standing rule added to CLAUDE.md:

> **Every existing gate runs at ticket boundaries, even off-territory** (`mix test`, `tsc -b`/`bun run build`, `bun run lint`, sprint, `drift_check --strict`). A red gate gets a tracked ticket the day it's found — never carried silently. Source: BL-016, BL-005 (×2).

With the clause that a known-red gate already carrying a tracked ticket is named in the packet with its ticket ref, not re-triaged — the rule prevents silent carry, not tracked carry (otherwise BL-016/BL-017 being open would make every future packet read as a violation).

**Adjusted closeout (the promotion changes the upload math):** CLAUDE.md (gate rule) + backlog (BL-017) + manifest regen last; the `aetheris-agents--CLAUDE.md` manifest row now points at the closeout commit (not `a12a145` — superseded by the edit itself), runbook and backlog rows to their BL-005 commits. **Upload set becomes four files**: CLAUDE.md, runbook, backlog, manifest.

**Queue:** closeout → BL-016 → BL-017 → milestone conversation (BL-007 planning, gated on the activegraph brief). BL-004 stays parked for its harness.rs touch; BL-006 waits on its trigger.
