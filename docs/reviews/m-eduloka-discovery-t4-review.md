# m-eduloka-discovery — t4 review

> Reviewer: claude-ui. Against `milestone.md §t4`.

## Round 1 — Verdict: approved (one N1 to disposition)

**Done-check:** pytest + `_v` present in `enrichment.keywords` passed. ✓ (48/48 full suite)

| ID | Severity | Finding |
|----|----------|---------|
| N1 | non-blocking | Name-only idempotency guard (`if name in record.enrichment: continue`) made `_v` write-only — a version bump would never re-enrich already-stamped records |
| — | note | `enrich_keywords` ignores `record.text`; title+snippet only. Not a defect (illustrative enricher); flagged so gold `terms` output isn't mistaken for the target enrichment shape |

**N1 detail:** Version-aware guard added: skip only when `existing.get("_v") == ENRICHER_VERSIONS[name]`; re-enrich on version bump. Regression test: stale `_v=0` record gets overwritten with `_v=1`.

**Positive:** Per-line resilience + `partial`/exit 1 and `_USE_CASE_ROOT`-anchored `--out` adopted proactively from t3 — graceful-degradation pattern carried forward without being asked.

## Verdict: cleared to merge

Done-check 14/14. N1 dispositioned.

**Promotable-learning (three consecutive instances):** "degrade gracefully on empty/malformed input; emit `partial` + exit 1, never crash the envelope" — t2/B1, t3/N1, t4 proactively. Three instances: promotion candidate for `CLAUDE.md`.
