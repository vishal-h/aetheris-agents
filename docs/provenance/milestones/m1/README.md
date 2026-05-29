# m1 — Inventory

**Goal:** Know exactly what exists before touching anything.

No files are moved or deleted in this milestone. The output is a complete,
human-readable inventory report that stakeholders review and approve before
Phase 2 (classification) begins.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Scanner CLI](m1-001-scanner-cli.md) | — | Extract f2-scanner from Tauri into a standalone binary callable via `run_command` |
| 002 | [DuckDB schema](m1-002-duckdb-schema.md) | — | Create all tables and views; idempotent init script |
| 003 | [Scan orchestrator](m1-003-scan-orchestrator.md) | 001, 002 | Aetheris agent that drives the scanner and monitors completion |
| 004 | [Inventory report](m1-004-inventory-report.md) | 002 | Script that queries DuckDB and produces a stakeholder-ready Markdown report |

001 and 002 are independent and can run in parallel.
003 depends on both. 004 depends only on 002 and can be built alongside 003.

---

## Completion gate

A senior auditor reviews the inventory report and confirms it accurately reflects
the known state of storage. Sign-off recorded before m2 begins.

---

## Reference

- Full specs (DuckDB schema, scanner CLI, agent interfaces): `../specs.md`
- Architecture and component map: `../architecture.md`
- Agent file conventions: `docs/agent-creation-guide.md`
- CLAUDE.md: `CLAUDE.md`