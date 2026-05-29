# m5 — Corpus MCP + Search

**Goal:** Ask a question in plain English, get the relevant documents.

This milestone builds the search layer over the classified, migrated corpus.
A self-developed corpus-search MCP server exposes DuckDB-backed metadata search
to Aetheris agents. The search agent combines metadata lookup with optional
Matryoshka content search to answer natural language queries.

Search covers both `/clients/` (migrated) and `/archive/` (original), including
new-to-corpus files surfaced by zip archaeology.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [corpus-search MCP server](m5-001-corpus-search-mcp.md) | m2, m3 | Self-developed Python stdio MCP server with 5 tools backed by DuckDB |
| 002 | [search_agent.exs](m5-002-search-agent.md) | 001 | Natural language search agent using corpus-search MCP + optional Matryoshka |
| 003 | [Validation + eval task](m5-003-validation.md) | 002 | 20 representative queries, pass rate measurement, m5 eval task in Aetheris |

**001** first — the agent depends on it.
**002** and **003** are independent of each other once **001** is done.

---

## Completion gate

Auditors run 20 representative queries against the search agent.
Pass rate ≥ 85% (relevant results returned for each query) recorded before sign-off.

---

## Key design decisions

**Two-tier search.** The corpus-search MCP handles metadata search: client,
FY, document type, path patterns, and keyword search over `raw_excerpt`
(the first 20 lines captured during classification). Matryoshka handles deep
content search when more precision is needed. The agent uses metadata search
first and falls back to Matryoshka only when results are insufficient.

**`raw_excerpt` as lightweight content index.** Classification already captured
the first 20 lines of every document. This is stored in the `classifications`
table and provides free-text search without reading files. Good enough for most
queries; Matryoshka handles the long tail.

**No DuckDB FTS extension.** `ILIKE` with query tokenisation is sufficient for
the corpus size and avoids extension dependency. If query performance becomes
an issue at scale, FTS can be added later.

**Search covers the full corpus.** The `search_corpus` tool queries both
`client_corpus` (migrated, classified files) and `f2_file_index` (all indexed
files including archive). Filters narrow to classified files when needed.

**Corpus-search MCP is a self-developed stdio server.** Lives at
`mcp/stdio/src/corpus-search/`. Registered in `mcp/stdio/README.md` and
`mcp/README.md` per `mcp/CLAUDE.md` conventions. No external MCP framework —
plain Python JSON-RPC 2.0 over stdio.

---

## Reference

- DuckDB schema: `docs/provenance/specs.md`
- MCP server conventions: `mcp/CLAUDE.md`
- Matryoshka integration: `mcp/http/README.md` (or stdio once installed)
- Architecture: `docs/provenance/architecture.md`
