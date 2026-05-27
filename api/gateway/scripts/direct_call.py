#!/usr/bin/env python3
"""direct_call.py <capability> <payload_json> <on_duplicate>

Executes a single direct-mode API call for setup capabilities.

on_duplicate values:
  return_existing_id  — 409 → search for existing record → return its ID
  fail                — 409 → return status: failed
  ignore              — 409 → treat as success

Output (stdout):
  {"status": "ok", "result": {...}}
  {"status": "duplicate_resolved", "result": {"id": "..."}}
  {"status": "failed", "reason": "..."}

Exit 0 always (errors reported in result).
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request


CAPABILITY_ENDPOINTS: dict[str, tuple[str, str]] = {
    "create_institution": ("POST", "/api/auth/Institution"),
    "create_course":      ("POST", "/api/stu/Course"),
}


def _auth_headers(token: str) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
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


def _http(method: str, url: str, body: dict, headers: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_bytes = exc.read()
        try:
            err_body = json.loads(body_bytes.decode())
        except Exception:
            err_body = {"raw": body_bytes.decode()[:200]}
        return exc.code, err_body


def _find_existing(capability: str, payload: dict, base_url: str, headers: dict) -> str | None:
    """Attempt to retrieve the ID of a duplicate record after a 409."""
    if capability == "create_institution":
        name = payload.get("Name") or payload.get("name") or ""
        status, data = _http("GET", f"{base_url}/api/auth/Institution", {}, headers)
        if status == 200:
            for inst in data if isinstance(data, list) else data.get("data", []):
                if inst.get("name", "").strip().lower() == name.strip().lower():
                    return inst.get("id")
    elif capability == "create_course":
        name = payload.get("CourseName") or payload.get("courseName") or ""
        status, data = _http("GET", f"{base_url}/api/stu/Course", {}, headers)
        if status == 200:
            for course in data if isinstance(data, list) else data.get("data", []):
                if course.get("name", "").strip().lower() == name.strip().lower():
                    return course.get("id")
    return None


def direct_call(capability: str, payload: dict, on_duplicate: str) -> dict:
    base_url = os.environ.get("CT_API_BASE_URL", "").rstrip("/")
    token = os.environ.get("CT_API_TOKEN", "")

    if not base_url or not token:
        return {"status": "failed", "reason": "CT_API_BASE_URL or CT_API_TOKEN not set"}

    if capability not in CAPABILITY_ENDPOINTS:
        return {"status": "failed", "reason": f"unknown capability: {capability}"}

    method, path = CAPABILITY_ENDPOINTS[capability]
    url = base_url + path
    headers = _auth_headers(token)

    status, data = _http(method, url, payload, headers)

    if status in (200, 201):
        return {"status": "ok", "result": data}

    if status == 409:
        if on_duplicate == "return_existing_id":
            existing_id = _find_existing(capability, payload, base_url, headers)
            if existing_id:
                return {"status": "duplicate_resolved", "result": {"id": existing_id}}
            return {"status": "failed", "reason": "duplicate but could not retrieve existing ID"}
        elif on_duplicate == "ignore":
            return {"status": "ok", "result": {}}
        else:
            return {"status": "failed", "reason": f"409 Conflict: {data}"}

    return {"status": "failed", "reason": f"HTTP {status}: {data}"}


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: direct_call.py <capability> <payload_json> <on_duplicate>",
              file=sys.stderr)
        sys.exit(1)

    capability, payload_json, on_duplicate = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as e:
        print(f"Error: invalid payload JSON: {e}", file=sys.stderr)
        sys.exit(1)

    result = direct_call(capability, payload, on_duplicate)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
