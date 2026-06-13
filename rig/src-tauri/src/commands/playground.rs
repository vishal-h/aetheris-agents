use std::collections::HashMap;
use tauri::State;

// ============================================================================
// State
// ============================================================================

/// Managed state for the playground API connection.
/// `api_token` is intentionally NOT `serde::Serialize` — it must never appear
/// in a Tauri command response, TS type, or log output.
pub struct PlaygroundState {
    pub api_url:   Option<String>,
    pub api_token: Option<String>,
}

// ============================================================================
// Response types (all serializable to TS)
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PlaygroundStatus {
    pub connected: bool,
    pub api_url:   Option<String>,
    pub error:     Option<String>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PolicyCaps {
    pub max_steps:        Option<i64>,
    pub max_spawn_depth:  Option<i64>,
    pub max_tokens:       Option<i64>,
    pub max_prompt_chars: Option<i64>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PolicyDefaults {
    pub max_steps:        Option<i64>,
    pub max_spawn_depth:  Option<i64>,
    pub context_strategy: Option<String>,
    pub tools:            Option<Vec<String>>,
    pub user_prompt:      Option<String>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PlaygroundPolicy {
    pub providers: Vec<String>,
    pub models:    HashMap<String, Vec<String>>,
    pub tools:     Vec<String>,
    pub caps:      PolicyCaps,
    pub defaults:  PolicyDefaults,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct SandboxEntry {
    pub id:          String,
    pub description: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PlaygroundSandboxes {
    pub sandboxes: Vec<SandboxEntry>,
}

/// Request body for POST /api/playground/runs.
/// All fields mirror `playground-api.md` §3.3 known client-settable fields.
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PlaygroundSubmitRequest {
    pub sandbox_id:        String,
    pub provider:          String,
    pub model:             String,
    pub system_prompt:     String,
    pub user_prompt:       Option<String>,
    pub tools:             Option<Vec<String>>,
    pub max_steps:         Option<i64>,
    pub max_spawn_depth:   Option<i64>,
    pub max_tokens:        Option<i64>,
    pub label:             Option<String>,
    pub context_strategy:  Option<String>,
    pub max_context_steps: Option<i64>,
    pub temperature:       Option<f64>,
    pub top_p:             Option<f64>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PlaygroundSubmitResult {
    pub run_id: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct PlaygroundRunStatus {
    pub run_id:      String,
    pub status:      String,
    pub step_count:  i64,
    pub started_at:  String,
    pub finished_at: Option<String>,
    pub label:       Option<String>,
}

// ============================================================================
// playground_connection_status
// ============================================================================

/// Always returns Ok — frontend gates on `data.connected`, not the Result.
/// Follows the `harness_connection_status` pattern exactly.
#[tauri::command]
pub fn playground_connection_status(
    state: State<'_, PlaygroundState>,
) -> Result<PlaygroundStatus, String> {
    match (&state.api_url, &state.api_token) {
        (Some(url), Some(_token)) => {
            // Probe the policy endpoint: a 200 or 401 both mean the server is up;
            // a connection error means it is not.
            let client = reqwest::blocking::Client::new();
            match client
                .get(format!("{}/api/playground/policy", url))
                .send()
            {
                Ok(_) => Ok(PlaygroundStatus {
                    connected: true,
                    api_url:   Some(url.clone()),
                    error:     None,
                }),
                Err(e) => Ok(PlaygroundStatus {
                    connected: false,
                    api_url:   Some(url.clone()),
                    error:     Some(format!("connection failed: {}", e)),
                }),
            }
        }
        (None, _) => Ok(PlaygroundStatus {
            connected: false,
            api_url:   None,
            error:     Some("AETHERIS_API_URL is not set".to_string()),
        }),
        (_, None) => Ok(PlaygroundStatus {
            connected: false,
            api_url:   state.api_url.clone(),
            error:     Some("AETHERIS_API_TOKEN is not set".to_string()),
        }),
    }
}

// ============================================================================
// playground_get_policy
// ============================================================================

#[tauri::command]
pub fn playground_get_policy(
    state: State<'_, PlaygroundState>,
) -> Result<PlaygroundPolicy, String> {
    let (url, token) = require_connection(&state)?;
    let client = reqwest::blocking::Client::new();

    let resp = client
        .get(format!("{}/api/playground/policy", url))
        .header("Authorization", format!("Bearer {}", token))
        .send()
        .map_err(|e| format!("request failed: {}", e))?;

    if resp.status().is_success() {
        resp.json::<PlaygroundPolicy>()
            .map_err(|e| format!("parse error: {}", e))
    } else {
        Err(format!("API error {}: {}", resp.status(), resp.text().unwrap_or_default()))
    }
}

// ============================================================================
// playground_get_sandboxes
// ============================================================================

#[tauri::command]
pub fn playground_get_sandboxes(
    state: State<'_, PlaygroundState>,
) -> Result<PlaygroundSandboxes, String> {
    let (url, token) = require_connection(&state)?;
    let client = reqwest::blocking::Client::new();

    let resp = client
        .get(format!("{}/api/playground/sandboxes", url))
        .header("Authorization", format!("Bearer {}", token))
        .send()
        .map_err(|e| format!("request failed: {}", e))?;

    if resp.status().is_success() {
        resp.json::<PlaygroundSandboxes>()
            .map_err(|e| format!("parse error: {}", e))
    } else {
        Err(format!("API error {}: {}", resp.status(), resp.text().unwrap_or_default()))
    }
}

// ============================================================================
// playground_submit_run
// ============================================================================

/// Submits a run to POST /api/playground/runs.
/// On 422 (policy violation), returns Err with the raw JSON body so the
/// frontend hook can parse it as a structured error with violations.
#[tauri::command]
pub fn playground_submit_run(
    state:   State<'_, PlaygroundState>,
    request: PlaygroundSubmitRequest,
) -> Result<PlaygroundSubmitResult, String> {
    let (url, token) = require_connection(&state)?;
    let client = reqwest::blocking::Client::new();

    let resp = client
        .post(format!("{}/api/playground/runs", url))
        .header("Authorization", format!("Bearer {}", token))
        .header("Content-Type", "application/json")
        .json(&request)
        .send()
        .map_err(|e| format!("request failed: {}", e))?;

    let status = resp.status();
    let body = resp.text().unwrap_or_default();

    if status.as_u16() == 202 {
        serde_json::from_str::<PlaygroundSubmitResult>(&body)
            .map_err(|e| format!("parse error: {}", e))
    } else {
        // Return the raw JSON body so the frontend can parse violations (422)
        // or display the error message. Never log the token.
        Err(body)
    }
}

// ============================================================================
// playground_run_status
// ============================================================================

#[tauri::command]
pub fn playground_run_status(
    state:  State<'_, PlaygroundState>,
    run_id: String,
) -> Result<PlaygroundRunStatus, String> {
    let (url, token) = require_connection(&state)?;
    let client = reqwest::blocking::Client::new();

    let resp = client
        .get(format!("{}/api/playground/runs/{}", url, run_id))
        .header("Authorization", format!("Bearer {}", token))
        .send()
        .map_err(|e| format!("request failed: {}", e))?;

    if resp.status().is_success() {
        resp.json::<PlaygroundRunStatus>()
            .map_err(|e| format!("parse error: {}", e))
    } else if resp.status().as_u16() == 404 {
        Err(format!("run {} not found", run_id))
    } else {
        Err(format!("API error {}: {}", resp.status(), resp.text().unwrap_or_default()))
    }
}

// ============================================================================
// Private helpers
// ============================================================================

fn require_connection(
    state: &State<'_, PlaygroundState>,
) -> Result<(String, String), String> {
    let url = state
        .api_url
        .clone()
        .ok_or_else(|| "AETHERIS_API_URL is not set".to_string())?;
    let token = state
        .api_token
        .clone()
        .ok_or_else(|| "AETHERIS_API_TOKEN is not set".to_string())?;
    Ok((url, token))
}
