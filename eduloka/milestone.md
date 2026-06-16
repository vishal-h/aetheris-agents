# m-eduloka-discovery — institute discovery pipeline

> Canonical milestone doc (methodology §1.1). GitHub milestone + issues are
> generated from this file and are mirrors. Scope changes are edited here
> first, then re-synced (methodology §8). Drafted by claude-ui; human approves
> and commits before claude-code generates issues.
>
> **Change log.** r2: added Google CSE as a fourth provider (free, legacy
> engine, usable until 2027-01-01). This split the stage-1 fetch ticket in two
> (t1 core+cse+exa, t2 serp) under the §6 sizing rule; downstream tickets
> renumbered.

## Goal

Stand up the `eduloka/` use case: a provider-swappable, replayable,
medallion-layered discovery pipeline that replaces the legacy `ct-edux` Phoenix
app's CSE ingest, and lands its output in the same `gws_cse` table the live
site reads — with no change to the site. Google CSE is retained as a (free,
legacy) provider until its 2027-01-01 sunset alongside three paid alternatives.
Phase-2 (news/event-driven surfacing) is out of scope; it is enabled by, not
built in, this milestone.

## Inputs

- **Design spike** (this session): `fetch_*` (cse, serper, dataforseo, exa) /
  `map` / `enrich` scripts + `edux_record.py` + tests, 18 passing offline.
  t1–t4 land the spike; they are adoption + done-check + review, not greenfield.
  Treat the spike's `README.md` and `edux_record.py` as the pipeline/schema
  contract.
- Legacy reference: `ct-edux` `lib/gws/cse.ex` (`gws_cse` schema + link-keyed
  upsert) and `anek` `Anek.Gws.Cse` (the CSE response→fields mapping the `cse`
  provider reproduces).

## Contract refs (normative; tickets point at sections, never restate)

- `docs/agent-creation-guide.md` — orchestrator patterns, script design,
  pre-flight checklist.
- `aetheris-agents/CLAUDE.md` — §"Use-case layout", §"Python script
  conventions", §"Agent files", §"Sprint script".
- `docs/milestone-methodology.md` — process, ticket anatomy, done-condition.
- `eduloka/scripts/README.md` — pipeline stages, edux structure, providers,
  caveats (lands in t1–t4; the use-case contract thereafter).
- `eduloka/scripts/edux_record.py` — the edux schema + `to_gws_cse()`
  projection (canonical in code; do not paraphrase its fields in prompts).
- `ct-edux` `lib/gws/cse.ex`, `anek` `Anek.Gws.Cse` — legacy CSE behaviour.
- tools.json manifest schema — `docs/rig/milestones/p4-tools/p4-001-manifest-spec.md`.

## Conventions for this milestone

- Implementation notes → `eduloka/docs/tN-implementation-notes.md` (matches the
  CLAUDE.md "read first" table for existing use cases).
- Review files → `docs/reviews/m-eduloka-discovery-tN-review.md` (methodology §3).
- Target layout (CLAUDE.md §"Use-case layout"): `eduloka/{agents,scripts,tests,
  data,docs,output}` + `milestone.md` `README.md` `runbook.md` `tools.json`.
- "eduloka" does not collide with a stdlib package, so the conftest sys.path
  pattern (CLAUDE.md) applies; no top-level `__init__.py`.

## Ticket sequence

t1 fetch core + cse + exa → t2 fetch serp (serper, dataforseo) → t3 map (silver,
4 mappers) → t4 enrich (gold) → t5 upsert (operational) → t6 orchestrator +
harness wiring → t7 datalake readiness → t8 doc/drift sync. t1–t5 are
pure-Python and independently testable; t6 wires them under the harness; t7–t8
close out analytics-readiness and canonical-doc sync.

---

### t1 — Scaffold + stage-1 fetch core (cse, exa)

**Scope.** After this ticket `eduloka/` exists with the standard layout;
`fetch_base.py` provides the GET and POST helpers + fetcher registry; `fetch.py`
is the CLI; and the `cse` and `exa` fetchers write provider-native raw records
to `data/raw/{provider}.jsonl`. `cse` is the free legacy baseline (native
`start`, real pagemap); `exa` is the semantic/enrichment path.

**Contract refs.** `aetheris-agents/CLAUDE.md` §"Python script conventions"
(stdout-is-contract, exit codes, conftest), §"Use-case layout";
`eduloka/scripts/README.md` §"Providers", §"Run"; `anek` `Anek.Gws.Cse` and
`ct-edux` `lib/gws/cse.ex` (CSE endpoint, params, response shape, 429/403 paths).

**Touches.** `eduloka/scripts/fetch_base.py`, `fetch_cse.py`, `fetch_exa.py`,
`fetch.py`; `eduloka/tests/conftest.py`, `tests/test_fetch.py` (cse + exa
cases); `eduloka/.gitignore` (excludes `data/raw`, `data/edux`, `data/gold`,
`output/`); `eduloka/runbook.md` (env vars); `eduloka/README.md` (stub linking
the scripts README).

**Do not generate.** No mapping/enrichment in fetchers (raw items only). No new
HTTP dependency — stdlib `urllib`. No live API calls in tests. Do not add the
serp providers here (t2).

**Runbook update rule.** Introduces `SEARCH_PROVIDER`, `GWS_CSE_API_KEY`,
`GWS_CSE_ENGINE_ID`, optional `GWS_CSE_REFERER`, and `EXA_API_KEY`. Document in
`eduloka/runbook.md` this commit, including the CSE free 100/day cap and the
2027-01-01 sunset, and flag the Rig agent-config group these keys will need
(rig runbook §"Agent config").

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_fetch.py -q -k "cse or exa or credentials or unknown"
python3 eduloka/scripts/fetch.py --term "edu.in"; test $? -eq 1   # no provider -> error envelope, exit 1
```

**Claude-code prompt.**
> Create the `eduloka/` standard layout and land the fetch core from the spike:
> `fetch_base.py` (GET + POST helpers, `Fetcher` ABC, registry), `fetch.py`
> CLI, and the `cse` and `exa` fetchers. Follow CLAUDE.md §"Python script
> conventions" (JSON to stdout, errors to stderr, exit 0/1, conftest; no
> top-level `__init__.py`). The `cse` fetcher reproduces the legacy
> `anek` `Anek.Gws.Cse` request/response (endpoint, `cr=country{CC}`, native
> `start`) — reference it, do not restate it. Fetchers return raw items only.
> Write the env vars to `eduloka/runbook.md` per the Runbook update rule. Run
> the done-check; put actual output in the review packet.

---

### t2 — Stage-1 fetch: paid SERP providers (serper, dataforseo)

**Scope.** After this ticket the `serper` and `dataforseo` fetchers exist behind
the same registry and CLI, writing raw records identically to t1's providers.

**Contract refs.** `eduloka/scripts/README.md` §"Providers" (billing models,
pagination/geo notes); `aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/fetch_serper.py`, `fetch_dataforseo.py`;
`eduloka/tests/test_fetch.py` (serper + dataforseo cases); `eduloka/runbook.md`
(their env vars).

**Do not generate.** No mapping. No changes to `fetch_base.py` or the t1
fetchers beyond registry entries (already present from the spike). Do not
introduce a shared HTTP client other than the `fetch_base` helpers.

**Runbook update rule.** Introduces `SERPER_API_KEY`, `DATAFORSEO_LOGIN`,
`DATAFORSEO_PASSWORD`. Document in `eduloka/runbook.md` this commit, with the
prepaid/credit notes from README §"Providers".

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_fetch.py -q -k "serper or dataforseo"
```

**Claude-code prompt.**
> Land the `serper` and `dataforseo` fetchers from the spike behind the
> existing registry, returning raw items only. Pagination/geo per README
> §"Providers" (Serper page-based; DataForSEO over-fetch+slice). Add their env
> vars to `eduloka/runbook.md`. Run the done-check; include output.

---

### t3 — Stage-2 map (silver) + edux contract

**Scope.** After this ticket `edux_record.py` defines the edux schema and its
`to_gws_cse()` projection, and `map.py` transforms a raw JSONL file into edux
records at `data/edux/{provider}.jsonl`. Mappers are pure; one per provider; the
`cse` mapper populates `image`/`metatags` from real pagemap, the others
best-effort.

**Contract refs.** `eduloka/scripts/edux_record.py` (the schema — canonical in
code); `eduloka/scripts/README.md` §"edux structure", §"Caveats"; legacy
`gws_cse` schema (the column set `to_gws_cse()` must match).

**Touches.** `eduloka/scripts/edux_record.py`, `mappers.py`, `map.py`;
`eduloka/tests/test_map.py`; `eduloka/tests/fixtures/{cse,exa}.raw.jsonl`.

**Do not generate.** No enrichment (slots stay empty; t4 fills them). Do not
push full `text` into `to_gws_cse()`. No `gws_cse` migration here (t5).

**Runbook update rule.** No new env/config — no runbook touch.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_map.py -q
python3 eduloka/scripts/map.py --in eduloka/tests/fixtures/cse.raw.jsonl --out /tmp/edux.jsonl
python3 -c "import json; r=json.loads(open('/tmp/edux.jsonl').readline()); assert r['image'] and r['metatags']"  # cse pagemap populated
```

**Claude-code prompt.**
> Land stage-2 map from the spike: `edux_record.py`, `mappers.py` (four pure
> per-provider mappers — the `cse` mapper pulls `image` from
> `pagemap.cse_image` and `metatags` from `pagemap.metatags`), `map.py`. The
> field set and `to_gws_cse()` columns are defined in `edux_record.py` and must
> match legacy `gws_cse` — do not restate or alter them. Commit the cse+exa raw
> fixtures. Run the done-check; include output.

---

### t4 — Stage-3 enrich (gold) + enricher versioning

**Scope.** After this ticket `enrichers.py` is a registry of pure
`record -> payload` functions and `enrich.py` writes each under
`enrichment[name]` stamped `_by`/`_at`/`_v`, idempotent per namespace,
producing `data/gold/{provider}.jsonl`.

**Contract refs.** `eduloka/scripts/README.md` §"Enrichment workers";
`eduloka/scripts/edux_record.py` (the `enrichment` jsonb bag);
`aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/enrichers.py`, `enrich.py`;
`eduloka/tests/test_enrich.py`; `eduloka/tests/fixtures/exa.edux.jsonl`.

**Do not generate.** No LLM/network enrichers — the two deterministic examples
only. No cross-namespace writes.

**Runbook update rule.** No new env/config — no runbook touch.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_enrich.py -q
python3 eduloka/scripts/enrich.py --in eduloka/tests/fixtures/exa.edux.jsonl --out /tmp/gold.jsonl
python3 -c "import json; r=json.loads(open('/tmp/gold.jsonl').readline()); assert '_v' in r['enrichment']['keywords']"
```

**Claude-code prompt.**
> Land stage-3 from the spike, adding a per-namespace `_v` to each enricher
> payload. Enrichers are pure; `enrich.py` does the namespaced, idempotent
> write per README §"Enrichment workers". Keep the two examples
> deterministic/offline. Commit the edux fixture. Run the done-check; include
> output.

---

### t5 — Operational upsert + `gws_cse` enrichment migration

**Scope.** After this ticket `upsert_institute.py` writes `to_gws_cse()` rows
into Postgres `gws_cse` (link-keyed upsert, legacy semantics), and one additive,
idempotent migration adds a nullable `enrichment jsonb` column. The live site is
unaffected.

**Contract refs.** `ct-edux` `lib/gws/cse.ex` (`upsert/1` semantics, columns);
`eduloka/scripts/edux_record.py` (`to_gws_cse()` output);
`aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/upsert_institute.py`;
`eduloka/data/migrations/0001_add_enrichment_jsonb.sql`;
`eduloka/tests/test_upsert.py` (`@pytest.mark.integration`, auto-skip if no DB);
`eduloka/runbook.md` (DB env + migration step).

**Do not generate.** No ORM — plain SQL/`psycopg`. Additive migration only; do
not alter existing columns/indexes. No full `text` in the operational row.

**Runbook update rule.** Introduces DB connection env (`EDUX_DATABASE_URL` or
equivalent) and a migration-apply step. Document both, including applying the
migration against the existing `ct-edux` DB and the zero-migration fallback
(fold enrichment into `metatags`) noted in `edux_record.py`.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_upsert.py -q                    # integration skips cleanly without a DB
psql "$EDUX_DATABASE_URL" -f eduloka/data/migrations/0001_add_enrichment_jsonb.sql   # idempotent
```

**Claude-code prompt.**
> Build `upsert_institute.py`: read edux/gold JSONL, project via
> `EduxRecord.to_gws_cse()`, upsert into `gws_cse` keyed on `link` with the same
> insert-or-update semantics as `ct-edux` `lib/gws/cse.ex`. Write the additive
> `enrichment jsonb` migration (`IF NOT EXISTS`). Gate DB tests with
> `@pytest.mark.integration`. Document DB env + migration in `eduloka/runbook.md`
> per the Runbook update rule. Run the done-check; include output.

---

### t6 — Orchestrator agent + harness wiring

**Scope.** After this ticket `agents/eduloka_orchestrator.exs` drives the full
pipeline (fetch → map → enrich → upsert) over a term list using `run_command` +
`spawn_agent` + `wait_for_all`, a capability-matrix agent file exists, and a
`sprint.sh` case runs the pipeline end-to-end against fixtures. The term list is
loaded from a committed, editable config file (`data/terms.txt`) via
`list_terms.py` — never hardcoded in the agent.

**Contract refs.** `docs/agent-creation-guide.md` §"Orchestrator patterns",
§"Standard RunConfig fields", §"Runtime parameters in orchestrators",
§"Pre-flight checklist"; `aetheris-agents/CLAUDE.md` §"Agent files",
§"Sprint script".

**Touches.** `eduloka/agents/eduloka_orchestrator.exs`;
`eduloka/scripts/list_terms.py`;
`eduloka/data/terms.txt` (committed config — note this path is NOT in the
`.gitignore` layer-dir excludes); `eduloka/tests/test_list_terms.py`;
`agents/capability_matrix_eduloka.exs` (repo-root agents dir);
`aetheris/scripts/sprint.sh` (new case before `# Summary`);
`eduloka/runbook.md` (terms file + term selection + provider selection).

**Do not generate.** LLM does not construct file content or compute values —
scripts do, the agent orchestrates. No `read_file`/`write_file` in the tool set.
Include the "report failures and stop" rule.

**Runbook update rule.** Introduces the terms-file config (`data/terms.txt`,
overridable via `EDUX_TERMS_FILE`) and the `SEARCH_PROVIDER` selection per run.
Document the terms file (how to edit it) and the run invocation.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_list_terms.py -q
python3 eduloka/scripts/list_terms.py | python3 -c "import json,sys; assert json.load(sys.stdin)['count'] >= 1"
mix run --eval 'Code.eval_file("eduloka/agents/eduloka_orchestrator.exs")'
cd ../aetheris && ./scripts/sprint.sh eduloka
```

**Claude-code prompt.**
> Write `eduloka_orchestrator.exs` as a `RunConfig` per agent-creation-guide
> §"Standard RunConfig fields" (`__ENV__.file` sandbox_path, `overlay_base_dir:
> nil`, minimal sub-agent tools, "report failures and stop"). The term list is
> obtained by `run_command` into `list_terms.py` (reading `data/terms.txt`) —
> the agent must not hold or hardcode terms. Spawn one fetch→map→enrich→upsert
> sub-agent per returned term; `wait_for_all`. Provider via the
> runtime-parameter pattern (default `cse`). Add `list_terms.py`, a seed
> `data/terms.txt`, `capability_matrix_eduloka.exs`, and a `sprint.sh` case on
> committed fixtures (no live API). Walk the pre-flight checklist. Run the
> done-check; include output.

---

### t7 — Datalake readiness (partitioned bronze + load smoke test)

**Scope.** After this ticket `fetch.py` can write partitioned bronze paths
(`data/raw/provider={p}/dt={YYYY-MM-DD}/…jsonl`) under a flag, and a done-check
loads the partitioned tree with DuckDB to prove it is analytics-ready.

**Contract refs.** `eduloka/scripts/README.md` §"medallion / three-stage";
`aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/fetch.py` (partition mode); `tests/test_fetch.py`
(partition-path unit test); `eduloka/runbook.md` (the flag/env);
`eduloka/scripts/README.md` (promote partition convention to documented mode).

**Do not generate.** No object-storage SDK — local partitioned paths only. Do
not change the JSONL record shape or the default flat path.

**Runbook update rule.** Introduces the partition-output flag/env. Document it.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_fetch.py -q
duckdb -c "select count(*) from read_json_auto('eduloka/data/raw/provider=*/dt=*/*.jsonl')"  # integration; skip if duckdb absent
```

**Claude-code prompt.**
> Add a partitioned-output mode to `fetch.py` (`provider={p}/dt={date}`) behind
> a flag, leaving the flat default intact. Add a path-construction unit test.
> Promote the partition convention in README from note to mode; record the flag
> in `eduloka/runbook.md`. DuckDB load is an integration check — skip if absent.
> Run the done-check; include output.

---

### t8 — Doc + tools.json + drift sync (milestone-end)

**Scope.** After this ticket `eduloka/tools.json` declares every script,
`README.md`/`runbook.md` are complete, the capability matrix includes eduloka,
the drift checker reports zero FAIL, and a milestone summary exists. Doc-sync
ticket (methodology §6 runbook rule, §7 ritual).

**Contract refs.** tools.json schema —
`docs/rig/milestones/p4-tools/p4-001-manifest-spec.md`; `rig/docs/runbook.md`
§"Adding a tools.json manifest"; `docs/milestone-methodology.md` §7;
`docs/capability-matrix.md`.

**Touches.** `eduloka/tools.json`; `eduloka/README.md`, `runbook.md` (final);
`docs/capability-matrix.md` (eduloka row);
`docs/milestones/m-eduloka-discovery-summary.md`.

**Do not generate.** No new behaviour — docs and manifest only. Do not restate
contracts in the README; link to the scripts README and contract docs.

**Runbook update rule.** Sync-only. A missing runbook entry is a defect in the
originating ticket — file it back, do not paper over it here.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/ -q                 # full suite green
python3 scripts/drift_check.py                       # zero FAIL, zero WARN
python3 -c "import json,glob,os; m=json.load(open('eduloka/tools.json')); declared={os.path.basename(s['path']) for s in m['scripts']}; actual={os.path.basename(p) for p in glob.glob('eduloka/scripts/*.py')}; assert actual<=declared, actual-declared"
```

**Claude-code prompt.**
> Author `eduloka/tools.json` declaring every script per the manifest schema so
> none shows the amber undeclared badge. Final pass on `eduloka/README.md` and
> `runbook.md` (link contracts, do not restate). Add the eduloka row to
> `docs/capability-matrix.md`. Run the drift checker to zero FAIL/WARN; write
> `docs/milestones/m-eduloka-discovery-summary.md` (shipped / deferred / open
> questions for the Phase-2 surfacing milestone). Run the done-check; include
> output.

---

## Done definition (methodology §4)

m-eduloka-discovery is **done** when: every ticket's done-check passes; all
`blocking` review findings are dispositioned `fixed` or `overruled-by-human`;
`python3 scripts/drift_check.py` reports zero FAIL; and the §7 learning
promotion is committed (recurring findings → `aetheris-agents/CLAUDE.md`).

## Deferred to next milestone (m-eduloka-surfacing)

Phase-2 news/event-driven surfacing over the enriched corpus (Vertex AI Search
or pgvector); real (LLM/geocode/SERP-fetch-text) enrichers; remote object
storage for the lake; promotion of hot enrichment keys to real `gws_cse`
columns; the discovery-source migration plan off CSE ahead of the 2027-01-01
sunset (paid provider or Vertex), since CSE discovery is time-boxed.
