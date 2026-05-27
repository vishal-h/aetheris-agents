import json
import subprocess
import sys
from pathlib import Path

import pytest

TENANT_ROOT = Path(__file__).parent.parent
SCRIPT = str(TENANT_ROOT / "scripts" / "extract_skill_hints.py")

INTENT_JSON = json.dumps({
    "tap_version": "0",
    "message_type": "intent",
    "intent_id": "int-test-001",
    "correlation_id": "cor-test-001",
    "seq": 1,
    "depends_on": [],
    "intent_type": "enroll_students",
    "user_intent": "Enroll students from CSV",
    "payload": [
        {"name": "Priya Agent", "date_of_birth": "2010-06-15", "gender": "Female",
         "course": "SSLC", "section": "A"},
        {"name": "Ravi Agent", "date_of_birth": None, "gender": "Male",
         "course": "SSLC", "section": "B"},
    ],
    "flags": [{"record": "Ravi Agent", "reason": "dob absent from source"}],
    "provenance": {"source_file": "tenant/data/sample.csv", "record_count": 2, "batch": 1, "of": 1},
})

SAMPLE_EVENTS = [
    {"id": "e1", "run_id": "uc-api-t2-TEST-cot1", "step": 0, "seq": 0,
     "type": "prompt_built", "payload": {"context_hash": "abc", "message_count": 1},
     "timestamp": "2026-01-01T00:00:00Z"},
    {"id": "e2", "run_id": "uc-api-t2-TEST-cot1", "step": 0, "seq": 1,
     "type": "tool_called", "payload": {"tool_name": "wait_for_event",
                                         "tool_input": {"condition": "message_received", "timeout_ms": 120000}},
     "timestamp": "2026-01-01T00:00:01Z"},
    {"id": "e3", "run_id": "uc-api-t2-TEST-cot1", "step": 1, "seq": 2,
     "type": "tool_called", "payload": {"tool_name": "read_blackboard",
                                         "tool_input": {"key": "tap:intent:int-test-001"}},
     "timestamp": "2026-01-01T00:00:02Z"},
    {"id": "e4", "run_id": "uc-api-t2-TEST-cot1", "step": 2, "seq": 3,
     "type": "tool_called", "payload": {"tool_name": "run_command",
                                         "tool_input": {"command": "python3",
                                                         "args": ["gateway/scripts/validate_intent.py",
                                                                  INTENT_JSON,
                                                                  "domain/ct.stu.vocabulary.jsonl"]}},
     "timestamp": "2026-01-01T00:00:03Z"},
    {"id": "e5", "run_id": "uc-api-t2-TEST-cot1", "step": 3, "seq": 4,
     "type": "tool_called", "payload": {"tool_name": "run_command",
                                         "tool_input": {"command": "python3",
                                                         "args": ["gateway/scripts/resolve_context.py",
                                                                  INTENT_JSON, "{}"]}},
     "timestamp": "2026-01-01T00:00:04Z"},
    {"id": "e6", "run_id": "uc-api-t2-TEST-cot1", "step": 4, "seq": 5,
     "type": "tool_called", "payload": {"tool_name": "run_command",
                                         "tool_input": {"command": "python3",
                                                         "args": ["gateway/scripts/build_etl_job.py",
                                                                  INTENT_JSON, "{}"]}},
     "timestamp": "2026-01-01T00:00:05Z"},
    {"id": "e7", "run_id": "uc-api-t2-TEST-cot1", "step": 5, "seq": 6,
     "type": "tool_called", "payload": {"tool_name": "write_blackboard",
                                         "tool_input": {"key": "tap:result:int-test-001", "value": "{}"}},
     "timestamp": "2026-01-01T00:00:06Z"},
    {"id": "e8", "run_id": "uc-api-t2-TEST-cot1", "step": 5, "seq": 7,
     "type": "run_complete", "payload": {"reason": "agent_finished"},
     "timestamp": "2026-01-01T00:00:07Z"},
]


def run_script(trajectory_path: str):
    return subprocess.run(
        [sys.executable, SCRIPT, trajectory_path],
        capture_output=True, text=True, cwd=str(TENANT_ROOT)
    )


@pytest.fixture
def trajectory_file(tmp_path):
    path = tmp_path / "trajectory.json"
    path.write_text(json.dumps(SAMPLE_EVENTS))
    return str(path)


@pytest.fixture
def full_trajectory_file(tmp_path):
    """Full trajectory format (schema_version + events wrapper)."""
    path = tmp_path / "full_trajectory.json"
    path.write_text(json.dumps({
        "schema_version": "1",
        "run_id": "uc-api-t2-TEST-cot1",
        "meta": {},
        "events": SAMPLE_EVENTS,
    }))
    return str(path)


def test_exits_zero(trajectory_file):
    result = run_script(trajectory_file)
    assert result.returncode == 0


def test_output_is_valid_json(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_intent_type_extracted(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert data["intent_type"] == "enroll_students"


def test_tool_sequence_extracted(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    seq = data["tool_sequence"]
    assert "wait_for_event" in seq
    assert "read_blackboard" in seq
    assert "run_command" in seq
    assert "write_blackboard" in seq


def test_tool_sequence_ordered(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    seq = data["tool_sequence"]
    assert seq[0] == "wait_for_event"
    assert seq[1] == "read_blackboard"


def test_scripts_extracted(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    scripts = data["scripts"]
    assert "gateway/scripts/validate_intent.py" in scripts
    assert "gateway/scripts/resolve_context.py" in scripts
    assert "gateway/scripts/build_etl_job.py" in scripts


def test_scripts_deduplicated(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert len(data["scripts"]) == len(set(data["scripts"]))


def test_flags_extracted(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert "dob absent from source" in data["flags"]


def test_record_count_extracted(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert data["record_count"] == 2


def test_step_count(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert data["step_count"] == 6


def test_extracted_from_run(trajectory_file):
    result = run_script(trajectory_file)
    data = json.loads(result.stdout)
    assert data["extracted_from_run"] == "uc-api-t2-TEST-cot1"


def test_full_trajectory_format_supported(full_trajectory_file):
    """Script handles full trajectory dict (schema_version + events wrapper)."""
    result = run_script(full_trajectory_file)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["intent_type"] == "enroll_students"


def test_missing_file_exits_nonzero():
    result = run_script("/nonexistent/path.json")
    assert result.returncode != 0


def test_no_args_exits_nonzero():
    result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert result.returncode != 0


def test_invalid_json_exits_nonzero(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    result = run_script(str(bad))
    assert result.returncode != 0


def test_empty_events_returns_nones(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("[]")
    result = run_script(str(empty))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["intent_type"] is None
    assert data["tool_sequence"] == []
    assert data["flags"] == []
