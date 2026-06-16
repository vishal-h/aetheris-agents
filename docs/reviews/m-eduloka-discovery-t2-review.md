# m-eduloka-discovery — t2 review

> Reviewer: claude-ui. Against `milestone.md §t2`.

## Round 1 — Verdict: changes requested

**Done-check:** 8/8 subset passed. ✓ (all fixtures well-formed; malformed/empty response path not exercised)

| ID | Severity | Finding |
|----|----------|---------|
| B1 | blocking | `fetch_dataforseo` response parsing crashed (uncaught `TypeError`) on a `null` `result`/`items` — real DataForSEO error/empty response breaks the stdout envelope contract |
| N1 | non-blocking | `_LOCATION_MAP.get(country.upper(), "India")` silently fell back to India for unknown country codes |
| — | note | Serper `start` is page-quantized; consistent with spike and orchestrator's 1/11/21 stepping |

**B1 detail:** `dict.get(k, default)` only guards absent keys, not explicit `null`. DataForSEO returns `"result": null` on auth/quota errors → `None[0]` → `TypeError` not caught by `except SearchError` → traceback on stderr, no JSON envelope. Fixed: `or []` pattern at all three nesting levels; two regression tests added (`null result → []`, `null items → []`).

**N1 detail:** Documented India fallback explicitly in module docstring as intentional for the India-focused pipeline.

## Round 2 — Verdict: cleared to merge

Done-check 10/10 subset, 20/20 full. All findings dispositioned.

**Promotable-learning candidate:** In fetchers, treat explicit API `null` the same as absent — use `or []` not `dict.get(k, default)` — so error responses degrade to `[]` rather than crashing the envelope contract.
