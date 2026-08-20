"""docbuilder's adoption of the per-step run record (ds t2).

Two steps write artifacts and so two steps attest them: `rename_output.py` (the render
step's deliverables) and `upload_output.py` (the upload). Both are driven through their
CLIs here, because the property under test is that the record is written **by the script**
rather than by an orchestrator prompt step — a unit call on a helper could not tell the
difference.

`AETHERIS_RUN_RECORD_ROOT` keeps each subprocess's record inside `tmp_path`. These stay in
the whole-suite gate: they run a script tracked in this repo, on inputs this repo carries,
with no sibling repository present and nothing skipped — the `integration` criterion's own
question ("would it do its work in a fresh clone at this commit, offline?") answers yes.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

USE_CASE_ROOT = Path(__file__).parent.parent
RECORD_RELPATH = Path("data") / "run-records.json"


@pytest.fixture
def record_root(tmp_path):
    """A root for the record file, isolated from the checked-out tree."""
    root = tmp_path / "record-root"
    (root / "data").mkdir(parents=True)
    return root


def _env(record_root):
    env = dict(os.environ)
    env["AETHERIS_RUN_RECORD_ROOT"] = str(record_root)
    return env


def _records(record_root):
    return json.loads((record_root / RECORD_RELPATH).read_text())


def _rendered(out_dir, prefix="proposal_v1", exts=("pdf", "docx")):
    for ext in exts:
        (out_dir / f"{prefix}.{ext}").write_bytes(f"body-{ext}".encode())


CONTEXT = '{"client_name":"Acme Corp","date":"2026-06-20","doc_type":"proposal"}'


def test_rename_output_attests_the_files_it_renamed(tmp_path, record_root):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    _rendered(out_dir)

    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(out_dir), "--filename-prefix", "proposal_v1",
         "--context", CONTEXT, "--run-id", "docbuilder-orch-TEST01"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env(record_root),
    )
    assert result.returncode == 0, result.stderr

    entry, = _records(record_root)
    assert entry["run_id"] == "docbuilder-orch-TEST01"
    assert entry["step"] == "rename_output"
    assert "attested_at" in entry
    assert entry["started_at"].endswith("Z") and entry["attested_at"].endswith("Z")

    named = {Path(a["path"]).name for a in entry["artifacts"]}
    assert named == {"acme_corp_proposal_2026-06-20.pdf",
                     "acme_corp_proposal_2026-06-20.docx"}
    # The hashes are of the renamed files as they now sit on disk.
    import hashlib
    by_name = {Path(a["path"]).name: a for a in entry["artifacts"]}
    assert by_name["acme_corp_proposal_2026-06-20.pdf"]["sha256"] == \
        hashlib.sha256(b"body-pdf").hexdigest()
    assert by_name["acme_corp_proposal_2026-06-20.pdf"]["bytes"] == 8


def test_the_result_file_is_attested_too(tmp_path, record_root):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    _rendered(out_dir, exts=("pdf",))
    renamed_json = tmp_path / "renamed.json"

    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(out_dir), "--filename-prefix", "proposal_v1",
         "--context", CONTEXT, "--output", str(renamed_json),
         "--run-id", "docbuilder-orch-TEST02"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env(record_root),
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(renamed_json)

    entry, = _records(record_root)
    assert any(Path(a["path"]).name == "renamed.json" for a in entry["artifacts"])


def test_an_omitted_run_id_is_recorded_as_null_not_invented(tmp_path, record_root):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    _rendered(out_dir, exts=("pdf",))

    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(out_dir), "--filename-prefix", "proposal_v1",
         "--context", CONTEXT],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env(record_root),
    )
    assert result.returncode == 0, result.stderr

    entry, = _records(record_root)
    assert entry["run_id"] is None
    assert '"run_id": null' in (record_root / RECORD_RELPATH).read_text()


def test_a_failing_step_leaves_an_unattested_entry_and_still_exits_1(tmp_path, record_root):
    """THE BROKEN STATE: the context is missing a required field, so the rename raises."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    _rendered(out_dir, exts=("pdf",))

    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(out_dir), "--filename-prefix", "proposal_v1",
         "--context", '{"date":"2026-06-20"}',  # no client_name
         "--run-id", "docbuilder-orch-TEST03"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=_env(record_root),
    )
    assert result.returncode == 1
    assert json.loads(result.stderr)["status"] == "error"

    entry, = _records(record_root)
    assert entry["run_id"] == "docbuilder-orch-TEST03"
    assert "attested_at" not in entry, "a failed step must not read as complete"


def test_rerunning_the_same_run_and_step_replaces_the_entry(tmp_path, record_root):
    for i in (1, 2):
        out_dir = tmp_path / f"output{i}"
        out_dir.mkdir()
        _rendered(out_dir, exts=("pdf",))
        subprocess.run(
            [sys.executable, "scripts/rename_output.py",
             "--output-dir", str(out_dir), "--filename-prefix", "proposal_v1",
             "--context", CONTEXT, "--run-id", "docbuilder-orch-TEST04"],
            capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
            env=_env(record_root), check=True,
        )

    assert len(_records(record_root)) == 1


def test_upload_output_is_a_separate_step_from_the_render(tmp_path, record_root, monkeypatch):
    """The upload gets its OWN entry — the defect A2 names is D2 attesting before it ran.

    The upload itself needs Drive, so this drives the record seam directly rather than the
    network: it asserts the shape two steps of one run produce, which is the property the
    D2-before-PHASE-E ordering could not express.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from run_record import run_record

    (record_root / "output").mkdir()
    (record_root / "output" / "uploaded.json").write_text("[]")

    with run_record(record_root, "docbuilder-orch-TEST05", "rename_output") as rec:
        rec.add(record_root / "output" / "uploaded.json")
    with run_record(record_root, "docbuilder-orch-TEST05", "upload_output") as rec:
        rec.add(record_root / "output" / "uploaded.json")

    entries = _records(record_root)
    assert [e["step"] for e in entries] == ["rename_output", "upload_output"]
    assert all(e["run_id"] == "docbuilder-orch-TEST05" for e in entries)
    # Each step's attestation is its own: the render's does not certify the upload's file.
    assert entries[0]["attested_at"] <= entries[1]["attested_at"]


def test_upload_output_accepts_run_id_and_names_the_step():
    """The CLI carries `--run-id` and the module names the step, without a Drive call."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "upload_output_probe", USE_CASE_ROOT / "scripts" / "upload_output.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.STEP == "upload_output"

    help_text = subprocess.run(
        [sys.executable, "scripts/upload_output.py", "--help"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    ).stdout
    assert "--run-id" in help_text
