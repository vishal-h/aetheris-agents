use duckdb::Connection;
use std::path::Path;
use std::sync::{Arc, Mutex};

pub type DbConn = Arc<Mutex<Connection>>;

pub fn open(db_path: &Path) -> Result<DbConn, String> {
    if let Some(parent) = db_path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create parent directory: {}", e))?;
        }
    }

    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open database at {}: {}", db_path.display(), e))?;

    crate::migrations::run_migrations(&conn)?;

    Ok(Arc::new(Mutex::new(conn)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_open_creates_db_file() {
        let tmp = TempDir::new().unwrap();
        let db_path = tmp.path().join("test.duckdb");
        let db = open(&db_path).unwrap();
        assert!(db_path.exists());
        let conn = db.lock().unwrap();
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM schema_migrations", [], |row| row.get(0))
            .unwrap();
        assert!(count > 0);
    }

    #[test]
    fn test_open_is_idempotent() {
        let tmp = TempDir::new().unwrap();
        let db_path = tmp.path().join("test.duckdb");
        drop(open(&db_path).unwrap());
        let db = open(&db_path).unwrap();
        let conn = db.lock().unwrap();
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM schema_migrations", [], |row| row.get(0))
            .unwrap();
        assert!(count > 0);
    }

    #[test]
    fn test_scan_runs_table_exists() {
        let tmp = TempDir::new().unwrap();
        let db_path = tmp.path().join("test.duckdb");
        let db = open(&db_path).unwrap();
        let conn = db.lock().unwrap();
        let exists: bool = conn
            .query_row(
                "SELECT COUNT(*) > 0 FROM information_schema.tables WHERE table_name = 'scan_runs'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        assert!(exists);
    }
}
