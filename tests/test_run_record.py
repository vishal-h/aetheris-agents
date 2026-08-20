"""Tests for `scripts/run_record.py` — the per-step run/artifact record (ds t2).

Every check here constructs the state in which it fails and asserts the failure, per the
harness `CLAUDE.md` **Silent-wrong-answer** rule: *construct the broken state and watch the
check fail in it, as part of writing the check.* A check whose only observed outcome is a
pass is not yet a check. Where the property is "X is absent", the test also shows X present
in the neighbouring case, so an absence is a result rather than an artefact of looking in
the wrong place.

The seven properties the ticket names, and where each is:

  * attestation absent when a write raises mid-step — `test_a_raising_step_*`
  * idempotent replace on re-run                    — `test_rerunning_*`
  * atomicity                                       — `test_a_truncated_temp_file_*`
  * malformed file raises                           — `test_a_malformed_record_file_*`
  * missing file yields empty                       — `test_a_missing_record_file_*`
  * a null run_id is recorded as null               — `test_a_null_run_id_*`
  * UTC-Z ordering across two offsets               — `test_utc_z_stamps_sort_*`
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_record import (  # noqa: E402
    RECORD_RELPATH,
    RunRecordError,
    describe_artifact,
    load_records,
    record_path,
    run_record,
    upsert,
    utc_now,
    write_records,
)


@pytest.fixture
def root(tmp_path):
    """A use-case root with the `output/` and `data/` directories a producer has."""
    (tmp_path / "output").mkdir()
    (tmp_path / "data").mkdir()
    return tmp_path


def _artifact(root, relpath, content=b"payload"):
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def _records(root):
    return json.loads((root / RECORD_RELPATH).read_text())


# --------------------------------------------------------- attestation carries the meaning


def test_a_completed_step_is_attested_and_names_its_artifacts(root):
    with run_record(root, "run-1", "render") as rec:
        rec.add(_artifact(root, "output/report.html", b"<html>"))

    entry, = _records(root)
    assert entry["run_id"] == "run-1"
    assert entry["step"] == "render"
    assert "attested_at" in entry
    assert entry["started_at"].endswith("Z") and entry["attested_at"].endswith("Z")
    assert entry["artifacts"] == [{
        "path": "output/report.html",
        "sha256": hashlib.sha256(b"<html>").hexdigest(),
        "bytes": 6,
    }]


def test_a_raising_step_leaves_the_entry_unattested_and_reraises(root):
    """THE BROKEN STATE: a write raises mid-step. `attested_at` must be absent."""
    with pytest.raises(RuntimeError, match="disk full"):
        with run_record(root, "run-1", "render") as rec:
            rec.add(_artifact(root, "output/first.html"))
            raise RuntimeError("disk full")

    entry, = _records(root)
    assert "attested_at" not in entry, "an interrupted step must not read as complete"
    assert entry["started_at"].endswith("Z")
    # The entry exists, so an interrupted step is VISIBLE rather than indistinguishable
    # from a step that never ran. It names what it had written when it died.
    assert [a["path"] for a in entry["artifacts"]] == ["output/first.html"]


def test_the_unattested_and_attested_cases_differ_only_in_that_field(root):
    """The neighbouring case: same step, completing. Absence above is a result."""
    with run_record(root, "run-ok", "render") as rec:
        rec.add(_artifact(root, "output/ok.html"))
    with pytest.raises(RuntimeError):
        with run_record(root, "run-bad", "render") as rec:
            rec.add(_artifact(root, "output/bad.html"))
            raise RuntimeError("boom")

    by_run = {e["run_id"]: e for e in _records(root)}
    assert "attested_at" in by_run["run-ok"]
    assert "attested_at" not in by_run["run-bad"]


def test_a_step_that_writes_nothing_is_still_attested(root):
    """Attestation is about the step finishing, not about it producing files."""
    with run_record(root, "run-1", "noop"):
        pass
    entry, = _records(root)
    assert "attested_at" in entry and entry["artifacts"] == []


# ------------------------------------------------------------------- idempotent replace


def test_rerunning_the_same_run_and_step_replaces_rather_than_appends(root):
    for content in (b"v1", b"v2"):
        with run_record(root, "run-1", "render") as rec:
            rec.add(_artifact(root, "output/report.html", content))

    entry, = _records(root)  # THE BROKEN STATE would be two entries here
    assert entry["artifacts"][0]["bytes"] == 2
    assert entry["artifacts"][0]["sha256"] == hashlib.sha256(b"v2").hexdigest()


def test_a_different_step_of_the_same_run_is_a_second_entry(root):
    """The unit is the step: one run legitimately contributes several entries."""
    with run_record(root, "run-1", "render") as rec:
        rec.add(_artifact(root, "output/report.html"))
    with run_record(root, "run-1", "upload") as rec:
        rec.add(_artifact(root, "output/uploaded.json"))

    assert [(e["run_id"], e["step"]) for e in _records(root)] == [
        ("run-1", "render"), ("run-1", "upload")]


def test_the_same_step_of_a_different_run_is_a_second_entry(root):
    with run_record(root, "run-1", "render"):
        pass
    with run_record(root, "run-2", "render"):
        pass
    assert [e["run_id"] for e in _records(root)] == ["run-1", "run-2"]


def test_a_null_run_id_is_not_a_wildcard_when_replacing():
    """`None` matches only `None`. A null-run_id entry must not evict a real one."""
    records = [{"run_id": "run-1", "step": "render", "artifacts": []}]
    out = upsert(records, {"run_id": None, "step": "render", "artifacts": []})
    assert [e["run_id"] for e in out] == ["run-1", None]
    # And replacing the null one leaves the real one alone.
    out2 = upsert(out, {"run_id": None, "step": "render", "artifacts": ["x"]})
    assert [e["run_id"] for e in out2] == ["run-1", None] and len(out2) == 2


# ------------------------------------------------------------------------------ atomicity


def test_a_truncated_temp_file_does_not_destroy_history(root):
    """THE BROKEN STATE: a kill mid-write. A whole-file rewrite loses everything."""
    with run_record(root, "run-1", "render") as rec:
        rec.add(_artifact(root, "output/a.html"))
    before = (root / RECORD_RELPATH).read_text()

    # Simulate the kill: a partially-written temp file left in place, no replace.
    tmp = record_path(root).with_name(record_path(root).name + ".tmp")
    tmp.write_text('[{"run_id": "run-2", "step": "ren')

    assert (root / RECORD_RELPATH).read_text() == before, "history must be intact"
    assert len(load_records(root)) == 1
    # And the next successful write still works, leaving no temp behind.
    with run_record(root, "run-2", "render"):
        pass
    assert len(load_records(root)) == 2
    assert not tmp.exists()


def test_write_records_replaces_atomically_and_leaves_no_temp(root):
    write_records(root, [{"run_id": "a", "step": "s", "artifacts": []}])
    assert not record_path(root).with_name("run-records.json.tmp").exists()
    assert load_records(root)[0]["run_id"] == "a"


# ---------------------------------------------------------------------- the record file


def test_a_missing_record_file_yields_empty(root):
    assert not (root / RECORD_RELPATH).exists()
    assert load_records(root) == []


def test_an_empty_record_file_yields_empty(root):
    (root / RECORD_RELPATH).write_text("   \n")
    assert load_records(root) == []


@pytest.mark.parametrize("body,reason", [
    ("{not json at all", "not valid JSON"),
    ('{"run_id": "r"}', "not a JSON array"),
    ('"a string"', "not a JSON array"),
])
def test_a_malformed_record_file_raises(root, body, reason):
    """THE BROKEN STATE: a corrupt record file. It must never be silently overwritten."""
    (root / RECORD_RELPATH).write_text(body)
    with pytest.raises(RunRecordError, match=reason):
        load_records(root)


def test_best_effort_skips_the_write_and_preserves_a_malformed_file(root, capsys):
    """Both halves of the posture at once: producer not failed, history not overwritten."""
    (root / RECORD_RELPATH).write_text("{corrupt")

    with run_record(root, "run-1", "render") as rec:  # must NOT raise
        rec.add(_artifact(root, "output/a.html"))

    assert (root / RECORD_RELPATH).read_text() == "{corrupt", "must not overwrite"
    warning = json.loads(capsys.readouterr().err.strip().splitlines()[0])
    assert warning["status"] == "warning" and "NOT written" in warning["warning"]


def test_strict_mode_raises_on_a_malformed_file(root):
    """The recording-is-the-job call site. Contrast with the test above."""
    (root / RECORD_RELPATH).write_text("{corrupt")
    with pytest.raises(RunRecordError):
        with run_record(root, "run-1", "render", strict=True):
            pass


# ------------------------------------------------------------------------------- run_id


def test_a_null_run_id_is_recorded_as_null_and_never_invented(root):
    """boxy-pipeline's case: no harness run reaches the script."""
    with run_record(root, None, "extract") as rec:
        rec.add(_artifact(root, "output/plan.json"))

    entry, = _records(root)
    assert entry["run_id"] is None
    # Explicitly present as null rather than omitted, so a reader can tell "no run id"
    # from "this record predates the field".
    assert "run_id" in entry
    assert '"run_id": null' in (root / RECORD_RELPATH).read_text()


# ------------------------------------------------------------------------- UTC-Z ordering


def test_utc_now_is_utc_with_a_z_suffix():
    stamp = utc_now()
    assert stamp.endswith("Z") and "+" not in stamp
    assert len(stamp) == 20  # YYYY-MM-DDTHH:MM:SSZ


def test_utc_z_stamps_sort_chronologically_where_local_offset_stamps_invert():
    """THE BROKEN STATE: the same two instants stamped with local offsets sort backwards.

    Two instants, three hours apart. Under UTC-Z a lexicographic sort — which is what
    `resolve_last_run.find_last_match` performs — is chronological. Under the local-offset
    form `run_log_writer.build_entry` emits, it inverts.
    """
    earlier_utc, later_utc = "2026-06-30T09:00:00Z", "2026-06-30T12:00:00Z"
    assert max(earlier_utc, later_utc) == later_utc

    # The same two instants, stamped the way `datetime.now().astimezone()` would in
    # +05:30 and +00:00 respectively.
    earlier_local, later_local = "2026-06-30T14:30:00+05:30", "2026-06-30T12:00:00+00:00"
    assert max(earlier_local, later_local) == earlier_local, (
        "this is the defect BL-151 records: the string sort picks the EARLIER instant"
    )


# ---------------------------------------------------------------------------- artifacts


def test_artifact_paths_are_relative_to_the_use_case_root(root):
    _artifact(root, "output/r.html", b"body")
    d = describe_artifact(root, root / "output" / "r.html")
    assert d["path"] == "output/r.html" and d["bytes"] == 4


def test_artifacts_outside_output_are_covered(root):
    """BL-153 ruling 2's coverage clause — cloudcost's `history/` tree."""
    _artifact(root, "history/aws/2026-08/aws_costs_2026-08.json", b"{}")
    with run_record(root, "run-1", "compose") as rec:
        rec.add(root / "history/aws/2026-08/aws_costs_2026-08.json")

    entry, = _records(root)
    assert entry["artifacts"][0]["path"] == "history/aws/2026-08/aws_costs_2026-08.json"


def test_a_relative_path_resolves_against_the_root_not_the_cwd(root, monkeypatch, tmp_path):
    """THE BROKEN STATE: cwd elsewhere. A cwd-relative resolve would raise or mis-hash."""
    _artifact(root, "output/r.html", b"abc")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    d = describe_artifact(root, "output/r.html")
    assert d["path"] == "output/r.html" and d["bytes"] == 3


def test_an_artifact_outside_the_root_keeps_its_absolute_path(root, tmp_path):
    """Never a `../..`-prefixed path that reads as though it were inside."""
    outside = tmp_path.parent / "outside.txt"
    outside.write_bytes(b"x")
    d = describe_artifact(root, outside)
    assert Path(d["path"]).is_absolute() and not d["path"].startswith("..")


def test_naming_a_missing_artifact_raises_inside_the_step(root):
    """A path named but never written is an error, and leaves the step unattested."""
    with pytest.raises(FileNotFoundError):
        with run_record(root, "run-1", "render") as rec:
            rec.add(root / "output" / "never-written.html")

    entry, = _records(root)
    assert "attested_at" not in entry


# ---------------------------------------------------------------------------- concurrency


def test_concurrent_writers_do_not_lose_entries(root):
    """THE BROKEN STATE: N processes read-modify-write one file; the last write wins.

    `os.replace` makes the write atomic and does nothing for the read-modify-write around
    it. eduloka spawns one sub-agent per search term and joins them only at
    `wait_for_all`, so this is its live shape, not a hypothetical.

    Real subprocesses rather than `multiprocessing`: each producer genuinely is a separate
    `python3` invocation, and under `--import-mode=importlib` this test module has no
    importable dotted name for `spawn` to pickle a target out of.
    """
    import subprocess

    scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    child = (
        "import sys; sys.path.insert(0, %r)\n"
        "from run_record import run_record\n"
        "with run_record(sys.argv[1], 'run-' + sys.argv[2], 'fetch'):\n"
        "    pass\n" % scripts
    )

    procs = [
        subprocess.Popen([sys.executable, "-c", child, str(root), str(i)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in range(12)
    ]
    for p in procs:
        p.wait(timeout=60)

    assert all(p.returncode == 0 for p in procs), [
        (p.returncode, p.stderr.read().decode()[-300:]) for p in procs if p.returncode
    ]
    got = sorted(e["run_id"] for e in _records(root))
    assert got == sorted(f"run-{i}" for i in range(12)), (
        f"{len(got)} of 12 entries survived — concurrent writers lost entries"
    )
