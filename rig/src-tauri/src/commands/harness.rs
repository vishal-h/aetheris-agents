use crate::HarnessState;
use rusqlite::params;
use tauri::State;

pub(crate) fn get_harness_conn<'a>(
    state: &'a State<'a, HarnessState>,
) -> Result<std::sync::MutexGuard<'a, rusqlite::Connection>, String> {
    state
        .conn
        .as_ref()
        .ok_or_else(|| "harness not connected".to_string())?
        .lock()
        .map_err(|e| format!("DB lock error: {}", e))
}

// ============================================================================
// harness_connection_status
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct HarnessStatus {
    pub connected: bool,
    pub db_path:   Option<String>,
    pub run_count: i64,
    pub error:     Option<String>,
}

#[tauri::command]
pub fn harness_connection_status(state: State<'_, HarnessState>) -> Result<HarnessStatus, String> {
    match get_harness_conn(&state) {
        Ok(conn) => {
            let count: i64 = conn
                .query_row("SELECT COUNT(*) FROM runs", [], |row| row.get(0))
                .map_err(|e| format!("query error: {}", e))?;
            Ok(HarnessStatus {
                connected: true,
                db_path:   state.path.clone(),
                run_count: count,
                error:     None,
            })
        }
        Err(e) => Ok(HarnessStatus {
            connected: false,
            db_path:   None,
            run_count: 0,
            error:     Some(e),
        }),
    }
}

// ============================================================================
// harness_list_runs
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct RunSummary {
    pub run_id:         String,
    pub label:          String,
    pub status:         String,
    pub provider:       String,
    pub model:          String,
    pub started_at:     String,
    pub finished_at:    Option<String>,
    pub step_count:     i64,
    pub event_count:    i64,
    pub last_event_at:  Option<String>,
    pub total_cost_usd: Option<f64>,
}

#[tauri::command]
pub fn harness_list_runs(
    state: State<'_, HarnessState>,
    limit: Option<i64>,
) -> Result<Vec<RunSummary>, String> {
    let conn = get_harness_conn(&state)?;
    let limit = limit.unwrap_or(500);

    let sql = "
        SELECT
            r.run_id,
            COALESCE(
                json_extract(r.config_json, '$.label'),
                r.run_id
            ) AS label,
            r.status,
            COALESCE(json_extract(r.config_json, '$.provider'), '') AS provider,
            COALESCE(json_extract(r.config_json, '$.model'), '')    AS model,
            r.started_at,
            r.finished_at,
            COALESCE((SELECT MAX(e.step)   FROM events e WHERE e.run_id = r.run_id), 0) AS step_count,
            COALESCE((SELECT COUNT(*)      FROM events e WHERE e.run_id = r.run_id), 0) AS event_count,
            (SELECT MAX(e.timestamp) FROM events e WHERE e.run_id = r.run_id)            AS last_event_at,
            (SELECT SUM(CASE WHEN e.type = 'llm_responded'
                             THEN json_extract(e.payload_json, '$.cost_usd') END)
             FROM events e WHERE e.run_id = r.run_id)                                    AS total_cost_usd
        FROM runs r
        ORDER BY r.started_at DESC
        LIMIT ?
    ";

    let mut stmt = conn.prepare(sql).map_err(|e| format!("prepare error: {}", e))?;
    let rows = stmt
        .query_map(params![limit], |row| {
            Ok(RunSummary {
                run_id:         row.get(0)?,
                label:          row.get(1)?,
                status:         row.get(2)?,
                provider:       row.get(3)?,
                model:          row.get(4)?,
                started_at:     row.get(5)?,
                finished_at:    row.get(6)?,
                step_count:     row.get(7)?,
                event_count:    row.get(8)?,
                last_event_at:  row.get(9)?,
                total_cost_usd: row.get(10)?,
            })
        })
        .map_err(|e| format!("query error: {}", e))?;

    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("row error: {}", e))
}

// ============================================================================
// harness_get_events
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct EventRow {
    pub id:         String,
    pub run_id:     String,
    pub step:       i64,
    pub seq:        i64,
    pub event_type: String,
    pub payload:    String,
    pub timestamp:  String,
}

#[tauri::command]
pub fn harness_get_events(
    state: State<'_, HarnessState>,
    run_id: String,
) -> Result<Vec<EventRow>, String> {
    let conn = get_harness_conn(&state)?;

    let sql = "
        SELECT id, run_id, step, seq, type, payload_json, timestamp
        FROM events
        WHERE run_id = ?
        ORDER BY seq ASC
    ";

    let mut stmt = conn.prepare(sql).map_err(|e| format!("prepare error: {}", e))?;
    let rows = stmt
        .query_map(params![run_id], |row| {
            Ok(EventRow {
                id:         row.get(0)?,
                run_id:     row.get(1)?,
                step:       row.get(2)?,
                seq:        row.get(3)?,
                event_type: row.get(4)?,
                payload:    row.get(5)?,
                timestamp:  row.get(6)?,
            })
        })
        .map_err(|e| format!("query error: {}", e))?;

    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("row error: {}", e))
}

// ============================================================================
// harness_get_run
// ============================================================================

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct RunDetail {
    pub run_id:      String,
    pub label:       String,
    pub status:      String,
    pub config:      String,
    pub started_at:  String,
    pub finished_at: Option<String>,
}

#[tauri::command]
pub fn harness_get_run(
    state: State<'_, HarnessState>,
    run_id: String,
) -> Result<RunDetail, String> {
    let conn = get_harness_conn(&state)?;

    let sql = "
        SELECT
            run_id,
            COALESCE(json_extract(config_json, '$.label'), run_id) AS label,
            status,
            config_json,
            started_at,
            finished_at
        FROM runs
        WHERE run_id = ?
    ";

    conn.query_row(sql, params![run_id], |row| {
        Ok(RunDetail {
            run_id:      row.get(0)?,
            label:       row.get(1)?,
            status:      row.get(2)?,
            config:      row.get(3)?,
            started_at:  row.get(4)?,
            finished_at: row.get(5)?,
        })
    })
    .map_err(|e| format!("query error: {}", e))
}
