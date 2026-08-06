# Handoff — cloudcost-in-Rig batch (post-m2-cloudcost) — 2026-08-03

> **Three corrections applied at landing** — see §Corrections at the end for the diff against the
> handed-over text. Two were stale repo-state claims, one would have actively misled the fresh
> session (the `.html` artifact-selection rule, corrected in `31c0d88` before this landed). Noting
> rather than silently following, per the repo's ticket-text-quotes-repo-state rule.

## Status
m2-cloudcost is CLOSED and sealed. Both repos pushed (aetheris-agents through the BL-083–086
filings and the BL-073 rescope; aetheris `265d336`), project knowledge exported/uploaded ==
manifest, seven §7 learnings promoted and byte-verified. This handoff covers the small **Rig
follow-on batch** to finish before the next cloud-provider costing milestone (provider three: GCP
or Linode).

## Triad rules (unchanged)
claude-ui = design + review, never touches the repos; claude-code implements (fresh session per
ticket); the human relays packets verbatim and arbitrates. Pushes held for review.
Offline-pytest-against-fixtures is the test spine. claude-ui's doc edits are **section-scoped**,
applied against HEAD and diffed — never whole-file, and claude-ui keeps no writable mirror of a
repo doc.

## The batch — five rows in aetheris-agents `docs/backlog-2026-06.md`
Sequence: **BL-084 → BL-085** (084's `tools.json` env_deps render 085's config rows, so that order
avoids duplicated work). **BL-083, BL-086, BL-073** are independent drop-ins.

- **BL-084 — `cloudcost/tools.json` manifest.** Declare the six pipeline scripts (fetch_aws,
  fetch_do, detect_orphans, detect_optimization_signals, compose_report_data, render_report) with
  descriptions (reuse capability-matrix wording) + arg forms; `_normalized.py` is import-only
  (describe-or-omit). Manifest `env_deps` auto-generate Rig dynamic config rows (`tools.rs:594`,
  already exercised by api/tools.json's 16 keys) — which is why it precedes 085. Note the row is
  filed wider than cloudcost: `tools.json` is also absent for **docbuilder, provenance and
  boxy-pipeline**.
- **BL-085 — Cloudcost agent-config group + Rig-launch.** Config surface may come free from 084's
  env_deps (`CLOUDCOST_AWS_*` declared there). Narrows to: launch affordance + **per-run provider
  selection** (aws vs do, must be per-launch, not a static config value — the PAYSLIP_MONTH
  edited-between-runs shape is the anti-pattern the row rejects) + the D2 doc note. **Peel-off
  trigger:** if per-run provider selection needs a new Rig launch-parameter concept, it becomes a
  milestone, not a ticket. **D2 posture:** Rig's spawn injects config env but not the `env -u`
  hermetic prefix, and api/tools.json already declares AWS_ACCESS_KEY_ID/SECRET as env_deps — so a
  Rig-launched run may have the **poison actively present**, not merely the belt absent. The
  adapter's explicit-session construction holds D2 by construction (t1 poison guard); documentation
  duty, not a blocker — "no belt" ≠ "clean env." `agent-config.json` is plaintext on disk:
  read-only key only, never a write key.
- **BL-083 — single Cloudcost run-group + provider-in-label.** `classifyRun` matches on `run.label`
  against a hardcoded prefix list (run_id never enters it); no cloudcost entry → Unclassified.
  **Widened to the class (P4):** docbuilder (54 runs, 3 label variants, 6× the volume), cloudcost
  (9), legacy provenance-matrix (5), and api-tenant/gateway (whose entries match nothing — the real
  labels are `at1cmd`/`at1qry`/`cot1`) all fall through. Plus (.exs) orchestrator sets a
  provider-distinct label `Cloudcost · AWS` / `· DigitalOcean`.

  **Open question — ANSWERED at landing (see §Corrections 3). Re-key `classifyRun` on the run_id
  prefix; it is strictly better than patching the label list.** Measured over the last 250 runs,
  run_ids are regular where labels are not — `{use_case}-{role}[-{variant}]-{shortid}`:

  | run_id prefix | label | today |
  |---|---|---|
  | `docbuilder-orch`, `docbuilder-ctx` | 2 different labels | Unclassified |
  | `cloudcost-orch-aws`, `cloudcost-orch-digitalocean` | both `Cloudcost Orchestrator` | Unclassified |
  | `cap-matrix-provenance` | `Capability Matrix -- Provenance` (legacy wording) | Unclassified |
  | `payslip-orch`, `cap-matrix-*` | regular | correct |

  Three reasons run_id wins: it is **self-maintaining** (first segment is the use case, so a new use
  case groups without touching Rig); it fixes the legacy `Capability Matrix -- Provenance` label for
  free; and — the one that actually bites — **it decouples grouping from the label that this very
  row rewrites.** Keying on the label while also changing the label means the two must be kept
  consistent forever; a future rewording silently unfiles the runs. Bonus: the provider is already
  in the run_id (`cloudcost-orch-aws`), so the group and the provider are both derivable without
  the `.exs` change — keep the label change for display, not for classification.
- **BL-086 — generic TrajectoryView: label steps by run_command stage.** Derive `stage =
  basename(first .py arg)` from a step's `run_command` tool_called → step badge ("Step 0 ·
  fetch_aws"). Pure frontend, no harness change, retroactive, generic (docbuilder benefits);
  non-script steps stay "Step N."
- **BL-073 (rescoped in place, `e9b87f8`; selection rule pinned `31c0d88`) — minimal "View
  report."** Scrape the report path from the **`tool_result`**, NOT the `llm_responded` restatement
  — don't rest a UI affordance on the model honouring an instruction when structured output is
  beside it. Resolve the relative path (`output/aws/…`) against the run's `sandbox_path` /
  `overlay_base_dir` (both already in `runs.config_json` → "no harness change" holds by
  construction; overlay is a live generic case). Surface = "View report" opens external (Tauri
  shell) or a sandboxed iframe/CSP — **never** innerHTML into Rig's DOM. Generic (docbuilder too).
  Rich inline render (section nav, panels, live) explicitly DEFERRED — the scope-creep magnet.
  Carried: 1:1 run→report (decision H); doc-sync DoD (any new Tauri command / RunSummary field
  lands with its specs.md §4/§5 entry; drift check 9 guards §4 structs).

  **Artifact selection — by document extension, NOT by step and NOT by `.html`.** Measured on both
  real pipelines: `cloudcost-orch-aws-oFbapA` emits files from **4** tool_results (final is
  `.html`); `docbuilder-orch-iDGIIQ` emits **4 paths from a single** tool_result and its finals are
  `.docx` **and** `.pdf` — **no `.html` anywhere**. So "the last `.html`-producing one" finds
  nothing in docbuilder and leaves the control permanently absent on exactly the generic case the
  row exists to prove — and it would read as "docbuilder has no report" rather than as a bug.
  Discriminate on a document-extension set (`.html`, `.pdf`, `.docx`, …), take the **last
  qualifying artifact across tool_results** (intermediates are all `.json`). Flagged, not resolved:
  docbuilder emits two formats of two documents in one result, so "last wins" is not self-evidently
  right there — offer the qualifying set or take the last and say so, but never silently pick one
  of four and label it "the report".

**Verified, not reasoned** (run `cloudcost-orch-aws-oFbapA`): the report path is in the trajectory
twice — step 4 `tool_result` seq 28, step 5 `llm_responded` seq 32 — so scrape is viable with no
harness change.

## Deferred, not in this batch
Rich inline report render (BL-073's deferred half) — a separate small milestone if wanted. Settle
BL-073's discovery convention (scrape vs recorded-artifact-path) before provider three regardless,
since a third provider also produces reports.

## Live tripwire

> **Superseded 2026-08-06 (m4 t2), BL-069 only.** The instruction below — plant a resource before
> any run that must assert ≥1 orphan — is retired. **Decision 12**
> (`cloudcost/m4-consolidation.md` §Ratified decisions → Technical) rules out planted cloud
> resources on every provider, and **BL-069 closed by retiring the practice** rather than by
> re-fixturing it. The ≥1-orphan assertion no longer exists; the cloudcost sprint case asserts
> **rule legibility** in its place — that the adapter's inventory reached the rule catalog in a
> shape the catalog could read, with the canonical `type` vocabulary imported from
> `cloudcost/scripts/_normalized.py`. The live description is `cloudcost/runbook.md` §"What a
> zero-orphan account means, and what the sprint asserts instead". What is superseded is the
> **instruction**, not the record that a tripwire was armed. The BL-077 note below is unaffected.

**BL-069 armed** — the planted AWS Elastic IP was released after m2 close; the DO reserved IP was
deleted 2026-07-30. Any run that must assert ≥1 orphan needs a resource planted first; otherwise
`sprint.sh cloudcost`'s ≥1-orphan assertion is expected-red (named, tracked, not re-triaged).
**BL-077:** sprint `fail` sets no exit status — read the `[OK]`/`[FAIL]` lines, not `$?`.

## Repo state at handoff
aetheris-agents **`31c0d88`** — pushed, in sync, tree clean. aetheris `265d336`, pushed, in sync.
`drift_check --strict` exit 0 with one strict-exempt `project_knowledge` stale-WARN on
`backlog-2026-06.md` until the next export boundary; claude-code reads the backlog from git, so it
is unaffected.

## After this batch
Provider three — GCP or Linode costing, same triad, same bet. A third adapter is written against
m1's frozen §Normalized schemas + the canonical vocabulary in `cloudcost/scripts/_normalized.py`.

---

## Corrections applied at landing

The handed-over text quoted repo state at three points where the repo had moved. Recorded rather
than silently followed, and rather than committed as-is.

1. **BL-073 artifact selection said "the `.html`-producing one" / "the last `.html`-producing one
   (so docbuilder resolves to its final doc)".** This is the rule corrected in `31c0d88`, one
   commit before this handoff was written, and it is wrong in the specific direction that matters:
   **docbuilder emits no `.html` at all** (measured — `.docx` + `.pdf`), so the rule resolves
   docbuilder to *nothing*, not to its final doc. Replaced with the extension-set rule above. This
   is the correction most worth having caught: a fresh session would have implemented it verbatim,
   and the resulting bug would have looked like an absence rather than a defect.

2. **"Repo state at handoff: aetheris-agents `e9b87f8` — confirm it's pushed before starting (it
   was held for review)."** Stale on both counts: HEAD is `31c0d88` (`e9b87f8` is one behind), and
   it is already pushed — the review hold was released. Corrected in §Repo state.

3. **BL-083's "Open question: fix the hardcoded list, or re-key on the stable run_id prefix — CC to
   confirm run_id conventions."** Confirmed at landing rather than deferred into the ticket: run_id
   prefixes are regular across the last 250 runs and re-keying is strictly better, for the three
   reasons given in the row above. The decisive one is that keying on the label while this same row
   *rewrites* the label couples two things that then have to be kept consistent forever.

Also carried over from the filed rows but absent from the handoff text: BL-084 is filed wider than
cloudcost (`tools.json` is missing for docbuilder, provenance and boxy-pipeline too), and BL-083's
`api-tenant`/`api-gateway` prefix entries currently match **nothing** — they are dead entries, not
merely incomplete ones. Both are in the backlog rows; noted here so the batch's scope is not
under-read from the handoff alone.
