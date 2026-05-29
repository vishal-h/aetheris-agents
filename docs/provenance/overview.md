# Provenance — Document Intelligence for Audit Firms

## The problem

Over years of operation, document storage grows organically. Backups are made of backups.
Files are zipped, re-zipped, and copied across drives without a consistent naming convention
or folder structure. What started as organised client folders becomes a layered archive where
finding a specific document requires knowing who created it and roughly when — knowledge that
lives in people's heads, not in any system.

The result: terabytes of storage, most of it redundant, with the actual working corpus
estimated at under 100GB. Searches are manual. Institutional knowledge walks out the door
when people leave. Recovering a specific document from three years ago takes hours.

---

## What Provenance delivers

Provenance is an intelligent document management system built specifically for audit firms.
It does not replace how you work — it makes your existing documents findable, structured,
and auditable.

At the end of the project, your firm will have:

- **A clean, structured document store** — every document classified by client, financial
  year, and document type, stored in a consistent location
- **A searchable archive** — the existing storage (duplicates, old backups, everything) kept
  intact and searchable, without any permanent deletions in early phases
- **Natural language search** — ask a question in plain English and get the relevant
  documents, without navigating folder structures
- **A full audit trail** — every classification decision, every file moved, every duplicate
  identified is logged and reviewable

---

## How it works — four phases

### Phase 1 — Inventory (weeks 1–2)

We scan everything. No files are moved or deleted. The output is a complete picture of
your current storage: how many files exist, how much is duplicated, what types of documents
are present, and how the data is distributed across clients and financial years.

This phase ends with a report your team reviews and approves before anything else proceeds.

### Phase 2 — Classification (weeks 3–5)

Each unique document is read and classified: which client it belongs to, which financial
year, and what type of document it is (tax form, legal notice, correspondence, accounts, etc.).

The classification rules come from your team — we conduct a structured conversation with a
senior member of staff to capture the taxonomy that currently exists only as institutional
knowledge. That knowledge becomes the engine that classifies every document automatically.

Proposed classifications are reviewed by your team before any files move.

### Phase 3 — Migration (weeks 6–8)

Approved documents are moved to the new, structured store. The original storage is left
completely intact — it becomes a searchable archive. Nothing is deleted.

The new store follows a consistent structure:

```
Client Name /
  FY2024 /
    Tax /
    Legal /
    Accounts /
    Correspondence /
```

From this point, new documents go into the structured store. The old storage is the archive.

### Phase 4 — Search and discovery (weeks 9–12)

With documents classified and structured, natural language search becomes possible.
Your staff ask questions — "Find all legal notices for Client X from FY23" or
"Show me all documents related to this matter" — and get answers directly, without
manually navigating folders.

The archive (old storage) remains searchable on the same terms.

---

## What we need from you

- **Server access** — a server we can connect to via VPN, with access to the NAS
- **A taxonomy session** — one hour with a senior staff member to capture your document
  classification rules. This is the most important input to the project.
- **A review contact** — one person who approves classifications and migration decisions
  at the end of each phase before we proceed
- **Patience with Phase 1** — the inventory scan of terabytes of data takes time.
  Nothing changes during this phase.

---

## What does not change

- You do not need to change how you work during the project
- No documents are permanently deleted without explicit approval
- The old storage remains accessible throughout
- Your existing NAS setup continues to function as-is

---

## Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Documents misclassified | Human review gate before any file moves |
| Something important only in a zip | Zip contents inventoried before any deletion considered |
| Institutional knowledge not captured | Taxonomy session recorded and reviewed before classification runs |
| System unavailable during scan | Scans are resumable; no data loss on interruption |
| Wrong document deleted | No deletions in Phases 1–3; archive preserved indefinitely |
