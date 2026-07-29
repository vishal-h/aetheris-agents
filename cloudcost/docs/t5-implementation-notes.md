# t5 — orchestrator `.exs` + sprint case + end-to-end — implementation notes

**Ticket:** m1-cloudcost §t5. **Built:** 2026-07-29.
**Deliverables:** `cloudcost/agents/cloudcost_orchestrator.exs`,
`aetheris/scripts/sprint.sh` (new `cloudcost` case + `cap-matrix-cloudcost` line),
`agents/capability_matrix_cloudcost.exs`, `agents/capability_matrix_assemble.exs` (wired),
`docs/capability-matrix.md` (regenerated), `cloudcost/milestone.md` §t5 (corrected).
**Live run:** `cloudcost-orch-qPCKmw` — real DO bill, record mode, 4 steps, 1 orphan.

---

## Decisions

**`context_strategy: :full`, not §t5's `:rolling`/6 — and §t5 corrected in the same commit.**
Ratified by the human before the build. Two reasons, both structural: the guide's
`:full`-for-under-~10-step-pipelines rule applies (this is four steps), and the workflow
*threads file paths forward* — STEP 2 needs STEP 1's `files.inventory`, STEP 3 needs STEP 1's
`files.costs` **and** `files.inventory` **and** STEP 2's output. A rolling window of 6 would
begin discarding exactly the messages carrying those paths, and the failure mode is not a
crash but a fabricated filename. The milestone doc now reads `:full` with that rationale
inline, so the next reader is not adjudicating this again.

**The stop condition is `status: "error"`, not a non-zero exit — a deliberate divergence from
the docbuilder orchestrator.** Docbuilder's rule is *"if any script returns exit code 1,
report its stderr and stop"*. Copying it here would have broken the pipeline on healthy runs:
every cloudcost stage `exit 1`s on a **partial** (`{"status": "partial"}` with the output file
written), which is the repo's stage-CLI contract — "stage CLIs degrade, they don't crash".
A `--cost` file that could not be fetched, one unparseable inventory row, a missing prior
snapshot: all partials, all still produce a report. So the prompt separates the two axes
explicitly — *"`partial` is NOT a failure … These scripts exit non-zero on a partial run by
design; the output file was still written"* — and fails only on `status: "error"` or a missing
output path. **Not exercised by this run** (all four stages returned `ok`/exit 0); it is a
prompt rule verified by reading, not by firing. Named here rather than implied.

**STEP 3 ships two arg vectors verbatim instead of asking the LLM to edit an array.**
`fetch_do.py` omits `files.costs` from its stdout when billing is unavailable
(`fetch_do.py:566-568` writes the key only when `costs is not None`). `compose_report_data.py`
accepts an omitted `--cost` — its arity check rejects only *mismatched non-zero* counts
(`compose_report_data.py:760-775`), and the bundle degrades to a skipped entry. Rather than
"drop the flag if absent", which invites improvisation, the prompt prints both full commands
and says which to use. The LLM picks; it never edits.

**`provider`/`model` are literals, breaking the sibling agents' env-override idiom.** Every
other agent here does `System.get_env("AETHERIS_MODEL") || "claude-haiku-…"`. sprint.sh sources
`aetheris-agents/.env`, so an `AETHERIS_MODEL` there would silently change the model —
and the stub-guard done-check asserts `resolved_model == "claude-haiku-4-5-20251001"`. An
overridable value would make that assertion assert nothing in particular. §t5 names both
literally; they stay literal.

**`--history-dir` is omitted at STEP 3.** Its default is `__file__`-anchored to
`cloudcost/history` (`compose_report_data.py:86`) and is already correct; passing it would add
a path the LLM could get wrong for no gain.

---

## Deviation: §t5's `agents/capability_matrix.exs` does not exist

§t5 says *"regenerate the capability matrix (`agents/capability_matrix.exs`)"*, and
`docs/capability-matrix.md`'s own header said the same. There is no such file, and there is no
evidence there ever was. The matrix is produced by **nine per-use-case section agents**
(`agents/capability_matrix_{uc}.exs`, each writing `docs/.sections/{uc}.md`) plus
`agents/capability_matrix_assemble.exs`, driven by sprint.sh's `capability_matrix` case.

The ticket's *invariant* — cloudcost registers in the matrix — holds; its *sketch* does not.
Implemented as the invariant: a new `capability_matrix_cloudcost.exs`, three edits to
`capability_matrix_assemble.exs` (Step 1 read list, paste slot, Summary row), and one
`run_agent` line in the sprint case. The stale header line in the generated artifact is also
corrected, since it was the source of the bad pointer.

**Rig reads the regenerated artifact, not a re-scan** — settled by reading
`rig/src-tauri/src/commands/capability_matrix.rs:30-42`: `capability_matrix_load` reads
`$AETHERIS_AGENTS_PATH/docs/capability-matrix.md` and parses its `##` / `### Agents` /
`### Scripts` tables. So the regen *is* the mechanism that surfaces cloudcost in Rig's matrix
view; no Rig code change is needed or was made.

---

## Fixture state cleared before the live run (two silent-green traps)

Both are the **Silent-wrong-answer** shape — a check that passes identically whether or not
the thing under test worked.

1. **`output/cloudcost_report_2026-07.html` already existed**, left by the t4 fixture run. The
   sprint case's `[[ -f "$CLOUDCOST_REPORT" ]]` would have reported `ok` for a stale file even
   if the agent had never run. The whole of `cloudcost/output/` was moved aside first, so the
   artifacts checked are the ones this run produced (all five carry the run's timestamp).
2. **`cloudcost/history/{2026-06,2026-07}` held fixture snapshots** ($158.00 / $172.21) from
   t3/t4. Left in place, the live run would have computed a month-on-month delta of real July
   against a **fabricated** June and printed it in the deliverable. Moved aside, so the first
   real run reports `mom_delta.status: "no_prior_month"` — the honest first-run path. Both
   directories are gitignored; they are preserved in the session scratchpad.

Milestone prerequisite 1 also re-checked in the run shell: `DO_TOKEN` and
`DIGITALOCEAN_ACCESS_TOKEN` both empty, `CLOUDCOST_DO_TOKEN` set — no write token could shadow
the read-only one.

---

## Done-check (§t5) — evidence

| §t5 clause | Result |
|---|---|
| `.exs` evaluates without error | exit 0, no output |
| `./scripts/sprint.sh cloudcost` runs and finds the report | `report: cloudcost_report_2026-07.html (14K)` |
| End-to-end on the real DO bill (record) | `cloudcost-orch-qPCKmw`, status `done`, 4 steps |
| **≥1 orphan with its evidence** | 1 — reserved IP `168.144.13.150`, HIGH (0.95), $4.38/mo |
| Reviewable without the DO console | orphan section renders id, type, region, `raw_ref`, rule, confidence + base + modifiers, evidence line, saving |
| `CLOUDCOST_DO_TOKEN` nowhere in the trajectory | 0 occurrences (full token, both 12-char fragments, and the var name) |
| Matrix lists cloudcost | `## Cloudcost` — 1 agent, 5 scripts |
| Rig `CapabilityMatrix` data source | regenerated artifact (`capability_matrix.rs:30-42`) |

**The agent executed exactly four commands, all `run_command`, arg-for-arg as written** — no
scratch script, no re-run-to-inspect, no `write_file` (it has no such tool):

```
1. python3 ["scripts/fetch_do.py", "--output-dir", "output"]
2. python3 ["scripts/detect_orphans.py", "output/do_inventory_2026-07.json", "--output-dir", "output"]
3. python3 ["scripts/compose_report_data.py", "--cost", "output/do_costs_2026-07.json",
            "--inventory", "output/do_inventory_2026-07.json",
            "--orphans", "output/orphan_candidates_2026-07.json", "--output-dir", "output"]
4. python3 ["scripts/render_report.py", "output/report_data_2026-07.json", "--output-dir", "output"]
```

**Guard (a) — real Anthropic adapter, not the stub fallback.** A `[stub exhausted]` run
completes `:done` with zero latency and produces nothing; it is indistinguishable from success
in the sprint's own output. Five `llm_responded` events, `latency_ms` 2318 / 1802 / 1596 /
1872 / 1608, `resolved_model` `claude-haiku-4-5-20251001` on every one, `[stub exhausted]`
count 0.

**Guard (b) — token containment (D2).** The 71-char token, its first and last 12-char
fragments, and the literal string `CLOUDCOST_DO_TOKEN` all appear **0** times in
`priv/runs/cloudcost-orch-qPCKmw/trajectory.json`, and 0 times in the sprint `run.json` and all
five output artifacts. The token reaches `fetch_do.py` through the process environment only.

**Live figures** (real account): $185.50 grand total, 3 services, 19 resources, 84.21 % tag
coverage, 3 untagged, 1 orphan candidate at $4.38/mo estimated, `mom_delta: no_prior_month`,
zero warnings, zero skipped inputs.

---

## Open items forwarded

**BL-067 — the assembler does arithmetic in the LLM.** `capability_matrix_assemble.exs` Step 3
asks the model to *count* agents and scripts. It got it wrong twice in a row on identical
inputs (`docbuilder 27 · Total 27/70`, then `docbuilder 25 · Total 27/68`; actual, counted from
the emitted rows, `docbuilder 24 · Total 26/67`). This violates the repo's core principle
directly, and it is a Silent-wrong-answer inside a generated artifact nobody recounts. t5
hand-corrected the three numbers to the verified values and filed BL-067 for the real fix (a
deterministic counter script the assembler pastes verbatim). Backlog row filed this round, per
the "a deferred finding gets a row in the same round" rule.

**Partial-path unexercised.** The `status: "partial"` continue-don't-stop rule (above) has
never fired in a live run. The cheap exercise is a run with billing unavailable; it needs a
way to fail the billing call without a write op, so it is not free.

**`docs/.sections/` is gitignored, so a full regen is destructive.** Re-running all nine
section agents rewrote every section — reordering rows, rewording purposes, and dropping the
hand-curated m3/m5/m6 provenance annotations from the docbuilder table — a 121-line diff for a
one-section addition. The prior three matrix commits are 1–6 line diffs, i.e. previous sessions
regenerated only the changed section. That practice is correct and undocumented; the sections
were reconstructed from `HEAD:docs/capability-matrix.md` and only `assemble` re-run, giving the
intended 34/5 diff. Worth writing down somewhere the next milestone-close will read.
