# Review packet — BL-205: the cloudcost seat test asserts a pre-t3 outcome against today's date

Author: claude-code · Date: 2026-09-10
Repo: `aetheris-agents` · Branch: `main` · Baseline commit: `34b1575` · Commit under review: `390569f`, **pushed** (`34b1575..390569f`)
Round type: **defect fix (test)**, as declared in the cc:prompt.

## Head

Plain language, for a reader deciding whether to read the body.

1. **What this is.** BL-205, one row, one commit, fix and close together. Status **DONE**, moved to
   `docs/backlog-2026-06-closed.md`.
2. **Baseline.** Agents at `34b1575`, tree clean at start and clean now but for the commit itself.
   Every measurement below is at `34b1575` (the pre-fix reds) or at `390569f` (everything else),
   and each block says which. The harness checkout was not written to; `drift_check` reads it.
3. **What it does.** One test stops asserting that seats have no rule — they got one at `97c61a0`
   four weeks ago — and starts asserting what the rule does, against a pinned reference date
   instead of against today. No source change, no fixture change, one test.
4. **Deviations from the ticket as written.** One, in §Decisions: the ticket's stated arithmetic
   (35d firing / 28d not) is off by a day in both places. Measured is 34d and 27–28d. The count the
   assertion rests on is unchanged, and the ticket's step 4 instruction was to stop and report if
   the *count* differed — it did not. The comment was written from the measured figures.
5. **What is owed, and by whom.** Nothing by this row. One thing is captured and deliberately not
   acted on, in §Findings: the pin this fix adds is **not load-bearing today** and cannot be shown
   green-vs-red until 2026-09-12. That is a property of the pin's date, not a defect, and it is
   flagged rather than papered over.
6. **Read first.** §Findings, item 1, and §Verification 4 — the mutation that establishes the pin
   is wired is not the same as one establishing the pin is doing work today, and the packet does
   not claim it is.

---

## Done-check output

Opened first, per `CLAUDE.md` §Learning — m1-docbuilder. Every block is transcribed from a command
that had exited. Where a block is filtered rather than whole, the filter is in the command line so
the elision is visible. No sprint arm exists for this territory and none was run; this is a
pytest-gated use case.

### 1. The target file — gate 5, at `390569f`

```
$ timeout 600 python3 -m pytest -q cloudcost/tests/test_fetch_github.py
.......................................................                  [100%]
55 passed in 9.44s
EXIT=0
```

### 2. The whole-suite gate — gate 6, at `390569f`

The gate is `python3 -m pytest -q -m "not integration and not dormant"` from the repo root. Run in
the **foreground** under an explicit cap, output redirected to a file rather than piped, so the
exit status is pytest's own and not a wrapping shell's:

```
$ timeout 1800 python3 -m pytest -q -m "not integration and not dormant" > wholesuite.txt 2>&1
EXIT=0
$ tail -8 wholesuite.txt
........................................................................ [ 79%]
........................................................................ [ 83%]
........................................................................ [ 88%]
........................................................................ [ 92%]
........................................................................ [ 97%]
.x.x....x.............x.x...xx.................                          [100%]
deselected by reason: integration=114, dormant=211 (total 325)
1621 passed, 3 skipped, 325 deselected, 7 xfailed in 213.18s (0:03:33)
```

**1621 passed, 0 failed**, the figure the ticket predicted. **The cap did not fire**: 213s against
1800s, and the run ended by finishing. Recorded because a cap that does not actually cap is one a
later session will trust wrongly. The `tail -8` is the elision, stated here: the elided lines are
the progress-dot rows above 79%, which carry no result the summary line does not.

### 3. `backlog_status.py --check` — gate 7, at `390569f`, whole output

```
$ python3 scripts/backlog_status.py --check
/home/it/sandbox/elixirws/aetheris-agents/docs/backlog-2026-06.md: 125 sections
/home/it/sandbox/elixirws/aetheris-agents/docs/backlog-2026-06-closed.md: 96 sections
union: 221 sections, 204 row ids
OK: 204 of 204 row ids carry exactly one field, all in vocabulary, and each is on the correct side of the split (DONE archives, everything else stays open)
EXIT=0
```

Before the move: 126 open / 95 closed. After: 125 / 96. Same 204 row ids either side, which is the
check confirming a move rather than a rewrite.

### 4. `drift_check.py --strict` — the done-check, at `390569f`, **post-commit**

Run after the commit, not before, because check 8 reads committed history and this commit edits
`docs/backlog-2026-06.md` — a manifest-tracked row on the `export` surface. A `--strict` run
preceding that commit reads the file's pre-edit hash and cannot see the staleness the edit
introduces.

**The WARN set was predicted before the run, and the prediction is a set rather than a count**
(`CLAUDE.md` §Learning — ds): *the same three `project_knowledge` staleness members as at
`34b1575`, no fourth — this commit re-stales `backlog-2026-06.md`'s existing row rather than adding
one, and `backlog-2026-06-closed.md` sits on the `on-demand` surface where check 8 compares
nothing.*

```
$ AETHERIS_DB_PATH=/home/it/sandbox/elixirws/aetheris/priv/aetheris.db \
    timeout 600 python3 scripts/drift_check.py --strict
EXIT=0
$ grep -E "WARN|FAIL" drift_post.txt
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=30164d6 current=390569f
[WARN] project_knowledge: docs/aetheris/research/index.md stale — manifest=f77e565 current=6c62345
[WARN] project_knowledge: docs/methodology/milestone-methodology.md stale — manifest=c3e70a0 current=aa2f429
$ tail -2 drift_post.txt
Summary: 19 PASS  0 FAIL  3 WARN  8 INFO
```

Confirmed **member by member**, not by count. The pre-commit run at `34b1575` was the same three
with `backlog-2026-06.md` at `current=34b1575`; the only delta is that hash. All three are the
exempt manifest-staleness class and stay WARN under `--strict` by the stated exemption. The
manifest was **not** re-pinned. The `grep -E` filter is the elision: the 19 PASS and 8 INFO lines
are omitted and the summary line above carries their counts.

---

## What changed, file by file

- `cloudcost/tests/test_fetch_github.py` — one test,
  `test_the_normalized_inventory_is_readable_by_the_shared_rule_engine`: `--reference-date
  2026-09-10` added to the `detect_orphans.py` invocation; `assert counts["candidates"] == 0`
  becomes `== 1`; the two-line comment justifying `0` is replaced by six lines stating why the date
  is pinned and what it selects. `returncode == 0` and `skipped == 0` untouched.
- `docs/backlog-2026-06.md` — BL-205 removed with its separator (62 lines).
- `docs/backlog-2026-06-closed.md` — BL-205 added under a new `## The close — 2026-09-10 (third
  round)` container, `**Status:** DONE` (146 lines).

The diff is confined to the ticket's `Touches` list plus the two backlog files the close requires:

```
$ git show --format= --stat 390569f
 cloudcost/tests/test_fetch_github.py |  13 +++-
 docs/backlog-2026-06-closed.md       | 146 +++++++++++++++++++++++++++++++++++
 docs/backlog-2026-06.md              |  62 ---------------
 3 files changed, 155 insertions(+), 66 deletions(-)
```

Out of scope and untouched, as the ticket specified: `cloudcost/scripts/detect_orphans.py`, every
other test, the fixtures, `lib/`, the manifest.

## Decisions

**1. The fix is neither candidate the row offered, and the row's own "one thing to establish first"
is what settles that.** The row asked whether t3 had landed. It had: `97c61a0`, 2026-08-14, *"feat(m6
t3): the seat orphan rule — an activity timestamp, and what a saving is a figure of"*.

```
$ git log -1 --format='%h %ad %s' --date=short 97c61a0
97c61a0 2026-08-14 feat(m6 t3): the seat orphan rule — an activity timestamp, and what a saving is a figure of
$ git log -1 --format='%h %ad' --date=short -S 'def rule_idle_seat' -- cloudcost/scripts/detect_orphans.py
97c61a0 2026-08-14
```

The `-S` search returns that commit and no other, so `rule_idle_seat` entered the file there and
has not been re-introduced elsewhere. Therefore candidate (2) — *give seats a rule* — was
discharged four weeks before the row was filed, and candidate (1) — *pin `--reference-date`* — is
half a fix: the assertion was **obsolete**, not merely date-sensitive. Its comment deferred to a
ticket that had landed, and `candidates == 0` had been asserting the absence of a rule that exists.
A pin alone would have frozen a wrong expectation into a deterministic one.

**2. The live assertion is retired, and the close says so rather than leaving it to the diff.**
The row's Done-when demanded this explicitly. Before the pin the test tracked the account — the six
recorded seats aged against today, and the assertion would have changed value twice more this month.
After it, the test tracks a frozen date. That is a real loss of coverage. It is the right trade
because the seam this test exists to assert is `skipped == 0` over a resource shape the rule engine
has never seen, which is date-independent, and because it was the only **subprocess** caller of
`detect_orphans.py` not pinning a date. Enumerated at the baseline rather than recalled — the
population is larger than the ticket's four, and the extra member is the reason to run the command:

```
$ for f in $(git ls-tree --name-only 34b1575 cloudcost/tests/ | grep '\.py$'); do
    if git show 34b1575:$f | grep -q '"scripts" / "detect_orphans.py"'; then
      if git show 34b1575:$f | grep -q '"--reference-date"'; then echo "PINS      ${f#cloudcost/tests/}"
      else echo "NO PIN    ${f#cloudcost/tests/}"; fi
    fi
  done
PINS      test_compose_report_data.py
PINS      test_detect_orphans.py
NO PIN    test_fetch_github.py
PINS      test_fetch_linode.py
NO PIN    test_render_report.py
```

**`test_render_report.py` is a false positive of that search and is NOT a second offender.** Its
match is `(USE_CASE_ROOT / "scripts" / "detect_orphans.py").read_text(...)` at `:529` — it reads the
script's source as a positive control for an imports-nothing guard, and never runs it. It pins its
own reference in-process anyway:
`REF = detect_orphans.parse_timestamp("2026-07-27T00:00:00Z")` (`:33`). Both lines were read, not
inferred from the grep. `test_optimization_signals.py`, which the ticket lists, pins a date but
drives a different script, so it does not appear in this enumeration at all — the ticket's list of
four is a list of *pinning* tests, not of subprocess callers, and the two sets are not the same set.

**3. Deviation — the ticket's arithmetic is off by a day in both places; the count is not.** The
ticket states the firing seat is 35 days idle and the five others 28. Measured at the pin: **34d**
for `10000004` and **27–28d** for the rest (`10000003` is 28d, the other four 27d). The engine
floors a timestamp difference against a midnight reference, so a `05:39:27Z` activity stamp costs
the seat a day against the calendar count. The ticket's step 4 instructed a stop-and-report if the
**candidate count** was not 1; it was 1, so this is a deviation noted rather than a halt. The
comment in the test was written from the measured figures, not the ticket's.

**4. The assertion is on the count only.** The ticket said *"an assertion of the post-t3
outcome"*; asserting the rule name or the evidence would mean reading the candidates file and
widening a defect fix into coverage work. The rule name is recorded in this packet and in the close
instead.

---

## The diff, verbatim

Generated by `git show` into this file, not retyped. The identity check is in §Verbatim
control at the foot of this packet.

### `cloudcost/tests/test_fetch_github.py` — the whole change

```diff
diff --git a/cloudcost/tests/test_fetch_github.py b/cloudcost/tests/test_fetch_github.py
index 8a1553f..40a33dc 100644
--- a/cloudcost/tests/test_fetch_github.py
+++ b/cloudcost/tests/test_fetch_github.py
@@ -915,15 +915,20 @@ def test_the_normalized_inventory_is_readable_by_the_shared_rule_engine(
 
     result = subprocess.run(
         [sys.executable, str(USE_CASE_ROOT / "scripts" / "detect_orphans.py"),
-         str(tmp_path / f"github_inventory_{PERIOD}.json"), "--output-dir", str(tmp_path)],
+         str(tmp_path / f"github_inventory_{PERIOD}.json"), "--output-dir", str(tmp_path),
+         "--reference-date", "2026-09-10"],
         capture_output=True, text=True, cwd=USE_CASE_ROOT,
     )
     assert result.returncode == 0, result.stderr
     counts = json.loads(result.stdout)["counts"]
     assert counts["skipped"] == 0
-    # t3 is the ticket that gives seats a rule. Until it lands, a legible seat yields no
-    # candidate, and that is the correct result rather than a gap.
-    assert counts["candidates"] == 0
+    # The date is pinned because ages are otherwise measured against the inventory's
+    # `generated_at`, which the stub stamps at fetch time — so what this asserts would depend
+    # on the day the suite runs. Every other cross-stage test in the suite pins one.
+    # At 2026-09-10 the fixture's six seats fall either side of `rule_idle_seat`'s >30d with
+    # room to spare: seat 10000004 last acted 2026-08-06 and is 34d idle, the other five acted
+    # 2026-08-12/13 and are 27–28d. So one candidate, and not a boundary case.
+    assert counts["candidates"] == 1
 
 
 # ---------------------------------------------------------------------------------- fixtures
```

### The two backlog files

Not inlined. The elision is declared and bounded: `docs/backlog-2026-06.md` loses exactly the
62 lines BL-205 occupied (its `---` separator included) and gains nothing;
`docs/backlog-2026-06-closed.md` gains exactly those lines back, unchanged, inside a new
container with a supersession note before them and a close after them. The check that
establishes the correspondence is run rather than asserted, and it is §Verbatim control item 2 —
a sha256 over the carried body, computed before the write and re-computed from the committed
archive after it. The close text that is NOT carried is quoted in §The close below, in full.

---

## Verification

Every block transcribed from a command that had exited.

### 1. The measurement, taken BEFORE the assertion was written

The ticket's step 4 required the count be measured, not reasoned. The inventory was captured from
the test itself — `--basetemp` so pytest keeps its tmp dir — with the test **unmodified**, so the
inventory is the one the test actually produces and not a reconstruction:

```
$ rm -rf bt && timeout 300 python3 -m pytest -q --basetemp=bt \
    cloudcost/tests/test_fetch_github.py::test_the_normalized_inventory_is_readable_by_the_shared_rule_engine
pytest exit=1
$ find bt -name 'github_inventory_*.json'
bt/test_the_normalized_inventory_0/github_inventory_2026-07.json
```

`exit=1` is the defect itself — this is the pre-fix red, at `34b1575`. Its assertion line:

```
>       assert counts["candidates"] == 0
E       assert 1 == 0
```

Then `detect_orphans.py` over that inventory, at the pin:

```
$ python3 scripts/detect_orphans.py bt/.../github_inventory_2026-07.json \
      --output-dir out --reference-date 2026-09-10
EXIT=0
counts: {"resources": 6, "candidates": 1, "reported": 0, "excluded": 0, "skipped": 0}
 fired: idle_seat 10000004 ['last activity 2026-08-06 — idle 34d at ref 2026-09-10; threshold >30d', "attached_to is 'user:user-4' — the seat is assigned, so it is not idle in the unattached sense the other rules key on; it is an entitlement nobody is exercising", 'monthly_cost_estimate is $19.00/mo and a seat bills for as long as it is assigned regardless of use — so reclaiming it saves that whole figure']
```

**candidates = 1.** The number was read here and then written into the test, not the other way
round. `skipped` is 0 at the pin as well, so the pin does not disturb the assertion the test exists
for.

### 2. The six seats and their idle days at the pin

Computed from the same inventory, which is where the comment's figures come from:

```
10000001 2026-08-13T05:49:41Z -> 27 days
10000002 2026-08-13T05:41:14Z -> 27 days
10000003 2026-08-12T23:55:00Z -> 28 days
10000004 2026-08-06T05:39:27Z -> 34 days
10000005 2026-08-13T06:00:56Z -> 27 days
10000006 2026-08-13T05:58:15Z -> 27 days
```

`DEFAULT_SEAT_INACTIVE_DAYS = 30` at `cloudcost/scripts/detect_orphans.py:92`, read at HEAD. 34 > 30
fires; 28 ≤ 30 does not. The pin sits between 28 and 34 — six days of margin above, four below —
so it is **not** on the rule's boundary, which the ticket forbade.

### 3. Green after fix — gate 5, whole file

```
$ timeout 600 python3 -m pytest -q cloudcost/tests/test_fetch_github.py
.......................................................                  [100%]
55 passed in 9.44s
```

### 4. Mutation — is the new assertion load-bearing?

Three mutations, each applied to the committed file, run, then restored **from a working-copy
backup and verified by sha**, never by `git checkout --` (`CLAUDE.md` §Learning — the 2026-08-16
export boundary). Backup sha `80073e1f228053371e5c72911a14ae06f27b7d6d990dfb50c3ae15ffcb88ead7`;
the same sha was re-computed after each restore and `git status --short` was empty each time.

**M1 — the count.** `== 1` → `== 2`:

```
>       assert counts["candidates"] == 2
E       assert 1 == 2
```
Red. The count binds.

**M2 — the pin is wired.** `2026-09-10` → `2026-09-13`:

```
>       assert counts["candidates"] == 1
E       assert 6 == 1
```
Red, and **6** is exactly what the row's own independent sweep predicted for `2026-09-13`. The flag
reaches the script and the script consumes it.

**M3 — the pin removed entirely.** The `--reference-date` argument deleted, leaving the invocation
as it was at `34b1575`:

```
1 passed in 0.66s
```

**Green.** This is the finding in §Findings item 1, and it is reported rather than omitted: today's
date *is* the pin, so the flag this fix adds cannot be shown to be doing work today. M2 establishes
that it is wired; it does not establish that it is load-bearing, and this packet does not claim it.

### 5. t3's landing, established rather than taken from the ticket

```
$ git log -1 --format='%h %ad %s' --date=short 97c61a0
97c61a0 2026-08-14 feat(m6 t3): the seat orphan rule — an activity timestamp, and what a saving is a figure of
$ git log -1 --format='%h %ad' --date=short -S 'def rule_idle_seat' -- cloudcost/scripts/detect_orphans.py
97c61a0 2026-08-14
```

### 6. The push

```
$ git push origin main
To github.com:vishal-h/aetheris-agents.git
   34b1575..390569f  main -> main
PUSH EXIT=0
$ git status -sb
## main...origin/main
```

No divergence marker, so local and remote agree.

---

## The close, verbatim

BL-205 authored a judgment — which candidate was taken and why — so it is quoted here in full
rather than cited to the commit. Two blocks, both extracted from `docs/backlog-2026-06-closed.md`
at `390569f` by `sed` line range and checked in §Verbatim control. The 55 lines between them are
the row's own pre-work body, carried byte-identical from the open file and not reproduced twice.

### Container, heading and supersession note (lines 8000–8026)

````markdown
## The close — 2026-09-10 (third round)

**A third container on the same date, on the precedent of the second above.** That container's
own note explains itself by BL-204's non-membership in the first round; BL-205 belongs to
neither, so the date is qualified again rather than reused.

### BL-205 — DONE 2026-09-10 · the seat test's reference date is pinned and it asserts the post-t3 outcome (#TBD)
**Status:** DONE
**Kind:** defect — a green test that expires · **Size:** TBD — the fix is a judgement, not yet ruled · **Priority:** medium
**Section:** cloudcost (`cloudcost/tests/test_fetch_github.py`, `cloudcost/scripts/detect_orphans.py`)

`[Heading superseded 2026-09-10, corrected in place with this dated note per the harness
supersession rule (`../aetheris/CLAUDE.md` §Continuous learning → Workflow patterns). The heading
previously read:*

> `### BL-205 — the cloudcost seat-idleness test asserts `candidates == 0` against today's date, so it went red on a calendar boundary (#TBD)`

*and the depth-0 `**Status:**` field is REPLACED, `OPEN` -> `DONE`; BL-205 carries no `<details>`
block, so there is no archived status to preserve beside a live one. The heading was TRUE WHEN
WRITTEN and is false as of `cloudcost/tests/test_fetch_github.py` at this commit. The `**Size:**`
field is carried unchanged and still reads `TBD — the fix is a judgement, not yet ruled`; the
judgement is ruled below, and the field is left as the row filed it rather than back-filled.
EVERYTHING BETWEEN THIS NOTE AND THE **Neither candidate was taken** PARAGRAPH IS BYTE-IDENTICAL
to the row as it stood in `docs/backlog-2026-06.md` at `34b1575`, lines 9250–9304, its Done-when
included. sha256 of that body, computed before the write and verified against this file after it:
`5f271ee0a4aee5f7576bbbaa2ba5c90fa5dcac1419cd898e5876f00f2ade8a87`. WHAT FOLLOWS IT IS NOT
BYTE-IDENTICAL AND IS NOT CLAIMED TO BE.]`
````

### The close itself (lines 8083–8142, to end of file)

````markdown
**Neither candidate was taken, because the row's one-thing-to-establish settles them both.**
t3 **has** landed — `97c61a0`, 2026-08-14, *"feat(m6 t3): the seat orphan rule"*, which is where
`rule_idle_seat` and `DEFAULT_SEAT_INACTIVE_DAYS = 30` come from (`git log -S 'def rule_idle_seat'`
returns that commit and no other). So candidate (2), *give seats a rule*, was already discharged
four weeks before this row was filed, and candidate (1), *pin `--reference-date`*, was diagnosed as
the whole fix when it is half of one: the assertion was **obsolete**, not merely date-sensitive. Its
comment deferred to a ticket that had landed, and `candidates == 0` had been asserting the absence
of a rule that exists. A pin alone would have frozen a wrong expectation into a deterministic one.

**What landed.** `--reference-date 2026-09-10` on the `detect_orphans.py` invocation, and
`candidates == 1` in place of `candidates == 0`, with the comment replaced by one stating why the
date is pinned and what it selects. `returncode == 0` and `skipped == 0` are untouched — they are
the test's stated purpose, the adapter/rule-engine seam, and they are not what broke.

**The count was measured, not reasoned.** Before the assertion was written, `detect_orphans.py`
was run over the inventory the test itself produces, at the pin:

```
$ python3 scripts/detect_orphans.py <tmp>/github_inventory_2026-07.json \
      --output-dir <tmp> --reference-date 2026-09-10          # exit 0
{"resources": 6, "candidates": 1, "reported": 0, "excluded": 0, "skipped": 0}
```

The single candidate is `idle_seat` on seat `10000004`, whose own evidence string reads *"last
activity 2026-08-06 — idle 34d at ref 2026-09-10; threshold >30d"*. **34, not 35** — the engine
floors a timestamp difference against a midnight reference, so the seat's `05:39:27Z` costs it a
day against the calendar count. The nearest non-firing seat is 28d. The pin therefore sits between
28 and 34 with margin on both sides, and is not on the rule's `>30` boundary; the row's own swept
schedule (`2026-09-12` → 2, `2026-09-13` → 6) is now inert, because a frozen reference date cannot
reach either step.

**The live assertion is retired, and this says so rather than leaving it to the diff.** Before the
pin this test tracked the account: the six recorded seats aged against today, and the assertion
would have changed value twice more this month. After it, the test tracks a frozen date and asserts
what the rule engine does with a fixed inventory. That is a real loss of coverage and it is the
right trade here — the seam this test exists to assert is `skipped == 0` over a shape the engine
has never seen, which is date-independent, and the four other cross-stage tests in the suite
(`test_detect_orphans.py`, `test_compose_report_data.py`, `test_fetch_linode.py`,
`test_optimization_signals.py`) all pin a reference date for exactly this reason. This test was the
only one that did not.

**Gates**, all from the agents repo root at this commit. `python3 -m pytest -q
cloudcost/tests/test_fetch_github.py` — **55 passed**, exit 0. `python3 -m pytest -q -m "not
integration and not dormant"` under `timeout 1800` — **1621 passed, 3 skipped, 325 deselected
(integration=114, dormant=211), 7 xfailed in 213.18s**, exit 0, the exit read from the pytest
command itself and not from a wrapping shell; the run finished well inside its cap rather than
being cap-killed. `python3 scripts/backlog_status.py --check` — exit 0, *204 of 204 row ids*.

**`drift_check --strict` is owed after this commit, not inside it.** Check 8 reads committed
history, so its verdict on a commit that edits `docs/backlog-2026-06.md` — a manifest-tracked row
on the `export` surface — cannot be established by a run that precedes the commit, and a result
asserted here would be a claim landing in the same commit as the thing that would make it true.
Run pre-commit at `34b1575` it was **exit 0, 19 PASS 0 FAIL 3 WARN 8 INFO**, the three WARNs all
`project_knowledge` staleness (`backlog-2026-06.md`, `docs/aetheris/research/index.md`,
`docs/methodology/milestone-methodology.md`). The post-commit prediction is the **same three
members** — this commit re-stales `backlog-2026-06.md`'s row rather than adding one, and
`backlog-2026-06-closed.md` sits on the `on-demand` surface where check 8 compares nothing. The
run and its verdict are in this round's packet. The manifest is not re-pinned.

**Not touched:** `detect_orphans.py`, the fixtures, any other test, `lib/`, the manifest.
````

---

## Findings (captured, not acted on)

Nothing here was fixed or allowed to widen the diff.

**1. The pin this fix adds is not load-bearing today, and becomes so on 2026-09-12.** §Verification
4, M3: delete the `--reference-date` argument and the test still passes, because the pinned date
and today are the same date. The determinism the fix buys is real but unobservable for two more
days — a fails-before-fix control for *the pin* cannot be produced at this commit, only for the
assertion (M1) and for the flag's wiring (M2). Whoever reviews this after 2026-09-12 can produce
the missing control in one command by deleting the argument: the row's swept schedule says the
count goes to 2 that day and 6 the next. **This is a property of the date the ticket specified, not
a defect in the fix**, and the alternative — picking a pin far from today so the control is
producible now — would have moved the assertion nearer the `>30` boundary or past the next two step
changes, which the ticket forbade. Flagged because a reader running M3 today would otherwise
conclude the flag is inert.

**2. The row's `**Size:**` field still reads `TBD — the fix is a judgement, not yet ruled`.** The
judgement is ruled in the close directly beneath it. The field was carried unchanged rather than
back-filled, and the supersession note says so; `backlog_status.py --check` is indifferent to
`Size`, so this is a legibility wrinkle in the archive, not a gate matter. Left as filed on the
principle that the archived body is the record of what the row declared before the work.

**3. The ticket's arithmetic was wrong in both figures and nothing in the pipeline would have
caught it.** §Decisions 3. Had the ticket's step 4 instruction been *"confirm the seat is 35 days
idle"* rather than *"read the actual candidates count"*, this round would have stopped on a
correct fix. The instruction was phrased against the count — the thing the assertion rests on —
and that phrasing is what made it survivable. Recorded as a note on how the instruction was
written, not as a defect in it.

## For the reviewer, first

**The one judgment the ticket does not settle** is whether retiring a live assertion is acceptable
here at all. The ticket directed the pin, and §Decisions 2 argues the trade is right — the seam
this test exists for (`skipped == 0` over an unfamiliar resource shape) is date-independent, so
what the pin freezes is not what the test is for. If that reading is wrong, the alternative is not
a different pin but a second test: keep this one pinned, and add a date-free one asserting only the
seam. That was not done, being outside a defect fix's scope.

**Round type was declared** — defect fix (test) — as `CLAUDE.md` §What this repo is requires, and
the round produced what the type predicts: one test file, no source change, no fixture change.

---

## Verbatim control

**1. The diff block in §The diff, verbatim** was generated by `git show` into this file and then
checked against the commit rather than asserted to match:

```
fenced diff blocks found: 1
test diff: identical to `git show 390569f` -> True  (packet 29 lines, live 29 lines)
```

**2. The two blocks in §The close, verbatim** were extracted by `sed` line range and checked the
same way against the committed archive:

```
fenced markdown blocks found: 2
container+note: identical to committed archive -> True  (packet 27 lines, live 27 lines)
close body:     identical to committed archive -> True  (packet 60 lines, live 60 lines)
```

**This control fired, and its first run is why the blocks carry four-backtick fences.** The close
body contains a fenced block of its own, so the three-backtick wrapper it was first written with
was closed by the *inner* fence: the control reported `close body: identical -> False (packet 17
lines, live 60 lines)`, a silent 43-line truncation inside a block labelled verbatim. Nothing in
the rendered text marked the cut — the 17 lines that survived were all accurate, and ended on a
line that reads finished. Recorded rather than quietly fixed, because it is the exact failure the
verbatim rule exists for and the packet is the artifact that travels.

**3. The body carried into the archive** — the 55 lines between the two quoted blocks — was
checked by sha256 computed **before** the write and re-computed from the committed file after it,
not asserted:

```
$ sha256sum bl205_body.md            # extracted from docs/backlog-2026-06.md at 34b1575, lines 9250–9304
5f271ee0a4aee5f7576bbbaa2ba5c90fa5dcac1419cd898e5876f00f2ade8a87
$ diff bl205_body.md archived_body.md && echo "BYTE-IDENTICAL: yes" && sha256sum archived_body.md
BYTE-IDENTICAL: yes
5f271ee0a4aee5f7576bbbaa2ba5c90fa5dcac1419cd898e5876f00f2ade8a87
```

Line counts and shas are published beside each identity result because a truncated capture and a
complete one are indistinguishable by content alone.
