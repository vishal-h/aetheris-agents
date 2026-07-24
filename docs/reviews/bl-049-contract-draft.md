# BL-049 — determinism contract §5 edits (draft for human approval)

**Status:** DRAFT — awaiting human approval per contract §8.
**Gate:** §8 — "Any code change that would alter a guarantee here lands only with a
human-approved edit to this doc in the same review cycle." BL-049 changes what verify's
comparison ranges over, which is a §5 semantics change, so the edits are drafted here and
land only once approved.
**Drafted:** 2026-07-24, against harness `9d994fd` + the BL-049 working tree.
**Verification basis:** §5 was re-read from
`../aetheris/docs/aetheris/determinism-contract.md` at `9d994fd` this cycle. The
project-knowledge export is stale (pre-BL-025/042) and was not used. Line numbers below are
at `9d994fd`.

Two edits, both scoped by the ticket. (a) is the one BL-049 earns; (b) is a completeness
gap noticed at BL-042 and folded here rather than spending a standalone §8 cycle.

The implementation commit referenced below is `13ff59c` (harness).

---

## (a) Residual limitations — the `run_command` verdict bullet

**Before** (§5 "Residual limitations", lines 313-321, verbatim):

> - **A `run_command` step can essentially never report `:verified`.** Comparison is value
>   equality over the tool's whole output payload, and the exec server's payload carries
>   `duration_ms` — a wall-clock measurement that differs between the recording and the
>   re-execution. A perfectly reproducible command therefore reports `:output_mismatch` on
>   timing alone (measured: five of six runs; the sixth coincided). Verify tells the truth
>   about the bytes it compared, but "the outputs differ" is not the claim an operator reads
>   it as. Tracked as **BL-049**, which decides whether the comparison should exclude volatile
>   fields, compare structurally, or the tool should stop returning timing in the compared
>   payload — a §5 semantics decision, not a patch.

**After** (replaces that bullet; the surrounding bullets are unchanged):

> - **What the comparison ranges over: the deterministic portion of the output.** Volatile
>   execution metadata — `duration_ms`, and any wall-clock or timing field — is **not part of
>   the compared value**. It is recorded in the step envelope alongside the output, never
>   inside it, so a difference in how long a tool took is not reported as a difference in what
>   it did. Worker-native tools always satisfied this at the parse layer
>   (`worker/client.ex`, `parse_execute_response/1`); exec-server tools did not, which is why
>   a perfectly reproducible `run_command` reported `:output_mismatch` on timing alone
>   (measured: five of six runs, the sixth coinciding). Closed by **BL-049** at `13ff59c`.
>   The fields treated as volatile are defined once, in
>   `Aetheris.Execution.VolatileMetadata`; both the exec-server response parse
>   (`Loop.exec_server_payload/2`) and the verifier call that definition, so there is no
>   second list to drift. The resolution covers **both record eras**: trajectory events are
>   immutable, so a trajectory recorded before `13ff59c` still carries `duration_ms` inside
>   its recorded blob, and the verifier normalizes the recorded side through the same strip
>   before comparing. A `:verified` `run_command` step therefore now asserts something an
>   honest command can satisfy.

**Note on the dependency, for the approver.** Without the read-side normalization this edit
would have to hedge to *"resolved for records at or after `13ff59c`"* — the pre-fix corpus
would otherwise have gone from a 1-in-6 flap to a deterministic `:output_mismatch`, which is
a confident wrong verdict rather than a flaky one. Normalizing both sides is what earns the
unqualified "resolved", and it is why the verifier changed at all.

---

## (b) "The opt-in" — `--allow-effects` also waives the network namespace

**Before** (§5 "The opt-in", lines 288-292, verbatim):

> ### The opt-in
>
> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.

**After:**

> ### The opt-in
>
> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.
>
> It also **waives the network namespace**. The re-execution worker is started with
> `network_namespace: not allow_effects` (`verifier.ex`), so the flag removes *both* guards
> at once: record-and-serve for `:uncontained` tools, and the containment boundary described
> above for everything else. This is a requirement rather than an oversight — `--allow-effects`
> exists to re-issue real network effects, and a worker inside a fresh network namespace
> cannot. The consequence is that under `--allow-effects` a `:contained` tool's incidental
> egress is live again, and the report says so
> (`Re-execution ran WITHOUT network isolation (--allow-effects): real effects were re-issued.`).
>
> Requesting effects is therefore requiring the uncontained path. The converse also holds and
> is stated under "When containment cannot be established": a default verify that cannot
> establish the namespace **refuses** rather than falling back to running without one.

**Why this belongs in §5 rather than being left implicit.** The netns gating is already
documented under "Containment boundary (from source)", which is where a reader looking for
*how containment works* will find it. "The opt-in" is where a reader looking for *what the
flag does* will look, and it named only the record-and-serve half. An operator reading only
this subsection would reasonably conclude `--allow-effects` re-executes uncontained tools
while leaving the namespace in place — the one reading it cannot have.

---

## What this draft does **not** change

- §3's verify row. It describes the compare as "recorded vs. re-executed tool **output by
  value equality**", which remains exactly true — BL-049 changes what the recorded output
  *is*, not how it is compared. No edit needed, and inventing one would overstate the change.
- §5's three classes, the containment boundary, the fail-closed refusal, served-not-verified,
  or the tripwire. BL-049 is verdict-correctness only and touches no containment guarantee.
- The `git_*` residual-limitation bullet (BL-047) and the `echo` bullet — both still open,
  both unchanged.
