# Review — BL-193 — round 2

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bl193r1packet.md` · Commit: `c171034` on `2b2f0f4`

**Verdict:** findings 10 and 11 closed. One new finding: the Drive read the round performed can settle (i) versus (ii), which the row still calls unsettled — it stopped one folder short. Non-blocking; the row is correct as it stands and would be stronger.

---

## Findings

### 12. [non-blocking] The Drive record can settle (i) versus (ii) — the round read one folder of eighteen

§8 item 1 states what would now settle the two histories: *"evidence about whether the process was alive at `run_start + 300 s` — `02:47:52.469Z` — where the Drive objects stop at `02:43:15`."*

The Drive objects stop at `02:43:15` **in `BTL_01`**. That is one employee folder. There are eighteen, and the ones processed later carry later timestamps.

`collect_upload_files` sorts by `(employee_id, path.name)` and `main()` groups over that order, so upload proceeds through employees alphabetically — `BTL_01`, `BTL_010`, `BTL_014`, … `BTL_Consult_01`. `BTL_01` is first. Its six objects are the first six of the run, which is why they cluster at the start and say nothing about the cap.

**The round's own numbers make this a sharp, falsifiable prediction.** The six inter-object gaps in `BTL_01`:

```
02:42:59.432 → 02:43:02.744   3.312 s
02:43:02.744 → 02:43:05.866   3.122 s
02:43:05.866 → 02:43:09.137   3.271 s
02:43:09.137 → 02:43:12.324   3.187 s
02:43:12.324 → 02:43:15.359   3.035 s
                        mean   3.185 s
```

Steady, low-variance, and consistent with the per-object cost of a `files.list` probe plus a create — the two round trips `upload_file` makes. At 3.185 s across the round's own measured population of 108 objects (36 each for `2026-05`, `2026-07`, `2026-08`), a complete run needs **≈344 s of upload after the first write at `02:42:59.432`**, finishing near `02:48:43`.

The cap fires at ≈ `02:47:52`, which is ≈293 s after the first write. So if the cap is what ended this run:

- **≈92 of 108 objects** exist under `2026-08/` with `createdTime` on 2026-09-07,
- the **latest is ≈`02:47:5x`**, immediately before the cap,
- and **≈16 are missing**, concentrated in the last two or three employee folders alphabetically.

If instead the process died on its own before the cap, the objects stop earlier and short of that count. **The two histories predict different, countable Drive states**, and both are readable with the query the round already wrote — widened from one folder to the eighteen under `2026-08/`.

This also bears on BUG-001, which carries 108 → 36 as measured and the causal claim as hypothesis. A last object at ≈`02:47:5x` is the first direct evidence that upload volume, not something else, is what ran the step into a wall.

**Suggested fix:** re-run the Files API listing over every employee folder under `2026-08/`, reporting the object count and the maximum `createdTime`. Then either settle (i)/(ii) in the row, or — if the numbers do not fit either shape — record what they do show. Do not force them: a third possibility is that the rate is not constant across employees, and the mean above is derived from one folder.

Same scrub as before: counts and timestamps carry the evidence, file names do not need to appear.

---

## Findings 10 and 11 — closed

**10.** The row now asserts no death time, the superseded wording is preserved in a dated block anchored by lead-in text rather than by position, and the outside record is cited at second granularity with both caveats intact — including the one that matters most, that the run-table query rules out another *run* but not another *writer*, since BL-191's own evidence records a direct script invocation that creates no run row. Resting the binding on latency (5.2 s from `tool_called` to first object, which is what authenticate-then-upload costs) rather than on the query is the right load-bearing choice.

**11.** Hop 2 marked confirmed with the derivation kept beside the observation, the citation's nature recorded — the card is not an artifact either repo holds — and the Done-when clause folded into the existing sentence rather than appended.

---

## Commended

**The negative control in §7 deviation 1 is the packet's most useful paragraph.** A first Drive query returned zero folders named `2026-08`; a positive control returned 50 objects and 7 folders, showing the search worked and the query was wrong. That zero, published as a finding, would have been indistinguishable from "the folder does not exist" — and the entire round rests on that folder existing. Reporting the near-miss rather than only the corrected result is what makes the rest of the section credible.

**Deviation 2 catches two things the review did not ask for.** A cross-reference written as *"two paragraphs above"* — a positional citation that silently repoints on any insert, and which was already wrong when written — replaced with lead-in text. And a quotation that had acquired a comma the source does not have, corrected and then verified **by occurrence count** rather than by eye: 2 for source-plus-quotation, and 1 would have meant divergence. Checking a verbatim claim with a mechanism instead of a re-read is the discipline the whole packet convention is for.

**Reading the API rather than taking the fallback.** The ticket permitted deferring to the fixing ticket if credentials were absent. They were present, the read was taken read-only under `drive.readonly` with `files().list` and no write, the conditional was checked rather than assumed, and the deviation records that a live external read happened. The row now cites seconds where it would have cited an API call name.

**An observation worth drawing out of §8 item 2, which the round left flat.** The object counts across the three period folders are `2026-05` → 2, `2026-07` → 4, `2026-08` → 6. That is BUG-001's blast radius growing by one month per run, measured on a clock this repo does not own, with no reference to `payslip/output/` at all. It is independent corroboration of the defect's mechanism from outside the system that produced it — worth a sentence in BUG-001, and stronger evidence than the local `find` count that has been carrying that claim.

---

## Dispositions requested

| # | Expected |
|---|---|
| 12 | fixed, or `deferred (backlog ref)` if the wider read is out of scope for this round |

If deferred, the row should say what the query is and what each outcome would mean, so the next reader does not re-derive it.

## Owed

Unchanged. `(i)` versus `(ii)` remains open unless finding 12 closes it; BUG-001's September verification is unaffected either way.
