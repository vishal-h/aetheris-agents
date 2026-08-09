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

---

This file is R20's committed record for the pin edit. **The packet is not** — a packet travels as a
claim about its content and is committed in neither repo, which is the whole reason R20 puts the
record here. Every figure above was derived in this session at the HEAD it names: the two anchors
re-resolved rather than carried from r2, the §6 counts re-run and enumerated, the `823` containment
grepped across both repos, and the heading census read from `m4-consolidation.md` directly.
