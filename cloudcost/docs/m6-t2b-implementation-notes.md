# m6 t2b — wire the GitHub adapter into the pipeline

`Measured at agents HEAD 0303597 and harness HEAD 66a9ca5 unless a line says otherwise. Every
file:line citation below was read at those commits; the two commits this ticket lands are named
in §9.`

Provider four becomes selectable. t2 shipped `fetch_github.py`; nothing chose it. After this
ticket `CLOUDCOST_PROVIDER=github` runs the four-stage pipeline end to end, the sprint exercises
it, and a GitHub report is produced carrying `seat` resources.

Two commits, agents first. The harness's `MODULES` map and credential preflight are one-way
pointers at an agents module, and a one-way pointer lands after its target.

---

## 1. The gate, and the one thing in it that was not as described

Six items. Five held; one did not, and it was the one the ticket expected to stop on.

**(vi) — the stop point's premise was false.** The ticket anticipated an arm going *permanently
red* on GitHub's shadow names and asked for a reading before any harness code was written. The
arm (`../aetheris/scripts/sprint.sh:2824–2832`) **warns**. `warn()` is `sprint.sh:43`, a bare
printer: it touches none of the exit contract's four counters. Only `fail()` increments
`NOT_DECLARED` (`:76–79`) and only `blocking_fail()` increments `FAILURES`, which alone drives the
exit code (`:82–86`). So the github leg goes permanently **amber**, non-blocking and uncounted —
which `runbook.md:192–195` already declares intended for this adapter: *"On a workstation with
`gh` configured this warning is routine rather than exceptional."*

Ruled: proceed unchanged. The arm is not touched, not reclassified, and GitHub is not
special-cased. §2 records the reading so the next round does not pay for it again.

**(iv) — the companion-artifact gate found a red at HEAD.** See §3.

**(iii) — both recorded defects hold, and one of the reviewer's figures does not.** The prose
said *five places*; the enumeration has five semicolon-separated groups but names **seven**
distinct edit sites, not six — group 1 carries two (provider `case` + credential raise) and group
4 carries two (preflight `case` + `MODULES` map). The disagreement the defect asserts is real; the
count attached to it was not. De-numeralisation (§5) moots the figure either way, which is the
argument for de-numeralising rather than correcting.

**(v)** — `R1`…`R25` contiguous in `docs/milestones/hc-consolidation.md` §Ratified decisions, each
a `### Rn — …` heading; highest `BL-150`. This ticket takes **R26** and **BL-151**.

---

## 2. The hazard arm is not a stop point — recorded so the next round does not re-raise it

`sprint.sh`'s ambient shadow/redirect arm **warns and does not fail**. `warn()` (`sprint.sh:43`)
is a bare printer; the exit contract's four counters (`FAILURES`, `NOT_DECLARED`,
`BLOCKING_ARMS`, `KNOWN_RED_ARMS`, `:68–71`) are untouched by it.

**Therefore an ambient shadow name on the github leg is not a stop point, and a later session
should not re-raise it as one.** The reviewer raised it as a likely stop because the arm's
*severity* was unread; the gate resolved it in one reading. This paragraph is what stops the next
round paying for the same resolution — and there will be a next round: **Google Workspace and the
AI providers are the same consumption class and will meet the same ambient-credential situation**,
because the ambient names are put there by tooling the operator legitimately runs.

**What would be a stop point here**, stated rather than implied: the arm becoming blocking, or an
ambient name appearing that the adapter's own lists do not refuse. Neither holds today — the arm
is `warn`, and `SHADOWING_ENV` + `ENDPOINT_REDIRECT_ENV` name all seven of the variables `gh` and
`@actions/github` read.

**The cost the design accepts, stated as accepted rather than discovered later:** an arm amber on
every run of a provider trains an operator to read past it. The mitigation is already in place —
the arm prints *the names it found*, so a **new** hazard name changes the line's text rather than
only its colour, and a reader who has learned to skip the colour still sees a different line. That
is why the current form is adequate. Recorded as accepted cost, not as a defect; it opens no work.

Observed on this workstation, github leg, seven names checked:

```
[WARN]  ambient credential-shadow/redirect names set: GITHUB_TOKEN GITHUB_PERSONAL_ACCESS_TOKEN — the prefix strips them so this run is unaffected, but your shell still carries them (names only; no values read)
```

---

## 3. The red this ticket inherited, and closed

`python3 -m pytest tests/test_tools_manifests.py` was **red at HEAD**, on two arms:

```
FAILED tests/test_tools_manifests.py::test_discovery_sweep_intact
  assert len(_flat_cli_scripts("cloudcost")) == 7      # 8 on disk since t2
FAILED tests/test_tools_manifests.py::test_no_undeclared_scripts[cloudcost]
  AssertionError: cloudcost: undeclared runnable CLI(s) ['scripts/fetch_github.py']
2 failed, 22 passed, 7 xfailed
```

t2 (`0303597`) landed `scripts/fetch_github.py` without its `tools.json` companion. The gate's
standing companion-artifact item is what surfaced it — the ticket's own warning that *"this list
has been one file short twice"* was correct a third time, and the missing file was already in
Touches (W2/W3), so closing it needed no widening.

**Both arms are green after W2 + W3** (`24 passed, 7 xfailed`).

Worth noting *which* arm caught it: `test_no_undeclared_scripts` is the offline proxy for Rig's
amber badge, and it fired because Rig would have badged `fetch_github.py` amber with a raw-args
box. The count assertion fired for the reason it was written to fire — that a new CLI and its
manifest entry land together. It did not prevent the divergence; it recorded it, one ticket late.

---

## 4. W1 — the orchestrator arm

`cloudcost/agents/cloudcost_orchestrator.exs`. The case tuple is
`{provider_name, provider_short, provider_slug, fetch_script}`:

| Position | Meaning | GitHub |
|---|---|---|
| `provider_name` | display name in prose — the prompt's *"Run the … cost-report pipeline"*, and the run label | `"GitHub"` |
| `provider_short` | the short label STEP 1's heading uses (*"Fetch the … cost snapshot"*) | `"GitHub"` |
| `provider_slug` | filesystem/URL token — `output/{slug}`, `history/{slug}`, and the run id | `"github"` |
| `fetch_script` | the adapter path STEP 1 execs | `"scripts/fetch_github.py"` |

The positions are not self-evident from the DigitalOcean arm, which is the only one where all
three spellings genuinely differ (`"DigitalOcean", "DO", "digitalocean"`) — AWS's are all `"AWS"`
and Linode's differ only in case. GitHub's differ only in case too, so this arm does not
re-establish the distinction; the table above is here because reading the arms alone would not
have.

The credential raise follows Linode's form and Linode's ground: GitHub is never the default and
can only be reached by naming it, so the *"must stay clean on a machine with no credential"*
argument that exempts DO does not apply. Empty string is treated as absent, matching both
predecessors. The message names the five shadow variables it refuses — names only, never a value
(D2).

Verified across every arm, eval only, no LLM call:

```
<unset>        eval OK
digitalocean   eval OK
linode         raised: ** (RuntimeError) CLOUDCOST_PROVIDER=linode requires CLOUDCOST_LINODE_TOKEN to be set. …
github         eval OK
nosuchcloud    raised: ** (RuntimeError) CLOUDCOST_PROVIDER must be "digitalocean", "aws", "linode" or "github", got: "nosuchcloud"

env -u CLOUDCOST_GITHUB_TOKEN CLOUDCOST_PROVIDER=github
  ** (RuntimeError) CLOUDCOST_PROVIDER=github requires CLOUDCOST_GITHUB_TOKEN to be set. …
```

The unset and `digitalocean` rows are the positive control: the raises above are the guards
firing, not the file being broken.

---

## 5. W2 — `tools.json`, and the *kind* the schema does not have

**The cost of an undeclared env row**, per the runbook and `tools.rs`: an undeclared runnable CLI
is synthesised as `undeclared: true` (`tools.rs:560–575`) and badged amber with a raw-args box
(`ToolTree.tsx:71–73`); and `env` rows are the source of Rig's dynamic agent-config rows
(`tools.rs:594–604` → `AgentConfigTab.tsx`), so an undeclared variable costs the config surface
too. Worse, `EnvDep` carries no `#[serde(default)]` on any of its five fields — **one missing key
drops the entire manifest**, silently, because `tools.rs:526` is `from_str(&raw).ok()`. A
malformed manifest and an absent one are indistinguishable in the UI.

**How the existing entries distinguish the adapter's three classes: they do not.** `EnvDep`'s
five fields are `key/label/group/masked/placeholder`. There is no *kind* axis, and no adapter
declares a hazard name at all:

| Adapter | rows | which |
|---|---|---|
| `fetch_do` | 1 | cred |
| `fetch_aws` | 5 | 3 cred + 2 knob |
| `fetch_linode` | 1 | cred |

The only distinguishers in practice are `masked` and the label prose. So the ticket's *"declared
as its own kind"* is not expressible in this schema, and the clause was **struck** by ruling
rather than satisfied some other way.

**GitHub declares the credential and the org, and not the seven hazard names.** The ground is not
precedent: a Rig config row is an **invitation to set the variable**, and `GH_TOKEN`,
`GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`,
`GITHUB_PERSONAL_ACCESS_TOKEN`, `GH_HOST` and `GITHUB_API_URL` are names this adapter exists to
**refuse**. Declaring them would build a UI affordance for exactly the action the credential
convention prevents. The next provider in this class will ask the same question and this paragraph
is the answer.

They are still *named* in the manifest — in the `api_base` arg's description, as prose explaining
what the base URL is never taken from. That is the same treatment `fetch_linode`'s entry gives
`LINODE_CLI_API_HOST/_VERSION/_SCHEME`: documentation, not a config row.

**Is the two-surface split itself a defect?** Probably not. `tools.json` answers *what an operator
may configure*; the adapter's own constants answer *what it reads and refuses*; and `sprint.sh`
already reads the second directly rather than the first. Hazards belonging to only one of those
surfaces is coherent design. What *is* a defect is narrower, and §6 has it.

---

## 6. The knob that never reached the adapter

`fetch_github.ORG_ENV = "CLOUDCOST_GITHUB_ORG"` is a **documented operator knob**
(`runbook.md:175–178`, *optional*). The sprint's adapter env bridge selects knobs by a list of
constant **names**, `KNOB_CONSTANTS = ("REGION_ENV", "REGIONS_ENV")` (`sprint.sh:2784`).
`ORG_ENV` is on none of the three tuples, so under the m4 t3 default-deny inversion it was
**stripped**, and the adapter fell through to `/user/orgs` sole-membership discovery.

That is verbatim the failure the `knob` category was created to prevent — `sprint.sh:2760–2764`:
*"the inversion would otherwise SILENTLY disable a documented feature"* — and it is BL-113's
recorded shape (*the map is keyed on constant names, so an adapter adding a credential under a new
constant is still missed silently*).

**It is not degraded operation.** If the knob is stripped, discovery runs; if discovery resolves
to a single organisation that is **not** the one the operator configured, the run bills the wrong
organisation and nothing downstream can tell. Silent wrong answer, not a missing feature.

**Why it has been silent here.** `CLOUDCOST_GITHUB_ORG` is not set on this workstation, and
`GET /user/orgs` with this token returns **exactly one** organisation. Sole-membership discovery
is therefore *accidentally correct today*, which is precisely why a stripped knob produced no
observable symptom. Add a second membership to the token, or set the knob to any login but that
one, and the strip starts billing the wrong org.

**Fixed in the harness commit** (`KNOB_CONSTANTS` gains `"ORG_ENV"`), not filed. The
code-findings row is for defects with **no natural home**; this one had a natural home in the
commit already editing that file, in the ticket whose subject is declaring this adapter's env
surface. Filing something fixable in the commit that found it is the deferral the standing rule
exists to discourage — and seeding a brand-new row with an item that should have been fixed would
have taught the row the wrong purpose on its first day.

### The adjacent-case sweep — run, and clean

If GitHub's knob was missed, another might be. Every module-level environment constant across all
four adapters, checked against `KNOB_CONSTANTS`:

| Adapter | cred | knob | hazard | unclassified |
|---|---|---|---|---|
| `fetch_do` | `TOKEN_ENV` | — | `SHADOWING_ENV` (2) | none |
| `fetch_aws` | `ACCESS_KEY_ENV`, `SECRET_KEY_ENV`, `SESSION_TOKEN_ENV` | `REGION_ENV`, `REGIONS_ENV` | `SHADOWING_ENV` (4) | none |
| `fetch_linode` | `TOKEN_ENV` | — | `SHADOWING_ENV` (2), `ENDPOINT_REDIRECT_ENV` (3) | none |
| `fetch_github` | `TOKEN_ENV` | — | `SHADOWING_ENV` (5), `ENDPOINT_REDIRECT_ENV` (2) | **`ORG_ENV`** |

**`ORG_ENV` is the only unclassified environment constant in the use case.** Reported in full
including the clean rows, because a clean sweep is a finding too — three adapters were checked and
found correct, which is what makes the fourth's gap a gap rather than a pattern.

One thing the sweep surfaced that is *not* a finding: `CURRENCY` matched the sweep's
name-and-value shape on all four adapters and is **not** an environment variable — it is D1's
adapter-declared constant, value `"USD"`. Named here so the clean result is not read as the sweep
having missed something.

Nothing falls outside Touches, so no code-findings entry arises from the sweep itself.

---

## 7. W4/W5 — the wiring list, repaired by the ticket that followed it

**W4a — the path.** `tests/test_tools_manifests.py` does not resolve from the runbook's own
directory; `cloudcost/tests/` holds no such file. Corrected to `../tests/test_tools_manifests.py`
with an explicit gloss (*the repo root `tests/`, not `cloudcost/tests/`*), because the `../` alone
is the kind of thing a reader skims past.

**W4b — the count, de-numeralised rather than corrected.** The list enumerates the places, so a
number in the prose is a second surface that can drift from it — m6 t1's rule, applied. Correcting
*five* to *seven* would have re-armed the same trap for provider five.

**W4c — two additions, reported separately from the repairs.** Following the list revealed places
it does not name:

1. **`KNOB_CONSTANTS`** in the adapter env bridge — the substantive one. §Adding a provider named
   the preflight `case` and the `MODULES` map in `sprint.sh` but not the knob declaration, which
   is why §6 happened. A one-word fix that left the list still missing the entry would have made
   provider five pay again.
2. **Every prose enumeration of the provider set** — this file's opening sentence,
   `tools.json`'s top-level `description`, the orchestrator's header comment, and `sprint.sh`'s
   usage headers. One clause rather than four bullets.

**W5 — the provider list, and the unwired clause.** The opening sentence gains GitHub. t2's
*"GitHub is not wired into the pipeline yet"* clause was quoted at HEAD and **replaced as a unit**
rather than line-edited; its replacement states what is now true and adds the t3 boundary (no rule
keys on `seat` yet, so a GitHub run reports zero orphan candidates, and that is the catalog
reading the inventory correctly rather than failing to).

**Three further runbook edits, inside units this ticket was already editing**, reported because
they widen the diff past the four sites W4c enumerates:

- §Run it gains a **GitHub** invocation block, because W5's replacement clause points the reader
  at §Run it and that pointer would otherwise be false.
- The sprint-cases fence listed **DigitalOcean and AWS only** — Linode has been selectable since
  m3 and was never added. Both `linode` and `github` lines added. That is a pre-existing
  incompleteness in a unit this ticket edits, not a defect this ticket introduced.
- The allowlist table's knob row gains `CLOUDCOST_GITHUB_ORG`, and the *"add it to `CC_ALLOW`"*
  advice below it is corrected: for a knob, the right lever is the adapter constant plus
  `KNOB_CONSTANTS`, and hand-adding to `CC_ALLOW` re-introduces the hand-typed copy the selection
  exists to avoid.

**One ordering consequence, stated rather than left to be noticed.** The allowlist-table edit
describes behaviour that does not exist until the harness commit lands, so between commit 1 and
commit 2 the runbook is one commit ahead of the harness. The alternative — deferring the doc edit
to a third commit — would have left the table wrong at the end of commit 1 in the other direction,
and this ticket lands both commits before its packet.

---

## 8. W6/W7 — the close-criteria clause, R26, and BL-151

**W6.** §Close criteria quoted at HEAD and replaced as a unit; one clause, in the existing *verify
and record* register — **what the milestone recovered, with its basis**, not that any figure was
achieved. A recorded zero with its basis satisfies it. Ground carried in a dated bracket per R25's
form.

**W7a — R26**, at the next free number, one `###` heading, one clause of ground, a dated stamp
naming R22 as its authority. It states the separateness argument because that is the part a later
reader would otherwise re-litigate: **a documentation-system finding closes on a decision about
the system; a code finding closes by being fixed. One row cannot state both discharge
conditions** — widening BL-150 would have given half its contents a `Done when:` that does not
apply to them.

**W7b — BL-151**, in BL-150's shape: `Kind: standing`, `Census items: n/a`, `Contract: … R26`,
`Size: n/a — does not close on any single item`, the append-only paragraph, an `**Appended.**`
block, and a `Source:` stamp. Its `Done when:` is **its own**: not the list emptying, but a
decision about how these are swept and what retires one — whether an item is retired individually
when fixed or only struck when the row is disposed, whether a sweep runs at a close or on a
cadence, and who decides an item is too small to keep.

It also carries a **guard against its own misuse**, because the first thing this row could do is
absorb work that should be done: *a finding with a natural home does not come here*. §6 is the
worked example, named in the row.

**W7c — three seeded entries**, all re-verified at HEAD before writing, because a seeded entry
that is already false is worse than an empty row:

1. `fetch_aws.py:391`'s private `money()` duplicating `_normalized.money` (`:92–97`) — same
   `round(float(value), 2)`, same `(TypeError, ValueError) → 0.0` — while the module **does**
   import from `_normalized` (`:41–50`, eight `TYPE_*`/`STATE_*` names) without taking `money`.
   C4's *coerced through one function* guarantee has two implementations. **Holds.**
2. `cloudcost/tests/conftest.py:724`'s unreachable `return aws_stub`, after `full_linode_stub`'s
   own `return linode_stub` at `:723`. **Holds.**
3. *(added by ruling)* A knob must be declared in **two unlinked places** — a `tools.json` `env`
   row and `sprint.sh`'s `KNOB_CONSTANTS` — with nothing checking they agree. The instance was
   found and **fixed** here (§6); what is filed is the absence of a check. **The absence was
   verified at HEAD**, and this is the part worth stating because an entry asserting an absence
   that turns out to exist would be worse than no entry: `tests/test_tools_manifests.py` is the
   only reader of `cloudcost/tools.json` in either repo and never mentions `sprint.sh` or
   `KNOB_CONSTANTS`; `sprint.sh` reads the adapter modules directly (`:2772–2801`) and never opens
   `tools.json`; `drift_check.py`'s check 4 (`env_vars`) compares Rust `env::var()` calls against
   `docs/rig/specs.md` §1 and `runbook.md`, touching neither surface. No check is proposed.

**W7d — the exclusion, recorded as a decision.** `fetch_linode.py`'s round-before-multiply is
**not** seeded. Its `PriceTable` rounds the unit rate at ingest (`:396`, `:402`) and multiplies at
`:763` (`money(rate * (size_gb or 0))`), so the rate is rounded before the multiply — the shape D4
rules on. It is already dispositioned as `m6-github.md` **D4's recorded counter-example**, and a
second record of the same finding is the two-surfaces defect **BL-145** ruled on. Recorded in the
row itself, not only here, so the omission reads as a decision from wherever it is next read.

---

## 9. Done-check

Two stages, because the wiring is not complete until both commits land. Both stages' full output
is in the review packet.

**A pre-existing red found off-territory**, named here per the standing rule and not carried
silently: `python3 -m pytest -q` at the repo root — the literal stage-1 command — **fails
collection at HEAD**, on two modules this ticket does not touch:

```
ERROR boxy-pipeline/tests/test_pipeline.py          ModuleNotFoundError: No module named 'main'
ERROR provenance/mcp/corpus-search/tests/test_server.py   ModuleNotFoundError: No module named 'tests.test_server'
```

Reproduced with this ticket's changes stashed, so it is inherited rather than introduced. This is
a rootdir / `sys.path` collection defect, not broken product code — and the two named modules are
its visible edge rather than its extent: `cloudcost/tests/` collects 440 alone and `tests/`
collects 136 alone, but **the two together** collect 136 with 8 errors and abort. No single
invocation covers even two scopes at once, which is why *"run the whole suite"* has been satisfied
by scoped runs whose numbers no root command reproduces. Tracked as **BL-152**; see §11.

Collection is also only the first obstacle: with the two uncollectable modules `--ignore`d, the
tree run blocks inside `boxy-pipeline/scripts/plan_extractor.py` running live against two sample
PDFs — still going at 8m42s with no output, and killed rather than waited out. So the root command
would run live extraction work on every invocation even once it collected.

What this ticket therefore ran, and reports as its stage-1 test evidence: `cloudcost/tests/`
(**440 passed**) and the root `tests/` scope that W3 edits (**129 passed, 7 xfailed**), each in the
only invocation that collects it. Named rather than presented as *"the whole suite"*, because it is
not the whole suite — and the two together cannot be run as one command.

---

## 10. Reading the GitHub report — and the one live defect in it

The run wrote `cloudcost/output/github/cloudcost_report_2026-08.html` (16K) and
`report_data_2026-08.json`. Read directly, not through the sprint's assertions.

`$47.81 USD`, period `2026-08`, one provider, one account, five services of which one is
non-zero — `copilot_for_business` at 47.81, with `actions_linux`, `actions_storage`,
`coding_agent_ai_unit` and `copilot_ai_unit` at 0.00. Declared period total reconciles against
the sum of service lines. Six `seat` resources, each `business`, each estimated at 7.97.
Month-on-month is `no_prior_month`, correct on a first run, and the report says the snapshot has
been persisted for next month.

**Three things read as broken and are not.**

1. **Six seats, zero orphan candidates.** All six catalog rules key on infrastructure types
   (`unattached_volume`, `unassociated_static_ip`, `aged_snapshot`, `idle_load_balancer`,
   `stopped_compute_with_attached_storage`, `stopped_database_with_storage`). Zero is the honest
   output of a catalog with no seat rule. Inert until t3, working correctly.
2. **Tag coverage 0%.** GitHub exposes no seat tags. The report does better than print a zero —
   the *"Untagged in a tagged account"* governance rule **declines to run** and says so:
   *"coverage 0.00% is at or below the 50.00% threshold, so this account does not count as using
   tags and the rule did not run. This is not a finding of 'no untagged resources'."*
3. **All six seats in the untagged-spender ranking.** *"Every untagged resource is shown; the cap
   of 10 dropped none"* — no silent truncation. The listed estimates sum to 47.82 against a billed
   47.81; that gap is the estimate-vs-billed distinction D4 mandates, and no estimate is ever
   summed into a total.

### 10a. The live defect: `evaluation_coverage` claims a completeness it does not have

**This is the finding t2c exists for.** The report prints, over six resources no rule can match:

> Of 6 usable resource(s), **every type is one the rule catalog evaluates** — 0 carried a type
> outside it, **so the totals above cover the whole inventory.**

and, in the tag section:

> **Every resource in this denominator carries a type the rule catalog evaluates**; none is
> counted here and evaluated nowhere.

A third sentence overstates in the same direction:

> 6 resource(s) carry `last_activity_at`, **so the recent-activity modifier was applied**; where
> it does not appear on a candidate it did not match.

The modifier adjusts confidence on candidates that fired. None fired.

**The mechanism, exactly.** `compose_report_data.py:578` computes the uncatalogued set as:

```python
if resource.get("type") not in CANONICAL_TYPES:
    uncatalogued.append({...})
```

Its own comment states the property it is standing in for — the N8 / BL-117 note at
`compose_report_data.py:594–596`:

> N8 (BL-117): a resource whose `type` is outside the canonical set is counted in every total
> and matched by no rule. Zero is emitted explicitly — an omitted zero and an uncounted quantity
> look identical.

*Counted in every total and matched by no rule* is the real predicate. **Membership of
`CANONICAL_TYPES` was a sound proxy for it only while the canonical set and the rule-keyed set
coincided.** m6 t1 ended that coincidence by adding `seat` to `CANONICAL_TYPES` before any rule
keyed on it — which was correct, the rule-legibility arm needs it — and the side effect is that
the one field designed to catch *counted everywhere, evaluated nowhere* can no longer see the
case its own comment names. Had `seat` not been made canonical, all six would have appeared under
`uncatalogued` and the report would have been right.

**Why this is worse than reading as broken.** A report that looks broken gets investigated. This
one tells an operator the evaluation is complete and the answer is zero.

**Why it does not wait for t3.** t3's seat rule makes these sentences true again *for `seat`*
while leaving the mechanism intact, so the next canonical type introduced ahead of its rule
reproduces it — and the consumption-class providers this milestone opens the door to are exactly
the ones that will. Filed as **t2c**, ahead of t3, in `../m6-github.md` §Ticket set.

Not fixed here: `compose_report_data.py` is outside Touches, and the ticket's instruction was to
report the report's reading rather than act on it.

### 10b. `monthly_cost_estimate` is month-to-date for a consumption provider

Carried here because t3's saving figure comes from this field and should not discover it.

`fetch_github.seat_monthly_cost` (`fetch_github.py:547–581`) returns

```python
money(float(price) * (float(quantity) / seat_count))
```

where `price` is the SKU's `pricePerUnit` and `quantity` its `netQuantity` — user-months
**consumed so far**. So the result is the rate scaled by `netQuantity / seat_count`, a ratio that
reaches ~1.0 only on a settled month in which every seat was held throughout, and is a fraction on
an in-flight one. Measured, same six seats, identical resource-id sets:

| Period | State | `pricePerUnit` | `netQuantity` | per-seat estimate | billed line |
|---|---|---|---|---|---|
| `2026-07` | settled | 19.00 | 5.999999904 | **19.00** | 114.00 |
| `2026-08` | in flight | 19.00 | 2.516128992 | **7.97** | 47.81 |

`19.0 × (5.999999904/6) → 19.00` and `19.0 × (2.516128992/6) → 7.97`, both reproduced from the
cost artifacts' own line items. DigitalOcean's equivalent is a true monthly list price — 4.00 for
`s-1vcpu-512mb-10gb`, 96.00 for `s-8vcpu-16gb`, 12.00 for `lb-small` — so the two providers'
`monthly_cost_estimate` do not currently mean the same thing.

**This is not an adapter defect and t2 is not to be amended.** The adapter reports consumed spend
faithfully and its D4 handling is deliberate: the multiplication is one operation at full
precision, rounded once, precisely so a sub-cent unit price is not zeroed. What is unsettled is
what the *field* should mean for a consumption provider — the monthly rate (`pricePerUnit`, which
is present in the same row and available) or spend to date. A seat orphan's saving is understated
mid-month under the current meaning, and the understatement shrinks as the month runs, which is
the kind of thing that is much cheaper to decide than to notice later.

---

## 10c. R27 — and this ticket is its first application

This ticket produced a rule by breaking the same thing twice, and the rule is recorded as **R27**
in `docs/milestones/hc-consolidation.md` §Ratified decisions: *in a cross-repo pair, the later
commit's reference to the earlier one is written last, after the earlier commit's SHA is final.*

**The two breakages that grounded it**, both inside this ticket:

1. The harness commit's body originally named agents `80e322c`. Amending the agents commit to
   correct its `[OK]` counts moved it to `28db111`, and the harness message was left citing a SHA
   on no branch. Caught and repointed.
2. The review amendment (AC1/AC2) moved the agents commit again, `28db111 → c7be6aa`, and
   re-broke the same three references the same way. Reported rather than fixed at that point,
   because the review had pinned the harness SHA.

Both are the same shape: **a one-way pointer written as a SHA is falsified by every amendment of
its target**, and nothing in either repo resolves such a reference, so nothing catches it. The
fix is ordering, not vigilance — write the pointer once the target has stopped moving.

**The amendment order used here is the rule's own first application**, and deliberately so: R27
landed in the agents commit *first*, and only then was the harness message repointed at the
resulting SHA — read fresh from the amended commit rather than carried forward from a prompt or a
packet, which is the specific way this pair failed the second time. A rule whose first
demonstration is the commit that introduces it is easier to trust than one asserted.

It extends the standing landing order rather than replacing it. Harness-first for a cross-citing
pair, and a one-way pointer landing after its target, both still hold; R27 governs only when the
pointer's SHA is *written*.

---

## 11. Forward

- **BL-152** — the root-level `python3 -m pytest -q` invocation cannot collect. Filed the day it
  was found, per the standing gate rule. Not fixed here: it is off-territory, it touches two use
  cases this ticket has no business in, and the fix is a `conftest.py`/rootdir question rather
  than a one-liner.
- **BL-151** is open and seeded with three entries. It is a home, not a work order — none of the
  three is fixed here.
- **t2c** carries §10a's defect and is filed ahead of t3, because t3 would paper over the instance
  and leave the mechanism. **t3** carries §10b's question about what `monthly_cost_estimate` means
  for a consumption provider. Both are recorded in `../m6-github.md` §Ticket set; §10 above is the
  detail that ticket's author reads.
- **R27** is recorded and applied here (§10c). Nothing enforces it — no check resolves a SHA named
  in a commit message — so it is a discipline the next cross-repo pair inherits as prose, which is
  the same footing as the landing order it extends.
- **`runbook.md` §Adding a provider still says *"Before provider four, read §Contracts"***.
  Provider four has now landed, so that instruction is spent. Left alone: it reads as standing
  advice, rewording it is not a defect this ticket found, and the runbook-update rule is engaged
  for command semantics rather than for prose that has merely been overtaken. Noted so the next
  round can decide rather than rediscover.
