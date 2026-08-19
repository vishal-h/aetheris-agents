# ds t1a — the use-case registry (implementation notes)

`Measurement stamp: baselines taken at agents 7841060 / harness 8eb960d, 2026-08-19, both trees
clean and pushed. Every figure below was measured by this session, not carried from stage 1's
packet; where stage 1 and this session agree, that is two derivations, not one relayed.`

Run in two stages. Stage 1 was read-only derivation and wrote nothing to either repository; its
packet is the input to stage 2, which landed the work in two commits. **Stage 2 re-verified
everything it relied on** rather than taking the packet's word: a packet reporting a file is not
the file.

---

## 1. Criterion 5's instrument — was the GitHub Project consulted?

**NO.**

No `gh project` command was run at either stage, and no decision in this ticket was taken by
consulting the Project. `gh issue view 76` was run, because criterion 6's mirror comparison needs
the issue body; its output incidentally prints a `projects:` line, which is the issue's own field
surfacing in an issue read and decided nothing.

**That is now two tickets — ds t0 and ds t1a — answering `no`, and the accumulating answer is
itself the evidence verdict A wants.** The criterion's failure condition is an empty
consulted-list beside a non-empty kept-current list, and each `no` recorded honestly is a data
point toward settling it. Answering `yes` on the strength of an incidental line would make the
criterion unfalsifiable, which is what its own ground forbids.

---

## 2. The four ratified decisions, as landed

| decision | as landed |
|---|---|
| **Criterion** — a surface is in scope iff its enumeration can be extracted by a parser that never has to decide what a sentence means | landed verbatim in `docs/use-cases.md` §What checks this file and in `ds-milestone.md` §t1a's RESOLVED block; stage 1's twenty-six-row application ratified as it stands and not re-applied |
| **Membership** — a directory D ≠ repo root with both `D/tests/conftest.py` and `D/scripts/` | landed in `docs/use-cases.md` §Membership with its reproducing command; **ten** rows, `api` split |
| **Registry** — `docs/use-cases.md`, a markdown table, no manifest row | landed; the no-manifest-row decision is recorded in `ds-milestone.md` §t1a as deferred to the cycle's close on the standing specification test |
| **Capability matrix — option (a)** | `SECTIONS` and the section-agent set are compared against the registry **filtered to agent-bearing use cases**; the predicate is named in the check's own failure message; the ground is stated in `ds-milestone.md` §t1a and in `drift_check.py`'s check comment |

**gc t3's predicate: discharged by the pointer**, landed in `gc-t1-implementation-notes.md` §M.
The scope item says *carrying*, not *re-running*; the census is not re-run, and the notes say so
in the carried-in stamp. Its second half — applying the predicate to t1a's own check — is
discharged **structurally** by the criterion rather than by implementing a predicate, and t1a
says that is why rather than leaving it unmentioned: a markdown table row and a Rust literal
cannot be confused with an enumeration quoted inside a dated correction block, and prose is out
of scope, so no live-vs-quoted distinction is left for the check to get wrong.

---

## 3. Where the four checks live, and why they are not all in one place

The brief had t1a's checks converging on `scripts/drift_check.py`. **One of four does**, and the
divergence is deliberate, on the criterion stage 1 proposed and this session applied:

> A check goes to `drift_check.py` when its subject is the correspondence between a committed
> document and something outside it that the checker must reach, and when a human running the
> doc-sync gate is the person who needs its answer. It goes to `tests/` when it is a property of
> this repository's own tracked content, decidable by reading files, and the person who needs its
> answer is whoever just broke it.

| check | home | ground |
|---|---|---|
| registry ↔ use-case directories | `tests/test_use_case_registry.py` | pure tracked-content property; breaks the moment someone adds a directory, and that person should learn it from the gate they already run |
| registry ↔ `pytest.mark.dormant` | `tests/test_use_case_registry.py` | both sides in this repo; pytest already reads the markers |
| registry ↔ the separable doc enumerations | `scripts/drift_check.py`, one check named `use_case_registry`, **no `strict_exempt`** | doc-vs-source correspondence, which is what the script's other checks are; wants `--check` addressability for an operator reconciling one surface |
| registry ↔ Rig's two `USE_CASE_PREFIXES` | `scripts/check_run_classifier.py` + `tests/test_run_classifier.py` | the guard, its parser and its wrapper already exist and already run in the gate; widening the existing parser is smaller than a new check, and it puts the fix where BL-083 should have put it |

The t0 precedent is the ground for three of the four riding the whole-suite gate: a check that is
a property of tracked content runs on every ticket for free, and a check nobody runs is the
failure mode BL-150's off-territory-gate entry names.

---

## 4. The `use_case_registry` check's nine arms, and the one it deliberately omits

Nine arms, each recording its own finding so a failure names the surface rather than the check.
Two keyings, both stated in the messages that use them: the **matrix keying** (`api/tenant` →
`api_tenant`) and the **sweep keying** (`api/tenant` → `api`, for surfaces that walk top-level
directories). Four arms are **subset** arms by design and fail on an *extra*, never on a
shortfall — `capability-matrix-overrides.json` is sparse by design, `NO_MANIFEST_YET` is a
tracked gap (BL-089), and the `tools.json` set and `tools.rs`'s `vec!` cover the manifest-bearing
subset only.

**Omitted deliberately:** `docs/capability-matrix.md`'s `## ` headings. They are *derived* from
`SECTIONS` and are already asserted against it by `tests/test_assemble_matrix.py`. Checking the
generated output and calling the input verified is the seam this ticket exists to close, so the
check reads `SECTIONS` itself. The omission is stated in the check's own comment rather than left
for a reader to notice.

---

## 5. What the doc edits were, and what was deliberately not edited

Only the edits needed to land the check green. `CLAUDE.md` §Key docs gained a `provenance` row
and split `api (TAP)` into `api/tenant` and `api/gateway`; `README.md` §Use cases gained six rows
and split `api`. Both tables now carry a sentence saying the first column is checked, so the next
reader knows the row set is enforced rather than remembered.

**`CLAUDE.md`'s "Current use cases" sentence was de-numeralised, not fixed.** It is out of scope
for the check by the check's own criterion, and a sentence kept in step by hand is the surface
that went four use cases short without anything noticing. It now points at the registry and
quotes what it used to say as the historical fact it is. Correcting the list in place would have
re-armed the trap for the next use case — the m6-cloudcost de-numeralise rule, applied to an
enumeration rather than a count.

**The doc table parser is structural, not lexical.** It takes the contiguous pipe-row block, drops
the header row and the `---` separator, and reads cell 1 of the rest. A lexical rule — "cells that
look like identifiers" — would have to decide what a heading means, which is exactly what this
check is defined never to do. The first draft was lexical (backticked cells only) and reported
`zero identifiers parsed` against `CLAUDE.md`, whose cells are bare; the fix was to change the
parser rather than to backtick nine table cells to suit it.

---

## 6. The Rig defect, and what it cost

`usage.rs`'s `USE_CASE_PREFIXES` carried the two dead entries BL-083 removed from `RunList.tsx`
and left here, and was missing every group added since. It was **derived from the declared agent
labels**, not copied from `RunList.tsx` — copying one hand-written list into another is what
produced the defect. `check_run_classifier.py` now parses **both** constants, compares them, and
runs its two checks against each; a hand-copied expectation in the guard would have passed while
the real classifier was broken, which is the failure the guard's own docstring already warned
about for the single-constant case.

Figures are in the review packet, measured before and after.

---

## 7. Open, and forwarded

- **No manifest row for `docs/use-cases.md`.** Decided at the cycle's close on the standing
  specification test, as `ds-milestone.md`'s own row is. Recorded in §t1a so it is a deferred
  decision with a stated resolver, not an omission.
- **`agents/capability_matrix_boxy_pipeline.exs` is not authored, and that is a ruling, not a
  gap.** Under option (a) the omission is declared. Authoring it would add planner capability for
  paused work; it is a matrix ticket if anyone wants it.
- **The second consumer of the capability matrix is unserved**, and that is filed on **BL-155**
  as a dated append rather than left in this file — prose in a notes file has no executor.
