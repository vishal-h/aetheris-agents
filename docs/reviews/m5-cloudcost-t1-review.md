# Review — m5-cloudcost t1

**Format** is `../aetheris/docs/methodology/milestone-methodology.md` §5 → *Review file format
(claude-ui → claude-code)*, in the shape `hc-b-review.md` through `hc-e-review.md` established:
one `## Round <R>` section, appended, never rewritten; reviewer findings verbatim; claude-code's
disposition beneath them. Committed per **R2** and, since R2's own text is scoped to `hc-*`
tickets, on the two unscoped sections R2 grounds itself in — methodology §1 principle 4 and §8.

**Adaptations to the §5 format, named rather than left to be noticed.** The round lives in a
`## Round <R>` section rather than in the H1, so later rounds append to one file — `hc-*`
practice, against the `bl-047`/`bl-049` alternative of a second `-r1` file. The findings are
**not** re-tagged `[blocking]`/`[non-blocking]`/`[question]`: the reviewer's text carries
`APPROVE` and its own F1/F2 labels and no tags, and adding them would be authoring. There is no
`## Cross-ticket notes` section because the reviewer's text carried none — stated here rather
than filled; the reviewer's *"Not findings, recorded because they were done right"* block is
theirs and stays inside the verbatim block under its own heading.

---

## Round 0 — the review of r0 (`5db4585`)

**Raised on:** t1 r0, `5db4585` (agents), harness `2ef0517` untouched. **Answered in:** r1.

### Findings, verbatim

**Verdict: APPROVE, with two findings for r1.** E1–E8 stand and none is re-run. The
step-1 gate produced the round's most consequential finding, and the mid-ticket
ruling that the stop condition is temporal holds.

**F1 — E4's document population is one repo.** E4(6) swept the agents repo's
tracked `.md` files plus `cloudcost/tools.json`. The harness was not swept, and
E2's own positive control establishes that the harness carries files mentioning
cloudcost. A blast radius stated as *every sentence in every document* that covers
one of two repos is a count over a population narrower than its claim. Not material
to a retain ruling; material to a remove ruling — which is why it is closed before
the ruling rather than after.

**F2 — the packet asserted verbatim inlining without a check.** The packet states
its §1 and §2 are inlined verbatim from the committed record and elides the notes
file's diff on that basis. The assertion is unverified. A packet reporting a file is
not the file, and the elision meant the reviewer ratified from the packet rather
than from the artifact. Not a defect in the work — a defect in what the packet can
be trusted to stand for.

**Not findings, recorded because they were done right.**

- The done-check's item 4 substitution. `git status` is structurally blind to
  `cloudcost/output/` and `cloudcost/history/`, both gitignored, so a before/after
  `find -printf` snapshot was taken instead and the substitution was *named* rather
  than left to read as a pass. That is §Promotion candidates' first entry applied
  one round after it was recorded, by the session that had no part in recording it.
- E3's AST pass stating what it structurally cannot see — a list literal bound to a
  variable before the call — and then naming the sites found by reading. A count
  that declares its own blind spot.
- E6's note that a line-scoped grep fails on the *"live at the first fan-out"*
  phrase because it wraps a line break, and that the failure would otherwise have
  read as absence.
- Every route demonstrated by execution rather than only by reading, and the two CLI
  routes shown to converge on a byte-identical payload. The gate asked for a
  derivation; the ticket returned a demonstration.

### Dispositions

**F1 — fixed at r1.** `cloudcost/docs/m5-t1-implementation-notes.md` §r1 → **F1** carries
E4(6)'s eight terms swept over the harness's **full tracked population** (441 files, named by
`git ls-files | wc -l` before searching — wider in kind than E4(6)'s `.md`-plus-one-manifest
population, so a zero is not a filter artefact). **Two hits, both quoted and classified into
the bucket E4(6) itself created for its own two out-of-scope hits** — BL-039's *"cross-provider
forking"* and dirge's *"multi-provider routing"*, both **LLM** providers. **Zero in-scope hits:
nothing in the harness enters either blast radius.** Three positive controls (reach → 8 files,
reproducing E2's list; multi-word → `per provider` 1; `>`-bearing → `>=` 41), plus a `-i` guard
that surfaced one genuine capitalization variant the case-sensitive form misses — also
LLM-provider, also out of scope, so the in-scope count is unchanged. **E4 is not rewritten and
114/24 is retained as r0's agents figure**, with the harness figure placed beside it.

The finding's premise was verified, not assumed: E4(6) does name a one-repo population, and E2
did sweep the harness — for `compose_report_data`, not for this vocabulary.

**F1a — a further defect found while closing F1, recorded not repaired.** E4(6) states its
population as *467* tracked `.md` files under a stamp saying `70addd3`; at `70addd3` the count
is **466**, and 467 is the count at `5db4585` — after r0's own notes file joined the tree. That
file matches the vocabulary on 47 lines yet is absent from E4(6)'s 24-file distribution. Two
readings, and the tree cannot separate them; either way two published figures in one section
disagree by exactly the file the ticket was writing. Settling route named (r0's sweep
transcript, not in the repo). Not repaired, because r1's instruction retains r0's number.

**F2 — fixed at r1, and the finding was right in a way stronger than stated.** §r1 → **F2**
records the strong check rather than the weaker fallback: r0's packet survives as a file, so
its §1 and §2 ranges were diffed byte-for-byte against
`git show 5db4585:cloudcost/docs/m5-t1-implementation-notes.md` — **no diff, matching md5s on
both.** The assertion was true. **The elision's stated basis was not:** §1+§2 carry 577 of the
file's 634 lines, and the file's opening framing — including the **§Measurement stamp**, which
binds every `path:line` in those sections to a commit — appears nowhere in the packet in any
form. The check's boundary is stated: it cannot establish that the on-disk packet is what the
reviewer *received*, which is F2's residue and stays open. The rule is recorded in force for
the rest of the round — *an elision justified by "this is inlined above" carries the check that
establishes it, or the diff is not elided* — and flagged as a §Promotion candidates candidate
for `cloudcost/m5-n1-compose.md` rather than written there, since r1 authorises the t1 row only.

**The four "recorded because they were done right" items** are read and carried; none asks for
work and none is re-litigated here.

**Deviation on this file.** `docs/reviews/m5-cloudcost-t1-review.md` is outside t1's `Touches`
(*"Nothing else"*). Declared in §r1 → §Deviation with its authority: methodology §1 principle 4
and §8, both unscoped, which are the sections **R2** itself invokes. R2's own text binds
*"Every `hc-*` ticket"* and m5 t1 is not one, so R2 is cited as the round-level restatement of a
general rule, not as its source.
