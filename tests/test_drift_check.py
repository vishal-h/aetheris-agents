"""
Unit and integration tests for scripts/drift_check.py.

Unit tests use inline fixtures and never touch the repo files.
Integration tests (marked @pytest.mark.integration) run against the live repo.
"""

import pytest
import drift_check


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def reset():
    drift_check.FINDINGS.clear()


def fails_of(check_name):
    return [msg for l, c, msg in drift_check.FINDINGS if l == "FAIL" and c == check_name]


def warns_of(check_name):
    return [msg for l, c, msg in drift_check.FINDINGS if l == "WARN" and c == check_name]


def passes_of(check_name):
    return [msg for l, c, msg in drift_check.FINDINGS if l == "PASS" and c == check_name]


# --------------------------------------------------------------------------- #
# event_types — parser tests                                                   #
# --------------------------------------------------------------------------- #

_EVENT_EX_SAMPLE = """
  @type event_type ::
          :prompt_built
          | :llm_called
          | :llm_responded
          | :context_summarised
"""

_SPECS_S6_SAMPLE = """
## 6. Event Type Reference

Authoritative source: event.ex

| Event type | Payload fields (key ones) |
|-----------|--------------------------|
| `prompt_built` | `context_hash`, `message_count` |
| `llm_called` | `model` |
| `llm_responded` | `cost_usd`, `latency_ms` |
| `context_summarised` | `summary` |

"""


def test_parse_event_types_from_event_ex():
    types = drift_check._parse_event_types_from_event_ex(_EVENT_EX_SAMPLE, "test")
    assert types == {"prompt_built", "llm_called", "llm_responded", "context_summarised"}


def test_parse_event_types_from_specs():
    types = drift_check._parse_event_types_from_specs(_SPECS_S6_SAMPLE, "test")
    assert types == {"prompt_built", "llm_called", "llm_responded", "context_summarised"}


def test_event_types_anchor_missing_in_event_ex_is_fail():
    reset()
    result = drift_check._parse_event_types_from_event_ex("no type block here", "event_types")
    assert result is None
    assert fails_of("event_types"), "expected FAIL when @type event_type anchor missing"


def test_event_types_anchor_missing_in_specs_is_fail():
    reset()
    result = drift_check._parse_event_types_from_specs("no section here", "event_types")
    assert result is None
    assert fails_of("event_types"), "expected FAIL when §6 anchor missing"


def test_event_types_zero_items_is_fail():
    reset()
    result = drift_check._parse_event_types_from_event_ex(
        "@type event_type ::\n  no_atoms_here", "event_types"
    )
    assert result is None
    assert fails_of("event_types"), "expected FAIL when zero atoms parsed"


# --------------------------------------------------------------------------- #
# tauri_commands — parser tests                                                #
# --------------------------------------------------------------------------- #

_LIB_RS_SAMPLE = """
    .invoke_handler(tauri::generate_handler![
      commands::harness::harness_list_runs,
      commands::harness::harness_get_events,
      commands::agent_config::agent_config_set,
    ])
"""

_SPECS_S4_SAMPLE = """
## 4. Tauri Command Shapes

### Harness commands (`commands/harness.rs`)

**`harness_list_runs`**

Returns a `Vec<RunSummary>`.

**`harness_get_events`**

Takes `run_id: String`.

### Agent config commands (`commands/agent_config.rs`) — p7

| Command | Args | Returns |
|---------|------|---------|
| `agent_config_set` | `key`, `value` | `()` |
| `agent_config_get_all` | — | `HashMap<String, String>` |

"""


def test_parse_commands_from_lib_rs():
    cmds = drift_check._parse_commands_from_lib_rs(_LIB_RS_SAMPLE, "test")
    assert cmds == {"harness_list_runs", "harness_get_events", "agent_config_set"}


def test_commands_lib_rs_anchor_missing_is_fail():
    reset()
    result = drift_check._parse_commands_from_lib_rs("no handler here", "tauri_commands")
    assert result is None
    assert fails_of("tauri_commands"), "expected FAIL when generate_handler! missing"


def test_parse_commands_from_specs():
    cmds = drift_check._parse_commands_from_specs(_SPECS_S4_SAMPLE, "test")
    assert "harness_list_runs" in cmds
    assert "harness_get_events" in cmds
    assert "agent_config_set" in cmds
    assert "agent_config_get_all" in cmds
    # Prose words like "String" or "HashMap" must not appear (no underscore)
    assert "String" not in cmds
    assert "HashMap" not in cmds


def test_commands_specs_anchor_missing_is_fail():
    reset()
    result = drift_check._parse_commands_from_specs("no §4 here", "tauri_commands")
    assert result is None
    assert fails_of("tauri_commands"), "expected FAIL when §4 anchor missing"


# --------------------------------------------------------------------------- #
# db_schema — parser tests                                                     #
# --------------------------------------------------------------------------- #

_STORE_EX_SAMPLE = """
Exqlite.Sqlite3.execute(conn, \"\"\"
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'running',
  label  TEXT
)
\"\"\")

Exqlite.Sqlite3.execute(conn, \"\"\"
ALTER TABLE runs ADD COLUMN extra_col TEXT
\"\"\")
"""

_SPECS_S2_SAMPLE = """
## 2. Harness DB Schema

### `runs`
```sql
CREATE TABLE runs (
  run_id  TEXT PRIMARY KEY,
  status  TEXT NOT NULL DEFAULT 'running',
  label   TEXT
);
```

"""


def test_parse_tables_from_store_ex():
    tables = drift_check._parse_tables_from_store_ex(_STORE_EX_SAMPLE, "test")
    assert tables is not None
    assert "runs" in tables
    assert "run_id" in tables["runs"]
    assert "status" in tables["runs"]
    assert "label" in tables["runs"]
    assert "extra_col" in tables["runs"]  # added via ALTER TABLE


def test_parse_tables_from_specs():
    tables = drift_check._parse_tables_from_specs(_SPECS_S2_SAMPLE, "test")
    assert tables is not None
    assert "runs" in tables
    assert "run_id" in tables["runs"]
    assert "status" in tables["runs"]
    assert "label" in tables["runs"]


def test_db_schema_anchor_missing_in_store_is_fail():
    reset()
    result = drift_check._parse_tables_from_store_ex("no tables here", "db_schema")
    assert result is None
    assert fails_of("db_schema"), "expected FAIL when no CREATE TABLE in store.ex"


def test_db_schema_anchor_missing_in_specs_is_fail():
    reset()
    result = drift_check._parse_tables_from_specs("no schema section", "db_schema")
    assert result is None
    assert fails_of("db_schema"), "expected FAIL when §2 anchor missing"


# --------------------------------------------------------------------------- #
# routes — parser tests                                                        #
# --------------------------------------------------------------------------- #

_REGISTRY_SAMPLE = """
const harnessModule = {
  sections: [
    { id: 'runs',  path: '/harness' },
    { id: 'diff',  path: '/diff'    },
  ],
};
"""

_APP_TSX_SAMPLE = """
<Route path="/" element={<Navigate to="/harness" replace />} />
<Route path="/harness" element={<HarnessRoute />} />
<Route path="/diff" element={<DiffView />} />
<Route path="/settings" element={<SettingsRoute />} />
"""


def test_parse_routes_from_registry():
    paths = drift_check._parse_routes_from_registry(_REGISTRY_SAMPLE, "test")
    assert paths == {"/harness", "/diff"}


def test_parse_routes_from_app_tsx():
    paths = drift_check._parse_routes_from_app_tsx(_APP_TSX_SAMPLE, "test")
    # "/" and "/settings" excluded by _ROUTE_EXCEPTIONS
    assert paths == {"/harness", "/diff"}


def test_routes_registry_anchor_missing_is_fail():
    reset()
    result = drift_check._parse_routes_from_registry("no paths here", "routes")
    assert result is None
    assert fails_of("routes"), "expected FAIL when no paths in registry.ts"


def test_routes_app_tsx_anchor_missing_is_fail():
    reset()
    result = drift_check._parse_routes_from_app_tsx("no routes here", "routes")
    assert result is None
    assert fails_of("routes"), "expected FAIL when no paths in App.tsx"


# --------------------------------------------------------------------------- #
# env_vars — parser tests                                                      #
# --------------------------------------------------------------------------- #

_RUST_ENV_SAMPLE = """\
let x = std::env::var("AETHERIS_DB_PATH").unwrap();
let y = std::env::var("AETHERIS_AGENTS_PATH").ok();
let z = std::env::var("PROVENANCE_DB_PATH").ok();
// system vars — no underscore so filtered out:
let _ = std::env::var("USER");
let _ = std::env::var("USERNAME");
// dynamic var — not a literal, not captured:
let _ = std::env::var(&some_key);
"""


def test_parse_env_vars_from_rust_text():
    result = drift_check._parse_env_vars_from_rust_text(_RUST_ENV_SAMPLE)
    assert "AETHERIS_DB_PATH" in result
    assert "AETHERIS_AGENTS_PATH" in result
    assert "PROVENANCE_DB_PATH" in result
    assert "USER" not in result      # no underscore — filtered
    assert "USERNAME" not in result  # no underscore — filtered


# --------------------------------------------------------------------------- #
# payload_fields — parser tests                                                #
# --------------------------------------------------------------------------- #

_SPECS_S6_PAYLOAD_SAMPLE = """
## 6. Event Type Reference

| Event type | Payload fields (key ones) |
|-----------|--------------------------|
| `llm_responded` | `response_type`, `cost_usd`, `latency_ms` |
| `tool_called` | `tool_name`, `tool_input` |
| `run_complete` | `reason` — `agent_finished` \\| `max_steps_reached` |

"""


def test_parse_payload_fields_from_specs():
    fields = drift_check._parse_payload_fields_from_specs(_SPECS_S6_PAYLOAD_SAMPLE, "test")
    assert fields is not None
    assert "llm_responded" in fields
    assert "cost_usd" in fields["llm_responded"]
    assert "latency_ms" in fields["llm_responded"]
    assert "tool_called" in fields
    assert "tool_name" in fields["tool_called"]
    assert "tool_input" in fields["tool_called"]
    assert "run_complete" in fields
    assert "reason" in fields["run_complete"]
    # enum values listed after " — " must not be extracted as payload fields
    assert "agent_finished" not in fields["run_complete"]
    assert "max_steps_reached" not in fields["run_complete"]


def test_payload_fields_anchor_missing_is_fail():
    reset()
    result = drift_check._parse_payload_fields_from_specs("nothing here", "payload_fields")
    assert result is None
    assert fails_of("payload_fields"), "expected FAIL when §6 anchor missing"


# --------------------------------------------------------------------------- #
# milestone_status — behaviour test                                            #
# --------------------------------------------------------------------------- #

def test_milestone_status_no_status_line_is_warn(tmp_path):
    reset()
    milestone = tmp_path / "p99"
    milestone.mkdir()
    (milestone / "README.md").write_text("# P99\n\nNo status here.\n")

    orig = drift_check.MILESTONES_DIR
    drift_check.MILESTONES_DIR = tmp_path
    try:
        drift_check.check_milestone_status()
    finally:
        drift_check.MILESTONES_DIR = orig

    assert warns_of("milestone_status"), "expected WARN when Status: line missing"


def test_milestone_status_with_status_line_passes(tmp_path):
    reset()
    milestone = tmp_path / "p99"
    milestone.mkdir()
    (milestone / "README.md").write_text("# P99\n\n**Status: IMPLEMENTED**\n")

    orig = drift_check.MILESTONES_DIR
    drift_check.MILESTONES_DIR = tmp_path
    try:
        drift_check.check_milestone_status()
    finally:
        drift_check.MILESTONES_DIR = orig

    assert not warns_of("milestone_status")
    assert passes_of("milestone_status")


# --------------------------------------------------------------------------- #
# Integration — run all checks against live repo                               #
# --------------------------------------------------------------------------- #

@pytest.mark.integration
def test_integration_no_fail():
    """Run all drift checks against the live repo. Zero FAIL findings required."""
    reset()
    drift_check._strict = False
    for fn in drift_check.CHECKS:
        fn()

    failed = [(c, msg) for l, c, msg in drift_check.FINDINGS if l == "FAIL"]
    report = "\n".join(f"  [{c}] {msg}" for c, msg in failed)
    assert not failed, f"drift_check found FAIL findings:\n{report}"
