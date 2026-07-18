# BL-007 / t1 — implementation notes: determinism contract doc + F2 semantics fix

**Ticket:** [README.md](./README.md) §t1 · **Milestone:** [BL-007](./README.md) (#48; per-ticket issues waived)
**Date:** 2026-07-18 · **Repos:** harness `../aetheris/` (contract + docstrings) + `aetheris-agents/` (these notes)

## What was built

1. **`../aetheris/docs/aetheris/determinism-contract.md`** (new) — the NORMATIVE determinism
   contract, from the ticket APPENDIX (byte-identical to the `/tmp/bl-007/` draft; sanity-diffed,
   no divergence), with the `[t1-verify]` claims resolved against source: the MATCHES rows carry
   confirmed citations; the DIVERGES rows (§3 verify + §5) were rewritten under operator approval
   (this review cycle). No `[t1-verify]` tag survives into the committed doc.
2. **`../aetheris/lib/aetheris/execution/fork.ex`** — two docstring fixes (F2): the `from_step/3`
   `@doc` fork-point line and its `:step_not_found` error line, "at or before `step`" → **exact**
   `step` match. Docstrings only; no code change.
3. **`../aetheris/lib/aetheris.ex`** — one docstring fix (F2): `fork_run/3` `@doc`
   `:step_not_found` line, "at or before `step`" → "at `step`". Docstring only.

`replayer.ex` / `verifier.ex` were **read-only** verification targets — no edits.

## The `[t1-verify]` verification table (produced before commit)

Read `../aetheris/lib/aetheris/execution/replayer.ex` and `.../verifier.ex` in full against source.

### §3 replay row + rider — all **MATCH**

| Claim | file:line | Verdict |
|---|---|---|
| replay reconstructs from recorded events; no live model/tool calls | `replayer.ex:24-29`, `52-70` (esp. 57-60); only `Trajectory.{Event,Log}` aliases (L13) | MATCHES |
| replay reads the trajectory file (not SQLite) | `replayer.ex:25` → `file.ex:51-59,65` (`priv/runs/{id}/trajectory.json`); file.ex L9-11 | MATCHES |
| replay reproduces no environment effects (fs overlay/clock) | no env code; timestamps excluded `replayer.ex:35-36,44`; ephemeral in-memory `Log` (L54,60) | MATCHES |

Nuance kept out of the doc's wording: replay regenerates `id`/`run_id`/`seq` and re-timestamps;
`identical?/2` (`replayer.ex:44`) compares `type`/`payload`/`seq`/`step` only. The doc says
"reconstruction," never "byte-identity" — consistent.

### §3 verify row + §5 tool-enumeration + rider — **DIVERGE** (blocking → dispositioned)

| Claim (draft) | file:line | Verdict |
|---|---|---|
| verify re-executes **effect-free** tools | `verifier.ex:130-136` re-executes ALL recorded tools; safety via required sandbox (`95-106`) | DIVERGES |
| **"hash comparison against recorded outputs"** | `verifier.ex:168-174` — output by value equality (L170); only *filesystem* `fs_hash` is hashed (L171) | DIVERGES |
| §5: verify **restricts to the built-in tools it handles** [enumerate] | `verifier.ex:108-136` — no allowlist; every paired tool re-executed | DIVERGES (nothing to enumerate) |
| §3 rider: report names the **first diverging event**? | `verifier.ex:176-186,188-242` — lists all steps + counts | Does NOT (non-blocking per the rider) |

### Rider A — sandbox containment boundary (from source)

- **Verify sandbox construction:** worker started with `sandbox_path`, **no overlay**
  (`verifier.ex:46`) → OverlayFS not mounted on the verify path (`main.rs:59-74` gate). Isolation =
  user+mount namespace + sandbox-root path confinement (`sandbox.rs:135-161`, `28-104`; worker cwd
  = sandbox root, `client.ex:79`). OverlayFS is the *general run* path only (`worker/supervisor.ex:52,66-69`).
- **Network egress — NOT contained:** no network namespace (`CLONE_NEWNET` absent, `sandbox.rs:144`);
  seccomp explicitly permits `socket`/`connect`/`sendto`/… (`sandbox.rs:265-278`, comment
  "Network (http_call + MCP stdio)").
- **A current built-in tool reaches the network:** `http_call` — arbitrary outbound HTTP(S) via
  `ureq`, no host allowlist (`tool_schema/registry.ex:263-287`, `native/aetheris_worker/src/http.rs:3-39`);
  verify re-dispatches it like any recorded tool (`main.rs:375-400`). `run_command`'s allowlist has
  **no** networked command (`curl`/`wget` blocked + tested — `runner.rs:7-24,207-218`); `git_*` are
  local-only (no push/fetch/pull/clone exposed).
- **Effect-class map (current built-ins):** filesystem — `read_file`/`list_dir`/`write_file`;
  filesystem/git (local) — `run_command` + 10 `git_*`; in-process/inter-agent — `echo`,
  `send_message`, `broadcast_message`, `read_blackboard`, `write_blackboard`, `spawn_agent`,
  `wait_for_event`, `wait_for_all`, `ask_human`; **network — `http_call` (the sole non-contained tool).**

## Decisions

**Verify divergences → descriptive rewrite, not normative-aspiration (adjudicated with the operator).**
The verify claims were `[t1-verify]`-tagged because they were claude-ui's extrapolation from
`architecture.md` + the paper, never a ratified decision (unlike seed-carry/CLI, which D1/D2 ratified
and t2 closes). Committing the harness to an unbuilt effect-class mechanism would be ownership inversion.
And the draft's wrongness ran in the dangerous direction — it told an operator effectful tools are never
re-executed, which is false today. §3's verify row + §5 were rewritten to describe actual behavior.
**My (claude-ui) §5 draft was the defect here** — tagged as such in the commit trail.

**Rider A resolved to its adverse branch — verify is NOT side-effect-safe today.** The sandbox contains
the filesystem but not the network, and `http_call` exists *now* and is re-executed by verify. So §5
states this plainly (with `http_call` named) rather than "safe because today's tool set can't reach the
network." §5 keeps a **tripwire**: before any further tool with sandbox-uncontained effects is added,
§5 must be revisited via a human-approved edit; record-and-serve for effectful tools is the deferred fix.

**§3 rider (first diverging event) — non-blocking, per the contract's own instruction.** Verify's report
lists all diverging steps, not a designated first event. The draft rider pre-dispositioned this as a
non-blocking gap; the committed §3 states the fact and points to the backlog (filed at the D6 boundary).

**F2 scope — three docstrings, NOT the comment, NOT a rename.** Fixed `fork.ex:15-16`, `fork.ex:22-23`,
`aetheris.ex:69`. The ticket cited only `fork.ex:15-16` + `aetheris.ex:64-69`; the repo has a **third**
"at or before" at `fork.ex:22-23` (same defect, uncited) — fixed and noted, not silently followed to the
narrower cite (ticket-text vs. repo-reality divergence). **Deliberately not touched:** the comment at
`fork.ex:67-70` ("for each event at step <= fork_step") — verified against source, it describes
`extract_context`, which genuinely filters `e.step <= step` (`fork.ex:80`); the comment is *correct* (it
is about context extraction, not fork-point matching). Editing it to say "exact" would make it wrong. The
private fn name `find_last_step_complete` (`fork.ex:63`) is mildly misleading ("last") but a rename is a
code change beyond "docstrings only" — left for a future ticket if desired.

**Manifest row + verify backlog entries — deferred to t5's export boundary (D6), NOT edited in t1.** The
manifest is regenerated only at an export boundary (project-knowledge-manifest.md L15-21), and README
**t5** ("Docs sync + boundary") explicitly owns "manifest regen including … the contract" + the backlog
filing, with `docs/project-knowledge-manifest.md` and `docs/backlog-2026-06.md` in **t5's** Touches —
both **outside t1's strict Touches**. So t1 adds neither; the contract's §5/§3 self-document the deferral
(backlog "filed at the D6 export boundary"). `drift_check` project_knowledge stays green (the new doc is
not a manifest-tracked entry). *(Round-1 review correction: this paragraph originally said "t2" — t2 is
seed-carry + CLI convergence and owns no boundary work; the export boundary is t5. Fixed here and the
three t1-surfaced backlog items named in t5's README scope.)*

## Review round 1 — finding resolutions

**Finding 1 (gated the commit) — verify's handling of harness-side/in-process tools, from source.** The
§5 draft claimed the in-process/inter-agent tools "have no effects the sandbox fails to contain." Verified
against source, that was wrong (in a new direction), and §5 was corrected under human approval:

- **Verify is worker-only.** `verify_tool_steps/3` starts one worker `Client` (`verifier.ex:46`); the only
  re-exec call is `Client.execute(worker_pid, …)` (`verifier.ex:136`) → the Rust worker. There is **no
  harness-side dispatch** — verify never invokes `loop.ex`'s in-process clauses. So the feared adverse
  cases are unreachable: `spawn_agent` cannot start a live sub-agent; `ask_human`/`wait_*` cannot block
  (their `.call/2` bodies never run under verify).
- **But in-process tools are not cleanly handled.** All tools share the `:tool_called`/`:tool_result`
  recording path (`loop.ex:312-326`), so verify's pairing (`verifier.ex:121-128`, strict adjacency) sees
  them. Of the 9 tools the effect-class map listed as in-process:
  - **5 silently skipped** — `spawn_agent`, `send_message`, `broadcast_message`, `ask_human`,
    `wait_for_all` emit an intervening trajectory event that breaks `:tool_called`→`:tool_result`
    adjacency (`spawn_agent.ex:164-174`, `send_message.ex:79-89`, `broadcast_message.ex:63-73`,
    `ask_human.ex:57-58`, `wait_for_all.ex:209-217,358-368`) → dropped (`verifier.ex:128`).
  - **3 crash verify** — `wait_for_event`, `read_blackboard`, `write_blackboard` emit no intervening event
    → paired → `verify_step/2` does `Map.fetch!(result_event.payload, "output")` (`verifier.ex:133`), but
    their `:tool_result` payloads use the `"result"` key, not `"output"` (`loop.ex:424,482,492`) →
    **`KeyError`**, raised inside a `try/after` with no `rescue` (`verifier.ex:48-53`) → crashes the whole
    `verify/2` call, before any worker call.
  - **1 (echo) graceful + effect-free** — `echo` is NOT a name-specific harness clause; it falls through
    the catch-all `handle_tool_call` (`loop.ex:525-527`) → `dispatch_tool`, whose payload carries the
    `"output"` key (`loop.ex:553` no-worker stub / `loop.ex:570` worker path) and emits no intervening
    event → paired, no KeyError. Verify re-executes it via the worker, which has no `echo` arm
    (`main.rs:371-403`, `unknown => unknown_tool:echo`) → graceful `:error` status (`verifier.ex:153-165`),
    never a crash; echo is effect-free (`echo.ex:58-59`, JSON-encodes its input).

  Net: a multi-agent/orb trajectory using blackboard or wait tools makes `verify` **raise rather than
  return a report**. §5's safe-set sentence was corrected accordingly — in-process is *not* a safe class.

**The verify `KeyError` crash is a real, pre-existing harness robustness defect** (`verifier.ex:133`
assumes the worker `"output"` payload shape for every paired tool). Out of scope for docs-only t1 and
outside BL-007 (verify robustness). Tracked today with citations here + in the review file + named in t5's
README scope; the `backlog-2026-06.md` row lands at the t5 export boundary. Standalone-harness-ticket vs.
trigger-parked (trigger: first verify run against an orb trajectory) is the human's call at t5.

**Finding 2 — boundary ownership is t5, not t2** (corrected above). **Finding 3 — full Elixir gate set run**
(see Gates). **Finding 4 — MCP guidance folded** into §5's closing safe-set sentence.

## Gates (done-check, all green at the boundary)

```
cd ../aetheris && mix test          → 865 tests, 0 failures, 114 excluded
                 mix hex.audit       → No retired or security advisory packages found (exit 0)
                 mix format --check-formatted → exit 0 (clean)
                 mix credo --strict  → 1905 mods/funs, no issues (exit 0)   [finding 3]
                 mix dialyzer        → passed successfully, 0 errors (exit 0) [finding 3]
cd ../aetheris-agents && python3 scripts/drift_check.py
                 → 8 PASS  0 FAIL  0 WARN  7 INFO (exit 0)  [7 INFO pre-existing, unrelated]
```

No behavior change: docstrings + a new doc only. `mix test`/`format` are unaffected by docstring text;
`drift_check` tracks Rig specs/runbook/architecture, not `aetheris/docs/aetheris/`, so the new doc is
inert to it.

## Open items forwarded

- **t2:** seed-carry (`assemble_config/5`), CLI↔`fork_run/3` convergence (`cli/commands/fork.ex`).
- **t5 (export boundary, D6):** manifest regen incl. the contract; filing of the backlog entries below.
- **Backlog (filed at t5's D6 boundary), all surfaced by t1's `verifier.ex` verification:**
  (a) effect-class declaration mechanism + record-and-serve for effectful tools under verify — motivating
  hazard is `http_call` re-execution issuing real network calls; carries the paper/brief citation;
  (b) the verify divergence-report "first diverging event" gap (`verifier.ex:176-242`);
  (c) the verify `KeyError` crash on paired in-process tools (`verifier.ex:133`) — verify robustness,
  outside BL-007; standalone-ticket vs. trigger-parked decided by the human at t5.
