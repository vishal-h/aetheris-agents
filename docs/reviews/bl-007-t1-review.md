# Review — bl-007 t1 — round 1

## Findings

1. [question — gates the contract commit] How does verify dispatch tools that
   don't run in the worker? The table establishes verify re-executes ALL recorded
   tools (`verifier.ex:130-136`) and the packet's dispatch citation
   (`main.rs:375-400`) covers the worker path — but `spawn_agent`,
   `send_message`, `ask_human`, `wait_for_event`, `wait_for_all` are harness-side,
   not worker-side. The committed §5 claims the in-process/inter-agent tools "have
   no effects the sandbox fails to contain," yet the sandbox is a worker
   filesystem sandbox that these tools never pass through. If verify re-executes
   `spawn_agent`, it starts a live sub-agent run — real model calls, real cost —
   an uncontained effect worse than `http_call`; if it re-executes `ask_human` or
   `wait_for_*`, verify can block indefinitely (liveness). Answer with file:line:
   (a) does the verify path re-dispatch harness-side tools at all, or serve/skip
   them? (b) if re-dispatched, what does each of the five do under verify? If any
   answer is adverse, §5's safe-set sentence and effect-class map get a
   human-approved edit before the commit — the current wording would be wrong in
   the dangerous direction again.

2. [non-blocking] Boundary-ownership discrepancy + orphaned backlog entries. The
   notes assign the D6 export boundary (manifest regen, backlog filing) to t2;
   the milestone doc as drafted placed it in t5. Reconcile — quote the README's
   t2 text if it genuinely moved, else correct the notes. Either way: the two
   NEW backlog entries this ticket generated (effect-class mechanism /
   record-and-serve under verify; first-diverging-event report gap) appear in no
   ticket's written scope — t5's text predates them and lists only D4's entry. A
   strict-Touches executor will not file what its ticket doesn't name. One README
   edit adding both to the owning ticket's scope, next correction moment.

3. [non-blocking] Gate consistency. t0 ran `mix credo --strict` + `mix dialyzer`
   as boundary gates for touched Elixir; t1 touched Elixir (docstrings) and ran
   neither. Run them (trivial for docstrings) or record a docstring-only
   exemption in a file — either is fine; unstated inconsistency is not.

4. [non-blocking] §5's MCP parenthetical ("likewise uncontained; out of scope
   here") floats free of the operational guidance. Fold it into the safe-list
   sentence — "safe to run only on trajectories whose tools are the filesystem /
   local-git / in-process built-ins; not `http_call`, not MCP tools" — so the
   normative statement and the operational rule cannot drift apart. (Wording
   pending finding 1's answer for the in-process clause.)

## Cross-ticket notes

- Learning-promotion candidate (strong): *normative claims about code require a
  read-verification table in the authoring ticket's packet; unverifiable claims
  get tagged at draft time and resolved before commit.* Source: t1 — the
  mechanism's first use caught three divergences in a safety-relevant direction.
- Finding 1 is the same defect class the table caught: a containment claim made
  about a path nobody read. The effect-class map row for in-process tools cites
  no line for its "contained" verdict — the tell was the missing citation.
- Optional t2 rider for human ratification: rename `find_last_step_complete` →
  exact-match-honest name. t2 already touches `fork.ex` code; natural home, one
  line in t2's ticket text if wanted.

## Round 2 — resolution (t1 closed)

- **Finding 1 — fixed.** Verify is worker-only (`verifier.ex:46,136`); no
  harness-side dispatch, so the feared adverse branch (live sub-agent spawn,
  indefinite block) is disproven from source. But §5's "contained" claim still
  fell — in a new direction: three paired in-process tools (`wait_for_event`,
  `read_blackboard`, `write_blackboard`) crash verify with `KeyError`
  (`verifier.ex:133` assumes the worker `"output"` payload key; in-process results
  use `"result"`, `loop.ex:421-497`), five are silently skipped, and `echo` is the
  benign exception (worker-dispatched, effect-free, yields a spurious per-step
  error). §5 rewritten under human approval; `echo` classified; the harness
  `KeyError` bug surfaced and tracked (below).
- **Finding 2 — fixed.** t5 owns the D6 export boundary (not t2); notes corrected;
  four backlog items named in t5's README scope with citations (D4 deferral;
  verify effect-class/record-and-serve; first-diverging-event report gap; verify
  `KeyError` crash). Standalone-ticket-vs-trigger-parked recorded as the human's
  call at t5.
- **Finding 3 — fixed.** Full Elixir gate set run at the boundary: `mix credo
  --strict` (no issues) + `mix dialyzer` (0 errors), alongside `mix test` (865/0),
  `mix hex.audit`, `mix format`, and `drift_check.py` (8 PASS / 0 FAIL / 0 WARN).
- **Finding 4 — fixed.** MCP guidance folded into §5's closing safe-set sentence.

**Zero blocking findings remain.** Contract commit authorized (§8 approval via this
review cycle). Push held for the human.
