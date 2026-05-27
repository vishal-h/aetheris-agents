#!/usr/bin/env python3
"""submit_to_rmq.py <s3_path> <inst_id> [<etl_content>]

Publishes an ETL job message to RabbitMQ pointing to an S3 file.

etl_content (optional): the full ETL job list text. When supplied the JOB_KEY
is extracted from the "# JOB_KEY: <hash>" header line and used as the RabbitMQ
message_id, making submissions idempotent within the broker's deduplication
window. If omitted or the header is absent a random UUID is used.

Message shape:
  {
    "title": "etl_run_script",
    "payload": {"s3_path": "<s3_path>", "queue": []},
    "client_id": "<inst_id>"
  }

Queue: ct_r_etl_worker
Connection: CT_RABBITMQ_URL (amqps://...)

Output (stdout): {"job_ref": "<job_key_or_uuid>", "status": "queued"}
Exit 0 on success, exit 1 on failure.
"""

import json
import os
import sys
import uuid


def _job_key_from_etl(etl_content: str) -> str | None:
    first_line = etl_content.splitlines()[0] if etl_content else ""
    if first_line.startswith("# JOB_KEY:"):
        return first_line.split(":", 1)[1].strip()
    return None


def submit(s3_path: str, inst_id: str, etl_content: str | None = None) -> dict:
    import pika

    rmq_url = os.environ.get("CT_RABBITMQ_URL", "")
    if not rmq_url:
        raise ValueError("CT_RABBITMQ_URL not set")

    job_ref = (_job_key_from_etl(etl_content) if etl_content else None) or str(uuid.uuid4())
    message = {
        "title": "etl_run_script",
        "payload": {"s3_path": s3_path, "queue": []},
        "client_id": inst_id,
    }

    params = pika.URLParameters(rmq_url)
    params.socket_timeout = 10
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="ct_r_etl_worker", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="ct_r_etl_worker",
        body=json.dumps(message).encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2,
            message_id=job_ref,
            content_type="application/json",
        ),
    )
    connection.close()

    return {"job_ref": job_ref, "status": "queued"}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: submit_to_rmq.py <s3_path> <inst_id> [<etl_content>]", file=sys.stderr)
        sys.exit(1)

    s3_path = sys.argv[1]
    inst_id = sys.argv[2]
    etl_content = sys.argv[3] if len(sys.argv) >= 4 else None

    try:
        result = submit(s3_path, inst_id, etl_content)
        print(json.dumps(result))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
