# Backlog — 2026-06

> **The open-row index.** One section per open row: its heading and a field list, nothing
> else. Terminal rows live in [`backlog-2026-06-closed.md`](backlog-2026-06-closed.md). The id
> is the address: `scripts/backlog_status.py`, `drift_check.py`'s `backlog_resolution` and the
> harness sprint's KNOWN_RED resolver all read the union of the two files.
>
> **Row fields are the only status surface.** GitHub Issues carry none (arbiter ruling R1,
> 2026-09-14).
>
> **Evidence path: `docs/evidence/<ID>.md`**, derived from the id; no index lists the files.
> Each holds the row's body verbatim, with corrections and later evidence appended below it.
>
> **Fields, in order:** `state` · `type` · `area` · `priority · size` · `blocked-by / trigger`
> (optional) · `evidence` · `done-when` · `disposition` (terminal rows only).
> `python3 scripts/backlog_status.py --check` enforces the shape.
>
> **`state`** ∈ `open`, `committed`, `ready`, `blocked`, `triggered`, `verifying`, `done`.
> **`disposition`** ∈ `fixed`, `verified`, `accepted-risk`, `evidence-only`, `superseded`,
> `rejected`.
>
> **Closing an index row** (ruling 2026-09-14, reverses BL-252 D7 going forward): set
> `state: done`, add `disposition`, move the field list to `backlog-2026-06-closed.md`; the
> evidence file stays. BL-252 itself predates this rule and is left as committed.
>
> **`ready` requires a stated `done-when`.** A row whose `done-when` reads `not stated` may not
> be set `ready`.

---

## Bugs

> **`BUG-` is a distinct id space from `BL-`, and the split is by kind, not by
> priority.** A `BUG-` row is a **defect with a root cause** — something that
> behaved wrongly, was diagnosed, and whose row records the diagnosis. A `BL-` row
> is **enhancement or hardening** — work that makes something better or safer,
> including defects filed as opportunities rather than as diagnosed faults. Both
> spaces are parsed by `scripts/backlog_status.py` via the same union, and
> `drift_check.py`'s `backlog_resolution` resolves `BL-` references only; the id
> remains the address, and
> nothing about the prefix changes where a row may live or when it closes.
> `[Declared 2026-09-07 with BUG-001, the first row in this space. The convention
> had been proposed and used in filenames — the ticket was `bug-001`, its reviews
> are `docs/reviews/bug-001-review*.md` — with no row anchoring it, which is the
> shape BL-162 names: a rule alive only in the artifacts that assume it.]`
> [Corrected 2026-09-14, BL-252: this sentence said both spaces were read by both readers.
> When written, both parsed `BL-` headings only; `backlog_status.py` reads `BUG-` since `995b4d0`.]

### BUG-001 — the Drive upload step ignored the requested month and uploaded every archived month into it
- state: verifying
- type: defect
- area: aetheris-agents
- priority: high · size: S
- evidence: docs/evidence/BUG-001.md
- done-when: The next live upload for a month that has **prior months present in `payslip/output/`** both: 1. completes inside the step timeout, and 2. leaves the destination period folder containing **only that month's files**.

---

## Harness (aetheris/)

### BL-024 — Fork lineage queries (`fork_event_id` / "list forks of run X")
- state: open
- type: not stated
- area: Harness
- priority: low · size: M
- evidence: docs/evidence/BL-024.md
- done-when: a lineage query exists that composes with `caused_by`, handles both provenance shapes, and has an e2e covering the null-`fork_step` case.

---

### BL-026 — Verify: divergence report names no first diverging event
- state: triggered
- type: not stated
- area: Harness
- priority: low — **PARKED ON TRIGGER** · size: S
- blocked-by / trigger: the first `verify` run against a multi-agent / orb trajectory
- evidence: docs/evidence/BL-026.md
- done-when: a failing verify names the first diverging event/step explicitly, and the trigger condition above has actually occurred.

---

### BL-032 — WAL connection-lifecycle follow-ups
- state: open
- type: not stated
- area: Harness
- priority: low · size: M
- evidence: docs/evidence/BL-032.md
- done-when: a decision is recorded — either WAL is made deterministic via connection lifecycle (with the three items addressed), or opportunistic WAL is ratified as the permanent design and documented as such.

---

### BL-033 — Remove `:fork` from the `RunConfig` mode union
- state: open
- type: not stated
- area: Harness
- priority: low · size: S
- evidence: docs/evidence/BL-033.md
- done-when: `:fork` is removed from the union, or a reason to keep it is recorded on this entry.

---


---

## Rig (aetheris-agents/rig/)

### BL-006 — Document `stop_reason` when first observed
- state: triggered
- type: not stated
- area: Rig
- priority: tracked (event-triggered, not scheduled) · size: S
- blocked-by / trigger: when drift_check emits `INFO payload_fields: llm_responded.stop_reason in DB events but not listed in specs.md §6`
- evidence: docs/evidence/BL-006.md
- done-when: the INFO fires once and the field is promoted.

---

### BL-023 — Retry parity for hosted-provider adapters: 429 handling
- state: triggered
- type: not stated
- area: Rig
- priority: answered-and-parked (event-triggered, not scheduled) · size: S
- blocked-by / trigger: an observed 429 from OpenRouter in a real run's trajectory
- evidence: docs/evidence/BL-023.md
- done-when: the question is answered and recorded here.

---

### BL-035 — Extract `formatCost` / `formatTokens` to `src/lib/format.ts`
- state: open
- type: not stated
- area: Rig
- priority: low · size: XS
- evidence: docs/evidence/BL-035.md
- done-when: one `src/lib/format.ts` exports both helpers; all four sites import them; no local copies remain; `bunx tsc -b && bun run lint` green.

---

### BL-054 — The twelfth `requires_worker` failure is a load-sensitive flake with no stable identity
- state: committed
- type: not stated
- area: Harness
- priority: low · size: XS–S
- evidence: docs/evidence/BL-054.md
- done-when: the fixed-ms windows in `run_helpers_timeout_test.exs` are made load-insensitive (poll for the state transition rather than assert against a wall-clock budget — the pattern the harness `CLAUDE.md` already promotes, *"poll for trajectory events, not time"*), or the tests are tagged so a loaded full-suite run cannot flake them; and BL-050's race is settled.

---

### BL-052 — drift_check check 9: ghost-struct arm is scoped to `commands/*.rs`
- state: open
- type: not stated
- area: Rig
- priority: low · size: XS
- evidence: docs/evidence/BL-052.md
- done-when: the source scan covers `src-tauri/src/**/*.rs`, or the row is closed with a recorded reason for keeping the narrow scope; `tests/test_drift_check.py` covers a non-`commands/` struct either way.

---

### BL-037 — Nullable `label` in RunSummary/RunDetail: backend distinguishes real from fallback
- state: blocked
- type: not stated
- area: Rig
- priority: low · size: XS–S
- blocked-by / trigger: BL-024
- evidence: docs/evidence/BL-037.md
- done-when: `label` is nullable end-to-end; no consumer compares `label` to `run_id`; the run_id fallback is applied once, at display; `cargo test` + `tsc -b` + `bun run lint` green.

---

### BL-058 — specs §5 (TypeScript Interfaces) is unchecked, and already stale
- state: open
- type: not stated
- area: Rig
- priority: low-medium · size: S
- evidence: docs/evidence/BL-058.md
- done-when: a `drift_check` check compares specs §5 interfaces against `src/hooks/types.ts` with a documented scope rule, §5's `RunSummary` matches source, and `--strict` is green.

---

### BL-062 — Fork provider/model overrides
- state: triggered
- type: not stated
- area: harness CLI + Rig fork dialog
- priority: medium · size: S–M
- blocked-by / trigger: a milestone claims it
- evidence: docs/evidence/BL-062.md
- done-when: the CLI accepts the flags and they reach the fork run; the §4 sentence is corrected and its ref repointed under §8 ratification; operator access (picker vs CLI-only) is decided and recorded.

---

### BL-071 — Resource-level AWS cost + the resource-rate spot-check
- state: triggered
- type: not stated
- area: aetheris-agents
- priority: low (deferred) · size: M
- blocked-by / trigger: the first provider actually billed per resource, or AWS usage growing enough that enabling CE resource-level granularity is worthwhile
- evidence: docs/evidence/BL-071.md
- done-when: a resource-level cost path emits per-resource cost lines for at least one provider, and the rate spot-check compares them against the inventory estimates.

---

### BL-072 — Cost Optimization Hub / Compute Optimizer optimization milestone
- state: triggered
- type: not stated
- area: Milestones
- priority: low · size: L
- blocked-by / trigger: a milestone claims it
- evidence: docs/evidence/BL-072.md
- done-when: milestone docs exist (docs-first, per repo convention); t4's real-bill read seeds the scope (which signals are worth surfacing, what noise looks like); read-only, gated behind its own IAM.

---

### BL-076 — `compose_report_data` sums *every* provider's prior snapshot into one `prior_total`
- state: committed
- type: not stated
- area: cloudcost
- priority: medium · size: S
- evidence: docs/evidence/BL-076.md
- done-when: `load_prior_snapshots`/`month_on_month` scope priors to the providers present in the run's own bundles, with a test asserting the `no_prior_month` path survives another provider's history sitting in the same tree, and a second asserting an N>1 run is unchanged (so the fix does not over-filter).

---

### BL-061 — Gemini thought signatures are not recorded, so a forked Gemini run loses them
- state: triggered
- type: not stated
- area: harness
- priority: low-medium · size: S
- blocked-by / trigger: the first fork of a Gemini tool run
- evidence: docs/evidence/BL-061.md
- done-when: a Gemini fork of a tool step has been run and its outcome recorded, **and §4 is updated from that work either way** — the limitation is confirmed harmless and the clause says so, *or* the signature is recorded, the fork round-trips it, and the clause's Gemini scoping is corrected in the same change, with a test that fails if the block loses its signature.

---

### BL-059 — Parallel tool calls are silently discarded: the adapter keeps the first `tool_use` block
- state: committed
- type: not stated
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-059.md
- done-when: a run whose provider response carries multiple `tool_use` blocks either executes and records all of them (a), or cannot occur because the request disables parallel tool use (b) — with the choice recorded in the determinism contract, and a test that fails if the extra blocks are silently dropped.

---

### BL-040 — Event-type list exists in three places; drift between them is silent
- state: open
- type: not stated
- area: Rig
- priority: low-medium · size: S
- evidence: docs/evidence/BL-040.md
- done-when: `Trajectory.File` derives its map from `Event.known_types/0`, and a test asserts the `@type` union and `@event_types` agree — the union is not derivable, so the test is the only possible guard.

### BL-078 — Converge the AWS client plumbing into a shared `scripts/_aws.py`
- state: triggered
- type: not stated
- area: cloudcost
- priority: low · size: S
- blocked-by / trigger: do it the next time `fetch_aws.py` is legitimately edited
- evidence: docs/evidence/BL-078.md
- done-when: `AWSClients` / `load_credentials` / `warn_shadowing_env` / `enumerate_regions` live in `scripts/_aws.py`; both CLIs import from there; `fetch_aws.py`'s existing 62 AWS tests and t4's suite stay green with no fixture change (the check that it *was* a relocation and not a change — the same evidence t2 used when the type constants moved to `_normalized.py`).

### BL-079 — cloudcost holds no S3 storage rate for `ap-south-1`, where this account's buckets live
- state: triggered
- type: not stated
- area: cloudcost
- priority: low · size: XS
- blocked-by / trigger: a milestone claims it
- evidence: docs/evidence/BL-079.md
- done-when: an `ap-south-1` Standard rate is added **from a verified source with its `as_of`**, or the table is dropped in favour of whatever BL-072's engine-backed integration returns.

### BL-080 — `detect_optimization_signals` reports `partial` for intentional honesty, not only for a read gap
- state: triggered
- type: not stated
- area: cloudcost
- priority: low · size: S
- blocked-by / trigger: a milestone claims it
- evidence: docs/evidence/BL-080.md
- done-when: the third category exists in the envelope, `status` reads `partial` for `denied[] or warnings[]` and `ok` for omissions alone, the render section distinguishes the third (it currently renders warnings under "Left unknown", which is the wrong heading for an intentional omission), and a test asserts a run whose ONLY finding is an unrated region reports `ok`.

### BL-081 — `s3_no_lifecycle_policy` fires on an observably empty bucket
- state: open
- type: not stated
- area: cloudcost
- priority: low · size: XS
- evidence: docs/evidence/BL-081.md
- done-when: `s3_no_lifecycle_policy` is suppressed when and only when the object count was observed to be 0; a test asserts an unknown-count bucket with no policy still raises it.

### BL-082 — no end-to-end orchestrated run of the `CLOUDCOST_OPTIMIZATION=1` path
- state: open
- type: not stated
- area: cloudcost
- priority: low · size: S
- evidence: docs/evidence/BL-082.md
- done-when: either a `cloudcost` sprint leg runs the orchestrator with `CLOUDCOST_OPTIMIZATION=1` and asserts the rendered report contains the optimization section, or an operator runs it once and the trajectory is recorded in the implementation notes.

### BL-084 — Tools manifests for the four use cases that have none
- state: open
- type: not stated
- area: aetheris-agents
- priority: low-medium · size: S
- evidence: docs/evidence/BL-084.md
- done-when: the six cloudcost scripts show without the amber badge and with structured arg forms; descriptions match `capability-matrix.md`; the other three use cases are filed or done.

### BL-085 — Cloudcost credentials + per-launch provider selection in Rig
- state: open
- type: not stated
- area: aetheris-agents
- priority: medium · size: M
- evidence: docs/evidence/BL-085.md
- done-when: with the credentials set, a Rig-launched AWS run authenticates with the read-only key and produces its report; `CLOUDCOST_AWS_*` appears nowhere in the trajectory or `config_json`; the operator can pick aws vs do per launch; the runbook records the posture above.

### BL-086 — Trajectory: label steps by their `run_command` stage
- state: open
- type: not stated
- area: aetheris-agents
- priority: medium · size: S
- evidence: docs/evidence/BL-086.md
- done-when: a cloudcost run labels its stages (`fetch_aws` → `detect_orphans` → `compose_report_data` → `render_report`, plus `detect_optimization_signals` when `CLOUDCOST_OPTIMIZATION=1`); a docbuilder run shows its stages; non-script steps render unchanged.

### BL-087 — `payslip/tools.json` omits a runnable CLI
- state: open
- type: not stated
- area: aetheris-agents
- priority: low · size: XS
- evidence: docs/evidence/BL-087.md
- done-when: the entry is declared with arg forms derived from `python3 scripts/merge_employee_payslips.py --help`; the `xfail` marker in `tests/test_tools_manifests.py` is removed in the same commit.

### BL-088 — `ManifestScript.runnable`: mark a manifest entry describe-only
- state: triggered
- type: not stated
- area: aetheris-agents
- priority: low · size: S
- blocked-by / trigger: a milestone claims it
- evidence: docs/evidence/BL-088.md
- done-when: `runnable: Option<bool>` (serde default true) exists on `ManifestScript`, mirrors into `src/hooks/types.ts`, gates the Run button, and is rejected server-side in `tools_run_script` so the gate is not frontend-only; `p4-001-manifest-spec.md` documents it.

### BL-089 — tools.json for the three use cases that still have none
- state: open
- type: not stated
- area: aetheris-agents
- priority: low-medium · size: S
- evidence: docs/evidence/BL-089.md
- done-when: not stated — see evidence

### BL-091 — exportConfig() drops every manifest-derived env key
- state: open
- type: not stated
- area: aetheris-agents
- priority: low-medium · size: S
- evidence: docs/evidence/BL-091.md
- done-when: not stated — see evidence

### BL-093 — runbook drift: PAYSLIP_MONTH described as non-persistent
- state: open
- type: not stated
- area: aetheris-agents
- priority: low · size: XS
- evidence: docs/evidence/BL-093.md
- done-when: not stated — see evidence

## Milestones (L — issue docs first, per repo convention)

### BL-094 — A direct, non-LLM launch door for config-style orchestrators
- state: open
- type: not stated
- area: aetheris-agents
- priority: medium · size: M/L
- evidence: docs/evidence/BL-094.md
- done-when: an operator can launch a named config-style orchestrator from Rig without an LLM planning turn; the driver-vs-config discriminator is explicit and tested (including the negative — a config file through the wrong path must fail loudly, not exit 0); `specs.md`, `architecture.md` and the p9 t4 notes agree with the code; cloudcost is the first consumer and its runbook §Rig loses the "interim" caveat.

---

### BL-266 — no streaming transport for run/trajectory updates: a UI must poll
- state: open
- type: missing capability
- area: harness — API (Rig/UI consumer)
- priority: medium _(proposed)_ · size: L _(proposed; docs-first per repo convention)_
- evidence: docs/evidence/BL-266.md
- done-when: a UI can follow a run without polling over BOTH an SSE stream and a WebSocket, each auth-gated by the existing token model, built on a transport-neutral core (tranches T0 core, T1 SSE, T2 WebSocket, T3 Rig consumer); wakeups originate inside Store after commit, never a server-side poll-and-forward; no cursor replays from the start and a cursor resumes after it; events arrive in seq order; each frame carries the full event body (the EventRow projection: id, run_id, step, seq, event_type, payload, timestamp) rather than the trajectory summary; once runs.status is terminal the stream delivers every event with seq ≤ runs.terminal_seq, sends a stream_end control frame and closes; non-terminal runs stream only from the hosting VM; a slow or disconnected client neither wedges the run nor leaks; harness playground-api.md documents the endpoints (T1/T2) and Rig's specs.md documents its consumer with drift green (T3); tests assert subscribe → append N → receive N in seq order → terminal closes, and that an unauthenticated subscribe is refused. Design: docs/aetheris/backlog/bl-266-run-event-streaming.md. T1 is blocked by BL-267.

---

## Drift apparatus (optional hardening)

### BL-046 — Tool-result payload key is a convention, not a contract: `"output"` vs `"result"`
- state: open
- type: not stated
- area: Harness
- priority: low · size: S
- evidence: docs/evidence/BL-046.md
- done-when: the `:tool_result` payload contract is stated in one place (a `@type` plus docstring on the writer side, or a documented accessor), the existing readers are pointed at it, and adding a writer that invents a third key is caught — by a test or by there being only one way to write the payload.

---

### BL-044 — `mix aetheris` discards every command's exit code
- state: open
- type: not stated
- area: Harness
- priority: low · size: S
- evidence: docs/evidence/BL-044.md
- done-when: `mix aetheris` propagates the exit code (or documents why it cannot), and `sprint.sh` is audited for commands that would newly abort it.

---

### BL-057 — A stub run that declares tools silently gets no worker, so its tool calls never execute
- state: committed
- type: not stated
- area: Harness
- priority: medium · size: S–M
- evidence: docs/evidence/BL-057.md
- done-when: the question is answered and recorded; the behaviour matches the answer (worker started, or config rejected); `OverlayAutonomousTest`'s `@moduletag :skip` is removed and it passes, or the test is rewritten against whatever the answer makes correct; and the blast radius on the six files is walked, not assumed.

---

### BL-051 — One unidentified `mix test` failure, and the capture discipline that lost its name
- state: open
- type: not stated
- area: Harness
- priority: low (capture fix) / unknown (the flake itself) · size: XS
- evidence: docs/evidence/BL-051.md
- done-when: gate runs capture full test output to a file (summary *and* failure blocks) so a single occurrence is identifiable — this is a habit fix, not a code fix, and belongs in whatever runs the gates; and if the flake recurs with a name, it gets its own row with a mechanism.

---

### BL-045 — `RunConfig mode: :verify` is a misnomer: no verification semantics
- state: open
- type: not stated
- area: Harness
- priority: low · size: S
- evidence: docs/evidence/BL-045.md
- done-when: the mode is renamed to what it does (e.g. `:replay_context`) with its two call-site parsers updated, or kept with a docstring stating it performs no verification — decided, not left ambiguous.

---

### BL-185 — `backlog_status.py --check` reports ARCHIVED-ONLY as a NOTE, and the corpus population is now zero
- state: committed
- type: not stated
- area: Drift apparatus
- priority: low · size: S
- evidence: docs/evidence/BL-185.md
- done-when: `ARCHIVED-ONLY` is promoted from `notes` to `problems` in `resolve`, so `--check` exits 1 on it; the promotion lands with its own red-by-mutation evidence (a fixture row put into the state, watched to fail, restored from a sha-verified working-copy backup); and the corpus population is **re-measured at the promoting commit and found to be 0** rather than inherited from this row — `python3 scripts/backlog_status.py --census` prints it on the `ARCHIVED-ONLY` line, and the line prints even when it is zero for exactly this reason.

---


## boxy-pipeline

### BL-011 — Extract shared parsing helpers into `scripts/parsing_utils.py`
- state: open
- type: not stated
- area: boxy-pipeline
- priority: before next catalog/resolver change · size: S
- evidence: docs/evidence/BL-011.md
- done-when: not stated — see evidence

---

### BL-012 — Catalog enrichment merge strategy
- state: triggered
- type: not stated
- area: boxy-pipeline
- priority: before anyone enriches `catalog.jsonl` · size: S–M
- blocked-by / trigger: m-boxy-pipeline-1a t3 merged (resolver reads JSONL)
- evidence: docs/evidence/BL-012.md
- done-when: not stated — see evidence

---

### BL-013 — Parameterise column x-boundaries in `so_extractor.py`
- state: open
- type: not stated
- area: boxy-pipeline
- priority: before processing a second SO PDF · size: S–M
- evidence: docs/evidence/BL-013.md
- done-when: not stated — see evidence

---

### BL-014 — Parse Bill To and Ship To addresses separately in `_parse_header`
- state: open
- type: not stated
- area: boxy-pipeline
- priority: low (before multi-customer use) · size: S
- evidence: docs/evidence/BL-014.md
- done-when: not stated — see evidence

---

## Unsectioned

### BL-098 — The inventory envelope has no extras key, so adapter run-metadata dies at stdout
- state: committed
- type: not stated
- area: aetheris-agents
- priority: medium · size: M
- evidence: docs/evidence/BL-098.md
- done-when: the §Normalized inventory envelope carries a sanctioned extras key, ratified doc-first per m3 §D-C (section-scoped edit applied against HEAD and diffed by the arbiter, before any adapter emits it); all three adapters emit it; `compose_report_data.py` carries it through; and the report surfaces "this class could not be assessed" distinctly from "this class is empty".

---

### BL-102 — The complete-but-unmarked sweep runs at milestone closes only, so batch closes leave rows silently open
- state: committed
- type: not stated
- area: aetheris-agents
- priority: low-medium · size: XS–S
- evidence: docs/evidence/BL-102.md
- done-when: the export procedure states what the complete-but-unmarked sweep reads at a batch close; BL-084 and BL-085 are each adjudicated done-or-open, with a DONE section written for any that is done; and the rule's wording in `CLAUDE.md` §Definition of done — doc sync no longer reads as milestone-only if it currently does.

---

### BL-108 — the eduloka sink gate parses a merged stream: same shape, different root cause
- state: open
- type: not stated
- area: harness
- priority: low · size: XS
- evidence: docs/evidence/BL-108.md
- done-when: the gate's parse is robust to anything on stderr (or the capture stops merging it); the ambient-variable question is settled and recorded; and the anti-vacuity posture is shown — a constructed stderr-contaminated run must still yield the right verdict or fail loudly.

---

### BL-109 — two `milestone-reference.md` files, canonical by different measures
- state: open
- type: not stated
- area: harness
- priority: low · size: XS
- evidence: docs/evidence/BL-109.md
- done-when: one file is canonical or both are retired; every cross-reference points at whatever survives; and if an index is kept, it either covers current work or says plainly what era it stops at.

---

### BL-111 — session memory is a durable instruction surface outside git, and no census, review or gate can reach it
- state: open
- type: not stated
- area: process
- priority: medium · size: S to characterise
- evidence: docs/evidence/BL-111.md
- done-when: the surface is characterised to a ruling — is it a private scratchpad whose staleness is nobody's problem, or an untracked normative document that a retirement, a promotion or a correction owes an update? — and, if the latter, what a census owes it is written down somewhere a session will read.

---

### BL-112 — the BEAM's latin1 fallback silently corrupts non-ASCII in `--json` payloads
- state: committed
- type: not stated
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-112.md
- done-when: a `--json` payload containing non-ASCII is byte-identical with and without a UTF-8 locale in the environment, or the harness refuses to emit one and names the reason; the mutation posture is recorded against a run with no `LANG` and one with it; and Rig's fork consumer is verified unbroken either way.

---

### BL-113 — a missed *knob* or *optional* credential constant disappears from the sprint's adapter env bridge silently
- state: open
- type: not stated
- area: aetheris-agents
- priority: low · size: XS
- evidence: docs/evidence/BL-113.md
- done-when: an adapter constant naming a credential cannot be added, renamed, or mis-categorised without either the sprint selecting it correctly or a test failing; and the mutation posture is recorded for the **silent** cases specifically — a missed knob, a missed optional credential, and a credential mis-categorised as a knob — not only for the mandatory-credential case that already fails loudly.

---

### BL-114 — the recent-activity modifier has never fired against any real inventory, on any provider
- state: open
- type: defect
- area: cloudcost
- priority: low · size: XS–S
- evidence: docs/evidence/BL-114.md
- done-when: not stated — see evidence

---

### BL-115 — a stopped instance with no attached storage and a non-zero own estimate yields no candidate
- state: committed
- type: defect
- area: cloudcost
- priority: **high** · size: S–M
- evidence: docs/evidence/BL-115.md
- done-when: not stated — see evidence

---

### BL-116 — the aged-snapshot rule's docstring requires a gate its code does not apply
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: S
- evidence: docs/evidence/BL-116.md
- done-when: not stated — see evidence

---

### BL-117 — an out-of-vocabulary `type` is counted everywhere and evaluated by nothing
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: S
- evidence: docs/evidence/BL-117.md
- done-when: not stated — see evidence

---

### BL-118 — five I/O sites decode adapter JSON under the platform default encoding
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: S
- evidence: docs/evidence/BL-118.md
- done-when: not stated — see evidence

---

### BL-119 — a cost snapshot with a declared total and no line items is silently dropped from discovery
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: S (the warning) / M (the document-type change)
- evidence: docs/evidence/BL-119.md
- done-when: not stated — see evidence

---

### BL-120 — the idle-load-balancer rule rests on a `tag:` convention nothing enforces
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: XS to check
- evidence: docs/evidence/BL-120.md
- done-when: not stated — see evidence

---

### BL-122 — `source_granularity` is carried into the report and validated nowhere
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: XS–S
- evidence: docs/evidence/BL-122.md
- done-when: not stated — see evidence

---

### BL-123 — `age_phrase` truncates, so the evidence sentence contradicts its own threshold
- state: open
- type: defect
- area: cloudcost
- priority: low · size: XS
- evidence: docs/evidence/BL-123.md
- done-when: not stated — see evidence

---

### BL-124 — C3: reject a naive timestamp rather than assuming UTC
- state: open
- type: contract consequence
- area: cloudcost
- priority: medium · size: S
- evidence: docs/evidence/BL-124.md
- done-when: not stated — see evidence

---

### BL-125 — C3: name the timestamp field set once instead of hardcoding the pair
- state: open
- type: contract consequence
- area: cloudcost
- priority: low · size: XS
- evidence: docs/evidence/BL-125.md
- done-when: not stated — see evidence

---

### BL-126 — C4: carry the currency's minor-unit exponent and round to it
- state: open
- type: contract consequence
- area: cloudcost
- priority: medium · size: M
- evidence: docs/evidence/BL-126.md
- done-when: not stated — see evidence

---

### BL-128 — C6: the keep marker becomes a first-class field, not a tag spelling
- state: open
- type: contract consequence
- area: cloudcost
- priority: medium · size: M
- evidence: docs/evidence/BL-128.md
- done-when: not stated — see evidence

---

### BL-129 — C10: service identity needs a stable identifier beside the display name
- state: open
- type: contract consequence
- area: cloudcost
- priority: medium · size: M–L
- evidence: docs/evidence/BL-129.md
- done-when: not stated — see evidence

---

### BL-130 — C11: promote `swept_regions` to a first-class optional envelope field
- state: open
- type: contract consequence
- area: cloudcost
- priority: medium · size: S–M
- evidence: docs/evidence/BL-130.md
- done-when: not stated — see evidence

---

### BL-133 — the loop's evidence is not retained, so no past run's greenness is checkable after the fact
- state: open
- type: method
- area: process / harness
- priority: medium · size: S to rule, S–M to implement
- evidence: docs/evidence/BL-133.md
- done-when: not stated — see evidence

---

### BL-134 — verify the seven comment-anchored census claims, and hand-classify the eight the sweep could not reach
- state: open
- type: verification
- area: cloudcost
- priority: low–medium · size: S
- evidence: docs/evidence/BL-134.md
- done-when: not stated — see evidence

---

### BL-136 — decision H's consequent: a read-only cross-provider cost summary over the persisted per-provider snapshots
- state: triggered
- type: feature
- area: cloudcost
- priority: medium · size: S–M
- blocked-by / trigger: a milestone claims it
- evidence: docs/evidence/BL-136.md
- done-when: not stated — see evidence

---

### BL-137 — a freshness census over `cloudcost/milestone.md` §Open items: items whose trigger has already fired, or whose framing predates adapters that have since shipped
- state: open
- type: method
- area: cloudcost
- priority: medium · size: S–M
- evidence: docs/evidence/BL-137.md
- done-when: Every one of the eleven items in §Open items is read against HEAD and marked one of: still accurate; **trigger fired** (the condition it waits on has occurred — say what discharged it and whether the item survives); **framing stale** (the sentence is true but its stated reason is not — corrected in place with the superseded wording quoted, per decision 7); or **discharged elsewhere** (another milestone closed it — cite where).

---

### BL-138 — C8's D21 clause enumerates the declared parameter block wrongly
- state: open
- type: accuracy
- area: cloudcost
- priority: low · size: XS
- evidence: docs/evidence/BL-138.md
- done-when: C8's D21 clause names the five emitted keys, or names the four and says the fifth explicitly; and the *"and nothing else"* claim is either true as written or replaced.

---

### BL-139 — record the conditions under which a triad exchange may be looped without a human turn
- state: committed
- type: method
- area: process / methodology
- priority: low · size: S to rule
- evidence: docs/evidence/BL-139.md
- done-when: the two conditions are written into whichever of the triad documents the ruling names, or the row is closed with a recorded decision that no criterion is to be stated.

---

### BL-140 — whether a correction owes a same-commit sweep for recurrences as a standing obligation
- state: committed
- type: method
- area: process / methodology
- priority: medium · size: S to rule
- evidence: docs/evidence/BL-140.md
- done-when: the obligation is either stated in one named document with its scope (every correction, or a named subset) or declined with the reason recorded, and the existing `CLAUDE.md` correction-chasing entry is reconciled with whichever answer lands.

---

### BL-141 — a Done-check that cannot fail, and whether a positional claim must carry path:line
- state: ready
- type: method
- area: process / methodology
- priority: medium · size: S–M to rule (two questions, one document)
- evidence: docs/evidence/BL-141.md
- done-when: (a) §6 either carries a bar with a stated recognition test or records the decision not to add one; and (b) is either settled by reference to **m5-D1** with the reference written down, or ruled on separately.

---

### BL-142 — whether §6 should require `Touches` to be derived from a search for the premise
- state: committed
- type: method
- area: process / methodology
- priority: medium · size: S to rule
- evidence: docs/evidence/BL-142.md
- done-when: §6's `Touches` field either states the derivation requirement with the search it implies, or records the decision that enumeration stays the author's and why.

---

### BL-143 — the `project_knowledge` export boundary has no owner and no schedule
- state: ready
- type: decision
- area: process / project knowledge
- priority: medium · size: S to decide
- evidence: docs/evidence/BL-143.md
- done-when: either the refresh has a named owner and a trigger with a mechanism behind it (something that fires without a human remembering), or the permanent occupancy is accepted in writing with its reason recorded **where `drift_check`'s output sends a reader**.

---

### BL-144 — a round whose output is a derivation may leave it only in a scratch directory
- state: committed
- type: decision
- area: process / round records
- priority: medium · size: S to decide
- evidence: docs/evidence/BL-144.md
- done-when: the obligation is stated in one named document with its scope — which artifacts, whose responsibility, and where they land — or declined with the reason recorded.

---

### BL-147 — the absence of a reachability stamp encodes three different dispositions
- state: open
- type: defect
- area: cloudcost
- priority: medium · size: S
- evidence: docs/evidence/BL-147.md
- done-when: either every contract carries a legible disposition, or the three-way silence is stated once in §Contracts' preamble so a reader can decode it without the notes file.

---

### BL-148 — C7 and C13 state adapter obligations with no exemplar and no verdict in the contract
- state: committed
- type: defect
- area: cloudcost
- priority: medium — before provider four · size: S–M
- evidence: docs/evidence/BL-148.md
- done-when: C7 and C13 either carry an exemplar or state that they do not and why; and C7's tag-grammar obligation has a stated enforcement position, even if that position is "none, by decision".

---

### BL-149 — two live documents use "live" in incompatible senses
- state: committed
- type: decision
- area: process / round vocabulary
- priority: medium · size: S to decide
- evidence: docs/evidence/BL-149.md
- done-when: either a discriminator is stated in one named document and the citing rounds are consistent with it, or the collision is recorded as accepted with the reason, so the next census author is warned before building an instrument that cannot see it.

---

### BL-153 — the cloudcost sprint's credential gate exits before the stale-artifact guard, so a credential-less leg leaves the previous run's artifacts in place
- state: committed
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-153.md
- done-when: not stated — see evidence

---

### BL-154 — Rig's Cancel kills the direct child only, and transitions nothing
- state: committed
- type: defect
- area: aetheris-agents
- priority: medium · size: M
- evidence: docs/evidence/BL-154.md
- done-when: cancelling a run from Rig leaves a record that says it was cancelled — a terminal event and a `runs.status` distinguishable from both `running` and an unattended `failed` — and the UI reflects the actual end state of the steps rather than freezing them; **or** it is ruled that `failed`-by-sweep is the intended record for a cancel, in which case the sweep's own `run_orphaned` framing is corrected to say so and the UI half is still owed.

---

### BL-155 — the capability matrix has three consumers, no gate, and is the one wiring place an LLM writes
- state: committed
- type: defect
- area: aetheris-agents
- priority: medium-high · size: M
- evidence: docs/evidence/BL-155.md
- done-when: a stale or wrong capability matrix is caught by something other than a person noticing — with the mechanism's own blind spots named, since a row-existence check and a cell-content check are different instruments and the first does not imply the second; **or** it is ruled that the matrix is not gate-worthy, with that ruling recorded and the three consumers documented as reading an unchecked artefact.

---

### BL-156 — the approval card's step text is written by the planner per run, and nothing checks it
- state: committed
- type: defect
- area: aetheris-agents
- priority: medium · size: M
- evidence: docs/evidence/BL-156.md
- done-when: the text on the approval card is either derived from something checkable — the agent's own manifest description, its matrix row, a per-agent template — or it is labelled on the card as model-generated and unverified, so an operator knows what they are reading.

---

### BL-157 — the bare module name `conftest` is a standing trap, and it is held open by an absence
- state: open
- type: defect
- area: test apparatus
- priority: medium · size: S
- evidence: docs/evidence/BL-157.md
- done-when: the absence is either enforced or removed as a dependency, and which of those is **not decided here**.

---

### BL-158 — the pre-existing `integration` population has never been audited against the criterion the gate now uses
- state: open
- type: gate
- area: test apparatus
- priority: medium · size: M
- evidence: docs/evidence/BL-158.md
- done-when: the 159 have been read against the criterion and the result recorded — each either confirmed, or reported as not meeting it — and the reverse sweep for unmarked tests that should carry it has been run once over the whole tree.

---

### BL-159 — what the dormant set owes when boxy-pipeline resumes
- state: triggered
- type: gate
- area: test apparatus
- priority: low until boxy-pipeline resumes, then blocking · size: M
- blocked-by / trigger: boxy-pipeline resumes
- evidence: docs/evidence/BL-159.md
- done-when: boxy-pipeline's work resumes and, before the `pytestmark` lines are removed, the set has been run to completion once under a cap large enough to finish, its true duration recorded, every failure identified by name, and a decision taken on whether the set can be part of the gate at that duration or needs splitting.

---

### BL-160 — the U2 export gate has never returned information in either direction
- state: committed
- type: gate
- area: process / project knowledge
- priority: medium · size: M
- evidence: docs/evidence/BL-160.md
- done-when: a decision is recorded on (3), and (1) and (2) are answered against whatever that decision makes possible — either the pattern set is ruled sufficient with its under-reach accepted in writing, or a corpus and its custody are defined and the value sweep is restored beside it.

---

### BL-162 — an inbound pointer is not a scope change, and nothing tells the row
- state: committed
- type: decision
- area: process / backlog discipline
- priority: medium · size: S to decide
- evidence: docs/evidence/BL-162.md
- done-when: one of the three remedies is chosen and written into a named document with its scope, or the gap is accepted in writing with its reason — either way stating what a citing document owes its target, and where a reader of a row learns what has been routed to it.

---

### BL-164 — a test that hard-codes a value the code derives goes red when the derivation moves, not when the code breaks
- state: committed
- type: defect (instance fixed) + decision (the class)
- area: testing discipline
- priority: medium · size: S to decide the class; the instance is already done
- evidence: docs/evidence/BL-164.md
- done-when: the class has a stated check — a rule in a standing document, a lint, or a sweep with a recorded result — **or** is accepted in writing with its reason, and either way the sweep above has been run and its result recorded, including the result that there is nothing else, if that is what it finds.

---

### BL-166 — `drift_check --strict` is green because of an untracked personal profile export
- state: ready
- type: defect
- area: process / gates
- priority: medium _(proposed)_ · size: S _(proposed)_
- evidence: docs/evidence/BL-166.md
- done-when: `drift_check --strict` is green in a fresh clone at HEAD with no untracked environment, **or** the dependency is declared in a tracked file the gate reads and a run without it is a stated, legible skip rather than a machine-dependent pass — and, either way, a published `drift_check` done-check says what `payload_fields` sampled.

---

### BL-167 — run-level completion needs a harness post-run hook; it is not satisfiable agents-side
- state: committed
- type: gap
- area: harness
- priority: medium _(proposed)_ · size: M _(proposed)_
- evidence: docs/evidence/BL-167.md
- done-when: a reader can distinguish a complete run from an interrupted one **for all six producers**, by a mechanism no prompt line can skip — or it is ruled that per-step attestation is sufficient and the run-level property is retired, in which case BL-153's "writer that runs LAST UNCONDITIONALLY" clause is corrected to say so rather than left standing unmet.

---

### BL-168 — `aetheris_run_id` is declared in five DDL sites across two languages, written by nothing and read by nothing
- state: open
- type: defect
- area: aetheris-agents
- priority: low _(proposed)_ · size: S _(proposed)_
- evidence: docs/evidence/BL-168.md
- done-when: either the five sites are written and something reads them, **or** all five are dropped and `docs/provenance/specs.md`'s four lines go with them.

---

### BL-170 — the concurrency detector is probabilistic, and a single green is not evidence the lock is present
- state: committed
- type: bug
- area: aetheris-agents
- priority: medium · size: S
- evidence: docs/evidence/BL-170.md
- done-when: the mutation control is deterministic, evidenced the way the current figure was: N runs with the lock disabled all red, N runs with it restored all green, with N and the commands recorded.

---

### BL-175 — nothing can report a workflow cache path that names nothing, and the instrument that can is uncommitted
- state: ready
- type: bug
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-175.md
- done-when: the check is committed at a named path in one of the two repos, is invoked by something that runs on its own (not by hand), and has been demonstrated red — by mutation, on the tree it guards, with the restore verified.

---


### BL-180 — the single-backtick wrapper convention mangles wherever the wrapped text carries an inner backtick
- state: open
- type: bug
- area: documentation system
- priority: medium · size: M
- evidence: docs/evidence/BL-180.md
- done-when: a form is chosen and stated; the population is converted **by a committed script**, with the script named and its before-and-after render on a real drawn sample published; **and** something keeps new instances out — a check, a lint, or a `drift_check` arm — that has been demonstrated red against a deliberately reintroduced instance and restored.

---

### BL-183 — `orb_blackboard_test.exs:73` reads a blackboard key one step after the other agent writes it, with nothing synchronising the two
- state: committed
- type: bug
- area: harness
- priority: not stated · size: not stated
- evidence: docs/evidence/BL-183.md
- done-when: all three: 1. The interleaving is **forced** — A's write held until after B's read — and the outcome recorded whichever way it lands. 2. If it is a real race, B's read is synchronised against A's write by a mechanism in the test or the agent, **not** by a sleep, a retry or a relaxed assertion — the same prohibitions BL-181 carried, and for the same reason. 3. The sibling assertions in that test named in BL-181's census output are ruled on rather than left implied


### BL-187 — the planner's `params` map has no declared per-use-case spec, and nothing validates it before the operator approves
- state: committed
- type: defect
- area: aetheris-agents
- priority: medium · size: M
- evidence: docs/evidence/BL-187.md
- done-when: an operator cannot approve a plan carrying a param key no agent in that plan reads, or a value outside that key's declared admissible set — either because the plan is rejected before the card renders, or because the card marks the offending param as unvalidated.


### BL-188 — nothing carries a month from a cloudcost request to the pipeline, so a month-named request cannot be honoured
- state: open
- type: missing capability
- area: aetheris-agents
- priority: medium · size: S–M
- evidence: docs/evidence/BL-188.md
- done-when: a cloudcost request naming a month either produces a report for that month, or produces a plan or report that says which period it will actually cover and why it differs — for every one of the four providers, not only the two with the simple semantics.


### BL-189 — a degraded run has no representation: the stage CLIs' three-valued status is collapsed to a boolean on both operator surfaces, in opposite directions
- state: committed
- type: defect
- area: aetheris-agents and harness
- priority: medium · size: M
- evidence: docs/evidence/BL-189.md
- done-when: on a nonzero step exit the Orchestrator step card shows the stage-CLI `errors[]` when stdout parses to that shape, else truncated stdout, **never a blank** — including the `partial`-with-`errors: null` case above, which has no `errors[]` to show; **and** a `partial` run is distinguishable from both success and failure on whichever surface the operator reads.

---

### BL-190 — the whole-suite gate is red: a cloudcost seat test compares a frozen fixture against a reference date that is the wall clock
- state: ready
- type: defect
- area: aetheris-agents
- priority: medium · size: S
- evidence: docs/evidence/BL-190.md
- done-when: one of two, and the choice is the ticket's: 1. The test pins `--reference-date` to a date fixed relative to the fixture, and asserts the answer that date implies. 2. The test asserts the post-t3 truth — that a legible seat now yields a candidate — with a reference date still pinned, since without pinning the count moves with the calendar either way.

---

### BL-198 — MVML record-mode assertion: at prompt assembly, the assembled prompt equals the log-derived prompt
- state: committed
- type: gate
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-198.md
- done-when: in record mode, at the `prompt_built` site, the loop derives the prompt from prior trajectory events plus recorded config, compares it with the assembled one, and surfaces a divergence — as an event carrying the first differing position, or as a run failure; which one is the row's decision and is recorded on it.

---

### BL-199 — length-stop tool-call guard: a tool call inside a response the token limit cut off is executed as if it were whole, on both provider paths
- state: ready
- type: defect — reachable by reading, not demonstrated live
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-199.md
- done-when: on a length stop with at least one tool call present, nothing executes; each call gets a recorded `tool_result` carrying a structured error (under `failure_category: "truncated_response"` if that vocabulary exists by then, otherwise a named error key stated on the row), and the loop continues to the next turn.

---

### BL-202 — measure the two-surface fetch-instruction condition: the generated index's fetch header has never been in front of a probe
- state: open
- type: measurement
- area: aetheris
- priority: low — cheap, and gated on nothing · size: S
- evidence: docs/evidence/BL-202.md
- done-when: one probe run under the TWO-SURFACE condition — Appendix A's project instructions live AND the store's index carrying the fetch header — filed as a measurement record under harness `docs/aetheris/research/` in the shape the series established: OKF frontmatter per that tree's `README.md` §Frontmatter convention (OKF F3); a **Run against** block stating both surfaces and the store copy each rests on; the operator's results file rendered verbatim as the probe table; and a **§Reading** that names the outcome against the two branches below rather than leaving the comparison to the reader.

### BL-203 — the on-demand pin column carries no obligation, and does not say so
- state: open
- type: documentation
- area: aetheris-agents
- priority: low — nothing fails; the cost is a reader chasing a lag that is not drift · size: XS
- evidence: docs/evidence/BL-203.md
- done-when: the manifest states, AT THE POINT A READER MEETS THE COLUMN — the opening paragraphs, not only the `Surfaces` paragraph below them — what the pin means for each surface: for `export` and `both` a claim about the store that check 8 compares, for `on-demand` a last-moved note that nothing compares.

---

### BL-206 — the event-type map in `trajectory/file.ex` is unenforced and is already one short: `:observation` is declared but unmapped
- state: open
- type: hardening
- area: harness
- priority: low while latent; the trigger that makes it live is ordinary work · size: S
- evidence: docs/evidence/BL-206.md
- done-when: all THREE harness sites hold the same set — `@event_types` (`event.ex:20`), the `@type event_type` union (`event.ex:~46`) and `@event_type_map` (`file.ex:96`) — AND that three-way identity is covered by a check, either a `drift_check.py` arm or a harness test.

---

### BL-207 — `run_command` is not confined to the sandbox root; `read_file` and `write_file` are
- state: ready
- type: hardening
- area: harness
- priority: high — a permitted basename with an out-of-root argument executes today, and the containment the two file tools enforce is absent from the tool that spawns processes · size: TBD — the row states the severity; scoping belongs to the round that takes it
- evidence: docs/evidence/BL-207.md
- done-when: a decision is recorded ON THIS ROW between: **(a)** `pivot_root` inside the worker's existing mount namespace, plus a shared confinement crate the exec server can depend on; or **(b)** `run_command` permanently declared-uncontained, stated in the determinism contract as a standing position.

---

### BL-209 — `build_synthesis_request/1` hardcodes `model: "stub-v1"`, so skill LLM synthesis 404s against a real provider
- state: blocked
- type: bug
- area: harness
- priority: medium · size: TBD — see the Done-when; the row's decision is whether this is fixed at all
- blocked-by / trigger: BL-224
- evidence: docs/evidence/BL-209.md
- done-when: The row closes on **either**: 1. the model is taken from the run's config rather than hardcoded, and `mix test --include integration` passes that test; **or** 2. it is recorded that m14 T5's supersession retires this code path, and the row is closed against **that** — with the retirement pointed at, not merely claimed.

---
### BL-210 — the Anthropic adapter discards the text block on tool-calling responses
- state: ready
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-210.md
- done-when: The adapter preserves the text block alongside `tool_use`, the `llm_responded` payload carries it, and a test asserts a tool-calling response round-trips both.

---
### BL-211 — Segmenter's public surface: an events-taking entry point, and fence-stripping's home
- state: open
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-211.md
- done-when: `Segmenter` takes events without re-reading the file and `Candidate` uses that path; fence-stripping has exactly one implementation in `lib/` with the existing callers pointing at it; a test asserts a fenced response and a bare one both parse through the shared path.

---
### BL-212 — `EXTRACTOR_DENY_LIST` is applied by nothing, and T3's notes claim otherwise
- state: open
- type: defect
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-212.md
- done-when: The deny-list is reachable from a run — a `RunConfig` field (rule 15's three sites), a worker init-payload field, and `main.rs` — with a test that a run declaring it cannot write a denied path; and T3's notes sentence is corrected to say what actually landed.

---

### BL-213 — the curator's provenance record has no durable home
- state: open
- type: defect
- area: harness
- priority: high · size: M
- evidence: docs/evidence/BL-213.md
- done-when: A curation writes its report durably; the record is readable back by `source_run_id` and by skill id; §2's constraint says documents; and a test asserts a rejected candidate — which produces no `skills` row — still appears in the log.

---
### BL-214 — the pre-reflection envelope is recoverable and unused
- state: open
- type: enhancement
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-214.md
- done-when: The curator accepts an extractor run id, diffs the reflected envelope against the stored one, and records the differences in the same record BL-213 gives a home; a run whose extractor had `store_prompts` false produces a stated not-available outcome rather than a pass; and a test covers both.

---
### BL-215 — the reflector can exceed its response budget, leaving an unparseable envelope
- state: open
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-215.md
- done-when: A truncated or unparseable envelope is detectable by the run itself rather than by whoever tries to parse it later, and a long trajectory has a stated strategy — chunking, a per-candidate emission, or a documented cap on candidates per run.

---

### BL-217 — the nested row structs in `commands/*.rs` are fence-undocumented, so `command_fields` cannot see them
- state: open
- type: defect
- area: Rig
- priority: medium · size: M
- evidence: docs/evidence/BL-217.md
- done-when: Every `pub struct` in `commands/*.rs` is inside `command_fields`' population by one of the two routes, or is excluded by a rule the check implements rather than by absence; the sweep covers all 44; and a test asserts that a field added to a previously-unfenced struct draws a finding.

---

### BL-218 — `usage.rs` drops undecodable DB rows silently
- state: committed
- type: defect
- area: Rig
- priority: medium · size: S
- evidence: docs/evidence/BL-218.md
- done-when: An undecodable row is surfaced — an error, or a returned count of what was dropped — rather than discarded, and a test covers the drop path.

---

### BL-219 — the reflector's `findings` describe its own input, not the harness
- state: open
- type: defect
- area: harness
- priority: low · size: S
- evidence: docs/evidence/BL-219.md
- done-when: The `findings` instruction distinguishes an observation about the harness from a description of the envelope the reflector was given — or the key is closed with a recorded reason for keeping it as is; and a live run produces findings that are about the harness or none, an empty list already being the stated right answer when the run suggests nothing.

---

### BL-222 — a skill row can be INSERTED already approved, bypassing the gate
- state: open
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-222.md
- done-when: No write path other than `approve_skill/3` can produce a row with `status: "approved"`, and a test asserts that `insert_skill/1` cannot.

---

### BL-224 — retire m04's `Skill.Extractor` and `extract_skill/3`
- state: open
- type: chore
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-224.md
- done-when: `grep -rn 'extract_skill\|Skill.Extractor' lib/` returns 0; the suite is green with every m04 extraction assertion converted or explicitly retired with its reason; no doc names either.

---

### BL-225 — FrequencyPrior's corpus should read the run's recorded `use_case`
- state: triggered
- type: enhancement
- area: harness
- priority: medium · size: S
- blocked-by / trigger: `RunConfig.use_case` landing, which is part of m14 T12
- evidence: docs/evidence/BL-225.md
- done-when: The corpus comes from runs' recorded `use_case` where present; the union remains the fallback for runs predating the field; a test asserts a run never extracted from still counts toward the prior.

---

### BL-226 — an edited approved body has no re-approval path
- state: open
- type: defect
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-226.md
- done-when: An operator who edits an approved body has a supported path back to served, the path leaves a record of both approvals, and a test asserts the original approval is not overwritten.

---

### BL-227 — `docs/rig/specs.md` §2 is two columns behind on `skills`
- state: open
- type: chore
- area: Rig
- priority: low · size: XS
- evidence: docs/evidence/BL-227.md
- done-when: §2's `skills` block lists both columns and `db_schema` emits no `skills` INFO.

---

### BL-228 — a resumed run loses its served catalog mid-run
- state: open
- type: defect
- area: harness
- priority: high · size: M
- evidence: docs/evidence/BL-228.md
- done-when: A resumed run either re-serves the same catalog — same entries, same body hashes — or records in the trajectory, not only in a log, that it could not.

---

### BL-230 — `broadcast_message_test.exs:258` is a timing race between two agents
- state: committed
- type: defect
- area: harness
- priority: low · size: S
- evidence: docs/evidence/BL-230.md
- done-when: The mechanism is identified and the test no longer races, or the row records why it cannot be made deterministic.

---

### BL-231 — `uc3-skill-extraction.md` describes the retired injector
- state: open
- type: chore
- area: harness
- priority: low · size: XS
- evidence: docs/evidence/BL-231.md
- done-when: The doc is swept to index injection, or marked as describing m04 as history.

---

### BL-233 — a recorded run does not say which agent file produced it
- state: committed
- type: defect
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-233.md
- done-when: A run records what produced it — the agent file's path and the commit or content hash it was read at — and a test asserts a recorded run can name its producer without inference.

---

### BL-234 — baselines locked before BL-221 were computed over unmarked runs
- state: open
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-234.md
- done-when: A baseline records the selection rule it was locked under, and a baseline predating BL-221 is either re-locked or refused by the gate rather than used silently.

---

### BL-238 — `Runner.build_run_config/3` hand-builds a `RunConfig`, bypassing rule 15
- state: ready
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-238.md
- done-when: `Runner` constructs through `from_map/2`, the two divergences are resolved with the choice stated, and a test asserts a newly added `RunConfig` field reaches a Runner-built config without a Runner change — that test is what makes the fix durable rather than a one-time sweep.

---

### BL-240 — `specs.md` §6 does not list `skill_injected`'s marker fields
- state: open
- type: chore
- area: aetheris-agents
- priority: low · size: XS
- evidence: docs/evidence/BL-240.md
- done-when: §6's `skill_injected` row lists `served_under?` and `status?` and says that `served_under` marks a gate measurement.

---

### BL-241 — a forked arm drops its template's pre-tools output
- state: open
- type: defect
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-241.md
- done-when: A forked run's first turn carries the same context an unforked run of the same template would — either the prefix is built after pre-tools, or the pre-tools block is re-applied on top of it — and a test asserts a task with pre-tools produces the same first-turn context forked and unforked.

---

### BL-243 — after a use_case's first approval, no ordinary run can seed a baseline
- state: open
- type: defect
- area: harness
- priority: high · size: M
- evidence: docs/evidence/BL-243.md
- done-when: A baseline can be locked for a use_case that has approved entries — state the mechanism and what a baseline then means — and a test asserts a scope with one approved entry can still seed a baseline for a new candidate.

---

### BL-244 — a forked arm takes its tool list from the template and only its prefix from the recorded run
- state: open
- type: defect
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-244.md
- done-when: A fork either refuses a template whose tool list cannot execute the prefix, or the mismatch is recorded on the run; a test covers a prefix calling a tool the template omits.

---

### BL-245 — a corpus run's recorded segmentation cannot be found, so the prior re-segments it
- state: open
- type: defect
- area: harness
- priority: medium · size: M
- evidence: docs/evidence/BL-245.md
- done-when: An extraction is findable from the run it segmented and from the skills rows it produced; the prior reuses a recorded segmentation where one exists and says so; a test asserts the prior and the candidate agree on segment boundaries for the same run.

---

### BL-246 — a run declaring `tools: []` is still offered spawn_agent, wait_for_event and wait_for_all
- state: ready
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-246.md
- done-when: A run is offered exactly its declared `tools`, plus what a stated contract adds, or the extractor stops claiming it has none and its run fails rather than reports done when it produces no envelope.

---

### BL-247 — the gate's result does not record which control-2 check rejected a candidate
- state: open
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-247.md
- done-when: The control-2 result names which check fired, both when only one does and when both do; a test asserts a candidate matching only the modal path reports that reason and not membership.

### BL-248 — the ETXTBSY / `spawn_agent` worker-sharing question is answered in code and recorded nowhere
- state: committed
- type: documentation
- area: both repos
- priority: medium · size: S
- evidence: docs/evidence/BL-248.md
- done-when: The answer is recorded where the question is asked: both cross-repo tables, with the citations; uc-ingestion phase 1 no longer names it as a gate; and the nested-mix case is stated separately so the answer is not read wider than it goes.

---

### BL-249 — the harness ExUnit `:integration` population has no audit
- state: open
- type: gate
- area: harness
- priority: low–medium · size: M
- evidence: docs/evidence/BL-249.md
- done-when: A criterion exists for what the harness `:integration` tag means; the 24 are audited against it; each either loses the tag or keeps it with the reason recorded where a reader of the gate output can reach it.

---

### BL-250 — a run that fails before serving is recorded `:unavailable` and counted as a no-skill run
- state: committed
- type: defect
- area: harness
- priority: medium · size: S
- evidence: docs/evidence/BL-250.md
- done-when: A run that failed before serving reads `:unknown`, not `:unavailable`; `lock/2` therefore refuses it; and a test covers a run that fails at step 0 with its serve incomplete.

### BL-251 — `mix test` results vary between runs at the same seed: `Skill.BodyTest` captures a concurrent test's warning
- state: ready
- type: defect (test infrastructure)
- area: harness
- priority: medium — a gate whose result varies at a fixed seed is not evidence the suite passed · size: TBD
- evidence: docs/evidence/BL-251.md
- done-when: the assertion distinguishes this test's own log output from concurrent output, or the test is made non-async — with the choice and its cost recorded.

### BL-254 — three retained-manifest-header sentences point "after the table" / "below" at blocks BL-253 moved out
- state: open
- type: defect
- area: process / project knowledge
- priority: low · size: XS
- evidence: docs/evidence/BL-254.md
- done-when: the three pointers (manifest header :25 the SURFACE COLUMN reference, and the 2026-09-07 record references at :71 and :76 — re-derive the line numbers at the fixing commit) resolve to where the blocks now live, by naming the `## Inclusion rulings` / `## Export boundary log` index entry or `docs/export-boundaries/`, rather than to a position in the file; and a check or sweep confirms no retained-header sentence still points at a moved block.

### BL-255 — the kernel-ceiling decrease-only rule sets zero headroom, so the next backlog filing fails --strict
- state: open
- type: defect
- area: process / project knowledge
- priority: low · size: XS
- evidence: docs/evidence/BL-255.md
- done-when: the manifest header's Kernel ceiling rule states how much headroom a downward ratchet leaves — a fixed slack or a round-up — so that lowering the ceiling cannot make an ordinary backlog filing fail kernel_budget under --strict; and the rule names what re-tightens the slack as the kernel shrinks toward the target.

### BL-263 — a boot-resumed run is not yet registered when the scheduler's first tick runs, so `:overlap_live` cannot see it
- state: open
- type: defect — found while implementing BL-256, not demonstrated live
- area: harness — scheduler / admission (INV-2)
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-263.md
- done-when: a run restored by boot resume is registered before the scheduler's first tick can admit a start for its schedule — or the scheduler's first tick is held until resume has completed — so `:overlap_live` cannot return false for a schedule whose previous run the harness has just restored; a test asserts a schedule whose prior run is restored at boot is refused `:overlap_live` by the first tick, and names the window it closes.

### BL-264 — the suite's live scheduler fires other modules' residue schedule rows, starting untracked runs mid-suite
- state: open
- type: defect — demonstrated live (seed 70665, two `Aetheris.AdmissionDedupTest` failures)
- area: harness — test environment
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-264.md
- done-when: a `mix test` run starts no run the suite did not ask for — either `Store.ScheduledRunTest` removes the `sched-test-*` rows it inserts, or the suite's scheduler does not act on rows a test left behind; and the run directories such starts leave under `priv/runs/` are named as in or out of BL-261b's retention scope. A test asserts that a `HarnessRestart.with_file_store/1` round trip starts no scheduled run.

### BL-265 — a default or inherited `max_duration` bound for unattended scheduled runs
- state: open
- type: gap — deferred by the arbiter at BL-262, not demonstrated live
- area: harness — scheduler / watchdog
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-265.md
- done-when: a ruling states whether a scheduled run that sets no `max_duration` gets a bound, and from what; before any such bound lands, the ruling records whether any legitimate run (m13 persistent agents especially) lives longer than the intended default, and how boot resume grandfathers a run that was admitted unbounded — the watchdog measures from the original start, so a default applied on resume retroactively bounds a parked run; if a bound lands, a test asserts an unattended run without `max_duration` is bounded and a previously-unbounded resumed run is treated as the ruling says.

### BL-268 — terminal transitions are not final: events and status writes follow the first terminal write
- state: open
- type: defect
- area: harness — Agent.Server / execution loop
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-268.md
- done-when: _(proposed)_ no event is appended to a run after its first terminal status write, or each remaining case is documented as intended; each item in the evidence has a regression test or a recorded disposition.

### BL-269 — multiple VMs write one store: every CLI command boots its own Store, Scheduler and sweep on the same file
- state: open
- type: defect
- area: harness — Store / Scheduler / Sweep
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-269.md
- done-when: _(proposed)_ each multi-VM hazard in the evidence is either prevented (single-writer enforcement or cross-VM coordination) or documented as an unsupported deployment with a guard; tests or recorded dispositions for each.

### BL-270 — a busy read crashes the singleton Store: `collect_rows/3` has no `:busy` arm
- state: open
- type: defect
- area: harness — Store
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-270.md
- done-when: _(proposed)_ a busy read returns an error to the caller instead of crashing Store, with a test.

### BL-271 — a terminal worker `:DOWN` never notifies waiters or the agent tree
- state: open
- type: defect
- area: harness — Agent.Server
- priority: unset — the arbiter's · size: S _(proposed)_
- evidence: docs/evidence/BL-271.md
- done-when: _(proposed)_ a run driven terminal by a worker `:DOWN` notifies the same surfaces as `{:run_failed, _}`; a test asserts a parent waiting on `agent_done` is woken when its child's worker dies.

### BL-272 — Rig infers run completion from `run_complete` on the poll path
- state: open
- type: defect
- area: rig — harness views (`useRunEvents`, RunList EventsContent)
- priority: unset — the arbiter's · size: unset
- evidence: docs/evidence/BL-272.md
- done-when: _(proposed)_ both sites take completion from the run row's status (`TERMINAL_STATUSES`, `useHarness.ts:141`), or from a stream control frame where one is present, and neither reads `run_complete` as a status.

### BL-273 — stale `server.ex:` line citations across Rig source, one of them a false claim
- state: open
- type: defect
- area: rig — source comments citing harness `lib/aetheris/agent/server.ex`
- priority: unset — the arbiter's · size: S _(proposed)_
- evidence: docs/evidence/BL-273.md
- done-when: _(proposed)_ every `server.ex:` citation in `rig/src` and `rig/src-tauri/src` names its anchor with the line as a parenthetical and resolves at the harness commit it cites; `useTrajectory.ts`'s write-result sentence states what `run_outcome/2` does.
