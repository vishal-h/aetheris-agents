# Handoff — provider three (Linode) kickoff — 2026-08-04

> Not exported to project knowledge — handoffs never carry a manifest row. Commit to
> `docs/handoffs/` and attach it to the next claude-ui session.

## Status
The cloudcost-in-Rig batch is CLOSED and exported: five rows (BL-084, BL-085, BL-083, BL-086,
BL-073) plus satellites BL-095/096/097, all DONE, merged, and described in project knowledge at
the 2026-08-04 boundary. Next milestone: **provider three — Linode**.

Repo state: aetheris-agents `main@cf5f062` (pushed, tree clean); aetheris (harness) unchanged this
batch, last at `265d336`. `drift_check --strict`: 9 PASS / 0 FAIL / 0 WARN.

## Triad rules (unchanged)
claude-ui = design + review, never touches the repos; claude-code implements (fresh session per
ticket); the human relays packets verbatim and arbitrates. Pushes held for review.
Offline-pytest-against-fixtures is the test spine. claude-ui's doc edits are section-scoped, applied
against HEAD and diffed.

## The bet (unchanged — held twice)
A new provider = a new adapter + its fixtures + its own run. The frozen pieces do NOT change:
`detect_orphans`, the m1 §Normalized schemas, `compose_report_data`. `render_report` is touched only
for enumerated provider-agnostic adjustments. This held for AWS at m2-cloudcost (AWS landed as
provider two, contract intact). Linode is the third instance of the same bet — and Linode-first is
deliberate: it is the smaller adapter (fewer resource types, a more direct APIv4 surface than GCP's
billing-export path), so it is the faster proof the contract generalizes past AWS a *second* time
rather than the bigger coverage win.

## What Linode inherits generic (built this batch — no Linode-specific work)
- **View report (BL-073).** The Rig resolver is provider-agnostic — it scrapes document-extension
  paths from any run's `tool_result`. Linode's report comes out of the shared `render_report` as
  HTML and is discovered identically. No new resolver, no adapter dependency.
- **Run classification (BL-083).** `classifyRun` keys on the `cloudcost` label prefix, so a
  `Cloudcost · Linode` label classifies with no Rig change.
- **Manifest (BL-084) + config surface (BL-085).** Declaring `CLOUDCOST_LINODE_*` env in
  `cloudcost/tools.json` renders its config rows for free; per-launch provider selection rides the
  existing `extra_env` "Additional env vars" panel.

## What Linode specifically needs (the milestone's actual work)
- **`fetch_linode.py`** — a read-only Linode cost + inventory adapter, written against the frozen m1
  §Normalized schemas (`cloudcost--milestone.md` §Normalized + `cloudcost/scripts/_normalized.py`),
  emitting the same normalized artifacts as `fetch_aws` / `fetch_do`. Its API surface (Linode APIv4
  billing + inventory) is the adapter's to determine; the OUTPUT contract is frozen.
- **The provider-vocabulary seams (BL-074).** m1/m2 found provider vocabulary reaches shared
  machinery in at least three places — `state` (`STOPPED_STATES`), inventory `type` values, and the
  third seam BL-074 enumerates. Linode's own statuses and resource types must map to the canonical
  §Normalized values, never leak Linode vocabulary into `detect_orphans`. This seam analysis is the
  first thing the issue-doc must do — it is where the frozen-contract bet is actually won or lost.
- **`CLOUDCOST_PROVIDER = "linode"` literal.** `cloudcost/agents/cloudcost_orchestrator.exs` accepts
  only `"aws"` / `"digitalocean"` today and raises otherwise; add `"linode"` (name, short, slug,
  `fetch_linode.py`), and confirm the run_id slug (`cloudcost-orch-linode-…`) so BL-083 groups it.
- **`CLOUDCOST_LINODE_TOKEN`** (masked) in `fetch_linode`'s `env` in `cloudcost/tools.json` — the
  read-only APIv4 token. D2 posture carries verbatim from AWS: read-only key only, plaintext-on-disk
  trust level, never a write key; the runbook records the posture.
- **Declare the fetch-step timeout explicitly (BL-096).** `fetch_aws` needed
  `fetch_timeout_ms = 300_000` because it exceeds the 60 s exec-server default. Linode's latency is
  unproven, not absent — measure it and declare the timeout in the agent file rather than letting the
  model rediscover it at runtime. *Absent is unknown, not zero.*
- **Fixtures + its own run.** Offline pytest fixtures for `fetch_linode` (the test spine), and a
  Linode `sprint.sh` run — minding the live tripwires below.
- **Currency (§Open).** Confirm Linode's billing currency and whether it re-opens the multi-currency
  §Open item m1 deferred.

## Fold into this arc (not standalone)
- **BL-090** — regenerate the (generated) capability-matrix once `fetch_linode` + its manifest land;
  it wants the new script/use-case entry, and the cloudcost cell is already stale from BL-083's label
  change. Regenerate, do not hand-edit; reconcile the `detect_optimization_signals` cell at regen.
- **BL-092** — land the `tools.rs` serde guard with the new manifest, so a third provider's
  `tools.json` is covered by the standing offline check, not only pytest transcription.

## Not a gate (revised from the prior handoff)
The scrape-vs-record decision is **not** a prerequisite for Linode. BL-073's resolver is already
provider-agnostic, so Linode adds zero scrape-specific debt; and recorded-path, if ever wanted, is a
single harness/event-union change independent of provider count and of the adapter. Proceed on
scrape; treat recorded-path as its own optional milestone, picked up on merits or when scraping
strains — not something that blocks Linode.

## Live tripwires (carried)

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

- **BL-069** — plant a resource before any run that must assert ≥1 orphan, or the sprint's ≥1-orphan
  assertion is expected-red.
- **BL-077** — sprint `fail` sets no exit status; read the `[OK]` / `[FAIL]` lines, not `$?`.

## Review-discipline learnings promoted (apply here)
- The **click-through is a merge gate**, not an owed residual, for any ticket whose Done-when names a
  user-facing action — and **name the branch under test** in every click-through hand-off; a gate is
  only valid if the build holds the change.
- **`drift_check` verifies a pin is current, never that it is complete** — read the pinned content
  against what it should say, do not trust the green.
- **Export is remove-all-upload-all** against the full manifest set, never a hash-driven diff.
- An **owed click-through is only owed if the primitive behind it is known-good** — otherwise it is an
  unexamined assumption wearing a residual's clothes (the BL-073 shell-open case).

## Cold set (parked, trigger-fired)
BL-087 (payslip manifest omission), BL-088 (runnable gate), BL-089 (three missing manifests),
BL-091 (exportConfig omission), BL-093 (payslip runbook drift), BL-094 (direct-launch milestone,
issue-doc-first). None has teeth; each fires on its trigger or when someone is in the file.
BL-090 / BL-092 fold into the Linode arc above.

## First move
Milestones here are **issue-doc-first**, so the first deliverable is the Linode milestone issue-doc,
not code. It must establish: the frozen output contract `fetch_linode` is written to (§Normalized);
the provider-vocabulary seam analysis (state / type / the third BL-074 seam — Linode's values →
canonical); the fixture plan; the sprint-run plan; and the currency check. Design that, hand the
human the milestone framing, then sequence the tickets (adapter → fixtures → run, with the fold-ins).

Source: cloudcost-in-Rig batch close, 2026-08-04.
