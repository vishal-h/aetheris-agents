# §7 promotion commit — review

Reviewer: claude-ui. Subject: the b1–b3 §7 promotion commits — aetheris `1ebe971`,
aetheris-agents `c2729ac`. Adjudication under promotion: `bb90254`.

The draft (`dcce608`) and adjudication (`bb90254`) files are *records*; this is the
review file for the promotion itself.

---

## Round 1 — 2026-07-21

**Packet integrity: conforms**, and the done-check is the class-1 rule applied to the
commit that promotes the class-1 rule — the mutation self-test (a corrupted block must
*fail* the comparison, proving the comparison can fail) and the shape-checked deletion
(`count == 2`, both inside the superseding rule, rather than mere absence "which would
pass trivially") are exactly the two properties that distinguish a verification from a
well-formed assertion. The self-demonstration (both learning sections read before first
edit, with line ranges, stated as required) closes the loop on Q2's own requirement.
This is what the batch's rules look like when they're load-bearing rather than
decorative.

### Dispositions on the three flags

1. **Adjudication table slip — accepted as resolved; one line of correction-chasing
   owed.** Following repo-truth + brief over the table row was right. But `bb90254` is
   committed and pushed with a false location claim in its net-effect table, and the
   correction-chasing rule doesn't exempt adjudication files: a future reader
   reconstructing this promotion from the adjudication alone inherits the slip. Fix:
   one-line erratum appended to the adjudication file — in the closeout commit, not a
   rewrite of the table (the file is a record; errata are how records get corrected
   without misdating them, per the BL-016 / milestone-README precedent).
2. **Sixth edit — ratified, already was.** The mid-session authorization is on the
   record; the packet's restatement is correct transport. No residue.
3. **Formatting divergence — verbatim-over-local was the right precedence** (substance
   rules bind harder than shape rules, and the FINAL WORDING blocks were the adjudicated
   artifact). Normalising the older neighbours *up* to the new shape: **declined as a
   task** — cosmetic churn in the two files with the highest blast radius per edit, each
   edit costing a session restart downstream. Recorded as the standing answer so it
   isn't re-asked; if the section ever gets a structural edit for substantive reasons,
   normalise opportunistically then.

### Finding

26. **[non-blocking — take the invitation]** Write the implementation-notes file. The
    open item's framing is exactly backwards in one respect: the m1 rule's *reason* —
    the notes are how a future session reconstructs why, not just what — applies *more*
    to a §7 ritual commit than to a docs ticket, because this commit's why lives across
    five artifacts (draft, adjudication, two chat-ratified deviations, one mid-flight
    format ruling) that nothing currently stitches together. The notes file is that
    stitch: the edit table, the six-plus-one edit list with the mirror's ratification
    pointer, the two departures' one-line summaries, the done-check method (mutation
    self-test + shape assertion, worth preserving as a reusable pattern for future
    CLAUDE.md-touching commits), and the format-precedence ruling.

### Verdict

**Zero blocking findings.** F26 + the erratum are one small agents-side commit. Then
push both repos — harness `1ebe971`, agents `c2729ac` plus the closeout commit. The
export boundary is then fully unblocked: manifest regen as the batch's final commit
(clearing all seven WARNs), push, then remove-all/upload-all.

### Note for the record

The full-restart rule is now in effect *twice over* — both CLAUDE.mds changed in this
commit. Every subsequent session, including the one that does the manifest regen and
the one that eventually picks up BL-025-or-BL-008, is post-edit and takes fresh state by
construction. The regen session needs no learning-section depth, but it must be *fresh*,
not this one continued.

### Resolution

F26 taken: `docs/rig/milestones/bl-batch-2026-07-promotion-implementation-notes.md`
(landed first at `docs/reviews/bl-batch-2026-07-promotion-notes.md` in `c3296c4`; moved
to the milestones convention by the closeout ticket). Erratum appended to
`bl-batch-2026-07-section7-adjudication.md`. Both in the closeout commit below.
