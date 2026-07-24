# BL-049 — determinism contract §5 edits (draft for human approval)

**Status:** LANDED — harness `a926631`, 2026-07-24. claude-ui ratified all three at review
r2 ((b)/(c) as-is, (a) on content); human approved landing this cycle and chose the
restructured placement for (a). Edit (a) landed **restructured** per the r2 non-blocking
note: the positive statement went into §5's "What the comparison ranges over" body rather
than staying as a paragraph inside "Residual limitations", where a one-line resolved pointer
remains. (b) and (c) landed verbatim as drafted below.
**Gate:** §8 — "Any code change that would alter a guarantee here lands only with a
human-approved edit to this doc in the same review cycle." BL-049 changes what verify's
comparison ranges over, which is a §5 semantics change, so the edits were drafted here and
landed once approved.
**Drafted:** 2026-07-24, against harness `9d994fd` + the BL-049 working tree.
**Verification basis:** §5 was re-read from
`../aetheris/docs/aetheris/determinism-contract.md` at `9d994fd` this cycle. The
project-knowledge export is stale (pre-BL-025/042) and was not used. Line numbers below are
at `9d994fd`.

Three edits. (a) is the one BL-049 earns; (b) is a completeness gap noticed at BL-042 and
folded here rather than spending a standalone §8 cycle; **(c) was added at review r1 (F3)** —
an earlier version of this draft claimed §3 needed no change, and that claim was wrong. See
"Why three, not two" below.

## Why three, not two

The first draft asserted that §3's verify row stayed "exactly true, since BL-049 changes what
the recorded output *is*, not how it is compared." Read against the live row at `9d994fd`,
that does not hold. The row says the mode "compares recorded vs. re-executed tool **output by
value equality**". After BL-049 the equality is preceded by a normalization on *both* sides
(`Verifier.normalize_recorded/2` on the recorded side, `VolatileMetadata.strip/1` on the
re-executed one) — so what is compared is no longer the tool output but its deterministic
portion. "Output by value equality" now reads as whole-output equality, which is the claim
BL-049 makes false. §3 is a guarantee table; a row that overstates what was checked is
exactly what §5's own residual-limitations discipline exists to prevent.

Recorded here rather than quietly fixed: the omission was mine, and the correction is the
reviewer's (r1 F3).

The implementation commit referenced below is `13ff59c` (harness).

---

## (a) Residual limitations — the `run_command` verdict bullet

> **Landed restructured (see Status).** The "After" text below is the *content* that landed;
> its *placement* changed on the r2 note. Rather than replacing the residual-limitation
> bullet with this positive paragraph, the paragraph moved into a new §5 body subsection,
> "What the comparison ranges over", and the residual-limitations bullet became a one-line
> resolved pointer to it. The paragraph's wording is otherwise as below. See harness
> `a926631` for the landed form.

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

## (c) §3 verify row — what the equality ranges over

**Before** (§3 mode-guarantees table, the `verify` row's *Guarantees* cell, line 59,
verbatim — the *Does NOT guarantee* cell is unchanged and is elided here):

> | `verify` | Re-execution of every recorded tool call **whose effect class permits it** in a
> fresh sandboxed worker (`verifier.ex`, `effect_class.ex`); compares recorded vs.
> re-executed tool **output by value equality** and recorded vs. actual filesystem
> **`fs_hash`**; serves the recorded result for `:uncontained` tools instead of re-executing
> them (§5), reporting those steps as **served, not verified**; emits a per-step report with
> verified/served/failed counts | … |

**After** (only the emphasised clause changes; everything else in the cell stands):

> … compares recorded vs. re-executed tool output by value equality **over the deterministic
> portion of that output — volatile execution metadata is excluded from the comparison on
> both sides (§5)** — and recorded vs. actual filesystem **`fs_hash`**; …

**Scope note for the approver.** This is a precision fix to a row that became imprecise, not
a new guarantee: the comparison is still value equality, and nothing about which tools are
re-executed or served changes. The alternative — leaving the row as-is — asserts whole-output
equality, which BL-049 deliberately no longer performs.

---

## What this draft does **not** change

- §5's three classes, the containment boundary, the fail-closed refusal, served-not-verified,
  or the tripwire. BL-049 is verdict-correctness only and touches no containment guarantee.
- The `git_*` residual-limitation bullet (BL-047) and the `echo` bullet — both still open,
  both unchanged.
