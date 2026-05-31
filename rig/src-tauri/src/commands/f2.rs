use crate::db::DbConn;
use crate::modules::f2::scanner::{scan_directory, ScannerConfig};
use duckdb::params;
use std::sync::Arc;
use tauri::{AppHandle, State};

/// Serializable representation of a watched folder
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct WatchedFolder {
    pub id: i64,
    pub path: String,
    pub enabled: bool,
    pub ignore_globs: Option<String>,
    pub added_at: Option<String>,
    pub last_scan: Option<String>,
}

/// Serializable representation of a file entry from the index
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct FileEntry {
    pub id: i64,
    pub path: String,
    pub size_bytes: Option<i64>,
    pub modified_at: Option<i64>,
    pub mime_type: Option<String>,
    pub sha256: Option<String>,
    pub status: String,
    pub last_scanned: Option<String>,
}

/// Summary of duplicate groups
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct DuplicateGroup {
    pub sha256: String,
    pub file_count: i64,
    pub total_size: i64,
    pub wasted_bytes: i64,
    pub files: Vec<FileEntry>,
}

/// Statistics about duplicates
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct DuplicateStats {
    pub duplicate_count: i64,
    pub wasted_bytes: i64,
}

// ============================================================================
// Watched Folders Commands
// ============================================================================

/// Get all watched folders
#[tauri::command]
pub fn f2_get_watched_folders(db: State<'_, DbConn>) -> Result<Vec<WatchedFolder>, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let mut stmt = conn
        .prepare("SELECT id, path, enabled, ignore_globs, CAST(added_at AS VARCHAR) as added_at, CAST(last_scan AS VARCHAR) as last_scan FROM f2_watched_folders ORDER BY id")
        .map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let folders = stmt
        .query_map([], |row| {
            Ok(WatchedFolder {
                id: row.get(0)?,
                path: row.get(1)?,
                enabled: row.get(2)?,
                ignore_globs: row.get(3)?,
                added_at: row.get(4)?,
                last_scan: row.get(5)?,
            })
        })
        .map_err(|e| format!("Failed to query watched folders: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect results: {}", e))?;

    Ok(folders)
}

/// Add a new watched folder
#[tauri::command]
pub fn f2_add_watched_folder(path: String, db: State<'_, DbConn>) -> Result<WatchedFolder, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    // Insert the new watched folder and return the created record
    let folder = conn
        .query_row(
            "INSERT INTO f2_watched_folders (path, enabled) VALUES (?, true) RETURNING id, path, enabled, ignore_globs, CAST(added_at AS VARCHAR) as added_at, CAST(last_scan AS VARCHAR) as last_scan",
            params![&path],
            |row| {
                Ok(WatchedFolder {
                    id: row.get(0)?,
                    path: row.get(1)?,
                    enabled: row.get(2)?,
                    ignore_globs: row.get(3)?,
                    added_at: row.get(4)?,
                    last_scan: row.get(5)?,
                })
            },
        )
        .map_err(|e| format!("Failed to retrieve new watched folder: {}", e))?;

    Ok(folder)
}

/// Toggle a watched folder's enabled status
#[tauri::command]
pub fn f2_toggle_watched_folder(id: i64, enabled: bool, db: State<'_, DbConn>) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    conn.execute(
        "UPDATE f2_watched_folders SET enabled = ? WHERE id = ?",
        params![enabled, id],
    )
    .map_err(|e| format!("Failed to update watched folder: {}", e))?;

    Ok(())
}

/// Remove a watched folder
#[tauri::command]
pub fn f2_remove_watched_folder(id: i64, db: State<'_, DbConn>) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    conn.execute(
        "DELETE FROM f2_watched_folders WHERE id = ?",
        params![id],
    )
    .map_err(|e| format!("Failed to delete watched folder: {}", e))?;

    Ok(())
}

// ============================================================================
// Scan Commands
// ============================================================================

/// Trigger a scan of all enabled watched folders
#[tauri::command]
pub async fn f2_trigger_scan(app_handle: AppHandle, db: State<'_, DbConn>) -> Result<(), String> {
    // Clone the db Arc for use in the spawned task
    let db_clone = Arc::clone(&*db);

    // Get all enabled watched folders
    let watched_folders = {
        let conn = db_clone.lock().map_err(|e| format!("DB lock error: {}", e))?;

        let mut stmt = conn
            .prepare("SELECT id, path, ignore_globs FROM f2_watched_folders WHERE enabled = true")
            .map_err(|e| format!("Failed to prepare statement: {}", e))?;

        let folders = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, i64>(0)?,     // id
                    row.get::<_, String>(1)?,  // path
                    row.get::<_, Option<String>>(2)?, // ignore_globs
                ))
            })
            .map_err(|e| format!("Failed to query watched folders: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Failed to collect results: {}", e))?;

        folders
    };

    if watched_folders.is_empty() {
        return Err("No enabled watched folders to scan".to_string());
    }

    // Spawn a background task to scan all folders
    tokio::spawn(async move {
        for (folder_id, folder_path, ignore_globs) in watched_folders {
            log::info!("Starting scan of watched folder: {}", folder_path);

            let config = ScannerConfig {
                root_path: folder_path.clone().into(),
                ignore_globs: ignore_globs
                    .map(|s| s.split(',').map(|g| g.trim().to_string()).collect())
                    .unwrap_or_default(),
            };

            match scan_directory(config, db_clone.clone(), app_handle.clone()).await {
                Ok(_) => {
                    log::info!("Completed scan of: {}", folder_path);

                    // Update last_scan timestamp
                    if let Ok(conn) = db_clone.lock() {
                        let _ = conn.execute(
                            "UPDATE f2_watched_folders SET last_scan = CURRENT_TIMESTAMP WHERE id = ?",
                            params![folder_id],
                        );
                    }
                }
                Err(e) => {
                    log::error!("Failed to scan {}: {}", folder_path, e);
                }
            }
        }

        log::info!("All scans complete");
    });

    Ok(())
}

// ============================================================================
// File Index Commands
// ============================================================================

/// Get file index with optional pagination
#[tauri::command]
pub fn f2_get_file_index(
    limit: Option<i64>,
    offset: Option<i64>,
    db: State<'_, DbConn>,
) -> Result<Vec<FileEntry>, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let limit_val = limit.unwrap_or(100);
    let offset_val = offset.unwrap_or(0);

    let mut stmt = conn
        .prepare(
            "SELECT id, path, size_bytes, epoch(modified_at) as modified_at, mime_type, sha256, status, CAST(last_scanned AS VARCHAR) as last_scanned
             FROM f2_file_index
             ORDER BY last_scanned DESC
             LIMIT ? OFFSET ?",
        )
        .map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let entries = stmt
        .query_map(params![limit_val, offset_val], |row| {
            Ok(FileEntry {
                id: row.get(0)?,
                path: row.get(1)?,
                size_bytes: row.get(2)?,
                modified_at: row.get(3)?,
                mime_type: row.get(4)?,
                sha256: row.get(5)?,
                status: row.get(6)?,
                last_scanned: row.get(7)?,
            })
        })
        .map_err(|e| format!("Failed to query file index: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect results: {}", e))?;

    Ok(entries)
}

/// Get total count of files in the index
#[tauri::command]
pub fn f2_get_file_count(db: State<'_, DbConn>) -> Result<i64, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let count: i64 = conn
        .query_row("SELECT COUNT(*) FROM f2_file_index", [], |row| row.get(0))
        .map_err(|e| format!("Failed to count files: {}", e))?;

    Ok(count)
}

// ============================================================================
// Duplicate Detection Commands
// ============================================================================

/// Get all duplicate file groups
#[tauri::command]
pub fn f2_get_duplicates(db: State<'_, DbConn>) -> Result<Vec<DuplicateGroup>, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    // Get all hashes that have duplicates
    let mut stmt = conn
        .prepare(
            r#"
            SELECT sha256, COUNT(*) as count, SUM(size_bytes) as total_size
            FROM f2_file_index
            WHERE sha256 IS NOT NULL AND status != 'missing'
            GROUP BY sha256
            HAVING count > 1
            ORDER BY total_size DESC
            "#,
        )
        .map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let hash_groups: Vec<(String, i64, i64)> = stmt
        .query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, i64>(2)?,
            ))
        })
        .map_err(|e| format!("Failed to query duplicate hashes: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect results: {}", e))?;

    // For each hash group, get all files and build DuplicateGroup
    let mut duplicate_groups = Vec::new();

    for (sha256, file_count, total_size) in hash_groups {
        let mut file_stmt = conn
            .prepare(
                "SELECT id, path, size_bytes, epoch(modified_at) as modified_at, mime_type, sha256, status, CAST(last_scanned AS VARCHAR) as last_scanned
                 FROM f2_file_index
                 WHERE sha256 = ?
                 ORDER BY path",
            )
            .map_err(|e| format!("Failed to prepare file query: {}", e))?;

        let files = file_stmt
            .query_map(params![&sha256], |row| {
                Ok(FileEntry {
                    id: row.get(0)?,
                    path: row.get(1)?,
                    size_bytes: row.get(2)?,
                    modified_at: row.get(3)?,
                    mime_type: row.get(4)?,
                    sha256: row.get(5)?,
                    status: row.get(6)?,
                    last_scanned: row.get(7)?,
                })
            })
            .map_err(|e| format!("Failed to query files for hash: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Failed to collect file results: {}", e))?;

        // Calculate wasted bytes: (count - 1) * file_size
        let file_size = files.first().and_then(|f| f.size_bytes).unwrap_or(0);
        let wasted_bytes = (file_count - 1) * file_size;

        duplicate_groups.push(DuplicateGroup {
            sha256,
            file_count,
            total_size,
            wasted_bytes,
            files,
        });
    }

    Ok(duplicate_groups)
}

/// Get duplicate statistics
#[tauri::command]
pub fn f2_get_duplicate_stats(db: State<'_, DbConn>) -> Result<DuplicateStats, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    // Count total duplicate files
    let duplicate_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM f2_file_index WHERE status = 'duplicate'",
            [],
            |row| row.get(0),
        )
        .map_err(|e| format!("Failed to count duplicates: {}", e))?;

    // Calculate wasted bytes: for each hash with duplicates, (count - 1) * file_size
    let wasted_bytes: i64 = conn
        .query_row(
            r#"
            SELECT COALESCE(SUM((count - 1) * size_bytes), 0)
            FROM (
                SELECT COUNT(*) as count, MIN(size_bytes) as size_bytes
                FROM f2_file_index
                WHERE sha256 IS NOT NULL AND status != 'missing'
                GROUP BY sha256
                HAVING count > 1
            )
            "#,
            [],
            |row| row.get(0),
        )
        .map_err(|e| format!("Failed to calculate wasted bytes: {}", e))?;

    Ok(DuplicateStats {
        duplicate_count,
        wasted_bytes,
    })
}
