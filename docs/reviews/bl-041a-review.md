# BL-041(a) — review packet (light)

**Ticket:** BL-041(a) — §7 promotion: the manifest-staleness done-check runs post-commit.
Docs-only edit to `aetheris-agents/CLAUDE.md`.
**Commit:** `1013a95` (agents `main`), **push held**.
**Base:** agents `f624337`, harness `af56a57`. Ratified §7 wording:
`docs/reviews/bl-041a-promotion-draft.md`. Notes:
`docs/rig/milestones/bl-041a-promotion-implementation-notes.md`.

Two edits, both verbatim from the ratified draft, both in the "Definition of done — doc sync"
section: (1) the new learning rule after the strict-mode exemption paragraph; (2) the "When to
run" reconciliation. One placement divergence was caught and resolved before editing — the
draft's original "after the Silent-wrong-answer rule" anchor is in the **harness** `CLAUDE.md`,
not this repo; the human chose the doc-sync-section placement (see notes). Scope held:
strict-mode exemption, `drift_check.py`, and all other rules untouched.

---

## 1. Diff — `CLAUDE.md` (`1013a95`)

```diff
commit 1013a955f388151d64f9307318c0961d0719189c
Author: Vishal Honnatti <vishal@bitloka.com>
Date:   Sat Jul 25 07:45:29 2026 +0530

    BL-041(a): promote — manifest-staleness done-check runs post-commit (§7, CLAUDE.md)
    
    Two edits to aetheris-agents/CLAUDE.md's "Definition of done — doc sync"
    section, verbatim from the human-ratified §7 draft:
    
    1. New learning rule (after the strict-mode exemption paragraph): a
       drift_check --strict before committing a manifest-tracked edit is vacuous —
       check 8 (project_knowledge) compares the manifest against committed history,
       so pre-commit it reads the pre-edit hash and can't see the staleness the edit
       introduces (the Silent-wrong-answer class, gate-ordering form). Run --strict
       post-commit; name the exempt project_knowledge staleness WARNs.
       Source: BL-034 (fe8298c, latent), BL-025 (8021a59/00ddd34, fired: 1→3 WARN).
    
    2. "When to run" reconciled: zero *unexplained* WARN findings; the
       project_knowledge portion is meaningful only post-commit; checks 1–7 remain
       valid pre-commit.
    
    Placement divergence caught and resolved: the draft first anchored Edit 1 "after
    the Silent-wrong-answer rule", which lives in the HARNESS CLAUDE.md, not this
    repo. Reported rather than forced (the section's own text-vs-repo rule); human
    chose the doc-sync-section placement, and the rule keeps Silent-wrong-answer as
    an explicit harness cross-reference.
    
    Scope held: strict-mode exemption, drift_check.py, and all other rules untouched
    (the tooling guard is BL-041(b), out of scope). §7 draft on record:
    docs/reviews/bl-041a-promotion-draft.md. Notes:
    docs/rig/milestones/bl-041a-promotion-implementation-notes.md.
    
    Full restart due after this (CLAUDE.md learning-section change); the
    manifest/export is the next session's work, not this one's. Push held.
    
    Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

diff --git a/CLAUDE.md b/CLAUDE.md
index af2e8eb..771fd20 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -213,7 +213,11 @@ routes (registry.ts ↔ App.tsx), payload field sampling (live DB ↔ specs.md 
 milestone README Status: lines.
 
 **When to run:** after any Rig milestone, after adding commands, event types, env vars,
-routes, or DB tables. Zero FAIL findings and zero WARN findings required before committing.
+routes, or DB tables. Zero FAIL findings and zero *unexplained* WARN findings required — for a
+**manifest-tracked** edit the `project_knowledge` (check 8) portion is meaningful only
+**post-commit** (it reads committed history; see the learning rule below), so run the `--strict`
+done-check after that commit and name the expected `project_knowledge` WARNs. Checks 1–7 remain
+valid pre-commit.
 
 **Strict mode (`--strict`, BL-009).** The sprint runs `drift_check.py --strict`: any
 WARN fails the sprint, so drift cannot accumulate into the next alarm-fatigue cycle.
@@ -226,6 +230,18 @@ manifest-staleness WARN in day-to-day output is the signal we chose to keep, not
 regression to chase. Structural manifest problems (missing manifest, unknown repo, git
 failure) are **not** exempt and still fail under `--strict`.
 
+**A manifest-staleness done-check runs post-commit — a `drift_check --strict` before committing a
+manifest-tracked edit is vacuous.** Check 8 (`project_knowledge`) compares the manifest against
+committed history (`git log -1 --format=%h -- <file>`), so run *before* the commit it reads the
+file's pre-edit hash and cannot see the staleness the edit introduces — it passes green where a
+gap exists (the **Silent-wrong-answer** class — harness `CLAUDE.md` — in gate-ordering form). Run the `--strict`
+done-check *after* the commit that touches a manifest-tracked file, when check 8 can compare the
+new commit hash against the manifest; then **name** the exempt `project_knowledge` staleness
+WARNs rather than chasing them (mid-cycle staleness is expected truth, cleared only at the export
+boundary — the strict-mode exemption above). Checks 1–7 (source-vs-doc) remain valid pre-commit;
+it is check 8's committed-history dependency that forces the ordering.
+`Source: BL-034 (fe8298c — the export-prompt self-staling ordering hazard, real but latent; its "628f15f production-fired" claim withdrawn as false after a clean check-8 sweep of all 38 committed manifests), BL-025 (8021a59/00ddd34 — the vacuity fired on the caveat's own author: pre-commit 1 WARN, post-commit 3).`
+
 **Ticket text that quotes repo state** (counts, paths, expected outputs) cites the commit
 it was verified against; claude-code treats divergence between ticket text and repo reality
 as a deviation to note, never to silently follow. Source: BL-001, BL-015, BL-002.
```

---

## 2. Post-commit `drift_check --strict`

Run **after** the commit, following the rule just landed — a pre-commit run reads the pre-edit
hash and cannot see the staleness the edit introduces.

```
Rig doc-drift checker — 8 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 48 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[WARN] project_knowledge: CLAUDE.md stale — manifest=c2729ac current=1013a95
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=f0df85a current=f624337
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=a935038 current=8021a59
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=9b2b102 current=af56a57

Summary: 7 PASS  0 FAIL  4 WARN  7 INFO

exit=0
```

**0 FAIL, exit 0.** All four WARNs are `project_knowledge` manifest staleness — the standing
strict-mode exemption. The **`CLAUDE.md stale — manifest=c2729ac current=1013a95`** WARN is the
one this commit introduced, and it is the rule demonstrating itself: it is invisible to a
pre-commit check (which would read the pre-edit hash) and appears only post-commit, when check 8
compares the new commit against the manifest. Named, not chased; it clears at the next export
boundary. The other three (`backlog-2026-06.md`, `runbook.md`, `determinism-contract.md`) are
pre-existing mid-cycle staleness.

---

## 3. Restart boundary

This is a CLAUDE.md learning-section change, so a **full restart** is due now. The
manifest/export refresh (which re-stales all these entries clear, and re-authors the withdrawn
`628f15f` born-stale narrative so it is not copied forward) is the **next session's** work —
not started here. **Push held.**
