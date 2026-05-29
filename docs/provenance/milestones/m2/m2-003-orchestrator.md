# provenance/m2: Classification orchestrator

## Context

With the classifier sub-agent in place, we need an orchestrator that drives
classification at scale. The corpus may contain tens of thousands of unique
files — classifying them sequentially would take hours. The orchestrator
uses Aetheris's `spawn_agent` + `wait_for_all` pattern to classify in parallel.

## What to build

`agents/classification_orchestrator.exs`

### Behaviour

1. Query DuckDB for unclassified unique files:
   ```sql
   SELECT MIN(path) AS path, sha256
   FROM f2_file_index
   WHERE sha256 IS NOT NULL
     AND status != 'missing'
     AND path NOT IN (SELECT path FROM classifications WHERE status != 'rejected')
   GROUP BY sha256
   ORDER BY path
   ```
   One path per unique SHA-256 (the alphabetically first path representing that content).

2. Split results into batches of `CLASSIFICATION_BATCH_SIZE` (default: 20).

3. For each batch: `spawn_agent` with `classify_batch.exs` as the template,
   passing the file paths in `task_prompt`.

4. `wait_for_all` on all spawned run IDs with timeout
   `CLASSIFICATION_TIMEOUT_MS` (default: 600_000 — 10 minutes).

5. Report: total files queued, batches spawned, results written (from DuckDB
   count after all agents complete), any failures.

### Env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | required | DuckDB file path |
| `PROVENANCE_NAS_PATH` | required | NAS root (for sandbox_path) |
| `TAXONOMY_PATH` | `agents/taxonomy.md` | Path to taxonomy rules |
| `CLASSIFICATION_BATCH_SIZE` | `20` | Files per sub-agent |
| `CLASSIFICATION_THRESHOLD` | `0.70` | Confidence threshold |
| `CLASSIFICATION_TIMEOUT_MS` | `600000` | Per-batch timeout |

### Sub-agent spawning

Each batch is spawned via `spawn_agent` tool with:
```elixir
tools: ["read_file", "run_command"],
max_steps: 30,
task_prompt: """
Classify the following files...
[file list for this batch]
"""
```

The orchestrator does not inspect individual file content — that is entirely
the sub-agent's responsibility.

### Error handling

If a batch sub-agent fails or times out:
- Log which files were in that batch (from the orchestrator's context)
- Continue with remaining batches — do not abort the full run
- Include failed batch count in the final summary

At the end, report how many files remain unclassified (still query DuckDB).
The orchestrator can be re-run safely — already-classified files are skipped
by `classify_documents.py`.

## Acceptance criteria

- [ ] Agent evaluates without error
- [ ] Test run against `tests/fixtures/sample_corpus.duckdb` completes with
  `agent_finished` reason
- [ ] Spawns correct number of sub-agents (ceil(unique_files / batch_size))
- [ ] All spawned run IDs appear in `wait_for_all` call
- [ ] `classifications` table populated after run
- [ ] Re-run is a no-op (already classified files skipped)
- [ ] Agent handles sub-agent failure gracefully (does not crash)
- [ ] env vars documented in `docs/provenance/runbook.md`

## Files to create/modify

- `provenance/agents/classification_orchestrator.exs`
- `docs/provenance/runbook.md` (add classification orchestrator section)

## Notes

**Scale estimate.** A corpus with 50,000 unique files at batch size 20 produces
2,500 sub-agents. `wait_for_all` collects all of them. At ~30 seconds per batch
(20 files × ~1.5s per read_file + classification), with full parallelism this
is ~30 seconds wall-clock time. In practice, parallelism is limited by Aetheris's
`max_spawn_depth` and available LLM rate limits.

**Token budget.** Each sub-agent reads 20 files × ~500 chars excerpt = ~10K
chars of content, plus taxonomy (~2K tokens), plus prompt overhead. Total
~15K tokens input per batch. At 100 batches, this is ~1.5M input tokens.
Budget accordingly — Haiku is strongly preferred for this workload.

**Dry run.** Add a `DRY_RUN=true` env var check at the start of the agent:
if set, query and report how many files would be classified and how many
batches would be spawned, but do not spawn any agents. Useful for estimating
cost before a full run.

Follow the `uc-payslip` orchestrator pattern from `docs/agent-creation-guide.md`.
The parallel sub-agent + `wait_for_all` shape is identical.
