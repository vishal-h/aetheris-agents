# Implementation notes — m7 t4 (docs sync + milestone close)

Ticket: close m7 — drift check, review scan (t1–t3), the one CLAUDE.md learning promotion,
milestone summary. Docs-only.

---

## What shipped

- **`CLAUDE.md`** — `## Learning — m7-docbuilder`: write done-check/sprint commands against the
  **verified** runtime shape, not an assumed one (data structure, export status, arg
  convention). Four instances cited across two milestones —
  `m-docbuilder-m5 t1, m-docbuilder-m6 t4b, m-docbuilder-m7 t2, t3` — so it's a recurring class,
  not a one-milestone fluke. The standalone-only promotion from the t1–t3 scan.
- **`docbuilder/docs/milestones/m7-offer-letter.md`** — `## Milestone summary` appended (pre-t1
  doc correction = methodology working; t2 e2e de-risk narrowing t3's failure surface; the
  fresh→direct trade-off + the m8 open items).

## Review scan (t1–t3, all in `docbuilder/docs/reviews/`)

- t1: F1 CSS cascade (one-off), F2 phone, F3 title, F4/F5 notes, round-2 review-path. No m7
  recurrence.
- t2: F1 `cat["doc_types"]` catalogue structure, F2 logo note. The catalogue-structure item is a
  surface instance of the command-shape class (see below), not its own recurrence.
- t3: F1 stale runbook ref (one-off), F2 OL_HTML persistence (hardened).
- **One promotion:** the **command-shape** pattern — 4 instances (m5 t1 smoke, m6 t4b positional,
  m7 t2 `cat["doc_types"]`, m7 t3 `CAND` env/argv). No other finding recurred across ≥2 m7
  tickets. Promoted to `## Learning — m7-docbuilder`.

## Done-check

- `drift_check.py`: **8 PASS / 0 FAIL / 0 WARN** *before* this commit (t1–t3 touched no
  manifest-tracked file). **After** this commit: **1 `project_knowledge` WARN — `CLAUDE.md`
  ahead of the manifest** (the new learning). Expected, BL-002, human-owned. No FAIL.
- Anchored `^## Milestone summary` in `m7-offer-letter.md` = **1**.
- `## Learning — m7-docbuilder` present in `CLAUDE.md`.
- The milestone doc's t4 done-check had a `docbuilder/docs/runbook.md` manifest-grep snippet —
  wrong path (the runbook is `docbuilder/runbook.md`) AND not manifest-tracked anyway.
  **Corrected in the t4 round-1 review (F1):** replaced the snippet (in both the §t4 Done-check
  block and the prompt step 4) with a `git diff --name-only eeb37a1 HEAD -- <tracked files>`
  check that confirms `CLAUDE.md` is the only manifest-tracked change — same §1.1 doc-hygiene
  fix as the t3 `removal is m7` correction.

## BL-002 (human-owned)

m7 changed exactly one manifest-tracked file: **`CLAUDE.md`** (`capability-matrix.md` and
`docs/rig/runbook.md` unchanged; `docbuilder/runbook.md` is not tracked; m7 added no scripts so
counts are unchanged). Re-upload **`aetheris-agents--CLAUDE.md`** to the Claude.ai project, then
advance the `aetheris-agents--CLAUDE.md` row in `docs/project-knowledge-manifest.md` to this
commit and re-run drift → 0 FAIL / 0 WARN. (Manifest advance is the post-upload step, not done
in this commit.)

## m7 close

t1–t4 complete. The offer letter renders a faithful PDF (primary) + DOCX (secondary) via the
HTML+inline-CSS Jinja2 template; live PASS `docbuilder-orch-iDGIIQ`. One learning promoted. m8
open items recorded in the summary (render_template removal, fresh-path offer_letter coverage,
context-builder optional-field naming, content pixel-fidelity).
