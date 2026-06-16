# eduloka discovery pipeline (medallion / three-stage)

    fetch  ->  data/raw/{p}.jsonl   (bronze: provider-native, immutable, replayable)
    map    ->  data/edux/{p}.jsonl  (silver: mapped to the edux schema)
    enrich ->  data/gold/{p}.jsonl  (gold: + namespaced enrichment, analytics-ready)
    upsert ->  Postgres gws_cse (+ enrichment jsonb)   [operational; feeds the site]

The bronze JSONL is the datalake landing layer — append-only, newline-delimited,
loads straight into DuckDB/Athena/BigQuery. See `fetch.py --partition` for the
Hive-style path (`raw/provider=exa/dt=YYYY-MM-DD/…`) when wiring object storage
(t7).

Why staged: raw is lossless, so growing the edux structure or adding an enricher
means re-running downstream **without re-querying** (no extra prepaid quota).
map and enrich are pure (no network) → testable with plain data.

## Run

    python3 scripts/fetch.py  --provider exa --term "edu.in" --start 1 --num 10
    python3 scripts/map.py    --in data/raw/exa.jsonl
    python3 scripts/enrich.py --in data/edux/exa.jsonl --enrichers domain,keywords

All CLIs: JSON summary to stdout, errors to stderr, exit 0 / 1. Dedup on `link`
is left to upsert (gws_cse.link is unique).

## edux structure — edux_record.py (the tweakable surface)

- **core**: link, title, snippet (lean, display), image, search_term, status, metatags — 1:1 with gws_cse.
- **text**: full page text — enrichment/lake fuel; Exa provides it inline, SERP
  providers need a fetch-text enricher. Kept OUT of the operational row.
- **provenance**: source_provider, fetched_at.
- **enrichment**: a jsonb bag, namespaced per enricher and stamped (_by/_at/_v), e.g.
  `{"keywords": {"state": "...", "_by": "keywords", "_at": "...", "_v": 1}}`.
  Queryable via jsonb/GIN; promote a hot key to a real column later.

`to_gws_cse()` → operational row: core columns + `enrichment` jsonb (one additive,
non-breaking migration; the site ignores it). Full `text` excluded. Zero-migration
fallback: fold `enrichment` into the metatags `_edux` map instead.

## Enrichment workers — enrichers.py / enrich.py

Each enricher is a pure `record → payload dict`; enrich.py stamps it and writes
`record.enrichment[name]`. Idempotent per namespace, so workers compose and run
independently (in aetheris: one spawned sub-agent per batch, wait_for_all). The
two shipped enrichers (domain TLD, keyword extraction) are deterministic/offline
illustrations — real ones (LLM classification, geocoding, SERP fetch-text) plug
in the same way.

## Providers (select with --provider or SEARCH_PROVIDER)

| Provider   | Credentials                                          | Billing         | Notes |
|------------|------------------------------------------------------|-----------------|-------|
| cse        | GWS_CSE_API_KEY, GWS_CSE_ENGINE_ID, GWS_CSE_REFERER? | free ≤100/day, until 2027-01-01 | legacy engine; native `start`; real pagemap image+metatags |
| serper     | SERPER_API_KEY                                       | prepaid (6-mo)  | Google results; closest paid CSE match |
| dataforseo | DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD                | pure prepaid    | cheapest/query; live/advanced endpoint |
| exa        | EXA_API_KEY                                          | usage-based     | semantic; returns full page text |

cse is the free baseline to lean on until sunset; the paid three stay dormant
until needed. GWS_CSE_REFERER is optional (only for a referer-restricted key).

## Files

    scripts/fetch_base.py     http helpers, SearchError, fetcher registry
    scripts/fetch_{p}.py      stage-1 fetchers → raw items
    scripts/fetch.py          stage-1 CLI → data/raw
    scripts/edux_record.py    edux schema (+ to_gws_cse projection)
    scripts/mappers.py        stage-2 pure raw→EduxRecord transforms
    scripts/map.py            stage-2 CLI → data/edux
    scripts/enrichers.py      enricher registry (example deterministic workers)
    scripts/enrich.py         stage-3 worker CLI → data/gold
    scripts/upsert_institute.py  operational upsert → Postgres gws_cse
    scripts/list_terms.py     read data/terms.txt → JSON for orchestrator
    tests/                    pytest; offline

## Caveats

- `cse` returns real pagemap, so its `image`/`metatags` are populated; the other
  three give best-effort `image` and provider extras in `metatags`.
- `cse` paginates natively by `start` (max 91); Serper paginates by page;
  DataForSEO/Exa over-fetch+slice; Exa ignores country.
- Written to current API shapes; not live-tested in this sandbox (reaches only
  package registries). Confirm endpoints/field names before prod; raw→edux
  mapping is isolated per provider in `mappers.py` to make corrections a
  one-spot edit.

## Partition mode (t7 — datalake readiness)

Pass `--partition` to `fetch.py` to write Hive-partitioned bronze paths:

    data/raw/provider=exa/dt=2026-06-16/edu.in.jsonl

The flat default (`data/raw/exa.jsonl`) is unchanged without the flag. DuckDB
can query the partitioned tree directly:

    duckdb -c "select count(*) from read_json_auto('data/raw/provider=*/dt=*/*.jsonl')"
