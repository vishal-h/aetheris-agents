# Review — m3-cloudcost t3 — round 0

Reviewed at `m3-t3-run@14489aa`. Click-through gate passed on both surfaces (report and
capability-matrix view), observed by the human at that branch. **One blocking finding, and it
is a filing action rather than a code change.**

The plant gate firing before the run — reporting zero and stopping rather than running the
sprint and reading the answer off a `[FAIL]` — is the single best decision in this ticket. So
is discriminating the zero with `not_inventoried: []` rather than treating an empty list as an
observation. The M1 mutation on the negative proof is the right instinct on the milestone's
central claim: an absence that cannot be shown to become a presence is not evidence.

## Findings

1. **[blocking] Two real defects are recorded only in an implementation-notes file, which does
   not travel.** §3.3's finding — `sprint.sh:2670` gates the D2 credential grep on
   `CC_PROVIDER == "aws"`, so no sprint assertion covers done-when 7 on the Linode or DO legs —
   is a genuine gap in a merged file, found by a ticket that correctly could not fix it. §4's
   `run.json` `2>&1` defect is the same shape: pre-existing, provider-wide, and invisible to
   everyone who reads `no-json` as noise. The repo's standing rule is that a deferred finding
   gets a row the day it is found, and m1 closed with the explicit lesson that *an
   implementation-notes file does not travel to the next ticket's session*. File both as
   backlog rows before merge — `docs/backlog-2026-06.md` is outside §t3's Touches, but BL-098
   was filed from inside t1 on the same reasoning, so declare the deviation and file. Suggested
   content: the D2 row records that a provider whose credential is never grepped has a D2
   posture asserted rather than checked, and that the fix is the same shape as the Linode
   `CC_HERMETIC` strip t2 landed; the `run.json` row records that the status line has read
   `no-json` on every cloudcost run ever recorded, that the assertion is the surrounding exit
   status so nothing is mis-asserted, and that the cost is a signal nobody will read when it
   finally matters. While you are in the file, append to **BL-069** that the Linode leg went
   green once — run `cloudcost-orch-linode-h5lltQ`, `idle_load_balancer`, $10.00 — and reverts
   to red when the plant is deleted; without that line the row reads as never-green and the
   next person re-derives what t3 already established.

2. **[non-blocking] The milestone summary marks done-when 4 ✓ in the same commit whose Status
   line says "Merge pending the click-through gate."** Both cannot be true at commit time, and
   the ✓ was ahead of its evidence by about an hour. It is now satisfied, so fix it forward
   rather than backward: leave the ✓ and change the Status line to record the gate as passed,
   naming what was observed on both surfaces. The reason this is worth a line at all is that it
   is the same self-falsifying class as the `DRAFT — awaiting commit` line the arbiter caught at
   ratification, and this milestone has now produced three instances of a claim landing one
   commit ahead of the thing that makes it true.

## Cross-ticket notes

- **Two of the three Linode-shaped defects in `sprint.sh` were found by tickets that could not
  fix them** — t1 found the wall-clock filename, t2 fixed it; t3 found the AWS-only D2 grep and
  cannot. That is the ticket boundary working as designed, but only if the finding lands
  somewhere durable, which is finding 1.
- **The plant priced from the types endpoint while July's invoice corroborated the same rate
  from a different source.** That is the `rate_basis` argument (§D-L5) demonstrated rather than
  argued, and it is the strongest evidence in the milestone for retro-fitting it uniformly.
- The `Cloudcost · {provider}` brace-vs-angle spelling being left as generated is correct — the
  cell is reconciled, and hand-editing a generated artifact to match a doc's prose is what
  §t3's Do-not-generate exists to prevent.
