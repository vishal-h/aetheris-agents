"""Stage 1 (fetch) shared bits.

Fetchers return provider-native *raw* item dicts — lossless, unmapped. The
fetch CLI wraps each in an envelope and writes JSONL. Mapping to the edux
structure happens in stage 2 (mappers.py), so raw captures can be re-mapped
without re-querying.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class SearchError(Exception):
    def __init__(self, message: str, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


class Fetcher(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, term: str, start: int = 1, num: int = 10, country: str = "IN") -> list[dict]:
        """Return up to `num` provider-native raw item dicts from index `start`
        (1, 11, 21, …). No mapping — that is stage 2's job."""
        raise NotImplementedError


def _send(req: urllib.request.Request, timeout: int) -> Any:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        raise SearchError(
            f"HTTP {exc.code} from {req.full_url}", status=exc.code, body=parsed
        ) from exc
    except urllib.error.URLError as exc:
        raise SearchError(
            f"network error contacting {req.full_url}: {exc.reason}"
        ) from exc


def http_post_json(url: str, headers: dict[str, str], payload: Any, timeout: int = 30) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    return _send(req, timeout)


def http_get_json(
    url: str, headers: dict[str, str], params: dict[str, Any], timeout: int = 30
) -> Any:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        full, headers={"Accept": "application/json", **headers}, method="GET"
    )
    return _send(req, timeout)


def basic_auth(login: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{login}:{password}".encode()).decode()


def get_fetcher(provider: str) -> Fetcher:
    provider = provider.lower()
    if provider == "cse":
        from fetch_cse import CseFetcher
        return CseFetcher()
    if provider == "serper":
        from fetch_serper import SerperFetcher
        return SerperFetcher()
    if provider == "dataforseo":
        from fetch_dataforseo import DataForSeoFetcher
        return DataForSeoFetcher()
    if provider == "exa":
        from fetch_exa import ExaFetcher
        return ExaFetcher()
    raise SearchError(
        f"unknown provider {provider!r}; expected: cse, serper, dataforseo, exa"
    )


PROVIDERS = ("cse", "serper", "dataforseo", "exa")
