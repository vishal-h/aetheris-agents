# BL-047 — determinism contract §5/§3 edits (draft for human approval)

**Status:** DRAFT — awaiting human approval per §8.
**Gate:** §8 — a change that alters a guarantee lands only with a human-approved edit to this
doc in the same review cycle. BL-047 changes how verify treats a whole tool family
(`git_*` → served-not-verified), which is a §5/§3 semantics change.
**Drafted:** 2026-07-24 by claude-ui, against harness `a926631` + the ratified Option-3
classification. Verbatim "Before" blocks are from the live text at `a926631` (claude-code relay,
this cycle); the project-knowledge export is stale and was not used. `f41eb12` is the
implementation commit, filled when it lands.

## Edit set — why five, not three

The design sketch named (a) residual bullet, (b) served-not-verified, (c?) §3. The source read
surfaced two more that the same change forces, plus a factual correction that must ride along:

- **Edit 1 (new)** — §5 "The three classes" `:contained` bullet says `git_*` tools "are
  **re-executed and compared**," and its routing paragraph says they "remain unrouted … report
  `:error`." Both are exactly what BL-047 makes false; leaving them is the overstatement §5's own
  discipline forbids. This block also carries the **`eleven` → `ten`** correction (§5:186 and
  §5:196), inherited from BL-042's edit — it lands here because BL-047 rewrites both sentences
  anyway. Flagged, not silent.
- **Edit 5 adjacent-case** — §3's *Guarantees* cell says verify re-executes "every recorded tool
  call whose effect class permits it." After BL-047, `git_*` is `:contained` (effect class
  permits) but is **not** re-executed (non-reproducible gate). So that clause over-includes
  `git_*` and needs the reproducibility qualifier — one clause wider than the obvious serve-clause
  edit. Named per the Adjacent-case rule.

The omission of edits 1 and 5 from the sketch was claude-ui's; the source read is what caught
them. Recorded here rather than quietly widened.

---

## Edit 1 — §5 "The three classes", `:contained` bullet + routing paragraph (lines 184–198)

**Before** (verbatim):

> - **`:contained`** — contained against the exec allowlist and, under a default verify,
>   against the network itself. Members: `read_file`, `list_dir`, `write_file`,
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

**After:**

> - **`:contained`** — contained against the exec allowlist and, under a default verify,
>   against the network itself. Members: `read_file`, `list_dir`, `write_file`, `run_command`,
>   and the ten local `git_*` tools. The filesystem tools and `run_command` are **re-executed
>   and compared** — that is what verify is for. The `git_*` family is `:contained` for
>   *safety* (local-only — no `push`/`fetch`/`pull`/`clone`/`remote`) but is **served, not
>   re-executed**, for the reason given below and detailed under "Reporting: served is not
>   verified".
>
>   **The exec-server route, and why `git_*` is served (BL-042, BL-047).** Re-execution reaches
>   a tool only by the route that dispatches it. `run_command` and the `git_*` tools are
>   exec-server MCP tools in a live run (`loop.ex` `@exec_server_tools`, `dispatch_mcp_tool/4`);
>   the worker's own dispatch table (`main.rs` `dispatch/3`) knows only `read_file`, `list_dir`,
>   `write_file`, `http_call`. Before either ticket, `Verifier` sent every tool down the
>   worker-native path, so the whole exec-server family re-executed as `unknown_tool:<name>` — a
>   per-step `:error`, never a comparison. **BL-042** routes `run_command` correctly
>   (`verifier.ex` `@exec_server_tools`, `reexecute/3`). **BL-047** decides the ten `git_*` tools
>   the other way: they are **not** re-executed, because they are not verify-reproducible —
>   verify reconstructs no repo working-tree or history (it mounts no overlay), so a re-executed
>   `git_*` op would read an absent repo and `git_commit` would embed a fresh, nondeterministic
>   SHA. A recorded `git_*` step is therefore served-not-verified (resolved at `f41eb12`),
>   and that serve is **not** lifted by `--allow-effects`.

*Note.* `eleven` → `ten` in both sentences (the family is ten: five read-only —
`git_status`, `git_diff`, `git_diff_staged`, `git_log`, `git_show`; five mutating — `git_add`,
`git_commit`, `git_checkout`, `git_cherry_pick`, `git_cherry_pick_control`). The
re-executed-vs-served split resolves the flat "these are re-executed and compared," which was
false for `git_*` once it is served.

---

## Edit 2 — §5 "Reporting: served is not verified" (lines 299–308): the second reason

**Before** (verbatim):

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

**After** (existing paragraph unchanged; one paragraph appended):

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
> **Two reasons a step is served, and they differ under `--allow-effects`.** A step is served
> either because re-executing it is *unsafe* — an `:uncontained` tool whose effects the sandbox
> cannot hold (network egress, external MCP, in-process orb tools; "The three classes") — or
> because re-executing it is *not meaningful* — a `:contained` tool whose output is
> environment-dependent while verify reconstructs no environment. The `git_*` family is the
> second kind: `:contained` for safety (local-only, no egress) but not verify-reproducible,
> because verify mounts no overlay, so the recorded run's repo working-tree and history are
> absent and a re-executed `git_*` op would read a repo that is not there (and `git_commit`
> would embed a fresh, nondeterministic SHA). The two reasons diverge on exactly one point: the
> unsafe-to-re-execute serve is **lifted by `--allow-effects`** — the operator opts into the real
> effects to obtain a verdict; the non-reproducible serve is **not** lifted — re-executing a
> `git_*` op still reconstructs no repo, so it would only manufacture a spurious mismatch, and
> `--allow-effects` has no external `git_*` effect to re-issue. `git_*` is therefore served under
> both default and `--allow-effects` verify.

---

## Edit 3 — §5 "The opt-in" (lines 310–327): `--allow-effects` does not lift the `git_*` serve

**Before** (verbatim, first paragraph only — the rest of the subsection is unchanged):

> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.

**After:**

> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text. It does **not** restore re-execution of the non-reproducible `git_*` serve
> ("Reporting: served is not verified"): that serve is unconditional, because re-executing a
> `git_*` op reconstructs no repo and the flag has no external `git_*` effect to re-issue.
> `--allow-effects` lifts the *unsafe* serve, never the *non-reproducible* one.

---

## Edit 4 — §5 "Residual limitations", the `git_*` bullet (lines 345–347): → resolved

**Before** (verbatim):

> - **`git_*` tools are not re-executed at all** — the exec-server routing gap above; a
>   recorded `git_*` step reports `:error`. Tracked as **BL-047**, which also decides whether
>   they *should* be re-executed.

**After** (one-line resolved marker, matching the list's `Incidental egress … closed by` /
`run_command verdict … resolved at 13ff59c` convention):

> - **`git_*` tools are served, not re-executed** — resolved at `f41eb12` (BL-047):
>   `:contained` for safety but not verify-reproducible, so served-not-verified and not lifted by
>   `--allow-effects`. See "The three classes" and "Reporting: served is not verified" above.

---

## Edit 5 — §3 verify row (line 59): reproducibility qualifier + the served set + the non-guarantee

Three clauses in the one row. **Before** (verbatim, the changing clauses shown in context):

> *Guarantees cell:* Re-execution of every recorded tool call **whose effect class permits it**
> in a fresh sandboxed worker … ; serves the recorded result **for `:uncontained` tools** instead
> of re-executing them (§5), reporting those steps as **served, not verified**; emits a per-step
> report with verified/served/failed counts
>
> *Does NOT guarantee cell:* … ; **re-execution of the `git_*` family (§5, BL-047)** ; …

**After:**

> *Guarantees cell:* Re-execution of every recorded tool call **whose effect class permits it and
> whose output verify can reproduce** in a fresh sandboxed worker … ; serves the recorded result
> **for `:uncontained` tools, and for the `:contained` but non-reproducible `git_*` family,**
> instead of re-executing them (§5), reporting those steps as **served, not verified**; emits a
> per-step report with verified/served/failed counts
>
> *Does NOT guarantee cell:* … ; **re-execution of the `git_*` family — served, not re-executed
> by design (§5)** ; …

*(The BL-049 (c) qualifier already in this cell — "over the deterministic portion … excluded on
both sides (§5)" — and every other clause are unchanged.)*

---

## What this draft does **not** change

- §5's class *definitions* (`:pure` / `:contained` / `:uncontained`), the containment boundary,
  the fail-closed refusal, or "When containment cannot be established." `git_*` stays `:contained`
  — its safety label is correct; only its re-execution disposition changes.
- The `run_command` handling, the `http_call`/`:uncontained` handling, or BL-049's volatile strip.
- Verifier's `@exec_server_tools` (stays `~w[run_command]`) — `git_*` is served, never
  re-executed, so it is never added there and BL-049 F2's subset-containment concern does not
  touch it.

---

## Held

Contract edits land only on human ratification (§8), in the same cycle as the implementation.
Push held.
