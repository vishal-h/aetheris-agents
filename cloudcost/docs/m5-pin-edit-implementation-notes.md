# m5 — the pin edit

A reviewer-authored section-scoped edit landing t1's done-check pin (`cloudcost/m5-n1-compose.md`,
the `**Done-check.**` block of §t1) and one correction (`cloudcost/docs/m5-scoping-landing-notes.md`,
§Review, F2's disposition), at agents r3 — the fourth commit of the m5 scoping round, on top of
`eebd47c` (r0), `a039a0d` (r1) and `2876d26` (r2). **The r3 SHA is deferred to the packet:** this
file is committed *in* r3, the round lands as one commit with no amend, so it cannot carry its own
hash without falsifying the thing it records.

`Authored 2026-08-09 at r3. Every figure below was derived in this session at the HEAD it names;
none is carried from r2's packet.`

---

## What changed

### P1 — t1's done-check item 1, pinned

**File:** `cloudcost/m5-n1-compose.md`. **Section scoped to:** §t1's `**Done-check.**` block only.
Items 2, 3 and 4 and the fence are untouched; the diff is one hunk.

The item told t1 to *derive* its own pytest invocation. That is a slot t1 could get wrong quietly:
the command is stated in one document, the working directory in another, and a session reading only
the first would have to guess the second.

```diff
 # 1. The offline pytest spine over the cloudcost suite, as a HEAD baseline.
-#    DERIVE the exact invocation from cloudcost/runbook.md or CLAUDE.md and
-#    record the command verbatim beside its summary line. Do not invent one;
-#    if neither document states it, report that as a finding and record what
-#    you ran and why.
+#    Pinned 2026-08-09 by the reviewer. Command: cloudcost/runbook.md
+#    §Offline tests. Working directory: the aetheris-agents/ root, per
+#    CLAUDE.md §Commands — the runbook's block states no cd and every cd in
+#    that file points elsewhere, so the root is not inferable from the
+#    runbook alone.
+#    RE-RESOLVE BOTH ANCHORS AT HEAD BEFORE RUNNING. Quote each. If either
+#    has moved, report it and run what the anchors say now — the pin is an
+#    anchor, not an assertion.
+python3 -m pytest cloudcost/tests/ -v
```

**Both anchors are section names, and no line number was introduced into the block.** Line numbers
rot, and a rotted pin is worse than a derivation: a stale `:380` sends t1 to whatever now sits at
that offset, silently, whereas a stale section name fails loudly and t1's re-resolution clause
covers it. The pin is an anchor, not an assertion — t1 re-resolves both before running and reports
any move.

### P2 — F2's disposition, corrected in place

**File:** `cloudcost/docs/m5-scoping-landing-notes.md`. **Section scoped to:** §Review, F2's
disposition blockquote. The three-sibling enumeration two lines above is untouched.

```diff
 > `m4-consolidation.md`, the one the finding leaned on, does not: it carries a
-> state table and no ticket headings. The correction is accepted; §6's template
-> is the authority regardless of what the siblings do.
+> state table and no ticket *sections* — its three `###` headings under
+> §Ticket set carry none of §6's seven fields (derived at r2, G2). The
+> correction is accepted; §6's template is the authority regardless of what the
+> siblings do.
```

Corrected **in place** rather than as a dated supersession block. The file has never been pushed and
no reader saw the earlier text — which is G3's own argument, applied to the section G3 did not
reach. A supersession block preserves a reading history that does not exist, and buys that fiction
at the cost of leaving the false sentence on the page.

---

## G1 — the invocation, as resolved

**Verdict: the invocation is derivable, but not from one document — and the half that is missing is
the half a session is least likely to notice is missing.** The command is stated verbatim in the
runbook. The working directory is stated nowhere in the runbook, and comes from a different file's
§Commands block. A session that resolved the runbook anchor alone would have a complete-looking
command and a wrong root, and `pytest cloudcost/tests/` fails from the wrong root by *not finding
the path* — which reads as a missing suite, not as a wrong cwd.

```
$ ( cd ../aetheris && python3 -m pytest cloudcost/tests/ -v -p no:cacheprovider ); echo "exit=$?"
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0 -- /home/it/.local/share/mise/installs/python/3.12.13/bin/python3
rootdir: /home/it/sandbox/elixirws/aetheris
plugins: anyio-4.13.0
collecting ... ERROR: file or directory not found: cloudcost/tests/

collected 0 items

============================ no tests ran in 0.00s =============================
exit=4
```

That block is the clause's truth-maker, run in this session at r4's tree rather than carried from
r3's packet: the failure is a usage error (exit 4) whose one diagnostic line names the *path* and
never the working directory, so the only cue to the real cause is the `rootdir:` line stating the
wrong root as though it were the right one — which is precisely why a session holding a
complete-looking command would read this as a suite that is missing rather than as a root that is
wrong. (`-p no:cacheprovider` so the demonstration writes nothing into the harness tree; the
harness repo was confirmed clean before and after.)

**Command:** `python3 -m pytest cloudcost/tests/ -v`

**Anchor 1 — the command.** `cloudcost/runbook.md` §Offline tests. Re-resolved at HEAD in this
session:

````
$ grep -n '^## Offline tests' cloudcost/runbook.md
377:## Offline tests

$ sed -n '377,381p' cloudcost/runbook.md
## Offline tests

```
python3 -m pytest cloudcost/tests/ -v      # no credentials; recorded DO + AWS + Linode fixtures
```
````

**Anchor 2 — the working directory.** `CLAUDE.md` (this repo's, at the root) §Commands.
Re-resolved at HEAD in this session:

````
$ grep -n '^## Commands' CLAUDE.md
45:## Commands

$ sed -n '45,52p' CLAUDE.md
## Commands

**Run tests for a use case:**
```bash
# From the aetheris-agents/ root
python3 -m pytest payslip/tests/ -v
python3 -m pytest api/tenant/tests/ api/gateway/tests/ -v
```
````

**The finding: the runbook's block states no working directory.** Its §Offline tests fence is three
lines (`cloudcost/runbook.md:379–381`) and contains no `cd`. Every `cd` in the file points
elsewhere — five to the harness repo, one into `cloudcost/` itself, none establishing the
aetheris-agents root for the pytest block:

```
$ grep -n 'cd ' cloudcost/runbook.md
160:cd ~/sandbox/elixirws/aetheris
166:cd ~/sandbox/elixirws/aetheris
180:cd ~/sandbox/elixirws/aetheris
193:cd ~/sandbox/elixirws/aetheris
223:cd ~/sandbox/elixirws/aetheris
306:cd cloudcost && mkdir -p history/digitalocean && mv history/2026-* history/digitalocean/
```

The `cloudcost/tests/` path in the command is itself the evidence for the root — the path is
repo-root-relative — but that is an inference from the argument, not a statement in the document,
and the pin states it rather than leaving t1 to make it.

---

## r5 — the ruling on r4's hold, and what it changed

`Authored 2026-08-09 at r5, the sixth commit of the round, on top of eebd47c (r0), a039a0d (r1),
2876d26 (r2), 9d7afe0 (r3) and a9639de (r4).`

**The R15 analogy holds, and the one place it differs is named.** R15 is written about a ticket;
r5 repairs r4's own output, which is that shape one level down, and R20 already makes this file
the edit's committed record — so r5 appends here rather than opening a fourth record file. The
difference is in R15's supporting mechanism, not in its classification: R15 argues that a repair
round's scope is committed *before* the round opens, and here it was not. r4 held and relayed in
a packet, and a packet travels as a claim about its content, so **F11 below is committed by r5
rather than pre-dating it**. Recorded rather than smoothed.

**This file's header is now partial and r5 does not repair it.** It describes the file as the
record of an edit landing "at agents r3 — the fourth commit"; r4 and r5 have both appended since.
Repairing the header is not in this round's instructions and is left for the reviewer.

### What r5 changed, and where

| § | file | change |
|---|---|---|
| S2 | `cloudcost/docs/m5-scoping-landing-notes.md` §Closing note | the standing r1-anchor caveat replaced by **Anchors in this file resolve at HEAD**, with a dated retirement note beneath it |
| S3 | same file, three sites | three line-number citations into `cloudcost/m5-n1-compose.md` converted to section-name + quotation form |
| S4 | `cloudcost/m5-n1-compose.md` §Ratified decisions | the *"None yet"* opener replaced; **m5-D1** ratified beneath it |
| S5 | `cloudcost/m5-n1-compose.md` | §Promotion candidates opened between §Ratified decisions and §Not established, carrying its first entry |
| S6 | this file | this section, and **F11**/**F12** appended to §Review |

`docs/backlog-2026-06.md` is not edited, neither ticket is opened, and the harness is untouched
(harness HEAD `2ef0517057e4eda991a8da10ccba66650d1e65a2`, clean, nothing to push).

**The sentence S2 replaced**, quoted from HEAD before the edit rather than from the r5 prompt:

```
they appear. Line numbers cited into `cloudcost/m5-n1-compose.md` are **r1** line numbers: F7
inserted four lines above `:13` and F2 removed four, so the file is 300 lines at both commits
while anchors between `:6` and `:57` differ from r0's.
```

Only that sentence moved; the paragraph's three preceding sentences, ending *"…both marked as
such where they appear."*, are untouched.

**S2's own pre-condition, checked before landing.** The replacement points the reader at the
entries that record the r0→r1 shift instead of at a standing rule, so those entries have to
exist. Both classes do record it: **§Verifications** at verification 1's heading
(`### 1. §6 field names — **r0 result superseded 2026-08-09 (r1 F2e)**`, with the r1 heading
census it added) and verification 4's (`### 4. Section-name convention vs m4-consolidation.md —
**r0 result superseded 2026-08-09 (r1 F7d)**`); **§Divergences** at class 2's
`[Updated at r1 (F7), 2026-08-09.]` block, which records the two heading insertions and where
each fell, and class 4's `[Updated at r1 (F2), 2026-08-09.]` block, which records the demotion
and the two removed `---` separators.

### S3 — the conversion table

Population derived by command over the three m5 records, not carried from r4's six hits. Two
sweeps: anchors qualified with a moving document's path, and bare `` `:NNN `` tokens whose
binding document is the enclosing section's subject.

```bash
R="cloudcost/docs/m5-scoping-landing-notes.md cloudcost/docs/m5-pin-edit-implementation-notes.md cloudcost/m5-n1-compose.md"
grep -nE '(m5-n1-compose\.md|backlog-2026-06\.md):[0-9]+' $R   # qualified
grep -nE '`:[0-9]+' $R                                          # bare
```

**Converted (3), all in the landing record.** Each is a locator for content that can be named and
quoted; none carries a claim about a line.

| before | after | why it converts |
|---|---|---|
| ``Declared `*(new)*` by t1's **Touches** field at `cloudcost/m5-n1-compose.md:91` — the line reads`` | ``Declared `*(new)*` by t1's **Touches** field in `cloudcost/m5-n1-compose.md` — the line reads`` | the quoted `*(new)*` entry follows in the same cell, so the offset added nothing a search could not |
| ``resolves to a heading that exists at `cloudcost/m5-n1-compose.md:181` (see verification 6).`` | ``resolves to a heading that exists in `cloudcost/m5-n1-compose.md` — t1's **Claude-code prompt** → **E7**, `**E7 — Decision H's re-derivability clause.**` (see verification 6).`` | **the worked case** — this is the anchor r4 moved from `:176` to `:181`, and the one whose correction falsified the caveat |
| ``document's own deviation blockquote records it at `cloudcost/m5-n1-compose.md:19–23`:`` | ``document's own deviation blockquote records it — `cloudcost/m5-n1-compose.md` §Scope, the blockquote opening `[Deviation, recorded rather than glossed.`:`` | the passage is quoted in full immediately beneath; the range was a locator only |

**Left unconverted, per S3(c) — every one, with why.** All four are claims about a line as such.

| site | anchors | kind, and why it stays |
|---|---|---|
| §Divergences class 2, the `[Updated at r1 (F7)]` block | `cloudcost/m5-n1-compose.md:6`, `:13`, `:19–23` | **where an insertion fell.** The block's whole subject is that two headings were inserted at those points and that the deviation blockquote did not move. The number is the claim. |
| §Verifications 4's G2 output fence | `cloudcost/m5-n1-compose.md:14` | **`file:count` grep output**, and verbatim command output besides — editing it would falsify the transcript. |
| §The attribution rule, the annotation table | `docs/backlog-2026-06.md:7535`, `:7586`; row openings `:7484`, `:7547` | **where an insertion fell.** The section exists to satisfy §Carried in's first rule, which requires an edit to state where its insertion point falls relative to the surrounding unit's boundaries; the offsets are that statement. |
| §The attribution rule, the prose beneath | `docs/backlog-2026-06.md:7542`, `:7591` | same — the following unit's bound, against which the insertion's position is measured. |

**No sentence's claim was rewritten.** Three citations changed and nothing else; no conversion
required S3(d)'s escape.

**One observation on the exemption's reach, since it decides a whole document.** S3(c)'s
"a statement about where an insertion fell" covers *every* backlog anchor in the three records —
they all sit in §The attribution rule — so S3(b)'s `BL-131's row` example converts nothing here.
If the intended reading is that the annotation table converts, it is one further edit.

**Post-conversion sweep (S3(e)).** Qualified form, verbatim:

```
cloudcost/docs/m5-scoping-landing-notes.md:386:> `cloudcost/m5-n1-compose.md:6`, above the paragraph beginning *"**What this round decides.**"*;
cloudcost/docs/m5-scoping-landing-notes.md:446:> cloudcost/m5-n1-compose.md:14
cloudcost/docs/m5-scoping-landing-notes.md:662:| `**Scoped 2026-08-09 into `cloudcost/m5-n1-compose.md`**` | `docs/backlog-2026-06.md:7535` | BL-131, opening `:7484` |
cloudcost/docs/m5-scoping-landing-notes.md:663:| `**Annotated 2026-08-09.**` | `docs/backlog-2026-06.md:7586` | BL-132, opening `:7547` |
```

Four hits, all four in the exempt table above. The bare sweep returns 37 hits (34 landing record,
3 this file, 0 the round document); of those, the ones bound to a **moving** document are `:13`
and `:19–23` in class 2's F7 block and `:7484`/`:7535`/`:7542`/`:7547`/`:7586`/`:7591` in
§The attribution rule — again the exempt table. Every remaining bare anchor binds to
`cloudcost/m4-consolidation.md` (§F1's four passages and §Divergences class 4's heading census)
or to `cloudcost/milestone.md` / `m2-milestone.md` / `m3-milestone.md`, none of which this round
edits, plus the hypothetical `` `:380` `` in P1's prose, which cites nothing.

**Zero line-number anchors into a moving document outside the enumerated kinds.**

### S4 — the identifier check, and why the decision landed as `m5-D1`

Run before authoring the decision:

```
$ grep -nE '(^|[^A-Za-z0-9_-])M1([^A-Za-z0-9_-]|$)' cloudcost/*.md docs/milestones/*.md
docs/milestones/bl-067-implementation-notes.md:74:| M1 | Summary undercounts agents by one | per-section agent counts, totals, counts-follow-sections |
cloudcost/m2-milestone.md:89:  new), 8/8 mutations (M1–M8), drift 8 PASS/3 exempt-WARN exit 0. Review r0 **APPROVE merge-clean**
cloudcost/m2-milestone.md:96:  moves both sides together — M1 shows it — leaving DO's raw API values as the only thing binding a
cloudcost/m2-milestone.md:480:**Outcome.** Merge-clean, r0 APPROVE. 229 tests (219 t1 + 10 new), 8/8 mutations (M1–M8). Negative
```

**`M1` is taken, in both of the globs the check named.** In `cloudcost/m2-milestone.md` it is a
**mutation** label — the m2 mutation-testing set `M1–M8`, cited three times, including in that
document's own outcome line; in `docs/milestones/bl-067-implementation-notes.md` it is again a
mutation row (`| M1 | Summary undercounts agents by one | … |`). A reader meeting `M1` in a
cloudcost cycle document already has a referent, and it is not a decision.

`m5-D1` is free — zero hits over both trees:

```
$ grep -rnE '(^|[^A-Za-z0-9_-])m5-D1([^A-Za-z0-9_-]|$)' cloudcost/ docs/ ; echo "exit=$?"
exit=1
```

Bare `D1` is not free, which is what the `m5-` prefix buys: `cloudcost/milestone.md` carries
design decisions `D1–D6` (`**D1 — Record-and-deliver, NOT a verify-target.**`) and
`docs/milestones/hc-d-implementation-notes.md` opens `## 1. D1 — the R12 narrowing was offered
conditionally`. The decision therefore landed as **`m5-D1`** in its heading, in §Promotion
candidates' preamble, and in a bracketed note beneath the decision recording the substitution and
its condition. **The commit message still reads `ratify M1`** — it is the reviewer's text, landed
as given, with the divergence reported rather than silently reconciled.

**This is a hold trigger, and the push is held on it.** r5's instructions push only if the
identifier check "resolved without a collision you had to work around". It did not.

---

## Review

`[Authored by the reviewer, 2026-08-09, at r3. R20's shape: findings verbatim, dispositions
beneath. Covers the pin edit. This edit is not a ticket round and gets no review file; this file is
its committed record.]`

**G1 — pytest invocation.** *t1's done-check told t1 to derive the cloudcost pytest invocation,
which is a slot t1 could get wrong quietly.*

> **Disposition: STATED, and pinned at r3 (P1).** The command is in the runbook; the working
> directory is not, and comes from a different file's §Commands block. Pinned with both anchors by
> section name rather than by line number, and t1 re-resolves both before running.

**G2 — interpretation → command.** *One landed sentence rested on a reading of what
`### What t1b inherits` headings are.*

> **Disposition: derived at r2.** The seven §6 field markers return zero over the whole of
> `m4-consolidation.md`, with four non-zero counts as the positive control. Re-derived at HEAD in
> this session, enumerated rather than tallied: `m4-consolidation.md` **0** ·
> `cloudcost/milestone.md` **25** · `m2-milestone.md` **15** · `m3-milestone.md` **18** ·
> `m5-n1-compose.md` **14**. Three of the four non-zero documents are sibling *cycle* documents;
> the fourth is `m5-n1-compose.md`, the round document itself — the control holds either way, and
> the enumeration is published so the reader need not take the count's population on trust.
> §6's seven fields are Scope · Contract refs · Touches · Do not generate · Runbook update rule ·
> Done-check · Claude-code prompt (`../aetheris/docs/methodology/milestone-methodology.md` §6).
> r0's class-4 correction stands on a test rather than a reading.

**G3 — §F1's internal tension.** *`:362` was tabled as a gate statement and described in the prose
beneath as not a gate.*

> **Disposition: corrected in place at r2.** The table now sorts by kind and `:362` sits in its own
> row as a sequencing rationale — a third kind, belonging to neither side of the discrepancy.

**G4 — R20 compliance.** *The landing record carried no `## Review` section, so the reviewer's
findings on the edit lived only in packets.*

> **Disposition: closed at r2.**

**F9 — the disposition sentence.** *Raised by claude-code against text the reviewer authored: F2's
disposition in the §Review block read "no ticket headings", which is false read literally and
reintroduces the loose form G2 was sent to replace, a few hundred lines from the fix.*

> **Disposition: accepted and corrected in place at r3 (P2).** `m4-consolidation.md` carries three
> `###` headings under §Ticket set — `### What t1b inherits` (:188), `### What t2 inherits` (:216),
> `### What t3, t4 and t5 inherit` (:230), the section spanning :133–246 — so read literally the
> sentence was simply wrong, and it was true only under the reading G2 exists to displace. A
> correction that lands in one section and leaves the same claim uncorrected in another is the
> vocabulary-sweep candidate's shape: **the population that speaks a claim is not always the
> section it was found in.** The finding is the reviewer's own text failing the reviewer's own
> rule, which is the cheapest possible demonstration that the sweep is owed.

**F10 — a packet figure contradicting its own printed evidence.** *r2's packet printed `wc -l` =
831 for the landing record and then stated the file "is 823 after G2/G3/G4" two lines below.*

> **Disposition: recorded, not fixed — the figure is packet-only and reaches no committed
> artifact.** Recorded because it is carrier 1 in its purest form: a count stated beside the
> evidence that refutes it, in a packet whose discipline is otherwise exact. The refutation was
> already on the page, and a reader scanning the prose rather than the fence would have carried the
> wrong number away.
>
> **How the containment was verified.** `git grep -n '823' -- '*.md'` over this repo returns two
> hits, neither a line count: `cloudcost/docs/m3-t3-implementation-notes.md:22` (a Linode volume id,
> `ccm-8cac00823f9b`) and `docs/provenance/specs.md:194` (a `duration_ms` value in a JSON sample).
> The same grep over `../aetheris/` returns nothing. So no committed artifact in either repo states
> 823 as the landing record's length. The record's true length is confirmed directly by
> `wc -l cloudcost/docs/m5-scoping-landing-notes.md` — 831 before this round's P2, 833 after, P2
> being a three-line-for-five-line replacement.

**F11 — the retired convention.** *Finding, raised by claude-code at r4: correcting one stale
anchor falsified a standing caveat declaring every anchor in the landing record to be an r1
number, and repairing the caveat is a ruling about the reviewer's own prose rather than
arithmetic — so r4 held rather than pushing past it.*

> **Disposition: ruled at r5. The convention is retired, not preserved** — see m5-D1. The hold was
> correct: the alternative reading, reverting the anchor to keep the caveat true, would have
> adopted a misdirecting citation as policy.

**F12 — a blind check, specified by the reviewer.** *Finding: r4's harness-clean check used
`git status` against a gitignored path, so it could not observe the artifact it was watching for.*

> **Disposition: accepted; substitution was correct and is recorded as a promotion candidate on
> the round document (S5).** The finding is against the check the reviewer wrote, and the
> substitution was reported rather than silently made, which is the behaviour the candidate asks
> for.

---

This file is R20's committed record for the pin edit. **The packet is not** — a packet travels as a
claim about its content and is committed in neither repo, which is the whole reason R20 puts the
record here. Every figure above was derived in this session at the HEAD it names: the two anchors
re-resolved rather than carried from r2, the §6 counts re-run and enumerated, the `823` containment
grepped across both repos, and the heading census read from `m4-consolidation.md` directly.
