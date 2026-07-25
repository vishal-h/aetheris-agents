# BL-039 scout — fork continuation against real providers

Read-only reconnaissance. **No source, test, or contract change.** This memo exists so
the BL-039 design decision is made against verified state rather than against the
backlog row's citations, which predate BL-028 and have moved.

**Pinned at:**

| repo | HEAD | tree |
|---|---|---|
| `aetheris-agents/` | `b1d9ccc` | clean |
| `../aetheris/` (harness) | `da25e01` | clean |

Every `file:line` below was read at those commits. Recorded payloads are quoted from
real trajectory files on this machine, not reconstructed from sibling shapes.

---

## 1. Reconstruction at HEAD — `Fork.event_to_messages/1`

`../aetheris/lib/aetheris/execution/fork.ex`. The function is still named
`event_to_messages/1`. Three clauses, `:88-111`.

### 1a. The `:llm_responded` clause — `fork.ex:88-99`

```elixir
  defp event_to_messages(%{type: :llm_responded, payload: payload}) do
    case Map.get(payload, "response_type") do
      "text" ->
        case Map.get(payload, "raw_response") do
          nil -> []
          content -> [%{"role" => "assistant", "content" => content}]
        end

      _ ->
        []
    end
  end
```

**Emits:** exactly one message, `%{"role" => "assistant", "content" => <string>}`, and
only when `response_type == "text"` **and** `raw_response` is non-nil.

**Drops:** every other response type. The catch-all `_ -> []` is at **`fork.ex:96-97`**
(the row cites `:95-96` — off by one, pre-BL-028). For a `tool_call` response this
drops `tool_name`, `tool_input`, and the whole turn: nothing is emitted at all. A
`"text"` response with a nil `raw_response` is also dropped (`:92`).

### 1b. The `:tool_result` clause — `fork.ex:101-109`

```elixir
  defp event_to_messages(%{type: :tool_result, payload: payload}) do
    tool_name = Map.get(payload, "tool_name", "")
    # Worker/MCP dispatch writes the payload under "output" (loop.ex:537, :553,
    # :570); the in-process family and the tool-error path write "result"
    # (loop.ex:354 and :424-508). Read "output" first — it stays authoritative
    # when present, so a genuinely empty worker result is not overridden.
    output = normalize_content(Map.get(payload, "output") || Map.get(payload, "result"))
    [%{"role" => "tool", "tool_name" => tool_name, "content" => output}]
  end
```

**Emits:** `%{"role" => "tool", "tool_name" => ..., "content" => <string>}` at
**`fork.ex:108`** (the row cites `:104`).

**Correction to the row's quoted body.** The row quotes
`output = Map.get(payload, "output", "")`. That is the **pre-BL-028** body. At HEAD the
line is `:107` and reads `normalize_content(Map.get(payload, "output") || Map.get(payload, "result"))`
— BL-028 landed the `"output"`/`"result"` key fix plus `normalize_content/1`
(`fork.ex:117-125`, which JSON-encodes non-binary results). The row's sequencing note
("Land BL-028 (b2) first") is satisfied: BL-028 is in.

**Correction to the row's "only site" claim.** The row states *"This is the only
`"role" => "tool"` site in the tree."* **False at HEAD.** Four sites in `lib/`:

| site | direction |
|---|---|
| `fork.ex:108` | writes `role: "tool"` **into** the canonical transcript |
| `openrouter.ex:97` | translates canonical → OpenAI wire (`tool_call_id`) |
| `gemini.ex:153` | translates canonical → Gemini wire (`tool_call_id`) |
| `ollama.ex:260` | translates canonical → Ollama wire (`tool_call_id`) |

The precise true statement: `fork.ex:108` is the only site that *produces* a
`role: "tool"` message in the **canonical** (Anthropic-shaped) transcript. The other
three consume a canonical `%{"role" => "user", "content" => [%{"type" => "tool_result",
"tool_use_id" => id, ...}]}` block and emit their provider's `role: "tool"` form. This
matters for the design: **the canonical transcript shape is the Anthropic shape, and
the three non-Anthropic adapters already translate out of it.** Reconstruction that
produces canonical blocks feeds all four providers; the current `role: "tool"` message
feeds none of them correctly — `openrouter.ex:79-81` matches it on the binary-content
clause and passes `role: "tool"` through with **no `tool_call_id`**, which OpenAI-shaped
endpoints also reject.

### 1c. Catch-all — `fork.ex:111`

```elixir
  defp event_to_messages(_event), do: []
```

`:tool_called` events (which *do* carry `tool_name` + `tool_input`) contribute nothing.

---

## 2. Feasibility gate — does the recorded payload retain enough?

**Recorded site.** `loop.ex:277-293`, the non-text branch of `handle_llm_response/4`
(the `:text` branch at `:247-263` is byte-identical in its payload keys):

```elixir
      append_event(log_pid, config.run_id, step, :llm_responded, %{
        "response_type" => Atom.to_string(response.type),
        "raw_response" => Map.get(response, :content, nil),
        "tool_name" => Map.get(response, :tool_name, nil),
        "tool_input" => Map.get(response, :tool_input, nil),
        "latency_ms" => response.latency_ms,
        "resolved_model" => Map.get(response, :resolved_model),
        "system_fingerprint" => Map.get(response, :system_fingerprint),
        "input_tokens" => Map.get(response, :input_tokens),
        "output_tokens" => Map.get(response, :output_tokens),
        "cost_usd" => Pricing.compute_cost(...)
      })
```

**`tool_use_id` is not in that map.** The adapter response carries it —
`anthropic.ex:215`, `tool_use_id: Map.get(tool_block, "id")` — and the live loop reads
it back off the response struct at `loop.ex:364` / `:374`. It is never written to an
event.

**Real recorded payload.** `../aetheris/priv/runs/payslip-orch-a7Vi3A/trajectory.json`
— the exact parent named in the BL-039 row (`provider: anthropic`, `model:
claude-haiku-4-5-20251001`, `mode: record`). Step 0, seq 2, `llm_responded`, verbatim:

```json
{
  "cost_usd": 0.0017328,
  "input_tokens": 1526,
  "latency_ms": 2152,
  "output_tokens": 128,
  "raw_response": null,
  "resolved_model": "claude-haiku-4-5-20251001",
  "response_type": "tool_call",
  "system_fingerprint": null,
  "tool_input": {
    "args": [
      "scripts/generate_employee_payslips.py",
      "--csv",
      "data/payroll.csv"
    ],
    "command": "python3",
    "timeout_ms": 300000
  },
  "tool_name": "run_command"
}
```

Complete payload — all ten keys, nothing truncated.

**Verdict on the gate:**

| needed to rebuild a `tool_use` block | present? |
|---|---|
| tool **name** | **yes** — `"tool_name": "run_command"` |
| tool **input** | **yes** — `"tool_input": {…}`, full arguments |
| tool_use **id** | **no** — key absent from the payload entirely |

So reconstruction of the *content* of an assistant tool-call turn is feasible from the
record. The **id is not recoverable** and would have to be synthesised at fork time
(the same synthetic-id device `openrouter.ex:219` and `ollama.ex:181` already use for
providers that don't supply one). Note also `"raw_response": null` on a tool-call step:
any assistant text accompanying the tool call is *not* recorded either, so a
reconstructed turn is tool_use-only.

---

## 3. Pairing — is the link real or positional?

Same step, same run, seq 4, `tool_result` payload verbatim (the `output` string is
~1.6 KB of the script's JSON; elided in the middle only, marked):

```json
{
  "fs_hash": null,
  "output": "{\"duration_ms\":5692,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"Generated 1 payslip(s) for BTL_015.\\n  2026-05-Payslip.html\\n … [1.4 KB elided] … \\n\\nDone: 18 employee(s), 18 payslip(s) generated.\\n\"}",
  "tool_name": "run_command"
}
```

Three keys: `fs_hash`, `output`, `tool_name`. **No `tool_use_id`.** Confirmed against
the writers — `loop.ex:580-585` (`exec_server_payload/2`), `:610-615` (worker
`dispatch_tool/3`), `:548-552` (`dispatch_mcp_tool/4`), `:593-598` (Echo), and the
error path `:358-362` — none of the five write a `tool_use_id`.

**The link is positional only:** `(run_id, step)`, plus seq order within the step. The
`llm_responded` at step *N* and the `tool_result` at step *N* are paired by sharing *N*,
nothing else.

**Can one `llm_responded` hold more than one tool_use?** No.
`anthropic.ex:207` takes the **first** `tool_use` block only:

```elixir
    tool_block = Enum.find(content_blocks, fn b -> Map.get(b, "type") == "tool_use" end)
```

`Enum.find/2`, not `Enum.filter/2` — so a multi-tool-use API response is collapsed to
one call and the rest are silently discarded before any event is written. Downstream,
`loop.ex:307-339` dispatches exactly one tool and appends exactly one `:tool_result`
per step.

Corroborated empirically: across 91 trajectories (`payslip-orch-*` plus 40
`docbuilder-*`), 537 steps carry a `tool_result` and **0 steps carry more than one**.

Consequence for the design: ordering is not a problem to solve. One step ⇒ at most one
`(tool_use, tool_result)` pair, and step order is the transcript order.

---

## 4. Target shape — what reconstruction must produce

**Correction to the ticket's framing.** `anthropic.ex build_request_body/2`
(`anthropic.ex:136-156`) does **not** render tool_use or tool_result blocks. It passes
the message list through untouched:

```elixir
    body = %{
      "model" => Map.fetch!(request, :model),
      "max_tokens" => Map.get(config, :max_tokens) || @default_max_tokens,
      "system" => Map.fetch!(request, :system_prompt),
      "messages" => Map.fetch!(request, :messages)
    }
```

The shape is authored one layer up, in the **live loop**, and `build_request_body/2`
serialises it verbatim. So the structure reconstruction must produce is defined by
`loop.ex:1116-1152`:

**(a) assistant turn with a `tool_use` block** — `loop.ex:1116-1127`:

```elixir
  defp assistant_tool_use_message(response, tool_use_id) do
    tool_use_block =
      %{
        "type" => "tool_use",
        "id" => tool_use_id,
        "name" => response.tool_name,
        "input" => response.tool_input || %{}
      }
      |> maybe_put_thought_signature(Map.get(response, :thought_signature_blob))

    %{"role" => "assistant", "content" => [tool_use_block]}
  end
```

**(b) user turn with a `tool_result` block** — `loop.ex:1132-1152`:

```elixir
  defp tool_result_message(tool_use_id, output, is_error \\ false) do
    content_block = %{
      "type" => "tool_result",
      "tool_use_id" => tool_use_id,
      "content" => output
    }

    content_block_with_error =
      if is_error do
        Map.put(content_block, "is_error", true)
      else
        content_block
      end

    %{
      "role" => "user",
      "content" => [
        content_block_with_error
      ]
    }
  end
```

**The pairing rule the live loop enforces.** `loop.ex:374-377` (success) and `:364-368`
(tool error) build both messages from **one** `tool_use_id` read off the same response,
and push them adjacently onto the reversed message list:

```elixir
        tool_use_id = Map.get(response, :tool_use_id)
        assistant_msg = assistant_tool_use_message(response, tool_use_id)
        tool_result_msg = tool_result_message(tool_use_id, output)
        {:ok, [tool_result_msg, assistant_msg | messages], updated_history}
```

So the invariant is: **`tool_result.tool_use_id` equals the `id` of a `tool_use` block
in the immediately preceding assistant turn**, and the two turns are adjacent. The id
is opaque to the harness — the live path never validates it, it only has to be
*consistent between the pair*. That is what makes a synthesised id viable.

**One constraint the design must respect.** `fork_context` is normalised on the way in
by `server.ex:643-649`:

```elixir
  defp normalize_context_entry(%{role: role} = entry) do
    %{role: role, content: Map.fetch!(entry, "content")}
  end

  defp normalize_context_entry(%{"role" => role} = entry) do
    %{role: role, content: Map.fetch!(entry, "content")}
  end
```

Only `role` and `content` survive; **every other top-level key is dropped** (this is
already why `fork.ex:108`'s `"tool_name"` never reaches the wire). `content` is fetched
as-is, so a **list** of blocks passes through intact. Reconstruction must therefore put
everything inside `content` blocks and add no sibling keys.

---

## 5. Contract §4 known limitation — verbatim at HEAD

`../aetheris/docs/aetheris/determinism-contract.md:126-134`:

> **Known limitation (documented, not guaranteed away):** non-text assistant turns
> (tool-call turns) are dropped in reconstruction (`fork.ex:88-111`). The prefix a
> forked run sees is therefore the *text-and-tool-results* transcript, not a
> byte-copy of the source context at step *N*. Changing this is future work and
> requires a doc edit here first.
>
> *Demonstrated consequence (2026-07-20): a fork continuation against the Anthropic
> provider fails at its first LLM call — the reconstructed tool-role message is
> rejected (HTTP 400), and relabeling alone cannot fix it because the paired assistant
> `tool_use` turns are not reconstructed. Stub-provider forks are unaffected.
> Tracked: BL-039 (`../aetheris-agents/docs/backlog-2026-06.md`).*

The `fork.ex:88-111` citation is **still accurate at HEAD** (BL-028 changed the clause
bodies but not the span). The clause's closing sentence — *"requires a doc edit here
first"* — is the docs-first constraint the row's **Size: M** rests on.

**Demonstration, not citation.** The failing run is on disk:
`../aetheris/priv/runs/fork-aa6a6a65804f6645/trajectory.json`, meta `fork_from:
payslip-orch-a7Vi3A`, `fork_step: 0`, `provider: anthropic`. All three events, verbatim:

```
seq 0 step 0 prompt_built   {"message_count": 2, "tool_schema": ["run_command"], "user_prompt": "", "context_hash": "sha256:206f9aa…", "system_prompt": "You are a payslip generation orchestrator…"}
seq 1 step 0 llm_called     {"model": "claude-haiku-4-5-20251001"}
seq 2 step 0 error          {"reason": "\"HTTP 400: messages: Unexpected role \\\"tool\\\". Allowed roles are \\\"user\\\" or \\\"assistant\\\". For instructions on how to use tools, see https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview.\""}
```

`message_count: 2` decomposes exactly as §1 predicts: the source's `meta.user_prompt`
(`"Generate payslips. The script handles all employees automatically."`, 66 chars,
prepended at `fork.ex:74-78`) plus the one `role: "tool"` message from `fork.ex:108`.
The source's step-0 `llm_responded` was `response_type: "tool_call"`, so the
`:llm_responded` clause contributed **zero** messages. Three events, then dead.

---

## 6. Verification hole — the stub queue on a fork

**Correction: the row's citation is mis-attributed.** The row says *"`encode_config`
strips `stub_responses` (`../aetheris/lib/aetheris.ex:372`)"*. At HEAD,
`aetheris.ex:372` is `defp encode_run_config_template(%RunConfig{} = config)`, and its
only caller is `schedule_run/1` at `aetheris.ex:301` (`run_config_json:`). It is the
**scheduled-run** template encoder. It is not on the fork path at all.

**Where a fork actually gets its config** — `Fork.assemble_config/5`,
`fork.ex:127-146`:

```elixir
    base = %{
      run_id: new_run_id,
      mode: String.to_existing_atom(Map.get(meta, "mode", "record")),
      provider: Map.get(meta, "provider", "stub"),
      model: Map.get(meta, "model", "stub-v1"),
      max_steps: Map.get(meta, "max_steps", 10),
      seed: Map.get(meta, "seed"),
      system_prompt: Map.get(meta, "system_prompt", ""),
      user_prompt: "",
      tools: Map.get(meta, "tools", []),
      fork_from: source_run_id,
      fork_step: step,
      fork_context: context
    }

    struct(RunConfig, Map.merge(base, overrides))
```

Every field comes from the **trajectory meta**. `stub_responses` is not in `base`, so
it falls to the `run_config.ex:84` defstruct default `stub_responses: []` — an empty
queue. And it could not come from meta anyway: the meta writer (`server.ex:661-678`)
never records it. Confirmed on both real trajectories read for this memo — meta keys are
`finished_at, fork_from, fork_step, max_steps, mode, model, overlay_changes, provider,
sandbox_path, seed, started_at, step_count, system_prompt, tools, user_prompt`. No
`stub_responses`.

So the *conclusion* the row draws is right — a stub fork begins with an empty queue —
but the mechanism is **absence at construction**, not a strip. (The genuine strip,
`Agent.Server.encode_config/1` at `server.ex:759-767`, drops `stub_responses` before
persisting `config_json` to SQLite; that is why `Application.reconstruct_config/2`
(`application.ex:146-152`) can never recover a queue either — but it is a *resume*-path
fact, not a fork-path one.)

**Demonstration of the vacuous stub success.**
`../aetheris/priv/runs/fork-94c31612127f2009/trajectory.json`, `provider: stub`,
`fork_from: fixture-unlabelled-fork-CbZX6w`, `fork_step: 0`:

```
seq 0 step 0 prompt_built  {"message_count": 2, "tool_schema": ["run_command"], …}
seq 1 step 0 llm_called    {"model": "stub-model"}
seq 2 step 0 llm_responded {"raw_response": "[stub exhausted]", "response_type": "text", "latency_ms": 0, "resolved_model": null, "tool_name": null, "tool_input": null, "cost_usd": null, "input_tokens": null, "output_tokens": null, "system_fingerprint": null}
seq 3 step 0 run_complete  {"reason": "agent_finished"}
```

`[stub exhausted]` is `stub.ex:19-28`'s `@exhausted` constant, returned by the empty-queue
clause `stub.ex:87-89`. Because `@exhausted` is `type: :text`, `loop.ex:243-271` writes
`run_complete{reason: "agent_finished"}` — a **`done`** run that made zero real progress.
Exactly the Silent-wrong-answer shape.

**What a test that actually continues a fork would need.** The good news: the hook
already exists and is already used. `overrides` flows straight into
`struct(RunConfig, Map.merge(base, overrides))`, and `fork_test.exs:245` already passes
a queue through it:

```elixir
    {:ok, config} = Fork.from_step(source_id, 0, %{stub_responses: [stub_resp]})
```

No production change is needed to seed a fork's queue from a test. Three real gaps:

1. That test's `stub_resp` is `type: :text` (`fork_test.exs:236-243`) → terminates at
   step 0. It asserts `fork_from`/`fork_step` meta only, and tolerates failure
   (`assert_run_done(fork_id, …, accept_failed: true)` at `:250`). It proves provenance,
   not continuation. A continuation test needs a **`type: :tool_call`** first response
   plus at least one more queued reply — the harness `CLAUDE.md` "Testing patterns" rule
   already says exactly this.
2. Neither operator entry point can supply overrides beyond a label. The CLI's
   `fork_overrides/1` (`cli/commands/fork.ex:61-66`) builds `%{label: name}` and nothing
   else; Rig invokes that CLI (`rig/src-tauri/src/commands/fork.rs:51-55`). So the
   `stub_responses` path is **test-only by construction** — which is fine for a test, and
   means the "carry it across the fork" option costs nothing in production surface.
3. All ten tests in `fork_test.exs` exercise `from_step/3` in isolation except the one
   above. There is **no test anywhere that drives a reconstructed transcript into an
   adapter's request builder** — which is precisely the seam that failed in the field.
   A `build_request_body/2`-level assertion over a reconstructed fork context would have
   caught this without a network call.

---

## 7. Operator symptom — who owns surfacing it

**Confirmed: the error string carries the sandbox preamble and never the HTTP 400.**

The chain, end to end:

- On a failed fork the CLI's terminal branch is `run_helpers.ex:118-120` →
  `{:error, "run #{run_id} failed"}`. That string carries **no** provider detail; the
  HTTP 400 lives only in the trajectory `error` event (§5).
- `cli/output/formatter.ex:38` prints it: `IO.puts(:stderr, "Error: #{reason}")`.
- The worker has already written the preamble to the same stream —
  `native/aetheris_worker/src/sandbox.rs:213-221`:
  ```rust
      eprintln!(
          "[sandbox] entered {} namespaces (uid={uid}, gid={gid}); network namespace {}",
          entered.join("+"),
          …
      );
  ```
- Rig captures **all** of stderr verbatim — `rig/src-tauri/src/commands/fork.rs:63-70`:
  ```rust
      parse_run_id(&stdout).ok_or_else(|| {
          let stderr = String::from_utf8_lossy(&output.stderr);
          let detail = stderr.trim();
          …
              format!("fork failed: {}", detail)
      })
  ```
- `useFork.ts:36` strips the redundant `fork failed:` prefix; `TrajectoryView.tsx:430`
  re-frames it as `Fork failed: {error}`.

So the operator sees `Fork failed: [sandbox] entered user+mount namespaces (uid=…,
gid=…); network namespace not requested … Error: run <id> failed` — preamble plus a
content-free failure line. The row's characterisation is accurate.

**Ownership.** The defect is *upstream of Rig*: `fork.rs` is doing the right thing
(surface stderr verbatim, never fake a success), and the CLI simply has nothing better
to say — `await_run/2` reports a status, and the reason is only in the trajectory. Any
real fix means the CLI reading the terminal `error` event and putting its `reason` in
the message. That is a CLI/harness change on the fork path, so **BL-039 is the natural
owner**; BL-030 (fork UX / early return) would inherit only the presentation. Recording
this as a scout observation, not a decision.

---

## Summary of corrections to the BL-039 row

The row's *conclusions* all survive. Four of its *citations* do not.

| row claim | status at HEAD |
|---|---|
| `role: "tool"` at `fork.ex:104` | moved → **`fork.ex:108`** |
| `_ -> []` drop at `fork.ex:95-96` | moved → **`fork.ex:96-97`** |
| quoted body `Map.get(payload, "output", "")` | **superseded by BL-028** → `fork.ex:107` now `normalize_content("output" \|\| "result")` |
| "only `role => tool` site in the tree" | **false** — 4 sites; true only of the *canonical* transcript |
| `stub_responses` stripped at `aetheris.ex:372` | **mis-attributed** — that is the scheduled-run template encoder; the fork path never *sets* it (`fork.ex:127-146`) |
| contract §4 cites `fork.ex:88-111` | **still accurate** |
| Layer-1 and Layer-2 analysis; 100% real-provider failure | **confirmed**, demonstrated on disk |

And two facts the row does not state, both load-bearing for the design:

- **`tool_use_id` is nowhere in the record.** Name and input survive; the id does not,
  on either side of the pair. Reconstruction must synthesise it — which is sound,
  because the harness never validates it, only pairs on it.
- **One step ⇒ at most one tool call**, enforced by `Enum.find/2` at `anthropic.ex:207`
  and corroborated over 537 recorded tool steps. Multi-`tool_use` ordering is not a
  problem this design has to solve.

No design proposed; no source, test, or contract file touched.
