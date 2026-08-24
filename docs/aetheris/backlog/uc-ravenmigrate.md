# uc-ravenmigrate — RavenDB → PostgreSQL (design brief)

**Status:** parked — **design closed, no blocking open questions.** Ready for
milestone-doc drafting when scheduled.
**Type:** design brief. §8 records the decisions and their rationale.
**Date:** 2026-08-05 (rev 2 — closes all four open questions)

---

## 1. Framing — the data migration is not the project

The proposed pipeline was `profile → map → transform → validate → migrate → reconcile`.
Given the settled parameters (§2), that describes the *small* half of the work.

A few thousand documents across fewer than 30 collections, no extended RavenDB
features, and an agreed downtime window is not a data engineering problem. It is a
script that runs in under a minute, profiles **100% of documents** rather than
sampling, and can be rehearsed end to end against a production copy as many times as
you like before the real cutover.

**The project is the query migration.** The app moves to a PG data layer at the same
time, and every RavenDB query site in the .NET codebase has to be ported. That is where
the risk, the effort, and the durable value are.

### The inversion

`profile data → map → …` has the dependency backwards here. The Postgres schema is
determined by how the application queries, not by what the documents look like. Profile
the **queries** first; the data profile then only has to confirm the shapes those
queries assume.

---

## 2. Settled parameters

| Question | Answer | Consequence |
|---|---|---|
| Does the consuming app change? | Yes — upgraded to a PG data layer; microservices consolidating into a modular single repo | Schema is designed, not inherited. Query sites must all be ported. |
| Cutover style | **One-shot with a downtime window** | No delta capture, no change vectors, no CDC, no live rollback machinery. Halves the data-side project. |
| Motive | Licensing, cost, maintenance, availability of skilled people | Does **not** justify renormalisation. Cheapest faithful landing wins. |
| Scale | A few thousand documents, <30 collections | No batching, no streaming, no fan-out on the data side. Fits in memory. |
| RavenDB extended features | None in use | No unmapped constructs. Current state only; no history to migrate. |
| Failure policy | **Halt** — a failure is a script or mapping bug, not bad data | No quarantine tier, no human adjudication gate. |
| "Query agent" means | **Migration-time porter** — rewrites existing Raven queries into the PG data layer | Runtime query surfaces are out of scope. |
| Data layer | **EF Core** (Npgsql provider) | Preserves the `IQueryable` lever; see §8.1. |
| Consolidation timeline | Weeks | Strict barrier — consolidate, then inventory, then port. See §8.3. |

---

## 3. Profiling the queries — two deterministic sources

Both are scripts producing inventories; the agent reads the inventories and decides.
This is the `scripts do, agents decide` line from `agent-creation-guide.md`.

**a. RavenDB index definitions.** Static indexes are a machine-readable declaration of
the application's access patterns. Every field an index touches needs a real column
(and probably a real index) in Postgres; every field no index touches can live in the
jsonb tail. Auto-indexes are equally informative — they record what the app actually
queried at runtime.

**b. A Roslyn pass over the .NET repo.** Enumerates every data-access call site
exhaustively and deterministically: `Query<T>()`, `Load<T>()`, `Include()`,
projections, and any `IDocumentSession` usage. Output is a classified inventory —
pattern, file, line, entity type.

### The inventory tool lives in the .NET repo (§8.2)

It is a C# project (`Microsoft.CodeAnalysis.CSharp.Workspaces`, `MSBuildLocator` to
open the solution). It belongs in the repo being migrated, where a C# project is
native, where it can reference the solution directly, and where the team can re-run it
without involving Aetheris. `aetheris-agents` stays Python-and-Elixir.

The harness invokes it *there* via `run_command` with a configured repo path — so this
is in-pipeline, not an out-of-band copy step.

Two requirements on the artifact, because the producer sits outside this repo's test
suite:

- **Stamp the source commit SHA and tool version into the JSON.** Without it you cannot
  tell whether an inventory matches the tree agents are porting against — precisely the
  failure the consolidate-first ordering exists to prevent.
- **Validate the shape on ingest.** A committed JSON Schema plus a Python validator as
  step 0 on the harness side, so a malformed artifact fails loudly rather than producing
  strange agent behaviour. Cross-repo artifact seams are where this rots.

### Sites that will not port mechanically

Inventory these first; they set the true size of the project.

- `Load<T>()` by string ID — trivial individually, but the pattern is everywhere.
- `Include()` — EF Core has `Include` too, but it operates over **navigation
  properties that do not exist yet**. Every one is a modelling decision, and the count
  of `Include()` sites is the best early proxy for total modelling work.
- Anywhere the app depends on Raven's stale-index reads or eventual-consistency
  semantics. In Postgres those reads become strongly consistent — usually a silent
  improvement, occasionally a behaviour change.
- Projections into anonymous or DTO types where Raven's server-side projection has no
  direct equivalent.

---

## 4. Target schema shape

**Entity-shape-preserving.** One table per collection. Real columns for fields the
queries touch (from §3a); `jsonb` for the remaining tail, mapped natively by the Npgsql
provider.

**Do not renormalise.** Nothing in §2 justifies it — the motive is cost and staffing,
not relational analytics. At a few thousand rows, performance is a non-issue: index for
semantics, not for speed.

Shape preservation is also what makes the query port cheap. Raven's `Query<T>()` and EF
Core's `DbSet<T>` are both `IQueryable`, and `IDocumentSession` → `DbContext` is a close
conceptual match — both unit-of-work with an identity map, with `SaveChanges()` nearly a
rename. Renormalising forfeits that lever.

### Identity — keep the Raven string IDs

Use the Raven document ID (`students/1-A`) directly as a `text` primary key. Every
cross-document reference stays valid with **zero identity remapping and no translation
table**. Foreign keys become text columns; navigation properties are declared over them.

> **Retraction.** An earlier recommendation in discussion was to mint deterministic
> UUID v5 keys, reusing `api/gateway/scripts/build_etl_job.py`. That was sized for a
> large migration wanting clean new keys. At this scale it is strictly more machinery
> for no benefit. Do not do it.

> **Rejected — the compatibility shim.** A wrapper presenting a Raven-shaped surface
> over EF Core would shrink the port diff, but it ossifies Raven semantics into the new
> codebase permanently. The port is small enough not to need the accelerant.

---

## 5. The data half — disposable, but exhaustive

**Determinism.** Export RavenDB to a content-addressed JSONL snapshot first; every
downstream stage reads the snapshot and is pure and replayable. Same rule as uc-inbox:
the agent never touches live state. Mirrors eduloka's bronze layer exactly.

**Reconciliation is exhaustive, not statistical.** At this scale, diff *every* document
round-trip: source document → mapped row → canonical projection → compare. Acceptable
delta is **zero**. Row counts alone are not reconciliation — a checksum over the
canonical projection is what catches silent transform errors.

**Rehearsal is the safety net, not tooling.** Run the whole pipeline against a
production copy twenty times before cutover day. Worth more than any amount of clever
migration machinery, and only affordable because the dataset is small.

**These scripts are disposable.** Profiler, per-collection mappers, loader — written
once, rehearsed, then deleted. Do not gold-plate them and do not generalise them.

**Independent of consolidation.** The data half depends only on the schema decision, so
it runs in parallel with everything in §6 regardless of sequencing.

---

## 6. The query half — the actual project

**Shape:** Roslyn inventory (§3b) → classify by pattern → route by class → gate on
`dotnet build` + `dotnet test` → halt on red.

### Route by pattern class, not one blanket method (§8.4)

The classified inventory is what makes this per-class rather than a single global
decision:

| Class | Method | Why |
|---|---|---|
| Deterministic renames (bulk `Load<T>()`, mechanical `Query<T>()`) | **Roslyn codemod** — no agent | Exact and verifiable. Same toolchain, already in that repo. Scripts do, agents decide, applied to the port itself. |
| Judgment sites — `Include()`, projections, stale-index dependencies | **Harness runs** | Real modelling decisions; also where the trajectory corpus has signal. |
| First few of each distinct pattern | **Harness runs** | Seeds the corpus and the eval baseline. |
| Bulk mechanical remainder | Whatever is fastest | 200 identical renames teach a skill extractor nothing the first three didn't. |

**The done-check is the best of any use case so far.** `dotnet build` and `dotnet test`
are free, machine-checkable done-conditions satisfying methodology §1.3 without
inventing a validator. An agent whose output must compile and pass tests is
well-bounded in a way "propose a mapping" never is.

**Fan-out** uses the existing `spawn_agent` + `wait_for_all` pattern (as in provenance
classification and eduloka).

### Convergence is a separate proof from correctness

Re-run the inventory at the end. `dotnet build` + tests prove **nothing broke**; a fresh
inventory returning **zero remaining Raven call sites** proves **nothing was missed**.
Those are different claims and the milestone needs both. Take the initial inventory as
an immutable work list; the re-run is the exit criterion.

---

## 7. What is durable, and the decision it requires now

**Disposable:** everything in §5.

**Durable, in descending order of value:**

1. **The Roslyn call-site inventory tool.** Nothing about "enumerate every data-access
   call site in a .NET repo and classify by pattern" is Raven-specific. It also serves
   the microservice→modular-monolith consolidation already underway, and any future
   EF6→EF Core or Dapper swap. Living in the .NET repo (§3) is what keeps it reusable.
2. **The fan-out-with-compile-gate pattern** — one agent per call site, build+test as
   the done-check, halt on red. A methodology §7 promotion candidate: a standing
   instruction in `CLAUDE.md`, not a script.
3. **The translation corpus.** Every ported site is a (before, after) pair. The
   machinery exists and is idle for this class of work: `extract_skill_hints.py`, the
   skills table (`examples_json`, `source_run_ids_json`), and the m11 eval store. A
   query-porting skill extracted from the judgment-class trajectories, with an eval task
   seeded from the first hand-verified ports as its baseline, is the m04/m11 design
   intent applied.

### The cost, now bounded

The corpus exists only for ports that run through the harness as recorded trajectories.
Per §6 routing, that is the judgment classes and the first few of each pattern — not
every site. The ceremony tax is therefore paid where it buys signal and skipped where it
would buy repetition.

> **Correction.** An earlier framing held that harness-vs-editor had to be decided
> globally before the first port. It does not: the classification in §3b makes it a
> per-class routing decision taken *after* the inventory.

**Sequencing:** build the one-shot; do not build the reusable version. A framework
designed against a sample size of one is designed wrong. Instrument for extraction,
harvest after the migration lands, promote at milestone end per the existing ritual.

---

## 8. Decisions taken in design discussion

1. **Data layer: EF Core with the Npgsql provider.** The only option that makes the port
   cheap *and* serves the stated motive. Preserves `IQueryable`, so shape-preserved LINQ
   sites port with small diffs; `IDocumentSession`→`DbContext` is a close analog; EF
   migrations give schema versioning free; largest .NET hiring pool, which is literally
   why the migration is happening. Dapper and raw Npgsql forfeit the LINQ lever and turn
   every site into hand-written SQL, buying predictability and performance not needed at
   a few thousand rows. The usual EF objection (hidden SQL, N+1) is a scale argument that
   does not apply here.
2. **Inventory tool placement: inside the .NET repo**, invoked by the harness via
   `run_command`. Avoids a C# subproject inside a Python-and-Elixir repo while keeping
   the step in-pipeline. Requires the SHA stamp and ingest validation in §3.
3. **Sequencing: strict barrier.** Consolidation is a weeks-long project, so consolidate
   → inventory → port. A stable tree means the inventory does not go stale underneath the
   work and a red build has one candidate cause, not two. *(Had consolidation been
   months, the alternative was porting module-by-module as each landed — a pipeline
   rather than a barrier.)*
4. **Port routing: per pattern class**, per the §6 table. Deterministic renames are a
   codemod, not an agent.

No blocking open questions remain. Residual unknowns are sizing facts the inventory
itself will answer — chiefly the count of `Include()` sites, which drives the modelling
workload.

---

## 9. Reuse map

| Existing asset | Use here |
|---|---|
| eduloka bronze/silver/gold staging + pure `mappers.py` | Direct template for the §5 data pipeline |
| eduloka `upsert_institute.py` | Postgres sink pattern |
| provenance `execute_migration.py` (verify-after-write, log result) | Reconciliation instinct at row granularity |
| provenance scanner extracted to `provenance/scanner/` | Precedent for §3 tool placement — producer lives where it belongs, harness consumes |
| `spawn_agent` / `wait_for_all` fan-out | §6 per-call-site parallelism |
| `conftest.py` skip markers, sprint-case prerequisite loop, `mix aetheris doctor` | How `dotnet` is declared as a use-case prerequisite — no harness change |
| `extract_skill_hints.py`, skills table, m11 eval store | §7 corpus harvest |
| `api/gateway/scripts/build_etl_job.py` UUID v5 | **Not used** — see §4 retraction |

---

## 10. Suggested first milestone shape (not tickets)

Order matters, and it is not the order of the original pipeline.

1. **Consolidation completes** (external prerequisite, §8.3).
2. Roslyn inventory tool built in the .NET repo → classified JSON with SHA stamp;
   ingest validator on the harness side.
3. Raven index definitions → access-pattern report.
4. Schema proposal from (2)+(3), reviewed and **committed as an artifact** — the mapping
   is a checked-in file, not a per-run agent output, or the migration is not
   reproducible.
5. Data pipeline: export snapshot → map → load → exhaustive reconcile. Rehearse.
6. Query port: codemod the deterministic classes; harness fan-out with build+test gate
   on the judgment classes, largest-count pattern first.
7. Convergence: re-run inventory → zero remaining Raven call sites.
8. Harvest: skill extraction + eval baseline from the judgment-class trajectories.

Step 4 is the gate. Steps 5 and 6 are independent once it lands and run in parallel.
