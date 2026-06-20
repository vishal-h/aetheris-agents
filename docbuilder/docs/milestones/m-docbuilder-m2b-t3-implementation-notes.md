# Implementation notes — m-docbuilder-m2b t3

Ticket: `fetch_data.py --output FILE` + orchestrator PHASE A hardening (scratch → 0).

---

## What shipped

- `fetch_data.py`: `--output FILE` (default None). Present → write the raw JSON to the
  file, print only the path; absent → print JSON to stdout (unchanged). Backward-compatible,
  same pattern as `compute_doc.py --output` (m2a t10).
- `docbuilder_orchestrator.exs`: PHASE A fetch steps use
  `--output output/pipeline_raw_{key}.json` and the per-source `write_file` step is gone
  (PHASE A is now N run_commands, not 2N). Strengthened the "don't investigate" rule.
- `tests/test_fetch_data.py`: +1 (`--output FILE` writes file, stdout is the path only,
  file holds valid JSON).
- Tests: 9 in test_fetch_data; full suite green.
- **Sprint re-run (run `docbuilder-orch-kW_70A`, status `done`): scratch artifacts = 0.**

---

## Decisions

**`write_file` removed from the orchestrator tools list.** t3's PHASE A change was the
last `write_file` user: PHASE A now fetches with `--output`, PHASE B computes with
`--output` (m2a t10), PHASE C renders with `--input`/`--output-dir`. With no phase
writing files via `write_file`, the tool is dead capability, so `tools` is now
`["run_command"]`. This is the clean consequence of the `--output` pattern and supports
the scratch→0 goal (one fewer tool the LLM can misuse). The negative reminders
("Do NOT write_file …") remain in the step text as harmless reinforcement.

**Strengthened the "don't investigate" rule.** The m2a t10 residual scratch was the LLM
running `compute_doc` a second time (bare) to *view* the spec. The rule now reads: "Each
`--output FILE` call writes its result directly to that file and prints ONLY the path. Do
NOT re-run a script without `--output` to view its content, and do NOT write any
helper/scratch script — use the file the script already wrote and proceed." This run
produced **zero** scratch files, so the combination (`--output` everywhere + the explicit
rule) resolved the behaviour.

**Done-check scratch check made exhaustive (location-based).** Replaced the fragile
`-newer fetch_data.py` timestamp heuristic with a location-based `find` that lists any
`.py` outside the known dirs (output/, __pycache__/, tests/, scripts/, agents/, docs/).
Any output is a scratch file. Updated in the t3 milestone done-check per reviewer note.

## Result — scratch trajectory

| Milestone point | Orchestrator scratch files |
|---|---|
| m2a t8 (write_file for spec + raw) | 8 |
| m2a t10 (compute_doc `--output`; raw still write_file) | 1 |
| m2b t3 (fetch_data `--output`; no write_file at all) | **0** |

All three branded outputs (`proposal_v1.{xlsx,docx,pdf}`) and the per-source
intermediates were produced correctly.

## Forward notes

- **t7:** PHASE A is now `--output`-based; the full orchestrator update keeps this for the
  multi-source fetch and adds the new PHASE 0/D/E/F. The `tools: ["run_command"]` change
  carries forward (the delivery scripts also use `--output`/stdout, no `write_file`).
- **t8:** no `write_file`-related capability-matrix change needed; the orchestrator row's
  tools become just `run_command` on regen.
