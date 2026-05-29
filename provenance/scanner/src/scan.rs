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

pub struct ScanConfig {
    pub root_path: PathBuf,
    pub ignore_globs: Vec<String>,
    pub run_id: String,
    pub batch_size: u64,
    pub throttle_pct: f32,
}

pub struct ScanResult {
    pub run_id: String,
    pub files_scanned: u64,
    #[allow(dead_code)]
    pub files_new: u64,
    #[allow(dead_code)]
    pub files_updated: u64,
    pub duplicates_found: u64,
    pub duration_ms: u64,
}

enum FileOutcome {
    New,
    Updated,
    Cached,
}

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

pub async fn scan_directory(db: DbConn, config: ScanConfig) -> Result<ScanResult, String> {
    log::info!("Starting scan of: {}", config.root_path.display());

    let started = std::time::Instant::now();

    insert_scan_run(&db, &config.run_id, &config.root_path.to_string_lossy())?;

    let mut ignore_patterns = Vec::new();
    for pattern in DEFAULT_IGNORE_PATTERNS {
        ignore_patterns
            .push(Pattern::new(pattern).map_err(|e| format!("Invalid pattern: {}", e))?);
    }
    for pattern in &config.ignore_globs {
        ignore_patterns
            .push(Pattern::new(pattern).map_err(|e| format!("Invalid pattern: {}", e))?);
    }

    let mut sys = System::new_all();
    let mut scanned_paths = Vec::new();
    let mut scanned_count = 0u64;
    let mut files_new = 0u64;
    let mut files_updated = 0u64;

    for entry in walkdir::WalkDir::new(&config.root_path)
        .follow_links(false)
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

        if !entry.file_type().is_file() {
            continue;
        }

        let path = entry.path();
        let path_str = path.to_string_lossy().to_string();
        scanned_paths.push(path_str.clone());

        if scanned_count % config.batch_size == 0 {
            check_cpu_and_throttle(&mut sys, config.throttle_pct).await;
        }

        match process_file(path, &db).await {
            Ok(outcome) => {
                scanned_count += 1;
                match outcome {
                    FileOutcome::New => files_new += 1,
                    FileOutcome::Updated => files_updated += 1,
                    FileOutcome::Cached => {}
                }

                if scanned_count % config.batch_size == 0 {
                    let dups = count_duplicates(&db).await?;
                    update_scan_run_progress(
                        &db,
                        &config.run_id,
                        scanned_count,
                        files_new,
                        files_updated,
                        dups,
                    )?;
                }
            }
            Err(e) => {
                log::warn!("Error processing file {}: {}", path_str, e);
            }
        }
    }

    mark_missing_files(&db, scanned_paths).await?;
    update_duplicate_statuses(&db).await?;

    let duplicates_found = count_duplicates(&db).await?;
    let duration_ms = started.elapsed().as_millis() as u64;

    complete_scan_run(
        &db,
        &config.run_id,
        scanned_count,
        files_new,
        files_updated,
        duplicates_found,
    )?;

    log::info!("Scan complete. Scanned {} files", scanned_count);

    Ok(ScanResult {
        run_id: config.run_id,
        files_scanned: scanned_count,
        files_new,
        files_updated,
        duplicates_found,
        duration_ms,
    })
}

pub async fn resume_scan(db: DbConn, run_id: &str, batch_size: u64, throttle_pct: f32) -> Result<ScanResult, String> {
    let (root_path_str, status) = {
        let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
        conn.query_row(
            "SELECT root_path, status FROM scan_runs WHERE id = ?",
            params![run_id],
            |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
        )
        .map_err(|_| format!("Run '{}' not found in scan_runs", run_id))?
    };

    if status == "complete" {
        return Err(format!("Run '{}' already completed — nothing to resume", run_id));
    }

    {
        let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
        conn.execute(
            "UPDATE scan_runs SET status = 'running', finished_at = NULL WHERE id = ?",
            params![run_id],
        )
        .map_err(|e| format!("Failed to reset run status: {}", e))?;
    }

    let config = ScanConfig {
        root_path: PathBuf::from(root_path_str),
        ignore_globs: vec![],
        run_id: run_id.to_string(),
        batch_size,
        throttle_pct,
    };

    // scan_directory will call insert_scan_run which will conflict — skip re-insert
    // by calling the inner scan loop directly
    scan_directory_resume(db, config).await
}

// TODO: scan_directory_resume duplicates the walk loop from scan_directory.
// Extract a scan_loop(db, config) inner fn if the core loop ever changes.
async fn scan_directory_resume(db: DbConn, config: ScanConfig) -> Result<ScanResult, String> {
    log::info!("Resuming scan of: {}", config.root_path.display());

    let started = std::time::Instant::now();

    let mut ignore_patterns = Vec::new();
    for pattern in DEFAULT_IGNORE_PATTERNS {
        ignore_patterns
            .push(Pattern::new(pattern).map_err(|e| format!("Invalid pattern: {}", e))?);
    }
    for pattern in &config.ignore_globs {
        ignore_patterns
            .push(Pattern::new(pattern).map_err(|e| format!("Invalid pattern: {}", e))?);
    }

    let mut sys = System::new_all();
    let mut scanned_paths = Vec::new();
    let mut scanned_count = 0u64;
    let mut files_new = 0u64;
    let mut files_updated = 0u64;

    for entry in walkdir::WalkDir::new(&config.root_path)
        .follow_links(false)
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

        if !entry.file_type().is_file() {
            continue;
        }

        let path = entry.path();
        let path_str = path.to_string_lossy().to_string();
        scanned_paths.push(path_str.clone());

        if scanned_count % config.batch_size == 0 {
            check_cpu_and_throttle(&mut sys, config.throttle_pct).await;
        }

        match process_file(path, &db).await {
            Ok(outcome) => {
                scanned_count += 1;
                match outcome {
                    FileOutcome::New => files_new += 1,
                    FileOutcome::Updated => files_updated += 1,
                    FileOutcome::Cached => {}
                }

                if scanned_count % config.batch_size == 0 {
                    let dups = count_duplicates(&db).await?;
                    update_scan_run_progress(
                        &db,
                        &config.run_id,
                        scanned_count,
                        files_new,
                        files_updated,
                        dups,
                    )?;
                }
            }
            Err(e) => {
                log::warn!("Error processing file {}: {}", path_str, e);
            }
        }
    }

    mark_missing_files(&db, scanned_paths).await?;
    update_duplicate_statuses(&db).await?;

    let duplicates_found = count_duplicates(&db).await?;
    let duration_ms = started.elapsed().as_millis() as u64;

    complete_scan_run(
        &db,
        &config.run_id,
        scanned_count,
        files_new,
        files_updated,
        duplicates_found,
    )?;

    log::info!("Resume complete. Scanned {} files", scanned_count);

    Ok(ScanResult {
        run_id: config.run_id,
        files_scanned: scanned_count,
        files_new,
        files_updated,
        duplicates_found,
        duration_ms,
    })
}

fn should_ignore(path: &std::path::Path, patterns: &[Pattern]) -> bool {
    let path_str = path.to_string_lossy();
    patterns.iter().any(|p| p.matches(&path_str))
}

async fn check_cpu_and_throttle(sys: &mut System, throttle_pct: f32) {
    sys.refresh_cpu_usage();

    loop {
        let usage = sys.global_cpu_info().cpu_usage();
        if usage > throttle_pct {
            log::debug!("CPU usage high ({}%), pausing for 5 seconds", usage);
            tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
            sys.refresh_cpu_usage();
        } else {
            break;
        }
    }
}

async fn process_file(path: &std::path::Path, db: &DbConn) -> Result<FileOutcome, String> {
    let metadata = std::fs::metadata(path)
        .map_err(|e| format!("Failed to read metadata for {}: {}", path.display(), e))?;

    let size_bytes = metadata.len() as i64;
    let modified_at = metadata
        .modified()
        .ok()
        .and_then(|t| t.duration_since(SystemTime::UNIX_EPOCH).ok())
        .map(|d| d.as_secs() as i64);

    let mime_type = from_path(path).first_raw().map(|s| s.to_string());
    let path_str = path.to_string_lossy().to_string();

    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
    let cached: Option<(String, i64)> = conn
        .query_row(
            "SELECT sha256, epoch_ms(modified_at) / 1000 FROM f2_file_index WHERE path = ?",
            params![&path_str],
            |row| Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?)),
        )
        .ok();
    drop(conn);

    let (sha256, outcome) = match cached {
        Some((hash, cached_modified)) if Some(cached_modified) == modified_at => {
            log::debug!("Cache hit for {}", path_str);
            (hash, FileOutcome::Cached)
        }
        Some(_) => (compute_sha256(path)?, FileOutcome::Updated),
        None => (compute_sha256(path)?, FileOutcome::New),
    };

    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
    conn.execute(
        r#"
        INSERT INTO f2_file_index (path, size_bytes, modified_at, mime_type, sha256, status, last_scanned)
        VALUES (?, ?, to_timestamp(?), ?, ?, 'ok', now())
        ON CONFLICT (path) DO UPDATE SET
            size_bytes   = excluded.size_bytes,
            modified_at  = excluded.modified_at,
            mime_type    = excluded.mime_type,
            sha256       = excluded.sha256,
            status       = 'ok',
            last_scanned = now()
        "#,
        params![&path_str, size_bytes, modified_at, mime_type, &sha256],
    )
    .map_err(|e| format!("Failed to upsert file: {}", e))?;

    Ok(outcome)
}

fn compute_sha256(path: &std::path::Path) -> Result<String, String> {
    let file = File::open(path)
        .map_err(|e| format!("Failed to open file {}: {}", path.display(), e))?;
    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 65536];

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

async fn mark_missing_files(db: &DbConn, scanned_paths: Vec<String>) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let mut stmt = conn
        .prepare("SELECT path FROM f2_file_index")
        .map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let db_paths: Vec<String> = stmt
        .query_map([], |row| row.get::<_, String>(0))
        .map_err(|e| format!("Failed to query paths: {}", e))?
        .filter_map(|r| r.ok())
        .collect();

    drop(stmt);

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

async fn update_duplicate_statuses(db: &DbConn) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    conn.execute(
        "UPDATE f2_file_index SET status = 'ok' WHERE status != 'missing'",
        [],
    )
    .map_err(|e| format!("Failed to reset statuses: {}", e))?;

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

fn insert_scan_run(db: &DbConn, run_id: &str, root_path: &str) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
    conn.execute(
        "INSERT INTO scan_runs (id, root_path, started_at, status) VALUES (?, ?, now(), 'running')",
        params![run_id, root_path],
    )
    .map_err(|e| format!("Failed to insert scan_run: {}", e))?;
    Ok(())
}

fn update_scan_run_progress(
    db: &DbConn,
    run_id: &str,
    files_scanned: u64,
    files_new: u64,
    files_updated: u64,
    duplicates_found: u64,
) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
    conn.execute(
        r#"UPDATE scan_runs SET
            files_scanned    = ?,
            files_new        = ?,
            files_updated    = ?,
            duplicates_found = ?
           WHERE id = ?"#,
        params![
            files_scanned as i64,
            files_new as i64,
            files_updated as i64,
            duplicates_found as i64,
            run_id
        ],
    )
    .map_err(|e| format!("Failed to update scan_run progress: {}", e))?;
    Ok(())
}

fn complete_scan_run(
    db: &DbConn,
    run_id: &str,
    files_scanned: u64,
    files_new: u64,
    files_updated: u64,
    duplicates_found: u64,
) -> Result<(), String> {
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;
    conn.execute(
        r#"UPDATE scan_runs SET
            status           = 'complete',
            finished_at      = now(),
            files_scanned    = ?,
            files_new        = ?,
            files_updated    = ?,
            duplicates_found = ?
           WHERE id = ?"#,
        params![
            files_scanned as i64,
            files_new as i64,
            files_updated as i64,
            duplicates_found as i64,
            run_id
        ],
    )
    .map_err(|e| format!("Failed to complete scan_run: {}", e))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db;
    use std::io::Write;
    use tempfile::TempDir;

    fn make_db() -> (TempDir, DbConn) {
        let tmp = TempDir::new().unwrap();
        let db_path = tmp.path().join("test.duckdb");
        let conn = db::open(&db_path).unwrap();
        (tmp, conn)
    }

    #[tokio::test]
    async fn test_scan_empty_directory() {
        let (_tmp, db) = make_db();
        let dir = TempDir::new().unwrap();
        let config = ScanConfig {
            root_path: dir.path().to_path_buf(),
            ignore_globs: vec![],
            run_id: "test-run-1".to_string(),
            batch_size: 50,
            throttle_pct: 50.0,
        };
        let result = scan_directory(db, config).await.unwrap();
        assert_eq!(result.files_scanned, 0);
        assert_eq!(result.files_new, 0);
    }

    #[tokio::test]
    async fn test_scan_counts_files() {
        let (_tmp, db) = make_db();
        let dir = TempDir::new().unwrap();

        for name in &["a.txt", "b.txt", "c.pdf"] {
            let mut f = File::create(dir.path().join(name)).unwrap();
            f.write_all(b"hello world").unwrap();
        }

        let config = ScanConfig {
            root_path: dir.path().to_path_buf(),
            ignore_globs: vec![],
            run_id: "test-run-2".to_string(),
            batch_size: 50,
            throttle_pct: 50.0,
        };
        let result = scan_directory(db, config).await.unwrap();
        assert_eq!(result.files_scanned, 3);
        assert_eq!(result.files_new, 3);
    }

    #[tokio::test]
    async fn test_scan_run_row_populated() {
        let (_tmp, db) = make_db();
        let dir = TempDir::new().unwrap();
        let mut f = File::create(dir.path().join("test.txt")).unwrap();
        f.write_all(b"data").unwrap();

        let run_id = "test-run-3".to_string();
        let config = ScanConfig {
            root_path: dir.path().to_path_buf(),
            ignore_globs: vec![],
            run_id: run_id.clone(),
            batch_size: 50,
            throttle_pct: 50.0,
        };
        scan_directory(db.clone(), config).await.unwrap();

        let conn = db.lock().unwrap();
        let status: String = conn
            .query_row(
                "SELECT status FROM scan_runs WHERE id = ?",
                params![&run_id],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(status, "complete");
    }

    #[tokio::test]
    async fn test_cache_hit_on_rescan() {
        let (_tmp, db) = make_db();
        let dir = TempDir::new().unwrap();
        let mut f = File::create(dir.path().join("same.txt")).unwrap();
        f.write_all(b"unchanged").unwrap();

        let make_config = |run_id: &str| ScanConfig {
            root_path: dir.path().to_path_buf(),
            ignore_globs: vec![],
            run_id: run_id.to_string(),
            batch_size: 50,
            throttle_pct: 50.0,
        };

        let r1 = scan_directory(db.clone(), make_config("run-a")).await.unwrap();
        let r2 = scan_directory(db.clone(), make_config("run-b")).await.unwrap();

        assert_eq!(r1.files_new, 1);
        // Second scan: file unchanged → cached, not new
        assert_eq!(r2.files_new, 0);
        assert_eq!(r2.files_updated, 0);
    }
}
