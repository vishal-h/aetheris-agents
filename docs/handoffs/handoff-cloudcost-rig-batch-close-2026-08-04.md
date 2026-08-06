# Handoff — cloudcost-in-Rig batch CLOSED — 2026-08-04

## Status

The five-row cloudcost-in-Rig batch is complete: BL-084, BL-085, BL-083, BL-086, BL-073.
All verified, all doc-synced.

**All five are merged to `main`, and so is BL-095** (`5fe1903`). BL-073 and BL-095 were each held
unmerged until their in-app click-through passed — this handoff's own promoted learning applied to
itself — and both passed on 2026-08-04: cloudcost's report opens, docbuilder shows
"View reports (3)", the plan card renders `SMTP_PASSWORD` / `GOOGLE_SERVICE_ACCOUNT` as `set`, and
Settings dots the service-account path. **Nothing owed.**

*Applied against `main@67df3ec` + `bl-073-view-report@11e53ef`, 2026-08-04. Three claims in the
draft diverged from repo state and were corrected rather than followed — the divergences are named
inline so the correction is auditable, not silent.*

## Triad rules (unchanged)

claude-ui = design + review, never touches the repos; claude-code implements (fresh session per
ticket); the human relays packets verbatim and arbitrates. Pushes held for review. Offline test
spine. claude-ui's doc edits are section-scoped, applied against HEAD and diffed.

## What landed

- **BL-084** (`4f08264`, merged) — `cloudcost/tools.json` manifest + the repo's first manifest test
  suite (`tests/test_tools_manifests.py`). Six `CLOUDCOST_*` env declared;
  `detect_optimization_signals` source-derived (the matrix omits it); `_normalized` declared
  import-only. Deserialization proven by a discarded serde round-trip against the real
  `ToolsManifest`.
  > *Draft correction:* the draft credited this suite with "parses `USE_CASE_PREFIXES` from source
  > so it can't drift". It does not — `grep -c USE_CASE_PREFIXES tests/test_tools_manifests.py` is
  > **0**. That property belongs to `scripts/check_run_classifier.py` (BL-083, 5 references), and is
  > recorded there instead. Two different guards were conflated.

- **BL-085** (`f94b9d3`, merged) — cloudcost launchable from Rig on the **existing** orchestrator
  door + the shipped `extra_env` panel for per-launch `CLOUDCOST_PROVIDER`; config surface
  dynamic-only (no `agentConfigDefs.ts` change). D2 posture documented in `cloudcost/runbook.md`:
  Rig injects the whole agent-config map unfiltered, so `api/tools.json`'s bare `AWS_*` is actively
  present — **"no belt" ≠ "clean env"** — and the adapter's explicit session holds it by
  construction (demonstrated live, not asserted: selecting AWS with the poison present and no
  `CLOUDCOST_AWS_*` raises and refuses). The **direct** (non-LLM) launch door was peeled to BL-094.

- **BL-096** (`32933d8`, merged; closed by `cloudcost-orch-aws-3KU2NQ`) — fetch-step timeout
  declared in the agent file. A determinism-contract fix, not a slow step: completion had been
  model-dependent, since STEP 1 always timed out and only a model-chosen retry finished the run.

- **BL-097** (`779018d`, merged) — Recent-prompt suggestions-dropdown overlay unbroken.

- **BL-083** (`064664a`, merged) — run-list classifier: **label**-patch (`prefixes: string[]` per
  group), **not** run_id re-keying. run_id fails on api (first segment `uc`, tenant/gateway
  discriminator is a *suffix*, prefix embeds a milestone number), and `classifyRun` already reads
  `COALESCE(label, run_id)` so label-keying is a **superset**, not an alternative. Supersedes the
  prior handoff's §Corrections 3. Standing guard `scripts/check_run_classifier.py` +
  `tests/test_run_classifier.py`. Provider now in the cloudcost label (`Cloudcost · AWS` / `· DigitalOcean`).
  Unclassified 693 → 565 over 957 runs.

- **BL-086** (`de0b77b`, merged) — `TrajectoryView` labels steps by `run_command` stage
  ("Step 0 · fetch_aws"). Pure frontend; reads `tool_input.args` for the `.py` (there is no
  top-level `args`); proven offline against real trajectories with a mutation control pinning the
  `type` → `event_type` rename — without it every assertion passes vacuously. Retrospective:
  257 of 268 pipeline runs back to 2026-05-21 label correctly.

- **BL-073** (`11e53ef`, merged `d4f44e4`) — "View report": scrape document-extension paths from
  `tool_result` (4-hop guarded parse: `output` → JSON → `stdout` → JSON → value-scan), server-side
  resolve + existence-gate (subsumes overlays **and** docbuilder's `rename_output`
  `original`/`renamed`), offer-the-set (1 → button, N → list), open server-side via
  `harness_open_artifact`, which re-vets the path against the freshly computed set before
  `open::that_detached`. Shell scope untouched.
  **Closed 2026-08-04** by in-app click-through: cloudcost's HTML opens, and
  `docbuilder-orch-wFwf_g` (3 artifacts) renders the offer-the-set list. The open is server-side
  (`harness_open_artifact`) because the frontend shell `open` is URL-scoped and rejects file paths.

## Satellite ledger (filed, unstarted unless noted)

**With BL-095 and BL-096 closed, the cold set is BL-087–BL-094 and there are no teeth left in it** —
priority-ordered cleanup plus the BL-094 direct-launch milestone. Provider three is the real next
chapter, not this list.

- **BL-087** — `payslip/tools.json` omits `merge_employee_payslips.py` (xfail-tracked in the
  manifest suite).
- **BL-088** — `ManifestScript.runnable`: mark a manifest entry describe-only (the `_normalized` case).
- **BL-089** — `tools.json` for docbuilder / provenance / boxy-pipeline (the three still without one).
- **BL-090** — capability-matrix regen (generated doc): omits `detect_optimization_signals` **and**
  now carries BL-083's stale cloudcost label. One regen reconciles both; do not hand-edit.
- **BL-091** — `exportConfig()` drops every manifest-derived env key from Export (api's 16 already
  affected).
- **BL-092** — `tools.rs` manifest-deserialization test coverage (make BL-084's discarded round-trip
  permanent).
- **BL-093** — runbook drift: `PAYSLIP_MONTH` claimed "not a persistent setting" but rendered persistent.
- **BL-094 — MILESTONE** (issue-doc first): direct, non-LLM launch of config-orchestrators. Blocked by
  the config-vs-driver defect (`mix run` on a `%RunConfig{}` file exits 0 doing nothing; only
  `mix aetheris run` loads it; the two `.exs` kinds need distinct paths); plus no UI supplies
  `script_path`, the Capability-Matrix Run button discards `agent.file`, and `RunConfig.env` is a
  latent unused hook.
- **BL-095 — DONE** (`63ea4b5`, merged `5fe1903`) — the plan card no longer prints secret values.
  Deny-by-default: a value renders only on an explicit `masked === false`, so the two keys with no
  metadata at all, and any future undeclared key, show `set` rather than leaking.
  `GOOGLE_SERVICE_ACCOUNT` was `masked: false` and is now `true` — it is a credential-file locator,
  and neither candidate rule would have hidden it otherwise.
- **BL-096 — DONE** — fetch-step timeout instructed in the agent file (determinism-contract fix).
- **BL-097 — DONE** — Recent-prompt suggestions-dropdown overlay unbroken.

## Live tripwires (carried, unchanged)

> **Superseded 2026-08-06 (m4 t2), BL-069 only.** The instruction below — plant a resource before
> any run that must assert ≥1 orphan — is retired. **Decision 12**
> (`cloudcost/m4-consolidation.md` §Ratified decisions → Technical) rules out planted cloud
> resources on every provider, and **BL-069 closed by retiring the practice** rather than by
> re-fixturing it. The ≥1-orphan assertion no longer exists; the cloudcost sprint case asserts
> **rule legibility** in its place — that the adapter's inventory reached the rule catalog in a
> shape the catalog could read, with the canonical `type` vocabulary imported from
> `cloudcost/scripts/_normalized.py`. The live description is `cloudcost/runbook.md` §"What a
> zero-orphan account means, and what the sprint asserts instead". What is superseded is the
> **instruction**, not the record that a tripwire was armed. The BL-077 line below is unaffected.

BL-069 armed — plant a resource before any run that must assert ≥1 orphan.
BL-077 — sprint `fail` sets no exit status; read `[OK]`/`[FAIL]`, not `$?`.

## Settle before provider three (GCP/Linode)

- **The report-artifact discovery convention.** BL-073 **scrapes** the path from the trajectory. A
  run that formally **records** its artifact path is cleaner and cross-provider-stable but touches
  the harness and likely the event union (three-change rule + `drift_check`). A third provider also
  produces reports — decide scrape-vs-record before it lands.
- Provider three is a third adapter against m1's frozen §Normalized schemas +
  `cloudcost/scripts/_normalized.py`, same triad, same frozen-adapter-contract bet. When it lands:
  declare its fetch-step timeout explicitly (BL-096 convention), confirm its output extension is in
  `DOCUMENT_EXTENSIONS` (BL-073), and confirm its label/run_id classifies (BL-083).
  > Note on the second: `DOCUMENT_EXTENSIONS` is nine entries but only four (`.html .pdf .docx
  > .xlsx`) are observed in the two real pipelines; the rest are forward-looking margin. An
  > unlisted extension yields **no control** rather than an error — the safe direction, but silent.

## Review learnings promoted

- **Rebuild Rig after each frontend merge before eyeballing.** Tauri does not hot-reload the merge,
  so a working change reads as broken (cost a false alarm on BL-086).
- **Residual vs unexamined assumption.** An "owed click-through" is only owed if the primitive
  behind it is *known-good*. BL-073's "the open is owed" concealed that the shell primitive could
  not take a file path at all — "is the path right" was proven while "can this primitive open a
  path" was never asked. **For a UI ticket whose Done-when names a user-facing action, the
  click-through is a merge gate, not a post-merge residual.** Applied here twice: BL-073 and
  BL-095 were both held unmerged until their report/card was seen in a rebuilt Rig, and both
  discharged 2026-08-04. Corollary learned the hard way in the same round: **name the branch under
  test when handing over a click-through** — BL-095's first check ran against a BL-073 build that
  did not contain it, and read as a broken fix.
- **Re-derive, don't copy.** Row claims (docbuilder bare-`Context` labels, stale counts) were false
  at HEAD; the live store is the oracle. Enumerate before extracting. This handoff's own draft
  carried three such divergences (see §Status and the BL-084 note).
- **Anti-vacuity.** Every all-empty/degrade assertion needs a positive control proving the harness
  *can* find something, and every offline proof must match the real runtime/render shape, not the
  serializer's.

## Export boundary (human-owned)

project-knowledge manifest is stale for `docs/rig/specs.md` and `docs/backlog-2026-06.md` — expected
mid-cycle, strict-exempt, clears when Vishal next exports. Note this handoff's own commit re-stales
`docs/backlog-2026-06.md`'s neighbour set no further: it adds a new file only.
