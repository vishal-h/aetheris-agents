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

**CSE notes:**
- Free tier: 100 queries/day. Shared with any other CSE usage on the key.
- Sunset: **2027-01-01**. CSE is the free baseline until then; paid providers (serper, dataforseo, exa) are available as drop-in replacements.
- Same credentials as the legacy `ct-edux` app (`GWS_CSE_API_KEY`, `GWS_CSE_ENGINE_ID`).

### Stage-2 (map) and stage-3 (enrich)

No additional credentials — pure transforms, no network.

### Stage-5 upsert (t5)

| Variable | Required | Description |
|---|---|---|
| `EDUX_DATABASE_URL` | yes | PostgreSQL connection string for the `gws_cse` database |

---

## Rig agent config

Add a new **"Eduloka"** group to `agentConfigDefs.ts` (rig runbook
§"Agent config") for the keys above. The current groups are: Harness,
Anthropic, SMTP, Google Drive, Payslip, GitHub. Eduloka keys needed:
`SEARCH_PROVIDER`, `GWS_CSE_API_KEY`, `GWS_CSE_ENGINE_ID`,
`GWS_CSE_REFERER` (optional), `EXA_API_KEY`, `EDUX_DATABASE_URL` (t5),
`SERPER_API_KEY` (t2), `DATAFORSEO_LOGIN` (t2), `DATAFORSEO_PASSWORD` (t2).

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
```

Output: `data/raw/{provider}.jsonl` (one envelope per line: `provider`,
`term`, `fetched_at`, `raw`). JSON summary to stdout; errors to stderr.

Partitioned bronze output (t7 — for datalake/analytics):
```bash
python3 scripts/fetch.py --provider cse --term "iit.ac.in" --partition
# writes to data/raw/provider=cse/dt=YYYY-MM-DD/iit.ac.in.jsonl
```

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
| `data/raw/{provider}.jsonl` | bronze | Provider-native envelopes; append-only |
| `data/raw/provider={p}/dt={date}/` | bronze (partition) | Hive-partitioned; DuckDB-queryable |
| `data/edux/{provider}.jsonl` | silver | EduxRecord JSON; re-mappable without re-querying |
| `data/gold/{provider}.jsonl` | gold | EduxRecord + namespaced enrichment; analytics-ready |

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
