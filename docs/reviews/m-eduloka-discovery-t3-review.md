# m-eduloka-discovery — t3 review

> Reviewer: claude-ui. Against `milestone.md §t3`.

## Round 1 — Verdict: changes requested

**Done-check:** pytest + cse-pagemap assertion passed. ✓ (34/34 full suite)

| ID | Severity | Finding |
|----|----------|---------|
| B1 | blocking | `EduxRecord` omitted the `status` core field documented in README §"edux structure"; `to_gws_cse()` hardcoded `status: 1`, making the record unable to represent `status ≠ 1` |
| N1 | non-blocking | `map.py` aborted the whole file on one malformed line — regressed spike's per-line skip + `mapped/skipped/errors` reporting |
| M1 | minor | `map.py` default `--out` was CWD-relative; `fetch.py` anchors to `_USE_CASE_ROOT` |

**B1 detail:** The schema is the most expensive artifact to change once t4/t5 and fixtures build on it. Known consumer: re-validation/dead-link path needs `status=0`. Fixed: `status: int = 1` restored to `EduxRecord`; `to_dict()` and `to_gws_cse()` project `self.status`.

**N1 detail:** Bronze is append-only; one corrupt capture shouldn't block mapping the rest. Fixed: per-line `try/except`; `mapped/skipped/errors` in response; `"partial"` + exit 1.

**M1 detail:** Fixed: default `--out` anchored to `_USE_CASE_ROOT / "data" / "edux"`.

## Round 2 — Verdict: cleared to merge

Done-check 15/15. All findings dispositioned.

**Promotable-learning watch:** "degrade gracefully on empty/malformed input rather than crash" — t2/B1 + t3/N1, two instances of one class.
