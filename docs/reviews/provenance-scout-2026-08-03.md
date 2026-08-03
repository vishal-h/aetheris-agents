# Provenance — scout report, 2026-08-03

**Type:** reconnaissance, read-only. No code changed, no docs edited, no fixes applied.
**Requested by:** claude-ui, for an investor-facing positioning assessment and a
project-knowledge export decision.
**Repos:** `aetheris-agents/` at `2f87738`; `aetheris/` (harness) for run/eval stores.

---

## Headline

Provenance is a six-milestone document-intelligence pipeline for audit firms — scan,
classify, migrate, zip-archaeology, corpus search, dashboard — and it is more built
than the brief assumed: the Rig dashboard ships six of its seven planned views, and
the human approval gate exists as a real Tauri write path, not an aspiration. What
works end to end is the scan stage and the read-and-approve UI over whatever a scan
produced. What does not is everything after it: **no classification, migration, zip,
or search agent has ever executed** — across 953 harness runs there are exactly two
Provenance runs, both `provenance-scan`, both on 2026-05-29, one of them failed — and
both corpus databases on this machine hold zero classifications and zero migrations.

---

## Corrections to the brief

1. **Rig lives at `rig/` in this repo**, not the sibling. *Verified absent:* no `rig/`
   and no `src-tauri/` in `../aetheris/` (`find /home/it/sandbox/elixirws/aetheris
   -maxdepth 2 -name rig -o -maxdepth 2 -name src-tauri`; 0 hits).
2. **Six of seven dashboard items are shipped**, all seven boxes unchecked — see Q2.
   The checklist is stale documentation, not a to-do list.
3. **The `rig/CLAUDE.md` manifest pin is exactly HEAD.**
   `docs/project-knowledge-manifest.md:33` pins `5a5089b`;
   `git log --oneline 5a5089b..HEAD -- rig/CLAUDE.md` → **0 commits**. It is not
   stale, and the premise that its checklist "cannot be trusted as current state"
   because of the pin does not hold — the file's *content* is wrong, its pin is right.

Premise 3 is the instructive one. Staleness was inferred from a date — last changed
2026-06-11, seven weeks before the export — but an unchanged file is pinned correctly
*because* nothing changed it. Drift was inferred from age when the manifest was doing
its job. That is the **silent-wrong-answer** class in its confident form: a wrong
answer arrived at with nothing present to prompt doubt.

What the corrections do not move: a shipped review UI with an empty `classifications`
table is still a demo. The gap is not build. It is a first real corpus through the
pipeline.

---

## The load-bearing finding: the pipeline has never been run on a populated corpus

Established three independent ways, so it is not an artifact of looking at the wrong
database.

**1 — Both corpus DBs are empty of everything past the scan stage.**

```
$ duckdb -readonly /home/it/sandbox/provenance-test/corpus.duckdb -c \
    "SELECT 'scan_runs' t, count(*) n FROM scan_runs UNION ALL
     SELECT 'f2_file_index', count(*) FROM f2_file_index UNION ALL
     SELECT 'classifications', count(*) FROM classifications UNION ALL
     SELECT 'migrations', count(*) FROM migrations UNION ALL
     SELECT 'zip_inventory', count(*) FROM zip_inventory;"
scan_runs 1 · f2_file_index 26 · classifications 0 · migrations 0 · zip_inventory 0
```

Same query against the tracked fixture
`provenance/tests/fixtures/sample_corpus.duckdb`: `scan_runs` 1, `f2_file_index` 30,
`classifications` **0**, `migrations` **0**, `zip_inventory` 2.

**2 — The harness run store has two Provenance runs, ever.**

```
$ sqlite3 -readonly aetheris/priv/aetheris.db \
    "SELECT run_id, status, started_at FROM runs WHERE run_id LIKE 'provenance%' ORDER BY started_at;"
provenance-scan-ChshBA|failed|2026-05-29T15:55:18.223659Z
provenance-scan-VTFmSg|done  |2026-05-29T16:16:40.951551Z
```

Out of `SELECT count(*) FROM runs` → **953**. No `classification_orchestrator`,
`classify_batch`, `migration_agent`, `zip_orchestrator`, `zip_archaeologist`, or
`search_agent` run exists. `ls aetheris/priv/runs/ | grep -ic '^provenance'` → **2**,
matching.

**3 — The registered eval has never run.**

```
$ sqlite3 -readonly aetheris/priv/aetheris.db \
    "SELECT t.name, count(r.id) runs FROM eval_tasks t LEFT JOIN eval_runs r ON r.task_id=t.id GROUP BY t.name;"
provenance_search|0        uc1_codebase_qa|6        uc3_skill_extraction|4
uc2_patch_generation|0     uc5_hierarchical_delegation|0     uc_auto_autonomous|0
```

**And the one scan that did run was a toy.**

```
$ duckdb -readonly /home/it/sandbox/provenance-test/corpus.duckdb -c \
    "SELECT status, files_scanned, duplicates_found,
            datediff('second', started_at, finished_at) AS wall_seconds FROM scan_runs;"
complete | 26 | 11 | 0
$ ... "SELECT status, count(*) n, sum(size_bytes) total_bytes FROM f2_file_index GROUP BY status;"
duplicate | 11 | 2378        ok | 15 | 6491
```

26 files, **8,869 bytes total**, wall clock 0.2 s (`started_at 16:17:05.642768` →
`finished_at 16:17:05.843866`). Against `docs/provenance/overview.md:11-12`, which
describes the target as *"terabytes of storage… the actual working corpus estimated
at under 100GB."* The gap between the design target and the only execution on record
is roughly seven orders of magnitude.

**Supporting — the tree is dormant.**
`git log --oneline --since=2026-06-01 -- docs/provenance/ provenance/` → **0 commits**.
Last touch `02c903a` (2026-05-31), while `docs/` HEAD activity runs to 2026-08-03.

### The honest boundary on this claim

This establishes that **no populated corpus is reachable from this machine, and no
repo-visible or harness-visible run history shows that one ever existed.** The
production path documented at `docs/provenance/runbook.md:230` (`/data/corpus.duckdb`)
does not exist here — `ls /data/` → *No such file or directory* — and an exhaustive
sweep (`find /home/it -name "*.duckdb" -not -path "*/node_modules/*" -not -path
"*/_build/*" -not -path "*/deps/*"`) returns only the two Provenance DBs above plus an
unrelated `analytics.duckdb`.

It does **not** rule out a corpus on the firm's own server behind VPN. What it rules
out is any evidence in either repo that such a run happened — no trajectory, no eval
run, no committed report, no non-null `aetheris_run_id`.

So the supportable claim is *"built, shipped, demonstrable; never operated on real
data as far as this repo can show,"* not *"proven never used anywhere."* The deck's
**RUNNING ON THE HARNESS TODAY** banner is not supportable as written. *Ran* on the
harness, twice, in May, on 26 synthetic files — that is a demo claim.

**Second-order: the fixtures are synthetic.** `seed_search_fixture.py` seeds five
placeholder classifications with obvious placeholder tenant names, and the sandbox
tree uses the same. The brief's "the corpus holds real audit-firm documents" does not
describe anything present on this machine. The no-client-data rule was easy to honour
because there is no client data here.

---

## Q1 — Documentation inventory

`ls -R docs/provenance/` → six top-level docs and six milestone READMEs (plus 22 issue
specs under `milestones/m*/`).

| File | H1 / purpose | Last commit | Class |
|---|---|---|---|
| `overview.md` | *Provenance — Document Intelligence for Audit Firms.* Problem statement: organic sprawl, terabytes stored, <100GB real corpus, search is manual. | `cd8299f` 2026-05-29 | **standing reference** |
| `architecture.md` | *Provenance — Architecture.* Agents drive intelligent work, scripts do deterministic ops, DuckDB is the shared layer between agents and dashboard. | `cd8299f` 2026-05-29 | **standing reference** |
| `specs.md` | *Provenance — Technical Specifications.* Opens straight into §1 DuckDB schema DDL; the contract the scripts are written against. | `d652ade` 2026-05-29 | **standing reference** |
| `roadmap.md` | *Provenance — Roadmap.* m1–m6 summary table, each with theme, deliverable, human-review gate. | `cd8299f` 2026-05-29 | **standing reference** |
| `runbook.md` | *Provenance — Runbook.* Operator how-to; env setup through go-live checklist. ~900 lines, the longest. | `02c903a` 2026-05-31 | **standing reference** |
| `duckdb-gotchas.md` | *DuckDB 1.5.3 — Known Gotchas.* "Check here before writing new SQL." Two entries, D1 and D2. | `6883d31` 2026-05-29 | **standing reference** |
| `milestones/m1/README.md` | *m1 — Inventory.* Goal: know exactly what exists before touching anything. | `cd8299f` 2026-05-29 | milestone spec (see note) |
| `milestones/m2/README.md` | *m2 — Classification.* | `f1d1f92` 2026-05-29 | milestone spec |
| `milestones/m3/README.md` | *m3 — Migration.* | `0ab18bd` 2026-05-29 | milestone spec |
| `milestones/m4/README.md` | *m4 — Zip Archaeology.* | `51c5d70` 2026-05-29 | milestone spec |
| `milestones/m5/README.md` | *m5 — Corpus MCP + Search.* | `1694ccb` 2026-05-29 | milestone spec |
| `milestones/m6/README.md` | *m6 — Tauri Dashboard.* | `e023924` 2026-05-29 | milestone spec |

Applying the manifest's own rule (`docs/project-knowledge-manifest.md:67-84`):
architecture/specs/roadmap/overview/runbook are standing reference docs and qualify.
The milestone READMEs are milestone *specifications* that later work is written
against — the same category as the two existing exceptions `rig--protocol.md` and
`rig--bl-007-milestone.md` — but see Q9 for why I recommend only one of them.
No `docs/reviews/*` or `*-implementation-notes.md` exist in this tree, so the
exclusion side of the rule is not exercised here.

**Doc-vs-reality contradictions found:**

- **`architecture.md:173-175` — "Trajectory as audit log."** Verbatim: *"Every agent
  decision — every classification, every migration proposal, every escalation — is
  recorded in the Aetheris trajectory. The auditors can audit the auditor."* This is
  the product's central claim and **the code does not support it**: the join key
  linking a corpus row to its trajectory is declared and never written (Q6). The
  trajectory exists; nothing points at it from the data.
- **`m6/README.md:6-8`** declares *"This milestone is in the `hai-rig` repo, not
  `aetheris-agents`. Claude Code must be running in `hai-rig/`."* Rig is at
  `aetheris-agents/rig/`. The doc names a repo that is not where the code lives — this
  is the likely origin of the brief's own sibling-repo error.
- **No milestone README carries a `Status:` line** (each opens `**Goal:**` instead).
  *Verified absent:* `grep -in "^\*\*Status\|^Status:" docs/provenance/milestones/*/README.md`;
  0 hits. Per-milestone completion state is recorded nowhere in this tree, which is
  why "what is done" had to be reconstructed from code and run history for this report.

**Against `docs/capability-matrix.md` at `e60bcfd` (2026-07-30):** the matrix's
Provenance section (line 115, `## Provenance -- Corpus Management`) lists 7 agents and
16 scripts, matching the tree. One overstatement: it describes `execute_migration.py`
as *"Copy approved files to their destination, verify SHA-256, and log results to
DuckDB."* The verification is against a **stored** hash rather than a re-read of the
source, and the hash is **not** among the logged results — `migrations` has no hash
column (Q5). The matrix is generated from script docstrings, so this reflects the
docstring, not a matrix defect.

---

## Q2 — Rig dashboard: what is actually implemented

`rig/CLAUDE.md:495-504` lists seven items, **all unchecked**. Six are shipped. The
checklist is the wrong artifact to read.

| Feature | Status | Component | Tauri command |
|---|---|---|---|
| Corpus overview | **shipped** | `rig/src/modules/provenance/CorpusOverview.tsx:87-88,315` | `provenance_corpus_summary`, `provenance_client_breakdown`, `provenance_duplicate_groups` |
| Classification review UI | **shipped, incl. write** | `rig/src/modules/provenance/ClassificationReview.tsx:481,486` | `provenance_classification_list` + `provenance_set_classification_status` |
| Migration status view | **shipped** | `rig/src/modules/provenance/MigrationStatus.tsx:208,213` | `provenance_migration_summary`, `provenance_failed_migrations` |
| Scan run history | **shipped** | `rig/src/modules/provenance/CorpusOverview.tsx:130,320` | `provenance_scan_runs` |
| Virtual corpus browser | **ABSENT** | `rig/src/modules/f2/F2Viewer.tsx:5-30` — two hardcoded placeholders | none |
| Zip inventory view | **shipped** | `rig/src/modules/provenance/ZipStatus.tsx:191,196` | `provenance_zip_inventory`, `provenance_encrypted_zips` |
| Agent run history | **shipped** | `rig/src/modules/harness/RunList.tsx:560,640` at `/harness` | `harness_list_runs`, `harness_get_events`, `trajectory_load` |

`rig/src-tauri/src/lib.rs:58-68` registers 11 provenance commands (of 47 total); all 11
have a live frontend consumer under `rig/src/hooks/`, so there are no orphan commands.
Provenance is one route (`rig/src/App.tsx:106-116`) composing four tab-groups into 9
tabs; `rig/src/modules/registry.ts:93-101` registers 7 modules.

**Where checklist and code disagree, the checklist is wrong** — for six of seven rows.
The one honest unchecked box is the virtual corpus browser: `F2Viewer.tsx` contains
`ViewsPlaceholder` and `LabelsPlaceholder` and makes zero `invoke` calls. The
client/FY/doc_type tree does not exist anywhere.

---

## Q3 — The human approval gate

**Two write paths exist, not one. The Rig path is shipped, not aspirational.**

`rig/CLAUDE.md`'s claim that classification review is "the one write path Rig owns" is
**accurate**. `rig/src-tauri/src/commands/provenance.rs:317-341`:

```rust
pub fn provenance_set_classification_status(
    path: String, status: String, reviewer: String, state: State<'_, CorpusState>,
) -> Result<(), String> {
    let write_conn = duckdb::Connection::open(&corpus_path)  // :330
    write_conn.execute(
        "UPDATE classifications SET status = ?, reviewed_by = ?, reviewed_at = now() WHERE path = ?",
        params![&status, &reviewer, &path],
    )
```

Wired end to end: per-row Approve at `ClassificationReview.tsx:340`, bulk at `:267` →
`useSetClassificationStatus()` (`rig/src/hooks/useClassifications.ts:47-60`, typed
`'approved' | 'rejected'`, reviewer auto-filled from `get_system_username`) →
`invoke(...)` at `:56`. Reject is symmetric (`:349`); a review-history tab reads
decided rows back (`:486`).

Mechanism worth noting: `rig/src-tauri/src/lib.rs:119-131` opens the corpus
`AccessMode::ReadOnly` and every other command reads through that handle. This command
is the sole exception — it deliberately opens a **second, read-write** connection from
`state.path`. The read-only invariant is bypassed for exactly this one call.

The CSV round-trip is the other path: `export_for_review.py` →
`approve_classifications.py:61-64`, issuing the identical
`UPDATE classifications SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE path = ?`.

### What is recorded at approval

`classifications` schema, verbatim from `provenance/scripts/init_db.py:35-48`:

```sql
CREATE TABLE IF NOT EXISTS classifications (
    id              TEXT PRIMARY KEY,
    path            TEXT NOT NULL REFERENCES f2_file_index(path),
    client          TEXT,
    financial_year  TEXT,
    doc_type        TEXT,
    confidence      REAL,
    raw_excerpt     TEXT,
    status          TEXT DEFAULT 'proposed',
    classified_at   TIMESTAMP NOT NULL,
    reviewed_at     TIMESTAMP,
    reviewed_by     TEXT,
    aetheris_run_id TEXT
)
```

- **Approver identity:** captured in `reviewed_by`, but **self-asserted and
  unauthenticated** — CSV path defaults to `$USER` with fallback `"unknown"`
  (`approve_classifications.py:81-82`); Rig path fills it from
  `get_system_username`. Neither validates.
- **Timestamp:** captured. CSV path computes `now` **once** at
  `approve_classifications.py:27` and applies it to every row in the batch, so a whole
  import shares one identical timestamp rather than per-decision times.
- **Prior status:** **not recorded.** The UPDATE overwrites `status` in place. The
  pre-check at `approve_classifications.py:43-45,53` reads the current status and then
  discards it (`_, current_status = existing`).
- **What the approver was shown:** **not recorded.** The CSV export truncates
  `raw_excerpt` to 200 chars (`export_for_review.py:51`); nothing persists which
  excerpt, confidence, or taxonomy version was on screen at decision time.

### Rejection

**A rejection is a bare status flip with no reason.** `export_for_review.py:16` exports
a `reviewer_notes` column and `csv.DictReader` reads it (`approve_classifications.py:89`),
but `apply_reviews` references only `path` (:30) and `reviewer_action` (:31) —
`reviewer_notes` is never read. No column exists to hold it. *Verified absent:* no
notes/reason/comment column in the DDL above. The test at
`provenance/tests/test_review_tooling.py:209-217` asserts only that status flips.

The Rig path is the same: `provenance_set_classification_status` takes
`path, status, reviewer` — no reason parameter.

### Can an approval be reconstructed from the DB alone?

**No.** You can recover *that* `reviewed_by` set `status` at `reviewed_at`. You cannot
recover what it was before, why it was rejected, which taxonomy version defined the
doc_type, which agent run proposed it, or what the reviewer saw. For a system whose
pitch is that auditors can audit the auditor, the approval record is a three-column
overwrite.

---

## Q4 — Evidence of real use

**Labelled: dev. The production DB is unreachable, and I am not substituting one for
the other.** `PROVENANCE_DB_PATH=/home/it/sandbox/provenance-test/corpus.duckdb`
(2,109,440 bytes, mtime 2026-05-29). The runbook's production path
(`docs/provenance/runbook.md:230,236`, `/data/corpus.duckdb`) does not exist on this
machine (`ls /data/` → No such file or directory). Not a VPN timeout — the mount point
is absent.

Full numbers are in the load-bearing-finding section above. Condensed:

| Table | Dev DB | Tracked fixture |
|---|---|---|
| `scan_runs` | 1 (`complete`, 2026-05-29, 26 scanned, 11 dupes, 0.2 s) | 1 |
| `f2_file_index` | 26 rows / **8,869 bytes** — 15 `ok`, 11 `duplicate`; 26/26 have `sha256` | 30 |
| `classifications` | **0** — no rows in any status; no confidence distribution exists | **0** |
| `migrations` | **0** — no SHA-256 verification failures because no migration ran | **0** |
| `zip_inventory` | 0 processed / 0 pending | 2 |

**Largest single scan by file count:** the only scan — 26 files, 0.2 s wall clock.

**Is there a number we can honestly state?** Yes, but not a flattering one: *two agent
runs, 26 files, 8.9 KB, one day in May 2026.* Every other number is zero. There is no
honest classification-accuracy figure, no approval-throughput figure, and no migration
integrity record, because none of those stages has run.

---

## Q5 — Migration integrity

Read `provenance/scripts/execute_migration.py`. Of the four claims:

- **SHA-256 computed on both source and destination and compared — REFUTED as stated.**
  The destination is hashed live (`_sha256_file(dst)` at :103, helper :169-174, 64 KiB
  chunks). The source is **not re-hashed**: `_lookup_sha256` (:162-166) reads the
  `sha256` column stored in `f2_file_index` by an earlier scan. Comparison at :104
  (`if actual_sha != expected_sha:`). So it verifies the copy against a **recorded**
  value that may be arbitrarily stale, not against the bytes it actually read. If the
  source changed since the scan, the copy is faithful to the new bytes and the check
  fails; if the stored hash were ever wrong, the check validates nothing.
- **A mismatch aborts rather than logging and continuing — REFUTED.** :105-109 unlinks
  the bad destination, records `status='failed'` with
  `error = "SHA-256 mismatch: expected … got …"`, increments a counter, and
  **continues the loop**. The process still **exits 0**; failure surfaces only in JSON
  counters and `migrations` rows. (Credit where due: a pre-existing destination is
  handled well — hashed at :76-92, equal hash treated as already-migrated, differing
  hash refuses to overwrite.)
- **The `migrations` row records source, destination, hash, status and timestamp —
  REFUTED on hash.** `_upsert_migration` (:185-213) inserts `id, path, dest_path,
  classification_id, status, proposed_at, migrated_at, error` (:205-213). The DDL
  (`init_db.py:51-61`) has **no hash column at all**. The verification happens and its
  result is discarded. `aetheris_run_id` is also never populated (absent from both the
  INSERT column list at :208 and the UPDATE at :201).
- **Nothing is deleted; rule 8 honoured — CONFIRMED.** `_copy_file` (:177-182) uses
  `shutil.copy2`, or chunked `copyfileobj` for files ≥100 MB (:24, :178). *Verified
  absent:* no `unlink`/`os.remove`/`shutil.move` targets `src` anywhere in the file
  (`grep -n "unlink\|os.remove\|shutil.move" provenance/scripts/execute_migration.py`
  → only `dst` at :105 and :145). **It copies.** Consequences: storage doubles, and
  `f2_file_index` is not updated to reflect the new location, so the index still
  describes the pre-migration world.

`rollback_migrations` (:121-155) deletes the destination and resets status to
`proposed`. Safe because sources survive, but unguarded — with no `--since` it rolls
back every `migrated` row (:126-131).

---

## Q6 — Per-document lineage

| Element | Recorded? | Where |
|---|---|---|
| Content hash at ingest | **Yes** | `f2_file_index.sha256` (`init_db.py:10-18`); populated 26/26 in the dev DB |
| Originating scan run | **No** | `f2_file_index` has no `scan_run_id`. `scan_runs` records aggregate counts only (`files_scanned`, `files_new`); no per-file link exists in either direction |
| Classifying **Aetheris run id** on the classification row | **Column exists, never written** | `classifications.aetheris_run_id` declared `init_db.py:47`; omitted from the INSERT at `classify_documents.py:93-96`. Non-null count **0** |
| Taxonomy version in force at classification | **No** | No column, no version concept — see Q7 |
| Approver identity and timestamp | **Yes, weakly** | `reviewed_by` / `reviewed_at`; self-asserted, batch-shared timestamp, no prior status, no reason — see Q3 |
| Migration source, destination, verified hash | **Partial** | `migrations.path` and `.dest_path` yes; **hash no** — no column exists (Q5) |
| Link from a file back to the trajectory that classified it | **No** | Depends entirely on the row above it; nothing else joins |

### The join key — answered unambiguously

**The column exists on four tables and is written by nothing. It is a write-path gap,
not a schema change and not a subsystem.**

Declared: `init_db.py:31` (`scan_runs`), `:47` (`classifications`), `:60`
(`migrations`), `:74` (`zip_inventory`), and `provenance/scanner/src/migrations.rs:39`.
`specs.md:30` even annotates it `-- trajectory reference`.

Never written by any producer:

- `provenance/scanner/src/scan.rs:457` — `INSERT INTO scan_runs (id, root_path,
  started_at, status)`; the updates at :465-489 and :493-519 do not set it either. The
  UUID in `scan_runs.id` is the scanner's own (`main.rs:92 uuid::Uuid::new_v4()`), not
  an Aetheris run id.
- `provenance/scripts/classify_documents.py:93-96` — 9 columns, not this one.
- `provenance/scripts/execute_migration.py:207-213` — 8 columns, not this one.
- `provenance/scripts/process_zip_finds.py:104,228,238` — not set.
- `provenance/scripts/approve_classifications.py:62` — status/reviewer/time only.

The agents *do* mint Aetheris run ids — `scan_orchestrator.exs:13`,
`classify_batch.exs:10`, `classification_orchestrator.exs:30`, `migration_agent.exs:29`,
`zip_orchestrator.exs:29`, `zip_archaeologist.exs:10`, `search_agent.exs:27` (all
`"provenance-*-#{Aetheris.ID.generate()}"`) — but use them only as their own
identifier; they are never passed into SQL. `classification_orchestrator.exs:73,109`
merely prints them into the agent's text summary.

*Verified absent (empirical):* `SELECT count(aetheris_run_id) FROM …` → **0** on
`classifications`, `scan_runs`, `migrations`, `zip_inventory` across both DBs.
*Verified absent (code):* `grep -rn "trajectory" provenance/` → 0 hits.

**Consequence.** Wiring one value into four INSERT statements would convert
`architecture.md:173-175` from a claim into a fact. That is a small, well-defined
change — which makes its absence more surprising, not less. Today the sentence "the
auditors can audit the auditor" describes a capability the data model was designed for
and the write path never delivered.

---

## Q7 — Taxonomy

**The taxonomy is unversioned, untracked, and unstamped. All three.**

- `provenance/scripts/taxonomy_session.py` writes `agents/taxonomy.md` (:279, :301-304).
- **No version field.** The only marker is a wall-clock line at :199 —
  `f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"` — local time, no
  timezone, no semantic version, no content hash. The auditor name (:200) is free text.
  `provenance/agents/taxonomy.md.example:2-3` shows the whole of it:
  `Generated: 2026-05-29 17:01:50` / `Auditor: [AUDITOR NAME]`.
- **Not version-controlled.** *Verified absent:* `agents/taxonomy.md` does not exist on
  disk (`ls provenance/agents/taxonomy.md` → No such file; only `.example`), and
  `provenance/.gitignore` ignores `agents/*.md` except the example. The real taxonomy
  is local-only, so there is no history of what it said at any past moment.
- **No taxonomy version on classifications.** No column in the DDL (Q3), and
  `classify_documents.py:93-96` inserts nine columns, none of them a version.

**Can classifications made under a previous version be identified? No.** There is no
version to compare, no committed history of the taxonomy text, and no stamp on the
rows. An edit to `taxonomy.md` silently changes the meaning of every prior
classification, and nothing in the system can detect that it happened. The only
correlate is `classified_at` versus the taxonomy file's mtime — and the file is
untracked, so even that is unreliable.

There is also no taxonomy table or view anywhere in the schema; the discriminator for
the entire classification stage lives in one gitignored markdown file.

---

## Q8 — Open issues touching Provenance

From `docs/backlog-2026-06.md` at HEAD (the master backlog is in **this** repo; the
sibling has only two standalone ticket files under `aetheris/docs/backlog/`).

- **BL-057 — open.** No `**Status:**` line; section at `docs/backlog-2026-06.md:3977`.
  Disposition row 27 at `:4492`: *"a stub run declaring tools starts no worker and its
  tool calls silently never execute. Blocks un-skipping `OverlayAutonomousTest`. A
  product question (what is a stub run?), not a test fix — walk the six affected
  files."* The six files are named at `:3990-3993`: `loop_test.exs`,
  `pre_tools_test.exs`, `injector_test.exs`, `spawn_agent_test.exs`,
  `skill_extraction_test.exs`, and the overlay test — all harness tests, none in
  Provenance.
  **Does a Provenance agent config hit this path? Conditionally, yes.** No agent
  hardcodes stub (`grep -rn '"stub"' provenance/` → 0 hits), but all seven read
  `provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"`
  (e.g. `scan_orchestrator.exs:10`) and all seven declare tools. The first clause
  `worker_child_spec(%{provider: "stub", mcp_servers: []})` matches on provider without
  looking at tools, so **`AETHERIS_PROVIDER=stub` on any Provenance agent yields no
  worker, silently unexecuted tool calls, and a run that reports `:done`.** It is one
  environment variable away, not structurally excluded.
- **BL-039 — closed.** `:1860` — *"Done 2026-07-26 — harness `ebc3878`"*; disposition
  `:4472` adds `e44d35c` (implementation), `3f561d9` (notes), agents `7d6013a`.
- **BL-024 — open.** No `**Status:**` line; section `:309`, disposition row 19b at
  `:4481`. **Re-run count, 2026-08-03:** of **2,232** `fork_from`-bearing trajectory
  metas, `fork_step` is integer **1,554** and null **678** — **30.4%**, against the
  ~45% (540/1,201) recorded at BL-007 t4. The proportion fell, but the **absolute null
  count grew (540 → 678)**: integer-producing forks simply grew faster. Both provenance
  shapes remain live, so the ticket's design requirement — handle both — is unchanged.
  No shape has aged out.
- **BL-046 — open.** No `**Status:**` line; section `:3164`, disposition row 23c at
  `:4487`: *"Do with the next `:tool_result` reader, not on a calendar."*
  **No Provenance script is among the affected readers** — Provenance reads DuckDB, not
  harness event payloads. *Verified absent:* `grep -rn "tool_result\|payload_json"
  provenance/` → 0 hits.
- **BL-003 — closed, and the cure holds.** `:215` *"Done 2026-07-15. `Aetheris.Sweep`
  ships the cure"*; disposition `:4453` records 76 orphaned rows cured.
  **Current census, 2026-08-03:** `SELECT status, count(*) FROM runs GROUP BY status`
  → `done|786`, `failed|167`. **Zero `running` rows.** Total 953.
- **BL-054 — open, deliberately unscheduled.** Section `:1523`, disposition `:4493`:
  *"Fires whenever the `requires_worker` twelfth slot flakes; the row exists so it has
  a name."* Related BL-075 at `:4498` fires on the next `mix test` red. No status
  change to report; I did not run `mix test` (off-territory for a read-only scout, and
  a red result would need a tracked ticket rather than a mention here).

### `validate_search.py` — not run, deliberately

**I did not buy a number from an instrument already found broken**, and on
investigation the intended workaround is broken too.

The scorer is unreliable by construction: `score_query` (:77-106) matches **regex over
agent stdout/stderr** — `_PATH_PATTERN = /\S+\.\w{2,5}` (:31) — not structured output,
so a path counts as "found" even if the agent printed it inside a negative sentence.
And `--n`, documented as "runs per query" (:115), **is never read** — the loop at
:135-144 runs each query exactly once, so flakiness cannot be measured at all. Twenty
queries × up to 120 s of real LLM calls would have produced a pass rate nobody should
cite.

The intended fix — `seed_search_fixture.py`, whose docstring is *"Seed approved
classifications into a corpus DuckDB for search validation"* — **crashes on the
DuckDB version in use.** Run against a scratchpad copy of the tracked fixture (never
the fixture itself):

```
$ cp provenance/tests/fixtures/sample_corpus.duckdb $SCRATCH/seeded2.duckdb
$ python3 provenance/scripts/seed_search_fixture.py --db $SCRATCH/seeded2.duckdb
_duckdb.CatalogException: Catalog Error: Scalar Function with name changes does not exist!
  File "provenance/scripts/seed_search_fixture.py", line 92, in seed
    inserted += conn.execute("SELECT changes()").fetchone()[0]
REAL EXIT CODE: 1
```

`SELECT changes()` is a SQLite function; DuckDB 1.5.3 has no such scalar. The script
intends to seed **5** classifications and the crash lands after the first INSERT
commits, so it exits 1 having written **1 of 5** — a partial, non-atomic write that
leaves the DB in a half-seeded state (`SELECT count(*) FROM classifications` → 1).

This is a **third DuckDB-compat gotcha of exactly the class `duckdb-gotchas.md` exists
to record** (D1: no `basename()`; D2: no `LIMIT` inside `LIST(... ORDER BY ...)`), and
it is not in that file. Per the agreed rule, seeding was not trivial, so I stopped at
static analysis rather than repairing it — recorded here for a ticket.

**Eval task registration:** `provenance_search` **is** registered — confirmed live in
the harness store (`sqlite3 -readonly aetheris/priv/aetheris.db "select name from
eval_tasks"` lists it) — and **has never been executed** (0 rows in `eval_runs`, query
in the headline section). Registration is imperative-only via
`provenance/scripts/register_eval_task.exs:22`; there is no declarative checked-in
definition, so a DB reset silently drops it. Meanwhile the m5 done-when checkbox at
`docs/provenance/milestones/m5/m5-003-validation.md:126` is still `[ ]` — stale in the
opposite direction from the registration.

### Silent-failure modes in the Provenance path

The disqualifying class for a system whose claim is that it records what happened.
BL-057 is one; these are the others found.

1. **`aetheris_run_id` written by nothing** (Q6). Four tables, zero writes, no error,
   no warning. The audit claim in `architecture.md` fails silently and permanently.
2. **Rejection reasons collected and discarded** (Q3). `reviewer_notes` is exported,
   parsed into the row dict, and never read. The reviewer types a justification and the
   system drops it without complaint.
3. **`approve_classifications.py` updates by a non-unique key.**
   `classifications.path` is not UNIQUE (only `id` is PK), yet the lookup
   (:43-45) does `fetchone()` on one arbitrary row while the UPDATE (:62) hits
   `WHERE path = ?` — **all** rows for that file. Re-classify a file and one approval
   decision silently mutates every version of it, including ones the reviewer never
   saw. The Rig path shares the identical predicate.
4. **`approve_classifications.py`'s error counter is dead.** `errors` is initialised 0
   at :26 and never incremented; the returned count is always 0 regardless of what
   happened.
5. **Migration mismatch logs and continues, exit 0** (Q5). A corrupted copy produces a
   `failed` row and a zero exit status; a caller checking exit codes sees success.
6. **Migration verifies against a stale stored hash** (Q5), and discards the result —
   no hash column on `migrations`.
7. **Taxonomy edits invalidate prior classifications undetectably** (Q7).
8. **Two hand-synced schema sources** — `provenance/scripts/init_db.py` and
   `provenance/scanner/src/migrations.rs` both declare `f2_file_index`/`scan_runs`,
   with no check that they agree. They already differ cosmetically (`VARCHAR(64)` vs
   `TEXT`, a `DEFAULT now()` on `last_scanned` in the Rust side only).
9. **`seed_search_fixture.py` partial-writes then crashes** (above) — 1 of 5 rows, no
   transaction.
10. **Three independent DB-path mechanisms with nothing enforcing agreement:**
    `PROVENANCE_DB_PATH` (Elixir agents, each `raise`-ing if unset), `CORPUS_DB_PATH`
    (MCP server, `mcp/corpus-search/server.py:20`), and a mandatory `--db` argument on
    every Python script. `search_agent.exs:11` bridges the first two by hand. Point two
    of them at different files and every stage succeeds against the wrong database.

---

## Q9 — Manifest recommendation

`docs/project-knowledge-manifest.md` carries 25 rows (lines 27-51) in the format:

```
| export name | repo path | repo | commit | last changed |
```

*Verified absent:* `grep -in provenance docs/project-knowledge-manifest.md` → **0
hits**. Provenance appears in neither the table nor any of the four
"what this table does not include, by rule" blocks (`:67-84`, `:86-98`, `:100-119`,
`:121-134`). Its absence is an **undocumented gap, not a recorded decision** — which
matters, because `rig/CLAUDE.md` directs readers to this tree for "the full Provenance
architecture, specs, and roadmap."

### Proposed rows

Applying the manifest's own inclusion rule — standing reference docs in, working
artifacts out:

| export name | repo path | repo | commit | last changed |
|-------------|-----------|------|--------|--------------|
| `provenance--overview.md` | `docs/provenance/overview.md` | aetheris-agents | `cd8299f` | 2026-05-29 |
| `provenance--architecture.md` | `docs/provenance/architecture.md` | aetheris-agents | `cd8299f` | 2026-05-29 |
| `provenance--specs.md` | `docs/provenance/specs.md` | aetheris-agents | `d652ade` | 2026-05-29 |
| `provenance--roadmap.md` | `docs/provenance/roadmap.md` | aetheris-agents | `cd8299f` | 2026-05-29 |
| `provenance--runbook.md` | `docs/provenance/runbook.md` | aetheris-agents | `02c903a` | 2026-05-31 |
| `provenance--duckdb-gotchas.md` | `docs/provenance/duckdb-gotchas.md` | aetheris-agents | `6883d31` | 2026-05-29 |

**On the milestone READMEs — recommend holding.** They qualify structurally (milestone
specifications, like the `rig--protocol.md` / `rig--bl-007-milestone.md` exceptions),
but exporting six of them adds six rows that describe *intent* with no `Status:` line,
into a manifest whose readers will take them as current state. Given that this report
establishes m2–m5 have never executed, exporting them now would propagate exactly the
"more shipped than it is" impression the corrections section exists to undo. Export
them when there is a status to export.

**Two corrections to make before any export, not after:**

1. `architecture.md:173-175` claims trajectory-backed audit that the write path does
   not deliver (Q6). Exporting it makes an unsupported claim authoritative and
   quotable. Either wire `aetheris_run_id` or soften the claim first.
2. `m6/README.md:6-8` names the wrong repo for Rig. This error has already propagated
   once — into the brief for this scout.

### On re-pinning `rig/CLAUDE.md`

**Recommend against — it would be a no-op.** The manifest pins `5a5089b` at
`docs/project-knowledge-manifest.md:33`, and
`git log --oneline 5a5089b..HEAD -- rig/CLAUDE.md` → **0 commits**. The pin is exactly
HEAD; the export is current.

**What a reviewer reading the exported copy gets wrong is not caused by staleness — it
is wrong in the file itself, at HEAD.** Specifically, `rig/CLAUDE.md:495-504` presents
seven unchecked "Current Focus" items, of which six are shipped (Q2). A reviewer
concludes the Provenance dashboard is unbuilt and that classification review has no
UI. Both are false, and that false picture is what fed the "Provenance is a demo, not
a deployment" reasoning from the build side.

The irony worth recording: the conclusion survives anyway, on stronger evidence. It is
a demo because nothing has run through it, not because it was never built.

**Recommended instead:** a ticket to correct the checklist in `rig/CLAUDE.md` (tick the
six, leave the virtual corpus browser unticked, note that `F2Viewer.tsx` is a
placeholder), then re-export on the next boundary — at which point the pin advances
naturally. Per the repo's own rule, the manifest-staleness `project_knowledge` WARN is
expected until that export boundary and should be named rather than chased.

**No export performed.** This section is a recommendation only.

---

## Verified absent

Each with the command that established it.

| Claim | Command | Result |
|---|---|---|
| No `rig/` or `src-tauri/` in the harness repo | `find /home/it/sandbox/elixirws/aetheris -maxdepth 2 -name rig -o -maxdepth 2 -name src-tauri` | 0 hits |
| No populated corpus DB anywhere on this machine | `find /home/it -name "*.duckdb" -not -path "*/node_modules/*" -not -path "*/_build/*" -not -path "*/deps/*"` | 4 hits; 2 Provenance (both 0 classifications), 1 unrelated, 1 `.duckdb` config dir |
| Production DB path does not exist | `ls /data/` | No such file or directory |
| No Provenance agent run beyond two scans | `sqlite3 -readonly aetheris/priv/aetheris.db "SELECT run_id FROM runs WHERE run_id LIKE 'provenance%'"` | 2 rows, both `provenance-scan-*` |
| `provenance_search` never executed | `SELECT count(r.id) FROM eval_tasks t LEFT JOIN eval_runs r ON r.task_id=t.id WHERE t.name='provenance_search'` | 0 |
| `aetheris_run_id` never populated | `SELECT count(aetheris_run_id) FROM classifications / scan_runs / migrations / zip_inventory` (both DBs) | 0 in all 8 |
| `reviewed_by` never populated | `SELECT count(reviewed_by) FROM classifications` (both DBs) | 0 |
| No trajectory linkage in Provenance code | `grep -rn "trajectory" provenance/` | 0 hits |
| No rejection-reason column | Full `classifications` DDL, `provenance/scripts/init_db.py:35-48` | no notes/reason/comment column |
| No hash column on `migrations` | Full DDL, `provenance/scripts/init_db.py:51-61` | 9 columns, none a hash |
| Migration never deletes the source | `grep -n "unlink\|os.remove\|shutil.move" provenance/scripts/execute_migration.py` | only `dst` (:105, :145) |
| `agents/taxonomy.md` not on disk / not tracked | `ls provenance/agents/taxonomy.md`; `provenance/.gitignore` | absent; `agents/*.md` gitignored except `.example` |
| No taxonomy table in the schema | `SHOW TABLES` on both DBs | 11 tables, none taxonomy |
| No milestone README has a `Status:` line | `grep -in "^\*\*Status\|^Status:" docs/provenance/milestones/*/README.md` | 0 hits |
| No Provenance agent hardcodes `provider: "stub"` | `grep -rn '"stub"' provenance/` | 0 hits |
| No Provenance script reads harness event payloads (BL-046) | `grep -rn "tool_result\|payload_json" provenance/` | 0 hits |
| Provenance has no manifest row | `grep -in provenance docs/project-knowledge-manifest.md` | 0 hits |
| `rig/CLAUDE.md` unchanged since its pin | `git log --oneline 5a5089b..HEAD -- rig/CLAUDE.md` | 0 commits |
| Provenance tree dormant since May | `git log --oneline --since=2026-06-01 -- docs/provenance/ provenance/` | 0 commits |

---

## Surprises

Things this scout found that the brief did not think to ask about, roughly in
descending order of how much they change the picture.

1. **The checklist was stale in the optimistic direction.** Every prior assumption ran
   the other way — that docs overstate what code does. Here the doc *understated* it by
   six of seven items. Worth internalising: a stale artifact is not reliably
   pessimistic, and "the docs oversell" is itself a bias.
2. **A live Rig instance held a write lock on the corpus DB during this scout.** An
   unqualified `duckdb <path>` failed with *"Conflicting lock is held in
   `rig/src-tauri/target/debug/app` (PID 208076)"*. This is the Q3 concurrency hazard
   observed in the field rather than reasoned about: `provenance_set_classification_status`
   opens a second read-write connection with **no retry and no lock-error handling**, so
   a contended approval surfaces to the user as the raw string
   `Failed to open corpus for write: {e}`. All my subsequent reads used `-readonly`.
3. **`seed_search_fixture.py` is broken and partial-writes** — a third undocumented
   DuckDB-compat gotcha of exactly the class `duckdb-gotchas.md` was created to hold
   (Q8). The file's own premise — "check here before writing new SQL" — did not save
   the script that was written after it.
4. **`ask_human` is real and wired, and I nearly reported the opposite.** The
   `m4-docbuilder` learning in `CLAUDE.md` says `ask_human` is "intentionally excluded
   from the tool set," which reads as harness-wide. It is not — that was a
   docbuilder-scoped choice. The tool exists (`aetheris/lib/aetheris/execution/tool/ask_human.ex:21`,
   dispatched at `loop.ex:464`), is gated by `allow_escalation` in `RunConfig`, and
   **two Provenance agents use it**: `migration_agent.exs:38,96` and
   `zip_orchestrator.exs:38,143,177`. So `architecture.md:165-166`'s approval-gate
   mechanism is real in design — it has simply never run. Recording the near-miss
   because a promoted learning read as more general than it was, which is the same
   over-generalisation failure the promotion rules are meant to prevent.
5. **The classification approval gate does not use `ask_human`** despite
   `architecture.md:165-166` describing escalation as the mechanism for "human approval
   gates between phases." Classification approval is CSV or Rig; escalation is used only
   for encrypted zips and migration. The doc and the implementation chose different
   mechanisms for the same stated concept.
6. **The schema is richer than the pipeline.** The DBs carry 11 tables including four
   views never mentioned in the brief — `client_corpus`, `duplicate_groups`,
   `migration_queue`, `zip_backlog` (`init_db.py:92-142`) — plus `zip_contents` and the
   Rust scanner's `schema_migrations`. The data model anticipated considerably more
   operation than has occurred.
7. **The two DBs were built by different tools.** Only the sandbox DB has
   `schema_migrations`, meaning the Rust scanner ran against it; the tracked fixture was
   built by `init_db.py` alone. So the "same" schema has two provenances, and the
   fixture has never seen the scanner that production would use.
8. **11 Tauri commands, 11 consumers, zero orphans.** Whatever else is true, the Rig
   provenance surface is cleanly wired — every registered command has a live caller.
   That is unusual and worth saying, given how much of this report is gaps.
9. **`search_agent.exs` is the only agent in the entire capability matrix whose tools
   column is MCP servers rather than named harness tools**
   (`docs/capability-matrix.md:145`, `MCP servers (corpus_search, lattice)`). It is the
   most architecturally distinctive agent in the repo and the least exercised — 0 runs.

---

## What this supports, for the positioning decision

Stated plainly, since that is what the scout was for:

- **Supportable:** a six-milestone pipeline is designed and largely built; the Rig
  dashboard ships six views over the corpus; a human approval gate exists as a real
  write path with reviewer attribution; migration copies with hash verification and
  never deletes; the schema was designed for full custody tracking.
- **Not supportable:** "running on the harness today." Two runs, both scans, both
  2026-05-29, one failed, 26 files, 8.9 KB. Nothing has been classified, approved,
  migrated, or searched — ever.
- **Not supportable:** the audit-trail claim. `architecture.md`'s "the auditors can
  audit the auditor" requires a join key that is declared on four tables and written on
  none.
- **The gap is not build effort.** It is one real corpus through the pipeline, plus a
  handful of small write-path fixes (four INSERT statements, one rejection-reason
  column, one hash column, a UNIQUE constraint or an id-keyed UPDATE).

---

*Scout complete. No repairs applied — every defect above is recorded for ticketing, per
the read-only rules of engagement. Findings deferred to tickets: the ten silent-failure
modes in Q8, the two doc corrections in Q9, and the `rig/CLAUDE.md` checklist fix.*
