use std::path::Path;
use tauri::State;
use crate::HarnessState;

#[derive(serde::Serialize)]
pub struct TrajectoryEvent {
    pub id:         String,
    pub run_id:     String,
    pub seq:        i64,
    pub step:       i64,
    pub event_type: String,
    pub payload:    serde_json::Value,
    pub timestamp:  String,
}

#[derive(serde::Serialize)]
pub struct TrajectoryFile {
    pub run_id:         String,
    pub schema_version: String,
    pub meta:           serde_json::Value,
    pub events:         Vec<TrajectoryEvent>,
}

fn traj_path(run_id: &str) -> Result<std::path::PathBuf, String> {
    let db_path = std::env::var("AETHERIS_DB_PATH")
        .map_err(|_| "AETHERIS_DB_PATH not set".to_string())?;

    Path::new(&db_path)
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.join("priv").join("runs").join(run_id).join("trajectory.json"))
        .ok_or_else(|| "could not derive trajectory path from AETHERIS_DB_PATH".to_string())
}

#[tauri::command]
pub fn trajectory_load(
    _state: State<'_, HarnessState>,
    run_id: String,
) -> Result<TrajectoryFile, String> {
    let path = traj_path(&run_id)?;

    let raw = std::fs::read_to_string(&path)
        .map_err(|e| format!("read failed: {}", e))?;

    let v: serde_json::Value = serde_json::from_str(&raw)
        .map_err(|e| format!("parse failed: {}", e))?;

    let run_id_out      = v["run_id"].as_str().unwrap_or("").to_string();
    let schema_version  = v["schema_version"].as_str().unwrap_or("1").to_string();
    let meta            = v["meta"].clone();

    let events = v["events"]
        .as_array()
        .ok_or("events not an array")?
        .iter()
        .map(|e| TrajectoryEvent {
            id:         e["id"].as_str().unwrap_or("").to_string(),
            run_id:     e["run_id"].as_str().unwrap_or("").to_string(),
            seq:        e["seq"].as_i64().unwrap_or(0),
            step:       e["step"].as_i64().unwrap_or(0),
            event_type: e["type"].as_str().unwrap_or("").to_string(),
            payload:    e["payload"].clone(),
            timestamp:  e["timestamp"].as_str().unwrap_or("").to_string(),
        })
        .collect();

    Ok(TrajectoryFile { run_id: run_id_out, schema_version, meta, events })
}

#[tauri::command]
pub async fn trajectory_export(
    app:    tauri::AppHandle,
    run_id: String,
) -> Result<(), String> {
    use tauri_plugin_dialog::DialogExt;

    let src = traj_path(&run_id)?;

    let dest = app
        .dialog()
        .file()
        .set_file_name(format!("trajectory-{}.json", run_id))
        .blocking_save_file();

    if let Some(path) = dest {
        std::fs::copy(&src, path.as_path().unwrap())
            .map_err(|e| format!("copy failed: {}", e))?;
    }

    Ok(())
}
