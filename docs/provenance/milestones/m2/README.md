# m2 — Classification

**Goal:** Every unique document assigned to client, financial year, and document type.

No files are moved in this milestone. The output is a proposed classification
for every unique file in the corpus, reviewed and approved before Phase 3 begins.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Taxonomy session](m2-001-taxonomy-session.md) | — | Interactive interview script that captures classification rules from a senior auditor and produces `taxonomy.md` |
| 002 | [Classifier script and agent](m2-002-classifier.md) | 001 | `classify_documents.py` writes classifications to DuckDB; classifier sub-agent reads files and applies taxonomy rules |
| 003 | [Classification orchestrator](m2-003-orchestrator.md) | 002 | Orchestrator agent that spawns parallel classifier sub-agents and collects results |
| 004 | [Review tooling](m2-004-review-tooling.md) | 002 | Export proposed classifications to CSV; bulk approve/reject back to DuckDB |

**001** is a human step — requires a session with a senior auditor before any
code runs. Everything else depends on the `taxonomy.md` it produces.

**002** and **004** are independent of each other once **001** is done.
**003** depends on **002**.

---

## Completion gate

A human operator reviews proposed classifications — at minimum:
- All low-confidence results (below 0.70)
- A random sample of 50 high-confidence results

Approval recorded in the `classifications` table (`status = 'approved'`) before
the m3 migration milestone begins.

---

## Key design decisions

**Taxonomy first.** The classification agent is only as good as the rules it is
given. `taxonomy.md` is the single source of truth for classification logic —
produced by a human, not inferred by the model. Get this right before running
at scale.

**Classify unique files, not all files.** Group by `sha256` and classify one
representative path per unique hash. Duplicates inherit the classification.
This reduces LLM calls significantly for a corpus with many duplicates.

**Confidence threshold.** Classifications below 0.70 are flagged
`status = 'needs_review'` rather than `proposed`. They appear at the top of the
review queue. Configurable via `CLASSIFICATION_THRESHOLD` env var (default 0.70).

**Batch size.** Each classifier sub-agent receives ~20 files. Tune via
`CLASSIFICATION_BATCH_SIZE` (default 20).

---

## Reference

- DuckDB schema (classifications table): `docs/provenance/specs.md`
- Architecture and data flow: `docs/provenance/architecture.md`
- Agent file conventions: `docs/agent-creation-guide.md`
- CLAUDE.md: `CLAUDE.md`
