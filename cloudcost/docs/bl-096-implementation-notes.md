# BL-096 — declare the fetch-step timeout (implementation notes)

One-line change in substance: `timeout_ms: 300_000` is now declared on STEP 1 of
`cloudcost/agents/cloudcost_orchestrator.exs` instead of being left to the exec server's
default and rediscovered by the model at runtime. These notes carry the precondition finding
(which is not what the ticket assumed), the framing correction it forces, and one adjacent
claim the edit falsified.

---

## Precondition — there is no step schema, and that changes the claim

The ticket asked to verify that "the RunConfig STEP declaration can PRE-set `timeout_ms`", and
to **stop** if the step schema cannot carry one. The finding is narrower than either branch:

**There is no step schema.** `cloudcost_orchestrator.exs` is a `%Aetheris.RunConfig{}` whose
"steps" are prose blocks inside `system_prompt` (`:160-236` pre-edit). A step declares its call as
literal text the model transcribes:

```
STEP 1 — Fetch the AWS cost snapshot and inventory.
  run_command  command: "python3"
               args: ["scripts/fetch_aws.py", "--output-dir", "output/aws"]
```

`command:` and `args:` are carried by exactly this mechanism and nothing else. So `timeout_ms:`
can be declared the same way — this is the native declaration channel, not a workaround — and the
edit is a prompt edit.

**Plumbing, traced and already observed.** The exec server reads
`args.get("timeout_ms").and_then(Value::as_u64).unwrap_or(60_000)`
(`../aetheris/native/aetheris_exec_server/src/main.rs:469-472`; advertised in the tool schema at
`:123-128`, "Timeout in milliseconds (default: 60000)"). Both citations re-verified at HEAD rather
than inherited from the row — both were correct. The path from `tool_input` to the exec call did
not need inferring: `cloudcost-orch-aws--ez4vQ`'s retry carried `timeout_ms: 300000` and ran
66,991 ms, i.e. well past the 60 s default, so a declared value demonstrably reaches `runner::run`.

### The framing correction

The ticket's stated goal was to put "the model off the success path." **A prompt declaration does
not do that, and it should not be claimed to.** The model still emits the value; a model that
ignores the instruction still fails. What the change actually buys:

- the timeout moves from **discovered by failure** to **stated once**, under the prompt's existing
  rule *"Execute the commands exactly as written"* (`:219` pre-edit) — the same rule that has
  carried `command`/`args` correctly on 9 of 9 recorded runs across both providers;
- the guaranteed 60 s loss disappears;
- the value becomes reviewable, greppable, and diffable instead of living in model behaviour.

The only mechanism that would **structurally** remove the model is `pre_tools`
(`../aetheris/lib/aetheris/run_config.ex:44-47`, field at `:108`) — "tool calls to execute before
the LLM loop begins… eliminating LLM-as-router round-trips for deterministic setup steps." That was
not taken, for three reasons: it restructures STEP 1 out of the agent loop entirely; it would break
this ticket's own Done-when, which counts `fetch_aws` `tool_called` events that a pre-loop call
would not produce; and it is skipped in `:replay`/`:verify` modes, which is a determinism-contract
question of its own. Recorded here as the honest ceiling of what shipped, and as the option if
prompt-adherence ever proves insufficient.

---

## What changed

**`cloudcost/agents/cloudcost_orchestrator.exs`** — one binding, one prompt line, two comments:

- `fetch_timeout_ms = 300_000`, with the measurements, the exec-server citation, the
  determinism-contract cross-reference, and the reason the exec-server default was *not* touched.
- STEP 1 gains `timeout_ms: #{fetch_timeout_ms}` plus an instruction that it is part of the call
  rather than an `args` entry, and that there is never a reason to retry the step with a different
  timeout (closing the behaviour the model previously had to invent).

**One number, both providers.** STEP 1 is shared — `fetch_script` is the only provider-dependent
part — so the single declaration covers `fetch_aws.py` and `fetch_do.py` at once. Measured from
recorded trajectories:

| step | observed | vs 60 s default |
|---|---|---|
| `fetch_aws.py` | 63–67 s (5 runs) | **exceeds** — timed out 5/5 |
| `fetch_do.py` | 8.2–9.3 s (4 runs) | fits, ~6.5× margin |

`fetch_do` is declared defensively, exactly as the ticket asked: not because it needs headroom, but
so completion no longer *depends* on that margin holding as the DO account grows. The other three
steps run in 38–172 ms and were left untouched.

**Not touched: the exec-server default.** A low global default is a fail-fast safety property for
every other script in every use case; per-step declaration is the correct lever for the one step
that legitimately exceeds it. Scope was aetheris-agents only, and stayed there.

---

## Adjacent claim falsified by this edit

The optimization block's comment asserted that with `CLOUDCOST_OPTIMIZATION` unset, "the prompt
this file builds is **byte-for-byte the t3 prompt**." Adding a line to STEP 1 changes the base
prompt in the set and unset cases identically, so that equality is now false.

The **invariant** it was protecting is unharmed — set-vs-unset isolation — and that is what was
re-verified. Holding the provider constant at `aws` and toggling only `CLOUDCOST_OPTIMIZATION`, the
prompts differ by exactly: `four steps`→`five steps`, the STEP 2b block, and render_report gaining
`--optimization-file "<SIGNALS>"` with its replacement note. Nothing else, and STEP 1's
`timeout_ms: 300000` is identical in both.

The first attempt at that check varied the provider *and* the flag, which conflated provider
substitution with optimization isolation and would have "passed" while proving nothing about either.
Re-run with the provider pinned. The comment was corrected in the same commit rather than left as a
silent mismatch — the equality claim is now stated as superseded, with the invariant restated as
what it actually is.

No test or sprint assertion depended on the byte-for-byte wording (`grep` over `cloudcost/tests/`
and `sprint.sh`); the `m2-t4` notes reference is past-tense design rationale about step *numbering*
and remains accurate, so it was left alone.

---

## Verification

**Offline — done:**

- Agent file evaluates clean on both branches; the declaration is present in the rendered prompt
  (`timeout_ms: 300000`) for DO-default and AWS.
- Isolation invariant re-verified with the provider pinned (above).
- `python3 -m pytest cloudcost/tests/` — full suite.
- Plumbing confirmed by trace plus the live 66,991 ms observation.

**Offline cannot close this ticket.** The Done-when requires a live AWS run, and the row's five-run
evidence table came from `aetheris/priv/runs/<id>/trajectory.json`, which is gitignored — those rows
are given, not re-derivable from the repo.

**Live acceptance — one AWS run suffices** (the fix is deterministic, so a single run is
dispositive rather than indicative):

```
cd ~/sandbox/elixirws/aetheris
CLOUDCOST_PROVIDER=aws \
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \
    AWS_SHARED_CREDENTIALS_FILE=/dev/null \
    mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
```

Then, against that run's trajectory:

```
python3 - <<'PY'
import json
t=json.load(open('priv/runs/<run_id>/trajectory.json'))
calls=[e for e in t['events'] if e.get('type')=='tool_called'
       and 'fetch_aws.py' in json.dumps(e.get('payload',{}))]
tos=[e for e in t['events'] if e.get('type')=='tool_result'
     and 'timed out' in json.dumps(e.get('payload',{}))]
print("fetch_aws tool_called:", len(calls), "(expect 1)")
print("timeout events:", len(tos), "(expect 0)")
print("declared timeout on first call:",
      calls[0]['payload']['tool_input'].get('timeout_ms'), "(expect 300000)")
PY
```

Pass = exactly one `fetch_aws` `tool_called`, zero timeout events, and `timeout_ms: 300000` present
on that **first** call — the last check is what distinguishes "the fix worked" from "the run
happened to be fast today".

### Result — `cloudcost-orch-aws-3KU2NQ`, 2026-08-04, PASS

Status `done` in 1 m 18 s; `output/aws/cloudcost_report_2026-08.html` produced.

| check | before (`--ez4vQ`) | after (`3KU2NQ`) | |
|---|---|---|---|
| `fetch_aws` `tool_called` | 2 | 1 | ✅ |
| timeout events | 1 | 0 | ✅ |
| `timeout_ms` on the **first** call | absent → defaulted to 60 000 | 300000 | ✅ |
| tool durations (ms) | 60000, 66991, 49, 47, 134 | 63882, 45, 47, 115 | |
| wall clock | 2 m 18 s | 1 m 18 s | |

The first call carries the declared value and completes in 63.9 s — inside the 63–67 s band
measured before the fix, so the script did not get faster; the call simply stopped being killed at
60 s. The 60 s that used to be spent failing is gone, which is the whole delta in wall clock.

One run is dispositive here rather than indicative, because the mechanism is deterministic: the
value is in the prompt or it is not, and the trajectory shows which.

**Non-leak re-checked under the settled BL-085 criterion.** All 20 stored agent-config values of
length ≥ 8 grepped against this run's trajectory and `config_json`: zero secret hits. The only
value matches are non-secrets — `AETHERIS_MODEL`, `AETHERIS_PROVIDER`, `CLOUDCOST_AWS_REGION` —
`RunConfig.env` serialised `{}`, and both D2 guard warnings fired
(`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` each once), confirming the run was in the
poisoned-but-guarded posture the criterion expects rather than a trivially clean environment.

---

## Carry-forward (note, not a deliverable)

Provider three's fetch adapter declares its own step timeout explicitly, by this same convention —
so a third adapter does not rediscover the 60 s default the way AWS did. Flagged in
`runbook.md` §"Adding a provider", where an adapter author actually looks, rather than only here.
