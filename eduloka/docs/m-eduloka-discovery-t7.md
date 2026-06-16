# t7 — Datalake readiness (partitioned bronze + load smoke test)

> Ticket extracted from `eduloka/milestone.md`. Canonical source is
> `milestone.md`; this file is a working reference for implementation.

**Depends on.** t1 merged.

**Scope.** After this ticket `fetch.py` can write partitioned bronze paths
(`data/raw/provider={p}/dt={YYYY-MM-DD}/…jsonl`) under a flag, and a done-check
loads the partitioned tree with DuckDB to prove it is analytics-ready.

**Contract refs.** `eduloka/scripts/README.md` §"medallion / three-stage";
`aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/fetch.py` (partition mode); `tests/test_fetch.py`
(partition-path unit test); `eduloka/runbook.md` (the flag/env);
`eduloka/scripts/README.md` (promote partition convention to documented mode).

**Do not generate.** No object-storage SDK — local partitioned paths only. Do
not change the JSONL record shape or the default flat path.

**Runbook update rule.** Introduces the partition-output flag/env. Document it.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_fetch.py -q
duckdb -c "select count(*) from read_json_auto('eduloka/data/raw/provider=*/dt=*/*.jsonl')"  # integration; skip if duckdb absent
```

**Claude-code prompt.**
> Add a partitioned-output mode to `fetch.py` (`provider={p}/dt={date}`) behind
> a flag, leaving the flat default intact. Add a path-construction unit test.
> Promote the partition convention in README from note to mode; record the flag
> in `eduloka/runbook.md`. DuckDB load is an integration check — skip if absent.
> Run the done-check; include output.

**Spike reference.** No dedicated spike — this is a new mode on top of t1's
`fetch.py`.

**Implementation notes.** → `eduloka/docs/t7-implementation-notes.md` (write
after ticket closes).
