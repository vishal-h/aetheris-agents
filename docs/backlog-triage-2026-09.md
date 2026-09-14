# Backlog triage — 2026-09

**Date:** 2026-09-14. **Covered:** both backlog files (`docs/backlog-2026-06.md`,
`docs/backlog-2026-06-closed.md`) and both roadmaps (`../aetheris/ROADMAP.md`, `ROADMAP.md`).
The census was read at agents `1ae2db1`; the closing sweep was verified at harness `ee7f529` /
agents `e6f0227` and committed at agents `09fd641`.

Each row's own dated line is the authority for its disposition or sweep verdict. This file
records the pass.

## Totals

| open before | closed | filed | open after |
|---|---|---|---|
| 163 | 11 | 1 | 153 |

153 from `python3 scripts/backlog_status.py --census` at `09fd641`.

- **Closed:** BL-007, BL-010, BL-097, BL-146, BL-220, BL-221, BL-223, BL-229, BL-232, BL-239, BL-242.
- **Filed:** BL-248.

## Dispositions (R40)

- **STANDING** — the default: open work, neither deferred nor blocked. It carries no per-row
  line, except where a row held an earlier deferral or blocking claim that the line voids.
- **DEFERRED** — a recorded decision to wait, naming what changes it.
- **RECORD-ONLY** — a collector whose Done-when is an unmade system decision: a record, not work.
- **AWAITING-RULING** — blocked on the arbiter, not unscheduled.
- **BLOCKS** — the row blocks a named milestone target that is live at HEAD.

| disposition | ids |
|---|---|
| DEFERRED | BL-037, BL-062, BL-072, BL-079, BL-080, BL-088, BL-136, BL-209 |
| RECORD-ONLY | BL-150, BL-151 |
| AWAITING-RULING | BL-032, BL-045, BL-046, BL-064 |
| BLOCKS | none |
| STANDING, with an explicit line | BL-102 (its deferral's trigger has fired), BL-195 (its blocking target `m-payslip-release` is a draft) |

## Left open by the closing sweep

| id | the clause that kept it open |
|---|---|
| BL-084 | *"descriptions match `capability-matrix.md`"* — true of none at the sweep: the matrix was regenerated and `cloudcost/tools.json` was not |
| BL-085 | *"`CLOUDCOST_AWS_*` appears nowhere in the trajectory or `config_json`"* — the key names appear in the guard's warning; per-launch selection is also still open (BL-187) |
| BL-086 | *"plus `detect_optimization_signals` when `CLOUDCOST_OPTIMIZATION=1`"* — no recorded run has exercised it, and it has no owner or closing condition |
| BL-103 | the first clause — the writer of `claude/aetheris-agents--inbox-brief.md` is still inferred, and whether it persists is recorded nowhere |
| BL-133 | face 1 — reviews remain session artifacts; R2 binds `hc-*` tickets only |
| BL-145 | the first and third clauses — the `## Suggested order` table is neither retired nor derived, and its sequencing opinion has no disposition |
| BL-153 | ruling 1's closing condition — a failed credential gate does not mark the run directory as not current |
| BL-190 | the sweep owed with the fix — `cloudcost/tests/test_fetch_linode.py`'s seam test pins no reference date, though BL-205's close says every cross-stage test does |
| BL-236 | *"the serving path takes an explicit entry list only from the gate and from nowhere else"* — `Runner.run_task/2` accepts `:skill_measurement` from any caller |

## Roadmap reconciliation

Read at harness `1c717cf`, agents `1ae2db1`. `:N` citations into the backlog files are line
numbers at that commit. Later, at `09fd641`, BL-007 was closed, so H1.hdr and D5 describe the
state before that commit, and C1/D4's answer was filed as BL-248. The tables below are copied
unchanged from the triage review packet's §3.

## (a) Harness `ROADMAP.md` (last touched `481ae2a`, 2026-08-12)

| # | Item | Verdict | Establishing citation |
|---|---|---|---|
| A1 | BL-001 / BL-015 / BL-002 | done | agents `docs/backlog-2026-06-closed.md:101`, `:127`, `:176`, each `**Status:** DONE` |
| A2 | BL-003 orphan sweep | done | closed `:232` DONE |
| A3 | BL-005 TrajectoryView fallback | done | closed `:761` DONE |
| A4 | BL-009 drift_check `--strict` | done | closed `:2796` DONE |
| A5 | BL-004 per-run token totals | done (row) | closed `:318` DONE; its body `:323` records "token totals did not" land in the run list |
| A6 | BL-006 `stop_reason` trigger | still true | agents `docs/backlog-2026-06.md:365` OPEN, event-triggered |
| H0.1 | `caused_by` on Event | partly done | field at `lib/aetheris/trajectory/event.ex:12` since `f80521e`; set nowhere (4 `lib` hits, all event.ex/file.ex); 0 hits in `rig/src` (control: `fork_run` hits `rig/src/hooks/useFork.ts:38`) |
| H0.2 | `observation` convention | still true | 0 hits in `docs/agent-creation-guide.md` (control `run_command`: 16); m14 doc `:125` ":observation is emitted nowhere"; BL-206 OPEN `:9171` |
| H0.3 | Token-cost aggregation query | still true | no run record; `research/prewalk-trajectory-handoff-2026-08.md:66` predicts it, `legion-code-mode-2026-08.md:93` waits on it |
| H1.1 | `fork_run(run_id, step)` | done | `lib/aetheris.ex:73`; `lib/aetheris/execution/fork.ex` |
| H1.2 | Determinism contract in §3 language | partly done (not fully checked) | `docs/aetheris/determinism-contract.md` exists (cited by BL-223 `:9928`); §3-language not verified |
| H1.3 | `fork_event_id` on `agent_trees` | superseded | 0 hits in `lib`/`priv`; provenance is `fork_from`/`fork_step` on RunConfig (`run_config.ex:100`) persisted to trajectory meta (BL-007 row's verified table) |
| H1.4 | Rig "Fork from here" | done | `rig/src/components/modules/harness/TrajectoryView.tsx:248` |
| H1.5 | Incremental (step-count) checkpointing | superseded | a checkpoint is already written after every `step_complete` (`lib/aetheris/execution/loop.ex:299`, since `54c2e54` 2026-05-20), pid passed at `agent/server.ex:719` |
| H1.hdr | "BL-007 closed 2026-07-20" | contradicted | BL-007 row is `**Status:** OPEN` at `docs/backlog-2026-06.md:1646`; its work shipped (row `:17-21`) |
| E1 | API authentication | partly done | `lib/aetheris/api/auth_plug.ex` (`99e3052`, constant-time `:76`) gates resume/trigger/playground; `GET /api/runs/:id` and `/trajectory` open (`router.ex:11-12`); tokens env-only (`config/runtime.exs:16`) |
| E2 | Release packaging + sandbox spike | still true | ticket doc only (`docs/aetheris/milestones/release-packaging.md`, `1b34968`); no `releases:` in `mix.exs`, no Dockerfile/`rel/` tracked; no spike record |
| E3 | Per-instance secrets | still true | `config/runtime.exs` reads env only (`:16`); no mounted-dir path |
| E4 | BL-003 prerequisite | done | closed `:232` DONE |
| E5 | IP / client-material sweep | still true | `\bE5\b` 0 hits in both backlog files and harness milestones; control: same pattern hits `research/qm-patterns-2026-08.md:72` |
| H2.0 | BL-008 / m14 as a whole | done — negative result | m14 doc `:4-5` Complete 2026-09-14, P2 kill fired, P3 not reached; `1c717cf`; BL-008 DONE closed `:8493` |
| H2.1 | `use_case` tag on skills | done | `lib/aetheris/store.ex:925` |
| H2.2 | Extraction as post-run `.exs` | done | `agents/skill_extractor.exs` (harness), m14 T5 |
| H2.3 | Sub-run segmentation by reasoning | done | `lib/aetheris/skill/segmenter.ex`; m14 §1.1 (D3) |
| H2.4 | Deterministic curator | done | `lib/aetheris/skill/curator.ex`; constants 0.65 / 100 (m14 §8 item 2) |
| H2.5 | `skill_injected` logged event | done | `lib/aetheris/skill/injector.ex:27`; m14 T2, T12 notes exist |
| H2.6 | Zero-regression gate | partly done (built, never discharged) | `lib/aetheris/skill/gate.ex`; m14 §6: no candidate passed control 2, control 1 never ran |
| H2.7 | Eval tables read-only to extractor | done | structural: `tools: []` (`agents/skill_extractor.exs:30-36`, m14-t5 notes); T3 deny-list |
| H2.8 | Open question: rows vs prompt/guide edits | superseded (settled) | D1 two channels ratified (`research/bl-008-synthesis-2026-08.md:43`, `:55`); channel (b) measured, not acted on — 95 of 104 findings restate input (m14 §7.4, §8 item 4) |
| H3.1 | Read Sen et al. | still true | only citation `research/dirge-agent-2026-06.md:184`, `:211`; no reading record |
| H3.2 | FTS5 prototype | still true | 0 hits in `lib` (only ROADMAP + dirge brief) |
| H3.3 | Rust vector sidecar (conditional) | still true | conditional on H3.2, unreached |
| H3.4 | Determinism treatment up front | still true | conditional, unreached |
| H3.5 | Semantic facts table | still true | no facts table in `lib`/`priv`; control: `CREATE TABLE IF NOT EXISTS skills` hits `store.ex:915` |
| Ref | "activegraph, universal-ingestion — cited but not yet written" (also H1/H2 `[activegraph — brief not yet written]` tags) | superseded | `research/activegraph-log-is-agent-2026-07.md` added `c195cbb`; `research/universal-ingestion-extraction-pipeline-2026-06.md` added `2c1a6b6` |

## (b) Agents `ROADMAP.md` (last touched `4339ba7`, 2026-07-16)

| # | Item | Verdict | Establishing citation |
|---|---|---|---|
| G0 | Active: "Nothing active" vs provenance-validation "Ready to start" | still true, stale framing | not a contradiction in vocabulary (Ready = Planned), but "ready, competing only for human hours" since `docs/handoffs/handoff-bl007-close-2026-07-20.md:61` with no later record — a deferral with no recorded decision |
| PV1 | Taxonomy session → `provenance/agents/taxonomy.md` | still true (not done) | file absent on disk; gitignored (`provenance/.gitignore:10`); only `taxonomy.md.example` |
| PV2 | Classification against sandbox | still true | no classification run in `priv/runs/` (runtime state: 3 name matches are random-id false positives `run_4IZiPQ`/`run_bziPsQ`/`run_-zipMQ`) |
| PV3–PV7 | Review cycle, migration, zip, search ≥85%, eval sprint | still true | sequenced after PV1; `provenance-validation` appears only in two July handoffs (`handoff-bl007-t2-design-2026-07-18.md:74`, close `:61`) |
| PV.dep | "all Provenance milestones m1–m6 (complete)" | not re-verified | `docs/provenance/milestones/m1..m6` exist; statuses not read |
| PV.env | Test sandbox available | still true | `~/sandbox/provenance-test` exists, mtime 2026-05-29 (predates every later record) |
| UI1 | uc-ingestion phases 1–5 | still true (unstarted) | 0 hits for `uc-ingestion`/`pdf_extract`/`ingestion_agent` outside ROADMAP (control incl. ROADMAP: 5) |
| UI2 | "brief not yet written" | superseded | brief added harness `2c1a6b6` |
| UI3 | "ETXTBSY-gated; Phase 1 ready once answered" | superseded | the question is answerable from code — see (c) C1 |

## (c) Cross-repo dependencies (same seven rows in both files)

| # | Row | Verdict | Citation |
|---|---|---|---|
| C1 | ETXTBSY / `spawn_agent` worker sharing | answered by code and live runs; **not answered on the record** | `File.copy!` exists only in the compile task (`lib/mix/tasks/compile/aetheris_worker.ex:46`, sole `lib` hit); `spawn_agent` starts an in-process `Agent.Server` (`spawn_agent.ex:161-172`), whose loop gets a worker client (`server.ex:719`) that `Port.open({:spawn_executable, …})`s the existing priv binary (`worker/client.ex:241-243`) — exec, no write; runtime: `docbuilder-orch-3qwZ9g` child `run_lACAeA` made 17 `run_command` calls, `docbuilder-ctx-orch-WRNyiQ` child `run_O0_s9w` 6. No backlog row records it (ETXTBSY/"worker sharing" 0 hits in both backlogs; control `spawn_agent`: 18); `research-reconciliation-2026-07-26.md:138` still calls it unanswered. ETXTBSY remains real for a nested `mix` inside a run (`agents/skill_extractor.exs:32`) |
| C2 | `caused_by` | live | H0.1 |
| C3 | `observation` convention | live | H0.2; BL-206 |
| C4 | `skill_injected` + BL-008 | resolved | BL-008 DONE closed `:8493`; "sprint runs leave skill rows" met — 126 payslip rows (m14 §7.1); injection built and dormant |
| C5 | Semantic facts table | live, dormant both sides | H3.5; uc-ingestion phase 3 unstarted (UI1) |
| C6 | E5 IP sweep | live | E5 |
| C7 | Pilot delivery (Tier A) | not established | no repo evidence either way |

## (d) What m14 established that is absent from the roadmaps

| # | Gap | Basis for wording (not an edit) |
|---|---|---|
| D1 | Harness Completed "Skill store schema + `extract_skill` API (write path only; operationally empty) \| m04" is false now | schema extended (`store.ex:1378` use_case/status/content_hash/superseded_by/approved_by); `lib/aetheris/skill/` segmenter/curator/gate/frequency_prior/injector/consultation; Rig `SkillsView.tsx`; populated table (m14 §7.1). Basis: "skills pipeline built end-to-end through index injection, table populated, machinery dormant — m14, negative result (P2 kill, P3 not reached)"; m04's extractor survives pending BL-224 |
| D2 | Horizon 2 still under Planned | move to Completed with the negative verdict and m14 §7.5's two reopen conditions: a corpus with real tool-sequence variance, or a control testing prose novelty |
| D3 | m14's follow-on rows unrepresented | BL-223 (body substrate, gates P3) OPEN `:9926`; BL-224 (retire m04 extractor) OPEN `:9992`; BL-219 (reflector findings); BL-206 (`:observation`) |
| D4 | ETXTBSY answer | C1 belongs in both cross-repo tables and unblocks uc-ingestion's orchestrator-design precondition |
| D5 | BL-007 row/roadmap disagreement | harness says closed 2026-07-20; row OPEN `:1646` |
| D6 | Agents roadmap is two months stale (outside m14, noted only) | Completed omits cloudcost, docbuilder, eduloka, boxy-pipeline, provenance m1–m6, Rig; registry `docs/use-cases.md` has the rows; roadmap last touched `4339ba7` |
