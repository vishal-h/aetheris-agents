use crate::commands::trajectory::{aetheris_root, traj_path};
use std::io::{BufRead, BufReader, Read};
use std::process::{ChildStderr, ChildStdout, Stdio};

/// Fork a completed run at `step` via the post-t2 CLI
/// (`mix aetheris fork <trajectory> --step N [--name label]`, converged on
/// `Fork.from_step/3`).
///
/// Resolves the source run's trajectory path from `run_id`, spawns the CLI in
/// the aetheris repo root, and returns the forked run's id parsed from the CLI's
/// fork-*start* line. The child run executes in `:record` mode and is identified
/// by `meta.fork_from` (t2 convention); it is not a `:fork` mode.
///
/// **Returns early; Rig owns the subprocess (BL-030).** The CLI emits
/// `{"status":"forked","run_id":"…"}` as soon as the fork run is started, then
/// blocks to completion as before and prints its result line at the end. That
/// block is load-bearing and must not be interrupted: the fork run is a Task in
/// the CLI process's own supervision tree (`Aetheris.RunSupervisor`), so the
/// process has to stay alive for the run to finish. This command therefore does
/// **not** wait for exit — it reads stdout only until the first `run_id` line,
/// returns it, and hands the still-running child to a detached thread that
/// drains both pipes to EOF and reaps it. The pattern is `orchestrate.rs`'s
/// owned-subprocess shape; the run outlives the invoke, not the app.
///
/// The command stays `async` on `spawn_blocking`: the wait is now seconds (mix
/// boot + fork start) rather than minutes, but it is still blocking, and Tauri
/// v2 runs *sync* commands on the main thread.
///
/// **Start failure.** A fork that never starts — `step_not_found`, an unreadable
/// trajectory, a config error — fails inside `Fork.from_step/3` before any run
/// exists, so no `run_id` line is ever written and stdout reaches EOF. The CLI
/// reports the reason on *stderr* with a zero exit code (`mix` discards the CLI
/// exit code), so that is where the diagnosis lives: stderr stays piped and is
/// read on this path, preserving `fork failed: <reason>` — including BL-039
/// Part C's terminal-reason detail. Nulling stderr the way `orchestrate.rs`
/// does (it has no stderr contract) would silently degrade every start failure
/// to a bare "produced no run_id".
///
/// **Run failure is no longer this command's business.** A fork that starts and
/// then fails does so after this command has returned; the operator sees it on
/// the child run's own streamed trajectory, which is where the diagnosis was
/// always recorded.
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

/// The blocking body: spawn the CLI, read up to the fork-start line, hand off.
/// Runs off the UI thread via `spawn_blocking`.
fn fork_run_blocking(run_id: String, step: u64, label: Option<String>) -> Result<String, String> {
    let traj = traj_path(&run_id)?;
    let root = aetheris_root()?;
    let traj_str = traj.to_str().ok_or("trajectory path is not valid UTF-8")?;

    let mut child = std::process::Command::new("mix")
        .args(fork_argv(traj_str, step, label.as_deref()))
        .current_dir(&root)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("failed to spawn `mix aetheris fork`: {}", e))?;

    let stdout = child
        .stdout
        .take()
        .ok_or("fork subprocess produced no stdout pipe")?;
    let stderr = child
        .stderr
        .take()
        .ok_or("fork subprocess produced no stderr pipe")?;

    // stderr is drained on its own thread from the moment of spawn, in both
    // outcomes. A start failure needs its contents, and a successful fork must
    // not be able to wedge on a full stderr pipe while nobody is reading it —
    // one collector satisfies both, so neither pipe can deadlock the run.
    let stderr_collector = std::thread::spawn(move || collect(stderr));

    let mut reader = BufReader::new(stdout);

    match read_first_run_id(&mut reader) {
        // Started. Hand the child off: drain the rest of stdout to EOF and reap,
        // so the run completes and leaves no zombie. Nothing here is awaited.
        Some(forked_run_id) => {
            std::thread::spawn(move || {
                drain(&mut reader);
                let _ = stderr_collector.join();
                let _ = child.wait();
            });
            Ok(forked_run_id)
        }

        // Never started: stdout hit EOF with no run_id line. The reason is on
        // stderr — surface it verbatim, preserving the `fork failed: <reason>`
        // shape the UI and its error-strip were built against.
        None => {
            let detail = stderr_collector.join().unwrap_or_default();
            let _ = child.wait();
            Err(start_failure_error(&detail))
        }
    }
}

/// Build the `mix` argv for the fork invocation. `--json` (a global CLI flag)
/// must precede the `fork` subcommand so the CLI emits machine-parseable lines.
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

/// Extract a run id from one stdout line, if it carries one.
///
/// This is the predicate the pre-BL-030 `parse_run_id` applied while scanning
/// the whole buffer backwards; only the scan direction changed, not what counts
/// as a run_id line. `mix` compile and log noise shares stdout and does not
/// parse as JSON, so no filtering beyond "is a JSON object with a string
/// `run_id`" is needed.
fn run_id_from_line(line: &str) -> Option<String> {
    serde_json::from_str::<serde_json::Value>(line.trim())
        .ok()
        .and_then(|v| v.get("run_id").and_then(|r| r.as_str()).map(String::from))
}

/// Read stdout line by line and stop at the **first** line carrying a `run_id` —
/// the CLI's fork-start emit. Returns `None` if stdout reaches EOF without one.
///
/// First-wins is safe here, and the reader deliberately does not try to
/// disambiguate further: `await_run`'s verbose event stream goes to stderr, and
/// under `--json` the closing `Formatter.print/2` writes exactly once, so the
/// only JSON-with-`run_id` lines on stdout are this start line and the eventual
/// completion line. Stopping at the first is what makes the command return in
/// seconds instead of minutes — the whole point of BL-030.
fn read_first_run_id<R: BufRead>(reader: &mut R) -> Option<String> {
    let mut line = String::new();
    loop {
        line.clear();
        match reader.read_line(&mut line) {
            Ok(0) => return None,
            Ok(_) => {
                if let Some(id) = run_id_from_line(&line) {
                    return Some(id);
                }
            }
            Err(_) => return None,
        }
    }
}

/// Render the error for a fork that never started. Preserves the `fork failed:`
/// prefix `useFork.ts` strips and the UI's error strip re-labels.
fn start_failure_error(stderr: &str) -> String {
    let detail = stderr.trim();
    if detail.is_empty() {
        "fork produced no run_id and reported no error".to_string()
    } else {
        format!("fork failed: {}", detail)
    }
}

/// Read a pipe to EOF and return it as a lossy string.
fn collect(mut pipe: ChildStderr) -> String {
    let mut buf = Vec::new();
    let _ = pipe.read_to_end(&mut buf);
    String::from_utf8_lossy(&buf).into_owned()
}

/// Discard the remainder of a pipe so the child never blocks on a full buffer.
fn drain(reader: &mut BufReader<ChildStdout>) {
    let mut sink = Vec::new();
    let _ = reader.read_to_end(&mut sink);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

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
    fn read_first_run_id_returns_the_start_line_id() {
        let out = "Compiling 2 files (.ex)\n\
                   {\"status\":\"forked\",\"run_id\":\"fork-abc123\"}\n\
                   {\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n";
        let mut cursor = Cursor::new(out);
        assert_eq!(read_first_run_id(&mut cursor), Some("fork-abc123".to_string()));
    }

    /// The early-return property, asserted structurally rather than by wall
    /// clock: after the id is read, the completion line must still be unread in
    /// the stream. A reader that drained to EOF first (the old last-wins scan)
    /// would leave nothing behind and fail this.
    #[test]
    fn read_first_run_id_stops_before_the_completion_line() {
        let out = "{\"status\":\"forked\",\"run_id\":\"fork-abc123\"}\n\
                   {\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n";
        let mut cursor = Cursor::new(out);

        assert_eq!(read_first_run_id(&mut cursor), Some("fork-abc123".to_string()));

        let mut rest = String::new();
        cursor.read_to_string(&mut rest).unwrap();
        assert_eq!(rest, "{\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n");
    }

    #[test]
    fn read_first_run_id_none_on_eof_without_a_run_id() {
        // A fork that never starts: no run_id line is ever written to stdout.
        let mut cursor = Cursor::new("no json here\n{\"status\":\"error\"}\n");
        assert_eq!(read_first_run_id(&mut cursor), None);
    }

    /// A start failure must carry the CLI's stderr reason (BL-039 Part C's
    /// diagnosis), not a generic "no run_id" line.
    #[test]
    fn start_failure_error_carries_the_stderr_reason() {
        assert_eq!(
            start_failure_error("Error: failed to build fork config: :step_not_found\n"),
            "fork failed: Error: failed to build fork config: :step_not_found"
        );
    }

    #[test]
    fn start_failure_error_without_stderr_says_so() {
        assert_eq!(
            start_failure_error("   \n"),
            "fork produced no run_id and reported no error"
        );
    }
}
