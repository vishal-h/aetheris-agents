#!/usr/bin/env python3
"""upload_etl_to_s3.py <etl_content> <seq>

Uploads an ETL job list to S3.

Filename convention: {CT_ENV}_{seq}_{CT_INST_SHORT_CODE}_{acad_year}_students.etl
Academic year extracted from InstId (CT_API_TOKEN claim): inst_id.split("-")[1]
S3 path: s3://{CT_S3_BUCKET}/{CT_INST_SHORT_CODE}/etls/{filename}

Output (stdout): {"s3_path": "s3://..."}
Exit 0 on success, exit 1 on failure.
"""

import base64
import json
import os
import sys


def _acad_year_from_token(token: str) -> str:
    try:
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "==").decode())
        inner = json.loads(payload["token"])
        inst_id = inner.get("ClientId", "")
        return inst_id.split("-")[1] if "-" in inst_id else "0000"
    except Exception:
        return "0000"


def upload(etl_content: str, seq: str) -> dict:
    import boto3

    bucket = os.environ.get("CT_S3_BUCKET", "")
    region = os.environ.get("CT_S3_REGION", "ap-south-1")
    short_code = os.environ.get("CT_INST_SHORT_CODE", "unknown")
    env = os.environ.get("CT_ENV", "dev")
    token = os.environ.get("CT_API_TOKEN", "")

    if not bucket:
        raise ValueError("CT_S3_BUCKET not set")

    acad_year = _acad_year_from_token(token)
    filename = f"{env}_{seq}_{short_code}_{acad_year}_students.etl"
    s3_key = f"{short_code}/etls/{filename}"

    client = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=etl_content.encode("utf-8"),
        ContentType="text/plain",
    )

    return {"s3_path": f"s3://{bucket}/{s3_key}"}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: upload_etl_to_s3.py <etl_content> [seq]", file=sys.stderr)
        sys.exit(1)

    etl_content = sys.argv[1]
    seq = sys.argv[2] if len(sys.argv) >= 3 else "1"

    try:
        result = upload(etl_content, seq)
        print(json.dumps(result))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
