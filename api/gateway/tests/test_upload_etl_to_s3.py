import json
import subprocess
import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).parent.parent
SCRIPT = str(GATEWAY_ROOT / "scripts" / "upload_etl_to_s3.py")

SAMPLE_ETL = "# JOB_KEY: abc123\nPOST\t/api/stu/Student\t{\"Name\":\"Test\"}"


def run_script(etl_content, seq="1"):
    return subprocess.run(
        [sys.executable, SCRIPT, etl_content, seq],
        capture_output=True, text=True,
        cwd=str(GATEWAY_ROOT),
    )


def test_no_args_exits_nonzero():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    assert r.returncode != 0


def test_output_has_s3_path_key():
    import os
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("CT_S3_BUCKET"):
        pytest.skip("AWS credentials or CT_S3_BUCKET not set")
    result = run_script(SAMPLE_ETL)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "s3_path" in data


@pytest.mark.integration
def test_s3_path_format():
    import os
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("CT_S3_BUCKET"):
        pytest.skip("AWS credentials not set")
    result = run_script(SAMPLE_ETL, "2")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    s3_path = data["s3_path"]
    bucket = os.environ["CT_S3_BUCKET"]
    short_code = os.environ.get("CT_INST_SHORT_CODE", "")
    assert s3_path.startswith(f"s3://{bucket}/")
    assert short_code in s3_path
    assert s3_path.endswith("_students.etl")


@pytest.mark.integration
def test_seq_in_filename():
    import os
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("CT_S3_BUCKET"):
        pytest.skip("AWS credentials or CT_S3_BUCKET not set")
    result = run_script(SAMPLE_ETL, "3")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "_3_" in data["s3_path"]
