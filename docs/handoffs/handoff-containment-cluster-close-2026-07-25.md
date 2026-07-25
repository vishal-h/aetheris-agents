# Handoff — containment cluster + BL-048 closeout shipped / next: BL-038 (pre-arc mainline resumes) — 2026-07-25

Date: 2026-07-25 · From: claude-ui (design session, opened from
`handoff-bl049-bl047-close-2026-07-24.md`) · For: fresh claude-ui design session, same project —
**the BL-038 session, resuming the pre-arc mainline.**

> **Note added at commit (claude-code) — three citations did not resolve; two are now fixed.**
> Checked at commit time; flagged rather than silently corrected, because each is an instance of
> the very transport rule this handoff restates — artifacts land as **files**, not chat.
>
> 1. **`handoff-bl049-bl047-close-2026-07-24.md`** (the predecessor cited above) is **not in this
>    repo**; `git log --all` finds no commit that ever added it. Recover the BL-049/BL-047 detail
>    from `../aetheris/docs/reviews/bl-049-review.md`, `bl-049-contract-draft.md`,
>    `bl-047-review.md`, `bl-047-contract-draft.md` and the backlog rows instead.
> 2. ~~**`bl-053-review.md`** — not committed.~~ **Resolved:** transcribed from the relay and
>    committed alongside this handoff, with the r1 response appended and a provenance note
>    recording that it landed after the fact.
> 3. ~~**`bl-043-review.md`** — not committed.~~ **Resolved:** same.
>
> Items 2 and 3 were fixed rather than left flagged, because the texts existed verbatim in the
> relay — transcription, not reconstruction. Item 1 stands: that handoff's content is not
> recoverable from this session, so it is left named rather than invented.
>
> Everything else this handoff cites was verified present at commit: the other six review-file
> artifacts, `scripts/containment_probe.exs`, and the `sandbox` job in `.github/workflows/ci.yml`.
> Note the review files live in the **harness** repo (`../aetheris/docs/reviews/`), not here.

**Watermark at handoff:** harness `a804ba1`, agents `1d43871` — **both = `origin/main`, synced,
clean, nothing held.** `drift_check --strict`: **0 FAIL, exit 0, one exempt WARN** —
`backlog-2026-06.md` stale (the BL-048 closeout re-staled it *after* this cycle's export; expected,
strict-exempt, clears at the next export). **Verify via relay as first move**, and read both repos'
`CLAUDE.md` learning sections before your first edit. Recover specifics from the repos + review
files, not from this handoff.

## What shipped this session (the verify-effect-classes cluster, end to end + its cleanup)

All landed and pushed. Recover the detail from the review files, not here.

- **BL-053** (harness `915d582`, §3 ratified `b4857eb`) — verify makes **no filesystem-hash claim**.
  The `fs_hash` compare was `nil != nil` (dead since `d4728af` removed the whole-sandbox hash for a
  timeout); the `:hash_mismatch` arm is deleted, §3 corrected in both cells (§8 option B), five doc
  mirrors swept. The lost capability (cross-file drift detection) is named, not restored.
- **BL-043** (harness `515a4ab`, §5 ratified `1e00a52`) — `http_call` **repaired** (was SIGSYS in
  every mode). Five syscalls enumerated empirically over three probe rounds (not guessed);
  worker-crash-kills-caller fixed in **both** its mechanisms (unlink + the independent
  `GenServer.call` exit path). §5 generalized to point at `sandbox.rs` rather than re-list the
  syscalls (the BL-053 anti-drift lesson).
- **BL-050 + BL-055 + BL-056** (harness `9871059`, §5 ratified `dd12dbb`) — **one reorder**: `ready`
  is now the *fully-established barrier* (namespaces → cgroup → overlay → exec-server → stdio MCP →
  seccomp → `ready`) and **attests** each primitive. Verify **refuses** on netns *or* seccomp with
  distinguishable messages; record **attests-and-continues** (no longer silently unfiltered). stdio
  MCP servers spawn pre-filter from the init payload; the dead request-time `mcp_spawn` is gone.
- **BL-048 closeout** (harness `6e2fad8`) — the `requires_worker` set is **green** (951/0, two runs)
  and **wired** behind a containment-attestation gate. **DONE pending the first CI dispatch** (see
  Open human calls).
- **BL-002 export** (agents `f72f096`) — project knowledge refreshed to this cluster; the four stale
  docs re-pinned; first **0-WARN** strict run of the arc. (A copy-forward defect in the manifest
  *narrative* was caught by human review and fixed — see Dispositions.)

## Facts the next session must not relearn

- **The attestation infrastructure is now the ground truth for containment.** The worker attests
  `network_namespace / overlay / exec_server / seccomp (+ error) / mcp_servers` in its `ready`
  handshake; `Client.containment/1` reads it; `Client.startup_verdict/4` holds the verify-refuses /
  record-attests split (policy on the BEAM, not the worker). `scripts/containment_probe.exs` turns
  capability into a runtime fact any test or CI job can read. Do not reintroduce host-capability
  *assumptions* — ask the worker.
- **determinism-contract §3/§5 are normative at `dd12dbb`** (BL-053 §3, BL-043 §5, BL-050/055/056
  §5). The project-knowledge export is at this cluster but **re-verify any §3/§5 citation at HEAD**.
  §5 now: verify refuses on either containment primitive (distinguishable messages, seccomp message
  is directive by design while §5 itself is hedged — an *intended* split, don't reconcile); record
  is best-effort and attested, not silent.
- **New ExUnit tags:** `:requires_real_provider` and `:requires_internet` are excluded by default and
  are **not** pulled in by `--include requires_worker` (they need a live model / the internet, which
  no sandbox capability provides). `McpGithubTest` and the httpbin `http_call` test carry them.
- **`http_call` works now** and is `:uncontained`/served under verify, re-executed under
  `--allow-effects`. `git_*` is served-not-verified (BL-047). `run_command` reproduces only for a
  hermetic command.

## Open human calls carried

- **BL-048 — the first CI dispatch is the pending move.** The `sandbox` job in
  `aetheris/.github/workflows/ci.yml` gates on the probe; the probe only reports on `ubuntu-latest`
  once a job runs there (a PR or `workflow_dispatch`). **If capable** → BL-048 closes as a CI job.
  **If it skips** (GitHub's 24.04 image may restrict unprivileged userns — deliberately unsurveyed) →
  the sprint is the home, but **confirm the sprint runs on a schedule / capable runner** before
  calling Part B satisfied: "wired to a sprint nobody runs" is the exact rot BL-048 existed to kill
  (review observation #2, `docs/reviews/bl-048-closeout-review.md`).
- **No pushes held** — everything this session is on origin.

## Next work + sequencing

- **BL-038 is next** — the pre-arc mainline resumes here now that the verify cluster has settled.
  Medium, operator-facing; it carries the **shared find-run-by-id** piece that **BL-024** (19b)
  should inherit, so BL-038 lands first. Read its row in `backlog-2026-06.md` for the specifics — do
  not restate from memory.
- Then the pre-arc order continues per the sequencing table: **BL-039** (fork UX, builds on BL-028's
  landed state — must not race it) → **BL-030** → **BL-032** (WAL-or-not, after the fork call pattern
  settles) → **BL-033** (trivial deletion, after BL-024) → **BL-037** (before BL-024) → **BL-024**
  (design-led, compose with `caused_by`).
- **Parked / trigger-fired (recorded, not scheduled — do not pick up as ready work unless the trigger
  fired):**
  - **BL-057** (new) — a `provider: "stub"` run that declares tools starts **no worker** and its tool
    calls silently never execute, yet reports `:done` (`Agent.Supervisor.worker_child_spec/1` first
    clause). A **product question** (is a stub run tool-inert, or should it start a worker / reject
    the config?), not a test fix — blast radius is six test files, three in the default suite.
    **Blocks un-skipping `OverlayAutonomousTest`.** Medium.
  - **BL-054** — the `requires_worker` load-sensitive flake slot (`RunHelpersTimeoutTest` / a
    fixed-ms window); fold into a poll-not-time rewrite when someone's in that file.
  - **BL-052** — drift check-9 ghost-struct arm scoped to `commands/*.rs`; fires when §4 first
    documents a struct outside it (`rglob` fix).
  - **BL-046** — the `"output"` vs `"result"` payload-key convention (mind the fourth reader).
  - **BL-045** — `mode: :verify` is a misnomer (naming decision, not a BL-033 deletion).
  - **BL-044** — `mix aetheris` discards exit codes.
  - **BL-035** — `formatCost`/`formatTokens` extraction, fires on the fourth formatter site.
  - **BL-026** — first `verify` against a multi-agent/orb trajectory (trigger-parked, ratified
    2026-07-19).
  - **BL-051** — the one unreproduced `mix test` flake (capture fix landed; re-triage only if it
    fires again with a name).
  - **BL-034 / BL-041(b) follow-on** — the manifest-narrative copy-forward this session hit (a stale
    narrative passed a green checker; only human review caught it) is BL-034's live form: when BL-034
    is worked, the concrete check is to assert the "N rows re-pinned" narrative against the actual
    manifest-table diff. `BL-036`/`BL-041(b)` landed check-9 and the drift guards already.

## Standing rules (session hygiene — unchanged)

Fresh claude-code session per ticket; **full restart after any CLAUDE.md change**; **§8** governs
determinism-contract edits (contract-draft artifact + human-ratified exact wording — this session
landed BL-053 §3, BL-043 §5, BL-050/055/056 §5 that way), **§7** governs CLAUDE.md promotions; every
existing gate at every boundary (even off-territory), a red gate gets a tracked ticket the day it's
found; `drift --strict` **post-commit** for manifest-tracked edits, name the exempt
`project_knowledge` WARNs rather than chase them; the export's own narrative is **authored fresh each
time, never copied forward** (this session's manifest bug is why that's now explicit); pushes held
for the human; transport rule — §7 wordings and §8 contract drafts land as **review-file artifacts**,
not chat; recover from repos + review files, not memory of a closed session.

## Review-file artifacts produced this session (recover from the repo, not chat)

`docs/reviews/`: `bl-053-review.md` + `bl-053-contract-draft.md` (RATIFIED),
`bl-048-fs-hash-diagnosis.md`, `bl-043-review.md` + `bl-043-contract-draft.md` (RATIFIED),
`bl-055-bl-056-containment-decisions.md` (the scout memo), `bl-050-055-056-review.md` +
`bl-050-055-056-contract-draft.md` (RATIFIED), `bl-048-closeout-review.md`. New scripts:
`scripts/containment_probe.exs`; new CI job `sandbox` in `.github/workflows/ci.yml`. New backlog
rows: **BL-055, BL-056, BL-057** (and BL-052/BL-054 from earlier in the arc).
