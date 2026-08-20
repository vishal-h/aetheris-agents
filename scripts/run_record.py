"""The run/artifact record — one entry per producing STEP (ds t2).

Every use case that writes durable artifacts keeps a record at
`<use_case>/data/run-records.json`: a JSON array in which each entry names one
*step* of one run and enumerates the artifacts that step wrote.

**The attestable unit is the step, not the directory.** BL-153's first ruling spoke of
"an unstamped or mismatched DIRECTORY"; its second requires coverage of an accumulating
tree no guard clears (cloudcost's `history/`, written at an earlier step into a directory
the sprint's guard never touches). A directory-level stamp cannot express the second, so
the record enumerates artifacts and attests the step that wrote them:

    an artifact not named in an attested step record is not that step's output.

**`attested_at` carries the meaning.** It is written only after every artifact write for
that step has returned. An entry with `started_at` and no `attested_at` is a step that
began and did not finish — which is the state BL-153's ruling 1 asks for, an interrupted
unit reading as UNSTAMPED rather than as stamped-and-partial. The entry is written when
the step opens precisely so that an interrupted step is *visible*: no entry at all cannot
be told apart from a step that never ran.

**The writer is code, never a prompt line.** A stamp a reader may ignore and a stamp a
writer may skip are the same defect one step apart, so recording is a context manager
wrapped around the writes rather than an extra step an orchestrator prompt asks for. See
`docs/milestones/ds-t2-implementation-notes.md`.

Location: this module is repo-root `scripts/` rather than any one use case's, following
`scripts/_manifest.py` — the in-repo precedent for a shared module with several consumers.
No use case may import another's `scripts/`, and a module owned by one producer and
imported by five would invert that. Use-case scripts reach it with the two-line bootstrap
in `run_record_bootstrap()`'s docstring.

Timestamps are UTC with a `Z` suffix, and that is not cosmetic: entries are compared and
sorted as strings by their readers, so a local-offset stamp sorts by printed digits rather
than by instant. `docbuilder/scripts/resolve_last_run.py` already does exactly that over
`datetime.now().astimezone().isoformat()` (BL-151, filed by this ticket).

Atomicity: writes go to a temp file in the same directory and are then `os.replace`d, so a
kill mid-write leaves the previous record intact rather than truncating the whole history.
`cloudcost/scripts/render_report.py:380-382` is the in-repo precedent.

Failure posture, both halves preserved from `docbuilder/scripts/run_log_writer.py`:

  * Recording is **best-effort at the point of write** and must never fail a producer.
  * A **malformed** existing record file is never silently overwritten.

Those two only look opposed. In best-effort mode a malformed file makes the write *skip*
with a loud stderr warning — history is preserved and the producer is not failed. Under
`strict=True` — for a call site whose only job is the recording — it raises.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

#: The record file's name, relative to a use-case root. Deliberately under `data/` and
#: never under `output/`: payslip's `output/runs.log` sits inside the tree
#: `../aetheris/scripts/sprint.sh:1006` `rm -rf`s, so it dies with the artifacts it
#: attests. `docbuilder/data/run_log.json` is the placement precedent.
RECORD_RELPATH = Path("data") / "run-records.json"

#: Read in chunks so a large artifact does not have to fit in memory.
_HASH_CHUNK = 1 << 20


class RunRecordError(ValueError):
    """A history file exists and is not a JSON array of entries.

    Subclasses `ValueError` deliberately. `run_log_writer.main` and `resolve_last_run.main`
    both catch `(json.JSONDecodeError, ValueError)` around the loader and exit 1 with a
    message; `json.JSONDecodeError` is itself a `ValueError`. Raising this type means both
    CLIs keep their existing behaviour with no change to their `except` clauses — the
    generalisation moves the loader without moving the contract.
    """


def utc_now() -> str:
    """Current instant as ISO-8601 UTC with a `Z` suffix, seconds resolution.

    `Z` rather than an offset so that a lexicographic sort over these strings is a
    chronological sort. See this module's docstring.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_path(use_case_root) -> Path:
    """Absolute path to a use case's record file."""
    return Path(use_case_root).resolve() / RECORD_RELPATH


#: Test seam. When set, records are written under this root instead of the use case's.
#: Deliberately an environment variable read in ONE function, and deliberately **not** a
#: CLI flag: cloudcost's `history/` tree carries two incompatible layouts today precisely
#: because `--history-dir` is an optional flag whose default differs from what the
#: orchestrator passes, so the same script writes `history/{provider}/{period}/` under the
#: orchestrator and `history/{period}/` under the Tools panel (BL-151, filed by ds t2). An
#: env var cannot be half-set in an argv array, and one reader means one layout.
RUN_RECORD_ROOT_ENV = "AETHERIS_RUN_RECORD_ROOT"


def use_case_root_for(script_file) -> Path:
    """The use-case root, given a `__file__` inside that use case's `scripts/`.

    Never `Path.cwd()`: a producer is invoked from the use-case root by `run_command` but
    from anywhere by a test, an operator or Rig's Tools panel, and a cwd-derived root
    silently writes the record somewhere else. Same reason the agent files use
    `__ENV__.file` rather than `File.cwd!()`.

    `AETHERIS_RUN_RECORD_ROOT` overrides it, so a subprocess test can keep its records in
    `tmp_path` rather than in the checked-out tree.
    """
    override = os.environ.get(RUN_RECORD_ROOT_ENV)
    if override:
        return Path(override).resolve()
    return Path(script_file).resolve().parents[1]


def sha256_file(path) -> str:
    """Hex SHA-256 of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_HASH_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_artifact(use_case_root, path) -> dict:
    """Return `{path, sha256, bytes}` for one artifact.

    `path` is relative to the use-case root — including for artifacts *outside*
    `output/`, which is BL-153 ruling 2's coverage clause: cloudcost's `history/` tree is
    written at an earlier step into a directory the sprint's guard never clears, and a
    record scoped to the guarded directory would certify a subset while reading as
    certifying the run.
    """
    root = Path(use_case_root).resolve()
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    p = p.resolve()
    try:
        rel = p.relative_to(root)
    except ValueError:
        # Outside the use-case root: keep the absolute path rather than emitting a
        # `../..`-prefixed relative one that reads as though it were inside.
        rel = p
    return {"path": str(rel), "sha256": sha256_file(p), "bytes": p.stat().st_size}


def load_json_array(path) -> list:
    """Load a JSON-array history file. Missing or empty → `[]`; anything else raises.

    The primitive `load_records` and `docbuilder/scripts/run_log_writer._load_log` both
    sit on, so the two record files share one loader and one definition of "malformed"
    rather than two that can drift. `resolve_last_run.py` already imports the docbuilder
    loader, so this extends an existing coupling rather than creating one.
    """
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RunRecordError(f"'{p}' is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise RunRecordError(f"'{p}' is not a JSON array")
    return data


def write_json_array(path, data: list) -> Path:
    """Write a JSON array atomically: temp file beside it, then `os.replace`.

    The primitive `write_records` and `run_log_writer` both sit on. A whole-file
    `write_text` truncates the entire history when killed mid-write rather than losing one
    entry; `cloudcost/scripts/render_report.py:380-382` is the in-repo precedent for doing
    it this way.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, p)
    return p


def load_records(use_case_root) -> list:
    """Load a use case's records. Missing or empty file → `[]`.

    Raises `RunRecordError` if the file exists and is not a JSON array, so run history is
    never silently overwritten. This mirrors `run_log_writer._load_log`'s posture.
    """
    return load_json_array(record_path(use_case_root))


def upsert(records: list, entry: dict) -> list:
    """Replace any entry with the same `(run_id, step)`, else append. Returns a new list.

    Idempotent by `(run_id, step)` rather than by `run_id` alone, because the unit is the
    step: one run legitimately contributes several entries. This generalises
    `run_log_writer.append_run`'s replace-by-`run_id`, which is the same rule for a
    producer that had only one step.

    A `None` `run_id` matches only another `None` `run_id` — it is a real value meaning
    "no harness run reached this script", never a wildcard.
    """
    key = (entry.get("run_id"), entry.get("step"))
    return [e for e in records if (e.get("run_id"), e.get("step")) != key] + [entry]


def write_records(use_case_root, records: list) -> Path:
    """Write a use case's record list atomically. See `write_json_array`."""
    return write_json_array(record_path(use_case_root), records)


def _warn(message: str) -> None:
    print(json.dumps({"status": "warning", "warning": message}), file=sys.stderr)


@contextmanager
def _exclusive(use_case_root):
    """Hold an exclusive lock for the duration of one read-modify-write.

    `os.replace` makes the *write* atomic; it does nothing for the read-modify-write around
    it. eduloka's orchestrator spawns **one sub-agent per search term** and joins them only
    at `wait_for_all` (`eduloka/agents/eduloka_orchestrator.exs:53, :105-106`), so without
    this every concurrent term reads the same array and the last writer silently drops the
    others' entries — a record that under-reports exactly when the most work happened.

    The lock is a sidecar rather than the record file itself: the record's inode is
    replaced on every write, so a lock held on it would not be held on its successor.
    """
    lock = record_path(use_case_root).with_name(
        record_path(use_case_root).name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _save(use_case_root, entry: dict, *, strict: bool) -> None:
    """Upsert one entry and write it out, honouring the failure posture.

    Best-effort (`strict=False`): any recording failure warns on stderr and returns. A
    malformed existing file **skips the write** rather than overwriting it — history is
    preserved and the producer is not failed, which is both halves of the posture at once.
    """
    try:
        with _exclusive(use_case_root):
            records = upsert(load_records(use_case_root), entry)
            write_records(use_case_root, records)
    except RunRecordError as exc:
        if strict:
            raise
        _warn(f"{exc}; run record NOT written and existing history left untouched")
    except OSError as exc:
        if strict:
            raise
        _warn(f"could not write run record: {exc}")


class StepRecord:
    """One step's in-progress record. Obtained from `run_record()`; not built directly."""

    def __init__(self, use_case_root, run_id, step, *, strict: bool):
        self.use_case_root = Path(use_case_root).resolve()
        self.run_id = run_id
        self.step = step
        self.started_at = utc_now()
        self.strict = strict
        self._artifacts: list = []

    def add(self, *paths) -> None:
        """Name artifacts this step has *already finished writing*, and persist.

        Call after each write returns, never before: the hash and size are read from disk
        here, so naming a path before its write completes records a partial file.

        Each call rewrites the (still unattested) entry, so a step that dies mid-way
        leaves a record naming the artifacts that *did* land. Accumulating in memory and
        writing once at the end would leave every interrupted step with an empty artifact
        list — an unattested entry that says nothing, which is most of the value of having
        written it at all.
        """
        for path in paths:
            self._artifacts.append(describe_artifact(self.use_case_root, path))
        self.open()

    def _entry(self, *, attested: bool) -> dict:
        entry = {
            "run_id": self.run_id,
            "step": self.step,
            "started_at": self.started_at,
        }
        if attested:
            entry["attested_at"] = utc_now()
        entry["artifacts"] = list(self._artifacts)
        return entry

    def open(self) -> None:
        """Write the unattested entry, so an interrupted step is visible."""
        _save(self.use_case_root, self._entry(attested=False), strict=self.strict)

    def attest(self) -> None:
        """Write the entry with `attested_at`. Called only after every write returned."""
        _save(self.use_case_root, self._entry(attested=True), strict=self.strict)


@contextmanager
def run_record(use_case_root, run_id, step, *, strict: bool = False):
    """Record one producing step.

        with run_record(ROOT, run_id, "render_report") as rec:
            path = render(...)
            rec.add(path)

    On clean exit the entry gains `attested_at`. If the body raises, the entry is left
    **unattested** and the exception propagates unchanged — the producer's failure is the
    producer's, and the record states that the step did not finish.

    `run_id` is the harness run id where one reaches the script and `None` where none
    does; never a fabricated substitute. `strict=True` makes recording failures fatal, for
    a call site whose only job is the recording.
    """
    rec = StepRecord(use_case_root, run_id, step, strict=strict)
    rec.open()
    yield rec
    rec.attest()


def run_record_bootstrap() -> None:
    """Documentation-only: how a use-case script imports this module.

    Use-case scripts run with the use-case root as cwd (`run_command` invokes
    `python3 scripts/<name>.py`), so `sys.path[0]` is `<use_case>/scripts` and repo-root
    `scripts/` is not reachable. Each of the six producers is one level below the repo
    root, so two lines suffice:

        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
        from run_record import run_record  # noqa: E402
    """
