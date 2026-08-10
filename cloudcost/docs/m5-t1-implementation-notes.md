# m5 t1 — establish the N>1 compose surface (read-only) — implementation notes

`Round r0, 2026-08-10. Ticket: cloudcost/m5-n1-compose.md §Ticket set → t1.`

**What this file is.** t1 establishes; it does not rule. Eight questions are answered at
HEAD so that the evidence the BL-131 ruling needs exists as a committed artifact in this
repo rather than as a derivation inside a closed cycle's prose. **No ruling is made here,
no direction is named, and no behaviour changed.** Where the evidence points one way, the
evidence is published and the reading is left to the reviewer.

**Measurement stamp.** Every `path:line` below was measured at agents
`70addd3` (`70addd335ec2d854d532f00e2f11116dd817a487`), harness `2ef0517`, unless a claim
names its own commit. Per **m5-D1**, citations into documents still being edited
(`cloudcost/m5-n1-compose.md`, `docs/backlog-2026-06.md`, `cloudcost/milestone.md`,
`cloudcost/m2-milestone.md`, `docs/milestones/hc-consolidation.md`) name their section and
quote their text rather than carrying a line number; source files, tests, `tools.json` and
the orchestrator carry `path:line` as the ticket's prompt requires.

---

## Step-1 gate

*(m4 decision 3, carried by hc-consolidation **R8**. Run before any other work in the
ticket; this section was written before E1–E8 were begun.)*

### (b) How many `--cost` / `--inventory` / `--orphans` triples the orchestrator passes

`cloudcost/agents/cloudcost_orchestrator.exs` STEP 3 carries **two mutually-exclusive
forms of one invocation**:

- `:258` — the full triple, used when STEP 1 printed `files.costs`:
  `args: ["scripts/compose_report_data.py", "--cost", "<COSTS>", "--inventory", "<INVENTORY>", "--orphans", "<ORPHANS>", "--output-dir", …, "--history-dir", …]`
- `:263` — the degraded form, used when STEP 1 did **not** print `files.costs`:
  `args: ["scripts/compose_report_data.py", "--inventory", "<INVENTORY>", "--orphans", "<ORPHANS>", "--output-dir", …, "--history-dir", …]`

Each passes **at most one of each flag**, so each yields exactly one bundle. Note the
second form passes **no `--cost` at all** — it is a pair, not a triple; BL-131's phrasing
*"passes exactly one `--cost`/`--inventory`/`--orphans` triple"* is exact for `:258` and
loose for `:263`, and the bundle count it asserts (one) is correct for both.

**Unmoved.** `git diff 6832159 HEAD -- cloudcost/agents/cloudcost_orchestrator.exs`
produces no output, so BL-131's cited `:258, :263` still resolve to the text it read.

### (a) The set of routes by which `compose_report_data.py` can receive more than one bundle

BL-131 (§*The reachability derivation*) states: *"the N>1 path is reachable only through
`--input-dir` → `discover_bundles`"*.

**That is not what source says at HEAD.** `bundles_from_args`
(`cloudcost/scripts/compose_report_data.py:912–951`) reaches N>1 with no `--input-dir`:

- the three flags are declared `action="append"` — `:887–895`;
- when `--input-dir` is absent the branch requires equal counts (`:930–937`), then computes
  `size = max(given.values())` (`:939`) and builds one bundle per index, `for i in range(size)` (`:950`).

The module docstring advertises exactly this: `:33`,
`[--cost ... --inventory ... --orphans ...]   # repeat per provider`, and `:24–26`,
*"Each provider contributes one bundle (cost + inventory + orphans), given either as a
repeatable triple or discovered from a directory."*

**The divergence is not temporal.** Filtering `git diff 6832159 HEAD --
cloudcost/scripts/compose_report_data.py` to the route-bearing identifiers
(`bundles_from_args`, `discover_bundles`, `size = max`, `range(size)`, `input-dir`,
`action="append"`) returns **no lines**: that code is byte-unchanged across the range
`6832159..70addd3`. The file did change over that range (117 insertions, 10 deletions,
`git diff --stat`, measured at `70addd3`), but not in the routes. **The derivation BL-131
cites was incomplete when it was written; nothing moved under it.**

### Gate disposition

The gate's stop condition is *"if either **has moved**"* / *"the row's premise **has
changed**"*. Nothing moved, so the temporal condition is not met.

The reviewer ruled mid-ticket (2026-08-10) that the temporal reading governs, and set a
narrower stop: stop only if the divergence means *what surface exists* differs, not if the
row's *description* of it differs. **Applied here, it does not stop.** The surface is
`compose_report_data.py`'s capacity to merge more than one provider bundle into one report
payload; that surface exists at HEAD and is the one BL-131 asks about. What diverges is the
row's count of routes reaching it. The question *supported, or removed* is answerable about
identical code, so the ticket continued to E1–E8.

One clause of the row's characterisation is materially affected and is recorded here rather
than adjudicated: BL-131 says *"N>1 is an emergent capability of a supported interface that
nothing advertises, tests or invokes"*. **E1–E3 below bear on all three verbs separately,
and they do not answer alike.**

### Bearing on §Not established item 2

`cloudcost/m5-n1-compose.md` §Not established item 2 records, as an `[OPEN]` carried
unknown, that *"BL-131's `Source:` line cites gate items that exist as no committed text"*,
and says: *"**Settled by:** nothing in-repo — the derivation is re-run at HEAD instead,
which is t1's step-1 gate and E1/E2."*

**Bearing: advanced, not settled.** Two things are now on the record that were not.

1. The item's premise is confirmed at HEAD by enumeration. Population: the 26 git-tracked
   files under `cloudcost/docs/`. `git ls-files | grep -i t5b` returns exactly one path,
   `eduloka/docs/m-eduloka-discovery-t5b.md`, which is a different use case; there is no
   `m4-t5b` notes file, and none for `m4-t5c` either. **Positive control**: the same grep
   form for `t5c\|t4c` returns 1 (`cloudcost/docs/m4-t4c-implementation-notes.md`), so the
   search reaches and the zero is absence rather than a failed search.
2. The re-run the item names as its settling route has now happened, and it did **not**
   reproduce the cited derivation — it contradicted part of it. That is the substantive
   advance: the item anticipated a re-derivation confirming or replacing the uncommitted
   one, and the re-derivation replaces it.

The item is **not settled** because settling it is a disposition, and disposing rows is not
t1's. **The item is not edited** — that file is outside `Touches` except t1's own row.

### Finding — the gate's stop condition was ambiguous

Recorded at the reviewer's instruction, and not repaired here.

`cloudcost/m5-n1-compose.md` §Ticket set → t1 → **Step-1 gate** reads *"If either has moved
from what BL-131 states, stop and report before doing anything else — the row's premise has
changed and the ticket is re-scoped rather than continued."* Two readings are available:
**temporal** (differs from what the row stated *because the world moved*) and **divergence**
(differs from what the row states, full stop). They select different tickets, and the
ambiguity is invisible until a divergence appears that is *not* temporal — which is the case
this gate produced. The reviewer ruled the temporal reading governs and added the narrower
surface test above. **The text is the reviewer's and is left unedited**; it is corrected, if
at all, in the section-scoped edit that authors the ruling into §Ratified decisions before
t2 opens, per **R12**.

---

## The eight questions

### E1 — Route census

**Derived independently of the step-1 gate**, per the reviewer's guard (a): the population
and enumeration below were built from source and from execution, and the comparison with the
gate is stated only at the end.

**Population.** Every path in `cloudcost/scripts/compose_report_data.py` by which
`compose()` receives a `bundles` list of length > 1. `compose` is defined at `:666`; it is
called from exactly one place inside the module, `main` at `:972`, which takes its list from
`bundles_from_args` at `:960` (enumeration: `grep -n "compose(\|bundles_from_args(\|discover_bundles("`
returns `:666`, `:810`, `:912`, `:920`, `:960`, `:972` as the definition and call sites).
So the CLI routes are exactly the branches of `bundles_from_args`, and one further route
exists outside `main` — importing the module and calling `compose()` directly.

**Three routes. Each demonstrated by execution, not only by reading.**

| # | Route | Reached by | N>1? |
|---|---|---|---|
| R1 | repeatable triples → positional pairing | `bundles_from_args` `:922–951`, no `--input-dir` | **yes** |
| R2 | `--input-dir` → shape-classified grouping | `bundles_from_args` `:914–920` → `discover_bundles` `:810–838` | **yes** |
| R3 | library — `import compose_report_data; compose([…])` | `compose` `:666`, bypassing `main` | **yes** |

**R1** — `--cost a --inventory a --orphans a --cost b --inventory b --orphans b`, run from
`cloudcost/`, printed `status= ok  providers= 2  grand_total= 30.0` (exit 0).
**R2** — `--input-dir <dir>` over a directory holding both providers' six files printed
`status= ok  providers= 2  grand_total= 30.0` (exit 0).
**The two CLI routes converge on one payload**: `diff -q` over the two
`report_data_2026-07.json` files reports them identical.
**R3** — `compose([bundle_a, bundle_b], period='2026-07')` returned
`providers= 2  list= ['provider-a', 'provider-b']  grand_total= 30.0`.
Fixtures were two minimal normalized documents per provider, written to the session
scratchpad; `--output-dir` and `--history-dir` were pointed at the scratchpad so the run
wrote nothing under `cloudcost/`.

**R1 and R2 are mutually exclusive**, enforced at `:915–916`: passing both prints
`--input-dir cannot be combined with --cost/--inventory/--orphans` and exits 1 (run, exit
observed = 1). So no invocation uses both, and the union — not either alone — is the surface.

**R3's population, and it is small.** Importers of the module across **population A** — the
204 git-tracked `.py` files in both repos (200 agents, 4 harness; `git ls-files '*.py' | wc -l`
in each) — are exactly two, both tests:

```
cloudcost/tests/test_compose_report_data.py:17:import compose_report_data
cloudcost/tests/test_render_report.py:22:import compose_report_data
```

Harness repo: **zero**. **Positive control**: the same sweep over the same population for
`import _normalized` returns 4 in the agents repo, and the harness's own 4 `.py` files do
contain `import` lines, so the sweep reaches both trees.

**A fourth candidate, examined and rejected — stated rather than left implicit.**
`month_on_month` builds `prior_bundles` from N prior snapshots at `:269–272` and feeds them
through `service_totals` at `:278`, so multi-provider data can enter the delta even when the
current period has one bundle — `load_prior_snapshots` (`:861–877`) globs *every* `*.json`
in one history directory, which is BL-076's subject. **This is not a route by which the
script receives a bundle**: the objects built at `:269` are `{"provider":…, "cost":…}`
two-key dicts synthesised inside the function, never supplied by a caller, and they never
reach `compose`'s `bundles` parameter. It is a distinct N>1 aggregation *inside* the surface,
not an entrance to it. Recorded because "how many bundles can arrive" and "how many providers
can be summed" are different questions and this row sits between them.

**Convergence with the step-1 gate.** The gate, run before this section and from the same
source, found R1 and R2 and said the route set is larger than the one BL-131 names. E1,
derived independently and extended to execution and to the library route, **reproduces that
and adds R3**. Two derivations, same direction; the enumerations differ only in that E1
carries the third route and the demonstrations, which the gate's two questions did not ask
for.

### E2 — Invocation census

**Population, named before searching.** Population B = every git-tracked file in both repos:
**1031** in `aetheris-agents/`, **441** in `../aetheris/` (`git ls-files | wc -l` in each).
The ticket named six surfaces to cover — the orchestrator, the sprint script, the runbook,
`tools.json`, the test suite, and any CI or helper script — and the sweep below is over the
whole population rather than those six, so a seventh surface would have appeared.

**Files mentioning the script.** Agents repo: **40** files
(`git ls-files -z | xargs -0 grep -l 'compose_report_data\.py' | wc -l`).
Harness repo: **0** (`git ls-files -z | xargs -0 grep -l 'compose_report_data' | wc -l`).
**Positive control for that zero**: the same sweep over the same harness population for
`cloudcost` returns **8** files — `CLAUDE.md`, `docs/aetheris/claude-notes.md`,
`docs/aetheris/milestones/handoff-m10b-m11.md`,
`docs/aetheris/milestones/milestone-reference.md`, `docs/aetheris/runbook-m10b.md`,
`docs/methodology/milestone-methodology.md`, `docs/methodology/triad-loop.md`,
`scripts/sprint.sh` — so the sweep reaches the harness tree, and the zero is absence.

Most of the 40 are prose. **The invocations — every place the script is actually executed:**

| # | Site | Form | Bundles it can produce | Route |
|---|---|---|---|---|
| 1 | `cloudcost/agents/cloudcost_orchestrator.exs:258` | `run_command` argv, full triple | **1** | R1 at N=1 |
| 2 | `cloudcost/agents/cloudcost_orchestrator.exs:263` | `run_command` argv, no `--cost` | **1** | R1 at N=1 |
| 3 | `cloudcost/runbook.md` §*The four stages standalone*, `:256–259` | shell recipe, one triple | **1** | R1 at N=1 |
| 4 | `cloudcost/tools.json:453` (`example`) | `--input-dir output/aws …` | **1** as written | R2, one provider's dir |
| 5 | `cloudcost/tests/test_compose_report_data.py` | `cli()` helper `:71`, subprocess | **1 and 2** — see E3 | R1 and R2 |

**`../aetheris/scripts/sprint.sh` invokes the script zero times.** It reaches compose only
through the orchestrator: `:3117–3121` runs `cloudcost_orchestrator.exs`, one provider per
run, selected by `CLOUDCOST_PROVIDER` (`:2646–2648`). **Positive control**: `grep -c
compose_report_data` on that file returns 0 while `grep -c cloudcost_orchestrator` on the
same file returns 7.

**No CI or helper script invokes it.** The 40-file sweep surfaced no such caller, and the
only agent file in the cloudcost use case is the orchestrator itself — population D,
`git ls-files 'cloudcost/agents/*'`, is `.gitkeep` and `cloudcost_orchestrator.exs`.

**So: no in-repo invocation outside the test suite produces N>1.** That part of BL-131 holds
exactly as written, and this is the one of its three verbs that survives unqualified.

**On "nothing advertises" — `tools.json` says otherwise, and it is a declared interface.**
BL-131 notes `--input-dir` is *"declared in `cloudcost/tools.json` (`args[3]`) with a worked
example"*; `args[3]` is `input_dir` and that is accurate. But the three repeatable flags are
`args[0..2]` and each declares the repeatable form in its own `description`, e.g. `--cost`:
*"Normalized cost snapshot. Repeatable on the command line (once per provider, paired
positionally with `--inventory` and `--orphans`); this form supplies one. Cannot be combined
with `--input-dir`"* (`cloudcost/tools.json:393`). `cloudcost/docs/bl-084-implementation-notes.md`
§*`compose_report_data`'s three repeatable flags have no manifest analogue* is the record of
why it reads that way: *"the schema has no repeatable arg. Each is declared single-valued
with the constraint stated in its description"*. **The manifest cannot supply N>1; it does
advertise it.** Those are different, and the row's *"nothing advertises"* does not
distinguish them.

### E3 — Test coverage

**Population.** The 7 git-tracked `test_*.py` files under `cloudcost/tests/`
(`git ls-files 'cloudcost/tests/test_*.py'`): `test_compose_report_data.py` (74 tests),
`test_detect_orphans.py` (61), `test_fetch_aws.py` (63), `test_fetch_do.py` (27),
`test_fetch_linode.py` (63), `test_optimization_signals.py` (34), `test_render_report.py` (62).
The directory also holds `conftest.py`, `aws_wire.py`, two fixture-recorder scripts and 89
JSON fixtures — 100 git-tracked paths in total — none of which define tests.

**The ticket's distinction is the answer, and it separates three tiers, not two.**

**Tier 1 — tests that pass several bundles, library route (R3).** AST-derived, not grep:
a call to `compose(…)` or `compose_report_data.compose(…)` whose first positional argument
is a list literal of ≥ 2 elements. **21 call sites in 2 files** —
`test_compose_report_data.py:180, 241, 276, 299, 334, 514, 522, 537 (×2), 593, 594, 599,
1194, 1203, 1206, 1217, 1221, 1341` and `test_render_report.py:88, 93, 454`, every one with
`bundles=2`.
**This count is a floor, and the AST pass states what it cannot see**: a list literal bound
to a variable before the call is invisible to it. Three such sites were found by reading and
are named here rather than left in the gap — `test_compose_report_data.py:1016` and `:1090`
(`bundles = [do_bundle(), soc_bundle()]`, composed at `:1018` and `:1092`), and `:1336`, a
loop whose second tuple element is `[do_bundle(), soc_bundle()]`, composed at `:1337`.
**24 sites once those are added.**

**Tier 2 — a CLI test at N>1 through `--input-dir` (R2).** Exactly one:
`test_compose_report_data.py:540`,
`test_input_dir_groups_files_into_per_provider_bundles_by_shape_not_by_filename`, which
writes six files for two providers into one directory, invokes the real CLI through
`cli()`, and asserts `summary["counts"]["providers"] == 2` and
`report["providers"] == ["digitalocean", "someothercloud"]` (`:562–564`).
Its sibling at `:568`, `test_input_dir_ignores_a_previously_written_report_data_file`, is
`--input-dir` **at N=1** — the discovery function with one bundle. **That pair is precisely
the distinction the ticket draws, and both members exist.**

**Tier 3 — a CLI test at N>1 through the repeatable triples (R1).** It exists:
`test_compose_report_data.py:666`, `test_each_provider_gets_its_own_history_file`, passes
**two full triples** (`:669–674`) and asserts both providers' history files are written
(`:680–683`). One further multi-flag CLI test is a negative:
`test_the_cli_rejects_mismatched_triple_counts_rather_than_mispairing_them` (`:775`) passes
two `--cost` against one `--inventory` and asserts exit 1.

**Enumeration of the flag literals behind tier 3**, so the count is not taken on trust —
every occurrence of `"--cost"`, `"--inventory"`, `"--orphans"` as a string literal across the
7-file population is at `test_compose_report_data.py:78–80, 669–674, 778–780, 835–837,
916–918`; the only sites with a repeated flag are `:669–674` (two of each) and `:778–779`
(two `--cost`). **Positive control**: the same grep form applied to a file that does repeat
the flag reports the repeat, so a repeated flag would not have been missed.

**All three routes are tested at N>1.** The row's *"nothing … tests … it"* does not hold at
HEAD on any of the three. What is **not** tested at N>1 is the agent surface: no test drives
the orchestrator at more than one provider, and the sprint has no such leg — see E5.

### E4 — Blast radius of REMOVE

Everything that deletes if the multi-bundle surface goes. Enumerated; not adjudicated.

**(1) The declared interface — `cloudcost/tools.json`.** `args[3]` `input_dir` (`:411–418`)
deletes outright. `args[0..2]` `cost` / `inventory` / `orphans` survive as flags but each
`description` loses its repeatability clause (`:393`, `:401`, `:409`). The `example` at
`:453` is `--input-dir`-based and is rewritten entirely.

**(2) Argument parsing and bundle construction — `compose_report_data.py`.**
`action="append"` on the three flags, `:887–895`; the `--input-dir` argument, `:896–900`;
`discover_bundles` entire, `:810–838`; and in `bundles_from_args` the exclusivity check
`:915–916`, the directory check `:918–919`, the equal-count check `:930–937`, and the
`size`/`range(size)` construction `:939–951`.
**`classify` (`:797–807`) does *not* delete** — `load_prior_snapshots` calls it at `:875`.

**(3) Multi-bundle machinery inside the sections.** `compose`'s provider sort `:686` and its
per-bundle warning loop `:689–708`; `service_totals`' `by_provider` accumulation and sort
`:159`, `:205–217`, the `totals_by_currency` map `:219–222` and the multi-currency branch
`:227–238`; `month_on_month`'s `prior_bundles` `:269–272`, the per-provider rows `:310–324`,
`missing` / `providers_without_prior_snapshot` `:326–333` and `:348`, and
`providers_only_in_prior` `:349`; `coverage_section`'s `per_provider` `:366`, `:386–396`,
`:442`; `orphan_section`'s per-candidate `provider` key `:536` and `evaluated_as_of` sort
`:598`; `region_coverage_section`'s per-bundle loop `:644–659`; `persist_history`'s loop
`:852–857`; and in the payload, `providers` `:728`, `accounts` `:729–742`,
`totals.providers` `:753`, echoed in the CLI summary at `:995`.

**(4) Documentation inside the script.** `:2` (*"Merge N providers' …"*), `:24–26`, `:29–37`
(both usage forms), `:885` (parser description), and the N>1 rationale in
`orphan_section`'s docstring `:477`.

**(5) Tests.** The 24 tier-1 sites, the two tier-2 tests (`:540`, `:568`) and the two tier-3
tests (`:666`, `:775`) from E3, plus `test_render_report.py:88`, `:93`, `:454` and the
two-prior-snapshot case at `:283`.

**(6) Documents describing cross-provider behaviour.** Population: the **467** git-tracked
`.md` files plus `cloudcost/tools.json` in this repo. Vocabulary swept: `cross-provider`,
`across all providers`, `N providers`, `N-merge`, `merge-across-clouds`, `N>1`,
`multi-provider`, `per-provider bundles`. **114 matching lines in 24 files**, distributed:
`docs/backlog-2026-06.md` 30 · `cloudcost/m2-milestone.md` 22 · `cloudcost/milestone.md` 13 ·
`cloudcost/m4-consolidation.md` 9 · `cloudcost/m5-n1-compose.md` 8 ·
`cloudcost/docs/m5-scoping-landing-notes.md` 7 · `cloudcost/docs/m4-t4a-implementation-notes.md` 3 ·
`docs/reviews/bl-039-review-packet.md` 2 · `cloudcost/runbook.md` 2 · `cloudcost/m3-milestone.md` 2 ·
`cloudcost/docs/t3-implementation-notes.md` 2 · `cloudcost/docs/m5-pin-edit-implementation-notes.md` 2 ·
and 1 each in `docs/reviews/m2-cloudcost-t3-review.md`, `docs/reviews/m2-cloudcost-closeout.md`,
`docs/milestones/m-eduloka-discovery-summary.md`, `docs/handoffs/handoff-m3-close-2026-08-05.md`,
`docs/handoffs/handoff-cloudcost-rig-batch-close-2026-08-04.md`, `docs/capability-matrix.md`,
`docs/aetheris/backlog/litellm-migration.md`, `cloudcost/tools.json`,
`cloudcost/docs/t1-implementation-notes.md`, `cloudcost/docs/m2-t3-implementation-notes.md`,
`cloudcost/docs/m2-t2-implementation-notes.md`, `cloudcost/docs/bl-084-implementation-notes.md`.

**Two of the 24 are out of scope and were checked rather than assumed.**
`docs/milestones/m-eduloka-discovery-summary.md:14` (*"multi-provider, enrichment-capable,
orchestrated pipeline"*) is the eduloka pipeline, and
`docs/aetheris/backlog/litellm-migration.md:19` (*"No cross-provider spend tracking"*) is
about LLM providers. Neither concerns this surface.

**Of the remaining 22, the live descriptions — documents stating current behaviour, as
distinct from backlog rows, milestone histories, review records and handoffs, which describe
what was decided when and would be falsified rather than corrected by deletion:**

- `docs/capability-matrix.md:209` — *"Merge N providers' cost, inventory, and orphan
  artifacts into a single report payload …"* — the generated matrix cell. **Outside
  `cloudcost/`**, and regenerated per-section (`scripts/assemble_matrix.py`), so it changes
  by regeneration rather than by hand.
- `cloudcost/tools.json:417` — *"Group every normalized artifact in this directory into
  per-provider bundles."*
- `cloudcost/runbook.md:10` — *"There is no cross-provider run and no combined …"* —
  already states the N=1 operational position, so it is consistent with removal and would
  need no change.
- `cloudcost/runbook.md:623` — *"**BL-070**, which retires the now-unreachable cross-provider
  merge code in `compose_report_data.py`."* **This asserts unreachability as current**, which
  is one of the three readings E6 tabulates; it is a live document carrying a disputed
  premise either way the ruling goes.
- `cloudcost/milestone.md` §Contracts **C4** (the one-currency-scalar paragraph) and **C11**
  (the caps paragraph), both already carrying m4 t5b pointer blocks — these are the two the
  ticket's own §Scope says change whichever way the ruling goes.
- `cloudcost/milestone.md` §Open items carried forward, the cross-currency bullet — quoted
  in full in E6.

### E5 — Blast radius of SUPPORT

A census of **absences** — what must be *added* for the surface to be supported rather than
merely present. Each carries its own positive control.

**(a) A sprint leg exercising N>1 — absent.** `grep -c compose_report_data
../aetheris/scripts/sprint.sh` returns **0**, and the cloudcost legs run the orchestrator
once per provider (`:3117–3121`), selected by `CLOUDCOST_PROVIDER` (`:2646–2648`), so no
sprint path composes two providers into one report. **Positive control**: `grep -c
cloudcost_orchestrator` on the same file returns **7**.

**(b) A runbook recipe for N>1 — absent.** `grep -n -- "--input-dir" cloudcost/runbook.md`
returns **0 occurrences**; the only compose recipe is the single-triple one at `:256–259`.
**Positive control**: `grep -c -- "--history-dir"` on the same file returns **1**, so the
grep form finds a flag in that file when one is present. An operator reading the runbook has
no N>1 instruction of either route.

**(c) A manifest form that can *supply* more than one — absent.** The repeatability is
stated in prose in three `description` fields (E2), but `cloudcost/tools.json` has no
repeatable arg type, so the Rig-facing surface can supply exactly one of each and one
`--input-dir`. **Positive control**: the manifest does express the other constraints it
needs — `required`, `default`, and `type` are populated on all eight args of this entry
(the `args` array spans `cloudcost/tools.json:386–451`) — so the absence is of a repeatable
*kind*, not of declaration effort.

**(d) An N>1 test above the script level — absent.** Every N>1 test enumerated in E3 drives
the library or the CLI. No test drives `cloudcost_orchestrator.exs` at more than one
provider. **Positive control**: the sprint *does* assert on the orchestrator — it evaluates
the agent file (`../aetheris/scripts/sprint.sh:2922–2927`) and asserts exactly one report is
produced (`:3138–3151`) — so an orchestrator-level assertion is an expressible thing that is
simply not written for N>1.

**(e) Semantics C4 and C11 would then have to state — absent as *settled* text.** Both
paragraphs already describe the cross-provider behaviour; what does not exist is the
resolution each marks as owed. C4 §*Money and currency* carries *"The minor-unit exponent
belongs in the cost snapshot beside `currency`, and `money()` should take it. **[code
consequence]**"* and *"The reconcile tolerance is currency-relative, or stated per currency"*
— both unimplemented; the multi-currency path is exactly where they bite, because at one
currency the questions do not arise. C11 §*Optionality and presentation* states the cap is
applied *"after a global sort across all providers"* and that *"one provider can be absent
from the table entirely"*; supporting N>1 means deciding whether that is the intended
presentation or whether the cap becomes per-provider. **Positive control that these are
unimplemented rather than merely undiscussed**: `money()` is
`def money(value) -> float` — one parameter, no exponent (`cloudcost/scripts/_normalized.py:89`,
imported at `compose_report_data.py:48–57`), and `RECONCILE_TOLERANCE` is a single module
constant, `0.01`, at `compose_report_data.py:99`, with no currency dimension.

**Not an absence, recorded so it is not re-counted as one.** N>1 tests, an N>1 CLI, and a
manifest declaration of the repeatable form all exist (E2, E3). The absences above are
narrower than "the surface is untested and unadvertised".

### E6 — The three-state contradiction

BL-131 §*The three states, and each is asserted somewhere* tabulates three assertions. Each
is located at HEAD, quoted, and read. **Nothing here is adjudicated.**

**State 1 — "dead", attributed to BL-070.** `docs/backlog-2026-06.md` §BL-070 opens:
*"m2 adopted per-provider reporting (decision H, no cross-provider roll-up), which makes the
N-merge, the `providers_without_prior_snapshot` caveat, the multi-currency "No combined
total" path, and the cross-currency 4-site aggregation all **unreachable**."*
**Reading: present, and withdrawn as a premise by the row itself.** The same row's
§*Why the premise is under question — three states, not two* says *"Dead, source-only, and
live are three different things and **this row assumed the first**. BL-131 decides which it
is."*, and its **Done when** clause carries `[deferred 2026-08-07 — see the amendment note]`
against the deletions. So the sentence stands, and the row no longer asserts it as settled.
**HEAD supports the sentence as a description of what BL-070 once assumed; it does not
support it as BL-070's current position.**

**State 2 — "live at the first fan-out", attributed to `cloudcost/milestone.md` §Open
items.** **It resolves at HEAD**, in §Open items carried forward (not this milestone), in
the bullet *"Cross-currency aggregation is handled in one place and unhandled in four —
`compose_report_data.py`"*, which ends: *"**Latent while m1 is DO-only single-currency; live
at the first fan-out.** t4 mitigates on the render side only …"*.
*(A line-scoped grep for the quoted string fails, because the phrase wraps a line break
between "first" and "fan-out"; `grep -Pzo` over the file matches it. Recorded because the
failing grep is the kind of evidence that would otherwise read as absence.)*
**Reading: HEAD supports it, with a scope note.** The bullet's subject is the four
**cross-currency aggregation sites**, not the N-merge as such; BL-131's table reads it as an
assertion about this surface. The two are connected — the cross-currency sites are reachable
only at N>1 — but the sentence is about currency handling, and that is stated here rather
than resolved.

**State 3 — "advertised but uninvoked", established at m4 t5b.** **It exists as no committed
implementation-notes text**; the enumeration and positive control are in the step-1 gate's
§Bearing on §Not established item 2 above. Its in-repo carriers at HEAD are three, all of
which restate it rather than record its derivation: BL-131's own §*The reachability
derivation*; BL-070's §*Why the premise is under question*, *"the `--input-dir` route that
reaches them is **declared in `cloudcost/tools.json` with a worked example**, so it is an
advertised interface that the orchestrator simply never invokes"*; and `cloudcost/milestone.md`
§C4's pointer block, *"the cross-provider compose path is reachable only through a CLI flag
the orchestrator never passes"*. **Reading: HEAD supports "uninvoked" (E2) and does not
support "reachable only through a CLI flag the orchestrator never passes" (E1).**

**A fourth item, per the reviewer's guard (b) — marked as the row's own description, not one
of the three tabulated states.** BL-131 §*The reachability derivation* states *"the N>1 path
is reachable only through `--input-dir` → `discover_bundles`"*. **HEAD does not support it**:
three routes exist (E1), two of them CLI, and the two CLI routes produce an identical payload.
The same sentence has propagated into `cloudcost/milestone.md` §C4's pointer block in the
form quoted above, so the description now sits in a contract as well as in the row.
**Adjudicated nothing; four quotations, four readings.**

### E7 — Decision H's re-derivability clause

**The clause, verbatim.** `cloudcost/m2-milestone.md` §H — *Per-provider reporting; no
cross-provider roll-up (ratified 2026-07-30, rev 3)*:

> Consolidation is not foreclosed: each provider persists a **normalized** cost snapshot to
> `history/{provider}/{period}/`, so a cross-provider total is later re-derivable by a thin
> read-only aggregator — a separate optional read-layer, never coupled to the pipeline.

**Is that path written today? Yes — by `persist_history`, on every orchestrator run.**

*By which code.* `persist_history` (`cloudcost/scripts/compose_report_data.py:841–858`)
writes, per bundle carrying a cost document, to
`history_dir / period / f"{provider_slug(bundle['provider'])}_costs_{period}.json"` (`:856`),
and the document written is the provider's cost snapshot verbatim — `write_json(path, cost)`
(`:857`), where `cost` is the normalized snapshot the adapter emitted. It is idempotent by
`(provider, period)` because both are in the filename, and it is guarded by
`prior_period(period) is None` (`:848–851`) so a non-calendar period writes nothing.
**Demonstrated rather than read off a listing**: calling `persist_history` with two bundles
and `history_dir = …/history/provider-x`, period `2026-07`, returned
`history/provider-x/2026-07/provider-a_costs_2026-07.json` and
`…/provider-b_costs_2026-07.json`.

*On which invocation.* The orchestrator sets `history_dir = "history/#{provider_slug}"`
(`cloudcost/agents/cloudcost_orchestrator.exs:122`) and passes it as `--history-dir` on both
STEP 3 forms (`:258`, `:263`). Composing that with `persist_history`'s own
`{history_dir}/{period}/` gives **`history/{provider}/{period}/`** — H's layout exactly. The
runbook's standalone recipe passes `--history-dir history/digitalocean` (`cloudcost/runbook.md:259`),
same shape. Left unset, the default is the shared `cloudcost/history` (`:95`), which is the
BL-076 condition H's per-provider layout exists to avoid.

*What is on disk.* Four snapshots across three providers, each self-declaring a provider and
period that match its own path: `cloudcost/history/aws/2026-08/aws_costs_2026-08.json`
(`provider='aws' period='2026-08'`), `…/digitalocean/2026-07/…` (`'digitalocean'`,
`'2026-07'`), `…/digitalocean/2026-08/…`, `…/linode/2026-07/…`. **Bound to the code that
writes that layout, not to the tree listing.** Which *run* wrote each file is **not
established** — the tree is gitignored (`cloudcost/.gitignore:10`, `history/*`), the files
carry no run id, and a listing cannot say. **What would settle it**: the run record for each
period (`mix aetheris inspect <run_id>` / the run's trajectory), matched on the
`generated_at` each snapshot carries.

**The aggregator H names does not exist.** Population: the 8 git-tracked `.py` files under
`cloudcost/scripts/`. The only readers of a history tree are `load_prior_snapshots`
(`:861–877`), which reads **one** `history_dir` and only the **prior** period, and
`persist_history`, which writes. Nothing reads across providers. **Positive control**: the
same sweep locates `load_prior_snapshots` at `:861`, so it reaches.

**Bearing, stated without ruling.** H's precondition — normalized per-provider snapshots
persisted in the layout it names — **is satisfied today, by the live pipeline, for all three
providers**. H's consequent — the thin read-only aggregator — **is not built**. So what
*removed* would foreclose turns on whether the aggregator is read as depending on the
N-merge; H's own text places it outside the pipeline (*"never coupled to the pipeline"*), and
the snapshots it would read are written by `persist_history`, which E4(3) lists as
multi-bundle machinery only in its *loop*, not in its output layout. **The evidence is
published; the reading is the reviewer's.**

### E8 — Reachability of C4's and C11's stated behaviour

Two known instances only. **The check is not extended to C1–C15** — that is BL-132's row,
and BL-132 §*Collides with* says *"Take BL-131 first"*. Entry point is the orchestrator, per
BL-132's stated method.

**C4 — `cloudcost/milestone.md` §*C4 — Money and currency*: source-only (and tested).**

The clause at issue: *"When bundles disagree on currency, the grand total is withheld and
per-currency figures are reported instead — correct, and m1's stated position … **adding a
single non-USD provider blanks the report's headline number for every provider**, because
the scalar total becomes null and renders as an em dash."*

*Basis, demonstrated.* At one bundle — the orchestrator's N — `compose([a])` returned
`grand_total= 10.0  currency= USD` and **no** multi-currency warning. At two bundles with
disagreeing currencies, `compose([a, b_eur])` returned `grand_total= None`,
`totals_by_currency= {'EUR': 20.0, 'USD': 10.0}` and the warning *"bundles report more than
one currency (EUR, USD); no conversion is done at m1 …"*. The branch is
`compose_report_data.py:227–238`. **Since no in-repo invocation produces N>1 (E2), the
described behaviour cannot arise from the live pipeline: source-only.**

*A precision the label alone loses.* The `else` arm at `:230` **is** reachable at N=1 — with
no usable cost document `totals_by_currency` is empty, so `currency` and `grand_total` are
`None` and the headline blanks — but the *warning* at `:232–238` is guarded by
`if totals_by_currency:` and needs ≥ 2 currencies. So the em dash is reachable; *the em dash
for the reason C4 gives* is not.

*Source-only is not untested.* `test_render_report.py:93` composes
`[do_bundle(), soc_bundle(currency="EUR")]`, so the path has library-route coverage.

**C11 — `cloudcost/milestone.md` §*C11 — Optionality and presentation*: reachable in its
guarantee, source-only in its cross-provider clause.**

The clause at issue: *"The untagged-spenders table is capped **after a global sort across all
providers**, so one provider can be absent from the table entirely while another fills every
row — and nothing reports it."*

*Basis, demonstrated.* At one bundle with `top_untagged=2` over four untagged resources, the
table held one provider and `untagged_not_shown = 2` — **the cap and its truncation report
are reachable at N=1**. At two bundles where one provider outspends the other on every
resource, with the same cap, the table held only `provider-a`, `untagged_not_shown = 6`, and
`provider-b` was **absent from the table entirely** — the described condition, and it needed
N=2. Code: the global sort at `:397–403`, the cap at `:405–419`, `untagged_not_shown` at
`:449`.

*So the contract splits.* Its **Shared machinery guarantees** clause and the m4 t5b pointer's
*"the cap reports its truncation at any N"* are **reachable**. Its P2 clause — *"across all
providers … one provider can be absent from the table entirely"* — is **source-only**, for
the same reason as C4. The contract's own pointer block already says as much: *"describes the
**cross-provider** path BL-131 decides the support of. **Not false, not yet amendable**"*.

*Also tested.* `test_compose_report_data.py:1203`, `:1206`, `:1217`, `:1221` exercise the cap
at two bundles.

**Summary, and the distinction it turns on.** Both contracts are **source-only** in the
clauses that describe cross-provider behaviour, and **both are tested** — through the library
route, which is not the orchestrator. **Source-only and untested are different properties
here, and this surface has the first without the second.**

---

## Deviations

**None.** Two paths changed in this ticket, both in `Touches`:
`cloudcost/docs/m5-t1-implementation-notes.md` (new) and the **t1 row only** in
`cloudcost/m5-n1-compose.md` §Ticket set, per **R19**. `git status --short` was clean before
the work and shows only those two paths after it.

All execution was run with `--output-dir` and `--history-dir` pointed at the session
scratchpad, so no demonstration wrote under `cloudcost/`.

## Done-check

Run from the `aetheris-agents/` root. Item 1's two anchors were re-resolved at HEAD before
running, per the ticket; **neither has moved**.

- **Anchor 1**, `cloudcost/runbook.md` §Offline tests — present, and its block is
  `python3 -m pytest cloudcost/tests/ -v`, commented *"no credentials; recorded DO + AWS +
  Linode fixtures"*. Matches the pin.
- **Anchor 2**, `CLAUDE.md` §Commands — present, and its block opens
  `# From the aetheris-agents/ root`. Matches the pin's working-directory clause.

1. `python3 -m pytest cloudcost/tests/ -v` → **386 passed in 145.23s, exit 0**; 0 FAILED,
   0 ERROR, 0 SKIPPED. 395 lines captured.
2. `test -s cloudcost/docs/m5-t1-implementation-notes.md` → `NOTES_PRESENT`.
3. `grep -c '^### E[1-8] ' …` → **8**.
4. `git status --short` → the two `Touches` paths only.

**A substitution, reported as one.** Item 4 cannot observe whether the test run wrote into
`cloudcost/output/` or `cloudcost/history/`: both are gitignored
(`cloudcost/.gitignore:6` `output/*`, `:10` `history/*`), so `git status` returns clean
whether or not an artifact appeared. A `find -printf '%T@ %s %p'` snapshot of both trees was
taken before and after the run — 25 files — and compared: **identical**, no mtime or size
change. The substitution is named here rather than left to read as an item-4 pass.
