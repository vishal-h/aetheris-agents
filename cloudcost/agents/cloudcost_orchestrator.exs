# cloudcost/agents/cloudcost_orchestrator.exs
#
# m1-cloudcost t5 — the report pipeline orchestrator.
# m2-cloudcost t3 — generalized over CLOUDCOST_PROVIDER.
# m3-cloudcost t2 — Linode wired in as provider three.
# m6-cloudcost t2b — GitHub wired in as provider four, the first consumption-class one.
#
# Linear, four stages, ONE provider per run (decision H): the provider is chosen at eval
# time and the run fetches, detects, composes and renders for that provider alone. Two
# providers are two runs and two reports — there is no fan-out and no merge step, which is
# what keeps provider specifics out of the shared machinery downstream of the adapter.
#
#   fetch_{provider}.py → detect_orphans.py → compose_report_data.py → render_report.py
#
# Record-and-deliver: `run_command` is a :contained effect, so there is no verify
# support here (D1). No spawn_agent/wait_for_all — a single provider needs no fan-out.
# No write op, no scheduling. Credentials are env-only (D2): CLOUDCOST_DO_TOKEN,
# CLOUDCOST_AWS_*, CLOUDCOST_LINODE_TOKEN and CLOUDCOST_GITHUB_TOKEN are read by the adapter
# from the environment and never appear in a prompt, an argument, or the trajectory.
#
#   cd ~/sandbox/elixirws/aetheris
#   # DigitalOcean (the default — unchanged from m1):
#   mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
#   # AWS — always through the D2 hermetic prefix (m2 decision C):
#   CLOUDCOST_PROVIDER=aws \
#   env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \
#       AWS_SHARED_CREDENTIALS_FILE=/dev/null \
#       mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
#   # AWS + the exploratory optimization spike (m2 t4) — add CLOUDCOST_OPTIMIZATION=1 to the
#   # line above. Unset, the pipeline and the report are exactly the four-stage ones.
#   # Linode (m3 t2) — the shadow names are Linode's own, not boto3's:
#   CLOUDCOST_PROVIDER=linode \
#   env -u LINODE_CLI_TOKEN -u LINODE_TOKEN \
#       mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
#   # GitHub (m6 t2b) — CLOUDCOST_GITHUB_ORG is optional; unset, the adapter uses the
#   # token's sole organisation membership and refuses to choose between two:
#   CLOUDCOST_PROVIDER=github \
#   env -u GH_TOKEN -u GITHUB_TOKEN -u GITHUB_PERSONAL_ACCESS_TOKEN \
#       mix aetheris run ../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs
#
# A Linode run's artifacts are named for the month the invoice COVERS, not the current
# one: Linode publishes no preview invoice, so a run reads the newest settled invoice and
# its snapshot is structurally one month behind (m3 §Seam 7). Nothing here constructs a
# filename — STEP 1 reports the period and every later stage is handed the path it wrote.

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

# --- provider selection (m2 t3) ------------------------------------------------------
#
# CLOUDCOST_PROVIDER is the one env-overridable knob in this file, and deliberately so: it
# selects a *pipeline*, not a model. Unset ⇒ DigitalOcean, and the prompt below then renders
# exactly as m1's did — the DO run is not a new run shape, it is the same one with its
# provider named.
#
# An unrecognised value raises rather than defaulting: a silent fall-through to DO would run
# the wrong pipeline and label the report for a cloud it never queried.

provider = System.get_env("CLOUDCOST_PROVIDER") || "digitalocean"

{provider_name, provider_short, provider_slug, fetch_script} =
  case provider do
    "digitalocean" -> {"DigitalOcean", "DO", "digitalocean", "scripts/fetch_do.py"}
    "aws" -> {"AWS", "AWS", "aws", "scripts/fetch_aws.py"}
    "linode" -> {"Linode", "Linode", "linode", "scripts/fetch_linode.py"}
    "github" -> {"GitHub", "GitHub", "github", "scripts/fetch_github.py"}
    other ->
      raise ~s(CLOUDCOST_PROVIDER must be "digitalocean", "aws", "linode" or "github", ) <>
              "got: #{inspect(other)}"
  end

# Fail fast on the selected sink's credential (repo rule: explicit sink selection with
# fail-fast — a required-but-absent credential raises immediately, never a silent fallback
# to a different sink). CLOUDCOST_PROVIDER is the selector, so `aws` without the read-only
# AWS key is exactly the case that rule names: without this raise the run burns an LLM call
# and reaches STEP 1 before fetch_aws.py says the same thing.
#
# Names only, never a value — the credential must not reach the trajectory (D2).
#
# There is deliberately no symmetric DO raise: DO is the *default* sink rather than a
# selected one, and §t3's offline done-check (`Code.eval_file/1`) has to keep evaluating
# clean on a machine that carries no DO token. sprint.sh preflights CLOUDCOST_DO_TOKEN.
#
# Linode (m3 t2) falls on the AWS side of that line, not the DO side: it is never the
# default and can only be reached by naming it, so the "must stay clean on a machine with
# no credential" argument that exempts DO does not apply. Its raise is below.
if provider == "aws" do
  missing =
    for name <- ["CLOUDCOST_AWS_ACCESS_KEY_ID", "CLOUDCOST_AWS_SECRET_ACCESS_KEY"],
        System.get_env(name) in [nil, ""],
        do: name

  if missing != [] do
    raise "CLOUDCOST_PROVIDER=aws requires #{Enum.join(missing, " and ")} to be set. " <>
            "cloudcost authenticates with the CLOUDCOST_AWS_* read-only key only and never " <>
            "falls back to boto3's default credential chain."
  end
end

# Same posture for Linode (m3 t2), and the reason it is worth an eval-time raise rather
# than letting STEP 1 discover it: without this the run still fails, but ~4 s in, as a tool
# error the model then has to interpret and report. The raise keeps "does this pipeline
# complete" a harness property instead of a model behaviour — the same argument BL-096
# makes for declaring STEP 1's timeout below.
#
# Empty string is treated as absent, matching the AWS check above; a variable exported as
# "" is the shape a mis-sourced credential file produces, and it authenticates nothing.
if provider == "linode" and System.get_env("CLOUDCOST_LINODE_TOKEN") in [nil, ""] do
  raise "CLOUDCOST_PROVIDER=linode requires CLOUDCOST_LINODE_TOKEN to be set. " <>
          "cloudcost authenticates with that read-only Linode PAT only and never reads " <>
          "LINODE_CLI_TOKEN or LINODE_TOKEN."
end

# And for GitHub (m6 t2b), on the same ground as Linode's: never the default, reachable only
# by naming it. The shadow names it refuses are the reason the raise names the variable it
# does want — `gh` is installed on most developer workstations and CI runners, so GH_TOKEN /
# GITHUB_TOKEN are normally PRESENT here, and a run that fell back to one of them would
# authenticate with a broader-scoped write credential than this pipeline is ever given.
if provider == "github" and System.get_env("CLOUDCOST_GITHUB_TOKEN") in [nil, ""] do
  raise "CLOUDCOST_PROVIDER=github requires CLOUDCOST_GITHUB_TOKEN to be set. " <>
          "cloudcost authenticates with that read-only fine-grained PAT only and never " <>
          "reads GH_TOKEN, GITHUB_TOKEN, GH_ENTERPRISE_TOKEN, GITHUB_ENTERPRISE_TOKEN " <>
          "or GITHUB_PERSONAL_ACCESS_TOKEN."
end

# Per-provider output and history trees (decision H: one provider, one report, one run).
#
# `output/` — `report_data_{period}.json` and `cloudcost_report_{period}.html` carry no
# provider in their names (m2 t2 prefixed the orphan-candidates file only), so two providers
# sharing one directory would overwrite each other's report. The directory carries the
# provider instead, which needs no change to any script.
#
# `history/` — `compose_report_data.load_prior_snapshots` globs *every* provider's snapshot
# in `history/{prior_period}/` and `month_on_month` sums them into one `prior_total`. That is
# m1's N-merge assumption meeting decision H: under per-provider solo runs it makes the first
# AWS run's headline "AWS this month minus DigitalOcean last month" — a well-formed wrong
# figure rather than the honest no-prior-month path. Giving each provider its own history
# tree (decision H's own `history/{provider}/{period}/` layout) scopes the lookup to the
# provider that is actually running. The underlying shared-machinery defect is filed, not
# fixed here: compose stays unedited outside the A4 lift.
output_dir = "output/#{provider_slug}"
history_dir = "history/#{provider_slug}"

# --- fetch-step timeout, declared rather than defaulted (BL-096) ----------------------
#
# STEP 1 is the only step that calls a live cloud API, and it is the only one whose runtime
# approaches `run_command`'s 60_000 ms default (the exec server's
# `unwrap_or(60_000)` — ../aetheris/native/aetheris_exec_server/src/main.rs:472, advertised
# in the tool schema at :127). Measured: fetch_aws 63–67 s against the real bill, fetch_do
# 8.2–9.3 s. So AWS exceeded the default on every run ever recorded, and the pipeline only
# finished because the model chose to retry with a larger timeout_ms — a recovery nothing
# instructs, observed 5/5 under claude-haiku-4-5-20251001 and guaranteed by nothing.
#
# That put the model on the success path for whether a deterministic four-stage pipeline
# COMPLETES, which is a harness-side property: "The harness is deterministic; the model is
# not" (../aetheris/docs/aetheris/determinism-contract.md:31). Declaring the value here
# moves the timeout from something rediscovered at runtime to something stated once.
#
# One number for both providers: STEP 1 is shared, and fetch_do is declared defensively
# rather than because it needs the headroom — it fits inside the default today with ~6.5x
# margin, and the point is that it no longer *depends* on that remaining true. A third
# provider's adapter declares its own step timeout by this same convention.
#
# Deliberately NOT raising the exec-server default: a low global default is a fail-fast
# safety property for every other script in every use case. Per-step declaration is the
# right lever for the one step that legitimately exceeds it.
fetch_timeout_ms = 300_000

# --- optional optimization spike (m2 t4) ---------------------------------------------
#
# CLOUDCOST_OPTIMIZATION=1 adds ONE step and threads its file into the render. Unset — the
# default — the three chunks below are empty strings, so the prompt carries no trace of the
# spike and the pipeline is exactly the unoptimized one. That is the orchestrator half of
# §t4's isolation invariant, and it is measurable: render the prompt with the variable set
# and unset and diff — the difference is the optimization chunks and nothing else.
#
# t4 stated this as "byte-for-byte the t3 prompt". That equality no longer holds and is not
# what the invariant needs: BL-096 added STEP 1's `timeout_ms` declaration below, which
# changes the base prompt in the set and unset cases identically. The invariant is set-vs-unset
# isolation, not equality with a frozen historical prompt.
#
# The step is numbered 2b rather than 3 deliberately. Inserting a renumbered step would
# rewrite the text of every step after it, so the unset case could no longer be compared to
# t3's byte-for-byte — the isolation claim would rest on reading the diff instead of on
# running it.
#
# There is no credential raise for this gate: it needs no credential of its own beyond the
# CLOUDCOST_AWS_* key the provider check above already fails fast on, and `Code.eval_file/1`
# must stay clean with the variable set on a machine with no credentials at all.
optimization? = System.get_env("CLOUDCOST_OPTIMIZATION") == "1"

# The spike reads S3, ECR, Secrets Manager and CloudWatch — it exists for one provider only.
# Asking for it on another one raises rather than quietly dropping the flag: a silent no-op
# would hand back a report with no optimization section and no reason given, which reads
# exactly like a spike that ran and found nothing. Same posture as the two raises above.
if optimization? and provider != "aws" do
  raise "CLOUDCOST_OPTIMIZATION=1 is only meaningful with CLOUDCOST_PROVIDER=aws " <>
          "(the optimization spike reads S3/ECR/Secrets Manager/CloudWatch); got " <>
          "provider #{inspect(provider)}. Unset CLOUDCOST_OPTIMIZATION to run the " <>
          "standard pipeline for this provider."
end

step_count = if optimization?, do: "five", else: "four"

optimization_step =
  if optimization? do
    """

    STEP 2b — Detect exploratory optimization signals (S3 / ECR / Secrets Manager).
      run_command  command: "python3"
                   args: ["scripts/detect_optimization_signals.py", "--output-dir", "#{output_dir}"]

      Parse the JSON on stdout and keep `file` — the optimization-signals path.

      This step is EXPLORATORY and best-effort. A thin or empty result is a normal
      outcome, not a failure, and `"status": "partial"` here means some API was denied
      or some fact was unavailable — the file was still written. Carry on either way.
    """
  else
    ""
  end

render_optimization_arg =
  if optimization?, do: ~s(, "--optimization-file", "<SIGNALS>"), else: ""

render_optimization_note =
  if optimization? do
    """

      Replace "<SIGNALS>" with the `file` path from STEP 2b.\
    """
  else
    ""
  end

# provider/model are literals rather than the AETHERIS_MODEL/AETHERIS_PROVIDER env
# override the sibling agents use: sprint.sh sources aetheris-agents/.env, so an
# override there would silently change what the stub-guard done-check asserts
# `resolved_model` against. §t5 names both literally; keep them that way.

system_prompt = """
You are the cloudcost orchestrator. Run the #{provider_name} cost-report pipeline by
executing the #{step_count} steps below in order, then report the report file and the orphan
count. Every step is a `run_command` call; each script writes its own output file and
prints a JSON summary to stdout containing the path it wrote.

---

STEP 1 — Fetch the #{provider_short} cost snapshot and inventory.
  run_command  command: "python3"
               args: ["#{fetch_script}", "--output-dir", "#{output_dir}"]
               timeout_ms: #{fetch_timeout_ms}

  Pass `timeout_ms` on this call exactly as written. It is part of the call, not an
  entry in the args array. This step reaches a live cloud API and legitimately runs
  longer than the default timeout; the value above is already sized for it, so there
  is never a reason to retry this step with a different timeout.

  Parse the JSON on stdout. Keep three values for later steps:
    - `period`           (e.g. "2026-07")
    - `files.costs`      the cost snapshot path
    - `files.inventory`  the inventory path

  `files.costs` is absent when the billing API was unavailable. That is a partial run,
  not a failure — note it and carry on; STEP 3 has a second arg form for that case.

STEP 2 — Detect orphan candidates from the inventory.
  run_command  command: "python3"
               args: ["scripts/detect_orphans.py", "<INVENTORY>", "--output-dir", "#{output_dir}"]

  Replace "<INVENTORY>" with the `files.inventory` path from STEP 1.
  Parse the JSON on stdout and keep `file` — the orphan-candidates path.
#{optimization_step}
STEP 3 — Compose the report data (merges cost + inventory + orphans, adds the MoM delta).

  If STEP 1 printed `files.costs`, use this form:
    run_command  command: "python3"
                 args: ["scripts/compose_report_data.py", "--cost", "<COSTS>", "--inventory", "<INVENTORY>", "--orphans", "<ORPHANS>", "--output-dir", "#{output_dir}", "--history-dir", "#{history_dir}"]

  If STEP 1 did NOT print `files.costs`, use this form instead — drop the flag and its
  value together, and change nothing else:
    run_command  command: "python3"
                 args: ["scripts/compose_report_data.py", "--inventory", "<INVENTORY>", "--orphans", "<ORPHANS>", "--output-dir", "#{output_dir}", "--history-dir", "#{history_dir}"]

  Replace "<COSTS>" with `files.costs` from STEP 1, "<INVENTORY>" with `files.inventory`
  from STEP 1, and "<ORPHANS>" with the `file` path from STEP 2.
  Parse the JSON on stdout and keep `file` — the report-data path.

STEP 4 — Render the HTML report.
  run_command  command: "python3"
               args: ["scripts/render_report.py", "<REPORT_DATA>", "--output-dir", "#{output_dir}"#{render_optimization_arg}]

  Replace "<REPORT_DATA>" with the `file` path from STEP 3.#{render_optimization_note}
  Parse the JSON on stdout and keep `file` (the HTML report) and
  `counts.orphan_candidates`.

STEP 5 — Report, in plain text:
    - the HTML report path from STEP 4
    - the orphan-candidate count from STEP 4
    - the period from STEP 1
    - any step that reported `"status": "partial"`, and what it said was degraded

---

Rules:
- Execute the commands exactly as written. Do not add, drop, or reorder arguments.
  The only permitted variation is the two arg forms offered in STEP 3.
- Do not pass "python3" inside the args array — it is already the command field.
- All paths are relative to the sandbox root. overlay_base_dir is nil, so the output
  files persist on disk and are the deliverable.
- Use the path each step printed. Never construct, guess, or reconstruct a filename,
  and never edit a path a script gave you.
- `"status": "partial"` is NOT a failure. These scripts exit non-zero on a partial run
  by design; the output file was still written. Note what was degraded and continue to
  the next step.
- A step fails only when its stdout carries `"status": "error"`, or when the output
  path that step is documented to print is absent from its stdout. In that case report
  which step failed, quote its stderr, and STOP.
- After a failure, stop completely. Do not retry the step, do not re-run a script to
  inspect its output, do not read or list files, and do not run any other command.
- Do not compute, adjust, or restate any figure from the report data. The scripts
  produce every number; you orchestrate and report paths and counts only.
"""

%Aetheris.RunConfig{
  # The provider is in the run id so Rig's run list tells the two solo runs apart at a
  # glance (decision H: one provider, one report, one run).
  run_id:           "cloudcost-orch-#{provider_slug}-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         "anthropic",
  model:            "claude-haiku-4-5-20251001",
  # Provider in the label, not only in the run id (BL-083): Rig's run list groups on
  # COALESCE(label, run_id) and renders the label, so this is what makes an AWS row
  # distinguishable from a DO one at a glance instead of via the search filter.
  # The suffix is safe for grouping — classifyRun lowercases and does startsWith, so
  # "cloudcost · aws" still matches the `cloudcost` prefix (RunList.tsx:118-140).
  label:            "Cloudcost · #{provider_name}",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        20,
  # :full, not :rolling/6 (§t5, corrected in the t5 commit). Four steps is well under the
  # guide's ~10-step threshold, and the workflow threads file paths from STEP 1 through
  # STEP 4 — a rolling window would truncate them out of context mid-pipeline.
  context_strategy: :full,
  tools:            ["run_command"],
  system_prompt:    system_prompt,
  user_prompt:      "Run the cloudcost report pipeline."
}
