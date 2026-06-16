# eduloka runbook

Operational guide for the eduloka use case. For pipeline design see
`scripts/README.md`; for the ticket sequence see `milestone.md`.

---

## Prerequisites

- Python 3.12 (mise-managed — check `mise.toml` at repo root)

```bash
cd aetheris-agents/eduloka
pip install -r requirements.txt   # no extra deps for t1; stdlib urllib only
```

---

## Environment variables

### Stage-1 fetch

Set via shell export or Rig agent config (§"Agent config" below).

| Variable | Required | Description |
|---|---|---|
| `SEARCH_PROVIDER` | yes (or `--provider`) | Active fetch provider: `cse`, `serper`, `dataforseo`, `exa` |
| `GWS_CSE_API_KEY` | cse | Google Custom Search JSON API key |
| `GWS_CSE_ENGINE_ID` | cse | Programmable Search Engine ID (`cx`) |
| `GWS_CSE_REFERER` | cse (optional) | HTTP Referer header — only if the key is referer-restricted |
| `EXA_API_KEY` | exa | Exa API key |
| `SERPER_API_KEY` | serper | Serper API key |
| `DATAFORSEO_LOGIN` | dataforseo | DataForSEO account login (email) |
| `DATAFORSEO_PASSWORD` | dataforseo | DataForSEO account password |

**CSE notes:**
- Free tier: 100 queries/day. Shared with any other CSE usage on the key.
- Sunset: **2027-01-01**. CSE is the free baseline until then; paid providers (serper, dataforseo, exa) are available as drop-in replacements.
- Same credentials as the legacy `ct-edux` app (`GWS_CSE_API_KEY`, `GWS_CSE_ENGINE_ID`).

**Serper notes:**
- Prepaid 6-month billing. Closest paid match to CSE results (Google SERP).
- Paginates by page number (`page=1` = results 1–num; `page=2` = num+1–2·num).

**DataForSEO notes:**
- Pure prepaid credits (charged per task). Cheapest per-query of the paid three.
- Uses the live/advanced Google organic endpoint. No result offset — over-fetches and slices.
- Login is the account email; password is the account password (not an API key).

### Stage-2 (map) and stage-3 (enrich)

No additional credentials — pure transforms, no network.

### Stage-5 operational sink

| Variable | Required | Description |
|---|---|---|
| `EDUX_SINK` | no (default: `export`) | Sink selection: `direct` → upsert into Postgres; `export` → write JSONL for ct-edux ingest |
| `EDUX_DATABASE_URL` | `direct` only | PostgreSQL connection string for the `gws_cse` database |
| `EDUX_TERMS_FILE` | no | Override path to terms file (default: `data/terms.txt`) |

`EDUX_SINK` is read by the orchestrator at eval time. Running the orchestrator with
`EDUX_SINK=direct` and no `EDUX_DATABASE_URL` raises immediately — it never silently
falls back to export. Running `export_institute.py` directly requires no DB credentials.

---

## Rig agent config

Add a new **"Eduloka"** group to `agentConfigDefs.ts` (rig runbook
§"Agent config") for the keys above. The current groups are: Harness,
Anthropic, SMTP, Google Drive, Payslip, GitHub. Eduloka keys needed:
`SEARCH_PROVIDER`, `GWS_CSE_API_KEY`, `GWS_CSE_ENGINE_ID`,
`GWS_CSE_REFERER` (optional), `EXA_API_KEY`, `EDUX_DATABASE_URL` (t5),
`SERPER_API_KEY` (t2), `DATAFORSEO_LOGIN` (t2), `DATAFORSEO_PASSWORD` (t2).

---

## Terms file

`data/terms.txt` is committed config — edit it to change which search terms the
pipeline runs against. One term per line; blank lines and `#` comments are ignored.

```bash
# Show current terms
python3 scripts/list_terms.py

# Use a custom file (also via EDUX_TERMS_FILE env var)
python3 scripts/list_terms.py --terms-file /path/to/custom_terms.txt
```

---

## Running the orchestrator (t6)

The orchestrator drives the full pipeline: `list_terms → [fetch → map → enrich → sink]`
one sub-agent per term, all in parallel.

```bash
cd ~/sandbox/elixirws/aetheris

# Export sink (no DB required — writes data/export/*.jsonl)
export SEARCH_PROVIDER=exa
export EXA_API_KEY=...
export EDUX_SINK=export
mix aetheris run ../aetheris-agents/eduloka/agents/eduloka_orchestrator.exs

# Direct sink (upsert to Postgres)
export SEARCH_PROVIDER=cse
export GWS_CSE_API_KEY=...
export GWS_CSE_ENGINE_ID=...
export EDUX_SINK=direct
export EDUX_DATABASE_URL="postgresql://user:pass@host:5432/dbname"
mix aetheris run ../aetheris-agents/eduloka/agents/eduloka_orchestrator.exs
```

The orchestrator fails at eval time if `EDUX_SINK=direct` and `EDUX_DATABASE_URL` is unset.

---

## Running fetch

```bash
cd aetheris-agents/eduloka

# CSE — free baseline
export GWS_CSE_API_KEY=...
export GWS_CSE_ENGINE_ID=...
python3 scripts/fetch.py --provider cse --term "iit.ac.in" --num 10

# Exa — semantic, full page text
export EXA_API_KEY=...
python3 scripts/fetch.py --provider exa --term "iit.ac.in" --num 10

# Serper — paid Google SERP (prepaid 6-month credits)
export SERPER_API_KEY=...
python3 scripts/fetch.py --provider serper --term "iit.ac.in" --num 10

# DataForSEO — paid Google SERP (prepaid per-query credits)
export DATAFORSEO_LOGIN=...
export DATAFORSEO_PASSWORD=...
python3 scripts/fetch.py --provider dataforseo --term "iit.ac.in" --num 10
```

Output: `data/raw/{provider}.jsonl` (one envelope per line: `provider`,
`term`, `fetched_at`, `raw`). JSON summary to stdout; errors to stderr.

**Partitioned bronze output** (`--partition` flag):
```bash
python3 scripts/fetch.py --provider cse --term "iit.ac.in" --partition
# writes to data/raw/provider=cse/dt=YYYY-MM-DD/iit.ac.in.jsonl

python3 scripts/fetch.py --provider exa --term "engineering college" --partition
# term slug used as filename: engineering-college.jsonl
# writes to data/raw/provider=exa/dt=YYYY-MM-DD/engineering-college.jsonl
```

Term slugs replace unsafe characters (spaces, slashes, colons) with dashes so
the filename is safe across filesystems. DuckDB can query the partitioned tree:
```bash
duckdb -c "select count(*) from read_json_auto('eduloka/data/raw/provider=*/dt=*/*.jsonl')"
```

---

## Running the operational sink (t5 / t5b)

Two sink scripts share the same `to_gws_cse()` row projection. The orchestrator
(t6) selects between them via `EDUX_SINK`.

### Sink A — direct upsert into Postgres (t5)

```bash
cd aetheris-agents/eduloka
export EDUX_DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# From gold (preferred — enrichment populated)
python3 scripts/upsert_institute.py --in data/gold/exa.jsonl

# From edux silver (enrichment empty; fills in later via enrich)
python3 scripts/upsert_institute.py --in data/edux/cse.jsonl
```

Output: `{"status": "ok"|"partial", "upserted": N, "skipped": M, ...}`.
Exit 1 on partial (some lines failed) or error.

#### Migration

The `enrichment` column is owned by ct-edux Ecto migrations (companion
workstream, issue #65). Apply via the ct-edux migration path.

**Emergency fallback only:** if the ct-edux migration is blocked, apply
`0001_add_enrichment_jsonb.sql` manually:

```bash
psql "$EDUX_DATABASE_URL" -f eduloka/data/migrations/0001_add_enrichment_jsonb.sql
```

`0000_create_gws_cse_clone.sql` is test-only — it clones the live DDL for the
`eduloka_test` DB. Do not apply it to any production or staging database.

### Sink B — export JSONL for ct-edux ingest (t5b)

Use when the ct-edux Postgres DB is unreachable from the agent. Output files
land in `data/export/` (gitignored) and are consumed by ct-edux via
`GwsCseApi.upsert/1` (companion workstream).

```bash
cd aetheris-agents/eduloka

# From gold (preferred)
python3 scripts/export_institute.py --in data/gold/exa.jsonl
# writes data/export/exa.jsonl

# Explicit output path
python3 scripts/export_institute.py --in data/gold/exa.jsonl --out /tmp/exa_export.jsonl
```

Output: `{"status": "ok"|"partial", "exported": N, "skipped": M, "out": path}`.
Exit 1 on partial or error.

**ct-edux handoff:** copy or move `data/export/*.jsonl` to the ct-edux host and
run its ingest task against the file. The row shape (`link`, `title`, `snippet`,
`image`, `search_term`, `status`, `metatags`, `enrichment`) is the
cross-repo contract — both this export and the direct upsert produce the same
column set from `to_gws_cse()`.

---

## Running tests

```bash
cd aetheris-agents/eduloka
python3 -m pytest tests/ -v

# t1 done-check subset (offline, no credentials)
python3 -m pytest tests/test_fetch.py -v -k "cse or exa or credentials or unknown"

# Skip integration tests (no DB / API needed)
python3 -m pytest tests/ -v -m "not integration"
```

---

## Data files (gitignored)

| Path | Stage | Notes |
|---|---|---|
| `data/raw/{provider}.jsonl` | bronze (flat) | Provider-native envelopes; append-only; default fetch output |
| `data/raw/{slug}/{provider}.jsonl` | bronze (per-term) | Per-term isolation used by the orchestrator (parallel sub-agents) |
| `data/raw/provider={p}/dt={date}/{slug}.jsonl` | bronze (Hive) | Partitioned output; `fetch.py --partition`; queryable by DuckDB/Athena |
| `data/edux/{slug}.jsonl` | silver | EduxRecord JSON; re-mappable without re-querying |
| `data/gold/{slug}.jsonl` | gold | EduxRecord + namespaced enrichment; analytics-ready |
| `data/export/{slug}.jsonl` | export | gws_cse-shaped rows; ct-edux ingest handoff |

**Bronze layout note:** the orchestrator uses the per-term layout (`data/raw/{slug}/`),
not the Hive partition tree. The `--partition` flag produces a separate Hive tree
intended for analytics workloads (DuckDB, Athena). These are two distinct layouts;
the Hive tree must be populated separately via manual or batch `--partition` fetch
runs — it is not populated by a normal pipeline run.

`data/terms.txt` is **committed config** — it is not gitignored.

---

## Troubleshooting

**`{"status": "error", "error": "no provider …"}`** — set `--provider` or
`SEARCH_PROVIDER`.

**`GWS_CSE_API_KEY / GWS_CSE_ENGINE_ID not set`** — export both before running
the cse provider.

**`HTTP 429`** — CSE daily quota (100 queries) exhausted. Wait until midnight
Pacific time for the quota to reset, or switch provider.

**`HTTP 403`** — key or engine ID is invalid; check the Google Cloud Console.
If the key is referer-restricted, set `GWS_CSE_REFERER`.
