# Review — m-tenant-data-layer t1 — round 1

Reviewer: claude-ui
Subject: `tenants/` dir + bitloka data samples + `.gitignore` (commit `3ab125c`)

> Filed at `docbuilder/docs/reviews/`.

---

## Findings

**1. [non-blocking] Fold the `grep -qF` done-check correction into the milestone doc now, not
t5.** §1.1 (as in m7 t2): correct the canonical doc in the commit that found the defect. One-char
fix (`-F`).

**2. [question] The commit trailer reads `Co-Authored-By: Claude Opus 4.8 (1M context)`** — the
project standard was `claude-sonnet-4-6`. If Opus 4.8 was used for the 1M window (long session,
full repo state), that's valid — record it as a session-level decision so t2 onward knows.

## Cross-ticket notes

The `.gitignore` anchoring (leading `/` → `sample/` committed, root real files ignored) is correct
and well-documented in the runbook. The command-shape instance count is now **five** (m5 t1 smoke,
m6 t4b positional, m7 t2 `cat["doc_types"]`, m7 t3 `CAND` env/argv, m-TDL t1 `grep` regex). The
m7 learning is already in CLAUDE.md; this doesn't change the rule but confirms it's still firing —
at t5, consider whether the rule needs a sharper example, or whether the done-check authoring step
needs a **pre-flight habit** (run the check command once standalone before embedding it in a doc).

t1 clean. Non-blocking doc fix, then merge.

---

## Resolution (actioned)

- **F1 — done.** §t1 Done-check step 3 corrected: `grep -q '*.jsonl'` → `grep -qF '*.jsonl'`
  (fixed-string; `-q '*.jsonl'` errors under ugrep where a leading `*` is an empty sub-expression),
  plus an authoritative `git check-ignore` behaviour check added (real ignored, `sample/` tracked).
- **F2 — answered + recorded.** The session runs on **Claude Opus 4.8 (1M context)** (long session
  with full repo state); the harness dictates the matching `Co-Authored-By:` trailer. m1–m7 were a
  Sonnet 4.6 session. Not a mistake — recorded in the t1 implementation notes as a session-level
  decision.

**Carried to t5 (per the cross-ticket note):** the command-shape learning is established but still
firing (5th instance) — note at close whether to sharpen the example or add a "run the check
command standalone before embedding it in the done-check" pre-flight habit.

**Disposition: t1 clear to merge.** F1 (doc) + F2 (notes) actioned; the t1 deliverables
(`tenants/` structure, samples, gitignore, runbook) stand at `3ab125c`.
