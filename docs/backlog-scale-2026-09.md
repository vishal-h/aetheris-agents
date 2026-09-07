# Backlog scale and the order the fixes go in

**Status:** analysis, not a decision. No row filed for the work it describes.
**Written:** 2026-09-07 by claude-ui.
**Measurements read at:** `aetheris-agents` `9962454` / `87a4c30` unless stated otherwise. The file has grown since — see §6.

> Every figure below carries the read it rests on. A count over a moving set goes stale the moment it is published; the commands are given so a later reader re-derives rather than trusts.

---

## 1. The measurement

`docs/backlog-2026-06.md` at `87a4c30`: **6,352 lines / 392 KB / 127 rows.**

| | rows | bytes |
|---|---|---|
| open | 102 | 304 KB |
| done | 25 | 87 KB |

```bash
python3 - <<'EOF'
import re
lines = open('docs/backlog-2026-06.md').read().split('\n')
starts = [i for i,l in enumerate(lines) if re.match(r'^### BL-\d+', l)] + [len(lines)]
for a,b in zip(starts, starts[1:]):
    body = '\n'.join(lines[a:b])
    m = re.search(r'\*\*Status:\*\*\s*(\w+)', body)
    print(re.match(r'^### (BL-\d+)', lines[a]).group(1), (m.group(1) if m else 'open').lower(), b-a, len(body))
EOF
```

**Archiving closed rows recovers 22%.** That is the first thing worth knowing, because it is the opposite of the intuition: the file is not large because of history. It is large because 102 rows are open. 301 of the 314 date stamps in the file fall in July–August, so effectively the whole document is two months old and still accreting.

---

## 2. The sharpest cost is project knowledge, not the repo

The file is `docs/project-knowledge-manifest.md` row 38 — exported to the Claude project. At ~400 KB, retrieval returns arbitrary chunks.

**Observed, not predicted:** a `project_search` for payslip/Drive upload during the 2026-09-07 session returned BL-010 (boxy-pipeline order formatter) and BL-077 (`sprint.sh` exit codes). Neither is related to the query. The row that *was* relevant — the drive upload defect — was not among the hits, and the defect was ultimately found by reading the source instead.

And because export is remove-all-upload-all against the full manifest set (never a hash-driven diff — the manifest header is explicit that the check is blind in the other direction), **every backlog edit re-uploads the whole file.**

---

## 3. The mechanisms

1. **Archive on close.** Done rows move whole to `docs/backlog-2026-06-closed.md`; the live file keeps a one-line stub (ID, title, close date, pointer). Recovers the 87 KB — but the real gain is that closing a row now *removes* bytes rather than adding them, which turns the growth curve from monotonic into sawtooth. **This mechanism exists as of 2026-09-07** (`docs/backlog-2026-06-closed.md` is present).
2. **Split on the section boundaries that already exist.** The seven `##` headings map to ownership and are stable: `docs/backlog/{housekeeping,harness,rig,milestones,drift,boxy-pipeline}.md`. Each lands at 50–100 KB. The manifest gets N rows instead of 1, so editing the rig backlog re-exports rig alone.
3. **Tombstone the old path.** `docs/backlog-2026-06.md` becomes a ten-line index. Roughly 20 implementation notes and milestone READMEs cite that path; those are point-in-time audit records and must not be rewritten. The tombstone keeps them resolving — and stays **inert**, which is why it is not a candidate home for §4.
4. **IDs stay global and immutable.** `BL-NNN` never renumbers and never moves except into the archive, so `grep -rn BL-070 docs/backlog/` is the index. No hand-maintained index file — that is the mirror-that-drifts methodology §1.1 warns about.
5. **Drop the date from the live filename.** `backlog-2026-06.md` carrying rows filed in September is a stale mirror in the one place no checker looks. `closed-2026.md` keeps its year because it genuinely is an annual archive.

**Cost is lower than it looks:** `scripts/drift_check.py` does not hardcode the path — check 8 parses the manifest table generically. The change is the manifest rows, `prompts/bl-002-refresh-project-knowledge.md`, the file moves, and a post-commit `--strict` run plus a full re-export per the standing export-boundary rule.

---

## 4. The execution queue needs a declared home before the split

`## Suggested order` is the file's one genuinely cross-cutting structure: it spans every section, so §3.2's split orphans it. **Declare its home before the split** or the one thing that sequences work loses its address.

`docs/backlog/queue.md`, holding **IDs and one-line rationale only — never row content**. Row content in the queue makes it a second source of truth, which is the §1.1 failure the rest of this analysis is built to avoid.

Not the tombstone: a live queue inside a deprecated, mis-dated file re-animates it, and inertness is the tombstone's whole function.

---

## 5. Ordering — sweep before split

1. **Archive-on-close mechanism** — so closures have somewhere to go. *(Done.)*
2. **The `superseded`/`wontfix` sweep** — closures flow straight into the archive.
3. **Split what remains — conditionally.** Re-measure first. If the sweep closes thirty rows, the remainder may not need splitting at all.

Splitting first means restructuring rows that are about to be tombstoned. **The sweep is the fix; the reorg is symptom relief.**

---

## 6. The part none of that addresses, with the evidence a day of work supplied

Filing outpaces closing. Some rows are near-certainly obsoleted by later milestones — BL-070 was described as retiring the code BL-071 patches.

**The 2026-09-07 session is a clean measurement of the ratio.** In one day it filed **six rows** — BUG-001, BL-190, BL-191, BL-192, BL-193, BL-194 — and closed **none of the pre-existing 102**. BUG-001 is `fixed` with one Done-when arm outstanding; the other five are open. `backlog_resolution` moved 192 → 193 rows over the union of live and archived files.

Against that, the day's production-code change was about 40 lines in one function, plus ~100 lines of tests. The prose-to-code ratio for the day was roughly 12:1, over nine review rounds.

That is not an argument the rows were unwarranted — BL-193 documents a real latent defect (two equal 300 000 ms timeouts racing, the less informative one structurally winning) and BL-191 documents a sprint arm that cannot pass its own prerequisite loop. It is an argument that **a backlog nobody can hold generates work**, and that the sweep is the intervention with compounding returns.

**A stopping rule worth adopting alongside it:** a review round that changes no code and closes no defect gets one round; remaining findings become backlog rows, not another round. That converts an open-ended loop into a queue, which is the thing that can be prioritised against real work.

---

## 7. What to re-measure before acting

The §1 figures are from `87a4c30` and the file has grown by roughly 500 lines since. Before any sweep or split:

- re-run §1's script for the current open/done split and byte weights;
- re-derive the per-section sizes, since the split's shape depends on them;
- check whether `docs/backlog-2026-06-closed.md` has absorbed anything since the archive mechanism landed.

Publishing the old numbers as current is the failure this document is trying to make hard, so it does not restate them as if they were.
