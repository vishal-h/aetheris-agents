# m1-cloudcost — milestone close, §7 promotion pass

**Milestone:** m1-cloudcost (t1–t5), closed 2026-07-29.
**Author of the wording:** claude-ui. **Committed by:** claude-code.
**Status:** ratified by the human, 2026-07-29.
**Lands in:** `../aetheris/CLAUDE.md` → *Continuous learning* → *Workflow patterns*.

This file exists because promotion wording travels as a review-file artifact, not as chat —
the BL-007 t5 rule, whose own mechanism failed twice in that milestone's promotion pipeline
when the authored wording lived only in conversation.

---

## 1. Silent-wrong-answer — **rewrite, not a sibling**

**Why a rewrite.** The class recurred as *blocking* at t1 (vacuous import check), t4 (the
"not a failure" test that never ran the failing level), t5 (non-hermetic sprint), plus the
token-check typo — each caught at **review**, never prevented at **authoring**. §7's own test
reads a class recurring as blocking as evidence the promoted wording was too vague, so this
replaces the entry's body rather than adding a fifth sibling beside it. The prior Source
lineage is preserved verbatim and the m1 entries appended.

Wording as ratified:

> **Silent-wrong-answer (supersedes Vacuous-exercise; rewritten at m1-cloudcost close — the
> class kept recurring as blocking under the prior wording, which §7 reads as too vague, so
> this replaces the body rather than adding a sibling).**
>
> A mechanism that returns a well-formed value where a gap exists is asserting, not reporting.
> The prior wording — "ask what it would look like if broken; if identical, it verifies
> nothing" — is the right *diagnostic* but did not stop the vacuous checks being *authored*:
> across m1 they were written happy-path-only and caught downstream at review, ticket after
> ticket. So the rule is now operational, and it binds the author, not the reviewer:
> **construct the broken state and watch the check fail in it, as part of writing the check.**
> A check you have only ever seen pass is not yet a check — run it once against the state where
> the thing it guards is broken, confirm it fails, then restore. That is the mutation test,
> owed by the author of every check, guard, asserted value, and displayed figure.
>
> The carriers are wider than the prior list (fallbacks, windows, non-validating providers,
> all-modules-loaded envs, summary headlines). m1 added four, each passing identically broken
> and working:
>
> - **Stale/leftover artifacts from a prior run.** A `-f report.html` check and an orphan-count
>   read both greened on the *previous* run's gitignored output; a sprint is not hermetic until
>   it clears the state its own checks read (reset accumulating fixtures — m3). "It passed" in
>   a workspace that ran before proves nothing about a re-run where the agent failed.
> - **A reference that resolves to empty for a reason unrelated to the condition.**
>   `[ -z "$DO_TOKEN_ECHO" ]` is always true because the variable is misspelled;
>   `python3 -c "import cloudcost"` from the repo root always succeeds via namespace packages,
>   and would succeed for a genuinely colliding name too. The check tests the typo, or the cwd
>   — not the thing it names.
> - **A cross-cutting aggregate one path guards and its siblings don't.** `grand_total` withheld
>   the cross-currency sum; `mom_delta.current_total`, the orphan band subtotals, and the
>   untagged total did not — one defect at four sites, one guarded. Enumerate every site of a
>   class before trusting the one you fixed (see Adjacent-case).
> - **An LLM computing a value inside a generated artifact nobody recounts.** The
>   capability-matrix assembler counted the rows, the tools line, and the overlap report by
>   model — wrong twice, differently, on identical input; well-formed and plausible, so
>   authoritative until someone counted. Derived values come from a script with a test
>   asserting claimed == counted (D3 / BL-067).
>
> The through-line: well-formedness is exactly what lets a wrong answer survive review, so the
> author owns proving the check can fail before it is trusted.

---

## 2. Secondary candidates — **Source-line additions, not rewrites**

Both accepted as additions. Neither existing rule's body changes: each already states the
invariant, and m1 supplies fresh instances rather than a correction.

**Binds-by-invariant-not-sketch / Cited-means-read** — three m1 instances appended:
the milestone's `pydo` default-pickup claim was false (it is `doctl` that reads
`DO_TOKEN`/`DIGITALOCEAN_ACCESS_TOKEN` by default); `agents/capability_matrix.exs` did not
exist, and the generated artifact's own header pointed at that ghost; §t5's `:rolling`/6
contradicted the agent-creation guide's own `:full`-under-~10-steps rule. Each time the
ticket's *invariant* held and its *sketch* did not.

**Adjacent-case and load-bearing coincidence** — two m1 instances appended: the cross-currency
guard present at one of four aggregate sites, and the t5 r0 F2 widening (reviewer named the
unique-tools line; the whole Step-2 derived block — tools line *and* the never-checked Overlap
Report — was the same class).

**Claude-code's call on the borderline** (delegated by the reviewer): the operational shape
*"when you find a defect, enumerate every site of that exact class before filing the first
one"* stays a **Source addition to Adjacent-case, not a standalone rule**. It is the same
invariant that rule already carries — "a fix's blast radius is one case wider than the case it
was written against" — and splitting it into a sibling would repeat the proliferation error
§7's rewrite test exists to prevent. The Silent-wrong-answer rewrite cross-links it
(`see Adjacent-case`) from the aggregate-carrier bullet, so the shape is reachable from the
rule most likely to be read at authoring time without a fifth entry to keep in sync.

---

## 3. Not promoted

Nothing else cleared §7's ≥2-ticket bar. The m1 findings not listed above were single-ticket
and are recorded in their own review files and implementation notes.
