"""Stage-1 fetcher: Google Custom Search JSON API (the legacy engine).

Free up to 100 queries/day; usable until the 2027-01-01 sunset. The same engine
ct-edux used, so results are continuous with the legacy site. Credentials reuse
the legacy names: GWS_CSE_API_KEY, GWS_CSE_ENGINE_ID, and optional
GWS_CSE_REFERER (for a referer-restricted key).

Unlike the other providers, CSE returns real pagemap (cse_image, metatags), so
its mapper populates `image` and `metatags` properly. Native `start` pagination
(1, 11, 21, …, max 91) — no over-fetch/slice. Geo is `cr=countryXX`.
"""

from __future__ import annotations

import os

from fetch_base import Fetcher, SearchError, http_get_json

ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class CseFetcher(Fetcher):
    name = "cse"

    def __init__(self) -> None:
        self.api_key = os.environ.get("GWS_CSE_API_KEY")
        self.engine_id = os.environ.get("GWS_CSE_ENGINE_ID")
        self.referer = os.environ.get("GWS_CSE_REFERER")  # optional
        if not self.api_key or not self.engine_id:
            raise SearchError("GWS_CSE_API_KEY / GWS_CSE_ENGINE_ID not set")

    def fetch(self, term: str, start: int = 1, num: int = 10, country: str = "IN") -> list[dict]:
        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": term,
            "start": max(start, 1),
            "num": min(max(num, 1), 10),        # CSE caps at 10 per request
            "cr": f"country{country.upper()}",   # e.g. countryIN
        }
        headers = {"Referer": self.referer} if self.referer else {}
        body = http_get_json(ENDPOINT, headers, params)
        return list(body.get("items", []))  # raw items (incl. pagemap), unmapped
