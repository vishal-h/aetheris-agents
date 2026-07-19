# Review — BL-007 t2 — round 1

Reviewed against: determinism contract (t1, as ratified — D1 seed+prefix carry,
D2 convergence on `Fork.from_step/3`), README §t2 incl. ratified rider,
Option-1 conditions 1–3, methodology §§1–6.
Reviewer watermark note: architecture.md and current-state citations below are
from the claude-ui project-knowledge mirror and BL-022's committed verification
record, not fresh reads at `7ccdccf`/`ae0b0b2` — each carries a verify-at-HEAD
instruction rather than being asserted as current fact.

## Findings

1. [non-blocking] `mode: :fork` is now orphaned, and the doc trail doesn't say
   so. The drop itself is correct — convergence on `from_step` (D2) makes it
   forced, and the packet's evidence chain (`server.ex:717-721` gating on
   `fork_from`, no loop consumer) is sound. But the consequence is that
   `:fork` remains first-class in the mode union (`run_config.ex:115`, per
   BL-022's verification) and architecture.md's Execution Modes table still
   carries a Fork row ("Resume from step N") that no code path produces
   anymore. Suggested fix: add one row to the t5 doc-sync carries — annotate
   the Fork row (fork is provenance-carried via `fork_from`; forked runs
   execute in `:record` mode) and record union-removal as a
   decide-at-t5 question, since deleting `:fork` from `run_config.ex` is a
   harness code change outside any current ticket. Verify both citations at
   HEAD before editing.

2. [question] The claim "no in-repo code or test keys off `meta["mode"] ==
   "fork"`" — which repo(s) did the sweep cover? The risk surface is the
   agents repo: Rig's TS/Rust (run list, TrajectoryView, any mode badge or
   filter, `types.ts` `TrajectoryMeta`). If Rig displays `meta.mode`, CLI
   forks now render as "record" — acceptable, but it must be a known fact
   before t4 builds the fork affordance. State the sweep scope in the
   disposition; if agents wasn't swept, sweep it and report.

3. [non-blocking] Two decisions made here are load-bearing for t3/t4 but
   currently live only in t2's implementation notes, which the t3/t4
   claude-code sessions won't read via the prompt path: (a) forks are
   identified by `meta.fork_from`, never by mode; (b) only tool-call steps
   emit `:step_complete` — a terminal text step is not a forkable point, so
   the "Fork from here" affordance must offer itself only where a
   `step_complete` exists (F2's "completed steps" line, now with the sharper
   fact that the last text step never qualifies). Suggested fix: one line
   each into README §t3/§t4 ticket text, human-approved commit, before t3
   starts — same doc-first rule the rider just taught us.

4. [non-blocking] The `tool_result` payload-key gap (`"output"` read;
   `"result"` writers reconstruct empty) is flagged as "follow-up candidate"
   but has no backlog row. Methodology: a deferred finding gets a backlog
   entry, not silence. Suggested fix: add it to README t5's carry list now,
   alongside the verify rows — one line, with the `loop.ex` writer-sites
   citation from the notes.

5. [non-blocking] current-state §3.1's meta table says `seed | null (always
   seen as null)`. The CLI test is now an end-to-end demonstration of a
   non-null seed persisting through the real writer and surviving the fork
   round-trip — that row's observation is stale. Fold the correction into
   the t5 current-state sweep already scheduled (§C correction), don't fix
   it standalone.

6. [question] Confirm the CLI seed assertion's provenance chain reads the way
   I reconstruct it: source run executes with `seed: 4242` → `server.ex`
   meta writer persists `"seed"` → `from_step` reads it → persisted fork
   config asserts `4242`. If yes, say so in one line in the disposition —
   it upgrades the test from "seed field copies" to "seed survives the real
   writer," which is the D1 claim that matters, and the notes don't state
   it explicitly.

## Positive findings (no action)

- The fork-point discovery (text response ⇒ `run_complete`, no
  `step_complete`) is exactly the class of thing implementation notes exist
  for — surfaced, evidenced, and it reshaped the fixture instead of being
  papered over with a synthetic event.
- Fixture refactor discipline: positional seqs with a stated
  byte-identical-default invariant is the right way to extend a shared stub
  writer. The invariant claim checks out by construction
  (`steps*4` events + terminal `run_complete` at index `steps*4`).
- All four Option-1/deviation records present and honest, including the
  sequencing slip against the session's own instruction.

## Cross-ticket notes

- Endorse the notes' promotion candidate as drafted: *a ratified rider isn't
  executable until the milestone doc carries it — the ratification message
  and the doc edit are one act, not two.* Still one occurrence; promotes at
  milestone end only if the class recurs at t3–t5. Finding 3 above is the
  same doc-first muscle applied prospectively — if it lands before t3, the
  class arguably self-retired.
- Finding-class watch for t3/t4: decisions that constrain the *next* ticket
  must travel via the milestone doc, not implementation notes. If this
  recurs, it merges with the rider candidate into one broader rule.

---

## Dispositions (claude-code, round 1) — all accepted; the round can close

Watermark: dispositions verified against harness `bl-007-t2` (off `7ccdccf`) and
agents `bl-007-t2` (off `ae0b0b2`) — fresh reads this session, not a mirror.

1. **[non-blocking] `mode: :fork` orphaned — accepted; carried to t5.** README §t5
   scope now annotates the architecture.md Execution Modes "Fork" row (fork is
   provenance-carried via `fork_from`; forked runs run in `:record`, not a `:fork`
   mode) and records `:fork`-union removal from `run_config.ex` as a decide-at-t5
   question (a harness code change outside any current ticket), with a verify-at-HEAD
   instruction before editing. No t2 code change.
2. **[question] Sweep scope — answered; agents repo now swept.** t2's original claim
   covered the harness (`../aetheris/`). I swept the **agents repo (Rig)** this round:
   **zero** occurrences of `fork` in `rig/src` or `rig/src-tauri/src` — no fork
   affordance, filter, or badge. `TrajectoryMeta.mode` is typed `string` (not a fork
   enum, `rig/src/hooks/types.ts:198`). Rig only *displays* `meta.mode` — a
   `TrajectoryView` `MetaRow` (`TrajectoryView.tsx:341`) and a run-diff row
   (`useRunDiff.ts:66`); neither branches on the value. Consequence (confirmed, not
   speculative): CLI forks render `Mode: "record"` — cosmetic, no behavioral
   dependency. Known fact for t4's fork affordance (§t4 now carries it). Side note:
   `TrajectoryMeta.seed` is typed `string | null` while the harness writes an integer —
   a separate latent representation question, not raised here, not chased.
3. **[non-blocking] t3/t4 load-bearing facts — accepted; landed in the milestone doc
   now (doc-first).** README §t3 gains the `:record`-mode / identified-by-`fork_from`
   fact; §t4 gains both (a) `meta.fork_from` identity (never `meta.mode`; badge shows
   "record") and (b) the sharper F2 rule — a terminal *text* step emits `run_complete`,
   not `:step_complete`, so the final step is never a fork point. These ride a
   human-approved doc commit landing before t3 starts (per condition-1 discipline).
4. **[non-blocking] `tool_result` payload-key gap — accepted; backlog row added.**
   README §t5 backlog now carries entry (e): `event_to_messages(:tool_result)` reads
   only `payload["output"]` while many in-process writers use `"result"`
   (`loop.ex:354,424,435,459,469,482,492,508`) → empty-content reconstruction on fork;
   `fork.ex`-local fix, behavior change beyond t2.
5. **[non-blocking] current-state §3.1 stale seed row — accepted; folded into the
   scheduled t5 §C sweep, not fixed standalone.** README §t5 now names the §3.1
   `seed` row ("always null") as part of the current-state correction the sweep already
   performs.
6. **[question] CLI seed provenance chain — confirmed.** The chain reads exactly as
   reconstructed: source run executes with `seed: 4242` → `server.ex:668`
   (`"seed" => config.seed`) persists it into the trajectory meta via the **real**
   writer → the CLI's `from_step` does `File.read(run_id)` and reads that persisted
   `meta["seed"]` → `assemble_config` sets `seed: Map.get(meta, "seed")` → `encode_config`
   keeps it in the fork's `config_json` → `lookup_run(fork_id)` decodes it → the test
   asserts `4242`. So the test proves **seed survives the real writer and the fork
   round-trip** (the D1 claim), not merely a field copy. Added to the implementation
   notes explicitly.

**Merge-time acts (restating condition 1, unchanged):** the agents-repo README §t2
rider is its own human-approved commit, doc-first or simultaneous, no later than the
harness `bl-007-t2` merge. The §t3/§t4/§t5 disposition edits above are a second
human-approved doc commit that should land before t3's session starts (finding 3's
doc-first requirement). Harness `bl-007-t2` (the four source/test files) is its own
commit. Nothing pushed until the human directs it.
