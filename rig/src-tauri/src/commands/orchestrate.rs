use crate::OrchestratorState;
use std::io::BufRead;
use std::sync::atomic::Ordering;
use std::sync::{Arc, Mutex};
use tauri::State;

#[tauri::command]
pub fn orchestrate_start(
    state: State<'_, OrchestratorState>,
    request: String,
) -> Result<String, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;
    let aetheris_dir = state.aetheris_dir.as_ref()
        .ok_or("aetheris dir unavailable — is AETHERIS_DB_PATH set?")?;

    let script_path = format!("{}/agents/orchestrator.exs", agents_path);

    let mut child = std::process::Command::new("mix")
        .args(["run", &script_path])
        .env("ORCHESTRATOR_REQUEST", &request)
        .current_dir(aetheris_dir)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())
        .spawn()
        .map_err(|e| format!("spawn failed: {}", e))?;

    let stdin  = Arc::new(Mutex::new(child.stdin.take().unwrap()));
    let stdout = child.stdout.take().unwrap();

    let buffer: Arc<Mutex<Vec<serde_json::Value>>> = Arc::new(Mutex::new(vec![]));
    let done   = Arc::new(std::sync::atomic::AtomicBool::new(false));

    let buf_clone  = buffer.clone();
    let done_clone = done.clone();

    std::thread::spawn(move || {
        for line in std::io::BufReader::new(stdout).lines() {
            if let Ok(l) = line {
                let trimmed = l.trim().to_string();
                if !trimmed.is_empty() {
                    if let Ok(v) = serde_json::from_str::<serde_json::Value>(&trimmed) {
                        buf_clone.lock().unwrap().push(v);
                    }
                }
            }
        }
        done_clone.store(true, Ordering::Relaxed);
    });

    let job_id = format!(
        "orch-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis()
    );

    state.jobs.lock().unwrap().insert(
        job_id.clone(),
        crate::OrchestratorJob { child: Arc::new(Mutex::new(child)), stdin, buffer, done },
    );

    Ok(job_id)
}

#[derive(serde::Serialize)]
pub struct PollResult {
    pub messages: Vec<serde_json::Value>,
    pub done:     bool,
}

#[tauri::command]
pub fn orchestrate_poll(
    state: State<'_, OrchestratorState>,
    job_id: String,
) -> Result<PollResult, String> {
    let jobs = state.jobs.lock().unwrap();
    let job  = jobs.get(&job_id).ok_or("job not found")?;

    let messages: Vec<serde_json::Value> = job.buffer.lock().unwrap().drain(..).collect();
    let done = job.done.load(Ordering::Relaxed);

    Ok(PollResult { messages, done })
}

#[tauri::command]
pub fn orchestrate_approve(
    state: State<'_, OrchestratorState>,
    job_id:   String,
    approved: bool,
) -> Result<(), String> {
    use std::io::Write;
    let stdin = {
        let jobs = state.jobs.lock().unwrap();
        let job  = jobs.get(&job_id).ok_or("job not found")?;
        job.stdin.clone()
    };
    let msg = serde_json::json!({ "approved": approved, "type": "approval" });
    let mut guard = stdin.lock().unwrap();
    let result = writeln!(guard, "{}", msg)
        .map_err(|e| format!("stdin write failed: {}", e));
    result
}

#[tauri::command]
pub fn orchestrate_cancel(
    state:  State<'_, OrchestratorState>,
    job_id: String,
) -> Result<(), String> {
    let mut jobs = state.jobs.lock().unwrap();
    if let Some(job) = jobs.remove(&job_id) {
        let _ = job.child.lock().unwrap().kill();
    }
    Ok(())
}
