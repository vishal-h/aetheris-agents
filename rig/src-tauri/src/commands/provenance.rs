use crate::CorpusState;
use duckdb::params;
use tauri::State;

// ============================================================================
// System utilities
// ============================================================================

#[tauri::command]
pub fn get_system_username() -> String {
    std::env::var("USER")
        .or_else(|_| std::env::var("USERNAME"))
        .unwrap_or_else(|_| "unknown".to_string())
}

fn get_corpus_conn<'a>(
    state: &'a State<'a, CorpusState>,
) -> Result<std::sync::MutexGuard<'a, duckdb::Connection>, String> {
    state
        .conn
        .as_ref()
        .ok_or_else(|| "corpus not connected".to_string())?
        .lock()
        .map_err(|e| format!("DB lock error: {}", e))
}

// ============================================================================
// Corpus summary
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct CorpusSummary {
    pub total_files: i64,
    pub unique_files: i64,
    pub duplicate_files: i64,
    pub total_size_bytes: i64,
    pub unique_size_bytes: i64,
    pub wasted_bytes: i64,
    pub classified_files: i64,
    pub migrated_files: i64,
    pub zip_files: i64,
    pub last_scan_at: Option<String>,
}

#[tauri::command]
pub fn provenance_corpus_summary(
    state: State<'_, CorpusState>,
) -> Result<CorpusSummary, String> {
    let conn = get_corpus_conn(&state)?;

    conn.query_row(
        r#"
        SELECT
            COUNT(*) AS total_files,
            COUNT(DISTINCT sha256) AS unique_files,
            COUNT(*) - COUNT(DISTINCT sha256) AS duplicate_files,
            COALESCE(SUM(size_bytes), 0) AS total_size_bytes,
            COALESCE((
                SELECT SUM(min_size) FROM (
                    SELECT MIN(size_bytes) AS min_size
                    FROM f2_file_index
                    WHERE sha256 IS NOT NULL
                    GROUP BY sha256
                )
            ), 0) AS unique_size_bytes,
            COALESCE(SUM(size_bytes), 0) - COALESCE((
                SELECT SUM(min_size) FROM (
                    SELECT MIN(size_bytes) AS min_size
                    FROM f2_file_index
                    WHERE sha256 IS NOT NULL
                    GROUP BY sha256
                )
            ), 0) AS wasted_bytes,
            (SELECT COUNT(*) FROM classifications) AS classified_files,
            (SELECT COUNT(*) FROM migrations WHERE status = 'migrated') AS migrated_files,
            (SELECT COUNT(*) FROM zip_inventory) AS zip_files,
            (SELECT CAST(MAX(finished_at) AS VARCHAR)
             FROM scan_runs WHERE status = 'complete') AS last_scan_at
        FROM f2_file_index
        "#,
        [],
        |row| {
            Ok(CorpusSummary {
                total_files: row.get(0)?,
                unique_files: row.get(1)?,
                duplicate_files: row.get(2)?,
                total_size_bytes: row.get(3)?,
                unique_size_bytes: row.get(4)?,
                wasted_bytes: row.get(5)?,
                classified_files: row.get(6)?,
                migrated_files: row.get(7)?,
                zip_files: row.get(8)?,
                last_scan_at: row.get(9)?,
            })
        },
    )
    .map_err(|e| format!("Failed to query corpus summary: {}", e))
}

// ============================================================================
// Client breakdown
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct ClientRow {
    pub client: String,
    pub file_count: i64,
    pub total_size_bytes: i64,
    pub migrated_count: i64,
    pub doc_types: Vec<String>,
}

#[tauri::command]
pub fn provenance_client_breakdown(
    state: State<'_, CorpusState>,
) -> Result<Vec<ClientRow>, String> {
    let conn = get_corpus_conn(&state)?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT
                c.client,
                COUNT(DISTINCT c.path) AS file_count,
                COALESCE(SUM(f.size_bytes), 0) AS total_size_bytes,
                COUNT(DISTINCT m.id) FILTER (WHERE m.status = 'migrated') AS migrated_count,
                STRING_AGG(DISTINCT c.doc_type, ',') AS doc_types
            FROM classifications c
            JOIN f2_file_index f ON c.path = f.path
            LEFT JOIN migrations m ON m.classification_id = c.id
            GROUP BY c.client
            ORDER BY c.client
            "#,
        )
        .map_err(|e| format!("Failed to prepare client breakdown: {}", e))?;

    let rows = stmt
        .query_map([], |row| {
            let doc_types_str: Option<String> = row.get(4)?;
            let doc_types = doc_types_str
                .map(|s| s.split(',').map(|t| t.to_string()).collect())
                .unwrap_or_default();

            Ok(ClientRow {
                client: row.get(0)?,
                file_count: row.get(1)?,
                total_size_bytes: row.get(2)?,
                migrated_count: row.get(3)?,
                doc_types,
            })
        })
        .map_err(|e| format!("Failed to query client breakdown: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect client rows: {}", e))?;

    Ok(rows)
}

// ============================================================================
// Scan runs
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct ScanRun {
    pub id: String,
    pub root_path: String,
    pub status: String,
    pub files_scanned: i64,
    pub duplicates_found: i64,
    pub started_at: String,
    pub finished_at: Option<String>,
    pub duration_secs: Option<i64>,
}

#[tauri::command]
pub fn provenance_scan_runs(state: State<'_, CorpusState>) -> Result<Vec<ScanRun>, String> {
    let conn = get_corpus_conn(&state)?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT
                id,
                root_path,
                status,
                files_scanned,
                duplicates_found,
                CAST(started_at AS VARCHAR) AS started_at,
                CAST(finished_at AS VARCHAR) AS finished_at,
                CASE
                    WHEN finished_at IS NOT NULL
                    THEN CAST(epoch(finished_at) - epoch(started_at) AS BIGINT)
                    ELSE NULL
                END AS duration_secs
            FROM scan_runs
            ORDER BY started_at DESC
            "#,
        )
        .map_err(|e| format!("Failed to prepare scan runs query: {}", e))?;

    let rows = stmt
        .query_map([], |row| {
            Ok(ScanRun {
                id: row.get(0)?,
                root_path: row.get(1)?,
                status: row.get(2)?,
                files_scanned: row.get(3)?,
                duplicates_found: row.get(4)?,
                started_at: row.get(5)?,
                finished_at: row.get(6)?,
                duration_secs: row.get(7)?,
            })
        })
        .map_err(|e| format!("Failed to query scan runs: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect scan runs: {}", e))?;

    Ok(rows)
}

// ============================================================================
// Classification list
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct ClassificationRow {
    pub path: String,
    pub client: String,
    pub financial_year: String,
    pub doc_type: String,
    pub confidence: f64,
    pub status: String,
    pub raw_excerpt: String,
    pub classified_at: String,
    pub reviewed_by: Option<String>,
}

#[tauri::command]
pub fn provenance_classification_list(
    client: Option<String>,
    status: Option<String>,
    limit: Option<i64>,
    state: State<'_, CorpusState>,
) -> Result<Vec<ClassificationRow>, String> {
    let conn = get_corpus_conn(&state)?;
    let limit_val = limit.unwrap_or(100);

    let mut where_parts: Vec<&str> = Vec::new();
    let mut param_strs: Vec<String> = Vec::new();

    if let Some(ref c) = client {
        where_parts.push("client = ?");
        param_strs.push(c.clone());
    }
    if let Some(ref s) = status {
        where_parts.push("status = ?");
        param_strs.push(s.clone());
    }

    let where_clause = if where_parts.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", where_parts.join(" AND "))
    };

    let sql = format!(
        r#"
        SELECT
            path,
            client,
            financial_year,
            doc_type,
            confidence,
            status,
            COALESCE(raw_excerpt, '') AS raw_excerpt,
            CAST(classified_at AS VARCHAR) AS classified_at,
            reviewed_by
        FROM classifications
        {}
        ORDER BY classified_at DESC
        LIMIT {}
        "#,
        where_clause, limit_val
    );

    let mut stmt = conn
        .prepare(&sql)
        .map_err(|e| format!("Failed to prepare classification query: {}", e))?;

    let param_refs: Vec<&str> = param_strs.iter().map(|s| s.as_str()).collect();

    let rows = stmt
        .query_map(duckdb::params_from_iter(param_refs.iter().copied()), |row| {
            Ok(ClassificationRow {
                path: row.get(0)?,
                client: row.get(1)?,
                financial_year: row.get(2)?,
                doc_type: row.get(3)?,
                confidence: row.get(4)?,
                status: row.get(5)?,
                raw_excerpt: row.get(6)?,
                classified_at: row.get(7)?,
                reviewed_by: row.get(8)?,
            })
        })
        .map_err(|e| format!("Failed to query classifications: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect classifications: {}", e))?;

    Ok(rows)
}

// ============================================================================
// Set classification status (single write command)
// ============================================================================

#[tauri::command]
pub fn provenance_set_classification_status(
    path: String,
    status: String,
    reviewer: String,
    state: State<'_, CorpusState>,
) -> Result<(), String> {
    let corpus_path = state
        .path
        .as_ref()
        .ok_or_else(|| "corpus not connected".to_string())?
        .clone();

    let write_conn = duckdb::Connection::open(&corpus_path)
        .map_err(|e| format!("Failed to open corpus for write: {}", e))?;

    write_conn
        .execute(
            "UPDATE classifications SET status = ?, reviewed_by = ?, reviewed_at = now() WHERE path = ?",
            params![&status, &reviewer, &path],
        )
        .map_err(|e| format!("Failed to update classification status: {}", e))?;

    Ok(())
}

// ============================================================================
// Migration summary
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct MigrationClientRow {
    pub client: String,
    pub migrated: i64,
    pub failed: i64,
    pub pending: i64,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct MigrationSummary {
    pub total: i64,
    pub migrated: i64,
    pub failed: i64,
    pub pending: i64,
    pub by_client: Vec<MigrationClientRow>,
}

#[tauri::command]
pub fn provenance_migration_summary(
    state: State<'_, CorpusState>,
) -> Result<MigrationSummary, String> {
    let conn = get_corpus_conn(&state)?;

    let totals = conn
        .query_row(
            r#"
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'migrated') AS migrated,
                COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                COUNT(*) FILTER (WHERE status = 'approved') AS pending
            FROM migrations
            "#,
            [],
            |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, i64>(2)?,
                    row.get::<_, i64>(3)?,
                ))
            },
        )
        .map_err(|e| format!("Failed to query migration totals: {}", e))?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT
                c.client,
                COUNT(*) FILTER (WHERE m.status = 'migrated') AS migrated,
                COUNT(*) FILTER (WHERE m.status = 'failed') AS failed,
                COUNT(*) FILTER (WHERE m.status = 'approved') AS pending
            FROM migrations m
            JOIN classifications c ON m.classification_id = c.id
            GROUP BY c.client
            ORDER BY c.client
            "#,
        )
        .map_err(|e| format!("Failed to prepare by-client migration query: {}", e))?;

    let by_client = stmt
        .query_map([], |row| {
            Ok(MigrationClientRow {
                client: row.get(0)?,
                migrated: row.get(1)?,
                failed: row.get(2)?,
                pending: row.get(3)?,
            })
        })
        .map_err(|e| format!("Failed to query migrations by client: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect migration rows: {}", e))?;

    Ok(MigrationSummary {
        total: totals.0,
        migrated: totals.1,
        failed: totals.2,
        pending: totals.3,
        by_client,
    })
}

// ============================================================================
// Zip inventory
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct ZipRow {
    pub path: String,
    pub size_bytes: i64,
    pub status: String,
    pub contents_count: Option<i64>,
    pub new_to_corpus: Option<i64>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct ZipInventory {
    pub total: i64,
    pub processed: i64,
    pub encrypted: i64,
    pub pending: i64,
    pub failed: i64,
    pub new_to_corpus: i64,
    pub largest_zips: Vec<ZipRow>,
}

#[tauri::command]
pub fn provenance_zip_inventory(
    state: State<'_, CorpusState>,
) -> Result<ZipInventory, String> {
    let conn = get_corpus_conn(&state)?;

    let summary = conn
        .query_row(
            r#"
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'processed') AS processed,
                COUNT(*) FILTER (WHERE status = 'encrypted') AS encrypted,
                COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                COALESCE(SUM(new_to_corpus), 0) AS new_to_corpus
            FROM zip_inventory
            "#,
            [],
            |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, i64>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, i64>(4)?,
                    row.get::<_, i64>(5)?,
                ))
            },
        )
        .map_err(|e| format!("Failed to query zip inventory summary: {}", e))?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT path, size_bytes, status, contents_count, new_to_corpus
            FROM zip_inventory
            ORDER BY size_bytes DESC
            LIMIT 10
            "#,
        )
        .map_err(|e| format!("Failed to prepare largest zips query: {}", e))?;

    let largest_zips = stmt
        .query_map([], |row| {
            Ok(ZipRow {
                path: row.get(0)?,
                size_bytes: row.get(1)?,
                status: row.get(2)?,
                contents_count: row.get(3)?,
                new_to_corpus: row.get(4)?,
            })
        })
        .map_err(|e| format!("Failed to query largest zips: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect zip rows: {}", e))?;

    Ok(ZipInventory {
        total: summary.0,
        processed: summary.1,
        encrypted: summary.2,
        pending: summary.3,
        failed: summary.4,
        new_to_corpus: summary.5,
        largest_zips,
    })
}

// ============================================================================
// Duplicate groups (top 10 by total size)
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct CorpusDuplicateGroup {
    pub sha256: String,
    pub copy_count: i64,
    pub size_each: i64,
    pub wasted_bytes: i64,
}

#[tauri::command]
pub fn provenance_duplicate_groups(
    state: State<'_, CorpusState>,
) -> Result<Vec<CorpusDuplicateGroup>, String> {
    let conn = get_corpus_conn(&state)?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT
                sha256,
                COUNT(*) AS copy_count,
                MIN(size_bytes) AS size_each,
                (COUNT(*) - 1) * MIN(size_bytes) AS wasted_bytes
            FROM f2_file_index
            WHERE sha256 IS NOT NULL AND status != 'missing'
            GROUP BY sha256
            HAVING COUNT(*) > 1
            ORDER BY SUM(size_bytes) DESC
            LIMIT 10
            "#,
        )
        .map_err(|e| format!("Failed to prepare duplicate groups query: {}", e))?;

    let rows = stmt
        .query_map([], |row| {
            Ok(CorpusDuplicateGroup {
                sha256: row.get(0)?,
                copy_count: row.get(1)?,
                size_each: row.get(2)?,
                wasted_bytes: row.get(3)?,
            })
        })
        .map_err(|e| format!("Failed to query duplicate groups: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect duplicate groups: {}", e))?;

    Ok(rows)
}

// ============================================================================
// Failed migrations (individual rows)
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct FailedMigration {
    pub path: String,
    pub dest_path: String,
    pub error: Option<String>,
    pub proposed_at: String,
    pub migrated_at: Option<String>,
}

#[tauri::command]
pub fn provenance_failed_migrations(
    state: State<'_, CorpusState>,
) -> Result<Vec<FailedMigration>, String> {
    let conn = get_corpus_conn(&state)?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT
                path,
                dest_path,
                error,
                CAST(proposed_at AS VARCHAR) AS proposed_at,
                CAST(migrated_at AS VARCHAR) AS migrated_at
            FROM migrations
            WHERE status = 'failed'
            ORDER BY proposed_at DESC
            "#,
        )
        .map_err(|e| format!("Failed to prepare failed migrations query: {}", e))?;

    let rows = stmt
        .query_map([], |row| {
            Ok(FailedMigration {
                path: row.get(0)?,
                dest_path: row.get(1)?,
                error: row.get(2)?,
                proposed_at: row.get(3)?,
                migrated_at: row.get(4)?,
            })
        })
        .map_err(|e| format!("Failed to query failed migrations: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect failed migrations: {}", e))?;

    Ok(rows)
}

// ============================================================================
// Encrypted zip backlog
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct EncryptedZipRow {
    pub path: String,
    pub size_bytes: i64,
    pub parent_zip: Option<String>,
    pub depth: i64,
}

#[tauri::command]
pub fn provenance_encrypted_zips(
    state: State<'_, CorpusState>,
) -> Result<Vec<EncryptedZipRow>, String> {
    let conn = get_corpus_conn(&state)?;

    let mut stmt = conn
        .prepare(
            r#"
            SELECT path, size_bytes, parent_zip, depth
            FROM zip_inventory
            WHERE status = 'encrypted'
            ORDER BY size_bytes DESC
            "#,
        )
        .map_err(|e| format!("Failed to prepare encrypted zips query: {}", e))?;

    let rows = stmt
        .query_map([], |row| {
            Ok(EncryptedZipRow {
                path: row.get(0)?,
                size_bytes: row.get(1)?,
                parent_zip: row.get(2)?,
                depth: row.get(3)?,
            })
        })
        .map_err(|e| format!("Failed to query encrypted zips: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect encrypted zips: {}", e))?;

    Ok(rows)
}
