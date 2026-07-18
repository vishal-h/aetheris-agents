# BL-007 / t0 — `caused_by` event lineage field (harness)

**Milestone:** [BL-007 — Fork](./README.md) · **Ticket:** t0 · **Repo:** `../aetheris/` (harness)
**Status:** Ready — D3 ratified 2026-07-18 (`caused_by` folds as t0). Runs in a **fresh**
claude-code session.
**Verified against:** aetheris `19c08be` — field confirmed absent (`grep -rn "caused_by"
lib/ test/` → 0 hits, 2026-07-17 recon/verification pass).

Generated from the committed milestone doc's t0 section (`README.md:115-158`). Scope is
that section verbatim, restructured to the p3 issue-doc pattern — no scope added.

---

## Context

`caused_by` is the roadmap's Horizon-0 lineage field, ordered to land **before** the fork UX
so fork ships with a causal-tree view rather than retrofitting lineage
(`../aetheris/ROADMAP.md:48-53`). Decision **D3** (ratified 2026-07-18) folds *only this field*
into BL-007 as t0 — the rest of Horizon 0 (observation convention, token-cost query) stays on
the roadmap. Reference shape: brief Part 4 / paper Listing 1 — a single nullable pointer;
per-object provenance stays a payload convention.

## Scope

Every trajectory event gains an optional `caused_by` field: a nullable event-id pointer to the
triggering event (`tool_result` ← `tool_called` ← `llm_responded`), `null` for
user/runtime-initiated events. Serialization round-trips it. Existing trajectory files without
the field load cleanly (**back-compat: absent ⇒ nil**). After this ticket, new events *can*
carry causal lineage; nothing is yet required to set it beyond what the ticket wires (fork's
`run_started`-equivalent event should name the fork's causing context if one exists).

## What to build

A Rule-14 **three-place change in one commit**:

1. `../aetheris/lib/aetheris/trajectory/event.ex` — add the optional `caused_by` field
   (nullable event-id) to the event struct per brief Part 4's reference shape.
2. `../aetheris/lib/aetheris/trajectory/file.ex` — serialize/deserialize the field so it
   round-trips through the trajectory map.
3. `../aetheris/docs/aetheris/specs.md` — document the field in the harness-owned schema doc:
   §1 Event Schema typespec + §6 Trajectory File Format JSON. (The original `../aetheris/docs/…
   specs §6` ellipsis is corrected to this concrete path. Note: Rig's `docs/rig/specs.md` §6
   is the drift-checked mirror, but `caused_by` is a top-level field — not an event type or
   payload key — so it is not a drift-checked row; the Rig mirror row lands with t5, see the
   adjudication note in `README.md`.)
4. Matching tests — round-trip assertion + a **back-compat test**: a pre-existing trajectory
   file without the field loads with `caused_by == nil`.

## Touches

- `../aetheris/lib/aetheris/trajectory/event.ex`
- `../aetheris/lib/aetheris/trajectory/file.ex`
- `../aetheris/docs/aetheris/specs.md` (§1 typespec + §6 JSON)
- matching tests

Harness edits are explicit per the cross-repo Touches rule (working dir is `aetheris-agents/`;
this ticket edits the sibling `../aetheris/`).

## Do not generate

**No emit-site sweep across the codebase** — only the field, its round-trip, and back-compat.
Populating `caused_by` broadly is future work.

## Contract refs

- Brief Part 4 (reference shape; paper Listing 1):
  `../aetheris/docs/aetheris/research/activegraph-log-is-agent-2026-07.md`
- Harness rule 14 (three-place change)
- specs §6 (event schema)

## Done-check

```bash
cd ../aetheris && mix test test/aetheris/trajectory/ && mix test && mix hex.audit
cd ../aetheris-agents && python3 scripts/drift_check.py
```

> **Done-check correction (2026-07-18).** `drift_check.py` lives only in `aetheris-agents/`
> (`REPO_ROOT = Path(__file__).parent.parent`; no drift checker in the harness). The original
> single-`cd ../aetheris && … && python3 scripts/drift_check.py` fails file-not-found — verified
> live. The drift step is repo-qualified to run from `aetheris-agents/`.

Include the done-check output in the review packet (done-check block opens the packet).

## Claude-code prompt

> t0, BL-007. Add optional `caused_by` (nullable event-id) to the trajectory event struct per
> brief Part 4's reference shape. Rule-14 three-place change in one commit: event.ex +
> Trajectory.File map + harness specs (§1 + §6). Back-compat test: pre-existing trajectory file without the
> field loads with nil. Run the done-check; include output in the packet. Touch nothing outside
> Touches.

## Sequencing

t0 is first in the milestone (t0 → t1 → t2 → t3 → t4 → t5). It is the roadmap-ordered
prerequisite and unblocks the fork causal-tree view. **Fresh claude-code session**; full
restart after any CLAUDE.md change. Push held for the human; every gate at every boundary.
