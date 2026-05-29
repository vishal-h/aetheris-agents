# provenance/m2: Taxonomy session

## Context

Classification agents are only as good as the rules they apply. Rather than
inferring the taxonomy from the corpus (which produces inconsistent results),
Provenance captures it explicitly from a senior auditor in a structured session.

The output is `agents/taxonomy.md` — a human-authored document that becomes
the classification system prompt. All classification agent runs read this file.
It is the single source of truth for client names, FY conventions, and document
types.

This is a **human step with a script assistant**, not an automated step.
The script conducts the interview; a senior auditor provides the answers.

## What to build

`scripts/taxonomy_session.py` — an interactive CLI that conducts a structured
interview and writes `agents/taxonomy.md`.

### Interview sections (in order)

**1. Clients**
- How many clients does the firm manage? (approximate)
- List the client names or codes used in filenames/folders (e.g. "ACME", "acme_pty")
- Are there aliases or abbreviations? (e.g. "acme" = "Acme Pty Ltd")
- Any clients whose files are never mixed with others?

**2. Financial year convention**
- Does the firm use calendar year (Jan–Dec) or Australian/UK FY (Apr–Mar)?
- How is the FY labelled in filenames? (e.g. "FY2024", "2023-24", "FY24")
- Which month marks the FY boundary?

**3. Document types**
- What are the main document categories? (prompt with defaults: tax, legal,
  accounts, correspondence, other)
- For each type: what keywords, filename patterns, or content signals identify it?
  (e.g. "BAS", "GST", "tax return" → tax; "ASIC", "notice", "deed" → legal)
- Are there subtypes worth tracking? (e.g. tax/BAS vs tax/income-return)

**4. Naming patterns**
- Do filenames typically include the client name? The year? The document type?
- Are there common prefixes or suffixes? (e.g. "DRAFT", "FINAL", "v2", "_signed")
- What language are most document headers written in?

**5. Special cases**
- Are there documents that span multiple clients? How to handle?
- Are there confidential documents that should be flagged regardless of type?
- Any folders or path patterns that should always map to a specific client?

### Output format

The script writes `agents/taxonomy.md` with this structure:

```markdown
# Provenance Document Taxonomy
Generated: {datetime}
Auditor: {name}

## Clients
| Client ID | Full name | Aliases | Notes |
...

## Financial year convention
- Format: FY{YYYY} (April–March)
- Example: FY2024 = April 2023 – March 2024
- Boundary month: April

## Document types
### tax
Keywords: BAS, GST, tax return, income statement, PAYG, franking credits
Filename signals: tax, bas, gst, return
Content signals: "Australian Taxation Office", "taxable income"

### legal
...

## Classification rules (for the agent)
When classifying a document:
1. Check the file path for client ID or known alias
2. Check the first 20 lines for client name, FY indicators, and document keywords
3. If confident (>0.85): assign client, FY, doc_type directly
4. If uncertain (0.50–0.85): assign best guess, set confidence accordingly
5. If client unidentifiable (<0.50): set client = "unknown", doc_type as best effort

## Edge cases
...
```

### CLI

```
python3 scripts/taxonomy_session.py [--output agents/taxonomy.md] [--auditor NAME]
```

Non-interactive mode (for testing):
```
python3 scripts/taxonomy_session.py --non-interactive --output /tmp/taxonomy.md
```
Non-interactive mode writes a minimal template with placeholder values.

## Acceptance criteria

- [ ] Script runs interactively without errors
- [ ] `--non-interactive` mode produces a valid template file (for CI)
- [ ] Output file follows the structure above
- [ ] `agents/taxonomy.md.example` committed as a sample for reference
- [ ] `pytest tests/test_taxonomy_session.py` passes (non-interactive mode + structure checks)
- [ ] Script noted in `docs/provenance/runbook.md` under "Before m2 begins"

## Files to create

- `provenance/scripts/taxonomy_session.py`
- `provenance/agents/taxonomy.md.example`
- `provenance/tests/test_taxonomy_session.py`

## Notes

The `agents/` directory is gitignored for `*.md` files that contain real client
data. Add `!agents/taxonomy.md.example` to `provenance/.gitignore` so the example
is committed but the real `taxonomy.md` is not.

The real `taxonomy.md` is generated once per engagement and stored securely
alongside the `.env.google-drive` credentials — not in the repo.

`taxonomy.md` should be short enough to fit in an LLM context window without
truncation (~2000 tokens maximum). If the auditor's answers produce more than
this, the session script should warn and suggest consolidation.
