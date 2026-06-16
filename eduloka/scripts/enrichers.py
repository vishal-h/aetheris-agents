"""Stage-3 enrichers: pure record → payload functions.

Each enricher takes an EduxRecord and returns a payload dict. enrich.py
stamps _by/_at/_v and writes it under enrichment[name]. Enrichers must be:
  - pure: no side effects, no network, no randomness
  - deterministic: same record → same payload every time
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from edux_record import EduxRecord

ENRICHER_VERSIONS: dict[str, int] = {
    "domain": 1,
    "keywords": 1,
}

_STOPWORDS = frozenset([
    "a", "an", "the", "and", "or", "of", "in", "is", "it", "to", "for",
    "with", "on", "at", "by", "from", "as", "be", "are", "was", "were",
    "its", "this", "that", "has", "have", "had", "not", "but", "also",
])


def enrich_domain(record: EduxRecord) -> dict:
    if not record.link:
        return {"domain": None, "tld": None}
    host = urlparse(record.link).hostname or ""
    host = re.sub(r"^www\.", "", host)
    parts = host.split(".")
    tld = parts[-1] if len(parts) >= 2 else None
    return {"domain": host, "tld": tld}


def enrich_keywords(record: EduxRecord) -> dict:
    text = " ".join(filter(None, [record.title, record.snippet]))
    words = re.findall(r"[a-z]+", text.lower())
    seen: set[str] = set()
    terms: list[str] = []
    for w in words:
        if w not in _STOPWORDS and w not in seen and len(w) > 2:
            seen.add(w)
            terms.append(w)
    return {"terms": terms}


ENRICHERS: dict[str, object] = {
    "domain": enrich_domain,
    "keywords": enrich_keywords,
}
