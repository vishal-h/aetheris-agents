# BL-041(a) — §7 promotion draft (for human approval)

**Status:** LANDED — `aetheris-agents/CLAUDE.md`, 2026-07-25 (§7, human-ratified). Both edits
applied verbatim in the doc-sync section; Edit 1 placement resolved to the doc-sync strict-mode
exemption (see the placement correction below), which the human ratified. On record here per the
transport rule (§7 wordings land as review-file artifacts, not chat).
**Target:** `aetheris-agents/CLAUDE.md` — a learning-section rule + a one-line reconciliation of
the doc-sync section.
**Drafted:** 2026-07-24 by claude-ui, against the CLAUDE.md at `c2729ac` (project-knowledge copy;
no CLAUDE.md change has landed since b1–b3, so this is current — **claude-code confirms the exact
"When to run" text at HEAD before applying**).
**⚠ Restart boundary.** This edits a CLAUDE.md learning section. Per the standing rule, once it
lands there is a **full restart**, and any packet-producing session predating it is stale by
construction — **this claude-ui session included**. So this draft is the last artifact this
session produces; a fresh claude-ui session picks up the manifest/export afterward.

---

## The class, and why it promotes now

**Pre-commit-drift / Silent-wrong-answer-in-gate-ordering.** A `drift_check --strict` run *before*
committing a manifest-tracked edit is vacuous as a done-check: check 8 (`project_knowledge`)
compares the manifest against **committed history** (`git log -1 --format=%h -- <file>`), so run
pre-commit it reads the file's *pre-edit* hash and cannot see the staleness the edit introduces.
It passes green where a gap exists — the Silent-wrong-answer class, in gate-ordering form.

Countable at 2, recorded not self-promoted; its promotion vehicle is this ticket:

- **BL-034 (`fe8298c`)** — the export-prompt self-staling ordering hazard: real but **latent,
  never fired**. Its earlier "fired in production at `628f15f`" claim was **withdrawn as false**
  after a clean check-8 sweep of all 38 committed manifests. (Separate loose end, not this rule's:
  the withdrawn `628f15f` born-stale narrative still sits in the manifest and must not be copied
  forward at the next export.)
- **BL-025 (`8021a59` / `00ddd34`)** — the vacuity actually **fired, on the caveat's own author**:
  BL-025's pre-commit gate reported **1 WARN**, post-commit **3**. The two it missed were staleness
  its own commit introduced, invisible to a pre-commit check 8.

---

## Edit 1 — new rule (methodology §7 format)

Placement: in `aetheris-agents/CLAUDE.md`'s **"Definition of done — doc sync"** section,
**immediately after the strict-mode exemption paragraph** (the `--strict` / `project_knowledge`
exemption the rule's text points at with "the strict-mode exemption above"). This keeps BL-041(a) a
single-repo agents edit, co-locates the rule with the drift/manifest procedure it extends and with
Edit 2, and makes the done-check WARN land on `aetheris-agents--CLAUDE.md` — the file the done-check
names.

> **Correction (review):** the first draft anchored this "after the **Silent-wrong-answer** rule" —
> but that rule lives in the **harness** `aetheris/CLAUDE.md`, not this repo. Anchoring to it would
> have made BL-041(a) a two-repo edit, dangled the "exemption above" cross-reference, and put the
> manifest WARN on the wrong file. A cross-repo mis-anchor (sibling's-shape ≠ this-file's-shape),
> caught in review. The rule's *conceptual* reference to the Silent-wrong-answer class is kept and
> made explicit — both CLAUDE.md learning sections are read together, so the named class is
> discoverable across the seam.

Ready to insert verbatim:

> **A manifest-staleness done-check runs post-commit — a `drift_check --strict` before committing a
> manifest-tracked edit is vacuous.** Check 8 (`project_knowledge`) compares the manifest against
> committed history (`git log -1 --format=%h -- <file>`), so run *before* the commit it reads the
> file's pre-edit hash and cannot see the staleness the edit introduces — it passes green where a
> gap exists (the **Silent-wrong-answer** class — harness `CLAUDE.md` — in gate-ordering form). Run the `--strict`
> done-check *after* the commit that touches a manifest-tracked file, when check 8 can compare the
> new commit hash against the manifest; then **name** the exempt `project_knowledge` staleness
> WARNs rather than chasing them (mid-cycle staleness is expected truth, cleared only at the export
> boundary — the strict-mode exemption above). Checks 1–7 (source-vs-doc) remain valid pre-commit;
> it is check 8's committed-history dependency that forces the ordering.
> `Source: BL-034 (fe8298c — the export-prompt self-staling ordering hazard, real but latent; its "628f15f production-fired" claim withdrawn as false after a clean check-8 sweep of all 38 committed manifests), BL-025 (8021a59/00ddd34 — the vacuity fired on the caveat's own author: pre-commit 1 WARN, post-commit 3).`

---

## Edit 2 — reconcile the doc-sync "before committing" line

Without this, the doc contradicts itself — the "Definition of done — doc sync" section says the
check is run *before committing*, and the new rule says the manifest-staleness portion runs
*post-commit*. A silent internal mismatch is exactly the class being promoted, so it is closed in
the same edit.

**Before** (verbatim, "Definition of done — doc sync" → "When to run"):

> **When to run:** after any Rig milestone, after adding commands, event types, env vars,
> routes, or DB tables. Zero FAIL findings and zero WARN findings required before committing.

**After:**

> **When to run:** after any Rig milestone, after adding commands, event types, env vars,
> routes, or DB tables. Zero FAIL findings and zero *unexplained* WARN findings required — for a
> **manifest-tracked** edit the `project_knowledge` (check 8) portion is meaningful only
> **post-commit** (it reads committed history; see the learning rule below), so run the `--strict`
> done-check after that commit and name the expected `project_knowledge` WARNs. Checks 1–7 remain
> valid pre-commit.

*(Uses "unexplained WARN," aligning this line with the strict-mode section's already-stated
invariant — "zero *unexplained* WARNs, not zero WARNs" — rather than the flat "zero WARN," which
the exemption already contradicts.)*

---

## What this draft does not change

- The strict-mode section's `project_knowledge` **exemption** and its rationale — unchanged; the
  new rule *cites* it, adding only the ordering insight (post-commit), which it did not carry.
- Any other learning rule, the drift checks themselves, or `drift_check.py`. This is doc/rule only.
  (The tooling guard — making the vacuity mechanically detectable — is **BL-041(b)**, deferred and
  batched with BL-036; out of scope here.)

---

## After ratification — the sequence

1. claude-code commits Edit 1 + Edit 2 to `aetheris-agents/CLAUDE.md` (this is the promotion commit;
   §7 draft on record here first, per the transport rule).
2. **Full restart.** This claude-ui session is stale from that commit; a fresh session takes over.
3. The fresh session runs the manifest/export (BL-002-style refresh) — whose own done-check the new
   rule now governs (`drift --strict` **post-commit**) — and authors the `628f15f` narrative fresh
   so the withdrawn born-stale claim is not copied forward.

Push held.
