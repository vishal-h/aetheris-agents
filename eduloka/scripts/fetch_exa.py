"""Stage-1 fetcher: Exa (semantic search, returns full page text).

Usage-based billing. No native result offset — over-fetch and slice by start.
Country filtering is not supported by Exa and is silently ignored.

EXA_API_KEY must be set.
"""

from __future__ import annotations

import os

from fetch_base import Fetcher, SearchError, http_post_json

ENDPOINT = "https://api.exa.ai/search"


class ExaFetcher(Fetcher):
    name = "exa"

    def __init__(self) -> None:
        self.api_key = os.environ.get("EXA_API_KEY")
        if not self.api_key:
            raise SearchError("EXA_API_KEY not set")

    def fetch(self, term: str, start: int = 1, num: int = 10, country: str = "IN") -> list[dict]:
        # Exa has no offset param — over-fetch from the top and slice to [start-1:].
        # country is ignored (Exa does not support geo-filtering).
        fetch_n = (start - 1) + num
        payload = {
            "query": term,
            "numResults": fetch_n,
            "contents": {"text": True},  # include full page text inline
        }
        body = http_post_json(ENDPOINT, {"x-api-key": self.api_key}, payload)
        results = body.get("results", [])
        return results[start - 1:][:num]
