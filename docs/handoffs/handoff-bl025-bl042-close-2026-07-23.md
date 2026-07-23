# Handoff — BL-034/BL-041/BL-025/BL-042 design session closed / next design session — 2026-07-23

Date: 2026-07-23 · From: claude-ui (design session, opened from `handoff-b1b3-close-2026-07-22.md`) · For: fresh claude-ui design session, same project.

**Watermark at handoff:** agents `main` `63a2ab3`, harness `main` `9d994fd`. Both synced to
origin, clean trees at close. **Verify both via relay as first move.** Project knowledge was
last exported 2026-07-22 at the b1–b3 close (24-file bundle); it is now behind by this
session's four tickets — three manifest-tracked docs are expected-stale (see Loose ends). Read
both repos' CLAUDE.md learning sections before your first edit — the promotion set is unchanged
from b1–b3, but a new §7 candidate is now countable (see Standing rules).

## State: four tickets shipped, one new class recorded

All merged to `main` and pushed. Recover specifics from the review files and the contract, not
from memory of this closed session.

- **BL-034** (agents `fe8298c`) — export-prompt self-staling fix. Dropped the drift-baseline
  append from `prompts/bl-002-refresh-project-knowledge.md` (it re-staled the manifest it had
  just written). Three defects closed, not one: the ordering hazard, an unreachable "zero WARN"
  done-check, and a read-only-scope self-contradiction. **Evidence correction:** the row's "it
  fired in production at `628f15f`" claim was **withdrawn as false** — a check-8 sweep of all 38
  committed manifests is clean; the hazard is real but **latent, never fired**. Review:
  `docs/reviews/bl-034-*` (the ticket landed via the drop-decision; see the row's Status block).
- **BL-041** (filed `d567d75`; worked instance in the `b8a72fe` range) — "manifest-staleness
  done-checks are vacuous pre-commit" (`drift_check` check 8 reads committed history). Filed
  with disposition (a) doc-rule / (b) tooling guard both open. **Worked instance recorded on the
  row:** BL-025's own pre-commit gate reported 1 WARN, post-commit 3 — the vacuity fired on the
  caveat's own author. **The class is now countable at 2** (BL-034 `fe8298c`, BL-025
  `8021a59/00ddd34`), recorded not self-promoted.
- **BL-025** (harness `8021a59`, agents `b8a72fe`) — verify effect classes + record-and-serve.
  `EffectClass` (`:pure`/`:contained`/`:uncontained`, single source, completeness test);
  `:uncontained` (http_call, external MCP, in-process orb tools) record-and-served by default,
  reported **served-not-verified**; `--allow-effects` re-executes. **Grew in-cycle (approved):**
  `aetheris verify` never reached `Verifier` — it started a live run returning `verified: true`
  unconditionally; rewired to `Aetheris.verify_run/2` with a real verdict and failure-reflecting
  exit code. §3+§5 contract landed. **Closed BL-027** (folded the `recorded_result/1` reader
  into `verify_step`); **spawned** BL-042/043/044/045/046. Review: `docs/reviews/bl-025-review.md`.
- **BL-042** (harness `9d994fd`, agents `63a2ab3`) — capability-shaped containment. Default
  verify re-executes inside a network namespace (`CLONE_NEWNET`, gated on `not allow_effects`);
  establishment status rides a reordered `ready` handshake; **fail-closed** enforced in
  `Worker.Client.init/1` (`containment_verdict/2`), so a worker that can't establish a *required*
  netns never starts. `lo` left down. **Grew in-cycle (approved):** `run_command` was never
  re-executed under verify at all (`unknown_tool`), so the red arm was vacuous — routed
  `run_command` only; `git_*` → BL-047. §3+§5 landed (three statements incl. the correction that
  `:contained` was never "re-executed and compared" for the exec-server family). **Spawned**
  BL-047/048/049; **BL-043 now unblocked**. Review: `docs/reviews/bl-042-review.md`.

## Facts the next session must not relearn

- **`aetheris verify` is now real and safe.** Routes through `Verifier`; record-and-serves
  `:uncontained`; default runs under a netns so no re-executed tool can egress; **fail-closed**
  when the netns can't be established — **non-Linux hosts and restricted containers refuse a
  default verify** (accepted 2026-07-23), operators use `--allow-effects` to proceed uncontained.
- **`run_command` re-executes but its verdict is unreliable** — its exec-server payload embeds
  `duration_ms` and §5's compare is value-equality over the whole blob, so a reproducing command
  reports `:output_mismatch`/`:verified` **nondeterministically** (~1-in-6 verified). BL-042's
  containment proof does not rest on the verdict (connection counts + a non-vacuity guard do).
  Tracked as **BL-049**, sequenced *ahead* of BL-047. Root cause: worker-native tools split
  `duration_ms` out in `parse_execute_response/1`; exec-server tools don't.
- **`git_*` is still `unknown_tool` under verify** — the exec-server routing gap BL-042 fixed
  only for `run_command`. **BL-047**, which must decide the taxonomy first (should mutating git
  ops re-execute under verify at all?) — routing is three lines once that's settled.
- **Contract §5/§3 are normative and current** (harness `9d994fd`). §5 carries the three classes,
  record-and-serve, served-not-verified, netns containment, the fail-closed refusal as
  contract-visible behaviour, and residual limitations (incidental egress *closed* by the netns;
  `git_*` gap → BL-047; `run_command` verdict → BL-049; echo; first-diverging-event → BL-026).
  **§8 governs:** any change to a guarantee lands with a human-approved review-file draft in the
  same cycle. Both BL-025 and BL-042 exercised this.
- **The pre-commit-drift vacuity** (BL-041): a `drift_check --strict` run *before* committing a
  manifest-tracked edit is vacuous — check 8 reads committed history. Run it **post-commit**, and
  name the exempt `project_knowledge` staleness WARNs rather than chasing them.
- **BL-043**: `http_call` is SIGSYS-killed in every mode (`setsockopt` absent from the seccomp
  allowlist) — dead, no live users assumed. Now **unblocked**: the netns landed, so restoring
  egress no longer widens an open window. Confirm no live users before repair-vs-retire.

## Standing rules

- The b1–b3 promotion set still binds (Silent-wrong-answer, Adjacent-case/coincidence,
  reviewer-mechanisms, cross-repo done-check clause, amended Repos/P8 rule).
- **New §7 candidate, countable at 2, NOT yet promoted:** the pre-commit-drift / Silent-wrong-
  answer-in-gate-ordering class (BL-034, BL-025). Its **promotion vehicle is BL-041(a)** — the
  CLAUDE.md doc-sync rule "manifest-staleness done-checks run post-commit." BL-041(a) is a
  CLAUDE.md change → **full restart after**, and any packet-producing session predating it is
  stale by construction.
- Transport rule holds: §7 wordings and §8 contract drafts land as review-file artifacts, not
  chat. Both were exercised this session (BL-025/BL-042 contract drafts; the CLI-rewire and
  taxonomy-spine decisions pulled into `bl-025-review.md` §A when they'd have been stranded).

## Dispositions on record — do not reopen

- **BL-027 Done** (folded into BL-025). Its payload-key convention residue → **BL-046** (declare
  the writer-side convention; the fourth reader is what the row exists to catch — do not naively
  dedupe fork's reader, which normalizes per §2, with verify's, which reflects the record verbatim).
- **BL-045** (`mode: :verify` misnomer) is a *naming* decision, **not** a BL-033-shaped deletion —
  still reachable from agent-file config + eval templates. Do not batch with BL-033. This is the
  RunConfig **mode** union, not the event-type union (BL-040).
- BL-042 ratifications: **H3 fail-closed** (incl. non-Linux refusal accepted); **H2 lo-down**;
  **H4 netns gated on `not allow_effects`** (requirement). `run_command` stays **`:contained`**;
  git_* taxonomy deferred to BL-047.
- **BL-026** still parked on trigger (first `verify` against a multi-agent/orb trajectory).

## Next work candidates + sequencing (no commitment made)

Primary chain: **BL-049** (run_command verdict — exclude volatile fields / structural per-tool
policy / move `duration_ms` into the step envelope, matching the worker-native shape; **carries
a one-line §5 rider** — "The opt-in" subsection should state that `--allow-effects` also waives
the netns, a completeness gap noticed but not touched at BL-042, folded here rather than a
standalone §8 cycle) → **BL-047** (git_* routing + taxonomy; decide classification first) →
**BL-041(a)** [restart after] → **BL-041(b)** (drift tooling guard, batch with BL-036).

Alongside: **BL-048** triage (the `requires_worker` set is red — 15 failures, identical on a
clean tree, invisible to CI; one — nil `fs_hash` — is *possibly a live defect*, needs diagnosis
not a test edit); **BL-043** (unblocked). The pre-arc original order resumes at **BL-038** once
the verify cluster settles.

## Open human calls carried

None pending. Loose ends (owned, not open):
- **Manifest `628f15f` narrative correction owed at the next export** — the withdrawn "born-stale
  instance at 628f15f" claim still sits in `docs/project-knowledge-manifest.md`; the next BL-002
  run authors that narrative fresh, so ensure it is not copied forward from the old manifest.
- **Three exempt staleness WARNs** (`backlog-2026-06.md`, `aetheris/runbook.md`,
  `aetheris/determinism-contract.md`) clear at the next export.
- **BL-041(a) is a precondition to that export** — its post-commit-ordering rule governs the
  export's own done-check.
- The **opt-in §5 sentence** rides BL-049 (above).

## Session hygiene (unchanged)

Fresh claude-code session per ticket; full restart after any CLAUDE.md change (BL-041(a) is one);
both CLAUDE.md learning sections before the first edit of any packet-producing session; pushes
held for the human; every gate at every boundary (drift `--strict` **post-commit** for
manifest-tracked edits); recover from repos and review files, not from memory of this closed
session.
