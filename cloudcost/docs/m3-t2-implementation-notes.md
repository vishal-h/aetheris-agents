# m3-cloudcost t2 — wiring: orchestrator literal, manifest, sprint case, runbook, BL-092

**Branch:** `m3-t2-wiring` (off `main@2000e9b`).
**Ticket:** `cloudcost/m3-milestone.md` §t2, doc **rev 5** (`m3-milestone.md:27-31`).
**Inherited:** `cloudcost/docs/m3-t1-implementation-notes.md` §10 "Obligations t2 inherits";
`docs/reviews/m3-cloudcost-t1-review.md` r1 F2 and F3.

No live Linode run and no sprint execution happened in this session — both are §t3's
done-check. What t2 could verify without them is verified; §7 says which is which.

---

## 1. What the ticket found already broken

Two tests in `tests/test_tools_manifests.py` were **red at `main` before any edit**, and for
exactly the gap t2 closes:

```
FAILED test_discovery_sweep_intact           — asserts 6 cloudcost CLIs, disk carries 7
FAILED test_no_undeclared_scripts[cloudcost] — ['scripts/fetch_linode.py']
```

t1 added the seventh runnable CLI; declaring it is t2's. They are also this ticket's
anti-vacuity control for the manifest work: they fail before and pass after, and **neither was
relaxed** — `test_no_undeclared_scripts` was not touched at all, and the count assertion moved
6→7 to match a disk state that had already changed.

This is the BL-084 suite doing the job it was built for: the manifest and the scripts directory
cannot silently disagree.

---

## 2. Decisions

### 2a. The Linode credential raise is in scope, and Linode sits on the AWS side of the line

§t2's Contract refs cite `cloudcost_orchestrator.exs:42-49` (the provider literal table), which
reads as a limit on what may change. It is not: **Touches names the file**, and Contract refs
name what to *read*. Adjudicated with the human before implementing.

The substantive question is whether Linode gets AWS's fail-fast raise or DO's exemption. The
file already records why DO has none (`:72-74` in the edited file): DO is the **default** sink,
and the offline `Code.eval_file/1` done-check has to keep evaluating clean on a machine with no
DO token. Linode is never the default — it can only be reached by naming it — so that argument
does not reach it, and the repo's standing rule (*explicit sink selection with fail-fast*,
root `CLAUDE.md`) names this case directly.

The concrete gain is not "it fails either way". Without the raise the run still fails, but ~4 s
into STEP 1, as a tool error the model must then interpret and report. The raise keeps *does
this pipeline complete* a harness property rather than a model behaviour — the same argument
BL-096 makes for declaring STEP 1's timeout.

**Empty string is treated as absent** (`in [nil, ""]`). The human asked for this to be stated as
a divergence if AWS's check were nil-only. It is not: `cloudcost_orchestrator.exs:65` (pre-edit
numbering) already uses `in [nil, ""]`. So this mirrors the existing check exactly, and there is
no divergence to declare.

**Consequence for §t2's own done-check, and it must be read as a change:** line 1
(`CLOUDCOST_PROVIDER=linode mix run --eval …` succeeding) now requires `CLOUDCOST_LINODE_TOKEN`
to be present, so it runs after `set -a; . ~/.secrets/linode-cloudcost.env; set +a`. Both arms
are in the packet — the eval succeeding with the token, and raising without it.

### 2b. The sprint locates the report by discovery, not by construction (t1 obligation 1)

`sprint.sh` built `cloudcost_report_$(date -u +%Y-%m).html` and its `report_data_` sibling from
the wall clock, with a comment asserting that is "what both adapters default to". True of DO and
AWS, **false of Linode** (§Seam 7), so the Linode leg would have failed its report-exists
assertion for a reason with nothing to do with the report. The comment is now rewritten; it was
asserting something no longer true, which is worse than the code.

Replaced by `mapfile` over `find … -name 'cloudcost_report_*.html'`, then **exactly one** or
`fail`. Three notes:

- **`find`, not `shopt -s nullglob`.** The script runs `set -euo pipefail` and uses `shopt`
  nowhere; toggling a shell option mid-script for one glob is a footgun for every later case.
- **Exactly-one, not first-match.** Two reports in the directory means the stale-artifact clear
  did not happen or two runs shared a tree; the old code would silently have picked whichever
  matched the clock. Ambiguity is now a `fail`, which is strictly more than the old check saw.
- **Discovery is not a stale-artifact hazard here.** `$CLOUDCOST_OUT` is emptied immediately
  before the run (the m1-t5 clear), so anything matching afterwards was written by *this* run.
  That pre-existing clear is what makes glob-by-discovery sound; without it this would be the
  greening-on-a-previous-run defect that clear exists to prevent.

The alternative §t2 allows — reading STEP 1's reported period — was rejected: the period reaches
the sprint only through the model's STEP 5 prose, so parsing it would put a deterministic check
back on model output.

### 2c. `CC_HERMETIC` strips two names, and the two it does not strip are the interesting half

Added `-u LINODE_CLI_TOKEN -u LINODE_TOKEN` — exactly `fetch_linode.SHADOWING_ENV`
(`cloudcost/scripts/fetch_linode.py:68`), so the strip list and the adapter's own notion of what
shadows it cannot drift apart.

Two names were deliberately **left out**, and both exclusions are load-bearing:

- **`LINODE_CLI_API_HOST` / `_VERSION` / `_SCHEME`** (`fetch_linode.py:73-77`) are a *worse*
  hazard than a shadow token — they redirect **where a credential is sent**. But the adapter
  handles them by warning, not by reading them, and stripping them in the prefix would delete
  the only signal that hazard has. A sprint that silently sanitised them would report clean on
  a workstation that is misconfigured for every non-sprint run.
- **`LINODE_BILLING`** — the §Prerequisites 2 variable. No Linode library reads it (scout §B8),
  so it is not a shadowing vector for this adapter; stripping it would imply otherwise.

### 2d. A separate Linode poison-control block, not a widened AWS probe

The AWS block's assertion strings encode a specific shape: three env names plus a
credentials-*file* arm, compared against one exact string. Linode has two token spellings and no
file arm. Threading both families through one probe would have produced an assertion string that
says less than either does now, and would have rewritten the AWS arm's expected value — a change
to a passing check made for an unrelated reason. Two blocks; the AWS one is byte-unchanged.

Arms (i) and (ii) run for **every** provider, matching the AWS block: the strip is a property of
the prefix, not of the selected provider. Arm (iii) is gated on `linode`, matching the AWS
block's own `aws` gate (`../aetheris/scripts/sprint.sh:2512` post-edit), because only then is
the surviving credential present to check.

### 2e. BL-092 discovers manifests rather than listing them, and carries its own negative control

The test module walks `CARGO_MANIFEST_DIR/../..` for `<use_case>/tools.json`, mirroring the
walker's own exclusions, so a manifest added later is covered without editing `tools.rs`. Three
guards make the walk mean something:

- `discovery_finds_every_committed_manifest` asserts the **set**, not a count. A discovery that
  silently returned nothing would otherwise pass a round-trip over zero manifests.
- `a_manifest_missing_an_env_dep_field_is_rejected` is the mutation: it drops `"masked"` from a
  real `EnvDep` and asserts `Err`. Without it the round-trip test has only ever been seen
  passing, which by the Silent-wrong-answer rule is not yet a check. It also asserts the
  mutation *applied* (`assert_ne!`), so a fixture reshuffle fails loudly instead of silently
  testing the unmutated string.
- `env_deps_dedup_walk_keeps_the_first_occurrence_only` is anchored on a key that genuinely
  repeats (`CLOUDCOST_AWS_ACCESS_KEY_ID`, declared by both `fetch_aws` and
  `detect_optimization_signals`) and asserts that repetition first — otherwise a dedup over an
  already-unique list would pass while proving nothing.

`tools.rs` is **byte-identical outside `#[cfg(test)]`**: `157 insertions(+), 0 deletions`, one
hunk appended at end-of-file. The `git diff` is in the packet.

---

## 3. Deviations, declared

1. **`tests/test_tools_manifests.py` lives at the repo root, not `cloudcost/tests/`.** §t2's
   Touches and Done-check both say `cloudcost/tests/test_tools_manifests.py`; the file is at
   `tests/test_tools_manifests.py` and computes `REPO_ROOT = Path(__file__).resolve().parent.parent`
   (`:36`), which only works from the root. §t2's done-check line 3 as written would collect
   nothing. Real path used, and it is the one in the packet.

2. **`cloudcost/tests/` and `tests/` cannot be collected in one pytest invocation.** Both carry
   a `conftest.py` and the module names collide (`ImportError: cannot import name 'FIXTURES'`).
   Pre-existing, unrelated to t2 — both suites are run separately in the packet, and the full
   output of each is there.

3. **Runbook edits beyond §t2's literal list.** §t2 names the `### Linode` subsection, the
   partial-run line and the BL-096 record. Four more landed in the same file, each because
   leaving it would have made the file self-contradictory after the mandated edits:
   - The **Linode BL-069 planting recipe** in §"Exercising the ≥1-orphan path". t3's Touches does
     not include the runbook, and §t3's own prompt cites `cloudcost/runbook.md:197` for the
     planting procedure — a procedure that named only DO and AWS. Writing it in t2 is what
     methodology §6 asks (the operator needs it to run the thing t2 just wired), and the
     alternative was a citation into a section that does not answer it.
   - The **"Step 1 shows a timeout" block**, which said the orchestrator "declares no
     `timeout_ms`" and to "expect to see it until BL-096 lands". BL-096 landed 2026-08-04
     (`32933d8`, `docs/backlog-2026-06.md:3351`) and the declaration is at `:147`. Recording
     t2's BL-096 *confirmation* three sections above a block saying BL-096 has not landed was
     not an option.
   - The **five-places wiring enumeration** in §"Adding a provider". t2 found those five one at
     a time; §"Adding a provider" previously said "plus a clause in the orchestrator's provider
     `case`", which is one of five. That undercount is the *"the one X" is an observation, not a
     census* class, in the doc that exists to prevent exactly this for provider four.
   - The **≥1-orphan section's opening**, "neither live account" → "no live account", now that
     there are three and t1 measured Linode's at 0 candidates / 0 skipped.

4. **`cloudcost_orchestrator.exs` header comment and the `### Linode` runbook Run-it recipe.**
   Both enumerate providers; §t2's Scope is "first-class selection everywhere it is currently
   enumerated", so both were updated rather than left one provider short.

---

## 4. Surprises

- **`env`'s last-wins for a duplicated assignment was verified, not assumed.** The Linode
  negative guard runs `env -u CLOUDCOST_LINODE_TOKEN "${CC_HERMETIC[@]}" CLOUDCOST_PROVIDER=linode …`,
  and `CC_HERMETIC` already carries its own `CLOUDCOST_PROVIDER="$CC_PROVIDER"`. Whether the
  trailing assignment wins is the difference between guarding Linode and guarding whatever
  `CC_PROVIDER` happened to be. Probed directly (GNU coreutils 8.32): the trailing assignment
  wins, the outer `-u` strips the token, and the prefix's own effects survive. Probe output is
  in the packet.

- **`fetch_linode.py`'s own `--period` help string is stale.** `:1291` says
  `"YYYY-MM (default: current UTC month)"`, but the real default is the newest **settled**
  invoice's covered month (`:1034`, `resolve_billing`); `current_period()` is only the
  billing-failed fallback (`:1343`). `fetch_linode.py` is outside §t2's Touches, so it was not
  edited — `tools.json`'s description states the true behaviour, and the string is filed in §6.

- **`~/.secrets/linode-cloudcost.env` already uses `export`**, so a bare `source` would in fact
  work for this particular file. The `set -a` requirement is documented anyway, exactly as §t2
  mandates: the rule protects the operator who writes the next credential file as bare
  `KEY=value`, and the failure mode when it bites is silent disagreement between parent and
  child, not an error.

---

## 5. Mutation record

Load-bearing checks were watched failing in the state they guard, then restored.

| # | Broken state constructed | Guard that fired |
|---|---|---|
| M1 | `EnvDep` missing `masked` in a real manifest | `a_manifest_missing_an_env_dep_field_is_rejected` (in-suite, permanent) |
| M2 | `$CLOUDCOST_OUT` holds **no** report | sprint report discovery → `fail "no cloudcost_report_*.html …"` |
| M3 | `$CLOUDCOST_OUT` holds **two** reports | sprint report discovery → `fail "expected exactly one …, found 2"` |
| M4 | one report named for a **non-current** month (the Linode shape) | discovery passes and derives `2026-07`; the superseded `date -u +%Y-%m` construction would have looked for `2026-08` |
| M5 | `CLOUDCOST_LINODE_TOKEN` unset, provider `linode` | orchestrator raise, exit 1 |
| M6 | `fetch_linode.py` undeclared in the manifest | `test_no_undeclared_scripts[cloudcost]` (observed red at `main` before the fix) |
| M7 | period empty (from M2 and M3) with the r0-F2 guard in place | one `[WARN]`, and `report_data_.json` is never constructed — the guard branches **both** ways across the three cases, so it is not vacuous |

M2–M4 and M7 were run against blocks **extracted verbatim from `sprint.sh` by line range**, so
the text exercised is the text that ships rather than a paraphrase of it. The harness is at
`scratchpad/mutate_report_discovery.sh`; its full output is in the packet.

---

## 6. Carried forward / open

- **The PAT's expiry date is not recorded.** §Prerequisites 1 requires it and this session did
  not hold it. The `### Linode` subsection states the gap as a required fill rather than
  carrying a placeholder that reads like a value. **This is the one open item.**

- **`m3-milestone.md`'s citations into `cloudcost/runbook.md` are now shifted** by this ticket's
  insert. `m3-milestone.md` is t3's Touches, not t2's, so they are not edited here. The map:

  | Cited as | Now |
  |---|---|
  | `runbook.md:15-63` (§Prerequisites, `m3-milestone.md:382`) | `:17-137` |
  | `runbook.md:51-61` (AWS `set -a`, `:419`) | `:53-63` |
  | `runbook.md:197-232` (BL-069 planting, `:452`) | `:283-346` |
  | `runbook.md:197` (`:486`) | `:283` |
  | `runbook.md:414-437` (Adding a provider, `:382`, `:452`) | `:538-580` |
  | `runbook.md:420-428` (measure-and-confirm, `:61`, `:433`) | `:553-566` |

  `cloudcost/scripts/fetch_linode.py:1386` carries the same `runbook.md:420-428` citation and is
  also outside Touches.

- **§Done-when 5 says BL-092 covers "three manifests"; the repo has six.** BL-092's own row
  (`docs/backlog-2026-06.md:3235`) and §t2's prompt both say *every* committed manifest, which is
  what landed — discovered by walk, so the figure cannot go stale again. The done-when figure is
  flagged, not edited.

- **`fetch_linode.py:1291`'s `--period` help string** (§4) — a one-line fix for whoever next
  opens that file.

- **BL-069 remains armed and red for Linode too.** `sprint.sh`'s ≥1-orphan assertion is left as
  a `fail`, named not re-triaged; t3 plants the zero-backend `common` NodeBalancer. The recipe
  and the reasoning for why it must be a NodeBalancer rather than a volume or a reserved address
  are now in the runbook.

- **Not run at t2, stated rather than implied:** the live Linode sprint case and the live
  orchestrator run. Both are §t3's done-check, both cost an LLM call and a live API read, and
  §t2's done-check does not include them. The sprint changes are covered by `bash -n`, the
  extracted-block mutation harness, and the `env` probe.

---

## 7. Round-0 disposition

Review at `docs/reviews/m3-cloudcost-t2-review.md`. Zero blocking findings; approved for merge.

| Finding | Disposition |
|---|---|
| **F1** — `main` red for a suite t1 never ran | **no change.** Correctly diagnosed as t1's gap, not t2's; the rule goes to the m3-close promotion set. Nothing in t2 to alter. |
| **F2** — empty `CLOUDCOST_PERIOD` cascades into `report_data_.json` | **fixed**, §7a. |
| **F3** — two stale strings in `fetch_linode.py` | **no change, already recorded.** Both are in §6 above, and the arbiter is folding them into the milestone's §Open items at rev 6 with the BL-078 trigger shape. `fetch_linode.py` is outside §t2's Touches and editing it to close a documentation nit would be the deviation, not the fix. |
| **F4** — the PAT expiry | **human-owned, unchanged.** The runbook states it as a required fill; it stays the one open item, now with a deadline (before t3's live run). |

### 7a. F2 — the guard, and the one thing it deliberately does not cover

The three period-dependent assertions (`report_data.providers`, the orphan count, and AWS's
`region_coverage` pair) now sit inside `if [[ -z "$CLOUDCOST_PERIOD" ]]; then warn … else …`,
and `CLOUDCOST_DATA` is assigned **inside** the `else` — so the misleading path is not merely
unused, it is never constructed. No `exit`: the block reports every failure rather than
stopping at the first, per the review.

**The D2 credential grep was deliberately moved *outside* the guard** rather than swept in with
its AWS siblings. It reads `run.json`, not the report, so it is meaningful on exactly the runs
where the report is missing — and a run that failed to produce a report is not a run where you
want the credential check silently skipped. This required splitting the single
`if [[ "$CC_PROVIDER" == "aws" ]]` block into two; that split is the whole of the change's blast
radius, and it is the reason the AWS leg loses nothing.

Mutation M7 pins it, and pins that the guard is not vacuous: across the three constructed
states the same guard text branches **both** ways — `RUN` on the working case, `WARN` on both
broken ones. A guard that always skipped, or never did, would show only one of those lines.
