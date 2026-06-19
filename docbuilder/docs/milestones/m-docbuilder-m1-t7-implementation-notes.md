# m-docbuilder-m1 t7 — Implementation Notes

Ticket: t7 — docbuilder_orchestrator.exs + sprint case  
Committed: (this session)

---

## What was built

- `agents/docbuilder_orchestrator.exs` — linear pipeline orchestrator; env vars resolved at eval time; `context_strategy: :full`; tools: `run_command`, `write_file`; `max_steps: 20`
- `runbook.md` — env vars, how to run, expected output, common failure modes
- `../aetheris/scripts/sprint.sh` — `docbuilder` case added before `# Summary` section; also registered in usage line
- `--input FILE` flag added to all 7 generate_*.py scripts (backward-compatible; stdin still works when `--input` is absent)

---

## Design decisions made during implementation

### `--input FILE` added to all generate scripts — the core insight

`run_command` has no `stdin` parameter (confirmed in `registry.ex`). The generate scripts (t3–t6) all read doc spec JSON from stdin. Without a way to feed stdin, the agent cannot call them via `run_command`.

The first attempt used `sh -c "cat output/pipeline_spec.json | python3 scripts/generate_xlsx.py ..."`. The LLM did not follow this pattern reliably — at step 13 it called `python3 scripts/generate_xlsx.py` directly (without the shell pipe), which blocked waiting for stdin and timed out. The run hit max_steps (15) before any output files were produced.

The clean fix: add `--input PATH` as an optional argument to all 7 generate scripts. When `--input` is provided, the script reads from that file; when absent, it falls back to stdin (preserving full backward compatibility and all t3–t6 tests passing). The orchestrator then calls each renderer with explicit `--input output/pipeline_spec.json`, which the LLM follows reliably.

This change touches t3–t6 scripts. The modification is a single, uniform 2-line delta in each `main()`:
```python
parser.add_argument("--input", default=None, ...)
src = open(args.input, encoding="utf-8") if args.input else sys.stdin
```

All 123 existing tests continue to pass (they don't pass `--input`, so they exercise the stdin path as before).

### Pipeline flow with temp files

The orchestrator uses two intermediate files, both written with `write_file`:

```
fetch_data.py → output/pipeline_raw.json
compute_doc.py (reading pipeline_raw.json) → output/pipeline_spec.json
generate_{fmt}.py --input output/pipeline_spec.json → output/{filename}.{fmt}
```

This makes each step inspectable after the run and avoids any pipe-chain coordination problem. The intermediate files persist because `overlay_base_dir: nil`.

### `write_file` in the tools list

The guide says "orchestrators almost never need write_file." This orchestrator is the exception: it must write the fetch output and computed doc spec to files so downstream `run_command` calls can read them. The justification is documented here rather than in the code.

### `context_strategy: :full` confirmed correct

The pipeline is: 4 setup steps (fetch, write, compute, write) + N render steps (2 for the demo template). Total steps is well under 10. `:full` keeps the full message history visible to the LLM, which helps it track which formats it has already processed.

### max_steps: 20 (raised from 15)

The first attempt hit max_steps at 15. The pipeline consumes approximately:
- 1 LLM reasoning step before each tool call
- 4 setup tool calls (fetch, write_raw, compute, write_spec)
- 1 LLM step to read output_formats from the doc spec
- 2 render calls (xlsx, pdf for demo template)

That's ~12 steps minimum with no retries. 20 gives comfortable headroom for longer format lists or a single LLM retry step.

### `run_id` not surfaced in sprint output

The sprint run output contains log noise before the JSON line (`{"label":"...","status":"done","run_id":"..."`), so `jq -r '.run_id // empty'` fails when used against the raw output file. The sprint.sh reports `Run ID: n/a` but the actual ID is in the file. This is a sprint.sh display issue, not a pipeline issue. The run ID can be retrieved manually with `mix aetheris list --limit 5`. Flagged for t8 docs sync.

### Env vars and raise on missing values

All four `DOCBUILDER_*` vars use `|| raise "..."`. This means the syntax check (`mix run --eval`) requires the env vars to be set. The sprint.sh sets them as defaults before both the eval and the run. This matches the done-check pattern — the sprint.sh passes defaults so the eval always succeeds.

---

## Known limitations

- **`proposal_v1` filename suffix includes the version**: `DOCBUILDER_DOC_TYPE=proposal`, `DOCBUILDER_VERSION=v1` → filename is `proposal_v1`. This is deliberate (version in filename avoids silent overwrite on template upgrade). Document this convention in the runbook.
- **run_id not captured in sprint output**: see §"run_id not surfaced" above.
- **Intermediate files not cleaned up**: `output/pipeline_raw.json` and `output/pipeline_spec.json` persist after each run, overwritten on the next. A `--cleanup` flag on the orchestrator is m2 scope.

---

## t8 notes

- Add the per-renderer `--input` behaviour to `docs/doc-spec-schema.md` under §"Renderer contract" — all renderers now accept `--input FILE` in addition to stdin.
- The run_id display issue in sprint.sh warrants a fix — the `jq` call should extract from the last JSON line of the output file, not assume the whole file is JSON.
- `docbuilder/README.md` open questions: all should be resolvable now that the full pipeline is running.
- The per-renderer format characteristics table (merge_ranges, row types, bold, alignment) is a t8 addition to `doc-spec-schema.md`.
