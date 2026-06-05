use crate::AgentConfigState;
use std::collections::HashMap;
use tauri::State;

fn persist(state: &AgentConfigState) -> Result<(), String> {
    let cache = state.cache.lock().unwrap();
    let json = serde_json::to_string_pretty(&*cache)
        .map_err(|e| format!("serialise failed: {}", e))?;
    std::fs::write(&state.store_path, json)
        .map_err(|e| format!("write failed: {}", e))
}

#[tauri::command]
pub fn agent_config_get_all(
    state: State<'_, AgentConfigState>,
) -> Result<HashMap<String, String>, String> {
    Ok(state.cache.lock().unwrap().clone())
}

#[tauri::command]
pub fn agent_config_set(
    state: State<'_, AgentConfigState>,
    key:   String,
    value: String,
) -> Result<(), String> {
    state.cache.lock().unwrap().insert(key, value);
    persist(&state)
}

#[tauri::command]
pub fn agent_config_delete(
    state: State<'_, AgentConfigState>,
    key:   String,
) -> Result<(), String> {
    state.cache.lock().unwrap().remove(&key);
    persist(&state)
}

#[tauri::command]
pub fn agent_config_export(
    state: State<'_, AgentConfigState>,
) -> Result<String, String> {
    let cache = state.cache.lock().unwrap();
    serde_json::to_string_pretty(&*cache)
        .map_err(|e| format!("serialise failed: {}", e))
}

#[tauri::command]
pub fn agent_config_import(
    state:  State<'_, AgentConfigState>,
    values: HashMap<String, String>,
) -> Result<usize, String> {
    let count = values.len();
    {
        let mut cache = state.cache.lock().unwrap();
        for (k, v) in values {
            cache.insert(k, v);
        }
    }
    persist(&state)?;
    Ok(count)
}
