# BL-153 s0 — read-and-report on artifact/run binding (implementation notes)

`2026-08-16, at agents 900662f / aetheris d19f4b6. Every path, line number, command and figure
below is measured at that pair unless it names another. The harness is READ ONLY for this ticket
and its HEAD is unchanged at both ends — d19f4b6 is also the commit BL-153's own ordering was
read at, so nothing here is a read against a moved tree. Absolute paths are normalised to ~
throughout.`

Standalone row; no milestone. Notes filed at `docs/milestones/` per the convention for repo-wide
(non-use-case) BL rows — nearest recent example `docs/milestones/bl-152-implementation-notes.md`,
the commit before this arc.

**This file is the record; the ticket's review packet is scratch.** The ticket text said no notes
file was owed. The arbiter withdrew that at the amendment round: `CLAUDE.md` §Learning —
m1-docbuilder makes a notes file a required deliverable *explicitly including docs-only tickets*,
and a ticket instruction that gives no reason and rules no exemption does not suspend a standing
rule. The conflict was reported rather than resolved in the first round, per the ticket; this
file discharges it in the second.

**What the ticket delivered.** Four reads, three arbiter-owed documents (a ruling on BL-153, a
closure on BL-152, two promoted lessons), and — at the amendment — a findings annotation, a
placement ruling, a supersession note, and one seed. **No fix of any kind was implemented**: no
stamp, no run id, no invalidation, no reorder, and no edit to `../aetheris/scripts/sprint.sh`,
which is where the fix would go.

---

## 1. R1 — the order of the three events in the cloudcost sprint leg

All three in `../aetheris/scripts/sprint.sh` at `d19f4b6`.

| # | event | lines |
|---|---|---|
| 1 | credential preflight (`case "$CC_PROVIDER" in` … `esac`) | **2895–2932** |
| 2 | stale-artifact guard (`find "$CLOUDCOST_OUT" -mindepth 1 -delete`) | **2944–2946** |
| 3 | first command that can write into `$CLOUDCOST_OUT` (the orchestrator run) | **3148–3151** |

Preflight head, `sprint.sh:2892–2895`:

```
  # The case runs against the live bill; without the credential the adapter cannot
  # produce a snapshot and every downstream assertion would pass vacuously on stale
  # output. Preflight the selected provider's own credential, not both.
  case "$CC_PROVIDER" in
```

Every arm is `fail …; exit 1`, e.g. `sprint.sh:2896–2900`:

```
    digitalocean)
      if [[ -z "${CLOUDCOST_DO_TOKEN:-}" ]]; then
        fail "CLOUDCOST_DO_TOKEN is not set — the digitalocean pipeline needs the read-only DO PAT"
        exit 1
      fi
```

Guard, `sprint.sh:2944–2946`:

```
  mkdir -p "$CLOUDCOST_OUT"
  find "$CLOUDCOST_OUT" -mindepth 1 -delete 2>/dev/null || true
  ok "cleared ${CLOUDCOST_OUT} (stale-artifact guard, scoped to this provider)"
```

First writer, `sprint.sh:3148–3151`:

```
  info "Starting: uc-cloudcost orchestrator (provider=${CC_PROVIDER})"
  if ( cc_hermetic mix aetheris --json run \
       "${CLOUDCOST_DIR}/agents/cloudcost_orchestrator.exs" ) \
       > "$OUT_DIR/cloudcost/run.json" 2>&1; then
```

`$CLOUDCOST_OUT` is defined once, `sprint.sh:2679`:
`CLOUDCOST_OUT="${CLOUDCOST_DIR}/output/${CC_PROVIDER}"`.

### 1a. How the negative — *nothing between the guard and the run writes there* — was established

Not by inference from reading the region. By **exhausting every mention of the variable in the
file**, so the claim is over a closed set rather than over what a reader happened to notice:

```
$ grep -n 'CLOUDCOST_OUT' scripts/sprint.sh
2679:  CLOUDCOST_OUT="${CLOUDCOST_DIR}/output/${CC_PROVIDER}"
2944:  mkdir -p "$CLOUDCOST_OUT"
2945:  find "$CLOUDCOST_OUT" -mindepth 1 -delete 2>/dev/null || true
2946:  ok "cleared ${CLOUDCOST_OUT} (stale-artifact guard, scoped to this provider)"
3166:  # The discovery is not a stale-artifact hazard: $CLOUDCOST_OUT was emptied above, so
3170:    find "$CLOUDCOST_OUT" -maxdepth 1 -name 'cloudcost_report_*.html' | sort)
3180:    fail "no cloudcost_report_*.html in ${CLOUDCOST_OUT} — the run wrote no report"
3182:    fail "expected exactly one cloudcost_report_*.html in ${CLOUDCOST_OUT}, found ${#CLOUDCOST_REPORTS[@]}: ${CLOUDCOST_REPORTS[*]}"
3200:    CLOUDCOST_DATA="${CLOUDCOST_OUT}/report_data_${CLOUDCOST_PERIOD}.json"
3273:  CC_SEEN=$(python3 - "$CLOUDCOST_OUT" "${CLOUDCOST_DIR}/scripts" <<'PY'
3399:  ls -lh "${CLOUDCOST_OUT}/" 2>/dev/null || true
3405:  unset CC_PROVIDER CC_SEEN CLOUDCOST_OUT CLOUDCOST_REPORTS
```

Thirteen mentions; every one after 2946 is a read (a `find -name` discovery, a path built to be
read, an `ls`, an `unset`). The four `mix run --eval` checks that sit in the gap — at `:2953`,
`:2980`, `:3008`, `:3021` — all evaluate
`Code.eval_file("../aetheris-agents/cloudcost/agents/cloudcost_orchestrator.exs")`, which builds
the `OrbConfig` struct and runs no pipeline, so they write nothing anywhere.

### 1b. The consequence, wanted either way: **YES**

The guard precedes the first writer by ~200 lines, and the preflight precedes the guard. A run
that passes the preflight and dies anywhere in between — at any of the four eval checks, at the
three hermetic-prefix arms, or mid-pipeline inside the orchestrator — has **already destroyed the
previous artifacts**. The order is **preflight → destroy → produce**.

This closes the OPEN QUESTION the ruling recorded and declined to rest on: the reorder's marginal
loss really is confined to preflight-stage failures, so the reorder is **cheaper than BL-153
feared**. It does not revive the reorder, because R2 shows most mechanisms never reach the sprint.

---

## 2. R2 — Rig does not reach cloudcost through `sprint.sh`

**NO**, and this is the finding the placement ruling turns on.

```
$ grep -rn 'sprint' --include=*.rs --include=*.ts --include=*.tsx --include=*.json src src-tauri
$ echo "exit=$?"
exit=1
```

Run from `rig/`. **A zero here is worthless without a positive control**, so the same tool over a
corpus known to contain a term: `grep -rc 'cloudcost' --include=*.rs src-tauri/src/commands/harness.rs`
→ `14`.

Rig starts a process in exactly the five places `grep -rn 'Command::new' --include=*.rs src-tauri/src`
returns — `orchestrate.rs:36`, `orchestrate.rs:46`, `fork.rs:67`, `tools.rs:264`, `tools.rs:658`.
None is a shell; none names `sprint.sh`.

### 2a. Path (a) — the Orchestrator module, which is what Cancel reaches

`rig/src/components/modules/orchestrator/OrchestratorView.tsx:258` calls `start` with **two**
arguments — no `scriptPath`:

```
              onClick={() => { history.add(request); start(request, serializeExtraEnv()); }}
```

so `script_path` reaches the backend as `None` and `rig/src-tauri/src/commands/orchestrate.rs:25–26`
defaults it:

```
    let rel = script_path.unwrap_or_else(|| "agents/orchestrator.exs".to_string());
    let full_path = format!("{}/{}", agents_path, rel);
```

The argv is assembled at `rig/src-tauri/src/commands/orchestrate.rs:45–50`:

```
    } else {
        let mut c = std::process::Command::new("mix");
        c.args(["run", &full_path])
            .env("ORCHESTRATOR_REQUEST", &request)
            .current_dir(aetheris_dir);
        c
    };
```

**argv: `mix run $AETHERIS_AGENTS_PATH/agents/orchestrator.exs`**, cwd the aetheris dir, env
`ORCHESTRATOR_REQUEST` plus the stored agent config and per-run `extra_env` (`:56–65`). Note
`mix run`, **not** the sprint's `mix aetheris --json run` (`sprint.sh:3149`) — a different command,
which is why the run-id surface differs too (§5).

That agent is an LLM planner. Its vocabulary is `docs/capability-matrix.md`, read whole into the
system prompt at `agents/orchestrator.exs:17–18`, and the matrix carries cloudcost at
`docs/capability-matrix.md:198` (`| cloudcost_orchestrator.exs | Cloudcost | run_command |`). The
emitted path is validated against nothing (`agents/orchestrator.exs:267–268`, `:287`):

```
  agent_file = step["agent"]
  agent_path = Path.join(agents_path, agent_file)
  …
    with {:ok, config}  <- RunHelpers.load_agent_file(agent_path),
         {:ok, run_id}  <- Aetheris.start_run(config),
```

`Aetheris.start_run/1` runs it **in-process**, inside the very `mix run` child that
`orchestrate_cancel` SIGKILLs (`rig/src-tauri/src/commands/orchestrate.rs:149–159`). So a
cloudcost pipeline is reachable from Rig and killable by its Cancel.

**Stated as what it is:** whether the planner in fact emits `cloudcost/agents/cloudcost_orchestrator.exs`
is a model decision, not a code fact. The code constrains it in no way and the matrix supplies the
name. This is reachability, not a demonstrated run.

### 2b. Path (b) — the Tools panel, a fourth mechanism this row did not know about

`rig/src/hooks/useTools.ts:51–53` invokes `tools_run_script`; the argv is assembled at
`rig/src-tauri/src/commands/tools.rs:658–663`:

```
    let mut cmd = std::process::Command::new("python3");
    cmd.arg(&canonical_script)
        .args(&args)
        .current_dir(&use_case_dir);
    for (key, value) in &agent_config {
        cmd.env(key, value);
    }
```

**argv: `python3 $AETHERIS_AGENTS_PATH/cloudcost/<file> <args…>`**, cwd
`$AETHERIS_AGENTS_PATH/cloudcost`. `cloudcost` is one of the six discovered manifests — the set is
asserted literally at `rig/src-tauri/src/commands/tools.rs:789–792` — so every script in
`cloudcost/tools.json`, including all four that write into `cloudcost/output/<provider>/`, is
runnable one at a time from that panel. It uses `cmd.output()` (`:666`), is never registered in
`state.jobs`, and therefore **has no cancel at all** and no pipeline ordering.

This is a **fourth mechanism** reaching BL-153's symptom, and it is worse than the third in one
respect: it needs no interruption. A single stage run from the panel leaves a directory whose
other artifacts came from a different run entirely, and nothing distinguishes that from a
complete run.

### 2c. The consequence for the ruling

A stamp written by `sprint.sh` **cannot cover either Rig path**, and is worse than absent on both.
Rig writes into the same `cloudcost/output/<provider>/` the sprint stamps, so a Rig run mutates a
directory that may still carry the *previous sprint run's* stamp — internally coherent, and under
the ruling's own reader rule (*an unstamped or mismatched directory is not a run*) it would read
as a stale sprint directory rather than as the new thing it is. That argument is what the arbiter
ruled on; the ruling is on BL-153's row.

---

## 3. R3 — who writes what, and whether there is a last writer

For `cloudcost/output/digitalocean/`. Pipeline order is the agent prompt's STEP 1→5
(`cloudcost/agents/cloudcost_orchestrator.exs:248–295`); the provider→script map is `:62–65`.

| # | artifact | step / script | write site |
|---|---|---|---|
| 1 | `do_costs_{period}.json` | STEP 1 `scripts/fetch_do.py` | `cloudcost/scripts/fetch_do.py:582` |
| 2 | `do_inventory_{period}.json` | STEP 1 `scripts/fetch_do.py` | `cloudcost/scripts/fetch_do.py:583` |
| 3 | `optimization_signals_{provider}_{period}.json` — **only under `CLOUDCOST_OPTIMIZATION`** (STEP 2b) | `scripts/detect_optimization_signals.py` | `cloudcost/scripts/detect_optimization_signals.py:892–893` |
| 4 | `digitalocean_orphan_candidates_{period}.json` | STEP 2 `scripts/detect_orphans.py` | `cloudcost/scripts/detect_orphans.py:789` |
| 5 | `report_data_{period}.json` | STEP 3 `scripts/compose_report_data.py` | `cloudcost/scripts/compose_report_data.py:907` |
| 6 | `cloudcost_report_{period}.html` | STEP 4 `scripts/render_report.py` | `cloudcost/scripts/render_report.py:378, :381` |
| 7 | `cloudcost_report_{period}.pdf` — **only with `--pdf`, and only if `wkhtmltopdf` is present** | STEP 4 `scripts/render_report.py` | `cloudcost/scripts/render_report.py:261–285` |

Live confirmation of the five unconditional ones (`ls cloudcost/output/digitalocean/`):
`cloudcost_report_2026-08.html`, `digitalocean_orphan_candidates_2026-08.json`,
`do_costs_2026-08.json`, `do_inventory_2026-08.json`, `report_data_2026-08.json`.

**A complete run also writes outside that directory.** STEP 3 is passed
`--history-dir history/{provider_slug}` (`cloudcost/agents/cloudcost_orchestrator.exs:141`) and
`persist_history` (`cloudcost/scripts/compose_report_data.py:974–991`) writes
`{history_dir}/{period}/{provider}_costs_{period}.json`. So a DO run's footprint is the files
above **plus** `cloudcost/history/digitalocean/{period}/…`.

### 3a. The answer: a single point in execution order, no point at all in the artifacts

- On the default configuration the last writer is **STEP 4, `render_report.py`, writing the HTML**.
  Nothing writes into the provider directory after it. That is a genuine single point.
- **It is not observable from the directory.** It is defined by *the agent having executed STEP 4*,
  and nothing in the directory records that a STEP 4 was owed. Five files with the HTML missing is
  exactly what a run killed after STEP 3 leaves — and also exactly what a successful run of an
  earlier pipeline shape left. The HTML's presence is a proxy that works only for a reader who
  already knows the pipeline shape and the flag settings.
- **It moves with configuration.** With `--pdf` the last writer is the PDF branch inside STEP 4.
  And the history write happens at STEP 3 — *before* the report — into a tree the guard at
  `sprint.sh:2944–2945` never clears, being scoped to `$CLOUDCOST_OUT`. So "the run is complete" is
  not even a single *directory's* property.

That is what the placement ruling's added property — *a writer that runs last unconditionally* —
is for. No current step is one.

---

## 4. R4 — a per-run identifier exists and reaches no script

**It exists.** `config.run_id` is carried through every trajectory event —
`../aetheris/lib/aetheris/execution/loop.ex:183`, `:185`, `:267`, `:322` and throughout, e.g.:

```
    :ok = append_event(log_pid, config.run_id, step, :prompt_built, prompt_payload)
```

and it is surfaced to the sprint on the run payload, `sprint.sh:3401–3403`:

```
  RUN_ID=$(json_read "$OUT_DIR/cloudcost/run.json" '.run_id // empty')
  info "Run ID: ${RUN_ID:-n/a}"
  info "Inspect: mix aetheris inspect ${RUN_ID:-<run_id>}"
```

— i.e. read *after* the run has exited.

**Where it stops short, precisely.** `run_command` is the only channel from agent to script and it
passes no environment. `../aetheris/native/aetheris_exec_server/src/runner.rs:46–48`:

```
pub fn run(command: &str, args: &[String], working_dir: &Path, timeout_ms: u64) -> RunResult {
    run_with_env(command, args, &[], working_dir, timeout_ms)
}
```

The `&[]` is the env slice. `run_with_env` (`:92–109`) *can* set env — its two non-empty callers
are the git-identity ones at `:53`, `:62`, `:78` — and the generic entry point hands it nothing.
The tool schema has no `env` field either:
`../aetheris/lib/aetheris/execution/tool_schema/registry.ex:44–68` declares exactly `command`,
`args`, `working_dir`, `timeout_ms`.

**Nor by argv.** The cloudcost agent's `args` arrays are literal but for paths a previous step
printed (`cloudcost/agents/cloudcost_orchestrator.exs:249–288`), and the prompt forbids variation:
*"Execute the commands exactly as written. Do not add, drop, or reorder arguments."* (`:307–308`).

**Negative control**, run in the harness repo at `d19f4b6`:

```
$ grep -rn 'AETHERIS_RUN_ID' lib native scripts
$ echo "exit=$?"
exit=1
```

**Rig has its own id and it is a different thing.** `job_id = format!("orch-{}", …unix millis…)` is
minted at `rig/src-tauri/src/commands/orchestrate.rs:91–98` — **after** the child's environment is
set at `:56–65`, so it could not reach the child even in principle. It is the key of Rig's job map
and nothing else.

**Summary.** The harness has one and stops at the exec-server boundary; Rig has one and stops at
its own map; the sprint reads the harness's one post-hoc. **None reaches a script.** This confirms
BL-153's third annotation — *zero artifacts carry a run_id* — from the production end: nothing
could have put one there.

---

## 5. The two BL-153 pointers that were imprecise at HEAD

Recorded here rather than corrected in the row, because dated annotations record what was believed
at a date.

1. **`sprint.sh:2894-2931` (preflight).** The `case`…`esac` is **2895–2932**. `2894` is a blank
   line and `2931` is the `*)` arm's `exit 1`, so the cited span truncates the `esac`.
2. **`sprint.sh:2934-2946` (guard).** The **end is right**; the start is not. `2934` is inside the
   explanatory comment block; the guard proper begins at the `mkdir -p` on **2944**.

Neither changes any finding. **Everything else in BL-153 checked out at HEAD**: the harness commit
`d19f4b6` is HEAD; `orchestrate_cancel` is at `rig/src-tauri/src/commands/orchestrate.rs:149–159`
as cited; and the third annotation's *zero run_id in artifacts* is corroborated by §4 from the
other direction.

---

## 6. P1–P4, the proposals carried out of the reads

Filed here as the record. P1 and P2 were taken by the arbiter's placement ruling on BL-153's row;
P3 and P4 were folded into it as constraints. None is implemented.

**P1 — the stamp cannot live in `sprint.sh`.** §2c. **Ruled: script-side.**

**P2 — the stamp needs a run id and nothing supplies one to a script.** §4. A *script-minted* id
threaded stage to stage — the way the period and the paths already are — needs no harness change,
whereas inheriting one means changing the exec-server boundary. This repo's own precedent for the
shape is `slug_term()` (`CLAUDE.md` §Python script conventions): derive it in Python, pass it
through, never let the LLM construct it. **Ruled: pipeline-minted.**

**P3 — if a stamp is ever fed from the sprint's environment, `CC_ALLOW` must name it.**
`sprint.sh:2743` is default-deny (`CC_ALLOW=(PATH HOME LANG ANTHROPIC_API_KEY CLOUDCOST_OPTIMIZATION)`
plus adapter-derived names at `:2828–2829`). A stamp variable not on that list is stripped and the
stamp silently absent — the exact shape the inversion was built to make impossible for
credentials. **Folded into the ruling.**

**P4 — the "last writer" is not in the output directory alone.** §3. `persist_history` writes into
`cloudcost/history/` at STEP 3, before the report, into a tree the guard never clears. **Folded
into the ruling as a coverage property.**

---

## 7. The history-tree observation — why no new row was opened

The amendment asked for a new row on *"the history tree holds two layouts on disk"*, with an
explicit out: *"If your reading shows it inert, say so and file nothing."* The reading produced a
third answer, and it is recorded as an annotation on **BL-076** instead. The deviation and its
ground:

**The composer writes one layout, not two.** `persist_history` writes exactly
`{history_dir}/{period}/{provider}_costs_{period}.json`
(`cloudcost/scripts/compose_report_data.py:989`). The two shapes on disk are two values of
`--history-dir`, not two behaviours. The orchestrator passes `history/{provider_slug}`
(`cloudcost/agents/cloudcost_orchestrator.exs:141`); the default is the shared `cloudcost/history`
(`DEFAULT_HISTORY_DIR`, `:111`, wired at `:1037`). So the row's premise as framed — two layouts —
is **false as a fact about the composer**, and a row asserting it would be a false entry.

**The stray is not residue of a layout change.** `cloudcost/history/2026-08/github_costs_2026-08.json`
has mtime `2026-08-14 08:18`, six hours *before* that same day's provider-scoped GitHub run at
`14:29`, and the per-provider layout predates both. It is a direct `compose` call that omitted the
flag.

**The mechanism is already owned by an open row.** BL-076 (`docs/backlog-2026-06.md:2993`) is open
and its **Why it is not fixed here** paragraph names this exact case: *"a direct `compose`
invocation with the m1-shaped shared tree still produces the wrong figure."* Filing a second row
would be precisely the two-surfaces defect **BL-145** ruled on and **BL-146** names. What the
observation adds is evidence about BL-076's *live-ness* — its convention-only mitigation observed
failing unprompted, twelve days after the row predicted it — so it belongs *in* BL-076, which
stays open and therefore satisfies the standing rule that a deferred finding gets a row that keeps
an executor.

**The artifact itself is inert.** `cloudcost/history/` is gitignored (`cloudcost/.gitignore:10`,
`history/*`; only `.gitkeep` tracked), and `load_prior_snapshots` reads `history_dir / previous`
(`:1002`) — under the orchestrator, `history/github/2026-07`, never the flat tree. No orchestrated
run can read it. No cleanup is proposed.

**Two of BL-076's own citations have drifted** and are recorded in the annotation:
`load_prior_snapshots` is at `:994` (glob at `:1006`), not `:711`; the `month_on_month` lines are
`:352` and `:360`, not `:334`/`:342`. The quoted code is present verbatim at the new lines.

**The seed that was asked for and filed as asked:** the planner validating its emitted agent path
against nothing → **BL-151**, with `agents/orchestrator.exs:267-268` and `:287`, no proposal, and
its distinctness from BL-156 and BL-094 stated.

---

## 8. What was declined, and what the arbiter changed

**Declined, per the ticket.** No harness edit; `../aetheris/scripts/sprint.sh` is where R1's
finding lives and where a reorder would go, and it was read only. No stamp, run id, invalidation
or reorder implemented. The Tools path's missing cancel was **not** pursued — it is BL-154's
neighbourhood, and §2b records only the artifacts such a run leaves.

**Two arbiter corrections folded in**, both of which changed the deliverable:

1. **The notes file.** The ticket said none was owed; the standing convention says otherwise and
   the arbiter withdrew the instruction. This file exists because of that.
2. **BL-152's contradictory annotation.** The first round flagged that the row's earlier
   *"the row is NOT closed"* annotation contradicts the closure pasted beneath it, and declined to
   resolve it because the instruction to paste verbatim gave no authority to reword. The arbiter
   ruled the defect its own and supplied a supersession line, appended after the closure. The
   earlier annotation stands, unrewritten.

**One deviation of the session's own**, §7 above: a row was asked for and an annotation on an
existing open row was written instead, on the ground that the row's premise is false at HEAD and
the mechanism is already owned. Flagged rather than folded.

---

## 9. Gates

Run at the final tree of the amendment commit, from the `aetheris-agents/` repo root.

**The whole-suite gate**, under `timeout 600`:

```
$ timeout 600 python3 -m pytest -q -m "not integration and not dormant"
deselected by reason: integration=112, dormant=208 (total 320)
1384 passed, 3 skipped, 320 deselected, 7 xfailed
```

Both deselected counts present; exit 0. Neither deferred set was run — this ticket is
off-territory for both, and BL-152's record already covers them (integration 25.27s; dormant
deliberately not run, two capped runs killed at 52m21s and 10m17s).

**`drift_check.py --strict`**, post-commit: `8 PASS  0 FAIL  2 WARN  7 INFO`, exit 0. Both WARNs
are the declared `project_knowledge` manifest-staleness exemption — `CLAUDE.md` §Definition of
done — and are this commit's own two files reported back. No structural manifest problem fired.
Run post-commit because check 8 compares against committed history and is vacuous before.

**Harness unchanged** at `d19f4b6`, clean, at both ends of both commits. Nothing in `../aetheris/`
was written; every harness citation above is a read.

Exact commands, full outputs and the byte-identity diffs for the pasted blocks are in the two
review packets; the figures above are transcribed from those runs.
