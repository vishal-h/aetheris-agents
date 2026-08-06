# t1a-p — implementation notes

**Ticket:** t1a-p — promote the t1a cycle's findings into the standing instructions (methodology §7).
**Date:** 2026-08-06.
**Verified at:** `aetheris-agents@13eac9f`, `aetheris@e6687f1` — both clean and level with origin by
sha equality at the moment of acting. Every anchor and citation in this file is pinned to those two
shas unless a post-edit line is explicitly labelled as such.
**Repos touched:** both. No code change in either; three `.md` files.
**Command convention:** every repo-scoped command in the gate, the census and the done-check used
`git -C <repo>` or an absolute path. Nothing relied on the shell's working directory, which resets
between invocations in this environment.

---

## 1. The gate, as read

| Gate | Result |
|---|---|
| **G0** fresh session, not carrying t1a's conversation | PASS — every input read from disk |
| **G0** not in plan mode | The session opened in plan mode. Gate reading is read-only, so it ran; **no write occurred until plan mode exited**, and G1/G2 were re-run immediately before the first edit and were unchanged. |
| **G1** both repos clean; t1a's commits pushed | PASS — `aetheris-agents` HEAD `13eac9f` == `origin/main`; `aetheris` HEAD `e6687f1` == `origin/main`; both `git -C … status --porcelain` empty |
| **G2** three anchors exist at HEAD and read as described | PASS, with one recorded difference (§4) |
| **G3** no edit touches an entry other than the three named | PASS — verified by diff, not by intent: harness `39 insertions(+), 0 deletions`, agents `2 insertions(+), 2 deletions(-)` |
| **G4** all commands cwd-independent | PASS — see the command convention above |

**Anchors verified at HEAD before writing**, by opening them rather than by quoting the ticket:

- **A** — `../aetheris/CLAUDE.md:656`, `- **Cited-means-read (author side).**`, inside
  §Continuous learning → Workflow patterns (section opens `:520`).
- **B** — `../aetheris/CLAUDE.md:550–609`, the **Silent-wrong-answer** entry. Structure read in
  full: bolded head `:550–552`, body `:554–562`, carrier bullets `:568–585`, bolded carrier
  paragraph *"Absent is unknown, not zero"* `:587–597`, bolded carrier paragraph *"The rule is
  run-level"* `:599–603` with an **inner** `Source:` at `:604–605`, through-line `:607–608`,
  **closing** `Source:` at `:609`.
- **C** — `CLAUDE.md:452` with its `Source:` at `:453`, inside §Learning — BL-007. Text
  byte-identical to the ticket's quotation.

## 2. What landed

| Edit | File | Post-edit location |
|---|---|---|
| A | `../aetheris/CLAUDE.md` | `:667–693`, immediately before `Cited-means-read (author side)`, now `:695` |
| B | `../aetheris/CLAUDE.md` | `:607–616`, inside the Silent-wrong-answer entry |
| C | `CLAUDE.md` | `:452–453`, replacing the superseded entry in full |

Harness `CLAUDE.md` 759 → 798 lines; agents `CLAUDE.md` 471 → 471.

## 3. The dropped `Source:` clause — edit A

The ticket's edit-A `Source:` line ended with a fifth clause: *"Plus that cycle's five drafted
tickets, each carrying exactly one blocking defect, every one a claim about repo state its author
could not check."* It was **dropped** before writing, on the operator's ruling, and the entry's
`Source:` now ends at *"an absolute about an era nothing in the repo can inspect."*

Why: no durable artifact carries it. Not `docs/reviews/t1a-review.md`, which is the file the
`Source:` line itself cites; not `cloudcost/docs/t1a-implementation-notes.md`; not
`docs/backlog-2026-06.md`; and not t1a's session packet, which says *"this cycle has spent **five
rounds** on what happens when an invented claim enters a durable document"* — a different claim
about a different countable. No cycle document exists yet and no t1b–t1e drafts exist in either
repo, so there is nothing the phrase could resolve against. Committing it would have installed an
uncheckable claim inside the entry that exists to stop exactly that.

The four retained instances were each pinned to a line before the entry was written:

| Instance in the `Source:` line | Where it is evidenced |
|---|---|
| A packet section asserted present that had not travelled | `docs/reviews/t1a-review.md:58` |
| Mechanism *"emitted only when there is state to report"*, false for one of the two lines it named | `cloudcost/docs/t1a-implementation-notes.md:59–72` |
| A documented search term set that was not the one executed | `cloudcost/docs/t1a-implementation-notes.md:§3`; `docs/reviews/t1a-review.md:15` |
| *"stream splitting could never have worked"* | `cloudcost/docs/t1a-implementation-notes.md:36–38` |

**Citation-provenance note, edit C.** Edit C's `Source:` attributes *"three channel failures in one
ticket"* to `docs/reviews/t1a-review.md`, which names the class as a promotion candidate (`:50–51`)
but does not enumerate the three forms. The enumeration is in t1a's session packet, which is not a
repo artifact. The claim is supported; its cited resolver carries the class, not the count.
Recorded rather than silently kept.

## 4. Edit-C format adaptation

The ticket describes the edit-C anchor as a bullet. In the file it is a **bolded paragraph with an
unindented `Source:` line on its own** — the format of all seven entries in §Learning — BL-007, none
of which is a list item. Content matched the ticket's quotation exactly, so this is a rendering
difference, not a materially different anchor: the wording landed verbatim, rendered in the
section's house style on the operator's ruling. The superseded text is quoted with its before and
after in the review packet.

Edit A needed no such adaptation — §Continuous learning → Workflow patterns *is* a list, and the
ticket's rendering already matched.

## 5. Edit-B placement

The Silent-wrong-answer entry has **two** `Source:` lines, so *"before its closing `Source:` line"*
does not pick out a single insertion point until the entry's shape is read. The insert went after
the *run-level* paragraph and its **inner** `Source:` (`:604–605` pre-edit) and **before** the
through-line, which:

- puts it alongside the entry's other two bolded carrier paragraphs, matching the shape it joins;
- leaves the through-line and the entry's **closing** `Source:` intact as the conclusion.

The alternative — between the through-line and the closing `Source:` — would have separated a
sentence from the citation it belongs to.

## 6. §7 census clause

Searched this cycle's review file and implementation notes for any claim that a learning **was**
promoted. **Nothing else is claimed.** The two matches are forward-looking, not assertions of a
completed promotion:

- `docs/reviews/t1a-review.md:47` — heading *"Promotion candidates (§7)"*, listing the three
  candidates this ticket discharges.
- `cloudcost/docs/t1a-implementation-notes.md:290` — *"The promotion candidate"*, naming the
  substance-search rule as a carry.

Terms run (recorded because a method record must describe what executed): case-insensitive
`promot` across both files, absolute paths. No cycle document exists for this cycle, so there is no
handoff or close note of the kind §7's census clause was written against.

## 7. Not established

- Whether t1a's session packet (`t1a-review-packet.md`, a scratchpad artifact outside both repos)
  will remain reachable. Two `Source:` details resolve only there — edit C's three-channel count,
  and the "five rounds" reading that displaced the dropped clause. Neither is load-bearing for the
  rules themselves.
- Whether a fourth promotion candidate is owed. None was identified; per the ticket, one would be
  reported rather than added.

## 8. Scope

No code change. No fourth bullet. No neighbouring entry edited. No restatement of the promoted
rules in this file, in the review file, or anywhere else — a document that restates a rule is how
the rule stops being read where it lives. `docs/reviews/t1a-review.md` unchanged.
