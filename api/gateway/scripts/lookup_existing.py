#!/usr/bin/env python3
"""lookup_existing.py <name> <course_name> <sec_name>

Deduplication guard: searches ct-api for an existing student matching
name + course + section. Uses client-side filtering over flatData since
the API does not support server-side name filtering.

Output (stdout):
  {"found": true, "guid": "<id>"}
  {"found": false, "guid": null}
  {"found": false, "search_unavailable": true}  — when API is unreachable or uncredentialed

Exit 0 always.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request


def _auth_headers(token: str) -> dict:
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    try:
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "==").decode())
        inner = json.loads(payload["token"])
        app_id = inner.get("AppId")
        if app_id:
            headers["AccessCode"] = app_id
    except Exception:
        pass
    return headers


def lookup(name: str, course_name: str, sec_name: str) -> dict:
    base_url = os.environ.get("CT_API_BASE_URL", "").rstrip("/")
    token = os.environ.get("CT_API_TOKEN", "")

    if not base_url or not token:
        return {"found": False, "search_unavailable": True, "guid": None}

    url = f"{base_url}/api/stu/Student/flatData"
    headers = _auth_headers(token)
    headers["Content-Type"] = "application/json"
    body = json.dumps({"pageNo": 1, "pageSize": 500}).encode()

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return {"found": False, "search_unavailable": True, "guid": None}
            data = json.loads(resp.read().decode())
    except Exception:
        return {"found": False, "search_unavailable": True, "guid": None}

    name_lower = name.strip().lower()
    course_lower = course_name.strip().lower()
    sec_lower = sec_name.strip().lower()

    for student in data.get("data", []):
        if (
            student.get("name", "").strip().lower() == name_lower
            and student.get("course", "").strip().lower() == course_lower
            and student.get("section", "").strip().lower() == sec_lower
        ):
            return {"found": True, "guid": student["id"]}

    return {"found": False, "guid": None}


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: lookup_existing.py <name> <course_name> <sec_name>", file=sys.stderr)
        sys.exit(1)

    name, course_name, sec_name = sys.argv[1], sys.argv[2], sys.argv[3]
    result = lookup(name, course_name, sec_name)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
