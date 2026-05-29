use duckdb::Connection;

struct Migration {
    version: i32,
    sql: &'static str,
}

const MIGRATIONS: &[Migration] = &[
    Migration {
        version: 1,
        sql: r#"
CREATE SEQUENCE IF NOT EXISTS seq_f2_file_index;

CREATE TABLE IF NOT EXISTS f2_file_index (
    id            INTEGER PRIMARY KEY DEFAULT nextval('seq_f2_file_index'),
    path          VARCHAR NOT NULL UNIQUE,
    size_bytes    BIGINT,
    modified_at   TIMESTAMP,
    mime_type     VARCHAR,
    sha256        VARCHAR(64),
    status        VARCHAR DEFAULT 'ok',
    last_scanned  TIMESTAMP DEFAULT now()
);
"#,
    },
    Migration {
        version: 2,
        sql: r#"
CREATE TABLE IF NOT EXISTS scan_runs (
    id               TEXT PRIMARY KEY,
    root_path        TEXT NOT NULL,
    started_at       TIMESTAMP NOT NULL,
    finished_at      TIMESTAMP,
    status           TEXT DEFAULT 'running',
    files_scanned    BIGINT DEFAULT 0,
    files_new        BIGINT DEFAULT 0,
    files_updated    BIGINT DEFAULT 0,
    duplicates_found BIGINT DEFAULT 0,
    aetheris_run_id  TEXT
);
"#,
    },
];

pub fn run_migrations(conn: &Connection) -> Result<(), String> {
    conn.execute(
        r#"
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT now()
        )
        "#,
        [],
    )
    .map_err(|e| format!("Failed to create schema_migrations table: {}", e))?;

    let current_version: i32 = conn
        .query_row(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations",
            [],
            |row| row.get(0),
        )
        .unwrap_or(0);

    for migration in MIGRATIONS {
        if migration.version > current_version {
            conn.execute_batch(migration.sql)
                .map_err(|e| format!("Failed to apply migration {}: {}", migration.version, e))?;

            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                [migration.version],
            )
            .map_err(|e| format!("Failed to record migration {}: {}", migration.version, e))?;

            log::info!("Applied migration {}", migration.version);
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use duckdb::Connection;

    #[test]
    fn test_migrations_are_idempotent() {
        let conn = Connection::open_in_memory().unwrap();
        run_migrations(&conn).unwrap();
        run_migrations(&conn).unwrap();
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM schema_migrations", [], |row| row.get(0))
            .unwrap();
        assert_eq!(count, MIGRATIONS.len() as i32);
    }

    #[test]
    fn test_all_tables_created() {
        let conn = Connection::open_in_memory().unwrap();
        run_migrations(&conn).unwrap();
        for table in &["f2_file_index", "scan_runs"] {
            let exists: bool = conn
                .query_row(
                    "SELECT COUNT(*) > 0 FROM information_schema.tables WHERE table_name = ?",
                    [table],
                    |row| row.get(0),
                )
                .unwrap();
            assert!(exists, "table {} should exist", table);
        }
    }
}
