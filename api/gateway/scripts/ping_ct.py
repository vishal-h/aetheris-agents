#!/usr/bin/env python3
"""ping_ct.py

Checks connectivity to the ct-api by calling GET /api/stu/_Monitor/ping.
Reads CT_API_BASE_URL and CT_API_TOKEN from environment.
Output: {"status": "ok", "latency_ms": N} or {"status": "error", "reason": "..."}
Exit 0 on 200, exit 1 on failure.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _app_id_from_token(token: str) -> str | None:
    try:
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "==").decode())
        inner = json.loads(payload["token"])
        return inner.get("AppId")
    except Exception:
        return None


def ping() -> dict:
    base_url = os.environ.get("CT_API_BASE_URL", "").rstrip("/")
    token = os.environ.get("CT_API_TOKEN", "")

    if not base_url:
        return {"status": "error", "reason": "CT_API_BASE_URL not set"}

    url = f"{base_url}/api/stu/_Monitor/ping"
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        app_id = _app_id_from_token(token)
        if app_id:
            headers["AccessCode"] = app_id

    req = urllib.request.Request(url, headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status == 200:
                return {"status": "ok", "latency_ms": latency_ms}
            return {"status": "error", "reason": f"HTTP {resp.status}"}
    except urllib.error.HTTPError as exc:
        return {"status": "error", "reason": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


def main() -> None:
    result = ping()
    print(json.dumps(result))
    if result["status"] != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
