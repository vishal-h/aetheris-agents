//! Read-only view of the harness `skills` table (m14 T7).
//!
//! Every row the curator has written, with the three lifecycle dispositions an
//! operator has to tell apart derived here rather than left to the caller.
//! Nothing in this module writes: approval is a decision line (m14 q3) until
//! T11 gives it a mechanism, and the harness owns the table either way.

use crate::commands::harness::get_harness_conn;
use crate::HarnessState;
use std::collections::HashMap;
use tauri::State;

/// One `skills` row, JSON columns decoded.
///
/// `disposition` is DERIVED, never stored. It inverts the curator's own
/// `active/1` predicate (harness `lib/aetheris/skill/curator.ex`) —
/// `superseded_by IS NULL AND status != 'retired'` — into the three states a
/// reader must distinguish. The derivation lives in exactly one place so a
/// superseded row cannot reach the operator looking current.
#[derive(serde::Serialize)]
pub struct SkillRow {
    pub id:                 String,
    pub name:               String,
    pub description:        String,
    pub prompt_template:    String,
    pub tool_sequence:      Vec<String>,
    pub step_count:         i64,
    pub example_count:      i64,
    pub source_run_ids:     Vec<String>,
    pub extracted_at:       String,
    pub use_case:           Option<String>,
    pub status:             String,
    pub content_hash:       Option<String>,
    pub superseded_by:      Option<String>,
    pub superseded_by_name: Option<String>,
    pub approved_by:        Option<String>,
    pub approved_at:        Option<String>,
    pub disposition:        String,
    pub parse_errors:       Vec<String>,
}

#[derive(serde::Serialize)]
pub struct SkillCatalog {
    pub rows:             Vec<SkillRow>,
    pub active_count:     i64,
    pub superseded_count: i64,
    pub retired_count:    i64,
}

pub const DISPOSITION_ACTIVE:     &str = "active";
pub const DISPOSITION_SUPERSEDED: &str = "superseded";
pub const DISPOSITION_RETIRED:    &str = "retired";

// Supersession is checked first. A row that is both superseded and retired
// cannot arise from today's curator — only active rows are evictable and
// similarity runs against active rows only — so this is a defensive ordering,
// and it prefers the answer the operator can act on: supersession says where
// the content went. Nothing is hidden either way, because `status` travels on
// the row beside the disposition and the view renders both.
fn disposition(superseded_by: Option<&str>, status: &str) -> &'static str {
    match (superseded_by, status) {
        (Some(_), _) => DISPOSITION_SUPERSEDED,
        (None, DISPOSITION_RETIRED) => DISPOSITION_RETIRED,
        (None, _) => DISPOSITION_ACTIVE,
    }
}

// A malformed JSON column is REPORTED, not defaulted away: an empty tool
// sequence and an unparseable one render identically otherwise, which is the
// silent-wrong-answer the operator would have no way to see.
fn json_str_array(raw: &str, column: &str, errors: &mut Vec<String>) -> Vec<String> {
    match serde_json::from_str::<Vec<String>>(raw) {
        Ok(values) => values,
        Err(_) => {
            errors.push(column.to_string());
            Vec::new()
        }
    }
}

fn json_array_len(raw: &str, column: &str, errors: &mut Vec<String>) -> i64 {
    match serde_json::from_str::<serde_json::Value>(raw) {
        Ok(serde_json::Value::Array(items)) => items.len() as i64,
        _ => {
            errors.push(column.to_string());
            0
        }
    }
}

// Newest first, id as the tie-break: one curator pass writes many rows with the
// same `extracted_at`, and an unstable order makes two reads of the same table
// disagree about what an operator is looking at.
const SKILLS_SQL: &str = "
    SELECT
        id, name, description, prompt_template,
        tool_sequence_json, step_count, examples_json,
        source_run_ids_json, extracted_at,
        use_case, status, content_hash, superseded_by, approved_by, approved_at
    FROM skills
    ORDER BY extracted_at DESC, id ASC
";

#[tauri::command]
pub fn skills_catalog_load(state: State<'_, HarnessState>) -> Result<SkillCatalog, String> {
    let conn = get_harness_conn(&state)?;

    let mut stmt = conn
        .prepare(SKILLS_SQL)
        .map_err(|e| format!("skills query failed: {}", e))?;

    // Collected as a Result rather than filtered with `.ok()`: a row that fails
    // to decode is a fact about the table, and dropping it silently would show
    // the operator a short catalogue that looks complete.
    let mut rows: Vec<SkillRow> = stmt
        .query_map([], |r| {
            let mut parse_errors: Vec<String> = Vec::new();
            let tool_sequence =
                json_str_array(&r.get::<_, String>(4)?, "tool_sequence_json", &mut parse_errors);
            let example_count =
                json_array_len(&r.get::<_, String>(6)?, "examples_json", &mut parse_errors);
            let source_run_ids =
                json_str_array(&r.get::<_, String>(7)?, "source_run_ids_json", &mut parse_errors);

            let status: String = r.get(10)?;
            let superseded_by: Option<String> = r.get(12)?;

            Ok(SkillRow {
                disposition: disposition(superseded_by.as_deref(), &status).to_string(),
                id: r.get(0)?,
                name: r.get(1)?,
                description: r.get(2)?,
                prompt_template: r.get(3)?,
                tool_sequence,
                step_count: r.get(5)?,
                example_count,
                source_run_ids,
                extracted_at: r.get(8)?,
                use_case: r.get(9)?,
                status,
                content_hash: r.get(11)?,
                superseded_by,
                superseded_by_name: None,
                approved_by: r.get(13)?,
                approved_at: r.get(14)?,
                parse_errors,
            })
        })
        .map_err(|e| format!("skills rows failed: {}", e))?
        .collect::<Result<Vec<SkillRow>, _>>()
        .map_err(|e| format!("skills row decode failed: {}", e))?;

    // A supersession link is only readable if it resolves to something an
    // operator can look up; the id alone sends them back to the database.
    let names: HashMap<String, String> =
        rows.iter().map(|s| (s.id.clone(), s.name.clone())).collect();
    for row in &mut rows {
        row.superseded_by_name = row
            .superseded_by
            .as_ref()
            .and_then(|id| names.get(id).cloned());
    }

    let count_of = |want: &str| {
        rows.iter().filter(|s| s.disposition == want).count() as i64
    };

    Ok(SkillCatalog {
        active_count:     count_of(DISPOSITION_ACTIVE),
        superseded_count: count_of(DISPOSITION_SUPERSEDED),
        retired_count:    count_of(DISPOSITION_RETIRED),
        rows,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disposition_mirrors_the_curator_active_predicate() {
        assert_eq!(disposition(None, "candidate"), DISPOSITION_ACTIVE);
        assert_eq!(disposition(None, "validated"), DISPOSITION_ACTIVE);
        assert_eq!(disposition(None, "approved"), DISPOSITION_ACTIVE);
        assert_eq!(disposition(None, "retired"), DISPOSITION_RETIRED);
        assert_eq!(disposition(Some("abc"), "candidate"), DISPOSITION_SUPERSEDED);
        // Both at once: supersession wins, and `status` still carries "retired".
        assert_eq!(disposition(Some("abc"), "retired"), DISPOSITION_SUPERSEDED);
    }

    #[test]
    fn a_malformed_json_column_is_reported_not_defaulted() {
        let mut errors = Vec::new();
        assert_eq!(json_str_array(r#"["a","b"]"#, "tool_sequence_json", &mut errors), vec!["a", "b"]);
        assert!(errors.is_empty());

        assert!(json_str_array("not json", "tool_sequence_json", &mut errors).is_empty());
        assert_eq!(errors, vec!["tool_sequence_json"]);

        let mut errors = Vec::new();
        assert_eq!(json_array_len("[{}, {}]", "examples_json", &mut errors), 2);
        assert!(errors.is_empty());
        assert_eq!(json_array_len("{}", "examples_json", &mut errors), 0);
        assert_eq!(errors, vec!["examples_json"]);
    }
}
