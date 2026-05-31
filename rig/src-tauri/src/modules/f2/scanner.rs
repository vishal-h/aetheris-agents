use crate::db::DbConn;
use digest::Digest;
use duckdb::params;
use glob::Pattern;
use mime_guess::from_path;
use sha2::Sha256;
use std::collections::HashSet;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::PathBuf;
use std::time::SystemTime;
use sysinfo::System;
use tauri::{AppHandle, Emitter};

/// Configuration for directory scanning
#[derive(Debug, Clone)]
pub struct ScannerConfig {
    pub root_path: PathBuf,
    pub ignore_globs: Vec<String>,
}

/// Progress information during scanning (serializable for Tauri events)
#[derive(Debug, Clone, serde::Serialize)]
pub struct ScanProgress {
    pub scanned: u64,
    pub total_estimate: u64,
    pub current_path: String,
    pub duplicates_found: u64,
}

/// Default ignore patterns that are always applied
const DEFAULT_IGNORE_PATTERNS: &[&str] = &[
    ".git/",
    "node_modules/",
    ".cache/",
    "*.sock",
    "*.pid",
    "/proc/",
    "/sys/",
    "/dev/",
];

/// Scan a directory, hash files, and update the database
///
/// # Arguments
/// * `config` - Scanner configuration with root path and ignore globs
/// * `db` - Database connection wrapped in Arc<Mutex<>>
/// * `app_handle` - Tauri app handle for emitting events
///
/// # Returns
/// * `Result<(), String>` - Success or error message
pub async fn scan_directory(
    config: ScannerConfig,
    db: DbConn,
    app_handle: AppHandle,
) -> Result<(), String> {
    log::info!("Starting scan of: {}", config.root_path.display());

    // Build combined ignore patterns
    let mut ignore_patterns = Vec::new();
    for pattern in DEFAULT_IGNORE_PATTERNS {
        ignore_patterns.push(Pattern::new(pattern).map_err(|e| format!("Invalid pattern: {}", e))?);
    }
    for pattern in &config.ignore_globs {
        ignore_patterns.push(Pattern::new(pattern).map_err(|e| format!("Invalid pattern: {}", e))?);
    }

    // Initialize system info for CPU monitoring
    let mut sys = System::new_all();

    // Track files on disk for detecting missing entries
    let mut scanned_paths = Vec::new();

    // Progress tracking
    let mut scanned_count = 0u64;
    let total_estimate = estimate_file_count(&config.root_path, &ignore_patterns)?;

    // Walk directory tree
    for entry in walkdir::WalkDir::new(&config.root_path)
        .follow_links(false) // Do NOT follow symlinks
        .into_iter()
        .filter_entry(|e| !should_ignore(e.path(), &ignore_patterns))
    {
        let entry = match entry {
            Ok(e) => e,
            Err(e) => {
                log::warn!("Error accessing entry: {}", e);
                continue;
            }
        };

        // Only process files, not directories
        if !entry.file_type().is_file() {
            continue;
        }

        let path = entry.path();
        let path_str = path.to_string_lossy().to_string();

        scanned_paths.push(path_str.clone());

        // CPU throttling check (every 50 files)
        if scanned_count % 50 == 0 {
            check_cpu_and_throttle(&mut sys).await;
        }

        // Process file
        match process_file(path, &db).await {
            Ok(_) => {
                scanned_count += 1;

                // Emit progress event every 50 files
                if scanned_count % 50 == 0 {
                    let duplicates = count_duplicates(&db).await?;
                    let progress = ScanProgress {
                        scanned: scanned_count,
                        total_estimate,
                        current_path: path_str.clone(),
                        duplicates_found: duplicates,
                    };

                    if let Err(e) = app_handle.emit("scan-progress", &progress) {
                        log::warn!("Failed to emit scan-progress event: {}", e);
                    }
                }
            }
            Err(e) => {
                log::warn!("Error processing file {}: {}", path_str, e);
            }
        }
    }

    // Mark files that no longer exist on disk as missing
    mark_missing_files(&db, scanned_paths).await?;

    // Update duplicate statuses
    update_duplicate_statuses(&db).await?;

    // Emit completion event
    if let Err(e) = app_handle.emit("scan-complete", &()) {
        log::warn!("Failed to emit scan-complete event: {}", e);
    }

    log::info!("Scan complete. Scanned {} files", scanned_count);
    Ok(())
}

/// Check if a path should be ignored based on glob patterns
fn should_ignore(path: &std::path::Path, patterns: &[Pattern]) -> bool {
    let path_str = path.to_string_lossy();
    patterns.iter().any(|p| p.matches(&path_str))
}

/// Estimate total file count for progress tracking
fn estimate_file_count(root: &PathBuf, ignore_patterns: &[Pattern]) -> Result<u64, String> {
    let count = walkdir::WalkDir::new(root)
        .follow_links(false)
        .into_iter()
        .filter_entry(|e| !should_ignore(e.path(), ignore_patterns))
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .count();

    Ok(count as u64)
}

/// Check CPU usage and throttle if necessary
async fn check_cpu_and_throttle(sys: &mut System) {
    sys.refresh_cpu();

    loop {
        let usage = sys.global_cpu_info().cpu_usage();

        if usage > 50.0 {
            log::debug!("CPU usage high ({}%), pausing for 5 seconds", usage);
            tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
            sys.refresh_cpu();
        } else {
            // If under 30%, proceed immediately
            // Between 30-50%, also proceed (only throttle above 50%)
            break;
        }
    }
}

/// Process a single file: extract metadata, hash, and upsert to DB
async fn process_file(path: &std::path::Path, db: &DbConn) -> Result<(), String> {
    // Get file metadata
    let metadata = std::fs::metadata(path)
        .map_err(|e| format!("Failed to read metadata for {}: {}", path.display(), e))?;

    let size_bytes = metadata.len() as i64;

    let modified_at = metadata
        .modified()
        .ok()
        .and_then(|t| t.duration_since(SystemTime::UNIX_EPOCH).ok())
        .map(|d| d.as_secs() as i64);

    // Guess MIME type
    let mime_type = from_path(path).first_raw().map(|s| s.to_string());

    let path_str = path.to_string_lossy().to_string();

    // Check if file exists in DB and modified_at is unchanged (cache hit)
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let cached_hash: Option<(String, i64)> = conn
        .query_row(
            "SELECT sha256, modified_at FROM f2_file_index WHERE path = ?",
            params![&path_str],
            |row| Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?)),
        )
        .ok();

    drop(conn); // Release lock before potentially expensive hashing

    // If cached and modified_at unchanged, skip hashing
    let sha256 = if let Some((hash, cached_modified)) = cached_hash {
        if Some(cached_modified) == modified_at {
            log::debug!("Cache hit for {}", path_str);
            hash
        } else {
            compute_sha256(path)?
        }
    } else {
        compute_sha256(path)?
    };

    // Upsert into database
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    conn.execute(
        r#"
        INSERT INTO f2_file_index (path, size_bytes, modified_at, mime_type, sha256, status, last_scanned)
        VALUES (?, ?, to_timestamp(?), ?, ?, 'ok', now())
        ON CONFLICT (path) DO UPDATE SET
            size_bytes = excluded.size_bytes,
            modified_at = excluded.modified_at,
            mime_type = excluded.mime_type,
            sha256 = excluded.sha256,
            status = 'ok',
            last_scanned = now()
        "#,
        params![&path_str, size_bytes, modified_at, mime_type, &sha256],
    )
    .map_err(|e| format!("Failed to upsert file: {}", e))?;

    Ok(())
}

/// Compute SHA-256 hash of a file using streaming (64KB chunks)
fn compute_sha256(path: &std::path::Path) -> Result<String, String> {
    let file = File::open(path)
        .map_err(|e| format!("Failed to open file {}: {}", path.display(), e))?;

    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 65536]; // 64KB chunks

    loop {
        let n = reader
            .read(&mut buf)
            .map_err(|e| format!("Failed to read file {}: {}", path.display(), e))?;

        if n == 0 {
            break;
        }

        hasher.update(&buf[..n]);
    }

    Ok(hex::encode(hasher.finalize()))
}

/// Count total duplicate files in the database
async fn count_duplicates(db: &DbConn) -> Result<u64, String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM f2_file_index WHERE status = 'duplicate'",
            [],
            |row| row.get(0),
        )
        .unwrap_or(0);

    Ok(count as u64)
}

/// Mark files that no longer exist on disk as missing
async fn mark_missing_files(db: &DbConn, scanned_paths: Vec<String>) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    // Get all paths from DB
    let mut stmt = conn
        .prepare("SELECT path FROM f2_file_index")
        .map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let db_paths: Vec<String> = stmt
        .query_map([], |row| row.get::<_, String>(0))
        .map_err(|e| format!("Failed to query paths: {}", e))?
        .filter_map(|r| r.ok())
        .collect();

    drop(stmt);

    // Find paths in DB but not scanned
    let scanned_set: HashSet<_> = scanned_paths.into_iter().collect();

    for db_path in db_paths {
        if !scanned_set.contains(&db_path) {
            conn.execute(
                "UPDATE f2_file_index SET status = 'missing' WHERE path = ?",
                params![&db_path],
            )
            .map_err(|e| format!("Failed to mark file as missing: {}", e))?;
        }
    }

    Ok(())
}

/// Update status for all files: mark duplicates
async fn update_duplicate_statuses(db: &DbConn) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    // First, reset all non-missing files to 'ok'
    conn.execute(
        "UPDATE f2_file_index SET status = 'ok' WHERE status != 'missing'",
        [],
    )
    .map_err(|e| format!("Failed to reset statuses: {}", e))?;

    // Then mark duplicates (files with same hash where count > 1)
    conn.execute(
        r#"
        UPDATE f2_file_index
        SET status = 'duplicate'
        WHERE sha256 IN (
            SELECT sha256
            FROM f2_file_index
            WHERE sha256 IS NOT NULL AND status != 'missing'
            GROUP BY sha256
            HAVING COUNT(*) > 1
        ) AND status != 'missing'
        "#,
        [],
    )
    .map_err(|e| format!("Failed to mark duplicates: {}", e))?;

    Ok(())
}
