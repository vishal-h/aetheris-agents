# Review — BL-025: Verify effect classes + record-and-serve

**Ticket:** BL-025 — Verify: effect classes + record-and-serve for uncontained tools
**Cycle:** 2026-07-22 → 2026-07-23 · cross-repo (harness `../aetheris/` + `aetheris-agents/`)
**Branch:** `bl-025-verify-effect-classes` (both repos)
**Reviewer:** human (direct; no claude-ui findings file this cycle)
**Outcome:** signed off, mergeable

**What this file is.** By convention `docs/reviews/bl-0XX-review.md` holds the reviewer's
findings (BL-028 r1 finding 3 makes the ownership explicit). This cycle the review arrived
as direct human messages rather than a claude-ui findings file, and the packet existed only
in a scratch directory. Both halves of the record were therefore un-recoverable from the
repo. This file carries both, in the order they happened: the review rounds verbatim (§A),
the dispositions (§B), and the final packet with its evidence (§C). Nothing here is
reconstructed from memory — §C is the generated packet artifact, and §A is quoted verbatim.

---

## §A. Review rounds (verbatim)

The first two rounds arrived as ticket scope corrections *before* implementation; the third
reviewed the packet; the fourth signed off. All four are review acts and all four are
recorded here, because each changed the work and none was otherwise durable.

### A.1 — Round 1 (scope correction rev 2, human, 2026-07-22)

> # BL-025 — scope correction (rev 2): the CLI reaches a different "verify"
>
> **Decision (human, 2026-07-22): Option 1 — rewire the CLI to the `Verifier`.** Fold this
> into the BL-025 prompt; it supersedes §B/§E's assumption that `aetheris verify` reaches
> `Verifier`.
>
> ## Discovery (executing session, re-verify-at-HEAD pass)
> `aetheris verify` never reaches `Verifier`. `Commands.Verify.run/2` (`verify.ex:44-57`)
> starts a **new live run** with `mode: :verify` and returns `%{verified: true}`
> **unconditionally** (`:35`). `mode: :verify` only skips context-trimming
> (`loop.ex:409-411`) and pre-tools (`pre_tools.ex:59`) — otherwise a full live LLM + live
> tool run, `http_call` included. `Verifier.verify/2` is reachable only via
> `Aetheris.verify/2` (`aetheris.ex:98-100`) and tests. Rig invokes verify nowhere.
>
> Consequence: the ticket as drafted (Verifier-only + a CLI flag) fixes a path the operator
> never runs. Two operator-surface defects the discovery exposes, both squarely in BL-025's
> spirit:
> - **Unconditional `verified: true` (`verify.ex:35`)** — a vacuous green (Silent-wrong-answer,
>   the promoted class): the CLI cannot report a verification failure.
> - **Full live re-run** — the CLI re-issues every effect (`http_call` included) with none of
>   even the filesystem containment the `Verifier` sandbox has. *More* dangerous than the
>   `Verifier` path BL-025 was scoped against.
>
> ## Additions to the ticket (fold into the BL-025 prompt)
> 1. **Rewire `Commands.Verify.run/2` → `Aetheris.verify/2`** and render the real report.
>    `aetheris verify <traj>` now re-executes recorded tool calls and compares — the behavior
>    `determinism-contract §3`'s verify row already describes — instead of starting a live run.
>    Grep `aetheris verify` usages (`sprint.sh`, docs) and reconcile any that assumed the old
>    live-run shape.
> 2. **Kill the unconditional `verified: true`.** The CLI propagates the `Verifier` verdict —
>    verified / failed / **served** (§D) — and its **exit code reflects failure** (a failing
>    verify exits non-zero; a served-only verify does not print a green that overstates
>    coverage). Red-first face (a): show the CLI returns `verified: true` today on a trajectory
>    the `Verifier` would fail.
> 3. **`--allow-effects` is now real** (§E stands) — it gates the `Verifier` path the CLI
>    actually reaches once rewired.
> 4. **Second contract edit — §3 verify row (§8-governed, human-approved in-cycle, drafted
>    with §5).** §3 cites `verifier.ex`, so it describes the `Verifier`; the CLI had silently
>    diverged (§8: "code diverging from this doc is a defect… never a silent reinterpretation").
>    The §3 edit: state that the CLI routes through the `Verifier`, and **disentangle
>    `RunConfig mode: :verify` (a live-run modifier: skip trimming + pre-tools) from the
>    `Verifier` (re-execution + compare)** — the contract currently blurs the two, and that
>    blur is what let the CLI diverge unnoticed. Put §3 + §5 in one review-file
>    (`docs/reviews/bl-025-contract-draft.md`) for a single human approval before the commit.
> 5. **Rewrite the vacuous test.** `verify_test.exs`'s `verified == true` assertion is over a
>    zero-tool-call run — vacuous by the Silent-wrong-answer rule (passes whether or not
>    verification works). Replace with a real pair: a run whose recorded tool call **verifies**
>    (true) and one whose recorded output was tampered so it **fails** (false), mutation-checked.
> 6. **CLI-level red-first.** The hermetic no-egress test runs against `aetheris verify` (the
>    operator surface), not only `Aetheris.verify/2`: default → **0 inbound connections** to
>    the local listener + served-not-verified reporting; `--allow-effects` → the hit returns.
>    Done-when is true where the operator is, not only in the library.
>
> ## Adjacent finding — do NOT fix here (file a row)
> After the rewire, confirm whether anything still sets `RunConfig mode: :verify`. If
> `Commands.Verify` was its only setter, the member is vestigial — the exact shape of
> **BL-033** (`:fork` in the same union). File a sibling backlog row; do **not** delete it in
> BL-025 (don't grow scope). This is the RunConfig **mode** union, distinct from the event-type
> union (BL-040) — name it precisely; conflating those two was itself a recorded sketch-failure.
>
> ## Updated Touches (repo-qualified) — adds to the prior list
> - `../aetheris/lib/aetheris/cli/commands/verify.ex` (rewire → `Aetheris.verify/2`;
>   `--allow-effects`; propagate verdict + failure-reflecting exit code)
> - `../aetheris/docs/aetheris/determinism-contract.md` **§3 and §5** (both §8, one approval)
> - `../aetheris/test/…/verify_test.exs` (replace the vacuous `verified == true` with a
>   mutation-checked pass/fail pair)
>
> ## Updated done-when
> As drafted (effect classes; record-and-serve for `:uncontained` = http_call + MCP;
> served-not-verified reporting; completeness test), **plus:** `aetheris verify` — the CLI, the
> operator surface — routes through the `Verifier`; returns the real verdict with a
> failure-reflecting exit code; re-issues no uncontained effect without `--allow-effects`,
> proven by a **CLI-level** hermetic no-egress test (0 hits default, hit under opt-in); §3 and
> §5 both rewritten and human-approved this cycle; the vacuous `verified == true` test replaced
> with a mutation-checked pass/fail pair; the vestigial-`mode: :verify` finding filed if it
> holds.
>
> ## Note — ticket has grown
> This is now "make `aetheris verify` real *and* safe" rather than "add containment to the
> Verifier." Still coherent as one cycle (the `--allow-effects` opt-in and the no-egress
> done-when both require the CLI on the `Verifier`). If you'd rather keep cycles small it splits
> cleanly — **(1)** rewire CLI → Verifier + kill unconditional-true + §3 edit ("make verify
> real"), then **(2)** effect classes + record-and-serve + `--allow-effects` + §5 ("make it
> safe") — each independently verifiable, and (1) already improves the operator surface
> (fs-contained real verification vs today's uncontained live re-run). Your call; single-cycle
> stands unless you say otherwise.

### A.2 — Round 2 (scope correction rev 3, human, 2026-07-22)

> # BL-025 — scope correction (rev 3): run_command is allowlist-contained, not egress-incapable
>
> **Decision (human, 2026-07-22): Option 1** — classify `run_command` `:contained`, name the
> interpreter-egress limitation plainly in §5, file a capability-containment row. Folds into
> the BL-025 prompt §A + §F.
>
> ## Finding (executing session, re-verify-at-HEAD)
> `aetheris_exec_server/src/runner.rs:7-24` permits not just fs/`git_*` but `python3`,
> `python`, `node`, `npm`, `mix`, `cargo`, `git` — every one can open a socket, and
> `npm install` / `mix deps.get` / `cargo build` / a fetching python script egress **by
> design**. §5's "run_command has no effects the sandbox fails to contain" is **command-shaped**
> (the allowlist blocks `curl`/`wget`), not **capability-shaped**. So `run_command` re-executed
> under verify can egress today.
>
> ## The conceptual spine (put this in the §5 rewrite)
> Record-and-serve and capability containment defend **different tool kinds**; the taxonomy
> must say which is which, and why:
> - **Purpose-is-network** (`http_call`, MCP): the tool's output *is* a network response.
>   Serving the recorded response is semantically correct; re-executing is both unsafe and a
>   live call. → `:uncontained`, **record-and-serve** (BL-025).
> - **Incidental egress** (`run_command`): egress is a property of *some invocations*, not of
>   the tool; you want to re-run it to verify the computation. Record-and-serve would be
>   semantically wrong and would gut verify (run_command is verify's primary subject). The
>   correct defence is the **sandbox layer** (`CLONE_NEWNET`), not the taxonomy. → `:contained`,
>   **re-executed**, with the egress hole named until the netns row lands.
>
> `:contained` therefore means **"contained against the exec allowlist,"** explicitly **not
> "incapable of egress."** State that definition in §5 verbatim — the class name overpromises
> without it.
>
> ## §5 rewrite requirements (truthful at HEAD — this is why Option 3 is rejected)
> The §5 edit must:
> 1. Define the three classes by the spine above (purpose-network → serve; incidental egress →
>    re-execute under capability containment; pure → re-execute).
> 2. **Replace** the current "run_command has no effects the sandbox fails to contain" claim
>    with the accurate one: the exec allowlist blocks `curl`/`wget` but permits interpreters
>    and build tools (`python3`/`node`/`npm`/`mix`/`cargo`/`git`) that can egress, and verify
>    re-executes `run_command`, so an egressing invocation re-egresses. This is a **named
>    limitation of the taxonomy**, not a bug in it — the taxonomy is tool-shaped and cannot see
>    capability-level egress through an allowed interpreter.
> 3. State that record-and-serve (BL-025) closes egress for the **purpose-network** tools only;
>    incidental egress via `run_command` is closed by **BL-042** (capability containment), and
>    until that lands verify's egress-safety is **partial**. Cross-ref BL-042.
>
> ## Done-when — narrowed honestly (do NOT overclaim)
> BL-025's done-when is **not** "verify cannot re-perform any external effect." It is: verify
> does not re-perform **worker-native network-tool** effects (`http_call`, MCP) without
> `--allow-effects`, proven by the CLI-level hermetic no-egress test **for `http_call`**. The
> `run_command` interpreter-egress path is a named §5 limitation tracked by BL-042 — **not
> closed here**, and the packet must say so rather than let "verify is now safe" imply
> capability-level containment. (A doc/report that implies full egress-safety it doesn't have
> is the same Silent-wrong-answer this ticket exists to remove — applied to our own claim.)
>
> *[The round also supplied the full BL-042 row text, filed verbatim — see §C's agents diff.]*
>
> ## Note — could fold netns into BL-025 instead of BL-042
> The netns change is what makes the done-when literally true. It's held out because it's a
> Rust sandbox change with its own verification surface (clone flags + seccomp interaction +
> the run_command divergence semantics above), and it *requires* BL-025's record-and-serve
> already landed so `http_call`/MCP don't just fail. Sequencing BL-025 → BL-042 keeps each
> bounded and independently verifiable. Say the word if you'd rather fold it in and take one
> bigger cycle.

### A.3 — Round 3 (packet review, human, 2026-07-23)

> BL-027 exposure → fold the fix into BL-025. Apply `recorded_result/1` (the "output"-else-"result"
> reader `serve_step` already uses) to `verify_step`'s recorded-output read, plus a red-first test:
> a trajectory with a failed `read_file` verifies without crashing. It's ~1 line + a test, it's the
> precedent BL-028 already set, and it closes the operator crash BL-025 itself creates. Shipping
> "make verify real" with the now-real command crashing on a routine failed-tool trajectory isn't
> a state worth releasing. This largely closes BL-027 — mark it Done (or near-done, if you want its
> shared-payload-key-convention note with BL-028 tracked separately).
>
> Contract §3/§5 → approve, with the one coupling edit. I reviewed the draft line-by-line; it's
> accurate and honest (the two corrected inferences are exemplary). The only change: if you fold
> the BL-027 fix in, §5's "Residual limitations → in-process tools" paragraph flips from "remains
> reachable for a contained tool whose recorded result is an error (BL-027)" to closed. Everything
> else lands as drafted.
>
> Net: one small code addition (verify_step reader + test), then the contract approval, then it's
> mergeable. Everything else in the packet I accept as-is.

### A.4 — Round 4 (sign-off, human, 2026-07-23)

> Signed off — this is mergeable. The BL-027 fold-in is clean: red (KeyError on a plain failed
> `read_file`), green (honest `:output_mismatch` with `recorded_output: "Error: :enoent"` — record
> failed, re-execution succeeded, which is the truthful divergence, not a crash), Done. Gates green
> post-change (900/0, worker 25/0, drift exit 0).
>
> The BL-046 split is the right call and the reasoning is exactly the discipline — you caught that
> fork's reader normalizes (nil→"", non-binary→JSON per §2) while verify must reflect the record
> verbatim, so a naive shared helper would silently impose fork's normalization on verify.
> Declaring the writer-side convention and leaving "shared code vs shared convention" explicit —
> with the fourth-reader as the thing the row exists to catch — is the load-bearing-coincidence
> lesson applied forward, not another point patch. And the dated header amendment recording the two
> inferred→demonstrated corrections is the correction-chasing norm done properly: the next reader
> sees that a correction happened, not just the corrected text.
>
> One housekeeping item before you commit: the review packet needs to land in-repo at
> `aetheris-agents/docs/reviews/bl-025-review.md`, matching the bl-028/029/031 precedent. Right now
> it's only in /tmp, which strands the record — the whole "recover from repos and review files, not
> memory" norm depends on it being in the repo. That's the last durable artifact to place.

---

## §B. Dispositions

| # | Round | Instruction | Disposition |
|---|---|---|---|
| 1 | A.1 | Rewire `Commands.Verify.run/2` to the `Verifier` | **Done.** Routes to `Aetheris.verify_run/2` (not `verify/2` — the ticket and my first draft both had the wrong arity/name; corrected against source). `start_verify/3` and the `mode: :verify` run deleted |
| 2 | A.1 | Kill unconditional `verified: true`; exit code reflects failure | **Done.** `{:error, …}` on `failed > 0` → `Formatter.print/2` returns 1. Caveat filed: `mix aetheris` discards exit codes for every command (**BL-044**), so the code is asserted at `Formatter.print/2`, not by shelling through `mix` |
| 3 | A.1 | `--allow-effects` gates the real path | **Done**, with one adjudicated deviation: declared subcommand-local, not global. The cited learning describes *where parsing happens* (flags after the subcommand are parsed by the subcommand handler), and `Commands.Verify` already called `OptionParser.parse/2`. Gives `aetheris verify <traj> --allow-effects` without adding a switch every other command ignores |
| 4 | A.1 | §3 contract edit, drafted with §5, one approval | **Done.** Both drafted in `bl-025-contract-draft.md`, approved in A.3, landed |
| 5 | A.1 | Replace the vacuous `verified == true` test | **Done.** Mutation-checked pass/fail pair. Coverage gap named, not papered over: the pair re-executes a contained tool so it carries `:requires_worker`, which **CI excludes** (`ci.yml:64`) |
| 6 | A.1 | CLI-level hermetic no-egress test | **Done.** 0 connections default / 1 under opt-in. Green arm runs in the **default** `mix test` — enabled by having `Verifier` start no worker when every step is served |
| 7 | A.1 | Confirm whether `mode: :verify` is vestigial; file a row | **Filed as BL-045, with the premise corrected.** It is *not* vestigial — still reachable from agent-file config (`run_helpers.ex`) and eval templates (`eval/runner.ex:298`). The real defect is naming, so the row is a rename/document decision, explicitly **not** a BL-033-shaped deletion |
| 8 | A.2 | `run_command` stays `:contained`; name the limitation in §5 | **Done**, spine and definition stated verbatim in §5 |
| 9 | A.2 | File BL-042 (capability containment) | **Done**, verbatim, sequenced after BL-025 |
| 10 | A.2 | Do not overclaim the done-when | **Done.** Packet §12 states what is not claimed; §5 says egress-safety is *partial* until BL-042 |
| 11 | A.3 | Fold the BL-027 fix in, red-first | **Done.** One line (`verify_step/2` → `recorded_result/1`) + test. Red: `KeyError` on a plain failed `read_file`. Green: `:output_mismatch`, `recorded_output: "Error: :enoent"` |
| 12 | A.3 | Mark BL-027 Done; track the convention note separately if wanted | **Done + split.** BL-027 closed; the payload-key convention filed as **BL-046**, because the two readers are *not* interchangeable — fork's normalizes (nil → `""`, non-binary → JSON per contract §2) while verify must reflect the record verbatim, so a naive shared helper would impose fork's normalization on verify |
| 13 | A.3 | §5 residual-limitations entry flips to closed | **Done**, applied in the draft and in the landed §5 |
| 14 | A.4 | Land the record in-repo | **This file.** |

**Self-reported, not requested by the reviewer:**

- Two §5 claims were *inferred rather than demonstrated* and both proved wrong when run:
  `http_call` re-execution opens a real TCP connection but is SIGSYS-killed at `setsockopt`
  before the request is written (**BL-043** — `http_call` has never worked in any mode), and
  `run_command` is not free of uncontained effects (**BL-042**). Recorded as a dated amendment
  in the contract header so the next reader sees that a correction happened.
- The classifier could not be keyed on tool name alone (MCP names are runtime-discovered), and
  the obvious source-based fallback is a trap: the internal exec server routes `run_command`
  and all eleven `git_*` as `source: :mcp, server_id: "aetheris_exec"`, so a naive
  `source == "mcp" ⇒ uncontained` rule would have served the entire *contained* family. Pinned
  by a test.
- In-process tools are `:uncontained`, not `:pure` as the ticket sketched — `spawn_agent` can
  start a run that issues live model calls.
- The tracked escript binary cannot load the SQLite NIF, so `./aetheris <anything>` fails.
  Pre-existing and unrelated (`./aetheris list` fails identically); **not filed** — flagged to
  the reviewer, no row requested.

---

## §C. Packet (final, round 2)

Generated artifact — gate output, diffs and evidence captured from the tools, not retyped.

---

## BL-025 — Verify: effect classes + record-and-serve for uncontained tools

**Review packet** · cross-repo (harness `../aetheris/` + `aetheris-agents/`) · 2026-07-23
**Branch:** `bl-025-verify-effect-classes` (both repos) · **nothing committed, pushes held**
**Basis:** harness `1ebe971`, agents `d567d75`

**Round 2.** Review accepted the packet as-is with two instructions, both applied:
**(1)** fold the BL-027 fix into BL-025 — `verify_step/2` now reads the recorded result
through the same fallback as the served path, plus a red-first test; **(2)** contract §3+§5
**approved** with one coupling edit (§5's residual-limitations entry for recorded tool
failures flips from "remains reachable" to closed). Both landed in
`../aetheris/docs/aetheris/determinism-contract.md`. Still uncommitted; pushes held.

---

### 1. Done-check output

#### 1a. Harness gates (from `../aetheris/`)

```
$ mix format --check-formatted
(no output — clean)
```

```
$ mix compile --warnings-as-errors
Compiling 2 files (.ex)
```

```
$ mix credo --strict
Please report incorrect results: https://github.com/rrrene/credo/issues

Analysis took 2.7 seconds (0.1s to load, 2.6s running 69 checks on 219 files)
1959 mods/funs, found no issues.

Use `mix credo explain` to explain issues, `mix credo --help` for options.
```

```
$ mix dialyzer
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done in 0m4.76s
done (passed successfully)
```

```
$ mix hex.audit
No retired or security advisory packages found
```

```
$ mix test
...........
Finished in 88.6 seconds (2.6s async, 86.0s sync)
900 tests, 0 failures, 118 excluded
```

> `117 excluded` is the standing default exclusion set (`:requires_worker`, `:integration`,
> `:m10_fixture` — `test_helper.exs`), not a BL-025 change.

#### 1b. Cross-repo gate (from `aetheris-agents/`)

```
$ python3 scripts/drift_check.py --strict   (from aetheris-agents/)
Rig doc-drift checker — 8 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 48 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=f0df85a current=d567d75

Summary: 7 PASS  0 FAIL  1 WARN  7 INFO
exit code: 0
```

> The single WARN is the **exempt** `project_knowledge` manifest-staleness one (CLAUDE.md:
> manifest-staleness WARNs stay WARN and do not fail `--strict`). Exit code 0.
> Per **BL-041**, this pre-commit reading is vacuous in both directions — check 8 reads
> committed history, so the working-tree backlog edit in this packet is invisible to it and
> the hash will move after commit. Stated rather than presented as a clean bill.

#### 1c. Full test-name output for the BL-025 files (both arms)

```
$ mix test test/aetheris/execution/effect_class_test.exs test/aetheris/execution/verify_effects_test.exs test/aetheris/execution/verifier_test.exs test/aetheris/cli/commands/verify_test.exs --include requires_worker --trace
Running ExUnit with seed: 192353, max_cases: 1
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]
Aetheris.Execution.EffectClassTest [test/aetheris/execution/effect_class_test.exs]
  * test classify/2 run_command stays contained despite being routed with source: :mcp [L#54]
  * test classify/2 run_command stays contained despite being routed with source: :mcp (2.3ms) [L#54]
  * test from_tool_called/1 a payload with no source is a built-in call [L#105]
  * test from_tool_called/1 a payload with no source is a built-in call (0.00ms) [L#105]
  * test from_tool_called/1 reads the MCP source recorded on the event payload [L#83]
  * test from_tool_called/1 reads the MCP source recorded on the event payload (0.00ms) [L#83]
  * test classify/2 an unknown tool with no source is uncontained — the fail-safe default [L#50]
  * test classify/2 an unknown tool with no source is uncontained — the fail-safe default (0.00ms) [L#50]
  * test completeness over the tool set every registry tool name is classified [L#16]
  * test completeness over the tool set every registry tool name is classified (2.9ms) [L#16]
  * test classify/2 an unknown tool from an external MCP server is uncontained [L#45]
  * test classify/2 an unknown tool from an external MCP server is uncontained (0.00ms) [L#45]
  * test classify/2 in-process orb tools are uncontained — they run outside the worker sandbox [L#71]
  * test classify/2 in-process orb tools are uncontained — they run outside the worker sandbox (0.00ms) [L#71]
  * test classify/2 http_call is uncontained — its purpose is network egress [L#41]
  * test classify/2 http_call is uncontained — its purpose is network egress (0.00ms) [L#41]
  * test from_tool_called/1 an exec-server payload resolves to the contained class [L#94]
  * test from_tool_called/1 an exec-server payload resolves to the contained class (0.00ms) [L#94]
  * test classify/2 the filesystem built-ins are contained [L#65]
  * test classify/2 the filesystem built-ins are contained (0.00ms) [L#65]
  * test classify/2 echo is pure [L#77]
  * test classify/2 echo is pure (0.00ms) [L#77]
  * test completeness over the tool set the classified domain contains no name that no longer exists [L#32]
  * test completeness over the tool set the classified domain contains no name that no longer exists (22.2ms) [L#32]
  * test completeness over the tool set every in-process tool module is classified [L#25]
  * test completeness over the tool set every in-process tool module is classified (0.1ms) [L#25]
Aetheris.Execution.VerifyEffectsTest [test/aetheris/execution/verify_effects_test.exs]
  * test default verify serves the recorded http_call and opens no connection [L#34]
  * test default verify serves the recorded http_call and opens no connection (11.2ms) [L#34]
  * test --allow-effects re-executes the http_call and the connection returns [L#86][sandbox] entered user+mount namespaces (uid=1000, gid=1000)

  * test --allow-effects re-executes the http_call and the connection returns (115.6ms) [L#86]
  * test a recorded http_call failure is served verbatim, not improved on [L#60]
  * test a recorded http_call failure is served verbatim, not improved on (0.7ms) [L#60]
Aetheris.Execution.VerifierTest [test/aetheris/execution/verifier_test.exs]
  * test a recorded tool FAILURE on a contained tool verifies without crashing [L#127][sandbox] entered user+mount namespaces (uid=1000, gid=1000)

  * test a recorded tool FAILURE on a contained tool verifies without crashing (3.0ms) [L#127]
  * test verify/2 returns {:error, :not_found} for an unknown run_id [L#22]
  * test verify/2 returns {:error, :not_found} for an unknown run_id (0.05ms) [L#22]
  * test verify/2 marks a recorded read_file tool step as verified [L#80][sandbox] entered user+mount namespaces (uid=1000, gid=1000)

  * test verify/2 marks a recorded read_file tool step as verified (6.0ms) [L#80]
  * test to_report/1 includes the run_id and verified marker [L#52]
  * test to_report/1 includes the run_id and verified marker (0.03ms) [L#52]
  * test verify/2 returns an empty report when the trajectory has no tool calls [L#35]
  * test verify/2 returns an empty report when the trajectory has no tool calls (0.3ms) [L#35]
  * test verify/2 returns {:error, :sandbox_required} when no sandbox path is available [L#27]
  * test verify/2 returns {:error, :sandbox_required} when no sandbox path is available (0.2ms) [L#27]
Aetheris.CLI.Commands.VerifyTest [test/aetheris/cli/commands/verify_test.exs]
  * test a trajectory whose recorded output was tampered with fails, and exits non-zero [L#36][sandbox] entered user+mount namespaces (uid=1000, gid=1000)
Error: verify failed: 1 of 1 steps diverged
Verify: verify-cli-3330
Tools verified: 0  Served (not verified): 0  Failed: 1
step 1  read_file  {"path":"hello.txt"}  output_mismatch
  recorded output: NOT what is on disk
  actual output: on disk
  recorded fs_hash: nil
  actual fs_hash: nil

  * test a trajectory whose recorded output was tampered with fails, and exits non-zero (8.4ms) [L#36]
  * test a verify with no tool calls reports zero verified, not a blanket pass [L#67]
  * test a verify with no tool calls reports zero verified, not a blanket pass (0.5ms) [L#67]
  * test a trajectory whose recorded output matches verifies, and exits zero [L#53][sandbox] entered user+mount namespaces (uid=1000, gid=1000)

  * test a trajectory whose recorded output matches verifies, and exits zero (3.5ms) [L#53]
Finished in 0.2 seconds (0.1s async, 0.1s sync)
25 tests, 0 failures
```

---

### 2. Red-first evidence

The load-bearing assertion is **inbound connection count**, not exit status.

#### 2a. Green — default verify opens no connection (runs in the DEFAULT `mix test`)

From §1c, `Aetheris.Execution.VerifyEffectsTest`:

- `default verify serves the recorded http_call and opens no connection` — asserts
  `connection_count == 0`, `served == 1`, `verified == 0`, and that the **recorded** output
  was served.
- `a recorded http_call failure is served verbatim, not improved on` — asserts
  `connection_count == 0` and that the recorded `"result"` (a failure with **no `"output"`
  key at all**) is served unchanged.

Both are untagged, so they run in the default suite. That was a design constraint, not an
accident: `:requires_worker` is excluded by `test_helper.exs` **and** by CI
(`ci.yml:64`), so a worker-dependent green arm would have been silently excluded from every
automated run — a vacuous green of exactly the class this ticket removes. `Verifier` now
starts no worker at all when every step is served, which is both the safety property and
what keeps this arm runnable.

#### 2b. Red — the effect is real: `--allow-effects` re-opens the connection

`--allow-effects re-executes the http_call and the connection returns` (§1c, tagged
`:requires_worker`) asserts `connection_count >= 1`.

Independent confirmation on a path BL-025 does not touch (`Worker.Client` only):

```
$ mix run scratchpad/probe2.exs   # Worker.Client only — no BL-025 code on this path
** (stop) {:worker_crashed, 159}
>>> execute result: {:error, "worker_crashed"}
>>> INBOUND TCP CONNECTIONS TO LISTENER: 1
```

#### 2c. Correction to §5's premise — the egress claim was inferred, and is partly wrong

§5 states verify "issues those network calls again". Demonstrated: a **TCP connection does
land** (count 1 above), but the HTTP request is never written — the worker is killed by
SIGSYS. Kernel audit:

```
$ journalctl -k --no-pager | grep aetheris_worker | tail -2
audit: type=1326 audit(1784774526.208:283): auid=1000 uid=1000 gid=1000 ses=4 subj=unconfined pid=295637 comm="aetheris_worker" exe="/home/it/sandbox/elixirws/aetheris/priv/worker/aetheris_worker" sig=31 arch=c000003e syscall=54 compat=0 ip=0x791c01927b4e code=0x80000000
audit: type=1326 audit(1784774550.811:284): auid=1000 uid=1000 gid=1000 ses=4 subj=unconfined pid=295748 comm="aetheris_worker" exe="/home/it/sandbox/elixirws/aetheris/priv/worker/aetheris_worker" sig=31 arch=c000003e syscall=54 compat=0 ip=0x70d664f27b4e code=0x80000000
```

`sig=31` is SIGSYS; `syscall=54` on x86_64 is **`setsockopt`**, which is absent from the
worker's seccomp allowlist — under a section headed *"Network (http_call + MCP stdio)"*.
Worker exit status 159 = 128+31.

So `http_call` has **never worked, in any mode, including record runs**. Filed as **BL-043**.
The trap this packet is explicit about: *do not read that crash as containment*. It is an
accidental truncation of a real egress path; repairing it restores full egress instantly,
which is why BL-043 is sequenced after BL-042.

#### 2d. Red → green — BL-027 folded in: a failed contained tool crashed verify

Round-2 instruction. The stated trigger for BL-027 (a multi-agent/orb trajectory) was too
narrow: `Loop.record_tool_error/7` writes **every** recorded tool failure under `"result"`
with `"is_error"` and no `"output"` key, contained worker tools included. So a single failed
`read_file` took verify down — and BL-025, by making `aetheris verify` actually route through
`Verifier`, would have shipped that as the command's operator-visible behaviour.

Fix is one line: `verify_step/2` reads through the same `recorded_result/1` the served path
already used.

```
# RED — before the verify_step reader change
$ mix test test/aetheris/execution/verifier_test.exs --include requires_worker
Running ExUnit with seed: 194983, max_cases: 16
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]
....[sandbox] entered user+mount namespaces (uid=1000, gid=1000)
  1) test a recorded tool FAILURE on a contained tool verifies without crashing (Aetheris.Execution.VerifierTest)
     test/aetheris/execution/verifier_test.exs:127
     ** (KeyError) key "output" not found in: %{"is_error" => true, "result" => "Error: :enoent", "tool_name" => "read_file"}
     code: assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)
     stacktrace:
       :erlang.map_get("output", %{"is_error" => true, "result" => "Error: :enoent", "tool_name" => "read_file"})
       (aetheris 0.1.0) lib/aetheris/execution/verifier.ex:201: Aetheris.Execution.Verifier.verify_step/2
       (elixir 1.17.2) lib/enum.ex:1703: Enum."-map/2-lists^map/1-1-"/2
       (aetheris 0.1.0) lib/aetheris/execution/verifier.ex:76: Aetheris.Execution.Verifier.execute_planned_steps/3
       test/aetheris/execution/verifier_test.exs:155: (test)
.
Finished in 0.1 seconds (0.00s async, 0.1s sync)
6 tests, 1 failure

# GREEN — after applying recorded_result/1 to verify_step
$ mix test test/aetheris/execution/verifier_test.exs --include requires_worker --trace
Compiling 2 files (.ex)
Running ExUnit with seed: 732775, max_cases: 1
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]
Aetheris.Execution.VerifierTest [test/aetheris/execution/verifier_test.exs]
  * test verify/2 returns {:error, :not_found} for an unknown run_id [L#22]
  * test verify/2 returns {:error, :not_found} for an unknown run_id (1.1ms) [L#22]
  * test a recorded tool FAILURE on a contained tool verifies without crashing [L#127][sandbox] entered user+mount namespaces (uid=1000, gid=1000)

  * test a recorded tool FAILURE on a contained tool verifies without crashing (11.3ms) [L#127]
  * test verify/2 returns an empty report when the trajectory has no tool calls [L#35]
  * test verify/2 returns an empty report when the trajectory has no tool calls (0.4ms) [L#35]
  * test verify/2 returns {:error, :sandbox_required} when no sandbox path is available [L#27]
  * test verify/2 returns {:error, :sandbox_required} when no sandbox path is available (0.3ms) [L#27]
  * test to_report/1 includes the run_id and verified marker [L#52]
  * test to_report/1 includes the run_id and verified marker (0.02ms) [L#52]
  * test verify/2 marks a recorded read_file tool step as verified [L#80][sandbox] entered user+mount namespaces (uid=1000, gid=1000)

  * test verify/2 marks a recorded read_file tool step as verified (6.3ms) [L#80]
Finished in 0.1 seconds (0.00s async, 0.1s sync)
6 tests, 0 failures
```

#### 2e. Red — the CLI could not report a failure at all

Face (a) is evidenced by the code being removed (§5 diff, `cli/commands/verify.ex`):
`Commands.Verify.run/2` started a **new live run** (`mode: :verify`) and returned
`%{run_id: …, status: :done, verified: true}` unconditionally — plus the deleted test that
asserted `verified == true` over a **zero-tool-call** run, which would have passed whether or
not verification worked.

---

### 3. Operator surface — before / after

`aetheris verify` now routes through `Aetheris.Execution.Verifier`. Shown through
`Aetheris.CLI.run/1`, which is exactly the value the escript hands to `System.halt/1`.

**Pass arm** (mixed trajectory: one contained tool, one uncontained):

```
$ mix run -e 'System.halt(Aetheris.CLI.run(["verify", "priv/runs/bl025-demo/trajectory.json"]))'
Verify: bl025-demo
Tools verified: 1  Served (not verified): 1  Failed: 0
step 1  read_file  {"path":"hello.txt"}  ✓ verified
step 2  http_call  {"url":"https://api.example.com/v1/things"}  served (not re-executed)
  recorded output: {"status":200,"body":"recorded"}
  not re-executed (uncontained effect); no fs_hash claim
exit code: 0
```

**Divergence arm** (same command, recorded `read_file` output tampered):

```
# same command, after tampering the recorded read_file output in the trajectory
Error: verify failed: 1 of 2 steps diverged
Verify: bl025-demo
Tools verified: 0  Served (not verified): 1  Failed: 1
step 1  read_file  {"path":"hello.txt"}  output_mismatch
  recorded output: TAMPERED — not what is on disk
  actual output: on disk
  recorded fs_hash: nil
  actual fs_hash: nil
step 2  http_call  {"url":"https://api.example.com/v1/things"}  served (not re-executed)
  recorded output: {"status":200,"body":"recorded"}
  not re-executed (uncontained effect); no fs_hash claim
exit code: 1
```

Before BL-025 this command returned `verified: true` and exit 0 in **both** cases.

> Not demonstrated through the built escript: `mix escript.build`'s binary cannot load the
> SQLite NIF, so every DB-touching command fails there. Confirmed **pre-existing and
> unrelated** — `./aetheris list`, untouched by this ticket, fails identically. Not filed;
> say if it warrants a row.

---

### 4. Mutation-check — the completeness test is load-bearing

```
# MUTATION: remove git_cherry_pick_control from the classifier, as if a tool were added unclassified
$ mix test test/aetheris/execution/effect_class_test.exs
Running ExUnit with seed: 680441, max_cases: 16
Excluding tags: [:requires_worker, :integration, :m10_fixture]
.....
  1) test completeness over the tool set every registry tool name is classified (Aetheris.Execution.EffectClassTest)
     test/aetheris/execution/effect_class_test.exs:16
     unclassified registry tools: ["git_cherry_pick_control"]. Add them to Aetheris.Execution.EffectClass and revisit determinism-contract.md §5 if any is uncontained.
     code: assert unclassified == [],
     stacktrace:
       test/aetheris/execution/effect_class_test.exs:19: (test)
.......
Finished in 0.04 seconds (0.04s async, 0.00s sync)
13 tests, 1 failure

# restored
.............
Finished in 0.03 seconds (0.03s async, 0.00s sync)
13 tests, 0 failures
```

---

### 5. Diff — harness (`../aetheris/`)

```
$ git diff --stat  (harness)
 docs/aetheris/determinism-contract.md          | 196 ++++++++++++++++++-------
 docs/aetheris/runbook.md                       |  61 +++++++-
 lib/aetheris.ex                                |   4 +
 lib/aetheris/cli/commands/verify.ex            |  71 +++++----
 lib/aetheris/cli/output/formatter.ex           |   6 +
 lib/aetheris/execution/tool_schema/registry.ex |   9 ++
 lib/aetheris/execution/verifier.ex             | 111 ++++++++++++--
 lib/aetheris/execution/verify_report.ex        |  17 ++-
 test/aetheris/cli/commands/verify_test.exs     | 125 ++++++++++++----
 test/aetheris/execution/verifier_test.exs      |  44 +++++-
 10 files changed, 515 insertions(+), 129 deletions(-)

new files:
?? docs/aetheris/milestones/bl-025-implementation-notes.md
?? lib/aetheris/execution/effect_class.ex
?? test/aetheris/execution/effect_class_test.exs
?? test/aetheris/execution/verify_effects_test.exs
```

<details><summary>Full diff + new files (complete, untruncated)</summary>

`````diff
diff --git a/docs/aetheris/determinism-contract.md b/docs/aetheris/determinism-contract.md
index eb7942c..6873c4d 100644
--- a/docs/aetheris/determinism-contract.md
+++ b/docs/aetheris/determinism-contract.md
@@ -12,6 +12,14 @@ diverged from `verifier.ex`, and §3's verify row + §5 were rewritten under hum
 approval to describe actual behavior (the prior draft's effect-free / output-hash
 framing was incorrect). No `[t1-verify]` tag remains — each is resolved to a source
 citation or corrected wording.
+**Amended 2026-07-23 (BL-025, human-approved in-cycle per §8):** §3's verify row and §5
+rewritten for the effect-class taxonomy and record-and-serve. Two §5 claims that had been
+*inferred from source reading rather than demonstrated* were corrected against a hermetic
+test: `http_call` re-execution opens a real TCP connection but is SIGSYS-killed before the
+request is written (BL-043), and `run_command` is **not** free of uncontained effects — its
+allowlist permits socket-capable interpreters (BL-042). §3 additionally separates `verify`
+the command from `RunConfig mode: :verify`, a blur that had let the CLI diverge from this
+section unnoticed.
 **Research basis:** `docs/aetheris/research/activegraph-log-is-agent-2026-07.md`
 (paper: arXiv:2605.21997).
 
@@ -48,11 +56,29 @@ happen if the run were executed again.
 |---|---|---|
 | `record` (live run) | Complete event capture sufficient to reconstruct the transcript; atomic trajectory write (`write .tmp`, rename) | Any reproducibility of the execution itself |
 | `replay` | Reconstruction from recorded events; **no live model or tool calls** (`replayer.ex:24-29`, `52-70`; reads the trajectory file, `replayer.ex:25` → `file.ex:51-59`) | Reproduction of environment effects; anything about events the record lacks |
-| `verify` | Re-execution of every recorded tool call in a fresh sandboxed worker (`verifier.ex:45-58,130-136`); compares recorded vs. re-executed tool **output by value equality** and recorded vs. actual filesystem **`fs_hash`** (`verifier.ex:168-174`); emits a per-step report with verified/failed counts (`verifier.ex:176-186`) | Effect-class selection — **all** recorded tools are re-executed regardless of side effects, so re-execution can cause **real external effects** (notably `http_call` network egress, §5); byte-identity of anything a model produced; naming a single first diverging event (§5) |
+| `verify` | Re-execution of every recorded tool call **whose effect class permits it** in a fresh sandboxed worker (`verifier.ex`, `effect_class.ex`); compares recorded vs. re-executed tool **output by value equality** and recorded vs. actual filesystem **`fs_hash`**; serves the recorded result for `:uncontained` tools instead of re-executing them (§5), reporting those steps as **served, not verified**; emits a per-step report with verified/served/failed counts | Verification of a served step — a served step is a record echo and cannot fail; byte-identity of anything a model produced; naming a single first diverging event (§5); **capability-level egress safety** — see §5's `run_command` limitation |
 | `fork` | §4 — the fork guarantee (D1) | §4 non-guarantees |
 
+**`verify` the command vs. `:verify` the run mode.** These are different things and this
+contract previously blurred them, which is how the CLI diverged from this section
+unnoticed for the life of the doc.
+
+- **`Aetheris.Execution.Verifier`** — re-execution of recorded tool calls and comparison
+  against the record. This is what "verify" means in this contract, what §5 governs, and
+  what `aetheris verify <trajectory>` invokes (`cli/commands/verify.ex` →
+  `Aetheris.verify_run/2`).
+- **`RunConfig.mode: :verify`** — a *live-run modifier* with no verification semantics
+  whatsoever. It skips context trimming (`loop.ex:409-411`) and pre-tools
+  (`pre_tools.ex:59`); every other aspect of the run is a normal live run, including live
+  model calls and live tool execution. It is reachable from agent-file config
+  (`run_helpers.ex`, `normalize_config_value(:mode, …)`) and eval task templates
+  (`eval/runner.ex:298`).
+
+Nothing in the harness treats `mode: :verify` as verification. A consumer wanting the
+guarantee in the table above must use the `Verifier`, not the mode.
+
 **Divergence report (verify).** Verify's divergence report lists every diverging step
-with verified/failed counts and per-step details (`verifier.ex:176-186`, `188-242`); it
+with verified/served/failed counts and per-step details; it
 does **not** single out the first diverging event. This is a documented gap (reference
 UX: divergence pinned to the first non-reproducing event, brief Part 2), tracked in the
 milestone backlog (filed at the D6 export boundary) — the claim is not upgraded to the
@@ -111,54 +137,124 @@ Tracked: BL-039 (`../aetheris-agents/docs/backlog-2026-06.md`).*
 through `Fork.from_step/3`. (Today the CLI does not, `cli/commands/fork.ex:47-55`
 — a defect against this contract, resolved by t2.)
 
-## 5. Verify re-execution: current policy and containment
-
-`verify` re-executes **every** recorded tool call in a sandboxed worker; there is
-**no** effect-class declaration mechanism and **no** allowlist — tool identity is
-never inspected before re-execution (`verifier.ex:108-136`). (Replay, by contrast,
-re-executes nothing — §3.)
-
-**Containment boundary (from source).** The verify sandbox confines the **filesystem
-only**: the re-execution worker runs under a user+mount namespace with sandbox-root
-path confinement (`sandbox.rs:135-161`, `28-104`; verify passes no overlay, so
-OverlayFS is not mounted on this path — `verifier.ex:46`, `main.rs:59-74`). It does
-**not** confine the network — no network namespace is created (`CLONE_NEWNET` absent,
-`sandbox.rs:144`) and the seccomp filter explicitly permits the socket/connect family
-(`sandbox.rs:265-278`).
-
-**Consequence — verify re-execution is NOT side-effect-safe today.** Of the current
-built-in tools, the filesystem tools (`read_file`, `list_dir`, `write_file`), the
-local-only `git_*` family (no `push`/`fetch`/`pull`/`clone` exposed — `runner.rs`),
-`run_command` (its allowlist carries no networked command; `curl`/`wget` are blocked
-and tested — `runner.rs:7-24`, `207-218`) have no effects the sandbox fails to
-contain. But **`http_call`** (`tool_schema/registry.ex:263-287`,
-`native/aetheris_worker/src/http.rs:3-39` via `ureq`, no host allowlist) makes **real
-outbound HTTP(S) requests**, and verify re-executes it like any other recorded tool
-(`main.rs:375-400`). Running `verify` on a trajectory containing `http_call` therefore
-issues those network calls again.
-
-**In-process / inter-agent tools are not handled by verify.** Verify's re-execution is
-worker-only (`verifier.ex:46,136`) with no harness-side dispatch, so no in-process tool
-implementation runs under verify (`spawn_agent` cannot start a live sub-agent;
-`ask_human`/`wait_*` cannot block). But verify does not cleanly skip them either: an
-in-process tool whose `:tool_called`/`:tool_result` events stay adjacent is paired
-(`verifier.ex:121-128`) and makes verify raise `KeyError` at `verifier.ex:133`
-(`Map.fetch!(payload, "output")` — in-process results use the `"result"` key,
-`loop.ex:421-497`) before any worker call; others are silently skipped when an
-intervening recorded event breaks adjacency. A multi-agent/orb trajectory therefore
-crashes or under-reports under verify — a robustness defect (backlog).
-
-**Tripwire + deferral.** The fix — declaring a tool's effect class and switching
-effectful tools to **record-and-serve** under verify (the recorded response is served,
-never re-executed) — does not exist yet; it is deferred, with a backlog entry filed at
-the milestone's export boundary (D6) carrying the paper/brief citation. **Before any
-further tool with effects the sandbox does not contain is added to the harness, this
-section MUST be revisited via a human-approved edit.** Until then, treat `verify` as
-reliable only on trajectories whose tools are the filesystem built-ins (`read_file`,
-`list_dir`, `write_file`), `run_command`, and the local `git_*` family — it re-issues
-`http_call`'s network effect, MCP tool calls are likewise uncontained, and in-process /
-orb tools crash or silently skip it (above; echo is the exception — worker-dispatched
-and effect-free, it yields a spurious per-step error rather than a crash).
+## 5. Verify re-execution: effect classes and containment
+
+`verify` re-executes recorded tool calls in a sandboxed worker and compares the result
+against the record. Whether a given tool is re-executed at all is decided by its
+**effect class**, declared in one place — `Aetheris.Execution.EffectClass`
+(`lib/aetheris/execution/effect_class.ex`). (Replay, by contrast, re-executes nothing —
+§3.)
+
+### The three classes
+
+The taxonomy is aligned to the containment boundary, and the two effectful classes are
+separated by *why* they escape it — because the correct defence differs:
+
+- **`:uncontained`** — the tool's **purpose** is to reach outside the boundary, so the
+  recorded result *is* the answer and re-executing it is both unsafe and pointless.
+  Members: `http_call`; every external MCP tool; and the in-process orb/agent tools
+  (`spawn_agent`, `wait_for_all`, `wait_for_event`, `ask_human`, `send_message`,
+  `broadcast_message`, `read_blackboard`, `write_blackboard`), which run in the BEAM and
+  are therefore outside the worker sandbox altogether — `spawn_agent` can start a run
+  that issues live model calls. These are **record-and-served**: the recorded result is
+  returned, the tool is never invoked.
+
+- **`:contained`** — contained **against the exec-server allowlist**. Members:
+  `read_file`, `list_dir`, `write_file`, `run_command`, and the eleven local `git_*`
+  tools. These are **re-executed and compared** — that is what verify is for.
+
+- **`:pure`** — effect-free (`echo`). Re-executed.
+
+**`:contained` does not mean "incapable of egress."** It means the exec allowlist
+(`native/aetheris_exec_server/src/runner.rs:7-24`) does not name a networking command:
+`curl` and `wget` are blocked and tested (`runner.rs`, `non_permitted_command_is_blocked`).
+But the same allowlist permits `python3`, `python`, `node`, `npm`, `mix`, `cargo` and
+`git` — every one socket-capable, and `npm install` / `mix deps.get` / `cargo build`
+egress by design. So a recorded `run_command` that performed network I/O **will do so
+again under verify**. This is *incidental* egress: a property of particular invocations
+rather than of the tool, which is why record-and-serve is the wrong instrument for it
+(it would serve every computation verify exists to re-check). The right instrument is
+capability-shaped containment at the sandbox layer — tracked as **BL-042**
+(`../aetheris-agents/docs/backlog-2026-06.md`). **Until BL-042 lands, verify's
+egress-safety is partial: closed for the purpose-network tools, open for incidental
+egress through an allowed interpreter.**
+
+### Containment boundary (from source)
+
+The re-execution worker runs under a user+mount namespace with sandbox-root path
+confinement (`sandbox.rs:135-161`, `28-104`; verify passes no overlay, so OverlayFS is
+not mounted on this path — `verifier.ex`, `main.rs:59-74`). It confines the
+**filesystem only**: no network namespace is created (`CLONE_NEWNS | CLONE_NEWUSER`
+only — `sandbox.rs:137,144`), and the seccomp filter's allowlist explicitly includes the
+socket family under a "Network (`http_call` + MCP stdio)" heading (`sandbox.rs:264-278`).
+
+### Demonstrated behaviour of an `http_call` re-execution
+
+Re-executing a recorded `http_call` under `--allow-effects` **opens a real TCP connection
+to the recorded host**. Demonstrated, not inferred: against a hermetic localhost listener
+that counts inbound connections, the default path records **0** connections and the
+`--allow-effects` path records **1**
+(`test/aetheris/execution/verify_effects_test.exs`).
+
+The request is not completed, for a reason that is a defect rather than a safeguard: the
+seccomp allowlist omits `setsockopt` (x86_64 syscall 54), so `ureq` is killed by SIGSYS
+after `connect(2)` and before the request is written — kernel audit
+`type=1326 … comm="aetheris_worker" sig=31 … syscall=54`, worker exit status 159. The
+connection still lands. **This truncation must not be read as containment**: it is
+tracked separately (BL-043), it makes `http_call` unusable in *record* runs as well, and
+repairing it (adding `setsockopt` to the allowlist, which the "Network" heading shows was
+the intent) restores full egress immediately. Record-and-serve is what makes verify safe
+here; the SIGSYS is an unrelated bug that happens to truncate the symptom.
+
+### Reporting: served is not verified
+
+A served step performs no re-execution, so nothing is compared: there is no output
+equality check and **no `fs_hash` claim**. A served step is reported with status
+`served (not re-executed)` and counted in a distinct `served` tally, never in `verified`
+(`verify_report.ex`, `verifier.ex`). A verify whose every effectful step was served
+therefore reports `Tools verified: 0  Served (not verified): N  Failed: 0` — it does not
+print a green count that overstates what was checked. This matters because a served step
+**cannot fail**: it echoes the record, so it would look identical if the underlying tool
+were entirely broken.
+
+### The opt-in
+
+`aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
+tools. Default is off. The flag re-issues real network and MCP effects and says so in its
+help text.
+
+### Tripwire — now mechanized
+
+The previous version of this section carried a prose tripwire: *"before any further tool
+with effects the sandbox does not contain is added to the harness, this section MUST be
+revisited."* Prose has no executor. It is now enforced by
+`test/aetheris/execution/effect_class_test.exs`, which asserts `EffectClass` is **total**
+over the built-in registry (`Registry.names/0`) and over every in-process tool module, and
+fails CI with an actionable message when a tool is added unclassified. An unknown tool
+name classifies as `:uncontained` at runtime — fail-safe, so an unclassified tool is
+served rather than silently re-executed. The doc obligation stands alongside the test: a
+new `:uncontained` tool still requires a human-approved edit here.
+
+### Residual limitations
+
+- **Incidental egress via `run_command`** — above; BL-042.
+- **Recorded tool failures** are read correctly on **both** paths. Every recorded tool
+  failure is written under `"result"` with `"is_error"` and no `"output"` key
+  (`loop.ex`, `record_tool_error/7`); the served and re-executed paths share one reader
+  that falls back accordingly. The former hard `Map.fetch!("output")` on the re-execution
+  path — which crashed verify on any trajectory containing a failed tool call — is fixed
+  (BL-027, closed here; its stated trigger of "a multi-agent/orb trajectory" was narrower
+  than the real one).
+- **`echo`** is worker-dispatched but unknown to the worker's dispatch table
+  (`main.rs`), so it yields a spurious per-step error under verify. Pre-existing,
+  unchanged.
+- **First diverging event** is still not named (§3, BL-026).
+
+**Research basis:** the record-and-serve mechanism is adapted from
+`docs/aetheris/research/activegraph-log-is-agent-2026-07.md` (arXiv:2605.21997), whose
+§3 framing — determinism as re-projection of recorded state rather than reproducibility
+of live execution (§1) — is exactly why serving a recorded network response is the
+correct semantics rather than a concession.
 
 ## 6. What Aetheris's fork is — and is not (divergence table)
 
diff --git a/docs/aetheris/runbook.md b/docs/aetheris/runbook.md
index 519cf95..c86e3a3 100644
--- a/docs/aetheris/runbook.md
+++ b/docs/aetheris/runbook.md
@@ -88,7 +88,7 @@ mix aetheris doctor
 mix aetheris run agents/codebase_qa.exs [--name label] [--model M] [--max-steps N]
 mix aetheris replay priv/runs/<run_id>/trajectory.json
 mix aetheris fork priv/runs/<run_id>/trajectory.json --step N [--name label]
-mix aetheris verify priv/runs/<run_id>/trajectory.json
+mix aetheris verify priv/runs/<run_id>/trajectory.json [--allow-effects]
 
 # Inspection
 mix aetheris inspect <run_id>
@@ -145,7 +145,7 @@ mix aetheris server [--port N]         # foreground; blocks until killed
 
 ## Waiting for a run to finish
 
-`mix aetheris run`, `fork`, `replay` and `verify` all block until the run reaches a
+`mix aetheris run`, `fork` and `replay` all block until the run reaches a
 terminal status (`done`, `failed`, `cancelled`). That wait is bounded by
 **inactivity**, not by total runtime: every 200 ms the CLI reads the run's status and
 its highest event seq, and the clock resets whenever either advances. A run that
@@ -156,8 +156,12 @@ non-terminal status emitting nothing for 5 minutes is given up on:
 Error: run run_abc123 stalled: no status or event activity for 300000ms (last status: running, last event seq: 47)
 ```
 
-`verify` prefixes the same message with `verification failed:`. Exit code is 1 in
-both cases.
+Exit code is 1.
+
+`verify` is **not** in that list as of BL-025: it no longer starts a run. It reads the
+recorded trajectory, re-executes the tool calls its effect class permits, and returns
+synchronously — so there is no status to wait on and no stall to bound. See "Verifying a
+run" below.
 
 This replaces an indefinite hang. Before BL-031 the loop had no bound at all, so any
 cause of a stuck non-terminal status hung the CLI — and any Rig `invoke` wrapping it —
@@ -165,6 +169,55 @@ forever, with nothing on stderr to say why. That is what amplified the BL-007 t4
 hang: a store `:busy` crash stopped statuses landing (cured separately at `059c92e`),
 and the unbounded loop turned it into a hang instead of an error.
 
+---
+
+## Verifying a run
+
+```bash
+mix aetheris verify priv/runs/<run_id>/trajectory.json [--allow-effects]
+```
+
+Verify re-executes the recorded tool calls in a fresh sandboxed worker and compares each
+result against the record — output by value equality, plus the filesystem `fs_hash`.
+
+**Not every tool is re-executed.** Each tool has an *effect class*
+(`Aetheris.Execution.EffectClass`); tools whose effects the verify sandbox does not
+contain are `:uncontained`, and their recorded result is **served** rather than
+re-performed. That covers `http_call`, every external MCP tool, and the in-process
+orb/agent tools. The filesystem built-ins, `run_command` and the local `git_*` family are
+`:contained` and are re-executed as before.
+
+Output distinguishes the two:
+
+```
+Verify: run_abc123
+Tools verified: 3  Served (not verified): 1  Failed: 0
+
+step 2  http_call  {"url":"https://api.example.com/v1/things"}  served (not re-executed)
+  recorded output: {"status":200,"body":"…"}
+  not re-executed (uncontained effect); no fs_hash claim
+```
+
+**A served step is not a verified one.** Nothing was compared, so it cannot fail — which
+is exactly why it is counted separately and never folded into `Tools verified`. Read a
+`Served` count as "this many steps were taken on the record's word".
+
+**Exit code** is 1 when any step diverged, 0 otherwise — via the escript (`./aetheris`).
+Note that `mix aetheris` currently discards exit codes for every command (BL-044), so use
+the escript when the code matters.
+
+### `--allow-effects`
+
+Restores the pre-BL-025 behaviour: `:uncontained` tools are re-executed too. **This
+re-issues real network and MCP effects** — a recorded `http_call` will open a real
+connection to the recorded host, and a recorded MCP tool call will be made again. Default
+is off. Use it only when you specifically intend to re-perform those effects.
+
+`docs/aetheris/determinism-contract.md` §5 is normative on the taxonomy and on what verify
+does and does not guarantee — including the limitation that `run_command`'s allowlist
+permits interpreters that can egress, so `:contained` means "contained against the
+allowlist", not "incapable of egress" (BL-042).
+
 ### Configuration
 
 ```elixir
diff --git a/lib/aetheris.ex b/lib/aetheris.ex
index 83ad41b..3214b31 100644
--- a/lib/aetheris.ex
+++ b/lib/aetheris.ex
@@ -93,6 +93,10 @@ defmodule Aetheris do
 
   @doc """
   Re-executes the tool calls from a recorded trajectory and verifies reproducibility.
+
+  Tools classified `:uncontained` by `Aetheris.Execution.EffectClass` are served
+  from the record rather than re-executed, unless `allow_effects: true` is passed.
+  See `Aetheris.Execution.Verifier.verify/2` for the full option list.
   """
   @spec verify_run(String.t(), keyword()) ::
           {:ok, VerifyReport.t()} | {:error, term()}
diff --git a/lib/aetheris/cli/commands/verify.ex b/lib/aetheris/cli/commands/verify.ex
index 435491c..06f0fce 100644
--- a/lib/aetheris/cli/commands/verify.ex
+++ b/lib/aetheris/cli/commands/verify.ex
@@ -1,26 +1,36 @@
 defmodule Aetheris.CLI.Commands.Verify do
   @moduledoc """
-  Implements `aetheris verify <trajectory.json>`.
+  Implements `aetheris verify <trajectory.json> [--allow-effects]`.
+
+  Routes through `Aetheris.verify_run/2`, which re-executes the recorded tool calls
+  and compares them against the record — the behaviour
+  `docs/aetheris/determinism-contract.md` §3 describes. Tools whose effects the
+  verify sandbox does not contain are served from the record rather than
+  re-executed; `--allow-effects` opts back in to re-executing them, which
+  re-issues real network and MCP effects.
   """
 
   alias Aetheris.CLI.Commands.RunHelpers
-  alias Aetheris.RunConfig
+  alias Aetheris.Execution.{Verifier, VerifyReport}
+
+  @switches [allow_effects: :boolean]
 
   @doc """
   Runs the CLI verify command.
+
+  Returns `{:error, _}` when any step diverged, so the process exit code reflects
+  the verdict rather than merely reporting that the command ran.
   """
   @spec run([String.t()], keyword()) :: {:ok, map()} | {:error, String.t()}
   def run(args, _global_opts) do
-    {opts, positional, _} = OptionParser.parse(args, strict: [])
+    {opts, positional, _invalid} = OptionParser.parse(args, strict: @switches)
 
     case positional do
       [path | _rest] ->
         with {:ok, run_id} <- RunHelpers.extract_run_id(path),
              {:ok, _trajectory} <- RunHelpers.load_trajectory(run_id),
-             :ok <- RunHelpers.ensure_started(),
-             {:ok, config} <- RunHelpers.lookup_run(run_id),
-             {:ok, new_id} <- start_verify(config, run_id, opts) do
-          await_verify(new_id)
+             :ok <- RunHelpers.ensure_started() do
+          verify_run(run_id, opts)
         end
 
       [] ->
@@ -28,31 +38,34 @@ defmodule Aetheris.CLI.Commands.Verify do
     end
   end
 
-  @spec await_verify(String.t()) :: {:ok, map()} | {:error, String.t()}
-  defp await_verify(run_id) do
-    case RunHelpers.await_run(run_id) do
-      {:ok, %{status: :done}} ->
-        {:ok, %{run_id: run_id, status: :done, verified: true}}
+  @spec verify_run(String.t(), keyword()) :: {:ok, map()} | {:error, String.t()}
+  defp verify_run(run_id, opts) do
+    allow_effects = Keyword.get(opts, :allow_effects, false)
 
-      {:error, reason} ->
-        {:error, "verification failed: #{reason}"}
+    case Aetheris.verify_run(run_id, allow_effects: allow_effects) do
+      {:ok, %VerifyReport{} = report} -> report_result(report)
+      {:error, :not_found} -> {:error, "no trajectory found for run #{run_id}"}
+      {:error, :sandbox_required} -> {:error, "no sandbox_path recorded for run #{run_id}"}
+      {:error, reason} -> {:error, "verification failed: #{inspect(reason)}"}
     end
   end
 
-  @spec start_verify(RunConfig.t(), String.t(), keyword()) ::
-          {:ok, String.t()} | {:error, String.t()}
-  defp start_verify(stored_config, original_run_id, _opts) do
-    verify_config = %RunConfig{
-      stored_config
-      | run_id: Aetheris.ID.generate(),
-        mode: :verify,
-        fork_from: original_run_id,
-        fork_step: nil
-    }
-
-    case Aetheris.start_run(verify_config) do
-      {:ok, run_id} -> {:ok, run_id}
-      {:error, reason} -> {:error, "failed to start verify run: #{inspect(reason)}"}
-    end
+  @spec report_result(VerifyReport.t()) :: {:ok, map()} | {:error, String.t()}
+  defp report_result(%VerifyReport{failed: failed} = report) when failed > 0 do
+    {:error,
+     "verify failed: #{failed} of #{length(report.steps)} steps diverged\n" <>
+       Verifier.to_report(report)}
+  end
+
+  defp report_result(%VerifyReport{} = report) do
+    {:ok,
+     %{
+       run_id: report.run_id,
+       status: :done,
+       verified: report.verified,
+       served: report.served,
+       failed: report.failed,
+       report: Verifier.to_report(report)
+     }}
   end
 end
diff --git a/lib/aetheris/cli/output/formatter.ex b/lib/aetheris/cli/output/formatter.ex
index 697f3fd..e1ea68f 100644
--- a/lib/aetheris/cli/output/formatter.ex
+++ b/lib/aetheris/cli/output/formatter.ex
@@ -97,6 +97,12 @@ defmodule Aetheris.CLI.Output.Formatter do
     report
   end
 
+  # `aetheris verify` — the rendered report already carries the verified/served/
+  # failed counts, so print it rather than the map that wraps it for --json.
+  defp format_human(%{report: report, verified: _verified, served: _served}) do
+    report
+  end
+
   defp format_human(%{entries: entries}) do
     Table.format(entries, [
       {:type, "Type"},
diff --git a/lib/aetheris/execution/tool_schema/registry.ex b/lib/aetheris/execution/tool_schema/registry.ex
index e5c7cde..e4369a2 100644
--- a/lib/aetheris/execution/tool_schema/registry.ex
+++ b/lib/aetheris/execution/tool_schema/registry.ex
@@ -300,6 +300,15 @@ defmodule Aetheris.Execution.ToolSchema.Registry do
     end
   end
 
+  @doc """
+  Returns every registered tool name.
+
+  The single enumeration of the built-in tool set; `Aetheris.Execution.EffectClass`
+  is asserted total over it rather than against a copied list.
+  """
+  @spec names() :: [String.t()]
+  def names, do: Map.keys(@schemas)
+
   @doc """
   Returns `ToolSchema` structs for the given list of tool names.
 
diff --git a/lib/aetheris/execution/verifier.ex b/lib/aetheris/execution/verifier.ex
index 0b1ca77..5840aa3 100644
--- a/lib/aetheris/execution/verifier.ex
+++ b/lib/aetheris/execution/verifier.ex
@@ -2,14 +2,26 @@ defmodule Aetheris.Execution.Verifier do
   @moduledoc """
   Re-executes the tool calls from a recorded trajectory and verifies that
   outputs and filesystem hashes match what was captured.
+
+  Tools whose effects the verify sandbox does not contain are **not** re-executed
+  by default. Their recorded result is *served* instead, and reported as served
+  rather than verified — see `Aetheris.Execution.EffectClass` and
+  `docs/aetheris/determinism-contract.md` §5. Pass `allow_effects: true` to
+  restore re-execution of everything; that re-issues real network and MCP effects.
   """
 
-  alias Aetheris.Execution.VerifyReport
+  alias Aetheris.Execution.{EffectClass, VerifyReport}
   alias Aetheris.Trajectory.{Event, File}
   alias Aetheris.Worker.Client
 
   @doc """
   Re-executes recorded tool calls for `run_id` and verifies their outputs.
+
+  ## Options
+
+    * `:sandbox_path` — overrides the sandbox path recorded in the trajectory meta.
+    * `:allow_effects` — when `true`, re-executes `:uncontained` tools as well.
+      Defaults to `false`, which serves their recorded result instead.
   """
   @spec verify(String.t(), keyword()) ::
           {:ok, VerifyReport.t()} | {:error, :not_found | :sandbox_required | term()}
@@ -34,6 +46,8 @@ defmodule Aetheris.Execution.Verifier do
       "\n",
       "Tools verified: ",
       Integer.to_string(report.verified),
+      "  Served (not verified): ",
+      Integer.to_string(report.served),
       "  Failed: ",
       Integer.to_string(report.failed),
       "\n\n",
@@ -42,11 +56,24 @@ defmodule Aetheris.Execution.Verifier do
     |> IO.iodata_to_binary()
   end
 
-  defp verify_tool_steps(run_id, sandbox_path, tool_steps) do
+  defp verify_tool_steps(run_id, sandbox_path, tool_steps, opts) do
+    allow_effects = Keyword.get(opts, :allow_effects, false)
+    planned = Enum.map(tool_steps, &plan_step(&1, allow_effects))
+
+    if Enum.any?(planned, fn {action, _step} -> action == :execute end) do
+      execute_planned_steps(run_id, sandbox_path, planned)
+    else
+      # Nothing to re-execute: do not start a worker at all. Serving every step
+      # must not spawn the process whose job is to re-enter the world.
+      {:ok, build_report(run_id, Enum.map(planned, fn {:serve, step} -> serve_step(step) end))}
+    end
+  end
+
+  defp execute_planned_steps(run_id, sandbox_path, planned) do
     case Client.start_link(run_id: "verify-#{run_id}", sandbox_path: sandbox_path) do
       {:ok, worker_pid} ->
         try do
-          step_results = Enum.map(tool_steps, &verify_step(worker_pid, &1))
+          step_results = Enum.map(planned, &run_planned_step(worker_pid, &1))
           {:ok, build_report(run_id, step_results)}
         after
           stop_worker(worker_pid)
@@ -57,6 +84,19 @@ defmodule Aetheris.Execution.Verifier do
     end
   end
 
+  defp plan_step({called_event, _result_event} = tool_step, allow_effects) do
+    class = EffectClass.from_tool_called(called_event.payload)
+
+    if class == :uncontained and not allow_effects do
+      {:serve, tool_step}
+    else
+      {:execute, tool_step}
+    end
+  end
+
+  defp run_planned_step(_worker_pid, {:serve, tool_step}), do: serve_step(tool_step)
+  defp run_planned_step(worker_pid, {:execute, tool_step}), do: verify_step(worker_pid, tool_step)
+
   defp verify_trajectory(run_id, trajectory, opts) do
     meta = Map.fetch!(trajectory, :meta)
     events = Map.fetch!(trajectory, :events)
@@ -68,14 +108,14 @@ defmodule Aetheris.Execution.Verifier do
       [] when events == [] ->
         case resolve_sandbox_path(meta, opts) do
           {:ok, _sandbox_path} ->
-            {:ok, %VerifyReport{run_id: run_id, verified: 0, failed: 0, steps: []}}
+            {:ok, %VerifyReport{run_id: run_id, verified: 0, served: 0, failed: 0, steps: []}}
 
           {:error, :sandbox_required} ->
             {:error, :sandbox_required}
         end
 
       [] ->
-        {:ok, %VerifyReport{run_id: run_id, verified: 0, failed: 0, steps: []}}
+        {:ok, %VerifyReport{run_id: run_id, verified: 0, served: 0, failed: 0, steps: []}}
 
       _tool_steps ->
         verify_with_sandbox(run_id, meta, opts, tool_steps)
@@ -85,7 +125,7 @@ defmodule Aetheris.Execution.Verifier do
   defp verify_with_sandbox(run_id, meta, opts, tool_steps) do
     case resolve_sandbox_path(meta, opts) do
       {:ok, sandbox_path} ->
-        verify_tool_steps(run_id, sandbox_path, tool_steps)
+        verify_tool_steps(run_id, sandbox_path, tool_steps, opts)
 
       {:error, :sandbox_required} ->
         {:error, :sandbox_required}
@@ -127,10 +167,44 @@ defmodule Aetheris.Execution.Verifier do
 
   defp do_pair_tool_events([_event | rest], acc), do: do_pair_tool_events(rest, acc)
 
+  # Record-and-serve: return the recorded result without touching the worker.
+  # No re-execution happened, so there is no output comparison and no fs_hash
+  # claim — the step is reported as served, never as verified.
+  defp serve_step({called_event, result_event}) do
+    %{
+      step: called_event.step,
+      tool_name: Map.fetch!(called_event.payload, "tool_name"),
+      tool_input: Map.fetch!(called_event.payload, "tool_input"),
+      recorded_output: recorded_result(result_event.payload),
+      actual_output: nil,
+      recorded_fs_hash: Map.get(result_event.payload, "fs_hash"),
+      actual_fs_hash: nil,
+      status: :served,
+      error: nil
+    }
+  end
+
+  # Successful worker and MCP results are written under "output"; in-process
+  # results and *every* recorded tool error are written under "result" with no
+  # "output" key at all (`Loop.record_tool_error/7`). Verify reflects the record,
+  # so a recorded failure is served exactly as recorded.
+  #
+  # Both the served and the re-executed paths read through here (BL-027). A hard
+  # `Map.fetch!("output")` on the re-execution path crashed verify on any
+  # trajectory containing a failed tool call, which is a routine shape — and one
+  # this ticket would otherwise have shipped as an operator-visible crash in the
+  # command it had just made real.
+  defp recorded_result(payload) do
+    case Map.fetch(payload, "output") do
+      {:ok, output} -> output
+      :error -> Map.get(payload, "result")
+    end
+  end
+
   defp verify_step(worker_pid, {called_event, result_event}) do
     tool_name = called_event.payload |> Map.fetch!("tool_name")
     tool_input = called_event.payload |> Map.fetch!("tool_input")
-    recorded_output = result_event.payload |> Map.fetch!("output")
+    recorded_output = recorded_result(result_event.payload)
     recorded_fs_hash = Map.get(result_event.payload, "fs_hash")
 
     case Client.execute(worker_pid, %{name: tool_name, input: tool_input}) do
@@ -174,17 +248,24 @@ defmodule Aetheris.Execution.Verifier do
   end
 
   defp build_report(run_id, step_results) do
-    verified =
-      Enum.count(step_results, fn step_result -> Map.fetch!(step_result, :status) == :verified end)
+    verified = count_status(step_results, :verified)
+    served = count_status(step_results, :served)
 
     %VerifyReport{
       run_id: run_id,
       verified: verified,
-      failed: Enum.count(step_results) - verified,
+      served: served,
+      # Served steps are neither verified nor failed — a served step cannot fail,
+      # which is exactly why it must not be counted as a pass either.
+      failed: Enum.count(step_results) - verified - served,
       steps: step_results
     }
   end
 
+  defp count_status(step_results, status) do
+    Enum.count(step_results, fn step_result -> Map.fetch!(step_result, :status) == status end)
+  end
+
   defp render_step(step_result) do
     input_json = Jason.encode!(Map.fetch!(step_result, :tool_input))
     status = Map.fetch!(step_result, :status)
@@ -204,10 +285,20 @@ defmodule Aetheris.Execution.Verifier do
   end
 
   defp render_status(:verified), do: "\u2713 verified"
+  defp render_status(:served), do: "served (not re-executed)"
   defp render_status(status), do: Atom.to_string(status)
 
   defp render_failure_details(_step_result, :verified), do: []
 
+  defp render_failure_details(step_result, :served) do
+    [
+      "  recorded output: ",
+      truncate(Map.get(step_result, :recorded_output)),
+      "\n",
+      "  not re-executed (uncontained effect); no fs_hash claim\n"
+    ]
+  end
+
   defp render_failure_details(step_result, :error) do
     [
       "  error: ",
diff --git a/lib/aetheris/execution/verify_report.ex b/lib/aetheris/execution/verify_report.ex
index d8355c0..fee662a 100644
--- a/lib/aetheris/execution/verify_report.ex
+++ b/lib/aetheris/execution/verify_report.ex
@@ -3,24 +3,33 @@ defmodule Aetheris.Execution.VerifyReport do
   Verification report for replayed tool execution checks.
   """
 
-  @enforce_keys [:run_id, :verified, :failed, :steps]
-  defstruct [:run_id, :verified, :failed, :steps]
+  @enforce_keys [:run_id, :verified, :served, :failed, :steps]
+  defstruct [:run_id, :verified, :served, :failed, :steps]
 
+  @typedoc """
+  Outcome of a single recorded tool step.
+
+  `:served` means the recorded result was returned **without re-executing the
+  tool** — see `Aetheris.Execution.EffectClass`. A served step is not a verified
+  step: nothing was compared, so it carries no `actual_output` and makes no
+  `fs_hash` claim.
+  """
   @type step_result :: %{
           step: non_neg_integer(),
           tool_name: String.t(),
           tool_input: map(),
-          recorded_output: String.t(),
+          recorded_output: String.t() | nil,
           actual_output: String.t() | nil,
           recorded_fs_hash: String.t() | nil,
           actual_fs_hash: String.t() | nil,
-          status: :verified | :output_mismatch | :hash_mismatch | :error,
+          status: :verified | :served | :output_mismatch | :hash_mismatch | :error,
           error: String.t() | nil
         }
 
   @type t :: %__MODULE__{
           run_id: String.t(),
           verified: non_neg_integer(),
+          served: non_neg_integer(),
           failed: non_neg_integer(),
           steps: [step_result()]
         }
diff --git a/test/aetheris/cli/commands/verify_test.exs b/test/aetheris/cli/commands/verify_test.exs
index d916a3b..02e4a3f 100644
--- a/test/aetheris/cli/commands/verify_test.exs
+++ b/test/aetheris/cli/commands/verify_test.exs
@@ -1,50 +1,113 @@
 defmodule Aetheris.CLI.Commands.VerifyTest do
+  @moduledoc """
+  The previous version of this file asserted `verified == true` over a run with
+  **zero tool calls**, against a command that returned that value unconditionally.
+  It passed whether or not verification worked — vacuous by the Silent-wrong-answer
+  rule. It is replaced here by a pass/fail pair over a real recorded tool call.
+  """
   use ExUnit.Case, async: false
 
-  import Aetheris.Test.RunHelpers
-
   alias Aetheris.CLI.Commands.Verify
-  alias Aetheris.RunConfig
+  alias Aetheris.CLI.Output.Formatter
+  alias Aetheris.Trajectory.{Event, File}
+
+  @timestamp DateTime.from_naive!(~N[2026-07-23 00:00:00], "Etc/UTC")
 
   setup do
     {:ok, _apps} = Application.ensure_all_started(:aetheris)
 
-    run_id = "verify-source-#{System.unique_integer([:positive])}"
-    config = base_config(run_id)
+    run_id = "verify-cli-#{System.unique_integer([:positive])}"
+    sandbox_path = Path.join("/tmp", run_id)
+    Elixir.File.mkdir_p!(sandbox_path)
+
+    on_exit(fn ->
+      Elixir.File.rm_rf!(Path.join(["priv", "runs", run_id]))
+      Elixir.File.rm_rf!(sandbox_path)
+    end)
+
+    %{run_id: run_id, sandbox_path: sandbox_path}
+  end
+
+  # NOTE: this pair re-executes a contained tool, so it needs the Rust worker and
+  # carries :requires_worker — which CI excludes (`ci.yml:64`). The pair is run
+  # locally with `--include requires_worker` and its output is quoted in the
+  # BL-025 packet. Naming that gap rather than leaving the tag to imply coverage.
+  @tag :requires_worker
+  test "a trajectory whose recorded output was tampered with fails, and exits non-zero", %{
+    run_id: run_id,
+    sandbox_path: sandbox_path
+  } do
+    Elixir.File.write!(Path.join(sandbox_path, "hello.txt"), "on disk")
+    path = write_trajectory(run_id, sandbox_path, "NOT what is on disk")
 
-    {:ok, ^run_id} = Aetheris.start_run(config)
-    assert_run_done(run_id)
+    assert {:error, message} = Verify.run([path], [])
+    assert message =~ "verify failed"
+    assert message =~ "1 of 1 steps diverged"
 
-    trajectory_path = Path.join(["priv", "runs", run_id, "trajectory.json"])
-    {:ok, trajectory_path: trajectory_path}
+    # The verdict reaches the exit code: Formatter.print/2 is what CLI.run/1
+    # hands to System.halt/1.
+    assert Formatter.print({:error, message}, :quiet) == 1
   end
 
-  test "verify completed run returns done with verified true", %{trajectory_path: path} do
+  @tag :requires_worker
+  test "a trajectory whose recorded output matches verifies, and exits zero", %{
+    run_id: run_id,
+    sandbox_path: sandbox_path
+  } do
+    content = "on disk"
+    Elixir.File.write!(Path.join(sandbox_path, "hello.txt"), content)
+    path = write_trajectory(run_id, sandbox_path, content)
+
     assert {:ok, result} = Verify.run([path], [])
-    assert :done == Map.fetch!(result, :status)
-    assert true == Map.fetch!(result, :verified)
+    assert Map.fetch!(result, :verified) == 1
+    assert Map.fetch!(result, :failed) == 0
+    assert Formatter.print({:ok, result}, :quiet) == 0
+  end
+
+  test "a verify with no tool calls reports zero verified, not a blanket pass", %{
+    run_id: run_id,
+    sandbox_path: sandbox_path
+  } do
+    events = [
+      event(run_id, 0, 0, :llm_called, %{"model" => "stub-v1"}),
+      event(run_id, 0, 1, :run_complete, %{"reason" => "max_steps_reached"})
+    ]
+
+    {:ok, path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+
+    assert {:ok, result} = Verify.run([path], [])
+    # The old assertion here was `verified == true`. Nothing was checked then and
+    # nothing is checked now — but the report no longer claims otherwise.
+    assert Map.fetch!(result, :verified) == 0
+    assert Map.fetch!(result, :served) == 0
+  end
+
+  defp write_trajectory(run_id, sandbox_path, recorded_output) do
+    events = [
+      event(run_id, 1, 0, :tool_called, %{
+        "tool_name" => "read_file",
+        "tool_input" => %{"path" => "hello.txt"}
+      }),
+      event(run_id, 1, 1, :tool_result, %{
+        "tool_name" => "read_file",
+        "output" => recorded_output,
+        "fs_hash" => nil
+      })
+    ]
+
+    {:ok, path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+    path
   end
 
-  defp base_config(run_id) do
-    %RunConfig{
+  defp event(run_id, step, seq, type, payload) do
+    %Event{
+      id: "#{run_id}-#{seq}",
       run_id: run_id,
-      mode: :record,
-      provider: "stub",
-      model: "stub-v1",
-      system_prompt: "verify test",
-      max_steps: 1,
-      stub_responses: [
-        {:ok,
-         %{
-           type: :text,
-           content: "done",
-           tool_name: nil,
-           tool_input: nil,
-           latency_ms: 0,
-           input_tokens: 5,
-           output_tokens: 3
-         }}
-      ]
+      step: step,
+      type: type,
+      payload: payload,
+      timestamp: @timestamp,
+      seq: seq
     }
   end
 end
diff --git a/test/aetheris/execution/verifier_test.exs b/test/aetheris/execution/verifier_test.exs
index 3cca115..bd19264 100644
--- a/test/aetheris/execution/verifier_test.exs
+++ b/test/aetheris/execution/verifier_test.exs
@@ -44,13 +44,16 @@ defmodule Aetheris.Execution.VerifierTest do
     ]
 
     assert {:ok, _path} = File.write(run_id, events, %{"sandbox_path" => "/tmp/unused"})
-    assert {:ok, %VerifyReport{verified: 0, failed: 0, steps: []}} = Verifier.verify(run_id)
+
+    assert {:ok, %VerifyReport{verified: 0, served: 0, failed: 0, steps: []}} =
+             Verifier.verify(run_id)
   end
 
   test "to_report/1 includes the run_id and verified marker" do
     report = %VerifyReport{
       run_id: "run-abc",
       verified: 1,
+      served: 0,
       failed: 0,
       steps: [
         %{
@@ -120,6 +123,45 @@ defmodule Aetheris.Execution.VerifierTest do
            ] = report.steps
   end
 
+  @tag :requires_worker
+  test "a recorded tool FAILURE on a contained tool verifies without crashing", %{
+    run_id: run_id,
+    sandbox_path: sandbox_path
+  } do
+    # Every recorded tool error is written under "result" with "is_error" and no
+    # "output" key at all (Loop.record_tool_error/7) — including for contained,
+    # worker-dispatched tools. The re-execution path read "output" with a hard
+    # fetch, so a routine failed-tool trajectory took verify down with a KeyError
+    # (BL-027, whose stated trigger of "a multi-agent/orb trajectory" was too
+    # narrow). Record-and-serve sidestepped it for uncontained tools only; this
+    # is the contained face.
+    Elixir.File.mkdir_p!(sandbox_path)
+    Elixir.File.write!(Path.join(sandbox_path, "hello.txt"), "on disk")
+
+    events = [
+      event(run_id, 1, 0, :tool_called, %{
+        "tool_name" => "read_file",
+        "tool_input" => %{"path" => "hello.txt"}
+      }),
+      event(run_id, 1, 1, :tool_result, %{
+        "tool_name" => "read_file",
+        "result" => "Error: :enoent",
+        "is_error" => true
+      })
+    ]
+
+    assert {:ok, _path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+
+    assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)
+
+    # The recorded failure is read, not fetched-and-crashed, and the step is
+    # reported as the genuine divergence it is: the record failed, the
+    # re-execution succeeded.
+    assert report.failed == 1
+    assert report.verified == 0
+    assert [%{status: :output_mismatch, recorded_output: "Error: :enoent"}] = report.steps
+  end
+
   defp event(run_id, step, seq, type, payload) do
     %Event{
       id: "#{run_id}-#{seq}",

--- NEW FILES (untracked) ---

=== lib/aetheris/execution/effect_class.ex ===
defmodule Aetheris.Execution.EffectClass do
  @moduledoc """
  The single source of truth for a tool's *effect class* — how a re-execution of
  that tool relates to the verify containment boundary.

  Verify re-executes recorded tool calls in a fresh worker. That worker confines
  the **filesystem only**: it creates user and mount namespaces but no network
  namespace (`native/aetheris_worker/src/sandbox.rs`), so a tool whose effect is
  network egress is not contained by it. This module declares which tools those
  are, so `Aetheris.Execution.Verifier` can serve their recorded result instead of
  re-performing the effect.

  ## The three classes

    * `:uncontained` — the tool's **purpose is to reach outside** the verify
      containment boundary, so serving the recorded result is the semantically
      correct thing to do. Two families: worker-native network tools (`http_call`)
      and external MCP tools; plus the in-process orb/agent tools, which run in the
      BEAM and are therefore outside the worker sandbox altogether (`spawn_agent`
      can start a sub-agent that issues live model calls).

    * `:contained` — contained **against the exec-server allowlist**. This
      explicitly does **not** mean "incapable of egress": the allowlist
      (`native/aetheris_exec_server/src/runner.rs`) blocks `curl`/`wget` but
      permits `python3`, `node`, `npm`, `mix`, `cargo` and `git`, every one of
      which can open a socket, and some of which (`npm install`, `mix deps.get`)
      egress by design. That residual is *incidental* egress — a property of some
      invocations rather than of the tool — and the correct defence for it is
      capability-shaped containment at the sandbox layer, not record-and-serve.
      Re-executing these is the point of verify, so they are re-executed.

    * `:pure` — effect-free.

  ## Why this is not keyed on name alone

  MCP tool names are discovered at runtime from the server's `tools/list`
  (`Aetheris.Execution.Loop`), so no static name map can enumerate them. The
  recorded `:tool_called` event does carry the discriminator — `"source"` and
  `"server_id"` — so classification reads the source when the name is unknown.

  The trap this avoids: the internal exec server routes `run_command` and the
  `git_*` family with `source: :mcp, server_id: "aetheris_exec"`. Keying on
  `source` alone would misclassify that entire *contained* family as uncontained,
  which would serve them instead of verifying them — the opposite of the mistake
  this module exists to prevent, and just as wrong.

  Adding a tool without classifying it here fails
  `Aetheris.Execution.EffectClassTest`, which mechanizes the tripwire recorded in
  `docs/aetheris/determinism-contract.md` §5.
  """

  @type t :: :pure | :contained | :uncontained
  @type source :: :builtin | {:mcp, String.t()}

  @exec_server_id "aetheris_exec"

  # Worker-dispatched, filesystem-confined by the verify sandbox.
  @contained_tools ~w[
    read_file list_dir write_file
    run_command
    git_status git_diff git_add git_commit git_diff_staged git_log git_show
    git_checkout git_cherry_pick git_cherry_pick_control
  ]

  # In-process (BEAM-side) tools: never dispatched to the worker, therefore never
  # inside the sandbox. `spawn_agent` can start a run that makes live model calls.
  @in_process_uncontained_tools ~w[
    spawn_agent wait_for_all wait_for_event ask_human
    send_message broadcast_message read_blackboard write_blackboard
  ]

  # Worker-native tools whose purpose is network egress.
  @network_tools ~w[http_call]

  @pure_tools ~w[echo]

  @classes Map.new(
             Enum.map(@pure_tools, &{&1, :pure}) ++
               Enum.map(@contained_tools, &{&1, :contained}) ++
               Enum.map(@in_process_uncontained_tools, &{&1, :uncontained}) ++
               Enum.map(@network_tools, &{&1, :uncontained})
           )

  @doc """
  Returns the effect class for `tool_name` called via `source`.

  A known name always wins, so `run_command` stays `:contained` even though the
  internal exec server routes it with `source: {:mcp, "aetheris_exec"}`.

  An unknown name is `:uncontained` — fail-safe, since an unclassified tool must
  never be re-executed by default. `known_tools/0` plus the completeness test are
  what keep that fallback from silently absorbing a newly added built-in.
  """
  @spec classify(String.t(), source()) :: t()
  def classify(tool_name, source \\ :builtin) when is_binary(tool_name) do
    case Map.fetch(@classes, tool_name) do
      {:ok, class} -> class
      :error -> classify_unknown(source)
    end
  end

  @doc """
  Returns the effect class for a recorded `:tool_called` event payload.

  Reads `"tool_name"`, and `"source"`/`"server_id"` when present — the fields
  written by the execution loop when a call is routed through an MCP server.
  """
  @spec from_tool_called(map()) :: t()
  def from_tool_called(payload) when is_map(payload) do
    payload
    |> Map.fetch!("tool_name")
    |> classify(source_from_payload(payload))
  end

  @doc """
  Returns every tool name carrying an explicit classification.

  This is the domain the completeness test asserts against; it is deliberately the
  only enumeration of that domain.
  """
  @spec known_tools() :: [String.t()]
  def known_tools, do: Map.keys(@classes)

  @doc """
  Returns the `server_id` of the internal exec server.

  Exposed so callers and tests name the contained-MCP discriminator once.
  """
  @spec exec_server_id() :: String.t()
  def exec_server_id, do: @exec_server_id

  @spec classify_unknown(source()) :: t()
  defp classify_unknown({:mcp, @exec_server_id}), do: :contained
  defp classify_unknown({:mcp, _server_id}), do: :uncontained
  defp classify_unknown(:builtin), do: :uncontained

  @spec source_from_payload(map()) :: source()
  defp source_from_payload(payload) do
    case Map.get(payload, "source") do
      "mcp" -> {:mcp, Map.get(payload, "server_id", "")}
      _other -> :builtin
    end
  end
end

=== test/aetheris/execution/effect_class_test.exs ===
defmodule Aetheris.Execution.EffectClassTest do
  @moduledoc """
  Mechanizes the tripwire recorded in `docs/aetheris/determinism-contract.md` §5:
  a tool cannot be added to the harness without being classified, so a future
  networked tool cannot be silently re-executed under verify.

  Before BL-025 that tripwire was prose ("before any further uncontained tool is
  added, this section MUST be revisited"). Prose has no executor; this file does.
  """
  use ExUnit.Case, async: true

  alias Aetheris.Execution.EffectClass
  alias Aetheris.Execution.ToolSchema.Registry

  describe "completeness over the tool set" do
    test "every registry tool name is classified" do
      unclassified = Registry.names() -- EffectClass.known_tools()

      assert unclassified == [],
             "unclassified registry tools: #{inspect(unclassified)}. " <>
               "Add them to Aetheris.Execution.EffectClass and revisit " <>
               "determinism-contract.md §5 if any is uncontained."
    end

    test "every in-process tool module is classified" do
      unclassified = in_process_tool_names() -- EffectClass.known_tools()

      assert unclassified == [],
             "unclassified in-process tools: #{inspect(unclassified)}"
    end

    test "the classified domain contains no name that no longer exists" do
      live_names = Registry.names() ++ in_process_tool_names()
      ghosts = EffectClass.known_tools() -- live_names

      assert ghosts == [], "classified but absent from the harness: #{inspect(ghosts)}"
    end
  end

  describe "classify/2" do
    test "http_call is uncontained — its purpose is network egress" do
      assert EffectClass.classify("http_call") == :uncontained
    end

    test "an unknown tool from an external MCP server is uncontained" do
      assert EffectClass.classify("search_the_web", {:mcp, "some-external-server"}) ==
               :uncontained
    end

    test "an unknown tool with no source is uncontained — the fail-safe default" do
      assert EffectClass.classify("a_tool_added_tomorrow") == :uncontained
    end

    test "run_command stays contained despite being routed with source: :mcp" do
      # The internal exec server routes run_command and the git_* family as MCP
      # calls. Keying on source alone would serve this whole contained family
      # instead of verifying it.
      assert EffectClass.classify("run_command", {:mcp, EffectClass.exec_server_id()}) ==
               :contained

      assert EffectClass.classify("git_commit", {:mcp, EffectClass.exec_server_id()}) ==
               :contained
    end

    test "the filesystem built-ins are contained" do
      for name <- ~w[read_file list_dir write_file] do
        assert EffectClass.classify(name) == :contained
      end
    end

    test "in-process orb tools are uncontained — they run outside the worker sandbox" do
      for name <- ~w[spawn_agent send_message write_blackboard wait_for_event] do
        assert EffectClass.classify(name) == :uncontained
      end
    end

    test "echo is pure" do
      assert EffectClass.classify("echo") == :pure
    end
  end

  describe "from_tool_called/1" do
    test "reads the MCP source recorded on the event payload" do
      payload = %{
        "tool_name" => "fetch_issue",
        "tool_input" => %{},
        "source" => "mcp",
        "server_id" => "github"
      }

      assert EffectClass.from_tool_called(payload) == :uncontained
    end

    test "an exec-server payload resolves to the contained class" do
      payload = %{
        "tool_name" => "run_command",
        "tool_input" => %{},
        "source" => "mcp",
        "server_id" => EffectClass.exec_server_id()
      }

      assert EffectClass.from_tool_called(payload) == :contained
    end

    test "a payload with no source is a built-in call" do
      payload = %{"tool_name" => "read_file", "tool_input" => %{}}

      assert EffectClass.from_tool_called(payload) == :contained
    end
  end

  # Discovered rather than listed: a hardcoded list here would be the second copy
  # that EffectClass exists to prevent, and would go stale silently.
  defp in_process_tool_names do
    {:ok, modules} = :application.get_key(:aetheris, :modules)

    modules
    |> Enum.filter(&in_process_tool_module?/1)
    |> Enum.map(& &1.name())
  end

  defp in_process_tool_module?(module) do
    module
    |> Module.split()
    |> Enum.take(3) == ["Aetheris", "Execution", "Tool"] and
      Code.ensure_loaded?(module) and
      function_exported?(module, :name, 0)
  end
end

=== test/aetheris/execution/verify_effects_test.exs ===
defmodule Aetheris.Execution.VerifyEffectsTest do
  @moduledoc """
  BL-025 red-first test: verify must not re-perform an uncontained effect.

  Hermetic — no real external egress. A localhost listener counts inbound
  connections; the fabricated trajectory's recorded `http_call` targets it.
  The load-bearing assertion is the connection count, not the exit status:
  a verify that "succeeded" while re-issuing the call has failed this test.
  """
  use ExUnit.Case, async: false

  alias Aetheris.Execution.{Verifier, VerifyReport}
  alias Aetheris.Trajectory.{Event, File}

  @timestamp DateTime.from_naive!(~N[2026-07-23 00:00:00], "Etc/UTC")
  @recorded_output ~s({"status":200,"body":"recorded-not-live"})

  setup do
    run_id = "test-verify-effects-#{System.unique_integer([:positive])}"
    sandbox_path = Path.join("/tmp", run_id)
    Elixir.File.mkdir_p!(sandbox_path)

    listener = start_counting_listener()

    on_exit(fn ->
      stop_counting_listener(listener)
      Elixir.File.rm_rf!(Path.join(["priv", "runs", run_id]))
      Elixir.File.rm_rf!(sandbox_path)
    end)

    %{run_id: run_id, sandbox_path: sandbox_path, listener: listener}
  end

  test "default verify serves the recorded http_call and opens no connection", context do
    %{run_id: run_id, sandbox_path: sandbox_path, listener: listener} = context
    write_http_call_trajectory(run_id, sandbox_path, listener.port)

    assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)

    # Load-bearing: the network was never touched.
    assert connection_count(listener) == 0

    # Served is not verified: it must not inflate the verified tally.
    assert report.served == 1
    assert report.verified == 0
    assert report.failed == 0

    assert [step_result] = report.steps
    assert Map.fetch!(step_result, :status) == :served
    assert Map.fetch!(step_result, :recorded_output) == @recorded_output
    # No re-execution happened, so no actual output and no fs_hash claim.
    assert Map.get(step_result, :actual_output) == nil
    assert Map.get(step_result, :actual_fs_hash) == nil

    rendered = Verifier.to_report(report)
    assert rendered =~ "Served (not verified): 1"
    assert rendered =~ "served (not re-executed)"
  end

  test "a recorded http_call failure is served verbatim, not improved on", context do
    %{run_id: run_id, sandbox_path: sandbox_path, listener: listener} = context

    # A failed tool call records under "result" with is_error — there is no
    # "output" key at all (loop.ex record_tool_error/7).
    events = [
      event(run_id, 1, 0, :tool_called, %{
        "tool_name" => "http_call",
        "tool_input" => %{"url" => probe_url(listener.port)}
      }),
      event(run_id, 1, 1, :tool_result, %{
        "tool_name" => "http_call",
        "result" => "Error: :timeout",
        "is_error" => true
      })
    ]

    assert {:ok, _path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
    assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)

    assert connection_count(listener) == 0
    assert report.served == 1
    assert [%{status: :served, recorded_output: "Error: :timeout"}] = report.steps
  end

  @tag :requires_worker
  test "--allow-effects re-executes the http_call and the connection returns", context do
    %{run_id: run_id, sandbox_path: sandbox_path, listener: listener} = context
    write_http_call_trajectory(run_id, sandbox_path, listener.port)

    # The verify worker is started with start_link, so a worker that dies takes
    # the caller with it. It does die here — see the assertion note below.
    Process.flag(:trap_exit, true)

    assert {:ok, %VerifyReport{} = report} =
             Verifier.verify(run_id, sandbox_path: sandbox_path, allow_effects: true)

    # Load-bearing: the opt-in path lives — a real TCP connection reached the
    # target host, which is precisely the effect the default path prevents.
    #
    # It stops there rather than completing the request: the worker's seccomp
    # allowlist omits `setsockopt` (x86_64 nr 54), so ureq is SIGSYS-killed after
    # connect() and before the request is written. That truncation is a harness
    # defect, not containment by design, and it is not what makes verify safe —
    # the count below is 1, not 0. Asserting the connection rather than a
    # completed HTTP exchange keeps this test honest about what was demonstrated.
    assert connection_count(listener) >= 1

    assert report.served == 0
    assert [step_result] = report.steps
    assert Map.fetch!(step_result, :status) != :served
  end

  defp write_http_call_trajectory(run_id, sandbox_path, port) do
    events = [
      event(run_id, 1, 0, :tool_called, %{
        "tool_name" => "http_call",
        "tool_input" => %{"url" => probe_url(port), "method" => "GET"}
      }),
      event(run_id, 1, 1, :tool_result, %{
        "tool_name" => "http_call",
        "output" => @recorded_output,
        "fs_hash" => nil
      })
    ]

    assert {:ok, _path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
  end

  defp probe_url(port), do: "http://127.0.0.1:#{port}/bl-025-egress-probe"

  defp event(run_id, step, seq, type, payload) do
    %Event{
      id: "#{run_id}-#{seq}",
      run_id: run_id,
      step: step,
      type: type,
      payload: payload,
      timestamp: @timestamp,
      seq: seq
    }
  end

  # --- counting listener -----------------------------------------------------

  defp start_counting_listener do
    {:ok, listen_socket} =
      :gen_tcp.listen(0, [:binary, packet: :raw, active: false, reuseaddr: true])

    {:ok, port} = :inet.port(listen_socket)
    {:ok, counter} = Agent.start(fn -> 0 end)
    acceptor = spawn(fn -> accept_loop(listen_socket, counter) end)

    %{port: port, counter: counter, listen_socket: listen_socket, acceptor: acceptor}
  end

  defp accept_loop(listen_socket, counter) do
    case :gen_tcp.accept(listen_socket) do
      {:ok, socket} ->
        Agent.update(counter, &(&1 + 1))
        :gen_tcp.send(socket, "HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nlive")
        :gen_tcp.close(socket)
        accept_loop(listen_socket, counter)

      {:error, _reason} ->
        :ok
    end
  end

  defp connection_count(listener) do
    Agent.get(Map.fetch!(listener, :counter), & &1)
  end

  defp stop_counting_listener(listener) do
    :gen_tcp.close(Map.fetch!(listener, :listen_socket))
    Process.exit(Map.fetch!(listener, :acceptor), :kill)
    Agent.stop(Map.fetch!(listener, :counter))
  end
end
`````

</details>

---

### 6. Diff — agents (`aetheris-agents/`)

```
$ git diff --stat  (aetheris-agents)
 docs/backlog-2026-06.md | 297 +++++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 293 insertions(+), 4 deletions(-)

?? docs/reviews/bl-025-contract-draft.md
```

<details><summary>Full backlog diff (complete, untruncated)</summary>

`````diff
diff --git a/docs/backlog-2026-06.md b/docs/backlog-2026-06.md
index 3e02adf..0f6bcf1 100644
--- a/docs/backlog-2026-06.md
+++ b/docs/backlog-2026-06.md
@@ -340,7 +340,48 @@ provenance shapes, and has an e2e covering the null-`fork_step` case.
 ---
 
 ### BL-025 — Verify: effect classes / record-and-serve for effectful tools (#TBD)
-**Size:** M · **Priority:** medium
+**Size:** M · **Priority:** medium — **DONE 2026-07-23**
+
+**Landed.** `Aetheris.Execution.EffectClass` declares `:pure` / `:contained` /
+`:uncontained` as the single source of truth; `Verifier` record-and-serves `:uncontained`
+tools by default and reports them **served, not verified** (excluded from the verified
+tally); `aetheris verify <traj> --allow-effects` opts back in. Proven by a hermetic
+localhost listener: **0 inbound connections** under default verify, **1** under
+`--allow-effects`. A completeness test asserts the classifier is total over
+`Registry.names/0` and every in-process tool module, mutation-checked.
+
+**Scope grew, by human decision in-cycle (rev 2, 2026-07-22).** `aetheris verify` never
+reached `Verifier` at all — `Commands.Verify` started a fresh **live** run
+(`mode: :verify`) and returned `verified: true` unconditionally. The CLI was rewired to
+`Aetheris.verify_run/2` and now returns the real verdict with a failure-reflecting exit
+code; the vacuous `verified == true` test was replaced with a mutation-checked pass/fail
+pair.
+
+**Contract edits (§8, human-approved in-cycle):** determinism-contract **§3** (verify row;
+plus a new paragraph separating `verify` the command from `RunConfig mode: :verify`) and
+**§5** (full rewrite: taxonomy, record-and-serve, served-not-verified, mechanized
+tripwire). Draft: `docs/reviews/bl-025-contract-draft.md`.
+
+**MCP scope note:** the MCP *family* is classified `:uncontained`, not `http_call` alone.
+Because MCP tool names are discovered at runtime, classification falls back to the recorded
+`"source"`/`"server_id"` — with `server_id == "aetheris_exec"` held `:contained`, since the
+internal exec server routes `run_command` and all eleven `git_*` as MCP calls.
+
+**BL-027 folded in (human call, 2026-07-23).** `verify_step/2` now reads the recorded result
+through the same `"output"`-else-`"result"` fallback as the served path. Without it, BL-025
+would have shipped the crash as the behaviour of the command it had just made real: any
+trajectory with a failed contained tool call took verify down. See BL-027 for the red-first
+evidence; the payload-key *convention* residue is BL-046.
+
+**Deliberately not closed here:** capability-level egress safety. `run_command` stays
+`:contained` (rev 3) and its allowlisted interpreters can still egress — named as a §5
+limitation, tracked by **BL-042**. Follow-ups filed: BL-042, BL-043 (`http_call` is
+SIGSYS-killed in every mode), BL-044 (`mix aetheris` discards exit codes), BL-045
+(`mode: :verify` misnomer), BL-046 (payload-key convention).
+
+---
+
+**Original row:**
 
 `verify` **re-executes** every recorded tool call against a live worker
 (`verifier.ex:136`, `Client.execute/2`). For a pure tool that is the point; for an
@@ -381,7 +422,40 @@ and the trigger condition above has actually occurred.
 ---
 
 ### BL-027 — Verify: `KeyError` crash on paired in-process tools (#TBD)
-**Size:** S · **Priority:** medium — **PARKED ON TRIGGER**
+**Size:** S · **Priority:** medium — **DONE 2026-07-23 (folded into BL-025)**
+
+**Closed.** `Verifier.verify_step/2` now reads the recorded result through the same
+`recorded_result/1` fallback (`"output"`, else `"result"`) that the record-and-serve path
+uses — one reader, both paths. Red-first evidence, on a trajectory whose recorded
+`read_file` **failed**:
+
+```
+** (KeyError) key "output" not found in:
+   %{"is_error" => true, "result" => "Error: :enoent", "tool_name" => "read_file"}
+   verifier.ex:201  Aetheris.Execution.Verifier.verify_step/2
+→ after the fix: 6 tests, 0 failures; the step reports :output_mismatch with
+  recorded_output "Error: :enoent" — a genuine divergence, legibly, instead of a crash.
+```
+
+**Why it was unparked rather than left on its trigger.** The stated trigger — a
+multi-agent/orb trajectory — was **too narrow**, and the row's in-process framing was the
+reason. `Loop.record_tool_error/7` writes *every* recorded tool failure under `"result"`
+with `"is_error"` and no `"output"` key, including for **contained, worker-dispatched**
+tools. So a single failed `read_file` or `run_command` — a routine shape, needing no orb —
+crashed verify. BL-025 made `aetheris verify` actually route through `Verifier`, which would
+have shipped that crash as the operator-visible behaviour of the command it had just made
+real. Human call, 2026-07-23: fold the fix in rather than release that state.
+
+BL-025's record-and-serve independently removed the *in-process* face (those tools are
+`:uncontained` and no longer dispatched), so the residual this fix closes is precisely the
+contained-tool face the original row did not describe.
+
+**Not closed here — tracked as BL-046:** the payload-key *convention* itself, shared with
+BL-028. This row fixed the reader; it did not unify the writers.
+
+---
+
+**Original row:**
 
 **Same trigger and ratification as BL-026: activates on the first `verify` run
 against a multi-agent / orb trajectory.** Human-ratified 2026-07-19. Recorded, not
@@ -398,6 +472,28 @@ The tools that hit this are exactly the orb/coordination ones —
 is a multi-agent/orb trajectory: that is the first trajectory shape that can
 contain them, and the crash is unreachable until one exists.
 
+**Trigger correction (BL-025, 2026-07-23) — the stated trigger is too narrow, and the
+in-process framing is now stale in both directions.** Two changes:
+
+1. **The crash never needed an orb trajectory.** `Loop.record_tool_error/7` writes *every*
+   recorded tool failure — including worker-dispatched, contained tools — under `"result"`
+   with `"is_error" => true` and **no `"output"` key at all**. So a trajectory containing a
+   single failed `read_file` or `run_command` reaches the same `Map.fetch!` and crashes
+   verify. Demonstrated at BL-025 against a recorded `http_call` failure before that tool
+   was reclassified:
+   `** (KeyError) key "output" not found in: %{"is_error" => true, "result" => "Error: :timeout", …}`
+   at `verifier.ex:133`. The parked-on-trigger status understates reachability accordingly.
+
+2. **BL-025 sidesteps the in-process case without fixing this row.** The in-process tools are
+   now classified `:uncontained` and record-and-served, so verify no longer dispatches them
+   and the `"result"`-key crash is unreachable *for them*. The residual — and the real scope
+   of this row now — is a **`:contained`** tool whose recorded result is an error. Do not
+   read BL-025 as having closed this; the hard fetch on the re-execution path is untouched.
+
+Fix shape unchanged: read the recorded result with a fallback (`"output"`, else `"result"`),
+as `Verifier.serve_step/1` already does on the served path — the two paths should share one
+reader.
+
 Note the shared root cause with BL-028: two independent consumers of recorded tool
 results each assume `"output"` while a family of writers uses `"result"`. Worth
 fixing as one payload-key convention rather than two point patches.
@@ -1639,6 +1735,194 @@ a reason.
 
 ---
 
+### BL-046 — Tool-result payload key is a convention, not a contract: `"output"` vs `"result"` (#TBD)
+**Size:** S · **Priority:** low · **Section:** Harness (aetheris/)
+
+Three tickets have now fixed the *same root cause* on the read side, one reader at a time:
+
+| Ticket | Reader fixed | Failure shape it produced |
+|---|---|---|
+| BL-028 (`9b2b102`) | `Fork.event_to_messages/1` — `Map.get(payload, "output", "")` | **Silent empty** tool messages; fork proceeds from a wrong transcript |
+| BL-025 | `Verifier.serve_step/1` (new path) | — (written correctly from the start) |
+| BL-027 (folded into BL-025) | `Verifier.verify_step/2` — `Map.fetch!(payload, "output")` | **Crash**; verify dies on any failed-tool trajectory |
+
+The writers remain unreconciled. `Loop` emits `:tool_result` payloads under **`"output"`**
+for worker and MCP dispatch, **`"result"`** for in-process tools, and **`"result"` +
+`"is_error"`** for every tool error regardless of dispatch route (`record_tool_error/7`).
+Nothing declares this; each new reader must rediscover it, and the two failure shapes above
+are what rediscovery costs. A fourth reader will be written eventually.
+
+Note the two fixes differ in a way worth preserving: BL-028's read-side fallback also
+normalizes (nil → `""`, non-binary → JSON) per contract §2's string invariant; BL-025's does
+not, because verify must reflect the record verbatim rather than improve on it. So "one
+shared helper" is not automatically the right answer — the *convention* needs declaring even
+if the readers stay separate.
+
+**Done when:** the `:tool_result` payload contract is stated in one place (a `@type` plus
+docstring on the writer side, or a documented accessor), the existing readers are pointed at
+it, and adding a writer that invents a third key is caught — by a test or by there being
+only one way to write the payload. Decide explicitly whether the readers share code or only
+share the convention.
+
+`Source: BL-028 (2026-07-21), BL-027/BL-025 (2026-07-23) — same root cause, third reader.`
+
+---
+
+### BL-042 — Capability-shaped containment for the verify worker (`CLONE_NEWNET`) (#TBD)
+**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)
+
+BL-025 classifies `run_command` `:contained` and record-and-serves only the purpose-network
+tools (`http_call`, MCP). But the verify sandbox confines filesystem only — no network
+namespace (`CLONE_NEWNET` absent, `sandbox.rs:144`), seccomp permits `connect`
+(`sandbox.rs:265-278`) — and the exec allowlist (`aetheris_exec_server/src/runner.rs:7-24`)
+permits `python3`/`node`/`npm`/`mix`/`cargo`/`git`, every one socket-capable
+(`npm install` / `mix deps.get` egress by design). So verify re-executing a `run_command`
+that ran a networked script **egresses**, regardless of BL-025's record-and-serve. The
+containment is command-shaped, not capability-shaped (found at BL-025, HEAD `d567d75`).
+
+Fix: add `CLONE_NEWNET` to the verify worker's namespace set so re-execution cannot egress
+regardless of allowlist — capability-shaped containment. This makes BL-025's record-and-serve
+**defence-in-depth** for the purpose-network tools rather than the sole (and partial) defence.
+
+**Builds on BL-025, does not race it.** Under a network namespace, `http_call`/MCP would
+*fail* (no network) rather than egress — so record-and-serve (BL-025) must be landed first,
+or those tools break under verify. Sequence BL-042 after BL-025.
+
+**Adjacent — decide, don't assume:** a networked `run_command` re-executed under a netns will
+*diverge* (the script fails/times out) rather than reproduce. That is verify honestly
+reporting a non-reproducible (network-dependent) step, but the divergence message must read
+as "network unavailable under verify," not a spurious content mismatch — specify the surfaced
+error. Do not silently skip it.
+
+**Interacts with BL-043.** BL-043 (missing `setsockopt`) currently truncates worker egress at
+`connect(2)` by accident. Fixing BL-043 restores full egress and makes this row's exposure
+larger, not smaller; fixing this row makes BL-043's repair safe. Neither is a substitute for
+the other — do not let BL-043's accidental truncation be read as containment.
+
+**Done when:** the verify worker runs under `CLONE_NEWNET`; a `run_command` recorded doing
+network egress cannot egress during verify (hermetic listener: 0 hits) and its divergence is
+reported legibly; `http_call`/MCP remain served (BL-025) and do not fail under the netns;
+§5's egress-safety statement upgrades from partial to capability-complete, human-approved
+in-cycle (§8).
+
+`Source: BL-025 execution, run_command allowlist finding, HEAD d567d75, 2026-07-22.`
+
+---
+
+### BL-043 — `http_call` is killed by seccomp (SIGSYS) in every mode: `setsockopt` missing from the allowlist (#TBD)
+**Size:** S · **Priority:** medium · **Section:** Harness (aetheris/)
+
+`http_call` does not work at all — not in verify, not in a normal **record** run. The worker's
+seccomp allowlist (`native/aetheris_worker/src/sandbox.rs`) carries a section explicitly
+headed *"Network (http_call + MCP stdio)"* listing `socket`, `connect`, `sendto`, `recvfrom`,
+`sendmsg`, `recvmsg`, `bind`, `listen`, `accept4`, `poll`, `epoll_*` — but **omits
+`setsockopt`** (x86_64 syscall 54), which `ureq` calls to set timeouts immediately after
+`connect(2)`. The filter's default action is `KillProcess`, so the worker dies of SIGSYS.
+
+**Demonstrated at BL-025** (hermetic localhost listener + kernel audit, 2026-07-23):
+
+```
+audit: type=1326 … comm="aetheris_worker" … sig=31 arch=c000003e syscall=54 code=0x80000000
+worker exit status 159   (128 + 31 = SIGSYS)
+Worker.Client.execute → {:error, "worker_crashed"}
+INBOUND TCP CONNECTIONS TO LISTENER: 1
+```
+
+So the TCP connection **does** land; only the HTTP request is never written.
+
+**Do not read this as containment.** It is an unintended truncation of a real egress path,
+and the "Network" heading shows egress was the intent. Two consequences:
+
+- **`http_call` is unusable.** Any agent using it gets a crashed worker, not a response. That
+  the defect went unnoticed suggests the tool has no live users — worth confirming before
+  choosing a fix direction.
+- **It is load-bearing by accident.** Adding `setsockopt` restores full egress instantly,
+  which widens BL-042's exposure. Sequence: BL-025 (landed) → BL-042 (netns) → this row, or
+  accept the widened window knowingly.
+
+**Second defect, same path:** `Verifier` starts the worker with `Client.start_link`, so a
+worker that dies takes the **caller** with it (`{:worker_crashed, 159}` propagates as an exit
+signal). A library function should not kill its caller because a sandboxed tool crashed; the
+BL-025 test traps exits to assert around it. Decide whether the verify worker should be
+started unlinked or supervised.
+
+**Operator-visible consequence, observed at BL-025:** the two defects compose, so
+`aetheris verify <traj> --allow-effects` on any trajectory containing `http_call` **crashes
+the CLI** rather than reporting a verdict:
+
+```
+** (stop) {:worker_crashed, 159}
+** (EXIT from #PID<0.95.0>) {:worker_crashed, 159}
+```
+
+BL-025's opt-in flag is proven to route correctly (the step is served without it, re-executed
+with it — 0 vs 1 inbound connections at a hermetic listener), but the opt-in is not
+practically usable for `http_call` until this row lands. Not a BL-025 regression: the same
+crash occurs on the pre-BL-025 code path and in record runs.
+
+**Done when:** `setsockopt` (and any other syscall a real `ureq` request needs — enumerate by
+running one, do not guess the list) is either added to the allowlist with an `http_call`
+round-trip test against a hermetic local listener, or `http_call` is explicitly retired; the
+worker-crash-kills-caller behaviour is resolved or consciously accepted with a reason.
+
+`Source: BL-025 execution, demonstrated 2026-07-23 (kernel audit + hermetic listener).`
+
+---
+
+### BL-044 — `mix aetheris` discards every command's exit code (#TBD)
+**Size:** S · **Priority:** low · **Section:** Harness (aetheris/)
+
+`Mix.Tasks.Aetheris.run/1` is `_ = Aetheris.CLI.run(argv); :ok`
+(`lib/mix/tasks/aetheris.ex:10-11`). `Aetheris.CLI.run/1` returns `Formatter.print/2`'s
+`0 | 1` — which the escript entry point does halt on (`main.ex:33-34`) — but the Mix task
+throws it away. So **`mix aetheris <anything>` exits 0 regardless of outcome**, for every
+command, not just verify.
+
+Surfaced at BL-025, where `aetheris verify` was given a failure-reflecting exit code: the
+escript honours it, `mix aetheris verify` does not. The BL-025 test therefore asserts the code
+at `Formatter.print/2` rather than by shelling out through `mix`.
+
+**Not fixed at BL-025 deliberately** — making the Mix task halt non-zero would change
+behaviour for every command at once, and `scripts/sprint.sh` runs `mix aetheris` under
+`set -euo pipefail`, so any command that starts reporting failure honestly could abort the
+sprint. That is a wanted outcome eventually, but it needs the sprint audited in the same
+change rather than as a side effect.
+
+**Done when:** `mix aetheris` propagates the exit code (or documents why it cannot), and
+`sprint.sh` is audited for commands that would newly abort it.
+
+`Source: BL-025 execution, 2026-07-23.`
+
+---
+
+### BL-045 — `RunConfig mode: :verify` is a misnomer: no verification semantics (#TBD)
+**Size:** S · **Priority:** low · **Section:** Harness (aetheris/)
+
+After BL-025 routed `aetheris verify` through `Aetheris.Execution.Verifier`, nothing in the
+harness treats `mode: :verify` as verification. The mode does exactly two things — skip
+context trimming (`loop.ex:409-411`) and skip pre-tools (`pre_tools.ex:59`) — and is
+otherwise a normal **live** run: live model calls, live tool execution, no comparison against
+any record.
+
+**This is not a BL-033-shaped deletion.** BL-033 removes `:fork` from the same union because
+it is unused; `:verify` is *still reachable* — from agent-file config
+(`run_helpers.ex`, `normalize_config_value(:mode, …)`) and from eval task templates
+(`eval/runner.ex:298`). The defect is naming, not deadness: a config author writing
+`mode: "verify"` reasonably expects verification and gets a live run. That mis-expectation is
+precisely what let the CLI diverge from determinism-contract §3 unnoticed for the life of the
+doc (BL-025 §3 edit separates the two by name).
+
+**Scope note:** this is the `RunConfig` **mode** union (`run_config.ex:115`), *not* the
+event-type union (BL-040). Conflating those two is a recorded sketch-failure; keep them apart.
+
+**Done when:** the mode is renamed to what it does (e.g. `:replay_context`) with its two
+call-site parsers updated, or kept with a docstring stating it performs no verification —
+decided, not left ambiguous.
+
+`Source: BL-025 execution, rev-2 adjacent finding, 2026-07-23.`
+
+---
+
 ## boxy-pipeline
 
 ### BL-010 — Clean order_formatter output: strip extra sheets and clear stale template formulas (#51)
@@ -1875,7 +2159,9 @@ multi-line street/city/state/zip.
 | 12 | BL-029 | Every run shows the wrong label today; one line per site. Batch with BL-004 — same file (`harness.rs`) |
 | 13 | BL-028 | Silent-empty is the worst failure shape: a fork proceeds from a wrong context with no signal |
 | 14 | BL-031 | Small resilience fix; converts a class of hangs into a legible error. Cheaper before BL-030 changes the fork call shape |
-| 15 | BL-025 | Verify can re-perform real external effects — the one BL-007 carry with a blast radius outside the repo |
+| ✔ | BL-025 | **Done 2026-07-23.** Grew in-cycle to include the CLI rewire (it never reached `Verifier`). Spawned BL-042/043/044/045 |
+| 15 | BL-042 | Inherits BL-025's slot: closes the *incidental* egress BL-025 named but could not fix. Must follow BL-025 (landed), and should precede BL-043 — repairing `setsockopt` before the netns exists widens the window |
+| 15a | BL-043 | `http_call` is dead in every mode, so nothing regresses by waiting; but it is the reason BL-042's exposure looks smaller than it is. Confirm the tool has no live users before choosing repair-vs-retire |
 | 15b | BL-038 | Medium, operator-facing, and it carries the shared find-run-by-id piece so BL-024 (19b) inherits it rather than the reverse — deciding which lands first rather than leaving "whichever" open |
 | 15c | BL-039 | Ahead of BL-030 — an early-return fork UX matters little while real-provider forks fail at the first LLM call. Builds atop BL-028's landed state (same clause, `fork.ex:101-105`); must not race it |
 | 16 | BL-030 | Unblocks a non-blocking fork UX; do after BL-031 so the wait path is already bounded |
@@ -1887,5 +2173,8 @@ multi-line street/city/state/zip.
 | 21 | BL-035 | Do with the next frontend ticket that touches a fourth formatter site — the trigger, not the calendar |
 | 22 | BL-036 | Closes the blind spot that hid the phantom `RunDetail.events` field. After BL-035; both are cleanup on the same surface |
 | 23 | BL-041 | Disposition (a) is a doc-only rule worth landing before the next export, since that export's own done-check is the case it governs. Disposition (b) batches with BL-036 — both are drift_check blind spots |
-| — | BL-026, BL-027 | Fire on their shared trigger: first `verify` run against a multi-agent/orb trajectory (ratified 2026-07-19). BL-027 shares BL-028's payload-key root cause — if BL-028 lands first, check whether one convention closes both |
+| 23b | BL-044, BL-045 | Small harness cleanups from BL-025; neither blocks anything. BL-045 is a naming decision, not a deletion — do not batch it with BL-033 |
+| 23c | BL-046 | The payload-key convention, after three read-side fixes. Low priority but rising: each new reader has cost a bug. Do with the next `:tool_result` reader, not on a calendar |
+| — | BL-026 | Fires on its trigger: first `verify` run against a multi-agent/orb trajectory (ratified 2026-07-19) |
+| ✔ | BL-027 | **Done 2026-07-23, folded into BL-025.** Its trigger was too narrow — any failed contained tool call reached the crash — and BL-025 made `aetheris verify` real, which would have shipped it. Convention residue → BL-046 |
 | — | BL-006 | Fires on its own trigger |
`````

</details>

---

### 7. Contract §3 + §5 — APPROVED and landed (§8)

Approved in round 2 with one coupling edit (the BL-027 residual-limitations entry, applied).
The draft below is the approval artifact, verbatim from
`aetheris-agents/docs/reviews/bl-025-contract-draft.md`; the resulting §3 and §5 text is now
in `../aetheris/docs/aetheris/determinism-contract.md` — see the §5 diff in §5 above, which
is the authoritative landed version.

---

### BL-025 — determinism contract §3 + §5 rewrite (draft for human approval)

**Status:** **APPROVED** 2026-07-23 (human, in-cycle per §8), with one coupling edit: the
BL-027 fix was folded into BL-025, so §5's residual-limitations entry for recorded tool
failures flips from "remains reachable" to closed. Applied below and landed in
`../aetheris/docs/aetheris/determinism-contract.md`.
**Gate:** contract §8 — "Any code change that would alter a guarantee here lands only
with a human-approved edit to this doc in the same review cycle." BL-025 alters §5's
verify policy and §3's verify row, so both are drafted here first.
**Drafted:** 2026-07-23, against harness `1ebe971` + the BL-025 working tree.
**Verification basis:** every claim below was re-verified at HEAD in this cycle, and the
two that were previously *inferred* rather than demonstrated are corrected — see
"Corrections to the existing text" at the end. Line citations are from the post-BL-025
tree except where marked as pre-change.

---

#### Why two sections

§5 changes because BL-025 introduces the effect-class mechanism §5 said did not exist.
§3 changes for a different reason: §3's verify row cites `verifier.ex` and therefore
describes the **`Verifier`** — but `aetheris verify`, the CLI, did not route through it.
It started a fresh live run and reported success unconditionally. §8 forbids leaving that
as a silent reinterpretation, so the row is corrected and the two things it conflated are
separated by name.

---

#### Replacement for the §3 `verify` row

> | `verify` | Re-execution of every recorded tool call **whose effect class permits it** in a fresh sandboxed worker (`verifier.ex`, `effect_class.ex`); compares recorded vs. re-executed tool **output by value equality** and recorded vs. actual filesystem **`fs_hash`**; serves the recorded result for `:uncontained` tools instead of re-executing them (§5), reporting those steps as **served, not verified**; emits a per-step report with verified/served/failed counts | Verification of a served step — a served step is a record echo and cannot fail; byte-identity of anything a model produced; naming a single first diverging event (§5); **capability-level egress safety** — see §5's `run_command` limitation |

**Add immediately after the mode table** (new paragraph, replacing nothing):

> **`verify` the command vs. `:verify` the run mode.** These are different things and the
> contract previously blurred them, which is how the CLI diverged from this section
> unnoticed for the life of the doc.
>
> - **`Aetheris.Execution.Verifier`** — re-execution of recorded tool calls and comparison
>   against the record. This is what "verify" means in this contract, what §5 governs, and
>   what `aetheris verify <trajectory>` invokes (`cli/commands/verify.ex` →
>   `Aetheris.verify_run/2`).
> - **`RunConfig.mode: :verify`** — a *live-run modifier* with no verification semantics
>   whatsoever. It skips context trimming (`loop.ex:409-411`) and pre-tools
>   (`pre_tools.ex:59`); every other aspect of the run is a normal live run, including live
>   model calls and live tool execution. It is reachable from agent-file config
>   (`run_helpers.ex`, `normalize_config_value(:mode, …)`) and eval task templates
>   (`eval/runner.ex:298`).
>
> Nothing in the harness treats `mode: :verify` as verification. A consumer wanting the
> guarantee in the table above must use the `Verifier`, not the mode.

**Also update the existing "Divergence report (verify)" paragraph**, one clause only:
`verified/failed counts` → `verified/served/failed counts`.

---

#### Replacement for §5 (entire section)

> ## 5. Verify re-execution: effect classes and containment
>
> `verify` re-executes recorded tool calls in a sandboxed worker and compares the result
> against the record. Whether a given tool is re-executed at all is decided by its
> **effect class**, declared in one place — `Aetheris.Execution.EffectClass`
> (`lib/aetheris/execution/effect_class.ex`). (Replay, by contrast, re-executes nothing —
> §3.)
>
> ### The three classes
>
> The taxonomy is aligned to the containment boundary, and the two effectful classes are
> separated by *why* they escape it — because the correct defence differs:
>
> - **`:uncontained`** — the tool's **purpose** is to reach outside the boundary, so the
>   recorded result *is* the answer and re-executing it is both unsafe and pointless.
>   Members: `http_call`; every external MCP tool; and the in-process orb/agent tools
>   (`spawn_agent`, `wait_for_all`, `wait_for_event`, `ask_human`, `send_message`,
>   `broadcast_message`, `read_blackboard`, `write_blackboard`), which run in the BEAM and
>   are therefore outside the worker sandbox altogether — `spawn_agent` can start a run
>   that issues live model calls. These are **record-and-served**: the recorded result is
>   returned, the tool is never invoked.
>
> - **`:contained`** — contained **against the exec-server allowlist**. Members:
>   `read_file`, `list_dir`, `write_file`, `run_command`, and the eleven local `git_*`
>   tools. These are **re-executed and compared** — that is what verify is for.
>
> - **`:pure`** — effect-free (`echo`). Re-executed.
>
> **`:contained` does not mean "incapable of egress."** It means the exec allowlist
> (`native/aetheris_exec_server/src/runner.rs:7-24`) does not name a networking command:
> `curl` and `wget` are blocked and tested (`runner.rs`, `non_permitted_command_is_blocked`).
> But the same allowlist permits `python3`, `python`, `node`, `npm`, `mix`, `cargo` and
> `git` — every one socket-capable, and `npm install` / `mix deps.get` / `cargo build`
> egress by design. So a recorded `run_command` that performed network I/O **will do so
> again under verify**. This is *incidental* egress: a property of particular invocations
> rather than of the tool, which is why record-and-serve is the wrong instrument for it
> (it would serve every computation verify exists to re-check). The right instrument is
> capability-shaped containment at the sandbox layer — tracked as **BL-042**
> (`../aetheris-agents/docs/backlog-2026-06.md`). **Until BL-042 lands, verify's
> egress-safety is partial: closed for the purpose-network tools, open for incidental
> egress through an allowed interpreter.**
>
> ### Containment boundary (from source)
>
> The re-execution worker runs under a user+mount namespace with sandbox-root path
> confinement (`sandbox.rs:135-161`, `28-104`; verify passes no overlay, so OverlayFS is
> not mounted on this path — `verifier.ex`, `main.rs:59-74`). It confines the
> **filesystem only**: no network namespace is created (`CLONE_NEWNS | CLONE_NEWUSER`
> only — `sandbox.rs:137,144`), and the seccomp filter's allowlist explicitly includes the
> socket family under a "Network (`http_call` + MCP stdio)" heading (`sandbox.rs:264-278`).
>
> ### Demonstrated behaviour of an `http_call` re-execution
>
> Re-executing a recorded `http_call` under `--allow-effects` **opens a real TCP connection
> to the recorded host**. Demonstrated, not inferred: against a hermetic localhost listener
> that counts inbound connections, the default path records **0** connections and the
> `--allow-effects` path records **1**
> (`test/aetheris/execution/verify_effects_test.exs`).
>
> The request is not completed, for a reason that is a defect rather than a safeguard: the
> seccomp allowlist omits `setsockopt` (x86_64 syscall 54), so `ureq` is killed by SIGSYS
> after `connect(2)` and before the request is written — kernel audit
> `type=1326 … comm="aetheris_worker" sig=31 … syscall=54`, worker exit status 159. The
> connection still lands. **This truncation must not be read as containment**: it is
> tracked separately, it makes `http_call` unusable in *record* runs as well, and repairing
> it (adding `setsockopt` to the allowlist, which the "Network" heading shows was the
> intent) restores full egress immediately. Record-and-serve is what makes verify safe
> here; the SIGSYS is an unrelated bug that happens to truncate the symptom.
>
> ### Reporting: served is not verified
>
> A served step performs no re-execution, so nothing is compared: there is no output
> equality check and **no `fs_hash` claim**. A served step is reported with status
> `served (not re-executed)` and counted in a distinct `served` tally, never in `verified`
> (`verify_report.ex`, `verifier.ex`). A verify whose every effectful step was served
> therefore reports `Tools verified: 0  Served (not verified): N  Failed: 0` — it does not
> print a green count that overstates what was checked. This matters because a served step
> **cannot fail**: it echoes the record, so it would look identical if the underlying tool
> were entirely broken.
>
> ### The opt-in
>
> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.
>
> ### Tripwire — now mechanized
>
> The previous version of this section carried a prose tripwire: *"before any further tool
> with effects the sandbox does not contain is added to the harness, this section MUST be
> revisited."* Prose has no executor. It is now enforced by
> `test/aetheris/execution/effect_class_test.exs`, which asserts `EffectClass` is **total**
> over the built-in registry (`Registry.names/0`) and over every in-process tool module, and
> fails CI with an actionable message when a tool is added unclassified. An unknown tool
> name classifies as `:uncontained` at runtime — fail-safe, so an unclassified tool is
> served rather than silently re-executed. The doc obligation stands alongside the test: a
> new `:uncontained` tool still requires a human-approved edit here.
>
> ### Residual limitations
>
> - **Incidental egress via `run_command`** — above; BL-042.
> - **Recorded tool failures** are read correctly on **both** paths. Every recorded tool
>   failure is written under `"result"` with `"is_error"` and no `"output"` key
>   (`loop.ex`, `record_tool_error/7`); the served and re-executed paths share one reader
>   that falls back accordingly. The former hard `Map.fetch!("output")` on the re-execution
>   path — which crashed verify on any trajectory containing a failed tool call — is fixed
>   (BL-027, closed here; its stated trigger of "a multi-agent/orb trajectory" was narrower
>   than the real one).
> - **`echo`** is worker-dispatched but unknown to the worker's dispatch table
>   (`main.rs`), so it yields a spurious per-step error under verify. Pre-existing,
>   unchanged.
> - **First diverging event** is still not named (§3, BL-026).
>
> **Research basis:** the record-and-serve mechanism is adapted from
> `docs/aetheris/research/activegraph-log-is-agent-2026-07.md` (arXiv:2605.21997), whose
> §3 framing — determinism as re-projection of recorded state rather than reproducibility
> of live execution (§1) — is exactly why serving a recorded network response is the
> correct semantics rather than a concession.

---

#### Corrections to the existing text (what changed and why)

Both are cases where the prior wording was **inferred from source reading rather than
demonstrated**, and the demonstration disagrees. Recording them so the correction is
auditable rather than silent.

1. **"Running `verify` on a trajectory containing `http_call` therefore issues those
   network calls again."** Partly wrong at HEAD. A TCP connection *is* opened (count = 1 at
   a hermetic listener), but the HTTP request is never written — the worker is SIGSYS-killed
   at `setsockopt`. The old sentence would have led a reader to expect a completed request,
   and a reader who tested for one and saw none could have wrongly concluded verify was
   already safe. The replacement states the connection, the truncation, and that the
   truncation is a bug rather than a defence.

2. **"`run_command` … [has] no effects the sandbox fails to contain."** Wrong. The claim
   was command-shaped (curl/wget are blocked) but the allowlist permits six socket-capable
   interpreters and build tools. The replacement states the residual explicitly and points
   at BL-042.

3. **§3's verify row and the CLI.** The row described the `Verifier` while
   `aetheris verify` ran something else entirely — a live re-run reporting unconditional
   success. BL-025 resolves the divergence in the code's favour by routing the CLI through
   the `Verifier`; the row is updated for the effect classes, and the new paragraph
   separates the command from the run mode so the blur cannot recur.

#### Approval

- [ ] §3 verify row + "command vs mode" paragraph + divergence-report clause
- [ ] §5 full replacement

On approval these land in `../aetheris/docs/aetheris/determinism-contract.md` in the same
commit cycle as the code, per §8.

---

### 8. Implementation notes

Verbatim, `../aetheris/docs/aetheris/milestones/bl-025-implementation-notes.md`.

---

### BL-025 — implementation notes

**Ticket:** BL-025 — Verify: effect classes + record-and-serve for uncontained tools.
**Cycle:** 2026-07-23. Cross-repo (harness + `../aetheris-agents` backlog/review-file).
**Basis:** harness `1ebe971`, agents `d567d75`.

Context that does not survive in the diff. Not a restatement of the spec.

---

#### 1. The ticket's central assumption was wrong, and finding out cost nothing

BL-025 was scoped as "add containment to `Verifier`, expose `--allow-effects` on the CLI."
The re-verify-at-HEAD pass (the ticket's own instruction: *treat every §5 line citation as
a lead*) found that **`aetheris verify` never reached `Verifier`**. `Commands.Verify.run/2`
started a *new live run* with `mode: :verify` and returned `%{verified: true}`
unconditionally. `mode: :verify` only skips context trimming and pre-tools; everything else
is a normal live run.

So the ticket as drafted would have hardened a path no operator uses, while the
operator-facing command kept re-issuing every effect *and* was structurally incapable of
reporting a failure. The human took Option 1 (rewire the CLI) in-cycle.

**The transferable part:** the instruction that caught this was "verify the citations, treat
the list as leads." §5's citations were all accurate — they just described a module the CLI
did not call. No amount of checking `verifier.ex` would have surfaced it; what surfaced it
was asking *who calls this* before changing it. Worth doing on any ticket whose scope is
phrased as "change X" rather than "make behaviour Y true".

#### 2. Two §5 claims were inferred, not demonstrated — and both were wrong

§5 said verify "issues those network calls again" for `http_call`. Rather than restate it,
I ran it against a hermetic localhost listener. Result:

- **1 inbound TCP connection** — so the egress hazard is real, and the default path's
  **0 connections** is a genuine improvement, not a formality.
- But the HTTP request is **never written**. The worker is killed by SIGSYS. Kernel audit:
  `type=1326 … comm="aetheris_worker" sig=31 arch=c000003e syscall=54`, exit status 159
  (128+31). Syscall 54 on x86_64 is `setsockopt`, which is **absent** from the worker's
  seccomp allowlist — under a section explicitly headed *"Network (http_call + MCP stdio)"*.

So `http_call` is broken in **every** mode, record runs included, and has presumably never
worked. Filed as **BL-043**. The trap to avoid: reading that crash as containment. It is an
accidental truncation of a real egress path; repairing it restores full egress instantly.
That is why BL-043 is sequenced *after* BL-042 (netns), and why the §5 rewrite says so
explicitly rather than leaving a future reader to infer safety from a crash.

The second inferred claim: §5 said `run_command` has "no effects the sandbox fails to
contain". The allowlist blocks `curl`/`wget` but permits `python3`, `node`, `npm`, `mix`,
`cargo`, `git` — all socket-capable, and `npm install` / `mix deps.get` egress by design.
Command-shaped, not capability-shaped. Human decision (rev 3): keep `:contained`, name the
limitation in §5, file **BL-042**.

#### 3. Why the classifier is not keyed on tool name alone

The ticket specified `effect_class(tool_name)`. That cannot work: MCP tool names are
discovered at runtime from the server's `tools/list`, so no static map enumerates them.

The recorded `:tool_called` payload carries `"source"` and `"server_id"`, so classification
falls back to those when the name is unknown. **The trap that shape avoids:**
`build_exec_server_index/1` routes `run_command` and all eleven `git_*` with
`source: :mcp, server_id: "aetheris_exec"`. A naive `source == "mcp" ⇒ uncontained` rule
would have served the entire *contained* family instead of verifying it — the exact inverse
of this ticket's purpose, and it would have passed every test written against `http_call`.
`classify/2` therefore resolves **known name first**, source second, and there is a test
pinning `run_command` under `{:mcp, "aetheris_exec"}` to `:contained`.

Unknown name ⇒ `:uncontained`. Fail-safe at runtime; loud at CI via the completeness test.

#### 4. In-process tools are `:uncontained` — and that half-closed BL-027, which is how the rest of it got found

The ticket's sketch put `:pure` on "effect-free worker/in-process tools". But `spawn_agent`
can start a sub-agent that issues live model calls, and none of the in-process tools run
inside the worker sandbox at all — they run in the BEAM. Containment-aligned, they are
`:uncontained`. Only `echo` is `:pure`.

That made BL-027's `KeyError` unreachable *for in-process tools* — they are no longer
dispatched. My first pass stopped there and recorded the residual as still-open: the hard
`Map.fetch!("output")` on the re-execution path, reachable by a **contained** tool whose
recorded result is an error, since `record_tool_error/7` writes `"result"` + `"is_error"`
and no `"output"` for *every* tool regardless of dispatch route.

**Human call, 2026-07-23: fold the fix in.** The reasoning is the part worth keeping. BL-025
made `aetheris verify` actually route through `Verifier` for the first time. Shipping that
while the now-real command crashed on a routine failed-tool trajectory would have been a
worse state than before the ticket — the ticket would have *created* an operator-visible
crash out of a latent one. A ticket that makes a path real inherits the defects on that
path, even ones filed under someone else's row.

The fix is one line: `verify_step/2` reads through the same `recorded_result/1` the served
path already used. Red-first evidence on a trajectory whose recorded `read_file` failed:

```
** (KeyError) key "output" not found in:
   %{"is_error" => true, "result" => "Error: :enoent", "tool_name" => "read_file"}
   verifier.ex:201  Aetheris.Execution.Verifier.verify_step/2
```

After: the step reports `:output_mismatch` with `recorded_output: "Error: :enoent"` — a
genuine divergence (the record failed, the re-execution succeeded), reported legibly.

**What stayed open, deliberately:** the payload-key *convention*. Three tickets have now
fixed the same root cause on the read side — BL-028 (fork, silent-empty), BL-025 (the served
path, written correctly), BL-027 (the re-execute path, crash). The writers are still
unreconciled and nothing declares the convention, so a fourth reader will rediscover it.
Filed as **BL-046**. Note the two fixes are not identical: BL-028's fallback also normalizes
(nil → `""`, non-binary → JSON) per contract §2's string invariant, while verify's must
reflect the record verbatim. So "extract one shared helper" is not automatically right —
which is exactly why the convention needs declaring rather than silently deduplicating.

#### 5. Skipping the worker when every step is served — a testability decision that is also a safety property

`verify_tool_steps/4` classifies all steps first and starts no worker when none needs
re-execution. Two reasons, and the second is why it is not gold-plating:

1. **Safety:** serving every step should not spawn the process whose job is to re-enter the
   world.
2. **Testability:** `:requires_worker` is excluded by default (`test_helper.exs`) *and* by
   CI (`ci.yml:64`). Had the green arm needed a worker, the load-bearing
   "0 inbound connections" assertion would have been silently excluded from every automated
   run — a vacuous green of exactly the class this ticket exists to remove. It now runs in
   the default `mix test`.

#### 6. Known coverage gap, stated rather than papered over

The CLI pass/fail pair (`verify_test.exs`) re-executes a contained tool, so it genuinely
needs the worker and carries `:requires_worker` — which **CI excludes**. So the
mutation-checked replacement for the old vacuous test does not run in CI, only locally with
`--include requires_worker`. This is pre-existing (the worker-backed `verifier_test` case
has the same property), but it is named here rather than left for the tag to imply coverage
it does not provide. The 0-egress assertion, which matters most, does run in CI.

#### 7. Deviation from the ticket: `--allow-effects` is subcommand-local

§E specified a global flag (`mix aetheris --allow-effects verify …`), citing the "global CLI
flags must precede the subcommand" learning. Checked the parser: that learning says flags
*after* the subcommand are parsed by the subcommand handler — and `Commands.Verify` already
called `OptionParser.parse/2`. The flag is verify-specific, so it is declared there, giving
`aetheris verify <traj> --allow-effects` without adding a switch every other command
ignores. The learning is not contradicted; it was describing where parsing happens, not
mandating a global.

#### 8. Small corrections made along the way

- The public API is `Aetheris.verify_run/2`, not `Aetheris.verify/2` (the ticket and my own
  first draft of the CLI both had the latter).
- `VerifyReport` gained `:served` in `@enforce_keys`, so all three in-repo struct literals
  needed updating. `failed` is now `count - verified - served`; previously
  `count - verified`, which would have counted every served step as a failure.

#### 9. `--allow-effects` is proven to route, but is unusable for `http_call` today

Be precise about what "the opt-in path lives" means, because the two levels differ:

- **Library level (proven working):** `Verifier.verify(…, allow_effects: true)` re-executes
  and the hermetic listener records **1** connection vs **0** by default. The test traps
  exits to observe this.
- **CLI level (routes, then crashes):** `aetheris verify <traj> --allow-effects` on a
  trajectory containing `http_call` dies with `{:worker_crashed, 159}` — the SIGSYS of
  BL-043, plus the fact that `Client.start_link` links the worker to its caller, so the
  crash propagates out of `Verifier.verify/2` into the CLI process.

The flag is doing its job (the step is served without it and re-executed with it — that is
the behavioural difference BL-025 owns). The crash is BL-043's, and it is pre-existing:
`http_call` cannot complete in *any* mode. But it means the opt-in is not practically usable
for `http_call` trajectories until BL-043 lands, and the packet says so rather than letting
"opt-in path lives" imply a working operator flow.

#### 10. What the next ticket should know

- **BL-042 before BL-043.** Repairing `setsockopt` without the netns widens the egress
  window. Both rows say so; the ordering is the point.
- **BL-045** (`mode: :verify` misnomer) is a *naming* decision, not a BL-033-shaped
  deletion — the mode is still reachable from agent-file config and eval templates. Do not
  batch it with BL-033.
- **The verify worker kills its caller.** `Client.start_link` links the worker to the
  caller, so a worker crash propagates an exit signal into whatever called
  `Verifier.verify/2`. The BL-025 test traps exits to assert around it. Noted on BL-043.
- The contract draft lives at `../aetheris-agents/docs/reviews/bl-025-contract-draft.md`
  and records *why* each §3/§5 sentence changed, including the two corrections in §2 above.

---

### 9. Adjacent cases enumerated

| Case | Disposition | Evidence |
|---|---|---|
| MCP classified as a **family**, not `http_call`-only | Runtime-discovered names fall back to recorded `"source"`/`"server_id"` | `effect_class_test.exs` — *an unknown tool from an external MCP server is uncontained* |
| `run_command` / `git_*` are routed `source: :mcp, server_id: "aetheris_exec"` | Name resolves **first**, so the contained family stays contained. A naive `source == "mcp"` rule would have served all twelve — the inverse failure, invisible to any `http_call` test | `effect_class_test.exs` — *run_command stays contained despite being routed with source: :mcp* |
| Served steps carry no `fs_hash` claim | No re-execution ⇒ no comparison; renderer says so explicitly | §3 output: `not re-executed (uncontained effect); no fs_hash claim` |
| Recorded-failure `http_call` has **no `"output"` key** (not an empty one) | Served path reads `"output"`, else `"result"` | `verify_effects_test.exs` — *a recorded http_call failure is served verbatim* |
| Completeness test can actually fail | Mutation-checked | §4 |
| Unknown/unclassified tool at runtime | `:uncontained` — fail-safe (served, not re-executed); loud at CI via the completeness test | `effect_class_test.exs` — *an unknown tool with no source is uncontained* |
| `served` must not be counted as `failed` | `failed = count - verified - served`; was `count - verified` | `verify_report.ex` + §3 output |
| `mix aetheris` swallows exit codes for **every** command | Not fixed — filed **BL-044**; exit code asserted at `Formatter.print/2`, not by shelling through `mix` | `mix/tasks/aetheris.ex:10-11` |
| In-process tools classified `:uncontained` | Removes BL-027's *in-process* face | — |
| A **contained** tool with a recorded error still crashed verify | **Fixed** (round 2): one shared reader on both paths. BL-027 closed | §2d red→green |
| The two readers are not identical — BL-028's also normalizes (nil → `""`, non-binary → JSON) per contract §2; verify's must reflect the record verbatim | Not deduplicated. The *convention* is what needs declaring, not the code — **BL-046** | §11 |

---

### 10. Deviations from the ticket — each adjudicated with evidence

1. **Scope grew to the CLI rewire** (§B/§E assumed `aetheris verify` reached `Verifier`; it
   did not). Human decision rev 2, in-cycle.
2. **`run_command` stays `:contained`** despite the allowlist permitting six socket-capable
   interpreters; limitation named in §5, tracked by BL-042. Human decision rev 3.
3. **`--allow-effects` is subcommand-local, not global.** §E cited the "global CLI flags must
   precede the subcommand" learning. Checked the parser: that learning describes *where
   parsing happens* — flags after the subcommand are parsed by the subcommand handler — and
   `Commands.Verify` already called `OptionParser.parse/2`. The flag is verify-specific, so
   it is declared there. `aetheris verify <traj> --allow-effects`.
4. **In-process tools are `:uncontained`, not `:pure`.** The ticket's §A sketch put
   "effect-free worker/in-process tools" under `:pure`, but `spawn_agent` can start a run
   that issues live model calls, and none of them run inside the worker sandbox. Only `echo`
   is `:pure`.
5. **The classifier takes `(name, source)`, not `(name)`.** Forced by MCP's runtime-discovered
   names; §A anticipated a name-keyed map, which cannot cover them.
6. **Public API is `Aetheris.verify_run/2`**, not `Aetheris.verify/2` (as the ticket and my
   own first CLI draft both had).

---

### 11. Backlog rows filed this round

Full text in the §6 diff. Summary:

- **BL-042** — capability-shaped containment (`CLONE_NEWNET`) for the verify worker. Closes
  the *incidental* egress BL-025 named but could not fix. After BL-025, before BL-043.
- **BL-043** — `http_call` is SIGSYS-killed in every mode (`setsockopt` missing). Includes the
  second defect on the same path: `Client.start_link` means a worker crash kills its caller,
  so `verify --allow-effects` on an `http_call` trajectory **crashes the CLI** today.
- **BL-044** — `mix aetheris` discards every command's exit code.
- **BL-045** — `RunConfig mode: :verify` is a misnomer (no verification semantics). Explicitly
  **not** a BL-033-shaped deletion: it is still reachable from agent-file config and eval
  templates. This is the `RunConfig` **mode** union, not the event-type union (BL-040).
- **BL-046** — `"output"` vs `"result"` is a convention with no declaration. Three tickets
  have now fixed the *same* root cause on the read side, one reader at a time: BL-028 (fork —
  silent-empty), BL-025 (served path — written correctly), BL-027 (re-execute path — crash).
  The writers are unreconciled; a fourth reader will rediscover it.
- **BL-027** — **Done**, folded into BL-025 (round 2). Its stated trigger was too narrow.
- **BL-025** — marked Done with the contract-edit, MCP-scope, and BL-027-fold notes.

---

### 12. What this ticket does NOT claim

Capability-level egress safety. `run_command`'s allowlist permits `python3`, `node`, `npm`,
`mix`, `cargo`, `git`, all socket-capable — so verify re-executing a `run_command` that did
network I/O will do so again. That is a **named limitation** in the §5 rewrite and is tracked
by BL-042, not closed here.

Nor is the opt-in usable end-to-end: `--allow-effects` is proven to route (served without it,
re-executed with it — 0 vs 1 connections), but on an `http_call` trajectory it hits BL-043's
crash. Stated rather than left for "opt-in path lives" to imply a working operator flow.

---

### 13. Done-when

| Clause | Status |
|---|---|
| Effect classes as single source of truth | ✅ `EffectClass`; `known_tools/0` is the only enumeration |
| `http_call` + MCP family `:uncontained`, record-and-served by default | ✅ family, not `http_call`-only |
| Served steps reported served-not-verified, excluded from verified tally | ✅ §3 output |
| Completeness test guards the mapping | ✅ mutation-checked, §4 |
| Hermetic no-egress test passes both arms | ✅ 0 default / 1 opt-in |
| CLI routes through `Verifier`, real verdict, failure-reflecting exit code | ✅ §3 |
| Vacuous `verified == true` test replaced with mutation-checked pass/fail pair | ✅ §1c |
| §3 + §5 rewritten and human-approved **this cycle** | ✅ approved round 2, landed in the contract |
| BL-027 folded in: no crash on a failed contained tool | ✅ §2d, red-first |
| BL-025 row Done + follow-ups filed | ✅ §11 |
| Complete output or stated truncation in every section | ✅ |
| Push held | ✅ nothing committed |

**Known coverage gap, named not papered over:** the CLI pass/fail pair re-executes a
contained tool, so it carries `:requires_worker` — which **CI excludes** (`ci.yml:64`). It
runs locally (§1c) but not in CI. Pre-existing for the worker-backed `verifier_test` case
too. The 0-egress assertion, which matters most, does run in CI.
