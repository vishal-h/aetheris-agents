# m2-cloudcost — AWS cost report + orphan detection + optimization spike (report-only, per-provider)

**Status:** **RATIFIED 2026-08-02 (rev 5.1)** — Phase 1 closed; **t1 MERGED** (aetheris-agents
`3bc970b`, review `docs/reviews/m2-cloudcost-t1-review.md`). t2 in progress, against the corrected
contract below (rev 5.1 lands two pre-t2 contract corrections — see the revision log).
**Origin:** m1-cloudcost close (`cloudcost--milestone.md`, CLOSED 2026-07-29) +
`handoff-m2-cloudcost-aws-2026-07-30.md`; decisions A–H settled 2026-07-30 (C amended rev 4).
**Repo state at ratification:** aetheris-agents `3bc970b` — t1 merged, t1 files only; the m1
pipeline is otherwise untouched (two append-only edits, `tests/conftest.py` and
`requirements.txt`). aetheris `fd9ac48`, untouched (t1 is single-repo). Rev 4 was ratified at
`d2667ad`.
**Draft state:** rev 4 drafted at aetheris-agents `bd37e90`.
**Repo:** `aetheris-agents/cloudcost/` (existing use case from m1 — this milestone *adds*
adapters/scripts, it does not re-scaffold).

**Revision log.**
- rev 1 → 2: scope widened (EC2-family → EC2-family + RDS orphans; added the exploratory
  S3/ECR/Secrets optimization spike, t4). Decision G.
- rev 2 → 3: **dropped cross-provider consolidated reporting** (Vishal). Each provider is its **own
  solo run producing its own standard-structure report**, surfaced against its run in Rig. Decision
  H; decision A superseded. Retired the new-provider-caveat, multi-currency, and cross-currency
  open items; mooted the orchestrator-topology question.
- rev 3 → 4: folded four operational corrections from IAM/env setup — (i) corrected S3 IAM action
  `s3:GetBucketLifecycleConfiguration` → `s3:GetLifecycleConfiguration`; (ii) **D2 enforced per-run
  via hermetic launch hygiene** (decision C amended); (iii) a t1 default-chain-poison regression
  guard; (iv) the `env -u …` launch prefix in t3's sprint + runbook. Ratified 2026-08-01; then
  BL-069–BL-073 folded into §Backlog / §Referenced Rig ticket / §Open items (traceability only).
- rev 4 → 5 (post-t1, 2026-08-01): folded the t1 review's ratified contract-changes so t2 starts
  against the corrected contract — **§t2 (a′)** canonical `type` normalization (both adapters +
  `detect_orphans` re-key) + the **canonical `type` vocabulary** enumerated below (completing the
  m1 §Normalized schemas gap: the field existed, its allowed values never did); the **t2 (c)
  cost-model half** (a stopped compute/DB bills no compute, so the stopped-with-storage rule's
  saving must sum the *attached storage*); the **Decision C** profile-neutralization caveat (A2); a
  **§t1** poison-guard offline/live note (A3); the **"one seam" → three seams** correction (state,
  `type`, flat-billed cost model) + a seam-sweep row (**BL-074**); and the **A4** swept-regions t3
  resolution. Applies t1's r0/r1 adjudications; no change to the milestone's goal or scope.
  *Two citation corrections applied at commit, both flagged by claude-code and verified at
  `3bc970b`: the m1 stopped-with-storage forward is `detect_orphans.py:243`, not `:250` (the wrong
  line originated in t1's implementation notes and reached this doc's rev-5 draft; corrected in
  both); and the §Repo-state line now stamps rev 5's own ratification commit rather than carrying
  rev 4's.*
- rev 5 → 5.1 (pre-t2, 2026-08-02): two **contract corrections** adjudicated with Vishal at the
  opening of t2, landed before any t2 code so the ticket runs against the corrected contract.
  (i) **The stopped-with-storage saving is `own + attached`, not `attached` replacing `own`** —
  rev 5's "not the instance's own" hardcoded AWS's `own = 0` into a *shared* rule, i.e. it
  re-created seam #3 while claiming to close it. The additive form is provider-agnostic because
  each adapter already encodes its own cost model in the estimate (§t2 c, §t2 Done-check, §t2
  prompt, D4 corollary, the seam-#3 open-items row). (ii) **The canonical `type`/`state`
  vocabulary's one home is `cloudcost/scripts/_normalized.py`**, imported by `fetch_aws.py`,
  `fetch_do.py` and `detect_orphans.py` — the alternative forces `fetch_do.py` either to
  cross-import from another adapter or to re-declare the constants, which is drift on the very
  seam t2 exists to remove (§t2 Touches, which now also names `fetch_aws.py`: its t1-local
  constants become imports, a recorded byte-identical relocation, not scope creep). Also ratified,
  no doc change needed: the aged manual RDS snapshot **widens** `rule_aged_snapshot` rather than
  adding a second rule (§t2 c). No change to the milestone's goal or scope.

---

## Goal

Add **AWS** as the second provider for the cloudcost use case and run the first real test of the
m1 claim that the frozen adapter contract makes fan-out **mechanical** — while delivering
cost-monitoring and first optimization value on the *real* AWS bill.

Reporting is **per-provider** (decision H): each provider is its own solo `mix aetheris run`
producing its own standard-structure report, one report per run. This is the purest form of the
contract claim — *a new provider = a new adapter + fixtures + its own run, with `detect_orphans` /
`compose_report_data` / `render_report` untouched* — because there is no cross-provider merge step
where provider-specific data could leak into shared machinery.

Two mechanisms, deliberately in **separate lanes** (decision G):

1. **Contract-proof core (t1–t3).** `fetch_aws.py` re-emits the two normalized schemas; the
   downstream scripts run **unchanged** except a small *enumerated* set of contract-adjustments
   (§t2). Orphan detection covers the **orphan-shaped** resource types — EC2-family + **RDS**. Any
   change AWS forces on a downstream script not on the enumerated list means the contract leaked —
   that is the finding, worth stopping on.
2. **Optimization-signals spike (t4, exploratory, non-gating).** A *separate* script → a
   *separate* output section for the **non-orphan-shaped** services (S3 / ECR / Secrets Manager).
   Does **not** touch the frozen schema, `detect_orphans.py`, or the contract proof.

Cost monitoring covers **every** service on the bill regardless of lane — it rides on Cost
Explorer, which is bill-wide.

Same posture as m1: **report-only, read-only, local-file delivery.** No writes, no cleanup, no
review queue, no email/Drive, no scheduling (m1 §NOT in scope carries verbatim).

## Done-when (milestone)

**Core (gating):**
- The AWS pipeline runs end-to-end via `cloudcost_orchestrator.exs` (`CLOUDCOST_PROVIDER=aws`) as
  its **own solo run** against the real AWS account (read-only, launched with the D2 hermetic
  prefix — §Prereqs 2) and produces **its own report** (HTML/PDF, local file) in the standard
  structure.
- The report is reviewable **without opening the AWS console**: totals by service (all services),
  tag coverage + top untagged spenders, MoM (from AWS month two — against AWS's own prior
  snapshot), and an **orphan-candidates section** with per-candidate `evidence[]` and
  `monthly_saving_estimate`.
- **≥1 real orphan** surfaced with its evidence trail (planted unassociated Elastic IP is the
  done-when target; stopped EC2 + attached EBS and/or a stopped RDS instance are optional extras).
- `fetch_aws.py` re-emits **both** normalized schemas; the downstream scripts run unchanged
  **except** the §t2 enumerated adjustments — *that negative result is itself a deliverable*.
- Scripts standalone-runnable and pytest-covered against **recorded AWS fixtures** (offline);
  `sprint.sh cloudcost` green.
- AWS registers in the capability matrix.

**Spike (non-gating — best-effort):**
- t4 produces `optimization_signals_aws_{period}.json` + an "Optimization signals (exploratory)"
  section in the AWS report, pytest-covered against recorded fixtures. A thin/noisy result is a
  **pass** (labeled exploratory), not a blocker.

## NOT in scope (this milestone)

- Any provider but DO + AWS.
- **A cross-provider consolidated / roll-up report.** Reporting is per-provider (decision H).
  Consolidation, if ever wanted, is a later **optional aggregator read-layer** over the normalized
  per-provider snapshots in `history/{provider}/{period}/` — decoupled from the pipeline, not built
  here.
- Any **write** credential or cleanup execution (P3, gated).
- The review/approve queue (P2).
- Email/Drive delivery (local file only), automated scheduling, currency conversion, DuckDB trend
  store — unchanged from m1.
- **Resource-level AWS cost** — decision B settled at **service-level**.
- The AWS **Billing & Cost Management MCP** server (decision F), incl. Cost Optimization Hub /
  Compute Optimizer as the *engine* for S3/ECR/rightsizing. t4 is a hand-rolled read-only spike,
  not that integration; the engine-backed optimization milestone is forwarded.
- Fan-out orchestration (`spawn_agent × N + wait_for_all`) — moot under per-provider solo runs
  (decision H supersedes A).
- **Surfacing reports against runs in Rig** — a real, wanted capability, but its own **Rig ticket**
  (see §Referenced Rig ticket), not cloudcost use-case Python work.

---

## Design decisions

D1–D6 from m1 carry verbatim (not restated). A–H are the m2-specific ratifications (2026-07-30).
**A is superseded by H; C amended at rev 4 (+ profile caveat rev 5); G and H are new since rev 1.**

**D1 (record-and-deliver, not a verify-target)** — unchanged; AWS fetch is `:contained`.

**D2 (credential separation) — remapped for AWS, hazard wider than DO's, enforced per-run.** boto3's
default chain reads `AWS_ACCESS_KEY_ID`/`AWS_PROFILE`, `~/.aws/credentials`, **and** instance
metadata. The adapter builds the boto3 session **explicitly** from `CLOUDCOST_AWS_*` and never
touches the default chain (decision C). Because the operator's workstation legitimately carries a
personal AWS credential (env + `~/.aws/credentials`), D2 is enforced **per invocation** by launch
hygiene that neutralizes the default chain for the harness process only (decision C, §Prereqs 2) —
not by requiring a globally clean environment.

**D3 (scripts do, agents decide)** — unchanged.

**D4 (honest granularity)** — service-level for AWS cost (decision B); per-resource dollars are
inventory estimates. Resource-level cost test forwarded. *Corollary the adapter owns (t1):* a
provider's cost *model* lives in its adapter — a stopped AWS instance bills no compute, so its
estimate is 0.0 (unlike DO, which bills a droplet on-or-off). Keeping that assumption out of shared
machinery is why the stopped-with-storage rule's saving is the instance's own estimate **plus** its
attached storage (§t2 c); because the adapter encodes the model, AWS's own term is 0 and DO's is the
full droplet price, so the same "own + attached" sum is correct for both — no provider fact in the
shared rule.

**D5 (shared machinery is provider-agnostic; only the adapter is provider-specific)** — the
decision m2's **core** tests, now in its cleanest form: each provider is its **own solo linear
run** (already how m1's DO pipeline runs). No multi-provider orchestrator, no merge step. The
`state` and `type` vocabularies and the cost-model assumption are the seams where this had leaked
(§Canonical `type` vocabulary; BL-074).

**D6 (integration is the SDK, not the MCP)** — reaffirmed (decision F).

### A — Orchestrator topology — **SUPERSEDED by H**

Rev 1–2 settled A at "linear multi-provider orchestrator." Rev 3 dropped cross-provider reporting,
so there is no multi-provider orchestrator to make linear-vs-fan-out about. Each provider is a solo
run. Retained only to record the supersession.

### C — Credential env contract + per-run D2 hygiene (amended rev 4; profile caveat rev 5)

Env names: `CLOUDCOST_AWS_ACCESS_KEY_ID` / `CLOUDCOST_AWS_SECRET_ACCESS_KEY` (+ optional
`CLOUDCOST_AWS_SESSION_TOKEN` / `CLOUDCOST_AWS_REGION`). boto3 `Session(...)` built **explicitly**
from these — never the default chain. Credentials via env only; never in
`config_json`/stdout/stderr/trajectory.

**Per-run D2 enforcement (belt + suspenders).** The operator keeps their personal `~/.aws`
credential; the harness run is made hermetic w.r.t. the default chain per invocation:

- **Belt — launch hygiene.** The canonical cloudcost AWS invocation strips the shadow env vars and
  points the credentials-file lookup at nothing, for that process only:
  ```bash
  env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \
      AWS_SHARED_CREDENTIALS_FILE=/dev/null \
      mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
  ```
  `CLOUDCOST_AWS_*` are not in the `-u` list, so they survive. This line is baked into t3's sprint
  case and documented in the cloudcost runbook.
- **Suspenders — adapter guarantee.** The adapter's explicit-session construction means the default
  chain is never consulted even without the belt; t1 proves it with a hermetic default-chain-poison
  regression guard (§t1 Done-check).

**Profile-neutralization caveat (t1, A2).** "Explicit-session construction alone" holds only once
the profile config var is *removed from botocore's resolution*, not merely left unread: a stray
`AWS_PROFILE` naming a nonexistent profile raises `ProfileNotFound` from `get_scoped_config`
*before* boto3 looks at the explicit credentials, so a run supplying a good read-only key would die.
`fetch_aws.py` neutralizes it with `botocore.session.Session(session_vars={"profile":(None,None,None,None)})`
(verified boto3 1.43.14). It fails loud, never silent — so it was never a correctness hazard — but
the "suspenders" clause is exact only with the neutralization. (Same shape as m1 t1's `pydo`
default-pickup correction.)

This replaces rev 1–3's "confirm the global env is clean" pre-flight: D2 holds by construction and
by launch hygiene, every run, without disturbing the operator's personal AWS setup.

### B — AWS cost granularity: **SERVICE-LEVEL** (ratified 2026-07-30)

`ce:GetCostAndUsage`, `MONTHLY`, `GroupBy=SERVICE`, unblended → service-level `line_items`,
`resource_id:null`, mapping 1:1 to DO. Resource-level cost + rate spot-check forwarded (BL-071).

### D — Region scope: **FULL-REGION SWEEP** (ratified 2026-07-30)

Enumerate opted-in regions (`ec2.describe_regions`, bootstrapped from `CLOUDCOST_AWS_REGION` or
`us-east-1`), iterate per-region inventory, union. `CLOUDCOST_AWS_REGIONS` is a documented
override. The report **states the swept-region set** (no-silent-caps). Paginated. *(Render home for
the swept set is a t3 decision — A4, §Open items.)*

### E — Billing currency: **USD** (confirmed 2026-07-30)

AWS bills USD. With per-provider reporting (H) each report is single-currency by construction, so
cross-currency aggregation is **moot** for m2 — see the retired open items.

### F — AWS Billing MCP: **NOT USED; boto3/SDK** (ratified 2026-07-30)

Re-proves D6: default-chain auth (D2 hazard), raw shapes (breaks D3), no offline/sandbox path
(kills the pytest spine). **Forward:** Cost Optimization Hub / Compute Optimizer are AWS's own
optimization engine — the natural source for the *full* S3/ECR/rightsizing milestone (BL-072).

### G — Two-lane design: orphans vs optimization signals (ratified 2026-07-30, rev 2)

Orphan-shaped waste (unattached / unassociated / aged / stopped-with-storage / idle) → the existing
`detect_orphans.py` pipeline on the frozen inventory; covers EC2-family + **RDS**.
Non-orphan-shaped waste (S3 lifecycle/storage-class/incomplete-multipart, ECR no-lifecycle/old-image,
Secrets unused) → a **separate** `detect_optimization_signals.py` (t4) emitting a **separate**
file/section. Contract-integrity rule: t4's render addition is additive, isolated, and labeled —
absent its file, the report is byte-identical to the core.

### H — Per-provider reporting; no cross-provider roll-up (ratified 2026-07-30, rev 3)

Each provider is its own solo `mix aetheris run` producing one standard-structure report, one report
per run — mapping cleanly onto Rig's per-run model. Rationale: optimization actions are per-provider,
and every report is human-analysed before action, so a cross-provider grand-total adds little
actionable insight while adding the one merge step where provider specifics could leak into shared
code. `compose_report_data.py` still runs **per provider** (it merges *that provider's* cost +
inventory + orphans) — only the merge-across-clouds is dropped. Consolidation is not foreclosed:
each provider persists a **normalized** cost snapshot to `history/{provider}/{period}/`, so a
cross-provider total is later re-derivable by a thin read-only aggregator — a separate optional
read-layer, never coupled to the pipeline.

---

## Contract refs (read, do not restate)

- `cloudcost--milestone.md` **§Normalized schemas** — frozen shapes; `fetch_aws.py` re-emits
  *these exact shapes*. §t2 (a′) **enumerates the canonical `type` vocabulary** there (completing a
  gap m1 left — the field existed, its values were never enumerated). **§t2 Scope** — orphan-heuristic
  catalog (RDS extends it in-shape). **§t3/§t4** — report-data shape + render contract.
- `agent-creation-guide.md`; both repos' `CLAUDE.md` learning sections (read *both* — t3 touches
  `aetheris/`).
- `capability-matrix.md`; the `sprint.sh` pattern; `agents/capability_matrix.exs`.
- boto3: EC2, ELBv2 + classic ELB, RDS, Cost Explorer (core); S3, ECR, Secrets Manager, CloudWatch
  (t4 spike).

### Canonical `type` vocabulary (schema-level — enumerated at m2, completing the m1 gap)

`detect_orphans.py` keys every rule on the inventory `type` field, but m1's §Normalized schemas
never enumerated its allowed *values* — so the DO adapter's `droplet` / `reserved_ip` were provider
vocabulary sitting inside shared machinery (the same seam `STOPPED_STATES` occupies). Surfaced at t1
and ratified with Vishal: `type` is **schema-level, not provider-flavoured**. Every adapter emits
from this closed set; §t2 (a′) enumerates it in `cloudcost/milestone.md` §Normalized schemas and
renames the DO adapter onto it.

| Canonical `type` | AWS emits for | DO emits for (renamed at t2 a′) |
|---|---|---|
| `compute_instance` | EC2 instance | `droplet` → |
| `static_ip` | Elastic IP | `reserved_ip` → |
| `volume` | EBS volume | `volume` (unchanged) |
| `snapshot` | EBS snapshot | `snapshot` (unchanged) |
| `load_balancer` | ELB / ALB / NLB | `load_balancer` (unchanged) |
| `database` | RDS instance | — (new at t2 c) |
| `database_snapshot` | RDS manual snapshot | — (new at t2 c) |

t1's `fetch_aws.py` already emits canonical from its first line (fixtures recorded canonical once).
Between t1 and t2, AWS orphan detection does not fire — the rules still key on `droplet`/`reserved_ip`
— which is harmless (detection isn't run end-to-end until t3, and t2 precedes it) and is the same
ordering ratified for `state`.

### AWS field-mapping notes (how AWS populates the frozen §Normalized schemas — not a re-spec)

**Cost snapshot** `aws_costs_{YYYY-MM}.json`: `provider:"aws"`, `currency:"USD"`,
`source_granularity:"service"`, `resource_id:null`; `line_items[]` = CE groups by SERVICE (all
services — Secrets Manager, Tax, S3, ECR, RDS, EC2, …), one line per service; `balance` from CE
month-to-date (`account_balance:null`); `provider_extra` = CE `ResultsByTime` metadata + the opaque
`swept_regions` list (downstream must not key on it generically; render home is A4/t3).

**Resource inventory** `aws_inventory_{YYYY-MM}.json`: frozen first-class fields per resource;
`region` a **real value**; `type` from the **canonical vocabulary** (§Canonical `type` vocabulary);
`state` from the **normalized enum** (§t2 a), canonical `"stopped"` for stopped compute (EC2
`stopped`, RDS `stopped`); `attached_to` per m1 semantics (RDS instance→null when stopped-idle; RDS
snapshot→source DB/null, cross-referenced against the sweep and left face-value when the sweep
didn't complete — t1 F1); `monthly_cost_estimate` from size/type (**0.0 for stopped compute** — no
compute charge); AWS `tags` (incl. load balancers, via `DescribeTags`); `raw_ref` =
`aws://<service>/<region>/<id>`. RDS lands in first-class fields — no `provider_extra`.

**Optimization signals (t4, NOT a frozen-contract shape)** `optimization_signals_aws_{YYYY-MM}.json`:
a *separate* loose list of `{service, resource_id, region, signal, evidence[],
monthly_cost_estimate?, note}` (`signal` ∈ `s3_no_lifecycle_policy` / `s3_incomplete_multipart` /
`s3_empty_bucket` / `ecr_no_lifecycle_policy` / `ecr_untagged_image_accumulation` / `secret_unused`).
Not confidence-scored like orphans; exploratory. The core pipeline never reads it.

---

## m1 open items — final triage after A–H (LIVE / latent / RETIRED)

| m1 open item | Status at m2 | Why |
|---|---|---|
| **`STOPPED_STATES={"off"}`** normalization (seam #1) | **LIVE — t2 a** | Both adapters emit canonical `"stopped"`; constant → schema-level value; 3 pinning tests + DO fixtures update. RDS `stopped` maps here too. One of **three** seams (BL-074). |
| **`type` vocabulary un-enumerated (seam #2)** | **LIVE — t2 a′** | m1 keyed rules on `type` but never enumerated its values; DO's `droplet`/`reserved_ip` were provider vocab in shared machinery. Canonical enum (above) + adapter renames. Surfaced at t1. |
| **flat-billed cost assumption (seam #3)** | **Adapter half done (t1); saving half LIVE — t2 c** | DO bills a droplet on-or-off; AWS doesn't. Adapter emits 0.0 for stopped compute; the stopped-with-storage rule's saving must sum **own + attached storage** (own encodes each provider's model: AWS 0, DO full price). BL-074. |
| **t2 output filename collision** | **LIVE — t2 b** | Each provider writes `{provider}_orphan_candidates_{period}.json`. |
| **Resource-level cost rate spot-check** | **DEFERRED (BL-071)** | B is service-level. Forwarded. |
| **New-provider-caveat render path** | **RETIRED** | Unreachable without a cross-provider roll-up (H). |
| **Multi-currency "No combined total" render path** | **RETIRED** | Reports are per-provider, single-currency (H + E). |
| **Cross-currency aggregation (4 sites in `compose`)** | **RETIRED / moot (BL-070)** | Never aggregate across providers. Dead code left **dormant** for m2, filed for retirement — `compose` stays literally unchanged (pristine negative proof). |
| **Recency-modifier window bound + `last_activity_at` future guard** | **LATENT** | AWS adapter leaves `last_activity_at:null`. |
| **`reported` governance list not in report_data** | Scope question, unchanged | Carry as-is unless wanted now. |
| **BL-067** (matrix assembler LLM-derived block) | Carried | Touched only if t3's matrix regen surfaces it. |

---

## Prerequisites (human-owned)

1. **Read-only IAM user/role → `CLOUDCOST_AWS_*`.** Least-privilege (attached as
   `aetheris-cloudcost-aws` on user `aetheris-ro`):
   - *Core (t1–t3):* `ce:GetCostAndUsage`, `ce:GetDimensionValues`, `ec2:Describe*`,
     `elasticloadbalancing:Describe*` (covers `DescribeTags`), `rds:Describe*`.
   - *Spike (t4):* `s3:ListAllMyBuckets`, `s3:GetBucketLocation`, `s3:GetLifecycleConfiguration`,
     `s3:ListBucketMultipartUploads`, `ecr:DescribeRepositories`, `ecr:DescribeImages`,
     `ecr:GetLifecyclePolicy`, `secretsmanager:ListSecrets`, `cloudwatch:GetMetricData`.
   - **No** `GetCostAndUsageWithResources`; **no** write actions. **Status: DONE** — user
     `aetheris-ro`, policy `aetheris-cloudcost-aws` attached; secrets sourced from
     `~/.secrets/aws-cloudcost.env` (`CLOUDCOST_AWS_*` confirmed present).
2. **D2 per-run launch hygiene (replaces the old global pre-flight).** The operator's personal AWS
   credential (`~/.aws/credentials` and/or `AWS_*` env) may remain in place. Every cloudcost AWS
   run is launched with the hermetic prefix so boto3's default chain cannot shadow the read-only
   key:
   ```bash
   env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \
       AWS_SHARED_CREDENTIALS_FILE=/dev/null \
       mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
   ```
   `CLOUDCOST_AWS_*` survive the strip. This is the canonical invocation (baked into t3's sprint
   case + the runbook); the adapter's explicit-session construction is the code-level backstop
   (t1 poison guard). **Note:** the operator's workstation *does* carry a personal `~/.aws/credentials`
   and a live `AWS_*` env var — which is exactly why the per-run prefix (not a global unset) is the
   chosen enforcement.
3. **A genuine orphan.** Unassociated **Elastic IP** (primary done-when target). Optional: stopped
   EC2 + attached EBS; stopped RDS instance (exercises the RDS heuristic on real data).
   **Status: PENDING** — gates t3's real-bill run only, not t1/t2 offline work. *t1 confirmed the
   live account carries no EC2/EBS/EIP/RDS at all, so the ≥1-orphan done-when rests wholly on the
   planted Elastic IP; the live bill (Secrets Manager / S3 / ECR / Tax) is entirely t4's lane.*
4. **Environment tooling.** `boto3` installed; `mix aetheris doctor` reads ✅/⚠. Optional smoke:
   `( export AWS_ACCESS_KEY_ID=$CLOUDCOST_AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$CLOUDCOST_AWS_SECRET_ACCESS_KEY; aws sts get-caller-identity )`
   → the `aetheris-ro` ARN. **Status: PENDING.**

*No DO token needed for m2* — AWS is a standalone solo run (H). *Not needed (deferred):* any AWS
write credential; the CE resource-level paid opt-in; email/Drive.

---

## Ticket set

Weight in **t1** (adapter, **MERGED** `3bc970b`). **t2** = contract-adjustments + RDS rule. **t3** =
AWS solo run, integration + core done-when. **t4** = the exploratory optimization spike (non-gating).

### t1 — AWS adapter (`fetch_aws.py`): cost (all services) + inventory (EC2-family + RDS) — **DONE (`3bc970b`)**

**Scope.** Add `scripts/fetch_aws.py` (no re-scaffold). Cost via CE `GetCostAndUsage` (service-level,
all services). Inventory via **full-region sweep** — EC2/EBS/Elastic-IP/snapshot/ELB **+ RDS
instances & manual snapshots** — unioned, emitting the two normalized JSON files per frozen
§Normalized schemas, canonical `type` + `state`, `monthly_cost_estimate` (0.0 for stopped compute),
`aws://…` `raw_ref`. Explicit boto3 `Session` from `CLOUDCOST_AWS_*`; paginators; region enumeration
via `describe_regions`.

**Done-check (as shipped).** Both files schema-valid; region-sweep mutation-proven; default-chain
poison guard green live + offline; credentials in neither stream. 62 AWS tests + 157 m1 baseline =
219; 28/28 mutations. Live: 17-region sweep exit 0; real 2026-07 bill = 9 service lines / $4.99.
- *A3 note (offline poison guard):* offline the guard holds only with an **access-key-enforcing**
  stub — the exit-code arm alone goes green under a fallback against a permissive stub. "A green run
  proves it" is exact for the **live** half (AWS is the oracle); the offline suite pins it via the
  stub's key enforcement + a wire-observation assertion (`access_keys_seen() == {CLOUDCOST}`).
  Recorded so the mechanism isn't mis-cited later.

### t2 — Contract adjustments + RDS heuristic + negative proof

**Scope.**
(a) **Normalized `state` enum:** shrink `detect_orphans.py:71 STOPPED_STATES={"off"}` → schema-level
`{"stopped"}`; update `fetch_do.py` to emit `"stopped"` + regen its fixtures; `fetch_aws.py` already
emits it; update the 3 pinning tests.
(a′) **Normalized `type` vocabulary (canonical, schema-level):** enumerate the canonical `type`
values (§Canonical `type` vocabulary) in `cloudcost/milestone.md` §Normalized schemas — an
**amendment-to-complete** (the field existed, its values never did), not a behaviour change. Rename
`fetch_do.py`'s two DO-vocabulary values — `droplet`→`compute_instance`, `reserved_ip`→`static_ip` —
and regen its recorded fixtures (rides the (a) fixture regen). Re-key the two DO-specific rules in
`detect_orphans.py` onto canonical: rename `rule_stopped_droplet_with_attached_storage` →
`rule_stopped_compute_with_attached_storage` (keys on `compute_instance`) and the unassociated
reserved-IP rule (keys on `static_ip`). The generic `volume`/`snapshot`/`load_balancer` rules already
key on canonical values — unchanged. **Also confirm `compose_report_data.py` / `render_report.py`
do not key on any `type` *value*** — a special-case on a value is a *third* leak and its own finding
(extends the (d) negative proof to the `type` field).
(b) **Output filename prefix:** `{provider}_orphan_candidates_{period}.json`.
(c) **RDS heuristic + the cost-model half:** extend the §t2 catalog with RDS rules that fit existing
shapes — stopped RDS instance with allocated storage (mirrors stopped-droplet+storage) and aged
manual RDS snapshot (**widens** `rule_aged_snapshot` to `type ∈ {snapshot, database_snapshot}`
rather than adding a second rule: same age threshold, same 0.7, same type-agnostic evidence
sentence; never fork the threshold — parameterize it if RDS ever needs its own) — keyed on the
normalized schema.

**Cost-model half (seam #3 saving side).** m1 reported the orphan's **own** estimate and named the
attached storage but did not **sum** it (`detect_orphans.py:243`) — an *under-report*. The fix
**adds** attached storage to own, it does not replace own:
`saving = own.monthly_cost_estimate + Σ(attached separately-inventoried storage estimates)`.
Provider-agnostic — the shared rule keys on no provider fact — because each adapter encodes its own
cost model: AWS stopped own = 0.0 (`i-0aaa3333`→16.00), AWS stopped RDS own = storage with no
separate resource (`db-stopped-1`→23.00), DO stopped droplet own = full price
(`drop-stopped-1`→29.00). **Double-count guard:** only separately-inventoried storage counts; RDS
storage is in the instance's own estimate. Structural: `fired()` gains an optional saving, `score()`
honours it.
(d) **Negative proof:** `compose_report_data.py` / `render_report.py` run **unchanged** on AWS data
(single-provider, as m1 shipped); the now-dead cross-provider merge code in `compose` is left
**dormant** (not deleted; retirement is **BL-070**). Any *needed* change to compose/render = a
**contract-leak finding**, documented, not silent.

**Contract refs.** frozen §Normalized schemas + §Canonical `type` vocabulary; §t2 Scope catalog;
STOPPED_STATES + filename open items; the seam sweep (BL-074); decision H (single-provider compose;
dormant merge).

**Touches.** `cloudcost/scripts/detect_orphans.py` (state constant + `type` re-key + rule rename +
filename + RDS rules + `score()`/`fired()` saving); `cloudcost/scripts/fetch_do.py` (state + `type`
mapping — cross-adapter, recorded); `cloudcost/scripts/_normalized.py` (**the canonical
`type`/`state` vocabulary lives here** — `TYPE_*`, `STATE_STOPPED`, imported by `fetch_aws.py`,
`fetch_do.py`, and `detect_orphans.py`); `cloudcost/scripts/fetch_aws.py` (t1-local
`TYPE_*`/`STATE_STOPPED` → imports; byte-identical output, t1 tests stay green);
`cloudcost/milestone.md` (§Normalized schemas — enumerate the canonical `type` vocabulary,
amendment-to-complete); `cloudcost/tests/test_detect_orphans.py`;
`cloudcost/tests/fixtures/do_*.json` + `aws_*.json` + crafted RDS `inventory_*.json`. **Not**
`compose_report_data.py` / `render_report.py` (a change there is the finding).

**Do-not-generate.** Silently widening `STOPPED_STATES`; leaving any provider-flavoured `type` value
in shared machinery; keying compose/render on a `type` *value*; a stopped-with-storage saving that
**replaces** own with attached (or leaves attached unsummed) instead of adding them, or that
double-counts RDS storage already inside the instance's own estimate; a second aged-snapshot rule
where widening the existing one suffices; provider-specific field access in shared machinery;
deleting/altering the dormant merge code (retire via BL-070, not here); any compose/render change
absent a documented contract-leak finding; confidence-scoring S3/ECR-style signals here (that is t4).

**Done-check.**
- AWS fixtures with a stopped-EC2+EBS and a stopped-RDS+storage each produce the expected stopped
  orphan via the normalized enum; **mutation:** a mis-normalized/reverted `state` fails.
- **`type` mutation:** reverting any canonical `type` to DO vocabulary (`compute_instance`→`droplet`,
  `static_ip`→`reserved_ip`) fails a test; DO fixtures/tests green after the rename.
- **Stopped-orphan saving = own + attached, provider-correct:** DO stopped-droplet `== 29.00`
  (24+5), AWS EC2 `== 16.00` (0+16), AWS RDS `== 23.00` (own, no separate storage). **Mutations:**
  drop own → DO reads 5.00 (fails); drop attached → AWS EC2 reads 0.00 (fails); double-add RDS
  storage → RDS reads 46.00 (fails).
- Aged manual RDS snapshot fires the aged-snapshot-shaped rule with `evidence[]`.
- `keep=true` excludes; untagged is reported-not-queued; filename carries the provider prefix.
- `detect_orphans.py`'s m1 suite + new tests green; `fetch_do.py` tests green after fixture regen.
- `compose_report_data.py` / `render_report.py` unchanged (diff shows no edit) and key on no `type`
  value (grep) — or any edit filed as a contract-leak finding.

**Claude-code prompt.**
> Apply §t2 of `cloudcost/m2-milestone.md`. Read both `CLAUDE.md` first (cross-adapter). (a)
> Normalize stopped-compute `state` to schema-level `"stopped"`: shrink `STOPPED_STATES`, update
> `fetch_do.py` + its fixtures, confirm `fetch_aws.py` emits it, update the 3 pinning tests. (a′)
> Enumerate the canonical `type` vocabulary (§Canonical `type` vocabulary) in
> `cloudcost/milestone.md` §Normalized schemas (amendment-to-complete); rename `fetch_do.py`'s
> `droplet`→`compute_instance`, `reserved_ip`→`static_ip` + regen its fixtures; re-key the two
> DO-specific rules onto canonical (rename `rule_stopped_droplet_…`→`…_compute_…`); confirm
> compose/render key on no `type` value. (b) `{provider}_` filename prefix. (c) Add RDS orphan rules
> reusing existing shapes (stopped RDS + storage; aged manual RDS snapshot **by widening
> `rule_aged_snapshot` to both snapshot types, not a second rule**), and give `fired()` an optional
> saving that `score()` honours so the saving = the orphan's own estimate **plus** each attached
> separately-inventoried storage resource (stopped AWS own is 0.0, stopped DO own is full price, RDS
> storage is in its own estimate — so "own + attached" is provider-correct without the rule knowing
> the provider). Mutation-test DO 29 / AWS-EC2 16 / AWS-RDS 23. (d) Leave `compose_report_data.py`
> / `render_report.py` **unchanged** and the cross-provider merge code **dormant** (BL-070 retires
> it) — if AWS forces a change, STOP and report a contract-leak finding. Mutation-test the `state`
> and `type` normalizations and the non-zero stopped-orphan saving. Done-check per §t2.

### t3 — AWS solo run: orchestrator + sprint + end-to-end + matrix regen (core done-when)

**Scope.** Generalize `agents/cloudcost_orchestrator.exs` to select the adapter + output filenames
by `CLOUDCOST_PROVIDER` (default preserves DO behavior; `aws` runs the AWS pipeline), running the
**linear per-provider** pipeline `fetch_{provider} → detect_orphans → compose_report_data →
render_report` — one provider, one report, one run (maps to Rig). `:full` context;
`tools:["run_command"]`; no `spawn_agent`; no cross-provider anything. Add/extend the hermetic
`cloudcost` case in `aetheris/scripts/sprint.sh`: clear prior gitignored output before asserting,
and **launch the orchestrator through the D2 hermetic prefix** (`env -u AWS_ACCESS_KEY_ID -u
AWS_SECRET_ACCESS_KEY -u AWS_PROFILE AWS_SHARED_CREDENTIALS_FILE=/dev/null`) so the sprint proves
the launch hygiene, not just the pipeline. Document the canonical invocation in the cloudcost
runbook. Regenerate `agents/capability_matrix.exs`. End-to-end on the real AWS bill (record mode):
the AWS report is produced with **≥1 AWS orphan** + evidence, reviewable without the console; AWS's
MoM is against its own prior snapshot (first run → m1-tested "no prior month" path). **Do not run
the real-bill step on the first of a month** (CE returns the period with no groups → an honest but
empty $0.00 cost section; DO finds no invoice — both degrade correctly to nothing useful; t1 notes).
**Adjudicate A4** (below) — surface the swept-region set in the report.

**Contract refs.** agent-creation-guide (orchestrator, run_command format, report-failures-and-stop);
m1 §t5; the `sprint.sh` pattern; `capability_matrix.exs` + Rig `CapabilityMatrix` source; decision C
(the launch prefix); A4 (swept-regions render).

**Touches.** `cloudcost/agents/cloudcost_orchestrator.exs`; `aetheris/scripts/sprint.sh`;
`cloudcost/runbook.md` (canonical hermetic invocation + the first-of-month caveat);
`cloudcost/docs/m2-t3-implementation-notes.md`; `docs/capability-matrix.md` (regen — manifest
staleness is an exempt WARN); possibly `compose_report_data.py`/`render_report.py`/`templates/` **if**
A4 is resolved as an enumerated adjustment. DO-tripwire backlog row (**BL-069**).

**Do-not-generate.** `spawn_agent`/`wait_for_all`; any multi-provider / cross-provider run;
`write_file`/`read_file` in orchestrator tools; scheduling; any write op; resource-level cost; a
non-hermetic sprint; a sprint that launches the AWS run **without** the default-chain prefix; reading
the t4 optimization file; a compose/render change for A4 that is *not* a deliberate enumerated
adjustment (i.e. don't have compose key on `provider_extra` generically).

**Done-check.**
- `mix run --eval 'Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")'`
  evaluates clean.
- `CLOUDCOST_PROVIDER=aws ./scripts/sprint.sh cloudcost` runs the AWS pipeline (through the hermetic
  launch prefix) and finds the report; hermetic output reset. (DO path still runs under its own
  provider value — regression check.)
- Real AWS bill: report + **≥1 orphan** with evidence (the planted Elastic IP), reviewable without
  the console.
- `CLOUDCOST_AWS_*` appears nowhere in the trajectory.
- `capability_matrix.exs` re-run; matrix lists cloudcost's AWS adapter; Rig source confirmed + noted.
- The report states the swept-region set (A4 resolution).

**Claude-code prompt.**
> Build the AWS solo run per §t3 of `cloudcost/m2-milestone.md`. Read both `CLAUDE.md` first
> (cross-repo). Generalize `cloudcost_orchestrator.exs` to pick the adapter + output names by
> `CLOUDCOST_PROVIDER` (default = DO behavior; `aws` = AWS pipeline), running the linear per-provider
> chain `fetch_{provider} → detect_orphans → compose_report_data → render_report` — one provider,
> one report, one run; `:full`; `tools:["run_command"]`; no spawn_agent; no cross-provider logic; do
> not read the t4 file. Add a hermetic `cloudcost` sprint case for the AWS provider that launches the
> orchestrator through the D2 prefix and resets prior output; keep the DO path green; document the
> canonical invocation + the first-of-month caveat in `cloudcost/runbook.md`. Resolve A4 — surface the
> swept-region set in the report as a deliberate enumerated compose/render adjustment (a named
> region-coverage field lifted into report_data, rendered generically), NOT by keying on
> `provider_extra`; if that forces any other compose/render change, STOP and report it as a
> contract-leak finding. Re-run `capability_matrix.exs`; confirm + note the Rig source. Verify
> credentials never reach the trajectory. Done-check per §t3 incl. the real-bill end-to-end (≥1 AWS
> orphan).

### t4 — Optimization-signals spike (S3 / ECR / Secrets) — exploratory, non-gating

**Scope.** A **separate** `scripts/detect_optimization_signals.py` (+ a render addition), read-only,
best-effort. Signals: **S3** — no lifecycle policy, incomplete multipart uploads, empty buckets,
(size via CloudWatch `BucketSizeBytes`); **ECR** — repos with no lifecycle policy, untagged/old image
accumulation; **Secrets Manager** — old/absent `LastAccessedDate`. Emits
`optimization_signals_aws_{period}.json` (the loose structure above — *not* the frozen contract).
`render_report.py` gains an **additive, isolated** "Optimization signals (exploratory)" section that
renders only when the file is present (absent → the report is byte-identical to the core). Each
signal shows `evidence[]` + a `note`; a `monthly_cost_estimate` only where honestly available (secret
charge; CloudWatch-derived S3 size × rate), else omitted — never invented. Launched under the same
D2 hermetic prefix as t3. t4's real-bill read seeds the scope of the engine-backed optimization
milestone (**BL-072**). *This account's live bill is entirely non-orphan-shaped (Secrets Manager /
S3 / ECR / Tax), so t4 is where the real value is here.*

**Contract refs.** boto3 S3/ECR/Secrets Manager/CloudWatch; the render-data shape from t3 (additive
section only); decision G (must not touch the frozen schema or `detect_orphans`); decision C (launch
prefix).

**Touches.** `cloudcost/scripts/detect_optimization_signals.py`;
`cloudcost/scripts/render_report.py` (**additive** optional section only); `cloudcost/templates/`;
`cloudcost/tests/test_optimization_signals.py`; `cloudcost/tests/test_render_report.py` (absent-file
= unchanged core render); `cloudcost/tests/fixtures/optimization_*.json`; orchestrator gains one
optional step + `CLOUDCOST_OPTIMIZATION=1` gate. IAM spike actions (§Prereqs 1).

**Do-not-generate.** Any write/non-read call; forcing S3/ECR/Secrets into `detect_orphans.py` or the
frozen schema; confidence scores dressed up as orphan candidates; a fabricated dollar figure; a
render change that alters the core report when the optimization file is absent (isolation invariant);
listing every S3 object where a CloudWatch metric answers the size question.

**Done-check.**
- `python3 scripts/detect_optimization_signals.py --output-dir /tmp/cc --period <YYYY-MM>` (creds set)
  writes the signals file; schema-shaped; pytest green offline against recorded fixtures.
- **Isolation invariant (mutation posture):** file absent → `render_report.py` output identical to
  the core report (asserted); file present → the exploratory section renders with `evidence[]`.
- Real bill: the section renders a first read; a thin/empty result is a **pass** (labeled
  exploratory), not a failure.
- Credentials in neither stdout nor stderr.

**Claude-code prompt.**
> Build the exploratory optimization-signals spike per §t4 of `cloudcost/m2-milestone.md`. A
> **separate** `scripts/detect_optimization_signals.py` (read-only) for S3 (no-lifecycle /
> incomplete-multipart / empty-bucket / size-via-CloudWatch), ECR (no-lifecycle / old-image), and
> Secrets Manager (unused via LastAccessedDate) → a separate `optimization_signals_aws_{period}.json`
> (loose structure, NOT the frozen schema, NOT confidence-scored orphan candidates). Add an
> **additive, isolated** "Optimization signals (exploratory)" section to `render_report.py` that
> renders only when the file is present — with it absent, the core report must be byte-identical.
> Gate the orchestrator step behind `CLOUDCOST_OPTIMIZATION=1`; launch under the D2 hermetic prefix.
> Do NOT touch `detect_orphans.py` or the frozen schema, invent dollar figures, or make any write
> call. pytest incl. the isolation invariant. A thin real-bill result is a pass. Done-check per §t4.

---

## Referenced Rig ticket (separate — not cloudcost Python work) — **BL-073**

**Surface each run's report artifact against its run in Rig.** Runs already appear in Harness →
Runs; this ticket records the generated report's path on the run and renders/links it in the run
view, so a human opens a run and sees its cost report. Pairs naturally with per-provider solo runs
(decision H) — each run has exactly one report. Belongs to the Rig backlog (harness/Rig repo), is
referenced by this milestone, and is **not** part of t1–t4. Scoping note: the report is a local file
today (m1 delivery), so this needs a stable, Rig-readable location (or the run recording the artifact
path). **Filed as BL-073** in `docs/backlog-2026-06.md`; scoped generically over any report-producing
use case (docbuilder too), not cloudcost-specifically.

## Sequencing

t1 (**done**) → t2 → t3 is the **contract-proof core**, linear; t3 closes the core done-when and *is
the clean mechanical result* (compose/render unchanged beyond §t2, single-provider). **t4 after t3**
(offline parts may build in parallel; its render change lands after t3 so the isolation invariant is
measured against a settled core). t4 is **non-gating**.

## Open items forwarded (post-m2)

- **`swept_regions` render home (t3 decision, A4).** Decision D says the report states the swept
  set; t1 emits it in the stdout summary and `provider_extra.swept_regions` (opaque — downstream
  must not key on it generically), and §t2 (d) holds compose/render unchanged. Recommended t3
  resolution: surface it as a **deliberate, enumerated compose/render adjustment** — a named
  region-coverage field `compose` lifts from the snapshot into report_data, rendered generically —
  **not** a leak and **not** by weakening Decision D. Adjudicate at t3.
- **Cross-provider consolidation** as an optional aggregator read-layer over
  `history/{provider}/{period}/` snapshots (decision H) — if/when a FinOps roll-up is wanted.
  (Not filed as a row — no live trigger; revisit when wanted.)
- **Full S3/ECR/rightsizing optimization** via **Cost Optimization Hub / Compute Optimizer**
  (decision F) — t4's real-bill read seeds its scope. **BL-072.**
- **Rig report-surfacing** ticket (above). **BL-073.**
- **Resource-level AWS cost** + rate spot-check — deferred (B). **BL-071.**
- **Seam sweep** — enumerate every provider-vocabulary / provider-assumption seam in shared
  machinery. **BL-074.**
- **Recency-modifier window bound + `last_activity_at` guard** — at the first adapter populating
  `last_activity_at` (unchanged from m1; latent).
- **P2 queue; P3 gated cleanup; email/Drive; scheduling; DuckDB; the `reported` governance
  section** — unchanged from m1.

## Backlog rows filed with this milestone (`docs/backlog-2026-06.md`)

- **BL-069 — DO ≥1-orphan tripwire (armed).** Reserved IP 168.144.13.150 (NYC1) confirmed deleted
  2026-07-30 — the DO pipeline's ≥1-orphan *assertion* (a known-positive pipeline test) depended on
  it. Next DO run finds 0 DO orphans → the test fails or greens vacuously off stale output. Re-plant
  or re-point to a fixture before the next DO run. **Verified fired** at t1 (live DO: 18 resources,
  0 orphans). Independent of AWS.
- **BL-070 — Retire the dormant cross-provider merge code in `compose_report_data.py`** — N-merge,
  `providers_without_prior_snapshot` caveat, multi-currency, cross-currency 4-site paths are
  unreachable under per-provider reporting (H). Dormant in m2 to keep `compose` unchanged; delete in
  a dedicated cleanup.
- **BL-071 — Resource-level cost path** + the resource-rate spot-check — forwarded (B service-level).
- **BL-072 — Cost Optimization Hub optimization milestone** — forwarded (t4's read seeds its scope).
- **BL-073 — Surface each run's report artifact against its run in Rig** — the §Referenced Rig
  ticket above; Rig-repo concern, scoped generically.
- **BL-074 — Seam sweep: enumerate every provider-vocabulary / provider-assumption seam in shared
  machinery.** m1 called `STOPPED_STATES` "the one seam"; t1 found it is at least **three** —
  `state`, `type` (both resolved at t2 a/a′), and the **flat-billed-regardless-of-state cost
  assumption** (adapter half at t1, saving half at t2 c). The claim came from observation, not
  enumeration (the **Adjacent-case** rule: enumerate every site of the class before fixing the
  first). Sweep `detect_orphans.py` + the shared helpers for *any other* value/threshold/spelling a
  provider could differ on — the rule-catalog **age thresholds** and the **`keep=true` tag spelling**
  are the named next candidates — and correct m1's "the one seam" text where it appears. §7 promotion
  candidate at m2 close (Adjacent-case / enumerate-the-class). *(ID confirmed next-free against
  `docs/backlog-2026-06.md` at `3bc970b`: BL-073 was the highest.)*
