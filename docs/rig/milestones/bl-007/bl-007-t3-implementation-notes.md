# BL-007 / t3 — implementation notes: Rig Tauri command `fork_run`

**Ticket:** [README.md](./README.md) §t3 · **Milestone:** [BL-007](./README.md) (#48; per-ticket issues waived)
**Date:** 2026-07-19 · **Branch:** `aetheris-agents` → `bl-007-t3` (off `cb3574f`)
**Watermark:** verified against agents `cb3574f`, harness `eef174f` (bl-007-t2, reference-only this ticket). Anything cited beyond these HEADs was fresh-read this session.

## What was built

One Tauri command, `fork_run(run_id: String, step: u64, label: Option<String>) -> Result<String, String>`, spawning the post-t2 CLI `mix aetheris --json fork <trajectory> --step N [--name label]`.

- **`rig/src-tauri/src/commands/fork.rs`** (new) — the command. Resolves the source trajectory, spawns the CLI in the aetheris repo root, parses the forked run id from the CLI's JSON result line. Logic factored into two pure, unit-tested helpers: `fork_argv/3` (builds the `mix` argv) and `parse_run_id/1` (scans stdout from the end for the last JSON object carrying `run_id`, tolerating mix/log noise).
- **`rig/src-tauri/src/commands/trajectory.rs`** (extended) — `traj_path` promoted to `pub(crate)`; new `pub(crate) fn aetheris_root()` factored out (the `AETHERIS_DB_PATH`.parent().parent() derivation), reused by `fork.rs` for the `mix` working directory. Per `rig/CLAUDE.md` "`pub(crate)` on shared helpers" — reuse over duplication. Behavior-neutral (`traj_path` derivation unchanged).
- **`rig/src-tauri/src/commands/mod.rs`** — `pub mod fork;`.
- **`rig/src-tauri/src/lib.rs`** — `commands::fork::fork_run` registered in `generate_handler!`.
- **`docs/rig/specs.md`** §4 — `fork_run` command entry (same commit, per §t3).

## Design decisions (with evidence)

- **Spawn `mix aetheris --json fork`, parse the JSON result line.** The CLI formats via `Formatter.print(result, mode)`; `--json` mode does `IO.puts(Jason.encode!(data))` (`../aetheris/lib/aetheris/cli/output/formatter.ex` `print({:ok, data}, :json)`). The global `--json` flag is parsed by `CLI.run`'s `parse_head` (`cli/main.ex:41-42`, `@global_switches` includes `json: :boolean`) so it must precede the `fork` subcommand — hence argv `["aetheris","--json","fork",…]`. Verified headlessly: the CLI emits `{"status":"done","run_id":"fork-…"}` on stdout.
- **`parse_run_id` scans from the end for the last `run_id`-bearing JSON line.** Booting `mix aetheris` prints Logger noise to stdout (observed: an `[Aetheris.Application] orphan sweep` line preceding the result). Scanning `.rev()` for the last JSON object with `run_id` (the same tolerance `orchestrate.rs:80-92` applies) is robust to that noise.
- **`async` command, blocks to completion (finding 2 resolution).** `fork_run` is an `async` Tauri command that runs the blocking `mix aetheris fork` on `tauri::async_runtime::spawn_blocking`. Rationale: Tauri v2 runs *synchronous* commands on the **main thread** (v2.tauri.app/develop/calling-rust — "Commands without the async keyword are executed on the main thread"; "Asynchronous commands are preferred … doesn't result in UI freezes"), so a sync `fork_run` would freeze the UI for the full duration of a real-provider fork (minutes). It does **not** follow `orchestrate_start`'s spawn-and-return-`job_id` pattern (`orchestrate.rs:80` thread + `:107` immediate return) because the CLI reveals the run id only at completion (`await_run`) — there is no early id to return without a harness change (out of scope). It matches the other codebase precedent instead: `tools_run_script` (`tools.rs:636`) is likewise a command wrapping a blocking `Command::output()`. The invoke promise still resolves only at completion (progress UX is t4's — carried into README §t4).
- **No Tauri `State`.** `fork_run` derives everything from `AETHERIS_DB_PATH` via `aetheris_root`/`traj_path` (as `trajectory_load` does) and shells out to `mix`; it needs no harness DB handle. Omitted the unused `State` param rather than carry a `_state` placeholder.
- **Non-`done` terminal status → `Err` (finding 3 resolution).** A run id appears on stdout only for a `done` fork. `await_run` turns `failed`/`cancelled` into `{:error, …}` (`../aetheris/lib/aetheris/cli/commands/run_helpers.ex:67-74`), which the Formatter prints to *stderr*; `mix` discards the CLI exit code (`lib/mix/tasks/aetheris.ex:10` `_ = CLI.run(argv)`) so exit is always 0. Demonstrated: `mix aetheris --json fork <traj> --step 9` (no `:step_complete`) → exit 0, empty stdout, stderr `Error: failed to build fork config: :step_not_found`. So `fork_run` cannot rely on exit code; it returns `Err` whenever stdout has no run_id, and now surfaces the CLI's *stderr* in that error (was a generic message) — a failed fork is never reported as success.
- **Pure-join helpers unit-tested (finding 6).** `root_from_db_path` and `traj_path_under` factored out of `aetheris_root`/`traj_path` and pinned with two `trajectory.rs` unit tests (no env-var flakiness), so the shared helper's contract is asserted, not assumed.
- **`step: u64`.** Non-negative step index; maps to CLI `--step N` (`cli/commands/fork.ex` `@switches [step: :integer]`).
- **Env inheritance.** The spawned `mix` inherits Rig's env (so `AETHERIS_DB_PATH` and provider config flow through), consistent with `orchestrate.rs` (`mix run` in `aetheris_dir`). The fork run lands in the same harness DB Rig reads because `aetheris_root` = `AETHERIS_DB_PATH`.parent().parent() and the harness default DB is `<root>/priv/<db>`.

## The `label` finding (named open item — resolved from repo state)

**`label` IS durably stored, but Rig cannot currently read it — a pre-existing Rig defect, independent of t3.**

- `label` maps: CLI `--name` → `fork_overrides(opts)` → `%{label: name}` → `RunConfig.label` (`../aetheris/lib/aetheris/cli/commands/fork.ex`, t2).
- t2 found `encode_config` **strips** `label` from `config_json` (`../aetheris/lib/aetheris/agent/server.ex:758` `Map.delete(:label)`). But it is not lost — it is persisted to a **dedicated `runs.label` column**: schema `label TEXT` (`store.ex:794`), written from `config.label` at run init/finish (`server.ex:233`, `:744`) via the store upsert `INSERT INTO runs (…, label) … label = excluded.label` (`store.ex:1072-1087`), and read back by `deserialize_run_row` (`store.ex:1120-1127`).
- **The defect:** Rig's own harness commands read `label` from the *wrong place* — `json_extract(r.config_json, '$.label')` (`rig/src-tauri/src/commands/harness.rs:82` in `harness_list_runs`; `:196` in `harness_get_run`), i.e. from `config_json`, where `encode_config` stripped it. So `COALESCE(json_extract(config_json,'$.label'), run_id)` **always falls back to `run_id`** — Rig never shows a real label, for forks or any run.

**Option taken: pass `label?` through with the caveat documented** (in the `fork.rs` doc comment and the specs §4 entry), rather than omit it. Rationale: `--name` is a real, durable CLI capability; the param is not dead at the storage layer, only at Rig's read layer. Omitting it would drop a genuine feature; silently exposing it (pretending Rig will show it today) is the anti-pattern the ticket warns against — so the caveat is explicit.

**Recommended backlog item (outside §t3 Touches — `harness.rs` is a different command, and §t3 is "one command, no UI"):** fix `harness_list_runs`/`harness_get_run` to read the `r.label` column instead of `json_extract(config_json,'$.label')` (`harness.rs:82,196`). One-line SQL change per site; makes labels (including fork labels) visible retroactively. Candidate for t5's carry list or a standalone Rig ticket — flagged here, not fixed, to keep t3 scoped.

## Deviations

- **`trajectory.rs` extended** — not named individually in §t3 Touches (which lists `commands/` new-or-extended file, `lib.rs`, `specs.md`). It is under `commands/`; extending it to `pub(crate)`-share `traj_path`/`aetheris_root` is reuse-over-duplication per `rig/CLAUDE.md`, and behavior-neutral. Within the spirit of Touches; recorded here.
- **Done-check exceeded** — added `cargo test` units (the §t3-invited pure-helper tests) beyond the stated compile+sweep+drift gate; all green.

## Surprises

- **Terminal-text runs are not forkable, and it bit the verification.** A run that ends on a text response records `run_complete` with no `:step_complete` (t2's finding) — so most real runs in the dev store are not fork points. Confirmed while hunting a source: `mix aetheris --json fork` on a run without a `:step_complete` at `step` returns `:step_not_found` (correctly). The verification source had to be a tool-call-step run (created a stub one).
- **Dev store vs test DB.** `fork-source-*` trajectories from t2's tests exist as files under `priv/runs/` but are not in the dev SQLite store, so `mix aetheris fork` on them fails at `lookup_run` (the CLI requires the source in the store). Verification used a run created in the dev store.

## Done-check results

| Gate | Result |
|---|---|
| `cd rig/src-tauri && cargo build` | Finished, exit 0 |
| camelCase invoke sweep (from `rig/`) | 2 benign baseline hits only (command name `provenance_set_classification_status`; value `trajectory.run_id`); no new key — no UI added, per §t3 |
| `python3 scripts/drift_check.py` | 8 PASS · 0 FAIL · 0 WARN · 7 INFO; `tauri_commands` now 48 (was 47), `fork_run` matched lib.rs ↔ specs §4 |
| `cargo test` | 11 passed, 0 failed — `fork_argv`×2, `parse_run_id`×2, `root_from_db_path`, `traj_path_under` (F6), + 5 pre-existing db tests |
| **End-to-end fork** (human-verified exception) | **Headless portion verified:** created a stub forkable source in the dev store, ran the real subprocess `mix aetheris --json fork <traj> --step 0` → stdout `{"status":"done","run_id":"fork-80cf8333fb4edc14"}`; `parse_run_id` emulation extracted `fork-80cf8333fb4edc14`; forked meta = `fork_from: t3-fork-src-452`, `fork_step: 0`, `mode: "record"`, `seed: 7` (carried). **Pending-human:** invoke `fork_run(runId, step)` from the running Rig app and confirm the child run surfaces (the Tauri IPC round-trip only — the command logic and CLI seam are verified above). |

## Open items forwarded

- **Rig `label` read defect** (`harness.rs:82,196` read `config_json.$.label` where `encode_config` strips it → labels never surface). One-line-per-site SQL fix to read `r.label`. Recommend t5 carry list or standalone Rig ticket.
- **Early-returning `fork_run`** — now `async` (off the UI thread) but still **blocks to completion**: the invoke promise resolves only when the forked run finishes, because the CLI reveals the run id only at completion (`await_run`). A spawn-and-return-early variant (surface the child run immediately, like `orchestrate_start`) would need the harness CLI to emit the run id at fork-start — a harness change, out of t3 scope. Flagged for t4 (progress affordance) and as a possible future harness enhancement.
