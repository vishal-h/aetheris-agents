# Review — m3-cloudcost t1 — round 0

Reviewed at branch `m3-t1-fetch-linode`, commit `b644f48`, against `cloudcost/m3-milestone.md`
rev 3 (§t1 is byte-unchanged in rev 4; the rev-3 citation is correct, not stale).

## Findings

1. **[blocking] `period` carries a different meaning than it does on DO, and the divergence is
   in a first-class contract field.** §Decisions records `period` = invoice **issue** month, so
   a snapshot labelled `2026-08` contains July's charges. m1's §Normalized uses `period` as the
   **covered** period (its own example pairs `"period": "2026-07"` with a July fetch), and DO's
   live preview invoice makes covered ≡ current. Two providers assigning different semantics to
   the same first-class field is a silent-wrong-answer: the MoM history tree stays internally
   consistent because it is per-provider and consistently offset, so nothing errors — the report
   simply states a month it is not about. Suggested fix: `period` is the **covered** period on
   every provider; emit `linode_costs_2026-07.json` for the July invoice, and keep
   `provider_extra.invoice.issued` for the issue date. **The `$(date -u +%Y-%m)` filename
   expression in §t1's own done-check is the defect that pushed this the other way — it presumes
   covered ≡ current, which is true on DO and AWS and false on Linode. That is a doc defect, not
   an implementation one, and it is being corrected.** State in the notes that a Linode cost
   snapshot is structurally one month behind, because no preview invoice exists; the current
   month survives only as `balance_uninvoiced`, which the balance block already carries.

2. **[blocking] The adapter's correctness now rests on three fields the OpenAPI spec does not
   declare, and the failure mode of losing them is silence.** `reserved`, `assigned_entity` and
   `tags` on an IP object are undocumented live behaviour. The finding itself is excellent — and
   §D-L9's rule *is* reachable because of it — but an undeclared field is not contractual, and if
   `reserved` stops being returned, `is_reservable_address` presumably evaluates false for every
   address and the static-IP class silently reports zero. That is exactly the shape §D-L6 forbids:
   an empty list indistinguishable from a class nobody could assess. Suggested fix: branch on
   **presence**, not truthiness. If no address in the response carries a `reserved` key, the class
   is `not_inventoried` with the reason "reservability not determinable — field absent from the
   live response", never an empty emission. Same treatment for `assigned_entity`: if it is absent
   while `linode_id` is null, attachment is undetermined, not unattached — a false orphan is the
   costlier error. Assert both in the suite with a fixture whose objects lack the fields.

3. **[blocking, answer before the next round] Name the exact JSON location of `surveyed`,
   `not_inventoried`, `exclusions`, `warnings` and `duration_ms`.** The packet shows them under
   "Full summary from the same run", which reads like the CLI summary — in which case §D-L6's
   not-inventoried marker never reaches the report and is lost the moment the process exits. If
   instead any of them is a **top-level key on either emitted document**, it is an unratified
   §Normalized extension: the m1 cost schema sanctions `provider_extra` and the m1 **inventory
   schema has no extras key at all**, so there is no contract-sanctioned home for them on the
   inventory side. Both readings need a decision rather than an inference, so state the location
   per key. If any sits at top level on a normalized document, either relocate it under a
   sanctioned key or ratify the extension doc-first per §D-C — and note that ratifying one is
   still compatible with the milestone's negative proof, which constrains the four shared
   *scripts*, not the schema.

4. **[non-blocking] Reconciliation is asserted in the suite; assert it at runtime too.** `money`
   was imported from `_normalized` rather than duplicated — defensible, and better than a third
   copy — but that version coerces an uncoercible value to `0.0` rather than raising as
   `fetch_do`'s does, and Linode's `unit_price` is a **string** in the schema. A malformed amount
   therefore under-reports silently. Since Σ`line_items` == `totals.amount` is already known to
   hold, make it a runtime check that appends a `warnings[]` entry on mismatch, not only a test
   over fixtures. Record the `money` divergence from both predecessors in the notes as the
   deliberate choice it is.

5. **[non-blocking] `surveyed` covers IPs only; it should cover every class the adapter filters.**
   Public distribution images are excluded by `test_public_distribution_images_are_not_inventoried`,
   correctly — but the exclusion is invisible in the output, so a reader cannot tell "no private
   images" from "images not examined". Milestone done-when 8 asks for every exclusion recorded with
   its reason. Add a `surveyed` entry per filtered class with its counts (read / retained /
   emitted), in the same shape as the `networking_ips` entry.

6. **[non-blocking, and the cheapest de-risking available before t3] The suite proves the shared
   engine *parses* Linode output; add a positive control proving it *fires*.** `0 candidates, 0
   skipped` over the live inventory is a genuine anti-vacuity result for parsing, and
   `test_the_normalized_inventory_is_readable_by_the_shared_rule_engine` establishes readability —
   but nothing yet shows an unchanged `detect_orphans.py` producing a candidate from Linode-shaped
   input. The fixtures for it already exist (`linode_volumes_orphan.json`,
   `linode_nodebalancers_idle.json`). One test running the unchanged engine over a crafted Linode
   inventory and asserting ≥1 candidate with its evidence proves the milestone's bet mechanically,
   offline, without waiting on the account plant.

7. **[non-blocking, carries into t3] The BL-069 plant must be a `common` NodeBalancer.** `premium`
   is deliberately unmapped and prices at `0.0` plus a warning, so a premium plant would satisfy
   the ≥1-orphan assertion with a $0.00 saving — a candidate with no dollar figure is a weak
   proof of a cost report. Fold into t3's planting step.

## Cross-ticket notes

- **The spec is a hypothesis; the live read is the evidence.** Finding 2's three undeclared fields
  mean every spec-derived conclusion in `m3-linode-scout.md` is provisional until a live response
  confirms it — including the ones this milestone's design decisions rest on. The scout was right
  to pin an ETag; the missing half is that a pinned spec can be *incomplete*, not merely stale.
  Promotion candidate at m3 close.
- **Anchor-window edits to shared test fixtures.** The dropped `return aws_stub` was caught only
  by running the whole suite off-territory, and it silently failed 43 unrelated tests. The rule
  that catches it is already the repo's (`off-territory runs at every ticket boundary`); the
  addition worth promoting is that an edit anchored on a window ending inside a function body is
  the specific mechanism, and `git diff --stat` against `main` is the two-second check.
- Self-reported defects, the mutation record with M10 replayed after narrowing, and the
  §Prerequisites closure record are all exemplary and want no change.
