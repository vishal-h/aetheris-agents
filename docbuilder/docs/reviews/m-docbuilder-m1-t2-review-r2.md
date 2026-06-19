# Review — m-docbuilder-m1 t2 — round 2

Reviewer: claude-ui
Round 1 findings dispositioned by claude-code at 7763019.

---

## Finding dispositions

| # | Finding | Disposition | Assessment |
|---|---------|-------------|------------|
| F1 | [blocking] t1 impl notes missing | `disagree` — file exists at 895dab2, not in t2 diff | **Accepted.** False positive on my part. The file was committed in the prior session. Reviewer must verify against repo state, not just the diff presented. See cross-ticket note below. |
| F2 | [non-blocking] pipe vs temp-file inconsistency | `fixed` — note added to t2 impl notes clarifying both forms valid; pipe preferred for t3+ | ✅ Resolved. |
| F3 | [non-blocking] count semantics undocumented | `fixed` — added to template-schema.md §Aggregate | ✅ Resolved. |
| F4 | [question/doc gap] bold/align absent from column spec | `fixed` — one-liner added to doc-spec-schema.md §Column | ✅ Resolved. |

---

## Status

**Zero blocking findings remaining.** t2 is clear to merge and t3 is clear to start.

---

## Cross-ticket notes

- **F1 was a reviewer error — false positive.** Root cause: reviewed the diff only, did not verify repo state before flagging absence. This is the "reviewer-claims-verified" anti-pattern from aetheris--CLAUDE.md: *"When a reviewer states that a behaviour 'is correct' or 'matches the spec,' verify it against the actual source."* The inverse applies equally — when a reviewer states something is *absent*, verify that too. Candidate for CLAUDE.md learning promotion if it recurs: **"Before flagging a missing file as blocking, verify it is absent from the repo, not just absent from the diff in front of you."**

- The t2 implementation notes (both the original and the round-2 addition) are now a solid reference for t3–t7 renderer authors. Specifically: pipe form is preferred, `-` stdin is supported, aggregate store re-computes on demand from raw rows.

- t3 (generate_xlsx.py) is the first renderer. The doc-spec-schema.md is now complete and unambiguous — renderers read cell-level bold/align, column-level type for number formatting, and header_row for placement. No open questions going into t3.
