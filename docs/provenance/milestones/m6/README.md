# m6 — Tauri Dashboard

**Goal:** All stakeholders can see the state of the corpus without touching
a terminal.

This milestone is in the **`hai-rig` repo**, not `aetheris-agents`.
Claude Code must be running in `hai-rig/` for all implementation work here.
The hai-rig `CLAUDE.md` has been updated to reflect the new role.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Corpus DB connection + commands](m6-001-corpus-db.md) | m5 | Rust backend: open PROVENANCE_DB_PATH, add Tauri commands for corpus queries |
| 002 | [Corpus overview tab](m6-002-corpus-overview.md) | 001 | Main dashboard: file counts, duplicate summary, scan history, per-client breakdown |
| 003 | [Classification review tab](m6-003-classification-review.md) | 001 | Approve/reject proposed classifications — the one write path Rig owns |
| 004 | [Migration + zip status tabs](m6-004-migration-zip.md) | 001 | Migration progress by client; zip inventory status and backlog |

**001** first — all UI tabs depend on the Tauri commands it exposes.
**002**, **003**, **004** are independent of each other once **001** is done.

---

## Completion gate

Stakeholder walkthrough with the firm contact:
- Corpus overview loads and shows correct totals
- Classification review allows approve/reject and updates correctly
- Migration status reflects the current state of `/clients/`
- Zip inventory shows processed/encrypted/pending counts
- Sign-off recorded before production use

---

## Key design decisions

**Two DuckDB connections.** The Rust backend maintains two connections:
`app_conn` (existing, for the F2 module's local data) and `corpus_conn`
(new, read-only, opened from `PROVENANCE_DB_PATH` at startup). If
`PROVENANCE_DB_PATH` is not set, Provenance tabs render a "corpus not
connected" placeholder rather than crashing.

**Read-only corpus, one write exception.** All corpus DB access is
read-only except `set_classification_status` (approve/reject). This is
enforced at the connection level: `corpus_conn` opens with `read_only=true`,
and a separate short-lived write connection is opened only for
`set_classification_status`. See hai-rig `CLAUDE.md` rule on writes.

**New module: `provenance`.** Follows the existing `f2` module pattern:
- Backend: `src-tauri/src/commands/provenance.rs` — all Tauri commands
- Frontend: `src/components/modules/provenance/` — React components
- Hooks: `src/hooks/useProvenance*.ts` — custom hooks wrapping `invoke()`
- Registered in `src-tauri/src/lib.rs` and `src/modules/registry.ts`

**F2Operations tab factory pattern.** The Provenance dashboard is a tab
factory function `ProvenanceDashboard()` returning `Tab[]`, not a React
component. Call it as `ProvenanceDashboard()`, not `<ProvenanceDashboard />`.

**DuckDB rules D1–D6 apply.** All queries follow hai-rig `CLAUDE.md`
DuckDB rules — TIMESTAMP columns cast to VARCHAR, `ON CONFLICT (path) DO
UPDATE` for upserts, `now()` not `CURRENT_TIMESTAMP`, etc.

---

## Reference

- hai-rig architecture and rules: `CLAUDE.md` (in hai-rig repo root)
- Provenance DuckDB schema: `docs/provenance/specs.md` (in aetheris-agents)
- Existing Tauri command pattern: `src-tauri/src/commands/f2.rs`
- Existing hook pattern: `src/hooks/useFileIndex.ts`
