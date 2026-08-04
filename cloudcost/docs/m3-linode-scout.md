# m3-cloudcost — Linode scout (read-only)

Scouting input for the m3 milestone issue-doc: Linode as the third cloud-cost adapter.
**This file is not a milestone doc and decides nothing.** It records repo state and Linode
APIv4 spec state, each with the citation it was read from.

Rules applied: cited-means-read (every repo claim carries `file:line`; every API claim carries
the JSON pointer); absent is unknown, not zero (§Unknowns); complete output.

**Retrieval record for Part B.** Source of record fetched once to a scratch path and read
locally; the rendered docs site was not scraped.

```
$ curl -sS -D headers.txt -o linode-openapi.json \
    https://raw.githubusercontent.com/linode/linode-api-docs/refs/heads/development/openapi.json

HTTP/2 200
cache-control: max-age=300
content-security-policy: default-src 'none'; style-src 'unsafe-inline'; sandbox
content-type: text/plain; charset=utf-8
etag: "290888161afda3d3566f755d664856fb937fbafbf817838587bb2be6e77ef6cd"
strict-transport-security: max-age=31536000
x-content-type-options: nosniff
x-frame-options: deny
x-xss-protection: 1; mode=block
x-github-request-id: 640C:1D349E:7D8B:11118:6A71F4D9
x-github-edge-region: centralindia
accept-ranges: bytes
date: Tue, 04 Aug 2026 14:19:07 GMT
via: 1.1 varnish
x-served-by: cache-maa10230-MAA
x-cache: MISS
x-cache-hits: 0
x-timer: S1785853147.003802,VS0,VE776
vary: Authorization,Accept-Encoding
access-control-allow-origin: *
cross-origin-resource-policy: cross-origin
x-fastly-request-id: 812c9b821df44d8cdeb77cee26ea419ad9347214
expires: Tue, 04 Aug 2026 14:24:07 GMT
source-age: 0
content-length: 7911272
```

- Retrieved **2026-08-04 14:19:07 UTC**; `date -u` at retrieval: `Tuesday 04 August 2026 02:19:08 PM UTC`.
- ETag `"290888161afda3d3566f755d664856fb937fbafbf817838587bb2be6e77ef6cd"` (no `last-modified` header served).
- `openapi: 3.0.1`, `info.version: 4.215.0`, 7 911 272 bytes, 308 paths, 77 named schemas.
- `development` is a moving branch: quote the ETag above when re-reading.

Repo state read at `aetheris-agents main@dc8c077` (working tree clean at read time).

---

# Part A — repo state

## A1. `cloudcost/scripts/_normalized.py` — the closed set (140 lines total)

Everything the module exports, with line numbers:

| Export | Line | Value / signature |
|---|---|---|
| `TYPE_COMPUTE_INSTANCE` | 39 | `"compute_instance"` |
| `TYPE_VOLUME` | 40 | `"volume"` |
| `TYPE_STATIC_IP` | 41 | `"static_ip"` |
| `TYPE_SNAPSHOT` | 42 | `"snapshot"` |
| `TYPE_LOAD_BALANCER` | 43 | `"load_balancer"` |
| `TYPE_DATABASE` | 44 | `"database"` |
| `TYPE_DATABASE_SNAPSHOT` | 45 | `"database_snapshot"` |
| `CANONICAL_TYPES` | 48–58 | `frozenset` of exactly the seven above |
| `STATE_STOPPED` | 62 | `"stopped"` |
| `parse_timestamp(value)` | 65–78 | ISO-8601 → aware UTC `datetime`, or `None`; `Z`/`z` → `+00:00`; naive → UTC |
| `iso(moment)` | 81–82 | `strftime("%Y-%m-%dT%H:%M:%SZ")` |
| `day(moment)` | 85–86 | `strftime("%Y-%m-%d")` |
| `money(value)` | 89–94 | `round(float(value), 2)`; uncoercible → `0.0`, never raises |
| `provider_slug(value)` | 97–107 | `re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")` or `"unknown"` |
| `tags_of(resource)` | 110–112 | `resource["tags"]` filtered to `str` entries; non-list → `[]` |
| `usable_resources(inventory)` | 115–132 | `(usable, skipped)`; skips non-dict, missing `resource_id`, missing `type` |
| `tag_coverage(resources)` | 135–140 | fraction with ≥1 tag, 4dp; empty list → `0.0` |

Module docstring (`_normalized.py:11–19`) states the contract a third adapter is bound by: the
canonical `type`/`state` values "are the definition of the schema seam, so by construction they
have exactly one home — this module — which every adapter … imports from". `_normalized.py:35–37`
names the anti-pattern explicitly: "an adapter importing from a *sibling adapter* is the
cross-import anti-pattern."

Note `_normalized.py:97–107`: `provider_slug` has a deliberate duplicate — `compose_report_data.slug`
(`compose_report_data.py:96–100`, byte-identical logic), kept un-converged to preserve m2 §t2 (d)'s
"compose ran unchanged" negative proof. **BL-070** owns the convergence.

## A2. `cloudcost/scripts/detect_orphans.py` — rules, keys, provider-differing constants

### Rule functions and the normalized fields each keys on

| Rule fn | Line | Keys on |
|---|---|---|
| `rule_unattached_volume` | 165–184 | `type == TYPE_VOLUME`, `attached_to is None`, `created_at` age > 14d |
| `rule_unassociated_static_ip` | 187–199 | `type == TYPE_STATIC_IP`, `attached_to is None`; **no age threshold** (`created_at` used for evidence only) |
| `rule_aged_snapshot` | 202–224 | `type in SNAPSHOT_TYPES`, `created_at` age > `snapshot_age_days`; `attached_to is None` adds evidence only |
| `rule_idle_load_balancer` | 227–245 | `type == TYPE_LOAD_BALANCER`, `attached_to is None` (a `"tag:<name>"` attachment excludes) |
| `rule_stopped_compute_with_attached_storage` | 248–303 | `type == TYPE_COMPUTE_INSTANCE`, `state in STOPPED_STATES`, `created_at` age > 30d, ≥1 volume whose `attached_to == resource_id` |
| `rule_stopped_database_with_storage` | 306–347 | `type == TYPE_DATABASE`, `state in STOPPED_STATES`, `attached_to is None`, `monthly_cost_estimate > 0`, `created_at` age > 30d |
| `RULES` tuple | 351–358 | evaluation order = the six above |

Modifiers: `modifier_recent_activity` (364–383, keys on `last_activity_at` only),
`modifier_ephemeral_name` (386–402, keys on `name`); `MODIFIERS` at 405; `clamp` 408–409.
Governance-only rule `untagged_in_tagged_account` is inline in `detect()` at 500–519 —
structurally not a candidate (no `confidence`, no `monthly_saving_estimate`; 536–544).

The full normalized field set the engine reads: `state`, `type`, `attached_to`, `created_at`,
`last_activity_at`, `tags`, `name`, `monthly_cost_estimate`, `resource_id`, `region`, `raw_ref`,
`size` (`identity()` 415–424; `size` read for evidence text at 289–292).

### Module-level constants a provider could legitimately differ on

| Constant | Line | Value |
|---|---|---|
| `CONFIDENCE_UNATTACHED_VOLUME` | 57 | `0.9` |
| `CONFIDENCE_UNASSOCIATED_STATIC_IP` | 58 | `0.95` |
| `CONFIDENCE_AGED_SNAPSHOT` | 59 | `0.7` |
| `CONFIDENCE_IDLE_LOAD_BALANCER` | 60 | `0.85` |
| `CONFIDENCE_STOPPED_COMPUTE_WITH_STORAGE` | 61 | `0.6` |
| `CONFIDENCE_STOPPED_DATABASE_WITH_STORAGE` | 62 | `0.6` |
| `UNATTACHED_VOLUME_MIN_AGE_DAYS` | 65 | `14` |
| `STOPPED_COMPUTE_MIN_AGE_DAYS` | 68 | `30` (one threshold for compute **and** databases, deliberately — 66–67) |
| `DEFAULT_SNAPSHOT_AGE_DAYS` | 69 | `30`, overridable via `--snapshot-age-days` |
| `MODIFIER_RECENT_ACTIVITY` | 72 | `-0.2` |
| `MODIFIER_EPHEMERAL_NAME` | 73 | `+0.1` |
| `RECENT_ACTIVITY_WINDOW_DAYS` | 78 | `14` |
| `EPHEMERAL_NAME_PATTERN` | 81 | `re.compile(r"^(tmp-|ci-|test-)")`, matched **case-sensitively** |
| `KEEP_TAG` | 84 | `"keep=true"`; matched `tag.strip().lower() == KEEP_TAG` (112) |
| `TAGGED_ACCOUNT_COVERAGE_THRESHOLD` | 88 | `0.5`, strict `>` (500) |
| `STOPPED_STATES` | 93 | `frozenset({STATE_STOPPED})` — i.e. `{"stopped"}` and nothing else |
| `SNAPSHOT_TYPES` | 99 | `frozenset({TYPE_SNAPSHOT, TYPE_DATABASE_SNAPSHOT})` |

### The exact saving expression after m2 t2 (c)

`detect_orphans.py:284–303`, verbatim:

```python
        storage_total = 0.0
        for volume in sorted(attached, key=lambda v: str(v.get("resource_id"))):
            cost = money(volume.get("monthly_cost_estimate"))
            storage_total += cost
            evidence.append(
                f"attached storage {volume.get('resource_id')} "
                f"({volume.get('name')}, {volume.get('size')}) — "
                f"${cost:.2f}/mo"
            )
        saving = round(own + storage_total, 2)
```

where `own = money(resource.get("monthly_cost_estimate"))` (274). So the saving is
**instance's own estimate + the sum of separately-inventoried attached volumes' estimates**.
The docstring at 256–261 states why adding rather than replacing keeps it provider-agnostic:
each adapter has already encoded its own cost model in `monthly_cost_estimate` (DO: own is the
full droplet price; AWS: own is `0.0` and EBS carries the charge). The sibling
`rule_stopped_database_with_storage` deliberately does **not** sum (312–314) — storage a provider
folds into the instance's own estimate is already counted once.

## A3. `fetch_aws.py` / `fetch_do.py` — the skeleton a third adapter copies

### Shape, side by side

| Aspect | `fetch_do.py` (601 lines) | `fetch_aws.py` (1135 lines) |
|---|---|---|
| CLI flags | `--output-dir` (528, default `"output"`), `--period` (529), `--api-base` (530), `--timeout` (531), `--max-retries` (532), `--retry-base-delay` (533) | `--output-dir` (1051), `--period` (1052), `--endpoint-url` (1053–1057), `--timeout` (1058), `--max-attempts` (1059) |
| `--output`/`--output-dir` contract | writes 2 files under `--output-dir`, prints a JSON summary carrying their paths (580–596) | same (1106–1130) |
| Credential env | `TOKEN_ENV = "CLOUDCOST_DO_TOKEN"` (49) | `CLOUDCOST_AWS_ACCESS_KEY_ID` / `_SECRET_ACCESS_KEY` / `_SESSION_TOKEN` / `_REGION` (53–56), plus `CLOUDCOST_AWS_REGIONS` (58) |
| Shadowing set | `SHADOWING_ENV = ("DO_TOKEN", "DIGITALOCEAN_ACCESS_TOKEN")` (53) | `("AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","AWS_SESSION_TOKEN","AWS_PROFILE")` (63–68) |
| Shadowing warning | `warn_shadowing_env` (213–225) — names, never values; stream resolved at call time | `warn_shadowing_env` (252–264), identical shape |
| Credential load | `load_token` (200–210) — raises `DOAuthError` naming the ignored fallbacks | `load_credentials` (227–249) — raises `AWSAuthError`, same wording pattern |
| Redaction | `DOClient._redact` (111–113) + token-free `__repr__` (115–116) | `AWSClients.redact` (324–329) + token-free `__repr__` (331–332) |
| Pagination | `DOClient.paginate` (180–194) follows `links.pages.next`, re-rooted onto `api_base` by `_same_origin` (134–143); `MAX_PAGES=100`, `PER_PAGE=200` (59–60) | `paginate` (374–385) uses botocore paginators, falling back to a single call when `can_paginate` is false |
| Retry | `RETRY_STATUSES = {429,500,502,503,504}` (58); `_retry_delay` honours `retry-after` then `ratelimit-reset`, else exponential (118–132) | delegated to botocore `Config(retries={"max_attempts":…, "mode":"standard"})` (283–288) |
| Error-code handling | 401/403 → fatal `DOAuthError` (162–166); other non-OK → `DOAPIError` with redacted 200-char body (171–173) | `AUTH_ERROR_CODES` (82–93) fatal; `REGION_DISABLED_CODES = {"OptInRequired"}` (103) warns; everything else → `errors[]` and a partial run. 98–102 records why `UnauthorizedOperation`/`AccessDenied` are deliberately **not** treated as disabled-region |
| `write_json` | 518–523 — mkdir, write `.tmp`, atomic `replace` | 1041–1046 — byte-identical |
| Degrade posture | per-source try/except → `errors[]` (492–512); exit `0` clean / `1` partial (597) | per-source `guard()` closure (885–905); exit `0`/`1` (1131) |

### How each maps its own vocabulary onto canonical values

**State.** DO: `normalize_droplet` (332–352) — `"state": STATE_STOPPED if status == "off" else status`
(345). Other DO statuses (`new`, `active`, `archive`) pass through unmapped, deliberately (334–336).
AWS: `normalize_instance` (489–509) — `STATE_STOPPED if state == "stopped" else state or None` (500),
mapped *through the constant even though EC2's own spelling already matches* (498–499);
`normalize_db_instance` (659–686) does the same at 679. Derived (not read) states: DO volume
`"attached"/"available"` (366, because the DO volumes endpoint carries no status), AWS Elastic IP
`"associated"/"unassociated"` (555), AWS classic ELB constant `"active"` (649).

**Type.** Every normalizer hard-codes one imported `TYPE_*` constant; neither adapter defines its own.
DO: droplet→`TYPE_COMPUTE_INSTANCE` (341), volume→`TYPE_VOLUME` (360), reserved IP→`TYPE_STATIC_IP` (382),
snapshot→`TYPE_SNAPSHOT` (403), LB→`TYPE_LOAD_BALANCER` (437). AWS adds RDS→`TYPE_DATABASE` (675) and
manual RDS snapshot→`TYPE_DATABASE_SNAPSHOT` (700).

**`monthly_cost_estimate`.**

- DO (`fetch_do.py:62–68`): droplets read the API's real `size.price_monthly` (349); everything else
  is a module constant × size — `VOLUME_GIB_MONTHLY = 0.10` (65, "confirmed against a real invoice
  line"), `SNAPSHOT_GIB_MONTHLY = 0.06` (66), `RESERVED_IP_UNASSIGNED_MONTHLY = 4.38` (67, charged
  only while unassigned — 390), `LOAD_BALANCER_NODE_MONTHLY` × `size_unit` (68, 444).
- AWS (`fetch_aws.py:114–210`): two explicitly separated tables. The **load-bearing closed set**
  (`EBS_GIB_MONTHLY` 130–139, `EBS_SNAPSHOT_GIB_MONTHLY` 142, `ELASTIC_IP_UNASSOCIATED_MONTHLY` 145,
  `LOAD_BALANCER_MONTHLY` 148–154, `RDS_STORAGE_GIB_MONTHLY` 157–165, `RDS_SNAPSHOT_GIB_MONTHLY` 168)
  — every orphan saving derives from these. And the **not load-bearing** `COMPUTE_MONTHLY` table
  (176–210), reached only via `instance_compute_estimate` (459–483), which returns `0.0` for a
  *stopped* instance (D5, 471–472) and `0.0` + a named `warnings[]` entry for an unknown instance
  type (474–482) — never an invented figure. The AWS Pricing API is deliberately not used (117–120).

### `rate_basis` — the prompt's premise does not hold

`fetch_aws.py` never emits `rate_basis`. Repo-wide grep places it only in
`detect_optimization_signals.py` (the m2 t4 exploratory spike — 43, 248, 261, 270, 345), its tests
(`test_optimization_signals.py:140, 277–299, 346`), the template (`templates/report.html.j2:559–560`),
and prose (`cloudcost/m2-milestone.md:715–717`, `cloudcost/docs/m2-t4-implementation-notes.md:56`).
The **§Normalized inventory resource carries no `rate_basis` field at all**, on either adapter.
See §Contradictions C1.

### What a new CLI would be tempted to import from `fetch_aws`, and must not

Neither adapter imports the other: `fetch_do.py:37–44` and `fetch_aws.py:41–50` both import from
`_normalized` and nothing else. The following are **duplicated on purpose** and are the live
temptation for a third CLI — each already exists twice, so a Linode adapter importing either copy
would create the first CLI-to-CLI import in the use case:

| Symbol | In `fetch_do.py` | In `fetch_aws.py` | Note |
|---|---|---|---|
| `money` | 228–232 | 391–396 | **Not identical.** DO's raises on a bad value; AWS's swallows to `0.0`. Both differ from `_normalized.money` (89–94), which every downstream stage uses |
| `current_period` | 235–236 | 399–400 | identical |
| `iso_now` | 239–240 | 403–404 | identical |
| `write_json` | 518–523 | 1041–1046 | identical |
| `warn_shadowing_env` | 213–225 | 252–264 | same shape, different constant set |
| `tags_of` | 243–249 | 421–439 | different semantics: DO reconciles `tags`/`tag`; AWS flattens `[{Key,Value}]` → `"k=v"` |
| `paginate` | 180–194 (method) | 374–385 (function) | transport-specific |

Also tempting and equally off-limits: `AUTH_ERROR_CODES` (82–93), `REGION_DISABLED_CODES` (103),
`error_code` (335–336), `raise_for` (339–346) and `resolve_source` (567–587). `resolve_source` is
the interesting one — its "only cross-reference when the sweep resolved" discipline (573–581) is a
*pattern* a Linode snapshot/backup normalizer should reproduce, not a function to import.

## A4. Exact output filenames

**Written today:**

| Writer | Filename pattern | Line | Observed on disk |
|---|---|---|---|
| `fetch_do.py` | `{output_dir}/do_costs_{period}.json` | 582 | `cloudcost/output/digitalocean/do_costs_2026-08.json` |
| `fetch_do.py` | `{output_dir}/do_inventory_{period}.json` | 583 | `cloudcost/output/digitalocean/do_inventory_2026-08.json` |
| `fetch_aws.py` | `{output_dir}/aws_costs_{period}.json` | 1108 | `cloudcost/output/aws/aws_costs_2026-08.json` |
| `fetch_aws.py` | `{output_dir}/aws_inventory_{period}.json` | 1110 | `cloudcost/output/aws/aws_inventory_2026-08.json` |
| `detect_orphans.py` | `{output_dir}/{provider_slug}_orphan_candidates_{period}.json` | 628–631 | `digitalocean_orphan_candidates_2026-08.json`, `aws_orphan_candidates_2026-08.json` |
| `compose_report_data.py` | `{output_dir}/report_data_{period}.json` | 875 | `cloudcost/output/aws/report_data_2026-08.json` |
| `compose_report_data.py` | `{history_dir}/{period}/{slug(provider)}_costs_{period}.json` | 749 | `cloudcost/history/digitalocean/2026-08/digitalocean_costs_2026-08.json` |
| `render_report.py` | `{output_dir}/cloudcost_report_{period}.html` | 378 | `cloudcost/output/aws/cloudcost_report_2026-08.html` |

**The provider-prefix convention is not one convention, it is two.** The adapter prefix is a
hand-written literal in the adapter (`do_`, `aws_`) — it is *not* derived from the `provider` field.
The orphans prefix and the history prefix are `provider_slug(document["provider"])`, i.e.
`digitalocean` and `aws`. Hence `do_costs_2026-08.json` sits beside
`digitalocean_orphan_candidates_2026-08.json` in the same directory. For Linode the two happen to
coincide (`provider_slug("linode") == "linode"`), so a `linode_costs_…` / `linode_inventory_…`
naming is both conventions at once — but the inconsistency is real and the milestone should note it
rather than rediscover it.

**What `compose_report_data.py` expects: no filenames at all.** It classifies by *shape*, not name —
`classify()` (`compose_report_data.py:690–700`):

```python
def classify(document: dict):
    """Which normalized artifact a parsed document is, by shape rather than by filename —
    so a directory holding several providers' files groups correctly whatever they are
    called."""
    if isinstance(document.get("line_items"), list):
        return "cost"
    if isinstance(document.get("candidates"), list):
        return "orphans"
    if isinstance(document.get("resources"), list):
        return "inventory"
    return None
```

`--input-dir` globs `*.json` and groups by the documents' own `provider` field
(`discover_bundles`, 703–731); the orchestrator's actual call form passes explicit
`--cost/--inventory/--orphans` paths. `load_prior_snapshots` (754–770) likewise globs
`history/{prior_period}/*.json` and keeps whatever `classify()` calls a cost document. So a third
adapter can name its two files anything; what it may **not** do is emit a cost document without
`line_items` or an inventory without `resources`.

## A5. `cloudcost/agents/cloudcost_orchestrator.exs` (298 lines)

**Provider literal table** — `cloudcost_orchestrator.exs:42–49`, verbatim:

```elixir
provider = System.get_env("CLOUDCOST_PROVIDER") || "digitalocean"

{provider_name, provider_short, provider_slug, fetch_script} =
  case provider do
    "digitalocean" -> {"DigitalOcean", "DO", "digitalocean", "scripts/fetch_do.py"}
    "aws" -> {"AWS", "AWS", "aws", "scripts/fetch_aws.py"}
    other -> raise ~s(CLOUDCOST_PROVIDER must be "digitalocean" or "aws", got: #{inspect(other)})
  end
```

So each accepted value carries four fields: `provider_name` (prose, used in the system prompt and
the label), `provider_short` (STEP 1 prose), `provider_slug` (output/history directory names, run id),
`fetch_script` (STEP 1 argv). **The raise on an unknown provider is line 48.**

Two further raises, both fail-fast on selection rather than at runtime:

- 62–73 — `CLOUDCOST_PROVIDER=aws` with either `CLOUDCOST_AWS_ACCESS_KEY_ID` or
  `CLOUDCOST_AWS_SECRET_ACCESS_KEY` unset raises at eval time, names only (never values). 59–61
  records why there is deliberately no symmetric DO raise (DO is the default sink, and the offline
  `Code.eval_file/1` done-check must stay clean on a machine with no DO token).
- 145–150 — `CLOUDCOST_OPTIMIZATION=1` with `provider != "aws"` raises.

**Derived paths** — `output_dir = "output/#{provider_slug}"` (90), `history_dir = "history/#{provider_slug}"` (91).
75–89 records why: the report and report-data filenames carry no provider, so per-provider
directories are what stop two providers overwriting each other, and the per-provider history tree
scopes the MoM lookup (otherwise the first AWS run's headline would read "AWS this month minus
DigitalOcean last month").

**Run id** — line 277: `run_id: "cloudcost-orch-#{provider_slug}-#{Aetheris.ID.generate()}"`.
**Label after BL-083** — line 286: `label: "Cloudcost · #{provider_name}"`. 282–285 records that
Rig's `classifyRun` lowercases and does `startsWith`, so the `· <provider>` suffix still matches the
`cloudcost` prefix (`RunList.tsx:118-140`).

**Timeouts, step by step:**

| Step | Line | `timeout_ms` |
|---|---|---|
| STEP 1 — fetch | 199–201 | **declared**: `timeout_ms: #{fetch_timeout_ms}`, and `fetch_timeout_ms = 300_000` at 116 |
| STEP 2 — detect_orphans | 216–218 | **not declared** (exec-server default) |
| STEP 2b — optimization (conditional) | 158–161 | **not declared** |
| STEP 3 — compose | 223–236 (both arg forms) | **not declared** |
| STEP 4 — render | 238–240 | **not declared** |

93–116 is the BL-096 rationale block: the exec server's `unwrap_or(60_000)`
(`../aetheris/native/aetheris_exec_server/src/main.rs:472`, advertised in the tool schema at `:127`);
measured `fetch_aws` 63–67 s, `fetch_do` 8.2–9.3 s; one number for both providers because STEP 1 is
shared; and 110–111 states the convention directly — *"A third provider's adapter declares its own
step timeout by this same convention."* Lines 203–206 additionally instruct the model in prose not
to retry STEP 1 with a different timeout.

Also fixed at eval time: `mode: :record` (278), `provider: "anthropic"` (279),
`model: "claude-haiku-4-5-20251001"` (280) — literals rather than the `AETHERIS_*` env overrides the
sibling agents use, because `sprint.sh` sources `.env` (185–188); `max_steps: 20` (289);
`context_strategy: :full` (293); `tools: ["run_command"]` (294); `overlay_base_dir: nil` (288).

## A6. `cloudcost/tools.json` and the serde structs it deserializes into

**Current entries** (`cloudcost/tools.json`, 455 lines): `manifest_version "1"`, `use_case "cloudcost"`,
and seven scripts —

| `name` | `file` | args | `env` | `output` |
|---|---|---|---|---|
| `fetch_aws` | `scripts/fetch_aws.py` | 5 | 5 rows (`CLOUDCOST_AWS_ACCESS_KEY_ID`, `_SECRET_ACCESS_KEY`, `_SESSION_TOKEN`, `_REGION`, `_REGIONS`) | `json` |
| `fetch_do` | `scripts/fetch_do.py` | 6 | 1 row (`CLOUDCOST_DO_TOKEN`) | `json` |
| `detect_orphans` | `scripts/detect_orphans.py` | 4 | — | `json` |
| `detect_optimization_signals` | `scripts/detect_optimization_signals.py` | 9 | 5 rows (same AWS set) | `json` |
| `compose_report_data` | `scripts/compose_report_data.py` | 8 | — | `json` |
| `render_report` | `scripts/render_report.py` | 6 | — | `json` |
| `_normalized` | `scripts/_normalized.py` | 0 | — | `text` |

Masked flags as declared: `CLOUDCOST_DO_TOKEN` `masked: true` (151); `CLOUDCOST_AWS_SECRET_ACCESS_KEY`
and `CLOUDCOST_AWS_SESSION_TOKEN` `masked: true` (64, 71); `CLOUDCOST_AWS_ACCESS_KEY_ID`,
`_REGION`, `_REGIONS` `masked: false` (57, 78, 85).

**The structs** — `rig/src-tauri/src/commands/tools.rs:6–46`, verbatim:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvDep {
    pub key:         String,
    pub label:       String,
    pub group:       String,
    pub masked:      bool,
    pub placeholder: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestArg {
    pub name:        String,
    pub flag:        Option<String>,
    #[serde(rename = "type")]
    pub arg_type:    String,
    pub required:    bool,
    pub default:     Option<String>,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestScript {
    pub name:        String,
    pub file:        String,
    pub description: String,
    pub args:        Vec<ManifestArg>,
    pub output:      String,   // "json" | "text" | "files"
    pub example:     String,
    #[serde(default)]
    pub undeclared:  bool,
    #[serde(default)]
    pub env:         Vec<EnvDep>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolsManifest {
    pub manifest_version: String,
    pub use_case:         String,
    pub description:      String,
    pub scripts:          Vec<ManifestScript>,
}
```

So: the env array is `Vec<EnvDep>` and **a masked flag does exist** (`EnvDep.masked: bool`, line 11).
`env` and `undeclared` are the only `#[serde(default)]` fields on `ManifestScript` (34, 36); every
`EnvDep` field is mandatory, so one missing key drops the whole manifest.

## A7. `tests/test_tools_manifests.py` (261 lines)

Five tests, all offline:

1. `test_discovery_sweep_intact` (129–153) — asserts `SWEPT == ["api","boxy-pipeline","cloudcost","docbuilder","drive","eduloka","email","payslip","provenance"]`; asserts `len(_flat_cli_scripts("cloudcost")) == 6`; asserts `_flat_cli_scripts("api") == []` so that api's vacuity is visible rather than reading as coverage.
2. `test_manifest_parses` (156–201) — required top-level keys, `use_case` matches the directory, `manifest_version == "1"`, per-script required fields, `output ∈ {json,text,files}`, per-arg required fields, `type ∈ {string,file,directory,integer,float,boolean}`, `required` is a real bool, `default` is `str` or `None` (**a bare int fails serde**).
3. `test_declared_files_exist` (204–211).
4. `test_env_dep_fields_complete` (214–230) — all five `EnvDep` keys present, `masked` a real bool, the other four strings.
5. `test_no_undeclared_scripts` (250–260) — the offline proxy for Rig's amber badge.

**Current expected-fail set:**

- `NO_MANIFEST_YET = ("boxy-pipeline", "docbuilder", "provenance")` (107) → `pytest.mark.xfail(strict=True)` with reason naming **BL-089** (109–112, applied by `_param`, 115–122). Applies to `test_manifest_parses` and `test_no_undeclared_scripts`.
- `payslip` carries its own `xfail(strict=True)` on `test_no_undeclared_scripts` only (236–246), reason **BL-087** — `payslip/tools.json` omits `merge_employee_payslips.py`.

The suite's own stated limit (18–21): the schema is a *transcription* of the serde structs, not serde
itself — a manifest that passes here and still fails `serde_json::from_str` would be dropped silently
by `tools.rs:526`. That gap is **BL-092**'s subject.

## A8. `../aetheris/scripts/sprint.sh` — the cloudcost case

The case is `sprint.sh:2350–2581`, guarded by `if [[ "$TARGET" == "cloudcost" || "$TARGET" == "all" ]]`.
Its structure, in order:

1. `CC_PROVIDER="${CLOUDCOST_PROVIDER:-digitalocean}"` (2351); `CLOUDCOST_OUT="${CLOUDCOST_DIR}/output/${CC_PROVIDER}"` (2356).
2. **Prereq — python3** (2358–2359): `command -v python3 &>/dev/null || { fail "python3 not found"; exit 1; }`.
3. **`CC_HERMETIC` array** (2371–2373): `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE AWS_SHARED_CREDENTIALS_FILE=/dev/null CLOUDCOST_PROVIDER="$CC_PROVIDER"` — block-local and invoked inline, never exported (2366–2370).
4. **Prereq — the selected provider's credential** (2378–2397): a `case` on `$CC_PROVIDER` preflighting `CLOUDCOST_DO_TOKEN` for `digitalocean`, both `CLOUDCOST_AWS_*` for `aws`, and a `*)` arm that fails on any provider "this case knows" nothing about. Each arm `exit 1`s. **A third provider needs a fourth arm here or the run dies at 2394.**
5. **Stale-artifact guard** (2409–2411): `mkdir -p` then `find "$CLOUDCOST_OUT" -mindepth 1 -delete`, scoped to this provider's directory (2406–2408 explains why not the whole tree).
6. **Eval check** (2414–2421) through the same env the run will see.
7. **Fail-fast guards** (2431–2446): AWS-without-key must raise; unknown provider must raise. Both are inverted `if` blocks — a *successful* eval is the failure.
8. **Poison control + hermetic proof** (2453–2487): (i) without the prefix the probe must see the poison, (ii) through the prefix it must see nothing, (iii) for AWS, `CLOUDCOST_AWS_ACCESS_KEY_ID` must survive.
9. **The run** (2493–2500) — `"${CC_HERMETIC[@]}" mix aetheris --json run … > "$OUT_DIR/cloudcost/run.json" 2>&1`.
10. **Assertions** (2502–2572): report file exists; `report_data.providers == [$CC_PROVIDER]`; orphan count ≥1 (**BL-069, armed and known-red — 2529–2533**); and for AWS only, `region_coverage` ≥1 in the payload, `"regions swept"` present in the HTML, and no key id in `run.json` (gated at 2563 on the file having content and a `run_id`, so the grep can't pass vacuously).

**How `[OK]`/`[FAIL]` are emitted** — `sprint.sh:35` and `:37`:

```bash
ok()      { echo -e "\033[0;32m[OK]\033[0m    $*"; }
fail()    { echo -e "\033[0;31m[FAIL]\033[0m  $*"; }
```

`fail` **prints and returns; it sets no exit status** — this is BL-077. Some call sites pair it with
an explicit `exit 1` (2358, 2382, 2389, 2395, 2420, 2436, 2444, 2465, 2474, 2485); the assertion
block at 2508–2571 does **not**. So the sprint can print `[FAIL]` for the report, the provider check
and the orphan count and still exit 0. **Read the `[OK]`/`[FAIL]` lines, never `$?`.**

## A9. The capability-matrix regen path

- **Sprint case:** `capability_matrix` (`sprint.sh:1226–1283`), also run under `TARGET=all`.
- **Section agents:** nine `run_agent` calls (1231–1268), one per use case, each writing
  `$OUT_DIR/capability_matrix/<uc>.json` as its run log and — the actual artifact — a section file.
  The cloudcost one is `sprint.sh:1259–1261` → `../aetheris-agents/agents/capability_matrix_cloudcost.exs`,
  which writes `docs/.sections/cloudcost.md` (`capability_matrix_cloudcost.exs:4`, and the literal
  `path:` at `:55`). A failed section agent only `warn`s (1261).
- **Assembler:** `python3 ../aetheris-agents/scripts/assemble_matrix.py` (1276). Deterministic —
  concatenation plus a derived Overlap Report and Summary counted from the sections' own tables;
  no LLM, because the assembler agent's arithmetic was wrong every regen (**BL-067**, 1270–1274).
- **`docs/.sections/`** — `SECTIONS_DIR` at `assemble_matrix.py:48`. **Gitignored**
  (`.gitignore:10`; `git check-ignore -v docs/.sections/cloudcost.md` → `.gitignore:10:docs/.sections/`;
  `git ls-files docs/.sections/` → only `.gitkeep`). Currently on disk: all nine files
  (`api_gateway.md`, `api_tenant.md`, `cloudcost.md`, `docbuilder.md`, `drive.md`, `eduloka.md`,
  `email.md`, `payslip.md`, `provenance.md`).
- **`docs/capability-matrix-overrides.json`** — `OVERRIDES_JSON` at `assemble_matrix.py:50`;
  committed, and the durable home for curated prose the section agents would otherwise reword away
  (**BL-068**, docstring 21–25). Overrides are merged into the section's rows *before* anything is
  counted (`apply_overrides`, 248–…), and an override matching no row **fails the run** rather than
  silently dropping the curation. Its current keys are `_comment`, `provenance`, `docbuilder` —
  **there is no `cloudcost` entry**, so cloudcost has no curated cells to protect today.

**The ritual that avoids clobbering curated prose** (do **not** run a full regen):

```bash
# 1. Confirm every section file is present first — a missing one is silently
#    replaced by "_Section not available._" and the matrix ships partial.
ls docs/.sections/

# 2. Regenerate ONLY the changed section (from aetheris/):
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/agents/capability_matrix_cloudcost.exs

# 3. Re-assemble from the full nine-file set:
python3 ../aetheris-agents/scripts/assemble_matrix.py
```

The hazard is mechanical, not stylistic: `load_sections` (`assemble_matrix.py:181–209`) walks the
fixed `SECTIONS` list and, for any file not on disk, appends a placeholder whose body is
`_Section not available._` and whose agent/script row lists are empty — with a `_warn` and exit 1,
but the file is still written. Because `docs/.sections/` is gitignored, a fresh clone or a cleaned
scratch directory has **zero** sections, so `./scripts/sprint.sh capability_matrix` on such a tree
would re-run all nine agents, and a single agent failure silently empties that use case's rows in
the committed matrix. Regenerate the one section; keep the other eight files.

**Current cloudcost cells (stale — BL-090's subject).** `docs/capability-matrix.md:192–209`:
the Label cell reads `Cloudcost Orchestrator` (192–198), i.e. pre-BL-083, where the agent now emits
`"Cloudcost · DigitalOcean"` / `"Cloudcost · AWS"` (`cloudcost_orchestrator.exs:286`); the Scripts
table lists six scripts (204–209) and **omits `detect_optimization_signals.py`**, which
`tools.json:198–315` declares and which has existed since m2 t4; and the Summary row reads
`| cloudcost | 1 | 6 |` (`capability-matrix.md:270`).

## A10. `cloudcost/runbook.md` — credential posture, and where a third provider's goes

Both existing postures are recorded:

- **`## Prerequisites`** at `runbook.md:15`, with `### DigitalOcean` at **:24** (the `CLOUDCOST_DO_TOKEN`
  read-only PAT, the `DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN` shadowing hazard, and a fresh-login-shell
  verification one-liner at :31) and `### AWS` at **:34** (the `CLOUDCOST_AWS_*` set, the explicit-session
  claim, why the shadowing problem is worse on AWS, the eval-time raise, and the `set -a` export rule
  at :51–61). The section closes at :63 with "The credentials gate only the *live* steps".
- Further D2 material: `### D2 posture — credentials in Rig (documented, not coded)` at **:294**
  (storage is plaintext on disk, :331; a non-leak verification against a live run, :340–354);
  the Rig agent-config table at :251–262 listing the six current rows.
- `## Exercising the ≥1-orphan path` at **:197** (the BL-069 planting procedure, DO at :197ff, AWS at :215).
- `## Adding a provider` at **:414** — already written as the third-provider checklist: new adapter
  emitting the two frozen schemas with the canonical vocabulary, recorded fixtures, an orchestrator
  `case` clause, and (`:420–428`) the BL-096 rule that the new adapter measures its own real duration
  and confirms the declared `fetch_timeout_ms` still has margin rather than inheriting a number. It
  closes (`:433–437`) pointing at **BL-074** and **BL-070** as pre-provider-three reading.

**Where a Linode posture section belongs:** a new `### Linode` heading immediately after the AWS
subsection, i.e. inserted at **`runbook.md:62`**, before the "The credentials gate only the *live*
steps" line at :63 — matching the two-heading pattern established at :24 and :34. A second edit
belongs at `## Adding a provider` (:414) only if the Linode work changes that checklist; and the Rig
env table at :251–262 gains a `CLOUDCOST_LINODE_TOKEN` row when `tools.json` declares one.

## A11. TAX AND TOTALS

**`fetch_do.py`.** `totals.amount` is `money(summary.get("amount"))` — `fetch_do.py:306`, where
`summary` is the response of `GET /customers/my/invoices/{uuid}/summary` (`fetch_costs`, 481–489).
Each `line_items[].amount` is a per-service sum over `summary["product_charges"]["items"][].amount`
(`normalize_cost`, 283–297).

**Whether that is pre- or post-tax is not determinable from the code.** The adapter reads exactly one
scalar (`summary["amount"]`) and never touches the sibling fields. The recorded fixture
`cloudcost/tests/fixtures/do_invoice_summary.json` shows the invoice-summary document *does* carry
the distinction — `"amount": "172.21"`, `"product_charges": {"amount": "172.21", …}`,
`"overages": {"amount": "0.00"}`, `"taxes": {"name": "Taxes", "amount": "0.00"}`,
`"credits_and_adjustments": {"amount": "0.00"}`, `"usage_total": "172.21"` — but with
`taxes.amount == 0.00` the pre-tax and post-tax readings coincide numerically, so the fixture cannot
discriminate them either. Per the prompt's instruction this is **not** inferred from DO's published
docs. See §Unknowns U5.

**`fetch_aws.py`.** `totals.amount` is `round(sum(item["amount"] for item in line_items), 2)`
(`fetch_aws.py:741`) — the adapter's own sum, not a figure AWS declares. Each `line_items[].amount`
is the `UnblendedCost.Amount` of one Cost Explorer `SERVICE` group (`fetch_costs`, 841–854;
`normalize_cost`, 728–740).

**AWS's total is therefore post-tax, with tax as an ordinary line item.** Cost Explorer returns `Tax`
as its own `SERVICE` group, so it is summed like any other service. Evidence from the recorded
fixture `cloudcost/tests/fixtures/aws_ce_cost_and_usage.json`, whose groups are:

```
['Amazon Elastic Compute Cloud - Compute']  UnblendedCost 120.50 USD
['Amazon Relational Database Service']      UnblendedCost  47.67 USD
['EC2 - Other']                             UnblendedCost  22.05 USD
['Tax']                                     UnblendedCost   8.40 USD
['Amazon Simple Storage Service']           UnblendedCost   3.12 USD
['AWS Cost Explorer']                       UnblendedCost   0.00 USD
```

Nothing in `normalize_cost` or `fetch_costs` filters or special-cases `Tax`.

**Comparability, stated plainly.** AWS is post-tax and shows tax as a service row; DO is one
undifferentiated provider scalar of undetermined tax treatment. So the three providers' `totals.amount`
are **not** known to be comparable today, before Linode is added. Linode's invoice splits
`subtotal` / `tax` / `total` (Part B1), which makes the choice explicit rather than inherited: the
milestone doc has to pick one and say which, and the honest reading of the existing two is that
picking `total` matches AWS's behaviour and picking `subtotal` matches nothing that has been
established.

## A12. Does anything downstream read `line_items[].region`?

**No. It is carried and never read.**

- Both adapters emit it hard-coded null — `fetch_do.py:290` (`"region": None`, with 275–278 recording
  that DO bills at service granularity so the adapter never fabricates resource-level attribution)
  and `fetch_aws.py:733` (same, per D4/decision B at 724–727).
- `compose_report_data.py` — `service_totals` (150–246) is the only function that iterates
  `cost["line_items"]` (167), and it reads exactly two keys: `item.get("service")` (176) and
  `item.get("amount")` (177). Grep for `line_items` in that file returns lines 20, 154, 167, 191, 193,
  194, 200, 208, 694 — none of which touch `region`. Every `region` occurrence in the file is
  something else: `compose_report_data.py:402` reads the **inventory resource's** `region` for the
  top-untagged-spenders rows, and 507–550/607/641–644 are the `region_coverage` section, which is
  lifted from `cost["provider_extra"]["swept_regions"]` (`SWEPT_REGIONS_KEY`, 516; 540–550) — a
  different field entirely.
- `render_report.py` — grep for `line_items` returns nothing; grep for `region` returns one line,
  `render_report.py:84` (`OPTIONAL_FIELDS = (("region_coverage", list),)`).
- `templates/report.html.j2` — the `region` hits are `region_coverage` (111–121), `row.region` at 365
  and 529 (top-untagged-spenders and optimization-signals rows, both inventory-derived), and
  `candidate.region` at 460 (orphan candidates, inventory-derived). No template expression reads a
  cost line item's region.

Consequence for Linode: `invoice-item.region` (Part B1, non-null for hourly items) has **no consumer**
today. Populating it changes no rendered output; leaving it null matches both existing adapters.

---

# Part B — Linode APIv4, from the OpenAPI spec

All pointers below are into the retrieved artifact identified in the Retrieval record. Note the
schema names are **kebab-case** (`invoice-item`, not `InvoiceItem`); pointers are given as read.

## B1. VERIFY — the four stated findings

| Stated | Verdict | Pointer |
|---|---|---|
| Invoice properties: `billing_source` (enum `akamai\|linode`), `date`, `id`, `label`, `subtotal`, `tax`, `tax_summary[]` (name + tax), `total` | **CONFIRMED, exactly and completely** | `components.schemas.invoice.properties` |
| InvoiceItem properties: `amount`, `from`, `label`, `quantity`, `region` (nullable), `tax`, `to`, `total`, `type` (enum `hourly\|misc`), `unit_price` | **CONFIRMED, exactly and completely** | `components.schemas.invoice-item.properties` |
| Account: `balance`, `balance_uninvoiced` | **CONFIRMED** | `components.schemas.account.properties.balance`, `.balance_uninvoiced` |
| No `currency` field anywhere in the billing surface; USD only in descriptions | **CONFIRMED** | see the sweep below |

**Invoice** — `components.schemas.invoice.properties` has exactly these eight keys, no more:

- `.billing_source` — `type: string`, `enum: ["akamai","linode"]`, `__Filterable__ __Read-only__`.
- `.date` — `type: string`, `format: date-time`, "When this Invoice was generated."
- `.id` — `type: integer`, "The Invoice's unique ID."
- `.label` — `type: string`, "The Invoice's display label."
- `.subtotal` — `type: number`, "**The amount of the Invoice before taxes** in US Dollars."
- `.tax` — `type: number`, "The amount of tax levied on the Invoice in US Dollars."
- `.tax_summary` — `type: array`; `components.schemas.invoice.properties.tax_summary.items.properties`
  is exactly `{name: string ("The source of this tax subtotal.", example "PA STATE TAX"),
  tax: number ("The amount of tax subtotal attributable to this source.", example 12.25)}`,
  `additionalProperties: false`.
- `.total` — `type: number`, `__Filterable__ __Read-only__`, "**The amount of the Invoice after taxes** in US Dollars."

`subtotal`/`tax`/`total` are three separate fields with explicit before/after-tax descriptions — this
is the fact that makes the A11 comparability question decidable for Linode and only for Linode.

**InvoiceItem** — `components.schemas.invoice-item.properties` has exactly those ten keys.
`.region` is `type: string, nullable: true` — "The ID of the applicable Region associated with this
Invoice Item. `null` if there is no applicable Region." `.type` is `enum: ["hourly","misc"]`.
`.unit_price` is `type: string` (not number — a coercion the adapter must handle, cf. `_normalized.money`).
`.amount` = "unit price multiplied by quantity"; `.total` = "The price of this Item **after taxes**".
The list wrapper `components.schemas.added-get-invoice-items-200.properties.data.items` declares the
identical ten keys with `additionalProperties: false`, so the endpoint adds nothing to the named schema.

**Account** — `.balance` = "This account's balance, in US dollars."; `.balance_uninvoiced` =
"This account's **current estimated invoice** in US dollars. This is not your final invoice balance.
**Transfer charges are not included in the estimate.**" That caveat matters: `balance_uninvoiced` is
the natural analogue of DO's `month_to_date_usage`, and it is documented as incomplete.

**Currency sweep.** Two independent passes over the retrieved artifact:

1. Structural — walk every `properties` object in the document and report any key matching `currenc`.
   Hits: only `innodb_thread_concurrency` (six occurrences under the `databases/mysql` config paths)
   and `trigger_occurrences` (seven, under `monitor/*/alert-definitions`). **Zero currency fields.**
2. Textual — regex `currenc` (case-insensitive) over the raw 7.9 MB file. Two hits, both irrelevant:
   the CLI example containing `--trigger_conditions.trigger_occurrences 3`, and an object-storage
   delimiter description containing "first occurrence of this character".

`US Dollars` / `US dollars` appears **100 times**, all in `description` strings. So: no currency field
exists anywhere in the spec, billing surface included, and USD is documentation only — structurally
identical to DO (`fetch_do.py:55–56`: "DO bills in USD; the billing API carries no currency field",
`CURRENCY = "USD"`) and to AWS (`fetch_aws.py:70–71`).

## B2. Is there a machine-readable resource identifier on an InvoiceItem?

**CONFIRMED — there is none.** The complete property set is
`{amount, from, label, quantity, region, tax, to, total, type, unit_price}`
(`components.schemas.invoice-item.properties`, cross-checked against
`components.schemas.added-get-invoice-items-200.properties.data.items.properties`, which carries
`additionalProperties: false`). No `id`, no `linode_id`, no `entity`, no `url`, no `resource_id`, and
no `x-` extension carrying one. The only place a resource appears is inside the human-facing
`label` string, whose own example is `"Linode 123"`.

This matches — and is bounded by — the existing contract: both adapters already emit
`line_items[].resource_id: null` at service granularity (`fetch_do.py:289`, `fetch_aws.py:732`), and
`source_granularity` is a first-class field (`fetch_do.py:304`, `fetch_aws.py:746`). Linode's
grouping key is therefore the `label` string, and any parsing of an id *out* of that label would be
fabricated attribution of exactly the kind D4 forbids.

## B3. Linode instance `status` — the complete enum

`paths./{apiVersion}/linode/instances.get.responses.200.content.application/json.schema` →
`…data.items.properties.status`. Complete enum, in spec order:

```
running, offline, booting, busy, rebooting, shutting_down, provisioning,
deleting, migrating, rebuilding, cloning, restoring, stopped, billing_suspension
```

Fourteen values. Classification, from the spec's own text and only that:

| Value | Reading |
|---|---|
| `offline` | powered-off, terminal. `x-linode-cli-color` renders it `red` alongside `running`→`green`, i.e. the CLI treats it as one of the two steady states |
| `stopped` | powered-off, terminal — **and the value the description explicitly names**: "when a compute instance goes into maintenance mode, its status is `stopped`" |
| `billing_suspension` | terminal, not powered-off by the customer: "payment is past due on the compute instance, so we've suspended its use" |
| `running` | terminal, in service |
| `booting`, `rebooting`, `shutting_down`, `provisioning`, `deleting`, `migrating`, `rebuilding`, `cloning`, `restoring`, `busy` | transient. `busy` = assigned to a placement group and currently booting; `provisioning` = OS/Marketplace application being applied; the rest are self-describing |

**The seam problem this creates.** The enum contains *two* powered-off spellings, `offline` and
`stopped`, and the spec does not say which one a customer-stopped Linode reports — it documents only
that `stopped` is what maintenance mode produces. Mapping the wrong one to `STATE_STOPPED`
(`_normalized.py:62`) silently disarms `rule_stopped_compute_with_attached_storage`
(`detect_orphans.py:265`) with no error anywhere. Note also that `stopped` *collides literally* with
the canonical value, so a naïve pass-through would produce a rule that fires correctly for the
maintenance case and never for the ordinary powered-off case — the well-formed-wrong-answer shape.
Settling this is U1.

## B4. Per-class inventory surface

Requests below are stated as spec facts (`security` scope, path, list-vs-per-parent), not as a
recommended sweep. Object Storage, LKE, Firewalls and VPCs are **out of scope** for this milestone and
were not scouted; noted only as existing (`/{apiVersion}/object-storage/*`, `/{apiVersion}/lke/*`,
`/{apiVersion}/networking/firewalls*`, `/{apiVersion}/vpcs*` are present in `paths`).

### Compute instance — `GET /{apiVersion}/linode/instances` (`linodes:read_only`)

Complete field set: `alerts, backups, capabilities, created, disk_encryption, group, has_user_data,
host_uuid, hypervisor, id, image, interface_generation, ipv4, ipv6, label, lke_cluster_id,
maintenance_policy, placement_group, region, specs, status, tags, type, updated, watchdog_enabled`.

| Need | Field |
|---|---|
| status | `.status` (B3) |
| attachment | — (an instance is the attachment target, not the attached) |
| created | `.created` (`format: date-time`); `.updated` also present |
| tags | `.tags` — `array` of `string` |
| region | `.region` — `string`, the region slug |
| size/type | `.type` — the Linode type id (e.g. `g6-standard-2`), the key into `/linode/types` for pricing |
| extra | `.specs.{disk,memory,vcpus,gpus,transfer}`; `.backups.{available,enabled,last_successful,schedule}` — `.backups.enabled` says whether the Backup add-on bills for this instance, `.backups.last_successful` is `null` when there was no previous backup |
| LKE linkage | `.lke_cluster_id` — non-null marks an instance owned by an LKE cluster (out of scope, but it identifies rows that are not independently orphanable) |

### Volume — `GET /{apiVersion}/volumes` (`volumes:read_only`)

Complete field set: `created, encryption, filesystem_path, hardware_type, id, io_ready, label,
linode_id, linode_label, region, size, status, tags, updated`.

| Need | Field |
|---|---|
| status | `.status` — `enum: ["creating","active","resizing","key_rotating"]` |
| attachment | `.linode_id` — `type: integer, nullable: true`, "The unique identifier of the Linode this volume is attached to, if applicable"; `.linode_label` (nullable) is its human name; `.io_ready` is a boolean "successfully attached to a Linode and ready for read and write operations" |
| created | `.created`; `.updated` also present |
| tags | `.tags` — `array` of `string` |
| region | `.region` |
| size | `.size` — `integer`, gigabytes |

Note the axis mismatch: Linode's volume `status` is **lifecycle**, not attachment — there is no
`available`/`attached` value. Attachment is `linode_id`, exactly as DO derives it from `droplet_ids`
(`fetch_do.py:366–369`). The canonical `attached_to` maps cleanly; a normalized `state` does not have
an obvious source, and `active` means "online and ready for use" whether attached or not.

### IP address — `GET /{apiVersion}/networking/ips` (`ips:read_only`)

Complete field set: `address, gateway, interface_id, linode_id, prefix, public, rdns, region,
subnet_mask, type, vpc_nat_1_1`. `GET /{apiVersion}/networking/ips/{address}` returns the identical
set.

| Need | Field |
|---|---|
| status | **absent** — no status/state/reserved field |
| attachment | `.linode_id` — "The ID of the Linode this address currently belongs to", `type: integer`, **not marked nullable**; `.interface_id` (`integer, nullable`) is the Beta Linode-interface assignment, `null` when unassigned or on a legacy config profile |
| created | **absent** — no allocation or creation timestamp |
| tags | **absent** |
| region | `.region` |
| kind | `.type` — `enum: ["ipv4","ipv6","ipv6/pool","ipv6/range"]`; `.public` — boolean |

**Which are reservable/extra: not answerable from this spec state.** A textual sweep for `reserved`
over the whole artifact returns five hits, all inside *request-body prose* for assigning an address
("If the address is a reserved or an automatically assigned IP, the IP must be reserved or already
assigned to a single Linode…") plus one unrelated rescue-mode note about the `sdh` slot. **No response
schema anywhere carries a `reserved` boolean, and no endpoint lists reservations.** So the direct
analogue of DO's unassigned reserved IP (`fetch_do.py:376–393`, priced by
`RESERVED_IP_UNASSIGNED_MONTHLY` at :67) and of AWS's unassociated Elastic IP
(`fetch_aws.py:538–564`) is **not expressible from this spec** — and note that `created_at: None` is
already the AWS precedent (`fetch_aws.py:556–558`), and that `rule_unassociated_static_ip` has no age
threshold (`detect_orphans.py:187–199`), so a null `created_at` costs nothing. What is missing is the
distinction between "extra/reserved" and "the free primary address every Linode has", which is the
whole content of the rule. See U2.

### NodeBalancer — `GET /{apiVersion}/nodebalancers` (`nodebalancers:read_only`)

Complete field set: `client_conn_throttle, created, hostname, id, ipv4, ipv6, label, lke_cluster,
region, tags, transfer, type, updated`.

| Need | Field |
|---|---|
| status | **absent** — no status/state field on the NodeBalancer itself |
| attachment | **not on this object** — see below |
| created | `.created`; `.updated` also present |
| tags | `.tags` — `array` of `string` |
| region | `.region` |
| type | `.type` — `enum: ["common","premium"]`, the key into `/nodebalancers/types` |
| LKE linkage | `.lke_cluster` — `object, nullable`, "`null` if this NodeBalancer isn't related to an LKE cluster" |

**How backends are read, and the request count.** Backends live under configs:
`GET /{apiVersion}/nodebalancers/{nodeBalancerId}/configs` (`nodebalancers:read_only`) returns a
`oneOf` of four protocol variants (`udp`, `tcp`, `http`, `https`), and **every one of the four**
carries `.nodes_status` — an object with `.up` ("number of backends considered to be `UP` and healthy,
and that are serving requests") and `.down` ("considered to be `DOWN` and unhealthy… not in rotation").
So a NodeBalancer has zero backends iff, across all its configs, `sum(up + down) == 0` — including
the degenerate case of zero configs.

**Request count: 1 + N.** One `GET /nodebalancers` for the list, then one `GET /{id}/configs` per
NodeBalancer. The per-config `…/configs/{configId}/nodes` endpoint is **not** required — `nodes_status`
on the config already carries the count. (Contrast AWS, where the equivalent is
`describe_target_groups` + `describe_target_health` per group — `fetch_aws.py:935–957`.)
No tag-targeting concept exists on Linode, so the `"tag:<name>"` attachment convention DO needs
(`fetch_do.py:426–433`, and the exclusion at `detect_orphans.py:242–244`) has no Linode analogue.

### Image — `GET /{apiVersion}/images` (`images:read_only`)

Complete field set: `capabilities, created, created_by, deprecated, description, eol, expiry, id,
image_sharing, is_public, is_shared, label, regions, size, status, tags, total_size, type, updated,
vendor`.

| Need | Field |
|---|---|
| status | `.status` — `enum: ["creating","pending_upload","available"]` |
| attachment | **absent** — an image records no source instance or disk |
| created | `.created`; `.updated`, `.expiry` (nullable; only `type=automatic` images expire), `.eol` (nullable, public images only) |
| tags | `.tags` — `array` of `string` |
| region | **`.regions`, plural** — `array` of `object`, "Details on the regions where this image is stored"; there is no scalar region field |
| size | `.size` (MB, minimum deploy size), `.total_size` (bytes across all regions — but "This object is empty for existing images. It's intended for use with future functionality") |
| kind | `.type` — `enum: ["manual","automatic","shared"]`; `.is_public` boolean, `.is_shared` |

Two consequences worth carrying into the issue-doc: the normalized scalar `region` has no direct
source (pick one from `regions[]` or emit null — the schema's own answer is "many"), and the aged-
snapshot rule's second signal, `attached_to is None` meaning "the source is gone"
(`detect_orphans.py:220–223`), has **no field to read** — an image records no source, so
`resolve_source`'s AWS-style cross-reference (`fetch_aws.py:567–587`) has nothing to cross-reference
against. `is_public: true` marks distribution images that are not the account's own.

### Backup — `GET /{apiVersion}/linode/instances/{linodeId}/backups` (`linodes:read_only`)

**Not a paginated collection.** The response is
`{automatic: [Backup], snapshot: {current: Backup, in_progress: Backup}}` — the envelope has no
`data`/`page`/`pages`/`results`. The Backup object's complete field set is
`available, configs, created, disks, finished, id, label, status, type, updated`.

| Need | Field |
|---|---|
| status | `.status` — `enum: ["paused","pending","running","needsPostProcessing","successful","failed","userAborted"]`; `.available` boolean ("available for restoration") |
| attachment | **implicit only** — the parent `linodeId` in the request path; no field on the object |
| created | `.created` ("The date the Backup was taken"), `.finished`, `.updated` |
| tags | **absent** |
| region | **absent** |
| kind | `.type` — `enum: ["auto","snapshot"]`; `.label` (nullable) applies to `snapshot` type only |

This is a **per-instance N+1 call**, gated on the instance's `backups.enabled`
(`…linode/instances…data.items.properties.backups.enabled`), and the backup rows only exist while
the Linode does — so the "source is gone" signal is structurally unavailable here too.

### Managed Database — `GET /{apiVersion}/databases/instances` (`databases:read_only`)

Complete field set: `allow_list, cluster_size, created, encrypted, engine, fork, hosts, id,
instance_uri, label, members, oldest_restore_time, platform, port, region, status,
total_disk_size_gb, type, updated, updates, used_disk_size_gb, version`.

| Need | Field |
|---|---|
| status | `.status` — `enum: ["provisioning","active","suspending","suspended","resuming","failed","degraded","updating","resizing"]` |
| attachment | **absent** — no attachment concept; `.allow_list` is a CIDR access list, not an attachment |
| created | `.created`; `.updated`, `.oldest_restore_time` |
| tags | **absent — Managed Databases carry no `tags` field** |
| region | `.region` |
| size | `.type` (Linode type id), `.cluster_size` (`enum: [1,2,3]`), `.total_disk_size_gb`, `.used_disk_size_gb` |

Two seam notes. `suspended` is the closest analogue to `STATE_STOPPED` for
`rule_stopped_database_with_storage` (`detect_orphans.py:306–347`), but that rule *also* requires
`attached_to is None` (323) and `monthly_cost_estimate > 0` (326) — and a Managed Database has no
attachment field to be null and no priced type (B6), so the rule as written cannot fire on Linode
without both an adapter convention for `attached_to` (AWS invents one: `None if stopped else identifier`,
`fetch_aws.py:682`) and a price source. And the absent `tags` field means every Managed Database is
structurally untagged, which drags `tag_coverage` (`_normalized.py:135–140`) down and can flip
`account_uses_tags` (`detect_orphans.py:500`) — a governance figure moved by a schema gap, not by the
account's actual practice.

## B5. Tags

**Flat strings, not key/value.** Every occurrence is `tags: {type: array, items: {type: string}}`.
The instance-level description reads "Tags to help you organize your content"; the volume-level one
reads "Any tags applied to this object. Use [tags] to label and organize your cloud computing
resources"; the NodeBalancer one adds "Tags are for organizational purposes only."

**Complete list of GET endpoints in the spec whose item schema carries `tags`** (all `array` of `string`):

```
/{apiVersion}/domains
/{apiVersion}/domains/{domainId}
/{apiVersion}/images
/{apiVersion}/images/sharegroups/tokens/{tokenUuid}/sharegroup/images
/{apiVersion}/images/sharegroups/{sharegroupId}/images
/{apiVersion}/images/{imageId}
/{apiVersion}/linode/instances
/{apiVersion}/linode/instances/{linodeId}
/{apiVersion}/linode/instances/{linodeId}/firewalls
/{apiVersion}/linode/instances/{linodeId}/interfaces/{interfaceId}/firewalls
/{apiVersion}/linode/instances/{linodeId}/nodebalancers
/{apiVersion}/linode/instances/{linodeId}/volumes
/{apiVersion}/lke/clusters
/{apiVersion}/lke/clusters/{clusterId}
/{apiVersion}/lke/clusters/{clusterId}/pools
/{apiVersion}/lke/clusters/{clusterId}/pools/{poolId}
/{apiVersion}/networking/firewalls
/{apiVersion}/networking/firewalls/{firewallId}
/{apiVersion}/networking/firewalls/{firewallId}/history
/{apiVersion}/networking/firewalls/{firewallId}/history/rules/{version}
/{apiVersion}/nodebalancers
/{apiVersion}/nodebalancers/{nodeBalancerId}
/{apiVersion}/nodebalancers/{nodeBalancerId}/firewalls
/{apiVersion}/volumes
/{apiVersion}/volumes/{volumeId}
```

Within the milestone's in-scope classes: **instances, volumes, NodeBalancers and images carry tags;
IP addresses, backups and Managed Databases do not.** A standalone tag surface also exists
(`GET /{apiVersion}/tags`, `GET /{apiVersion}/tags/{tagLabel}`), not scouted further.

Bearing on `KEEP_TAG` (`detect_orphans.py:84`, `"keep=true"`, matched
`tag.strip().lower() == KEEP_TAG`): Linode tags are flat strings like DO's, so the `k=v` spelling is
writable by hand but is not a native key/value construct — the same "adapter convention masquerading
as a shared constant" that BL-074 already names for AWS.

## B6. Pricing

Monthly price per class, from the spec:

| Class | Endpoint | Monthly field | `security` |
|---|---|---|---|
| Compute instance | `GET /{apiVersion}/linode/types` | `.price.monthly` (`number`), plus `.region_prices[].{id,hourly,monthly}` for region-specific prices | **`null` — unauthenticated** |
| Backups add-on | same endpoint | `.addons.backups.price.monthly`, plus `.addons.backups.region_prices[]` | unauthenticated |
| Volume | `GET /{apiVersion}/volumes/types` | `.price.monthly` + `.region_prices[]` | **`null` — unauthenticated** |
| NodeBalancer | `GET /{apiVersion}/nodebalancers/types` | `.price.monthly` + `.region_prices[]` | **`null` — unauthenticated** |
| Network transfer | `GET /{apiVersion}/network-transfer/prices` | `.price.monthly` is **`nullable: true`, example `null`** | unauthenticated |
| Managed Database | `GET /{apiVersion}/databases/types` | **no `price` object at all** — fields are `class, disk, engines, id, label, memory, vcpus` | — |
| Image | *(no types/prices endpoint exists)* | — | — |

**Classes with no monthly figure obtainable from the API: network transfer (`monthly` is explicitly
nullable and exemplified as `null`), Managed Databases (no price object), and Images (no endpoint).**
I cannot date this to 2026-07-01 — the artifact carries no price effective-date anywhere; what is
dated is the retrieval (2026-08-04) and the ETag. See U7.

Two cautions for whoever writes the adapter's cost model:

1. The `monthly` values visible in the spec are **`example` values, not data** — `/volumes/types`
   shows `{hourly: 0.0015, monthly: 0.1}` with `id: "volume"`, `label: "Storage Volume"`, and
   `/nodebalancers/types` shows the identical `{0.0015, 0.1}` pair. Whether the volume figure is
   per-GB (as DO's `VOLUME_GIB_MONTHLY = 0.10` is, `fetch_do.py:65`) or per-volume is **not stated in
   the schema**; the NodeBalancer example being the same number strongly suggests both are
   placeholders rather than real rates. Read live values; do not transcribe examples. See U11.
2. Because the four types endpoints are unauthenticated (`security: null`), the price sweep needs no
   scope and cannot be defeated by a narrow PAT — which is a genuine simplification over AWS, where
   `pricing:GetProducts` was deliberately excluded from the IAM policy and a hand-maintained table
   was written instead (`fetch_aws.py:114–128`). A Linode adapter can read real prices rather than
   hard-coding a table, which removes the whole class of drift BL-071 exists to check.

## B7. Pagination and rate limits

**Pagination — fully specified.** The envelope is `components.schemas.pagination-envelope`:
`{data: [...], page: integer, pages: integer, results: integer}` (`components.schemas.page`,
`.pages`, `.results` are the individual field schemas; `additionalProperties: false`). The query
parameters are `components.parameters.page-offset` (`name: page`, `in: query`,
`schema: {type: integer, default: 1, minimum: 1}`) and `components.parameters.page-size`
(`name: page_size`, `in: query`, `schema: {type: integer, default: 100, minimum: 25, maximum: 500}`).
`GET /{apiVersion}/linode/instances` declares exactly `X-Filter` (header),
`page` and `page_size` (query).

This is page-number pagination with a total (`pages`), unlike DO's `links.pages.next` follow-the-URL
scheme (`fetch_do.py:180–194`) — so the `_same_origin` re-rooting guard (`fetch_do.py:134–143`) has
no Linode analogue and no purpose; a Linode client increments an integer.

Server-side filtering is available via the `X-Filter` header
(`components.parameters.x-filter-header`, plus `components.schemas.x-filter` and `x-filter-criteria`),
which neither existing adapter uses.

**Rate limits — not in the spec, per endpoint family or otherwise.** The artifact contains no
numeric rate limit, no `X-RateLimit-*` header definition, and no `429` response declaration. What it
carries is a link to an external page (`techdocs.akamai.com/linode-api/reference/rate-limits`) and a
per-operation note "This operation has specific rate limits" on exactly four operations, all
out of scope:

```
POST   /{apiVersion}/object-storage/buckets       (post-object-storage-bucket)
POST   /{apiVersion}/object-storage/keys          (post-object-storage-keys)
PUT    /{apiVersion}/object-storage/keys/{keyId}  (put-object-storage-key)
DELETE /{apiVersion}/object-storage/keys/{keyId}  (delete-object-storage-key)
```

None of the in-scope GET list operations carries that note. That is the absence of a *special* limit,
not evidence of no limit — the general limit exists and is documented off-spec. See U4.

## B8. Auth env vars read by default

*(Scope-set selection is the human's and is not proposed here.)* Neither library is installed locally
(`python3 -c "import linode_api4"` → `ModuleNotFoundError`; `pip3 show linode-cli linode_api4` →
"Package(s) not found"), so both were read from source: `linode/linode-cli@main` and
`linode/linode_api4-python@main`, fetched 2026-08-04 to the same scratch path.

**`linode_api4` (the Python SDK) reads no environment variable at all.**
`grep -rn "os.environ\|getenv" linode_api4-python-main/linode_api4/` returns **0 hits**. The token is
a required positional constructor argument: `linode_api4/linode_client.py:341–352`,
`def __init__(self, token, base_url="https://api.linode.com/v4", user_agent=None, page_size=None, retry=True, …)`.
So there is **no default-pickup arm**, and therefore no shadowing hazard of the DO/AWS kind from the
SDK — the credential can only arrive as an argument the adapter chose to pass.

**`linode-cli` reads exactly one token variable: `LINODE_CLI_TOKEN`.**
`linodecli/configuration/config.py:28` — `ENV_TOKEN_NAME = "LINODE_CLI_TOKEN"`; read at
`config.py:69` — `environ_token = os.getenv(ENV_TOKEN_NAME, None)`, and at 74–79 its presence is what
suppresses the interactive `configure()` and sets `used_env_token`. Documented in
`wiki/Installation.md:15`. It also reads endpoint-shaping variables — `linodecli/helpers.py:12–19`:
`LINODE_CLI_API_HOST`, `LINODE_CLI_API_VERSION`, `LINODE_CLI_API_SCHEME`, `LINODE_CLI_CA` — plus
`LINODE_CLI_CONFIG` (config-file path), `LINODE_CLI_TEST_MODE` (`linodecli/__init__.py:41`),
`LINODE_CLI_SUPPRESS_VERSION_WARNING` (`api_request.py:544`), and, in the `obj` plugin only,
`LINODE_CLI_OBJ_ACCESS_KEY` / `LINODE_CLI_OBJ_SECRET_KEY` (`plugins/obj/__init__.py:378–379`).

**A bare `LINODE_TOKEN` is read by nothing.** All 7 occurrences across both trees are CI secret names
and shell scripts — `linode-cli-main/.github/workflows/e2e-suite.yml:126,188,202,221`,
`e2e-suite-windows.yml:129`, `scripts/lke_calico_rules_e2e.sh:24,39`, and
`wiki/Installation.md:15` (`-e LINODE_CLI_TOKEN=$LINODE_TOKEN`, i.e. the *user's* variable being
mapped onto the CLI's). It is a widespread convention with no library that honours it.

**So the DO-style hazard is materially weaker here, and the residual is different in kind.** The
`warn_shadowing_env` analogue (`fetch_do.py:53`, `fetch_aws.py:63–68`) has a much shorter honest
list — `LINODE_CLI_TOKEN` is the only variable any Linode tooling reads as a credential, with
`LINODE_TOKEN` warnable on convention grounds alone. The endpoint trio
(`LINODE_CLI_API_HOST`/`_VERSION`/`_SCHEME`) is a *different* hazard class worth naming: it redirects
where a credential is sent rather than which credential is used, and neither existing adapter has an
analogue of it.

**One live observation.** This machine's environment carries a variable named **`LINODE_BILLING`**
(64 characters, non-path, non-URL shape — a Linode PAT is 64 hex characters). Its value was **not
read, not echoed, and not used**, and it is not a name any library above reads. Flagged only because
it is a credential-shaped variable already present under a name outside the documented set. See U12.

## B9. SCOPE-GRANTED vs GENUINELY-EMPTY

### (a) What a list endpoint returns when the token lacks scope — **NOT ESTABLISHABLE from the spec**

Per-operation responses are not enumerated by status. `paths./{apiVersion}/linode/instances.get.responses`
declares exactly two keys: `"200"` and `"default"`. The `200` description is "Returns an array of all
Linodes on your Account."; the `default` description is the sentence "See [Errors](…/errors) for the
range of possible error response codes." — i.e. the spec defers the entire status-code question to an
external page. There is **no `401`, `403` or `429` response object on any in-scope operation**
(`components.responses` holds only `409`, `504-account-cancel`, `accepted-response`,
`deprecated-response`, `error-response`).

The error **body shape** is fully specified, and is the same for every failure —
`components.responses.error-response` →
`{errors: [{field: string, reason: string}]}`, `additionalProperties: false`
(also `components.schemas.error-object`). `field` is "The field in the request that caused this
error… In some cases this may come back as `null` if the error is not specific to any single element
of the request"; `reason` is "What happened to cause this error."

So: shape yes, **status code no**, and — critically — no documented machine-readable discriminator
inside the body either. `reason` is prose. See U3.

### (b) Can a token's own granted scopes be read back at runtime — **partially**

`GET /{apiVersion}/profile/tokens` (`operationId: get-personal-access-tokens`,
`security: [{personalAccessToken: []}, {oauth: ["account:read_only"]}]`) returns items with the
complete field set `{created, expiry, id, label, scopes, token}`, where
`…data.items.properties.scopes` is
`{type: string, format: "oauth-scopes", example: "*", readOnly: true}` — "The scopes this token was
created with. These define what parts of the Account the token can be used to access."

The exact string format is `format: oauth-scopes`; the only example in the spec is `"*"`. The
vocabulary is `components.securitySchemes.oauth.flows.authorizationCode.scopes`, 29 entries:

```
account:read_only        account:read_write        domains:read_only      domains:read_write
events:read_only         events:read_write         firewall:read_only     firewall:read_write
images:read_only         images:read_write         ips:read_only          ips:read_write
linodes:read_only        linodes:read_write        lke:read_only          lke:read_write
longview:read_only       longview:read_write       monitor:read_only      monitor:read-write
nodebalancers:read_only  nodebalancers:read_write  object_storage:read_only object_storage:read_write
stackscripts:read_only   stackscripts:read_write   volumes:read_only      volumes:read_write
vpc:read_write
```

(Note `monitor:read-write` uses a hyphen where every other write scope uses an underscore, and
`vpc` has no read-only variant — both as written in the spec.)

**Two limits that make this less useful than it looks.** First, the endpoint lists *every* PAT on the
account and the objects carry no "this is the caller" marker — `.token` is documented as returning
"only the first 16 characters" outside creation, so identifying which row is the calling token means
comparing a prefix of the secret, which the D2 posture forbids handling. Second, the endpoint itself
requires `account:read_only`; a PAT deliberately scoped down to `linodes`/`volumes`/`nodebalancers`
and *not* granted account access cannot call it — and, by (a), the failure is indistinguishable in
kind from any other. `GET /{apiVersion}/profile` and `GET /{apiVersion}/profile/grants` are the two
endpoints declaring `oauth: []` (no scope required), but neither returns the token's scopes.

### (c) Which of (a) or (b) gives a reliable "not inventoried — scope not granted" marker

**Neither, as things stand — and that is the finding.** (b) is the only one that could yield a
*positive* declaration ("the token holds `volumes:read_only`, so an empty volume list means the
account owns no volumes"), but it is self-referentially gated: it needs `account:read_only`, which is
exactly the scope a minimal inventory PAT would omit. (a) cannot supply the marker because the spec
declares no status code for the denial.

What the spec *does* support is a construction the milestone can lean on, stated here as a fact and
not as a recommendation: because the adapter already treats a failing source as an `errors[]` entry
rather than an empty list (`fetch_do.py:497–504`, `fetch_aws.py:885–905`), any non-200 on a class
endpoint is already distinguishable from a 200-with-empty-data — *provided the class is never allowed
to degrade silently to `[]`*. The precedent is explicit in the AWS adapter: `fetch_aws.py:98–102`
records why `UnauthorizedOperation` is deliberately **not** classed as a benign disabled-region
warning, because "a missing `ec2:Describe*` [would] produce an empty inventory on a green run, with a
reason that reads plausibly and is wrong". That is this exact hazard, already met once and already
decided once.

If `account:read_only` **is** on the PAT, `GET /profile/tokens` gives a genuine
scope-grant read-back; the granted set can then be compared against the 29-value vocabulary and each
un-granted class marked. Whether to require that scope is the human's call, not this scout's.

## B10. `last_activity_at`

The candidate source is **`GET /{apiVersion}/account/events`** (`operationId: get-events`,
`security: [{personalAccessToken: []}, {oauth: ["events:read_only"]}]`).

**Retention: 90 days**, stated in the operation description — "Returns a collection of event objects
that represent actions you've taken on your account, **over the last 90 days**. The events returned
depend on your user grants."

**Entity linkage.** `…data.items.properties.entity` is
`{id: integer, label: string, type: string, url: string}` — `entity.id` is "The unique identifier
assigned to the entity", with the documented caveat that "The `disks` and `backups` entities use the
`id` of their parent Linode when filtering"; `entity.url` is "The URL where you can access this
event's entity". A `secondary_entity` of the same shape is also present. Each event carries
`.created` (`format: date-time`, `__Filterable__`), `.action`, `.status`
(`enum: ["completed","failed","finished","in_progress","notification","scheduled","started"]`),
`.username`, `.duration`, `.percent_complete`, `.message`, `.seen`, `.rate`, `.time_remaining`.

**Coverage — some classes, not all.** `entity.type` is an enum of exactly:

```
account, backups, community, disks, domain, entity_transfer, firewall, image,
ipaddress, linode, longview, loadbalancer, managed_service, nodebalancer,
oauth_client, profile, stackscript, tag, ticket, token, user, user_ssh_key, volume
```

In-scope classes present: `linode`, `volume`, `ipaddress`, `nodebalancer`, `image`, `backups`.
In-scope class **absent: Managed Databases** — there is no `database` entity type, even though the
`action` enum contains 18 `database_*` actions (`database_create`, `database_suspend`,
`database_resume`, `database_resize`, …). So database events exist but their entity linkage is not
expressible through `entity.type`.

**What it would actually populate.** The `action` enum is control-plane actions —
`linode_boot`, `linode_shutdown`, `linode_reboot`, `linode_resize`, `volume_attach`, `volume_detach`,
`volume_create`, `nodebalancer_config_update`, `image_upload`, and so on. The newest event's `created`
for a given entity is therefore "when someone last *changed* this resource", not "when this resource
was last *used*". That is a different quantity from what `modifier_recent_activity`
(`detect_orphans.py:364–383`) reads it as — a signal that the resource is in service — and a
90-day window truncates it. Cost: one paginated sweep of `/account/events` (page_size ≤ 500),
joined client-side on `(entity.type, entity.id)`.

**Reported, not decided** — per the prompt, whether to populate `last_activity_at` is the milestone
doc's call. The relevant precedent is that both existing adapters emit `null` for every resource
(`fetch_do.py:347,367,387,407,442`; `fetch_aws.py:502,530,559,602,623,651,681,706`) and
`detect_orphans.py:76–77` calls that "the correct outcome, not a gap to paper over with
`created_at`".

---

# Part C — latency measurement

**Not measured — no token.** `CLOUDCOST_LINODE_TOKEN` is not exported in this environment (checked
without echoing any value; the check printed `TOKEN_UNSET`, and `LINODE_TOKEN`, `LINODE_CLI_TOKEN`,
`LINODE_API_TOKEN` are all unset likewise). Per the stated precondition, no Linode API call was made
and no token was prompted for. No token value appears anywhere in this file.

The measurement remains owed before the fetch-step timeout can be declared per BL-096 (§A5) — see U9.

---

# §Unknowns

| # | Unknown | What would settle it |
|---|---|---|
| U1 | Which of `offline` / `stopped` a customer-powered-off Linode actually reports (B3). Both are in the enum; the spec documents only that maintenance mode yields `stopped` | One live `GET /linode/instances` against an account holding a deliberately powered-off Linode, recorded as a fixture. A `linode-cli linodes list` transcript from the human would do equally well |
| U2 | Whether an unassigned or "extra"/reserved IP appears in `GET /networking/ips` at all, and how it is distinguishable from the free primary address (B4). The spec has no `reserved` flag and no `created` on an IP | A live read of `/networking/ips` on an account with a deliberately-unassigned extra IP; or a later spec state that adds the field. Until then the DO/AWS static-IP rule has no established Linode input |
| U3 | The HTTP status code returned when a PAT lacks scope for a list endpoint (B9a). Only the body shape `{errors:[{field,reason}]}` is specified | One live call with a deliberately narrow PAT, status code recorded. Cannot be settled from the spec — it defers to an external errors page |
| U4 | Numeric rate limits per endpoint family (B7). The spec carries none and flags "specific" limits on four out-of-scope object-storage operations only | Reading the external rate-limits page (outside this scout's remit), or observing `X-RateLimit-*` response headers on a live sweep |
| U5 | Whether DO's `invoice summary.amount` — the value `fetch_do.py:306` writes to `totals.amount` — is pre- or post-tax (A11). The recorded fixture has `taxes.amount == 0.00`, so it cannot discriminate | A recorded DO invoice summary from a month with non-zero tax; or an explicit DO-side determination. Decides whether AWS/DO/Linode totals are comparable |
| U6 | Whether `databases:read_only` is a real OAuth scope. `paths./{apiVersion}/databases/instances.get.security` requires it, but it is absent from the 29 scopes in `components.securitySchemes` (see C4) | Creating a PAT in the Linode console and observing whether a Databases access control is offered; or a corrected spec state |
| U7 | Actual monthly prices, and their effective date. The spec's `monthly` values are `example` fields, and it carries no price effective-date anywhere | One unauthenticated `GET /linode/types`, `/volumes/types`, `/nodebalancers/types` — no credential needed, so this is settleable at any time |
| U8 | Whether an `akamai`-sourced invoice (`invoice.billing_source == "akamai"`) has the same item shape and tax fields as a `linode`-sourced one | The account's own invoices; the spec declares one schema for both |
| U9 | Linode adapter latency, hence whether `fetch_timeout_ms = 300_000` (`cloudcost_orchestrator.exs:116`) has margin for a third provider (Part C, and the runbook's own instruction at `runbook.md:420–428`) | Part C's measurement, once `CLOUDCOST_LINODE_TOKEN` exists. *Absent is unknown, not zero* |
| U10 | Whether `GET /tags/{tagLabel}` enumerates the resources carrying a tag (which would be a second route to tag coverage) — not scouted | Dumping that path's response schema; ~5 minutes, deferred as out of the stated scope |
| U11 | Whether `/volumes/types.price.monthly` is per-GB or per-volume (B6). The schema does not say, and the example (`0.1`) is identical to the NodeBalancer example | One live `GET /volumes/types` compared against a known volume's invoice line |
| U12 | What `LINODE_BILLING` (present in this environment, 64 chars, non-path) holds and who set it (B8). Value deliberately not read | The human. If it is a PAT under a non-standard name, it is a live instance of the shadowing class this milestone is about to write a guard for |

---

# §Contradictions

**C1 — `fetch_aws.py` does not populate `rate_basis`.** The prompt's A3 asks for "how each populates
`monthly_cost_estimate` and (AWS) `rate_basis`". `rate_basis` is not emitted by either adapter and is
not a field of the §Normalized inventory resource. It belongs to `detect_optimization_signals.py`, the
m2 t4 exploratory spike (`detect_optimization_signals.py:248–270`, template
`report.html.j2:559–560`), where the rule is that `monthly_cost_estimate` and `rate_basis` appear
together-or-not-at-all *within that signals artifact*. The adapters' `monthly_cost_estimate` carries
no basis. This matters for the milestone: if the Linode adapter is to emit a basis alongside its
estimates — which the unauthenticated types endpoints would make cheap and honest (B6) — that is a
**new schema field on the frozen inventory**, not the adoption of an existing AWS behaviour, and it
touches the frozen §Normalized schemas the bet says do not change.

**C2 — the prompt's B4 asks which IPs are "reservable/extra" and how attachment is expressed; this
spec state cannot answer the first half.** There is no `reserved` field on any IP response schema and
no reservation-listing endpoint; the word appears only in request-body prose for *assigning* an
address. Attachment is expressible (`linode_id`, `interface_id`), reservation is not. A milestone
plan that assumes a DO-shaped `reserved_ips` collection has no counterpart to read.

**C3 — the prompt's B9 presumes (a) is answerable from the spec ("status code and error body shape.
Quote it"); it is not.** In-scope operations declare only `200` and `default`, and `default` defers to
an external errors page. The body shape is quotable and is quoted; the status code is not in the
artifact. The instruction "if any is wrong, that is the single most valuable thing this scout can
return" applies to B1, where nothing was wrong — this is the place where a stated premise did not hold.

**C4 — spec-internal inconsistency.** `paths./{apiVersion}/databases/instances.get.security` requires
`oauth: ["databases:read_only"]`, but `components.securitySchemes.oauth.flows.authorizationCode.scopes`
does not define `databases:read_only` (or any `databases:*` scope) among its 29 entries. Either the
scope vocabulary is incomplete or the operation's requirement is wrong; the artifact contradicts
itself. Consequence: an adapter cannot decide from the spec whether a PAT *can* be granted Managed
Database read access at all. Feeds U6.

**C5 — the milestone-inherited assumption that "a provider's stopped state is one value" does not
survive contact with Linode.** `STOPPED_STATES` (`detect_orphans.py:93`) is
`frozenset({STATE_STOPPED})` — deliberately a one-element set after m2 t2 (a). Linode's enum offers
two terminal powered-off spellings, one of which (`stopped`) *is literally* the canonical value while
plausibly denoting a different condition (maintenance). This is not a contradiction of the prompt but
of the seam's shape: DO needed a rename (`off` → `stopped`), AWS needed an identity map, and Linode
may need a **decision between two candidate values**, which is a third kind of mapping the seam has
not had to express before. It belongs in the issue-doc's seam analysis, and it is the clearest single
place where the frozen-contract bet is tested this milestone.

**C6 — the provider-prefix "convention" is two conventions (A4).** Adapter output prefixes are
hand-written literals (`do_`, `aws_`); orphan and history prefixes are `provider_slug(provider)`
(`digitalocean`, `aws`). They already disagree in the shipped DO tree. Linode masks the divergence by
coincidence, which is exactly how it survives another milestone.

---

```
$ git status --short
?? cloudcost/docs/m3-linode-scout.md
```
