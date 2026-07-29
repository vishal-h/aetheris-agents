# t3 — `compose_report_data.py` (N-provider merge + MoM) — implementation notes

**Ticket:** m1-cloudcost §t3. **Built:** 2026-07-29.
**Deliverables:** `scripts/compose_report_data.py`, `scripts/_normalized.py` (extracted —
see §Scope note), `tests/test_compose_report_data.py` (47 tests, offline),
`tests/fixtures/cost_do_2026-07.json`, `cost_do_2026-06.json`, `cost_soc_2026-07.json`,
`inventory_soc_2026-07.json`, `orphans_soc_2026-07.json`, `history/.gitkeep`,
`.gitignore` (excludes `history/*`).

---

## Scope note — one function moved out of t2's script, declared not silent

§t3 requires the report's tag-coverage figure to *equal* t2's. Two ways to get that: state
the definition twice and test that the two agree, or state it once. The m2b promoted rule
("factor cross-script plumbing into a shared `_helper.py` module rather than duplicating or
cross-importing between CLIs") settles it, so `parse_timestamp` / `iso` / `day` / `money` /
`tags_of` / `usable_resources` / `tag_coverage` moved verbatim from `detect_orphans.py` into
`scripts/_normalized.py`, and both stages import them. The coverage number and the
usable-resource denominator behind it now have one definition; drift between the stages is
not a thing that can happen rather than a thing a test watches for.

This touches a file t2's review approved, which is why it is called out here rather than
buried in the diff. Two things bound the risk:

- **The move is mechanical and t2's 54 tests are the proof** — they pass unchanged (see the
  packet's done-check block), including the two that read `detect_orphans.py`'s *source text*.
- **The provider-agnostic guard was extended to follow the code it watches.** `t2
  test_the_rules_never_read_a_provider_specific_field` greps the rule module for field reads;
  the extraction would have quietly moved three of those reads out of its reach. It now reads
  `detect_orphans.py` + `_normalized.py`, so the refactor cannot shrink the guard — the
  adjacent-case failure this class of change invites. (`_normalized.py`'s docstring
  deliberately does not spell out the provider-payload key, because that same guard greps for
  the literal.)

---

## Decisions

**The report is stamped from its inputs, never from a clock — so `compose()` is pure and the
payload is byte-deterministic.** §t3's contract-ref note flagged that t1's snapshot carries a
wall-clock `generated_at` and t2's candidates deliberately do not, and told t3 to decide
explicitly what the report is "as of". It is `as_of = max(generated_at)` over the cost
snapshots and inventories it merged — the newest fetch the report was built from. That is a
*derived input value*, so re-composing the same files never moves it, and the whole payload
is byte-identical run to run (asserted). The orphan side's own stamps are not folded into
`as_of`; they are carried separately as `orphans.evaluated_as_of[]` (`reference_date` +
`inventory_generated_at` per provider), because "when the data was fetched" and "what date the
age rules were evaluated against" are different questions and a report that conflates them
cannot answer either. `datetime.now`/`utcnow` appear nowhere in the module, and a test asserts
that.

**A cross-currency grand total is withheld, not summed.** m1 does no conversion (original
currency). When the bundles disagree on currency, `grand_total` and `currency` are `null`,
`totals_by_currency` carries the real figures, and a warning names the currencies. Summing
them would have produced a well-formed number that means nothing — the exact shape of the
silent-wrong-answer class. At N=1, and at N=2 in one currency, `grand_total` is a plain scalar
as the report expects.

**The declared period total is authoritative; the line-item sum is the check on it.** Each
provider row carries `amount` (the snapshot's `totals.amount`), `line_items_sum` (summed from
the *rounded* rows the report renders, so the column adds up on paper), and `reconciled`. A
disagreement past a cent is a warning, not a silent pick — and the same reconciliation runs on
the prior-month side, its warnings carried with `scope: "prior period YYYY-MM"` rather than
swallowed.

**Both sides of the MoM delta go through the same grouping function.** `month_on_month`
re-runs `service_totals` over the prior snapshots rather than reading their `line_items`
directly, so the two sides of every subtraction were grouped, aggregated and rounded by
identical rules. A service that appeared or disappeared is labelled (`new` / `removed`) rather
than silently differenced against a zero it never had, and `delta_pct` is `null` off a zero
base — never a fabricated percentage. `prior_period()` derives the prior month from the
*period string*, so re-composing an old period looks at that period's own predecessor and not
at the calendar.

**First run is a path, not an error.** No `history/{prior}/` directory → `mom_delta:
{"status": "no_prior_month", ...}`, no warning, exit 0. An *absent* prior month is silent; an
*unreadable* one is a skipped entry, because those are different facts.

**Candidates are carried through verbatim, plus exactly one key.** Each t2 candidate keeps its
`evidence[]`, `base_confidence`, `modifiers[]` and `monthly_saving_estimate` untouched;
`provider` is added because at N>1 the bands are shared across providers and the candidate
itself carries no provenance. A test asserts `entry minus provider == the t2 candidate`, so
"verbatim" is checked rather than claimed. Band cutoffs (HIGH ≥ 0.9, MEDIUM 0.7–<0.9, LOW <
0.7) are emitted into the payload as `orphans.bands[]` so the report can print the thresholds
it grouped by; a candidate with a non-numeric confidence is skipped and counted, never banded
into LOW by default.

**Bundle discovery is by document shape, not by filename.** `--input-dir` classifies each
`*.json` by its top-level shape (`line_items` → cost, `candidates` → orphans, `resources` →
inventory) and groups by the `provider` field *inside* the file. This is what lets one
directory hold several providers despite t2 writing a provider-less
`orphan_candidates_{period}.json` name (see §Open items), and it means the pipeline's own
`report_data_*.json` output sitting in that directory is ignored rather than re-read as input
— asserted by a test that runs the CLI twice over its own output directory.

**Positional triples are strict about count.** `--cost/--inventory/--orphans` pair by
position, so unequal counts would misattribute one provider's inventory to another's costs.
Mismatched counts are an error envelope; a provider whose file is genuinely absent passes the
path anyway and degrades to a skipped entry.

**`--history-dir` defaults to the use-case root, not the cwd.** Unlike `--output-dir`
(cwd-relative `output`, per t1/t2), history is a store that accumulates across runs and must
land in the same place whichever directory the orchestrator invoked the script from —
`Path(__file__).resolve().parent.parent / "history"`, the same anchoring rationale as
`__ENV__.file` in agent files. Persistence is keyed `{provider-slug}_costs_{period}.json`
under `history/{period}/`, so re-running a period overwrites and never appends; the slug is
computed in Python, never by the LLM. A period that is not `YYYY-MM` writes no history at all
rather than leaving a `history/unknown/` tree nothing can ever read back.

**Degrade, don't crash (repo rule), and the two degradation channels stay distinct.**
`warnings[]` is "composed, but you should know"; `skipped[]` is "an input could not be used".
Either makes the run `{"status": "partial"}` with exit 1, and the report file is still
written. A missing orphan file costs the report its orphan section and nothing else.

---

## Fixtures

Five new, all offline. The DO side deliberately reuses what the earlier stages are already
tested against: `inventory_rules_positive.json` (t2) is the inventory, and the orphan input is
produced by calling the **real t2 `detect()`** in the test rather than a hand-copied stand-in —
so the "carried through verbatim" assertion compares against the object t2 actually emits.

| Fixture | Purpose |
|---|---|
| `cost_do_2026-07.json` | current period, frozen §Normalized schemas shape; the service totals the recorded DO invoice aggregates to (168.50 + 3.71 + 0.00 = 172.21) |
| `cost_do_2026-06.json` | the seeded prior month: one service grew, one is absent-then-new, one exists-then-removed, so the delta exercises three cases and not one |
| `cost_soc_2026-07.json` | a second provider's costs — the N-provider proof |
| `inventory_soc_2026-07.json` | its inventory; 25 % coverage, and its untagged compute is the costliest resource in the two-provider union, so the top-untagged ranking has to sort *across* providers |
| `orphans_soc_2026-07.json` | **generated by running the real t2 CLI** over that inventory, committed as emitted — a crafted stand-in would have proved only that t3 reads what t3's author wrote |

The MoM assertions derive their expected numbers from the seeded snapshot in the test body; a
hardcoded delta would still pass if the prior month were never read at all.

---

## Cross-stage check (t1 → t2 → t3)

Per the m6 learning, `test_the_whole_pipeline_composes_end_to_end` runs the **real t1 adapter**
against the recorded DO responses (over t1's `DOStub` HTTP server), feeds its emitted inventory
to the **real t2 CLI**, and feeds both its files plus t2's candidates to the **t3 CLI**. It then
asserts the report against *the stages' own output* rather than against constants: the grand
total equals the snapshot's `totals.amount`, the service map equals its `line_items`, the
coverage figure equals the one t2 independently reported on the same inventory, every t2
candidate lands in a band with its evidence list intact, and the run's snapshot is on disk for
next month. Two seams, one assertion set — a rename or a shape drift on either fails here
rather than in the live pipeline.

---

## Mutation checks (the guards are failable)

| Mutation | Result |
|---|---|
| `band_of`: `>=` → `>` at both cutoffs | 4 failed |
| `coverage_section`: read `tag_coverage` from the orphan file instead of the inventories | 2 failed |
| `prior_period`: return the same month (no decrement) | 6 failed |

Restored: 47 passed. The D4 source guard is checked the same way from the other direction — it
asserts the estimate-read patterns are *absent* from the two cost functions **and present** in
the two sections that legitimately rank and total estimates, so it cannot pass by matching
nothing.

---

## Open items forwarded

- **t2's output filename carries no provider.** `orphan_candidates_{period}.json` collides at
  N≥2 in a single directory. t3 is unaffected (it groups by document shape and by the
  `provider` field inside the file, and the explicit-triple form takes any paths), but the
  first real multi-provider run wants either per-provider output dirs or a
  `{provider}_orphan_candidates_{period}.json` name from t2. A naming decision, not a bug.
- **`t4` renders, it does not compute.** Everything the report needs is in
  `report_data_{period}.json`, including the band cutoffs, the `top_k` actually applied, the
  reconciliation flags, and the two "this is an estimate, not billed cost" notes — so the
  template never needs a figure t3 did not put there.
- **Spot-check the t1 list-price rates against an invoice line.** t1 forwarded this to t3 on
  the grounds that "invoice items are already in hand" at t3 — they are not, in the sense that
  matters: DO bills at *service* granularity (D4), so the invoice carries no per-resource line
  to check a volume/snapshot/reserved-IP/LB rate against. Only the volume rate was
  invoice-derivable and t1 already did it. Re-forwarded to whoever has a resource-granular bill
  (the first AWS/GCP adapter), not silently dropped.
- **`monthly_saving_estimate` inherits t1's estimate accuracy.** The orphan section's saving
  subtotals are only as good as the per-resource rates above; the payload labels them
  estimates, and the report should too.
- **t1/t2's open items stand:** the live account still carries no genuine orphan
  (§Prerequisites 2), so t5's "≥1 real orphan" done-when still needs one planted.
