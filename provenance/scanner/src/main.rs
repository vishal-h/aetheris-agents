mod db;
mod migrations;
mod scan;

use clap::{Parser, Subcommand};
use scan::{ScanConfig, ScanResult};
use serde::Serialize;
use std::path::PathBuf;

#[derive(Parser)]
#[command(
    name = "f2-scanner",
    about = "File corpus scanner for Provenance",
    version
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Scan a directory and populate the file index
    Scan {
        /// Root path to scan
        #[arg(long)]
        root: PathBuf,

        /// DuckDB file path
        #[arg(long)]
        db: PathBuf,

        /// Additional ignore patterns (repeatable)
        #[arg(long, action = clap::ArgAction::Append)]
        ignore: Vec<String>,

        /// Scan run ID (generated if not provided)
        #[arg(long)]
        run_id: Option<String>,

        /// CPU throttle threshold percentage (default: 50)
        #[arg(long, default_value = "50")]
        throttle: f32,

        /// Progress update interval in files (default: 50)
        #[arg(long, default_value = "50")]
        batch_size: u64,
    },

    /// Resume an interrupted or failed scan
    Resume {
        /// Run ID to resume
        #[arg(long)]
        run_id: String,

        /// DuckDB file path
        #[arg(long)]
        db: PathBuf,

        /// CPU throttle threshold percentage (default: 50)
        #[arg(long, default_value = "50")]
        throttle: f32,

        /// Progress update interval in files (default: 50)
        #[arg(long, default_value = "50")]
        batch_size: u64,
    },

    /// Show recent scan run status
    Status {
        /// DuckDB file path
        #[arg(long)]
        db: PathBuf,
    },
}

#[derive(Serialize)]
struct CompletionOutput {
    run_id: String,
    status: &'static str,
    files_scanned: u64,
    duplicates_found: u64,
    duration_ms: u64,
}

fn main() {
    env_logger::init();
    let cli = Cli::parse();

    let result = match cli.command {
        Commands::Scan { root, db, ignore, run_id, throttle, batch_size } => {
            let run_id = run_id.unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
            run_scan(root, db, ignore, run_id, throttle, batch_size)
        }
        Commands::Resume { run_id, db, throttle, batch_size } => {
            run_resume(run_id, db, throttle, batch_size)
        }
        Commands::Status { db } => run_status(db),
    };

    if let Err(e) = result {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}

fn run_scan(
    root: PathBuf,
    db_path: PathBuf,
    ignore: Vec<String>,
    run_id: String,
    throttle: f32,
    batch_size: u64,
) -> Result<(), String> {
    let db = db::open(&db_path)?;

    let config = ScanConfig {
        root_path: root,
        ignore_globs: ignore,
        run_id,
        batch_size,
        throttle_pct: throttle,
    };

    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| format!("Failed to start async runtime: {}", e))?;

    let result: ScanResult = rt.block_on(scan::scan_directory(db, config))?;

    print_completion(&result);
    Ok(())
}

fn run_resume(
    run_id: String,
    db_path: PathBuf,
    throttle: f32,
    batch_size: u64,
) -> Result<(), String> {
    let db = db::open(&db_path)?;

    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| format!("Failed to start async runtime: {}", e))?;

    let result: ScanResult =
        rt.block_on(scan::resume_scan(db, &run_id, batch_size, throttle))?;

    print_completion(&result);
    Ok(())
}

fn run_status(db_path: PathBuf) -> Result<(), String> {
    let db = db::open(&db_path)?;
    let conn = db.lock().map_err(|e| format!("DB lock error: {}", e))?;

    let mut stmt = conn
        .prepare(
            r#"SELECT id, root_path, status, files_scanned, duplicates_found,
                      started_at::VARCHAR, finished_at::VARCHAR
               FROM scan_runs
               ORDER BY started_at DESC
               LIMIT 20"#,
        )
        .map_err(|e| format!("Failed to prepare query: {}", e))?;

    #[derive(Debug)]
    struct Row {
        id: String,
        root_path: String,
        status: String,
        files_scanned: i64,
        duplicates_found: i64,
        started_at: String,
        finished_at: Option<String>,
    }

    let rows: Vec<Row> = stmt
        .query_map([], |row| {
            Ok(Row {
                id: row.get(0)?,
                root_path: row.get(1)?,
                status: row.get(2)?,
                files_scanned: row.get(3)?,
                duplicates_found: row.get(4)?,
                started_at: row.get(5)?,
                finished_at: row.get(6)?,
            })
        })
        .map_err(|e| format!("Failed to query scan_runs: {}", e))?
        .filter_map(|r| r.ok())
        .collect();

    if rows.is_empty() {
        println!("No scan runs found.");
        return Ok(());
    }

    println!("{:<38} {:<10} {:>14} {:>16}  {}", "run_id", "status", "files_scanned", "duplicates_found", "started_at");
    println!("{}", "-".repeat(100));

    for row in &rows {
        println!(
            "{:<38} {:<10} {:>14} {:>16}  {}",
            truncate(&row.id, 36),
            row.status,
            row.files_scanned,
            row.duplicates_found,
            row.started_at,
        );
        println!("  root: {}", row.root_path);
        if let Some(finished) = &row.finished_at {
            println!("  finished: {}", finished);
        }
    }

    Ok(())
}

fn print_completion(result: &ScanResult) {
    let output = CompletionOutput {
        run_id: result.run_id.clone(),
        status: "complete",
        files_scanned: result.files_scanned,
        duplicates_found: result.duplicates_found,
        duration_ms: result.duration_ms,
    };
    println!("{}", serde_json::to_string(&output).unwrap());
}

fn truncate(s: &str, max: usize) -> &str {
    if s.len() <= max { s } else { &s[..max] }
}
