# BL-042 — determinism contract §5 edit (draft for human approval)

**Status:** DRAFT — awaiting human approval per contract §8.
**Gate:** §8 — "Any code change that would alter a guarantee here lands only with a
human-approved edit to this doc in the same review cycle." BL-042 alters §5's containment
guarantee, so the edit is drafted here first and lands only once approved.
**Drafted:** 2026-07-23, against harness `8021a59` + the BL-042 working tree.
**Verification basis:** every citation below was read at the post-change tree in this cycle.
The third statement is a *correction* of text BL-025 landed one cycle ago — see "Why three
statements".

---

## Why three statements

The row scoped two (upgrade + condition). Implementation surfaced a third, and it is not
optional: §5's existing `:contained` claim is **false at HEAD**, and §8 forbids leaving a
false guarantee standing once it is known.

- **(a) Upgrade** — the egress-safety statement goes from *partial* to *capability-complete*.
- **(b) Condition** — that guarantee holds only where the namespace is establishable, and the
  fail-closed refusal is contract-visible behaviour. Drafting (a) without (b) would restate
  the exact unconditional overclaim BL-025's §5 rewrite existed to remove.
- **(c) Correction** — §5 says `:contained` tools are "re-executed and compared". They were
  not: `run_command` and all eleven `git_*` tools are dispatched to the exec server over MCP
  in a live run but were sent down the worker-native path by `Verifier`, so they returned
  `unknown_tool:<name>` and never ran. Only the worker-native filesystem built-ins were ever
  actually re-executed.

(c) is a Cited-means-read instance one level up: BL-025's claim was true of `read_file`, from
which the family's behaviour was inferred rather than exercised. Demonstrated this cycle
before the fix, against the unmodified tree:

```
BL-042 PRE-FIX default-verify step: %{
  error: "unknown_tool:run_command",
  status: :error,
  recorded_output: "{\"duration_ms\":20,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"connected\\n\"}",
  actual_output: nil,
  tool_name: "run_command"
}
```

BL-042 fixes the routing for **`run_command` only** — the tool its own proof requires, whose
re-execution BL-025 already ratified as `:contained`, and whose sole new hazard is the egress
this row contains. The `git_*` family is left exactly as it is (`unknown_tool` today, already
broken, not regressed) and filed as **BL-047**, because whether mutating git operations should
re-execute under verify at all, be served, or be declared unsupported is a taxonomy decision of
the same weight as BL-025's three classes — it should be decided, not inherited from a routing
accident.

---

## Replacement for the `:contained` bullet (§5 "The three classes")

> - **`:contained`** — contained **against the exec allowlist and, under a default verify,
>   against the network itself**. Members: `read_file`, `list_dir`, `write_file`,
>   `run_command`, and the eleven local `git_*` tools. These are **re-executed and compared** —
>   that is what verify is for — with one live gap named below.
>
>   **Routing gap (BL-047).** Re-execution reaches a tool only by the route that dispatches it.
>   `run_command` and the `git_*` tools are exec-server MCP tools in a live run (`loop.ex`
>   `@exec_server_tools`, `dispatch_mcp_tool/4`); the worker's own dispatch table
>   (`main.rs` `dispatch/3`) knows only `read_file`, `list_dir`, `write_file`, `http_call`.
>   `Verifier` sent every tool down the worker-native path, so the whole exec-server family
>   re-executed as `unknown_tool:<name>` — a per-step `:error`, never a comparison. BL-042
>   routes **`run_command`** correctly (`verifier.ex` `@exec_server_tools`, `reexecute/3`); the
>   eleven `git_*` tools remain unrouted and are tracked as **BL-047**, which decides whether
>   mutating git operations should re-execute under verify at all. Until it lands, a recorded
>   `git_*` step reports `:error`, not a verdict.

## Replacement for the `run_command` limitation paragraph (§5, after the three classes)

Replaces the paragraph beginning "**`:contained` does not mean "incapable of egress."**" whose
last sentence currently reads *"Until BL-042 lands, verify's egress-safety is partial: closed
for the purpose-network tools, open for incidental egress through an allowed interpreter."*

> **The exec allowlist does not constrain capability; the sandbox does.** The allowlist
> (`native/aetheris_exec_server/src/runner.rs:7-24`) names no networking command — `curl` and
> `wget` are blocked and tested — but permits `python3`, `python`, `node`, `npm`, `mix`,
> `cargo` and `git`, every one socket-capable, and `npm install` / `mix deps.get` /
> `cargo build` egress by design. A recorded `run_command` that performed network I/O would
> therefore have done so again under verify. This is *incidental* egress: a property of
> particular invocations rather than of the tool, which is why record-and-serve is the wrong
> instrument for it (it would serve every computation verify exists to re-check).
>
> **The instrument is capability-shaped containment at the sandbox layer, and it is now in
> place (BL-042).** A default verify re-executes inside a **network namespace**: the worker
> `unshare`s `CLONE_NEWNET` alongside the user and mount namespaces
> (`native/aetheris_worker/src/sandbox.rs:161-224`), and the exec server is spawned *after*
> that call (`main.rs:59` → `:100`), so it inherits the namespace and `run_command` inherits it
> in turn. The namespace has only a loopback interface and it is left **down**: nothing in the
> worker needs it, since the worker↔BEAM channel and MCP stdio are pipes. No re-executed tool
> can egress, whatever the allowlist permits and whatever the recorded command chose to do.
>
> **Verify's egress-safety is therefore capability-complete for re-execution, conditional on
> the namespace being establishable** — see "When containment cannot be established" below.
> Record-and-serve (BL-025) remains in force for the `:uncontained` class and is now
> defence-in-depth rather than the sole defence.

## Replacement for "Containment boundary (from source)"

The existing subsection states the opposite of what is now true and must be replaced, not
amended.

> ### Containment boundary (from source)
>
> The re-execution worker runs under a user + mount namespace with sandbox-root path
> confinement (`sandbox.rs`, `Sandbox::resolve/resolve_new`; verify passes no overlay, so
> OverlayFS is not mounted on this path — `verifier.ex`, `main.rs`). Under a **default**
> verify it additionally runs under a **network namespace** (`CLONE_NEWUSER | CLONE_NEWNS |
> CLONE_NEWNET`, `sandbox.rs:169-172`), which is what closes incidental egress.
>
> The namespace is requested per verify, not globally: `Verifier` passes
> `network_namespace: not allow_effects` when it starts the worker (`verifier.ex:89-96`). This
> gating is a requirement rather than a preference — `--allow-effects` exists to re-issue real
> network effects, and a worker inside a fresh network namespace cannot. **Record runs are
> unaffected**: they never request the namespace, so their flags and their fail-open behaviour
> in restricted containers are unchanged.
>
> The seccomp filter still allows the socket family (`sandbox.rs`, "Network (`http_call` +
> MCP stdio)"), and is deliberately not the mechanism here: the exec server is a *separate
> process*, spawned before the filter is applied (`main.rs:100` vs `:112`), so it never runs
> under the filter at all. The namespace is inherited by that process; the filter would not
> have been.

## New subsection — "When containment cannot be established"

Insert immediately after "Containment boundary (from source)".

> ### When containment cannot be established
>
> A kernel may refuse `unshare` — restricted containers do, and no namespaces exist on
> non-Linux hosts at all. The worker reports what it actually established rather than only
> logging it: namespaces are entered **before** the `ready` handshake is written, and `ready`
> carries `network_namespace: true|false` (`main.rs:56-74`).
>
> **A default verify fails closed.** Requesting the namespace is requiring it: a worker that
> could not establish one never finishes starting (`client.ex`, `containment_verdict/2`), and
> `aetheris verify` reports
>
> ```
> cannot establish network containment for verify; re-run with --allow-effects to proceed
> uncontained, or run where unshare is permitted
> ```
>
> rather than a verdict. This is contract-visible behaviour, not an internal detail: an
> operator whose kernel denies `unshare` gets an error instead of a report, and on a non-Linux
> host every default verify refuses. The reasoning is that verify's entire value *is* the
> guarantee, so a verify that cannot guarantee has nothing to report — and `--allow-effects`
> already names the deliberate uncontained path, so a *silently* uncontained default has no
> constituency.
>
> **Record mode keeps its fail-open** and is untouched: a normal run in a restricted container
> continues without isolation, exactly as before.
>
> The report says which way it ran. A verify that re-executed under isolation prints
> `Re-execution ran under a network namespace: no re-executed tool could egress.`; under
> `--allow-effects` it prints the corresponding warning; and a diverging step under isolation
> carries a note that a step which reached the network when recorded cannot reproduce there
> (`verifier.ex`, `render_containment/1`, `render_isolation_note/2`). A networked divergence is
> a true report about a non-reproducible step, and it must read as one rather than as a
> mystery mismatch.

## Update to "Residual limitations"

Replace the first bullet; leave the rest as they are.

> - **Incidental egress via `run_command`** — closed by the network namespace (above), for
>   re-execution under a default verify. `--allow-effects` re-opens it by design.
> - **`git_*` tools are not re-executed at all** — the exec-server routing gap above; a
>   recorded `git_*` step reports `:error`. Tracked as **BL-047**, which also decides whether
>   they *should* be re-executed.
> - **A `run_command` step can essentially never report `:verified`.** Comparison is value
>   equality over the tool's whole output payload, and the exec server's payload carries
>   `duration_ms` — a wall-clock measurement that differs between the recording and the
>   re-execution. A perfectly reproducible command therefore reports `:output_mismatch` on
>   timing alone (measured: five of six runs; the sixth coincided). Verify tells the truth
>   about the bytes it compared, but "the outputs differ" is not the claim an operator reads
>   it as. Tracked as **BL-049**, which decides whether the comparison should exclude volatile
>   fields, compare structurally, or the tool should stop returning timing in the compared
>   payload — a §5 semantics decision, not a patch.

## Update to the §3 `verify` row

One clause only, in the "does not guarantee" column. The row currently ends:

> … **capability-level egress safety** — see §5's `run_command` limitation

Replace with:

> … re-execution of the `git_*` family (§5, BL-047); capability-level egress safety **where
> the kernel refuses to create a network namespace** — verify declines rather than
> guaranteeing (§5)

---

## Demonstration (both arms, hermetic)

`test/aetheris/execution/verify_effects_test.exs`, run with `--include requires_worker`
(the tag is excluded by default in `test_helper.exs`, so a plain `mix test` does not
exercise either arm). The listener counts inbound connections; the recorded step is produced
by a real worker, so both arms measure a **delta** against that recording.

| arm | connections | step status |
|---|---|---|
| pre-fix, routing unrouted | 0 | `:error` — `unknown_tool:run_command` (never ran) |
| pre-netns, routing fixed | **1** | re-executed and egressed — the red arm |
| default verify (netns) | **0** | `:output_mismatch`, with the isolation note |
| `--allow-effects` (no netns) | **≥1** | re-executed and egressed — status not asserted, see below |

The middle row is why the routing fix rides this ticket: without it the "0 connections" of a
default verify is true before the namespace exists, and proves nothing.

**The `--allow-effects` arm's status is deliberately not asserted, and cannot be.** The exec
server's `run_command` payload carries `duration_ms`, and §5's comparison is value equality
over that whole JSON blob. Measured over six runs of an identical, perfectly reproducible
command: five `:output_mismatch`, one `:verified` — decided entirely by whether the
millisecond timing happened to coincide.

```
status: :output_mismatch  recorded: {"duration_ms":19,…}  actual: {"duration_ms":21,…}
status: :verified         recorded: {"duration_ms":22,…}  actual: {"duration_ms":22,…}
status: :output_mismatch  recorded: {"duration_ms":23,…}  actual: {"duration_ms":19,…}
status: :output_mismatch  recorded: {"duration_ms":19,…}  actual: {"duration_ms":20,…}
status: :output_mismatch  recorded: {"duration_ms":19,…}  actual: {"duration_ms":21,…}
status: :output_mismatch  recorded: {"duration_ms":21,…}  actual: {"duration_ms":20,…}
```

So **a `run_command` step can essentially never verify**, whatever it does. This is not
introduced by BL-042 — it is exposed by it, because BL-042 is what makes `run_command` reach
the comparison at all (before, it errored). It is a live consequence of this ticket for any
operator running `aetheris verify` on a trajectory with `run_command` steps, and it is
tracked as **BL-049**. The default-verify row above is unaffected: that step diverges on
`exit_code` and `stderr`, not on timing.

---

## Not in this edit

- **BL-043** (`setsockopt` missing from the seccomp allowlist → `http_call` SIGSYS) is
  unchanged, and §5's existing paragraph on it stands as written. `--allow-effects` on an
  `http_call` trajectory still crashes the CLI. BL-042 lands first by design: repairing
  `setsockopt` before this namespace existed would have widened the egress window.
- The `echo` residual limitation is unchanged — same routing mechanism, different family
  (in-process, not exec-server).
