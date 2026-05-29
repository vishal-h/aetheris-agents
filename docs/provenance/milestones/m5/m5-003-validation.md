# provenance/m5: Validation + eval task

## Context

The search agent needs to be validated against real-world queries before
auditors rely on it. This issue builds the validation scaffolding: a set of
representative test queries, a script to measure pass rate, and an Aetheris
eval task definition so regression can be detected after future changes.

## What to build

### `scripts/validate_search.py`

Runs a set of test queries against the search agent and measures pass rate.

```
python3 scripts/validate_search.py \
  --db /data/corpus.duckdb \
  --queries tests/fixtures/search_queries.json \
  [--model claude-haiku-4-5-20251001] \
  [--n 1]
```

For each query:
1. Run `search_agent.exs` with that query via `mix aetheris run`
2. Check the trajectory for `tool_called` events with `search_corpus`
3. Parse the agent's final text response for result paths
4. Compare against `expected_paths` in the query fixture (if provided)
5. Score: pass if ≥1 expected path appears in the response, or
   if `expected_paths` is empty and ≥1 result is returned

Output JSON:
```json
{
  "total": 20,
  "passed": 18,
  "failed": 2,
  "pass_rate": 0.90,
  "results": [
    {"query": "...", "passed": true, "result_count": 5, "run_id": "..."},
    ...
  ]
}
```

Exits 0 if pass_rate ≥ threshold (default 0.85), exits 1 otherwise.

### `tests/fixtures/search_queries.json`

20 representative queries covering the range of real auditor needs.
Format:
```json
[
  {
    "query":          "tax returns for acme FY2024",
    "expected_paths": [],
    "notes":          "Basic metadata search — client + FY + type"
  },
  {
    "query":          "legal notices from globex",
    "expected_paths": [],
    "notes":          "Client + doc_type filter"
  },
  {
    "query":          "balance sheet 2022",
    "expected_paths": [],
    "notes":          "Content keyword + year"
  },
  ...
]
```

`expected_paths` is empty for most queries (we don't have the real corpus yet).
The validation script counts a pass if ≥1 result is returned and the agent
doesn't report "no documents found".

When the real corpus is available, `expected_paths` can be populated with
known correct answers for precision measurement.

### Query categories (20 total)

| Category | Count | Examples |
|----------|-------|---------|
| Client + FY | 4 | "acme FY2024", "globex FY2023 documents" |
| Client + doc_type | 4 | "legal notices globex", "acme tax returns" |
| Content keyword | 4 | "balance sheet 2022", "court notice" |
| FY only | 2 | "all documents from FY2022" |
| Doc type only | 2 | "all legal documents", "all tax returns" |
| Multi-term | 2 | "acme FY2024 tax GST" |
| No-results (expected) | 2 | gibberish queries that should return 0 results gracefully |

### Eval task registration

Add `provenance_search` to the Aetheris eval suite via
`Eval.Tasks.Builtin` (or a separate provenance eval tasks file if the
builtin suite is not extended):

```elixir
%EvalTask{
  name:        "provenance_search",
  description: "Search agent returns results for a basic corpus query",
  run_config:  %{
    provider:      "anthropic",
    model:         "claude-haiku-4-5-20251001",
    tools:         [],
    mcp_servers:   [...corpus_search_server...],
    max_steps:     10,
    user_prompt:   "Find all documents for client acme from FY2024"
  },
  outcome_spec: %{
    type:    :regex,
    pattern: "(?i)(acme|FY2024|tax|legal|accounts)"
  }
}
```

This allows `mix aetheris eval run provenance_search` and regression
detection via `mix aetheris eval compare provenance_search`.

## Acceptance criteria

- [ ] `search_queries.json` contains exactly 20 queries across all categories
- [ ] `validate_search.py` runs all queries and produces correct pass/fail report
- [ ] Pass rate ≥ 85% against `sample_corpus.duckdb` fixture (seeded with classifications)
- [ ] No-results queries handled gracefully (agent reports "not found", not an error)
- [ ] `provenance_search` eval task registered and `mix aetheris eval run provenance_search` works
- [ ] Eval task passes on first run (confirms agent + MCP wired correctly)
- [ ] `docs/provenance/runbook.md` updated with validation instructions

## Files to create/modify

- `provenance/scripts/validate_search.py`
- `provenance/tests/fixtures/search_queries.json`
- `aetheris-agents/provenance/eval_tasks.ex` (or update `Eval.Tasks.Builtin` in aetheris)
- `docs/provenance/runbook.md`

## Notes

**`expected_paths` will be empty initially.** The fixture DB has known paths
but the real corpus doesn't exist yet. Design the pass/fail logic so that an
empty `expected_paths` list means "pass if ≥1 result returned" — not "pass
always". The no-results queries (last 2) should have `expected_paths: null`
as a signal to check for graceful no-results response instead.

**Seeding fixture classifications for validation.** The `sample_corpus.duckdb`
fixture needs some approved classifications for the search queries to find
anything. Add a `seed_search_fixture.py` helper that inserts approved
classifications for the known fixture paths. This is the only new fixture
work needed.

**The 85% threshold is the acceptance criterion for sign-off.** When the
real corpus is loaded and the auditors run the validation, the threshold
confirms the system is production-ready. Document this clearly in the runbook
so the sign-off process is unambiguous.
