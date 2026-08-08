# hc-b2 — implementation notes

**Ticket.** Repair hc-c's specification before hc-c opens. Documentation only.
**Base.** agents `a581a8c`, harness `b4d782a`. **Harness untouched.**
**Naming.** `hc-b2`, on m4's suffixed-sibling precedent (`t1a-p`, `t1a-c`); decision 4 makes it
permanent. hc-b is **closed and not re-opened** — this repairs its artifact, dated, with
superseded wording quoted, per decision 7.

---

## 1. G3 — the reconnaissance, four answers

This was the ticket's real work. Each answer is derived from harness source at `b4d782a` and
named by anchor.

### G3(1) — the agent file

**`../aetheris/agents/ollama_smoke.exs`** — `provider: "ollama"`, `tools: ["list_dir"]`,
`model: "llama3.2:latest"`, `max_steps: 2`.

**How it was established that it spawns a worker, rather than inferred from having a tool.** The
decision is not made from the tool list. `../aetheris/lib/aetheris/agent/supervisor.ex:62–63`
gates the child spec with two negative clauses before a catch-all:

```elixir
defp worker_child_spec(%{provider: "stub", mcp_servers: []}), do: []
defp worker_child_spec(%{tools: [], mcp_servers: []}), do: []
```

`ollama_smoke.exs` matches neither — its provider is not `"stub"` and its `tools` is not `[]` —
so it reaches the catch-all, which builds a `Worker.Supervisor` child. **A tool in the definition
is genuinely not the same as a worker starting**, which is what the ticket warned about: an
`anthropic` agent with `tools: []` starts no worker, and a `stub` agent starts none whatever its
tools.

### G3(2) — the observable that proves a worker started

**The trajectory meta's `"containment"` key, non-nil.**

`../aetheris/lib/aetheris/agent/server.ex:962` — `defp worker_containment(nil), do: nil`, whose
own comment at `:960` reads *"Nil when no worker ran at all (stub/no-tools runs never start one)
— distinct from a worker that ran without containment, which reports `seccomp: false`."*
`:678` writes `"containment" => containment` into the meta map that
`Aetheris.Trajectory.File.write/3` persists.

Chosen over a log line deliberately: it is durable, it is in the trajectory rather than in a
stream whose routing is the very thing under test, and it distinguishes *no worker* from *worker
without containment* — which a `[sandbox]`-line count cannot.

### G3(3) — what a `[sandbox]` line is, verbatim, and where it comes from

**Every one is an `eprintln!` in the Rust worker.** Sixteen call sites across
`../aetheris/native/aetheris_worker/src/sandbox.rs` and `main.rs`.

The five in `main.rs` (`:88`, `:94`, `:114`, `:117`, `:153`) are **all failure paths** —
namespace entry failed, cgroup setup failed, overlay setup failed, overlay init missing fields,
seccomp filter failed. **A clean run emits none of them**, which is why an emptiness test alone
proves nothing.

The success-path lines are in `sandbox.rs`, and on Linux at least two fire on a successful start:

- `:213–220`, unconditional once namespaces are entered —
  `"[sandbox] entered {} namespaces (uid={uid}, gid={gid}); network namespace {}"`, with
  `entered.join("+")` and `"established"` / `"not requested"`.
- one of the cgroup pair — `:574`
  `"[sandbox] cgroup configured: memory={memory_limit_bytes}B cpu={cpu_quota_pct}%"` on success,
  or `:537` `"[sandbox] cgroup delegation unavailable; continuing without resource limits"` when
  delegation is unavailable. Both are `[sandbox]` lines, so one fires either way.

**Where they land.** `../aetheris/lib/aetheris/worker/client.ex:133–140`:

```elixir
def port_options(sandbox_path) do
  [:binary, :exit_status, {:packet, 4}, {:cd, resolve_sandbox_path(sandbox_path)}]
end
```

**No `:stderr_to_stdout`.** The worker's stderr is therefore *inherited* from the BEAM rather than
captured by the port, and should reach the CLI's fd 2. Two consequences worth stating:

1. `[sandbox]` lines **never pass through Logger**. They are a child process writing to an
   inherited descriptor. So BL-105's Logger-reconfiguration arms do not move them, and could not
   have.
2. **This is a derivation from source, not an observation.** It is exactly the kind of claim this
   round refuses to bank, so the gate still runs and can refute it. A refutation would be the more
   interesting result.

### G3(4) — credentials: the gate is credential-free but not free

**hc-b's premise is refuted at source, and this is the ticket's largest finding.** hc-a costed the
gate as *"a stub-provider run with a worker … cheap and needs no API key"*, and hc-b authored it
that way. `supervisor.ex:62` makes that configuration **impossible**: a stub-provider run with no
MCP servers never starts a worker, whatever its `tools:` list. So Finding B was worse than a
placeholder — **no agent file could have satisfied the authored gate**, because the disqualifier
was the provider, not the missing path.

The routes that do spawn a worker, enumerated from the three clauses:

| Route | Worker? | Cost |
|---|---|---|
| non-stub provider **and** non-empty `tools` | yes | a live provider |
| `stub` provider **and** non-empty `mcp_servers` | yes (clause 1 requires `mcp_servers: []`) | free — **but no such agent file exists** |
| anything else with non-empty `mcp_servers` | yes | depends on provider |
| `stub` + `mcp_servers: []` | **no** | — |
| any provider + `tools: []` + `mcp_servers: []` | **no** | — |

**No agent file in `../aetheris/agents/` uses `provider: "stub"`** — all twenty use `anthropic`,
`ollama` or `gemini` — so the free route exists in the code and not in the repo. Taking it would
mean authoring a new agent file, which is hc-c's work and not this ticket's.

**What makes the gate runnable without a credential is the local Ollama**, verified on this
machine: the binary is present, `http://localhost:11434/api/tags` answers `200`, and
`llama3.2:latest` is among the three models served. So the gate needs **no API key** but does need
**a live local model server**, which is an environmental dependency the gate now states and checks
first.

`ANTHROPIC_API_KEY`, `GEMINI_API_KEY` and `OPENROUTER_API_KEY` are present in this environment
**by name only** — checked with `[ -n "${VAR+x}" ]`, never read, never sent anywhere.

**None of G3's four was left unestablished**, so the ticket proceeded.

---

## 2. Item 1 — the gate, rewritten so it can fail

All four properties are in the document and each is visible:

**(a) Named agent, no placeholder.** `agents/ollama_smoke.exs`, with the supervisor clauses
quoted as the reason it spawns a worker, and the Ollama precondition stated as a check that runs
first. A failed precondition is recorded as *the gate could not run* — deliberately **not** a
verdict, because a precondition failure and an experimental result are different facts.

**(b) Positive control, first and separate.** `containment` non-nil, then total `[sandbox]` count
≥ 1, both before the routing question is asked at all.

**(c) One invocation, streams separated.** `> stdout.txt 2> stderr.txt`. The prior text said
*"over the same run"* while showing two invocations.

**(d) A verdict for every observation**, five rows, including the two that stop the ticket:
`containment` nil is *no worker ran*; count 0 is **`inconclusive`, a gate failure**, with the
question explicitly staying open in §Not established rather than being resolved on the likelier
reading. The both-streams row is included because *two emitters* is a real outcome an arm could
half-fix.

The anti-vacuity property is written into the gate's own text: **the positive control is the only
thing that makes *routes to stderr* distinguishable from *nothing was emitted***, and *nothing was
emitted* is what m4 produced.

## 3. Item 2 — the gate's home

The gate is now a **named construct after the seven §6 fields**, headed *"Step-1 gate — decision
3, not a §6 field"*, in both hc-c and hc-d. `Done-check` keeps only what runs after the work — in
hc-c's case it is now wholly R13-marked, since the gate half was the only part that was ever
authorable.

**Why hc-b got this wrong, stated rather than defended.** hc-b had just recorded that listing the
step-1 gate as a §6 obligation *"would have manufactured an authority"*, and over-corrected by
hiding it inside an existing field. **§6 governs what §6 owes, not what this document may
contain.** Decision 3 is a real authority that is simply not §6's. The tell was in the authored
text itself: it had to say *"a step-1 gate failure stops the ticket without an edit"* in prose, to
undo the semantics of the field it had been placed in.

**hc-d's dangling resolver is repaired by marking, not authoring.** Its R3 paragraph resolved to
*"this ticket's step-1 gate"*, which existed in no document. hc-d's design is not done, so the
gate cannot be written; authoring one now would be the guess R13 forbids. It is marked with its
real resolver — hc-d's own opening section-scoped edit, per R12 — and **R13 gains the reading that
makes this a rule application rather than a judgement call**: *a resolver names something that
exists; a pointer to an unauthored artifact is a guess wearing a citation's clothes.* No new rule.

## 4. Item 4 and §5's observation

hc-c's `Claude-code prompt` is authored in the document, so the relayed ticket becomes a pointer
(R12). Content is the reviewer's; formatting is this file's (decision 11).

§5's closing observation is recorded **beside R13**, where a later reader meets it while deciding
whether to mark a slot: **R13 flags known uncertainty, and known uncertainty is safe.** Every
R13-marked slot in hc-c was sound; every defect was in the one slot hc-b completed confidently.
Review effort follows confidence, not deferral.

## 5. Deviations, and what this ticket did not do

- **No hc-c work.** No agent file authored, no gate run, no arm chosen, no harness code touched.
- **No new backlog row.** The stub-plus-worker impossibility is a fact about the harness recorded
  here and in the gate's text, not a defect in it — the clauses are deliberate.
- **hc-b is not re-opened.** Every edit to its artifacts is dated `hc-b2` with the superseded
  wording quoted beneath, per decision 7.
- **One thing left open on purpose.** Whether a `stub` + non-empty `mcp_servers` agent would be a
  better gate subject than a live Ollama — it would remove the model-server dependency — is not
  decided here. It needs an agent file, which is hc-c's to write if hc-c wants it, and the current
  gate runs without one.
