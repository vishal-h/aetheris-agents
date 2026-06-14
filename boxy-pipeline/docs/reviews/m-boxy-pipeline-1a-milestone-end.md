# Milestone-end review — m-boxy-pipeline-1a

## Scope

Findings scan across all ticket reviews in this milestone:

- `m-boxy-pipeline-1a-t1-review.md` — catalog extractor + schema additions
- `m-boxy-pipeline-1a-t2-review.md` — SO extractor
- `m-boxy-pipeline-1a-t3-review.md` — resolver JSONL refactor

---

## Recurring-findings scan

**Promotion threshold: a finding must appear in ≥ 2 ticket reviews to warrant
promotion to a process rule or standing backlog item.**

| Finding pattern | t1 | t2 | t3 | Recurs? |
|-----------------|----|----|-----|---------|
| Deferred to backlog | F1, F3 (BL-011, BL-012) | F1, F2 (BL-013, BL-014) | — | yes — *intended workflow*, not a defect |
| Reviewer asked a question resolved in-ticket | — | F3 (line-item count) | F1 (import json), F2 (key count) | yes — see §Analysis |
| Blocking finding that required a fix | — | — | F1 (resolved before merge) | no |

---

## Analysis

### Deferred backlog items

t1 and t2 each produced two backlog items (BL-011–BL-014). This is the
intended ticket workflow: scope-controlled tickets defer lower-priority
improvements to the backlog. No process change warranted.

### Reviewer clarification questions

Across t2 and t3, four reviewer questions were resolved in-ticket rather than
blocking merge:

- **t2 F3**: reviewer estimated ~27 line items; actual was 34 (page 2 wall and
  door items undercounted). Corrected in §Finding 3 disposition; test asserts
  `len > 20`, which holds for both counts.
- **t3 F1**: reviewer flagged `import json` as possibly missing from
  `catalog_resolver.py`; confirmed present at line 8 (unchanged from original,
  not shown in diff). No fix needed.
- **t3 F2**: reviewer questioned 332-key index vs 4,594 total entries; explained
  as code-keyed index (each key maps to all color variants for that code).
  `real_index` integration test threshold corrected from `> 1000` to `> 100`
  before merge.

**Common thread**: reviewer knowledge gaps about PDF column layout (t2) and
index structure (t3) led to questions that were one-time clarifications, not
recurring defects. No process rule is actionable here — the clarifications are
now documented in the respective §Design notes sections.

---

## Milestone summary

| Ticket | Scope | Outcome |
|--------|-------|---------|
| t1 — catalog extractor | `catalog_extractor.py`, `CatalogEntry` schema | 21 tests, 4,594 entries, 5 series |
| t2 — SO extractor | `so_extractor.py` | 32 tests, 34 line items, $8,099.54 total |
| t3 — resolver JSONL refactor | `load_catalog_jsonl`, auto-detect in `resolve()` | 14 new tests, matches Excel baseline |
| t1-patch — overlap fix | `x_tolerance=1` in `plan_extractor.py` | 4 new tests, garbled tokens rejected |

All tickets approved and merged. Test suite: 158 tests passing.

---

## Promotions

**None.** No findings recur across ≥ 2 tickets with an actionable pattern
distinct from the intended backlog workflow.
