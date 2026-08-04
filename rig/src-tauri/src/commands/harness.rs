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
// harness_run_artifacts (BL-073)
// ============================================================================

/// A document a run produced, resolved to an absolute path and **verified to exist**.
///
/// Existence is checked here rather than in the UI so "never a broken link" is a
/// structural property: the frontend can only render controls for artifacts that were
/// on disk when it asked. It also makes the overlay case fall out for free — a run under
/// a non-nil `overlay_base_dir` writes into the overlay, so the sandbox-resolved path
/// does not exist and the artifact is simply absent, with no overlay special-casing.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct RunArtifact {
    /// Absolute path on disk.
    pub path:     String,
    /// Basename, for display.
    pub filename: String,
}

/// Extensions that mean "a document a human would open".
///
/// Derived from what the generators actually emit — cloudcost renders `.html` (+ `.pdf`
/// when wkhtmltopdf is present), docbuilder emits `.xlsx`/`.docx`/`.pdf` — plus a small
/// forward-looking margin. `.json` is deliberately absent: every pipeline's intermediate
/// stages emit `.json`, which is exactly what must not be offered as "the report".
///
/// Matching is on the **value**, not the key: cloudcost puts its report under `file`,
/// docbuilder under `renamed`/`original` inside a list. Keying on `file` would be
/// cloudcost-specific and silently find nothing in docbuilder.
const DOCUMENT_EXTENSIONS: &[&str] = &[
    ".html", ".htm", ".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".md", ".xml",
];

fn is_document_path(s: &str) -> bool {
    let lower = s.to_ascii_lowercase();
    DOCUMENT_EXTENSIONS.iter().any(|ext| lower.ends_with(ext))
}

/// Collect every string value anywhere in `value` that looks like a document path.
///
/// Recursive because the shapes genuinely differ: cloudcost's parsed stdout is an object
/// with `file` at the top level; docbuilder's `rename_output` stdout is a **list** of
/// `{original, renamed}` objects. A top-level-keys-only scan finds the first and misses
/// the second entirely.
fn collect_document_paths(value: &serde_json::Value, out: &mut Vec<String>) {
    match value {
        serde_json::Value::String(s) => {
            if is_document_path(s) {
                out.push(s.clone());
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                collect_document_paths(item, out);
            }
        }
        serde_json::Value::Object(map) => {
            for item in map.values() {
                collect_document_paths(item, out);
            }
        }
        _ => {}
    }
}

/// Document paths carried by one `tool_result` payload, or none.
///
/// Four fallible hops, every one of which occurs in real data (BL-086 §7, measured over
/// 68 trajectories): the payload may carry `result` instead of `output` (native tools —
/// they produce no documents, so they are skipped rather than parsed); `output` is a JSON
/// *string* and is null 16×; that JSON's `stdout` is itself a string; and 63 of those
/// stdouts are not JSON at all. Any failure yields no artifacts and never propagates.
fn document_paths_in_payload(payload_json: &str) -> Vec<String> {
    let mut found = Vec::new();

    let Ok(payload) = serde_json::from_str::<serde_json::Value>(payload_json) else {
        return found;
    };
    // `output` is the MCP/exec key. Native tools use `result` and emit no documents.
    let Some(output) = payload.get("output").and_then(|v| v.as_str()) else {
        return found;
    };
    let Ok(outer) = serde_json::from_str::<serde_json::Value>(output) else {
        return found;
    };
    let Some(stdout) = outer.get("stdout").and_then(|v| v.as_str()) else {
        return found;
    };
    let Ok(inner) = serde_json::from_str::<serde_json::Value>(stdout) else {
        return found;
    };

    collect_document_paths(&inner, &mut found);
    found
}

/// Query core, split out so it is reachable from `cargo test` against a real connection.
///
/// `exists` is injected rather than calling the filesystem directly, so the existence
/// gate — the thing that makes "never a broken link" true — is testable without writing
/// files. Production passes a real `Path::exists`.
pub(crate) fn run_artifacts_with(
    conn: &rusqlite::Connection,
    run_id: &str,
    exists: &dyn Fn(&str) -> bool,
) -> Result<Vec<RunArtifact>, String> {
    let config_json: Option<String> = conn
        .query_row(
            "SELECT config_json FROM runs WHERE run_id = ?",
            params![run_id],
            |row| row.get(0),
        )
        .map_err(|e| format!("query error: {}", e))?;

    // No config → no sandbox → nothing can be resolved. Not an error; an empty answer.
    let Some(config_json) = config_json else {
        return Ok(vec![]);
    };
    let Ok(config) = serde_json::from_str::<serde_json::Value>(&config_json) else {
        return Ok(vec![]);
    };
    let Some(sandbox) = config.get("sandbox_path").and_then(|v| v.as_str()) else {
        return Ok(vec![]);
    };

    let mut stmt = conn
        .prepare(
            "SELECT payload_json FROM events
             WHERE run_id = ? AND type = 'tool_result'
             ORDER BY seq ASC",
        )
        .map_err(|e| format!("prepare error: {}", e))?;

    let payloads = stmt
        .query_map(params![run_id], |row| row.get::<_, Option<String>>(0))
        .map_err(|e| format!("query error: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("row error: {}", e))?;

    let mut seen = std::collections::HashSet::new();
    let mut artifacts = Vec::new();

    for payload in payloads.into_iter().flatten() {
        for rel in document_paths_in_payload(&payload) {
            let abs = if std::path::Path::new(&rel).is_absolute() {
                rel.clone()
            } else {
                format!("{}/{}", sandbox.trim_end_matches('/'), rel)
            };
            if !seen.insert(abs.clone()) {
                continue;
            }
            // The existence gate. docbuilder's rename_output reports both `original` and
            // `renamed`; the originals were renamed away, so they fail here and only the
            // real files survive — without this resolver knowing what those keys mean.
            if !exists(&abs) {
                continue;
            }
            let filename = abs.rsplit('/').next().unwrap_or(&abs).to_string();
            artifacts.push(RunArtifact { path: abs, filename });
        }
    }

    Ok(artifacts)
}

/// Report artifacts a run produced that still exist on disk. Empty when it produced none.
#[tauri::command]
pub fn harness_run_artifacts(
    state:  State<'_, HarnessState>,
    run_id: String,
) -> Result<Vec<RunArtifact>, String> {
    let conn = get_harness_conn(&state)?;
    run_artifacts_with(&conn, &run_id, &|p| std::path::Path::new(p).exists())
}

/// Open one of a run's artifacts with the OS default application.
///
/// **Why this exists rather than the frontend shell `open`.** `tauri-plugin-shell`'s
/// frontend `open` is URL-scoped — its allowlist regex is
/// `^((mailto:\w+)|(tel:\w+)|(https?://\w+)).+`, so a local filesystem path is rejected
/// outright. The obvious "fix" is to widen that scope to accept file paths, which would
/// hand the frontend the ability to open *any* local file and throw away the whole point
/// of the existence-gated resolver. Opening server-side instead keeps the surface closed:
/// there is no frontend primitive taking a raw path at all.
///
/// **The path is re-resolved, not trusted.** The caller passes a path, but it is only
/// opened if `run_artifacts_with` independently produces it for this run — the same
/// scrape, the same existence check, run again here. So the command can only ever open a
/// document some `tool_result` of that run actually recorded and that is on disk now. A
/// caller cannot use it to open an arbitrary file by passing one, which is exactly the
/// property widening the shell scope would have destroyed.
#[tauri::command]
pub fn harness_open_artifact(
    state:  State<'_, HarnessState>,
    run_id: String,
    path:   String,
) -> Result<(), String> {
    let allowed = {
        let conn = get_harness_conn(&state)?;
        run_artifacts_with(&conn, &run_id, &|p| std::path::Path::new(p).exists())?
    };

    if !allowed.iter().any(|a| a.path == path) {
        // Covers both "never an artifact of this run" and "was, but is gone now".
        return Err(format!(
            "not an existing artifact of run {run_id}: {path}"
        ));
    }

    open::that_detached(&path).map_err(|e| format!("open failed: {e}"))
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
    ///
    /// Windows at `DEFAULT_LIMIT`, not a literal: `useRunList` passes no `limit`, so
    /// the default *is* the window an operator sees, and the number this prints is
    /// the one the UI's "N of M" badge will show. A hardcoded 250 proved the same
    /// conclusion about a window nobody runs. (BL-038 review F1)
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

        let windowed = list_runs(&conn, DEFAULT_LIMIT, None).unwrap();
        assert!(
            !ids(&windowed).contains(&"demo-01".to_string()),
            "demo-01 is inside the {DEFAULT_LIMIT}-run default window — the search arm proves nothing"
        );
        assert!(
            windowed.total_count > windowed.runs.len() as i64,
            "store is not larger than the window; nothing to disclose"
        );

        let found = list_runs(&conn, DEFAULT_LIMIT, Some("demo-01")).unwrap();
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

    // ========================================================================
    // BL-073 — run_artifacts: the four-hop parse, value-scan, existence gate
    // ========================================================================

    /// Wrap a script's structured stdout in the two envelopes the exec server adds,
    /// exactly as observed on disk: payload.output is a JSON *string* whose `stdout`
    /// is itself a JSON string.
    fn tool_result_payload(stdout_json: &str) -> String {
        let outer = serde_json::json!({
            "tool_name": "run_command",
            "fs_hash": serde_json::Value::Null,
            "output": serde_json::json!({
                "exit_code": 0, "stderr": "", "stdout": stdout_json
            }).to_string(),
        });
        outer.to_string()
    }

    fn insert_event(conn: &Connection, run_id: &str, seq: i64, ty: &str, payload: Option<&str>) {
        conn.execute(
            "INSERT INTO events (id, run_id, step, seq, type, payload_json, timestamp)
             VALUES (?1, ?2, 0, ?3, ?4, ?5, '2026-08-04T00:00:00Z')",
            params![format!("{run_id}-{seq}"), run_id, seq, ty, payload],
        )
        .unwrap();
    }

    fn store_with_run(run_id: &str, config_json: &str) -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        seed(&conn);
        conn.execute(
            "INSERT INTO runs (run_id, label, status, config_json, started_at, finished_at)
             VALUES (?1, 'L', 'done', ?2, '2026-08-04T00:00:00Z', NULL)",
            params![run_id, config_json],
        )
        .unwrap();
        conn
    }

    const SANDBOX: &str = "/sbx";
    fn cfg() -> String {
        serde_json::json!({"sandbox_path": SANDBOX, "overlay_base_dir": serde_json::Value::Null})
            .to_string()
    }
    /// Everything exists — isolates parsing/selection from the existence gate.
    fn all_exist(_: &str) -> bool { true }

    /// cloudcost: object-shaped stdout, report under `file`, `template` beside it.
    #[test]
    fn cloudcost_shape_yields_only_the_report() {
        let conn = store_with_run("cc", &cfg());
        insert_event(&conn, "cc", 1, "tool_result", Some(&tool_result_payload(
            r#"{"status":"ok","file":"output/aws/aws_orphan_candidates_2026-08.json"}"#)));
        insert_event(&conn, "cc", 2, "tool_result", Some(&tool_result_payload(
            r#"{"status":"ok","file":"output/aws/cloudcost_report_2026-08.html",
                "pdf":null,"bytes":13063,
                "template":"/home/it/x/cloudcost/templates/report.html.j2"}"#)));

        let got = run_artifacts_with(&conn, "cc", &all_exist).unwrap();
        assert_eq!(
            got.iter().map(|a| a.path.as_str()).collect::<Vec<_>>(),
            vec!["/sbx/output/aws/cloudcost_report_2026-08.html"],
            "expected exactly the report: the .json intermediate must be excluded, and \
             `template` (report.html.j2) must NOT match — it ends .j2, not .html"
        );
        assert_eq!(got[0].filename, "cloudcost_report_2026-08.html");
    }

    /// docbuilder: stdout parses to a LIST of {original, renamed}. A top-level-keys-only
    /// scan finds nothing here, which is why the walk recurses.
    #[test]
    fn docbuilder_list_shape_is_found_by_recursion() {
        let conn = store_with_run("db", &cfg());
        insert_event(&conn, "db", 1, "tool_result", Some(&tool_result_payload(
            r#"[{"original":"output/invoice_v1.xlsx","renamed":"output/xyz_invoice.xlsx"},
                {"original":"output/invoice_v1.pdf","renamed":"output/xyz_invoice.pdf"}]"#)));

        let got = run_artifacts_with(&conn, "db", &all_exist).unwrap();
        assert_eq!(got.len(), 4, "all four paths are candidates before the existence gate");
    }

    /// The existence gate is what reduces docbuilder's 4 candidates to the 2 real files —
    /// without this resolver knowing what `original` and `renamed` mean.
    #[test]
    fn existence_gate_drops_the_renamed_away_originals() {
        let conn = store_with_run("db", &cfg());
        insert_event(&conn, "db", 1, "tool_result", Some(&tool_result_payload(
            r#"[{"original":"output/invoice_v1.xlsx","renamed":"output/xyz_invoice.xlsx"},
                {"original":"output/invoice_v1.pdf","renamed":"output/xyz_invoice.pdf"}]"#)));

        let on_disk = |p: &str| !p.contains("_v1.");
        let got = run_artifacts_with(&conn, "db", &on_disk).unwrap();
        assert_eq!(
            got.iter().map(|a| a.filename.as_str()).collect::<Vec<_>>(),
            vec!["xyz_invoice.xlsx", "xyz_invoice.pdf"]
        );
    }

    /// Overlay falls out of the existence gate: nothing is at the sandbox-resolved path,
    /// so the answer is empty and no control renders. No overlay special-casing exists.
    #[test]
    fn overlay_run_yields_nothing_via_the_existence_gate() {
        let cfg = serde_json::json!({
            "sandbox_path": SANDBOX, "overlay_base_dir": "/tmp/overlay"
        }).to_string();
        let conn = store_with_run("ov", &cfg);
        insert_event(&conn, "ov", 1, "tool_result", Some(&tool_result_payload(
            r#"{"file":"output/aws/cloudcost_report_2026-08.html"}"#)));

        let nothing_at_sandbox = |p: &str| !p.starts_with(SANDBOX);
        assert!(run_artifacts_with(&conn, "ov", &nothing_at_sandbox).unwrap().is_empty());
    }

    /// Every malformed hop observed in real data degrades to "no artifact", never an error.
    #[test]
    fn every_malformed_hop_degrades() {
        let conn = store_with_run("bad", &cfg());
        // native tool: `result`, not `output`
        insert_event(&conn, "bad", 1, "tool_result",
            Some(r#"{"tool_name":"read_file","result":"output/x.html"}"#));
        insert_event(&conn, "bad", 2, "tool_result", Some(r#"{"tool_name":"run_command"}"#));
        insert_event(&conn, "bad", 3, "tool_result",
            Some(r#"{"tool_name":"run_command","output":null}"#));
        insert_event(&conn, "bad", 4, "tool_result",
            Some(r#"{"tool_name":"run_command","output":"not json"}"#));
        insert_event(&conn, "bad", 5, "tool_result", Some(&tool_result_payload("not json either")));
        insert_event(&conn, "bad", 6, "tool_result", Some("{ this is not json"));
        insert_event(&conn, "bad", 7, "tool_result", None);
        insert_event(&conn, "bad", 8, "tool_result", Some(&tool_result_payload(
            r#"{"file":"output/report_data.json"}"#)));

        assert!(run_artifacts_with(&conn, "bad", &all_exist).unwrap().is_empty());
    }

    /// A `result`-carrying native tool must not be mined for paths even though its value
    /// looks like one — the anti-vacuity arm for the previous test, which would pass
    /// identically if the resolver simply found nothing anywhere.
    #[test]
    fn the_degrade_test_is_not_vacuous() {
        let conn = store_with_run("ok", &cfg());
        insert_event(&conn, "ok", 1, "tool_result", Some(&tool_result_payload(
            r#"{"file":"output/aws/cloudcost_report_2026-08.html"}"#)));
        assert_eq!(
            run_artifacts_with(&conn, "ok", &all_exist).unwrap().len(), 1,
            "the same harness DOES find an artifact in a well-formed payload, so the \
             all-empty assertions above are observations rather than a resolver that \
             never finds anything"
        );
    }

    /// Duplicate paths across results collapse; ordering is first-seen.
    #[test]
    fn duplicates_collapse() {
        let conn = store_with_run("dup", &cfg());
        for seq in 1..=3 {
            insert_event(&conn, "dup", seq, "tool_result", Some(&tool_result_payload(
                r#"{"file":"output/r.html"}"#)));
        }
        assert_eq!(run_artifacts_with(&conn, "dup", &all_exist).unwrap().len(), 1);
    }

    /// A run with no config_json resolves to nothing rather than erroring.
    #[test]
    fn missing_config_yields_empty() {
        let conn = Connection::open_in_memory().unwrap();
        seed(&conn);
        conn.execute(
            "INSERT INTO runs (run_id, label, status, config_json, started_at, finished_at)
             VALUES ('nc', 'L', 'done', NULL, '2026-08-04T00:00:00Z', NULL)", params![],
        ).unwrap();
        assert!(run_artifacts_with(&conn, "nc", &all_exist).unwrap().is_empty());
    }

    /// Live arm — the real store and the real filesystem, both reference runs (BL-073).
    ///
    /// The unit tests above inject `exists`; this one uses the actual `Path::exists`, so
    /// it is the only place the resolution + existence gate is exercised end to end
    /// against files that really are (and are not) on disk.
    #[test]
    #[ignore = "requires AETHERIS_DB_PATH — run with `cargo test -- --ignored`"]
    fn live_artifacts_for_cloudcost_and_docbuilder() {
        let path = std::env::var("AETHERIS_DB_PATH")
            .expect("AETHERIS_DB_PATH must be set for the live arm");
        let conn =
            Connection::open_with_flags(&path, rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        let real = |p: &str| std::path::Path::new(p).exists();

        // cloudcost: exactly one artifact, the HTML report.
        let cc = run_artifacts_with(&conn, "cloudcost-orch-aws-3KU2NQ", &real).unwrap();
        eprintln!("live cloudcost → {:?}", cc.iter().map(|a| &a.filename).collect::<Vec<_>>());
        assert_eq!(cc.len(), 1, "expected a single report, got {cc:?}");
        assert!(cc[0].filename.ends_with(".html"));
        assert!(cc[0].path.starts_with('/') && real(&cc[0].path));

        // docbuilder: several documents, and ONLY the ones that survived the rename.
        let db = run_artifacts_with(&conn, "docbuilder-orch-wFwf_g", &real).unwrap();
        eprintln!("live docbuilder → {:?}", db.iter().map(|a| &a.filename).collect::<Vec<_>>());
        assert!(db.len() > 1, "expected the multi-document case, got {db:?}");
        assert!(
            db.iter().all(|a| real(&a.path)),
            "every returned artifact must exist on disk"
        );
        assert!(
            !db.iter().any(|a| a.filename.contains("_v1.")),
            "the renamed-away `original` paths must have been dropped by the existence \
             gate, but some survived: {db:?}"
        );

        // A run that produced no document at all → no control.
        let none = run_artifacts_with(&conn, "docbuilder-ctx-0nDlug", &real).unwrap();
        eprintln!("live no-artifact run → {} artifact(s)", none.len());
        assert!(none.is_empty(), "expected no artifacts, got {none:?}");
    }

    /// Live open arm (BL-073 reopen) — exercises the exact server-side path the button
    /// calls, including the real `open::that_detached`, against real artifacts.
    ///
    /// This is the acceptance for the shell-scope fix: the frontend `open` rejected local
    /// paths with a regex-validation error, and the question is whether opening from Rust
    /// works. SIDE EFFECT: actually launches the OS handler for two files.
    #[test]
    #[ignore = "opens real files in the OS default app — run with `cargo test -- --ignored`"]
    fn live_open_artifact_end_to_end() {
        let path = std::env::var("AETHERIS_DB_PATH")
            .expect("AETHERIS_DB_PATH must be set for the live arm");
        let conn =
            Connection::open_with_flags(&path, rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        let real = |p: &str| std::path::Path::new(p).exists();

        for (run, want_ext) in [
            ("cloudcost-orch-aws-3KU2NQ", ".html"),
            ("docbuilder-orch-wFwf_g", ".pdf"),
        ] {
            let allowed = run_artifacts_with(&conn, run, &real).unwrap();
            let target = allowed
                .iter()
                .find(|a| a.filename.ends_with(want_ext))
                .unwrap_or_else(|| panic!("no {want_ext} artifact for {run}: {allowed:?}"));

            // The membership check the command performs before opening.
            assert!(allowed.iter().any(|a| a.path == target.path));
            eprintln!("opening {}", target.path);
            open::that_detached(&target.path)
                .unwrap_or_else(|e| panic!("open failed for {}: {e}", target.path));
        }

        // The guard: a path that is not one of the run's artifacts is refused.
        let allowed = run_artifacts_with(&conn, "cloudcost-orch-aws-3KU2NQ", &real).unwrap();
        assert!(
            !allowed.iter().any(|a| a.path == "/etc/hostname"),
            "an arbitrary local file must never appear in the allowed set"
        );
        eprintln!("guard ok: arbitrary path not in allowed set");
    }
}
