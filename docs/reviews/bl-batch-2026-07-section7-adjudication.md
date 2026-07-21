# §7 promotion draft — adjudication

**Adjudicated by:** claude-code, 2026-07-21, on delegation from the human operator.
**Draft adjudicated:** `docs/reviews/bl-batch-2026-07-section7-draft.md` (`dcce608`,
committed byte-identical to claude-ui's authored wording, md5 `1800dbeb…`).

Two of the six answers depart from the draft's stated assumption (Q2 and Q5). Both
departures are flagged as such rather than folded in silently; the human can overrule
either without re-reading the draft.

**The promotion commit takes the FINAL WORDING blocks below verbatim.** Where a block
says *replaces X*, the promotion commit deletes X in the same edit — a rewrite that
leaves the original standing produces two rules where one was too vague, which is the
failure the m1 pair already demonstrated.

---

## Q1 — Class 1: rewrite-and-replace, not a neighbour. **Rewrite.**

The draft is right that this is a rewrite of **Vacuous-exercise**, and right about
why: five of eight faces were not exercises. But a pure generalisation would lose the
one thing that made Vacuous-exercise operational — the *concrete* instruction to
assert both halves. The rewrite therefore keeps the generalised test as the headline
and Vacuous-exercise's imperative as its concrete form.

Stated plainly: this widens the rule's subject from "an exercise" to "any mechanism
that reports," and keeps the imperative unchanged for the exercise case.

### FINAL WORDING — replaces **Vacuous-exercise** in the harness CLAUDE.md

> - **Silent-wrong-answer (supersedes Vacuous-exercise).** A mechanism that returns a
>   well-formed value where a gap exists is asserting, not reporting. Before trusting
>   any green result, displayed value, or summary line, ask what it would look like if
>   the thing were broken; if the answer is "identical," it verifies nothing and the
>   gap case must be exercised explicitly. For a check or sprint exercise this is the
>   original concrete form: assert both that the mechanism engaged *and* that it
>   prevented the behaviour it exists to prevent — an exercise with only a happy-path
>   check is half an exercise, and one that cannot fail to pass is not an exercise.
>   The recurring carriers are fallbacks, windows, non-validating providers,
>   all-modules-loaded test environments, and summary headlines: each degrades to a
>   confident wrong answer rather than a visible gap, and well-formedness is exactly
>   what lets it survive review.
>   `Source: m-playground-p2 t4/t5 (original Vacuous-exercise); BL-029 (COALESCE label fallback, 596 runs); BL-038 (LIMIT window read as the whole store); BL-039 (stub-green fork e2e; fourteen empty-queue "successes"); BL-029 batch r2→gate (a "CLOSED" headline over an unevidenced arm); BL-031 r2 §1c (suite green while the harness crashed on boot — test env structurally unlike the operator's); BL-040 (a deserialiser accepting a type the spec denies, silently); post-push 2026-07-21 (cross-repo claim verified against one repo).`

---

## Q2 — Home repo: **harness CLAUDE.md, but the reachability mechanism is broken and the promotion commit must fix it.** Departs from the draft.

The draft proposes harness CLAUDE.md, reachable from the agents repo via the
cross-repo rule. I agree on the file and dispute the reachability, with evidence from
this session.

**The evidence is my own non-compliance.** `CLAUDE.md:22-24` (agents) says: *"Cross-repo
milestone sessions read **both** repos' CLAUDE.md learning sections at session start —
promoted rules live in one repo only and are not otherwise reachable from the other."*
BL-031 was a cross-repo session by its own ticket text ("all edits harness-side"). **I
did not read the harness CLAUDE.md at session start.** I first opened it during this
adjudication, three review rounds after the work was done. Vacuous-exercise,
Cited-means-read, Demonstration-not-citation and Complete-output were therefore absent
from my context for the entire ticket — including while I was writing packets those
rules govern, and while §1f was reproducing Complete-output's exact failure with
`tail -3`.

That is not an argument for moving the rule. It is an argument that the rule which
makes one-repo promotion safe is an unenforced manual step, and it did not fire. The
agents CLAUDE.md is loaded automatically every session (it is the working directory);
the harness one is loaded only if someone remembers. Promoting to the harness repo and
relying on the existing sentence promotes into a file the next session will probably
not read.

Keep the file (cohesion: the review-discipline block — Vacuous-exercise,
Cited-means-read, Demonstration-not-citation, Complete-output, Reviewer-claims-verified
— belongs together, and splitting one member out is worse than the reachability gap).
Fix the mechanism instead, in the same commit.

### FINAL WORDING — amends the Repos rule, agents `CLAUDE.md:22-24`

> **Cross-repo sessions, and any session that will produce a review packet, read
> *both* repos' CLAUDE.md learning sections before the first edit** — promoted rules
> live in one repo only and are not otherwise reachable from the other. This is a
> first-action step, not a background intention: BL-031 was a cross-repo ticket whose
> session never opened `../aetheris/CLAUDE.md`, so the entire review-discipline block
> was absent while three review packets were written against it, and Complete-output
> was re-broken (`tail -3`, BL-031 §1f) by a session that had never read it. If you
> have not read the sibling's learning sections, you have not started the ticket.

*(Two changes: "milestone" → any cross-repo or packet-producing session, since BL-031
was a backlog ticket and would have been exempt on a literal reading; and "at session
start" → "before the first edit", which is checkable.)*

---

## Q3 — Class 2: **keep unified.**

Two imperatives, one diagnostic move: *the truth is not where the diff is.* Splitting
gives two rules of two faces each, weakens both, and adds a "which one applies here?"
hesitation at exactly the moment someone is about to ship. The draft's own evidence
settles it — §1c's fix direction was chosen by reasoning from the unified wording
before it was promoted. A rule that already steered a live decision in its draft form
does not need splitting for actionability.

Vagueness is what §7 punishes, and this wording is not vague: it names a concrete
action ("enumerate the adjacent cases"; "name any coincidence the current behaviour
depends on") and a concrete reason the usual safeguard misses it.

### FINAL WORDING — new rule in the harness CLAUDE.md, beside the review-discipline block

> - **Adjacent-case and load-bearing coincidence.** A fix's blast radius is one case
>   wider than the case it was written against. Before shipping a fix or a refactor,
>   enumerate the adjacent cases that share its syntax but not its semantics, and name
>   any coincidence the current behaviour depends on. Removing a coincidence that was
>   doing real work is a regression that diff review structurally cannot see, because
>   the break is in code the diff never touched — and the test suite may not see it
>   either, if the suite's environment is the thing supplying the coincidence.
>   `Source: BL-029 F9 (label≡run_id was the UI's only run_id display); BL-028 r2 F1 (map-valued results truthy past a nil guard); BL-031 r2 F18 (paused runs quiet-by-design inside an inactivity frame); BL-031 r2 §1c (a literal atom in sweep.ex was the sole reason event deserialisation worked at boot; moving it crashed the harness on start, invisibly to a green suite).`

---

## Q4 — Home for Class 2: **harness CLAUDE.md**, same as Q1, covered by the Q2 amendment.

Three of four faces are harness-side and the fourth (BL-028) is too. No split.

---

## Q5 — Class 3: **fold into Reviewer-claims-verified, not Cited-means-read.** Departs from the draft.

The draft weighs class 3 against **Cited-means-read** and proposes standing alone. It
compared against the wrong neighbour. The harness CLAUDE.md already carries:

> **Reviewer-claims-verified.** When a reviewer states that a behaviour "is correct"
> or "matches the spec," verify it against the actual source — reviewer wording is
> contract text like any other and gets confirmed in the next round, not trusted on
> faith. `Source: m-playground-p2 t0/t1/t4 reviews.`

That is class 3's mechanism exactly, one step short: it binds reviewer *claims* and
stops before reviewer *suggested fixes*. Cited-means-read is about citations standing
in for reading — a different failure. Standing class 3 alone would put a third rule
next to two that already overlap it.

There is a small irony worth stating, since it is the class's own content: the draft
matched "reviewer" + "verify" to the nearest rule carrying that vocabulary
(Cited-means-read's reviewer clause) without checking which rule actually owns the
family. That is instance five of the same mechanism, and the first one not authored by
claude-ui — which is the real reason Q6 resolves the way it does.

### FINAL WORDING — replaces **Reviewer-claims-verified** in the harness CLAUDE.md

> - **Reviewer-claims-verified — and reviewer *mechanisms* verified.** Reviewer wording
>   is contract text like any other: a stated behaviour ("this is correct", "this
>   matches the spec") gets confirmed against source, not trusted on faith. The same
>   applies, more strongly, to a suggested fix. **A finding binds by its invariant, not
>   by its sketch** — verify any proposed mechanism against the full writer/consumer
>   family before adopting it, and implement the invariant when the two disagree. The
>   recurring failure is a single one: a word matched the vocabulary of the right
>   family without belonging to it, so the sketch named something that does not exist
>   or does not apply. Every observed instance had a holding invariant and a failing
>   sketch, and implementing the invariant produced the correct fix each time. A
>   sketch that survives this check is worth following; one that does not is worth
>   saying so in the packet, with the family that disproves it.
>   `Source: m-playground-p2 t0/t1/t4 (original, claims side); BL-029 r1 F1 (--label inferred; the flag is --name); BL-028 r2 F1 (third-|| arm under-covered the map shape); BL-031 r2 F18 ("paused" is not a run status — the match would have been dead code beside a green test); BL-031 F23 (RunConfig mode union ≠ Event type union); and this batch's §7 draft itself, which matched class 3 to Cited-means-read rather than to this rule.`

---

## Q6 — The single-author sentence: **strike from the promoted wording.** Keep it in the review record.

Three reasons, in order of weight:

1. **It is wrong by the time it is read.** The fifth instance (the draft's own
   mis-homing, above) is not claude-ui's. "All four were the reviewer's" would be
   promoted already-false.
2. **Attribution is noise at the point of use.** A session in 2027 reading this rule
   has no idea who claude-ui was; the sentence costs a clause and buys nothing for the
   person deciding whether to follow a suggested fix.
3. **It reads as blame in a rule whose purpose is to license pushback.** The rule works
   by making challenge routine and expected. Naming a culprit makes challenge feel
   personal, which is the opposite of the intended effect.

The calibration value is real and is preserved where it belongs: the review files and
the draft (`dcce608`) both record the ledger, with authorship, permanently.

---

## Riding clause — accepted as drafted

The cross-repo done-check sharpening is accurate and lands as drafted, appended to the
existing gate-before-action rule. I hit exactly this failure in this session's own
first push (repo-scoped `git add -A` in one repo under a two-repo claim).

> A cross-repo change needs a cross-repo done-check — any gate that runs in one repo
> silently passes omissions in the sibling (repo-scoped `git add -A` + single-repo
> drift check let a one-repo edit push under a two-repo claim).
> `Source: b1 post-push correction, 2026-07-21 (d831220)`

---

## Net effect on the two CLAUDE.mds

| Repo | Edit |
|---|---|
| harness | **Vacuous-exercise** → replaced by **Silent-wrong-answer** (Q1) |
| harness | **Reviewer-claims-verified** → replaced by the claims+mechanisms rewrite (Q5) |
| harness | **Adjacent-case and load-bearing coincidence** → new rule (Q3) |
| harness | gate-before-action rule → cross-repo done-check clause appended (riding) |
| agents | Repos rule `CLAUDE.md:22-24` → reachability amendment (Q2) |

Two replacements, one addition, two amendments. No rule is added beside the rule it
supersedes.
