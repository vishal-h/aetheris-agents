# TECHNICAL BRIEF: Function-Level Wiring Specs for AI-Assisted Development

## 1. What this is

A proposal to maintain a machine-readable inventory of every function in our
system — its dependencies, its guard conditions, and where control flows next —
as line-per-record JSONL files colocated with the code and compiled into a
single artifact in CI, with a query layer on top.

**What it is not:** a replacement for code, a behavioral specification, or a
guarantee of correctness. The spec captures *wiring* — what a function depends
on and what it calls — not *logic*. The transformation a function performs
still lives in code and is described, imperfectly, in prose. We are explicit
about this limit because everything downstream depends on not forgetting it.

## 2. The problem

When an AI agent (or a new engineer) works on this codebase, the expensive
question is rarely "what does this function compute?" — reading the body
answers that. The expensive questions are structural:

- What does this function depend on (infra, services, injected functions)?
- Under what conditions does it run at all?
- Where does control go on success and on failure?
- If I change it, what breaks?

Today these answers are scattered across imports, framework config, middleware
chains, and tribal knowledge. The proposal is to make them explicit, queryable,
and validated in CI.

## 3. The record schema

One JSON object per line. One line per function. Fields:

```json
{
  "id": "core.billing.checkout.process_payment",
  "version": "1.2.0",
  "status": "active",
  "visibility": "public",
  "provenance": "authored",
  "description": "Charges the customer's payment method for a valid cart.",
  "guards": {
    "meta.action": "SUBMIT_PAYMENT",
    "context.user.is_authenticated": true
  },
  "deps": {
    "infra":    ["infra.db.postgres", "infra.gateways.stripe"],
    "context":  ["core.iam.session.UserSession"],
    "input":    "core.billing.types.Cart",
    "meta":     "core.shared.types.RequestMeta",
    "injected": ["core.billing.ledger.record_transaction",
                 "infra.gateways.stripe.charge"]
  },
  "flow": {
    "on_success": "core.billing.checkout.handle_success",
    "on_failure": ["core.billing.checkout.handle_failure",
                   "core.billing.checkout.retry_payment"]
  }
}
```

Notes on deliberate choices:

- **`guards`, not `pattern_match`.** Same idea (declarative preconditions,
  lifted out of function bodies — Elixir function heads, essentially), plainer
  name. The value vocabulary is small and closed: literals, `"EXISTS"`,
  `"ABSENT"`, and enum membership. Anything more complex stays in code and the
  guard says `"_custom": true` so the analyzer knows it can't reason about it.
- **`flow` values are arrays where needed.** Real error handling branches more
  than two ways. We don't pretend otherwise.
- **`id` is a hierarchical URI**: `domain.subdomain.bounded_context.function`.
  Uniqueness is enforced at compile time.
- **`version`** bumps when the record changes, so consumers can diff.
- **`status`** is `active` or `deprecated`. Deprecated records may carry
  `"replaced_by": "<id>"`. The compiler warns on any inbound reference to a
  deprecated ID, so IDs can evolve without breaking consumers overnight.
- **`provenance`** is `authored` (human-written or human-approved) or
  `extracted` (machine-generated, unreviewed). See §5 and §11.
- **`provenance` and `status` are orthogonal.** `provenance` says who vouches
  for the record; `status` says whether the function is current. An `authored`
  record can be `deprecated`; an `extracted` one is usually `active`.

## 4. Schema ownership

The record schema, the compiler, and the query CLI have **one named owner** —
a person, not a working group. All field additions and guard-vocabulary
changes go through them. Spec formats without an owner accrete fields until
nobody can write a valid record from memory.

## 5. Granularity: complete graph, tiered effort

"Spec every function" explodes; "spec only the public surface" leaves holes in
the graph — if a spec'd function calls an unspec'd one that touches Stripe,
impact analysis from Stripe upward silently breaks. We do neither. Instead:

- **Public surface / module boundaries:** human-authored (or human-approved)
  records. `description` required. Guards reviewed. `provenance: "authored"`.
- **Interior functions:** auto-emitted by the extractor with mechanical fields
  only — `deps`, observable `flow`, no `description` required.
  `provenance: "extracted"`. Zero review burden.

The graph is always complete; human attention is spent only at the
boundaries. To enforce completeness, the extractor emits a record for
**every** function it can discover — even if some fields are empty or null —
so there are no ghost nodes. Functions it *cannot* discover (dynamic dispatch,
reflection) are a known limitation, covered in §11; everything statically
visible is in the graph. An interior record gets promoted to `authored` only
when someone has a reason to care about it (it shows up in a hotspot query, a
migration touches it, etc.).

## 6. What the graph is (and isn't)

`injected` + `flow` edges give us a directed graph of the system. It is **not
guaranteed acyclic** — retries, recursion, and event re-entry are cycles, and
they're legitimate. The compiler:

1. Builds the graph.
2. Reports cycles. Each cycle must be either listed in an `allowed_cycles`
   manifest (with a one-line justification) or fixed.
3. Topologically sorts the acyclic remainder for build/test ordering.

This turns "the architecture is a DAG" from a false claim into an enforced,
exception-tracked policy.

## 7. Guards: overlap resolution and vocabulary discipline

**Overlap.** If an input can satisfy the guards of two functions in the same
dispatch context, which runs? We require one of:

- **Disjointness** — the compiler proves the guard sets can't both match
  (cheap for our closed value vocabulary), or
- **Explicit ordering** — records in the same dispatch group carry a
  `priority` field, first match wins (Elixir clause-order semantics).

Ambiguous overlap without a declared ordering is a compile error.

**Vocabulary discipline.** Teams will push to make guards more expressive.
Two mechanisms keep this honest, rather than relying on willpower:

1. **The `_custom` ratio is published.** The compiler reports, per module, the
   fraction of records using `"_custom": true`. Vocabulary pressure becomes
   visible data, reviewed at each rollout checkpoint — not hallway grumbling.
2. **Checkability is the admission price.** A proposed guard construct enters
   the vocabulary only with a demonstration that the analyzer can still
   perform disjointness checking over it. If it can't be statically checked
   for overlap, it stays in code behind `_custom`. This is the actual cost of
   expressiveness, and making it the entry fee keeps the guard language from
   becoming a second programming language.

## 8. Files, layout, compilation

- `specs.jsonl` files live next to the code they describe
  (`src/billing/checkout/specs.jsonl`).
- CI runs `compile_specs`:
  - validates every line against the JSON Schema for the record format,
  - checks ID uniqueness and that every referenced ID resolves,
  - runs cycle and overlap checks (§6, §7),
  - warns on references to `deprecated` records,
  - emits `dist/architecture.jsonl` and a Graphviz DOT export of the graph.
- A failing check fails the build. The compiled artifact is what tools and
  agents consume.

The DOT export is deliberately low-tech: `dot -Tsvg` during design reviews
covers most visualization needs. IDE-integrated graph views are explicitly
out of scope until the pilot proves the rest.

## 9. Keeping specs honest: the drift problem

Specs adjacent to code **will** diverge from the code unless something forces
agreement. ID uniqueness checks don't catch a spec that lies. Our conformance
strategy, in order of increasing strength:

1. **Extraction diff (baseline, required).** A static extractor regenerates
   the mechanical fields (`deps.infra`, `deps.injected`, observable `flow`
   targets) from the AST on every CI run and diffs against the committed spec.
   Mismatch fails the build. Prose `description` and `guards` semantics are
   exempt — the extractor can't verify meaning.
2. **Spec-first for new code (target state).** For new modules, the spec is
   written first and a scaffold generator emits the function skeleton (guards,
   injected params, flow stubs) **and the matching wiring-test skeleton** —
   the test that asserts declared dependencies are called under declared
   guards. Generating both from the same record reinforces the contract:
   the spec governs structure, the hand-written body governs behavior. The
   code can't drift from what was generated from the spec — only the body
   is hand-written.
3. We do **not** attempt round-trip equivalence for legacy code. See §11.

## 10. The query layer

The compiled artifact does nothing by itself; the value is realized through
queries. A small library plus a thin CLI (`specs query ...`) — deterministic,
JSON to stdout, no daemon — answers questions like:

- *Subgraph extraction:* "everything under `core.billing` reachable in ≤3
  hops" — the slice handed to an agent or an engineer for a task.
- *Reachability conditions:* "what guards must hold for execution to reach
  this function?" — composed along the path.
- *Impact analysis:* "what transitively depends on this injected dependency
  or infra component?" — the blast radius of a change.
- *Hotspots:* "rank functions by infra-dependency count / injected-graph
  density" — coupling made visible and sortable.

Because the CLI is a plain script with JSON output, AI agents consume it the
same way humans do — as a command — with no agent-specific integration work.
Two stability rules, since agent prompts will hard-code invocations: query
output schemas are versioned behind a `--format` flag (default pinned per
major version), and breaking output changes require a new format version, not
an edit to the existing one. Workflow patterns built on these queries live in
the agent-development guide (§12), not here.

**Context packing for agents.** One query mode emits a task bundle: the
spec records for the relevant subgraph plus the code bodies of only those
functions. The agent gets the wiring of the neighborhood and the logic of the
focus area, and nothing else. This is the concrete payoff of the streamable
format: context budget spent on the relevant 40 records, not the whole repo.
(Streamability helps our tooling slice; the model still needs the slice in
context — we claim the former, not magic.)

## 11. Legacy extraction: descriptive, not normative

An agent + static-analysis pipeline can draft specs for existing code
(AST parse → dependency walk → guard-clause lift). This is a genuinely good
use of agents — but the output is a **descriptive inventory**, not ground
truth:

- Dynamic dispatch, reflection, framework magic, and metaprogramming defeat
  static extraction, and they're most common in exactly the legacy code we
  most want to map. Extracted `deps` will be silently incomplete.
- Extraction drops binding-level semantics. `charge({amount: cart.total})`
  becomes a bare edge to `stripe.charge`; the fact that the amount is
  `cart.total` is gone. A spec extracted this way is **not** a sufficient
  basis for regenerating the code.

Rules for extracted records:

- Tagged `"provenance": "extracted"` until a human reviews and promotes them
  to `authored` (§5 — interior records may stay `extracted` indefinitely).
- Descriptions for public-surface records are **agent-drafted, human-approved**
  — the review burden is reading a paragraph and a guard set per public
  function, not writing specs from scratch.
- Used for inventory, hotspot analysis, and strangler-fig routing decisions —
  all tolerant of an approximate map with a human in the loop.
- Migration verification uses golden/shadow testing against recorded
  production traffic, not spec-derived tests.

## 12. Prior art (use it, don't rebuild it)

- **Interface layer:** TypeSpec / Smithy / OpenAPI already solve type
  definition and validation. `deps.input` / `deps.meta` should reference types
  defined in one of these, not a homegrown type system. Recommendation:
  TypeSpec, compiled to JSON Schema for the validator.
- **Guards as dispatch:** Erlang/Elixir function heads — steal the semantics,
  including clause ordering.
- **Flow:** workflow engines (BPMN, Temporal) model continuation explicitly;
  we're doing a lightweight static version, not replacing them.

The one thing here that isn't off-the-shelf is the unification: one streamable
artifact covering deps + guards + flow per function, validated in CI, with a
query layer. That's the whole pitch.

Agent *workflow* conventions built on top of the specs (e.g. "before editing
a function, query its flow targets") are deliberately not part of this brief —
they belong in the agent-development guide that consumes it.

## 13. What this actually buys us

Honest versions of the claims:

- **Cheap structural retrieval** via the query layer and context packing
  (§10).
- **Pre-flight wiring validation.** Dangling references, undeclared
  dependencies, unhandled flow outcomes, ambiguous guards — all caught before
  any code is generated or reviewed.
- **Impact analysis and hotspot detection** as one-line queries instead of
  archaeology.
- **Wiring tests, labeled as such.** From a record we can generate tests that
  verify the function calls its declared dependencies under its declared
  guards. These verify *structure*, not *correctness*. Behavioral confidence
  comes from hand-written tests and (for migrations) recorded-traffic replay —
  never from spec-generated tests alone.

Claims we are explicitly **not** making: zero ambiguity, flawless generation,
100% meaningful coverage, mathematical proof of anything.

## 14. Rollout

**Known risks the pilot is designed to quantify.** Two failure modes would
sink this proposal, and the rollout below exists to measure them, not to
assume them away: (a) **spec tax** — even reduced to "review a paragraph and
a guard set per public function," the authored-record burden proves too high
in practice; (b) **extraction floor** — extraction quality on the worst-case
module is too poor for the graph to be trusted, which caps the whole thing at
friendly-codebase-only. If (a) fails we fall back to inventory-only; if (b)
fails we constrain scope to modules that meet a measured extraction-quality
bar. Neither outcome is a disaster, but we want to know by week 4, not month 6.

1. **Week 1–2: toolchain.** JSON Schema for the record format; `compile_specs`
   with ID, reference, cycle, overlap, and deprecation checks; DOT export.
   Editor support is part of this step and is nearly free: schema-validated
   autocomplete via the stock JSON language server, plus a lint command.
   Pure scripts, no AI involved.
2. **Week 2–3: hand-written pilot.** One small, well-understood module. Write
   specs by hand. Find out where the schema fights reality; amend it.
3. **Week 3–4: extraction pilot, two targets.** The extraction pipeline (AST
   scripts + agent for naming, descriptions, domain assignment) runs against
   *two* modules: the friendliest one we have **and the worst-case one** —
   heaviest framework indirection, most dynamic dispatch. The friendly module
   tells us the ceiling; the hostile one tells us the floor, and the floor is
   what decides whether extraction generalizes. Human review of every
   public-surface record. "Generate spec from this function" falls out of the
   extractor for free.
4. **Then decide:** adopt spec-first for new code, or stop at
   inventory-and-analysis. Both outcomes are wins; the second is cheaper.

**Metrics.** Most plausible-sounding metrics (onboarding time, wiring-bug
counts, PR cycle time) are noisy and unmeasurable at our team size. We track
three that aren't:

1. **Agent A/B via the harness (headline).** Same tasks run as harness cases
   with and without the spec subgraph packed into context; compare success
   rate, steps to completion, and wrong-file edits. The agent harness records
   every run — this is a real controlled comparison, and the most credible
   evidence this proposal can produce.
2. **Extraction-diff failure rate** — how often CI catches spec/code drift.
   A proxy for whether the conformance mechanism is doing its job.
3. **`_custom` ratio per module** — guard-vocabulary pressure (§7), reviewed
   at each checkpoint.

## 15. Open questions for the team

1. TypeSpec vs. JSON Schema directly for the type references — who has
   appetite to own the toolchain (and is that the same person as the schema
   owner in §4)?
2. Dispatch-group boundaries for overlap checking (§7): per bounded context,
   or per transport route? The pilot should force a decision.
3. Where does the `authored`/`extracted` promotion review live — PR review,
   or a dedicated review queue?
