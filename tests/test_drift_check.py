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

_SPECS_S6_OPTIONAL_SAMPLE = """
## 6. Event Type Reference

| Event type | Payload fields (key ones) |
|-----------|--------------------------|
| `llm_responded` | `cost_usd`, `stop_reason?` |

"""


def test_parse_payload_fields_from_specs():
    fields = drift_check._parse_payload_fields_from_specs(_SPECS_S6_PAYLOAD_SAMPLE, "test")
    assert fields is not None
    assert "llm_responded" in fields
    # required fields parse as is_optional=False
    assert "cost_usd" in fields["llm_responded"]
    assert fields["llm_responded"]["cost_usd"] is False
    assert "latency_ms" in fields["llm_responded"]
    assert "tool_called" in fields
    assert "tool_name" in fields["tool_called"]
    assert "tool_input" in fields["tool_called"]
    assert "run_complete" in fields
    assert "reason" in fields["run_complete"]
    # enum values listed after " — " must not be extracted as payload fields
    assert "agent_finished" not in fields["run_complete"]
    assert "max_steps_reached" not in fields["run_complete"]


def test_parse_payload_fields_optional_flag():
    fields = drift_check._parse_payload_fields_from_specs(_SPECS_S6_OPTIONAL_SAMPLE, "test")
    assert fields is not None
    assert fields["llm_responded"]["cost_usd"] is False   # required
    assert fields["llm_responded"]["stop_reason"] is True  # optional; ? stripped from key


def test_payload_fields_optional_absent_no_fail():
    """Optional field missing from DB events must not produce FAIL — only INFO."""
    reset()
    fields = drift_check._parse_payload_fields_from_specs(_SPECS_S6_OPTIONAL_SAMPLE, "test")
    assert fields is not None
    # Simulate: DB has cost_usd but not stop_reason
    drift_check._evaluate_payload_fields("llm_responded", fields["llm_responded"], {"cost_usd"})
    assert not fails_of("payload_fields"), "optional absent field must not FAIL"


def test_payload_fields_optional_present_passes():
    """Optional field present in DB events validates the same as a required field."""
    reset()
    fields = drift_check._parse_payload_fields_from_specs(_SPECS_S6_OPTIONAL_SAMPLE, "test")
    assert fields is not None
    # Simulate: DB has both fields
    drift_check._evaluate_payload_fields("llm_responded", fields["llm_responded"], {"cost_usd", "stop_reason"})
    assert not fails_of("payload_fields"), "optional field present should not FAIL"


def test_payload_fields_required_absent_still_fails():
    """Regression guard: required field absent from DB must still FAIL."""
    reset()
    fields = drift_check._parse_payload_fields_from_specs(_SPECS_S6_OPTIONAL_SAMPLE, "test")
    assert fields is not None
    # Simulate: DB has stop_reason but NOT cost_usd (required)
    drift_check._evaluate_payload_fields("llm_responded", fields["llm_responded"], {"stop_reason"})
    assert fails_of("payload_fields"), "required field absent must FAIL"


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
# project_knowledge — behaviour tests                                          #
# --------------------------------------------------------------------------- #

_MANIFEST_SAMPLE = """\
# Project Knowledge Manifest

| export name | repo path | repo | commit | last changed |
|-------------|-----------|------|--------|--------------|
| `rig--specs.md` | `docs/rig/specs.md` | aetheris-agents | `abc1234` | 2026-06-11 |
| `aetheris--CLAUDE.md` | `CLAUDE.md` | aetheris | `def5678` | 2026-06-11 |
| `project-knowledge-manifest.md` | `docs/project-knowledge-manifest.md` | aetheris-agents | _(this export)_ | 2026-06-11 |
"""

_MANIFEST_ZERO_ROWS = """\
# Project Knowledge Manifest

No table here.
"""


def test_project_knowledge_manifest_absent_is_warn(tmp_path):
    reset()
    orig = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = tmp_path / "nonexistent.md"
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig
    assert warns_of("project_knowledge"), "expected WARN when manifest absent"
    assert not fails_of("project_knowledge")


def test_project_knowledge_zero_rows_is_fail(tmp_path):
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_ZERO_ROWS)
    orig = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig
    assert fails_of("project_knowledge"), "expected FAIL when zero rows parsed"


def test_project_knowledge_stale_entry_is_warn(tmp_path, monkeypatch):
    """A manifest commit that differs from git HEAD must produce WARN."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    # Patch git to always return a hash different from the manifest values.
    # _git_is_dirty is patched too: it shells out to the real working tree, which
    # would make this test depend on ambient repo state (BL-041b).
    monkeypatch.setattr(drift_check, "_git_head_hash", lambda repo_dir, path: "zzz9999")
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    assert warns_of("project_knowledge"), "expected WARN for stale entry"
    assert not fails_of("project_knowledge")


def test_project_knowledge_stale_exempt_under_strict(tmp_path, monkeypatch):
    """BL-009: under --strict, manifest STALENESS stays WARN, does not FAIL."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest
    monkeypatch.setattr(drift_check, "_git_head_hash", lambda repo_dir, path: "zzz9999")
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    drift_check._strict = True
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest
        drift_check._strict = False

    assert warns_of("project_knowledge"), "staleness must stay WARN under --strict"
    assert not fails_of("project_knowledge"), "staleness must NOT be promoted to FAIL"


def test_project_knowledge_structural_fails_under_strict(tmp_path, monkeypatch):
    """BL-009: under --strict, a STRUCTURAL pk problem (git can't verify) still FAILs.

    Exemption is staleness-specific, not check-specific — the un-walked boundary
    branch flagged in the BL-009 review (finding 1)."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest
    # git_head_hash returns None → "git log failed — cannot verify" (structural WARN)
    monkeypatch.setattr(drift_check, "_git_head_hash", lambda repo_dir, path: None)
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    drift_check._strict = True
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest
        drift_check._strict = False

    assert fails_of("project_knowledge"), "structural pk WARN must FAIL under --strict"


def test_project_knowledge_fresh_entries_pass(tmp_path, monkeypatch):
    """All manifest commits matching git HEAD must produce PASS."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    # Return the exact commit hash from the manifest for each call
    commit_map = {"docs/rig/specs.md": "abc1234", "CLAUDE.md": "def5678"}
    monkeypatch.setattr(
        drift_check, "_git_head_hash",
        lambda repo_dir, path: commit_map.get(path, "abc1234"),
    )
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    assert not warns_of("project_knowledge")
    assert not fails_of("project_knowledge")
    assert passes_of("project_knowledge")


# --------------------------------------------------------------------------- #
# project_knowledge — uncommitted-edit guard (BL-041b)                         #
# --------------------------------------------------------------------------- #
#
# check 8 compares COMMITTED history (`git log -1 -- <path>`), so an uncommitted
# edit to a tracked path is invisible to it and a pre-commit --strict run reports
# the manifest clean whether or not the edit was made. These tests cover both
# directions of the guard that makes that vacuity visible.


def _fresh_hashes(repo_dir, path):
    """_git_head_hash stub: every manifest row matches, so staleness never fires."""
    return {"docs/rig/specs.md": "abc1234", "CLAUDE.md": "def5678"}.get(path, "abc1234")


def test_project_knowledge_uncommitted_path_is_warn(tmp_path, monkeypatch):
    """A manifest-tracked path with working-tree changes must produce WARN."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(
        drift_check, "_git_is_dirty",
        lambda repo_dir, path: path == "docs/rig/specs.md",
    )
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    warns = warns_of("project_knowledge")
    assert any("uncommitted" in w and "docs/rig/specs.md" in w for w in warns), warns
    assert not fails_of("project_knowledge")
    # No PASS: "all match git HEAD" would answer a question this run cannot answer.
    assert not passes_of("project_knowledge")


def test_project_knowledge_uncommitted_exempt_under_strict(tmp_path, monkeypatch):
    """BL-041b: the uncommitted-edit WARN is strict-exempt — WARN, never FAIL."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(
        drift_check, "_git_is_dirty",
        lambda repo_dir, path: path == "docs/rig/specs.md",
    )
    drift_check._strict = True
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest
        drift_check._strict = False

    assert warns_of("project_knowledge"), "uncommitted WARN must survive --strict"
    assert not fails_of("project_knowledge"), "uncommitted WARN must NOT be promoted to FAIL"


def test_project_knowledge_clean_tree_is_silent(tmp_path, monkeypatch):
    """Clean tree + fresh hashes: no uncommitted signal at all, PASS emitted."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    assert not warns_of("project_knowledge")
    assert passes_of("project_knowledge")


def test_project_knowledge_dirty_untracked_path_is_silent(tmp_path, monkeypatch):
    """A dirty path that is NOT a manifest row produces no signal.

    The guard is scoped to manifest-tracked paths — an unrelated working-tree
    edit must not make check 8 noisy."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(
        drift_check, "_git_is_dirty",
        lambda repo_dir, path: path == "scripts/not_in_the_manifest.py",
    )
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    assert not warns_of("project_knowledge")
    assert passes_of("project_knowledge")


def test_project_knowledge_git_status_failure_fails_under_strict(tmp_path, monkeypatch):
    """A git status failure is STRUCTURAL, not exempt — it FAILs under --strict."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: None)
    drift_check._strict = True
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest
        drift_check._strict = False

    fails = fails_of("project_knowledge")
    assert any("git status failed" in f for f in fails), fails


def test_project_knowledge_structural_failure_suppresses_pass(tmp_path, monkeypatch):
    """BL-041b review F1: a row that could not be verified must suppress the PASS.

    "N manifest entries all match git HEAD" beside a structural WARN is a count
    that includes rows the run never checked — the Silent-wrong-answer carrier this
    ticket exists to remove, one arm over. Non-strict, so the WARN is not masked by
    promotion to FAIL."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    # git log cannot answer for one row; the others are clean and fresh.
    monkeypatch.setattr(
        drift_check, "_git_head_hash",
        lambda repo_dir, path: None if path == "CLAUDE.md" else "abc1234",
    )
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    assert warns_of("project_knowledge")
    assert not passes_of("project_knowledge"), "PASS must not print beside a structural WARN"


def test_project_knowledge_unknown_repo_suppresses_pass(tmp_path, monkeypatch):
    """The unknown-repo arm `continue`s before either guard — its own case."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(
        _MANIFEST_SAMPLE.replace("| aetheris |", "| not-a-repo |")
    )

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(drift_check, "_git_is_dirty", lambda repo_dir, path: False)
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    warns = warns_of("project_knowledge")
    assert any("unknown repo name" in w for w in warns), warns
    assert not passes_of("project_knowledge"), "PASS must not print beside a skipped row"


def test_project_knowledge_dirty_check_runs_in_the_rows_own_repo(tmp_path, monkeypatch):
    """Each row's porcelain runs in the repo that OWNS it.

    The harness rows live in the sibling ../aetheris checkout; running git status
    against REPO_ROOT for them would report every harness path clean."""
    reset()
    manifest = tmp_path / "manifest.md"
    manifest.write_text(_MANIFEST_SAMPLE)

    calls: list[tuple] = []

    orig_manifest = drift_check.MANIFEST_MD
    drift_check.MANIFEST_MD = manifest

    def recording_is_dirty(repo_dir, path):
        calls.append((repo_dir, path))
        return False

    monkeypatch.setattr(drift_check, "_git_head_hash", _fresh_hashes)
    monkeypatch.setattr(drift_check, "_git_is_dirty", recording_is_dirty)
    try:
        drift_check.check_project_knowledge()
    finally:
        drift_check.MANIFEST_MD = orig_manifest

    assert (drift_check.REPO_ROOT, "docs/rig/specs.md") in calls, calls
    assert (drift_check.HARNESS_ROOT, "CLAUDE.md") in calls, calls


# --------------------------------------------------------------------------- #
# command_fields — behaviour tests (BL-036)                                    #
# --------------------------------------------------------------------------- #

_SPECS_S4_STRUCTS = """
## 4. Tauri Command Shapes

**`harness_get_run`**

```rust
pub struct RunDetail {
    pub run_id:      String,
    pub label:       String,       // COALESCE(runs.label, run_id) — the label column,
                                   // NOT config_json
    pub finished_at: Option<String>,
}
```

## 5. TypeScript Interfaces
"""

_RUST_STRUCTS = """
#[derive(Debug, serde::Serialize)]
pub struct RunDetail {
    pub run_id:      String,
    /// COALESCE over the label column.
    pub label:       String,
    pub finished_at: Option<String>,
}
"""


def _run_command_fields(monkeypatch, specs_text, rust_text):
    """Drive check_command_fields against inline fixtures only (no repo files)."""
    monkeypatch.setattr(drift_check, "_require_file", lambda path, check: specs_text)
    monkeypatch.setattr(
        drift_check, "_parse_command_structs_from_source",
        lambda commands_dir: drift_check._parse_structs_from_rust_text(rust_text),
    )
    reset()
    drift_check.check_command_fields()


def test_parse_rust_struct_fields_strips_comments_and_attributes():
    body = """
    #[serde(rename = "id")]
    pub run_id: String,
    /// A doc comment.
    pub label:  String,        // trailing note
    pub extra:  HashMap<String, String>,
"""
    fields = drift_check._parse_rust_struct_fields(body)
    assert fields == {
        "run_id": "String",
        "label": "String",
        "extra": "HashMap<String,String>",
    }


def test_command_fields_matching_struct_passes(monkeypatch):
    _run_command_fields(monkeypatch, _SPECS_S4_STRUCTS, _RUST_STRUCTS)
    assert not warns_of("command_fields")
    assert not fails_of("command_fields")
    assert passes_of("command_fields")


def test_command_fields_phantom_documented_field_is_warn(monkeypatch):
    """The RunDetail.events case: documented in §4, never present in the struct."""
    specs = _SPECS_S4_STRUCTS.replace(
        "    pub finished_at: Option<String>,",
        "    pub finished_at: Option<String>,\n    pub events:      Vec<EventRow>,",
    )
    _run_command_fields(monkeypatch, specs, _RUST_STRUCTS)

    warns = warns_of("command_fields")
    assert any("RunDetail.events" in w and "not in the Rust struct" in w for w in warns), warns
    assert not passes_of("command_fields")


def test_command_fields_undocumented_source_field_is_warn(monkeypatch):
    rust = _RUST_STRUCTS.replace(
        "    pub finished_at: Option<String>,",
        "    pub finished_at: Option<String>,\n    pub status:      String,",
    )
    _run_command_fields(monkeypatch, _SPECS_S4_STRUCTS, rust)

    warns = warns_of("command_fields")
    assert any("RunDetail.status" in w and "not documented" in w for w in warns), warns


def test_command_fields_type_mismatch_is_warn(monkeypatch):
    rust = _RUST_STRUCTS.replace("pub run_id:      String,", "pub run_id:      i64,")
    _run_command_fields(monkeypatch, _SPECS_S4_STRUCTS, rust)

    warns = warns_of("command_fields")
    assert any("RunDetail.run_id" in w and "type mismatch" in w for w in warns), warns


def test_command_fields_optional_suffix_matches_option(monkeypatch):
    """§6's `field?` convention, reused: documented `field?: T` ↔ Rust Option<T>."""
    specs = _SPECS_S4_STRUCTS.replace(
        "pub finished_at: Option<String>,", "pub finished_at?: String,"
    )
    _run_command_fields(monkeypatch, specs, _RUST_STRUCTS)

    assert not warns_of("command_fields"), warns_of("command_fields")
    assert passes_of("command_fields")


def test_command_fields_optional_suffix_still_flags_absent_field(monkeypatch):
    """`?` relaxes the TYPE, not existence — a `field?` absent from the struct warns."""
    specs = _SPECS_S4_STRUCTS.replace(
        "    pub finished_at: Option<String>,",
        "    pub finished_at: Option<String>,\n    pub events?:     Vec<EventRow>,",
    )
    _run_command_fields(monkeypatch, specs, _RUST_STRUCTS)

    warns = warns_of("command_fields")
    assert any("RunDetail.events" in w and "not in the Rust struct" in w for w in warns), warns


def test_command_fields_ghost_struct_is_warn(monkeypatch):
    _run_command_fields(monkeypatch, _SPECS_S4_STRUCTS, "// no structs here\n")

    warns = warns_of("command_fields")
    assert any("RunDetail" in w and "ghost" in w for w in warns), warns


def test_command_fields_zero_structs_parsed_is_fail(monkeypatch):
    specs = "## 4. Tauri Command Shapes\n\nNo fenced blocks here.\n\n## 5. Next\n"
    _run_command_fields(monkeypatch, specs, _RUST_STRUCTS)

    assert fails_of("command_fields"), "expected FAIL when §4 has zero rust structs"


def test_command_fields_section_anchor_missing_is_fail(monkeypatch):
    _run_command_fields(monkeypatch, "# specs\n\nno section 4\n", _RUST_STRUCTS)

    assert fails_of("command_fields"), "expected FAIL when the §4 anchor is missing"


# --------------------------------------------------------------------------- #
# use_case_registry — ds t1a                                                   #
# --------------------------------------------------------------------------- #
# Every fixture below is SYNTHETIC and written to tmp_path. The broken states are
# constructed here, never by editing a tracked file — per `../aetheris/CLAUDE.md`
# **Silent-wrong-answer**, ***"construct the broken state and watch the check fail in it,
# as part of writing the check"***, and per the 2026-08-16 export-boundary rule that a
# mutation on a file carrying uncommitted work is restored from a working copy, which is
# avoided entirely by never mutating a tracked file.

_USE_CASES_SAMPLE = """# Use cases

## Membership — what is a row

Prose, with a table the parser must not read as data:

| check | home |
|---|---|
| registry <-> directories | tests/ |

## The registry

| Use case | Status | Status set | Reason (business state) | Condition for return |
|---|---|---|---|---|
| `alpha` | active | 2026-01-01 | Work is not paused. | Nothing pending. |
| `beta/one` | active | 2026-01-01 | Work is not paused. | Nothing pending. |
| `beta/two` | dormant | 2026-01-02 | Paused pending a client. | It runs again when that work resumes. |

## After the table

| not | a row |
|---|---|
"""

_KEY_DOCS_SAMPLE = """# CLAUDE.md

## Key docs to read for each use case

| Use case | Read first |
|----------|-----------|
| alpha | `alpha/runbook.md` |
| beta/one | `beta/docs/design.md` |
| beta/two | `beta/docs/design.md` |

Trailing prose.

## Next section
"""

_README_SAMPLE = """# readme

## Use cases

| Directory | What it does | Status |
|-----------|-------------|--------|
| [`alpha/`](alpha/) | does alpha | OK |
| [`beta/one/`](beta/one/) | does beta one | OK |
| [`beta/two/`](beta/two/) | does beta two | dormant |

### Something else
"""


def _registry_env(tmp_path, monkeypatch, registry=None, key_docs=None, readme=None):
    """Point every path the check reads at tmp_path, and stub the tree-derived arms.

    The three arms that read the real tree (the section-agent glob, the tools.json glob and
    the agent-bearing predicate) are given a synthetic layout under tmp_path rather than
    being skipped, so the predicate itself is exercised.
    """
    root = tmp_path / "repo"
    (root / "agents").mkdir(parents=True)
    # alpha and beta/one carry agents; beta/two does not — the dormant, non-agent-bearing case.
    for uc in ("alpha", "beta/one"):
        (root / uc / "agents").mkdir(parents=True)
        (root / uc / "agents" / "orch.exs").write_text("%Aetheris.RunConfig{}")
        (root / "agents" / f"capability_matrix_{uc.replace('/', '_')}.exs").write_text("x")
    (root / "beta" / "two").mkdir(parents=True)
    (root / "alpha" / "tools.json").write_text("{}")

    assemble = root / "assemble_matrix.py"
    assemble.write_text('SECTIONS = [\n    ("alpha", "alpha"),\n    ("beta_one", "beta/one"),\n]\n')
    overrides = root / "overrides.json"
    overrides.write_text('{"_comment": "ignored", "alpha": {}}')
    manifests = root / "test_tools_manifests.py"
    manifests.write_text(
        'assert SWEPT == [\n    "alpha",\n    "beta",\n]\n'
        'NO_MANIFEST_YET = ("beta",)\n'
    )
    tools_rs = root / "tools.rs"
    tools_rs.write_text('        vec!["alpha"],\n')

    reg = root / "use-cases.md"
    reg.write_text(registry if registry is not None else _USE_CASES_SAMPLE)
    kd = root / "CLAUDE.md"
    kd.write_text(key_docs if key_docs is not None else _KEY_DOCS_SAMPLE)
    rm = root / "README.md"
    rm.write_text(readme if readme is not None else _README_SAMPLE)

    monkeypatch.setattr(drift_check, "REPO_ROOT", root)
    monkeypatch.setattr(drift_check, "USE_CASES_MD", reg)
    monkeypatch.setattr(drift_check, "AGENTS_CLAUDE_MD", kd)
    monkeypatch.setattr(drift_check, "README_MD", rm)
    monkeypatch.setattr(drift_check, "ASSEMBLE_PY", assemble)
    monkeypatch.setattr(drift_check, "OVERRIDES_JSON", overrides)
    monkeypatch.setattr(drift_check, "TOOLS_MANIFEST_TEST", manifests)
    monkeypatch.setattr(drift_check, "TOOLS_RS", tools_rs)


def test_use_case_registry_all_arms_green(tmp_path, monkeypatch):
    """The positive control. Every mutation below is read against this."""
    reset()
    _registry_env(tmp_path, monkeypatch)
    drift_check.check_use_case_registry()
    assert not fails_of("use_case_registry"), fails_of("use_case_registry")
    assert len(passes_of("use_case_registry")) == 9, passes_of("use_case_registry")


def test_use_case_registry_names_the_agent_bearing_predicate(tmp_path, monkeypatch):
    """A failure must say WHICH set it is comparing, not just that two sets differ."""
    reset()
    _registry_env(tmp_path, monkeypatch)
    drift_check.check_use_case_registry()
    infos = [m for l, c, m in drift_check.FINDINGS if l == "INFO" and c == "use_case_registry"]
    assert any("agent-bearing: 2" in m and "beta/two" in m for m in infos), infos
    assert any(
        "AGENT-BEARING" in m for m in passes_of("use_case_registry")
    ), "the SECTIONS arm must name the predicate it filters by"


def test_use_case_registry_missing_file_is_fail(tmp_path, monkeypatch):
    reset()
    _registry_env(tmp_path, monkeypatch)
    monkeypatch.setattr(drift_check, "USE_CASES_MD", tmp_path / "nope.md")
    drift_check.check_use_case_registry()
    assert any("file not found" in m for m in fails_of("use_case_registry"))


def test_use_case_registry_anchor_missing_is_fail(tmp_path, monkeypatch):
    reset()
    _registry_env(
        tmp_path, monkeypatch, registry=_USE_CASES_SAMPLE.replace("## The registry", "## Rows")
    )
    drift_check.check_use_case_registry()
    assert any("anchor not found" in m for m in fails_of("use_case_registry"))


def test_use_case_registry_zero_rows_is_fail(tmp_path, monkeypatch):
    reset()
    gutted = _USE_CASES_SAMPLE.replace("| `alpha`", "").replace("| `beta/one`", "").replace(
        "| `beta/two`", ""
    )
    _registry_env(tmp_path, monkeypatch, registry=gutted)
    drift_check.check_use_case_registry()
    assert any("zero rows parsed" in m for m in fails_of("use_case_registry"))


def test_use_case_registry_mutation_claude_md_row_dropped(tmp_path, monkeypatch):
    """MUTATION — a use case is added to the registry and CLAUDE.md is not extended."""
    reset()
    _registry_env(
        tmp_path,
        monkeypatch,
        key_docs=_KEY_DOCS_SAMPLE.replace("| beta/two | `beta/docs/design.md` |\n", ""),
    )
    drift_check.check_use_case_registry()
    hits = [m for m in fails_of("use_case_registry") if "CLAUDE.md" in m]
    assert hits and "'beta/two'" in hits[0], fails_of("use_case_registry")


def test_use_case_registry_mutation_readme_row_orphaned(tmp_path, monkeypatch):
    """MUTATION — README names a use case the registry does not declare."""
    reset()
    _registry_env(
        tmp_path,
        monkeypatch,
        readme=_README_SAMPLE.replace(
            "\n### Something else", "| [`ghost/`](ghost/) | not declared | ? |\n\n### Something else"
        ),
    )
    drift_check.check_use_case_registry()
    hits = [m for m in fails_of("use_case_registry") if "README.md" in m]
    assert hits and "'ghost'" in hits[0], fails_of("use_case_registry")


def test_use_case_registry_mutation_sections_drifts(tmp_path, monkeypatch):
    """MUTATION — a section agent's key is dropped from SECTIONS."""
    reset()
    _registry_env(tmp_path, monkeypatch)
    drift_check.ASSEMBLE_PY.write_text('SECTIONS = [\n    ("alpha", "alpha"),\n]\n')
    drift_check.check_use_case_registry()
    hits = [m for m in fails_of("use_case_registry") if "SECTIONS" in m]
    assert hits and "'beta_one'" in hits[0], fails_of("use_case_registry")


def test_use_case_registry_mutation_dormant_use_case_pulled_into_matrix(tmp_path, monkeypatch):
    """MUTATION — the predicate is load-bearing, not decoration.

    Add a section agent for the NON-agent-bearing use case and SECTIONS gains its key: the
    arms must go red, because the matrix's declared scope is agent-bearing use cases and
    `beta/two` has no agents. Without the predicate this mutation would pass.
    """
    reset()
    _registry_env(tmp_path, monkeypatch)
    (drift_check.REPO_ROOT / "agents" / "capability_matrix_beta_two.exs").write_text("x")
    drift_check.ASSEMBLE_PY.write_text(
        'SECTIONS = [\n    ("alpha", "alpha"),\n    ("beta_one", "beta/one"),\n'
        '    ("beta_two", "beta/two"),\n]\n'
    )
    drift_check.check_use_case_registry()
    hits = fails_of("use_case_registry")
    assert len(hits) == 2, hits
    assert all("beta_two" in m for m in hits), hits


def test_use_case_registry_mutation_subset_arm_gains_an_outsider(tmp_path, monkeypatch):
    """MUTATION — a subset arm fails on an EXTRA, never on a shortfall."""
    reset()
    _registry_env(tmp_path, monkeypatch)
    drift_check.OVERRIDES_JSON.write_text('{"_comment": "x", "alpha": {}, "ghost": {}}')
    drift_check.check_use_case_registry()
    hits = [m for m in fails_of("use_case_registry") if "overrides" in m]
    assert hits and "'ghost'" in hits[0], fails_of("use_case_registry")


def test_use_case_registry_subset_arm_tolerates_a_shortfall(tmp_path, monkeypatch):
    """The restore side of the arm above: a subset arm covering ONE row is still green."""
    reset()
    _registry_env(tmp_path, monkeypatch)
    drift_check.OVERRIDES_JSON.write_text('{"_comment": "x"}')
    drift_check.check_use_case_registry()
    assert not fails_of("use_case_registry"), fails_of("use_case_registry")


def test_use_case_registry_mutation_swept_uses_sweep_keying(tmp_path, monkeypatch):
    """MUTATION — SWEPT is compared on the TOP-LEVEL keying, so `beta/one` presents as `beta`."""
    reset()
    _registry_env(tmp_path, monkeypatch)
    drift_check.TOOLS_MANIFEST_TEST.write_text(
        'assert SWEPT == [\n    "alpha",\n    "beta",\n    "gamma",\n]\n'
        'NO_MANIFEST_YET = ("beta",)\n'
    )
    drift_check.check_use_case_registry()
    hits = [m for m in fails_of("use_case_registry") if "SWEPT" in m]
    assert hits and "'gamma'" in hits[0], fails_of("use_case_registry")


def test_use_case_registry_takes_no_strict_exemption(tmp_path, monkeypatch):
    """Under --strict this check has no exempt findings: a WARN would become a FAIL.

    It emits none today; the assertion is that nothing it records is marked strict_exempt,
    which is what would silently neuter it later.
    """
    reset()
    _registry_env(tmp_path, monkeypatch)
    recorded = []
    orig = drift_check.record

    def spy(level, check, message, strict_exempt=False):
        recorded.append((level, check, strict_exempt))
        orig(level, check, message, strict_exempt)

    monkeypatch.setattr(drift_check, "record", spy)
    monkeypatch.setattr(drift_check, "_fail", lambda c, m: spy("FAIL", c, m))
    monkeypatch.setattr(drift_check, "_warn", lambda c, m, e=False: spy("WARN", c, m, e))
    monkeypatch.setattr(drift_check, "_info", lambda c, m: spy("INFO", c, m))
    monkeypatch.setattr(drift_check, "_ok", lambda c, m: spy("PASS", c, m))
    drift_check.check_use_case_registry()
    assert recorded, "check recorded nothing"
    assert not any(exempt for _, _, exempt in recorded), recorded


def test_use_case_registry_is_check_addressable():
    """--check use_case_registry resolves; the ticket's Done-check requires it."""
    assert "use_case_registry" in drift_check._CHECK_NAMES
    assert drift_check._CHECK_NAMES["use_case_registry"] is drift_check.check_use_case_registry
    assert drift_check.check_use_case_registry in drift_check.CHECKS


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


# --------------------------------------------------------------------------- #
# backlog_resolution — every BL-nnn in the scoped corpus names a real row       #
# (ds t1b)                                                                      #
# --------------------------------------------------------------------------- #

_OPEN_SAMPLE = """# Backlog — fixture

### BL-204 — an open row (#TBD)
**Status:** OPEN

body text
"""

_CLOSED_SAMPLE = """# Backlog — fixture (closed)

### BL-205 — a terminal row (#TBD)
**Status:** DONE

body text
"""


def _wire_backlog(monkeypatch, tmp_path, scope_text, open_md=None, closed_md=None):
    """Point the check at fixture backlogs and a one-file fixture corpus."""
    open_p = tmp_path / "backlog-2026-06.md"
    closed_p = tmp_path / "backlog-2026-06-closed.md"
    open_p.write_text(_OPEN_SAMPLE if open_md is None else open_md)
    closed_p.write_text(_CLOSED_SAMPLE if closed_md is None else closed_md)
    scope_p = tmp_path / "scoped.py"
    scope_p.write_text(scope_text)
    monkeypatch.setattr(drift_check, "BACKLOG_FILES", (open_p, closed_p))
    monkeypatch.setattr(
        drift_check, "_backlog_scope_files",
        lambda: [(open_p, "docs/backlog-2026-06.md"),
                 (closed_p, "docs/backlog-2026-06-closed.md"),
                 (scope_p, "scripts/scoped.py")],
    )


def test_backlog_resolution_resolves_across_the_union(tmp_path, monkeypatch):
    """The point of the check: a row in EITHER file resolves.

    BL-205 lives only in the archive. Reading the open file alone would report it
    as dangling — a well-formed answer to the wrong question.
    """
    reset()
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-204 and BL-205\n")
    drift_check.check_backlog_resolution()
    assert not fails_of("backlog_resolution")
    assert passes_of("backlog_resolution")


def test_backlog_resolution_open_file_alone_would_miss_the_archive(tmp_path, monkeypatch):
    """The union is load-bearing, not decorative — drop the archive and BL-205 dangles."""
    reset()
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-205\n")
    monkeypatch.setattr(drift_check, "BACKLOG_FILES",
                        (tmp_path / "backlog-2026-06.md",))
    drift_check.check_backlog_resolution()
    assert any("BL-205" in m for m in fails_of("backlog_resolution"))


def test_backlog_resolution_dangling_id_is_fail_not_warn(tmp_path, monkeypatch):
    """FAIL, never WARN: a WARN would be indistinguishable from the two exempt
    project_knowledge staleness WARNs and would inherit their expected-truth reading."""
    reset()
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-998\n")
    drift_check.check_backlog_resolution()
    assert any("BL-998" in m for m in fails_of("backlog_resolution"))
    assert not warns_of("backlog_resolution")
    assert not passes_of("backlog_resolution")


def test_backlog_resolution_allowlist_is_keyed_by_id_AND_file(tmp_path, monkeypatch):
    """An id excused in one file is NOT excused in another."""
    reset()
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-998\n")
    monkeypatch.setitem(drift_check.BACKLOG_REF_ALLOW,
                        ("BL-998", "some/other/file.py"), "excused elsewhere")
    drift_check.check_backlog_resolution()
    assert any("BL-998" in m for m in fails_of("backlog_resolution")), \
        "an allowlist entry for a DIFFERENT file must not excuse this one"

    reset()
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-998\n")
    monkeypatch.setitem(drift_check.BACKLOG_REF_ALLOW,
                        ("BL-998", "scripts/scoped.py"), "excused here, with a reason")
    drift_check.check_backlog_resolution()
    assert not fails_of("backlog_resolution")
    assert passes_of("backlog_resolution")


@pytest.mark.parametrize("token", ["BL-0xx", "BL-0NN", "BL-1xx", "BL-09[02]"])
def test_backlog_resolution_placeholders_do_not_match(tmp_path, monkeypatch, token):
    """The boundary is the point. A bare `BL-\\d+` truncates these to BL-0 / BL-1 /
    BL-09 and reports each as dangling; the three-digit-with-boundary form removes
    them structurally rather than by allowlist."""
    reset()
    _wire_backlog(monkeypatch, tmp_path, f"# a placeholder: {token}\n")
    drift_check.check_backlog_resolution()
    assert not fails_of("backlog_resolution"), f"{token} should not match"


@pytest.mark.parametrize("token,should_match", [
    ("BL-204", True),      # exact three digits
    ("BL-2040", False),    # four digits — right boundary
    ("xBL-204", False),    # left boundary: part of a longer word
    ("BL-10", False),      # two digits
])
def test_backlog_resolution_pattern_boundaries(token, should_match):
    got = bool(drift_check.BACKLOG_REF_RE.search(token))
    assert got is should_match, f"{token}: expected match={should_match}, got {got}"


def test_backlog_resolution_multi_id_heading_yields_every_owner(tmp_path, monkeypatch):
    """`### BL-050 + BL-055 + BL-056 — …` registers all three as real rows."""
    reset()
    closed = _CLOSED_SAMPLE + (
        "\n### BL-201 + BL-202 + BL-203 — DONE 2026-01-01 (one reorder, three rows)\n"
        "\nshared closure body\n"
    )
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-201 BL-202 BL-203\n", closed_md=closed)
    drift_check.check_backlog_resolution()
    assert not fails_of("backlog_resolution")


def test_backlog_resolution_missing_backlog_is_fail(tmp_path, monkeypatch):
    """Absent is unknown, not zero: with no rows parsed the check must not report
    that everything resolves against an empty set."""
    reset()
    _wire_backlog(monkeypatch, tmp_path, "# refs BL-204\n")
    monkeypatch.setattr(drift_check, "BACKLOG_FILES", (tmp_path / "nope.md",))
    drift_check.check_backlog_resolution()
    assert fails_of("backlog_resolution")
    assert not passes_of("backlog_resolution")


@pytest.mark.integration
def test_backlog_resolution_live_repo_passes():
    """Against the real corpus at this commit. `integration`: it reads the sibling
    harness repo, so its outcome depends on state a fresh clone does not carry."""
    reset()
    drift_check.check_backlog_resolution()
    assert not fails_of("backlog_resolution"), fails_of("backlog_resolution")
    assert passes_of("backlog_resolution")
