mod migrations;

use duckdb::Connection;
use std::path::Path;
use std::sync::{Arc, Mutex};

/// Type alias for the database connection wrapped for thread-safety
/// DuckDB Connection is not Send + Sync by default, so we wrap it in Arc<Mutex<>>
pub type DbConn = Arc<Mutex<Connection>>;

/// Initialize the database: create/open the DB file, run migrations, return connection
///
/// # Arguments
/// * `app_data_dir` - The OS-appropriate app data directory (resolved via Tauri)
///
/// # Returns
/// * `Result<DbConn, String>` - The database connection or an error message
pub fn init(app_data_dir: &Path) -> Result<DbConn, String> {
    // Ensure the app data directory exists
    std::fs::create_dir_all(app_data_dir)
        .map_err(|e| format!("Failed to create app data directory: {}", e))?;

    // Database file path
    let db_path = app_data_dir.join("data.db");

    log::info!("Initializing database at: {}", db_path.display());

    // Open or create the database
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    // Run migrations
    migrations::run_migrations(&conn)?;

    log::info!("Database initialized successfully");

    // Wrap in Arc<Mutex<>> for thread-safety
    Ok(Arc::new(Mutex::new(conn)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_init_creates_db_file() {
        let temp_dir = TempDir::new().unwrap();
        let app_data_dir = temp_dir.path();

        let db_conn = init(app_data_dir).unwrap();

        // Verify DB file exists
        let db_path = app_data_dir.join("data.db");
        assert!(db_path.exists());

        // Verify we can query the DB
        let conn = db_conn.lock().unwrap();
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM schema_migrations", [], |row| {
                row.get(0)
            })
            .unwrap();

        assert!(count > 0, "Migrations should have been applied");
    }

    #[test]
    fn test_init_is_idempotent() {
        let temp_dir = TempDir::new().unwrap();
        let app_data_dir = temp_dir.path();

        // Initialize twice
        let db_conn1 = init(app_data_dir).unwrap();
        drop(db_conn1); // Release the connection

        let db_conn2 = init(app_data_dir).unwrap();

        // Verify migrations weren't duplicated
        let conn = db_conn2.lock().unwrap();
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM schema_migrations", [], |row| {
                row.get(0)
            })
            .unwrap();

        assert_eq!(count, 2, "Should have exactly 2 migrations");
    }
}
