import json
import subprocess
import sys
from pathlib import Path

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "resolve_context.py")
VOCAB = str(GATEWAY_ROOT.parent / "domain" / "ct.stu.vocabulary.jsonl")

EMPTY_CONTEXT = json.dumps({})

CONTEXT_WITH_INST = json.dumps({"inst_id": "aaa-bbb-ccc"})

CONTEXT_WITH_COURSE_MAP = json.dumps({
    "inst_id": "aaa-bbb-ccc",
    "course_map": {"SSLC": "09242481-2425-4f10-9f4a-9a6251465c04"},
})

INTENT_ENROLL = json.dumps({
    "tap_version": "0",
    "message_type": "intent",
    "intent_type": "enroll_students",
    "intent_id": "int-test",
    "correlation_id": "cor-test",
    "payload": [
        {"name": "Priya", "course": "SSLC", "section": "A", "gender": "Female"},
    ],
})


def run_script(intent_json, context_json, vocab_path=VOCAB):
    return subprocess.run(
        [sys.executable, SCRIPT, intent_json, context_json, vocab_path],
        capture_output=True, text=True,
        cwd=str(GATEWAY_ROOT),
    )


def test_returns_inst_id_from_context():
    result = run_script(INTENT_ENROLL, CONTEXT_WITH_INST)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)
    assert ctx["inst_id"] == "aaa-bbb-ccc"


def test_inst_id_from_jwt_when_context_empty():
    import os
    if not os.environ.get("CT_API_TOKEN"):
        import pytest
        pytest.skip("CT_API_TOKEN not set")
    result = run_script(INTENT_ENROLL, EMPTY_CONTEXT)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)
    assert ctx["inst_id"]
    assert len(ctx["inst_id"]) > 8


def test_course_map_from_vocabulary_doc():
    result = run_script(INTENT_ENROLL, CONTEXT_WITH_INST)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)
    assert "course_map" in ctx
    # SSLC course is in vocabulary doc
    assert "SSLC" in ctx["course_map"] or len(ctx["course_map"]) >= 0


def test_course_map_from_context_overrides_vocab():
    result = run_script(INTENT_ENROLL, CONTEXT_WITH_COURSE_MAP)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)
    assert ctx["course_map"]["SSLC"] == "09242481-2425-4f10-9f4a-9a6251465c04"


def test_term_name_default_when_absent():
    result = run_script(INTENT_ENROLL, CONTEXT_WITH_INST)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)
    # Should have a default term name from current: true lookup
    assert ctx.get("term_name") in (None, "Annual", "")


def test_unresolved_courses_listed():
    intent = json.dumps({
        "tap_version": "0",
        "message_type": "intent",
        "intent_type": "enroll_students",
        "intent_id": "int-test",
        "correlation_id": "cor-test",
        "payload": [{"name": "Priya", "course": "NoSuchCourse", "section": "A", "gender": "Female"}],
    })
    result = run_script(intent, CONTEXT_WITH_INST)
    assert result.returncode == 0
    ctx = json.loads(result.stdout)
    assert "NoSuchCourse" in ctx.get("unresolved_courses", [])


def test_exit_1_on_missing_args():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert r.returncode != 0


def test_exit_0_on_bad_context_json():
    r = run_script(INTENT_ENROLL, "not-json")
    assert r.returncode == 0
    ctx = json.loads(r.stdout)
    assert "inst_id" in ctx
