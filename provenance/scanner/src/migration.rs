use duckdb::Connection;

/// Represents a single database migration
struct Migration {
    version: i32,
    sql: &'static str,
}

/// All migrations in order
const MIGRATIONS: &[Migration] = &[
    Migration {
        version: 1,
        sql: r#"
-- Migration 001: Create all F2 tables

-- Sequences for auto-incrementing IDs
CREATE SEQUENCE IF NOT EXISTS seq_f2_file_index;
CREATE SEQUENCE IF NOT EXISTS seq_f2_file_labels;
CREATE SEQUENCE IF NOT EXISTS seq_f2_watched_folders;
CREATE SEQUENCE IF NOT EXISTS seq_f2_views;

-- Indexed file metadata (populated by scanner)
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

-- User-applied labels
CREATE TABLE IF NOT EXISTS f2_file_labels (
    id        INTEGER PRIMARY KEY DEFAULT nextval('seq_f2_file_labels'),
    file_id   INTEGER NOT NULL,
    label     VARCHAR NOT NULL,
    added_at  TIMESTAMP DEFAULT now(),
    UNIQUE(file_id, label)
);

-- Watched folder configuration
CREATE TABLE IF NOT EXISTS f2_watched_folders (
    id            INTEGER PRIMARY KEY DEFAULT nextval('seq_f2_watched_folders'),
    path          VARCHAR NOT NULL UNIQUE,
    enabled       BOOLEAN DEFAULT true,
    ignore_globs  VARCHAR,
    added_at      TIMESTAMP DEFAULT now(),
    last_scan     TIMESTAMP
);

-- Saved virtual views (v1: predefined, v2: user-defined)
CREATE TABLE IF NOT EXISTS f2_views (
    id            INTEGER PRIMARY KEY DEFAULT nextval('seq_f2_views'),
    name          VARCHAR NOT NULL,
    primary_dim   VARCHAR NOT NULL,
    secondary_dim VARCHAR,
    is_builtin    BOOLEAN DEFAULT true,
    created_at    TIMESTAMP DEFAULT now()
);

-- App-wide settings
CREATE TABLE IF NOT EXISTS settings (
    key        VARCHAR PRIMARY KEY,
    value      VARCHAR NOT NULL,
    updated_at TIMESTAMP DEFAULT now()
);
"#,
    },
    Migration {
        version: 2,
        sql: r#"
-- Migration 002: Seed predefined F2V views

INSERT INTO f2_views (id, name, primary_dim, secondary_dim, is_builtin)
VALUES
    (1, 'By Type', 'mime', NULL, true),
    (2, 'By Date', 'date', 'month', true),
    (3, 'By Size', 'size', NULL, true),
    (4, 'By Label', 'label', NULL, true),
    (5, 'By Type + Label', 'mime', 'label', true),
    (6, 'By Date + Type', 'date', 'mime', true)
ON CONFLICT DO NOTHING;
"#,
    },
];

/// Run all pending migrations on the given connection
pub fn run_migrations(conn: &Connection) -> Result<(), String> {
    // Create schema_migrations table if it doesn't exist
    conn.execute(
        r#"
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT now()
        )
        "#,
        [],
    )
    .map_err(|e| format!("Failed to create schema_migrations table: {}", e))?;

    // Get current max version
    let current_version: i32 = conn
        .query_row(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations",
            [],
            |row| row.get(0),
        )
        .unwrap_or(0);

    // Apply pending migrations
    for migration in MIGRATIONS {
        if migration.version > current_version {
            // Execute migration SQL
            conn.execute_batch(migration.sql)
                .map_err(|e| format!("Failed to apply migration {}: {}", migration.version, e))?;

            // Record migration
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

        // Run migrations twice
        run_migrations(&conn).unwrap();
        run_migrations(&conn).unwrap();

        // Check that schema_migrations has correct entries
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM schema_migrations", [], |row| {
                row.get(0)
            })
            .unwrap();

        assert_eq!(count, MIGRATIONS.len() as i32);
    }

    #[test]
    fn test_all_f2_tables_created() {
        let conn = Connection::open_in_memory().unwrap();
        run_migrations(&conn).unwrap();

        // Verify all F2 tables exist
        let tables = vec![
            "f2_file_index",
            "f2_file_labels",
            "f2_watched_folders",
            "f2_views",
            "settings",
        ];

        for table in tables {
            let exists: bool = conn
                .query_row(
                    "SELECT COUNT(*) > 0 FROM information_schema.tables WHERE table_name = ?",
                    [table],
                    |row| row.get(0),
                )
                .unwrap();
            assert!(exists, "Table {} should exist", table);
        }
    }

    #[test]
    fn test_f2_views_seeded() {
        let conn = Connection::open_in_memory().unwrap();
        run_migrations(&conn).unwrap();

        // Check that 6 predefined views exist
        let count: i32 = conn
            .query_row("SELECT COUNT(*) FROM f2_views WHERE is_builtin = true", [], |row| {
                row.get(0)
            })
            .unwrap();

        assert_eq!(count, 6, "Should have 6 predefined views");
    }
}
