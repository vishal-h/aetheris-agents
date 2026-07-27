# m1-cloudcost — DigitalOcean cost report + orphan detection (report-only)

**Status:** Milestone doc — Phase-1 approved-pending-commit. First milestone of the
cloudcost use case; DO-only vertical slice.
**Origin:** uc-cloudcost proposal (2026-07-26) + claude-ui review + Phase-1 iteration.
**Repo:** `aetheris-agents/cloudcost/` (new use case). Runs in its own session, parallel
to the harness backlog.

---

## Goal

Prove the full cloudcost pipeline end-to-end on **DigitalOcean** — fetch → normalize →
detect orphans → compose → report → deliver — on the real DO bill, **read-only**, and
establish the adapter contract (normalized schemas) so later providers are near-mechanical
adds.

## Done-when (milestone)

- The pipeline runs end-to-end via `cloudcost_orchestrator.exs` against the real DO account
  (read-only) and produces a **report (PDF/HTML, local file)**.
- The report is reviewable **without opening the DO console**: totals by service, tag
  coverage + top untagged spenders, MoM delta (from month two), and an **orphan-candidates
  section** with per-candidate `evidence[]` and `monthly_saving_estimate`.
- **≥1 real orphan** surfaced on the actual account with its evidence trail (unattached
  volume / unassociated reserved IP / aged snapshot are the likely DO hits).
- All scripts standalone-runnable and pytest-covered against **recorded DO fixtures**
  (offline, no token needed); sprint case green.

*(The two-billing-cycle before/after evidence is the mainstream-candidacy gate — it accrues
over time and is not a coding blocker. The milestone completes on the first correct
end-to-end run.)*

## NOT in scope (this milestone)

- Any provider but DO (AWS/GCP/Workspace/Linode/GitHub are later milestones; the schema
  absorbs them).
- Any **write** credential or cleanup execution (the P3 cleanup milestone, gated).
- The review/approve queue (the P2 milestone).
- Email/Drive delivery (m1 delivers to a **local file**; productionized delivery is later).
- Automated scheduling (the first evidence runs are manual; scheduling is a later small
  ticket).
- GCP BigQuery, currency conversion, and a SQLite/DuckDB trend store — deferred per the
  brief (flat-file history + original-currency for now).
- The DO **MCP** server — see D6.

---

## Prerequisites (human-owned — provide before the loop reaches its live steps)

The build runs mostly on offline fixtures, but three things are the human's to supply, and
t1 needs the first before it can record real fixtures — so treat the token as effectively a
**t1-start dependency**, not a late one.

1. **Read-only DO API token → `CLOUDCOST_DO_TOKEN`.** Create a DigitalOcean API token scoped
   **read-only** (billing + resource read; no write), and export it in the harness process
   environment *before* `mix aetheris run`. Per **D2** it must be the *only* DO token in that
   environment. Gates: t1 (recording real fixtures + the live `--output` done-check) and t5
   (the end-to-end run). The offline unit tests (t1–t4) do **not** need it — so structural
   work can start before the token lands, but t1 can't *complete* (real fixtures) without it.

2. **A real DO account carrying a genuine orphan.** The ≥1-orphan done-when needs the account
   to actually contain one — an unattached volume / unassociated reserved IP / aged snapshot.
   Confirm one exists, or plant one, before t5's end-to-end run.

3. **Environment tooling.** `pydo` (or `requests`) installed; and, if t4 renders PDF via the
   Docbuilder path, `wkhtmltopdf`/`pandoc` present (rendering HTML instead avoids that system
   dep). `mix aetheris doctor` should read ✅/⚠ (not ❌) for what's required.

**Not needed for m1** (deferred): any DO *write* token, and email/Drive credentials —
delivery is a local file.

---

## Design decisions

**D1 — Record-and-deliver, NOT a verify-target.** Fetches run through `run_command`
(python3 → DO REST), which the harness classifies **`:contained`**; verify *re-executes*
contained tools (under BL-042's netns), so a recorded cloudcost run cannot be cleanly
verified — the fetch re-executes and either fails (no network under the netns) or re-fetches
live and diverges on changed billing data. Cloudcost trajectories are therefore **not
verify-targets**: record-and-deliver only, and the adapters' `--output` JSON files (captured
in record mode) are the run's evidence. The build session must not add or claim verify
support. *(This corrects the proposal's `:uncontained`/record-and-serve framing, which was
inaccurate for the `run_command` path.)*

**D2 — Credential separation is operational, not config-enforced.** Trivial here (one
read-only `CLOUDCOST_DO_TOKEN`), but the pattern is set: read and write tokens live in
disjoint process environments; the reporting run's environment never holds a write token
(this becomes load-bearing at P3). The token is passed via env only — never in `config_json`,
never echoed to stdout/stderr (the trajectory captures both). Set `store_prompts: false` if
provider context is ever sensitive.

**D3 — Scripts do, agents decide.** All DO API calls, pagination, retry, cost math, orphan
heuristics, and confidence scoring live in pytest-covered Python. The orchestrator LLM only
sequences the script calls, routes exceptions, and composes narrative. No cost figure or
orphan selection is ever the LLM's.

**D4 — Honest granularity.** DO's Billing API is invoice/service-level, so cost line items
carry `source_granularity: "service"` and `resource_id: null` — the report renders
service-level cost and never fabricates resource attribution DO's API doesn't give. Per-
resource dollars live as `monthly_cost_estimate` on the **inventory** side (derived from
size/type), which feeds the orphan `monthly_saving_estimate`. Actual-at-service-level,
estimated-at-resource-level.

**D5 — Shared machinery is provider-agnostic; only the adapter is DO-specific.**
`detect_orphans.py` and `compose_report_data.py` operate on the normalized schema (tested on
DO fixtures), so fan-out is a new adapter + fixtures with nothing downstream changing. The
m1 orchestrator is a **linear `run_command` pipeline** (one provider); fan-out to
`spawn_agent × N + wait_for_all` is a later change, noted not built (single-provider
`spawn_agent` is the OrbConfig-overkill the guide warns against).

**D6 — DO integration is REST, not the DO MCP.** DO's REST API has a dedicated Billing API
(balance/invoices/history) and list endpoints for droplets/volumes/reserved-IPs/snapshots/
load-balancers — everything the read-only reporter needs. The DO **MCP** server *also*
exposes read-only billing tools (`balance-get`, `billing-history-list`, `invoice-list`,
`account-get-information`) and likely the inventory reads, so tool *coverage* is not the
deciding factor. REST wins for m1 on **fit**: the MCP returns raw DO shapes, so normalization
to the schema still needs a script — or, worse, the LLM, breaking D3; the fetch is a fixed,
paginated, multi-resource sweep a deterministic script does in one pass, where MCP is many
LLM tool-call round-trips; and only the script path is offline-pytest-testable against
recorded fixtures, which is the testing strategy the whole milestone rests on and the adapter
contract m1 exists to prove. The MCP's genuine upside is *less plumbing* (DO maintains the
surface, auth, pagination); against it, the MCP tool set also carries **write** tools
(`key-create`/`key-delete`) — a broader capability surface than a read-only reporter wants,
where a scoped read-only DO token calling only `list`/`get` is tighter. REST via DO's
official Python client (`pydo`) or `requests` is the integration. *(If MCP is ever
reconsidered at fan-out: it's `:uncontained`/record-and-served — which would make the
proposal's original determinism framing correct — but D1's not-a-verify-target conclusion
holds either way, so it changes nothing m1 needs.)*

---

## Contract refs (read, do not restate)

- `agent-creation-guide.md` (authoritative build reference + pre-flight checklist) and its
  conventions: `__ENV__.file` sandbox, `--output` flag, standalone + pytest with recorded
  fixtures, no `python3 -c` inline, dir-name stdlib-collision check.
- `capability-matrix.md` and both `CLAUDE.md` learning sections.
- The uc-cloudcost proposal — normalized schemas (cost snapshot, resource inventory) and the
  orphan-heuristic catalog with base confidences and modifiers.
- DO Billing API reference (`/platform/billing/reference/` — balance, invoices, billing
  history) and the DO API reference list endpoints for droplets, volumes, reserved IPs,
  snapshots, load balancers. `docs.digitalocean.com/llms.txt` is the index.
- Docbuilder `generate_pdf.py` / `generate_html.py` for the report-render reuse (t4).

---

## Ticket set

### t1 — Use-case scaffold + DO adapter (`fetch_do.py`)

**Scope.** Create the `cloudcost/` use-case tree and the DO adapter. `fetch_do.py` fetches
(a) DO billing — balance, current-period invoice/billing-history — and (b) resource
inventory — droplets, volumes, reserved IPs, snapshots, load balancers, with `state`,
`attached_to`, `created_at`, size/type — and emits **two normalized JSON files** per the
proposal schemas: `do_costs_{YYYY-MM}.json` and `do_inventory_{YYYY-MM}.json`. Auth via
read-only `CLOUDCOST_DO_TOKEN` (env). Pagination + retry + rate-limit handling live in the
adapter. `source_granularity: "service"`, `resource_id: null` on cost items;
`monthly_cost_estimate` derived from size/type on inventory items. `raw_ref` (`do://…`) on
each resource for the evidence trail.

**Contract refs.** agent-creation-guide (adapter conventions); the proposal schemas; DO
Billing API + resource list endpoints (via `llms.txt`); `pydo` (confirm its billing-endpoint
coverage; fall back to `requests` for any endpoint it doesn't expose).

**Touches.** `cloudcost/` scaffold (`agents/ scripts/ data/ tests/ docs/ output/.gitkeep`);
`cloudcost/.gitignore` (excludes real data + `output/`); `scripts/fetch_do.py`;
`tests/conftest.py`; `tests/test_fetch_do.py`; `tests/fixtures/do_*.json` (recorded
responses); `requirements.txt` (`pydo`/`requests`).

**Do-not-generate.** The DO MCP path (REST only); any write/management call (list/get only —
never create/modify/delete); resource-level *cost* fabrication (cost stays service-level;
resource $ is the inventory estimate); any other provider; `python3 -c` inline logic.

**Done-check.**
- `python3 -c "import cloudcost"` fails (dir name is stdlib-safe).
- With `CLOUDCOST_DO_TOKEN` set: `python3 scripts/fetch_do.py --output-dir /tmp/cc` writes
  both files, each schema-valid, with real balance + a populated inventory.
- `python3 -m pytest cloudcost/tests/test_fetch_do.py -v` green against recorded fixtures
  (offline — no token).
- The token appears in neither stdout nor stderr on success or on an auth failure.

**Claude-code prompt.**
> Build the `cloudcost` use-case scaffold and the DO adapter per `cloudcost/milestone.md`
> §t1. Read `agent-creation-guide.md` and both `CLAUDE.md` learning sections first.
> `fetch_do.py` fetches DO billing (balance/invoice/history) and resource inventory
> (droplets/volumes/reserved-IPs/snapshots/load-balancers with state + attachment + age) via
> the DO REST API (`pydo` or `requests`, read-only `CLOUDCOST_DO_TOKEN` from env), and emits
> the two normalized JSON files per the proposal schemas — `source_granularity:"service"`,
> `resource_id:null` on cost items; `monthly_cost_estimate` and `raw_ref` on inventory items.
> Pagination/retry in the adapter. Standalone-runnable; pytest against recorded fixtures
> (offline). Do NOT use the DO MCP, do NOT make any write/management call, do NOT let the
> token reach stdout/stderr. Done-check per §t1.

---

### t2 — `detect_orphans.py` (provider-agnostic heuristics)

**Scope.** Apply the deterministic orphan catalog to a normalized inventory and emit
candidates with `confidence`, `evidence[]` (the specific facts that fired), and
`monthly_saving_estimate`. DO-relevant rules from the proposal: unattached volume >14d
(0.9), unassociated reserved IP (0.95), snapshot older than N days (0.7), stopped droplet
with attached storage >30d (0.6), idle load balancer / zero backends (0.85); untagged-in-
tagged-account → **reported-only, never queued**. Modifiers (additive, capped): recent tag
activity −0.2; ephemeral name pattern (`tmp-`/`ci-`/`test-`) +0.1; `keep=true` tag →
excluded outright. All rules and modifiers are reviewable code, keyed to the **normalized
schema** (not DO shapes).

**Contract refs.** The proposal's heuristic table (rules, base confidences, modifiers); the
normalized inventory schema.

**Touches.** `scripts/detect_orphans.py`; `tests/test_detect_orphans.py`;
`tests/fixtures/inventory_*.json` (crafted edge cases).

**Do-not-generate.** Any LLM in the detection loop; DO-specific field access (operate on the
normalized schema so it's reusable); queuing of a reported-only rule; a hardcoded "now" (take
a reference date param so age rules are testable deterministically).

**Done-check.** Fixtures produce the expected candidates and confidences; a `keep=true`
resource is excluded; an untagged resource is **reported, not queued**; each modifier is
exercised; `evidence[]` names the facts that fired; `pytest` green.

**Claude-code prompt.**
> Build `detect_orphans.py` per `cloudcost/milestone.md` §t2 — deterministic heuristics over
> the **normalized** inventory schema (not DO-specific), emitting candidates with
> `confidence` + `evidence[]` + `monthly_saving_estimate`. Implement the proposal's rule
> catalog and modifiers; reported-only rules are never queued; `keep=true` excludes. Take a
> reference-date parameter so age rules test deterministically. pytest over crafted fixture
> inventories including a `keep=true` case, a reported-only untagged case, and each modifier.
> Done-check per §t2.

---

### t3 — `compose_report_data.py`

**Scope.** Merge the cost snapshot + inventory + orphan candidates into one report-data
structure: totals by service; **MoM delta** vs the prior month's snapshot read from
`cloudcost/history/{YYYY-MM}/`; tag-coverage % + top untagged spenders; the orphan section
(candidates grouped by confidence, each with `evidence[]` + saving). First run has no prior
snapshot → the MoM section renders "no prior month" gracefully, not an error. Written to
merge **N providers** (trivial at N=1). **Persist this run's cost snapshot** into
`history/{YYYY-MM}/` for next month.

**Contract refs.** The normalized schemas; the report-data shape the t4 template consumes.

**Touches.** `scripts/compose_report_data.py`; `tests/test_compose_report_data.py`;
`cloudcost/history/.gitkeep`; `.gitignore` updated to exclude `history/*` (real cost data).

**Do-not-generate.** LLM in the merge/delta; a crash on a missing prior month; committing
history data (gitignored); resource-level cost totals (totals are service-level per D4).

**Done-check.** Correct report data on DO fixtures (totals, tag coverage, orphan section);
first-run no-prior-month path clean; the run's snapshot is written to `history/`; the merge
is N-provider-shaped (a two-provider fixture composes without code change).

**Claude-code prompt.**
> Build `compose_report_data.py` per `cloudcost/milestone.md` §t3 — merge cost + inventory +
> orphan candidates into report data: service totals, MoM delta vs the prior-month snapshot
> in `cloudcost/history/{YYYY-MM}/` (graceful "no prior month" first run), tag-coverage % +
> top untagged, and the confidence-grouped orphan section with evidence + saving. Persist
> this run's cost snapshot to `history/` (gitignored). Write it to merge N providers. pytest
> including the first-run path and a two-provider merge fixture. Done-check per §t3.

---

### t4 — Custom report template + render (local file)

**Scope.** A **custom** cloudcost report layout and a render script that turns t3's report
data into a report document (PDF/HTML) written to a **local file** (no email/Drive this
milestone). Sections: cost summary (service totals + MoM), tag coverage + top untagged
spenders, and the **orphan candidates** section — each candidate showing its evidence and
`monthly_saving_estimate`, grouped by confidence. Reuse Docbuilder's `generate_pdf.py` /
`generate_html.py` render path if it fits the custom layout cleanly; otherwise a purpose-
built renderer.

**Contract refs.** Docbuilder `generate_pdf.py` / `generate_html.py`; the report-data shape
from t3.

**Touches.** `scripts/render_report.py`; `cloudcost/templates/` (the custom layout);
`tests/test_render_report.py`.

**Do-not-generate.** Email/Drive delivery (local file only for m1); any data not present in
t3's report data (render-only — the report never computes or invents a figure).

**Done-check.** t3 report data → a local PDF/HTML with all sections, the orphan section
showing per-candidate evidence + saving; visually reviewable; renders cleanly on the
first-run (no-MoM) data too.

**Claude-code prompt.**
> Build the custom cloudcost report per `cloudcost/milestone.md` §t4 — a render script taking
> t3's report data to a **local-file** PDF/HTML (no email/Drive), with a custom layout: cost
> summary + MoM, tag coverage + top untagged, and a confidence-grouped orphan-candidates
> section showing each candidate's evidence and saving estimate. Reuse Docbuilder's
> generate_pdf/html path if it fits, else a purpose-built renderer. Render-only — never
> compute a figure. pytest including the first-run no-MoM data. Done-check per §t4.

---

### t5 — Orchestrator `.exs` + sprint case + end-to-end

**Scope.** `agents/cloudcost_orchestrator.exs` — `%Aetheris.RunConfig{}` with
`tools: ["run_command"]`, `sandbox_path` via `__ENV__.file`, `overlay_base_dir: nil`,
`context_strategy: :rolling`, `max_context_steps: 6`, `provider: "anthropic"`,
`model: "claude-haiku-4-5-20251001"`, `label: "Cloudcost Orchestrator"`. System prompt = the
**linear** workflow: `run_command python3 fetch_do.py` → `detect_orphans.py` →
`compose_report_data.py` → `render_report.py`, each with the exact `command:`/`args:` format,
plus a Rules section ("all paths relative to the sandbox root; `overlay_base_dir` is nil,
outputs persist; if any step fails, report which and stop — do not investigate or retry").
Add a `cloudcost` case to `aetheris/scripts/sprint.sh` (prereqs: `python3` +
`CLOUDCOST_DO_TOKEN`; run the orchestrator; verify the report file exists). Finally,
**regenerate the capability matrix** (`agents/capability_matrix.exs`) so cloudcost registers
in `docs/capability-matrix.md` and Rig's matrix view — the matrix is a generate step, not a
live scan, so it needs the re-run to surface the new use case.

**Contract refs.** agent-creation-guide (orchestrator conventions, run_command format,
"report failures and stop"); the sprint.sh pattern; `agents/capability_matrix.exs` (the
matrix generator) and how Rig's `CapabilityMatrix` command sources it.

**Touches.** `cloudcost/agents/cloudcost_orchestrator.exs`; `aetheris/scripts/sprint.sh`
(new case); `cloudcost/docs/t5-implementation-notes.md`; `docs/capability-matrix.md`
(regenerated — manifest-tracked, so its staleness is an exempt WARN until the next export;
do not chase it).

**Do-not-generate.** `spawn_agent`/`wait_for_all` (single provider — linear `run_command`);
`write_file`/`read_file` in the orchestrator tools (not needed); any scheduling; any write op.

**Done-check.**
- `cd aetheris && mix run --eval 'Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")'`
  evaluates without error.
- `./scripts/sprint.sh cloudcost` runs the pipeline and finds the report file.
- **End-to-end on the real DO bill** (record mode): a report is produced and **≥1 orphan** is
  surfaced with its evidence; the report is reviewable without opening the DO console.
- `CLOUDCOST_DO_TOKEN` appears nowhere in the trajectory.
- `agents/capability_matrix.exs` re-run; `docs/capability-matrix.md` now lists cloudcost
  (its orchestrator + scripts). Confirm the Rig `CapabilityMatrix` command's data source: if
  it reads the regenerated matrix artifact, cloudcost surfaces in Rig's matrix view; if it
  re-scans agent files, confirm it appears there. (This is the only "surfaces on Rig" step —
  runs already appear in Harness → Runs automatically; a dedicated cloudcost *panel* is out of
  scope, a separate Rig ticket.)

**Claude-code prompt.**
> Build the orchestrator and sprint case per `cloudcost/milestone.md` §t5. Read both
> `CLAUDE.md` learning sections first (cross-repo: the sprint case is in `aetheris/`).
> `cloudcost_orchestrator.exs` is a `RunConfig` with `tools:["run_command"]`, `__ENV__.file`
> sandbox, `overlay_base_dir: nil`, `:rolling`/6, anthropic/haiku, and a system prompt
> sequencing fetch_do → detect_orphans → compose_report_data → render_report with exact
> run_command formats and a "report failures and stop" rule. Linear only — no spawn_agent
> (single provider). Add a `cloudcost` sprint case. Then re-run
> `agents/capability_matrix.exs` so cloudcost registers in `docs/capability-matrix.md` (and
> Rig's matrix view) — confirm the Rig `CapabilityMatrix` command reads the regenerated
> artifact vs re-scans, and note it in the packet. Verify the token never reaches the
> trajectory. Done-check per §t5, including the real-bill end-to-end run producing a report
> and ≥1 orphan.

---

## Sequencing

t1 → t2 → t3 → t4 → t5, mostly linear (t2 and t4 can overlap once t1's schema is fixed and
t3's report-data shape is agreed). t5 is the integration + the milestone done-when.

## Open items carried forward (not this milestone)

- Fan-out to AWS/GCP/Workspace/Linode/GitHub — each a new adapter + fixtures against the
  frozen schema; the resource-level cost path gets its first real proof at AWS/GCP.
- P2 review/approve queue (Provenance migration-queue pattern, resource IDs).
- P3 gated cleanup — separate agent + write tokens + the effect-class re-execution decision
  (a `:contained`-but-non-reproducible marker for the cleanup `run_command`, BL-047-style,
  is a *harness* ticket if we want verify to enforce "never re-execute a delete").
- Email/Drive delivery, automated monthly scheduling, currency conversion, DuckDB trend
  store.
