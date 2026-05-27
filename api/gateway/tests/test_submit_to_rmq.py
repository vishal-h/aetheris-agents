import json
import subprocess
import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "submit_to_rmq.py")

INST_ID = "0c250000-2425-11e7-89e2-1cbdb9e7fd04"
S3_PATH = "s3://s3-btl-ct-test/btlcol/etls/dev_1_btlcol_2425_students.etl"

SAMPLE_ETL = "# JOB_KEY: abc123def456abc123def456abc123def456abc123def456abc123def456abc123\nPOST\t/api/stu/Student\t{}"


def run_script(s3_path, inst_id, etl_content=None):
    cmd = [sys.executable, SCRIPT, s3_path, inst_id]
    if etl_content is not None:
        cmd.append(etl_content)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(GATEWAY_ROOT))


def test_no_args_exits_nonzero():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert r.returncode != 0


def test_job_key_extracted_from_etl_content():
    import os
    if not os.environ.get("CT_RABBITMQ_URL"):
        pytest.skip("CT_RABBITMQ_URL not set")
    result = run_script(S3_PATH, INST_ID, SAMPLE_ETL)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["job_ref"] == "abc123def456abc123def456abc123def456abc123def456abc123def456abc123"


@pytest.mark.integration
def test_random_job_ref_when_etl_omitted():
    import os
    if not os.environ.get("CT_RABBITMQ_URL"):
        pytest.skip("CT_RABBITMQ_URL not set")
    r1 = run_script(S3_PATH, INST_ID)
    r2 = run_script(S3_PATH, INST_ID)
    d1 = json.loads(r1.stdout)
    d2 = json.loads(r2.stdout)
    assert d1["job_ref"] != d2["job_ref"]


@pytest.mark.integration
def test_returns_job_ref():
    import os
    if not os.environ.get("CT_RABBITMQ_URL"):
        pytest.skip("CT_RABBITMQ_URL not set")
    result = run_script(S3_PATH, INST_ID)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "job_ref" in data
    assert data["status"] == "queued"


@pytest.mark.integration
def test_job_ref_is_nonempty():
    import os
    if not os.environ.get("CT_RABBITMQ_URL"):
        pytest.skip("CT_RABBITMQ_URL not set")
    result = run_script(S3_PATH, INST_ID)
    data = json.loads(result.stdout)
    assert data["job_ref"]
    assert len(data["job_ref"]) > 4
