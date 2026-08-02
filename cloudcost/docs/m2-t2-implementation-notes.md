# m2-cloudcost t2 — implementation notes

**Ticket:** `cloudcost/m2-milestone.md` §t2 — contract adjustments + RDS heuristic + negative proof.
**Commits:** `163e059` (milestone rev 5.1, doc-only, pre-code) → `7a7b7ec` (implementation).
**Repos:** aetheris-agents only. `../aetheris` untouched (`fd9ac48`).
**Suite:** 229 pass (219 at t1 + 10 new). 8 mutations, all caught.

---

## Three adjudications, settled before the first edit

The ticket opened with three decisions that changed the shape of the work. All three were put
to Vishal and ratified; two of them corrected the committed contract, which is why rev 5.1
landed as its own commit *before* any code (doc governs code — no action past a gate until the
gate has run).

### 1. The stopped-with-storage saving is `own + attached`, not `attached` replacing `own`

Rev 5 said the saving "must sum the *attached storage's* estimate, **not the instance's own**".
Taken literally that is wrong, and wrong in an instructive way: it bakes AWS's `own = 0` into a
**shared** rule — a provider cost-model assumption sitting in shared machinery, which is
precisely seam #3, the thing BL-074 exists to remove. The rev-5 wording re-created the seam
while claiming to close it. (Vishal's own adjudication; recorded because the mechanism matters
more than the number.)

The correct rule adds and never replaces:

```
saving = resource.monthly_cost_estimate
       + Σ( v.monthly_cost_estimate  for each separately-inventoried storage resource v
                                     whose v.attached_to == resource.resource_id )
```

It is provider-agnostic *because each adapter has already encoded its own cost model into the
estimate* — the shared rule keys on no provider fact:

| | own | separately-inventoried storage | saving |
|---|---|---|---|
| DO stopped droplet `drop-stopped-1` | 24.00 (billed on-or-off, D4) | 5.00 volume | **29.00** |
| AWS stopped EC2 `i-0aaa3333` | 0.00 (no compute charge) | 16.00 EBS | **16.00** |
| AWS stopped RDS `db-stopped-1` | 23.00 (storage priced in) | none | **23.00** |

**Double-count guard.** Only *separately inventoried* storage is summed. RDS allocated storage
lives inside the instance's own estimate, so it is counted once; summing an attached volume for
a database would report 46.00 for a 23.00 saving. This is the reason the stopped-database rule
is a separate rule rather than the compute rule widened to a second type: the two differ in
exactly this, and the difference is not cosmetic. Mutation M6 pins it.

### 2. The canonical vocabulary's one home is `scripts/_normalized.py`

t1 declared `TYPE_*` / `STATE_STOPPED` locally in `fetch_aws.py`, before the shared home was
agreed. Leaving them there forces `fetch_do.py` either to cross-import from a *sibling adapter*
(the anti-pattern the repo rule names) or to re-declare the constants — drift on the very seam
t2 exists to remove. The canonical vocabulary *is* the definition of the schema seam, so by
construction it has exactly one home; `_normalized.py` already was that home for the shared
normalized-schema helpers, and its provider-agnostic source guard already read it.

So: `_normalized.py` gains `TYPE_*`, `CANONICAL_TYPES`, `STATE_STOPPED`; `fetch_aws.py`,
`fetch_do.py` and `detect_orphans.py` import them. The `fetch_aws.py` edit is a **relocation**,
not a change — and t1's 62 tests staying green is the check that it was one (run before
anything else touched the file, so the relocation was proven in isolation). §t2 Touches was
corrected to name `fetch_aws.py` explicitly rather than leaving the edit unsanctioned.

### 3. The aged manual RDS snapshot widens `rule_aged_snapshot`; it is not a second rule

An RDS manual snapshot and an EBS snapshot are the *same* heuristic — age, plus a source that
is gone — differing only in the canonical `type` the adapter emitted, which the candidate
carries. So `SNAPSHOT_TYPES = {snapshot, database_snapshot}` is the whole delta: one rule, one
0.7, one `--snapshot-age-days`, and **type-agnostic evidence sentences** (deliberately not
branched on EBS-vs-RDS). The threshold is explicitly not forked per type — if RDS ever needs a
different bound it becomes a parameter, never a second rule.

---

## What changed, by ticket clause

**(a) `state`.** `STOPPED_STATES` shrank from DO's `{"off"}` to `frozenset({STATE_STOPPED})`.
`fetch_do.normalize_droplet` maps `off` → `stopped`; DO's other statuses (`new`, `active`,
`archive`) have no canonical spelling and pass through as themselves — only the value a shared
rule keys on is normalized. `fetch_aws` already emitted canonical from its first line (t1).

**(a′) `type`.** The canonical vocabulary is now enumerated in `cloudcost/milestone.md`
§Normalized schemas (an amendment-to-complete — m1 froze the field, never its values) with the
DO↔AWS mapping table, plus a note that the provider's own name survives in `raw_ref`, which is
provenance and not vocabulary. `fetch_do` emits `compute_instance` / `static_ip`. The two
DO-keyed rules are renamed and re-keyed: `rule_unassociated_static_ip`,
`rule_stopped_compute_with_attached_storage`; their confidences and
`STOPPED_COMPUTE_MIN_AGE_DAYS` follow, as does the emitted parameter key
`stopped_droplet_min_age_days` → `stopped_compute_min_age_days` (nothing downstream reads
`parameters` — checked by grep across compose, render and the template before renaming).

**(b) filename.** `{provider}_orphan_candidates_{period}.json`, provider slugged from the
inventory envelope. Verified safe by inspection before writing it: `compose.classify()` groups
by document *shape*, not filename; the orchestrator threads the path each script prints; the
sprint case asserts only the report and `report_data`. So nothing downstream needed a change —
had `classify` keyed on the filename, this clause alone would have been a contract-leak finding.

**(c) RDS + cost model.** `fired()` takes an optional `saving` that `score()` honours; the
default path (the resource's own estimate) is unchanged for every other rule.
`rule_stopped_database_with_storage` keys on canonical `database` + stopped + `attached_to is
null` (a stopped DB serves nothing; a running one is attached to itself) + a non-zero estimate,
which *is* the signal that allocated storage still bills. `rule_aged_snapshot` widened as above.

**(d) negative proof.** `compose_report_data.py`, `render_report.py` and `templates/` are
untouched — `git diff` shows no edit. Rather than assert that in prose,
`test_compose_and_render_key_on_no_type_value` reads their code and fails if any canonical (or
DO) `type` *value* appears as a literal in either script or the template. The dormant
cross-provider merge code stays dormant (BL-070 retires it).

---

## Notes on the tests

**The test the ticket exists for.** `test_the_aws_adapter_output_feeds_detection_without_translation`
runs t1's real adapter against the recorded AWS stub and feeds its emitted inventory to the t2
CLI. Before this ticket that same run produced **zero** candidates from an inventory full of
them — a green pipeline reporting nothing, which is the milestone's own recurring class. t1's
fixtures were recorded for exactly this: stopped `i-0aaa3333` + attached `vol-0aaa3333`
(200GiB gp3 → 16.00), stopped `db-stopped-1` (200GiB gp2 → 23.00), and
`snap-db-manual-orphan` whose source DB is gone. No new AWS wire fixtures were needed.

**Vocabulary guards read the AST, not the raw text.** The m1 guard asserted on a source-text
literal (`off_literals == ['STOPPED_STATES = {"off"}  # DO vocabulary']`), which breaks the
moment prose mentions the history. `code_string_literals()` walks the AST and excludes
docstrings, so the guard asserts on *what the engine can key on* — a comment recording what m1
did here is documentation; the same word in a set literal is the seam coming back.

**Crafted RDS fixtures are separate files.** `inventory_rds_positive` / `inventory_rds_negative`
rather than extending m1's DO-shaped `inventory_rules_*`, which keeps m1's counts and ordering
assertions meaningful. `test_every_rule_in_the_catalog_fires_on_the_positive_fixture` now
asserts the *union* over both fixtures covers all six rules, derived from `RULES` itself rather
than a hand-listed set.

**Three compose test expectations moved; `compose_report_data.py` did not.** The LOW band
subtotal (24.00 → 29.00), the two-provider saving total (91.58 → 96.58) and one hardcoded
orphans filename. The script is unedited — those numbers moved because the stage *above* it
stopped under-reporting. Flagged here because "compose tests changed" and "compose changed" are
one grep apart, and only the second would be a finding.

---

## Done-check

- `python3 -m pytest cloudcost/tests/ -v` → **229 passed** (83s). Full output in the packet.
- Standalone, both providers: `aws_orphan_candidates_2026-07.json` (3 candidates, 28.75) and
  `digitalocean_orphan_candidates_2026-07.json` (5 candidates, 56.58).
- `python3 scripts/drift_check.py --strict` → 8 PASS, 0 FAIL, 3 WARN, exit 0. All three WARNs
  are `project_knowledge` manifest staleness — the documented exempt class; one of them
  (`cloudcost/milestone.md`) is this ticket's own commit re-staling the manifest, which is
  expected truth cleared at the export boundary. Run post-commit, per the check-8 ordering rule.
- **Mutations, all eight caught** (each applied to a clean tree, run, restored):

  | # | Mutation | Caught by |
  |---|---|---|
  | M1 | `STATE_STOPPED` → `"off"` | 9 tests incl. the state-vocabulary guard and the DO adapter mapping |
  | M2 | `fetch_do` stops normalizing `off` | `test_droplet_state_off_is_normalized_to_the_canonical_stopped` |
  | M3 | canonical `type` → DO vocabulary | 13 tests incl. both `type` guards and the DO inventory tests |
  | M4 | saving drops `own` | DO reads 5.00, expected 29.00 |
  | M5 | saving drops attached storage | AWS EC2 reads 0.00, expected 16.00 |
  | M6 | RDS storage double-added | RDS reads 46.00, expected 23.00 |
  | M7 | `SNAPSHOT_TYPES` narrowed to `{snapshot}` | both widened-rule tests **and** the AWS cross-stage test |
  | M8 | filename prefix removed | the CLI filename assertion |

  *Recorded because it is a real property, not an oversight:* M1 does **not** fail the AWS
  cross-stage test. Adapter and engine import the same constant, so a rename moves both
  together and the AWS pipeline stays self-consistent; what catches it is the **DO** adapter,
  whose raw `off` no longer maps onto the renamed value. The guard that binds the vocabulary to
  the *schema* rather than to itself is the DO mapping test plus the explicit
  `STOPPED_STATES == {"stopped"}` assertion — a same-constant rename is invisible to the AWS
  path by construction.

### Gates run off-territory (ticket-boundary rule)

- `bun run lint` — **green**. `bunx tsc -b` — **green**. `bun run build` — **green**.
- `mix test` — **red once, then green three times**: `969 tests, 1 failure` on the first run,
  then `969 tests, 0 failures` on three consecutive re-runs of the same tree. `../aetheris` is
  untouched by this ticket, so the failure is not attributable to the change. **The failing
  test's name was not captured** — the first run's output was piped through `tail -12`, showing
  the summary and none of the failure block (the Complete-output rule failing in its mildest
  form). Filed as **BL-075** rather than dropped, with the capture instruction in the row.
  Plausibly BL-054's `requires_worker` twelfth-slot flake; not claimed as such.
- `./scripts/sprint.sh cloudcost` — **not run**: it needs `CLOUDCOST_DO_TOKEN` and the live DO
  bill (t3 territory), and its ≥1-orphan assertion is known-red under **BL-069** (the planted
  reserved IP was deleted 2026-07-30; verified fired at t1). Named with its ticket ref per the
  tracked-carry clause, not re-triaged.

---

## Forwarded

- **t3 owes the sprint the new filename.** Nothing reads `orphan_candidates_*` by name today,
  but t3 writes the AWS sprint case and generalizes the orchestrator — the orchestrator's
  "use the path each step printed, never construct a filename" rule is what makes (b) free, and
  it should stay that way when the provider becomes a variable.
- **A4 (`swept_regions` render home) is untouched here**, as §t2 (d) requires — t3 adjudicates
  it as a deliberate enumerated compose/render adjustment.
- **BL-074's sweep is still owed.** t2 closed the three known seams; the named next candidates
  (rule-catalog age thresholds, the `keep=true` tag spelling, `EPHEMERAL_NAME_PATTERN`,
  `TAGGED_ACCOUNT_COVERAGE_THRESHOLD`) are untouched. m1's "the one seam" text is corrected in
  `cloudcost/milestone.md` §Open items, which was part of that row.
- **`provider_slug()` is duplicated on purpose.** `compose_report_data.py` carries an identical
  private `slug()`; converging them would edit compose and spoil the negative proof. The
  docstring says so and points at BL-070, which is where they converge.
- **`last_activity_at` stays null on both adapters**, so the recency modifier remains inert and
  its unfixed one-sided window bound stays latent (unchanged from m1/t1).
