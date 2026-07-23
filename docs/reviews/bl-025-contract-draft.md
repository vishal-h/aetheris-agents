# BL-025 — determinism contract §3 + §5 rewrite (draft for human approval)

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

## Why two sections

§5 changes because BL-025 introduces the effect-class mechanism §5 said did not exist.
§3 changes for a different reason: §3's verify row cites `verifier.ex` and therefore
describes the **`Verifier`** — but `aetheris verify`, the CLI, did not route through it.
It started a fresh live run and reported success unconditionally. §8 forbids leaving that
as a silent reinterpretation, so the row is corrected and the two things it conflated are
separated by name.

---

## Replacement for the §3 `verify` row

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

## Replacement for §5 (entire section)

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

## Corrections to the existing text (what changed and why)

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

## Approval

- [ ] §3 verify row + "command vs mode" paragraph + divergence-report clause
- [ ] §5 full replacement

On approval these land in `../aetheris/docs/aetheris/determinism-contract.md` in the same
commit cycle as the code, per §8.
