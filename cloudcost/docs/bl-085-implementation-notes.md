# BL-085 — cloudcost credentials + per-launch provider in Rig (implementation notes)

Docs-only. No source file changed, deliberately — the ticket's two open questions both resolved
to "the mechanism already exists." These notes carry what does not survive in the runbook: why the
peel-off trigger did not fire, the code-trace that replaces a live test for the parts a live test
cannot reach, why the live proof was run on DigitalOcean rather than AWS, and the one deliverable
that resolved to "do not build it."

---

## The peel-off trigger did not fire

BL-085 carried a pre-agreed trigger: *"if per-run provider selection needs a NEW Rig
launch-parameter concept, it becomes a milestone, not a ticket."* The row's premise was that
"a per-launch value has no home in single-valued global agent config today."

**That premise was false at the time it was written.** `orchestrate_start` has accepted
`extra_env: HashMap<String, String>` since rig-p9 t1 (`rig/src-tauri/src/commands/orchestrate.rs:13`),
injects it *after* the agent-config loop so a per-run value wins on key collision, and persists it
nowhere — the comment at `:61-63` says so explicitly. The operator-facing control ships too: the
"Additional env vars" panel at `OrchestratorView.tsx:126-128` (state), `:186-236` (the KEY/value
rows), `:143-148` (serialisation), `:139-141` (cleared on terminal phase).

So the concept, the precedence rule, the non-persistence and the UI were all already in place. The
trigger fired on the *other* half of the row — the **direct, non-LLM door** — which is a genuinely
absent thing and is now **BL-094**.

**Why the row got this wrong is worth recording:** the row reasoned from the nearest precedent it
knew, `PAYSLIP_MONTH` in `agentConfigDefs.ts:38`, and correctly identified that as an
anti-pattern. It did not know there were *three* mechanisms, not one:

| # | Mechanism | Per-run? | Chosen by |
|---|---|---|---|
| a | Static row in `agentConfigDefs.ts` | no — global, persisted | operator, between runs |
| b | Planner `params` → `System.put_env` (`agents/orchestrator.exs:272-273`, restored `:295-298`) | yes | an LLM parsing free text |
| c | `extra_env` → "Additional env vars" | yes | operator, explicitly, per launch |

Only (a) is the anti-pattern. BL-085 lands on (c). The payslip rows still sit in (a) while
`rig/docs/runbook.md:316-317` describes them as (b) — filed as **BL-093**.

---

## Plumbing proof — how `CLOUDCOST_PROVIDER` reaches the pipeline

Six links, each opened at HEAD:

1. **Panel → command.** `serializeExtraEnv()` drops blank-key rows and trims
   (`OrchestratorView.tsx:143-148`) → `start(request, serializeExtraEnv())` at `:242` →
   `invoke('orchestrate_start', { request, extraEnv, scriptPath })`
   (`rig/src/hooks/useOrchestrator.ts:88`).
2. **Command → process env, per-run wins.** `orchestrate.rs:57-59` writes the whole agent-config
   map onto the `Command`; `:64-66` then writes `extra_env` over it. Last write wins, so a stored
   `CLOUDCOST_PROVIDER` is overridden by the typed one, never the reverse.
3. **Process.** The non-`.py` branch spawns `mix run <agents/orchestrator.exs>`
   (`orchestrate.rs:46-49`) — the planner — so that env is the BEAM's OS environment.
4. **Planner → run.** Each planned step is started in-process:
   `RunHelpers.load_agent_file(agent_path)` → `Aetheris.start_run(config)`
   (`agents/orchestrator.exs:287-289`). No new OS process, so no env boundary is crossed.
5. **Harness → tool subprocess.** The worker port sets **no `:env`** —
   `port_options/1` returns `[:binary, :exit_status, {:packet, 4}, {:cd, …}]`
   (`../aetheris/lib/aetheris/worker/client.ex:132-140`). `run_command` subprocesses therefore
   inherit the BEAM environment unchanged.
6. **Script.** `fetch_aws.py:229-250` (`load_credentials`) and `fetch_do.py:200-206`
   (`load_token`) read their keys from `os.environ`.

`CLOUDCOST_PROVIDER` itself never travels that far: it is read at **eval time**, in the planner's
own BEAM process, at `cloudcost/agents/cloudcost_orchestrator.exs:42` — before a run exists. That
is why it must be an env var and could not be a `RunConfig` field.

---

## Non-leak — the structural half

Credentials cannot reach `config_json`, independent of any run:

- The `runs` table has six columns and no env/params column — `run_id, status, config_json,
  started_at, finished_at, label` (`../aetheris/lib/aetheris/store.ex:800-808`).
- `RunConfig` declares `env: %{}` (`../aetheris/lib/aetheris/run_config.ex:81`, typespec `:195`)
  and **nothing in `lib/` consumes it**. It serialises as `{}` and is applied to no process. (The
  `env` at `run_config.ex:124` is the unrelated MCP `stdio_config` key — a different field with the
  same name, which is exactly the kind of near-miss the Cited-means-read rule exists for.)
- `cloudcost_orchestrator.exs` puts no credential into the `RunConfig`. Its AWS check reads
  `CLOUDCOST_AWS_ACCESS_KEY_ID` / `_SECRET_ACCESS_KEY` for **presence only** — `System.get_env(name)
  in [nil, ""]` at `:64-65`; the value is never bound to a variable, let alone emitted.

Confirmed empirically below: the live run's `config_json` carries `"env": {}`.

---

## Non-leak — the live half, and why DigitalOcean

**Substitution, stated plainly.** The acceptance asked for a read-only **AWS** run. This
environment has no `CLOUDCOST_AWS_ACCESS_KEY_ID` / `_SECRET_ACCESS_KEY`, so that leg could not be
run here. It does have `CLOUDCOST_DO_TOKEN`, so the live leg is **DigitalOcean**. What that proves
and does not prove is delimited below; the AWS leg remains owed.

**Run:** `cloudcost-orch-digitalocean-TW2-sA`, 2026-08-04, status `:done`, output
`cloudcost/output/digitalocean/cloudcost_report_2026-08.html` (14,532 B). Launched **without** the
hermetic prefix, with bare `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` exported and
`~/.aws/credentials` present — i.e. deliberately in the Rig-launched "no belt, poison present"
posture, not the sprint's hermetic one.

| Check | Result |
|---|---|
| `CLOUDCOST_` key names in trajectory (39,488 B) | 0 |
| `CLOUDCOST_DO_TOKEN` value in trajectory | 0 |
| bare `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` values in trajectory | 0 / 0 |
| `CLOUDCOST_` key names in `config_json` (4,944 B) | 0 |
| `CLOUDCOST_DO_TOKEN` value in `config_json` | 0 |
| `RunConfig.env` as serialised | `{}` |

**The zeros are non-vacuous.** Both greps were run against a file that *did* contain the token and
returned 1 each; the token variable is 71 characters, not empty. Without that step a zero would be
indistinguishable from a misspelled variable matching nothing — the `DO_TOKEN_ECHO` carrier named
in the harness `CLAUDE.md`. The probe file was deleted.

**Why a shell-launched run is representative of a Rig-launched one.** Two facts close the gap:

1. The trajectory recording path is identical. Rig does not record runs; the harness does. Rig
   spawns `mix run`, and everything downstream — `Aetheris.start_run`, the trajectory writer, the
   `runs` row — is the same code on both paths. There is no Rig-specific recording branch to differ.
2. Rig's env injection writes to a `std::process::Command` and logs nothing
   (`orchestrate.rs:57-66` — the whole loop is two `cmd.env(key, value)` calls, no `log::`, no
   trajectory write). Env set this way is invisible to the harness as *data*; it is only ever the
   process environment. So a clean shell-run trajectory implies a clean Rig-run trajectory.

**What the live leg does NOT prove**, and is honestly owed:

- The AWS adapter authenticating with a read-only `CLOUDCOST_AWS_*` key (no such key here).
- The `extra_env` panel → `orchestrate_start` wiring end-to-end. That is a Tauri GUI action over
  in-process IPC; it has no HTTP or CLI entry point (verified: `orchestrate_start` appears only at
  its definition `orchestrate.rs:9`, its registration `lib.rs:78`, and the single `invoke` at
  `useOrchestrator.ts:88` — Rig has no server, and `reqwest` is a client used by `playground.rs` to
  call *out*). It is the operator's single click, and it is the one thing a shell run structurally
  cannot stand in for.

When that Rig run happens, grep its trajectory the same way and add the row to
`runbook.md` §"D2 posture" beside this one.

---

## The D2 guard, demonstrated rather than asserted

The runbook previously said the belt was suspenders-only and the suspenders hold. That was true but
untested in the condition that matters. Run in the exact poisoned posture — bare AWS keys exported,
`~/.aws/credentials` present, no `env -u`:

```
$ CLOUDCOST_PROVIDER=aws mix run --eval \
    'Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")'
** (RuntimeError) CLOUDCOST_PROVIDER=aws requires CLOUDCOST_AWS_ACCESS_KEY_ID and
CLOUDCOST_AWS_SECRET_ACCESS_KEY to be set. …never falls back to boto3's default credential chain.
                                                                        # exit 1
```

The orchestrator refused rather than silently authenticating with the ambient credential. This is
the eval-time raise (`cloudcost_orchestrator.exs:62-73`); the adapter-level guard is the explicitly
constructed session at `fetch_aws.py:301-310`, which supplies the `CLOUDCOST_AWS_*` keys directly
(read at `:229-250`) *and* nulls botocore's `profile` session var — so neither the ambient env chain
nor `~/.aws` is reachable. Shadowing vars are read solely to warn (`:257`). Two independent layers,
both now observed failing closed.

Note the control: the same command with `CLOUDCOST_PROVIDER` unset evaluates clean and exits 0 —
the raise is keyed to the provider selection, not to the environment being poisoned.

---

## Config surface — dynamic-only, confirmed; no `agentConfigDefs.ts` change

BL-084 left this as a live-only open item. It is closed by trace, and the trace is short:

- `SettingsRoute.tsx:18` passes `inventory?.env_deps ?? []` into the tab.
- `AgentConfigTab.tsx:184-189` excludes keys already in `AGENT_CONFIG_DEFS`, appends the rest, and
  derives the group list from the **merged** array. Dynamic defs are structurally identical to
  static ones downstream — `EnvDep` (`tools.rs:6-13`, TS mirror `hooks/types.ts:421-427`) is
  assignable to `Omit<AgentConfigEntry,'value'>`.
- Group header: `:109-113` renders `{group}` verbatim inside a CSS `uppercase`, so manifest
  `"cloudcost"` displays as **CLOUDCOST**, consistent with the static title-case groups.
- Masking: `:114-126` passes `masked={def.masked}` into `ConfigRow`, which sets
  `type={masked && !visible ? 'password' : 'text'}` (`:42`) plus an Eye/EyeOff toggle (`:50-61`).

So a static group would be duplication, not polish — and worse than neutral: the merge at `:186` is
a hard *exclusion*, not a field-level merge, so a static entry would silently discard the
manifest's label, group, masked and placeholder for that key. **Decision: dynamic only.**

Precision on "dotted": obscuring is browser-native `type="password"`. The literal `••••••••` at
`:46` is the placeholder shown when a value is set, and it renders for masked and unmasked rows
alike (`isSet` at `:30` does not consult `masked`) — it is not the masking mechanism, and reading it
as one would make the check vacuous.

Two known divergences from static rows, neither blocking: `linkPrefix` is static-only (`EnvDep` has
no such field), and Export drops dynamic keys (`useAgentConfig.ts:33-41`) until **BL-091**.

---

## STEP_CONFIG_HINTS — resolved to "do not add an entry"

The ticket made this optional: add a cloudcost provider hint if the surface fits, else say so. It
does not fit, for two independent reasons.

**1 — it would render nothing.** `StepCard` filters hints to keys that are set in *persisted* agent
config and renders those (`OrchestratorView.tsx:83-86`; `configValues` from `useAgentConfig()` at
`:130`). `CLOUDCOST_PROVIDER` lives in `extra_env` and is deliberately not in agent config, so the
hint is filtered out every time. The failure mode if someone "fixes" that by storing it globally is
worse than nothing: the card would display the stale global while the run used the per-launch
override — a displayed value that is not the value the run used.

**2 — listing the credential keys would print them in clear.** The hint list is built as
`` `${k}: ${configValues[k]}` `` and rendered as visible text (`:86`, `:105-111`). A cloudcost entry
naming `CLOUDCOST_AWS_SECRET_ACCESS_KEY` or `CLOUDCOST_DO_TOKEN` would put the secret on the plan
card.

Reason 2 is not hypothetical and not cloudcost-specific: the existing
`payslip/agents/payslip_pipeline.exs` entry already lists `SMTP_PASSWORD` and
`GOOGLE_SERVICE_ACCOUNT` (`:20-30`), so an approved payslip plan card renders those secrets in
clear **today**. Filed as **BL-095** rather than left in prose.

The runbook carries the operator instruction instead, with a note explaining the absence so the
next reader does not re-propose the entry.

---

## What is proven, and by what

| Claim | Proven by |
|---|---|
| `extra_env` is per-run, wins over global, persists nowhere | code (`orchestrate.rs:57-66`) + shipped UI |
| `CLOUDCOST_PROVIDER` reaches the orchestrator | 6-link trace above; eval-time read at `:42` |
| Credentials cannot reach `config_json` | schema (6 columns) + `RunConfig.env` unconsumed + live `"env": {}` |
| Credentials do not reach the trajectory | live DO run, mutation-checked greps |
| The D2 guard holds without the belt | live raise under bare AWS keys + `~/.aws/credentials` |
| Manifest alone renders group + masking | trace `SettingsRoute:18` → `AgentConfigTab:184-189` → `:109-113`, `:41-61` |
| AWS read-only key authenticates from Rig | **not proven** — no AWS key in this environment |
| The panel → `orchestrate_start` wiring end-to-end | **not proven** — GUI-only, operator's click |
