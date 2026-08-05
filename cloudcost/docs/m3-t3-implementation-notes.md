# m3-cloudcost t3 — the live run, the click-through gate, and BL-090

**Branch:** `m3-t3-run` (off `main@f5c7fe5`).
**Ticket:** `cloudcost/m3-milestone.md` §t3, doc **rev 7** (`m3-milestone.md:42-44`; rev 6 at read
time, rev 7 authored by the arbiter mid-session — see §3.2).
**Inherited:** `cloudcost/docs/m3-t1-implementation-notes.md` §10;
`cloudcost/docs/m3-t2-implementation-notes.md` §6; `docs/reviews/m3-cloudcost-t1-review.md`,
`-t2-review.md`.
**Live reads:** 2026-08-05, read-only, against the account's own PAT.

---

## 1. The plant was a blocking gate, and it fired

§t3's done-check opens by planting a zero-backend NodeBalancer. That plant is human-owned, so the
first action was to establish whether it existed — not to run the sprint and read the answer off a
`[FAIL]`.

**First read — the plant did not exist.** Two NodeBalancers, both serving:

```
1343674 ccm-8cac00823f9b | common | ap-west | attached_to='backends:2' | $10.0
1433944 ccm-ba3fa112725b | common | ap-west | attached_to='backends:2' | $10.0
ZERO-BACKEND COUNT: 0
```

The sprint was **not run**, the `≥1` assertion was **not relaxed** and **not re-pointed**. Reported
and stopped, which is what §Rule reachability's "do not relax the assertion; plant the resource"
asks for.

**The zero was proven, not assumed.** *Absent is unknown, not zero* — an absent NodeBalancer and an
unread NodeBalancer class arrive in the same shape (an empty list). The fetch summary discriminates
them: `status: ok`, `not_inventoried: []`, `errors: []`, `warnings: []`, so the class was read in
full and the zero is an observation. Corroborated by `detect_orphans.py` over that same inventory:
**0 candidates, 0 skipped**, matching t1 exactly.

**Second read, after the human created it — exactly one:**

```
2405879 aetheris-m3-bl069-plant | common | us-southeast | attached_to=None | $10.0
ZERO-BACKEND COUNT: 1
```

`common`, and priced at a **real $10.00** rather than the `0.00` a `premium` balancer or a reserved
IP would have produced (§Rule reachability). The engine fires on it before the sprint ever runs:
1 candidate, `idle_load_balancer`, confidence 0.85, `monthly_saving_estimate` 10.0.

## 2. The run

`CLOUDCOST_PROVIDER=linode ./scripts/sprint.sh cloudcost` — **18 `[OK]`, 0 `[FAIL]`, 0 `[WARN]`**,
counted with `grep -c` rather than read off the tail, because `fail` sets no exit status (BL-077)
and a count is the only complete-output form of "every line passed".

Run id `cloudcost-orch-linode-h5lltQ`, status `done`, label `Cloudcost · Linode`.

**Seam 7 held in production.** Every artifact is named **2026-07** on a run executed 2026-08-05.
The invoice behind it is `#32251471`, **issued** `2026-08-01T04:36:37`, **covering**
`2026-07-01T04:00:00 → 2026-08-01T03:59:59`. A `cloudcost_report_2026-08.html` would have meant a
regression to the wall clock; there is none. `period_basis` rides under `provider_extra`, the
sanctioned key, not at top level (the t1 r0 F3 relocation).

**The orphan carries a dollar figure and its basis.** `$10.00/month`, MEDIUM band (0.85), with both
evidence lines rendered in the HTML beside the resource id, region and `raw_ref`:

```
aetheris-m3-bl069-plant | load_balancer | linode | 10.00 USD / month
2405879 | us-southeast | linode://nodebalancers/2405879
rule idle_load_balancer · confidence 0.85 (base 0.85, no modifiers)
  attached_to is null — no backend instances and no backend tag
  a tag-targeted load balancer would carry attached_to = 'tag:<name>' and is excluded from this rule
```

That is done-when 1's "reviewable without the Linode console" satisfied on the page, not in the
payload. Note where the $10.00 comes from: the live `/nodebalancers/types` price endpoint, **not**
an invoice line — the plant was created in August and cannot appear on July's invoice. July's
`NodeBalancer` line reads `$20.00`, which is the two pre-existing balancers at the same rate, so
the invoice independently corroborates the rate the estimate was priced at.

**Done-when 7 needed a hand-run arm** — see §3.3. Both arms clean, with a working control.

## 3. Decisions and declared deviations

### 3.1 The PAT expiry — `cloudcost/runbook.md`, outside §t3's Touches

Filled per the human's verbatim text: expiry **2027-02-04**, PAT label `aetheris-cloudcost`,
created 2026-08-04 15:34. Declared because the file is not in Touches. The reason it was done here
rather than deferred: it is the milestone's **one open item** (t2 §6, t2 review F4), and t3 is the
last point in m3 where anyone is looking at that credential. The text records the console's
displayed value and names the two derivations that disagree with it ("6 months" → 2027-02-04,
"180 days" → 2027-01-31), so the next reader cannot re-derive a wrong date from the creation stamp.

### 3.2 The matrix Summary count is **eight**, and §t3 said seven

`docs/capability-matrix.md`'s Summary row went `| cloudcost | 1 | 6 |` → `| 1 | 8 |`, total 82 → 84.
§t3 and the ticket prompt both predicted **seven**.

The prediction was stale, not wrong-in-kind: it comes from scout §A9, written against `dc8c077` —
six rows on the matrix plus the omitted `detect_optimization_signals.py`. t1 then added
`fetch_linode.py`, and the section agent collects every `.py` in `cloudcost/scripts/` including the
import-only `_normalized.py` (`agents/capability_matrix_cloudcost.exs:41-45`). Eight files on disk,
eight rows.

Handled as *ticket text quoting repo state*: reported as the regen produced it, **not** followed —
no hand-edit down to seven, and no edit to §t3 (t3's Touches scopes `m3-milestone.md` to the
milestone summary). The arbiter subsequently issued **rev 7** correcting both sites, applied in this
session; that edit is the arbiter's, not a t3 adjudication.

### 3.3 The sprint's D2 credential grep has no Linode arm, so done-when 7 was run by hand

`sprint.sh:2670` gates the credential grep on `CC_PROVIDER == "aws"`. Done-when 7 requires
`CLOUDCOST_LINODE_TOKEN` to appear in neither stdout, stderr nor the trajectory, and no sprint
assertion covers that on the Linode leg — so a green Linode sprint says nothing about done-when 7.

Run by hand, in the shape the AWS arm uses: gated on the searched file demonstrably having content
and a `run_id`, so the grep cannot pass vacuously over an empty file. Both arms clean — `run.json`
(695 bytes, carries the run id) and the trajectory (1930 bytes). Plus an explicit anti-vacuity
control the AWS arm does not have: the same `grep -qF` against a file constructed to contain the
token **does** find it, so the two clean results are the grep working rather than the grep being
incapable of matching.

`sprint.sh` is in t2's Touches, not t3's, so the missing arm is recorded here and not fixed.
It is a real gap: the same reasoning that put a Linode strip in `CC_HERMETIC` applies to the D2
grep, and a provider whose credential is never grepped is a provider whose D2 posture is asserted
rather than checked.

### 3.4 The milestone doc's Status line, edited beyond the arbiter's two sites

`cloudcost/m3-milestone.md` **is** in t3's Touches, but scoped to "the milestone summary at close".
The Status line read `t3 next.` — which the same commit makes false, since it lands a summary
written at t3 close. Updated to `t3 DONE … Merge pending the click-through gate`, on the same
leaving-it-self-contradictory reasoning as the runbook edit. Declared because it is outside the
Touches entry's stated scope and outside the arbiter's rev-7 instruction, which named two sites.

### 3.5 BL-069 is discharged for the Linode leg only, and only while the plant lives

The `≥1` assertion went **green** on this run — the first time any leg has. That is done-when 1, and
it is not BL-069's closure:

- The **DO** leg's reserved IP was deleted 2026-07-30 and the **AWS** leg's Elastic IP is
  `m2-milestone.md` §Prereqs 3, still PENDING. Both remain red.
- The Linode plant is deleted after the run (`runbook.md:310`), at which point the Linode leg
  reverts to red too.

So the assertion is still armed and still correctly named in the sprint's `fail` text. What t3
proves is that it *can* go green on real account state, with a real dollar figure, through an
unchanged shared engine — which is what the assertion was always for. `docs/backlog-2026-06.md` is
outside Touches and is not edited; the disposition is stated here for whoever closes BL-069.

The runbook's §"Exercising the ≥1-orphan path" opening ("no live account currently carries an
orphan-shaped resource") is left alone deliberately: it describes the steady state, and the steady
state returns the moment the plant is deleted.

## 4. Surprises

- **The sprint's orchestrator status line reads `no-json`, on every provider.** `run_agent`'s inline
  equivalent redirects `2>&1` into `run.json` (`sprint.sh:2571-2572`), so the harness's boot
  warnings and the two `[sandbox]` lines are prepended to the JSON document and `jq -r '.status'`
  cannot parse the file. The payload is intact on the last line
  (`{"label":"Cloudcost · Linode","status":"done","run_id":"cloudcost-orch-linode-h5lltQ"}`), and
  the *assertion* is the surrounding `if` on exit status rather than the `jq`, so nothing is
  mis-asserted — the display is just wrong, and has been for every cloudcost run ever recorded.
  Pre-existing, provider-independent, `sprint.sh` out of Touches. Not fixed here; noted because a
  status field that always reads `no-json` is one nobody will read as a signal when it matters.

- **The regenerated Label cell reads `Cloudcost · {provider}`, where §t3 predicts
  `Cloudcost · <provider>`.** The agent is rendering the Elixir interpolation
  `label: "Cloudcost · #{provider_name}"` (`cloudcost/agents/cloudcost_orchestrator.exs:317`) with a
  placeholder of its own choosing. Substantively this is the BL-090 cell reconciled — it is no
  longer the pre-BL-083 static `Cloudcost Orchestrator`, and it correctly signals that the label
  varies per run. The angle-vs-brace spelling is the agent's, and a hand-edit to match the doc is
  exactly what §t3's Do-not-generate forbids. Left as generated.

- **The plant priced from the types endpoint, and the invoice agreed independently.** See §2. This
  is the `rate_basis` argument in miniature: the estimate and the settled invoice line were derived
  from different sources and matched, which is stronger than either alone.

## 5. Mutation record

Load-bearing checks were watched failing in the state they guard, then restored.

| # | Broken state constructed | Guard that fired |
|---|---|---|
| M1 | a probe line appended to `detect_orphans.py` | the negative proof reports `1 file changed, 2 insertions(+)`; empty again after `git checkout --`, working tree clean |
| M2 | a file constructed to contain the live token | the D2 `grep -qF` finds it — so the two clean results in §3.3 are the grep working, not the grep being unable to match |

M1 matters because an empty `git diff --stat` is exactly what a **mistyped path** produces. The
milestone's central claim is an absence of output from one command; an absence that cannot be shown
to become a presence is not evidence.

## 6. Carried forward / open

- **The sprint's D2 grep covers AWS only** (§3.3). The Linode and DO legs have no credential
  assertion. `sprint.sh` is outside t3's Touches; this is the second Linode-shaped gap found in that
  file by a ticket that could not fix it (t1 found the wall-clock filename, which t2 fixed).
- **`run.json`'s `2>&1` makes the status line unparseable** (§4). Pre-existing and provider-wide.
- **BL-069 stays armed** (§3.5) — DO and AWS legs red, Linode red again once the plant is deleted.
- **The plant must be deleted** — `aetheris-m3-bl069-plant` (`2405879`, us-southeast), a console
  write, human-owned. The agent stays read-only and did not delete it.
- **The two stale `fetch_linode.py` strings** (`:1291` `--period` help, `:1386` runbook citation)
  are still open, recorded in the milestone's §Open items with the BL-078 trigger shape. Still
  outside every m3 ticket's Touches; still not fixed.
- **`project_knowledge` manifest staleness** for `docs/capability-matrix.md` — expected, exempt, and
  cleared at the export boundary, which follows the merge and is not t3's.
