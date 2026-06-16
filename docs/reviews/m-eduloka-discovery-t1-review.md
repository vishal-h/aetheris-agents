# m-eduloka-discovery — t1 review

> Reviewer: claude-ui. Against `milestone.md §t1`.

## Round 1 — Verdict: changes requested

**Done-check:** 7/7 subset passed. ✓

| ID | Severity | Finding |
|----|----------|---------|
| B1 | blocking | `fetch.py` stdout used `{"ok": bool}` — diverged from map/enrich CLIs; t6 needs one parser |
| N1 | non-blocking | `date.today().isoformat()` for `fetched_at` — coarse, local timezone, wrong for immutable bronze layer |
| N3 | non-blocking | runbook referenced `pip install -r requirements.txt` but file was missing |
| M2 | minor | `--provider` lacked `choices=PROVIDERS` |
| M4 | minor | Orphaned `python3 -m pytest tests/ -q` line in scripts/README.md |

**B1 detail:** `{"ok": bool}` in `fetch.py` diverged from the map/enrich stage CLIs. t6 orchestrator's single parser would break on mixed envelopes. Fixed: all error/success output changed to `{"status": "ok"|"error", "out": ...}`.

**N1 detail:** `fetched_at` derives the `dt=` partition key in the bronze layer. Local-timezone `date.today()` is wrong for an immutable record; fixed to `datetime.now(timezone.utc).isoformat()`.

## Round 2 — Verdict: cleared to merge

All findings dispositioned. Done-check 7/7.

**Promotable-learning candidate:** stdout envelope shape (`{"status": "ok"|"error"}` with `out` key) must be consistent across all stage CLIs so t6 has one parser.
