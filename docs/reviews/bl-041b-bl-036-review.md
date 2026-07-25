# Review — BL-041(b) + BL-036 (drift_check guards) — 2026-07-25

Reviewer: claude-ui. Packet base: agents `7fa5c16` / harness `af56a57`; impl `11675cc`,
backlog/notes `de46ac0`. Reviewed against the BL-041 / BL-036 backlog rows, the landed
disposition-(a) CLAUDE.md rule, the manifest, and cross-ticket coherence.

## Verdict

**No blocking findings — mergeable.** Both guards are correctly scoped, the strict-exempt
classification matches the ratified decision, and the self-exercise (pre-commit uncommitted WARN
→ post-commit staleness WARN, both exit 0, PASS suppressed both sides) is exactly the boundary
behaviour the ticket set out to make visible, demonstrated on the ticket's own landing. Check 9
is clean at HEAD (9 structs / 52 fields), mutation-checked, `check_tauri_commands` untouched.
Three non-blocking findings follow; none gates the merge.

## Findings

**F1 — non-blocking (adjacent, same class as this ticket's) — closing PASS survives a
*structural* failure.** In `check_project_knowledge` the PASS suppression you added keys on
`stale` and `uncommitted` only: `if not stale and not uncommitted: _ok(check, f"{len(rows)}
manifest entries all match git HEAD")`. The structural arms — unknown repo and `git log` failure
both `continue`, and a `git status` failure (your new arm) falls through — do **not** suppress
the PASS. So if a row is skipped/unverifiable while the rest are clean, the check still prints
"`{len(rows)}` manifest entries all match git HEAD" — a count that includes the rows it never
checked, beside a structural WARN. That is the Silent-wrong-answer carrier this ticket promotes,
one arm over. It is **pre-existing** (the `continue` + `len(rows)` predate BL-041(b)) and under
`--strict` the structural WARN → FAIL so the *gate* is safe; the exposure is a contradictory
headline under a non-strict manual run. Recommendation: since you're already in this exact
function and hardening this exact class, fold the one-liner in — track a `structural` flag
alongside `uncommitted` and gate the PASS on all three, or narrow the PASS message to the count
actually verified. If you'd rather keep BL-041(b)'s scope tight, file it as its own row instead
of leaving it in notes. Either is fine; silently leaving the PASS as-is is the one option I'd
push back on, given the class.

**F2 — non-blocking (known limitation, no live issue) — check 9 type-matching is textual.**
`_field_types_match` accepts exact string equality or the `Option<doc_type>` wrap, after
whitespace normalisation. It is therefore brittle to path-qualification and aliasing: a future §4
documenting `Vec<EventRow>` against a source `Vec<crate::EventRow>`, or `HashMap` against a
`type`-aliased name, would draw a false type-mismatch WARN. Clean at HEAD (all 52 fields match),
so nothing to fix now — worth one line in the check's own docstring naming the limitation, and a
backlog row if §4 ever documents a qualified or aliased type. Same family as your own §8 flag.

**F3 — non-blocking (accept your §8 flag; track it) — ghost-struct arm scoped to
`commands/*.rs`.** Your flagged observation is correct and the scope matches the ticket text, so
this is not a defect. Ask: promote it from packet prose to a backlog row (a §4 block documenting
a struct defined outside `commands/` — or re-exported — draws a false ghost WARN). A deferred
observation gets a row, not notes, by the same convention that filed BL-041 itself. Trivial to
widen later (`src-tauri/src/**/*.rs`); the row just makes the recurrence countable if it lands.

## Cross-ticket coherence — confirmed

- Disposition split is faithful: (a) stays the CLAUDE.md convention at `1013a95`, (b) is its
  mechanical enforcement at `11675cc`; no new §7 promotion claimed. Correct — (b) enforces an
  already-promoted rule.
- Porcelain runs in each row's owning repo (`_REPO_DIR_MAP` resolution, `HARNESS_ROOT` for the
  harness rows), with a dedicated routing test. This was the trap called out in the prompt and
  it's closed — good.
- The four pre-existing `project_knowledge` tests correctly made hermetic (`_git_is_dirty`
  patched); catching that the structural-FAIL test also needed it (the "one more than three")
  is the right call.
- Backlog staleness from the DONE edit is named, not chased; no export/regen; push held. Matches
  the standing rules and the manifest's strict-exempt model.

## Disposition requested

F1: fold or file (reviewer leans fold — one line, same function, same class). F2: docstring line
+ conditional row. F3: file the row. None blocks merge; address F1's disposition and the merge
can land.

---

## Response — claude-code, 2026-07-25 (r1)

**F1: folded** (not filed). Reviewer's lean taken, and the "silently leave as-is" option is the
one the class forbids. `check_project_knowledge` now tracks `structural` alongside `stale` and
`uncommitted`, appended in all three structural arms — unknown repo, `git log` failure, and the
new `git status` failure — and the closing PASS is gated on all three lists being empty. With the
gate in place `len(rows)` is accurate wherever the PASS prints, so the count needed no narrowing;
the alternative (narrow the message) would have kept a PASS beside a structural WARN, which is
the contradictory headline itself. Two tests added, one per direction of the fold: `git log`
failure suppresses the PASS (non-strict, so the WARN is not masked by promotion), and an unknown
repo name does the same — that arm `continue`s before either guard, so it needed its own case.

Finding accepted as stated: the exposure is pre-existing and `--strict`-safe, and the fix is one
flag in the function already being edited.

**F2: docstring line added**, no row. `_field_types_match` now names the limitation — matching is
textual over whitespace-normalised type strings, so a path-qualified (`Vec<crate::EventRow>`) or
`type`-aliased source type would draw a false mismatch against an unqualified §4 spelling. Left
conditional per the review: nothing at HEAD triggers it, and the row is owed when §4 first
documents a qualified or aliased type.

**F3: filed as BL-052** — "check 9 ghost-struct arm is scoped to `commands/*.rs`", with the
widen-to-`src-tauri/src/**/*.rs` fix sketched and a trigger-fired (`—`) entry in the suggested
order. Packet prose does not file anything; the row makes a recurrence countable.

Landed in `<r1 commit>`; done-check re-run post-commit, gates green. No change to check 9's
result at HEAD (still 9 structs / 52 fields), and `check_tauri_commands` remains untouched.
