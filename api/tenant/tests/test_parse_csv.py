import json
import subprocess
import sys
from pathlib import Path

TENANT_ROOT = Path(__file__).parent.parent
SCRIPT = str(TENANT_ROOT / "scripts" / "parse_csv.py")
SAMPLE_CSV = str(TENANT_ROOT / "data" / "sample_enrollments.csv")


def run_script(args):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True,
        text=True,
        cwd=str(TENANT_ROOT),
    )


def test_parse_sample_csv_returns_three_rows():
    result = run_script([SAMPLE_CSV])
    assert result.returncode == 0
    rows = json.loads(result.stdout)
    assert len(rows) == 3


def test_priya_sharma_row_parsed_correctly():
    result = run_script([SAMPLE_CSV])
    rows = json.loads(result.stdout)
    priya = rows[0]
    assert priya["name"] == "Priya Sharma"
    assert priya["gender"] == "Female"
    assert priya["course"] == "Standard I"
    assert priya["section"] == "A"
    assert priya["roll_no"] == "1"


def test_dob_normalised_to_iso8601():
    result = run_script([SAMPLE_CSV])
    rows = json.loads(result.stdout)
    assert rows[0]["date_of_birth"] == "2010-06-15"
    assert rows[1]["date_of_birth"] == "2011-03-22"


def test_missing_dob_is_null():
    result = run_script([SAMPLE_CSV])
    rows = json.loads(result.stdout)
    # Ravi Kumar has no DOB
    ravi = rows[2]
    assert ravi["name"] == "Ravi Kumar"
    assert ravi["date_of_birth"] is None


def test_empty_strings_become_null():
    result = run_script([SAMPLE_CSV])
    rows = json.loads(result.stdout)
    priya = rows[0]
    # email and mobile are empty in CSV
    assert priya["email"] is None
    assert priya["mobile"] is None


def test_father_fields_parsed():
    result = run_script([SAMPLE_CSV])
    rows = json.loads(result.stdout)
    priya = rows[0]
    assert priya["father_name"] == "Rajesh Sharma"
    assert priya["father_email"] == "rajesh.sharma@gmail.com"
    assert priya["father_mobile"] == "9876543210"


def test_arjun_has_no_father_name():
    result = run_script([SAMPLE_CSV])
    rows = json.loads(result.stdout)
    arjun = rows[1]
    assert arjun["father_name"] is None


def test_file_not_found_exits_1():
    result = run_script(["data/nonexistent.csv"])
    assert result.returncode == 1


def test_no_args_exits_1():
    result = run_script([])
    assert result.returncode == 1
