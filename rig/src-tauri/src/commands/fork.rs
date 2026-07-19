use crate::commands::trajectory::{aetheris_root, traj_path};

/// Fork a completed run at `step` via the post-t2 CLI
/// (`mix aetheris fork <trajectory> --step N [--name label]`, converged on
/// `Fork.from_step/3`).
///
/// Resolves the source run's trajectory path from `run_id`, spawns the CLI in
/// the aetheris repo root, and returns the forked run's id parsed from the CLI's
/// JSON result line. The child run executes in `:record` mode and is identified
/// by `meta.fork_from` (t2 convention); it is not a `:fork` mode.
///
/// **Async, blocks to completion.** `mix aetheris fork` blocks until the forked
/// run reaches a terminal status (the CLI's `await_run` contract), and only then
/// prints the run id — so this command cannot spawn-and-return an id early like
/// `orchestrate_start` (the id does not exist until completion; changing that is a
/// harness concern). The command is therefore `async` and runs the blocking
/// subprocess on `spawn_blocking`, so a long (real-provider) fork does not freeze
/// the UI thread (Tauri v2 runs *sync* commands on the main thread). The invoke
/// promise still resolves only when the fork finishes — a progress affordance is
/// t4's concern.
///
/// **Terminal status.** A run id appears on stdout only for a `done` fork. The CLI
/// turns `failed`/`cancelled` into an error on *stderr* with a zero exit code
/// (`mix` discards the CLI exit code), so a non-`done` fork yields no stdout id and
/// this command returns `Err` carrying the CLI's stderr — it never reports a failed
/// fork as success.
///
/// **`label` caveat.** `label` maps to CLI `--name` → `RunConfig.label`, durably
/// stored in the harness `runs.label` column. Rig's own `harness_list_runs` /
/// `harness_get_run` read the label from `config_json` (`harness.rs:82,196`), where
/// `encode_config` strips it (`../aetheris/.../server.ex:758`) — so a fork label is
/// persisted but not surfaced by Rig today. See the t3 notes' label finding.
#[tauri::command]
pub async fn fork_run(
    run_id: String,
    step: u64,
    label: Option<String>,
) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || fork_run_blocking(run_id, step, label))
        .await
        .map_err(|e| format!("fork task failed to run: {}", e))?
}

/// The blocking body: spawn the CLI and parse the result. Runs off the UI thread
/// via `spawn_blocking`.
fn fork_run_blocking(run_id: String, step: u64, label: Option<String>) -> Result<String, String> {
    let traj = traj_path(&run_id)?;
    let root = aetheris_root()?;
    let traj_str = traj.to_str().ok_or("trajectory path is not valid UTF-8")?;

    let output = std::process::Command::new("mix")
        .args(fork_argv(traj_str, step, label.as_deref()))
        .current_dir(&root)
        .output()
        .map_err(|e| format!("failed to spawn `mix aetheris fork`: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);

    // A run id is present on stdout only for a `done` fork. Absence means the CLI
    // reported an error on stderr (with a zero exit code) — surface it verbatim so
    // a `failed`/`cancelled`/`step_not_found` fork is never mistaken for success.
    parse_run_id(&stdout).ok_or_else(|| {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let detail = stderr.trim();
        if detail.is_empty() {
            format!("fork produced no run_id; stdout: {}", stdout.trim())
        } else {
            format!("fork failed: {}", detail)
        }
    })
}

/// Build the `mix` argv for the fork invocation. `--json` (a global CLI flag)
/// must precede the `fork` subcommand so the CLI emits a machine-parseable line.
fn fork_argv(traj: &str, step: u64, label: Option<&str>) -> Vec<String> {
    let mut args = vec![
        "aetheris".to_string(),
        "--json".to_string(),
        "fork".to_string(),
        traj.to_string(),
        "--step".to_string(),
        step.to_string(),
    ];
    if let Some(name) = label {
        args.push("--name".to_string());
        args.push(name.to_string());
    }
    args
}

/// Extract the forked run id from the CLI's stdout. The `--json` result is one
/// line, but mix/compile/log noise may share stdout, so scan from the end for the
/// last JSON object carrying a `run_id`.
fn parse_run_id(stdout: &str) -> Option<String> {
    stdout.lines().rev().find_map(|line| {
        serde_json::from_str::<serde_json::Value>(line.trim())
            .ok()
            .and_then(|v| v.get("run_id").and_then(|r| r.as_str()).map(String::from))
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn svec(a: &[&str]) -> Vec<String> {
        a.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn fork_argv_without_label() {
        assert_eq!(
            fork_argv("/p/runs/r1/trajectory.json", 3, None),
            svec(&["aetheris", "--json", "fork", "/p/runs/r1/trajectory.json", "--step", "3"])
        );
    }

    #[test]
    fn fork_argv_with_label() {
        assert_eq!(
            fork_argv("/p/t.json", 0, Some("my fork")),
            svec(&["aetheris", "--json", "fork", "/p/t.json", "--step", "0", "--name", "my fork"])
        );
    }

    #[test]
    fn parse_run_id_finds_last_json_line() {
        let out = "Compiling 2 files (.ex)\n{\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n";
        assert_eq!(parse_run_id(out), Some("fork-abc123".to_string()));
    }

    #[test]
    fn parse_run_id_none_when_absent() {
        // A `failed`/`cancelled` fork prints its error to stderr, not a run_id line.
        assert_eq!(parse_run_id("no json here\n{\"status\":\"done\"}\n"), None);
    }
}
