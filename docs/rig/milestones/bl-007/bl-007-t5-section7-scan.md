# BL-007 — §7 scan input (finding-class scan across all five review files)

**Prepared at t5 (Phase A) as INPUT for claude-ui's §7 milestone-end ritual.
This file deliberately contains NO promotion wording** — distilling each class into a
standing CLAUDE.md instruction is claude-ui's deliverable, and the promotion commit is a
separate act after the human adjudicates (it triggers a session restart per the
sequencing rule).

**Sources scanned in full:** `docs/reviews/bl-007-t0-review.md` (80 lines) ·
`bl-007-t1-review.md` (80) · `bl-007-t2-review.md` (147) · `bl-007-t3-review.md` (203) ·
`bl-007-t4-review.md` (392).

**Format note.** Methodology §7
(`../aetheris/docs/methodology/milestone-methodology.md:207-220`) specifies only the
*input* ("the milestone's review files") and the ≥2-ticket threshold. It prescribes **no
table format** — the table below is a structure built for this packet, not one §7
mandates.

**Threshold reminder.** §7 promotes findings that recurred on **≥2 tickets**. Classes
below that line are listed anyway, marked, so the human can see what was considered and
rejected rather than only what survived.

---

## Scan table

| # | Finding class | Tickets / rounds where it appeared | Meets ≥2-ticket bar? | Already promoted? (where) |
|---|---|---|---|---|
| **A** | **A deferred finding gets a backlog row, not prose.** A finding accepted-but-not-fixed was left in packet prose or notes, with no backlog entry, so nothing would have filed it. | **t1** F2 (the two backlog entries t1 generated "appear in no ticket's written scope") · **t2** F4 (`tool_result` payload-key gap flagged "follow-up candidate", no row) · **t3** F4 (label rec "lives only in packet prose"; the review itself cites "F4 precedent this milestone") | **Yes — 3 tickets** | **No.** The t2 review cites it as a *methodology* rule ("a deferred finding gets a backlog entry, not silence"), but it is in no CLAUDE.md learning section. |
| **B** | **Decisions that constrain ticket N+1 must land in N+1's README section before its session starts** — not in the previous ticket's implementation notes, which the next session never reads. | **t2** F3 (t3/t4 load-bearing facts only in t2's notes) + t2 cross-note (a ratified rider isn't executable until the doc carries it) · **t3** cross-note ("the third consecutive occasion") + t3 F7 disposition (quit-during-fork line into §t4) | **Yes — 2 tickets** | **No.** Note t3's review frames this as a **positive pattern** earning promotion ("decisions that constrain ticket N+1 land in ticket N+1's README section before its session starts"), not a defect class. |
| **C** | **Claims about code require read-verification at HEAD — including absence claims.** Citations from a mirror, from memory, or from a single grep were asserted as current fact. | **t1** cross-note (named "strong": the missing citation was "the tell") · **t2** reviewer watermark note + F1 ("verify both citations at HEAD before editing") · **t3** F2 ("Cited-means-read applies") · **t4** F4 (the sweep's "all other fields match" falsified by artifacts) · **t5** (this session: `store.ex:794`→`:807` drift; `harness.rs:82` is a multi-line `COALESCE` a single-line grep misses; **and the runbook's own false "not a bare run id" claim, caught at t5 review F1**) | **Yes — 4+ tickets** | **YES — substantially promoted already.** `../aetheris/CLAUDE.md:530-532`, **"Cited-means-read (author side)"** (`Source: BL-021, BL-022`): *"A `file:line` citation asserts that you read that line. Grep proving the absence of X is not evidence for the presence of Y…"* — and its BL-022 paragraph is **itself an absence claim about `fork_run`**, the exact error BL-007 was founded on. It also binds reviewers, names planning docs as the seductive source, and prescribes "treat the list as leads, not facts." **See the corrected residual below.** |
| **D** | **Stale-recon: a correction must chase the claim into every doc that adopted it.** A verification pass's output goes stale the moment a later pass corrects it. | **t2** F5 (current-state §3.1 seed row stale) · **t4** F5 (co-presence claim chased into all three carriers + repo-wide grep) · **t5** (§C's false "no fork API" text; the "`types.ts` does not declare `resumed`" note, resolved at t4 but still asserted) | **Yes — 3 tickets** | **No.** Already named as the visible candidate in this README's `## Done` section. |
| **E** | **Packet integrity: a section referenced is a section absent.** Implementation notes cited in the packet but not inlined. | **t3** F1 — **[blocking]** · t3 cross-note ("t2 inlined notes, t3 referenced them… if a third packet arrives partial, that's a promotion candidate") | 1 ticket in *this* milestone | **YES — already promoted, twice, and it recurred as blocking anyway.** m1 learnings: "Review packets must include the full done-check output block, opened first" and "Implementation notes are a required deliverable… commit before submitting the review packet." **See the flag below — this is the highest-signal row in the table.** |
| **F** | **Acting ahead of an unexecuted gate, under momentum.** Doing the next step before the gate that should precede it has run and reported. | **t2** (the "sequencing slip against the session's own instruction", recorded in *positive findings* as an honest deviation record) · **t4** pre-t4 "rider slip" (doc edited ahead of its gate) · **t4** post-r4 (both branches **pushed** before the GUI e2e was green, inverting the agreed order) | **Yes — 2 tickets / 3 instances** | **No.** t4's notes set its own bar — "if a third instance appears at t5, promoting as one line" — and counted two. **See the counting correction below.** |
| **G** | **A simulated adversary verifies the simulation; only the real counterpart verifies the fix.** A fix called "verified" against a simulation that could not reproduce the field failure. | **t4** r3 (claimed verified) → r4 (F9/F10: wrong connection mode, already-converted DB, lock never actually held) | No — 1 ticket, 2 rounds | **No.** t4's notes record it as subsumed by class **H**. |
| **H** | **One symptom, several mechanisms — separate symptom from mechanism by direct capture in the operator's own environment.** "Fork hangs" had three faces (`:busy` crash → `await_run` poll-forever → StrictMode-dead mount guard); a real fix for face 1 was mistaken for closure of a symptom actually caused by face 3. | **t4** r3 / r4 / r5 | No — 1 ticket, 3 rounds | **No.** t4's notes call this the sharpest and most complete candidate, subsuming G. Recurrence is across *rounds*, not tickets — the human's call whether §7's ticket-threshold is the right test for a class this well-evidenced. |
| **I** | **The runbook-update rule was not honored at the origin ticket.** Operator-visible changes shipped with no runbook entry; both had to be recovered at t5. | **t2** (fork CLI semantics change — harness runbook had only the bare command) · **t4** (Rig affordance — `grep -i fork` on the Rig runbook returned **zero hits**) | **Yes — 2 tickets** | **No.** Surfaced by t5's sweep, so it appears in **no review file** — it would be invisible to a scan of the reviews alone. Methodology §6 carries the rule; see the wording observation below. |
| **J** | **Gate consistency across tickets** — t0 ran `credo --strict` + `dialyzer` for touched Elixir; t1 touched Elixir and ran neither. | **t1** F3 | No — 1 ticket | **YES.** Root CLAUDE.md: "Every existing gate runs at ticket boundaries, even off-territory" (`Source: BL-016, BL-005 (×2)`). The promoted rule worked — the reviewer caught it. |
| **K** | **Done-check commands must be repo-qualified and existence-verified**, the same way Touches paths are. | **t0** F3 + t0 cross-note (swept pre-emptively across t1–t5 in the same round) | No — 1 ticket | **Adjacent to promoted.** m7's "verified runtime shape" rule covers the same muscle from a different angle. t0's own note called finding 3 "the test of whether it bites twice" — it did not. |

---

## Four observations handed over with the table

These are **not** promotion drafts. They are facts about the scan that the human should
have before adjudicating.

### 1. Class E is the highest-signal row, and it is an *already-promoted* class

§7's own test reads: *"the same finding class should not appear as `blocking` in two
consecutive milestones. If it does, the promoted rule was too vague — rewrite it with a
concrete example."*

Class E is covered by **two** m1 learnings and still arrived as **t3 F1 [blocking]**. By
§7's test, the question is not whether to promote it but whether to **rewrite** it. Worth
noting *how* it failed: both m1 rules are phrased as "must include / is a required
deliverable," which t3 arguably satisfied — the notes existed and were committed; they
were *referenced* rather than pasted. The reviewer's own phrasing is sharper than the
promoted rule ("a packet section referenced is a packet section absent").

### 2. Class F has already met its own stated threshold — a counting correction

t4's notes set the bar explicitly: *"if a third instance appears at t5, promoting as one
line."* They counted two instances, both at t4.

The count was low. The **t2** review's positive-findings section records an earlier
instance — "the sequencing slip against the session's own instruction" — logged as an
honest deviation record rather than as an instance of a class. That makes **three
instances across two tickets, entirely within this milestone**, without needing a t5
occurrence. The threshold t4 set for itself is met on the existing record.

### 3. Class I is invisible to a scan of the review files alone

Class I was surfaced by t5's runbook sweep, not by any reviewer, so a §7 scan whose input
is "the milestone's review files" (as §7 specifies) would miss it entirely. It is
included here because the ticket asked for a scan across the reviews *and* because the
class meets the ≥2-ticket bar on the milestone's own evidence.

One observation about the rule that was missed, offered as a fact rather than a fix:
methodology §6 fires on *"a new environment variable, a new startup step, a new
configuration key, or a new operational procedure."* t2 changed the **semantics of an
existing command** (`--step N` went from re-run-from-original-prompt to replay-to-step-N)
— which matches none of those four nouns, while being exactly the kind of change an
operator must know about. t4's affordance is closer to "new operational procedure," but
was still missed.

### 4. Class C is already promoted — and its residual is class D (corrected at t5 review F2)

The first version of this table said class C was only *partially* promoted. **That was
wrong**, and the reviewer caught it — an instance of class C inside the class-C row.
`../aetheris/CLAUDE.md:530-532` carries "Cited-means-read (author side)" at HEAD, whose
BL-022 example is an absence claim about `fork_run` asserted from planning documents
without opening `lib/aetheris.ex`. That is BL-007's founding error, already promoted.

So the open question is not whether to promote C, but **what C's residual is.** Sorting
this milestone's C instances against the promoted rule:

| Instance | Covered by the promoted rule? |
|---|---|
| t1 "the tell" — a claim whose row cited no line | **Yes**, directly |
| t3 F2, t4 F4 — inference from a neighbour / from writer code, falsified by artifacts | **Yes** — "a sibling file's shape is not evidence of this file's shape" |
| t5 runbook "not a bare run id" — asserted from the `@moduledoc` usage string without reading `extract_run_id/1` | **Yes**, directly |
| t2 watermark — citations from the project-knowledge **mirror**, not a fresh read | **Partly.** A mirror is a stale copy of *code truth*, not a planning doc; the rule's examples don't quite name it |
| t5 `store.ex:794`→`:807` — the line **was** read correctly, then the file moved | **No.** This is not "never looked at it"; it is a verified fact going stale |

The last two rows are the residual, and both are **class D** (a verified claim decaying
after verification), not class C (a claim never verified). **C's residual folds into D** —
which is the reviewer's read, and the sorting above is the evidence for it.

**A separate structural fact, surfaced while confirming this.** The Cited-means-read entry
lives in the **harness** repo's `CLAUDE.md` (`../aetheris/CLAUDE.md:530`). There is **no
such entry** in `aetheris-agents/CLAUDE.md` — verified by grep at HEAD. Sessions for this
milestone run with `aetheris-agents/` as the working directory, so that repo's CLAUDE.md
is the one loaded into context; the harness rule was **not** in this session's context
while its own class was being violated. Whether promoted rules should be duplicated,
cross-referenced, or otherwise made reachable across the two repos is a question about the
promotion mechanism itself — flagged here because it plausibly bears on why an
already-promoted class kept recurring.
