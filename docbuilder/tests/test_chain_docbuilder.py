"""Tests for chain_docbuilder.py (rig-p9 t3).

`subprocess.run` is mocked — no real `mix aetheris run` / LLM. Pure stdlib;
runs in the standard `-m "not integration"` done-check.
"""

import json
from unittest import mock

import pytest

from chain_docbuilder import _build_env, build_plan, chain


def _mk_agents(tmp_path):
    (tmp_path / "docbuilder" / "agents").mkdir(parents=True)
    (tmp_path / "docbuilder" / "output").mkdir(parents=True)
    return tmp_path


def _proc(returncode=0, stderr=""):
    m = mock.Mock()
    m.returncode = returncode
    m.stderr = stderr
    m.stdout = ""
    return m


# --- _build_env ---

def test_build_env_applies_overrides(monkeypatch):
    monkeypatch.setenv("BASE", "1")
    env = _build_env({"FOO": "bar"})
    assert env["BASE"] == "1"
    assert env["FOO"] == "bar"


def test_build_env_removes_keys(monkeypatch):
    monkeypatch.setenv("DOCBUILDER_CONTEXT", "stale")
    env = _build_env({"DOCBUILDER_CONTEXT_FILE": "/p"}, remove=("DOCBUILDER_CONTEXT",))
    assert "DOCBUILDER_CONTEXT" not in env
    assert env["DOCBUILDER_CONTEXT_FILE"] == "/p"


# --- build_plan (orchestrator protocol shape) ---

def test_build_plan_shape():
    plan = build_plan("bitloka", "the request")
    assert plan["type"] == "plan"
    assert plan["request"] == "the request"
    assert plan["params"]["DOCBUILDER_TENANT"] == "bitloka"
    ids = [s["id"] for s in plan["steps"]]
    agents = [s["agent"] for s in plan["steps"]]
    assert ids == ["context_builder", "orchestrator"]
    # agent paths must match the t2 STEP_CONFIG_HINTS keys
    assert agents == [
        "docbuilder/agents/context_builder.exs",
        "docbuilder/agents/docbuilder_orchestrator.exs",
    ]
    for s in plan["steps"]:
        assert {"id", "description", "agent", "context"} <= set(s)


# --- chain: event emission (protocol) ---

def test_chain_emits_event_sequence_on_success(tmp_path):
    agents = _mk_agents(tmp_path)
    confirmed = agents / "docbuilder" / "output" / "confirmed_context.json"
    events = []

    def side(args, **kw):
        if args[3].endswith("context_builder.exs"):
            confirmed.write_text("{}")
        return _proc()

    with mock.patch("chain_docbuilder.subprocess.run", side_effect=side):
        chain("bitloka", "req", "/aeth", str(agents), on_event=events.append)

    assert [(e["type"], e.get("step_id"), e.get("status")) for e in events] == [
        ("step_started", "context_builder", None),
        ("step_complete", "context_builder", "done"),
        ("step_started", "orchestrator", None),
        ("step_complete", "orchestrator", "done"),
    ]


def test_chain_emits_failed_event_and_skips_orchestrator(tmp_path):
    agents = _mk_agents(tmp_path)
    events = []
    with mock.patch("chain_docbuilder.subprocess.run",
                    return_value=_proc(returncode=1, stderr="boom")):
        chain("bitloka", "req", "/aeth", str(agents), on_event=events.append)
    # context_builder started then failed; orchestrator never started
    assert [(e["type"], e.get("step_id"), e.get("status")) for e in events] == [
        ("step_started", "context_builder", None),
        ("step_complete", "context_builder", "failed"),
    ]


# --- chain: happy path ---

def test_chain_success(tmp_path):
    agents = _mk_agents(tmp_path)
    confirmed = agents / "docbuilder" / "output" / "confirmed_context.json"
    renamed = agents / "docbuilder" / "output" / "renamed.json"

    def side(args, **kw):
        exs = args[3]
        if exs.endswith("context_builder.exs"):
            confirmed.write_text(json.dumps({"client_name": "XYZ Inc", "date": "30-Jun-2026"}))
        elif exs.endswith("docbuilder_orchestrator.exs"):
            renamed.write_text(json.dumps([
                {"original": "output/invoice_v1.pdf", "renamed": "output/xyz_inc_invoice_30-Jun-2026.pdf"},
                {"original": "output/invoice_v1.xlsx", "renamed": "output/xyz_inc_invoice_30-Jun-2026.xlsx"},
            ]))
        return _proc()

    with mock.patch("chain_docbuilder.subprocess.run", side_effect=side) as m:
        summary, code = chain("bitloka", "req", "/aeth", str(agents))

    assert code == 0
    assert summary["status"] == "ok"
    assert summary["context_builder_exit"] == 0
    assert summary["orchestrator_exit"] == 0
    assert summary["outputs"] == [
        "output/xyz_inc_invoice_30-Jun-2026.pdf",
        "output/xyz_inc_invoice_30-Jun-2026.xlsx",
    ]
    assert m.call_count == 2


# --- chain: env + cwd construction ---

def test_step1_env_and_cwd(tmp_path):
    agents = _mk_agents(tmp_path)
    confirmed = agents / "docbuilder" / "output" / "confirmed_context.json"
    calls = []

    def side(args, **kw):
        calls.append((args, kw))
        if args[3].endswith("context_builder.exs"):
            confirmed.write_text("{}")
        return _proc()

    with mock.patch("chain_docbuilder.subprocess.run", side_effect=side):
        chain("bitloka", "the request", "/aeth", str(agents))

    a1, k1 = calls[0]
    assert a1[:3] == ["mix", "aetheris", "run"]
    assert a1[3].endswith("docbuilder/agents/context_builder.exs")
    assert k1["cwd"] == "/aeth"
    assert k1["env"]["DOCBUILDER_TENANT"] == "bitloka"
    assert k1["env"]["DOCBUILDER_REQUEST"] == "the request"


def test_step2_env_removes_docbuilder_context(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCBUILDER_CONTEXT", "stale-value")
    agents = _mk_agents(tmp_path)
    confirmed = agents / "docbuilder" / "output" / "confirmed_context.json"
    calls = []

    def side(args, **kw):
        calls.append((args, kw))
        if args[3].endswith("context_builder.exs"):
            confirmed.write_text("{}")
        return _proc()

    with mock.patch("chain_docbuilder.subprocess.run", side_effect=side):
        chain("bitloka", "req", "/aeth", str(agents))

    a2, k2 = calls[1]
    assert a2[3].endswith("docbuilder/agents/docbuilder_orchestrator.exs")
    assert "DOCBUILDER_CONTEXT" not in k2["env"]                 # shadow removed
    assert k2["env"]["DOCBUILDER_CONTEXT_FILE"].endswith("confirmed_context.json")
    assert k2["env"]["DOCBUILDER_TENANT"] == "bitloka"


# --- chain: failure paths (each stops before the next step) ---

def test_context_builder_failure_no_step2(tmp_path):
    agents = _mk_agents(tmp_path)
    with mock.patch("chain_docbuilder.subprocess.run",
                    return_value=_proc(returncode=1, stderr="boom")) as m:
        summary, code = chain("bitloka", "req", "/aeth", str(agents))
    assert code == 1
    assert summary["status"] == "error"
    assert summary["context_builder_exit"] == 1
    assert "boom" in summary["stderr_tail"]
    assert m.call_count == 1


def test_confirmed_context_missing_no_step2(tmp_path):
    agents = _mk_agents(tmp_path)
    # subprocess "succeeds" but never writes confirmed_context.json
    with mock.patch("chain_docbuilder.subprocess.run", return_value=_proc()) as m:
        summary, code = chain("bitloka", "req", "/aeth", str(agents))
    assert code == 1
    assert "confirmed_context.json" in summary["error"]
    assert m.call_count == 1


def test_confirmed_context_invalid_json_no_step2(tmp_path):
    agents = _mk_agents(tmp_path)
    confirmed = agents / "docbuilder" / "output" / "confirmed_context.json"

    def side(args, **kw):
        if args[3].endswith("context_builder.exs"):
            confirmed.write_text("{not json")
        return _proc()

    with mock.patch("chain_docbuilder.subprocess.run", side_effect=side) as m:
        summary, code = chain("bitloka", "req", "/aeth", str(agents))
    assert code == 1
    assert "not valid JSON" in summary["error"]
    assert m.call_count == 1


def test_orchestrator_failure(tmp_path):
    agents = _mk_agents(tmp_path)
    confirmed = agents / "docbuilder" / "output" / "confirmed_context.json"

    def side(args, **kw):
        if args[3].endswith("context_builder.exs"):
            confirmed.write_text("{}")
            return _proc()
        return _proc(returncode=2, stderr="render failed")

    with mock.patch("chain_docbuilder.subprocess.run", side_effect=side) as m:
        summary, code = chain("bitloka", "req", "/aeth", str(agents))
    assert code == 1
    assert summary["status"] == "error"
    assert summary["orchestrator_exit"] == 2
    assert "render failed" in summary["stderr_tail"]
    assert m.call_count == 2
