"""Stage-1 fetcher: DataForSEO (cheapest per-query; live/advanced endpoint).

Pure prepaid billing. No result offset — over-fetch and slice by start.
Only `type == "organic"` items are returned; ads, knowledge panels, etc. are dropped.

Country defaults to India when the ISO code is not in _LOCATION_MAP (DataForSEO
uses location_name strings, not ISO codes). Unknown codes fall back to "India"
silently — this is intentional for the India-focused eduloka pipeline. Pass a
`country` value present in _LOCATION_MAP to target another market explicitly.

DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD must be set.
"""

from __future__ import annotations

import os

from fetch_base import Fetcher, SearchError, basic_auth, http_post_json

ENDPOINT = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

# DataForSEO uses location_name strings rather than ISO codes.
_LOCATION_MAP = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "AU": "Australia",
    "CA": "Canada",
    "DE": "Germany",
    "SG": "Singapore",
}


class DataForSeoFetcher(Fetcher):
    name = "dataforseo"

    def __init__(self) -> None:
        login = os.environ.get("DATAFORSEO_LOGIN")
        password = os.environ.get("DATAFORSEO_PASSWORD")
        if not login or not password:
            raise SearchError("DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not set")
        self._auth = basic_auth(login, password)

    def fetch(self, term: str, start: int = 1, num: int = 10, country: str = "IN") -> list[dict]:
        # No offset param — over-fetch from the top and slice to [start-1:].
        fetch_n = (start - 1) + num
        location = _LOCATION_MAP.get(country.upper(), "India")
        payload = [{
            "keyword": term,
            "location_name": location,
            "language_name": "English",
            "depth": fetch_n,
        }]
        headers = {"Authorization": self._auth}
        body = http_post_json(ENDPOINT, headers, payload)
        # Use `or []` (not `get(k, [])`) so that explicit null values — which
        # DataForSEO returns on task-level errors like auth/quota failures —
        # are also treated as empty rather than causing a TypeError on indexing.
        tasks = body.get("tasks") or []
        if not tasks:
            return []
        results = tasks[0].get("result") or []
        if not results:
            return []
        all_items = results[0].get("items") or []
        organic = [i for i in all_items if i.get("type") == "organic"]
        return organic[start - 1:][:num]
