# t1 — Scaffold + stage-1 fetch core (cse, exa)

> Ticket extracted from `eduloka/milestone.md`. Canonical source is
> `milestone.md`; this file is a working reference for implementation.

**Scope.** After this ticket `eduloka/` exists with the standard layout;
`fetch_base.py` provides the GET and POST helpers + fetcher registry; `fetch.py`
is the CLI; and the `cse` and `exa` fetchers write provider-native raw records
to `data/raw/{provider}.jsonl`. `cse` is the free legacy baseline (native
`start`, real pagemap); `exa` is the semantic/enrichment path.

**Contract refs.** `aetheris-agents/CLAUDE.md` §"Python script conventions"
(stdout-is-contract, exit codes, conftest), §"Use-case layout";
`eduloka/scripts/README.md` §"Providers", §"Run"; `anek` `Anek.Gws.Cse` and
`ct-edux` `lib/gws/cse.ex` (CSE endpoint, params, response shape, 429/403 paths).

**Touches.** `eduloka/scripts/fetch_base.py`, `fetch_cse.py`, `fetch_exa.py`,
`fetch.py`; `eduloka/tests/conftest.py`, `tests/test_fetch.py` (cse + exa
cases); `eduloka/.gitignore` (excludes `data/raw`, `data/edux`, `data/gold`,
`output/`); `eduloka/runbook.md` (env vars); `eduloka/README.md` (stub linking
the scripts README).

**Do not generate.** No mapping/enrichment in fetchers (raw items only). No new
HTTP dependency — stdlib `urllib`. No live API calls in tests. Do not add the
serp providers here (t2).

**Runbook update rule.** Introduces `SEARCH_PROVIDER`, `GWS_CSE_API_KEY`,
`GWS_CSE_ENGINE_ID`, optional `GWS_CSE_REFERER`, and `EXA_API_KEY`. Document in
`eduloka/runbook.md` this commit, including the CSE free 100/day cap and the
2027-01-01 sunset, and flag the Rig agent-config group these keys will need
(rig runbook §"Agent config").

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_fetch.py -q -k "cse or exa or credentials or unknown"
python3 eduloka/scripts/fetch.py --term "edu.in"; test $? -eq 1   # no provider -> error envelope, exit 1
```

**Claude-code prompt.**
> Create the `eduloka/` standard layout and land the fetch core from the spike:
> `fetch_base.py` (GET + POST helpers, `Fetcher` ABC, registry), `fetch.py`
> CLI, and the `cse` and `exa` fetchers. Follow CLAUDE.md §"Python script
> conventions" (JSON to stdout, errors to stderr, exit 0/1, conftest; no
> top-level `__init__.py`). The `cse` fetcher reproduces the legacy
> `anek` `Anek.Gws.Cse` request/response (endpoint, `cr=country{CC}`, native
> `start`) — reference it, do not restate it. Fetchers return raw items only.
> Write the env vars to `eduloka/runbook.md` per the Runbook update rule. Run
> the done-check; put actual output in the review packet.

**Spike reference.** `fetch_base.py`, `fetch_cse.py`, `fetch_exa.py`, `fetch.py`,
`test_fetch.py` (cse/exa cases), `conftest.py` — at `/tmp/eduloka/` (reference
only; do not copy verbatim; rebuild against the contract).

**Implementation notes.** → `eduloka/docs/t1-implementation-notes.md` (write
after ticket closes).
