# §7 promotion commit — implementation notes

**Commits:** aetheris `1ebe971`, aetheris-agents `c2729ac` (+ this closeout).
**Batch:** b1–b3, 2026-07-21.

Written per the promotion review's F26. The reason for these notes is the reason the
m1 rule gives, and it binds harder here than on a docs ticket: this commit's *why*
lives across five artifacts — the draft, the adjudication, two chat-ratified
deviations, and one mid-flight formatting ruling — and nothing else stitches them
together. A future session reconstructing the promotion from the two CLAUDE.mds alone
sees six edits and no reasons.

## Artifact chain

| Artifact | Commit | Status |
|---|---|---|
| §7 promotion draft (claude-ui wording) | `dcce608` | record; **two blocks superseded**, do not sync |
| Adjudication — six answers | `bb90254` | **source of truth** for the promoted wording |
| Harness CLAUDE.md edits (4) | `1ebe971` | shipped |
| Agents CLAUDE.md edits (2) | `c2729ac` | shipped |
| Round-1 promotion review | this commit | `bl-batch-2026-07-promotion-review.md` |

The draft is a record of what was *proposed*. Q2 and Q5 depart from it deliberately;
re-deriving from the draft reintroduces the two errors the adjudication exists to fix.

## The edit set — six, not five

| # | Repo | Edit | Authority |
|---|---|---|---|
| 1 | harness | **Vacuous-exercise** → **Silent-wrong-answer** | Q1 |
| 2 | harness | **Reviewer-claims-verified** → claims+mechanisms rewrite | Q5 |
| 3 | harness | **Adjacent-case and load-bearing coincidence** (new) | Q3 |
| 4 | harness | Repos-rule mirror `CLAUDE.md:5-8` → Q2 wording | **operator, mid-session** |
| 5 | agents | Repos rule `CLAUDE.md:22` → Q2 wording | Q2 |
| 6 | agents | gate-before-action → riding cross-repo done-check clause | riding clause |

Edits 1 and 2 **delete the rule they supersede in the same edit**. A rewrite that
leaves the original standing produces two rules where one was too vague — the failure
the m1 pair already demonstrated, and the reason the adjudication states this as a
condition on the commit rather than a preference.

**Edit 4 is the one not in the adjudication's net-effect table.** It was authorised in
session before any edit was made, on the grounds that the harness carries its own
mirror of the Repos rule; amending only the agents copy would leave the harness stating
the pre-amendment rule — the decay named by BL-007's correction-chasing rule. Ratified
in the round-1 review ("ratified, already was"). If a future reader diffs the commit
against the net-effect table and finds an extra edit, this is it.

## The two departures from the draft, in one line each

- **Q2** — the draft proposed promoting to the harness and relying on the existing
  cross-repo sentence for reachability. The adjudication kept the file and fixed the
  *mechanism*: the sentence is an unenforced manual step that demonstrably did not fire
  (BL-031 was a cross-repo ticket whose session never opened the harness CLAUDE.md).
  Widened to any cross-repo *or packet-producing* session, and "at session start" →
  "before the first edit", which is checkable.
- **Q5** — the draft weighed class 3 against **Cited-means-read** and proposed a
  standalone rule. Wrong neighbour: **Reviewer-claims-verified** already owns that
  family and stops one step short (it binds reviewer *claims*, not reviewer *suggested
  fixes*). Folded in as a rewrite instead. The draft's own mis-homing is instance five
  of the class it was describing, and is cited in the promoted rule's Source line.

## Done-check method — reusable, and the reason to reuse it

Preserved here as a pattern for any future CLAUDE.md-touching or verbatim-transcription
commit. Script: `verify_promotion.py` (scratchpad, not committed — it is specific to
this block set; the *method* is what carries).

1. **Extract, don't retype.** Blockquote runs are parsed out of the adjudication file
   programmatically. Nothing was hand-copied into the checker, so the checker cannot
   inherit a transcription error from the same hands that made one.
2. **Normalised byte comparison.** Whitespace collapses on both sides (blocks are
   re-wrapped when pasted into a differently-formatted file); everything else compares
   byte-for-byte. Not grep-presence, not a paraphrase check.
3. **Mutation self-test.** A deliberately corrupted copy of one block must *fail* to
   match. Without this the whole script could pass by matching nothing — a green result
   identical to the broken case, which is precisely what rule Q1 promotes against.
4. **Shape-checked deletion, not absence.** `Vacuous-exercise` must appear exactly
   twice, both inside the superseding rule (its name and its Source line). Asserting
   mere absence would pass trivially and would also wrongly fail once the superseding
   rule cites the name it replaces.
5. **Cross-repo by construction.** Both files are loaded and each span is asserted
   against the repo that owns it. A one-repo verification of a two-repo change is the
   riding clause's own subject; the check refuses to be that.

One defect found and fixed mid-check: the result lines printed the wrong repo label for
every row (a `split` index error), so the output read identically whether the repo
routing was right or wrong. Caught and corrected before the result was trusted — noted
because it is a small live instance of the class, inside the check for that class.

## Standing rulings recorded so they are not re-asked

- **Verbatim beats local convention.** The promoted blocks carry `` `Source:` ``
  backticked on its own line; older neighbours in the same harness section carry it
  inline and unbacticked. The adjudicated artifact's shape won.
- **Normalising the older neighbours up to the new shape: declined**, standing. It is
  cosmetic churn in the two files with the highest blast radius per edit — each edit
  forces a full session restart downstream. If that section ever takes a structural
  edit for substantive reasons, normalise opportunistically then.
- **Full-restart rule is in effect twice over.** Both CLAUDE.mds changed here. Every
  subsequent session — including the manifest-regen session — is post-edit and must be
  *fresh*, not this one continued.

## Forward

The export boundary is unblocked once this closeout is pushed. Manifest regen is the
final commit **of the export**, from a fresh session — not simply "the batch's last
commit", which is how this line first read and was wrong: *every manifest-tracked edit
must precede the manifest write* (backlog rows, the drift-baseline append, anything
else being exported). Following `prompts/bl-002-refresh-project-knowledge.md` literally
reproduces **BL-034**, whose closing constraint appends a drift-baseline line to
`docs/rig/current-state-2026-06.md` — a file the manifest tracks — after the manifest
is written, so that row is born stale (it fired in production at the 2026-07-17 export,
`628f15f` recording `current-state` two commits behind). Fix BL-034 first or
hand-sequence around it as BL-007 Phase B did, but choose deliberately. The regen
clears all seven staleness WARNs (both CLAUDE.mds, both runbooks, the determinism
contract, backlog, specs). Both
CLAUDE.mds joined the stale set as predicted at commit time — the harness one was not
stale before `1ebe971`, which is what made the prediction checkable.
