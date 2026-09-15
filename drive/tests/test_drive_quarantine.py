"""BL-194: quarantine of misplaced payslip objects, against an in-memory Drive."""
import json
import re

import pytest

import drive.scripts.drive_download as drive_download
from drive.scripts.drive_quarantine import (
    QUARANTINE_FOLDER,
    READONLY_SCOPE,
    WRITE_SCOPE,
    classify,
    main,
)

FOLDER = "application/vnd.google-apps.folder"


class _Request:
    def __init__(self, run):
        self._run = run

    def execute(self):
        return self._run()


class FakeDrive:
    """Folders and files keyed by id; records every call; has no delete."""

    def __init__(self):
        self.nodes = {}
        self.calls = []

    def add(self, node_id, name, parent=None, folder=False):
        self.nodes[node_id] = {
            "name": name,
            "mimeType": FOLDER if folder else "application/pdf",
            "parents": [parent] if parent else [],
        }
        return node_id

    def files(self):
        return _Files(self)

    def called(self, kind):
        return [c for c in self.calls if c[0] == kind]

    def ancestors(self, node_id):
        chain, parents = [], self.nodes[node_id]["parents"]
        while parents:
            chain.append(parents[0])
            parents = self.nodes[parents[0]]["parents"]
        return chain


class _Files:
    def __init__(self, drive):
        self.drive = drive

    def list(self, q, **_kwargs):
        self.drive.calls.append(("list", q))
        parent = re.search(r"'([^']+)' in parents", q).group(1)
        name = re.search(r"name = '([^']+)'", q)
        mime = re.search(r"mimeType = '([^']+)'", q)

        def run():
            return {"files": [
                {"id": i, "name": n["name"], "mimeType": n["mimeType"]}
                for i, n in sorted(self.drive.nodes.items())
                if parent in n["parents"]
                and (name is None or n["name"] == name.group(1))
                and (mime is None or n["mimeType"] == mime.group(1))
            ]}
        return _Request(run)

    def get(self, fileId, **_kwargs):
        self.drive.calls.append(("get", fileId))
        return _Request(lambda: {"id": fileId, **self.drive.nodes[fileId]})

    def create(self, body, **_kwargs):
        self.drive.calls.append(("create", body["name"]))

        def run():
            new_id = f"created-{len(self.drive.nodes)}"
            self.drive.nodes[new_id] = {
                "name": body["name"], "mimeType": body.get("mimeType", ""), "parents": list(body["parents"]),
            }
            return {"id": new_id}
        return _Request(run)

    def update(self, fileId, addParents, removeParents, **_kwargs):
        self.drive.calls.append(("update", fileId))

        def run():
            node = self.drive.nodes[fileId]
            node["parents"] = [p for p in node["parents"] if p != removeParents] + [addParents]
            return {"id": fileId, "parents": node["parents"]}
        return _Request(run)


@pytest.fixture
def drive(monkeypatch):
    d = FakeDrive()
    d.add("shared", "Shared drive")
    d.add("root", "payslips", "shared", folder=True)
    d.add("p05", "2026-05", "root", folder=True)
    d.add("p07", "2026-07", "root", folder=True)
    d.add("payroll", "payroll.csv", "p07")
    for emp in ("BTL_01", "BTL_02"):
        d.add(f"{emp}-07", emp, "p07", folder=True)
        for month in ("2026-05", "2026-07"):
            for ext in ("pdf", "csv"):
                d.add(f"{emp}-{month}-{ext}", f"{month}-Payslip.{ext}", f"{emp}-07")
    d.add("BTL_01-05", "BTL_01", "p05", folder=True)
    d.add("may-in-may", "2026-05-Payslip.pdf", "BTL_01-05")

    d.scopes = []

    def build_service(scopes=None):
        d.scopes.append(scopes)
        return d

    monkeypatch.setattr(drive_download, "build_service", build_service)
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root")
    return d


MISPLACED = [
    "2026-07/BTL_01/2026-05-Payslip.csv", "2026-07/BTL_01/2026-05-Payslip.pdf",
    "2026-07/BTL_02/2026-05-Payslip.csv", "2026-07/BTL_02/2026-05-Payslip.pdf",
]


def test_identity_test_compares_month_prefix_to_period_folder():
    assert classify("2026-05-Payslip.pdf", "2026-07") == "misplaced"
    assert classify("2026-07-Payslip.csv", "2026-07") == "clean"
    assert classify("payroll.csv", "2026-07") == "unclassifiable"


def test_dry_run_reports_every_misplaced_pair_and_moves_nothing(drive, tmp_path, capsys):
    report_path = tmp_path / "report.json"

    assert main(["--period", "2026-07", "--report", str(report_path)]) == 0

    report = json.loads(report_path.read_text())
    assert report["mode"] == "dry-run"
    assert [p["source"] for p in report["pairs"]] == MISPLACED
    assert [p["quarantine"] for p in report["pairs"]] == [
        s.replace("2026-07/", f"{QUARANTINE_FOLDER}/2026-07/", 1) for s in MISPLACED
    ]
    assert report["counts"] == {"objects": 9, "clean": 4, "misplaced": 4, "unclassifiable": 1}
    assert report["unclassifiable"] == [{"source": "2026-07/payroll.csv", "mimeType": "application/pdf"}]
    assert report["quarantine_parent_id"] == "shared"
    assert drive.scopes == [READONLY_SCOPE]
    assert drive.called("create") == [] and drive.called("update") == []
    assert json.loads(capsys.readouterr().out)["misplaced"] == 4


def test_dry_run_never_overwrites_a_report(drive, tmp_path, capsys):
    report_path = tmp_path / "report.json"
    report_path.write_text("reviewed")

    assert main(["--period", "2026-07", "--report", str(report_path)]) == 1
    assert report_path.read_text() == "reviewed"
    assert "never overwritten" in capsys.readouterr().err


def test_dry_run_rejects_a_malformed_period_before_touching_drive(drive, tmp_path, capsys):
    assert main(["--period", "2026-7", "--report", str(tmp_path / "r.json")]) == 1
    assert "--period must be YYYY-MM, got: '2026-7'" in capsys.readouterr().err
    assert drive.scopes == []


def test_execute_moves_exactly_the_reported_pairs_to_a_quarantine_outside_the_root(drive, tmp_path, capsys):
    report_path = tmp_path / "report.json"
    assert main(["--period", "2026-07", "--report", str(report_path)]) == 0
    capsys.readouterr()

    assert main(["--execute", "--report", str(report_path)]) == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary == {"status": "ok", "mode": "executed", "period": "2026-07", "moved": 4,
                       "skipped": 0, "misplaced_after": 0, "record": f"{report_path}.executed.json"}
    assert drive.scopes == [READONLY_SCOPE, WRITE_SCOPE]
    assert sorted(fid for _, fid in drive.called("update")) == sorted(
        f"{e}-2026-05-{x}" for e in ("BTL_01", "BTL_02") for x in ("pdf", "csv")
    )
    for file_id in (c[1] for c in drive.called("update")):
        ancestors = drive.ancestors(file_id)
        assert "root" not in ancestors
        assert [drive.nodes[a]["name"] for a in ancestors] == ["BTL_01" if "BTL_01" in file_id else "BTL_02",
                                                               "2026-07", QUARANTINE_FOLDER, "Shared drive"]
    assert drive.nodes["may-in-may"]["parents"] == ["BTL_01-05"]
    assert drive.nodes["BTL_01-2026-07-pdf"]["parents"] == ["BTL_01-07"]
    assert drive.nodes["payroll"]["parents"] == ["p07"]
    record = json.loads((tmp_path / "report.json.executed.json").read_text())
    assert [m["source"] for m in record["moved"]] == MISPLACED
    assert record["counts_after"]["misplaced"] == 0


def test_execute_skips_a_pair_that_changed_since_the_dry_run(drive, tmp_path, capsys):
    report_path = tmp_path / "report.json"
    assert main(["--period", "2026-07", "--report", str(report_path)]) == 0
    drive.nodes["BTL_02-2026-05-pdf"]["parents"] = ["BTL_01-05"]  # moved by someone else meanwhile
    capsys.readouterr()

    assert main(["--execute", "--report", str(report_path)]) == 1

    summary = json.loads(capsys.readouterr().out)
    assert (summary["status"], summary["moved"], summary["skipped"]) == ("partial", 3, 1)
    assert ("update", "BTL_02-2026-05-pdf") not in drive.calls
    assert drive.nodes["BTL_02-2026-05-pdf"]["parents"] == ["BTL_01-05"]


def test_execute_refuses_to_run_a_report_twice(drive, tmp_path, capsys):
    report_path = tmp_path / "report.json"
    assert main(["--period", "2026-07", "--report", str(report_path)]) == 0
    assert main(["--execute", "--report", str(report_path)]) == 0
    updates = len(drive.called("update"))
    capsys.readouterr()

    assert main(["--execute", "--report", str(report_path)]) == 1
    assert "already executed" in capsys.readouterr().err
    assert len(drive.called("update")) == updates
