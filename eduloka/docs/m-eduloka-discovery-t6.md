# t6 — Orchestrator agent + harness wiring

> Ticket extracted from `eduloka/milestone.md`. Canonical source is
> `milestone.md`; this file is a working reference for implementation.

**Depends on.** t1–t5 merged.

**Scope.** After this ticket `agents/eduloka_orchestrator.exs` drives the full
pipeline (fetch → map → enrich → upsert) over a term list using `run_command` +
`spawn_agent` + `wait_for_all`, a capability-matrix agent file exists, and a
`sprint.sh` case runs the pipeline end-to-end against fixtures. The term list is
loaded from a committed, editable config file (`data/terms.txt`) via
`list_terms.py` — never hardcoded in the agent.

**Contract refs.** `docs/agent-creation-guide.md` §"Orchestrator patterns",
§"Standard RunConfig fields", §"Runtime parameters in orchestrators",
§"Pre-flight checklist"; `aetheris-agents/CLAUDE.md` §"Agent files",
§"Sprint script".

**Touches.** `eduloka/agents/eduloka_orchestrator.exs`;
`eduloka/scripts/list_terms.py`;
`eduloka/data/terms.txt` (committed config — note this path is NOT in the
`.gitignore` layer-dir excludes); `eduloka/tests/test_list_terms.py`;
`agents/capability_matrix_eduloka.exs` (repo-root agents dir);
`aetheris/scripts/sprint.sh` (new case before `# Summary`);
`eduloka/runbook.md` (terms file + term selection + provider selection).

**Do not generate.** LLM does not construct file content or compute values —
scripts do, the agent orchestrates. No `read_file`/`write_file` in the tool set.
Include the "report failures and stop" rule.

**Runbook update rule.** Introduces the terms-file config (`data/terms.txt`,
overridable via `EDUX_TERMS_FILE`) and the `SEARCH_PROVIDER` selection per run.
Document the terms file (how to edit it) and the run invocation.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_list_terms.py -q
python3 eduloka/scripts/list_terms.py | python3 -c "import json,sys; assert json.load(sys.stdin)['count'] >= 1"
mix run --eval 'Code.eval_file("eduloka/agents/eduloka_orchestrator.exs")'
cd ../aetheris && ./scripts/sprint.sh eduloka
```

**Claude-code prompt.**
> Write `eduloka_orchestrator.exs` as a `RunConfig` per agent-creation-guide
> §"Standard RunConfig fields" (`__ENV__.file` sandbox_path, `overlay_base_dir:
> nil`, minimal sub-agent tools, "report failures and stop"). The term list is
> obtained by `run_command` into `list_terms.py` (reading `data/terms.txt`) —
> the agent must not hold or hardcode terms. Spawn one fetch→map→enrich→upsert
> sub-agent per returned term; `wait_for_all`. Provider via the
> runtime-parameter pattern (default `cse`). Add `list_terms.py`, a seed
> `data/terms.txt`, `capability_matrix_eduloka.exs`, and a `sprint.sh` case on
> committed fixtures (no live API). Walk the pre-flight checklist. Run the
> done-check; include output.

**Spike reference.** `list_terms.py`, `terms.txt`, `test_list_terms.py` — at
`/tmp/eduloka/` (reference only). The orchestrator `.exs` is greenfield.

**Implementation notes.** → `eduloka/docs/t6-implementation-notes.md` (write
after ticket closes).
