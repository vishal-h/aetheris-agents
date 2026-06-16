"""Stage-1 fetcher: Serper (Google SERP, closest paid CSE match).

Prepaid 6-month billing. Paginates natively by page number.

SERPER_API_KEY must be set.
"""

from __future__ import annotations

import os

from fetch_base import Fetcher, SearchError, http_post_json

ENDPOINT = "https://google.serper.dev/search"


class SerperFetcher(Fetcher):
    name = "serper"

    def __init__(self) -> None:
        self.api_key = os.environ.get("SERPER_API_KEY")
        if not self.api_key:
            raise SearchError("SERPER_API_KEY not set")

    def fetch(self, term: str, start: int = 1, num: int = 10, country: str = "IN") -> list[dict]:
        # Serper paginates by page; page 1 = results 1–num, page 2 = num+1–2*num, …
        page = (start - 1) // num + 1
        payload = {
            "q": term,
            "num": num,
            "page": page,
            "gl": country.lower(),  # geo-location: "in", "us", …
        }
        body = http_post_json(ENDPOINT, {"X-API-KEY": self.api_key}, payload)
        return list(body.get("organic", []))  # raw organic items, unmapped
