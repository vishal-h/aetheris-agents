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
    /// SUM of `input_tokens` / `output_tokens` over this run's `llm_responded`
    /// events. NULL (not 0) when no event carries token data — stub/Ollama runs
    /// and pre-instrumentation Anthropic runs, same contract as `total_cost_usd`.
    pub total_input_tokens:  Option<i64>,
    pub total_output_tokens: Option<i64>,
}

/// The rows *and* the count they were drawn from, in one round-trip (BL-038).
///
/// `total_count` is `COUNT(*)` under the **same** `WHERE` as `runs`, taken inside
/// the same read transaction, so the UI's "N of M" disclosure cannot disagree with
/// the list it labels. A second `harness_runs_count` command was rejected for
/// exactly this reason: two calls can straddle a harness write and desync the badge
/// from the rows — a well-formed wrong answer, which is the class this ticket exists
/// to remove, not to relocate.
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct RunListResult {
    pub runs:        Vec<RunSummary>,
    pub total_count: i64,
}

const DEFAULT_LIMIT: i64 = 500;

/// The single filter both queries share. `?1` is the `%term%` pattern, or NULL when
/// there is no search — NULL short-circuits the OR to "every run", so the searched
/// and unsearched paths are one SQL string with one binding rather than two clauses
/// that can drift apart.
///
/// Matches the **raw** `r.label` / `r.run_id`, not the `COALESCE(r.label, r.run_id)
/// AS label` alias the SELECT exposes: an unlabelled run has `label IS NULL`, `LIKE`
/// never matches NULL, and the `r.run_id` arm is what finds it. `demo-01` (NULL
/// label, 879th by `started_at DESC` of 896) is the recorded instance.
const RUNS_WHERE: &str = "
        WHERE (?1 IS NULL
               OR r.label  LIKE ?1 ESCAPE '\\'
               OR r.run_id LIKE ?1 ESCAPE '\\')
";

/// Wrap a search term as a `%term%` LIKE pattern with metacharacters escaped.
///
/// `%` and `_` are LIKE wildcards and `\` is the escape character. Unescaped, a
/// search for the real run_id `run_zS6XSQ` would treat its `_` as "any character",
/// and a lone `_` or `%` would match the whole store — a silently *wider* result set
/// that looks exactly like a correct one.
fn like_pattern(term: &str) -> String {
    let mut out = String::with_capacity(term.len() + 2);
    out.push('%');
    for c in term.chars() {
        if matches!(c, '\\' | '%' | '_') {
            out.push('\\');
        }
        out.push(c);
    }
    out.push('%');
    out
}

/// An absent, empty, or whitespace-only search is "no search" — the same binding
/// (NULL) as the no-search path, so the two are identical by construction.
fn search_pattern(search: Option<&str>) -> Option<String> {
    match search.map(str::trim) {
        Some(t) if !t.is_empty() => Some(like_pattern(t)),
        _ => None,
    }
}

#[tauri::command]
pub fn harness_list_runs(
    state: State<'_, HarnessState>,
    limit: Option<i64>,
    search: Option<String>,
) -> Result<RunListResult, String> {
    let conn = get_harness_conn(&state)?;
    list_runs(&conn, limit.unwrap_or(DEFAULT_LIMIT), search.as_deref())
}

/// Query core, split out from the `#[tauri::command]` wrapper so it is reachable
/// from `cargo test` against a real (in-memory or on-disk) connection — a command
/// taking `State` is not.
pub(crate) fn list_runs(
    conn: &rusqlite::Connection,
    limit: i64,
    search: Option<&str>,
) -> Result<RunListResult, String> {
    let pattern = search_pattern(search);

    let select = "
        SELECT
            r.run_id,
            -- The harness strips `label` from config_json before persisting
            -- (server.ex:758 `Map.delete(:label)`); it lives in the dedicated
            -- runs.label column (store.ex:807). The fallback stays for runs that
            -- are genuinely unlabelled — label is nullable. (BL-029)
            COALESCE(r.label, r.run_id) AS label,
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
             FROM events e WHERE e.run_id = r.run_id)                                    AS total_cost_usd,
            -- Tokens live ONLY on llm_responded (specs §6). No COALESCE: NULL must
            -- stay NULL so stub runs stay distinguishable from a genuine zero. (BL-004)
            (SELECT SUM(CASE WHEN e.type = 'llm_responded'
                             THEN json_extract(e.payload_json, '$.input_tokens') END)
             FROM events e WHERE e.run_id = r.run_id)                                    AS total_input_tokens,
            (SELECT SUM(CASE WHEN e.type = 'llm_responded'
                             THEN json_extract(e.payload_json, '$.output_tokens') END)
             FROM events e WHERE e.run_id = r.run_id)                                    AS total_output_tokens
        FROM runs r";

    let list_sql = format!("{select}{RUNS_WHERE}        ORDER BY r.started_at DESC\n        LIMIT ?2\n");
    let count_sql = format!("SELECT COUNT(*) FROM runs r{RUNS_WHERE}");

    // Both reads under one deferred transaction so `total_count` describes the same
    // snapshot the rows came from. The connection is opened SQLITE_OPEN_READ_ONLY
    // (rig/CLAUDE.md), so this only takes a read snapshot — it never writes, and the
    // implicit rollback on drop is a no-op. Without it, a harness INSERT landing
    // between the two statements is enough to make the badge misdescribe the list.
    let tx = conn
        .unchecked_transaction()
        .map_err(|e| format!("read transaction error: {}", e))?;

    let mut stmt = tx.prepare(&list_sql).map_err(|e| format!("prepare error: {}", e))?;
    let rows = stmt
        .query_map(params![pattern, limit], |row| {
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
                total_input_tokens:  row.get(11)?,
                total_output_tokens: row.get(12)?,
            })
        })
        .map_err(|e| format!("query error: {}", e))?;

    let runs = rows
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("row error: {}", e))?;

    let total_count: i64 = tx
        .query_row(&count_sql, params![pattern], |row| row.get(0))
        .map_err(|e| format!("count error: {}", e))?;

    Ok(RunListResult { runs, total_count })
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
            -- runs.label column, not config_json — see harness_list_runs. (BL-029)
            COALESCE(label, run_id) AS label,
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

// ============================================================================
// Tests — harness_list_runs search + window disclosure (BL-038)
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    /// Only the columns `list_runs` actually reads. The real schema is the
    /// harness's (`../aetheris/lib/aetheris/store.ex`); `runs.label` is nullable
    /// there, which is the property under test.
    fn seed(conn: &Connection) {
        conn.execute_batch(
            "CREATE TABLE runs (
                 run_id      TEXT PRIMARY KEY,
                 label       TEXT,
                 status      TEXT NOT NULL,
                 config_json TEXT,
                 started_at  TEXT NOT NULL,
                 finished_at TEXT
             );
             CREATE TABLE events (
                 id           TEXT PRIMARY KEY,
                 run_id       TEXT NOT NULL,
                 step         INTEGER,
                 seq          INTEGER,
                 type         TEXT,
                 payload_json TEXT,
                 timestamp    TEXT
             );",
        )
        .unwrap();
    }

    fn insert_run(conn: &Connection, run_id: &str, label: Option<&str>, started_at: &str) {
        conn.execute(
            "INSERT INTO runs (run_id, label, status, config_json, started_at, finished_at)
             VALUES (?1, ?2, 'done', '{\"provider\":\"stub\",\"model\":\"m\"}', ?3, NULL)",
            params![run_id, label, started_at],
        )
        .unwrap();
    }

    /// 12 recent runs (`recent-00`..`recent-11`, 2026-07-*) plus one deliberately
    /// old, **unlabelled** run standing in for `demo-01`. Every query in these
    /// tests runs at a limit well below 13, so the old run is outside the window.
    fn store_with_an_old_unlabelled_run() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        seed(&conn);
        for i in 0..12 {
            insert_run(
                &conn,
                &format!("recent-{i:02}"),
                Some(&format!("Payslip Orchestrator {i}")),
                &format!("2026-07-{:02}T10:00:00Z", i + 1),
            );
        }
        insert_run(&conn, "demo-01", None, "2026-05-12T06:15:25.146402Z");
        conn
    }

    fn ids(result: &RunListResult) -> Vec<String> {
        result.runs.iter().map(|r| r.run_id.clone()).collect()
    }

    /// The load-bearing arm: **absent first, then present**. A search test against
    /// a run already inside the window proves nothing — it would pass identically
    /// if the search term were ignored entirely.
    #[test]
    fn search_reaches_a_run_outside_the_window() {
        let conn = store_with_an_old_unlabelled_run();

        let windowed = list_runs(&conn, 5, None).unwrap();
        assert_eq!(windowed.runs.len(), 5);
        assert!(
            !ids(&windowed).contains(&"demo-01".to_string()),
            "precondition failed — demo-01 is inside the window, so the search arm below \
             would pass without searching anything: {:?}",
            ids(&windowed)
        );

        let found = list_runs(&conn, 5, Some("demo-01")).unwrap();
        assert_eq!(ids(&found), vec!["demo-01".to_string()]);
    }

    #[test]
    fn unsearched_total_count_is_the_whole_store_not_the_window() {
        let conn = store_with_an_old_unlabelled_run();
        let result = list_runs(&conn, 5, None).unwrap();

        assert_eq!(result.runs.len(), 5);
        assert_eq!(result.total_count, 13);
        assert!(result.total_count > result.runs.len() as i64);
    }

    #[test]
    fn searched_total_count_is_the_match_count_not_the_store_count() {
        let conn = store_with_an_old_unlabelled_run();
        // "recent-0" matches recent-00..recent-09 — 10 of 13, windowed to 4.
        let result = list_runs(&conn, 4, Some("recent-0")).unwrap();

        assert_eq!(result.runs.len(), 4);
        assert_eq!(result.total_count, 10);
    }

    #[test]
    fn empty_and_whitespace_search_are_identical_to_no_search() {
        let conn = store_with_an_old_unlabelled_run();
        let none = list_runs(&conn, 5, None).unwrap();

        for term in ["", "   "] {
            let searched = list_runs(&conn, 5, Some(term)).unwrap();
            assert_eq!(ids(&searched), ids(&none), "term {term:?}");
            assert_eq!(searched.total_count, none.total_count, "term {term:?}");
        }
    }

    /// An unlabelled run is reachable only by run_id (`LIKE` never matches NULL),
    /// which is why the WHERE matches the raw columns and not the COALESCE alias.
    #[test]
    fn search_matches_label_and_run_id_separately() {
        let conn = store_with_an_old_unlabelled_run();

        let by_label = list_runs(&conn, 50, Some("Orchestrator 7")).unwrap();
        assert_eq!(ids(&by_label), vec!["recent-07".to_string()]);

        let by_run_id = list_runs(&conn, 50, Some("emo-0")).unwrap();
        assert_eq!(ids(&by_run_id), vec!["demo-01".to_string()]);
    }

    #[test]
    fn search_is_case_insensitive() {
        let conn = store_with_an_old_unlabelled_run();
        let result = list_runs(&conn, 50, Some("PAYSLIP orchestrator 3")).unwrap();
        assert_eq!(ids(&result), vec!["recent-03".to_string()]);
    }

    /// `_` and `%` are LIKE wildcards; escaped, they match themselves only.
    #[test]
    fn like_metacharacters_are_literal() {
        let conn = Connection::open_in_memory().unwrap();
        seed(&conn);
        insert_run(&conn, "run_zS6XSQ", None, "2026-07-01T10:00:00Z");
        insert_run(&conn, "runXzS6XSQ", None, "2026-07-02T10:00:00Z");

        let underscore = list_runs(&conn, 50, Some("run_z")).unwrap();
        assert_eq!(ids(&underscore), vec!["run_zS6XSQ".to_string()]);

        let percent = list_runs(&conn, 50, Some("%")).unwrap();
        assert_eq!(percent.total_count, 0);
    }

    /// Live evidence arm — opt-in (`cargo test -- --ignored`), because it reads the
    /// operator's real harness store. Panics rather than skips when
    /// `AETHERIS_DB_PATH` is unset: a check that quietly passes when it did not run
    /// is worse than no check.
    #[test]
    #[ignore = "requires AETHERIS_DB_PATH — run with `cargo test -- --ignored`"]
    fn live_store_demo_01_absent_from_window_then_found_by_search() {
        let path = std::env::var("AETHERIS_DB_PATH")
            .expect("AETHERIS_DB_PATH must be set for the live arm");
        let conn = Connection::open_with_flags(
            &path,
            rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
        )
        .unwrap();

        let windowed = list_runs(&conn, 250, None).unwrap();
        assert!(
            !ids(&windowed).contains(&"demo-01".to_string()),
            "demo-01 is inside the 250-run window — the search arm proves nothing"
        );
        assert!(
            windowed.total_count > windowed.runs.len() as i64,
            "store is not larger than the window; nothing to disclose"
        );

        let found = list_runs(&conn, 250, Some("demo-01")).unwrap();
        assert!(
            found.runs.iter().any(|r| r.run_id == "demo-01"),
            "search did not reach demo-01: {:?}",
            ids(&found)
        );
        eprintln!(
            "live: window {} of {} runs; search 'demo-01' → {} match(es)",
            windowed.runs.len(),
            windowed.total_count,
            found.total_count
        );
    }
}
