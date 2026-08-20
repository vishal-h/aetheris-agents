"""Every producer adopts the run record, and each adoption says what verifies it (ds t2).

One file rather than five, because the property is a **census over the producer set**: that
each of the six producers records, that no other use case pretends to, and that the six are
the six the registry plus the producer criterion yield. Split per use case, the census
clause — the one that catches a seventh producer landing unrecorded — would have no home.

**How the six are derived, since `docs/use-cases.md` alone does not yield them.** The
registry has TEN rows and carries no producer column; its membership criterion
(`D/tests/conftest.py` + `D/scripts/`) is about separately-testable code. The registry
supplies the population and this criterion supplies the subset:

    a producer writes a durable local artifact that a later reader inspects
    to establish what a run produced.

`api/gateway` and `api/tenant` write no local files at all. `drive` and `email` write only
*inbound* fetches (`drive_download.py`, `email_download_template.py` pull a remote file into
`data/`) — input-fetchers, not producers. The remaining six are the producers. Both halves
are asserted below, so the set cannot drift silently in either direction.

**What each adoption is verified by** is the second thing this file records, because the
six are not equally exercised and a uniform-looking test file would imply they were:

| use case | verified by |
|---|---|
| `docbuilder` | its own CLI subprocess tests — `docbuilder/tests/test_run_record_adoption.py` |
| `cloudcost`  | its own suite drives both instrumented stages; asserted here structurally |
| `payslip`    | its suite drives the generator loop; asserted here structurally |
| `eduloka`    | structural only — its stages need a live search provider |
| `provenance` | structural only — its report stage needs a populated DuckDB |
| `boxy-pipeline` | **dormant**; `boxy-pipeline/tests/test_run_record_adoption.py`, deselected from the gate |
"""

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_record import RECORD_RELPATH, run_record  # noqa: E402

#: The producer set, and the ONE script in each that this ticket instrumented. A second
#: instrumented script in a use case is fine; this names the one whose absence would mean
#: the adoption had been reverted.
PRODUCERS = {
    "boxy-pipeline": ["scripts/order_formatter.py"],
    "cloudcost": ["scripts/compose_report_data.py", "scripts/render_report.py"],
    "docbuilder": ["scripts/rename_output.py", "scripts/upload_output.py"],
    "eduloka": ["scripts/fetch.py", "scripts/map.py", "scripts/enrich.py"],
    "payslip": ["scripts/generate_employee_payslips.py"],
    "provenance": ["scripts/inventory_report.py"],
}

#: Registry rows that are NOT producers, with the reason. Asserted so the negative half of
#: the census is a claim rather than an omission.
NON_PRODUCERS = {
    "api/gateway": "writes no local file",
    "api/tenant": "writes no local file",
    "drive": "fetches a remote file inbound; produces nothing of its own",
    "email": "fetches a remote file inbound; produces nothing of its own",
}


def _registry_rows():
    """The registry's own reproducing command, run here rather than quoted."""
    import subprocess

    out = subprocess.run(
        ["git", "ls-files", "*/tests/conftest.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    rows = {p[: -len("/tests/conftest.py")] for p in out}
    return rows - {"tests"}


def test_the_producer_set_partitions_the_registry():
    """Producers and non-producers together are exactly the registry, with no leftovers."""
    rows = _registry_rows()
    claimed = set(PRODUCERS) | set(NON_PRODUCERS)
    assert claimed == rows, (
        f"registry moved: only-in-registry={sorted(rows - claimed)}, "
        f"only-in-this-file={sorted(claimed - rows)} — a new use case must be classified "
        f"as producer or not, and instrumented if it is"
    )
    assert not (set(PRODUCERS) & set(NON_PRODUCERS))


@pytest.mark.parametrize("use_case,scripts", sorted(PRODUCERS.items()))
def test_every_producer_script_imports_the_shared_record(use_case, scripts):
    """Parsed, not grepped: a mention inside a docstring is not an import."""
    for rel in scripts:
        path = REPO_ROOT / use_case / rel
        assert path.is_file(), path
        tree = ast.parse(path.read_text())
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "run_record"
            for alias in node.names
        }
        assert "run_record" in imported, f"{use_case}/{rel} does not import run_record"


@pytest.mark.parametrize("use_case,scripts", sorted(PRODUCERS.items()))
def test_every_producer_script_actually_opens_a_record(use_case, scripts):
    """THE BROKEN STATE an import alone would pass: imported and never called."""
    for rel in scripts:
        tree = ast.parse((REPO_ROOT / use_case / rel).read_text())
        called = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "run_record"
            for node in ast.walk(tree)
        )
        assert called, f"{use_case}/{rel} imports run_record but never calls it"


@pytest.mark.parametrize("use_case,scripts", sorted(PRODUCERS.items()))
def test_every_producer_script_accepts_a_run_id(use_case, scripts):
    """`--run-id` is the seam; where no run reaches the script it stays None, not invented."""
    for rel in scripts:
        source = (REPO_ROOT / use_case / rel).read_text()
        assert '"--run-id"' in source, f"{use_case}/{rel} has no --run-id flag"


@pytest.mark.parametrize("use_case,reason", sorted(NON_PRODUCERS.items()))
def test_non_producers_do_not_record(use_case, reason):
    """The negative half of the census, with a positive control on the same search."""
    scripts = sorted((REPO_ROOT / use_case / "scripts").glob("*.py"))
    assert scripts, f"{use_case} has no scripts — the search would be vacuous"
    hits = [p.name for p in scripts if "run_record" in p.read_text()]
    assert hits == [], f"{use_case} ({reason}) unexpectedly records: {hits}"

    # Positive control: the identical search over a producer returns non-empty, so the
    # zero above is a fact about these files rather than about the search.
    control = [
        p.name for p in (REPO_ROOT / "docbuilder" / "scripts").glob("*.py")
        if "run_record" in p.read_text()
    ]
    assert control, "positive control found nothing — the search is broken, not the result"


@pytest.mark.parametrize("use_case", sorted(PRODUCERS))
def test_every_producer_gitignores_its_record(use_case):
    """The record names artifacts and their hashes; it is ignored like the artifacts."""
    import subprocess

    for name in ("run-records.json", "run-records.json.lock"):
        rc = subprocess.run(
            ["git", "check-ignore", "-q", f"{use_case}/{RECORD_RELPATH.parent}/{name}"],
            cwd=REPO_ROOT,
        ).returncode
        assert rc == 0, f"{use_case}/data/{name} is not gitignored"


def test_the_record_relpath_is_outside_output(tmp_path):
    """Never under `output/`: payslip's `output/runs.log` dies with the tree the sprint
    `rm -rf`s (`../aetheris/scripts/sprint.sh:1006`), taking the attestation with it."""
    assert RECORD_RELPATH.parts[0] == "data"
    assert "output" not in RECORD_RELPATH.parts

    (tmp_path / "data").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "a.txt").write_bytes(b"x")
    with run_record(tmp_path, "r", "s") as rec:
        rec.add(tmp_path / "output" / "a.txt")

    import shutil
    shutil.rmtree(tmp_path / "output")          # what the sprint's guard does
    assert (tmp_path / RECORD_RELPATH).is_file(), "the record must survive the guard"
