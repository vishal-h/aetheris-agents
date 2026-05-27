#!/usr/bin/env python3
"""notify_at1qry.py <at1qry_run_id> <message>

POSTs to the Aetheris resume endpoint to wake at1qry via the webhook path.
Reads AETHERIS_API_BASE from the environment (default http://localhost:4001).

Output (stdout): {"status": "ok"} or {"status": "failed", "reason": "..."}
Exit 0 always — webhook failure is non-fatal; cot1 falls back to send_message.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def notify(at1qry_run_id: str, message: str) -> dict:
    base = os.environ.get("AETHERIS_API_BASE", "http://localhost:4001").rstrip("/")
    url = f"{base}/api/runs/{at1qry_run_id}/resume"
    body = json.dumps({"message": message}).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)
            return {"status": "ok", "response": data}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        return {"status": "failed", "reason": f"HTTP {exc.code}: {raw}"}
    except (urllib.error.URLError, OSError) as exc:
        return {"status": "failed", "reason": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "reason": f"unexpected: {exc}"}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: notify_at1qry.py <at1qry_run_id> <message>", file=sys.stderr)
        sys.exit(1)

    at1qry_run_id = sys.argv[1]
    message = sys.argv[2]
    result = notify(at1qry_run_id, message)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
