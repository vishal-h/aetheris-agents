# Review — BUG-001 / BL-193 — round 4

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bl193r3packet.md` · Commit: `c9e34a3` on `ab036be`

**Verdict:** findings 13 and 14 closed; the arm marking and the figure pairing are right. Two new findings. **15 is blocking** — BUG-001 now cites a cleanup that the cited row does not contain, and the obligation it points at has no executor anywhere.

---

## Findings

### 15. [blocking] "BL-191's cleanup" does not exist — the citation is dangling and the cleanup is unowned

BUG-001's new block, and §3 and §9 of the packet, distinguish the archive gap from *"BL-191's cleanup … about files present and misplaced."*

**BL-191 contains no cleanup.** Its filed content, from the r0 packet's own verbatim quotation, is three things: (a) `drive/runbook.md` naming two folder-ID env vars nothing has read since `72367ac`; (a′) `sprint.sh:1061` gating the drive arm on those dead vars; (b) the Expected-output block showing per-file lines the script never prints. Its Done-when is entirely about renaming variables and correcting documentation. Nothing in it concerns misplaced Drive objects, and later rounds added only the `DRIVE_TEMPLATES_FOLDER_ID` evidence block and the BL-189 pointer.

Two consequences, and the second is the one that matters:

1. **The citation is wrong.** A reader following it lands on a runbook row and finds no cleanup.
2. **The cleanup has no row at all.** Removing stray months from period folders was proposed as a separate defect back when this work started and was never filed. So BUG-001 now discharges its own obligation by pointing at a row that never accepted it — the *"prose files nothing"* failure with an extra step, since here the prose points somewhere that looks authoritative.

**`backlog_resolution` cannot catch this class**, which is worth stating in whichever row lands. Its check is that every `BL-nnn` reference *resolves to an existing row* — a currency check, not a content check. Exactly the shape of the existing learning that *drift_check verifies a pin is current, never that it is complete*, now firing on the cross-reference checker rather than the manifest.

**Suggested fix:** file the cleanup row, and correct BUG-001's and BL-193's references to point at it. Its scope is now small and precisely known — see finding 16. If the arbiter would rather defer the row, then BUG-001's sentence must say the cleanup is **unfiled**, not attribute it to BL-191.

### 16. [non-blocking] The cleanup population is now exactly one folder, and the reads already establish it

Three period folders, three states, all from Drive reads this session:

- **`2026-05/`** — clean. `BTL_01` holds 2 objects created 2026-06-10. The first run had one month in `payslip/output/`, so there was nothing to misplace.
- **`2026-07/`** — contaminated. `BTL_01` holds 4 objects created 2026-08-07: the July pair and a May pair. Across 18 employee folders that is **72 objects, of which ~36 are misplaced May files**.
- **`2026-08/`** — clean, by rebuild. 36 objects, 18 employees, one month.

So the cleanup is one folder, one wrong month, a known count, and a mechanical identity test (filename prefix ≠ containing folder name). That is a small S row rather than the open-ended sweep it looked like when the period folders were unexamined.

Worth carrying into the row: `2026-08/` is clean **by accident of remediation**, not by cleanup, and `2026-05/` is clean **by accident of history**. Neither state was produced by anything that would keep them clean.

---

## Findings 13 and 14 — closed

**13.** The structural point leads — the requested month sorts last, so any truncation loses it first, stated as a property of the defect rather than of this run. The closure is verified three independent ways (folder `createdTime` inside the rebuild window proving new objects rather than an amended tree; zero trashed objects; the `64 → 66` census reconciling as `64 − 17 + 19`). The "no employee was harmed, the gap was the archive" line is the right thing for an operator to meet first.

**14.** Restated as consistency, the in-flight account named, the shutdown mechanism kept rather than deleted because it remains the likelier reading, and the settlement explicitly re-anchored to the sign of the subtraction that both accounts agree on.

**The arm marking and the figure pairing are correct as written**, including the part that was easiest to get wrong: 159.701 s pairs with the budget because the tool call spans startup, auth, uploads and exit; 156.3 s is the archive figure and sits inside it; comparing the latter to the cap would read 52.4% where the answer is 53.5%. Naming that as the two-clocks class rather than as a rounding nicety is right.

---

## Commended, and one thing I owe

**§8 deviation 1 is the round's real content, and the failure it caught is mine.**

My finding 13 said three employees have no August payslip *"today"* and *"nothing currently says so"* — present tense, about mutable external state, with no read timestamp attached. It was true at 12:26. It was false by 13:16, because in the same session I advised the rebuild that falsified it. A session optimising for throughput would have written the block from the review's text and left BUG-001 asserting, with citations, that three employees are missing their August payslips — false at the moment of writing, in a row an operator reads under pressure, and false in the direction that causes unnecessary remediation.

The packet's generalisation is right and I would sharpen it in one place: the rule *verify before acting, the source wins* was written for documents quoting **repo** state, and this instance extends it to a **live external system** that can change faster than a review cycle. But the fix is not only on the executing side. **A review finding about mutable external state should carry the timestamp of the read it rests on and say what would falsify it.** Had finding 13 read "as of BL-193's widened read at 02:47Z" rather than "today", the staleness would have been visible from the citation instead of discoverable only by re-reading Drive. I will write findings that way from here.

That is the third time today my evidence base has been the weak link — a UI string read while the trajectory sat unread, a conclusion asserted from a `rig/`-only grep, and now a present-tense claim about state I then had changed. The first two were incomplete searches; this one is a different failure, and the packet is right that staleness is invisible from inside the document.

**Two other things worth naming.** The refusal to close `fixed → verified` is recorded in the packet **as an instruction declined**, with the reasoning quoted, rather than silently done right — which is the only way a later reader learns the option existed. And §8 deviation 2 reports that a mis-terminated heredoc wrote the generating script into the packet body, caught by reading the file back rather than trusting the append. A packet that silently contained its own build script would have been a strange thing to receive; saying so is better than a clean-looking file.

---

## Dispositions requested

| # | Expected |
|---|---|
| 15 | fixed — file the cleanup row and repoint BUG-001's and BL-193's references; or, if deferred, say "unfiled" rather than naming BL-191 |
| 16 | fixed — the three-folder state carried into whichever row takes the cleanup |

## Owed

Unchanged: arm 1 of BUG-001's Done-when, by September's orchestrated run, against ≈298.3 s; the six-item packet head, to the housekeeping pass. **Corrected:** BL-191's outstanding work is the runbook and `sprint.sh` sweep only — the cleanup is a separate obligation and, until finding 15 lands, an unowned one.
