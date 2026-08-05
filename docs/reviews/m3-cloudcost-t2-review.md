# Review — m3-cloudcost t2 — round 0

Reviewed at `aetheris-agents m3-t2-wiring@f28b817` and `aetheris m3-t2-wiring@325a967`.
**Zero blocking findings. Approved for merge.**

The report-discovery rewrite, the separate Linode poison block, the BL-092 walk with its own
negative control, and the `env` last-wins probe are all stronger than the ticket asked for.
Three of the four unmandated runbook edits are the kind that should not need asking — a
mandated edit that leaves its own file self-contradictory is not finished.

## Findings

1. **[non-blocking, and it is about t1 rather than t2] `main` was red for a suite t1 never
   ran.** Two tests in `tests/test_tools_manifests.py` were failing at `main` before this
   ticket, because t1 added the seventh cloudcost CLI and declaring it is t2's job. t1's
   off-territory gate ran `cloudcost/tests/` and the harness suite; the repo-root `tests/`
   suite — which asserts *about* cloudcost from outside its directory — was in neither t1's
   done-check nor my review of it. So the merge at `cb3ca63` left `main` red for a day, and
   nothing would have caught it before t2 happened to run that suite. Nothing to fix here;
   the generalisable rule goes to the m3-close promotion set: **adding or removing a script
   in a use case changes assertions in a suite that does not live in that use case's
   directory**, so the manifest suite belongs in the done-check of any ticket that changes
   the script inventory, not only of the ticket that edits the manifest.

2. **[non-blocking] An empty `CLOUDCOST_PERIOD` cascades into a misleading filename.** On the
   zero-report and two-report paths the `fail` prints and returns (BL-077), `CLOUDCOST_PERIOD`
   stays `""`, and the next line builds `report_data_.json` — which your own mutation output
   shows. The dependent assertions then fail against a path that reads like a script defect
   rather than a missing report. Don't add `exit 1` — the assertion block deliberately reports
   every failure rather than stopping at the first. Guard the dependent assertions on
   `[[ -n "$CLOUDCOST_PERIOD" ]]` and emit one explicit line saying they were skipped because
   the period could not be determined.

3. **[non-blocking] Two stale strings in `fetch_linode.py`, both outside Touches.** The
   `--period` help at `:1291` describes a default the adapter no longer has, and `:1386`
   carries a `runbook.md:420-428` citation this ticket shifted. Neither is worth its own
   backlog row; both are being recorded in the milestone's §Open items with the BL-078 trigger
   shape — do them the next time someone is legitimately in that file.

4. **[question, human-owned] The PAT expiry is still unrecorded.** Stating the gap as a
   required fill rather than a placeholder is exactly right. It should be filled before t3's
   live run, since t3 is the last point in this milestone where anyone is looking at the
   credential.

## Doc defects this ticket found in the milestone — being corrected at rev 6

Three of your carried-forward items are my defects, not yours, and are named here so the
review record shows they were found rather than tolerated: §Done-when 5's "three manifests"
(the row and your implementation both say *every* committed manifest, which is the correct
reading), §t2's offer of "or from STEP 1's reported period" as an alternative to globbing —
unsound, because that period reaches the sprint only through model prose, and your rejection
of it is the right call — and the six runbook citations this ticket shifted.

## Cross-ticket notes

- **"The wiring is five places, and they are enumerated here because m3 t2 found them one at a
  time."** That runbook paragraph is the single most valuable artifact this ticket produced,
  and it is the enumerate-the-class rule applied prospectively for the first time in this
  milestone rather than retrospectively. Provider four reads that instead of rediscovering it.
- The `LINODE_CLI_API_*` non-strip is the round's sharpest judgement: stripping a hazard in the
  one context that would have reported it is how a proof gets quieter while looking stronger.
