# boxy-pipeline backlog

Deferred items from patch reviews and milestone-end scans. Each item has a
status (`open`, `in-progress`, `done`) and a reference to where it was surfaced.

---

## BL-015 — Tighten `_CABINET_RE` to require ≥2 digits

**Status:** open
**Surfaced in:** vision prompt patch review (round 1)

**Problem.** `_CABINET_RE` pattern B allows `[0-9]{1,4}` (≥1 digit), so
`BPBC1` (4 uppercase letters + 1 digit = 5 chars) passes both `_token_to_code`
and minimum-length checks. `BPBC1` appears on the floor plan page as a
text-layer fragment of `BPBC12` and ends up in the output as a false code.

**Fix.** Change `[0-9]{1,4}` → `[0-9]{2,4}` in pattern B of `_CABINET_RE`:

```python
# BEFORE
r"|[1-3]?[A-Z]{2,4}[0-9]{1,4}[A-Z]{0,4}"

# AFTER
r"|[1-3]?[A-Z]{2,4}[0-9]{2,4}[A-Z]{0,4}"
```

**Scope check.** Verify no real codes are dropped. Known single-digit codes:
`BPBC9` (1 digit). After the change `BPBC9` would fail pattern B. Check if
`BPBC9` matches pattern A (`[A-Z][0-9]{4}` — no, 1 digit not 4) or C
(dash-suffix — no). **Conclusion:** `BPBC9` needs explicit handling or the
threshold must stay at ≥1 digit for pattern B. Two options:

1. Add `BPBC9` as a named exception in `_token_to_code`.
2. Keep `[0-9]{1,4}` in pattern B; instead add `BPBC1` to the
   `_filter_floor_plan_fragments` logic (fragment suppression already handles
   similar cases like `B42FHL` ← `BLB42FHL`).

Option 2 is lower risk — `_filter_floor_plan_fragments` already has a
proper-suffix suppression rule; `BPBC1` is a proper suffix of `BPBC12`
and would be caught by the existing pattern 1 check. Verify with a unit test.

**Suggested approach:** option 2 — no regex change needed; confirm
`_filter_floor_plan_fragments` already suppresses `BPBC1` when `BPBC12` is
present in an elevation drawing, then add a unit test asserting this.

**Files affected:** `scripts/plan_extractor.py`, `tests/test_plan_extractor.py`
