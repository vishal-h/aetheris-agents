# m3 — Migration

**Goal:** Approved documents in the correct location on the new NAS structure.

No documents are deleted in this milestone. The original `/archive/` storage
stays intact — it becomes a read-only archive. Migration copies approved files
to the structured `/clients/` store and logs every action to DuckDB.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Migration script](m3-001-execute-migration.md) | m2 complete | `execute_migration.py` — copy files to destination, verify hash, log to DuckDB |
| 002 | [Migration agent](m3-002-migration-agent.md) | 001 | `migration_agent.exs` — reads migration_queue, batches moves, escalates large batches, reports |

**001** first — the agent depends on it.

---

## Completion gate

- Human reviews migration summary report
- Spot-check: 10+ randomly selected files confirmed in correct `/clients/` location
- `/archive/` mount confirmed read-only
- `migrations` table shows `status = 'migrated'` for all approved files

---

## Key design decisions

**Copy, not move.** Files are copied to `/clients/`, not moved from `/archive/`.
The source stays in `/archive/` permanently. This eliminates the risk of data
loss from a failed migration and preserves the archive as a searchable backup.

**Hash verification.** After each copy, the SHA-256 of the destination file is
verified against the source. A mismatch marks the migration as `failed` and
triggers an error — the corrupt copy is deleted, the source is untouched.

**No deletions.** Nothing in `/archive/` is ever deleted by any agent. If
disk space becomes a concern after the migration is validated, deduplication
of `/archive/` is a separate future decision, made by the auditors.

**Escalation threshold.** The migration agent escalates batches above 100 files
via `ask_human` before executing. This is configurable via
`MIGRATION_ESCALATION_THRESHOLD` (default: 100). The agent never autonomously
migrates more than this many files in one batch.

**Idempotent.** Re-running the migration agent on an already-migrated corpus
is safe. `execute_migration.py` skips files already in `status = 'migrated'`
in the `migrations` table.

---

## Reference

- DuckDB schema (migrations table, migration_queue view): `docs/provenance/specs.md`
- Architecture: `docs/provenance/architecture.md`
- Agent conventions: `docs/agent-creation-guide.md`
- CLAUDE.md: `CLAUDE.md`
