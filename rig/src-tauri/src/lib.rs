mod commands;
mod db;
mod modules;

use duckdb::{AccessMode, Config};
use std::collections::HashMap;
use std::sync::atomic::AtomicBool;
use std::sync::{Arc, Mutex};
use tauri::Manager;

pub struct CorpusState {
    pub conn: Option<Arc<Mutex<duckdb::Connection>>>,
    pub path: Option<String>,
}

pub struct HarnessState {
    pub conn: Option<Arc<Mutex<rusqlite::Connection>>>,
    pub path: Option<String>,
}

pub struct OrchestratorJob {
    pub child:  Arc<Mutex<std::process::Child>>,
    pub stdin:  Arc<Mutex<std::process::ChildStdin>>,
    pub buffer: Arc<Mutex<Vec<serde_json::Value>>>,
    pub done:   Arc<AtomicBool>,
}

pub struct OrchestratorState {
    pub jobs:         Mutex<HashMap<String, OrchestratorJob>>,
    pub agents_path:  Option<String>,
    pub aetheris_dir: Option<String>,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![
      commands::f2::f2_get_watched_folders,
      commands::f2::f2_add_watched_folder,
      commands::f2::f2_toggle_watched_folder,
      commands::f2::f2_remove_watched_folder,
      commands::f2::f2_trigger_scan,
      commands::f2::f2_get_file_index,
      commands::f2::f2_get_file_count,
      commands::f2::f2_get_duplicates,
      commands::f2::f2_get_duplicate_stats,
      commands::provenance::provenance_corpus_summary,
      commands::provenance::provenance_client_breakdown,
      commands::provenance::provenance_scan_runs,
      commands::provenance::provenance_classification_list,
      commands::provenance::provenance_set_classification_status,
      commands::provenance::provenance_migration_summary,
      commands::provenance::provenance_zip_inventory,
      commands::provenance::provenance_duplicate_groups,
      commands::provenance::get_system_username,
      commands::provenance::provenance_failed_migrations,
      commands::provenance::provenance_encrypted_zips,
      commands::harness::harness_connection_status,
      commands::harness::harness_list_runs,
      commands::harness::harness_get_events,
      commands::harness::harness_get_run,
      commands::orchestrate::orchestrate_start,
      commands::orchestrate::orchestrate_poll,
      commands::orchestrate::orchestrate_approve,
      commands::orchestrate::orchestrate_cancel,
      commands::trajectory::trajectory_load,
      commands::trajectory::trajectory_export,
      commands::capability_matrix::capability_matrix_load,
    ])
    .plugin(tauri_plugin_dialog::init())
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // Initialize app database
      let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to resolve app data directory: {}", e))?;

      let db_conn = db::init(&app_data_dir)
        .map_err(|e| format!("Database initialization failed: {}", e))?;

      app.manage(db_conn);

      // Open corpus DB read-only if PROVENANCE_DB_PATH is set
      let corpus_state = match std::env::var("PROVENANCE_DB_PATH") {
        Ok(path) => {
          match Config::default()
            .access_mode(AccessMode::ReadOnly)
            .and_then(|cfg| duckdb::Connection::open_with_flags(&path, cfg))
          {
            Ok(conn) => {
              log::info!("Corpus DB opened: {}", path);
              CorpusState {
                conn: Some(Arc::new(Mutex::new(conn))),
                path: Some(path),
              }
            }
            Err(e) => {
              log::warn!("Cannot open corpus DB {}: {}", path, e);
              CorpusState { conn: None, path: None }
            }
          }
        }
        Err(_) => {
          log::info!("PROVENANCE_DB_PATH not set — corpus commands unavailable");
          CorpusState { conn: None, path: None }
        }
      };

      app.manage(corpus_state);

      // Open harness DB read-only if AETHERIS_DB_PATH is set
      let harness_state = match std::env::var("AETHERIS_DB_PATH") {
        Ok(path) => {
          match rusqlite::Connection::open_with_flags(
            &path,
            rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY
              | rusqlite::OpenFlags::SQLITE_OPEN_NO_MUTEX,
          ) {
            Ok(conn) => {
              log::info!("Harness DB opened: {}", path);
              HarnessState {
                conn: Some(Arc::new(Mutex::new(conn))),
                path: Some(path),
              }
            }
            Err(e) => {
              log::warn!("Cannot open harness DB {}: {}", path, e);
              HarnessState { conn: None, path: None }
            }
          }
        }
        Err(_) => {
          log::info!("AETHERIS_DB_PATH not set — harness commands unavailable");
          HarnessState { conn: None, path: None }
        }
      };

      app.manage(harness_state);

      let agents_path = std::env::var("AETHERIS_AGENTS_PATH").ok();
      let aetheris_dir = std::env::var("AETHERIS_DB_PATH").ok().and_then(|p| {
        std::path::Path::new(&p)
          .parent()
          .and_then(|p| p.parent())
          .map(|p| p.to_string_lossy().to_string())
      });
      app.manage(OrchestratorState {
        jobs:        Mutex::new(HashMap::new()),
        agents_path,
        aetheris_dir,
      });

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
