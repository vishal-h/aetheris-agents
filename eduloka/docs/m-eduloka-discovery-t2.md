# t2 — Stage-1 fetch: paid SERP providers (serper, dataforseo)

> Ticket extracted from `eduloka/milestone.md`. Canonical source is
> `milestone.md`; this file is a working reference for implementation.

**Depends on.** t1 merged.

**Scope.** After this ticket the `serper` and `dataforseo` fetchers exist behind
the same registry and CLI, writing raw records identically to t1's providers.

**Contract refs.** `eduloka/scripts/README.md` §"Providers" (billing models,
pagination/geo notes); `aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/fetch_serper.py`, `fetch_dataforseo.py`;
`eduloka/tests/test_fetch.py` (serper + dataforseo cases); `eduloka/runbook.md`
(their env vars).

**Do not generate.** No mapping. No changes to `fetch_base.py` or the t1
fetchers beyond registry entries (already present from the spike). Do not
introduce a shared HTTP client other than the `fetch_base` helpers.

**Runbook update rule.** Introduces `SERPER_API_KEY`, `DATAFORSEO_LOGIN`,
`DATAFORSEO_PASSWORD`. Document in `eduloka/runbook.md` this commit, with the
prepaid/credit notes from README §"Providers".

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_fetch.py -q -k "serper or dataforseo"
```

**Claude-code prompt.**
> Land the `serper` and `dataforseo` fetchers from the spike behind the
> existing registry, returning raw items only. Pagination/geo per README
> §"Providers" (Serper page-based; DataForSEO over-fetch+slice). Add their env
> vars to `eduloka/runbook.md`. Run the done-check; include output.

**Spike reference.** `fetch_serper.py`, `fetch_dataforseo.py`, `test_fetch.py`
(serp cases) — at `/tmp/eduloka/` (reference only; rebuild against the contract).

**Spike gotcha.** DataForSEO and Exa have no result offset → over-fetch and
slice; CSE and Serper paginate natively. Exa ignores `country`. Verify
endpoints/field names against each provider's docs during this ticket.

**Implementation notes.** → `eduloka/docs/t2-implementation-notes.md` (write
after ticket closes).
