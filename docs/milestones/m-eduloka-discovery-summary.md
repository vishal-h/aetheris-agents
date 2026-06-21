# m-eduloka-discovery — Milestone Summary

**Status:** shipped  
**Closed:** 2026-06-16  
**Tickets:** t1–t8 (8 tickets, all merged)

---

## What shipped

A provider-swappable, replayable medallion discovery pipeline for Indian
educational institutes, landing in the same `gws_cse` table the live
`ct-edux` site reads. Replaces the legacy CSE-only ingest with a
multi-provider, enrichment-capable, orchestrated pipeline.

### Medallion stages

| Stage | Script | Input → Output |
|-------|--------|----------------|
| Bronze | `fetch.py` | API → `data/raw/{slug}/{provider}.jsonl` |
| Silver | `map.py` | bronze → `data/edux/{slug}.jsonl` (EduxRecord) |
| Gold | `enrich.py` | silver → `data/gold/{slug}.jsonl` (+ enrichment) |
| Operational (A) | `upsert_institute.py` | gold → Postgres `gws_cse` |
| Operational (B) | `export_institute.py` | gold → `data/export/{slug}.jsonl` |

### What each ticket delivered

| Ticket | Deliverable |
|--------|-------------|
| t1 | `fetch.py` + `fetch_base.py` + `fetch_cse.py` + `fetch_exa.py` — core fetch loop, CSE + Exa adapters |
| t2 | `fetch_serper.py` + `fetch_dataforseo.py` — Serper + DataForSEO adapters |
| t3 | `mappers.py` + `map.py` — bronze→silver; `EduxRecord` schema |
| t4 | `enrichers.py` + `enrich.py` — versioned enrichers; silver→gold |
| t5 | `upsert_institute.py` — direct Postgres sink; faithful `gws_cse` DDL |
| t5b | `export_institute.py` — file-handoff sink; shared `to_gws_cse()` projection |
| t6 | `eduloka_orchestrator.exs` + `list_terms.py` + `data/terms.txt` + sprint case |
| t7 | `--partition` mode; `slug_term()`; orchestrator path sanitization |
| t8 | `tools.json`; capability-matrix row; this summary; drift sync |

### Key design decisions

**EduxRecord as the shared projection authority.** `to_gws_cse()` is the single
function that produces the `gws_cse` column set. Both sinks (upsert + export)
call it — the cross-repo contract with ct-edux can't drift between sinks.

**Explicit sink selection.** `EDUX_SINK=direct|export` is resolved at
orchestrator eval time. `EDUX_SINK=direct` with no `EDUX_DATABASE_URL` raises
immediately — no silent fallback. Regression-guarded in the sprint case.

**slug_term() in a script, not the LLM.** Slugification lives in
`list_terms.slug_term()`. The orchestrator receives pre-computed slugs alongside
original terms and does string substitution only — the LLM never derives a slug.

**Two bronze layouts.** The orchestrator's per-term layout (`data/raw/{slug}/`)
gives parallel sub-agents file isolation with no races. The `--partition` Hive
layout (`data/raw/provider={p}/dt={date}/{slug}.jsonl`) is a separate analytics
concern — populated via explicit `--partition` fetch runs, not by normal pipeline
runs.

**Status preserved on conflict.** `upsert_institute.py` excludes `status` from
`DO UPDATE SET` — `status=0` soft-deletes survive re-discovery.

---

## Test coverage at milestone close

| Test file | Count | Notes |
|-----------|-------|-------|
| test_fetch.py | 25 | offline; DuckDB integration (1) auto-skips if absent |
| test_map.py | 15 | fully offline |
| test_enrich.py | 14 | fully offline |
| test_upsert.py | 9 | 6 offline + 3 integration (auto-skip w/o EDUX_DATABASE_URL) |
| test_export.py | 12 | fully offline |
| test_list_terms.py | 16 | unit + CLI + slug |
| **Total** | **88 pass / 91 collected** | **+ 3 integration skips** |

Sprint: `./scripts/sprint.sh eduloka` — 8/8 checks, no live API or DB required.

---

## Deferred to m-eduloka-surfacing (Phase 2)

- Phase-2 news/event-driven surfacing over the enriched corpus (Vertex AI
  Search or pgvector)
- Real enrichers: LLM classification, geocoding, SERP fetch-text
- Remote object storage for the Hive lake
- Promotion of hot enrichment keys to real `gws_cse` columns
- Production discovery-provider decision (Serper vs Exa) — see open question #3;
  CSE is already closed to new customers, so this is active, not a 2027 plan
- ct-edux companion workstream: Ecto migration for `enrichment` column;
  `GwsCseApi.upsert/1` ingest task for the export file (issue #65)

---

## Open questions for Phase 2

1. **Hive layout wiring:** unify the orchestrator with `--partition` so pipeline
   runs also populate the analytics tree, or keep the operational and analytics
   lakes separate by design.
2. **max_steps ceiling:** current `max_steps: 50` handles ~44 terms. Past that,
   batch sub-agents (each takes several terms) to decouple step count from term
   count.
3. **Production discovery provider:** CSE's JSON API is already closed to new
   customers (2026) — new GCP projects get `403 PERMISSION_DENIED`; CSE survives
   only via ct-edux's grandfathered key. The free baseline for new runs is
   already Serper, so this is an active choice, not a 2027 migration: bake off
   Serper vs Exa on the real `terms.txt` (homepage hit-rate vs aggregator noise;
   Exa's inline full text for the harvesting path). Status: open, not yet run.
