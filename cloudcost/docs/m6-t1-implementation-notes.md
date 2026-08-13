# m6 t1 — open the milestone, extend the canonical type vocabulary by one member

Landed 2026-08-13, agents `3e1f6be` → this commit. Harness untouched at `66a9ca5`.

**This file's standing, settled at the r1 review.** It was written outside t1's `Touches`,
against a *Do not generate* clause reading *"No document other than
`cloudcost/m6-github.md`"*, on the repo-level rule that an implementation-notes file is a
required deliverable — §6 frames a ticket's exclusions as *"on top of the repo-level
CLAUDE.md list"*, i.e. additive rather than overriding. **The reviewer ruled the clause
wrong, not the file** (r1, R1): the exclusion was aimed at a new milestone or specification
document and should never have reached the round's own record, whose reader is t2. The file
**stays**, t1's `Claude-code prompt` pointer is **correct as it stands**, and t1's
*Do not generate* clause was amended so the next ticket does not inherit the trap.

**`Touches` was widened by reviewer decision, not by a deviation taken here.** r1's **R3**
directs the C3 finding below to be appended to **BL-150** under **R23**, which adds
`docs/backlog-2026-06.md` to this ticket's `Touches`. Recorded as a reviewer decision made
at the review, so a later reader does not read it as scope taken unilaterally.

---

## Gate (§11), five verdicts

| # | Verdict |
|---|---|
| i | **TRUE** — agents `3e1f6be`, harness `66a9ca5`, both clean, both level with `origin/main` |
| ii | **TRUE** — seven `TYPE_*` constants at `_normalized.py:39–45`; `CANONICAL_TYPES` at `:48–58` built from those names, not from literals |
| iii | **TRUE, with a precision** — `sprint.sh:3250` imports `CANONICAL_TYPES`. The assertion is not a Python `<=` subset test: it is `outside = sorted(t for t in emitted if t not in CANONICAL_TYPES)` at `:3273`, with the message at `:3279–3280` printing the whole sorted set |
| iv | **TRUE of the sentence, with a precision** — the importer list at `:12–14` names two adapters where three import, and omits `compose_report_data.py`. The docstring's **first** paragraph (`:3–4`) *does* name `compose_report_data.py`, as a downstream stage rather than as an importer, so "the docstring omits it" is true only of the unit W4 replaces |
| v | **TRUE** — see below |

**Gate (v), the filename.** Five milestone documents; naming is **not uniform**:
`milestone.md` (m1, unprefixed — it predates the series), `m2-milestone.md`,
`m3-milestone.md`, `m4-consolidation.md`, `m5-n1-compose.md`. m4's own blockquote ratifies
the break — named *"for what it is rather than to the series pattern. A sweep looking for
`m4-milestone.md` will not find it."* So `m<N>-<subject>.md` is the live convention for the
last two rounds and `m6-github.md` matches m5's shape. No `m6*` file existed under
`cloudcost/`. **Proceeded.**

**Two reviewer repo-state claims inside the W1 body, verified rather than trusted** — both
hold, so both sentences landed:

- **D1's ground.** All three adapters declare the constant: `fetch_do.py:56`
  (`CURRENCY = "USD"`, with *"the billing API carries no currency field"*),
  `fetch_aws.py:71`, `fetch_linode.py:89`. `fetch_linode.py:583` alone emits a
  `currency_basis` field recording the check as provenance — the "one records the check"
  half.
- **D4's ground.** The exemplar is `fetch_aws.py`, which aggregates then rounds at exactly
  four sites: `:532` (`gib * rate`), `:604`, `:683` (`compute + gib * storage_rate`),
  `:708`. The counter-example is `fetch_linode.py`: its `PriceTable` stores rates through
  `money()` at `:396` and `:401` — rounding the unit rate at ingest — and then multiplies
  that rounded rate at `:763` (`money(rate * (size_gb or 0))`). Latent rather than live,
  because the volume-rate unit is ambiguous and that path is guarded.

---

## A1 — the docstring edit's width (reviewer amendment)

Instructed: fix both defects in the quoted unit, because §11 scopes a surgical edit by
**unit** and a sentence the replacement falsified but did not touch is precisely the failure
§11 names.

**Unit at HEAD** (`_normalized.py:11–14`), verbatim:

```
The same argument, more strongly, holds for the canonical `type` / `state` *values* below:
they are the definition of the schema seam, so by construction they have exactly one home
— this module — which every adapter (`fetch_do.py`, `fetch_aws.py`) and the shared rule
engine imports from (m2 t2 a/a′).
```

**Replacement**, verbatim:

```
The same argument, more strongly, holds for the canonical `type` / `state` *values* below:
they are the definition of the schema seam, so by construction they have exactly one home
— this module — which all three adapters (`fetch_do.py`, `fetch_aws.py`,
`fetch_linode.py`), the shared rule engine and `compose_report_data.py` import from
(m2 t2 a/a′).
```

Constraints, each discharged:

- **True about how many adapters import:** three, named and counted.
- **Does not omit the production importer of the set:** `compose_report_data.py` imports
  `CANONICAL_TYPES` at `:59` and consumes it at `:578` (the `uncatalogued` accumulator).
  It is the only production consumer of the *set*.
- **The two imports differ, and the distinction was deliberately not carried.** The
  adapters take individual `TYPE_*` constants and never the set; the composer takes the
  set and none of the constants. The existing sentence speaks at the level of *who imports
  from this module*, and carrying the distinction would have turned it into a paragraph —
  so it was kept accurate at the level it already spoke. **Recorded here as instructed
  rather than silently chosen.**
- **`sprint.sh` deliberately not added.** C1 already records that cross-repo coupling; a
  second copy in the docstring can drift out of agreement with the first. On whether it
  belongs: it does not — C1 is the right home, because the coupling is a *contract*
  property (any change to it is a cross-repo change) rather than a fact about this module's
  import graph.
- **Trailing provenance marker preserved:** `(m2 t2 a/a′)`, unchanged.

---

## A2 — the storage-class deferral paragraph (reviewer amendment)

The paragraph W1 landed stated one blanket ground across three entities, and it was wrong
for packages: package versions persist until deleted rather than expiring under a retention
policy. Quoted at HEAD and replaced as a unit with the reviewer's supplied text; surrounding
sections untouched. A ratified decision carrying a false ground is the worst kind, because
the next two providers in this class inherit it.

---

## B1 — the count sweep, full enumeration

**Defect class:** prose in either repo stating the canonical type set's *size*, or counting
its members, rather than referring to them without a number.

**Population and command.** Both repos, `.md`/`.py`/`.exs`/`.sh`: lines naming the
vocabulary (`CANONICAL_TYPES`, `TYPE_*`, ``canonical `type`|vocabulary``, `type vocabulary`)
filtered for `seven|eight|\b7\b|\b8\b|each of the|all (seven|eight)|the N canonical`.

**Controls.** The harness path returns a real **0** under the count filter while the same
pattern without it returns **4** hits for `CANONICAL_TYPES` there — so the harness zero is
an observation about the world, not about the command. `sprint.sh` prints
`sorted(CANONICAL_TYPES)` dynamically (`:3280`) and carries no count in any form.

| Path:line | Sentence (abbreviated) | Verdict | Action |
|---|---|---|---|
| `cloudcost/milestone.md:327` | *"adapters import the seven `TYPE_*` constants individually and never the set"* | **(a) count claim** — the argument is individually-versus-the-set, which the number does not carry | **FIXED** — in `Touches` |
| `docs/backlog-2026-06.md:2778` | *"Adapters import the seven `TYPE_*` constants"* | **(a) count claim** — same sentence, same argument | **report only, outside `Touches`** |
| `docs/reviews/m2-cloudcost-t2-review.md:28` | *"type vocabulary → 7 canonical TYPE_\* + CANONICAL_TYPES frozenset"* | (a)-shaped, but a **closed round's review record** | report only |
| `cloudcost/docs/bl-084-implementation-notes.md:83` | *"seven canonical types"* | (a)-shaped, closed round record | report only |
| `cloudcost/docs/m4-t4a-implementation-notes.md:505` | *"`TYPE_*` ×7"* | (a)-shaped, closed round record | report only |
| `…m4-t4a…:509` | *"two of the seven canonical types"* | (a)-shaped, closed round record | report only |
| `…m4-t4a…:516` | *"adapters import the seven `TYPE_*` names individually"* | (a)-shaped, closed round record | report only |
| `…m4-t4a…:523` | *"`detect_orphans` (7 `TYPE_*` imports…)"* | (a)-shaped, closed round record | report only |
| `…m4-t4a…:1362` | *"Adapters import the seven `TYPE_*` individually"* | (a)-shaped, closed round record | report only |
| `…m4-t4a…:1364` | *"the sprint depends on `_normalized` at three points"* | **(b) load-bearing** — the figure *is* the finding | report only, no edit ever |
| `cloudcost/docs/m3-linode-scout.md:68` | *"`frozenset` of exactly the seven above"* | (a)-shaped, closed round record | report only |
| `cloudcost/milestone.md:252–261` (table) | the eight table rows | **(c) data** — an enumeration, not a size claim | row added; not a count |
| `cloudcost/tests/test_detect_orphans.py:840–848` | the literal set | **(c) data** | `"seat"` added; not a count |

**Two count-bearing lines this ticket introduced, both examined:**

- `cloudcost/tests/test_detect_orphans.py:855` — `assert len(CANONICAL_TYPES) == 8`.
  **(c)/assertion, not prose.** W7 requires it, and an assertion whose whole job is to pin
  the size is the one place the number belongs.
- `cloudcost/m6-github.md:100` — t1's Scope, *"gains an eighth member"*. **(b)
  load-bearing and non-expiring.** It is an ordinal about an *event* — the position t1's
  addition occupied — not a claim about the set's current size, so t2 adding a ninth does
  not falsify it. Kept deliberately; recorded here so the choice is auditable rather than
  assumed.

**The sweep caught one defect it had just created.** The W5 prose as first written said
*"what GitHub emits for each of the seven rows above"* and *"asserting what Linode emits for
all seven"* — two fresh instances of the exact class. De-numeralised before the B2 edit.

## B2 — the fix, `:327` only

Confirmed at HEAD that the count is not load-bearing before editing: the sentence's argument
is *individually versus the set*, and its conclusion (`CANONICAL_TYPES` is used without being
declared as API) follows from the manner of import, never from how many constants there are.
De-numeralised rather than incremented — a count in prose about a set that grows is a claim
with an expiry date, and `:327` would have been ambiguous the moment t1 landed and false the
moment t2 does.

**The boundary loss, named rather than implied.** `docs/backlog-2026-06.md:2778` is the one
**live, non-record** (a) instance left standing, and it carries the same sentence as `:327`
did. It is outside `Touches`; `Touches` was not widened. The remaining nine are closed-round
records (implementation notes, a review file, a scout), which decision 7 says are corrected
by a dated note rather than rewritten — so they are report-only on two independent grounds.

---

## C3 — m5's header divergence: reported, no action

**Question:** was m5's departure from m1–m4's `**Status:**` block deliberate?

**Answer: cannot be established, and nothing explains it.**

- `cloudcost/m5-n1-compose.md` contains **zero** occurrences of the string "Status".
- Its opening commit `eebd47c` (*"docs(m5): open the N>1 compose round"*) says nothing about
  header form.
- Its own provenance stamp cites `hc-consolidation` **R12**, which governs *when a ticket's
  anatomy is authored*, not a document's header shape.

**One piece of evidence, labelled as evidence rather than proof.** The same document *does*
carry an explicit `[Deviation, recorded rather than glossed …]` block about its own creation
— so its author was recording deviations where they knew of one, and did not record this
one. That is consistent with the change being unnoticed, and also with its being thought too
minor to record. It does not settle intent, and is not treated as if it did.

**Disposition, settled at r1 (R3).** The finding belongs to the documentation system, which
under **R23** means the standing append-only row **BL-150** rather than a row of its own.
r0 reported it and did not append; **the reviewer placed it there at r1**, and the entry was
appended in this commit — one dated item in BL-150's `**Appended.**` block, matching the form
of the existing entry. It is **not triaged**, proposes **no convention**, and states that
intent was **not established** rather than asserting drift. `m5-n1-compose.md` is unchanged.

---

## The m6 provenance block (W1), element by element

m5's form matched exactly: H1, blank line, a two-line single-backtick code span, blank line,
straight into the first `##` — no `---`, no `**Status:**` line.

```
`Opened 2026-08-13. Canonical document for GitHub as provider four. Authored by
the reviewer; recorded here by claude-code.`
```

| Required element | Carried by |
|---|---|
| the milestone is OPEN, and the date | *"Opened 2026-08-13"* |
| canonical for GitHub as provider four | *"Canonical document for GitHub as provider four"* |
| authorship split | *"Authored by the reviewer; recorded here by claude-code"* — taken verbatim from `docs/milestones/hc-consolidation.md:108–109` (§Ratified decisions preamble), not invented |

---

## W3 — the ordering convention, established by reading

`_normalized.py:39–45` is neither alphabetical nor grouped. The constants follow **the order
the types entered the contract**: m1's five DigitalOcean types first (`compute_instance`,
`volume`, `static_ip`, `snapshot`, `load_balancer`), then m2's two AWS additions
(`database`, `database_snapshot`). `CANONICAL_TYPES` repeats that same order rather than
sorting. So `TYPE_SEAT` appends at the end of both, as the newest member — which is what the
convention dictates, not merely what is convenient.

**Collision check — clean, with a positive control.** `seat` (whole-word, case-insensitive)
returns **no hits** in `compose_report_data.py`, `render_report.py`, `report.html.j2`,
`fetch_linode.py`, `_normalized.py` or `sprint.sh`; the identical command with the
known-present term `snapshot` fires on five of those six. Every `seat` occurrence in either
repo is English prose in unrelated documents. **This mattered concretely**: three tests
derive forbidden-literal sets from `CANONICAL_TYPES`
(`test_detect_orphans.py:866`, `:870`; `test_fetch_linode.py:115`), so a collision would
have turned the widening into an immediate red.

## W5 — why prose and not a column

The table is three columns, and **every row carries a cell in each**; the existing `—`
(on `database`/`database_snapshot` for DigitalOcean) means *this provider emits nothing for
this type*. A fourth column is therefore **not sparse** — it would force an assertion about
GitHub on every infrastructure row, which is exactly the reason the ticket gives for
excluding a Linode column. So: the row landed, and GitHub is named in prose beneath the
table. The row's `—` cells for DigitalOcean and AWS are checkable at HEAD — neither adapter
emits `seat`.

## W7 — the tests, and the mutation test

Module: `cloudcost/tests/test_detect_orphans.py`,
`test_the_rules_key_only_on_canonical_type_values` (`:829`).

A membership assertion already existed as an exact `==` against a seven-element literal
(`:840`), so extending it with `"seat"` was **required, not optional** — `TYPE_SEAT` breaks
that test on landing. The two assertions W7 names were added on top.

**Mutation test, in two parts, because the first part did not exercise the new assertions.**
Removing `TYPE_SEAT` from the frozenset made the test fail — but at the `==` assertion, which
short-circuits before the two new lines, so that run proved nothing about them. The two were
then exercised individually under the same mutation and **each failed**: membership, and
`len(...) == 8` against an observed size of 7. The `TYPE_SEAT` constant itself remained
defined throughout, confirming the mutation hit the set and not the name.

**The restore was verified, not assumed** — a control on the restoration itself: the mutated
line absent from the frozenset (`grep -c` → 0) before, present (→ 1) after, and the resulting
`git diff` showing exactly the three intended changes and nothing else.

### HAZARD FOR t2 AND t3 — the `==` at `:840` masks every assertion after it

**Read this before adding an assertion to
`test_the_rules_key_only_on_canonical_type_values`.** Both t2 and t3 add assertions in this
region, so this is live rather than historical.

`test_detect_orphans.py:840`'s exact set-equality (`CANONICAL_TYPES == {…}`) **short-circuits
the rest of the function**. Any assertion appended after it — as t1's two were — can be
shipped **having never once been executed against a failing state**, because the mutation you
reach for to test it trips the equality first and the test goes red for the wrong reason. A
red test then reads as proof the new assertion works, and it is not.

This is **Silent-wrong-answer one level in**: the rule says construct the broken state and
watch the check fail, and here *a* check fails while *the check under test* never runs. t1
came within one command of shipping both new assertions unexercised.

**The two-part procedure that exposed it, owed by whoever adds the next assertion:**

1. **Mutate**, then run the test. Note *which* assertion raised. If it is `:840` rather than
   yours, **this run has told you nothing about your assertion** — do not stop here.
2. **Exercise your assertion in isolation under the same mutation**, outside the test
   function — import `_normalized` directly and evaluate your predicate — and confirm it
   fails on its own. t1 did this with a standalone `python3 -` block, which is enough.
3. **Restore, and verify the restore as its own claim**: the mutated text present, then
   absent, plus a `git diff` showing only the intended changes. A restore that silently did
   nothing leaves a red that will be explained away.

The general fix — reordering so the broadest assertion comes last, or splitting the function
— is **not taken here**: it is outside t1's `Touches`, and t1 ships no rule and no adapter.
Recorded rather than fixed, deliberately.

---

## Done-check

- `python3 -m pytest cloudcost/tests/ -q` → **386 passed**, exit 0 — r0 in 145.17s, re-run at
  r1 in 143.27s. Identical to the figure m5 t1, t2 and t3 each recorded.
- `./scripts/sprint.sh cloudcost` → exit 0, **23 `[OK]` · 0 `[FAIL]` · 0 `[WARN]`**, 76 lines,
  on all three runs now on record: r0 before, r0 after, and the r1 re-run.

**Both commands were re-run in full at r1** rather than waived on the ground that the
amendments were mostly prose — **R2 touched `_normalized.py`**, so the sprint was not exempt.

**The rule-legibility arm, byte-identical across the change** — the arm is non-blocking by
construction (its failure path increments a counter and does not halt), so the green summary
is not what is being relied on here:

```
r0 before: [OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set
r0 after : [OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set
r1       : [OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set
```

**The first sprint attempt is recorded rather than dropped**: run without a provider
credential, it halted at `CLOUDCOST_DO_TOKEN is not set` after 22 lines (exit 1) and the arm
never ran. The before-capture was then taken the runbook's documented way
(`set -a; source ~/.secrets/do-cloudcost.env; set +a`), which reached the **legible** branch
— a stronger before-state than the `na` branch would have given.

**`../aetheris/scripts/sprint.sh` — verified, not edited.** The harness tree is clean at
`66a9ca5`. Widening only relaxes `:3273` (`t not in CANONICAL_TYPES`), and `:3280` prints
`sorted(CANONICAL_TYPES)` on a failure path only, so no harness edit is owed and this does
not become a cross-repo pair with a landing order.

## Runbook

No entry owed: no environment variable, no startup step, no configuration key, no new
procedure, and no changed command semantics — the new type is emitted by nothing. Recorded
explicitly rather than left as an unexplained absence.
